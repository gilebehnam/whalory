# Learnings note: [the brand's name]

> This file sits next to the voice profile: as `LEARNINGS.md` beside `VOICE.md` in the project, or as `<brand>.LEARNINGS.md` beside `<brand>.md` in `~/.whalory/profiles/`. Before every task, Whalory reads the profile first and then this file. After each piece of accepted feedback, one row is added here; the chat history is not the place for it. Method: [learning](../references/judgment.md#learning). The Persian template is [LEARNINGS-template.md](LEARNINGS-template.md).

## What goes here

- Accepted feedback that has not become a rule yet.
- An answer about the brand itself that will be needed again, such as the email sign-off or the exact name of a product.
- Anything repeated three times moves into the profile itself. The row then gets "yes" in the last column, with the section or key it moved to.

## What does not go here

- A one-off preference.
- Customers' personal data: names, phone numbers, addresses, and health or financial information.
- Passwords, keys, and anything else confidential.

## Notes

| Date | Format | Observation | Decision | Moved to the profile? |
|---|---|---|---|---|
| [2026-09-27] | [email] | [the client found the sentences in emails too long] | [email sentences up to 18 words; captions stay as they are] | [yes: `max_words` under `formats.email` in the JSON, and the "One voice, many tones" table] |
| | | | | |

The "Format" column holds one of the [format ids](../references/voice-profile.md#format-ids), or "all" for a decision that applies to every format.
