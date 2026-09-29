# Whalory guide

Hi. We're Whalory, a copy team for English and Persian. This guide is for anyone who wants to work with us. It covers installing us on the assistant you use, handing over a task, why we sometimes ask questions, and how to check what we deliver. Each section answers one real question, so jump straight to the one you need. Persian guide: [`GUIDE.fa.md`](GUIDE.fa.md).

## Contents

- [What we do for you](#what-we-do-for-you)
- [Three promises](#three-promises)
- [Install](#install)
- [A first task in five steps](#a-first-task-in-five-steps)
- [How we read the situation](#how-we-read-the-situation)
- [When we ask, and how to answer](#when-we-ask-and-how-to-answer)
- [How to brief us](#how-to-brief-us)
- [Voice profiles](#voice-profiles)
- [Variants and spelling](#variants-and-spelling)
- [Transcreation](#transcreation)
- [Common tasks](#common-tasks)
- [Commands and agents](#commands-and-agents)
- [MCP tools reference](#mcp-tools-reference)
- [Checking the work](#checking-the-work)
- [Continuous integration](#continuous-integration)
- [Autolint](#autolint)
- [Troubleshooting](#troubleshooting)

## What we do for you

Hand us business copy in English or Persian to write from scratch, repair, or score.

| Area | Tasks |
|---|---|
| Social | Captions, LinkedIn posts, X posts, carousels, stories, reels, and Telegram channel posts |
| Sales | Product descriptions, marketplace listings, ads, SMS messages, email, headlines, and taglines |
| Web and apps | Landing and about pages, error messages, and the strings in locale files |
| Customers | Replies to customers and to public reviews, apologies, other hard messages, and chatbot turns |
| Brand and strategy | Voice profiles, naming, pitch decks, campaigns, and content plans |
| Repair and teaching | Style repair, meeting-note cleanup, scoring, review, and lessons with exercises |
| Between languages | Transcreation from Persian to English and back |

The full list, with everyday phrasings for each task in both languages, is in the [task index](references/playbooks.md#task-index).

## Three promises

These three hold in every task, whatever the profile says:

1. We don't invent anything. No made-up stories, customers, numbers, quotes, or permits. Anything we don't know goes in brackets, like `[confirm: weight]`, and the delivery note lists what's missing.
2. We don't write like a machine. Straw-man contrast (`it's not X, it's Y`), `not just… but also`, `delve`, `seamless`, `Did you know…?`, and dashes in the middle of a sentence stay out of our copy. The full list: [AI tells](references/en/ai-tells.md).
3. We don't make claims without evidence. Every objective claim needs evidence the brand can show. Otherwise it gets a bracket: `[source needed: …]` in English copy, «[… تأیید شود]» in Persian copy. In a [high-risk industry](references/router.md#high-risk-words-and-industry-cards), the note also marks it "confirm before publishing". See [claims](references/en/claims.md).

## Install

The commands for each assistant are in the [install section](README.en.md#install) of `README.en.md`. This table shows which package fits which assistant.

| Assistant | Package | Edition |
|---|---|---|
| Claude Code | The Claude plugin from the public repository | Core and Pro |
| Codex, Visual Studio Code (VS Code) with GitHub Copilot, and other Agent Plugins hosts | The Agent Plugins zip, or the skill folder | Core and Pro |
| Claude Desktop | The `.mcpb` bundle, which adds the tools only | Core and Pro |
| claude.ai | The claude.ai skill zip | Core and Pro |
| Gemini CLI | The Gemini extension | Core and Pro |
| Cursor | The skill folder, with the tools in `.cursor/mcp.json` | Core and Pro; a Cursor plugin in Pro |
| GitHub Copilot outside VS Code | The skill folder | Core and Pro |
| ChatGPT custom GPTs and Gemini Gems | Instructions and knowledge files in English and Persian | Pro |
| Any other chat | Paste-in prompts of 1,500 and 4,000 characters, plus 8,000 in Pro | Core and Pro |

Core packages come from the public repository and its releases. Pro buyers download every package from their account page on the website.

A few things are the same everywhere:

- Keep your brand profile outside the skill folder: `VOICE.md` in your project root, or `~/.whalory/profiles/<brand>.md`. Updates replace the skill folder and never touch these two. The full search order is in [`SKILL.md`](SKILL.md#profile-lookup-order).
- Keep the learnings note next to the profile that gets read: `LEARNINGS.md` next to `VOICE.md`, or `<brand>.LEARNINGS.md` next to `<brand>.md`. We read it every time ([template](profiles/LEARNINGS-template.en.md)).
- To update a plugin, use your host's update command, for example `claude plugin update whalory@whalory` in Claude Code. To update a plain skill folder, replace the `whalory` folder. The version is in [`VERSION`](VERSION), and the changes are in [`CHANGELOG.md`](CHANGELOG.md).
- The scripts need Python 3.8 or later. See [troubleshooting](#troubleshooting) if the command isn't found.
- Whalory was called Whalya before version 3.0.0. A profile still in the old `~/.whalya/profiles/` folder is read when `~/.whalory/profiles/` has none of that name, and nothing is ever written to the old folder. The old `WHALYA_*` environment variables still work when the matching `WHALORY_*` variable is empty, but they're deprecated.

## A first task in five steps

1. Give us a profile, or let us build one. Without a profile we still write, in the default voice. That means US English, sentences of 25 words or fewer, no humor, and no exclamation marks or emoji. Copy the closest English [starter profile](profiles/starters/README.md) from `profiles/starters/en/`, or start from the [blank template](profiles/_template.en.md). If you ask for brand-building work and there's no profile, we ask three questions first and offer to save the answers in `VOICE.md`.
2. Tell us the task. One sentence in the language you speak is enough, for example `Write a LinkedIn post announcing [feature]. Facts: [what it does, who it's for, launch date].`
3. If we ask, answer briefly, for example `1a 2b`. If you'd rather not answer, reply `write`. We'll use the recommended options and put brackets where facts are missing.
4. Get the delivery. The finished copy comes first, followed by a short note. It starts with "Diagnosis:" and says what the task was, which profile we read, and which brackets are still open.
5. Check it. If you have Python:

```bash
python <skill-path>/scripts/lint.py draft.txt --profile VOICE.md
```

Zero errors means the mechanics and the patterns are clean. The script doesn't judge the story or the truth of the text, so read it against the [review checklist](references/review.md) yourself.

## How we read the situation

Before any question, we silently fill in a context card. First the task: write, rewrite, review, teach, or plan. Then where the text will be read, who reads it, what's attached, the output language, the risk, the occasion, and the profile. We never ask which assistant you use; our tools tell us.

| When you | We |
|---|---|
| Name the place: caption, SMS, Amazon listing, email | Take the playbook for that format |
| Only say "copy for my product" | Ask where it will be read, in an interactive chat; otherwise guess and say so in the note |
| Send a product photo | Ask before writing whether it's the brand's own photo or you want a story with a "story" label |
| Paste a text and say "make it better" | Repair it without changing any number, name, or condition |
| Work in a repository with locale files | Change the values only; keys and placeholders stay untouched |
| Use a risky word: supplement, `clinically proven`, `guaranteed returns`, immigration | Put brackets on the claim and mark it "confirm before publishing" |
| Publish on a holiday or a day of mourning | Adjust the tone with the [occasions calendar](references/en/occasions.md) |
| Write in English, or name an English market | Write English copy with the English pack; your profile or the market sets the variant |
| Ask for code comments, a poem or story with no marketing job, an academic essay, legal drafting, or literary translation | Leave it to your assistant, which answers without a Whalory note: these are out of scope. A labeled brand story or a rhymed slogan stays with us |

The "Diagnosis:" line in the note sums up this card, for example `Diagnosis: Instagram caption · new customers · profile: cafe (starter) · no questions · QA: manual`. If the route was wrong, fix it in one sentence: "this is an SMS." Details: [context detection](references/router.md).

## When we ask, and how to answer

- We never ask if you said "just write", "no questions", or "quick draft", or if the task runs unattended. We write with brackets and list our assumptions at the top of the note.
- Anything already in the request, the attachments, the profile, or `LEARNINGS.md` is never asked again.
- Questions come first only when the risk is high and facts are missing, or when two readings of the task would change the whole text. Costly tasks also get their questions first: strategy, naming, campaigns, and pitch decks. So does brand-building work when there's no profile.
- In every other case we write first and add at most two follow-up questions at the end of the note.

Each round has at most three questions, all in one message. Each question offers options that come from the task, with the recommended one first:

```
Before writing, two or three quick things:
1. Where will this be read? a) Instagram caption (recommended) b) website page c) SMS
2. Who is the reader? a) first-time buyers (recommended) b) regulars
3. Give us one concrete fact: a number, a name, or how it's made.
Answer briefly, for example "1a 2b". If you'd rather not answer, just reply "write". We'll use the recommended options and put brackets where facts are missing.
```

We ask in the language of your request, and "write" works in both languages («بنویس» in Persian). An answer that belongs to the brand, such as "we use contractions with customers," goes into the profile or `LEARNINGS.md`, so we don't ask again. The full rules: [question gate](references/intake.md).

## How to brief us

- Say where the text will be read. A caption isn't a product page, and an SMS isn't an email.
- Say who the reader is and what state they're in. A traveler just back from a trip and a company's purchasing manager need different texts.
- Give us materials, not adjectives. `Monofloral astragalus honey from Khalkhal, 500 g, in a hexagonal jar` gives us a story. `authentic, high-quality honey` gives us nothing.
- Ask for one version unless you need more. If you want several, say how they should differ: tone, hook, or length.
- Send feedback back to the profile. We learn from the profile and `LEARNINGS.md`; the conversation's memory doesn't last. The format: [learnings note](profiles/LEARNINGS-template.en.md).

## Voice profiles

A voice profile is two files that make one decision: `VOICE.md` for people and `voice.json` for the linters. The method stays the same for every brand, and the profile holds everything that makes the brand sound like itself. Structure: [voice profile](references/voice-profile.md). Building one: [profile builder](references/profile-builder.md).

### English profiles

An English profile sets `"language": "en"` and adds these keys ([language and style](references/voice-profile.md#language-and-style)):

| Key | Values | When missing |
|---|---|---|
| `variant` | `en-US`, `en-GB`, `en-AU`, `en-CA`, `en-NZ`, `en-IE`, `en-IN` | `en-US` |
| `spelling` | `us`, `uk`, `uk-ize` | Follows the variant |
| `oxford_comma` | `true`, `false` | Checked for consistency only |
| `contractions` | `use`, `avoid`, `positive-only` | No rule |
| `house_style` | `chicago`, `ap`, `microsoft`, `google`, `govuk`, `mailchimp` | None |
| `reading_grade_max` | A school grade from 4 to 16 | Follows the jargon dial |

The tone dials are the same in both languages: warmth, formality, humor, narrative density, sentence length, loud marks, jargon, and rhetoric. The quickest way in is the [English route](references/profile-builder.md#english-route): three questions, or a few good texts you already have.

### Bilingual brands

A brand that publishes in both languages sets `"language": "bilingual"` and lists every variant it uses, primary first. Settings that differ by language go under `by_lang` ([bilingual brands](references/voice-profile.md#bilingual-brands)):

```json
{"language": "bilingual", "variant": "fa-IR", "variants": ["fa-IR", "en-GB"],
 "by_lang": {"en": {"max_words": 20, "banned": ["world-class"]},
             "fa": {"address": "shoma"}}}
```

Keys under `by_lang.en` override the top-level keys for English copy, and `by_lang.fa` does the same for Persian. The address (`to` or `shoma`) and the register are Persian-only settings.

## Variants and spelling

We pick the variant from the channel or market first, then from the profile, and fall back to `en-US`. The spelling follows the variant unless the profile sets it:

| Variant | Spelling | Example |
|---|---|---|
| `en-US` | `us` | `color`, `organize`, `center` |
| `en-GB`, `en-AU`, `en-NZ`, `en-IE`, `en-IN` | `uk` | `colour`, `organise`, `centre` |
| `en-CA` | `uk-ize` | `colour`, `organize`, `centre` |

- Mixing US and UK forms in one text is an error (`en-spelling-mix`), whatever the variant.
- Oxford commas, contractions, numbers, dates, and dashes follow the profile and its house style. The presets are in the [style guide](references/en/style-guide.md#house-style-presets).
- For readability, `reading_grade_max` sets the target grade. Without it, the jargon dial does: 1 means grade 6, 2 means 8, 3 means 10, 4 means 12, and 5 means 14.

To check a text against one variant:

```bash
python <skill-path>/scripts/lint.py draft.md --md --lang en --variant en-GB
```

## Transcreation

Transcreation moves copy between Persian and English for a named market and keeps the meaning, the voice, and every fact. It's part of Whalory Pro. Method: `transcreation.md` (in Whalory Pro). Playbook: transcreation and bilingual copy (in Whalory Pro).

- Delivery. A two-column table with the source and the target side by side, plus a short list of what changed and why.
- Fact lock. Numbers, names, prices, dates, and conditions stay exactly as they were. We check them with `compare.py` or the `compare_texts` tool, which reads Persian and Latin digits alike.
- Persian into English. Politeness formulas become plain courtesy, «شما» becomes "you," Iranian calendar dates get their Gregorian equivalent, and prices in toman or rial are never converted silently. Names follow the profile's `romanization`.
- English into Persian. We choose the register and address, then apply half-spaces, Persian digits, and «» quotes. Persian text usually runs longer, so we check the channel limits again.
- A new market brings new rules. Claims and regulations are checked again for the target market.

A request can be as short as `Transcreate this Persian caption for our UK Instagram account.`

## Common tasks

| You want | Say | We read |
|---|---|---|
| A caption | `Instagram caption for [product or moment]; goal: [sell / introduce]` | [Caption](references/playbooks-social.md#caption) |
| A LinkedIn post | `LinkedIn post announcing [feature]; facts: [what, who, when]` | [Social post](references/playbooks-social.md#social-post) |
| A product description | `Product description for the store page; materials: [name, origin, weight]` | [Description](references/playbooks-product.md#product-description) |
| A cold email | `Cold email to [role] at [company type]; offer: [what]` | [Email](references/playbooks-messages.md#email) |
| An SMS | `Order-shipped SMS; variables: [order code, tracking link]` | [SMS](references/playbooks-messages.md#sms) |
| App microcopy | `Button and label text for the checkout form`, or the file `en.json` | [UI microcopy](references/playbooks-web.md#ui-microcopy) |
| Error and empty states | `Failed payment message and empty cart text` | [Error, empty, and waiting states](references/playbooks-web.md#error-empty-and-waiting-states) |
| A better text | `Improve this text; sentences only` | [Style repair](references/playbooks-repair.md#style-repair) |
| A customer reply | `Reply to this unhappy customer; what happened: [facts]` | [Customer reply](references/playbooks-messages.md#customer-reply) |
| A score | `Score this text and tell me what to fix` | [Scoring and review](references/playbooks-repair.md#scoring-and-review) |
| A voice profile | `Build a voice profile from these three texts of ours` | [Voice profile in three questions](references/playbooks-strategy.md#voice-profile-in-three-questions) |

## Commands and agents

The Claude Code plugin and the Gemini extension add commands. In Claude Code and Gemini CLI they are `/whalory:write`, `/whalory:review`, and so on. Hosts that use Agent Plugins, such as Codex and Copilot, get the same commands as skills named `whalory-write`, `whalory-review`, and so on.

| Command | Example | What happens | Edition |
|---|---|---|---|
| `write` | `/whalory:write LinkedIn post for our launch, en-GB` | The writer drafts; the editor reviews it blind; must-fix items are applied; you get the copy, then the note | Core |
| `review` | `/whalory:review landing.md linkedin` | A blind review: a score table and fixes | Core |
| `voice` | `/whalory:voice acme samples/` | The voice keeper builds or updates the profile | Core |
| `lint` | `/whalory:lint locales/en.json --format ui` | The linters run and each file gets a summary; nothing is edited unless you ask | Core |
| `campaign` | `/whalory:campaign spring sale, Instagram and email, UK` | The strategist plans; the writer and editor handle each piece | Pro |
| `transcreate` | `/whalory:transcreate caption.txt to en UK` | Transcreation, then an editor pass in the target language | Pro |
| `audit` | `/whalory:audit content/ --profile auto` | The worst files, drift in register, spelling, and variant, and next steps | Pro |

The agents behind the commands:

- `whalory-writer` drafts with the full method and hands over the draft, a facts list, and the diagnosis note.
- `whalory-editor` is the blind reviewer. It sees only the draft, the profile, the channel, and the facts list, never the writer's reasoning. Any fact missing from the facts list counts as invented. The editor returns a score table, at most seven must-fix items, and at most three line edits.

Pro adds four more:

- `whalory-researcher` collects and checks facts and sources and never writes copy.
- `whalory-strategist` plans campaigns, chains, and tests.
- `whalory-transcreator` moves copy between the languages with the fact lock.
- `whalory-voice-keeper` builds and maintains `VOICE.md`, `voice.json`, and `LEARNINGS.md`.

## MCP tools reference

The Whalory MCP (Model Context Protocol) server is `scripts/mcp_server.py`, a single Python file with no dependencies. The plugin and the `.mcpb` bundle start it for you. Every tool is read-only, touches no network, and writes no files.

| Tool | Main inputs | Returns | Edition |
|---|---|---|---|
| `lint_text` | `text`; optional `lang`, `format`, `channel`, `profile`, `facts` | Issues with rule, line, and message, plus statistics | Core |
| `lint_file` | `path` inside an allowed folder; the same options | The same, for text, Markdown, HTML, CSV, or locale files | Core |
| `get_playbook` | `task`, as an anchor such as `caption` or free text in either language | The playbook section that matches best, and other matches | Core |
| `get_reference_section` | `path` under `references/`, `profiles/`, or `data/channels/`; optional `anchor` | One section, or the contents list when no anchor is given | Core |
| `profile_lookup` | Optional `name`, `project_dir`, `language`, `industry` | The profile in lookup order, its learnings note, and starter suggestions | Core |
| `detect_context` | Optional `dir` and `request` | Repository signals, locale files, profiles, and a suggested route | Pro |
| `channel_limits` | `channel`, `field`, `region`, or `query` | Limits per field with unit, source, and check date | Pro |
| `compare_texts` | `before`, `after` | Numbers, names, quotes, and conditions added or dropped | Pro |
| `ab_test_size` | `mode` (`size` or `test`) and rates or results | Sample size per variant, or significance | Pro |

The server also offers the prompts `write`, `review`, and `voice`, plus `transcreate` in Pro. It serves the references as `whalory://` resources.

File tools read only inside the skill folder and your project folders. The project folders come from one of three sources, checked in this order:

1. `--root` on the command line, or the `WHALORY_ROOTS` environment variable.
2. Otherwise, the folders your host shares with the server (MCP roots), if it shares any.
3. Otherwise, the folder the server starts in, but only when neither `--root` nor `WHALORY_ROOTS` was given. A drive's top folder, your home folder, the Windows folder, and Whalory's own folder never count.

If `--root` or `WHALORY_ROOTS` was given but points nowhere usable, the server never falls back to the folder it starts in. Pasted text is capped at 200,000 characters and files at 2 MB. A lint or compare call stops after 30 seconds by default; `--time-limit` changes that. `WHALORY_LANG` sets the default language (`auto`, `fa`, or `en`).

To connect the server by hand, point your host at it. For VS Code, put this in `.vscode/mcp.json` ([VS Code docs](https://code.visualstudio.com/docs/copilot/reference/mcp-configuration)):

```json
{"servers": {"whalory": {"type": "stdio", "command": "python3",
  "args": ["<path-to-whalory>/scripts/mcp_server.py", "--root", "${workspaceFolder}"]}}}
```

For Codex, put this in `~/.codex/config.toml` ([Codex docs](https://learn.chatgpt.com/docs/extend/mcp)):

```toml
[mcp_servers.whalory]
command = "python3"
args = ["<path-to-whalory>/scripts/mcp_server.py", "--root", "."]
default_tools_approval_mode = "auto"
```

On Windows, use the Python command that answers on your machine: `python3`, `python`, or `py` ([Python](README.en.md#python)).

## Checking the work

Check five things before you publish:

1. The first sentence starts with something concrete, such as a thing, a place, a person, or a moment, not with "we."
2. It has one real detail that belongs to this brand alone. The test: swap in a competitor's name. If the text still works, send it back.
3. It has no number, quote, or customer that you didn't give us.
4. The note comes separately, starts with "Diagnosis:", and says what's missing.
5. `lint.py` reports zero errors, or the note says `QA: manual`.

If something fails, send the text back with that exact message: "no story," "made-up number," "doesn't match the profile." A precise message teaches us more than "make it a bit better."

The scripts at a glance:

```bash
python <skill-path>/scripts/lint.py draft.txt --profile VOICE.md       # review
python <skill-path>/scripts/lint.py draft.txt --format caption        # with the format's limits
python <skill-path>/scripts/lint.py --text "Short copy to check"      # no file needed
python <skill-path>/scripts/lint.py src/locales/en.json --format ui   # locale file
python <skill-path>/scripts/lint.py draft.txt --fix                   # mechanical fixes only
python <skill-path>/scripts/detect_context.py .                       # where are we?
python <skill-path>/scripts/selftest.py                               # are the rules healthy?
```

`lint.py` picks the language of each line; `--lang fa` or `--lang en` forces one. `--fix` saves a fixed copy next to the file, and `--write` fixes the file in place.

## Continuous integration

`lint.py` exits with 0 when there are no errors, 1 when there are, and 2 on bad input, so any CI system can run it. Add `--strict` to fail on warnings too. Put the skill in the repository, for example in `.agents/skills/whalory/`, and point the linter at your copy and locale files.

A GitHub Actions workflow, for example `.github/workflows/copy-lint.yml` (action versions checked on 2026-09-27: [checkout](https://github.com/actions/checkout), [setup-python](https://github.com/actions/setup-python)):

```yaml
name: copy-lint
on: [pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.x"
      - run: python .agents/skills/whalory/scripts/lint.py content/ locales/ --profile VOICE.md
```

A pre-commit hook, in `.pre-commit-config.yaml` ([pre-commit docs](https://pre-commit.com/#repository-local-hooks)):

```yaml
repos:
  - repo: local
    hooks:
      - id: whalory-lint
        name: Whalory copy lint
        entry: python3 .agents/skills/whalory/scripts/lint.py --profile VOICE.md
        language: unsupported
        files: \.(md|txt|json|po|xliff|strings)$
```

`language: unsupported` needs pre-commit 4.4.0 or later; older versions call it `system`.

## Autolint

Autolint checks content and locale files each time the assistant writes or edits one, and reports the issues back to it. Nothing runs until you install it, and no edit is ever blocked.

- In Claude Code, install the separate plugin: `claude plugin install whalory-autolint@whalory`. The check runs after each Write or Edit and finishes within 10 seconds.
- It checks `.md`, `.mdx`, `.txt`, `.html`, `.htm`, `.po`, `.pot`, `.arb`, `.xliff`, `.xlf`, `.strings`, `.csv`, and `.tsv` files, plus `.json` and `.xml` files that look like locale files. It skips files over 1 MB and folders such as `node_modules`, `.git`, `dist`, `build`, and `vendor`.
- Set `WHALORY_AUTOLINT=0` to turn it off for a session, or `WHALORY_AUTOLINT=strict` to report warnings as well as errors.
- Without the plugin, you can add the same hook by hand. The script is `hook_lint.py`, in the skill's `scripts/` folder in every package; the Core Claude plugin also has it in `autolint/scripts/`. In Claude Code, put this in `.claude/settings.json` with the absolute path to the script ([Claude Code hooks](https://code.claude.com/docs/en/hooks)):

```json
{"hooks": {"PostToolUse": [{"matcher": "Write|Edit|MultiEdit",
  "hooks": [{"type": "command", "command": "python3",
             "args": ["/absolute/path/to/whalory/scripts/hook_lint.py"], "timeout": 30}]}]}}
```

- Cursor gets no hook by default. To add one, put a `postToolUse` entry in `.cursor/hooks.json` ([Cursor hooks](https://cursor.com/docs/hooks)):

```json
{"version": 1, "hooks": {"postToolUse": [{"matcher": "Write", "timeout": 30,
  "command": "python3 \"/absolute/path/to/whalory/scripts/hook_lint.py\""}]}}
```

  `hook_lint.py` answers Cursor in the `additional_context` field that Cursor's docs describe for this event (checked 2026-09-28). We haven't run it inside Cursor yet.
- Whalory Pro's editor rules package has these settings ready in its `hooks/` folder, plus one for Gemini CLI.
- On Windows, `python3` in these examples may need to be `python` or `py`; see [Python](README.en.md#python).

## Troubleshooting

| Problem | What to do |
|---|---|
| Whalory doesn't start by itself | Call it by name: `/whalory` or `/whalory:write` in Claude Code, `$whalory` in Codex, `/whalory:write` in Gemini CLI. Check that the folder is named exactly `whalory` and `SKILL.md` sits directly inside it. |
| claude.ai rejects the zip | Use the claude.ai zip. Its root must be the `whalory` folder, and code execution must be on. |
| `python3` isn't found on Windows | For the Claude Code plugin's tools, set its Python option: reinstall with `--config python=python`, or run `/plugin configure whalory`. The autolint hook and the other packages run `python3`; see [Python](README.en.md#python). The version must be 3.8 or later. |
| The tools don't appear | Check the Python command first, then the host's MCP list. Tool calls in Claude Code look like `mcp__plugin_whalory_whalory__lint_text`. |
| The script can't find a file | Write the full skill path; `scripts/...` doesn't work from your own folder. |
| We asked too much | Reply `write`, or start with "just write". Put lasting answers in the profile so we don't ask again. |
| We didn't ask and the text went wrong | Read the "Diagnosis:" line and fix that part in one sentence: "the channel is SMS." |
| The copy reads like a brochure | The brief had no materials. Send facts and ask again. |
| The English spelling is mixed | Set `variant` or `spelling` in the profile, then run `lint.py --lang en`. |
| The tone shifted | Either there's no profile, or it doesn't set the tone for that format. Fill in the format table in the profile. |
| The profile wasn't read | The "Diagnosis:" line says which profile we read. Put the file in the project root as `VOICE.md`, or paste it into the chat. |
| The task isn't in the index | Tell us what it's closest to. We'll build from the nearest playbook and say what changed in the note. |
| You want to learn it yourself | Say "teach me". You get the rule, a before-and-after example, and an exercise. Start with [writing craft](references/en/craft.md). |

Found a bug or have a question? Use the [contact page](https://whalory.com/en/contact), or open an issue in the public repository for a bug in Core.
