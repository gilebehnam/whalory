#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hub_overlay: the verified Whalory Hub overlay, applied inside the linters (spec 5.8, 5.9, 7.4, 7.5).

Standard library only, Python 3.8 to 3.14. Read-only: it opens no socket, writes no file
and starts no process. No public function raises into a linter or the MCP server; on any
failure the linters fall back to their built-in rules.

For the linters (lint_fa, lint_en, lint.py):

    active(lang) -> Overlay | None      None if WHALORY_HUB=0, WHALORY_HUB_OVERLAY=0, --no-overlay,
                                        or nothing valid. Cached by the (mtime, size) of active.json
                                        and the trusted metadata, and re-verified from the pinned root
                                        when one changes (checked at most every 2 seconds).
    Overlay.id -> {"baseline": str|None, "auto": str|None, "stale": bool}
    Overlay.severity(rule_or_phrase_id) -> "shadow" | "warning" | "error" | "off" | None
    Overlay.param(name, default) -> number
    Overlay.phrases_added() -> [{"id", "phrase", "state", "issued"}]      literal strings
    Overlay.channel(channel_id, field) -> dict | None
    apply_issues(lang, issues) -> issues   severity override, holdout, hidden findings moved out
    stamp_stats(lang, stats) -> stats      adds stats["rules_version"] while an overlay is active
    param(lang, name, default) -> number   the overlay default of a tunable parameter
    channel_update(channel_id, field) -> dict | None
    hub_phrases(lang) -> [(phrase, id, state)]  the hub phrases the linters match (longest first)
    lint_with_shadow(text, lang='auto', **settings) -> (issues, hidden_issues, stats)
    note_exception() -> None               spec 5.8 step 10 (fallback, overlay_exception, revert)
    set_cli_disabled(flag)                 --no-overlay
    register(lang, module)                 each linter registers itself on import

For hub_client (activation, spec 5.8 steps 7 to 9):

    decide(sync_result, active_record, now=None, ...) -> Decision
    check_caps(overlay, ctx) -> {"result", "code", "path", "changes"}     spec 7.5, vectors/caps.json
    make_context(baseline_overlay, policy, lists=None, ...) -> ctx for check_caps
    self_test(baseline_overlay, auto_overlay, policy=None) -> (ok, detail)
    configure(hub_home=None, data_dir=None, skill_version=None, now=None, test=False)
                                           (hub_client --hub-home and --test, the tests)
    parse_active(data) -> dict             the active record, strictly checked

Hidden findings (shadow and held out) never reach text output, JSON output, MCP output,
exit codes or counts: apply_issues() removes them, and only lint_with_shadow() returns them,
with the internal fields _pid (phrase id), _level and _end (end column) kept for hub_mine.
Nothing from the Hub is ever shown except as part of the user's own excerpt: hub phrases are
reported under the fixed messages of the rules hub-tell and en-hub-tell.

The active record (active.json, written by hub_client from Decision.active_bytes):
    {"schema": "whalory.active/1", "activated": "<UTC time>",
     "baseline": {"id", "target", "sha256"}, "auto": {"id", "target", "sha256", "role", "prev"} | null,
     "pin": null | "baseline" | "bundled", "previous": [{"baseline": {...}, "auto": {...} | null}]}
A target it names is used only when its hash equals the entry of the verified baseline.json
or auto.json, the release is not revoked, compat.skill fits and the content checks pass.

Where the overlay comes from, in order: the Hub folder (active.json), else the bundled set of
the release (SKILL/data/hub/bundled/, the baseline overlay and the stable auto overlay), else
nothing. Overlays that change nothing (no severity, parameter, phrase or channel entry) are
applied without checking signatures, since there is nothing to apply; every other overlay is
re-verified from the pinned root SKILL/data/hub/root.json. A pinned root that lists one of the
public test keys (hub_verify.TEST_KEY_IDS) verifies nothing outside test mode.
"""
from __future__ import print_function

import contextlib
import datetime
import json
import os
import re
import sys
import threading
import time

__all__ = ['active', 'Overlay', 'apply_issues', 'stamp_stats', 'param', 'channel_update', 'channel_updates',
           'hub_phrases', 'rules_rows', 'lint_with_shadow', 'note_exception', 'set_cli_disabled', 'register',
           'disabled', 'decide', 'Decision', 'check_caps', 'make_context', 'self_test', 'configure', 'parse_active',
           'load_lists', 'builtin_severities', 'lexicon_ids', 'channel_keys', 'effective_percent', 'LADDER',
           'PHRASE_LIST_RULES', 'HUB_RULE', 'HUB_MESSAGE']

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
UTC = datetime.timezone.utc

LADDER = {'shadow': 0, 'warning': 1, 'error': 2}
#: The phrase-list rules of spec 3; their findings are attributed to lx- ids.
PHRASE_LIST_RULES = {
    'fa': ('lexicon',),
    'en': ('en-ai-vocab', 'en-buzzword', 'en-cliche-open', 'en-journey', 'en-moral-close', 'en-clickbait'),
}
HUB_RULE = {'fa': 'hub-tell', 'en': 'en-hub-tell'}
HUB_MESSAGE = {'fa': 'عبارتِ کلیشه‌ای که هوش مصنوعی زیاد می‌نویسد؛ بازنویسی کن',
               'en': 'Stock phrase that AI writes often; rewrite it'}
COMMON_WORDS = 2000              # a one-word hub phrase among these vocabulary words is refused
_FALSE = ('0', 'false', 'off', 'no')
_STAT_EVERY = 2.0                # seconds between checks of active.json in a long-running process
_ACTIVE_MAX = 16 * 1024

_conf = {'hub_home': None, 'data_dir': None, 'skill_version': None, 'now': None, 'test': False}
_cli = {'off': False}
_lock = threading.RLock()
_tls = threading.local()
_cache = {}
_linters = {}
_errors = {'day': None, 'count': 0, 'reverted': False}


# ----------------------------------------------------------------------------- configuration


def _env(name):
    v = os.environ.get('WHALORY_' + name)
    if v is None:
        v = os.environ.get('WHALYA_' + name)          # former name, read only
    return (v or '').strip().lower()


def disabled():
    """True when the overlay is off: WHALORY_HUB=0, WHALORY_HUB_OVERLAY=0 or --no-overlay."""
    return _cli['off'] or _env('HUB') in _FALSE or _env('HUB_OVERLAY') in _FALSE


def set_cli_disabled(flag):
    """--no-overlay for this process (lint.py, lint_fa.py and lint_en.py set it from their flags)."""
    with _lock:
        _cli['off'] = bool(flag)


def configure(hub_home=None, data_dir=None, skill_version=None, now=None, test=False):
    """Point the module at another Hub folder or data folder (hub_client --hub-home, tests).
    test=True accepts a pinned root made of the public test keys (hub_client --test only).
    There is no environment variable for any of this (spec 5.10). Clears every cache."""
    with _lock:
        _conf.update(hub_home=hub_home, data_dir=data_dir, skill_version=skill_version, now=now, test=bool(test))
        _cache.clear()
        _errors.update(day=None, count=0, reverted=False)


def _test_mode():
    if _conf['test']:
        return True
    he = sys.modules.get('hub_events')
    try:
        return bool(he is not None and he.test_mode())
    except Exception:
        return False


def _data_dir():
    return _conf['data_dir'] or os.path.join(SKILL_ROOT, 'data', 'hub')


def _default_hub_home():
    if sys.platform.startswith('win'):
        base = os.environ.get('LOCALAPPDATA') or os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
        return os.path.join(base, 'Whalory', 'hub')
    if sys.platform == 'darwin':
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Whalory', 'hub')
    base = os.environ.get('XDG_STATE_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'state')
    return os.path.join(base, 'whalory', 'hub')


def _hub_home():
    if _conf['hub_home']:
        return _conf['hub_home']
    he = sys.modules.get('hub_events')
    if he is not None:
        try:
            return he.hub_home()
        except Exception:
            return None
    return _default_hub_home()


def _now():
    n = _conf['now']
    if n is None:
        return datetime.datetime.now(UTC).replace(microsecond=0)
    if isinstance(n, str):
        return datetime.datetime.strptime(n, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=UTC)
    return n


def _skill_version():
    if _conf['skill_version']:
        return _conf['skill_version']
    got = _cache.get('skill_version')
    if got is None:
        got = '3.0.0'
        try:
            with open(os.path.join(SKILL_ROOT, 'VERSION'), 'r', encoding='utf-8') as fh:
                v = fh.read(64).strip()
            if re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', v):
                got = v
        except (IOError, OSError, UnicodeDecodeError):
            pass
        _cache['skill_version'] = got
    return got


def register(lang, module):
    """Each linter registers itself when it is imported (rule_list and LEXICON)."""
    _linters[lang] = module


def _linter(lang):
    mod = _linters.get(lang)
    if mod is None:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import importlib
        mod = importlib.import_module('lint_fa' if lang == 'fa' else 'lint_en')
        _linters[lang] = mod
    return mod


def _hv():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import hub_verify
    return hub_verify


def _events():
    """hub_events, when it is there and the Hub folder exists (it records health and the holdout)."""
    mod = sys.modules.get('hub_events')
    if mod is None:
        if 'events_missing' in _cache:
            return None
        home = _hub_home()
        if not home or not os.path.isdir(home):
            return None
        try:
            if HERE not in sys.path:
                sys.path.insert(0, HERE)
            import hub_events as mod
        except Exception:
            _cache['events_missing'] = True
            return None
    return mod


def _health(kind, reason=None, overlay_id=None):
    mod = _events()
    if mod is not None:
        try:
            mod.record_health(kind, reason, overlay_id)
        except Exception:
            pass


# ----------------------------------------------------------------------------- lists (spec 5.1, 7.5)


def load_lists(lang, data_dir=None):
    """{"vocab", "stop", "sensitive", "common"} sets from SKILL/data/hub/{vocab,stop,sensitive}.<lang>.txt.

    One entry per line, '#' starts a comment; vocab.<lang>.txt lists words by descending
    frequency, and its first 2,000 entries are the common words of the one-word rule. A
    missing file gives an empty set, so every hub phrase then fails the phrase gates.
    """
    folder = data_dir or _data_dir()
    key = ('lists', folder, lang)
    got = _cache.get(key)
    if got is not None:
        return got
    out = {}
    for name in ('vocab', 'stop', 'sensitive'):
        words = []
        try:
            with open(os.path.join(folder, '%s.%s.txt' % (name, lang)), 'r', encoding='utf-8') as fh:
                for line in fh:
                    w = line.split('#', 1)[0].strip()
                    if w:
                        words.append(w.lower() if lang == 'en' else w)
        except (IOError, OSError, UnicodeDecodeError):
            words = []
        out[name] = words
    lists = {'vocab': set(out['vocab']), 'stop': set(out['stop']), 'sensitive': set(out['sensitive']),
             'common': set(out['vocab'][:COMMON_WORDS])}
    _cache[key] = lists
    return lists


# ----------------------------------------------------------------------------- the overlay


class Overlay(object):
    """The effective overlay of one language: baseline overlay, then auto overlay (spec 7.4)."""

    def __init__(self, state, lang):
        self._s = state
        self.lang = lang
        self.id = {'baseline': state.ids[0], 'auto': state.ids[1], 'stale': state.stale}
        self._sev = state.severity.get(lang, {})
        self._params = state.params.get(lang, {})
        self._phrases = state.phrases.get(lang, [])

    def severity(self, rule_or_phrase_id):
        return self._sev.get(rule_or_phrase_id)

    def param(self, name, default):
        v = self._params.get(name)
        return default if v is None else v

    def phrases_added(self):
        return [dict(p) for p in self._phrases]

    def channel(self, channel_id, field):
        got = self._s.channels.get('%s.%s' % (channel_id, field))
        return dict(got) if got else None

    def has_effect(self):
        return bool(self._sev or self._params or self._phrases or self._s.channels)


class _State(object):
    """Merged, verified overlays: severity {lang: {id: level}} (phrase states included), params,
    phrases {lang: [{"id", "phrase", "state", "issued"}]}, channels, ids and the stale flag."""

    def __init__(self, baseline=None, auto=None, stale=False, policy=None, source='hub'):
        self.docs = (baseline, auto)
        self.ids = (baseline['id'] if baseline else None, auto['id'] if auto else None)
        self.stale = bool(stale)
        self.policy = policy
        self.source = source
        self.severity, self.params, self.phrases, self.channels = {}, {}, {}, {}
        for doc in (baseline, auto):
            if not doc:
                continue
            for lang, block in doc['lang'].items():
                sev = self.severity.setdefault(lang, {})
                sev.update(block['severity'])
                self.params.setdefault(lang, {}).update(block['params'])
                ph = dict((p['id'], p) for p in self.phrases.get(lang, []))
                for p in block['phrases']:
                    old = ph.get(p['id'])
                    ph[p['id']] = {'id': p['id'], 'phrase': p['phrase'], 'state': p['state'],
                                   'issued': old['issued'] if old else doc['issued']}
                self.phrases[lang] = sorted(ph.values(), key=lambda p: (-len(p['phrase']), p['id']))
                for p in self.phrases[lang]:
                    sev[p['id']] = p['state']
            for key, ch in doc['channels'].items():
                self.channels.setdefault(key, {}).update(ch)
        self.views = {}

    def view(self, lang):
        v = self.views.get(lang)
        if v is None:
            v = self.views[lang] = Overlay(self, lang)
        return v

    def has_effect(self):
        return any(self.view(lang).has_effect() for lang in ('fa', 'en'))


def _empty(doc):
    return not doc['channels'] and all(not (b['severity'] or b['params'] or b['phrases']) for b in doc['lang'].values())


def active(lang):
    """The Overlay of lang, or None (see the module docs); never raises."""
    try:
        st = _state()
        return st.view(lang) if st is not None else None
    except Exception:
        return None


def _state():
    forced = getattr(_tls, 'forced', None)
    if forced is not None:
        return forced
    if disabled():
        return None
    now = time.monotonic()
    hit = _cache.get('state')
    if hit is not None and now - hit[0] < _STAT_EVERY:
        return hit[2]
    home = _hub_home()
    mark = _mark(home)
    if hit is not None and hit[1] == mark:
        _cache['state'] = (now, mark, hit[2])
        return hit[2]
    with _lock:
        st = _build(home, mark)
        if _errors['reverted'] and st is not None and st.docs[1] is not None and st.source != 'previous':
            st = _State(st.docs[0], None, st.stale, st.policy, st.source)
        _cache['state'] = (now, mark, st)
    return st


def _mark(home):
    """(mtime, size) of active.json, the trusted metadata and the bundled set: any change re-verifies."""
    out = []
    paths = [os.path.join(home, 'active.json')] + [os.path.join(home, 'trusted', n) for n in
                                                    ('timestamp.json', 'auto.json', 'halt.json')] if home else []
    paths.append(os.path.join(_data_dir(), 'bundled', 'baseline.json'))
    for p in paths:
        try:
            s = os.stat(p)
            out.append((s.st_mtime_ns, s.st_size))
        except OSError:
            out.append(None)
    return tuple(out)


def _read(path, cap):
    try:
        with open(path, 'rb') as fh:
            data = fh.read(cap + 1)
    except (IOError, OSError):
        return None
    return data if len(data) <= cap else None


_ID_B = re.compile(r'b-[0-9]{4}\.(0[1-9]|1[0-2])\.[1-9][0-9]{0,2}')
_ID_A = re.compile(r'a-[0-9]{4}w(0[1-9]|[1-4][0-9]|5[0-3])\.[1-9][0-9]{0,2}')
_SHA = re.compile(r'[0-9a-f]{64}')
_TIME = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z')


def _target_ref(x, kind):
    if not isinstance(x, dict):
        return False
    rx = _ID_B if kind == 'baseline' else _ID_A
    keys = {'id', 'target', 'sha256'} if kind == 'baseline' else {'id', 'target', 'sha256', 'role', 'prev'}
    if set(x) != keys or not isinstance(x['id'], str) or not rx.fullmatch(x['id']):
        return False
    if x['target'] != '%s/overlay-%s.json' % (kind, x['id']) or not _SHA.fullmatch(str(x['sha256'])):
        return False
    if kind == 'auto':
        if x['role'] not in ('candidate', 'stable', 'previous'):
            return False
        if x['prev'] is not None and not (isinstance(x['prev'], str) and _ID_A.fullmatch(x['prev'])):
            return False
    return True


def parse_active(data):
    """The active record (see the module docs), strictly checked; raises ValueError."""
    hv = _hv()
    try:
        doc = hv.loads(data, max_bytes=_ACTIVE_MAX)
    except hv.HubError as e:
        raise ValueError(e.code)
    if set(doc) != {'schema', 'activated', 'baseline', 'auto', 'pin', 'previous'}:
        raise ValueError('active record keys')
    if doc['schema'] != 'whalory.active/1' or not isinstance(doc['activated'], str) or \
            not _TIME.fullmatch(doc['activated']):
        raise ValueError('active record header')
    if not _target_ref(doc['baseline'], 'baseline'):
        raise ValueError('active baseline')
    if doc['auto'] is not None and not _target_ref(doc['auto'], 'auto'):
        raise ValueError('active auto')
    if doc['pin'] not in (None, 'baseline', 'bundled'):
        raise ValueError('active pin')
    prev = doc['previous']
    if not isinstance(prev, list) or len(prev) > 2:
        raise ValueError('active previous')
    for p in prev:
        if not isinstance(p, dict) or set(p) != {'baseline', 'auto'} or not _target_ref(p['baseline'], 'baseline') \
                or (p['auto'] is not None and not _target_ref(p['auto'], 'auto')):
            raise ValueError('active previous entry')
    return doc


def _build(home, mark):
    """The state for the Hub folder, else the bundled set, else None; never raises."""
    rec = None
    raw = _read(os.path.join(home, 'active.json'), _ACTIVE_MAX) if home else None
    if raw is not None:
        try:
            rec = parse_active(raw)
        except Exception:
            _health('verify_fail', 'local')
            rec = None
    if rec is not None and _errors['reverted']:
        # spec 5.8 step 10: after 3 overlay exceptions today, the previous active overlays
        if rec['previous']:
            try:
                st = _from_hub(home, dict(rec, baseline=rec['previous'][0]['baseline'],
                                          auto=rec['previous'][0]['auto']))
                if st is not None:
                    st.source = 'previous'
                    return st
            except Exception:
                pass
    if rec is not None and rec.get('pin') != 'bundled':
        try:
            st = _from_hub(home, rec)
            if st is not None:
                return st
        except Exception:
            _health('verify_fail', 'local')
    try:
        return _from_bundled()
    except Exception:
        _health('verify_fail', 'local')
        return None


def _load_target(read, sha, entry=None):
    hv = _hv()
    data = read('targets/%s.json' % sha, hv.MAX_BYTES['overlay-1'])
    if data is None:
        raise hv.HubError('not_found', 'targets/%s.json' % sha)
    if entry is None:
        entry = {'sha256': sha, 'length': len(data)}
    return hv.check_target(data, entry)


def _pinned_root():
    """The pinned root's bytes, or None when it is missing, or when it lists a public test key
    outside test mode (then nothing it verifies is applied)."""
    data = _read(os.path.join(_data_dir(), 'root.json'), 64 * 1024)
    if data is None or _test_mode():
        return data
    hv = _hv()
    try:
        env = hv.loads(data, max_bytes=64 * 1024)
        root = hv.loads(hv.b64std_decode(env['payload']))
    except Exception:
        return None
    return None if hv.is_test_root(root) else data


def _state_rules(home):
    raw = _read(os.path.join(home, 'state.json'), 1024 * 1024)
    if raw is None:
        return {}
    try:
        doc = json.loads(raw.decode('utf-8'))
        rules = doc.get('rules') if isinstance(doc, dict) else None
        return rules if isinstance(rules, dict) else {}
    except (ValueError, UnicodeDecodeError):
        return {}


def _from_hub(home, rec):
    hv = _hv()
    read = hv.reader(home, 'hub')
    base_doc = _load_target(read, rec['baseline']['sha256'])
    auto_doc = _load_target(read, rec['auto']['sha256']) if rec['auto'] else None
    if rec['pin'] == 'baseline':
        auto_doc = None
    if base_doc['kind'] != 'baseline' or base_doc['id'] != rec['baseline']['id']:
        raise hv.HubError('mismatch', 'active baseline')
    if auto_doc is not None and (auto_doc['kind'] != 'auto' or auto_doc['id'] != rec['auto']['id']):
        raise hv.HubError('mismatch', 'active auto')
    if _empty(base_doc) and (auto_doc is None or _empty(auto_doc)):
        return _State(base_doc, auto_doc, source='hub')        # nothing to apply: no need to verify
    pinned = _pinned_root()
    if pinned is None:
        return None
    snap = hv.load_snapshot(read, pinned, now=_now(), rules=_state_rules(home), check_pinned=False)
    if snap.halt_active():
        if snap.halt.get('pin') == 'bundled':
            return None
        auto_doc = None
    entry = snap.target_entry(rec['baseline']['target'])
    if entry is None or entry['sha256'] != rec['baseline']['sha256']:
        raise hv.HubError('mismatch', 'the active baseline is not in the verified baseline.json')
    version = _skill_version()
    if not hv.compat_ok(base_doc['compat']['skill'], version):
        return None
    if auto_doc is not None:
        entry = snap.target_entry(rec['auto']['target'])
        ok = (entry is not None and entry['sha256'] == rec['auto']['sha256'] and entry.get('role') != 'registry'
              and auto_doc['id'] not in snap.revoked and auto_doc['base'] == base_doc['id']
              and hv.compat_ok(auto_doc['compat']['skill'], version))
        if ok:
            got = check_caps(auto_doc, make_context(base_doc, snap.baseline['policy']), stateless=True)
            if got['result'] != 'accept':
                _health('cap_reject', 'violation', auto_doc['id'])
                ok = False
        if not ok:
            auto_doc = None
    return _State(base_doc, auto_doc, snap.stale, snap.baseline['policy'], 'hub')


def _from_bundled():
    """The bundled set of this release (SKILL/data/hub/bundled/, mirror layout): its baseline
    overlay and its stable auto overlay. Verified from the pinned root unless both are empty."""
    folder = os.path.join(_data_dir(), 'bundled')
    if not os.path.isdir(folder):
        return None
    hv = _hv()
    read = hv.reader(folder, 'mirror')
    targets = {}
    for role in ('baseline', 'auto'):
        raw = read(role + '.json', hv.MAX_BYTES['envelope.' + role])
        if raw is None:
            continue
        env = hv.loads(raw, max_bytes=hv.MAX_BYTES['envelope.' + role])
        body = hv.loads(hv.b64std_decode(env['payload']))
        targets[role] = body.get('targets') or {}
    base_path = None
    for path in sorted(targets.get('baseline', {}), key=hv._baseline_key, reverse=True):
        base_path = path
        break
    if base_path is None:
        return None
    base_doc = _load_target(read, targets['baseline'][base_path]['sha256'], targets['baseline'][base_path])
    auto_path = None
    for path, t in sorted(targets.get('auto', {}).items()):
        if t.get('role') == 'stable':
            auto_path = path
    auto_doc = _load_target(read, targets['auto'][auto_path]['sha256'], targets['auto'][auto_path]) \
        if auto_path else None
    if _empty(base_doc) and (auto_doc is None or _empty(auto_doc)):
        return _State(base_doc, auto_doc, source='bundled')
    pinned = _pinned_root()
    if pinned is None:
        return None
    snap = hv.load_snapshot(read, pinned, now=_now(), check_pinned=False)
    version = _skill_version()
    entry = snap.target_entry(base_path)
    if entry is None or entry['sha256'] != targets['baseline'][base_path]['sha256'] or \
            not hv.compat_ok(base_doc['compat']['skill'], version):
        return None
    if auto_doc is not None:
        entry = snap.target_entry(auto_path)
        ok = (entry is not None and entry['sha256'] == targets['auto'][auto_path]['sha256']
              and auto_doc['base'] == base_doc['id'] and auto_doc['id'] not in snap.revoked
              and hv.compat_ok(auto_doc['compat']['skill'], version))
        if ok:
            ok = check_caps(auto_doc, make_context(base_doc, snap.baseline['policy']),
                            stateless=True)['result'] == 'accept'
        if not ok:
            auto_doc = None
    return _State(base_doc, auto_doc, snap.stale, snap.baseline['policy'], 'bundled')


# ----------------------------------------------------------------------------- inside the linters


def _strip(x):
    x.pop('_pid', None)
    x.pop('_end', None)
    x.pop('_level', None)
    return x


_ORDER = {'error': 0, 'warning': 1}


def apply_issues(lang, issues):
    """Map each finding through the overlay severity and the measurement holdout (spec 5.9).

    'off' drops a finding; 'shadow' and held-out findings leave the list (lint_with_shadow
    collects them); 'warning' and 'error' replace the level. Phrase-list findings are looked
    up by their phrase id first, then by the rule id. Internal fields are removed unless
    lint_with_shadow is collecting. Never raises: on an error the built-in findings come back.
    """
    collector = getattr(_tls, 'collector', None)
    try:
        st = _state()
        ev = None
        if getattr(_tls, 'forced', None) is None and not disabled():
            ev = _events()          # the holdout; never during a self-test, never with the overlay off
            try:
                if ev is not None and not ev.enabled():
                    ev = None       # one check per call: held_out() is always False while capture is off
            except Exception:
                ev = None
        if st is None and ev is None:
            if collector is None:
                for x in issues:
                    _strip(x)
            else:
                for x in issues:
                    x['_level'] = x['level']
            return issues
        ov = st.view(lang) if st is not None else None
        held = getattr(ev, 'held_out', None) if ev is not None else None
        out, resort = [], False
        for x in issues:
            pid = x.get('_pid')
            rid = pid or x['code']
            sev = None
            if ov is not None:
                sev = ov.severity(pid) if pid else None
                if sev is None:
                    sev = ov.severity(x['code'])
            if sev == 'off':
                continue
            level = sev if sev in ('warning', 'error') else x['level']
            hidden = sev == 'shadow'
            if not hidden and held is not None:
                try:
                    hidden = bool(held(lang, rid, level))
                except Exception:
                    hidden = False
            if hidden:
                if collector is not None:
                    y = dict(x)
                    y['_level'] = 'shadow' if sev == 'shadow' else level
                    y['level'] = y['severity'] = level
                    collector.append(y)
                continue
            if level != x['level']:
                x['level'] = x['severity'] = level
                resort = True
            if collector is None:
                _strip(x)
            else:
                x['_level'] = level
            out.append(x)
        if resort:
            out.sort(key=lambda x: (_ORDER.get(x['level'], 1), x['line'] or 0, x.get('key') or '', x['col'] or 0))
        return out
    except Exception:
        note_exception()
        return [x if collector is not None else _strip(x) for x in issues
                if not str(x.get('_pid', '')).startswith('ht-')]


def stamp_stats(lang, stats):
    """stats.rules_version = {"baseline", "auto", "stale"} while an overlay is active (spec 5.9)."""
    try:
        ov = active(lang)
        if ov is not None:
            stats['rules_version'] = dict(ov.id)
    except Exception:
        pass
    return stats


def param(lang, name, default):
    """The overlay default of a parameter (lang-local name such as 'long-sentence.max_words'),
    kept inside the baseline policy's [min, max]; the built-in default otherwise. Never raises."""
    try:
        st = _state()
        if st is None:
            return default
        v = st.view(lang).param(name, None)
        if v is None:
            return default
        spec = ((st.policy or {}).get('params') or {}).get('%s:%s' % (lang, name))
        if spec is not None and not (spec['min'] <= v <= spec['max']):
            return default
        if type(default) is int and float(v).is_integer():
            v = int(v)
        return v
    except Exception:
        return default


def channel_update(channel_id, field):
    """The overlay's update of one shipped channel field ({max_chars, status, verified_on,
    checked_on}), or None. Never raises."""
    try:
        st = _state()
        if st is None:
            return None
        got = st.channels.get('%s.%s' % (channel_id, field))
        return dict(got) if got else None
    except Exception:
        return None


def channel_updates():
    """{"<channel>.<field>": update} of the active overlays (empty without one). Never raises."""
    try:
        st = _state()
        return dict((k, dict(v)) for k, v in st.channels.items()) if st is not None else {}
    except Exception:
        return {}


def hub_phrases(lang):
    """[(phrase, ht id, state)] of lang, longest first; the linters compile them literally
    (re.escape inside their word-boundary helper, spec 7.5). Never raises."""
    try:
        st = _state()
        if st is None:
            return []
        return [(p['phrase'], p['id'], p['state']) for p in st.phrases.get(lang, [])]
    except Exception:
        return []


def note_exception():
    """An exception attributable to the overlay (spec 5.8 step 10): record overlay_exception,
    and after 3 in one day switch this process back to the previous active overlays of
    active.json (when they still verify; else to the baseline overlay alone) and record revert.
    hub_overlay writes nothing, so the switch lasts for this process; hub_client makes it
    lasting (rollback)."""
    try:
        day = datetime.datetime.now(UTC).date()
        with _lock:
            if _errors['day'] != day:
                _errors.update(day=day, count=0)
            _errors['count'] += 1
            revert = _errors['count'] >= 3 and not _errors['reverted']
            if revert:
                _errors['reverted'] = True
                _cache.pop('state', None)
        _health('overlay_exception')
        if revert:
            _health('revert')
    except Exception:
        pass


@contextlib.contextmanager
def _collecting():
    prev = getattr(_tls, 'collector', None)
    _tls.collector = []
    try:
        yield _tls.collector
    finally:
        _tls.collector = prev


def lint_with_shadow(text, lang='auto', **settings):
    """(issues, hidden_issues, stats) of lint.lint_text with the active overlay and the holdout.

    Both lists keep the internal fields _pid (lx- or ht- phrase id), _level and _end; hidden
    findings are the shadow and held-out ones and never reach any output (spec 5.3, 5.9).
    """
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import lint
    with _collecting() as hidden:
        issues, stats, _lang = lint.lint_text(text, lang=lang, **settings)
        return issues, list(hidden), stats


@contextlib.contextmanager
def _using(baseline_overlay, auto_overlay=None, policy=None):
    """Apply these overlay documents in this thread only (self-test before activation)."""
    prev = getattr(_tls, 'forced', None)
    _tls.forced = _State(baseline_overlay, auto_overlay, False, policy, 'test')
    try:
        yield _tls.forced
    finally:
        _tls.forced = prev


@contextlib.contextmanager
def _without():
    prev = getattr(_tls, 'forced', None)
    _tls.forced = _State(None, None, False, None, 'none')
    try:
        yield
    finally:
        _tls.forced = prev


def rules_rows(lang, rows):
    """The rows of `--rules --json` with the overlay shown: overridden severities (severity
    becomes the effective one, builtin_severity keeps the built-in), and one row for the hub
    phrases when there are any. Rows without an overlay come back unchanged. Never raises."""
    try:
        ov = active(lang)
        if ov is None:
            return rows
        out = []
        for r in rows:
            sev = ov.severity(r['id'])
            if sev in ('shadow', 'warning', 'error', 'off') and sev != r['severity']:
                r = dict(r, builtin_severity=r['severity'], severity=sev)
            out.append(r)
        phrases = ov.phrases_added()
        if phrases:
            row = {'id': HUB_RULE[lang], 'severity': 'warning', 'kind': 'hub', 'description': HUB_MESSAGE[lang],
                   'phrases': [{'id': p['id'], 'phrase': p['phrase'], 'state': p['state']} for p in phrases]}
            if lang == 'en':
                row.update(ref='HUB', fix='Rewrite it in plain words, or state the fact')
            out.append(row)
        return out
    except Exception:
        return rows


# ----------------------------------------------------------------------------- caps (spec 5.8 step 7, 7.5)


class _Reject(Exception):
    def __init__(self, result, code=None, path=None):
        Exception.__init__(self, result)
        self.result, self.code, self.path = result, code, path


def _frac(v):
    from fractions import Fraction
    return Fraction(repr(v)) if isinstance(v, float) else Fraction(v)


def _ptime(s):
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=UTC)


def _locked(ident, locked):
    hv = _hv()
    return any(hv.glob_match(p, ident) for p in locked)


def _phrase_tokens(lang, phrase):
    return [w.lower() if lang == 'en' else w for w in phrase.split(' ')]


def make_context(baseline_overlay, policy, lists=None, builtin=None, lexicon=None, channels=None,
                 active_auto=None, prev_release=None, state=None, now=None, strict_ids=False):
    """The ctx of check_caps, built from this client (see check_caps for the keys). Missing
    parts come from the linters (built-in severities and lexicon ids), SKILL/data/hub (lists)
    and SKILL/data/channels (channel keys), all loaded only when a check needs them."""
    return {'baseline_overlay': baseline_overlay, 'policy': policy, 'lists': lists, 'builtin': builtin,
            'lexicon': lexicon, 'channels': channels, 'active_auto': active_auto, 'prev_release': prev_release,
            'state': state or {}, 'now': now, 'strict_ids': strict_ids}


def builtin_severities():
    """{lang: {rule id: built-in severity}} from the linters' rule tables."""
    got = _cache.get('builtin')
    if got is None:
        got = dict((lang, dict((r['id'], r['severity']) for r in _linter(lang).rule_list())) for lang in ('fa', 'en'))
        _cache['builtin'] = got
    return got


def lexicon_ids():
    """{lang: {lx id: umbrella rule}} of the built-in phrase lists (as tools/registry.py builds them)."""
    got = _cache.get('lexicon')
    if got is None:
        hv = _hv()
        got = {}
        for lang in ('fa', 'en'):
            lex = getattr(_linter(lang), 'LEXICON', {}) or {}
            got[lang] = dict((hv.lx_id(lang, cat, phrase), 'lexicon' if lang == 'fa' else 'en-' + cat)
                             for cat in lex for phrase in lex[cat])
        _cache['lexicon'] = got
    return got


def channel_keys():
    """Every shipped "<channel>.<field>" of SKILL/data/channels."""
    got = _cache.get('channel_keys')
    if got is None:
        got = set()
        folder = os.path.join(SKILL_ROOT, 'data', 'channels')
        try:
            names = sorted(os.listdir(folder))
        except OSError:
            names = []
        for name in names:
            if not name.endswith('.json'):
                continue
            try:
                with open(os.path.join(folder, name), 'r', encoding='utf-8') as fh:
                    d = json.load(fh)
                for cid, ch in d['channels'].items():
                    got.update('%s.%s' % (cid, f) for f in ch.get('fields') or {})
            except (IOError, OSError, ValueError, KeyError, TypeError, AttributeError):
                continue
        _cache['channel_keys'] = got
    return got


def _ctx_part(ctx, key):
    v = ctx.get(key)
    if v is None:
        if key == 'builtin':
            v = builtin_severities()
        elif key == 'lexicon':
            v = lexicon_ids()
        elif key == 'channels':
            v = channel_keys()
        elif key == 'lists':
            v = {'fa': load_lists('fa'), 'en': load_lists('en')}
        ctx[key] = v
    return v


def effective_percent(percent, first_seen, now, rolling):
    """Dwell times of spec 7.5 (the same function as hub_verify.effective_percent)."""
    return _hv().effective_percent(percent, first_seen, now, rolling)


def check_caps(overlay, ctx, stateless=False):
    """The client caps and content checks on an auto overlay (spec 5.8 step 7, 7.5), in the
    order of STUDIO/hub/contracts/tools/caps_ref.py, reproducing vectors/caps.json.

    ctx keys: baseline_overlay, policy (of the verified baseline.json), builtin, lexicon,
    lists ({lang: {vocab, stop, sensitive, common}}), channels (shipped keys), active_auto
    (the active auto overlay or None), prev_release (the prev of the target entry), state
    ({"activations": [...]}, the "rules" object of state.json), now (UTC time string),
    strict_ids (the pipeline gate). stateless=True runs steps 1 to 6 only (the checks that
    need no history: re-verification at load and a fall back to stable).

    Returns {"result": accept|accept_gap|reject|defer, "code", "path", "changes"}.
    A baseline overlay is signed offline and is not capped (accept).
    """
    try:
        changes = _check(overlay, ctx, stateless)
    except _Reject as r:
        return {'result': r.result, 'code': r.code, 'path': r.path, 'changes': None}
    return {'result': changes.pop('_result'), 'code': changes.pop('_code'), 'path': changes.pop('_path'),
            'changes': changes}


def _base_severity(ctx, lang, ident):
    bo = ctx['baseline_overlay']['lang'].get(lang, {}).get('severity', {})
    if ident in bo:
        return bo[ident]
    if ident.startswith('lx-'):
        umbrella = _ctx_part(ctx, 'lexicon')[lang][ident]
        return bo.get(umbrella, _ctx_part(ctx, 'builtin')[lang][umbrella])
    return _ctx_part(ctx, 'builtin')[lang][ident]


def _known(ctx, lang, ident):
    return ident in _ctx_part(ctx, 'builtin')[lang] or ident in _ctx_part(ctx, 'lexicon')[lang]


def _check(ov, ctx, stateless):
    hv = _hv()
    pol = ctx['policy']
    caps = pol['caps']
    locked = pol['locked']
    strict = ctx.get('strict_ids', False)
    if ov['kind'] != 'auto':
        return {'_result': 'accept', '_code': None, '_path': None}
    # 1 base
    if ov['base'] != ctx['baseline_overlay']['id']:
        raise _Reject('reject', 'base_mismatch', 'base')
    langs = [lg for lg in ('fa', 'en') if lg in ov['lang']]
    # 2 ids
    for lang in langs:
        for ident in sorted(ov['lang'][lang]['severity']):
            p = 'lang.%s.severity.%s' % (lang, ident)
            level = ov['lang'][lang]['severity'][ident]
            if not _known(ctx, lang, ident):
                if strict:
                    raise _Reject('reject', 'unknown_id', p)
                continue
            if _locked(ident, locked):
                raise _Reject('reject', 'locked', p)
            if ident.startswith('lx-'):
                umbrella = _ctx_part(ctx, 'lexicon')[lang][ident]
                if _locked(umbrella, locked):
                    raise _Reject('reject', 'locked', p)
                if umbrella not in PHRASE_LIST_RULES[lang]:
                    raise _Reject('reject', 'lx_umbrella', p)
            base = _base_severity(ctx, lang, ident)
            if base not in LADDER or level not in LADDER:
                raise _Reject('reject', 'rule_off', p)
            if abs(LADDER[level] - LADDER[base]) > caps['cumulative']['severity_steps']:
                raise _Reject('reject', 'cumulative_severity', p)
    # 3 phrases
    for lang in langs:
        phrases = ov['lang'][lang]['phrases']
        if phrases:
            lists = _ctx_part(ctx, 'lists')[lang]
            vocab, stop, sensitive, common = (set(lists[k]) for k in ('vocab', 'stop', 'sensitive', 'common'))
        for i, ph in enumerate(phrases):
            p = 'lang.%s.phrases[%d]' % (lang, i)
            if hv.phrase_literal_problem(lang, ph['phrase']):
                raise _Reject('reject', 'phrase_literal', p)
            toks = _phrase_tokens(lang, ph['phrase'])
            if any(t not in vocab for t in toks):
                raise _Reject('reject', 'phrase_not_vocab', p)
            if any(t in sensitive for t in toks):
                raise _Reject('reject', 'phrase_sensitive', p)
            if all(t in stop for t in toks):
                raise _Reject('reject', 'phrase_stopwords', p)
            if len(toks) == 1 and toks[0] in common:
                raise _Reject('reject', 'phrase_common', p)
            if ph['state'] not in ('shadow', 'warning'):
                raise _Reject('reject', 'phrase_error', p + '.state')
        if len(phrases) > caps['cumulative']['phrases_per_lang']:
            raise _Reject('reject', 'phrases_per_lang', 'lang.%s.phrases' % lang)
    # 4 params
    for lang in langs:
        for name in sorted(ov['lang'][lang]['params']):
            pid = '%s:%s' % (lang, name)
            p = 'lang.%s.params.%s' % (lang, name)
            if pid not in pol['params']:
                if strict:
                    raise _Reject('reject', 'unknown_param', p)
                continue
            spec = pol['params'][pid]
            v = _frac(ov['lang'][lang]['params'][name])
            if not (_frac(spec['min']) <= v <= _frac(spec['max'])):
                raise _Reject('reject', 'param_range', p)
            bo = ctx['baseline_overlay']['lang'].get(lang, {}).get('params', {})
            base = _frac(bo.get(name, spec['default']))
            if abs(v - base) > base * _frac(caps['cumulative']['param_pct']) / 100:
                raise _Reject('reject', 'param_cumulative', p)
    # 5 channels
    if ov['channels']:
        shipped = _ctx_part(ctx, 'channels')
        for key in sorted(ov['channels']):
            p = 'channels.%s' % key
            if key not in shipped:
                raise _Reject('reject', 'channel_unknown', p)
            if 'max_chars' in ov['channels'][key] and key not in pol['channels_machine']:
                raise _Reject('reject', 'channel_value', p)
    # 6 shadow floor
    share = _frac(caps['cumulative']['max_shadow_share'])
    for lang in langs:
        sev = ov['lang'][lang]['severity']
        if not any(v == 'shadow' for v in sev.values()):
            continue
        shown = [r for r in _ctx_part(ctx, 'builtin')[lang]
                 if not _locked(r, locked) and _base_severity(ctx, lang, r) in ('warning', 'error')]
        shadowed = [r for r in shown if sev.get(r) == 'shadow']
        if len(shadowed) > share * len(shown):
            raise _Reject('reject', 'shadow_floor', 'lang.%s.severity' % lang)
    if stateless:
        return {'_result': 'accept', '_code': None, '_path': None}
    # 7 per release, against the active auto overlay (or the baseline when none is active)
    active = ctx.get('active_auto')
    against_prev = active is not None and active['id'] == ctx.get('prev_release')
    rules_changed, demotions, promotions, new_phrases, changed_ids, changed_params = [], [], [], [], [], []
    problem = None
    pr = caps['per_release']
    for lang in ('fa', 'en'):
        new_sev = ov['lang'].get(lang, {}).get('severity', {})
        old_sev = active['lang'].get(lang, {}).get('severity', {}) if active else {}
        for ident in sorted(set(new_sev) | set(old_sev)):
            if not _known(ctx, lang, ident):
                continue
            base = _base_severity(ctx, lang, ident)
            new, old = new_sev.get(ident, base), old_sev.get(ident, base)
            if new == old:
                continue
            changed_ids.append(ident)
            if abs(LADDER[new] - LADDER[old]) > pr['severity_step'] and problem is None:
                problem = ('severity_step', 'lang.%s.severity.%s' % (lang, ident))
            if ident.startswith('lx-'):
                (demotions if LADDER[new] < LADDER[old] else promotions).append(ident)
            else:
                rules_changed.append(ident)
        new_ph = dict((ph['id'], ph['state']) for ph in ov['lang'].get(lang, {}).get('phrases', ()))
        old_ph = dict((ph['id'], ph['state']) for ph in active['lang'].get(lang, {}).get('phrases', ())) \
            if active else {}
        for pid in sorted(new_ph):
            if pid not in old_ph:
                new_phrases.append(pid)
                changed_ids.append(pid)
            elif new_ph[pid] != old_ph[pid]:
                changed_ids.append(pid)
                (demotions if LADDER[new_ph[pid]] < LADDER[old_ph[pid]] else promotions).append(pid)
        new_par = ov['lang'].get(lang, {}).get('params', {})
        old_par = active['lang'].get(lang, {}).get('params', {}) if active else {}
        for name in sorted(set(new_par) | set(old_par)):
            pid = '%s:%s' % (lang, name)
            if pid not in pol['params']:
                continue
            bo = ctx['baseline_overlay']['lang'].get(lang, {}).get('params', {})
            base = _frac(bo.get(name, pol['params'][pid]['default']))
            new, old = _frac(new_par.get(name, base)), _frac(old_par.get(name, base))
            if new != old:
                changed_params.append(pid)
                if abs(new - old) > old * _frac(pr['param_step_pct']) / 100 and problem is None:
                    problem = ('param_step', 'lang.%s.params.%s' % (lang, name))
    if problem is None:
        for code, n, cap in (('per_release_rules', len(rules_changed), pr['rules']),
                             ('per_release_phrase_demotions', len(demotions), pr['phrase_demotions']),
                             ('per_release_phrase_new', len(new_phrases), pr['phrase_new']),
                             ('per_release_phrase_promotions', len(promotions), pr['phrase_promotions'])):
            if n > cap:
                problem = (code, None)
                break
    result, code, path = 'accept', None, None
    if problem is not None:
        if against_prev:
            raise _Reject('reject', problem[0], problem[1])
        result, code, path = 'accept_gap', problem[0], problem[1]
    # 8 rolling limits (client history)
    roll = caps['rolling']
    now = _ptime(ctx['now'])
    acts = [dict(a, at_dt=_ptime(a['at'])) for a in (ctx.get('state') or {}).get('activations', ())]
    if acts and now - acts[-1]['at_dt'] < datetime.timedelta(days=roll['min_days_between_auto']):
        raise _Reject('defer', 'release_interval', None)
    window = [a for a in acts if now - a['at_dt'] < datetime.timedelta(days=roll['window_days'])]
    if sum(len(a['rules']) for a in window) + len(rules_changed) > roll['rules']:
        raise _Reject('defer', 'rolling_rules', None)
    if sum(len(a['phrase_demotions']) for a in window) + len(demotions) > roll['phrase_demotions']:
        raise _Reject('defer', 'rolling_phrase_demotions', None)
    cool = datetime.timedelta(days=roll['cooldown_days'])
    for a in acts:
        if now - a['at_dt'] < cool:
            for ident in a.get('changed', ()):
                if ident in changed_ids:
                    raise _Reject('defer', 'cooldown', ident)
    return {'_result': result, '_code': code, '_path': path, 'rules': rules_changed, 'phrase_demotions': demotions,
            'phrase_promotions': promotions, 'phrase_new': new_phrases, 'changed': sorted(set(changed_ids)),
            'params': changed_params}


# ----------------------------------------------------------------------------- self-test (spec 5.8 step 8)

_SELFTEST_FA = ('good.txt', 'fp-ok.txt', 'legit-negation.txt')
_SELFTEST_EN = ('en/good.txt',)
_WORDS = re.compile(r'\w+')


def self_test(baseline_overlay, auto_overlay=None, policy=None, samples_dir=None):
    """Lint the bundled samples with and without the new overlay (spec 5.8 step 8).

    Passes if: no exception; the time with the overlay (minimum of 3 runs) is at most twice
    the time without it (plus 5 ms for timer noise); the good samples gain no error; warnings
    on the good samples rise by at most 0.5 per 1,000 words; every locked rule fires on the
    bad samples exactly as before. Returns (ok, detail)."""
    folder = samples_dir or os.path.join(HERE, 'samples')
    locked = ((policy or {}).get('locked')) or []
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import lint
        texts = []
        for name, lang, good in ([(n, 'fa', True) for n in _SELFTEST_FA] + [('bad.txt', 'fa', False)]
                                 + [(n, 'en', True) for n in _SELFTEST_EN] + [('en/bad.txt', 'en', False)]):
            path = os.path.join(folder, *name.split('/'))
            if os.path.isfile(path):
                with open(path, 'r', encoding='utf-8') as fh:
                    texts.append((name, lang, good, fh.read()))
        if not texts:
            return False, 'no samples'

        def run(overlay_on):
            got, best = [], None
            for _ in range(3):
                t0 = time.perf_counter()
                cur = []
                for name, lang, good, text in texts:
                    if overlay_on:
                        with _using(baseline_overlay, auto_overlay, policy):
                            issues = lint.lint_text(text, lang=lang)[0]
                    else:
                        with _without():
                            issues = lint.lint_text(text, lang=lang)[0]
                    cur.append(issues)
                spent = time.perf_counter() - t0
                best = spent if best is None else min(best, spent)
                got = cur
            return got, best

        before, t_before = run(False)
        after, t_after = run(True)
        if t_after > 2 * t_before + 0.005:
            return False, 'slower: %.1f ms with the overlay, %.1f ms without' % (t_after * 1e3, t_before * 1e3)
        for (name, lang, good, text), b, a in zip(texts, before, after):
            if good:
                if sum(1 for x in a if x['level'] == 'error') > sum(1 for x in b if x['level'] == 'error'):
                    return False, '%s gains an error' % name
                words = max(1, len(_WORDS.findall(text)))
                rise = sum(1 for x in a if x['level'] == 'warning') - sum(1 for x in b if x['level'] == 'warning')
                if rise * 1000.0 / words > 0.5:
                    return False, '%s gains %d warnings' % (name, rise)
            else:
                def locked_counts(issues):
                    out = {}
                    for x in issues:
                        if _locked(x['code'], locked):
                            out[x['code']] = out.get(x['code'], 0) + 1
                    return out
                if locked_counts(a) != locked_counts(b):
                    return False, '%s: a locked rule no longer fires as before' % name
        return True, 'ok'
    except Exception as e:
        return False, 'exception: %s: %s' % (type(e).__name__, str(e)[:120])


# ----------------------------------------------------------------------------- activation (spec 5.8 steps 7 and 9)


class Decision(object):
    """What hub_client does after a sync: result accept, accept_gap (activate and record
    cap_reject gap), reject (keep the previous overlay, record cap_reject violation), defer
    (keep it, record nothing, try again next sync) or keep (nothing changed). When activate
    is true, write active_bytes to active.json (tmp, fsync, os.replace), store rules under
    state.json "rules", and keep the targets listed in keep_targets."""

    def __init__(self):
        self.result = 'keep'
        self.code = None
        self.path = None
        self.health = []
        self.activate = False
        self.active = None
        self.active_bytes = None
        self.rules = None
        self.keep_targets = []

    def as_dict(self):
        return {'result': self.result, 'code': self.code, 'path': self.path, 'health': list(self.health),
                'activate': self.activate, 'active': self.active, 'keep_targets': list(self.keep_targets)}


def _ref(sel, kind):
    if sel is None:
        return None
    out = {'id': sel['id'], 'target': sel['path'], 'sha256': sel['sha256']}
    if kind == 'auto':
        out.update(role=sel.get('role') or 'stable', prev=sel.get('prev'))
    return out


def decide(sync_result, active_record=None, now=None, active_auto_doc=None, lists=None, run_self_test=True,
           samples_dir=None):
    """Spec 5.8 steps 7 to 9 for a successful hub_verify.sync() result.

    active_record: the parsed active.json (parse_active) or None; its pin is the person's own
    (hub_client pin) and is kept. active_auto_doc: the currently active auto overlay document
    (hub_client reads targets/<sha256>.json through hub_verify.check_target), needed for the
    per-release caps. While a halt is in force nothing is activated (result keep, code halt).
    A fall back (to the listed stable after a candidate, or to the same overlays) runs the
    content checks only; anything new runs every cap, then the self-test. Returns a Decision."""
    dec = Decision()
    hv = _hv()
    res = sync_result
    if not getattr(res, 'ok', False) or not res.selection:
        dec.result, dec.code = 'keep', getattr(res, 'code', None)
        return dec
    now_dt = hv._now(now)
    now_s = hv.fmt_time(now_dt)
    rules = json.loads(json.dumps(res.rules or {}))
    sel = res.selection
    policy = res.snapshot.baseline['policy']
    base = sel['baseline']
    auto = sel.get('auto')
    if res.halt is not None:
        # a halt pauses activation; the halt itself pins at load time (spec 5.8 step 2), so the
        # record stays as it is and a lift resumes it without a new activation
        dec.result, dec.code, dec.rules = 'keep', 'halt', rules
        return dec
    pin = None
    if active_record and active_record.get('pin') in ('baseline', 'bundled'):
        pin = active_record['pin']          # the person's own pin (hub_client pin), kept
        if pin == 'baseline':
            auto = None
    cur_auto = (active_record or {}).get('auto') or None
    cur_base = (active_record or {}).get('baseline') or None
    same_base = cur_base is not None and cur_base['sha256'] == base['sha256']
    same_auto = (cur_auto is None and auto is None) or (cur_auto is not None and auto is not None
                                                          and cur_auto['sha256'] == auto['sha256'])
    ctx = make_context(base['overlay'], policy, lists=lists, active_auto=active_auto_doc,
                       prev_release=(auto or {}).get('prev'), state=rules, now=now_s)
    changes = None
    if auto is not None:
        fallback = same_auto or (sel.get('reason') == 'stable' and cur_auto is not None
                                 and cur_auto.get('role') == 'candidate' and cur_auto.get('prev') == auto['id'])
        got = check_caps(auto['overlay'], ctx, stateless=bool(fallback))
        dec.code, dec.path = got['code'], got['path']
        if got['result'] == 'reject':
            dec.result = 'reject'
            dec.health.append(('cap_reject', 'violation'))
            return dec
        if got['result'] == 'defer':
            dec.result = 'defer'
            return dec
        if got['result'] == 'accept_gap':
            dec.health.append(('cap_reject', 'gap'))
        dec.result = got['result']
        if not fallback:
            changes = got['changes']
    else:
        dec.result = 'accept'
    if same_base and same_auto and (active_record or {}).get('pin') == pin:
        dec.result = 'keep'
        dec.rules = rules
        return dec
    if run_self_test and (auto is not None or not same_base):
        ok, detail = self_test(base['overlay'], auto['overlay'] if auto else None, policy, samples_dir)
        dec.health.append(('selftest_ok' if ok else 'selftest_fail', None))
        if not ok:
            dec.result, dec.code, dec.path = 'reject', 'self_test', detail
            return dec
    if changes is not None:
        acts = list(rules.get('activations') or [])
        acts.append({'release': auto['id'], 'at': now_s, 'rules': changes['rules'],
                     'phrase_demotions': changes['phrase_demotions'], 'changed': changes['changed']})
        roll = policy['caps']['rolling']
        keep_days = max(roll['cooldown_days'], roll['window_days'], roll['min_days_between_auto'])
        cutoff = now_dt - datetime.timedelta(days=keep_days)
        rules['activations'] = [a for a in acts[:-1] if _ptime(a['at']) >= cutoff] + acts[-1:]
    previous = list((active_record or {}).get('previous') or [])
    if active_record:
        previous = ([{'baseline': active_record['baseline'], 'auto': active_record['auto']}] + previous)[:2]
    record = {'schema': 'whalory.active/1', 'activated': now_s, 'baseline': _ref(base, 'baseline'),
              'auto': _ref(auto, 'auto'), 'pin': pin if pin in ('baseline', 'bundled') else None,
              'previous': previous}
    dec.activate = True
    dec.active = record
    dec.active_bytes = (json.dumps(record, ensure_ascii=False, indent=1, sort_keys=True) + '\n').encode('utf-8')
    dec.rules = rules
    keep = [record['baseline']['sha256']] + ([record['auto']['sha256']] if record['auto'] else [])
    for p in previous:
        keep.append(p['baseline']['sha256'])
        if p['auto']:
            keep.append(p['auto']['sha256'])
    dec.keep_targets = sorted(set(keep))
    return dec
