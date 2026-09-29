# Question gate

This file is step two of every task, after [context detection](router.md). It says when to ask the user, how many questions, in what form, and with which tool in each assistant. Every question must change the copy. Wherever a safe default exists, the draft comes before the question.

Only this file decides whether to ask. Other places only name a bank row or point back here. They are the "Question bank" column in the [route table](router.md#signals-to-routes), the "Questions" line in each playbook, and the [unstated genre](judgment.md#unstated-genre). If another file disagrees with this one, this file wins.

Each fixed template below comes in both languages. Use the conversation language, which is the language of the request, even when the copy will be in the other language. A request with no prose, such as JSON from a pipeline, takes the output language as its conversation language ([conversation language](router.md#output-language-variant-and-market)).

## Contents

- [Definitions](#definitions)
- [Decision order](#decision-order)
- [Task level and question cap](#task-level-and-question-cap)
- [Question format](#question-format)
- [How each host asks](#how-each-host-asks)
- [`needs_input` output](#needs_input-output)
- [Question template in chat](#question-template-in-chat)
- [Question bank by task](#question-bank-by-task)
- [Bulk tasks](#bulk-tasks)
- [Defaults](#defaults)
- [Never ask](#never-ask)
- [Saving durable answers](#saving-durable-answers)
- [Novice or professional](#novice-or-professional)
- [Claude Code example](#claude-code-example)
- [Plain chat example](#plain-chat-example)

## Definitions

| Term | Means |
|---|---|
| Brand profile | A profile that records this brand's own voice: steps 1 to 4 of the [profile lookup order](../SKILL.md#profile-lookup-order). |
| Starter profile | Step 5 of the same order. The dials, limits, and benchmark text come from it, but it doesn't record this brand's voice. It is enough for routine work, and tone isn't asked. |
| No profile | No brand profile is in play. A starter profile and the defaults don't change this. |
| Brand-building task | A request whose subject is the brand's voice itself: «صدای برندمون», «لحنِ ما چیه», «یه VOICE بساز», "our brand voice", "what's our tone", or building a profile. An about page, a tagline, and a landing page use the voice, so they don't count as brand-building. Verbal identity and a tone guide are strategic work; how they start without a brand profile is in the [decision order](#decision-order). |
| Costly task | A task where a wrong route costs a lot. Strategic work: strategy, verbal identity, naming, a pitch deck, and a campaign. Copy the user asked to run over 800 words. More than 20 bulk rows. Repairing a text of over 300 words when the request doesn't say how deep to go. |
| Blog post length | The 800-word threshold only counts a length the user asked for. A blog post with no length is routine work, with a default of 600 to 800 words, and the draft comes first. |
| Complete input | The request and the attachments hold every slot needed; step 2 of the decision order. |
| Risk | The level of the `industry/risk` slot on the card: [Risk level](router.md#risk-level). Only `high` changes asking. |

## Decision order

Take these four steps in order. The earliest step that answers is the decision.

1. Never ask if either of these two flags is on. Write with brackets and put the assumptions at the top of the note; in JSON output, put them in `assumptions`. High risk doesn't change this step: every unknown claim and license gets "confirm before publishing" («پیش از انتشار تأیید شود»).
   - `no_questions`: the user set questions aside with «فقط بنویس», «بی‌سؤال», «سؤال نپرس», or «سریع بنویس», or in English with "just write", "no questions", "don't ask", or "write it quickly"; or they replied «بنویس» or "write" to a question. The delivery shape stays that of their own host: in a chat, the copy and the note. «سریع» ("quick") is a flag only when it is about the process: [capability flags](router.md#capability-flags).
   - `interactive` off: no one is there to answer, as with `claude -p`, `codex exec`, an API, a batch job, or an agent that called Whalory. Delivery follows the `autonomous` host.
2. Don't ask if the answer shows in the request, the attachments, the files, the profile, `LEARNINGS.md`, or this conversation.
3. Ask first if any of these is true:
   - Risk is high and the facts or the license are missing. When no cue gives the market, the market counts as one of these facts: [market](router.md#output-language-variant-and-market).
   - A vital slot is empty and has no safe default: the last column of the [question bank](#question-bank-by-task).
   - The mode of the task is ambiguous, and the choice changes the whole output. Examples: a real photo or a story, a landing page or an about page, the facts behind an apology.
   - No place is known: the request has none of the three signals of the [unstated genre](judgment.md#unstated-genre), and `LEARNINGS.md` gives no default channel. The first question is "Where will it be read?"
   - It is a [costly task](#definitions).
   - It is a [brand-building task](#definitions) and no [brand profile](#definitions) is in play. A starter profile doesn't close this step.
4. Otherwise, write first. Then add at most two follow-up questions at the end of the note.

In step 3, the questions come from the task's row in the bank. Order them this way: the no-default slot first, then the question that changes the whole output, then the rest, up to three. In a brand-building task with no brand profile, the three questions of the "Building a profile" row make up the whole first round. A brand that writes in Persian gets address, formality, and a sample text. One that writes in English gets variant, formality, and a sample text ([English route](profile-builder.md#english-route)). The output language picks these questions, and the conversation language picks their wording. A step 3 message holds only questions, with no draft beside it. [Bulk tasks](#bulk-tasks) are the one exception.

**Layer banks.** Row 19 (risk) and row 20 (occasion) in the [route table](router.md#signals-to-routes) bring their own bank beside the bank of the main row. The two banks share one cap: three questions in total. No-default slots come first, from the layer bank and then from the main row. At high risk, the question about evidence for a claim also comes here, because it changes the whole output. Then the main row's questions follow, up to three. Any other layer question doesn't fit, so it is written with a default or a bracket. Example: a channel post for a fund that promises «سودِ تضمینی» ("guaranteed returns"). The license number and the evidence for the returns come from the "Claim check" bank. The "Captions and social media" bank has no no-default slot, so it fills the third place at most.

**Verbal identity and a tone guide without a brand profile.** This request is row 18 and strategic work. Row 21 is for when the voice itself is asked for and no document is, as in «لحنِ ما چیه» ("what's our tone"). If no [brand profile](#definitions) is in play, the first round is still the three "Building a profile" questions. The brief card of row 18 comes in the next round, and these answers fill its "Brand and profile" line. Sometimes the brand's own texts are attached, and the address and formality show in them. Then step 2 closes these three questions, and the work starts with the brief card. In the "new brand" chain, these three questions are three ★ lines of that one card: [Voice profile in three questions](playbooks-strategy.md#voice-profile-in-three-questions).

## Task level and question cap

| Level | Examples | Question cap |
|---|---|---|
| Micro | Button, error message, SMS, one-time passcode | Zero |
| Routine | Post, email, product description, ad, one page, a blog post with no length | Zero to three |
| Strategic | Strategy, verbal identity, naming, pitch deck, campaign, chain | One brief card and at most one calibration round |

Step 3 of the decision order comes before the level's cap. A micro task with a no-default slot, such as the type of an SMS, gets that one question.

**Strategic work always starts with a brief card.** Its ★ lines are the task's questions from the bank. A no-default slot is a line left empty for the user to fill. It counts as one question, and the diagnosis line records it as "brief card" («کارتِ بریف»).

A **brief card** is the [brief template](brief.md#template) with its starred slots pre-filled from the context card, and the user edits it in one reply. The **calibration round** is [route 3](profile-builder.md#route-3-calibration-round): one short text in two versions, and one choice.

**A chain asks once.** One brief card for the whole chain comes in the first message, and no later step brings a new question. The research step's questions are also one line of this card. Without a web tool, that line stands in for the list of research questions. The full rule is in Chains (in Whalory Pro).

```
کارِ راهبردی است؛ این کارت را از روی گفته‌هایتان پر کردیم. هر خطی که درست نیست، همان را اصلاح کنید:
★ برند و پروفایل: [نام] · VOICE.md پیدا شد
★ کار: کمپینِ یلدا
★ کانال‌ها: پستِ اینستاگرام، استوری، پیامک
★ خواننده: مشتریِ قدیمیِ [برند]، روی موبایل
★ کارِ بعد از خواندن: [خرید از سایت یا سفارش در دایرکت]
★ هدفِ قابلِ سنجش: [مثلاً شمارِ سفارش در بازه‌ی کمپین]
★ مواد و واقعیت‌ها: [پیشنهاد، قیمت، مهلت]
★ مرزِ ادعا: [ادعایی که تأیید می‌خواهد و تأییدکننده‌اش]
بازه‌ی زمانی: [شروع و پایان]
اگر نمی‌خواهید جواب بدهید، فقط بنویسید «بنویس»؛ با گزینه‌های پیشنهادی می‌نویسیم و جای واقعیت‌ها کروشه می‌گذاریم.
```

```
This is a strategic task, so we filled in this card from what you've told us. Correct any line that's wrong:
★ Brand and profile: [name] · VOICE.md found
★ Task: Black Friday campaign
★ Channels: Instagram post, story, email
★ Reader: returning [brand] customers, on their phones
★ What the reader does next: [buy on the site or order by DM]
★ Measurable goal: [for example, the number of orders during the campaign]
★ Materials and facts: [offer, price, deadline]
★ Claim boundary: [claims that need approval, and who approves them]
Time window: [start and end]
If you'd rather not answer, just reply "write". We'll use the recommended options and put brackets where facts are missing.
```

## Question format

- Put every question in one message, one after another, and end the turn once.
- Ask three at most. If a fourth seems needed, one of the first three matters less; leave that one to its default.
- Build the options from the situation. Each question has two to four options, made from this task.
- Put the recommended option first, marked "(recommended)" («(پیشنهادی)»). If no answer comes, it is used.
- Ask in the conversation language and at the level of the user's request.
- Accept short answers: «۱الف ۲ب» or `1a 2b` is a full answer, and a free answer works too.
- End the message with the fixed escape line, word for word, in the conversation language:

> اگر نمی‌خواهید جواب بدهید، فقط بنویسید «بنویس»؛ با گزینه‌های پیشنهادی می‌نویسیم و جای واقعیت‌ها کروشه می‌گذاریم.

> If you'd rather not answer, just reply "write". We'll use the recommended options and put brackets where facts are missing.

**Fact questions.** Nobody can guess a fact, so "give us one concrete fact" has no answer options. In a chat, it stays an open question. In a multiple-choice tool such as `AskUserQuestion`, the same question has two options. The English options are "I don't have it; use brackets (recommended)" and "I'll type it"; the Persian ones are «ندارم؛ کروشه بگذار (پیشنهادی)» and «جواب را می‌نویسم». The description of the second option says to type the answer in the `Other` row. If every question is a fact question, set the tool aside and ask in plain text with the [chat template](#question-template-in-chat).

| Not this | This |
|---|---|
| لحنتان چطور باشد؟ | با مشتری «تو» می‌گویید یا «شما»؟ الف) شما (پیشنهادی) ب) تو |
| مخاطبِ هدفتان کیست؟ | این پیامک به دستِ کی می‌رسد؟ الف) خریدارِ همین هفته (پیشنهادی) ب) مشتریِ قدیمیِ ساکت |
| محصول چه ویژگی‌هایی دارد؟ | وزن، جنس و ضمانت را دارید؟ اگر نه، جایشان کروشه می‌گذاریم. |
| سؤالِ دیگری ندارید؟ | [پرسشی که متن را عوض نمی‌کند، پرسیده نمی‌شود.] |
| What tone do you want? | Is this for first-time buyers or regulars? a) first-time buyers (recommended) b) regulars |
| Who is your target audience? | Who gets this email? a) people who bought this week (recommended) b) past customers who went quiet |
| What features does the product have? | Do you have the weight, material, and warranty? If not, we'll put brackets in their place. |
| Any other questions? | [A question that doesn't change the copy doesn't get asked.] |

## How each host asks

The form of asking comes from the tool at hand, and the assistant's name plays no part in it. See the `ask_tool` flag in [Capability flags](router.md#capability-flags).

| Host | Question form | Note |
|---|---|---|
| Claude Code, interactive | The `AskUserQuestion` tool. Each question has a `header` of at most 12 characters and two to four options. The tool takes one to four questions; Whalory's cap is three (checked 2026-09-27, [docs](https://code.claude.com/docs/en/agent-sdk/user-input)). | The interface has its own `Other` row for a free answer (checked 2026-09-27, [docs](https://code.claude.com/docs/en/tools-reference)). Fact questions: [Question format](#question-format). |
| Claude Code with `claude -p` | Never ask. The Claude Code docs call this run non-interactive (checked 2026-09-27, [docs](https://code.claude.com/docs/en/headless)). | With `--permission-prompts none` or the `dontAsk` mode, the `AskUserQuestion` tool is removed or denied. |
| Codex | The `request_user_input` tool, wherever it is in the tool list. At first the tool worked only in plan mode. A change merged into the Codex repository brought it to the default mode too (checked 2026-09-27, [report](https://github.com/openai/codex/issues/10384), [change](https://github.com/openai/codex/pull/12735)). With no tool: a numbered list, then end the turn. | In `codex exec`, never ask; the `interactive` flag is off. |
| ChatGPT (skill, custom GPT, project), claude.ai, Gemini, Copilot, Cursor, Windsurf, Kiro | A numbered list in the [chat template](#question-template-in-chat), then end the turn | Accept short answers such as «۱الف ۲ب» or `1a 2b` |
| Any other host with a structured question tool | The same rules with that tool | The cap of three questions and the recommended option first stay fixed |
| API and automation | Never ask. Use the [`needs_input` output](#needs_input-output) only when the input accepted it; otherwise write with brackets | Assumptions go in `assumptions` |
| An in-house assistant with a pasted prompt | Plain text in the same chat template | The pasteable prompts include a section on questions |

## `needs_input` output

Some pipelines pass questions to a person and bring back the answer. Such a pipeline announces it with one of these two signals:

- The input JSON has the key `"accepts": ["needs_input"]`.
- The system text says plainly that `needs_input` output is accepted.

Without a signal, the pipeline doesn't accept `needs_input`. Whalory then writes with brackets and puts the assumptions in `assumptions`. With a signal, and only when step 3 of the [decision order](#decision-order) says "ask first", Whalory returns this shape with no copy beside it. Its questions follow the rules of [Question format](#question-format) and use the conversation language, while the keys stay the same in both languages. The answer comes back in the next call under the `answers` key, with the same `id` values.

```json
{
  "status": "needs_input",
  "questions": [
    {"id": "channel", "question": "کجا خوانده می‌شود؟", "options": ["کپشنِ اینستاگرام (پیشنهادی)", "پیامک", "صفحه‌ی سایت"]}
  ],
  "context": "تشخیص: متنِ معرفی · مشتریِ تازه · پروفایل: پیش‌فرض · خودکار · آزمون: اسکریپت"
}
```

```json
{
  "status": "needs_input",
  "questions": [
    {"id": "channel", "question": "Where will it be read?", "options": ["Instagram caption (recommended)", "SMS", "Website page"]}
  ],
  "context": "Diagnosis: intro copy · new customer · Profile: default · automated · QA: script"
}
```

## Question template in chat

```
پیش از نوشتن، دو سه چیزِ کوتاه:
۱. کجا خوانده می‌شود؟ الف) کپشنِ اینستاگرام (پیشنهادی)  ب) صفحه‌ی سایت  ج) پیامک یا پیام‌رسان  د) جای دیگر
۲. خواننده کیست؟ الف) مشتریِ تازه که ما را نمی‌شناسد (پیشنهادی)  ب) مشتریِ قدیمی  ج) همکار یا شریکِ تجاری
۳. یک واقعیتِ ملموس بدهید: عدد، اسم، جزئیاتِ ساخت یا حرفِ یک مشتری.
کوتاه جواب بدهید، مثلاً «۱الف ۲ب».
اگر نمی‌خواهید جواب بدهید، فقط بنویسید «بنویس»؛ با گزینه‌های پیشنهادی می‌نویسیم و جای واقعیت‌ها کروشه می‌گذاریم.
```

```
Before we write, a few quick questions:
1. Where will this be read? a) Instagram caption (recommended)  b) website page  c) SMS or messaging app  d) somewhere else
2. Who is the reader? a) a new customer who doesn't know us (recommended)  b) a regular customer  c) a colleague or business partner
3. Give us one concrete fact: a number, a name, a detail of how it's made, or something a customer said.
Short answers are fine, for example "1a 2b".
If you'd rather not answer, just reply "write". We'll use the recommended options and put brackets where facts are missing.
```

- Build the options from the card. If the channel is known, drop question 1 and bring in the next question of the bank.
- In step 3, the message ends with the questions, and the turn ends there. No half-done draft comes beside them, except in [bulk tasks](#bulk-tasks).
- In step 4, the draft comes first, and two follow-up questions go at the end of the note, in the same form.

## Question bank by task

Each task has two or three questions. Ask only those whose answers aren't on the card. The last column shows the slot that has no safe default and needs a question before writing. In strategic work, these same questions are the lines of the brief card. The output language decides which questions apply. The conversation language decides their wording: the English column in an English conversation, the Persian column in a Persian one. A question that exists for one output language only, such as the Persian address or the English variant, appears in both columns.

| Task | Questions (en) | Questions (fa) | No-default slot |
|---|---|---|---|
| Base questions | "Where will it be read?" · "Who is the reader, and what state are they in?" · "Give us one concrete fact." | «کجا خوانده می‌شود؟» · «خواننده کیست و در چه حالی است؟» · «یک واقعیتِ ملموس بدهید.» | Channel, only when the request shows no sign of a place |
| Captions and social media | "What is this post for? Sales, an introduction, trust, or news" · "What should the reader do next? Send a direct message, buy from the bio link, save or share, or nothing" | «هدفِ این پست چیست؟ فروش، معرفی، اعتمادسازی یا خبر» · «بعد از خواندن چه کند؟ دایرکت، خرید از لینکِ بیو، ذخیره و ارسال، یا هیچ» | None |
| Product descriptions and marketplace listings | "Where will it be published? Your own site, Amazon, Etsy, eBay, or Shopify" · "Do you have the exact specifications? Weight, size, material, warranty" · "Does it make a sensitive claim? Health, authenticity, free shipping" | «کجا منتشر می‌شود؟ سایتِ خودتان، دیجی‌کالا، باسلام، دیوار یا شیپور» · «مشخصاتِ قطعی را دارید؟ وزن، ابعاد، جنس، ضمانت» · «ادعای حساس دارد؟ سلامت، اصل بودنِ کالا، ارسالِ رایگان» | Specifications; when they're missing, brackets |
| Customer replies and public reviews | "What exactly happened, and what have you done so far?" · "What can we promise? A time, a remedy, or the next step" · "Which private channel continues the conversation?" · For a Google review, only when the business may be registered in Iran: "In which country is the business registered?" | «دقیقاً چه شده و تا حالا چه کرده‌اید؟» · «چه چیزی را می‌شود قول داد؟ زمان، جبران یا قدمِ بعد» · «ادامه‌ی گفت‌وگو از کدام راهِ خصوصی؟» · برای نظر در گوگل، فقط اگر کسب‌وکار ممکن است در ایران ثبت شده باشد: «کسب‌وکار در کدام کشور ثبت شده؟» | The facts of the case. For a Google review, also the country of registration, under the condition in the next row. In automated mode: brackets and "confirm before sending" («پیش از فرستادن تأیید شود») |
| Hard messages and crises | "What exactly happened, and who was harmed?" · "What have you done, and when does the next update come?" · "Is any compensation on offer?" | «دقیقاً چه شد و به چه کسانی آسیب رسید؟» · «چه کرده‌اید و خبرِ بعدی کِی می‌آید؟» · «جبرانی در کار است؟» | All three. In automated mode: brackets and "don't publish without approval" («بدونِ تأیید منتشر نشود») |
| Pitch deck, in the brief card | "What stage are you at, and how much are you raising?" · "Real growth numbers, with a source?" · "Who is the audience? Angel investors, a fund, or a competition" | «در چه مرحله‌ای هستید و چه مبلغی می‌خواهید؟» · «عددهای واقعیِ رشد، با منبع؟» · «مخاطب کیست؟ سرمایه‌گذارِ فرشته، صندوق یا مسابقه» | The numbers |
| Campaign, in the brief card | "What is the measurable goal?" · "Which channels? How many may we pick" · "Which occasion, and what time window?" | «هدفِ قابلِ سنجش چیست؟» · «کدام کانال‌ها؟ چند انتخاب مجاز است» · «مناسبت و بازه‌ی زمانی؟» | The goal |
| Blog and SEO | "What is the reader's main question, or the keyword?" · "Depth: a full guide or a short answer?" · "Which sources can we quote?" | «پرسشِ اصلیِ خواننده یا کلیدواژه چیست؟» · «عمق: راهنمای کامل یا جوابِ کوتاه؟» · «از کدام منبع‌ها می‌شود نقل کرد؟» | None; only a requested length of over 800 words gets asked first |
| Style repair | "How deep should we go? Only the mechanics, the sentences (recommended), or a full rewrite" · "Keep this tone, or bring it in line with the profile?" | «چقدر دست ببریم؟ فقط نگارش، جمله‌ها (پیشنهادی)، یا بازنویسیِ کامل» · «لحن همین بماند یا به پروفایل برسد؟» | Depth, only for a text of over 300 words whose request doesn't say how deep; shorter texts get "the sentences" |
| Story from a photo | "Is this photo the brand's own, or do you want a labeled story?" · "What do you know about the photo? Place, people, time" | «این عکس از خودِ برند است یا قصه‌ی برچسب‌دار می‌خواهید؟» · «از عکس چه می‌دانید؟ جا، آدم، زمان» | The task mode |
| Personal bio | "Do you have this person's consent?" · "Where will it be published?" | «رضایتِ خودِ این آدم را دارید؟» · «کجا منتشر می‌شود؟» | Consent |
| UI microcopy and repo strings | "Do you have a glossary or a length limit?" · "Just this screen, or the whole locale file?" · Only for Persian copy with no brand profile: "Should the app address users informally («تو») or formally («شما»)?" | «واژه‌نامه یا سقفِ طول دارید؟» · «فقط این صفحه یا کلِ فایلِ زبان؟» · فقط برای متنِ فارسی و بی پروفایلِ برند: «با کاربر «تو» یا «شما»؟» | The one word for a concept, when the file uses several words for it and has no glossary |
| Ads | "Which network? Google, Microsoft, Meta, LinkedIn, TikTok, or Reddit" · "Where is the landing page?" | «کدام شبکه؟ گوگل، یکتانت، اینستاگرام، کانالِ تلگرام یا ایتا» · «صفحه‌ی فرود کجاست؟» | The network |
| Bulk catalog | One confirmation question beside the column map and three sample rows: "Is this right? a) write the rest (recommended) b) change a column"; the shape of the reply is in [Bulk tasks](#bulk-tasks) | «درست است؟ الف) بقیه را بنویس (پیشنهادی) ب) یک ستون عوض شود» | The column map |
| Building a profile | For a brand that writes in Persian: "Does the brand say «تو» (informal) or «شما» (formal) to customers?" · "Formality: casual, middle, or formal?" · "A past text you like?". For a brand that writes in English ([English route](profile-builder.md#english-route)): "US English, British English, or another variant?" · the same formality and sample questions. Then "Save it in `VOICE.md`?" | برای برندی که فارسی می‌نویسد: «برند با مشتری «تو» می‌گوید یا «شما»؟» · «رسمیت: خودمانی، میانه یا رسمی؟» · «یک متنِ قبلی که دوستش دارید؟». برای برندی که انگلیسی می‌نویسد: «انگلیسیِ آمریکایی، بریتانیایی یا گونه‌ای دیگر؟ الف) آمریکایی (پیشنهادی) ب) بریتانیایی ج) دیگر» · همان دو پرسشِ رسمیت و متنِ نمونه. بعد: «در `VOICE.md` ذخیره‌اش کنیم؟» | None; in a brand-building task without a brand profile, these three make up the whole first round |

The questions for business documents sit at the top of each document: job posting (in Whalory Pro), company profile (in Whalory Pro), proposal (in Whalory Pro), and invitation (in Whalory Pro). For a phone menu: "Why do people call most often, and which key reaches a person?" («دلیلِ پرتکرارِ تماس چیست و کدام کلید به آدم می‌رسد؟»). For a restaurant menu: "Has the kitchen approved the prices, the portion sizes, and the allergens?" («قیمت، اندازه و حساسیت‌زاها را آشپزخانه تأیید کرده؟»). Whalory never writes a tender response without the tender's own documents.

The more detailed banks stay in their own files and are only linked here:

- [Brief template](brief.md#template)
- [Questions that draw out the story](gathering.md#questions-that-draw-out-the-story)
- [Short interview for building a profile](profile-builder.md#route-2-short-interview)
- Founder and customer interviews: fa (in Whalory Pro), en (in Whalory Pro)
- Learning the product: fa (in Whalory Pro), en (in Whalory Pro)
- Makers and craftspeople (in Whalory Pro)
- Questions before a repair: [fa](fa/style-repair.md#ده-پرسش-پیش-از-تعمیر), [en](en/style-repair.md#questions-before-you-repair)
- Creative brief (in Whalory Pro)
- Message strategy sheet: fa (in Whalory Pro), en (in Whalory Pro)
- An industry not on the list: fa (in Whalory Pro), en (in Whalory Pro)

## Bulk tasks

A file with tens or hundreds of rows has its own rule, because a mistake in the column map repeats in every row. Examples are a CSV file or a spreadsheet of products with an `sku`, title, or description column.

- Interactive, first reply: three pieces in one message, which are the column-map table, three sample rows in the new columns, and one confirmation question. This is the one place where a draft comes beside a question before the work. Until the confirmation arrives, Whalory writes no further rows.
- Automated: don't ask. Write the first three rows, check them with lint, then go on. The column map and every other assumption go at the top of the note; in JSON output, they go in `assumptions`.
- New columns: `title_new`, `bullets_new`, `desc_new`, and `flags`, as in the column map (fa: column map (in Whalory Pro) · en: column map (in Whalory Pro)). The original columns stay untouched: bulk mode (fa: bulk mode (in Whalory Pro) · en: bulk mode (in Whalory Pro)) and [bulk work in editing](editor.md#bulk-work).
- Round by round, with a check on each row: the Bulk catalog (in Whalory Pro) playbook.

```
نقشه‌ی ستون‌ها را این‌طور فهمیدیم:
| ستونِ فایل | کارِ والوری | ستونِ تازه |
| name، brand، model | مواد برای عنوان | title_new |
| specs | مواد برای ویژگی‌ها | bullets_new |
| description | مواد و مقایسه | desc_new |

سه ردیفِ نمونه: [جدولِ سه ردیفِ اول با ستون‌های تازه]

درست است؟ الف) بقیه را بنویس (پیشنهادی)  ب) این ستون را عوض کنید: …
اگر نمی‌خواهید جواب بدهید، فقط بنویسید «بنویس»؛ با گزینه‌های پیشنهادی می‌نویسیم و جای واقعیت‌ها کروشه می‌گذاریم.
```

```
We read the column map like this:
| File column | What Whalory does | New column |
| name, brand, model | material for the title | title_new |
| specs | material for the bullets | bullets_new |
| description | material and comparison | desc_new |

Three sample rows: [table of the first three rows with the new columns]

Is this right? a) write the rest (recommended)  b) change this column: …
If you'd rather not answer, just reply "write". We'll use the recommended options and put brackets where facts are missing.
```

## Defaults

When the user didn't answer, replied "write", turned on `no_questions`, or the task is automated, these defaults apply, and the note names them.

| Slot | Default |
|---|---|
| Channel | From the verb and the place name. Short promotional copy: an Instagram caption. A product: the product page. "Message" on its own: the channel that `LEARNINGS.md` names, otherwise SMS |
| Reader | The profile's reader; otherwise "a new customer, in a hurry, on a phone" («مشتریِ تازه، عجول، روی موبایل») |
| Tone | The profile. Otherwise: warmth 3, formality 3, humor 1, narrative density 3, and sentence length 3 (at most 24 words in Persian, 25 in English). Loud marks 0, so no emoji and no exclamation marks; jargon 2; rhetoric dose 3. Table: [tone dials](voice-profile.md#tone-dials) |
| Address (Persian only) | The `address` slot of the profile; otherwise «شما» |
| Length | The channel default in channels.md (fa: [channels.md](fa/channels.md) · en: [channels.md](en/channels.md)); if `data/channels/` exists, the limit recorded there. A blog post with no length: 600 to 800 words |
| Closing call to action | One soft step, in a bracket |
| Facts, numbers, claims | A bracket. A claim without evidence comes out, and no softened version of it stays |
| Photo mode | The brand's real photo; only what can be seen |
| Language | The [decision order in the router](router.md#output-language-variant-and-market), which ends with fa-IR, or en-US for English. The market stays `unknown` unless a cue gives it |
| Number of versions | One; three for headlines; for names, a shortlist of three |
| Occasion | Check the publishing date against occasions.md (fa: [occasions.md](fa/occasions.md) · en: [occasions.md](en/occasions.md)); if the date is unknown, add one line to the note |

## Never ask

- About tone, when a brand profile or a starter profile is in play. The profile is the answer to that question. A brand-building task gets no open question about tone either; the "Building a profile" row asks about address and formality, with options.
- About anything that shows in the request, the attachments, the files, the profile, or `LEARNINGS.md`.
- Which assistant or model the user works with. The flags read that from the tools.
- For permission to do what the user asked for.
- A question whose every answer leaves the copy the same.
- Anything already answered once in this conversation.
- "Anything else?" or "Are you happy with this?" before delivery.

## Saving durable answers

An answer about the brand itself is useful in later tasks too, so it lasts. Save it so nobody has to ask again.

| Answer | Durable? | Where |
|---|---|---|
| Persian address, «تو» or «شما» | Yes | The profile; until a profile exists, `LEARNINGS.md` |
| English variant and spelling, such as en-US or en-GB | Yes | The profile: `variant`, `spelling`; until a profile exists, `LEARNINGS.md` |
| The brand's default channel | Yes | `LEARNINGS.md` |
| Glossary, banned words, spelling of the name | Yes | The profile: `prefer`, `banned`, `misspellings` |
| Who approves the claims | Yes | The profile, in the claim boundary section |
| The goal of this post, the deadline of this discount | No | This task only |
| Personal data of the brand's customers | Never | Nowhere; fa: [ethics.md](fa/ethics.md) · en: [consent and privacy](en/ethics.md#consent-and-privacy) |

- Add a new row in the [learnings note format](judgment.md#learnings-note-format): date, format, observation, decision.
- The learnings note sits next to the chosen profile: `LEARNINGS.md` next to `VOICE.md` at the project root, `voice/LEARNINGS.md` next to `voice/VOICE.md`, or `<brand>.LEARNINGS.md` next to `<brand>.md` in `~/.whalory/profiles/`.
- If `fs_write` is off, give the user the text of the row so they can put it next to the profile themselves.
- When building a profile, ask after the three questions: "Save it in `VOICE.md`?" («در `VOICE.md` ذخیره‌اش کنیم؟»). Without `fs_write`, give the full text of the file to copy.

## Novice or professional

A question must speak to the person who reads it. Read the user's level from the request, and don't ask about it.

| | Most users | Professionals |
|---|---|---|
| Signal | A short, colloquial request such as «یه متن خوب» ("some good copy"), and no brief | Words such as brief, persona, CTA, and click-through rate; a brief file; work in a repository |
| Words | Plain: "reader" instead of persona, "what the reader does next" instead of CTA | The user's own terms |
| Options | Each option with a short example | Labels only |
| Length | A short question with a one-line explanation | The question only |
| Defaults | More defaults, fewer questions | Sharper questions about the goal and the measurement |

```
برای عمومِ کاربران:
۱. این متن کجا دیده می‌شود؟ الف) پستِ اینستاگرام، مثلِ عکسِ کیک با دو خط زیرش (پیشنهادی)  ب) پیامک، مثلِ «سفارشتان آماده است»

برای حرفه‌ای:
۱. کانال؟ الف) کپشن (پیشنهادی)  ب) پیامک  ج) صفحه‌ی فرود
```

```
For most users:
1. Where will people see this? a) an Instagram post, like a photo of a cake with two lines under it (recommended)  b) an SMS, like "Your order is ready"

For professionals:
1. Channel? a) caption (recommended)  b) SMS  c) landing page
```

## Claude Code example

In Claude Code, the user sent a photo of a jar of honey and wrote «برای این یه متن بنویس». No profile was found. The photo mode is a no-default slot, and the channel is unknown too, so two questions go in one call:

```json
{
  "questions": [
    {
      "question": "این عکس از محصولِ خودِ شماست یا قصه‌ی خیالی می‌خواهید؟",
      "header": "حالتِ عکس",
      "multiSelect": false,
      "options": [
        {"label": "عکسِ خودمان (پیشنهادی)", "description": "فقط آنچه در عکس دیده می‌شود و آنچه شما می‌گویید."},
        {"label": "قصه‌ی برچسب‌دار", "description": "قصه‌ی خیالی با برچسبِ «قصه»؛ جای واقعیتِ برند نمی‌نشیند."}
      ]
    },
    {
      "question": "متن کجا منتشر می‌شود؟",
      "header": "کانال",
      "multiSelect": false,
      "options": [
        {"label": "کپشنِ اینستاگرام (پیشنهادی)", "description": "یک تا سه جمله؛ خطِ اول پیش از «بیشتر»."},
        {"label": "صفحه‌ی محصول", "description": "سه تا شش جمله، با مشخصاتِ قطعی."},
        {"label": "باسلام یا دیجی‌کالا", "description": "عنوان و توضیح طبقِ قاعده‌ی همان بازارگاه."}
      ]
    }
  ]
}
```

The user picks «عکسِ خودمان» and «کپشنِ اینستاگرام». Whalory writes with no further question and puts brackets where the city of origin and the time of the shot belong. The note starts like this:

«تشخیص: کپشنِ اینستاگرام از عکسِ محصول · مشتریِ تازه · پروفایل: پیش‌فرض · دو پرسش · آزمون: اسکریپت»

## Plain chat example

In ChatGPT, the user wrote «یه متن تبلیغ واسه بوتاکس کلینیکمون بنویس، تخفیف ۳۰ درصد». Risk is high and the facts are missing, so this is step 3 of the decision order. «بوتاکس» is the trade name of one product, and advertising a drug product and advertising a medical service each need their own license: regulation.md (in Whalory Pro). Whalory replies:

```
پیش از نوشتن، سه چیزِ کوتاه؛ تبلیغِ خدمتِ پزشکی مرزِ قانونی دارد:
۱. نامِ پزشکِ مسئول، شماره‌ی نظامِ پزشکی‌اش و مجوزِ تبلیغ را دارید؟ اگر نه، جایشان کروشه می‌گذاریم.
۲. کدام فرآورده تزریق می‌شود، با نام و شناسه‌ی IRC؟ تخفیف با چه شرطی و تا چه تاریخی است؟
۳. متن کجا منتشر می‌شود؟ الف) پیجِ اینستاگرام (پیشنهادی)  ب) آگهیِ پولی  ج) پیامک
کوتاه جواب بدهید، مثلاً «۱ ندارم، ۲ نمی‌دانم، تا ۱۵ مهر، ۳الف».
اگر نمی‌خواهید جواب بدهید، فقط بنویسید «بنویس»؛ با گزینه‌های پیشنهادی می‌نویسیم و جای واقعیت‌ها کروشه می‌گذاریم.
```

The user answers «۱ ندارم، ۲ نامِ فرآورده را نمی‌دانم، تخفیف تا ۱۵ مهر، ۳الف». Whalory writes the caption, with brackets in place of the doctor's name and number, the license, and the product name. The discount also stays in a confirm bracket, and the copy makes no promise of results:

```
تزریقِ [نامِ فرآورده طبقِ پروانه] در کلینیکِ [نامِ کلینیک]، زیرِ نظرِ [نامِ پزشک، شماره‌ی نظامِ پزشکی].
پزشک در ویزیتِ پیش از تزریق می‌گوید این تزریق برایتان مناسب است یا نه.
[تخفیفِ ۳۰٪ تا ۱۵ مهر؛ مجاز بودنِ تبلیغِ تخفیف روی خدمتِ پزشکی پیش از انتشار تأیید شود]
نوبت: [راهِ رزرو]
```

The note, in the language of the conversation:

- «تشخیص: کپشنِ اینستاگرام · مراجعِ تازه · پروفایل: پیش‌فرض · سه پرسش · خطر: بالا · آزمون: دستی»
- پیش از انتشار تأیید شود: نام و شماره‌ی نظامِ پزشکیِ پزشکِ مسئول؛ مجوزِ تبلیغ؛ نام و شناسه‌ی IRCِ فرآورده؛ مجاز بودنِ تبلیغِ تخفیف روی خدمتِ پزشکی. مرجع: regulation.md (in Whalory Pro).
- پیشنهادِ ثبت در `LEARNINGS.md`: «تبلیغِ این کلینیک فقط با نامِ پزشکِ مسئول و نامِ فرآورده طبقِ پروانه.»
