# Whalory

> Release status: 3.2.0 is an unpublished local candidate. Public 3.0.0 is the verified release; 3.1.0 is an unpublished development precursor. Candidate artifact names below refer to local build outputs, not newly published download URLs.

Whalory («والوری») turns your AI assistant into a copywriting team for English and Persian (Farsi). The team writes, rewrites, and reviews business copy in each brand's own voice. It works out the task, channel, and output language before it writes. It asks at most three short questions, and only when the answer would change the text. Nothing gets invented: no facts, quotes, or numbers. Drafts are checked with bilingual linters that run on your machine. Without Python, Whalory works through a manual checklist instead and says so in its note. Guide: [`GUIDE.en.md`](GUIDE.en.md). Persian version: [`README.md`](README.md).

## Contents

- [What it does](#what-it-does)
- [Three rules no profile can change](#three-rules-no-profile-can-change)
- [Languages and variants](#languages-and-variants)
- [Install](#install)
- [Python](#python)
- [Commands and agents](#commands-and-agents)
- [MCP tools](#mcp-tools)
- [Editions](#editions)
- [Network activity](#network-activity)
- [Privacy](#privacy)
- [Folder map](#folder-map)
- [License and support](#license-and-support)

## What it does

| Area | Tasks |
|---|---|
| Social | Instagram captions, LinkedIn posts, X posts, carousels, stories, reels, and Telegram channel posts |
| Sales | Product descriptions, marketplace listings, app store listings, ads, SMS messages, push notifications, email, headlines, and taglines |
| Web and apps | Landing, about, and pricing pages; error messages; interface strings in the locale files of a code repository |
| Customers | Replies to customers and to public reviews, apologies, other hard messages, and chatbot turns |
| Brand and strategy | Voice profiles, naming, pitch decks, campaigns, and content plans |
| Repair and teaching | Style repair, meeting-note cleanup, scoring, review, and lessons with exercises |
| Between languages | Transcreation from Persian to English and back, with every fact kept |

Each brand's voice lives in a voice profile (`VOICE.md`), and the method stays the same for every brand. The skill's map is [`SKILL.md`](SKILL.md), and every task has a playbook in the [task index](references/playbooks.md#task-index).

## Three rules no profile can change

1. Nothing is invented. No made-up stories, people, numbers, quotes, reviews, results, or permits. Unknown details go in brackets, such as `[confirm: weight]` in English copy and «[وزن تأیید شود]» in Persian copy.
2. No machine patterns. No straw-man contrast, no stacked adjectives, no moral wrap-up, and no dash in the middle of a sentence. Catalogs: [English](references/en/ai-tells.md), [Persian](references/fa/ai-tells.md).
3. No claim without evidence. Every objective claim needs evidence the brand can show. Otherwise it gets a bracket: `[source needed: …]` in English copy, «[… تأیید شود]» in Persian copy. In a [high-risk industry](references/router.md#high-risk-words-and-industry-cards), the note also marks it "confirm before publishing". Details: [English claims](references/en/claims.md), [Persian claims](references/fa/claims.md).

## Languages and variants

- Output language. Whalory decides it before writing. An explicit instruction comes first, then the target channel or market. Next come the text you supplied and the language of your request, and last the profile.
- English. US English (`en-US`) by default. A profile or market can set `en-GB`, `en-AU`, `en-CA`, `en-NZ`, `en-IE`, or `en-IN`, with the matching spelling, the Oxford comma setting, and a contractions policy.
- Persian. Iranian Persian (`fa-IR`) with correct half-spaces, Persian digits, and «» quotes. Dari (`fa-AF`) and Tajik (`tg`) get notes on their differences.
- Transcreation. Copy moves between Persian and English as a side-by-side table with notes on what changed and why. Numbers, names, prices, dates, and conditions stay locked.
- Out of scope. Code and code comments, academic essays, legal drafting, and translation that is literary, certified, or word for word. The same goes for fiction and verse wanted for their own sake. A labeled brand story, a rhymed slogan, or an ad jingle stays in scope. So do plain-language summaries around legal text, such as a cookie banner or a terms summary.

## Install

The public repository is [`gilebehnam/whalory`](https://github.com/gilebehnam/whalory) on GitHub. Every install path was checked against the host's documentation on 2026-09-27 or 2026-09-28.

### Claude Code

```bash
claude plugin marketplace add gilebehnam/whalory
claude plugin install whalory@whalory
```

On Windows, add `--config python=python` to the install command, so the tools use the right Python command (Claude Code 2.1.147 or later, [CLI reference](https://code.claude.com/docs/en/plugins/cli-reference)). The plugin brings the skill, the commands, the subagents, and the tools. Skills in a plugin are called as `/whalory:<name>` ([skills docs](https://code.claude.com/docs/en/skills)).

The lint-on-save hook is a separate, opt-in plugin: `claude plugin install whalory-autolint@whalory`. It checks content and locale files after each edit and never blocks one. It runs `python3`; see [Python](#python).

To use the skill alone, copy the `whalory` folder into `~/.claude/skills/` and call it with `/whalory`.

### Claude Desktop

Download `whalory-core-mcp-3.2.0.mcpb` from the verified local candidate kit. Double-click it, drag it into the Claude Desktop window, or go to Settings > Extensions > Advanced settings > Install Extension ([desktop extension docs](https://claude.com/docs/connectors/building/mcpb)). The bundle adds the tools only and needs Python 3.8 or later: Claude Desktop includes Node.js, not Python. For the method itself, also install the skill, as in the claude.ai section below.

### claude.ai

Turn on code execution, then upload the claude.ai zip in Customize > Skills. On claude.ai the skill description is limited to 200 characters, and the zip root must be the skill folder ([Claude help](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)).

### Codex and the ChatGPT desktop app

The simplest route is the skill folder. Copy `whalory` into `~/.agents/skills/`, or into `.agents/skills/` in a repository, and call it with `$whalory` ([Codex skills](https://learn.chatgpt.com/docs/build-skills)). To add the tools, put the MCP server in `~/.codex/config.toml`, as the [guide](GUIDE.en.md#mcp-tools-reference) shows.

For the commands as well, install the Agent Plugins build from the verified local candidate kit, `whalory-core-3.2.0-agent-plugin.zip`. Its `INSTALL.md` shows how to add it to a Codex marketplace; then install Whalory from `/plugins`. Its MCP server runs `python3`. In our test with codex-cli 0.145.0, Codex didn't tell the server which project was open. From the plugin, the file tools then can't read your files, while `lint_text` still works on pasted text. Plugins work in the ChatGPT desktop app and the Codex CLI, but not in the Codex IDE extension ([plugins overview](https://learn.chatgpt.com/docs/plugins)).

Don't use the public repository as a Codex plugin. Codex loads its skills, but in our test its MCP server didn't start. OpenAI doesn't expand the Claude plugin's `user_config` values, and the server command is one of them ([OpenAI docs](https://developers.openai.com/plugins/guides/submit-claude-plugin)).

### Gemini CLI

The Gemini CLI extension's repository is not published yet. Until it is, copy the `whalory` folder into `~/.gemini/skills/` ([Gemini CLI skills](https://geminicli.com/docs/cli/skills/)). The extension will bring the skill, the commands as `/whalory:<name>`, the subagents, and the tools ([extension reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md)).

### Visual Studio Code (VS Code)

For GitHub Copilot in Visual Studio Code (VS Code), use the Agent Plugins build, `whalory-core-3.2.0-agent-plugin.zip`. Unzip it and add its `whalory` folder to the `chat.pluginLocations` setting with the value `true` ([VS Code docs](https://github.com/microsoft/vscode-docs/blob/main/docs/agent-customization/agent-plugins.md)). Its MCP server runs `python3`.

VS Code can also load the public repository as a Claude-format plugin, through Chat: Install Plugin From Source. That route brings the skill and the commands, but probably not the tools. The plugin starts its server with a Claude Code setting, and VS Code's docs name only `${CLAUDE_PLUGIN_ROOT}` among the values it fills in. Neither route has been tested in VS Code yet. To add the tools by hand, use `.vscode/mcp.json` as the [guide](GUIDE.en.md#mcp-tools-reference) shows.

### Cursor

Copy the `whalory` folder into `.cursor/skills/` or `.agents/skills/` in your project ([Cursor skills](https://cursor.com/docs/skills)). To add the tools, put this in `.cursor/mcp.json` ([Cursor MCP](https://cursor.com/docs/mcp)):

```json
{"mcpServers": {"whalory": {"command": "python3",
  "args": ["<path-to-whalory>/scripts/mcp_server.py", "--root", "${workspaceFolder}"]}}}
```

Whalory Pro also ships a Cursor plugin. The Agent Plugins build is not a route for the tools in Cursor: Cursor doesn't fill in `${PLUGIN_ROOT}` in its `mcp.json` ([Cursor plugins](https://cursor.com/docs/plugins)).

### Other assistants

- Assistants that read Agent Skills from `.agents/skills/`, such as [Codex](https://learn.chatgpt.com/docs/build-skills), [Copilot](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), and [Gemini CLI](https://geminicli.com/docs/cli/skills/): copy the `whalory` folder there.
- ChatGPT, the Gemini app, and any other chat: paste one of the ready prompts. It goes into the app's custom instructions, or at the start of the conversation. Core includes 1,500- and 4,000-character prompts in English and Persian, in `whalory-core-3.2.0-paste.zip`. Pro adds an 8,000-character prompt and ready GPT and Gem packs in both languages.

## Python

Whalory works without Python: it then checks drafts against a manual checklist and says so in its note. The linters, the MCP server, and the autolint hook need Python 3.8 or later, with the standard library only.

| System | Check it with | What to know |
|---|---|---|
| macOS and Linux | `python3 --version` | Every package starts the tools with `python3`. |
| Windows | `python3 --version`, `python --version`, and `py -3 --version` | Which of these work depends on how Python was installed. The Python install manager, from python.org or the Microsoft Store, adds all three ([Python on Windows](https://docs.python.org/3/using/windows.html), checked 2026-09-28). Other installs may have only `python` or `py`. |

What each package runs on Windows:

- The Claude Code plugin starts its MCP server with its Python option, `python3` by default. Set it with `--config python=python` when you install, or later with `/plugin configure whalory`.
- The Claude Desktop bundle (`.mcpb`) runs `python` on Windows and `python3` elsewhere.
- The autolint hook, the Agent Plugins build, the Gemini CLI extension, and the Cursor plugin run `python3`. If `python3 --version` fails on Windows, their tools and the autolint check don't run; the skill itself still works. Installing Python with the Python install manager adds the `python3` command.
- In an MCP configuration you write by hand, use the command that works on your machine.

## Commands and agents

| Command | What it does | Edition |
|---|---|---|
| `write` | Drafts with the writer agent, then passes only the draft, facts list, profile, and format to the editor for a blind review | Core |
| `review` | Blind review of a file or pasted text: a score table and fixes | Core |
| `voice` | Builds or updates `VOICE.md` and `voice.json` from three questions or from sample texts | Core |
| `lint` | Runs the bilingual linters on files and summarizes the results | Core |
| `campaign` | Plans a multichannel campaign; the writer and editor then handle each piece | Pro |
| `transcreate` | Moves copy between Persian and English for a named market | Pro |
| `audit` | Audits a folder of copy for drift in register, spelling, and variant | Pro |

Claude Code and Gemini CLI call these `/whalory:write` and so on. Hosts that use Agent Plugins get them as skills named `whalory-write` and so on. The agents are `whalory-writer` and `whalory-editor` in Core, plus `whalory-researcher`, `whalory-strategist`, `whalory-transcreator`, and `whalory-voice-keeper` in Pro. The editor sees only the draft and the facts it was given, never the writer's reasoning.

## MCP tools

The Whalory MCP (Model Context Protocol) server is a single Python file that speaks JSON-RPC over standard input and output. No tool uses the network. By default the tools write nothing. If you turn on Whalory Hub statistics or packets in your own terminal, `lint_text`, `lint_file`, and `check_final` add counts to the Hub folder. They never write your text there ([Network activity](#network-activity)).

| Tool | What it returns | Edition |
|---|---|---|
| `lint_text` | Issues in pasted Persian or English copy: AI tells, puffery, spelling, punctuation, sentence length, readability, profile, and channel limits | Core |
| `lint_file` | The same for a text, Markdown, HTML, CSV, or locale file inside an allowed folder | Core |
| `check_final` | The final check of the copy you approved: the same findings as `lint_text` | Core |
| `get_playbook` | The playbook for a task, matched in either language | Core |
| `get_reference_section` | One section of a reference file, or its contents list | Core |
| `profile_lookup` | The brand's voice profile and learnings note, found in Whalory's lookup order | Core |
| `detect_context` | A cheap scan of a project folder: locale files, content folders, profiles | Pro |
| `channel_limits` | Character, byte, and item limits for each platform field. Each limit has a source and a check date | Pro |
| `compare_texts` | Facts added or dropped between two versions, also across languages | Pro |
| `ab_test_size` | Sample size or significance for an A/B test | Pro |

## Editions

| | Core | Pro | Studio |
|---|---|---|---|
| Price | Free | See the Whalory website | See the Whalory website |
| Users | Anyone | One person | Up to 5 people in one organization |
| Method | Context detection, question gate, judgment, brief | Same | Same |
| Playbooks | The most common tasks | All, with multichannel chains | All, with multichannel chains |
| Language packs | Core craft files in English and Persian | Every craft and market file in both languages | Same as Pro |
| Voice | Templates, Whalory's own voice, two starter profiles per language | Every starter profile, verbal identity | Same as Pro |
| Plugin | Writer and editor agents; `write`, `review`, `voice`, `lint`, `learn`, `lessons`, `hub`, and `feedback` | Every agent and command | Same as Pro |
| Tools | Linters, self-tests, six MCP tools | Ten MCP tools, before-and-after comparison, corpus audit, A/B calculator, channel data | Same as Pro |
| License | [Open licenses for text and code](LICENSE-CORE.en.md) | End-user license (in Whalory Pro) | End-user license (in Whalory Pro) |

Whalory Core is free for everyone. Pro and Studio are sold only in Iran for now. Prices are in toman, and payment is by Iranian bank card. They are not yet available outside Iran. To ask about them, use the [contact page](https://whalory.com/support/), or watch the repository's releases for news.

Text you write with Whalory is yours in every edition, including for commercial use. Whalory never adds promotion for itself to the copy it delivers.

## Network activity

The linters, the MCP server, and the autolint hook make no network calls. Only `scripts/hub_client.py`, the Whalory Hub client, uses the network, and only as this table shows. The plugins for Claude Code, Codex, and Cursor, and the Gemini CLI extension, run `hub_client.py tick` when a session starts. It prints nothing and does at most one of these things per run.

| What | When | Where | Sends | Turn off |
|---|---|---|---|---|
| Rule updates | At most once a day, when a session starts | `gilebehnam.github.io`, `github.com`, `hub.whalory.com` | The download request only; the servers see your IP address and that Whalory ran that day | `WHALORY_HUB_UPDATES=0`, or `python scripts/hub_client.py off updates` |
| License proof for statistics | Pro and Studio only, only if you opted in; once a week | `whalory.com` | A one-time proof made from your license key (never the key) and a blinded ticket request | `python scripts/hub_client.py off` |
| Weekly statistics | Only if you opted in | `hub.whalory.com` (Iran) | Counts per Whalory rule, rounded word counts, edit and revision measures, versions; never text | `python scripts/hub_client.py off` |
| Phrase sharing | Only if you opted in separately | `hub.whalory.com` | At most 20 ids a week from Whalory's public phrase list | `python scripts/hub_client.py off phrases` |
| Weekly packet | Only if you turned packets on, and only when you post it yourself | A comment under your own GitHub account on the public `whalory-hub` repository | Counts only, shown to you in full first; the program itself sends nothing | `python scripts/hub_client.py off packets` |

Statistics, phrase sharing, and packets stay off unless you turn them on yourself, in your own terminal: `python scripts/hub_client.py consent`, `on stats`, or `on packets`. In this release they are also closed on the server side, until a signed setting from the owner opens them. Updates are signed. The client checks each file against the keys it ships with, and when a check fails it keeps the rules it already has. On Codex, `tick` stays offline unless the Codex sandbox allows network access.

Other switches:

- `WHALORY_HUB=0` turns the Hub off completely: no network, no Hub files, built-in rules only.
- `WHALORY_HUB_OVERLAY=0`, or `lint.py --no-overlay`, lints with the built-in rules only.
- `DO_NOT_TRACK` or `DISABLE_TELEMETRY`, set to any value, keeps statistics and packets off. `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, set to any value, stops all Hub network activity.
- `python scripts/hub_client.py status` shows what is on, and `log --net` lists every network request.

Before uninstalling, run `hub_client.py forget`; uninstalling alone does not delete the Hub folder or send deletion requests. The privacy notice for the Hub is on the [legal page](https://whalory.com/legal/#hub-privacy).

## Privacy

The linters, the MCP server, and the autolint hook run on your own machine. They make no network calls and send no text anywhere. They change your files only when you run `lint.py --fix` yourself: it saves a fixed copy next to the original, or fixes the file in place with `--write`. While Hub statistics or packets are on, they also add counts, never text, to the Hub folder. The assistant you use handles your text under its own terms.

## Folder map

```
whalory/
  SKILL.md              the skill's map; every assistant starts here
  README.en.md          this file; README.md is the Persian README
  GUIDE.en.md           user guide (GUIDE.fa.md in Persian)
  WHALORY.md            who Whalory is (WHALORY.fa.md in Persian; Pro)
  CHANGELOG.md          changes per version (CHANGELOG.fa.md in Persian)
  LICENSE.en.md         which license covers which edition (LICENSE.md in Persian)
  LICENSE-CORE.en.md    CC BY 4.0 and MIT texts (LICENSE-CORE.md in Persian)
  EULA.en.md|fa.md      end-user license for Pro and Studio (Pro)
  VERSION               version number
  references/           the method: detection, questions, playbooks, review, voice
    en/                 English craft, channels, claims, and market files
    fa/                 Persian craft, channels, claims, and market files
  profiles/             templates, Whalory's voice, learnings template, starters/ (fa) and starters/en/
  data/channels/        channel limits with sources and check dates (Pro)
  scripts/              lint.py, lint_fa.py, lint_en.py, mcp_server.py, self-tests, other tools
  agents/openai.yaml    Codex display metadata
  portable/             install guide and paste-in prompts (Pro)
  examples/             a complete profile of a real brand (Pro)
```

Keep your own brand profile outside this folder, as `VOICE.md` in your project root or as `~/.whalory/profiles/<brand>.md`, so updates never overwrite it. Its learnings note sits next to it: `LEARNINGS.md` next to `VOICE.md`, or `<brand>.LEARNINGS.md` next to `<brand>.md`.

## License and support

- Licenses: [`LICENSE.en.md`](LICENSE.en.md). Core text is under Creative Commons Attribution 4.0 (CC BY 4.0), and Core scripts are under the MIT License ([`LICENSE-CORE.en.md`](LICENSE-CORE.en.md)).
- Changes: [`CHANGELOG.md`](CHANGELOG.md). Version: [`VERSION`](VERSION).
- Website: [whalory.com](https://whalory.com/). Whalory is made by the Whalya studio.
- Support: for a bug in Whalory Core, open an issue in the public repository; Core has no other support. Support for Pro and Studio is described in the end-user license (in Whalory Pro). Other questions: the [contact page](https://whalory.com/support/).
