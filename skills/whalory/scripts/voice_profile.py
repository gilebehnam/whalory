#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portable, offline voice-profile contract, resolver and reversible migration.

Python 3.8+, standard library only. Product and profile schema versions are independent.
Run with --help. No lookup, network access or writes occur on import or resolution.
"""
from __future__ import print_function

import argparse
import copy
import hashlib
import io
import json
import os
import sys
import tempfile

SCHEMA_VERSION = 3
DIAL_DEFAULTS = {'warmth': 3, 'formality': 3, 'humor': 1, 'narrative': 3,
                 'sentence_length': 3, 'loud_marks': 0, 'jargon': 2, 'rhetoric': 3,
                 'energy': 3, 'directness': 3, 'slang': 1}
DIAL_RANGES = {key: (0, 3) if key == 'loud_marks' else (1, 5) for key in DIAL_DEFAULTS}
NEW_DIALS = ('energy', 'directness', 'slang')
FORMAT_IDS = ('caption', 'story', 'reels', 'carousel', 'post', 'sms', 'otp', 'email',
              'subject', 'push', 'ui', 'error', 'product', 'listing', 'landing', 'about',
              'blog', 'ad', 'press', 'bot', 'reply', 'hard', 'deck', 'script', 'name', 'headline')
WORD_CAPS = {'fa': {1: 14, 2: 18, 3: 24, 4: 28, 5: 34},
             'en': {1: 15, 2: 20, 3: 25, 4: 30, 5: 35}}
MARK_CAPS = {0: (0, 0), 1: (1, 0), 2: (1, 1), 3: (2, 1)}
ENUMS = {'register': ('any', 'formal', 'colloquial'), 'address': ('any', 'shoma', 'to'),
         'language': ('fa', 'en', 'bilingual'),
         'variant': ('fa-IR', 'fa-AF', 'tg', 'en-US', 'en-GB', 'en-AU', 'en-CA',
                     'en-NZ', 'en-IE', 'en-IN', 'en-ZA'),
         'spelling': ('us', 'uk', 'uk-ize'), 'contractions': ('use', 'avoid', 'positive-only'),
         'house_style': ('chicago', 'ap', 'microsoft', 'google', 'govuk', 'mailchimp')}
NULLABLE = ('spelling', 'contractions', 'house_style', 'reading_grade_max', 'oxford_comma')
WORD_LISTS = ('banned', 'avoid', 'allow', 'claim_boundaries')
STRING_MAPS = ('prefer', 'romanization')
STYLE_KEYS = ('register', 'address', 'variant', 'spelling', 'contractions', 'house_style',
              'reading_grade_max', 'oxford_comma', 'dials', 'max_words', 'emoji_max',
              'exclaim_max', 'banned', 'avoid', 'allow', 'prefer', 'romanization',
              'claim_boundaries', 'fixed_facts', 'note', 'extensions')
ROOT_KEYS = STYLE_KEYS + ('schema_version', 'name', 'language', 'variants', 'brand',
                          'industry', 'formats', 'by_lang')
ALIASES = {'register': {'written': 'formal', 'colloquial-written': 'colloquial'},
           'address': {'شما': 'shoma', 'تو': 'to'}}
PROTECTED_LISTS = ('banned', 'claim_boundaries')


class ProfileError(ValueError):
    def __init__(self, issues):
        self.issues = issues if isinstance(issues, list) else [
            {'path': '$', 'code': 'profile', 'message': str(issues)}]
        super(ProfileError, self).__init__('; '.join('%s: %s' % (x['path'], x['message'])
                                                     for x in self.issues))


def _canonical(data):
    p = copy.deepcopy(data)
    if not isinstance(p, dict):
        return p
    for key, aliases in ALIASES.items():
        if isinstance(p.get(key), str):
            p[key] = aliases.get(p[key], p[key])
    dials = p.get('dials')
    if isinstance(dials, dict) and 'rhetoric_dose' in dials:
        if 'rhetoric' not in dials:
            dials['rhetoric'] = dials.pop('rhetoric_dose')
        elif dials['rhetoric'] == dials['rhetoric_dose']:
            del dials['rhetoric_dose']
    for key in ('by_lang', 'formats'):
        if isinstance(p.get(key), dict):
            p[key] = {name: _canonical(value) for name, value in p[key].items()}
    return p


def validate_profile(profile, partial=False):
    """Return structured errors; absence is allowed, explicit invalid null is not.

    Versionless/v1/v2 documents are readable. English nullable style fields retain
    their v2 meaning. Arbitrary application metadata belongs in extensions.
    """
    errors = []

    def err(path, code, message):
        errors.append({'path': path, 'code': code, 'message': message})

    def obj(value, path, allowed):
        if not isinstance(value, dict):
            err(path, 'type', 'must be an object')
            return False
        for key in value:
            if not isinstance(key, str) or key not in allowed:
                err(path + '.' + str(key), 'unknown_key', 'unknown key; store custom data in extensions')
        return True

    def string_map(value, path):
        if not isinstance(value, dict) or any(not isinstance(k, str) or not k.strip()
                                            or not isinstance(v, str) for k, v in value.items()):
            err(path, 'type', 'must map nonempty strings to strings')

    def settings(value, path, root=False, language=False):
        allowed = ROOT_KEYS if root else STYLE_KEYS + (('formats',) if language else ())
        if not obj(value, path, allowed):
            return
        for key, item in value.items():
            p = path + '.' + str(key)
            if key == 'schema_version':
                if type(item) is not int or item not in (1, 2, 3):
                    err(p, 'version', 'supported schema versions are 1, 2 and 3')
            elif key in ENUMS:
                if item is None and key in NULLABLE:
                    continue
                if not isinstance(item, str) or item not in ENUMS[key]:
                    err(p, 'enum', 'must be one of: ' + ', '.join(ENUMS[key]))
            elif key in ('name', 'industry', 'note'):
                if not isinstance(item, str):
                    err(p, 'type', 'must be a string')
            elif key == 'dials':
                if obj(item, p, DIAL_RANGES):
                    for dial, val in item.items():
                        if dial in DIAL_RANGES:
                            lo, hi = DIAL_RANGES[dial]
                            if type(val) is not int or not lo <= val <= hi:
                                err(p + '.' + dial, 'range', 'must be an integer from %d to %d' % (lo, hi))
            elif key in ('max_words', 'emoji_max', 'exclaim_max'):
                if type(item) is not int or item < (1 if key == 'max_words' else 0):
                    err(p, 'range', 'must be a %s integer' % ('positive' if key == 'max_words' else 'nonnegative'))
            elif key == 'reading_grade_max':
                if item is not None and (type(item) not in (int, float) or not 4 <= item <= 16):
                    err(p, 'range', 'must be a number from 4 to 16 or null')
            elif key == 'oxford_comma':
                if item is not None and type(item) is not bool:
                    err(p, 'type', 'must be a boolean or null')
            elif key in WORD_LISTS or key == 'variants':
                if not isinstance(item, list) or not all(isinstance(v, str) for v in item):
                    err(p, 'type', 'must be an array of strings')
                elif key == 'variants' and any(v not in ENUMS['variant'] for v in item):
                    err(p, 'enum', 'contains an unsupported language variant')
            elif key in STRING_MAPS:
                string_map(item, p)
            elif key == 'brand':
                if obj(item, p, ('fa', 'latin', 'misspellings')):
                    for bk, bv in item.items():
                        if bk == 'misspellings':
                            string_map(bv, p + '.' + bk)
                        elif not isinstance(bv, str):
                            err(p + '.' + bk, 'type', 'must be a string')
            elif key == 'by_lang':
                if obj(item, p, ('fa', 'en')):
                    for lang, val in item.items():
                        if lang in ('fa', 'en'):
                            settings(val, p + '.' + lang, language=True)
            elif key == 'formats':
                if obj(item, p, FORMAT_IDS):
                    for fid, val in item.items():
                        settings(val, p + '.' + fid)
            elif key in ('extensions', 'fixed_facts'):
                if not isinstance(item, dict):
                    err(p, 'type', 'must be an object')
                else:
                    try:
                        json.dumps(item, allow_nan=False)
                    except (TypeError, ValueError):
                        err(p, 'type', 'must contain finite JSON values')
        if root and isinstance(value.get('variants'), list) and value['variants']:
            if value.get('variant') and value['variant'] not in value['variants']:
                err(path + '.variants', 'variant', 'must contain the default variant')

    version = profile.get('schema_version', 1) if isinstance(profile, dict) else 1
    settings(profile if version == 3 else _canonical(profile), '$', root=not partial)
    return errors


def normalize_profile(profile):
    """Return a fresh schema3 profile; only the three new neutral dials are added.

    Old absent dials stay absent so legacy lint activation and caps do not change.
    resolve_profile supplies the complete eleven-dial defaults for generation.
    """
    errors = validate_profile(profile)
    p = _canonical(profile)
    if errors:
        raise ProfileError(errors)
    p['schema_version'] = SCHEMA_VERSION
    p.setdefault('dials', {})
    for key in NEW_DIALS:
        p['dials'].setdefault(key, DIAL_DEFAULTS[key])
    return p


def _unique(values):
    result = []
    for value in values:
        if value not in result:
            result.append(copy.deepcopy(value))
    return result


def deep_merge(base, extra):
    """Deep language/format merge; protected lists cannot be cleared by a tone."""
    result = copy.deepcopy(base)
    for key, value in extra.items():
        if key in PROTECTED_LISTS:
            result[key] = _unique(result.get(key, []) + value)
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


_GUIDANCE = {
    'en': {
        'energy': ('Keep a still, measured pace.', 'Use calm, active sentences.',
                   'Use a steady everyday pace.', 'Use brisk, varied sentences.',
                   'Use a lively pace without adding urgency or punctuation.'),
        'directness': ('Give brief context before the main point.', 'Ease into the main point.',
                       'Balance context with a clear next step.', 'Lead with the answer or action.',
                       'State the answer and necessary next step immediately; stay respectful.'),
        'slang': ('Use familiar words without slang.', 'Use only widely understood informal expressions.',
                  'Use occasional audience-familiar idioms.', 'Use colloquial idioms when the audience expects them.',
                  'Use community idioms only with explicit audience fit; avoid exclusion or ridicule.')},
    'fa': {
        'energy': ('آرام و سنجیده پیش بروید.', 'جمله‌ها آرام و فعال باشند.',
                   'ریتم طبیعی و روزمره داشته باشید.', 'جمله‌ها چابک و متنوع باشند.',
                   'ریتم زنده باشد؛ فوریت یا علامت تعجب اضافه نکنید.'),
        'directness': ('پیش از نکتهٔ اصلی کمی زمینه بدهید.', 'با مقدمهٔ کوتاه به نکته برسید.',
                       'زمینه و اقدام بعدی را متعادل کنید.', 'با پاسخ یا اقدام اصلی شروع کنید.',
                       'پاسخ و قدم لازم را همان اول، محترمانه بگویید.'),
        'slang': ('واژه‌های آشنا، بدون اصطلاح کوچه به کار ببرید.', 'فقط تعبیر خودمانی و فراگیر بیاورید.',
                  'گاهی اصطلاح آشنای مخاطب بیاورید.', 'اصطلاح گفتاری را با شناخت مخاطب به کار ببرید.',
                  'اصطلاح خاص جمع فقط با تناسب روشن مخاطب؛ بدون تمسخر یا طرد.')}
}


def tone_instructions(dials, lang='fa'):
    """Deterministic writer guidance, not a claim that text generation was tested."""
    return {key: _GUIDANCE[lang][key][dials[key] - 1] for key in NEW_DIALS}


def resolve_profile(profile=None, lang='fa', fmt=None, preset=None, industry=None,
                    request=None, host_limits=None, industry_selected=False):
    """Resolve settings, preserving provenance and invariant claim restrictions.

    Industry is a fallback unless explicitly selected. A by_lang layer overrides
    its own parent; no language is inferred from another language's address rules.
    Format defaults only tighten caps; explicit format/request settings can relax
    those defaults. Host hard caps apply last and can only tighten.
    """
    if lang not in ('fa', 'en'):
        raise ProfileError('lang must be fa or en')
    if fmt is not None and fmt not in FORMAT_IDS:
        raise ProfileError('unknown format: %s' % fmt)
    if type(industry_selected) is not bool:
        raise ProfileError('industry_selected must be a boolean')
    documents = [('brand', profile), ('industry', industry), ('preset', preset), ('request', request)]
    for label, doc in documents:
        if doc is not None:
            errors = validate_profile(doc)
            if errors:
                raise ProfileError([{**e, 'path': label + e['path'][1:]} for e in errors])
    resolved, sources, trace, conflicts = {}, {}, [], []

    def record(path, before, value, source, policy='override'):
        sources[path] = source
        trace.append({'path': path, 'source': source, 'previous': copy.deepcopy(before),
                      'value': copy.deepcopy(value), 'policy': policy})

    def merge(target, layer, source, prefix=''):
        for key, value in layer.items():
            if key in ('schema_version', 'formats', 'by_lang'):
                continue
            path = prefix + key
            before = copy.deepcopy(target.get(key))
            if key in PROTECTED_LISTS:
                target[key] = _unique(target.get(key, []) + value)
                record(path, before, target[key], source, 'protected_union')
            elif key == 'fixed_facts':
                target.setdefault(key, {})
                for fact, fact_value in value.items():
                    fact_path = path + '.' + fact
                    if fact in target[key] and target[key][fact] != fact_value:
                        conflicts.append({'path': fact_path, 'source': source,
                                          'policy': 'immutable', 'kept': copy.deepcopy(target[key][fact]),
                                          'rejected': copy.deepcopy(fact_value)})
                    else:
                        old = target[key].get(fact)
                        target[key][fact] = copy.deepcopy(fact_value)
                        record(fact_path, old, fact_value, source, 'immutable')
            elif key == 'extensions':
                target[key] = copy.deepcopy(value)
                record(path, before, value, source, 'metadata')
            elif isinstance(value, dict):
                if not isinstance(target.get(key), dict):
                    target[key] = {}
                merge(target[key], value, source, path + '.')
            else:
                target[key] = copy.deepcopy(value)
                record(path, before, value, source)

    def apply(layer, source):
        layer = _canonical(layer)
        merge(resolved, layer, source)
        d = layer.get('dials', {})
        derived = {}
        if 'sentence_length' in d and 'max_words' not in layer:
            derived['max_words'] = WORD_CAPS[lang][d['sentence_length']]
        if 'loud_marks' in d:
            em, ex = MARK_CAPS[d['loud_marks']]
            if 'emoji_max' not in layer:
                derived['emoji_max'] = em
            if 'exclaim_max' not in layer:
                derived['exclaim_max'] = ex
        merge(resolved, derived, source + '.dials')

    defaults = {'language': lang, 'variant': 'fa-IR' if lang == 'fa' else 'en-US',
                'register': 'any', 'address': 'shoma' if lang == 'fa' else 'any',
                'dials': DIAL_DEFAULTS, 'banned': [], 'avoid': [], 'allow': [],
                'claim_boundaries': [], 'fixed_facts': {}}
    apply(defaults, 'default')
    active = []
    for label, doc in documents[:3]:
        if doc is None:
            continue
        if label == 'industry' and profile and not industry_selected:
            conflicts.append({'path': 'industry', 'source': 'industry', 'policy': 'brand_preserved',
                              'message': 'Automatic industry inference does not replace a brand profile.'})
            continue
        doc = _canonical(doc)
        active.append((label, doc))
        apply(doc, label)
        if lang in doc.get('by_lang', {}):
            apply(doc['by_lang'][lang], label + '.by_lang.' + lang)
    if fmt:
        # Import lazily: canonical defaults stay the existing lint contract.
        if lang == 'fa':
            import lint_fa
            fd = lint_fa.FORMAT_DEFAULTS.get(fmt, {})
        else:
            import lint_en
            fd = lint_en.EN_FORMAT_DEFAULTS.get(fmt, {})
        for key in ('max_words', 'emoji_max', 'exclaim_max'):
            if key in fd and fd[key] < resolved[key]:
                merge(resolved, {key: fd[key]}, 'format_default.' + fmt)
        for label, doc in active:
            if fmt in doc.get('formats', {}):
                apply(doc['formats'][fmt], label + '.formats.' + fmt)
            lang_formats = doc.get('by_lang', {}).get(lang, {}).get('formats', {})
            if fmt in lang_formats:
                apply(lang_formats[fmt], label + '.by_lang.' + lang + '.formats.' + fmt)
    if request is not None:
        apply(request, 'request')
        if lang in request.get('by_lang', {}):
            apply(request['by_lang'][lang], 'request.by_lang.' + lang)
        if fmt and fmt in request.get('formats', {}):
            apply(request['formats'][fmt], 'request.formats.' + fmt)
        request_formats = request.get('by_lang', {}).get(lang, {}).get('formats', {})
        if fmt and fmt in request_formats:
            apply(request_formats[fmt], 'request.by_lang.' + lang + '.formats.' + fmt)
    if host_limits is not None:
        errors = validate_profile(host_limits, partial=True)
        extra = set(host_limits) - {'max_words', 'emoji_max', 'exclaim_max'} if isinstance(host_limits, dict) else set()
        if errors or extra:
            raise ProfileError(errors or 'host_limits only accepts max_words, emoji_max, exclaim_max')
        for key, value in host_limits.items():
            if value < resolved[key]:
                conflicts.append({'path': key, 'source': 'host_limits', 'policy': 'ceiling',
                                  'requested': resolved[key], 'applied': value})
                merge(resolved, {key: value}, 'host_limits')
    # An allow-list may never excuse a banned word from any contributing layer.
    rejected = [word for word in resolved['allow'] if word in resolved['banned']]
    if rejected:
        conflicts.append({'path': 'allow', 'source': sources.get('allow'), 'policy': 'banned_wins',
                          'rejected': rejected})
        merge(resolved, {'allow': [x for x in resolved['allow'] if x not in rejected]}, 'invariant.banned')
    resolved['schema_version'] = SCHEMA_VERSION
    sources['schema_version'] = 'contract'
    return {'schema_version': SCHEMA_VERSION, 'profile': resolved, 'sources': sources,
            'trace': trace, 'conflicts': conflicts, 'instructions': tone_instructions(resolved['dials'], lang)}


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ProfileError('duplicate JSON key: %s' % key)
        value[key] = item
    return value


def read_profile(path):
    try:
        with open(path, 'rb') as fh:
            raw = fh.read()
        return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ProfileError('nonfinite JSON number')))
    except (UnicodeError, ValueError, OSError) as exc:
        if isinstance(exc, ProfileError):
            raise
        raise ProfileError('cannot read profile: %s' % exc)


def _preserve_custom(profile):
    p = copy.deepcopy(profile)
    if not isinstance(p, dict):
        return p

    def save(value, namespace, extra):
        if not extra:
            return
        ext = value.setdefault('extensions', {})
        if not isinstance(ext, dict):
            raise ProfileError('extensions must be an object before migration')
        saved = ext.setdefault(namespace, {})
        if not isinstance(saved, dict) or any(k in saved and saved[k] != v for k, v in extra.items()):
            raise ProfileError('custom fields conflict with extensions.' + namespace)
        saved.update(copy.deepcopy(extra))

    def move(value, allowed):
        if not isinstance(value, dict):
            return
        unknown = {k: value[k] for k in value if k not in allowed}
        save(value, 'legacy_fields', unknown)
        for key in unknown:
            del value[key]
        if isinstance(value.get('dials'), dict):
            bad = {k: v for k, v in value['dials'].items() if k not in DIAL_RANGES and k != 'rhetoric_dose'}
            save(value, 'legacy_dials', bad)
            for key in bad:
                del value['dials'][key]
        if isinstance(value.get('brand'), dict):
            bad = {k: v for k, v in value['brand'].items() if k not in ('fa', 'latin', 'misspellings')}
            save(value, 'legacy_brand_fields', bad)
            for key in bad:
                del value['brand'][key]
        if isinstance(value.get('formats'), dict):
            bad = {k: v for k, v in value['formats'].items() if k not in FORMAT_IDS}
            save(value, 'legacy_formats', bad)
            for key in bad:
                del value['formats'][key]
            for sub in value['formats'].values():
                move(sub, STYLE_KEYS)
        if isinstance(value.get('by_lang'), dict):
            bad = {k: v for k, v in value['by_lang'].items() if k not in ('fa', 'en')}
            save(value, 'legacy_by_lang', bad)
            for key in bad:
                del value['by_lang'][key]
            for sub in value['by_lang'].values():
                move(sub, STYLE_KEYS + ('formats',))

    move(p, ROOT_KEYS)
    return p


def migrate_document(profile):
    """Preserve legacy custom fields explicitly; reject unsupported future schemas."""
    if not isinstance(profile, dict):
        raise ProfileError('profile must be an object')
    version = profile.get('schema_version', 1)
    if type(version) is not int or version not in (1, 2, 3):
        raise ProfileError('supported schema versions are 1, 2 and 3')
    return normalize_profile(_preserve_custom(profile) if version < 3 else profile)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _atomic(path, data, mode=None):
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix='.whalory-profile-', dir=directory)
    try:
        with os.fdopen(fd, 'wb') as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def migrate_file(path, dry_run=True):
    """Default dry-run. Writes only this explicit file and adjacent backup/receipt."""
    path = os.path.abspath(path)
    if os.path.islink(path):
        raise ProfileError('migration requires a regular file, not a symbolic link')
    with open(path, 'rb') as fh:
        original = fh.read()
    profile = read_profile(path)
    migrated = migrate_document(profile)
    bom = original.startswith(b'\xef\xbb\xbf')
    newline = '\r\n' if b'\r\n' in original else '\n'
    changed = migrated != profile
    target = original if not changed else (b'\xef\xbb\xbf' if bom else b'') + (
        json.dumps(migrated, ensure_ascii=False, indent=2, allow_nan=False).replace('\n', newline)
        + (newline if original.endswith(b'\n') else '')).encode('utf-8')
    result = {'operation': 'migrate', 'dry_run': bool(dry_run), 'changed': changed,
              'from_version': profile.get('schema_version', 1), 'to_version': 3,
              'before_sha256': _sha(original), 'after_sha256': _sha(target),
              'bom': bom, 'newline': 'CRLF' if newline == '\r\n' else 'LF', 'profile': migrated}
    if dry_run or not changed:
        return result
    backup = path + '.v%s.%s.bak' % (result['from_version'], result['before_sha256'][:16])
    receipt = path + '.migration.json'
    if os.path.exists(receipt):
        raise ProfileError('migration receipt already exists; resolve or rollback the earlier migration first')
    if os.path.exists(backup):
        with open(backup, 'rb') as fh:
            if fh.read() != original:
                raise ProfileError('existing backup checksum does not match; refusing overwrite')
    else:
        with open(backup, 'xb') as fh:
            fh.write(original)
    record = {k: v for k, v in result.items() if k != 'profile'}
    record.update({'path': path, 'backup': backup, 'receipt_version': 1})
    with open(receipt, 'x', encoding='utf-8', newline='\n') as fh:
        json.dump(record, fh, ensure_ascii=False, indent=2)
        fh.write('\n')
    # Do not overwrite a concurrent user edit between validation and replacement.
    with open(path, 'rb') as fh:
        if fh.read() != original:
            raise ProfileError('profile changed during migration; original backup retained')
    _atomic(path, target, os.stat(path).st_mode)
    result.update({'backup': backup, 'receipt': receipt})
    return result


def rollback_file(path, dry_run=True):
    """Restore exact original bytes only if the current file still matches the receipt."""
    path = os.path.abspath(path)
    receipt = path + '.migration.json'
    with io.open(receipt, encoding='utf-8') as fh:
        record = json.load(fh)
    expected_backup = path + '.v%s.%s.bak' % (record['from_version'], record['before_sha256'][:16])
    if record.get('path') != path or record.get('backup') != expected_backup or os.path.islink(path):
        raise ProfileError('receipt does not identify this regular profile file and adjacent backup')
    with open(expected_backup, 'rb') as fh:
        original = fh.read()
    with open(path, 'rb') as fh:
        current = fh.read()
    if _sha(original) != record['before_sha256']:
        raise ProfileError('backup checksum mismatch')
    current_sha = _sha(current)
    if current_sha not in (record['after_sha256'], record['before_sha256']):
        raise ProfileError('profile changed since migration; rollback would overwrite user changes')
    changed = current_sha != record['before_sha256']
    if changed and not dry_run:
        _atomic(path, original, os.stat(path).st_mode)
    return {'operation': 'rollback', 'dry_run': bool(dry_run), 'changed': changed,
            'before_sha256': current_sha, 'after_sha256': record['before_sha256']}


def profile_schema():
    """JSON Schema 2020-12 used by web/server adapters; matches schema3 validation."""
    string_list = {'type': 'array', 'items': {'type': 'string'}}
    string_map = {'type': 'object', 'propertyNames': {'minLength': 1}, 'additionalProperties': {'type': 'string'}}
    props = {key: {'enum': list(vals) + ([None] if key in NULLABLE else [])} for key, vals in ENUMS.items()}
    props.update({key: {'type': 'string'} for key in ('name', 'industry', 'note')})
    props['schema_version'] = {'type': 'integer', 'const': 3}
    props['dials'] = {'type': 'object', 'additionalProperties': False, 'properties': {
        key: {'type': 'integer', 'minimum': bounds[0], 'maximum': bounds[1], 'default': DIAL_DEFAULTS[key]}
        for key, bounds in DIAL_RANGES.items()}}
    for key in ('max_words', 'emoji_max', 'exclaim_max'):
        props[key] = {'type': 'integer', 'minimum': 1 if key == 'max_words' else 0}
    props['reading_grade_max'] = {'type': ['number', 'null'], 'minimum': 4, 'maximum': 16}
    props['oxford_comma'] = {'type': ['boolean', 'null']}
    props.update({key: copy.deepcopy(string_list) for key in WORD_LISTS})
    props.update({key: copy.deepcopy(string_map) for key in STRING_MAPS})
    props['variants'] = {'type': 'array', 'items': {'enum': list(ENUMS['variant'])}}
    props['brand'] = {'type': 'object', 'additionalProperties': False, 'properties': {
        'fa': {'type': 'string'}, 'latin': {'type': 'string'}, 'misspellings': string_map}}
    props['extensions'] = {'type': 'object', 'description': 'Custom metadata; never interpreted as tone or claims.'}
    props['fixed_facts'] = {'type': 'object', 'description': 'Immutable facts keyed by a stable identifier.'}
    style = {'type': 'object', 'additionalProperties': False,
             'properties': {key: copy.deepcopy(props[key]) for key in STYLE_KEYS}}
    formats = {'type': 'object', 'additionalProperties': False,
               'properties': {key: {'$ref': '#/$defs/style'} for key in FORMAT_IDS}}
    lang_style = copy.deepcopy(style)
    lang_style['properties']['formats'] = copy.deepcopy(formats)
    props['formats'] = formats
    props['by_lang'] = {'type': 'object', 'additionalProperties': False,
                        'properties': {key: {'$ref': '#/$defs/languageStyle'} for key in ('fa', 'en')}}
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema',
            '$id': 'urn:whalory:voice-profile:3',
            'title': 'Whalory voice profile schema 3', 'type': 'object',
            'required': ['schema_version'], 'additionalProperties': False, 'properties': props,
            '$defs': {'style': style, 'languageStyle': lang_style},
            'allOf': [{'if': {'required': ['variant', 'variants'],
                              'properties': {'variant': {'const': variant}, 'variants': {'minItems': 1}}},
                       'then': {'properties': {'variants': {'contains': {'const': variant}}}}}
                      for variant in ENUMS['variant']]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    subs = ap.add_subparsers(dest='command', required=True)
    for name in ('validate', 'normalize', 'migrate', 'rollback'):
        cmd = subs.add_parser(name, help=name + ' an explicit JSON profile path')
        cmd.add_argument('path')
        if name in ('migrate', 'rollback'):
            group = cmd.add_mutually_exclusive_group()
            group.add_argument('--write', action='store_true', help='write after validation; default is dry-run')
            group.add_argument('--dry-run', action='store_true', help='preview without any writes (default)')
    subs.add_parser('schema', help='print the portable JSON schema')
    cmd = subs.add_parser('resolve', help='resolve layered profiles with sources and trace')
    cmd.add_argument('--profile')
    cmd.add_argument('--lang', choices=('fa', 'en'), default='fa')
    cmd.add_argument('--format', choices=FORMAT_IDS)
    for name in ('preset', 'industry', 'request', 'host-limits'):
        cmd.add_argument('--' + name, help='explicit JSON file')
    cmd.add_argument('--industry-selected', action='store_true')
    args = ap.parse_args(argv)
    try:
        if args.command == 'schema':
            result = profile_schema()
        elif args.command == 'resolve':
            values = {key: read_profile(getattr(args, key)) if getattr(args, key) else None
                      for key in ('profile', 'preset', 'industry', 'request', 'host_limits')}
            result = resolve_profile(lang=args.lang, fmt=args.format, industry_selected=args.industry_selected, **values)
        elif args.command in ('migrate', 'rollback'):
            fn = migrate_file if args.command == 'migrate' else rollback_file
            result = fn(args.path, dry_run=not args.write)
        else:
            profile = read_profile(args.path)
            if args.command == 'validate':
                errors = validate_profile(profile)
                result = {'valid': not errors, 'errors': errors}
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 2 if errors else 0
            result = normalize_profile(profile)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ProfileError, OSError, ValueError, KeyError) as exc:
        errors = exc.issues if isinstance(exc, ProfileError) else [{'path': '$', 'code': 'io', 'message': str(exc)}]
        print(json.dumps({'valid': False, 'errors': errors}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
