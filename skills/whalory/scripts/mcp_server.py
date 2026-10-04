#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mcp_server: Whalory's local MCP server (stdio, JSON-RPC 2.0).

Zero dependencies: Python 3.8+ standard library only. The server speaks both
protocol eras on the same process:

- legacy: the ``initialize`` handshake, versions 2025-11-25, 2025-06-18,
  2025-03-26 and 2024-11-05 (the client's version is echoed when supported);
- modern: 2026-07-28, with ``server/discover`` and per-request ``_meta``.

The server opens no sockets and starts no process except its time-limited lint worker
(this same file with ``--worker``). It writes no files, except that when the user has
turned on Whalory Hub statistics in a terminal, ``lint_text``, ``lint_file`` and
``check_final`` append counts (never text) to the Hub folder, through
``hub_events.py``; it never writes Python bytecode caches. Tools never access the
network. It writes JSON-RPC messages to stdout and nothing else; logs go to stderr.

Whalory Hub (spec 5.11). ``check_final`` is the final lint of the copy the user
approved. While ``hub_events.enabled()`` is false, ``lint_text``, ``lint_file`` and
``check_final`` are annotated read-only. When it becomes true, the server sends
``notifications/tools/list_changed`` (legacy sessions, and modern listen streams that
asked for ``toolsListChanged``) and lists them with ``readOnlyHint: false``. The
setting is checked again at every call, so a change takes effect at once even if a
host ignores the notification. Only then do ``lint_text`` and ``lint_file`` record
counts of their findings (the hidden shadow and held-out ones travel back from the
worker internally and never reach the output) and keep the linted text in memory for
``check_final`` (at most 8 texts for at most 6 hours, never on disk). The linters
read the verified overlay through ``hub_overlay.py``, a read of the Hub folder that is
not subject to ``--root``. ``--test --hub-home DIR`` (a folder inside the system temp
folder) points the Hub modules at a test folder; tests use it, hosts never do.

Allowed folders. File tools read only inside the project folders and the skill
folder. The project folders come from the first of these that applies:

1. ``--root`` or WHALORY_ROOTS, when at least one value is a folder that exists;
2. the client's roots (MCP ``roots/list``), when the client declares the ``roots``
   capability; the server asks again on ``notifications/roots/list_changed``;
The current working directory never grants file access. An explicit folder
argument, environment setting, or client workspace root is required.

This fails closed: when ``--root`` or WHALORY_ROOTS was given but no value is
usable (a ``${...}`` the host did not fill in, an empty value, a missing folder),
the working folder is never used; only client roots can stand in. With no
project folder, the file tools return an error that says how to add one, and
profile_lookup skips the project step. Symbolic links and junctions that lead
outside the allowed folders are refused.

Time limit. lint_text, lint_file and compare_texts run in a child Python process
(this same file with ``--worker``, started with ``sys.executable`` and no shell).
A call that runs longer than the time limit (``--time-limit``, default 30 s) is
stopped with a tool error, and ``notifications/cancelled`` stops it at once. The
server keeps reading while a tool runs, so ``ping`` is answered at once;
responses to other requests keep their order. ``--time-limit 0`` runs every tool
in the server process with no limit, which is also the fallback when a child
process cannot start.

Usage:
    python mcp_server.py                          # serve over stdio
    python mcp_server.py --root ~/project ~/docs  # folders the file tools may read
    python mcp_server.py --time-limit 10          # seconds per lint or compare call
    python mcp_server.py --self-check --json      # tools, prompts, resources, tier
    python mcp_server.py --version
    python mcp_server.py --test --hub-home DIR    # tests only: a Hub folder inside the temp folder

Environment: WHALORY_ROOTS (folders separated by os.pathsep), WHALORY_LANG (auto,
fa or en) and WHALORY_TIME_LIMIT (seconds). The deprecated WHALYA_* names are read
when the WHALORY_* one is empty. Design: Whalory 3.0.0 build spec,
section G, and the Hub spec (hub/SPEC.md), section 5.11. Protocol:
https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning ;
roots: https://modelcontextprotocol.io/specification/2025-11-25/client/roots
"""
from __future__ import print_function

import sys

if sys.version_info < (3, 8):  # before anything else, so the message stays readable
    sys.stderr.write('whalory mcp_server needs Python 3.8 or newer (found %s).\n' % sys.version.split()[0])
    sys.exit(2)

# The skill or plugin folder is read-only for this server: the lazy imports of lint, lint_fa,
# lint_en, textcount and ab_calc must not create scripts/__pycache__ (spec G.5.6).
sys.dont_write_bytecode = True

import base64  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import queue  # noqa: E402
import re  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402

__version__ = '3.2.1'

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- protocol constants
LEGACY_VERSIONS = ['2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05']
LEGACY_DEFAULT = '2025-11-25'
MODERN_VERSIONS = ['2026-07-28']
# Versions that predate structuredContent and outputSchema (added in 2025-06-18).
PRE_STRUCTURED = ('2024-11-05', '2025-03-26')

META_PV = 'io.modelcontextprotocol/protocolVersion'
META_CAPS = 'io.modelcontextprotocol/clientCapabilities'
META_SINFO = 'io.modelcontextprotocol/serverInfo'
META_SUBID = 'io.modelcontextprotocol/subscriptionId'

SERVER_INFO = {
    'name': 'whalory',
    'title': 'Whalory',
    'version': __version__,
    'description': 'English and Persian copy tools: bilingual linters, playbooks, references, channel limits.',
    'websiteUrl': 'https://whalory.com/',
}

INSTRUCTIONS = (
    'Whalory tools check and support English and Persian business copy. Call lint_text or lint_file '
    'after drafting, and check_final once on the copy the user approves; channel_limits before writing for a '
    'platform; get_playbook to load the procedure for a task; get_reference_section to read one section of a '
    'craft reference; profile_lookup to find the brand voice. Tools never access the network. '
    '\u00ab\u0627\u0628\u0632\u0627\u0631\u0647\u0627\u06cc \u0648\u0627\u0644\u0648\u0631\u06cc \u0628\u0631\u0627\u06cc \u0645\u062a\u0646\u0650 \u0641\u0627\u0631\u0633\u06cc \u0648 \u0627\u0646\u06af\u0644\u06cc\u0633\u06cc\u200c\u0627\u0646\u062f.\u00bb'
)

CAPABILITIES = {'tools': {'listChanged': True}, 'prompts': {}, 'resources': {}}

TTL_LONG = 3600000     # discover, tools/list, prompts/list, resources/templates/list
TTL_SHORT = 300000     # resources/list, resources/read

# ---------------------------------------------------------------- limits (spec G.5)
MAX_LINE = 16 * 1024 * 1024      # one JSON-RPC line
MAX_RESPONSE = 5 * 1024 * 1024   # one response (the TS SDK v1 client caps at 10 MB)
MAX_ARGS = 1024 * 1024           # serialized tool arguments
MAX_DEPTH = 64                   # JSON nesting
MAX_TEXT = 200000                # text inputs, in characters
MAX_FILE = 2 * 1024 * 1024       # files read by tools and resources
MAX_CSV_ROWS = 20000
MAX_ISSUES = 200
MAX_ENTRIES = 5000               # detect_context
PAGE = 50
PLAYBOOK_MAX_CHARS = 60000
TIME_LIMIT = 30.0                # seconds per worker call (the TS SDK v1 client gives up at 60 s)
TIME_LIMIT_MAX = 600.0
ROOTS_WAIT = 5.0                 # seconds a file tool waits for the client's roots/list answer
MAX_CLIENT_ROOTS = 100

# Tools whose linters can run long on odd input; they run in the worker process (see Worker).
WORKER_TOOLS = ('lint_text', 'lint_file', 'check_final', 'compare_texts')
# Tools whose annotations follow the Whalory Hub statistics setting (Hub spec 5.11).
HUB_TOOLS = ('lint_text', 'lint_file', 'check_final')
# check_final's outcome refuses longer texts (Hub spec 5.3, "too_long"), so a longer linted text is
# remembered only as its first REMEMBER_MAX + 1 characters: enough to be refused, never compared.
REMEMBER_MAX = 20000
HUB_POLL = 15.0                  # seconds between looks at the statistics setting while serving
# Requests answered as soon as they are read; the rest wait their turn in order.
SYNC_METHODS = ('initialize', 'ping', 'subscriptions/listen')

MD_MIME = 'text/markdown'
JSON_MIME = 'application/json'

ROOT_DOCS = ['GUIDE.en.md', 'GUIDE.fa.md', 'README.en.md', 'README.md', 'WHALORY.md']
SKILL_DIRS = ('scripts', 'references', 'profiles', 'examples', 'data')  # relative paths that may reach the skill

FMT = ['caption', 'story', 'reels', 'carousel', 'post', 'sms', 'otp', 'email', 'subject', 'push', 'ui',
       'error', 'product', 'listing', 'landing', 'about', 'blog', 'ad', 'press', 'bot', 'reply', 'hard',
       'deck', 'script', 'name', 'headline']

READ_ONLY = {'readOnlyHint': True, 'destructiveHint': False, 'idempotentHint': True, 'openWorldHint': False}
# lint_text, lint_file and check_final while Hub statistics are on: they append counts to the Hub folder.
RECORDING = {'readOnlyHint': False, 'destructiveHint': False, 'idempotentHint': False, 'openWorldHint': False}

LINT_EXTS = ('.txt', '.md', '.mdx', '.markdown', '.html', '.htm', '.json', '.po', '.pot', '.arb',
             '.xliff', '.xlf', '.strings', '.xml', '.csv', '.tsv')
MD_EXTS = ('.md', '.mdx', '.markdown')

EN_MISSING = ('English linting needs scripts/lint.py and scripts/lint_en.py, which are not in this copy '
              'of Whalory. Lint Persian text with lang "fa", or update Whalory.')

_WIN = os.name == 'nt'


# ---------------------------------------------------------------- schemas
ISSUE = {'type': 'object', 'properties': {
    'line': {'type': ['integer', 'null']}, 'col': {'type': ['integer', 'null']},
    'key': {'type': ['string', 'null']}, 'rule': {'type': 'string'},
    'severity': {'type': 'string', 'enum': ['error', 'warning']},
    'message': {'type': 'string'}, 'excerpt': {'type': 'string'}},
    'required': ['rule', 'severity', 'message']}

LANG_IN = {'type': 'string', 'enum': ['auto', 'fa', 'en'], 'default': 'auto',
           'description': 'auto detects the language per line'}
FORMAT_IN = {'type': 'string', 'enum': FMT,
             'description': 'Whalory format id; sets the limits for sentence length, emoji and exclamation marks'}
CHANNEL_IN = {'type': 'string', 'pattern': '^[a-z0-9-]+(/[a-z0-9-]+)?(\\.[a-z0-9_]+)?$',
              'description': 'e.g. instagram.caption, linkedin.post (Pro data)'}
PROFILE_IN = {'type': 'string', 'maxLength': 260,
              'description': "Profile name (whalory, starter-saas, en/saas), 'auto', or a path inside an allowed root"}
FACTS_IN = {'type': 'string', 'maxLength': 200000,
            'description': 'Brief or source text; English facts missing from it are flagged'}

LINT_TEXT_IN = {'type': 'object', 'additionalProperties': False, 'required': ['text'], 'properties': {
    'text': {'type': 'string', 'minLength': 1, 'maxLength': MAX_TEXT, 'description': 'The copy to check'},
    'lang': LANG_IN,
    'format': FORMAT_IN,
    'channel': CHANNEL_IN,
    'profile': PROFILE_IN,
    'profile_json': {'type': 'object', 'description': 'Inline voice profile (schema v2); wins over profile'},
    'facts': FACTS_IN,
    'md': {'type': 'boolean', 'default': False, 'description': 'The text is Markdown'},
    'max_words': {'type': 'integer', 'minimum': 3, 'maximum': 120, 'description': 'Sentence length cap'},
    'strict': {'type': 'boolean', 'default': False, 'description': 'Warnings also fail the check'}}}

LINT_OUT = {'type': 'object', 'required': ['lang', 'passed', 'summary', 'issues', 'stats'], 'properties': {
    'lang': {'type': 'string', 'enum': ['fa', 'en', 'mixed']},
    'passed': {'type': 'boolean'},
    'summary': {'type': 'object', 'required': ['errors', 'warnings'],
                'properties': {'errors': {'type': 'integer'}, 'warnings': {'type': 'integer'}}},
    'issues': {'type': 'array', 'maxItems': MAX_ISSUES, 'items': ISSUE},
    'stats': {'type': 'object'},
    'truncated': {'type': 'boolean'}}}

LINT_FILE_IN = {'type': 'object', 'additionalProperties': False, 'required': ['path'], 'properties': {
    'path': {'type': 'string', 'minLength': 1, 'maxLength': 1024,
             'description': 'File inside an allowed folder; a relative path starts at the project folder'},
    'lang': LANG_IN,
    'format': FORMAT_IN,
    'channel': CHANNEL_IN,
    'profile': PROFILE_IN,
    'facts': FACTS_IN,
    'csv_columns': {'type': 'string', 'maxLength': 500, 'description': 'CSV/TSV: comma-separated text columns'},
    'csv_key': {'type': 'string', 'maxLength': 100, 'description': 'CSV/TSV: id column used in issue keys'},
    'md': {'type': 'boolean', 'description': 'Treat as Markdown; default comes from the extension'}}}

LINT_FILE_OUT = json.loads(json.dumps(LINT_OUT))
LINT_FILE_OUT['properties']['path'] = {'type': 'string'}

CHECK_FINAL_IN = {'type': 'object', 'additionalProperties': False, 'required': ['text'], 'properties': {
    'text': {'type': 'string', 'minLength': 1, 'maxLength': MAX_TEXT, 'description': 'The final copy the user approved'},
    'language': LANG_IN,
    'format': FORMAT_IN,
    'channel': CHANNEL_IN,
    'profile': PROFILE_IN,
    'md': {'type': 'boolean', 'default': False, 'description': 'The text is Markdown'},
    'playbook': {'type': 'string', 'pattern': '^[a-z0-9-]{1,40}$',
                 'description': "The playbook used for the copy, e.g. caption or landing"},
    'revisions': {'type': 'integer', 'minimum': 0, 'maximum': 20,
                  'description': 'Revision rounds before the user approved (0: approved as first shown)'}}}

DETECT_IN = {'type': 'object', 'additionalProperties': False, 'properties': {
    'dir': {'type': 'string', 'maxLength': 1024, 'description': 'Project folder; default: the first allowed folder'},
    'request': {'type': 'string', 'maxLength': 5000, 'description': "The user's request, for a language hint"},
    'max_entries': {'type': 'integer', 'minimum': 100, 'maximum': MAX_ENTRIES, 'default': 2000},
    'max_depth': {'type': 'integer', 'minimum': 1, 'maximum': 10, 'default': 4}}}

DETECT_OUT = {'type': 'object', 'required': ['route', 'summary', 'probe'], 'properties': {
    'route': {'type': 'string', 'enum': ['repo-microcopy', 'repo-content', 'bulk-catalog', 'standard']},
    'summary': {'type': 'string'},
    'request_lang': {'type': ['string', 'null'], 'enum': ['fa', 'en', 'mixed', None]},
    'probe': {'type': 'object'}}}

PLAYBOOK_IN = {'type': 'object', 'additionalProperties': False, 'required': ['task'], 'properties': {
    'task': {'type': 'string', 'minLength': 2, 'maxLength': 500,
             'description': "A playbook anchor such as 'caption', or the task in English or Persian"},
    'limit': {'type': 'integer', 'minimum': 1, 'maximum': 5, 'default': 3}}}

REFERENCE_IN = {'type': 'object', 'additionalProperties': False, 'required': ['path'], 'properties': {
    'path': {'type': 'string', 'pattern': '^[A-Za-z0-9._/-]+\\.(md|json)$', 'maxLength': 200,
             'description': 'e.g. references/router.md, fa/craft.md, en/prose.md, profiles/whalory.json'},
    'anchor': {'type': 'string', 'maxLength': 200, 'description': 'Heading slug; omit it to get the contents list'},
    'max_chars': {'type': 'integer', 'minimum': 1000, 'maximum': 60000, 'default': 20000}}}

CHANNEL_LIMITS_IN = {'type': 'object', 'additionalProperties': False, 'properties': {
    'channel': {'type': 'string', 'maxLength': 80, 'description': 'Channel id, e.g. instagram or social/x'},
    'field': {'type': 'string', 'maxLength': 60, 'description': 'Field id, e.g. caption'},
    'region': {'type': 'string', 'enum': ['ir', 'intl', 'any'], 'default': 'any'},
    'query': {'type': 'string', 'maxLength': 100, 'description': 'Free-text filter on ids, names and labels'},
    'limit': {'type': 'integer', 'minimum': 1, 'maximum': 100, 'default': 20}}}

_FIELD_OUT = {'type': 'object', 'properties': {
    'field': {'type': 'string'}, 'label_en': {'type': 'string'},
    'max_chars': {'type': ['integer', 'null']}, 'visible_chars': {'type': ['integer', 'null']},
    'max_items': {'type': ['integer', 'null']}, 'item_max_chars': {'type': ['integer', 'null']},
    'unit': {'type': 'string'}, 'status': {'type': 'string'}, 'verified_on': {'type': 'string'},
    'source': {'type': 'string'}, 'note_en': {'type': 'string'}}}

CHANNEL_LIMITS_OUT = {'type': 'object', 'required': ['channels', 'count'], 'properties': {
    'count': {'type': 'integer'},
    'channels': {'type': 'array', 'items': {'type': 'object', 'required': ['id', 'group', 'region', 'fields'],
                                            'properties': {
                                                'id': {'type': 'string'}, 'group': {'type': 'string'},
                                                'name_en': {'type': 'string'}, 'name_fa': {'type': 'string'},
                                                'region': {'type': 'string'}, 'kind': {'type': 'string'},
                                                'format_id': {'type': 'string'},
                                                'fields': {'type': 'array', 'items': _FIELD_OUT}}}}}}

COMPARE_IN = {'type': 'object', 'additionalProperties': False, 'required': ['before', 'after'], 'properties': {
    'before': {'type': 'string', 'maxLength': MAX_TEXT, 'description': 'Original text, or the source of a transcreation'},
    'after': {'type': 'string', 'maxLength': MAX_TEXT, 'description': 'Rewrite, or the transcreated text'},
    'lang': {'type': 'string', 'enum': ['auto', 'fa', 'en'], 'default': 'auto'},
    'profile': {'type': 'string', 'maxLength': 260},
    'format': {'type': 'string', 'enum': FMT},
    'strict': {'type': 'boolean', 'default': False}}}

_STR_LIST = {'type': 'array', 'items': {'type': 'string'}}
COMPARE_OUT = {'type': 'object', 'required': ['verdict', 'added', 'removed', 'dropped_conditions'], 'properties': {
    'verdict': {'type': 'string', 'enum': ['ok', 'review']},
    'lang_before': {'type': 'string'}, 'lang_after': {'type': 'string'},
    'added': {'type': 'object', 'properties': {'numbers': _STR_LIST, 'names': _STR_LIST, 'quotes': _STR_LIST}},
    'removed': {'type': 'object'},
    'dropped_conditions': _STR_LIST,
    'lint_before': {'type': 'object'}, 'lint_after': {'type': 'object'},
    'notes': _STR_LIST}}

_COUNT = {'type': 'object', 'required': ['successes', 'total'], 'properties': {
    'successes': {'type': 'integer', 'minimum': 0}, 'total': {'type': 'integer', 'minimum': 1}}}
AB_IN = {'type': 'object', 'additionalProperties': False, 'required': ['mode'], 'properties': {
    'mode': {'type': 'string', 'enum': ['size', 'test'],
             'description': 'size: sample size per variant; test: significance of observed results'},
    'base_rate': {'type': 'number', 'exclusiveMinimum': 0, 'exclusiveMaximum': 1},
    'mde': {'type': 'number', 'exclusiveMinimum': 0, 'description': 'Minimum detectable effect'},
    'mde_type': {'type': 'string', 'enum': ['relative', 'absolute'], 'default': 'relative'},
    'alpha': {'type': 'number', 'minimum': 0.001, 'maximum': 0.2, 'default': 0.05},
    'power': {'type': 'number', 'minimum': 0.5, 'maximum': 0.99, 'default': 0.8},
    'variants': {'type': 'integer', 'minimum': 2, 'maximum': 10, 'default': 2},
    'daily_traffic': {'type': 'integer', 'minimum': 1},
    'one_sided': {'type': 'boolean', 'default': False},
    'a': _COUNT,
    'b': _COUNT}}

AB_OUT = {'type': 'object', 'required': ['mode'], 'properties': {
    'mode': {'type': 'string'}, 'per_variant': {'type': 'integer'}, 'total': {'type': 'integer'},
    'days': {'type': ['number', 'null']}, 'p1': {'type': 'number'}, 'p2': {'type': 'number'},
    'p_a': {'type': 'number'}, 'p_b': {'type': 'number'}, 'lift_abs': {'type': 'number'},
    'lift_rel': {'type': 'number'}, 'z': {'type': 'number'}, 'p_value': {'type': 'number'},
    'significant': {'type': 'boolean'}, 'ci_low': {'type': 'number'}, 'ci_high': {'type': 'number'}}}

PROFILE_LOOKUP_IN = {'type': 'object', 'additionalProperties': False, 'properties': {
    'name': {'type': 'string', 'maxLength': 80, 'description': 'Brand or profile name, e.g. whalory, saas, en/saas'},
    'project_dir': {'type': 'string', 'maxLength': 1024, 'description': 'Project folder; default: the first allowed folder'},
    'include_learnings': {'type': 'boolean', 'default': True},
    'language': {'type': 'string', 'enum': ['fa', 'en']},
    'industry': {'type': 'string', 'maxLength': 40, 'description': 'Industry slug for the closest starter, e.g. saas'}}}

PROFILE_LOOKUP_OUT = {'type': 'object', 'required': ['found', 'source'], 'properties': {
    'found': {'type': 'boolean'},
    'source': {'type': 'string', 'enum': ['project', 'user', 'skill', 'starter', 'whalory', 'none']},
    'is_brand_profile': {'type': 'boolean'},
    'path': {'type': ['string', 'null']}, 'markdown_path': {'type': ['string', 'null']},
    'profile': {'type': ['object', 'null']},
    'warnings': _STR_LIST,
    'learnings': {'type': ['object', 'null'], 'properties': {'path': {'type': 'string'}, 'text': {'type': 'string'}}},
    'starters': {'type': 'array', 'items': {'type': 'object', 'properties': {
        'slug': {'type': 'string'}, 'language': {'type': 'string'}, 'path': {'type': 'string'},
        'industry': {'type': 'string'}}}}}}

CONTENT_META = {'anthropic/maxResultSizeChars': 100000}

# Order of spec G.2; the listed set depends on what this copy of Whalory contains.
TOOLS = [
    {'name': 'lint_text', 'title': 'Lint copy (Persian or English)',
     'description': ("Check Persian or English copy against Whalory's rules (AI tells, puffery, spelling, "
                     "punctuation, sentence length, readability, brand profile and channel limits). Language is "
                     "detected per line unless set."),
     'inputSchema': LINT_TEXT_IN, 'outputSchema': LINT_OUT, 'needs': 'lint', 'run': 't_lint_text'},
    {'name': 'lint_file', 'title': 'Lint a file',
     'description': ("Lint a text, Markdown, HTML, CSV/TSV or locale file (json, po, arb, xliff, strings, "
                     "strings.xml) inside an allowed folder. Locale keys and placeholders are never changed; CSV "
                     "issues are keyed row/sku/column."),
     'inputSchema': LINT_FILE_IN, 'outputSchema': LINT_FILE_OUT, 'needs': 'lint', 'run': 't_lint_file'},
    {'name': 'check_final', 'title': 'Final check of approved copy',
     'description': ("Final check of the copy the user approved: runs Whalory's checks and returns any remaining "
                     "findings, in the same form as lint_text. Call it once when the user approves final copy. If "
                     "the user turned on Whalory Hub statistics or weekly packets in their own terminal, it also "
                     "records counts on this computer, never text, of which Whalory checks the user's own edits "
                     "removed. With statistics, the user chose to send those counts weekly to Whalory's server in "
                     "Iran; a packet leaves the computer only if the user posts it on GitHub."),
     'inputSchema': CHECK_FINAL_IN, 'outputSchema': LINT_OUT, 'needs': 'lint', 'run': 't_check_final'},
    {'name': 'detect_context', 'title': 'Probe a project folder',
     'description': ("Cheap scan of a project folder for step 0 of the method: repository signals, locale files "
                     "and their languages, content folders, catalogs, images, voice-profile candidates and "
                     "learnings notes, and a suggested route. Optional request text gets a language hint."),
     'inputSchema': DETECT_IN, 'outputSchema': DETECT_OUT, 'needs': 'detect_context', 'run': 't_detect_context'},
    {'name': 'get_playbook', 'title': 'Load a playbook',
     'description': ("Return the Whalory playbook section for a task (steps, questions, references, output, QA). "
                     "Accepts a playbook anchor such as 'caption' or a free-text task in English or Persian; "
                     "returns the best match and up to limit-1 alternatives."),
     'inputSchema': PLAYBOOK_IN, 'needs': 'playbooks', 'run': 't_get_playbook', '_meta': CONTENT_META},
    {'name': 'get_reference_section', 'title': 'Read a reference section',
     'description': ("Read one section (or the contents list) of a Whalory reference file under references/ "
                     "(method, fa/, en/), profiles/ or data/channels/. Long files: call without anchor to get "
                     "the contents list first."),
     'inputSchema': REFERENCE_IN, 'needs': 'references', 'run': 't_get_reference_section', '_meta': CONTENT_META},
    {'name': 'channel_limits', 'title': 'Channel limits',
     'description': ("Character, byte, grapheme or item limits for a platform field, with unit, fold, "
                     "verification status, date and source. Covers Iranian and international channels."),
     'inputSchema': CHANNEL_LIMITS_IN, 'outputSchema': CHANNEL_LIMITS_OUT, 'needs': 'channels',
     'run': 't_channel_limits'},
    {'name': 'compare_texts', 'title': 'Compare before and after',
     'description': ("Compare an original and a rewrite (or a source and its transcreation) in Persian or "
                     "English: numbers, names, quotes, currencies and conditions added or dropped, plus lint "
                     "counts before and after."),
     'inputSchema': COMPARE_IN, 'outputSchema': COMPARE_OUT, 'needs': 'compare', 'run': 't_compare_texts'},
    {'name': 'ab_test_size', 'title': 'A/B test size and significance',
     'description': ("Sample size per variant for a conversion-rate test, or a two-proportion z-test on "
                     "observed results. Rates are fractions (0.03 = 3%)."),
     'inputSchema': AB_IN, 'outputSchema': AB_OUT, 'needs': 'ab_calc', 'run': 't_ab_test_size'},
    {'name': 'profile_lookup', 'title': 'Find the voice profile',
     'description': ("Find the brand voice profile in Whalory's order: project VOICE.md/voice.json/voice/VOICE.md, "
                     "~/.whalory/profiles/<brand>, the skill's profiles, the closest starter. Returns the normalized "
                     "JSON profile, the learnings note and starter suggestions."),
     'inputSchema': PROFILE_LOOKUP_IN, 'outputSchema': PROFILE_LOOKUP_OUT, 'needs': None, 'run': 't_profile_lookup'},
]
PRO_TOOLS = ('detect_context', 'channel_limits', 'compare_texts', 'ab_test_size')

PROMPTS = [
    {'name': 'write', 'title': 'Write copy with Whalory',
     'description': 'Load the Whalory method and write copy for a task, channel and output language.',
     'arguments': [
         {'name': 'task', 'description': 'What to write, e.g. a LinkedIn post announcing a feature', 'required': True},
         {'name': 'channel', 'description': 'Channel or format, e.g. instagram.caption or email', 'required': False},
         {'name': 'language', 'description': 'Output language: auto, fa or en', 'required': False},
         {'name': 'profile', 'description': 'Voice profile name or path', 'required': False}],
     'resource': 'skill/SKILL.md'},
    {'name': 'review', 'title': 'Blind review',
     'description': 'Score a draft as a blind editor: score table, must-fix list and at most three line edits.',
     'arguments': [
         {'name': 'text', 'description': 'The draft to review', 'required': True},
         {'name': 'channel', 'description': 'Channel or format of the draft', 'required': False},
         {'name': 'language', 'description': 'Language of the draft: auto, fa or en', 'required': False}],
     'resource': 'references/editor.md'},
    {'name': 'transcreate', 'title': 'Transcreate fa-en',
     'description': 'Transcreate copy between Persian and English for a market, keeping every fact.',
     'arguments': [
         {'name': 'text', 'description': 'The source text', 'required': True},
         {'name': 'target_language', 'description': 'fa or en', 'required': True},
         {'name': 'market', 'description': 'Target market, e.g. US, UK, Iran', 'required': False}],
     'resource': 'references/transcreation.md'},
    {'name': 'voice', 'title': 'Build a voice profile',
     'description': 'Build VOICE.md and voice.json for a brand from a few answers or sample texts.',
     'arguments': [
         {'name': 'brand', 'description': 'Brand name', 'required': True},
         {'name': 'samples', 'description': 'Sample texts in the brand voice (optional)', 'required': False}],
     'resource': 'references/profile-builder.md'},
]

# ---------------------------------------------------------------- stderr logging
try:  # Persian-safe stderr on Windows code pages
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

_DEBUG = [False]


def log(msg):
    try:
        sys.stderr.write('whalory-mcp: %s\n' % msg)
        sys.stderr.flush()
    except Exception:
        pass


def debug(msg):
    if _DEBUG[0]:
        log(msg)


# ---------------------------------------------------------------- names kept from the old product name
# Whalory was called Whalya before 3.0. The old names are read, never written:
# WHALYA_<NAME> when WHALORY_<NAME> is empty, ~/.whalya/profiles when a profile is missing
# from ~/.whalory/profiles, and the house-voice id "whalya".
LEGACY_PROFILE_IDS = {'whalya': 'whalory', 'whalya.en': 'whalory.en', 'whalya.fa': 'whalory.fa'}


def env_value(name, environ=None):
    """WHALORY_<name>, else the deprecated WHALYA_<name>; '' when neither is set."""
    environ = os.environ if environ is None else environ
    return environ.get('WHALORY_' + name) or environ.get('WHALYA_' + name) or ''


def user_profile_dirs(home=None):
    """[~/.whalory/profiles, ~/.whalya/profiles]; the second one is a read-only fallback."""
    home = os.path.expanduser('~') if home is None else home
    return [os.path.join(home, '.whalory', 'profiles'), os.path.join(home, '.whalya', 'profiles')]


class RpcError(Exception):
    def __init__(self, code, message, data=None):
        Exception.__init__(self, message)
        self.code, self.message, self.data = code, message, data


class ToolError(Exception):
    """An actionable problem shown to the model as a tool result with isError: true."""


class PathError(ToolError):
    pass


# ---------------------------------------------------------------- small helpers
def _b64(offset):
    return base64.b64encode(('o:%d' % offset).encode('ascii')).decode('ascii')


def _paginate(items, params):
    cursor = params.get('cursor')
    start = 0
    if cursor is not None:
        if not isinstance(cursor, str):
            raise RpcError(-32602, 'Invalid cursor')
        if cursor != '':
            try:
                raw = cursor.encode('ascii')
                try:
                    dec = base64.b64decode(raw, validate=True).decode('ascii')
                except Exception:
                    dec = base64.urlsafe_b64decode(raw).decode('ascii')
                if not dec.startswith('o:'):
                    raise ValueError(dec)
                start = int(dec[2:])
                if start < 0 or start > len(items) or str(start) != dec[2:]:
                    raise ValueError(dec)
            except Exception:
                raise RpcError(-32602, 'Invalid cursor')
    page = items[start:start + PAGE]
    nxt = _b64(start + PAGE) if start + PAGE < len(items) else None
    return page, nxt


def _depth_exceeds(obj, limit):
    stack = [(obj, 1)]
    while stack:
        o, d = stack.pop()
        if isinstance(o, dict):
            if d > limit:
                return True
            stack.extend((v, d + 1) for v in o.values())
        elif isinstance(o, list):
            if d > limit:
                return True
            stack.extend((v, d + 1) for v in o)
    return False


def _jsonable(o, _depth=0):
    """Plain JSON data: sets and tuples become lists, NaN and infinities become null."""
    if _depth > 200:
        return None
    if o is None or isinstance(o, (bool, str)):
        return o
    if isinstance(o, int):
        return o
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if isinstance(k, str) and k.startswith('_'):
                continue  # private keys of the linters (_path, _warnings, _span, _normalized)
            out[str(k)] = _jsonable(v, _depth + 1)
        return out
    if isinstance(o, (list, tuple, set, frozenset)):
        items = sorted(o, key=lambda x: str(x)) if isinstance(o, (set, frozenset)) else o
        return [_jsonable(v, _depth + 1) for v in items]
    return str(o)


def _compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


_HEX = set('0123456789abcdefABCDEF')


def _pct_decode(s):
    """Percent-decode once (RFC 3986); invalid escapes or UTF-8 raise ValueError."""
    if '%' not in s:
        return s
    out, i = bytearray(), 0
    while i < len(s):
        c = s[i]
        if c == '%':
            h = s[i + 1:i + 3]
            if len(h) != 2 or not all(ch in _HEX for ch in h):
                raise ValueError('bad escape')
            out.append(int(h, 16))
            i += 3
        else:
            out.extend(c.encode('utf-8'))
            i += 1
    return out.decode('utf-8')


_UNRESERVED = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~/')


def _pct_encode(s):
    out = []
    for ch in s:
        if ch in _UNRESERVED:
            out.append(ch)
        else:
            out.extend('%%%02X' % b for b in ch.encode('utf-8'))
    return ''.join(out)


def _read_text(path, limit=MAX_FILE):
    try:
        size = os.path.getsize(path)
    except OSError:
        raise ToolError('Cannot read the file.')
    if size > limit:
        raise ToolError('The file is %d bytes; the limit is %d bytes (2 MB).' % (size, limit))
    with open(path, 'rb') as f:
        data = f.read(limit + 1)
    if data.startswith(b'\xef\xbb\xbf'):
        data = data[3:]
    if data[:2] in (b'\xff\xfe', b'\xfe\xff'):
        try:
            return data.decode('utf-16')
        except UnicodeDecodeError:
            pass
    return data.decode('utf-8', 'replace')


def _call(fn, *args, **kw):
    """Call fn with only the keyword arguments it accepts (feature detection across versions)."""
    import inspect
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return fn(*args, **kw)
    if any(p.kind == p.VAR_KEYWORD for p in params.values()):
        return fn(*args, **kw)
    return fn(*args, **dict((k, v) for k, v in kw.items() if k in params))


def _accepts(fn, name):
    import inspect
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False
    return name in params or any(p.kind == p.VAR_KEYWORD for p in params.values())


def _is_user_error(e):
    return type(e).__name__ == 'UserError'


# ---------------------------------------------------------------- JSON Schema subset
def _type_ok(t, v):
    if t == 'null':
        return v is None
    if t == 'boolean':
        return isinstance(v, bool)
    if t == 'integer':
        if isinstance(v, bool):
            return False
        return isinstance(v, int) or (isinstance(v, float) and math.isfinite(v) and v.is_integer())
    if t == 'number':
        if isinstance(v, bool):
            return False
        return isinstance(v, int) or (isinstance(v, float) and math.isfinite(v))
    if t == 'string':
        return isinstance(v, str)
    if t == 'object':
        return isinstance(v, dict)
    if t == 'array':
        return isinstance(v, list)
    return True


def _fmt_enum(values):
    return ', '.join(json.dumps(x, ensure_ascii=False) for x in values)


def validate(schema, v, where, errs):
    """Subset of JSON Schema 2020-12 used by Whalory's own schemas (no $ref, no network)."""
    t = schema.get('type')
    if t is not None:
        ts = t if isinstance(t, list) else [t]
        if not any(_type_ok(x, v) for x in ts):
            errs.append('%s must be %s' % (where, ' or '.join(ts)))
            return
    if 'enum' in schema and not any(v == e and type(v) is type(e) for e in schema['enum']):
        errs.append('%s must be one of: %s' % (where, _fmt_enum(schema['enum'])))
        return
    if isinstance(v, str):
        if 'minLength' in schema and len(v) < schema['minLength']:
            errs.append('%s must not be empty' % where if schema['minLength'] == 1 else
                        '%s needs at least %d characters' % (where, schema['minLength']))
        if 'maxLength' in schema and len(v) > schema['maxLength']:
            errs.append('%s is %d characters; the limit is %d' % (where, len(v), schema['maxLength']))
        if 'pattern' in schema and not re.search(schema['pattern'], v):
            errs.append('%s does not match the pattern %s' % (where, schema['pattern']))
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if 'minimum' in schema and v < schema['minimum']:
            errs.append('%s must be at least %s' % (where, schema['minimum']))
        if 'maximum' in schema and v > schema['maximum']:
            errs.append('%s must be at most %s' % (where, schema['maximum']))
        if 'exclusiveMinimum' in schema and v <= schema['exclusiveMinimum']:
            errs.append('%s must be greater than %s' % (where, schema['exclusiveMinimum']))
        if 'exclusiveMaximum' in schema and v >= schema['exclusiveMaximum']:
            errs.append('%s must be less than %s' % (where, schema['exclusiveMaximum']))
    if isinstance(v, dict):
        props = schema.get('properties') or {}
        for k in schema.get('required') or []:
            if k not in v:
                errs.append('%s.%s is required' % (where, k) if where != 'arguments' else "'%s' is required" % k)
        if schema.get('additionalProperties') is False:
            extra = sorted(k for k in v if k not in props)
            if extra:
                errs.append('unknown %s: %s (allowed: %s)' % (
                    'argument' if where == 'arguments' else 'key in %s' % where,
                    ', '.join(extra), ', '.join(sorted(props)) or 'none'))
        for k, sub in props.items():
            if k in v:
                validate(sub, v[k], "'%s'" % k if where == 'arguments' else '%s.%s' % (where, k), errs)
    if isinstance(v, list):
        if 'maxItems' in schema and len(v) > schema['maxItems']:
            errs.append('%s has %d items; the limit is %d' % (where, len(v), schema['maxItems']))
        if 'minItems' in schema and len(v) < schema['minItems']:
            errs.append('%s needs at least %d items' % (where, schema['minItems']))
        if isinstance(schema.get('items'), dict):
            for i, item in enumerate(v[:1000]):
                validate(schema['items'], item, '%s[%d]' % (where, i), errs)


def _coerce(schema, v):
    """Integer-valued floats become int where the schema says integer; defaults fill missing keys."""
    if isinstance(v, dict) and isinstance(schema.get('properties'), dict):
        out = dict(v)
        for k, sub in schema['properties'].items():
            if k in out:
                out[k] = _coerce(sub, out[k])
            elif 'default' in sub:
                out[k] = sub['default']
        return out
    t = schema.get('type')
    ts = t if isinstance(t, list) else [t]
    if 'integer' in ts and isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def _conform(schema, v):
    """Drop null values the output schema does not allow, so structuredContent validates."""
    if not isinstance(v, dict) or not isinstance(schema, dict):
        return v
    props = schema.get('properties') or {}
    out = {}
    for k, val in v.items():
        sub = props.get(k)
        if sub is None:
            out[k] = val
            continue
        t = sub.get('type')
        ts = t if isinstance(t, list) else [t]
        if val is None and t is not None and 'null' not in ts:
            continue
        if isinstance(val, dict):
            val = _conform(sub, val)
        elif isinstance(val, list) and isinstance(sub.get('items'), dict):
            val = [_conform(sub['items'], x) if isinstance(x, dict) else x for x in val]
        out[k] = val
    return out


# ---------------------------------------------------------------- Markdown helpers
_HEADING_RE = re.compile(r'^\s{0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$')
_FENCE_RE = re.compile(r'^\s{0,3}(`{3,}|~{3,})')
_TIER_MARK = re.compile(r'^\s*<!--\s*/?\s*(pro|core)\s*-->\s*$')
_ZWNJ = '\u200c'


def slug_source(t):
    t = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', t)
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = t.replace('`', '')
    t = re.sub(r'\*+', '', t)
    return t.strip()


def gh_slug(text):
    """GitHub-style heading slug that keeps the ZWNJ (same rule as build.py)."""
    import unicodedata
    out = []
    for ch in text.strip().lower():
        if ch in (' ', '-', '_', _ZWNJ):
            out.append(ch)
            continue
        cat = unicodedata.category(ch)
        if cat[0] in 'LMN' or cat == 'Pc':
            out.append(ch)
    return ''.join(out).replace(' ', '-')


def md_structure(text):
    """(lines, headings) where each heading is (line_index, level, text, slug), fences and front matter skipped."""
    lines = text.split('\n')
    lines = [ln[:-1] if ln.endswith('\r') else ln for ln in lines]
    start = 0
    if lines and lines[0].strip() == '---':
        for i in range(1, min(len(lines), 200)):
            if lines[i].strip() in ('---', '...'):
                start = i + 1
                break
    heads, seen, fence = [], {}, None
    for i in range(start, len(lines)):
        ln = lines[i]
        m = _FENCE_RE.match(ln)
        if m:
            mark = m.group(1)
            if fence is None:
                fence = mark[0]
            elif mark[0] == fence:
                fence = None
            continue
        if fence is not None:
            continue
        h = _HEADING_RE.match(ln)
        if h:
            txt = slug_source(h.group(2) or '')
            base = gh_slug(txt)
            n = seen.get(base, 0)
            seen[base] = n + 1
            heads.append((i, len(h.group(1)), txt, base if n == 0 else '%s-%d' % (base, n)))
    return lines, heads


def section_bounds(heads, k, nlines):
    """Line range of heading k: up to the next heading of the same or a higher level."""
    level = heads[k][1]
    end = nlines
    for j in range(k + 1, len(heads)):
        if heads[j][1] <= level:
            end = heads[j][0]
            break
    return heads[k][0], end


def clean_block(lines):
    out = [ln for ln in lines if not _TIER_MARK.match(ln)]
    while out and not out[-1].strip():
        out.pop()
    while out and not out[0].strip():
        out.pop(0)
    # a trailing horizontal rule separates sections in Whalory files; drop it
    while out and out[-1].strip() in ('---', '***', '___'):
        out.pop()
        while out and not out[-1].strip():
            out.pop()
    return '\n'.join(out)


def find_heading(heads, anchor):
    """Index of the heading that matches an anchor: exact slug, slug of the text, or heading text."""
    if not anchor:
        return None
    a = anchor.strip()
    if a.startswith('#'):
        a = a[1:]
    cands = [a]
    try:
        dec = _pct_decode(a)
        if dec != a:
            cands.append(dec)
    except ValueError:
        pass
    cands.append(gh_slug(a))
    for c in cands:
        for k, h in enumerate(heads):
            if h[3] == c:
                return k
    low = a.lower()
    for k, h in enumerate(heads):
        if h[2].lower() == low:
            return k
    return None


def truncate(text, max_chars):
    if len(text) <= max_chars:
        return text
    cut = text.rfind('\n', 0, max_chars)
    if cut < max_chars // 2:
        cut = max_chars
    rest = len(text) - cut
    return text[:cut].rstrip() + '\n\n[truncated: %d more chars; request a narrower anchor]' % rest


# ---------------------------------------------------------------- language detection (fallback)
_FA_LETTER = re.compile('[\u0620-\u065f\u066e-\u06d3\u06d5-\u06ef\u06fa-\u06ff\ufb50-\ufdff\ufe70-\ufefe]')
_EN_LETTER = re.compile('[A-Za-z]')
# Linear time: the e-mail branch starts only where the previous character cannot be part of an
# address, and every quantifier around the "@" is bounded (an unbounded [\w.+-]+@ is quadratic on
# a long run of letters).
_LANG_MASK = re.compile(
    r'```.*?```|`[^`\n]*`|(?:https?|ftp)://\S+|www\.\S+|(?<![\w.+-])[\w.+-]{1,64}@[\w-]{1,63}\.[\w.-]{1,190}'
    r'|\{[^{}\n]{0,80}\}|%[sd@]|%\d\$[sd@]|<[^<>\n]{1,200}>', re.S)


def detect_lang_simple(text):
    """Spec D.5 thresholds, used only when scripts/lint.py is absent."""
    t = _LANG_MASK.sub(' ', text or '')
    fa = len(_FA_LETTER.findall(t))
    en = len(_EN_LETTER.findall(t))
    total = fa + en
    if total >= 20:
        r = fa / float(total)
        if r >= 0.80:
            return 'fa'
        if r <= 0.20:
            return 'en'
        return 'mixed'
    return 'fa' if fa >= en else 'en'


# ---------------------------------------------------------------- tokens for playbook matching
_TOKEN_RE = re.compile(r'[^\W_]+', re.U)
_HARAKAT = re.compile('[\u064b-\u065f\u0670\u0640]')
_FA_DIGITS = str.maketrans('\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9'
                           '\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669',
                           '01234567890123456789')
_STOP = set('''a an the for to of and or in on at by with from my our your this that these those it its is are be
please write make create need want some me us we i you can could would should help copy text
\u06cc\u0647 \u06cc\u06a9 \u0628\u0631\u0627\u06cc \u0648\u0627\u0633\u0647 \u0627\u06cc\u0646 \u0627\u0648\u0646 \u0648 \u0631\u0627 \u0631\u0648 \u0628\u0647 \u0627\u0632 \u06a9\u0647 \u0628\u0627 \u0645\u0646 \u0645\u0627 \u062a\u0648 \u0634\u0645\u0627 \u0628\u0646\u0648\u06cc\u0633 \u0628\u0646\u0648\u06cc\u0633\u06cc\u062f \u06a9\u0646 \u06a9\u0646\u06cc\u062f \u0628\u062f\u0647 \u0628\u062f\u06cc\u062f \u0647\u0645 \u06cc\u0627 \u062f\u0631 \u0628\u0631
\u0645\u06cc \u062e\u0648\u0627\u0645 \u0645\u06cc\u062e\u0648\u0627\u0645'''.split())


def fa_norm(s):
    s = (s or '').lower()
    s = s.replace('\u064a', '\u06cc').replace('\u0649', '\u06cc').replace('\u0643', '\u06a9')
    s = s.replace('\u0629', '\u0647').replace('\u06c0', '\u0647')
    s = _HARAKAT.sub('', s)
    s = s.replace(_ZWNJ, ' ').translate(_FA_DIGITS)
    return s


def tokens(s):
    return [t for t in _TOKEN_RE.findall(fa_norm(s)) if len(t) > 1 and t not in _STOP]


def _tok_score(q, pool):
    if q in pool:
        return 1.0
    if len(q) >= 4:
        for r in pool:
            if len(r) >= 3 and (r.startswith(q) or q.startswith(r)):
                return 0.6
    return 0.0


# ---------------------------------------------------------------- path safety
_DEVICE_RE = re.compile(r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])(\..*)?$', re.I)
_DRIVE_RE = re.compile(r'^[A-Za-z]:')


class Root(object):
    def __init__(self, path, probe=True):
        # probe=False: a network share from the client's roots is taken as given, so its arrival
        # causes no name lookup or SMB traffic; a tool reaches it only when asked for a file there.
        self.real = os.path.realpath(path) if probe else os.path.normpath(path)
        self.norm = os.path.normcase(self.real)
        self.unc = self.real.startswith('\\\\') or self.real.startswith('//')


def _inside(base_norm, p_norm):
    try:
        return os.path.commonpath([base_norm, p_norm]) == base_norm
    except ValueError:  # another drive on Windows
        return False


def check_raw_path(s, unc_ok=False):
    if '\x00' in s:
        raise PathError('The path contains a NUL character.')
    if any(ord(c) < 32 for c in s):
        raise PathError('The path contains control characters.')
    if _WIN:
        body = s[2:] if _DRIVE_RE.match(s) else s
        if ':' in body:
            raise PathError('":" is not allowed after the drive letter (alternate data streams).')
        if (s.startswith('\\\\') or s.startswith('//')) and not unc_ok:
            raise PathError('Network (UNC) paths are not allowed.')
        for seg in re.split(r'[\\/]+', s):
            if seg and _DEVICE_RE.match(seg.rstrip(' .')):
                raise PathError('Device names such as CON, NUL, COM1 or LPT1 are not allowed in paths.')


def _inside_any(bases, path):
    """True when the real path of path lies inside one of the Root objects in bases."""
    if not path:
        return False
    try:
        n = os.path.normcase(os.path.realpath(path))
    except (OSError, ValueError):
        return False
    return any(_inside(b.norm, n) for b in bases)


# ---------------------------------------------------------------- allowed folders (spec G.5.1)
_PLACEHOLDER_RE = re.compile(r'\$\{|^\$[A-Za-z_]|%[A-Za-z_][A-Za-z0-9_]*%')
# Files at the top of an installed plugin, extension or MCPB bundle (skills/<name> or server/<name>).
PLUGIN_MARKERS = ('plugin.json', '.claude-plugin', '.codex-plugin', '.cursor-plugin', 'gemini-extension.json',
                  'manifest.json')


def no_roots_message(reason):
    return ('No project folder is open to this server (%s). Start the server with --root <folder> or set '
            'WHALORY_ROOTS, or use a client that shares its workspace folders (MCP roots). In Claude Desktop, '
            'add the folder under "Folders Whalory may read" in the extension settings. Whalory\'s own files '
            '(references/, profiles/, scripts/samples/) stay readable.' % (reason or 'no folder was given'))


def _roots_from(cli_roots, env_value):
    """(usable roots, whether any value was given, why none is usable) from --root and WHALORY_ROOTS."""
    raw, given = [], False
    for group in cli_roots or []:
        given = True
        raw.extend(group or [])
    if env_value and env_value.strip():
        given = True
        raw += env_value.split(os.pathsep)
    roots, seen, bad = [], set(), []
    for r in raw:
        r = (r or '').strip().strip('"')
        if not r:
            bad.append('an empty value')
            continue
        if _PLACEHOLDER_RE.search(r):
            log('ignored a root with an unexpanded placeholder')
            bad.append('a placeholder the host did not fill in')
            continue
        p = os.path.expanduser(r)
        if not os.path.isdir(p):
            log('ignored a root that is not a folder')
            bad.append('a folder that does not exist')
            continue
        root = Root(p)
        if root.norm not in seen:
            seen.add(root.norm)
            roots.append(root)
    note = None
    if given and not roots:
        note = ('no --root or WHALORY_ROOTS value is a usable folder: %s' % ', '.join(sorted(set(bad)))
                if bad else '--root was given without a folder')
    return roots, given, note


# POSIX folders the working-folder fallback never uses: nothing inside the first list, and not the
# second list's folders themselves (projects under /var/www, /opt/app or a macOS temp folder in
# /var/folders stay usable). Folders that contain the home folder, such as /home and /Users, are
# refused by the home check.
POSIX_SYSTEM_DIRS = ('/etc', '/usr', '/bin', '/sbin', '/lib', '/lib32', '/lib64', '/boot', '/proc', '/sys', '/dev',
                     '/System', '/Library', '/private/etc')
POSIX_SYSTEM_TOPS = ('/var', '/opt', '/srv', '/private', '/private/var', '/tmp', '/private/tmp', '/mnt', '/media',
                     '/Volumes', '/Applications', '/root', '/run')


def _cwd_root(skill_dir):
    """(Root, None) for a working folder that may serve as the project, or (None, reason)."""
    try:
        real = os.path.realpath(os.getcwd())
    except OSError:
        return None, 'the working folder is not available'
    n = os.path.normcase(real)
    if os.path.dirname(real) == real:
        return None, 'the server was started at the top of a drive or file system (%s)' % real
    try:
        home = os.path.normcase(os.path.realpath(os.path.expanduser('~')))
    except (OSError, ValueError):
        home = None
    if home and n == home:
        return None, 'the server was started in the home folder'
    if home and _inside(n, home):
        return None, 'the server was started in a folder that contains the home folder (%s)' % real
    if not _WIN:
        for sys_dir in POSIX_SYSTEM_DIRS:
            if _inside(sys_dir, n):
                return None, 'the server was started in a system folder (%s)' % real
        if real in POSIX_SYSTEM_TOPS:
            return None, 'the server was started in a system folder (%s)' % real
    if _WIN:
        win = os.environ.get('SystemRoot') or os.environ.get('windir')
        if win and _inside(os.path.normcase(os.path.realpath(win)), n):
            return None, 'the server was started in the Windows folder'
    skill = os.path.normcase(os.path.realpath(skill_dir))
    if _inside(skill, n):
        return None, 'the server was started in the Whalory folder, not in a project'
    if _inside(n, skill):
        parts = os.path.relpath(skill, n).replace('\\', '/').split('/')
        if len(parts) == 1 and os.path.basename(n) == 'skills':
            return None, 'the server was started in a skills folder, not in a project'
        if len(parts) == 2 and parts[0] in ('skills', 'server') and any(
                os.path.exists(os.path.join(real, m)) for m in PLUGIN_MARKERS):
            return None, ('the server was started in the folder the plugin is installed in (%s), not in a project'
                          % real)
    return Root(real), None


def _file_uri_path(uri):
    """The local path of a file:// URI from roots/list, or None (RFC 8089; no urllib, see the imports)."""
    if not isinstance(uri, str) or len(uri) > 4096 or uri[:7].lower() != 'file://':
        return None
    rest = re.split(r'[?#]', uri[7:], maxsplit=1)[0]
    host, sep, path = rest.partition('/')
    path = '/' + path if sep else ''
    try:
        host, path = _pct_decode(host), _pct_decode(path)
    except ValueError:
        return None
    if '\x00' in path or '\x00' in host or not path:
        return None
    if host and host.lower() != 'localhost':
        if not _WIN or not re.match(r'^[A-Za-z0-9._-]+$', host):
            return None
        return '\\\\' + host + path.replace('/', '\\')  # a network share
    if _WIN:
        if re.match(r'^/[A-Za-z][:|]', path):
            path = path[1] + ':' + path[3:]
        path = path.replace('/', '\\')
        if re.match(r'^[A-Za-z]:$', path):
            path += '\\'
    return path


class RootPolicy(object):
    """The project folders the file tools may read; see "Allowed folders" at the top of this file.

    current() is called by the thread that runs requests. While a roots/list request is on its
    way it waits up to ROOTS_WAIT seconds; the reading thread records the answer."""

    def __init__(self, explicit=None, given=False, note=None, cwd_root=None, cwd_note=None):
        self.explicit = list(explicit or [])
        self.given = bool(given)
        self.note = note
        self.cwd_root, self.cwd_note = cwd_root, cwd_note
        self.client = None        # [Root] once the client has answered roots/list
        self.client_note = None
        self.pending = None       # id of the roots/list request on its way
        self.ready = threading.Event()
        self.ready.set()
        self.lock = threading.Lock()

    @classmethod
    def fixed(cls, paths, note=None):
        """Exactly these folders (the worker process gets the roots that the server resolved)."""
        roots = [Root(p) for p in paths or [] if isinstance(p, str) and os.path.isdir(p)]
        return cls(roots, True, note or 'no folder was given')

    def begin_request(self, rid):
        with self.lock:
            self.pending = rid
            self.ready.clear()

    def finish_request(self, rid, roots, note=None):
        """Record the client's answer; roots None means the client gave no list (an error)."""
        with self.lock:
            if rid != self.pending:
                return False
            self.pending = None
            if roots is not None:
                self.client, self.client_note = list(roots), note
            self.ready.set()
        return True

    def current(self, wait=0.0):
        """(roots, reason): the allowed project folders, and why there are none when the list is empty."""
        if self.explicit:
            return list(self.explicit), None
        if wait > 0 and not self.ready.is_set() and not self.ready.wait(wait):
            log('the client did not answer roots/list within %g s; going on without its roots' % wait)
            self.ready.set()  # do not wait again; a late answer is still recorded
        with self.lock:
            client, cnote = self.client, self.client_note
        if client is not None:
            return list(client), (None if client else cnote or 'the client shared no workspace folders')
        if self.given:
            return [], self.note
        if self.cwd_root is not None:
            return [self.cwd_root], None
        return [], self.cwd_note


# ---------------------------------------------------------------- worker process (time limit)
class Stopped(Exception):
    """The worker gave no answer. kind: 'timeout', 'died' (killed, cancelled or crashed) or
    'unavailable' (it cannot start here; the server then runs the tool itself)."""

    def __init__(self, kind):
        Exception.__init__(self, kind)
        self.kind = kind


def _pump(stream, lines):
    try:
        for line in iter(stream.readline, b''):
            lines.put(line)
    except (OSError, ValueError):
        pass
    lines.put(None)


def _terminate(proc):
    try:
        proc.kill()
    except OSError:
        pass
    try:
        proc.wait(timeout=5)
    except Exception:
        pass
    for s in (proc.stdin, proc.stdout):
        try:
            if s is not None:
                s.close()
        except Exception:
            pass


class Worker(object):
    """A child Python process that runs WORKER_TOOLS, one call at a time.

    Some linter rules use regular expressions that can run for minutes on odd input (a long run
    without spaces, for example). A regular expression cannot be interrupted inside a Python
    process, but a process can be stopped: when a call passes the time limit or the client cancels
    it, the server kills the child, answers, and starts a new child for the next call. The child is
    this same file run with sys.executable, -B and --worker; no shell, no network, and it writes no
    files. Jobs and answers are JSON lines on its stdin and stdout."""

    START_WAIT = 20.0

    def __init__(self, skill_dir, lang, extra=None):
        exe = sys.executable
        self.cmd = [exe, '-B', os.path.realpath(__file__), '--worker', '--skill-dir', skill_dir, '--lang', lang]
        if _DEBUG[0]:
            self.cmd.append('--debug')
        self.cmd += list(extra or [])  # the test-only Hub flags, so the child sees the same Hub folder
        self.usable = bool(exe)
        self.proc = None
        self.lines = None
        self.lock = threading.Lock()
        self.seq = 0

    def _spawn_locked(self):
        import subprocess
        kw = {'stdin': subprocess.PIPE, 'stdout': subprocess.PIPE, 'close_fds': True}
        if _WIN:  # no console window when the host is a desktop app
            kw['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        proc = subprocess.Popen(self.cmd, **kw)
        lines = queue.Queue()
        t = threading.Thread(target=_pump, args=(proc.stdout, lines), name='whalory-worker-reader')
        t.daemon = True
        t.start()
        try:
            first = lines.get(timeout=self.START_WAIT)
            hello = json.loads(first.decode('ascii')) if first else None
        except (queue.Empty, ValueError, UnicodeDecodeError):
            hello = None
        if not isinstance(hello, dict) or hello.get('ready') is not True:
            _terminate(proc)
            raise Stopped('unavailable')
        self.proc, self.lines = proc, lines

    def run(self, job, limit):
        """The worker's answer to one job, a dict with value, tool_error or internal; or Stopped."""
        with self.lock:
            if self.proc is None or self.proc.poll() is not None:
                if self.proc is not None:
                    _terminate(self.proc)
                    self.proc = self.lines = None
                if not self.usable:
                    raise Stopped('unavailable')
                try:
                    self._spawn_locked()
                except (OSError, ValueError, Stopped) as e:
                    self.usable = False
                    log('the lint worker process cannot start (%s); lint and compare now run in the server '
                        'process without a time limit' % (e.kind if isinstance(e, Stopped) else type(e).__name__))
                    raise Stopped('unavailable')
            proc, lines = self.proc, self.lines
            self.seq += 1
            job = dict(job, id=self.seq, limit=limit)
        # ASCII escapes: a lone surrogate from the client's JSON ("\ud800") must not break the pipe
        data = (json.dumps(job, ensure_ascii=True, allow_nan=False, separators=(',', ':')) + '\n').encode('ascii')
        try:
            proc.stdin.write(data)
            proc.stdin.flush()
        except (OSError, ValueError):
            self.kill(proc)
            raise Stopped('died')
        deadline = time.time() + limit
        while True:
            left = deadline - time.time()
            if left <= 0:
                self.kill(proc)
                raise Stopped('timeout')
            try:
                line = lines.get(timeout=left)
            except queue.Empty:
                continue
            if line is None:
                self.kill(proc)
                raise Stopped('died')
            try:
                msg = json.loads(line.decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(msg, dict) and msg.get('id') == job['id']:
                return msg

    def kill(self, proc=None):
        """Stop the given worker process (by default the current one); the next job starts a new one."""
        with self.lock:
            if proc is None:
                proc = self.proc
            if proc is None:
                return
            if proc is self.proc:
                self.proc = self.lines = None
        _terminate(proc)

    def close(self):
        with self.lock:
            proc, self.proc, self.lines = self.proc, None, None
        if proc is None:
            return
        try:
            proc.stdin.close()  # the worker exits at the end of its input
            proc.wait(timeout=1.0)
        except Exception:
            pass
        _terminate(proc)


def serve_worker(skill_dir, lang):
    """The --worker loop: one JSON job per stdin line, one JSON answer per stdout line."""
    import faulthandler
    out = sys.stdout.buffer
    sys.stdout = sys.stderr  # anything a linter prints goes to the log, never into the answers

    def emit(obj):
        try:
            line = json.dumps(obj, ensure_ascii=True, allow_nan=False, separators=(',', ':'))
        except (TypeError, ValueError):
            line = json.dumps({'id': obj.get('id'), 'internal': 'ValueError'})
        out.write(line.encode('ascii') + b'\n')
        out.flush()
    emit({'ready': True, 'version': __version__})
    # Backstop for an orphan: if the server dies while a job runs, a watchdog thread in C (it
    # needs no GIL) ends this process some seconds after the job's time limit.
    null_fd = None
    try:
        null_fd = os.open(os.devnull, os.O_WRONLY)
    except OSError:
        pass
    srv = Server(skill_dir, RootPolicy.fixed([]), lang)
    inp = sys.stdin.buffer
    while True:
        raw = inp.readline()
        if not raw:
            return 0
        try:
            job = json.loads(raw.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            continue
        if not isinstance(job, dict):
            continue
        rid = job.get('id')
        limit = job.get('limit')
        if null_fd is not None and isinstance(limit, (int, float)) and limit > 0:
            faulthandler.dump_traceback_later(float(limit) + 15.0, exit=True, file=null_fd)
        srv.rootpolicy = RootPolicy.fixed(job.get('roots'), job.get('no_roots'))
        t = srv.tool_map.get(job.get('tool'))
        try:
            if t is None:
                raise ToolError('Unknown tool.')
            args = job.get('args') if isinstance(job.get('args'), dict) else {}
            value, side = srv.run_local(t, args, job.get('hub') is True)
            res = {'id': rid, 'value': _jsonable(value)}
            if side is not None:
                res['hub'] = _jsonable(side)  # internal: counts for the server process, never output
        except ToolError as e:
            res = {'id': rid, 'tool_error': str(e)}
        except Exception as e:
            log('worker: tool %s failed: %s' % (str(job.get('tool'))[:60], type(e).__name__))
            if _DEBUG[0]:
                import traceback
                traceback.print_exc(file=sys.stderr)
            res = {'id': rid, 'internal': type(e).__name__}
        if null_fd is not None:
            faulthandler.cancel_dump_traceback_later()
        emit(res)


# ---------------------------------------------------------------- the server
def _rid_key(rid):
    if isinstance(rid, (str, int)) and not isinstance(rid, bool):
        return (type(rid).__name__, rid)
    return None


def _reject_constant(name):
    """json.loads accepts NaN, Infinity and -Infinity, which are not JSON; they become -32700."""
    raise ValueError('%s is not valid JSON' % name)


class Server(object):
    def __init__(self, skill_dir, roots, lang='auto', out=None, time_limit=0.0, worker_extra=None):
        self.skill_dir = os.path.realpath(skill_dir)
        self.skill = Root(self.skill_dir)
        if isinstance(roots, RootPolicy):
            self.rootpolicy = roots
        else:  # a plain list of Root: exactly these folders
            self.rootpolicy = RootPolicy(list(roots or []), True, 'no folder was given')
        self.lang = lang if lang in ('fa', 'en') else 'auto'
        self.scripts_dir = HERE
        self.out = out
        self.legacy_version = None
        self.client_has_roots = False
        self.initialized = False
        self.listens = {}
        self._mods = {}
        self._cache = {}
        self.time_limit = float(time_limit or 0)
        self.worker = Worker(self.skill_dir, self.lang, worker_extra) if self.time_limit > 0 else None
        self._tls = threading.local()   # capture flag and Hub side data of the running tool call
        self._ann_state = None    # the statistics setting behind the last tools/list (None: not listed yet)
        self._ann_lock = threading.Lock()
        self._stopping = threading.Event()
        self._out_lock = threading.Lock()
        self._jobs_lock = threading.Lock()
        self._jobs = {}           # request key -> queued or running job
        self._current = None      # the job the request thread is running
        self._queue = None        # set by serve(): requests run on their own thread, in order
        self._runner = None       # ident of that thread
        self._roots_seq = 0
        self.tools = [t for t in TOOLS if self._available(t.get('needs'))]
        self.tool_map = dict((t['name'], t) for t in self.tools)
        self.prompts = [p for p in PROMPTS if os.path.isfile(self._skill_path(p['resource']))]
        self.prompt_map = dict((p['name'], p) for p in self.prompts)

    # ------------------------------------------------ capability and modules
    def _skill_path(self, res):
        """whalory resource path (skill/SKILL.md, references/x.md) to a file path."""
        head, _, rest = res.partition('/')
        if head == 'skill':
            return os.path.join(self.skill_dir, rest)
        return os.path.join(self.skill_dir, *res.split('/'))

    def _has_script(self, name):
        return os.path.isfile(os.path.join(self.scripts_dir, name + '.py'))

    @property
    def channels_dir(self):
        return os.path.join(self.skill_dir, 'data', 'channels')

    def _has_channels(self):
        d = self.channels_dir
        try:
            return os.path.isdir(d) and any(f.lower().endswith('.json') for f in os.listdir(d))
        except OSError:
            return False

    def _available(self, needs):
        if needs is None:
            return True
        if needs == 'lint':
            return self._has_script('lint') or self._has_script('lint_fa')
        if needs == 'playbooks':
            return os.path.isfile(os.path.join(self.skill_dir, 'references', 'playbooks.md'))
        if needs == 'references':
            return os.path.isdir(os.path.join(self.skill_dir, 'references'))
        if needs == 'channels':
            return self._has_channels()
        return self._has_script(needs)

    @property
    def tier(self):
        return 'pro' if any(t['name'] in PRO_TOOLS for t in self.tools) else 'core'

    def mod(self, name):
        """Import a sibling script only when that exact file exists next to this server."""
        if name in self._mods:
            return self._mods[name]
        m = None
        if self._has_script(name):
            import importlib
            if self.scripts_dir not in sys.path:
                sys.path.insert(0, self.scripts_dir)
            try:
                m = importlib.import_module(name)
                f = os.path.normcase(os.path.realpath(getattr(m, '__file__', '') or ''))
                if os.path.dirname(f) != os.path.normcase(os.path.realpath(self.scripts_dir)):
                    log('ignored module %s from another folder' % name)
                    m = None
            except (Exception, SystemExit) as e:
                log('cannot import %s: %s' % (name, type(e).__name__))
                if _DEBUG[0]:
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                m = None
        self._mods[name] = m
        return m

    def dispatcher(self):
        m = self.mod('lint') if self._has_script('lint') else None
        if m is not None and callable(getattr(m, 'lint_text', None)):
            return m
        return None

    def lint_fa(self):
        m = self.mod('lint_fa')
        if m is None:
            raise ToolError('The Whalory linter (scripts/lint_fa.py) is missing or cannot be imported.')
        return m

    def detect_lang(self, text):
        L = self.dispatcher()
        if L is not None and callable(getattr(L, 'detect_lang', None)):
            try:
                res = L.detect_lang(text)
                lang = res[0] if isinstance(res, (tuple, list)) else res
                if lang in ('fa', 'en', 'mixed'):
                    return lang
            except Exception:
                pass
        return detect_lang_simple(text)

    # ------------------------------------------------ paths
    def project_roots(self):
        """(roots, reason) for this request. Only the request thread waits for a roots/list answer."""
        wait = ROOTS_WAIT if (self._runner is not None and threading.get_ident() == self._runner) else 0.0
        return self.rootpolicy.current(wait)

    def all_bases(self, roots=None):
        if roots is None:
            roots = self.project_roots()[0]
        return list(roots) + [self.skill]

    def resolve(self, raw, want='file'):
        """A user path inside an allowed folder or the skill folder, or PathError."""
        if not isinstance(raw, str) or not raw.strip():
            raise PathError('The path is empty.')
        raw = raw.strip()
        roots, reason = self.project_roots()
        bases = self.all_bases(roots)
        check_raw_path(raw, unc_ok=any(b.unc for b in roots))
        skill_rel = False
        if os.path.isabs(raw) or raw.startswith(('/', '\\')) or _DRIVE_RE.match(raw):
            cands = [raw]
        else:
            # Relative paths start at the allowed folders. The skill folder is tried last, and only for
            # paths into its own folders, so a missing project README never resolves to Whalory's README.
            cands = [os.path.join(b.real, raw) for b in roots]
            if re.split(r'[\\/]', raw, maxsplit=1)[0] in SKILL_DIRS:
                cands.append(os.path.join(self.skill.real, raw))
                skill_rel = True
        outside, missing = False, False
        for c in cands:
            real = os.path.realpath(c)  # resolves symbolic links and junctions before the check
            nreal = os.path.normcase(real)
            if not any(_inside(b.norm, nreal) for b in bases):
                outside = True
                continue
            if want == 'file' and os.path.isfile(real):
                return real
            if want == 'dir' and os.path.isdir(real):
                return real
            missing = True
        if not roots and not (missing and skill_rel):
            raise PathError(no_roots_message(reason))
        if outside and not missing:
            raise PathError('"%s" is outside the folders this server may read. Use a path inside the project '
                            'folder (relative paths start there), or ask the user to add the folder with --root.'
                            % raw[:300])
        raise PathError('%s not found: "%s". Relative paths start at the project folder.'
                        % ('File' if want == 'file' else 'Folder', raw[:300]))

    def display_path(self, real):
        n = os.path.normcase(real)
        if _inside(self.skill.norm, n):
            return os.path.relpath(real, self.skill_dir).replace(os.sep, '/')
        return real

    # ------------------------------------------------ profiles
    _NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9._-]+)?$')

    def _auto_profile(self):
        for b in self.project_roots()[0]:
            for rel in ('voice.json', os.path.join('voice', 'voice.json'), 'VOICE.json'):
                c = os.path.join(b.real, rel)
                if os.path.isfile(c) and _inside(b.norm, os.path.normcase(os.path.realpath(c))):
                    return os.path.realpath(c)
        return None

    def _skill_named(self, name, lang=None):
        """Profile JSON inside the skill for a bare name, as (path, source) or (None, None)."""
        p = os.path.join
        sd = self.skill_dir
        cands = []
        name = LEGACY_PROFILE_IDS.get(name, name)
        if name in ('whalory', 'whalory.en', 'whalory.fa'):
            en = p(sd, 'profiles', 'whalory.en.json')
            if (name == 'whalory.en' or (name == 'whalory' and lang == 'en')) and os.path.isfile(en):
                cands.append((en, 'whalory'))
            cands.append((p(sd, 'profiles', 'whalory.json'), 'whalory'))
        if '/' in name:
            head, _, slug = name.partition('/')
            if head == 'en':
                cands.append((p(sd, 'profiles', 'starters', 'en', slug + '.json'), 'starter'))
            elif head == 'fa':
                cands.append((p(sd, 'profiles', 'starters', slug + '.json'), 'starter'))
        else:
            cands.append((p(sd, 'profiles', name + '.json'), 'skill'))
            if name.startswith('starter-en-'):
                cands.append((p(sd, 'profiles', 'starters', 'en', name[len('starter-en-'):] + '.json'), 'starter'))
            elif name.startswith('starter-'):
                cands.append((p(sd, 'profiles', 'starters', name[len('starter-'):] + '.json'), 'starter'))
            if lang == 'en':
                cands.append((p(sd, 'profiles', 'starters', 'en', name + '.json'), 'starter'))
            cands.append((p(sd, 'profiles', 'starters', name + '.json'), 'starter'))
            if lang != 'en':
                cands.append((p(sd, 'profiles', 'starters', 'en', name + '.json'), 'starter'))
            cands.append((p(sd, 'examples', name, name + '.json'), 'skill'))
        for c, src in cands:
            if os.path.basename(c).startswith('_'):
                continue
            if os.path.isfile(c) and _inside(self.skill.norm, os.path.normcase(os.path.realpath(c))):
                return os.path.realpath(c), src
        return None, None

    def profile_path(self, spec):
        """A lint profile spec to a JSON path inside the allowed folders or the skill (never the home folder)."""
        spec = spec.strip()
        if spec == 'auto':
            return self._auto_profile()
        low = spec.lower()
        if not (low.endswith('.json') or low.endswith('.md')) and self._NAME_RE.match(spec):
            path, _src = self._skill_named(spec)
            if path is None:
                raise ToolError('No profile named "%s" in this copy of Whalory. Use a starter name such as saas or '
                                'en/saas, a path to voice.json inside the project, or call profile_lookup and '
                                'pass its profile as profile_json.' % spec)
            return path
        if low.endswith('.md'):
            md = self.resolve(spec, 'file')
            for c in (md[:-3] + '.json', os.path.join(os.path.dirname(md), 'voice.json')):
                if os.path.isfile(c):
                    return self.resolve(c, 'file')
            raise ToolError('The Markdown profile has no JSON twin (%s.json or voice.json next to it); the linter '
                            'needs the JSON form.' % os.path.basename(md)[:-3])
        if not low.endswith('.json'):
            raise ToolError('profile must be a name, "auto", or a path ending in .json or .md.')
        return self.resolve(spec, 'file')

    def load_profile(self, spec=None, inline=None):
        """Raw profile dict for the linters, or None. Each linter normalizes it for its own language
        (lint-api.md: pass raw profiles, so lint_en still sees by_lang.en)."""
        if inline is not None:
            if _depth_exceeds(inline, 16):
                raise ToolError('profile_json is nested too deeply.')
            return dict(inline)
        if not spec or not spec.strip():
            return None
        path = self.profile_path(spec)
        if path is None:
            return None
        L = self.dispatcher()
        fn = getattr(L, 'load_profile', None) if L is not None else None
        if not callable(fn):
            fn = self.lint_fa().load_profile
        try:
            return fn(path)
        except Exception as e:
            if _is_user_error(e):
                raise ToolError('The profile could not be read: %s' % e)
            raise

    # ------------------------------------------------ channels for lint
    def lint_channel(self, spec):
        if not self._has_channels():
            raise ToolError('Channel limits need data/channels/, which is not in this copy of Whalory (it ships '
                            'with Whalory Pro). Call again without "channel", or check the limit in the channels '
                            'reference.')
        LF = self.lint_fa()
        chans, _warns = LF.load_channels(self.channels_dir)
        cid, _, field = spec.partition('.')
        if cid not in chans:
            ids = sorted(k for k in chans if '/' not in k)
            raise ToolError('Unknown channel "%s". Known channels: %s.' % (cid, ', '.join(ids)))
        fields = chans[cid].get('fields') if isinstance(chans[cid].get('fields'), dict) else {}
        if field and field not in fields:
            raise ToolError('Channel "%s" has no field "%s". Fields: %s.' % (cid, field, ', '.join(fields) or 'none'))
        L = self.dispatcher()
        fn = getattr(L, 'resolve_channel', None) if L is not None else None
        if not callable(fn):
            fn = LF.resolve_channel
        try:
            return _call(fn, spec, dirpath=self.channels_dir)
        except Exception as e:
            if _is_user_error(e):
                raise ToolError('Channel "%s" could not be loaded: %s' % (spec, e))
            raise

    # ------------------------------------------------ lint adapter
    def run_lint_text(self, text, lang, profile, fmt, channel, md, max_words, facts, kind=None):
        L = self.dispatcher()
        try:
            if L is not None:
                kw = {'kind': kind} if kind else {}
                res = _call(L.lint_text, text, lang=lang, profile=profile, fmt=fmt, channel=channel, md=md,
                            max_words=max_words, facts=facts, channels_dir=self.channels_dir, **kw)
                issues, stats, got = res[0], res[1], res[2] if len(res) > 2 else self.detect_lang(text)
                return issues, stats, got
            LF = self.lint_fa()
            got = lang if lang in ('fa', 'en') else self.detect_lang(text)
            if got == 'en':
                raise ToolError(EN_MISSING)
            issues, stats = LF.lint(text, md=md, max_words=max_words, profile=profile, fmt=fmt, channel=channel)
            if got == 'mixed':
                stats = dict(stats)
                stats['note'] = 'Only the Persian rules ran: scripts/lint_en.py is not in this copy of Whalory.'
            return issues, stats, got
        except ToolError:
            raise
        except Exception as e:
            if _is_user_error(e):
                raise ToolError('The linter rejected the input: %s' % e)
            raise

    def run_lint_path(self, path, lang, profile, fmt, channel, md, csv_columns, csv_key, facts):
        L = self.dispatcher()
        try:
            if L is not None and callable(getattr(L, 'lint_path', None)):
                entry = _call(L.lint_path, path, lang=lang, profile=profile, fmt=fmt, channel=channel, md=md,
                              csv_columns=csv_columns, csv_key=csv_key, facts=facts,
                              channels_dir=self.channels_dir)
                if entry.get('error'):
                    raise ToolError('The linter could not read the file: %s' % entry['error'])
                return entry.get('issues') or [], entry.get('stats') or {}, entry.get('lang') or 'fa'
            LF = self.lint_fa()
            if md is None:
                md = os.path.splitext(path)[1].lower() in MD_EXTS
            kind = LF.detect_kind(path, bool(md))
            if kind in ('text', 'md', 'html'):
                text = LF.read_text(path)
                got = lang if lang in ('fa', 'en') else self.detect_lang(text)
                if got == 'en':
                    raise ToolError(EN_MISSING)
            else:
                got = 'fa' if lang in ('auto', 'fa') else lang
                if got == 'en':
                    raise ToolError(EN_MISSING)
            issues, stats = _call(LF.lint_file, path, profile=profile, fmt=fmt, channel=channel, md=bool(md),
                                  csv_columns=csv_columns, csv_key=csv_key)
            return issues, stats, got
        except ToolError:
            raise
        except Exception as e:
            if _is_user_error(e):
                raise ToolError('The linter rejected the input: %s' % e)
            raise

    @staticmethod
    def norm_issue(x):
        def _int(v):
            return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else None
        sev = x.get('severity') or x.get('level') or 'warning'
        if sev not in ('error', 'warning'):
            sev = 'error' if str(sev).lower().startswith('err') else 'warning'
        exc = x.get('excerpt')
        if exc is None:
            exc = x.get('text')
        key = x.get('key')
        return {'line': _int(x.get('line')), 'col': _int(x.get('col')),
                'key': key if isinstance(key, str) else None,
                'rule': str(x.get('rule') or x.get('code') or 'unknown'),
                'severity': sev, 'message': str(x.get('message') or ''),
                'excerpt': str(exc or '')}

    def lint_payload(self, issues, stats, lang, strict):
        norm = [self.norm_issue(x) for x in issues or [] if isinstance(x, dict)]
        errors = sum(1 for x in norm if x['severity'] == 'error')
        warnings = len(norm) - errors
        out = {'lang': lang if lang in ('fa', 'en', 'mixed') else 'fa',
               'passed': errors == 0 and not (strict and warnings),
               'summary': {'errors': errors, 'warnings': warnings},
               'issues': norm[:MAX_ISSUES],
               'stats': _jsonable(stats if isinstance(stats, dict) else {})}
        if len(norm) > MAX_ISSUES:
            out['truncated'] = True
        return out

    # ================================================ Whalory Hub capture (Hub spec 5.2, 5.3, 5.11)
    def _capturing(self):
        return bool(getattr(self._tls, 'capture', False))

    def _collector(self):
        """hub_overlay's collector of hidden findings, or None when the overlay module is absent."""
        ho = sys.modules.get('hub_overlay')
        fn = getattr(ho, '_collecting', None) if ho is not None else None
        return fn() if callable(fn) else None

    def _with_hidden(self, fn):
        """(fn(), hidden findings): the shadow and held-out findings the linters leave out of the output."""
        ctx = self._collector() if self._capturing() else None
        if ctx is None:
            return fn(), []
        with ctx as hidden:
            res = fn()
        return res, list(hidden)

    @staticmethod
    def _ids(issues, limit=5000):
        """Only what hub_events counts: the rule id and, for phrase-list findings, the phrase id."""
        out = []
        for x in issues or []:
            if isinstance(x, dict):
                d = {'code': str(x.get('code') or x.get('rule') or '')}
                if isinstance(x.get('_pid'), str):
                    d['_pid'] = x['_pid']
                out.append(d)
        return out[:limit]

    def _words(self, text):
        tc = self.mod('textcount')
        fn = getattr(tc, 'word_count', None) if tc is not None else None
        if callable(fn):
            try:
                n = fn(text)
                if isinstance(n, int) and not isinstance(n, bool):
                    return n
            except Exception:
                pass
        return len(text.split())

    def _set_side(self, lang, fmt, text, shown, hidden, keep_text=False, words=None):
        if not self._capturing():
            return
        side = {'lang': lang, 'fmt': fmt, 'words': self._words(text) if words is None else words,
                'shown': self._ids(shown), 'hidden': self._ids(hidden)}
        if keep_text:
            side['text'] = text[:REMEMBER_MAX + 1]
        self._tls.side = side

    def run_local(self, t, args, capture=False):
        """(value, Hub side data or None) of one tool call in this process."""
        self._tls.capture, self._tls.side = bool(capture), None
        try:
            value = getattr(self, t['run'])(args)
            return value, (self._tls.side if capture else None)
        finally:
            self._tls.capture, self._tls.side = False, None

    def hub(self):
        """hub_events when this copy of Whalory ships it, else None."""
        return self.mod('hub_events') if self._has_script('hub_events') else None

    def hub_on(self):
        """hub_events.enabled(): the person turned on statistics or packets in a terminal."""
        HE = self.hub()
        if HE is None:
            return False
        try:
            return bool(HE.enabled())
        except Exception:
            return False

    def hub_after(self, name, args, side):
        """Record counts in the server process after a tool call (never raises, never shown)."""
        HE = self.hub()
        if HE is None:
            return
        try:
            if name == 'check_final':
                try:
                    profile = self.load_profile(args.get('profile'))
                except Exception:
                    profile = None
                HE.check_final_outcome(args['text'], args.get('language', 'auto'), args.get('format'),
                                       args.get('playbook'), args.get('revisions'), profile=profile)
                return
            if not isinstance(side, dict):
                return
            lang = side.get('lang')
            HE.record_lint('mcp', lang, side.get('fmt'), (side.get('shown') or [], side.get('hidden') or []),
                           side.get('words') or 0)
            text = args.get('text') if name == 'lint_text' else side.get('text')
            if isinstance(text, str) and text:
                HE.remember(text[:REMEMBER_MAX + 1], lang if lang in ('fa', 'en') else 'auto')
        except Exception as e:
            debug('hub capture skipped: %s' % type(e).__name__)

    # ================================================ tools
    def t_lint_text(self, a):
        profile = self.load_profile(a.get('profile'), a.get('profile_json'))
        channel = self.lint_channel(a['channel']) if a.get('channel') else None
        (issues, stats, got), hidden = self._with_hidden(
            lambda: self.run_lint_text(a['text'], a.get('lang', 'auto'), profile, a.get('format'), channel,
                                       bool(a.get('md')), a.get('max_words'), a.get('facts')))
        self._set_side(got, a.get('format'), a['text'], issues, hidden)
        return self.lint_payload(issues, stats, got, bool(a.get('strict')))

    def t_check_final(self, a):
        """The final lint of approved copy; hub_after() records the outcome in the server process."""
        b = {'text': a['text'], 'lang': a.get('language', 'auto'), 'md': bool(a.get('md'))}
        for k in ('format', 'channel', 'profile'):
            if a.get(k):
                b[k] = a[k]
        return self.t_lint_text(b)

    def t_lint_file(self, a):
        path = self.resolve(a['path'], 'file')
        ext = os.path.splitext(path)[1].lower()
        if ext not in LINT_EXTS:
            raise ToolError('Unsupported file type "%s". Supported: %s.' % (ext or '(none)', ', '.join(LINT_EXTS)))
        size = os.path.getsize(path)
        if size > MAX_FILE:
            raise ToolError('The file is %d bytes; the limit is 2 MB. Split it or lint a part with lint_text.' % size)
        if ext in ('.csv', '.tsv'):
            with open(path, 'rb') as f:
                if f.read().count(b'\n') > MAX_CSV_ROWS + 1:
                    raise ToolError('The file has more than %d rows. Split it into smaller files.' % MAX_CSV_ROWS)
        md = a.get('md')  # None: the linter decides from the extension
        profile = self.load_profile(a.get('profile'))
        channel = self.lint_channel(a['channel']) if a.get('channel') else None
        prose = self._prose_for_capture(path, md) if self._capturing() else None
        if prose is not None:
            # Statistics on: lint the prose through lint_text, which keeps the phrase ids that the
            # file entry of lint_path drops. The findings are the same (lint_path does exactly this).
            text, kind = prose
            (issues, stats, got), hidden = self._with_hidden(
                lambda: self.run_lint_text(text, a.get('lang', 'auto'), profile, a.get('format'), channel,
                                           kind == 'md', None, a.get('facts'), kind=kind))
            self._set_side(got, a.get('format'), text, issues, hidden, keep_text=True)
        else:
            (issues, stats, got), hidden = self._with_hidden(
                lambda: self.run_lint_path(path, a.get('lang', 'auto'), profile, a.get('format'), channel, md,
                                           a.get('csv_columns'), a.get('csv_key'), a.get('facts')))
            words = stats.get('words') if isinstance(stats, dict) else None
            self._set_side(got, a.get('format'), '', issues, hidden,
                           words=words if isinstance(words, int) and not isinstance(words, bool) else 0)
        out = self.lint_payload(issues, stats, got, False)
        out['path'] = self.display_path(path)
        return out

    def _prose_for_capture(self, path, md):
        """(text, kind) of a prose file (text, Markdown, HTML) for the capture path, else None."""
        L = self.dispatcher()
        if L is None or not callable(getattr(L, 'lint_path', None)):
            return None
        LF = self.mod('lint_fa')
        if LF is None:
            return None
        try:
            kind = LF.detect_kind(path, bool(md))
            if kind not in ('text', 'md', 'html'):
                return None
            return LF.read_text(path), kind
        except Exception:
            return None

    def t_detect_context(self, a):
        DC = self.mod('detect_context')
        if DC is None:
            raise ToolError('detect_context.py is not in this copy of Whalory.')
        roots, reason = self.project_roots()
        if a.get('dir'):
            d = self.resolve(a['dir'], 'dir')
        elif roots:
            d = roots[0].real
        else:
            raise ToolError(no_roots_message(reason))
        bases = self.all_bases(roots)
        request = a.get('request')
        # ~/.whalory/profiles is read only by profile_lookup (spec G.5), so the probe gets a home
        # folder that does not exist.
        kw = {'max_entries': a.get('max_entries', 2000), 'max_depth': a.get('max_depth', 4),
              'skill_dir': self.skill_dir, 'home': os.path.join(self.skill_dir, '.no-home')}
        if request and _accepts(DC.probe, 'request'):
            kw['request'] = request
        if _accepts(DC.probe, 'lang'):
            kw['lang'] = self.lang
        if _accepts(DC.probe, 'confine'):
            # no links or junctions to the outside, and no git root above the allowed folders
            kw['confine'] = [b.real for b in bases]
        try:
            r = _call(DC.probe, d, **kw)
        except Exception as e:
            if _is_user_error(e):
                raise ToolError('The folder could not be probed: %s' % e)
            raise
        r = self._confine_probe(_jsonable(r), bases)
        route = r.get('suggested_route') or r.get('route')
        if route not in ('repo-microcopy', 'repo-content', 'bulk-catalog', 'standard'):
            route = 'standard'
        req_lang = r.get('request_lang')
        if req_lang not in ('fa', 'en', 'mixed'):
            req_lang = self.detect_lang(request) if request else None
        summary = None
        render = getattr(DC, 'render', None)
        if callable(render) and _accepts(render, 'lang'):  # 3.0: render follows the probe's summary_lang
            try:
                summary = render(r)
            except Exception:
                summary = None
        elif callable(render) and (req_lang == 'fa' or self.lang == 'fa'):  # 2.x: Persian summary only
            try:
                summary = render(r)
            except Exception:
                summary = None
        if not isinstance(summary, str) or not summary:
            summary = self._probe_summary(r, route)
        return {'route': route, 'summary': summary, 'request_lang': req_lang, 'probe': r,
                'note': 'User profiles in ~/.whalory/profiles are not scanned here; profile_lookup reads them.'}

    @staticmethod
    def _confine_probe(r, bases):
        """A second guard (for a detect_context.py without confine): drop paths outside the bases."""
        if not isinstance(r, dict):
            return r

        def outside(p):
            if not isinstance(p, str):
                return False
            if os.path.isabs(p):
                return not _inside_any(bases, p)
            return p.replace('\\', '/').startswith('../') or p == '..'
        for k in ('learnings', 'learnings_target', 'git_root'):
            if outside(r.get(k)):
                r[k] = None
        vp = r.get('voice_profile')
        if isinstance(vp, dict):
            for k in ('chosen', 'json_twin'):
                if outside(vp.get(k)):
                    vp[k] = None
            if isinstance(vp.get('candidates'), list):
                vp['candidates'] = [c for c in vp['candidates']
                                    if not (isinstance(c, dict) and outside(c.get('path')))]
        return r

    @staticmethod
    def _probe_summary(r, route):
        locs = r.get('locale_files') or {}
        n_loc = sum(len(v) for v in locs.values()) if isinstance(locs, dict) else 0
        n_fa = len(r.get('fa_locale_files') or [])
        vp = r.get('voice_profile') or {}
        chosen = vp.get('chosen') if isinstance(vp, dict) else None
        parts = ['Probe: route %s' % route,
                 'repository: %s' % ('yes' if r.get('is_repo') else 'no'),
                 '%d locale files (%d Persian)' % (n_loc, n_fa),
                 '%d content folders' % len(r.get('content_dirs') or []),
                 '%d catalogs' % len(r.get('catalogs') or []),
                 'voice profile: %s' % (os.path.basename(chosen) if chosen else 'none found')]
        if (r.get('probe') or {}).get('truncated'):
            parts.append('scan limited by max_entries or max_depth')
        return '; '.join(parts) + '.'

    # ---------------- playbooks
    def _md(self, path):
        """Cached (lines, headings) of a Markdown file."""
        try:
            st = os.stat(path)
        except OSError:
            return None
        key = (path, st.st_mtime, st.st_size)
        hit = self._cache.get(path)
        if hit and hit[0] == key:
            return hit[1]
        val = md_structure(_read_text(path))
        self._cache[path] = (key, val)
        return val

    def _playbook_files(self):
        ref = os.path.join(self.skill_dir, 'references')
        try:
            names = sorted(n for n in os.listdir(ref) if re.match(r'^playbooks-[a-z0-9-]+\.md$', n))
        except OSError:
            names = []
        return names + ['playbooks.md']

    def _task_index(self):
        path = os.path.join(self.skill_dir, 'references', 'playbooks.md')
        st = self._md(path)
        if st is None:
            return []
        lines, heads = st
        k = None
        for i, h in enumerate(heads):
            if h[3] in ('task-index', '\u0641\u0647\u0631\u0633\u062a\u0650-\u06a9\u0627\u0631\u0647\u0627') or h[2].lower() == 'task index':
                k = i
                break
        if k is None:
            return []
        start, end = section_bounds(heads, k, len(lines))
        table = []
        for ln in lines[start + 1:end]:
            if ln.lstrip().startswith('|'):
                table.append(ln)
            elif table:
                break
        if len(table) < 3:
            return []

        def cells(ln):
            s = ln.strip()
            if s.startswith('|'):
                s = s[1:]
            if s.endswith('|') and not s.endswith('\\|'):
                s = s[:-1]
            return [c.strip() for c in re.split(r'(?<!\\)\|', s)]

        head = [c.lower() for c in cells(table[0])]

        def col(*names):
            for i, h in enumerate(head):
                for n in names:
                    if h == n or h.startswith(n):
                        return i
            return None

        c_task = col('task', '\u06a9\u0627\u0631')
        c_fa = col('signals (fa)', '\u0646\u0634\u0627\u0646\u0647')
        c_en = col('signals (en)')
        c_pb = col('playbook', '\u062f\u0633\u062a\u0648\u0631')
        if c_task is None or c_pb is None:
            return []
        rows = []
        for ln in table[2:]:
            cs = cells(ln)
            if len(cs) <= max(c_task, c_pb):
                continue
            links = re.findall(r'\[([^\]]+)\]\(([^)\s]+)\)', cs[c_pb])
            if not links:
                continue
            title, href = links[0]
            fname, _, anchor = href.partition('#')
            fname = os.path.basename(fname) or 'playbooks.md'
            try:
                anchor = _pct_decode(anchor)
            except ValueError:
                pass
            task = cs[c_task]
            sfa = cs[c_fa] if c_fa is not None and c_fa < len(cs) else ''
            sen = cs[c_en] if c_en is not None and c_en < len(cs) else ''
            rows.append({'task': task, 'file': fname, 'anchor': anchor, 'title': title,
                         'task_tokens': set(tokens(task)),
                         'tokens': set(tokens(' '.join((task, sfa, sen, title))))})
        return rows

    def _playbook_section(self, fname, anchor):
        if not re.match(r'^playbooks(-[a-z0-9-]+)?\.md$', fname):
            return None
        path = os.path.join(self.skill_dir, 'references', fname)
        st = self._md(path)
        if st is None:
            return None
        lines, heads = st
        k = find_heading(heads, anchor)
        if k is None:
            return None
        start, end = section_bounds(heads, k, len(lines))
        return heads[k][2], heads[k][3], clean_block(lines[start + 1:end])

    def t_get_playbook(self, a):
        task = a['task'].strip()
        limit = a.get('limit', 3)
        files = self._playbook_files()
        picks = []   # (file, slug, title)
        # 1) an exact anchor wins: "caption", "#caption", "playbooks-social.md#caption"
        f_hint, sep, anc = task.partition('#')
        anc = anc if sep else task
        f_hint = os.path.basename(f_hint.strip()) if sep and f_hint.strip() else None
        order = ([f_hint] if f_hint in files else []) + [f for f in files if f != f_hint]
        for fname in order:
            st = self._md(os.path.join(self.skill_dir, 'references', fname))
            if st is None:
                continue
            k = find_heading(st[1], anc)
            if k is not None and st[1][k][1] >= 2:
                picks.append((fname, st[1][k][3], st[1][k][2]))
                break
        # 2) token overlap against Task, Signals (fa), Signals (en)
        q = tokens(task)
        scored = {}
        if q:
            for idx, row in enumerate(self._task_index()):
                s = sum(_tok_score(t, row['tokens']) for t in q)
                s += 0.25 * sum(1 for t in q if t in row['task_tokens'])
                if s <= 0:
                    continue
                key = (row['file'], row['anchor'])
                if key not in scored or s > scored[key][0]:
                    scored[key] = (s, -idx, row)
        ranked = sorted(scored.values(), key=lambda x: (x[0], x[1]), reverse=True)
        for _s_, _i, row in ranked:
            sec = self._playbook_section(row['file'], row['anchor'])
            if sec is None:
                continue
            item = (row['file'], sec[1], sec[0])
            if all((p[0], p[1]) != (item[0], item[1]) for p in picks):
                picks.append(item)
            if len(picks) >= limit:
                break
        if not picks:
            names = [r['anchor'] for r in self._task_index()][:60]
            raise ToolError('No playbook matched "%s". Try a playbook anchor or other words for the task. '
                            'Anchors: %s.' % (task[:200], ', '.join(dict.fromkeys(names)) or 'none found'))
        fname, slug, _title = picks[0]
        title, slug, body = self._playbook_section(fname, slug)
        text = '# %s  (references/%s#%s)\n%s' % (title, fname, slug, body)
        text = truncate(text, PLAYBOOK_MAX_CHARS)
        if len(picks) > 1:
            text += '\n---\nOther matches: %s' % ', '.join('%s (%s)' % (p[1], p[0]) for p in picks[1:limit])
        return text

    # ---------------- reference sections
    def _ref_file(self, path):
        p = path.strip()
        if p.startswith('/') or '\\' in p or '\x00' in p:
            raise ToolError('Use a relative path such as references/router.md.')
        segs = p.split('/')
        if any(s in ('', '.', '..') for s in segs) or any(_DEVICE_RE.match(s) for s in segs):
            raise ToolError('The path may not contain empty, "." or ".." segments or device names.')
        if p in ('SKILL.md',) or p in ROOT_DOCS:
            rel, base = p, self.skill_dir
            if os.path.isfile(os.path.join(base, rel)):
                return os.path.realpath(os.path.join(base, rel)), rel
        if segs[0] in ('references', 'profiles'):
            rel = p
        elif p.startswith('data/channels/'):
            rel = p
        else:
            rel = 'references/' + p
        rsegs = rel.split('/')
        if rsegs[0] == 'data':
            base = os.path.join(self.skill_dir, 'data', 'channels')
            if len(rsegs) != 3:
                raise ToolError('Channel data files sit directly in data/channels/.')
        else:
            base = os.path.join(self.skill_dir, rsegs[0])
        full = os.path.realpath(os.path.join(self.skill_dir, *rsegs))
        if not _inside(os.path.normcase(os.path.realpath(base)), os.path.normcase(full)) or not os.path.isfile(full):
            raise ToolError('No such reference file: %s. Paths look like references/router.md, fa/craft.md, '
                            'en/prose.md, profiles/whalory.json or data/channels/social.json; resources/list has '
                            'the full list.' % rel)
        return full, rel

    def t_get_reference_section(self, a):
        full, rel = self._ref_file(a['path'])
        max_chars = a.get('max_chars', 20000)
        anchor = (a.get('anchor') or '').strip()
        if rel.lower().endswith('.json'):
            return self._json_section(full, rel, anchor, max_chars)
        lines, heads = self._md(full)
        if anchor:
            k = find_heading(heads, anchor)
            if k is None:
                slugs = [h[3] for h in heads]
                listed = ', '.join(slugs[:150]) + (' \u2026' if len(slugs) > 150 else '')
                raise ToolError('No section "%s" in %s. Anchors: %s' % (anchor[:200], rel, listed or 'none'))
            start, end = section_bounds(heads, k, len(lines))
            h = heads[k]
            body = clean_block(lines[start + 1:end])
            text = '%s %s  (%s#%s)\n%s' % ('#' * h[1], h[2], rel, h[3], body)
            return truncate(text, max_chars)
        title = next((h for h in heads if h[1] == 1), None)
        out = ['# %s  (%s)' % (title[2] if title else os.path.basename(rel), rel), '', 'Contents:']
        for h in heads:
            if h[1] in (2, 3):
                out.append('%s- %s (#%s)' % ('  ' * (h[1] - 2), h[2], h[3]))
        first = ''
        t_line = title[0] if title else -1
        next_h = next((h for h in heads if h[0] > t_line and h[1] >= 2), None)
        intro = clean_block(lines[t_line + 1:next_h[0] if next_h else len(lines)])
        if intro.strip():
            first = intro
        else:
            for k, h in enumerate(heads):
                if h[1] == 2 and h[3] not in ('contents', '\u0641\u0647\u0631\u0633\u062a', 'table-of-contents'):
                    s, e = section_bounds(heads, k, len(lines))
                    first = '## %s  (#%s)\n%s' % (h[2], h[3], clean_block(lines[s + 1:e]))
                    break
        if first:
            out += ['', '---', first]
        return truncate('\n'.join(out), max_chars)

    def _json_section(self, full, rel, anchor, max_chars):
        try:
            data = json.loads(_read_text(full))
        except ValueError:
            raise ToolError('%s is not valid JSON.' % rel)
        if anchor:
            a = anchor.lstrip('#')
            val = None
            if isinstance(data, dict):
                if a in data:
                    val = data[a]
                elif isinstance(data.get('channels'), dict) and a in data['channels']:
                    val = data['channels'][a]
            if val is None:
                keys = list(data.keys()) if isinstance(data, dict) else []
                if isinstance(data, dict) and isinstance(data.get('channels'), dict):
                    keys += list(data['channels'].keys())
                raise ToolError('No key "%s" in %s. Keys: %s' % (a[:100], rel, ', '.join(keys[:150]) or 'none'))
            text = '```json\n%s\n```' % json.dumps(val, ensure_ascii=False, indent=1)
            return truncate('%s#%s\n%s' % (rel, a, text), max_chars)
        text = '```json\n%s\n```' % json.dumps(data, ensure_ascii=False, indent=1)
        return truncate('%s\n%s' % (rel, text), max_chars)

    # ---------------- channel limits
    def _channels(self):
        d = self.channels_dir
        out = []
        try:
            files = sorted(f for f in os.listdir(d) if f.lower().endswith('.json'))
        except OSError:
            return out
        for f in files:
            try:
                data = json.loads(_read_text(os.path.join(d, f)))
            except (ToolError, ValueError):
                log('channel data unreadable: %s' % f)
                continue
            if not isinstance(data, dict) or not isinstance(data.get('channels'), dict):
                continue
            group = data.get('group') if isinstance(data.get('group'), str) else os.path.splitext(f)[0]
            for cid, c in data['channels'].items():
                if isinstance(c, dict):
                    out.append((group, cid, c))
        return out

    @staticmethod
    def _field_out(fid, fv):
        def _int(v):
            return v if isinstance(v, int) and not isinstance(v, bool) else None
        o = {'field': fid}
        for k in ('label_en', 'label_fa'):
            if isinstance(fv.get(k), str) and fv.get(k):
                o[k] = fv[k]
        for k in ('max_chars', 'visible_chars', 'max_items', 'item_max_chars'):
            o[k] = _int(fv.get(k))
        for k in ('unit', 'status', 'verified_on', 'source', 'note_en'):
            if isinstance(fv.get(k), str):
                o[k] = fv[k]
        if isinstance(fv.get('note'), str) and fv.get('note'):
            o['note_fa'] = fv['note']
        if 'unit' not in o:
            o['unit'] = 'char'
        return o

    def t_channel_limits(self, a):
        chans = self._channels()
        want = (a.get('channel') or '').strip().lower()
        field = (a.get('field') or '').strip().lower()
        region = a.get('region', 'any')
        query = fa_norm((a.get('query') or '').strip())
        limit = a.get('limit', 20)
        if '.' in want and not field:
            want, _, field = want.partition('.')
        exact = [x for x in chans if want and (x[1].lower() == want or ('%s/%s' % (x[0], x[1])).lower() == want)]
        pool = exact
        if want and not exact:
            pool = [x for x in chans if want in x[1].lower()
                    or want in str(x[2].get('name_en') or '').lower() or want in fa_norm(str(x[2].get('name_fa') or ''))]
            if not pool:
                raise ToolError('Unknown channel "%s". Known channels: %s.'
                                % (want, ', '.join(sorted(set(x[1] for x in chans)))))
        elif not want:
            pool = chans
        res = []
        for group, cid, c in pool:
            reg = c.get('region') if isinstance(c.get('region'), str) else ''
            if region != 'any' and reg != region:
                continue
            fields = c.get('fields') if isinstance(c.get('fields'), dict) else {}
            fitems = [(fid, fv) for fid, fv in fields.items() if isinstance(fv, dict)]
            if field:
                fitems = [(fid, fv) for fid, fv in fitems if fid.lower() == field]
                if not fitems:
                    if exact:
                        raise ToolError('Channel "%s" has no field "%s". Fields: %s.'
                                        % (cid, field, ', '.join(fields) or 'none'))
                    continue
            if query:
                hay = fa_norm(' '.join(str(x) for x in (
                    cid, group, c.get('name_en', ''), c.get('name_fa', ''), c.get('kind', ''), c.get('format_id', ''))
                    + tuple(fid for fid, _ in fitems)
                    + tuple(str(fv.get('label_en', '')) + ' ' + str(fv.get('label_fa', '')) for _, fv in fitems)))
                if query not in hay:
                    continue
            item = {'id': cid, 'group': group, 'region': reg or 'unknown',
                    'fields': [self._field_out(fid, fv) for fid, fv in fitems]}
            for k in ('name_en', 'name_fa', 'kind', 'format_id'):
                if isinstance(c.get(k), str) and c.get(k):
                    item[k] = c[k]
            res.append(item)
        return {'count': len(res[:limit]), 'total': len(res), 'channels': res[:limit]}

    # ---------------- compare
    @staticmethod
    def _strs(items):
        out = []
        for x in items or []:
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, dict):
                v = x.get('text') or x.get('value') or x.get('marker') or x.get('after') or x.get('before')
                out.append(str(v) if v is not None else _compact(_jsonable(x)))
            else:
                out.append(str(x))
        return out

    def t_compare_texts(self, a):
        CM = self.mod('compare')
        if CM is None or not callable(getattr(CM, 'compare_texts', None)):
            raise ToolError('compare.py is not in this copy of Whalory.')
        profile = self.load_profile(a.get('profile'))
        try:
            res = _call(CM.compare_texts, a['before'], a['after'], profile=profile, fmt=a.get('format'), md=False,
                        strict=bool(a.get('strict')), lang=a.get('lang', 'auto'))
        except Exception as e:
            if _is_user_error(e):
                raise ToolError('compare_texts rejected the input: %s' % e)
            raise
        res = res if isinstance(res, dict) else {}
        if 'verdict' in res:  # the 3.0 result shape (WP-10)
            out = {'verdict': 'review' if res.get('verdict') == 'review' else 'ok'}
            for side in ('added', 'removed'):
                src = res.get(side) if isinstance(res.get(side), dict) else {}
                out[side] = dict((k, self._strs(v) if isinstance(v, list) else _jsonable(v)) for k, v in src.items())
            out['dropped_conditions'] = self._strs(res.get('dropped_conditions'))
            for k in ('lint_before', 'lint_after'):
                if isinstance(res.get(k), dict):
                    out[k] = _jsonable(res[k])
            out['notes'] = self._strs(res.get('notes'))
            for k in ('lang_before', 'lang_after'):
                if isinstance(res.get(k), str):
                    out[k] = res[k]
            for k, v in res.items():
                if k not in out and not k.startswith('_'):
                    out[k] = _jsonable(v)
        else:  # the 2.x result shape
            f = res.get('facts') or {}

            def pick(group, side):
                return self._strs(((f.get(group) or {}).get(side)) or [])
            out = {'verdict': 'review' if res.get('needs_check') else 'ok',
                   'added': {'numbers': pick('numbers', 'added'), 'names': pick('names', 'added'),
                             'quotes': pick('quoted', 'added')},
                   'removed': {'numbers': pick('numbers', 'removed'), 'names': pick('names', 'removed'),
                               'quotes': pick('quoted', 'removed')},
                   'dropped_conditions': pick('conditions', 'removed'),
                   'notes': self._strs(res.get('reasons'))}
            if f.get('currency'):
                out['currency'] = _jsonable(f['currency'])
            m = dict((x.get('key'), x) for x in res.get('metrics') or [] if isinstance(x, dict))
            if m:
                out['lint_before'] = dict((k, v.get('before')) for k, v in m.items())
                out['lint_after'] = dict((k, v.get('after')) for k, v in m.items())
            out['lang_before'] = self.detect_lang(a['before'])
            out['lang_after'] = self.detect_lang(a['after'])
        return out

    # ---------------- A/B
    def t_ab_test_size(self, a):
        AB = self.mod('ab_calc')
        if AB is None:
            raise ToolError('ab_calc.py is not in this copy of Whalory.')
        k = a.get('variants', 2)
        comparisons = k - 1
        alpha = a.get('alpha', 0.05)
        alpha_adj = alpha / comparisons if comparisons > 1 else alpha
        try:
            if a['mode'] == 'size':
                miss = [x for x in ('base_rate', 'mde') if x not in a]
                if miss:
                    raise ToolError('mode "size" needs %s. Rates are fractions: 0.03 means 3%%.' % ' and '.join(miss))
                base, mde = float(a['base_rate']), float(a['mde'])
                target = base + mde if a.get('mde_type') == 'absolute' else base * (1 + mde)
                if not 0 < target < 1:
                    raise ToolError('base_rate %.4g with this mde gives a target rate of %.4g, outside 0 to 1. '
                                    'Use a smaller mde, or mde_type "absolute".' % (base, target))
                if callable(getattr(AB, 'compute_size', None)):
                    return AB.compute_size(base, mde, a.get('mde_type', 'relative'), alpha, a.get('power', 0.8), k,
                                           a.get('daily_traffic'), bool(a.get('one_sided')))
                n = int(AB.sample_size(base, target, alpha_adj, a.get('power', 0.8), not a.get('one_sided')))
                total = n * k
                daily = a.get('daily_traffic')
                return {'mode': 'size', 'per_variant': n, 'total': total,
                        'days': int(math.ceil(total / float(daily))) if daily else None,
                        'p1': base, 'p2': target, 'variants': k, 'alpha_adjusted': alpha_adj,
                        'two_sided': not a.get('one_sided')}
            miss = [x for x in ('a', 'b') if x not in a]
            if miss:
                raise ToolError('mode "test" needs a and b, each {"successes": n, "total": n}.')
            x1, n1 = a['a']['successes'], a['a']['total']
            x2, n2 = a['b']['successes'], a['b']['total']
            if x1 > n1 or x2 > n2:
                raise ToolError('successes cannot be larger than total.')
            if callable(getattr(AB, 'compute_test', None)):
                out = AB.compute_test(a['a'], a['b'], alpha, k)
                out['two_sided'] = True
                return out
            r = AB.two_prop_test(x1, n1, x2, n2, alpha_adj)
            out = {'mode': 'test', 'p_a': r['p1'], 'p_b': r['p2'], 'lift_abs': r['diff'], 'z': r['z'],
                   'p_value': r['p_value'], 'significant': bool(r['p_value'] < alpha_adj),
                   'ci_low': r['ci'][0], 'ci_high': r['ci'][1], 'alpha_adjusted': alpha_adj, 'variants': k,
                   'two_sided': True}
            if r.get('lift') is not None:
                out['lift_rel'] = r['lift']
            if min(x1, n1 - x1, x2, n2 - x2) < 5:
                out['note'] = 'Fewer than 5 successes or failures in a group: the z-test is approximate.'
            return out
        except ToolError:
            raise
        except Exception as e:
            if _is_user_error(e):
                raise ToolError('The inputs do not give a valid test: %s' % e)
            raise

    # ---------------- profile lookup
    def _profile_doc(self, path, warnings):
        try:
            data = json.loads(_read_text(path))
        except (ToolError, ValueError) as e:
            warnings.append('%s is not valid JSON (%s).' % (os.path.basename(path), e))
            return None
        if not isinstance(data, dict):
            warnings.append('%s is not a JSON object.' % os.path.basename(path))
            return None
        LF = self.mod('lint_fa')
        if LF is not None:
            try:
                data = LF.normalize_profile(data)
                for w in data.get('_warnings') or []:
                    warnings.append('%s: %s' % tuple(w) if isinstance(w, (list, tuple)) and len(w) == 2 else str(w))
            except Exception as e:
                warnings.append('The profile could not be normalized (%s).' % type(e).__name__)
        return _jsonable(data)

    def _learnings(self, cands, bases):
        """The first learnings note among cands whose real path is inside bases (links that lead
        outside are skipped, like every other file this server reads)."""
        for c in cands:
            if c and os.path.isfile(c) and _inside_any(bases, c):
                try:
                    txt = _read_text(c, 256 * 1024)
                except ToolError:
                    continue
                if len(txt) > 20000:
                    txt = txt[:20000] + '\n[truncated]'
                return {'path': self.display_path(os.path.realpath(c)), 'text': txt}
        return None

    def _starters(self, lang, industry):
        out = []
        base = os.path.join(self.skill_dir, 'profiles', 'starters')
        for sub, lg in (('', 'fa'), ('en', 'en')):
            d = os.path.join(base, sub) if sub else base
            try:
                names = sorted(n for n in os.listdir(d) if n.endswith('.json') and not n.startswith('_'))
            except OSError:
                continue
            for n in names:
                p = os.path.join(d, n)
                ind, language = '', lg
                try:
                    data = json.loads(_read_text(p, 256 * 1024))
                    if isinstance(data, dict):
                        ind = data.get('industry') if isinstance(data.get('industry'), str) else ''
                        if data.get('language') in ('fa', 'en', 'bilingual'):
                            language = data['language']
                except (ToolError, ValueError):
                    pass
                out.append({'slug': n[:-5], 'language': language, 'path': self.display_path(os.path.realpath(p)),
                            'industry': ind or n[:-5]})
        if lang in ('fa', 'en'):
            out = [s for s in out if s['language'] in (lang, 'bilingual')]
        if industry:
            out.sort(key=lambda s: (0 if industry in (s['industry'].lower(), s['slug']) else 1))
        return out[:40]

    def t_profile_lookup(self, a):
        warnings = []
        name = (a.get('name') or '').strip()
        lang = a.get('language') or (self.lang if self.lang in ('fa', 'en') else None)
        industry = (a.get('industry') or '').strip().lower()
        learn = a.get('include_learnings', True)
        if name and not self._NAME_RE.match(name):
            raise ToolError('name may use letters, digits, ".", "_" and "-", with one "/" for a language '
                            'folder (for example saas or en/saas).')
        name = LEGACY_PROFILE_IDS.get(name, name)
        res = None
        # 1) the project: VOICE.md, voice.json, voice/VOICE.md. Every candidate, the voice/ folder
        # and LEARNINGS.md must stay inside the allowed folders after links and junctions resolve.
        roots, reason = self.project_roots()
        bases = self.all_bases(roots)
        if a.get('project_dir'):
            pdir = self.resolve(a['project_dir'], 'dir')
        elif roots:
            pdir = roots[0].real
        else:
            pdir = None
            warnings.append('The project folder was not checked: no project folder is open to this server (%s).'
                            % (reason or 'no folder was given'))

        def usable(p):
            return os.path.isfile(p) and _inside_any(bases, p)
        for sub in ('', 'voice') if pdir else ():
            d = os.path.join(pdir, sub) if sub else pdir
            if sub and not (os.path.isdir(d) and _inside_any(bases, d)):
                continue
            md = next((os.path.join(d, n) for n in ('VOICE.md', 'voice.md') if usable(os.path.join(d, n))), None)
            js = next((os.path.join(d, n) for n in ('voice.json', 'VOICE.json') if usable(os.path.join(d, n))), None)
            if md or js:
                res = {'found': True, 'source': 'project', 'is_brand_profile': True,
                       'path': os.path.realpath(js) if js else None,
                       'markdown_path': os.path.realpath(md) if md else None,
                       'profile': self._profile_doc(js, warnings) if js else None,
                       '_learn': [os.path.join(d, 'LEARNINGS.md')], '_bases': bases}
                if not js:
                    warnings.append('VOICE.md has no voice.json twin; lint_text needs the JSON form.')
                break
        # 2) ~/.whalory/profiles/<name>, else the old ~/.whalya/profiles/<name> (both read only here)
        for udir in user_profile_dirs() if res is None and name and '/' not in name else ():
            if os.path.isdir(udir):
                ubase = [Root(udir)]
                js, md = os.path.join(udir, name + '.json'), os.path.join(udir, name + '.md')
                js = js if os.path.isfile(js) and _inside_any(ubase, js) else None
                md = md if os.path.isfile(md) and _inside_any(ubase, md) else None
                if js or md:
                    res = {'found': True, 'source': 'user', 'is_brand_profile': True,
                           'path': os.path.realpath(js) if js else None,
                           'markdown_path': os.path.realpath(md) if md else None,
                           'profile': self._profile_doc(js, warnings) if js else None,
                           '_learn': [os.path.join(udir, name + '.LEARNINGS.md')], '_bases': ubase}
                    if not js:
                        warnings.append('%s.md has no %s.json twin; lint_text needs the JSON form.' % (name, name))
                    if os.path.basename(os.path.dirname(udir)) == '.whalya':
                        warnings.append('Read from the old folder ~/.whalya/profiles. Move the profile to '
                                        '~/.whalory/profiles; Whalory never writes to the old folder.')
                    break
        # 3) the skill's own profiles, 5) a starter by name, 6) Whalory's own voice
        if res is None and name:
            path, src = self._skill_named(name, lang)
            if path:
                md = path[:-5] + '.md'
                res = {'found': True, 'source': src, 'is_brand_profile': src == 'skill',
                       'path': self.display_path(path),
                       'markdown_path': self.display_path(md) if os.path.isfile(md) else None,
                       'profile': self._profile_doc(path, warnings), '_learn': []}
                if src == 'starter':
                    warnings.append('This is a starter profile, not the brand\'s own voice. Say so in the note.')
            else:
                warnings.append('No profile named "%s" in the project, ~/.whalory/profiles or the skill.' % name)
        # 5) the closest starter by industry
        if res is None and industry:
            for s in self._starters(lang, industry):
                if industry in (s['industry'].lower(), s['slug']):
                    full = os.path.join(self.skill_dir, *s['path'].split('/'))
                    md = full[:-5] + '.md'
                    res = {'found': True, 'source': 'starter', 'is_brand_profile': False, 'path': s['path'],
                           'markdown_path': self.display_path(os.path.realpath(md)) if os.path.isfile(md) else None,
                           'profile': self._profile_doc(full, warnings), '_learn': []}
                    warnings.append('This is a starter profile, not the brand\'s own voice. Say so in the note.')
                    break
        if res is None:
            res = {'found': False, 'source': 'none', 'is_brand_profile': False, 'path': None,
                   'markdown_path': None, 'profile': None, '_learn': []}
            warnings.append('No voice profile found. Use a starter below, build one with the voice prompt, or '
                            'write with the defaults and say so in the note.')
        cands = res.pop('_learn')
        lbases = res.pop('_bases', [])
        res['learnings'] = self._learnings(cands, lbases) if learn else None
        res['warnings'] = warnings
        res['starters'] = self._starters(lang, industry)
        return res

    # ================================================ protocol handlers
    def tool_defs(self, legacy_old=False):
        on = any(t['name'] in HUB_TOOLS for t in self.tools) and self.hub_on()
        with self._ann_lock:
            self._ann_state = on
        out = []
        for t in self.tools:
            ann = RECORDING if on and t['name'] in HUB_TOOLS else READ_ONLY
            d = {'name': t['name'], 'title': t['title'], 'description': t['description'],
                 'inputSchema': t['inputSchema'], 'annotations': dict(ann)}
            if 'outputSchema' in t and not legacy_old:
                d['outputSchema'] = t['outputSchema']
            if '_meta' in t:
                d['_meta'] = dict(t['_meta'])
            out.append(d)
        return out

    def call_tool(self, params, legacy_old=False):
        name = params.get('name')
        if not isinstance(name, str) or not name:
            raise RpcError(-32602, 'Invalid params: "name" (string) is required')
        t = self.tool_map.get(name)
        if t is None:
            raise RpcError(-32602, 'Unknown tool: %s' % name[:100])
        args = params.get('arguments')
        if args is None:
            args = {}
        if not isinstance(args, dict):
            raise RpcError(-32602, 'Invalid params: "arguments" must be an object')
        try:
            size = len(json.dumps(args, ensure_ascii=False))
        except (TypeError, ValueError):
            size = MAX_ARGS + 1
        if size > MAX_ARGS:
            return self._tool_error('The arguments are %d bytes; the limit is 1 MB.' % size)
        errs = []
        validate(t['inputSchema'], args, 'arguments', errs)
        if errs:
            return self._tool_error('Invalid arguments for %s: %s.' % (name, '; '.join(errs[:8])))
        args = _coerce(t['inputSchema'], args)
        t0 = time.time()
        try:
            value = self._run_tool(t, args)
        except ToolError as e:
            return self._tool_error(str(e))
        except Exception as e:
            log('tool %s failed: %s' % (name, type(e).__name__))
            if _DEBUG[0]:
                import traceback
                traceback.print_exc(file=sys.stderr)
            return self._tool_error('%s hit an internal error (%s). The details are in the server log.'
                                    % (name, type(e).__name__))
        debug('tool %s took %.0f ms' % (name, (time.time() - t0) * 1000))
        if 'outputSchema' in t:
            sc = _conform(t['outputSchema'], _jsonable(value))
            errs = []
            validate(t['outputSchema'], sc, 'structuredContent', errs)
            if errs:
                log('structuredContent of %s does not match its outputSchema: %s' % (name, '; '.join(errs[:3])))
            res = {'content': [{'type': 'text', 'text': _compact(sc)}], 'isError': False}
            if not legacy_old:
                res['structuredContent'] = sc
            return res
        return {'content': [{'type': 'text', 'text': value}], 'isError': False}

    def _run_tool(self, t, args):
        """Run a tool here, or in the worker process for WORKER_TOOLS (see Worker). While Hub statistics
        are on, lint_text and lint_file bring back their counts and check_final records the outcome,
        here in the server process, after the result is built (Hub spec 5.2, 5.3)."""
        name = t['name']
        hub = name in HUB_TOOLS and self.hub_on()
        capture = hub and name in ('lint_text', 'lint_file')
        value, side = self._run_somewhere(t, args, capture)
        if hub:
            self.hub_after(name, args, side)
        if name in HUB_TOOLS:
            self.refresh_annotations(hub)
        return value

    def _run_somewhere(self, t, args, capture):
        name = t['name']
        w = self.worker
        if name not in WORKER_TOOLS or w is None or not w.usable:
            return self.run_local(t, args, capture)
        roots, reason = self.project_roots()
        job = {'tool': name, 'args': args, 'roots': [b.real for b in roots], 'no_roots': reason}
        if capture:
            job['hub'] = True
        try:
            msg = w.run(job, self.time_limit)
        except Stopped as s:
            if s.kind == 'timeout':
                raise ToolError('%s stopped after %g seconds, the time limit for one call. Very long lines or long '
                                'runs without spaces (pasted data, minified code, encoded text) make some rules '
                                'slow. Check a shorter part, or split the long lines.' % (name, self.time_limit))
            if s.kind == 'died':
                raise ToolError('%s stopped before it finished: the lint process ended or the call was cancelled. '
                                'Try again, or check a shorter part.' % name)
            return self.run_local(t, args, capture)  # 'unavailable': no child process here; run in-process
        if 'tool_error' in msg:
            raise ToolError(str(msg['tool_error']))
        if 'internal' in msg:
            raise ToolError('%s hit an internal error (%s). The details are in the server log.'
                            % (name, str(msg['internal'])[:60]))
        side = msg.get('hub') if capture and isinstance(msg.get('hub'), dict) else None
        return msg.get('value'), side

    # ---------------- annotations that follow the statistics setting (Hub spec 5.11)
    def refresh_annotations(self, on=None):
        """Send tools/list_changed when the statistics setting changed since the last tools/list."""
        if self.out is None or not any(t['name'] in HUB_TOOLS for t in self.tools):
            return
        if on is None:
            on = self.hub_on()
        with self._ann_lock:
            if self._ann_state is None or self._ann_state == on:
                return
            self._ann_state = on
        debug('statistics are now %s; tools/list_changed' % ('on' if on else 'off'))
        msgs = []
        if self.legacy_version is not None and self.initialized:
            msgs.append({'jsonrpc': '2.0', 'method': 'notifications/tools/list_changed'})
        for key, filt in list(self.listens.items()):
            if isinstance(filt, dict) and filt.get('tools'):
                msgs.append({'jsonrpc': '2.0', 'method': 'notifications/tools/list_changed',
                             'params': {'_meta': {META_SUBID: key[1]}}})
        for m in msgs:
            try:
                self.send(m)
            except (OSError, ValueError):
                return

    def _watch_hub(self):
        """While serving: look at the statistics setting now and then, so an idle session hears of it."""
        while not self._stopping.wait(HUB_POLL):
            try:
                self.refresh_annotations()
            except Exception:
                pass

    @staticmethod
    def _tool_error(msg):
        return {'content': [{'type': 'text', 'text': msg}], 'isError': True}

    def prompt_get(self, params):
        name = params.get('name')
        p = self.prompt_map.get(name) if isinstance(name, str) else None
        if p is None:
            raise RpcError(-32602, 'Unknown prompt: %s' % (str(name)[:100]))
        args = params.get('arguments') or {}
        if not isinstance(args, dict):
            raise RpcError(-32602, 'Invalid params: "arguments" must be an object')
        for k, v in args.items():
            if not isinstance(v, str):
                raise RpcError(-32602, 'Invalid params: prompt argument "%s" must be a string' % str(k)[:50])
            if len(v) > MAX_TEXT:
                raise RpcError(-32602, 'Invalid params: prompt argument "%s" is too long' % str(k)[:50])
        known = set(x['name'] for x in p['arguments'])
        for x in p['arguments']:
            if x.get('required') and not (args.get(x['name']) or '').strip():
                raise RpcError(-32602, 'Missing required argument: %s' % x['name'])
        unknown = sorted(k for k in args if k not in known)
        if unknown:
            raise RpcError(-32602, 'Unknown argument: %s' % ', '.join(unknown)[:200])
        if name == 'transcreate' and args.get('target_language', '').strip() not in ('fa', 'en'):
            raise RpcError(-32602, 'target_language must be fa or en')
        path = self._skill_path(p['resource'])
        try:
            text = _read_text(path)
        except ToolError:
            raise RpcError(-32603, 'Internal error')
        uri = 'whalory://' + _pct_encode(p['resource'])
        return {'description': p['description'],
                'messages': [
                    {'role': 'user', 'content': {'type': 'resource',
                                                 'resource': {'uri': uri, 'mimeType': MD_MIME, 'text': text}}},
                    {'role': 'user', 'content': {'type': 'text', 'text': self._prompt_text(name, args)}}]}

    def _prompt_text(self, name, a):
        def g(k, default):
            v = (a.get(k) or '').strip()
            return v if v else default
        if name == 'write':
            lang = g('language', self.lang)
            return ('Task: %s\nChannel: %s\nOutput language: %s\nVoice profile: %s\n\n'
                    'Follow the Whalory method in SKILL.md above for this task. Fill the context card silently. '
                    'Ask at most three numbered questions in one message, and only when the question gate '
                    'requires them. Load the playbook with get_playbook, draft, then run the three editing '
                    'passes. Check the draft with lint_text and fix every error. Never invent facts, quotes or '
                    'numbers; put a bracket where a detail is missing. Deliver the copy first, then a short note '
                    'that starts with "Diagnosis:".'
                    % (g('task', ''), g('channel', 'not given'), lang,
                       g('profile', 'not given; find it with profile_lookup')))
        if name == 'review':
            return ('Review only the text below as a blind editor. Use the scoring rubric in editor.md above. '
                    'Do not read earlier drafts or notes, and do not rewrite the whole text. Check it with '
                    'lint_text. Return a score table, a must-fix list of at most seven items, and at most three '
                    'line edits.\n\nChannel: %s\nLanguage: %s\n\nText:\n<<<\n%s\n>>>'
                    % (g('channel', 'not given'), g('language', 'auto'), a.get('text', '')))
        if name == 'transcreate':
            tl = a.get('target_language', '').strip()
            return ('Transcreate the text below into %s for the %s market, with transcreation.md above. Keep '
                    'every number, name, price, date and condition. Check the result with lint_text in the '
                    'target language, then with compare_texts (before is the source, after is your text). '
                    'Deliver a two-column table, then a short list of what changed and why.\n\nText:\n<<<\n%s\n>>>'
                    % ('Persian (fa)' if tl == 'fa' else 'English (en)', g('market', 'stated'), a.get('text', '')))
        samples = (a.get('samples') or '').strip()
        tail = ('Use these samples as evidence:\n<<<\n%s\n>>>' % samples if samples
                else 'No samples were given, so use the quick route with three questions.')
        return ('Build a voice profile for the brand "%s" with profile-builder.md above. %s Output VOICE.md and '
                'voice.json (schema v2). Do not invent brand facts: leave unknown fields empty and list them.'
                % (g('brand', ''), tail))

    # ---------------- resources
    def _walk(self, base, exts):
        out = []
        if not os.path.isdir(base):
            return out
        bn = os.path.normcase(os.path.realpath(base))
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith(('.', '_')) and d != '__pycache__')
            for f in sorted(filenames):
                if not f.lower().endswith(exts) or not re.match(r'^[A-Za-z0-9._-]+$', f):
                    continue
                full = os.path.join(dirpath, f)
                if not _inside(bn, os.path.normcase(os.path.realpath(full))):
                    continue
                rel = os.path.relpath(full, base).replace(os.sep, '/')
                if all(re.match(r'^[A-Za-z0-9._-]+$', s) for s in rel.split('/')):
                    out.append((rel, full))
        return out

    def resource_list(self):
        sd = self.skill_dir
        items = []

        def add(uri_path, name, full, mime):
            try:
                size = os.path.getsize(full)
            except OSError:
                return
            items.append({'uri': 'whalory://' + _pct_encode(uri_path), 'name': name, 'mimeType': mime, 'size': size})
        for doc in ['SKILL.md'] + ROOT_DOCS:
            full = os.path.join(sd, doc)
            if os.path.isfile(full):
                add('skill/' + doc, doc, full, MD_MIME)
        for rel, full in self._walk(os.path.join(sd, 'references'), ('.md',)):
            add('references/' + rel, 'references/' + rel, full, MD_MIME)
        for rel, full in self._walk(os.path.join(sd, 'profiles'), ('.md', '.json')):
            add('profiles/' + rel, 'profiles/' + rel, full, JSON_MIME if rel.endswith('.json') else MD_MIME)
        cd = self.channels_dir
        if os.path.isdir(cd):
            for f in sorted(os.listdir(cd)):
                full = os.path.join(cd, f)
                if f.endswith('.json') and os.path.isfile(full) and re.match(r'^[A-Za-z0-9._-]+$', f):
                    add('data/channels/' + f, 'data/channels/' + f, full, JSON_MIME)
        return items

    _URI_RE = re.compile(r'^([A-Za-z][A-Za-z0-9+.-]*)://([a-z]+)/(.*)$', re.S)

    def resource_path(self, uri):
        """Resolve a whalory:// URI to (file path, mime type), or None."""
        if not isinstance(uri, str) or len(uri) > 1024:
            return None
        m = self._URI_RE.match(uri)
        if not m or m.group(1).lower() != 'whalory':
            return None
        auth, rest = m.group(2), m.group(3)
        if '?' in rest or '#' in rest:
            return None
        try:
            path = _pct_decode(rest)
        except ValueError:
            return None
        if not path or not re.match(r'^[A-Za-z0-9._/-]+$', path):
            return None  # rejects backslashes, NUL, drive colons and anything unusual
        segs = path.split('/')
        if any(s in ('', '.', '..') for s in segs) or any(_DEVICE_RE.match(s) for s in segs):
            return None
        ext = os.path.splitext(segs[-1])[1].lower()
        if ext not in ('.md', '.json'):
            return None
        sd = self.skill_dir
        if auth == 'skill':
            if len(segs) != 1 or segs[0] not in ['SKILL.md'] + ROOT_DOCS:
                return None
            base, parts = sd, segs
        elif auth == 'references':
            base, parts = os.path.join(sd, 'references'), segs
        elif auth == 'profiles':
            base, parts = os.path.join(sd, 'profiles'), segs
        elif auth == 'data':
            if len(segs) != 2 or segs[0] != 'channels' or ext != '.json':
                return None
            base, parts = self.channels_dir, segs[1:]
        else:
            return None
        full = os.path.realpath(os.path.join(base, *parts))
        if not _inside(os.path.normcase(os.path.realpath(base)), os.path.normcase(full)):
            return None
        if not os.path.isfile(full) or os.path.getsize(full) > MAX_FILE:
            return None
        return full, (JSON_MIME if ext == '.json' else MD_MIME)

    def resource_read(self, params, modern):
        uri = params.get('uri')
        if not isinstance(uri, str) or not uri:
            # a request that fails the params schema; -32002 / -32602 with data.uri is for a
            # well-formed URI that names no resource
            raise RpcError(-32602, 'Invalid params: "uri" (string) is required')
        hit = self.resource_path(uri)
        if hit is None:
            raise RpcError(-32602 if modern else -32002, 'Resource not found',
                           {'uri': uri if isinstance(uri, str) and len(uri) <= 1024 else None})
        full, mime = hit
        try:
            text = _read_text(full)
        except ToolError:
            raise RpcError(-32602 if modern else -32002, 'Resource not found', {'uri': uri})
        return {'contents': [{'uri': uri, 'mimeType': mime, 'text': text}]}

    @staticmethod
    def templates():
        return [
            {'uriTemplate': 'whalory://references/{+path}', 'name': 'references',
             'title': 'Whalory references', 'description': 'Method files, fa/ and en/ craft references (.md)',
             'mimeType': MD_MIME},
            {'uriTemplate': 'whalory://profiles/{+path}', 'name': 'profiles',
             'title': 'Whalory profiles', 'description': 'Voice profile templates and starters (.md, .json)'},
        ]

    # ---------------- dispatch
    def dispatch(self, method, params, modern):
        legacy_old = (not modern) and self.legacy_version in PRE_STRUCTURED
        if method == 'tools/list':
            page, nxt = _paginate(self.tool_defs(legacy_old), params)
            res = {'tools': page}
            ttl = TTL_LONG
        elif method == 'tools/call':
            return self.call_tool(params, legacy_old)
        elif method == 'prompts/list':
            defs = [dict((k, v) for k, v in p.items() if k != 'resource') for p in self.prompts]
            page, nxt = _paginate(defs, params)
            res = {'prompts': page}
            ttl = TTL_LONG
        elif method == 'prompts/get':
            return self.prompt_get(params)
        elif method == 'resources/list':
            page, nxt = _paginate(self.resource_list(), params)
            res = {'resources': page}
            ttl = TTL_SHORT
        elif method == 'resources/read':
            res = self.resource_read(params, modern)
            if modern:
                res.update({'ttlMs': TTL_SHORT, 'cacheScope': 'public'})
            return res
        elif method == 'resources/templates/list':
            page, nxt = _paginate(self.templates(), params)
            res = {'resourceTemplates': page}
            ttl = TTL_LONG
        else:
            raise RpcError(-32601, 'Method not found')
        if nxt is not None:
            res['nextCursor'] = nxt
        if modern:
            res.update({'ttlMs': ttl, 'cacheScope': 'public'})
        return res

    def initialize(self, params):
        requested = params.get('protocolVersion')
        self.legacy_version = requested if requested in LEGACY_VERSIONS else LEGACY_DEFAULT
        caps = params.get('capabilities')
        self.client_has_roots = isinstance(caps, dict) and isinstance(caps.get('roots'), dict)
        return {'protocolVersion': self.legacy_version, 'capabilities': json.loads(json.dumps(CAPABILITIES)),
                'serverInfo': dict(SERVER_INFO), 'instructions': INSTRUCTIONS}

    # ---------------- client roots (MCP roots/list)
    def request_roots(self):
        """Ask the client for its roots. Only while serving: the answer arrives on the reading thread."""
        if self._queue is None or not self.client_has_roots or self.rootpolicy.explicit:
            return
        self._roots_seq += 1
        rid = 'whalory-roots-%d' % self._roots_seq
        self.rootpolicy.begin_request(rid)
        self.send({'jsonrpc': '2.0', 'id': rid, 'method': 'roots/list'})

    def on_response(self, msg):
        """A response from the client: the answer to roots/list, or something to ignore."""
        rid = msg.get('id')
        pol = self.rootpolicy
        if not isinstance(rid, str) or rid != pol.pending:
            return
        res = msg.get('result')
        if isinstance(res, dict) and isinstance(res.get('roots'), list):
            roots, seen, skipped = [], set(), 0
            for item in res['roots'][:MAX_CLIENT_ROOTS]:
                path = _file_uri_path(item.get('uri')) if isinstance(item, dict) else None
                unc = bool(path) and (path.startswith('\\\\') or path.startswith('//'))
                if not path or (not unc and not os.path.isdir(path)):
                    skipped += 1
                    continue
                r = Root(path, probe=not unc)
                if r.norm not in seen:
                    seen.add(r.norm)
                    roots.append(r)
            note = None
            if not roots:
                note = ("none of the client's workspace folders is a folder on this machine" if res['roots']
                        else 'the client shared no workspace folders')
            pol.finish_request(rid, roots, note)
            debug('client roots: %d usable, %d skipped' % (len(roots), skipped))
        else:
            e = msg.get('error') if isinstance(msg.get('error'), dict) else {}
            pol.finish_request(rid, None)
            log('the client did not list its roots (error %s); using the other folder sources' % e.get('code'))

    def on_notification(self, method, params):
        if method == 'notifications/cancelled':
            key = _rid_key(params.get('requestId') if isinstance(params, dict) else None)
            if key in self.listens:
                del self.listens[key]
                debug('subscription %r closed' % (key[1],))
            kill = False
            with self._jobs_lock:
                job = self._jobs.get(key) if key is not None else None
                if job is not None:
                    job['cancelled'] = True
                    kill = job is self._current and job['method'] == 'tools/call' \
                        and job['params'].get('name') in WORKER_TOOLS
            if kill and self.worker is not None:
                self.worker.kill()  # stops the running lint at once; its answer is never sent
            if job is not None:
                debug('request %r cancelled' % (key[1],))
        elif method == 'notifications/initialized':
            self.initialized = True
            self.request_roots()
        elif method == 'notifications/roots/list_changed':
            if self.initialized:
                self.request_roots()
        # anything else: nothing to do, never answered

    @staticmethod
    def _err(rid, code, message, data=None):
        e = {'code': code, 'message': message}
        if data is not None:
            e['data'] = data
        r = {'jsonrpc': '2.0', 'error': e}
        if _rid_key(rid) is not None:
            r['id'] = rid
        return [r]

    def handle(self, msg):
        """Messages to write now for one parsed input message (possibly none). While serving, most
        requests are queued instead and answered in order by the request thread."""
        if isinstance(msg, list):
            return [{'jsonrpc': '2.0', 'error': {'code': -32600, 'message': 'Invalid Request: batching is not supported'}}]
        if not isinstance(msg, dict):
            return [{'jsonrpc': '2.0', 'error': {'code': -32600, 'message': 'Invalid Request'}}]
        has_id = 'id' in msg
        rid = msg.get('id')
        valid_id = has_id and _rid_key(rid) is not None

        def err(code, message, data=None):
            return self._err(rid if valid_id else None, code, message, data)
        if msg.get('jsonrpc') != '2.0':
            return err(-32600, 'Invalid Request')
        if _depth_exceeds(msg, MAX_DEPTH):
            return err(-32600, 'Invalid Request: JSON nested deeper than %d levels' % MAX_DEPTH)
        if 'method' not in msg:
            self.on_response(msg)  # a response from the client: roots/list, or ignored
            return []
        method = msg.get('method')
        if not isinstance(method, str):
            return err(-32600, 'Invalid Request') if has_id else []
        params = msg.get('params')
        if not has_id:
            self.on_notification(method, params if isinstance(params, dict) else {})
            return []
        if not valid_id:
            return err(-32600, 'Invalid Request: id must be a string or an integer')
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return err(-32602, 'Invalid params')
        if self._queue is not None and method not in SYNC_METHODS:
            job = {'key': _rid_key(rid), 'rid': rid, 'method': method, 'params': params, 'cancelled': False}
            with self._jobs_lock:
                self._jobs[job['key']] = job
            self._queue.put(job)
            return []
        return self.answer(rid, method, params)

    def answer(self, rid, method, params):
        """The response messages for one request with a valid id and object params."""
        def err(code, message, data=None):
            return self._err(rid, code, message, data)
        meta = params.get('_meta')
        pv = meta.get(META_PV) if isinstance(meta, dict) else None
        t0 = time.time()
        out = []
        try:
            if method == 'initialize':
                result = self.initialize(params)
            elif pv is not None:
                if not isinstance(pv, str) or pv not in MODERN_VERSIONS:
                    raise RpcError(-32022, 'Unsupported protocol version',
                                   {'supported': list(MODERN_VERSIONS), 'requested': pv})
                if not isinstance(meta.get(META_CAPS), dict):
                    raise RpcError(-32602, 'Invalid params: missing _meta %s' % META_CAPS)
                if method == 'server/discover':
                    result = {'supportedVersions': list(MODERN_VERSIONS),
                              'capabilities': json.loads(json.dumps(CAPABILITIES)),
                              'instructions': INSTRUCTIONS, 'ttlMs': TTL_LONG, 'cacheScope': 'public'}
                elif method == 'subscriptions/listen':
                    want = params.get('notifications') if isinstance(params.get('notifications'), dict) else {}
                    tools = want.get('toolsListChanged') is True and any(t['name'] in HUB_TOOLS for t in self.tools)
                    if tools:
                        with self._ann_lock:
                            if self._ann_state is None:
                                self._ann_state = self.hub_on()  # the state the client is told about from now
                    self.listens[(type(rid).__name__, rid)] = {'tools': tools}
                    return [{'jsonrpc': '2.0', 'method': 'notifications/subscriptions/acknowledged',
                             'params': {'_meta': {META_SUBID: rid},
                                        'notifications': {'toolsListChanged': True} if tools else {}}}]
                elif method == 'ping':
                    result = {}
                else:
                    result = self.dispatch(method, params, True)
                result['resultType'] = 'complete'
                rmeta = result.get('_meta') if isinstance(result.get('_meta'), dict) else {}
                rmeta[META_SINFO] = dict(SERVER_INFO)
                result['_meta'] = rmeta
            elif method == 'ping':
                result = {}
            elif self.legacy_version is not None:
                result = self.dispatch(method, params, False)
            else:
                raise RpcError(-32602, 'Invalid params: send initialize first, or add _meta with the protocol '
                                       'version and client capabilities')
            out.append({'jsonrpc': '2.0', 'id': rid, 'result': result})
        except RpcError as e:
            out = err(e.code, e.message, e.data)
        except Exception as e:  # never let one request kill the loop
            log('internal error in %s: %s' % (method[:60], type(e).__name__))
            if _DEBUG[0]:
                import traceback
                traceback.print_exc(file=sys.stderr)
            out = err(-32603, 'Internal error')
        debug('%s id=%r %.0f ms' % (method[:60], rid, (time.time() - t0) * 1000))
        return out

    # ---------------- transport
    def encode(self, msg):
        try:
            line = json.dumps(msg, ensure_ascii=True, allow_nan=False, separators=(',', ':'))
        except (TypeError, ValueError) as e:
            log('response not serializable: %s' % type(e).__name__)
            line = None
        if line is not None and len(line) > MAX_RESPONSE:
            log('response of %d bytes is over the limit' % len(line))
            res = msg.get('result') if isinstance(msg, dict) else None
            if isinstance(res, dict) and 'content' in res and 'isError' in res:
                small = dict(msg)
                small['result'] = self._tool_error('The result is too large (%d bytes). Narrow the request, '
                                                   'for example with an anchor or a smaller file.' % len(line))
                return self.encode(small)
            line = None
        if line is None:
            err = {'jsonrpc': '2.0', 'error': {'code': -32603, 'message': 'Internal error'}}
            if isinstance(msg, dict) and 'id' in msg:
                err['id'] = msg['id']
            line = json.dumps(err, ensure_ascii=True, separators=(',', ':'))
        return line.encode('ascii') + b'\n'

    def send(self, msg):
        data = self.encode(msg)
        with self._out_lock:  # the reading thread and the request thread both write
            self.out.write(data)
            self.out.flush()

    def _run_requests(self):
        """The request thread: queued requests in the order they arrived; cancelled ones get no answer."""
        self._runner = threading.get_ident()
        while True:
            job = self._queue.get()
            if job is None:
                return
            with self._jobs_lock:
                if job['cancelled']:
                    if self._jobs.get(job['key']) is job:
                        del self._jobs[job['key']]
                    continue
                self._current = job
            try:
                msgs = self.answer(job['rid'], job['method'], job['params'])
            finally:
                with self._jobs_lock:
                    self._current = None
                    if self._jobs.get(job['key']) is job:
                        del self._jobs[job['key']]
            if job['cancelled']:
                continue
            try:
                for m in msgs:
                    self.send(m)
            except (OSError, ValueError):
                return  # stdout is closed; the reading thread ends the process

    def serve(self, inp):
        """Read JSON-RPC lines until EOF. ping, initialize, notifications and client responses are
        handled on this thread at once; other requests run in order on the request thread, so
        ping and notifications/cancelled work while a tool runs."""
        self._queue = queue.Queue()
        runner = threading.Thread(target=self._run_requests, name='whalory-requests')
        runner.daemon = True
        runner.start()
        if any(t['name'] in HUB_TOOLS for t in self.tools) and self._has_script('hub_events'):
            watcher = threading.Thread(target=self._watch_hub, name='whalory-hub-watch')
            watcher.daemon = True
            watcher.start()
        at_eof = False
        try:
            while True:
                raw = inp.readline(MAX_LINE + 1)
                if not raw:
                    at_eof = True
                    return 0  # EOF: the client closed stdin
                if len(raw) > MAX_LINE and not raw.endswith(b'\n'):
                    while True:  # drop the rest of the oversized line
                        chunk = inp.readline(1 << 20)
                        if not chunk or chunk.endswith(b'\n'):
                            break
                    self.send({'jsonrpc': '2.0', 'error': {'code': -32700, 'message': 'Parse error: line over 16 MB'}})
                    continue
                raw = raw.strip()
                if raw.startswith(b'\xef\xbb\xbf'):
                    raw = raw[3:].strip()
                if not raw:
                    continue
                try:
                    msg = json.loads(raw.decode('utf-8'), parse_constant=_reject_constant)
                except (ValueError, UnicodeDecodeError, RecursionError):
                    self.send({'jsonrpc': '2.0', 'error': {'code': -32700, 'message': 'Parse error'}})
                    continue
                for m in self.handle(msg):
                    self.send(m)
        finally:
            self._stopping.set()
            self._queue.put(None)
            if at_eof:
                runner.join()  # requests read before EOF still get their answers (each is time-limited)
            if self.worker is not None:
                self.worker.close()


# ---------------------------------------------------------------- command line
def build_parser():
    import argparse
    ap = argparse.ArgumentParser(prog='mcp_server.py',
                                 description='Whalory MCP server (stdio). Local tools for English and Persian copy.')
    ap.add_argument('--root', action='append', nargs='*', metavar='DIR',
                    help='folder the file tools may read; repeatable, each takes one or more folders')
    ap.add_argument('--skill-dir', metavar='DIR', help='the Whalory skill folder (default: the folder above scripts/)')
    ap.add_argument('--lang', choices=['auto', 'fa', 'en'], help='default language (default: WHALORY_LANG or auto)')
    ap.add_argument('--time-limit', type=float, metavar='SECONDS',
                    help='time limit for one lint or compare call (default: WHALORY_TIME_LIMIT or %g; 0 runs them '
                         'in the server process with no limit)' % TIME_LIMIT)
    ap.add_argument('--debug', action='store_true', help='log requests and stack traces to stderr')
    ap.add_argument('--self-check', action='store_true', help='print the tools, prompts and resources, then exit')
    ap.add_argument('--json', action='store_true', help='with --self-check: JSON output')
    ap.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)  # the child process (see Worker)
    # Test-only (Hub spec 5.10): a Hub folder inside the system temp folder; hosts never pass these.
    ap.add_argument('--test', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('--hub-home', metavar='DIR', help=argparse.SUPPRESS)
    ap.add_argument('--now', metavar='TIME', help=argparse.SUPPRESS)  # with --test: a fixed UTC clock
    ap.add_argument('--version', action='version', version='whalory-mcp %s' % __version__)
    return ap


def _configure_hub_test(hub_home, now=None):
    """--test --hub-home [--now]: point hub_events and hub_overlay at a test Hub folder inside the
    temp folder, optionally with a fixed UTC clock ('YYYY-MM-DDTHH:MM:SSZ')."""
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import hub_events
    hub_events.configure(hub_home=hub_home, test=True, now=now)  # ValueError outside the temp folder
    try:
        import hub_overlay
    except ImportError:
        return
    hub_overlay.configure(hub_home=hub_home, test=True, now=now)


def _time_limit(cli_value):
    value = cli_value
    if value is None:
        env = env_value('TIME_LIMIT').strip()
        try:
            value = float(env) if env else TIME_LIMIT
        except ValueError:
            log('ignored WHALORY_TIME_LIMIT: not a number')
            value = TIME_LIMIT
    if not math.isfinite(value) or value < 0:
        return TIME_LIMIT
    return min(value, TIME_LIMIT_MAX)


def main(argv=None):
    a = build_parser().parse_args(argv)
    _DEBUG[0] = bool(a.debug)
    skill_dir = os.path.abspath(os.path.expanduser(a.skill_dir)) if a.skill_dir else os.path.dirname(HERE)
    env_lang = env_value('LANG').strip().lower()
    lang = a.lang or (env_lang if env_lang in ('auto', 'fa', 'en') else 'auto')
    worker_extra = None
    if a.test or a.hub_home or a.now:
        if not (a.test and a.hub_home):
            log('--test and --hub-home are test flags that go together (--now needs both)')
            return 2
        try:
            _configure_hub_test(a.hub_home, a.now)
        except (ValueError, ImportError) as e:
            log('cannot use the test Hub folder: %s' % e)
            return 2
        worker_extra = ['--test', '--hub-home', a.hub_home] + (['--now', a.now] if a.now else [])
    if a.worker:
        try:
            return serve_worker(skill_dir, lang)
        except (KeyboardInterrupt, BrokenPipeError, OSError):
            return 0
    if not os.path.isfile(os.path.join(skill_dir, 'SKILL.md')):
        log('SKILL.md not found in the skill folder; some tools may be missing')
    explicit, given, note = _roots_from(a.root, env_value('ROOTS'))
    cwd_root, cwd_note = (None, None) if given else _cwd_root(skill_dir)
    if cwd_root is not None:
        cwd_note = 'implicit working-folder access is disabled; use explicit --root or client workspace roots'
    roots = RootPolicy(explicit, given, note, None, cwd_note)
    out = sys.stdout.buffer
    if a.self_check:
        srv = Server(skill_dir, roots, lang, out)
        report = {'tools': [t['name'] for t in srv.tools], 'prompts': [p['name'] for p in srv.prompts],
                  'resources': len(srv.resource_list()), 'tier': srv.tier, 'version': __version__,
                  'projectRootsConfigured': bool(explicit), 'rootPolicy': 'explicit-or-client',
                  'transport': 'stdio', 'networkTools': False}
        if a.json:
            out.write((json.dumps(report, ensure_ascii=True) + '\n').encode('ascii'))
        else:
            txt = ('Whalory MCP server %s (%s)\ntools: %s\nprompts: %s\nresources: %d\n'
                   % (__version__, report['tier'], ', '.join(report['tools']), ', '.join(report['prompts']),
                      report['resources']))
            out.write(txt.encode('utf-8'))
        out.flush()
        return 0
    if given and not explicit:
        log('%s; the working folder is not used. File tools need the client\'s roots or a valid --root.' % note)
    elif not given and cwd_root is None:
        log('no --root and %s; file tools need the client\'s roots or --root.' % cwd_note)
    # Anything a module prints by mistake goes to stderr; stdout carries JSON-RPC only.
    sys.stdout = sys.stderr
    srv = Server(skill_dir, roots, lang, out, _time_limit(a.time_limit), worker_extra)
    debug('ready: %s tier, %d tools, %d explicit root(s), time limit %g s'
          % (srv.tier, len(srv.tools), len(explicit), srv.time_limit))
    try:
        return srv.serve(sys.stdin.buffer)
    except KeyboardInterrupt:
        return 130
    except (BrokenPipeError, OSError):
        return 0


if __name__ == '__main__':
    sys.exit(main())
