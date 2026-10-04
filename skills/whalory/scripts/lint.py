#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint: Whalory's checker for Persian and English copy (Whalory 3.1.0).

The dispatcher. It decides the language of each file, locale value, CSV cell or line and
sends it to lint_fa (Persian) or lint_en (English). A file that is mostly one language goes
to that linter whole; a mixed file is split by line (and by cell in Markdown tables), and
the two results are merged with exact line and column numbers.

It takes every lint_fa flag, the lint_en flags (--variant, --house-style, --facts) and
--lang auto|fa|en (--fa-only, --en-only). The JSON output is lint_fa's v2 shape with a
"lang" key per file. The Python API is frozen for 3.0 (migration/v3/lint-api.md):

    lint.detect_lang(text, kind='text', profile=None) -> (lang, fa_ratio)
    lint.lint_text(text, lang='auto', profile=None, fmt=None, channel=None, md=False,
                   max_words=None, facts=None, kind=None) -> (issues, stats, lang)
    lint.lint_path(path, lang='auto', profile=None, fmt=None, channel=None, md=None,
                   csv_columns=None, csv_key=None, facts=None) -> dict
    lint.load_profile(spec) -> dict
    lint.run(argv=None) -> exit code

Usage:
    python lint.py draft.txt
    python lint.py references SKILL.md "GUIDE*.md" --md --json
    python lint.py src/locales/ --format ui --profile auto
    python lint.py --text "Short copy" --lang en --format ui
    python lint.py draft.md --md --fix --write
    python lint.py --rules --json
    python lint.py draft.txt --no-overlay       (built-in rules only; WHALORY_HUB_OVERLAY=0 does the same)

Exit codes: 0 no errors; 1 at least one error (or a warning with --strict);
2 input, profile or flag error; 130 interrupted.

Whalory Hub (Hub spec 4.3, 5.2): only while the person turned on weekly statistics or
weekly packets in their own terminal, and neither CI nor GITHUB_ACTIONS is set, each
checked file or text adds one line of counts (rule ids, never text) to the Hub folder.
At the end of a run in a terminal (not --json), hub_client.terminal_notices() may print
the Hub's one-time notices on stderr.
"""
from __future__ import print_function

import sys

if sys.version_info < (3, 8):  # before anything else, so the message is readable
    sys.stderr.write('lint needs Python 3.8 or newer (found %s). '
                     'Install a newer Python and run it again.\n' % sys.version.split()[0])
    sys.exit(2)

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts: a skill or plugin folder may be read-only

import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import lint_fa as LF  # noqa: E402
import lint_en as LE  # noqa: E402
import textcount  # noqa: E402,F401  (part of the public toolset; imported for callers)

__version__ = '3.2.0'

UserError = LF.UserError
SKILL_ROOT = LF.SKILL_ROOT
_FA_LET = re.compile('[%s]' % LF.FA_LETTERS)
_EN_LET = re.compile('[A-Za-z]')
_LOCALE_PH = re.compile(r'%(?:\d+\$)?[-+#0]*(?:[1-9]\d*)?(?:\.\d+)?[sdifuxXoeEgGcpaA@]')
_PO_HEAD = re.compile(r'^[ \t]*msgid[ \t]+"', re.M)
_STRINGS_HEAD = re.compile(r'^[ \t]*"(?:[^"\\\n]|\\.)*"[ \t]*=[ \t]*"', re.M)


# ---------------------------------------------------------------- profile
def load_profile(spec):
    """Raw profile dict (+ '_path'); {} for no profile or 'auto' without voice.json.
    Accepts a dict, a path, a bare name, 'auto', 'en/<slug>', 'starter-en-<slug>',
    'starter-<slug>' and '<name>.en'. Raises UserError when a named profile is missing."""
    if not spec:
        return {}
    if isinstance(spec, dict):
        _validate_contract(spec)
        return dict(spec)
    spec = str(spec)
    if spec == 'auto':
        found = LF._find_auto()
        return _read_raw(found) if found else {}
    path = os.path.expanduser(spec)
    if os.path.exists(path) or path.lower().endswith(('.json', '.md')) or os.sep in path \
            or ('/' in path and not re.match(r'^en/[a-z0-9-]+$', path)):
        p = LF.load_profile(path)          # path rules of lint_fa (a .md uses the .json beside it)
        return _read_raw(p['_path'])
    spec = LF.LEGACY_PROFILE_IDS.get(spec, spec)   # the old house-voice id whalya
    cands = []
    m = re.match(r'^(?:en/|starter-en-)([a-z0-9-]+)$', spec)
    if m:
        cands.append(os.path.join(SKILL_ROOT, 'profiles', 'starters', 'en', m.group(1) + '.json'))
    m = re.match(r'^starter-([a-z0-9-]+)$', spec)
    if m and not spec.startswith('starter-en-'):
        cands.append(os.path.join(SKILL_ROOT, 'profiles', 'starters', m.group(1) + '.json'))
    if spec.endswith('.en'):
        cands.append(os.path.join(SKILL_ROOT, 'profiles', spec + '.json'))
        cands.extend(os.path.join(d, spec + '.json') for d in LF.user_profile_dirs())
    found = LF.find_profile(spec) if not os.path.splitext(spec)[1] else None
    for c in ([found] if found else []) + cands:
        if c and os.path.isfile(c):
            return _read_raw(c)
    raise UserError('profile "%s" not found (searched ~/.whalory/profiles, profiles/, profiles/starters/, '
                    'profiles/starters/en/ and examples/).' % spec)


def _read_raw(path):
    data = LF._read_json(path, 'profile')
    if not isinstance(data, dict):
        raise UserError('a profile must be a JSON object: %s' % path)
    if any(k in data for k in ('_path', '_normalized', '_en_normalized', '_warnings')):
        raise UserError('profile files cannot contain reserved runtime keys')
    _validate_contract(data)
    data = dict(data)
    data['_path'] = path
    return data


def resolve_profile(profile=None, lang='fa', fmt=None, preset=None, industry=None,
                    request=None, host_limits=None, industry_selected=False):
    if isinstance(profile, str):
        profile = load_profile(profile)
    if isinstance(profile, dict):
        profile = {k: v for k, v in profile.items()
                   if k not in ('_path', '_normalized', '_en_normalized', '_warnings')}
    return LF.VP.resolve_profile(profile, lang=lang, fmt=fmt, preset=preset, industry=industry,
                                 request=request, host_limits=host_limits,
                                 industry_selected=industry_selected)


def _validate_contract(profile):
    raw = {k: v for k, v in profile.items() if k not in ('_path', '_normalized', '_en_normalized', '_warnings')}
    sv = raw.get('schema_version', 1)
    errors = LF.VP.validate_profile(raw)
    if type(sv) is not int or sv not in (1, 2, 3) or (sv == 3 and errors):
        raise UserError(str(LF.VP.ProfileError(errors)))


def _as_profile(profile):
    if isinstance(profile, str):
        return load_profile(profile)
    return profile or {}


# ---------------------------------------------------------------- language
def _profile_masks(profile):
    words = []
    p = profile or {}
    brand = p.get('brand') if isinstance(p.get('brand'), dict) else {}
    if isinstance(brand.get('latin'), str) and brand['latin'].strip():
        words.append(brand['latin'].strip())
    rom = p.get('romanization') if isinstance(p.get('romanization'), dict) else {}
    words += [v.strip() for v in rom.values() if isinstance(v, str) and v.strip()]
    if not words:
        return None
    return re.compile(r'(?<![A-Za-z])(?:%s)(?![A-Za-z])' % '|'.join(re.escape(w) for w in
                                                                    sorted(set(words), key=len, reverse=True)), re.I)


def _mask_letters(s, rx):
    if rx is None:
        return s
    return rx.sub(lambda m: ' ' * len(m.group(0)), s)


def _count(s):
    return len(_FA_LET.findall(s)), len(_EN_LET.findall(s))


def _decide(fa, en):
    total = fa + en
    if total >= 20:
        r = fa / float(total)
        if r >= 0.80:
            return 'fa'
        if r <= 0.20:
            return 'en'
        return 'mixed'
    return 'fa' if fa >= en else 'en'


def _guess_locale_path(text):
    head = text.lstrip()[:400]
    if head.startswith('<'):
        return 'x.xml'
    if _PO_HEAD.search(text):
        return 'x.po'
    if _STRINGS_HEAD.search(text):
        return 'x.strings'
    return 'x.json'


def _value_masked(v):
    return _LOCALE_PH.sub(lambda m: ' ' * len(m.group(0)), LF.mask_value(v))


def letter_counts(text, kind='text', profile=None, path=None):
    """(Persian letters, Latin letters) after masking code, URLs, placeholders, tags and the
    profile's brand.latin and romanization values."""
    rx = _profile_masks(_as_profile(profile))
    text = LF.clean_text(text or '')
    if kind == 'locale':
        fa = en = 0
        for _k, v, _l in LF.extract_locale(text, path or _guess_locale_path(text)):
            if isinstance(v, str):
                a, b = _count(_mask_letters(_value_masked(v), rx))
                fa, en = fa + a, en + b
        return fa, en
    if kind == 'csv':
        fa = en = 0
        try:
            cells = LF.csv_cells(text, path or '')['cells']
        except UserError:
            cells = []
        for c in cells:
            a, b = _count(_mask_letters(LF.mask_prose(c[3], 'text'), rx))
            fa, en = fa + a, en + b
        return fa, en
    return _count(_mask_letters(LF.mask_prose(text, kind), rx))


def detect_lang(text, kind='text', profile=None):
    """('fa' | 'en' | 'mixed', Persian share of letters). No letters → ('fa', 0.5)."""
    fa, en = letter_counts(text, kind, profile)
    ratio = round(fa / float(fa + en), 3) if fa + en else 0.5
    return _decide(fa, en), ratio


def _block_line_set(text, kind):
    """Line numbers (0-based) fully inside code fences, lint-ignore blocks, HTML comments, raw HTML
    or front matter: neutral in mixed mode."""
    spans = []
    if kind == 'md':
        m = LF._FRONT.match(text)
        if m:
            spans.append((0, m.end()))
    fences = LF._fence_spans(text)
    spans += fences + LF.ignore_spans(text, fences)
    spans += [(m.start(), m.end()) for m in LF._HTML_RAW.finditer(text)]
    spans += [(m.start(), m.end()) for m in LF._HTML_COMMENT.finditer(text)]
    out, pos = set(), 0
    for i, ln in enumerate(text.split('\n')):
        end = pos + len(ln)
        if any(a <= pos and end <= b for a, b in spans):
            out.add(i)
        pos = end + 1
    return out


def segments(text, kind='text', profile=None):
    """Mixed-mode segments of a cleaned text: [(line index, start, end, lang)], line-relative spans.
    Neutral lines (blank, code, ignored) are left out. Also returns the file majority."""
    rx = _profile_masks(_as_profile(profile))
    masked = _mask_letters(LF.mask_prose(text, kind), rx)
    lines, mlines = text.split('\n'), masked.split('\n')
    neutral = _block_line_set(text, kind)
    rows, seps = LF._table_lines(lines, kind == 'md')
    fa_all, en_all = _count(masked)
    major = 'fa' if fa_all >= en_all else 'en'
    out = []
    for i, ln in enumerate(lines):
        if i in neutral or i in seps or not ln.strip():
            continue
        pieces = LF._table_cells(ln) if (kind == 'md' and i in rows) else [(0, len(ln))]
        for a, b in pieces:
            fa, en = _count(mlines[i][a:b])
            if fa == en:
                lang = major
            else:
                lang = 'fa' if fa > en else 'en'
            out.append((i, a, b, lang))
    return out, major


def _copies(text, segs):
    """(fa copy, en copy): the other language's segments replaced by spaces; lengths kept."""
    lines = text.split('\n')
    fa_l, en_l = [list(x) for x in lines], [list(x) for x in lines]
    for i, a, b, lang in segs:
        tgt = en_l if lang == 'fa' else fa_l
        for k in range(a, b):
            if tgt[i][k] not in '\r\n':
                tgt[i][k] = ' '
    return '\n'.join(''.join(x) for x in fa_l), '\n'.join(''.join(x) for x in en_l)


# ---------------------------------------------------------------- stats
def _merge_stats(fa_st, en_st, split):
    st = dict(fa_st)
    n_fa, n_en = fa_st.get('sentences', 0), en_st.get('sentences', 0)
    st['errors'] = fa_st.get('errors', 0) + en_st.get('errors', 0)
    st['warnings'] = fa_st.get('warnings', 0) + en_st.get('warnings', 0)
    st['sentences'] = n_fa + n_en
    st['placeholders'] = fa_st.get('placeholders', 0) + en_st.get('placeholders', 0)
    if n_fa + n_en:
        st['avg_words'] = round((fa_st.get('avg_words', 0) * n_fa + en_st.get('avg_words', 0) * n_en)
                                / float(n_fa + n_en), 1)
    st['max_words'] = fa_st.get('max_words')
    st['fa'] = fa_st
    st['en'] = en_st
    st['lang_split'] = split
    return st


def _recount(issues, stats):
    stats = dict(stats)
    stats['errors'] = sum(1 for x in issues if x['level'] == LF.ERROR)
    stats['warnings'] = sum(1 for x in issues if x['level'] == LF.WARN)
    return stats


def _by_pos(issues):
    return sorted(issues, key=lambda x: (x['line'] or 0, x['col'] or 0))


# ---------------------------------------------------------------- lint
def _resolve_channel(channel, channels_dir=None):
    if channel is None or isinstance(channel, dict):
        return channel
    return LF.resolve_channel(channel, channels_dir)


def _settings(profile, fmt, channel, max_words, variant, house_style):
    f = fmt or (channel or {}).get('format_id') or None
    return (LF.resolve_settings(profile, f, max_words),
            LE.resolve_settings(profile, f, max_words, variant=variant, house_style=house_style))


def _facts(facts):
    if facts is None or isinstance(facts, LE._Facts):
        return facts
    return LE._Facts(facts)


def _lint_prose(text, lang, profile, kind, fa_st, en_st, channel, facts):
    text = LF.clean_text(text)
    if lang == 'auto':
        lang = _decide(*letter_counts(text, kind, profile))
    if lang == 'fa':
        issues, stats = LF.lint(text, profile=profile, kind=kind, settings=fa_st, channel=channel)
        return issues, stats, 'fa'
    if lang == 'en':
        issues, stats = LE.lint(text, kind=kind, settings=en_st, channel=channel, facts=facts)
        return issues, stats, 'en'
    segs, major = segments(text, kind, profile)
    langs = set(s[3] for s in segs)
    if len(langs) < 2:
        one = langs.pop() if langs else major
        return _lint_prose(text, one, profile, kind, fa_st, en_st, channel, facts)
    fa_copy, en_copy = _copies(text, segs)
    fa_i, fa_s = LF.lint(fa_copy, profile=profile, kind=kind, settings=fa_st)
    if major == 'fa':
        # English lines in a Persian-majority file are quotes and examples: line rules only
        en_st = dict(en_st, fragments=True)
    en_i, en_s = LE.lint(en_copy, kind=kind, settings=en_st, facts=facts)
    issues = _by_pos(fa_i + en_i)
    split = {'fa_segments': sum(1 for s in segs if s[3] == 'fa'),
             'en_segments': sum(1 for s in segs if s[3] == 'en')}
    stats = _merge_stats(fa_s, en_s, split)
    if channel:
        ch_issues, ch_info = LE._channel_check(text, channel)
        extra = LE._hub_issues([LE._mk(0, 0, code, level, msg) for level, code, msg in ch_issues])
        issues = _by_pos(extra + issues)
        stats['channel'] = ch_info
        stats = _recount(issues, stats)
    return issues, stats, 'mixed'


def _value_lang(v, major):
    fa, en = _count(_value_masked(v))
    if not fa and not en:
        return None
    if fa == en:
        return major
    return 'fa' if fa > en else 'en'


def _lint_locale(text, path, lang, profile, fa_st, en_st, channel, facts):
    text = LF.clean_text(text)
    p = path or _guess_locale_path(text)
    entries = LF.extract_locale(text, p)
    if lang == 'fa':
        issues, stats = LF.lint_locale(text, p, profile, settings=fa_st, channel=channel, entries=entries)
        return issues, stats, 'fa'
    if lang == 'en':
        issues, stats = LE.lint_locale(text, p, settings=en_st, channel=channel, entries=entries, facts=facts)
        return issues, stats, 'en'
    fa_all = en_all = 0
    for _k, v, _l in entries:
        if isinstance(v, str):
            a, b = _count(_value_masked(v))
            fa_all, en_all = fa_all + a, en_all + b
    major = 'fa' if fa_all >= en_all else 'en'
    fa_e = [e for e in entries if isinstance(e[1], str) and _value_lang(e[1], major) == 'fa']
    en_e = [e for e in entries if isinstance(e[1], str) and _value_lang(e[1], major) == 'en']
    if not en_e:
        return _lint_locale(text, p, 'fa', profile, fa_st, en_st, channel, facts)
    if not fa_e:
        return _lint_locale(text, p, 'en', profile, fa_st, en_st, channel, facts)
    fa_i, fa_s = LF.lint_locale(text, p, profile, settings=fa_st, channel=channel, entries=fa_e)
    en_i, en_s = LE.lint_locale(text, p, settings=en_st, channel=channel, entries=en_e, facts=facts)
    stats = _merge_stats(fa_s, en_s, {'fa_segments': len(fa_e), 'en_segments': len(en_e)})
    stats['strings'] = fa_s.get('strings', 0) + en_s.get('strings', 0)
    return _by_pos(fa_i + en_i), stats, 'mixed'


def _lint_csv(text, path, lang, profile, fa_st, en_st, channel, facts, columns, key, md):
    text = LF.clean_text(text)
    if lang == 'fa':
        issues, stats = LF.lint_csv(text, path, profile, settings=fa_st, channel=channel, columns=columns,
                                    key=key, md=md)
        return issues, stats, 'fa'
    if lang == 'en':
        issues, stats = LE.lint_csv(text, path, settings=en_st, channel=channel, columns=columns, key=key, md=md,
                                    facts=facts)
        return issues, stats, 'en'
    info = LF.csv_cells(text, path, columns, key)
    fa_all = en_all = 0
    for c in info['cells']:
        a, b = _count(LF.mask_prose(c[3], 'text'))
        fa_all, en_all = fa_all + a, en_all + b
    major = 'fa' if fa_all >= en_all else 'en'
    en_keys, n_fa, n_en = set(), 0, 0
    for rowno, code, col, value, _line in info['cells']:
        vl = _value_lang(value, major)
        if vl == 'en':
            en_keys.add('row %d/%s/%s' % (rowno, code, col))
            n_en += 1
        elif vl == 'fa':
            n_fa += 1
    if not n_en:
        return _lint_csv(text, path, 'fa', profile, fa_st, en_st, channel, facts, columns, key, md)
    if not n_fa:
        return _lint_csv(text, path, 'en', profile, fa_st, en_st, channel, facts, columns, key, md)
    fa_i, fa_s = LF.lint_csv(text, path, profile, settings=fa_st, channel=channel, columns=columns, key=key, md=md)
    fa_i = [x for x in fa_i if x.get('key') not in en_keys]      # English cells belong to lint_en
    fa_s = _recount(fa_i, fa_s)
    en_i, en_s = LE.lint_csv(text, path, settings=en_st, channel=channel, columns=columns, key=key, md=md,
                             facts=facts)
    stats = _merge_stats(fa_s, en_s, {'fa_segments': n_fa, 'en_segments': n_en})
    return _by_pos(fa_i + en_i), stats, 'mixed'


def lint_text(text, lang='auto', profile=None, fmt=None, channel=None, md=False, max_words=None, facts=None,
              kind=None, channels_dir=None, variant=None, house_style=None):
    """Lint Persian, English or mixed text. Returns (issues, stats, lang)."""
    if lang not in ('auto', 'fa', 'en'):
        raise UserError('lang must be auto, fa or en (got %r)' % (lang,))
    profile = _as_profile(profile)
    channel = _resolve_channel(channel, channels_dir)
    kind = kind or ('md' if md else 'text')
    fa_st, en_st = _settings(profile, fmt, channel, max_words, variant, house_style)
    fx = _facts(facts)
    if kind == 'locale':
        return _lint_locale(text, None, lang, profile, fa_st, en_st, channel, fx)
    if kind == 'csv':
        return _lint_csv(text, '', lang, profile, fa_st, en_st, channel, fx, None, None, md)
    return _lint_prose(text, lang, profile, kind, fa_st, en_st, channel, fx)


def to_json_issue(x):
    return {'line': x['line'] or None, 'col': x['col'] or None, 'key': x.get('key'),
            'rule': x['code'], 'severity': x['level'], 'message': x['message'], 'excerpt': x['text']}


def _lint_loaded(text, path, kind, lang, profile, fa_st, en_st, channel, facts, csv_columns, csv_key, md):
    if kind == 'locale':
        return _lint_locale(text, path if path not in (None, '-') else None, lang, profile, fa_st, en_st,
                            channel, facts)
    if kind == 'csv':
        return _lint_csv(text, path if path not in (None, '-') else '', lang, profile, fa_st, en_st, channel,
                         facts, csv_columns, csv_key, md)
    return _lint_prose(text, lang, profile, kind, fa_st, en_st, channel, facts)


def lint_path(path, lang='auto', profile=None, fmt=None, channel=None, md=None, csv_columns=None, csv_key=None,
              facts=None, channels_dir=None, variant=None, house_style=None, max_words=None):
    """Lint one file. Returns a files[] entry: {'path', 'lang', 'issues' (JSON form), 'stats'}."""
    if lang not in ('auto', 'fa', 'en'):
        raise UserError('lang must be auto, fa or en (got %r)' % (lang,))
    profile = _as_profile(profile)
    channel = _resolve_channel(channel, channels_dir)
    fa_st, en_st = _settings(profile, fmt, channel, max_words, variant, house_style)
    text = LF.read_text(path)
    kind = LF.detect_kind(path, bool(md))
    issues, stats, lg = _lint_loaded(text, path, kind, lang, profile, fa_st, en_st, channel, _facts(facts),
                                     csv_columns, csv_key, bool(md))
    return {'path': path, 'lang': lg, 'issues': [to_json_issue(x) for x in issues], 'stats': stats}


# ---------------------------------------------------------------- fix
def fix_text(text, kind='text', lang='auto', profile=None, en_settings=None):
    """Mechanical fixes by language; mixed text is fixed line by line (cell by cell in tables).
    (fixed text, changed line count). Keeps CRLF; the BOM is dropped (write_text restores it)."""
    profile = _as_profile(profile)
    if kind in ('locale', 'csv'):
        return text, 0
    raw = text.replace(LF.BOM, '')
    clean = LF.clean_text(raw)
    en_st = en_settings or LE.resolve_settings(profile)
    if lang == 'auto':
        lang = _decide(*letter_counts(clean, kind, profile))
    if lang == 'fa':
        return LF.fix_text(raw, kind=kind)
    if lang == 'en':
        return LE.fix_text(raw, kind=kind, settings=en_st)
    segs, major = segments(clean, kind, profile)
    langs = set(s[3] for s in segs)
    if len(langs) < 2 or '\r' in raw.replace('\r\n', ''):
        return fix_text(raw, kind, langs.pop() if len(langs) == 1 else major, profile, en_st)
    fa_copy, en_copy = _copies(raw, segs)
    fixed_fa = LF.fix_text(fa_copy, kind=kind)[0].split('\n')
    fixed_en = LE.fix_text(en_copy, kind=kind, settings=en_st)[0].split('\n')
    orig = raw.split('\n')
    by_line = {}
    for i, a, b, lg in segs:
        by_line.setdefault(i, []).append(lg)
    out = []
    for i, ln in enumerate(orig):
        lg = by_line.get(i)
        if not lg:
            out.append(ln)
        elif len(lg) == 1 and not (kind == 'md' and '|' in ln and len(LF._table_cells(ln.rstrip('\r'))) > 1):
            out.append(fixed_fa[i] if lg[0] == 'fa' else fixed_en[i])
        else:
            pf, pe = LF._PIPE.split(fixed_fa[i]), LF._PIPE.split(fixed_en[i])
            po = LF._PIPE.split(ln)
            if not (len(pf) == len(pe) == len(po)):
                out.append(ln)
                continue
            cells_lang = _cell_langs(ln.rstrip('\r'), [s for s in segs if s[0] == i])
            parts = []
            for j, part in enumerate(po):
                cl = cells_lang.get(j)
                parts.append(pf[j] if cl == 'fa' else pe[j] if cl == 'en' else part)
            out.append('|'.join(parts))
    new = '\n'.join(out)
    n = sum(1 for x, y in zip(orig, out) if x != y)
    return new, n


def _cell_langs(line, segs):
    """{part index after splitting on unescaped pipes: lang} for one table row."""
    cuts = [m.start() for m in LF._PIPE.finditer(line)]
    out = {}
    for _i, a, _b, lg in segs:
        idx = sum(1 for c in cuts if c < a)
        out[idx] = lg
    return out


# ---------------------------------------------------------------- command line
def rules_json():
    rows = LF._HUB.rules_rows('fa', LF.rule_list()) if LF._HUB is not None else LF.rule_list()
    fa = {'version': 2, 'tool_version': LF.__version__, 'rules': rows, 'lexicon': LF.LEXICON,
          'jargon': LF.JARGON, 'formats': dict((k, LF.FORMAT_DEFAULTS[k]) for k in LF.FORMAT_IDS)}
    return {'version': 2, 'fa': fa, 'en': LE.rules_json()}


def _hub_events():
    """hub_events while this run may record counts (statistics or packets on, not CI), else None."""
    if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
        return None
    try:
        import hub_events
        return hub_events if hub_events.enabled() else None
    except Exception:
        return None


def _lint_recorded(hub, fmt, text, *args):
    """_lint_loaded(text, *args), and one `lint` event with the shown and the hidden findings (ids only)."""
    collecting = getattr(LF._HUB, '_collecting', None) if LF._HUB is not None else None
    if not callable(collecting):
        issues, stats, lg = _lint_loaded(text, *args)
        hidden = []
    else:
        with collecting() as found:
            issues, stats, lg = _lint_loaded(text, *args)
        hidden = list(found)
    try:
        hub.record_lint('cli', lg, fmt, (issues, hidden), textcount.word_count(text))
    except Exception:
        pass
    for x in issues:                  # internal fields of the collector never reach the output
        for k in ('_pid', '_level', '_end'):
            x.pop(k, None)
    return issues, stats, lg


def _terminal_notices(a):
    """The Hub's one-time notices on stderr, at the end of a run in a terminal (never with --json)."""
    if a.json:
        return
    try:
        if not (sys.stdin.isatty() and sys.stderr.isatty()):
            return
        import hub_client
        hub_client.terminal_notices()
    except Exception:
        pass


def _err(msg):
    LE._err(msg, 'lint')


def _print_fa_file(r, out):
    """lint_fa's text lines for a Persian file."""
    for x in r['issues']:
        if x.get('key'):
            where = '%s#%s' % (r['path'], x['key'])
        elif x['line']:
            where = '%s:%d:%d' % (r['path'], x['line'], x['col'])
        else:
            where = r['path']
        tail = '  «%s»' % x['text'] if x['text'] else ''
        out.write('%s  %-7s %-18s %s%s\n' % (where, x['level'], x['code'], x['message'], tail))
    s = r['stats']
    head = '%s: [fa] ' % r['path']
    if s.get('kind') == 'locale':
        head += '%d رشته‌ی فارسی، ' % s.get('strings', 0)
    elif s.get('kind') == 'csv':
        head += '%d ردیف (%d با مسئله)، %d خانه؛ ' % (s.get('rows', 0), s.get('rows_flagged', 0), s.get('cells', 0))
    out.write('%s%d جمله، میانگینِ %s واژه، سقفِ %s · %d خطا · %d هشدار\n\n'
              % (head, s['sentences'], s['avg_words'], s['max_words'], s['errors'], s['warnings']))


DESCRIPTION = ('Whalory %s copy checker for Persian and English. It picks the language of each file, locale '
               'value, CSV cell or line and sends it to lint_fa or lint_en; --lang fa|en forces one. '
               'بازبینِ متنِ فارسی و انگلیسیِ والوری. زبانِ هر فایل، مقدار، خانه یا سطر خودکار تشخیص داده '
               'می‌شود و lint_fa یا lint_en آن را می‌سنجد. --lang fa یا --lang en زبان را ثابت می‌کند.'
               % __version__)


def main(argv=None):
    LE._setup_stdio()
    ap = LE.build_parser(prog='lint', with_lang=True, description=DESCRIPTION)
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0) if e.code in (0, None) else 2
    if LF._HUB is not None:     # --no-overlay: built-in rules only (spec 5.9)
        LF._HUB.set_cli_disabled(a.no_overlay)
    lang = a.lang or ('fa' if a.fa_only else 'en' if a.en_only else 'auto')
    if sum(1 for x in (a.lang, a.fa_only or None, a.en_only or None) if x) > 1:
        _err('use only one of --lang, --fa-only and --en-only.')
        return 2
    out = sys.stdout
    if a.rules:
        if a.json:
            out.write(json.dumps(rules_json(), ensure_ascii=False, indent=1) + '\n')
        else:
            out.write('== fa (lint_fa %s) ==\n' % LF.__version__)
            sys.stdout.flush()
            LF.print_rules(False)
            sys.stdout.flush()
            out.write('\n== en (lint_en %s) ==\n' % LE.__version__)
            LE.print_rules(False)
        return 0
    paths = LF.iter_paths(a.paths)
    if not paths and not a.text:
        ap.print_usage(sys.stderr)
        _err('give at least one file, folder, - or --text.')
        return 2
    if a.write and not a.fix:
        _err('--write only works with --fix; ignored.')
    profile = load_profile(a.profile) if a.profile else {}
    if a.profile == 'auto' and not profile:
        _err('no voice.json found here or above; checked without a profile.')
    channel = LF.resolve_channel(a.channel, a.channels_dir) if a.channel else None
    for w in (channel or {}).get('load_warnings', []):
        _err(w)
    fmt = a.fmt or (channel or {}).get('format_id') or None
    if a.fmt and a.fmt not in LF.FORMAT_DEFAULTS and a.fmt not in (profile.get('formats') or {}):
        raise UserError('unknown format "%s". Formats: %s' % (a.fmt, ', '.join(LF.FORMAT_IDS)))
    fa_st, en_st = _settings(profile, fmt, channel, a.max_words, a.variant, a.house_style)
    facts = LE._read_facts(a.facts)
    inputs = [('<text>', None, t) for t in (a.text or [])] + [(p, p, None) for p in paths]
    report, any_bad, input_errors, csv_seen = [], False, 0, False
    hub = _hub_events()
    say = _err if a.json else (lambda m: out.write(m + '\n'))
    for label, path, inline in inputs:
        try:
            meta = {}
            if path is None:
                text, kind = inline, ('md' if a.md else 'text')
            elif path == '-':
                text, kind, label = LF.read_text('-'), ('md' if a.md else 'text'), '-'
                if a.csv_columns or a.csv_key:
                    kind = 'csv'
            else:
                text, meta = LF.read_text(path, with_meta=True)
                kind = LF.detect_kind(path, a.md)
            fixed_lines = None
            if a.fix:
                if kind in ('locale', 'csv'):
                    _err('--fix does not change %s files; %s was left as is. Fix the values by hand so keys and '
                         'placeholders stay intact.' % ('locale' if kind == 'locale' else 'CSV/TSV', label))
                else:
                    fixed, fixed_lines = fix_text(text, kind, lang, profile, en_st)
                    if path in (None, '-'):
                        sys.stdout.flush()
                        buf = getattr(sys.stdout, 'buffer', None)
                        if buf is not None:
                            buf.write(fixed.encode('utf-8'))
                            buf.flush()
                        else:
                            sys.stdout.write(fixed)
                        continue
                    target = path if a.write else '%s.fixed%s' % os.path.splitext(path)
                    LF.write_text(target, fixed, meta)
                    say('fixed: %d lines changed -> %s' % (fixed_lines, target))
                    text = fixed
            args = (path, kind, lang, profile, fa_st, en_st, channel, facts, a.csv_columns, a.csv_key, a.md)
            if hub is not None:
                issues, stats, lg = _lint_recorded(hub, fmt, text, *args)
            else:
                issues, stats, lg = _lint_loaded(text, *args)
            if kind == 'csv':
                csv_seen = True
            if fixed_lines is not None:
                stats['fixed_lines'] = fixed_lines
            report.append({'path': label, 'lang': lg, 'issues': issues, 'stats': stats})
            if stats['errors'] or (a.strict and stats['warnings']):
                any_bad = True
        except UserError as e:
            _err(str(e))
            input_errors += 1
            report.append({'path': label, 'lang': None, 'issues': [], 'stats': {}, 'error': str(e)})
    if (a.csv_columns or a.csv_key) and not csv_seen and not input_errors:
        _err('--csv-columns and --csv-key only apply to CSV or TSV files; ignored.')
    if a.json:
        if report:
            files = []
            for r in report:
                f = {'path': r['path'], 'lang': r['lang'], 'issues': [to_json_issue(x) for x in r['issues']],
                     'stats': r['stats']}
                if r.get('error'):
                    f['error'] = r['error']
                files.append(f)
            out.write(json.dumps({'version': 2, 'files': files,
                                  'summary': {'errors': sum(r['stats'].get('errors', 0) for r in report),
                                              'warnings': sum(r['stats'].get('warnings', 0) for r in report)}},
                                 ensure_ascii=False, indent=1) + '\n')
    else:
        LE.print_text_report([], profile, en_st, channel, out)          # header lines only
        for r in report:
            if r.get('error'):
                continue
            if r.get('lang') == 'fa':
                _print_fa_file(r, out)
            else:
                LE.print_text_report([r], None, {}, None, out, lang_label=True)
    sys.stdout.flush()
    _terminal_notices(a)
    if input_errors:
        return 2
    return 1 if any_bad else 0


def run(argv=None):
    """CLI with friendly errors; returns the exit code and never calls sys.exit."""
    try:
        return main(argv)
    except UserError as e:
        _err(str(e))
        return 2
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        try:
            sys.stdout = open(os.devnull, 'w')
        except Exception:
            pass
        return 0
    except Exception as e:  # unexpected; traceback only with WHALORY_DEBUG=1
        if os.environ.get('WHALORY_DEBUG') or os.environ.get('WHALYA_DEBUG'):  # WHALYA_*: deprecated name
            raise
        _err('unexpected error: %s: %s. Set WHALORY_DEBUG=1 and run it again for details.' % (type(e).__name__, e))
        return 2


if __name__ == '__main__':
    sys.exit(run())
