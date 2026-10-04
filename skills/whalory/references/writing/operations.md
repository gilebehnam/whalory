# Operations, process and work documents / فرایند، عملیات و اسناد کار

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Let the responsible person perform or review a real process.

Tone: Operational, sequenced and explicit about roles and exceptions. Avoid: Invented controls, unapproved policy, secret disclosure and false completion.

Evidence: Observed process, actual systems, confirmed roles and completion evidence.

Destination budget: Steps follow real dependencies; proposals are visibly separate from current procedure.

Shared craft: [existing family method](../playbooks-strategy.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Standard operating procedure](#sop)
- [Work instruction](#work-instruction)
- [Meeting agenda](#meeting-agenda)
- [Meeting minutes and follow-up](#meeting-minutes)
- [Project status update](#project-status)
- [Handover document](#handover)
- [Internal policy draft](#policy-draft)
- [Internal knowledge-base article](#knowledge-base)
- [Incident postmortem](#postmortem)
- [Process-change communication](#process-change)
- [Regulated-information draft](#regulated-information)
- [Custom business writing format](#other-business-format)

## Sop

**روش اجرایی استاندارد SOP · `operations.sop`**

Document the actual procedure or clearly label a proposed design. Use confirmed systems, roles, triggers and controls; safety-sensitive steps need qualified review.

Required inputs: actual_process, roles, systems, exceptions. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `sop` / رویه | State purpose, scope, trigger, inputs, outputs and revision history. |
| `steps` / مراحل | Sequence executable steps with responsible role and completion evidence. |
| `checks` / کنترل‌ها | Describe existing checks and their pass/fail response. |
| `exceptions` / استثناها | Explain exceptions, escalation and recovery with no invented control. |

Review: Step accuracy: review the actual Standard operating procedure against supplied evidence. Role confirmation: review the actual Standard operating procedure against supplied evidence. No invented control: review the actual Standard operating procedure against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Work Instruction

**دستور کار عملیاتی · `operations.work_instruction`**

Make one task executable under the actual tools and conditions.

Required inputs: task, tools, conditions, checks. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `steps` / مراحل | Write ordered actions and visible completion evidence. |
| `warnings` / هشدارها | State real hazards and specialist-review needs. |
| `completion_check` / بررسی پایان | Give the actual completion check. |

Review: Step accuracy: review the actual Work instruction against supplied evidence. Safety review if needed: review the actual Work instruction against supplied evidence. Next step: review the actual Work instruction against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Meeting Agenda

**دستور جلسه · `operations.meeting_agenda`**

Allocate the available time to decisions rather than a list of vague topics.

Required inputs: purpose, topics, participants, time_budget. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `agenda` / دستور جلسه | Order topics with time and intended outcome. |
| `prep` / آمادگی | List real preparation materials. |
| `decisions` / تصمیم‌ها | Specify decisions the named participants are being asked to make. |

Review: Decision focus: review the actual Meeting agenda against supplied evidence. No fake attendees: review the actual Meeting agenda against supplied evidence. Time fit: review the actual Meeting agenda against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Meeting Minutes

**صورت‌جلسه و پیگیری · `operations.meeting_minutes`**

Record only decisions and assignments present in notes; unknown ownership remains unassigned.

Required inputs: notes, decisions, assigned_actions. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `minutes` / صورت‌جلسه | Summarize what was discussed and decided. |
| `action_register` / فهرست اقدام‌ها | List actions with confirmed owner and date or explicit gaps. |
| `open_items` / موارد باز | Keep unresolved questions separate from decisions. |

Review: No invented decision: review the actual Meeting minutes and follow-up against supplied evidence. Owner confirmation: review the actual Meeting minutes and follow-up against supplied evidence. Compare the output to source meaning including material qualifications, negations and uncertainty. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Project Status

**گزارش وضعیت پروژه · `operations.project_status`**

Distinguish completed, in-progress, blocked and proposed work from actual evidence.

Required inputs: actual_status, milestones, risks. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `status` / وضعیت | Summarize status and milestone evidence. |
| `blockers` / موانع | Explain current blockers and impact. |
| `decisions_needed` / تصمیم‌های لازم | State decisions needed without inventing progress percentages or dates. |

Review: No fake progress: review the actual Project status update against supplied evidence. No fake dates: review the actual Project status update against supplied evidence. Evidence labels: review the actual Project status update against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Handover

**سند تحویل و انتقال کار · `operations.handover`**

Transfer current state, assets and open work with provenance; never include login secrets.

Required inputs: current_state, assets, owners, open_work. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `handover` / تحویل | Explain current operating state and responsibilities. |
| `checklist` / فهرست کنترل | List actions and verification steps for the recipient. |
| `references` / منابع | Point to actual assets and authorized access locations without secrets. |

Review: Asset accuracy: review the actual Handover document against supplied evidence. No secrets in copy: review the actual Handover document against supplied evidence. Open item clarity: review the actual Handover document against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Policy Draft

**پیش‌نویس سیاست و مقررات داخلی · `operations.policy_draft`**

Draft approved intent for the stated jurisdiction while identifying unresolved authority and legal questions.

Required inputs: approved_intent, scope, jurisdiction, roles. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `policy_draft` / پیش‌نویس سیاست | Define scope, roles and proposed rules. |
| `exceptions` / استثناها | Explain known exceptions and escalation. |
| `review_items` / موارد بازبینی | List decisions and qualified review required before adoption. |

Review: Mark the specific jurisdiction and issues requiring qualified legal review before adoption. No fake obligation: review the actual Internal policy draft against supplied evidence. Role confirmation: review the actual Internal policy draft against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Knowledge Base

**مقاله‌ی دانش داخلی · `operations.knowledge_base`**

Organize supplied workflow knowledge around what a reader needs to do.

Required inputs: source_material, workflow, reader. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `article` / مقاله | Write a findable article with steps and scope. |
| `examples` / مثال‌ها | Use source-faithful examples. |
| `references` / منابع | Link to the actual versioned sources. |

Review: Compare the output to source meaning including material qualifications, negations and uncertainty. Version accuracy: review the actual Internal knowledge-base article against supplied evidence. Findability: review the actual Internal knowledge-base article against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Postmortem

**گزارش رخداد و درس‌آموخته · `operations.postmortem`**

Reconstruct the timeline from evidence and separate causal hypotheses from confirmed factors.

Required inputs: timeline, evidence, impact, actions. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `timeline` / زمان‌بندی | Record evidenced events and their times. |
| `causes_to_confirm` / علت‌های نیازمند بررسی | Explain supported factors and hypotheses to test. |
| `actions` / اقدام‌ها | Propose actions with owners and verification, avoiding personal blame. |

Review: No blame shift: review the actual Incident postmortem against supplied evidence. Separate observed change from causal attribution and retain plausible concurrent factors. No fake timeline: review the actual Incident postmortem against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Process Change

**اعلان تغییر فرایند · `operations.process_change`**

Explain what changes for affected roles and when, based on the approved process.

Required inputs: approved_change, affected_roles, date. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `change_notice` / اعلام تغییر | State the change and effective date. |
| `steps` / مراحل | Describe the actual changed actions. |
| `faq` / پرسش‌ها | Answer transition questions and unknowns. |

Review: Date integrity: review the actual Process-change communication against supplied evidence. Role confirmation: review the actual Process-change communication against supplied evidence. Change clarity: review the actual Process-change communication against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Regulated Information

**پیش‌نویس اطلاعات سلامت، مالی یا حقوقی · `operations.regulated_information`**

Produce informational drafting assistance for the stated market, using supplied sources and qualified review gates.

Required inputs: topic, market, verified_sources, reviewer. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `draft` / پیش‌نویس | Explain the topic without individualized expert certainty. |
| `sources` / منابع | List sources, dates and scope. |
| `review_gates` / بازبینی لازم | State the specific legal, financial, medical or safety review needed. |

Review: Regulated review: review the actual Regulated-information draft against supplied evidence. No expert certainty: review the actual Regulated-information draft against supplied evidence. Dated claims: review the actual Regulated-information draft against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Other Business Format

**قالب نوشتاری سفارشی کسب‌وکار · `operations.other_business_format`**

Agree the reader goal and destination before reusing the nearest structure; label the adaptation and unsupported capability.

Required inputs: goal, reader, input_material, destination. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `agreed_structure` / ساختار پیشنهادی | State the proposed structure and why it fits. |
| `copy` / متن | Draft only what supplied material supports. |
| `qa_notes` / یادداشت بررسی | Record gaps, adaptation status and necessary review. |

Review: Fallback transparency: review the actual Custom business writing format against supplied evidence. Fact locks: review the actual Custom business writing format against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
