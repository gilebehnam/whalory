# Context detection

This file is step zero of every task. Before asking or writing, Whalory works out where it is and what it has been asked. It reads its own tools, the files at hand, and the request itself. The result is a context card. Whalory fills it silently, and only one line of it appears in the internal note. After this file, the [question gate](intake.md) decides whether a question is needed. This file has no rules for asking: the "Question bank" column of the route table only names the bank row of the task.

## Contents

- [Detection in four steps](#detection-in-four-steps)
- [Capability flags](#capability-flags)
- [Exploration budget](#exploration-budget)
- [Context card](#context-card)
  - [Risk level](#risk-level)
- [Signals to routes](#signals-to-routes)
  - [Out-of-scope genres](#out-of-scope-genres)
  - [High-risk words and industry cards](#high-risk-words-and-industry-cards)
- [Place names and format ids](#place-names-and-format-ids)
- [Output language, variant, and market](#output-language-variant-and-market)
- [Reader](#reader)
- [Delivery by host and intent](#delivery-by-host-and-intent)
- [Diagnosis note](#diagnosis-note)
- [The Whalory team](#the-whalory-team)
- [Worked examples](#worked-examples)
- [When detection is wrong](#when-detection-is-wrong)

## Detection in four steps

1. Capability: turn the flags on or off from the tools you have. Don't ask the user which assistant they use.
2. Exploration: if you can read files, look at what is next to you, within the short budget below.
3. Card: fill the twelve slots of the context card from the request, the attachments, the files, and the profile. A slot that stays unclear takes its default.
4. Route: find the row in [Signals to routes](#signals-to-routes) with the step rule. That row gives the playbook, the references, the output shape, and the quality check (QA). The question gate decides about asking.

Three slots of the card answer three of the [six questions](judgment.md#six-questions-before-writing): `reader` says who reads, `format/channel` says where it is read, and `industry/risk` says what risk it carries. The moment, the reader's state, and the action after reading come from the brief, the [question bank](intake.md#question-bank-by-task), or the channel default.

## Capability flags

Whalory runs inside many assistants, and each one has different tools. Don't guess the assistant's name or ask for it. Look at the tools you have.

| Flag | On when | What it changes |
|---|---|---|
| `fs_read` | A file-reading tool or a shell is available | Exploration; reading `VOICE.md` and `LEARNINGS.md` |
| `fs_write` | A tool that writes or edits files is available | Delivery in the file itself; saving the profile and the learnings |
| `exec` | A shell or code execution is available | QA by script: `python`, or `py -3` on Windows |
| `ask_tool` | A structured question tool is available, such as `AskUserQuestion` in Claude Code or `request_user_input` in Codex | The question format; [How each host asks](intake.md#how-each-host-asks) |
| `web` | A search tool or a web page reader is available | Checking limits, dates, and sources before writing |
| `interactive` | A person is there to read the answer and reply | Permission to ask; off means the `autonomous` host |
| `no_questions` | The user has set questions aside. Persian cues: «فقط بنویس», «بی‌سؤال», «سؤال نپرس», «سریع بنویس», or «بنویس» in reply to a question. English cues: "just write", "no questions", "don't ask", "write it quickly", or "write" in reply to a question | No questions come; the host and the delivery shape stay the same |
| `repo` | `fs_read` is on and the working folder has `.git`, `package.json`, `AGENTS.md`, `CLAUDE.md`, or `pyproject.toml` | Repository routes: microcopy, content files, delivery in the file |

`interactive` is off only when no one is there to answer:

- The request came from a run with no interface, such as `codex exec`, `claude -p`, or an API call. The Claude Code docs call `claude -p` a non-interactive run. In it, a permission request that no host can answer is denied. With `--permission-prompts none` or the `dontAsk` mode, the `AskUserQuestion` tool is also removed or denied (checked 2026-09-27, [docs](https://code.claude.com/docs/en/headless)).
- The input is JSON or a list of rows that a program sent, with no person behind it.
- The system text says the task is non-interactive, or the question tool was removed on purpose.
- Another agent called Whalory, and the answer goes back to that agent. In the Agent SDK, the `AskUserQuestion` tool isn't available to subagents (checked 2026-09-27, [docs](https://code.claude.com/docs/en/agent-sdk/user-input)).

What the user asks for doesn't turn `interactive` off. "Just write" in a chat only turns on `no_questions`, and the user still gets the copy and the note of a chat. «سریع» ("quick") is a flag only when it is about the process, as in «سریع بنویس» or «سریع، بی‌سؤال» ("write it quickly", "quick, no questions"). «ارسالِ سریع» ("fast shipping") inside the text of an ad is not a flag.

Invocation marks such as `$whalory` or `/whalory` only confirm what the flags already show.

## Exploration budget

Exploration only looks for signals; it never reads the whole project. Of the options below, take the first one you have. If the user named a file path, such as `locales/fa/messages.po`, skip exploration and open that file.

- With `fs_read` or a shell: take at most two actions, one listing of the folder root and one file-name search with the patterns below. Search the Persian and the English patterns together, in one pass. Exploration runs before the output language is known, and the locale files it finds are one of the inputs to that decision. All ten patterns count as one search. If the search tool can't expand braces, search the expanded patterns one after another; that is still one action.
- With no file access: skip exploration. The card is filled from the request and the attachments.

```
**/{fa,fa-IR,fa_IR}.{json,yml,yaml,toml,po,arb,ts,js,php,xlf,xliff}
**/*[._-]{fa,fa-IR,fa_IR}.{json,yml,yaml,arb,po,xlf,xliff}
**/{fa,fa-IR,fa_IR}/**/*.{json,po,php,yml,yaml,ftl}
**/values-fa*/strings.xml
**/fa.lproj/*.strings
**/{en,en-US,en_US,en-GB,en_GB}.{json,yml,yaml,toml,po,arb,ts,js,php,xlf,xliff}
**/*[._-]{en,en-US,en_US,en-GB,en_GB}.{json,yml,yaml,arb,po,xlf,xliff}
**/{en,en-US,en_US,en-GB,en_GB}/**/*.{json,po,php,yml,yaml,ftl}
**/values-en*/strings.xml
**/en.lproj/*.strings
```

These patterns catch the common layouts in any folder, from `locales/` and `i18n/` to `lang/`, `messages/`, and `translations/`. Examples: `src/i18n/fa.json`, `public/locales/fa/common.json`, `messages/fa.json`, `lang/fa/auth.php`, `config/locales/fa.yml`, `locales/fa/LC_MESSAGES/messages.po`, `translations/messages.fa.xlf`, `lib/l10n/app_fa.arb`, `res/values-fa/strings.xml`, and `fa.lproj/Localizable.strings`. The English patterns find the same layouts with `en`, `en-US`, and `en-GB`. Skip the `node_modules`, `vendor`, `build`, and `dist` folders. An Xcode string catalog with the `.xcstrings` extension has no language in its name; open it only when the user names it. Android's `res/values/` and iOS's `Base.lproj` hold the default strings, which may be English. Open them only for a task on English strings when no English locale file turns up.

| Signal | Meaning |
|---|---|
| `VOICE.md`, `voice.json`, `voice/VOICE.md` | Project profile; step 2 of the [profile lookup order](../SKILL.md#profile-lookup-order) |
| `LEARNINGS.md` next to `VOICE.md`, `voice/LEARNINGS.md` next to `voice/VOICE.md`, or `<brand>.LEARNINGS.md` next to `<brand>.md` | Earlier learnings; read them in every task |
| `.git`, `package.json`, `AGENTS.md`, `CLAUDE.md`, `pyproject.toml` | A repository; the `repo` flag |
| A file found by the patterns above | Microcopy in a repository; row 1 |
| A `content`, `docs`, or `posts` folder with `.md` or `.mdx` files | Site copy in a repository; row 2 |

Never open `.env` files, keys, passwords, or personal folders. Of the other files, look only at the names, except the profile, the learnings note, and any file the user named.

## Context card

Fill the card in your head and don't show it to the user. The keys are in English so they stay the same in evals and in JSON output.

```
host:            repo-agent | chat-tools | chat-plain | autonomous
inputs:          none | draft | image(product|ui|ad|other) | pdf/docx | transcript | csv/xlsx | url | locale-files | pptx
operation:       write | rewrite | shorten | lengthen | review | adapt/translate | name | strategize | teach | facilitate | measure
intent:          deliver | teach | review | strategize
format/channel:  caption@instagram | sms | ui@fa.json | listing@digikala | post@linkedin | ...
reader:          profile › channel default › industry default
language:        fa | en | bilingual | fa-AF | tg · <variant, BCP 47> · market: ir | us | uk | eu | intl | unknown · conversation: fa | en
industry/risk:   <industry> · low | medium | high
occasion:        none | festive | mourning | national
profile:         <source> · LEARNINGS: y/n
output:          chat-text | file-edit | table | csv | json | doc-via-other-skill
qa:              script | manual
```

| Slot | Filled from |
|---|---|
| `host` | The flags: `interactive` off means `autonomous`; `repo` means `repo-agent`; `exec` or file access means `chat-tools`; none of them means `chat-plain`. `no_questions` doesn't change the host |
| `inputs` | Attachments and pasted text; one look puts an image into one of the four kinds |
| `operation` | The verb of the request: «بنویس», «بهتر کن», «کوتاه کن», «نمره بده», «اسم بذار», «یاد بده»; in English, "write", "improve", "shorten", "score", "name", "teach me" |
| `intent` | Delivering copy, teaching, review, or strategy; "why" and "how" usually mean teaching |
| `format/channel` | The place name in the request and the [place-name table](#place-names-and-format-ids); with no place name, the [unstated genre](judgment.md#unstated-genre) |
| `reader` | The [reader rule](#reader) |
| `language` | [Output language, variant, and market](#output-language-variant-and-market): four values in one slot: output language, variant, market, and conversation language |
| `industry/risk` | The profile's industry or the topic of the request; the level comes from [Risk level](#risk-level) |
| `occasion` | The publishing date and the name of the occasion; occasions.md ([fa](fa/occasions.md), [en](en/occasions.md)) maps each occasion to one of these four values |
| `profile` | The [profile lookup order](../SKILL.md#profile-lookup-order); a starter profile has the source "starter" («آغاز») |
| `output` | The table in [Delivery by host and intent](#delivery-by-host-and-intent) |
| `qa` | `exec` on, or the MCP tools `lint_text` and `lint_file` connected, means script. If `exec` is off, the script run was denied, or Python was missing: [manual QA](../SKILL.md#manual-qa) |

### Risk level

| Level | When | What it changes |
|---|---|---|
| `high` | A [high-risk](#high-risk-words-and-industry-cards) industry or word; the row 19 layer | The risk layer, questions as the [gate](intake.md#decision-order) says, and "Risk: high" («خطر: بالا») in the diagnosis line |
| `medium` | One of three cases. The user's money is involved: a payment, a payment error, a refund, installments, or buying on credit. A food, cosmetic, hygiene, or herbal product invites a health claim. A hard message goes to a group of customers or to all of them | Read claims.md in the output language ([fa](fa/claims.md), [en](en/claims.md)). Give every money or health claim without evidence a confirm bracket: `[confirm: …]` in English, «[تأیید شود]» in Persian. Asking doesn't change, and the level stays out of the diagnosis line |
| `low` | Everything else | Nothing |

## Signals to routes

A row matches when all of its signals are on the card. **Signal precision** picks the main row. Take the steps in order: the earliest step with a matching row gives the main row. Within a step, the higher row wins.

0. Gate: row 15. If the request is an [out-of-scope genre](#out-of-scope-genres), Whalory steps aside and reads no further in the table. Brand copy that uses story or verse, such as a labeled story from a photo, is not one.
1. Attachment and input: a file, image, web address, or text that came with the request is the most precise signal. Rows 1, 2, 11, 10, 12, 5, 6, 7, 13, 9, and 8.
2. Intent: teaching, review, transcreation or bilingual copy, multi-part work, strategy, and brand voice. Rows 14, 16, 17, 22, 18, and 21.
3. Place and channel: row 3, a verb with a place name.
4. Fallback: row 4, only when no other row matches.

Rows 19 and 20 are layers: they sit on top of any main row and never take its place. A row number is an id and never changes; the order of the table is the order of the steps. When a teaching or review intent comes with an attachment, the playbook comes from the attachment's row and the output shape from the [delivery table](#delivery-by-host-and-intent).

The "Question bank" column only names the row of the [bank](intake.md#question-bank-by-task). Whether to ask, and how many questions, is set by the [decision order](intake.md#decision-order). "Complete input" means step 2 of that order: no question comes before the work.

The route column names the Persian pack (fa) and the English pack (en). Open the one for the [output language](#output-language-variant-and-market). When a row names only a fa file, use its method in English and write new examples. Never reuse its Persian examples as copy.

| Step | # | Signal | Route: playbook → references | Question bank | Output | QA |
|---|---|---|---|---|---|---|
| 0 | 15 | An [out-of-scope genre](#out-of-scope-genres), in any language: code, academic work, literary translation, legal drafting, or literature for its own sake. A labeled brand story, a rhymed slogan, or an ad jingle stays in scope | Outside Whalory | None | The assistant answers on its own; no diagnosis note | None |
| 1 | 1 | A repository with a locale file, or Persian or English strings in `.tsx`, `.jsx`, or `.vue` files | Microcopy in a code repository (in Whalory Pro) → fa: ux-strings.md (in Whalory Pro), [forms.md](fa/forms.md#ریزمتنِ-رابط) · en: ux-strings.md (in Whalory Pro), [forms.md](en/forms.md#ui-microcopy) | "UI microcopy and repo strings" | Edit the values in the same file; keys, `{placeholder}`, and ICU (International Components for Unicode) structure stay untouched; a summary of the change | `lint.py --format ui` on the changed values |
| 1 | 11 | A `.csv` or `.xlsx` file with an `sku`, title, description, or product code column | Bulk catalog from a spreadsheet (in Whalory Pro) → fa: bulk mode (in Whalory Pro), product-copy.md (in Whalory Pro) · en: bulk mode (in Whalory Pro) · [editor.md](editor.md#bulk-work) | "Bulk catalog"; the shape of the first reply is in [Bulk tasks](intake.md#bulk-tasks) | The same file format with new columns; the original columns stay untouched | `lint.py --csv-columns` on the new columns, with each row's key; one summary |
| 1 | 10 | A brief in `.pdf` or `.docx` | The starred slots of the [brief template](brief.md#template), then the playbook for that format | The row for that format | As that playbook says | Same |
| 1 | 5 | A product photo | Story from a photo (in Whalory Pro) or [Product description](playbooks-product.md#product-description) → fa: photo-to-story.md (in Whalory Pro), product-copy.md (in Whalory Pro) · en: [product blurb](en/forms.md#product-blurb), storytelling.md (in Whalory Pro) | "Story from a photo" | Copy and note | Script or manual |
| 1 | 6 | A screenshot of an app or a site | [UI microcopy](playbooks-web.md#ui-microcopy) in review mode → fa: [forms.md](fa/forms.md#ریزمتنِ-رابط) · en: [forms.md](en/forms.md#ui-microcopy) | Complete input | A table: element, current copy, suggestion, reason | Manual |
| 1 | 13 | A web address | Research before writing (in Whalory Pro) or [Style repair](playbooks-repair.md#style-repair) → fa: research.md (in Whalory Pro), [style-repair.md](fa/style-repair.md) · en: research.md (in Whalory Pro), [style-repair.md](en/style-repair.md) | Complete input | As that playbook says | Same |
| 1 | 9 | A voice transcript, meeting notes, or a voice message | Note cleanup (in Whalory Pro) → fa: [style-repair.md](fa/style-repair.md#تعمیرِ-یادداشتِ-جلسه) · en: [style-repair.md](en/style-repair.md#meeting-note-cleanup) | Complete input | Decision, task, owner, deadline | `compare.py` |
| 1 | 8 | Pasted text with «بهتر کن», «ویرایش کن», or «درستش کن»; in English, "improve this", "edit this", or "fix this" | [Style repair](playbooks-repair.md#style-repair) → fa: [style-repair.md](fa/style-repair.md) · en: [style-repair.md](en/style-repair.md) | "Style repair" | Copy and a three-line report | `compare.py` |
| 2 | 14 | Transcreation or bilingual copy (fa to en, en to fa): a text to rewrite for readers of the other language, or copy wanted in both | Transcreation and bilingual copy (in Whalory Pro) → transcreation.md (in Whalory Pro) · fa: english-copy.md (in Whalory Pro) · en: [style-guide.md](en/style-guide.md) | Complete input if the source text came with the request; otherwise "Base questions" | Two columns side by side, plus cultural notes | Lint on both columns, then `compare.py` for the facts: checklist (in Whalory Pro) |
| 2 | 16 | «یاد بده», «چطور», or «چرا این بهتره»; in English, "teach me", "how do I", or "why is this better" | Teaching and practice (in Whalory Pro) → fa: [craft.md](fa/craft.md) · en: [craft.md](en/craft.md) · roles.md (in Whalory Pro) | Complete input | A lesson: the rule, one before-and-after pair, one exercise | None |
| 2 | 17 | «نمره بده» or «بررسی کن»; in English, "score this" or "review this" | [Scoring and review](playbooks-repair.md#scoring-and-review) → [review.md](review.md), [editor.md](editor.md#scoring-rubric) | Complete input | A score table and fixes | Script or manual |
| 2 | 18 | Strategy, content plan, verbal identity, tone guide, campaign, name | Blog strategy (in Whalory Pro), Verbal identity from scratch (in Whalory Pro), Ad campaign (in Whalory Pro), Naming (in Whalory Pro) | The row for that task, in the [brief card](intake.md#task-level-and-question-cap). Verbal identity and a tone guide with no brand profile first get the three "Building a profile" questions: [decision order](intake.md#decision-order) | A decision document; docx or pptx through another skill | None |
| 2 | 21 | A [brand-building task](intake.md#definitions) with no [brand profile](intake.md#definitions): «صدای برندمون», «لحنِ ما چیه», «یه VOICE بساز»; in English, "our brand voice", "what's our tone", "make us a `VOICE.md`" | [Voice profile in three questions](playbooks-strategy.md#voice-profile-in-three-questions) → [profile-builder.md](profile-builder.md#route-2-short-interview), and for English brands the [English route](profile-builder.md#english-route) | "Building a profile" | A draft profile and the copy | Manual |
| 3 | 3 | A verb with a place name: «یه کپشن برای [کافه]», or "a caption for [my cafe]" | The playbook for that name; [place-name table](#place-names-and-format-ids) | The row for that task | Copy and note | Script or manual |
| 4 | 4 | The request has no place name and no other row matches: «یه متن برای محصولم», or "some copy for my product" | [Unstated genre](judgment.md#unstated-genre) | "Base questions" | The guessed route | Same |
| Layer | 19 | A high-risk industry or word: treatment, supplements, an aesthetics clinic, a fund, guaranteed or projected returns, crypto, a car or property pre-sale. English examples: `clinically proven`, `eco-friendly`, testimonials in the copy. [Full list](#high-risk-words-and-industry-cards) | Risk layer: Claim and license check (in Whalory Pro) → fa: [claims.md](fa/claims.md), regulation.md (in Whalory Pro), [ethics.md](fa/ethics.md) · en: [claims.md](en/claims.md), regulation.md (in Whalory Pro), [ethics.md](en/ethics.md); the regulation file follows the [market](#output-language-variant-and-market) | "Claim check" | As the main row says | Same |
| Layer | 20 | A date or an occasion in the request, or a publishing date in a sensitive period | Occasion layer: Occasion copy (in Whalory Pro) → fa: [occasions.md](fa/occasions.md) · en: [occasions.md](en/occasions.md) | [Defaults](intake.md#defaults): occasion | The tone of that occasion; humor 1 in mourning | Same |

Wherever `compare.py` isn't at hand, count the numbers, names, and conditions of the before and after texts by hand.

### Out-of-scope genres

Row 15 fires on any of these, in any language:

- code, code comments, or docstrings;
- academic essays, homework, or theses;
- fiction, poetry, or lyrics wanted as literature for their own sake: a short story, a poem, or a song with no marketing job;
- literary translation;
- legal drafting (binding clauses, contracts, non-disclosure agreements, the text of a privacy policy), and certified or word-for-word translation.

Whalory steps aside: the assistant answers in its own way, and no diagnosis note comes. Language alone never fires row 15, because English copy is in scope. Plain-language summaries and interface copy around legal text stay in scope as business documents. Examples are a cookie banner, a summary of the terms, and an email about a policy change. They go to Job posting and business documents (in Whalory Pro).

Brand copy that uses story or verse stays in scope, too. Row 15 never fires on these:

- Labeled stories: a story from a photo («قصه‌ی برچسب‌دار»), which is row 5 and Story from a photo (in Whalory Pro).
- Brand stories: a product story (in Whalory Pro), or an imagined scene for a post or an ad. It carries the "story" label («قصه»), as rule 1 of [SKILL.md](../SKILL.md#three-rules-that-never-change) requires.
- Rhymed slogans («سجع») and taglines with wordplay: [Tagline and slogan](playbooks-social.md#tagline-and-slogan).
- Jingle lines inside a radio or video ad: Radio or video ad script (in Whalory Pro).
- Occasion verse, or a quoted line of poetry, in a brand post: Occasion copy (in Whalory Pro).

The test is the job of the text. If it sells, introduces, or speaks for a brand, product, or offer, it is copy. If the person wants the story, poem, or song itself as the finished work, it is literature, and row 15 applies.

### High-risk words and industry cards

Row 19 turns on for a high-risk industry, whether the industry comes from the profile or from the request. The words in the table are examples: a request about one of these industries gets the same layer without them. Each industry card says which evidence to ask for, which claims get brackets, and when we refuse. If the task crosses the ethics line, Whalory writes no persuasive copy for it.

| Words in the request | Industry card | Ethics line |
|---|---|---|
| درمان، دارو، مکمل، پزشک · `treatment`, `medicine`, `supplement`, `doctor`, `cure`, `clinically proven` | fa: Health, treatment, and wellness (in Whalory Pro) · en: Health services and supplements (in Whalory Pro); US rules: health and supplement claims (in Whalory Pro) | fa: [Vulnerable readers](fa/ethics.md#خواننده‌ی-آسیب‌پذیر) · en: [Vulnerable readers](en/ethics.md#vulnerable-readers) |
| بوتاکس، فیلر، کلینیکِ زیبایی · `Botox`, `filler`, `aesthetics clinic` | fa: Beauty clinic (in Whalory Pro) · en: Aesthetics clinics (in Whalory Pro) | fa: [Fear and shame](fa/ethics.md#ترس-و-شرم) · en: [Fear and shame](en/ethics.md#fear-and-shame) |
| طبِ سنتی، عطاری، گیاهِ دارویی · `herbal remedy`, `traditional medicine` | fa: Traditional and herbal medicine (in Whalory Pro) · en: Health services and supplements (in Whalory Pro) | fa: [Honesty](fa/ethics.md#صداقت-ادعا-به-اندازه‌ی-شاهد) · en: [Honesty](en/ethics.md#honesty-claims-match-the-evidence) |
| سلامتِ روان، مشاوره، اضطراب، افسردگی · `mental health`, `therapy`, `anxiety`, `depression` | fa: Mental health (in Whalory Pro) · en: Health services and supplements (in Whalory Pro) | fa: [Vulnerable readers](fa/ethics.md#خواننده‌ی-آسیب‌پذیر) · en: [Vulnerable readers](en/ethics.md#vulnerable-readers) |
| سودِ تضمینی، وام، بیمه، کیفِ پول · `guaranteed returns`, `loan`, `insurance`, `wallet` | fa: Finance, payments, and insurance (in Whalory Pro) · en: Finance, investing, and crypto (in Whalory Pro) | fa: [Quick money](fa/ethics.md#بازاریابیِ-شبکه‌ای-و-پولِ-سریع) · en: [Get-rich-quick offers](en/ethics.md#get-rich-quick-and-multi-level-marketing) |
| صندوق، سرمایه‌گذاری، سهام، بورس، اوراق، سبدگردانی، سود یا بازدهیِ پیش‌بینی‌شده · `fund`, `investing`, `stocks`, `bonds`, `portfolio management`, `projected returns` | fa: Finance, payments, and insurance (in Whalory Pro), with licenses in Capital market and crowdfunding (in Whalory Pro) · en: Finance, investing, and crypto (in Whalory Pro); UK rules: financial promotions (in Whalory Pro); US rules: investment adviser ads (in Whalory Pro) | fa: [Honesty](fa/ethics.md#صداقت-ادعا-به-اندازه‌ی-شاهد) · en: [Honesty](en/ethics.md#honesty-claims-match-the-evidence) |
| رمزارز، سیگنال، طلا، ارز، ترید · `crypto`, `trading signals`, `gold`, `forex`, `trading` | fa: Crypto, gold, and currency courses (in Whalory Pro) · en: Finance, investing, and crypto (in Whalory Pro) | fa: [Quick money](fa/ethics.md#بازاریابیِ-شبکه‌ای-و-پولِ-سریع) · en: [Get-rich-quick offers](en/ethics.md#get-rich-quick-and-multi-level-marketing) |
| بازاریابیِ شبکه‌ای، عضوگیری، درآمد از خانه · `network marketing`, `multi-level marketing`, `income from home` | fa: Network marketing (in Whalory Pro) · en: no card; the ethics line decides | fa: [Quick money](fa/ethics.md#بازاریابیِ-شبکه‌ای-و-پولِ-سریع) · en: [Get-rich-quick offers](en/ethics.md#get-rich-quick-and-multi-level-marketing) |
| پیش‌فروشِ خودرو، ثبت‌نامِ خودرو · `car pre-sale`, `car registration` | fa: Cars and pre-sales (in Whalory Pro) · en: Industries not listed here (in Whalory Pro) | fa: [Fake urgency and scarcity](fa/ethics.md#فوریت-و-کمیابیِ-ساختگی) · en: [Fake urgency and scarcity](en/ethics.md#fake-urgency-and-scarcity) |
| پیش‌فروشِ ملک، آپارتمان یا ساختمان · `off-plan property`, `apartment pre-sale` | fa: Real estate and construction (in Whalory Pro), with the building pre-sale law of 1389 (Iranian calendar) in Building pre-sales (in Whalory Pro). Only its special rule for pre-sale ads is «[تأیید شود]» · en: Housing and employment ads (in Whalory Pro) | fa: [Fake urgency and scarcity](fa/ethics.md#فوریت-و-کمیابیِ-ساختگی) · en: [Fake urgency and scarcity](en/ethics.md#fake-urgency-and-scarcity) |
| کنکور، رتبه، تضمینِ قبولی · `entrance exam`, `exam rank`, `guaranteed admission` | fa: Entrance exams and test prep (in Whalory Pro) · en: Education outcomes (in Whalory Pro) | fa: [Fear and shame](fa/ethics.md#ترس-و-شرم) · en: [Fear and shame](en/ethics.md#fear-and-shame) |
| مهاجرت، ویزا، اعزامِ دانشجو · `immigration`, `visa`, `study abroad` | fa: Immigration and study abroad (in Whalory Pro) · en: Immigration services (in Whalory Pro) | fa: [Honesty](fa/ethics.md#صداقت-ادعا-به-اندازه‌ی-شاهد) · en: [Honesty](en/ethics.md#honesty-claims-match-the-evidence) |
| `eco-friendly`, `carbon neutral` (green claims) | en: Green products (in Whalory Pro); EU rules: green claims (in Whalory Pro) | fa: [Environment and green claims](fa/ethics.md#محیط‌زیست-و-ادعای-سبز) · en: [Green claims](en/claims.md#green-claims) |
| `testimonial`, `reviews` or star ratings quoted in the copy (endorsement rules); replying to a review is not this row | en: [Testimonials and reviews](en/claims.md#testimonials-and-reviews); US rules: endorsements (in Whalory Pro), reviews (in Whalory Pro); UK rules: advertising code (in Whalory Pro); EU rules: unfair commercial practices (in Whalory Pro) | fa: [Real people](fa/claims.md#آدم‌های-واقعی) · en: [Fake reviews and followers](en/ethics.md#fake-reviews-and-followers) |

From industries.md, ethics.md, and regulation.md, read only the card and the linked section, found by searching for its heading. These files are long, and you don't need to read them whole. The regulation file follows the market, not the language of the copy: see [Output language, variant, and market](#output-language-variant-and-market).

## Place names and format ids

The format id comes from this fixed list, and the same id goes to `lint.py --format`:

```
caption  story  reels  carousel  post  sms  otp  email  subject  push  ui  error  product
listing  landing  about  blog  ad  press  bot  reply  hard  deck  script  name  headline
```

In row 3, the place name decides the playbook. This table takes common words to a format id and a playbook. The colloquial phrasings of each task are in the [task index](playbooks.md#task-index), and close calls are in [Near-miss tasks](playbooks.md#near-miss-tasks). Each row lists the Persian words first and the English ones after the dot, so a request in either language reaches the same row.

A named place beats a generic word. On a marketplace, «آگهی» ("ad") means the listing: «یه آگهی برای آمازون» and «آگهیِ دیوار» go to `listing`. On LinkedIn, X, Threads, or Bluesky, «پست» ("post") means a social post, as in «یه پست برای لینکدین». A paid placement keeps the ad row: «تبلیغِ اینستاگرام», «آگهی در کانالِ تلگرام», «نردبانِ دیوار», or "sponsored post". «پست» or «پیج» with no platform named stays a caption.

| Words in the request | Format id | Playbook and reference |
|---|---|---|
| کپشن، پست، پیج، اینستا · caption, Instagram post | `caption`, `post` | [Caption](playbooks-social.md#caption); fa: [Instagram](fa/channels.md#اینستاگرام) · en: [Instagram](en/channels.md#instagram) |
| لینکدین، پستِ لینکدین · LinkedIn post | `post` | [Social post](playbooks-social.md#social-post), [LinkedIn](en/channels.md#linkedin) |
| توییت، ایکس، تردز، بلواسکای · tweet, X post, Threads post, Bluesky post | `post` | [Social post](playbooks-social.md#social-post); [X](en/channels.md#x), [Threads](en/channels.md#threads), [Bluesky](en/channels.md#bluesky) |
| پیامک، اس‌ام‌اس · text message, SMS | `sms` | [SMS](playbooks-messages.md#sms); fa: sms.md (in Whalory Pro) · en: sms-push.md (in Whalory Pro) |
| کدِ تأیید، رمزِ یک‌بارمصرف · verification code, one-time passcode | `otp` | [SMS](playbooks-messages.md#sms); fa: sms.md (in Whalory Pro) · en: one-time passcodes (in Whalory Pro) |
| ایمیل، خبرنامه، سری ایمیل · email, newsletter, email sequence | `email` | [Email](playbooks-messages.md#email), Email sequence (in Whalory Pro); en: email.md (in Whalory Pro) |
| ایمیلِ سرد، ایمیل به مشتریِ بالقوه · cold email | `email` | [Email](playbooks-messages.md#email), cold outreach (in Whalory Pro) |
| موضوعِ ایمیل · subject line | `subject` | [Email](playbooks-messages.md#email); fa: headlines.md (in Whalory Pro) · en: subject lines (in Whalory Pro) |
| اعلان، نوتیفیکیشن · push notification | `push` | No playbook of its own; the closest is [SMS](playbooks-messages.md#sms), as [When the task is not in the index](playbooks.md#when-the-task-is-not-in-the-index) says. fa: [channels.md](fa/channels.md#اعلانِ-اپ) · en: Push notifications (in Whalory Pro), [channel limits](en/channels.md#push-notifications) |
| دکمه، فرم، برچسب · button, form, label | `ui` | [UI microcopy](playbooks-web.md#ui-microcopy) |
| پیامِ خطا، صفحه‌ی خالی · error message, empty state | `error` | [Error, empty, and waiting states](playbooks-web.md#error-empty-and-waiting-states) |
| معرفیِ محصول، توضیحِ محصول · product description | `product` | [Product description](playbooks-product.md#product-description) |
| کافه‌بازار، مایکت، اپ‌استور، گوگل‌پلی، صفحه‌ی اپ در این فروشگاه‌ها · App Store listing, Google Play listing, app page on Cafe Bazaar and Myket | `listing` | [Product description](playbooks-product.md#product-description); fa: Cafe Bazaar and Myket (in Whalory Pro) · en: App Store listing (in Whalory Pro), Google Play listing (in Whalory Pro) |
| صفحه‌ی پرداخت، رفتن به درگاه، نتیجه‌ی پرداخت، ۴۰۴ · checkout page, payment result, 404 page | `error` or `ui` | [Error, empty, and waiting states](playbooks-web.md#error-empty-and-waiting-states); fa: Payment microcopy (in Whalory Pro) · en: Checkout and payment pages (in Whalory Pro) |
| درباره‌ی ما · about page | `about` | [About page](playbooks-web.md#about-page); fa: web-pages.md (in Whalory Pro) · en: about pages (in Whalory Pro) |
| جواب به مشتری، جواب به نظر · customer reply, reply to a review | `reply` | [Customer reply](playbooks-messages.md#customer-reply), Review replies on Google and map apps (in Whalory Pro) |
| تیتر، شعار، تگ‌لاین · headline, slogan, tagline | `headline` | [Tagline and slogan](playbooks-social.md#tagline-and-slogan) |
| تگ‌لاینِ پروداکت‌هانت · Product Hunt tagline | `headline` | [Tagline and slogan](playbooks-social.md#tagline-and-slogan), Product Hunt launch (in Whalory Pro). A whole launch, «معرفی در پروداکت‌هانت» or "Product Hunt launch", is row 22 and the Launch chain (in Whalory Pro) |
| یلدا، نوروز، محرم، تبریک، تسلیت · greetings, condolences | Depends on the channel | Occasion copy (in Whalory Pro); fa: [occasions.md](fa/occasions.md) · en: [occasions.md](en/occasions.md) |

Every id above comes from the fixed list; no id is new. Format ids are not channel ids. For `lint.py --channel`, an Iranian SMS panel is `sms`, and a sender outside Iran is `sms-intl`; the channel ids are in `data/channels/`.

## Output language, variant, and market

The `language` slot holds four values: the output language, the variant, the market, and the conversation language. Take these rules in order and stop at the one that decides the output language:

0. Explicit instruction: "in Farsi", «به انگلیسی», "bilingual", «دوزبانه».
1. Target channel, site, or locale file: a Digikala listing is fa-IR. Amazon.com is en-US. "Our UK site" is en-GB.
   - A locale file such as `fa.json` or `en-GB.json` is that locale when the request names it or it is the only locale file in play. When the repository has both, the request says which strings to work on; if it doesn't, the request language picks the file.
   - A Persian-only channel in `data/channels`, one with `region: "ir"`, decides fa only when the request names that platform, such as Digikala, Divar, Bale, or an Iranian SMS panel. Generic words such as SMS, text message, or email decide nothing.
   - A city or country sets the market, not the language. «برای مشتری‌های ایرانیِ فروشگاهمون تو لس‌آنجلس یه کپشن بنویس» stays fa, with the market `us`. Only a named English channel or site, such as "our US site", makes it en.
2. Materials: a rewrite or a review keeps the language of the supplied text. A transcreation request flips it.
3. Request language: the language the user writes in.
4. Profile: the profile's `language` and `variant`, then the defaults: Persian in fa-IR, or en-US when the language is English. This step decides when nothing above does, for example a JSON task from a pipeline that carries no text in either language.

`bilingual` means copy in both languages side by side, as in row 14.

**Variant.** It comes from the channel or the market, then the profile's `variant`, then the default (fa-IR for Persian, en-US for English). The market sets a variant only within the output language. An English text for Manchester is en-GB, while a Persian caption for Los Angeles stays fa-IR. Readers in Afghanistan or Tajikistan, or words such as «دری», «تاجیکی», and «خواننده‌ی افغان» ("Dari", "Tajik", "Afghan reader"), set the slot to `fa-AF` or `tg`: [Other Persian speakers](fa/conventions.md#فارسی‌زبانانِ-دیگر), Dari (in Whalory Pro), and Tajik (in Whalory Pro). For a language with no guide, see Languages without a guide (in Whalory Pro). English variants and their spelling are in [style-guide.md](en/style-guide.md#variants).

**Market.** Only claims and regulation use it. It comes from country cues (a city, a country, a currency, a local regulator), then the channel's region, then the profile, then `unknown`.

- `ir`, `us`, and `uk` are those countries. `eu` is copy aimed at the EU as a whole. `intl` is copy for readers in several markets at once.
- A channel with `region: "ir"` gives `ir` when the request names that platform, as in rule 1. A generic word such as SMS gives no market, and a channel with `region: "intl"` fixes none either.
- Persian output in the fa-IR variant counts as an Iran cue when nothing names another country. This keeps the v2 behavior, where every Persian task used the Iranian rules.
- Any other country, including a single EU member state such as Germany, is `unknown`, because Whalory has no file for its national rules. The note names the country in its [market line](#diagnosis-note).
- Ask about the market only when risk is `high` and no cue gives it: step 3 of the [decision order](intake.md#decision-order).

**Conversation language.** Questions and the diagnosis note use the language of the request, even when the copy is in the other language.

- The instruction decides it, not pasted material: «اینو بهتر کن» above an English paragraph is a Persian conversation about English copy.
- A request with no prose, such as JSON from a pipeline, takes the output language as its conversation language. That is the `lang` key, or the rules above.
- The card records it in the `language` slot as `conversation: fa` or `conversation: en`. A subagent that never sees the conversation reads it from there.

**Pack and regulation file.**

- The output language picks the pack: fa uses `references/fa/`, and en uses `references/en/`. Bilingual copy uses both. fa-AF and tg use `fa/` with other-languages.md (in Whalory Pro).
- The market picks the regulation file: `ir` uses the Persian regulation.md (in Whalory Pro), and `us`, `uk`, and `eu` use the English regulation.md (in Whalory Pro). Any other market gets the risk layer plus the bracket `[local rules to be confirmed]` («[قاعده‌ی محلی تأیید شود]» in Persian copy): Other markets (in Whalory Pro).

## Reader

The profile's reader comes first, then the channel default, then the industry default. Words such as «شرکت», «سازمان», «مناقصه», and «کارفرما» ("company", "organization", "tender", "client") make the reader a business. For Persian copy, the defaults then come from Industrial and B2B (in Whalory Pro). For English copy, the defaults come from Business buyers (B2B) (in Whalory Pro), the reader also from the B2B starter profile (in Whalory Pro), and the benchmark from B2B software (in Whalory Pro).

## Delivery by host and intent

| Host | Means |
|---|---|
| `repo-agent` | An assistant inside a repository that reads and writes files |
| `chat-tools` | A chat with tools, such as code execution or file creation, and no repository |
| `chat-plain` | A plain chat with no tools, including text pasted into another assistant |
| `autonomous` | A non-interactive run: a pipeline, an API, a batch job, or an agent that called Whalory |

| Host | Delivering copy | Teaching | Review | Strategy |
|---|---|---|---|---|
| `repo-agent` | Edit the file and summarize the change; drafts only in a temporary folder outside the repository | In the chat | A table in the chat | `docs/whalory/*.md` if asked; otherwise the chat |
| `chat-tools` | Copy and note; docx, pptx, and xlsx through an installed skill | In the chat | A table in the chat | A document through a document skill |
| `chat-plain` | Copy and note | In the chat | A table in the chat | A Markdown document |
| `autonomous` | A file, or JSON with the keys `text`, `assumptions`, `needs_verification`, and `context`. [The `needs_input` output](intake.md#needs_input-output) only when the input accepted it | The lesson in the same JSON, under `text` | The score in JSON | A Markdown file |

`no_questions` doesn't change this table. A user who wrote "just write" in a chat still gets the copy and the note of that host. The assumptions go at the top of the note.

## Diagnosis note

The internal note of every delivery starts with one line that sums up the card. With this line, the user can fix a wrong route in one sentence. The keyword follows the conversation language: «تشخیص:» in a Persian conversation, `Diagnosis:` in an English one.

```
تشخیص: [قالب و کانال] · [خواننده] · پروفایل: [منبع] · [پرسش] · آزمون: [اسکریپت یا دستی]
Diagnosis: [format and channel] · [reader] · Profile: [source] · [questions] · QA: [script or manual]
```

- The order of the parts is fixed. "Risk: high" («خطر: بالا») and "Occasion: [name]" («مناسبت: [نام]») appear only when they are on, before QA.
- "Profile" names the source: `VOICE.md`, the brand name in `~/.whalory/profiles/`, a starter profile's name followed by "(starter)" («(آغاز)»), or "default" («پیش‌فرض»).
- "Questions" takes one of these values:

| Persian | English | Means |
|---|---|---|
| «بی‌پرسش» | `no questions` | The draft came with no question |
| «پرسشِ تکمیلی» | `follow-up question` | The draft came first, with one or two questions at the end of the note |
| «یک پرسش»، «دو پرسش»، «سه پرسش» | `one question`, `two questions`, `three questions` | This many questions came before writing |
| «کارتِ بریف» | `brief card` | The strategic task started with a brief card |
| «فقط بنویس» | `just write` | The user set questions aside (`no_questions`); the assumptions sit at the top of the note |
| «خودکار» | `automated` | The host is `autonomous` |

- "QA" takes one of three values: «اسکریپت», «دستی», or «دستی (اسکریپت اجرا نشد)»; in English, `script`, `manual`, or `manual (script not run)`. A lint run through the MCP tools `lint_text` or `lint_file` counts as `script`.
- In JSON output, the same line goes under the `context` key.
- When the request names a country that has no rules file, so the market is `unknown`, a second line follows the diagnosis line. In English: `Market: unknown (Germany); local rules not checked.` In Persian: «بازار: نامعلوم (کانادا)؛ قاعده‌ی محلی بررسی نشد.» In JSON output, this line goes into `needs_verification`.

Examples:

- Caption: «تشخیص: کپشنِ اینستاگرام · مشتریِ تازه · پروفایل: cafe (آغاز) · پرسشِ تکمیلی · آزمون: دستی»
- Repository: «تشخیص: ریزمتنِ صفحه‌ی پرداخت در `fa.json` · خریدارِ وسطِ پرداخت · پروفایل: VOICE.md و LEARNINGS · بی‌پرسش · آزمون: اسکریپت»
- Automated: «تشخیص: پیامکِ ارسالِ سفارش · خریدار · پروفایل: پیش‌فرض · خودکار · آزمون: اسکریپت»
- English caption: `Diagnosis: Instagram caption · first-time customer · Profile: cafe (starter) · follow-up question · QA: manual`
- English repository: `Diagnosis: checkout microcopy in en.json · buyer mid-checkout · Profile: VOICE.md and LEARNINGS · no questions · QA: script`

## The Whalory team

Every Whalory task has a lead and a reviewer. The lead builds the draft, and the reviewer reads it with a second pair of eyes. In an assistant with a single model, the two roles are two separate passes. If the host has subagents, the reviewer can be a separate agent, briefed with the [handoff prompt](editor.md#handoff-prompt).

| Role | Work | Main references |
|---|---|---|
| Content lead | Goal, message, channel, and the order of work; whether any copy is needed at all | [judgment.md](judgment.md); copywriting: fa (in Whalory Pro), en (in Whalory Pro) |
| Writer | The draft, with the profile and the format of the task | Craft: [fa](fa/craft.md), [en](en/craft.md); forms: [fa](fa/forms.md), [en](en/forms.md) |
| Editor | Three editing passes, lint, and the score | [editor.md](editor.md), [review.md](review.md); style repair: [fa](fa/style-repair.md), [en](en/style-repair.md) |
| Researcher | Materials, sources, claims, and regulation | [gathering.md](gathering.md); research: fa (in Whalory Pro), en (in Whalory Pro); claims: [fa](fa/claims.md), [en](en/claims.md) |
| Voice keeper | Profile, glossary, `LEARNINGS.md`, and a consistent tone | [voice-profile.md](voice-profile.md), [profile-builder.md](profile-builder.md) |
| Interface writer | Buttons, errors, forms, and locale-file strings | UI microcopy: [fa](fa/forms.md#ریزمتنِ-رابط), [en](en/forms.md#ui-microcopy); locale strings: fa (in Whalory Pro), en (in Whalory Pro) |

| Task family | Lead | Reviewer | What the reviewer looks for |
|---|---|---|---|
| Short everyday copy: caption, SMS, product description, reply | Writer | Editor | Machine patterns, length, the closing call to action |
| Microcopy and repository strings | Interface writer | Voice keeper | One word for one concept, the address, intact placeholders |
| Rewriting and repairing copy | Editor | Researcher | No number, name, or condition lost or changed |
| Articles, site pages, SEO copy | Writer | Search specialist | The main question in the title and the first paragraph; real subheadings |
| Hard messages and high-risk industries | Content lead | Researcher | Claims, licenses, the skeleton of the message |
| Campaigns, strategy, verbal identity | Content lead | Voice keeper | Every channel speaks with one voice and makes the same claims as the landing page |
| Naming and ideation | Facilitator | Content lead | Fit with the brief, screening, legal risk |
| Profile and brand voice | Voice keeper | Editor | A benchmark text with no lint errors |
| Research and measurement | Researcher | Content lead | Sources, sample size, unsupported claims |
| Review and scoring | Editor | Voice keeper | A score against a fixed rubric; taste is not the measure |

- Don't narrate the roles to the user. They get one output; the roles only set the order of work and the reviewer's eye.
- The reviewer sees only the materials, the profile, and the copy itself, never the writer's reasons: [two-agent work](editor.md#two-agent-work).
- A "fabrication" or "unsupported claim" finding sends the copy back. A taste finding goes only into the note.

## Worked examples

Nine full examples, each with the card, the route, the questions, and the diagnosis line, are in [router-examples.md](router-examples.md). When you're torn between two rows or two decisions, read the closest example.

- [1. Cafe caption in a plain chat](router-examples.md#1-cafe-caption-in-a-plain-chat)
- [2. Checkout microcopy in a repository](router-examples.md#2-checkout-microcopy-in-a-repository)
- [3. Product photo in claude.ai](router-examples.md#3-product-photo-in-claudeai)
- [4. Automated SMS from an API](router-examples.md#4-automated-sms-from-an-api)
- [5. Beauty clinic, high risk](router-examples.md#5-beauty-clinic-high-risk)
- [6. Repairing a long text in Claude Code](router-examples.md#6-repairing-a-long-text-in-claude-code)
- [7. Yalda campaign across channels](router-examples.md#7-yalda-campaign-across-channels)
- [8. English tagline for a Berlin bakery](router-examples.md#8-english-tagline-for-a-berlin-bakery)
- [9. "Just write" in a chat](router-examples.md#9-just-write-in-a-chat)

## When detection is wrong

- The user fixes it in one sentence, such as «منظورم پیامک بود» ("I meant an SMS"). Change the card and write again from the right row.
- Don't defend the earlier guess, and don't apologize at length. One line is enough: «درست شد: پیامکِ خدماتی.» ("Fixed: transactional SMS.")
- Some mistakes can recur, such as «درخواستِ بی‌قالب در این برند یعنی پستِ کانالِ بله» ("for this brand, no format means a Bale channel post"). Add a row to `LEARNINGS.md` for them. After the second time, move the rule into the profile itself. The rule is in [Mistakes](judgment.md#mistakes).
- If `fs_write` is off, give the user the text of that row so they can add it to the brand's note themselves.
