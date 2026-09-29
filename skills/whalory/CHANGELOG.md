# Changelog

Every notable change to Whalory is recorded here, newest first. Open it when you get a new version or want to know since when Whalory behaves a certain way. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and version numbers follow [Semantic Versioning](https://semver.org/). The current version is in [`VERSION`](VERSION). Persian changelog: [`CHANGELOG.fa.md`](CHANGELOG.fa.md).

## [Unreleased]

Nothing yet.

## [3.0.0] - 2026-09-27

Whalya 3.0 writes business copy in English as well as Persian. The method is now written in English and serves both languages. Each language has its own craft pack. The same skill also runs as a plugin, with subagents, commands, and a local MCP (Model Context Protocol) server.

### Renamed

- The product is now Whalory, «والوری» in Persian. Whalya, «والیا», stays the name of the studio that makes it, which is also the licensor and the copyright holder. Entries written before the rename keep the old name.
- The skill, the plugin, and the MCP server are named `whalory`, and commands are `/whalory:<cmd>`. The subagents are `whalory-writer`, `whalory-editor`, `whalory-researcher`, `whalory-strategist`, `whalory-transcreator`, and `whalory-voice-keeper`. Packages are named `whalory-<edition>-<target>-<version>`, and MCP resources use `whalory://`.
- The identity files are `WHALORY.md` (in Whalory Pro) and `WHALORY.fa.md` (in Whalory Pro). The house voice is [`profiles/whalory.md`](profiles/whalory.md), and the old profile id `whalya` still finds it.
- User profiles live in `~/.whalory/profiles/`. A profile missing there is read from the old `~/.whalya/profiles/` folder, and nothing is ever written to that folder.
- License keys start with `WLR3-`, and the website is whalory.com.
- Environment variables are now `WHALORY_ROOTS`, `WHALORY_LANG`, `WHALORY_TIME_LIMIT`, `WHALORY_AUTOLINT`, `WHALORY_SCRIPTS_DIR`, and `WHALORY_DEBUG`. The old `WHALYA_*` names still work when the new variable is empty, but they're deprecated.

### Added

- English output. Whalya writes, rewrites, and reviews English copy, with US English (`en-US`) as the default and `en-GB`, `en-AU`, `en-CA`, `en-NZ`, `en-IE`, and `en-IN` available through the profile or the market.
- English pack. The new [`references/en/`](references/en/craft.md) folder holds 31 files. Eleven are in Core: craft, plain English, style guide, common errors, AI tells, occasions, claims, ethics, channels, forms, and style repair. The other 20, in Pro, cover commerce, channels, strategy, and trust. Every limit and rule carries a source and a check date, or is marked unverified.
- Transcreation. The method `transcreation.md` (in Whalory Pro) and the playbook transcreation and bilingual copy (in Whalory Pro) move copy between Persian and English with a fact lock and a two-column delivery.
- Social post. A Core playbook for text-first posts on LinkedIn, X, Threads, Bluesky, and Facebook: [social post](references/playbooks-social.md#social-post).
- Task index. A new "Signals (en)" column, plus rows for LinkedIn posts, cold outbound email, and Product Hunt launches. Listings now cover Amazon, Etsy, and eBay, as well as the App Store and Google Play.
- Linters. `scripts/lint_en.py` checks English copy: AI tells, puffery, plain English, style, readability, the brand profile, and channel limits. `scripts/lint.py` detects the language of each line and runs the right linter. `scripts/textcount.py` counts graphemes, X-weighted characters, UTF-16 units, and SMS segments.
- Voice profiles. New keys `language`, `variant`, `variants`, `spelling`, `oxford_comma`, `contractions`, `house_style`, `reading_grade_max`, and `by_lang`; `schema_version` stays 2. English templates, Whalya's own English voice, and 16 English starter profiles, two of them in Core.
- Channel data. Schema version 2 with `region`, `label_en`, and `note_en`, international channels, and new units: graphemes, weighted characters, UTF-16 units, bytes, segments, and items.
- Plugin. A Claude Code plugin with its own marketplace file. Core has the `whalya-writer` and `whalya-editor` subagents and the `write`, `review`, `voice`, and `lint` commands. Pro adds four subagents and the `campaign`, `transcreate`, and `audit` commands. A separate, opt-in autolint plugin lints content and locale files after each edit. The linter runs in a child process, which the hook stops after about 8 seconds. Its script, `scripts/hook_lint.py`, also ships in every skill package for a hook set up by hand. The Pro editor rules package has ready settings for Claude Code, Cursor, and Gemini CLI.
- More hosts. An Agent Plugins 1.0 build for Codex, Visual Studio Code with Copilot, and other hosts. It carries an `INSTALL.md` and, for Codex, a legacy `.mcp.json` and `.codex-plugin/plugin.json`. Also a Gemini CLI extension, and a Cursor plugin in Pro.
- MCP server. `scripts/mcp_server.py`, a read-only stdio server with no dependencies and no network access. It has five tools in Core and four more in Pro, four prompts, and `whalya://` resources. File tools read only the project folders given with `--root` or `WHALYA_ROOTS`, or the folders the host shares (MCP roots). Lint and compare calls stop after a time limit, 30 seconds by default. Links and junctions that lead outside the allowed folders are refused. When a folder given with `--root` or `WHALYA_ROOTS` can't be used, the server never falls back to the folder it starts in. While a tool runs, `ping` is answered and a cancel request stops the call. The server writes no files, not even Python bytecode caches. A `.mcpb` bundle installs it in Claude Desktop.
- English documents: [`GUIDE.en.md`](GUIDE.en.md), `WHALYA.md` (in Whalory Pro), [`LICENSE.en.md`](LICENSE.en.md), [`LICENSE-CORE.en.md`](LICENSE-CORE.en.md), and this changelog. [`README.en.md`](README.en.md) was rewritten as the international front door.
- Packs. English paste-in prompts in Core and Pro, and English GPT and Gem packs in Pro.
- New build gates. They check the language ratio, parity between the two packs, identifiers, and frontmatter. Others cover plugin schemas, the MCP tool list, the MCP bundle, directory readiness, and evals.
- An English version of the website under `/en/`.

### Changed

- The method is in English: the router, router examples, intake, judgment, playbooks, review, editor, brief, gathering, voice profile, profile builder, and roles. Rules, thresholds, order, and router row numbers are unchanged. Persian examples and the fixed Persian output strings stay in Persian.
- [`SKILL.md`](SKILL.md) is in English and covers both languages. Its description triggers on English and Persian requests.
- The 55 Persian craft and market files moved, unchanged, from `references/` to [`references/fa/`](references/fa/craft.md).
- Headings in the method files and `SKILL.md` have English anchors, for example `SKILL.md#profile-lookup-order`. See the migration notes.
- Router row 15 is now "Out of scope genre". It covers code and code comments, academic essays and homework, literary translation, legal drafting, and certified or word-for-word translation. It also covers fiction and verse wanted as literature for their own sake. A labeled brand story, a rhymed slogan, or an ad jingle stays in scope. English copy is no longer out of scope.
- Router row 14 is now "Transcreation or bilingual copy".
- The output language, variant, and market are decided before writing. The order is fixed: an explicit instruction; the channel or market; the supplied materials; the request language; and last the profile.
- Bilingual templates in the question gate. The English escape word is "write", and the Persian one stays «بنویس».
- `WHALYA.md` is now the English identity. The Persian one moved to `WHALYA.fa.md` (in Whalory Pro).
- `CHANGELOG.md` is now English and canonical. The Persian changelog moved to [`CHANGELOG.fa.md`](CHANGELOG.fa.md).
- The manual quality check gained an English checklist beside the Persian one, with `lint_en.py` rule ids.
- Documentation commands use `scripts/lint.py`. `lint_fa.py` keeps its flags and JSON output, reports version 3.0.0, and reads `by_lang.fa` from the profile.
- `compare.py`, `detect_context.py`, `ab_calc.py`, `profile_stats.py`, and `audit_corpus.py` handle English as well as Persian.

### Deprecated

- The `codex-plugin` build target, which uses the legacy `.codex-plugin/plugin.json` layout. It stays in 3.0 for existing Pro buyers and will be removed in 3.1. Use the Agent Plugins build or the Claude plugin instead.

### Migration notes

These notes are for Pro users and anyone with bookmarks, scripts, or CI jobs that point into Whalya.

- Paths. The 55 craft and market files moved from `references/<name>.md` to `references/fa/<name>.md`. The method files stay in `references/`.
- Anchors. Links into the method files and `SKILL.md` now use English anchors. Anchors inside `references/fa/` did not change. The most common ones:

| v2 link | v3 link |
|---|---|
| `SKILL.md#ترتیبِ-پیدا-کردنِ-پروفایل` | `SKILL.md#profile-lookup-order` |
| `SKILL.md#آزمونِ-دستی` | `SKILL.md#manual-qa` |
| `SKILL.md#اسکریپت‌ها` | `SKILL.md#scripts` |
| `references/playbooks.md#فهرستِ-کارها` | `references/playbooks.md#task-index` |
| `references/intake.md#ترتیبِ-تصمیم` | `references/intake.md#decision-order` |
| `references/router.md#یادداشتِ-تشخیص` | `references/router.md#diagnosis-note` |
| `references/playbooks-repair.md#متنِ-انگلیسی-یا-دوزبانه` | `references/playbooks-repair.md#transcreation-and-bilingual-copy` |

- Profiles. Version 2 profiles work unchanged. A profile without `language` is read as Persian (`fa`, `fa-IR`). Add `language` and `variant` to make it explicit, and `by_lang` for a bilingual brand.
- Scripts and CI. Replace `lint_fa.py` with `lint.py` to check both languages. `lint_fa.py` still runs with the same flags and output.
- File names. Look for the Persian identity in `WHALYA.fa.md` and the Persian changelog in `CHANGELOG.fa.md`.
- Codex. Move from the `codex-plugin` layout to the Agent Plugins build before 3.1.
- Python. The MCP server and the autolint hook need Python 3.8 or later. On Windows, set the Claude Code plugin's Python command with `--config python=python`. The autolint hook and the other packages run `python3`; see [Python](README.en.md#python).

## [2.0.0] - 2026-09-27

In version 2, Whalya first reads the situation, asks briefly if it must, and then writes. From this version on, Whalya comes in three editions: Core, Pro, and Studio.

### Added

- Context detection: the reference [`router.md`](references/router.md). Capability flags, the context card, the table from signals to routes, and the «تشخیص:» line at the top of the delivery note. Step "0. Detection" in `SKILL.md`.
- Question gate: the reference [`intake.md`](references/intake.md). When to ask and when not to, and at most three questions, each with a «(پیشنهادی)» (recommended) option. The word «بنویس» to write without questions, the mechanism of each assistant, a question bank for each task, and defaults. It never asks in automated runs.
- New references: [`occasions.md`](references/fa/occasions.md), `channels-ir.md` (in Whalory Pro), `sms.md` (in Whalory Pro), `marketplaces.md` (in Whalory Pro), `ads.md` (in Whalory Pro), `ux-strings.md` (in Whalory Pro), `regulation.md` (in Whalory Pro), `conversational.md` (in Whalory Pro), `video-audio.md` (in Whalory Pro), `press.md` (in Whalory Pro), `local-reviews.md` (in Whalory Pro), `business-docs.md` (in Whalory Pro), `web-pages.md` (in Whalory Pro).
- Channel data: the `data/channels/` folder with the character limit of each channel. Every number has a source and a check date, and an unverified number is labeled `unverified`.
- Voice profile version 2: the keys `schema_version` and `address`, the `jargon` and `rhetoric` dials, `formats` for a separate tone per format, and an optional `romanization` for fixed Latin spellings of names. Version 1 profiles work unchanged.
- A place for the user's profiles: `~/.whalya/profiles/<brand>.md`, outside the skill folder, so updates don't delete them.
- A learnings note next to the chosen profile: `LEARNINGS.md` in the project root next to `VOICE.md`, or `<brand>.LEARNINGS.md` next to `<brand>.md` in `~/.whalya/profiles/`. It's read in every task.
- Manual quality check: a checklist in `SKILL.md` for assistants that don't run code, with the ids of the matching `lint_fa.py` rules.
- New AI-tell rules in `lint_fa.py`: `did-you-know`, `lets`, `nowadays`, `no-secret`, `golden-tip`, `final-word`, `hope-helpful`, `emoji-bullet`, `caption-header`.
- New `lint_fa.py` options: `--format` for per-format limits, `--channel` for per-channel limits, `--text` and standard input, and reading locale files (json, po, arb, xliff, strings).
- An ignore marker in `lint_fa.py`: lines between `<!-- lint-ignore -->` and `<!-- /lint-ignore -->` are not checked. The marker only surrounds intentionally bad examples in teaching files. In `--md` mode, inline code is skipped too.
- New scripts: `detect_context.py` for a cheap folder probe, and `ab_calc.py` for A/B test sample size and significance.
- More starter profiles, all on profile version 2.
- A real example: the complete profile of a real brand moved to `examples/` and ships only in Pro.
- License and version files: [`LICENSE.md`](LICENSE.md), [`LICENSE-CORE.md`](LICENSE-CORE.md), `EULA.fa.md` (in Whalory Pro), `EULA.en.md` (in Whalory Pro), [`VERSION`](VERSION), and the changelog.
- An English front page: [`README.en.md`](README.en.md).
- Packaging: every assistant's package is built from one source. It includes the skill zip, the claude.ai zip, and paste-in prompts in three sizes. GPT and Gem packs come with instructions and knowledge files. For code editors there are a Cursor rule, Copilot instructions, `AGENTS.md` and `GEMINI.md` snippets, and a `VOICE.md` template.

### Changed

- `SKILL.md` rewritten: the method from "0. Detection" to "8. Learning", the profile lookup order, and the task table that points to the task index in [`playbooks.md`](references/playbooks.md).
- Trigger words in Persian and English were added to the skill description, along with the kinds of work Whalya won't take.
- The default sentence cap became 24 words in every file and script.
- The no-profile defaults became the same everywhere. Dials: warmth 3, formality 3, humor 1, narrative 3, and sentence length 3, which means a 24-word cap. The rest: loud marks 0, jargon 2, rhetoric 3, and «شما» address.
- Precedence of a format's tone: the command-line flag; `formats` in the profile; the format default; the profile's overall tone; and last the dial defaults. A format default only makes limits stricter and doesn't set the address; loosening is done only through `formats` in the profile.
- The SMS rule became the same in every file: the sender or brand name first with a colon, «[برند]: [پیام]». A promotional SMS ends with «لغو۱۱» on its last line. A template never starts with a variable that may be empty, such as `{name}`. The Persian word for each part of a long SMS is «پاره».
- Failed-payment copy: «پرداخت انجام نشد. اگر مبلغی از حسابتان کم شده، معمولاً تا ۷۲ ساعتِ کاری برمی‌گردد.» replaced the promise that no money was taken.
- The playbook "error, empty, and waiting states" moved to Core.
- Edition names: والیا هسته, والیا حرفه‌ای, and والیا استودیو; in Latin script Whalya Core, Whalya Pro, and Whalya Studio.
- claude.ai: skills on claude.ai need code execution, so Whalya runs its QA there with scripts.
- Codex skill path: `~/.agents/skills/` for the user and `.agents/skills/` for a repository.
- The question policy in every file points to [`intake.md`](references/intake.md) instead of a separate rule.
- The core references grew. Conventions gained a section on digital and bidirectional text, AI tells gained severities and rule ids, and review now checks the goal, ethics, and accessibility.
- `راهنما.md` was rewritten as [`GUIDE.fa.md`](GUIDE.fa.md). It covers installing on each assistant; detection and questions; and getting unstuck.
- `README.md` was rewritten with editions, install, quick start, and a folder map without fixed counts.
- The old register names in profiles (`written` and `colloquial-written`) are read as `formal` and `colloquial`, with a warning.

### Fixed

- `lint_fa.py --fix` no longer changes marks inside HTML, code, links, or English text.
- A file that starts with a byte order mark no longer breaks the scripts, and the mark isn't counted as a Persian character.
- File name patterns such as `*.txt` expand on Windows too.
- `--write` keeps the file's line endings as they were.
- A missing or unreadable file gives a readable message and exit code 2 instead of a raw error.
- Python older than 3.8 gets a clear message.
- Commands are written with the full skill path so they work from the user's folder too.
- Broken links, and contradictions between files about the number of questions and the situation questions.

### Removed

- `راهنما.md`, replaced by [`GUIDE.fa.md`](GUIDE.fa.md).
- Personal profiles and unrelated files from the publishable package.

## [1.x]

The first version, before version numbering. Its exact release date was not recorded.

- `SKILL.md` with the three rules, the five pillars, and the task-to-playbook table.
- Playbooks in `playbooks.md` and references for craft, story, hooks, persuasion, formats, channels, claims, ethics, industries, research, measurement, naming, and pitch decks.
- Voice profile with six dials, a blank template, Whalya's profile, and industry starter profiles.
- The scripts `lint_fa.py`, `compare.py`, `audit_corpus.py`, `profile_stats.py`, and `selftest.py`.
- Paste-in versions in the `portable/` folder.
