#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_en: tests for lint_en, the lint dispatcher and textcount (Whalory 3.1.0).

    python scripts/selftest_en.py

run() returns [(name, ok, detail)], like selftest_tools; selftest.py runs it and counts the
results. Standard library only, Python 3.8+. Covers spec §D.7: every rule has a positive and
a negative case, the good/bad samples, locale and CSV fixtures, readability, parity with
lint_fa, mixed mode, --fix, profiles, channels, speed and import hygiene.
"""
from __future__ import print_function

import sys

if sys.version_info < (3, 8):
    sys.stderr.write('selftest_en needs Python 3.8 or newer (found %s).\n' % sys.version.split()[0])
    sys.exit(2)
sys.dont_write_bytecode = True  # no __pycache__ next to the scripts: a skill or plugin folder may be read-only

import ast  # noqa: E402
import codecs  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['WHALORY_HUB_OVERLAY'] = '0'  # built-in rules only (Hub spec 5.9), whatever the Hub folder holds
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import lint_fa as LF  # noqa: E402
import lint_en as LE  # noqa: E402
import lint as LD  # noqa: E402
import textcount as TC  # noqa: E402

S = os.path.join(HERE, 'samples')
SE = os.path.join(S, 'en')
SM = os.path.join(S, 'mixed')
CH = os.path.join(SE, 'channels')


def _read(path):
    with io.open(path, encoding='utf-8') as fh:
        return fh.read()


def _prof(name):
    return LD.load_profile(os.path.join(SE, name))


def _cli(script, args, stdin=None, env_extra=None):
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    env.pop('WHALORY_DEBUG', None)
    env.pop('WHALYA_DEBUG', None)
    env.update(env_extra or {})
    r = subprocess.run([sys.executable, os.path.join(HERE, script)] + list(args), input=stdin,
                       capture_output=True, env=env)
    return r.returncode, r.stdout.decode('utf-8', 'replace'), r.stderr.decode('utf-8', 'replace')


def _codes(text, **kw):
    channel = kw.pop('channel', None)
    if isinstance(channel, str):
        channel = LF.resolve_channel(channel, CH)
    prof = kw.pop('profile', None)
    if isinstance(prof, str):
        prof = _prof(prof)
    issues, _ = LE.lint(text, profile=prof, channel=channel, **kw)
    return [x['code'] for x in issues]


# 60+ plain words used to reach the word-count gates without triggering anything
_FILL = ('Marlo Coffee roasts beans in a small shop on Fifth Street. We buy green coffee from two farms. '
         'Each bag shows the roast date. Most customers finish a bag within three weeks. You can order online '
         'before noon and we ship the same day. Local orders come by bike. If a bag arrives damaged, write to '
         'us with a photo. We send a new one or refund you. ')
_HARD = ('The committee evaluated alternative distribution strategies for international markets. Management '
         'identified significant operational risks, particularly regarding regulatory requirements. ')

# (rule, text, keyword arguments for lint_en.lint, expected: True = the rule fires)
CASES = [
    ('en-ai-vocab', 'This study delves into the data.', {}, True),
    ('en-ai-vocab', 'We dug into the data.', {}, False),
    ('en-ai-vocab', 'The underscore character is _.', {}, False),
    ('en-ai-vocab-density', _FILL * 3 + 'We delve into the tapestry of pivotal and meticulous work.', {}, True),
    ('en-ai-vocab-density', _FILL + _FILL, {}, False),
    ('en-buzzword', 'Our robust platform empowers teams.', {}, True),
    ('en-buzzword', 'The bridge is structurally sound.', {}, False),
    ('en-buzzword', 'Our robust tool is ready.', {'profile': 'profile-us.json'}, False),
    ('en-significance', 'It plays a vital role in the ecosystem.', {}, True),
    ('en-significance', 'The pump moves water.', {}, False),
    ('en-copula-avoid', 'Gallery 825 serves as the exhibition space.', {}, True),
    ('en-copula-avoid', 'Gallery 825 is the exhibition space.', {}, False),
    ('en-ing-analysis', "Sales rose in May, highlighting the brand's appeal.", {}, True),
    ('en-ing-analysis', 'Sales rose in May.', {}, False),
    ('en-vague-attribution', 'Experts argue that the policy failed.', {}, True),
    ('en-vague-attribution', 'Dr. Lee argued that the policy failed.', {}, False),
    ('en-vague-attribution', 'Experts argue that the policy failed (https://example.com/report).', {}, False),
    ('en-media-canned', 'She has been featured in numerous outlets.', {}, True),
    ('en-media-canned', 'Wired interviewed her in March.', {}, False),
    ('en-not-just', "It's not just a tool, but a way of life.", {}, True),
    ('en-not-just', 'It is a tool for cutting drywall.', {}, False),
    ('en-not-x-but-y', "This isn't about speed. It's about trust.", {}, True),
    ('en-not-x-but-y', 'The fee is not refundable, but you can cancel.', {}, False),
    ('en-no-x-no-y', 'No fluff, no filler, just results.', {}, True),
    ('en-no-x-no-y', 'The report had no filler.', {}, False),
    ('en-triads', _FILL + 'We sell apples, pears, and plums. We also sell bread, milk, and eggs.', {}, True),
    ('en-triads', _FILL, {}, False),
    ('en-dash-density', 'A tool—fast—cheap.', {}, True),
    ('en-dash-density', 'A fast, cheap tool.', {}, False),
    ('en-summary-opener', 'In conclusion, the plan works.', {}, True),
    ('en-summary-opener', 'The overall budget is small.', {}, False),
    ('en-challenges-outlook', 'Despite its success, the company faces several challenges.', {}, True),
    ('en-challenges-outlook', 'The company lost two contracts.', {}, False),
    ('en-didactic', "It's important to note that fees apply.", {}, True),
    ('en-didactic', 'Fees apply.', {}, False),
    ('en-chatbot-residue', 'Certainly! Here is a revised version of the text.', {}, True),
    ('en-chatbot-residue', 'We hope the new schedule helps commuters.', {}, False),
    ('en-chatbot-residue', 'Let me know if you have questions.', {}, True),
    ('en-chatbot-residue', 'Let me know if you have questions.', {'fmt': 'email'}, False),
    ('en-cutoff-speculation', 'As of my last knowledge update, the CEO is Jane Doe.', {}, True),
    ('en-cutoff-speculation', 'The CEO is Jane Doe (company site).', {}, False),
    ('en-template-residue', 'Contact [Your Name] at TBD.', {}, True),
    ('en-template-residue', 'Hello {{name}}, your order shipped.', {}, True),
    ('en-template-residue', 'Contact Sara at Acme. The price is [confirm: price].', {}, False),
    ('en-chatbot-markup', 'Revenue grew.:contentReference[oaicite:0]{index=0}', {}, True),
    ('en-chatbot-markup', 'See the annual report.', {}, False),
    ('en-title-case-heading', '## Impact of Technology and Digitalization\n\nText here.', {'kind': 'md'}, True),
    ('en-title-case-heading', '## Impact of technology on trade law\n\nText here.', {'kind': 'md'}, False),
    ('en-title-case-heading', '## Impact of Technology and Digitalization\n\nText here.',
     {'kind': 'md', 'settings': 'house:chicago'}, False),
    ('en-title-case-heading', '## Impact of Technology and Digitalization\n\nText here.',
     {'kind': 'md', 'settings': 'house:ap'}, True),
    ('en-bold-overuse', 'We offer **speed**, **trust** and **scale** for teams.', {'kind': 'md'}, True),
    ('en-bold-overuse', 'We offer speed for teams.', {'kind': 'md'}, False),
    ('en-inline-header-bullets', '- **Speed:** fast loading.\n- **Trust:** audited code.\n- **Scale:** many users.',
     {'kind': 'md'}, True),
    ('en-inline-header-bullets', '- fast loading\n- audited code\n- many users', {'kind': 'md'}, False),
    ('en-emoji-format', '✅ Fast setup', {}, True),
    ('en-emoji-format', 'Fast setup', {}, False),
    ('en-emoji-format', '✅ Fast setup', {'fmt': 'caption'}, False),
    ('en-quote-mix', 'He said "yes" and it’s done.', {}, True),
    ('en-quote-mix', 'He said "yes" and it\'s done.', {}, False),
    ('en-vague-association', 'He was associated with leadership of ExampleCorp.', {}, True),
    ('en-vague-association', 'He was chief executive of ExampleCorp.', {}, False),
    ('en-additionally', 'Additionally, it scales. Moreover, it syncs.', {}, True),
    ('en-additionally', 'It also scales.', {}, False),
    ('en-marketing-has', 'The hotel boasts a rooftop pool.', {}, True),
    ('en-marketing-has', 'The hotel has a rooftop pool.', {}, False),
    ('en-marketing-has', 'The hotel boasts a rooftop pool.', {'fmt': 'ad'}, False),
    ('en-sycophancy', 'That is a great point about pricing.', {}, True),
    ('en-sycophancy', 'The question has two parts.', {}, False),
    ('en-stat-claim', 'Cuts costs by 43%.', {}, True),
    ('en-stat-claim', 'Cuts costs.', {}, False),
    ('en-stat-claim', 'Cuts costs by 43%.', {'facts': 'Costs fall by 43%.'}, False),
    ('en-superlative', "The world's first AI notebook.", {}, True),
    ('en-superlative', 'A notebook for small teams. The first step is easy to take.', {}, False),
    ('en-establishment-claim', 'Clinically proven to reduce stress.', {}, True),
    ('en-establishment-claim', 'Designed to help you wind down.', {}, False),
    ('en-testimonial', '“This app changed my life.” — Sarah K., Marketing Manager', {}, True),
    ('en-testimonial', 'Our customers include Acme.', {}, False),
    ('en-fact-not-in-brief', 'We ship from Kenya.', {'facts': 'We ship the same day.'}, True),
    ('en-fact-not-in-brief', 'We ship the same day.', {'facts': 'We ship the same day.'}, False),
    ('en-citation-check', 'See doi:10.1126/sciadv.adt3813 for the study.', {}, True),
    ('en-citation-check', 'No identifiers here.', {}, False),
    ('en-long-sentence', ' '.join(['word'] * 30) + '.', {}, True),
    ('en-long-sentence', 'A short sentence.', {}, False),
    ('en-long-paragraph', ' '.join(['Fresh bread and coffee are ready at the shop every morning.'] * 16), {}, True),
    ('en-long-paragraph', 'Fresh bread is ready at eight.', {}, False),
    ('en-passive', 'Mistakes were made. The form was signed. We met the team. We fixed the bug. We sent the files.',
     {}, True),
    ('en-passive', 'We made mistakes. Sara signed the form. We met the team. We fixed the bug. We sent the files.',
     {}, False),
    ('en-hidden-verb', 'We conducted an analysis of costs.', {}, True),
    ('en-hidden-verb', 'We analyzed costs.', {}, False),
    ('en-complex-word', 'We utilize AI in order to help.', {}, True),
    ('en-complex-word', 'We use AI to help.', {}, False),
    ('en-shall', 'The user shall submit the form.', {}, True),
    ('en-shall', 'You must submit the form.', {}, False),
    ('en-double-negative', 'This is not uncommon.', {}, True),
    ('en-double-negative', 'Shipping is not included.', {}, False),
    ('en-slash', 'Bring your ID and/or passport.', {}, True),
    ('en-slash', 'Bring your ID or passport, or both.', {}, False),
    ('en-slash', 'Bring your ID and/or passport.', {'fmt': 'ui'}, False),
    ('en-please-note', 'Please note that the office is closed.', {}, True),
    ('en-please-note', 'The office is closed.', {}, False),
    ('en-minimizer', 'Simply click Save.', {'fmt': 'ui'}, True),
    ('en-minimizer', 'Click Save.', {'fmt': 'ui'}, False),
    ('en-minimizer', 'Simply click Save.', {}, False),
    ('en-bangs', 'Wow!!', {}, True),
    ('en-bangs', 'Done.', {}, False),
    ('en-there-is', 'There are three ways to pay.', {}, True),
    ('en-there-is', 'You can pay three ways.', {}, False),
    ('en-undefined-abbr', _FILL * 2 + 'Submit the DPIA by Friday.', {}, True),
    ('en-undefined-abbr', _FILL * 2 + 'Submit the data protection impact assessment (DPIA). Send the DPIA today.', {},
     False),
    ('en-metaphor-buzz', 'Going forward, we will drive growth.', {}, True),
    ('en-metaphor-buzz', 'From now on, we will grow sales.', {}, False),
    ('en-oxford-comma', 'We sell apples, pears and plums.', {'profile': 'profile-us.json'}, True),
    ('en-oxford-comma', 'We sell apples, pears, and plums.', {'profile': 'profile-us.json'}, False),
    ('en-oxford-comma', 'We sell apples, pears, and plums.', {'profile': 'profile-uk.json'}, True),
    ('en-oxford-comma', 'We sell apples, pears and plums.', {'profile': 'profile-uk.json'}, False),
    ('en-oxford-comma', 'We sell apples, pears, and plums. We also bake bread, rolls and pies.', {}, True),
    ('en-oxford-comma', 'In 2024, sales and profits rose.', {'profile': 'profile-us.json'}, False),
    ('en-dash-spacing', 'Use pipelines — logical groups — to work.', {}, True),
    ('en-dash-spacing', 'Use pipelines—logical groups—to work.', {}, False),
    ('en-dash-spacing', 'Use pipelines—logical groups.', {'settings': 'house:ap'}, True),
    ('en-numeral-style', 'We hired 3 people.', {'settings': 'house:ap'}, True),
    ('en-numeral-style', 'We hired three people. Step 3 of 5 starts at 5 pm.', {'settings': 'house:ap'}, False),
    ('en-numeral-style', 'We hired 3 people.', {}, False),
    ('en-numeral-start', '10 apps are included.', {}, True),
    ('en-numeral-start', 'More than 10 apps are included. 2026 was a good year.', {}, False),
    ('en-numeric-date', 'Due 6/12/2017.', {}, True),
    ('en-numeric-date', 'Due 12 June 2017.', {}, False),
    ('en-range-hyphen', 'Open 10-11am.', {'settings': 'house:govuk'}, True),
    ('en-range-hyphen', 'Open 10am to 11am. Call 2026-09-27.', {'settings': 'house:govuk'}, False),
    ('en-ampersand', 'Terms & conditions apply.', {}, True),
    ('en-ampersand', 'Terms and conditions apply.', {}, False),
    ('en-ampersand', 'Terms & conditions', {'fmt': 'ui'}, False),
    ('en-heading-punct', '## Move a tile.\n\nText.', {'kind': 'md'}, True),
    ('en-heading-punct', '## Move a tile\n\nText.', {'kind': 'md'}, False),
    ('en-double-space', 'End.  Next step.', {}, True),
    ('en-double-space', 'End. Next step.', {}, False),
    ('en-link-text', 'For prices [click here](https://example.com/p).', {'kind': 'md'}, True),
    ('en-link-text', 'See [the 2026 price list](https://example.com/p).', {'kind': 'md'}, False),
    ('en-all-caps', 'DO NOT USE BLOCK CAPITALS HERE', {}, True),
    ('en-all-caps', 'Do not use block capitals here', {}, False),
    ('en-latin-abbr', 'Fruit, e.g. apples.', {'settings': 'house:govuk'}, True),
    ('en-latin-abbr', 'Fruit such as apples.', {'settings': 'house:govuk'}, False),
    ('en-latin-abbr', 'Fruit, e.g. apples.', {}, False),
    ('en-contraction', "You can't apply.", {'profile': 'profile-uk.json'}, True),
    ('en-contraction', 'You cannot apply.', {'profile': 'profile-uk.json'}, False),
    ('en-contraction', "We're open.", {'profile': {'language': 'en', 'contractions': 'avoid'}}, True),
    ('en-no-contraction', 'We do not ship on Sundays.', {'profile': 'profile-us.json', 'fmt': 'email'}, True),
    ('en-no-contraction', "We don't ship on Sundays.", {'profile': 'profile-us.json', 'fmt': 'email'}, False),
    ('en-no-contraction', 'We do not ship on Sundays.', {'profile': 'profile-us.json', 'fmt': 'blog'}, False),
    ('en-spelling-mix', 'The color and the flavour.', {}, True),
    ('en-spelling-mix', 'The color and the flavor.', {}, False),
    ('en-spelling-mix', 'We organize the colour chart.', {}, False),
    ('en-spelling-variant', 'The colour is bright.', {'profile': 'profile-us.json'}, True),
    ('en-spelling-variant', 'The color is bright.', {'profile': 'profile-us.json'}, False),
    ('en-spelling-variant', 'The color is bright.', {'profile': 'profile-uk.json'}, True),
    ('en-spelling-variant', 'The colour is bright.', {}, False),
    ('en-readability-grade', _HARD * 6, {'fmt': 'blog'}, True),
    ('en-readability-grade', _FILL * 2, {'fmt': 'blog'}, False),
    ('en-readability-grade', _HARD * 6, {}, False),
    ('en-readability-fre', _HARD * 6, {'fmt': 'blog'}, True),
    ('en-readability-fre', _FILL * 2, {'fmt': 'blog'}, False),
    ('en-brand-spelling', 'Try toranjno today.', {'profile': 'profile-us.json'}, True),
    ('en-brand-spelling', 'Order from Toranj No today.', {'profile': 'profile-us.json'}, True),
    ('en-brand-spelling', 'Try Toranjno today.', {'profile': 'profile-us.json'}, False),
    ('en-profile-banned', 'A cheap gift.', {'profile': 'profile-us.json'}, True),
    ('en-profile-banned', 'A low-cost gift.', {'profile': 'profile-us.json'}, False),
    ('en-profile-avoid', 'We utilize tea leaves.', {'profile': 'profile-us.json'}, True),
    ('en-profile-avoid', 'We use tea leaves.', {'profile': 'profile-us.json'}, False),
    ('en-jargon', 'We will circle back on this.', {'profile': 'profile-us.json'}, True),
    ('en-jargon', 'We will talk again soon.', {'profile': 'profile-us.json'}, False),
    ('en-jargon', 'We will circle back on this.', {}, False),
    ('en-emoji', 'Fresh bread \U0001F35E', {}, True),
    ('en-emoji', 'Fresh bread', {}, False),
    ('en-same-opening', 'We bake bread. We roast beans. We ship orders.', {}, True),
    ('en-same-opening', 'We bake bread. Beans get roasted daily. Orders ship at noon.', {}, False),
    ('en-flat-rhythm', 'We bake bread every day. We roast beans every week. We ship orders every noon. '
     'We clean tables every night. We count cups every morning. We call farms every month.', {}, True),
    ('en-flat-rhythm', _read(os.path.join(SE, 'good.txt')), {}, False),
    ('en-rhetorical-open', 'Ever wondered why coffee tastes sour? It is the roast.', {}, True),
    ('en-rhetorical-open', 'Coffee tastes sour when the roast is light.', {}, False),
    ('en-cliche-open', "In today's fast-paced world, time matters.", {}, True),
    ('en-cliche-open', 'Time matters to our customers.', {}, False),
    ('en-journey', 'Start your journey with us.', {}, True),
    ('en-journey', 'Map the customer journey in the report.', {}, False),
    ('en-moral-close', 'Because at the end of the day, quality matters.', {}, True),
    ('en-moral-close', 'Quality matters.', {}, False),
    ('en-clickbait', "You won't believe this result.", {}, True),
    ('en-clickbait', 'The result surprised us.', {}, False),
    ('en-caption-header', '# New menu\nFresh bread today.', {'fmt': 'caption'}, True),
    ('en-caption-header', 'Fresh bread today.', {'fmt': 'caption'}, False),
    ('en-channel-length', 'a' * 301, {'channel': 'bluesky.post'}, True),
    ('en-channel-length', '\U0001F468‍\U0001F469‍\U0001F467' * 300, {'channel': 'bluesky.post'}, False),
    ('en-channel-length', 'See https://example.com/' + 'x' * 400 + ' ' + 'a' * 250, {'channel': 'x.post'}, False),
    ('en-channel-length', 'a' * 281, {'channel': 'x.post'}, True),
    ('en-channel-visible', 'Hello there world', {'channel': 'draft-channel.post'}, True),
    ('en-channel-visible', 'Hi', {'channel': 'draft-channel.post'}, False),
    ('en-channel-items', '#a #b #c #d #e #f', {'channel': 'instagram.hashtags'}, True),
    ('en-channel-items', '#a #b', {'channel': 'instagram.hashtags'}, False),
    ('en-channel-items', 'mug, handmade ceramic coffee mug gift', {'channel': 'etsy.tags'}, True),
    ('en-profile-invalid', 'Hello.', {'profile': 'profile-invalid.json'}, True),
    ('en-profile-invalid', 'Hello.', {'profile': 'profile-us.json'}, False),
]


def _case_kwargs(kw):
    kw = dict(kw)
    s = kw.pop('settings', None)
    if s and s.startswith('house:'):
        kw['settings'] = LE.resolve_settings(kw.pop('profile', None) or {}, kw.get('fmt'),
                                             house_style=s.split(':', 1)[1])
    return kw


def t_rules(out):
    ids = [r['id'] for r in LE.rule_list()]
    pos, neg, fails = set(), set(), []
    for rule, text, kw, want in CASES:
        try:
            got = rule in _codes(text, **_case_kwargs(kw))
        except Exception as e:  # a crash is a failure, with its message
            fails.append('%s: %s: %s' % (rule, type(e).__name__, e))
            continue
        if got != want:
            fails.append('%s %s: %s' % (rule, 'missed' if want else 'false positive', text[:50]))
        (pos if want else neg).add(rule)
    out.append(('en rule cases', not fails, '; '.join(fails[:6]) or '%d cases' % len(CASES)))
    missing = [i for i in ids if i not in pos or i not in neg]
    out.append(('en every rule has + and - cases', not missing, ', '.join(missing) or '%d rules' % len(ids)))
    bad = [i for i in ids if not i.startswith('en-')]
    dup = len(ids) != len(set(ids))
    sev = [r['id'] for r in LE.rule_list() if r['severity'] not in ('error', 'warning') or not r['description']
           or not r['fix'] or not r['ref']]
    out.append(('en rule ids, severities and refs', not (bad or dup or sev), ', '.join(bad + sev)))
    cat = json.loads(_read(os.path.join(SE, 'rules-catalog.json')))
    cat_ids = set(r['id'] for r in cat['rules'])
    unknown = [r['id'] for r in LE.rule_list() if r['ref'].startswith('EN-') and r['ref'] not in cat_ids]
    out.append(('en refs exist in the research catalog', not unknown, ', '.join(unknown)))
    # the catalog's own flagged examples still fire the mapped rule (where the rule is not gated)
    ref_map = dict((r['ref'], r['id']) for r in LE.rule_list())
    skip = {'EN-AI-030', 'EN-AI-051', 'EN-AI-052', 'EN-AI-061', 'EN-PL-003', 'EN-PL-010', 'EN-PL-013',
            'EN-ST-001', 'EN-ST-003', 'EN-ST-006', 'EN-ST-012', 'EN-ST-013', 'EN-AI-050', 'EN-ST-008',
            'EN-ST-010', 'EN-FACT-001', 'EN-AI-041', 'EN-AI-042', 'EN-AI-013', 'EN-AI-040', 'EN-AI-021',
            'EN-AI-060'}
    miss = []
    for r in cat['rules']:
        rid = ref_map.get(r['id'])
        if not rid or r['id'] in skip:
            continue
        for ex in r.get('examples_flagged') or []:
            got = _codes(ex)
            # a more specific rule may cover the span on purpose (lint_en._SUPPRESS)
            if rid not in got and not any(s in got for s in LE._SUPPRESS.get(rid, ())):
                miss.append('%s: %s' % (rid, ex[:40]))
        for ex in r.get('examples_ok') or []:
            if rid in _codes(ex):
                miss.append('%s ok-example flagged: %s' % (rid, ex[:40]))
    out.append(('en catalog examples', not miss, '; '.join(miss[:5])))


def t_samples(out):
    iss, st = LE.lint(_read(os.path.join(SE, 'good.txt')))
    out.append(('en good.txt: 0 errors, 0 warnings', not iss, ', '.join(x['code'] for x in iss[:6])))
    iss, st = LE.lint(_read(os.path.join(SE, 'bad.txt')))
    distinct = sorted(set(x['code'] for x in iss))
    out.append(('en bad.txt: 30+ distinct rules', len(distinct) >= 30, '%d rules' % len(distinct)))


LOCALE = [
    ('en.json', [('common.promo', 'en-buzzword'), ('common.promo', 'en-bangs'), ('common.printf', 'en-dash-spacing'),
                 ('errors.network', 'en-please-note')], ['common.save', 'common.greeting', 'common.count',
                                                          'errors.html', 'common.persian']),
    ('en.po', [('welcome', 'en-buzzword')], ['button|save', 'One file[0]', 'One file[1]']),
    (os.path.join('values-en', 'strings.xml'), [('save_done', 'en-bangs'), ('welcome', 'en-please-note')],
     ['app_name', 'orders[one]', 'orders[other]']),
    ('Localizable.strings', [('welcome_title', 'en-cliche-open')], ['url_hint', 'save_button', 'commented']),
    ('en.xlf', [('greeting', 'en-complex-word')], ['cart.count']),
    ('en.arb', [('title', 'en-buzzword')], ['hello', '@title', '@@locale']),
]


def t_locale(out):
    for name, must, clean in LOCALE:
        path = os.path.join(SE, name)
        text = _read(path)
        try:
            iss, st = LE.lint_locale(text, path)
        except Exception as e:
            out.append(('en locale %s' % name, False, '%s: %s' % (type(e).__name__, e)))
            continue
        got = set((x.get('key'), x['code']) for x in iss)
        pr = ['missing %s/%s' % k for k in must if k not in got]
        pr += ['unexpected issue on %s' % k for k in clean if any(x.get('key') == k for x in iss)]
        pr += ['issue without key: %s' % x['code'] for x in iss if x['line'] and not x.get('key')]
        if LE.fix_text(text, kind='locale')[0] != text:
            pr.append('--fix changed a locale file')
        out.append(('en locale %s' % name, not pr, '; '.join(pr) or '%d strings' % st.get('strings', 0)))


def t_csv(out):
    path = os.path.join(SE, 'catalog.csv')
    iss, st = LE.lint_csv(_read(path), path)
    keys = set((x.get('key'), x['code']) for x in iss)
    pr = []
    for k in (('row 3/B-202/description', 'en-superlative'), ('row 3/B-202/description', 'en-bangs')):
        if k not in keys:
            pr.append('missing %s %s' % k)
    if any(x.get('key', '').startswith('row 2/') or x.get('key', '').startswith('row 4/') for x in iss if x.get('key')):
        pr.append('clean or Persian rows flagged')
    if st.get('key_column') != 'sku':
        pr.append('key column %r' % st.get('key_column'))
    out.append(('en catalog.csv keys row n/sku/column', not pr, '; '.join(pr)))


def t_readability(out):
    exp = json.loads(_read(os.path.join(SE, 'readability', 'expected.json')))
    for name in ('easy.txt', 'medium.txt', 'hard.txt'):
        r = LE.readability(_read(os.path.join(SE, 'readability', name)))
        e = exp[name]
        pr = []
        for k in ('fre', 'fkgl'):
            if r[k] is None or abs(r[k] - e[k]) > 1.0:
                pr.append('%s %s, hand %s' % (k, r[k], e[k]))
        out.append(('en readability %s' % name, not pr, '; '.join(pr) or 'FRE %s, FKGL %s' % (r['fre'], r['fkgl'])))


def t_parity(out):
    good = os.path.join(S, 'good.txt')
    c1, o1, e1 = _cli('lint_fa.py', [good, '--json'])
    c2, o2, e2 = _cli('lint.py', [good, '--json'])
    pr = []
    try:
        d1, d2 = json.loads(o1), json.loads(o2)
        for f in d2['files']:
            if f.pop('lang', None) != 'fa':
                pr.append('lang is not fa')
        if d1 != d2:
            pr.append('JSON differs')
    except ValueError:
        pr.append('not JSON: %s %s' % (e1[:80], e2[:80]))
    if c1 != c2:
        pr.append('exit %s vs %s' % (c1, c2))
    out.append(('parity lint.py = lint_fa.py on good.txt', not pr, '; '.join(pr)))
    missing = os.path.join(S, 'no-such-file.txt')
    cases = [
        ('clean', {'lint_fa.py': [good], 'lint_en.py': [os.path.join(SE, 'good.txt')], 'lint.py': [good]}, 0),
        ('error', {'lint_fa.py': [os.path.join(S, 'bad.txt')], 'lint_en.py': [os.path.join(SE, 'bad.txt')],
                   'lint.py': [os.path.join(SE, 'bad.txt')]}, 1),
        ('missing file', {'lint_fa.py': [missing], 'lint_en.py': [missing], 'lint.py': [missing]}, 2),
        ('bad profile', {'lint_fa.py': [good, '--profile', missing + '.json'],
                         'lint_en.py': [good, '--profile', missing + '.json'],
                         'lint.py': [good, '--profile', missing + '.json']}, 2),
        ('no input', {'lint_fa.py': [], 'lint_en.py': [], 'lint.py': []}, 2),
        ('strict warnings', {'lint_fa.py': ['--strict', '--text', 'این متن امروزه کوتاه است.'],
                             'lint_en.py': ['--strict', '--text', 'Please note the office is closed.'],
                             'lint.py': ['--strict', '--text', 'Please note the office is closed.']}, 1),
    ]
    pr = []
    for label, runs, want in cases:
        for script, args in runs.items():
            code, _o, err = _cli(script, args)
            if code != want:
                pr.append('%s %s: exit %s, want %s' % (label, script, code, want))
            if 'Traceback' in err:
                pr.append('%s %s: traceback' % (label, script))
    out.append(('parity exit codes 0/1/2 in three CLIs', not pr, '; '.join(pr[:5])))


def t_mixed(out):
    path = os.path.join(SM, 'method.md')
    e = LD.lint_path(path)
    pr = []
    if e['lang'] != 'mixed':
        pr.append('lang %s' % e['lang'])
    got = [(x['line'], x['col'], x['rule']) for x in e['issues']]
    for want in ((12, 35, 'dash'), (16, 4, 'en-ai-vocab')):
        if want not in got:
            pr.append('missing %s' % (want,))
    if any(x['line'] == 19 for x in e['issues']):
        pr.append('code block linted')
    st = e['stats']
    if 'fa' not in st or 'en' not in st or st.get('lang_split', {}).get('fa_segments', 0) < 1:
        pr.append('stats fa/en/lang_split')
    if st.get('errors') != st['fa']['errors'] + st['en']['errors']:
        pr.append('errors not summed')
    out.append(('mixed method.md exact positions', not pr, '; '.join(pr) or '%s' % got))
    lang, ratio = LD.detect_lang(_read(path), 'md')
    out.append(('mixed detect_lang', lang == 'mixed' and 0.2 < ratio < 0.8, '%s %s' % (lang, ratio)))
    pr = []
    for text, want in (('سلام، این متن کاملاً فارسی است و برای آزمون نوشته شده.', 'fa'),
                       ('This text is plain English and it is long enough.', 'en'),
                       ('OK', 'en'), ('', 'fa'), ('123', 'fa'), ('ab سلام', 'fa'),
                       ('Order at https://example.com/very/long/english/path — سفارش بدهید', 'fa')):
        got = LD.detect_lang(text)[0]
        if got != want:
            pr.append('%r → %s' % (text[:20], got))
    out.append(('detect_lang thresholds and masking', not pr, '; '.join(pr)))
    # English fragments in a Persian-majority file: line rules only; block quotes keep their own variant
    pr = []
    fa_major = ('این راهنما برای نوشتنِ متنِ کوتاهِ فارسی است و نمونه‌ی انگلیسی را فقط برای مقایسه می‌آورد.\n'
                'نمونه‌ی اول:\n\nThe color is bright and the paper is thick.\n\nنمونه‌ی دوم:\n\n'
                'The colour is bright and the paper is thick.\n\n'
                'هر دو نمونه برای آموزش آمده‌اند و متنِ اصلی فارسی است.\n')
    iss, st, lg = LD.lint_text(fa_major, md=True)
    if lg != 'mixed' or 'en-spelling-mix' in [x['code'] for x in iss]:
        pr.append('fragments: %s %s' % (lg, [x['code'] for x in iss]))
    iss, st, lg = LD.lint_text('Hello {{name}}, welcome.\n\nاین متنِ فارسیِ کوتاه است و درباره‌ی خوشامد است.', md=True)
    if 'en-template-residue' not in [x['code'] for x in iss]:
        pr.append('line rules must still run on fragments')
    uk_quote = 'We print the color chart every week.\n\n> Enrolments for the course close in May.\n'
    if 'en-spelling-mix' in _codes(uk_quote, kind='md'):
        pr.append('block quote counted as the author\'s text')
    if 'en-spelling-mix' not in _codes('We print the color chart. Enrolments close in May.', kind='md'):
        pr.append('mix outside quotes missed')
    out.append(('mixed fragments and block quotes', not pr, '; '.join(pr)))
    fixed, n = LD.fix_text(_read(path), 'md')
    again, n2 = LD.fix_text(fixed, 'md')
    pr = [] if fixed == again else ['mixed fix not idempotent']
    if '—' in fixed.split('\n')[11] or 'delve — anything' not in fixed:
        pr.append('fa dash not fixed or code changed')
    out.append(('mixed --fix per segment', not pr, '; '.join(pr) or '%d lines' % n))


def t_fix(out, tmp):
    prof = _prof('profile-us.json')
    st = LE.resolve_settings(prof)
    text = _read(os.path.join(SE, 'fixme.md'))
    f1, n1 = LE.fix_text(text, kind='md', settings=st)
    f2, n2 = LE.fix_text(f1, kind='md', settings=st)
    pr = []
    if f1 != f2 or n2:
        pr.append('not idempotent')
    fixable = {'en-double-space', 'en-quote-mix', 'en-dash-spacing', 'en-heading-punct', 'en-spelling-variant'}
    left = [x['code'] for x in LE.lint(f1, kind='md', settings=st)[0] if x['code'] in fixable]
    if left:
        pr.append('still: %s' % ', '.join(sorted(set(left))))
    for keep in ('`a  --  b`', '{name}', '[confirm: price]', 'https://example.com/a--b',
                 'Bad example:  two spaces -- stays.', 'title: "Fix test -- front matter stays"'):
        if keep not in f1:
            pr.append('protected text changed: %s' % keep)
    out.append(('en --fix idempotent, protected spans kept', not pr, '; '.join(pr) or '%d lines' % n1))
    # CRLF and BOM with --write
    path = os.path.join(tmp, 'fix-crlf.md')
    with open(path, 'wb') as fh:
        fh.write(codecs.BOM_UTF8 + text.replace('\n', '\r\n').encode('utf-8'))
    code, _o, err = _cli('lint_en.py', [path, '--md', '--fix', '--write', '--profile', os.path.join(SE, 'profile-us.json')])
    with open(path, 'rb') as fh:
        data = fh.read()
    pr = []
    if not data.startswith(codecs.BOM_UTF8):
        pr.append('BOM lost')
    body = data[3:].decode('utf-8')
    if body.count('\r\n') != text.count('\n') or '\n' in body.replace('\r\n', ''):
        pr.append('CRLF not kept')
    if body.replace('\r\n', '\n') != f1:
        pr.append('CLI result differs from fix_text')
    if 'Traceback' in err:
        pr.append('traceback')
    out.append(('en --fix --write keeps CRLF and BOM', not pr, '; '.join(pr)))


def t_profiles(out):
    bi = _prof('profile-bilingual.json')
    en = LE.resolve_settings(bi)
    en_ui = LE.resolve_settings(bi, 'ui')
    fa = LF.resolve_settings(bi)
    fa_ui = LF.resolve_settings(bi, 'ui')
    pr = []
    if en['max_words'] != 22:
        pr.append('en max_words %s (want 22 from by_lang.en)' % en['max_words'])
    if en_ui['max_words'] != 7:
        pr.append('en ui %s (want 7)' % en_ui['max_words'])
    if fa['max_words'] != 18 or fa_ui['max_words'] != 10:
        pr.append('fa %s/%s (want 18/10)' % (fa['max_words'], fa_ui['max_words']))
    if en['banned'] != ['synergy'] or fa['banned'] != ['آزمایشی']:
        pr.append('banned %s / %s' % (en['banned'], fa['banned']))
    if en['spelling'] != 'uk-ize' or en['variant'] != 'en-CA':
        pr.append('bilingual variant %s spelling %s' % (en['variant'], en['spelling']))
    out.append(('profiles by_lang precedence', not pr, '; '.join(pr)))
    pr = []
    for name, want in (('profile-us.json', 'us'), ('profile-uk.json', 'uk')):
        got = LE.resolve_settings(_prof(name))['spelling']
        if got != want:
            pr.append('%s → %s' % (name, got))
    if LE.resolve_settings({})['spelling'] is not None:
        pr.append('no profile → spelling set')
    if LE.resolve_settings({}, variant='en-AU')['spelling'] != 'uk':
        pr.append('--variant en-AU')
    if LE.resolve_settings({'language': 'en'})['variant'] != 'en-US':
        pr.append('language en without variant → not en-US')
    out.append(('profiles spelling from the variant', not pr, '; '.join(pr)))
    # lint_fa accepts and ignores the English keys (spec §D.6)
    pr = ['%s: %s' % (n, w) for n in ('profile-us.json', 'profile-uk.json', 'profile-bilingual.json')
          for w in LF.validate_profile(json.loads(_read(os.path.join(SE, n))))]
    out.append(('lint_fa ignores the English profile keys', not pr, '; '.join(pr[:3])))
    pr = []
    raw = json.loads(_read(os.path.join(SE, 'profile-bilingual.json')))
    if LF.normalize_profile(raw).get('max_words') != 18:
        pr.append('lint_fa did not merge by_lang.fa')
    if 'by_lang' in LF.merge_by_lang({'a': 1}, 'fa') or LF.merge_by_lang(raw, 'xx') is not raw:
        pr.append('merge_by_lang side effects')
    out.append(('lint_fa by_lang.fa merge', not pr, '; '.join(pr)))


def t_channels(out):
    pr = []
    for s, n in (('\U0001F468‍\U0001F469‍\U0001F467‍\U0001F466', 1), ('\U0001F1EE\U0001F1F7', 1),
                 ('\U0001F44D\U0001F3FD', 1), ('é', 1), ('❤️', 1), ('a\r\nb', 3),
                 ('می‌خواهم', 7), ('1️⃣', 1)):
        if TC.grapheme_count(s) != n:
            pr.append('grapheme %r → %d' % (s, TC.grapheme_count(s)))
    for s, n in (('hello', 5), ('https://example.com/a/very/long/path', 23), ('see https://x.co', 27),
                 ('日本', 4), ('سلام', 4), ('\U0001F468‍\U0001F469‍\U0001F467', 2)):
        if TC.weighted_length(s) != n:
            pr.append('weighted %r → %d' % (s, TC.weighted_length(s)))
    if TC.utf16_units('\U0001F600a') != 3:
        pr.append('utf16')
    if TC.split_items('a, b\nc,,') != ['a', 'b', 'c'] or TC.count('a, b', 'items') != 2:
        pr.append('items')
    for s in ('hello', 'héllo \U0001F600', 'سلام ' * 20, 'x' * 161, '[' * 81):
        if TC.sms_segments(s) != LF.sms_segments(s):
            pr.append('sms differs from lint_fa: %r' % s[:10])
    if TC.count('abc', 'no-such-unit') != 3:
        pr.append('unknown unit')
    out.append(('textcount units', not pr, '; '.join(pr)))
    pr = []
    ch = LF.resolve_channel('bluesky.post', CH)
    iss, st = LE.lint('\U0001F468‍\U0001F469‍\U0001F467 hello', channel=ch)
    if st['channel'].get('unit') != 'grapheme' or st['channel'].get('count') != 7:
        pr.append('bluesky count %s' % st['channel'])
    iss, st = LE.lint('a' * 25, channel=LF.resolve_channel('draft-channel.post', CH))
    lv = [x['level'] for x in iss if x['code'] == 'en-channel-length']
    if lv != ['warning']:
        pr.append('unverified limit must warn: %s' % lv)
    iss, st = LE.lint('Hello ' * 40, channel=LF.resolve_channel('sms-intl.body', CH))
    if 'en-channel-length' not in [x['code'] for x in iss] or st['channel'].get('segments') != 2:
        pr.append('sms segments %s' % st['channel'].get('segments'))
    code, o, err = _cli('lint_en.py', ['--channels-dir', CH, '--channel', 'bluesky.post', '--text', 'Hi \U0001F44B'])
    if code != 0 or 'grapheme' not in o:
        pr.append('CLI grapheme report: %s %s' % (code, err[:80]))
    out.append(('channels grapheme/weighted/utf16/items checks', not pr, '; '.join(pr)))


def t_api(out):
    pr = []
    try:
        issues, stats, lang = LD.lint_text('Our robust platform empowers teams.')
        if lang != 'en' or 'en-buzzword' not in [x['code'] for x in issues]:
            pr.append('lint_text en')
        issues, stats, lang = LD.lint_text(_read(os.path.join(S, 'good.txt')))
        if lang != 'fa':
            pr.append('lint_text fa')
        issues, stats, lang = LD.lint_text('x', lang='en', fmt='ui', profile=os.path.join(SE, 'profile-us.json'))
        if stats.get('max_words') != 8:
            pr.append('profile path + format: %s' % stats.get('max_words'))
        e = LD.lint_path(os.path.join(SE, 'en.arb'))
        if set(e) != {'path', 'lang', 'issues', 'stats'} or e['lang'] != 'en':
            pr.append('lint_path shape %s %s' % (sorted(e), e.get('lang')))
        if any(set(x) != {'line', 'col', 'key', 'rule', 'severity', 'message', 'excerpt'} for x in e['issues']):
            pr.append('lint_path issue shape')
        e = LD.lint_path(os.path.join(SE, 'en.json'))
        if e['lang'] != 'mixed' or e['stats'].get('lang_split', {}).get('en_segments') != 7:
            pr.append('en.json (one Persian value) lang %s' % e['lang'])
        saved = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
        try:
            rc = LD.run([])
        finally:
            sys.stdout, sys.stderr = saved
        if rc != 2:
            pr.append('run([]) returned %r' % (rc,))
        issues, stats, lang = LD.lint_text('{"a": "Hello {{name}}, we leverage data."}', kind='locale')
        if lang != 'en' or 'en-buzzword' not in [x['code'] for x in issues]:
            pr.append('lint_text locale')
    except SystemExit:
        pr.append('SystemExit inside run()')
    except Exception as e:
        pr.append('%s: %s' % (type(e).__name__, e))
    try:
        LD.load_profile('no-such-profile-name')
        pr.append('missing profile did not raise')
    except LF.UserError:
        pass
    if LD.load_profile(None) != {} or LD.load_profile({'name': 'x'}) != {'name': 'x'}:
        pr.append('load_profile falsy/dict')
    out.append(('api: lint_text, lint_path, load_profile, run', not pr, '; '.join(pr)))
    pr = []
    code, o, err = _cli('lint.py', ['--rules', '--json'])
    try:
        d = json.loads(o)
        if set(d) != {'version', 'fa', 'en'} or set(d['en']) != {'version', 'tool_version', 'rules', 'lexicon',
                                                                   'jargon', 'formats'}:
            pr.append('shape %s' % sorted(d))
        if len(d['en']['formats']) != 26 or len(d['fa']['rules']) != len(LF.rule_list()):
            pr.append('formats/rules')
        if set(d['en']['rules'][0]) != {'id', 'severity', 'kind', 'description', 'ref', 'fix'}:
            pr.append('en rule keys')
    except ValueError:
        pr.append('not JSON: %s' % err[:80])
    code, o, err = _cli('lint_en.py', ['--version'])
    if code != 0 or 'lint_en 3.2.1' not in o:
        pr.append('--version %r' % o)
    code, o, err = _cli('lint.py', ['--version'])
    if code != 0 or 'lint 3.2.1' not in o:
        pr.append('lint --version %r' % o)
    code, o, err = _cli('lint.py', [os.path.join(SE, 'good.txt'), os.path.join(S, 'good.txt'), '--json'])
    try:
        d = json.loads(o)
        if [f['lang'] for f in d['files']] != ['en', 'fa'] or set(d) != {'version', 'files', 'summary'}:
            pr.append('lint.py --json files/lang')
    except ValueError:
        pr.append('lint.py --json not JSON')
    out.append(('cli: --rules --json, --version, --json lang', not pr, '; '.join(pr)))


def t_precision(out):
    """samples/en/precision.json: labelled true and false positives of the rules tuned for precision."""
    data = json.loads(_read(os.path.join(SE, 'precision.json')))
    fails, tp, fp = [], 0, 0
    for c in data['cases']:
        kw = {}
        if c.get('profile') is not None:
            kw['profile'] = c['profile']
        if c.get('fmt'):
            kw['fmt'] = c['fmt']
        if c.get('kind'):
            kw['kind'] = c['kind']
        try:
            got = c['rule'] in _codes(c['text'], **kw)
        except Exception as e:
            fails.append('%s: %s: %s' % (c['rule'], type(e).__name__, e))
            continue
        if got != c['expect']:
            fails.append('%s %s: %s' % (c['rule'], 'missed' if c['expect'] else 'false positive', c['text'][:50]))
        if c['expect']:
            tp += 1
        else:
            fp += 1
    out.append(('precision set: labelled hits fire, known false positives do not', not fails,
                '; '.join(fails[:5]) or '%d must fire, %d must not' % (tp, fp)))
    fails = []
    for c in data['lists']:
        got = [[ser, n] for _p, ser, n in LE.list_series(c['text'], c['text'])]
        if got != c['series']:
            fails.append('%s → %s' % (c['text'][:40], got))
    out.append(('list reader: serial flag and item count', not fails, '; '.join(fails[:4]) or '%d sentences'
                % len(data['lists'])))


def t_channel_latin(out):
    """An all-Latin SMS on a panel whose body limit is for Persian text is measured against the Latin
    field (160), and the report names the channel in English."""
    pr = []
    ch = LF.resolve_channel('panel-sms', CH)
    en = 'Flash sale: 20% off all mugs until Sunday. Shop now at example.com/sale and use code MUG20 at ' \
         'checkout. Reply STOP to opt out.'
    iss, st = LE.lint(en, channel=ch, fmt='sms')
    codes = [x['code'] for x in iss]
    if 'en-channel-length' in codes or st['channel'].get('field') != 'body_latin':
        pr.append('Latin SMS measured as %s: %s' % (st['channel'].get('field'), codes))
    if 'en-stat-claim' in codes:
        pr.append('"20% off" is a discount, not a claim')
    iss, st = LE.lint('Your order is ready ✓ ' * 5, channel=ch)
    if 'en-channel-length' not in [x['code'] for x in iss] or st['channel'].get('field') != 'body':
        pr.append('a non-GSM text keeps the 70 limit')
    code, o, err = _cli('lint.py', ['--channels-dir', CH, '--channel', 'panel-sms', '--text', en])
    if 'SMS panel (test copy' not in o:
        pr.append('header does not use name_en: %r' % o[:120])
    out.append(('channels: Latin SMS limit and English channel name', not pr, '; '.join(pr)))


def t_help(out):
    code, o, err = _cli('lint.py', ['--help'])
    ok = code == 0 and 'Persian and English' in o and 'فارسی و انگلیسی' in o and 'for English\n' not in o
    out.append(('lint.py --help names both languages', ok, '' if ok else o[:160]))


# Adversarial inputs, 50,000 characters each: every one used to take quadratic time somewhere (a
# regex that rescans the rest of the line from each start, or a filter that copies the line per
# match). Each must now finish in under a second.
_N = 50000


def _rep(unit, n=_N):
    return (unit * (n // len(unit) + 1))[:n]


def _uniq_caps(n=_N):
    out, i = [], 0
    while sum(len(x) + 1 for x in out) < n:
        a, b, c = i // 676 % 26, i // 26 % 26, i % 26
        out.append(chr(65 + a) + chr(65 + b) + chr(65 + c))
        i += 1
    return 'The ' + ' '.join(out)


REDOS = [
    ('e-mail local part', lambda: _rep('a'), 'fa'),
    ('e-mail runs', lambda: _rep('_a'), 'en'),
    ('at signs', lambda: _rep('a@'), 'en'),
    ('braces', lambda: _rep('{'), 'auto'),
    ('mustache openers', lambda: _rep('{{'), 'auto'),
    ('template openers', lambda: _rep('{%') + _rep('${', 2000), 'auto'),
    ('digit run', lambda: 'ب ' + _rep('1'), 'fa'),
    ('hyphenated run', lambda: _rep('a-'), 'en'),
    ('apostrophe run', lambda: _rep("a'"), 'en'),
    ('dotted labels', lambda: _rep('.a'), 'weighted'),
    ('table separator', lambda: '|' + _rep('\t') + 'x', 'md'),
    ('processing instructions', lambda: _rep('<?'), 'md'),
    ('comment openers', lambda: _rep('<!--'), 'md'),
    ('raw html openers', lambda: _rep('<code>'), 'md'),
    ('reference definition', lambda: '[a]: ' + _rep('/') + ' x', 'md'),
    ('printf zeros', lambda: '%' + _rep('0') + 'z', 'locale'),
    ('value placeholders', lambda: _rep('$t(') + _rep('<xliff:g>', 9000), 'mask'),
    ('dot run', lambda: _rep('.') + 'x', 'en'),
    ('trailing -ing clauses', lambda: _rep(', ensuring a'), 'en'),
    ('capitalized spelling words', lambda: _rep('Colour '), 'en-uk'),
    ('em dashes', lambda: _rep('—'), 'fa'),
    ('Persian lists', lambda: _rep('، ب، و '), 'fa'),
    ('Persian mi', lambda: _rep('می '), 'fa'),
    ('Persian na', lambda: _rep('، نه ب '), 'fa'),
    ('comma lists', lambda: _rep('a, ') + 'and b', 'en'),
    ('quoted lists', lambda: _rep('"a, and '), 'en'),
    ('copula', lambda: _rep('serves as a '), 'en'),
    ('abbreviations', _uniq_caps, 'en'),
    ('source brackets', lambda: _rep('[source '), 'en'),
    ('sentence ends', lambda: _rep('a. '), 'en'),
    ('blank run', lambda: _rep(' '), 'auto'),
    ('guillemets', lambda: _rep('«'), 'quoted'),
    ('locale guess', lambda: _rep('\n') + 'x', 'guess'),
    ('strings comments', lambda: _rep('/* '), 'strings'),
]


def _redos_job(kind, s):
    if kind == 'fa':
        return lambda: LF.lint(s)
    if kind == 'en':
        return lambda: LE.lint(s)
    if kind == 'en-uk':
        return lambda: LE.lint(s, settings=LE.resolve_settings({'language': 'en', 'spelling': 'us'}))
    if kind == 'md':
        return lambda: LD.lint_text(s, kind='md')
    if kind == 'auto':
        return lambda: LD.lint_text(s)
    if kind == 'weighted':
        return lambda: TC.weighted_length(s)
    if kind == 'locale':
        return lambda: LD.lint_text(json.dumps({'k': s}), kind='locale')
    if kind == 'mask':
        return lambda: LF.mask_value(s)
    if kind == 'quoted':
        return lambda: LF._QUOTED.sub('', s)
    if kind == 'guess':
        return lambda: LD._guess_locale_path(s)
    if kind == 'strings':
        return lambda: LF.extract_locale(s, 'x.strings')
    raise ValueError(kind)


def t_redos(out):
    slow, total = [], 0.0
    for name, build, kind in REDOS:
        s = build()
        job = _redos_job(kind, s)
        t0 = time.time()
        try:
            job()
        except LF.UserError:
            pass
        dt = time.time() - t0
        total += dt
        if dt >= 1.0:
            slow.append('%s %.2f s' % (name, dt))
    out.append(('ReDoS: %d adversarial 50k inputs, each under 1 s' % len(REDOS), not slow,
                '; '.join(slow) or 'total %.1f s' % total))


def t_speed(out):
    base = _read(os.path.join(SE, 'good.txt')) + '\n' + _read(os.path.join(SE, 'bad.txt')) + '\n'
    text = (base * (1024 * 1024 // len(base.encode('utf-8')) + 1))
    text = text[:1024 * 1024]
    t0 = time.time()
    LE.lint(text)
    dt = time.time() - t0
    out.append(('speed: 1 MB of English under 5 s', dt < 5.0, '%.2f s' % dt))


def t_hygiene(out):
    pr = []
    for name in ('lint_en.py', 'lint.py', 'textcount.py'):
        tree = ast.parse(_read(os.path.join(HERE, name)), feature_version=(3, 8))
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split('.')[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [(node.module or '').split('.')[0]]
            for m in mods:
                if m in ('subprocess', 'socket', 'urllib', 'http', 'requests'):
                    pr.append('%s imports %s' % (name, m))
    out.append(('hygiene: no subprocess/socket/urllib in the linters', not pr, '; '.join(pr)))


def _tree_state(folder):
    """{relative path: (size, mtime_ns)} for every file and folder under folder."""
    out = {}
    for dp, dn, fn in os.walk(folder):
        for n in dn + fn:
            p = os.path.join(dp, n)
            st = os.stat(p)
            out[os.path.relpath(p, folder)] = (st.st_size if n in fn else -1, st.st_mtime_ns)
    return out


def _stats_profile(so):
    """stats.profile of the first file in lint JSON output, or None."""
    try:
        return json.loads(so)['files'][0]['stats'].get('profile')
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def t_old_names(out, tmp):
    """Names from before the rename (Whalya 2): the profile id whalya and ~/.whalya/profiles are read,
    and nothing is ever written to the old folder."""
    home = os.path.join(tmp, 'oldnames-home')
    new_dir, old_dir = os.path.join(home, '.whalory', 'profiles'), os.path.join(home, '.whalya', 'profiles')
    for d, stem, name in ((old_dir, 'oldbrand', 'oldbrand'), (old_dir, 'shared', 'shared-old'),
                          (new_dir, 'shared', 'shared-new')):
        if not os.path.isdir(d):
            os.makedirs(d)
        with io.open(os.path.join(d, stem + '.json'), 'w', encoding='utf-8') as fh:
            fh.write(json.dumps({'schema_version': 2, 'name': name}))
    draft = os.path.join(tmp, 'oldnames-draft.txt')
    with io.open(draft, 'w', encoding='utf-8') as fh:
        fh.write('We ship on Monday.\n')
    before = _tree_state(old_dir)
    env = {'HOME': home, 'USERPROFILE': home}
    for script in ('lint.py', 'lint_fa.py'):
        if not os.path.isfile(os.path.join(HERE, script)):
            continue
        extra = ['--lang', 'en'] if script == 'lint.py' else []
        rc, so, se = _cli(script, [draft, '--json', '--profile', 'whalya'] + extra, env_extra=env)
        out.append(('%s --profile whalya: the legacy id finds whalory' % script,
                    rc in (0, 1) and _stats_profile(so) == 'whalory', 'rc %d %s %s' % (rc, _stats_profile(so), se[-120:])))
        rc, so, se = _cli(script, [draft, '--json', '--profile', 'oldbrand'] + extra, env_extra=env)
        out.append(('%s: a profile only in ~/.whalya/profiles is read' % script,
                    rc in (0, 1) and _stats_profile(so) == 'oldbrand', 'rc %d %s %s' % (rc, _stats_profile(so), se[-120:])))
        rc, so, se = _cli(script, [draft, '--json', '--profile', 'shared'] + extra, env_extra=env)
        out.append(('%s: ~/.whalory/profiles wins over ~/.whalya/profiles' % script,
                    rc in (0, 1) and _stats_profile(so) == 'shared-new', 'rc %d %s' % (rc, _stats_profile(so))))
    rc, so, se = _cli('lint.py', [draft, '--json', '--lang', 'en', '--profile', 'whalya.en'], env_extra=env)
    out.append(('lint.py --profile whalya.en finds whalory.en', rc in (0, 1) and _stats_profile(so) == 'whalory-en',
                'rc %d %s' % (rc, _stats_profile(so))))
    out.append(('~/.whalya/profiles stays untouched (read only)', _tree_state(old_dir) == before,
                str(sorted(_tree_state(old_dir)))))


def run():
    """[(name, ok, detail)] for every test."""
    out = []
    tmp = tempfile.mkdtemp(prefix='whalory-selftest-en-')
    try:
        for fn in (t_rules, t_samples, t_locale, t_csv, t_readability, t_parity, t_mixed, t_profiles,
                   t_channels, t_api, t_precision, t_channel_latin, t_help, t_redos, t_speed, t_hygiene):
            try:
                fn(out)
            except Exception as e:
                out.append((fn.__name__, False, '%s: %s' % (type(e).__name__, e)))
        for fn in (t_fix, t_old_names):
            try:
                fn(out, tmp)
            except Exception as e:
                out.append((fn.__name__, False, '%s: %s' % (type(e).__name__, e)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    res = run()
    failed = 0
    for name, ok, detail in res:
        print('%s  %-48s %s' % ('ok  ' if ok else 'FAIL', name, detail or ''))
        failed += 0 if ok else 1
    print('\n%s' % ('all %d tests passed' % len(res) if not failed else '%d of %d tests failed' % (failed, len(res))))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
