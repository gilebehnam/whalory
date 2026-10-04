---
name: learn
description: "Keep a correction for next time: Whalory turns what you changed or said into one lesson row, shows it with its file, and adds it to the LEARNINGS.md next to the brand's voice profile only after you say yes."
argument-hint: "[the correction, e.g. no exclamation marks in our emails] [brand]"
disable-model-invocation: true
---

Correction: $ARGUMENTS

Turn the user's correction into one lesson row for the brand's learnings note. Every later task for this brand reads that note, so the user approves the exact row before it is written. Its method is `references/judgment.md#saving-a-lesson` in the `whalory` skill, and its playbook is `references/playbooks-strategy.md#lessons-from-feedback`.
The skill folder is `${CLAUDE_PLUGIN_ROOT}/skills/whalory/`.

## Find the note

1. Find the brand's profile with the Whalory MCP tool `profile_lookup`, giving it the brand and the project folder. Without the MCP tools, follow the order in `SKILL.md#profile-lookup-order`.
2. The note sits next to that profile:
   - `LEARNINGS.md` next to `VOICE.md` or `voice.json` at the project root;
   - `voice/LEARNINGS.md` next to `voice/VOICE.md`;
   - `<brand>.LEARNINGS.md` next to `<brand>.md` in `~/.whalory/profiles/`.
3. A starter profile, the skill's own profiles, and "no profile" have no note of their own. The row then goes in `LEARNINGS.md` at the project root. Outside a project, offer to build a profile with the `voice` command first.
4. Never write inside the skill or plugin folder. A profile that `profile_lookup` read from the old `~/.whalya/profiles/` folder gets no note there. Offer to move that profile to `~/.whalory/profiles/` first, as a separate step with its own yes.

## Build the row

1. Start from the user's own words. If the input is empty, use the last change the user made to copy you delivered in this conversation, and say which change you used. If there is none, ask in one line what to keep.
2. Sort it with `references/judgment.md#what-goes-where` and `references/judgment.md#what-is-not-recorded`. A one-off preference, a customer's personal data, and anything secret are never recorded; say why in one line and stop. If the profile already holds the rule, say so. The problem is then how the profile was read, and no row is needed.
3. Write one row in `references/judgment.md#learnings-note-format`: date, format, observation, and decision, with "not yet" in the last column. The format is one format id from `references/voice-profile.md#format-ids`, or "all". An observation says what happened, and a decision says what changes next time.
4. The row takes the language of the note. A new note follows the profile's language, or else the language of this conversation. A Persian row dates itself in the Solar Hijri calendar with Persian digits, as in «۱۴۰۵/۰۷/۰۶». An English row uses `YYYY-MM-DD`.

## Ask once

Show the row as a table, then the full path of its file. Say whether the file exists or will be created from the template. Then ask the "Lesson" question from `references/intake.md#question-bank-by-task`, in the language of this conversation:

- "Save this row to `<file>`? a) Save it (recommended) b) Change it first c) Leave it out"
- «این ردیف در `<فایل>` ذخیره شود؟ الف) بله، ذخیره کن (پیشنهادی) ب) اول تغییرش بده ج) نه»

This is the one question of the command. It isn't a request for permission, because the user approves the exact words that later work will follow (`references/intake.md#never-ask`).

## Save after a yes

1. After "save", append the row to the table at the end of the note. Leave every other line of the file as it is.
2. If the note doesn't exist yet, create it from the template in the note's language: `profiles/LEARNINGS-template.md` in Persian or `profiles/LEARNINGS-template.en.md` in English. Put the brand's name in the title, drop the sample row in brackets, and add the new row.
3. After "change it first", apply the change, show the row again, and ask the same question once more.
4. After "leave it out", or with no answer, write nothing.
5. Without file access, give the row as a Markdown table line for the user to paste into the note. In an automated run, write nothing and return the row under `needs_verification`.
6. If the note now holds three rows with the same decision, offer to move it into the profile. That is a separate step with its own yes, and the `voice` command does it.

## Return

The row, the full path of the note, and whether it was saved, created, or left out. This is not copy, so no diagnosis note comes with it.

Never change Whalory Hub settings. If the user wants to share statistics, tell them to run `hub_client.py consent` from the `whalory` skill's `scripts/` folder in their own terminal, or `hub_client.py on packets` for the weekly packet.
