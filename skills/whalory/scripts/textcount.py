#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""textcount: length counters for channel limits (Whalory 3.1.0).

Platforms count length in different units. This module has one counter per unit,
with no dependencies beyond the Python standard library (3.8+):

    char       code points (Python len)
    byte       UTF-8 bytes
    utf16      UTF-16 code units (TikTok Content Posting API)
    grapheme   extended grapheme clusters (Bluesky)
    weighted   X weighting: 1 or 2 per code point, every URL 23, every emoji 2
    segment    SMS segments: GSM-7 160/153, UCS-2 70/67
    word       whitespace-separated tokens
    items      non-empty items split on newlines or commas (tags, bullets)

Sources (checked 2026-09-27):
    Bluesky post.json lexicon, maxGraphemes 300:
        https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/app/bsky/feed/post.json
    X counting rules: https://docs.x.com/fundamentals/counting-characters
    twitter-text weights (ranges 0-4351, 8192-8205, 8208-8223, 8242-8247 weigh 1;
        default weight 2; URLs 23; emoji parsing on):
        https://raw.githubusercontent.com/twitter/twitter-text/master/config/v3.json
    SMS segments: https://www.twilio.com/docs/glossary/what-sms-character-limit
    TikTok caption in UTF-16 units:
        https://developers.tiktok.com/doc/content-posting-api-reference-direct-post

Usage:
    python textcount.py "text" [--unit grapheme]
    python textcount.py --file post.txt --json
"""
from __future__ import print_function

import sys

if sys.version_info < (3, 8):
    sys.stderr.write('textcount needs Python 3.8 or newer (found %s).\n' % sys.version.split()[0])
    sys.exit(2)

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts: a skill or plugin folder may be read-only

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import re  # noqa: E402
import unicodedata  # noqa: E402

__version__ = '3.2.0-rc.2'

UNITS = ('char', 'byte', 'utf16', 'grapheme', 'weighted', 'segment', 'word', 'items')

# ---------------------------------------------------------------- simple units


def chars(text):
    """Code points."""
    return len(text or '')


def utf8_bytes(text):
    return len((text or '').encode('utf-8'))


def utf16_units(text):
    return len((text or '').encode('utf-16-le')) // 2


def word_count(text):
    return len((text or '').split())


def split_items(text):
    """Non-empty items split on newlines or commas (Latin, Persian or ideographic)."""
    return [x.strip() for x in re.split(r'[\n,،，、]+', text or '') if x.strip()]


_HASHTAG = re.compile(r'(?<![\w#])#[^\s#.,!?;:()\[\]{}"\'،؛؟]+')


def hashtags(text):
    """'#tag' tokens, in order."""
    return _HASHTAG.findall(text or '')


# ---------------------------------------------------------------- graphemes
# A dependency-free subset of UAX #29 extended grapheme clusters: CR LF, controls,
# Extend (combining marks, ZWNJ, variation selectors, emoji modifiers, tag characters),
# SpacingMark, ZWJ emoji sequences and regional-indicator pairs. Hangul jamo sequences
# and Indic conjuncts are not joined (precomposed Hangul is one code point anyway).

_PICTO_RANGES = (
    (0x00A9, 0x00A9), (0x00AE, 0x00AE), (0x203C, 0x203C), (0x2049, 0x2049), (0x2122, 0x2122),
    (0x2139, 0x2139), (0x2194, 0x2199), (0x21A9, 0x21AA), (0x231A, 0x231B), (0x2328, 0x2328),
    (0x2388, 0x2388), (0x23CF, 0x23CF), (0x23E9, 0x23F3), (0x23F8, 0x23FA), (0x24C2, 0x24C2),
    (0x25AA, 0x25AB), (0x25B6, 0x25B6), (0x25C0, 0x25C0), (0x25FB, 0x25FE), (0x2600, 0x27BF),
    (0x2934, 0x2935), (0x2B05, 0x2B07), (0x2B1B, 0x2B1C), (0x2B50, 0x2B50), (0x2B55, 0x2B55),
    (0x3030, 0x3030), (0x303D, 0x303D), (0x3297, 0x3297), (0x3299, 0x3299),
    (0x1F000, 0x1F0FF), (0x1F10D, 0x1F10F), (0x1F12F, 0x1F12F), (0x1F16C, 0x1F171),
    (0x1F17E, 0x1F17F), (0x1F18E, 0x1F18E), (0x1F191, 0x1F19A), (0x1F1AD, 0x1F1E5),
    (0x1F201, 0x1F20F), (0x1F21A, 0x1F21A), (0x1F22F, 0x1F22F), (0x1F232, 0x1F23A),
    (0x1F23C, 0x1F23F), (0x1F249, 0x1F3FA), (0x1F400, 0x1F53D), (0x1F546, 0x1F64F),
    (0x1F680, 0x1F6FF), (0x1F774, 0x1F77F), (0x1F7D5, 0x1F7FF), (0x1F80C, 0x1F80F),
    (0x1F848, 0x1F84F), (0x1F85A, 0x1F85F), (0x1F888, 0x1F88F), (0x1F8AE, 0x1F8FF),
    (0x1F90C, 0x1F93A), (0x1F93C, 0x1F945), (0x1F947, 0x1FAFF), (0x1FC00, 0x1FFFD),
)


def _is_picto(cp):
    for a, b in _PICTO_RANGES:
        if cp < a:
            return False
        if cp <= b:
            return True
    return False


def _gcb(ch):
    """Grapheme_Cluster_Break class (subset)."""
    cp = ord(ch)
    if ch == '\r':
        return 'CR'
    if ch == '\n':
        return 'LF'
    if cp == 0x200D:
        return 'ZWJ'
    if cp == 0x200C or 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF \
            or 0x1F3FB <= cp <= 0x1F3FF or 0xE0020 <= cp <= 0xE007F:
        return 'Extend'
    if 0x1F1E6 <= cp <= 0x1F1FF:
        return 'RI'
    cat = unicodedata.category(ch)
    if cat in ('Mn', 'Me'):
        return 'Extend'
    if cat == 'Mc':
        return 'SpacingMark'
    if cat in ('Cc', 'Zl', 'Zp') or (cat == 'Cf' and cp not in (0x0600, 0x0601, 0x0602, 0x0603,
                                                                  0x0604, 0x0605, 0x06DD, 0x070F,
                                                                  0x08E2, 0x110BD)):
        return 'Control'
    if _is_picto(cp):
        return 'ExtPict'
    return 'Other'


def graphemes(text):
    """Extended grapheme clusters (list of strings)."""
    out = []
    if not text:
        return out
    cur = text[0]
    prev = _gcb(text[0])
    ri_run = 1 if prev == 'RI' else 0
    pict_seq = prev == 'ExtPict'          # ExtPict Extend* (for GB11)
    for ch in text[1:]:
        c = _gcb(ch)
        brk = True
        if prev == 'CR' and c == 'LF':
            brk = False
        elif prev in ('CR', 'LF', 'Control') or c in ('CR', 'LF', 'Control'):
            brk = True
        elif c in ('Extend', 'ZWJ', 'SpacingMark'):
            brk = False
        elif prev == 'ZWJ' and c == 'ExtPict' and pict_seq:
            brk = False
        elif prev == 'RI' and c == 'RI' and ri_run % 2 == 1:
            brk = False
        if brk:
            out.append(cur)
            cur = ch
            pict_seq = c == 'ExtPict'
            ri_run = 1 if c == 'RI' else 0
        else:
            cur += ch
            if c == 'RI':
                ri_run += 1
            if c == 'ExtPict':
                pict_seq = True
            elif c not in ('Extend', 'ZWJ'):
                pict_seq = False
        prev = c
    out.append(cur)
    return out


def grapheme_count(text):
    return len(graphemes(text))


# ---------------------------------------------------------------- X weighting
_X_RANGES = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))
# A bare domain starts only where a host name can start (not inside "a.b.c" or "a-b-c"), so the
# search stays linear on long runs of labels.
_X_URL = re.compile(r'(?:https?://|www\.)[^\s<>"\']+'
                    r'|(?<![\w.-])[A-Za-z0-9][A-Za-z0-9-]*(?:\.[A-Za-z0-9-]+)*'
                    r'\.(?:com|org|net|io|co|ai|app|dev|me|info|biz|edu|gov|uk|us|ca|de|ir)\b(?:/[^\s<>"\']*)?',
                    re.I)
_X_URL_LEN = 23


def _x_weight(cp):
    for a, b in _X_RANGES:
        if a <= cp <= b:
            return 1
    return 2


def _is_emoji_cluster(g):
    cps = [ord(c) for c in g]
    if any(_is_picto(cp) for cp in cps) and (len(cps) > 1 or cps[0] >= 0x1F000 or 0xFE0F in cps):
        return True
    if len(cps) == 2 and all(0x1F1E6 <= cp <= 0x1F1FF for cp in cps):
        return True
    return len(cps) >= 2 and cps[-1] == 0x20E3            # keycap 1️⃣


def weighted_length(text):
    """X post length: NFC text; URLs count 23; an emoji (even a ZWJ sequence) counts 2;
    every other code point weighs 1 inside the twitter-text ranges and 2 outside."""
    t = unicodedata.normalize('NFC', text or '')
    total, pos = 0, 0
    for m in _X_URL.finditer(t):
        total += _plain_weight(t[pos:m.start()]) + _X_URL_LEN
        pos = m.end()
    return total + _plain_weight(t[pos:])


def _plain_weight(s):
    n = 0
    for g in graphemes(s):
        if _is_emoji_cluster(g):
            n += 2
        else:
            n += sum(_x_weight(ord(c)) for c in g)
    return n


# ---------------------------------------------------------------- SMS
_GSM7 = set('@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !"#¤%&\'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            'ÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà')
_GSM7_EXT = set('^{}\\[~]|€\f')


def sms_segments(text):
    """(segments, units, single-part limit, per-part limit, encoding). Same tuple as
    lint_fa.sms_segments: GSM-7 160/153 (extension characters count 2), UCS-2 70/67."""
    text = text or ''
    if all(c in _GSM7 or c in _GSM7_EXT for c in text):
        units = sum(2 if c in _GSM7_EXT else 1 for c in text)
        single, part, enc = 160, 153, 'gsm7'
    else:
        units = utf16_units(text)
        single, part, enc = 70, 67, 'ucs2'
    if units == 0:
        segs = 0
    elif units <= single:
        segs = 1
    else:
        segs = int(math.ceil(units / float(part)))
    return segs, units, single, part, enc


# ---------------------------------------------------------------- dispatcher


def count(text, unit='char'):
    """Length of text in a channel unit. An unknown unit falls back to 'char'.
    'segment' returns the number of SMS segments."""
    unit = (unit or 'char').lower()
    if unit == 'byte':
        return utf8_bytes(text)
    if unit == 'utf16':
        return utf16_units(text)
    if unit == 'grapheme':
        return grapheme_count(text)
    if unit == 'weighted':
        return weighted_length(text)
    if unit == 'segment':
        return sms_segments(text)[0]
    if unit == 'word':
        return word_count(text)
    if unit == 'items':
        return len(split_items(text))
    return chars(text)


def report(text):
    """Every unit at once (for the CLI and for tools)."""
    segs, units, single, part, enc = sms_segments(text)
    return {'char': chars(text), 'byte': utf8_bytes(text), 'utf16': utf16_units(text),
            'grapheme': grapheme_count(text), 'weighted': weighted_length(text),
            'segment': segs, 'sms_units': units, 'sms_encoding': enc, 'word': word_count(text),
            'items': len(split_items(text)), 'hashtags': len(hashtags(text))}


def run(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8')
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog='textcount', description='Count text length in channel units.')
    ap.add_argument('text', nargs='?', help='text to count (or use --file, or - for stdin)')
    ap.add_argument('--file', help='read the text from a UTF-8 file')
    ap.add_argument('--unit', choices=UNITS, help='print one unit only')
    ap.add_argument('--json', action='store_true', help='JSON output')
    ap.add_argument('--version', action='version', version='textcount %s' % __version__)
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0)
    try:
        if a.file:
            with open(a.file, 'rb') as fh:
                text = fh.read().decode('utf-8-sig')
        elif a.text == '-' or a.text is None:
            data = sys.stdin.buffer.read() if hasattr(sys.stdin, 'buffer') else sys.stdin.read().encode('utf-8')
            text = data.decode('utf-8-sig')
        else:
            text = a.text
    except (OSError, UnicodeDecodeError) as e:
        sys.stderr.write('textcount: cannot read the input: %s\n' % e)
        return 2
    text = text.replace('\r\n', '\n').strip()
    if a.unit:
        n = count(text, a.unit)
        print(json.dumps({a.unit: n}) if a.json else n)
        return 0
    r = report(text)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        for k in ('char', 'byte', 'utf16', 'grapheme', 'weighted', 'word', 'items', 'hashtags'):
            print('%-9s %d' % (k, r[k]))
        print('%-9s %d (%d units, %s)' % ('segment', r['segment'], r['sms_units'], r['sms_encoding']))
    return 0


if __name__ == '__main__':
    sys.exit(run())
