# Whalory Autolint

Whalory Core 3.2.1. An opt-in companion to the Whalory plugin for Claude Code.

After Claude writes or edits a content file or a locale file, this plugin runs the Whalory
linters on that file and passes the top issues back to Claude as context, so the next edit
can fix them. It never blocks a tool call and never changes a file.

## Install

    claude plugin install whalory-autolint@whalory

## What it checks

Markdown, MDX, text, HTML, CSV and TSV files, and locale files (`.json`, `.po`, `.arb`,
`.xliff`, `.strings` and `.xml`) whose path or name looks like a locale. Persian and English
are detected line by line. Files over 1 MB and folders such as `node_modules`, `.git`, `dist`, `build` and
`vendor` are skipped.

## Turn it off or up

- `WHALORY_AUTOLINT=0` turns it off without uninstalling it.
- `WHALORY_AUTOLINT=strict` reports warnings as well as errors.
- `WHALYA_AUTOLINT`, the name from before the rename to Whalory, still works but is deprecated.

## Requirements

Python 3.8 or newer, run as `python3`. On Windows, check that `python3` starts a real Python
and not the Microsoft Store alias. The scripts use the Python standard library only and make
no network calls.

## License

The scripts are MIT-licensed and this text is under Creative Commons Attribution 4.0.
See `LICENSE.md`.
