#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint_en: Whalory's automatic checker for English copy (Whalory 3.1.0).

It finds what the eye misses: AI-writing tells, puffery, vague attribution, unproven
claims, hidden verbs, long sentences, US/UK spelling mixes, punctuation and house-style
slips, readability, brand spelling, profile words and channel limits. It reads the same
inputs as lint_fa (text, Markdown, HTML, locale files, CSV/TSV) and takes the same flags,
plus --variant, --house-style and --facts.

The rule catalog comes from the research file en_rules.json (Whalory v3 research R3;
a copy is in scripts/samples/en/rules-catalog.json). Each rule id starts with "en-";
`--rules` lists them with the catalog reference and the fix.

A script never replaces reading. Story, detail and truth are checked by a person.

Usage:
    python lint_en.py draft.txt
    python lint_en.py draft.txt --profile profiles/whalory.en.json
    python lint_en.py "posts/*.txt" content/ --profile auto --json
    python lint_en.py --text "Short copy" --format ui
    python lint_en.py post.txt --channel bluesky.post
    python lint_en.py src/locales/en.json --format ui
    python lint_en.py catalog.csv --csv-columns title,description --csv-key sku
    python lint_en.py draft.md --md --facts brief.txt
    python lint_en.py draft.txt --variant en-GB --house-style govuk
    python lint_en.py draft.txt --fix            # writes draft.fixed.txt
    python lint_en.py draft.txt --fix --write    # fixes in place; keeps CRLF and BOM
    python lint_en.py --rules [--json]
    python lint_en.py --version

Exit codes: 0 no errors; 1 at least one error (or a warning with --strict);
2 input, profile or flag error; 130 interrupted.

Put deliberate bad examples in teaching files between two lines of their own so they
are neither checked nor changed by --fix:
    <!-- lint-ignore -->
    ...
    <!-- /lint-ignore -->
Inline code and code blocks are never checked. List items, headings and table cells
are sentences of their own.
"""
from __future__ import print_function

import sys

if sys.version_info < (3, 8):  # before anything else, so the message is readable
    sys.stderr.write('lint_en needs Python 3.8 or newer (found %s). '
                     'Install a newer Python and run it again.\n' % sys.version.split()[0])
    sys.exit(2)

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts: a skill or plugin folder may be read-only

import argparse  # noqa: E402
import bisect  # noqa: E402
import functools  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import unicodedata  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import hashlib  # noqa: E402

import lint_fa as LF  # noqa: E402
import textcount as TC  # noqa: E402

_HUB = LF._HUB      # the Whalory Hub overlay (spec 5.9), or None; the built-in rules never need it

__version__ = '3.2.0'

ERROR, WARN = LF.ERROR, LF.WARN
UserError = LF.UserError
MASK, BLOCK = LF.MASK, LF.BLOCK

# shared implementation (one reader, one masker, one locale extractor)
read_text = LF.read_text
write_text = LF.write_text
iter_paths = LF.iter_paths
detect_kind = LF.detect_kind
extract_locale = LF.extract_locale
csv_cells = LF.csv_cells
mask_value = LF.mask_value
ignore_spans = LF.ignore_spans
protected_spans = LF.protected_spans
clean_text = LF.clean_text
FORMAT_IDS = LF.FORMAT_IDS
EMOJI = LF.EMOJI

A = "['’]"            # apostrophe: straight or curly
_FA_LETTER = re.compile('[%s]' % LF.FA_LETTERS)
_LATIN = re.compile(r'[A-Za-z]')


def _rx(pattern, flags=0):
    """{A} is an apostrophe group; {AC} the same characters inside a [class]."""
    return re.compile(pattern.replace('{AC}', "'’").replace('{A}', A), flags)


# ---------------------------------------------------------------- formats and dials
EN_DIAL_WORDS = {1: 15, 2: 20, 3: 25, 4: 30, 5: 35}
EN_DEFAULT_MAX_WORDS = 25
EN_GRADE = {1: 6, 2: 8, 3: 10, 4: 12, 5: 14}
_FORMAT_NOTES = {
    'caption': 'Social caption', 'story': 'Story text', 'reels': 'Short-video text and subtitles',
    'carousel': 'Carousel slides', 'post': 'Channel or network post', 'sms': 'SMS',
    'otp': 'One-time passcode SMS', 'email': 'Email body', 'subject': 'Email subject line',
    'push': 'App push notification', 'ui': 'Interface microcopy', 'error': 'Error message',
    'product': 'Product description', 'listing': 'Marketplace listing', 'landing': 'Landing page',
    'about': 'About page', 'blog': 'Article', 'ad': 'Ad', 'press': 'Press release',
    'bot': 'Chatbot and assistant', 'reply': 'Reply to a review or message',
    'hard': 'Hard message: apology, bad news', 'deck': 'Presentation', 'script': 'Audio and video script',
    'name': 'Naming', 'headline': 'Headline',
}
# spec §D.3: format defaults only ever make limits stricter
EN_FORMAT_DEFAULTS = {
    'caption': {'max_words': 20}, 'sms': {'max_words': 20, 'emoji_max': 0},
    'otp': {'max_words': 15, 'emoji_max': 0, 'exclaim_max': 0}, 'subject': {'max_words': 9},
    'push': {'max_words': 12}, 'ui': {'max_words': 12, 'emoji_max': 0, 'exclaim_max': 0},
    'error': {'max_words': 16, 'emoji_max': 0, 'exclaim_max': 0}, 'headline': {'max_words': 12},
    'press': {'emoji_max': 0, 'exclaim_max': 0}, 'hard': {'emoji_max': 0, 'exclaim_max': 0},
    'deck': {'emoji_max': 0},
}
for _fid in FORMAT_IDS:
    EN_FORMAT_DEFAULTS.setdefault(_fid, {})
    EN_FORMAT_DEFAULTS[_fid]['note'] = _FORMAT_NOTES.get(_fid, '')

READ_FORMATS = ('landing', 'about', 'blog', 'email', 'product', 'press', 'deck', 'script', 'hard', 'reply')
SHORT_FORMATS = ('caption', 'story', 'reels', 'sms', 'otp', 'subject', 'push', 'ui', 'error', 'ad',
                 'headline', 'name', 'bot')
MINIMIZER_FORMATS = ('ui', 'error', 'email', 'landing', 'bot')
NO_CONTRACTION_FORMATS = ('caption', 'post', 'email', 'ui', 'bot', 'reply')
NUMERAL_START_OFF = ('otp', 'headline', 'ui', 'sms')
SIGNOFF_OK_FORMATS = ('email', 'reply', 'bot')

VARIANTS = ('en-US', 'en-GB', 'en-AU', 'en-CA', 'en-NZ', 'en-IE', 'en-IN', 'en-ZA')
_VARIANT_RX = re.compile(r'^(fa-(IR|AF)|tg|en-(US|GB|AU|CA|NZ|IE|IN|ZA))$')
SPELL_BY_VARIANT = {'en-US': 'us', 'en-GB': 'uk', 'en-AU': 'uk', 'en-NZ': 'uk', 'en-IE': 'uk',
                    'en-IN': 'uk', 'en-ZA': 'uk', 'en-CA': 'uk-ize'}
LANGUAGES = ('fa', 'en', 'bilingual')
SPELLINGS = ('us', 'uk', 'uk-ize')
CONTRACTIONS = ('use', 'avoid', 'positive-only')
HOUSE_STYLES = ('chicago', 'ap', 'microsoft', 'google', 'govuk', 'mailchimp')

# ---------------------------------------------------------------- word lists
# Catalog EN-AI-001 (Wikipedia "Signs of AI writing"; Kobak et al. 2025; Juzek & Ward 2025;
# Liang et al. 2024), plural forms added.
_AI_VOCAB = _rx(
    r"\b(?:delv(?:e|es|ed|ing)|tapestr(?:y|ies)|testaments?|underscor(?:es|ed|ing)"
    r"|underscore(?=\s+(?:the|that|its|their|his|her|how|why|a|an|our|this|these|those)\b)"
    r"|showcas(?:e|es|ed|ing)|pivotal|intricac(?:y|ies)|intricate(?:ly)?|meticulous(?:ly)?|realms?"
    r"|garner(?:s|ed|ing)?|boast(?:s|ed|ing)?|commendable|bolster(?:s|ed|ing)?|interplay|camaraderie"
    r"|palpable|noteworthy)\b", re.I)
_AI_LEMMAS = ('delv', 'tapestr', 'testament', 'underscor', 'showcas', 'pivotal', 'intrica', 'meticulous',
              'realm', 'garner', 'boast', 'commendable', 'bolster', 'interplay', 'camaraderie', 'palpable',
              'noteworthy')
# Catalog EN-AI-003 plus the spec additions (harness, embark, "take it to the next level")
_BUZZ = _rx(
    r"\b(?:vibrant|seamless(?:ly)?|robust(?:ly)?|leverag(?:e|es|ed|ing)|unlock(?:s|ed|ing)?"
    r"|elevat(?:e|es|ed|ing)|empower(?:s|ed|ing|ment)?|foster(?:s|ed|ing)?"
    r"|(?:evolving|ever-evolving|digital|competitive|business) landscape|holistic|cutting-edge"
    r"|state-of-the-art|game-?chang(?:er|ers|ing)|groundbreaking|revolutioni[sz](?:e|es|ed|ing)|renowned"
    r"|nestled|in the heart of|diverse array|rich (?:cultural )?heritage|commitment to|streamlin(?:e|es|ed|ing)"
    r"|synerg(?:y|ies)|best-in-class|world-class|transformative|navigat(?:e|ing) the complexities"
    r"|harness(?:es|ed|ing)?|embark(?:s|ed|ing)?|take (?:it|things|your \w+) to the next level)\b", re.I)

JARGON_EN = ['synergy', 'synergies', 'bandwidth', 'circle back', 'deep dive', 'low-hanging fruit',
             'move the needle', 'best-in-class', 'value-add', 'paradigm']
_JARGON = _rx(r"\b(?:synerg(?:y|ies)|bandwidth|circle back|deep[- ]dive|low-hanging fruit|move the needle"
              r"|best-in-class|value-add|paradigms?)\b", re.I)

_COMPLEX = [
    ('at this point in time', 'now'), ('due to the fact that', 'because'), ('at the present time', 'now'),
    ('in accordance with', 'under'), ('for the purpose of', 'to, or for'), ('has the ability to', 'can'),
    ('in the event that', 'if'), ('in the amount of', 'for'), ('in the event of', 'if'),
    ('with regard to', 'about'), ('in order that', 'so'), ('subsequent to', 'after'),
    ('approximately', 'about'), ('subsequently', 'later'), ('in regard to', 'about'),
    ('utilization', 'use'), ('in order to', 'to'), ('methodology', 'method'), ('a number of', 'some'),
    ('demonstrate', 'show'), ('facilitate', 'help'), ('promulgate', 'issue'), ('assistance', 'help'),
    ('sufficient', 'enough'), ('is able to', 'can'), ('additional', 'more, or extra'),
    ('implement', 'carry out, or do'), ('endeavour', 'try'), ('ascertain', 'find out'), ('terminate', 'end'),
    ('commence', 'start'), ('prior to', 'before'), ('numerous', 'many'), ('endeavor', 'try'),
    ('purchase', 'buy'), ('initiate', 'start'), ('utilize', 'use'), ('utilise', 'use'), ('assist', 'help'),
]
_COMPLEX_MAP = dict(_COMPLEX)
_COMPLEX_RX = _rx(r"\b(?:%s)\b" % '|'.join(re.escape(k) for k, _ in _COMPLEX), re.I)

LEXICON = {
    'cliche-open': ["In today's fast-paced world", 'In a world where', 'Welcome to the world of',
                    'Look no further', "Whether you're X or Y"],
    'journey': ['journey', 'unlock your potential', 'elevate your experience'],
    'moral-close': ['Because at the end of the day', 'After all, ... is what matters'],
    'clickbait': ["You won't believe", 'This one trick', 'Shocking'],
    'ai-vocab': ['delve', 'tapestry', 'testament', 'underscore', 'showcase', 'pivotal', 'intricate', 'meticulous',
                 'realm', 'garner', 'boast', 'commendable', 'bolster', 'interplay', 'camaraderie', 'palpable',
                 'noteworthy'],
    'buzzword': ['vibrant', 'seamless', 'robust', 'leverage', 'unlock', 'elevate', 'empower', 'foster',
                 'evolving landscape', 'holistic', 'cutting-edge', 'state-of-the-art', 'game-changer',
                 'groundbreaking', 'revolutionize', 'renowned', 'nestled', 'in the heart of', 'diverse array',
                 'rich heritage', 'commitment to', 'streamline', 'synergy', 'best-in-class', 'world-class',
                 'transformative', 'navigate the complexities', 'harness', 'embark', 'take it to the next level'],
}
# Which LEXICON entry a match of a phrase-list rule belongs to (the start of the matched text,
# case-insensitive), so the Hub can address one phrase by its lx- id (spec 5.3 step 2, 5.5).
_LEX_ATTR = {
    'cliche-open': [(0, r"in today{A}s\b"), (1, 'in a world where'), (2, 'welcome to the world of'),
                    (3, 'look no further'), (4, r"whether you{A}re\b")],
    'journey': [(0, r'journeys?\b'), (1, r'unlock\b'), (2, r'elevate\b')],
    'moral-close': [(0, '(?:because )?at the end of the day'), (1, 'after all')],
    'clickbait': [(0, 'you won'), (1, r'(?:this|one)\b'), (2, 'shocking')],
    'ai-vocab': [(0, 'delv'), (1, 'tapestr'), (2, 'testament'), (3, 'underscor'), (4, 'showcas'), (5, 'pivotal'),
                 (6, 'intrica'), (7, 'meticulous'), (8, 'realm'), (9, 'garner'), (10, 'boast'), (11, 'commendable'),
                 (12, 'bolster'), (13, 'interplay'), (14, 'camaraderie'), (15, 'palpable'), (16, 'noteworthy')],
    'buzzword': [(0, 'vibrant'), (1, 'seamless'), (2, 'robust'), (3, 'leverag'), (4, 'unlock'), (5, 'elevat'),
                 (6, 'empower'), (7, 'foster'),
                 (8, '(?:evolving|ever-evolving|digital|competitive|business) landscape'),
                 (9, 'holistic'), (10, 'cutting-edge'), (11, 'state-of-the-art'), (12, 'game-?chang'),
                 (13, 'groundbreaking'), (14, 'revolutioni'), (15, 'renowned'), (16, 'nestled'),
                 (17, 'in the heart of'), (18, 'diverse array'), (19, 'rich (?:cultural )?heritage'),
                 (20, 'commitment to'), (21, 'streamlin'), (22, 'synerg'), (23, 'best-in-class'), (24, 'world-class'),
                 (25, 'transformative'), (26, 'navigat'), (27, 'harness'), (28, 'embark'), (29, 'take ')],
}


@functools.lru_cache(maxsize=256)
def lx_pid(category, phrase):
    """lx-en- plus the first 10 hex of SHA-256("en|" + category + "|" + NFC(phrase)) (spec 5.5)."""
    text = unicodedata.normalize('NFC', phrase)
    return 'lx-en-' + hashlib.sha256(('en|%s|%s' % (category, text)).encode('utf-8')).hexdigest()[:10]


_LEX_ATTR_RX = {}


def _lex_pid(category, text):
    """The lx- id of the LEXICON entry a phrase-list match belongs to, or None."""
    rows = _LEX_ATTR_RX.get(category)
    if rows is None:
        rows = [(LEXICON[category][i], _rx(p, re.I)) for i, p in _LEX_ATTR.get(category, ())]
        _LEX_ATTR_RX[category] = rows
    t = (text or '').strip()
    for phrase, rx in rows:
        if rx.match(t):
            return lx_pid(category, phrase)
    return None

_ABBR_OK = set('''API APIs URL URLs HTML CSS PDF PDFs FAQ FAQs CEO CEOs CFO CTO COO USA US UK EU UN AI SMS OTP SEO
CTA CTAs SaaS B2B B2C DTC iOS OK TV ID IDs PR HR IT UI UX JSON CSV TSV XML HTTP HTTPS SQL MB GB KB TB AM PM UTC GMT
USB VAT GPS DIY FAQ PIN PINs NGO NGOs ATM ATMs CV CVs LLC PhD MBA BBC CNN NASA NATO DNA RSS QR PS PPS RSVP ASAP TBD
AI-generated AR VR CRM ERP KPI KPIs ROI SDK SDKs CLI IDE PWA SSO MFA VPN IP LLM LLMs GPT MCP PNG JPG JPEG GIF SVG
MP3 MP4 USD EUR GBP CAD AUD IRR NZ AU CA IN ISBN DOI URL HTML5 FAQ UTF AP MIT
STOP HELP YES NO CANCEL START END QUIT INFO JOIN UNSTOP SUBSCRIBE UNSUBSCRIBE'''.split())   # last row: SMS keywords
_ROMAN = re.compile(r'^(?:M{0,3})(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})$')

# ---------------------------------------------------------------- US/UK spelling families
# Families from the R3 research data (us_uk_families; source:
# https://en.wikipedia.org/wiki/American_and_British_English_spelling_differences), with
# inflected forms. Ambiguous items are left out on purpose: program/programme, check/cheque,
# tire/tyre, license/licence, practice/practise, meter/metre, dialog/dialogue (computing),
# prolog (a language), percent/per cent, and "analyses" (also the plural of analysis).
_OR = ['color', 'behavior', 'favor', 'honor', 'humor', 'labor', 'neighbor', 'flavor', 'harbor', 'rumor',
       'vapor', 'endeavor', 'armor', 'savior']
_OR_SUF = ['', 's', 'ed', 'ing', 'ful', 'fully', 'less', 'able', 'ably', 'ite', 'ites', 'hood', 'hoods',
           'al', 'ally', 'y', 'ies', 'er', 'ers', 'ly']
_ER = ['center', 'theater', 'fiber', 'liter', 'caliber', 'somber', 'specter', 'luster', 'meager', 'saber',
       'scepter']
_IZE = ['organ', 'real', 'recogn', 'optim', 'priorit', 'custom', 'final', 'apolog', 'author', 'emphas',
        'summar', 'minim', 'maxim', 'standard', 'categor', 'special', 'personal', 'visual', 'critic', 'memor',
        'modern', 'normal', 'util', 'familiar', 'stabil', 'synchron', 'sympath', 'symbol', 'global', 'local',
        'monet', 'digit', 'energ', 'mobil', 'capital', 'central', 'commercial', 'character']
_IZE_SUF = [('ize', 'ise'), ('izes', 'ises'), ('ized', 'ised'), ('izing', 'ising'), ('izer', 'iser'),
            ('izers', 'isers'), ('ization', 'isation'), ('izations', 'isations'), ('izable', 'isable')]
_YZE = ['anal', 'paral', 'catal']
_YZE_SUF = [('yze', 'yse'), ('yzed', 'ysed'), ('yzing', 'ysing'), ('yzer', 'yser'), ('yzers', 'ysers')]
_PAIRS = {
    'l-ll': [('traveled', 'travelled'), ('traveling', 'travelling'), ('traveler', 'traveller'),
             ('travelers', 'travellers'), ('canceled', 'cancelled'), ('canceling', 'cancelling'),
             ('labeled', 'labelled'), ('labeling', 'labelling'), ('modeling', 'modelling'),
             ('modeled', 'modelled'), ('modeler', 'modeller'), ('counselor', 'counsellor'),
             ('counselors', 'counsellors'), ('signaling', 'signalling'), ('signaled', 'signalled'),
             ('fueled', 'fuelled'), ('fueling', 'fuelling'), ('leveled', 'levelled'), ('leveling', 'levelling'),
             ('marvelous', 'marvellous'), ('fulfillment', 'fulfilment'), ('fulfill', 'fulfil'),
             ('fulfills', 'fulfils'), ('enrollment', 'enrolment'), ('enrollments', 'enrolments'),
             ('enroll', 'enrol'), ('enrolls', 'enrols'), ('installment', 'instalment'),
             ('installments', 'instalments'), ('skillful', 'skilful'), ('skillfully', 'skilfully'),
             ('willful', 'wilful'), ('jewelry', 'jewellery')],
    'og-ogue': [('catalog', 'catalogue'), ('catalogs', 'catalogues'), ('cataloged', 'catalogued'),
                ('cataloging', 'cataloguing'), ('analog', 'analogue'), ('analogs', 'analogues')],
    'se-ce': [('defense', 'defence'), ('defenses', 'defences'), ('defenseless', 'defenceless'),
              ('offense', 'offence'), ('offenses', 'offences'), ('pretense', 'pretence'), ('pretenses', 'pretences')],
    'ae-oe': [('anemia', 'anaemia'), ('anemic', 'anaemic'), ('anesthesia', 'anaesthesia'),
              ('anesthetic', 'anaesthetic'), ('pediatric', 'paediatric'), ('pediatrics', 'paediatrics'),
              ('pediatrician', 'paediatrician'), ('esophagus', 'oesophagus'), ('estrogen', 'oestrogen'),
              ('fetus', 'foetus'), ('fetal', 'foetal'), ('leukemia', 'leukaemia'), ('hemoglobin', 'haemoglobin')],
    'drop-e': [('aging', 'ageing'), ('likable', 'likeable'), ('sizable', 'sizeable')],
    'misc': [('gray', 'grey'), ('grays', 'greys'), ('grayish', 'greyish'), ('aluminum', 'aluminium'),
             ('maneuver', 'manoeuvre'), ('maneuvers', 'manoeuvres'), ('maneuvered', 'manoeuvred'),
             ('maneuvering', 'manoeuvring'), ('maneuverable', 'manoeuvrable')],
}


def _build_spelling():
    """{form: (family, side, counterpart)}; side is 'us' or 'uk'."""
    forms = {}

    def add(fam, us, uk, both=True):
        forms.setdefault(us, (fam, 'us', uk))
        if both:
            forms.setdefault(uk, (fam, 'uk', us))

    for b in _OR:
        stem = b[:-2]
        for s in _OR_SUF:
            if s == 'ies':
                add('or-our', stem + 'ories', stem + 'ouries')
            elif s == 'y':
                add('or-our', stem + 'ory', stem + 'oury')
            else:
                add('or-our', b + s, stem + 'our' + s)
    for b in _ER:
        stem = b[:-2]
        add('er-re', b, stem + 're')
        add('er-re', b + 's', stem + 'res')
        add('er-re', stem + 'ered', stem + 'red')
        add('er-re', stem + 'ering', stem + 'ring')
    for stem in _IZE:
        for us, uk in _IZE_SUF:
            add('ize-ise', stem + us, stem + uk)
    for stem in _YZE:
        for us, uk in _YZE_SUF:
            add('yze-yse', stem + us, stem + uk)
        add('yze-yse', stem + 'yzes', stem + 'yses', both=False)   # "analyses" is also a plural noun
    for fam, pairs in _PAIRS.items():
        for us, uk in pairs:
            add(fam, us, uk)
    return forms


SPELLING_FORMS = _build_spelling()
US_UK_FAMILIES = {}
for _k, (_fam, _side, _other) in SPELLING_FORMS.items():
    if _side == 'us':
        US_UK_FAMILIES.setdefault(_fam, []).append([_k, _other])

# ---------------------------------------------------------------- rule patterns
_SENT_START = r"(?:^[ \t]*(?:>[ \t]?)*(?:(?:[-*+•]|\d{1,3}[.)])[ \t]+)?|(?<=[.!?][ \t]))"

_SIGNIF = _rx(
    r"\b(?:stands as|serves as a (?:testament|reminder|symbol|beacon)|is a testament to|a testament to"
    r"|plays? an? (?:vital|crucial|pivotal|key|significant|important|central) role"
    r"|mark(?:s|ed|ing)? an? (?:pivotal|significant|key|major|important) (?:moment|shift|milestone|turning point)"
    r"|setting the stage for|left an indelible mark|indelible mark|deeply rooted|enduring legacy|lasting legacy"
    r"|reflects? (?:a )?broader|evolving landscape|key turning point|focal point|represents? a (?:significant )?shift)\b",
    re.I)
_COPULA = _rx(r"\b(?:serves|served|stands|stood|functions|functioned|operates|operated) as (?:a|an|the)\b", re.I)
_ING = _rx(r",[ \t]+(?P<at>(?:highlighting|underscoring|emphasi[sz]ing|showcasing|reflecting|symboli[sz]ing|ensuring"
           r"|fostering|cultivating|contributing to|enhancing|solidifying|cementing|reinforcing"
           r"|further (?:highlighting|underscoring))\b)", re.I)
_ING_END = re.compile(r"[.!?\n]")
_VAGUE_ATTR = _rx(
    r"\b(?:(?:many |some |several |leading |most )?(?:experts|observers|critics|analysts|scholars|researchers"
    r"|commentators|industry (?:reports|insiders|observers))\s+(?:say|says|argue|argued|suggest|believe|agree|note"
    r"|noted|have (?:noted|cited|argued|suggested))|(?:it is|it{A}s) (?:widely|generally|commonly) (?:believed"
    r"|accepted|recognized|recognised|regarded|acknowledged)|studies (?:show|suggest|have shown)"
    r"|research (?:shows|suggests|has shown))\b", re.I)
_MEDIA = _rx(
    r"\b(?:(?:has been |was )?(?:featured|profiled|highlighted|covered) (?:in|by) (?:multiple|numerous|various"
    r"|several|leading|prominent|major|other)\b|independent coverage|(?:maintains|has) an? (?:active|strong|robust)"
    r" (?:social media|online|digital) presence|widely covered|garnered (?:significant |widespread )?(?:attention"
    r"|acclaim|recognition))", re.I)
_NOT_JUST = _rx(r"\bnot (?:just|only|merely|simply)\b[^.?!\n]{1,80}?\bbut(?: also)?\b", re.I)
_NOT_X = _rx(
    r"\b(?:(?:it|this|that)(?:{A}s| is) not|(?:it|this|that) isn{A}t)\s+(?:just\s+|only\s+|merely\s+)?(?:about\s+)?"
    r"[^.?!,;\n]{1,60}?(?:[,;:]|\s[—–-]\s|—|\.)\s*(?:it{A}s|it is|this is|that{A}s|but)\b"
    r"|\bisn{A}t about\s+[^.?!,;\n]{1,60}?(?:[,;:]|\s[—–-]\s|—|\.)\s*(?:it{A}s|it is) about\b", re.I)
_NO_X = _rx(r"\bno [^,.;\n]{1,30}, no [^,.;\n]{1,30}(?:,|—|–| -)\s*(?:just|only)\b", re.I)
_SUMMARY = _rx(_SENT_START + r"(?P<at>(?:In conclusion|In summary|To summari[sz]e|To sum up|Overall|All in all"
               r"|Ultimately|In essence),)", re.M)
_CHALLENGES = _rx(r"\bDespite (?:its|their|these|the|this)\b[^.\n]{0,100}\b(?:faces?|faced|challenges)\b"
                  r"|^[ \t]{0,3}#{1,6}[ \t]*(?:Challenges(?: and (?:Legacy|Future (?:Prospects|Outlook|Directions)))?"
                  r"|Future (?:Outlook|Prospects))[ \t]*$", re.I | re.M)
_DIDACTIC = _rx(r"\b(?:it{A}?s|it is) (?:important|crucial|critical|essential|worth) (?:to (?:note|remember|consider"
                r"|mention)|noting|mentioning)\b|\bworth noting\b|\bresults may vary\b", re.I)
_CHATBOT = _rx(
    r"^[ \t]*(?P<a1>(?:Certainly|Of course|Absolutely|Sure thing)!)|^[ \t]*(?P<a2>(?:Great|Excellent|What a great)"
    r" question[!,.])|\bI hope this helps\b|\bWould you like me to\b|\bIs there anything else (?:I can|you{A}d like"
    r"|you would like)\b|\bHere(?:{A}s| is) (?:a|an|the|your) (?:revised|polished|improved|refined|rewritten|updated)"
    r" (?:version|draft|text|copy)\b|\bHere(?:{A}s| is) (?:a|the|your) (?:revised|polished|improved|refined|rewritten)"
    r" (?:post|caption|email|paragraph)\b|\bAs an AI(?: language model)?\b|\bAs a large language model\b"
    r"|\bYou{A}re absolutely right\b", re.I | re.M)
_SIGNOFF = _rx(r"\b(?:let me know|feel free to (?:ask|reach out)) if\b", re.I)
_CUTOFF = _rx(
    r"\b(?:as of my (?:last )?(?:knowledge|training) (?:update|cutoff|cut-off)|up to my last training"
    r"|my knowledge cutoff|based on (?:the )?(?:available|provided) (?:information|sources|search results)"
    r"|while specific details are (?:limited|scarce)|not widely (?:documented|disclosed|reported)"
    r"|(?:maintains|keeps) a low profile|keeps (?:his|her|their) personal (?:life|details) private)\b", re.I)
_TEMPLATE_I = _rx(r"\bLorem ipsum\b|\b20(?:\d\d|xx)-xx-xx\b|\[(?:Your|Insert)\b[^\]\n]{0,40}\]", re.I)
_TEMPLATE_C = _rx(r"\bTBD\b|\bXX+%")
_TEMPLATE_VAR = _rx(r"\{\{[ \t]*[A-Za-z_][\w.]*[ \t]*\}\}")
_MARKUP = _rx(r"oaicite|contentReference\[|turn\d+(?:search|news|view)\d+|attributableIndex|\[cite:\s*\d+\]"
              r"|\[span_\d+\]\(start_span\)|grok_card|grok_render_citation_card_json|【\d+†"
              r"|utm_source=(?:chatgpt\.com|openai|copilot\.com|perplexity)|ppl-ai-file-upload|:::writing", re.I)
_TITLE_CASE = _rx(r"^[ \t]{0,3}#{1,6}[ \t]+(?:[A-Z][\w{AC}-]*[ \t]+)(?:(?:a|an|the|and|or|of|in|on|for|to|with|by|at)"
                  r"[ \t]+|[A-Z][\w{AC}-]*[ \t]+){1,}[A-Z][\w{AC}-]*[ \t]*$", re.M)
_BOLD = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__")
_INLINE_HDR = re.compile(r"^[ \t]*(?:[-*•]|\d+\.)[ \t]+\*\*[^*\n]{1,60}?:?\*\*[ \t]*:?[ \t]")
_EMOJI_START = re.compile(r"^[ \t]*(?:[-*•][ \t]*|#{1,6}[ \t]*)?(?:%s)" % EMOJI.pattern)
_VAGUE_ASSOC = _rx(r"\b(?:(?:closely |widely |particularly )?associated with|in connection (?:with|to)"
                   r"|connected (?:with|to))\b", re.I)
_ADDITIONALLY = _rx(_SENT_START + r"(?P<at>(?:Additionally|Furthermore|Moreover|Notably),)", re.M)
_MARKETING_HAS = _rx(r"\b(?:boasts|features|offers)\s+(?:a|an|over|more than|\d)\b", re.I)
_SYCO = _rx(r"\b(?:great|excellent|fantastic|wonderful|insightful) (?:question|point|observation)s?\b"
            r"|\bwhat a (?:great|fantastic|wonderful) (?:question|point|idea|observation)\b", re.I)
_STAT = _rx(r"(?<![\w.,])\d[\d,]*(?:\.\d+)?[ \t]?(?:%|percent\b|per cent\b|x\b|×|times\b|million\b"
            r"|billion\b|trillion\b)", re.I)
_DISCOUNT_AFTER = re.compile(r"[ \t]*(?:off|discount|cashback)\b", re.I)
_DISCOUNT_BEFORE = re.compile(r"\b(?:save|saving|extra|up to)[ \t]+$", re.I)
_SUPERLATIVE = _rx(
    r"\b(?:the (?:best|leading|largest|fastest|cheapest|most (?:trusted|popular|advanced|secure))"
    r"|the (?:first|only)(?: (?!(?:is|are|was|were|will|can|has|have|had|do|does)\b)[\w-]+){1,2}"
    r" (?:to|that|who|which|ever|of its kind)"
    r"|world{A}?s (?:first|leading|best|largest|fastest)|number one|no\.? ?1|unmatched|unparalleled"
    r"|unrivall?ed|guaranteed)\b|(?<![\w#])#1\b|\b100% (?:safe|secure|effective|guaranteed|accurate)\b", re.I)
_ESTABLISH = _rx(r"\b(?:clinically|scientifically|independently|lab)[- ](?:proven|tested|validated)\b"
                 r"|\b(?:tests|studies|research) (?:prove|proves|show|shows|confirm|confirms)\b"
                 r"|\b(?:doctors|dentists|dermatologists|experts) (?:recommend|approve)\b", re.I)
# A quote with an attribution on the same line: — Name, ~ Name, "…," says Name, "…," Name said.
# A placeholder name ([customer name], masked) counts as a name.
_T_NAME = r"(?:[A-Z][A-Za-z{AC}\-]+\.?(?:[ \t]+(?:[A-Z][A-Za-z{AC}\-]*\.?|(?:de|van|von|da|di|al|bin)(?=[ \t])))*|%s{3,})" % MASK
_T_SAYS = r"(?:said|says|writes|wrote|adds|added|explains|explained|recalls|recalled)"
_T_IMPERSONAL = r"(?!(?:It|This|That|These|Those|There|Which|What)[ \t])"   # '"…" It adds' is not a name
_TESTIMONIAL = _rx(r"[\"“](?P<q>[^\"“”\n]{10,300})[\"”][ \t]*(?:(?:—|–|--?|~)[ \t]*" + _T_NAME +
                   r"|,?[ \t]*" + _T_SAYS + r"[ \t]+" + _T_NAME + r"|" + _T_IMPERSONAL + _T_NAME + r"[ \t]+" +
                   _T_SAYS + r"\b)")
_DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
_ISBN = re.compile(r"\bISBN(?:-1[03])?:?[ \t]*(?P<n>[0-9X][0-9X -]{8,16}[0-9X])\b", re.I)
_PASSIVE = _rx(r"\b(?:am|is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?(?:\w{2,}ed|built|done|made|given|taken"
               r"|shown|known|seen|written|sent|paid|held|found|kept|left|told|brought|bought|set|put|run|chosen"
               r"|driven|drawn|grown|thrown|won|lost|met|read|led)\b", re.I)
_HIDDEN = _rx(r"\b(?:conduct(?:ed|s|ing)?|perform(?:ed|s|ing)?|make|made|makes|making|give|gave|gives|giving"
              r"|provide[sd]?|providing|reach(?:ed|es)?|achieve[sd]?|effect(?:ed|s)?|take|took|takes|taking"
              r"|carry out|carried out|carries out)\s+(?:an?|the)\s+(?:\w+\s+)?\w+(?:tion|sion|ment|ance|ence"
              r"|ancy|ency|sis)\b", re.I)
_SHALL = re.compile(r"\bshall\b", re.I)
_DOUBLE_NEG = _rx(
    r"\bnot[ \t]+(?:un(?!der|iq|it|iv|if|io|til|less|to\b)[a-z]{3,}|in(?:significant|frequent|correct|accurate"
    r"|considerable|valid|appropriate|expensive|effective|consistent|complete|capable|conceivable|credible"
    r"|dispensable|elegant)\b|im(?:possible|probable|material|proper|practical|mune)\b|dis(?:similar|agreeable"
    r"|pleased|honest|like|liked|likes)\b|non-?[a-z]{3,})|\bno fewer than\b|\bnot[ \t]+[^.\n]{0,40}\bunless\b"
    r"|\bhas not yet attained\b", re.I)
_SLASH = _rx(r"\band/or\b|(?<![/:.\w#-])[A-Za-z]{2,}/[A-Za-z]{2,}\b(?![/.#-])", re.I)   # paths and file names skipped
_PLEASE_NOTE = _rx(r"\b(?:please note|kindly note|be advised|it should be noted)\b", re.I)
_MINIMIZER = _rx(r"\b(?:simply|just|easily|obviously|quickly|it{A}?s (?:easy|that simple))\b", re.I)
_THERE_IS = _rx(_SENT_START + r"(?P<at>There (?:is|are|was|were)\b)", re.M)
_METAPHOR = _rx(r"\b(?:going forward|moving forward|drive (?:growth|change|innovation|results|engagement)|drive out"
                r"|one-stop shop|ring[- ]?fenc(?:e|ed|ing)|deliver (?:improvements|value|outcomes|results|change)"
                r"|tackle|slim down|overarching|disincentivi[sz]e|incentivi[sz]e|liaise|dialogue)\b", re.I)
_NUMERIC_DATE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")
_NUM_START = re.compile(r"[ \t(%s]*(\d[\d,.]*)\b" % MASK)
_RANGE = re.compile(r"(?<![\d\-–/.])\d+(?:am|pm)?[ \t]?[-–][ \t]?\d+(?:am|pm)?\b(?![-–/]\d)", re.I)
_AMP = re.compile(r"(?<=[ \t])&(?=[ \t])")
_HEAD_PUNCT = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+\S.*?(?<![.:])(?P<at>[.:])[ \t]*$", re.M)
_DOUBLE_SPACE = re.compile(r"(?<=[.?!:])  +(?=[^\s|])")
_LINK_MD = re.compile(r"\[(?P<t>click here|here|read more|more|this link|learn more|link)\](?=[(\[])", re.I)
_LINK_HTML = re.compile(r"<a\b[^<>]*>\s*(?P<t>click here|here|read more|more|learn more)\s*</a>", re.I)
_ALL_CAPS = re.compile(r"\b(?:[A-Z]{2,}[ \t]+){4,}[A-Z]{2,}\b")
_LATIN_ABBR = re.compile(r"\b(?:e\.g\.|i\.e\.|etc\.?|eg|ie|viz\.)(?=[\s,)]|$)", re.I)
_CONTRACTION = _rx(r"\b(?:[A-Za-z]+n{A}t|(?:I|you|we|they|he|she|it|that|there|here|what|who|where|let)"
                   r"{A}(?:m|re|ve|ll|d|s))\b", re.I)
_NEG_CONTRACTION = _rx(r"\b[A-Za-z]+n{A}t\b", re.I)
_EXPANDED = _rx(r"\b(?:do not|does not|did not|is not|are not|was not|were not|cannot|could not|would not"
                r"|should not|will not|have not|has not|had not|we will|we are|you are|you will|they are|I am|I will"
                r"|let us)\b", re.I)
_RHETORICAL = _rx(r"^\W*(?:Ever (?:wondered|wonder|thought)|Did you know|Have you ever (?:wondered|thought)"
                  r"|Imagine\b|What if\b)", re.I)
_CLICHE_OPEN = _rx(r"\bIn today{A}s (?:fast-paced |digital |modern |competitive |busy )?(?:world|age|landscape)\b"
                   r"|\bIn a world where\b|\bWelcome to the world of\b|\bLook no further\b"
                   r"|\bWhether you{A}re (?:a |an )?[^,.?!\n]{1,40}? or (?:a |an )?[^,.?!\n]{1,40}?,", re.I)
_JOURNEY = _rx(r"(?<!customer )(?<!user )(?<!buyer )(?<!patient )\bjourneys?\b"
               r"|\bunlock (?:your|their|its) (?:full |true )?potential\b"
               r"|\belevate your (?:experience|game|brand|style|space)\b", re.I)
_MORAL_CLOSE = _rx(r"\b(?:Because )?at the end of the day\b"
                   r"|\bAfter all, [^.?!\n]{1,60}? (?:is|are) what (?:really |truly )?matters?\b", re.I)
_CLICKBAIT = _rx(r"\bYou won{A}t believe\b|\b(?:This|One) (?:one |simple |weird )?trick\b|\bShocking\b", re.I)
_URL_RX = LF._URL
_CORE_SUFFIX_EN = re.compile(r"(?<![ \t])[ \t]*\(in Whalory Pro\)")
_WORD = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9'’\-]*[A-Za-z0-9])?")
_ABBR_TOKEN = re.compile(r"(?<![\w\-])[A-Z]{2,6}s?(?![\w\-]|\.\w)")
_ABBR_PAREN = re.compile(r"\(([A-Z]{2,6})s?\)")
_ABBR_DEF = re.compile(r"[A-Za-z0-9][ \t]\((?:[A-Z0-9][A-Z0-9.\-]*[ \t])+$")
_HASHTAG_LINE = re.compile(r"^[ \t]*(?:[#@][^\s#@]+[ \t]*)+$")
_LINK_ONLY = re.compile(r"[ \t]*\[[^\[\]\n]{1,300}\]\([^()\s]{0,500}\)[ \t.;,]*$")
_MD_HEADING = re.compile(r"^[ \t]{0,3}(#{1,6})[ \t]+")
# Lists for the serial-comma and triad rules: a comma series that ends in "and" or "or".
# A word list, not a pattern: each "and"/"or" is read back to the last comma and the items are
# checked one by one, in bounded windows (linear time). Function words tell a list item from
# an appositive, a trailing phrase or a second clause.
_L_PREP = set('''about above across after against along amid among around as at before behind below beneath beside
besides between beyond by despite down during except for from in inside into like near of off on onto out outside
over past per plus minus since than through throughout till to toward towards under underneath unlike until up upon
via with within without versus vs'''.split())
_L_SUB = set('''and or but nor so yet if when whenever where wherever while whereas whether because although though
unless once that which who whom whose what how why then also such including'''.split())
_L_ADV = set('''not never only just even still too very often always sometimes usually already again now here there
later soon first finally instead otherwise however therefore thus clearly briefly simply either neither rather
quite ideally mostly mainly anywhere everywhere somewhere nowhere'''.split())
_L_PRON = set('''i you we they he she it them us him me myself yourself ourselves themselves itself himself herself
someone something anyone anything everyone everything nobody nothing'''.split())
_L_AUX = set('''is are was were be been being am has have had do does did will would can could should shall must may
might isn't aren't wasn't weren't don't doesn't didn't won't wouldn't can't cannot couldn't shouldn't mustn't
hasn't haven't hadn't it's that's there's here's what's who's'''.split())
_L_DET = set('''a an the one two three four five six seven eight nine ten each every any no some this these those
my your our their its his her all both several many few'''.split())
_L_NUMW = set('''one two three four five six seven eight nine ten eleven twelve fifteen twenty thirty forty fifty
hundred thousand dozen few several'''.split())
_L_NUM_NEXT = _L_NUMW | {'more', 'fewer', 'less', 'so'}
_L_APPOS = set('called named known based located founded dubbed titled labeled labelled'.split())
_L_START_BAD = _L_PREP | _L_SUB | _L_ADV | _L_PRON | _L_AUX | _L_APPOS   # cannot open a list item
_L_CLAUSE = _L_PRON | _L_AUX                                      # a clause, not an item
_L_INTRO = _L_PREP | _L_SUB | _L_ADV                              # "In June, …", "If so, …"
_L_WH = set('what who whom whose where when why how which'.split())
_L_PERSONAL = set('i you we they he she it them us him me'.split())
_L_INTRO_CLAUSE = set('when whenever if because although though while whereas whether unless once since as where '
                      'wherever'.split())      # "When it rains, …": an opening clause, not a list item
# the last item of a serial list may open with a wh-word, "not", "just" or a preposition ("and by
# when", "and not misleading", "and about the product"); never with a pronoun, a verb or "then"
_L_C_SERIAL_BAD = _L_PERSONAL | _L_AUX | (_L_SUB - _L_WH) | (_L_ADV - {'not', 'just'})
_L_CONJ = _rx(r"(?<![\w{AC}/&\-])(?:and|or)(?![\w{AC}/&\-])", re.I)
_L_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’&/\-]*")
_L_STOP = frozenset('.;:!?()[]{}"“”—–|<>' + MASK + BLOCK)
_L_LIGHT = ' \t*_%$£€#+~\u00a0'          # symbols an item may carry besides words
_L_SUFFIX = re.compile(r"(?<![\w-])-(?=[A-Za-z])")
_L_C_WORDS = re.compile(r"[ \t]+([A-Za-z0-9][A-Za-z0-9'’&/\-]*(?:[ \t]+[A-Za-z0-9][A-Za-z0-9'’&/\-]*){0,3})")
_L_STOP_RX = re.compile('[%s]' % re.escape(''.join(sorted(_L_STOP))))
_L_QUOTE_RX = re.compile('["“”]')
_L_LINK_TEXT = re.compile(r"\[[^\[\]\n]{0,300}\]\(")
_L_LINK_OUT = re.compile(r"\[[^\[\]\n]{0,300}\]\((?:https?:|www\.|mailto:)", re.I)   # a page someone else titled
_L_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3})")     # 8,000 is one number, not two items
_L_LATER = re.compile(r",[ \t]+(?:and|or)[ \t]", re.I)
_L_LOOK = 600                              # characters read back from a conjunction
_MONTHS = set('''january february march april may june july august september october november december jan feb mar
apr jun jul aug sep sept oct nov dec'''.split())
_NUM_PREV = set('''step steps page pages chapter chapters version row rows column columns part parts phase level tier
grade no no. of number figure table section room item items'''.split()) | _MONTHS
_NUMERAL = re.compile(r"(?<![\d.,:$£€#/\-\w])(?P<n>\d{1,2})(?![\d\w]|[.,]\d|[ \t]?(?:%|percent\b|per cent\b"
                      r"|am\b|pm\b|a\.m\.|p\.m\.|px\b|cm\b|mm\b|kg\b|km\b|GB\b|MB\b|x\b|×|:|-\w|\)))", re.I)

# ---------------------------------------------------------------- rule catalog
# (id, severity, kind, ref, description, fix)
RULES = [
    ('en-ai-vocab', WARN, 'pattern', 'EN-AI-001',
     'Word over-represented in AI-written text (delve, tapestry, testament, underscore, showcase, pivotal, '
     'intricate, meticulous, realm, garner, boast, commendable, bolster, interplay, camaraderie, palpable, '
     'noteworthy)', 'Use the plain or specific word, or state the fact it points at'),
    ('en-ai-vocab-density', ERROR, 'dynamic', 'EN-AI-002',
     '3 or more distinct AI-vocabulary lemmas, or 5 or more distinct AI-vocabulary and buzzword lemmas, in a '
     '300-word window (texts of 150 words or more)', 'Rewrite from the facts up; do not swap synonyms'),
    ('en-buzzword', WARN, 'pattern', 'EN-AI-003',
     'Buzzword or puffery (vibrant, seamless, robust, leverage, unlock, elevate, empower, foster, cutting-edge, '
     'game-changer, harness, embark, "take it to the next level" …); off for words in the profile allow list',
     'Say what it does, for whom, with a number'),
    ('en-significance', WARN, 'pattern', 'EN-AI-010',
     'Inflated significance: stands as, a testament to, plays a pivotal role, marks a shift, indelible mark',
     'Delete, or give the sourced consequence'),
    ('en-copula-avoid', WARN, 'pattern', 'EN-AI-011', 'serves/stands/functions as a/an/the instead of is',
     'Use is or are'),
    ('en-ing-analysis', WARN, 'pattern', 'EN-AI-012',
     'Trailing ", highlighting/underscoring/ensuring/fostering …" clause that adds commentary',
     'Cut it, or make it a sentence with a source'),
    ('en-vague-attribution', ERROR, 'pattern', 'EN-AI-013',
     'Vague attribution: experts say, observers note, it is widely believed, studies show, research shows '
     '(not flagged when the line cites a URL, DOI or [source: …])', 'Name and link the source, or delete'),
    ('en-media-canned', WARN, 'pattern', 'EN-AI-014',
     'Canned media claims: featured in numerous outlets, independent coverage, active social media presence',
     'List real outlets with dates, or cut'),
    ('en-not-just', WARN, 'pattern', 'EN-AI-020', 'not just/only/merely X, but (also) Y', 'State Y'),
    ('en-not-x-but-y', WARN, 'pattern', 'EN-AI-021',
     "Straw-man contrast: it's not X, it's Y / isn't about X. It's about Y", 'Say Y; drop the straw man'),
    ('en-no-x-no-y', WARN, 'pattern', 'EN-AI-022', 'no X, no Y, just Z', 'One plain sentence plus evidence'),
    ('en-triads', WARN, 'dynamic', 'EN-AI-030',
     'Lists of exactly three items in 2 or more sentences per 100 words, or in 2 consecutive sentences (60 '
     'words or more; prose and list items, not headings or table cells)',
     'Keep only real lists of three'),
    ('en-dash-density', WARN, 'dynamic', 'EN-AI-031',
     'More than 1 em dash per 150 words, or more than 1 in a paragraph', 'Use commas, colons or full stops'),
    ('en-summary-opener', WARN, 'pattern', 'EN-AI-032',
     'Sentence opens with In conclusion, In summary, Overall, Ultimately, In essence …',
     'End on the last concrete point or the call to action'),
    ('en-challenges-outlook', WARN, 'pattern', 'EN-AI-033',
     '"Despite its …, faces challenges" or a Challenges / Future Outlook heading', 'Give specific, sourced problems, or drop'),
    ('en-didactic', WARN, 'pattern', 'EN-AI-034', "It's important/crucial/worth noting; results may vary",
     'State the fact'),
    ('en-chatbot-residue', ERROR, 'pattern', 'EN-AI-040',
     'Chat residue: Certainly! / Of course! / Great question / I hope this helps / Here is a revised version / '
     'As an AI; "let me know if" and "feel free to ask" are allowed in email, reply and bot formats', 'Remove'),
    ('en-cutoff-speculation', ERROR, 'pattern', 'EN-AI-041',
     'Knowledge-cutoff speculation: as of my last knowledge update, based on available information, not widely '
     'documented, maintains a low profile', 'Delete; use [source needed: …]'),
    ('en-template-residue', ERROR, 'pattern', 'EN-AI-042',
     'Template residue: Lorem ipsum, TBD, XX%, 20xx-xx-xx, {{var}} in prose (not in locale files), [Your …], '
     '[Insert …]. Whalory brackets such as [confirm: …] and [source needed: …] are not flagged; they are '
     'counted in stats.placeholders', 'Fill it in, or use a Whalory bracket'),
    ('en-chatbot-markup', ERROR, 'pattern', 'EN-AI-043',
     'Chatbot citation artifacts: oaicite, contentReference[, turn0search0, [cite: N], grok_card, '
     'utm_source=chatgpt.com …', 'Delete it and re-check the claim'),
    ('en-title-case-heading', WARN, 'pattern', 'EN-AI-050',
     'Title Case Markdown heading (off when house_style is chicago; AP headlines use sentence case)',
     'Use sentence case'),
    ('en-bold-overuse', WARN, 'dynamic', 'EN-AI-051', 'More than 1 bold span per 100 words of prose (--md)',
     'Remove bold from running text'),
    ('en-inline-header-bullets', WARN, 'dynamic', 'EN-AI-052',
     '3 or more consecutive "- **Header:** text" bullets (--md)', 'Use prose, or plain bullets'),
    ('en-emoji-format', WARN, 'pattern', 'EN-AI-053',
     'Emoji at the start of a line, bullet or heading (off for caption, story, reels)',
     'Remove it in professional copy'),
    ('en-quote-mix', WARN, 'dynamic', 'EN-AI-054', 'Straight and curly quotes or apostrophes in the same text',
     'Normalize to one style (--fix uses the majority)'),
    ('en-vague-association', WARN, 'pattern', 'EN-AI-060',
     'associated with / in connection with / connected to (long formats, or no format)', 'State the relation'),
    ('en-additionally', WARN, 'dynamic', 'EN-AI-061',
     'Sentence-initial Additionally/Furthermore/Moreover/Notably: 2 or more, and more than 1 per 200 words',
     'Delete, or use "also"'),
    ('en-marketing-has', WARN, 'pattern', 'EN-AI-062', 'boasts/features/offers + a/an/number (not in ads)',
     'Use "has"'),
    ('en-sycophancy', ERROR, 'pattern', 'EN-AI-063', 'great/excellent/insightful question or point', 'Remove'),
    ('en-stat-claim', WARN, 'pattern', 'EN-FACT-001',
     'Percentage, multiplier, "N times", millions or billions; one warning per line (off with --facts; not '
     'flagged when the line cites a URL or [source: …]; a discount such as "20% off" or "save 20%" is not a '
     'claim)', 'Trace it to the brief or a source; else [source needed: metric]'),
    ('en-superlative', WARN, 'pattern', 'EN-FACT-002',
     'Superlative claim: the best, the leading, the first/only … to, world\'s first, #1, guaranteed, 100% safe',
     'Qualify with source and scope, or rewrite'),
    ('en-establishment-claim', ERROR, 'pattern', 'EN-FACT-003',
     'Establishment claim: clinically/scientifically proven, studies/tests show, doctors recommend (not '
     'flagged when the line cites a URL, DOI or [source: …])', 'Cite the actual study, or remove'),
    ('en-testimonial', WARN, 'pattern', 'EN-FACT-004',
     'Quoted text with an attribution on the same line (— Name, ~ Name, "…," says Name); an error with '
     '--facts when the quote is not in the facts',
     'Use only verbatim, consented quotes; else [testimonial needed]'),
    ('en-fact-not-in-brief', ERROR, 'facts', 'EN-FACT-005',
     'Number, date, money, percentage, proper noun, URL or quote that is not in the --facts text',
     'Remove it, or bracket it: [source needed: …]'),
    ('en-citation-check', WARN, 'pattern', 'EN-FACT-006',
     'DOI or ISBN in the text (warning: resolve it); an ISBN with a bad checksum is an error',
     'Resolve every DOI; fix the ISBN'),
    ('en-long-sentence', WARN, 'dynamic', 'EN-PL-001',
     'Sentence longer than the cap; cap: --max-words > formats[format] > format default (stricter only) > '
     'profile > dial (default 25); list items, headings and table cells are sentences', 'Split it'),
    ('en-long-paragraph', WARN, 'dynamic', 'EN-PL-002', 'Paragraph over 150 words (never over 250)',
     'Split it by topic'),
    ('en-passive', WARN, 'dynamic', 'EN-PL-003',
     'More than 20% of sentences are passive (5 sentences or more; up to 5 examples)', 'Name the actor'),
    ('en-hidden-verb', WARN, 'pattern', 'EN-PL-004', 'Hidden verb: conduct an analysis, make a decision, '
     'provide assistance …', 'Use the verb: analyze, decide, help'),
    ('en-complex-word', WARN, 'pattern', 'EN-PL-005', 'Complex word or phrase: utilize, facilitate, commence, '
     'prior to, in order to, in the event that …', 'Use the simple word'),
    ('en-shall', WARN, 'pattern', 'EN-PL-006', 'shall', 'Use must or must not'),
    ('en-double-negative', WARN, 'pattern', 'EN-PL-007', 'Double negative: not un-/in-/non-…, no fewer than, '
     'not … unless', 'Use at least, or only if'),
    ('en-slash', WARN, 'pattern', 'EN-PL-008', 'and/or, word/word (not in ui)', 'Write "a or b, or both", or pick one'),
    ('en-please-note', WARN, 'pattern', 'EN-PL-009', 'please note, kindly note, be advised, it should be noted',
     'Delete the frame'),
    ('en-minimizer', WARN, 'pattern', 'EN-PL-010',
     'simply, just, easily, obviously, quickly, it\'s easy (formats ui, error, email, landing, bot)',
     'Delete it, or give the real steps or time'),
    ('en-bangs', ERROR, 'dynamic', 'EN-PL-011',
     '"!!" is an error; more "!" than exclaim_max is a warning; any "!" in error or hard format is a warning',
     'Remove'),
    ('en-there-is', WARN, 'pattern', 'EN-PL-012', 'Sentence opens with There is/are/was/were',
     'Start with the real subject'),
    ('en-undefined-abbr', WARN, 'dynamic', 'EN-PL-013',
     'First use in body text of a 2–6 capital abbreviation without an expansion (80 words or more; common '
     'ones and SMS keywords allowed; headings and link text skipped)',
     'Expand it at first use'),
    ('en-metaphor-buzz', WARN, 'pattern', 'EN-PL-014', 'going forward, drive growth, one-stop shop, ring-fence, '
     'deliver improvements, tackle …', 'from now on; create; make'),
    ('en-oxford-comma', WARN, 'profile', 'EN-ST-001',
     'oxford_comma true: serial comma missing; false: serial comma present; null: both styles in one text. '
     'Counts only comma series whose items read as list items: not appositives (", with …", ", in …"), an '
     '"and" inside an item, names such as statutes, quotations or the text of a link to another site',
     'Add or remove it consistently'),
    ('en-dash-spacing', WARN, 'pattern', 'EN-ST-002',
     'Spaced em dash, "--" or " - " used as a dash (closed styles, the default); an unspaced em dash under ap',
     'word—word (ap: word — word); --fix applies it'),
    ('en-numeral-style', WARN, 'profile', 'EN-ST-003',
     'Numerals 1–9 in body text (house_style ap, microsoft) or under 100 (chicago)', 'Spell it out'),
    ('en-numeral-start', WARN, 'pattern', 'EN-ST-004', 'Sentence starts with a numeral (years allowed; not in '
     'list items, table cells, headings or quotations, nor in the otp, headline, ui and sms formats)',
     'Spell it out, or rephrase'),
    ('en-numeric-date', WARN, 'pattern', 'EN-ST-005', 'Numeric date such as 1/2/2026',
     'Write "June 12, 2026" (US) or "12 June 2026" (UK)'),
    ('en-range-hyphen', WARN, 'profile', 'EN-ST-006', 'Range with a hyphen or en dash (house_style govuk, microsoft)',
     'Write "10am to 11am"'),
    ('en-ampersand', WARN, 'pattern', 'EN-ST-007', 'Standalone " & " in prose (not ui, headline, table rows)',
     'Write "and"'),
    ('en-heading-punct', WARN, 'pattern', 'EN-ST-008', 'Heading ends with "." or ":" (--md)',
     'Remove it (--fix)'),
    ('en-double-space', WARN, 'pattern', 'EN-ST-009', 'Two spaces after . ? ! :', 'One space (--fix)'),
    ('en-link-text', WARN, 'pattern', 'EN-ST-010', 'click here / here / read more / learn more as link text '
     '(--md or HTML)', 'Describe the destination'),
    ('en-all-caps', WARN, 'pattern', 'EN-ST-011', '5 or more consecutive ALL-CAPS words', 'Use sentence case'),
    ('en-latin-abbr', WARN, 'profile', 'EN-ST-012', 'e.g., i.e., etc. (house_style govuk)',
     'for example, such as, that is'),
    ('en-contraction', WARN, 'profile', 'EN-ST-013',
     'contractions "avoid": any contraction; "positive-only" or house_style govuk: negative contractions',
     'Expand it'),
    ('en-no-contraction', WARN, 'profile', 'profile',
     'contractions "use" in caption, post, email, ui, bot or reply: "do not", "we will" …', 'Contract it'),
    ('en-spelling-mix', ERROR, 'dynamic', 'EN-ST-020',
     'US and UK spellings in the same text (-ize alone is not UK or US evidence; ambiguous words are skipped)',
     'Pick one variant'),
    ('en-spelling-variant', WARN, 'profile', 'profile',
     'Word off the profile spelling (us, uk, uk-ize; set or derived from the variant)',
     'Normalize it (--fix)'),
    ('en-readability-grade', WARN, 'dynamic', 'EN-READ-002',
     'Flesch–Kincaid grade above the target (reading_grade_max, or from the jargon dial: 1→6 … 5→14); '
     '100 words or more; formats landing, about, blog, email, product, press, deck, script, hard, reply',
     'Shorter sentences and plainer words; never game the score'),
    ('en-readability-fre', WARN, 'dynamic', 'EN-READ-001', 'Flesch Reading Ease below 30 (same gating)',
     'Shorter sentences and plainer words'),
    ('en-brand-spelling', ERROR, 'profile', 'profile', 'Brand name in the wrong case or form (brand.latin, '
     'Latin keys of brand.misspellings)', 'Use the exact brand form'),
    ('en-profile-banned', ERROR, 'profile', 'profile', 'Latin-script word from the profile banned list', 'Remove'),
    ('en-profile-avoid', WARN, 'profile', 'profile', 'Latin-script word from the profile avoid list (with the '
     'prefer hint)', 'Use the preferred form'),
    ('en-jargon', WARN, 'profile', 'profile',
     'Corporate jargon (synergy, bandwidth, circle back, deep dive …) when dials.jargon is 1 or 2', 'Use the plain word'),
    ('en-emoji', WARN, 'dynamic', 'dynamic', 'More emoji than emoji_max (a flag or ZWJ sequence counts once)',
     'Remove'),
    ('en-same-opening', WARN, 'dynamic', 'dynamic', '3 or more consecutive sentences start with the same word '
     '(one warning per run; a list item that is only a link is skipped)', 'Vary them'),
    ('en-flat-rhythm', WARN, 'dynamic', 'dynamic', '6 or more sentences whose lengths vary by less than 3 words '
     '(standard deviation)', 'Mix long and short'),
    ('en-rhetorical-open', WARN, 'dynamic', 'dynamic', 'Text opens with "Ever wondered…?", "Did you know…?", '
     '"Imagine…"', 'Open with something concrete'),
    ('en-cliche-open', WARN, 'lexicon', 'lexicon', "In today's fast-paced world, In a world where, Welcome to "
     "the world of, Look no further, Whether you're X or Y", 'Start with the fact'),
    ('en-journey', WARN, 'lexicon', 'lexicon', 'journey (not customer/user journey), unlock your potential, '
     'elevate your experience', 'Use a concrete verb'),
    ('en-moral-close', WARN, 'lexicon', 'lexicon', '"Because at the end of the day…", "After all, … is what '
     'matters"', 'End on the action'),
    ('en-clickbait', WARN, 'lexicon', 'lexicon', "You won't believe, this one trick, shocking", 'Say the finding'),
    ('en-caption-header', WARN, 'format', 'format', 'Heading or bold title line in a caption (--format caption)',
     'Start with the moment'),
    ('en-channel-length', ERROR, 'channel', 'channel',
     'Longer than the channel limit in its unit (char, byte, utf16, grapheme, weighted, segment, word); a '
     'warning when the limit is unverified', 'Cut'),
    ('en-channel-visible', WARN, 'channel', 'channel', 'Longer than the visible part before "more" (visible_chars)',
     'Front-load the point'),
    ('en-channel-items', ERROR, 'channel', 'channel',
     'More items than max_items, or an item longer than item_max_chars (hashtags, tags); a warning when '
     'unverified', 'Reduce'),
    ('en-profile-invalid', WARN, 'profile', 'profile', 'Invalid profile value (v2 keys, §E.1)', 'Fix the profile'),
]
_RULE_BY_ID = dict((r[0], r) for r in RULES)


#: Tunable parameters for the Hub (spec 7.3): the built-in default and the range a signed baseline may use.
HUB_PARAMS = {'en-long-sentence.max_words': {'default': EN_DEFAULT_MAX_WORDS, 'min': 18, 'max': 35, 'bucket': 4},
              'en-readability-grade.max': {'default': 8, 'min': 6, 'max': 12, 'bucket': 1}}


def rule_list():
    """Every rule once: id, severity, kind, description, ref (catalog id) and fix; a rule with
    tunable parameters also carries params (spec 7.3)."""
    rows = [{'id': r[0], 'severity': r[1], 'kind': r[2], 'description': r[4], 'ref': r[3], 'fix': r[5]}
            for r in RULES]
    by_id = dict((r['id'], r) for r in rows)
    for pid, spec in HUB_PARAMS.items():
        rule, _, name = pid.partition('.')
        if rule in by_id:
            by_id[rule].setdefault('params', {})[name] = dict(spec)
    return rows


def _fix_hint(code):
    r = _RULE_BY_ID.get(code)
    return r[5] if r else ''


# ---------------------------------------------------------------- profile
def _is_latin(w):
    return isinstance(w, str) and bool(_LATIN.search(w)) and not _FA_LETTER.search(w)


def _warn(warns, msg):
    warns.append(('en-profile-invalid', msg))


def _norm_dials_en(dials, where, warns):
    out = {}
    if dials is None:
        return out
    if not isinstance(dials, dict):
        _warn(warns, 'dials in %s must be an object' % where)
        return out
    for k, v in dials.items():
        k = LF.DIAL_ALIASES.get(k, k)
        if k not in LF.DIAL_RANGES:
            _warn(warns, 'unknown dial in %s: %s' % (where, k))
            continue
        lo, hi = LF.DIAL_RANGES[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            _warn(warns, 'dial %s in %s is not a number: %r' % (k, where, v))
            continue
        iv = int(round(v))
        if iv < lo or iv > hi:
            _warn(warns, 'dial %s in %s is outside %d to %d: %s' % (k, where, lo, hi, v))
            iv = min(hi, max(lo, iv))
        out[k] = iv
    return out


def _norm_limits_en(src, dst, where, warns):
    for k in ('max_words', 'emoji_max', 'exclaim_max'):
        if k not in src:
            continue
        v = src[k]
        if isinstance(v, bool) or not isinstance(v, int) or v < 0 or (k == 'max_words' and v == 0):
            _warn(warns, '%s in %s must be a positive whole number: %r' % (k, where, v))
            dst.pop(k, None)
        else:
            dst[k] = v


def _norm_words_en(src, dst, where, warns):
    for k in ('banned', 'avoid', 'allow'):
        if k not in src:
            continue
        v = src[k]
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            _warn(warns, '%s in %s must be a list of words' % (k, where))
            dst[k] = []
        else:
            dst[k] = [x for x in v if x.strip()]


def normalize_profile(profile):
    """Profile for English: by_lang.en merged over the top level, English warnings in '_warnings'.
    Accepts raw profiles (preferred) and lint_fa-normalized ones."""
    if not profile:
        return {'_en_normalized': True, '_warnings': [], 'dials': {}, 'formats': {}, 'brand': {},
                'prefer': {}, 'romanization': {}}
    if not isinstance(profile, dict):
        raise UserError('profile must be a JSON object')
    if profile.get('_en_normalized'):
        return profile
    raw = {k: v for k, v in profile.items() if k not in ('_path', '_normalized', '_en_normalized', '_warnings')}
    errors = LF.VP.validate_profile(raw)
    sv = raw.get('schema_version', 1)
    if type(sv) is not int or sv not in (1, 2, 3) or (sv == 3 and errors):
        raise UserError(str(LF.VP.ProfileError(errors)))
    warns = [('en-profile-invalid', e['path'] + ': ' + e['message']) for e in errors]
    bl = profile.get('by_lang')
    if bl is not None:
        if not isinstance(bl, dict):
            _warn(warns, 'by_lang must be an object with the keys fa and/or en')
        else:
            extra = sorted(k for k in bl if k not in ('fa', 'en'))
            if extra:
                _warn(warns, 'by_lang has unknown keys: %s (allowed: fa, en)' % ', '.join(extra))
            for k in ('fa', 'en'):
                if k in bl and not isinstance(bl[k], dict):
                    _warn(warns, 'by_lang.%s must be an object' % k)
    src = LF.merge_by_lang(profile, 'en')
    p = dict(src)
    sv = p.get('schema_version', 1)
    if sv not in (1, 2, 3):
        _warn(warns, 'schema_version "%s" is unknown; lint_en reads versions 1 through 3' % (sv,))
    lang = p.get('language')
    if lang is not None and lang not in LANGUAGES:
        _warn(warns, 'language "%s" is invalid (allowed: fa, en, bilingual)' % (lang,))
        lang = None
    p['language'] = lang
    var = p.get('variant')
    if var is not None and (not isinstance(var, str) or not _VARIANT_RX.match(var)):
        _warn(warns, 'variant "%s" is invalid (allowed: fa-IR, fa-AF, tg, %s)' % (var, ', '.join(VARIANTS)))
        var = None
    p['variant'] = var
    vs = p.get('variants')
    if vs is None:
        vs = []
    if not isinstance(vs, list) or not all(isinstance(x, str) for x in vs):
        _warn(warns, 'variants must be a list of BCP 47 tags')
        vs = []
    else:
        bad = [x for x in vs if not _VARIANT_RX.match(x)]
        if bad:
            _warn(warns, 'variants has invalid tags: %s' % ', '.join(bad[:4]))
            vs = [x for x in vs if _VARIANT_RX.match(x)]
        if vs and var and var not in vs:
            _warn(warns, 'variants must contain the variant "%s"' % var)
    p['variants'] = vs
    for key, allowed in (('spelling', SPELLINGS), ('contractions', CONTRACTIONS), ('house_style', HOUSE_STYLES)):
        v = p.get(key)
        if v is not None and v not in allowed:
            _warn(warns, '%s "%s" is invalid (allowed: %s, or null)' % (key, v, ', '.join(allowed)))
            v = None
        p[key] = v
    oc = p.get('oxford_comma')
    if oc is not None and not isinstance(oc, bool):
        _warn(warns, 'oxford_comma must be true, false or null: %r' % (oc,))
        oc = None
    p['oxford_comma'] = oc
    rg = p.get('reading_grade_max')
    if rg is not None and (isinstance(rg, bool) or not isinstance(rg, (int, float)) or rg < 4 or rg > 16):
        _warn(warns, 'reading_grade_max must be a number from 4 to 16, or null: %r' % (rg,))
        rg = None
    p['reading_grade_max'] = rg
    p['dials'] = _norm_dials_en(p.get('dials'), 'the profile', warns)
    for k in ('max_words', 'emoji_max', 'exclaim_max'):
        p.pop(k, None)
    _norm_limits_en(src, p, 'the profile', warns)
    _norm_words_en(src, p, 'the profile', warns)
    if not isinstance(p.get('prefer', {}) or {}, dict):
        _warn(warns, 'prefer must be an object of "word": "replacement"')
        p['prefer'] = {}
    p['prefer'] = dict(p.get('prefer') or {})
    brand = p.get('brand') or {}
    if not isinstance(brand, dict):
        _warn(warns, 'brand must be an object')
        brand = {}
    brand = dict(brand)
    if not isinstance(brand.get('misspellings', {}) or {}, dict):
        _warn(warns, 'brand.misspellings must be an object of "wrong": "right"')
        brand['misspellings'] = {}
    if brand.get('latin') is not None and not isinstance(brand.get('latin'), str):
        _warn(warns, 'brand.latin must be a string')
        brand['latin'] = ''
    p['brand'] = brand
    rom = p.get('romanization')
    if rom is None:
        rom = {}
    if not isinstance(rom, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in rom.items()):
        _warn(warns, 'romanization must be an object of "Persian word": "Latin spelling"')
        rom = {}
    p['romanization'] = dict(rom)
    fmts = p.get('formats') or {}
    if not isinstance(fmts, dict):
        _warn(warns, 'formats must be an object of "format id": settings')
        fmts = {}
    nf = {}
    for fid, fv in fmts.items():
        where = 'formats.%s' % fid
        if fid not in EN_FORMAT_DEFAULTS:
            _warn(warns, 'unknown format "%s" in formats; see --rules for the ids' % fid)
        if not isinstance(fv, dict):
            _warn(warns, '%s must be an object' % where)
            continue
        q = {}
        if 'dials' in fv:
            q['dials'] = _norm_dials_en(fv.get('dials'), where, warns)
        _norm_limits_en(fv, q, where, warns)
        _norm_words_en(fv, q, where, warns)
        if isinstance(fv.get('note'), str):
            q['note'] = fv['note']
        nf[fid] = q
    p['formats'] = nf
    seen, uniq = set(), []
    for w in warns:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    p['_warnings'] = uniq
    p['_en_normalized'] = True
    return p


def validate_profile(profile):
    """[(rule, message)] for a raw profile; empty means valid for English."""
    return list(normalize_profile(profile).get('_warnings', []))


def _en_variant(p, cli=None):
    if cli:
        return cli
    v = p.get('variant')
    if isinstance(v, str) and v.startswith('en-'):
        return v
    for x in p.get('variants') or []:
        if isinstance(x, str) and x.startswith('en-'):
            return x
    if p.get('language') == 'en':
        return 'en-US'
    return None


def resolve_settings(profile=None, fmt=None, max_words=None, emoji_max=None, exclaim_max=None,
                     variant=None, house_style=None):
    """Effective English settings (see the module docs and migration/v3/lint-api.md)."""
    p = normalize_profile(profile or {})
    warns = list(p.get('_warnings') or [])
    if variant and variant not in VARIANTS:
        raise UserError('--variant "%s" is not an English variant (%s)' % (variant, ', '.join(VARIANTS)))
    if house_style and house_style not in HOUSE_STYLES:
        raise UserError('--house-style "%s" is unknown (%s)' % (house_style, ', '.join(HOUSE_STYLES)))
    dials = dict(p.get('dials') or {})
    # a Hub overlay default only replaces the built-in default (spec 5.9)
    mw = EN_DIAL_WORDS.get(dials.get('sentence_length')) or _hub_param('en-long-sentence.max_words',
                                                                       EN_DEFAULT_MAX_WORDS)
    em, ex = LF.DIAL_MARKS.get(dials.get('loud_marks'), LF.DIAL_MARKS[LF.DEFAULT_LOUD_MARKS])
    src = {'max_words': 'dial', 'emoji_max': 'dial', 'exclaim_max': 'dial'}
    if 'max_words' in p:
        mw, src['max_words'] = p['max_words'], 'profile'
    if 'emoji_max' in p:
        em, src['emoji_max'] = p['emoji_max'], 'profile'
    if 'exclaim_max' in p:
        ex, src['exclaim_max'] = p['exclaim_max'], 'profile'
    banned = [w for w in (p.get('banned') or []) if _is_latin(w)]
    avoid = [w for w in (p.get('avoid') or []) if _is_latin(w)]
    allow = [w for w in (p.get('allow') or []) if _is_latin(w)]
    note = ''
    if fmt:
        fd = EN_FORMAT_DEFAULTS.get(fmt, {})
        if 'max_words' in fd and fd['max_words'] < mw:
            mw, src['max_words'] = fd['max_words'], 'format'
        if 'emoji_max' in fd and fd['emoji_max'] < em:
            em, src['emoji_max'] = fd['emoji_max'], 'format'
        if 'exclaim_max' in fd and fd['exclaim_max'] < ex:
            ex, src['exclaim_max'] = fd['exclaim_max'], 'format'
        pf = (p.get('formats') or {}).get(fmt) or {}
        fdials = pf.get('dials') or {}
        if fdials:
            dials.update(fdials)
            if 'sentence_length' in fdials:
                mw, src['max_words'] = EN_DIAL_WORDS[fdials['sentence_length']], 'profile.formats'
            if 'loud_marks' in fdials:
                em, ex = LF.DIAL_MARKS[fdials['loud_marks']]
                src['emoji_max'] = src['exclaim_max'] = 'profile.formats'
        for k in ('max_words', 'emoji_max', 'exclaim_max'):
            if k in pf:
                src[k] = 'profile.formats'
                if k == 'max_words':
                    mw = pf[k]
                elif k == 'emoji_max':
                    em = pf[k]
                else:
                    ex = pf[k]
        banned += [w for w in (pf.get('banned') or []) if _is_latin(w)]
        avoid += [w for w in (pf.get('avoid') or []) if _is_latin(w)]
        allow += [w for w in (pf.get('allow') or []) if _is_latin(w)]
        note = pf.get('note') or fd.get('note', '')
    if max_words:
        mw, src['max_words'] = max_words, 'cli'
    if emoji_max is not None:
        em, src['emoji_max'] = emoji_max, 'cli'
    if exclaim_max is not None:
        ex, src['exclaim_max'] = exclaim_max, 'cli'
    var = _en_variant(p, variant)
    spelling = p.get('spelling') or SPELL_BY_VARIANT.get(var)
    hs = house_style or p.get('house_style')
    rg = p.get('reading_grade_max')
    if rg is None:
        rg = EN_GRADE.get(dials['jargon'], 8) if dials.get('jargon') else _hub_param(
            'en-readability-grade.max', EN_GRADE.get(LF.DIAL_DEFAULTS['jargon'], 8))
    brand = p.get('brand') or {}
    misspell = dict((k, v) for k, v in (brand.get('misspellings') or {}).items()
                    if _is_latin(k) and isinstance(v, str))
    prefer = dict((k, v) for k, v in (p.get('prefer') or {}).items() if _is_latin(k))
    return {'max_words': mw, 'emoji_max': em, 'exclaim_max': ex, 'format': fmt or '', 'note': note,
            'dials': dials, 'variant': var, 'spelling': spelling, 'oxford_comma': p.get('oxford_comma'),
            'contractions': p.get('contractions'), 'house_style': hs, 'reading_grade_max': rg,
            'banned': banned, 'avoid': avoid, 'allow': allow, 'prefer': prefer,
            'brand_latin': (brand.get('latin') or '').strip(), 'misspellings': misspell,
            'romanization': dict(p.get('romanization') or {}), 'profile': p.get('name', '') or '',
            'jargon_on': 0 < (dials.get('jargon') or 0) <= 2 and bool((p.get('dials') or {}).get('jargon')),
            'sources': src, 'warnings': warns}


# ---------------------------------------------------------------- helpers
class _Lines(object):
    """Offset → (line, col) for a text."""

    def __init__(self, text):
        self.starts = [0] + [m.end() for m in re.finditer('\n', text)]

    def pos(self, off):
        i = bisect.bisect_right(self.starts, off) - 1
        return i + 1, off - self.starts[i] + 1


def _merge_spans(spans):
    spans = sorted(spans)
    out = []
    for a, b in spans:
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _in_spans(pos, spans, starts=None):
    if not spans:
        return False
    starts = starts if starts is not None else [a for a, _ in spans]
    i = bisect.bisect_right(starts, pos) - 1
    return i >= 0 and spans[i][0] <= pos < spans[i][1]


def _hard_spans(text, kind):
    """Code, comments, raw HTML, front matter and lint-ignore blocks (URLs and templates stay visible)."""
    spans = []
    if kind == 'md':
        m = LF._FRONT.match(text)
        if m:
            spans.append((0, m.end()))
    fences = LF._fence_spans(text)
    spans += fences
    spans += ignore_spans(text, fences)
    spans += [(m.start(), m.end()) for m in LF._HTML_RAW.finditer(text)]
    spans += [(m.start(), m.end()) for m in LF._HTML_COMMENT.finditer(text)]
    spans += [(m.start(), m.end()) for m in LF._INLINE_CODE.finditer(text)]
    return _merge_spans(spans)


def _whalory_bracket(s, allow=()):
    t = s.strip('[]').strip().lower()
    if s in allow:
        return True
    return bool(re.match(r'(?:confirm|source needed|source|testimonial needed|verify|check|todo: confirm|needs source'
                         r'|تأیید|منبع)', t))


_VOWEL = 'aeiouy'


@functools.lru_cache(maxsize=65536)
def count_syllables(word):
    """Heuristic English syllable count (spec §D.3). A token with a digit counts 1."""
    if any(c.isdigit() for c in word):
        return 1
    raw = unicodedata.normalize('NFKD', word.lower().replace('’', "'"))
    if '-' in raw:
        parts = [p for p in raw.split('-') if re.search('[a-z]', p)]
        return sum(count_syllables(p) for p in parts) if parts else 1
    neg_t = raw.endswith("n't") and len(raw) > 3 and raw[-4] not in _VOWEL     # isn't, didn't, couldn't
    w = re.sub(r'[^a-z]', '', raw)
    if not w:
        return 1
    if w in _SYL_EXC:
        return _SYL_EXC[w]
    v = re.sub(r'y(?=[aeiou])', 'Y', w)        # y before a vowel is a consonant: saying, player, year
    n = len(re.findall(r'[aeiouy]+', v))
    # final silent e, but not consonant + le/re (table, people, centre)
    if re.search(r'[^aeiouy]e$', v) and not re.search(r'[^aeiouy][lr]e$', v):
        n -= 1
    # -ed and -es that add no syllable (the e joined a vowel group, or t/d, s/x/z/ch/sh/c/g, consonant+l)
    if len(v) > 3 and v.endswith('ed') and v[-3] not in _VOWEL + 'td':
        n -= 1
    if len(v) > 3 and v.endswith('es') and v[-3] not in _VOWEL + 'sxzcg' and not v.endswith(('ches', 'shes')) \
            and not re.search(r'[^aeiouy]les$', v):
        n -= 1
    # silent e inside a suffixed word: lately, management, careful, hopeless, awareness
    if re.search(r'[^aeiouy]e(?:ly|ment|ments|ful|less|ness)$', v):
        n -= 1
    # vowel pairs that are two syllables: radio, actual, premium, video, being, media, easier
    n += len(re.findall(r'(?<=[drvbpmz])io|(?<![qg])ua|iu|(?<!p)eo(?!u)|[eo]ing|uing|(?<![ctsgl])ia', v))
    if len(v) > 4 and re.search(r'i(?:er|ers|est)$', v):
        n += 1
    if v.endswith('ism'):
        n += 1
    if neg_t:
        n += 1
    return max(1, n)


# Exceptions to the heuristic (spec §D.3 names every, business, people, area, idea, real, create)
_SYL_EXC = {
    'every': 2, 'everything': 3, 'everyone': 3, 'everybody': 4, 'everywhere': 3, 'business': 2,
    'businesses': 3, 'people': 2, 'area': 3, 'areas': 3, 'idea': 3, 'ideas': 3, 'real': 1, 'create': 2,
    'creates': 2, 'created': 3, 'creating': 3, 'creative': 3, 'creation': 3, 'science': 2, 'client': 2,
    'clients': 2, 'quiet': 2, 'diet': 2, 'variety': 4, 'society': 4, 'anxiety': 4, 'audience': 3,
    'audiences': 4, 'experience': 4, 'experiences': 5, 'experienced': 4, 'ingredient': 4, 'ingredients': 4,
    'convenient': 4, 'recipient': 4, 'poem': 2, 'poems': 2, 'poet': 2, 'react': 2, 'reality': 4, 'ideal': 3,
    'element': 3, 'elements': 3, 'recipe': 3, 'recipes': 3, 'cafe': 2, 'cafes': 2, 'naive': 2, 'hour': 1,
    'hours': 1, 'our': 1, 'fire': 1, 'wednesday': 2, 'maybe': 2, 'someone': 2, 'somewhere': 2,
    'sometimes': 2, 'something': 2, 'anyone': 3, 'lifetime': 2, 'online': 2, 'evening': 2, 'arent': 1,
    'werent': 1, 'frontier': 2, 'whalory': 3, 'forever': 3, 'however': 3, 'whatever': 3, 'whenever': 3,
    'wherever': 3, 'lion': 2, 'realize': 3, 'realizes': 4, 'realized': 3, 'realise': 3, 'realised': 3,
    'museum': 3, 'deliver': 3, 'orange': 2, 'whalya': 2,  # whalya: the maker, the Whalya studio
}


def readability_from(words_syl, sentences):
    """(FRE, FKGL) from word/syllable totals; None when there is nothing to measure."""
    words = words_syl[0]
    syl = words_syl[1]
    if not words or not sentences:
        return None, None
    wps = words / float(sentences)
    spw = syl / float(words)
    fre = 206.835 - 1.015 * wps - 84.6 * spw
    fkgl = 0.39 * wps + 11.8 * spw - 15.59
    return round(fre, 1), round(fkgl, 1)


_ABBR_NO_SPLIT = {'mr', 'mrs', 'ms', 'dr', 'st', 'no', 'vs', 'etc', 'e.g', 'i.e', 'u.s', 'u.k', 'a.m', 'p.m',
                  'inc', 'ltd', 'co'}
_EN_END = re.compile("(?<![.!?])[.!?]+[\"'’”)\\]*_]*(?=[ \t]|$)|%s+" % BLOCK)
_LAST_TOKEN = re.compile(r'([A-Za-z][A-Za-z.]*)$')


def _sentence_spans(seg):
    """(start, end) of each sentence in one line segment (spec §D.3)."""
    spans, pos = [], 0
    for m in _EN_END.finditer(seg):
        if m.group(0).startswith('.') and not m.group(0).startswith('..'):
            tok = _LAST_TOKEN.search(seg, max(0, m.start() - 24), m.start())
            if tok:
                t = tok.group(1).lower().rstrip('.')
                if t in _ABBR_NO_SPLIT or (len(t) == 1 and tok.group(1).isupper()):
                    continue
        spans.append((pos, m.end()))
        pos = m.end()
    spans.append((pos, len(seg)))
    return [(a, b) for a, b in spans if seg[a:b].strip(' \t' + MASK + BLOCK)]


def _words(s):
    return _WORD.findall(s)


def _lemma(word):
    w = word.lower()
    for l in _AI_LEMMAS:
        if w.startswith(l):
            return l
    w = re.sub(r"(?:ing|ed|es|s|ly|ment)$", '', w)
    return w[:7]


def _isbn_ok(digits):
    d = digits.replace('-', '').replace(' ', '').upper()
    if len(d) == 10 and re.match(r'^\d{9}[\dX]$', d):
        s = sum((10 - i) * (10 if c == 'X' else int(c)) for i, c in enumerate(d))
        return s % 11 == 0
    if len(d) == 13 and d.isdigit():
        s = sum((1 if i % 2 == 0 else 3) * int(c) for i, c in enumerate(d))
        return s % 10 == 0
    return False


_FA_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹'
                           '٠١٢٣٤٥٦٧٨٩',
                           '01234567890123456789')


def _norm_num(s):
    s = s.translate(_FA_DIGITS).replace('٬', '').replace('٫', '.').replace(',', '')
    s = s.rstrip('.')
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s.lstrip('0') or '0'


def _norm_quote(s):
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    return re.sub(r'\s+', ' ', s).strip(' "\'.,;:!?').lower()


class _Facts(object):
    """The --facts text, prepared for lookups."""

    def __init__(self, text):
        if isinstance(text, (list, tuple)):
            text = '\n'.join(str(x) for x in text)
        self.raw = text or ''
        low = self.raw.lower()
        self.low = low
        self.words = set(re.findall(r"[a-z0-9][a-z0-9'’\-]*", low.translate(_FA_DIGITS)))
        self.numbers = set(_norm_num(x) for x in re.findall(r'[0-9۰-۹٠-٩][0-9۰-۹'
                                                              r'٠-٩,٬]*(?:[.٫][0-9۰-۹'
                                                              r'٠-٩]+)?', self.raw))
        self.quote_text = _norm_quote(self.raw)
        self.urls = set(u.lower().rstrip('/') for u in _URL_RX.findall(self.raw))
        self.runs = set(re.findall(r'[a-z0-9]+', low))     # every maximal run of letters and digits
        self._seen = {}

    def has_word(self, w):
        w = w.lower().replace('’', "'")
        if w in self.words:
            return True
        if re.match(r'[a-z0-9]+$', w):
            return w in self.runs          # same answer as the search below, without scanning the text
        if w not in self._seen:
            self._seen[w] = bool(re.search(r'(?<![a-z0-9])%s(?![a-z0-9])' % re.escape(w), self.low))
        return self._seen[w]

    def has_number(self, n):
        return _norm_num(n) in self.numbers

    def has_quote(self, q):
        return _norm_quote(q) in self.quote_text

    def has_url(self, u):
        u = u.lower().rstrip('/')
        return u in self.urls or u in self.low


# ---------------------------------------------------------------- spelling analysis
_ALPHA_RUN = re.compile(r"(?<![A-Za-z'’\-])[A-Za-z]+(?![A-Za-z'’\-])")


def _spelling_hits(masked):
    """[(start, end, word, family, side)] for every US/UK family form in the text."""
    out = []
    for m in _ALPHA_RUN.finditer(masked):
        w = m.group(0)
        f = SPELLING_FORMS.get(w.lower())
        if f:
            out.append((m.start(), m.end(), w, f[0], f[1]))
    return out


_LINE_LEAD = re.compile(r'[ \t]*(?:>[ \t]?)*(?:#{1,6}|[-*+•]|\d{1,3}[.)])?[ \t]*')


def _sentence_initial(line, col0):
    i = col0
    while i > 0 and line[i - 1].isspace():
        i -= 1
    if i == 0 or _LINE_LEAD.match(line, 0, i).end() >= i:
        return True
    # after "(" or "[" (and link brackets, masked) a capital is most often a name: not a sentence start
    return line[i - 1] in '.!?:"“‘\'' + BLOCK


def _spell_target(word, mode):
    """The form this word should take under the spelling mode, or None when it is fine."""
    fam, side, other = SPELLING_FORMS[word.lower()]
    if mode == 'us':
        target_side = 'us'
    elif mode == 'uk':
        target_side = 'uk'
    elif mode == 'uk-ize':
        if fam == 'yze-yse':
            return None
        target_side = 'us' if fam == 'ize-ise' else 'uk'
    else:
        return None
    if side == target_side:
        return None
    if other not in SPELLING_FORMS and target_side == 'uk':
        return other                              # analyzes → analyses (one-way)
    return other


def _match_case(src, repl):
    if src.isupper():
        return repl.upper()
    if src[:1].isupper():
        return repl[:1].upper() + repl[1:]
    return repl


def _mix_evidence(hits, lines_of=None):
    us = [h for h in hits if h[4] == 'us' and h[3] not in ('ize-ise', 'yze-yse')]
    uk = [h for h in hits if h[4] == 'uk']
    ize = [h for h in hits if h[3] == 'ize-ise' and h[4] == 'us']
    ise = [h for h in hits if h[3] == 'ize-ise' and h[4] == 'uk']
    return us, uk, ize, ise


def spelling_counts(text):
    """US/UK spelling evidence in a text (code and URLs masked): us, uk, ize, ise, guess, examples."""
    masked = LF.mask_prose(clean_text(text or ''), 'md')
    hits = [h for h in _spelling_hits(masked)]
    lines = masked.split('\n')
    starts = _Lines(masked)
    keep = []
    for h in hits:
        ln, col = starts.pos(h[0])
        if h[2][:1].isupper() and not _sentence_initial(lines[ln - 1], col - 1):
            continue
        keep.append(h)
    us, uk, ize, ise = _mix_evidence(keep)
    all_us = [h for h in keep if h[4] == 'us']
    if uk and not us:
        guess = 'uk-ize' if ize and not ise else 'uk'
    elif all_us and not uk:
        guess = 'us'
    elif ize and not ise and not uk and not us:
        guess = 'us'
    else:
        guess = None
    return {'us': len(all_us), 'uk': len(uk), 'ize': len(ize), 'ise': len(ise), 'guess': guess,
            'us_words': sorted(set(h[2].lower() for h in all_us))[:10],
            'uk_words': sorted(set(h[2].lower() for h in uk))[:10]}


def oxford_counts(text):
    """Serial ("A, B, and C") and non-serial ("A, B and C") list counts."""
    raw = clean_text(text or '')
    masked = LF.mask_prose(raw, 'md')
    serial = nonserial = 0
    for ln, rl in zip(masked.split('\n'), raw.split('\n')):
        for a, b in _sentence_spans(ln):
            for _pos, ser, _n in list_series(ln[a:b], rl[a:b]):
                if ser:
                    serial += 1
                else:
                    nonserial += 1
    return {'serial': serial, 'nonserial': nonserial}


def contraction_counts(text):
    """Contractions, negative contractions and expanded forms."""
    masked = LF.mask_prose(clean_text(text or ''), 'md')
    return {'contractions': len(_CONTRACTION.findall(masked)), 'negative': len(_NEG_CONTRACTION.findall(masked)),
            'expanded': len(_EXPANDED.findall(masked))}


def _ltoks(seg):
    """Words of one list segment; None when it holds more than words and light symbols
    (masked code, a placeholder, a lone dash)."""
    seg = _L_SUFFIX.sub('', seg)           # "-ment, -tion, and -ance": suffixes are words here
    words = _L_WORD.findall(seg)
    rest = _L_WORD.sub('', seg).strip(_L_LIGHT)
    if rest:
        return ['CODE'] if not words and not rest.strip(MASK) else None     # masked code is one item
    return words


def _low(words):
    """Lower case for the word lists; an all-caps word stays as it is ("US" is not "us")."""
    return [w if len(w) > 1 and w.isupper() else w.lower().replace('’', "'") for w in words]


def _item(lw, most, inner=True):
    """A list item: 1 to `most` words, no pronoun or auxiliary, not opened by a function word.
    inner=False also refuses prepositions, conjunctions and adverbs inside it."""
    if not lw or len(lw) > most or lw[0] in _L_START_BAD or any(w in _L_CLAUSE for w in lw):
        return False
    if not inner and any(w in _L_INTRO and w != 'of' for w in lw[1:]):
        return False
    return True


def _capitalized(words):
    return all(w[:1].isupper() for w in words)


def _serial_item(lw, lc):
    """An item of a list with the serial comma (lw) before the last item (lc): a noun phrase, a
    wh-clause ("what they tried before") or a phrase that opens with the same preposition as the
    last item ("to a key, to placeholders, and to a screen")."""
    if not lw or len(lw) > 6:
        return False
    if lw[0] in _L_WH:
        return True
    if lw[0] in _L_PREP and lw[0] == lc[0] and not any(w in _L_CLAUSE for w in lw):
        return True
    return _item(lw, 6)


def list_series(s, raw=None):
    """Comma series that end in "and"/"or" in one sentence: [(pos, serial, items)].

    pos is where the item before the conjunction starts (the serial comma goes after it); serial is
    True for "A, B, and C"; items counts A, B, C and any items between. A series counts only when
    every item reads as a list item, so "the items, with images and prices", "surgical or not",
    "in two or three" and "Digital Markets, Competition and Consumers Act" are not lists. Text in
    quotation marks and Markdown link text (someone else's words, titles) is skipped. Linear: each
    conjunction reads at most _L_LOOK characters back and four words ahead."""
    out = []
    if ',' not in s:
        return out
    conj = [m for m in _L_CONJ.finditer(s)]
    if not conj:
        return out
    stops = [m.start() for m in _L_STOP_RX.finditer(s)]
    q_pos, q_cum = [], [(0, 0, 0)]          # running counts of ", “ and ”
    for q in _L_QUOTE_RX.finditer(s):
        d, o, c = q_cum[-1]
        ch = q.group(0)
        q_pos.append(q.start())
        q_cum.append((d + (ch == '"'), o + (ch == '“'), c + (ch == '”')))
    links = [(m.start(), m.end()) for m in _L_LINK_OUT.finditer(raw)] if raw and '](' in raw else []
    l_starts = [a for a, _ in links]
    for m in conj:
        j = m.start()
        if j < 2 or s[j - 1] not in ' \t':
            continue
        k = bisect.bisect_left(stops, j) - 1
        r0 = max(stops[k] + 1 if k >= 0 else 0, j - _L_LOOK)
        segs = _L_THOUSANDS.sub('0', s[r0:j]).split(',')
        if len(segs) < 2:
            continue
        serial = not segs[-1].strip()
        if serial:
            segs = segs[:-1]
            if len(segs) < 2:
                continue
        # someone else's words: inside quotation marks, or the text of a link to another site
        d, o, c = q_cum[bisect.bisect_left(q_pos, j)]
        if d % 2 or o > c:
            continue
        li = bisect.bisect_right(l_starts, j) - 1
        if li >= 0 and links[li][0] <= j < links[li][1]:
            continue
        bw = _ltoks(segs[-1])
        if not bw:
            continue
        lb = _low(bw)
        cm = _L_C_WORDS.match(s, m.end())
        if not cm:
            continue
        cw = cm.group(1).split()
        lc = _low(cw)
        if lc[0][:1].isdigit():
            continue
        after = s[cm.end():cm.end() + 4].lstrip(' \t')[:1]
        if serial and not _serial_item(lb, lc):
            continue
        mids, idx = [], len(segs) - 2
        while idx >= 1 and len(mids) < 12:
            t = _ltoks(segs[idx])
            lt = _low(t) if t else None
            if lt and (_serial_item(lt, lc) if serial else _item(lt, 4, inner=False)):
                mids.append(lt)
                idx -= 1
            else:
                break
        a_seg = segs[idx]
        a_all = _L_WORD.findall(_L_SUFFIX.sub('', a_seg)) or (_ltoks(a_seg) or [])
        if not a_all or not a_seg.rstrip(_L_LIGHT).endswith(a_all[-1]):
            continue
        la = _low(a_all)
        aw = _ltoks(a_seg)
        a_clean = bool(aw) and _item(_low(aw), 4)       # A is a whole item, not the end of a clause
        bad_end = _L_INTRO if serial else _L_START_BAD
        if la[-1] in bad_end and la[0] not in _L_WH and not (len(la) > 1 and la[-2] in _L_DET):
            continue                # "…from the script itself, read and run": A ends in a function word
        n = 3 + len(mids)
        if serial:
            if lc[0] in _L_C_SERIAL_BAD:
                continue            # "cut words, then sentences, and never a fact"
            if n == 3 and la[0] in _L_INTRO_CLAUSE and len(la) <= 4:
                continue            # "When it rains, the shop closes, and …": an opening clause
        else:
            if lc[0] in _L_START_BAD or (len(lc) > 1 and lc[1] in _L_AUX and not a_clean):
                continue            # "surgical or not"; "…in order, links and images are described"
            # a name with a comma in it: "Digital Markets, Competition and Consumers (DMCC) Act"
            if _capitalized([a_all[-1]] + bw + cw[:1]) and ((len(cw) > 1 and cw[1][:1].isupper()) or after == '('):
                continue
            nx = bisect.bisect_right(stops, j)
            r1 = min(stops[nx] if nx < len(stops) else len(s), m.end() + _L_LOOK)
            if after == ',' or _L_LATER.search(s, m.end(), r1):
                continue            # "housing and jobs, legal services, and …": the "and" is inside an item
            if (lb[-1] in _L_NUMW or lb[-1][:1].isdigit()) and lc[0] in _L_NUM_NEXT:
                continue            # "one or two", "ten or more"
            if (lb[0] in _L_DET) != (lc[0] in _L_DET):
                continue            # "…, clear and the same everywhere"; "a car or property pre-sale"
            if mids:
                if not _item(lb, 4, inner=False):
                    continue        # "a shop floor, anywhere with a clock and a queue"
                heads = set(x[0] for x in mids) | {lb[0]}
                if len(heads) == 1 and lb[0] in _L_DET and lc[0] != lb[0]:
                    continue        # "one idea, one example, one question or next step"
            else:
                if la[0] in _L_INTRO or not _item(lb, 3, inner=False):
                    continue        # "In June, sales and profits rose"; "…, with images and prices"
                # the noun phrase that ends A: from its last determiner ("a pen", "the postal address")
                d0 = len(la) - 1
                for i in range(len(la) - 2, max(-1, len(la) - 4), -1):
                    if la[i] in _L_DET:
                        d0 = i
                        break
                a_det = la[d0] in _L_DET
                if a_det != (lb[0] in _L_DET):
                    continue        # "One sentence, small and checkable": a noun, then its adjectives
                if not a_clean:
                    # A ends a longer clause: "We sell apples, pears and plums." The word before A must
                    # not be a preposition ("after washing, morning or night"), and B stays short.
                    prev = la[d0 - 1] if d0 > 0 else ''
                    proper = len(bw) == 1 and _capitalized([a_all[-1]] + bw + cw[:1])
                    if not proper and (prev in _L_INTRO or len(lb) > (3 if a_det else 1)):
                        continue
        b_off = r0 + sum(len(x) + 1 for x in segs[:-1])
        b_off += len(segs[-1]) - len(segs[-1].lstrip(' \t'))
        out.append((b_off, serial, n))
    return out



# ---------------------------------------------------------------- the checker
_SUPPRESS = {
    'en-ai-vocab': {'en-significance', 'en-marketing-has', 'en-ing-analysis', 'en-media-canned',
                    'en-profile-banned', 'en-profile-avoid', 'en-brand-spelling'},
    'en-buzzword': {'en-significance', 'en-journey', 'en-cliche-open', 'en-profile-banned', 'en-profile-avoid',
                    'en-brand-spelling', 'en-media-canned'},
    'en-jargon': {'en-buzzword', 'en-profile-banned', 'en-profile-avoid'},
    'en-copula-avoid': {'en-significance'},
    'en-vague-attribution': {'en-establishment-claim'},
    'en-sycophancy': {'en-chatbot-residue'},
    'en-minimizer': {'en-not-just', 'en-no-x-no-y', 'en-profile-banned', 'en-profile-avoid'},
    'en-not-x-but-y': {'en-not-just'},
    'en-please-note': {'en-didactic'},
    'en-complex-word': {'en-hidden-verb', 'en-profile-banned', 'en-profile-avoid'},
    'en-metaphor-buzz': {'en-profile-banned', 'en-profile-avoid'},
    'en-superlative': {'en-profile-banned', 'en-profile-avoid'},
    'en-fact-not-in-brief': {'en-testimonial'},
    'en-numeral-style': {'en-numeral-start'},
    'en-profile-avoid': {'en-profile-banned', 'en-brand-spelling'},
    'en-profile-banned': {'en-brand-spelling'},
    'en-spelling-variant': {'en-profile-banned', 'en-profile-avoid', 'en-brand-spelling'},
}
_ORDER = {ERROR: 0, WARN: 1}


def _finalize(issues):
    """Drop duplicates and issues covered by a more specific rule; sort errors first."""
    # spans by (line, key, rule), sorted, with the running maximum of their ends: an overlap test
    # is two bisects, not a walk over every issue of the line (a long line can hold thousands)
    groups = {}
    for x in issues:
        if x.get('_span') and x['line']:
            groups.setdefault((x['line'], x.get('key'), x['code']), []).append(x['_span'])
    index = {}
    for k, spans in groups.items():
        spans.sort()
        ends, top = [], None
        for _a, b in spans:
            top = b if top is None or b > top else top
            ends.append(top)
        index[k] = ([a for a, _b in spans], ends)

    def overlaps(line, key, code, a, b):
        got = index.get((line, key, code))
        if not got:
            return False
        i = bisect.bisect_left(got[0], b) - 1      # spans that start before b
        return i >= 0 and got[1][i] > a

    out, seen = [], set()
    for x in issues:
        ident = (x['line'], x.get('key'), x['col'], x['code'], x['message'])
        if ident in seen:
            continue
        sup = _SUPPRESS.get(x['code'])
        sp = x.get('_span')
        if sup and sp and x['line']:
            if any(overlaps(x['line'], x.get('key'), c, sp[0], sp[1]) for c in sup):
                continue
        seen.add(ident)
        out.append(x)
    out.sort(key=lambda x: (_ORDER[x['level']], x['line'] or 0, x.get('key') or '', x['col'] or 0))
    for x in out:
        span = x.pop('_span', None)
        if span:
            x['_end'] = span[1] + 1         # internal, for hub_mine; _hub_issues drops it before output
    return out


def _mk(line, col, code, level, msg, snippet='', key=None, span=None):
    return LF._issue(line, col, code, level, msg, snippet, key, span)


def _check(raw, masked, st, mode='doc', key=None, kind='text', facts=None):
    """Check one text. raw and masked have the same length and '\\n' line ends.
    mode 'doc' for a document or a CSV cell, 'string' for one locale value."""
    issues = []
    fmt = st.get('format') or ''
    # rules that need one continuous English text; off for English fragments in a Persian-majority
    # file (settings 'fragments', set by lint.py), where English lines are quotes and examples
    doc_rules = mode == 'doc' and not st.get('fragments')
    allow = set(w.lower() for w in st['allow'])
    raw_lines = raw.split('\n')
    lines = masked.split('\n')
    # link text in Markdown stays prose: hide only its brackets from the placeholder rule
    mlist = list(masked)
    for m in re.finditer(r'\[([^\[\]\n]{1,200})\](?=\()', raw):
        if mlist[m.start()] == '[':
            mlist[m.start()] = MASK
            mlist[m.end() - 1] = MASK
    masked = ''.join(mlist)
    lines = masked.split('\n')
    placeholders = 0
    new_lines = []
    for ln in lines:
        placeholders += len(LF.PLACEHOLDER.findall(ln))
        ln = LF.PLACEHOLDER.sub(lambda m: MASK * len(m.group(0)), ln)
        ln = _CORE_SUFFIX_EN.sub(lambda m: MASK * len(m.group(0)), ln)
        ln = LF._CORE_SUFFIX.sub(lambda m: MASK * len(m.group(0)), ln)
        new_lines.append(ln)
    lines = new_lines
    m2 = '\n'.join(lines)
    L = _Lines(m2)

    def add(off, code, level, msg, end=None, col_override=None):
        ln, col = L.pos(off)
        rl = raw_lines[ln - 1] if ln - 1 < len(raw_lines) else lines[ln - 1]
        c0 = col - 1
        e0 = c0 + ((end - off) if end is not None else 1)
        snippet = rl[max(0, c0 - 15):e0 + 15]
        issues.append(_mk(ln, col if col_override is None else col_override, code, level, msg, snippet, key,
                          (c0, e0)))

    def add_line(ln, code, level, msg, snippet=''):
        issues.append(_mk(ln, 0, code, level, msg, snippet, key))

    def tag(category, text):
        """The phrase id of the finding just added (internal _pid, never printed)."""
        pid = _lex_pid(category, text)
        if pid:
            issues[-1]['_pid'] = pid

    def allowed(word):
        return word.lower() in allow

    # URL/citation per line: a cited line does not need [source needed]
    url_lines = set()
    for a, b in LF._url_spans(raw):
        url_lines.add(L.pos(a)[0])
    for m in re.finditer(r'\[(?:source|sources|ref|citation)\b[^\]\n]{0,300}\]|\(source:|\bdoi:|\b10\.\d{4,9}/', raw,
                         re.I):
        url_lines.add(L.pos(m.start())[0])

    def cited(off):
        return L.pos(off)[0] in url_lines

    # ---- raw scans (code excluded; URLs and templates visible)
    hard = _hard_spans(raw, kind) if mode == 'doc' else []
    hs = [a for a, _ in hard]
    for rx in (_TEMPLATE_I, _TEMPLATE_C):
        for m in rx.finditer(raw):
            if _in_spans(m.start(), hard, hs) or (m.group(0).startswith('[') and
                                                  _whalory_bracket(m.group(0), st['allow'])):
                continue
            add(m.start(), 'en-template-residue', ERROR, 'Template residue "%s"; fill it in or use a Whalory '
                'bracket' % m.group(0)[:40], m.end())
    if kind not in ('locale',):
        for m in _TEMPLATE_VAR.finditer(raw):
            if not _in_spans(m.start(), hard, hs):
                add(m.start(), 'en-template-residue', ERROR, 'Template variable %s left in the prose'
                    % m.group(0)[:40], m.end())
    for m in _MARKUP.finditer(raw):
        if not _in_spans(m.start(), hard, hs):
            add(m.start(), 'en-chatbot-markup', ERROR, 'Chatbot citation artifact "%s"; delete it and re-check '
                'the claim' % m.group(0)[:30], m.end())
    if kind in ('md', 'text', 'html'):
        for m in _LINK_MD.finditer(raw):
            if not _in_spans(m.start(), hard, hs):
                add(m.start(), 'en-link-text', WARN, 'Link text "%s" does not say where it goes' % m.group('t'),
                    m.end())
    if kind == 'html':
        for m in _LINK_HTML.finditer(raw):
            if not _in_spans(m.start(), hard, hs):
                add(m.start(), 'en-link-text', WARN, 'Link text "%s" does not say where it goes' % m.group('t'),
                    m.end())

    # ---- pattern rules over the masked text
    def scan(rx, code, level, msg, gate=True, word_rule=False, cite_ok=False, lex=None):
        if not gate:
            return
        for m in rx.finditer(m2):
            s = m.start('at') if 'at' in rx.groupindex and m.group('at') is not None else m.start()
            e = m.end('at') if 'at' in rx.groupindex and m.group('at') is not None else m.end()
            if word_rule and allowed(m.group(0)):
                continue
            if cite_ok and cited(s):
                continue
            text_m = m2[s:e].replace(MASK, ' ').strip()
            add(s, code, level, msg(text_m) if callable(msg) else msg, e)
            if lex:
                tag(lex, text_m)

    long_fmt = not fmt or fmt not in SHORT_FORMATS
    vocab_hits = [(m.start(), m.group(0)) for m in _AI_VOCAB.finditer(m2) if not allowed(m.group(0))]
    buzz_hits = [(m.start(), m.group(0)) for m in _BUZZ.finditer(m2) if not allowed(m.group(0))]
    for s, w in vocab_hits:
        add(s, 'en-ai-vocab', WARN, '"%s" is over-represented in AI-written text; use the plain word or the fact' % w,
            s + len(w))
        tag('ai-vocab', w)
    for s, w in buzz_hits:
        add(s, 'en-buzzword', WARN, 'Buzzword "%s"; say what it does, for whom, with a number' % w, s + len(w))
        tag('buzzword', w)
    scan(_SIGNIF, 'en-significance', WARN, lambda t: 'Inflated significance "%s"; delete it or give the '
         'sourced consequence' % t)
    scan(_COPULA, 'en-copula-avoid', WARN, lambda t: '"%s": use is/are' % t)
    # a trailing ", highlighting …" clause that runs to the end of its sentence (".", "!" or "?" before
    # the line ends); one pass over the sentence ends keeps this linear
    ends = [m.start() for m in _ING_END.finditer(m2)] if _ING.search(m2) else []
    ing_done = -1                   # one warning per sentence, as when the match ran to its end
    for m in (_ING.finditer(m2) if ends else ()):
        if m.start() < ing_done:
            continue
        k = bisect.bisect_left(ends, m.end())
        if k < len(ends) and m2[ends[k]] != '\n':
            ing_done = ends[k] + 1
            add(m.start('at'), 'en-ing-analysis', WARN, 'Trailing ", %s …" commentary; cut it or make it a sourced '
                'sentence' % m.group('at'), m.end('at'))
    scan(_VAGUE_ATTR, 'en-vague-attribution', ERROR, lambda t: 'Vague attribution "%s"; name and link the '
         'source, or delete' % t, cite_ok=True)
    scan(_MEDIA, 'en-media-canned', WARN, lambda t: 'Canned media claim "%s"; list real outlets with dates' % t)
    scan(_NOT_JUST, 'en-not-just', WARN, '"not just X, but Y"; state Y')
    scan(_NOT_X, 'en-not-x-but-y', WARN, '"It\'s not X, it\'s Y" contrast; say Y and drop the straw man')
    scan(_NO_X, 'en-no-x-no-y', WARN, '"No X, no Y, just Z"; write one plain sentence with evidence')
    scan(_SUMMARY, 'en-summary-opener', WARN, lambda t: '"%s" summary opener; end on the last concrete point' % t)
    scan(_CHALLENGES, 'en-challenges-outlook', WARN, 'Challenges/outlook formula; give specific, sourced problems')
    scan(_DIDACTIC, 'en-didactic', WARN, lambda t: '"%s"; state the fact' % t)
    scan(_CHATBOT, 'en-chatbot-residue', ERROR, lambda t: 'Chat residue "%s"; remove it' % t)
    scan(_SIGNOFF, 'en-chatbot-residue', ERROR, lambda t: 'Chat residue "%s"; remove it' % t,
         gate=fmt not in SIGNOFF_OK_FORMATS)
    scan(_CUTOFF, 'en-cutoff-speculation', ERROR, lambda t: 'Knowledge-cutoff speculation "%s"; delete it or '
         'use [source needed: …]' % t)
    scan(_VAGUE_ASSOC, 'en-vague-association', WARN, lambda t: '"%s"; state the relation' % t, gate=long_fmt)
    scan(_MARKETING_HAS, 'en-marketing-has', WARN, lambda t: '"%s"; use "has"' % t, gate=fmt != 'ad')
    scan(_SYCO, 'en-sycophancy', ERROR, lambda t: 'Sycophancy "%s"; remove it' % t)
    if facts is None:
        # one warning per line, naming every number on it; a discount ("20% off", "save 20%") is an
        # offer term, not a claim (--facts still checks it against the brief)
        stat_lines = {}
        for m in _STAT.finditer(m2):
            if cited(m.start()):
                continue
            if m.group(0).rstrip().endswith(('%', 'percent', 'per cent')) and (
                    _DISCOUNT_AFTER.match(m2, m.end()) or _DISCOUNT_BEFORE.search(m2, max(0, m.start() - 12),
                                                                                 m.start())):
                continue
            stat_lines.setdefault(L.pos(m.start())[0], []).append(m)
        for _ln, ms in sorted(stat_lines.items()):
            vals = list(dict.fromkeys(x.group(0).strip() for x in ms))
            nums = ', '.join('"%s"' % v for v in vals[:4]) + (', …' if len(vals) > 4 else '')
            add(ms[0].start(), 'en-stat-claim', WARN, 'Number claim%s %s; trace %s to the brief or a source, else '
                '[source needed: metric]' % ('s' if len(ms) > 1 else '', nums, 'them' if len(ms) > 1 else 'it'),
                ms[0].end())
    scan(_SUPERLATIVE, 'en-superlative', WARN, lambda t: 'Superlative "%s"; qualify it with source and scope, '
         'or rewrite' % t)
    scan(_ESTABLISH, 'en-establishment-claim', ERROR, lambda t: 'Establishment claim "%s"; cite the actual '
         'study, or remove' % t, cite_ok=True)
    scan(_HIDDEN, 'en-hidden-verb', WARN, lambda t: 'Hidden verb "%s"; use the verb itself' % t)
    for m in _COMPLEX_RX.finditer(m2):
        if allowed(m.group(0)):
            continue
        add(m.start(), 'en-complex-word', WARN, '"%s": plain word "%s"'
            % (m.group(0), _COMPLEX_MAP.get(m.group(0).lower(), '')), m.end())
    scan(_SHALL, 'en-shall', WARN, '"shall": use must or must not')
    scan(_DOUBLE_NEG, 'en-double-negative', WARN, lambda t: 'Double negative "%s"; say it positively' % t)
    scan(_SLASH, 'en-slash', WARN, lambda t: '"%s": write "a or b, or both", or pick one' % t, gate=fmt != 'ui')
    scan(_PLEASE_NOTE, 'en-please-note', WARN, lambda t: '"%s": delete the frame' % t)
    scan(_MINIMIZER, 'en-minimizer', WARN, lambda t: '"%s": delete it, or give the real steps or time' % t,
         gate=fmt in MINIMIZER_FORMATS, word_rule=True)
    scan(_THERE_IS, 'en-there-is', WARN, lambda t: '"%s …": start with the real subject' % t)
    scan(_METAPHOR, 'en-metaphor-buzz', WARN, lambda t: '"%s": use a plain verb' % t, word_rule=True)
    scan(_NUMERIC_DATE, 'en-numeric-date', WARN, lambda t: 'Numeric date "%s"; write "June 12, 2026" (US) or '
         '"12 June 2026" (UK)' % t)
    hstyle = st.get('house_style')
    scan(_RANGE, 'en-range-hyphen', WARN, lambda t: 'Range "%s"; write "10 to 11"' % t,
         gate=hstyle in ('govuk', 'microsoft'))
    if fmt not in ('ui', 'headline'):
        # prose only: a table row holds labels and names ("Principles & Best Practices")
        amp_rows = LF._table_lines(lines, kind == 'md')[0] if '&' in m2 else ()
        for m in _AMP.finditer(m2):
            if L.pos(m.start())[0] - 1 not in amp_rows:
                add(m.start(), 'en-ampersand', WARN, '" & " in prose; write "and"', m.end())
    scan(_DOUBLE_SPACE, 'en-double-space', WARN, 'Two spaces after a full stop; use one (--fix)')
    scan(_ALL_CAPS, 'en-all-caps', WARN, 'Five or more words in capitals; use sentence case')
    scan(_LATIN_ABBR, 'en-latin-abbr', WARN, lambda t: '"%s": write "for example", "such as" or "that is"' % t,
         gate=hstyle == 'govuk')
    scan(_CLICHE_OPEN, 'en-cliche-open', WARN, lambda t: 'Cliché "%s"; start with the fact' % t, word_rule=True,
         lex='cliche-open')
    scan(_JOURNEY, 'en-journey', WARN, lambda t: '"%s": use a concrete verb' % t, word_rule=True, lex='journey')
    scan(_MORAL_CLOSE, 'en-moral-close', WARN, lambda t: 'Moral close "%s"; end on the action' % t,
         lex='moral-close')
    scan(_CLICKBAIT, 'en-clickbait', WARN, lambda t: 'Clickbait "%s"; say the finding' % t, lex='clickbait')
    hub = _hub_rx()
    if hub is not None:
        try:
            for m in hub[0].finditer(m2):
                got = hub[1].get(_hub_norm(m.group(1)))
                if got and not allowed(m.group(1)):
                    add(m.start(1), 'en-hub-tell', ERROR if got[1] == 'error' else WARN, _HUB.HUB_MESSAGE['en'],
                        m.end(1))
                    issues[-1]['_pid'] = got[0]
        except Exception:  # noqa: BLE001  (spec 5.8 step 10: built-in rules only for this call)
            _HUB.note_exception()
            issues[:] = [x for x in issues if x['code'] != 'en-hub-tell']
    for m in _TESTIMONIAL.finditer(m2):
        q = m.group('q')
        if facts is not None:
            if not facts.has_quote(q):
                add(m.start(), 'en-testimonial', ERROR, 'Quote with a name that is not in the facts; use only '
                    'verbatim, consented quotes, else [testimonial needed]', m.end())
        else:
            add(m.start(), 'en-testimonial', WARN, 'Quote with a name; use only verbatim, consented quotes, else '
                '[testimonial needed]', m.end())
    for m in _DOI.finditer(m2):
        add(m.start(), 'en-citation-check', WARN, 'DOI %s: resolve it and check it supports the claim'
            % m.group(0)[:40], m.end())
    for m in _ISBN.finditer(m2):
        if _isbn_ok(m.group('n')):
            add(m.start(), 'en-citation-check', WARN, 'ISBN %s: check it is the right book' % m.group('n'), m.end())
        else:
            add(m.start(), 'en-citation-check', ERROR, 'ISBN %s has a bad checksum' % m.group('n'), m.end())
    # dashes
    if hstyle == 'ap':
        for m in re.finditer(r'(?<=\S)—(?=\S)|(?<=\w) -- (?=\w)|(?<=\w)--(?=\w)|(?<=[A-Za-z]) - (?=[A-Za-z])', m2):
            add(m.start(), 'en-dash-spacing', WARN, 'AP style spaces the em dash: word — word (--fix)', m.end())
    else:
        for m in re.finditer(r'(?<=\S)[ \t]+—[ \t]+(?=\S)|(?<=\w) -- (?=\w)|(?<=\w)--(?=\w)'
                             r'|(?<=[A-Za-z]) - (?=[A-Za-z])', m2):
            add(m.start(), 'en-dash-spacing', WARN, 'Use a closed em dash: word—word (--fix)', m.end())
    # numerals
    if hstyle in ('ap', 'microsoft', 'chicago'):
        top = 99 if hstyle == 'chicago' else 9
        for m in _NUMERAL.finditer(m2):
            n = int(m.group('n'))
            if n < 1 or n > top:
                continue
            ln, col = L.pos(m.start())
            line = lines[ln - 1]
            prev = re.findall(r"[\w.]+", line[:col - 1])
            if prev and prev[-1].lower() in _NUM_PREV:
                continue
            if re.match(r'^[ \t]*(?:>[ \t]?)*\d{1,2}[.)][ \t]', line) and line.lstrip(' \t>').startswith(m.group('n')):
                continue
            add(m.start(), 'en-numeral-style', WARN, 'Spell out "%s" in body text (%s style)' % (m.group('n'), hstyle),
                m.end())

    # ---- line rules
    emoji_lines = []
    run = []
    runs = []
    for i, ln in enumerate(lines, 1):
        raw_ln = raw_lines[i - 1] if i - 1 < len(raw_lines) else ln
        if kind == 'md':
            m = _TITLE_CASE.match(ln)
            if m and hstyle != 'chicago':      # Chicago titles take title case; AP headlines do not
                add_line(i, 'en-title-case-heading', WARN, 'Title Case heading; use sentence case', raw_ln)
            m = _HEAD_PUNCT.match(ln)
            if m:
                add(L.starts[i - 1] + m.start('at'), 'en-heading-punct', WARN,
                    'Heading ends with "%s"; remove it (--fix)' % m.group('at'), L.starts[i - 1] + m.end('at'))
            if _INLINE_HDR.match(ln):
                run.append(i)
            else:
                if len(run) >= 3:
                    runs.append(run)
                run = []
        if fmt not in ('caption', 'story', 'reels') and _EMOJI_START.match(ln):
            emoji_lines.append(i)
        if fmt == 'caption' and (LF._MD_HEADER.match(ln) or LF._BOLD_LINE.match(ln)):
            add_line(i, 'en-caption-header', WARN, 'Heading or bold title line in a caption; start with the moment',
                     raw_ln)
    if len(run) >= 3:
        runs.append(run)
    for r in runs:
        add_line(r[0], 'en-inline-header-bullets', WARN, '%d bullets in a row start with a bold header; use prose '
                 'or plain bullets' % len(r), raw_lines[r[0] - 1])
    for i in emoji_lines:
        add_line(i, 'en-emoji-format', WARN, 'Emoji at the start of a line or bullet; remove it in professional copy',
                 raw_lines[i - 1][:40])

    # ---- sentences
    quotes, own = LF._quote_blocks(lines) if kind == 'md' else ([], lines)
    rows, seps = LF._table_lines(lines, kind == 'md')
    sents = []          # (line, raw text, words, masked text, tag, offset)
    paragraphs = []     # [(first line, words)]
    para_first, para_words = None, 0
    for i, ln in enumerate(lines, 1):
        s = ln.strip(' \t' + MASK + BLOCK)
        raw_ln = raw_lines[i - 1] if i - 1 < len(raw_lines) else ln
        base = L.starts[i - 1]
        if not s or (i - 1) in seps:
            if para_first is not None:
                paragraphs.append((para_first, para_words))
                para_first, para_words = None, 0
            continue
        hm = _MD_HEADING.match(ln) if kind == 'md' else None
        if hm:
            pieces, tag = [(hm.end(), len(ln.rstrip()))], 'heading'
        elif ln.lstrip().startswith('#') and kind != 'md' and _HASHTAG_LINE.match(ln):
            continue
        elif (i - 1) in rows:
            pieces, tag = LF._table_cells(ln), 'cell'
        else:
            lead = LF._LIST_LEAD.match(raw_ln if len(raw_ln) == len(ln) else ln)
            tag = 'item' if lead.group('mark') else 'prose'
            pieces = [(lead.end(), len(ln.rstrip()))]
        if tag != 'prose' and para_first is not None:
            paragraphs.append((para_first, para_words))
            para_first, para_words = None, 0
        for a0, b0 in pieces:
            seg = ln[a0:b0]
            for a, b in _sentence_spans(seg):
                part = seg[a:b]
                ws = _words(part)
                if ws:
                    sents.append((i, raw_ln[a0 + a:a0 + b], ws, part, tag, base + a0 + a))
                    if tag == 'prose':
                        if para_first is None:
                            para_first = i
                        para_words += len(ws)
    if para_first is not None:
        paragraphs.append((para_first, para_words))
    words_total = sum(len(x[2]) for x in sents)
    syl_total = sum(count_syllables(w) for x in sents for w in x[2])
    series = [list_series(x[3], x[1]) for x in sents]     # comma lists per sentence

    num_start = fmt not in NUMERAL_START_OFF
    for i, rpart, ws, part, tag, off in sents:
        if len(ws) > st['max_words']:
            add_line(i, 'en-long-sentence', WARN, '%d-word sentence; cap %d' % (len(ws), st['max_words']), rpart)
        # numeral at the start of a sentence (years allowed). Table cells and headings are labels, list
        # items are steps and quantities, a quotation is someone else's sentence, and codes, headlines,
        # interface strings and SMS start with numbers on purpose.
        m = _NUM_START.match(part) if num_start and tag not in ('cell', 'heading', 'item') else None
        if m and not re.match(r'^(1\d{3}|20\d{2})$', m.group(1)):
            add(off + m.start(1), 'en-numeral-start', WARN, 'Sentence starts with the numeral "%s"; spell it out '
                'or rephrase' % m.group(1), off + m.end(1))

    prose = [x for x in sents if x[4] == 'prose']
    if doc_rules:
        if prose and _RHETORICAL.match(prose[0][3].strip(' \t' + MASK)):
            add_line(prose[0][0], 'en-rhetorical-open', WARN, 'Rhetorical opening; open with something concrete',
                     prose[0][1])

        def eligible(x):
            # a list item that is only a link is navigation (a table of contents), not a sentence
            return x[4] == 'prose' or (x[4] == 'item' and len(x[2]) >= 3 and not _LINK_ONLY.match(x[1]))

        k = 0
        while k < len(sents) - 2:
            head = sents[k][2][0].lower()
            e = k
            while e < len(sents) and eligible(sents[e]) and sents[e][2][0].lower() == head:
                e += 1
            if e - k >= 3:          # one warning per run, however long
                add_line(sents[k][0], 'en-same-opening', WARN, '%s sentences in a row start with "%s"'
                         % ('Three' if e - k == 3 else str(e - k), sents[k][2][0]), sents[k][1])
                k = e
            else:
                k += 1
        lens = [len(x[2]) for x in prose]
        if len(lens) >= 6:
            mean = sum(lens) / float(len(lens))
            sd = math.sqrt(sum((v - mean) ** 2 for v in lens) / float(len(lens)))
            if sd < 3:
                add_line(0, 'en-flat-rhythm', WARN, 'Sentence lengths barely vary (SD %.1f words); mix long and short'
                         % sd)
        for first, n in paragraphs:
            if n > 150 and kind in ('md', 'text', 'html'):
                add_line(first, 'en-long-paragraph', WARN, '%d-word paragraph; split it by topic (never over 250)' % n)
        # passive density
        if len(sents) >= 5:
            pas = [x for x in sents if _PASSIVE.search(x[3])]
            if len(pas) / float(len(sents)) > 0.20:
                for x in pas[:5]:
                    add_line(x[0], 'en-passive', WARN, '%d of %d sentences are passive; name the actor'
                             % (len(pas), len(sents)), x[1])
        # triads: lists of exactly three items in prose and list items (not headings or table cells)
        if words_total >= 60:
            tri = [k for k, x in enumerate(sents) if x[4] in ('prose', 'item') and any(h[2] == 3 for h in series[k])]
            tri_set = set(tri)
            dense = len(tri) >= 2 and len(tri) * 100.0 / words_total >= 2
            consec = [k for k in tri if k + 1 in tri_set or k - 1 in tri_set]
            flagged = tri if dense else consec
            for k in flagged[:5]:
                add_line(sents[k][0], 'en-triads', WARN, 'List of three again (%d in %d words); keep only real '
                         'lists of three' % (len(tri), words_total), sents[k][1])
        # sentence-initial connectors
        adds = list(_ADDITIONALLY.finditer(m2))
        if len(adds) >= 2 and len(adds) > words_total / 200.0:
            for m in adds:
                add(m.start('at'), 'en-additionally', WARN, '"%s" opens %d sentences; delete it or use "also"'
                    % (m.group('at'), len(adds)), m.end('at'))
        # abbreviations: the first use in the body text. Not in link text (the title of someone
        # else's page) and not in a heading (a label; the body spells it out below it).
        if words_total >= 80:
            seen_abbr, caps_line = set(), {}
            lt = [(x.start(), x.end()) for x in _L_LINK_TEXT.finditer(raw)] if '](' in raw else []
            lt_starts = [a for a, _ in lt]
            defined = {}
            for x in _ABBR_PAREN.finditer(m2):
                defined.setdefault(x.group(1), x.start())
            for m in _ABBR_TOKEN.finditer(m2):
                if lt and _in_spans(m.start(), lt, lt_starts):
                    continue
                ln, col = L.pos(m.start())
                line = lines[ln - 1]
                if kind == 'md' and _MD_HEADING.match(line):
                    continue
                tok = m.group(0)
                base_tok = tok[:-1] if tok.endswith('s') and tok[:-1].isupper() and len(tok) > 2 else tok
                if base_tok in seen_abbr:
                    continue
                seen_abbr.add(base_tok)
                if base_tok in _ABBR_OK or tok in _ABBR_OK or _ROMAN.match(base_tok) or allowed(base_tok):
                    continue
                if st.get('brand_latin') and base_tok.lower() == st['brand_latin'].lower():
                    continue
                if ln not in caps_line:     # a line set in capitals: not an abbreviation problem
                    caps_line[ln] = len(re.findall(r'\b[A-Z]{2,}\b', line)) >= 3 and not re.search(r'[a-z]{3,}', line)
                if caps_line[ln]:
                    continue
                before = m2[max(0, m.start() - 1):m.start()]
                after = m2[m.end():m.end() + 2]
                if before == '(' or after.startswith(' (') or defined.get(base_tok, len(m2)) < m.start():
                    continue
                if _ABBR_DEF.search(m2, max(0, m.start() - 24), m.start()):
                    continue        # inside the defining parenthesis: "Creative Commons (CC BY 4.0)"
                add(m.start(), 'en-undefined-abbr', WARN, '"%s" is not expanded at first use' % base_tok, m.end())
        # AI-vocabulary density: 300-word windows
        if words_total >= 150 and (vocab_hits or buzz_hits):
            wstarts = [m.start() for m in _WORD.finditer(m2)]
            hits = [(bisect.bisect_right(wstarts, s), _lemma(w), 'v', s) for s, w in vocab_hits]
            hits += [(bisect.bisect_right(wstarts, s), _lemma(w), 'b', s) for s, w in buzz_hits]
            hits.sort()
            nwords = len(wstarts)
            reported = False
            start = 0
            while start < max(1, nwords - 150) and not reported:
                win = [h for h in hits if start <= h[0] < start + 300]
                v = set(h[1] for h in win if h[2] == 'v')
                allw = set(h[1] for h in win)
                if len(v) >= 3 or len(allw) >= 5:
                    add(win[0][3], 'en-ai-vocab-density', ERROR, '%d distinct AI-vocabulary and buzzword lemmas in '
                        '300 words (%s); rewrite from the facts up' % (len(allw), ', '.join(sorted(allw)[:6])),
                        win[0][3] + 1)
                    reported = True
                start += 150
        # em dash density
        dashes = [m.start() for m in re.finditer('—', m2)]
        if dashes:
            block_of, blk = [], 0
            for ln in lines:
                if not ln.strip(' \t' + MASK + BLOCK):
                    blk += 1
                block_of.append(blk)
            per_para = {}
            for d in dashes:
                per_para.setdefault(block_of[L.pos(d)[0] - 1], []).append(d)
            flagged_para = False
            for p, ds in sorted(per_para.items()):
                if len(ds) > 1:
                    add(ds[1], 'en-dash-density', WARN, '%d em dashes in one paragraph; use commas, colons or full '
                        'stops' % len(ds), ds[1] + 1)
                    flagged_para = True
            if not flagged_para and len(dashes) > 1 and len(dashes) > words_total / 150.0:
                add(dashes[1], 'en-dash-density', WARN, '%d em dashes in %d words; use commas, colons or full stops'
                    % (len(dashes), words_total), dashes[1] + 1)
        # bold
        if kind == 'md':
            bolds = [m for ln in own for m in _BOLD.finditer(ln)]
            if len(bolds) >= 2 and len(bolds) > words_total / 100.0:
                add_line(0, 'en-bold-overuse', WARN, '%d bold spans in %d words; remove bold from running text'
                         % (len(bolds), words_total))

    # ---- document marks (block quotes in Markdown are someone else's words)
    body = '\n'.join(own)
    for m in re.finditer(r'!{2,}', m2):
        add(m.start(), 'en-bangs', ERROR, 'Repeated exclamation marks', m.end())
    bangs = len(re.findall(r'!', body))
    if bangs > st['exclaim_max']:
        add_line(0, 'en-bangs', WARN, 'Exclamation marks: %d; limit %d' % (bangs, st['exclaim_max']))
    if fmt in ('error', 'hard'):
        for m in re.finditer(r'!', m2):
            add(m.start(), 'en-bangs', WARN, 'No exclamation marks in %s messages' % fmt, m.end())
    emo = EMOJI.findall(body)
    if len(emo) > st['emoji_max']:
        add_line(0, 'en-emoji', WARN, 'Emoji: %d; limit %d' % (len(emo), st['emoji_max']), ' '.join(emo[:6]))

    # quotes and spelling: the author's own text and each Markdown block quote (someone else's words,
    # often a sample in another variant) are checked apart, as lint_fa does for register
    qblock = {}
    if kind == 'md':
        n_b, in_b = 0, False
        for i, ln in enumerate(lines, 1):
            if LF._BQ.match(ln):
                if not in_b:
                    n_b, in_b = n_b + 1, True
                qblock[i] = n_b
            else:
                in_b = False

    def part_of(off):
        return qblock.get(L.pos(off)[0], 0) if qblock else 0

    if doc_rules:
        groups = {}
        for m in re.finditer('["\'\u201c\u201d\u2018\u2019]', m2):
            g = groups.setdefault(part_of(m.start()), ([], []))
            (g[0] if m.group(0) in '"\'' else g[1]).append(m.start())
        for straight, curly in groups.values():
            if straight and curly:
                minority = straight if len(straight) < len(curly) else curly
                add(minority[0], 'en-quote-mix', WARN, 'Straight and curly quotes in one text (%d straight, %d '
                    'curly); normalize them (--fix)' % (len(straight), len(curly)), minority[0] + 1)

    hits = []
    for h in _spelling_hits(m2):
        ln, col = L.pos(h[0])
        if h[2][:1].isupper() and not _sentence_initial(lines[ln - 1], col - 1):
            continue
        hits.append(h)
    uk = [h for h in hits if h[4] == 'uk']
    mode_sp = st.get('spelling')
    if doc_rules:
        by_part = {}
        for h in hits:
            by_part.setdefault(part_of(h[0]), []).append(h)
        for part_hits in by_part.values():
            p_us, p_uk, p_ize, p_ise = _mix_evidence(part_hits)
            words = set(h[2].lower() for h in part_hits)
            pair_both = words & set(SPELLING_FORMS[w][2] for w in words)
            if (p_us and p_uk) or (p_ize and p_ise) or pair_both:
                first_uk = (p_uk or p_ise)[0] if (p_uk or p_ise) else part_hits[0]
                add(first_uk[0], 'en-spelling-mix', ERROR, 'US and UK spellings in one text (US: %s; UK: %s); pick '
                    'one variant' % (', '.join(sorted(set(h[2].lower() for h in part_hits if h[4] == 'us'))[:3]),
                                     ', '.join(sorted(set(h[2].lower() for h in part_hits if h[4] == 'uk'))[:3])),
                    first_uk[1])
    if mode_sp:
        for s, e, w, fam, side in hits:
            if part_of(s):
                continue            # a quoted sample keeps its own variant
            tgt = _spell_target(w, mode_sp)
            if tgt:
                add(s, 'en-spelling-variant', WARN, '"%s" is off the %s spelling; write "%s" (--fix)'
                    % (w, mode_sp, _match_case(w, tgt)), e)

    # Oxford comma and contractions
    oc = st.get('oxford_comma')
    ser, non = [], []
    for k, (i, rpart, ws, part, tag, off) in enumerate(sents):
        for pos, is_serial, _n in series[k]:
            (ser if is_serial else non).append(off + pos)
    if oc is True:
        for p in non:
            add(p, 'en-oxford-comma', WARN, 'Serial comma missing before "and"/"or" (profile oxford_comma: true)', p + 1)
    elif oc is False:
        for p in ser:
            add(p, 'en-oxford-comma', WARN, 'Serial comma present (profile oxford_comma: false)', p + 1)
    elif ser and non and doc_rules:
        minority = non if len(non) <= len(ser) else ser
        for p in minority:
            add(p, 'en-oxford-comma', WARN, 'Lists with and without the serial comma in one text (%d with, %d without)'
                % (len(ser), len(non)), p + 1)
    ct = st.get('contractions')
    if ct == 'avoid':
        scan(_CONTRACTION, 'en-contraction', WARN, lambda t: 'Contraction "%s"; the profile avoids contractions' % t)
    elif ct == 'positive-only' or hstyle == 'govuk':
        scan(_NEG_CONTRACTION, 'en-contraction', WARN, lambda t: 'Negative contraction "%s"; write it in full' % t)
    if ct == 'use' and fmt in NO_CONTRACTION_FORMATS:
        scan(_EXPANDED, 'en-no-contraction', WARN, lambda t: '"%s": the profile uses contractions here' % t)

    # readability
    fre, fkgl = readability_from((words_total, syl_total), len(sents))
    if doc_rules and words_total >= 100 and fmt in READ_FORMATS and fkgl is not None:
        if fkgl > st['reading_grade_max']:
            add_line(0, 'en-readability-grade', WARN, 'Flesch–Kincaid grade %.1f; target %s or lower'
                     % (fkgl, st['reading_grade_max']))
        if fre < 30:
            add_line(0, 'en-readability-fre', WARN, 'Flesch Reading Ease %.1f; below 30 is very hard to read' % fre)

    # profile words
    brand = st.get('brand_latin')
    if brand:
        for m in re.finditer(r'(?<![\w\-])%s(?![\w\-])' % re.escape(brand), m2, re.I):
            got = m.group(0)
            if got == brand or (got.isupper() and _all_caps_context(m2, m.start())):
                continue           # exact form, or a line set in capitals
            add(m.start(), 'en-brand-spelling', ERROR, 'Brand name "%s"; write "%s"' % (got, brand), m.end())
    for bad, good in st['misspellings'].items():
        for m in re.finditer(r'(?<![\w\-])%s(?![\w\-])' % re.escape(bad), m2, re.I):
            if m.group(0) == good:
                continue
            add(m.start(), 'en-brand-spelling', ERROR, 'Brand spelling "%s"; write "%s"' % (m.group(0), good), m.end())
    for w in dict.fromkeys(st['banned']):
        for m in _word_rx(w).finditer(m2):
            add(m.start(), 'en-profile-banned', ERROR, 'Banned by the profile: "%s"' % w, m.end())
    for w in dict.fromkeys(st['avoid']):
        hint = st['prefer'].get(w)
        for m in _word_rx(w).finditer(m2):
            add(m.start(), 'en-profile-avoid', WARN, 'The profile avoids "%s"%s' % (w, '; use "%s"' % hint if hint else ''),
                m.end())
    if st.get('jargon_on'):
        for m in _JARGON.finditer(m2):
            if allowed(m.group(0)):
                continue
            add(m.start(), 'en-jargon', WARN, 'Jargon "%s"; the profile wants plain words (jargon=%s)'
                % (m.group(0), st['dials'].get('jargon')), m.end())

    # facts
    if facts is not None and mode in ('doc', 'string'):
        issues += _fact_issues(raw, m2, L, lines, raw_lines, sents, facts, st, key, hard)

    info = {'lens': [len(x[2]) for x in sents], 'placeholders': placeholders, 'words': words_total,
            'syllables': syl_total, 'paragraphs': len(paragraphs), 'us': len([h for h in hits if h[4] == 'us']),
            'uk': len(uk), 'fre': fre, 'fkgl': fkgl, 'masked': m2}
    return issues, info


def _all_caps_context(text, pos):
    line_start = text.rfind('\n', 0, pos) + 1
    line_end = text.find('\n', pos)
    line = text[line_start:line_end if line_end >= 0 else len(text)]
    return len(re.findall(r'\b[A-Z]{2,}\b', line)) >= 3


@functools.lru_cache(maxsize=4096)
def _word_rx(w):
    w = w.strip()
    core = re.escape(w).replace('\\ ', r'\s+')
    return re.compile(r"(?<![\w'’\-])%s(?:s|es)?(?![\w'’\-])" % core, re.I)


# ---------------------------------------------------------------- the Whalory Hub overlay (spec 5.9)
_HUB_RX = {}


def _hub_norm(s):
    return re.sub(r'\s+', ' ', s.replace('’', "'")).strip().lower()


def _hub_rx():
    """The hub phrases (ht-) as one alternation, longest first, each re.escape()d inside the
    boundaries of _word_rx (spec 5.9, 7.5): (regex, {normalised phrase: (id, state)}) or None."""
    if _HUB is None:
        return None
    phrases = tuple(_HUB.hub_phrases('en'))
    if not phrases:
        return None
    got = _HUB_RX.get(phrases)
    if got is None:
        alt = '|'.join(re.escape(p).replace('\\ ', r'\s+').replace("'", A).replace('’', A)
                       for p, _pid, _st in phrases)
        got = (re.compile(r"(?<![\w'’\-])(%s)(?:s|es)?(?![\w'’\-])" % alt, re.I),
               dict((_hub_norm(p), (pid, st)) for p, pid, st in phrases))
        _HUB_RX.clear()
        _HUB_RX[phrases] = got
    return got


def _hub_issues(issues):
    """Overlay severities and hidden findings (spec 5.9); without hub_overlay only the internal fields go."""
    if _HUB is not None:
        return _HUB.apply_issues('en', issues)
    for x in issues:
        x.pop('_pid', None)
        x.pop('_end', None)
    return issues


def _hub_param(name, default):
    return _HUB.param('en', name, default) if _HUB is not None else default


def _hub_stats(stats):
    return _HUB.stamp_stats('en', stats) if _HUB is not None else stats


_PROPER = re.compile(r"\b[A-Z][a-zA-Z'’\-]*[a-zA-Z]\b|\b[A-Z]\b")
_STOP_PROPER = set('''I A An The This That These Those It Its We Our You Your They Their He She His Her My Me Us
If When Then So And But Or Yes No OK Hi Hello Dear Thanks Thank Please'''.split())
_NUM_FACT = re.compile(r"(?<![\w.])[$£€]?\d[\d,]*(?:\.\d+)?")


def _fact_issues(raw, m2, L, lines, raw_lines, sents, facts, st, key, hard):
    out, seen = [], set()

    def flag(off, end, item, what):
        ident = (what, item.lower())
        if ident in seen:
            return
        seen.add(ident)
        ln, col = L.pos(off)
        rl = raw_lines[ln - 1] if ln - 1 < len(raw_lines) else ''
        out.append(_mk(ln, col, 'en-fact-not-in-brief', ERROR, '%s "%s" is not in the facts; remove it, or bracket '
                       'it: [source needed: …]' % (what, item[:40]), rl[max(0, col - 16):col - 1 + (end - off) + 15],
                       key, (col - 1, col - 1 + (end - off))))

    brand = (st.get('brand_latin') or '').lower()
    for m in _NUM_FACT.finditer(m2):
        num = m.group(0).lstrip('$£€')
        if not facts.has_number(num):
            flag(m.start(), m.end(), m.group(0), 'Number')
    heading_lines = set(i for i, ln in enumerate(lines, 1) if _MD_HEADING.match(ln))
    for i, rpart, ws, part, tag, off in sents:
        if tag == 'heading' or i in heading_lines:
            continue
        first = True
        for m in _PROPER.finditer(part):
            w = m.group(0)
            if first:
                first = False
                if not re.search(r'[A-Za-z0-9]', part[:m.start()].strip(' \t"“(‘\'' + MASK)):
                    continue
            if w in _STOP_PROPER or w.lower() == brand or w.lower() in _MONTHS and facts.has_word(w[:3]):
                continue
            if w.isupper() and len(w) == 1:
                continue
            if not facts.has_word(w):
                flag(off + m.start(), off + m.end(), w, 'Name')
    for a, b in LF._url_spans(raw):
        if _in_spans(a, hard):
            continue
        u = raw[a:b]
        if not facts.has_url(u):
            flag(a, b, u, 'URL')
    for m in re.finditer(r'[“"]([^“”"\n]{12,300})[”"]', m2):
        q = m.group(1)
        if len(q.split()) >= 3 and not facts.has_quote(q):
            flag(m.start(), m.end(), q, 'Quote')
    return out


# ---------------------------------------------------------------- channel
def _channel_check(text, ch):
    """Length against the channel limit in its unit. (issues, info for stats)."""
    spec = ch.get('spec') or {}
    t = text.strip()
    field = ch.get('field') or ''
    latin = (ch.get('specs') or {}).get(field + '_latin') if field and not field.endswith('_latin') else None
    if isinstance(latin, dict) and ch.get('kind') == 'sms' and t and TC.sms_segments(t)[4] == 'gsm7':
        # an all-Latin (GSM-7) SMS on a panel whose body limit is for Persian (UCS-2): use the Latin limit
        ch = dict(ch, spec=latin, field=field + '_latin')
        spec = latin
    unit = (spec.get('unit') or 'char').lower()
    if unit not in TC.UNITS:
        unit = 'char'
    status = (spec.get('status') or 'unverified').lower()
    verified = status == 'verified'
    note = '' if verified else 'unverified limit'
    info = {'id': ch.get('id'), 'group': ch.get('group'), 'field': ch.get('field'), 'unit': unit,
            'chars': len(t), 'max_chars': spec.get('max_chars'), 'visible_chars': spec.get('visible_chars'),
            'status': status, 'verified_on': spec.get('verified_on', ''), 'source': spec.get('source', ''),
            'note': note}
    issues = []
    tail = ' (%s)' % note if note else ''
    level = ERROR if verified else WARN
    label = '%s%s' % (ch.get('id'), '.' + ch['field'] if ch.get('field') else '')
    mx = spec.get('max_chars')
    unit_name = {'char': 'characters', 'byte': 'bytes', 'utf16': 'UTF-16 units', 'grapheme': 'graphemes',
                 'weighted': 'weighted characters', 'word': 'words', 'items': 'items'}.get(unit, unit)
    if unit == 'segment':
        segs, units, single, part, enc = TC.sms_segments(t)
        info.update({'segments': segs, 'units': units, 'encoding': enc, 'single': single, 'per_part': part,
                     'count': segs})
        limit_seg = spec.get('max_segments')
        if limit_seg is None and isinstance(mx, int) and 0 < mx <= 20:
            limit_seg = mx
        if isinstance(limit_seg, int) and segs > limit_seg:
            issues.append((level, 'en-channel-length', '%s: %d SMS segments (%d units, %s); limit %d. One segment '
                           'holds %d, each part of a longer message %d%s'
                           % (label, segs, units, enc, limit_seg, single, part, tail)))
        elif isinstance(mx, int) and mx > 20 and units > mx:
            issues.append((level, 'en-channel-length', '%s: %d units; limit %d (%d segments)%s'
                           % (label, units, mx, segs, tail)))
    else:
        n = TC.count(t, unit)
        info['count'] = n
        seg_note = ''
        if ch.get('kind') == 'sms':
            segs, units, single, part, enc = TC.sms_segments(t)
            info.update({'segments': segs, 'units': units, 'encoding': enc, 'single': single, 'per_part': part})
            seg_note = ' (%d segments; %s: %d in one, %d per part)' % (segs, enc, single, part)
        if isinstance(mx, int) and unit != 'items' and n > mx:
            issues.append((level, 'en-channel-length', '%s: %d %s; limit %d, %d over%s%s'
                           % (label, n, unit_name, mx, n - mx, seg_note, tail)))
        vis = spec.get('visible_chars')
        vis_n = n if unit in ('char', 'grapheme', 'utf16', 'weighted') else len(t)
        if isinstance(vis, int) and vis_n > vis:
            issues.append((WARN, 'en-channel-visible', '%s: only the first %d characters show before "more"; '
                           'front-load the point%s' % (label, vis, tail)))
    mi, imx = spec.get('max_items'), spec.get('item_max_chars')
    if unit == 'items' or isinstance(mi, int) or isinstance(imx, int):
        field = (ch.get('field') or '').lower()
        items = TC.hashtags(t) if 'hashtag' in field else TC.split_items(t)
        info['items'] = len(items)
        if isinstance(mi, int) and len(items) > mi:
            issues.append((level, 'en-channel-items', '%s: %d items; limit %d%s' % (label, len(items), mi, tail)))
        if isinstance(imx, int):
            long_items = [x for x in items if len(x) > imx]
            for x in long_items[:3]:
                issues.append((level, 'en-channel-items', '%s: item "%s" has %d characters; limit %d%s'
                               % (label, x[:30], len(x), imx, tail)))
    return issues, info


def _resolve_channel(channel, channels_dir=None):
    if channel is None or isinstance(channel, dict):
        return channel
    return LF.resolve_channel(channel, channels_dir)


# ---------------------------------------------------------------- lint
def _make_stats(issues, info, st, kind, extra=None):
    lens = info['lens']
    stats = {'kind': kind, 'sentences': len(lens),
             'avg_words': round(sum(lens) / float(len(lens)), 1) if lens else 0,
             'max_words': st['max_words'], 'emoji_max': st['emoji_max'], 'exclaim_max': st['exclaim_max'],
             'format': st.get('format') or '', 'profile': st.get('profile', ''),
             'placeholders': info['placeholders'],
             'errors': sum(1 for x in issues if x['level'] == ERROR),
             'warnings': sum(1 for x in issues if x['level'] == WARN),
             'words': info['words'], 'paragraphs': info['paragraphs'],
             'readability': {'fre': info['fre'], 'fkgl': info['fkgl'], 'syllables': info['syllables'],
                             'grade_max': st['reading_grade_max']},
             'spelling': {'us': info['us'], 'uk': info['uk'], 'mode': st.get('spelling'),
                          'variant': st.get('variant')}}
    if extra:
        stats.update(extra)
    return stats


def _profile_issues(st):
    return [_mk(0, 0, code, WARN, msg) for code, msg in st.get('warnings', [])]


def _settings_for(profile, fmt, channel, max_words, settings):
    if settings is not None:
        return settings
    f = fmt or (channel or {}).get('format_id') or None
    return resolve_settings(profile, f, max_words)


def lint(text, profile=None, fmt=None, channel=None, kind=None, settings=None, facts=None, md=False,
         max_words=None):
    """Check English text. Returns (issues, stats). See migration/v3/lint-api.md."""
    kind = kind or ('md' if md else 'text')
    channel = _resolve_channel(channel)
    st = _settings_for(profile, fmt, channel, max_words, settings)
    fx = facts if (facts is None or isinstance(facts, _Facts)) else _Facts(facts)
    if kind == 'locale':
        return lint_locale(text, settings=st, channel=channel, facts=fx)
    if kind == 'csv':
        return lint_csv(text, settings=st, channel=channel, facts=fx)
    text = clean_text(text)
    masked = LF.mask_prose(text, kind)
    issues, info = _check(text, masked, st, 'doc', kind=kind, facts=fx)
    issues = _profile_issues(st) + issues
    extra = {}
    if channel:
        ch_issues, ch_info = _channel_check(text, channel)
        issues += [_mk(0, 0, code, level, msg) for level, code, msg in ch_issues]
        extra['channel'] = ch_info
    issues = _hub_issues(_finalize(issues))
    return issues, _hub_stats(_make_stats(issues, info, st, kind, extra))


def _en_value(value):
    """True when a locale value or cell is English: more Latin than Persian letters after masking."""
    masked = mask_value(value)
    en = len(_LATIN.findall(masked))
    fa = len(_FA_LETTER.findall(masked))
    return en > 0 and en > fa


def lint_locale(text, path='', profile=None, fmt=None, channel=None, max_words=None, settings=None,
                entries=None, facts=None):
    """English values of a locale file; issues carry the key."""
    channel = _resolve_channel(channel)
    st = _settings_for(profile, fmt, channel, max_words, settings)
    fx = facts if (facts is None or isinstance(facts, _Facts)) else _Facts(facts)
    if entries is None:
        entries = extract_locale(text, path or 'x.json')
    issues, lens, placeholders, n_str, skipped = [], [], 0, 0, 0
    words = syl = paras = us = uk = 0
    joined = []
    for key, value, line in entries:
        if not isinstance(value, str):
            continue
        if not _en_value(value):
            skipped += 1
            continue
        value = clean_text(value)
        masked = mask_value(value)
        n_str += 1
        starts, pos = [], 0
        for ln in value.split('\n'):
            starts.append(pos)
            pos += len(ln) + 1
        its, info = _check(value, masked, st, 'string', key=key, kind='locale', facts=fx)
        for it in its:
            sub = it['line']
            if sub and it['col']:
                it['col'] = starts[sub - 1] + it['col']
            if sub and it.get('_span'):
                off = starts[sub - 1]
                it['_span'] = (it['_span'][0] + off, it['_span'][1] + off)
            it['line'] = line
        issues += its
        lens += info['lens']
        placeholders += info['placeholders']
        words += info['words']
        syl += info['syllables']
        paras += info['paragraphs']
        us += info['us']
        uk += info['uk']
        joined.append(info['masked'].replace('\n', ' '))
        if channel:
            for level, code, msg in _channel_check(value, channel)[0]:
                issues.append(_mk(line, 0, code, level, msg, value, key))
    # file-level: spelling mix and quote style across all values
    allm = '\n'.join(joined)
    hits = _spelling_hits(allm)
    u, k, iz, is_ = _mix_evidence(hits)
    if (u and k) or (iz and is_):
        issues.append(_mk(0, 0, 'en-spelling-mix', ERROR, 'US and UK spellings across the file (US: %s; UK: %s)'
                          % (', '.join(sorted(set(h[2].lower() for h in hits if h[4] == 'us'))[:3]),
                             ', '.join(sorted(set(h[2].lower() for h in hits if h[4] == 'uk'))[:3]))))
    straight = len(re.findall('["\']', allm))
    curly = len(re.findall('[“”‘’]', allm))
    if straight and curly:
        issues.append(_mk(0, 0, 'en-quote-mix', WARN, 'Straight and curly quotes across the file (%d straight, '
                          '%d curly)' % (straight, curly)))
    issues = _hub_issues(_finalize(_profile_issues(st) + issues))
    fre, fkgl = readability_from((words, syl), len(lens))
    info = {'lens': lens, 'placeholders': placeholders, 'words': words, 'syllables': syl, 'paragraphs': paras,
            'us': us, 'uk': uk, 'fre': fre, 'fkgl': fkgl}
    extra = {'strings': n_str, 'skipped': skipped}
    if channel:
        extra['channel'] = {'id': channel.get('id'), 'field': channel.get('field'),
                            'note': '' if (channel.get('spec') or {}).get('status') == 'verified'
                            else 'unverified limit', 'per_string': True}
    return issues, _hub_stats(_make_stats(issues, info, st, 'locale', extra))


def lint_csv(text, path='', profile=None, fmt=None, channel=None, max_words=None, settings=None,
             columns=None, key=None, md=False, delimiter=None, facts=None):
    """Each English cell of the text columns, as a whole text; key "row n/<sku>/<column>"."""
    channel = _resolve_channel(channel)
    st = _settings_for(profile, fmt, channel, max_words, settings)
    fx = facts if (facts is None or isinstance(facts, _Facts)) else _Facts(facts)
    info = csv_cells(text, path, columns, key, delimiter)
    kind = 'md' if md else 'text'
    issues, lens, placeholders, n_cells, skipped, flagged = [], [], 0, 0, 0, set()
    words = syl = paras = us = uk = 0
    for rowno, code, col, value, line in info['cells']:
        if not _en_value(value):
            skipped += 1
            continue
        value = clean_text(value)
        masked = LF.mask_prose(value, kind)
        n_cells += 1
        k = 'row %d/%s/%s' % (rowno, code, col)
        its, inf = _check(value, masked, st, 'doc', key=k, kind=kind, facts=fx)
        for it in its:
            it['line'] = line + (it['line'] - 1 if it['line'] else 0)
        if channel:
            for level, c, msg in _channel_check(value, channel)[0]:
                its.append(_mk(line, 0, c, level, msg, value, k))
        if its:
            flagged.add(rowno)
        issues += its
        lens += inf['lens']
        placeholders += inf['placeholders']
        words += inf['words']
        syl += inf['syllables']
        paras += inf['paragraphs']
        us += inf['us']
        uk += inf['uk']
    issues = _hub_issues(_finalize(_profile_issues(st) + issues))
    fre, fkgl = readability_from((words, syl), len(lens))
    inf = {'lens': lens, 'placeholders': placeholders, 'words': words, 'syllables': syl, 'paragraphs': paras,
           'us': us, 'uk': uk, 'fre': fre, 'fkgl': fkgl}
    extra = {'rows': info['rows'], 'cells': n_cells, 'skipped': skipped, 'rows_flagged': len(flagged),
             'columns': info['columns'], 'key_column': info['key'], 'delimiter': info['delimiter']}
    if channel:
        extra['channel'] = {'id': channel.get('id'), 'field': channel.get('field'),
                            'note': '' if (channel.get('spec') or {}).get('status') == 'verified'
                            else 'unverified limit', 'per_string': True}
    return issues, _hub_stats(_make_stats(issues, inf, st, 'csv', extra))


def lint_file(path, profile=None, fmt=None, channel=None, max_words=None, md=False, settings=None,
              csv_columns=None, csv_key=None, facts=None):
    """Read a file, pick its kind from the extension and check it."""
    text = read_text(path)
    kind = detect_kind(path, md)
    if kind == 'locale':
        return lint_locale(text, path, profile, fmt, channel, max_words, settings, facts=facts)
    if kind == 'csv':
        return lint_csv(text, path, profile, fmt, channel, max_words, settings, csv_columns, csv_key, md,
                        facts=facts)
    return lint(text, profile=profile, fmt=fmt, channel=channel, max_words=max_words, kind=kind,
                settings=settings, facts=facts)


def readability(text, md=False):
    """Words, sentences, syllables, FRE and FKGL of a text (code and URLs masked)."""
    kind = 'md' if md else 'text'
    t = clean_text(text or '')
    st = resolve_settings({})
    _issues, info = _check(t, LF.mask_prose(t, kind), st, 'string', kind=kind)
    return {'words': info['words'], 'sentences': len(info['lens']), 'syllables': info['syllables'],
            'fre': info['fre'], 'fkgl': info['fkgl']}


# ---------------------------------------------------------------- mechanical fixes
_FIX_DOUBLE = re.compile(r"(?<=[.?!:]) {2,}(?=[^\s|])")
_FIX_DASH_CLOSED = re.compile(r"(?<=\S)[ \t]+—[ \t]+(?=\S)|(?<=\w) -- (?=\w)|(?<=\w)--(?=\w)"
                              r"|(?<=[A-Za-z]) - (?=[A-Za-z])")
_FIX_DASH_AP = re.compile(r"(?<=\S)—(?=\S)|(?<=\w) -- (?=\w)|(?<=\w)--(?=\w)|(?<=[A-Za-z]) - (?=[A-Za-z])")
_FIX_HEAD = re.compile(r"^([ \t]{0,3}#{1,6}[ \t]+\S.*?)(?<![.:])([.:])([ \t]*)$")


def _fix_spans(text, kind):
    spans = [(a, b) for a, b, _ in protected_spans(text, kind)]
    spans += [(m.start(), m.end()) for m in LF.PLACEHOLDER.finditer(text)]
    return _merge_spans(spans)


def _sub_unprotected(rx, repl, text, kind):
    spans = _fix_spans(text, kind)
    starts = [a for a, _ in spans]

    def rep(m):
        if _in_spans(m.start(), spans, starts) or (m.end() > m.start() and _in_spans(m.end() - 1, spans, starts)):
            return m.group(0)
        return repl(m) if callable(repl) else repl
    return rx.sub(rep, text)


def _quote_counts(text, kind):
    spans = _fix_spans(text, kind)
    starts = [a for a, _ in spans]
    s = sum(1 for m in re.finditer('["\']', text) if not _in_spans(m.start(), spans, starts))
    c = sum(1 for m in re.finditer('[“”‘’]', text) if not _in_spans(m.start(), spans, starts))
    return s, c


def _fix_quotes(text, kind):
    s, c = _quote_counts(text, kind)
    if not (s and c):
        return text
    if s > c:
        tr = {'“': '"', '”': '"', '‘': "'", '’': "'"}
        return _sub_unprotected(re.compile('[“”‘’]'), lambda m: tr[m.group(0)], text, kind)

    def curl(m):
        q = m.group(0)
        prev = m.string[m.start() - 1] if m.start() > 0 else ' '
        opening = prev.isspace() or prev in '([{—–-/' + MASK + BLOCK
        if q == '"':
            return '“' if opening else '”'
        return '‘' if opening else '’'
    return _sub_unprotected(re.compile('["\']'), curl, text, kind)


def _fix_spelling(text, kind, mode):
    if not mode:
        return text
    lines = text.split('\n')
    L = _Lines(text)

    def rep(m):
        w = m.group(0)
        if w.lower() not in SPELLING_FORMS:
            return w
        ln, col = L.pos(m.start())
        if w[:1].isupper() and not _sentence_initial(lines[ln - 1], col - 1):
            return w
        tgt = _spell_target(w, mode)
        return _match_case(w, tgt) if tgt else w
    return _sub_unprotected(_ALPHA_RUN, rep, text, kind)


def _fix_headings(text, kind):
    if kind != 'md':
        return text
    spans = _fix_spans(text, kind)
    starts = [a for a, _ in spans]
    out, pos = [], 0
    for ln in text.split('\n'):
        cr = ln.endswith('\r')
        body = ln[:-1] if cr else ln
        m = _FIX_HEAD.match(body)
        if m and not _in_spans(pos + m.start(2), spans, starts) and not _in_spans(pos, spans, starts):
            body = m.group(1) + m.group(3)
        out.append(body + ('\r' if cr else ''))
        pos += len(ln) + 1
    return '\n'.join(out)


def fix_text(text, kind=None, profile=None, settings=None):
    """Mechanical, idempotent fixes. Keeps CRLF; never touches code, URLs, placeholders, tags or
    lint-ignore blocks. (fixed text, changed line count). Unchanged for locale and CSV."""
    kind = kind or 'text'
    if kind in ('locale', 'csv'):
        return text, 0
    text = text.replace(LF.BOM, '')
    st = settings or resolve_settings(profile or {})
    new = _sub_unprotected(_FIX_DOUBLE, ' ', text, kind)
    if st.get('house_style') == 'ap':
        new = _sub_unprotected(_FIX_DASH_AP, ' — ', new, kind)
    else:
        new = _sub_unprotected(_FIX_DASH_CLOSED, '—', new, kind)
    new = _fix_headings(new, kind)
    new = _fix_quotes(new, kind)
    new = _fix_spelling(new, kind, st.get('spelling'))
    old_l, new_l = text.split('\n'), new.split('\n')
    n = sum(1 for x, y in zip(old_l, new_l) if x != y) + abs(len(old_l) - len(new_l))
    return new, n


# ---------------------------------------------------------------- command line
def print_rules(as_json=False, out=None):
    out = out or sys.stdout
    rows = _HUB.rules_rows('en', rule_list()) if _HUB is not None else rule_list()
    if as_json:
        out.write(json.dumps(rules_json(), ensure_ascii=False, indent=1) + '\n')
        return
    out.write('# Rules (%d)\n' % len(rows))
    for r in rows:
        out.write('%-8s %-24s %-12s %s\n' % (r['severity'], r['id'], r['ref'], r['description']))
    out.write('\n# Formats (--format); a format default only makes limits stricter; the rest comes from the '
              'profile or the dials (sentence cap 25)\n')
    for k in FORMAT_IDS:
        d = EN_FORMAT_DEFAULTS[k]
        lim = ' '.join('%s=%s' % (x, d[x]) for x in ('max_words', 'emoji_max', 'exclaim_max') if x in d)
        out.write('%-9s %-40s %s\n' % (k, lim or '-', d.get('note', '')))
    out.write('\nPrecedence: --max-words > profile.formats[format] (after by_lang.en) > format (stricter only) > '
              'profile > dial\nIgnored: lines between <!-- lint-ignore --> and <!-- /lint-ignore --> (each on its '
              'own line), code blocks, inline code\n')


def rules_json():
    rows = _HUB.rules_rows('en', rule_list()) if _HUB is not None else rule_list()
    return {'version': 2, 'tool_version': __version__, 'rules': rows, 'lexicon': LEXICON,
            'jargon': JARGON_EN, 'formats': dict((k, EN_FORMAT_DEFAULTS[k]) for k in FORMAT_IDS)}


def _err(msg, prog='lint_en'):
    try:
        sys.stderr.write('%s: %s\n' % (prog, msg))
        sys.stderr.flush()
    except Exception:
        pass


def _setup_stdio():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8')
        except Exception:
            pass


def build_parser(prog='lint_en', with_lang=False, description=None):
    ap = argparse.ArgumentParser(prog=prog, description=description or
                                 'Whalory %s copy checker for English' % __version__)
    ap.add_argument('paths', nargs='*', help='file, folder (recursive), glob such as "posts/*.txt", or - for stdin')
    ap.add_argument('--text', action='append', metavar='TEXT', help='short text instead of a file; repeatable')
    ap.add_argument('--profile', help="profile JSON or Markdown, bare name (whalory), or 'auto'")
    ap.add_argument('--format', dest='fmt', metavar='ID', help='text format: %s' % ', '.join(FORMAT_IDS))
    ap.add_argument('--channel', metavar='ID[.FIELD]', help='channel limit from data/channels')
    ap.add_argument('--channels-dir', metavar='DIR', help='another folder of channel data')
    ap.add_argument('--md', action='store_true', help='input is Markdown; code and front matter are skipped')
    ap.add_argument('--csv-columns', metavar='COLS', help='CSV/TSV: columns to check, comma-separated')
    ap.add_argument('--csv-key', metavar='COL', help='CSV/TSV: id column for "row n/<id>/<column>" (default sku, id)')
    ap.add_argument('--json', action='store_true', help='JSON output (version 2)')
    ap.add_argument('--strict', action='store_true', help='warnings also give exit code 1')
    ap.add_argument('--max-words', type=int, help='sentence cap; beats everything else')
    ap.add_argument('--rules', action='store_true', help='list all rules and formats')
    ap.add_argument('--fix', action='store_true', help='mechanical fixes; output in <name>.fixed.<ext>')
    ap.add_argument('--write', action='store_true', help='with --fix, fix the file in place')
    ap.add_argument('--no-overlay', action='store_true',
                    help='built-in rules only, without the signed Whalory Hub updates (as WHALORY_HUB_OVERLAY=0)')
    ap.add_argument('--version', action='version', version='%s %s' % (prog, __version__))
    ap.add_argument('--variant', metavar='BCP47', help='English variant: %s' % ', '.join(VARIANTS))
    ap.add_argument('--house-style', dest='house_style', metavar='ID', help='house style: %s' % ', '.join(HOUSE_STYLES))
    ap.add_argument('--facts', metavar='PATH', help='brief or source text; facts missing from it are flagged')
    if with_lang:
        ap.add_argument('--lang', choices=('auto', 'fa', 'en'), default=None, help='force a language (default auto)')
        ap.add_argument('--fa-only', action='store_true', help='same as --lang fa')
        ap.add_argument('--en-only', action='store_true', help='same as --lang en')
    return ap


def to_json_issue(x):
    return {'line': x['line'] or None, 'col': x['col'] or None, 'key': x.get('key'),
            'rule': x['code'], 'severity': x['level'], 'message': x['message'], 'excerpt': x['text']}


def load_profile_any(spec):
    """Profile loader for the CLI: the forms of lint.load_profile."""
    import lint as _dispatch        # noqa: E402 (lazy: lint imports this module)
    return _dispatch.load_profile(spec)


def _read_facts(path):
    if not path:
        return None
    return _Facts(read_text(path))


def print_text_report(report, profile, settings, channel, out=None, lang_label=None):
    out = out or sys.stdout
    if profile:
        out.write('Profile: %s  (%s)\n' % (profile.get('name', ''), profile.get('_path', '')))
    if settings.get('format'):
        out.write('Format: %s  (sentence cap %s, emoji %s, exclamation marks %s)\n'
                  % (settings['format'], settings['max_words'], settings['emoji_max'], settings['exclaim_max']))
    if channel:
        sp = channel.get('spec') or {}
        out.write('Channel: %s%s  (%s)%s\n' % (channel['id'], '.' + channel['field'] if channel['field'] else '',
                                             channel.get('name_en') or channel.get('name', ''),
                                             '' if sp.get('status') == 'verified' else '  unverified limit'))
    if profile or settings.get('format') or channel:
        out.write('\n')
    for r in report:
        if r.get('error'):
            continue
        for x in r['issues']:
            if x.get('key'):
                where = '%s#%s' % (r['path'], x['key'])
            elif x['line']:
                where = '%s:%d:%d' % (r['path'], x['line'], x['col'])
            else:
                where = r['path']
            tail = '  "%s"' % x['text'] if x['text'] else ''
            out.write('%s  %-7s %-22s %s%s\n' % (where, x['level'], x['code'], x['message'], tail))
        s = r['stats']
        head = '%s: ' % r['path']
        if r.get('lang') and lang_label:
            head += '[%s] ' % r['lang']
        if s.get('kind') == 'locale':
            head += '%d strings, ' % s.get('strings', 0)
        elif s.get('kind') == 'csv':
            head += '%d rows (%d flagged), %d cells in %s%s; ' % (
                s.get('rows', 0), s.get('rows_flagged', 0), s.get('cells', 0), ', '.join(s.get('columns') or []),
                ' (key: %s)' % s['key_column'] if s.get('key_column') else ' (no key column)')
        rd = s.get('readability') or {}
        rtxt = ''
        if rd.get('fkgl') is not None:
            rtxt = ', grade %s, reading ease %s' % (rd['fkgl'], rd['fre'])
        out.write('%s%d sentences, %s words on average, cap %s%s · %d errors · %d warnings\n'
                  % (head, s.get('sentences', 0), s.get('avg_words', 0), s.get('max_words'), rtxt,
                     s.get('errors', 0), s.get('warnings', 0)))
        ch = s.get('channel')
        if ch and not ch.get('per_string'):
            if ch.get('unit') == 'segment':
                out.write('  channel %s: %d characters, %d SMS segments (%s; %d in one, %d per part)%s\n'
                          % (ch['id'], ch['chars'], ch.get('segments', 0), ch.get('encoding', ''),
                             ch.get('single', 0), ch.get('per_part', 0), ' · ' + ch['note'] if ch.get('note') else ''))
            else:
                out.write('  channel %s: %d %s of %s%s%s\n'
                          % (ch['id'], ch.get('count', ch['chars']), ch.get('unit', 'char'),
                             ch.get('max_chars') if ch.get('max_chars') is not None else 'unknown',
                             ' · %d items' % ch['items'] if 'items' in ch else '',
                             ' · ' + ch['note'] if ch.get('note') else ''))
        out.write('\n')


def main(argv=None):
    _setup_stdio()
    ap = build_parser()
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0) if e.code in (0, None) else 2
    if _HUB is not None:
        _HUB.set_cli_disabled(a.no_overlay)
    if a.rules:
        print_rules(a.json)
        return 0
    paths = iter_paths(a.paths)
    if not paths and not a.text:
        ap.print_usage(sys.stderr)
        _err('give at least one file, folder, - or --text.')
        return 2
    if a.write and not a.fix:
        _err('--write only works with --fix; ignored.')
    profile = load_profile_any(a.profile) if a.profile else {}
    if a.profile == 'auto' and not profile:
        _err('no voice.json found here or above; checked without a profile.')
    channel = LF.resolve_channel(a.channel, a.channels_dir) if a.channel else None
    for w in (channel or {}).get('load_warnings', []):
        _err(w)
    fmt = a.fmt or (channel or {}).get('format_id') or None
    if a.fmt and a.fmt not in EN_FORMAT_DEFAULTS and a.fmt not in (profile.get('formats') or {}):
        raise UserError('unknown format "%s". Formats: %s' % (a.fmt, ', '.join(FORMAT_IDS)))
    settings = resolve_settings(profile, fmt, a.max_words, variant=a.variant, house_style=a.house_style)
    facts = _read_facts(a.facts)
    inputs = [('<text>', None, t) for t in (a.text or [])] + [(p, p, None) for p in paths]
    report, any_bad, input_errors, csv_seen = [], False, 0, False
    say = _err if a.json else (lambda m: sys.stdout.write(m + '\n'))
    for label, path, inline in inputs:
        try:
            meta = {}
            if path is None:
                text, kind = inline, ('md' if a.md else 'text')
            elif path == '-':
                text, kind, label = read_text('-'), ('md' if a.md else 'text'), '-'
                if a.csv_columns or a.csv_key:
                    kind = 'csv'
            else:
                text, meta = read_text(path, with_meta=True)
                kind = detect_kind(path, a.md)
            fixed_lines = None
            if a.fix:
                if kind in ('locale', 'csv'):
                    _err('--fix does not change %s files; %s was left as is. Fix the values by hand so keys and '
                         'placeholders stay intact.' % ('locale' if kind == 'locale' else 'CSV/TSV', label))
                else:
                    fixed, fixed_lines = fix_text(text, kind=kind, settings=settings)
                    if path in (None, '-'):
                        sys.stdout.flush()
                        out = getattr(sys.stdout, 'buffer', None)
                        if out is not None:
                            out.write(fixed.encode('utf-8'))
                            out.flush()
                        else:
                            sys.stdout.write(fixed)
                        continue
                    target = path if a.write else '%s.fixed%s' % os.path.splitext(path)
                    write_text(target, fixed, meta)
                    say('fixed: %d lines changed -> %s' % (fixed_lines, target))
                    text = fixed
            if kind == 'locale':
                issues, stats = lint_locale(text, path or '', settings=settings, channel=channel, facts=facts)
            elif kind == 'csv':
                issues, stats = lint_csv(text, path if path not in (None, '-') else '', settings=settings,
                                         channel=channel, columns=a.csv_columns, key=a.csv_key, md=a.md, facts=facts)
                csv_seen = True
            else:
                issues, stats = lint(text, kind=kind, settings=settings, channel=channel, facts=facts)
            if fixed_lines is not None:
                stats['fixed_lines'] = fixed_lines
            report.append({'path': label, 'lang': 'en', 'issues': issues, 'stats': stats})
            if stats['errors'] or (a.strict and stats['warnings']):
                any_bad = True
        except UserError as e:
            _err(str(e))
            input_errors += 1
            report.append({'path': label, 'lang': 'en', 'issues': [], 'stats': {}, 'error': str(e)})
    if (a.csv_columns or a.csv_key) and not csv_seen and not input_errors:
        _err('--csv-columns and --csv-key only apply to CSV or TSV files; ignored.')
    if a.json:
        files = []
        for r in report:
            f = {'path': r['path'], 'lang': r['lang'], 'issues': [to_json_issue(x) for x in r['issues']],
                 'stats': r['stats']}
            if r.get('error'):
                f['error'] = r['error']
            files.append(f)
        sys.stdout.write(json.dumps({'version': 2, 'files': files,
                                     'summary': {'errors': sum(r['stats'].get('errors', 0) for r in report),
                                                 'warnings': sum(r['stats'].get('warnings', 0) for r in report)}},
                                    ensure_ascii=False, indent=1) + '\n')
    else:
        print_text_report(report, profile, settings, channel)
    if input_errors:
        return 2
    return 1 if any_bad else 0


def run(argv=None, prog='lint_en'):
    """CLI with friendly errors; returns the exit code and never calls sys.exit."""
    try:
        return main(argv)
    except UserError as e:
        _err(str(e), prog)
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
        _err('unexpected error: %s: %s. Set WHALORY_DEBUG=1 and run it again for details.' % (type(e).__name__, e),
             prog)
        return 2


if _HUB is not None:
    _HUB.register('en', sys.modules[__name__])

if __name__ == '__main__':
    sys.exit(run())
