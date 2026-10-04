---
name: review
description: "Blind review of English or Persian copy with Whalory: a score out of 20, must-fix items and a few line edits, checked against the voice profile, channel and facts."
argument-hint: "[file path or pasted text] [channel]"
disable-model-invocation: true
allowed-tools: Read Grep Glob
---

Input: $ARGUMENTS

Review the copy blind, as the Whalory editor. Leave the text as it is; the user gets a score and fixes, not a rewrite.

## Collect the four inputs

1. Draft: read the file the input names, or take the pasted text. If there is neither, ask for the text in one line.
2. Profile: the one the user names. Otherwise, take the first found in the order of `SKILL.md#profile-lookup-order` in the `whalory` skill, or call the Whalory MCP tool `profile_lookup`. Say which profile you used.
3. Format id and channel: from the input, such as `instagram.caption` or `email`, or from the file type. If you can't tell, use the closest format id and say so.
4. Facts list: the brief or source material the user supplied. If there's none, say "no facts list". The editor then treats every number, name, and claim as unverified.

## Review

Pass these four inputs, and nothing else, to the `whalory:whalory-editor` subagent (`@agent-whalory:whalory-editor`).
Don't pass the conversation or your own view of the text. Add only the report-language line, `report language: fa` or `report language: en`, set to the language of this conversation.

## Return

Give the editor's review as it stands:

1. the score table, with the total out of 20 and the verdict, "pass" or "return";
2. the must-fix list, seven items at most;
3. up to three line edits.

End with one line on the next step, such as running the `write` command with the must-fix list. A review of the user's own text is the editor pass itself, so it runs no revision loop of its own (`references/review.md#quality-loop`).

## Without subagents

If this host can't run subagents, run the blind-review protocol of `references/editor.md#blind-review-protocol` yourself.

1. Look only at the four inputs, as if someone else wrote the draft.
2. Load the profile and its entry for this format. Lint the text with `lint_text` or `lint_file` when the Whalory MCP tools are connected, and check the channel limit. Every lint error is a must-fix item.
3. Treat any number, name, date, price, quote, or claim missing from the facts list as invented. It goes on the must-fix list.
4. Score the ten axes of `references/editor.md#scoring-rubric`, from 0 to 2 each. A pass needs 17 out of 20 and no zero in fit with the brief, truthfulness, or cleanliness. Then run the three quick ethics tests.
5. Return the three parts above. Never rewrite the whole text.

Load method sections with the Whalory MCP tool `get_reference_section`, or read them from the `whalory` skill folder.
In Claude Code, that folder is `${CLAUDE_PLUGIN_ROOT}/skills/whalory/`.

Never change Whalory Hub settings. If the user wants to share statistics, tell them to run `hub_client.py consent` from the `whalory` skill's `scripts/` folder in their own terminal, or `hub_client.py on packets` for the weekly packet.
