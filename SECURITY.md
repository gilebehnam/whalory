# Security policy

## Report a vulnerability privately

Please use GitHub's private reporting form for this repository: [Report a vulnerability](https://github.com/gilebehnam/whalory/security/advisories/new). Only you and the maintainers can read the report. Please don't open a public issue, pull request, or discussion about an unfixed vulnerability.

A useful report includes:

- the Whalory version (`python skills/whalory/scripts/lint.py --version`) and the package you installed;
- your host, its version, and your operating system;
- the steps or a minimal input that shows the problem;
- what an attacker could do with it, as far as you can tell.

Please test only on your own machine and your own files. Don't include real client copy or anyone's personal data.

## Supported versions

| Version | Supported |
|---|---|
| 3.1.x | Yes |
| 3.0.x and earlier | No; they were never released publicly |

## What is in scope

- Linters: `lint.py`, `lint_fa.py`, `lint_en.py`, and `textcount.py`. Think of a crafted input that makes a check run for minutes. A crash that stops the autolint hook counts too, and so does `--fix` touching a file you did not name.
- MCP server: `mcp_server.py` promises that it opens no sockets, and that file tools read only inside the allowed folders. It writes no files, apart from Hub counts while you have statistics or packets on. A way around any of these is in scope, including links or junctions that lead outside those folders.
- Hub client: `hub_client.py`, `hub_verify.py`, and `hub_overlay.py` promise three things. No rule file is used before its signatures and limits check out. Nothing is shared unless a person turned sharing on at a console. No text leaves your machine. A way around any of these is in scope, and so is a crafted file that crashes the client or stalls the linters.
- Autolint hook: `hook_lint.py`, for example a file name that makes it run something other than the linter.
- Plugin manifests and skill text, if they could lead an assistant to do something unsafe on your machine.
- Release archives and the `SHA256SUMS` file attached to a GitHub release.

The same form also works for the Whalory website.

## Out of scope

- Problems in the assistants that load Whalory, such as Claude Code, Codex, Cursor, Copilot, or Gemini CLI. Please report those to their makers.
- A model ignoring Whalory's instructions and writing weak or inaccurate copy. That is a quality problem, so please open a normal issue.
- Findings that need an attacker who already controls your machine or your user account.

## What happens next

A maintainer confirms that the report arrived, reproduces it, and works on a fix in a private advisory. The fix ships in a release, and the advisory is published with it. The advisory credits you, unless you ask us not to. No response time is promised yet, and there is no bug bounty.
