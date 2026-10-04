# Support and difficult communications / پشتیبانی و ارتباطات دشوار

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Explain a verified customer situation and the available recovery path.

Tone: Calm, accountable and plain; humor is restricted. Avoid: Blame, false resolution, invented ETA and exposing private case data.

Evidence: Ticket facts, current policy, allowed remedies, status and next update owner.

Destination budget: Answer first, then steps and conditions; make unresolved status explicit.

Shared craft: [existing family method](../playbooks-messages.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Customer-support reply](#customer-reply)
- [Complaint response](#complaint-response)
- [Public-review reply](#review-reply)
- [Outage notice](#outage-notice)
- [Delay notice](#delay-notice)
- [Refund and return response](#refund-return)
- [Price-change communication](#price-change-notice)
- [Difficult stakeholder message](#hard-message)
- [Chatbot conversation flow](#chatbot-flow)
- [Help-center article](#help-article)

## Customer Reply

**پاسخ تیکت مشتری · `support.customer_reply`**

Answer the customer's actual question before explaining the allowed process.

Required inputs: ticket, case_facts, policy, allowed_actions. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `reply` / پاسخ | Write a calm case-specific reply under current policy. |
| `next_steps` / قدم‌های بعدی | List allowed next steps and unresolved ownership. |

Review: Policy accuracy: review the actual Customer-support reply against supplied evidence. Privacy fit: review the actual Customer-support reply against supplied evidence. No fake resolution: review the actual Customer-support reply against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Complaint Response

**پاسخ شکایت و نارضایتی · `support.complaint_response`**

Acknowledge the specific harm without accepting unverified claims or shifting blame.

Required inputs: complaint, verified_events, remedy. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `acknowledgment` / توجه به مسئله | Recognize the documented customer experience. |
| `explanation` / توضیح | Explain only verified events and current uncertainty. |
| `action` / اقدام | Offer an authorized remedy or next check with no invented promise. |

Review: No vague apology: review the actual Complaint response against supplied evidence. No blame shift: review the actual Complaint response against supplied evidence. No fake commitments: review the actual Complaint response against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Review Reply

**پاسخ نظر عمومی · `support.review_reply`**

Respond publicly without exposing order, payment or other private case data.

Required inputs: review, case_facts, public_scope. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `public_reply` / پاسخ عمومی | Give a concise respectful public reply. |
| `private_followup_route` / مسیر پیگیری خصوصی | Provide a legitimate private follow-up route without implying contact already happened. |

Review: No private data: review the actual Public-review reply against supplied evidence. Context fidelity: review the actual Public-review reply against supplied evidence. Calm tone: review the actual Public-review reply against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Outage Notice

**اطلاع‌رسانی اختلال · `support.outage_notice`**

Separate known scope from investigation; lack of ETA stays explicit.

Required inputs: affected_scope, known_status, next_update. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `notice` / اطلاعیه | State the incident and affected experience. |
| `status` / وضعیت | Describe confirmed status and uncertainty. |
| `update_path` / مسیر اطلاع‌رسانی | Give an approved next-update channel or time, never a guessed fix time. |

Review: Use only an approved estimate with status and timezone; unknown ETA remains unknown. Match the message to actual known state and allowed actions; never imply a completed action. Impact clarity: review the actual Outage notice against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Delay Notice

**پیام تأخیر و بدقولی · `support.delay_notice`**

Acknowledge the original commitment and describe verified current status.

Required inputs: original_commitment, actual_status, new_plan. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `notice` / اطلاعیه | Explain the delay without invented cause. |
| `options` / گزینه‌ها | Offer the options actually available. |
| `next_update` / اطلاع‌رسانی بعدی | State the approved next update or mark it unconfirmed. |

Review: Use only an approved estimate with status and timezone; unknown ETA remains unknown. Commitment accuracy: review the actual Delay notice against supplied evidence. Choice clarity: review the actual Delay notice against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Refund Return

**بازپرداخت و مرجوعی · `support.refund_return`**

Distinguish eligibility, requested refund, approved refund and completed payment.

Required inputs: policy, case_status, eligible_actions. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `reply` / پاسخ | Answer the case under the supplied policy. |
| `steps` / مراحل | Explain the allowed process and required information. |
| `conditions` / شرایط | Retain conditions and unresolved legal review where relevant. |

Review: Policy accuracy: review the actual Refund and return response against supplied evidence. Do not confirm success when the supplied state is pending, failed or unknown. Legal review if needed: review the actual Refund and return response against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Price Change Notice

**اطلاع تغییر قیمت · `support.price_change_notice`**

Explain the approved change without modifying existing contractual terms.

Required inputs: approved_change, effective_date, existing_terms. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `notice` / اطلاعیه | State what changes and the effective date. |
| `faq` / پرسش‌ها | Answer impact questions using current terms. |
| `options` / گزینه‌ها | Describe actual available choices. |

Review: No payment changes: review the actual Price-change communication against supplied evidence. Term clarity: review the actual Price-change communication against supplied evidence. Date integrity: review the actual Price-change communication against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Hard Message

**پیام سخت به ذی‌نفعان · `support.hard_message`**

Explain the authorized decision respectfully without speculative motive or humor.

Required inputs: decision, reason, affected_people, options. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `message` / پیام | State the decision and supported reason. |
| `questions` / پرسش‌ها | Address likely questions without disclosing others' private data. |
| `next_steps` / قدم‌های بعدی | Give real options and next steps. |

Review: Privacy fit: review the actual Difficult stakeholder message against supplied evidence. No fake commitments: review the actual Difficult stakeholder message against supplied evidence. Humor guardrail: review the actual Difficult stakeholder message against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Chatbot Flow

**دیالوگ چت‌بات · `support.chatbot_flow`**

Map intents only to actual knowledge and actions; unknowns need a real handoff.

Required inputs: intents, knowledge, actions, fallback. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `dialogue_nodes` / گره‌های گفت‌وگو | Write dialogue nodes keyed to verified intents. |
| `transitions` / انتقال‌ها | Define allowed transitions and unresolved inputs. |
| `handoff` / ارجاع | Provide honest human escalation and failure fallback. |

Review: Capability truth: review the actual Chatbot conversation flow against supplied evidence. Fallback safety: review the actual Chatbot conversation flow against supplied evidence. No fake resolution: review the actual Chatbot conversation flow against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Help Article

**مقاله‌ی راهنما و مرکز کمک · `support.help_article`**

Follow the actual product version and runnable steps, with recovery where they fail.

Required inputs: actual_steps, version, known_failures. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `steps` / مراحل | Write numbered actions and expected visible results. |
| `screens_notes` / یادداشت صفحه‌ها | Describe required screens without inventing screenshots. |
| `troubleshooting` / رفع اشکال | Explain known failures and available next steps. |

Review: Step accuracy: review the actual Help-center article against supplied evidence. Version accuracy: review the actual Help-center article against supplied evidence. Next step: review the actual Help-center article against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
