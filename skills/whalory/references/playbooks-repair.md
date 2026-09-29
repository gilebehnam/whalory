# Playbooks: rewriting and review

This file is part of the [playbooks](playbooks.md). Each task's row is in the [task index](playbooks.md#task-index), and every playbook here assumes the [shared steps](playbooks.md#shared-steps). The "Questions" line of a playbook only names its row in the question bank; the [question gate](intake.md#decision-order) decides whether to ask. The "References" line lists the Persian craft files after "fa:" and the English ones after "en:". Read the list for the output language. The quality assurance (QA) line gives the checks and the `--format` id.

## Contents

- [Rewriting and review](#rewriting-and-review)
  - [Style repair](#style-repair)
  - [Scoring and review](#scoring-and-review)

## Rewriting and review

### Style repair

1. Diagnose with the questions before repair (fa: [ten questions](fa/style-repair.md#ده-پرسش-پیش-از-تعمیر); en: [en/style-repair.md#questions-before-you-repair](en/style-repair.md#questions-before-you-repair)); choose the lowest repair level that does the job.
2. Every number, name, and condition stays. Remove machine patterns with the AI-tells file of the text's language: [fa/ai-tells.md](fa/ai-tells.md) or [en/ai-tells.md](en/ai-tells.md).
3. Use `lint.py --fix` only for mechanical errors. To keep the facts, run `compare.py`, or count numbers, names, and conditions by hand.
4. A three-line report: what changed, and why.

**Questions:** The "Style repair" row of the [question bank](intake.md#question-bank-by-task). No-default slot: the depth of the repair. This applies only to a text of more than about 300 words whose request verb is ambiguous, such as «درستش کن» or "fix this". Otherwise, repair at sentence level.
**References:** fa: [fa/style-repair.md](fa/style-repair.md), [fa/common-errors.md](fa/common-errors.md), [fa/ai-tells.md](fa/ai-tells.md), fa/rewrites.md (in Whalory Pro) · en: [en/style-repair.md](en/style-repair.md), [en/common-errors.md](en/common-errors.md), [en/ai-tells.md](en/ai-tells.md), [en/prose.md](en/prose.md)
**Output:** The repaired text and the three-line report.
**QA:** No fact, number, or condition was removed or changed. The text's own format goes in `--format`.

### Scoring and review

1. Establish the text, the format, the reader, and the profile. Without them the score is a guess, and the note says so.
2. Automated: `lint.py --profile <profile> --format <format>`. Without code execution, the [manual QA](../SKILL.md#manual-qa) checklist for the text's language, then the list in [review.md](review.md).
3. The [scoring rubric](editor.md#scoring-rubric): ten axes, each scored 0 to 2, with a one-line reason.
4. The three quick tests (fa: [fa/ethics.md#سه-آزمونِ-سریع](fa/ethics.md#سه-آزمونِ-سریع); en: [en/ethics.md#three-quick-tests](en/ethics.md#three-quick-tests)), and the claims against the claims file of the text's language.
5. Fixes in order of impact: first what makes the text fail, then the rest.
6. A full rewrite only if the user asks for one; otherwise, suggestions sentence by sentence.

**Questions:** The "Base questions" row of the [question bank](intake.md#question-bank-by-task).
**References:** [review.md](review.md), [editor.md](editor.md) · fa: [fa/ai-tells.md](fa/ai-tells.md), [fa/ethics.md](fa/ethics.md), [fa/claims.md](fa/claims.md), fa/testing.md#آزمون‌های-سریع (in Whalory Pro) · en: [en/ai-tells.md](en/ai-tells.md), [en/ethics.md](en/ethics.md), [en/claims.md](en/claims.md)
**Output:** A score table (axis, score, reason, fix), the total out of 20, and the three most important fixes.
**QA:** A pass follows the [scoring rubric](editor.md#scoring-rubric): at least 17 out of 20, and no zero in fit with the brief, truthfulness, or cleanliness. Every score has a specific reason.

