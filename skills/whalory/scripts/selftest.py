#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest: بعد از هر تغییر در قاعده‌ها اجرا کن تا مطمئن شوی چیزی نشکسته.

    python scripts/selftest.py

فقط کتابخانه‌ی استانداردِ پایتون ۳.۸ به بالا. از هر پوشه‌ای اجرا می‌شود. آزمونی که
فایلش در این بسته نیست (اسکریپت یا پروفایلی که فقط در والوری حرفه‌ای هست) «پرش» می‌خورد
و «رد» شمرده نمی‌شود. اگر scripts/selftest_tools.py باشد، آزمون‌های آن هم آخرِ کار اجرا و شمرده می‌شوند.
در والوری ۳ همین کار برای selftest_en.py (لینترِ انگلیسی، lint.py و textcount) و selftest_mcp.py هم انجام می‌شود،
و نحوِ پایتون ۳.۸ برای همه‌ی فایل‌های scripts/*.py سنجیده می‌شود.
"""
from __future__ import print_function

import sys

if sys.version_info < (3, 8):
    sys.stderr.write('selftest needs Python 3.8 or newer (found %s).\n' % sys.version.split()[0])
    sys.exit(2)
sys.dont_write_bytecode = True  # no __pycache__ next to the scripts: a skill or plugin folder may be read-only

import ast  # noqa: E402
import codecs  # noqa: E402
import glob  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['WHALORY_HUB_OVERLAY'] = '0'  # built-in rules only (Hub spec 5.9), whatever the Hub folder holds
sys.path.insert(0, HERE)
import lint_fa as LF  # noqa: E402
from lint_fa import lint, load_profile, fix_text  # noqa: E402

S = os.path.join(HERE, 'samples')
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, 'profiles')
LINT = os.path.join(HERE, 'lint_fa.py')
CH_DIR = os.path.join(S, 'channels')
BRAND = 'samples:brand-profile.json'   # برندِ ساختگیِ آزمون، در همین پوشه‌ی samples
ZWNJ = chr(0x200c)


def prof_path(name):
    """پروفایل را پیدا می‌کند: «samples:x.json» در samples/؛ بقیه در profiles/،
    profiles/starters/ و examples/*/. نبود → None (آزمون پرش می‌خورد)."""
    if name.startswith('samples:'):
        c = os.path.join(S, name.split(':', 1)[1])
        return c if os.path.isfile(c) else None
    base = os.path.basename(name)
    stem = os.path.splitext(base)[0]
    cands = [os.path.join(P, name), os.path.join(P, 'starters', base),
             os.path.join(ROOT, 'examples', stem, base)]
    cands += sorted(glob.glob(os.path.join(ROOT, 'examples', '*', base)))
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


LINT_CASES = [
    # (نمونه، پروفایل، حداقلِ خطا، حداکثرِ خطا، کدهایی که باید باشند، کدهایی که نباید باشند)
    ('good.txt', None, 0, 0, [], ['space-before-punct', 'mixed-register']),
    ('formal.txt', None, 0, 0, [], ['admin']),
    ('fintech.txt', None, 0, 0, [], []),
    ('after.txt', None, 0, 0, [], []),
    ('mixed.txt', None, 0, 0, ['mixed-register'], []),
    ('legit-negation.txt', None, 0, 0, [], ['neg-contrast']),
    ('bad.txt', None, 10, 99, ['neg-contrast', 'not-only', 'dash', 'admin', 'arabic-yeh',
                              'problem-solution', 'we-believe', 'bang-bang', 'welcome-world'], []),
    ('errors.txt', None, 3, 99, ['tanvin-fa', 'double-plural', 'heavy-passive', 'heavy-prep',
                                 'spacing-compound', 'vague-apology'], []),
    ('good.txt', BRAND, 0, 0, [], []),
    ('brand.txt', BRAND, 2, 99, ['brand-spelling', 'profile-banned', 'profile-avoid'], []),
    ('fintech.txt', 'starters/fintech.json', 0, 0, [], ['register']),
    ('good.txt', 'starters/saas.json', 0, 0, ['register'], []),
]

DIGIT_CASES = [
    # (متن، آیا latin-digit باید بیاید؟، برچسب)
    ('برای ۱۲ نفر، ۲٬۵۰۰٬۰۰۰ تومان کافی است.', False, 'رقمِ فارسی'),
    ('برای ١٢ نفر و ٢٥٠٠ تومان.', False, 'رقمِ عربی'),
    ('برای 12 نفر و 2500 تومان کافی است.', True, 'رقمِ لاتین کنارِ واژه'),
]

MUST_CLEAR_AFTER_FIX = ['arabic-yeh', 'arabic-kaf', 'dash', 'latin-comma', 'latin-question',
                        'bang-bang', 'zwnj-mi', 'zwnj-ha', 'ezafe-he', 'latin-quote',
                        'space-before-punct']

NEW_TELLS = {'did-you-know': 'error', 'lets': 'warning', 'nowadays': 'warning', 'no-secret': 'error',
             'golden-tip': 'warning', 'final-word': 'warning', 'hope-helpful': 'error'}

MUST_LIST = ['lexicon', 'brand-spelling', 'profile-banned', 'profile-avoid', 'jargon', 'address',
             'register', 'mixed-register', 'profile-register-alias', 'profile-invalid', 'long-sentence',
             'ke-chain', 'ra-chain', 'rhetorical-open', 'same-opening', 'flat-rhythm', 'bangs', 'emoji',
             'emoji-bullet', 'caption-header', 'channel-length', 'channel-visible', 'na-contrast',
             'serial-comma'] + list(NEW_TELLS)

LOCALE_CASES = [
    # (فایل، (کلید، قاعده)هایی که باید باشند، کلیدهایی که نباید مسئله داشته باشند)
    ('locale-fa.json', [('common.items', 'dash'), ('errors.network', 'admin'), ('list[1]', 'arabic-kaf'),
                        ('common.printf', 'latin-comma')],
     ['key—with—dash', 'common.english', 'common.count', 'common.greeting', 'errors.html']),
    ('strings.xml', [('save_done', 'bang-bang'), ('cdata', 'dash'), ('days[1]', 'arabic-yeh')],
     ['app_name', 'notrans', 'welcome', 'orders[one]', 'hint']),
    ('fa.po', [('Welcome', 'dash'), ('button|Save', 'arabic-yeh')], ['', 'One file[0]', 'Multi']),
    ('app_fa.arb', [('title', 'dash')], ['@title', '@@locale', 'hello']),
    ('Localizable.strings', [('welcome_title', 'dash'), ('quote', 'latin-quote')], ['url_hint', 'commented']),
    ('messages.xlf', [('greeting', 'dash'), ('cart.count', 'arabic-yeh')], []),
]

LONG = ' '.join(['واژه'] * 30) + '.'      # جمله‌ی سی‌واژه‌ای، بالاتر از سقفِ ۲۴


def check(label, problems, extra=''):
    if problems:
        print('FAIL  %-40s %s' % (label, ' · '.join(str(p) for p in problems)))
        return 1
    print('ok    %-40s %s' % (label, extra))
    return 0


def read(name):
    with io.open(os.path.join(S, name), encoding='utf-8') as fh:
        return fh.read()


def rbytes(path):
    with open(path, 'rb') as fh:
        return fh.read()


def wbytes(path, data):
    with open(path, 'wb') as fh:
        fh.write(data)


def codes_of(issues):
    return [x['code'] for x in issues]


def run_cli(args, stdin=None):
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    env.pop('WHALORY_DEBUG', None)
    r = subprocess.run([sys.executable, LINT] + list(args), input=stdin, capture_output=True, env=env)
    return r.returncode, r.stdout.decode('utf-8', 'replace'), r.stderr.decode('utf-8', 'replace')


def friendly(code, err, want=2):
    pr = []
    if code != want:
        pr.append('خروج %s، انتظار %s' % (code, want))
    if 'Traceback' in err:
        pr.append('traceback چاپ شد')
    if want == 2 and not err.strip():
        pr.append('پیامِ خطا خالی است')
    return pr


def has(text, code, **kw):
    return code in codes_of(lint(text, **kw)[0])


def expect_codes(cases, code, **kw):
    """cases: [(متن، باید باشد؟)] → فهرستِ مسئله‌ها."""
    pr = []
    for text, want in cases:
        got = has(text, code, **kw)
        if got != want:
            pr.append('%s %s: %s' % ('نبود' if want else 'نباید', code, text[:40]))
    return pr


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    tmp = tempfile.mkdtemp(prefix='whalory-selftest-')
    counts = [0, 0, 0]  # [همه، ردشده، پرش]

    def t(label, problems, extra=''):
        counts[0] += 1
        counts[1] += check(label, problems, extra)

    def skip(label, why):
        counts[2] += 1
        print('skip  %-40s %s' % (label, why))

    try:
        # ۱) قاعده‌ها
        for name, prof, min_e, max_e, must, mustnot in LINT_CASES:
            label = 'lint %s%s' % (name, ' + ' + prof.split(':')[-1] if prof else '')
            path = prof_path(prof) if prof else None
            if prof and not path:
                skip(label, 'پروفایل در این بسته نیست')
                continue
            profile = load_profile(path) if path else {}
            issues, st = lint(read(name), profile=profile)
            codes = set(codes_of(issues))
            pr = []
            if not (min_e <= st['errors'] <= max_e):
                pr.append('خطا %d، انتظار %d تا %d' % (st['errors'], min_e, max_e))
            pr += ['نبود: %s' % c for c in must if c not in codes]
            pr += ['نباید باشد: %s' % c for c in mustnot if c in codes]
            t(label, pr, 'خطا %d · هشدار %d' % (st['errors'], st['warnings']))

        # ۱‌ب) رقم: «\d» در پایتون ۳ رقمِ فارسی را هم می‌گیرد؛ قاعده باید فقط ۰-۹ لاتین را ببیند
        for text, expect, label in DIGIT_CASES:
            n = sum(1 for x in lint(text)[0] if x['code'] == 'latin-digit')
            pr = [] if (n > 0) == expect else ['latin-digit %d بار؛ انتظار %s' % (n, 'هست' if expect else 'نیست')]
            t('digit %s' % label, pr, 'latin-digit %d' % n)

        # ۲) اصلاحِ خودکار
        fixed, n = fix_text(read('fixme.txt'))
        codes = set(codes_of(lint(fixed)[0]))
        t('fix fixme.txt', ['هنوز هست: %s' % c for c in MUST_CLEAR_AFTER_FIX if c in codes], '%d خط اصلاح شد' % n)
        pr = []
        for name in ('good.txt', 'formal.txt', 'fintech.txt', 'after.txt'):
            tx = read(name)
            f2, n2 = fix_text(tx)
            if f2 != tx:
                pr.append('%s عوض شد (%d خط)' % (name, n2))
        t('fix متنِ سالم را دست نمی‌زند', pr)
        t('fix دوباره‌اجرا تغییری نمی‌دهد', [] if fix_text(fixed)[0] == fixed else ['اصلاح پایدار نیست'])

        # ۳) پروفایل‌های همراهِ اسکیل معتبرند (نسخه‌ی ۱ یا ۲): profiles/، examples/ و samples/
        pr = []
        need = {'name', 'register', 'dials', 'avoid', 'prefer'}
        files = glob.glob(os.path.join(P, '**', '*.json'), recursive=True)
        files += [f for f in glob.glob(os.path.join(ROOT, 'examples', '**', '*.json'), recursive=True)
                  if '"dials"' in LF.read_text(f)]
        files += [f for f in glob.glob(os.path.join(S, '*.json')) if '"dials"' in LF.read_text(f)]
        for pj in files:
            try:
                d = json.loads(LF.read_text(pj))
                miss = need - set(d)
                if miss:
                    pr.append('%s: %s' % (os.path.basename(pj), '، '.join(sorted(miss))))
                if d.get('register') not in ('any', 'formal', 'colloquial'):
                    pr.append('%s: register' % os.path.basename(pj))
                pr += ['%s: %s' % (os.path.basename(pj), m) for _, m in LF.validate_profile(d)]
            except Exception as e:
                pr.append('%s: %s' % (os.path.basename(pj), e))
        t('همه‌ی پروفایل‌های json', pr, '%d فایل' % len(files))

        # ۴) اسکریپت‌های دیگر اجرا می‌شوند (فقط اگر در این بسته باشند)
        for script, args, label in (
            ('audit_corpus.py', [S, '--json'], 'audit_corpus'),
            ('compare.py', [os.path.join(S, 'bad.txt'), os.path.join(S, 'after.txt')], 'compare'),
            ('profile_stats.py', [os.path.join(S, 'good.txt'), os.path.join(S, 'formal.txt')], 'profile_stats'),
        ):
            path = os.path.join(HERE, script)
            if not os.path.isfile(path):
                skip('script %s' % label, 'در این بسته نیست')
                continue
            env = dict(os.environ, PYTHONIOENCODING='utf-8')
            r = subprocess.run([sys.executable, path] + args, capture_output=True, env=env)
            ok = r.returncode in (0, 1) and not r.stderr.strip()
            t('script %s' % label, [] if ok else [r.stderr.decode('utf-8', 'replace')[-200:]])

        # ۵) نسخه و سازگاری
        code, out, err = run_cli(['--version'])
        t('v3 --version', [] if code == 0 and LF.__version__ in out and LF.__version__ == '3.2.0'
          else ['خروجی: %r' % out], out.strip())
        # نحوِ پایتون ۳.۸ برای همه‌ی اسکریپت‌های scripts/ (والوری ۳)
        pr = []
        py_files = sorted(glob.glob(os.path.join(HERE, '*.py')))
        for f in py_files:
            try:
                ast.parse(LF.read_text(f), feature_version=(3, 8))
            except SyntaxError as e:
                pr.append('%s: %s' % (os.path.basename(f), e))
        t('v3 نحوِ پایتون ۳.۸ (scripts/*.py)', pr, '%d فایل' % len(py_files))
        env = dict(os.environ, PYTHONIOENCODING='utf-8')
        code = ("import sys, runpy; sys.version_info = (3, 7, 9, 'final', 0); "
                "runpy.run_path(%r, run_name='__main__')" % LINT)
        r = subprocess.run([sys.executable, '-c', code], capture_output=True, env=env)
        err = r.stderr.decode('utf-8', 'replace')
        t('v2 پیامِ پایتونِ قدیمی', friendly(r.returncode, err) + ([] if '3.8' in err else ['پیام نسخه ندارد']))

        # ۶) BOM
        base = 'این متن با نیم‌فاصله و «گیومه» است. کالا — آماده.'
        a, sa = lint(base)
        b, sb = lint(LF.BOM + base + LF.BOM)
        pr = []
        if [(x['code'], x['line'], x['col']) for x in a] != [(x['code'], x['line'], x['col']) for x in b]:
            pr.append('BOM نتیجه را عوض کرد')
        if sa['avg_words'] != sb['avg_words']:
            pr.append('BOM واژه شمرده شد')
        if re.search(LF.W, LF.BOM) or LF.HAS_FA.search(LF.BOM) or LF.WORD.search(LF.BOM):
            pr.append('U+FEFF حرف شمرده می‌شود')
        tx = LF.read_text(os.path.join(S, 'bom-text.txt'))
        if LF.BOM in tx:
            pr.append('read_text BOM را نگه داشت')
        t('v2 BOM در متن', pr)
        try:
            bp = load_profile(os.path.join(S, 'bom-profile.json'))
            pr = [] if bp.get('name') == 'bom-cafe' else ['نام: %r' % bp.get('name')]
        except Exception as e:
            pr = ['%s: %s' % (type(e).__name__, e)]
        t('v2 پروفایلِ BOM‌دار', pr)
        code, out, err = run_cli([os.path.join(S, 'bom-text.txt'), '--profile', os.path.join(S, 'bom-profile.json')])
        t('v2 خطِ فرمان با BOM', friendly(code, err, 0))

        # ۷) مسیرها: الگو، پوشه، -، --text
        pr = []
        want = sorted(f for f in os.listdir(S) if f.endswith('.txt'))
        got = LF.iter_paths([os.path.join(S, '*.txt')])
        if sorted(os.path.basename(p) for p in got) != want:
            pr.append('الگو: %d از %d' % (len(got), len(want)))
        got = LF.iter_paths([S])
        if os.path.join(S, 'channels', 'test.json') not in got:
            pr.append('پوشه بازگشتی نیست')
        if any(not p.lower().endswith(LF.SUPPORTED_EXTS) for p in got):
            pr.append('پسوندِ ناپشتیبان در پوشه')
        if LF.iter_paths(['-', '-']) != ['-']:
            pr.append('- عبور نکرد')
        try:
            LF.iter_paths([os.path.join(S, 'nope.txt')])
            pr.append('فایلِ ناموجود خطا نداد')
        except LF.UserError:
            pass
        t('v2 iter_paths', pr, '%d فایل در پوشه' % len(got))
        code, out, err = run_cli([os.path.join(S, '*.txt'), '--json'])
        pr = friendly(code, err, code if code in (0, 1) else 0)
        try:
            n = len(json.loads(out)['files'])
            if n != len(want):
                pr.append('%d فایل، انتظار %d' % (n, len(want)))
        except ValueError:
            pr.append('JSON نیست')
        t('v2 الگو در خطِ فرمان (ویندوز)', pr)
        code, out, err = run_cli(['--text', 'این متن — تست است.', '--text', 'سلام', '--json'])
        d = json.loads(out) if out.strip().startswith('{') else {'files': []}
        pr = [] if code == 1 and len(d['files']) == 2 and d['files'][0]['issues'][0]['rule'] == 'dash' \
            else ['خروج %s، %r' % (code, out[:120])]
        t('v2 --text', pr)
        code, out, err = run_cli(['-', '--json'], stdin='این كالا خوب است.'.encode('utf-8'))
        d = json.loads(out) if out.strip().startswith('{') else {'files': [{'issues': []}]}
        t('v2 ورودیِ استاندارد', [] if 'arabic-kaf' in [x['rule'] for x in d['files'][0]['issues']] else [out[:120]])

        # ۸) پایانِ سطر و BOM در --write
        pr = []
        cp = os.path.join(tmp, 'crlf.txt')
        source = rbytes(os.path.join(S, 'crlf.txt')).replace(bytes([13, 10]), bytes([10]))
        wbytes(cp, source.replace(bytes([10]), bytes([13, 10])))
        if rbytes(cp).count(bytes([13, 10])) != 3:
            pr.append('fixture does not contain three real CRLF endings')
        code, out, err = run_cli([cp, '--fix', '--write'])
        data = rbytes(cp)
        if data.count(b'\r\n') != 3 or data.count(b'\n') != 3:
            pr.append('CRLF ماند؟ %d/%d' % (data.count(b'\r\n'), data.count(b'\n')))
        if 'ي'.encode('utf-8') in data or '،'.encode('utf-8') not in data:
            pr.append('اصلاح نشد')
        pr += friendly(code, err, 0)
        t('v2 --write و CRLF', pr)
        bp = os.path.join(tmp, 'bom.txt')
        with open(bp, 'wb') as fh:
            fh.write(codecs.BOM_UTF8 + 'این كالا خوب است.\r\n'.encode('utf-8'))
        run_cli([bp, '--fix', '--write'])
        data = rbytes(bp)
        t('v2 --write و BOM', [] if data.startswith(codecs.BOM_UTF8) and data.endswith(b'\r\n')
          and 'کالا'.encode('utf-8') in data and data.count(codecs.BOM_UTF8) == 1 else [repr(data[:20])])
        f3, _ = fix_text('کتاب ها\r\nخانه ی ما\r\n')
        t('v2 fix_text و CRLF', [] if f3 == 'کتاب%sها\r\nخانه%sی ما\r\n' % (ZWNJ, ZWNJ) else [repr(f3)])

        # ۹) خطای دوستانه
        code, out, err = run_cli([os.path.join(S, 'nope.txt')])
        t('v2 خطا: فایلِ ناموجود', friendly(code, err))
        bad = os.path.join(tmp, 'bad-profile.json')
        wbytes(bad, '{"name": "x",\n "dials": {},}\n'.encode('utf-8'))
        code, out, err = run_cli([os.path.join(S, 'good.txt'), '--profile', bad])
        t('v2 خطا: پروفایلِ JSON خراب', friendly(code, err) + ([] if 'خطِ 2' in err else ['شماره‌ی خط نیامد']))
        code, out, err = run_cli([os.path.join(S, 'good.txt'), '--profile', 'no-such-brand-xyz'])
        t('v2 خطا: پروفایلِ ناموجود', friendly(code, err))
        code, out, err = run_cli([os.path.join(S, 'good.txt'), '--format', 'tweet'])
        t('v2 خطا: قالبِ ناشناخته', friendly(code, err))
        code, out, err = run_cli([os.path.join(S, 'good.txt'), '--channel', 'nope', '--channels-dir', CH_DIR])
        t('v2 خطا: کانالِ ناشناخته', friendly(code, err) + ([] if 'testgram' in err else ['فهرستِ کانال نیامد']))
        nb = os.path.join(tmp, 'latin1.txt')
        wbytes(nb, b'caf\xe9 \xc3\x28')
        code, out, err = run_cli([nb])
        t('v2 خطا: فایلِ غیر UTF-8', friendly(code, err))

        # ۱۰) --fix به کد، برچسب، ویژگی، نشانی و جمله‌ی انگلیسی دست نمی‌زند
        src = read('html-quotes.html')
        f, n = fix_text(src, kind='html')
        keep = ['title=\'چای "بهاره", تازه\'', 'data-note="سلام, دنیا"', 'href="https://example.com/?q=چای,تازه&t=1"',
                'data-x=\'گفت "سلام"\'', '<code>pip install "whalory"</code>',
                'He said "hello, world" and left; see https://example.com/"a".',
                '<!-- یادداشت "داخلی", دست نخورد -->', 'var s = "سلام, دنیا"; if (a ? b : c) { s = s + "؟"; }',
                'content: "«"; font-family: "Vazirmatn", sans-serif;']
        change = ['<title>چای «بهاره»</title>', 'این چای را «اردیبهشت» چیدیم، و همان هفته']
        pr = ['خراب شد: %s' % k[:30] for k in keep if k not in f]
        pr += ['اصلاح نشد: %s' % c[:30] for c in change if c not in f]
        pr += [] if fix_text(f, kind='html')[0] == f else ['پایدار نیست']
        t('v2 fix در html', pr, '%d خط' % n)
        src = read('fix-protect.md')
        f, n = fix_text(src, kind='md')
        keep = ['title: "راهنمای دم‌کردن, چای"', '`lint_fa.py --fix "draft.txt"`', 'msg = "سلام, دنیا"',
                '(https://example.com/chai?a=1,b=2 "عنوان, پیوند")',
                'The tool prints "ok, done" when finished; see https://example.com/fa/"x".']
        change = ['را اجرا کن، بعد', '[صفحه‌ی «چای»]', 'بخوان، «لطفاً».',
                  'این چای را «اردیبهشت» چیدیم، و همان هفته، در باغ، خشک کردیم.']
        pr = ['خراب شد: %s' % k[:30] for k in keep if k not in f]
        pr += ['اصلاح نشد: %s' % c[:30] for c in change if c not in f]
        pr += [] if fix_text(f, kind='md')[0] == f else ['پایدار نیست']
        t('v2 fix در markdown', pr, '%d خط' % n)
        pr = []
        for s in ('ساعتِ ۹ – ۱۷ باز است.', 'He said "hi", then left - fast; ok?', 'قیمت: 10-20 دلار',
                  'حافظ از جامِ می ناب گفت.', 'اندازه‌ی 5" و 7" داریم.'):
            if fix_text(s)[0] != s:
                pr.append('%s → %s' % (s, fix_text(s)[0]))
        t('v2 fix به بازه، انگلیسی و «می» دست نمی‌زند', pr)

        # ۱۱) پروفایلِ نسخه‌ی ۲، قالب و خطاب
        v2raw = json.loads(LF.read_text(os.path.join(S, 'v2-profile.json')))
        v2 = load_profile(os.path.join(S, 'v2-profile.json'))
        t('v2 پروفایلِ نسخه‌ی ۲ معتبر است', LF.validate_profile(v2raw) +
          ([] if v2.get('schema_version') == 2 else ['schema_version']))
        exp = [  # (قالب، پرچم، سقفِ جمله، ایموجی، لحن، خطاب، چرا)
            (None, None, 26, 1, 'any', 'shoma', 'سراسریِ پروفایل > دکمه'),
            ('caption', None, 12, 2, 'colloquial', 'to', 'profile.formats > FORMAT_DEFAULTS'),
            ('error', None, 18, 0, 'formal', 'shoma', 'formats.dials > FORMAT_DEFAULTS'),
            ('ui', None, 14, 0, 'any', 'shoma', 'FORMAT_DEFAULTS سخت‌تر از سراسریِ پروفایل'),
            ('blog', None, 26, 1, 'any', 'shoma', 'بی‌پیش‌فرض: پروفایل'),
            ('caption', 9, 9, 2, 'colloquial', 'to', 'پرچم > همه'),
        ]
        pr = []
        for fmt, cli, mw, em, reg, addr, why in exp:
            s = LF.resolve_settings(v2, fmt, cli)
            got = (s['max_words'], s['emoji_max'], s['register'], s['address'])
            if got != (mw, em, reg, addr):
                pr.append('%s/%s: %s ≠ %s (%s)' % (fmt, cli, got, (mw, em, reg, addr), why))
        s0, s1 = LF.resolve_settings({}), LF.resolve_settings({}, 'ui')
        if (s0['max_words'], s1['max_words'], s1['emoji_max']) != (24, 14, 0):
            pr.append('پیش‌فرض: %s/%s/%s' % (s0['max_words'], s1['max_words'], s1['emoji_max']))
        if 'فوری' not in LF.resolve_settings(v2, 'sms')['banned']:
            pr.append('banned قالب')
        if LF.resolve_limits(v2) != (26, 1, 0, 'any'):
            pr.append('resolve_limits: %s' % (LF.resolve_limits(v2),))
        t('v2 تقدمِ قالب و پروفایل', pr)
        code, out, err = run_cli(['--text', 'ذخیره شد 🎉', '--format', 'ui', '--json'])
        d = json.loads(out) if out.strip().startswith('{') else {'files': [{'stats': {}, 'issues': []}]}
        st = d['files'][0]['stats']
        t('v2 --format ui', [] if st.get('max_words') == 14 and st.get('format') == 'ui'
          and 'emoji' in [x['rule'] for x in d['files'][0]['issues']] else [out[:160]])
        pr = []
        c1 = codes_of(lint('اگه دوست داری، باهات تماس می‌گیریم و خودت انتخاب کن.', profile=v2)[0])
        c2 = codes_of(lint('کیک رو تو فر بذارید و تو خونه بخورید؛ تو این فصل خوشمزه‌تره.', profile=v2)[0])
        c3 = codes_of(lint('شما می‌توانید همین حالا سفارش بدهید.', profile=v2, fmt='caption')[0])
        c4 = codes_of(lint('وقتی گفت «تو بیا»، رفتیم.', profile=v2)[0])
        if 'address' not in c1:
            pr.append('«تو» در پروفایلِ شما دیده نشد')
        if 'address' in c2:
            pr.append('«تو»ی مکانی خطاب شمرده شد')
        if 'address' not in c3:
            pr.append('«شما» در کپشنِ «تو» دیده نشد')
        if 'address' in c4:
            pr.append('نقل‌قول خطاب شمرده شد')
        if 'address' in codes_of(lint('بدهیِ شما تا فردا تسویه می‌شود و حسابِ نگهداری باز است.', profile=v2)[0]):
            pr.append('«بدهی» خطابِ «تو» شمرده شد')
        t('v2 خطاب (تو/شما)', pr)
        pr = []
        c = codes_of(lint('این متن رو گرم کنین.', profile={'name': 'x', 'register': 'written', 'dials': {}})[0])
        if 'profile-register-alias' not in c or 'register' not in c:
            pr.append('written: %s' % c)
        c = codes_of(lint('این متن رو گرم کنین.', profile={'name': 'x', 'register': 'colloquial-written'})[0])
        if 'profile-register-alias' not in c or 'register' in c:
            pr.append('colloquial-written: %s' % c)
        c = codes_of(lint('این متن رو گرم کنین.', profile={'name': 'x', 'register': 'fancy'})[0])
        if 'profile-invalid' not in c or 'register' in c:
            pr.append('fancy: %s' % c)
        c = codes_of(lint('سلام.', profile={'name': 'x', 'dials': {'warmth': 9}})[0])
        if 'profile-invalid' not in c:
            pr.append('دکمه‌ی بیرون از بازه')
        t('v2 لحنِ قدیمی و نامعتبر', pr)
        pr = []
        if 'jargon' not in codes_of(lint('این دیتا را ببین.', profile=v2)[0]):
            pr.append('jargon=1 بی‌اثر')
        if 'jargon' in codes_of(lint('این دیتا را ببین.', profile={'name': 'x', 'dials': {'jargon': 4}})[0]):
            pr.append('jargon=4 هشدار داد')
        if 'jargon' in codes_of(lint('این دیتا را ببین.')[0]):
            pr.append('بی‌پروفایل هشدار داد')
        t('v2 دکمه‌ی jargon', pr)

        # ۱۲) کانال
        pr = []
        for n, segs in ((70, 1), (71, 2), (134, 2), (135, 3), (201, 3), (202, 4)):
            if LF.sms_segments('س' * n)[0] != segs:
                pr.append('فارسی %d → %d' % (n, LF.sms_segments('س' * n)[0]))
        for n, segs in ((160, 1), (161, 2), (306, 2), (307, 3)):
            if LF.sms_segments('a' * n)[0] != segs:
                pr.append('لاتین %d' % n)
        if LF.sms_segments('a' * 69 + '🙂')[1] != 71:
            pr.append('ایموجی دو واحد نیست')
        t('v2 پاره‌ی پیامک', pr)
        pr = []
        ch = LF.resolve_channel('testgram', CH_DIR)
        iss, st = lint('این یک کپشنِ خیلی خیلی بلند است که از پنجاه نویسه بیشتر می‌شود و خطا می‌دهد.', channel=ch)
        lv = dict((x['code'], x['level']) for x in iss)
        if lv.get('channel-length') != 'error' or lv.get('channel-visible') != 'warning':
            pr.append('caption: %s' % lv)
        if st.get('format') != 'caption' or st.get('max_words') != 20:
            pr.append('format_id کانال: %s/%s' % (st.get('format'), st.get('max_words')))
        iss, st = lint('این بیوی بلندتر از بیست نویسه است.', channel=LF.resolve_channel('testgram.bio', CH_DIR))
        x = [x for x in iss if x['code'] == 'channel-length']
        if not x or x[0]['level'] != 'warning' or 'سقفِ تأییدنشده' not in x[0]['message'] \
                or st['channel'].get('note') != 'سقفِ تأییدنشده':
            pr.append('bio تأییدنشده: %s' % x)
        iss, _ = lint('شناسه‌ی من', channel=LF.resolve_channel('testgram.handle', CH_DIR))
        if 'channel-length' not in codes_of(iss):
            pr.append('بایت شمرده نشد')
        ch = LF.resolve_channel('testsms', CH_DIR)
        iss, st = lint('س' * 140, channel=ch)
        if 'channel-length' not in codes_of(iss) or st['channel'].get('segments') != 3 or st['format'] != 'sms':
            pr.append('پیامک ۱۴۰: %s %s' % (codes_of(iss), st.get('channel')))
        iss, st = lint('س' * 134, channel=ch)
        if 'channel-length' in codes_of(iss) or st['channel'].get('segments') != 2:
            pr.append('پیامک ۱۳۴')
        t('v2 --channel', pr)
        pr = []
        if LF.load_channels(os.path.join(tmp, 'no-such-dir')) != ({}, []):
            pr.append('پوشه‌ی ناموجود')
        broken = os.path.join(tmp, 'channels')
        os.makedirs(broken)
        wbytes(os.path.join(broken, 'bad.json'), b'{"channels": ')
        shutil.copy(os.path.join(CH_DIR, 'test.json'), os.path.join(broken, 'test.json'))
        chans, warns = LF.load_channels(broken)
        if 'testgram' not in chans or not warns:
            pr.append('فایلِ خراب کار را خواباند یا گزارش نشد')
        empty = os.path.join(tmp, 'empty')
        os.makedirs(empty)
        try:
            LF.resolve_channel('telegram', empty)
            pr.append('بی‌داده خطا نداد')
        except LF.UserError:
            pass
        try:
            real, _ = LF.load_channels()
        except Exception as e:
            pr.append('data/channels: %s' % e)
            real = {}
        t('v2 داده‌ی کانالِ ناقص یا خراب', pr, '%d کانال در data/channels' % len([k for k in real if '/' not in k]))
        code, out, err = run_cli(['--text', 'س' * 140, '--channel', 'testsms', '--channels-dir', CH_DIR])
        t('v2 --channel در خطِ فرمان', friendly(code, err, 0) + ([] if 'پاره' in out and 'بخش' not in out
                                                              else ['پاره گزارش نشد']))

        # ۱۳) فایلِ locale
        for name, must, clean_keys in LOCALE_CASES:
            iss, st = LF.lint_file(os.path.join(S, name))
            found = set((x['key'], x['code']) for x in iss)
            keys = set(x['key'] for x in iss)
            pr = ['نبود: %s/%s' % kv for kv in must if kv not in found]
            pr += ['نباید: %s' % k for k in clean_keys if k in keys]
            pr += ['کلیدِ @: %s' % k for k in keys if k and k.startswith('@')]
            pr += ['سطر نیست: %s' % x['key'] for x in iss if x['key'] and not isinstance(x['line'], int)]
            pr += ['جای‌نگهدار: latin-digit'] if 'latin-digit' in codes_of(iss) else []
            t('v2 locale %s' % name, pr, '%d رشته · خطا %d · هشدار %d' % (st['strings'], st['errors'], st['warnings']))
        pr = []
        ents = LF.extract_locale(os.path.join(S, 'locale-fa.json'))
        if ('common.save', 'ذخیره', 3) not in ents:
            pr.append('extract_locale(مسیر)')
        if LF.extract_locale(read('app_fa.arb'), 'x.arb')[0][0] != 'title':
            pr.append('extract_locale(متن، مسیر)')
        mv = LF.mask_value('{count, plural, one {# سفارش} other {# سفارش‌ها}} و %1$s و {{n}} و <b>x</b>')
        if '{' in mv or '%' in mv or '<' in mv or 'سفارش' not in mv or '#' in mv:
            pr.append('mask_value: %r' % mv)
        t('v2 خواننده‌ی locale', pr)
        lc = os.path.join(tmp, 'fa.json')
        shutil.copy(os.path.join(S, 'locale-fa.json'), lc)
        before = rbytes(lc)
        code, out, err = run_cli([lc, '--fix', '--write'])
        pr = [] if code in (0, 1) and 'locale' in err and rbytes(lc) == before else \
            ['خروج %s؛ %s' % (code, err[-120:])]
        t('v2 --fix روی locale پیامِ دوستانه', pr)
        code, out, err = run_cli([os.path.join(S, 'strings.xml'), '--json'])
        d = json.loads(out) if out.strip().startswith('{') else {'files': [{'issues': []}]}
        t('v2 locale در JSON کلید دارد', [] if d['files'][0]['issues'] and all(x['key'] for x in d['files'][0]['issues']
                                                                           if x['line']) else [out[:120]])

        # ۱۴) نشانه‌های تازه‌ی متنِ ماشینی
        iss, _ = lint(read('ai-tells-new.txt'))
        lv = {}
        for x in iss:
            lv.setdefault(x['code'], set()).add(x['level'])
        pr = ['نبود: %s' % k for k in NEW_TELLS if k not in lv]
        pr += ['سطح %s: %s' % (k, lv[k]) for k, v in NEW_TELLS.items() if k in lv and lv[k] != {v}]
        if codes_of(iss).count('final-word') < 2:
            pr.append('«جمع‌بندی» به‌عنوانِ تیتر دیده نشد')
        t('v2 نشانه‌های تازه', pr)
        n = codes_of(lint(read('emoji-bullets.txt'))[0]).count('emoji-bullet')
        t('v2 emoji-bullet', [] if n == 3 else ['%d بار' % n])
        a = codes_of(lint(read('caption-header.txt'))[0]).count('caption-header')
        b = codes_of(lint(read('caption-header.txt'), fmt='caption')[0]).count('caption-header')
        t('v2 caption-header فقط با --format caption', [] if (a, b) == (0, 2) else ['بی‌قالب %d، کپشن %d' % (a, b)])
        n = codes_of(lint('امروز ساعتِ ده باز هستیم.\nاگر فردا بیایید، چای تازه داریم.\nوقتی شما بیایید در باز است.\n')[0])
        m = codes_of(lint('خب. بیایید از اول شروع کنیم.\n- بیایید ببینیم.\n')[0])
        t('v2 «بیایید» فقط سرِ جمله', [] if n.count('lets') == 0 and m.count('lets') == 2
          else ['وسطِ جمله %d، سرِ جمله %d' % (n.count('lets'), m.count('lets'))])

        # ۱۵) مثبتِ کاذب
        c = set(codes_of(lint(read('fp-ok.txt'))[0]))
        bad_codes = {'dash', 'hyphen-dash', 'zwnj-mi', 'welcome-world', 'demo-word', 'emoji', 'address'}
        pr = ['نباید: %s' % x for x in sorted(c & bad_codes)]
        if 'emoji' in codes_of(lint(read('fp-ok.txt'), fmt='ui')[0]):
            pr.append('★ ایموجی شمرده شد')
        t('v2 مثبتِ کاذب fp-ok.txt', pr)
        pr = []
        for s, n in (('★ ☆ ✓ ✔ → • ◆ ♪ © ™', 0), ('🇮🇷🇫🇷', 2), ('👨‍👩‍👧', 1), ('❤️', 1),
                     ('1️⃣ 2️⃣', 2), ('👍🏽', 1), ('✔️', 1), ('✨🌿', 2), ('🏳️‍🌈', 1)):
            if len(LF.EMOJI.findall(s)) != n:
                pr.append('%s → %d' % (s, len(LF.EMOJI.findall(s))))
        t('v2 شمارِ ایموجی', pr)
        brand = load_profile(prof_path(BRAND))
        iss, _ = lint('این محصولِ آزمایشی است.', profile=brand)
        c = [x['code'] for x in iss if 'آزمایشی' in x['text']]
        t('v2 «آزمایشی» یک بار', [] if c == ['profile-banned'] else ['%s' % c])
        saas = prof_path('starters/saas.json')
        if saas:
            iss, _ = lint('این اکوسیستم تازه است.', profile=load_profile(saas))
            c = [x['code'] for x in iss if 'اکوسیستم' in x['text']]
            t('v2 lexicon و avoid یک بار', [] if c == ['profile-avoid'] else ['%s' % c])
        else:
            skip('v2 lexicon و avoid یک بار', 'starters/saas.json در این بسته نیست')
        iss, _ = lint('بهترین، واقعاً.', profile={'name': 'x', 'banned': ['بهترین']})
        t('v2 واژه‌ی ممنوع کنارِ «،»', [] if 'profile-banned' in codes_of(iss) else [codes_of(iss)])

        # ۱۶) --rules
        code, out, err = run_cli(['--rules', '--json'])
        pr = friendly(code, err, 0)
        try:
            d = json.loads(out)
            ids = [r['id'] for r in d['rules']]
            pr += ['نبود: %s' % x for x in MUST_LIST if x not in ids]
            if len(ids) != len(set(ids)):
                pr.append('شناسه‌ی تکراری')
            if any(r['severity'] not in ('error', 'warning') or not r['description'] for r in d['rules']):
                pr.append('سطح یا شرح')
            if sorted(d.get('formats', {})) != sorted(LF.FORMAT_IDS) or len(LF.FORMAT_IDS) != 26:
                pr.append('فهرستِ قالب‌ها')
            if set(d) != {'version', 'tool_version', 'rules', 'lexicon', 'jargon', 'formats'}:
                pr.append('شکلِ --rules --json: %s' % sorted(d))
        except ValueError:
            pr.append('JSON نیست')
        t('v2 --rules همه‌ی قاعده‌ها', pr, '%d قاعده' % len(LF.rule_list()))
        code, out, err = run_cli(['--rules'])
        t('v2 --rules متنی', [] if 'long-sentence' in out and 'caption' in out else ['ناقص'])

        # ۱۷) شکلِ یکدستِ --json
        pr = []
        for args in ([os.path.join(S, 'bad.txt')], [os.path.join(S, 'bad.txt'), os.path.join(S, 'good.txt')]):
            code, out, err = run_cli(args + ['--json'])
            d = json.loads(out)
            if set(d) != {'version', 'files', 'summary'} or d['version'] != 2:
                pr.append('ریشه: %s' % sorted(d))
            if set(d['summary']) != {'errors', 'warnings'} or len(d['files']) != len(args):
                pr.append('summary/files')
            for f in d['files']:
                if set(f) != {'path', 'issues', 'stats'}:
                    pr.append('فایل: %s' % sorted(f))
                for x in f['issues']:
                    if set(x) != {'line', 'col', 'key', 'rule', 'severity', 'message', 'excerpt'}:
                        pr.append('مسئله: %s' % sorted(x))
                        break
            if d['summary']['errors'] != sum(f['stats']['errors'] for f in d['files']):
                pr.append('جمعِ خطا')
        t('v2 شکلِ --json', pr)

        # ۱۸) مثبتِ کاذبِ موجِ دوم و قاعده‌های تازه
        wave2(t, skip, tmp)

        # ۱۸‌ب) موجِ سوم: «X، نه Y»، ویرگولِ پیش از «و»، «اقدام»، csv و tsv و بقیه
        wave3(t, skip, tmp)

        # ۱۹) آزمون‌های ابزارهای دیگر (اگر در این بسته باشند)
        tools = os.path.join(HERE, 'selftest_tools.py')
        if os.path.exists(tools):
            try:
                import selftest_tools  # noqa: E402
                results = selftest_tools.run() or []
                for name, ok, detail in results:
                    t('tools %s' % name, [] if ok else [detail or 'رد شد'], '' if not ok else (detail or ''))
            except Exception as e:
                t('tools selftest_tools', ['%s: %s' % (type(e).__name__, e)])
        else:
            skip('tools selftest_tools', 'در این بسته نیست')

        # ۲۰) والوری ۳: lint_en، lint.py و textcount (selftest_en) و سرورِ MCP (selftest_mcp)، اگر باشند
        for mod_name, prefix in (('selftest_en', 'en'), ('selftest_mcp', 'mcp'), ('selftest_profiles', 'profiles')):
            if not os.path.exists(os.path.join(HERE, mod_name + '.py')):
                skip('%s %s' % (prefix, mod_name), 'در این بسته نیست')
                continue
            try:
                mod = __import__(mod_name)
                for name, ok, detail in (mod.run() or []):
                    t('%s %s' % (prefix, name), [] if ok else [detail or 'رد شد'], '' if not ok else (detail or ''))
            except Exception as e:
                t('%s %s' % (prefix, mod_name), ['%s: %s' % (type(e).__name__, e)])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total, failed, skipped = counts
    tail = ' · %d پرش (فایلش در این بسته نیست)' % skipped if skipped else ''
    print('\n%s%s' % ('همه‌ی %d آزمون قبول' % total if not failed else '%d از %d آزمون رد شد' % (failed, total), tail))
    sys.exit(1 if failed else 0)


def wave2(t, skip, tmp):
    """آزمون‌های موجِ دوم: مرزِ «می»، «جهت»، «می‌گردد»، فهرست و جدول، lint-ignore،
    تعریفِ پیوند، strings.xml، واژه‌ی مرکب، جمله در پُررنگ، تقابلِ منفی، تقدمِ قالب،
    romanization و خطاب."""
    # ۱) «همیشه» محاوره‌ی «میشه» نیست
    pr = expect_codes([('این متن همیشه خوانده می‌شود و کوتاه است.', False),
                       ('همیشه خوب است و اگر بیاید.', False),
                       ('این در همیشه باز است.', False),
                       ('این کار نمیشه و این درست است.', True),
                       ('میشه کمک کنی؟ این کار درست است.', True)], 'mixed-register')
    if LF.COLLOQ.findall('همیشه') or LF.COLLOQ.findall('همیشگی'):
        pr.append('COLLOQ همیشه را گرفت')
    if not LF.COLLOQ.findall('نمیشه'):
        pr.append('COLLOQ نمیشه را نگرفت')
    if has('همیشه همین است.', 'register', profile={'name': 'x', 'register': 'formal'}):
        pr.append('register در پروفایلِ نوشتاری')
    t('w2 «همیشه» محاوره نیست', pr)

    # ۲) «جهتِ» فقط به معنای «برای»
    t('w2 «جهت» به معنای سو', expect_codes([
        ('جهتِ متن راست‌به‌چپ است.', False),
        ('قاعده‌ی جهت در متنِ فارسی ساده است.', False),
        ('جهت را از راست بگیر.', False),
        ('جهتِ بند را عوض نکن.', False),
        ('جهتِ نوشتن از راست است.', False),
        ('جهتِ اطلاعِ شما این پیام ارسال شد.', True),
        ('جهت خرید روی دکمه بزنید.', True),
        ('جهتِ ثبت‌نام فرم را پر کنید.', True),
        ('جهت رفاه حالِ مشتریان باز هستیم.', True)], 'admin-phrase'))

    # ۳) «می‌گردد» از «گشتن»
    t('w2 «می‌گردد» به معنای گشتن', expect_codes([
        ('کارجو دنبالِ خودش می‌گردد.', False),
        ('دنبال کار می‌گردند.', False),
        ('هر روز گیت‌هاب را می‌گردد.', False),
        ('همه‌جا را هر روز می‌گردد.', False),
        ('زمین دورِ خورشید می‌گردد.', False),
        ('پولتان تا سه روز باز می‌گردد.', False),
        ('مبلغ به حسابِ شما واریز می‌گردد.', True),
        ('سفارش پس از تأیید ارسال می‌گردد.', True),
        ('این فرم را پر کنید و درخواست ثبت می‌گردد.', True),
        ('از ما دور می‌گردد.', True)], 'admin'))

    # ۴) بندِ فهرست و خانه‌ی جدول هم جمله‌اند (--md و متن)
    pr = []
    for label, text, md in (
            ('بولت', '- ' + LONG, True), ('ستاره', '* ' + LONG, True), ('بعلاوه', '+ ' + LONG, True),
            ('شماره', '1. ' + LONG, True), ('شماره‌ی فارسی', '۱. ' + LONG, True),
            ('چک‌باکس', '- [ ] ' + LONG, True), ('چک‌باکسِ زده', '- [x] ' + LONG, True),
            ('نقل‌قول', '> ' + LONG, True), ('بولت در متن', '- ' + LONG, False),
            ('جدول', '| ستون | توضیح |\n|---|---|\n| یک | %s |' % LONG, True),
            ('جدول بی‌| آغازین', 'ستون | توضیح\n--- | ---\nیک | %s' % LONG, True),
            ('جدول در متن', '| یک | %s |' % LONG, False)):
        iss, st = lint(text, md=md)
        longs = [x for x in iss if x['code'] == 'long-sentence']
        if len(longs) != 1:
            pr.append('%s: long-sentence %d' % (label, len(longs)))
        elif longs[0]['text'].startswith(('-', '*', '+', '[', '|', '1', '۱', '>')):
            pr.append('%s: نشانه در گزیده «%s»' % (label, longs[0]['text'][:12]))
    t('w2 جمله‌ی بلند در فهرست و جدول', pr)
    pr = []
    if not has('- او گفت که کسی که آمد که ماند رفت.', 'ke-chain', md=True):
        pr.append('ke-chain در بند')
    if not has('| یک | این را و آن را ببین |', 'ra-chain', md=True):
        pr.append('ra-chain در خانه')
    if has('| این را ببین | آن را ببین |', 'ra-chain', md=True):
        pr.append('ra-chain دو خانه را یکی گرفت')
    if not has('- این اول است.\n- این دوم است.\n- این سوم است.\n', 'same-opening', md=True):
        pr.append('same-opening در بندها')
    if has('| بله | بله | بله |\n|---|---|---|\n| بله | بله | بله |\n', 'same-opening', md=True):
        pr.append('same-opening روی خانه‌های یک‌واژه‌ای')
    table = '| قالب | سقف |\n|---|---|\n' + ''.join('| کپشن %d | بیست واژه |\n' % k for k in range(8))
    if has(table, 'flat-rhythm', md=True):
        pr.append('flat-rhythm روی خانه‌های جدول')
    iss, st = lint('| ستون | توضیح |\n|:---|---:|\n', md=True)
    if st['sentences'] != 2:
        pr.append('سطرِ جداکننده جمله شد: %d' % st['sentences'])
    cells = LF._table_cells(LF.mask_prose('| `x|y` | متن \\| دوم |', 'md'))
    if len(cells) != 2:
        pr.append('| داخلِ کد یا \\| جداکننده شد: %d خانه' % len(cells))
    iss, _ = lint('**چای** را دم کن و آن را بنوش.', md=True)
    if 'long-sentence' in codes_of(iss) or LF._LIST_LEAD.match('**چای**').group('mark'):
        pr.append('سطرِ پُررنگ بند شمرده شد')
    t('w2 قاعده‌های جمله در فهرست و جدول', pr)

    # ۵) lint-ignore و کدِ درون‌خطی
    doc = ('متنِ سالم است.\n<!-- lint-ignore -->\nاین كالا بی‌نظیر است — نه این!!\n'
           '<!-- /lint-ignore -->\nاین كالا خوب است.\n')
    pr = []
    for md in (False, True):
        iss, st = lint(doc, md=md)
        if [(x['code'], x['line']) for x in iss] != [('arabic-kaf', 5)]:
            pr.append('%s: %s' % ('md' if md else 'متن', [(x['code'], x['line']) for x in iss]))
    iss, _ = lint('سالم است.\n<!-- lint-ignore -->\nاین كالا بی‌نظیر است!!\nاین هم كالا.\n')
    if iss:
        pr.append('نشانه‌ی بی‌بسته تا پایان نادیده نگرفت: %s' % codes_of(iss))
    fenced = '```md\n<!-- lint-ignore -->\n```\nاین كالا خوب است.\n'
    if not has(fenced, 'arabic-kaf', md=True):
        pr.append('نشانه‌ی داخلِ بلوکِ کد دستور شمرده شد')
    if not has('<!-- /lint-ignore -->\nاین كالا خوب است.\n', 'arabic-kaf'):
        pr.append('نشانه‌ی بسته‌ی تنها چیزی را پوشاند')
    if not has('این <!-- lint-ignore --> كالا خوب است.', 'arabic-kaf'):
        pr.append('نشانه‌ی وسطِ سطر دستور شمرده شد')
    crlf = doc.replace('\n', '\r\n')
    fx, _ = fix_text(crlf)
    if 'این كالا بی‌نظیر است — نه این!!' not in fx or 'این کالا خوب است.' not in fx:
        pr.append('--fix بخشِ نادیده را عوض کرد یا بقیه را اصلاح نکرد')
    t('w2 lint-ignore', pr)
    pr = []
    for text in ('این `بی‌نظیر` و `می باشد` و `نمایید` است.',
                 '| نه این | این |\n|---|---|\n| `کالای بی‌نظیر می باشد` | کالای خوب است |'):
        iss, _ = lint(text, md=True)
        bad = [x['code'] for x in iss if x['code'] in ('lexicon', 'admin', 'ellipsis', 'zwnj-mi')]
        if bad:
            pr.append('%s: %s' % (text[:20], bad))
    t('w2 کدِ درون‌خطی در --md پوشانده است', pr)

    # ۶) «[نامِ کلینیک]: …» تعریفِ پیوند نیست
    pr = []
    for md in (False, True):
        iss, st = lint('[نامِ کلینیک]: ' + LONG, md=md)
        if 'long-sentence' not in codes_of(iss):
            pr.append('پیشوندِ فرستنده سنجیده نشد (%s)' % ('md' if md else 'متن'))
    for ref in ('[1]: https://example.com/a', '[راهنما]: ./references/a.md "عنوان"', '[x]: <b.md>',
                '[بخش]: #بخشِ-اول'):
        iss, st = lint(ref + '\n', md=True)
        if st['sentences'] or iss:
            pr.append('تعریفِ پیوند سنجیده شد: %s' % ref)
    t('w2 پیشوندِ «[نام]:» و تعریفِ پیوند', pr)

    # ۷) strings.xml اندروید با <xliff:g>
    xml = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<!-- برای نام‌ها <xliff:g> بگذار؛ <xliff version="1.2"> این فایل نیست -->\n'
           '<resources xmlns:xliff="urn:oasis:names:tc:xliff:document:1.2">\n'
           '    <string name="hi">سلام <xliff:g id="shop" example="چای">دارچین — خانه</xliff:g>، '
           'لطفاً دوباره تلاش نمایید.</string>\n'
           '</resources>\n')
    pr = []
    ents = LF.extract_locale(xml, 'res/values-fa/strings.xml')
    if [e[0] for e in ents] != ['hi']:
        pr.append('کلیدها: %s' % [e[0] for e in ents])
    iss, st = LF.lint_locale(xml, 'strings.xml')
    got = set((x['key'], x['code']) for x in iss)
    if ('hi', 'admin') not in got:
        pr.append('«نمایید» دیده نشد')
    if ('hi', 'dash') in got:
        pr.append('درونِ <xliff:g> سنجیده شد')
    if LF._xml_root(xml) != 'resources':
        pr.append('ریشه: %s' % LF._xml_root(xml))
    x2 = '<?xml version="1.0"?>\n<xliff version="2.0"><file><unit id="u1"><segment><source>Hi</source>' \
         '<target>سلام — دوست</target></segment></unit></file></xliff>\n'
    if [e[0] for e in LF.extract_locale(x2, 'app.xml')] != ['u1']:
        pr.append('XLIFFِ .xml خوانده نشد')
    t('w2 strings.xml با <xliff:g>', pr, '%d رشته' % st['strings'])

    # ۸) واژه‌ی مرکب با نیم‌فاصله واژه‌ی دیگری است؛ پسوند همان واژه است
    pr = []
    for text, want in (('این اصالت‌بازی است.', False), ('کهن‌سالانِ محله آمدند.', False),
                       ('این اصالت‌ها مهم است.', True), ('پلتفرم‌های ما تازه است.', True),
                       ('راهکار‌هایمان ساده است.', True), ('بی‌نظیر‌ترین روز است.', True),
                       ('این اصالتِ کار است.', True)):
        if has(text, 'lexicon') != want:
            pr.append('%s lexicon: %s' % ('نبود' if want else 'نباید', text))
    brand = load_profile(prof_path(BRAND))
    for text, want in (('این پکیج‌ها رسید.', True), ('این پکیج‌سازی است.', False),
                       ('همه‌ی آیتم‌هاش رسید.', True), ('آیتم‌ساز ندارد.', False)):
        if has(text, 'profile-avoid', profile=brand) != want:
            pr.append('%s avoid: %s' % ('نبود' if want else 'نباید', text))
    t('w2 واژه‌ی مرکب و پسوند', pr)

    # ۹) پایانِ جمله داخلِ پُررنگ و «?»
    pr = []
    for text, n in (('**این را بکن.** بعد آن را ببین.', 2), ('__چرا؟__ چون دیر است.', 2),
                    ('*کوتاه!* بعد بلند.', 2), ('کجا? اینجا.', 2), ('این را بکن. بعد آن را ببین.', 2)):
        iss, st = lint(text)
        if st['sentences'] != n or 'ra-chain' in codes_of(iss):
            pr.append('%s: %d جمله %s' % (text, st['sentences'], codes_of(iss)))
    if len([p for p in LF.SENT_SPLIT.split('**یک.** دو.') if p.strip()]) != 2:
        pr.append('SENT_SPLIT')
    t('w2 پایانِ جمله داخلِ پُررنگ', pr)

    # ۱۰) تقابلِ منفی فقط با نیمه‌ی مثبتِ هم‌شخص در همان جمله
    t('w2 neg-contrast', expect_codes([
        ('باید روشن باشد چه کاری مجاز نیست، و به‌روزرسانیِ بعدی تا کِی است.', False),
        ('این متن مشاوره‌ی حقوقی نیست؛ پیش از انتشار با وکیل بازبینی شود. این یک نمونه است.', False),
        ('این متن مشاوره‌ی حقوقی نیست؛ پیش از انتشار با وکیل بازبینی شود و این لازم است.', False),
        ('این کار آسان نیست، ولی شدنی است.', False),
        ('قیمت ثابت نیست، ماست هم گران شد.', False),
        ('ما شرکتِ بزرگی نیستیم، مشتری‌ها راضی هستند.', False),
        ('ما فقط یک فروشگاه نیستیم، ما یک خانواده هستیم.', True),
        ('این یک فروشگاه نیست، یک خانواده است.', True),
        ('ما شرکت نیستیم؛ یک تیمِ کوچک هستیم.', True),
        ('اینجا کافه نیست، بلکه یک خانه است.', True),
        ('ما فروشگاه نیستیم، خانواده%sایم.' % ZWNJ, True)], 'neg-contrast'))

    # ۱۱) تقدم (D1): پیش‌فرضِ قالب فقط سخت‌تر می‌کند؛ romanization (D3)
    pr = []
    rs = LF.resolve_settings
    for prof, fmt, key, want in (
            ({'max_words': 14}, 'caption', 'max_words', 14),
            ({'max_words': 30}, 'ui', 'max_words', 14),
            ({'dials': {'sentence_length': 1}}, 'sms', 'max_words', 14),
            ({'dials': {'sentence_length': 5}}, 'sms', 'max_words', 16),
            ({'emoji_max': 2}, 'ui', 'emoji_max', 0),
            ({'emoji_max': 2}, 'caption', 'emoji_max', 2),
            ({'exclaim_max': 1}, 'press', 'exclaim_max', 0),
            ({'max_words': 18, 'formats': {'caption': {'max_words': 22}}}, 'caption', 'max_words', 22),
            ({'max_words': 18, 'formats': {'caption': {'dials': {'sentence_length': 4}}}}, 'caption', 'max_words', 28),
            ({}, None, 'emoji_max', 0), ({}, None, 'exclaim_max', 0), ({}, 'caption', 'max_words', 20)):
        got = rs(prof, fmt)[key]
        if got != want:
            pr.append('%s/%s %s=%s، انتظار %s' % (prof, fmt, key, got, want))
    if rs({'max_words': 14}, 'caption')['sources']['max_words'] != 'profile':
        pr.append('منبعِ سقف باید پروفایل بماند')
    if any('address' in v for v in LF.FORMAT_DEFAULTS.values()):
        pr.append('FORMAT_DEFAULTS خطاب دارد')
    if rs({'address': 'to'}, 'ui')['address'] != 'to':
        pr.append('قالب خطاب را عوض کرد')
    cafe = prof_path('starters/cafe.json')
    if cafe:
        cp = load_profile(cafe)
        want = min(LF.resolve_settings(cp)['max_words'], LF.FORMAT_DEFAULTS['caption']['max_words'])
        if 'max_words' not in ((cp.get('formats') or {}).get('caption') or {}) \
                and rs(cp, 'caption')['max_words'] != want:
            pr.append('کافه/کپشن: %s، انتظار %s' % (rs(cp, 'caption')['max_words'], want))
    t('w2 تقدم: قالب فقط سخت‌تر (D1)', pr)
    pr = []
    vp = LF.validate_profile
    if vp({'name': 'x', 'romanization': {'ترنج‌نو': 'Toranjno'}}):
        pr.append('romanization معتبر رد شد')
    if 'profile-invalid' not in [c for c, _ in vp({'name': 'x', 'romanization': ['Toranjno']})]:
        pr.append('فهرست به‌جای شیء پذیرفته شد')
    if 'profile-invalid' not in [c for c, _ in vp({'name': 'x', 'romanization': {'ترنج': 'ترنج'}})]:
        pr.append('املای لاتینِ فارسی پذیرفته شد')
    if 'profile-invalid' not in [c for c, _ in vp({'name': 'x', 'romanization': {'ترنج': ''}})]:
        pr.append('املای خالی پذیرفته شد')
    brand_raw = json.loads(LF.read_text(prof_path(BRAND)))
    pr += ['brand-profile: %s' % m for _, m in vp(brand_raw)]
    if rs(load_profile(prof_path(BRAND)))['romanization'].get('ترنج‌نو') != 'Toranjno':
        pr.append('romanization به تنظیم نرسید')
    t('w2 romanization (D3)', pr)

    # ۱۲) خطاب: با profile_stats (اگر باشد) و با فهرستِ جایگزین
    shoma = {'name': 'x', 'address': 'shoma'}
    to = {'name': 'x', 'address': 'to'}
    cases = [
        ('کیک رو تو فر بذارید و تو خونه بخورین؛ توی کیف هم جا می‌شه.', shoma, False),
        ('این رو گرم کنین و بخورین.', to, True),
        ('این رو گرم کنین و بخورین.', shoma, False),
        ('ما تو را دوست داریم.', shoma, True),
        ('اگه دوست داری، باهات تماس می‌گیریم.', shoma, True),
        ('او هر روز می‌آید و چیزی می‌گوید.', to, False),
        ('بدهیِ شما تا فردا تسویه می‌شود.', shoma, False),
    ]
    saved = list(LF._PS_COUNT)
    try:
        backends = [('فهرستِ جایگزین', [None])]
        LF._PS_COUNT[:] = []
        if LF._ps_count_address() is not None:
            backends.insert(0, ('profile_stats', list(LF._PS_COUNT)))
        else:
            skip('w2 خطاب با profile_stats', 'profile_stats.py در این بسته نیست')
        for name, state in backends:
            LF._PS_COUNT[:] = state
            pr = []
            for text, prof, want in cases:
                if has(text, 'address', profile=prof) != want:
                    pr.append('%s %s (%s)' % ('نبود' if want else 'نباید', text[:30], prof['address']))
            t('w2 خطاب با %s' % name, pr)
    finally:
        LF._PS_COUNT[:] = saved


def wave3(t, skip, tmp):
    """آزمون‌های موجِ سوم: «X، نه Y»، ویرگولِ پیش از «و»، «اقدام»، csv و tsv، پایانِ جمله پس از
    «»»، شمارِ واژه، پسوندِ نسخه‌ی هسته، لحن در نقل‌قول، same-opening در جدول، الگو و
    node_modules، drop_ignored و واژه‌ی «پاره»."""
    # ۱) «X، نه Y»
    t('w3 na-contrast', expect_codes([
        ('سایزها رو با متر گرفتیم، نه با حدس.', True),
        ('کوتاه، نه خشک', True),
        ('قیمت را از دستِ خودش می‌گیرد، نه از ما.', True),
        ('در این لحن، لوکس یعنی وقت و توجه؛ نه صفت.', True),
        ('نتیجه «هدف» است، نه «وعده».', True),
        ('**کوتاه، نه خشک.** بعد بقیه.', True),
        ('ما از او، نه از خودمان، پرسیدیم.', True),
        ('آیا دیر شده؟ نه، هنوز وقت داریم.', False),
        ('نه پول دارد، نه وقت.', False),
        ('فقط کیفیت، نه قیمت، نه برند.', False),
        ('این کار، نه تنها سخت که گران هم هست.', False),
        ('این کار، نه فقط برای ما مهم است.', False),
        ('نمی‌دانم درست است، یا نه.', False),
        ('بپرس آمده یا نه، بعد برو.', False),
        ('هفت، هشت، نه و ده.', False),
        ('قشنگ است، نه؟', False),
        ('این یکی را می‌خواهی، نه آن یکی؟', False),
        ('خیر، نه این بار.', False),
        ('این چای، نهالِ تازه است.', False),
        ('کار را کردیم، نه با این ابزارِ خیلی گرانِ تازه‌ی وارداتی.', False),
        ('خیلی بد، بد، نه بد نه خوب، خوب، خیلی خوب', False),
        ('دو پرسشِ باز، نه بیشتر.', False),
        ('سه هشتگ، نه کم‌تر.', False),
        ('خانه‌ای در شمال، نه چندان دور از دریا.', False),
        ('بیست تا، نه ببخشید، بیست و پنج تا.', False),
        ('فقط دو هشتگ، نه یک فهرستِ بلند.', True)], 'na-contrast'))
    pr = []
    if not has('| کوتاه، نه خشک | بلند |\n', 'na-contrast', md=True):
        pr.append('خانه‌ی جدول')
    iss, _ = lint('سایزها رو با متر گرفتیم، نه با حدس.')
    x = [i for i in iss if i['code'] == 'na-contrast']
    if not x or x[0]['level'] != 'warning' or x[0]['col'] != 26:
        pr.append('سطح یا ستون: %s' % [(i['level'], i['col']) for i in x])
    if has('<!-- lint-ignore -->\nکوتاه، نه خشک.\n<!-- /lint-ignore -->\n', 'na-contrast', md=True):
        pr.append('lint-ignore')
    t('w3 na-contrast در جدول، ستون و lint-ignore', pr)

    # ۲) ویرگولِ پیش از «و»ِ آخرِ فهرست
    t('w3 serial-comma', expect_codes([
        ('کیفیت، اعتماد، و اصالت.', True),
        ('رنگش سفید، آبی، و سبز است.', True),
        ('آرد، شکر، کره، و تخم‌مرغ لازم است.', True),
        ('آرد، شکر و کره لازم است.', False),
        ('این چای را چیدیم، و همان هفته خشک کردیم.', False),
        ('وقتی رسیدیم، بار را از ماشین پایین آوردیم، و بعد چای خوردیم.', False),
        ('قیمت ثابت است، ولی ما تخفیف می‌دهیم، و این هفته تمام می‌شود.', False),
        ('سه، چهار، ولی نه بیشتر.', False),
        ('از خواننده داده جمع می‌کنیم، با اطلاعش، و با آن کارِ دیگری نمی‌کنیم.', False),
        ('اول کیفیت، نه قیمت، و بعد برند.', False),
        ('سه چیز مهم است: کیفیت، اعتماد، و اصالت که همه می‌شناسند.', True),
        ('در تهران شعبه هست، در شیراز دو تا، و در تبریز یکی.', True)], 'serial-comma'))
    iss, _ = lint('کیفیت، اعتماد، و اصالت.')
    x = [i for i in iss if i['code'] == 'serial-comma']
    t('w3 serial-comma هشدار است و ستونش ویرگولِ دوم', [] if x and x[0]['level'] == 'warning' and x[0]['col'] == 14
      else ['%s' % [(i['level'], i['col']) for i in x]])

    # ۳) ساختِ «اقدام»
    t('w3 admin-phrase «اقدام»', expect_codes([
        ('برای تمدید اقدام کنید.', True),
        ('لطفاً نسبت به تمدیدِ اشتراک اقدام نمایید.', True),
        ('اقدام به خرید نمایید.', True),
        ('قبل از پایانِ مهلت اقدام بفرمایید.', True),
        ('نسبت به پرداختِ قبض اقدام شود.', True),
        ('دولت باید سریع اقدام کند.', False),
        ('این اقدامِ خوبی بود.', False),
        ('نسبت به پارسال گران‌تر است و اقدام کردیم.', False),
        ('قیمت نسبت به پارسال بالا رفت.', False)], 'admin-phrase'))
    pr = []
    c = codes_of(lint('لطفاً اقدام نمایید.')[0])
    if 'admin' not in c or 'admin-phrase' not in c:
        pr.append('«اقدام نمایید»: %s' % c)
    c = codes_of(lint('برای تمدید اقدام کنید.')[0])
    if 'admin' in c:
        pr.append('«اقدام کنید» خطای admin شد')
    t('w3 «اقدام نمایید» هم admin هم admin-phrase', pr)

    # ۴) --rules
    code, out, err = run_cli(['--rules', '--json'])
    pr = friendly(code, err, 0)
    try:
        rows = dict((r['id'], r) for r in json.loads(out)['rules'])
        for rid in ('na-contrast', 'serial-comma'):
            if rows.get(rid, {}).get('severity') != 'warning':
                pr.append('%s: %s' % (rid, rows.get(rid)))
        d = rows.get('na-contrast', {}).get('description', '')
        pr += ['شرحِ na-contrast «%s» ندارد' % w for w in ('نه تنها', 'یا نه', '«نه … نه …»', 'پرسش') if w not in d]
        if 'اقدام' not in rows.get('admin-phrase', {}).get('description', ''):
            pr.append('admin-phrase از «اقدام» نمی‌گوید')
    except ValueError:
        pr.append('JSON نیست')
    code, out, err = run_cli(['--rules'])
    pr += [] if 'na-contrast' in out and 'serial-comma' in out and 'csv' in out else ['--rules متنی ناقص']
    t('w3 --rules قاعده‌های تازه', pr)

    # ۵) csv و tsv
    cat = os.path.join(S, 'catalog.csv')
    must = {('row 3/A-102/desc', 'bang-bang', 3), ('row 3/A-102/desc', 'na-contrast', 3),
            ('row 3/A-102/desc', 'bangs', 3), ('row 3/A-102/title', 'latin-comma', 3),
            ('row 4/A-103/desc', 'serial-comma', 5), ('row 6/-/desc', 'admin', 7),
            ('row 6/-/desc', 'admin-phrase', 7)}
    only = re.compile(r'row \d+/[^/]+/(?:title|desc)$')

    def csv_check(iss, st, label, lines=True):
        pr = []
        got = set((x['key'], x['code'], x['line']) for x in iss)
        want = must if lines else set((k, c) for k, c, _ in must)
        have = got if lines else set((k, c) for k, c, _ in got)
        pr += ['%s نبود: %s' % (label, m) for m in sorted(want - have)]
        pr += ['%s ستونِ دیگر: %s/%s' % (label, x['key'], x['code']) for x in iss if not only.match(x['key'] or '')]
        pr += ['%s جداکننده سنجیده شد' % label for x in iss
               if x['code'] == 'latin-comma' and x['key'] != 'row 3/A-102/title']
        pr += ['%s «می باشد»ِ ستونِ note' % label for x in iss if 'باشد' in (x['text'] or '')]
        if (st.get('kind'), st.get('rows'), st.get('cells'), st.get('columns'), st.get('key_column')) != \
                ('csv', 5, 8, ['title', 'desc'], 'sku'):
            pr.append('%s آمار: %s' % (label, {k: st.get(k) for k in ('kind', 'rows', 'cells', 'columns',
                                                                       'key_column')}))
        return pr

    iss, st = LF.lint_file(cat)
    pr = csv_check(iss, st, 'csv')
    if (st['errors'], st['rows_flagged']) != (2, 3):
        pr.append('خطا %d، ردیفِ مسئله‌دار %d' % (st['errors'], st['rows_flagged']))
    t('w3 csv: هر خانه جدا، کلیدِ row/کد/ستون', pr, 'خطا %d · هشدار %d' % (st['errors'], st['warnings']))

    raw = LF.read_text(cat).replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10))
    pr = []
    for name, data in (
            ('catalog.tsv', raw.replace(',', '\t').replace('مدادِ مشکی\t نرم', 'مدادِ مشکی, نرم')),
            ('bom-crlf.csv', LF.BOM + raw.replace('\n', '\r\n')),
            ('semi.csv', raw.replace(',', ';').replace('مدادِ مشکی; نرم', 'مدادِ مشکی, نرم'))):
        fp = os.path.join(tmp, name)
        wbytes(fp, data.encode('utf-8'))
        try:
            iss, st = LF.lint_file(fp)
            pr += csv_check(iss, st, name)
        except LF.UserError as e:
            pr.append('%s: %s' % (name, e))
    iss, st = LF.lint(raw, kind='csv')
    pr += csv_check(iss, st, 'lint(kind=csv)')
    t('w3 tsv، BOM و CRLF، «;» و API', pr)

    pr = []
    code, out, err = run_cli([cat, '--json'])
    pr += friendly(code, err, 1)
    try:
        d = json.loads(out)
        f = d['files'][0]
        if set(d) != {'version', 'files', 'summary'} or set(f) != {'path', 'issues', 'stats'}:
            pr.append('شکل: %s / %s' % (sorted(d), sorted(f)))
        if any(set(x) != {'line', 'col', 'key', 'rule', 'severity', 'message', 'excerpt'} for x in f['issues']):
            pr.append('شکلِ مسئله')
        if not all((x['key'] or '').startswith('row ') for x in f['issues']):
            pr.append('کلید')
        if d['summary'] != {'errors': 2, 'warnings': f['stats']['warnings']}:
            pr.append('summary: %s' % d['summary'])
    except (ValueError, KeyError, IndexError) as e:
        pr.append('JSON: %s' % e)
    code, out, err = run_cli([cat])
    if 'catalog.csv#row 3/A-102/desc' not in out or '5 ردیف (3 با مسئله)' not in out or 'کلید: sku' not in out:
        pr.append('خروجیِ متنی: %r' % out[-200:])
    t('w3 csv در خطِ فرمان: JSON یکسان و خلاصه‌ی فایل', pr)

    pr = []
    code, out, err = run_cli([cat, '--csv-columns', 'desc', '--csv-key', 'price', '--json'])
    try:
        keys = [x['key'] for x in json.loads(out)['files'][0]['issues']]
        if not keys or any(not re.match(r'row \d+/\d+/desc$', k) for k in keys):
            pr.append('--csv-columns/--csv-key: %s' % keys[:4])
    except (ValueError, KeyError, IndexError):
        pr.append('JSON نیست: %r' % (out[:80] + err[-120:]))
    for args, word in (([cat, '--csv-columns', 'nope'], 'sku'), ([cat, '--csv-key', 'nope'], 'sku')):
        code, out, err = run_cli(args)
        pr += friendly(code, err) + ([] if word in err else ['فهرستِ ستون‌ها نیامد'])
    nt = os.path.join(tmp, 'numbers.csv')
    wbytes(nt, 'sku,price\nA,1\n'.encode('utf-8'))
    code, out, err = run_cli([nt])
    pr += friendly(code, err) + ([] if '--csv-columns' in err else ['راهنمای --csv-columns نیامد'])
    code, out, err = run_cli(['-', '--csv-columns', 'desc', '--json'], stdin=raw.encode('utf-8'))
    try:
        keys = [x['key'] for x in json.loads(out)['files'][0]['issues']]
        if 'row 6/-/desc' not in keys or any(k.endswith('/title') for k in keys):
            pr.append('ورودیِ استاندارد: %s' % keys[:4])
    except (ValueError, KeyError, IndexError):
        pr.append('ورودیِ استاندارد JSON نیست')
    fx = os.path.join(tmp, 'fix.csv')
    shutil.copy(cat, fx)
    before = rbytes(fx)
    code, out, err = run_cli([fx, '--fix', '--write'])
    if rbytes(fx) != before or 'csv' not in err or code not in (0, 1):
        pr.append('--fix روی csv: خروج %s؛ %s' % (code, err[-100:]))
    code, out, err = run_cli(['--text', 'سلام.', '--csv-columns', 'x'])
    if code != 0 or '--csv-columns' not in err:
        pr.append('هشدارِ --csv-columns بی csv')
    # سرستونِ خروجی‌های رایج: camelCase، «نامِ»ِ ووکامرس، کلیدِ productId؛ «width» کلید نیست
    ex = os.path.join(tmp, 'export.csv')
    wbytes(ex, ('width,productId,metaTitle,shortDescription,نامِ کالا,نامه,price\n'
                'W1,P-1,کیفیت، اعتماد، و اصالت.,خوب است.,مداد,این متن می باشد.,500\n').encode('utf-8'))
    try:
        iss, st = LF.lint_file(ex)
        if (st.get('columns'), st.get('key_column')) != (['metaTitle', 'shortDescription', 'نامِ کالا'], 'productId'):
            pr.append('سرستونِ خروجی: %s / %s' % (st.get('columns'), st.get('key_column')))
        if ('row 2/P-1/metaTitle', 'serial-comma') not in set((x['key'], x['code']) for x in iss):
            pr.append('کلیدِ خروجی: %s' % [(x['key'], x['code']) for x in iss][:3])
    except LF.UserError as e:
        pr.append('سرستونِ خروجی: %s' % e)
    t('w3 csv: ستون، کلید، خطای دوستانه، stdin و --fix', pr)

    # ۶) پایانِ جمله پس از گیومه‌ی بسته؛ «،» واژه نیست؛ پسوندِ هسته
    pr = []
    for text, n in (('«این را ببینید.» این یکی هم هست.', 2), ('«کجا؟» · «کی؟» · «چرا؟»', 3),
                    ('گفت «بیا!» و رفت.', 2), ('(این را ببین.) بعد برو.', 2)):
        st = lint(text)[1]
        if st['sentences'] != n:
            pr.append('%s: %d جمله' % (text, st['sentences']))
    for text, md, n in (('`a_b`، `c_d`، `e_f`، `g_h` را ببین.', True, 2), ('الف ، ب ، ج', False, 3),
                        ('۲٬۵۰۰ تومان.', False, 2)):
        st = lint(text, md=md)[1]
        if st['avg_words'] != n:
            pr.append('%s: %s واژه' % (text, st['avg_words']))
    body = 'این ' + ' '.join(['واژه'] * 22)
    if has(body + ' (در والوری حرفه‌ای).', 'long-sentence'):
        pr.append('پسوندِ هسته شمرده شد')
    if not has(body + ' (در نسخه‌ی دیگر).', 'long-sentence'):
        pr.append('پرانتزِ معمولی شمرده نشد')
    t('w3 پایانِ جمله، شمارِ واژه و پسوندِ هسته', pr)

    # ۷) لحن و نشانه‌ها در نقل‌قول
    pr = []
    if has('این محصول در خانه تهیه می‌شود. مشتری نوشت: «خیلی خوشمزه‌ست، اون یکی رو هم بفرستین».',
           'mixed-register'):
        pr.append('«…» لحنِ نویسنده شمرده شد')
    if has('این متن نوشتاری است و خوب است.\n\n> این حلوا رو گرم کنین؛ خوشمزه‌تره.\n', 'mixed-register', md=True):
        pr.append('بلوکِ نقل‌قول لحنِ نویسنده شمرده شد')
    iss, _ = lint('متن است.\n\n> این حلوا رو گرم کنین. این محصول در خانه تهیه می‌شود.\n', md=True)
    x = [i for i in iss if i['code'] == 'mixed-register']
    if not x or x[0]['line'] != 3 or 'نقل‌قول' not in x[0]['message']:
        pr.append('لحنِ مخلوطِ داخلِ بلوک: %s' % [(i['line'], i['message'][-12:]) for i in x])
    if not has('> این حلوا رو گرم کنین. این محصول در خانه تهیه می‌شود.\n', 'mixed-register'):
        pr.append('بی --md «>» نقل‌قول شمرده شد')
    if has('متنِ آرام است.\n\n> عالیه! خیلی خوبه!\n', 'bangs', md=True):
        pr.append('تعجبِ نقل‌قول شمرده شد')
    if not has('متنِ آرام است.\n\n> عالیه! خیلی خوبه!\n', 'bangs'):
        pr.append('بی --md تعجب شمرده نشد')
    if not has('این حلوا رو گرم کنین. این محصول در خانه تهیه می‌شود.', 'mixed-register'):
        pr.append('لحنِ مخلوطِ عادی دیده نشد')
    t('w3 لحن و نشانه در نقل‌قول', pr)

    # ۸) same-opening: خانه‌ی جدول شمرده نمی‌شود و زنجیره را می‌بُرد؛ بندِ فهرست شمرده می‌شود
    pr = []
    row = ('| الگو | «برای کسی که صبح زود بیدار می‌شود» | برای کسی که شب کار می‌کند | '
           'برای کسی که دیر می‌خوابد |\n')
    if has('| نام | الف | ب | پ |\n|---|---|---|---|\n' + row, 'same-opening', md=True):
        pr.append('خانه‌های یک ردیف')
    col = ('| نام | متن |\n|---|---|\n| سلامت | سلامت و بدن و خواب |\n'
           '| سلامت | سلامت و بدن و خواب |\n| سلامت | سلامت و بدن و خواب |\n')
    if has(col, 'same-opening', md=True):
        pr.append('یک ستون در سه ردیف')
    items = '- برای کسی که صبح زود بیدار می‌شود\n- برای کسی که شب کار می‌کند\n- برای کسی که دیر می‌خوابد\n'
    if not has(items, 'same-opening', md=True):
        pr.append('سه بندِ فهرست')
    if has('- برای کسی که صبح زود بیدار می‌شود\n- برای کسی که شب کار می‌کند\n\n| جدول | این |\n|---|---|\n'
           '| یک | دو سه چهار |\n\n- برای کسی که دیر می‌خوابد\n', 'same-opening', md=True):
        pr.append('جدول زنجیره را نبُرید')
    t('w3 same-opening در فهرست و جدول', pr)

    # ۹) الگو و node_modules؛ drop_ignored؛ «پاره»
    pr = []
    posts = os.path.join(tmp, 'posts')
    os.makedirs(os.path.join(posts, 'node_modules', 'pkg'))
    wbytes(os.path.join(posts, 'a.md'), 'متن.'.encode('utf-8'))
    wbytes(os.path.join(posts, 'node_modules', 'pkg', 'b.md'), 'متن.'.encode('utf-8'))
    for pat in (os.path.join(posts, '*'), os.path.join(posts, '**', '*.md')):
        got = [os.path.basename(x) for x in LF.iter_paths([pat])]
        if got != ['a.md']:
            pr.append('%s → %s' % (os.path.basename(pat), got))
    got = [os.path.basename(x) for x in LF.iter_paths([os.path.join(posts, 'node_modules', 'pkg', '*.md')])]
    if got != ['b.md']:
        pr.append('الگوی صریح در node_modules: %s' % got)
    t('w3 الگو وارد node_modules نمی‌شود', pr)
    pr = []
    src = 'الف\n<!-- lint-ignore -->\nبد\n<!-- /lint-ignore -->\nب\n'
    if LF.drop_ignored(src) != 'الف\n\n\n\nب\n':
        pr.append(repr(LF.drop_ignored(src)))
    fenced = '```\n<!-- lint-ignore -->\n```\nب\n'
    if LF.drop_ignored(fenced) != fenced:
        pr.append('نشانه‌ی داخلِ بلوکِ کد')
    if LF.drop_ignored('سالم.\n') != 'سالم.\n':
        pr.append('متنِ بی‌نشانه عوض شد')
    t('w3 drop_ignored', pr)
    pr = []
    iss, _ = lint('س' * 140, channel=LF.resolve_channel('testsms', CH_DIR))
    msg = ' '.join(x['message'] for x in iss if x['code'] == 'channel-length')
    if 'پاره' not in msg or 'بخش' in msg:
        pr.append(msg[:80])
    t('w3 واژه‌ی «پاره» برای بخشِ پیامک', pr)


if __name__ == '__main__':
    main()
