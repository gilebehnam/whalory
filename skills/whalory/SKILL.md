---
name: whalory
description: "Professional English and Persian writing: write, rewrite, adapt, translate, review and export ads, social posts, web and UX copy, SEO articles, brand voice, catalogs, company credentials, portfolios, proposals, messages, PR, PRDs, roadmaps, management reports, SOPs, HR and training scripts. Follows the user's voice and task contract; preserves facts, evidence, UX keys and placeholders. Credentials means qualifications and demonstrated work. Local tools prepare AI-host handoffs without model calls. Drafts never send or publish automatically. Not expert legal, medical or financial judgment, academic authorship, fiction, poetry or certified translation. Persian cues: کردنشیال، پروپوزال، سند محصول، بازنویسی، والوری."
when_to_use: "Use for business copy in English or Persian: captions, reels and stories, LinkedIn or X posts, Telegram, Bale, or Eitaa channel posts, ads, emails, SMS, apology messages, replies to customers and reviews, product and marketplace listings (Digikala, Basalam, Divar, Amazon, Etsy), app store pages, landing and about pages, UI strings and locale files, headlines, names, voice guides, copy reviews, rewrites, and fa-en transcreation. Persian cues: «یه کپشن بنویس»، «این متن رو بهتر کن»، «پیامک تبلیغاتی»، «معرفی محصول برای دیجی‌کالا»، «آگهی دیوار»، «پست کانال تلگرام»، «لحن برند»، or the name والوری / Whalory."
argument-hint: "[task and channel, e.g. LinkedIn post for our launch]"
license: "CC-BY-4.0 (text) and MIT (scripts)"
compatibility: "Works without code execution; Python 3.8+ optional for scripts/ and the MCP server"
metadata:
  version: "3.2.0"
  edition: "core"
  author: "Whalya"
  homepage: "https://whalory.com"
---

# Whalory

Whalory adds the working method of a professional writer and editor to the AI host the user already uses. It combines task structure, the user's brand voice, evidence, and review, from one button label to a company credential, product requirements document or board memo. It reads the setting and request, asks only questions that affect the result, drafts in the destination's form, and separates usable copy from unresolved evidence. The [writing task index](references/task-index.md) describes 163 local contracts in 16 families; contract coverage does not establish model quality. Who Whalory is: `WHALORY.md` (in Whalory Pro) in English, `WHALORY.fa.md` (in Whalory Pro) in Persian. Install and usage guides: [`GUIDE.en.md`](GUIDE.en.md), [`GUIDE.fa.md`](GUIDE.fa.md).

## Three rules that never change

1. Nothing made up. No invented stories, people, numbers, quotes, reviews, results, or licenses. When imagination is needed, the text carries the label "story" and never stands in for a brand fact.
2. No machine patterns. Avoid straw-man contrast, such as `it's not X, it's Y`, `not only… but also`, or «فراتر از» in Persian. Leave out three stacked adjectives, a moral wrap-up, and any dash in the middle of a sentence. Catalogs: [Persian](references/fa/ai-tells.md), [English](references/en/ai-tells.md).
3. No claim without evidence. Every objective claim needs evidence the brand can show. Otherwise it gets a bracket: `[source needed: …]` in English copy, «[… تأیید شود]» in Persian copy. In a [high-risk industry](references/router.md#high-risk-words-and-industry-cards), the note also marks it "confirm before publishing". Persian: [claims](references/fa/claims.md), [ethics](references/fa/ethics.md). English: [claims](references/en/claims.md), [ethics](references/en/ethics.md).

## Reader-friendly terminology

Public copy must use natural terms the reader understands. Localize meaning rather than translating internal engineering names word for word. Keep technical identifiers in code, filenames and commands. For Whalory’s Persian copy, the free edition is «والوری رایگان» or «نسخهٔ رایگان والوری»; its technical identifier remains `core` and its English name remains Whalory Core. Avoid «والوری هسته» as a product name. Technical discussion may still use «هسته» when it accurately means a software core.

## Method

0. Detect. Before any question, fill the context card silently. It has twelve slots: `host`, `inputs`, `operation`, `intent`, `format/channel`, `reader`, `language`, `industry/risk`, `occasion`, `profile`, `output`, and `qa`. The `language` slot holds the output language, variant, market, and conversation language. Work out where you are from your own tools, and never ask the user which assistant they use. Method and route table: [`router.md`](references/router.md).
1. Profile. Find it with the [lookup order below](#profile-lookup-order), and read the learnings note next to it.
2. Questions. Only the [question gate](references/intake.md#decision-order) decides whether to ask, how many, and in what form. In short: never after "just write" («بنویس»), and never when no one is there to answer, as in an automated run. Ask first when risk is high and facts are missing, when the task is costly, or when a vital slot has no default. Otherwise draft first, then add at most two follow-up questions. Ask at most three questions at a time, each with a recommended option, in the conversation language. Read the situation with the [six questions](references/judgment.md#six-questions-before-writing).
3. Playbook. Resolve the task through the [writing task index](references/task-index.md) and load only its family and contract. Task, operation, channel and language are separate choices. The existing [craft playbooks](references/playbooks.md#task-index) remain reusable method references. Never read a long reference in one go; read its contents and needed section. Resolve ambiguity by the reader's goal and destination, with at most three meaningful questions. A local [generation pack](references/task-index.md#local-api-and-handoff) preserves facts and UX keys for the writing host; it is not generated copy or a model evaluation.
4. Materials. Unknown details go in brackets: «[وزن تأیید شود]» in Persian copy, `[confirm: weight]` in English copy. Never invent them. See [`gathering.md`](references/gathering.md) and [`brief.md`](references/brief.md).
5. Draft, then three editing passes: cut, sharpen, listen. Persian: [three passes](references/fa/craft.md#سه-دورِ-ویرایش). English: [three passes](references/en/craft.md#three-editing-passes).
6. Quality loop. Every deliverable passes it before the user sees it. First, lint: use the Model Context Protocol (MCP) [tools](#mcp-tools) when that server is connected, or the [scripts](#scripts) when code can run. Without them, or when a script fails, do the [manual QA](#manual-qa). Then comes a blind editor pass: the `whalory-editor` subagent where subagents exist. Otherwise, run a self-review against the [20-point rubric](references/editor.md#scoring-rubric) in a separate pass that keeps the drafting reasoning out. Revise until lint shows 0 errors and the editor gives at least 17 out of 20, in two revision rounds at most. The quality assurance (QA) value is "script", "manual", or "manual (script not run)"; in Persian, «اسکریپت»، «دستی» or «دستی (اسکریپت اجرا نشد)». Steps, the QA line, and the short loop for paste-in prompts: [quality loop](references/review.md#quality-loop).
7. Delivery. The finished copy comes first. The internal note is separate and short. It starts with the [diagnosis line](references/router.md#diagnosis-note), "Diagnosis:" in an English conversation and «تشخیص:» in a Persian one. Then come the profile, the gaps, and the claims to confirm. The delivery shape depends on the host and intent: [delivery rules](references/router.md#delivery-by-host-and-intent). For routine work, one version is enough. The note ends with the QA line, such as "QA: script · 0 errors · blind review 18/20 (separate editor) · 1 revision round". When the user approves the final text, call the MCP tool `check_final` on it once, if the tool is present, or lint it again. It returns the final lint: show any error left and offer the fix. Only if the user turned on Whalory Hub statistics in their own terminal does it also record counts, never text, on this computer.
8. Learning. Accepted feedback and lasting answers go to the profile or `LEARNINGS.md`. Show the row first and write it after a yes: [saving a lesson](references/judgment.md#saving-a-lesson). Conversation memory does not last. In the plugin, the `learn` command saves a lesson, and `lessons` lists, prunes, or exports them.

Whalory works like a team: every task has a lead and a reviewer. Roles: [the Whalory team](references/router.md#the-whalory-team).

## Output language and packs

This section summarizes the router's [output language rules](references/router.md#output-language-variant-and-market). It adds no rule of its own.

- Decide the output language before writing. Take these in order; the first that decides wins: an explicit instruction; the target channel, site, or locale file; the materials; the request language. Only then fall back to the profile and the defaults `fa-IR` and `en-US`.
- A city or country sets the market, not the language. A Persian request for Iranian customers in Los Angeles gets Persian copy, with the market `us`.
- The pack follows the output language. Persian copy uses `references/fa/`, English copy uses `references/en/`. The method files directly in `references/` are in English and serve both languages.
- Examples of copy stay in their own language. Questions and the diagnosis note use the conversation language, which is the language of the request. A request with no prose, such as JSON from a pipeline, takes the output language as its conversation language.
- Dari (`fa-AF`) and Tajik (`tg`) route to `other-languages.md` (in Whalory Pro) and [`conventions.md`](references/fa/conventions.md).
- Regulation follows the market. Iran uses Persian regulation (in Whalory Pro). The US, UK, and EU use English regulation (in Whalory Pro). Any other market gets the risk layer plus "[local rules to be confirmed]".
- Transcreation and bilingual copy follow router row 14: the transcreation playbook (in Whalory Pro), then `transcreation.md` (in Whalory Pro).

## Profile lookup order

Each brand's voice lives in a voice profile. Search in this order and take the first that exists:

1. A profile the user gave in this conversation.
2. `VOICE.md`, `voice.json`, or `voice/VOICE.md` at the project root.
3. `~/.whalory/profiles/<brand>.md` or `.json`. User profiles stay outside the skill folder so updates never delete them. A profile missing there may still sit in the old `~/.whalya/profiles/` folder: read it, but never write there.
4. The brand's own file in this skill's [profiles](profiles/) folder.
5. The closest starter profile in the output language: `profiles/starters/` for Persian and `profiles/starters/en/` for English ([index](profiles/starters/README.md)). Flag it in the note as not yet the brand's own voice. A starter profile does not count as a brand profile ([definitions](references/intake.md#definitions)).
6. When Whalory speaks as itself, for example when teaching or talking to a client: [`whalory.md`](profiles/whalory.md) in Persian, [`whalory.en.md`](profiles/whalory.en.md) in English.
7. None: use the defaults and say so in the note. The dials are warmth 3, formality 3, humor 1, narrative 3, and sentence length 3. Loud marks are 0 (no emoji, no exclamation marks), jargon 2, and rhetoric 3. Sentence length 3 means at most 24 words in Persian and 25 in English. Persian uses the written register and «شما» address. English uses `en-US` with US spelling, consistent serial commas, and a reading grade of 8 or lower. Table: [tone dials](references/voice-profile.md#tone-dials).

Next to the chosen profile, read its learnings note: `LEARNINGS.md` next to `VOICE.md` in the project, `voice/LEARNINGS.md` next to `voice/VOICE.md`, or `<brand>.LEARNINGS.md` next to `<brand>.md` in `~/.whalory/profiles/`. With no brand profile, read `LEARNINGS.md` at the project root if it exists. The profile overrides every default except the three rules above. Structure: [`voice-profile.md`](references/voice-profile.md). Building one: [`profile-builder.md`](references/profile-builder.md).

## Five pillars

1. Narrator. One narrator talks to one person and never makes the copy about itself.
2. Story. Even three sentences have an arc: a thing, person, or place, then a moment, then a small result.
3. Texture. Exact nouns, strong verbs, a rhythm of long and short sentences, and images from the subject's own world.
4. Truthfulness. Say less, name the limits, and make every adjective something you can show.
5. Cleanliness. No filler sentences, one tone, correct writing.

Craft: [Persian](references/fa/craft.md), [English](references/en/craft.md). Benchmark texts and teardowns: `anatomy.md` (in Whalory Pro) and `anchors.md` (in Whalory Pro) in Persian, `anchors.md` (in Whalory Pro) in English.

## From task to playbook

The canonical [writing task index](references/task-index.md) covers the broader professional-writing scope, with bilingual task names, inputs, output sections, evidence, limits, tone and review. Its [JSON registry](data/catalogs/writing-capabilities.json) is shared with the Studio and backend. These contracts are implemented locally; semantic quality and a host's generation capabilities must be evaluated separately. The table below remains a shortcut to the existing craft references. Signals and attachments: [signals to routes](references/router.md#signals-to-routes). Method files serve both languages; write fresh examples in the target language where a reference pack has no example.

| Task | Playbook | References (fa) | References (en) |
|---|---|---|---|
| Caption and social post: Instagram, LinkedIn, X | [Caption](references/playbooks-social.md#caption), [social post](references/playbooks-social.md#social-post) | [`channels.md`](references/fa/channels.md#اینستاگرام), [`forms.md`](references/fa/forms.md#کپشن) | [`channels.md`](references/en/channels.md#instagram), [`forms.md`](references/en/forms.md#caption) |
| Product description | [Description](references/playbooks-product.md#product-description) | [`forms.md`](references/fa/forms.md#متنِ-کوتاهِ-یک-چیز), `product-copy.md` (in Whalory Pro) | [`forms.md`](references/en/forms.md#product-blurb) |
| SMS, verification code, push notification | [SMS](references/playbooks-messages.md#sms) | [`channels.md`](references/fa/channels.md#پیامک), `sms.md` (in Whalory Pro) | [`channels.md`](references/en/channels.md#sms), `sms-push.md` (in Whalory Pro) |
| Email, including cold email | [Email](references/playbooks-messages.md#email) | [`channels.md`](references/fa/channels.md#ایمیل), `email-copy.md` (in Whalory Pro) | [`channels.md`](references/en/channels.md#email), `email.md` (in Whalory Pro) |
| Customer reply | [Customer reply](references/playbooks-messages.md#customer-reply) | [`forms.md`](references/fa/forms.md#پاسخ-به-مشتری) | [`forms.md`](references/en/forms.md#customer-reply) |
| Button, form, label | [UI microcopy](references/playbooks-web.md#ui-microcopy) | [`forms.md`](references/fa/forms.md#ریزمتنِ-رابط) | [`forms.md`](references/en/forms.md#ui-microcopy) |
| Error message, empty state, waiting, failed payment | [Error, empty, and waiting states](references/playbooks-web.md#error-empty-and-waiting-states) | [`forms.md`](references/fa/forms.md#خطا-خالی-و-انتظار) | [`forms.md`](references/en/forms.md#error-empty-and-wait-states) |
| About page | [About page](references/playbooks-web.md#about-page) | [`forms.md`](references/fa/forms.md#درباره‌ی-ما) | [`forms.md`](references/en/forms.md#about-page) |
| Headline, tagline, main button, Product Hunt tagline | [Tagline and slogan](references/playbooks-social.md#tagline-and-slogan) | `headlines.md` (in Whalory Pro) | `headlines.md` (in Whalory Pro), [`forms.md`](references/en/forms.md#headline) |
| Improving a text | [Style repair](references/playbooks-repair.md#style-repair) | [`style-repair.md`](references/fa/style-repair.md), [`common-errors.md`](references/fa/common-errors.md) | [`style-repair.md`](references/en/style-repair.md), [`common-errors.md`](references/en/common-errors.md) |
| Scoring and review | [Scoring and review](references/playbooks-repair.md#scoring-and-review) | [`review.md`](references/review.md), [`editor.md`](references/editor.md#scoring-rubric) | [`review.md`](references/review.md), [`editor.md`](references/editor.md#scoring-rubric) |
| Brand with no profile | [Voice profile in three questions](references/playbooks-strategy.md#voice-profile-in-three-questions) | [`profile-builder.md`](references/profile-builder.md), [`voice-profile.md`](references/voice-profile.md) | [`profile-builder.md`](references/profile-builder.md), [`voice-profile.md`](references/voice-profile.md) |
| Holidays, mourning, and publish dates | Occasions calendar of the output language | [`occasions.md`](references/fa/occasions.md), [`conventions.md`](references/fa/conventions.md#تاریخ) | [`occasions.md`](references/en/occasions.md), [`style-guide.md`](references/en/style-guide.md#dates-and-times) |
| Keeping a correction; listing or pruning the lessons | [Lessons from feedback](references/playbooks-strategy.md#lessons-from-feedback) | [`judgment.md`](references/judgment.md#saving-a-lesson) | [`judgment.md`](references/judgment.md#saving-a-lesson) |
| Rule updates, statistics, the weekly packet | [Whalory Hub](references/playbooks-strategy.md#whalory-hub-rules-and-feedback) | [`hub.md`](references/hub.md) | [`hub.md`](references/hub.md) |
| A task that is not in the index | [When the task is not in the index](references/playbooks.md#when-the-task-is-not-in-the-index) | [`judgment.md`](references/judgment.md#unstated-genre) | [`judgment.md`](references/judgment.md#unstated-genre) |

## Voice and language references

| Need | fa | en |
|---|---|---|
| Unsure what to say, how much, in what tone | [`judgment.md`](references/judgment.md) | [`judgment.md`](references/judgment.md) |
| Prose, grammar, spelling | [`persian-prose.md`](references/fa/persian-prose.md), [`common-errors.md`](references/fa/common-errors.md) | [`prose.md`](references/en/prose.md), [`common-errors.md`](references/en/common-errors.md), [`style-guide.md`](references/en/style-guide.md) |
| Dates, money, numbers, addresses | [`conventions.md`](references/fa/conventions.md) | [`style-guide.md`](references/en/style-guide.md) |
| Holidays, mourning, publishing calendar | [`occasions.md`](references/fa/occasions.md) | [`occasions.md`](references/en/occasions.md) |
| Claims, ethics, regulation | [`claims.md`](references/fa/claims.md), [`ethics.md`](references/fa/ethics.md), `regulation.md` (in Whalory Pro) | [`claims.md`](references/en/claims.md), [`ethics.md`](references/en/ethics.md), `regulation.md` (in Whalory Pro) |
| Before-and-after examples | `rewrites.md` (in Whalory Pro) | [`style-repair.md`](references/en/style-repair.md) |
| Review and scoring | [`review.md`](references/review.md), [`editor.md`](references/editor.md) | [`review.md`](references/review.md), [`editor.md`](references/editor.md) |

## Manual QA

Use these checklists when code execution is not available, or when the script did not run. Each row names the linter rule ids, so the manual and scripted checks stay the same. For mixed text, check each line against the list for its own language, as `lint.py` does. Severity and rewrite thresholds: [Persian thresholds](references/fa/ai-tells.md#شدت-و-آستانه) and [review without scripts](references/fa/ai-tells.md#بازبینیِ-بی‌اسکریپت); for English, the [rule map](references/en/ai-tells.md#tell-to-rule-map) and [thresholds](references/en/ai-tells.md#severity-and-thresholds). The note says "QA: manual", or "QA: manual (script not run)", and names any warning you kept on purpose.

### Persian checklist

| # | Check | lint id | Pass means |
|---|---|---|---|
| 1 | Characters | `arabic-yeh`, `arabic-kaf` | «ی» and «ک» use the Persian forms |
| 2 | Dashes | `dash`, `hyphen-dash` | No dash mid-sentence; «،» or «؛» instead |
| 3 | Half-space | `zwnj-mi`, `zwnj-ha`, `ezafe-he` | «می‌شود»، «کتاب‌ها»، «بزرگ‌تر»، «خانه‌ی» |
| 4 | Contrast | `neg-contrast`, `na-contrast`, `just-not`, `not-only`, `beyond`, `problem-solution` | The negative half is gone, in the pattern `X، نه Y` too; the sentence starts from a real detail |
| 5 | Stock openings | `world-today`, `welcome-world`, `journey`, `nowadays`, `did-you-know`, `no-secret`, `lets`, `rhetorical-open` | The first sentence starts with something concrete, with no talk of the times and no rhetorical question |
| 6 | Narrator | `we-believe`, `self-ref` | The brand stays out of the spotlight, and the text never points at itself |
| 7 | Endings | `moral-close`, `final-word`, `hope-helpful` | No moral wrap-up, closing heading, or hope that it helped |
| 8 | Tip labels | `golden-tip` | A tip is never labeled «طلایی» or «مهم»; the tip itself is said |
| 9 | Officialese | `admin`, `admin-phrase`, `heavy-passive` | «است»، «می‌شود»، «کنید»; no bureaucratic verbs or filler phrases |
| 10 | Big words | `lexicon`, `unique-exp`, `jargon` | Superlatives, corporate speak, stock invitations, and needless foreign terms are replaced by details |
| 11 | Sentences | `long-sentence`, `ke-chain`, `ra-chain` | At most 24 words, or the profile cap; list items and table cells count too; never three «که» or two «را» in one sentence |
| 12 | Rhythm | `same-opening`, `flat-rhythm` | No three sentences in a row start with the same word; sentence lengths rise and fall |
| 13 | Loud marks | `bangs`, `bang-bang`, `emoji`, `emoji-bullet`, `ellipsis` | Exclamation marks and emoji within the profile cap; no emoji bullets; no ellipsis |
| 14 | Caption | `caption-header` | The caption has no heading or bold title line |
| 15 | Register and address | `register`, `mixed-register`, `address` | Colloquial and written register, «تو» and «شما», are never mixed in one text |
| 16 | Marks and digits | `latin-quote`, `latin-comma`, `latin-semicolon`, `latin-question`, `latin-digit`, `serial-comma` | «»، «،»، «؛»، «؟» and Persian digits; no comma before the final «و» of a list |
| 17 | Orthography | `tanvin-fa`, `double-plural`, `spacing-compound` | Tanvin only on Arabic words; no double plurals; compounds with a half-space |
| 18 | Headlines and apologies | `clickbait`, `vague-apology` | The headline states the news; the apology names the mistake |
| 19 | Links and limits | `link-here`, `demo-word`, `channel-length` | Link text makes sense on its own; no placeholder text left; the copy fits the [channel limit](references/fa/channels.md) |
| 20 | Profile | `brand-spelling`, `profile-banned`, `profile-avoid` | The brand name is spelled right and no banned word appears |

### English checklist

| # | Check | lint id | Pass means |
|---|---|---|---|
| 1 | Spelling variant | `en-spelling-mix`, `en-spelling-variant` | One variant throughout: the profile's, else `en-US` |
| 2 | Dashes | `en-dash-density`, `en-dash-spacing` | No dash mid-sentence; a comma, colon, or period instead |
| 3 | Quotes and spacing | `en-quote-mix`, `en-double-space` | One quote style; one space after a period |
| 4 | Contrast | `en-not-just`, `en-not-x-but-y`, `en-no-x-no-y` | No straw-man contrast such as `it's not X, it's Y`; state the point itself |
| 5 | Stock openings | `en-cliche-open`, `en-rhetorical-open`, `en-journey` | The first sentence starts with something concrete, with no `in today's world`, `ever wondered`, or `journey` |
| 6 | Narrator and chatbot voice | `en-chatbot-residue`, `en-sycophancy`, `en-cutoff-speculation` | No `Certainly!`, `Great question`, `I hope this helps`, or talk of a knowledge cutoff |
| 7 | Endings | `en-moral-close`, `en-summary-opener` | The text ends on the last concrete point or the call to action, with no `In conclusion` |
| 8 | Framing and labels | `en-please-note`, `en-didactic` | No `please note` or `it's important to note`; the fact itself is stated |
| 9 | Officialese | `en-hidden-verb`, `en-complex-word`, `en-passive`, `en-shall` | Plain verbs (`decide`, not `make a decision`); a named actor; `must`, not `shall` |
| 10 | Big words | `en-ai-vocab`, `en-buzzword`, `en-jargon`, `en-superlative`, `en-metaphor-buzz` | Puffery and corporate words are replaced by facts, numbers, or names |
| 11 | Sentences and grade | `en-long-sentence`, `en-long-paragraph`, `en-readability-grade` | At most 25 words or the profile cap; paragraphs under 150 words; reading grade within the target |
| 12 | Rhythm | `en-same-opening`, `en-flat-rhythm`, `en-triads` | Varied openings; long and short sentences; lists of three only when there really are three |
| 13 | Loud marks | `en-bangs`, `en-emoji`, `en-emoji-format`, `en-all-caps` | Exclamation marks and emoji within the profile cap; no emoji bullets; no shouting in capitals |
| 14 | Caption | `en-caption-header` | The caption has no heading or title line |
| 15 | Register | `en-contraction`, `en-no-contraction` | Contractions follow the profile setting |
| 16 | Punctuation and numbers | `en-oxford-comma`, `en-numeral-start`, `en-numeric-date`, `en-range-hyphen`, `en-ampersand` | One comma style; no sentence opens with a numeral; dates spelled out for the variant; ranges with "to" |
| 17 | Formatting | `en-title-case-heading`, `en-bold-overuse`, `en-inline-header-bullets`, `en-heading-punct` | Sentence-case headings without end punctuation; bold kept out of running text |
| 18 | Headlines and claims | `en-clickbait`, `en-establishment-claim`, `en-stat-claim`, `en-vague-attribution` | The headline states the finding; every number, study, or expert has a source or a `[source needed: …]` bracket |
| 19 | Links and limits | `en-link-text`, `en-template-residue`, `en-channel-length` | Link text names the destination; no `TBD` or `Lorem ipsum`; the copy fits the [channel limit](references/en/channels.md) |
| 20 | Profile | `en-brand-spelling`, `en-profile-banned`, `en-profile-avoid` | The brand name is spelled exactly and no banned word appears |

Story, detail, and truthfulness need a human reading: [`review.md`](references/review.md), including its [goal and call to action](references/review.md#goal-and-call-to-action), [dark patterns](references/review.md#dark-patterns), and [success metric](references/review.md#success-metric) sections. List every bracket in the note.

## Scripts

The scripts need only the Python standard library, version 3.8 or later. Write the full skill path so the command also works from the user's folder. In Claude Code the skill path is `${CLAUDE_SKILL_DIR}`. On Windows, use `py -3` when `python` is missing. `lint.py` detects Persian and English per line (`--lang auto|fa|en`); `lint_fa.py` and `lint_en.py` still run directly.

```bash
python <skill-path>/scripts/lint.py draft.txt --profile VOICE.md
python <skill-path>/scripts/lint.py draft.txt --profile auto --format caption
python <skill-path>/scripts/lint.py draft.md --md --lang en --variant en-GB
python <skill-path>/scripts/lint.py draft.txt --fix          # mechanical errors only
python <skill-path>/scripts/lint.py posts/ --json             # machine output for bulk work
python <skill-path>/scripts/selftest.py                       # the skill's own health check
```

`--profile` also takes a bare brand name; the search starts at `~/.whalory/profiles/`. Exit code 0 means no errors, 1 means errors in the text, and 2 means bad input or a bad profile.

If a command is refused, fails, or cannot find Python, continue with the [manual QA](#manual-qa) and write "QA: manual (script not run)" in the note. In a reference file, an intentionally bad example sits between `<!-- lint-ignore -->` and `<!-- /lint-ignore -->`, each marker on its own line; lint and `--fix` skip it.

### MCP tools

The Whalory MCP server comes with the plugin and the `.mcpb` bundle. When it is connected, use its tools instead of shell commands. They never touch the network. They write no files, except counts, never text, in the Hub folder once the user turns on statistics in their own terminal. A lint run through `lint_text` or `lint_file` counts as "QA: script".

- `lint_text` and `lint_file`: the same checks as `lint.py`, for pasted text or a file inside an allowed folder.
- `get_playbook`: the playbook section for a task, matched in either language.
- `get_reference_section`: one section of a reference file; call it without an anchor first to get the contents list.
- `profile_lookup`: the voice profile in the lookup order above, with its learnings note.
- `check_final`: one last lint of the text the user approved, as method step 7 says.

## Whalory Hub

Whalory checks once a day for signed rule updates. Sharing weekly counts of its checks stays off unless the user turns it on, and it never sends any text. Never change Whalory Hub settings. If the user wants to share statistics, tell them to run `python <skill-path>/scripts/hub_client.py consent` in their own terminal. For the weekly packet they post on GitHub themselves, the command ends in `on packets` instead. Anyone may turn sharing off. Status, sync, the packet, and what each one sends: [hub.md](references/hub.md). In the plugin, the `hub` and `feedback` commands run these steps.
