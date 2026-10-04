# Licenses

This file says which license covers each Whalory edition and where the full text of each license is. Read it before you install Whalory in an organization, share it, build your own version, or sell text you wrote with it. The editions are Whalory Core (free), Whalory Pro, and Whalory Studio. Persian version: [`LICENSE.md`](LICENSE.md).

## At a glance

| Edition | Files | License | Full text |
|---|---|---|---|
| Whalory Core | Core files | Text: Creative Commons Attribution 4.0 (CC BY 4.0); scripts: the MIT License | [`LICENSE-CORE.en.md`](LICENSE-CORE.en.md) |
| Whalory Pro | Core files | Same as Core | [`LICENSE-CORE.en.md`](LICENSE-CORE.en.md) |

Core files keep their open license inside Pro and Studio too. Buying a paid edition takes nothing away from the rights that CC BY 4.0 and MIT give you.

## Which files belong to which edition

- Core files:
  - `SKILL.md` and the front page, guide, changelog, and license files in both languages;
  - the method files in `references/`: context detection, question gate, judgment, brief, gathering, the playbooks, review, editor, voice profile, and profile builder;
  - eleven craft files in each language pack, `references/fa/` and `references/en/`: craft, prose, common errors, conventions (Persian) or style guide (English), AI tells, occasions, claims, ethics, channels, forms, and style repair;
  - the profile templates, Whalory's own voice, and the café and SaaS starter profiles, in both languages;
  - in `scripts/`, the linters, the shared counters, the Model Context Protocol (MCP) server, and the self-tests with their samples.
- The Core plugin and bundle. The Core plugin carries the Core license: its manifests, both of its agents (writer and editor), the `write`, `review`, `voice`, and `lint` commands, and the opt-in autolint hook. So does the Core `.mcpb` bundle.
- Files in every edition. `VERSION` and `agents/openai.yaml` ship with all three editions under the Core license. The icons in `assets/icon-*`, when present, also ship with every edition. They are trademarks of the Whalya studio, though, and fall under no license, as [the name and logo section](#name-and-logo) explains.
- Pro sections inside Core files. Any text between `<!-- pro -->` and `<!-- /pro -->` is not part of Core and falls under the Pro license.
- Pro files. Every other reference and profile, `data/`, the other scripts, the remaining agents, the remaining commands, and the packs for each assistant.
- In a purchased package. The `edition` field at the top of `SKILL.md` names the edition, and `LICENSE-BUYER.txt` holds the buyer's license identifier.

## Text you write with Whalory

This is the same in all three editions:

- It's yours. The Whalya studio claims no rights in the text you write with Whalory's help.
- Commercial use is allowed. That covers your own work and your clients' work. You don't need to mention Whalory in the text.
- Whoever publishes the text answers for it: correct facts, claims, permits, and compliance with the law. Whalory marks missing facts with brackets, and filling them in is your job.

The editions don't differ in your right to use what you write. They differ in the number of users, the packs, updates, and support.

## Name and logo

The product names "Whalory" and «والوری», the studio name "Whalya" and «والیا», and their logos are not covered by any of these licenses. You may use them to credit Whalory, as described in [how to credit Whalory](LICENSE-CORE.en.md#how-to-credit-whalory). A version you changed takes its own name and must not be presented as endorsed by the Whalya studio.

## Other people's services

Whalory is a set of files. It sells no access to any assistant or model. Every assistant you install Whalory on has its own terms, and those terms are separate from these licenses.

## Questions about licensing

Contact: the [contact page](https://whalory.com/en/contact) on the Whalory website. The legal text is only what [`LICENSE-CORE.en.md`](LICENSE-CORE.en.md) and `EULA.en.md` (in Whalory Pro) say; this page is a summary.

This text is not legal advice. Have a lawyer review it before publication.
