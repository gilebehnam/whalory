---
name: lessons
description: "List, prune, or export the lessons in a brand's LEARNINGS.md. Listing changes nothing; a prune or an export to a file is shown first and made only after you say yes."
argument-hint: "[list | prune | export] [brand]"
disable-model-invocation: true
---

Input: $ARGUMENTS

Work with the brand's learnings note, the file of lessons that every later task for the brand reads. Its method is `references/playbooks-strategy.md#lessons-from-feedback` in the `whalory` skill, and the row format is `references/judgment.md#learnings-note-format`.
The skill folder is `${CLAUDE_PLUGIN_ROOT}/skills/whalory/`.

With no action named, list.

## Find the note

Find the profile with the Whalory MCP tool `profile_lookup`, giving it the brand and the project folder. It returns the note's path and text when a note exists. Without the MCP tools, follow `SKILL.md#profile-lookup-order` and read the note next to the profile: `LEARNINGS.md` next to `VOICE.md`, `voice/LEARNINGS.md` next to `voice/VOICE.md`, or `<brand>.LEARNINGS.md` next to `<brand>.md` in `~/.whalory/profiles/`. With no brand profile, the note is `LEARNINGS.md` at the project root.

If there is no note, say where it would go and offer the `learn` command. Stop there.

## List

Show the rows, newest first, with the full path of the note. Keep each row's own words. Then flag three kinds of rows:

- three rows with the same decision: it is ready to move into the profile;
- a row the profile already holds, or one that a later row reverses;
- personal data of a customer, or a secret, in any row, which breaks `references/judgment.md#what-is-not-recorded`.

Listing changes nothing.

## Prune

1. Propose what to remove, and why for each row. Candidates are duplicates, rows a later row reverses, rows already moved into the profile, and rows that break the rules for what is not recorded.
2. Show the table before and after, and ask one question: "Apply this cleanup to `<file>`? a) Apply it (recommended) b) Change it first c) Leave the file as it is". In a Persian conversation: «این پاک‌سازی روی `<فایل>` انجام شود؟ الف) بله، انجام بده (پیشنهادی) ب) اول تغییرش بده ج) نه، دست نزن».
3. After a yes, rewrite only the rows of the table. The title, the notes above the table, and every row you keep stay word for word.
4. Never delete the note itself, and never edit the profile here. Moving a decision into the profile is the `voice` command's job, with its own yes.

## Export

Give the rows still in force as one Markdown table, headed by the brand and today's date, for a teammate or a paste-in prompt. Leave out any row with personal data, and any row the profile already holds. The export stays in the chat. When the user names a file, show its path and write it after a yes. Never write the export inside the skill or plugin folder.

## Return

For a list, the rows and the flags. For a prune or an export to a file, the change and its question; after a yes, the path that was written. This is not copy, so no diagnosis note comes with it.

Never change Whalory Hub settings. If the user wants to share statistics, tell them to run `hub_client.py consent` from the `whalory` skill's `scripts/` folder in their own terminal, or `hub_client.py on packets` for the weekly packet.
