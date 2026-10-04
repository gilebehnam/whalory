# Credentials, presentations and business development / کردنشیال، ارائه و توسعه‌ی کسب‌وکار

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Help a prospective client assess demonstrated qualifications and a proposed scope.

Tone: Confident but evidenced; explain the actual role and contribution. Avoid: Fabricated clients, logos, outcomes, titles, testimonials and guarantees.

Evidence: Work samples, contribution, permission to name/show, outcome evidence and approved terms.

Destination budget: Structure around the buyer decision; deck and document budgets are supplied, not universal.

Shared craft: [existing family method](../playbooks-strategy.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Company credential profile](#company-credential)
- [Agency credentials deck](#agency-credential)
- [Freelancer credential profile](#freelancer-profile)
- [Professional and executive bio](#professional-bio)
- [Portfolio copy](#portfolio)
- [Evidence-backed case study](#case-study)
- [Business and freelance proposal](#proposal)
- [RFP and tender response](#rfp-response)
- [Business and investor pitch deck](#pitch-deck)
- [Statement of work draft](#sow)

## Company Credential

**کردنشیال و پروفایل شرکت · `credentials_sales.company_credential`**

Present who does what, for whom, and with what demonstrated experience. Show real contribution and permission for every client, logo, quotation and result; never ask for login secrets.

Required inputs: company_facts, services, team, approved_cases. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `profile_sections` / بخش‌های معرفی | Structure introduction, expertise, working method, team, scope and contact. |
| `evidence` / شواهد | Attach source and naming/display permission to each material qualification claim. |
| `cases` / پروژه‌ها | Show selected projects with context, actual role, observed outcome and limits; unknown metrics stay placeholders. |
| `contact` / تماس | Give the approved next collaboration step and contact route. |

Review: No fake clients: review the actual Company credential profile against supplied evidence. Evidence links: review the actual Company credential profile against supplied evidence. Confirm permission for the actual client, person or partner to be named. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Agency Credential

**کردنشیال آژانس · `credentials_sales.agency_credential`**

Explain the agency's services and accountable contribution without attributing all client outcomes to the agency.

Required inputs: agency_services, team, case_evidence. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `deck_copy` / متن ارائه | Create slide copy suited to the buyer's evaluation. |
| `service_map` / نقشهٔ خدمات | Map services to actual team capability and scope. |
| `cases` / پروژه‌ها | Present permitted cases with role and evidenced results. |

Review: No fake clients: review the actual Agency credentials deck against supplied evidence. Use only evidenced outcomes with period and definition; never substitute an attractive invented metric. Confirm permission for the actual client, person or partner to be named. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Freelancer Profile

**پروفایل و کردنشیال فریلنسر · `credentials_sales.freelancer_profile`**

Help a client judge fit using verified work, actual role and current availability.

Required inputs: skills, verified_work, scope, availability. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `profile` / معرفی | Introduce specialization and working style. |
| `selected_work` / کارهای منتخب | Present selected work with attribution. |
| `offer` / پیشنهاد | Explain the offered scope and boundaries. |
| `contact` / تماس | Give a permitted contact route. |

Review: No fake experience: review the actual Freelancer credential profile against supplied evidence. Separate included deliverables, exclusions, dependencies and agreement status. Identity accuracy: review the actual Freelancer credential profile against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Professional Bio

**بیو حرفه‌ای و معرفی مدیر · `credentials_sales.professional_bio`**

Choose relevant verified roles for the audience while preserving chronology and privacy.

Required inputs: cv, verified_roles, reader, length. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `short_medium_long_bio` / زندگی‌نامه در سه طول | Provide short, medium and long bios with consistent names, titles and dates. |

Review: No fake titles: review the actual Professional and executive bio against supplied evidence. Chronology integrity: review the actual Professional and executive bio against supplied evidence. Privacy fit: review the actual Professional and executive bio against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Portfolio

**پورتفولیو و معرفی نمونه‌کار · `credentials_sales.portfolio`**

Make the creator's contribution and permission visible for each selected project.

Required inputs: work_samples, role, permission. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `project_intros` / معرفی پروژه‌ها | Introduce the actual project and context. |
| `role` / نقش | State the person's role distinctly from collaborators. |
| `process` / فرایند | Explain the actual process or artifact. |
| `outcome` / نتیجه | Report observed results with evidence and uncertainty. |

Review: Attribution accuracy: review the actual Portfolio copy against supplied evidence. Use only evidenced outcomes with period and definition; never substitute an attractive invented metric. Confirm rights to display each work sample, logo and asset. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Case Study

**کیس‌استادی مستند · `credentials_sales.case_study`**

Separate the starting problem, own contribution and observed outcome. Compare like periods and definitions; concurrent factors limit attribution.

Required inputs: case_facts, role, baseline, outcome, evidence. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `problem` / مسئله | Describe the supported starting context and problem. |
| `approach` / روش | Explain the actual intervention and role. |
| `results` / نتایج | State results with baseline, period and source; missing numbers remain missing. |
| `limits` / حدود | Retain causal limits, permissions and a short reusable case summary. |

Review: Baseline integrity: review the actual Evidence-backed case study against supplied evidence. Separate observed change from causal attribution and retain plausible concurrent factors. Use only evidenced outcomes with period and definition; never substitute an attractive invented metric. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Proposal

**پروپوزال و پیشنهاد همکاری · `credentials_sales.proposal`**

Separate estimate, option and commitment. Align each deliverable with acceptance, dependency and approved commercial terms.

Required inputs: client_need, scope, deliverables, terms. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `proposal` / پیشنهاد همکاری | Explain the client's problem and proposed approach. |
| `scope` / دامنه | Define included deliverables, exclusions and acceptance criteria. |
| `timeline` / زمان‌بندی | Show dependencies and proposed or approved timing with status labels. |
| `terms` / شرایط | State approved pricing and conditions, unresolved negotiations and next agreement step. |

Review: Separate included deliverables, exclusions, dependencies and agreement status. No fake commitments: review the actual Business and freelance proposal against supplied evidence. Preserve approved amount, currency, unit, eligibility and date without modifying commercial terms. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Rfp Response

**پاسخ به RFP و مناقصه · `credentials_sales.rfp_response`**

Read the supplied RFP before writing; missing tender documents block a substantive compliance claim.

Required inputs: rfp, capabilities, evidence, terms. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `compliance_matrix` / جدول انطباق | Map each requirement to response, evidence and compliance status. |
| `response` / پاسخ | Answer in the required order with actual capability evidence. |
| `gaps` / کمبودها | List unmet, unclear or unproven requirements explicitly. |

Review: Requirement traceability: review the actual RFP and tender response against supplied evidence. No fake compliance: review the actual RFP and tender response against supplied evidence. Evidence links: review the actual RFP and tender response against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Pitch Deck

**پیچ‌دک کسب‌وکار و سرمایه‌گذار · `credentials_sales.pitch_deck`**

Build the argument from real problem, solution, traction and market method; forecasts stay assumptions.

Required inputs: problem, solution, metrics, market_sources, ask. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `slide_copy` / متن اسلایدها | Give each slide one evidenced claim and a clear ask. |
| `speaker_notes` / یادداشت گوینده | Provide speakable notes that do not introduce unsupported extra claims. |
| `evidence` / شواهد | Attach metrics, market sources, dates and financial review items. |

Review: No fake traction: review the actual Business and investor pitch deck against supplied evidence. Market method: review the actual Business and investor pitch deck against supplied evidence. Financial narrative and forecasts need qualified review of data, assumptions and disclosure scope. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Sow

**شرح کار و دامنه‌ی قرارداد · `credentials_sales.sow`**

Draft scope and acceptance from supplied agreement points; do not invent binding terms.

Required inputs: scope, deliverables, roles, acceptance. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `sow_draft` / پیش‌نویس شرح خدمات | Describe deliverables, roles, boundaries and acceptance. |
| `assumptions` / فرض‌ها | Separate assumptions and dependencies from agreed obligations. |
| `review_items` / موارد بازبینی | Identify legal and commercial items for qualified review. |

Review: Separate included deliverables, exclusions, dependencies and agreement status. Mark the specific jurisdiction and issues requiring qualified legal review before adoption. No fake terms: review the actual Statement of work draft against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
