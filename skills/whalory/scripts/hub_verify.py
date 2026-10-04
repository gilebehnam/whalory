#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hub_verify: verification of Whalory Hub rule updates (spec 5.8, 7.2 to 7.8).

Standard library only, Python 3.8 to 3.14. It reads bytes and returns verified documents:
it opens no socket, writes no file and starts no process. hub_client does the fetching
and the writing; hub_overlay re-verifies what hub_client stored every time a process
first applies it.

Parts
  * Hardened JSON (spec 7.5): loads() refuses NaN and Infinity, duplicate keys, numbers
    with more than 15 significant digits, nesting deeper than 6, a byte order mark,
    invalid UTF-8, lone surrogates and anything over a byte cap.
  * Ed25519 verification (spec 7.8, RFC 8032 section 5.1.7): verify(public_key, message,
    signature) never raises; keys must be canonical and not of small order, 0 <= S < L,
    and the check is cofactorless with a byte-for-byte comparison of R. A port of
    hub/research/security/ed25519_verify.py with the same semantics.
  * DSSE envelopes (spec 7.2): pae(), verify_threshold(), verify_envelope().
  * The schemas and semantic checks of the Hub contracts for the signed metadata
    (root, timestamp, baseline, auto, halt), the envelope and whalory.overlay/1:
    validate_doc(), evaluate_document(). The schema table below is generated from
    STUDIO/hub/contracts; tests_hub/test_verify.py fails when the two drift apart.
  * The metadata chain of spec 5.8: root rotation, halt rules, the timestamp and its
    prev_sha256 chain, targets metadata, revoked releases, stale metadata, the choice of
    overlays, and target downloads: sync() for one run, load_snapshot() for a stored or
    bundled set.

Local layout (the contract with hub_client, which writes these files):

    <hub>/trusted/root/<N>.json       every root accepted after the pinned one, as served
    <hub>/trusted/timestamp.json      the verified timestamp, as served (also baseline.json,
    <hub>/trusted/baseline.json       auto.json and halt.json; halt.json only when one was
    <hub>/trusted/auto.json           accepted)
    <hub>/targets/<sha256>.json       verified overlay targets
    <hub>/state.json                  key "rules": see RULES_STATE below

The bundled set of a release (SKILL/data/hub/bundled/) and a mirror use the mirror layout
of spec 8.2 (root/<N>.json, timestamp.json, baseline.json, auto.json, halt.json,
targets/<sha256>.json). reader() makes a read function for either layout.

RULES_STATE, the "rules" object of state.json (hub_client stores sync()'s result.rules):
    {"versions": {"root": N, "timestamp": N, "baseline": N, "auto": N, "halt": N},
     "last_issued": "<UTC time>", "revoked": [auto ids], "first_seen": {release: time},
     "percent": {release: highest honoured percent},
     "activations": [{"release", "at", "rules", "phrase_demotions", "changed"}]}
Every key is optional; a missing key means nothing seen yet.

Every public function either returns a result or raises HubError with a short stable code;
verify() and the predicates never raise.
"""
from __future__ import print_function

import base64
import binascii
import datetime
import hashlib
import json
import math
import os
import re
import unicodedata

__all__ = [
    'HubError', 'loads', 'MAX_BYTES', 'verify', 'public_key_ok', 'keyid_of', 'PAYLOAD_TYPES', 'pae',
    'verify_threshold', 'verify_envelope', 'validate_doc', 'evaluate_document', 'open_signed',
    'parse_pinned_root', 'update_root', 'root_changes', 'check_timestamp', 'check_halt', 'halt_in_force',
    'check_targets_meta', 'check_target', 'load_snapshot', 'reader', 'sync', 'SyncResult', 'Snapshot',
    'canary_bucket', 'effective_percent', 'compat_ok', 'phrase_id', 'ht_id', 'lx_id',
    'phrase_literal_problem', 'glob_match', 'is_locked', 'parse_time', 'fmt_time', 'iso_week_valid',
    'b64url', 'b64url_decode', 'b64std_decode', 'sha256_hex', 'timestamps_disagree',
]

UTC = datetime.timezone.utc

# ----------------------------------------------------------------------------- errors


class HubError(Exception):
    """A document or a chain step failed; code is a short stable token, path points into the document."""

    def __init__(self, code, detail='', path=''):
        Exception.__init__(self, '%s%s%s' % (code, (' at ' + path) if path else '', (': ' + detail) if detail else ''))
        self.code = code
        self.detail = detail
        self.path = path


# ----------------------------------------------------------------------------- hardened JSON (spec 7.5)

MAX_DEPTH = 6
MAX_NUMBER_DIGITS = 15

#: Byte caps (spec 5.6, 7.5); envelopes are capped per role.
MAX_BYTES = {
    'overlay-1': 256 * 1024,
    'envelope.root': 64 * 1024,
    'envelope.timestamp': 16 * 1024,
    'envelope.halt': 8 * 1024,
    'envelope.baseline': 256 * 1024,
    'envelope.auto': 256 * 1024,
    'envelope.admin': 8 * 1024,
    'active': 16 * 1024,
}
DEFAULT_MAX_BYTES = 1024 * 1024

_TOKENS = re.compile(r'"(?:[^"\\]|\\.)*"|[\[\]{}]', re.S)
_SURROGATE = re.compile('[\ud800-\udfff]')
_EXP = re.compile('[eE]')


def _depth_prescan(text, max_depth):
    depth = 0
    for m in _TOKENS.finditer(text):
        c = m.group(0)
        if c in '{[':
            depth += 1
            if depth > max_depth:
                raise HubError('depth', 'nesting deeper than %d' % max_depth)
        elif c in '}]':
            depth -= 1


def _bad_constant(name):
    raise HubError('non_finite', name)


def _parse_int(s):
    if len(s.lstrip('-')) > MAX_NUMBER_DIGITS:
        raise HubError('long_number', '%d digits' % len(s.lstrip('-')))
    return int(s)


def _parse_float(s):
    mantissa = _EXP.split(s.lstrip('-'))[0].replace('.', '').lstrip('0')
    if len(mantissa) > MAX_NUMBER_DIGITS:
        raise HubError('long_number', '%d significant digits' % len(mantissa))
    v = float(s)
    if not math.isfinite(v):
        raise HubError('non_finite', s[:20])
    return v


def _pairs(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise HubError('duplicate_key', k[:40])
        d[k] = v
    return d


def _check_strings(obj):
    if isinstance(obj, str):
        if _SURROGATE.search(obj):
            raise HubError('surrogate', 'lone surrogate in a string')
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if _SURROGATE.search(k):
                raise HubError('surrogate', 'lone surrogate in a key')
            _check_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            _check_strings(v)


def loads(data, max_bytes=None, max_depth=MAX_DEPTH, top='object'):
    """Parse Hub JSON the hardened way; data is bytes.

    Raises HubError with code too_large, bom, utf8, depth, syntax, non_finite,
    long_number, duplicate_key, surrogate or top_level (the codes of the contracts).
    """
    if not isinstance(data, (bytes, bytearray)):
        raise HubError('syntax', 'not bytes')
    if max_bytes is not None and len(data) > max_bytes:
        raise HubError('too_large', '%d > %d bytes' % (len(data), max_bytes))
    if data[:3] == b'\xef\xbb\xbf':
        raise HubError('bom')
    try:
        text = bytes(data).decode('utf-8')
    except UnicodeDecodeError:
        raise HubError('utf8')
    _depth_prescan(text, max_depth)
    try:
        obj = json.loads(text, parse_constant=_bad_constant, parse_int=_parse_int,
                         parse_float=_parse_float, object_pairs_hook=_pairs)
    except HubError:
        raise
    except (ValueError, RecursionError) as e:
        raise HubError('syntax', str(e)[:80])
    if top == 'object' and not isinstance(obj, dict):
        raise HubError('top_level', 'the document must be a JSON object')
    _check_strings(obj)
    return obj


def dumps_compact(obj):
    """Compact UTF-8 bytes, the form of every signed payload and target."""
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def is_number(v):
    """Spec 7.5: an int, or a finite float; bool is never a number."""
    return type(v) is int or (type(v) is float and math.isfinite(v))


# ----------------------------------------------------------------------------- small helpers


def sha256_hex(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def b64url(data):
    return base64.urlsafe_b64encode(bytes(data)).rstrip(b'=').decode('ascii')


def b64url_decode(s):
    """Strict unpadded base64url; raises ValueError on any other spelling."""
    if not isinstance(s, str) or len(s) % 4 == 1:
        raise ValueError('not unpadded base64url')
    for ch in s:
        if not (ch.isascii() and (ch.isalnum() or ch in '-_')):
            raise ValueError('not unpadded base64url')
    raw = base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))
    if b64url(raw) != s:
        raise ValueError('non-canonical base64url')
    return raw


def b64std_decode(s):
    """Strict padded standard base64; raises ValueError on any other spelling."""
    if not isinstance(s, str):
        raise ValueError('not standard base64')
    try:
        raw = base64.b64decode(s, validate=True)
    except (binascii.Error, ValueError, TypeError):
        raise ValueError('not standard base64')
    if base64.b64encode(raw).decode('ascii') != s:
        raise ValueError('non-canonical base64')
    return raw


def parse_time(s):
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=UTC)


def fmt_time(dt):
    return dt.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')


def _now(now=None):
    if now is None:
        return datetime.datetime.now(UTC).replace(microsecond=0)
    if isinstance(now, str):
        return parse_time(now)
    return now if now.tzinfo else now.replace(tzinfo=UTC)


def time_valid(s):
    try:
        parse_time(s)
        return True
    except (ValueError, TypeError):
        return False


def date_valid(s):
    try:
        datetime.datetime.strptime(s, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False


def iso_week_valid(epoch):
    """True if YYYY-Www names a week that exists (W53 only in long years)."""
    try:
        datetime.date.fromisocalendar(int(epoch[:4]), int(epoch[6:]), 1)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def baseline_id_valid(i):
    return re.fullmatch(r'b-([0-9]{4})\.(0[1-9]|1[0-2])\.[1-9][0-9]{0,2}', i or '') is not None


def auto_id_valid(i):
    m = re.fullmatch(r'a-([0-9]{4})w([0-9]{2})\.[1-9][0-9]{0,2}', i or '')
    return m is not None and iso_week_valid('%s-W%s' % (m.group(1), m.group(2)))


def id_lang(ident):
    """Language of a rule or phrase id: en- rules and -en- phrase ids are English."""
    m = re.match(r'(lx|ht|ng)-(fa|en)-', ident)
    if m:
        return m.group(2)
    return 'en' if ident.startswith('en-') else 'fa'


def phrase_id(prefix, lang, category, phrase):
    """prefix-<lang>-<first 10 hex of SHA-256(lang|category|NFC(phrase))> (spec 5.4, 5.5)."""
    text = unicodedata.normalize('NFC', phrase)
    digest = hashlib.sha256((lang + '|' + category + '|' + text).encode('utf-8')).hexdigest()
    return '%s-%s-%s' % (prefix, lang, digest[:10])


def lx_id(lang, category, phrase):
    return phrase_id('lx', lang, category, phrase)


def ht_id(lang, phrase):
    return phrase_id('ht', lang, 'hub', phrase)


PHRASE_ID_RE = re.compile(r'(lx|ht)-(fa|en)-[0-9a-f]{10}')
_FA_PHRASE_LETTERS = set()
for _a, _b in ((0x0621, 0x063A), (0x0641, 0x0642), (0x0644, 0x0648)):
    _FA_PHRASE_LETTERS.update(chr(c) for c in range(_a, _b + 1))
_FA_PHRASE_LETTERS.update(chr(c) for c in (0x067E, 0x0686, 0x0698, 0x06A9, 0x06AF, 0x06CC, 0x06C0))
_LATIN = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
_LETTERS = _FA_PHRASE_LETTERS | _LATIN
ZWNJ = '‌'


def phrase_literal_problem(lang, phrase):
    """None if phrase passes the literal rules of spec 7.5, else a reason code.

    2 to 40 characters, 1 to 4 words separated by single spaces, Persian letters of the
    allowed set, Latin letters, ZWNJ inside a word and (English only) ' or U+2019 inside
    a word. The Arabic forms U+0643, U+0649 and U+064A are refused.
    """
    if not isinstance(phrase, str):
        return 'phrase_type'
    if unicodedata.normalize('NFC', phrase) != phrase:
        return 'phrase_not_nfc'
    if not (2 <= len(phrase) <= 40):
        return 'phrase_length'
    words = phrase.split(' ')
    if not (1 <= len(words) <= 4) or any(w == '' for w in words):
        return 'phrase_words'
    for w in words:
        for i, ch in enumerate(w):
            if ch in _LETTERS:
                continue
            joiner = ch == ZWNJ or (lang == 'en' and ch in "'’")
            if joiner and 0 < i < len(w) - 1 and w[i - 1] in _LETTERS and w[i + 1] in _LETTERS:
                continue
            return 'phrase_char'
    return None


def glob_match(pattern, ident):
    """policy.locked globs: '*' is any run of [a-z0-9-]; nothing else is special."""
    rx = '[a-z0-9-]*'.join(re.escape(p) for p in pattern.split('*'))
    return re.fullmatch(rx, ident) is not None


def is_locked(ident, locked):
    return any(glob_match(p, ident) for p in locked)


def _glob_path(pattern, path):
    """Role paths such as 'auto/*': '*' is any run without '/'."""
    return re.fullmatch('[^/]*'.join(re.escape(p) for p in pattern.split('*')), path) is not None


def _semver(v):
    return tuple(int(x) for x in v.split('.'))


def compat_ok(rng, version):
    """True if version (X.Y.Z, or X.Y) is inside a compat.skill range '>=A.B.C' or '>=A.B.C <D.E.F'."""
    try:
        parts = str(version).split('.')
        v = tuple(int(x) for x in (parts + ['0', '0'])[:3])
        bits = rng.split(' ')
        if not bits[0].startswith('>=') or v < _semver(bits[0][2:]):
            return False
        if len(bits) == 2:
            return bits[1].startswith('<') and v < _semver(bits[1][1:])
        return len(bits) == 1
    except (ValueError, AttributeError, TypeError):
        return False


def timestamps_disagree(a, b):
    """True when two mirrors serve different timestamp bytes for the same version (split view, spec 5.8)."""
    try:
        da = loads(b64std_decode(loads(a)['payload']))
        db = loads(b64std_decode(loads(b)['payload']))
        return da.get('version') == db.get('version') and bytes(a) != bytes(b)
    except (HubError, ValueError, KeyError, TypeError):
        return False


# ----------------------------------------------------------------------------- Ed25519 (spec 7.8)

P = 2 ** 255 - 19
L = 2 ** 252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
D2 = 2 * D % P
SQRT_M1 = pow(2, (P - 1) // 4, P)
IDENT = (0, 1, 1, 0)


def _inv(x):
    return pow(x, P - 2, P)


def _add(p1, p2):
    x1, y1, z1, t1 = p1
    x2, y2, z2, t2 = p2
    a = (y1 - x1) * (y2 - x2) % P
    b = (y1 + x1) * (y2 + x2) % P
    c = t1 * D2 % P * t2 % P
    d = 2 * z1 * z2 % P
    e, f, g, h = b - a, d - c, d + c, b + a
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _double(p1):
    x1, y1, z1, _ = p1
    a = x1 * x1 % P
    b = y1 * y1 % P
    c = 2 * z1 * z1 % P
    h = a + b
    e = h - (x1 + y1) * (x1 + y1)
    g = a - b
    f = c + g
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _neg(p1):
    x, y, z, t = p1
    return ((-x) % P, y, z, (-t) % P)


def _recover_x(y, sign):
    if y >= P:
        return None
    x2 = (y * y - 1) * _inv(D * y * y + 1) % P
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P != 0:
        x = x * SQRT_M1 % P
    if (x * x - x2) % P != 0:
        return None
    if (x & 1) != sign:
        x = P - x
    return x


def _decode_point(s):
    if len(s) != 32:
        return None
    y = int.from_bytes(s, 'little')
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % P)


def _encode_point(p1):
    x, y, z, _ = p1
    zi = _inv(z)
    x = x * zi % P
    y = y * zi % P
    return (y | ((x & 1) << 255)).to_bytes(32, 'little')


def _is_identity(p1):
    x, y, z, _ = p1
    return x % P == 0 and (y - z) % P == 0


_GY = 4 * _inv(5) % P
_GX = _recover_x(_GY, 0)
BASE = (_GX, _GY, 1, _GX * _GY % P)


def _double_scalar_mul(s, pb, k, pa):
    """[s]pb + [k]pa with one joint double-and-add (all inputs are public)."""
    table = (IDENT, pb, pa, _add(pb, pa))
    acc = IDENT
    for i in range(max(s.bit_length(), k.bit_length()) - 1, -1, -1):
        acc = _double(acc)
        idx = ((s >> i) & 1) | (((k >> i) & 1) << 1)
        if idx:
            acc = _add(acc, table[idx])
    return acc


def _small_order(pt):
    t = pt
    for _ in range(3):
        t = _double(t)
    return _is_identity(t)


_KEY_OK = {}


def public_key_ok(public_key):
    """True for the canonical encoding of an Ed25519 point that is not of small order; never raises."""
    try:
        public_key = bytes(public_key)
    except (TypeError, ValueError):
        return False
    got = _KEY_OK.get(public_key)
    if got is None:
        pt = _decode_point(public_key) if len(public_key) == 32 else None
        got = pt is not None and not _small_order(pt)
        if len(_KEY_OK) < 256:
            _KEY_OK[public_key] = got
    return got


def verify(public_key, message, signature):
    """True iff signature is a valid Ed25519 signature of message under public_key; never raises.

    Public key exactly 32 bytes, canonical (y < p; x = 0 with the sign bit refused), not of
    small order; signature exactly 64 bytes; 0 <= S < L; cofactorless check comparing the
    canonical encoding of [S]B - [k]A with R byte for byte (RFC 8032 section 5.1.7).
    """
    try:
        public_key = bytes(public_key)
        signature = bytes(signature)
        message = bytes(message)
    except (TypeError, ValueError):
        return False
    if len(public_key) != 32 or len(signature) != 64:
        return False
    a_pt = _decode_point(public_key)
    if a_pt is None or _small_order(a_pt):
        return False
    r_bytes = signature[:32]
    s = int.from_bytes(signature[32:], 'little')
    if s >= L:
        return False
    k = int.from_bytes(hashlib.sha512(r_bytes + public_key + message).digest(), 'little') % L
    return _encode_point(_double_scalar_mul(s, BASE, k, _neg(a_pt))) == r_bytes


def keyid_of(public_key):
    """Spec 7.2: the first 16 lower-case hex characters of SHA-256(raw 32-byte public key)."""
    return hashlib.sha256(bytes(public_key)).hexdigest()[:16]


# ----------------------------------------------------------------------------- DSSE (spec 7.2)

PAYLOAD_TYPES = {
    'root': 'application/vnd.whalory.hub.root+json',
    'timestamp': 'application/vnd.whalory.hub.timestamp+json',
    'baseline': 'application/vnd.whalory.hub.baseline+json',
    'auto': 'application/vnd.whalory.hub.auto+json',
    'halt': 'application/vnd.whalory.hub.halt+json',
    'admin': 'application/vnd.whalory.hub.admin+json',
}
ROLE_OF_TYPE = dict((v, k) for k, v in PAYLOAD_TYPES.items())


def pae(payload_type, body):
    """DSSE v1 pre-authentication encoding over the exact payload bytes."""
    t = payload_type.encode('utf-8')
    body = bytes(body)
    return b'DSSEv1 %d %s %d %s' % (len(t), t, len(body), body)


def verify_threshold(trusted_keys, threshold, signed_bytes, signatures):
    """TUF-style threshold check over already decoded signatures [{"keyid", "sig": bytes}].

    A key counts once however often it signed, unknown key ids are skipped without
    verification, and at most len(trusted_keys) signatures are verified. Never raises.
    """
    try:
        if threshold < 1:
            return False
        good, checked = set(), 0
        for entry in signatures:
            try:
                kid, sig = entry['keyid'], entry['sig']
            except (KeyError, TypeError):
                continue
            if kid in good or kid not in trusted_keys:
                continue
            if checked >= len(trusted_keys):
                break
            checked += 1
            if verify(trusted_keys[kid], signed_bytes, sig):
                good.add(kid)
                if len(good) >= threshold:
                    return True
        return len(good) >= threshold
    except Exception:
        return False


def verify_envelope(envelope, trusted_keys, threshold, expected_type, max_bytes=None):
    """Verify a DSSE envelope; return the payload bytes, parsed by the caller only afterwards.

    envelope is the served bytes (parsed hardened and checked against the envelope schema)
    or an already parsed dict. trusted_keys maps keyid -> 32-byte public key of the role.
    Raises HubError: envelope (not a valid envelope), payload_type, payload_base64,
    too_large (payload over max_bytes) or threshold.
    """
    if isinstance(envelope, (bytes, bytearray)):
        env = loads(envelope, max_bytes=max_bytes)
        errs = SCHEMAS.validate(env, 'envelope')
        if errs:
            raise HubError('envelope', errs[0][1], errs[0][0])
    else:
        env = envelope
    if not isinstance(env, dict) or env.get('payloadType') != expected_type:
        raise HubError('payload_type', str(env.get('payloadType') if isinstance(env, dict) else '')[:80])
    try:
        body = b64std_decode(env['payload'])
    except (ValueError, KeyError, TypeError):
        raise HubError('payload_base64')
    if max_bytes is not None and len(body) > max_bytes:
        raise HubError('too_large', 'payload over %d bytes' % max_bytes)
    sigs = []
    for s in env.get('signatures', ()) if isinstance(env.get('signatures'), list) else ():
        if not isinstance(s, dict):
            continue
        try:
            sigs.append({'keyid': s.get('keyid'), 'sig': b64std_decode(s.get('sig'))})
        except ValueError:
            sigs.append({'keyid': s.get('keyid'), 'sig': b''})
    if not verify_threshold(trusted_keys, threshold, pae(expected_type, body), sigs):
        raise HubError('threshold', 'fewer than %d valid signatures' % threshold)
    return body


# ----------------------------------------------------------------------------- schemas (generated)

# Generated from STUDIO/hub/contracts/schemas by tools/bundle_schema.py, annotations removed, the
# shared definitions of common.schema.json kept once under "common". Do not edit by hand:
# tests_hub/test_verify.py compares it with the contracts and prints a fresh copy on request.
_SCHEMA_JSON = r'''
{"common":{"auto_id":{"pattern":"^a-[0-9]{4}w(0[1-9]|[1-4][0-9]|5[0-3])[.][1-9][0-9]{0,2}$","type":"string"},"base_url":{"maxLength":200,
"pattern":"^(https://[a-z0-9.-]{1,100}|http://127[.]0[.]0[.]1:[0-9]{1,5})/([A-Za-z0-9._~-]{1,100}/){0,8}$","type":"string"},
"baseline_id":{"pattern":"^b-[0-9]{4}[.](0[1-9]|1[0-2])[.][1-9][0-9]{0,2}$","type":"string"},"consent_version":{"$ref":"#/$defs/common.date"},
"date":{"pattern":"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$","type":"string"},"datetime":{"pattern":"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z$",
"type":"string"},"epoch":{"pattern":"^[0-9]{4}-W(0[1-9]|[1-4][0-9]|5[0-3])$","type":"string"},"ht_id":{"pattern":"^ht-(fa|en)-[0-9a-f]{10}$",
"type":"string"},"keyid":{"pattern":"^[0-9a-f]{16}$","type":"string"},"metadata_common":{"properties":{"expires":{"$ref":"#/$defs/common.datetime"},
"issued":{"$ref":"#/$defs/common.datetime"},"spec":{"const":"whalory.tuf-lite/1"},"version":{"maximum":999999999999999,
"minimum":1,"type":"integer"}},"required":["_type","spec","version","issued","expires"],"type":"object"},"param_id":{"pattern":"^(fa|en):[a-z0-9-]{1,40}[.][a-z0-9_]{1,32}$",
"type":"string"},"rule_or_phrase_id":{"pattern":"^[a-z0-9-]{1,40}$","type":"string"},"severity":{"enum":["shadow",
"warning","error","off"]},"sha256_hex":{"pattern":"^[0-9a-f]{64}$","type":"string"}},"schemas":{"auto":{"additionalProperties":false,
"allOf":[{"$ref":"#/$defs/common.metadata_common"}],"properties":{"_type":{"const":"auto"},"expires":true,"issued":true,
"revoked":{"items":{"$ref":"#/$defs/common.auto_id"},"maxItems":1000,"type":"array","uniqueItems":true},"spec":true,
"targets":{"additionalProperties":{"additionalProperties":false,"properties":{"canary":{"additionalProperties":false,
"properties":{"changed":{"items":{"$ref":"#/$defs/common.rule_or_phrase_id"},"maxItems":100,"type":"array","uniqueItems":true},
"density_ratio":{"additionalProperties":{"maximum":100,"minimum":0,"type":"number"},"maxProperties":100,"propertyNames":{"pattern":"^[a-z0-9-]{1,40}$"},
"type":"object"}},"required":["changed","density_ratio"],"type":"object"},"length":{"maximum":33554432,"minimum":1,
"type":"integer"},"prev":{"$ref":"#/$defs/common.auto_id"},"release":{"$ref":"#/$defs/common.auto_id"},"role":{"enum":["candidate",
"stable","previous","registry"]},"schema":{"const":1},"sha256":{"$ref":"#/$defs/common.sha256_hex"}},"required":["sha256",
"length","schema","role"],"type":"object"},"maxProperties":4,"minProperties":1,"propertyNames":{"pattern":"^auto/(overlay-a-[0-9]{4}w(0[1-9]|[1-4][0-9]|5[0-3])[.][1-9][0-9]{0,2}|known-ids-[1-9][0-9]{0,14})[.]json$"},
"type":"object"},"version":true},"required":["_type","spec","version","issued","expires","revoked","targets"],
"type":"object"},"baseline":{"additionalProperties":false,"allOf":[{"$ref":"#/$defs/common.metadata_common"}],
"properties":{"_type":{"const":"baseline"},"expires":true,"issued":true,"policy":{"additionalProperties":false,
"properties":{"caps":{"additionalProperties":false,"properties":{"cumulative":{"additionalProperties":false,"properties":{"max_shadow_share":{"maximum":1,
"minimum":0,"type":"number"},"param_pct":{"maximum":100,"minimum":0,"type":"number"},"phrases_per_lang":{"maximum":3000,
"minimum":0,"type":"integer"},"severity_steps":{"maximum":2,"minimum":0,"type":"integer"}},"required":["severity_steps",
"param_pct","phrases_per_lang","max_shadow_share"],"type":"object"},"per_release":{"additionalProperties":false,
"properties":{"allow_new":{"maximum":10000,"minimum":0,"type":"integer"},"param_step_pct":{"maximum":100,"minimum":0,
"type":"number"},"phrase_demotions":{"maximum":1000,"minimum":0,"type":"integer"},"phrase_new":{"maximum":1000,
"minimum":0,"type":"integer"},"phrase_promotions":{"maximum":1000,"minimum":0,"type":"integer"},"rules":{"maximum":100,
"minimum":0,"type":"integer"},"severity_step":{"maximum":2,"minimum":0,"type":"integer"}},"required":["rules",
"phrase_demotions","phrase_new","phrase_promotions","severity_step","param_step_pct","allow_new"],"type":"object"},
"rolling":{"additionalProperties":false,"properties":{"cooldown_days":{"maximum":365,"minimum":0,"type":"integer"},
"dwell_days_over_10pct":{"maximum":90,"minimum":0,"type":"integer"},"dwell_days_over_50pct":{"maximum":90,"minimum":0,
"type":"integer"},"min_days_between_auto":{"maximum":90,"minimum":0,"type":"integer"},"phrase_demotions":{"maximum":1000,
"minimum":0,"type":"integer"},"rules":{"maximum":100,"minimum":0,"type":"integer"},"window_days":{"maximum":90,
"minimum":1,"type":"integer"}},"required":["window_days","rules","phrase_demotions","cooldown_days","min_days_between_auto",
"dwell_days_over_10pct","dwell_days_over_50pct"],"type":"object"}},"required":["per_release","cumulative","rolling"],
"type":"object"},"channels_machine":{"additionalProperties":{"maxLength":200,"pattern":"^(/[^/]*)+$","type":"string"},
"maxProperties":100,"propertyNames":{"pattern":"^[a-z0-9-]{1,40}[.][a-z0-9_]{1,40}$"},"type":"object"},"collection":{"additionalProperties":false,
"properties":{"consent_versions":{"items":{"$ref":"#/$defs/common.consent_version"},"maxItems":8,"minItems":1,
"type":"array","uniqueItems":true},"discovery_open":{"type":"boolean"},"editions":{"items":{"enum":["core","pro",
"studio"]},"maxItems":3,"type":"array","uniqueItems":true},"open":{"type":"boolean"}},"required":["open","editions",
"consent_versions","discovery_open"],"type":"object"},"explore":{"maximum":1,"minimum":0,"type":"number"},"global_lane":{"additionalProperties":false,
"properties":{"consent_versions":{"items":{"$ref":"#/$defs/common.consent_version"},"maxItems":8,"minItems":1,
"type":"array","uniqueItems":true},"k":{"maximum":1000,"minimum":2,"type":"integer"},"min_account_age_days":{"maximum":3650,
"minimum":0,"type":"integer"},"open":{"type":"boolean"},"repo":{"pattern":"^[A-Za-z0-9-]{1,39}/[A-Za-z0-9._-]{1,100}$",
"type":"string"}},"required":["open","repo","consent_versions","min_account_age_days","k"],"type":"object"},"locked":{"items":{"pattern":"^[a-z0-9*-]{1,40}$",
"type":"string"},"maxItems":200,"minItems":1,"type":"array","uniqueItems":true},"measure":{"additionalProperties":false,
"properties":{"anchors":{"additionalProperties":false,"properties":{"en":{"items":{"pattern":"^[a-z0-9-]{1,40}$",
"type":"string"},"maxItems":10,"type":"array","uniqueItems":true},"fa":{"items":{"pattern":"^[a-z0-9-]{1,40}$",
"type":"string"},"maxItems":10,"type":"array","uniqueItems":true}},"required":["fa","en"],"type":"object"},"holdout":{"additionalProperties":false,
"properties":{"error":{"maximum":100,"minimum":0,"type":"integer"},"warning":{"maximum":100,"minimum":0,"type":"integer"}},
"required":["warning","error"],"type":"object"},"lt_holdout_pct":{"maximum":100,"minimum":0,"type":"integer"},
"rho":{"maximum":1,"minimum":0,"type":"number"}},"required":["holdout","rho","anchors","lt_holdout_pct"],"type":"object"},
"params":{"additionalProperties":{"additionalProperties":false,"properties":{"bucket":{"exclusiveMinimum":0,"maximum":100000,
"type":"number"},"default":{"maximum":100000,"minimum":0,"type":"number"},"max":{"maximum":100000,"minimum":0,
"type":"number"},"min":{"maximum":100000,"minimum":0,"type":"number"}},"required":["default","min","max","bucket"],
"type":"object"},"maxProperties":200,"propertyNames":{"$ref":"#/$defs/common.param_id"},"type":"object"}},"required":["locked",
"params","channels_machine","caps","measure","collection","global_lane","explore"],"type":"object"},"spec":true,
"targets":{"additionalProperties":{"additionalProperties":false,"properties":{"length":{"maximum":262144,"minimum":1,
"type":"integer"},"schema":{"const":1},"sha256":{"$ref":"#/$defs/common.sha256_hex"}},"required":["sha256","length",
"schema"],"type":"object"},"maxProperties":4,"minProperties":1,"propertyNames":{"pattern":"^baseline/overlay-b-[0-9]{4}[.](0[1-9]|1[0-2])[.][1-9][0-9]{0,2}[.]json$"},
"type":"object"},"version":true},"required":["_type","spec","version","issued","expires","targets","policy"],"type":"object"},
"envelope":{"additionalProperties":false,"properties":{"payload":{"maxLength":400000,"minLength":4,"pattern":"^[A-Za-z0-9+/]+={0,2}$",
"type":"string"},"payloadType":{"enum":["application/vnd.whalory.hub.root+json","application/vnd.whalory.hub.timestamp+json",
"application/vnd.whalory.hub.baseline+json","application/vnd.whalory.hub.auto+json","application/vnd.whalory.hub.halt+json",
"application/vnd.whalory.hub.admin+json"]},"signatures":{"items":{"additionalProperties":false,"properties":{"keyid":{"$ref":"#/$defs/common.keyid"},
"sig":{"pattern":"^[A-Za-z0-9+/]{86}==$","type":"string"}},"required":["keyid","sig"],"type":"object"},"maxItems":16,
"minItems":1,"type":"array"}},"required":["payloadType","payload","signatures"],"type":"object"},"halt":{"additionalProperties":false,
"allOf":[{"$ref":"#/$defs/common.metadata_common"}],"properties":{"_type":{"const":"halt"},"expires":true,"halt":{"type":"boolean"},
"issued":true,"pin":{"enum":["baseline","bundled",null]},"reason":{"pattern":"^[A-Za-z0-9 ._:-]{1,64}$","type":"string"},
"spec":true,"stop_collection":{"type":"boolean"},"version":true},"required":["_type","spec","version","issued",
"expires","halt","pin","stop_collection","reason"],"type":"object"},"overlay-1":{"$defs":{"lang_block":{"additionalProperties":false,
"properties":{"params":{"additionalProperties":{"maximum":100000,"minimum":0,"type":"number"},"maxProperties":200,
"propertyNames":{"pattern":"^[a-z0-9-]{1,40}[.][a-z0-9_]{1,32}$"},"type":"object"},"phrases":{"items":{"additionalProperties":false,
"properties":{"id":{"$ref":"#/$defs/common.ht_id"},"phrase":{"maxLength":40,"minLength":2,"type":"string"},"state":{"enum":["shadow",
"warning","error"]}},"required":["id","phrase","state"],"type":"object"},"maxItems":300,"type":"array"},"severity":{"additionalProperties":{"$ref":"#/$defs/common.severity"},
"maxProperties":2000,"propertyNames":{"pattern":"^[a-z0-9-]{1,40}$"},"type":"object"}},"required":["severity",
"params","phrases"],"type":"object"}},"additionalProperties":false,"allOf":[{"else":{"properties":{"base":{"type":"null"},
"id":{"$ref":"#/$defs/common.baseline_id"}}},"if":{"properties":{"kind":{"const":"auto"}}},"then":{"properties":{"base":{"$ref":"#/$defs/common.baseline_id"},
"id":{"$ref":"#/$defs/common.auto_id"}}}}],"properties":{"base":{"anyOf":[{"$ref":"#/$defs/common.baseline_id"},
{"type":"null"}]},"channels":{"additionalProperties":{"additionalProperties":false,"properties":{"checked_on":{"$ref":"#/$defs/common.date"},
"max_chars":{"maximum":100000,"minimum":1,"type":"integer"},"status":{"enum":["verified","unverified","needs-review"]},
"verified_on":{"$ref":"#/$defs/common.date"}},"required":["status"],"type":"object"},"maxProperties":500,"propertyNames":{"pattern":"^[a-z0-9-]{1,40}[.][a-z0-9_]{1,40}$"},
"type":"object"},"compat":{"additionalProperties":false,"properties":{"skill":{"pattern":"^>=[0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}( <[0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3})?$",
"type":"string"}},"required":["skill"],"type":"object"},"evidence":{"anyOf":[{"type":"null"},{"maxLength":300,
"pattern":"^https://[A-Za-z0-9._~/#?=&%-]{1,292}$","type":"string"}]},"id":{"anyOf":[{"$ref":"#/$defs/common.baseline_id"},
{"$ref":"#/$defs/common.auto_id"}]},"issued":{"$ref":"#/$defs/common.datetime"},"kind":{"enum":["baseline","auto"]},
"lang":{"additionalProperties":false,"properties":{"en":{"$ref":"#/$defs/lang_block"},"fa":{"$ref":"#/$defs/lang_block"}},
"type":"object"},"schema":{"const":"whalory.overlay/1"}},"required":["schema","id","kind","base","compat","issued",
"lang","channels","evidence"],"type":"object"},"root":{"$defs":{"role":{"additionalProperties":false,"properties":{"keyids":{"items":{"$ref":"#/$defs/common.keyid"},
"maxItems":8,"minItems":1,"type":"array","uniqueItems":true},"paths":{"items":{"pattern":"^[a-z]{1,20}/[*]$","type":"string"},
"maxItems":4,"minItems":1,"type":"array"},"threshold":{"maximum":8,"minimum":1,"type":"integer"}},"required":["keyids",
"threshold"],"type":"object"}},"additionalProperties":false,"allOf":[{"$ref":"#/$defs/common.metadata_common"}],
"properties":{"_type":{"const":"root"},"collection_country":{"anyOf":[{"type":"null"},{"pattern":"^[A-Z]{2}$",
"type":"string"}]},"collectors":{"items":{"$ref":"#/$defs/common.base_url"},"maxItems":4,"type":"array","uniqueItems":true},
"expires":true,"issued":true,"keys":{"additionalProperties":{"additionalProperties":false,"properties":{"alg":{"const":"ed25519"},
"pub":{"pattern":"^[0-9a-f]{64}$","type":"string"}},"required":["alg","pub"],"type":"object"},"maxProperties":32,
"minProperties":1,"propertyNames":{"$ref":"#/$defs/common.keyid"},"type":"object"},"mirrors":{"items":{"$ref":"#/$defs/common.base_url"},
"maxItems":8,"minItems":1,"type":"array","uniqueItems":true},"roles":{"additionalProperties":false,"properties":{"auto":{"allOf":[{"$ref":"#/$defs/role"},
{"properties":{"paths":{"const":["auto/*"]}},"required":["paths"]}]},"baseline":{"allOf":[{"$ref":"#/$defs/role"},
{"properties":{"paths":{"const":["baseline/*"]}},"required":["paths"]}]},"halt":{"allOf":[{"$ref":"#/$defs/role"},
{"not":{"required":["paths"]}}]},"root":{"$ref":"#/$defs/role"},"timestamp":{"allOf":[{"$ref":"#/$defs/role"},
{"not":{"required":["paths"]}}]}},"required":["root","baseline","auto","timestamp","halt"],"type":"object"},"spec":true,
"token_issuer":{"anyOf":[{"type":"null"},{"$ref":"#/$defs/common.base_url"}]},"version":true},"required":["_type",
"spec","version","issued","expires","keys","roles","mirrors","collectors","token_issuer","collection_country"],
"type":"object"},"timestamp":{"$defs":{"file":{"additionalProperties":false,"properties":{"length":{"maximum":262144,
"minimum":1,"type":"integer"},"sha256":{"$ref":"#/$defs/common.sha256_hex"},"version":{"maximum":999999999999999,
"minimum":1,"type":"integer"}},"required":["version","sha256","length"],"type":"object"}},"additionalProperties":false,
"allOf":[{"$ref":"#/$defs/common.metadata_common"}],"properties":{"_type":{"const":"timestamp"},"expires":true,
"issued":true,"meta":{"additionalProperties":false,"properties":{"auto.json":{"$ref":"#/$defs/file"},"baseline.json":{"$ref":"#/$defs/file"},
"halt.json":{"anyOf":[{"type":"null"},{"$ref":"#/$defs/file"}]}},"required":["baseline.json","auto.json","halt.json"],
"type":"object"},"packets":{"anyOf":[{"type":"null"},{"additionalProperties":false,"properties":{"epoch":{"$ref":"#/$defs/common.epoch"},
"issue":{"anyOf":[{"type":"null"},{"maximum":999999999,"minimum":1,"type":"integer"}]}},"required":["epoch","issue"],
"type":"object"}]},"prev_sha256":{"anyOf":[{"type":"null"},{"$ref":"#/$defs/common.sha256_hex"}]},"rollout":{"additionalProperties":false,
"properties":{"percent":{"maximum":100,"minimum":0,"type":"integer"},"release":{"anyOf":[{"type":"null"},{"$ref":"#/$defs/common.auto_id"}]},
"step":{"maximum":3,"minimum":0,"type":"integer"}},"required":["release","percent","step"],"type":"object"},"spec":true,
"token_keys":{"additionalProperties":{"additionalProperties":false,"properties":{"est":{"$ref":"#/$defs/common.sha256_hex"},
"new":{"$ref":"#/$defs/common.sha256_hex"}},"required":["new","est"],"type":"object"},"maxProperties":6,"propertyNames":{"$ref":"#/$defs/common.epoch"},
"type":"object"},"version":true},"required":["_type","spec","version","issued","expires","prev_sha256","meta",
"rollout","token_keys","packets"],"type":"object"}}}
'''


def _strict_equal(a, b):
    """Equality that keeps bool, int and float apart (true is never 1)."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_strict_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(_strict_equal(x, y) for x, y in zip(a, b))
    return a == b


def _type_ok(v, t):
    if t == 'object':
        return isinstance(v, dict)
    if t == 'array':
        return isinstance(v, list)
    if t == 'string':
        return isinstance(v, str)
    if t == 'integer':
        return type(v) is int
    if t == 'number':
        return is_number(v)
    if t == 'boolean':
        return type(v) is bool
    if t == 'null':
        return v is None
    return False


def _fmt_path(path):
    out = ''
    for p in path:
        out += ('[%d]' % p) if isinstance(p, int) else (('.' if out else '') + p)
    return out


class _Schemas(object):
    """The JSON Schema subset of the contracts (validate.py), over the generated table."""

    def __init__(self, text):
        data = json.loads(text)
        self.common = data['common']
        self.schemas = data['schemas']
        self._rx = {}

    def names(self):
        return sorted(self.schemas)

    def _regex(self, pattern):
        rx = self._rx.get(pattern)
        if rx is None:
            rx = self._rx[pattern] = re.compile(pattern[1:-1])
        return rx

    def _resolve(self, ref, top):
        if ref.startswith('#/$defs/common.'):
            return self.common[ref[len('#/$defs/common.'):]]
        return top['$defs'][ref[len('#/$defs/'):]]

    def validate(self, instance, name):
        """[(path, message)]; empty means valid."""
        top = self.schemas[name]
        errors = []
        self._v(instance, top, top, [], errors)
        return errors

    def _valid(self, x, s, top):
        errs = []
        self._v(x, s, top, [], errs)
        return not errs

    def _v(self, x, s, top, path, errors):
        if s is True:
            return
        if s is False:
            errors.append((_fmt_path(path), 'not allowed'))
            return
        if '$ref' in s:
            self._v(x, self._resolve(s['$ref'], top), top, path, errors)
        t = s.get('type')
        if t is not None:
            types = t if isinstance(t, list) else [t]
            if not any(_type_ok(x, tt) for tt in types):
                errors.append((_fmt_path(path), 'expected %s' % ' or '.join(types)))
                return
        if 'const' in s and not _strict_equal(x, s['const']):
            errors.append((_fmt_path(path), 'must equal the fixed value'))
        if 'enum' in s and not any(_strict_equal(x, e) for e in s['enum']):
            errors.append((_fmt_path(path), 'not one of the allowed values'))
        if isinstance(x, dict):
            self._v_object(x, s, top, path, errors)
        elif isinstance(x, list):
            self._v_array(x, s, top, path, errors)
        elif isinstance(x, str):
            n = len(x)
            if 'minLength' in s and n < s['minLength']:
                errors.append((_fmt_path(path), 'shorter than %d characters' % s['minLength']))
            if 'maxLength' in s and n > s['maxLength']:
                errors.append((_fmt_path(path), 'longer than %d characters' % s['maxLength']))
            if 'pattern' in s and not self._regex(s['pattern']).fullmatch(x):
                errors.append((_fmt_path(path), 'does not match the pattern'))
        elif is_number(x):
            if 'minimum' in s and not (s['minimum'] <= x):
                errors.append((_fmt_path(path), 'below %s' % s['minimum']))
            if 'maximum' in s and not (x <= s['maximum']):
                errors.append((_fmt_path(path), 'above %s' % s['maximum']))
            if 'exclusiveMinimum' in s and not (s['exclusiveMinimum'] < x):
                errors.append((_fmt_path(path), 'must be above %s' % s['exclusiveMinimum']))
            if 'exclusiveMaximum' in s and not (x < s['exclusiveMaximum']):
                errors.append((_fmt_path(path), 'must be below %s' % s['exclusiveMaximum']))
            if 'multipleOf' in s:
                m = s['multipleOf']
                if not (type(x) is int and type(m) is int and x % m == 0):
                    errors.append((_fmt_path(path), 'not a multiple of %s' % m))
        for sub in s.get('allOf', ()):
            self._v(x, sub, top, path, errors)
        if 'anyOf' in s and not any(self._valid(x, sub, top) for sub in s['anyOf']):
            errors.append((_fmt_path(path), 'matches none of the allowed shapes'))
        if 'oneOf' in s:
            n = sum(1 for sub in s['oneOf'] if self._valid(x, sub, top))
            if n != 1:
                errors.append((_fmt_path(path), 'must match exactly one shape'))
        if 'not' in s and self._valid(x, s['not'], top):
            errors.append((_fmt_path(path), 'matches a forbidden shape'))
        if 'if' in s:
            if self._valid(x, s['if'], top):
                if 'then' in s:
                    self._v(x, s['then'], top, path, errors)
            elif 'else' in s:
                self._v(x, s['else'], top, path, errors)

    def _v_object(self, x, s, top, path, errors):
        props = s.get('properties', {})
        pats = s.get('patternProperties', {})
        for k in s.get('required', ()):
            if k not in x:
                errors.append((_fmt_path(path + [k]), 'required'))
        if 'minProperties' in s and len(x) < s['minProperties']:
            errors.append((_fmt_path(path), 'fewer than %d keys' % s['minProperties']))
        if 'maxProperties' in s and len(x) > s['maxProperties']:
            errors.append((_fmt_path(path), 'more than %d keys' % s['maxProperties']))
        for k, v in x.items():
            if 'propertyNames' in s:
                sub = []
                self._v(k, s['propertyNames'], top, path, sub)
                if sub:
                    errors.append((_fmt_path(path + [k]), 'key not allowed'))
                    continue
            matched = False
            if k in props:
                matched = True
                self._v(v, props[k], top, path + [k], errors)
            for pat, sub in pats.items():
                if self._regex(pat).fullmatch(k):
                    matched = True
                    self._v(v, sub, top, path + [k], errors)
            if not matched and 'additionalProperties' in s:
                ap = s['additionalProperties']
                if ap is False:
                    errors.append((_fmt_path(path + [k]), 'unknown key'))
                else:
                    self._v(v, ap, top, path + [k], errors)

    def _v_array(self, x, s, top, path, errors):
        if 'minItems' in s and len(x) < s['minItems']:
            errors.append((_fmt_path(path), 'fewer than %d items' % s['minItems']))
        if 'maxItems' in s and len(x) > s['maxItems']:
            errors.append((_fmt_path(path), 'more than %d items' % s['maxItems']))
        if s.get('uniqueItems'):
            for i in range(len(x)):
                for j in range(i):
                    if _strict_equal(x[i], x[j]):
                        errors.append((_fmt_path(path + [i]), 'duplicate item'))
                        break
        if 'items' in s:
            for i, v in enumerate(x):
                self._v(v, s['items'], top, path + [i], errors)


SCHEMAS = _Schemas(_SCHEMA_JSON)

# ----------------------------------------------------------------------------- semantic checks

#: Longest allowed issued-to-expires span per role, in days (spec 7.1, 5.8 step 2).
MAX_LIFETIME_DAYS = {'root': 366, 'baseline': 180, 'auto': 30, 'timestamp': 7, 'halt': 180}


def _lifetime(doc, role, errs):
    if not (time_valid(doc['issued']) and time_valid(doc['expires'])):
        errs.append(('issued', 'not a real date and time'))
        return
    issued, expires = parse_time(doc['issued']), parse_time(doc['expires'])
    if expires <= issued:
        errs.append(('expires', 'must be after issued'))
    elif expires - issued > datetime.timedelta(days=MAX_LIFETIME_DAYS[role]):
        errs.append(('expires', 'more than %d days after issued' % MAX_LIFETIME_DAYS[role]))


def sem_root(doc, check_keys=True):
    errs = []
    _lifetime(doc, 'root', errs)
    for kid, key in doc['keys'].items():
        pub = bytes.fromhex(key['pub'])
        if keyid_of(pub) != kid:
            errs.append(('keys.%s' % kid, 'keyid is not the first 16 hex of SHA-256(public key)'))
        if check_keys and not public_key_ok(pub):
            errs.append(('keys.%s' % kid, 'not a canonical, full-order Ed25519 public key'))
    owner = {}
    for role, spec in doc['roles'].items():
        for kid in spec['keyids']:
            if kid not in doc['keys']:
                errs.append(('roles.%s.keyids' % role, 'keyid %s is not in keys' % kid))
            if kid in owner:
                errs.append(('roles.%s.keyids' % role, 'keyid %s is also used by role %s' % (kid, owner[kid])))
            owner[kid] = role
        if spec['threshold'] > len(spec['keyids']):
            errs.append(('roles.%s.threshold' % role, 'higher than the number of keys'))
    if doc['roles']['root']['threshold'] < 2:
        errs.append(('roles.root.threshold', 'root needs a threshold of at least 2'))
    if set(owner) != set(doc['keys']):
        errs.append(('keys', 'every key belongs to a role'))
    if bool(doc['collectors']) != (doc['token_issuer'] is not None) or \
            bool(doc['collectors']) != (doc['collection_country'] is not None):
        errs.append(('collectors', 'collectors, token_issuer and collection_country are set together or not at all'))
    return errs


def sem_timestamp(doc):
    errs = []
    _lifetime(doc, 'timestamp', errs)
    for epoch in doc['token_keys']:
        if not iso_week_valid(epoch):
            errs.append(('token_keys.%s' % epoch, 'not a real ISO week'))
    if doc['packets'] is not None and not iso_week_valid(doc['packets']['epoch']):
        errs.append(('packets.epoch', 'not a real ISO week'))
    if (doc['version'] == 1) != (doc['prev_sha256'] is None):
        errs.append(('prev_sha256', 'null exactly for version 1'))
    r = doc['rollout']
    if r['release'] is None and (r['percent'] != 0 or r['step'] != 0):
        errs.append(('rollout', 'no release in flight means percent 0 and step 0'))
    if r['release'] is not None and not auto_id_valid(r['release']):
        errs.append(('rollout.release', 'not a real auto overlay id'))
    return errs


def sem_baseline(doc):
    errs = []
    _lifetime(doc, 'baseline', errs)
    for path in doc['targets']:
        if not baseline_id_valid(path[len('baseline/overlay-'):-len('.json')]):
            errs.append(('targets.%s' % path, 'not a real baseline id'))
    pol = doc['policy']
    for pid, p in pol['params'].items():
        if not (p['min'] <= p['default'] <= p['max']):
            errs.append(('policy.params.%s' % pid, 'default outside [min, max]'))
    for lang, anchors in pol['measure']['anchors'].items():
        for a in anchors:
            if id_lang(a) != lang:
                errs.append(('policy.measure.anchors.%s' % lang, '%s belongs to the other language' % a))
            if is_locked(a, pol['locked']):
                errs.append(('policy.measure.anchors.%s' % lang, 'anchor %s is locked' % a))
    for key in pol['channels_machine']:
        if key.count('.') != 1:
            errs.append(('policy.channels_machine.%s' % key, 'key is <channel>.<field>'))
    return errs


def sem_auto(doc):
    errs = []
    _lifetime(doc, 'auto', errs)
    for i, rel in enumerate(doc['revoked']):
        if not auto_id_valid(rel):
            errs.append(('revoked[%d]' % i, 'not a real auto overlay id'))
    roles = {}
    for path, t in doc['targets'].items():
        p = 'targets.%s' % path
        roles.setdefault(t['role'], []).append(path)
        if t['role'] == 'registry':
            if not path.startswith('auto/known-ids-') or 'release' in t:
                errs.append((p, 'a registry target is auto/known-ids-<n>.json and has no release'))
        else:
            if path != 'auto/overlay-%s.json' % t.get('release'):
                errs.append((p, 'path must be auto/overlay-<release>.json'))
            if t.get('release') in doc['revoked']:
                errs.append((p, 'a listed release must not be revoked'))
            if not auto_id_valid(t.get('release')):
                errs.append((p, 'not a real auto overlay id'))
        if t['role'] == 'candidate' and ('prev' not in t or 'canary' not in t):
            errs.append((p, 'a candidate needs prev and canary'))
        if t['role'] != 'candidate' and ('prev' in t or 'canary' in t):
            errs.append((p, 'only a candidate carries prev and canary'))
        if t['role'] == 'candidate' and t.get('prev') == t.get('release'):
            errs.append((p, 'prev names an earlier release'))
    for role, paths in roles.items():
        if len(paths) > 1:
            errs.append(('targets', 'more than one %s target' % role))
    return errs


def sem_halt(doc):
    errs = []
    _lifetime(doc, 'halt', errs)
    if doc['halt'] and doc['pin'] is None:
        errs.append(('pin', 'a halt pins baseline or bundled'))
    if not doc['halt'] and (doc['pin'] is not None or doc['stop_collection']):
        errs.append(('halt', 'a lift has pin null and stop_collection false'))
    return errs


def sem_overlay(doc):
    errs = []
    auto = doc['kind'] == 'auto'
    if not (baseline_id_valid(doc['id']) or auto_id_valid(doc['id'])):
        errs.append(('id', 'not a real overlay id (week or month does not exist)'))
    if not time_valid(doc['issued']):
        errs.append(('issued', 'not a real date and time'))
    rng = doc['compat']['skill'].split(' ')
    if len(rng) == 2 and not _semver(rng[0][2:]) < _semver(rng[1][1:]):
        errs.append(('compat.skill', 'the lower bound must be below the upper bound'))
    for lang, block in doc['lang'].items():
        for ident, level in block['severity'].items():
            p = 'lang.%s.severity.%s' % (lang, ident)
            if id_lang(ident) != lang:
                errs.append((p, 'id belongs to the other language'))
            if ident[:3] in ('lx-', 'ht-', 'ng-') and PHRASE_ID_RE.fullmatch(ident) is None:
                errs.append((p, 'malformed phrase id'))
            if auto and level == 'off':
                errs.append((p, 'only a baseline overlay may turn a rule off'))
            if ident.startswith('ht-'):
                errs.append((p, 'hub phrases take their state from phrases[], not from severity'))
        for name in block['params']:
            if name.startswith('en-') != (lang == 'en'):
                errs.append(('lang.%s.params.%s' % (lang, name), 'parameter of the other language'))
        seen = set()
        for i, ph in enumerate(block['phrases']):
            p = 'lang.%s.phrases[%d]' % (lang, i)
            problem = phrase_literal_problem(lang, ph['phrase'])
            if problem:
                errs.append((p + '.phrase', problem))
                continue
            if ph['id'] != ht_id(lang, ph['phrase']):
                errs.append((p + '.id', 'must be %s' % ht_id(lang, ph['phrase'])))
            if ph['id'] in seen:
                errs.append((p + '.id', 'duplicate phrase'))
            seen.add(ph['id'])
            if auto and ph['state'] == 'error':
                errs.append((p + '.state', 'hub phrases never reach error automatically'))
    for key, ch in doc['channels'].items():
        if 'max_chars' in ch and ch['status'] != 'verified':
            errs.append(('channels.%s' % key, 'a value update also sets status verified'))
        for f in ('verified_on', 'checked_on'):
            if f in ch and not date_valid(ch[f]):
                errs.append(('channels.%s.%s' % (key, f), 'not a real date'))
    return errs


_SEMANTICS = {'root': sem_root, 'timestamp': sem_timestamp, 'baseline': sem_baseline, 'auto': sem_auto,
              'halt': sem_halt, 'overlay-1': sem_overlay}


def validate_doc(doc, name):
    """Schema check, then the semantic checks; a list of (path, message)."""
    errs = SCHEMAS.validate(doc, name)
    if errs:
        return errs
    sem = _SEMANTICS.get(name)
    return sem(doc) if sem else []


def evaluate_document(raw, name):
    """The stage codes of the contracts for one document (vectors/documents.json):
    {'ok': True} or {'ok': False, 'stage': size|parse|schema|bounds, 'code', 'path'?}."""
    limit = MAX_BYTES.get(name, DEFAULT_MAX_BYTES)
    if len(raw) > limit:
        return {'ok': False, 'stage': 'size', 'code': 'too_large'}
    try:
        doc = loads(raw, max_bytes=limit)
    except HubError as e:
        return {'ok': False, 'stage': 'parse', 'code': e.code}
    errs = SCHEMAS.validate(doc, name)
    if errs:
        return {'ok': False, 'stage': 'schema', 'code': 'schema', 'path': errs[0][0]}
    sem = _SEMANTICS.get(name)
    errs = sem(doc) if sem else []
    if errs:
        return {'ok': False, 'stage': 'bounds', 'code': 'bounds', 'path': errs[0][0]}
    return {'ok': True}


# ----------------------------------------------------------------------------- signed metadata (spec 7.1 to 7.3)

ROLES = ('root', 'timestamp', 'baseline', 'auto', 'halt')

#: Key ids of the public TEST ONLY keys of STUDIO/hub/contracts/fixtures/test-keys. Anyone can sign
#: with them, so a root that lists one proves nothing outside tests (see is_test_root).
TEST_KEY_IDS = frozenset([
    '2319786c17c2bd85', '0347f3bf2ae6b02c', 'f6dfa2461f0f4739', '677bb2584cce4e2a', 'd96dbf08dccc9d92',
    'd595f9b676933a4c', '093401e2866137fe', '2c383f65e136c99f', '0c0a2b44529e56be', '0a81fcd4790de395',
])


def is_test_root(root):
    """True when a root document lists any public test key (its signatures prove nothing)."""
    try:
        return bool(TEST_KEY_IDS.intersection(root['keys']))
    except (KeyError, TypeError, AttributeError):
        return True


def role_keys(root, role):
    """({keyid: 32-byte public key}, threshold) of a role in a verified root."""
    spec = root['roles'][role]
    keys = {}
    for kid in spec['keyids']:
        k = root['keys'].get(kid)
        if k is not None:
            keys[kid] = bytes.fromhex(k['pub'])
    return keys, spec['threshold']


def _check_body(doc, role):
    if doc.get('_type') != role:
        raise HubError('schema', 'the body is not a %s document' % role, '_type')
    errs = SCHEMAS.validate(doc, role)
    if errs:
        raise HubError('schema', errs[0][1], errs[0][0])
    errs = _SEMANTICS[role](doc)
    if errs:
        raise HubError('semantic', errs[0][1], errs[0][0])


def open_signed(data, role, root, max_bytes=None):
    """Hardened parse, envelope schema, signatures of the role in root, then the body's schema
    and semantic checks. Returns the body document; raises HubError."""
    cap = MAX_BYTES['envelope.' + role]
    if max_bytes is not None:
        cap = min(cap, max_bytes)
    keys, thr = role_keys(root, role)
    body = verify_envelope(bytes(data), keys, thr, PAYLOAD_TYPES[role], max_bytes=cap)
    doc = loads(body, max_bytes=cap)
    _check_body(doc, role)
    return doc


def _peek(data, role):
    """The body of an envelope without checking signatures (to read a new root's own keys)."""
    env = loads(bytes(data), max_bytes=MAX_BYTES['envelope.' + role])
    errs = SCHEMAS.validate(env, 'envelope')
    if errs:
        raise HubError('envelope', errs[0][1], errs[0][0])
    if env['payloadType'] != PAYLOAD_TYPES[role]:
        raise HubError('payload_type', env['payloadType'][:80])
    try:
        body = b64std_decode(env['payload'])
    except ValueError:
        raise HubError('payload_base64')
    doc = loads(body, max_bytes=MAX_BYTES['envelope.' + role])
    _check_body(doc, role)
    return doc


def parse_pinned_root(data, check_signatures=True):
    """The pinned root that ships with the skill (SKILL/data/hub/root.json).

    It is trusted because it ships with the code: its body is parsed hardened and checked
    against the root schema and semantics (canonical, full-order keys), and with
    check_signatures it must carry a threshold of signatures by its own root keys (a check
    against a damaged file; hub_overlay skips it at lint time to stay within its budget).
    """
    doc = _peek(data, 'root')
    if check_signatures:
        keys, thr = role_keys(doc, 'root')
        verify_envelope(bytes(data), keys, thr, PAYLOAD_TYPES['root'], MAX_BYTES['envelope.root'])
    return doc


def update_root(trusted_root, data):
    """Spec 5.8 step 1 for one fetched root/<N+1>.json: signed by a threshold of the old
    root's root keys and of its own root keys, version exactly N + 1. Returns the new root."""
    new = _peek(data, 'root')
    for signer in (trusted_root, new):
        keys, thr = role_keys(signer, 'root')
        verify_envelope(bytes(data), keys, thr, PAYLOAD_TYPES['root'], MAX_BYTES['envelope.root'])
    if new['version'] != trusted_root['version'] + 1:
        raise HubError('root_version', 'root version %d after %d' % (new['version'], trusted_root['version']))
    return new


def root_changes(old, new):
    """What a root rotation changed (spec 5.8 step 1, 4.10): a set of role names whose keys or
    threshold changed, plus 'recipients' when collectors, token_issuer or collection_country changed."""
    out = set()
    for role in ROLES:
        a, b = old['roles'][role], new['roles'][role]
        keys_a = sorted((k, old['keys'][k]['pub']) for k in a['keyids'] if k in old['keys'])
        keys_b = sorted((k, new['keys'][k]['pub']) for k in b['keyids'] if k in new['keys'])
        if keys_a != keys_b or a['threshold'] != b['threshold']:
            out.add(role)
    for field in ('collectors', 'token_issuer', 'collection_country'):
        if old.get(field) != new.get(field):
            out.add('recipients')
    return out


def check_timestamp(roots, data, stored=None, fetch_prev=None, max_back=8):
    """Spec 5.8 step 3. roots: the verified root chain, oldest first. stored: the bytes of the
    trusted timestamp, or None. fetch_prev(version) returns the served timestamps/<version>.json
    bytes or None when the mirror does not have it. Returns the new timestamp document.

    Refuses a lower version (rollback); an equal version must have identical bytes (fork).
    When the new version is more than one above the stored one, up to max_back predecessors
    are fetched and the prev_sha256 chain must reach the stored timestamp (fork on a break,
    chain_missing when a predecessor cannot be fetched). A gap wider than max_back + 1 checks
    the links it fetched and then accepts: a client back from a long blackout cannot compare
    further back.
    """
    root = roots[-1]
    new = open_signed(data, 'timestamp', root)
    if stored is None:
        return new
    try:
        old = open_signed(stored, 'timestamp', root)
    except HubError:
        return new          # the stored copy no longer verifies (key rotation): nothing to compare
    if new['version'] < old['version']:
        raise HubError('rollback', 'timestamp version %d below the stored %d' % (new['version'], old['version']))
    if new['version'] == old['version']:
        if bytes(data) != bytes(stored):
            raise HubError('fork', 'same timestamp version with different bytes')
        return new
    succ, v, steps = new, new['version'] - 1, 0
    stored_hash = sha256_hex(stored)
    while True:
        if v == old['version']:
            if succ['prev_sha256'] != stored_hash:
                raise HubError('fork', 'the prev_sha256 chain does not reach the stored timestamp')
            return new
        if steps >= max_back:
            return new
        prev = fetch_prev(v) if fetch_prev is not None else None
        if prev is None:
            raise HubError('chain_missing', 'timestamps/%d.json is not available' % v)
        if sha256_hex(prev) != succ['prev_sha256']:
            raise HubError('fork', 'timestamps/%d.json does not match prev_sha256' % v)
        doc = None
        for r in reversed(roots):
            try:
                doc = open_signed(prev, 'timestamp', r)
                break
            except HubError:
                continue
        if doc is None or doc['version'] != v:
            raise HubError('fork', 'timestamps/%d.json does not verify' % v)
        succ, v, steps = doc, v - 1, steps + 1


def halt_in_force(halt, clock):
    """True while a verified halt with halt: true has not expired at clock."""
    return bool(halt) and bool(halt.get('halt')) and parse_time(halt['expires']) >= clock


def check_halt(root, data, stored=None, now=None, clock=None):
    """Spec 5.8 step 2 for a fetched halt.json. Returns the halt document when it is accepted,
    None when it is not newer than the stored one or already expired; raises HubError when it
    does not verify, is issued more than 1 day in the future (halt_future) or raises the version
    by more than 10^6 (halt_jump). stored: the stored halt document or None."""
    now = _now(now)
    clock = clock or now
    doc = open_signed(data, 'halt', root)
    floor = stored['version'] if stored else 0
    if doc['version'] <= floor:
        return None
    if doc['version'] - floor > 10 ** 6:
        raise HubError('halt_jump', 'halt version %d after %d' % (doc['version'], floor))
    if parse_time(doc['issued']) > now + datetime.timedelta(days=1):
        raise HubError('halt_future', 'halt issued %s' % doc['issued'])
    if parse_time(doc['expires']) < clock:
        return None
    return doc


def check_targets_meta(root, role, data, timestamp, floor=None):
    """Spec 5.8 step 4 for baseline.json or auto.json: length and SHA-256 as the timestamp
    pins them, signatures of the role, version as pinned and not below floor, and every
    target path inside the role's paths. Returns the document."""
    meta = timestamp['meta'][role + '.json']
    data = bytes(data)
    if len(data) != meta['length'] or sha256_hex(data) != meta['sha256']:
        raise HubError('mismatch', '%s.json is not the file the timestamp pins' % role)
    doc = open_signed(data, role, root, max_bytes=meta['length'])
    if doc['version'] != meta['version']:
        raise HubError('mismatch', '%s.json version %d, the timestamp pins %d'
                       % (role, doc['version'], meta['version']))
    if floor is not None and doc['version'] < floor:
        raise HubError('rollback', '%s.json version %d below the stored %d' % (role, doc['version'], floor))
    for tpath in doc['targets']:
        if not any(_glob_path(p, tpath) for p in root['roles'][role]['paths']):
            raise HubError('paths', '%s is outside the %s role' % (tpath, role), 'targets.' + tpath)
    return doc


def check_target(data, entry):
    """Spec 5.8 steps 6 and 7 for one overlay target: exact length and SHA-256 from the signed
    metadata, then the hardened parse, the overlay schema and its semantic checks."""
    data = bytes(data)
    if len(data) != entry['length'] or sha256_hex(data) != entry['sha256']:
        raise HubError('mismatch', 'target differs from its signed length or hash')
    doc = loads(data, max_bytes=MAX_BYTES['overlay-1'])
    errs = SCHEMAS.validate(doc, 'overlay-1')
    if errs:
        raise HubError('schema', errs[0][1], errs[0][0])
    errs = sem_overlay(doc)
    if errs:
        raise HubError('semantic', errs[0][1], errs[0][0])
    return doc


# ----------------------------------------------------------------------------- rollout (spec 6.14, 7.5)

def canary_bucket(install_salt, release):
    """int.from_bytes(SHA-256(salt + release id)[:8], 'big') % 10000."""
    return int.from_bytes(hashlib.sha256(bytes(install_salt) + release.encode('ascii')).digest()[:8], 'big') % 10000


def effective_percent(percent, first_seen, now, rolling):
    """Dwell times (spec 7.5): honour more than 10% only 6 days after first seeing the release,
    more than 50% only after 13 days (the numbers come from the baseline's caps.rolling)."""
    age = _now(now) - _now(first_seen)
    if age < datetime.timedelta(days=rolling['dwell_days_over_10pct']):
        return min(percent, 10)
    if age < datetime.timedelta(days=rolling['dwell_days_over_50pct']):
        return min(percent, 50)
    return percent


# ----------------------------------------------------------------------------- snapshots


def reader(folder, layout='mirror'):
    """A read(rel) function over a folder: layout 'mirror' (spec 8.2, also the bundled set) or
    'hub' (trusted/ plus targets/, see the module docs). rel is always in mirror form
    ('root/2.json', 'timestamp.json', 'targets/<sha256>.json'). Missing files give None."""
    def read(rel, max_bytes=None):
        parts = rel.split('/')
        if layout == 'hub' and parts[0] != 'targets':
            parts = ['trusted'] + parts
        path = os.path.join(folder, *parts)
        try:
            with open(path, 'rb') as fh:
                data = fh.read(-1 if max_bytes is None else max_bytes + 1)
        except (IOError, OSError):
            return None
        if max_bytes is not None and len(data) > max_bytes:
            raise HubError('too_large', '%s is over %d bytes' % (rel, max_bytes))
        return data
    return read


class Snapshot(object):
    """A verified set of metadata: roots (oldest first), timestamp, baseline, auto, halt."""

    def __init__(self):
        self.roots = []
        self.root = None
        self.timestamp = None
        self.baseline = None
        self.auto = None
        self.halt = None
        self.raw = {}
        self.stale = False
        self.root_expired = False       # an expired root still verifies; the client warns (spec 7.6)
        self.clock = None
        self.revoked = set()

    def target_entry(self, path):
        """The signed entry of a target path, from baseline.json or auto.json, or None."""
        for doc in (self.baseline, self.auto):
            if doc and path in doc['targets']:
                return doc['targets'][path]
        return None

    def halt_active(self):
        return halt_in_force(self.halt, self.clock)


def _clock(now, rules):
    now = _now(now)
    last = (rules or {}).get('last_issued')
    try:
        last = parse_time(last) if last else None
    except ValueError:
        last = None
    return max(now, last) if last else now


def load_roots(pinned_root, read, max_steps=32, check_pinned=True):
    """The pinned root, then root/<N+1>.json for as long as read() finds one (at most 32 steps)."""
    root = parse_pinned_root(pinned_root, check_pinned)
    roots = [root]
    for _ in range(max_steps):
        data = read('root/%d.json' % (root['version'] + 1), MAX_BYTES['envelope.root'])
        if data is None:
            break
        root = update_root(root, data)
        roots.append(root)
    return roots


def load_snapshot(read, pinned_root, now=None, rules=None, require=('timestamp', 'baseline'), check_pinned=True):
    """Verify a stored or bundled set (spec 5.9 re-verification) and return a Snapshot.

    read(rel) returns bytes or None (see reader()). The chain starts at the pinned root;
    baseline.json and auto.json must be the files the timestamp pins; version floors from
    rules['versions'] refuse anything older than what this install has seen. Expired
    metadata is not an error: the snapshot is marked stale (spec 7.6). Raises HubError.
    """
    rules = rules or {}
    floors = rules.get('versions') or {}
    snap = Snapshot()
    snap.clock = _clock(now, rules)
    snap.roots = load_roots(pinned_root, read, check_pinned=check_pinned)
    snap.root = snap.roots[-1]
    snap.root_expired = parse_time(snap.root['expires']) < snap.clock
    ts_raw = read('timestamp.json', MAX_BYTES['envelope.timestamp'])
    if ts_raw is None:
        if 'timestamp' in require:
            raise HubError('not_found', 'timestamp.json')
        return snap
    ts = open_signed(ts_raw, 'timestamp', snap.root)
    if isinstance(floors.get('timestamp'), int) and ts['version'] < floors['timestamp']:
        raise HubError('rollback', 'timestamp version %d below the stored %d' % (ts['version'], floors['timestamp']))
    snap.timestamp, snap.raw['timestamp.json'] = ts, ts_raw
    for role in ('baseline', 'auto'):
        meta = ts['meta'][role + '.json']
        data = read(role + '.json', meta['length'])
        if data is None:
            if role in require:
                raise HubError('not_found', role + '.json')
            continue
        floor = floors.get(role) if isinstance(floors.get(role), int) else None
        setattr(snap, role, check_targets_meta(snap.root, role, data, ts, floor))
        snap.raw[role + '.json'] = data
    halt_raw = read('halt.json', MAX_BYTES['envelope.halt'])
    if halt_raw is not None:
        try:
            snap.halt = open_signed(halt_raw, 'halt', snap.root)
            snap.raw['halt.json'] = halt_raw
        except HubError:
            snap.halt = None        # a halt that no longer verifies (halt key rotated) does not apply
    snap.revoked = set(rules.get('revoked') or ())
    if snap.auto:
        snap.revoked.update(snap.auto['revoked'])
    snap.stale = parse_time(ts['expires']) < snap.clock
    return snap


# ----------------------------------------------------------------------------- one sync run (spec 5.8 steps 1 to 6)


class SyncResult(object):
    """What one sync run decided. hub_client writes files, removes remove, stores rules under
    state.json "rules", records health, and then asks hub_overlay to decide the activation of
    selection (spec 5.8 steps 7 to 9)."""

    def __init__(self):
        self.ok = False
        self.code = None
        self.detail = ''
        self.health = []             # [(kind, reason)], kinds of spec 5.2 record_health
        self.files = {}              # {hub-relative path: bytes}
        self.remove = []             # hub-relative paths
        self.rules = {}
        self.snapshot = None
        self.stale = False
        self.halt = None             # the halt in force, or None
        self.recipients_changed = False
        self.selection = None        # {'baseline': target, 'auto': target or None, 'reason': str}
        self.targets = {}            # {sha256: parsed overlay}

    def as_dict(self):
        sel = None
        if self.selection:
            sel = dict((k, (dict((kk, vv) for kk, vv in v.items() if kk != 'overlay') if isinstance(v, dict) else v))
                       for k, v in self.selection.items())
        return {'ok': self.ok, 'code': self.code, 'detail': self.detail, 'health': list(self.health),
                'files': sorted(self.files), 'remove': list(self.remove), 'stale': self.stale,
                'root_expired': bool(self.snapshot and self.snapshot.root_expired), 'halt': self.halt,
                'recipients_changed': self.recipients_changed, 'selection': sel}


def _target_info(path, entry, doc):
    return {'path': path, 'sha256': entry['sha256'], 'length': entry['length'], 'role': entry.get('role'),
            'release': entry.get('release'), 'prev': entry.get('prev'), 'id': doc['id'], 'overlay': doc}


def _baseline_key(path):
    m = re.search(r'overlay-b-([0-9]{4})\.([0-9]{2})\.([0-9]+)\.json$', path)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0)


def sync(pinned_root, trusted, rules, fetch, now=None, skill_version='3.0.0', install_salt=b'',
         active=None, max_back=8):
    """One run of spec 5.8 steps 1 to 6; returns a SyncResult and never raises HubError.

    pinned_root   bytes of SKILL/data/hub/root.json
    trusted       read(rel) over the Hub folder (reader(hub, 'hub')), or a dict {rel: bytes}
    rules         the "rules" object of state.json (see the module docs), or None
    fetch         fetch(rel, max_bytes) -> bytes, or None when the mirror answers 404; it tries
                  the mirrors, builds If-None-Match, enforces the byte caps and raises any
                  exception for a network failure (reported as code 'network')
    active        the active record of hub_overlay (active.json), used for the stale rule
    """
    res = SyncResult()
    now = _now(now)
    original = json.loads(json.dumps(rules or {}))
    rules = json.loads(json.dumps(rules or {}))
    rules.setdefault('versions', {})
    if isinstance(trusted, dict):
        store = dict(trusted)
        trusted = (lambda rel, max_bytes=None: store.get(rel))
    try:
        _sync(res, pinned_root, trusted, rules, fetch, now, skill_version, install_salt, active or {}, max_back)
        res.ok = True
    except HubError as e:
        res.code, res.detail = e.code, str(e)
        if e.code == 'fork':
            res.health.append(('verify_fail', 'fork'))
        res.health.append(('sync_fail', None))
    except Exception as e:  # network or a bug in fetch: learning pauses, nothing changes
        res.code, res.detail = 'network', '%s: %s' % (type(e).__name__, str(e)[:120])
        res.health.append(('sync_fail', None))
        res.files, res.remove = {}, []
    if res.ok:
        res.health.append(('sync_ok', None))
        res.rules = rules
    else:
        res.files, res.remove, res.selection, res.snapshot = {}, [], None, None
        res.rules = original
    return res


def _fetch(fetch, rel, cap):
    data = fetch(rel, cap)
    if data is not None and len(data) > cap:
        raise HubError('too_large', '%s is over %d bytes' % (rel, cap))
    return data


def _sync(res, pinned_root, trusted, rules, fetch, now, skill_version, salt, active, max_back):
    versions = rules['versions']
    clock = _clock(now, rules)
    # --- 1. root chain: the stored chain first, then the mirrors
    roots = load_roots(pinned_root, trusted)
    removed = set()
    for _ in range(32 - (len(roots) - 1)):
        rel = 'root/%d.json' % (roots[-1]['version'] + 1)
        data = _fetch(fetch, rel, MAX_BYTES['envelope.root'])
        if data is None:
            break
        new = update_root(roots[-1], data)
        changed = root_changes(roots[-1], new)
        if 'timestamp' in changed or 'auto' in changed:
            removed.update(('timestamp', 'auto'))
        if 'baseline' in changed:
            removed.add('baseline')
        if 'halt' in changed:
            removed.add('halt')
        if 'recipients' in changed:
            res.recipients_changed = True
        roots.append(new)
        res.files['trusted/' + rel] = bytes(data)
    root = roots[-1]
    versions['root'] = max(root['version'], versions.get('root') or 0)
    for role in removed:
        res.remove.append('trusted/%s.json' % role)
        versions.pop(role, None)

    def stored(rel):
        if rel.split('.')[0] in removed:
            return None
        return trusted(rel, None)

    # --- 2. halt
    halt_stored = None
    raw = stored('halt.json')
    if raw is not None:
        try:
            halt_stored = open_signed(raw, 'halt', root)
        except HubError:
            halt_stored = None
    data = _fetch(fetch, 'halt.json', MAX_BYTES['envelope.halt'])
    halt = halt_stored
    if data is not None:
        floor = {'version': versions['halt']} if isinstance(versions.get('halt'), int) else halt_stored
        try:
            got = check_halt(root, data, floor, now=now, clock=clock)
        except HubError:
            got = None      # a halt that fails the rules is ignored; the stored one still applies
        if got is not None:
            halt = got
            versions['halt'] = got['version']
            res.files['trusted/halt.json'] = bytes(data)
    res.halt = halt if halt_in_force(halt, clock) else None
    # --- 3. timestamp
    ts_stored = stored('timestamp.json')
    data = _fetch(fetch, 'timestamp.json', MAX_BYTES['envelope.timestamp'])
    if data is None:
        if ts_stored is None:
            raise HubError('not_found', 'timestamp.json')
        data = ts_stored
    floor = versions.get('timestamp')

    def prev_of(v):
        return _fetch(fetch, 'timestamps/%d.json' % v, MAX_BYTES['envelope.timestamp'])

    ts = check_timestamp(roots, data, ts_stored, prev_of, max_back)
    if isinstance(floor, int) and ts['version'] < floor:
        raise HubError('rollback', 'timestamp version %d below the highest seen %d' % (ts['version'], floor))
    if ts_stored is None or bytes(data) != bytes(ts_stored):
        res.files['trusted/timestamp.json'] = bytes(data)
    versions['timestamp'] = ts['version']
    last = rules.get('last_issued')
    rules['last_issued'] = fmt_time(max([parse_time(ts['issued'])] + ([parse_time(last)] if last else [])))
    clock = _clock(now, rules)
    res.stale = parse_time(ts['expires']) < clock
    # --- 4. targets metadata
    docs = {}
    for role in ('baseline', 'auto'):
        meta = ts['meta'][role + '.json']
        cur = stored(role + '.json')
        data = cur if (cur is not None and len(cur) == meta['length'] and sha256_hex(cur) == meta['sha256']) else None
        if data is None:
            data = _fetch(fetch, role + '.json', meta['length'])
            if data is None:
                raise HubError('not_found', role + '.json')
            res.files['trusted/%s.json' % role] = bytes(data)
        floor = versions.get(role) if isinstance(versions.get(role), int) else None
        docs[role] = check_targets_meta(root, role, data, ts, floor)
        versions[role] = docs[role]['version']
    revoked = set(rules.get('revoked') or ())
    revoked.update(docs['auto']['revoked'])
    rules['revoked'] = sorted(revoked)
    snap = Snapshot()
    snap.roots, snap.root, snap.timestamp = roots, root, ts
    snap.baseline, snap.auto, snap.halt = docs['baseline'], docs['auto'], halt
    snap.stale, snap.clock, snap.revoked = res.stale, clock, revoked
    snap.root_expired = parse_time(root['expires']) < clock
    res.snapshot = snap

    def target(path, entry):
        rel = 'targets/%s.json' % entry['sha256']
        data = trusted(rel, entry['length'])
        if data is None or len(data) != entry['length'] or sha256_hex(data) != entry['sha256']:
            data = _fetch(fetch, rel, entry['length'])
            if data is None:
                raise HubError('not_found', rel)
            res.files[rel] = bytes(data)
        doc = check_target(data, entry)
        res.targets[entry['sha256']] = doc
        return doc

    # --- 5 and 6. choose and download
    base_sel = None
    for path in sorted(docs['baseline']['targets'], key=_baseline_key, reverse=True):
        entry = docs['baseline']['targets'][path]
        try:
            doc = target(path, entry)
        except HubError:
            continue
        if doc['kind'] == 'baseline' and compat_ok(doc['compat']['skill'], skill_version):
            base_sel = _target_info(path, entry, doc)
            break
    if base_sel is None:
        raise HubError('no_baseline', 'no baseline overlay fits skill %s' % skill_version)
    res.selection = {'baseline': base_sel, 'auto': None, 'reason': 'none'}
    if res.halt is not None:
        res.selection['reason'] = 'halt:' + str(res.halt.get('pin'))
        return
    rolling = docs['baseline']['policy']['caps']['rolling']
    rollout = ts['rollout']
    first_seen = rules.setdefault('first_seen', {})
    percent_seen = rules.setdefault('percent', {})
    if rollout['release']:
        first_seen.setdefault(rollout['release'], fmt_time(now))
    by_role = {}
    for path, entry in docs['auto']['targets'].items():
        if entry['role'] in ('candidate', 'stable'):
            by_role[entry['role']] = (path, entry)
    active_auto = ((active or {}).get('auto') or {}).get('id')

    def usable(role):
        if role not in by_role:
            return None
        path, entry = by_role[role]
        if entry.get('release') in revoked:
            return None
        try:
            doc = target(path, entry)
        except HubError:
            return None
        if doc['kind'] != 'auto' or doc['base'] != base_sel['id'] or doc['id'] != entry.get('release'):
            return None
        if not compat_ok(doc['compat']['skill'], skill_version):
            return None
        return _target_info(path, entry, doc)

    cand = None
    if 'candidate' in by_role and by_role['candidate'][1].get('release') == rollout['release']:
        rel_id = rollout['release']
        pct = effective_percent(rollout['percent'], first_seen.get(rel_id, fmt_time(now)), now, rolling)
        if res.stale:
            pct = min(pct, percent_seen.get(rel_id, 0))
            if active_auto != rel_id:
                pct = 0         # stale metadata never activates a new target
        if canary_bucket(salt, rel_id) < pct * 100:
            cand = usable('candidate')
            if cand is not None and not res.stale:
                percent_seen[rel_id] = max(percent_seen.get(rel_id, 0), pct)
    if cand is not None:
        res.selection.update(auto=cand, reason='candidate')
        return
    stable = usable('stable')       # the listed stable is the fall back, allowed even when stale
    if stable is not None:
        res.selection.update(auto=stable, reason='stable')
        return
    res.selection['reason'] = 'baseline'
