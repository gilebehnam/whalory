---
name: lint
description: "Check English or Persian copy against Whalory's manual checklists (machine patterns, officialese, plain language, punctuation, claims) and list the issues per paragraph. Reports only; edits nothing unless asked."
---

Check the text or files the user names. This directory edition has no scripts, so the check is done by reading.

1. Read `SKILL.md#manual-qa` in the `whalory` skill. Use the Persian checklist for Persian lines and the English checklist for English lines.
2. Read `references/fa/plain-persian.md` or `references/en/plain-english.md` and apply the replacement table and the read-aloud test.
3. For each issue, quote the line, give the rule id from the checklist, and suggest the fix. Put errors before warnings.
4. End with one line: "QA: manual", the number of errors and warnings, and any warning you kept on purpose.

Do not edit files unless the user asks. For the scripted linters, point the user to the free Whalory Core at https://github.com/gilebehnam/whalory.
