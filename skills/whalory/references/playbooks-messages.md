# Playbooks: customer messages

This file is part of the [playbooks](playbooks.md). Each task's row is in the [task index](playbooks.md#task-index), and every playbook here assumes the [shared steps](playbooks.md#shared-steps). The "Questions" line of a playbook only names its row in the question bank; the [question gate](intake.md#decision-order) decides whether to ask. The "References" line lists the Persian craft files after "fa:" and the English ones after "en:". Read the list for the output language. The quality assurance (QA) line gives the checks and the `--format` id.

## Contents

- [Customer messages](#customer-messages)
  - [SMS](#sms)
  - [Email](#email)
  - [Customer reply](#customer-reply)

## Customer messages

### SMS

Transactional and marketing messages, one-time codes, and panel templates.

1. Decide the type: transactional or marketing (in Whalory Pro) (en: en/sms-push.md#transactional-or-marketing (in Whalory Pro)). The type changes the opt-out line and the sending rules. The details, with check dates, are in fa/sms.md (in Whalory Pro) for Iranian senders and en/sms-push.md (in Whalory Pro) for US, UK, and EU senders.
2. Shape: the brand name once, at the start, with a colon, as in «[برند]: [پیام]»; then what happened, what the reader needs to do, and by when. See where the sender name goes (in Whalory Pro) (en: en/sms-push.md#sender-identity (in Whalory Pro)).
3. A template never starts with a variable that can be empty, such as `{name}`: templates and variables (in Whalory Pro) (en: en/sms-push.md#templates-and-variables (in Whalory Pro)).
4. A link or a code goes on its own line. For Iranian senders, «لغو۱۱» (in Whalory Pro) depends on the SMS type:
   - A marketing SMS always ends with «لغو۱۱» on the last line.
   - A notice or service SMS from a service line carries «لغو۱۱» only when the panel or the operator requires it, with «[تأیید شود]» in the note.
   - One-time codes and transaction messages never carry this line.

   For US, UK, and EU senders, the opt-out wording and keywords follow en/sms-push.md#stop-and-help-keywords (in Whalory Pro) and en/sms-push.md#consent-and-opt-out (in Whalory Pro).
5. A one-time code fits in one segment, as in «[برند]: کد ورود [کد]. آن را به کسی ندهید.» No link and no promotion sits next to the code: one-time codes (in Whalory Pro) (en: en/sms-push.md#one-time-passcodes (in Whalory Pro)).
6. Count segments for the worst case: every variable at its longest possible value. A zero-width non-joiner (ZWNJ) counts as a character too: worst-case variable length (in Whalory Pro) (en: en/sms-push.md#worst-case-variable-length (in Whalory Pro)). In English, check how the characters you use change the encoding: en/sms-push.md#how-encoding-changes-the-count (in Whalory Pro).

**Questions:** The "SMS" row of the [question bank](intake.md#question-bank-by-task). No-default slot: the SMS type, when the request does not show it.
**References:** fa: [fa/channels.md#پیامک](fa/channels.md#پیامک), [fa/forms.md#پیامک-و-اعلان](fa/forms.md#پیامک-و-اعلان), fa/sms.md (in Whalory Pro), [fa/conventions.md#تلفن-کارت-کد](fa/conventions.md#تلفن-کارت-کد) · en: [en/channels.md#sms](en/channels.md#sms), en/sms-push.md (in Whalory Pro), [en/style-guide.md#phone-numbers](en/style-guide.md#phone-numbers)
**Output:** The SMS text. For a panel template, the variables use that panel's notation: templates and variables (in Whalory Pro). Next to the text, the character and segment count for the worst case.
**QA:** One segment if possible; no collective address such as "dear customers", and no exclamation mark. `--format sms`; for a code, `--format otp`. When `data/channels/` is present, add the channel: `--channel sms` (or `sms-otp` for a code) only for an Iranian SMS panel, and `--channel sms-intl` for any other sender. The `sms` channel holds the Iranian panel's limits, where one Persian segment is 70 characters. The `sms-intl` channel counts segments in GSM-7 or UCS-2.

### Email

1. The email type and a one-sentence goal: why it goes out now.
2. A subject with one detail, and a preheader that continues it. The opening sentence is news or a scene. One button.
3. A real sender and one person's signature.
4. For a cold outbound email, also follow en/email.md#cold-outreach (in Whalory Pro): an honest identity, one specific ask, and an easy way to opt out. The Persian method is fa/email-copy.md#فروشِ-سرد-به-کسب‌وکار-b2b (in Whalory Pro).

**Questions:** The "Email" row of the [question bank](intake.md#question-bank-by-task), the same three questions as fa/email-copy.md#سه-پرسش-پیش-از-نوشتن (in Whalory Pro) and en/email.md#before-you-write (in Whalory Pro).
**References:** fa: [fa/channels.md#ایمیل](fa/channels.md#ایمیل), [fa/forms.md#خبرنامه](fa/forms.md#خبرنامه), fa/email-copy.md (in Whalory Pro), fa/headlines.md#موضوعِ-ایمیل (in Whalory Pro) · en: [en/channels.md#email](en/channels.md#email), en/email.md (in Whalory Pro), en/headlines.md#email-subject-lines (in Whalory Pro)
**Output:** Subject, preheader, body, and button text.
**QA:** No «امیدواریم حالتان خوب باشد» and no "I hope this email finds you well"; one call to action. `--format email`; the subject with `--format subject`.

### Customer reply

1. The opening sentence shows that you understood the exact problem.
2. What was done, the time or the next step, and a short close.
3. For money, delays, and complaints: warmth one step lower, humor at 1.
4. Promise only what the team will actually do; anything unknown gets a bracket.

**Questions:** The "Customer replies and public reviews" row of the [question bank](intake.md#question-bank-by-task). No-default slot: the facts of the case, when the message does not give them.
**References:** fa: [fa/forms.md#پاسخ-به-مشتری](fa/forms.md#پاسخ-به-مشتری), fa/hard-messages.md (in Whalory Pro), fa/persuasion.md#اعتراض‌ها (in Whalory Pro), fa/conversational.md (in Whalory Pro) for auto-replies · en: [en/forms.md#customer-reply](en/forms.md#customer-reply), en/copywriting.md#objection (in Whalory Pro), en/anchors.md#apology (in Whalory Pro)
**Output:** One reply, ready to send.
**QA:** No stock thank-you in the opening sentence; an apology, if there is one, names the mistake. `--format reply`.

