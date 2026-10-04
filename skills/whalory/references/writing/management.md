# Management, strategy and reporting / مدیریت، استراتژی و گزارش

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Help a decision maker distinguish evidence, choices and the requested decision.

Tone: Concise analytical language with uncertainty and tradeoffs. Avoid: Fake forecasts, unexplained metrics, assumed owners and correlation presented as cause.

Evidence: Data definitions, period, source, comparator, assumptions and confidentiality scope.

Destination budget: Decision summary first, evidence annex after; respect the supplied meeting budget.

Shared craft: [existing family method](../playbooks-strategy.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Business strategy memo](#strategy-memo)
- [Management decision memo](#decision-memo)
- [Board memo](#board-memo)
- [OKR draft and review](#okr)
- [KPI and WBR/MBR/QBR report](#kpi-report)
- [Executive summary](#executive-summary)
- [Business plan narrative](#business-plan)
- [Budget and financial narrative](#budget-narrative)
- [Management risk report](#risk-report)
- [Investor update](#investor-update)

## Strategy Memo

**یادداشت استراتژی کسب‌وکار · `management.strategy_memo`**

Frame the strategic choice and evidence before describing action.

Required inputs: context, evidence, goals, options. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `memo` / یادداشت | State the decision context and recommendation. |
| `choices` / انتخاب‌ها | Compare credible options. |
| `tradeoffs` / انتخاب‌ها و هزینه‌ها | Explain costs, risks and exclusions. |
| `actions` / اقدام‌ها | Propose the next decision or action. |

Review: Assumption labels: review the actual Business strategy memo against supplied evidence. No fake market data: review the actual Business strategy memo against supplied evidence. Decision clarity: review the actual Business strategy memo against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Decision Memo

**یادداشت تصمیم مدیریتی · `management.decision_memo`**

Make the decision and constraints explicit; uncertainty must survive the recommendation.

Required inputs: decision, options, evidence, constraints. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `recommendation` / پیشنهاد | Recommend one option with evidence and conditions. |
| `alternatives` / جایگزین‌ها | Compare actual alternatives fairly. |
| `risks` / ریسک‌ها | State risks, reversibility and missing information. |

Review: Evidence labels: review the actual Management decision memo against supplied evidence. Tradeoff clarity: review the actual Management decision memo against supplied evidence. No false certainty: review the actual Management decision memo against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Board Memo

**یادداشت و گزارش هیئت‌مدیره · `management.board_memo`**

Distinguish information for directors from decisions requested. Reconcile narrative with actual performance and financial evidence; unapproved decisions cannot become minutes.

Required inputs: actual_performance, risks, decisions_needed. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `summary` / خلاصه | Lead with the real decision need and evidence-backed situation. |
| `performance` / عملکرد | Report actual performance with source, period and assumptions; omit unavailable financial certainty. |
| `risks` / ریسک‌ها | Explain risks and alternative interpretations. |
| `asks` / درخواست‌ها | State precise asks, options and evidence annex references under the approved confidentiality scope. |

Review: Source traceability: review the actual Board memo against supplied evidence. Financial narrative and forecasts need qualified review of data, assumptions and disclosure scope. Decision clarity: review the actual Board memo against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Okr

**هدف و نتیجه‌ی کلیدی OKR · `management.okr`**

Separate outcomes from tasks. A target without a baseline is a proposal for agreement, and measurement needs a definition, denominator, period and source.

Required inputs: strategy, baseline, capacity, time_window. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `objectives` / هدف‌ها | Write qualitative objectives aligned to supplied strategy. |
| `key_results` / نتایج کلیدی | Specify measurable results with baseline and conditional target status. |
| `owners_to_confirm` / مسئولان نیازمند تأیید | Name confirmed owners or mark ownership for agreement; include review cadence and assumptions. |

Review: Outcome not task: review the actual OKR draft and review against supplied evidence. No fake targets: review the actual OKR draft and review against supplied evidence. Measurement clarity: review the actual OKR draft and review against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Kpi Report

**گزارش شاخص و WBR/MBR/QBR · `management.kpi_report`**

Keep zero distinct from missing and compare like definitions and periods. Driver explanations are hypotheses unless the evidence supports causation.

Required inputs: metrics, definitions, period, comparators. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `readout` / خوانش شاخص‌ها | Summarize performance with metric, value, unit, denominator, period and comparator. |
| `drivers` / توضیح تغییرها | Explain plausible drivers with linked evidence and qualitative uncertainty. |
| `uncertainties` / عدم قطعیت‌ها | Record missingness, changed definitions and limits. |
| `actions` / اقدام‌ها | Suggest actions tied to the decision, with owners and approval status explicit. |

Review: Show metric definition, denominator, unit, period and missingness; compare the same basis. Separate observed change from causal attribution and retain plausible concurrent factors. No fake numbers: review the actual KPI and WBR/MBR/QBR report against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Executive Summary

**خلاصه‌ی اجرایی · `management.executive_summary`**

Compress the source for the decision without removing material qualifications.

Required inputs: source_document, decision_context. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `summary` / خلاصه | State the essential situation and decision context. |
| `key_findings` / یافته‌های اصلی | Preserve key findings with source meaning. |
| `asks` / درخواست‌ها | Name actual decisions or requests; do not create new ones. |

Review: Compare the output to source meaning including material qualifications, negations and uncertainty. No missing caveats: review the actual Executive summary against supplied evidence. Decision focus: review the actual Executive summary against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Business Plan

**طرح کسب‌وکار · `management.business_plan`**

Describe the business model using source-backed market claims and explicit scenario assumptions.

Required inputs: model, market_sources, assumptions, capacity. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `plan` / طرح | Organize model, customers, operations, market and finances. |
| `assumptions` / فرض‌ها | Make inputs and dependencies of projections visible. |
| `scenarios` / سناریوها | Compare scenarios without presenting a forecast as guaranteed performance. |

Review: No fake forecast: review the actual Business plan narrative against supplied evidence. Market method: review the actual Business plan narrative against supplied evidence. Financial narrative and forecasts need qualified review of data, assumptions and disclosure scope. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Budget Narrative

**توضیح بودجه و سناریوی مالی · `management.budget_narrative`**

Explain supplied amounts and variance on a consistent basis without changing the budget.

Required inputs: actual_budget, assumptions, approved_scenarios. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `narrative` / شرح | Describe the approved budget and rationale. |
| `variance` / اختلاف | Explain arithmetic differences with period and unit. |
| `risks` / ریسک‌ها | State scenario assumptions and financial review needs. |

Review: Financial narrative and forecasts need qualified review of data, assumptions and disclosure scope. Number integrity: review the actual Budget and financial narrative against supplied evidence. No investment advice: review the actual Budget and financial narrative against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Risk Report

**گزارش ریسک مدیریتی · `management.risk_report`**

Distinguish observed exposure from estimated probability and confirm ownership.

Required inputs: observed_risks, evidence, owners. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `risk_summary` / خلاصهٔ ریسک | Describe each risk, evidence and possible impact. |
| `options` / گزینه‌ها | Present mitigation choices with tradeoffs. |
| `open_items` / موارد باز | Mark unowned risks and uncertain likelihoods. |

Review: No fake probability: review the actual Management risk report against supplied evidence. Assumption labels: review the actual Management risk report against supplied evidence. Owner confirmation: review the actual Management risk report against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Investor Update

**گزارش به سرمایه‌گذار · `management.investor_update`**

Give a balanced account of actual metrics, milestones and risks within disclosure permissions.

Required inputs: actual_metrics, milestones, risks, asks. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `update` / به‌روزرسانی | Summarize verified progress and obstacles. |
| `metrics` / شاخص‌ها | Report consistent metrics with definitions and period. |
| `asks` / درخواست‌ها | State actual requests without invented traction or commitments. |

Review: No fake traction: review the actual Investor update against supplied evidence. Number integrity: review the actual Investor update against supplied evidence. Confidentiality: review the actual Investor update against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
