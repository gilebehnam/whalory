#!/usr/bin/env python3
"""Offline contract tests for profile readers, resolution and reversible migration."""
import ast
import codecs
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import voice_profile as VP
import lint as L
import lint_fa as LF
import lint_en as LE


class Profiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='whalory-profile-tests-')
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args):
        return subprocess.run([sys.executable, str(HERE / 'voice_profile.py')] + list(args),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env=dict(os.environ, PYTHONIOENCODING='utf-8'), timeout=15)

    def test_01_v1_v2_read_without_mutation(self):
        for version in (None, 1, 2):
            p = {'name': 'legacy', 'dials': {'warmth': 4, 'loud_marks': 0},
                 'register': 'written', 'address': 'شما'}
            if version is not None:
                p['schema_version'] = version
            old = copy.deepcopy(p)
            n = VP.normalize_profile(p)
            self.assertEqual(n['schema_version'], 3)
            self.assertEqual(n['dials'], {'warmth': 4, 'loud_marks': 0, 'energy': 3, 'directness': 3, 'slang': 1})
            self.assertEqual((n['register'], n['address']), ('formal', 'shoma'))
            self.assertEqual(p, old)

    def test_02_strict_types_and_ranges(self):
        for key, (lo, hi) in VP.DIAL_RANGES.items():
            for bad in (True, False, None, '3', 2.5, lo - 1, hi + 1):
                p = {'schema_version': 3, 'dials': {key: bad}}
                with self.subTest(dial=key, bad=bad):
                    self.assertTrue(VP.validate_profile(p))
                    with self.assertRaises(VP.ProfileError):
                        VP.normalize_profile(p)
            self.assertFalse(VP.validate_profile({'dials': {key: lo}}))
            self.assertFalse(VP.validate_profile({'dials': {key: hi}}))

    def test_03_invalid_containers_future_and_unknown(self):
        invalid = [None, [], True, {'schema_version': True}, {'schema_version': None},
                   {'schema_version': 4}, {'dials': None}, {'formats': None}, {'brand': None},
                   {'max_words': True}, {'max_words': 0}, {'register': None}, {'by_lang': []},
                   {'by_lang': {'en': None}}, {'by_lang': {'fr': {}}}, {'dials': {'speed': 3}},
                   {'warmth': 4}, {'formats': {'caption': {'typo': 4}}},
                   {'formats': {'caption': {'dials': {'slang': False}}}}]
        for p in invalid:
            with self.subTest(profile=p):
                self.assertTrue(VP.validate_profile(p))
                with self.assertRaises(VP.ProfileError):
                    VP.normalize_profile(p)
        self.assertFalse(VP.validate_profile({'spelling': None, 'oxford_comma': None,
                                             'reading_grade_max': None, 'extensions': {'custom': None}}))

    def test_04_schema_portable_and_38_syntax(self):
        published = json.loads((ROOT / 'data' / 'voice-profile.schema.json').read_text(encoding='utf-8-sig'))
        self.assertEqual(published, VP.profile_schema())
        self.assertEqual(set(published['properties']['dials']['properties']), set(VP.DIAL_DEFAULTS))
        self.assertFalse(published['additionalProperties'])
        ast.parse((HERE / 'voice_profile.py').read_text(encoding='utf-8'), feature_version=(3, 8))

    def test_05_language_format_merge_deep(self):
        p = {'schema_version': 3, 'dials': {'warmth': 2, 'slang': 1},
             'banned': ['global'], 'formats': {'caption': {'dials': {'warmth': 4, 'energy': 2}}},
             'by_lang': {'en': {'dials': {'directness': 5}, 'banned': ['local'],
                                'formats': {'caption': {'dials': {'slang': 2}}}}}}
        r = VP.resolve_profile(p, lang='en', fmt='caption')
        self.assertEqual({k: r['profile']['dials'][k] for k in ('warmth', 'energy', 'slang', 'directness')},
                         {'warmth': 4, 'energy': 2, 'slang': 2, 'directness': 5})
        self.assertEqual(r['sources']['dials.slang'], 'brand.by_lang.en.formats.caption')
        self.assertEqual(r['profile']['banned'], ['global', 'local'])
        merged = LF.merge_by_lang(p, 'en')
        self.assertEqual(merged['formats']['caption']['dials'], {'warmth': 4, 'energy': 2, 'slang': 2})

    def test_06_brand_blocks_auto_industry(self):
        brand = {'dials': {'warmth': 4}, 'name': 'approved'}
        industry = {'dials': {'warmth': 1}, 'name': 'inferred'}
        r = VP.resolve_profile(brand, industry=industry)
        self.assertEqual(r['profile']['dials']['warmth'], 4)
        self.assertEqual(r['conflicts'][0]['policy'], 'brand_preserved')
        self.assertEqual(VP.resolve_profile(industry=industry)['profile']['dials']['warmth'], 1)
        self.assertEqual(VP.resolve_profile(brand, industry=industry, industry_selected=True)['profile']['dials']['warmth'], 1)

    def test_07_full_precedence_and_immutable_claims(self):
        p = {'name': 'approved', 'dials': {'warmth': 1}, 'banned': ['guaranteed'],
             'claim_boundaries': ['source required'], 'fixed_facts': {'price': 125, 'name': 'Acme'},
             'by_lang': {'fa': {'dials': {'warmth': 2}}},
             'formats': {'caption': {'dials': {'warmth': 4}, 'max_words': 28}}}
        preset = {'dials': {'warmth': 3}, 'banned': ['best ever']}
        req = {'dials': {'warmth': 5}, 'banned': [], 'claim_boundaries': [],
               'allow': ['guaranteed', 'normal'], 'fixed_facts': {'price': 126}, 'max_words': 40}
        r = VP.resolve_profile(p, fmt='caption', preset=preset, request=req, host_limits={'max_words': 22})
        self.assertEqual(r['profile']['dials']['warmth'], 5)
        self.assertEqual(r['profile']['max_words'], 22)
        self.assertEqual(r['sources']['dials.warmth'], 'request')
        self.assertEqual(r['sources']['max_words'], 'host_limits')
        self.assertEqual(r['profile']['banned'], ['guaranteed', 'best ever'])
        self.assertEqual(r['profile']['claim_boundaries'], ['source required'])
        self.assertEqual(r['profile']['fixed_facts'], {'price': 125, 'name': 'Acme'})
        self.assertEqual(r['profile']['allow'], ['normal'])
        self.assertEqual([e['value'] for e in r['trace'] if e['path'] == 'dials.warmth'], [3, 1, 2, 3, 4, 5])
        self.assertEqual({c['policy'] for c in r['conflicts']}, {'immutable', 'ceiling', 'banned_wins'})
        self.assertEqual(p['banned'], ['guaranteed'])

    def test_08_defaults_cap_then_explicit_format(self):
        p = {'dials': {'sentence_length': 5}, 'formats': {'caption': {'max_words': 28}}}
        for lang in ('fa', 'en'):
            r = VP.resolve_profile(p, lang=lang, fmt='caption')
            self.assertEqual(r['profile']['max_words'], 28)
            self.assertEqual(r['sources']['max_words'], 'brand.formats.caption')
            self.assertTrue(any(x['source'] == 'format_default.caption' for x in r['trace']))
        with self.assertRaises(VP.ProfileError):
            VP.resolve_profile(host_limits={'warmth': 4})

    def test_09_new_dials_independent_bilingual_guidance(self):
        for lang in ('fa', 'en'):
            baseline = VP.resolve_profile({'register': 'colloquial'}, lang=lang)
            for dial in VP.NEW_DIALS:
                results = [VP.resolve_profile({'register': 'colloquial', 'dials': {dial: n}}, lang=lang)
                           for n in range(1, 6)]
                self.assertEqual(len({r['instructions'][dial] for r in results}), 5)
                for r in results:
                    self.assertEqual(r['profile']['register'], 'colloquial')
                    self.assertEqual(r['profile']['emoji_max'], 0)
                    self.assertEqual(r['profile']['exclaim_max'], 0)
                    for other in VP.NEW_DIALS:
                        if other != dial:
                            self.assertEqual(r['instructions'][other], baseline['instructions'][other])

    def test_10_existing_profiles_validate_and_old_lint_behavior(self):
        paths = list((ROOT / 'profiles').rglob('*.json'))
        self.assertTrue((ROOT / 'profiles' / 'whalory.json') in paths)
        self.assertTrue((ROOT / 'profiles' / 'whalory.en.json') in paths)
        for path in paths:
            p = VP.read_profile(str(path))
            with self.subTest(path=path.name):
                self.assertFalse(VP.validate_profile(p))
                n = VP.normalize_profile(p)
                for lang, checker, text in [('fa', LF, 'این متن کوتاه است.'), ('en', LE, 'Your draft is ready.')]:
                    a = checker.resolve_settings(p)
                    b = checker.resolve_settings(n)
                    for key in ('max_words', 'emoji_max', 'exclaim_max'):
                        self.assertEqual(a[key], b[key])
                    ia = [(x['code'], x['line']) for x in checker.lint(text, profile=p)[0]]
                    ib = [(x['code'], x['line']) for x in checker.lint(text, profile=n)[0]]
                    self.assertEqual(ia, ib)

    def test_11_golden_cafe_saas_and_house(self):
        for lang, sub in [('fa', ''), ('en', 'en/')]:
            for slug in ('cafe', 'saas'):
                p = VP.read_profile(str(ROOT / 'profiles' / 'starters' / (sub + slug + '.json')))
                r = VP.resolve_profile(p, lang=lang, fmt='caption')
                old = (LF if lang == 'fa' else LE).resolve_settings(p, fmt='caption')
                self.assertEqual(r['profile']['max_words'], old['max_words'])
                self.assertEqual(r['profile']['emoji_max'], old['emoji_max'])
        p = VP.read_profile(str(ROOT / 'profiles' / 'whalory.json'))
        self.assertEqual(p['register'], 'colloquial')
        self.assertEqual(p['address'], 'shoma')
        self.assertEqual(list(p['dials'].values()), [4, 2, 2, 2, 2, 0, 1, 2, 2, 4, 1])
        for fid in VP.FORMAT_IDS:
            self.assertEqual(VP.resolve_profile(p, fmt=fid)['profile']['address'], 'shoma')
        en = VP.read_profile(str(ROOT / 'profiles' / 'whalory.en.json'))
        self.assertEqual(en['address'], 'any')
        self.assertEqual(en['max_words'], 20)
        self.assertEqual(en['dials']['humor'], 1)

    def test_12_migration_bom_crlf_dryrun_idempotent_rollback(self):
        p = {'schema_version': 2, 'name': 'café', 'register': 'colloquial',
             'dials': {'warmth': 4, 'loud_marks': 0}, 'custom': {'nested': [1, None, 'متن']},
             'formats': {'caption': {'custom_note': 'keep', 'dials': {'energy': 2}}}}
        path = self.root / 'نام با فاصله.json'
        original = codecs.BOM_UTF8 + (json.dumps(p, ensure_ascii=False, indent=2).replace('\n', '\r\n') + '\r\n').encode('utf-8')
        path.write_bytes(original)
        before = list(self.root.iterdir())
        dry = VP.migrate_file(str(path))
        self.assertTrue(dry['changed'])
        self.assertEqual(list(self.root.iterdir()), before)
        self.assertEqual(path.read_bytes(), original)
        result = VP.migrate_file(str(path), dry_run=False)
        self.assertEqual(Path(result['backup']).read_bytes(), original)
        target = path.read_bytes()
        self.assertTrue(target.startswith(codecs.BOM_UTF8))
        self.assertNotIn(b'\n', target.replace(b'\r\n', b''))
        migrated = VP.read_profile(str(path))
        self.assertEqual(migrated['extensions']['legacy_fields']['custom'], p['custom'])
        self.assertEqual(migrated['formats']['caption']['extensions']['legacy_fields']['custom_note'], 'keep')
        self.assertFalse(VP.migrate_file(str(path), dry_run=False)['changed'])
        self.assertEqual(path.read_bytes(), target)
        self.assertTrue(VP.rollback_file(str(path))['changed'])
        self.assertEqual(path.read_bytes(), target)
        self.assertTrue(VP.rollback_file(str(path), dry_run=False)['changed'])
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse(VP.rollback_file(str(path), dry_run=False)['changed'])

    def test_13_migration_checksum_and_user_edit_guards(self):
        path = self.root / 'voice.json'
        path.write_text('{"schema_version":2,"name":"test"}', encoding='utf-8')
        result = VP.migrate_file(str(path), dry_run=False)
        migrated = path.read_bytes()
        path.write_bytes(migrated + b' ')
        with self.assertRaises(VP.ProfileError):
            VP.rollback_file(str(path), dry_run=False)
        path.write_bytes(migrated)
        Path(result['backup']).write_bytes(b'corrupt')
        with self.assertRaises(VP.ProfileError):
            VP.rollback_file(str(path), dry_run=False)
        self.assertEqual(path.read_bytes(), migrated)

    def test_14_corrupt_duplicate_and_nonfinite_json(self):
        for raw in (b'{', b'\xff', b'{"name":"a","name":"b"}', b'{"max_words":NaN}'):
            path = self.root / 'bad.json'
            path.write_bytes(raw)
            with self.assertRaises(VP.ProfileError):
                VP.read_profile(str(path))
            with self.assertRaises((VP.ProfileError, ValueError)):
                VP.migrate_file(str(path), dry_run=False)
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_15_lint_schema3_and_invalid_profile_cli(self):
        path = self.root / 'profile.json'
        for invalid in ({'schema_version': 3, 'dials': {'energy': True}}, {'schema_version': 99},
                        {'schema_version': 3, 'typo': 4},
                        {'schema_version': 3, '_normalized': True, 'dials': {'energy': False}}):
            path.write_text(json.dumps(invalid), encoding='utf-8')
            for script in ('lint.py', 'lint_fa.py', 'lint_en.py'):
                cp = subprocess.run([sys.executable, str(HERE / script), '--text', 'Hello.', '--profile', str(path), '--json'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
                                    env=dict(os.environ, PYTHONIOENCODING='utf-8'))
                self.assertEqual(cp.returncode, 2, cp.stderr.decode('utf-8'))
                self.assertNotIn(b'Traceback', cp.stderr)
        p = L.load_profile(str(ROOT / 'profiles' / 'whalory.json'))
        self.assertFalse(LF.validate_profile(p))
        self.assertEqual(LF.resolve_settings(p)['dials']['energy'], 2)
        resolved = L.resolve_profile(p, fmt='caption')
        self.assertEqual(resolved['profile']['max_words'], 18)
        self.assertFalse(VP.validate_profile(resolved['profile']))
        self.assertFalse(L.lint_text('متن شما آماده شده.', lang='fa', profile=resolved['profile'])[1]['errors'])
        for checker in (LF, LE):
            self.assertTrue(checker.validate_profile({'dials': {'unknown': 3}}))

    def test_16_cli_help_happy_bad_and_exit(self):
        self.assertEqual(self.cli('--help').returncode, 0)
        self.assertEqual(self.cli('resolve', '--lang', 'xx').returncode, 2)
        self.assertEqual(self.cli('validate', str(self.root / 'missing.json')).returncode, 2)
        happy = self.cli('resolve', '--profile', str(ROOT / 'profiles' / 'whalory.json'), '--format', 'caption')
        self.assertEqual(happy.returncode, 0, happy.stderr.decode('utf-8'))
        self.assertEqual(json.loads(happy.stdout)['profile']['address'], 'shoma')
        self.assertEqual(self.cli('schema').returncode, 0)
        bad = self.root / 'bad.json'
        bad.write_text('{"schema_version":3,"dials":{"energy":null}}', encoding='utf-8')
        cp = self.cli('validate', str(bad))
        self.assertEqual(cp.returncode, 2)
        self.assertFalse(json.loads(cp.stdout)['valid'])

    def test_17_nested_custom_fields_preserved_and_legacy_aliases(self):
        old = {'schema_version': 2, 'brand': {'latin': 'Test', 'custom_id': 12},
               'dials': {'rhetoric_dose': 2, 'legacy_speed': 4},
               'formats': {'custom-format': {'length': 8}},
               'by_lang': {'fr': {'name': 'custom'}, 'fa': {'custom_style': True}},
               'extensions': {'owner': 'local'}}
        n = VP.migrate_document(old)
        self.assertEqual(n['extensions']['legacy_brand_fields'], {'custom_id': 12})
        self.assertEqual(n['extensions']['legacy_formats'], {'custom-format': {'length': 8}})
        self.assertEqual(n['extensions']['legacy_by_lang'], {'fr': {'name': 'custom'}})
        self.assertEqual(n['extensions']['legacy_dials'], {'legacy_speed': 4})
        self.assertEqual(n['by_lang']['fa']['extensions']['legacy_fields'], {'custom_style': True})
        self.assertEqual(n['dials']['rhetoric'], 2)
        self.assertEqual(n, VP.migrate_document(n))
        self.assertTrue(VP.validate_profile({'schema_version': 3, 'register': 'written'}))
        self.assertTrue(VP.validate_profile({'schema_version': 3, 'dials': {'rhetoric_dose': 2}}))
        with self.assertRaises(VP.ProfileError):
            VP.migrate_document({'schema_version': 2, 'typo': 1, 'extensions': {'legacy_fields': {'typo': 2}}})

    def test_18_lf_no_final_newline_and_metadata_no_interpretation(self):
        path = self.root / 'plain.json'
        original = b'{"schema_version": 1, "name": "plain"}'
        path.write_bytes(original)
        VP.migrate_file(str(path), dry_run=False)
        self.assertFalse(path.read_bytes().endswith(bytes([10])))
        self.assertNotIn(bytes([13]), path.read_bytes())
        VP.rollback_file(str(path), dry_run=False)
        self.assertEqual(path.read_bytes(), original)
        metadata = {'schema_version': 99, 'formats': None, 'banned': 'metadata only'}
        r = VP.resolve_profile({'extensions': metadata})
        self.assertEqual(r['profile']['extensions'], metadata)
        self.assertEqual(r['profile']['banned'], [])
        request = {'formats': {'caption': {'dials': {'energy': 1}}},
                   'by_lang': {'en': {'formats': {'caption': {'dials': {'energy': 5}}}}}}
        r = VP.resolve_profile(fmt='caption', lang='en', request=request)
        self.assertEqual(r['profile']['dials']['energy'], 5)
        self.assertEqual(r['sources']['dials.energy'], 'request.by_lang.en.formats.caption')

    def test_19_six_bilingual_examples_and_disclosed_warning(self):
        examples = json.loads((HERE / 'samples' / 'profile-v3-examples.json').read_text(encoding='utf-8'))
        self.assertEqual(len(examples['cases']), 6)
        for row in examples['cases']:
            self.assertTrue(row['facts'])
            for lang in ('fa', 'en'):
                filename = 'whalory.json' if lang == 'fa' else 'whalory.en.json'
                p = L.load_profile(str(ROOT / 'profiles' / filename))
                issues, _, _ = L.lint_text(row[lang]['after'], lang=lang, profile=p, fmt=row['format'])
                self.assertFalse([i for i in issues if i['level'] == 'error'])
                expected = ['rhetorical-open'] if row['id'] == 'brief' and lang == 'fa' else []
                self.assertEqual([i['code'] for i in issues], expected)
        live = [r for r in examples['cases'] if r['id'] == 'live-caption'][0]
        for stage in ('before', 'after'):
            self.assertIn('۱۸', live['fa'][stage])
            self.assertIn('18:00', live['en'][stage])
            self.assertIn('فردا', live['fa'][stage])
            self.assertIn('tomorrow', live['en'][stage])


class Results(unittest.TestResult):
    def __init__(self):
        super(Results, self).__init__()
        self.records = []

    def addSuccess(self, test):
        super(Results, self).addSuccess(test)
        self.records.append((test._testMethodName, True, ''))

    def addFailure(self, test, err):
        super(Results, self).addFailure(test, err)
        self.records.append((test._testMethodName, False, self._exc_info_to_string(err, test)))

    def addError(self, test, err):
        super(Results, self).addError(test, err)
        self.records.append((test._testMethodName, False, self._exc_info_to_string(err, test)))

    def addSubTest(self, test, subtest, err):
        super(Results, self).addSubTest(test, subtest, err)
        if err is not None:
            self.records.append((str(subtest), False, self._exc_info_to_string(err, test)))


def run():
    result = Results()
    unittest.defaultTestLoader.loadTestsFromTestCase(Profiles).run(result)
    return result.records


if __name__ == '__main__':
    result = run()
    for name, ok, detail in result:
        print(('PASS ' if ok else 'FAIL ') + name)
        if detail:
            print(detail)
    failed = sum(not ok for _, ok, _ in result)
    print(json.dumps({'passed': len(result) - failed, 'failed': failed, 'skipped': 0}))
    sys.exit(1 if failed else 0)
