# MCP server fixtures

These files feed `selftest_mcp.py` and let you try the Whalory MCP server by hand. They are test data. The drafts contain mistakes on purpose, and the brand in `project/` is made up.

| File | Used for |
|---|---|
| `session-legacy.jsonl` | A scripted session with the `initialize` handshake (protocol version 2025-11-25) |
| `session-modern.jsonl` | Calls in the 2026-07-28 style: `server/discover`, then `_meta` on every request |
| `draft.fa.txt`, `draft.en.txt` | `lint_file` in Persian and English; both drafts have known errors |
| `brief.txt` | The facts for the English draft (the `facts` argument) |
| `catalog.csv` | `lint_file` on a catalog; issues are keyed `row n/sku/column` |
| `locales/fa.json`, `locales/en.json` | `lint_file` on locale files; keys and placeholders stay as they are |
| `project/` | A project folder with `VOICE.md`, `voice.json` and `LEARNINGS.md` for `profile_lookup` and `detect_context` |

To replay a session, run this from the skill folder:

```bash
python scripts/mcp_server.py --root scripts/samples/mcp < scripts/samples/mcp/session-legacy.jsonl
```

Each output line is one JSON-RPC message. The server stops when the input ends. Responses come back in request order, except `ping`, which is answered as soon as it is read.

## Folders and time limits

The replay passes `--root` on purpose. File tools read only the skill folder and the project folders. The server looks for the project folders in this order and stops at the one that applies:

1. `--root` or `WHALORY_ROOTS`, when at least one value is a folder that exists.
2. The client's workspace folders (MCP `roots/list`), when the client offers them.
3. The folder the server starts in. This applies only when no `--root` or `WHALORY_ROOTS` value was given. It never applies to the top of a drive, the home folder, the Windows folder or the folder Whalory is installed in.

If `--root` or `WHALORY_ROOTS` was given but no value works, the server does not use the folder it starts in. Two cases cause this: a `${...}` placeholder the host left as it is, or a folder that does not exist. File tools then return an error that says how to add a folder. Links and junctions that lead out of these folders are not followed.

`lint_text`, `lint_file` and `compare_texts` run in a child Python process with a time limit of 30 seconds per call. Set another limit with `--time-limit` or `WHALORY_TIME_LIMIT`. A client can stop a call early with `notifications/cancelled`.
