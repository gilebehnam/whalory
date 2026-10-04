# Whalory Hub data

> **WARNING: `root.json` is the public test root.** It is `root/1.json` of the contract mirror (`STUDIO/hub/contracts/mirror/v1/`), signed with the public test keys of `STUDIO/hub/contracts/fixtures/test-keys/`. Those keys are public, so anyone can sign files that this root accepts. Until the owner's root key ceremony replaces this file:
>
> - `hub_client.py` never syncs outside `--test`, and every lane stays closed, whatever a signed file says;
> - `hub_client.py pinned-root --require-production` exits with code 5;
> - a release build must refuse this file unless it is run with `--allow-test-root`.

| File | What it is | Spec |
|---|---|---|
| `root.json` | The pinned initial root, a signed envelope in the format of spec 7.2. Replace it with the production root after the key ceremony, and delete the warning above | 5.1, 7.3 |
| `consent.json` | The versioned consent wording (version `2026-11-01`), copied from the spec. The owner fills `{CONTROLLER_NAME}` and `{HOST_LOG_PERIOD}` before collection opens; the client refuses to show a screen that still has an unfilled placeholder | 4.4, 4.10 |
| `notice.en.md`, `notice.fa.md` | Short privacy notices the client can show offline; the full notices on the website prevail | 4.11 |
| `report.schema.json`, `packet.schema.json` | Self-contained copies of the `whalory.report/2` and `whalory.packet/1` contracts, for tests (`STUDIO/hub/contracts/tools/bundle_schema.py`) | 5.5, 17.3.2 |
| `bundled/` | The stable baseline and auto overlays with their metadata, in the mirror layout of spec 8.2, copied in at release time. Empty while only the test root exists, so the linters use their built-in rules | 8.1 |

The Tier 2 lists (`vocab`, `stop`, `sensitive` and `ngrams`, one per language) come from the list build of the pipeline and ship through an owner release. Without them, phrase sharing records nothing.
