# How to install

> Release status: 3.2.0-rc.1 is an unpublished local candidate. Public 3.0.0 is the verified release; 3.1.0 is an unpublished development precursor. Candidate artifact names below refer to local build outputs, not newly published download URLs.

Each section below uses a package from the [latest release](https://github.com/gilebehnam/whalory/releases/latest) or this repository. The steps were checked against each host's documentation on 27 or 28 September 2026. The latest test record comes at the end of each section, and so far every test ran on the 3.0.0 build. We call a route tested only after a dated test.

Persian readers: the Persian guide is [GUIDE.fa.md](../skills/whalory/GUIDE.fa.md), and the website has the same steps on its [Persian download page](https://whalory.com/fa/download/).

## Contents

- [Before you start](#before-you-start)
- [Claude Code](#claude-code)
- [Claude Desktop](#claude-desktop)
- [claude.ai](#claudeai)
- [Codex](#codex)
- [Cursor](#cursor)
- [VS Code with GitHub Copilot](#vs-code-with-github-copilot)
- [Gemini CLI](#gemini-cli)
- [Other Agent Skills hosts](#other-agent-skills-hosts)
- [Any chat, by pasting](#any-chat-by-pasting)
- [Check that it works](#check-that-it-works)
- [Update or remove](#update-or-remove)

## Before you start

### The release files

| File | What it is |
|---|---|
| `whalory-core-3.2.0-rc.1-skill.zip` | The skill folder, for any host that reads Agent Skills |
| `whalory-core-3.2.0-rc.1-claudeai.zip` | The same skill, shaped for the claude.ai and Claude Desktop upload |
| `whalory-core-mcp-3.2.0-rc.1.mcpb` | The MCP tools as a Claude Desktop extension |
| `whalory-core-3.2.0-rc.1-agent-plugin.zip` | The Agent Plugins package, for Codex and for Copilot in Visual Studio Code (VS Code) |
| `whalory-core-3.2.0-rc.1-paste.zip` | Paste-in prompts in English and Persian |
| `SHA256SUMS` | The checksum of each file above |

This repository itself is the Claude Code plugin, and the skill folder sits at `skills/whalory/`.

### Verify a download

Put `SHA256SUMS` in the folder with the files you downloaded, then check them. `--ignore-missing` skips the files you didn't download:

```bash
sha256sum -c SHA256SUMS --ignore-missing            # Linux
shasum -a 256 -c SHA256SUMS --ignore-missing        # macOS
```

On Windows, print the checksum and compare it with the line for that file in `SHA256SUMS`:

```powershell
Get-FileHash whalory-core-3.2.0-rc.1-skill.zip -Algorithm SHA256
```

### Python

Whalory works without Python. It then checks drafts against a manual checklist, and the quality assurance (QA) line of its note says "QA: manual". The linters, the MCP server, and the autolint hook need Python 3.8 or later, with the standard library only.

- On macOS and Linux, every package starts the tools with `python3`.
- On Windows, which of `python3`, `python`, and `py` answers depends on how Python was installed. The Python install manager from python.org adds all three. Check with `python3 --version`.

## Claude Code

This repository is its own one-plugin marketplace. From a terminal:

```bash
claude plugin marketplace add gilebehnam/whalory
claude plugin install whalory@whalory
```

Inside Claude Code, the same steps are `/plugin marketplace add gilebehnam/whalory` and then `/plugin install whalory@whalory`.

- On Windows, install with `claude plugin install whalory@whalory --config python=python`, so the tools and the Hub client use the right Python command. That needs Claude Code 2.1.147 or later. You can change it later with `/plugin configure whalory`.
- The plugin brings the skill, eight commands, the writer and editor agents, and the MCP tools. The commands are `write`, `review`, `voice`, `lint`, `learn`, `lessons`, `hub`, and `feedback`, called as `/whalory:write` and so on.
- When a session starts, the plugin runs the Hub client in the background for the daily rule update. It prints nothing, and [PRIVACY.md](../PRIVACY.md) says how to turn it off.
- The lint-on-save hook is a separate, opt-in plugin: `claude plugin install whalory-autolint@whalory`. It checks content and locale files after each edit and never blocks one. It runs `python3`.

To use the skill alone, without the plugin, copy `skills/whalory` from this repository into `~/.claude/skills/` and call it with `/whalory`.

Test record: during packaging, Claude Code 2.1.278 loaded the plugin with `--plugin-dir` and listed its MCP server as connected. The marketplace install had not been run when 3.0.0 was built. Guide: [Claude Code on the website](https://whalory.com/guides/claude-code/).

## Claude Desktop

1. Download `whalory-core-mcp-3.2.0-rc.1.mcpb` from the verified local candidate kit.
2. Double-click it, drag it into the Claude Desktop window, or open Settings > Extensions > Advanced settings > Install Extension.
3. Choose the folders Whalory may read. The file tools read only inside them.

The bundle adds the tools only, and needs Python 3.8 or later, which Claude Desktop does not include. It runs `python` on Windows and `python3` elsewhere. For the method itself, also upload the skill as described under [claude.ai](#claudeai).

Test record: no end-to-end test recorded.

## claude.ai

1. Turn on code execution in your settings. Skills need it.
2. Open Customize > Skills and upload `whalory-core-3.2.0-rc.1-claudeai.zip`.

Use the `-claudeai.zip`, not the plain skill zip: its description fits claude.ai's 200-character limit, and its root is the skill folder. The scripts can run only in Claude's code execution sandbox. Keep your voice profile in a Claude project, or paste `VOICE.md` into the chat.

Test record: not yet tested with a real upload.

## Codex

The simplest route is the skill folder:

1. Copy `skills/whalory` into `~/.agents/skills/`, or into `.agents/skills/` in a repository.
2. Call it with `$whalory`, or pick it from `/skills`.

To add the MCP tools, put this in `~/.codex/config.toml`, with the path to your copy:

```toml
[mcp_servers.whalory]
command = "python3"
args = ["<path-to-whalory>/scripts/mcp_server.py", "--root", "."]
default_tools_approval_mode = "auto"
```

For the commands as well, use the Agent Plugins package, `whalory-core-3.2.0-rc.1-agent-plugin.zip`. Its `INSTALL.md` shows how to add it to a Codex marketplace; then restart Codex and install Whalory from `/plugins`. Plugins work in the ChatGPT desktop app and the Codex CLI, but not in the Codex IDE extension.

Don't load this repository as a Codex plugin. Codex loads its skills, but in our test its MCP server did not start, because Codex does not expand the Claude plugin's settings.

Test record: codex-cli 0.145.0 loaded the skills. The Agent Plugins server started only from the legacy `.mcp.json`, and Codex shared no project folder with it, so only `lint_text` worked from the plugin. Guide: [Codex on the website](https://whalory.com/guides/codex/).

## Cursor

1. Copy `skills/whalory` into `.cursor/skills/` or `.agents/skills/` in your project, or into the same folders under your home folder.
2. Type `/` in Agent chat to call it.

To add the tools, put this in `.cursor/mcp.json`:

```json
{"mcpServers": {"whalory": {"command": "python3",
  "args": ["<path-to-whalory>/scripts/mcp_server.py", "--root", "${workspaceFolder}"]}}}
```

The Agent Plugins package is not a route for the tools in Cursor, because Cursor does not expand `${PLUGIN_ROOT}` in its `mcp.json`. Whalory Pro ships a Cursor plugin.

Test record: no end-to-end test recorded. Guide: [Cursor on the website](https://whalory.com/guides/cursor/).

## VS Code with GitHub Copilot

With the Agent Plugins package:

1. Unzip `whalory-core-3.2.0-rc.1-agent-plugin.zip`.
2. Add its `whalory` folder to the `chat.pluginLocations` setting, with the value `true`.

The package's MCP server runs `python3`. With the skill folder alone, copy `skills/whalory` into `.github/skills/` in a repository, or into `~/.copilot/skills/`. To add the tools by hand, put this in `.vscode/mcp.json`:

```json
{"servers": {"whalory": {"type": "stdio", "command": "python3",
  "args": ["<path-to-whalory>/scripts/mcp_server.py", "--root", "${workspaceFolder}"]}}}
```

VS Code can also load this repository through Chat: Install Plugin From Source. That route brings the skill and the commands, but probably not the tools, because the plugin starts its server with a Claude Code setting.

Test record: neither plugin route had been tested in VS Code when 3.0.0 was built. Guide: [VS Code with GitHub Copilot on the website](https://whalory.com/guides/vscode-copilot/).

## Gemini CLI

Gemini CLI uses the skill folder:

1. Unzip `whalory-core-3.2.0-rc.1-skill.zip`, or copy `skills/whalory` from this repository.
2. Put the `whalory` folder in `~/.gemini/skills/` or `~/.agents/skills/` for your user, or in `.gemini/skills/` or `.agents/skills/` in a project.
3. Start Gemini CLI and describe the task. When Gemini asks to activate the `whalory` skill, confirm.

The skill reviews each draft in a separate pass of the same model. A Gemini CLI extension is built for 3.2.0-rc.1, with the commands and the writer and editor agents. Its repository is not published yet. When it is, its install command will appear here and in the changelog.

Test record: no end-to-end test recorded. Guide: [Gemini CLI on the website](https://whalory.com/guides/gemini-cli/).

## Other Agent Skills hosts

Hosts that read Agent Skills from `.agents/skills/` can load the same folder: copy `skills/whalory` there. To add the tools, point the host at `scripts/mcp_server.py` as a stdio server, with `--root` set to your project folder. Paths differ by host, and we have not verified them all.

## Any chat, by pasting

For ChatGPT, the Gemini app, or any assistant with a custom instructions field:

1. Unzip `whalory-core-3.2.0-rc.1-paste.zip`.
2. Pick the file that fits your assistant's limit: `en/paste-1500.txt` or `en/paste-4000.txt`, or the same sizes in `fa/` for Persian.
3. Paste all of it into the custom instructions, or at the start of the chat.
4. If you have a voice profile, paste it into the same chat.

A pasted prompt carries a summary of the method. It brings no local tools, no memory, no separate agents, and no updates, so its note says "QA: manual".

## Check that it works

Ask your assistant:

```text
Write a caption introducing [product].
```

You should get one to three short questions, each with a recommended option, or the caption with a note that starts with "Diagnosis:". Unknown facts stay in brackets.

To check the scripts on their own, run the self-tests from the skill folder:

```bash
python skills/whalory/scripts/selftest.py
```

## Update or remove

Whalory's files never update themselves. Only its rules do: the plugins download signed rule files once a day, unless you turn that off ([PRIVACY.md](../PRIVACY.md)).

- Claude Code: `claude plugin update whalory@whalory`, or turn on auto-update for this marketplace in `/plugin`.
- A skill folder: replace the `whalory` folder with the new version. Keep your own profiles outside it, as `VOICE.md` in your project or in `~/.whalory/profiles/`, and an update never touches them.

To remove Whalory, first run `python skills/whalory/scripts/hub_client.py forget` in your own terminal. It turns sharing off and clears the Hub's data. Then uninstall the plugin, or delete the `whalory` folder. The Hub folder named in [PRIVACY.md](../PRIVACY.md) is the only thing left behind, and you can delete it too.
