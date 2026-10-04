# Bundled overlay

At release time this folder holds the latest stable baseline and auto overlays and their signed metadata. The layout is the mirror layout of spec 8.2: `timestamp.json`, `baseline.json`, `auto.json`, `halt.json` when present, and `targets/<sha256>.json`. `hub_overlay` verifies them from the pinned `../root.json` and uses them when nothing newer is trusted in the Hub folder.

It stays empty while `../root.json` is the public test root. A set signed with public test keys proves nothing, so the linters run with their built-in rules.
