#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hub_mine: outcome computation, Tier 2 list matching and weekly aggregation (Whalory Hub).

Spec sections 5.3 (outcome computation inside check_final), 5.4 (phrase discovery
from a shipped list), 5.5 (the weekly report, whalory.report/2) and 17.3 (the global
lane's packet, whalory.packet/1). Standard library only, Python 3.8 to 3.14.

This module opens no socket, starts no process and writes no file. hub_events calls
it to compute the `out` event of one outcome; hub_client calls it to build the weekly
report or packet from that week's events and writes the result itself.

Public API (none of it prints; the aggregation functions never raise on bad events,
they skip them):

    compute_case(case, deadline=None) -> {"held_out", "recorded", "reason", "event"}
        The inner outcome function. It takes the sentences of both texts, the findings
        of every check as token ranges, the checks, the install salt, the week and
        `now`, and reproduces every case of STUDIO/hub/contracts/outcome_vectors.json
        (reference: contracts/tools/outcome_ref.py). A case may also carry `hidden`
        ({id: bool}) to replace the holdout computation, and `countable_ids`.
    outcome_from_texts(shown, final, ctx) -> {"recorded", "reason", "event"}
        The real path used by hub_events.record_outcome: resolves the language, lints
        both texts through ctx["lint"], maps findings to sentences and tokens, measures
        the tunable parameters, and adds Tier 2 rows when ctx["tier2"] is set.
    tier2_rows(shown_sents, final_sents, ops, lang, ngram_index, blocklist) -> [[id, del, kept]]
    load_ngram_index(path, lang, blocked=None) -> {tuple(tokens): id}   (blocked: sensitive words)
    aggregate(events, known_ids=None) -> body dict (volume, cells, placebo, params, playbooks, health)
    build_report(epoch, events, consent, client, secret, phrases=False, known_ids=None) -> dict | None
    build_packet(epoch, events, consent, client, known_ids=None) -> dict | None
    render_packet(packet) -> str          the fenced json block, one array element per line
    select_phrases(events) -> [row]       Tier 2 weekly selection (spec 5.4 step 7)
    deletion_hash(secret) -> str          base64url(SHA-256(secret)), unpadded
    py_bucket() -> '3.8-3.9' | '3.10-3.11' | '3.12+'
    fg_of(format) -> 'short' | 'long' | 'ui' | 'none'

Definitions the spec leaves open are the ones of contracts/tools/outcome_ref.py (tokens,
placebo positions, half-up rounding, refusal order) and contracts/README.md.
"""
from __future__ import print_function

import sys

sys.dont_write_bytecode = True

import base64  # noqa: E402
import datetime  # noqa: E402
import difflib  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402
import unicodedata  # noqa: E402
from fractions import Fraction  # noqa: E402

__all__ = ['compute_case', 'outcome_from_texts', 'tier2_rows', 'load_ngram_index', 'aggregate',
           'build_report', 'build_packet', 'render_packet', 'select_phrases', 'deletion_hash',
           'py_bucket', 'fg_of', 'tokens', 'normalise', 'split_sentences']

# ----------------------------------------------------------------------------- constants

TOKEN_RE = re.compile("[^\\W_]+(?:[‌'’\\-][^\\W_]+)*")
_WS = re.compile(r'\s+')
_SPLIT = re.compile('(?<=[.!?؟])[ \\t]+|\\n+')
MAX_CHARS = 20000
MAX_TOKENS = 4000
BLOCK_TOKENS = 300
SESSION_BUDGET = 3
WEEK_BUDGET = 20
BUDGET_SECONDS = 0.300
MAX_SENTENCES = 2000          # sentence alignment is quadratic in the worst case (spec 5.12)
PUBLICITY = datetime.timedelta(days=14)
DEFAULT_HOLDOUT = {'warning': 10, 'error': 5}

FG_OF_FORMAT = {}
for _fg, _names in (('short', 'caption story reels carousel post sms push ad headline subject name bot reply'),
                    ('long', 'email landing about blog press deck script product listing'),
                    ('ui', 'ui error otp hard')):
    for _n in _names.split():
        FG_OF_FORMAT[_n] = _fg
FGS = ('short', 'long', 'ui', 'none')
LANGS = ('fa', 'en')

#: Per-contributor bounds of report/2 and packet/1 (spec 5.5; final_errors: contracts README decision 3).
BOUNDS = {'hits': 200, 'kept': 10, 'ho': 10, 'placebo_n': 200, 'param_n': 10, 'playbook_n': 50,
          'revisions_per_n': 5, 'final_errors_per_n': 10, 'health': 1000, 'words': 200000}
LIMITS = {'cells': 600, 'params': 200, 'playbooks': 100, 'volume': 8, 'placebo': 8, 'phrases': 20}
REPORT_MAX_BYTES = 64 * 1024
PACKET_MAX_CHARS = 60000
MIN_OUT_EVENTS = 3
MIN_LINT_EVENTS = 20
HEALTH_KINDS = ('selftest_ok', 'selftest_fail', 'overlay_exception', 'revert', 'sync_ok', 'sync_fail')
HEALTH_REASONS = {'cap_reject': ('violation', 'gap'), 'verify_fail': ('fork', 'mismatch', 'local')}

_RULE_ID = re.compile(r'^[a-z0-9-]{1,40}$')
_PARAM_ID = re.compile(r'^(fa|en):[a-z0-9-]{1,40}[.][a-z0-9_]{1,32}$')
_PLAYBOOK_ID = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
_NG_ID = re.compile(r'^ng-(fa|en)-[0-9a-f]{10}$')
_EPOCH = re.compile(r'^[0-9]{4}-W(0[1-9]|[1-4][0-9]|5[0-3])$')
_DATE = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')


# ----------------------------------------------------------------------------- text basics

def normalise(sentence):
    """NFKC, every run of whitespace becomes one space, stripped (alignment only)."""
    return _WS.sub(' ', unicodedata.normalize('NFKC', sentence)).strip()


def tokens(text):
    """Runs of letters and digits joined across ZWNJ, ' , U+2019 and - (outcome_ref)."""
    return TOKEN_RE.findall(normalise(text))


def split_sentences(text):
    """After . ! ? or U+061F plus spaces, and at newlines; each part normalised."""
    return [s for s in (normalise(p) for p in _SPLIT.split(unicodedata.normalize('NFKC', text))) if s]


def sentence_spans(text):
    """[(start, end)] of the raw sentences of `text`, split like split_sentences.

    Offsets refer to `text` itself (not its NFKC form), so lint findings can be placed.
    Parts that normalise to nothing are left out, exactly as split_sentences does.
    """
    out = []
    pos = 0
    for m in _SPLIT.finditer(text):
        if normalise(text[pos:m.start()]):
            out.append((pos, m.start()))
        pos = m.end()
    if normalise(text[pos:]):
        out.append((pos, len(text)))
    return out


def fg_of(fmt):
    """Format group of a format id (spec 5.5); a group name passes through."""
    if fmt in FGS:
        return fmt
    return FG_OF_FORMAT.get((fmt or '').strip().lower(), 'none')


def py_bucket(version_info=None):
    v = version_info or sys.version_info
    if (v[0], v[1]) < (3, 10):
        return '3.8-3.9'
    if (v[0], v[1]) < (3, 12):
        return '3.10-3.11'
    return '3.12+'


def deletion_hash(secret):
    """Unpadded base64url of SHA-256 of the 32-byte deletion secret (report.del)."""
    return base64.urlsafe_b64encode(hashlib.sha256(bytes(secret)).digest()).decode('ascii').rstrip('=')


def _parse_time(s):
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)


def _as_time(v):
    if isinstance(v, datetime.datetime):
        return v if v.tzinfo else v.replace(tzinfo=datetime.timezone.utc)
    return _parse_time(v)


# ----------------------------------------------------------------------------- holdout

def holdout_value(salt, epoch, lang, rid):
    """int(SHA-256(salt || b"measure" || epoch || lang || id)[:4]) % 100 (spec 5.3)."""
    h = hashlib.sha256(bytes(salt) + b'measure' + epoch.encode('ascii') + lang.encode('ascii')
                       + rid.encode('ascii'))
    return int.from_bytes(h.digest()[:4], 'big') % 100


def holdout_rate(severity, locked=False, holdout=None):
    """H for one check: 0 locked, 100 shadow, else the baseline's measure.holdout."""
    holdout = holdout or DEFAULT_HOLDOUT
    if locked:
        return 0
    if severity == 'shadow':
        return 100
    if severity == 'error':
        return int(holdout.get('error', 5))
    return int(holdout.get('warning', 10))


def is_held_out(salt, epoch, lang, rid, rate):
    return holdout_value(salt, epoch, lang, rid) < rate


def canary_bucket(salt, release_id):
    """Spec 6.14: int(SHA-256(salt || release id)[:8]) % 10000."""
    return int.from_bytes(hashlib.sha256(bytes(salt) + release_id.encode('ascii')).digest()[:8], 'big') % 10000


def _round2(x):
    """Half up to two decimals, from an exact Fraction."""
    return math.floor(x * 100 + Fraction(1, 2)) / 100


# ----------------------------------------------------------------------------- outcome core (spec 5.3)

def _placebo_spans(salt, sentence, covered):
    toks = tokens(sentence)
    cands = [j for j in range(len(toks) - 1) if j not in covered and j + 1 not in covered]
    if not cands:
        return toks, []
    h = hashlib.sha256(bytes(salt) + sentence.encode('utf-8')).digest()
    first = cands[int.from_bytes(h[0:4], 'big') % len(cands)]
    spans = [first]
    rest = [j for j in cands if abs(j - first) >= 2]
    if rest:
        spans.append(rest[int.from_bytes(h[4:8], 'big') % len(rest)])
    return toks, spans


def _pairs(sentence):
    t = tokens(sentence)
    return set(zip(t, t[1:]))


class _Budget(Exception):
    pass


def _refusal(case):
    """The refusal order of contracts README decision 11, or None."""
    state = case.get('state', {})
    shown_text, final_text = case.get('shown'), case['final']
    if shown_text is None or not state.get('shown_available', True):
        return 'unlinted'
    if final_text == shown_text:
        return 'unchanged'
    if state.get('process_outcomes', 0) >= SESSION_BUDGET:
        return 'session_budget'
    if state.get('week_outcomes', 0) >= WEEK_BUDGET:
        return 'week_budget'
    for t in (shown_text, final_text):
        if len(t) > MAX_CHARS or len(tokens(t)) > MAX_TOKENS:
            return 'too_long'
    return None


def compute_case(case, deadline=None, want_ops=False):
    """Outcome of one case; see the module docstring. `deadline` is a time.monotonic() value.

    Returns {"held_out": {id: bool}, "recorded": bool, "reason": str|None, "event": dict|None};
    with want_ops also "ops" (the sentence opcodes, for Tier 2).
    """
    salt = bytes.fromhex(case['install_salt']) if isinstance(case['install_salt'], str) else bytes(case['install_salt'])
    epoch = case['epoch']
    lang = case['lang']
    now = _as_time(case['now'])
    checks = case['checks']
    holdout = case.get('holdout') or DEFAULT_HOLDOUT
    given_hidden = case.get('hidden')
    hidden = {}
    for rid in sorted(checks):
        if given_hidden is not None:
            hidden[rid] = bool(given_hidden.get(rid, False))
        else:
            c = checks[rid]
            hidden[rid] = is_held_out(salt, epoch, lang, rid,
                                      holdout_rate(c.get('severity'), c.get('locked'), holdout))
    out = {'held_out': hidden, 'recorded': False, 'reason': None, 'event': None}

    reason = _refusal(case)
    if reason:
        out['reason'] = reason
        return out

    s_shown = [normalise(x) for x in case['shown_sentences']]
    s_final = [normalise(x) for x in case['final_sentences']]
    t_shown = [tokens(x) for x in s_shown]
    t_final = [tokens(x) for x in s_final]
    countable_ids = case.get('countable_ids')

    def countable(rid):
        if countable_ids is not None:
            return rid in countable_ids
        c = checks[rid]
        if rid.startswith('ht-'):
            issued = c.get('issued')
            if not issued:
                return False
            return now - _as_time(issued) >= PUBLICITY
        return True

    by_sent = {'shown': {}, 'final': {}}
    loose = {'shown': {}, 'final': {}}   # findings with no sentence (s is None): kept and fe only
    for side in ('shown', 'final'):
        for f in case['findings'][side]:
            if f['id'] not in checks:
                raise ValueError('finding of unknown check %s' % f['id'])
            if f.get('s') is None:
                loose[side][f['id']] = loose[side].get(f['id'], 0) + 1
            else:
                by_sent[side].setdefault(f['s'], []).append(f)

    def count(side, rid, sentences):
        return sum(1 for i in sentences for f in by_sent[side].get(i, ()) if f['id'] == rid)

    ho, hg = {}, {}
    pl_n = pl_g = 0
    params = {}
    matched = 0
    td = 0
    param_defs = case.get('params') or {}
    values = case.get('param_values') or {'shown': {}, 'final': {}}

    if deadline is not None and time.monotonic() > deadline:
        out['reason'] = 'budget'
        return out
    ops = difflib.SequenceMatcher(None, s_shown, s_final, autojunk=False).get_opcodes()
    try:
        for tag, i1, i2, j1, j2 in ops:
            if deadline is not None and time.monotonic() > deadline:
                raise _Budget()
            a_tok = [t for i in range(i1, i2) for t in t_shown[i]]
            b_tok = [t for j in range(j1, j2) for t in t_final[j]]
            if tag == 'equal':
                matched += len(a_tok)
                continue
            if tag == 'delete':
                td += len(a_tok)
                continue
            if tag == 'insert':
                continue
            if len(a_tok) > BLOCK_TOKENS or len(b_tok) > BLOCK_TOKENS:
                td += len(a_tok)
                continue
            shown_idx = range(i1, i2)
            final_idx = range(j1, j2)
            for rid in sorted(checks):
                if hidden[rid] and countable(rid):
                    h1 = count('shown', rid, shown_idx)
                    hf = count('final', rid, final_idx)
                    if h1:
                        ho[rid] = ho.get(rid, 0) + h1
                        hg[rid] = hg.get(rid, 0) + max(0, h1 - hf)
            final_pairs = set()
            for j in final_idx:
                final_pairs |= _pairs(s_final[j])
            for i in shown_idx:
                covered = set()
                for f in by_sent['shown'].get(i, ()):
                    covered.update(range(f['t'][0], f['t'][1]))
                toks, spans = _placebo_spans(salt, s_shown[i], covered)
                for j in spans:
                    pl_n += 1
                    if (toks[j], toks[j + 1]) not in final_pairs:
                        pl_g += 1
            for pid in sorted(param_defs):
                width = Fraction(repr(param_defs[pid]['bucket']))
                if width <= 0:
                    continue
                fvals = values.get('final', {}).get(pid)
                svals = values.get('shown', {}).get(pid)
                if fvals is None or svals is None:
                    continue
                finals = [math.floor(Fraction(repr(fvals[j])) / width) for j in final_idx]
                for i in shown_idx:
                    b = math.floor(Fraction(repr(svals[i])) / width)
                    slot = params.setdefault(pid, {}).setdefault(str(b), {'n': 0, 'g': 0})
                    slot['n'] += 1
                    if all(fb < b for fb in finals):
                        slot['g'] += 1
            sm = difflib.SequenceMatcher(None, a_tok, b_tok, autojunk=False)
            matched += sum(m.size for m in sm.get_matching_blocks())
            for op, a1, a2, _b1, _b2 in sm.get_opcodes():
                if op in ('delete', 'replace'):
                    td += a2 - a1
    except _Budget:
        out['reason'] = 'budget'
        return out

    kept = {}
    fe = 0
    for rid in sorted(checks):
        if hidden[rid]:
            continue
        k = count('final', rid, range(len(s_final))) + loose['final'].get(rid, 0)
        if k and countable(rid):
            kept[rid] = k
        if checks[rid].get('severity') == 'error':
            fe += k

    total = sum(len(t) for t in t_shown) + sum(len(t) for t in t_final)
    er = _round2(1 - Fraction(2 * matched, total)) if total else 0.0
    cells = {}
    for rid in sorted(set(ho) | set(kept)):
        if rid in ho:
            cells[rid] = {'ho': ho[rid], 'hg': hg[rid]}
        else:
            cells[rid] = {'kept': kept[rid]}
    event = {
        't': 'out', 'e': epoch, 'day': now.strftime('%Y-%m-%d'), 'lang': lang,
        'fg': FG_OF_FORMAT.get(case.get('format') or '', 'none'),
        'pb': case.get('playbook'), 'rev': case.get('revisions') or 0, 'er': float(er), 'fe': fe,
        'cells': cells, 'pl': {'n': pl_n, 'g': pl_g},
        'params': {pid: dict(sorted(params[pid].items(), key=lambda kv: int(kv[0]))) for pid in sorted(params)},
        'base': {'ta': sum(len(t) for t in t_shown), 'td': td},
    }
    out['recorded'] = True
    out['event'] = event
    if want_ops:
        out['ops'] = ops
    return out


# ----------------------------------------------------------------------------- the real path

def _norm_prefix_len(raw_prefix):
    """Length of normalise() applied to a prefix, keeping a trailing space (for offsets)."""
    return len(_WS.sub(' ', unicodedata.normalize('NFKC', raw_prefix)).lstrip())


def _line_offsets(text):
    starts = [0]
    for i, ch in enumerate(text):
        if ch == '\n':
            starts.append(i + 1)
    return starts


def _issue_offset(issue, line_starts, text_len):
    """Absolute 0-based offset of a lint issue (line and col are 1-based), or None."""
    line = issue.get('line') or 0
    col = issue.get('col') or 0
    if not line or not col or line > len(line_starts):
        return None
    off = line_starts[line - 1] + col - 1
    if off < 0 or off > text_len:
        return None
    return off


def _issue_end(issue, line_starts, text_len):
    """Optional end offset: an internal `_end` column on the same line (hub_overlay may keep it)."""
    end_col = issue.get('_end')
    line = issue.get('line') or 0
    if not end_col or not line or line > len(line_starts):
        return None
    off = line_starts[line - 1] + int(end_col) - 1
    return off if 0 <= off <= text_len else None


def findings_of(text, issues, spans):
    """Map lint issues to {"id", "s", "t"} findings (sentence index and token range).

    The id is the internal phrase id `_pid` when the linter set one (lx-/ht- ids,
    spec 5.3 step 2), else the rule id. An issue without a position gets s None.
    """
    starts = _line_offsets(text)
    norm_tok = []
    for a, b in spans:
        nt = normalise(text[a:b])
        norm_tok.append([(m.start(), m.end()) for m in TOKEN_RE.finditer(nt)])
    out = []
    for x in issues:
        rid = x.get('_pid') or x.get('code') or x.get('rule')
        if not rid:
            continue
        off = _issue_offset(x, starts, len(text))
        if off is None or not spans:
            out.append({'id': rid, 's': None, 't': [0, 0]})
            continue
        si = 0
        for k, (a, _b) in enumerate(spans):
            if a <= off:
                si = k
            else:
                break
        a, b = spans[si]
        rel = min(max(off - a, 0), b - a)
        ns = _norm_prefix_len(text[a:a + rel])
        end = _issue_end(x, starts, len(text))
        ne = _norm_prefix_len(text[a:min(max(end - a, rel), b - a)]) if end is not None else None
        toks = norm_tok[si]
        first = None
        last = None
        for k, (ta, tb) in enumerate(toks):
            if tb <= ns:
                continue
            if first is None:
                first = k
                last = k + 1
                if ne is None:
                    break
                continue
            if ne is not None and ta < ne:
                last = k + 1
            else:
                break
        if first is None:
            out.append({'id': rid, 's': si, 't': [len(toks), len(toks)]})
        else:
            out.append({'id': rid, 's': si, 't': [first, last]})
    return out


def _word_count(sentence, lang):
    if lang == 'fa':
        return len(_FA_WORD.findall(sentence))
    return len(_EN_WORD.findall(sentence))


_FA_WORD = re.compile('[\\w‌٫٬]+')
_EN_WORD = re.compile("[A-Za-z0-9](?:[A-Za-z0-9'’\\-]*[A-Za-z0-9])?")
_VOWELS = re.compile('[aeiouy]+')


def _syllables(word):
    """A small syllable estimate, used only when lint_en.count_syllables is missing."""
    w = word.lower()
    n = len(_VOWELS.findall(w))
    if w.endswith('e') and n > 1:
        n -= 1
    return max(1, n)


def _fkgl(sentence, syllable_fn):
    words = _EN_WORD.findall(sentence)
    if not words:
        return 0
    syl = sum(syllable_fn(w) for w in words)
    return max(0.0, round(0.39 * len(words) + 11.8 * syl / float(len(words)) - 15.59, 1))


def param_measurer(pid, linters=None):
    """A function sentence -> number for a tunable parameter, or None when unknown.

    A linter module may define param_value(name, sentence) (spec 5.9, WP-C2); it wins.
    Built in: <rule>.max_words (words per sentence) and en-readability-grade.max
    (Flesch-Kincaid grade of the sentence alone).
    """
    lang, _, name = pid.partition(':')
    mod = (linters or {}).get(lang)
    fn = getattr(mod, 'param_value', None) if mod is not None else None
    if callable(fn):
        def measured(sentence, _fn=fn, _name=name):
            v = _fn(_name, sentence)
            return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None
        return measured
    if name.endswith('.max_words'):
        return lambda s, _l=lang: _word_count(s, _l)
    if lang == 'en' and name == 'en-readability-grade.max':
        syl = getattr(mod, 'count_syllables', None) if mod is not None else None
        return lambda s, _f=(syl if callable(syl) else _syllables): _fkgl(s, _f)
    return None


def outcome_from_texts(shown, final, ctx):
    """Outcome of one check_final call (spec 5.3), with Tier 2 (spec 5.4) when enabled.

    ctx keys: salt (bytes), epoch, now (datetime), lang ('fa'|'en'|'auto'), format,
    playbook, revisions, state ({process_outcomes, week_outcomes}), detect (text ->
    (lang, ratio)), lint (text, lang -> (issues, hidden_issues)), severities ({id:
    severity} of hidden checks when the linter does not keep a level), phrases_issued
    ({ht id: issued ISO time}), params ({pid: {bucket, ...}} of the baseline policy),
    linters ({lang: module}), tier2 (None or {"index", "blocklist"}), budget (seconds).
    Returns {"recorded", "reason", "event"}; never raises on bad input except a bug.
    """
    started = time.monotonic()
    deadline = started + float(ctx.get('budget', BUDGET_SECONDS))
    lang = ctx.get('lang') or 'auto'
    base_case = {'shown': shown, 'final': final, 'state': ctx.get('state') or {}}
    reason = _refusal(base_case)
    if reason:
        return {'recorded': False, 'reason': reason, 'event': None}
    if lang not in LANGS:
        detect = ctx.get('detect')
        if detect is None:
            return {'recorded': False, 'reason': 'mixed', 'event': None}
        lang = detect(shown)[0]
        if lang not in LANGS:
            return {'recorded': False, 'reason': 'mixed', 'event': None}
    spans_s = sentence_spans(shown)
    spans_f = sentence_spans(final)
    if len(spans_s) > MAX_SENTENCES or len(spans_f) > MAX_SENTENCES:
        return {'recorded': False, 'reason': 'too_long', 'event': None}
    lint = ctx['lint']
    shown_issues, shown_hidden = lint(shown, lang)
    if time.monotonic() > deadline:
        return {'recorded': False, 'reason': 'budget', 'event': None}
    final_issues, final_hidden = lint(final, lang)
    if time.monotonic() > deadline:
        return {'recorded': False, 'reason': 'budget', 'event': None}

    checks = {}
    hidden = {}
    sev_hint = ctx.get('severities') or {}
    phrases_issued = ctx.get('phrases_issued') or {}
    for issues, is_hidden in ((shown_issues, False), (final_issues, False), (shown_hidden, True),
                              (final_hidden, True)):
        for x in issues:
            rid = x.get('_pid') or x.get('code') or x.get('rule')
            if not rid:
                continue
            level = x.get('_level') or x.get('level') or x.get('severity') or sev_hint.get(rid) or 'warning'
            if level not in ('shadow', 'warning', 'error'):
                level = 'warning'
            c = checks.setdefault(rid, {'severity': level})
            if not is_hidden:
                c['severity'] = level
            if rid.startswith('ht-'):
                c['issued'] = phrases_issued.get(rid)
            hidden[rid] = hidden.get(rid, False) or is_hidden
    findings = {
        'shown': findings_of(shown, list(shown_issues) + list(shown_hidden), spans_s),
        'final': findings_of(final, list(final_issues) + list(final_hidden), spans_f),
    }
    s_shown = [normalise(shown[a:b]) for a, b in spans_s]
    s_final = [normalise(final[a:b]) for a, b in spans_f]
    params = {}
    values = {'shown': {}, 'final': {}}
    for pid, spec in sorted((ctx.get('params') or {}).items()):
        if not pid.startswith(lang + ':') or not _PARAM_ID.match(pid):
            continue
        fn = param_measurer(pid, ctx.get('linters'))
        if fn is None:
            continue
        try:
            sv = [fn(s) for s in s_shown]
            fv = [fn(s) for s in s_final]
        except Exception:
            continue
        if any(v is None for v in sv) or any(v is None for v in fv):
            continue
        params[pid] = {'bucket': spec.get('bucket', 1)}
        values['shown'][pid] = sv
        values['final'][pid] = fv
    case = {
        'install_salt': ctx['salt'], 'epoch': ctx['epoch'], 'lang': lang, 'now': ctx['now'],
        'format': ctx.get('format'), 'playbook': ctx.get('playbook'), 'revisions': ctx.get('revisions') or 0,
        'state': ctx.get('state') or {}, 'checks': checks, 'hidden': hidden,
        'shown': shown, 'final': final, 'shown_sentences': s_shown, 'final_sentences': s_final,
        'findings': findings, 'params': params, 'param_values': values,
    }
    res = compute_case(case, deadline=deadline, want_ops=True)
    if not res['recorded']:
        return {'recorded': False, 'reason': res['reason'], 'event': None}
    event = res['event']
    t2 = ctx.get('tier2')
    if t2 and t2.get('index'):
        try:
            rows = tier2_rows(s_shown, s_final, res['ops'], lang, t2['index'], t2.get('blocklist') or ())
        except Exception:
            rows = []
        if time.monotonic() > deadline:
            return {'recorded': False, 'reason': 'budget', 'event': None}
        if rows:
            event['ng'] = rows
    return {'recorded': True, 'reason': None, 'event': event}


# ----------------------------------------------------------------------------- Tier 2 (spec 5.4)

POISON = None
_T2_DROP = re.compile('[ـ‍ً-ٰٟ]')
_T2_SCAN = re.compile(r'(?P<mask>https?://\S+|www\.\S+|[^\s@]+@[^\s@]+\.[^\s@]+|[@#][\w‌]+)'
                      '|(?P<word>[\\w‌\'’]+)')
_T2_TOKEN = re.compile("[^\\W\\d_]+(?:[‌'’][^\\W\\d_]+)*")
_DIGIT = re.compile(r'\d')
_LATIN_UPPER = re.compile('^[A-Z]')


def t2_normalise(text):
    """Step 1: NFKC; Arabic yeh and kaf to Persian; drop tatweel, ZWJ and harakat; collapse spaces."""
    t = unicodedata.normalize('NFKC', text)
    t = t.replace('ي', 'ی').replace('ى', 'ی').replace('ك', 'ک')
    t = _T2_DROP.sub('', t)
    return _WS.sub(' ', t).strip()


def lower_forms(texts):
    """Every token that appears in lower case somewhere in the texts (for the name rule)."""
    seen = set()
    for text in texts:
        for m in _T2_SCAN.finditer(t2_normalise(text)):
            word = m.group('word')
            if word is None or _DIGIT.search(word):
                continue
            for t in _T2_TOKEN.findall(word):
                if not _LATIN_UPPER.match(t):
                    seen.add(t)
    return seen


def t2_tokens(text, lang, blocklist=(), lower_seen=None):
    """Steps 2 and 3: masked and tokenised; POISON (None) stands for every masked token.

    English: a capitalised token that never appears in lower case elsewhere in the same
    text is a name. lower_seen gives the lower-case forms of the whole text when `text`
    is one sentence of it; by default only `text` itself is looked at.
    """
    raw = []
    for m in _T2_SCAN.finditer(t2_normalise(text)):
        if m.group('mask') is not None:
            raw.append(POISON)
            continue
        word = m.group('word')
        if _DIGIT.search(word):
            raw.append(POISON)
            continue
        pieces = _T2_TOKEN.findall(word)
        if not pieces:
            continue
        raw.extend(pieces)
    if lang == 'en':
        if lower_seen is None:
            lower_seen = set(t for t in raw if t is not POISON and not _LATIN_UPPER.match(t))
        out = []
        for t in raw:
            if t is POISON:
                out.append(POISON)
            elif len(t) > 1 and t.isupper():
                out.append(POISON)
            elif _LATIN_UPPER.match(t) and t.lower() not in lower_seen:
                out.append(POISON)
            else:
                out.append(t.lower())
        raw = out
    if blocklist:
        raw = [POISON if (t is not POISON and t.lower() in blocklist) else t for t in raw]
    return raw


def phrase_key(lang, phrase):
    """The token tuple of a listed phrase, tokenised like a text (None if any part is masked)."""
    toks = t2_tokens(phrase, lang)
    if not toks or any(t is POISON for t in toks) or len(toks) > 4:
        return None
    return tuple(toks)


def ng_id(lang, phrase):
    """ng-<lang>- + first 10 hex of SHA-256(lang | ng | NFC(phrase)) (spec 5.4)."""
    return 'ng-%s-%s' % (lang, hashlib.sha256(
        (lang + '|ng|' + unicodedata.normalize('NFC', phrase)).encode('utf-8')).hexdigest()[:10])


def load_ngram_index(path, lang, blocked=None):
    """{token tuple: ng id} from ngrams.<lang>.txt; lines are '<id> <phrase>' ('#' comments).

    A line whose id does not match the formula of its phrase is skipped, so a damaged
    or edited list can never make the client send an id for other text. blocked: words
    (the shipped sensitive.<lang>.txt) that make an entry ineligible even if the list
    build let it through (spec 5.4, defence in depth).
    """
    blocked = set(w.lower() for w in (blocked or ()))
    index = {}
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(None, 1)
                if len(parts) != 2 or not _NG_ID.match(parts[0]) or not parts[0].startswith('ng-%s-' % lang):
                    continue
                ident, phrase = parts[0], parts[1].strip()
                if ng_id(lang, phrase) != ident:
                    continue
                key = phrase_key(lang, phrase)
                if key is not None and not any(t.lower() in blocked for t in key):
                    index[key] = ident
    except (OSError, UnicodeDecodeError):
        return {}
    return index


def _ngrams_in(toks, lo, hi, index, found):
    for i in range(lo, hi):
        for n in range(1, 5):
            j = i + n
            if j > hi:
                break
            gram = toks[i:j]
            if any(t is POISON for t in gram):
                break
            ident = index.get(tuple(gram))
            if ident:
                found.add(ident)


def tier2_rows(s_shown, s_final, ops, lang, index, blocklist=()):
    """[[ng id, deleted 0|1, kept 0|1]] for one session (spec 5.4 steps 4 to 6).

    Uses the sentence opcodes of the outcome computation. Deleted: n-grams entirely inside
    a token-level delete or replace span of a replace block (at most 300 tokens a side),
    or inside a deleted sentence. Kept: n-grams inside equal spans. Oversized blocks count
    for neither.
    """
    bl = set(w.lower() for w in blocklist)
    seen_a = lower_forms(s_shown) if lang == 'en' else None
    seen_b = lower_forms(s_final) if lang == 'en' else None
    deleted, kept = set(), set()
    for tag, i1, i2, j1, j2 in ops:
        a = []
        for i in range(i1, i2):
            if a:
                a.append(POISON)            # no n-gram crosses a sentence boundary
            a.extend(t2_tokens(s_shown[i], lang, bl, seen_a))
        if tag == 'insert':
            continue
        if tag == 'equal':
            _ngrams_in(a, 0, len(a), index, kept)
            continue
        if tag == 'delete':
            _ngrams_in(a, 0, len(a), index, deleted)
            continue
        b = []
        for j in range(j1, j2):
            if b:
                b.append(POISON)
            b.extend(t2_tokens(s_final[j], lang, bl, seen_b))
        if len(a) > BLOCK_TOKENS or len(b) > BLOCK_TOKENS:
            continue
        # POISON never equals another token, so it can not align (None == None would):
        a_keys = [('\x00', k) if t is POISON else t for k, t in enumerate(a)]
        b_keys = [('\x01', k) if t is POISON else t for k, t in enumerate(b)]
        for op, a1, a2, _b1, _b2 in difflib.SequenceMatcher(None, a_keys, b_keys, autojunk=False).get_opcodes():
            if op == 'equal':
                _ngrams_in(a, a1, a2, index, kept)
            elif op in ('delete', 'replace'):
                _ngrams_in(a, a1, a2, index, deleted)
    ids = sorted(deleted | kept)
    return [[i, 1 if i in deleted else 0, 1 if i in kept else 0] for i in ids][:2000]


def select_phrases(events):
    """Weekly Tier 2 selection (spec 5.4 step 7): eligible if deleted in 2 sessions on 2 days."""
    stats = {}
    for ev in events:
        if not isinstance(ev, dict) or ev.get('t') != 'out' or not isinstance(ev.get('ng'), list):
            continue
        day = ev.get('day') if isinstance(ev.get('day'), str) and _DATE.match(ev.get('day')) else None
        fg = ev.get('fg') if ev.get('fg') in FGS else 'none'
        for row in ev['ng']:
            if (not isinstance(row, list) or len(row) != 3 or not isinstance(row[0], str)
                    or not _NG_ID.match(row[0])):
                continue
            s = stats.setdefault(row[0], {'del_docs': 0, 'days': set(), 'kept_docs': 0, 'fgs': {}})
            if row[1] == 1:
                s['del_docs'] += 1
                if day:
                    s['days'].add(day)
                s['fgs'][fg] = s['fgs'].get(fg, 0) + 1
            if row[2] == 1:
                s['kept_docs'] += 1
    rows = []
    for ident, s in stats.items():
        if s['del_docs'] >= 2 and len(s['days']) >= 2:
            fg = sorted(s['fgs'].items(), key=lambda kv: (-kv[1], FGS.index(kv[0])))[0][0]
            rows.append((s['del_docs'], ident, fg, s['kept_docs']))
    rows.sort(key=lambda r: (-r[0], r[1]))
    return [{'ng': ident, 'fg': fg, 'del': min(d, 5), 'kept': min(k, 5)}
            for d, ident, fg, k in rows[:LIMITS['phrases']]]


# ----------------------------------------------------------------------------- aggregation (spec 5.5)

def _is_int(v):
    return type(v) is int


def _count_map(v):
    if not isinstance(v, dict):
        return {}
    return {k: c for k, c in v.items() if isinstance(k, str) and _RULE_ID.match(k) and _is_int(c) and c > 0}


def _round50(v):
    v = int(v)
    if v < 0:
        return 0
    return min(BOUNDS['words'], v - v % 50)


def _alloc(total_cap, parts):
    """Share a cap over parts proportionally (largest remainder); parts is [(key, value)]."""
    total = sum(v for _k, v in parts)
    if total <= total_cap:
        return dict(parts)
    raw = [(k, Fraction(v * total_cap, total)) for k, v in parts]
    out = {k: int(math.floor(q)) for k, q in raw}
    left = total_cap - sum(out.values())
    order = sorted(raw, key=lambda kv: (-(kv[1] - math.floor(kv[1])), str(kv[0])))
    for k, _q in order[:left]:
        out[k] += 1
    return out


def _estimate_final_words(base, er):
    """Words of the final text of one outcome, from its base counts and edit ratio.

    Every shown token is either matched or inside td, so matched M = ta - td, and
    er = 1 - 2M / (ta + tf) gives tf. The event format has no field for it (see the
    handoff to WP-H0); with er at 1 (nothing matched) the shown length stands in.
    """
    ta = base.get('ta', 0) if isinstance(base, dict) else 0
    td = base.get('td', 0) if isinstance(base, dict) else 0
    if not (_is_int(ta) and _is_int(td)) or ta < 0:
        return 0
    m = max(0, ta - max(0, td))
    if not isinstance(er, (int, float)) or isinstance(er, bool) or er >= 0.995 or m == 0:
        return ta
    tf = 2.0 * m / (1.0 - float(er)) - ta
    return int(max(0, min(MAX_TOKENS, round(tf))))


def aggregate(events, known_ids=None):
    """The shared body of report/2 and packet/1 from one week's events.

    known_ids: None (no filter) or {'fa': set, 'en': set} of ids the client may emit
    (built-in rule ids, lx- ids and the active overlay's ht- ids; spec 5.5 cells[].id),
    optionally with 'playbooks' (playbook anchors) and 'params' (parameter ids): rows
    whose id is not listed are left out, so the collector's registry check never fails.
    Returns {"volume", "cells", "placebo", "params", "playbooks", "health", "_counts"}.
    """
    known_pb = (known_ids or {}).get('playbooks')
    known_params = (known_ids or {}).get('params')
    hits = {}          # (lang, id, fg) -> n
    kept = {}
    ho = {}
    hg = {}
    words_shown = {}   # (lang, fg) -> n
    words_final = {}
    placebo = {}       # (lang, fg) -> [n, g]
    params = {}        # (pid, fg, b) -> [n, g]
    playbooks = {}     # (pb, lang) -> [n, first_pass, er_sum(Fraction), rev_sum, final_errors]
    health = dict((k, 0) for k in HEALTH_KINDS)
    health['cap_reject'] = {'violation': 0, 'gap': 0}
    health['verify_fail'] = {'fork': 0, 'mismatch': 0, 'local': 0}
    n_out = n_lint = 0

    def known(lang, ident):
        if not _RULE_ID.match(ident) or ident.startswith('ng-'):
            return False
        if ident[:3] in ('lx-', 'ht-') and ident[3:5] != lang:
            return False
        if lang == 'en' and not ident.startswith(('en-', 'lx-', 'ht-')):
            return False
        if lang == 'fa' and ident.startswith('en-'):
            return False
        return known_ids is None or ident in known_ids.get(lang, ())

    for ev in events:
        if not isinstance(ev, dict):
            continue
        t = ev.get('t')
        lang = ev.get('lang')
        fg = ev.get('fg') if ev.get('fg') in FGS else 'none'
        if t == 'lint' and lang in LANGS:
            n_lint += 1
            w = ev.get('w')
            if _is_int(w) and w > 0:
                words_shown[(lang, fg)] = words_shown.get((lang, fg), 0) + w
            for ident, c in _count_map(ev.get('hits')).items():
                if known(lang, ident):
                    hits[(lang, ident, fg)] = hits.get((lang, ident, fg), 0) + c
        elif t == 'out' and lang in LANGS:
            n_out += 1
            base = ev.get('base') if isinstance(ev.get('base'), dict) else {}
            words_final[(lang, fg)] = words_final.get((lang, fg), 0) + _estimate_final_words(base, ev.get('er'))
            cells = ev.get('cells') if isinstance(ev.get('cells'), dict) else {}
            for ident, c in cells.items():
                if not isinstance(c, dict) or not known(lang, ident):
                    continue
                if _is_int(c.get('kept')) and c['kept'] > 0:
                    kept[(lang, ident, fg)] = kept.get((lang, ident, fg), 0) + c['kept']
                if _is_int(c.get('ho')) and c['ho'] > 0:
                    g = c.get('hg') if _is_int(c.get('hg')) else 0
                    ho[(lang, ident, fg)] = ho.get((lang, ident, fg), 0) + c['ho']
                    hg[(lang, ident, fg)] = hg.get((lang, ident, fg), 0) + max(0, min(g, c['ho']))
            pl = ev.get('pl') if isinstance(ev.get('pl'), dict) else {}
            if _is_int(pl.get('n')) and pl['n'] > 0:
                slot = placebo.setdefault((lang, fg), [0, 0])
                slot[0] += pl['n']
                slot[1] += max(0, min(pl.get('g', 0) if _is_int(pl.get('g')) else 0, pl['n']))
            for pid, buckets in (ev.get('params') or {}).items() if isinstance(ev.get('params'), dict) else ():
                if not isinstance(pid, str) or not _PARAM_ID.match(pid) or not pid.startswith(lang + ':'):
                    continue
                if known_params is not None and pid not in known_params:
                    continue
                if not isinstance(buckets, dict):
                    continue
                for b, v in buckets.items():
                    if not (isinstance(b, str) and b.isdigit() and int(b) <= 1000 and isinstance(v, dict)):
                        continue
                    n, g = v.get('n'), v.get('g')
                    if not (_is_int(n) and n > 0):
                        continue
                    g = g if _is_int(g) else 0
                    slot = params.setdefault((pid, fg, int(b)), [0, 0])
                    slot[0] += n
                    slot[1] += max(0, min(g, n))
            pb = ev.get('pb')
            if isinstance(pb, str) and len(pb) <= 64 and _PLAYBOOK_ID.match(pb) and (
                    known_pb is None or pb in known_pb):
                slot = playbooks.setdefault((pb, lang), [0, 0, Fraction(0), 0, 0])
                if slot[0] < BOUNDS['playbook_n']:
                    rev = ev.get('rev') if _is_int(ev.get('rev')) else 0
                    er = ev.get('er')
                    er = Fraction(repr(float(er))) if isinstance(er, (int, float)) and not isinstance(er, bool) else Fraction(0)
                    er = min(max(er, Fraction(0)), Fraction(1))
                    fe = ev.get('fe') if _is_int(ev.get('fe')) else 0
                    slot[0] += 1
                    slot[1] += 1 if rev == 0 else 0
                    slot[2] += Fraction(math.floor(er * 100), 100)
                    slot[3] += max(0, min(rev, BOUNDS['revisions_per_n']))
                    slot[4] += max(0, min(fe, BOUNDS['final_errors_per_n']))
        elif t == 'health':
            k = ev.get('k')
            if k in HEALTH_REASONS:
                r = ev.get('r')
                if r in HEALTH_REASONS[k]:
                    health[k][r] += 1
            elif k in health:
                health[k] += 1

    # cells: per (lang, id) bounds summed over fg (spec 5.5)
    by_id = {}
    for key in set(hits) | set(kept) | set(ho):
        by_id.setdefault((key[0], key[1]), []).append(key[2])
    cells = []
    for (lang, ident), fgs in by_id.items():
        fgs = sorted(set(fgs), key=FGS.index)
        h = _alloc(BOUNDS['hits'], [(f, hits.get((lang, ident, f), 0)) for f in fgs])
        k = _alloc(BOUNDS['kept'], [(f, kept.get((lang, ident, f), 0)) for f in fgs])
        o = _alloc(BOUNDS['ho'], [(f, ho.get((lang, ident, f), 0)) for f in fgs])
        for f in fgs:
            o_orig = ho.get((lang, ident, f), 0)
            g_orig = hg.get((lang, ident, f), 0)
            g = 0
            if o_orig:
                g = min(o[f], int(math.floor(Fraction(g_orig * o[f], o_orig) + Fraction(1, 2))))
            row = {'id': ident, 'lang': lang, 'fg': f, 'hits': h[f], 'kept': k[f], 'ho': o[f], 'hg': g}
            if row['hits'] or row['kept'] or row['ho']:
                cells.append(row)
    cells.sort(key=lambda r: (LANGS.index(r['lang']), r['id'], FGS.index(r['fg'])))
    if len(cells) > LIMITS['cells']:
        ranked = sorted(cells, key=lambda r: (-r['ho'], -r['kept'], -r['hits'], r['lang'], r['id'], r['fg']))
        keep = set(id(r) for r in ranked[:LIMITS['cells']])
        cells = [r for r in cells if id(r) in keep]

    volume = []
    for lang in LANGS:
        for f in FGS:
            ws, wf = words_shown.get((lang, f), 0), words_final.get((lang, f), 0)
            if ws or wf:
                row = {'lang': lang, 'fg': f, 'words_shown': _round50(ws), 'words_final': _round50(wf)}
                if row['words_shown'] or row['words_final']:
                    volume.append(row)

    placebo_rows = []
    for lang in LANGS:
        for f in FGS:
            if (lang, f) not in placebo:
                continue
            n, g = placebo[(lang, f)]
            if n > BOUNDS['placebo_n']:
                g = int(math.floor(Fraction(g * BOUNDS['placebo_n'], n)))
                n = BOUNDS['placebo_n']
            placebo_rows.append({'lang': lang, 'fg': f, 'n': n, 'g': min(g, n)})

    param_rows = []
    by_param = {}
    for (pid, f, b), (n, g) in params.items():
        by_param.setdefault(pid, []).append(((f, b), n, g))
    for pid in sorted(by_param):
        parts = sorted(by_param[pid], key=lambda x: (FGS.index(x[0][0]), x[0][1]))
        share = _alloc(BOUNDS['param_n'], [(key, n) for key, n, _g in parts])
        for key, n, g in parts:
            n2 = share[key]
            if not n2:
                continue
            g2 = min(n2, int(math.floor(Fraction(g * n2, n) + Fraction(1, 2)))) if n else 0
            param_rows.append({'id': pid, 'fg': key[0], 'b': key[1], 'n': n2, 'g': g2})
    param_rows = param_rows[:LIMITS['params']]

    playbook_rows = []
    for (pb, lang) in sorted(playbooks, key=lambda k: (k[0], LANGS.index(k[1]))):
        n, fp, ers, rs, fe = playbooks[(pb, lang)]
        ers = min(ers, Fraction(n))
        playbook_rows.append({'id': pb, 'lang': lang, 'n': n, 'first_pass': fp,
                              'edit_ratio_sum': float(ers), 'revisions_sum': rs, 'final_errors': fe,
                              'explored': 0})
    playbook_rows = playbook_rows[:LIMITS['playbooks']]

    for k in HEALTH_KINDS:
        health[k] = min(health[k], BOUNDS['health'])
    for k, reasons in HEALTH_REASONS.items():
        for r in reasons:
            health[k][r] = min(health[k][r], BOUNDS['health'])
    ordered_health = {k: health[k] for k in ('selftest_ok', 'selftest_fail', 'overlay_exception', 'revert',
                                             'sync_ok', 'sync_fail', 'cap_reject', 'verify_fail')}
    return {'volume': volume, 'cells': cells, 'placebo': placebo_rows, 'params': param_rows,
            'playbooks': playbook_rows, 'health': ordered_health, '_counts': {'out': n_out, 'lint': n_lint}}


def big_enough(counts):
    """A week gives a report or packet only with >= 3 out events or >= 20 lint events."""
    return counts.get('out', 0) >= MIN_OUT_EVENTS or counts.get('lint', 0) >= MIN_LINT_EVENTS


def _base_rates(events):
    ta, td = {}, {}
    for ev in events:
        if isinstance(ev, dict) and ev.get('t') == 'out' and ev.get('lang') in LANGS:
            b = ev.get('base') if isinstance(ev.get('base'), dict) else {}
            if _is_int(b.get('ta')) and _is_int(b.get('td')):
                ta[ev['lang']] = ta.get(ev['lang'], 0) + max(0, b['ta'])
                td[ev['lang']] = td.get(ev['lang'], 0) + max(0, min(b['td'], b['ta']))
    out = {}
    for lang in LANGS:
        if lang in ta:
            a = _round50(ta[lang])
            out[lang] = {'ta': a, 'td': min(a, _round50(td[lang]))}
    return out


def _compact_size(doc):
    return len(json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


def _shrink_cells(doc, fits):
    """Drop the least informative cells until fits(doc) holds (reports are rarely this big)."""
    while not fits(doc) and doc['cells']:
        ranked = sorted(range(len(doc['cells'])), key=lambda i: (doc['cells'][i]['ho'], doc['cells'][i]['kept'],
                                                                 doc['cells'][i]['hits']))
        del doc['cells'][ranked[0]]
    return fits(doc)


def build_report(epoch, events, consent, client, secret, phrases=False, known_ids=None):
    """whalory.report/2 for one closed week (spec 5.5), or None when the week is too small.

    consent: {"version", "tiers"}; client: {"skill", "py", "overlay"}; secret: 32 bytes.
    With phrases (the Tier 2 opt-in and discovery open), adds `base` and `phrases`.
    """
    agg = aggregate(events, known_ids)
    if not big_enough(agg['_counts']):
        return None
    tiers = ['stats', 'phrases'] if phrases else ['stats']
    doc = {'schema': 'whalory.report/2', 'epoch': epoch,
           'consent': {'version': consent['version'], 'tiers': tiers},
           'del': deletion_hash(secret), 'client': client,
           'volume': agg['volume'], 'cells': agg['cells'], 'placebo': agg['placebo'],
           'params': agg['params'], 'playbooks': agg['playbooks'], 'health': agg['health']}
    if phrases:
        base = _base_rates(events)
        if base:
            doc['base'] = base
        doc['phrases'] = select_phrases(events)
    if not _shrink_cells(doc, lambda d: _compact_size(d) <= REPORT_MAX_BYTES):
        return None
    return doc


def build_packet(epoch, events, consent, client, known_ids=None):
    """whalory.packet/1 for one closed week (spec 17.3.2), or None when the week is too small."""
    agg = aggregate(events, known_ids)
    if not big_enough(agg['_counts']):
        return None
    return {'schema': 'whalory.packet/1', 'epoch': epoch,
            'consent': {'version': consent['version'], 'tiers': ['packets']},
            'client': client,
            'volume': agg['volume'], 'cells': agg['cells'], 'placebo': agg['placebo'],
            'params': agg['params'], 'playbooks': agg['playbooks'], 'health': agg['health']}


def _dump_row(v):
    return json.dumps(v, ensure_ascii=False, separators=(', ', ': '))


def render_packet(packet):
    """The fenced json block the person may post (spec 17.3.1): one array element per line.

    Byte for byte the form of contracts/samples/packet-1.comment.md. Returns None when the
    printed packet would exceed 60,000 characters (the caller then refuses and says so).
    """
    lines = ['{']
    keys = list(packet)
    for i, k in enumerate(keys):
        v = packet[k]
        end = ',' if i < len(keys) - 1 else ''
        if isinstance(v, list):
            if not v:
                lines.append(' %s: []%s' % (json.dumps(k), end))
                continue
            lines.append(' %s: [' % json.dumps(k))
            for j, row in enumerate(v):
                lines.append('  %s%s' % (_dump_row(row), ',' if j < len(v) - 1 else ''))
            lines.append(' ]%s' % end)
        else:
            lines.append(' %s: %s%s' % (json.dumps(k), _dump_row(v), end))
    lines.append('}')
    text = '```json\n' + '\n'.join(lines) + '\n```\n'
    if len(text) > PACKET_MAX_CHARS:
        return None
    return text


def fit_packet(packet):
    """(text, packet) within 60,000 characters: all-zero rows go first; None text if it still fails."""
    doc = dict(packet)
    for field, zero in (('cells', lambda r: not (r['hits'] or r['kept'] or r['ho'])),
                        ('placebo', lambda r: not r['n']), ('params', lambda r: not r['n']),
                        ('volume', lambda r: not (r['words_shown'] or r['words_final']))):
        doc[field] = [r for r in doc[field] if not zero(r)]
    text = render_packet(doc)
    return text, doc


# ----------------------------------------------------------------------------- events file helpers

def read_events(path, max_line=16 * 1024):
    """The parseable event lines of one events/<epoch>.jsonl file (bad lines are skipped)."""
    out = []
    try:
        with open(path, 'rb') as fh:
            for raw in fh:
                if len(raw) > max_line + 2:
                    continue
                try:
                    ev = json.loads(raw.decode('utf-8'), parse_constant=_no_constant)
                except (ValueError, UnicodeDecodeError):
                    continue
                if isinstance(ev, dict) and isinstance(ev.get('e'), str) and _EPOCH.match(ev['e']):
                    out.append(ev)
    except OSError:
        return []
    return out


def _no_constant(name):
    raise ValueError('non-finite number %s' % name)


def epoch_of(dt):
    """ISO 8601 week of a UTC datetime, 'YYYY-Www'."""
    y, w, _d = dt.isocalendar()[:3]
    return '%04d-W%02d' % (y, w)


def week_start(epoch):
    """Monday 00:00 UTC of an ISO week."""
    y, w = int(epoch[:4]), int(epoch[6:])
    jan4 = datetime.datetime(y, 1, 4, tzinfo=datetime.timezone.utc)
    monday = jan4 - datetime.timedelta(days=jan4.isoweekday() - 1)
    return monday + datetime.timedelta(weeks=w - 1)


def week_end(epoch):
    return week_start(epoch) + datetime.timedelta(days=7)


if __name__ == '__main__':
    sys.stdout.write(__doc__)
