---
name: voice
description: "Build or update a brand voice profile (VOICE.md, voice.json and LEARNINGS.md) in English, Persian or both, from three questions or from existing copy."
argument-hint: "[brand] [samples folder or pasted samples]"
disable-model-invocation: true
---

Input: $ARGUMENTS

Build or update the voice profile for the brand in the input. The method is `references/profile-builder.md` in the `whalory` skill, and the file format is `references/voice-profile.md`.
The skill folder is `${CLAUDE_PLUGIN_ROOT}/skills/whalory/`.

## See what exists

Look for the brand's profile in the order of `SKILL.md#profile-lookup-order`, or call the Whalory MCP tool `profile_lookup` with the brand and the project folder. If a brand profile exists, this is an update. Say what will change before you change it.

## Build the profile

Take one of two routes from `references/profile-builder.md`:

- With samples: route 1, from existing copy (`references/profile-builder.md#route-1-from-existing-copy`).
- Without samples: the quick route of three questions (`references/profile-builder.md#quick-route-three-questions`). An English brand takes the English route (`references/profile-builder.md#english-route`), and a brand that publishes in both languages follows `references/profile-builder.md#bilingual-brands`.

Ask here: three questions at most, in one message, each with a (recommended) option. End with the escape line from `references/intake.md#question-format`. After "write" or «بنویس», use the recommended options.

Draft `VOICE.md` and `voice.json` together, using only the keys in `references/voice-profile.md#the-json-file-key-by-key`. Prepare `LEARNINGS.md` from the learnings template.

## Check

Lint a short benchmark text in the new voice with the new profile. Use the Whalory MCP tool `lint_text` and pass the profile inline as `profile_json`. Fix every profile warning and every error until the benchmark text is clean.

## Save with approval

No file is created until the user says "yes" (`references/profile-builder.md#where-to-save`). Show a five-line summary of the voice and both files, then ask. After a "yes", save `VOICE.md`, `voice.json`, and `LEARNINGS.md` at the project root. A profile kept outside the project goes to `~/.whalory/profiles/` as `<brand>.md`, `<brand>.json`, and `<brand>.LEARNINGS.md`. In a chat without files, the reply carries the text of both files.

If the MCP tools weren't connected for the check, run the linter on the benchmark text once the files are saved:
`${user_config.python} "${CLAUDE_PLUGIN_ROOT}/skills/whalory/scripts/lint.py" --text "…" --profile voice.json`

## Return

The files saved or proposed, the five-line summary, the benchmark text with its lint result, and any open question.

Never change Whalory Hub settings. If the user wants to share statistics, tell them to run `hub_client.py consent` from the `whalory` skill's `scripts/` folder in their own terminal, or `hub_client.py on packets` for the weekly packet.
