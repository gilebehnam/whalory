# Context detection examples

This file holds full examples of [context detection](router.md). Each one shows the context card, the step and row of the route, the decision of the [question gate](intake.md#decision-order), and the diagnosis line. The rules live in router.md and intake.md. This file only shows how those rules fit together on a real request. When you're torn between two rows or two decisions, read the closest example.

Requests, card values, and note lines stay in the language of the conversation, so the Persian examples keep their Persian text.

## Contents

- [1. Cafe caption in a plain chat](#1-cafe-caption-in-a-plain-chat)
- [2. Checkout microcopy in a repository](#2-checkout-microcopy-in-a-repository)
- [3. Product photo in claude.ai](#3-product-photo-in-claudeai)
- [4. Automated SMS from an API](#4-automated-sms-from-an-api)
- [5. Beauty clinic, high risk](#5-beauty-clinic-high-risk)
- [6. Repairing a long text in Claude Code](#6-repairing-a-long-text-in-claude-code)
- [7. Yalda campaign across channels](#7-yalda-campaign-across-channels)
- [8. English tagline for a Berlin bakery](#8-english-tagline-for-a-berlin-bakery)
- [9. "Just write" in a chat](#9-just-write-in-a-chat)

## 1. Cafe caption in a plain chat

Request: «یه کپشن واسه کافه‌م بنویس»

```
host: chat-plain · inputs: none · operation: write · intent: deliver
format/channel: caption@instagram · reader: مشتریِ تازه، روی موبایل (پیش‌فرض)
language: fa · fa-IR · market: ir · conversation: fa · industry/risk: cafe · low · occasion: تاریخِ انتشار نامعلوم
profile: starters/cafe (آغاز) · LEARNINGS: n · output: chat-text · qa: manual
```

- Route: step 3, row 3 → [Caption](playbooks-social.md#caption).
- Language: the request is Persian and nothing earlier in the order decides, so the output is `fa` with the default variant fa-IR. With no other country named, fa-IR is the Iran cue, so the market is `ir`.
- Questions: step 4 of the gate, so the draft comes first. A caption is routine work, and every empty slot has a safe default. The copy carries one bracket for real details. One follow-up question goes at the end of the note: «یک چیزِ واقعی از کافه بگویید، مثلاً نوشیدنیِ این هفته یا جای نشستنِ کنارِ پنجره.»
- Note: «تشخیص: کپشنِ اینستاگرام · مشتریِ تازه · پروفایل: cafe (آغاز) · پرسشِ تکمیلی · آزمون: دستی»

## 2. Checkout microcopy in a repository

Request in Claude Code, inside the repository of an online store: «متن‌های فارسیِ صفحه‌ی پرداخت یه کم خشکه، درستش کن»

```
host: repo-agent · inputs: locale-files (src/locales/fa.json) · operation: rewrite · intent: deliver
format/channel: ui@fa.json · reader: خریدارِ وسطِ پرداخت
language: fa · fa-IR · market: ir · conversation: fa · industry/risk: ecommerce · medium (پول) · occasion: none
profile: VOICE.md · LEARNINGS: y · output: file-edit · qa: script
```

- Route: step 1, row 1 → Microcopy in a code repository (in Whalory Pro) and ux-strings.md (in Whalory Pro).
- Questions: none. The glossary is in `VOICE.md`, and `LEARNINGS.md` records a limit of three words per button.
- Delivery: only the values of the `checkout.*` keys change; the keys and `{amount}` stay untouched. Then comes a short table of key, old copy, and new copy.
- Note: «تشخیص: ریزمتنِ صفحه‌ی پرداخت در `fa.json` · خریدارِ وسطِ پرداخت · پروفایل: VOICE.md و LEARNINGS · بی‌پرسش · آزمون: اسکریپت»

## 3. Product photo in claude.ai

Request, with a photo of a jar of honey on a table: «برای این عکس یه متن بنویس واسه پیج»

```
host: chat-tools · inputs: image(product) · operation: write · intent: deliver
format/channel: caption@instagram · reader: مشتریِ تازه (پیش‌فرض)
language: fa · fa-IR · market: ir · conversation: fa · industry/risk: food · medium (ادعای سلامت ممکن است) · occasion: none
profile: پیش‌فرض · LEARNINGS: n · output: chat-text · qa: script
```

- Host: in claude.ai, skills work only with code execution (checked 2026-09-27, [docs](https://support.claude.com/en/articles/12512180-use-skills-in-claude)). So the `exec` flag is on, the host is `chat-tools`, and the quality check (QA) runs by script.
- Route: step 1, row 5 → Story from a photo (in Whalory Pro). «واسه پیج» is a place name, but the photo attachment is more precise and pushes row 3 aside.
- Questions: yes, before writing. The photo mode is a no-default slot, because the honesty line moves with it. No structured question tool is available, so two questions come in one message, in the [chat template](intake.md#question-template-in-chat), and the turn ends there:

```
۱. این عکس از محصولِ خودِ شماست یا قصه‌ی خیالی می‌خواهید؟ الف) عکسِ خودمان است (پیشنهادی)  ب) قصه‌ی برچسب‌دار
۲. از عکس چه می‌دانید؟ جا، آدم یا زمانِ برداشت، هر کدام که هست.
اگر نمی‌خواهید جواب بدهید، فقط بنویسید «بنویس»؛ با گزینه‌های پیشنهادی می‌نویسیم و جای واقعیت‌ها کروشه می‌گذاریم.
```

## 4. Automated SMS from an API

The input arrives from a store's software, and no person is there to answer:

```json
{"task": "sms", "event": "order_shipped", "brand": "[برند]", "vars": ["name", "order_id", "tracking_url"]}
```

```
host: autonomous · inputs: none · operation: write · intent: deliver
format/channel: sms · reader: خریدارِ همین سفارش
language: fa · fa-IR · market: ir · conversation: fa · industry/risk: ecommerce · low · occasion: none
profile: پیش‌فرض · LEARNINGS: n · output: json · qa: script اگر exec هست؛ وگرنه manual
```

- Route: step 3, row 3 and the place-name table → [SMS](playbooks-messages.md#sms) and sms.md (in Whalory Pro).
- Language: the JSON has no `lang` key and no prose, and the generic task `sms` names no Iranian platform. With no profile, rule 4 gives the default, fa-IR. A request with no prose takes the output language as its conversation language, so `context` is in Persian.
- Questions: never. The assumptions go into `assumptions`, and anything unknown gets a bracket. The input didn't accept `needs_input`.
- Shape: the brand name comes first, with a colon, and the link sits on its own line. The message doesn't start with `{name}`, because that variable may be empty: Template and variables (in Whalory Pro).
- QA: with `exec`, a script. A direct API call has no shell. In `claude -p` too, a command that asks for permission is denied unless `--allowedTools` or a permission mode opened it ([docs](https://code.claude.com/docs/en/headless)). Wherever the script didn't run, QA is manual and `context` ends with «آزمون: دستی (اسکریپت اجرا نشد)».

```json
{
  "text": "[برند]: سفارشِ {order_id} امروز ارسال شد.\nپیگیری: {tracking_url}",
  "assumptions": ["پیامکِ خدماتی فرض شد", "متغیرِ name به کار نرفت، چون ممکن است خالی باشد", "اگر پنل خودش نامِ برند را اولِ پیام می‌گذارد، «[برند]: » حذف شود [تأیید شود]"],
  "needs_verification": ["شمارِ پاره‌ها با بلندترین مقدارِ متغیرها؛ sms.md", "«لغو۱۱» در پیامکِ خدماتی فقط اگر پنل یا اپراتور بخواهد؛ sms.md"],
  "context": "تشخیص: پیامکِ ارسالِ سفارش · خریدار · پروفایل: پیش‌فرض · خودکار · آزمون: اسکریپت"
}
```

## 5. Beauty clinic, high risk

Request in ChatGPT: «یه متن تبلیغ واسه بوتاکس کلینیکمون بنویس، تخفیف ۳۰ درصد»

```
host: chat-plain · inputs: none · operation: write · intent: deliver
format/channel: ad (کانال نامعلوم) · reader: مراجعِ تازه
language: fa · fa-IR · market: ir · conversation: fa · industry/risk: beauty-clinic · high · occasion: none
profile: پیش‌فرض · LEARNINGS: n · output: chat-text · qa: manual
```

- Route: step 3, row 3 («تبلیغ»), with the risk layer of row 19 → [claims.md](fa/claims.md), regulation.md (in Whalory Pro). The market is `ir`, so the Iranian rules apply.
- Questions: yes, before writing. Risk is high and the facts are missing. Three questions. First, the doctor in charge, their medical council number, and the advertising license. Second, the product to be injected and the terms of the discount. Third, the channel. The full text is in the [plain chat example](intake.md#plain-chat-example).
- Boundary: until the license is clear, the copy carries no promise of results and no before-and-after photo. «بوتاکس» is the trade name of one product, and the product's name comes from its license. The discount on a medical service gets a bracket, so its legality is confirmed before publishing.

## 6. Repairing a long text in Claude Code

Request, with a text of about 450 words: «اینو یه دستی بکش»

```
host: chat-tools · inputs: draft (~450 words) · operation: rewrite · intent: deliver
format/channel: همان قالبِ متنِ اصلی · reader: خواننده‌ی متنِ اصلی
language: fa · fa-IR · market: ir · conversation: fa · industry/risk: از متن · low · occasion: none
profile: VOICE.md · LEARNINGS: y · output: chat-text · qa: script
```

- Route: step 1, row 8 → [Style repair](playbooks-repair.md#style-repair). The supplied text is Persian, so the output stays Persian.
- Questions: one, under step 3 of the gate. The text is over 300 words, and «دستی بکش» doesn't say how deep to go. Ask with `AskUserQuestion`, with «جمله‌ها» ("the sentences") as the recommended option. Tone isn't asked, because `VOICE.md` exists.
- QA: `compare.py`, to confirm that no number or name went missing.

## 7. Yalda campaign across channels

Request: «برای یلدا یه کمپین کوچیک می‌خوایم: پست، استوری و پیامک»

```
host: chat-plain · inputs: none · operation: strategize + write · intent: strategize
format/channel: chain (post, story, sms) · reader: از پروفایل
language: fa · fa-IR · market: ir · conversation: fa · industry/risk: از پروفایل · low · occasion: festive (یلدا)
profile: VOICE.md · LEARNINGS: n · output: chat-text · qa: manual
```

- Route: step 2, row 22, with the occasion layer of row 20 → Occasion campaign (in Whalory Pro), [occasions.md](fa/occasions.md).
- Questions: this is strategic work, so it gets one [brief card](intake.md#task-level-and-question-cap) with the channels and the occasion pre-filled. The user completes the measurable goal and the time window in one reply. The host has no web tool, so the research question is also one line of this card, and no second round follows.
- Delivery: the user said «کوچک» ("small"), so the chain stays short: one core message, then one section per channel, all making one claim.

## 8. English tagline for a Berlin bakery

Request: "Write a tagline for my bakery in Berlin"

```
host: chat-plain · inputs: none · operation: write · intent: deliver
format/channel: headline (channel unknown) · reader: new customer, on a phone (default)
language: en · en-US · market: unknown · conversation: en · industry/risk: bakery · low · occasion: none
profile: default · LEARNINGS: n · output: chat-text · qa: manual
```

- Route: step 3, row 3 ("tagline" is a place name for `headline`) → [Tagline and slogan](playbooks-social.md#tagline-and-slogan), with taglines (in Whalory Pro) from the English pack. English copy is in scope, so row 15 doesn't fire.
- Language: the request is in English and nothing earlier in the order decides, so the output is `en`. Berlin sets no English variant, and there is no profile, so the variant is the default, en-US.
- Market: Berlin points to Germany. Whalory has no file for German national rules, so the slot reads `unknown` and the note names Germany. Risk is low, so nobody asks about it.
- Questions: step 4 of the gate, so the draft comes first. Three tagline options come, which is the default for headlines, with a bracket for any claim that needs a fact. The note ends with one follow-up question: "What's one real thing about the bakery, such as the bread people come back for?"
- Note: `Diagnosis: tagline · new customer · Profile: default · follow-up question · QA: manual`, then the [market line](router.md#diagnosis-note) `Market: unknown (Germany); local rules not checked.`

## 9. "Just write" in a chat

Request in ChatGPT: «یه پیامک برای معرفی صندوق درآمد ثابت‌مون بنویس، سود پیش‌بینی‌شده ۲۸ درصد سالانه. فقط بنویس»

- Flags: `interactive` is on, and so is `no_questions`. The host stays `chat-plain`, and the delivery is copy and note.
- Route: step 3, row 3 (SMS), with the risk layer of row 19: «صندوق» and «سودِ پیش‌بینی‌شده». The market is `ir`.
- Questions: none, under step 1 of the gate. The copy carries brackets. The assumptions sit at the top of the note, and the fund's license and the projected-return figure get «پیش از انتشار تأیید شود». It's a promotional SMS, so its last line is «لغو۱۱».
- Note: «تشخیص: پیامکِ تبلیغاتی · مشتریِ بالقوه · پروفایل: پیش‌فرض · فقط بنویس · خطر: بالا · آزمون: دستی»
