# Product management and development / مدیریت محصول و توسعه

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Help a team decide and implement observable behavior from evidence.

Tone: Precise, testable and readable across product, design and engineering. Avoid: Invented research, unscheduled promises and proposed features presented as requirements.

Evidence: User evidence, approved scope, actual states, constraints and dependencies.

Destination budget: Trace each requirement to need and acceptance; document open questions separately.

Shared craft: [existing family method](../playbooks-web.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Product requirements document](#prd)
- [Product problem statement](#problem-statement)
- [Product opportunity brief](#opportunity-brief)
- [User stories and behavior scenarios](#user-stories)
- [Product acceptance criteria](#acceptance-criteria)
- [Roadmap narrative](#roadmap)
- [Release notes](#release-notes)
- [Discovery synthesis](#discovery-synthesis)
- [Product experiment plan](#experiment-plan)
- [Product strategy narrative](#strategy)

## Prd

**سند نیازمندی محصول PRD · `product.prd`**

Separate observed user need, product assumption and approved requirement. Trace each requirement to need and observable behavior; never invent interviews, metrics or scope approval.

Required inputs: problem, evidence, scope, constraints. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `prd` / سند نیازمندی | Provide problem, context, goals, non-goals and evidence with source status. |
| `requirements` / نیازمندی‌ها | Specify requirements, real states, edge cases and testable acceptance linked to needs. |
| `risks` / ریسک‌ها | List dependencies, failure modes, constraints and risks with evidence status. |
| `open_questions` / پرسش‌های باز | Keep unresolved scope, metrics and decisions explicit rather than turning them into requirements. |

Review: Problem solution traceability: review the actual Product requirements document against supplied evidence. Do not invent participants, interviews, study methods, findings or researcher authority. Each requirement needs an observable pass/fail outcome and meaningful boundary behavior. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Problem Statement

**بیانیه‌ی مسئله‌ی محصول · `product.problem_statement`**

Describe the user difficulty before proposing a solution; assumptions remain distinguishable from observations.

Required inputs: user_evidence, context, impact. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `statement` / بیانیه | State who experiences what problem in which context. |
| `evidence` / شواهد | Attach the supplied observations and impact evidence. |
| `gaps` / کمبودها | List what must be learned before certainty increases. |

Review: Do not invent participants, interviews, study methods, findings or researcher authority. Inference labels: review the actual Product problem statement against supplied evidence. Problem specificity: review the actual Product problem statement against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Opportunity Brief

**بریف فرصت محصول · `product.opportunity_brief`**

Organize signals around a possible opportunity without inventing market size.

Required inputs: signals, users, business_context. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `brief` / بریف | Explain user and business context with evidence status. |
| `options` / گزینه‌ها | Compare plausible options as proposals. |
| `unknowns` / نامعلوم‌ها | List missing validation and decision dependencies. |

Review: Evidence quality: review the actual Product opportunity brief against supplied evidence. No fake sizing: review the actual Product opportunity brief against supplied evidence. Uncertainty: review the actual Product opportunity brief against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## User Stories

**استوری کاربر و رفتارها · `product.user_stories`**

Express goals and observable value, not a list of implementation tasks.

Required inputs: roles, goals, flows, constraints. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `stories` / داستان‌های کاربر | Write role, goal and reason grounded in supplied flows. |
| `edge_cases` / حالت‌های مرزی | Include meaningful boundary and failure situations. |

Review: Goal clarity: review the actual User stories and behavior scenarios against supplied evidence. No invented requirement: review the actual User stories and behavior scenarios against supplied evidence. Testable behavior: review the actual User stories and behavior scenarios against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Acceptance Criteria

**معیار پذیرش محصول · `product.acceptance_criteria`**

Define observable outcomes for requirements without mirroring implementation choices.

Required inputs: requirements, states, edge_cases. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `criteria` / معیارها | Write clear pass/fail behavior tied to requirement ids. |
| `examples` / مثال‌ها | Give representative valid, invalid and boundary examples. |

Review: Testability: review the actual Product acceptance criteria against supplied evidence. Requirement traceability: review the actual Product acceptance criteria against supplied evidence. No implementation mirror: review the actual Product acceptance criteria against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Roadmap

**روایت و توضیح رودمپ · `product.roadmap`**

Explain why outcomes are ordered, including constraints and excluded alternatives. Distinguish planning horizons, estimates and existing commitments; do not invent team velocity.

Required inputs: goals, initiatives, capacity, dependencies. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `roadmap_narrative` / روایت نقشهٔ راه | Describe outcome priorities and initiative sequence with rationale. |
| `tradeoffs` / انتخاب‌ها و هزینه‌ها | Show what was deferred and why. |
| `uncertainties` / عدم قطعیت‌ها | Mark capacity evidence, dependencies, timing status and unresolved decisions. |

Review: No fake dates: review the actual Roadmap narrative against supplied evidence. Dependency consistency: review the actual Roadmap narrative against supplied evidence. Capacity labels: review the actual Roadmap narrative against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Release Notes

**یادداشت انتشار و تغییرات · `product.release_notes`**

Explain changes shipped in the named version from the user's perspective.

Required inputs: merged_changes, version, known_issues. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `notes` / یادداشت‌ها | List delivered changes only. |
| `user_impact` / اثر بر کاربر | Describe concrete user impact. |
| `limitations` / محدودیت‌ها | State known limitations and migration needs. |

Review: Version accuracy: review the actual Release notes against supplied evidence. Capability truth: review the actual Release notes against supplied evidence. No unshipped claims: review the actual Release notes against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Discovery Synthesis

**جمع‌بندی کشف و مصاحبه · `product.discovery_synthesis`**

Separate quotes and observations from themes inferred across a limited sample.

Required inputs: research_notes, method, participant_scope. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `themes` / موضوع‌ها | Group supported themes without claiming population prevalence. |
| `evidence` / شواهد | Link themes to permitted notes and participant scope. |
| `questions` / پرسش‌ها | Identify conflicting signals and next research questions. |

Review: Quote permission: review the actual Discovery synthesis against supplied evidence. Do not invent participants, interviews, study methods, findings or researcher authority. Selection bias labels: review the actual Discovery synthesis against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Experiment Plan

**طرح آزمایش محصول · `product.experiment_plan`**

Translate a hypothesis into a measurable comparison with decision rules and causal limits.

Required inputs: hypothesis, baseline, metrics, constraints. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `plan` / طرح | Define design, baseline, metrics, eligible population and procedure. |
| `decision_rules` / قواعد تصمیم | State prospective success/failure rules as proposals. |
| `risks` / ریسک‌ها | Document feasibility, bias and uncertainty; do not fabricate statistical power. |

Review: Metric definition: review the actual Product experiment plan against supplied evidence. No fake power: review the actual Product experiment plan against supplied evidence. Causal limits: review the actual Product experiment plan against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Strategy

**استراتژی محصول · `product.strategy`**

Make choices from market evidence, goals and actual capabilities, not aspirational feature lists.

Required inputs: market_evidence, goals, capabilities. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `choices` / انتخاب‌ها | State the selected choices and exclusions. |
| `rationale` / دلیل | Explain evidence and tradeoffs. |
| `assumptions` / فرض‌ها | Label strategic assumptions. |
| `actions` / اقدام‌ها | Propose actions with dependencies and decision owners to confirm. |

Review: Evidence labels: review the actual Product strategy narrative against supplied evidence. No fake market data: review the actual Product strategy narrative against supplied evidence. Tradeoff clarity: review the actual Product strategy narrative against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
