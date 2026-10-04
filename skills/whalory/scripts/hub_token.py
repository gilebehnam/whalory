#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hub_token: the client side of Whalory Hub's licensed tokens (spec 5.7, RFC 9474).

Standard library only, Python 3.8 to 3.14: hashlib, hmac, os.urandom and pow(r, -1, n).
It opens no socket, writes no file and starts no process; hub_client sends the requests
and stores the token. Nothing here ever sees or keeps the licence key itself after
licence_key_hash(): the shop receives a lookup code and a one-time proof, both derived from
key_hash, and a blinded message it cannot link to the token it signs.

Scheme: RSABSSA-SHA384-PSS-Randomized (RFC 9474 section 5): SHA-384, MGF1 with SHA-384,
a 48-byte salt and a 32-byte random prefix; the final signature is an ordinary RSASSA-PSS
signature over input_msg = prefix + msg. EMSA-PSS uses emBits = modBits - 1 (RFC 8017;
RFC 9474 erratum 9089), the only reading that reproduces the RFC 9474 test vectors.

Flow (hub_client drives it, in one tick of its own, spec 5.6):
    keys = trusted_keys(token_keys_doc_bytes, timestamp['token_keys'], epoch)   # fingerprint check
    body, pending = begin(epoch, keys[tenure], key_hash, nonce)                  # POST /api/hub/token
    token = finish(pending, response_bytes)                                      # unblind and verify
    header = token['header']                                                     # Whalory-Token at upload
    verify_token(token, timestamp['token_keys']) -> bool                         # again before the upload

Tenure: the shop signs with the key of the licence's tenure (new or est, spec 6.18 step 7),
but the client has to blind with that key before it asks. begin() takes the tenure the
client expects (hub_client keeps the tenure of its last token; with none, 'est'). When the
shop signed with the other key, finish() raises TokenError('tenure', tenure=<the shop's>)
so the client can use it next time. See the open question in the handoff notes.

Every public function returns a value or raises TokenError (code, and tenure where it
applies); the predicates never raise.
"""
from __future__ import print_function

import base64
import hashlib
import hmac
import json
import math
import os
import re

__all__ = ['TokenError', 'normalize_licence_key', 'licence_key_hash', 'licence_lookup', 'licence_proof',
           'parse_rsa_spki', 'rsa_spki_der', 'spki_fingerprint', 'emsa_pss_encode', 'emsa_pss_verify',
           'rsassa_pss_verify', 'rsabssa_prepare', 'rsabssa_blind', 'rsabssa_finalize', 'token_message',
           'token_epoch', 'token_pn', 'token_header', 'parse_token_header', 'trusted_keys', 'begin', 'finish',
           'verify_token', 'b64url', 'b64url_decode']

PREFIX_LEN = 32
SALT_LEN = 48
H_LEN = 48                      # SHA-384
TOKEN_MSG_PREFIX = 'whalory-hub-token|v1|'
PUBLIC_EXPONENT = 65537
MODULUS_BITS = (2048, 3072, 4096)
MAX_RESPONSE = 16 * 1024        # shop responses are read with a 16 KiB cap (spec 5.6)
_EPOCH = re.compile(r'[0-9]{4}-W(0[1-9]|[1-4][0-9]|5[0-3])')
_HEX64 = re.compile(r'[0-9a-f]{64}')
_HEX32 = re.compile(r'[0-9a-f]{32}')
_B64URL = re.compile(r'[A-Za-z0-9_-]+')


class TokenError(Exception):
    """A token step failed; code is a short stable token."""

    def __init__(self, code, detail='', tenure=None):
        Exception.__init__(self, code + (': ' + detail if detail else ''))
        self.code = code
        self.detail = detail
        self.tenure = tenure


# ----------------------------------------------------------------------------- encodings


def b64url(data):
    """Unpadded base64url (RFC 4648 section 5)."""
    return base64.urlsafe_b64encode(bytes(data)).rstrip(b'=').decode('ascii')


def b64url_decode(s):
    """Strict unpadded base64url; raises ValueError on any other spelling of the same bytes."""
    if not isinstance(s, str) or len(s) % 4 == 1 or not _B64URL.fullmatch(s or '-'):
        raise ValueError('not unpadded base64url')
    raw = base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))
    if b64url(raw) != s:
        raise ValueError('non-canonical base64url')
    return raw


def _i2osp(x, length):
    return int(x).to_bytes(length, 'big')


def _os2ip(b):
    return int.from_bytes(bytes(b), 'big')


def _sha256_hex(data):
    return hashlib.sha256(bytes(data)).hexdigest()


# ----------------------------------------------------------------------------- licence proof (spec 5.7)

_FA_DIGITS = dict((ord(c), str(i)) for i, c in enumerate('۰۱۲۳۴۵۶۷۸۹'))
_AR_DIGITS = dict((ord(c), str(i)) for i, c in enumerate('٠١٢٣٤٥٦٧٨٩'))
_KEY_RE = re.compile(r'WLR3-(PRO|STU)(-[0-9A-HJKMNP-TV-Z]{4}){5}')


def normalize_licence_key(value):
    """The canonical licence key, exactly as STUDIO/web/src/licensing.js normalizeLicenseKey()
    computes it (Persian and Arabic-Indic digits, case, separators, O -> 0, I and L -> 1), or None."""
    if not isinstance(value, str):
        return None
    s = value.translate(_FA_DIGITS).translate(_AR_DIGITS).upper()
    s = re.sub('[^0-9A-Z]', '', s)
    if len(s) > 64:
        return None
    m = re.fullmatch('WLR3(PRO|STU)([0-9A-Z]{20})', s)
    if not m:
        return None
    body = m.group(2).replace('O', '0').replace('I', '1').replace('L', '1')
    if re.search('[^0-9A-HJKMNP-TV-Z]', body):
        return None
    out = 'WLR3-%s-%s' % (m.group(1), '-'.join(body[i:i + 4] for i in range(0, 20, 4)))
    return out if _KEY_RE.fullmatch(out) else None


def licence_key_hash(canonical_key):
    """key_hash = lower-case hex SHA-256 of the canonical key (as the shop stores it)."""
    return _sha256_hex(canonical_key.encode('utf-8'))


def licence_lookup(key_hash):
    """lookup = hex(SHA-256("whalory-lookup|" + key_hash))[:16]."""
    return _sha256_hex(('whalory-lookup|' + key_hash).encode('ascii'))[:16]


def licence_proof(key_hash, nonce, epoch, blinded):
    """proof = hex(HMAC-SHA256(key = the 64 ASCII characters of key_hash,
    "whalory-hub-token|" + nonce + "|" + epoch + "|" + hex(SHA-256(blinded))))."""
    msg = 'whalory-hub-token|%s|%s|%s' % (nonce, epoch, _sha256_hex(blinded))
    return hmac.new(key_hash.encode('ascii'), msg.encode('ascii'), hashlib.sha256).hexdigest()


# ----------------------------------------------------------------------------- RSA public keys

_RSA_OID = bytes.fromhex('2a864886f70d010101')


def _der_len(n):
    if n < 0x80:
        return bytes([n])
    b = n.to_bytes((n.bit_length() + 7) // 8, 'big')
    return bytes([0x80 | len(b)]) + b


def _der(tag, body):
    return bytes([tag]) + _der_len(len(body)) + body


def _der_int(x):
    return _der(0x02, x.to_bytes(max(1, (x.bit_length() + 8) // 8), 'big'))


def rsa_spki_der(n, e):
    """DER SubjectPublicKeyInfo of an RSA public key (rsaEncryption, NULL parameters)."""
    alg = _der(0x30, _der(0x06, _RSA_OID) + b'\x05\x00')
    return _der(0x30, alg + _der(0x03, b'\x00' + _der(0x30, _der_int(n) + _der_int(e))))


def _der_read(buf, pos):
    if pos + 2 > len(buf):
        raise ValueError('truncated DER')
    tag, ln = buf[pos], buf[pos + 1]
    pos += 2
    if ln & 0x80:
        k = ln & 0x7f
        if k == 0 or k > 4 or pos + k > len(buf):
            raise ValueError('bad DER length')
        ln = int.from_bytes(buf[pos:pos + k], 'big')
        pos += k
    if pos + ln > len(buf):
        raise ValueError('truncated DER')
    return tag, buf[pos:pos + ln], pos + ln


def parse_rsa_spki(der):
    """(n, e) of an RSA SubjectPublicKeyInfo in DER; raises TokenError('key')."""
    try:
        der = bytes(der)
        tag, body, end = _der_read(der, 0)
        if tag != 0x30 or end != len(der):
            raise ValueError('SPKI is not one SEQUENCE')
        tag, alg, pos = _der_read(body, 0)
        if tag != 0x30:
            raise ValueError('no AlgorithmIdentifier')
        tag, oid, _ = _der_read(alg, 0)
        if tag != 0x06 or oid != _RSA_OID:
            raise ValueError('not rsaEncryption')
        tag, bits, pos = _der_read(body, pos)
        if tag != 0x03 or bits[:1] != b'\x00' or pos != len(body):
            raise ValueError('no BIT STRING')
        tag, seq, end = _der_read(bits, 1)
        if tag != 0x30 or end != len(bits):
            raise ValueError('no RSAPublicKey')
        tag, n_raw, pos = _der_read(seq, 0)
        tag2, e_raw, pos = _der_read(seq, pos)
        if tag != 0x02 or tag2 != 0x02 or pos != len(seq):
            raise ValueError('bad RSAPublicKey')
        if n_raw[:1] == b'\x00' and len(n_raw) > 1 and n_raw[1] < 0x80:
            raise ValueError('non-minimal INTEGER')
        n, e = _os2ip(n_raw), _os2ip(e_raw)
    except (ValueError, IndexError, TypeError) as ex:
        raise TokenError('key', str(ex))
    if rsa_spki_der(n, e) != der:
        raise TokenError('key', 'not the canonical DER of its key')
    return n, e


def spki_fingerprint(der):
    """Spec 5.7, 7.3: lower-case hex SHA-256 of the SubjectPublicKeyInfo DER."""
    return _sha256_hex(der)


# ----------------------------------------------------------------------------- EMSA-PSS (RFC 8017 section 9.1)


def _h(data):
    return hashlib.sha384(data).digest()


def _mgf1(seed, length):
    out = b''
    counter = 0
    while len(out) < length:
        out += _h(seed + counter.to_bytes(4, 'big'))
        counter += 1
    return out[:length]


def emsa_pss_encode(message, em_bits, salt):
    """EMSA-PSS-ENCODE with SHA-384 and MGF1-SHA384; em_bits = modBits - 1."""
    em_len = (em_bits + 7) // 8
    s_len = len(salt)
    if em_len < H_LEN + s_len + 2:
        raise TokenError('encoding', 'modulus too small')
    h = _h(b'\x00' * 8 + _h(bytes(message)) + bytes(salt))
    db = b'\x00' * (em_len - s_len - H_LEN - 2) + b'\x01' + bytes(salt)
    masked = bytes(a ^ b for a, b in zip(db, _mgf1(h, em_len - H_LEN - 1)))
    zero_bits = 8 * em_len - em_bits
    masked = bytes([masked[0] & (0xff >> zero_bits)]) + masked[1:]
    return masked + h + b'\xbc'


def emsa_pss_verify(message, em, em_bits, s_len=SALT_LEN):
    """EMSA-PSS-VERIFY with SHA-384 and MGF1-SHA384; never raises."""
    try:
        em = bytes(em)
        em_len = (em_bits + 7) // 8
        if len(em) != em_len or em_len < H_LEN + s_len + 2 or em[-1:] != b'\xbc':
            return False
        masked, h = em[:em_len - H_LEN - 1], em[em_len - H_LEN - 1:-1]
        zero_bits = 8 * em_len - em_bits
        if masked[0] & (0xff << (8 - zero_bits)) & 0xff:
            return False
        db = bytes(a ^ b for a, b in zip(masked, _mgf1(h, em_len - H_LEN - 1)))
        db = bytes([db[0] & (0xff >> zero_bits)]) + db[1:]
        ps_len = em_len - H_LEN - s_len - 2
        if db[:ps_len] != b'\x00' * ps_len or db[ps_len:ps_len + 1] != b'\x01':
            return False
        salt = db[len(db) - s_len:] if s_len else b''
        return hmac.compare_digest(_h(b'\x00' * 8 + _h(bytes(message)) + salt), h)
    except (TypeError, ValueError, IndexError):
        return False


def rsassa_pss_verify(n, e, message, signature, s_len=SALT_LEN):
    """RSASSA-PSS-VERIFY (RFC 8017 section 8.1.2), SHA-384 and MGF1-SHA384; never raises."""
    try:
        k = (n.bit_length() + 7) // 8
        signature = bytes(signature)
        if len(signature) != k:
            return False
        s = _os2ip(signature)
        if s >= n:
            return False
        m = pow(s, e, n)
        em_bits = n.bit_length() - 1
        em_len = (em_bits + 7) // 8
        if m >= 1 << (8 * em_len):
            return False
        return emsa_pss_verify(bytes(message), _i2osp(m, em_len), em_bits, s_len)
    except (TypeError, ValueError, AttributeError):
        return False


# ----------------------------------------------------------------------------- RSABSSA (RFC 9474 section 4)


def rsabssa_prepare(msg, prefix=None):
    """Randomized preparation: a 32-byte random prefix before the message (RFC 9474 section 4.1)."""
    prefix = os.urandom(PREFIX_LEN) if prefix is None else bytes(prefix)
    if len(prefix) != PREFIX_LEN:
        raise TokenError('prefix', 'the prefix is 32 bytes')
    return prefix + bytes(msg)


def rsabssa_blind(n, e, input_msg, salt=None, r=None, s_len=SALT_LEN):
    """RFC 9474 section 4.2. Returns (blinded bytes, inverse of r mod n, encoded message)."""
    k = (n.bit_length() + 7) // 8
    salt = os.urandom(s_len) if salt is None else bytes(salt)
    encoded = emsa_pss_encode(input_msg, n.bit_length() - 1, salt)
    m = _os2ip(encoded)
    if math.gcd(m, n) != 1:
        raise TokenError('invalid_input', 'the encoded message is not coprime to n')
    while r is None:
        cand = _os2ip(os.urandom(k)) % n
        if cand > 1 and math.gcd(cand, n) == 1:
            r = cand
    if not (1 < r < n) or math.gcd(r, n) != 1:
        raise TokenError('invalid_input', 'r is not a unit mod n')
    inv = pow(r, -1, n)
    z = m * pow(r, e, n) % n
    return _i2osp(z, k), inv, encoded


def rsabssa_finalize(n, e, input_msg, blind_sig, inv, s_len=SALT_LEN):
    """RFC 9474 section 4.4: unblind and verify. Returns the signature; raises TokenError."""
    k = (n.bit_length() + 7) // 8
    blind_sig = bytes(blind_sig)
    if len(blind_sig) != k:
        raise TokenError('signature', 'unexpected blind signature size')
    z = _os2ip(blind_sig)
    if z >= n:
        raise TokenError('signature', 'blind signature not below n')
    sig = _i2osp(z * inv % n, k)
    if not rsassa_pss_verify(n, e, input_msg, sig, s_len):
        raise TokenError('signature', 'the unblinded signature does not verify')
    return sig


# ----------------------------------------------------------------------------- tokens (spec 5.7, 6.3)


def token_message(epoch, rand32=None):
    """msg = "whalory-hub-token|v1|" + epoch + "|" + hex(32 random bytes)."""
    if not _EPOCH.fullmatch(epoch or ''):
        raise TokenError('epoch', 'not a YYYY-Www week')
    rand32 = os.urandom(32) if rand32 is None else bytes(rand32)
    if len(rand32) != 32:
        raise TokenError('random', 'the token message carries 32 random bytes')
    return (TOKEN_MSG_PREFIX + epoch + '|' + rand32.hex()).encode('ascii')


def token_epoch(input_msg):
    """The epoch named inside input_msg; raises TokenError('bad_message')."""
    input_msg = bytes(input_msg)
    if len(input_msg) != PREFIX_LEN + len(TOKEN_MSG_PREFIX) + 8 + 1 + 64:
        raise TokenError('bad_message', 'bad token message length')
    try:
        text = input_msg[PREFIX_LEN:].decode('ascii')
    except UnicodeDecodeError:
        raise TokenError('bad_message', 'token message not ASCII')
    if not text.startswith(TOKEN_MSG_PREFIX):
        raise TokenError('bad_message', 'bad token message prefix')
    epoch, sep, rand = text[len(TOKEN_MSG_PREFIX):].partition('|')
    if not sep or not _EPOCH.fullmatch(epoch) or not _HEX64.fullmatch(rand):
        raise TokenError('bad_message', 'bad token message')
    return epoch


def token_pn(input_msg):
    """pn = base64url(SHA-256(input_msg))[:22], the token id the hub deduplicates on."""
    return b64url(hashlib.sha256(bytes(input_msg)).digest())[:22]


def token_header(input_msg, sig, fingerprint):
    """Whalory-Token: v2.<base64url(input_msg)>.<base64url(sig)>.<fingerprint>."""
    return 'v2.%s.%s.%s' % (b64url(input_msg), b64url(sig), fingerprint)


def parse_token_header(value):
    """(input_msg, sig, fingerprint) of a Whalory-Token value; raises TokenError('malformed')."""
    try:
        if not isinstance(value, str) or len(value) > 2048:
            raise ValueError('token too long')
        parts = value.split('.')
        if len(parts) != 4 or parts[0] != 'v2':
            raise ValueError('not a v2 token')
        input_msg, sig = b64url_decode(parts[1]), b64url_decode(parts[2])
        if not _HEX64.fullmatch(parts[3]):
            raise ValueError('bad fingerprint')
        return input_msg, sig, parts[3]
    except ValueError as e:
        raise TokenError('malformed', str(e))


# ----------------------------------------------------------------------------- the key-fingerprint check


def _loads(data, cap):
    """Minimal hardened JSON for shop answers: bytes, capped, UTF-8, no NaN, no duplicate keys."""
    if not isinstance(data, (bytes, bytearray)) or len(data) > cap:
        raise TokenError('response', 'not bytes, or over %d bytes' % cap)

    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise TokenError('response', 'duplicate key')
            d[k] = v
        return d

    def bad(_name):
        raise TokenError('response', 'non-finite number')

    try:
        doc = json.loads(bytes(data).decode('utf-8'), object_pairs_hook=pairs, parse_constant=bad)
    except (ValueError, RecursionError):
        raise TokenError('response', 'not JSON')
    if not isinstance(doc, dict):
        raise TokenError('response', 'not a JSON object')
    return doc


def trusted_keys(keys_doc, token_keys, epoch):
    """{tenure: key} of the shop's published keys (GET /api/hub/token-keys, bytes or a parsed
    document) that the client may use for epoch: only keys whose SPKI hashes to the fingerprint
    the trusted timestamp lists for (epoch, tenure) in token_keys, with e = 65537 and a
    modulus of 2048, 3072 or 4096 bits. A key the timestamp does not list is never used, so
    the shop cannot hand one person a key of their own (spec 5.7). Raises TokenError('response')
    for a malformed document; an empty result means no usable key this week."""
    doc = _loads(keys_doc, MAX_RESPONSE) if isinstance(keys_doc, (bytes, bytearray)) else keys_doc
    if not isinstance(doc, dict) or set(doc) != {'keys'} or not isinstance(doc['keys'], list) or len(doc['keys']) > 8:
        raise TokenError('response', 'not a token-keys document')
    want = (token_keys or {}).get(epoch) or {}
    out = {}
    for k in doc['keys']:
        if not isinstance(k, dict) or set(k) != {'epoch', 'tenure', 'fingerprint', 'spki', 'modulus_bits'}:
            raise TokenError('response', 'malformed key entry')
        if k['epoch'] != epoch or k['tenure'] not in ('new', 'est') or want.get(k['tenure']) != k['fingerprint']:
            continue
        try:
            der = b64url_decode(k['spki'])
        except ValueError:
            continue
        if spki_fingerprint(der) != k['fingerprint']:
            continue
        try:
            n, e = parse_rsa_spki(der)
        except TokenError:
            continue
        if e != PUBLIC_EXPONENT or n.bit_length() not in MODULUS_BITS or n.bit_length() != k['modulus_bits']:
            continue
        out[k['tenure']] = {'epoch': epoch, 'tenure': k['tenure'], 'fingerprint': k['fingerprint'], 'n': n, 'e': e}
    return out


# ----------------------------------------------------------------------------- the request and its answer


def begin(epoch, key, key_hash, nonce, rand=None):
    """Build the POST /api/hub/token body for one key (a value of trusted_keys()).

    Returns (body, pending): body is the request document; pending keeps the blinding state
    in memory until finish() and must never be written to disk or sent. rand replaces
    os.urandom in tests only.
    """
    if not _HEX32.fullmatch(nonce or ''):
        raise TokenError('nonce', 'the nonce is 32 lower-case hex characters')
    if not _HEX64.fullmatch(key_hash or ''):
        raise TokenError('key_hash', 'key_hash is 64 lower-case hex characters')
    rnd = rand or os.urandom
    n, e = key['n'], key['e']
    input_msg = rsabssa_prepare(token_message(epoch, rnd(32)), rnd(PREFIX_LEN))
    r = None
    k = (n.bit_length() + 7) // 8
    while r is None:
        cand = _os2ip(rnd(k)) % n
        if cand > 1 and math.gcd(cand, n) == 1:
            r = cand
    blinded, inv, _encoded = rsabssa_blind(n, e, input_msg, salt=rnd(SALT_LEN), r=r)
    body = {'lookup': licence_lookup(key_hash), 'proof': licence_proof(key_hash, nonce, epoch, blinded),
            'nonce': nonce, 'epoch': epoch, 'blinded': b64url(blinded)}
    pending = {'epoch': epoch, 'key': key, 'input_msg': input_msg, 'inv': inv}
    return body, pending


def finish(pending, response):
    """Unblind the shop's answer (bytes or a parsed token-response) and verify it as an
    RSASSA-PSS signature with the trusted key (spec 5.7 step 4). Returns the token to store
    in tokens/<epoch>.json: {"epoch", "tenure", "key", "pn", "header"}.

    Raises TokenError: response (malformed), tenure (the shop signed with its key for the
    other tenure; error.tenure says which, so the next request can use it), signature
    (the token does not verify; the client discards it and records verify_fail local).
    """
    doc = _loads(response, MAX_RESPONSE) if isinstance(response, (bytes, bytearray)) else response
    if not isinstance(doc, dict) or set(doc) != {'blind_sig', 'tenure', 'key'}:
        raise TokenError('response', 'not a token-response document')
    if doc['tenure'] not in ('new', 'est') or not _HEX64.fullmatch(str(doc['key'])):
        raise TokenError('response', 'bad tenure or key')
    key = pending['key']
    if doc['key'] != key['fingerprint'] or doc['tenure'] != key['tenure']:
        raise TokenError('tenure', 'the shop signed with another key', tenure=doc['tenure'])
    try:
        blind_sig = b64url_decode(doc['blind_sig'])
    except ValueError:
        raise TokenError('response', 'blind_sig is not base64url')
    sig = rsabssa_finalize(key['n'], key['e'], pending['input_msg'], blind_sig, pending['inv'])
    input_msg = pending['input_msg']
    return {'epoch': pending['epoch'], 'tenure': key['tenure'], 'key': key['fingerprint'],
            'pn': token_pn(input_msg), 'header': token_header(input_msg, sig, key['fingerprint'])}


def verify_token(token, token_keys, keys=None):
    """True when a stored token is still usable for its epoch: its header parses, names the
    epoch, uses the fingerprint that token_keys (of the trusted timestamp) lists for
    (epoch, tenure), and, when keys ({fingerprint: (n, e)} or a trusted_keys() result) are
    given, the signature verifies. Never raises."""
    try:
        input_msg, sig, fp = parse_token_header(token['header'])
        if token_epoch(input_msg) != token['epoch'] or fp != token['key']:
            return False
        if ((token_keys or {}).get(token['epoch']) or {}).get(token['tenure']) != fp:
            return False
        if keys is None:
            return True
        k = keys.get(fp) or keys.get(token['tenure'])
        if k is None:
            return False
        n, e = (k['n'], k['e']) if isinstance(k, dict) else k
        if isinstance(k, dict) and k.get('fingerprint') != fp:
            return False
        return rsassa_pss_verify(n, e, input_msg, sig)
    except (TokenError, KeyError, TypeError, ValueError, AttributeError):
        return False
