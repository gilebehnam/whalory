---
name: feedback
description: "Show this week's Whalory feedback packet: counts of which checks fired and how much drafts were edited, never your text. Explains what it holds and how you can post it yourself under that week's public GitHub issue. Nothing is sent."
argument-hint: "[--week YYYY-Www]"
disable-model-invocation: true
---

Arguments: $ARGUMENTS

Show the user this week's Whalory packet and explain it. The packet is a small block of counts about Whalory's own checks. People who choose to can post it under their own GitHub account, which helps improve the checks for everyone. Whalory never sends it. Its method is `references/hub.md#the-weekly-packet` in the `whalory` skill.
The skill folder is `${CLAUDE_PLUGIN_ROOT}/skills/whalory/`.

## Show the packet

Run the Hub client with Python 3.8 or newer. Add `--lang fa` in a Persian conversation and `--lang en` in an English one, plus the `--week` argument if the user gave one.
`${user_config.python} "${CLAUDE_PLUGIN_ROOT}/skills/whalory/scripts/hub_client.py" packet --show --lang <fa|en>`
If that Python command isn't found, try `python3`, then `python`, then `py -3` on Windows. If the client answers with a usage error, run it with `--help` and use the packet command it lists. Never guess a command that turns anything on.

Show the output exactly as printed, the fenced `json` block included. Don't reformat, translate, shorten, or summarize anything inside the block, because the collector counts only that exact block.

## Say what it holds

Then explain, in the language of this conversation, what each part of the packet holds:

| Key | What it holds |
|---|---|
| `schema`, `epoch` | The packet format and the week, such as `2026-W40` |
| `consent` | The version of the notice the user accepted, and the option `packets` |
| `client` | The Whalory version (major and minor only), a range of Python versions, and the ids of the active signed rule sets |
| `volume` | Per language and format group: words checked and words in the approved text, rounded down to a multiple of 50 |
| `cells` | Per Whalory rule id: how often it fired (`hits`) and how often a flagged pattern stayed in the approved text (`kept`). For the checks hidden that week, how often they found something (`ho`) and how often the user's own edit removed it (`hg`) |
| `placebo` | Counts for random word pairs, a baseline for the hidden checks |
| `params` | Counts per step of a tunable limit, such as the sentence-length cap |
| `playbooks` | Per playbook id: approved texts, first drafts with no revision, the summed edit ratio, revision requests, and errors left at approval. The last field, `explored`, counts trial runs of a playbook variant and stays at 0 until Whalory ships one |
| `health` | Counters for self-tests, rule syncs, and rule files that were rejected or failed a check |

The packet holds no text, sentence, phrase, file name, path, prompt, or licence data. If the block shows anything besides counts, versions, and ids, stop. Say so, and tell the user not to post it.

If the client says the week has no packet, pass that on. A week with very little use gives none.

## How the user can post it

1. Open the link the client printed. It leads to that week's pinned "Packets" issue in Whalory's public GitHub repository.
2. Paste the fenced block, and nothing else, as one comment under your own GitHub account.
3. GitHub CLI users can add `--save <file>` to the command above, then run the `gh issue comment` line that the client printed, in their own terminal.

Then say what posting means. The comment is public, and GitHub's terms apply to it. It counts only from an account at least 90 days old, one packet per account per week. The user can delete it at any time; a comment deleted before the week's final count, 21 days after the week ends, is left out.

Never post the packet, never run `gh`, and never open the issue for the user.

## When packets are off

The client then prints how to turn them on. Pass that command on for the user's own terminal:
`${user_config.python} "${CLAUDE_PLUGIN_ROOT}/skills/whalory/scripts/hub_client.py" on packets`
Never run it yourself. Say what happens next: the client shows the full notice and asks for a short code that the user types. "No" is the default. If this option isn't open yet, the client says so and changes nothing.

## Without code execution

Explain the packet from `references/hub.md`, and give the commands above for the user's own terminal. Never claim a setting is on or off without the client's own output.

Never change Whalory Hub settings. If the user wants to share statistics, tell them to run `hub_client.py consent` from the `whalory` skill's `scripts/` folder in their own terminal, or `hub_client.py on packets` for the weekly packet.
