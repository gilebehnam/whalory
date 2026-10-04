# Whalory Hub

The Hub keeps Whalory's checks current and lets people who choose to help improve them. This file is for the assistant: what the Hub does, what it never does, and how to run its client for the user. The playbook is [Whalory Hub: rules and feedback](playbooks-strategy.md#whalory-hub-rules-and-feedback).

## Contents

- [What the Hub does](#what-the-hub-does)
- [What never happens](#what-never-happens)
- [The client](#the-client)
- [Status and sync](#status-and-sync)
- [Turning sharing on](#turning-sharing-on)
- [Turning things off](#turning-things-off)
- [The weekly packet](#the-weekly-packet)
- [After the user approves copy](#after-the-user-approves-copy)
- [Without code execution](#without-code-execution)

## What the Hub does

| Part | What it does | Default |
|---|---|---|
| Rule updates | Once a day, the client downloads public rule files that Whalory signed, checks every signature, and applies them to the linters. The request carries no identifier; the servers see the IP address and can tell that Whalory ran that day | On. Off with `WHALORY_HUB_UPDATES=0` or `hub_client.py off updates` |
| Rule statistics | Weekly counts of which Whalory checks fired and how much the user edited drafts, sent to Whalory's server. Offered only to licensed editions, and only after Whalory opens collection | Off |
| Weekly packet | The same kind of counts, kept on this computer. The user may post them under their own GitHub account; the client never sends them | Off |

An install uses statistics or the packet, never both. `WHALORY_HUB=0` turns the whole Hub off: no network, no Hub files, built-in rules only. `DO_NOT_TRACK` or `DISABLE_TELEMETRY` with any non-empty value turns sharing off.

## What never happens

- No text leaves the computer: no draft, sentence, phrase, file name, path, prompt, or licence key. Statistics and packets hold counts keyed by Whalory's own rule ids.
- The assistant never turns sharing on and never changes any other Hub setting. Only a person at a console can turn sharing on. Turning sharing off is the one change anyone may make, the assistant included, when the user asks.
- The client never posts to GitHub and never runs `gh`. Posting a packet is the user's own act.
- Nothing is collected while sharing is off. No hook, tool result, or setting file can turn it on.

## The client

The client is `scripts/hub_client.py` in the skill folder. It runs on Python 3.8 or later; on Windows, use `py -3` when `python` is missing. Show its output as printed. When it prints a command for the user, repeat that command exactly. If a command below gives a usage error, run the client with `--help` and use the matching command it lists. Never guess a command that turns anything on.

| Command | Does | Who runs it |
|---|---|---|
| `status` | Shows rule updates, the active rule set, the last sync, and each sharing setting | The assistant or the user |
| `sync --force` | Downloads and checks the latest signed rules now | The assistant or the user |
| `log` | Shows what the Hub has stored and sent on this computer | The assistant or the user |
| `off`, `off packets`, `off updates`, `off all` | Turns a part off; `off` alone turns statistics off | The assistant or the user |
| `packet --show` | Prints this week's packet and how to post it | The assistant or the user |
| `consent`, `on packets` | Shows the full notice and turns sharing on after a typed code | The user only, in their own terminal |
| `forget` | Deletes the Hub's state on this computer and asks the server to delete sent reports | The user, in their own terminal |

## Status and sync

Run `status` and sum it up in a few lines. Name the active rule set and the time of the last sync. Say whether rule updates are on and whether the rules are out of date. Then give each sharing setting as the client shows it. "Pending" means a plugin setting asked for statistics and no person has confirmed it at a console yet; nothing is collected. Then give the full output.

`sync --force` checks now instead of waiting a day. If rule updates are off, the client says so. Pass that on, and leave the setting as it is.

## Turning sharing on

Never run `consent` or `on`. Tell the user the exact command to run in their own terminal, with the full path of the client and the Python command that worked:

- statistics, for a licensed edition: `python3 <whalory skill folder>/scripts/hub_client.py consent`
- the weekly packet, for any edition: `python3 <whalory skill folder>/scripts/hub_client.py on packets`

Then say what happens. The client shows the full notice and asks for a typed code. "No" is the default. Collection may not be open for this edition yet; then the client says so and changes nothing.

## Turning things off

When the user asks, run the matching `off` command and show the result. `off` also asks Whalory's server to delete the reports it still holds. `off packets` deletes the packets kept on this computer; comments the user already posted stay on GitHub until the user deletes them. Before uninstalling, the user should run `forget` in their own terminal, because uninstalling alone leaves the Hub folder in place.

## The weekly packet

The packet is a JSON block of counts for one week. It carries the Whalory and Python versions, rounded word counts, edit measures, and counts per Whalory rule id. It holds no text, phrase, file name, path, or licence data. A week with very little use gives no packet.

1. Run `packet --show`, with `--lang fa` or `--lang en` for the conversation language. Show the output exactly as printed, the fenced `json` block included. The collector counts only that exact block, so show it unchanged.
2. Say in plain words what the packet holds. If it shows anything besides counts and ids, stop and say so.
3. Explain how to post it. The client prints a link to that week's pinned "Packets" issue. The user pastes the fenced block there, and nothing else, as one comment under their own account. People who use GitHub CLI can save it with `--save <file>` and run the `gh issue comment` line the client printed.
4. Say what posting means: the comment is public, and GitHub's terms apply to it. It counts only from an account at least 90 days old, one packet per account per week. The user can delete it at any time; a comment deleted before the week's final count, 21 days after the week ends, is left out.

When packets are off, the client prints how to turn them on. Pass that command on for the user's own terminal, as in [turning sharing on](#turning-sharing-on).

## After the user approves copy

When the user approves final copy, call the MCP tool `check_final` once on that exact text, if the tool is present. It returns the final lint, like `lint_text`. Only if the user turned on statistics in their own terminal does it also record counts, never text, on this computer. The steps are in the [quality loop](review.md#quality-loop).

## Without code execution

Explain what the user asked about from this file, and give the commands for their own terminal. Never claim that a setting is on or off without the client's own output.
