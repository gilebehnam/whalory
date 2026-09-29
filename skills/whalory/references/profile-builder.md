# Profile builder

A voice profile can be built by four routes. The quick route gives a working profile from three questions. The other three routes complete it, and a full profile comes from combining all three. Open this file when a brand has no profile, or when its profile needs completing or calibrating. The file structure and the meaning of each dial are in [voice profile](voice-profile.md).

## Contents

- [Quick route: three questions](#quick-route-three-questions)
- [English route](#english-route)
- [Route 1: from existing copy](#route-1-from-existing-copy)
- [Route 2: short interview](#route-2-short-interview)
- [Route 3: calibration round](#route-3-calibration-round)
- [Filling in the files](#filling-in-the-files)
- [Where to save](#where-to-save)
- [Profile test](#profile-test)
- [Maintenance](#maintenance)

## Quick route: three questions

When: the task is [brand-building](intake.md#definitions) and no [brand profile](intake.md#definitions) turned up in the [lookup order](voice-profile.md#lookup-order). The conversation must also be two-way. Both terms keep their definitions from `intake.md`. A starter profile that turned up doesn't count as a brand profile, because it hasn't captured this brand's voice. Verbal identity and tone guides for a brand without a profile also start with these three questions. The brief card follows them ([decision order](intake.md#decision-order)).

When not:
- About pages, taglines, and landing pages. These use a voice and don't build one. They are written with a starter profile, and their questions come from their own row in the [question bank](intake.md#question-bank-by-task).
- Micro tasks such as a button, an SMS, or an error message. The closest [starter profile](../profiles/starters/README.md) is enough.
- The user said `just write`, or the task is automated with no conversation. Work without questions, with a starter profile, and say so in the internal note.
- A brand profile exists. Don't ask about tone; the profile has the answer.

The general policy on asking, the question cap, and how each assistant asks are in [intake.md](intake.md). This section holds only the three profile questions. For English copy, use the [English route](#english-route).

### The three questions

| # | Question | Options | Where the recommended option comes from | Where it goes |
|---|---|---|---|---|
| 1 | Do you address customers as «تو» or «شما»? | «تو», «شما», depends on the place | The starter profile for that industry | `address` |
| 2 | How formal should the copy be? | casual, in between, formal | The starter profile; "in between" if the industry is unknown | `register` and the dials |
| 3 | An earlier text you like? | send it, none | none | Benchmark text and limits |

Ask all three in one message. The recommended option comes first, labeled «(پیشنهادی)». An example for a café without a profile:

```
برای اینکه متن صدای خودتان را داشته باشد، سه پرسشِ کوتاه:
۱. با مشتری «تو» می‌گویید یا «شما»؟ الف) تو (پیشنهادی)  ب) شما  ج) بسته به جا
۲. متن چقدر رسمی باشد؟ الف) خودمانی (پیشنهادی)  ب) میانه  ج) رسمی
۳. یک متنِ قبلی که دوستش دارید، از خودتان یا از هر برندِ دیگر، این‌جا بگذارید. اگر ندارید، بنویسید «ندارم».
کوتاه جواب بدهید، مثلاً «۱الف ۲ب ندارم». اگر نمی‌خواهید جواب بدهید، فقط بنویسید «بنویس»؛ با گزینه‌های پیشنهادی می‌نویسیم و جای واقعیت‌ها کروشه می‌گذاریم.
```

In an assistant with a question tool, the same three questions go out with the short headers «خطاب», «رسمیت», and «متنِ نمونه». The sample text comes back as a free answer.

### From answers to profile

| Answer | In the md file | In the json file |
|---|---|---|
| «تو» | Address: «تو» | `"address": "to"` |
| «شما» | Address: «شما» | `"address": "shoma"` |
| Depends on the place | The "one voice, many tones" table | `"address": "any"`, plus the address of each format in `formats` |
| Casual | Colloquial written style | `"register": "colloquial"`; formality 2, warmth 4, loud marks 1 |
| In between | Plain written style | `"register": "formal"`; formality 3, warmth 3 |
| Formal | Precise written style | `"register": "formal"`; formality 4, warmth 2, humor 1 |
| Earlier text | Benchmark text, if it passes the test below | Sentence cap, emoji, and exclamation marks from that text's stats |
| None | The starter's benchmark text, labeled «نمونه‌ی آموزشی» | The dials of that starter |

Take the remaining dials from the starter profile for the industry. If the industry is unknown, use the default column in [tone dials](voice-profile.md#tone-dials).

Earlier-text test: the user's text becomes the benchmark text only if it passes all three checks.
- No pattern from the AI tells lists ([fa](fa/ai-tells.md), [en](en/ai-tells.md)).
- Real details instead of adjectives.
- Written by this brand. Another brand's text is only a tone model: its numbers are taken, not its words or sentences. In the md file it gets the label «الگوی لحن، از برندِ دیگر», or "tone model, from another brand" in an English profile.

If scripts can run, take the stats from the text itself:

```bash
python <skill path>/scripts/profile_stats.py liked.txt
```

### Saving

Draft both files from [_template.md](../profiles/_template.md) and [_template.json](../profiles/_template.json). Then ask, in the conversation language: «ذخیره‌اش کنم در VOICE.md؟» or "Save it as `VOICE.md`?" With no project folder, offer `~/.whalory/profiles/` instead. Save only on a "yes" («بله»); the location rules are in [where to save](#where-to-save). In the history section, write in the profile's language: «پروفایلِ سریع از سه پرسش؛ خالی: [بخش‌ها]» or `Quick profile from three questions; empty: [sections]`. A quick profile works, but it isn't complete; after a few tasks, complete it with route 1 or route 2.

## English route

When: the same conditions as the quick route, and the brand writes in English. Register and address are Persian-only settings, so the English route asks about the variant instead. It keeps the three-question limit.

### Three questions in English

Ask all three in one message, with the recommended option first. The recommended variant comes from the target market or channel; otherwise it is `en-US`. With a question tool, use the short headers "Variant", "Formality", and "Sample text". An example for a software company without a profile:

```
So the copy sounds like you, three quick questions:
1. Which English do your readers use? a) US English (recommended)  b) UK English  c) another: Australian, Canadian, Irish, Indian, or New Zealand English
2. How formal should the copy be? a) casual  b) in between (recommended)  c) formal
3. Paste one earlier text you like, from you or any brand. If you have none, write "none".
Short answers work, such as "1a 2b none". If you'd rather not answer, just reply "write". We'll use the recommended options and put brackets where facts are missing.
```

### From answers to English settings

| Answer | In the md file | In the json file |
|---|---|---|
| A variant | Language and style: that variant | `"language": "en"`, `"variant"` such as `"en-US"`, `"en-GB"`, or `"en-AU"`, and `"spelling": null` |
| Casual | Casual, with contractions | `"contractions": "use"`; formality 2, warmth 4, loud marks 1 |
| In between | Plain and friendly, with contractions | `"contractions": "use"`; formality 3, warmth 3 |
| Formal | Precise; no negative contractions | `"contractions": "positive-only"`; formality 4, warmth 2, humor 1 |
| Earlier text | Benchmark text, if it passes the earlier-text test | Sentence cap, emoji, exclamation marks, and the Oxford comma from its stats |
| None | The English starter's benchmark text, labeled "teaching example" | The dials and the Oxford comma of that starter |

With `"spelling": null`, the spelling follows the variant ([spelling](voice-profile.md#spelling)). `register` and `address` stay `"any"`. `house_style` and `reading_grade_max` stay `null` unless the brand names a style guide or a reading level. Formal maps to `"positive-only"`. The reason: GOV.UK allows contractions such as "you'll" but not negative ones such as "can't" ([clear language](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-language/), checked 2026-09-27).

Start from [_template.en.md](../profiles/_template.en.md) and [_template.en.json](../profiles/_template.en.json), or from the closest English starter in `profiles/starters/en/`. The keys are defined in [language and style keys](voice-profile.md#language-and-style-keys). For English samples, `profile_stats.py` also reports the variant, spelling, Oxford comma, and contractions it finds.

### Bilingual brands

A brand that publishes in both languages gets one profile with `"language": "bilingual"`. The limit stays at three questions: ask the Persian three (address, formality, sample text), since the formality answer sets the dials for both languages. The English variant comes from the market or channel, or else defaults to `en-US`, and the internal note says which.

- Set `variant` to the primary variant, and list every published variant in `variants`, primary first: `["fa-IR", "en-US"]`.
- Put per-language settings in `by_lang`, such as `{"en": {"max_words": 25}}` ([bilingual brands](voice-profile.md#bilingual-brands)).
- Fill `brand.latin` and `romanization`, and add a two-column glossary (Persian term, English term) to the word section of the md file.
- Name the base language in the md file: facts come from it, and the other version takes its facts only from there (fact lock (in Whalory Pro)).

## Route 1: from existing copy

When the brand has texts it calls "this is our voice":

1. Collect three to ten good texts: pages, captions, emails, replies. Machine-written text is no use, and neither is work from an agency the brand wasn't happy with.
2. Take the stats:

```bash
python <skill path>/scripts/profile_stats.py good1.txt good2.txt good3.txt
```

The script gives the mean and spread of sentence length, the register, and the rate of emoji and exclamation marks. It also lists frequent words and any AI patterns present, and it proposes a starting json file.
3. Group by format. If captions and SMS messages differ in their stats, that difference is the "one voice, many tones" table, and it goes into `formats`.
4. Pick the benchmark text. Choose the text that is short, has real details, and got the fewest lint warnings. Take it apart with anatomy (in Whalory Pro).
5. Don't turn existing AI patterns into the profile. If the brand's texts carry big adjectives without evidence, those adjectives must go, and they don't become part of the voice.
6. Add one bad text too, one the brand isn't happy with, with the reason. A negative example makes the edge of the voice clearer.

## Route 2: short interview

If no good text is at hand, ask the brand owner these questions. Short answers are enough.

- Identity:
  - In one sentence with one verb, what do you do? No generic corporate words.
  - How exactly is the brand name written, in Persian and in Latin script?
  - Which terms do only you use?
- Reader:
  - Who usually reads you? How old, where, with what worry?
  - On what screen or in what state? On a phone in the metro, at a desk, the night before a deadline?
  - Do they know the terms of your trade, or do we need to explain them?
- Tone:
  - If your brand were a person, would it say «تو» or «شما» to customers? Everywhere, or depending on the place?
  - In English: US or UK English? Contractions or not? Which house style guide, if any?
  - Where is humor allowed, and where never?
  - Are wordplay, double meanings, and poetry part of the brand's voice? Where not?
  - Three brands or writers whose tone you like, and what exactly you like in each?
- Formats:
  - Which formats do you write most?
  - In which format should the tone be drier or warmer than usual, such as an error message or a caption?
- Limits:
  - What must we never say, even if it seems true?
  - Which claims need proof: results, returns, treatment, rankings, licenses?
  - What isn't ready yet and must not be presented as ready?
- Words:
  - Which words do you like, and which do you dislike?
  - Which words must be spelled the same way everywhere?

In a Persian conversation, ask them in this wording:

**هویت**
- در یک جمله و با یک فعل، چه می‌کنید؟ بی‌واژه‌های کلیِ شرکتی.
- نامِ برند دقیقاً چطور نوشته می‌شود، فارسی و لاتین؟
- اصطلاح‌هایی که فقط شما به کار می‌برید چیست؟

**خواننده**
- معمولاً چه کسی می‌خواند؟ چند سال دارد، کجاست، چه نگرانی‌ای دارد؟
- روی چه صفحه‌ای یا در چه حالی می‌خواند؟ روی موبایل در مترو، پشتِ میز، شبِ آخرِ مهلت؟
- اصطلاحِ کارِ شما را می‌شناسد، یا باید توضیح بدهیم؟

**لحن**
- اگر برندتان یک آدم بود، با مشتری «تو» می‌گفت یا «شما»؟ همه‌جا، یا بسته به جا؟
- اگر انگلیسی هم می‌نویسید: آمریکایی یا بریتانیایی؟ با شکلِ کوتاه‌شده‌ی فعل‌ها یا بی آن؟ کدام راهنمای سبک، اگر دارید؟
- کجا شوخی مجاز است و کجا هرگز؟
- بازیِ کلمه، ایهام و شعر جزوِ صدای برند است؟ کجا نه؟
- سه برند یا نویسنده که لحنشان را دوست دارید، و از هرکدام دقیقاً چه چیزی؟

**قالب**
- کدام قالب‌ها را بیشتر می‌نویسید؟
- در کدام قالب لحن باید خشک‌تر یا گرم‌تر از معمول باشد؟ مثلاً پیامِ خطا یا کپشن.

**مرز**
- چه چیزی را هرگز نباید بگوییم، حتی اگر درست به نظر برسد؟
- کدام ادعاها مدرک لازم دارند؟ نتیجه، سود، درمان، رتبه، مجوز؟
- چه چیزی هنوز آماده نیست و نباید آماده نشانش داد؟

**واژه**
- از چه واژه‌هایی خوشتان می‌آید و از چه واژه‌هایی نه؟
- املای کدام واژه‌ها باید یکدست باشد؟

## Route 3: calibration round

After the profile draft:

1. Write one short text in two versions: one with the profile's dials, one with a single dial one step higher or lower.
2. Ask the brand owner which is closer.
3. Adjust the dial.
4. Repeat twice, no more.

If the brand has a format table, calibrate in two formats that sit far apart, such as a caption and an error message.

## Filling in the files

- If the brand's industry has a [starter profile](../profiles/starters/README.md), start from it. Otherwise, start from [_template.md](../profiles/_template.md) and [_template.json](../profiles/_template.json), or the English templates for an English brand.
- Fill in the md file first, then the json file with the same decisions. The sync rule is in [two files, one decision](voice-profile.md#two-files-one-decision).
- The json file needs `"schema_version": 2`, all eight dials, and every format with its own tone in `formats`. A Persian profile also needs `address`; an English or bilingual one needs `language` and `variant`.
- Give both files the same name: `VOICE.md` and `voice.json` in a project, or `<brand>.md` and `<brand>.json` in `~/.whalory/profiles/`.

## Where to save

| Situation | Where |
|---|---|
| A project folder or repository is open and writing is possible | `VOICE.md` and `voice.json` at the project root |
| The same brand is used in several projects, or there is no project folder | `~/.whalory/profiles/<brand>.md` and `<brand>.json` |
| A chat without files | The text of both files in the reply, so the user can keep them |

The skill's own folder is no place for a profile, because an update wipes it. No file is created until the user says "yes". `LEARNINGS.md` is created next to the profile, from the [learnings note template](../profiles/LEARNINGS-template.md).

## Profile test

The profile is ready when:

- [ ] The benchmark text passes lint with the same json file and no errors.
- [ ] `python -m json.tool voice.json` opens the json file cleanly.
- [ ] `schema_version` is 2, and all eight dials have numbers.
- [ ] Both files agree: dials, address, the tone of each format, and every "avoid" word in `avoid` or `banned`.
- [ ] Every `prefer` key is also in `avoid`.
- [ ] An English or bilingual profile passes the [validation rules](voice-profile.md#validation-rules).
- [ ] Two different people write one text with this profile, and their voices come out close.
- [ ] The claim boundary for the brand's industry comes from sensitive claims ([fa](fa/claims.md), [en](en/claims.md)) and regulation (fa (in Whalory Pro), en (in Whalory Pro)).
- [ ] No AI pattern appears in the "say" section or in the examples.
- [ ] The profile lives outside the skill folder.

## Maintenance

- Every three months, measure three new good texts with `profile_stats.py`. If the numbers have drifted from the profile, fix either the texts or the profile, on purpose.
- Every profile change has a date and a reason, in the history section of that file.
- Anything repeated three times in `LEARNINGS.md` moves into the profile itself; the method is in [learning](judgment.md#learning).
- A version 1 profile is updated with the [version 2 steps](voice-profile.md#version-1-and-version-2).
