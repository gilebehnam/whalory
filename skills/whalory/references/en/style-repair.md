# Style repair

Sometimes the text exists but sounds wrong. Sometimes it is notes that are not copy yet. Think of messy meeting minutes, a voice memo transcript, a manager's rushed draft, or a paragraph that reads like a translation. This file is for repairing, not for writing from scratch. The difference is that in a repair, someone else's facts and intent are in your hands, and they must come back intact. Each "before" text sits in a code block, because it is broken on purpose; each "after" text must pass the linter.

## Contents

- [Questions before you repair](#questions-before-you-repair)
- [Repair order](#repair-order)
  - [Facts](#facts)
  - [Structure](#structure)
  - [Sentences](#sentences)
  - [Words](#words)
- [Removing AI tells without swapping synonyms](#removing-ai-tells-without-swapping-synonyms)
- [Meeting-note cleanup](#meeting-note-cleanup)
- [Voice-note transcript cleanup](#voice-note-transcript-cleanup)
- [Three-line change report](#three-line-change-report)
- [Comparing before and after](#comparing-before-and-after)
- [Checklist](#checklist)

## Questions before you repair

Diagnose first, then touch the text. The answers to these ten questions set how deep the repair goes and what must not change. Write down the answer to question 6; the others can stay in your head.

1. Reader: who reads this, and in what state? A colleague in a team chat, a customer waiting for an answer, an investor with two minutes?
2. Goal: what should happen after reading? A decision, an action, reassurance, or just information? If it is unclear, ask the owner.
3. Voice: how far is the text from the voice profile ([voice-profile.md](../voice-profile.md#tone-dials))? Does it mix registers?
4. Tells: how many patterns from [ai-tells.md](ai-tells.md) does it have? One or two means a sentence-level repair; more means structure.
5. Structure: where is the most important sentence? If it is in the third paragraph, the structure is the problem.
6. Facts: which numbers, names, dates, prices, conditions, and deadlines does it contain? List them. The list stays with you until the end.
7. Length: is it too long or too short for its channel ([channels.md](channels.md))?
8. Repetition: which idea is said twice, and which word shows up in every paragraph?
9. Rhythm: read it aloud. Where do you run out of breath? Are all the sentences the same length?
10. Mechanics: spacing, quotation marks, and spelling variant. The linter finds these.

## Repair order

Work in this order: facts, structure, sentences, words. Lock the facts first, every time. Then change as little as the text needs. If the structure works, leave it and go down a level; if the sentences work, only the words need care.

When the owner asked for "just the typos," repair only the words, even if you see bigger problems. Report the bigger problems in the [change report](#three-line-change-report) instead of fixing them. An unrequested rewrite, even a good one, costs trust.

A sentence from a software help page, repaired at three depths:

```
Input:      Users are able to utilize the reports functionality via the settings menu in order to download reports .
Words:      Users can use the reports feature in the settings menu to download reports.
Sentences:  Download reports from the settings menu.
Structure:  To download a report, open Settings > [confirm: section name]. [confirm: when reports are generated; ask the product team]
```

### Facts

In a repair, these belong to the owner, and each one comes back unchanged:

| Fact | Example | What editors often break |
|---|---|---|
| Numbers | 12 people, $2,500, 3 days | Rounding; "about ten days" turned into "10 days" |
| Names | People, products, companies, version numbers | "Better" spellings, synonyms |
| Conditions | "if paid by Friday" or "existing customers only" | Dropped to shorten the sentence |
| Deadlines | "by the end of October" or "Thursday" | Turned into "soon" |
| Intent | A firm "no" or a real "maybe" | A softened "no" or a hardened "maybe" |

If something is unclear, do not guess. Put in a bracket: `[confirm: amount]`. An honest, incomplete text beats a complete, wrong one.

### Structure

- Put the most important sentence first: the request, the decision, or the news.
- Reorder, merge, or cut paragraphs so each one holds one idea.
- A structural repair of someone else's text reorders their meaning. Ask before you do it, or say plainly in the report what moved.
- When material is missing, the rewritten text gets brackets, never invented details ([gathering.md](../gathering.md#when-materials-are-missing)).

### Sentences

- Split sentences over 25 words or the profile's cap. The plain-language guidelines ask for one idea per sentence. Source: [Federal Plain Language Guidelines, write short sentences](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/concise/write-short-sentences.md), checked 2026-09-27.
- Name the actor, and turn hidden verbs back into verbs ([prose.md](prose.md#hidden-verbs)).
- Remove filler: warm-up sentences, restated points, and `please note` frames.

### Words

- Use simple words ([prose.md](prose.md#simple-words)) and the variant's spelling ([style-guide.md](style-guide.md#us-and-uk-spelling)).
- Let the linter fix the mechanics. `python scripts/lint.py draft.txt --fix` writes the result to `draft.fixed.txt`, and `--write` changes the file in place. For English it fixes double spaces, mixed quotation marks, dash spacing, heading punctuation, and spelling off the variant.
- The fixer never touches word choice, tells, facts, or tone. Those stay with you.

## Removing AI tells without swapping synonyms

Swapping a flagged word for a synonym keeps the pattern and only hides it. Wikipedia's field guide warns that surface edits could "just make detection harder" without fixing the text. Source: [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), revision 1376889964, checked 2026-09-27. Rewrite from the facts up instead:

1. Run the [substitution test](ai-tells.md#substitution-test). If the text still fits after you swap the brand name, it has no real detail, and the repair is structural.
2. Delete the first and the last paragraph as a test. They usually stay deleted.
3. Remove every negative parallelism and every fake list of three. Put a real detail or a bracket in each place.
4. Delete or bracket every number and claim with no source. `Thousands of happy students` does not survive without a count.
5. Count what is left. If it is less than half the text, you need materials, not edits ([gathering.md](../gathering.md)).

```
In today's fast-paced world, learning a language isn't just an option; it's a necessity. Our innovative courses, led by experienced instructors, offer a truly transformative learning journey. Join us and unlock your potential!
```

"[confirm: course name] has [confirm: number of sessions] sessions of [confirm: length] each, on [confirm: weekdays]. The first session covers [confirm: first topic]; by the last, you [confirm: concrete outcome]. Your teacher: [confirm: name and one checkable fact about them]."

No fact survived from the original, so every slot is a bracket. At this point the repair has become a list of materials to request from the school.

## Meeting-note cleanup

Meeting notes are usually a list of everything said, in the order it was said. Tomorrow's reader wants four things: what was decided, what has to happen, who owns it, and by when.

1. Sort every line into one of four baskets: decision, task, open question, or discussion with no outcome.
2. Give each task a verb, an owner, and a deadline. An unknown owner becomes `[confirm: owner]`; never guess.
3. A discussion with no outcome is either deleted or kept as one line in the "Still open" list.
4. A decision that was not made in the meeting is not made in the notes.
5. Put the date and attendees at the top and the next meeting at the bottom.

Before (clinic front-desk notes):

```
mtg oct 12 - booking system
- booking system has issues patients calling saying no confirmation text
- dr [name] said no more thursdays
- sam to check with the sms company
- visit price?? discussed
- fix by end of month
- website needs updating w new hours
- dr [name] said maybe add 2 evening slots
```

After:

Booking meeting, October 12. Attendees: [confirm: names].

Decisions

1. From [confirm: start date], Dr. [confirm: doctor's name] takes no Thursday appointments.
2. The new opening hours go on the website.

| Task | Owner | Deadline |
|---|---|---|
| Ask the text message provider why booking confirmations are not reaching patients | Sam | [not set in the meeting] |
| Fix the confirmation texts | [confirm: owner] | End of October |
| Update the opening hours on the website | [confirm: owner] | [not set in the meeting] |

Still open

- Visit price: discussed, no decision.
- Two evening slots for Dr. [confirm: doctor's name]: still a "maybe." [confirm: who follows up, and by when]

What changed:

| Change | Why |
|---|---|
| Seven loose lines became two decisions, three tasks, and two open items | Tomorrow's reader wants their own task, not the order of the conversation |
| The doctor's "maybe" stayed a "maybe" | Notes record decisions; they do not make them |
| Unknown deadlines became brackets | An editor's guess must not become a real deadline |
| "Has issues" became "confirmations are not reaching patients" | A problem has to be specific enough for someone to fix |

## Voice-note transcript cleanup

A voice message was spoken for the ear, and now the eye reads it. A raw transcript carries three extras: fillers, false starts, and the speaker's own corrections.

| Remove | Example |
|---|---|
| Fillers | `um`, `so basically`, `you know`, `like` |
| False starts and self-corrections | `Tuesday, no, Wednesday at nine` keeps only Wednesday at nine |
| Emphatic repeats | `really, really important` keeps one "really" |

Keep the speaker's own words, their order of importance, and their warmth. If they said "don't come back empty-handed," keep it; `it is recommended that you return with stock` is not their voice.

The destination sets the register, not the speaker. A message for the team chat stays conversational; a task card or a customer email becomes clear written English. Numbers spoken as words become numerals: `twenty-five of them` becomes "25 of them." Anything ambiguous gets a bracket: `[confirm: which week "next week" means]`. What the speaker did not say is not in the text.

Before (a bakery owner's voice note to the sales lead):

```
hey so um I just talked to mr [name] and he wants the, you know, the rye order, the twenty, no sorry, twenty-five loaves, by thursday if possible, so can you check what we've got because if we don't have it it won't get there by thursday, and also he still hasn't paid the last invoice, he said next week, so really really make sure you call him
```

After (a task card):

Order for [confirm: customer name]: 25 rye loaves by Thursday, if possible. Owner: [confirm: sales lead's name].

Check stock. If we are short, the order won't arrive by Thursday. [confirm: what to tell the customer if it won't arrive]

His last invoice is still unpaid; he said he'd pay next week. Make sure you call him.

What changed:

| Change | Why |
|---|---|
| "twenty, no sorry, twenty-five" became 25 | The speaker's own correction counts; the first number goes |
| The fillers went | They helped the speaker breathe; on the page they are noise |
| "if possible" stayed | It is the customer's condition; dropping it makes a promise |
| "what to tell the customer" became a bracket | The speaker never said it, so it stays open for the owner |

## Three-line change report

Every repair ships with three lines, separate from the text:

1. What changed: the depth of the repair and the biggest change, in one sentence.
2. Why: in the reader's terms, not the editor's. "So the front desk knows what to do between two guests," not `removed redundancies and improved flow`.
3. What stayed and what needs sign-off: the numbers and conditions kept word for word, and every bracket.

For the booking notes above:

1. Structural repair: the notes became decisions, tasks, and open items.
2. So each person can find their own task tomorrow morning.
3. October 12, "end of October," and the doctor's "maybe" stayed as they were. Every owner, deadline, and name the meeting did not settle is a bracket.

If the owner asked only for typos and you saw a bigger problem, leave the text alone and say so in these three lines.

## Comparing before and after

After the repair, put the two versions side by side. Every item on the fact list from question 6 must appear in the "after" version. That means the same number, name, condition, and deadline. An item that is missing or changed goes back before delivery.

## Checklist

Linter rule ids: `en-long-sentence`, `en-hidden-verb`, `en-complex-word`, `en-spelling-mix`, `en-quote-mix`, `en-double-space`, and every error in [ai-tells.md](ai-tells.md#tell-to-rule-map).

- [ ] The ten questions were answered, and the fact list was written down.
- [ ] Every number, name, condition, deadline, and intent from the list appears unchanged.
- [ ] The repair went only as deep as the text needed, or as deep as the owner asked.
- [ ] Tells were rewritten from the facts, not swapped for synonyms.
- [ ] Meeting notes show decisions, tasks with owners and deadlines, and open items; nothing was decided in the notes.
- [ ] A cleaned transcript keeps the speaker's words, corrections, and conditions.
- [ ] Unknowns are brackets, and the three-line report lists them.
