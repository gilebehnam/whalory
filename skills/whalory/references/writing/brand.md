# Brand voice and verbal identity / صدای برند و هویت کلامی

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Make voice and messaging choices usable across real situations.

Tone: Distinct brand voice with practical examples and restrained rules. Avoid: Personality adjectives without examples and fictional brand history.

Evidence: Brand facts and permitted samples; sample claims are not new brand facts.

Destination budget: A usable guide with examples; keep profile data and prose consistent.

Shared craft: [existing family method](../playbooks-strategy.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Brand voice profile](#voice-profile)
- [Verbal identity guide](#verbal-identity)
- [Positioning statement](#positioning-statement)
- [Messaging architecture](#message-house)
- [Brand story](#brand-story)
- [Brand manifesto](#manifesto)
- [Naming concepts and rationale](#naming-rationale)
- [Brand terminology glossary](#terminology)
- [Situational tone matrix](#tone-matrix)
- [Brand voice audit](#brand-review)

## Voice Profile

**پروفایل صدای برند · `brand.voice_profile`**

Separate brand facts from preferred expression in samples. Decide Persian register/address or English variant; proposed voice stays proposed until accepted.

Required inputs: brand_facts, samples, reader, formats. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `VOICE_md` / راهنمای صدا | Provide VOICE.md with narrator, principles, situation matrix, claim boundaries and examples. |
| `voice_json` / پروفایل ساختاریافته | Provide matching structured profile using the current profile schema; retain supported dial ranges. |
| `examples` / مثال‌ها | Show good and unsuitable examples with identical facts; explain the difference. |

Review: Md json parity: review the actual Brand voice profile against supplied evidence. Sample claim separation: review the actual Brand voice profile against supplied evidence. Scope consistency: review the actual Brand voice profile against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Verbal Identity

**سند هویت کلامی · `brand.verbal_identity`**

Turn positioning and permitted samples into rules that a writer can apply.

Required inputs: position, audiences, voice_samples. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `principles` / اصول | State actionable principles with examples. |
| `tone_matrix` / ماتریس لحن | Adapt expression across real situations without changing identity. |
| `examples` / مثال‌ها | Show contrasting examples grounded in the same facts. |

Review: Brand fit: review the actual Verbal identity guide against supplied evidence. Channel variation: review the actual Verbal identity guide against supplied evidence. Claim boundary: review the actual Verbal identity guide against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Positioning Statement

**بیانیه‌ی جایگاه‌یابی · `brand.positioning_statement`**

Specify reader, problem and actual offer before asserting a difference.

Required inputs: segment, problem, offer, proof. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `statement` / بیانیه | Write a clear positioning statement with substantiated distinction. |
| `rationale` / دلیل | Explain the decision behind each component. |
| `evidence_gaps` / کمبود شواهد | Mark differentiation that still needs proof. |

Review: No fake differentiation: review the actual Positioning statement against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Reader clarity: review the actual Positioning statement against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Message House

**معماری پیام برند · `brand.message_house`**

Build supporting pillars only where evidence supports the central position.

Required inputs: position, proof, segments. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `core_message` / پیام محوری | State the consistent central message. |
| `pillars` / ستون‌ها | Connect each pillar to a reader concern. |
| `evidence_map` / نقشهٔ شواهد | Map each claim to proof or an explicit gap. |

Review: Message consistency: review the actual Messaging architecture against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Segment fit: review the actual Messaging architecture against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Brand Story

**داستان برند · `brand.brand_story`**

Use verified people, moments and decisions; do not add dialogue or sensory scenes as history.

Required inputs: verified_history, people, turning_points. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `story` / روایت | Tell the supported history in a coherent arc. |
| `short_version` / نسخهٔ کوتاه | Create a shorter version preserving factual meaning. |
| `source_notes` / یادداشت منابع | Record source and permission gaps separately. |

Review: No fake scene: review the actual Brand story against supplied evidence. No fake history: review the actual Brand story against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Manifesto

**مانیفست برند · `brand.manifesto`**

Express values through actual commitments rather than unlimited promises.

Required inputs: values, actual_commitments, reader. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `manifesto` / مانیفست | Write the values in a direct brand voice. |
| `commitment_map` / نقشهٔ تعهد | Map each promise to an existing action or clearly proposed commitment. |

Review: No empty promises: review the actual Brand manifesto against supplied evidence. Brand fit: review the actual Brand manifesto against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Naming Rationale

**نام‌گذاری و منطق نام · `brand.naming_rationale`**

Develop names from brief and language context, then distinguish creative screening from legal availability.

Required inputs: brief, constraints, language_context. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `name_options` / گزینه‌های نام | Offer genuinely distinct names. |
| `rationale` / دلیل | Explain meaning, pronunciation and fit. |
| `screening_plan` / برنامهٔ بررسی | List linguistic, cultural and legal checks still required. |

Review: No availability claim: review the actual Naming concepts and rationale against supplied evidence. Pronunciation review: review the actual Naming concepts and rationale against supplied evidence. Cultural fit: review the actual Naming concepts and rationale against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Terminology

**واژه‌نامه و اصطلاحات برند · `brand.terminology`**

Define product concepts before choosing preferred terms across languages.

Required inputs: terms, product_concepts, locales. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `glossary` / واژه‌نامه | List concept, preferred term, definition and locale. |
| `preferred_avoided_forms` / صورت‌های پیشنهادی و نامناسب | Explain avoided alternatives and the meaning difference. |

Review: Term consistency: review the actual Brand terminology glossary against supplied evidence. Meaning preservation: review the actual Brand terminology glossary against supplied evidence. Locale fit: review the actual Brand terminology glossary against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Tone Matrix

**ماتریس لحن موقعیت‌ها · `brand.tone_matrix`**

Keep the base voice stable while adjusting to reader state and risk.

Required inputs: base_voice, situations, channels. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `matrix` / ماتریس | Map situation, desired tone and concrete language choices. |
| `examples` / مثال‌ها | Demonstrate each situation with matched facts. |
| `guardrails` / حدود | State humor and claim boundaries for difficult messages. |

Review: Hard message fit: review the actual Situational tone matrix against supplied evidence. Claim boundary: review the actual Situational tone matrix against supplied evidence. Voice consistency: review the actual Situational tone matrix against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Brand Review

**ممیزی صدای محتوای برند · `brand.brand_review`**

Assess supplied samples against approved voice with quoted evidence, not a fictional overall score.

Required inputs: content_samples, approved_voice. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `findings` / یافته‌ها | Identify observable deviations and consequence. |
| `repairs` / اصلاح‌ها | Show specific repairs preserving the facts. |
| `priorities` / اولویت‌ها | Rank issues by reader impact and repeatability. |

Review: Sample scope: review the actual Brand voice audit against supplied evidence. Observable criteria: review the actual Brand voice audit against supplied evidence. No fake score: review the actual Brand voice audit against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
