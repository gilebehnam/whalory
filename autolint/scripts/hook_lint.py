#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hook_lint: Whalory's opt-in autolint hook.

The host runs this script after a tool writes or edits a file. It reads one hook
event as JSON on stdin. When the tool wrote a copy file or a locale file, the
script lints that file with Whalory's dispatcher, ``lint.lint_path``, with
``lang='auto'`` and ``profile='auto'``. When the result has errors, it prints one
JSON object that hands a short summary back to the model.

It never blocks. The exit code is always 0, stdout is empty or one JSON object,
and the linter gets about 8 seconds. The linter runs in a child process (this
same file with ``--child``, started with ``sys.executable`` and no shell), so the
time limit holds even inside a long regular expression, which a thread cannot
interrupt: when the time is up, the hook stops the child and reports only the
files it finished.

Output by event name:

    PostToolUse (Claude Code, Codex, VS Code with Claude-format hooks)
        {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "..."}}
    postToolUse (Cursor)
        {"additional_context": "..."}
    AfterTool (Gemini CLI)
        {"hookSpecificOutput": {"hookEventName": "AfterTool", "additionalContext": "..."}}

Other event names are ignored. A payload without an event name is treated as
PostToolUse.

Environment:

    WHALORY_AUTOLINT=0        do nothing (off, false and no work too)
    WHALORY_AUTOLINT=strict   report warnings as well as errors
    WHALORY_SCRIPTS_DIR       folder that holds lint.py, when it is not next to this file

The deprecated WHALYA_AUTOLINT and WHALYA_SCRIPTS_DIR are read when the WHALORY_* one is empty.

The script filters by itself, because some hosts ignore matchers: it skips
read-only tools, MCP tools, paths under node_modules, .git, dist, build or
vendor, files over 1 MB, unsupported extensions, and .json or .xml files that
do not look like locale files.

Python 3.8 or newer, standard library only. No network and no file writes: not
even Python bytecode caches next to lint.py (the child runs with -B).
"""
from __future__ import print_function

import sys

sys.dont_write_bytecode = True  # before lint.py is imported: no __pycache__ in the plugin folder

import contextlib  # noqa: E402
import importlib.util  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import threading  # noqa: E402

VERSION = '3.0.0'

MAX_BYTES = 1024 * 1024
TIMEOUT = 8.0
SUMMARY_MAX = 4000
LINE_MAX = 300
TOP_ISSUES = 15
MAX_FILES = 5

EXTS = ('.md', '.mdx', '.txt', '.html', '.htm', '.po', '.pot', '.arb', '.xliff', '.xlf',
        '.strings', '.xml', '.csv', '.tsv', '.json')
LOCALE_ONLY_EXTS = ('.json', '.xml')
SKIP_DIRS = ('node_modules', '.git', 'dist', 'build', 'vendor')
POST_EVENTS = ('PostToolUse', 'postToolUse', 'AfterTool')

LOCALE_DIR_RX = re.compile(
    r'(^|/)(locales|i18n|lang|messages|translations)(/|$)|(^|/)res/values[^/]*(/|$)', re.I)
LOCALE_NAME_RX = re.compile(r'^(fa|en)([-_][a-z0-9]+)*$|[._-](fa|en)([-_][a-z]{2,4})?$', re.I)
WRITE_TOOL_RX = re.compile(r'write|edit|replace|create|patch|insert|save', re.I)
MCP_TOOL_RX = re.compile(r'^(mcp_|mcp:)', re.I)
PATCH_FILE_RX = re.compile(r'^\*\*\* (?:Add File|Update File|Move to): (.+?)\s*$', re.M)
OFF_VALUES = ('0', 'off', 'false', 'no')

_TIMED_OUT = object()


# ---------------------------------------------------------------- input

def _read_stdin():
    data = sys.stdin.buffer.read() if hasattr(sys.stdin, 'buffer') else sys.stdin.read()
    if isinstance(data, bytes):
        data = data.decode('utf-8', 'replace')
    return data


def _parse(text):
    if not text:
        return None
    text = text.lstrip('﻿').strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
    except ValueError:
        return None
    return payload if isinstance(payload, dict) else None


def _tool_name(payload):
    name = payload.get('tool_name', payload.get('toolName'))
    return name if isinstance(name, str) else None


def _is_write_tool(name):
    """True for tools that write files. A missing name counts as a write."""
    if name is None:
        return True
    if MCP_TOOL_RX.match(name):
        return False
    return bool(WRITE_TOOL_RX.search(name))


def _candidate_paths(payload, tool):
    """Paths the tool wrote, in order, without duplicates."""
    found = []
    ti = payload.get('tool_input', payload.get('toolInput'))
    if isinstance(ti, dict):
        for key in ('file_path', 'path', 'filePath', 'target_file'):
            value = ti.get(key)
            if isinstance(value, str) and value.strip():
                found.append(value.strip())
                break
        if not found:
            cmd = ti.get('command')
            if isinstance(cmd, str) and ('*** Begin Patch' in cmd or (tool or '') == 'apply_patch'):
                found.extend(m.group(1) for m in PATCH_FILE_RX.finditer(cmd))
    if not found:
        value = payload.get('file_path')
        if isinstance(value, str) and value.strip():
            found.append(value.strip())
    out = []
    for p in found:
        if p not in out:
            out.append(p)
    return out[:MAX_FILES]


def _base_dir(payload, env):
    roots = payload.get('workspace_roots')  # Cursor sends the workspace folders as a list
    first_root = roots[0] if isinstance(roots, list) and roots else None
    for value in (payload.get('cwd'), first_root, env.get('CLAUDE_PROJECT_DIR'),
                  env.get('CURSOR_PROJECT_DIR'), env.get('GEMINI_PROJECT_DIR')):
        if isinstance(value, str) and value and os.path.isdir(value):
            return os.path.abspath(value)
    return os.getcwd()


def _resolve(path, base):
    if '\x00' in path:
        return None
    if not os.path.isabs(path):
        path = os.path.join(base, path)
    return os.path.normpath(path)


# ---------------------------------------------------------------- filters

def _relative_parts(path, base):
    """Path segments below the project folder (all segments when outside it)."""
    try:
        rel = os.path.relpath(path, base)
    except ValueError:
        rel = path
    if rel.startswith('..'):
        rel = path
    rel = rel.replace('\\', '/')
    return [s for s in rel.split('/') if s and s != '.'], rel


def _locale_like(rel, name):
    if LOCALE_DIR_RX.search(rel):
        return True
    stem = os.path.splitext(name)[0]
    return bool(LOCALE_NAME_RX.search(stem))


def eligible(path, base):
    """True when the hook should lint this file."""
    if not path:
        return False
    parts, rel = _relative_parts(path, base)
    if any(p.lower() in SKIP_DIRS for p in parts[:-1]):
        return False
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()
    if ext not in EXTS:
        return False
    if ext in LOCALE_ONLY_EXTS and not _locale_like(rel, name):
        return False
    try:
        if not os.path.isfile(path):
            return False
        if os.path.getsize(path) > MAX_BYTES:
            return False
    except OSError:
        return False
    return True


# ---------------------------------------------------------------- linter

def _script_dirs(env):
    here = os.path.dirname(os.path.abspath(__file__))
    dirs = []
    scripts_dir = env.get('WHALORY_SCRIPTS_DIR') or env.get('WHALYA_SCRIPTS_DIR')  # WHALYA_*: deprecated
    if scripts_dir:
        dirs.append(scripts_dir)
    dirs.append(here)
    root = env.get('CLAUDE_PLUGIN_ROOT')
    if root:
        dirs.append(os.path.join(root, 'scripts'))
        dirs.append(os.path.join(root, 'skills', 'whalory', 'scripts'))
    dirs.append(os.path.normpath(os.path.join(here, '..', '..', 'scripts')))
    return dirs


def load_linter(env, dirs=None):
    """Import lint.py from the first folder that has it; None when there is none."""
    for d in (dirs if dirs is not None else _script_dirs(env)):
        target = os.path.join(d, 'lint.py')
        if not os.path.isfile(target):
            continue
        d = os.path.abspath(d)
        if d not in sys.path:
            sys.path.insert(0, d)
        spec = importlib.util.spec_from_file_location('lint', target)
        module = importlib.util.module_from_spec(spec)
        sys.modules['lint'] = module
        spec.loader.exec_module(module)
        if hasattr(module, 'lint_path'):
            return module
        return None
    return None


def _lint_one(linter, path):
    """One files[] entry. profile='auto' first, then no profile when that fails."""
    folder = os.path.dirname(path)
    old = os.getcwd()
    try:
        if os.path.isdir(folder):
            os.chdir(folder)
        try:
            return linter.lint_path(path, lang='auto', profile='auto')
        except Exception:
            return linter.lint_path(path, lang='auto', profile=None)
    finally:
        try:
            os.chdir(old)
        except OSError:
            pass


def _run_with_timeout(func, timeout):
    box = {}

    def work():
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                box['value'] = func()
        except BaseException as exc:  # the hook must never fail
            box['error'] = exc

    worker = threading.Thread(target=work)
    worker.daemon = True
    worker.start()
    worker.join(timeout)
    if worker.is_alive():
        return _TIMED_OUT
    return box.get('value')


def _slim(entry):
    """The parts of a lint_path entry that the summary uses, as plain JSON."""
    if not isinstance(entry, dict):
        return {}
    return {'lang': entry.get('lang'), 'issues': [i for i in entry.get('issues') or [] if isinstance(i, dict)]}


def _run_child(paths, base, env, timeout):
    """Lint the files in a child process and stop it at the time limit.

    A thread cannot stop a linter that is stuck inside one regular expression (it holds the
    GIL), but a process can be killed. The child is this same file run with sys.executable, -B
    and --child; it prints one JSON line per file it finishes. Returns [(display, entry)] for the
    finished files, or [] when the child cannot start."""
    exe = sys.executable
    if not exe:
        return []
    import subprocess
    job = {'files': [[_display(p, base), p] for p in paths], 'dirs': _script_dirs(env), 'timeout': timeout}
    kw = {'stdin': subprocess.PIPE, 'stdout': subprocess.PIPE, 'stderr': subprocess.DEVNULL, 'close_fds': True}
    if os.name == 'nt':  # no console window when the host is a desktop app
        kw['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
    try:
        proc = subprocess.Popen([exe, '-B', os.path.abspath(__file__), '--child'], **kw)
    except (OSError, ValueError):
        return []
    try:
        out, _ = proc.communicate(json.dumps(job).encode('utf-8'), timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            out, _ = proc.communicate(timeout=5)  # what the child printed before it was stopped
        except Exception:
            out = b''
    except (OSError, ValueError):
        proc.kill()
        out = b''
    results = []
    for line in (out or b'').splitlines():
        try:
            item = json.loads(line.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(item, list) and len(item) == 2 and isinstance(item[0], str) and isinstance(item[1], dict):
            results.append((item[0], item[1]))
    return results


def child_main():
    """--child: read one job from stdin, lint each file, print one JSON line per finished file."""
    out = sys.stdout
    sys.stdout = sys.stderr  # anything the linter prints is dropped (the parent discards stderr)
    try:
        job = json.loads(_read_stdin() or '{}')
    except ValueError:
        return 0
    if not isinstance(job, dict):
        return 0
    limit = job.get('timeout')
    if isinstance(limit, (int, float)) and limit > 0:
        try:  # backstop if the parent is gone: a C watchdog ends this process without the GIL
            import faulthandler
            faulthandler.dump_traceback_later(float(limit) + 2.0, exit=True, file=sys.__stderr__)
        except Exception:
            pass
    dirs = [d for d in job.get('dirs') or [] if isinstance(d, str)]
    linter = load_linter({}, dirs)
    if linter is None:
        return 0
    for item in job.get('files') or []:
        try:
            shown, path = item
            entry = _lint_one(linter, path)
        except Exception:
            continue
        out.write(json.dumps([shown, _slim(entry)], ensure_ascii=True, default=str) + '\n')
        out.flush()
    return 0


# ---------------------------------------------------------------- summary

def _field(issue, *names):
    for n in names:
        value = issue.get(n)
        if value not in (None, ''):
            return value
    return None


def _norm_issues(entry):
    issues = entry.get('issues') if isinstance(entry, dict) else None
    out = []
    for it in issues or []:
        if not isinstance(it, dict):
            continue
        sev = _field(it, 'severity', 'level') or 'warning'
        out.append({'rule': str(_field(it, 'rule', 'code') or 'lint'),
                    'severity': 'error' if sev == 'error' else 'warning',
                    'line': _field(it, 'line'),
                    'key': _field(it, 'key'),
                    'message': ' '.join(str(_field(it, 'message') or '').split()),
                    'excerpt': ' '.join(str(_field(it, 'excerpt', 'text') or '').split())})
    return out


def _sort_key(issue):
    line = issue['line'] if isinstance(issue['line'], int) else 10 ** 9
    return (0 if issue['severity'] == 'error' else 1, line)


def _issue_line(issue):
    where = issue['line'] if issue['line'] is not None else issue['key']
    head = issue['rule'] if where is None else '%s:%s' % (issue['rule'], where)
    text = '- %s %s' % (head, issue['message'])
    if issue['excerpt']:
        text += ' "%s"' % issue['excerpt'][:60]
    return text[:LINE_MAX]


def build_summary(results, strict=False):
    """results: [(display_path, entry)]. None when there is nothing to report."""
    blocks = []
    for shown, entry in results:
        issues = sorted(_norm_issues(entry), key=_sort_key)
        errors = sum(1 for i in issues if i['severity'] == 'error')
        warnings = len(issues) - errors
        if errors == 0 and not (strict and warnings):
            continue
        if not strict:
            issues = [i for i in issues if i['severity'] == 'error']
        lang = entry.get('lang') if isinstance(entry, dict) else None
        blocks.append((shown, lang, errors, warnings, issues))
    if not blocks:
        return None
    footer = ('Fix the errors before you finish; warnings are advice. Turn this hook off with '
              'WHALORY_AUTOLINT=0.')
    lines = []
    budget = TOP_ISSUES
    for shown, lang, errors, warnings, issues in blocks:
        lines.append('Whalory lint: %s%s has %d error%s and %d warning%s.' % (
            shown, ' (%s)' % lang if lang else '', errors, '' if errors == 1 else 's',
            warnings, '' if warnings == 1 else 's'))
        take = issues[:budget]
        lines.extend(_issue_line(i) for i in take)
        budget -= len(take)
        if len(issues) > len(take):
            lines.append('- ... %d more not shown' % (len(issues) - len(take)))
    text = ''
    limit = SUMMARY_MAX - len(footer) - 1
    for ln in lines:
        if len(text) + len(ln) + 1 > limit:
            break
        text += ln + '\n'
    return text + footer


def render(event, text):
    if event == 'postToolUse':
        return {'additional_context': text}
    name = 'AfterTool' if event == 'AfterTool' else 'PostToolUse'
    return {'hookSpecificOutput': {'hookEventName': name, 'additionalContext': text}}


# ---------------------------------------------------------------- main

def _display(path, base):
    try:
        rel = os.path.relpath(path, base)
    except ValueError:
        return path.replace('\\', '/')
    return (path if rel.startswith('..') else rel).replace('\\', '/')


def main(stdin_text=None, env=None, linter=None, timeout=TIMEOUT, out=None):
    """Run the hook once. Always returns 0. The linter runs in a child process; a linter object
    passed in (tests) runs on a thread in this process instead."""
    env = os.environ if env is None else env
    out = sys.stdout if out is None else out
    mode = (env.get('WHALORY_AUTOLINT') or env.get('WHALYA_AUTOLINT') or '').strip().lower()  # WHALYA_*: deprecated
    if mode in OFF_VALUES:
        return 0
    try:
        payload = _parse(_read_stdin() if stdin_text is None else stdin_text)
        if payload is None:
            return 0
        event = payload.get('hook_event_name', payload.get('hookEventName')) or 'PostToolUse'
        if event not in POST_EVENTS:
            return 0
        tool = _tool_name(payload)
        if not _is_write_tool(tool):
            return 0
        base = _base_dir(payload, env)
        paths = []
        for p in _candidate_paths(payload, tool):
            full = _resolve(p, base)
            if full and eligible(full, base):
                paths.append(full)
        if not paths:
            return 0

        def job():
            done = []
            for p in paths:
                try:
                    done.append((_display(p, base), _lint_one(linter, p)))
                except Exception:
                    continue
            return done

        if linter is not None:
            results = _run_with_timeout(job, timeout)
        else:
            results = _run_child(paths, base, env, timeout)
        if results is _TIMED_OUT or not results:
            return 0
        text = build_summary(results, strict=(mode == 'strict'))
        if not text:
            return 0
        out.write(json.dumps(render(event, text), ensure_ascii=True) + '\n')
        out.flush()
    except BaseException:  # never block the host
        return 0
    return 0


if __name__ == '__main__':
    if '--version' in sys.argv[1:]:
        sys.stdout.write('hook_lint %s\n' % VERSION)
        sys.stdout.flush()
        os._exit(0)
    try:
        if sys.argv[1:2] == ['--child']:
            child_main()
        else:
            main()
    except BaseException:
        pass
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)
