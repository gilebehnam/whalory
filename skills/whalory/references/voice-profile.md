# Voice profile

The profile is what turns this skill from "a good method" into "the voice of one particular brand." This file describes the profile's structure: its two files, where they live, and the order in which Whalory looks for them. The eleven tone dials and the "one voice, many tones" table also live here; that table keeps the tone of each format separate. Open this file whenever you read, write, or lint a profile. To build a new profile, start with the [profile builder](profile-builder.md).

## Contents

- [Two files, one decision](#two-files-one-decision)
- [Where to keep it](#where-to-keep-it)
- [Lookup order](#lookup-order)
- [Profile sections](#profile-sections)
- [Tone dials](#tone-dials)
- [Register and address](#register-and-address)
- [Language and style](#language-and-style)
- [One voice, many tones](#one-voice-many-tones)
- [Precedence](#precedence)
- [The JSON file, key by key](#the-json-file-key-by-key)
- [Reading and migrating old profiles](#reading-and-migrating-old-profiles)
- [Incomplete profile](#incomplete-profile)

## Two files, one decision

Every profile has two files with the same name. Both record one decision, each for a different reader:

| File | Who reads it | What it holds |
|---|---|---|
| `<name>.md` | The model, the writer, and anyone who approves the text | Reader, benchmark text, tone and address, language and style, dials, format table, words, claim boundary, examples, and the reason for each decision |
| `<name>.json` | The linters: `scripts/lint.py`, which runs [lint_fa.py](../scripts/lint_fa.py) for Persian and `lint_en.py` for English | The same decisions as rules a script can run |

Only the model reads the md file; lint reads only the json file. If one changes and the other doesn't, the writer writes in one voice while lint measures another. So:

- Every number, every address, and the tone of every format match in both files.
- Every "avoid" word in the md file is also in the `avoid` or `banned` list. If it has a replacement, that goes in `prefer` too.
- Every `prefer` key also appears in `avoid`. Lint suggests a replacement only for a word that is in `avoid`.
- Each word needs to appear once, in the form the md file uses. When matching Persian entries, lint ignores the kasra and the zero-width non-joiner (ZWNJ): «سودِ تضمینی» also finds «سود تضمینی».
- The reason for a decision lives only in the md file. The json file holds no explanations, except one sentence in the `note` key of each format.
- A change lands in the md file first, with a date and reason in the history section, then in the json file.

Blank templates: [_template.md](../profiles/_template.md) and [_template.json](../profiles/_template.json) for Persian, and [_template.en.md](../profiles/_template.en.md) and [_template.en.json](../profiles/_template.en.json) for English. Whalory's own voice: [whalory.md](../profiles/whalory.md) and [whalory.en.md](../profiles/whalory.en.md).

## Where to keep it

| For | Where | Files |
|---|---|---|
| One project or repository | The root of that project | `VOICE.md` and `voice.json`, or both inside a `voice/` folder |
| One brand across several projects, or several brands in one agency | `~/.whalory/profiles/`; on Windows, `%USERPROFILE%\.whalory\profiles\` | `<brand>.md` and `<brand>.json` |
| Starter profiles and Whalory's own voice | The skill's [profiles](../profiles/) folder | Read and copy only |

Don't keep a brand profile in the skill folder. A Whalory update replaces the whole skill folder, and the profile goes with it. `~/.whalory/profiles/` sits outside the skill, and updates don't touch it.

- File name: `<brand>` is a Latin slug with lowercase letters, digits, and `-`, such as `cafe-noon`. The same slug goes in the `name` key.
- The learnings note always sits next to the profile that was chosen. Template: [LEARNINGS-template.md](../profiles/LEARNINGS-template.md). Method: [learning](judgment.md#learning).

| Profile | Learnings note |
|---|---|
| `VOICE.md` at the project root | `LEARNINGS.md` at the project root, next to `VOICE.md` |
| `voice/VOICE.md` | `voice/LEARNINGS.md` |
| `~/.whalory/profiles/<brand>.md` | `~/.whalory/profiles/<brand>.LEARNINGS.md`, next to `<brand>.md` |

Several brands share `~/.whalory/profiles/`, so each note's name starts with the brand slug, and the notes of two brands never mix. Don't keep a note next to the profiles inside the skill folder; an update deletes it.

## Lookup order

Before every task, Whalory checks these places in order. The first profile found is the one used. The reference order is in [`SKILL.md`](../SKILL.md#profile-lookup-order), and this list repeats it.

1. A profile the user gave in this conversation.
2. `VOICE.md`, `voice.json`, or `voice/VOICE.md` at the project root.
3. `~/.whalory/profiles/<brand>.md` or `<brand>.json`.
4. The file for this brand in the skill's own `profiles/` folder.
5. The closest [starter profile](../profiles/starters/README.md) in the output language; English starters are in `profiles/starters/en/`. Your internal note says it isn't the brand's own voice yet.
6. [whalory.md](../profiles/whalory.md) or [whalory.en.md](../profiles/whalory.en.md), when Whalory speaks as itself.
7. The defaults: the default column in [tone dials](#tone-dials), address «شما» for Persian, `en-US` for English, and zero emoji. Say so in the internal note.

Once a profile is found, read the learnings note next to it too, if there is one (`LEARNINGS.md` or `<brand>.LEARNINGS.md`). A profile with only an md file is enough for writing; to lint, also build the json file. A profile with only a json file has no benchmark text, so the closest benchmark text takes its place (fa (in Whalory Pro), en (in Whalory Pro)).

## Profile sections

| Section | Question | Required |
|---|---|---|
| Identity | Who is the brand, what does it do, how is its name spelled exactly? | Yes |
| Reader | Who usually reads, in what state, on what screen? | Yes |
| Benchmark text | One real text that has the right voice | Yes |
| Tone and address | Colloquial written style or plain written style; «تو» or «شما»; which one where | Yes, for Persian |
| Language and style | Output language and variant; for English, spelling, Oxford comma, contractions, house style, reading grade | Yes, for English or bilingual brands |
| Dials | Eleven integers | Yes |
| One voice, many tones | The most used formats, and where each departs from the global tone | Yes, for a brand that writes both captions and error messages |
| Words | Say, avoid, consistent spelling | No |
| Claim boundary | What do we never claim without evidence? | Yes, in a sensitive industry |
| Fixed facts | Spelling of names, product terms, states that must not change | No |
| Reference writers | Which technique do we borrow from whom? | No |
| Examples | Two or three good texts and one bad one, with reasons | No |
| History | Every change, with a date and reason | Yes |

## Tone dials

Eleven dials. Ten take an integer from 1 to 5, and "loud marks" takes an integer from 0 to 3. Jargon and rhetoric arrived in schema 2; energy, directness, and slang arrived in schema 3. A number turns a vague decision into a clear rule.

| Dial | Key | Range | Default |
|---|---|---|---|
| Warmth | `warmth` | 1 to 5 | 3 |
| Formality | `formality` | 1 to 5 | 3 |
| Humor | `humor` | 1 to 5 | 1 |
| Narrative density | `narrative` | 1 to 5 | 3 |
| Sentence length | `sentence_length` | 1 to 5 | 3: a cap of 24 words in Persian, 25 in English |
| Loud marks | `loud_marks` | 0 to 3 | 0 |
| Jargon | `jargon` | 1 to 5 | 2 |
| Rhetoric dose | `rhetoric` | 1 to 5 | 3 |
| Energy | `energy` | 1 to 5 | 3 |
| Directness | `directness` | 1 to 5 | 3 |
| Slang | `slang` | 1 to 5 | 1 |

When no profile exists, this column applies: warmth 3, formality 3, humor 1, narrative 3, and sentence length 3. Loud marks are 0, jargon is 2, rhetoric is 3, energy is 3, directness is 3, and slang is 1. Persian copy uses «شما» and a 24-word cap; English copy uses `en-US` and a 25-word cap. This table is the source for these numbers; [SKILL.md](../SKILL.md) and [intake.md](intake.md) repeat them in short.

### Warmth

| Value | In the text |
|---|---|
| 1 | Information only; no direct address, no advice |
| 2 | Polite and short; no emotional sentence |
| 3 | One human sentence per text; friendly advice at the end |
| 4 | Familiar address; one homely or personal detail about the subject |
| 5 | Like a friend you know; a small smile allowed; only in short, low-risk formats |

### Formality

| Value | In the text |
|---|---|
| 1 | Fully colloquial written style |
| 2 | Colloquial verbs, written vocabulary |
| 3 | Plain written style |
| 4 | Precise written style; no abbreviations, no jokes |
| 5 | Clear formal style, for contracts, notices, and legal documents; still no bureaucratic words |

In English, formality shows through contractions, vocabulary, and sentence length, since English has no «تو» and «شما» split. The `contractions` key sets the rule; see [Oxford comma and contractions](#oxford-comma-and-contractions).

### Humor

| Value | In the text |
|---|---|
| 1 | None |
| 2 | One quiet observation in the whole text, at the end |
| 3 | One smile in each low-risk text |
| 4 | Running wit in captions and stories; never in errors, money, or complaints |
| 5 | Humor is part of the identity; still never at the reader's expense |

### Narrative density

| Value | In the text |
|---|---|
| 1 | Information only; interface formats |
| 2 | One concrete detail, no scene |
| 3 | A compact four-move arc |
| 4 | A scene and a person in every non-interface text |
| 5 | The story is the center; information sits inside the story |

### Sentence length

| Value | Mean words (Persian) | Cap (Persian) | Cap (English) |
|---|---|---|---|
| 1 | 6 to 9 | 14 | 15 |
| 2 | 8 to 12 | 18 | 20 |
| 3 | 10 to 16 | 24 | 25 |
| 4 | 12 to 20 | 28 | 30 |
| 5 | 15 to 24 | 34 | 35 |

The default cap is value 3: 24 words in Persian and 25 in English. The `max_words` key states the cap explicitly; if it is missing, the cap comes from this table. If both are present, `max_words` wins, and the two should agree. A bilingual brand sets a separate cap per language in `by_lang`.

### Loud marks

This dial starts at 0; 1 is not its floor.

| Value | Emoji | Exclamation marks |
|---|---|---|
| 0 | None | None |
| 1 | One in a caption or closing advice | None |
| 2 | One in each short text | One in the whole text |
| 3 | Two in a caption | One in the whole text |

`emoji_max` and `exclaim_max` come from this table when they are missing. When present, they win.

### Jargon

How much of the brand's trade language the reader knows.

| Value | In the text |
|---|---|
| 1 | No terms; every technical idea in the reader's everyday words |
| 2 | Unavoidable terms, with a short explanation at first use |
| 3 | Terms that readers in this trade use themselves, without explanation |
| 4 | Professional readers; the field's terms and abbreviations, each abbreviation spelled out at first use |
| 5 | Expert to expert; standards, numbers, and codes, without explanation |

Corporate language from the AI tells lists ([fa](fa/ai-tells.md), [en](en/ai-tells.md)) never counts as jargon, at any value. In Persian text, a Latin word appears only when no established Persian word exists; the profile's glossary says which. For English, this dial also sets the default reading grade; see [house style and reading grade](#house-style-and-reading-grade).

### Rhetoric dose

The cap for each format is in the table dose, format by format (in Whalory Pro). English copy uses the same caps. This dial says how much of that cap the brand uses.

| Value | In the text |
|---|---|
| 1 | Zero; only the brand's fixed slogan, if it has one |
| 2 | Only in slogans, headlines, and captions; one in the whole text |
| 3 | The table's dose, format by format |
| 4 | The table's dose in every format that allows rhetoric; one central metaphor in long texts |
| 5 | Rhetoric is part of the identity; slogans and headlines use it, still within the table's cap |

Some formats have a dose of zero in that table: a button, an error message, a hard message, a formal document. They get no rhetoric at any value.

### Energy, directness, and slang

| Dial | 1 | 3 | 5 |
|---|---|---|---|
| Energy | Still, measured pace | Steady everyday pace | Lively pace without invented urgency |
| Directness | Brief context before the point | Balanced context and next step | Answer and necessary action immediately, respectfully |
| Slang | Familiar words without slang | Occasional audience-familiar idioms | Community idioms only with explicit audience fit |

Energy changes pace, not emoji or exclamation limits. Directness changes ordering, not certainty or permission to omit qualifications. Slang changes idiom density, not Persian register or address. A colloquial Persian sentence addressed to «شما» can have slang 1. The resolver provides separate Persian and English instructions for every value; it does not translate Persian address rules into English.

## Register and address

Two separate Persian decisions: how verbs are conjugated (`register`) and how the reader is addressed (`address`). Any combination of the two is possible:

| | Address «تو» (`to`) | Address «شما» (`shoma`) |
|---|---|---|
| Plain written style (`formal`) | این نسخه روی گوشیِ تو هم کار می‌کند. | این نسخه روی گوشیِ شما هم کار می‌کند. |
| Colloquial written style (`colloquial`) | این نسخه رو گوشیِ تو هم کار می‌کنه. | این نسخه رو گوشیِ شما هم کار می‌کنه. |

Both settings are Persian only. An English profile leaves them at `"any"`. For how «تو» and «شما» carry into English, see transcreation (in Whalory Pro).

### Register

| Value | Meaning |
|---|---|
| `formal` | Plain written style: «است، می‌شود، کنید، خانه» |
| `colloquial` | Colloquial written style: «ـه، می‌شه، کنین، خونه» |
| `any` | Both; the boundary is set in the md file and in `formats` |

Old values are still read: `written` means `formal`, and `colloquial-written` means `colloquial`. In a new file, write only the three values above. Formality 1 and 2 go with `colloquial`, and formality 3 to 5 go with `formal`. The boundary between the steps is in the [tone ladder](fa/persian-prose.md#نردبانِ-لحن).

### Address

| Value | Meaning |
|---|---|
| `to` | «تو» in every format, unless `formats` says otherwise |
| `shoma` | «شما» in every format, unless `formats` says otherwise |
| `any` | Each format sets its address in `formats`; a format that doesn't say gets «شما» |

Decision order for address:

1. An address the user explicitly asked for in this task.
2. `formats.<id>.address` in the profile.
3. The profile's global `address`.
4. «شما».

Lint's built-in format defaults never set the address. `any` means no decision yet, and until one is made, the address is «شما». The address doesn't change within a text. A plural or ceremonial address is not an address; the text speaks to one person ([AI tells](fa/ai-tells.md)). The written account of this rule, with examples, is in [«تو» or «شما»](fa/craft.md#تو-یا-شما).

## Language and style

The language keys below were introduced in schema 2 and remain supported in schema 3. A Persian profile needs only `"language": "fa"` and `"variant": "fa-IR"`. Both linters validate the profile contract; English style rules are applied by `lint_en.py`. The full table is in [language and style keys](#language-and-style-keys).

### Language and variant

- `language` is the brand's primary output language: `"fa"`, `"en"`, or `"bilingual"`. A file without it reads as `"fa"`, so version 2 files keep working.
- `variant` is a language tag (BCP 47) such as `fa-IR`, `en-US`, or `en-GB`. It defaults to `fa-IR` for Persian and `en-US` for English, and holds the primary variant for a bilingual brand. `fa-AF` and `tg` still route to other languages (in Whalory Pro) and [writing conventions](fa/conventions.md).

The profile decides the language and variant only when nothing stronger does. An explicit instruction, the target channel or market, the materials, and the request language come first ([output language, variant, and market](router.md#output-language-variant-and-market)). A task for "our UK site" is `en-GB` even when the profile says `en-US`.

### Spelling

`spelling` is `"us"`, `"uk"`, `"uk-ize"`, or `null`. With `null`, the spelling comes from the variant:

| Variant | Spelling |
|---|---|
| en-US | `us` |
| en-GB, en-AU, en-NZ, en-IE, en-IN, en-ZA | `uk` |
| en-CA | `uk-ize` |
| none | inferred from the document's majority; only `en-spelling-mix` applies |

`uk-ize` is UK spelling with -ize endings. `lint_en.py` reports an error (`en-spelling-mix`) when a text mixes US and UK forms of one word family. It gives a warning (`en-spelling-variant`) when a word is off the profile's spelling. Ambiguous words such as `program` and `programme`, `check` and `cheque`, and `license` are left out of that check. Style details: [US and UK spelling](en/style-guide.md#us-and-uk-spelling).

### Oxford comma and contractions

- `oxford_comma`: with `true`, lint flags a missing serial comma, and with `false`, a present one. A `null` value flags only mixed use within one document.
- `contractions`: with `"use"`, lint flags full forms such as "do not" in `caption`, `post`, `email`, `ui`, `bot`, and `reply`. Under `"avoid"`, any contraction is flagged. `"positive-only"` keeps "you'll" and flags negative contractions such as "can't". A `null` value sets no rule.

Whalory's own English voice uses `"oxford_comma": true` and `"contractions": "use"`. Background: [Oxford comma](en/style-guide.md#oxford-comma) and [contractions](en/prose.md#contractions).

### House style and reading grade

`house_style` is `"chicago"`, `"ap"`, `"microsoft"`, `"google"`, `"govuk"`, `"mailchimp"`, or `null`. Leave it `null` unless the brand follows one of these guides. Setting it turns on that guide's rules. For example, `ap` and `microsoft` spell out one to nine, `chicago` and `ap` allow title-case headings, and `govuk` flags "e.g." and negative contractions. What each preset changes: [house-style presets](en/style-guide.md#house-style-presets).

`reading_grade_max` is the Flesch-Kincaid grade level (FKGL) that long English formats should stay under: a number from 4 to 16, or `null`. With `null`, the jargon dial sets the target. Dial 1 gives grade 6, 2 gives 8, 3 gives 10, 4 gives 12, and 5 gives 14. The check runs on texts of 100 words or more in these formats: `landing`, `about`, `blog`, `email`, `product`, `press`, `deck`, `script`, `hard`, and `reply`. For health copy, consider 8 or lower. An Institute of Medicine workshop recommended 8th grade or lower for consent documents, as the National Cancer Institute reports ([reading level tools](https://dctd.cancer.gov/research/ctep-trials/trial-development/reading-level-tools.pdf), checked 2026-09-27). Scores guide the edit; never game them. See [readability scores](en/prose.md#readability-scores).

### Bilingual brands

- Set `"language": "bilingual"`. `variant` holds the primary variant, and `variants` lists every variant the brand publishes in, primary first.
- `by_lang` holds per-language overrides of `max_words`, `emoji_max`, `exclaim_max`, `dials`, `register`, `address`, `banned`, `avoid`, `prefer`, `allow`, and `formats`. For English copy, `by_lang.en` replaces the matching top-level keys; `lint_fa.py` merges `by_lang.fa` the same way.
- Keep `brand.latin`, `romanization`, and a two-column glossary in the md file. The md file also names the base language, the one the facts come from (fact lock (in Whalory Pro)).
- Example for a bilingual café with Persian as the base language: `"language": "bilingual"`, `"variant": "fa-IR"`, `"variants": ["fa-IR", "en-US"]`, `"max_words": 24`, and `"by_lang": {"en": {"max_words": 25}}`.

## One voice, many tones

The voice stays fixed, and the tone changes with the situation. A person has one voice at a party and in a hospital, but two tones. In version 1, the profile had only a global tone, and only the md file could say «کپشنِ گرم، پیامِ خطای خشک» ("warm caption, dry error message"). In version 2, the `formats` key makes the same table enforceable by lint. How to find this table for a brand is in verbal identity (in Whalory Pro) (en (in Whalory Pro)).

### Fixed and variable

| Fixed across all formats | Can change per format |
|---|---|
| The brand name and its spelling | Register (`register`) |
| The glossary: `avoid`, `prefer`, `allow` | Address (`address`) |
| The claim boundary and the global `banned` list | Caps: `max_words`, `emoji_max`, `exclaim_max` |
| The [three rules that never change](../SKILL.md#three-rules-that-never-change) | Dials (`dials`), only the ones that change |
| | Extra banned words for that format (`banned`) |
| | One sentence for the writer (`note`) |

A format's `banned` list adds to the global list and removes nothing from it. Anything a format doesn't set comes from the global tone, so write only the differences.

### Format ids

The ids are fixed, and lint reads that section of the profile with `--format <id>`. Use only these ids in `formats`.

| Id | Format | Persian pack | English pack |
|---|---|---|---|
| `caption` | Caption | [forms](fa/forms.md#کپشن), [channels](fa/channels.md) | [forms](en/forms.md#caption), [channels](en/channels.md) |
| `story` | Story | social scripts (in Whalory Pro) | [Instagram](en/channels.md#instagram) |
| `carousel` | Carousel | social scripts (in Whalory Pro) | [Instagram](en/channels.md#instagram) |
| `post` | Post in a channel, a messaging app, or LinkedIn | Iranian channels (in Whalory Pro), [channels](fa/channels.md) | [LinkedIn](en/channels.md#linkedin), [channels](en/channels.md) |
| `push` | App push notification | [app notifications](fa/channels.md#اعلانِ-اپ) | push notifications (in Whalory Pro) |
| `ui` | Interface microcopy | [forms](fa/forms.md#ریزمتنِ-رابط), interface strings (in Whalory Pro) | [forms](en/forms.md#ui-microcopy), interface strings (in Whalory Pro) |
| `error` | Error, empty, and wait states | [forms](fa/forms.md#خطا-خالی-و-انتظار) | [forms](en/forms.md#error-empty-and-wait-states) |
| `product` | Product introduction and specifications | product copy (in Whalory Pro) | [product blurb](en/forms.md#product-blurb), product pages (in Whalory Pro) |
| `about` | About page | web pages (in Whalory Pro), [forms](fa/forms.md#درباره‌ی-ما) | [forms](en/forms.md#about-page), about pages (in Whalory Pro) |
| `reply` | Replies to customers and reviews | [forms](fa/forms.md#پاسخ-به-مشتری), local reviews (in Whalory Pro) | [customer reply](en/forms.md#customer-reply) |
| `script` | Audio and video script | video and audio (in Whalory Pro), [forms](fa/forms.md#متنِ-صوتی-و-ویدیو) | video and audio copy (in Whalory Pro) |

Where the English column says "none yet", use the Persian method without its examples.

All 26 ids, in this order. `lint.py --rules` shows the same list:

```
caption story reels carousel post sms otp email subject push ui error product
listing landing about blog ad press bot reply hard deck script name headline
```

### Tasks without a format id

Some tasks have no id of their own. For `formats` and for `--format`, take the closest id:

| Task | Id | Why |
|---|---|---|
| Phone menu (interactive voice response) | `script` | Written for the ear |
| Restaurant and café menu line | `product` | Each line introduces one dish |
| Checkout page and the step to the payment gateway | `ui` | It is interface microcopy |
| Payment result | `ui` for «انجام شد» ("done"); `error` for «انجام نشد» and «در حالِ بررسی» ("failed", "pending") | The reader is worried about their money |
| Job ad | `post` | A mid-length text for a channel or a job site |
| Proposal and tender response | `post` | A mid-length written text with a known reader |
| Event and webinar invitation | `post` | A mid-length text with a time, a place, and one action |

Playbooks for phone menus, menus, job ads, proposals, and invitations are in business documents (in Whalory Pro). Payment and its result are in web pages (fa (in Whalory Pro), en (in Whalory Pro)).

A task that isn't in this table either is linted without `--format`, which means with the profile's global tone. A new id is added only in the next schema version.

### Example

For a [dental clinic] with a global tone of warmth 3 and formality 4:

| Format | Warmth | Formality | Narrative | Address | What stays fixed |
|---|---|---|---|---|---|
| Global | 3 | 4 | 2 | «شما» | «نوبت» and «مراجعه‌کننده»; no treatment claims |
| `caption` | 3 | 3 | 3 | «شما» | General education, approved by the doctor in charge |
| `sms` | 2 | 4 | 1 | «شما» | Day, time, place, how to cancel |
| `error` | 2 | 4 | 1 | «شما» | What happened first, then what to do |

The same table in json:

```json
{
  "schema_version": 3,
  "register": "formal",
  "address": "shoma",
  "dials": {"warmth": 3, "formality": 4, "humor": 1, "narrative": 2,
            "sentence_length": 3, "loud_marks": 0, "jargon": 2, "rhetoric": 1},
  "formats": {
    "caption": {"dials": {"formality": 3, "narrative": 3}},
    "sms":     {"max_words": 18, "dials": {"warmth": 2, "narrative": 1},
                "note": "روز، ساعت، مکان، راهِ لغو"},
    "error":   {"max_words": 14, "dials": {"warmth": 2, "narrative": 1},
                "note": "اول چه شد، بعد چه کنید"}
  }
}
```

## Precedence

Facts, claim restrictions, consent, and source requirements remain invariant. A stylistic request cannot authorize new facts, stronger certainty, or less protection. Situations such as grief, payment errors, health, or complaints still require an editorial review; the resolver is not a semantic safety judge.

The portable resolver applies these layers from lowest to highest:

| Layer | Merge policy |
|---|---|
| Defaults | Eleven dials; Persian address `shoma`, English address `any`; language-specific word caps |
| Brand, then its `by_lang.<lang>` | The selected language overrides its parent field by field |
| Industry, then its language layer | Used only without a brand, or when the caller explicitly sets `industry_selected=true`; an automatic guess never replaces the brand |
| Selected preset, then its language layer | Style fields override the lower layers |
| Format defaults | Only tighten `max_words`, `emoji_max`, and `exclaim_max` |
| Explicit format settings | Brand, selected industry, then preset format settings; each language-specific format follows its parent; can tighten or relax the format defaults |
| Request, then its language layer | Explicit settings for this task |
| Host limits | Final hard ceilings for the three numeric caps; may only tighten |

Nested dials and spelling maps merge field by field. In schema 3, `banned` and `claim_boundaries` use an ordered union across all contributing layers. An empty list cannot remove a restriction, and an `allow` entry cannot excuse a banned word. `fixed_facts` are immutable by key: a conflicting higher-layer value is rejected and the conflict is returned. Keep names, quantities, prices, dates, currency, conditions, and required qualifications in these facts and in the writing brief.

The result contains `profile`, `sources`, `trace`, `conflicts`, and three language-specific `instructions`. `sources["dials.energy"]` identifies the winning layer; `trace` retains the previous and new values and the merge policy. `conflicts` explains a retained fact, a skipped automatic industry, or a host ceiling. A caller should show material conflicts before generation. The returned profile has no unresolved `formats` or `by_lang`.

Legacy lint keeps its published call signatures and v1/v2 format-cap behavior. Loaders accept schema 3; malformed schema 3 and future schemas are input errors. Legacy malformed values produce visible profile warnings instead of silently disappearing. To lint a layered request, first call `lint.resolve_profile(...)` or `voice_profile.resolve_profile(...)`, then pass `result["profile"]` to `lint.lint_text`. Claim truth and the quality of the three new dials require editorial review; lint does not pretend to measure them.

## The JSON file, key by key

| Key | Type | Meaning | Since version |
|---|---|---|---|
| `schema_version` | integer | `3`; the reader also accepts 1, 2, and an omitted v1 version | 2 |
| `name` | text | Latin slug, same as the file name | 1 |
| `brand.fa`, `brand.latin` | text | Exact spelling of the name | 1 |
| `brand.misspellings` | map | Wrong spelling to right spelling; lint reports an error | 1 |
| `romanization` | map | Optional; fixed Latin spellings of other names, from Persian to Latin; [spelling map](fa/persian-prose.md#نامِ-برند-محصول-و-آدم) | 2 |
| `register` | `any`, `formal`, `colloquial` | Persian register | 1 |
| `address` | `any`, `shoma`, `to` | Persian address | 2 |
| `dials` | map | The eleven dials | 1; jargon/rhetoric since 2; energy/directness/slang since 3 |
| `max_words` | number | Word cap per sentence; defaults to 24 in Persian and 25 in English | 1 |
| `emoji_max` | number | Emoji cap per text | 1 |
| `exclaim_max` | number | Exclamation mark cap per text | 1 |
| `banned` | list | Banned words; lint reports an error | 1 |
| `avoid` | list | "Avoid" words; lint gives a warning | 1 |
| `prefer` | map | The replacement for each "avoid" word | 1 |
| `allow` | list | Words lint usually warns about but this brand uses with good reason, such as a word in the brand name | 1 |
| `formats` | map | The tone of each format; see [one voice, many tones](#one-voice-many-tones) | 2 |
| `claim_boundaries` | list of strings | Restrictions that tone selection cannot remove | 3 |
| `fixed_facts` | object | Immutable facts keyed by a stable identifier | 3 |
| `extensions` | object | Custom metadata preserved without interpreting it as style | 3 |

`romanization` covers names the brand writes in Latin script again and again. The brand name itself stays in `brand.latin`. Each key is a Persian name and each value its fixed Latin spelling, such as `{"[نامِ محصول]": "[Product Name]", "[شهر]": "[City]"}`. The writer reads this map before any bilingual text, and spellings are never made up anew.

Schema 3 skeleton, compatible with the older English template [_template.en.json](../profiles/_template.en.json). A Persian profile sets `"language": "fa"`, `"variant": "fa-IR"`, and `"max_words": 24`. It can leave out the English-only keys, as [_template.json](../profiles/_template.json) does:

```json
{
  "schema_version": 3,
  "name": "brand-name",
  "language": "en",
  "variant": "en-US",
  "variants": [],
  "spelling": null,
  "oxford_comma": null,
  "contractions": "use",
  "house_style": null,
  "reading_grade_max": null,
  "brand": {"fa": "", "latin": "", "misspellings": {}},
  "romanization": {},
  "register": "any",
  "address": "any",
  "dials": {"warmth": 3, "formality": 3, "humor": 1, "narrative": 3, "sentence_length": 3,
            "loud_marks": 0, "jargon": 2, "rhetoric": 3, "energy": 3, "directness": 3, "slang": 1},
  "max_words": 25,
  "emoji_max": 0,
  "exclaim_max": 0,
  "banned": [], "avoid": [], "prefer": {}, "allow": [],
  "industry": "",
  "formats": {
    "ui": {"max_words": 12, "emoji_max": 0, "exclaim_max": 0, "note": "Verb + object; name each feature as it appears in the product."},
    "email": {"note": "One call to action; subject line checked separately with format id 'subject'."}
  },
  "by_lang": {}
}
```

Save the file as `UTF-8`. Check its structure like this:

```bash
python scripts/voice_profile.py validate voice.json
```

### Language and style keys

These keys were introduced in schema 2 and retain their meanings in schema 3. The full skeleton above shows them in place.

| Key | Type / values | Default when missing | Meaning |
|---|---|---|---|
| `language` | `"fa"` \| `"en"` \| `"bilingual"` | `"fa"` (v2 back-compat) | Primary output language of the brand |
| `variant` | BCP 47: `fa-IR`, `fa-AF`, `tg`, `en-US`, `en-GB`, `en-AU`, `en-CA`, `en-NZ`, `en-IE`, `en-IN` | fa→`fa-IR`, en→`en-US` | Default variant (primary one when bilingual) |
| `variants` | array of BCP 47, primary first | `[]` | Bilingual brands: every variant they publish in |
| `spelling` | `"us"` \| `"uk"` \| `"uk-ize"` \| `null` | `null` = derived from the variant ([spelling](#spelling)) | English spelling |
| `oxford_comma` | `true` \| `false` \| `null` | `null` = consistency only | Serial comma |
| `contractions` | `"use"` \| `"avoid"` \| `"positive-only"` \| `null` | `null` = no rule | English contractions |
| `house_style` | `"chicago"` \| `"ap"` \| `"microsoft"` \| `"google"` \| `"govuk"` \| `"mailchimp"` \| `null` | `null` | Enables house-style rules ([house style](#house-style-and-reading-grade)). Optional |
| `reading_grade_max` | number 4–16 \| `null` | `null` = from the jargon dial | English FKGL target. Optional |
| `by_lang` | `{"fa": {…}, "en": {…}}` | `{}` | Per-language overrides of `max_words`, `emoji_max`, `exclaim_max`, `dials`, `register`, `address`, `banned`, `avoid`, `prefer`, `allow`, `formats`. Needed for bilingual brands |

### Validation rules

The portable [JSON schema](../data/voice-profile.schema.json) and `voice_profile.validate_profile` define structural validation. Both linters accept this contract. Existing nullable English fields retain their meaning; null dials, null containers, booleans used as integers, unknown fields, and future versions are invalid. Put custom metadata in `extensions`. No numeric rounding or clamping occurs in strict validation.

- enums as listed;
- `variant` must match `^(fa-(IR|AF)|tg|en-(US|GB|AU|CA|NZ|IE|IN|ZA))$`;
- `variants` must contain `variant` when it is non-empty;
- `by_lang` keys ⊆ {fa, en}.

## Reading and migrating old profiles

Schema version and product version are independent. The product release candidate uses profile schema 3. A missing `schema_version` means v1; v1 and v2 files remain readable without rewriting them. Documented aliases (`written`, `colloquial-written`, Persian address labels, and `rhetoric_dose`) are converted by the legacy normalizer. Schema 3 uses canonical names.

`normalize_profile` returns a fresh object. It adds only `energy=3`, `directness=3`, and `slang=1`, preserving all old dial values and absent old fields. This avoids accidentally enabling a legacy lint rule such as jargon. Energy 3 and directness 3 supply neutral writer guidance; slang 1 adds no idioms. These are compatibility defaults, not measured model-quality claims. The regression suite compares existing profile caps and lint findings before and after normalization. `resolve_profile` supplies the complete eleven-dial settings for the writing task.

Migration is explicit and dry-run by default:

```bash
python scripts/voice_profile.py migrate /path/to/voice.json --dry-run
python scripts/voice_profile.py migrate /path/to/voice.json --write
python scripts/voice_profile.py rollback /path/to/voice.json --dry-run
python scripts/voice_profile.py rollback /path/to/voice.json --write
```

The write operation creates an adjacent exact-byte `.vN.<checksum-prefix>.bak` and `.migration.json` receipt with both SHA-256 checksums. It preserves a UTF-8 BOM, CRLF or LF endings, final-newline presence, and the original permission mode. A second migration produces no diff. Rollback verifies the backup and current checksums before restoring exact original bytes; it refuses to overwrite a later user edit. Backups and receipts remain for audit. To start a new migration after a rollback, first archive the previous receipt yourself.

Legacy custom fields move visibly into the nearest `extensions.legacy_fields`, custom dials into `legacy_dials`, and unsupported format/language/brand metadata into the corresponding `legacy_formats`, `legacy_by_lang`, or `legacy_brand_fields`. They are preserved data and do not become executable
tone controls. The dry-run output shows the entire candidate. Corrupt JSON, duplicate keys, invalid known fields, future versions, and conflicting extension metadata fail before a profile write.

The migration command only handles the explicit path. It never scans the home folder or writes into an installed skill automatically. Profile lookup remains the established order: current `~/.whalory/profiles`, then read-only legacy `~/.whalya/profiles`, then bundled profiles; the historical `whalya` identifier resolves to `whalory`.

Public Python API (standard library, Python 3.8+):

```python
import voice_profile
errors = voice_profile.validate_profile(document)
normalized = voice_profile.normalize_profile(document)
result = voice_profile.resolve_profile(
    document, lang="fa", fmt="caption", preset=None, industry=None,
    request=None, host_limits=None, industry_selected=False)
```

The CLI `validate`, `normalize`, `resolve`, `schema`, `migrate`, and `rollback` commands emit JSON. Success returns 0; invalid input returns 2. `--help` documents each command. The caller owns profile scope and resolves any protected-fact conflicts before writing.

## Incomplete profile

Missing sections take the defaults. Dials come from the default column, the address is «شما», and the sentence cap is 24 words in Persian or 25 in English. Without a benchmark text, pick the closest one by the formality and warmth dials. Take it from the tone map (fa (in Whalory Pro), en (in Whalory Pro)) or from the starter profile for the same industry. Say which one in the internal note.

A brand with no profile and a brand-building task gets a working profile from three questions. Use the [quick route](profile-builder.md#quick-route-three-questions), or the [English route](profile-builder.md#english-route) for English copy.
