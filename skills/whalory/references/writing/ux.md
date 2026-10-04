# UX writing for websites and apps / یوایکس رایتینگ وب‌سایت و اپلیکیشن

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Help a person understand the current state and take an allowed next action.

Tone: Short, accessible, calm and specific to system behavior. Avoid: Blame, false success, fake progress and guessed error causes.

Evidence: Actual states, allowed transitions, field purpose and exact locale placeholders.

Destination budget: Respect supplied per-key budgets; missing budgets stay unverified.

Shared craft: [existing family method](../playbooks-web.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Complete website or app flow copy](#flow-microcopy)
- [Button and label copy](#button-label)
- [Form labels and hints](#form-hint)
- [Onboarding copy](#onboarding)
- [Error and recovery copy](#error-recovery)
- [Empty and loading states](#empty-loading)
- [Confirmation and success copy](#confirmation-success)
- [Push notification](#push-notification)
- [Consent and permission copy](#consent-permissions)
- [Locale-file copy review](#locale-file-review)

## Flow Microcopy

**متن کامل یک جریان وب یا اپ · `ux.flow_microcopy`**

Map each string to a real state and allowed transition. Preserve keys and variables per key; keep unknown error causes unknown and failed actions distinct from success.

Required inputs: flow_states, user_goal, system_behavior. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `state_string_map` / جدول حالت و متن | Return state/key with title, body, action and helper; preserve existing identifiers and placeholders exactly. |
| `notes` / یادداشت‌ها | Explain state assumptions, accessibility, bidi and per-key space constraints outside user copy. |
| `fallbacks` / حالت جایگزین | Provide honest fallback and recovery copy for missing, waiting, denied and failed states. |

Review: Match the message to actual known state and allowed actions; never imply a completed action. Next step: review the actual Complete website or app flow copy against supplied evidence. Accessibility: review the actual Complete website or app flow copy against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Button Label

**دکمه و لیبل · `ux.button_label`**

Name what activation will actually do, not an aspirational result.

Required inputs: action, result, space. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `labels` / برچسب‌ها | Provide a context-specific action label. |
| `alternatives` / جایگزین‌ها | Offer shorter alternatives only when they keep the same action. |

Review: Action accuracy: review the actual Button and label copy against supplied evidence. Context clarity: review the actual Button and label copy against supplied evidence. Do not invent a maximum; distinguish characters, graphemes, bytes, units and SMS segments. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Form Hint

**فرم و راهنمای فیلد · `ux.form_hint`**

Explain what the field needs and why, and make validation actionable.

Required inputs: field_purpose, validation, data_use. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `labels` / برچسب‌ها | Name the field in the user's terms. |
| `hints` / راهنماها | Explain format or use only where helpful. |
| `validation_messages` / پیام‌های اعتبارسنجی | State the actual validation issue and allowed correction. |

Review: Field specificity: review the actual Form labels and hints against supplied evidence. Privacy clarity: review the actual Form labels and hints against supplied evidence. Accessibility: review the actual Form labels and hints against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Onboarding

**آنبوردینگ و نخستین استفاده · `ux.onboarding`**

Guide a person to the first real product value, making optional steps explicit.

Required inputs: product_job, steps, permissions. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `intro` / مقدمه | Explain the actual first-use goal. |
| `step_copy` / متن مراحل | Write copy for each supplied step and permission request. |
| `skip_copy` / متن عبور | Explain skipping and its real consequences. |

Review: Progress truth: review the actual Onboarding copy against supplied evidence. No forced friction: review the actual Onboarding copy against supplied evidence. Capability truth: review the actual Onboarding copy against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Error Recovery

**پیام خطا و بازیابی · `ux.error_recovery`**

Separate known failure from suspected cause. Explain what happened to data and the permitted recovery action.

Required inputs: error_cause, data_state, allowed_actions. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `title` / عنوان | Name the actual failure calmly. |
| `body` / متن | Describe known state, including whether data is preserved. |
| `recovery_cta` / اقدام بازیابی | Offer a recovery action that the product can perform. |

Review: No fake cause: review the actual Error and recovery copy against supplied evidence. Next step: review the actual Error and recovery copy against supplied evidence. Data preservation: review the actual Error and recovery copy against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Empty Loading

**حالت خالی و انتظار · `ux.empty_loading`**

Distinguish no data, filtered results, pending work and failed loading.

Required inputs: state, cause, next_action. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `empty_copy` / متن حالت خالی | Explain the specific empty state and useful first step. |
| `loading_copy` / متن انتظار | Describe waiting without fabricated percentage or ETA. |
| `cancel_copy` / متن لغو | Explain cancellation only if it is supported. |

Review: No fake progress: review the actual Empty and loading states against supplied evidence. Match the message to actual known state and allowed actions; never imply a completed action. Next step: review the actual Empty and loading states against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Confirmation Success

**تأیید و موفقیت · `ux.confirmation_success`**

Confirm only an actual completed result and reference the correct object.

Required inputs: actual_result, next_step, reference_data. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `confirmation` / تأیید نتیجه | State the verified completed action. |
| `summary` / خلاصه | Summarize the supplied reference and material conditions. |
| `next_action` / اقدام بعدی | Give the next available action. |

Review: Do not confirm success when the supplied state is pending, failed or unknown. Reference accuracy: review the actual Confirmation and success copy against supplied evidence. Next step: review the actual Confirmation and success copy against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Push Notification

**پوش نوتیفیکیشن · `ux.push_notification`**

Make the event understandable without exposing private detail on a lock screen.

Required inputs: event, recipient_context, deep_link. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `title` / عنوان | Name the event within supplied title space. |
| `body` / متن | Give the necessary context without sensitive disclosure. |
| `destination_note` / یادداشت مقصد | Record the exact supported deep link. |

Review: Permission fit: review the actual Push notification against supplied evidence. Link integrity: review the actual Push notification against supplied evidence. Do not invent a maximum; distinguish characters, graphemes, bytes, units and SMS segments. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Consent Permissions

**رضایت و دسترسی · `ux.consent_permissions`**

Explain a specific purpose, scope and choice; do not imply a choice exists when it does not.

Required inputs: data_purpose, scope, retention, choices. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `notice` / اطلاعیه | State what data is used, why and for how long. |
| `choices` / انتخاب‌ها | Write distinct accept, refuse or defer choices consistent with behavior. |
| `settings_copy` / متن تنظیمات | Explain where an existing choice can be changed. |

Review: Consent specificity: review the actual Consent and permission copy against supplied evidence. No preticked consent: review the actual Consent and permission copy against supplied evidence. Privacy clarity: review the actual Consent and permission copy against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Locale File Review

**متن فایل‌های زبان محصول · `ux.locale_file_review`**

Edit only values while preserving structure, key identity, interpolation and per-key variable count.

Required inputs: locale_file, key_context, variables. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `safe_string_updates` / متن‌های اصلاح‌شده | Return safe string updates under the original keys. |
| `change_notes` / یادداشت تغییر | Explain semantic changes, bidi issues and unresolved context outside the locale data. |

Review: Preserve every interpolation token under its original key with identical multiplicity. Keep every original locale key, nesting and value type; change text values only. Bidi accessibility: review the actual Locale-file copy review against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
