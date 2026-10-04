# Playbooks: voice, strategy, and teaching

This file is part of the [playbooks](playbooks.md). Each task's row is in the [task index](playbooks.md#task-index), and every playbook here assumes the [shared steps](playbooks.md#shared-steps). The "Questions" line of a playbook only names its row in the question bank; the [question gate](intake.md#decision-order) decides whether to ask. The "References" line lists the Persian craft files after "fa:" and the English ones after "en:". Read the list for the output language. The quality assurance (QA) line gives the checks and the `--format` id.

## Contents

- [Voice, strategy, and teaching](#voice-strategy-and-teaching)
  - [Voice profile in three questions](#voice-profile-in-three-questions)
  - [Lessons from feedback](#lessons-from-feedback)
  - [Whalory Hub: rules and feedback](#whalory-hub-rules-and-feedback)

## Voice, strategy, and teaching

### Voice profile in three questions

For a brand that has no [brand profile](intake.md#definitions) and whose request is the brand's voice itself: a [brand-building task](intake.md#definitions). A starter profile does not replace these three questions. In the "New brand" chain, these three questions are the three ★ lines of the brief card. The fuller route builds the profile from existing texts: [profile-builder.md](profile-builder.md).

1. Three questions in one message, each with options and one recommendation: the address, «تو» or «شما»; the formality; and one earlier text the brand likes. For an English profile, the three questions are in [profile-builder.md#three-questions-in-english](profile-builder.md#three-questions-in-english).
2. Build the draft profile from the answers and the defaults. `VOICE.md` comes from [_template.md](../profiles/_template.md), and `voice.json`, with `"schema_version": 2`, from [_template.json](../profiles/_template.json). For an English profile, use [_template.en.md](../profiles/_template.en.md) and [_template.en.json](../profiles/_template.en.json).
3. Write one short text with this profile and show it. If the answer is "not this", move one dial by one step; no more than two rounds.
4. Offer to save; save only with the user's approval or the brief. For one project, `VOICE.md` and `voice.json` go in the project root; for several projects, `~/.whalory/profiles/<brand>.md` and `.json`.
5. Never save in the skill's own `profiles` folder; a skill update erases it.
6. Without file access, give both files in the chat so the user can save them.
7. Next to the profile, an empty `LEARNINGS.md` from [LEARNINGS-template.md](../profiles/LEARNINGS-template.md), or [LEARNINGS-template.en.md](../profiles/LEARNINGS-template.en.md) in English.

**Questions:** The "Building a profile" row of the [question bank](intake.md#question-bank-by-task): these three questions.
**References:** [profile-builder.md#route-2-short-interview](profile-builder.md#route-2-short-interview), [voice-profile.md](voice-profile.md), [intake.md](intake.md) · fa: [fa/craft.md#تو-یا-شما](fa/craft.md#تو-یا-شما), [fa/persian-prose.md#نردبانِ-لحن](fa/persian-prose.md#نردبانِ-لحن) · en: [profile-builder.md#english-route](profile-builder.md#english-route), [en/style-guide.md#variants](en/style-guide.md#variants), [en/prose.md#contractions](en/prose.md#contractions)
**Output:** `VOICE.md`, `voice.json`, one sample text, and the sentence that offers to save.
**QA:** With this same `voice.json`, the sample text passes lint with no errors; every dial has a number.

### Lessons from feedback

For a correction the user wants kept, and for the learnings note itself: listing its rows, pruning them, or exporting them. The method is [saving a lesson](judgment.md#saving-a-lesson). In the plugin, the `learn` and `lessons` commands run it.

1. Find the profile in the [lookup order](../SKILL.md#profile-lookup-order), then its learnings note. With no brand profile, the note is `LEARNINGS.md` at the project root.
2. Save: sort the correction with [what goes where](judgment.md#what-goes-where) and [what is not recorded](judgment.md#what-is-not-recorded). Build one row, show it with its file, and write it only after a yes.
3. List: show the rows, newest first, and whether each one moved to the profile. Flag any decision with three rows, which is ready for the profile. Flag any row that holds personal data or a secret. Change nothing.
4. Prune: propose what to remove and why. Show the note before and after, and change it only after a yes. Never delete the note itself, and never edit the profile here.
5. Export: give the rows still in force as one Markdown table, headed by the brand and the date. It stays in the chat unless the user names a file; then write it after a yes. Leave out any row with personal data.

**Questions:** The "Lesson" row of the [question bank](intake.md#question-bank-by-task): one confirmation before any change to the file.
**References:** [judgment.md#learnings-note-format](judgment.md#learnings-note-format), [voice-profile.md#format-ids](voice-profile.md#format-ids) · fa: [LEARNINGS-template.md](../profiles/LEARNINGS-template.md) · en: [LEARNINGS-template.en.md](../profiles/LEARNINGS-template.en.md)
**Output:** The proposed row or change, its file, and one question; after a yes, the path that was written. No diagnosis note.
**QA:** Every row has a date, a format, an observation, and a decision. No row holds personal data, and nothing was written without a yes.

### Whalory Hub: rules and feedback

For questions about Whalory's signed rule updates, rule statistics, and the weekly packet. The method is [hub.md](hub.md). In the plugin, the `hub` and `feedback` commands run it.

1. With code execution, run the Hub client from the skill folder: `python <skill-path>/scripts/hub_client.py <command>`. Show its output as printed.
2. Status and sync: `status`, or `sync --force` to check for new rules now. Sum up the result in a few lines, then give the full output.
3. Sharing: never turn it on and never change a Hub setting. Give the user the exact command for their own terminal: `consent` for statistics, `on packets` for the weekly packet. Turning something off at the user's request is allowed: `off`, `off packets`, `off updates`, or `off all`.
4. The weekly packet: `packet --show`. Show the block exactly, say what it holds, and explain how the user can post it under their own GitHub account. Never post it and never run `gh`.
5. Without code execution, explain from [hub.md](hub.md) and give the commands for the user's own terminal.

**Questions:** None; the request is complete input.
**References:** [hub.md](hub.md), [review.md#quality-loop](review.md#quality-loop) · fa and en: the same files
**Output:** The client's output as printed, a short summary, and the exact terminal command for anything only the user may do. No diagnosis note.
**QA:** No setting was turned on, nothing was posted, and the packet was shown unchanged.

