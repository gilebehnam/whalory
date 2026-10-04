# Whalory Hub: short privacy notice

Version 2026-11-01. This is the short form that Whalory can show you offline. The full notice is at https://whalory.com/legal/#hub-privacy, and where the two differ, the full notice applies. Both are drafts until counsel has reviewed them and the owner has filled in the fields in braces.

## Who runs it

Whalory is made by the Whalya studio. The controller of Whalory Hub is {CONTROLLER_NAME}, Iran. Contact: {PRIVACY_EMAIL}.

## What stays on your computer

Whalory checks your copy on your own computer. Your drafts, final texts, prompts, file names and voice profiles stay there. The linters and the MCP server never connect to the internet.

## Rule updates (on by default)

Once a day at most, Whalory downloads public files with signed rule updates from GitHub and from `hub.whalory.com`. It checks every signature before it uses a file. The request carries no identifier, but like any download, those servers see your IP address and can tell that Whalory was used that day. Turn it off with `hub_client.py off updates` or `WHALORY_HUB_UPDATES=0`.

## Weekly statistics (off unless you turn them on)

Only paid editions are asked, and only after an announcement in a signed update. Only you can turn statistics on, in your own terminal, by answering Yes and typing a short code. A plugin setting can only ask; your AI assistant cannot turn them on.

When they are on, Whalory sends one small report a week to its server in Iran. The report says which checks fired and how many words were checked, rounded. It also counts your edits to drafts and the revisions you asked for, and names the versions in use. Your text, file names, prompts and name are never in it. To measure its checks fairly, Whalory hides about 1 in 10 of them from you each week and counts whether you changed that wording yourself.

A paid edition proves once a week that it holds a licence. It sends a one-time code made from the licence key, never the key. The shop signs your weekly ticket without seeing it, so our records cannot link the ticket to your report.

## Phrase sharing (a second choice, off by default)

With weekly statistics on, you may also share which entries of a fixed public list of common phrases you deleted. Only list numbers are sent, at most 20 a week. Nothing outside the list is ever sent.

## Weekly packets you post yourself (off by default)

Any edition can keep the same kind of counts on your computer instead. Each week `hub_client.py packet` shows you the packet in full, with a link to that week's public issue on GitHub. Whalory sends nothing. If you want, you post the packet yourself as a comment under your own GitHub account. Anyone can read it, and you can delete it at any time. An installation uses statistics or packets, never both.

## Storage and deletion

Reports are stored in Iran and deleted within 22 days after the week ends. Only totals that cover at least 10 people are kept, with a little random noise added. Our code stores no IP address. Our hosting provider may keep network records for {HOST_LOG_PERIOD}, as Iranian law may require. Do not turn on statistics if you are in the United States or are a U.S. citizen or permanent resident.

## Your choices

- `hub_client.py off` turns statistics and phrase sharing off and asks our server to delete your reports.
- `hub_client.py off packets` turns packets off and deletes them from your computer. Comments you posted stay until you delete them on GitHub.
- `hub_client.py forget` deletes the Hub folder's data and asks for the deletion of every report still held. Run it before you uninstall Whalory.
- `hub_client.py log --sent` shows every report exactly as it was sent.

Saying No changes nothing in how Whalory works. Statistics and packets are only for people aged 18 or older.
