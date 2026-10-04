# People and team communications / منابع انسانی و ارتباطات تیم

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Support a fair, concrete conversation about roles, expectations and observed work.

Tone: Respectful, behavior-based and private; humor is restricted. Avoid: Mind-reading, identity judgments, invented observations and discriminatory criteria.

Evidence: Approved role criteria, observed examples, policy and audience permissions.

Destination budget: Use only relevant details; formal employment decisions require qualified review.

Shared craft: [existing family method](../playbooks-messages.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Job description](#job-description)
- [Recruitment ad](#recruitment-ad)
- [Employee onboarding guide](#employee-onboarding)
- [Employee handbook draft](#handbook)
- [Performance feedback](#performance-feedback)
- [Performance-review narrative](#performance-review)
- [Interview scorecard copy](#interview-scorecard)
- [Culture and values memo](#culture-memo)
- [Organizational-change message](#change-announcement)
- [Exit and transition communication](#exit-transition)

## Job Description

**شرح شغل · `people.job_description`**

Describe the actual work, scope and necessary requirements fairly.

Required inputs: actual_role, scope, requirements, terms. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `job_description` / شرح شغل | State role, responsibilities, requirements and approved terms. |
| `success_expectations` / انتظارهای موفقیت | Define what successful performance looks like without invented targets. |

Review: No fake terms: review the actual Job description against supplied evidence. Inclusive language: review the actual Job description against supplied evidence. Role accuracy: review the actual Job description against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Recruitment Ad

**آگهی استخدام · `people.recruitment_ad`**

Present a real role with relevant criteria and approved benefits only.

Required inputs: approved_role, terms, application_route. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `ad` / آگهی | Introduce the actual opportunity and terms. |
| `requirements` / نیازمندی‌ها | List job-related requirements without discriminatory proxies. |
| `apply_copy` / متن درخواست | Give the verified application route. |

Review: No discriminatory filter: review the actual Recruitment ad against supplied evidence. No fake benefits: review the actual Recruitment ad against supplied evidence. Contact accuracy: review the actual Recruitment ad against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Employee Onboarding

**آن‌بوردینگ کارکنان · `people.employee_onboarding`**

Help a new colleague navigate the actual process and permitted resources.

Required inputs: actual_process, roles, resources. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `guide` / راهنما | Explain the organization and role-specific workflow. |
| `first_steps` / گام‌های نخست | List first actions and required resources. |
| `contacts` / راه‌های تماس | Name confirmed contacts and access-request paths without secrets. |

Review: Role accuracy: review the actual Employee onboarding guide against supplied evidence. Resource accuracy: review the actual Employee onboarding guide against supplied evidence. No secrets in copy: review the actual Employee onboarding guide against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Handbook

**راهنمای کارکنان · `people.handbook`**

Organize approved policies without inventing obligations for a jurisdiction.

Required inputs: approved_policies, jurisdiction, resources. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `handbook` / راهنما | Explain the relevant policies in accessible language. |
| `policy_links` / پیوند سیاست‌ها | Link to the controlling versions. |
| `review_items` / موارد بازبینی | List legal or policy questions requiring approval. |

Review: Mark the specific jurisdiction and issues requiring qualified legal review before adoption. No fake policy: review the actual Employee handbook draft against supplied evidence. Version accuracy: review the actual Employee handbook draft against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Performance Feedback

**بازخورد عملکرد · `people.performance_feedback`**

Describe observed behavior in a real situation and its impact. Separate interpretation from observation; invite the person's context and agree a next step without personality judgments.

Required inputs: observations, impact, role_expectations. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `feedback` / بازخورد | Write situation, behavior, impact and role expectation respectfully. |
| `examples` / مثال‌ها | Use only supplied observable examples, scoped to the recipient. |
| `agreement_questions` / پرسش‌های توافق | Invite context and propose a concrete next agreement; formal employment consequences require appropriate review. |

Review: Describe observed behavior and impact without labels about personality or inferred motivation. Tie each feedback example to a supplied observation, not an invented incident. Privacy fit: review the actual Performance feedback against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Performance Review

**گزارش ارزیابی عملکرد · `people.performance_review`**

Apply the same role criteria to verified outcomes, preserving context and uncertainty.

Required inputs: verified_outcomes, criteria, employee_context. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `review` / ارزیابی | Write a criterion-based review. |
| `evidence` / شواهد | Attach observed evidence; do not invent a rating. |
| `growth_plan` / برنامهٔ رشد | Propose growth steps for agreement. |

Review: Criteria consistency: review the actual Performance-review narrative against supplied evidence. No fake score: review the actual Performance-review narrative against supplied evidence. Privacy fit: review the actual Performance-review narrative against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Interview Scorecard

**فرم و متن ارزیابی مصاحبه · `people.interview_scorecard`**

Evaluate only job-relevant criteria against actual interview evidence.

Required inputs: role_criteria, interview_evidence. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `questions` / پرسش‌ها | Provide relevant questions tied to role criteria. |
| `rubric` / معیار داوری | Define observable rating anchors without filling unsupported scores. |
| `evidence_notes` / یادداشت شواهد | Record evidence and gaps independently of impressions. |

Review: Job relevance: review the actual Interview scorecard copy against supplied evidence. No discriminatory filter: review the actual Interview scorecard copy against supplied evidence. No fake score: review the actual Interview scorecard copy against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Culture Memo

**پیام فرهنگ و ارزش‌ها · `people.culture_memo`**

Connect actual values to observable behaviors rather than aspirational slogans.

Required inputs: actual_values, examples, context. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `memo` / یادداشت | Explain the value in a real workplace situation. |
| `behavior_examples` / نمونهٔ رفتار | Use verified or clearly illustrative behavior examples. |

Review: No empty promises: review the actual Culture and values memo against supplied evidence. No fake story: review the actual Culture and values memo against supplied evidence. Reader fit: review the actual Culture and values memo against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Change Announcement

**اعلان تغییر سازمانی · `people.change_announcement`**

Explain approved changes and known impact without guessing personnel reasons.

Required inputs: approved_change, known_impacts, next_steps. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `message` / پیام | State the approved change respectfully. |
| `faq` / پرسش‌ها | Answer known questions while retaining uncertainty. |
| `support_routes` / مسیرهای پشتیبانی | Give actual support and next-step routes. |

Review: Privacy fit: review the actual Organizational-change message against supplied evidence. No speculation: review the actual Organizational-change message against supplied evidence. No fake commitments: review the actual Organizational-change message against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Exit Transition

**ارتباطات خروج و انتقال مسئولیت · `people.exit_transition`**

Respect the approved disclosure scope and real transition plan.

Required inputs: approved_facts, transition_plan, audience. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `message` / پیام | Write the permitted announcement without invented reason. |
| `handover_notice` / اطلاعیهٔ تحویل | Explain actual handover arrangements. |
| `review_items` / موارد بازبینی | Identify privacy and employment-review items. |

Review: Mark the specific jurisdiction and issues requiring qualified legal review before adoption. Privacy fit: review the actual Exit and transition communication against supplied evidence. No fake reason: review the actual Exit and transition communication against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
