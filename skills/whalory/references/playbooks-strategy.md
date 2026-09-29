# Playbooks: voice, strategy, and teaching

This file is part of the [playbooks](playbooks.md). Each task's row is in the [task index](playbooks.md#task-index), and every playbook here assumes the [shared steps](playbooks.md#shared-steps). The "Questions" line of a playbook only names its row in the question bank; the [question gate](intake.md#decision-order) decides whether to ask. The "References" line lists the Persian craft files after "fa:" and the English ones after "en:". Read the list for the output language. The quality assurance (QA) line gives the checks and the `--format` id.

## Contents

- [Voice, strategy, and teaching](#voice-strategy-and-teaching)
  - [Voice profile in three questions](#voice-profile-in-three-questions)

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

