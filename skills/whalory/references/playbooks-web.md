# Playbooks: interfaces, pages, and long-form copy

This file is part of the [playbooks](playbooks.md). Each task's row is in the [task index](playbooks.md#task-index), and every playbook here assumes the [shared steps](playbooks.md#shared-steps). The "Questions" line of a playbook only names its row in the question bank; the [question gate](intake.md#decision-order) decides whether to ask. The "References" line lists the Persian craft files after "fa:" and the English ones after "en:". Read the list for the output language. The quality assurance (QA) line gives the checks and the `--format` id.

## Contents

- [Interfaces and digital products](#interfaces-and-digital-products)
  - [UI microcopy](#ui-microcopy)
  - [Error, empty, and waiting states](#error-empty-and-waiting-states)
- [Pages and long-form copy](#pages-and-long-form-copy)
  - [About page](#about-page)

## Interfaces and digital products

### UI microcopy

1. One word for one concept across the whole product; the glossary lives in the profile.
2. A button is a verb and an object; a label is a plain noun; a confirmation message states the result, with no pleasantries.
3. Narrative density at 1.
4. The address, «تو» or «شما», follows the profile and stays the same across the product. This setting is Persian only.
5. If a screenshot came with the request, suggestions go in a table: element, current text, suggestion, and reason.

**Questions:** The "UI microcopy and repo strings" row of the [question bank](intake.md#question-bank-by-task).
**References:** fa: [fa/forms.md#ریزمتنِ-رابط](fa/forms.md#ریزمتنِ-رابط), fa/inclusive.md (in Whalory Pro), [fa/conventions.md](fa/conventions.md), fa/ux-strings.md (in Whalory Pro) · en: [en/forms.md#ui-microcopy](en/forms.md#ui-microcopy), en/ux-strings.md (in Whalory Pro), en/ux-strings.md#buttons (in Whalory Pro), en/inclusive.md (in Whalory Pro), [en/style-guide.md](en/style-guide.md)
**Output:** The strings in a table, or a table of suggestions for a screenshot.
**QA:** No ceremonious, bureaucratic confirmation; every button makes sense without context. `--format ui`.

### Error, empty, and waiting states

1. Error: what happened, what did not happen, and what to do now. No extra apology and no technical code in front of the user; a code, if needed, goes in small print for support.
2. Empty: one warm sentence and one way forward.
3. Waiting: what is in progress and roughly how long it takes, if that is known.
4. Failed payment, in Persian for Iranian payment gateways: «پرداخت انجام نشد. اگر مبلغی از حسابتان کم شده، معمولاً تا ۷۲ ساعتِ کاری برمی‌گردد.» Then a retry and a contact route. «پولی کم نشده» ("no money was taken") only when you are sure. In other markets, state only the refund timing the payment provider confirms: en/web-pages.md#payment-result-pages (in Whalory Pro).
5. Going to the payment gateway: the gateway's name and the next step, as in «به درگاهِ پرداختِ [زرین‌پال] می‌روید». «امن» ("secure") only next to the gateway's name. In English: en/web-pages.md#before-payment (in Whalory Pro).

**Questions:** The "UI microcopy and repo strings" row of the [question bank](intake.md#question-bank-by-task).
**References:** fa: [fa/forms.md#خطا-خالی-و-انتظار](fa/forms.md#خطا-خالی-و-انتظار), fa/web-pages.md#۴۰۴-و-صفحه‌ی-خالی (in Whalory Pro), fa/web-pages.md#ریزمتنِ-پرداخت (in Whalory Pro), fa/web-pages.md#صفحه‌ی-نتیجه‌ی-پرداخت (in Whalory Pro), fa/hard-messages.md#خرابی-و-قطعی (in Whalory Pro), fa/ux-strings.md (in Whalory Pro) · en: [en/forms.md#error-empty-and-wait-states](en/forms.md#error-empty-and-wait-states), en/ux-strings.md#error-messages (in Whalory Pro), en/ux-strings.md#empty-states (in Whalory Pro), en/web-pages.md#checkout-and-payment-pages (in Whalory Pro)
**Output:** Copy for each state, with its key or screen name.
**QA:** After reading, the reader knows what to do; no unsupported claim about money taken from an account. `--format error`.

## Pages and long-form copy

### About page

1. One real scene from the place and the work; the client provides it.
2. Say with verbs what you do; add one honest thing that has not happened yet.
3. No «چشم‌انداز و ارزش‌ها» and no «ما X نیستیم» ("vision and values", "we are not X").
4. Without a [brand profile](intake.md#definitions), write with a starter profile or the defaults, and turn building a profile into a follow-up question in the note. An about page uses the voice; it does not count as a [brand-building task](intake.md#definitions).

**Questions:** The "Base questions" row of the [question bank](intake.md#question-bank-by-task); for the real scene, [gathering.md](gathering.md#questions-that-draw-out-the-story).
**References:** fa: [fa/forms.md#درباره‌ی-ما](fa/forms.md#درباره‌ی-ما), fa/long-form.md#قصه‌ی-برند (in Whalory Pro), fa/people.md (in Whalory Pro), fa/web-pages.md#درباره‌ی-ما (in Whalory Pro) · en: [en/forms.md#about-page](en/forms.md#about-page), en/web-pages.md#about-pages (in Whalory Pro), en/storytelling.md (in Whalory Pro), en/anchors.md#about-page (in Whalory Pro)
**Output:** A short page: the scene, the work, the people, one thing not done yet, and one way to get in touch.
**QA:** Substitution test: with a rival's name in place, the text stops being true; no unsupported claim. `--format about`.

