---
name: hub
description: "Whalory Hub: see the status of the signed rule updates and your sharing settings, sync the rules now, or turn sharing or updates off. Only you can turn sharing on, in your own terminal; this command gives you the exact line."
argument-hint: "[status | sync | log | off [stats|packets|updates|all] | on]"
disable-model-invocation: true
---

Arguments: $ARGUMENTS

Run the Whalory Hub client for the user and explain what it says. The Hub keeps Whalory's checks current with signed rule updates. It also offers two ways to share counts, never text, and both stay off unless the user turns one on. Its method is in `references/hub.md` in the `whalory` skill.
The skill folder is `${CLAUDE_PLUGIN_ROOT}/skills/whalory/`.

With no argument, show the status.

## Run the client

Every action below runs the client with Python 3.8 or newer:
`${user_config.python} "${CLAUDE_PLUGIN_ROOT}/skills/whalory/scripts/hub_client.py" <command>`
If that Python command isn't found, try `python3`, then `python`, then `py -3` on Windows. Show the client's output as printed. If it answers with a usage error, run it with `--help` and use the matching command it lists. Never guess a command that turns anything on.

## Status

Run `status`. Sum it up in a few lines first:

1. the active rule set and the time of the last sync;
2. whether rule updates are on, and whether the rules are out of date;
3. each sharing option as the client shows it: rule statistics and the weekly packet.

"Pending" means a plugin setting asked for statistics and no person has confirmed it at a console yet. Nothing is collected while it is pending. Then give the full output.

## Sync

Run `sync --force` to download and check the latest signed rules now instead of waiting a day. The download carries no identifier, but like any download, the servers see the computer's address. If rule updates are off, the client says so. Pass that on and leave the setting as it is.

## Log

Run `log` to show what the Hub has stored and sent on this computer. Show it as printed.

## Off

When the user asks, run the matching command and show its result:

- `off` turns rule statistics off and asks Whalory's server to delete the reports it still holds;
- `off packets` turns the weekly packet off and deletes the packets kept on this computer. Comments the user already posted stay on GitHub until the user deletes them;
- `off updates` stops the daily rule updates; the linters keep the rules they have;
- `off all` turns everything off.

Turning a part off is the one change to Whalory Hub settings that you may make, and only at the user's request.

## On

Never run `consent` or `on`, not even when the user asks you to. Only a person at a console can turn sharing on. Give the user the exact line for their own terminal, with the full path of the client:

- rule statistics, offered only to licensed editions:
  `${user_config.python} "${CLAUDE_PLUGIN_ROOT}/skills/whalory/scripts/hub_client.py" consent`
- the weekly packet, for any edition: the same line, ending in `on packets` instead of `consent`.

Then say what happens. The client shows the full notice and asks for a short code that the user types. "No" is the default. An install uses statistics or the packet, never both. If sharing isn't open for this edition yet, the client says so and changes nothing. To see or post a packet, the user runs the `feedback` command.

## Before uninstalling

Tell the user to run `forget` in their own terminal. Uninstalling alone leaves the Hub folder in place.

## Without code execution

Explain from `references/hub.md`, and give the commands above for the user's own terminal. Never claim a setting is on or off without the client's own output.

Never turn on or change any other Whalory Hub setting. If the user wants to share statistics, give them the `consent` line above to run in their own terminal, or the `on packets` line for the weekly packet.
