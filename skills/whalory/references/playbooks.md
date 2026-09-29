# Playbooks

This file maps Whalory's playbooks. The task index shows which playbook each request reaches. The text of each playbook sits in one of six [playbook files](#playbook-files): its steps, questions, references, output, and quality assurance (QA). After you find the profile and detect the context, find the task's row in the index. Then read only that playbook's file and the references it names. Each playbook lists its Persian references after "fa:" and its English references after "en:"; read the list for the output language.

## Contents

- [Playbook files](#playbook-files)
- [Shared steps](#shared-steps)
- [Task index](#task-index)
- [Near-miss tasks](#near-miss-tasks)
- [When the task is not in the index](#when-the-task-is-not-in-the-index)

---

## Playbook files

Each task family has its own file. Open only the file of the playbook you need; there is no need to read them all.

| File | Family |
|---|---|
| [playbooks-product.md](playbooks-product.md) | [Products and stores](playbooks-product.md#products-and-stores) |
| [playbooks-social.md](playbooks-social.md) | [Social media and messaging apps](playbooks-social.md#social-media-and-messaging-apps); [Headlines, ads, and campaigns](playbooks-social.md#headlines-ads-and-campaigns) |
| [playbooks-messages.md](playbooks-messages.md) | [Customer messages](playbooks-messages.md#customer-messages) |
| [playbooks-web.md](playbooks-web.md) | [Interfaces and digital products](playbooks-web.md#interfaces-and-digital-products); [Pages and long-form copy](playbooks-web.md#pages-and-long-form-copy) |
| [playbooks-repair.md](playbooks-repair.md) | [Rewriting and review](playbooks-repair.md#rewriting-and-review) |
| [playbooks-strategy.md](playbooks-strategy.md) | [Voice, strategy, and teaching](playbooks-strategy.md#voice-strategy-and-teaching) |

---

## Shared steps

Every playbook assumes these eight steps and adds only what is specific to its own task.

1. Profile and learnings. Find the voice profile in the [order that SKILL.md sets](../SKILL.md#profile-lookup-order); its structure is in [voice-profile.md](voice-profile.md). If a `LEARNINGS.md` sits next to the profile, read it too. With no profile, take the closest [starter profile](../profiles/starters/README.md) and say so in the note, or run [Voice profile in three questions](playbooks-strategy.md#voice-profile-in-three-questions).
2. Detection and questions. Fill the context card silently, as [router.md](router.md#context-card) describes: host, input, task, intent, channel, output language, reader, risk, and occasion. The six context questions are in [judgment.md](judgment.md#six-questions-before-writing). Only [intake.md](intake.md#decision-order) decides whether to ask, how many questions, and how to ask them. The "Questions" line of each playbook only names that task's row in the [question bank](intake.md#question-bank-by-task). The "no-default slot" in that line comes from the same bank: something with no safe default.
3. Playbook. Find the task's row in the [task index](#task-index). If you are torn between two playbooks, see [near-miss tasks](#near-miss-tasks).
4. Materials. See [brief.md](brief.md) and [gathering.md](gathering.md). An unknown detail gets a bracket, such as «[وزن تأیید شود]» in Persian or `[confirm: weight]` in English; making it up is not allowed.
5. Draft in the playbook's pattern, then do three editing passes: cut, sharpen, and listen ([fa/craft.md#سه-دورِ-ویرایش](fa/craft.md#سه-دورِ-ویرایش), [en/craft.md#three-editing-passes](en/craft.md#three-editing-passes)).
6. QA. With code execution: `python <skill-path>/scripts/lint.py <text> --profile <profile> --format <format>`. The linter picks Persian or English for each file, line, or cell. Each playbook's QA line gives the format id. For a channel's character limit, add `--channel <id>` when `data/channels/` is present; otherwise take the limit from [fa/channels.md](fa/channels.md) or [en/channels.md](en/channels.md). In a rewrite, also run `compare.py`; without it, count the numbers, names, and conditions by hand before and after. The commands are in [Scripts](../SKILL.md#scripts). When the Whalory MCP server is connected, its `lint_text` and `lint_file` tools do the same job ([MCP tools](../SKILL.md#mcp-tools)). Without code execution, or when a script is refused or Python is missing, use [manual QA](../SKILL.md#manual-qa) and [review.md](review.md). The note says which one ran: "QA: script", "QA: manual", or "QA: manual (script not run)"; in Persian, «آزمون: اسکریپت»، «آزمون: دستی» or «آزمون: دستی (اسکریپت اجرا نشد)».
7. Delivery. Give the finished copy first, then a short internal note with the diagnosis line, the gaps, and the claims that need confirming. How you deliver depends on the host and the intent: see the [delivery table](router.md#delivery-by-host-and-intent). The [diagnosis line](router.md#diagnosis-note) follows the conversation language, for example «تشخیص: کپشنِ اینستاگرام · مشتریِ تازه · پروفایل: cafe (آغاز) · پرسشِ تکمیلی · آزمون: دستی» or `Diagnosis: Instagram caption · first-time customer · Profile: cafe (starter) · follow-up question · QA: manual`.
8. Learning. Accepted feedback goes into the profile or into `LEARNINGS.md`; the chat's memory does not last: [judgment.md](judgment.md#learning).

Two cases always require the claims file of the output language. One is a sensitive industry, such as health, finance, law, or children. The other is any task with medium or high [risk](router.md#risk-level). That file is [fa/claims.md](fa/claims.md) for Persian and [en/claims.md](en/claims.md) for English. Each industry's regulators are listed in fa/regulation.md (in Whalory Pro) for the Iranian market. For the US, the UK, and the EU, they are in en/regulation.md (in Whalory Pro). The router picks the file by market: [output language, variant, and market](router.md#output-language-variant-and-market). In these long files, read only the section for that industry or claim; search for its heading.

---

## Task index

Each row is one task, and the "Playbook" column leads to its family file. The "Signals (fa)" and "Signals (en)" columns show phrases that users actually write; a request with the same meaning reaches the same row. The "Intent" column shows the usual intent of the task: `deliver`, `teach`, `review`, or `strategize`. If the user wants the same task to learn from or to get a score, the intent changes, and the output follows the [delivery table](router.md#delivery-by-host-and-intent). The "Chain" column names the playbooks that usually come next.

| Task | Intent | Signals (fa) | Signals (en) | Typical input | Playbook | Chain |
|---|---|---|---|---|---|---|
| Short copy for one product, for a site or a sales page | `deliver` | «یه متن واسه محصولم»، «توضیحِ محصول»، «معرفیِ این عسل» | "product description", "write copy for this product", "a blurb for our honey" | Product sheet, product photo, name, and ingredients | [Product description](playbooks-product.md#product-description) | Product specifications; Caption; Marketplace listing |
| App store page: Cafe Bazaar, Myket, App Store, or Google Play | `deliver` | «توضیحِ اپ برای کافه‌بازار»، «متنِ صفحه‌ی مایکت»، «تغییراتِ نسخه‌ی جدید» | "App Store description", "Google Play listing", "what's new text for the update" | App features, the new version, screenshots | [Product description](playbooks-product.md#product-description) | Tagline and slogan; UI microcopy |
| Caption for a post | `deliver` | «یه کپشن»، «متن واسه پیج»، «زیرِ این عکس چی بنویسم» | "write a caption", "IG post copy", "what do I write under this photo" | Photo or post idea, profile | [Caption](playbooks-social.md#caption) | Tagline and slogan; Carousel; Stories |
| LinkedIn post, or another text-first post on X, Threads, Bluesky, or Facebook | `deliver` | «پستِ لینکدین»، «یه پست برای لینکدین» | "LinkedIn post", "write a tweet about this", "post for Threads or Bluesky" | News or idea, the author's role, profile | [Social post](playbooks-social.md#social-post) | Caption; Email |
| Transactional or marketing SMS, or a one-time code | `deliver` | «پیامکِ تخفیف»، «اس‌ام‌اسِ یادآوری»، «متنِ کدِ تأیید»، «پترنِ پنل» | "promo text message", "SMS reminder", "verification code text" | Offer or event, variables, sender name | [SMS](playbooks-messages.md#sms) | Channel post; Measurement and A/B testing |
| One email | `deliver` | «یه ایمیل برای مشتری‌ها»، «خبرنامه»، «ایمیلِ خوش‌آمد» | "email to our customers", "newsletter", "welcome email" | News or offer, recipients | [Email](playbooks-messages.md#email) | Tagline and slogan; Email sequence |
| Cold outbound email | `deliver` | «ایمیلِ سرد»، «ایمیل به مشتریِ بالقوه» | "cold email", "outbound email to prospects", "B2B outreach email" | Offer, the recipient's company and role, the reason to write now | [Email](playbooks-messages.md#email), with en/email.md#cold-outreach (in Whalory Pro) | Email sequence; Claim and license check |
| Reply to one customer's message or ticket | `deliver` | «جوابِ این مشتری»، «یه جوابِ مؤدبانه»، «مشتری شاکیه» | "reply to this customer", "a polite answer", "the customer is angry" | The customer's message, the facts of the case | [Customer reply](playbooks-messages.md#customer-reply) | Hard message |
| Button, label, field hint, or confirmation message | `deliver` | «متنِ دکمه»، «یو‌ایکس رایتینگ»، «متن‌های این فرم» | "button text", "UX writing", "copy for this form" | Screenshot or list of strings | [UI microcopy](playbooks-web.md#ui-microcopy) | Error, empty, and waiting states |
| Error, empty state, waiting, or failed payment | `deliver` | «پیامِ خطای پرداخت»، «وقتی چیزی پیدا نشد»، «لودینگ»، «صفحه‌ی بعد از درگاه» | "payment error message", "copy for when nothing is found", "loading message" | The event, the user's next step | [Error, empty, and waiting states](playbooks-web.md#error-empty-and-waiting-states) | UI microcopy |
| About page | `deliver` | «صفحه‌ی درباره‌ی ما»، «معرفیِ شرکت برای سایت»، «ما کی هستیم» | "about page", "rewrite this about page", "who we are" | Founding story, people, place | [About page](playbooks-web.md#about-page) | Personal bio; Landing page |
| Headline, slogan, or main button text | `deliver` | «یه تیتر»، «شعارِ برند»، «اسلوگان» | "headline", "brand tagline", "slogan ideas" | Offer, profile | [Tagline and slogan](playbooks-social.md#tagline-and-slogan) | Landing page; Measurement and A/B testing |
| Making a text better | `deliver` | «بهترش کن»، «ویرایش کن»، «درستش کن»، «ماشینی نباشه» | "make this better", "edit this", "make it sound less like AI" | The user's text | [Style repair](playbooks-repair.md#style-repair) | Scoring and review |
| Score and critique | `review` | «نمره بده»، «یه نگاه بنداز»، «ایراداشو بگو» | "score this", "take a look at this", "what is wrong with it" | Finished text | [Scoring and review](playbooks-repair.md#scoring-and-review) | Style repair; Claim and license check |
| Quick profile for a brand with no profile | `deliver` | «صدای برندِ ما»، «لحنِ ما چیه»، «یه VOICE بساز» | "our brand voice", "what is our tone", "make a VOICE file" | Nothing, or one earlier text | [Voice profile in three questions](playbooks-strategy.md#voice-profile-in-three-questions) | Full voice profile for a new brand; Verbal identity from scratch |
| A task with no row | all four | هر درخواستی که بالا نیامده | any request not listed above | Whatever there is | [When the task is not in the index](#when-the-task-is-not-in-the-index) | The closest playbook |

---

## Near-miss tasks

Some requests sit between two playbooks. Look for the deciding signal in the request, the file, or the profile. If there is none, take the default in the last column and write it in the diagnosis line. The user can then correct it with one sentence.

| Choice | Deciding signal | Default when there is no signal |
|---|---|---|
| Landing page, about page, or home page | A landing page is where an ad or a campaign sends people: one offer, one button. An about page is for someone who wants to know who is behind the work. A home page has several paths for several readers. It follows the landing page playbook: a headline, then one paragraph and one button for each path. | «صفحه‌ی اولِ سایت», like "homepage", means a landing page, as in the [unstated genre](judgment.md#unstated-genre) table. |
| Caption or carousel | A carousel has several slides, each with one idea you can count. A caption is one moment under one image. «چند نکته»، «مرحله‌به‌مرحله» and «اسلاید», like "tips", "step by step", and "slides", mean a carousel. | Caption. If the content has more than three points you can count, suggest a carousel in the note. |
| Caption or social post | A caption sits under a photo or a video and shows one moment. A social post is text-first: on LinkedIn, X, Threads, Bluesky, or a Facebook feed, the words carry it, image or not. Instagram, Reels, or TikTok means a caption; LinkedIn, X, Threads, or Bluesky means a social post. | Caption. «پست» or «پیج» with no platform named, like "post" alone, stays a caption, as in the router's [place-name table](router.md#place-names-and-format-ids). Social post only when the request names LinkedIn, X, Threads, Bluesky, or a Facebook feed. |
| Style repair or note cleanup | Text written for an outside reader that only needs to get better is style repair. Meeting notes, a transcribed voice message, and a jumbled list that needs a structure are note cleanup. | Full sentences: style repair. Fragments or spoken fillers: note cleanup. |
| SMS or a message in Bale, Eitaa, or Telegram | An SMS goes out from an SMS panel, is counted in segments, and costs money. A messaging-app message goes out from a channel or a bot, has formatting and buttons, and has its own limit. | The word «پیامک» or «اس‌ام‌اس», like "SMS" or "text message", means SMS. «پیام» ("message") alone means the channel that the profile or `LEARNINGS.md` names; if none, SMS, with one line in the note. |
| Product description or marketplace listing | A product description sits on the brand's own site or page and has the brand's voice. A marketplace listing sits on Digikala, Basalam, Divar, Torob, Amazon, Etsy, or eBay. It follows that marketplace's rules for titles, fields, and banned content. | The marketplace's name or the columns of its file appear: marketplace listing. Otherwise, product description. |
| Hard message or customer reply | A customer reply answers one person about one case. A hard message is news that reaches everyone or a group: an outage, a general delay, a price increase. A public complaint under a post or on a map needs the review-reply playbook. | One person and one incoming message: customer reply. A group or the public: hard message. |
| Error message or hard message | Error text sits on one user's screen and is about what that user is doing at that moment. A hard message is news that reaches everyone: a service outage, a general delay, a price increase. | On the screen, for one action: error message. In a channel, an email, or an SMS for everyone: hard message. |
| UI microcopy or microcopy in a code repository | A screenshot or a list in the chat: UI microcopy. A locale file in a repository, with file access: microcopy in a repository. | File access exists and a language file was found: repository. Otherwise, UI microcopy. |
| Ad copy or ad campaign | An ad is one text on one network. A campaign is one concept across several channels and formats. | One network named: ad copy. Two channels or more: campaign. |
| Profile in three questions, full profile, or verbal identity | The three questions are a quick start for a brand that has no [brand profile](intake.md#definitions); a starter profile does not replace them. A full profile is built from three to ten existing texts. Verbal identity is the strategy document for the whole brand. | No existing text given: three questions. Texts given: full profile. A "document" or a "brand guide" requested: verbal identity. |

---

## When the task is not in the index

1. Take the closest playbook by goal and by length, from the table below.
2. Run all the shared steps.
3. In the diagnosis line, say which playbook you started from and what you changed.
4. If the task comes up again, its playbook joins its family file, with a row in the task index.

| Goal | Short copy | Long copy |
|---|---|---|
| Inform | [SMS](playbooks-messages.md#sms) | [Email](playbooks-messages.md#email) |
| Tell a story | [Caption](playbooks-social.md#caption) | [About page](playbooks-web.md#about-page) |
| Sell | [Tagline and slogan](playbooks-social.md#tagline-and-slogan) | [Product description](playbooks-product.md#product-description) |
| Build trust | [Customer reply](playbooks-messages.md#customer-reply) | [About page](playbooks-web.md#about-page) |
| Help a user act in an interface | [UI microcopy](playbooks-web.md#ui-microcopy) | [UI microcopy](playbooks-web.md#ui-microcopy) |
| Judge an existing text | [Scoring and review](playbooks-repair.md#scoring-and-review) | [Style repair](playbooks-repair.md#style-repair) |

**Questions:** The closest task's row in the [question bank](intake.md#question-bank-by-task); if there is none, "Base questions".
**Output:** As the closest task's playbook says, with one line in the note about the changes.
**QA:** The QA of that playbook, with the `--format` of the closest format.

