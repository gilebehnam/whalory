# Changelog

This file records the changes to Whalory Core and to this repository, newest first. The skill's own changelog has every detail, the migration notes included: [English](skills/whalory/CHANGELOG.md), [Persian](skills/whalory/CHANGELOG.fa.md). The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and version numbers follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

Nothing yet.

## [3.1.0] - 2026-10-06

The first public release. It adds the Whalory Hub, a final check of approved copy, and commands that keep a brand's lessons.

### Added

- The Whalory Hub client, `hub_client.py`. The plugins start it when a session starts, and once a day it downloads rule files that Whalory signed. It checks every signature and limit before the linters use a file, and keeps its current rules when a check fails. `hub_client.py off updates` or `WHALORY_HUB_UPDATES=0` turns updates off. [PRIVACY.md](PRIVACY.md) lists every switch.
- Rule statistics and the weekly packet. Both ship switched off and closed, so nothing is collected. When Whalory opens them with a signed setting, only a person at a console can turn one on.
- `check_final`, an MCP tool for the final lint of approved copy. Core now has six MCP tools.
- The `learn` and `lessons` commands, which save, list, prune, and export a brand's lessons after you say yes. The `hub` and `feedback` commands show the Hub status and the week's packet.
- A written quality loop: lint, a blind editor pass, and at most two revision rounds before delivery.
- `lint.py --no-overlay`, and the variables `WHALORY_HUB_OVERLAY=0` and `WHALORY_HUB=0`.

### Changed

- The linters take extra phrases, severities, and thresholds from a verified Hub rule file when one is active. Without one, they behave as before.
- The scripts leave no Python bytecode cache next to themselves.

### Removed

- The legacy `codex-plugin` layout, a Pro package, as announced in 3.0.0. The Agent Plugins package replaces it.

## [3.0.0] - 2026-09-27

Built and never published: its changes first reached the public in 3.1.0. Whalory now writes business copy in English as well as Persian. The same skill also runs as a plugin, with agents, commands, and a local MCP server.

### Renamed

- The product is now Whalory, «والوری» in Persian. Whalya, «والیا», stays the name of the studio that makes it, which also holds the copyright.
- The skill, the plugin, and the MCP server are called `whalory`. Commands are `/whalory:<command>`.
- User profiles live in `~/.whalory/profiles/`. A profile missing there is still read from the old `~/.whalya/profiles/` folder, which nothing writes to.
- Environment variables start with `WHALORY_`. The old `WHALYA_` names still work when the new one is empty, and are deprecated.

### Added

- English output, in US English by default, with `en-GB`, `en-AU`, `en-CA`, `en-NZ`, `en-IE`, and `en-IN` available through a profile or a market.
- An English craft pack. Core has eleven of its files: craft, plain English, style guide, common errors, AI tells, occasions, claims, ethics, channels, forms, and style repair.
- `lint_en.py` for English copy, and `lint.py`, which picks the language of each line and runs the right linter. `textcount.py` counts graphemes, X-weighted characters, UTF-16 units, and SMS segments.
- A Claude Code plugin with its own marketplace file. Core has the `whalory-writer` and `whalory-editor` agents and the `write`, `review`, `voice`, and `lint` commands.
- A separate, opt-in autolint plugin that lints content and locale files after each edit.
- An Agent Plugins package for Codex, and for GitHub Copilot in Visual Studio Code.
- A Gemini CLI extension. It is built, but its repository is not published yet, so Gemini CLI uses the skill folder for now.
- `mcp_server.py`, a read-only MCP server over stdio with five tools in Core. It has no dependencies and makes no network calls. An `.mcpb` bundle installs it in Claude Desktop.
- English paste-in prompts next to the Persian ones.
- New voice profile keys for language, variant, spelling, the serial comma, contractions, and house style. Profile schema version 2 is unchanged, and version 2 profiles work as before.
- This repository's front pages in English and Persian, and the license texts. Also its Code of Conduct, its contributing, security, support, and privacy pages, its issue forms, and a CI workflow that runs the self-tests.

### Changed

- The method files are in English and serve both languages. Their rules, thresholds, and order did not change.
- The Persian craft files moved, unchanged, from `references/` to `references/fa/`.
- Headings in the method files and in `SKILL.md` have English anchors.
- The docs use `lint.py` in place of `lint_fa.py`. `lint_fa.py` keeps its flags and output.

### Deprecated

- The legacy `codex-plugin` layout, a Pro package. It will be removed in 3.1; the Agent Plugins package replaces it.

## [2.0.0] - 2026-09-27

Built under the name Whalya and never released publicly. The date is the one the skill's own changelog records for it. Version 2 added context detection and the question gate, plus channel data with sources and check dates. It also brought voice profile version 2 and the Core, Pro, and Studio editions. The skill's changelog has the full list.

## [1.x]

The first version, before version numbering, built under the name Whalya and never released publicly. Its date was not recorded.

[Unreleased]: https://github.com/gilebehnam/whalory/compare/v3.1.0...HEAD
[3.1.0]: https://github.com/gilebehnam/whalory/releases/tag/v3.1.0
