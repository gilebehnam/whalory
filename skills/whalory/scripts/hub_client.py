#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hub_client: the Whalory Hub command line and scheduler (spec 4.3 to 4.10, 5.6 to 5.8, 5.10, 17.3).

Standard library only, Python 3.8 to 3.14. The only Hub module that opens sockets.

    python hub_client.py <command> [options]

    status [--json]                      toggles, pending request, consent, overlays, queue
    consent [--lang fa|en]               the consent screen for weekly statistics (console only)
    on stats | on phrases [--preview] | on packets        (console only, typed code)
    off [stats|phrases|packets|updates|all]               (default stats; works offline)
    packet [--show] [--week YYYY-Www] [--lang fa|en|both] [--save FILE] [--json]
                                         the weekly packet you may post yourself; sends nothing
    report [--week YYYY-Www] [--json]    the built weekly report (Pro; closed until collection opens)
    upload [--now]                       sends due reports (Pro; closed until collection opens)
    preview [--approve | --drop N...]    phrase rows waiting for your approval
    forget  (alias: delete)              off for every lane, delete the Hub data, new install salt
    log [--events | --sent | --net] [--json]
    sync [--force]                       signed rule updates (at most once a day unless --force)
    tick [--quiet] [--detach] [--host NAME]   what the session-start hooks run; prints nothing
    pin baseline|bundled|<overlay id> ; unpin ; rollback
    verify FILE                          debug: verify one signed file (exit 4 on failure)
    pinned-root [--json] [--require-production]   is data/hub/root.json the public test root?

Exit codes: 0 success (always for tick), 2 usage error, 3 no console for an interactive
command, 4 verification failure (verify), 5 pinned-root --require-production on a test root.

Test-only flags (spec 5.10; never used by hooks): --test, --hub-home DIR (inside the system
temp folder), --mirror URL (repeatable), --collector URL, --issuer URL. --test allows
http://127.0.0.1 URLs and never reads secret.json or the licence environment variables.

Consent (spec 4.1, 4.3): only a person at a console turns a tier on. Answers are read from
the console device (/dev/tty or CONIN$), never from stdin, and only when stdin and stdout
are terminals; turning a tier on also needs a typed 4-character code. Environment variables
and host settings can only lower a setting or create a pending request.
"""
from __future__ import print_function

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import base64  # noqa: E402
import datetime  # noqa: E402
import hashlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import locale  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import hub_events as HE  # noqa: E402
import hub_mine as HM  # noqa: E402

UTC = datetime.timezone.utc
USER_AGENT = 'whalory-hub/1'
TIMEOUT = 10
MAX_REDIRECTS = 3
TICK_NET_SECONDS = 8.0
TICK_NET_BYTES = 512 * 1024
SHOP_CAP = 16 * 1024
LOCK_STALE = 120
LOG_LINES = 1000
FOLDER_CAP = 5 * 1024 * 1024
SYNC_EVERY = datetime.timedelta(hours=24)
FIRST_UPLOAD_WAIT = datetime.timedelta(hours=72)
TOKEN_GAP = datetime.timedelta(hours=24)
UPLOAD_WINDOW = datetime.timedelta(hours=48)
DEADLINE = datetime.timedelta(days=21)
SERVER_RETENTION = datetime.timedelta(days=22)
KEEP_WEEKS = datetime.timedelta(weeks=5)
RETRY = (3600, 4 * 3600, 12 * 3600, 24 * 3600)
MAX_UPLOADS = 4
CODE_ALPHABET = '23456789'
_PLACEHOLDER = re.compile(r'\{[A-Z_]+\}')
_EPOCH = re.compile(r'^[0-9]{4}-W(0[1-9]|[1-4][0-9]|5[0-3])$')
_B64URL = re.compile(r'^[A-Za-z0-9_-]+$')

EXIT_OK, EXIT_USAGE, EXIT_NO_CONSOLE, EXIT_VERIFY, EXIT_TEST_ROOT = 0, 2, 3, 4, 5


class UsageError(Exception):
    pass


class NoConsole(Exception):
    pass


# ----------------------------------------------------------------------------- messages

M = {
    'hub_off': ('WHALORY_HUB=0 is set: the Hub is off, and nothing was changed.',
                'متغیرِ WHALORY_HUB=0 تنظیم شده است: هاب خاموش است و چیزی تغییر نکرد.'),
    'env_blocks': ('An environment variable (WHALORY_HUB_CONTRIBUTE=0, DO_NOT_TRACK or DISABLE_TELEMETRY) '
                   'keeps contribution off. Nothing was changed.',
                   'یک متغیرِ محیطی (WHALORY_HUB_CONTRIBUTE=0، DO_NOT_TRACK یا DISABLE_TELEMETRY) مشارکت را '
                   'خاموش نگه می‌دارد. چیزی تغییر نکرد.'),
    'stats_closed': ('Statistics are not open for this edition yet.',
                     'آمار هنوز برای این نسخه باز نشده است.'),
    'packets_closed': ('Weekly packets are not open yet.', 'بسته‌های هفتگی هنوز باز نشده‌اند.'),
    'discovery_closed': ('Phrase sharing is not open yet.', 'هم‌رسانیِ عبارت‌ها هنوز باز نشده است.'),
    'needs_stats': ('Phrase sharing needs weekly statistics first: {cmd}',
                    'هم‌رسانیِ عبارت‌ها اول آمارِ هفتگی را لازم دارد: {cmd}'),
    'no_console': ('This command needs your own terminal. Nothing was changed.',
                   'این فرمان ترمینالِ خودتان را لازم دارد. چیزی تغییر نکرد.'),
    'not_final': ('The consent text is not final yet, so this cannot be turned on.',
                  'متنِ رضایت هنوز نهایی نشده است، پس این گزینه را نمی‌شود روشن کرد.'),
    'code_prompt': ('To confirm, type this code and press Enter: {code}',
                    'برای تأیید، این کد را تایپ کنید و Enter بزنید: {code}'),
    'code_wrong': ('The code did not match. Nothing was changed.', 'کد درست نبود. چیزی تغییر نکرد.'),
    'said_no': ('Nothing was changed. Whalory works exactly as before.',
                'چیزی تغییر نکرد. والوری همان‌طور کار می‌کند که پیش‌تر می‌کرد.'),
    'licence_prompt': ('Licence key for the weekly proof (optional; press Enter to skip): ',
                       'کلیدِ لایسنس برای اثباتِ هفتگی (اختیاری؛ برای رد شدن Enter بزنید): '),
    'licence_bad': ('That is not a Whalory licence key. It was not stored.',
                    'این کلیدِ لایسنسِ والوری نیست و ذخیره نشد.'),
    'stats_on': ('Weekly statistics are on. The first report goes out 3 days from now at the earliest. '
                 'Undo: {off}',
                 'آمارِ هفتگی روشن شد. نخستین گزارش زودتر از ۳ روزِ دیگر فرستاده نمی‌شود. برای برگرداندن: {off}'),
    'phrases_on': ('Phrase sharing is on.', 'هم‌رسانیِ عبارت‌ها روشن شد.'),
    'phrases_preview_on': ('Phrase sharing is on. Each week you approve the list first: {cmd}',
                           'هم‌رسانیِ عبارت‌ها روشن شد. هر هفته اول خودتان فهرست را تأیید می‌کنید: {cmd}'),
    'packets_on': ('Weekly packets are on. Nothing is sent: each week, {packet} shows you the packet. '
                   'Undo: {off}',
                   'بسته‌های هفتگی روشن شد. چیزی فرستاده نمی‌شود: هر هفته فرمانِ {packet} بسته را نشانتان '
                   'می‌دهد. برای برگرداندن: {off}'),
    'lane_switch_packets': ('Weekly packets were on; they are now off, because an installation uses one lane.',
                            'بسته‌های هفتگی روشن بود و حالا خاموش شد، چون هر نصب فقط یکی از این دو را دارد.'),
    'lane_switch_stats': ('Weekly statistics were on; they are now off, because an installation uses one lane.',
                          'آمارِ هفتگی روشن بود و حالا خاموش شد، چون هر نصب فقط یکی از این دو را دارد.'),
    'off_stats': ('Weekly statistics are off. Local counts, tickets and unsent reports were deleted.',
                  'آمارِ هفتگی خاموش شد. شمارش‌های محلی، برگه‌ها و گزارش‌های فرستاده‌نشده پاک شدند.'),
    'off_deleted': ('Asked the server to delete {n} sent report(s).',
                    'از سرور خواسته شد {n} گزارشِ فرستاده‌شده را پاک کند.'),
    'off_queued': ('{n} deletion request(s) wait for the network and go out on the next run.',
                   '{n} درخواستِ حذف منتظرِ اینترنت است و در اجرای بعدی فرستاده می‌شود.'),
    'off_phrases': ('Phrase sharing is off. Phrase rows waiting in the outbox were removed.',
                    'هم‌رسانیِ عبارت‌ها خاموش شد. ردیف‌های عبارت که در صفِ فرستادن بودند پاک شدند.'),
    'off_packets': ('Weekly packets are off. Local counts and packets were deleted. Comments you posted on '
                    'GitHub stay until you delete them there.',
                    'بسته‌های هفتگی خاموش شد. شمارش‌های محلی و بسته‌ها پاک شدند. دیدگاه‌هایی که در GitHub '
                    'گذاشته‌اید می‌مانند تا خودتان آن‌جا پاکشان کنید.'),
    'off_updates': ('Rule updates are off. Whalory uses the rules that came with this version.',
                    'به‌روزرسانیِ قاعده‌ها خاموش شد. والوری با قاعده‌های همین نسخه کار می‌کند.'),
    'forget_done': ('The Hub data on this computer was deleted, and a new install salt was made.',
                    'داده‌های هاب روی این رایانه پاک شد و یک نمکِ نصبِ تازه ساخته شد.'),
    'packets_off': ('Weekly packets are off. To turn them on, run this in your own terminal: {cmd}',
                    'بسته‌های هفتگی خاموش است. برای روشن‌کردن، این فرمان را در ترمینالِ خودتان اجرا کنید: {cmd}'),
    'packet_intro': ('This is your weekly packet for {week}: counts of Whalory\'s own checks on this computer, '
                     'never your text.',
                     'این بسته‌ی هفتگیِ شما برای {week} است: شمارش‌هایی از بررسی‌های خودِ والوری روی همین '
                     'رایانه، هرگز متنِ شما.'),
    'packet_link': ('If you want, post it as a comment on this week\'s issue: {link}',
                    'اگر خواستید، آن را به شکلِ یک دیدگاه زیرِ issueِ همین هفته بگذارید: {link}'),
    'packet_search': ('If you want, post it as a comment on the issue "Packets {week}": {link}',
                      'اگر خواستید، آن را به شکلِ یک دیدگاه زیرِ issueِ «Packets {week}» بگذارید: {link}'),
    'packet_gh': ('With GitHub CLI: {line}', 'با GitHub CLI: {line}'),
    'packet_public': ('Posting makes this packet public under your GitHub account. You can delete your comment '
                      'at any time; if you do before the week\'s final count, 21 days after the week ends, '
                      'it is left out.',
                      'با گذاشتنِ این بسته، بسته با حسابِ GitHubِ شما عمومی می‌شود. هر وقت خواستید می‌توانید '
                      'دیدگاهتان را پاک کنید؛ اگر پیش از شمارشِ نهاییِ هفته، یعنی ۲۱ روز پس از پایانِ آن، پاکش '
                      'کنید، در شمارش نمی‌آید.'),
    'packet_nothing_sent': ('Whalory sent nothing and never runs gh.',
                            'والوری چیزی نفرستاد و فرمانِ gh را هم اجرا نمی‌کند.'),
    'packet_saved': ('Saved the packet to {file}.', 'بسته در {file} ذخیره شد.'),
    'packet_none': ('No packet for {week}. A week needs at least 3 final checks or 20 lint runs, and packets '
                    'must have been on that week.',
                    'برای {week} بسته‌ای نیست. هر هفته دستِ‌کم ۳ بررسیِ نهایی یا ۲۰ بار بررسیِ متن لازم دارد و '
                    'بسته‌ها باید آن هفته روشن بوده باشند.'),
    'packet_too_big': ('The packet for {week} is longer than 60,000 characters even without empty rows, so '
                       'it cannot be posted as one comment.',
                       'بسته‌ی {week} حتی بی‌ردیف‌های خالی بیش از ۶۰٬۰۰۰ نویسه است و در یک دیدگاه جا نمی‌شود.'),
    'packet_open': ('The week is still open. Its packet is ready after Monday 00:00 UTC.',
                    'این هفته هنوز تمام نشده است. بسته‌اش پس از ساعتِ ۰۰:۰۰ دوشنبه به وقتِ UTC آماده می‌شود.'),
    'report_none': ('No report is waiting for {week}.', 'برای {week} گزارشی در صف نیست.'),
    'upload_done': ('Sent {n} report(s).', '{n} گزارش فرستاده شد.'),
    'upload_none': ('No report is due.', 'گزارشی برای فرستادن نیست.'),
    'preview_none': ('No phrase rows are waiting for approval.', 'ردیفِ عبارتی منتظرِ تأیید نیست.'),
    'preview_done': ('Updated the phrase rows.', 'ردیف‌های عبارت به‌روز شد.'),
    'sync_off': ('Rule updates are off.', 'به‌روزرسانیِ قاعده‌ها خاموش است.'),
    'sync_blocked': ('Hub network activity is off (CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC or WHALORY_HUB=0).',
                     'فعالیتِ شبکه‌ی هاب خاموش است (CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC یا WHALORY_HUB=0).'),
    'sync_test_root': ('The pinned root is the public test root, so this install does not download rule '
                       'updates.',
                       'ریشه‌ی سنجاق‌شده ریشه‌ی آزمایشیِ عمومی است، پس این نصب به‌روزرسانیِ قاعده‌ها را '
                       'دانلود نمی‌کند.'),
    'sync_not_due': ('The last sync was less than 24 hours ago. Use --force to sync now.',
                     'آخرین همگام‌سازی کمتر از ۲۴ ساعت پیش بود. برای همگام‌سازیِ فوری از --force استفاده کنید.'),
    'sync_ok': ('Rule updates checked: {state}.', 'به‌روزرسانیِ قاعده‌ها بررسی شد: {state}.'),
    'sync_fail': ('Rule update check failed ({code}). The current rules stay in use.',
                  'بررسیِ به‌روزرسانی ناموفق بود ({code}). قاعده‌های فعلی سرِ جایشان می‌مانند.'),
    'pinned': ('Local rules are pinned to {pin}. Undo: {cmd}',
               'قاعده‌های محلی روی {pin} ثابت شد. برای برگرداندن: {cmd}'),
    'unpinned': ('Local rules follow the signed updates again.',
                 'قاعده‌های محلی دوباره از به‌روزرسانی‌های امضاشده پیروی می‌کنند.'),
    'rollback_none': ('No previous overlay is left to go back to.', 'قاعده‌ی قبلی‌ای برای برگشتن نیست.'),
    'rollback_done': ('Went back to the previous overlay and pinned it. Undo: {cmd}',
                      'به قاعده‌های قبلی برگشت و روی همان ثابت شد. برای برگرداندن: {cmd}'),
    'pin_unknown': ('{pin} is not the active baseline or auto overlay.',
                    '{pin} شناسه‌ی قاعده‌های فعالِ پایه یا خودکار نیست.'),
    'turned_on_notice': ('Whalory Hub {what} were turned on at {time}. Undo: {off}',
                         '{what}ِ هابِ والوری در {time} روشن شد. برای برگرداندن: {off}'),
    'what_stats': ('statistics', 'آمارِ'),
    'what_packets': ('weekly packets', 'بسته‌های هفتگیِ'),
    'pending_prompt': ('Whalory Hub statistics were requested in your plugin settings. Show the consent screen '
                       'now? [n/y] ',
                       'آمارِ هابِ والوری در تنظیماتِ افزونه درخواست شده است. صفحه‌ی رضایت اکنون نشان داده '
                       'شود؟ [n/y] '),
    'reconsent': ('Whalory Hub needs your consent again before it sends statistics: {cmd}',
                  'هابِ والوری پیش از فرستادنِ آمار دوباره رضایتِ شما را لازم دارد: {cmd}'),
}


def lang_of(value=None):
    """--lang, else WHALORY_LANG, else the OS locale: Persian for fa*, English otherwise (spec 4.4)."""
    for v in (value, HE.env('LANG')):
        if v:
            return 'fa' if v.lower().startswith('fa') else 'en'
    loc = ''
    try:
        loc = locale.getlocale()[0] or ''
    except (ValueError, TypeError):
        loc = ''
    for name in ('LC_ALL', 'LC_MESSAGES', 'LANG'):
        loc = loc or os.environ.get(name, '')
    return 'fa' if loc.lower().startswith(('fa', 'persian', 'farsi')) else 'en'


def t(key, lang, **kw):
    s = M[key][1 if lang == 'fa' else 0]
    return s.format(**kw) if kw else s


# ----------------------------------------------------------------------------- the run context


class Ctx(object):
    """One command run: options, the Hub folder, output streams, a network budget."""

    def __init__(self, args=None):
        self.test = False
        self.mirrors = []
        self.collector = None
        self.issuer = None
        self.lang = lang_of(None)
        self.quiet = False
        self.host = None
        self.now = None
        self.out = sys.stdout
        self.err = sys.stderr
        self.net_deadline = None
        self.net_bytes = 0
        self.net_cap = None
        self.http = None                # injected by tests: fn(method, url, body, headers, cap) -> (status, bytes)
        self.console = None             # injected by tests: an object with write() and readline()
        self.key_hash = None            # tests only: the licence key_hash (test mode reads no key)

    def utcnow(self):
        return self.now or HE.utcnow()

    def home(self):
        return HE.hub_home()

    def say(self, text=''):
        if not self.quiet and self.out is not None:
            _write(self.out, text + '\n')


def _write(stream, text):
    try:
        stream.write(text)
    except UnicodeEncodeError:
        enc = getattr(stream, 'encoding', None) or 'ascii'
        stream.write(text.encode(enc, 'replace').decode(enc, 'replace'))
    try:
        stream.flush()
    except Exception:
        pass


def script_cmd(*args):
    """The exact command for this install, e.g. "python3" "/path/hub_client.py" off (spec 4.4 {OFF})."""
    exe = sys.executable or ''
    exe = ('"%s"' % exe) if exe and os.path.exists(exe) else ('python3' if os.name != 'nt' else 'python')
    path = os.path.abspath(__file__)
    return ' '.join([exe, '"%s"' % path] + list(args))


# ----------------------------------------------------------------------------- files


def p(*parts):
    home = HE.hub_home()
    return os.path.join(home, *parts) if home else None


def rm(path):
    HE.invalidate()
    try:
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def read_bytes(path, cap=None):
    try:
        with open(path, 'rb') as fh:
            data = fh.read(-1 if cap is None else cap + 1)
    except (OSError, TypeError):
        return None
    if cap is not None and len(data) > cap:
        return None
    return data


def read_json(path, cap=1024 * 1024):
    return HE.read_json(path, cap)


def write_json(path, doc, private=False):
    HE.write_atomic(path, HE.dump_json(doc), private=private)


def state():
    path = p('state.json')
    doc = read_json(path) if path else None
    if doc is None and path and os.path.exists(path):
        HE.move_corrupt(path)
    return doc if isinstance(doc, dict) else {}


def save_state(doc):
    path = p('state.json')
    if path:
        write_json(path, doc)


def ensure_settings():
    """settings.json with an install salt (the first run of any Hub command writes it)."""
    s = dict(HE.settings())
    if HE.install_salt(s) is None:
        s['install_salt'] = os.urandom(32).hex()
        HE.save_settings(s)
        s = dict(HE.settings())
    return s


def hub_log(ctx, url, nbytes, status, receipt=None):
    """One line per network action (spec 4.5): time, host and path, bytes, status, receipt."""
    path = p('hub.log')
    if not path:
        return
    m = re.match(r'^https?://([^/?#]+)([^?#]*)', url)
    where = (m.group(1) + m.group(2)) if m else '?'
    line = '%s %s %d %s%s' % (HE.fmt_time(ctx.utcnow()), where, nbytes, status, (' ' + receipt) if receipt else '')
    try:
        HE.makedirs(os.path.dirname(path))
        lines = []
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                lines = fh.read().splitlines()
        lines.append(line)
        HE.write_atomic(path, ('\n'.join(lines[-LOG_LINES:]) + '\n').encode('utf-8'))
    except OSError:
        pass


def folder_size(home):
    total = 0
    for root, _dirs, files in os.walk(home):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def _epoch_files(folder, suffix='.json'):
    out = []
    try:
        for name in os.listdir(folder):
            if name.endswith(suffix) and _EPOCH.match(name[:-len(suffix)]):
                out.append(name[:-len(suffix)])
    except OSError:
        pass
    return sorted(out)


def prune(ctx):
    """Retention of spec 4.5 and 4.8, and the 5 MiB folder budget of spec 5.12."""
    home = ctx.home()
    if not home or not os.path.isdir(home):
        return
    now = ctx.utcnow()
    HE.prune_events(now)
    for sub, keep in (('packets', KEEP_WEEKS), ('sent', KEEP_WEEKS), ('outbox', DEADLINE), ('tokens', DEADLINE)):
        for e in _epoch_files(os.path.join(home, sub)):
            if HM.week_end(e) + keep < now:
                rm(os.path.join(home, sub, e + '.json'))
    if folder_size(home) > FOLDER_CAP:
        for e in _epoch_files(os.path.join(home, 'sent')):
            rm(os.path.join(home, 'sent', e + '.json'))
            if folder_size(home) <= FOLDER_CAP:
                return
        keep = set()
        rec = read_json(os.path.join(home, 'active.json'), 16 * 1024) or {}
        for part in [rec] + list(rec.get('previous') or []):
            for kind in ('baseline', 'auto'):
                ref = part.get(kind) if isinstance(part, dict) else None
                if isinstance(ref, dict) and ref.get('sha256'):
                    keep.add(ref['sha256'])
        folder = os.path.join(home, 'targets')
        for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            if name[:-5] not in keep:
                rm(os.path.join(folder, name))


# ----------------------------------------------------------------------------- the console (spec 4.3)


class Console(object):
    """Reads the console device, never stdin; writes prompts to the console as well."""

    def __init__(self, reader, writer):
        self._r = reader
        self._w = writer

    def write(self, text):
        _write(self._w, text)

    def readline(self):
        line = self._r.readline()
        if not line:
            raise NoConsole()
        return line.rstrip('\r\n')

    def close(self):
        for f in (self._r, self._w):
            try:
                f.close()
            except Exception:
                pass


def _tty(stream):
    try:
        return stream is not None and stream.isatty()
    except Exception:
        return False


def open_console():
    """The console device, or raise NoConsole (a model's shell tool has none, spec 4.3)."""
    if not (_tty(sys.stdin) and (_tty(sys.stdout) or _tty(sys.stderr))):
        raise NoConsole()
    try:
        if os.name == 'nt':
            r = io.open('CONIN$', 'r', encoding='utf-8', errors='replace')
            w = io.open('CONOUT$', 'w', encoding='utf-8', errors='replace')
        else:
            r = io.open('/dev/tty', 'r', encoding='utf-8', errors='replace')
            w = io.open('/dev/tty', 'w', encoding='utf-8', errors='replace')
    except (OSError, IOError, ValueError):
        raise NoConsole()
    return Console(r, w)


def get_console(ctx):
    if ctx.console is not None:
        return ctx.console
    return open_console()


#: Answers: the Latin letter, the word, or the key of the same letter on the Persian layout.
YES = ('y', 'yes', 'بله', 'آره', 'غ')
NO = ('n', 'no', 'نه', 'د')
PREVIEW = ('p', 'ح')
_DIGITS = dict([(ord(c), str(i)) for i, c in enumerate('۰۱۲۳۴۵۶۷۸۹')]
               + [(ord(c), str(i)) for i, c in enumerate('٠١٢٣٤٥٦٧٨٩')])


def answer(con, choices=YES + NO):
    """'y', 'n' or 'p' from one console line; anything else (and Enter) is the default No."""
    ans = con.readline().strip().lower()
    if ans in YES and ans in choices:
        return 'y'
    if ans in PREVIEW and ans in choices:
        return 'p'
    return 'n'


def typed_code(con, lang):
    """A 4-digit code shown on the console must be typed back (spec 4.3); Persian digits count."""
    code = ''.join(CODE_ALPHABET[b % len(CODE_ALPHABET)] for b in os.urandom(4))
    con.write(t('code_prompt', lang, code=code) + '\n> ')
    got = con.readline().translate(_DIGITS).strip().upper().replace(' ', '')
    return got == code


# ----------------------------------------------------------------------------- consent texts (spec 4.4)


def consent_doc():
    doc = read_json(os.path.join(HE.DATA_DIR, 'consent.json'), 256 * 1024)
    return doc if isinstance(doc, dict) and doc.get('schema') == 'whalory.consent-texts/1' else None


def render(kind, lang, doc, extra=None):
    """The exact wording of one screen with its placeholders filled; None if one stays unfilled."""
    texts = (doc.get('texts') or {}).get(kind) or {}
    lines = texts.get(lang) or texts.get('en')
    if not lines:
        return None
    text = '\n'.join(lines)
    values = {
        '{CONTROLLER}': doc.get('controller') or '',
        '{HOST_LOG_PERIOD}': (doc.get('host_log_period') or {}).get(lang, ''),
        '{EU_LINE}': '' if doc.get('art28_contract') else (doc.get('eu_line') or {}).get(lang, ''),
        '{NOTICE}': (doc.get('notice') or {}).get(lang, ''),
        '{OFF}': script_cmd('off'),
        '{OFF_PACKETS}': script_cmd('off', 'packets'),
        '{UPDATES_OFF}': script_cmd('off', 'updates'),
    }
    values.update(extra or {})
    for k, v in values.items():
        text = text.replace(k, v)
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    if _PLACEHOLDER.search(text):
        return None
    return text


def full_screen(kind, lang, doc):
    """A consent screen with the update notice as its footer (spec 4.4.6)."""
    extra = {}
    if kind == 'stats':
        lic = render('licence', lang, doc)
        if lic is None:
            return None
        extra['{LICENCE_PARAGRAPH}'] = lic
    body = render(kind, lang, doc, extra)
    foot = render('updates_notice', lang, doc)
    if body is None or foot is None:
        return None
    return body + '\n\n' + foot


def consent_record(tier_list, lang, text, pol):
    rec = {'tiers': tier_list, 'version': HE.CONSENT_VERSION,
           'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'lang': lang,
           'at': HE.fmt_time(HE.utcnow()), 'source': 'console', 'age_confirmed': True,
           'skill_major': HE.skill_major()}
    if tier_list != ['packets']:
        r = pol.get('recipients') or {}
        rec['collectors'] = list(r.get('collectors') or [])
        rec['token_issuer'] = r.get('token_issuer')
        rec['collection_country'] = r.get('collection_country')
    return rec


# ----------------------------------------------------------------------------- turning things off (spec 4.9)


def _clear_dir(path, keep=()):
    if not path or not os.path.isdir(path):
        return
    for name in os.listdir(path):
        if name not in keep:
            rm(os.path.join(path, name))


def off_stats(ctx, send=True):
    """stats and phrases OFF, local data deleted, deletion requests for sent reports (spec 4.9)."""
    s = ensure_settings()
    s.update(stats='off', phrases=False, phrases_preview=False, pending=None)
    s['consent'] = dict(s.get('consent') or {}, stats=None)
    s['turned_on'] = dict(s.get('turned_on') or {}, stats=None)
    HE.save_settings(s)
    home = ctx.home()
    lane = HE.settings().get('packets') is True
    if not lane:
        _clear_dir(os.path.join(home, 'events'))
    _clear_dir(os.path.join(home, 'tokens'))
    _clear_dir(os.path.join(home, 'outbox'), keep=('deletions.json',))
    rm(os.path.join(home, 'secret.json'))
    queue = _deletion_queue(ctx)
    for e in _epoch_files(os.path.join(home, 'sent')):
        doc = read_json(os.path.join(home, 'sent', e + '.json')) or {}
        if doc.get('receipt') and doc.get('secret') and HM.week_end(e) + SERVER_RETENTION >= ctx.utcnow():
            queue.append({'epoch': e, 'receipt': doc['receipt'], 'secret': doc['secret']})
    _clear_dir(os.path.join(home, 'sent'))
    _save_deletions(ctx, queue)
    sent = send_deletions(ctx) if (send and queue) else 0
    return sent, len(_deletion_queue(ctx))


def off_packets(ctx):
    s = ensure_settings()
    s['packets'] = False
    s['consent'] = dict(s.get('consent') or {}, packets=None)
    s['turned_on'] = dict(s.get('turned_on') or {}, packets=None)
    HE.save_settings(s)
    home = ctx.home()
    if HE.settings().get('stats') != 'on':
        _clear_dir(os.path.join(home, 'events'))
    _clear_dir(os.path.join(home, 'packets'))


def off_phrases(ctx):
    s = ensure_settings()
    s.update(phrases=False, phrases_preview=False)
    rec = (s.get('consent') or {}).get('stats')
    if isinstance(rec, dict) and rec.get('tiers') == ['stats', 'phrases']:
        rec = dict(rec, tiers=['stats'])
        s['consent'] = dict(s.get('consent') or {}, stats=rec)
    HE.save_settings(s)
    folder = p('outbox')
    for e in _epoch_files(folder):
        path = os.path.join(folder, e + '.json')
        doc = read_json(path)
        if isinstance(doc, dict) and isinstance(doc.get('report'), dict):
            rep = doc['report']
            rep.pop('phrases', None)
            rep.pop('base', None)
            rep['consent'] = dict(rep.get('consent') or {}, tiers=['stats'])
            doc['phrases_pending'] = False
            write_json(path, doc, private=True)


def _deletion_queue(ctx):
    doc = read_json(p('outbox', 'deletions.json')) or {}
    q = doc.get('queue') if isinstance(doc.get('queue'), list) else []
    return [x for x in q if isinstance(x, dict) and x.get('receipt') and x.get('secret')]


def _save_deletions(ctx, queue):
    path = p('outbox', 'deletions.json')
    if not queue:
        rm(path)
        return
    write_json(path, {'queue': queue}, private=True)


# ----------------------------------------------------------------------------- the network (spec 5.6)


class NetError(Exception):
    pass


def _url_ok(ctx, url):
    if url.startswith('https://'):
        return True
    return ctx.test and re.match(r'^http://(127\.0\.0\.1|localhost|\[::1\])(:[0-9]+)?/', url) is not None


def _opener(ctx):
    import urllib.request

    class Redirects(urllib.request.HTTPRedirectHandler):
        max_redirections = MAX_REDIRECTS

        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if req.full_url.startswith('https://') and not newurl.startswith('https://'):
                raise NetError('redirect from https to http refused')
            if not _url_ok(ctx, newurl):
                raise NetError('redirect refused')
            return urllib.request.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)

    return urllib.request.build_opener(urllib.request.ProxyHandler(), Redirects())


def http(ctx, method, url, body=None, headers=None, cap=SHOP_CAP):
    """(status, bytes) for one request; raises NetError for a refused URL, the budget or a failure."""
    if not _url_ok(ctx, url):
        raise NetError('refused URL')
    if HE.network_blocked():
        raise NetError('network off')
    if ctx.net_deadline is not None and time.monotonic() > ctx.net_deadline:
        raise NetError('time budget')
    if ctx.net_cap is not None:
        cap = min(cap, max(0, ctx.net_cap - ctx.net_bytes))
    hdrs = {'User-Agent': USER_AGENT, 'Connection': 'close'}
    if body is not None:
        hdrs['Content-Type'] = 'application/json'
    hdrs.update(headers or {})
    if ctx.http is not None:
        status, data = ctx.http(method, url, body, hdrs, cap)
    else:
        status, data = _urllib(ctx, method, url, body, hdrs, cap)
    ctx.net_bytes += len(data or b'')
    return status, data


def _urllib(ctx, method, url, body, hdrs, cap):
    import urllib.error
    import urllib.request
    timeout = TIMEOUT
    if ctx.net_deadline is not None:
        timeout = max(0.5, min(TIMEOUT, ctx.net_deadline - time.monotonic()))
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        resp = _opener(ctx).open(req, timeout=timeout)
        status = resp.getcode()
    except urllib.error.HTTPError as e:
        resp, status = e, e.code
    except NetError:
        raise
    except Exception as e:
        raise NetError('%s: %s' % (type(e).__name__, str(e)[:100]))
    try:
        data = resp.read(cap + 1) if status not in (204, 304) else b''
    except Exception as e:
        raise NetError('read: %s' % type(e).__name__)
    finally:
        try:
            resp.close()
        except Exception:
            pass
    if len(data) > cap:
        raise NetError('response over %d bytes' % cap)
    return status, data


def _json_body(data, cap=SHOP_CAP):
    try:
        import hub_verify as HV
        doc = HV.loads(data, max_bytes=cap)
    except Exception:
        return None
    return doc if isinstance(doc, dict) else None


# ----------------------------------------------------------------------------- sync (spec 5.8)


def _hv():
    import hub_verify
    return hub_verify


def _ho():
    import hub_overlay
    return hub_overlay


def pinned_root():
    return HE.pinned_root_bytes()


def trusted_roots():
    """The verified root chain of the Hub folder (pinned root first), or []."""
    try:
        hv = _hv()
        return hv.load_roots(pinned_root(), hv.reader(HE.hub_home(), 'hub'))
    except Exception:
        return []


def mirror_list(ctx, st):
    if ctx.mirrors:
        return list(ctx.mirrors)
    roots = trusted_roots()
    listed = list(roots[-1].get('mirrors') or []) if roots else []
    last = (st.get('mirrors') or {}).get('last')
    if last in listed:
        listed.remove(last)
        listed.insert(0, last)
    return listed


def _mirror_rel(base, rel):
    """Releases assets are flattened: '/' becomes '__' in asset names (spec 8.2)."""
    if '/releases/' in base:
        return rel.replace('/', '__')
    return rel


class Fetcher(object):
    """fetch(rel, max_bytes) for hub_verify.sync: one mirror per run, the first that answers."""

    def __init__(self, ctx, mirrors, home):
        self.ctx = ctx
        self.mirrors = list(mirrors)
        self.home = home
        self.chosen = None
        self.failed = []
        self.served = {}

    def _local(self, rel):
        if rel in ('timestamp.json', 'halt.json'):
            return read_bytes(os.path.join(self.home, 'trusted', rel), 64 * 1024)
        return None

    def __call__(self, rel, max_bytes):
        order = [self.chosen] if self.chosen else [m for m in self.mirrors if m not in self.failed]
        last_error = None
        for base in order:
            url = base + _mirror_rel(base, rel)
            headers = {}
            local = self._local(rel)
            if local is not None:
                headers['If-None-Match'] = '"%s"' % hashlib.sha256(local).hexdigest()
            try:
                status, data = http(self.ctx, 'GET', url, None, headers, max_bytes)
            except NetError as e:
                hub_log(self.ctx, url, 0, 'error')
                last_error = e
                if self.chosen:
                    raise
                self.failed.append(base)
                continue
            hub_log(self.ctx, url, len(data or b''), status)
            if status == 304 and local is not None:
                self.chosen = base
                self.served[rel] = local
                return local
            if status == 404:
                self.chosen = base
                return None
            if status == 200:
                self.chosen = base
                self.served[rel] = data
                return data
            last_error = NetError('HTTP %s' % status)
            if self.chosen:
                raise last_error
            self.failed.append(base)
        raise last_error or NetError('no mirror')


def sync_due(st, now):
    last = st.get('last_sync')
    try:
        return last is None or now - HE.parse_time(last) >= SYNC_EVERY
    except (TypeError, ValueError):
        return True


def sync_blocker(ctx):
    """Why this run may not sync, or None."""
    if HE.network_blocked():
        return 'sync_blocked'
    if not HE.settings().get('updates', True) or HE.updates_blocked():
        return 'sync_off'
    if HE.pinned_root_is_test() and not ctx.test:
        return 'sync_test_root'
    return None


def run_sync(ctx, force=False):
    """Spec 5.8 once; returns (ok, code, summary). Writes only verified files."""
    hv, ho = _hv(), _ho()
    s = ensure_settings()
    st = state()
    now = ctx.utcnow()
    if not force and not sync_due(st, now):
        return True, 'not_due', None
    home = ctx.home()
    fetcher = Fetcher(ctx, mirror_list(ctx, st), home)
    active_raw = read_bytes(os.path.join(home, 'active.json'), 16 * 1024)
    active = None
    if active_raw:
        try:
            active = ho.parse_active(active_raw)
        except Exception:
            HE.move_corrupt(os.path.join(home, 'active.json'))
            active = None
    res = hv.sync(pinned_root(), hv.reader(home, 'hub'), st.get('rules'), fetcher, now=now,
                  skill_version=HE.skill_version(), install_salt=HE.install_salt(s) or b'', active=active)
    st = state()
    st['last_sync'] = HE.fmt_time(now)
    mirrors = dict(st.get('mirrors') or {})
    if fetcher.chosen:
        mirrors['last'] = fetcher.chosen
    st['mirrors'] = mirrors
    for kind, reason in res.health:
        HE.record_health(kind, reason)
    if not res.ok:
        st['last_sync_result'] = res.code
        save_state(st)
        return False, res.code, None
    for rel in res.remove:                      # dropped first: a rotated role's new files follow
        if rel not in res.files:
            rm(os.path.join(home, *rel.split('/')))
    for rel, data in sorted(res.files.items()):
        HE.write_atomic(os.path.join(home, *rel.split('/')), data)
    st['rules'] = res.rules
    st['last_sync_result'] = 'ok'
    st['stale'] = bool(res.stale)
    save_state(st)
    if res.recipients_changed:
        recipients_changed(ctx)
    _split_view(ctx, fetcher, res)
    summary = 'no change'
    pin = s.get('pin') if isinstance(s.get('pin'), dict) else {}
    if pin.get('mode') == 'freeze' and res.halt is None:
        return True, 'ok', 'pinned to %s' % pin.get('id')
    if active is not None and pin.get('mode') in ('baseline', 'bundled') and active.get('pin') != pin['mode']:
        active = dict(active, pin=pin['mode'])
    auto_doc = None
    if active and active.get('auto'):
        raw = read_bytes(os.path.join(home, 'targets', active['auto']['sha256'] + '.json'), 256 * 1024)
        if raw is not None:
            try:
                auto_doc = hv.check_target(raw, {'sha256': active['auto']['sha256'], 'length': len(raw)})
            except Exception:
                auto_doc = None
    dec = ho.decide(res, active, now=now, active_auto_doc=auto_doc)
    for kind, reason in dec.health:
        oid = (dec.active or {}).get('auto', {}) or {}
        HE.record_health(kind, reason, oid.get('id') if isinstance(oid, dict) else None)
    if dec.rules is not None:
        st = state()
        st['rules'] = dec.rules
        save_state(st)
    if dec.activate and dec.active_bytes:
        if pin.get('mode') in ('baseline', 'bundled') and dec.active.get('pin') != pin['mode'] and res.halt is None:
            dec.active = dict(dec.active, pin=pin['mode'])
            dec.active_bytes = _active_bytes(dec.active)
        HE.write_atomic(os.path.join(home, 'active.json'), dec.active_bytes)
        keep = set(dec.keep_targets)
        folder = os.path.join(home, 'targets')
        for name in os.listdir(folder) if os.path.isdir(folder) else []:
            if name.endswith('.json') and name[:-5] not in keep and name[:-5] not in _registry_targets(res):
                rm(os.path.join(folder, name))
        rec = dec.active
        summary = 'active %s%s' % (rec['baseline']['id'], (' + ' + rec['auto']['id']) if rec.get('auto') else '')
    elif dec.result in ('reject', 'defer'):
        summary = '%s (%s)' % (dec.result, dec.code)
    return True, 'ok', summary


def _registry_targets(res):
    out = set()
    try:
        for entry in res.snapshot.auto['targets'].values():
            if entry.get('role') == 'registry':
                out.add(entry['sha256'])
    except Exception:
        pass
    return out


def _split_view(ctx, fetcher, res):
    """Compare the timestamp of a second reachable mirror (spec 5.8): verify_fail mismatch."""
    served = fetcher.served.get('timestamp.json')
    if served is None or ctx.mirrors and len(ctx.mirrors) < 2:
        return
    others = [m for m in fetcher.mirrors if m != fetcher.chosen and m not in fetcher.failed]
    if not others:
        return
    base = others[0]
    try:
        status, data = http(ctx, 'GET', base + _mirror_rel(base, 'timestamp.json'), None, None, 16 * 1024)
    except NetError:
        return
    hub_log(ctx, base + 'timestamp.json', len(data or b''), status)
    if status == 200 and data and _hv().timestamps_disagree(served, data):
        HE.record_health('verify_fail', 'mismatch')


def recipients_changed(ctx):
    """A new root named other collectors, issuer or country: stop, delete tokens and outbox (spec 4.10)."""
    home = ctx.home()
    _clear_dir(os.path.join(home, 'tokens'))
    _clear_dir(os.path.join(home, 'outbox'), keep=('deletions.json',))


# ----------------------------------------------------------------------------- weekly build (spec 5.5, 17.3.1)


def known_ids():
    """Ids this client may emit (spec 5.5 cells[].id): built-in rules and lx- ids, the active
    overlay's ht- ids, the playbook anchors of the task index and the baseline's parameters."""
    out = {'fa': set(), 'en': set()}
    hv = _hv()
    try:
        import lint_fa
        import lint_en
    except Exception:
        return None
    for lang, mod in (('fa', lint_fa), ('en', lint_en)):
        for row in mod.rule_list():
            out[lang].add(row['id'])
        for category, phrases in (getattr(mod, 'LEXICON', None) or {}).items():
            for phrase in phrases:
                out[lang].add(hv.lx_id(lang, category, phrase))
        try:
            for _phrase, ident, _state in _ho().hub_phrases(lang):
                out[lang].add(ident)
        except Exception:
            pass
    out['playbooks'] = playbook_ids()
    out['params'] = set((HE.policy().get('params') or {}).keys())
    return out


def playbook_ids():
    path = os.path.join(HE.SKILL_DIR, 'references', 'playbooks.md')
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            text = fh.read()
        start = text.index('## Task index')
        end = text.find('\n## ', start + 5)
        block = text[start:end if end > 0 else len(text)]
        return set(re.findall(r'\]\(playbooks-[a-z]+\.md#([a-z0-9-]+)\)', block))
    except (OSError, ValueError, UnicodeDecodeError):
        return set()


def client_block():
    ids = HE._active_ids()
    return {'skill': HE.skill_minor(), 'py': HM.py_bucket(), 'overlay': {'baseline': ids['b'], 'auto': ids['a']}}


def build_due(ctx):
    """Turn the event files of closed weeks into packets or reports (first run after Monday)."""
    home = ctx.home()
    folder = os.path.join(home, 'events')
    if not os.path.isdir(folder):
        return []
    now = ctx.utcnow()
    current = HE.current_epoch(now)
    lane, _why = HE.lane_state()
    s = HE.settings()
    built = []
    ids = None
    for name in sorted(os.listdir(folder)):
        m = re.match(r'^([0-9]{4}-W[0-9]{2})\.jsonl$', name)
        if not m or m.group(1) >= current:
            continue
        e = m.group(1)
        path = os.path.join(folder, name)
        events = HM.read_events(path)
        if ids is None:
            ids = known_ids()
        if lane == 'packets':
            rec = (s.get('consent') or {}).get('packets') or {}
            pk = HM.build_packet(e, events, {'version': rec.get('version', HE.CONSENT_VERSION)}, client_block(), ids)
            if pk is not None:
                write_json(os.path.join(home, 'packets', e + '.json'), pk)
                built.append(('packet', e))
        elif lane == 'stats' and HM.week_end(e) + DEADLINE > now:
            rec = (s.get('consent') or {}).get('stats') or {}
            secret = os.urandom(32)
            phrases = s.get('phrases') is True and HE.policy().get('discovery_open')
            rep = HM.build_report(e, events, {'version': rec.get('version', HE.CONSENT_VERSION)}, client_block(),
                                  secret, phrases=bool(phrases), known_ids=ids)
            if rep is not None:
                doc = {'report': rep, 'secret': _b64url(secret), 'built': HE.fmt_time(now),
                       'phrases_pending': bool(phrases and s.get('phrases_preview') and rep.get('phrases')),
                       'attempts': 0, 'next_try': None}
                write_json(os.path.join(home, 'outbox', e + '.json'), doc, private=True)
                built.append(('report', e))
        else:
            continue            # no lane consumes it: the 14-day rule deletes it (spec 4.5)
        rm(path)
    return built


def _b64url(data):
    return base64.urlsafe_b64encode(bytes(data)).decode('ascii').rstrip('=')


# ----------------------------------------------------------------------------- packets (spec 17.3)


def last_closed_week(now):
    return HE.current_epoch(now - datetime.timedelta(days=7))


def packet_link(pol, week):
    """(url, issue number or None) of the week's issue, from the signed baseline and timestamp."""
    repo = pol.get('lane_repo')
    if not isinstance(repo, str) or not re.match(r'^[A-Za-z0-9-]{1,39}/[A-Za-z0-9._-]{1,100}$', repo):
        return None, None
    pk = pol.get('packets') or {}
    if pk.get('epoch') == week and isinstance(pk.get('issue'), int) and pk['issue'] > 0:
        return 'https://github.com/%s/issues/%d' % (repo, pk['issue']), pk['issue']
    q = 'is%%3Aissue+label%%3Apackets+%%22Packets+%s%%22' % week
    return 'https://github.com/%s/issues?q=%s' % (repo, q), None


def cmd_packet(ctx, a):
    lang_mode = a.lang or ctx.lang
    langs = ['en', 'fa'] if lang_mode == 'both' else [lang_mode if lang_mode in ('fa', 'en') else ctx.lang]
    s = ensure_settings()
    pol = HE.policy()
    if s.get('packets') is not True:
        for lg in langs:
            if not pol['lane_open']:
                ctx.say(t('packets_closed', lg))
            ctx.say(t('packets_off', lg, cmd=script_cmd('on', 'packets')))
        return EXIT_OK
    build_due(ctx)
    now = ctx.utcnow()
    week = a.week or last_closed_week(now)
    if not _EPOCH.match(week):
        raise UsageError('--week must look like 2026-W40')
    if week >= HE.current_epoch(now):
        for lg in langs:
            ctx.say(t('packet_open', lg))
        return EXIT_OK
    doc = read_json(p('packets', week + '.json'), 256 * 1024)
    if not isinstance(doc, dict) or doc.get('schema') != 'whalory.packet/1':
        for lg in langs:
            ctx.say(t('packet_none', lg, week=week))
        return EXIT_OK
    text, fitted = HM.fit_packet(doc)
    if text is None:
        for lg in langs:
            ctx.say(t('packet_too_big', lg, week=week))
        return EXIT_OK
    if a.json:
        ctx.say(json.dumps({'week': week, 'packet': fitted, 'comment': text,
                            'link': packet_link(pol, week)[0]}, ensure_ascii=False, indent=1))
        return EXIT_OK
    link, issue = packet_link(pol, week)
    save = a.save
    if save:
        with open(save, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
    for lg in langs:
        ctx.say(t('packet_intro', lg, week=week))
    ctx.say()
    ctx.say(text.rstrip('\n'))
    ctx.say()
    for lg in langs:
        if link and issue:
            ctx.say(t('packet_link', lg, link=link))
        elif link:
            ctx.say(t('packet_search', lg, week=week, link=link))
        if link and issue:
            repo = pol.get('lane_repo')
            line = 'gh issue comment %d --repo %s --body-file %s' % (issue, repo, _q(save or 'packet-%s.md' % week))
            ctx.say(t('packet_gh', lg, line=line))
        ctx.say(t('packet_public', lg))
        ctx.say(t('packet_nothing_sent', lg))
        if save:
            ctx.say(t('packet_saved', lg, file=save))
    return EXIT_OK


def _q(path):
    return '"%s"' % path if (' ' in path or '\t' in path) else path


# ----------------------------------------------------------------------------- reports (spec 5.5 to 5.7)


def stats_ready(ctx):
    """None when the stats lane may send, else a message key."""
    pol = HE.policy()
    if not pol['collection_open']:
        return 'stats_closed'
    lane, why = HE.lane_state()
    if lane != 'stats':
        return 'stats_closed' if why == 'closed' else 'upload_none'
    return None


def cmd_report(ctx, a):
    pol = HE.policy()
    if not pol['collection_open']:
        ctx.say(t('stats_closed', ctx.lang))
        return EXIT_OK
    build_due(ctx)
    week = a.week or last_closed_week(ctx.utcnow())
    doc = read_json(p('outbox', week + '.json'), 256 * 1024)
    if not isinstance(doc, dict) or not isinstance(doc.get('report'), dict):
        sent = read_json(p('sent', week + '.json'), 256 * 1024)
        if isinstance(sent, dict) and sent.get('body'):
            ctx.say(sent['body'])
            return EXIT_OK
        ctx.say(t('report_none', ctx.lang, week=week))
        return EXIT_OK
    ctx.say(json.dumps(doc['report'], ensure_ascii=False, indent=None if a.json else 1))
    return EXIT_OK


def licence_key_hash(ctx):
    """key_hash of the licence key, or None. In test mode it never reads secret.json or the
    licence variables (spec 5.10); a test hands a key_hash to the Ctx object instead."""
    if ctx.test:
        return ctx.key_hash
    import hub_token as HT
    raw = HE.env('LICENSE_KEY') or os.environ.get('CLAUDE_PLUGIN_OPTION_LICENSE_KEY') or ''
    if not raw:
        doc = read_json(p('secret.json'), 4096) or {}
        raw = doc.get('licence_key') or ''
    key = HT.normalize_licence_key(raw) if raw else None
    return HT.licence_key_hash(key) if key else None


def _recipients_ok(ctx):
    rec = (HE.settings().get('consent') or {}).get('stats')
    pol = HE.policy()
    return HE.consent_problem(rec, 'stats', pol) is None


def _issuer(ctx):
    if ctx.issuer:
        return ctx.issuer
    roots = trusted_roots()
    return roots[-1].get('token_issuer') if roots else None


def _collector(ctx):
    if ctx.collector:
        return ctx.collector
    roots = trusted_roots()
    listed = roots[-1].get('collectors') if roots else None
    return listed[0] if listed else None


def _schedule(st, e, now):
    """Random token and upload times for week e, drawn once from os.urandom (spec 5.6)."""
    sched = st.setdefault('schedule', {})
    ent = sched.get(e)
    if isinstance(ent, dict) and ent.get('token_at') and ent.get('upload_at'):
        return ent
    start, end = HM.week_start(e), HM.week_end(e)
    lo = max(now, start)
    hi = end - TOKEN_GAP
    span = max(0, int((hi - lo).total_seconds()))
    token_at = lo + datetime.timedelta(seconds=(int.from_bytes(os.urandom(4), 'big') % span) if span else 0)
    upload_at = end + datetime.timedelta(seconds=int.from_bytes(os.urandom(4), 'big') % int(UPLOAD_WINDOW.total_seconds()))
    ent = {'token_at': HE.fmt_time(token_at), 'upload_at': HE.fmt_time(upload_at)}
    sched[e] = ent
    for old in list(sched):
        if old < HE.current_epoch(now - DEADLINE - datetime.timedelta(days=7)):
            sched.pop(old, None)
    return ent


def token_due(ctx, st, now):
    """The epoch whose token should be requested now, or None."""
    if HE.lane() != 'stats':
        return None
    cur = HE.current_epoch(now)
    candidates = [cur] + [e for e in _epoch_files(p('outbox')) if e < cur and HM.week_end(e) + DEADLINE > now]
    for e in candidates:
        if os.path.exists(p('tokens', e + '.json')) or (st.get('token_refused') or {}).get(e):
            continue
        ent = _schedule(st, e, now)
        if now >= HE.parse_time(ent['token_at']) and (e != cur or now <= HM.week_end(e) - TOKEN_GAP):
            return e
    return None


def request_token(ctx, e):
    """Spec 5.7 steps 1 to 4 for epoch e; True when a token was stored."""
    import hub_token as HT
    if not _recipients_ok(ctx):
        recipients_changed(ctx)
        return False
    key_hash = licence_key_hash(ctx)
    base = _issuer(ctx)
    snap = HE.snapshot()
    if not key_hash or not base or snap is None or snap.timestamp is None:
        return False
    token_keys = snap.timestamp.get('token_keys') or {}
    status, data = http(ctx, 'GET', base + 'token-keys', None, None, SHOP_CAP)
    hub_log(ctx, base + 'token-keys', len(data or b''), status)
    if status != 200:
        return False
    keys = HT.trusted_keys(data, token_keys, e)
    st = state()
    tenure = st.get('token_tenure') if st.get('token_tenure') in ('new', 'est') else 'est'
    key = keys.get(tenure) or keys.get('new' if tenure == 'est' else 'est')
    if key is None:
        return False
    status, data = http(ctx, 'POST', base + 'nonce', b'{}', None, SHOP_CAP)
    hub_log(ctx, base + 'nonce', len(data or b''), status)
    doc = _json_body(data) if status == 200 else None
    if not doc or not isinstance(doc.get('nonce'), str):
        return False
    body, pending = HT.begin(e, key, key_hash, doc['nonce'])
    raw = json.dumps(body, separators=(',', ':')).encode('utf-8')
    status, data = http(ctx, 'POST', base + 'token', raw, None, SHOP_CAP)
    hub_log(ctx, base + 'token', len(data or b''), status)
    st = state()
    if status == 403:
        st.setdefault('token_refused', {})[e] = HE.fmt_time(ctx.utcnow())
        save_state(st)
        return False
    if status != 200:
        return False
    try:
        tok = HT.finish(pending, data)
    except HT.TokenError as err:
        if err.code == 'tenure' and err.tenure in ('new', 'est'):
            st['token_tenure'] = err.tenure
            save_state(st)
        elif err.code == 'signature':
            HE.record_health('verify_fail', 'local')
        return False
    tok['at'] = HE.fmt_time(ctx.utcnow())
    write_json(p('tokens', e + '.json'), tok, private=True)
    st['token_tenure'] = tok['tenure']
    st['last_token'] = tok['at']
    save_state(st)
    return True


def upload_due(ctx, st, now, force=False):
    """Epochs of outbox reports that may go out now (at most 4, oldest first)."""
    if HE.lane() != 'stats':
        return []
    s = HE.settings()
    on_at = (s.get('turned_on') or {}).get('stats')
    try:
        if not force and on_at and now - HE.parse_time(on_at) < FIRST_UPLOAD_WAIT:
            return []
    except ValueError:
        return []
    out = []
    for e in _epoch_files(p('outbox')):
        doc = read_json(p('outbox', e + '.json'), 256 * 1024) or {}
        tok = read_json(p('tokens', e + '.json'), 8192)
        if not tok or HM.week_end(e) + DEADLINE < now:
            continue
        if not force:
            ent = _schedule(st, e, now)
            if now < HE.parse_time(ent['upload_at']):
                continue
            try:
                if now - HE.parse_time(tok.get('at')) < TOKEN_GAP:
                    continue
            except (TypeError, ValueError):
                continue
            nxt = doc.get('next_try')
            if nxt and now < HE.parse_time(nxt):
                continue
        out.append(e)
    return out[:MAX_UPLOADS]


def upload_one(ctx, e):
    """POST one report (spec 5.5, 6.2); returns 'sent', 'retry' or 'dropped'."""
    import hub_token as HT
    if not _recipients_ok(ctx):
        recipients_changed(ctx)
        return 'dropped'
    path = p('outbox', e + '.json')
    doc = read_json(path, 256 * 1024)
    tok = read_json(p('tokens', e + '.json'), 8192)
    base = _collector(ctx)
    if not doc or not tok or not base:
        return 'retry'
    snap = HE.snapshot()
    if snap is None or snap.timestamp is None or not HT.verify_token(tok, snap.timestamp.get('token_keys') or {}):
        rm(p('tokens', e + '.json'))
        return 'retry'
    rep = dict(doc['report'])
    if doc.get('phrases_pending'):
        rep['phrases'] = []
    body = json.dumps(rep, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    try:
        status, data = http(ctx, 'POST', base + 'report', body, {'Whalory-Token': tok['header']}, SHOP_CAP)
    except NetError:
        _retry(path, doc, ctx)
        hub_log(ctx, base + 'report', 0, 'error')
        return 'retry'
    got = _json_body(data) or {}
    receipt = got.get('receipt') if isinstance(got.get('receipt'), str) else None
    hub_log(ctx, base + 'report', len(body), status, receipt)
    if status in (200, 202) and receipt and len(receipt) == 22 and _B64URL.match(receipt):
        write_json(p('sent', e + '.json'), {'epoch': e, 'sent_at': HE.fmt_time(ctx.utcnow()), 'receipt': receipt,
                                            'secret': doc['secret'], 'body': body.decode('utf-8')}, private=True)
        rm(path)
        rm(p('tokens', e + '.json'))
        return 'sent'
    if status == 422:
        recipients_changed(ctx)
        return 'dropped'
    if status == 401:
        rm(p('tokens', e + '.json'))
        return 'retry'
    if status in (400, 409, 410, 413):
        rm(path)
        rm(p('tokens', e + '.json'))
        return 'dropped'
    _retry(path, doc, ctx)
    return 'retry'


def _retry(path, doc, ctx):
    n = int(doc.get('attempts') or 0)
    doc['attempts'] = n + 1
    doc['next_try'] = HE.fmt_time(ctx.utcnow() + datetime.timedelta(seconds=RETRY[min(n, len(RETRY) - 1)]))
    write_json(path, doc, private=True)


def send_deletions(ctx):
    """Send queued deletion requests (spec 4.9, 6.2); returns how many went out."""
    queue = _deletion_queue(ctx)
    if not queue:
        return 0
    base = _collector(ctx)
    if not base or HE.network_blocked():
        return 0
    left, done = [], 0
    for item in queue:
        body = json.dumps({'receipt': item['receipt'], 'secret': item['secret']}, separators=(',', ':')).encode('utf-8')
        try:
            status, data = http(ctx, 'POST', base + 'report/delete', body, None, SHOP_CAP)
        except NetError:
            left.append(item)
            continue
        hub_log(ctx, base + 'report/delete', len(body), status, item['receipt'])
        if status == 200:
            done += 1
        elif status in (429, 500, 502, 503, 504):
            left.append(item)
    _save_deletions(ctx, left)
    return done


def cmd_upload(ctx, a):
    why = stats_ready(ctx)
    if why:
        ctx.say(t(why, ctx.lang))
        return EXIT_OK
    build_due(ctx)
    st = state()
    n = 0
    for e in upload_due(ctx, st, ctx.utcnow(), force=a.now):
        if upload_one(ctx, e) == 'sent':
            n += 1
    save_state(_merge_schedule(st))
    ctx.say(t('upload_done', ctx.lang, n=n) if n else t('upload_none', ctx.lang))
    return EXIT_OK


def _merge_schedule(st_with_schedule):
    cur = state()
    cur['schedule'] = st_with_schedule.get('schedule') or cur.get('schedule') or {}
    return cur


def cmd_preview(ctx, a):
    rows_by_week = []
    for e in _epoch_files(p('outbox')):
        doc = read_json(p('outbox', e + '.json'), 256 * 1024)
        if isinstance(doc, dict) and doc.get('phrases_pending') and (doc.get('report') or {}).get('phrases'):
            rows_by_week.append((e, doc))
    if not rows_by_week:
        ctx.say(t('preview_none', ctx.lang))
        return EXIT_OK
    texts = _ngram_texts()
    if a.approve or a.drop:
        drop = set(a.drop or [])
        for e, doc in rows_by_week:
            rows = doc['report']['phrases']
            doc['report']['phrases'] = [r for i, r in enumerate(rows, 1) if i not in drop]
            if a.approve:
                doc['phrases_pending'] = False
            write_json(p('outbox', e + '.json'), doc, private=True)
        ctx.say(t('preview_done', ctx.lang))
        return EXIT_OK
    for e, doc in rows_by_week:
        ctx.say(e)
        for i, r in enumerate(doc['report']['phrases'], 1):
            ctx.say('  %d. %s  %s  (%s, deleted %s, kept %s)' % (i, r['ng'], texts.get(r['ng'], '?'), r['fg'],
                                                                r['del'], r['kept']))
    return EXIT_OK


def _ngram_texts():
    out = {}
    for lang in ('fa', 'en'):
        path = os.path.join(HE.DATA_DIR, 'ngrams.%s.txt' % lang)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                for line in fh:
                    parts = line.strip().split(None, 1)
                    if len(parts) == 2 and parts[0].startswith('ng-'):
                        out[parts[0]] = parts[1]
        except (OSError, UnicodeDecodeError):
            pass
    return out


# ----------------------------------------------------------------------------- host settings and notices (spec 4.3)


def apply_host_setting(ctx):
    """The plugin setting can only lower a setting or create a pending request (spec 4.3)."""
    req = HE.host_request()
    s = HE.settings()
    if req is None or req == s.get('host_seen'):
        return False
    s = ensure_settings()
    last = s.get('host_seen')
    s['host_seen'] = req
    if req == 'off':
        s['pending'] = None
        if s.get('stats') == 'pending':
            s['stats'] = 'off'
        HE.save_settings(s)
        if last in ('stats', 'stats+phrases') and HE.settings().get('stats') == 'on':
            off_stats(ctx, send=not HE.network_blocked())
        return True
    if s.get('stats') != 'on':
        s['stats'] = 'pending'
        s['pending'] = {'requested': req, 'at': HE.fmt_time(ctx.utcnow()), 'source': 'host'}
        s['asked'] = dict(s.get('asked') or {}, pending_prompted=False)
    HE.save_settings(s)
    return True


def terminal_notices(stream=None, lang=None):
    """For lint.py in a terminal (stdin and stderr are TTYs; never MCP, hook or JSON output):
    the 'turned on' notice, the pending prompt, the one-line hint and the re-consent hint,
    each at most once (spec 4.3, 4.4.6, 4.10). Never raises."""
    try:
        err = stream or sys.stderr
        if HE.hub_disabled() or not (_tty(sys.stdin) and _tty(err)):
            return None
        ctx = Ctx()
        ctx.err = err
        ctx.test = HE.test_mode()
        ctx.out = err
        lg = lang_of(lang)
        s = HE.settings()
        home = HE.hub_home()
        if not home:
            return None
        apply_host_setting(ctx)
        s = HE.settings()
        due = s.get('on_notice_due')
        if isinstance(due, dict) and due.get('at'):
            what = t('what_packets' if due.get('tier') == 'packets' else 'what_stats', lg)
            off = script_cmd('off', 'packets') if due.get('tier') == 'packets' else script_cmd('off')
            _write(err, t('turned_on_notice', lg, what=what, time=due['at'], off=off) + '\n')
            s = dict(s, on_notice_due=None)
            HE.save_settings(s)
        pol = HE.policy()
        asked = dict(s.get('asked') or {})
        if s.get('stats') == 'pending' and not asked.get('pending_prompted') and pol['collection_open']:
            asked['pending_prompted'] = True
            HE.save_settings(dict(s, asked=asked))
            try:
                con = open_console()
            except NoConsole:
                return None
            try:
                con.write(t('pending_prompt', lg))
                if answer(con) == 'y':
                    consent_flow(ctx, lg, con)
            finally:
                con.close()
            return None
        rec = (s.get('consent') or {}).get('stats')
        if rec and HE.consent_problem(rec, 'stats', pol) in ('version', 'old_major', 'expired') \
                and rec.get('version') not in (asked.get('reconsent_hint') or []):
            asked['reconsent_hint'] = list(asked.get('reconsent_hint') or []) + [rec.get('version')]
            HE.save_settings(dict(HE.settings(), asked=asked))
            _write(err, t('reconsent', lg, cmd=script_cmd('consent')) + '\n')
            return None
        never_asked = s.get('stats') == 'off' and not s.get('packets') and not rec \
            and not (s.get('consent') or {}).get('packets')
        if never_asked and asked.get('hint_major') != HE.skill_major():
            doc = consent_doc() or {}
            if pol['collection_open']:
                text = render('hint', lg, doc, {'{CONSENT}': script_cmd('consent')})
            elif pol['lane_open']:
                text = render('hint_packets', lg, doc, {'{CONSENT}': script_cmd('on', 'packets')})
            else:
                text = None
            if text:
                asked['hint_major'] = HE.skill_major()
                HE.save_settings(dict(HE.settings(), asked=asked))
                _write(err, text + '\n')
    except Exception:
        pass
    return None


# ----------------------------------------------------------------------------- consent flows (spec 4.3, 4.4)


def _gate(ctx, lang, tier):
    """None when the screen for tier may be shown, else the message to print."""
    if HE.hub_disabled():
        return t('hub_off', lang)
    if HE.contribution_blocked():
        return t('env_blocks', lang)
    pol = HE.policy()
    if tier == 'stats' and not pol['collection_open']:
        return t('stats_closed', lang)
    if tier == 'packets' and not pol['lane_open']:
        return t('packets_closed', lang)
    if tier == 'phrases':
        if not pol['discovery_open']:
            return t('discovery_closed', lang)
        if HE.lane() != 'stats':
            return t('needs_stats', lang, cmd=script_cmd('on', 'stats'))
    return None


def consent_flow(ctx, lang, con=None):
    """Tier 1 on the console, then Tier 2 when discovery is open (spec 4.4)."""
    msg = _gate(ctx, lang, 'stats')
    if msg:
        ctx.say(msg)
        return EXIT_OK
    doc = consent_doc()
    text = full_screen('stats', lang, doc) if doc else None
    if text is None:
        ctx.say(t('not_final', lang))
        return EXIT_OK
    own = con is None
    con = con or get_console(ctx)
    try:
        con.write(text + '\n> ')
        if answer(con) != 'y':
            con.write(t('said_no', lang) + '\n')
            return EXIT_OK
        if not typed_code(con, lang):
            con.write(t('code_wrong', lang) + '\n')
            return EXIT_OK
        pol = HE.policy()
        s = ensure_settings()
        switched = s.get('packets') is True
        if switched:
            off_packets(ctx)
            s = ensure_settings()
        now = HE.fmt_time(ctx.utcnow())
        s.update(stats='on', pending=None, on_notice_due={'tier': 'stats', 'at': now})
        s['consent'] = dict(s.get('consent') or {}, stats=consent_record(['stats'], lang, text, pol))
        s['turned_on'] = dict(s.get('turned_on') or {}, stats=now)
        HE.save_settings(s)
        if switched:
            con.write(t('lane_switch_packets', lang) + '\n')
        con.write(t('stats_on', lang, off=script_cmd('off')) + '\n')
        _ask_licence(ctx, lang, con)
        if pol['discovery_open']:
            phrases_flow(ctx, lang, con)
    finally:
        if own:
            con.close()
    return EXIT_OK


def _ask_licence(ctx, lang, con):
    if ctx.test or HE.skill_edition() not in ('pro', 'studio'):
        return
    if HE.env('LICENSE_KEY') or os.environ.get('CLAUDE_PLUGIN_OPTION_LICENSE_KEY'):
        return
    import hub_token as HT
    if ctx.console is None:
        import getpass                  # reads the console device without echo, never stdin
        try:
            raw = getpass.getpass(t('licence_prompt', lang)).strip()
        except (EOFError, KeyboardInterrupt, OSError):
            return
    else:
        con.write(t('licence_prompt', lang))
        raw = con.readline().strip()
    if not raw:
        return
    key = HT.normalize_licence_key(raw)
    if key is None:
        con.write(t('licence_bad', lang) + '\n')
        return
    write_json(p('secret.json'), {'licence_key': key}, private=True)


def phrases_flow(ctx, lang, con=None, preview=None):
    msg = _gate(ctx, lang, 'phrases')
    if msg:
        (con.write(msg + '\n') if con is not None else ctx.say(msg))
        return EXIT_OK
    doc = consent_doc()
    text = render('phrases', lang, doc) if doc else None
    if text is None:
        ctx.say(t('not_final', lang))
        return EXIT_OK
    own = con is None
    con = con or get_console(ctx)
    try:
        con.write(text + '\n> ')
        ans = answer(con, YES + NO + PREVIEW)
        if ans not in ('y', 'p'):
            con.write(t('said_no', lang) + '\n')
            return EXIT_OK
        if not typed_code(con, lang):
            con.write(t('code_wrong', lang) + '\n')
            return EXIT_OK
        s = ensure_settings()
        want_preview = (ans == 'p') if preview is None else bool(preview or ans == 'p')
        s.update(phrases=True, phrases_preview=want_preview)
        rec = dict((s.get('consent') or {}).get('stats') or {})
        rec['tiers'] = ['stats', 'phrases']
        s['consent'] = dict(s.get('consent') or {}, stats=rec)
        HE.save_settings(s)
        con.write((t('phrases_preview_on', lang, cmd=script_cmd('preview')) if want_preview
                   else t('phrases_on', lang)) + '\n')
    finally:
        if own:
            con.close()
    return EXIT_OK


def packets_flow(ctx, lang, con=None):
    msg = _gate(ctx, lang, 'packets')
    if msg:
        ctx.say(msg)
        return EXIT_OK
    doc = consent_doc()
    text = full_screen('packets', lang, doc) if doc else None
    if text is None:
        ctx.say(t('not_final', lang))
        return EXIT_OK
    own = con is None
    con = con or get_console(ctx)
    try:
        con.write(text + '\n> ')
        if answer(con) != 'y':
            con.write(t('said_no', lang) + '\n')
            return EXIT_OK
        if not typed_code(con, lang):
            con.write(t('code_wrong', lang) + '\n')
            return EXIT_OK
        pol = HE.policy()
        s = ensure_settings()
        switched = s.get('stats') in ('on', 'pending')
        if switched:
            off_stats(ctx, send=not HE.network_blocked())
            s = ensure_settings()
        now = HE.fmt_time(ctx.utcnow())
        s.update(packets=True, on_notice_due={'tier': 'packets', 'at': now})
        s['consent'] = dict(s.get('consent') or {}, packets=consent_record(['packets'], lang, text, pol))
        s['turned_on'] = dict(s.get('turned_on') or {}, packets=now)
        HE.save_settings(s)
        if switched:
            con.write(t('lane_switch_stats', lang) + '\n')
        con.write(t('packets_on', lang, packet=script_cmd('packet'), off=script_cmd('off', 'packets')) + '\n')
    finally:
        if own:
            con.close()
    return EXIT_OK


# ----------------------------------------------------------------------------- commands


def cmd_consent(ctx, a):
    return consent_flow(ctx, a.lang or ctx.lang)


def cmd_on(ctx, a):
    lang = a.lang or ctx.lang
    if a.tier == 'stats':
        return consent_flow(ctx, lang)
    if a.tier == 'phrases':
        return phrases_flow(ctx, lang, preview=True if a.preview else None)
    return packets_flow(ctx, lang)


def cmd_off(ctx, a):
    lang = ctx.lang
    what = a.tier or 'stats'
    if HE.hub_disabled():
        ctx.say(t('hub_off', lang))
        return EXIT_OK
    if what in ('stats', 'all'):
        sent, left = off_stats(ctx, send=not HE.network_blocked())
        ctx.say(t('off_stats', lang))
        if sent:
            ctx.say(t('off_deleted', lang, n=sent))
        if left:
            ctx.say(t('off_queued', lang, n=left))
    if what == 'phrases':
        off_phrases(ctx)
        ctx.say(t('off_phrases', lang))
    if what in ('packets', 'all'):
        off_packets(ctx)
        ctx.say(t('off_packets', lang))
    if what in ('updates', 'all'):
        s = ensure_settings()
        s['updates'] = False
        HE.save_settings(s)
        ctx.say(t('off_updates', lang))
    return EXIT_OK


def cmd_forget(ctx, a):
    if HE.hub_disabled():
        ctx.say(t('hub_off', ctx.lang))
        return EXIT_OK
    off_stats(ctx, send=not HE.network_blocked())
    off_packets(ctx)
    home = ctx.home()
    for name in ('trusted', 'targets', 'state.json', 'active.json', 'packets', 'events', 'tokens', 'sent',
                 'secret.json', 'corrupt', 'lock'):
        rm(os.path.join(home, name))
    _clear_dir(os.path.join(home, 'outbox'), keep=('deletions.json',))
    s = ensure_settings()
    fresh = HE.default_settings()
    fresh['updates'] = s.get('updates', True)
    fresh['install_salt'] = os.urandom(32).hex()
    fresh['host_seen'] = s.get('host_seen')
    HE.save_settings(fresh)
    ctx.say(t('forget_done', ctx.lang))
    return EXIT_OK


def status_doc(ctx):
    s = HE.settings()
    pol = HE.policy()
    lane, why = HE.lane_state(s, pol)
    st = state()
    active = read_json(p('active.json') or '', 16 * 1024) or {}
    home = ctx.home()
    queue = _epoch_files(os.path.join(home, 'outbox')) if home else []
    pk = _epoch_files(os.path.join(home, 'packets')) if home else []
    sched = {}
    for e, ent in sorted((st.get('schedule') or {}).items()):
        sched[e] = ent
    env = []
    for name in ('WHALORY_HUB', 'WHALORY_HUB_UPDATES', 'WHALORY_HUB_CONTRIBUTE', 'DO_NOT_TRACK', 'DISABLE_TELEMETRY',
                 'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC', 'WHALORY_HUB_OVERLAY'):
        if os.environ.get(name):
            env.append(name)
    consent = s.get('consent') or {}
    return {
        'hub_folder': home,
        'edition': HE.skill_edition(),
        'skill': HE.skill_version(),
        'pinned_root': 'test' if HE.pinned_root_is_test() else 'production',
        'updates': bool(s.get('updates', True)) and not HE.updates_blocked(),
        'stats': s.get('stats'),
        'phrases': bool(s.get('phrases')),
        'phrases_preview': bool(s.get('phrases_preview')),
        'packets': bool(s.get('packets')),
        'capturing': lane,
        'not_capturing_because': why if lane is None else None,
        'pending': s.get('pending'),
        'consent': {k: ({'version': v.get('version'), 'tiers': v.get('tiers'), 'at': v.get('at')} if v else None)
                    for k, v in consent.items()},
        'collection_open': pol['collection_open'],
        'discovery_open': pol['discovery_open'],
        'global_lane_open': pol['lane_open'],
        'active': {'baseline': _ref_id(active.get('baseline')), 'auto': _ref_id(active.get('auto')),
                   'pin': _pin_label(s, active)},
        'stale': bool(pol.get('stale')),
        'halt': bool(pol.get('halt')),
        'last_sync': st.get('last_sync'),
        'last_sync_result': st.get('last_sync_result'),
        'queued_reports': queue,
        'packets_ready': pk,
        'schedule': sched,
        'environment_overrides': env,
    }


def cmd_status(ctx, a):
    d = status_doc(ctx)
    if a.json:
        ctx.say(json.dumps(d, ensure_ascii=False, indent=1))
        return EXIT_OK
    fa = ctx.lang == 'fa'
    stats_word = {'on': ('on', 'روشن'), 'off': ('off', 'خاموش'),
                  'pending': ('requested, waiting for you in a terminal', 'درخواست شده، منتظرِ تأییدِ شما در ترمینال')}
    stats_label = stats_word.get(d['stats'], (d['stats'], d['stats']))[1 if fa else 0]
    capturing = d['capturing'] or (('خیر (%s)' if fa else 'no (%s)') % d['not_capturing_because'])
    rows = [
        ('Hub folder', 'پوشه‌ی هاب', d['hub_folder']),
        ('Edition', 'نسخه', '%s %s' % (d['edition'], d['skill'])),
        ('Pinned root', 'ریشه‌ی سنجاق‌شده', ('آزمایشی' if d['pinned_root'] == 'test' else 'اصلی') if fa
         else d['pinned_root']),
        ('Rule updates', 'به‌روزرسانیِ قاعده‌ها', _onoff(d['updates'], fa)),
        ('Weekly statistics', 'آمارِ هفتگی', stats_label),
        ('Phrase sharing', 'هم‌رسانیِ عبارت‌ها', _onoff(d['phrases'], fa)),
        ('Weekly packets', 'بسته‌های هفتگی', _onoff(d['packets'], fa)),
        ('Capturing now', 'ثبتِ شمارش', capturing),
        ('Collection open', 'جمع‌آوری باز است', _onoff(d['collection_open'], fa)),
        ('Global lane open', 'راهِ جهانی باز است', _onoff(d['global_lane_open'], fa)),
        ('Active overlay', 'قاعده‌های فعال', '%s / %s%s' % (d['active']['baseline'], d['active']['auto'],
                                                            (' (pin %s)' % d['active']['pin']) if d['active']['pin']
                                                            else '')),
        ('Stale metadata', 'فراداده‌ی کهنه', _onoff(d['stale'], fa)),
        ('Last sync', 'آخرین همگام‌سازی', '%s (%s)' % (d['last_sync'], d['last_sync_result'])),
        ('Queued reports', 'گزارش‌های در صف', ', '.join(d['queued_reports']) or '-'),
        ('Packets ready', 'بسته‌های آماده', ', '.join(d['packets_ready']) or '-'),
    ]
    if d['pending']:
        rows.append(('Pending request', 'درخواستِ منتظر', d['pending'].get('requested')))
    if d['environment_overrides']:
        rows.append(('Environment', 'متغیرهای محیطی', ', '.join(d['environment_overrides'])))
    for en, fa_label, value in rows:
        ctx.say('%s: %s' % (fa_label if fa else en, value))
    return EXIT_OK


def _ref_id(ref):
    return ref.get('id') if isinstance(ref, dict) else None


def _pin_label(s, active):
    pin = s.get('pin') if isinstance(s.get('pin'), dict) else {}
    if pin.get('mode') == 'freeze':
        return pin.get('id')
    return pin.get('mode') or active.get('pin')


def _onoff(v, fa):
    return ('روشن' if v else 'خاموش') if fa else ('on' if v else 'off')


def cmd_log(ctx, a):
    home = ctx.home()
    if a.sent:
        out = []
        for e in _epoch_files(os.path.join(home, 'sent')):
            doc = read_json(os.path.join(home, 'sent', e + '.json'), 256 * 1024) or {}
            out.append({'epoch': e, 'sent_at': doc.get('sent_at'), 'receipt': doc.get('receipt'),
                        'body': doc.get('body')})
        if a.json:
            ctx.say(json.dumps(out, ensure_ascii=False, indent=1))
        else:
            for x in out:
                ctx.say('%s  %s  %s' % (x['epoch'], x['sent_at'], x['receipt']))
                ctx.say(x['body'] or '')
        return EXIT_OK
    if a.net:
        data = read_bytes(os.path.join(home, 'hub.log')) or b''
        lines = data.decode('utf-8', 'replace').splitlines()
        ctx.say(json.dumps(lines, indent=1) if a.json else '\n'.join(lines))
        return EXIT_OK
    folder = os.path.join(home, 'events')
    lines = []
    for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        if name.endswith('.jsonl'):
            data = read_bytes(os.path.join(folder, name)) or b''
            lines.extend(data.decode('utf-8', 'replace').splitlines())
    if a.json:
        ctx.say(json.dumps([json.loads(x) for x in lines if x.strip()], ensure_ascii=False, indent=1))
    else:
        ctx.say('\n'.join(lines))
    return EXIT_OK


def cmd_sync(ctx, a):
    why = sync_blocker(ctx)
    if why:
        ctx.say(t(why, ctx.lang))
        return EXIT_OK
    ok, code, summary = run_sync(ctx, force=a.force)
    if code == 'not_due':
        ctx.say(t('sync_not_due', ctx.lang))
    elif ok:
        ctx.say(t('sync_ok', ctx.lang, state=summary or 'no change'))
    else:
        ctx.say(t('sync_fail', ctx.lang, code=code))
    return EXIT_OK


def cmd_pin(ctx, a):
    home = ctx.home()
    target = a.target
    raw = read_bytes(os.path.join(home, 'active.json'), 16 * 1024)
    rec = None
    if raw:
        try:
            rec = _ho().parse_active(raw)
        except Exception:
            rec = None
    s = ensure_settings()
    now = HE.fmt_time(ctx.utcnow())
    if target in ('baseline', 'bundled'):
        s['pin'] = {'mode': target, 'id': None, 'at': now}
        HE.save_settings(s)
        if rec is not None:
            rec = dict(rec, pin=target)
            HE.write_atomic(os.path.join(home, 'active.json'), _active_bytes(rec))
        ctx.say(t('pinned', ctx.lang, pin=target, cmd=script_cmd('unpin')))
        return EXIT_OK
    ids = [(rec or {}).get('baseline') or {}, (rec or {}).get('auto') or {}]
    if target not in [x.get('id') for x in ids if isinstance(x, dict)]:
        ctx.say(t('pin_unknown', ctx.lang, pin=target))
        return EXIT_USAGE
    s['pin'] = {'mode': 'freeze', 'id': target, 'at': now}
    HE.save_settings(s)
    ctx.say(t('pinned', ctx.lang, pin=target, cmd=script_cmd('unpin')))
    return EXIT_OK


def _active_bytes(rec):
    return (json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + '\n').encode('utf-8')


def cmd_unpin(ctx, a):
    home = ctx.home()
    s = ensure_settings()
    s['pin'] = None
    HE.save_settings(s)
    raw = read_bytes(os.path.join(home, 'active.json'), 16 * 1024)
    if raw:
        try:
            rec = _ho().parse_active(raw)
            if rec.get('pin'):
                new = dict(rec, pin=None)
                prev = (rec.get('previous') or [None])[0]
                # A baseline pin dropped the auto overlay; the one active before the pin comes back
                # at once (it passed the caps then), instead of waiting for the next release interval.
                if rec.get('pin') == 'baseline' and rec.get('auto') is None and prev and prev.get('auto') \
                        and prev['baseline']['sha256'] == rec['baseline']['sha256'] \
                        and os.path.exists(os.path.join(home, 'targets', prev['auto']['sha256'] + '.json')):
                    new['auto'] = prev['auto']
                    new['previous'] = list(rec.get('previous') or [])[1:]
                HE.write_atomic(os.path.join(home, 'active.json'), _active_bytes(new))
        except Exception:
            pass
    ctx.say(t('unpinned', ctx.lang))
    return EXIT_OK


def cmd_rollback(ctx, a):
    home = ctx.home()
    raw = read_bytes(os.path.join(home, 'active.json'), 16 * 1024)
    rec = None
    if raw:
        try:
            rec = _ho().parse_active(raw)
        except Exception:
            rec = None
    prev = list((rec or {}).get('previous') or [])
    usable = None
    for i, x in enumerate(prev):
        shas = [x['baseline']['sha256']] + ([x['auto']['sha256']] if x.get('auto') else [])
        if all(os.path.exists(os.path.join(home, 'targets', h + '.json')) for h in shas):
            usable = i
            break
    if usable is None:
        ctx.say(t('rollback_none', ctx.lang))
        return EXIT_OK
    back = prev[usable]
    rest = [x for j, x in enumerate(prev) if j != usable]
    new = {'schema': 'whalory.active/1', 'activated': HE.fmt_time(ctx.utcnow()), 'baseline': back['baseline'],
           'auto': back['auto'], 'pin': None,
           'previous': ([{'baseline': rec['baseline'], 'auto': rec['auto']}] + rest)[:2]}
    HE.write_atomic(os.path.join(home, 'active.json'), _active_bytes(new))
    s = ensure_settings()
    s['pin'] = {'mode': 'freeze', 'id': (back['auto'] or back['baseline'])['id'], 'at': HE.fmt_time(ctx.utcnow())}
    HE.save_settings(s)
    HE.record_health('revert', None, (back['auto'] or back['baseline'])['id'])
    ctx.say(t('rollback_done', ctx.lang, cmd=script_cmd('unpin')))
    return EXIT_OK


def cmd_verify(ctx, a):
    hv = _hv()
    data = read_bytes(a.file, 400 * 1024)
    if data is None:
        ctx.say('cannot read %s' % a.file)
        return EXIT_VERIFY
    try:
        env = hv.loads(data, max_bytes=400 * 1024)
        role = hv.ROLE_OF_TYPE.get(env.get('payloadType'))
        if role is None or role == 'admin':
            raise hv.HubError('payload_type')
        roots = trusted_roots() or [hv.parse_pinned_root(pinned_root())]
        if role == 'root':
            try:
                doc = hv.update_root(roots[-1], data)          # the next root of the chain
            except hv.HubError:
                doc = None
                for r in roots:                                # or one this install already trusts
                    try:
                        got = hv.open_signed(data, 'root', r)
                    except hv.HubError:
                        continue
                    if got['version'] == r['version']:
                        doc = got
                        break
                if doc is None:
                    raise hv.HubError('signature')
        else:
            doc = hv.open_signed(data, role, roots[-1])
    except Exception as e:
        ctx.say('verification failed: %s' % (getattr(e, 'code', None) or type(e).__name__))
        return EXIT_VERIFY
    ctx.say('ok: %s version %s' % (role, doc.get('version')))
    ctx.say(json.dumps(doc, ensure_ascii=False, indent=1))
    return EXIT_OK


def cmd_pinned_root(ctx, a):
    data = pinned_root() or b''
    test = HE.pinned_root_is_test(data)
    ids = HE.root_keyids(data)
    info = {'path': HE.PINNED_ROOT, 'test_root': test, 'keyids': ids,
            'test_keyids': sorted(HE.TEST_KEY_IDS.intersection(ids))}
    try:
        info['version'] = _hv().parse_pinned_root(data)['version']
        info['valid'] = True
    except Exception as e:
        info['valid'] = False
        info['error'] = getattr(e, 'code', type(e).__name__)
    if a.json:
        ctx.say(json.dumps(info, indent=1))
    else:
        ctx.say('%s: %s root%s' % (info['path'], 'TEST' if test else 'production',
                                   '' if info['valid'] else ' (invalid: %s)' % info.get('error')))
    if a.require_production and (test or not info['valid']):
        return EXIT_TEST_ROOT
    return EXIT_OK


# ----------------------------------------------------------------------------- tick (spec 5.6, 5.11)


def codex_network_on():
    """[sandbox_workspace_write] network_access = true in ~/.codex/config.toml (spec 5.6)."""
    path = os.path.join(os.environ.get('CODEX_HOME') or os.path.join(os.path.expanduser('~'), '.codex'),
                        'config.toml')
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            text = fh.read(256 * 1024)
    except (OSError, UnicodeDecodeError):
        return False
    table = None
    for raw in text.splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        m = re.match(r'^\[\s*([^\]]+?)\s*\]$', line)
        if m:
            table = m.group(1).replace('"', '').replace(' ', '')
            continue
        m = re.match(r'^([A-Za-z0-9_."-]+)\s*=\s*(.+)$', line)
        if not m:
            continue
        key, value = m.group(1).replace('"', ''), m.group(2).strip()
        full = key if table is None else table + '.' + key
        if full == 'sandbox_workspace_write.network_access':
            return value == 'true'
    return False


class Lock(object):
    """The `lock` file: one tick at a time, stale after 120 s (spec 4.5)."""

    def __init__(self, path):
        self.path = path
        self.held = False

    def __enter__(self):
        HE.makedirs(os.path.dirname(self.path))
        for _ in range(2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.write(fd, str(os.getpid()).encode('ascii'))
                os.close(fd)
                self.held = True
                return self
            except OSError:
                try:
                    if time.time() - os.path.getmtime(self.path) > LOCK_STALE:
                        os.remove(self.path)
                        continue
                except OSError:
                    continue
                return self
        return self

    def __exit__(self, *exc):
        if self.held:
            rm(self.path)
        return False


def detach(argv):
    """Start `tick` again in a detached child and return at once (spec 5.10 --detach)."""
    args = [sys.executable or 'python3', os.path.abspath(__file__)] + [x for x in argv if x != '--detach']
    kw = {'stdin': subprocess.DEVNULL, 'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL,
          'close_fds': True}
    if os.name == 'nt':
        kw['creationflags'] = 0x00000008 | 0x00000200      # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        kw['start_new_session'] = True
    try:
        subprocess.Popen(args, **kw)
    except Exception:
        pass


def tick(ctx, a):
    """One of: sync if due, a token request if due, or an upload if due (spec 5.10).

    Never prints to stdout. A token request and an upload never happen in one run.
    """
    home = ctx.home()
    if not home:
        return EXIT_OK
    with Lock(os.path.join(home, 'lock')) as lk:
        if not lk.held:
            return EXIT_OK
        ensure_settings()
        apply_host_setting(ctx)
        prune(ctx)
        build_due(ctx)
        net_ok = not HE.network_blocked()
        if a.host == 'codex' and not codex_network_on():
            net_ok = False
        if not net_ok:
            return EXIT_OK
        ctx.net_deadline = time.monotonic() + TICK_NET_SECONDS
        ctx.net_cap = TICK_NET_BYTES
        try:
            send_deletions(ctx)
        except Exception:
            pass
        now = ctx.utcnow()
        st = state()
        if sync_blocker(ctx) is None and sync_due(st, now):
            try:
                run_sync(ctx)
            except Exception:
                HE.record_health('sync_fail')
            return EXIT_OK
        if HE.lane() != 'stats' or not HE.policy()['collection_open']:
            return EXIT_OK
        e = token_due(ctx, st, now)
        save_state(_merge_schedule(st))
        if e is not None:
            try:
                request_token(ctx, e)
            except Exception:
                pass
            return EXIT_OK
        st = state()
        for e in upload_due(ctx, st, now):
            try:
                upload_one(ctx, e)
            except Exception:
                pass
        save_state(_merge_schedule(st))
    return EXIT_OK


# ----------------------------------------------------------------------------- the command line


def _parser():
    ap = argparse.ArgumentParser(prog='hub_client.py', description='Whalory Hub: rule updates, consent, weekly '
                                 'statistics and weekly packets.', epilog='Exit codes: 0 ok, 2 usage, 3 no console, '
                                 '4 verification failure, 5 test root with --require-production.')
    sub = ap.add_subparsers(dest='cmd')
    x = sub.add_parser('status', help='toggles, consent, overlays and queue')
    x.add_argument('--json', action='store_true')
    x = sub.add_parser('consent', help='the consent screen for weekly statistics (console only)')
    x.add_argument('--lang', choices=('fa', 'en'))
    x = sub.add_parser('on', help='turn a tier on (console only)')
    x.add_argument('tier', choices=('stats', 'phrases', 'packets'))
    x.add_argument('--preview', action='store_true')
    x.add_argument('--lang', choices=('fa', 'en'))
    x = sub.add_parser('off', help='turn a tier off (default stats); works offline')
    x.add_argument('tier', nargs='?', choices=('stats', 'phrases', 'packets', 'updates', 'all'))
    x = sub.add_parser('packet', help='show the weekly packet; sends nothing')
    x.add_argument('--show', action='store_true', help='print the packet (the default)')
    x.add_argument('--week')
    x.add_argument('--lang', choices=('fa', 'en', 'both'))
    x.add_argument('--save', metavar='FILE')
    x.add_argument('--json', action='store_true')
    x = sub.add_parser('report', help='show the weekly report (Pro; closed until collection opens)')
    x.add_argument('--week')
    x.add_argument('--json', action='store_true')
    x = sub.add_parser('upload', help='send due reports (Pro; closed until collection opens)')
    x.add_argument('--now', action='store_true')
    x = sub.add_parser('preview', help='phrase rows waiting for approval')
    x.add_argument('--approve', action='store_true')
    x.add_argument('--drop', type=int, nargs='+')
    sub.add_parser('forget', help='off for every lane, delete Hub data, new install salt')
    sub.add_parser('delete', help='same as forget')
    x = sub.add_parser('log', help='local events, sent reports or network log')
    g = x.add_mutually_exclusive_group()
    g.add_argument('--events', action='store_true')
    g.add_argument('--sent', action='store_true')
    g.add_argument('--net', action='store_true')
    x.add_argument('--json', action='store_true')
    x = sub.add_parser('sync', help='signed rule updates')
    x.add_argument('--force', action='store_true')
    x = sub.add_parser('tick', help='what session-start hooks run; prints nothing')
    x.add_argument('--quiet', action='store_true')
    x.add_argument('--detach', action='store_true')
    x.add_argument('--host')
    x = sub.add_parser('pin', help='freeze the local rules')
    x.add_argument('target')
    sub.add_parser('unpin', help='follow signed updates again')
    sub.add_parser('rollback', help='back to the previous active overlay')
    x = sub.add_parser('verify', help='debug: verify one signed file')
    x.add_argument('file')
    x = sub.add_parser('pinned-root', help='is data/hub/root.json the public test root?')
    x.add_argument('--json', action='store_true')
    x.add_argument('--require-production', action='store_true')
    return ap


COMMANDS = {
    'status': cmd_status, 'consent': cmd_consent, 'on': cmd_on, 'off': cmd_off, 'packet': cmd_packet,
    'report': cmd_report, 'upload': cmd_upload, 'preview': cmd_preview, 'forget': cmd_forget,
    'delete': cmd_forget, 'log': cmd_log, 'sync': cmd_sync, 'tick': tick, 'pin': cmd_pin,
    'unpin': cmd_unpin, 'rollback': cmd_rollback, 'verify': cmd_verify, 'pinned-root': cmd_pinned_root,
}


def split_test_flags(argv):
    """Pull the test-only flags (anywhere on the line) out of argv."""
    rest, opts = [], {'test': False, 'hub_home': None, 'mirrors': [], 'collector': None, 'issuer': None}
    it = iter(argv)
    for arg in it:
        name, eq, value = arg.partition('=')
        if name == '--test':
            opts['test'] = True
            continue
        if name in ('--hub-home', '--mirror', '--collector', '--issuer'):
            if not eq:
                value = next(it, None)
                if value is None:
                    raise UsageError('%s needs a value' % name)
            if name == '--hub-home':
                opts['hub_home'] = value
            elif name == '--mirror':
                opts['mirrors'].append(value if value.endswith('/') else value + '/')
            elif name == '--collector':
                opts['collector'] = value if value.endswith('/') else value + '/'
            else:
                opts['issuer'] = value if value.endswith('/') else value + '/'
            continue
        rest.append(arg)
    if (opts['hub_home'] or opts['mirrors'] or opts['collector'] or opts['issuer']) and not opts['test']:
        raise UsageError('--hub-home, --mirror, --collector and --issuer are test flags; they need --test')
    if opts['test'] and not opts['hub_home']:
        raise UsageError('--test needs --hub-home inside the system temp folder')
    return rest, opts


def main(argv=None, ctx=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ctx = ctx or Ctx()
    is_tick = bool(argv) and 'tick' in argv
    try:
        rest, opts = split_test_flags(argv)
        if opts['test']:
            try:
                HE.configure(hub_home=opts['hub_home'], test=True, now=ctx.now)
            except ValueError as e:
                raise UsageError(str(e))
            try:
                _ho().configure(hub_home=HE.hub_home(), now=ctx.now)
            except Exception:
                pass
        ctx.test = opts['test']
        ctx.mirrors = opts['mirrors']
        ctx.collector = opts['collector']
        ctx.issuer = opts['issuer']
        for u in ctx.mirrors + [x for x in (ctx.collector, ctx.issuer) if x]:
            if not _url_ok(ctx, u):
                raise UsageError('refused URL %s' % u)
        ap = _parser()
        if not rest:
            ap.print_help(ctx.out)
            return EXIT_USAGE
        saved = sys.stdout
        if ctx.out is not None:
            sys.stdout = ctx.out                # --help goes where the run's output goes
        try:
            a = ap.parse_args(rest)
        except SystemExit as e:
            return EXIT_OK if e.code in (0, None) else EXIT_USAGE
        finally:
            sys.stdout = saved
        if a.cmd is None:
            ap.print_help(ctx.out)
            return EXIT_USAGE
        if getattr(a, 'lang', None) in ('fa', 'en'):
            ctx.lang = a.lang
        if a.cmd == 'tick':
            ctx.quiet = True
            ctx.out = None
            ctx.host = a.host
            if a.detach:
                detach(argv)
                return EXIT_OK
        if HE.hub_disabled() and a.cmd not in ('status', 'pinned-root', 'verify'):
            if a.cmd != 'tick':
                ctx.say(t('hub_off', ctx.lang))
            return EXIT_OK
        if a.cmd not in ('tick', 'pinned-root', 'verify'):
            ensure_settings()
            apply_host_setting(ctx)
            prune(ctx)
            if a.cmd not in ('off', 'forget', 'delete'):
                build_due(ctx)          # the first run of any Hub command after Monday (spec 17.3.1)
        return COMMANDS[a.cmd](ctx, a)
    except UsageError as e:
        if not is_tick:
            _write(sys.stderr, 'hub_client.py: %s\n' % e)
        return EXIT_OK if is_tick else EXIT_USAGE
    except NoConsole:
        if not is_tick:
            ctx.say(t('no_console', ctx.lang))
        return EXIT_OK if is_tick else EXIT_NO_CONSOLE
    except Exception as e:
        if is_tick:
            return EXIT_OK
        _write(sys.stderr, 'hub_client.py: %s: %s\n' % (type(e).__name__, str(e)[:200]))
        return 1


if __name__ == '__main__':
    if 'tick' in sys.argv[1:]:
        sys.stdout = open(os.devnull, 'w')
    sys.exit(main())
