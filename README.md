# Whalory, directory edition

Whalory («والوری») gives Claude a professional writer's method for English and Persian (Farsi) business copy. Before writing, it works out the task, the channel and the output language. It asks at most three short questions, and only when an answer would change the text. It keeps to the facts you supply and marks each gap with a bracket, such as `[confirm: price]`. A blind editor then reviews the draft. Persian version: [README.fa.md](README.fa.md).

This edition is text only. It holds Markdown, JSON and images, and runs nothing on your computer: no scripts, no MCP server, no hooks and no network calls. Every check is done by reading, with the checklists in the skill. The full Whalory Core adds Persian and English linters that run locally, and it is free at [github.com/gilebehnam/whalory](https://github.com/gilebehnam/whalory).

## What is inside

| Part | What it does |
|---|---|
| `skills/whalory` | The method: context card, question gate, playbooks for ads, social posts, email, SMS, web and UX copy, product listings, reviews and transcreation, plus voice profiles and craft references in both languages |
| `references/fa/plain-persian.md`, `references/en/plain-english.md` | Plain-language guides: what to ask for before writing, a replacement table for officialese and machine patterns, the read-aloud test, and a compact brief you can paste into any assistant |
| `/whalory:write` | Writes or rewrites copy; a writer drafts and a blind editor reviews |
| `/whalory:review` | Blind review: a score out of 20, must-fix items and up to three line edits |
| `/whalory:lint` | Checks text against the manual checklists and lists issues by rule |
| `/whalory:voice` | Builds or updates a brand voice profile (VOICE.md, voice.json, LEARNINGS.md) |
| `/whalory:learn`, `/whalory:lessons` | Keeps a correction as a lesson for next time, after you approve it |
| `whalory-writer`, `whalory-editor` agents | The writer and the blind reviewer the commands use |

## Files it writes

Whalory writes only when you ask, and it shows the change first. `/whalory:voice` and `/whalory:learn` save the voice profile and lessons in your project folder after you say yes. Nothing is sent anywhere.

## Privacy

The plugin collects nothing. Your prompts and files go to Claude under Anthropic's terms, as with any conversation. Website privacy notice: [whalory.com/privacy](https://whalory.com/privacy/).

## License and support

Text under CC BY 4.0; see [LICENSE.en.md](LICENSE.en.md). Support: [whalory.com/support](https://whalory.com/support/). Guide for Claude Code: [whalory.com/guides/claude-code](https://whalory.com/guides/claude-code/).
