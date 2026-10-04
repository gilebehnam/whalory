---
name: lint
description: "Check copy, Markdown, HTML, CSV or locale files with Whalory's Persian and English linters and summarize the issues per file. Reports only; edits nothing unless asked."
argument-hint: "[paths…] [--format id] [--channel id]"
disable-model-invocation: true
allowed-tools: Read Bash(python3 *) Bash(python *) mcp__plugin_whalory_whalory__lint_file mcp__plugin_whalory_whalory__lint_text
---

Arguments: $ARGUMENTS

Check the named files, or the pasted text, with Whalory's bilingual linter. It detects the language per file and per line, so Persian, English, and mixed files all work. This command reports; it doesn't edit.

## Run the linter

When the Whalory MCP tools are connected, call `lint_file` for each path and `lint_text` for pasted text. Pass `format` and `channel` when the arguments give them, and `profile: auto`.

Otherwise, run the dispatcher with Python 3.8 or newer:
`${user_config.python} "${CLAUDE_PLUGIN_ROOT}/skills/whalory/scripts/lint.py" $ARGUMENTS --json`
If that Python command isn't found, try `python3`, then `python`, then `py -3` on Windows.

If neither route works, say so and check the text by hand against `SKILL.md#manual-qa` in the `whalory` skill. Write the quality assurance (QA) line as "QA: manual (script not run)".

Exit codes: `0` means no errors; `1` means at least one error, or a warning under `--strict`; `2` means a problem with the input or the profile.

## Summarize per file

Start each file with its language (fa, en, or mixed) and its counts of errors and warnings. List each error with its rule id, its line (or key, in a locale file), and its message. Group the warnings by rule. End with the totals.

In locale files, only values are linted. Never suggest changing a key, a placeholder such as `{name}` or `%s`, or a plural or select structure.

## Don't edit

Change no file unless the user asks. For mechanical fixes on request, `--fix` writes a copy named `<name>.fixed.<ext>`, and `--fix --write` changes the file in place. Show what changed.

Never change Whalory Hub settings. If the user wants to share statistics, tell them to run `hub_client.py consent` from the `whalory` skill's `scripts/` folder in their own terminal, or `hub_client.py on packets` for the weekly packet.
