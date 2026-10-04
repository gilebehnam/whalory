# Privacy and network activity

> Release status: 3.2.0-rc.1 is an unpublished local candidate. Public 3.0.0 is the verified release; 3.1.0 is an unpublished development precursor. Candidate artifact names below refer to local build outputs, not newly published download URLs.

This page describes what Whalory Core 3.2.0-rc.1 does with your text and your network. The privacy notice for purchases on the website is separate: [the website's privacy notice](https://whalory.com/legal/#privacy). The Hub has its own notice: [the Hub privacy notice](https://whalory.com/legal/#hub-privacy).

## What stays on your machine

- The linters, the MCP server, and the autolint hook run on your machine. They make no network calls and send nothing anywhere.
- No text leaves your machine through Whalory: no draft, sentence, phrase, file name, path, prompt, or license key.
- It writes your files only when you ask. `lint.py --fix` saves a fixed copy next to the original, and `--fix --write` changes the file in place. The scripts leave no Python bytecode cache next to themselves.
- The MCP server writes no files, apart from the Hub counts described below. Its file tools read only inside the folders you give it with `--root` or `WHALORY_ROOTS`, or the folders your host shares with it.
- The autolint hook reads the file the assistant just wrote and prints its findings back to the assistant.
- The skill is text. Your assistant reads it the way it reads any instructions.

## What your assistant does

Whalory runs inside an assistant such as Claude, Codex, Cursor, Copilot, or Gemini. That assistant sends your prompts and files to its model provider under its own terms. Whalory changes nothing about that, and adds no service of its own to the path.

## The Hub

The Hub keeps Whalory's rules current between releases. Its client, `skills/whalory/scripts/hub_client.py`, is the only part of Whalory that uses the network. The Claude Code plugin, the Agent Plugins package, and the Gemini CLI extension start it in the background when a session starts. It then does at most one task, and prints nothing. With a plain skill folder, the client runs only when you start it.

### Rule updates, on by default

- At most once a day, the client downloads rule files that Whalory signed. It tries the GitHub Pages site of the [whalory-hub](https://github.com/gilebehnam/whalory-hub) repository, `hub.whalory.com` in Iran, and that repository's GitHub releases. It starts with the one that answered last time.
- No identifier goes with the request. Like any web server, a mirror sees your IP address and can tell that Whalory ran that day.
- Only data arrives. A file can move a rule's severity, set a threshold inside limits that Whalory signed offline, or add a literal phrase, and nothing else. The client checks every signature and every limit before the linters use a file. It refuses a file that fails, and keeps the rules it already has.
- `python skills/whalory/scripts/hub_client.py off updates` turns updates off, and so does `WHALORY_HUB_UPDATES=0`. In Claude Code, the plugin setting "Download signed rule updates" does the same.

### Statistics and the weekly packet, off by default

- Both are off. No choice is pre-ticked. They also stay closed until Whalory opens them with a signed setting, after a legal review of their notices. Until then, the client says so and changes nothing.
- Only a person at a console can turn one on. No assistant, plugin setting, project file, or employer policy can do it. The console shows the full notice and asks you to type a short code.
- Statistics need a paid license, so Whalory Core never sends them. They are weekly counts about Whalory's own rules, such as how often a rule fired and whether you kept the wording.
- The weekly packet is for any edition. It holds the same kind of counts and stays on your computer, because the client never sends it. If you choose to, you post it yourself as a comment on that week's issue in whalory-hub, under your own GitHub account. The comment is public and tied to your account. The counting job hides counted comments, but anyone can still open a hidden comment, so delete yours if you want it gone.
- Neither holds text you wrote, file names, paths, or license data.
- Anyone, including an assistant, can turn sharing off, and turning it off works offline: `hub_client.py off`, `off packets`, or `off all`.

### What the Hub keeps on your computer

- The Hub folder holds the verified rule files, the client's settings and state, and a log. It is `%LOCALAPPDATA%\Whalory\hub\` on Windows, `~/Library/Application Support/Whalory/hub/` on macOS, and `~/.local/state/whalory/hub/` on Linux.
- `hub_client.py status` shows what is on, and `hub_client.py log --net` lists every network request the client made.
- Uninstalling Whalory leaves the Hub folder in place. Run `hub_client.py forget` in your own terminal first. It turns sharing off and clears the Hub's data, and then you can delete the folder.

### Switches

| Switch | Effect |
|---|---|
| `WHALORY_HUB=0` | Turns the whole Hub off: no network, no Hub files, built-in rules only |
| `WHALORY_HUB_UPDATES=0` | Stops the rule updates |
| `WHALORY_HUB_OVERLAY=0`, or `lint.py --no-overlay` | The linters use their built-in rules only |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, set to any value | Stops all Hub network activity |
| `DO_NOT_TRACK` or `DISABLE_TELEMETRY`, set to any value | Keeps statistics and packets off |

## Issues and pull requests

Anything you post in this repository is public, and GitHub's privacy statement applies to it. Leave out client copy you may not share, personal data, and license keys.

## Questions

Open an issue for a question about this page. If the question involves something private, use the private reporting form described in [SECURITY.md](SECURITY.md).
