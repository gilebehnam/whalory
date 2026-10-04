# Copywriting and advertising / کپی‌رایتینگ و تبلیغات

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Help the reader understand the approved offer and choose one next step.

Tone: Concrete, economical persuasion, adjusted to placement. Avoid: Invented scarcity, unproven superiority and pressure.

Evidence: Approved offer, destination, eligibility and dated terms.

Destination budget: One placement-sized unit per distinct angle; no platform maximum is assumed.

Shared craft: [existing family method](../playbooks-social.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Ad copy and variants](#ad-variant)
- [Campaign concept](#campaign-concept)
- [Search ad](#search-ad)
- [Display ad](#display-ad)
- [Paid social ad](#paid-social-ad)
- [Retargeting copy](#retargeting-ad)
- [Headline bank](#headline-bank)
- [Tagline and slogan](#tagline-slogan)
- [Print and outdoor copy](#print-outdoor-ad)
- [Offer announcement](#offer-announcement)

## Ad Variant

**متن و واریانت تبلیغ · `copy_ads.ad_variant`**

Choose distinct message angles for the same approved offer. Keep price, eligibility, destination and deadline identical across variants.

Required inputs: offer, facts, reader, placement. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `headline` / تیتر | State one evidenced benefit without an unsupported superlative. |
| `body` / متن | Explain the offer and material conditions within the placement budget. |
| `cta` / اقدام بعدی | Name the actual next action at the verified destination. |
| `variants` / گزینه‌ها | Give each variant an angle label and explain the difference without changing the offer. |

Review: Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Verify the destination field and counting unit from dated source data; otherwise label its limit unverified. Match deadline, scarcity and capacity exactly to approved evidence; remove invented urgency. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Campaign Concept

**کانسپت و پیام کمپین · `copy_ads.campaign_concept`**

Connect the audience problem to one campaign idea, then show how each channel expresses that idea.

Required inputs: campaign_goal, offer, audience, channels. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `concept` / ایده | Name the central creative idea and its evidence boundary. |
| `key_message` / پیام اصلی | Write the single message every execution must preserve. |
| `channel_map` / نقشهٔ کانال‌ها | Map channels to role, asset need and next action. |

Review: One message: review the actual Campaign concept against supplied evidence. Compare names, numbers, units, conditions and claims across every output unit. Match deadline, scarcity and capacity exactly to approved evidence; remove invented urgency. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Search Ad

**متن تبلیغ جست‌وجو · `copy_ads.search_ad`**

Match the query's intent to the actual landing page before composing independently usable combinations.

Required inputs: query_intent, offer, destination. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `headlines` / تیترها | Provide self-contained headline alternatives that combine without contradicting the offer. |
| `descriptions` / توضیح‌ها | Write descriptions with material conditions and one action. |
| `destination_note` / یادداشت مقصد | Record destination match and unresolved placement limits. |

Review: Do not invent a maximum; distinguish characters, graphemes, bytes, units and SMS segments. Landing consistency: review the actual Search ad against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Display Ad

**تبلیغ بنری و نمایشی · `copy_ads.display_ad`**

Make the offer understandable at the supplied viewing distance and asset size.

Required inputs: offer, audience, placement. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `headline` / تیتر | Write a short headline understandable without the body. |
| `support_line` / توضیح کوتاه | Use the support line for the strongest evidenced detail or condition. |
| `cta` / اقدام بعدی | Use the destination's action label. |

Review: Visual fit: review the actual Display ad against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Verify the destination field and counting unit from dated source data; otherwise label its limit unverified. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Paid Social Ad

**تبلیغ شبکه‌ی اجتماعی · `copy_ads.paid_social_ad`**

Use the actual asset and audience context to select an angle; do not infer sensitive personal attributes.

Required inputs: offer, audience, platform, asset_context. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `primary_text` / متن اصلی | Write primary text whose claims agree with the asset. |
| `headline` / تیتر | Write a headline that stands beside the image without repeating it. |
| `cta` / اقدام بعدی | Name a supported action and destination. |

Review: Platform fit: review the actual Paid social ad against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Match deadline, scarcity and capacity exactly to approved evidence; remove invented urgency. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Retargeting Ad

**متن بازگشت مخاطب · `copy_ads.retargeting_ad`**

Acknowledge only the contact history the brand is allowed to use; make returning optional.

Required inputs: offer, stage, previous_contact. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `message` / پیام | Address the documented stage without saying the brand knows private behavior. |
| `cta` / اقدام بعدی | Offer one low-pressure next step. |
| `variants` / گزینه‌ها | Vary the reason to return, not the factual terms. |

Review: No sensitive inference: review the actual Retargeting copy against supplied evidence. Match deadline, scarcity and capacity exactly to approved evidence; remove invented urgency. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Headline Bank

**بانک تیتر · `copy_ads.headline_bank`**

Generate genuinely distinct reader angles, then compare them against the supplied subject and evidence.

Required inputs: subject, facts, placement. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `distinct_headlines` / تیترهای متمایز | Group headlines by angle rather than near-synonym. |
| `selection_rationale` / دلیل انتخاب | Explain which reader and placement each strong option serves. |

Review: No clickbait: review the actual Headline bank against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Semantic distinctness: review the actual Headline bank against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Tagline Slogan

**شعار و عبارت برند · `copy_ads.tagline_slogan`**

Turn the approved position into a compact line; originality and legal availability remain review tasks.

Required inputs: brand_position, voice, proof. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `options` / گزینه‌ها | Give a small set of conceptually different taglines. |
| `rationale` / دلیل | Explain the relation to the brand's evidenced position. |
| `usage_note` / راهنمای کاربرد | State where each line works and what screening remains. |

Review: Unsupported superlatives: review the actual Tagline and slogan against supplied evidence. Originality review: review the actual Tagline and slogan against supplied evidence. Brand fit: review the actual Tagline and slogan against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Print Outdoor Ad

**متن آگهی چاپی و محیطی · `copy_ads.print_outdoor_ad`**

Account for viewing distance, reading time and physical contact details.

Required inputs: offer, reading_context, space. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `headline` / تیتر | Write the idea that survives a brief glance. |
| `body` / متن | Add only essential supporting detail or terms. |
| `contact_or_cta` / تماس یا اقدام | Print the verified contact or action clearly. |

Review: Legibility context: review the actual Print and outdoor copy against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Contact accuracy: review the actual Print and outdoor copy against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Offer Announcement

**معرفی پیشنهاد یا تخفیف · `copy_ads.offer_announcement`**

Treat the price and conditions as a single offer; never create a deadline to improve urgency.

Required inputs: price, terms, dates, eligibility. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `offer_copy` / متن پیشنهاد | State the approved price or benefit. |
| `conditions` / شرایط | Include date, timezone where relevant, eligibility and exclusions. |
| `cta` / اقدام بعدی | State the actual redemption action. |

Review: Preserve approved amount, currency, unit, eligibility and date without modifying commercial terms. Deadline integrity: review the actual Offer announcement against supplied evidence. Match deadline, scarcity and capacity exactly to approved evidence; remove invented urgency. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
