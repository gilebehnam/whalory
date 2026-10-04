#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint_fa: بازبینِ خودکارِ والوری برای متنِ فارسی.

چیزهایی را پیدا می‌کند که با چشم راحت از دست می‌روند: نویسه‌ی عربی، خطِ تیره
وسطِ جمله، نیم‌فاصله‌ی افتاده، الگوهای متنِ ماشینی، واژه‌ی اداری، لحنِ مخلوط،
جمله‌ی بیش از حد بلند و علامت‌گذاریِ پرسروصدا. با پروفایلِ صدا (نسخه‌ی ۱ و ۲)،
املای نامِ برند، واژه‌های ممنوع و «نگو»، لحن، خطاب (تو/شما)، سقفِ طولِ جمله،
سقفِ ایموجی، قالبِ متن (--format) و سقفِ نویسه‌ی کانال (--channel) را هم می‌سنجد.
فایلِ locale (json، po، arb، xliff، strings، strings.xml) را هم می‌خواند و فقط
مقدارهای فارسی را می‌سنجد؛ کلید و جای‌نگهدار دست نمی‌خورد.

در csv و tsv (کاتالوگِ انبوه) هر خانه‌ی ستون‌های متنی جدا سنجیده می‌شود و مسئله با
کلیدِ «row n/کد/ستون» گزارش می‌شود؛ ستون‌های دیگر خوانده نمی‌شوند.

اسکریپت جای خواندن را نمی‌گیرد. قصه، جزئیات و واقعی بودن را فقط آدم می‌سنجد.

استفاده:
    python lint_fa.py draft.txt
    python lint_fa.py draft.txt --profile profiles/whalory.json
    python lint_fa.py "posts/*.txt" content/ --profile auto --json
    python lint_fa.py --text "متنِ کوتاه" --format ui
    python lint_fa.py caption.txt --channel instagram.caption
    python lint_fa.py src/locales/fa.json --format ui
    python lint_fa.py catalog.csv --csv-columns title_new,desc_new --csv-key sku
    cat draft.txt | python lint_fa.py - --profile VOICE.md
    python lint_fa.py draft.txt --fix            # خروجی در draft.fixed.txt
    python lint_fa.py draft.txt --fix --write    # اصلاح در همان فایل؛ CRLF و BOM می‌مانند
    python lint_fa.py --rules
    python lint_fa.py --version

خروج: ۰ اگر خطا نبود، ۱ اگر حداقل یک خطا بود، ۲ اگر ورودی یا پروفایل خوانده نشد.
هشدار خروج را عوض نمی‌کند، مگر با --strict.

نمونه‌ی «نادرست»ِ عمدی در فایلِ آموزشی را میانِ دو سطرِ جدا بگذار تا نه سنجیده شود و
نه با --fix عوض شود:
    <!-- lint-ignore -->
    …
    <!-- /lint-ignore -->
کدِ درون‌خطی (`…`) و بلوکِ کد هم سنجیده نمی‌شوند. بندِ فهرست و خانه‌ی جدول جمله‌اند.
"""
from __future__ import print_function

import sys

if sys.version_info < (3, 8):  # پیش از هر چیزِ دیگر، تا پیام خوانا باشد
    sys.stderr.write('lint_fa needs Python 3.8 or newer (found %s). '
                     'Install a newer Python and run it again.\n' % sys.version.split()[0])
    sys.exit(2)

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts: a skill or plugin folder may be read-only

import argparse  # noqa: E402
import bisect  # noqa: E402
import codecs  # noqa: E402
import csv  # noqa: E402
import functools  # noqa: E402
import glob  # noqa: E402
import html  # noqa: E402
import io  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import unicodedata  # noqa: E402
import voice_profile as VP

try:  # لایه‌ی هاب (spec 5.9)؛ بی آن قاعده‌های درونی مثلِ همیشه کار می‌کنند
    import hub_overlay as _HUB  # noqa: E402
except Exception:  # noqa: BLE001
    _HUB = None

__version__ = '3.2.1'

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
CHANNELS_DIR = os.path.join(SKILL_ROOT, 'data', 'channels')

# ---------------------------------------------------------------- نویسه‌ها
# U+FEFF (BOM) عمداً بیرون است: هرگز حرف شمرده نمی‌شود.
FA = '\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFE'
ZWNJ = '\u200c'
W = '[%s%s]' % (FA, ZWNJ)
# فقط حرف (با اِعراب)، بی رقم و بی نشانه‌ی فارسی
FA_LETTERS = '\u0620-\u065F\u066E-\u06D3\u06D5-\u06EF\u06FA-\u06FF\uFB50-\uFDFF\uFE70-\uFEFE'
L = '[%s]' % FA_LETTERS
LZ = '[%s%s]' % (FA_LETTERS, ZWNJ)
HAS_FA = re.compile(L)
DIGITS = '0123456789\u06F0\u06F1\u06F2\u06F3\u06F4\u06F5\u06F6\u06F7\u06F8\u06F9' \
         '\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669'
BOM = '\ufeff'
MASK = '\ue000'    # جای کد، برچسب، نشانی و جای‌نگهدار؛ نه حرف است، نه فاصله
BLOCK = '\ue001'   # مرزِ بلوک (برچسبِ بلوکیِ html، شاخه‌ی ICU)؛ جمله را می‌شکند
HARAKAT = '\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653\u0654\u0655\u0670'

ERROR, WARN = 'error', 'warning'


class UserError(Exception):
    """خطایی که کاربر باید ببیند: بی‌traceback و با خروجِ ۲."""


# ---------------------------------------------------------------- ایموجی
# فقط نویسه‌هایی که به‌طورِ پیش‌فرض ایموجی نمایش داده می‌شوند، یا نویسه‌ی متنی
# که پشتش U+FE0F آمده. ★ ☆ ✓ ✔ ♪ → • و مانندِ این‌ها ایموجی نیستند.
_EMO_PRES = ('\u231A\u231B\u23E9-\u23EC\u23F0\u23F3\u25FD\u25FE\u2614\u2615\u2648-\u2653\u267F\u2693'
             '\u26A1\u26AA\u26AB\u26BD\u26BE\u26C4\u26C5\u26CE\u26D4\u26EA\u26F2\u26F3\u26F5\u26FA\u26FD'
             '\u2705\u270A\u270B\u2728\u274C\u274E\u2753-\u2755\u2757\u2764\u2795-\u2797\u27B0\u27BF'
             '\u2B1B\u2B1C\u2B50\u2B55'
             '\U0001F004\U0001F0CF\U0001F18E\U0001F191-\U0001F19A\U0001F201\U0001F21A\U0001F22F'
             '\U0001F232-\U0001F236\U0001F238-\U0001F23A\U0001F250\U0001F251\U0001F300-\U0001F64F'
             '\U0001F680-\U0001F6FF\U0001F7E0-\U0001F7EB\U0001F7F0\U0001F90C-\U0001F9FF'
             '\U0001FA70-\U0001FAFF')
_EMO_TEXT = ('\u00A9\u00AE\u203C\u2049\u2122\u2139\u2194-\u2199\u21A9\u21AA\u2328\u23CF\u23ED-\u23EF'
             '\u23F1\u23F2\u23F8-\u23FA\u24C2\u25AA\u25AB\u25B6\u25C0\u25FB\u25FC\u2600-\u27BF\u2934'
             '\u2935\u2B05-\u2B07\u3030\u303D\u3297\u3299\U0001F170-\U0001F189')
_EMO_ONE = '(?:[%s]|[%s]\uFE0F)' % (_EMO_PRES, _EMO_TEXT)
_EMO_ZWJ_PART = '(?:[%s]|[%s]\uFE0F?)' % (_EMO_PRES, _EMO_TEXT)
_EMO_MOD = '(?:\uFE0F|[\U0001F3FB-\U0001F3FF])?'
EMOJI = re.compile(
    '[\U0001F1E6-\U0001F1FF]{2}'                    # پرچم
    '|[0-9#*]\uFE0F?\u20E3'                         # کلیدِ عددی 1️⃣
    '|%s%s(?:[\U000E0020-\U000E007F]+)?(?:\u200D%s%s)*' % (_EMO_ONE, _EMO_MOD, _EMO_ZWJ_PART, _EMO_MOD))

# ---------------------------------------------------------------- قاعده‌ها
# واژه‌ی دنباله‌ی «، نه …»: بی‌فاصله و بی‌نشانه‌ی پایانِ جمله یا خانه
_NA_TOKEN = r'[^\s.!؟?؛;،,…»)|%s]+' % BLOCK
# فعلِ ساختِ «اقدام»: دوم‌شخص، «نمودن» و مجهول («اقدام کند» در خبر فعلِ عادی است)
_EQDAM_VERB = r'(?:ب?کنید|ب?کنین|ب?نمایید|نمایند|نماید|نماییم|ب?فرمایید|شود|گردد)'

# (کد، سطح، الگو، پیام). اگر گروهِ «at» باشد، ستون از همان‌جا حساب می‌شود.
PATTERNS = [
    # نویسه
    ('arabic-yeh', ERROR, re.compile('[\u064A\u0649]'), '«ي» یا «ى» عربی؛ «ی» فارسی بنویس'),
    ('arabic-kaf', ERROR, re.compile('\u0643'), '«ك» عربی؛ «ک» فارسی بنویس'),

    # خطِ تیره (بازه‌ی عددی مثلِ ۱۰–۲۰ و خطِ تیره‌ی سرِ سطر معاف است)
    ('dash', ERROR, re.compile(r'[\u2014\u2013]'),
     'خطِ تیره وسطِ جمله؛ جایش «،» یا «؛»'),
    ('hyphen-dash', ERROR, re.compile(r'(?<=[%s»)]) - (?=[%s«(])' % (FA_LETTERS, FA_LETTERS)),
     'خطِ فاصله‌دار به‌جای ویرگول؛ جایش «،» یا «؛»'),

    # نیم‌فاصله
    ('zwnj-mi', WARN, re.compile(r'(?<!%s)(ن?می) (?=[%s]{2,})' % (W, FA)),
     'پیشوندِ «می/نمی» با فاصله‌ی کامل؛ نیم‌فاصله بگذار'),
    ('zwnj-mi-joined', WARN,
     re.compile(r'(?<!%s)(ن?می)(?=(شه|شود|کنه|کند|کنین|کنید|خوام|خواهم|ره|رود|گه|گوید|دونم|دانم|تونی|توانی|تونین|تونید|پزن|پزند|شن|شوند)(?!%s))' % (W, W)),
     'پیشوندِ «می/نمی» چسبیده؛ نیم‌فاصله بگذار'),
    ('zwnj-ha', WARN, re.compile(r'(?<=%s) (ها|های|هایی|تر|ترین)(?!%s)' % (W, W)),
     'پسوندِ «ها/تر/ترین» با فاصله‌ی کامل؛ نیم‌فاصله بگذار'),
    ('ezafe-he', WARN, re.compile(r'(?<=[%s]ه) ی(?!%s)' % (FA, W)),
     'اضافه بعد از «ه» جدا نوشته شده؛ «ه‌ی» بنویس'),

    # تقابل و قالب‌های ماشینی
    # دو نیمه در یک جمله و با یک شخص: «نیستیم، … هستیم»، «نیست، … است»
    ('neg-contrast', ERROR, re.compile(
        r'(?<!%s)نیست(?:(?P<p1>یم)|(?P<p3>ند)|(?P<p2>ید))?\s*[،,؛]\s*(?P<gap>[^.!؟?؛\n]{0,60}?)'
        r'(?(p1)(?:(?<!%s)هستیم|(?<=[%s])\u200cایم)'
        r'|(?(p3)(?:(?<!%s)هستند|(?<=[%s])\u200cاند)'
        r'|(?(p2)(?:(?<!%s)هستید|(?<=[%s])\u200cاید)|(?<!%s)(?:است|هست))))(?!%s)'
        % (LZ, LZ, FA_LETTERS, LZ, FA_LETTERS, LZ, FA_LETTERS, LZ, LZ)),
     'تقابلِ منفی «X نیستیم، Y هستیم»'),
    # «X، نه Y» (تقابلِ بلاغی): «، نه» یا «؛ نه» و ۱ تا ۴ واژه تا پایانِ جمله یا «،»
    ('na-contrast', WARN, re.compile(
        r'[،؛,;][ \t]*(?P<at>نه)[ \t]+(?P<tail>%s(?:[ \t]+%s){0,3})'
        r'(?=[ \t]*(?:[.!؟?؛;،,…»)|%s]|$))' % (_NA_TOKEN, _NA_TOKEN, BLOCK)),
     'تقابلِ «X، نه Y»؛ نیمه‌ی منفی را بردار و خودِ X را با جزئیات بگو'),
    ('just-not', ERROR, re.compile(r'فقط\s+یک\s+[^.،؛]{1,30}\s+نیست'),
     'تقابلِ «فقط یک... نیست»'),
    ('not-only', ERROR, re.compile(r'نه\s+(فقط|تنها)[^.]{0,80}بلکه'),
     'قالبِ «نه فقط... بلکه»'),
    ('beyond', ERROR, re.compile(r'فراتر\s+از\s+یک'), 'قالبِ «فراتر از یک»'),
    ('problem-solution', ERROR,
     re.compile(r'(خسته\s+شده‌?\s?اید|دیگر\s+نگران\s+\S+\s+نباشید|راه[‌\s]?حلِ?\s+(شما|ما)ست)'),
     'قالبِ مسئله و راه‌حل'),
    ('journey', ERROR, re.compile(r'سفری\s+به\s+(دلِ?|قلبِ?|دنیای)'),
     'استعاره‌ی کلیشه «سفری به دلِ...»'),
    ('welcome-world', ERROR, re.compile(
        r'به\s+دنیای\s+[^.؟!?\n]{1,40}?خوش[\s\u200c]*(?:آمدید|آمدی|آمدین|اومدین|اومدی|اومدید)'
        r'|قدم\s+(?:به|در)\s+دنیای\s+[^.؟!?\n]{1,30}?(?:بگذارید|بذارید|بزارید|بگذارین|بذارین|بگذار|بذار|بزار)(?!%s)'
        r'|وارد\s+دنیای\s+[^.؟!?\n]{1,30}?(?:شوید|بشوید|بشید|بشین|بشو|شو)(?!%s)' % (LZ, LZ)),
     'کلیشه‌ی «به دنیای... خوش آمدید»'),
    ('world-today', ERROR, re.compile(r'(در\s+)?دنیای\s+(پرشتابِ?\s+)?امروز'),
     'شروعِ کلیشه «دنیای امروز»'),
    ('unique-exp', ERROR, re.compile(r'تجربه‌?\s?ای\s+(بی‌?\s?نظیر|منحصر\s?به\s?فرد|فراموش‌?\s?نشدنی)'),
     'کلیشه «تجربه‌ای بی‌نظیر»'),
    ('we-believe', ERROR,
     re.compile(r'(ما\s+)?(معتقدیم|بر\s+این\s+باوریم|افتخار\s+می‌?\s?کنیم)'),
     'راوی خودش را وسط کشیده'),
    ('self-ref', ERROR,
     re.compile(r'(با\s+ما\s+همراه\s+باشید|در\s+این\s+(مقاله|متن|نوشته)\s+(خواهیم\s+دید|می‌?\s?خوانید))'),
     'اشاره‌ی متن به خودش'),
    ('moral-close', WARN, re.compile(r'(و\s+این\s+یعنی|در\s+نهایت،|به\s+طور\s+خلاصه)'),
     'جمع‌بندی یا نتیجه‌گیریِ اخلاقی'),

    # نشانه‌های تازه‌ی متنِ ماشینی (references/fa/ai-tells.md)
    ('did-you-know', ERROR, re.compile(
        r'آیا\s+(?:شما\s+)?می[\u200c ]?(?:دانستید|دانستی|دانستین|دونستید|دونستین|دونستی)(?!%s)'
        r'|(?:^|(?<=[.!؟?]))\s*(?:شما\s+)?می[\u200c ]?(?:دونستی|دونستین|دانستید|دانستی)\s+که(?!%s)'
        % (LZ, LZ)),
     'شروعِ کلیشه‌ی «آیا می‌دانستید»؛ خودِ واقعیت را بگو'),
    ('lets', WARN, re.compile(
        r'(?:^|(?<=[.!؟?؛:…»]))[ \t]*(?:[-*•>]+[ \t]*)?(?:پس[ \t]+|حالا[ \t]+)?(?P<at>بیایید|بیاین)(?!%s)' % LZ),
     'شروع با «بیایید»؛ مستقیم برو سرِ حرف'),
    ('nowadays', WARN, re.compile(
        r'(?<!%s)امروزه(?!%s)|در\s+عصرِ?\s+(?:حاضر|کنونی)(?!%s)' % (LZ, LZ, LZ)),
     'کلیشه‌ی «امروزه» / «در عصرِ حاضر»؛ زمان را مشخص کن یا حذف کن'),
    ('no-secret', ERROR, re.compile(r'بر\s+(?:کسی|هیچ[\u200c ]?کس|هیچ\s+کس)\s+پوشیده\s+نیست'),
     'کلیشه‌ی «بر کسی پوشیده نیست»'),
    ('golden-tip', WARN, re.compile(
        r'نکته(?:[\u200c ]?ی|\u0654)?\s+طلایی|نکات\s+طلایی'
        r'|نکته(?:[\u200c ]?ی|\u0654)?\s+(?:مهم|کلیدی)\s+(?:این\s+است|اینجاست|این\u200cجاست|اینه)\s+که'),
     'کلیشه‌ی «نکته‌ی طلایی» / «نکته‌ی مهم این است که»؛ خودِ نکته را بگو'),
    ('final-word', WARN, re.compile(r'سخنِ?\s+پایانی|کلامِ?\s+آخر(?!%s)' % LZ),
     'تیتر یا پایانِ کلیشه‌ی «سخنِ پایانی» / «کلامِ آخر»'),
    ('hope-helpful', ERROR, re.compile(
        r'امیدوار(?:م|یم)[^.؟!?\n]{0,60}?(?:مفید\s+(?:بوده|واقع\s+شده)\s+باش(?:د|ه)'
        r'|لذت\s+برده\s+باشی(?:د|ن)|به\s+کارتان\s+آمده\s+باشد|به\s+کارتون\s+اومده\s+باشه)'),
     'پایانِ کلیشه‌ی «امیدوارم مفید بوده باشد»'),

    # واژه‌ی اداری
    ('admin', ERROR,
     re.compile(r'(?<!%s)(می‌?\s?باشد|می‌?\s?باشند|می‌?\s?گردد|می‌?\s?گردند|گردیده|نمایید|خواهد\s+گردید|اقدام\s+به\s+\S+\s+نمایید)' % W),
     'فعلِ اداری؛ «است»، «می‌شود»، «کنید»'),
    # «جهتِ» فقط وقتی «برای» است (پیش از اسمِ هدف)؛ «جهتِ متن» یعنی سو و درست است
    ('admin-phrase', WARN,
     re.compile(r'(لازم\s+به\s+ذکر\s+است|قابل\s+توجه\s+است|شایان\s+ذکر|در\s+راستای|به\s+منظورِ?|علی‌?\s?رغم|کلیه‌?\s?ی|مذکور'
                r'|(?<!%s)جهتِ?\s+(?:%s)\u0650?(?![%s]))' % (LZ, '|'.join(sorted([
                    'اطلاع', 'اطلاعات', 'آگاهی', 'خرید', 'ثبت', 'ثبت‌نام', 'استفاده', 'دریافت', 'انجام', 'تهیه',
                    'رفاه', 'سهولت', 'ارسال', 'پرداخت', 'بررسی', 'کسب', 'رفع', 'تسریع', 'تکمیل', 'مشاهده',
                    'پیگیری', 'ورود', 'عضویت', 'شرکت', 'حفظ', 'جلوگیری', 'آشنایی', 'تأمین', 'تامین', 'ارائه',
                    'رزرو', 'سفارش', 'تماس', 'همکاری', 'استعلام', 'ارتقا', 'ارتقای', 'افزایش', 'کاهش', 'بهبود',
                    'رعایت', 'حضور', 'اخذ', 'صدور', 'تمدید', 'فعال‌سازی', 'دانلود', 'راهنمایی', 'کمک', 'حمایت',
                    'ایجاد', 'توسعه', 'تحقق', 'نیل', 'رضایت', 'اطمینان', 'برخورداری', 'بهره‌مندی',
                    'واریز', 'بازگشت', 'تحویل', 'نصب', 'راه‌اندازی', 'تنظیم', 'ویرایش', 'حذف', 'لغو', 'انصراف',
                    'بازیابی', 'مطالعه', 'دسترسی', 'پشتیبانی'], key=len, reverse=True)),
                                                        FA_LETTERS)),
     'عبارتِ اداری یا پُرکن'),
    # ساختِ «اقدام»: «اقدام کنید»، «اقدام به … نمایید»، «نسبت به … اقدام». «نمایید» خودش خطای admin است؛
    # این هشدار راهِ درمان را نشان می‌دهد، چون «اقدام کنید» هم هنوز اداری است.
    ('admin-phrase', WARN, re.compile(
        r'(?<!%s)(?:نسبت\s+به\s+(?P<g1>[^.!؟?؛،\n]{1,40}?)\s+اقدام\u0650?(?!%s)'
        r'|اقدام\s+به\s+(?P<g2>[^.!؟?؛،\n]{1,40}?)\s+%s(?!%s)'
        r'|اقدام\s+%s(?!%s))' % (LZ, LZ, _EQDAM_VERB, LZ, _EQDAM_VERB, LZ)),
     'ساختِ اداریِ «اقدام»؛ خودِ فعل را بیاور، مثلِ «تمدید کنید» یا «بخرید»'),


    # غلط‌های رایج؛ references/fa/common-errors.md
    ('tanvin-fa', ERROR,
     re.compile(r'(?<!%s)(گاهاً|گاها|دوماً|سوماً|چهارماً|خواهشاً|ناچاراً|زباناً|جاناً|تلفناً)(?!%s)' % (W, W)),
     'تنوین روی واژه‌ی فارسی؛ «گاهی»، «دوم»، «لطفاً»'),
    ('double-plural', ERROR,
     re.compile(r'(?<!%s)(اخبار|اساتید|مسائل|حقوق|اسناد|اشخاص)‌?ها(?!%s)' % (W, W)),
     'جمعِ دوباره؛ جمعِ عربی «ها» نمی‌گیرد'),
    ('spacing-compound', WARN,
     re.compile(r'(?<!%s)(بعنوان|بخاطر|بنابر این|اینطور|اینطوری|آنطور|همینطور)(?!%s)' % (W, W)),
     'نیم‌فاصله در واژه‌ی مرکب؛ «به‌عنوان»، «به‌خاطر»، «این‌طور»'),
    ('heavy-passive', WARN,
     re.compile(r'(مورد\s+(استفاده|بررسی|توجه|تأیید|تایید)\s+قرار\s+(گرفت|می‌?\s?گیرد|گرفته)|(?<!%s)توسطِ?\s)' % W),
     'ساختِ سنگین؛ «به کار می‌رود»، «بررسی شد»، فاعل را بیاور'),
    ('heavy-prep', WARN,
     re.compile(r'(?<!%s)(بر\s+روی|در\s+رابطه\s+با|درصورتیکه|در\s+صورتی\s?که|ولیکن|مضافاً|کماکان)(?!%s)' % (W, W)),
     'حرف‌اضافه یا پیوندِ سنگین؛ «روی»، «درباره‌ی»، «اگر»'),
    ('latin-question', WARN, re.compile(r'(?<=%s)[ \t]*\?(?![A-Za-z0-9=&])' % L),
     'علامتِ سؤالِ لاتین؛ «؟» بنویس'),
    ('clickbait', ERROR,
     re.compile(r'(باور\s+نمی‌?\s?کنید|رازِ?\s+\S+\s+که|چیزی\s+که\s+هیچ‌?\s?کس\s+به\s+شما\s+نمی‌?\s?گوید|آخرین\s+فرصت)'),
     'تیترِ کنجکاوی‌سازِ توخالی'),
    ('vague-apology', ERROR,
     re.compile(r'(هرگونه|هر\s+گونه)\s+(ناراحتی|مشکل|اختلال|نارضایتی)[^.]{0,20}(احتمالی)?'),
     'عذرخواهیِ مبهم؛ اشتباه را نام ببر'),
    ('link-here', WARN, re.compile(r'\[(اینجا|این‌?\s?جا|کلیک\s+کنید)\]'),
     'متنِ پیوند باید خودش معنا داشته باشد'),

    # متنِ نمایشی که به خواننده‌ی نهایی رسیده
    ('demo-word', WARN, re.compile(
        r'(?<!%s)(?:لورم\s+ایپسوم|[Ll]orem\s+ipsum)'
        r'|(?<!%s)(?:متن|محصول|قیمت|تصویر|عکس|کالا|آیتم|پست|آگهی|صفحه|سفارش|کاربر|نظر|پیام|عنوان'
        r'|توضیح|توضیحات|لینک|شماره|آدرس|ایمیل|نام|محتوا|بنر|فایل)'
        r'(?:\u0650|\u200cی|\u200cهای|\u200cها|های|ها)?\s+(?:نمایشی|آزمایشی|تستی)(?!%s)'
        r'|[(]\s*(?:نمایشی|آزمایشی|تستی)\s*[)]' % (LZ, LZ, L)),
     'متنِ نمایشی/آزمایشی/تستی یا لورم‌ایپسوم در متنِ خواننده‌ی نهایی'),

    # علامت
    ('bang-bang', ERROR, re.compile(r'[!！]{2,}'), 'علامتِ تعجبِ پیاپی'),
    ('ellipsis', WARN, re.compile(r'(\.\.\.|…)'), 'سه‌نقطه در متنِ روایی'),
    ('latin-quote', WARN, re.compile(r'"(?=%s)|(?<=%s)"' % (L, L)),
     'گیومه‌ی لاتین؛ «» بنویس'),
    ('latin-comma', WARN, re.compile(r'(?<=%s)[ \t]*,(?![0-9])' % L), 'ویرگولِ لاتین؛ «،» بنویس'),
    ('latin-semicolon', WARN, re.compile(r'(?<=%s);' % L), 'نقطه‌ویرگولِ لاتین؛ «؛» بنویس'),
    # ویرگولِ پیش از «و»ِ آخرِ فهرست: «الف، ب، و ج» → «الف، ب و ج»
    ('serial-comma', WARN, re.compile(
        r'،[ \t]*(?P<x>[^،,.!؟?؛;\n%s]{1,40}?)[ \t]*(?P<at>،)[ \t]*و(?![%s%s])[ \t]+(?=\S)'
        % (BLOCK, FA_LETTERS, ZWNJ)),
     'ویرگول پیش از «و»ِ آخرِ فهرست؛ فارسی آن را نمی‌گذارد: «الف، ب و ج»'),
    ('space-before-punct', WARN, re.compile(r'(?<=%s) +(?![:;][)(DP])(?:[،؛:؟!]|\.(?!\.))' % W),
     'فاصله پیش از نشانه'),
    ('latin-digit', WARN, re.compile(r'(?<=%s\s)[0-9]+|(?<![0-9])[0-9]+(?=\s%s)' % (W, W)),
     'رقمِ لاتین کنارِ متنِ فارسی؛ رقمِ فارسی بنویس'),
]

LEXICON = {
    'صفتِ بزرگ': ['بی‌نظیر', 'بی نظیر', 'منحصربه‌فرد', 'منحصر به فرد', 'شگفت‌انگیز',
                  'جادویی', 'بی‌همتا', 'بی‌رقیب', 'استثنایی', 'خیره‌کننده', 'بهترین',
                  'مرغوب‌ترین', 'باکیفیت‌ترین'],
    'صفتِ عاطفیِ توخالی': ['دلنشین', 'دل‌انگیز', 'به‌یادماندنی', 'رؤیایی', 'رویایی',
                           'لذت‌بخش'],
    'اصالت‌بازی': ['اصیل', 'اصالت', 'ریشه‌دار', 'کهن'],
    'استعاره‌ی کلیشه': ['غرق شوید', 'کاوش کنید', 'جواهرِ', 'جواهر ', 'گنجینه‌ی',
                        'قلبِ تپنده', 'قلب تپنده'],
    'زبانِ شرکتی': ['پلتفرم', 'اکوسیستم', 'راهکار', 'ارزش‌آفرینی', 'هم‌افزایی',
                    'نوآورانه', 'پیشرو', 'بهینه‌سازی', 'ارتقا'],
    'جزئیاتِ عمومی': ['با دقت و عشق', 'با عشق و دقت', 'با عشق تهیه', 'با دقت تهیه',
                      'هزاران مشتری', 'مشتریان راضی'],
    'پیوندِ پُرکن': ['در واقع', 'به طور کلی', 'به‌طور کلی', 'از سوی دیگر'],
    'دعوتِ کلیشه': ['همین حالا', 'فرصت را از دست ندهید', 'تجربه کنید'],
    'احساسِ جمعی': ['دلِ هر ایرانی', 'دل هر ایرانی', 'همه‌ی ما', 'همه ی ما'],
    'زبانِ خطابِ جمعی': ['مشتریانِ گرامی', 'مشتریان گرامی', 'کاربرانِ گرامی',
                         'کاربران گرامی', 'مخاطبانِ عزیز', 'مخاطبان عزیز',
                         'مشتری گرامی', 'مشتریِ گرامی'],
}

# واژه‌ی فرنگیِ تخصصی؛ فقط وقتی دکمه‌ی jargon پروفایل ۱ یا ۲ است
JARGON = ['کانتنت', 'اینفلوئنسر', 'اینفلوئنسری', 'فیچر', 'آنبوردینگ', 'ترند', 'ترندینگ', 'دیتا',
          'تسک', 'پرزنت', 'کانورژن', 'کانورت', 'انگیجمنت', 'ریچ', 'اسکیل', 'دیپلوی', 'ریلیز',
          'بنچمارک', 'پرفورمنس', 'پرسونا', 'فانل', 'سگمنت', 'تارگت', 'اپتیمایز', 'برندینگ',
          'مارکتینگ', 'بیزینس', 'استوری‌تلینگ', 'کال‌تواکشن', 'یوزر', 'اینسایت']

# «می/نمی» فقط سرِ واژه: «همیشه» محاوره‌ی «میشه» نیست، «نمیشه» هست.
_MI_HEAD = '(?<![%s%s])ن?' % (FA_LETTERS, ZWNJ)
COLLOQ = re.compile(r'(%sمی‌?(?:شه|کنه|خوام|ره|گه|دونم|تونی)\b|کنین\b|بکنین\b|(?<!%s)اون(?!%s)|(?<!%s)اگه(?!%s)|خونه|زمستون|(?<!%s)رو(?!%s)|خوشمزه‌?ست)'
                    % (_MI_HEAD, W, W, W, W, W, W))
FORMAL = re.compile(r'(%sمی‌?(?:شود|کند|خواهم|رود|گوید|دانم|توانی)(?!%s)|(?<!%s)کنید(?!%s)|(?<!%s)است(?!%s)|(?<!%s)اگر(?!%s)|خانه(?!%s)|زمستان)'
                    % (_MI_HEAD, W, W, W, W, W, W, W, W))

# پایانِ جمله: . ! ؟ ? ؛ حتی وقتی پشتش بسته‌شدنِ پُررنگ یا کج آمده («**…کن.** بعد»)
_END = '[.؟!؛?]'
_END_LB = '(?:%s)' % '|'.join('(?<=%s%s)' % (_END, re.escape(t))
                              for t in ('', '**', '__', '*', '_', '\u00bb', '\u00bb**', '**\u00bb', ')'))
SENT_SPLIT = re.compile(r'%s\s+|\n+' % _END_LB)
_SENT_BOUND = re.compile(r'%s\s+|%s+' % (_END_LB, BLOCK))
# واژه: حرف، رقم و نیم‌فاصله؛ «،» «؛» «؟» و نشانه‌های دیگرِ بازه‌ی عربی واژه نیستند.
# «٫» و «٬» جداکننده‌ی درونِ عددند (۲٬۵۰۰ یک واژه است).
WORD = re.compile(r'[%s%s\u066B\u066C\w]+' % (FA_LETTERS, ZWNJ))
# پسوندی که build به پیوندِ فایلِ حرفه‌ای در نسخه‌ی هسته می‌چسباند؛ در شمارِ واژه‌ی جمله نمی‌آید
_CORE_SUFFIX = re.compile(r'(?<![ \t])[ \t]*\(در والوری حرفه\u200cای\)')

# ---------------------------------------------------------------- خطاب (تو/شما)
# اگر scripts/profile_stats.py باشد، منطقِ count_address همان‌جا به کار می‌رود تا lint و
# profile_stats یکی بشمارند. این فهرست‌ها جایگزینِ هم‌راستای آن‌اند (والوری هسته آن را ندارد):
# «کنین/بخورین» جمعِ محاوره است (شما)؛ «تو خونه»، «توی کیف» مکان است (خطاب نیست)؛
# «می‌آید/بیاید» سوم‌شخص است؛ «بدهی» (وام)، «بدی» و «بری» (پنیر) عمداً نیستند.
_LB = '(?<![%s%s])' % (FA_LETTERS, ZWNJ)
_RB = '(?![%s%s])' % (FA_LETTERS, ZWNJ)
_TO_WORDS = [
    'باهات', 'واست', 'واسَت', 'برایت', 'خودت', 'خودتو', 'خودتم', 'بهت', 'برات', 'ازت',
    r'ن?می[\u200c ]?(?:کنی|خوای|خواهی|تونی|توانی|دونی|دانی|گی|گویی|شی|شوی|بینی|خری|گیری|زنی|خوری'
    r'|دی|دهی|یای|آیی|پوشی|فرستی|مونی|مانی|ری|روی|رسی|پرسی|کشی|بری|آری|ذاری|گذاری|پسندی)',
    r'ن?می\u200c(?!گسار|خوار|پرست|فروش|شایست)[%s]{2,}(?<!بایست)ی' % FA_LETTERS,
    r'(?:ب|ن)?کنی', 'بکنی', 'داری', 'نداری', 'هستی', 'نیستی', 'باشی', 'نباشی',
    'بخری', 'بگیری', 'ببینی', 'بدونی', 'بدانی', 'بیای', 'بزنی', 'بخوری', 'بپوشی', 'بفرستی',
    'بمونی', 'بمانی', 'بتونی', 'بتوانی', 'بشی', 'بخوای', 'بخواهی', 'بگی', 'بگویی', 'بذاری', 'بگذاری',
    'بزاری', 'بنویسی', 'بپرسی', 'بسازی', 'بچشی', 'بخونی', 'بیاری', 'ببری', 'بشنوی',
    # فعلِ امرِ مفرد (هم‌راستا با profile_stats)
    'بخر', 'بیا', 'بزن', 'بگیر', 'ببین', 'بپرس', 'بنویس', 'بچش', 'بپوش', 'برو', 'بمون', 'بفرست', 'بکن',
    'بساز', 'بخون', 'بخور', 'بذار', 'بزار', 'بگو', 'بشنو', 'بیار', 'نکن', 'نخر', 'نرو', 'کن', 'بده',
]
ADDRESS_TO = re.compile(_LB + '(?:' + '|'.join(_TO_WORDS) + ')' + _RB + '|(?<=[%s])\u200cت' % FA_LETTERS + _RB)
ADDRESS_SHOMA = re.compile(_LB + '(?:' + '|'.join([
    'شما', 'شماها', 'شماست', 'شمایید', 'برایتان', 'براتون', 'بهتان', 'بهتون', 'ازتان', 'ازتون', 'باهاتون',
    'باهاتان', 'خودتان', 'خودتون', 'واستون',
    r'ن?می[\u200c ]?(?:کنید|کنین|خواهید|خواین|خوایید|خواید|توانید|تونید|تونین|دانید|دونید|دونین|گویید|گید'
    r'|گین|شید|شین|بینید|بینین|گیرید|گیرین|دهید|دین|زنید|زنین|خورید|خورین|یایید|یاین|آیید|فرستید'
    r'|فرستین|مانید|مونید|مونین|رید|رین|ذارید|ذارین|گذارید|خرین)',
    # «می‌…ید/ین» جدا از «می»، جز سوم‌شخصِ «می‌آید، می‌گوید، می‌پاید»
    r'ن?می[\u200c ][%s]+(?:ید|ین)(?<![اوآ]ید)' % FA_LETTERS,
    r'(?:ب|ن)?کنید', r'(?:ب|ن)?کنین', 'دارید', 'دارین', 'ندارید', 'ندارین', 'هستید', 'هستین',
    'نیستید', 'نیستین', 'باشید', 'باشین', 'نباشید', 'نباشین', 'شوید', 'نشوید', 'بخرید', 'بخرین',
    'بگیرید', 'بگیرین', 'ببینید', 'ببینین', 'بدانید', 'بدونید', 'بدونین', 'بخوانید', 'بخونید', 'بخونین',
    'بروید', 'برین', 'بیایید', 'بیاین', 'بزنید', 'بزنین', 'بفرستید', 'بفرستین', 'بدهید', 'بمانید',
    'بمونید', 'بشوید', 'بشید', 'بخورید', 'بخورین', 'بپوشید', 'بپوشین', 'بگذارید', 'بذارید', 'بذارین',
    'بزارین', 'بگید', 'بگین', 'بگویید', 'بنویسید', 'بچشید', 'بچشین', 'بپرسین', 'بفرمایید', 'فرمایید',
]) + ')' + _RB + '|(?<=[%s])\u200c(?:تان|تون)' % FA_LETTERS + _RB)
# «تو»ی تنها فقط وقتی ضمیر است: پایانِ جمله، «به تو»، «تو را»، «تو هم می‌خوای»؛ «تو خونه» مکان است
_TO_PRON = re.compile(_LB + 'تو' + _RB)
_TO_PRON_NEXT = {'را', 'رو', 'هم', 'که', 'خودت', 'عزیز', 'جان', 'جون', 'تنها', 'باید'}
_TO_PRON_PREV = {'به', 'با', 'برای', 'واسه', 'مثل', 'مال', 'پیش', 'کنار', 'عاشق', 'همراه', 'جای',
                 'بدون', 'بی', 'منتظر', 'مخصوص'}
_TO_VERB = re.compile('(?:' + '|'.join(w for w in _TO_WORDS if w != 'بده') + ')$')
_FA_TOKEN = re.compile('[%s%s]+' % (FA_LETTERS, ZWNJ))


def _to_pronouns(src):
    """بازه‌های «تو»یی که ضمیرِ خطاب است (منطقِ profile_stats)."""
    out = []
    for m in _TO_PRON.finditer(src):
        after = src[m.end():m.end() + 60]
        if re.match(r'^[\s\u200c]*($|[،؛.!؟?:»)\]\n])', after):
            out.append((m.start(), m.end()))
            continue
        nxt = _FA_TOKEN.findall(after)[:2]
        before = _FA_TOKEN.findall(src[max(0, m.start() - 30):m.start()])
        prev = before[-1] if before else ''
        if prev in _TO_PRON_PREV or (nxt and (nxt[0] in _TO_PRON_NEXT or _TO_VERB.match(nxt[0]))) \
                or (len(nxt) > 1 and nxt[0] in ('هم', 'که', 'خودت') and _TO_VERB.match(nxt[1])):
            out.append((m.start(), m.end()))
    return out


# ---------------------------------------------------------------- جای‌نگهدار و محافظت
PLACEHOLDER = re.compile(r'\[[^\[\]\n]{1,120}\](?!\()')

_FRONT = re.compile(r'\A---[ \t]*\r?\n.*?\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|\Z)', re.S)
_HTML_RAW_OPEN = re.compile(r'<(script|style|pre|code|textarea|kbd|samp)\b[^<>]*>', re.I)
_HTML_RAW_CLOSE = dict((t, re.compile(r'</%s\s*>' % t, re.I))
                       for t in ('script', 'style', 'pre', 'code', 'textarea', 'kbd', 'samp'))


class _Span(object):
    """همان رابطِ لازمِ یک Match: start()، end()، group(0)."""
    __slots__ = ('string', '_a', '_b')

    def __init__(self, string, a, b):
        self.string, self._a, self._b = string, a, b

    def start(self, _g=0):
        return self._a

    def end(self, _g=0):
        return self._b

    def span(self, _g=0):
        return self._a, self._b

    def group(self, _g=0):
        return self.string[self._a:self._b]


class _Finder(object):
    """جایگزینِ خطی برای الگویی که فقط finditer از آن خواسته می‌شود."""

    def __init__(self, fn):
        self._fn = fn

    def finditer(self, text):
        return (_Span(text, a, b) for a, b in self._fn(text))

    def sub(self, repl, text):
        out, pos = [], 0
        for a, b in self._fn(text):
            out.append(text[pos:a])
            out.append(repl(_Span(text, a, b)) if callable(repl) else repl)
            pos = b
        out.append(text[pos:])
        return ''.join(out)


def _html_raw_spans(text):
    """<script|style|pre|code|textarea|kbd|samp>…</همان> مثلِ الگوی تنبلِ قدیم، در زمانِ خطی:
    برچسبی که بسته‌ای پس از آن نیست، بسته‌ای برای برچسب‌های بعدی‌اش هم ندارد."""
    out, pos, dead = [], 0, set()
    while True:
        m = _HTML_RAW_OPEN.search(text, pos)
        if not m:
            return out
        name = m.group(1).lower()
        c = None if name in dead else _HTML_RAW_CLOSE[name].search(text, m.end())
        if c is None:
            dead.add(name)
            pos = m.start() + 1
            continue
        out.append((m.start(), c.end()))
        pos = c.end()


def _html_comment_spans(text):
    """<!--…--> مثلِ «<!--.*?-->» با re.S، در زمانِ خطی."""
    out, pos = [], 0
    while True:
        a = text.find('<!--', pos)
        if a < 0:
            return out
        b = text.find('-->', a + 4)
        if b < 0:
            return out
        out.append((a, b + 3))
        pos = b + 3


_HTML_RAW = _Finder(_html_raw_spans)
_HTML_COMMENT = _Finder(_html_comment_spans)
_TAG = re.compile(r'</?[A-Za-z][A-Za-z0-9:-]*(?:\s[^<>]*)?/?>|<![A-Za-z][^<>]*>|<\?[^<]*?\?>')
_BLOCK_TAGS = {'p', 'div', 'br', 'li', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr', 'td',
               'th', 'table', 'section', 'article', 'header', 'footer', 'nav', 'aside', 'main',
               'blockquote', 'hr', 'title', 'option', 'dt', 'dd', 'figcaption', 'figure', 'body',
               'head', 'html', 'form', 'label', 'button', 'caption', 'summary', 'details'}
_INLINE_CODE = re.compile(r'``[^\n]+?``|`[^`\n]+`')
_MD_LINK_TARGET = re.compile(r'\]\([^()\s]*(?:\([^()\s]*\)[^()\s]*)*(?:\s+"[^"\n]*"|\s+\'[^\'\n]*\')?\)')
# تعریفِ پیوندِ ارجاعی فقط وقتی هدفش نشانی یا مسیر است: «[1]: https://…»، «[x]: ./a.md "عنوان"».
# «[نامِ کلینیک]: متنِ پیامک…» پیشوندِ فرستنده است و باید سنجیده شود.
_REF_TARGET = (r'(?:<[^<>\s]+>|[A-Za-z][A-Za-z0-9+.\-]*:\S+|[./#~?]\S*|[^\s/]*/\S*'
               r'|[^\s#?]*\.[A-Za-z0-9]{1,8}(?:[#?]\S*)?)')
_MD_REFDEF = re.compile(r'^[ \t]{0,3}\[[^\]\n]+\]:[ \t]*%s(?:[ \t]+(?:"[^"\n]*"|\'[^\'\n]*\'|\([^()\n]*\)))?[ \t\r]*$'
                        % _REF_TARGET, re.M)
# بخشِ «نادرست»ِ عمدی در فایل‌های آموزشی: هر نشانه روی سطرِ خودش (تصمیمِ D2)
_IGN_OPEN = re.compile(r'^[ \t]*<!--[ \t]*lint-ignore[ \t]*-->[ \t\r]*$', re.M)
_IGN_CLOSE = re.compile(r'^[ \t]*<!--[ \t]*/lint-ignore[ \t]*-->[ \t\r]*$', re.M)
_URL = re.compile(r'(?:https?|ftp)://[^\s<>"\'«»]+|www\.[^\s<>"\'«»]+'
                  r'|(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,63}')
_URL_TRAIL = '.,;:!?،؛؟)]}\'"'
_MUSTACHE = r'\{\{(?:[^{}\n]|\{(?!\{)|\}(?!\}))*\}\}'
_TEMPLATE = re.compile(_MUSTACHE + r'|\{%(?:[^%{\n]|%(?!\})|\{(?!%))*%\}|\{[^{}\n]{1,40}\}|%[A-Za-z_]\w*%'
                       r'|\$\{[^{}\n]*\}')
_FENCE = re.compile(r'^[ \t]{0,3}(`{3,}|~{3,})')


def _fence_spans(text):
    spans, pos, start, marker = [], 0, None, None
    for ln in text.split('\n'):
        m = _FENCE.match(ln)
        end = pos + len(ln)
        if start is None:
            if m:
                start, marker = pos, m.group(1)[0]
        elif m and m.group(1)[0] == marker:
            spans.append((start, end))
            start = None
        pos = end + 1
    if start is not None:
        spans.append((start, len(text)))
    return spans


def ignore_spans(text, fences=None):
    """بازه‌های میانِ «<!-- lint-ignore -->» و «<!-- /lint-ignore -->» (هر کدام روی سطرِ خودش).
    نشانه‌ی داخلِ بلوکِ کد نمونه است و دستور حساب نمی‌شود. نشانه‌ی بازِ بی‌بسته تا پایانِ متن."""
    if 'lint-ignore' not in text:
        return []
    fences = _fence_spans(text) if fences is None else fences

    def in_fence(p):
        return any(a <= p < b for a, b in fences)

    def find(rx, pos):
        m = rx.search(text, pos)
        while m and in_fence(m.start()):
            m = rx.search(text, m.end())
        return m

    out, pos = [], 0
    while True:
        m = find(_IGN_OPEN, pos)
        if not m:
            break
        c = find(_IGN_CLOSE, m.end())
        end = c.end() if c else len(text)
        out.append((m.start(), end))
        if not c:
            break
        pos = end
    return out



def drop_ignored(text):
    """متن با سطرهای خالی به‌جای بخش‌های lint-ignore (نشانه‌ها هم)؛ شمارِ سطرها می‌ماند.
    برای ابزارهای دیگر (audit_corpus، profile_stats) تا همه یک قاعده را بفهمند."""
    spans = ignore_spans(text)
    if not spans:
        return text
    out, pos = [], 0
    for ln in text.split('\n'):
        end = pos + len(ln)
        out.append('' if any(a <= pos and end <= b for a, b in spans) else ln)
        pos = end + 1
    return '\n'.join(out)


def _url_spans(text):
    out = []
    for m in _URL.finditer(text):
        a, b = m.start(), m.end()
        while b > a and text[b - 1] in _URL_TRAIL:
            b -= 1
        out.append((a, b))
    return out


def _is_block_tag(tag):
    m = re.match(r'</?([A-Za-z][A-Za-z0-9]*)', tag)
    return bool(m) and m.group(1).lower() in _BLOCK_TAGS


def protected_spans(text, kind='text'):
    """بازه‌هایی که نه سنجیده می‌شوند و نه اصلاح: کد، برچسب و ویژگیِ html، نشانی،
    هدفِ پیوند، سرصفحه‌ی yaml و جای‌نگهدارِ قالب. (آغاز، پایان، بلوکی؟)"""
    spans = []

    def add(a, b, block=False):
        if b > a:
            spans.append((a, b, block))

    if kind == 'md':
        m = _FRONT.match(text)
        if m:
            add(0, m.end(), True)
    fences = _fence_spans(text)
    for a, b in fences:
        add(a, b, True)
    for a, b in ignore_spans(text, fences):
        add(a, b, True)
    for m in _HTML_RAW.finditer(text):
        add(m.start(), m.end(), True)
    for m in _HTML_COMMENT.finditer(text):
        add(m.start(), m.end(), True)
    for m in _TAG.finditer(text):
        add(m.start(), m.end(), _is_block_tag(m.group(0)))
    for m in _INLINE_CODE.finditer(text):
        add(m.start(), m.end())
    for m in _MD_LINK_TARGET.finditer(text):
        add(m.start() + 1, m.end())
    for m in _MD_REFDEF.finditer(text):
        add(m.start(), m.end(), True)
    for a, b in _url_spans(text):
        add(a, b)
    for m in _TEMPLATE.finditer(text):
        add(m.start(), m.end())
    spans.sort()
    merged = []
    for a, b, blk in spans:
        if merged and a <= merged[-1][1]:
            pa, pb, pblk = merged[-1]
            merged[-1] = (pa, max(pb, b), pblk or blk)
        else:
            merged.append((a, b, blk))
    return merged


def clean_text(text):
    """BOM را برمی‌دارد و پایانِ سطر را یکی می‌کند."""
    return text.replace(BOM, '').replace('\r\n', '\n').replace('\r', '\n')


def mask_prose(text, kind='text'):
    """همان طول: کد و برچسب و نشانی با نویسه‌ی MASK/BLOCK پوشانده می‌شوند."""
    spans = protected_spans(text, kind)
    if not spans:
        return text
    out = list(text)
    for a, b, blk in spans:
        ch = BLOCK if blk else MASK
        for k in range(a, b):
            if out[k] != '\n':
                out[k] = ch
    return ''.join(out)


def strip_md(lines):
    """بلوکِ کد را کنار می‌گذارد تا قالب‌ها و نمونه‌ها خطا نسازند."""
    out, fence = [], False
    for ln in lines:
        if ln.lstrip().startswith('```'):
            fence = not fence
            out.append('')
            continue
        out.append('' if fence else ln)
    return out


# ---------------------------------------------------------------- فیلترِ قاعده‌ها
NEG_EXEMPT = re.compile(r'(?<!%s)(اگر|اگه|وقتی|چون|هرچند|گرچه|ولی|اما|ولیکن|با\s+اینکه)(?!%s)' % (W, W))

_MI_WINE_BEFORE = re.compile(
    r'(?:(?<![%s])(?:جام|ساغر|پیاله|پیمانه|ساقی|باده|شراب|خم|سبو|سبوی|بوی|رنگ|مستیِ|قدح|صراحی)\u0650?'
    r'|\u0650)\s*$' % FA_LETTERS)
_MI_NOUN_AFTER = {'ناب', 'گلگون', 'کهنه', 'کهن', 'لعل', 'لعلی', 'ارغوانی', 'صاف', 'خوشگوار',
                  'انگوری', 'دوساله', 'مستانه'}
_VERB_LAST = set('مىیدتهن')
_WORD_AT = re.compile(r'[%s]+' % FA_LETTERS)


class _LineCtx(object):
    """جای‌های یک سطر، یک بار برای همه‌ی تطبیق‌ها: فاصله‌ها، حرف‌های فارسی، مرزها و فعل‌ها.
    فیلترها با bisect به چپ و راستِ هر تطبیق نگاه می‌کنند، بی کپی و بی پیمایشِ دوباره‌ی سطر
    (وگرنه سطرِ بلندِ پُرتطبیق زمانِ مربعی می‌گیرد)."""

    def __init__(self, src):
        self.src = src
        self.ws = [m.start() for m in re.finditer(r'\s', src)]
        self.fa = [m.start() for m in HAS_FA.finditer(src)]
        m = re.search('[^ \t%s%s]' % (MASK, BLOCK), src)
        self.first_sig = m.start() if m else len(src)
        self._marks = {}
        self._verbs = None

    def run_start(self, k):
        """آغازِ رشته‌ی بی‌فاصله‌ای که k درونِ آن است."""
        i = bisect.bisect_left(self.ws, k) - 1
        return self.ws[i] + 1 if i >= 0 else 0

    def run_end(self, k):
        i = bisect.bisect_right(self.ws, k)
        return self.ws[i] if i < len(self.ws) else len(self.src)

    def has_fa(self, a, b):
        i = bisect.bisect_left(self.fa, a)
        return i < len(self.fa) and self.fa[i] < b

    def marks(self, chars):
        """جای‌های مرتبِ این نویسه‌ها در سطر."""
        if chars not in self._marks:
            self._marks[chars] = [i for i, c in enumerate(self.src) if c in chars]
        return self._marks[chars]

    def before(self, pos, chars):
        """آخرین جای یکی از chars پیش از pos، یا ‎-1."""
        lst = self.marks(chars)
        i = bisect.bisect_left(lst, pos) - 1
        return lst[i] if i >= 0 else -1

    def after(self, pos, chars):
        lst = self.marks(chars)
        i = bisect.bisect_left(lst, pos)
        return lst[i] if i < len(lst) else -1

    def starts(self, rx):
        key = id(rx)
        if key not in self._marks:
            self._marks[key] = [m.start() for m in rx.finditer(self.src)]
        return self._marks[key]

    def found(self, rx, a, b):
        """آیا تطبیقی از rx در بازه‌ی [a, b) آغاز می‌شود؟ (مرزها نشانه‌اند، نه حرف)"""
        lst = self.starts(rx)
        i = bisect.bisect_left(lst, a)
        return i < len(lst) and lst[i] < b


_CTX = [None]


def _ctx(src):
    c = _CTX[0]
    if c is None or c.src is not src:
        c = _LineCtx(src)
        _CTX[0] = c
    return c


def _mi_is_verb(src, start, end):
    """«می» در «جامِ می ناب» اسم است و پیشوندِ فعل نیست."""
    w = _WORD_AT.match(src, end)
    word = ''.join(c for c in (w.group(0) if w else '') if c not in HARAKAT)
    if not word or word in _MI_NOUN_AFTER or word[-1] not in _VERB_LAST:
        return False
    i = start
    while i > 0 and src[i - 1].isspace():
        i -= 1
    # واژه‌ی پیش از «می» حداکثر هفت نویسه است (+ نگاهِ پشتِ سر)؛ پنجره‌ی کوتاه همان جواب را می‌دهد
    if _MI_WINE_BEFORE.search(src, max(0, i - 12), start):
        return False
    return True


def _keep_mi(src, m):
    return _mi_is_verb(src, m.start(), m.end())


def _keep_dash(src, m):
    c = _ctx(src)
    i, j, n = m.start(), m.end(), len(src)
    while i > 0 and src[i - 1] in ' \t\u00a0':
        i -= 1
    while j < n and src[j] in ' \t\u00a0':
        j += 1
    if c.first_sig >= i:
        return False                                     # خطِ تیره‌ی سرِ سطر، مثلِ فهرست یا گفت‌وگو
    if src[i - 1] in DIGITS and j < n and src[j] in DIGITS:
        return False                                     # بازه‌ی عددی: ۱۰–۲۰
    # واژه‌ی چسبیده به چپ و راستِ خط تیره (رشته‌ی بی‌فاصله)
    left_fa = not src[i - 1].isspace() and c.has_fa(c.run_start(i - 1), i)
    right_fa = j < n and not src[j].isspace() and c.has_fa(j, c.run_end(j))
    return left_fa or right_fa                           # جمله‌ی انگلیسی کارِ ما نیست


# نیمه‌ی مثبت خودش فعلِ دیگری ندارد و با «و/یا» شروع نمی‌شود؛ وگرنه فهرست یا دو جمله است
_NEG_GAP_VERB = re.compile(
    r'(?<!%s)(?:ن?می[\u200c ]\S+|ب?شود|ب?شوند|شد|شدند|ن?کنید|ن?کنند|ن?کند|کرد|کردند|ن?باشد|ن?باشند'
    r'|دارد|دارند|داشت|بود|بودند|نیست|نیستند|نیستیم|نیستید|هست|است|هستند|هستیم)(?!%s)'
    % (LZ, LZ))
_NEG_GAP_LIST = re.compile(r'^\s*(?:و|یا|ولی|اما|چون|زیرا|که|تا|اگر|اگه|وقتی)(?!%s)' % LZ)


def _keep_neg(src, m):
    if NEG_EXEMPT.search(src[max(0, m.start() - 40):m.end()]):
        return False
    gap = m.group('gap') or ''
    if _NEG_GAP_LIST.match(gap) or _NEG_GAP_VERB.search(gap):
        return False
    return True


# «می‌گردد» از «گشتن» (جست‌وجو، چرخیدن، برگشتن) اداری نیست:
# «دنبالِ کار می‌گردد»، «گیت‌هاب را می‌گردد»، «دورِ خورشید می‌گردد»، «باز می‌گردد»
_GARDAD = re.compile(r'می‌?\s?گرد(?:د|ند)$')
_GASHTAN_BEFORE = re.compile(
    r'(?:(?<!%s)(?:دنبال|دنبالِ|دنبالش|دنبالشان|دنبالم|دنبالت|دورِ|پیِ|گردِ)(?!%s)[^.!؟?؛،\n]{0,40}$'
    r'|(?<!%s)دور(?!%s)\s+[^\s.!؟?؛،][^.!؟?؛،\n]{0,38}$'
    r'|(?<!%s)(?:را|رو)(?!%s)\s+(?:(?!و\s)[^\s.!؟?؛،]+\s+){0,2}$'
    r'|(?<!%s)(?:باز|بر)\s*$)' % (LZ, LZ, LZ, LZ, LZ, LZ, LZ))


def _keep_admin(src, m):
    if _GARDAD.search(m.group(0)):
        before = src[max(0, m.start() - 60):m.start()]
        if _GASHTAN_BEFORE.search(before):
            return False
    return True


# «X، نه Y»: «نه تنها/فقط» (not-only)، «نه»ِ عدد («هشت، نه و ده»)، «نه … نه …»، پرسش و
# جوابِ «نه» («آیا …؟ نه، …»، «خیر، نه این بار») معاف‌اند. «یا نه» اصلاً «، نه» نیست.
# «نه چندان/خیلی» قید است («نه چندان دور»)، «نه ببخشید» اصلاحِ گوینده، و «، نه بیشتر» سقفِ شمار.
_NA_SKIP_FIRST = {'تنها', 'فقط', 'و', 'یا', 'چندان', 'خیلی', 'ببخشید'}
_NA_LIMIT = {'بیشتر', 'بیش‌تر', 'کمتر', 'کم‌تر', 'زیادتر', 'زودتر', 'دیرتر'}
_NA_ANSWER = {'بله', 'آره', 'آری', 'خیر', 'نخیر', 'نه', 'اصلاً', 'اصلا', 'هرگز', 'ابداً', 'ابدا', 'البته'}
_NA_WORD = re.compile(r'(?<![%s%s])نه(?![%s%s])' % (FA_LETTERS, ZWNJ, FA_LETTERS, ZWNJ))
_NA_NEXT = re.compile(r'[ \t]*[،,][ \t]*(?:و[ \t]+)?نه(?![%s%s])' % (FA_LETTERS, ZWNJ))
_NA_BOUNDS = '.!؟?؛;\n' + BLOCK
_AND_WORD = re.compile(r'(?<![%s%s])و(?![%s%s])' % (FA_LETTERS, ZWNJ, FA_LETTERS, ZWNJ))


def _keep_na(src, m):
    words = [w.strip('«»"\'*_()[]' + MASK) for w in m.group('tail').split()]
    if words[0] in _NA_SKIP_FIRST or (len(words) == 1 and words[0] in _NA_LIMIT):
        return False
    if 'نه' in words[1:]:
        return False                                   # «بد، نه بد نه خوب، خوب»
    j = m.end()
    while j < len(src) and src[j] in ' \t':
        j += 1
    if src[j:j + 1] in ('؟', '?'):
        return False                                   # پرسش: «این را می‌خواهی، نه آن را؟»
    if _NA_NEXT.match(src, m.end()):
        return False                                   # «…، نه X، نه Y»
    c = _ctx(src)
    start = c.before(m.start(), _NA_BOUNDS) + 1
    if c.found(_NA_WORD, start, m.start()):
        return False                                   # «نه پول دارد، نه وقت»؛ «آیا …؟ نه، …»
    last = src[max(start, c.before(m.start(), '،,') + 1):m.start()].strip(' \t*_' + MASK)
    return last not in _NA_ANSWER                      # «خیر، نه این بار»


_SERIAL_BOUNDS = '.!؟?؛;:\n' + BLOCK


def _keep_serial(src, m):
    """فقط فهرست: بندِ میانی ۱ تا ۴ واژه، بی‌فعل و بی «و»ِ دیگر. اگر پیش از ویرگولِ اول و پس از
    «و» هر دو فعل داشته باشند، متن دو جمله است با یک بندِ معترضه («… جمع می‌کنیم، با اطلاعش، و …
    نمی‌کنیم») و فهرست نیست. بندِ «نه …» کارِ na-contrast است."""
    x = m.group('x')
    words = WORD.findall(x)
    if not HAS_FA.search(x) or not words or len(words) > 4 or words[0] == 'نه':
        return False
    if _NEG_GAP_VERB.search(x) or _AND_WORD.search(x):
        return False
    c = _ctx(src)
    start = c.before(m.start(), _SERIAL_BOUNDS) + 1
    end = c.after(m.end(), _SERIAL_BOUNDS)
    end = len(src) if end < 0 else end
    return not (c.found(_NEG_GAP_VERB, start, m.start()) and c.found(_NEG_GAP_VERB, m.end(), end))


def _keep_admin_phrase(src, m):
    """«نسبت به … اقدام» و «اقدام به … کنید»: فاصله‌ی میانی فعل ندارد (وگرنه دو بند است)."""
    gd = m.groupdict()
    for g in ('g1', 'g2'):
        gap = gd.get(g)
        if gap and (_NEG_GAP_VERB.search(gap) or _NEG_GAP_LIST.match(gap)):
            return False
    return True


PATTERN_FILTERS = {'dash': _keep_dash, 'zwnj-mi': _keep_mi, 'neg-contrast': _keep_neg, 'admin': _keep_admin,
                   'na-contrast': _keep_na, 'serial-comma': _keep_serial, 'admin-phrase': _keep_admin_phrase}

# ---------------------------------------------------------------- قاعده‌های سطری
_HEADING_SUMMARY = re.compile(
    r'^\s{0,3}(?:#{1,6}\s*)?(?:\*\*|__)?\s*(?:[0-9\u06F0-\u06F9]+[.)\-]\s*)?'
    r'(?P<at>جمع[\u200c ]?بندی)(?:\s+(?:نهایی|کلی))?\s*(?:\*\*|__)?\s*[:：]?\s*(?:\*\*|__)?\s*$')
_MD_HEADER = re.compile(r'^\s{0,3}#{1,6}\s+\S')
_BOLD_LINE = re.compile(r'^\s*(\*\*|__)[^*_\n]{1,80}\1\s*[:：]?\s*$')
_EMOJI_LEAD = re.compile(r'^[ \t]*(?:[-*•][ \t]*)?(?:%s)(?:[ \t]*(?:%s))*[ \t]*(?=\S)'
                         % (EMOJI.pattern, EMOJI.pattern))


# ---------------------------------------------------------------- قاعده‌های پویا (برای --rules)
DYNAMIC_RULES = [
    ('lexicon', WARN, 'lexicon', 'واژه‌ی لودهنده از فهرستِ LEXICON'),
    ('brand-spelling', ERROR, 'profile', 'املای نادرستِ نامِ برند (brand.misspellings)'),
    ('profile-banned', ERROR, 'profile', 'واژه‌ی ممنوعِ پروفایل (banned، و banned در formats[قالب])'),
    ('profile-avoid', WARN, 'profile', 'واژه‌ی «نگو»ی پروفایل (avoid)، با جایگزین از prefer'),
    ('jargon', WARN, 'profile', 'واژه‌ی فرنگیِ تخصصی وقتی dials.jargon برابرِ ۱ یا ۲ است'),
    ('address', WARN, 'profile', 'خطابِ ناهمخوان: پروفایل address=shoma و متن «تو»، یا برعکس'),
    ('register', WARN, 'profile', 'لحنِ ناهمخوان با register پروفایل یا قالب (formal/colloquial)'),
    ('mixed-register', WARN, 'dynamic', 'محاوره و نوشتاری کنارِ هم وقتی لحن any است'),
    ('profile-register-alias', WARN, 'profile',
     'نامِ قدیمیِ لحن در پروفایل: written→formal، colloquial-written→colloquial'),
    ('profile-invalid', WARN, 'profile', 'مقدارِ نامعتبر در پروفایل (لحن، خطاب، دکمه، قالب، نسخه، romanization)'),
    ('long-sentence', WARN, 'dynamic',
     'جمله‌ی بلندتر از سقف؛ سقف: --max-words > formats[قالب] > قالب (فقط سخت‌تر) > پروفایل > دکمه (پیش‌فرض ۲۴)؛ '
     'بندِ فهرست و خانه‌ی جدول هم جمله‌اند'),
    ('ke-chain', WARN, 'dynamic', 'سه «که» یا بیشتر در یک جمله (بندِ فهرست و خانه‌ی جدول هم)'),
    ('ra-chain', WARN, 'dynamic', 'دو «را» در یک جمله (بندِ فهرست و خانه‌ی جدول هم)'),
    ('rhetorical-open', WARN, 'dynamic', 'شروعِ متن با سؤالِ بلاغی'),
    ('same-opening', WARN, 'dynamic', 'سه جمله‌ی پیاپی با یک واژه شروع شده‌اند (بندِ فهرستِ سه‌واژه‌ای به بالا هم)'),
    ('flat-rhythm', WARN, 'dynamic', 'طولِ جمله‌ها تقریباً یکسان است'),
    ('bangs', WARN, 'dynamic', 'علامتِ تعجب بیش از سقف (exclaim_max)'),
    ('emoji', WARN, 'dynamic', 'ایموجی بیش از سقف (emoji_max)؛ پرچم و دنباله‌ی ZWJ یکی شمرده می‌شوند'),
    ('emoji-bullet', WARN, 'dynamic', 'ایموجی به‌جای بولت در سرِ دو سطر یا بیشتر'),
    ('caption-header', WARN, 'format', 'تیترِ markdown یا سطرِ پُررنگ داخلِ کپشن (فقط با --format caption)'),
    ('final-word', WARN, 'dynamic', '«جمع‌بندی» به‌عنوانِ تیتر (بخشِ سطریِ همین قاعده)'),
    ('channel-length', ERROR, 'channel',
     'متن بلندتر از سقفِ کانال (نویسه، بایت یا پاره‌ی پیامک)؛ اگر سقف تأییدنشده باشد هشدار'),
    ('channel-visible', WARN, 'channel', 'متن بلندتر از بخشِ پیدا پیش از «بیشتر» (visible_chars)'),
]

# توضیحِ بیشترِ --rules؛ پیامِ خودِ مسئله کوتاه می‌ماند
RULE_NOTES = {
    'na-contrast': '«، نه» یا «؛ نه» و ۱ تا ۴ واژه تا پایانِ جمله، «،» یا پایانِ خانه. معاف: «نه … نه …»، '
                   '«نه تنها/فقط» (قاعده‌ی not-only)، «یا نه»، «نه»ِ عدد در فهرست، پرسش، جوابِ «نه» '
                   'مثلِ «آیا …؟ نه، …»، قیدِ «نه چندان/خیلی»، «نه ببخشید» و سقفِ «، نه بیشتر/کمتر»',
    'serial-comma': '«…، X، و Y» با بندِ میانیِ ۱ تا ۴ واژه و بی‌فعل؛ «، و» میانِ دو جمله سنجیده نمی‌شود '
                    '(وقتی پیش از ویرگولِ اول و پس از «و» هر دو فعل دارند) و بندِ «نه …» کارِ na-contrast است',
    'admin-phrase': '«اقدام کنید/نمایید»، «اقدام به … کنید/نمایید» و «نسبت به … اقدام» هم؛ '
                    '«نمایید» جدا خطای admin است',
    'mixed-register': 'متنِ داخلِ «…» شمرده نمی‌شود؛ در --md هر بلوکِ نقل‌قول (>) جدا سنجیده می‌شود',
    'register': 'متنِ داخلِ «…» و در --md بلوکِ نقل‌قول (>) شمرده نمی‌شوند',
    'bangs': 'در --md بلوکِ نقل‌قول (>) شمرده نمی‌شود',
    'emoji': 'در --md بلوکِ نقل‌قول (>) شمرده نمی‌شود',
    'long-sentence': '«،» و نشانه واژه نیستند؛ پسوندِ « (در والوری حرفه‌ای)»ِ نسخه‌ی هسته شمرده نمی‌شود',
    'same-opening': 'خانه‌ی جدول شمرده نمی‌شود و زنجیره را می‌بُرد: خانه‌های یک ردیف نمونه‌های یک الگو هستند '
                    'و خانه‌های یک ستون برچسب یا منبعِ تکراری',
}

# ---------------------------------------------------------------- اصلاحِ مکانیکی
# فقط چیزهایی که معنا را عوض نمی‌کنند، و فقط در بازه‌ی فارسی بیرون از کد، برچسب،
# ویژگیِ html، نشانی و جمله‌ی انگلیسی. صدا، قصه و ادعا دستی درست می‌شوند.
_FIX_QUOTE = re.compile(r'"(?=\S)([^"\n]{1,80}?)(?<=\S)"')
_FIX_DASH = re.compile(r'(?<=[%s»)])[ \t\u00a0]+[\u2014\u2013][ \t\u00a0]+(?=[%s«(])' % (FA_LETTERS, FA_LETTERS))
_FIX_HYPHEN = re.compile(r'(?<=[%s»)]) - (?=[%s«(])' % (FA_LETTERS, FA_LETTERS))
_FIX_COMMA = re.compile(r'(?<=[%s»)])[ \t]*,(?![0-9\u06F0-\u06F9])(?=[ \t]*(?:[%s«(\n\r]|$))'
                        % (FA_LETTERS, FA_LETTERS))
_FIX_SEMI = re.compile(r'(?<=[%s»)])[ \t]*;(?=[ \t]*(?:[%s«(\n\r]|$))' % (FA_LETTERS, FA_LETTERS))
_FIX_QMARK = re.compile(r'(?<=[%s»)])[ \t]*\?(?=[ \t]*(?:[%s«()\n\r.!؟»]|$))' % (FA_LETTERS, FA_LETTERS))
_FIX_SPACE_PUNCT = re.compile(r'(?<=[%s»)\u06F0-\u06F9])[ \t]+(?![:;][)(DP])([،؛:؟!]|\.(?!\.))(?=[ \t\n\r«»)]|$)'
                              % FA_LETTERS)
_FIX_BANGS = re.compile(r'(?<=[%s»)؟ \t])[!！]{2,}' % FA_LETTERS)
_FIX_MI = re.compile(r'(?<!%s)(ن?می) (?=[%s]{2,})' % (W, FA))
_FIX_HA = re.compile(r'(?<=%s) (ها|های|هایی|تر|ترین)(?!%s)' % (W, W))
_FIX_EZAFE = re.compile(r'(?<=[%s]ه) ی(?!%s)' % (FA, W))
_FIX_WORDS = [
    (re.compile(r'(?<!%s)بعنوان(?!%s)' % (W, W)), 'به\u200cعنوان'),
    (re.compile(r'(?<!%s)بخاطر(?!%s)' % (W, W)), 'به\u200cخاطر'),
    (re.compile(r'(?<!%s)(این|آن|همین)طور' % W), '\\1\u200cطور'),
]


def _fix_quotes(seg):
    def rep(m):
        inner = m.group(1)
        if not HAS_FA.search(inner):
            return m.group(0)                 # "hello" انگلیسی است
        before = seg[:m.start()].rstrip(' \t')
        after = seg[m.end():].lstrip(' \t')
        if before and ((before[-1].isascii() and before[-1].isalnum()) or before[-1] in '=\\'):
            return m.group(0)                 # وسطِ جمله‌ی انگلیسی یا کد
        if after and after[0].isascii() and after[0].isalnum():
            return m.group(0)
        return '«%s»' % inner
    return _FIX_QUOTE.sub(rep, seg)


def _fix_mi(m):
    if _mi_is_verb(m.string, m.start(), m.end()):
        return m.group(1) + ZWNJ
    return m.group(0)


def _fix_segment(s):
    if not s:
        return s
    s = s.replace('\u064A', 'ی').replace('\u0649', 'ی').replace('\u0643', 'ک')
    s = _fix_quotes(s)
    s = _FIX_DASH.sub('، ', s)
    s = _FIX_HYPHEN.sub('، ', s)
    s = _FIX_COMMA.sub('،', s)
    s = _FIX_SEMI.sub('؛', s)
    s = _FIX_QMARK.sub('؟', s)
    s = _FIX_SPACE_PUNCT.sub(r'\1', s)
    s = _FIX_BANGS.sub('!', s)
    s = _FIX_MI.sub(_fix_mi, s)
    s = _FIX_HA.sub('\u200c\\1', s)
    s = _FIX_EZAFE.sub('\u200cی', s)
    for rx, rep in _FIX_WORDS:
        s = rx.sub(rep, s)
    return s


def fix_text(text, md=False, kind=None):
    """اصلاحِ مکانیکی. کد، برچسب، ویژگی، نشانی و سرصفحه دست نمی‌خورند؛ پایانِ سطر
    (CRLF یا LF) همان می‌ماند. (متنِ اصلاح‌شده، تعدادِ سطرهای عوض‌شده)."""
    kind = kind or ('md' if md else 'text')
    if kind == 'locale':
        return text, 0
    text = text.replace(BOM, '')
    out, pos = [], 0
    for a, b, _blk in protected_spans(text, kind):
        if a > pos:
            out.append(_fix_segment(text[pos:a]))
        out.append(text[a:b])
        pos = b
    out.append(_fix_segment(text[pos:]))
    new = ''.join(out)
    old_l, new_l = text.split('\n'), new.split('\n')
    n = sum(1 for x, y in zip(old_l, new_l) if x != y) + abs(len(old_l) - len(new_l))
    return new, n


# ---------------------------------------------------------------- خواندنِ فایل
def _decode(data, label):
    if data.startswith(codecs.BOM_UTF8):
        try:
            return data[3:].decode('utf-8'), {'encoding': 'utf-8', 'bom': True}
        except UnicodeDecodeError:
            pass
    elif data.startswith(codecs.BOM_UTF16_LE) or data.startswith(codecs.BOM_UTF16_BE):
        try:
            return data.decode('utf-16'), {'encoding': 'utf-16', 'bom': True}
        except UnicodeDecodeError:
            pass
    else:
        try:
            return data.decode('utf-8'), {'encoding': 'utf-8', 'bom': False}
        except UnicodeDecodeError:
            pass
    raise UserError('«%s» با UTF-8 خوانده نشد؛ فایل را با کدگذاریِ UTF-8 ذخیره کن. '
                    '(not valid UTF-8)' % label)


def read_text(path, with_meta=False):
    """فایل را با utf-8-sig (یا utf-16 اگر BOM داشت) می‌خواند؛ BOM هرگز در متن نمی‌ماند.
    with_meta=True: (متن، {'encoding', 'bom', 'newline'})."""
    if path == '-':
        data = sys.stdin.buffer.read() if hasattr(sys.stdin, 'buffer') else sys.stdin.read().encode('utf-8')
        label = 'stdin'
    else:
        try:
            with open(path, 'rb') as fh:
                data = fh.read()
        except FileNotFoundError:
            raise UserError('فایل پیدا نشد: %s (file not found)' % path)
        except IsADirectoryError:
            raise UserError('این مسیر پوشه است؛ نامِ یک فایل را بده: %s' % path)
        except PermissionError:
            raise UserError('اجازه‌ی خواندنِ این فایل نیست: %s' % path)
        except OSError as e:
            raise UserError('خواندنِ «%s» نشد: %s' % (path, e.strerror or e))
        label = path
    text, meta = _decode(data, label)
    text = text.replace(BOM, '')
    meta['newline'] = '\r\n' if '\r\n' in text else '\n'
    return (text, meta) if with_meta else text


def write_text(path, text, meta=None):
    """با همان کدگذاری و BOM؛ پایانِ سطر همان است که در متن است."""
    meta = meta or {}
    if meta.get('encoding') == 'utf-16':
        data = text.encode('utf-16')
    else:
        data = text.encode('utf-8')
        if meta.get('bom'):
            data = codecs.BOM_UTF8 + data
    try:
        with open(path, 'wb') as fh:
            fh.write(data)
    except OSError as e:
        raise UserError('نوشتن در «%s» نشد: %s' % (path, e.strerror or e))


PROSE_EXTS = ('.txt', '.md', '.mdx', '.markdown', '.html', '.htm')
LOCALE_EXTS = ('.json', '.po', '.pot', '.arb', '.xliff', '.xlf', '.strings', '.xml')
SUPPORTED_EXTS = PROSE_EXTS + LOCALE_EXTS
SKIP_DIRS = {'node_modules', '__pycache__', 'venv', '.venv', 'site-packages'}
SKIP_FILES = {'package-lock.json', 'npm-shrinkwrap.json', 'composer.lock'}  # فقط در پیمایشِ پوشه
_FIXED_OUT = re.compile(r'\.fixed\.[^./\\]+$')


def _has_magic(s):
    return any(c in s for c in '*?[')


def _in_skip_dir(path, pattern):
    """پوشه‌ای از SKIP_DIRS (node_modules و مانندش) زیرِ بخشِ ثابتِ الگو؟ «posts/*» پوشه‌ی
    posts/node_modules را برنمی‌دارد؛ اگر خودِ بخشِ ثابت در node_modules باشد، کاربر خواسته است."""
    cut = min([pattern.find(c) for c in '*?[' if c in pattern] or [len(pattern)])
    base = os.path.dirname(pattern[:cut]) or '.'
    try:
        rel = os.path.relpath(path, base)
    except ValueError:        # درایوِ دیگر در ویندوز
        return False
    return any(part in SKIP_DIRS for part in re.split(r'[\\/]', rel))


def _walk(root, exts):
    for r, ds, fs in os.walk(root):
        ds[:] = sorted(d for d in ds if not d.startswith('.') and d not in SKIP_DIRS)
        for f in sorted(fs):
            if f.lower().endswith(exts) and not _FIXED_OUT.search(f) and f.lower() not in SKIP_FILES:
                yield os.path.join(r, f)


def iter_paths(args, exts=SUPPORTED_EXTS, missing='error'):
    """مسیرهای ورودی را باز می‌کند: الگو (حتی روی ویندوز)، پوشه (بازگشتی، فقط پسوندهای
    پشتیبانی‌شده)، '-' برای ورودیِ استاندارد. فهرستِ یکتا به همان ترتیب.
    missing='error' → UserError؛ 'skip' → نادیده."""
    out, seen = [], set()

    def push(p):
        key = p if p == '-' else os.path.normcase(os.path.abspath(p))
        if key not in seen:
            seen.add(key)
            out.append(p)

    for a in args or []:
        if a == '-':
            push('-')
            continue
        p = os.path.expanduser(a)
        if os.path.isdir(p):
            found = list(_walk(p, exts))
            if not found and missing == 'error':
                raise UserError('در پوشه‌ی «%s» فایلِ پشتیبانی‌شده نیست (%s).' % (a, ' '.join(exts)))
            for f in found:
                push(f)
            continue
        if os.path.isfile(p):
            push(p)
            continue
        if _has_magic(p):
            hits = 0
            pat_ext = os.path.splitext(p)[1].lower()
            own = tuple([pat_ext]) if pat_ext and not _has_magic(pat_ext) else ()
            for mp in sorted(glob.glob(p, recursive=True)):
                if _in_skip_dir(mp, p):
                    continue
                if os.path.isdir(mp):
                    for f in _walk(mp, exts):
                        push(f)
                        hits += 1
                elif mp.lower().endswith(exts + own):   # «*.csv» یعنی کاربر خودش csv خواسته
                    push(mp)
                    hits += 1
            if hits:
                continue
            if missing == 'error':
                raise UserError('هیچ فایلی با الگوی «%s» پیدا نشد.' % a)
            continue
        if missing == 'error':
            raise UserError('فایل یا پوشه پیدا نشد: %s (file not found)' % a)
    return out


def detect_kind(path, md=False):
    ext = os.path.splitext(path or '')[1].lower()
    if ext in CSV_EXTS:
        return 'csv'
    if ext in LOCALE_EXTS:
        return 'locale'
    if md or ext in ('.md', '.mdx', '.markdown'):
        return 'md'
    if ext in ('.html', '.htm'):
        return 'html'
    return 'text'


# ---------------------------------------------------------------- پروفایل
DIAL_WORDS = {1: 14, 2: 18, 3: 24, 4: 28, 5: 34}
DIAL_MARKS = {0: (0, 0), 1: (1, 0), 2: (1, 1), 3: (2, 1)}
DEFAULT_MAX_WORDS = 24
# پارامترهای تنظیم‌پذیر برای هاب (spec 7.3): پیش‌فرضِ درونی و بازه‌ای که پایه‌ی امضاشده می‌پذیرد
HUB_PARAMS = {'long-sentence.max_words': {'default': DEFAULT_MAX_WORDS, 'min': 18, 'max': 34, 'bucket': 4}}
# پیش‌فرضِ دکمه‌ها بی‌پروفایل (تصمیمِ D5). lint از این‌ها فقط سقفِ جمله و نشانه‌های پرصدا را
# می‌گیرد؛ خطاب و jargon قاعده‌ی پروفایل‌اند و بی‌پروفایل سنجیده نمی‌شوند.
DIAL_DEFAULTS = dict(VP.DIAL_DEFAULTS)
DEFAULT_LOUD_MARKS = DIAL_DEFAULTS['loud_marks']
REGISTERS = ('any', 'formal', 'colloquial')
REGISTER_ALIASES = {'written': 'formal', 'colloquial-written': 'colloquial'}
ADDRESSES = ('any', 'shoma', 'to')
ADDRESS_ALIASES = {'شما': 'shoma', 'تو': 'to'}
DIAL_RANGES = dict(VP.DIAL_RANGES)
DIAL_ALIASES = {'rhetoric_dose': 'rhetoric'}

FORMAT_IDS = ['caption', 'story', 'reels', 'carousel', 'post', 'sms', 'otp', 'email', 'subject', 'push',
              'ui', 'error', 'product', 'listing', 'landing', 'about', 'blog', 'ad', 'press', 'bot',
              'reply', 'hard', 'deck', 'script', 'name', 'headline']
# پیش‌فرضِ محافظه‌کارانه‌ی هر قالب. آنچه نیست از پروفایل یا دکمه می‌آید (سقفِ جمله ۲۴).
FORMAT_DEFAULTS = {
    'caption': {'max_words': 20, 'note': 'کپشنِ شبکه‌ی اجتماعی'},
    'story': {'note': 'متنِ استوری'},
    'reels': {'note': 'متن و زیرنویسِ ویدیوی کوتاه'},
    'carousel': {'note': 'اسلایدهای کاروسل'},
    'post': {'note': 'پستِ کانال یا شبکه'},
    'sms': {'max_words': 16, 'emoji_max': 0, 'note': 'پیامک'},
    'otp': {'max_words': 12, 'emoji_max': 0, 'exclaim_max': 0, 'note': 'پیامکِ رمزِ یک‌بارمصرف'},
    'email': {'note': 'بدنه‌ی ایمیل'},
    'subject': {'max_words': 16, 'note': 'موضوعِ ایمیل'},
    'push': {'max_words': 14, 'note': 'اعلانِ اپ'},
    'ui': {'max_words': 14, 'emoji_max': 0, 'exclaim_max': 0, 'note': 'ریزمتنِ رابط'},
    'error': {'max_words': 14, 'emoji_max': 0, 'exclaim_max': 0, 'note': 'پیامِ خطا'},
    'product': {'note': 'توضیحِ محصول'},
    'listing': {'note': 'آگهیِ بازارگاه'},
    'landing': {'note': 'صفحه‌ی فرود'},
    'about': {'note': 'درباره‌ی ما'},
    'blog': {'note': 'مقاله'},
    'ad': {'note': 'آگهی'},
    'press': {'emoji_max': 0, 'exclaim_max': 0, 'note': 'خبرِ مطبوعاتی'},
    'bot': {'note': 'ربات و دستیارِ گفت‌وگو'},
    'reply': {'note': 'پاسخ به نظر یا پیام'},
    'hard': {'emoji_max': 0, 'exclaim_max': 0, 'note': 'پیامِ سخت: عذرخواهی، خبرِ بد'},
    'deck': {'emoji_max': 0, 'note': 'ارائه'},
    'script': {'note': 'متنِ صوتی و ویدیویی'},
    'name': {'note': 'نام‌گذاری'},
    'headline': {'note': 'تیتر'},
}


# نامِ پیش از نسخه‌ی ۳ (والیا) فقط خوانده می‌شود: شناسه‌ی whalya و پوشه‌ی ~/.whalya/profiles.
LEGACY_PROFILE_IDS = {'whalya': 'whalory', 'whalya.en': 'whalory.en', 'whalya.fa': 'whalory.fa'}


def user_profile_dirs():
    """~/.whalory/profiles، بعد پوشه‌ی قدیمیِ ~/.whalya/profiles که فقط خوانده می‌شود، هرگز نوشته نمی‌شود."""
    home = os.path.expanduser('~')
    return [os.path.join(home, '.whalory', 'profiles'), os.path.join(home, '.whalya', 'profiles')]


def find_profile(name):
    """نامِ خالیِ پروفایل (مثلاً whalory) را پیدا می‌کند؛ ترتیبِ SKILL.md:
    ~/.whalory/profiles → ~/.whalya/profiles (قدیمی) → profiles/ → profiles/starters/ → examples/<نام>/ → examples/*/.
    شناسه‌ی قدیمیِ whalya همان whalory است."""
    name = LEGACY_PROFILE_IDS.get(name, name)
    cands = [os.path.join(d, name + '.json') for d in user_profile_dirs()]
    cands += [os.path.join(SKILL_ROOT, 'profiles', name + '.json'),
             os.path.join(SKILL_ROOT, 'profiles', 'starters', name + '.json'),
             os.path.join(SKILL_ROOT, 'examples', name, name + '.json')]
    cands += sorted(glob.glob(os.path.join(SKILL_ROOT, 'examples', '*', name + '.json')))
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def _find_auto():
    d = os.getcwd()
    while True:
        for name in ('voice.json', os.path.join('voice', 'voice.json')):
            c = os.path.join(d, name)
            if os.path.isfile(c):
                return c
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up


def _norm_choice(value, allowed, aliases, alias_rule, what, where, warns):
    if value is None or value == '':
        return 'any'
    v = value.strip().lower() if isinstance(value, str) else value
    if v in allowed:
        return v
    if v in aliases:
        if alias_rule:
            warns.append((alias_rule, '%s «%s» در %s نامِ قدیمی است؛ «%s» بنویس'
                          % (what, value, where, aliases[v])))
        return aliases[v]
    warns.append(('profile-invalid', '%s «%s» در %s ناشناخته است؛ any در نظر گرفته شد (مجاز: %s)'
                  % (what, value, where, '، '.join(allowed))))
    return 'any'


def _norm_dials(dials, where, warns):
    out = {}
    if dials is None:
        return out
    if not isinstance(dials, dict):
        warns.append(('profile-invalid', 'dials در %s باید شیء باشد' % where))
        return out
    for k, v in dials.items():
        k = DIAL_ALIASES.get(k, k)
        if k not in DIAL_RANGES:
            warns.append(('profile-invalid', 'unknown dial in %s: %s' % (where, k)))
            continue
        lo, hi = DIAL_RANGES[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            warns.append(('profile-invalid', 'دکمه‌ی %s در %s عدد نیست: %r' % (k, where, v)))
            continue
        iv = int(round(v))
        if iv < lo or iv > hi:
            warns.append(('profile-invalid', 'دکمه‌ی %s در %s بیرون از %d تا %d است: %s' % (k, where, lo, hi, v)))
            iv = min(hi, max(lo, iv))
        out[k] = iv
    return out


def _norm_limits(src, dst, where, warns):
    for k in ('max_words', 'emoji_max', 'exclaim_max'):
        if k not in src:
            continue
        v = src[k]
        if isinstance(v, bool) or not isinstance(v, int) or v < 0 or (k == 'max_words' and v == 0):
            warns.append(('profile-invalid', '%s در %s باید عددِ صحیحِ مثبت باشد: %r' % (k, where, v)))
            dst.pop(k, None)
        else:
            dst[k] = v


def _norm_words(src, dst, where, warns):
    for k in ('banned', 'avoid', 'allow'):
        if k not in src:
            continue
        v = src[k]
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            warns.append(('profile-invalid', '%s در %s باید فهرستِ واژه باشد' % (k, where)))
            dst[k] = []
        else:
            dst[k] = [x for x in v if x.strip()]


# کلیدهایی که by_lang.<زبان> می‌تواند رویِ سطحِ بالای پروفایل بنشاند (والوری ۳؛ spec §D.6)
BY_LANG_KEYS = ('max_words', 'emoji_max', 'exclaim_max', 'dials', 'register', 'address',
                'banned', 'avoid', 'prefer', 'allow', 'formats')


def merge_by_lang(profile, lang):
    """by_lang[lang] را رویِ سطحِ بالا می‌نشاند (lint_fa با 'fa'، lint_en با 'en').
    عدد و فهرست جایگزین می‌شوند؛ dials و prefer کلید به کلید؛ formats قالب به قالب و درونِ
    هر قالب کلید به کلید. پروفایلِ بی by_lang همان شیء برمی‌گردد."""
    if not isinstance(profile, dict):
        return profile
    bl = profile.get('by_lang')
    sub = bl.get(lang) if isinstance(bl, dict) else None
    if not isinstance(sub, dict) or not sub:
        return profile
    if profile.get('schema_version') == 3:
        return VP.deep_merge(profile, sub)
    p = dict(profile)
    for k in BY_LANG_KEYS:
        if k not in sub:
            continue
        v = sub[k]
        cur = p.get(k)
        if k in ('dials', 'prefer') and isinstance(v, dict) and isinstance(cur, dict):
            merged = dict(cur)
            merged.update(v)
            p[k] = merged
        elif k == 'formats' and isinstance(v, dict) and isinstance(cur, dict):
            merged = dict(cur)
            for fid, fv in v.items():
                if isinstance(fv, dict) and isinstance(merged.get(fid), dict):
                    one = dict(merged[fid])
                    one.update(fv)
                    for nested in ('dials', 'prefer'):
                        if isinstance(merged[fid].get(nested), dict) and isinstance(fv.get(nested), dict):
                            one[nested] = dict(merged[fid][nested])
                            one[nested].update(fv[nested])
                    merged[fid] = one
                else:
                    merged[fid] = fv
            p[k] = merged
        else:
            p[k] = v
    return p


def normalize_profile(profile):
    """پروفایلِ نسخه‌ی ۱ یا ۲ را یکدست می‌کند. هشدارها در '_warnings' می‌مانند.
    کلیدهای انگلیسیِ والوری ۳ (language، variant، spelling و …) پذیرفته و نادیده گرفته می‌شوند؛
    by_lang.fa پیش از یکدست‌سازی رویِ سطحِ بالا می‌نشیند."""
    if not profile:
        return {'_normalized': True, '_warnings': [], 'dials': {}, 'register': 'any', 'address': 'any'}
    if not isinstance(profile, dict):
        raise UserError('profile must be a JSON object')
    if profile.get('_normalized'):
        return profile
    raw = {k: v for k, v in profile.items() if k not in ('_path', '_normalized', '_en_normalized', '_warnings')}
    errors = VP.validate_profile(raw)
    sv = raw.get('schema_version', 1)
    if type(sv) is not int or sv not in (1, 2, 3) or (sv == 3 and errors):
        raise UserError(str(VP.ProfileError(errors)))
    profile = merge_by_lang(profile, 'fa')
    p = dict(profile)
    warns = [('profile-invalid', e['path'] + ': ' + e['message']) for e in errors]
    sv = p.get('schema_version', 1)
    if sv not in (1, 2, 3):
        warns.append(('profile-invalid', 'schema_version «%s» ناشناخته است؛ lint_fa نسخه‌های ۱ تا ۳ را می‌فهمد' % (sv,)))
    p['schema_version'] = sv if isinstance(sv, int) and not isinstance(sv, bool) else 1
    p['register'] = _norm_choice(p.get('register'), REGISTERS, REGISTER_ALIASES, 'profile-register-alias',
                                 'لحنِ', 'پروفایل', warns)
    p['address'] = _norm_choice(p.get('address'), ADDRESSES, ADDRESS_ALIASES, None, 'خطابِ', 'پروفایل', warns)
    p['dials'] = _norm_dials(p.get('dials'), 'پروفایل', warns)
    _norm_limits(profile, p, 'پروفایل', warns)
    _norm_words(profile, p, 'پروفایل', warns)
    if not isinstance(p.get('prefer', {}), dict):
        warns.append(('profile-invalid', 'prefer باید شیءِ «واژه: جایگزین» باشد'))
        p['prefer'] = {}
    brand = p.get('brand') or {}
    if not isinstance(brand, dict):
        warns.append(('profile-invalid', 'brand باید شیء باشد'))
        brand = {}
    brand = dict(brand)
    if not isinstance(brand.get('misspellings', {}) or {}, dict):
        warns.append(('profile-invalid', 'brand.misspellings باید شیءِ «غلط: درست» باشد'))
        brand['misspellings'] = {}
    p['brand'] = brand
    # نسخه‌ی ۲، اختیاری (تصمیمِ D3): املای ثابتِ لاتین برای واژه‌های فارسی
    if 'romanization' in p:
        rom = p.get('romanization')
        if rom is None:
            rom = {}
        if not isinstance(rom, dict) or not all(isinstance(k, str) and k.strip() and isinstance(v, str)
                                                and v.strip() for k, v in rom.items()):
            warns.append(('profile-invalid', 'romanization باید شیءِ «واژه‌ی فارسی: املای لاتین» باشد'))
            rom = {}
        else:
            bad = [k for k, v in rom.items() if HAS_FA.search(v)]
            if bad:
                warns.append(('profile-invalid', 'املای لاتینِ romanization حرفِ فارسی دارد: %s'
                              % '، '.join(bad[:4])))
        p['romanization'] = dict(rom)
    fmts = p.get('formats') or {}
    if not isinstance(fmts, dict):
        warns.append(('profile-invalid', 'formats باید شیءِ «قالب: تنظیم» باشد'))
        fmts = {}
    nf = {}
    for fid, fv in fmts.items():
        where = 'formats.%s' % fid
        if fid not in FORMAT_DEFAULTS:
            warns.append(('profile-invalid', 'قالبِ ناشناخته «%s» در formats؛ شناسه‌های مجاز در --rules' % fid))
        if not isinstance(fv, dict):
            warns.append(('profile-invalid', '%s باید شیء باشد' % where))
            continue
        q = {}
        if 'register' in fv:
            q['register'] = _norm_choice(fv.get('register'), REGISTERS, REGISTER_ALIASES,
                                         'profile-register-alias', 'لحنِ', where, warns)
        if 'address' in fv:
            q['address'] = _norm_choice(fv.get('address'), ADDRESSES, ADDRESS_ALIASES, None, 'خطابِ', where, warns)
        if 'dials' in fv:
            q['dials'] = _norm_dials(fv.get('dials'), where, warns)
        _norm_limits(fv, q, where, warns)
        _norm_words(fv, q, where, warns)
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
    p['_normalized'] = True
    return p


def validate_profile(profile):
    """فهرستِ (قاعده، پیام) برای پروفایلِ خام؛ خالی یعنی سالم."""
    return list(normalize_profile(profile).get('_warnings', []))


def _read_json(path, what):
    text = read_text(path)
    try:
        data = json.loads(text, object_pairs_hook=VP._pairs)
    except ValueError as e:
        line, col = getattr(e, 'lineno', 0), getattr(e, 'colno', 0)
        msg = getattr(e, 'msg', str(e))
        raise UserError('%s JSON معتبر نیست: %s (خطِ %s، ستونِ %s): %s' % (what, path, line, col, msg))
    return data


def load_profile(path):
    """پروفایلِ json را می‌خواند. اگر md داده شد، json هم‌نامِ کنارش (یا voice.json) را
    برمی‌دارد. 'auto': voice.json در پوشه‌ی جاری و بالاتر. نامِ خالی (whalory): جست‌وجو
    در ~/.whalory/profiles، profiles/، profiles/starters/ و examples/."""
    if not path:
        return {}
    if path == 'auto':
        found = _find_auto()
        if not found:
            return {}
        path = found
    path = os.path.expanduser(path)
    if path.lower().endswith('.md'):
        cand = path[:-3] + '.json'
        if not os.path.isfile(cand):
            alt = os.path.join(os.path.dirname(path), 'voice.json')
            if os.path.isfile(alt):
                cand = alt
            else:
                raise UserError('پروفایلِ md برای آدم است؛ lint نسخه‌ی json کنارش را لازم دارد و پیدا نشد: %s' % cand)
        path = cand
    elif not os.path.exists(path) and not os.path.splitext(path)[1] and os.sep not in path and '/' not in path:
        found = find_profile(path)
        if not found:
            raise UserError('پروفایلِ «%s» پیدا نشد (در ~/.whalory/profiles، profiles/، '
                            'profiles/starters/ و examples/ گشتم).' % path)
        path = found
    if os.path.isdir(path):
        raise UserError('پروفایل باید فایل باشد و این مسیر پوشه است: %s' % path)
    if not os.path.exists(path):
        raise UserError('پروفایل پیدا نشد: %s' % path)
    data = _read_json(path, 'پروفایل')
    if not isinstance(data, dict):
        raise UserError('پروفایل باید یک شیءِ JSON باشد: %s' % path)
    if any(k in data for k in ('_path', '_normalized', '_en_normalized', '_warnings')):
        raise UserError('profile files cannot contain reserved runtime keys')
    p = normalize_profile(data)
    p['_path'] = path
    return p


def resolve_settings(profile=None, fmt=None, max_words=None, emoji_max=None, exclaim_max=None):
    """تنظیمِ نهایی (تصمیمِ D1): پرچمِ خطِ فرمان > profile.formats[قالب] (صریح؛ سخت‌تر یا
    آزادتر) > FORMAT_DEFAULTS[قالب] که فقط سخت‌تر می‌کند (کمینه‌ی آن و سراسریِ پروفایل) >
    سراسریِ پروفایل > پیش‌فرضِ دکمه (طولِ جمله ۳ یعنی ۲۴، نشانه‌های پرصدا ۰).
    FORMAT_DEFAULTS هرگز خطاب را تعیین نمی‌کند."""
    p = normalize_profile(profile or {})
    dials = dict(p.get('dials') or {})
    # پیش‌فرضِ لایه‌ی هاب فقط جای پیش‌فرضِ درونی را می‌گیرد (spec 5.9)
    mw = DIAL_WORDS.get(dials.get('sentence_length')) or _hub_param('long-sentence.max_words', DEFAULT_MAX_WORDS)
    em, ex = DIAL_MARKS.get(dials.get('loud_marks'), DIAL_MARKS[DEFAULT_LOUD_MARKS])
    src = {'max_words': 'dial', 'emoji_max': 'dial', 'exclaim_max': 'dial'}
    if 'max_words' in p:
        mw, src['max_words'] = p['max_words'], 'profile'
    if 'emoji_max' in p:
        em, src['emoji_max'] = p['emoji_max'], 'profile'
    if 'exclaim_max' in p:
        ex, src['exclaim_max'] = p['exclaim_max'], 'profile'
    reg, addr = p.get('register') or 'any', p.get('address') or 'any'
    banned = list(p.get('banned') or [])
    avoid = list(p.get('avoid') or [])
    allow = list(p.get('allow') or [])
    note = ''
    if fmt:
        fd = FORMAT_DEFAULTS.get(fmt, {})
        # پیش‌فرضِ قالب فقط سخت‌تر می‌کند: کپشنِ ۲۰ واژه‌ای سقفِ ۱۴ِ پروفایل را بالا نمی‌برد
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
                mw, src['max_words'] = DIAL_WORDS[fdials['sentence_length']], 'profile.formats'
            if 'loud_marks' in fdials:
                em, ex = DIAL_MARKS[fdials['loud_marks']]
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
        if pf.get('register'):
            reg = pf['register']
        if pf.get('address'):
            addr = pf['address']
        banned += pf.get('banned') or []
        avoid += pf.get('avoid') or []
        allow += pf.get('allow') or []
        note = pf.get('note') or fd.get('note', '')
    if max_words:
        mw, src['max_words'] = max_words, 'cli'
    if emoji_max is not None:
        em, src['emoji_max'] = emoji_max, 'cli'
    if exclaim_max is not None:
        ex, src['exclaim_max'] = exclaim_max, 'cli'
    brand = p.get('brand') or {}
    return {'max_words': mw, 'emoji_max': em, 'exclaim_max': ex, 'register': reg, 'address': addr,
            'dials': dials, 'format': fmt or '', 'note': note, 'banned': banned, 'avoid': avoid,
            'allow': allow, 'prefer': dict(p.get('prefer') or {}),
            'misspellings': dict(brand.get('misspellings') or {}), 'profile': p.get('name', ''),
            'romanization': dict(p.get('romanization') or {}),
            'sources': src, 'warnings': list(p.get('_warnings') or [])}


def resolve_limits(profile, max_words=None):
    """سازگاری با نسخه‌ی ۱: (سقفِ واژه، سقفِ ایموجی، سقفِ تعجب، لحن)."""
    s = resolve_settings(profile or {}, max_words=max_words)
    return s['max_words'], s['emoji_max'], s['exclaim_max'], s['register']


# ---------------------------------------------------------------- کانال
_FIELD_PRIORITY = ('body', 'text', 'message', 'caption', 'post', 'description', 'title')
_GSM7 = set('@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !"#¤%&\'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            'ÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà')
_GSM7_EXT = set('^{}\\[~]|€\f')


def load_channels(dirpath=None):
    """همه‌ی data/channels/*.json. پوشه‌ی ناموجود یا فایلِ خراب کار را نمی‌خواباند.
    (کانال‌ها، هشدارها)؛ کلید هم شناسه است و هم «گروه/شناسه»."""
    d = dirpath or CHANNELS_DIR
    chans, warns = {}, []
    if not os.path.isdir(d):
        return chans, warns
    for f in sorted(glob.glob(os.path.join(d, '*.json'))):
        try:
            data = json.loads(read_text(f))
        except (UserError, ValueError) as e:
            warns.append('داده‌ی کانال خوانده نشد: %s (%s)' % (os.path.basename(f), e))
            continue
        if not isinstance(data, dict) or not isinstance(data.get('channels'), dict):
            warns.append('ساختارِ داده‌ی کانال درست نیست: %s' % os.path.basename(f))
            continue
        group = data.get('group') or os.path.splitext(os.path.basename(f))[0]
        for cid, c in data['channels'].items():
            if not isinstance(c, dict):
                continue
            entry = dict(c)
            entry['id'], entry['group'] = cid, group
            chans.setdefault(cid, entry)
            chans['%s/%s' % (group, cid)] = entry
    if _HUB is not None:
        # به‌روزرسانیِ ماشینیِ لایه‌ی هاب: max_chars و status؛ needs-review خطا را هشدار می‌کند (spec 5.9)
        for key, upd in _HUB.channel_updates().items():
            cid, _, field = key.partition('.')
            spec = ((chans.get(cid) or {}).get('fields') or {}).get(field)
            if isinstance(spec, dict):
                for k in ('max_chars', 'status', 'verified_on', 'checked_on'):
                    if k in upd:
                        spec[k] = upd[k]
    return chans, warns


def resolve_channel(spec, dirpath=None):
    """«شناسه[.فیلد]» یا «گروه/شناسه[.فیلد]» → تنظیمِ کانال؛ نبود → UserError."""
    chans, warns = load_channels(dirpath)
    cid, _, field = spec.partition('.')
    ch = chans.get(cid)
    if ch is None:
        ids = sorted(k for k in chans if '/' not in k)
        where = dirpath or CHANNELS_DIR
        if not ids:
            raise UserError('داده‌ی کانال پیدا نشد (%s)؛ --channel بی‌داده کار نمی‌کند.' % where)
        raise UserError('کانالِ «%s» شناخته نشد. کانال‌های موجود: %s' % (cid, '، '.join(ids)))
    fields = ch.get('fields') if isinstance(ch.get('fields'), dict) else {}
    if field:
        if field not in fields:
            raise UserError('کانالِ «%s» فیلدِ «%s» ندارد. فیلدها: %s' % (cid, field, '، '.join(fields) or '—'))
    elif fields:
        field = next((f for f in _FIELD_PRIORITY if f in fields), None) or next(iter(fields))
    spec_f = fields.get(field) if field else None
    return {'id': ch['id'], 'group': ch.get('group', ''), 'name': ch.get('name_fa') or ch.get('name_en') or cid,
            'name_en': ch.get('name_en') or ch.get('name_fa') or cid,
            'specs': dict((k, v) for k, v in fields.items() if isinstance(v, dict)),
            'kind': ch.get('kind') or '',
            'format_id': ch.get('format_id') or '', 'field': field or '', 'spec': spec_f or {},
            'fields': list(fields), 'field_given': bool(spec.partition('.')[2]), 'load_warnings': warns}


def sms_segments(text):
    """(پاره، واحد، سقفِ یک‌پاره، هر پاره در چندپاره، کدگذاری). فارسی یونیکد است:
    یک‌پاره تا ۷۰، در چندپاره هر پاره ۶۷."""
    if all(c in _GSM7 or c in _GSM7_EXT for c in text):
        units = sum(2 if c in _GSM7_EXT else 1 for c in text)
        single, part, enc = 160, 153, 'gsm7'
    else:
        units = len(text.encode('utf-16-le')) // 2
        single, part, enc = 70, 67, 'ucs2'
    if units == 0:
        segs = 0
    elif units <= single:
        segs = 1
    else:
        segs = int(math.ceil(units / float(part)))
    return segs, units, single, part, enc


def _channel_check(text, ch):
    """بررسیِ طول با سقفِ کانال. (مسئله‌ها، اطلاعات برای stats)."""
    spec = ch.get('spec') or {}
    t = text.strip()
    unit = (spec.get('unit') or 'char').lower()
    status = (spec.get('status') or 'unverified').lower()
    verified = status == 'verified'
    note = '' if verified else 'سقفِ تأییدنشده'
    info = {'id': ch.get('id'), 'group': ch.get('group'), 'field': ch.get('field'), 'unit': unit,
            'chars': len(t), 'max_chars': spec.get('max_chars'), 'visible_chars': spec.get('visible_chars'),
            'status': status, 'verified_on': spec.get('verified_on', ''), 'source': spec.get('source', ''),
            'note': note}
    issues = []
    tail = ' (%s)' % note if note else ''
    level = ERROR if verified else WARN
    label = '%s%s' % (ch.get('id'), '.' + ch['field'] if ch.get('field') else '')
    mx = spec.get('max_chars')
    if unit == 'segment':
        segs, units, single, part, enc = sms_segments(t)
        info.update({'segments': segs, 'units': units, 'encoding': enc, 'single': single, 'per_part': part})
        limit_seg = spec.get('max_segments')
        if limit_seg is None and isinstance(mx, int) and 0 < mx <= 20:
            limit_seg = mx          # سقفِ کوچک در واحدِ segment یعنی تعدادِ پاره
        if isinstance(limit_seg, int) and segs > limit_seg:
            issues.append((level, 'channel-length',
                           '%s: %d پاره (%d واحد، %s)؛ سقف %d پاره. یک‌پاره تا %d، در چندپاره هر پاره %d%s'
                           % (label, segs, units, enc, limit_seg, single, part, tail)))
        elif isinstance(mx, int) and mx > 20 and units > mx:
            issues.append((level, 'channel-length', '%s: %d واحد؛ سقف %d (%d پاره)%s'
                           % (label, units, mx, segs, tail)))
    else:
        n = len(t.encode('utf-8')) if unit == 'byte' else len(t)
        info['count'] = n
        seg_note = ''
        if ch.get('kind') == 'sms':    # پیامک با واحدِ نویسه: شمارِ پاره هم گزارش می‌شود
            segs, units, single, part, enc = sms_segments(t)
            info.update({'segments': segs, 'units': units, 'encoding': enc, 'single': single, 'per_part': part})
            seg_note = ' (%d پاره؛ %s: یک‌پاره تا %d، در چندپاره هر پاره %d)' % (segs, enc, single, part)
        if isinstance(mx, int) and n > mx:
            issues.append((level, 'channel-length', '%s: %d %s؛ سقف %d، %d تا زیادی%s%s'
                           % (label, n, 'بایت' if unit == 'byte' else 'نویسه', mx, n - mx, seg_note, tail)))
        vis = spec.get('visible_chars')
        if isinstance(vis, int) and len(t) > vis:
            issues.append((WARN, 'channel-visible', '%s: فقط %d نویسه‌ی اول پیش از «بیشتر» دیده می‌شود؛ '
                           'حرفِ اصلی را جلو بیاور%s' % (label, vis, tail)))
    return issues, info


# ---------------------------------------------------------------- هسته‌ی سنجش
# پسوندهایی که پس از نیم‌فاصله هنوز همان واژه‌اند: جمع، اضافه، نکره، ضمیرِ پیوسته، صفتِ برتر
_SUFFIXES = '|'.join(sorted(['ها', 'های', 'هایی', 'هایم', 'هایت', 'هایش', 'هایمان', 'هایتان', 'هایشان',
                             'هام', 'هات', 'هاش', 'هامون', 'هاتون', 'هاشون', 'هاست',
                             'ی', 'ای', 'یی', 'ام', 'ات', 'اش', 'مان', 'تان', 'شان', 'مون', 'تون', 'شون',
                             'ست', 'است', 'تر', 'ترین', 'اند', 'ایم', 'اید'], key=len, reverse=True))


@functools.lru_cache(maxsize=4096)
def word_rx(w, tolerant=False):
    """واژه با مرزِ فارسی؛ پسوند بعد از نیم‌فاصله («آیتم‌ها») و کسره‌ی اضافه هنوز همان واژه است.
    tolerant: کسره اختیاری، نیم‌فاصله = فاصله یا هیچ، ي/ی و ك/ک یکی."""
    w = w.strip()
    latin = bool(re.match(r'[A-Za-z0-9]', w))
    if tolerant:
        parts = []
        for ch in w:
            if ch == '\u0650':
                parts.append('\u0650?')
            elif ch == ZWNJ:
                parts.append('\u0650?[\u200c ]?')
            elif ch == ' ':
                parts.append('\u0650?\\s+')
            elif ch in 'یيى':
                parts.append('[یيى]')
            elif ch in 'کك':
                parts.append('[کك]')
            else:
                parts.append(re.escape(ch))
        core = ''.join(parts)
    else:
        core = re.escape(w)
    left = '(?<![%s%s])' % (FA_LETTERS, ZWNJ)
    # \u067e\u0633 \u0627\u0632 \u0646\u06cc\u0645\u200c\u0641\u0627\u0635\u0644\u0647 \u0641\u0642\u0637 \u067e\u0633\u0648\u0646\u062f \u0647\u0645\u0627\u0646 \u0648\u0627\u0698\u0647 \u0627\u0633\u062a (\u00ab\u0622\u06cc\u062a\u0645\u200c\u0647\u0627\u00bb\u060c \u00ab\u062e\u0627\u0646\u0647\u200c\u06cc\u00bb)\u061b \u00ab\u0627\u0635\u0627\u0644\u062a\u200c\u0628\u0627\u0632\u06cc\u00bb \u0648\u0627\u0698\u0647\u200c\u06cc \u062f\u06cc\u06af\u0631\u06cc \u0627\u0633\u062a
    right = '\u0650?(?:(?![%s%s])|%s(?:%s)(?![%s%s]))' % (FA_LETTERS, ZWNJ, ZWNJ, _SUFFIXES, FA_LETTERS, ZWNJ)
    if latin:
        left += '(?<![A-Za-z0-9_])'
    if re.search(r'[A-Za-z0-9]$', w):
        right = '(?![A-Za-z0-9_])' + right
    return re.compile(left + core + right)


@functools.lru_cache(maxsize=512)
def lx_pid(group, phrase):
    """شناسه‌ی عبارتِ واژه‌نامه (spec 5.5): lx-fa- و ۱۰ نویسه‌ی اولِ SHA-256(fa|گروه|NFC(عبارت))."""
    text = unicodedata.normalize('NFC', phrase)
    return 'lx-fa-' + hashlib.sha256(('fa|%s|%s' % (group, text)).encode('utf-8')).hexdigest()[:10]


_HUB_RX = {}


def _hub_rx():
    """عبارت‌های هاب (ht-) در یک الگوی جایگزینی، بلندتر اول، هر کدام با re.escape و همان مرزِ
    word_rx (spec 5.9، 7.5). (الگو، {عبارت: (شناسه، وضعیت)}) یا None."""
    if _HUB is None:
        return None
    phrases = tuple(_HUB.hub_phrases('fa'))
    if not phrases:
        return None
    got = _HUB_RX.get(phrases)
    if got is None:
        alt = '|'.join(re.escape(p) for p, _pid, _st in phrases)
        left = '(?<![%s%s])' % (FA_LETTERS, ZWNJ)
        right = 'ِ?(?:(?![%s%s])|%s(?:%s)(?![%s%s]))' % (FA_LETTERS, ZWNJ, ZWNJ, _SUFFIXES, FA_LETTERS, ZWNJ)
        got = (re.compile(left + '(' + alt + ')' + right), dict((p, (pid, st)) for p, pid, st in phrases))
        _HUB_RX.clear()
        _HUB_RX[phrases] = got
    return got


def _hub_issues(issues):
    """شدتِ لایه‌ی هاب و کنار گذاشتنِ یافته‌های پنهان (spec 5.9)؛ بی لایه فقط فیلدهای درونی می‌روند."""
    if _HUB is not None:
        return _HUB.apply_issues('fa', issues)
    for x in issues:
        x.pop('_pid', None)
        x.pop('_end', None)
    return issues


def _hub_param(name, default):
    return _HUB.param('fa', name, default) if _HUB is not None else default


def _hub_stats(stats):
    return _HUB.stamp_stats('fa', stats) if _HUB is not None else stats


def _issue(line, col, code, level, msg, snippet='', key=None, span=None):
    ex = (snippet or '').replace(MASK, ' ').replace(BLOCK, ' ').strip()[:60]
    return {'line': line, 'col': col, 'key': key, 'code': code, 'rule': code, 'level': level,
            'severity': level, 'message': msg, 'text': ex, 'excerpt': ex, '_span': span}


def _compiled(st):
    c = st.get('_rx')
    if c is None:
        c = {
            'misspell': [(word_rx(k), k, v) for k, v in st['misspellings'].items() if k.strip()],
            'banned': [(word_rx(w, True), w) for w in dict.fromkeys(st['banned'])],
            'avoid': [(word_rx(w, True), w) for w in dict.fromkeys(st['avoid'])],
            'jargon': [(word_rx(w, True), w) for w in JARGON]
            if 0 < (st['dials'].get('jargon') or 0) <= 2 else [],
        }
        st['_rx'] = c
    return c


def _register_issues(body, st):
    """لحنِ نویسنده. متنِ داخلِ «…» حرفِ کسِ دیگر یا نمونه است و شمرده نمی‌شود."""
    out = []

    def uniq(found):
        return sorted({x[0] if isinstance(x, tuple) else x for x in found})[:4]

    body = _QUOTED.sub(lambda m: MASK * len(m.group(0)), body)
    c, f = COLLOQ.findall(body), FORMAL.findall(body)
    reg = st['register']
    if reg == 'formal' and c:
        out.append(('register', 'پروفایل نوشتاری می‌خواهد؛ نشانه‌ی محاوره: %s' % '، '.join(uniq(c))))
    elif reg == 'colloquial' and f:
        out.append(('register', 'پروفایل محاوره‌ی نوشتاری می‌خواهد؛ نشانه‌ی نوشتاری: %s' % '، '.join(uniq(f))))
    elif c and f:
        out.append(('mixed-register', 'لحنِ مخلوط؛ محاوره (%s) کنارِ نوشتاری (%s)'
                    % ('، '.join(uniq(c)), '، '.join(uniq(f)))))
    return out


_QUOTED = re.compile(r'«[^«»\n]*»')


def _address_issues(items, st):
    """items: (سطر، کلید، متنِ سطر، متنِ خام). یک هشدار برای هر سطری که خطابِ دیگر دارد."""
    want = st['address']
    if want not in ('shoma', 'to'):
        return []
    other = '«تو»' if want == 'shoma' else '«شما»'
    mine = '«شما»' if want == 'shoma' else '«تو»'
    out = []
    for line, key, ln, raw in items:
        src = _QUOTED.sub(lambda m: MASK * len(m.group(0)), ln)
        found = address_matches(src, 'to' if want == 'shoma' else 'shoma')
        if not found:
            continue
        forms = []
        for _a, _b, f in found:
            if f not in forms:
                forms.append(f)
        a, b = found[0][0], found[0][1]
        out.append(_issue(line, a + 1, 'address', WARN,
                          'خطابِ پروفایل %s است ولی اینجا %s آمده: %s' % (mine, other, '، '.join(forms[:4])),
                          raw[max(0, a - 15):b + 15], key, (a, b)))
    return out


_PS_COUNT = []   # [تابع یا None] پس از اولین تلاش


def _ps_count_address():
    """profile_stats.count_address اگر کنارِ همین فایل باشد و درست جواب دهد؛ وگرنه None."""
    if _PS_COUNT:
        return _PS_COUNT[0]
    fn = None
    try:
        path = os.path.join(HERE, 'profile_stats.py')
        mod = sys.modules.get('profile_stats')
        main = sys.modules.get('__main__')
        if mod is None and os.path.abspath(getattr(main, '__file__', '') or '') == os.path.abspath(path):
            mod = main
        if mod is None and os.path.isfile(path):
            import importlib.util
            if __name__ == '__main__' and 'lint_fa' not in sys.modules:
                sys.modules['lint_fa'] = sys.modules['__main__']   # profile_stats همین lint را بگیرد
            spec = importlib.util.spec_from_file_location('profile_stats', path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules['profile_stats'] = mod
            try:
                spec.loader.exec_module(mod)
            except Exception:
                sys.modules.pop('profile_stats', None)
                raise
        cand = getattr(mod, 'count_address', None) if mod is not None else None
        if callable(cand):
            probe = cand('کیک رو تو فر بذارید و تو خونه بخورین. خودت بیا.')
            ev = probe.get('evidence') if isinstance(probe, dict) else None
            if isinstance(ev, dict) and probe.get('shoma') and probe.get('to') \
                    and 'تو' not in (ev.get('to') or {}):
                fn = cand
    except Exception:
        fn = None
    _PS_COUNT.append(fn)
    return fn


def address_matches(src, which):
    """شکل‌های خطابِ which ('to' یا 'shoma') در یک سطر: فهرستِ (آغاز، پایان، شکل)، به ترتیب.
    اگر profile_stats باشد شمارش از count_address است و فقط جا از این‌جا پیدا می‌شود."""
    fn = _ps_count_address()
    if fn is not None:
        try:
            res = fn(src)
            if not res.get(which):
                return []
            ev = (res.get('evidence') or {}).get(which) or {}
            out = []
            for form in ev:
                m = word_rx(form, True).search(src) if form.strip() else None
                out.append((m.start(), m.end(), form) if m else (0, 0, form))
            return sorted(out)
        except Exception:
            pass
    if which == 'to':
        out = [(m.start(), m.end(), m.group(0).strip()) for m in ADDRESS_TO.finditer(src)]
        out += [(a, b, 'تو') for a, b in _to_pronouns(src)]
    else:
        out = [(m.start(), m.end(), m.group(0).strip()) for m in ADDRESS_SHOMA.finditer(src)]
    return sorted(out)


def _sentence_spans(ln):
    """(آغاز، پایان) هر جمله در سطر."""
    spans, pos = [], 0
    for m in _SENT_BOUND.finditer(ln):
        spans.append((pos, m.start()))
        pos = m.end()
    spans.append((pos, len(ln)))
    return spans


_KE = re.compile(r'(?<!%s)که(?!%s)' % (W, W))
_RA = re.compile(r'(?<!%s)را(?!%s)' % (W, W))
# سرِ بندِ فهرست: نقل‌قول (>)، بولت (- * + •)، شماره (1. ۱) ۲-)، چک‌باکس ([ ] [x])
_LIST_LEAD = re.compile(
    r'^[ \t]*(?:>[ \t]?)*[ \t]*(?P<mark>(?:[-*+\u2022]|[0-9\u06F0-\u06F9\u0660-\u0669]{1,3}[.)\-])[ \t]+'
    r'(?:\[[ xX]\][ \t]+)?)?')
_TABLE_SEP = re.compile(r'^[ \t]*(?:\|[ \t]*)?:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*(?:\|[ \t]*)?$')
_PIPE = re.compile(r'(?<!\\)\|')


def _table_lines(lines, md=False):
    """(سطرهای جدول، سطرهای جداکننده) به شکلِ اندیسِ صفرمبنا. سطری که با | شروع شود همیشه
    جدول است؛ در markdown جدولِ بی‌| آغازین هم از روی سطرِ جداکننده (--- | ---) شناخته می‌شود."""
    seps = set(i for i, ln in enumerate(lines) if '|' in ln and _TABLE_SEP.match(ln))
    rows = set(i for i, ln in enumerate(lines) if ln.lstrip().startswith('|'))
    if md:
        for i in seps:
            if i > 0 and _PIPE.search(lines[i - 1]):
                rows.add(i - 1)
            j = i + 1
            while j < len(lines) and lines[j].strip() and _PIPE.search(lines[j]):
                rows.add(j)
                j += 1
    return rows - seps, seps


def _table_cells(ln):
    """بازه‌ی (آغاز، پایان)ِ هر خانه‌ی ناتهیِ یک سطرِ جدول؛ «\\|» جداکننده نیست."""
    cuts = [-1] + [m.start() for m in _PIPE.finditer(ln)] + [len(ln)]
    out = []
    for a, b in zip(cuts, cuts[1:]):
        a += 1
        while a < b and ln[a] in ' \t':
            a += 1
        while b > a and ln[b - 1] in ' \t\r':
            b -= 1
        if b > a:
            out.append((a, b))
    return out


_BQ = re.compile(r'^[ \t]{0,3}>[ \t]?')


def _quote_blocks(lines):
    """(بلوک‌های نقل‌قول، سطرهای بیرونِ آن‌ها). هر بلوک (سطرِ آغاز، متن) است؛ سطرِ بلوک در
    فهرستِ دوم خالی می‌شود تا شماره‌ی سطرها بماند."""
    blocks, own, cur = [], [], None
    for i, ln in enumerate(lines, 1):
        m = _BQ.match(ln)
        if m:
            own.append('')
            if cur is None:
                cur = (i, [])
                blocks.append(cur)
            cur[1].append(_BQ.sub('', ln))
        else:
            own.append(ln)
            cur = None
    return [(a, '\n'.join(b)) for a, b in blocks], own


def _check(raw_lines, lines, st, mode='doc', key=None, kind='text'):
    """سنجشِ سطرها. mode: 'doc' برای متن، 'string' برای یک مقدارِ locale."""
    issues = []

    def add(ln, col, code, level, msg, snippet='', span=None):
        issues.append(_issue(ln, col, code, level, msg, snippet, key, span))

    def around(src, a, b):
        return src[max(0, a - 15):b + 15]

    pre_lines = lines
    placeholders = sum(len(PLACEHOLDER.findall(ln)) for ln in lines)
    # متنِ داخلِ [کروشه] جای خالیِ عمدی است؛ پوشانده می‌شود تا ستون‌ها بمانند
    lines = [PLACEHOLDER.sub(lambda m: MASK * len(m.group(0)), ln) for ln in lines]
    lines = [_CORE_SUFFIX.sub(lambda m: MASK * len(m.group(0)), ln) for ln in lines]
    allow = set(w.strip() for w in st['allow'])
    rx = _compiled(st)
    prefer = st['prefer']
    fmt = st.get('format') or ''
    hub_rx = _hub_rx()

    emoji_lead = []
    for i, ln in enumerate(lines, 1):
        raw = raw_lines[i - 1] if i - 1 < len(raw_lines) else ln
        for code, level, prx, msg in PATTERNS:
            src = pre_lines[i - 1] if code == 'link-here' else ln
            flt = PATTERN_FILTERS.get(code)
            for m in prx.finditer(src):
                if flt and not flt(src, m):
                    continue
                s = m.start('at') if 'at' in prx.groupindex else m.start()
                add(i, s + 1, code, level, msg, around(raw, s, m.end()), (s, m.end()))
        for group, words in LEXICON.items():
            for w0 in words:
                w = w0.strip()
                if w in allow:
                    continue
                for m in word_rx(w).finditer(ln):
                    add(i, m.start() + 1, 'lexicon', WARN,
                        'واژه‌ی %s: «%s»؛ با جزئیات عوض کن یا حذف کن' % (group, w),
                        around(raw, m.start(), m.end()), (m.start(), m.end()))
                    issues[-1]['_pid'] = lx_pid(group, w0)
        if hub_rx is not None:
            try:
                for m in hub_rx[0].finditer(ln):
                    pid, state = hub_rx[1].get(m.group(1), (None, None))
                    if pid and m.group(1) not in allow:
                        add(i, m.start() + 1, 'hub-tell', ERROR if state == 'error' else WARN,
                            _HUB.HUB_MESSAGE['fa'], around(raw, m.start(), m.end()), (m.start(), m.end()))
                        issues[-1]['_pid'] = pid
            except Exception:  # noqa: BLE001  (spec 5.8 step 10: built-in rules only for this call)
                hub_rx = None
                _HUB.note_exception()
                issues = [x for x in issues if x['code'] != 'hub-tell']
        for r, bad, good in rx['misspell']:
            for m in r.finditer(ln):
                add(i, m.start() + 1, 'brand-spelling', ERROR,
                    'املای نامِ برند «%s»؛ درستش «%s»' % (bad, good), around(raw, m.start(), m.end()),
                    (m.start(), m.end()))
        for r, w in rx['banned']:
            for m in r.finditer(ln):
                add(i, m.start() + 1, 'profile-banned', ERROR,
                    'واژه‌ی ممنوعِ پروفایل: «%s»' % w, around(raw, m.start(), m.end()), (m.start(), m.end()))
        for r, w in rx['avoid']:
            for m in r.finditer(ln):
                hint = '؛ به‌جایش «%s»' % prefer[w] if w in prefer else ''
                add(i, m.start() + 1, 'profile-avoid', WARN,
                    'واژه‌ی «نگو»ی پروفایل: «%s»%s' % (w, hint), around(raw, m.start(), m.end()),
                    (m.start(), m.end()))
        for r, w in rx['jargon']:
            if w in allow:
                continue
            for m in r.finditer(ln):
                add(i, m.start() + 1, 'jargon', WARN,
                    'واژه‌ی فرنگیِ تخصصی «%s»؛ پروفایل jargon=%s می‌خواهد' % (w, st['dials'].get('jargon')),
                    around(raw, m.start(), m.end()), (m.start(), m.end()))
        # قاعده‌های سطری
        m = _HEADING_SUMMARY.match(ln)
        if m:
            add(i, m.start('at') + 1, 'final-word', WARN, 'تیترِ کلیشه‌ی «جمع‌بندی»؛ حرفِ آخر را بی‌تیتر بزن',
                raw, (m.start('at'), m.end('at')))
        if fmt == 'caption' and (_MD_HEADER.match(ln) or _BOLD_LINE.match(ln)):
            add(i, 1, 'caption-header', WARN, 'تیتر یا سطرِ پُررنگ داخلِ کپشن؛ کپشن تیتر ندارد', raw)
        m = _EMOJI_LEAD.match(ln)
        if m and HAS_FA.search(ln[m.end():]) or (m and re.search(r'[A-Za-z]', ln[m.end():])):
            emoji_lead.append((i, m.end(), raw))
    if len(emoji_lead) >= 2:
        for i, e, raw in emoji_lead:
            add(i, 1, 'emoji-bullet', WARN, 'ایموجی به‌جای بولت در سرِ سطر؛ فهرست را با خطِ فاصله یا عدد بساز',
                raw[:40], (0, e))

    # بلوکِ نقل‌قول (>) در markdown نمونه یا حرفِ کسِ دیگر است: در سقفِ تعجب و ایموجی و لحنِ
    # نویسنده نمی‌آید؛ هر بلوک جدا فقط برای لحنِ مخلوط سنجیده می‌شود.
    quotes, own = _quote_blocks(lines) if kind == 'md' else ([], lines)
    body = '\n'.join(own)
    bangs = len(re.findall(r'[!！]', body))
    if bangs > st['exclaim_max']:
        add(0, 0, 'bangs', WARN, 'علامتِ تعجب %d بار؛ سقف %d' % (bangs, st['exclaim_max']))
    emo = EMOJI.findall(body)
    if len(emo) > st['emoji_max']:
        add(0, 0, 'emoji', WARN, 'ایموجی %d بار؛ سقف %d' % (len(emo), st['emoji_max']), ' '.join(emo[:6]))

    if mode == 'doc':
        for code, msg in _register_issues(body, st):
            add(0, 0, code, WARN, msg)
        for first, block in quotes:
            for code, msg in _register_issues(block, dict(st, register='any')):
                add(first, 0, code, WARN, msg + '؛ در نقل‌قول')
        issues.extend(_address_issues([(i, key, ln, raw_lines[i - 1] if i - 1 < len(raw_lines) else ln)
                                       for i, ln in enumerate(lines, 1)], st))

    # جمله‌ها: نثر، بندِ فهرست (بی‌نشانه‌ی - * + ۱. [x]) و خانه‌ی جدول (هر خانه جدا)
    sents = []
    rows, seps = _table_lines(lines, kind == 'md')
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if not s or s.startswith('#') or (i - 1) in seps:
            continue
        raw = raw_lines[i - 1] if i - 1 < len(raw_lines) else ln
        if (i - 1) in rows:
            pieces, tag = _table_cells(ln), 'cell'
        else:
            # نشانه از سطرِ خام: «[ ]»ِ چک‌باکس در سطرِ پوشانده جای‌نگهدار شده است
            lead = _LIST_LEAD.match(raw if len(raw) == len(ln) else ln)
            tag = 'item' if lead.group('mark') else 'prose'
            if ln[lead.end():].lstrip().startswith('#'):
                continue
            pieces = [(lead.end(), len(ln.rstrip()))]
        for a0, b0 in pieces:
            seg = ln[a0:b0]
            for a, b in _sentence_spans(seg):
                part = seg[a:b]
                words = WORD.findall(part)
                if words:
                    sents.append((i, raw[a0 + a:a0 + b], words, part, tag))

    for i, rpart, words, part, _tag in sents:
        if len(words) > st['max_words']:
            add(i, 0, 'long-sentence', WARN,
                'جمله‌ی %d واژه‌ای؛ سقف %d' % (len(words), st['max_words']), rpart)
        if len(_KE.findall(part)) >= 3:
            add(i, 0, 'ke-chain', WARN, 'زنجیره‌ی «که»؛ جمله را بشکن', rpart)
        if len(_RA.findall(part)) >= 2:
            add(i, 0, 'ra-chain', WARN, 'دو «را» در یک جمله', rpart)

    prose = [x for x in sents if x[4] == 'prose']
    if mode == 'doc':
        if prose and prose[0][3].strip().endswith('؟'):
            add(prose[0][0], 0, 'rhetorical-open', WARN, 'شروع با سؤالِ بلاغی', prose[0][1])

        # خانه‌ی جدول فیلد است و خواندنِ پشتِ هم ندارد: خانه‌های یک ردیف نمونه‌های یک الگو هستند و
        # خانه‌های یک ستون برچسب و منبعِ تکراری. خانه و بندِ یکی‌دوواژه‌ای زنجیره را می‌بُرند.
        def eligible(x):
            return x[4] == 'prose' or (x[4] == 'item' and len(x[2]) >= 3)

        for k in range(len(sents) - 2):
            trio = sents[k:k + 3]
            if all(eligible(x) for x in trio) and trio[0][2][0] == trio[1][2][0] == trio[2][2][0]:
                add(sents[k][0], 0, 'same-opening', WARN,
                    'سه جمله‌ی پیاپی با «%s» شروع شده‌اند' % trio[0][2][0], sents[k][1])
        lens = [len(x[2]) for x in prose]
        if len(lens) >= 5 and max(lens) - min(lens) <= 4:
            add(0, 0, 'flat-rhythm', WARN, 'طولِ جمله‌ها تقریباً یکسان است؛ ریتم را بشکن')
    return issues, {'lens': [len(x[2]) for x in sents], 'placeholders': placeholders}


# ترتیبِ ماندن وقتی چند قاعده‌ی واژه‌ای یک جا را گرفته‌اند
_WORD_RANK = {'brand-spelling': 0, 'profile-banned': 1, 'profile-avoid': 2, 'jargon': 3,
              'demo-word': 4, 'lexicon': 5}
_ORDER = {ERROR: 0, WARN: 1}


def _finalize(issues):
    """تکراری‌ها را برمی‌دارد و مرتب می‌کند. «آزمایشی» که هم ممنوعِ پروفایل است و هم
    demo-word فقط یک بار گزارش می‌شود."""
    out, seen = [], set()
    kept = {}   # (سطر، کلید) → بازه‌های واژه‌ای که ماندند
    ranked = sorted(issues, key=lambda x: (_WORD_RANK.get(x['code'], -1), _ORDER[x['level']]))
    for x in ranked:
        ident = (x['line'], x.get('key'), x['col'], x['code'], x['message'])
        if ident in seen:
            continue
        span = x.get('_span')
        if x['code'] in _WORD_RANK and span and x['line']:
            k = (x['line'], x.get('key'))
            if any(span[0] < b and a < span[1] for a, b in kept.get(k, [])):
                continue
            kept.setdefault(k, []).append(span)
        seen.add(ident)
        out.append(x)
    out.sort(key=lambda x: (_ORDER[x['level']], x['line'] or 0, x.get('key') or '', x['col'] or 0))
    for x in out:
        span = x.pop('_span', None)
        if span:
            x['_end'] = span[1] + 1         # درونی، برای hub_mine؛ _hub_issues پیش از خروجی برمی‌دارد
    return out


def _profile_issues(st):
    return [_issue(0, 0, code, WARN, msg) for code, msg in st.get('warnings', [])]


def _make_stats(issues, lens, st, kind, placeholders, extra=None):
    stats = {'sentences': len(lens),
             'avg_words': round(sum(lens) / float(len(lens)), 1) if lens else 0,
             'max_words': st['max_words'],
             'emoji_max': st['emoji_max'],
             'exclaim_max': st['exclaim_max'],
             'register': st['register'],
             'address': st['address'],
             'format': st.get('format') or '',
             'profile': st.get('profile', ''),
             'placeholders': placeholders,
             'kind': kind,
             'errors': sum(1 for x in issues if x['level'] == ERROR),
             'warnings': sum(1 for x in issues if x['level'] == WARN)}
    if extra:
        stats.update(extra)
    return stats


def lint(text, md=False, max_words=None, profile=None, fmt=None, channel=None, kind=None, settings=None):
    """متن را می‌سنجد. (مسئله‌ها، آمار). هر مسئله: line، col، key، rule/code،
    severity/level، message، excerpt/text. channel خروجیِ resolve_channel است."""
    kind = kind or ('md' if md else 'text')
    p = normalize_profile(profile or {})
    if settings is None:
        f = fmt or (channel or {}).get('format_id') or None
        settings = resolve_settings(p, f, max_words)
    st = settings
    if kind == 'locale':
        return lint_locale(text, profile=p, settings=st, channel=channel)
    if kind == 'csv':
        return lint_csv(text, profile=p, settings=st, channel=channel)
    text = clean_text(text)
    masked = mask_prose(text, kind)
    raw_lines, lines = text.split('\n'), masked.split('\n')
    issues, info = _check(raw_lines, lines, st, 'doc', kind=kind)
    issues = _profile_issues(st) + issues
    extra = {}
    if channel:
        ch_issues, ch_info = _channel_check(text, channel)
        issues += [_issue(0, 0, code, level, msg) for level, code, msg in ch_issues]
        extra['channel'] = ch_info
    issues = _hub_issues(_finalize(issues))
    return issues, _hub_stats(_make_stats(issues, info['lens'], st, kind, info['placeholders'], extra))


# ---------------------------------------------------------------- فایلِ locale
_JSON_STR = re.compile(r'"(?:[^"\\\n]|\\.)*"')
_JSON_LIT = re.compile(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null')


class _LineIndex(object):
    def __init__(self, text):
        self.starts = [0] + [m.end() for m in re.finditer('\n', text)]

    def line(self, pos):
        return bisect.bisect_right(self.starts, pos)


def _json_entries(text):
    try:
        json.loads(text)
    except ValueError as e:
        raise UserError('JSON معتبر نیست (خطِ %s، ستونِ %s): %s'
                        % (getattr(e, 'lineno', '?'), getattr(e, 'colno', '?'), getattr(e, 'msg', e)))
    idx = _LineIndex(text)
    n = len(text)
    out = []

    def ws(i):
        while i < n and text[i] in ' \t\r\n':
            i += 1
        return i

    def keypath(path):
        s = ''
        for k in path:
            s += '[%d]' % k if isinstance(k, int) else (k if not s else '.' + k)
        return s

    def value(i, path, skip):
        i = ws(i)
        c = text[i]
        if c == '{':
            i = ws(i + 1)
            if text[i] == '}':
                return i + 1
            while True:
                i = ws(i)
                m = _JSON_STR.match(text, i)
                k = json.loads(m.group(0))
                i = ws(m.end())
                i += 1  # ':'
                i = value(i, path + [k], skip or k.startswith('@'))
                i = ws(i)
                if text[i] == ',':
                    i += 1
                    continue
                return i + 1
        if c == '[':
            i = ws(i + 1)
            if text[i] == ']':
                return i + 1
            j = 0
            while True:
                i = value(i, path + [j], skip)
                i = ws(i)
                j += 1
                if text[i] == ',':
                    i += 1
                    continue
                return i + 1
        if c == '"':
            m = _JSON_STR.match(text, i)
            if not skip:
                out.append((keypath(path), json.loads(m.group(0)), idx.line(i)))
            return m.end()
        m = _JSON_LIT.match(text, i)
        return m.end() if m else i + 1

    value(0, [], False)
    return out


_PO_ESC = {'n': '\n', 't': '\t', 'r': '\r', '"': '"', '\\': '\\'}


def _po_unescape(s):
    return re.sub(r'\\(.)', lambda m: _PO_ESC.get(m.group(1), m.group(1)), s)


def _po_entries(text):
    entries, cur, last = [], {}, None

    def flush():
        if cur:
            entries.append(dict(cur))
        cur.clear()

    for no, ln in enumerate(text.split('\n'), 1):
        s = ln.strip()
        if not s:
            flush()
            last = None
            continue
        if s.startswith('#'):
            continue
        m = re.match(r'(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?)\s+"(.*)"\s*$', s)
        if m:
            kw = m.group(1)
            if kw == 'msgctxt' and cur:
                flush()
            elif kw == 'msgid' and ('msgid' in cur or any(k.startswith('msgstr') for k in cur)):
                flush()
            cur[kw] = _po_unescape(m.group(2))
            cur['@' + kw] = no
            last = kw
            continue
        m = re.match(r'"(.*)"\s*$', s)
        if m and last:
            cur[last] += _po_unescape(m.group(1))
    flush()
    out = []
    for e in entries:
        mid = e.get('msgid', '')
        ctx = e.get('msgctxt')
        if mid == '' and ctx is None:
            continue  # سرصفحه
        key = ('%s|%s' % (ctx, mid) if ctx else mid)[:60]
        strs = sorted(k for k in e if k.startswith('msgstr'))
        any_str = False
        for kw in strs:
            if e[kw]:
                any_str = True
                sub = kw[6:] if kw != 'msgstr' else ''
                out.append((key + sub, e[kw], e.get('@' + kw)))
        if not any_str and HAS_FA.search(mid):
            out.append((key, mid, e.get('@msgid')))   # زبانِ مبدأ فارسی است
    return out


def _attr(attrs, name):
    m = re.search(r'\b%s\s*=\s*("([^"]*)"|\'([^\']*)\')' % re.escape(name), attrs)
    return (m.group(2) if m.group(2) is not None else m.group(3)) if m else None


def _blank_comments(text):
    return _HTML_COMMENT.sub(lambda m: re.sub(r'[^\n]', ' ', m.group(0)), text)


def _android_value(inner):
    v = re.sub(r'<!\[CDATA\[(.*?)\]\]>', lambda m: m.group(1), inner, flags=re.S)
    v = v.strip()
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        v = v[1:-1]
    v = html.unescape(v)
    v = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), v)
    v = re.sub(r'\\(.)', lambda m: {'n': '\n', 't': '\t'}.get(m.group(1), m.group(1)), v)
    return v


def _android_entries(text):
    t = _blank_comments(text)
    idx = _LineIndex(t)
    out = []
    for m in re.finditer(r'<string(?=[\s/>])([^>]*?)(?:/>|>(.*?)</string\s*>)', t, re.S):
        attrs = m.group(1)
        if (_attr(attrs, 'translatable') or '').lower() == 'false' or m.group(2) is None:
            continue
        out.append((_attr(attrs, 'name') or '?', _android_value(m.group(2)), idx.line(m.start(2))))
    for m in re.finditer(r'<plurals\b([^>]*)>(.*?)</plurals\s*>', t, re.S):
        name = _attr(m.group(1), 'name') or '?'
        for it in re.finditer(r'<item\b([^>]*)>(.*?)</item\s*>', m.group(2), re.S):
            q = _attr(it.group(1), 'quantity') or '?'
            out.append(('%s[%s]' % (name, q), _android_value(it.group(2)), idx.line(m.start(2) + it.start(2))))
    for m in re.finditer(r'<string-array\b([^>]*)>(.*?)</string-array\s*>', t, re.S):
        if (_attr(m.group(1), 'translatable') or '').lower() == 'false':
            continue
        name = _attr(m.group(1), 'name') or '?'
        for j, it in enumerate(re.finditer(r'<item\b[^>]*>(.*?)</item\s*>', m.group(2), re.S)):
            out.append(('%s[%d]' % (name, j), _android_value(it.group(1)), idx.line(m.start(2) + it.start(1))))
    out.sort(key=lambda e: e[2])
    return out


def _xliff_entries(text):
    t = _blank_comments(text)
    idx = _LineIndex(t)
    out = []
    for m in re.finditer(r'<(trans-unit|unit)\b([^>]*)>(.*?)</\1\s*>', t, re.S):
        uid = _attr(m.group(2), 'id') or _attr(m.group(2), 'resname') or '?'
        body, base = m.group(3), m.start(3)
        targets = [x for x in re.finditer(r'<target\b[^>]*>(.*?)</target\s*>', body, re.S) if x.group(1).strip()]
        picks = targets or [x for x in re.finditer(r'<source\b[^>]*>(.*?)</source\s*>', body, re.S)
                            if HAS_FA.search(x.group(1))]
        for j, x in enumerate(picks):
            key = uid if len(picks) == 1 else '%s[%d]' % (uid, j)
            out.append((key, html.unescape(x.group(1)), idx.line(base + x.start(1))))
    return out


def _generic_xml_entries(text):
    t = _blank_comments(text)
    idx = _LineIndex(t)
    return [('text@%d' % idx.line(m.start(1)), html.unescape(m.group(1)).strip(), idx.line(m.start(1)))
            for m in re.finditer(r'>([^<>]+)<', t) if HAS_FA.search(m.group(1))]


_STRINGS_TOK = re.compile(r'"(?:[^"\\]|\\.)*"|/\*.*?(?:\*/|\Z)|//[^\n]*', re.S)


def _strings_unescape(s):
    s = re.sub(r'\\[Uu]([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), s)
    return re.sub(r'\\(.)', lambda m: {'n': '\n', 't': '\t', 'r': '\r'}.get(m.group(1), m.group(1)), s)


def _strings_entries(text):
    t = _STRINGS_TOK.sub(lambda m: m.group(0) if m.group(0).startswith('"')
                         else re.sub(r'[^\n]', ' ', m.group(0)), text)
    idx = _LineIndex(t)
    return [(_strings_unescape(m.group(1)), _strings_unescape(m.group(2)), idx.line(m.start(2)))
            for m in re.finditer(r'"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;', t)]


def extract_locale(source, path=None):
    """مقدارهای رشته‌ای یک فایلِ locale: فهرستِ (کلید، مقدار، سطر). کلیدها سنجیده نمی‌شوند.
    extract_locale('fa.json') یا extract_locale(متن، 'fa.json')."""
    if path is None:
        if isinstance(source, str) and '\n' not in source and os.path.isfile(source):
            path, source = source, read_text(source)
        else:
            path = ''
    text = clean_text(source)
    ext = os.path.splitext(path)[1].lower()
    head = text.lstrip()[:400]
    if ext in ('.json', '.arb') or (not ext and head.startswith(('{', '['))):
        return _json_entries(text)
    if ext in ('.po', '.pot'):
        return _po_entries(text)
    if ext == '.strings':
        return _strings_entries(text)
    if ext in ('.xliff', '.xlf'):
        return _xliff_entries(text)
    if ext == '.xml' or head.startswith('<'):
        # اول ریشه: strings.xml اندروید ریشه‌ی <resources> دارد، حتی وقتی <xliff:g> درونش هست
        root = _xml_root(text)
        if root == 'resources' or (root is None and re.search(r'<resources[\s>]', text)):
            return _android_entries(text)
        if root == 'xliff' or (root is None and re.search(r'<(?:xliff|trans-unit)[\s>]', text)):
            return _xliff_entries(text)
        return _generic_xml_entries(text)
    return _json_entries(text)


_XML_PROLOG = re.compile(r'\s*(?:<\?.*?\?>|<!--.*?-->|<!DOCTYPE[^>\[]*(?:\[.*?\])?\s*>)', re.S | re.I)


def _xml_root(text):
    """نامِ عنصرِ ریشه (بی‌پیشوندِ فضای‌نام، کوچک)، یا None اگر پیدا نشد."""
    pos = 0
    while True:
        m = _XML_PROLOG.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
    m = re.compile(r'\s*<([A-Za-z_][\w.\-]*:)?([A-Za-z_][\w.\-]*)').match(text, pos)
    return m.group(2).lower() if m else None


extract_locale_strings = extract_locale

_PH_VALUE = re.compile(
    r'%(?:\d+\$)?[-+#0]*(?:[1-9]\d*)?(?:\.\d+)?(?:hh|h|ll|l|L|q|j|z|t)?[sdifuxXoeEgGcpaA@]'
    r'|%\([A-Za-z_]\w*\)[sdif]|%\{[A-Za-z_]\w*\}|%[A-Za-z_]\w*%'
    r'|\$t\([^()]*\)|@:[\w.]+|\$\{[^{}]*\}|(?<![\w:/]):[A-Za-z_]\w*'
    r'|&[A-Za-z]+;|&#\d+;')
_TAG_VALUE = re.compile(r'</?[A-Za-z][^<>]*>')
_XLIFF_G = re.compile(r'<xliff:g\b[^<>]*?(?:/>|>(?:(?!<xliff:g\b).)*?</xliff:g\s*>)', re.S)


def _mask_braces(s, out):
    n = len(s)

    def msg(i, depth, plural):
        while i < n:
            c = s[i]
            if c == '{':
                i = arg(i, depth)
            elif c == '}':
                if depth > 0:
                    return i
                i += 1
            elif c == '#' and plural:
                out[i] = MASK
                i += 1
            else:
                i += 1
        return i

    def arg(i, depth):
        j = i + 1
        while j < n and s[j] not in '{}':
            j += 1
        if j >= n:
            return n
        parts = [x.strip() for x in s[i + 1:j].split(',')]
        kind = parts[1] if len(parts) > 1 else ''
        if s[j] == '}':
            for k in range(i, j + 1):
                out[k] = MASK
            return j + 1
        if kind in ('plural', 'select', 'selectordinal'):
            for k in range(i, j):
                out[k] = MASK
            k = j
            while k < n and s[k] == '{':
                out[k] = BLOCK
                e = msg(k + 1, depth + 1, kind != 'select')
                if e >= n:
                    return n
                out[e] = BLOCK
                k = e + 1
                while k < n and s[k] not in '{}':
                    out[k] = MASK
                    k += 1
                if k < n and s[k] == '}':
                    out[k] = MASK
                    return k + 1
            return k
        d, k = 0, i
        while k < n:
            if s[k] == '{':
                d += 1
            elif s[k] == '}':
                d -= 1
                if d == 0:
                    break
            k += 1
        for t in range(i, min(k + 1, n)):
            out[t] = MASK
        return k + 1

    msg(0, 0, False)


def mask_value(s):
    """جای‌نگهدار ({x}، {{x}}، %s، %1$s، ICU، برچسبِ html، نشانی) پوشانده می‌شود؛
    متنِ شاخه‌های plural/select می‌ماند. همان طول."""
    out = list(s)

    def mark(a, b, ch=MASK):
        for k in range(a, b):
            if out[k] != '\n':
                out[k] = ch

    for a, b in _url_spans(s):
        mark(a, b)
    for m in _XLIFF_G.finditer(s):     # <xliff:g> یعنی «ترجمه نشود»؛ درونش سنجیده نمی‌شود
        mark(m.start(), m.end())
    for m in _TAG_VALUE.finditer(s):
        mark(m.start(), m.end(), BLOCK if _is_block_tag(m.group(0)) else MASK)
    for m in _PH_VALUE.finditer(s):
        mark(m.start(), m.end())
    s2 = ''.join(out)
    for m in re.finditer(_MUSTACHE, s2):
        mark(m.start(), m.end())
    _mask_braces(''.join(out), out)
    return ''.join(out)


def lint_locale(text, path='', profile=None, fmt=None, channel=None, max_words=None, settings=None,
                entries=None):
    """فقط مقدارهای فارسیِ فایلِ locale؛ مسئله با کلید (key) گزارش می‌شود."""
    p = normalize_profile(profile or {})
    st = settings or resolve_settings(p, fmt or (channel or {}).get('format_id') or None, max_words)
    if entries is None:
        entries = extract_locale(text, path or 'x.json')
    issues, lens, placeholders, n_str, skipped = [], [], 0, 0, 0
    joined, items = [], []
    for key, value, line in entries:
        if not isinstance(value, str):
            continue
        if not HAS_FA.search(value):       # ارزان: بیشترِ مقدارهای یک فایلِ بزرگ فارسی ندارند
            skipped += 1
            continue
        value = clean_text(value)
        masked = mask_value(value)
        if not HAS_FA.search(masked):
            skipped += 1
            continue
        n_str += 1
        raw_lines, mlines = value.split('\n'), masked.split('\n')
        starts, pos = [], 0
        for ln in raw_lines:
            starts.append(pos)
            pos += len(ln) + 1
        its, info = _check(raw_lines, mlines, st, 'string', key=key)
        for it in its:
            sub = it['line']
            if sub and it['col']:
                it['col'] = starts[sub - 1] + it['col']
            it['line'] = line
        issues += its
        lens += info['lens']
        placeholders += info['placeholders']
        if channel:
            for level, code, msg in _channel_check(value, channel)[0]:
                issues.append(_issue(line, 0, code, level, msg, value, key))
        joined.append(masked)
        flat = masked.replace('\n', ' ')
        items.append((line, key, flat, value.replace('\n', ' ')))
    for code, msg in _register_issues('\n'.join(joined), st):
        issues.append(_issue(0, 0, code, WARN, msg))
    issues += _address_issues(items, st)
    issues = _hub_issues(_finalize(_profile_issues(st) + issues))
    extra = {'strings': n_str, 'skipped': skipped}
    if channel:
        extra['channel'] = {'id': channel.get('id'), 'field': channel.get('field'),
                            'note': '' if (channel.get('spec') or {}).get('status') == 'verified'
                            else 'سقفِ تأییدنشده', 'per_string': True}
    return issues, _hub_stats(_make_stats(issues, lens, st, 'locale', placeholders, extra))


# ---------------------------------------------------------------- csv و tsv (کاتالوگِ انبوه)
CSV_EXTS = ('.csv', '.tsv')
# ستونِ متنیِ پیش‌فرض: نامی که یکی از این‌ها را دارد (desc_new، metaTitle، body_html، عنوانِ کالا،
# «نام»ِ خروجیِ ووکامرس). خانه‌ی بی‌حرفِ فارسی سنجیده نمی‌شود، پس ستونِ اضافه هزینه‌ای ندارد.
_CSV_TEXT_COL = re.compile(r'(?i)title|name|desc|body|text|عنوان|توضیح|متن'
                           r'|(?<![%s])نام\u0650?(?![%s])' % (FA_LETTERS, FA_LETTERS))
_CSV_KEYS = ('sku', 'id', 'کد')
# «id» فقط واژه‌ی جدا (product_id، productId)؛ «width» و «valid» کلید نیستند
_CSV_KEY_LOOSE = re.compile(r'(?i)(?:^|[^a-z])(?:sku|id)(?:[^a-z]|$)|^کد(?:$|[\s\u200c\u0650_\-])')
_CAMEL = re.compile(r'([a-z0-9])([A-Z])')


def _csv_delimiter(text, path=''):
    """tsv یعنی تب؛ csv از روی سطرِ سرستون: پرتکرارترین میانِ «,» «;» و تب (اکسلِ بعضی زبان‌ها «;» دارد)."""
    if (path or '').lower().endswith('.tsv'):
        return '\t'
    first = text.split('\n', 1)[0]
    n, _comma, d = max((first.count(d), d == ',', d) for d in (',', ';', '\t'))
    return d if n else ','


def _csv_split_names(spec):
    return [c.strip() for c in re.split('[,،]', spec or '') if c.strip()]


def _csv_pick(header, columns, key, label):
    """(اندیسِ ستون‌های متنی، اندیسِ ستونِ کلید یا None، نامِ نمایشیِ ستون‌ها)."""
    names, seen = [], {}
    for j, h in enumerate(header):
        base = h or 'col%d' % (j + 1)
        seen[base] = seen.get(base, 0) + 1
        names.append(base if seen[base] == 1 else '%s#%d' % (base, seen[base]))
    low = [h.lower() for h in header]
    shown = '، '.join(names)
    if columns:
        idx = []
        for c in _csv_split_names(columns):
            hits = [j for j, h in enumerate(low) if h == c.lower()]
            if not hits:
                raise UserError('ستونِ «%s» در سرستونِ %s نیست. ستون‌ها: %s' % (c, label, shown))
            idx += [j for j in hits if j not in idx]
    else:
        idx = [j for j, h in enumerate(header) if _CSV_TEXT_COL.search(h)]
        if not idx:
            raise UserError('در %s ستونِ متنی پیدا نشد؛ با --csv-columns نام ببر. ستون‌ها: %s' % (label, shown))
    if key:
        hits = [j for j, h in enumerate(low) if h == key.strip().lower()]
        if not hits:
            raise UserError('ستونِ کلیدِ «%s» در سرستونِ %s نیست. ستون‌ها: %s' % (key, label, shown))
        kj = hits[0]
    else:
        kj = next((j for k in _CSV_KEYS for j, h in enumerate(low) if h == k), None)
        if kj is None:
            kj = next((j for j, h in enumerate(header) if _CSV_KEY_LOOSE.search(_CAMEL.sub(r'\1_\2', h))), None)
    return sorted(idx), kj, names


def csv_cells(text, path='', columns=None, key=None, delimiter=None):
    """خانه‌های ستون‌های متنیِ یک csv یا tsv. ستون‌های دیگر خوانده نمی‌شوند.
    خروجی: {'columns'، 'key'، 'delimiter'، 'rows'، 'cells'}؛ هر خانه (ردیف، کد، ستون، مقدار،
    سطرِ آغاز در فایل). ردیف مثلِ صفحه‌گسترده شمرده می‌شود: سرستون ردیفِ ۱ است."""
    text = clean_text(text)
    label = '«%s»' % (path or 'stdin')
    delim = delimiter or _csv_delimiter(text, path)
    try:
        csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))
    except (OverflowError, ValueError):
        pass
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    header, idx, kj, names, want = None, [], None, [], set()
    rowno = prev = nrows = 0
    cells = []
    try:
        for rec in reader:
            rowno += 1
            start, prev = prev + 1, reader.line_num
            if header is None:
                if not any(c.strip() for c in rec):
                    continue
                header = [c.strip() for c in rec]
                idx, kj, names = _csv_pick(header, columns, key, label)
                want = set(idx)
                continue
            nrows += 1
            code = (rec[kj].strip() if kj is not None and kj < len(rec) else '') or '-'
            nl = 0
            for j, val in enumerate(rec):
                if j in want:
                    cells.append((rowno, code, names[j], val, start + nl))
                nl += val.count('\n')
    except csv.Error as e:
        raise UserError('%s به‌عنوانِ csv خوانده نشد (سطرِ %d): %s' % (label, reader.line_num, e))
    if header is None:
        raise UserError('%s خالی است یا سرستون ندارد؛ سطرِ اول باید نامِ ستون‌ها باشد.' % label)
    return {'columns': [names[j] for j in idx], 'key': names[kj] if kj is not None else '',
            'delimiter': delim, 'rows': nrows, 'cells': cells}


def lint_csv(text, path='', profile=None, fmt=None, channel=None, max_words=None, settings=None,
             columns=None, key=None, md=False, delimiter=None):
    """هر خانه‌ی ستون‌های متنی جدا، مثلِ یک متنِ کامل (سقفِ تعجب و ایموجی، لحن و جمله‌ها برای
    همان خانه). کلیدِ مسئله «row n/کد/ستون» است و line سطرِ همان خانه در فایل."""
    p = normalize_profile(profile or {})
    st = settings or resolve_settings(p, fmt or (channel or {}).get('format_id') or None, max_words)
    info = csv_cells(text, path, columns, key, delimiter)
    kind = 'md' if md else 'text'
    issues, lens, placeholders, n_cells, skipped, flagged = [], [], 0, 0, 0, set()
    for rowno, code, col, value, line in info['cells']:
        if not HAS_FA.search(value):
            skipped += 1
            continue
        masked = mask_prose(value, kind)
        if not HAS_FA.search(masked):
            skipped += 1
            continue
        n_cells += 1
        k = 'row %d/%s/%s' % (rowno, code, col)
        its, inf = _check(value.split('\n'), masked.split('\n'), st, 'doc', key=k, kind=kind)
        for it in its:
            it['line'] = line + (it['line'] - 1 if it['line'] else 0)
        if channel:
            for level, c, msg in _channel_check(value, channel)[0]:
                its.append(_issue(line, 0, c, level, msg, value, k))
        if its:
            flagged.add(rowno)
        issues += its
        lens += inf['lens']
        placeholders += inf['placeholders']
    issues = _hub_issues(_finalize(_profile_issues(st) + issues))
    extra = {'rows': info['rows'], 'cells': n_cells, 'skipped': skipped, 'rows_flagged': len(flagged),
             'columns': info['columns'], 'key_column': info['key'], 'delimiter': info['delimiter']}
    if channel:
        extra['channel'] = {'id': channel.get('id'), 'field': channel.get('field'),
                            'note': '' if (channel.get('spec') or {}).get('status') == 'verified'
                            else 'سقفِ تأییدنشده', 'per_string': True}
    return issues, _hub_stats(_make_stats(issues, lens, st, 'csv', placeholders, extra))


def lint_file(path, profile=None, fmt=None, channel=None, max_words=None, md=False, settings=None,
              csv_columns=None, csv_key=None):
    """فایل را می‌خواند، نوعش را از پسوند می‌فهمد و می‌سنجد."""
    text = read_text(path)
    kind = detect_kind(path, md)
    if kind == 'locale':
        return lint_locale(text, path, profile, fmt, channel, max_words, settings)
    if kind == 'csv':
        return lint_csv(text, path, profile, fmt, channel, max_words, settings, csv_columns, csv_key, md)
    return lint(text, profile=profile, fmt=fmt, channel=channel, max_words=max_words, kind=kind,
                settings=settings)


# ---------------------------------------------------------------- فهرستِ قاعده‌ها
def rule_list():
    """همه‌ی قاعده‌ها، هر شناسه یک بار: الگوها، واژه‌نامه و سنجه‌های پویا."""
    rows, by_id = [], {}
    for c, lv, _, msg in PATTERNS:
        if c in by_id:
            by_id[c]['description'] += '؛ و ' + msg
            continue
        by_id[c] = {'id': c, 'severity': lv, 'kind': 'pattern', 'description': msg}
        rows.append(by_id[c])
    for c, lv, k, d in DYNAMIC_RULES:
        if c in by_id:
            by_id[c]['description'] += '؛ و ' + d
            continue
        by_id[c] = {'id': c, 'severity': lv, 'kind': k, 'description': d}
        rows.append(by_id[c])
    for c, note in RULE_NOTES.items():
        if c in by_id:
            by_id[c]['description'] += ' (' + note + ')'
    for pid, spec in HUB_PARAMS.items():
        rule, _, name = pid.partition('.')
        if rule in by_id:
            by_id[rule].setdefault('params', {})[name] = dict(spec)
    return rows


def print_rules(as_json=False):
    rows = _HUB.rules_rows('fa', rule_list()) if _HUB is not None else rule_list()
    if as_json:
        print(json.dumps({'version': 2, 'tool_version': __version__, 'rules': rows,
                          'lexicon': LEXICON, 'jargon': JARGON,
                          'formats': dict((k, FORMAT_DEFAULTS[k]) for k in FORMAT_IDS)},
                         ensure_ascii=False, indent=1))
        return
    print('# قاعده‌ها (%d)' % len(rows))
    for r in rows:
        print('%-8s %-24s %s' % (r['severity'], r['id'], r['description']))
    print('\n# واژه‌نامه‌ی lexicon')
    for g, ws in LEXICON.items():
        print('%s: %s' % (g, '، '.join(w.strip() for w in ws)))
    print('\n# قالب‌ها (--format)؛ سقفِ قالب فقط سخت‌تر می‌کند؛ آنچه نیامده از پروفایل یا دکمه می‌آید، سقفِ جمله ۲۴')
    for k in FORMAT_IDS:
        d = FORMAT_DEFAULTS[k]
        lim = ' '.join('%s=%s' % (x, d[x]) for x in ('max_words', 'emoji_max', 'exclaim_max') if x in d)
        print('%-9s %-40s %s' % (k, lim or '—', d.get('note', '')))
    print('\nتقدم: --max-words > profile.formats[قالب] > قالب (فقط سخت‌تر: کمینه‌ی قالب و پروفایل) > پروفایل > دکمه')
    print('نادیده: سطرهای میانِ <!-- lint-ignore --> و <!-- /lint-ignore --> (هر کدام روی سطرِ خودش)')
    print('نقل‌قول: متنِ «…» در لحن شمرده نمی‌شود؛ در --md بلوکِ «>» جدا از متنِ نویسنده سنجیده می‌شود')
    print('csv/tsv: هر خانه‌ی ستون‌های متنی جدا سنجیده می‌شود (--csv-columns؛ پیش‌فرض ستون‌هایی که نامشان '
          'title، name، desc، body، text، عنوان، توضیح، متن یا واژه‌ی «نام» دارد). کلیدِ مسئله «row n/کد/ستون» '
          'است؛ n شماره‌ی ردیف مثلِ صفحه‌گسترده (سرستون ردیفِ ۱) و کد از --csv-key (پیش‌فرض sku، id یا کد)')


# ---------------------------------------------------------------- خطِ فرمان
def _err(msg):
    try:
        sys.stderr.write('lint_fa: %s\n' % msg)
        sys.stderr.flush()
    except Exception:
        pass


def _setup_stdio():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8')
        except Exception:
            pass


def build_parser():
    ap = argparse.ArgumentParser(
        prog='lint_fa', description='بازبینِ صدای روایی فارسی (والوری %s)' % __version__)
    ap.add_argument('paths', nargs='*',
                    help='فایل، پوشه (بازگشتی)، الگو مثلِ "posts/*.txt"، یا - برای ورودیِ استاندارد')
    ap.add_argument('--text', action='append', metavar='TEXT', help='متنِ کوتاه به‌جای فایل؛ تکرارپذیر')
    ap.add_argument('--profile', help="پروفایلِ json یا md، نامِ خالی (whalory)، یا 'auto'")
    ap.add_argument('--format', dest='fmt', metavar='ID',
                    help='قالبِ متن: %s' % '، '.join(FORMAT_IDS))
    ap.add_argument('--channel', metavar='ID[.FIELD]', help='سقفِ نویسه‌ی کانال از data/channels')
    ap.add_argument('--channels-dir', metavar='DIR', help='پوشه‌ی دیگری برای داده‌ی کانال')
    ap.add_argument('--md', action='store_true', help='ورودی markdown است؛ کد و سرصفحه نادیده')
    ap.add_argument('--csv-columns', metavar='COLS',
                    help='csv/tsv: ستون‌هایی که سنجیده می‌شوند، جدا با ویرگول؛ پیش‌فرض ستون‌هایی که نامشان '
                         'title، name، desc، body، text، عنوان، توضیح، متن یا واژه‌ی «نام» دارد')
    ap.add_argument('--csv-key', metavar='COL',
                    help='csv/tsv: ستونِ شناسه در کلیدِ «row n/کد/ستون»؛ پیش‌فرض sku، id یا کد')
    ap.add_argument('--json', action='store_true', help='خروجیِ JSON (نسخه‌ی ۲)')
    ap.add_argument('--strict', action='store_true', help='هشدار هم خروج را ۱ کند')
    ap.add_argument('--max-words', type=int, help='سقفِ واژه‌ی جمله؛ بر همه مقدم است')
    ap.add_argument('--rules', action='store_true', help='فهرستِ همه‌ی قاعده‌ها و قالب‌ها')
    ap.add_argument('--fix', action='store_true', help='اصلاحِ مکانیکی؛ خروجی در <نام>.fixed.<پسوند>')
    ap.add_argument('--write', action='store_true', help='با --fix، اصلاح در همان فایل')
    ap.add_argument('--no-overlay', action='store_true',
                    help='فقط قاعده‌های درونی، بی به‌روزرسانیِ امضاشده‌ی هاب (مثلِ WHALORY_HUB_OVERLAY=0)')
    ap.add_argument('--version', action='version', version='lint_fa %s' % __version__)
    return ap


def _json_issue(x):
    return {'line': x['line'] or None, 'col': x['col'] or None, 'key': x.get('key'),
            'rule': x['code'], 'severity': x['level'], 'message': x['message'], 'excerpt': x['text']}


def main(argv=None):
    _setup_stdio()
    ap = build_parser()
    a = ap.parse_args(argv)
    if _HUB is not None:
        _HUB.set_cli_disabled(a.no_overlay)
    if a.rules:
        print_rules(a.json)
        return 0
    paths = iter_paths(a.paths)
    if not paths and not a.text:
        ap.print_usage(sys.stderr)
        _err('حداقل یک فایل، پوشه، - یا --text لازم است.')
        return 2
    if a.write and not a.fix:
        _err('--write فقط همراهِ --fix کاری می‌کند؛ نادیده گرفته شد.')
    profile = load_profile(a.profile) if a.profile else {}
    if a.profile == 'auto' and not profile:
        _err('پروفایلِ خودکار (voice.json) در این پوشه و بالاتر پیدا نشد؛ بی‌پروفایل سنجیده شد.')
    channel = resolve_channel(a.channel, a.channels_dir) if a.channel else None
    for w in (channel or {}).get('load_warnings', []):
        _err(w)
    fmt = a.fmt or (channel or {}).get('format_id') or None
    if a.fmt and a.fmt not in FORMAT_DEFAULTS and a.fmt not in (profile.get('formats') or {}):
        raise UserError('قالبِ «%s» شناخته نشد. قالب‌ها: %s' % (a.fmt, '، '.join(FORMAT_IDS)))
    settings = resolve_settings(profile, fmt, a.max_words)

    inputs = [('<text>', None, t) for t in (a.text or [])] + [(p, p, None) for p in paths]
    report, any_bad, input_errors, csv_seen = [], False, 0, False
    say = _err if a.json else print
    for label, path, inline in inputs:
        try:
            meta = {}
            if path is None:
                text, kind = inline, ('md' if a.md else 'text')
            elif path == '-':
                text, kind, label = read_text('-'), ('md' if a.md else 'text'), '-'
                if a.csv_columns or a.csv_key:
                    kind = 'csv'           # ورودیِ استاندارد با --csv-columns یعنی csv
            else:
                text, meta = read_text(path, with_meta=True)
                kind = detect_kind(path, a.md)
            fixed_lines = None
            if a.fix:
                if kind == 'locale':
                    _err('--fix برای فایلِ locale پشتیبانی نمی‌شود؛ %s دست نخورد. مقدارها را دستی '
                         'اصلاح کن تا کلید و جای‌نگهدار سالم بمانند.' % label)
                elif kind == 'csv':
                    _err('--fix برای csv و tsv پشتیبانی نمی‌شود؛ %s دست نخورد. خانه‌ها را دستی یا در '
                         'صفحه‌گسترده اصلاح کن تا ستون‌های دیگر دست نخورند.' % label)
                else:
                    fixed, fixed_lines = fix_text(text, kind=kind)
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
                    say('اصلاح: %d خط تغییر کرد → %s' % (fixed_lines, target))
                    text = fixed
            if kind == 'locale':
                issues, stats = lint_locale(text, path, profile, settings=settings, channel=channel)
            elif kind == 'csv':
                issues, stats = lint_csv(text, path if path not in (None, '-') else '', profile,
                                         settings=settings, channel=channel, columns=a.csv_columns,
                                         key=a.csv_key, md=a.md)
                csv_seen = True
            else:
                issues, stats = lint(text, profile=profile, kind=kind, settings=settings, channel=channel)
            if fixed_lines is not None:
                stats['fixed_lines'] = fixed_lines
            report.append({'path': label, 'issues': issues, 'stats': stats})
            if stats['errors'] or (a.strict and stats['warnings']):
                any_bad = True
        except UserError as e:
            _err(str(e))
            input_errors += 1
            report.append({'path': label, 'issues': [], 'stats': {}, 'error': str(e)})

    if (a.csv_columns or a.csv_key) and not csv_seen and not input_errors:
        _err('--csv-columns و --csv-key فقط برای فایلِ csv یا tsv کار می‌کنند؛ نادیده گرفته شدند.')
    if a.json:
        if report:
            files = []
            for r in report:
                f = {'path': r['path'], 'issues': [_json_issue(x) for x in r['issues']], 'stats': r['stats']}
                if r.get('error'):
                    f['error'] = r['error']
                files.append(f)
            print(json.dumps({'version': 2, 'files': files,
                              'summary': {'errors': sum(r['stats'].get('errors', 0) for r in report),
                                          'warnings': sum(r['stats'].get('warnings', 0) for r in report)}},
                             ensure_ascii=False, indent=1))
    else:
        if profile:
            print('پروفایل: %s  (%s)' % (profile.get('name', ''), profile.get('_path', '')))
        if settings.get('format'):
            print('قالب: %s  (سقفِ جمله %s، ایموجی %s، تعجب %s)'
                  % (settings['format'], settings['max_words'], settings['emoji_max'], settings['exclaim_max']))
        if channel:
            sp = channel.get('spec') or {}
            print('کانال: %s%s  (%s)%s' % (channel['id'], '.' + channel['field'] if channel['field'] else '',
                                          channel.get('name', ''),
                                          '' if sp.get('status') == 'verified' else '  سقفِ تأییدنشده'))
        if profile or settings.get('format') or channel:
            print('')
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
                tail = '  «%s»' % x['text'] if x['text'] else ''
                print('%s  %-7s %-18s %s%s' % (where, x['level'], x['code'], x['message'], tail))
            s = r['stats']
            head = '%s: ' % r['path']
            if s.get('kind') == 'locale':
                head += '%d رشته‌ی فارسی، ' % s.get('strings', 0)
            elif s.get('kind') == 'csv':
                head += '%d ردیف (%d با مسئله)، %d خانه‌ی فارسی در ستونِ %s%s؛ ' % (
                    s.get('rows', 0), s.get('rows_flagged', 0), s.get('cells', 0),
                    '، '.join(s.get('columns') or []),
                    ' (کلید: %s)' % s['key_column'] if s.get('key_column') else ' (بی‌ستونِ کلید)')
            print('%s%d جمله، میانگینِ %s واژه، سقفِ %s · %d خطا · %d هشدار'
                  % (head, s['sentences'], s['avg_words'], s['max_words'], s['errors'], s['warnings']))
            ch = s.get('channel')
            if ch and not ch.get('per_string'):
                if ch.get('unit') == 'segment':
                    print('  کانال %s: %d نویسه، %d پاره (%s؛ یک‌پاره تا %d، در چندپاره هر پاره %d)%s'
                          % (ch['id'], ch['chars'], ch.get('segments', 0), ch.get('encoding', ''),
                             ch.get('single', 0), ch.get('per_part', 0),
                             ' · ' + ch['note'] if ch.get('note') else ''))
                else:
                    segs = (' · %d پاره (%s)' % (ch['segments'], ch.get('encoding', ''))
                            if 'segments' in ch else '')
                    print('  کانال %s: %d %s از سقفِ %s%s%s'
                          % (ch['id'], ch.get('count', ch['chars']), 'بایت' if ch.get('unit') == 'byte' else 'نویسه',
                             ch.get('max_chars') if ch.get('max_chars') is not None else 'نامعلوم', segs,
                             ' · ' + ch['note'] if ch.get('note') else ''))
            print('')
    if input_errors:
        return 2
    return 1 if any_bad else 0


def run(argv=None):
    """اجرای خطِ فرمان با خطای دوستانه: خطای کاربر بی‌traceback و با خروجِ ۲."""
    try:
        code = main(argv)
    except UserError as e:
        _err(str(e))
        code = 2
    except KeyboardInterrupt:
        code = 130
    except BrokenPipeError:
        try:
            sys.stdout = open(os.devnull, 'w')
        except Exception:
            pass
        code = 0
    except SystemExit:
        raise
    except Exception as e:  # خطای پیش‌بینی‌نشده؛ traceback فقط با WHALORY_DEBUG=1
        if os.environ.get('WHALORY_DEBUG') or os.environ.get('WHALYA_DEBUG'):  # WHALYA_*: deprecated name
            raise
        _err('خطای پیش‌بینی‌نشده: %s: %s. برای جزئیات WHALORY_DEBUG=1 بگذار و دوباره اجرا کن.'
             % (type(e).__name__, e))
        code = 2
    sys.exit(code)


if _HUB is not None:
    _HUB.register('fa', sys.modules[__name__])

if __name__ == '__main__':
    run()
