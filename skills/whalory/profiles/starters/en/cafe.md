# Starter profile: Café and restaurant

> A starting point for any brand in this industry, not the voice of a real brand. Copy it, then replace the identity and the benchmark text with the brand's own, and calibrate the dials with the [profile builder](../../../references/profile-builder.md#english-route). Save the copy as `VOICE.md` in the project root or in `~/.whalory/profiles/`. The machine-readable rules for this voice are in [cafe.json](cafe.json), and the Persian twin is [cafe.md](../cafe.md).

## Identity

| Field | Value |
|---|---|
| Name | [exact spelling and capitalization] |
| What it does, in one sentence | [with a verb] |
| Industry | Café and restaurant |
| Language | English (en-US) |

## Reader

| Field | Value |
|---|---|
| Who it usually is | A neighbor who stops by on the way to work, or someone looking for a table for an evening meetup. |
| What state they read in | On a phone, on the move or hungry, with one question: is it open now, and what's on today? |
| What they do next | Comes in, books a table, or sends a message. |

## Benchmark text

**A made-up teaching sample.** Measure the voice against it until the brand's real copy arrives; from then on, the real copy takes priority.

> Our [bread name] comes out of the oven at [time]. It stays warm until [time], and you can smell it from the door.
>
> If you're in early, have it with a [drink]. By the afternoon it's gone; the next batch is tomorrow morning.

Why this text: An exact time instead of an adjective, the smell, a useful tip, and an honest limit: the bread sells out.

## Language and style

| Setting | Value | JSON |
|---|---|---|
| Variant | US English | `"variant": "en-US"` |
| Spelling | Derived from the variant: US | `"spelling": null` |
| Oxford comma | Yes: "red, white, and blue" | `"oxford_comma": true` |
| Contractions | Use: write `you'll`, `we're`, and `don't`. | `"contractions": "use"` |
| House style | None | `"house_style": null` |
| Reading grade | Grade 6 or lower, from the jargon dial | `"reading_grade_max": null` |

What each setting does: [language and style](../../../references/voice-profile.md#language-and-style).

## Tone by context

| Where | Tone |
|---|---|
| Menu, captions, booking messages | Conversational and warm; contractions |
| House rules, allergen questions | Plain and exact, still friendly |

## Dials

| Dial | Value |
|---|---|
| Warmth | 4 |
| Formality | 2 |
| Humor | 3 |
| Narrative density | 3 |
| Sentence length | 2, cap 20 words |
| Loud marks | 1 |
| Jargon | 1 |
| Rhetoric dose | 3 |

## One voice, many tones

Only the differences from the global tone are listed; everything else comes from above. Format ids: [format ids](../../../references/voice-profile.md#format-ids).

| Id | Format | Length | Difference from the global tone | Note |
|---|---|---|---|---|
| `caption` | Caption | One to three sentences | warmth 5 | One hour of the day, one smell. |
| `reply` | Reply to a review or message | Two or three sentences | humor 1, narrative density 1; no emoji | Name the problem, say what you did, and give a way to reach you. |
| `product` | Menu | Name and two or three ingredients | humor 1, narrative density 2, rhetoric dose 2; no emoji | One cooking verb, no adjectives. |

## Words

<!-- lint-ignore -->

| Say | Don't say |
|---|---|
| [exact dish and its main ingredient] | delicious, mouthwatering, to die for |
| out of the oven at [time] | freshly baked goodness |
| [what is different, as a fact] | best in town, world-famous |
| book a table | secure your spot |

<!-- /lint-ignore -->

## Claim boundary

- No ranking such as 'best in town' without a named, dated source.
- Allergens and ingredients exactly as the kitchen states them; 'gluten-free' only if a test or a controlled process backs it.
- Opening hours and prices kept current; if unknown, a bracket.
- Customer reviews only if they are real and used with permission.
- General table in [claims.md](../../../references/en/claims.md); the rules of each market in regulation.md (in Whalory Pro).

## Switching to en-GB, en-AU, or en-CA

1. Set `variant` to `en-GB`, `en-AU`, or `en-CA` and leave `spelling` as `null`. The linter then derives the spelling: UK forms for en-GB and en-AU, and UK forms with `-ize` endings for en-CA. See [spelling](../../../references/voice-profile.md#spelling).
2. Dates change order: `June 12, 2026` in US copy and `12 June 2026` in UK copy. For en-AU and en-CA, follow [dates and times](../../../references/en/style-guide.md#dates-and-times) or the brand.
3. Prices, currencies, and measurements come from the brand's facts for that market; never convert them yourself.
4. Words that change in UK copy: `check` becomes `bill`, `takeout` becomes `takeaway`. For en-AU and en-CA, ask the brand which forms its customers use.
5. The variant sets spelling and style only. The market for claims and law is decided separately: which market applies (in Whalory Pro).
