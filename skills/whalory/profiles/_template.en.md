# Voice profile: [the brand's name]

> Copy this file and fill in every bracket. Sections marked "required" must be filled in. Guide: [profile builder](../references/profile-builder.md#english-route); what each section and dial means: [voice profile](../references/voice-profile.md). Save the copy as `VOICE.md` in the project root, or in `~/.whalory/profiles/`; the skill folder is not the place for it. Its JSON twin starts from [_template.en.json](_template.en.json). The Persian template is [_template.md](_template.md).

## Identity (required)

| Field | Value |
|---|---|
| Name | [exact spelling and capitalization] |
| Persian name, if the brand has one | [exact spelling, with the zero-width non-joiner] |
| Slug | [lowercase Latin letters; the `name` key in the JSON] |
| What it does, in one sentence | [with a verb; no generic corporate words] |
| Tagline, if any | [text] |

## Reader (required)

| Field | Value |
|---|---|
| Who it usually is | [a person, not a demographic] |
| What state they read in | [place, device, time, worry] |
| What they do after reading | [an action] |
| How well they know the field's language | [sets the jargon dial] |

## Benchmark text (required)

> [a short real text that has the right voice]

Where it comes from: [the brand's own copy / a tone model from another brand / the teaching sample of a starter profile]

Why this text: [three or four reasons]

## Language and style (required)

| Setting | JSON key | Value | Options |
|---|---|---|---|
| Language | `language` | en | `fa`, `en`, `bilingual` |
| Variant | `variant` | [en-US] | `en-US`, `en-GB`, `en-AU`, `en-CA`, `en-NZ`, `en-IE`, `en-IN`, `en-ZA` |
| Other variants | `variants` | [none] | For a brand that publishes in several variants: all of them, the primary one first |
| Spelling | `spelling` | [derived from the variant] | `us`, `uk`, `uk-ize`, or `null` to derive it from the variant |
| Oxford comma | `oxford_comma` | [yes, no, or no rule] | `true`, `false`, or `null` to check only that the document is consistent |
| Contractions | `contractions` | [use] | `use`, `avoid`, `positive-only`, or `null` for no rule |
| House style | `house_style` | [none] | `chicago`, `ap`, `microsoft`, `google`, `govuk`, `mailchimp`, or `null` |
| Reading grade | `reading_grade_max` | [from the jargon dial] | A grade from 4 to 16, or `null` to take it from the jargon dial |

What each setting does: [language and style](../references/voice-profile.md#language-and-style). A bilingual brand keeps one profile and puts the settings that differ by language under `by_lang` in the JSON: see [bilingual brands](../references/voice-profile.md#bilingual-brands).

## Tone by context (required)

| Where | Tone |
|---|---|
| [formats] | [for example: plain and warm; contractions] |
| [formats] | [for example: precise and formal; no contractions] |

## Dials (required)

| Dial | JSON key | Value | Short note |
|---|---|---|---|
| Warmth | `warmth` | [1 to 5] | |
| Formality | `formality` | [1 to 5] | |
| Humor | `humor` | [1 to 5] | |
| Narrative density | `narrative` | [1 to 5] | |
| Sentence length | `sentence_length` | [1 to 5] | |
| Loud marks | `loud_marks` | [0 to 3] | |
| Jargon | `jargon` | [1 to 5] | |
| Rhetoric dose | `rhetoric` | [1 to 5] | |

Sentence cap: [25 words, unless you have a reason]. In English, sentence length 1 to 5 means a cap of 15, 20, 25, 30, or 35 words. The jargon dial also sets the reading grade when `reading_grade_max` is empty: 1 to 5 means grade 6, 8, 10, 12, or 14.

## One voice, many tones

List only the formats whose tone differs from the global tone, and for each one only the difference. The ids are in [format ids](../references/voice-profile.md#format-ids). The two rows below are starting suggestions that match `formats` in [_template.en.json](_template.en.json); delete any row the brand does not need.

| Id | Format | Length | Tone | Dials and caps | Note |
|---|---|---|---|---|---|
| `ui` | UI microcopy | [one to five words] | Plain | Sentences up to 12 words; no emoji or exclamation marks | Verb and object; name each feature as it appears in the product |
| `email` | Email | [three to eight sentences] | [as the global tone] | [as the global tone] | One call to action; the subject line is checked separately with the format id `subject` |

## Words

<!-- lint-ignore -->

| Say | Don't say |
|---|---|
| [word] | [word] |

<!-- /lint-ignore -->

Consistent terms: [for example, "sign in" everywhere, never "log in"]

Every entry in the "Don't say" column also goes into the JSON `avoid` list, with its replacement in `prefer`.

## Claim boundary (required in sensitive industries)

- [a claim that never appears without evidence]
- [a state of the product that must not be shown as ready]
- [the industry's license or legal limit], from regulation.md (in Whalory Pro)
- General table: [claims.md](../references/en/claims.md)

## Fixed facts

- [a product term and its meaning]
- [a name whose spelling is sensitive]

Romanization map, for a brand that also writes in Persian: the fixed Latin spelling of Persian names it uses often, apart from the brand name. The same table is the `romanization` key in the JSON.

| Persian | Latin | Where |
|---|---|---|
| [the Persian name of a product] | [its Latin spelling] | [packaging, site, marketplace] |

## Reference writers

| Writer or brand | Technique we borrow |
|---|---|
| [a writer or a brand] | [a technique, not a sentence] |

## Examples

### Good

> [text]

Why: [reason]

### Bad

> [text]

Why not: [reason]

## History

| Date | Change | Reason |
|---|---|---|
| [2026-09-27] | Profile created | [which route: three questions, existing copy, or interview] |
