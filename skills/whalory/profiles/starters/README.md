# Starter profiles

Each file is a starting point for the voice of one industry, not the voice of any real brand. Copy one, then replace the identity and the benchmark text with the brand's own, and calibrate the dials with the [profile builder](../../references/profile-builder.md). Every starter uses profile schema version 2: eight dials, a global tone, and separate tones for two or three common formats in `formats`. The benchmark text in each file is a made-up teaching sample, and the brand's real copy always takes priority.

The Persian starters sit in this folder and the English starters in `en/`. Both sets share the slugs and the dials. Each English starter is written for English readers, with its own formats, words, and claim limits. It also sets the English keys: variant, spelling, Oxford comma, and contractions.

## Persian starters

Language `fa`, variant `fa-IR`. Address (`to` or `shoma`) is a Persian-only setting.

| File | Industry | Language | Variant | Address | Warmth | Formality | Humor | Narrative | Separate formats |
|---|---|---|---|---|---|---|---|---|---|
| [cafe](cafe.md) | Café and restaurant | fa | fa-IR | `to` | 4 | 2 | 3 | 3 | `caption`, `sms`, `product` |
| [saas](saas.md) | Software and tech startup | fa | fa-IR | `shoma` | 3 | 3 | 2 | 2 | `ui`, `error`, `landing` |

## English starters

Language `en`, variant `en-US`, spelling derived from the variant, and the Oxford comma on. Each file explains how to switch it to en-GB, en-AU, or en-CA.

| File | Industry | Language | Variant | Contractions | Warmth | Formality | Humor | Narrative | Separate formats |
|---|---|---|---|---|---|---|---|---|---|
| [cafe](en/cafe.md) | Café and restaurant | en | en-US | `use` | 4 | 2 | 3 | 3 | `caption`, `reply`, `product` |
| [saas](en/saas.md) | Software and tech startup | en | en-US | `use` | 3 | 3 | 2 | 2 | `ui`, `error`, `landing` |

## Related files

Where to keep a copy: [where to keep it](../../references/voice-profile.md#where-to-keep-it). Whalory's own voice, for when it speaks for itself: [whalory.md](../whalory.md) in Persian and [whalory.en.md](../whalory.en.md) in English. A learnings note for each brand: [LEARNINGS-template.md](../LEARNINGS-template.md) and [LEARNINGS-template.en.md](../LEARNINGS-template.en.md).

A brand whose industry is not here starts from [_template.md](../_template.md) or [_template.en.md](../_template.en.md). It then answers the six questions in the Persian industry file (in Whalory Pro), or checks the English industries not listed here (in Whalory Pro).
