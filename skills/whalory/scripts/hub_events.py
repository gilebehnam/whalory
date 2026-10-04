#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hub_events: local capture for Whalory Hub (spec 4.2 to 4.10, 5.2, 5.3, 17.3.1).

Standard library only, Python 3.8 to 3.14. This module opens no socket and starts no
process. It writes only events/<epoch>.jsonl in the Hub folder, and only while a person
turned on weekly statistics (`stats`) or weekly packets (`packets`) in a terminal and the
owner-signed baseline has that lane open. No public function raises: each one catches
Exception and returns a neutral value.

Public API (spec 5.2):

    enabled() -> bool
    held_out(lang, rule_or_phrase_id, severity=None) -> bool
    record_lint(source, lang, fg, result, words) -> None
    record_outcome(shown, final, lang='auto', fmt=None, playbook=None, revisions=None,
                   profile=None) -> {"recorded": bool, "reason": str|None}
    record_health(kind, reason=None, overlay_id=None) -> None

Helpers for the MCP server (spec 4.5, 5.3; texts stay in memory, at most 8 texts for at
most 6 hours, and only while enabled() is true):

    remember(text, lang='auto') -> None      after lint_text / lint_file
    recall(lang) -> str | None               the most recent text in that language
    check_final_outcome(final, lang='auto', fmt=None, playbook=None, revisions=None,
                        profile=None) -> {"recorded", "reason"}   recall() + record_outcome()
    forget_texts() -> None

Shared with hub_client (never needed by the linters):

    configure(hub_home=None, test=False, now=None)   test flags of spec 5.10 (hub_client, tests)
    test_mode(), invalidate(), terminal hooks live in hub_client.terminal_notices()
    hub_home() -> str | None                 None when WHALORY_HUB=0
    lane() -> 'stats' | 'packets' | None     the lane that captures right now
    policy() -> dict                          the verified baseline switches (see _policy)
    settings() -> dict                        settings.json with defaults
    save_settings(s)                          atomic write
    skill_version(), skill_edition(), current_epoch(now=None)

Environment variables only lower a setting (spec 5.10); the former WHALYA_* names are read
when the WHALORY_* name is unset.
"""
from __future__ import print_function

import sys

sys.dont_write_bytecode = True

import datetime  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import tempfile  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402

__all__ = ['enabled', 'held_out', 'record_lint', 'record_outcome', 'record_health', 'remember', 'recall',
           'check_final_outcome', 'forget_texts', 'configure', 'hub_home', 'lane', 'policy', 'settings',
           'save_settings', 'skill_version', 'skill_edition', 'current_epoch', 'invalidate']

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
DATA_DIR = os.path.join(SKILL_DIR, 'data', 'hub')
PINNED_ROOT = os.path.join(DATA_DIR, 'root.json')
BUNDLED_DIR = os.path.join(DATA_DIR, 'bundled')

UTC = datetime.timezone.utc
SETTINGS_SCHEMA = 'whalory.hub-settings/1'
CONSENT_VERSION = '2026-11-01'
CONSENT_MAX_AGE_DAYS = 730          # re-consent every 24 months (spec 4.10)
EVENT_MAX_LINE = 16 * 1024
EVENT_MAX_AGE_DAYS = 14
TEXT_TTL = 6 * 3600                 # MCP memory of shown texts (spec 4.5)
TEXT_SLOTS = 8
MARK_TTL = 2.0                      # seconds between looks at the trusted files in a long-running process
SESSION_BUDGET = 3
WEEK_BUDGET = 20
HOST_REQUEST_VALUES = ('off', 'stats', 'stats+phrases')
HEALTH_KINDS = ('selftest_ok', 'selftest_fail', 'cap_reject', 'overlay_exception', 'revert', 'sync_ok',
                'sync_fail', 'verify_fail')
HEALTH_REASONS = {'cap_reject': ('violation', 'gap'), 'verify_fail': ('fork', 'mismatch', 'local')}
_ID = re.compile(r'^[a-z0-9-]{1,40}$')
_OV_B = re.compile(r'^b-[0-9]{4}\.[0-9]{2}\.[0-9]{1,3}$')
_OV_A = re.compile(r'^a-[0-9]{4}w[0-9]{2}\.[0-9]{1,3}$')
_FALSE = ('0', 'false', 'off', 'no')

#: Public TEST ONLY Ed25519 key ids of STUDIO/hub/contracts/fixtures/test-keys (derived from fixed
#: labels, so anyone can sign with them). A pinned root that lists any of them is a test root:
#: outside --test the client then treats every lane as closed and never syncs (see hub_client).
TEST_KEY_IDS = frozenset([
    '2319786c17c2bd85', '0347f3bf2ae6b02c', 'f6dfa2461f0f4739', '677bb2584cce4e2a', 'd96dbf08dccc9d92',
    'd595f9b676933a4c', '093401e2866137fe', '2c383f65e136c99f', '0c0a2b44529e56be', '0a81fcd4790de395',
])

_lock = threading.RLock()
_config = {'home': None, 'test': False, 'now': None}
_cache = {}
_texts = []                         # [(monotonic time, lang, text)]
_process = {'outcomes': 0}


# ----------------------------------------------------------------------------- environment


def env(name):
    """WHALORY_<name>, else the deprecated WHALYA_<name> (read only), else ''."""
    v = os.environ.get('WHALORY_' + name)
    if v is None:
        v = os.environ.get('WHALYA_' + name)
    return (v or '').strip()


def hub_disabled():
    """WHALORY_HUB=0: everything off, no Hub writes, no overlay (spec 4.2)."""
    return env('HUB').lower() in _FALSE


def contribution_blocked():
    """WHALORY_HUB_CONTRIBUTE=0, or DO_NOT_TRACK / DISABLE_TELEMETRY with any non-empty value."""
    if env('HUB_CONTRIBUTE').lower() in _FALSE:
        return True
    return bool(os.environ.get('DO_NOT_TRACK') or os.environ.get('DISABLE_TELEMETRY'))


def network_blocked():
    """CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC with any non-empty value: no Hub network at all."""
    return bool(os.environ.get('CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC')) or hub_disabled()


def updates_blocked():
    return network_blocked() or env('HUB_UPDATES').lower() in _FALSE


def host_request():
    """The host setting (CLAUDE_PLUGIN_OPTION_HUB_CONTRIBUTE or WHALORY_HUB_CONTRIBUTE_REQUEST).

    Returns None when neither is set, else 'off', 'stats' or 'stats+phrases'; any other value
    means 'off' (spec 4.3). It can only lower a setting or create a pending request.
    """
    raw = os.environ.get('CLAUDE_PLUGIN_OPTION_HUB_CONTRIBUTE')
    if raw is None:
        raw = os.environ.get('WHALORY_HUB_CONTRIBUTE_REQUEST')
    if raw is None:
        raw = os.environ.get('WHALYA_HUB_CONTRIBUTE_REQUEST')
    if raw is None:
        return None
    v = raw.strip().lower().replace(' ', '')
    return v if v in HOST_REQUEST_VALUES else 'off'


# ----------------------------------------------------------------------------- paths


def default_hub_home():
    """The Hub folder of spec 4.5 (no environment variable moves it, apart from the XDG base)."""
    if sys.platform.startswith('win'):
        base = os.environ.get('LOCALAPPDATA') or os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
        return os.path.join(base, 'Whalory', 'hub')
    if sys.platform == 'darwin':
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Whalory', 'hub')
    base = os.environ.get('XDG_STATE_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'state')
    return os.path.join(base, 'whalory', 'hub')


def inside_temp(path):
    """True when path lies inside the system temp folder (the only place --hub-home may point)."""
    try:
        tmp = os.path.normcase(os.path.realpath(tempfile.gettempdir()))
        p = os.path.normcase(os.path.realpath(path))
        return os.path.commonpath([tmp, p]) == tmp and p != tmp
    except (ValueError, OSError):
        return False


def configure(hub_home=None, test=False, now=None):
    """Test flags of spec 5.10, set by hub_client from its command line and by the tests.

    A hub_home is accepted only together with test=True and only inside the system temp
    folder; anything else raises ValueError (hub_client turns it into a usage error).
    now (tests only, with test=True) fixes the clock: a datetime or 'YYYY-MM-DDTHH:MM:SSZ'.
    """
    with _lock:
        if hub_home is not None:
            if not test:
                raise ValueError('--hub-home needs --test')
            if not inside_temp(hub_home):
                raise ValueError('--hub-home must be inside the system temp folder')
            hub_home = os.path.realpath(hub_home)
        if now is not None and not test:
            raise ValueError('a fixed clock needs test mode')
        if isinstance(now, str):
            now = parse_time(now)
        _config['home'] = hub_home
        _config['test'] = bool(test)
        _config['now'] = now
        _cache.clear()
        del _texts[:]
        _process['outcomes'] = 0


def test_mode():
    return bool(_config['test'])


def hub_home():
    """The Hub folder, or None when WHALORY_HUB=0."""
    if hub_disabled():
        return None
    return _config['home'] or default_hub_home()


def _p(*parts):
    home = hub_home()
    return os.path.join(home, *parts) if home else None


# ----------------------------------------------------------------------------- small file helpers


def utcnow():
    fixed = _config.get('now')
    if fixed is not None:
        return fixed
    return datetime.datetime.now(UTC).replace(microsecond=0)


def fmt_time(dt):
    return dt.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_time(s):
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=UTC)


def current_epoch(now=None):
    y, w = (now or utcnow()).isocalendar()[:2]
    return '%04d-W%02d' % (y, w)


def _mtime(path):
    try:
        return os.stat(path).st_mtime_ns
    except (OSError, TypeError):
        return None


def read_json(path, max_bytes=1024 * 1024):
    """A JSON object from a local Hub file, or None (missing, too big, not an object).

    Uses hub_verify.loads (the hardened loader of spec 7.5) when it is present.
    """
    try:
        with open(path, 'rb') as fh:
            data = fh.read(max_bytes + 1)
    except (OSError, TypeError):
        return None
    if len(data) > max_bytes:
        return None
    try:
        hv = _hub_verify()
        if hv is not None:
            doc = hv.loads(data, max_bytes=max_bytes)
        else:
            doc = json.loads(data.decode('utf-8'), parse_constant=_bad_constant)
    except Exception:
        return None
    return doc if isinstance(doc, dict) else None


def _bad_constant(name):
    raise ValueError('non-finite number %s' % name)


def makedirs(path):
    try:
        os.makedirs(path, 0o700)
    except OSError:
        if not os.path.isdir(path):
            raise


def write_atomic(path, data, private=False):
    """Write bytes: temp file in the same folder, fsync, os.replace (spec 5.8 step 9)."""
    invalidate()
    makedirs(os.path.dirname(path))
    tmp = '%s.%d.tmp' % (path, os.getpid())
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, 'O_BINARY', 0)
    fd = os.open(tmp, flags, 0o600 if private else 0o644)
    try:
        with os.fdopen(fd, 'wb') as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def dump_json(doc):
    return (json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=False) + '\n').encode('utf-8')


def move_corrupt(path):
    """Corrupt Hub files go to corrupt/ (spec 5.12); the client carries on with defaults."""
    home = hub_home()
    if not home or not os.path.exists(path):
        return
    invalidate()
    try:
        dest = os.path.join(home, 'corrupt')
        makedirs(dest)
        os.replace(path, os.path.join(dest, '%s.%d' % (os.path.basename(path), int(time.time()))))
    except OSError:
        pass


# ----------------------------------------------------------------------------- the skill


def _frontmatter():
    """SKILL.md metadata; the installed skill does not change while a process runs."""
    hit = _cache.get('fm')
    if hit is not None:
        return hit
    path = os.path.join(SKILL_DIR, 'SKILL.md')
    key = 'fm'
    meta = {}
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            head = fh.read(8192)
        if head.startswith('---'):
            block = head[3:head.find('\n---', 3)]
            inside = False
            for line in block.splitlines():
                if line.startswith('metadata:'):
                    inside = True
                    continue
                if inside and line.startswith((' ', '\t')):
                    k, _, v = line.strip().partition(':')
                    meta[k.strip()] = v.strip().strip('"\'')
                elif line.strip():
                    inside = False
    except (OSError, UnicodeDecodeError):
        pass
    _cache[key] = meta
    return meta


def skill_version():
    """The installed version: SKILL.md metadata.version, else the VERSION file, else 3.0.0."""
    v = _frontmatter().get('version')
    if not v:
        try:
            with open(os.path.join(SKILL_DIR, 'VERSION'), 'r', encoding='utf-8') as fh:
                v = fh.read().strip()
        except OSError:
            v = ''
    return v if re.match(r'^[0-9]+\.[0-9]+\.[0-9]+$', v or '') else '3.0.0'


def skill_major():
    return int(skill_version().split('.')[0])


def skill_minor():
    """Major.minor, the only version a report or packet carries (spec 5.5)."""
    return '.'.join(skill_version().split('.')[:2])


def skill_edition():
    """core | pro | studio, from SKILL.md metadata.edition; unknown means core."""
    e = (_frontmatter().get('edition') or '').strip().lower()
    return e if e in ('core', 'pro', 'studio') else 'core'


# ----------------------------------------------------------------------------- settings.json


def default_settings():
    return {'schema': SETTINGS_SCHEMA, 'updates': True, 'stats': 'off', 'phrases': False,
            'phrases_preview': False, 'packets': False, 'consent': {'stats': None, 'packets': None},
            'install_salt': None, 'pending': None, 'host_seen': None,
            'asked': {'hint_major': None, 'pending_prompted': False, 'reconsent_hint': []},
            'turned_on': {'stats': None, 'packets': None}, 'on_notice_due': None, 'pin': None}


def settings():
    """settings.json merged over the defaults; cached by mtime (spec 5.2 enabled())."""
    path = _p('settings.json')
    if path is None:
        return default_settings()
    m = _mtime(path)
    key = ('settings', path, m)
    hit = _cache.get('settings')
    if hit and hit[0] == key:
        return hit[1]
    s = default_settings()
    if m is not None:
        doc = read_json(path, 256 * 1024)
        if doc is None or doc.get('schema') != SETTINGS_SCHEMA:
            move_corrupt(path)
            m = None
        else:
            for k, v in doc.items():
                if k in s:
                    s[k] = v
    _cache['settings'] = (('settings', path, m), s)
    return s


def save_settings(s):
    """Write settings.json (never with WHALORY_HUB=0)."""
    path = _p('settings.json')
    if path is None:
        return False
    s = dict(s)
    s['schema'] = SETTINGS_SCHEMA
    write_atomic(path, dump_json(s), private=True)
    _cache.pop('settings', None)
    return True


def install_salt(s=None):
    s = s if s is not None else settings()
    v = s.get('install_salt')
    if isinstance(v, str) and re.match(r'^[0-9a-f]{64}$', v):
        return bytes.fromhex(v)
    return None


# ----------------------------------------------------------------------------- verified state


def _hub_verify():
    if 'hv' not in _cache:
        try:
            import hub_verify as hv  # noqa: F401
            _cache['hv'] = hv
        except Exception:
            _cache['hv'] = None
    return _cache['hv']


def _hub_overlay():
    if 'ho' not in _cache:
        try:
            import hub_overlay as ho  # noqa: F401
            _cache['ho'] = ho
        except Exception:
            _cache['ho'] = None
    return _cache['ho']


def _hub_mine():
    if 'hm' not in _cache:
        import hub_mine as hm
        _cache['hm'] = hm
    return _cache['hm']


def pinned_root_bytes():
    try:
        with open(PINNED_ROOT, 'rb') as fh:
            return fh.read(64 * 1024 + 1)
    except OSError:
        return None


def root_keyids(env_bytes):
    """Key ids listed in a root envelope's body, read without verification (for the test check)."""
    try:
        import base64
        env_doc = json.loads(env_bytes.decode('utf-8'))
        body = json.loads(base64.b64decode(env_doc['payload']).decode('utf-8'))
        return sorted(body.get('keys') or {})
    except Exception:
        return []


def pinned_root_is_test(env_bytes=None):
    """True when the pinned root lists a public TEST ONLY key (or cannot be read at all)."""
    if env_bytes is None:
        key = ('pinned_test', _mtime(PINNED_ROOT))
        if key not in _cache:
            _cache[key] = pinned_root_is_test(pinned_root_bytes() or b'')
        return _cache[key]
    if not env_bytes:
        return True
    ids = root_keyids(env_bytes)
    return not ids or bool(TEST_KEY_IDS.intersection(ids))


def state_doc():
    path = _p('state.json')
    if path is None:
        return {}
    doc = read_json(path, 1024 * 1024)
    return doc if isinstance(doc, dict) else {}


def invalidate():
    """Forget cached file marks at once (after this process wrote or removed Hub files)."""
    _cache.pop('marks', None)
    _cache.pop('active_ids', None)


def _trusted_marks():
    """Marks of the trusted files; looked at again at most every MARK_TTL seconds, or at once
    after invalidate(), so the hot paths of the linters stay cheap (spec 5.12)."""
    home = hub_home()
    if not home:
        return None
    now = time.monotonic()
    hit = _cache.get('marks')
    if hit is not None and hit[0] == home and now - hit[1] < MARK_TTL:
        return hit[2]
    marks = _compute_marks(home)
    _cache['marks'] = (home, now, marks)
    return marks


def _compute_marks(home):
    names = ['timestamp.json', 'baseline.json', 'auto.json', 'halt.json']
    marks = [_mtime(os.path.join(home, 'trusted', n)) for n in names]
    try:
        roots = sorted(os.listdir(os.path.join(home, 'trusted', 'root')))
    except OSError:
        roots = []
    return tuple(marks) + tuple(roots) + (_mtime(os.path.join(home, 'state.json')), _mtime(PINNED_ROOT))


def snapshot():
    """The verified metadata (hub_verify.Snapshot) of the Hub folder, else of the bundled set,
    else None. Re-verified from the pinned root whenever a trusted file changes (spec 5.9)."""
    marks = _trusted_marks()
    hit = _cache.get('snapshot')
    if hit is not None and hit[0] == marks:
        return hit[1]
    snap = None
    hv = _hub_verify()
    pinned = pinned_root_bytes()
    if hv is not None and pinned and marks is not None:
        rules = (state_doc().get('rules') or {})
        for folder, layout in ((hub_home(), 'hub'), (BUNDLED_DIR, 'mirror')):
            try:
                snap = hv.load_snapshot(hv.reader(folder, layout), pinned, rules=rules,
                                        require=('timestamp', 'baseline'), check_pinned=False)
                break
            except Exception:
                snap = None
    _cache['snapshot'] = (marks, snap)
    return snap


def _host(url):
    m = re.match(r'^https?://([^/]+)', url or '')
    return m.group(1).lower() if m else ''


def policy():
    """The switches of the verified baseline, closed when anything is missing (spec 17.2).

    {"known": bool, "test_root": bool, "collection_open": bool (for this edition),
     "discovery_open", "consent_versions", "lane_open", "lane_versions", "lane_repo",
     "holdout", "locked", "params", "stop_collection", "recipients": {collectors,
     token_issuer, collection_country}, "packets": {epoch, issue} | None, "baseline_id",
     "stale", "halt"}
    A test root outside --test closes every lane (its keys are public).
    """
    key = (_trusted_marks(), test_mode(), skill_edition())
    hit = _cache.get('policy')
    if hit is not None and hit[0] == key:
        return hit[1]
    out = _policy()
    _cache['policy'] = (key, out)
    return out


def _policy():
    snap = snapshot()
    test_root = pinned_root_is_test()
    out = {'known': False, 'test_root': test_root, 'collection_open': False, 'discovery_open': False,
           'consent_versions': [], 'lane_open': False, 'lane_versions': [], 'lane_repo': None,
           'holdout': {'warning': 10, 'error': 5}, 'locked': [], 'params': {}, 'stop_collection': False,
           'recipients': None, 'packets': None, 'stale': False, 'halt': None, 'editions': []}
    if snap is None or snap.baseline is None:
        return out
    pol = snap.baseline.get('policy') or {}
    coll = pol.get('collection') or {}
    gl = pol.get('global_lane') or {}
    meas = pol.get('measure') or {}
    trusted_ok = (not test_root) or test_mode()
    out['known'] = True
    out['editions'] = list(coll.get('editions') or [])
    out['collection_open'] = bool(trusted_ok and coll.get('open') is True
                                  and skill_edition() in (coll.get('editions') or []))
    out['discovery_open'] = bool(out['collection_open'] and coll.get('discovery_open') is True)
    out['consent_versions'] = list(coll.get('consent_versions') or [])
    out['lane_open'] = bool(trusted_ok and gl.get('open') is True)
    out['lane_versions'] = list(gl.get('consent_versions') or [])
    out['lane_repo'] = gl.get('repo')
    if isinstance(meas.get('holdout'), dict):
        out['holdout'] = meas['holdout']
    out['locked'] = list(pol.get('locked') or [])
    out['params'] = pol.get('params') or {}
    root = snap.root or {}
    out['recipients'] = {'collectors': sorted(set(_host(u) for u in root.get('collectors') or [])),
                         'token_issuer': _host(root.get('token_issuer')),
                         'collection_country': root.get('collection_country')}
    ts = snap.timestamp or {}
    if isinstance(ts.get('packets'), dict):
        out['packets'] = ts['packets']
    out['stale'] = bool(snap.stale)
    try:
        halt = snap.halt if snap.halt_active() else None
    except Exception:
        halt = None
    out['halt'] = halt
    out['stop_collection'] = bool(halt and halt.get('stop_collection'))
    return out


# ----------------------------------------------------------------------------- consent and lanes


def consent_problem(record, tier, pol, s=None):
    """Why a stored consent record no longer counts, or None (spec 4.10)."""
    if not isinstance(record, dict) or record.get('source') != 'console' or record.get('age_confirmed') is not True:
        return 'no_record'
    want = ['packets'] if tier == 'packets' else None
    tiers = record.get('tiers')
    if want and tiers != want:
        return 'no_record'
    if tier == 'stats' and tiers not in (['stats'], ['stats', 'phrases']):
        return 'no_record'
    if not isinstance(record.get('skill_major'), int) or record['skill_major'] < skill_major():
        return 'old_major'
    try:
        at = parse_time(record.get('at'))
    except (TypeError, ValueError):
        return 'no_record'
    if utcnow() - at > datetime.timedelta(days=CONSENT_MAX_AGE_DAYS):
        return 'expired'
    versions = pol['lane_versions'] if tier == 'packets' else pol['consent_versions']
    if record.get('version') not in versions:
        return 'version'
    if tier == 'stats':
        rec = pol.get('recipients') or {}
        if (sorted(record.get('collectors') or []) != rec.get('collectors')
                or record.get('token_issuer') != rec.get('token_issuer')
                or record.get('collection_country') != rec.get('collection_country')):
            return 'recipients'
    return None


def lane_state(s=None, pol=None):
    """(lane, reason): the lane that captures right now, or (None, why not)."""
    if hub_disabled():
        return None, 'hub_off'
    if contribution_blocked():
        return None, 'env_off'
    s = s if s is not None else settings()
    req = host_request()
    if req == 'off' and s.get('host_seen') in ('stats', 'stats+phrases'):
        return None, 'host_off'         # lowered at once; hub_client writes the change later
    want = None
    if s.get('stats') == 'on':
        want = 'stats'
    elif s.get('packets') is True:
        want = 'packets'
    if want is None:
        return None, 'pending' if s.get('stats') == 'pending' else 'off'
    if install_salt(s) is None:
        return None, 'no_salt'
    pol = pol if pol is not None else policy()
    if pol['stop_collection']:
        return None, 'halt'
    if want == 'stats' and not pol['collection_open']:
        return None, 'closed'
    if want == 'packets' and not pol['lane_open']:
        return None, 'closed'
    problem = consent_problem((s.get('consent') or {}).get(want), want, pol, s)
    if problem:
        return None, problem
    return want, None


def lane():
    return lane_state()[0]


def enabled():
    """True while this install captures counts (spec 5.2). Cached by the settings mtime."""
    try:
        if hub_disabled() or contribution_blocked():
            return False
        s = settings()
        if s.get('stats') != 'on' and s.get('packets') is not True:
            return False
        marks = (_cache.get('settings') or (None,))[0], _trusted_marks(), host_request(), current_epoch()
        hit = _cache.get('enabled')
        if hit is not None and hit[0] == marks:
            return hit[1]
        value = lane_state(s)[0] is not None
        _cache['enabled'] = (marks, value)
        return value
    except Exception:
        return False


# ----------------------------------------------------------------------------- holdout (spec 5.3)


def held_out(lang, rule_or_phrase_id, severity=None):
    """True if this check runs hidden this week on this install (spec 5.3).

    severity: the check's effective severity after the overlay ('warning', 'error' or
    'shadow'); None means warning. Always False when enabled() is False and for locked rules.
    """
    try:
        if lang not in ('fa', 'en') or not enabled():
            return False
        rid = str(rule_or_phrase_id)
        pol = policy()
        hv = _hub_verify()
        if hv is not None and hv.is_locked(rid, pol['locked']):
            return False
        hm = _hub_mine()
        rate = hm.holdout_rate('shadow' if severity == 'shadow' else severity, False, pol['holdout'])
        return hm.is_held_out(install_salt(), current_epoch(), lang, rid, rate)
    except Exception:
        return False


# ----------------------------------------------------------------------------- the event log


def _events_path(epoch):
    return _p('events', '%s.jsonl' % epoch)


def _active_ids():
    """{"b": baseline id|None, "a": auto id|None} of active.json (written by hub_client)."""
    now = time.monotonic()
    hit = _cache.get('active_ids')
    if hit is not None and now - hit[0] < MARK_TTL:
        return dict(hit[1])
    doc = read_json(_p('active.json') or '', 16 * 1024) or {}
    out = {'b': None, 'a': None}
    b = (doc.get('baseline') or {}).get('id') if isinstance(doc.get('baseline'), dict) else None
    a = (doc.get('auto') or {}).get('id') if isinstance(doc.get('auto'), dict) else None
    if isinstance(b, str) and _OV_B.match(b):
        out['b'] = b
    if isinstance(a, str) and _OV_A.match(a):
        out['a'] = a
    _cache['active_ids'] = (now, dict(out))
    return out


def prune_events(now=None):
    """Delete event files older than 14 days (spec 4.5, 4.9)."""
    folder = _p('events')
    if not folder or not os.path.isdir(folder):
        return 0
    cutoff = (now or utcnow()) - datetime.timedelta(days=EVENT_MAX_AGE_DAYS)
    hm = _hub_mine()
    n = 0
    for name in os.listdir(folder):
        m = re.match(r'^([0-9]{4}-W[0-9]{2})\.jsonl$', name)
        try:
            old = (m is None) or hm.week_end(m.group(1)) < cutoff
        except Exception:
            old = True
        if old:
            try:
                os.remove(os.path.join(folder, name))
                n += 1
            except OSError:
                pass
    return n


def append_event(ev):
    """Append one event line (<= 16 KiB) to events/<epoch>.jsonl; True if written."""
    path = _events_path(ev['e'])
    if path is None:
        return False
    line = json.dumps(ev, ensure_ascii=True, separators=(',', ':'), sort_keys=False)
    if len(line.encode('utf-8')) > EVENT_MAX_LINE:
        return False
    with _lock:
        new_file = not os.path.exists(path)
        makedirs(os.path.dirname(path))
        with open(path, 'a', encoding='utf-8', newline='\n') as fh:
            fh.write(line + '\n')
        if new_file:
            prune_events()
    return True


def _issue_id(x):
    if not isinstance(x, dict):
        return None
    rid = x.get('_pid') or x.get('code') or x.get('rule')
    return rid if isinstance(rid, str) and _ID.match(rid) else None


def _split_result(result):
    """(shown issues, hidden issues) from the shapes a linter hands over."""
    if isinstance(result, dict):
        return list(result.get('issues') or []), list(result.get('hidden') or result.get('hidden_issues') or [])
    if isinstance(result, tuple):
        shown = result[0] if len(result) > 0 and isinstance(result[0], list) else []
        hidden = result[1] if len(result) > 1 and isinstance(result[1], list) else []
        return list(shown), list(hidden)
    if isinstance(result, list):
        return list(result), []
    return [], []


def _counts(issues, limit=2000):
    out = {}
    for x in issues:
        rid = _issue_id(x)
        if rid:
            out[rid] = min(out.get(rid, 0) + 1, 100000)
    if len(out) > limit:
        out = dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0]))[:limit])
    return dict(sorted(out.items()))


def record_lint(source, lang, fg, result, words):
    """One `lint` event (spec 5.2): counts by rule or phrase id, never text."""
    try:
        if source not in ('mcp', 'cli', 'hook') or lang not in ('fa', 'en'):
            return None
        if source == 'cli' and (os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS')):
            return None
        if not enabled():
            return None
        shown, hidden = _split_result(result)
        w = words if isinstance(words, int) and not isinstance(words, bool) else 0
        ev = {'t': 'lint', 'e': current_epoch(), 'src': source, 'lang': lang,
              'fg': _hub_mine().fg_of(fg), 'w': max(0, min(w, 1000000)),
              'hits': _counts(shown), 'hidden': _counts(hidden), 'ov': _active_ids()}
        while not append_event(ev) and (ev['hits'] or ev['hidden']):
            for key in ('hits', 'hidden'):      # an oversized line loses its rarest ids first
                if ev[key]:
                    ev[key] = dict(sorted(ev[key].items(), key=lambda kv: (-kv[1], kv[0]))[:len(ev[key]) // 2])
    except Exception:
        pass
    return None


def record_health(kind, reason=None, overlay_id=None):
    """One `health` event (spec 5.2); nothing unless enabled()."""
    try:
        if kind not in HEALTH_KINDS:
            return None
        if kind in HEALTH_REASONS:
            if reason not in HEALTH_REASONS[kind]:
                return None
        else:
            reason = None
        if not enabled():
            return None
        ov = overlay_id if isinstance(overlay_id, str) and (_OV_B.match(overlay_id) or _OV_A.match(overlay_id)) else None
        ev = {'t': 'health', 'e': current_epoch(), 'k': kind}
        if reason:
            ev['r'] = reason
        ev['ov'] = ov
        append_event(ev)
    except Exception:
        pass
    return None


def week_outcomes(epoch=None):
    """How many `out` events this install recorded in the week (the 20-per-week budget)."""
    path = _events_path(epoch or current_epoch())
    n = 0
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            for line in fh:
                if line.startswith('{"t":"out"'):
                    n += 1
    except (OSError, TypeError, UnicodeDecodeError):
        return 0
    return n


# ----------------------------------------------------------------------------- outcomes (spec 5.3, 5.4)


def _linters():
    try:
        import lint
        return lint
    except Exception:
        return None


def _lint_fn(lint_mod, profile, fmt):
    """lint(text, lang) -> (shown issues, hidden issues) with the active overlay and holdout."""
    ho = _hub_overlay()
    shadow = getattr(ho, 'lint_with_shadow', None) if ho is not None else None

    def run(text, lang):
        if callable(shadow):
            issues, hidden, _stats = shadow(text, lang, profile=profile, fmt=fmt)
            return list(issues), list(hidden)
        issues, _stats, _lang = lint_mod.lint_text(text, lang=lang, profile=profile, fmt=fmt)
        return list(issues), []
    return run


def _phrases_issued(lang):
    ho = _hub_overlay()
    out = {}
    try:
        ov = ho.active(lang) if ho is not None else None
        for p in (ov.phrases_added() if ov is not None else []):
            if isinstance(p, dict) and p.get('id') and p.get('issued'):
                out[p['id']] = p['issued']
    except Exception:
        pass
    return out


def _blocklist(profile):
    """Words that make a Tier 2 phrase ineligible (spec 5.4 step 3)."""
    words = set()
    prof = profile if isinstance(profile, dict) else {}
    for key in ('brand', 'brand_name', 'name'):
        v = prof.get(key)
        if isinstance(v, str):
            words.update(v.lower().split())
    for key in ('banned', 'avoid', 'prefer', 'misspellings', 'brand_spellings'):
        v = prof.get(key)
        items = v if isinstance(v, list) else (list(v) + list(v.values()) if isinstance(v, dict) else [])
        for item in items:
            if isinstance(item, str):
                words.update(item.lower().split())
    path = env('HUB_BLOCKLIST')
    if path:
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                for line in fh:
                    words.update(line.strip().lower().split())
        except (OSError, UnicodeDecodeError):
            pass
    return frozenset(w for w in words if w)


def _word_list(path):
    """One word per line, '#' starts a comment; a missing file is empty."""
    out = set()
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            for line in fh:
                w = line.split('#', 1)[0].strip()
                if w:
                    out.add(w.lower())
    except (OSError, UnicodeDecodeError):
        pass
    return out


def _tier2(lang, pol, s, profile):
    if lane() != 'stats' or s.get('phrases') is not True or not pol['discovery_open']:
        return None
    path = os.path.join(DATA_DIR, 'ngrams.%s.txt' % lang)
    sens = os.path.join(DATA_DIR, 'sensitive.%s.txt' % lang)
    key = ('ngrams', path, _mtime(path), _mtime(sens))
    idx = _cache.get(key)
    if idx is None:
        idx = _hub_mine().load_ngram_index(path, lang, _word_list(sens))
        _cache[key] = idx
    if not idx:
        return None
    return {'index': idx, 'blocklist': _blocklist(profile)}


def record_outcome(shown, final, lang='auto', fmt=None, playbook=None, revisions=None, profile=None):
    """Compute one outcome locally and append one `out` event (spec 5.3).

    Called only by mcp_server.check_final, with a `shown` text the server itself received
    through lint_text or lint_file. Returns {"recorded": bool, "reason": str|None} and never
    returns counts, ids or overlay information.
    """
    try:
        if not enabled():
            return {'recorded': False, 'reason': 'disabled'}
        if not isinstance(final, str) or (shown is not None and not isinstance(shown, str)):
            return {'recorded': False, 'reason': 'unlinted'}
        hm = _hub_mine()
        lint_mod = _linters()
        if lint_mod is None:
            return {'recorded': False, 'reason': 'unavailable'}
        s = settings()
        pol = policy()
        now = utcnow()
        epoch = current_epoch(now)
        rev = revisions if isinstance(revisions, int) and not isinstance(revisions, bool) else 0
        lang = lang if lang in ('fa', 'en') else 'auto'

        def detect(text):
            got = lint_mod.detect_lang(text)
            return got[0], got[1]

        resolved = lang
        if resolved == 'auto' and isinstance(shown, str):
            resolved = detect(shown)[0]
        ctx = {
            'salt': install_salt(s), 'epoch': epoch, 'now': now, 'lang': lang, 'format': fmt,
            'playbook': playbook if isinstance(playbook, str) else None, 'revisions': max(0, min(rev, 20)),
            'state': {'process_outcomes': _process['outcomes'], 'week_outcomes': week_outcomes(epoch),
                      'shown_available': shown is not None},
            'detect': detect, 'lint': _lint_fn(lint_mod, profile, fmt),
            'phrases_issued': _phrases_issued(resolved) if resolved in ('fa', 'en') else {},
            'params': pol.get('params') or {},
            'linters': {'fa': getattr(lint_mod, 'LF', None), 'en': getattr(lint_mod, 'LE', None)},
            'tier2': _tier2(resolved, pol, s, profile) if resolved in ('fa', 'en') else None,
        }
        res = hm.outcome_from_texts(shown, final, ctx)
        if not res.get('recorded'):
            return {'recorded': False, 'reason': res.get('reason')}
        if not append_event(res['event']):
            return {'recorded': False, 'reason': 'too_long'}
        with _lock:
            _process['outcomes'] += 1
        return {'recorded': True, 'reason': None}
    except Exception:
        return {'recorded': False, 'reason': 'error'}


# ----------------------------------------------------------------------------- MCP memory of shown texts


def _resolve_lang(text, lang):
    if lang in ('fa', 'en'):
        return lang
    lint_mod = _linters()
    if lint_mod is None:
        return None
    got = lint_mod.detect_lang(text)[0]
    return got if got in ('fa', 'en') else None


def remember(text, lang='auto'):
    """Keep a linted text in memory for check_final (only while enabled(); never on disk)."""
    try:
        if not isinstance(text, str) or not text or not enabled():
            return None
        resolved = _resolve_lang(text, lang)
        if resolved is None:
            return None
        now = time.monotonic()
        with _lock:
            _texts[:] = [t for t in _texts if now - t[0] <= TEXT_TTL]
            _texts.append((now, resolved, text))
            del _texts[:-TEXT_SLOTS]
    except Exception:
        pass
    return None


def recall(lang):
    """The most recent remembered text in `lang` from the last 6 hours, or None."""
    try:
        now = time.monotonic()
        with _lock:
            _texts[:] = [t for t in _texts if now - t[0] <= TEXT_TTL]
            for t in reversed(_texts):
                if t[1] == lang:
                    return t[2]
    except Exception:
        pass
    return None


def forget_texts():
    with _lock:
        del _texts[:]


def check_final_outcome(final, lang='auto', fmt=None, playbook=None, revisions=None, profile=None):
    """What mcp_server.check_final calls after its final lint (spec 5.3 trigger)."""
    try:
        if not enabled():
            return {'recorded': False, 'reason': 'disabled'}
        resolved = _resolve_lang(final, lang)
        shown = recall(resolved) if resolved else None
        return record_outcome(shown, final, resolved or 'auto', fmt, playbook, revisions, profile)
    except Exception:
        return {'recorded': False, 'reason': 'error'}


if __name__ == '__main__':
    sys.stdout.write(__doc__)
