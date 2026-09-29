# Starter profile: Software and tech startup

> A starting point for any brand in this industry, not the voice of a real brand. Copy it, then replace the identity and the benchmark text with the brand's own, and calibrate the dials with the [profile builder](../../../references/profile-builder.md#english-route). Save the copy as `VOICE.md` in the project root or in `~/.whalory/profiles/`. The machine-readable rules for this voice are in [saas.json](saas.json), and the Persian twin is [saas.md](../saas.md).

## Identity

| Field | Value |
|---|---|
| Name | [exact spelling and capitalization] |
| What it does, in one sentence | [with a verb] |
| Industry | Software and tech startup |
| Language | English (en-US) |

## Reader

| Field | Value |
|---|---|
| Who it usually is | A user who opens the tool for daily work, and the manager who decides whether to buy it. |
| What state they read in | At a desk, mid-task; short on patience if something is stuck. |
| What they do next | Turns the feature on, fixes the error, or talks to the team about buying. |

## Benchmark text

**A made-up teaching sample.** Measure the voice against it until the brand's real copy arrives; from then on, the real copy takes priority.

> Month-end reports now build in one place. [Feature name] reads the rows from [source] and lays out the table right there.
>
> Turn it on from [menu path]. The first run takes [measured time, if you have one].

Why this text: The user's job and the feature each get a verb, the path is exact, and a time appears only if measured.

## Language and style

| Setting | Value | JSON |
|---|---|---|
| Variant | US English | `"variant": "en-US"` |
| Spelling | Derived from the variant: US | `"spelling": null` |
| Oxford comma | Yes: "red, white, and blue" | `"oxford_comma": true` |
| Contractions | Use: write `you'll`, `we're`, and `don't`. | `"contractions": "use"` |
| House style | None | `"house_style": null` |
| Reading grade | Grade 10 or lower, from the jargon dial | `"reading_grade_max": null` |

What each setting does: [language and style](../../../references/voice-profile.md#language-and-style).

## Tone by context

| Where | Tone |
|---|---|
| Interface, help, release notes, landing page | Plain and direct; contractions |
| Team posts on social media | Plain, a little warmer |

## Dials

| Dial | Value |
|---|---|
| Warmth | 3 |
| Formality | 3 |
| Humor | 2 |
| Narrative density | 2 |
| Sentence length | 3, cap 25 words |
| Loud marks | 0 |
| Jargon | 3 |
| Rhetoric dose | 2 |

## One voice, many tones

Only the differences from the global tone are listed; everything else comes from above. Format ids: [format ids](../../../references/voice-profile.md#format-ids).

| Id | Format | Length | Difference from the global tone | Note |
|---|---|---|---|---|
| `ui` | UI microcopy | One to five words | warmth 2, humor 1, narrative density 1, rhetoric dose 1; sentences up to 12 words | Verb and object; name each feature as it appears in the menu. |
| `error` | Error message | One or two sentences | warmth 2, humor 1, narrative density 1, rhetoric dose 1; sentences up to 16 words | First what happened, then what to do. |
| `landing` | Landing page | See web-pages.md | narrative density 3, rhetoric dose 3 | What the product does, with a verb; an honest limit. |

## Words

<!-- lint-ignore -->

| Say | Don't say |
|---|---|
| [the specific job, with a verb] | solution, ecosystem, revolutionary |
| [the verb for the action, such as 'Saved'] | Operation completed successfully |
| [what the automation does, exactly] | AI-powered, smart |
| use | leverage, utilize |

<!-- /lint-ignore -->

## Claim boundary

- Time or cost savings only with a documented test.
- No 'fully secure' or 'error-free'; name the standard and the actual method.
- 'AI-powered' only with a plain account of what it automates.
- Customer names and logos only with permission.
- General table in [claims.md](../../../references/en/claims.md); the rules of each market in regulation.md (in Whalory Pro).

## Switching to en-GB, en-AU, or en-CA

1. Set `variant` to `en-GB`, `en-AU`, or `en-CA` and leave `spelling` as `null`. The linter then derives the spelling: UK forms for en-GB and en-AU, and UK forms with `-ize` endings for en-CA. See [spelling](../../../references/voice-profile.md#spelling).
2. Dates change order: `June 12, 2026` in US copy and `12 June 2026` in UK copy. For en-AU and en-CA, follow [dates and times](../../../references/en/style-guide.md#dates-and-times) or the brand.
3. Prices, currencies, and measurements come from the brand's facts for that market; never convert them yourself.
4. Words that change in UK copy: `optimize` becomes `optimise`, `license (noun)` becomes `licence`. For en-AU and en-CA, ask the brand which forms its customers use.
5. The variant sets spelling and style only. The market for claims and law is decided separately: which market applies (in Whalory Pro).
