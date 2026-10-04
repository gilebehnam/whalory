# DM, email and SMS / دایرکت، ایمیل و پیامک

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Answer or initiate a specific conversation with one appropriate next step.

Tone: Direct, courteous and matched to relationship and recipient state. Avoid: Fake familiarity, secret examples, assumed consent and unapproved promises.

Evidence: Thread context, case facts, allowed policy and correct destination.

Destination budget: A short message or named sequence; SMS segments differ from character count.

Shared craft: [existing family method](../playbooks-messages.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Direct-message reply](#dm-reply)
- [Direct-message outreach](#dm-outreach)
- [DM follow-up](#dm-followup)
- [Customer email](#customer-email)
- [Cold outreach email](#cold-email)
- [Email sequence](#email-sequence)
- [Transactional SMS and verification code](#sms-transactional)
- [Promotional SMS](#sms-promotion)
- [Messenger-channel post](#messenger-channel)
- [Event invitation and reminder](#event-invitation)

## Dm Reply

**پاسخ دایرکت · `messaging.dm_reply`**

Answer the actual message in the recipient's language. Use only known case facts and permitted remedies; escalation is a draft instruction, not a completed action.

Required inputs: incoming_message, case_facts, policy. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `reply` / پاسخ | Give the direct answer followed by an allowed next step; keep private details scoped to the conversation. |
| `optional_clarifying_question` / پرسش ضروری اختیاری | Ask one consequential question only if it changes the answer; do not send the draft. |

Review: Message context: review the actual Direct-message reply against supplied evidence. Privacy fit: review the actual Direct-message reply against supplied evidence. Deliver a draft or export only; no email, direct message or post is sent. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Dm Outreach

**دایرکت معرفی و همکاری · `messaging.dm_outreach`**

Use public relationship context without pretending familiarity or access to sensitive information.

Required inputs: recipient_context, offer, relationship. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `short_dm` / پیام کوتاه | Introduce relevant reason to contact and the real offer. |
| `optional_followup` / پیگیری اختیاری | Offer an optional later follow-up without manufacturing urgency. |

Review: No fake relationship: review the actual Direct-message outreach against supplied evidence. No sensitive inference: review the actual Direct-message outreach against supplied evidence. Deliver a draft or export only; no email, direct message or post is sent. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Dm Followup

**پیگیری دایرکت · `messaging.dm_followup`**

Respect the actual thread and elapsed context; a follow-up is not evidence that the recipient agreed.

Required inputs: previous_thread, time_context, next_step. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `followup` / پیگیری | Write a short contextual reminder. |
| `close_option` / گزینهٔ پایان | Offer a polite way to close or defer the conversation. |

Review: Context fidelity: review the actual DM follow-up against supplied evidence. Match deadline, scarcity and capacity exactly to approved evidence; remove invented urgency. Deliver a draft or export only; no email, direct message or post is sent. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Customer Email

**ایمیل به مشتری · `messaging.customer_email`**

Organize the message around the recipient's actual stage and needed action.

Required inputs: purpose, facts, recipient_stage. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `subject` / موضوع پیام | State the real purpose in the subject. |
| `preheader` / پیش‌نمایش | Add useful context in the preheader. |
| `body` / متن | Give the answer, facts and material conditions. |
| `cta` / اقدام بعدی | Name the actual next step. |

Review: Reader fit: review the actual Customer email against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Deliver a draft or export only; no email, direct message or post is sent. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Cold Email

**ایمیل معرفی سرد · `messaging.cold_email`**

Connect public recipient context to a real offer without invented personalization.

Required inputs: recipient_public_context, offer, proof. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `subject` / موضوع پیام | Write an honest specific subject. |
| `email` / ایمیل | Explain relevance and evidence succinctly. |
| `soft_cta` / درخواست کم‌فشار | Offer a low-pressure reply action; no send occurs. |

Review: No fake personalization: review the actual Cold outreach email against supplied evidence. Privacy fit: review the actual Cold outreach email against supplied evidence. Deliver a draft or export only; no email, direct message or post is sent. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Email Sequence

**توالی ایمیل · `messaging.email_sequence`**

Give each step a distinct job using the approved cadence and eligibility.

Required inputs: goal, stages, offer, approved_cadence. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `sequence` / دنباله | Write each step with stage, subject and body. |
| `entry_exit_notes` / شرایط شروع و پایان | Define entry, exit and suppression assumptions without activating automation. |

Review: Stage consistency: review the actual Email sequence against supplied evidence. Match deadline, scarcity and capacity exactly to approved evidence; remove invented urgency. Deliver a draft or export only; no email, direct message or post is sent. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Sms Transactional

**پیامک تراکنشی و کد تأیید · `messaging.sms_transactional`**

State a real event and preserve variables; never use a real secret or invent an expiry.

Required inputs: event, variables, sender, expiry. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `sms_template` / قالب پیامک | Provide the transactional template with exact placeholders. |
| `variables` / متغیرها | Describe each variable and approved expiry; segment limits remain separate from characters. |

Review: Preserve every interpolation token under its original key with identical multiplicity. No secret example: review the actual Transactional SMS and verification code against supplied evidence. Segment limits: review the actual Transactional SMS and verification code against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Sms Promotion

**پیامک تبلیغاتی · `messaging.sms_promotion`**

Keep offer and material terms together within an explicitly measured SMS budget.

Required inputs: offer, terms, recipient_scope. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `sms` / پیامک | Write concise offer copy with sender context. |
| `conditions` / شرایط | Preserve eligibility, deadline and exclusions. |
| `cta` / اقدام بعدی | Use the supplied action or URL unchanged. |

Review: Segment limits: review the actual Promotional SMS against supplied evidence. Preserve approved amount, currency, unit, eligibility and date without modifying commercial terms. Match deadline, scarcity and capacity exactly to approved evidence; remove invented urgency. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Messenger Channel

**متن کانال تلگرام و پیام‌رسان‌ها · `messaging.messenger_channel`**

Adapt the message to the named messenger's actual channel and button affordances.

Required inputs: channel, facts, links, goal. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `post` / پست | Write the sourced channel post. |
| `button_labels` / متن دکمه‌ها | Name supported buttons by their real action. |
| `links` / پیوندها | Preserve supplied URLs and destination notes. |

Review: Do not invent a maximum; distinguish characters, graphemes, bytes, units and SMS segments. Link integrity: review the actual Messenger-channel post against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Event Invitation

**دعوت‌نامه و یادآوری رویداد · `messaging.event_invitation`**

Distinguish event date, publication date and registration deadline with timezone.

Required inputs: event, date, timezone, location, registration. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `invitation` / دعوت | State the actual event, audience, date and location. |
| `reminder` / یادآوری | Write a reminder consistent with the same facts. |
| `cta` / اقدام بعدی | Give the verified registration path and conditions. |

Review: Date timezone integrity: review the actual Event invitation and reminder against supplied evidence. Contact accuracy: review the actual Event invitation and reminder against supplied evidence. No fake capacity: review the actual Event invitation and reminder against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
