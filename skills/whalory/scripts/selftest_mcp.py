#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_mcp: conformance tests for scripts/mcp_server.py (Whalory 3.0.0 build spec, G.6; Hub spec 5.11).

Each test spawns the server with sys.executable and talks JSON-RPC over its stdin and stdout,
the way an MCP client does. run() returns [(name, passed, detail)], like selftest_tools.run();
selftest.py calls it when this file is present. The expected tool set follows this copy of
Whalory: the five Core tools always, and each Pro tool when its backing file or data exists.

Usage:
    python selftest_mcp.py          # prints one line per test; exit code 1 on any failure
"""
from __future__ import print_function

import sys

if sys.version_info < (3, 8):
    sys.stderr.write('selftest_mcp needs Python 3.8 or newer.\n')
    sys.exit(2)

sys.dont_write_bytecode = True  # the Hub tests import tests_hub/test_client.py and hub_client.py

import ast  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import queue  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402

# Built-in rules only (Hub spec 5.9): a synced Hub folder on this computer must not change what the
# tests expect. The server processes also get WHALORY_HUB=0 unless a test turns the Hub on itself.
os.environ['WHALORY_HUB_OVERLAY'] = '0'

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SERVER = os.path.join(HERE, 'mcp_server.py')
SAMPLES = os.path.join(HERE, 'samples', 'mcp')
REL_SAMPLES = 'scripts/samples/mcp'

LEGACY = ['2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05']
MODERN = '2026-07-28'
PV = 'io.modelcontextprotocol/protocolVersion'
CAPS = 'io.modelcontextprotocol/clientCapabilities'
SINFO = 'io.modelcontextprotocol/serverInfo'
SUBID = 'io.modelcontextprotocol/subscriptionId'

ORDER = ['lint_text', 'lint_file', 'check_final', 'detect_context', 'get_playbook', 'get_reference_section',
         'channel_limits', 'compare_texts', 'ab_test_size', 'profile_lookup']
CORE = ['lint_text', 'lint_file', 'check_final', 'get_playbook', 'get_reference_section', 'profile_lookup']
PRO_BACKING = {'detect_context': 'scripts/detect_context.py', 'channel_limits': 'data/channels',
               'compare_texts': 'scripts/compare.py', 'ab_test_size': 'scripts/ab_calc.py'}
TIMEOUT = 20.0


def _exists(rel):
    full = os.path.join(SKILL, *rel.split('/'))
    if rel.endswith('.py'):
        return os.path.isfile(full)
    try:
        return os.path.isdir(full) and any(f.endswith('.json') for f in os.listdir(full))
    except OSError:
        return False


def expected_tools():
    names = set(CORE) | set(t for t, rel in PRO_BACKING.items() if _exists(rel))
    return [n for n in ORDER if n in names]


def has_english_linter():
    return os.path.isfile(os.path.join(HERE, 'lint.py')) and os.path.isfile(os.path.join(HERE, 'lint_en.py'))


# ---------------------------------------------------------------- minimal JSON Schema check
def schema_errors(schema, v, where='$'):
    """type, required, enum, properties and items only: enough to hold structuredContent to outputSchema."""
    errs = []
    t = schema.get('type')
    if t is not None:
        ts = t if isinstance(t, list) else [t]

        def ok(x):
            if x == 'null':
                return v is None
            if x == 'boolean':
                return isinstance(v, bool)
            if x == 'integer':
                return isinstance(v, int) and not isinstance(v, bool)
            if x == 'number':
                return isinstance(v, (int, float)) and not isinstance(v, bool)
            if x == 'string':
                return isinstance(v, str)
            if x == 'object':
                return isinstance(v, dict)
            if x == 'array':
                return isinstance(v, list)
            return True
        if not any(ok(x) for x in ts):
            return ['%s: expected %s, got %s' % (where, ts, type(v).__name__)]
    if 'enum' in schema and v not in schema['enum']:
        errs.append('%s: %r not in enum' % (where, v))
    if isinstance(v, dict):
        for k in schema.get('required') or []:
            if k not in v:
                errs.append('%s: missing %s' % (where, k))
        for k, sub in (schema.get('properties') or {}).items():
            if k in v:
                errs += schema_errors(sub, v[k], '%s.%s' % (where, k))
    if isinstance(v, list) and isinstance(schema.get('items'), dict):
        if 'maxItems' in schema and len(v) > schema['maxItems']:
            errs.append('%s: %d items > maxItems' % (where, len(v)))
        for i, x in enumerate(v):
            errs += schema_errors(schema['items'], x, '%s[%d]' % (where, i))
    return errs


# ---------------------------------------------------------------- a small stdio client
class Client(object):
    """Spawns the server and exchanges JSON-RPC lines with it."""

    def __init__(self, args=(), env=None, cwd=None, server=None, dash_b=True, drop=()):
        e = dict(os.environ)
        for k in ('ROOTS', 'LANG', 'TIME_LIMIT'):   # and the deprecated WHALYA_* twins
            e.pop('WHALORY_' + k, None)
            e.pop('WHALYA_' + k, None)
        e['PYTHONIOENCODING'] = 'utf-8'
        e['PYTHONUTF8'] = '1'
        e['WHALORY_HUB'] = '0'      # no Hub folder of this computer; t_hub_live turns it on
        for k in drop:
            e.pop(k, None)
        if env:
            e.update(env)
        self.q = queue.Queue()
        self.raw, self.bad, self.stderr, self.notes = [], [], [], []
        self.next_id = 1000
        self.t0 = time.time()
        # -B: the tests must not leave scripts/__pycache__ behind either (t_no_bytecode runs without
        # it, to test the server's own sys.dont_write_bytecode)
        cmd = [sys.executable] + (['-B'] if dash_b else []) + [server or SERVER] + list(args)
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  env=e, cwd=cwd or SKILL)
        self._t1 = threading.Thread(target=self._read_out)
        self._t2 = threading.Thread(target=self._read_err)
        self._t1.daemon = self._t2.daemon = True
        self._t1.start()
        self._t2.start()

    def _read_out(self):
        for line in iter(self.p.stdout.readline, b''):
            self.raw.append(line)
            try:
                self.q.put(json.loads(line.decode('utf-8')))
            except ValueError:
                self.bad.append(line[:200])

    def _read_err(self):
        for line in iter(self.p.stderr.readline, b''):
            self.stderr.append(line.decode('utf-8', 'replace'))

    def send_raw(self, data):
        self.p.stdin.write(data + b'\n')
        self.p.stdin.flush()

    def send(self, obj):
        self.send_raw(json.dumps(obj, ensure_ascii=False).encode('utf-8'))

    def recv(self, timeout=TIMEOUT):
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None

    def request(self, method, params=None, rid=None, modern=False, meta=None):
        if rid is None:
            self.next_id += 1
            rid = self.next_id
        msg = {'jsonrpc': '2.0', 'id': rid, 'method': method}
        if params is not None or modern:
            params = dict(params or {})
        if modern:
            m = dict(params.get('_meta') or {})
            m.update(meta if meta is not None else {PV: MODERN, CAPS: {}})
            params['_meta'] = m
        if params is not None:
            msg['params'] = params
        self.send(msg)
        return self.wait_for(rid)

    def wait_for(self, rid, timeout=TIMEOUT):
        end = time.time() + timeout
        while time.time() < end:
            m = self.recv(max(0.05, end - time.time()))
            if m is None:
                break
            if 'id' in m and m.get('id') == rid and type(m.get('id')) is type(rid):
                return m
            self.notes.append(m)
        return None

    def call(self, name, args, modern=False):
        return self.request('tools/call', {'name': name, 'arguments': args}, modern=modern)

    def server_request(self, method, timeout=5.0):
        """The next request the server sent to this client (for example roots/list), or None."""
        for i, m in enumerate(self.notes):
            if m.get('method') == method and 'id' in m:
                return self.notes.pop(i)
        end = time.time() + timeout
        while time.time() < end:
            m = self.recv(max(0.05, end - time.time()))
            if m is None:
                break
            if m.get('method') == method and 'id' in m:
                return m
            self.notes.append(m)
        return None

    def close(self, timeout=5.0):
        try:
            self.p.stdin.close()
        except Exception:
            pass
        t = time.time()
        try:
            code = self.p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.wait()
            code = None
        self._t1.join(2)
        self._t2.join(2)
        for s in (self.p.stdout, self.p.stderr):
            try:
                s.close()
            except Exception:
                pass
        return code, time.time() - t


# ---------------------------------------------------------------- test bookkeeping
class Results(object):
    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail=''):
        self.rows.append(('mcp ' + name, bool(ok), detail if isinstance(detail, str) else repr(detail)))

    def skip(self, name, why):
        self.rows.append(('mcp ' + name, True, 'skipped: ' + why))


def _result(resp):
    return resp.get('result') if isinstance(resp, dict) else None


def _error(resp):
    return resp.get('error') if isinstance(resp, dict) else None


def _text(res):
    try:
        return res['content'][0]['text']
    except (TypeError, KeyError, IndexError):
        return ''


def _short(x, n=200):
    s = x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + '...'


def _is_tool_error(resp):
    r = _result(resp)
    return isinstance(r, dict) and r.get('isError') is True and bool(_text(r))


def _headings(path):
    """(level, slug) of Markdown headings, with the same slug rule as the server and build.py."""
    import unicodedata
    out, fence, seen = [], None, {}
    with open(path, encoding='utf-8') as f:
        for ln in f:
            m = re.match(r'^\s{0,3}(`{3,}|~{3,})', ln)
            if m:
                fence = None if fence == m.group(1)[0] else (fence or m.group(1)[0])
                continue
            if fence:
                continue
            h = re.match(r'^\s{0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$', ln.rstrip('\n'))
            if not h:
                continue
            t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', h.group(2))
            t = re.sub(r'<[^>]+>', '', t).replace('`', '')
            t = re.sub(r'\*+', '', t).strip()
            s = ''.join(c for c in t.lower() if c in ' -_\u200c' or unicodedata.category(c)[0] in 'LMN'
                        or unicodedata.category(c) == 'Pc').replace(' ', '-')
            n = seen.get(s, 0)
            seen[s] = n + 1
            out.append((len(h.group(1)), s if n == 0 else '%s-%d' % (s, n)))
    return out


# ---------------------------------------------------------------- the tests
def _read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def t_static(R):
    src = _read(SERVER)
    for label, path in (('mcp_server.py', SERVER), ('selftest_mcp.py', os.path.abspath(__file__))):
        try:
            ast.parse(_read(path), feature_version=(3, 8))
            R.add('%s parses as Python 3.8' % label, True)
        except SyntaxError as e:
            R.add('%s parses as Python 3.8' % label, False, str(e))
    tree = ast.parse(src)
    bad, popens = set(), 0
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or '']
        for n in names:
            if n.split('.')[0] in ('socket', 'urllib', 'http', 'ssl', 'asyncio', 'ftplib',
                                   'smtplib', 'requests', 'multiprocessing', 'shutil', 'tempfile'):
                bad.add(n)
        if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'print':
            bad.add('print()')
        attr = getattr(node.func, 'attr', None) if isinstance(node, ast.Call) else None
        owner = getattr(getattr(node.func, 'value', None), 'id', None) if isinstance(node, ast.Call) else None
        if attr in ('system', 'popen', 'unlink', 'remove', 'rmtree', 'rename', 'makedirs', 'mkdir', 'startfile',
                    'spawnl', 'spawnv', 'execv', 'execl', 'execvp'):
            bad.add(attr)
        if owner in ('os', 'subprocess') and attr in ('replace', 'run', 'call', 'check_call', 'check_output',
                                                      'getoutput', 'getstatusoutput'):
            bad.add('%s.%s' % (owner, attr))
        if attr == 'Popen':
            popens += 1
        if isinstance(node, ast.keyword) and node.arg == 'shell':
            bad.add('shell=')
    R.add('server: no network, shell, file-writing or print() calls', not bad, ', '.join(sorted(bad)))
    # The one child process is the time-limited worker: this same file, run with sys.executable.
    R.add('server: one child process, sys.executable running this file with --worker',
          popens == 1 and re.search(r"\[exe, '-B', os\.path\.realpath\(__file__\), '--worker'", src)
          and 'exe = sys.executable' in src, 'Popen calls: %d' % popens)
    R.add('server: no open() for writing', not re.search(r"open\([^)]*['\"][wax]b?['\"]", src))
    R.add('server: sys.dont_write_bytecode before the first sibling import',
          re.search(r'^sys\.dont_write_bytecode = True$', src, re.M) is not None
          and src.index('sys.dont_write_bytecode = True') < src.index('importlib.import_module'))


def t_cli(R):
    e = dict(os.environ)
    e.pop('WHALORY_ROOTS', None)
    e.pop('WHALYA_ROOTS', None)
    p = subprocess.run([sys.executable, SERVER, '--version'], capture_output=True, env=e)
    R.add('--version', p.returncode == 0 and p.stdout.strip() == b'whalory-mcp 3.2.0-rc.2', _short(p.stdout.decode()))
    p = subprocess.run([sys.executable, SERVER, '--self-check', '--json'], capture_output=True, env=e, cwd=SKILL)
    try:
        rep = json.loads(p.stdout.decode('ascii'))
    except ValueError:
        R.add('--self-check --json', False, _short(p.stdout.decode('utf-8', 'replace')))
        return None
    want = expected_tools()
    R.add('--self-check --json: tools', rep.get('tools') == want, 'got %s, want %s' % (rep.get('tools'), want))
    R.add('--self-check --json: keys', set(rep) == {'tools', 'prompts', 'resources', 'tier', 'version', 'projectRootsConfigured', 'rootPolicy', 'transport', 'networkTools'}
          and rep.get('version') == '3.2.0-rc.2' and rep.get('projectRootsConfigured') is False
          and rep.get('rootPolicy') == 'explicit-or-client' and rep.get('transport') == 'stdio'
          and rep.get('networkTools') is False
          and isinstance(rep.get('resources'), int) and rep.get('tier') in ('core', 'pro'), _short(rep))
    tier = 'pro' if any(t in rep.get('tools', []) for t in PRO_BACKING) else 'core'
    R.add('--self-check --json: tier', rep.get('tier') == tier, rep.get('tier'))
    return rep


def t_legacy(R, tmp, report):
    root = os.path.join(tmp, 'root')
    outside = os.path.join(tmp, 'outside')
    home = os.path.join(tmp, 'home')
    for d in (root, outside, os.path.join(home, '.whalory', 'profiles')):
        os.makedirs(d)
    with open(os.path.join(root, 'inside.txt'), 'w', encoding='utf-8') as f:
        f.write('\u0686\u0627\u06CC \u062A\u0627\u0632\u0647 \u0631\u0633\u06CC\u062F.\n')
    with open(os.path.join(root, 'blob.bin'), 'wb') as f:
        f.write(b'\x00\x01')
    with open(os.path.join(outside, 'outside.txt'), 'w', encoding='utf-8') as f:
        f.write('secret\n')
    with open(os.path.join(home, '.whalory', 'profiles', 'userbrand.json'), 'w', encoding='utf-8') as f:
        json.dump({'schema_version': 2, 'name': 'userbrand', 'dials': {'warmth': 4}}, f)
    env = {'HOME': home, 'USERPROFILE': home}
    c = Client(['--root', root], env=env)
    try:
        # startup and handshake
        r = c.request('initialize', {'protocolVersion': LEGACY[0], 'capabilities': {},
                                     'clientInfo': {'name': 'selftest', 'version': '1'}}, rid=1)
        R.add('startup under 1 s', r is not None and (time.time() - c.t0) < 1.0, '%.2f s' % (time.time() - c.t0))
        res = _result(r) or {}
        R.add('initialize %s echoed' % LEGACY[0], res.get('protocolVersion') == LEGACY[0], _short(res))
        si = res.get('serverInfo') or {}
        R.add('initialize: serverInfo and capabilities',
              si.get('name') == 'whalory' and si.get('version') == '3.2.0-rc.2' and si.get('title') == 'Whalory'
              and set(res.get('capabilities') or {}) == {'tools', 'prompts', 'resources'}, _short(si))
        ins = res.get('instructions') or ''
        R.add('initialize: instructions under 1,200 characters', 0 < len(ins) <= 1200, '%d' % len(ins))
        R.add('legacy result has no resultType', 'resultType' not in res and '_meta' not in res)
        for v in LEGACY[1:]:
            r = c.request('initialize', {'protocolVersion': v, 'capabilities': {}})
            R.add('initialize %s echoed' % v, (_result(r) or {}).get('protocolVersion') == v, _short(r))
        r = c.request('initialize', {'protocolVersion': '1999-01-01', 'capabilities': {}})
        R.add('initialize unknown version -> 2025-11-25',
              (_result(r) or {}).get('protocolVersion') == '2025-11-25', _short(r))
        r = c.request('initialize', {'protocolVersion': MODERN, 'capabilities': {}})
        R.add('initialize never answers 2026-07-28', (_result(r) or {}).get('protocolVersion') == '2025-11-25')
        c.request('initialize', {'protocolVersion': LEGACY[0], 'capabilities': {}})

        # notifications get no reply
        c.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        c.send({'jsonrpc': '2.0', 'method': 'notifications/cancelled', 'params': {'requestId': 'nobody', 'reason': 't'}})
        c.send({'jsonrpc': '2.0', 'method': 'notifications/unknown-thing'})
        before = len(c.notes)
        r = c.request('ping', rid='p-1')
        R.add('ping -> {}', _result(r) == {}, _short(r))
        R.add('notifications get no reply (initialized, cancelled for an unknown id, unknown)',
              len(c.notes) == before, _short(c.notes[before:]))

        # tools/list
        r1 = c.request('tools/list')
        r2 = c.request('tools/list')
        tools = (_result(r1) or {}).get('tools') or []
        names = [t.get('name') for t in tools]
        want = expected_tools()
        R.add('tools/list: expected tools in spec order', names == want, 'got %s' % names)
        R.add('tools/list: deterministic', r1 and r2 and _result(r1) == _result(r2))
        R.add('tools/list: no resultType in legacy', 'resultType' not in (_result(r1) or {}))
        probs = []
        for t in tools:
            if (t.get('inputSchema') or {}).get('type') != 'object':
                probs.append('%s inputSchema' % t.get('name'))
            if 'outputSchema' in t and t['outputSchema'].get('type') != 'object':
                probs.append('%s outputSchema' % t.get('name'))
            if len(t.get('description') or '') > 2048 or not t.get('description'):
                probs.append('%s description' % t.get('name'))
            if t.get('annotations') != {'readOnlyHint': True, 'destructiveHint': False, 'idempotentHint': True,
                                        'openWorldHint': False}:
                probs.append('%s annotations' % t.get('name'))
            if not re.match(r'^[a-z0-9_]{1,64}$', t.get('name') or ''):
                probs.append('%s name' % t.get('name'))
            if '$ref' in json.dumps(t):
                probs.append('%s uses $ref' % t.get('name'))
        R.add('tools/list: object schemas, read-only annotations, descriptions <= 2,048', not probs, ', '.join(probs))
        content_tools = [t for t in tools if t['name'] in ('get_playbook', 'get_reference_section')]
        R.add('content tools: no outputSchema, maxResultSizeChars 100000',
              all('outputSchema' not in t and (t.get('_meta') or {}).get('anthropic/maxResultSizeChars') == 100000
                  for t in content_tools) and all('outputSchema' in t for t in tools if t not in content_tools))
        schemas = dict((t['name'], t.get('outputSchema')) for t in tools)

        def check_data(label, resp, tool):
            res = _result(resp) or {}
            sc = res.get('structuredContent')
            ok = res.get('isError') is False and isinstance(sc, dict)
            errs = schema_errors(schemas[tool], sc) if ok else ['no structuredContent']
            R.add('%s: structuredContent matches outputSchema' % label, ok and not errs,
                  '; '.join(errs[:3]) or _short(res))
            try:
                mirror = json.loads(_text(res))
            except ValueError:
                mirror = None
            R.add('%s: text mirror equals structuredContent' % label, ok and mirror == sc)
            return sc if isinstance(sc, dict) else {}

        def check_err(label, resp):
            R.add(label + ' -> isError', _is_tool_error(resp), _short(resp))

        # lint_text
        fa_text = '\u06A9\u0627\u0644\u0627\u0647\u0627\u064A \u0645\u0627 \u0631\u0627 \u0647\u0645\u06CC\u0646 ' \
                  '\u062D\u0627\u0644\u0627 \u0633\u0641\u0627\u0631\u0634 \u062F\u0647\u06CC\u062F \u2014 ' \
                  '\u0641\u0631\u0635\u062A!!'
        n_raw = len(c.raw)
        r = c.call('lint_text', {'text': fa_text})
        sc = check_data('lint_text fa', r, 'lint_text')
        rules = set(i.get('rule') for i in sc.get('issues') or [])
        R.add('lint_text fa: finds arabic-yeh and dash', {'arabic-yeh', 'dash'} <= rules and sc.get('lang') == 'fa'
              and sc.get('passed') is False, _short(sorted(rules)))
        exc = ''.join(i.get('excerpt', '') for i in sc.get('issues') or [])
        ascii_only = all(b < 128 for ln in c.raw[n_raw:] for b in ln)
        R.add('Persian round trip survives ensure_ascii', ascii_only and '\u0633\u0641\u0627\u0631\u0634' in exc,
              'ascii=%s %s' % (ascii_only, _short(exc)))
        en_text = 'Certainly! Here is a vibrant caption that will delve into our story.'
        r = c.call('lint_text', {'text': en_text})
        if has_english_linter():
            sc = check_data('lint_text en', r, 'lint_text')
            rules = set(i.get('rule') for i in sc.get('issues') or [])
            R.add('lint_text en: finds en-chatbot-residue', sc.get('lang') == 'en'
                  and 'en-chatbot-residue' in rules, _short(sorted(rules)))
            r = c.call('lint_text', {'text': en_text, 'facts': 'Our cafe opens on Friday.'})
            R.add('lint_text en with facts', (_result(r) or {}).get('isError') is False, _short(r))
        else:
            R.add('lint_text en without lint_en.py -> actionable isError',
                  _is_tool_error(r) and 'lint_en' in _text(_result(r)), _short(r))
        r = c.call('lint_text', {'text': fa_text, 'profile': 'whalory', 'format': 'caption', 'md': True,
                                 'max_words': 12, 'strict': True})
        check_data('lint_text with profile, format, md, max_words, strict', r, 'lint_text')
        r = c.call('lint_text', {'text': fa_text, 'profile_json': {'schema_version': 2, 'name': 'inline',
                                                                    'banned': ['\u0641\u0631\u0635\u062A']}})
        sc = check_data('lint_text with profile_json', r, 'lint_text')
        R.add('lint_text: profile_json banned word is reported', 'profile-banned' in set(
            i.get('rule') for i in sc.get('issues') or []), _short(sc.get('issues')))
        check_err('lint_text without text', c.call('lint_text', {}))
        check_err('lint_text with text as a number', c.call('lint_text', {'text': 5}))
        check_err('lint_text with lang "de"', c.call('lint_text', {'text': 'x', 'lang': 'de'}))
        check_err('lint_text with an unknown argument', c.call('lint_text', {'text': 'x', 'colour': 'red'}))
        check_err('lint_text with an unknown profile', c.call('lint_text', {'text': 'x', 'profile': 'no-such-profile'}))
        check_err('lint_text with profile outside the roots',
                  c.call('lint_text', {'text': 'x', 'profile': os.path.join(outside, 'voice.json')}))
        r = c.call('lint_text', {'text': fa_text, 'channel': 'instagram.caption'})
        if _exists('data/channels'):
            sc = check_data('lint_text with channel', r, 'lint_text')
            R.add('lint_text with channel: stats.channel', isinstance((sc.get('stats') or {}).get('channel'), dict))
            check_err('lint_text with an unknown channel', c.call('lint_text', {'text': 'x', 'channel': 'nochannel'}))
        else:
            check_err('lint_text with channel but no data/channels', r)

        # lint_file
        r = c.call('lint_file', {'path': REL_SAMPLES + '/draft.fa.txt'})
        sc = check_data('lint_file fa', r, 'lint_file')
        R.add('lint_file fa: issues and path', (sc.get('summary') or {}).get('errors', 0) > 0
              and sc.get('path', '').endswith('draft.fa.txt'), _short(sc.get('summary')))
        r = c.call('lint_file', {'path': 'inside.txt'})
        check_data('lint_file inside --root (relative)', r, 'lint_file')
        r = c.call('lint_file', {'path': REL_SAMPLES + '/locales/fa.json'})
        sc = check_data('lint_file locale', r, 'lint_file')
        R.add('lint_file locale: issues keyed by locale key',
              any(i.get('key') == 'cart.retry' for i in sc.get('issues') or []), _short(sc.get('issues')))
        r = c.call('lint_file', {'path': REL_SAMPLES + '/catalog.csv'})
        sc = check_data('lint_file csv', r, 'lint_file')
        R.add('lint_file csv: issues keyed row n/sku/column',
              any((i.get('key') or '').startswith('row 3/T-200/') for i in sc.get('issues') or []),
              _short(sc.get('issues')))
        check_err('lint_file outside the roots (absolute)', c.call('lint_file', {'path': os.path.join(outside, 'outside.txt')}))
        check_err('lint_file outside the roots (../)', c.call('lint_file', {'path': '../outside/outside.txt'}))
        r = c.call('lint_file', {'path': '../outside/outside.txt'})
        R.add('lint_file outside the roots: message says so', 'outside' in _text(_result(r)), _short(r))
        check_err('lint_file with a missing file', c.call('lint_file', {'path': 'missing.txt'}))
        r = c.call('lint_file', {'path': 'SKILL.md'})
        R.add('lint_file: a missing project file never resolves to the skill copy', _is_tool_error(r)
              and 'not found' in _text(_result(r)), _short(r))
        check_err('lint_file with an unsupported extension', c.call('lint_file', {'path': 'blob.bin'}))
        check_err('lint_file with a NUL in the path', c.call('lint_file', {'path': 'inside\u0000.txt'}))
        check_err('lint_file without path', c.call('lint_file', {}))
        if os.name == 'nt':
            check_err('lint_file with an alternate data stream', c.call('lint_file', {'path': 'inside.txt:stream'}))
            check_err('lint_file with a device name', c.call('lint_file', {'path': 'CON.txt'}))
        # symlink escape
        link = os.path.join(root, 'escape')
        try:
            os.symlink(outside, link, target_is_directory=True)
        except (OSError, NotImplementedError, AttributeError) as e:
            R.skip('lint_file symlink escape -> isError', 'symlinks unavailable (%s)' % type(e).__name__)
        else:
            check_err('lint_file symlink escape', c.call('lint_file', {'path': 'escape/outside.txt'}))

        # get_playbook
        pb_files = sorted(f for f in os.listdir(os.path.join(SKILL, 'references')) if re.match(r'^playbooks-.+\.md$', f))
        target = None
        for f in pb_files:
            for lvl, slug in _headings(os.path.join(SKILL, 'references', f)):
                if lvl == 3:
                    target = (f, slug)
                    break
            if target:
                break
        if target:
            r = c.call('get_playbook', {'task': target[1], 'limit': 1})
            txt = _text(_result(r))
            R.add('get_playbook: an exact anchor wins', (_result(r) or {}).get('isError') is False
                  and txt.startswith('# ') and '(references/%s#%s)' % target in txt.split('\n')[0]
                  and 'Other matches' not in txt, _short(txt))
            r = c.call('get_playbook', {'task': '%s#%s' % target})
            R.add('get_playbook: file#anchor form', '(references/%s#%s)' % target in _text(_result(r)), _short(r))
            R.add('get_playbook: no structuredContent', 'structuredContent' not in (_result(r) or {}))
        else:
            R.skip('get_playbook: an exact anchor wins', 'no playbook headings found')
        row = _index_probe()
        if row:
            r = c.call('get_playbook', {'task': row[0], 'limit': 3})
            R.add('get_playbook: free text in the task index', (_result(r) or {}).get('isError') is False
                  and _text(_result(r)).startswith('# '), _short(r))
        else:
            R.skip('get_playbook: free text in the task index', 'no task-index row links to an existing anchor yet')
        check_err('get_playbook with nothing to match', c.call('get_playbook', {'task': 'qqqq zzzz xxyyzz'}))
        check_err('get_playbook with a one-letter task', c.call('get_playbook', {'task': 'x'}))
        check_err('get_playbook with limit 9', c.call('get_playbook', {'task': 'caption', 'limit': 9}))

        # get_reference_section
        r = c.call('get_reference_section', {'path': 'references/router.md'})
        txt = _text(_result(r))
        R.add('get_reference_section: contents list', (_result(r) or {}).get('isError') is False
              and 'Contents:' in txt and txt.startswith('# '), _short(txt))
        m = re.search(r'\(#([^)\s]+)\)', txt)
        if m:
            r = c.call('get_reference_section', {'path': 'router.md', 'anchor': m.group(1), 'max_chars': 1000})
            t2 = _text(_result(r))
            R.add('get_reference_section: one section by anchor', t2.startswith('#') and '#%s)' % m.group(1)
                  in t2.split('\n')[0] and len(t2) <= 1100, _short(t2))
        r = c.call('get_reference_section', {'path': 'references/router.md', 'anchor': 'no-such-anchor-xyz'})
        R.add('get_reference_section: unknown anchor -> isError with the anchor list',
              _is_tool_error(r) and 'Anchors:' in _text(_result(r)), _short(r))
        r = c.call('get_reference_section', {'path': 'profiles/_template.json', 'anchor': 'dials'})
        R.add('get_reference_section: JSON key', '"warmth"' in _text(_result(r)), _short(r))
        check_err('get_reference_section with ../', c.call('get_reference_section', {'path': 'references/../SKILL.md'}))
        check_err('get_reference_section with .. that stays inside',
                  c.call('get_reference_section', {'path': 'references/fa/../router.md'}))
        check_err('get_reference_section outside references/', c.call('get_reference_section', {'path': 'scripts/x.md'}))
        check_err('get_reference_section with a .txt path', c.call('get_reference_section', {'path': 'router.txt'}))
        check_err('get_reference_section with max_chars 10', c.call('get_reference_section',
                                                                    {'path': 'router.md', 'max_chars': 10}))

        # profile_lookup
        r = c.call('profile_lookup', {'project_dir': REL_SAMPLES + '/project'})
        sc = check_data('profile_lookup project', r, 'profile_lookup')
        R.add('profile_lookup: project VOICE.md and voice.json', sc.get('source') == 'project' and sc.get('found')
              and (sc.get('profile') or {}).get('name') == 'mcp-sample' and sc.get('is_brand_profile') is True
              and bool((sc.get('learnings') or {}).get('text')), _short(sc))
        r = c.call('profile_lookup', {'name': 'userbrand'})
        sc = check_data('profile_lookup user', r, 'profile_lookup')
        R.add('profile_lookup: ~/.whalory/profiles/<brand>', sc.get('source') == 'user', _short(sc))
        r = c.call('profile_lookup', {'name': 'whalory'})
        sc = check_data('profile_lookup whalory', r, 'profile_lookup')
        R.add('profile_lookup: Whalory\'s own voice', sc.get('source') == 'whalory' and sc.get('found'), _short(sc))
        r = c.call('profile_lookup', {'name': 'saas', 'language': 'fa'})
        sc = check_data('profile_lookup starter', r, 'profile_lookup')
        R.add('profile_lookup: a starter is not a brand profile', sc.get('source') == 'starter'
              and sc.get('is_brand_profile') is False, _short(sc))
        r = c.call('profile_lookup', {'industry': 'cafe'})
        sc = check_data('profile_lookup by industry', r, 'profile_lookup')
        R.add('profile_lookup: closest starter by industry', sc.get('source') == 'starter', _short(sc))
        r = c.call('profile_lookup', {'name': 'no-such-brand-xyz'})
        sc = check_data('profile_lookup none', r, 'profile_lookup')
        R.add('profile_lookup: none found, starters suggested', sc.get('found') is False
              and sc.get('source') == 'none' and len(sc.get('starters') or []) > 0, _short(sc))
        check_err('profile_lookup with a bad name', c.call('profile_lookup', {'name': 'a b'}))
        check_err('profile_lookup outside the roots', c.call('profile_lookup', {'project_dir': outside}))

        # Pro tools
        if 'detect_context' in names:
            r = c.call('detect_context', {'dir': REL_SAMPLES + '/project', 'request': 'write a caption for our tea'})
            sc = check_data('detect_context', r, 'detect_context')
            R.add('detect_context: route and request language', sc.get('route') in (
                'repo-microcopy', 'repo-content', 'bulk-catalog', 'standard') and sc.get('request_lang') == 'en'
                and bool(sc.get('summary')), _short(sc.get('summary')))
            check_err('detect_context outside the roots', c.call('detect_context', {'dir': outside}))
            check_err('detect_context with max_entries 50', c.call('detect_context', {'max_entries': 50}))
        if 'channel_limits' in names:
            r = c.call('channel_limits', {})
            sc = check_data('channel_limits all', r, 'channel_limits')
            R.add('channel_limits: channels listed', sc.get('count', 0) > 0, _short(sc.get('count')))
            r = c.call('channel_limits', {'channel': 'instagram', 'field': 'caption'})
            sc = check_data('channel_limits instagram.caption', r, 'channel_limits')
            ch = (sc.get('channels') or [{}])[0]
            R.add('channel_limits: one channel, one field', ch.get('id') == 'instagram'
                  and [f.get('field') for f in ch.get('fields') or []] == ['caption'], _short(ch))
            r = c.call('channel_limits', {'region': 'ir', 'limit': 100})
            sc = check_data('channel_limits region ir', r, 'channel_limits')
            R.add('channel_limits: region filter', all(x.get('region') == 'ir' for x in sc.get('channels') or []))
            check_err('channel_limits with an unknown channel', c.call('channel_limits', {'channel': 'no-such-channel'}))
            check_err('channel_limits with limit 0', c.call('channel_limits', {'limit': 0}))
        if 'compare_texts' in names:
            before = '\u0642\u06CC\u0645\u062A \u06F2\u06F5\u06F0 \u0647\u0632\u0627\u0631 \u062A\u0648\u0645\u0627\u0646\u060C ' \
                     '\u0641\u0642\u0637 \u062A\u0627 \u062C\u0645\u0639\u0647.'
            after = '\u0642\u06CC\u0645\u062A \u06F3\u06F0\u06F0 \u0647\u0632\u0627\u0631 \u062A\u0648\u0645\u0627\u0646.'
            r = c.call('compare_texts', {'before': before, 'after': after})
            sc = check_data('compare_texts fa', r, 'compare_texts')
            R.add('compare_texts: changed number -> review', sc.get('verdict') == 'review'
                  and len((sc.get('added') or {}).get('numbers') or []) > 0, _short(sc))
            r = c.call('compare_texts', {'before': 'Save 20% until Friday.', 'after': 'Save 30% now.', 'lang': 'en'})
            sc = check_data('compare_texts en', r, 'compare_texts')
            R.add('compare_texts en: review', sc.get('verdict') == 'review', _short(sc))
            check_err('compare_texts without after', c.call('compare_texts', {'before': 'x'}))
        if 'ab_test_size' in names:
            r = c.call('ab_test_size', {'mode': 'size', 'base_rate': 0.03, 'mde': 0.2, 'daily_traffic': 1000})
            sc = check_data('ab_test_size size', r, 'ab_test_size')
            R.add('ab_test_size size: per_variant and days', sc.get('per_variant', 0) > 1000
                  and sc.get('total') == 2 * sc.get('per_variant', 0) and sc.get('days', 0) > 0, _short(sc))
            r = c.call('ab_test_size', {'mode': 'test', 'a': {'successes': 120, 'total': 4000},
                                        'b': {'successes': 160, 'total': 4000}})
            sc = check_data('ab_test_size test', r, 'ab_test_size')
            R.add('ab_test_size test: p-value and verdict', 0 <= sc.get('p_value', -1) <= 1
                  and isinstance(sc.get('significant'), bool), _short(sc))
            check_err('ab_test_size size without mde', c.call('ab_test_size', {'mode': 'size', 'base_rate': 0.03}))
            check_err('ab_test_size test with successes > total', c.call('ab_test_size', {
                'mode': 'test', 'a': {'successes': 9, 'total': 5}, 'b': {'successes': 1, 'total': 5}}))
            check_err('ab_test_size with base_rate 1.5', c.call('ab_test_size', {'mode': 'size', 'base_rate': 1.5,
                                                                                 'mde': 0.1}))
        for t in ORDER:
            if t not in names:
                r = c.call(t, {})
                R.add('%s is not callable in this tier (-32602)' % t, (_error(r) or {}).get('code') == -32602)

        r = c.call('no_such_tool', {})
        R.add('unknown tool -> -32602', (_error(r) or {}).get('code') == -32602, _short(r))
        r = c.request('tools/call', {'name': 'lint_text', 'arguments': 'text'})
        R.add('tools/call with arguments not an object -> -32602', (_error(r) or {}).get('code') == -32602)

        # resources
        seen, cursor, pages = [], None, 0
        while True:
            r = c.request('resources/list', {'cursor': cursor} if cursor else {})
            res = _result(r) or {}
            seen += [x.get('uri') for x in res.get('resources') or []]
            pages += 1
            cursor = res.get('nextCursor')
            if not cursor or pages > 20:
                break
        n = (report or {}).get('resources')
        R.add('resources/list: pagination covers every resource once', len(seen) == len(set(seen))
              and (n is None or len(seen) == n) and 'whalory://skill/SKILL.md' in seen,
              '%d resources in %d pages' % (len(seen), pages))
        R.add('resources/list: 50 per page', pages == max(1, -(-len(seen) // 50)), '%d pages' % pages)
        r = c.request('resources/list', {'cursor': 'not-a-cursor'})
        R.add('resources/list: bad cursor -> -32602', (_error(r) or {}).get('code') == -32602, _short(r))
        r = c.request('resources/templates/list')
        R.add('resources/templates/list', [x.get('uriTemplate') for x in (_result(r) or {}).get('resourceTemplates') or []]
              == ['whalory://references/{+path}', 'whalory://profiles/{+path}'], _short(r))
        r = c.request('resources/read', {'uri': 'whalory://skill/SKILL.md'})
        cont = ((_result(r) or {}).get('contents') or [{}])[0]
        R.add('resources/read: SKILL.md', cont.get('mimeType') == 'text/markdown' and 'name:' in cont.get('text', '')
              and cont.get('uri') == 'whalory://skill/SKILL.md', _short(r))
        jres = [u for u in seen if u.endswith('.json')]
        if jres:
            r = c.request('resources/read', {'uri': jres[0]})
            cont = ((_result(r) or {}).get('contents') or [{}])[0]
            R.add('resources/read: JSON resource', cont.get('mimeType') == 'application/json', _short(r))
        for label, uri in _traversal_uris():
            r = c.request('resources/read', {'uri': uri})
            e = _error(r) or {}
            R.add('resources/read %s -> -32002 (legacy)' % label, e.get('code') == -32002
                  and (e.get('data') or {}).get('uri') == uri, _short(r))

        # prompts
        r = c.request('prompts/list')
        plist = [p.get('name') for p in (_result(r) or {}).get('prompts') or []]
        R.add('prompts/list: write, review and voice at least', {'write', 'review', 'voice'} <= set(plist), _short(plist))
        r = c.request('prompts/get', {'name': 'write', 'arguments': {'task': 'LinkedIn post for our launch'}})
        msgs = (_result(r) or {}).get('messages') or []
        R.add('prompts/get write: embedded SKILL.md and the task', len(msgs) == 2
              and msgs[0]['content'].get('type') == 'resource'
              and msgs[0]['content']['resource'].get('uri') == 'whalory://skill/SKILL.md'
              and 'LinkedIn post for our launch' in msgs[1]['content'].get('text', ''), _short(r))
        r = c.request('prompts/get', {'name': 'write', 'arguments': {}})
        R.add('prompts/get: missing required argument -> -32602', (_error(r) or {}).get('code') == -32602, _short(r))
        r = c.request('prompts/get', {'name': 'no-such-prompt', 'arguments': {}})
        R.add('prompts/get: unknown prompt -> -32602', (_error(r) or {}).get('code') == -32602, _short(r))
        if 'transcreate' in plist:
            r = c.request('prompts/get', {'name': 'transcreate', 'arguments': {'text': 'x', 'target_language': 'de'}})
            R.add('prompts/get transcreate: bad target_language -> -32602', (_error(r) or {}).get('code') == -32602)

        # JSON-RPC edge cases
        for label, raw, code in (('a garbage line', b'this is not json', -32700),
                                 ('a batch []', b'[]', -32600),
                                 ('id true', b'{"jsonrpc":"2.0","id":true,"method":"ping"}', -32600),
                                 ('id null', b'{"jsonrpc":"2.0","id":null,"method":"ping"}', -32600),
                                 ('id 1.5', b'{"jsonrpc":"2.0","id":1.5,"method":"ping"}', -32600),
                                 ('jsonrpc 1.0', b'{"jsonrpc":"1.0","method":"ping"}', -32600)):
            c.send_raw(raw)
            m = c.recv()
            R.add('%s -> %d without id' % (label, code), isinstance(m, dict) and 'id' not in m
                  and (m.get('error') or {}).get('code') == code, _short(m))
        deep = '{"jsonrpc":"2.0","id":77,"method":"ping","params":{"x":' + '[' * 70 + ']' * 70 + '}}'
        c.send_raw(deep.encode('ascii'))
        m = c.wait_for(77)
        R.add('JSON nested deeper than 64 -> -32600', (_error(m) or {}).get('code') == -32600, _short(m))
        c.send_raw(b'{"jsonrpc":"2.0","id":88,"method":"ping","x":"' + b'a' * (16 * 1024 * 1024 + 16) + b'"}')
        m = c.recv()
        R.add('a line over 16 MB -> -32700 without id', isinstance(m, dict) and 'id' not in m
              and (m.get('error') or {}).get('code') == -32700, _short(m))
        r = c.request('ping', rid='after-big')
        R.add('the loop reads on after an oversized line', _result(r) == {}, _short(r))
        r = c.call('lint_text', {'text': 'a' * (1024 * 1024 + 64)})
        R.add('tool arguments over 1 MB -> isError', _is_tool_error(r) and '1 MB' in _text(_result(r)), _short(r))
        r = c.request('logging/setLevel', {'level': 'info'})
        R.add('logging/setLevel -> -32601', (_error(r) or {}).get('code') == -32601, _short(r))
        r = c.request('no/such/method')
        e = _error(r) or {}
        R.add('unknown method -> -32601 "Method not found"', e.get('code') == -32601
              and e.get('message') == 'Method not found', _short(r))
        r = c.request('ping', rid='after-errors')
        R.add('the loop survives bad input', _result(r) == {})
        c.send({'jsonrpc': '2.0', 'id': 555, 'result': {}})  # a response from the "client": ignored
        r = c.request('ping', rid='after-response')
        R.add('a client response is ignored', _result(r) == {} and not any(n.get('id') == 555 for n in c.notes))
    finally:
        code, dt = c.close()
    R.add('every stdout line is JSON', not c.bad, _short([b.decode('utf-8', 'replace') for b in c.bad]))
    R.add('stdin EOF -> exit 0 within 2 s', code == 0 and dt < 2.0, 'code %s in %.2f s' % (code, dt))
    R.add('no stack trace on stderr', not any('Traceback' in s for s in c.stderr), _short(''.join(c.stderr)))


def _traversal_uris():
    return [('../', 'whalory://references/../SKILL.md'),
            ('%2e%2e', 'whalory://references/%2e%2e/SKILL.md'),
            ('.. that stays inside', 'whalory://references/fa/../router.md'),
            ('. segment', 'whalory://references/./router.md'),
            ('absolute', 'whalory://references//etc/passwd'),
            ('drive letter', 'whalory://references/C:/Windows/win.ini'),
            ('backslash', 'whalory://references/..\\SKILL.md'),
            ('%5c', 'whalory://references/..%5cSKILL.md'),
            ('NUL', 'whalory://references/router%00.md'),
            ('CON.md', 'whalory://references/CON.md'),
            ('wrong extension', 'whalory://references/router.txt'),
            ('unlisted root file', 'whalory://skill/VERSION.md'),
            ('file scheme', 'file:///etc/passwd'),
            ('missing file', 'whalory://references/missing.md')]


def _index_probe():
    """(signal phrase, file, anchor) of a task-index row whose link resolves, or None."""
    path = os.path.join(SKILL, 'references', 'playbooks.md')
    if not os.path.isfile(path):
        return None
    with open(path, encoding='utf-8') as f:
        lines = f.read().split('\n')
    head = None
    for ln in lines:
        if not ln.lstrip().startswith('|'):
            continue
        cells = [x.strip() for x in ln.strip().strip('|').split('|')]
        if head is None:
            if cells and cells[0].lower() in ('task', '\u06A9\u0627\u0631'):
                head = [x.lower() for x in cells]
            continue
        if set(''.join(cells)) <= set('-: '):
            continue
        m = re.search(r'\]\(([^)#\s]*)#([^)\s]+)\)', ln)
        if not m or len(cells) != len(head):
            continue
        fname = m.group(1) or 'playbooks.md'
        full = os.path.join(SKILL, 'references', os.path.basename(fname))
        if not os.path.isfile(full) or m.group(2) not in [s for _, s in _headings(full)]:
            continue
        sig = re.findall('\u00ab([^\u00bb]+)\u00bb', ln) or re.findall(r'"([^"]+)"', ln)
        phrase = sig[0] if sig else cells[0]
        if len(phrase.strip()) >= 2:
            return phrase.strip(), fname, m.group(2)
    return None


def t_modern(R):
    c = Client([])
    try:
        r = c.request('server/discover', modern=True, rid='d-1')
        res = _result(r) or {}
        R.add('server/discover: versions, resultType, ttlMs, cacheScope, serverInfo',
              res.get('supportedVersions') == [MODERN] and res.get('resultType') == 'complete'
              and res.get('ttlMs') == 3600000 and res.get('cacheScope') == 'public'
              and ((res.get('_meta') or {}).get(SINFO) or {}).get('name') == 'whalory'
              and set(res.get('capabilities') or {}) == {'tools', 'prompts', 'resources'}, _short(res))
        r = c.request('tools/list', modern=True)
        res = _result(r) or {}
        R.add('modern tools/list: resultType, ttlMs 3600000', res.get('resultType') == 'complete'
              and res.get('ttlMs') == 3600000 and res.get('cacheScope') == 'public' and len(res.get('tools') or []) > 0)
        r = c.request('prompts/list', modern=True)
        R.add('modern prompts/list: ttlMs 3600000', (_result(r) or {}).get('ttlMs') == 3600000)
        r = c.request('resources/templates/list', modern=True)
        R.add('modern resources/templates/list: ttlMs 3600000', (_result(r) or {}).get('ttlMs') == 3600000)
        r = c.request('resources/list', modern=True)
        R.add('modern resources/list: ttlMs 300000', (_result(r) or {}).get('ttlMs') == 300000)
        r = c.request('resources/read', {'uri': 'whalory://skill/SKILL.md'}, modern=True)
        res = _result(r) or {}
        R.add('modern resources/read: ttlMs 300000 and serverInfo', res.get('ttlMs') == 300000
              and res.get('resultType') == 'complete' and SINFO in (res.get('_meta') or {}))
        for label, uri in _traversal_uris()[:11]:
            r = c.request('resources/read', {'uri': uri}, modern=True)
            e = _error(r) or {}
            R.add('modern resources/read %s -> -32602' % label, e.get('code') == -32602
                  and (e.get('data') or {}).get('uri') == uri, _short(r))
        r = c.request('tools/call', {'name': 'lint_text', 'arguments': {'text': '\u0633\u0644\u0627\u0645.'}},
                      modern=True)
        res = _result(r) or {}
        R.add('modern tools/call: resultType and serverInfo', res.get('resultType') == 'complete'
              and SINFO in (res.get('_meta') or {}) and 'structuredContent' in res, _short(res))
        r = c.request('prompts/get', {'name': 'voice', 'arguments': {'brand': 'Sample Tea House'}}, modern=True)
        res = _result(r) or {}
        R.add('modern prompts/get: no ttlMs', res.get('resultType') == 'complete' and 'ttlMs' not in res
              and len(res.get('messages') or []) == 2, _short(res))
        r = c.request('tools/list', modern=True, meta={PV: '1900-01-01', CAPS: {}})
        e = _error(r) or {}
        R.add('unsupported protocol version -> -32022 with data', e.get('code') == -32022
              and e.get('data') == {'supported': [MODERN], 'requested': '1900-01-01'}, _short(r))
        r = c.request('tools/list', modern=True, meta={PV: MODERN})
        R.add('missing clientCapabilities -> -32602', (_error(r) or {}).get('code') == -32602, _short(r))
        r = c.request('tools/list', {})
        e = _error(r) or {}
        R.add('no initialize and no _meta -> -32602 without version numbers', e.get('code') == -32602
              and not re.search(r'20\d\d-\d\d-\d\d', json.dumps(e)), _short(r))
        r = c.request('server/discover', {})
        R.add('server/discover without _meta -> an error, not a crash', (_error(r) or {}).get('code') == -32602)
        # subscriptions/listen: an acknowledgement, no response, then cancelled
        c.send({'jsonrpc': '2.0', 'id': 'sub-1', 'method': 'subscriptions/listen',
                'params': {'_meta': {PV: MODERN, CAPS: {}}, 'notifications': {'toolsListChanged': True}}})
        ack = c.recv()
        R.add('subscriptions/listen -> acknowledgement', isinstance(ack, dict)
              and ack.get('method') == 'notifications/subscriptions/acknowledged' and 'id' not in ack
              and ((ack.get('params') or {}).get('_meta') or {}).get(SUBID) == 'sub-1', _short(ack))
        c.send({'jsonrpc': '2.0', 'method': 'notifications/cancelled', 'params': {'requestId': 'sub-1'}})
        r = c.request('ping', modern=True, rid='p-2')
        R.add('the listen stream stays silent; ping still works', (_result(r) or {}).get('resultType') == 'complete'
              and not any(n.get('id') == 'sub-1' for n in c.notes), _short(c.notes))
        r = c.request('ping', rid=7)
        R.add('an integer id keeps its type', isinstance(r, dict) and r.get('id') == 7 and type(r['id']) is int)
    finally:
        code, dt = c.close()
    R.add('modern session: every stdout line is JSON; exit 0', not c.bad and code == 0, 'code %s' % code)


def t_old_legacy(R):
    """Clients on 2025-03-26 or 2024-11-05 do not know outputSchema or structuredContent."""
    c = Client([])
    try:
        c.request('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {}})
        r = c.request('tools/list')
        tools = (_result(r) or {}).get('tools') or []
        R.add('2025-03-26: tools/list without outputSchema', tools and all('outputSchema' not in t for t in tools))
        r = c.call('lint_text', {'text': '\u0633\u0644\u0627\u0645.'})
        res = _result(r) or {}
        R.add('2025-03-26: tools/call with the JSON text only', 'structuredContent' not in res
              and isinstance(json.loads(_text(res) or 'null'), dict), _short(res))
    finally:
        c.close()


def t_env_roots(R, tmp):
    """WHALORY_ROOTS and --root placeholders that a host did not expand."""
    d = os.path.join(tmp, 'envroot')
    os.makedirs(d)
    with open(os.path.join(d, 'env.txt'), 'w', encoding='utf-8') as f:
        f.write('\u0633\u0644\u0627\u0645.\n')
    c = Client(['--root', '${CLAUDE_PROJECT_DIR}', '--root'], env={'WHALORY_ROOTS': d, 'WHALORY_LANG': 'xx'})
    try:
        c.request('initialize', {'protocolVersion': LEGACY[0], 'capabilities': {}})
        r = c.call('lint_file', {'path': 'env.txt'})
        R.add('WHALORY_ROOTS is a root; unexpanded ${...} and an empty --root are ignored',
              (_result(r) or {}).get('isError') is False, _short(r))
    finally:
        code, _ = c.close()
    R.add('bad WHALORY_LANG does not stop the server', code == 0)


def _tree_state(folder):
    """{relative path: (size, mtime_ns)} for every file and folder under folder."""
    out = {}
    for dp, dn, fn in os.walk(folder):
        for n in dn + fn:
            p = os.path.join(dp, n)
            st = os.stat(p)
            out[os.path.relpath(p, folder)] = (st.st_size if n in fn else -1, st.st_mtime_ns)
    return out


def t_old_names(R, tmp):
    """Names from before the rename (Whalya 2): WHALYA_* and ~/.whalya/profiles are read, never written;
    the house-voice id whalya finds whalory."""
    new_root, old_root = os.path.join(tmp, 'names-new'), os.path.join(tmp, 'names-old')
    _write(os.path.join(new_root, 'new-only.txt'), 'سلام.\n')
    _write(os.path.join(old_root, 'old-only.txt'), 'سلام.\n')
    # both set: WHALORY_ROOTS wins, and the WHALYA_ROOTS folder is not a root
    c = Client([], env={'WHALORY_ROOTS': new_root, 'WHALYA_ROOTS': old_root}, cwd=tmp)
    try:
        _init(c)
        ok_new = (_result(c.call('lint_file', {'path': 'new-only.txt'})) or {}).get('isError') is False
        r = c.call('lint_file', {'path': os.path.join(old_root, 'old-only.txt')})
        R.add('WHALORY_ROOTS wins over WHALYA_ROOTS', ok_new and (_result(r) or {}).get('isError') is True,
              _short(r))
    finally:
        c.close()
    # only the old name set: it still works
    c = Client([], env={'WHALYA_ROOTS': old_root}, cwd=tmp)
    try:
        _init(c)
        r = c.call('lint_file', {'path': 'old-only.txt'})
        R.add('WHALYA_ROOTS alone still sets the root', (_result(r) or {}).get('isError') is False, _short(r))
    finally:
        c.close()
    # ~/.whalya/profiles: read when ~/.whalory/profiles lacks the name, never written
    home = os.path.join(tmp, 'names-home')
    new_dir, old_dir = os.path.join(home, '.whalory', 'profiles'), os.path.join(home, '.whalya', 'profiles')
    for d, brand, warmth in ((old_dir, 'oldbrand', 2), (old_dir, 'shared', 1), (new_dir, 'shared', 5)):
        _write(os.path.join(d, brand + '.json'),
               json.dumps({'schema_version': 2, 'name': brand, 'dials': {'warmth': warmth}}))
    before = _tree_state(old_dir)
    c = Client([], env={'HOME': home, 'USERPROFILE': home, 'WHALORY_ROOTS': new_root}, cwd=tmp)
    try:
        _init(c)
        sc = _sc(c.call('profile_lookup', {'name': 'oldbrand'}))
        R.add('profile_lookup: a profile only in ~/.whalya/profiles is read, with a warning',
              sc.get('source') == 'user' and (sc.get('profile') or {}).get('name') == 'oldbrand'
              and '.whalya' in (sc.get('path') or '')
              and any('~/.whalya/profiles' in w for w in sc.get('warnings') or []), _short(sc))
        sc = _sc(c.call('profile_lookup', {'name': 'shared'}))
        R.add('profile_lookup: ~/.whalory/profiles wins over ~/.whalya/profiles',
              sc.get('source') == 'user' and '.whalory' in (sc.get('path') or '')
              and ((sc.get('profile') or {}).get('dials') or {}).get('warmth') == 5, _short(sc))
        sc = _sc(c.call('profile_lookup', {'name': 'whalya'}))
        R.add('profile_lookup: the legacy id whalya resolves to whalory',
              sc.get('source') == 'whalory' and sc.get('found')
              and (sc.get('path') or '').replace('\\', '/').endswith('profiles/whalory.json'), _short(sc))
        sc = _sc(c.call('profile_lookup', {'name': 'whalya', 'language': 'en'}))
        R.add('profile_lookup: whalya in English resolves to whalory.en',
              (sc.get('path') or '').replace('\\', '/').endswith('profiles/whalory.en.json'), _short(sc))
        r = c.call('lint_text', {'text': 'We ship on Monday.', 'lang': 'en', 'profile': 'whalya'})
        R.add('lint_text: profile whalya resolves to the house voice', (_result(r) or {}).get('isError') is False,
              _short(r))
    finally:
        c.close()
    R.add('~/.whalya/profiles stays untouched (read only)', _tree_state(old_dir) == before,
          _short(sorted(_tree_state(old_dir))))


# ---------------------------------------------------------------- security review fixes (3.0.0)
SECRET = 'SECRET-TOKEN-7f3a9c'


def _write(path, text):
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def _dir_link(target, link):
    """A directory junction (Windows; needs no privilege) or a symbolic link: its kind, or None."""
    if os.name == 'nt':
        try:
            import _winapi
            _winapi.CreateJunction(target, link)
            return 'junction'
        except Exception:
            pass
    try:
        os.symlink(target, link, target_is_directory=True)
        return 'symlink'
    except (OSError, NotImplementedError, AttributeError):
        return None


def _file_link(target, link):
    try:
        os.symlink(target, link)
        return True
    except (OSError, NotImplementedError, AttributeError):
        return False


def _file_uri(path):
    from urllib.parse import quote
    p = os.path.abspath(path).replace('\\', '/')
    return 'file://' + quote(p if p.startswith('/') else '/' + p, safe='/:')


def _init(c, caps=None):
    return c.request('initialize', {'protocolVersion': LEGACY[0], 'capabilities': caps or {},
                                    'clientInfo': {'name': 'selftest', 'version': '1'}})


def _sc(resp):
    return (_result(resp) or {}).get('structuredContent') or {}


def t_confinement(R, tmp, names):
    """profile_lookup, its learnings note and detect_context never follow a link out of the roots."""
    base = os.path.join(tmp, 'conf')
    outside = os.path.join(base, 'outside')
    _write(os.path.join(outside, 'voice.json'), json.dumps({'schema_version': 2, 'name': SECRET,
                                                            'brand': {'latin': SECRET}}))
    _write(os.path.join(outside, 'VOICE.md'), '# %s\n' % SECRET)
    _write(os.path.join(outside, 'LEARNINGS.md'), '# Learnings\n\n%s\n' % SECRET)
    _write(os.path.join(outside, 'locales', 'fa.json'), '{"a": "سلام"}')
    proj = os.path.join(base, 'proj')
    _write(os.path.join(proj, 'README.md'), 'Hello.\n')
    kind = _dir_link(outside, os.path.join(proj, 'voice'))
    if kind is None:
        R.skip('profile_lookup: a linked voice/ folder is not followed', 'no junctions or symlinks here')
        return
    _dir_link(outside, os.path.join(proj, 'junc'))
    proj3 = os.path.join(base, 'proj3')
    _write(os.path.join(proj3, 'VOICE.md'), '# Voice\n')
    _write(os.path.join(proj3, 'voice.json'), json.dumps({'schema_version': 2, 'name': 'proj3'}))
    linked_note = _file_link(os.path.join(outside, 'LEARNINGS.md'), os.path.join(proj3, 'LEARNINGS.md'))
    git = os.path.join(base, 'gitrepo')
    os.makedirs(os.path.join(git, '.git'))
    _write(os.path.join(git, 'VOICE.md'), '# %s\n' % SECRET)
    _write(os.path.join(git, 'voice.json'), json.dumps({'schema_version': 2, 'name': SECRET}))
    _write(os.path.join(git, 'LEARNINGS.md'), SECRET + '\n')
    docs = os.path.join(git, 'docs')
    _write(os.path.join(docs, 'intro.md'), 'Hello.\n')
    c = Client(['--root', proj, proj3, docs])
    try:
        _init(c)
        r = c.call('profile_lookup', {})
        sc = _sc(r)
        R.add('profile_lookup: a %s voice/ that leads outside the roots is not followed' % kind,
              (_result(r) or {}).get('isError') is False and sc.get('source') != 'project'
              and SECRET not in json.dumps(r), _short(sc))
        if linked_note:
            r = c.call('profile_lookup', {'project_dir': proj3})
            sc = _sc(r)
            R.add('profile_lookup: a LEARNINGS.md linked outside the roots is not read',
                  sc.get('source') == 'project' and sc.get('learnings') is None and SECRET not in json.dumps(r),
                  _short(sc))
        else:
            R.skip('profile_lookup: a LEARNINGS.md linked outside the roots is not read',
                   'file symlinks need a privilege here')
        r = c.call('profile_lookup', {'project_dir': docs})
        R.add('profile_lookup: no profile from the git root above the roots',
              _sc(r).get('source') != 'project' and SECRET not in json.dumps(r), _short(_sc(r)))
        check = c.call('lint_file', {'path': 'junc/LEARNINGS.md'})
        R.add('lint_file through a %s to outside the roots -> isError' % kind, _is_tool_error(check), _short(check))
        if 'detect_context' in names:
            r = c.call('detect_context', {'dir': proj})
            probe = _sc(r).get('probe') or {}
            locs = json.dumps(probe.get('locale_files'))
            R.add('detect_context: a %s that leads outside the roots is not walked' % kind,
                  (_result(r) or {}).get('isError') is False and 'junc' not in locs and 'voice' not in locs
                  and (probe.get('probe') or {}).get('links_outside', 0) >= 2 and SECRET not in json.dumps(r),
                  _short(probe.get('probe')))
            r = c.call('detect_context', {'dir': docs})
            probe = _sc(r).get('probe') or {}
            vp = probe.get('voice_profile') or {}
            R.add('detect_context: no git root, profile or learnings above the roots; is_repo still set',
                  probe.get('is_repo') is True and probe.get('git_root') is None and not vp.get('chosen')
                  and not any('..' in (x.get('path') or '') for x in vp.get('candidates') or [])
                  and probe.get('learnings') is None and SECRET not in json.dumps(r), _short(vp))
    finally:
        c.close()


def t_roots_fail_closed(R, tmp, names):
    """Unusable --root or WHALORY_ROOTS values never fall back to the working folder."""
    base = os.path.join(tmp, 'failclosed')
    proj = os.path.join(base, 'proj')
    _write(os.path.join(proj, 'a.txt'), 'سلام.\n')
    cases = [('an unexpanded ${...} --root', ['--root', '${CLAUDE_PROJECT_DIR}'], None),
             ('a --root folder that does not exist', ['--root', os.path.join(base, 'missing')], None),
             ('--root with no folder', ['--root'], None),
             ('an unexpanded WHALORY_ROOTS', [], {'WHALORY_ROOTS': '${workspaceFolder}'})]
    for n, (label, args, env) in enumerate(cases):
        c = Client(args, env=env, cwd=proj)
        try:
            _init(c)
            r = c.call('lint_file', {'path': 'a.txt'})
            R.add('fails closed with %s: no working-folder fallback, an actionable error' % label,
                  _is_tool_error(r) and '--root' in _text(_result(r)), _short(r))
            if n:
                continue
            r = c.call('lint_file', {'path': os.path.join(proj, 'a.txt')})
            R.add('fails closed: an absolute path in the working folder -> isError', _is_tool_error(r), _short(r))
            r = c.call('lint_file', {'path': REL_SAMPLES + '/draft.fa.txt'})
            R.add('fails closed: the skill folder stays readable', (_result(r) or {}).get('isError') is False,
                  _short(r))
            r = c.call('profile_lookup', {'name': 'whalory'})
            sc = _sc(r)
            R.add('fails closed: profile_lookup skips the project step and says so',
                  sc.get('source') == 'whalory' and any('not checked' in w for w in sc.get('warnings') or []),
                  _short(sc))
            if 'detect_context' in names:
                R.add('fails closed: detect_context without dir -> isError',
                      _is_tool_error(c.call('detect_context', {})))
                R.add('fails closed: detect_context on a system folder -> isError',
                      _is_tool_error(c.call('detect_context', {'dir': os.path.dirname(sys.executable)})))
        finally:
            c.close()
    top = os.path.abspath(os.sep)
    c = Client([], cwd=top)
    try:
        _init(c)
        r = c.call('lint_file', {'path': os.path.join(proj, 'a.txt')})
        R.add('no --root and the working folder is the top of the disk -> isError, no disk-wide root',
              _is_tool_error(r) and 'top of a drive' in _text(_result(r)), _short(r))
    finally:
        c.close()
    plug = os.path.join(base, 'plug')
    _write(os.path.join(plug, 'plugin.json'), '{"name": "whalory"}')
    _write(os.path.join(plug, 'notes.txt'), 'سلام.\n')
    shutil.copy(os.path.join(SKILL, 'SKILL.md'), _mk(os.path.join(plug, 'skills', 'whalory')))
    c = Client(['--skill-dir', os.path.join(plug, 'skills', 'whalory')], cwd=plug)
    try:
        _init(c)
        r = c.call('lint_file', {'path': 'notes.txt'})
        R.add('no --root and the working folder is the plugin folder -> isError that says so',
              _is_tool_error(r) and 'installed' in _text(_result(r)), _short(r))
    finally:
        c.close()
    c = Client([], cwd=proj)
    try:
        _init(c)
        r = c.call('lint_file', {'path': 'a.txt'})
        R.add('no --root: ordinary working folder is not implicitly authorized',
              _is_tool_error(r) and '--root' in _text(_result(r)), _short(r))
    finally:
        c.close()


def _mk(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def t_client_roots(R, tmp):
    """MCP roots/list: asked after notifications/initialized, refreshed on list_changed."""
    base = os.path.join(tmp, 'croots')
    ra, rb, rc = os.path.join(base, 'root a'), os.path.join(base, 'rootb'), os.path.join(base, 'cwd')
    _write(os.path.join(ra, 'a.txt'), 'سلام.\n')
    _write(os.path.join(rb, 'b.txt'), 'سلام.\n')
    _write(os.path.join(rc, 'c.txt'), 'سلام.\n')
    caps = {'roots': {'listChanged': True}}

    def ok(resp):
        return (_result(resp) or {}).get('isError') is False

    c = Client([], cwd=rc)
    try:
        _init(c, caps)
        c.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        req = c.server_request('roots/list')
        R.add('client roots: roots/list is sent after notifications/initialized',
              isinstance(req, dict) and _rid_ok(req.get('id')), _short(req))
        if not req:
            return
        c.send({'jsonrpc': '2.0', 'id': 'lf-1', 'method': 'tools/call',
                'params': {'name': 'lint_file', 'arguments': {'path': 'a.txt'}}})
        time.sleep(0.3)
        c.send({'jsonrpc': '2.0', 'id': req['id'], 'result': {'roots': [{'uri': _file_uri(ra), 'name': 'A'}]}})
        r = c.wait_for('lf-1')
        R.add('client roots: a file tool waits for the answer, then reads inside the client root', ok(r), _short(r))
        r = c.call('lint_file', {'path': 'c.txt'})
        R.add('client roots: the working folder is not used when the client has roots', _is_tool_error(r), _short(r))
        c.send({'jsonrpc': '2.0', 'method': 'notifications/roots/list_changed'})
        req = c.server_request('roots/list')
        R.add('client roots: roots/list again after notifications/roots/list_changed', req is not None, _short(req))
        if req:
            c.send({'jsonrpc': '2.0', 'id': req['id'], 'result': {'roots': [{'uri': _file_uri(rb)}]}})
            R.add('client roots: the new list replaces the old one',
                  ok(c.call('lint_file', {'path': 'b.txt'})) and _is_tool_error(c.call('lint_file', {'path': 'a.txt'})))
    finally:
        c.close()
    c = Client([], cwd=rc)
    try:
        _init(c, caps)
        c.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        req = c.server_request('roots/list')
        if req:
            c.send({'jsonrpc': '2.0', 'id': req['id'], 'error': {'code': -32601, 'message': 'Roots not supported'}})
        R.add('client roots: an error answer never authorizes the working folder',
              req is not None and _is_tool_error(c.call('lint_file', {'path': 'c.txt'})))
    finally:
        c.close()
    c = Client(['--root', ra], cwd=rc)
    try:
        _init(c, caps)
        c.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        req = c.server_request('roots/list', timeout=1.0)
        R.add('client roots: a usable --root wins; roots/list is not sent',
              req is None and ok(c.call('lint_file', {'path': 'a.txt'})), _short(req))
    finally:
        c.close()
    c = Client(['--root', '${workspaceFolder}'], cwd=rc)
    try:
        _init(c, caps)
        c.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        req = c.server_request('roots/list')
        if req:
            c.send({'jsonrpc': '2.0', 'id': req['id'], 'result': {'roots': [{'uri': _file_uri(rb)}]}})
        R.add('client roots stand in for an unexpanded --root (never the working folder)',
              req is not None and ok(c.call('lint_file', {'path': 'b.txt'}))
              and _is_tool_error(c.call('lint_file', {'path': 'c.txt'})))
    finally:
        c.close()


def _rid_ok(rid):
    return isinstance(rid, (str, int)) and not isinstance(rid, bool)


STUB_LINT = '''
import re


def detect_lang(text, **kw):
    return ('en', {})


def load_profile(path):
    return {}


def lint_text(text, lang='auto', **kw):
    if 'STUCK' in text:
        re.match(r'(a|aa)+$', 'a' * 64 + 'b')  # exponential backtracking in C: it holds the GIL
    return [{'line': 1, 'col': 1, 'rule': 'stub', 'severity': 'warning', 'message': 'stub'}], {'stub': True}, 'en'
'''


def t_time_limit(R, tmp):
    """A call stuck inside one regular expression is stopped; ping and cancel still work."""
    root = os.path.join(tmp, 'stub')
    scripts = _mk(os.path.join(root, 'scripts'))
    shutil.copy(SERVER, scripts)
    shutil.copy(os.path.join(SKILL, 'SKILL.md'), root)
    _write(os.path.join(scripts, 'lint.py'), STUB_LINT)
    server = os.path.join(scripts, 'mcp_server.py')
    c = Client(['--root', root, '--time-limit', '1.5'], server=server)
    try:
        _init(c)
        r = c.call('lint_text', {'text': 'hello'})
        R.add('time limit: lint_text runs in the worker process', ((_sc(r).get('stats') or {}).get('stub') is True),
              _short(r))
        t0 = time.time()
        c.send({'jsonrpc': '2.0', 'id': 'slow-1', 'method': 'tools/call',
                'params': {'name': 'lint_text', 'arguments': {'text': 'STUCK'}}})
        time.sleep(0.3)
        t1 = time.time()
        p = c.request('ping', rid='p-during')
        R.add('time limit: ping is answered while a tool is stuck', _result(p) == {} and time.time() - t1 < 1.0,
              '%.2f s' % (time.time() - t1))
        r = c.wait_for('slow-1', timeout=10)
        R.add('time limit: a stuck lint_text is stopped with an isError after the limit',
              _is_tool_error(r) and 'time limit' in _text(_result(r)) and time.time() - t0 < 6.0,
              '%.2f s %s' % (time.time() - t0, _short(r)))
        R.add('time limit: the next call gets a new worker', (_sc(c.call('lint_text', {'text': 'again'})).get('stats')
                                                              or {}).get('stub') is True)
        c.send({'jsonrpc': '2.0', 'id': 'slow-2', 'method': 'tools/call',
                'params': {'name': 'lint_text', 'arguments': {'text': 'STUCK'}}})
        time.sleep(0.3)
        t2 = time.time()
        c.send({'jsonrpc': '2.0', 'method': 'notifications/cancelled', 'params': {'requestId': 'slow-2'}})
        r = c.call('lint_text', {'text': 'after the cancel'})
        R.add('cancel: notifications/cancelled stops the running call at once',
              (_result(r) or {}).get('isError') is False and time.time() - t2 < 1.2, '%.2f s' % (time.time() - t2))
        R.add('cancel: the cancelled request gets no response', not any(n.get('id') == 'slow-2' for n in c.notes),
              _short(c.notes))
        n0 = len(c.raw)
        c.send({'jsonrpc': '2.0', 'id': 'o-1', 'method': 'tools/call',
                'params': {'name': 'lint_text', 'arguments': {'text': 'order'}}})
        c.send({'jsonrpc': '2.0', 'id': 'o-2', 'method': 'resources/templates/list'})
        c.wait_for('o-2')
        ids = [json.loads(x.decode('utf-8')).get('id') for x in c.raw[n0:]]
        R.add('responses other than ping keep the request order', ids[:2] == ['o-1', 'o-2'], _short(ids))
    finally:
        code, dt = c.close()
    R.add('time limit: EOF still exits 0 and stops the worker', code == 0 and dt < 3.0, 'code %s %.2f s' % (code, dt))
    c = Client(['--root', root, '--time-limit', '0'], server=server)
    try:
        _init(c)
        r = c.call('lint_text', {'text': 'hello'})
        R.add('--time-limit 0 runs the tools in the server process', (_sc(r).get('stats') or {}).get('stub') is True,
              _short(r))
    finally:
        c.close()


def t_pathological(R, tmp, names):
    """The real linters on inputs that used to hold the server for minutes: each call now ends
    (with a result or a time-limit error) within the limit, and ping is answered meanwhile."""
    proj = _mk(os.path.join(tmp, 'patho'))
    _write(os.path.join(proj, 'blob.txt'), 'a-' * 100000)
    limit = 2.0
    c = Client(['--root', proj, '--time-limit', str(limit)])
    try:
        _init(c)
        calls = [('lint_text', {'text': '{' * 100000}), ('lint_file', {'path': 'blob.txt'})]
        if 'compare_texts' in names:
            calls.append(('compare_texts', {'before': 'a' * 100000, 'after': '1' * 100000}))
        for n, (tool, args) in enumerate(calls):
            rid = 'patho-%d' % n
            t0 = time.time()
            c.send({'jsonrpc': '2.0', 'id': rid, 'method': 'tools/call', 'params': {'name': tool, 'arguments': args}})
            time.sleep(0.2)
            t1 = time.time()
            p = c.request('ping', rid='patho-ping-%d' % n)
            pong = time.time() - t1
            r = c.wait_for(rid, timeout=limit + 10)
            dt = time.time() - t0
            res = _result(r) or {}
            ended = isinstance(res, dict) and (res.get('isError') is False or 'time limit' in _text(res))
            R.add('%s on a 100,000-character pathological input ends within the time limit; ping answered' % tool,
                  ended and dt < limit + 4.0 and _result(p) == {} and pong < 1.0,
                  '%.2f s, ping %.2f s, %s' % (dt, pong, _short(r, 120)))
    finally:
        c.close()


def t_no_bytecode(R, tmp, names):
    """A session writes no __pycache__ into the skill (spec G.5.6): the server is run without -B."""
    root = os.path.join(tmp, 'pyc')
    scripts = _mk(os.path.join(root, 'scripts'))
    for f in os.listdir(HERE):
        if f.endswith('.py'):
            shutil.copy(os.path.join(HERE, f), scripts)
    shutil.copy(os.path.join(SKILL, 'SKILL.md'), root)
    for sub in ('profiles', os.path.join('data', 'channels')):
        if os.path.isdir(os.path.join(SKILL, sub)):
            shutil.copytree(os.path.join(SKILL, sub), os.path.join(root, sub))
    proj = _mk(os.path.join(tmp, 'pyc-proj'))
    _write(os.path.join(proj, 'a.md'), 'سلام دوستان.\n')
    c = Client(['--root', proj], server=os.path.join(scripts, 'mcp_server.py'), dash_b=False)
    try:
        _init(c)
        c.call('lint_text', {'text': 'سلام.'})
        c.call('lint_file', {'path': 'a.md'})
        c.call('profile_lookup', {'name': 'whalory'})
        for tool, args in (('ab_test_size', {'mode': 'size', 'base_rate': 0.03, 'mde': 0.2}),
                           ('detect_context', {}), ('compare_texts', {'before': 'a 1', 'after': 'a 2'})):
            if tool in names:
                c.call(tool, args)
    finally:
        c.close()
    caches = [d for d, subdirs, _ in os.walk(root) if os.path.basename(d) == '__pycache__']
    R.add('no __pycache__ written into the skill during a session', not caches, _short(caches))


def t_json_edges(R):
    """NaN and Infinity are not JSON; resources/read without a string uri is -32602."""
    c = Client([])
    try:
        _init(c)
        for lit in ('NaN', 'Infinity', '-Infinity'):
            c.send_raw(('{"jsonrpc":"2.0","id":15,"method":"ping","params":{"x":%s}}' % lit).encode('ascii'))
            m = c.recv()
            R.add('%s in a request -> -32700 without id' % lit, isinstance(m, dict) and 'id' not in m
                  and (m.get('error') or {}).get('code') == -32700, _short(m))
        for label, params in (('missing', {}), ('empty', {'uri': ''}), ('a number', {'uri': 5})):
            for modern in (False, True):
                r = c.request('resources/read', params, modern=modern)
                R.add('resources/read with the uri %s -> -32602 (%s)' % (label, 'modern' if modern else 'legacy'),
                      (_error(r) or {}).get('code') == -32602, _short(r))
    finally:
        c.close()
    code = ('import sys, time; sys.dont_write_bytecode = True; sys.path.insert(0, %r); import mcp_server as m; '
            'w = 0.0\n'
            'for s in ("a" * 200000, "a@" * 100000, "a." * 100000, "_a" * 100000, "`" * 200000):\n'
            '    t = time.time(); m.detect_lang_simple(s); w = max(w, time.time() - t)\n'
            'print("%%.3f" %% w)' % HERE)
    p = subprocess.run([sys.executable, '-B', '-c', code], capture_output=True, timeout=120)
    try:
        worst = float(p.stdout.decode('ascii').strip())
    except ValueError:
        worst = None
    R.add('the fallback language mask runs in linear time (200,000 characters < 1 s)',
          worst is not None and worst < 1.0, '%s %s' % (worst, p.stderr.decode('utf-8', 'replace')[-200:]))


# ---------------------------------------------------------------- Whalory Hub integration (Hub spec 5.11)
READ_ONLY = {'readOnlyHint': True, 'destructiveHint': False, 'idempotentHint': True, 'openWorldHint': False}
RECORDING = {'readOnlyHint': False, 'destructiveHint': False, 'idempotentHint': False, 'openWorldHint': False}
HUB_TOOLS = ('lint_text', 'lint_file', 'check_final')
HUB_ENV = ('WHALORY_HUB', 'WHALORY_HUB_UPDATES', 'WHALORY_HUB_CONTRIBUTE', 'WHALYA_HUB', 'WHALYA_HUB_CONTRIBUTE',
           'DO_NOT_TRACK', 'DISABLE_TELEMETRY', 'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC',
           'CLAUDE_PLUGIN_OPTION_HUB_CONTRIBUTE', 'WHALORY_HUB_CONTRIBUTE_REQUEST', 'WHALYA_HUB_CONTRIBUTE_REQUEST',
           'WHALORY_LICENSE_KEY', 'CLAUDE_PLUGIN_OPTION_LICENSE_KEY', 'CI', 'GITHUB_ACTIONS')
HUB_NOW = '2026-10-01T12:00:00Z'        # the clock of the TEST ONLY fixtures of tests_hub/test_client.py
HUB_FIXTURES_UNTIL = '2027-03-29'        # the fixture baseline expires then; later runs skip the live check

SHOWN_EN = 'The report was written by our team. We ship in May. Plans were made.'
FINAL_EN = 'Our team wrote the report. We ship in May. We made plans.'


class FakeHub(object):
    """hub_events for the in-process checks: records what the server hands over."""

    def __init__(self):
        self.on = False
        self.calls = []

    def enabled(self):
        return self.on

    def record_lint(self, source, lang, fg, result, words):
        self.calls.append(('record_lint', source, lang, fg, result, words))

    def remember(self, text, lang='auto'):
        self.calls.append(('remember', text, lang))

    def check_final_outcome(self, final, lang='auto', fmt=None, playbook=None, revisions=None, profile=None):
        self.calls.append(('check_final_outcome', final, lang, fmt, playbook, revisions, profile))
        return {'recorded': True, 'reason': None}


def _server_module():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import importlib
    return importlib.import_module('mcp_server')


def _lines(buf):
    out = []
    for ln in buf.getvalue().splitlines():
        try:
            out.append(json.loads(ln.decode('ascii')))
        except ValueError:
            pass
    return out


def t_check_final(R):
    """check_final is listed, read-only while statistics are off, and returns lint_text's findings."""
    c = Client([])
    try:
        r = c.request('initialize', {'protocolVersion': LEGACY[0], 'capabilities': {}})
        caps = (_result(r) or {}).get('capabilities') or {}
        R.add('initialize: tools.listChanged is declared', (caps.get('tools') or {}).get('listChanged') is True,
              _short(caps))
        c.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        tools = (_result(c.request('tools/list')) or {}).get('tools') or []
        t = dict((x['name'], x) for x in tools).get('check_final')
        R.add('tools/list: check_final after lint_file', t is not None
              and [x['name'] for x in tools].index('check_final') == 2, _short([x['name'] for x in tools]))
        if t is None:
            return
        props = (t.get('inputSchema') or {}).get('properties') or {}
        R.add('check_final: inputs text, language, format, playbook, revisions (0 to 20)',
              t['inputSchema'].get('required') == ['text']
              and {'text', 'language', 'format', 'playbook', 'revisions'} <= set(props)
              and props['revisions'].get('minimum') == 0 and props['revisions'].get('maximum') == 20, _short(props))
        d = t.get('description') or ''
        R.add('check_final: description says when to call it and that no text is recorded',
              'once when the user approves final copy' in d and 'never text' in d and 'Iran' in d, d[:200])
        R.add('check_final: read-only while statistics are off', t.get('annotations') == READ_ONLY,
              _short(t.get('annotations')))
        text = 'Certainly! Here is a vibrant caption that will delve into our story.' if has_english_linter() \
            else 'سلام — دوستان!!'
        a = _result(c.call('lint_text', {'text': text})) or {}
        b = _result(c.call('check_final', {'text': text, 'playbook': 'caption', 'revisions': 1})) or {}
        sa, sb = a.get('structuredContent') or {}, b.get('structuredContent') or {}
        R.add('check_final returns the findings of lint_text', b.get('isError') is False and sb
              and sa.get('issues') == sb.get('issues') and sb.get('summary') == sa.get('summary')
              and not schema_errors(t.get('outputSchema') or {}, sb), _short(sb.get('summary')))
        r = c.call('check_final', {'text': text, 'language': 'fa' if 'Certainly' not in text else 'en',
                                   'format': 'caption', 'md': False})
        R.add('check_final with language and format', (_result(r) or {}).get('isError') is False, _short(r))
        for label, args in (('revisions 21', {'text': 'x', 'revisions': 21}),
                            ('a playbook id with spaces', {'text': 'x', 'playbook': 'Landing Page'}),
                            ('lang instead of language', {'text': 'x', 'lang': 'en'}),
                            ('no text', {})):
            R.add('check_final with %s -> isError' % label, _is_tool_error(c.call('check_final', args)))
        leaked = [ln for ln in c.raw if b'_pid' in ln or b'_level' in ln or b'"hidden"' in ln]
        R.add('no internal Hub field in any output', not leaked, _short(leaked[:1]))
        R.add('no notification while statistics stay off',
              not any(n.get('method') == 'notifications/tools/list_changed' for n in c.notes), _short(c.notes))
    finally:
        c.close()


def t_hub_switch(R):
    """In process, with a stand-in for hub_events: annotations, notifications and what is recorded."""
    import io as _io
    M = _server_module()
    buf = _io.BytesIO()
    srv = M.Server(SKILL, [], 'auto', buf, 0.0)
    fake = FakeHub()
    srv._mods['hub_events'] = fake
    srv.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                'params': {'protocolVersion': LEGACY[0], 'capabilities': {}}})
    srv.handle({'jsonrpc': '2.0', 'method': 'notifications/initialized'})

    def annotations():
        out = srv.handle({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'})
        return dict((t['name'], t['annotations']) for t in out[0]['result']['tools'])

    def call(name, args):
        out = srv.handle({'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call',
                          'params': {'name': name, 'arguments': args}})
        return out[0]['result']

    ann = annotations()
    R.add('hub off: lint_text, lint_file and check_final are read-only',
          all(ann.get(n) == READ_ONLY for n in HUB_TOOLS), _short(ann))
    call('lint_text', {'text': SHOWN_EN})
    R.add('hub off: nothing is recorded or remembered', fake.calls == [], _short(fake.calls))
    fake.on = True
    n0 = len(_lines(buf))
    res = call('lint_text', {'text': SHOWN_EN, 'format': 'landing'})
    notes = [m for m in _lines(buf)[n0:] if m.get('method') == 'notifications/tools/list_changed']
    R.add('hub on: the next call sends notifications/tools/list_changed once', len(notes) == 1
          and 'params' not in notes[0], _short(notes))
    rec = [x for x in fake.calls if x[0] == 'record_lint']
    ok = len(rec) == 1 and rec[0][1] == 'mcp' and rec[0][2] in ('en', 'fa') and rec[0][3] == 'landing' \
        and isinstance(rec[0][4], tuple) and len(rec[0][4]) == 2 and isinstance(rec[0][5], int) and rec[0][5] > 0 \
        and all(set(x) <= {'code', '_pid'} for x in rec[0][4][0] + rec[0][4][1])
    R.add('hub on: lint_text records (source, lang, format, (shown, hidden), words), ids only', ok,
          _short(rec[:1]))
    R.add('hub on: lint_text remembers the text in memory for check_final',
          ('remember', SHOWN_EN, rec[0][2] if rec else 'en') in fake.calls, _short(fake.calls))
    R.add('hub on: the output has no internal field', '_pid' not in json.dumps(res) and 'hidden' not in json.dumps(res))
    ann = annotations()
    R.add('hub on: tools/list marks the three tools as writing counts',
          all(ann.get(n) == RECORDING for n in HUB_TOOLS)
          and all(v == READ_ONLY for k, v in ann.items() if k not in HUB_TOOLS), _short(ann))
    del fake.calls[:]
    res = call('check_final', {'text': FINAL_EN, 'language': 'en', 'format': 'landing', 'playbook': 'landing',
                               'revisions': 2, 'profile': 'whalory'})
    cfo = [x for x in fake.calls if x[0] == 'check_final_outcome']
    R.add('hub on: check_final hands the outcome to hub_events with the resolved profile',
          len(cfo) == 1 and cfo[0][1:6] == (FINAL_EN, 'en', 'landing', 'landing', 2) and isinstance(cfo[0][6], dict)
          and not [x for x in fake.calls if x[0] == 'record_lint'], _short(cfo))
    R.add('hub on: check_final returns findings, nothing about the outcome',
          res.get('isError') is False and 'recorded' not in json.dumps(res), _short(res)[:200])
    fake.on = False
    n0 = len(_lines(buf))
    srv.refresh_annotations()
    notes = [m for m in _lines(buf)[n0:] if m.get('method') == 'notifications/tools/list_changed']
    R.add('hub off again: one more list_changed, and read-only annotations',
          len(notes) == 1 and all(v == READ_ONLY for v in annotations().values()), _short(notes))
    # modern clients hear of it only on a listen stream that asked for toolsListChanged
    srv2 = M.Server(SKILL, [], 'auto', _io.BytesIO(), 0.0)
    fake2 = FakeHub()
    srv2._mods['hub_events'] = fake2
    meta = {PV: MODERN, CAPS: {}}
    ack = srv2.handle({'jsonrpc': '2.0', 'id': 'L1', 'method': 'subscriptions/listen',
                       'params': {'_meta': meta, 'notifications': {'toolsListChanged': True}}})
    ack2 = srv2.handle({'jsonrpc': '2.0', 'id': 'L2', 'method': 'subscriptions/listen',
                        'params': {'_meta': meta, 'notifications': {'resourcesListChanged': True}}})
    R.add('modern listen: toolsListChanged is acknowledged; other types are left out',
          ack[0]['params']['notifications'] == {'toolsListChanged': True}
          and ack2[0]['params']['notifications'] == {}, _short([ack, ack2]))
    fake2.on = True
    n0 = len(_lines(srv2.out))
    srv2.refresh_annotations()
    notes = [m for m in _lines(srv2.out)[n0:] if m.get('method') == 'notifications/tools/list_changed']
    R.add('modern listen: list_changed carries the subscription id of the stream that asked',
          len(notes) == 1 and notes[0]['params']['_meta'].get(SUBID) == 'L1', _short(notes))


def _hub_world(tmp):
    """(test_client module, world, home) with packets on in a fresh TEST ONLY Hub folder, or a skip reason."""
    tests = os.path.join(HERE, 'tests_hub', 'test_client.py')
    if not os.path.isfile(tests) or not os.path.isfile(os.path.join(HERE, 'hub_client.py')):
        return None, 'tests_hub/test_client.py or hub_client.py is not in this copy'
    if time.strftime('%Y-%m-%d', time.gmtime()) >= HUB_FIXTURES_UNTIL:
        return None, 'the TEST ONLY fixtures of tests_hub expired on %s' % HUB_FIXTURES_UNTIL
    saved = dict((k, os.environ.get(k)) for k in HUB_ENV)
    for k in HUB_ENV:
        os.environ.pop(k, None)
    if os.path.join(HERE, 'tests_hub') not in sys.path:
        sys.path.insert(0, os.path.join(HERE, 'tests_hub'))
    import importlib
    TC = importlib.import_module('test_client')
    C, HE, HO = TC.C, TC.HE, TC.HO
    mirror = os.path.join(tmp, 'hub-mirror')
    home = tempfile.mkdtemp(prefix='whalory-mcp-hub-')
    TC.build_mirror(mirror, collection=False, lane=True, packets={'epoch': '2026-W40', 'issue': 7})
    world = TC.World(mirror)
    orig = C.consent_doc
    C.consent_doc = TC.filled_consent
    try:
        def client(*args, **kw):
            ctx = C.Ctx()
            ctx.now = TC.T(HUB_NOW)
            ctx.out = __import__('io').StringIO()
            ctx.console = kw.get('console')
            flags = ['--test', '--hub-home', home, '--mirror', world.base + 'mirror/',
                     '--collector', world.base + 'v1/', '--issuer', world.base + 'api/hub/']
            return C.main(flags + list(args), ctx), ctx.out.getvalue()
        code, out = client('sync', '--force')
        if code != 0:
            raise RuntimeError('sync: %s %s' % (code, out[-300:]))
        con = TC.FakeConsole(['y', 'CODE'])
        code, out = client('on', 'packets', console=con)
        if code != 0:
            raise RuntimeError('on packets: %s %s' % (code, (out + con.text)[-300:]))
    finally:
        C.consent_doc = orig
        HE.configure()
        HO.configure()
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return (TC, world, home, client), None


def t_hub_live(R, tmp):
    """A real server over stdio against a TEST ONLY Hub folder with weekly packets on."""
    got, why = _hub_world(tmp)
    if got is None:
        R.skip('Hub statistics on: annotations, counts and outcome', why)
        return
    TC, world, home, client = got
    env = dict((k, '') for k in ('DO_NOT_TRACK', 'DISABLE_TELEMETRY', 'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC'))
    env['WHALORY_HUB'] = '1'
    c = Client(['--test', '--hub-home', home, '--now', HUB_NOW], env=env, drop=HUB_ENV)
    try:
        r = c.request('initialize', {'protocolVersion': LEGACY[0], 'capabilities': {}})
        c.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        tools = (_result(c.request('tools/list')) or {}).get('tools') or []
        ann = dict((t['name'], t.get('annotations')) for t in tools)
        R.add('Hub on (packets): lint_text, lint_file and check_final are not read-only',
              all(ann.get(n) == RECORDING for n in HUB_TOOLS), _short(ann))
        r = c.call('lint_text', {'text': SHOWN_EN, 'format': 'landing'})
        R.add('Hub on: lint_text answers as usual', (_result(r) or {}).get('isError') is False, _short(r))
        r = c.call('check_final', {'text': FINAL_EN, 'language': 'en', 'format': 'landing',
                                   'playbook': 'landing', 'revisions': 1})
        R.add('Hub on: check_final answers with findings only', (_result(r) or {}).get('isError') is False
              and 'recorded' not in json.dumps(_result(r)), _short(r))
        events = []
        folder = os.path.join(home, 'events')
        for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            with open(os.path.join(folder, name), encoding='utf-8') as fh:
                events += [json.loads(ln) for ln in fh if ln.strip()]
        kinds = [(e.get('t'), e.get('src')) for e in events]
        R.add('Hub on: one mcp lint event and one outcome event in the Hub folder',
              ('lint', 'mcp') in kinds and ('out', None) in kinds, _short(kinds))
        raw = json.dumps(events)
        R.add('Hub on: the events hold no text of the drafts', not re.search(r'report|Plans|May|team', raw),
              _short(raw)[:200])
        leaked = [ln for ln in c.raw if b'_pid' in ln or b'_level' in ln or b'"hidden"' in ln]
        R.add('Hub on: no internal field in any output', not leaked, _short(leaked[:1]))
        code, out = client('off', 'packets')
        c.call('lint_text', {'text': 'Plain words.'})
        notes = [n for n in c.notes if n.get('method') == 'notifications/tools/list_changed']
        tools = (_result(c.request('tools/list')) or {}).get('tools') or []
        R.add('Hub off in a terminal: the next call sends list_changed and the tools are read-only again',
              code == 0 and len(notes) == 1 and all(t.get('annotations') == READ_ONLY for t in tools),
              _short(notes))
    finally:
        c.close()
        world.stop()
        TC.HE.configure()
        TC.HO.configure()
        for _ in range(20):
            shutil.rmtree(home, ignore_errors=True)
            if not os.path.exists(home):
                break
            time.sleep(0.25)


def t_cwd_contains_home(R, tmp):
    """The working-folder fallback refuses a folder that contains the home folder."""
    parent = _mk(os.path.join(tmp, 'users'))
    home = _mk(os.path.join(parent, 'someone'))
    _write(os.path.join(home, 'notes.txt'), 'private\n')
    env = {'HOME': home, 'USERPROFILE': home}
    c = Client([], env=env, cwd=parent)
    try:
        _init(c)
        r = c.call('lint_file', {'path': 'someone/notes.txt'})
        R.add('cwd that contains the home folder -> not a project folder', _is_tool_error(r)
              and 'contains the home folder' in _text(_result(r)), _short(r))
    finally:
        c.close()


def run():
    R = Results()
    if not os.path.isfile(SERVER):
        R.add('mcp_server.py present', False, 'not found')
        return R.rows
    tmp = tempfile.mkdtemp(prefix='whalory-mcp-')
    try:
        for label, fn in (('static checks', lambda: t_static(R)),):
            try:
                fn()
            except Exception as e:
                R.add('%s: did not run' % label, False, '%s: %s' % (type(e).__name__, e))
        report = None
        try:
            report = t_cli(R)
        except Exception as e:
            R.add('command line: did not run', False, '%s: %s' % (type(e).__name__, e))
        names = expected_tools()
        for label, fn in (('legacy session', lambda: t_legacy(R, tmp, report)),
                          ('modern session', lambda: t_modern(R)),
                          ('old legacy clients', lambda: t_old_legacy(R)),
                          ('roots from the environment', lambda: t_env_roots(R, tmp)),
                          ('names from before the rename', lambda: t_old_names(R, tmp)),
                          ('links out of the roots', lambda: t_confinement(R, tmp, names)),
                          ('roots fail closed', lambda: t_roots_fail_closed(R, tmp, names)),
                          ('client roots', lambda: t_client_roots(R, tmp)),
                          ('time limit and cancel', lambda: t_time_limit(R, tmp)),
                          ('pathological inputs', lambda: t_pathological(R, tmp, names)),
                          ('no bytecode', lambda: t_no_bytecode(R, tmp, names)),
                          ('JSON edge cases', lambda: t_json_edges(R)),
                          ('check_final', lambda: t_check_final(R)),
                          ('Hub switch in process', lambda: t_hub_switch(R)),
                          ('Hub statistics on', lambda: t_hub_live(R, tmp)),
                          ('working folder that contains the home folder', lambda: t_cwd_contains_home(R, tmp))):
            try:
                fn()
            except Exception as e:  # one broken group must not hide the others
                R.add('%s: did not run' % label, False, '%s: %s' % (type(e).__name__, e))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return R.rows


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    rows = run()
    failed = 0
    for name, ok, detail in rows:
        if not ok:
            failed += 1
        print('%-5s %-70s %s' % ('ok' if ok else 'FAIL', name, detail if not ok or detail.startswith('skipped') else ''))
    print('\n%s' % ('all %d MCP tests passed' % len(rows) if not failed else '%d of %d MCP tests failed' % (failed, len(rows))))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
