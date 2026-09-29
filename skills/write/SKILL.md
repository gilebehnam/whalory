---
name: write
description: "Write or rewrite business copy in English or Persian with the Whalory method. A writer drafts, a blind editor reviews, and you get the text first, then the diagnosis note."
argument-hint: "[task, channel, language — e.g. LinkedIn post for our launch, en-GB]"
disable-model-invocation: true
---

Request: $ARGUMENTS

Follow the `whalory` skill for this request. If its `SKILL.md` isn't in your context yet, read it first.
It's at `${CLAUDE_PLUGIN_ROOT}/skills/whalory/SKILL.md`.
If the request is empty, ask in one line what to write.

## Detect, then ask only if you must

Fill the context card silently from the request, the open project, and the conversation (`references/router.md#context-card`). Then apply the question gate in `references/intake.md#decision-order`. Ask here, in this conversation, because subagents can't ask the user. The limits:

- three questions at most, in one message, each with a (recommended) option;
- only when the answer changes the text;
- never after "write" or «بنویس», and never when nobody can answer.

End the message with the escape line from `references/intake.md#question-format`. Without answers, use the recommended options and put brackets where facts are missing. Questions and the note use the language of the request.

## Draft

Delegate the draft to the `whalory:whalory-writer` subagent (`@agent-whalory:whalory-writer`).
The writer can't ask anything, so give it all it needs. That's the request, the context card, the answers, the materials with their file paths, and the profile. Add one line for the conversation language, `conversation language: fa` or `conversation language: en`, because the writer can't see the conversation and its note must match it. It returns a draft, a facts list, and a note.

## Blind review

Pass four inputs to the `whalory-editor` subagent: the draft, the facts list, the profile, and the format id with its channel. Leave out the conversation, the writer's note, and your own view of the draft. Add only a report-language line, `report language: fa` or `report language: en`, set to the language of this conversation. It tells the editor which language to answer in and says nothing about the draft.
In Claude Code, the editor is `whalory:whalory-editor` (`@agent-whalory:whalory-editor`).

## Fix

Apply every must-fix item. Take a line edit only when it keeps every number, name, and condition. If a fix needs a fact nobody gave, use a bracket: `[confirm: …]` in English copy, «[… تأیید شود]» in Persian copy. When the verdict is "return", fix the draft and send it to the editor once more with the same four inputs.

## Deliver

The text comes first. For repository files, apply the final values and list what changed. A short, separate note follows. It opens with the "Diagnosis:" line («تشخیص:» in a Persian conversation). The profile comes next, followed by the gaps, the brackets, and the claims to confirm before publishing. The note ends with the editor's total and the quality assurance (QA) line.

## Without subagents

If this host can't run subagents, play both roles in two separate passes. First, write the draft, the facts list, and the note by the steps of the `whalory` skill. Then run the blind-review protocol of `references/editor.md#blind-review-protocol` as a fresh pass:

1. Start again from four inputs alone: the draft, the profile, the format id with its channel, and the facts list. Read the draft as if someone else wrote it.
2. Load the profile and its entry for this format. Lint the draft with `lint_text`, or with the `whalory` skill's `scripts/lint.py` and `--facts`, and check the channel limit.
3. Treat any number, name, date, price, quote, or claim missing from the facts list as invented. It goes on the must-fix list.
4. Score the ten axes of `references/editor.md#scoring-rubric`, from 0 to 2 each. A pass needs 17 out of 20 and no zero in fit with the brief, truthfulness, or cleanliness. Then run the three quick ethics tests.
5. Write down the score table, at most seven must-fix items, and at most three line edits. Then apply the must-fix items.

Keep your drafting reasoning out of the review.
