# PR and media communications / روابط عمومی و رسانه

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Communicate confirmed news or a public position with attributable facts.

Tone: Measured public language with authorized quotation and disclosure. Avoid: Speculation, fabricated quotes, unsupported news and invented spokesperson authority.

Evidence: Approved facts, dated events, quote/partner permission and media contact.

Destination budget: Match announcement, Q&A or speaking format; use supplied timing.

Shared craft: [existing family method](../playbooks-messages.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Press release](#press-release)
- [Press kit](#press-kit)
- [Media pitch](#media-pitch)
- [Founder announcement](#founder-announcement)
- [Crisis statement draft](#crisis-statement)
- [Interview preparation](#interview-qa)
- [Executive speech](#executive-speech)
- [Event and speaker introduction](#event-intro)
- [Partnership announcement](#partnership-announcement)
- [Public stakeholder Q&A](#public-qa)

## Press Release

**بیانیه و خبر رسمی · `pr_media.press_release`**

Lead with actual news and dated facts; quotations need approval and attribution.

Required inputs: news, facts, approved_quotes, contact. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `release` / بیانیه | Write the release in news order with only approved quotes. |
| `boilerplate` / معرفی ثابت | Describe the organization using verified facts. |
| `contact` / تماس | Give the authorized media contact. |

Review: Quote permission: review the actual Press release against supplied evidence. Dated claims: review the actual Press release against supplied evidence. No fake news: review the actual Press release against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Press Kit

**پرس‌کیت و معرفی رسانه‌ای · `pr_media.press_kit`**

Assemble a source-checkable media packet with explicit asset rights.

Required inputs: facts, approved_assets, spokespeople. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `fact_sheet` / برگهٔ واقعیت | Provide a dated fact sheet. |
| `bios` / معرفی افراد | Use approved speaker biographies. |
| `assets_manifest` / فهرست فایل‌ها | List actual assets, captions, permissions and missing items. |

Review: Source quality: review the actual Press kit against supplied evidence. List each actual asset source and usage permission; placeholders or briefs are not delivered assets. Contact accuracy: review the actual Press kit against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Media Pitch

**پیشنهاد سوژه به رسانه · `pr_media.media_pitch`**

Explain the evidence-backed news angle without pretending a journalist relationship.

Required inputs: angle, evidence, recipient_context. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `pitch` / پیشنهاد | Write a relevant concise pitch. |
| `subject` / موضوع پیام | Use a factual subject line. |
| `source_offer` / دسترسی به منبع | Offer access to actual evidence or authorized spokespersons. |

Review: Newsworthiness: review the actual Media pitch against supplied evidence. No fake quotes: review the actual Media pitch against supplied evidence. Deliver a draft or export only; no email, direct message or post is sent. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Founder Announcement

**اعلان بنیان‌گذار · `pr_media.founder_announcement`**

Use the founder's real role and voice to explain the confirmed event.

Required inputs: actual_event, founder_role, facts. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `announcement` / اعلام | Write the actual announcement without fictional memories. |
| `short_version` / نسخهٔ کوتاه | Provide a consistent shorter version. |

Review: No fake experience: review the actual Founder announcement against supplied evidence. Capability truth: review the actual Founder announcement against supplied evidence. Identity accuracy: review the actual Founder announcement against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Crisis Statement

**بیانیه‌ی بحران · `pr_media.crisis_statement`**

State known facts, unknowns and approved action without speculation or humor.

Required inputs: verified_events, unknowns, approved_actions. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `holding_statement` / بیانیهٔ اولیه | Write a limited holding statement with scope and uncertainty. |
| `update` / به‌روزرسانی | Provide an update structure tied to new confirmed facts. |
| `review_items` / موارد بازبینی | List legal, privacy and spokesperson approvals still required. |

Review: Mark the specific jurisdiction and issues requiring qualified legal review before adoption. No speculation: review the actual Crisis statement draft against supplied evidence. Privacy fit: review the actual Crisis statement draft against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Interview Qa

**آمادگی مصاحبه و پرسش‌وپاسخ · `pr_media.interview_qa`**

Answer actual questions with the spokesperson's approved facts; bridging cannot become evasion.

Required inputs: subject, facts, spokesperson, known_questions. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `question_answers` / پرسش و پاسخ | Give direct supported answers. |
| `bridges` / پیوند موضوعی | Offer honest bridges to relevant known information. |
| `gaps` / کمبودها | Mark unanswered or unauthorized topics. |

Review: No fake quotes: review the actual Interview preparation against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. No evasion: review the actual Interview preparation against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Executive Speech

**سخنرانی مدیر · `pr_media.executive_speech`**

Use the speaker's actual experience and occasion, then test speakability against time.

Required inputs: occasion, audience, facts, speaker_voice. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `speech` / سخنرانی | Write spoken copy with clear thought transitions. |
| `delivery_notes` / یادداشت اجرا | Indicate pauses and delivery needs as estimates, not measured timings. |

Review: Speakability: review the actual Executive speech against supplied evidence. No fake story: review the actual Executive speech against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Event Intro

**معرفی سخنران و مراسم · `pr_media.event_intro`**

Introduce the person using verified titles and relevant context.

Required inputs: verified_bio, event_context, pronunciation. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `intro` / مقدمه | Write a timed introduction based on the approved bio. |
| `transition` / انتقال | Provide the transition and pronunciation notes. |

Review: Identity accuracy: review the actual Event and speaker introduction against supplied evidence. No fake titles: review the actual Event and speaker introduction against supplied evidence. Timing fit: review the actual Event and speaker introduction against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Partnership Announcement

**اعلان همکاری مشترک · `pr_media.partnership_announcement`**

Describe only the approved partnership scope and naming permissions.

Required inputs: approved_scope, partners, permissions. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `announcement` / اعلام | State the confirmed collaboration and boundaries. |
| `partner_copy` / متن شریک | Provide partner-specific copy with matching facts. |
| `faq` / پرسش‌ها | Answer questions without implying unapproved commitments. |

Review: Partner permission: review the actual Partnership announcement against supplied evidence. No fake commitments: review the actual Partnership announcement against supplied evidence. Separate included deliverables, exclusions, dependencies and agreement status. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Public Qa

**پرسش‌وپاسخ عمومی ذی‌نفعان · `pr_media.public_qa`**

Answer public questions from approved facts without discussing private cases.

Required inputs: actual_questions, facts, approved_policy. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `qa` / پرسش و پاسخ | Pair real questions with supported answers. |
| `unresolved_items` / موارد باز | Identify topics requiring a policy or fact decision. |

Review: Policy accuracy: review the actual Public stakeholder Q&A against supplied evidence. Privacy fit: review the actual Public stakeholder Q&A against supplied evidence. No speculation: review the actual Public stakeholder Q&A against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
