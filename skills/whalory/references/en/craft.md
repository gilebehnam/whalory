# Writing craft

This file is the everyday toolkit for English copy. It covers who speaks, the small story, concrete detail, proof, and clean mechanics. Open it before every first draft and again for the three editing passes. The numbers here are defaults, and a voice profile can change them ([voice-profile.md](../voice-profile.md#tone-dials)). Examples use a fictional bakery and a fictional software company. Bad examples sit in code blocks so the linter skips them.

## Contents

- [Five pillars](#five-pillars)
  - [Narrator](#narrator)
  - [Story](#story)
  - [Texture](#texture)
  - [Truthfulness](#truthfulness)
  - [Cleanliness](#cleanliness)
- [One reader, one action](#one-reader-one-action)
- [Specificity ladder](#specificity-ladder)
- [Show with facts, not adjectives](#show-with-facts-not-adjectives)
- [Sentence rhythm](#sentence-rhythm)
- [Three editing passes](#three-editing-passes)
  - [Cut](#cut)
  - [Sharpen](#sharpen)
  - [Listen](#listen)
- [Checklist](#checklist)

## Plain terms and useful detail

Keep technical identifiers in commands and code. In public copy, name the reader's task first and explain an unfamiliar term at its first useful appearance. Use the established glossary consistently; do not rename contractual products without authorization. Prefer meaning in the target locale over a literal engineering translation.

Synthetic example, with supplied facts: a tool accepts a draft, returns suggested edits, and lets the writer export Markdown. “A powerful content optimization engine” gives the reader no usable picture. “Paste your draft, review the suggested edits, then download it as Markdown” names the actual work. It must not become “Publish automatically” unless publication is a verified capability.

When editing “Export is available on the paid plan; AI usage is charged separately,” retain both conditions. “Everything included” changes the offer and fails review. Clearer wording does not create a cheaper price, extra entitlement or stronger result.

## Five pillars

Every piece of copy, from a button label to a landing page, stands on the same five pillars. The review checklist checks each of them ([review.md](../review.md#narrator-and-story)).

| Pillar | The question it asks |
|---|---|
| Narrator | Who is talking, and to whom? |
| Story | What changes between the first line and the last? |
| Texture | Could a reader see, touch, or check what the words describe? |
| Truthfulness | Is every claim backed by something the brand can show? |
| Cleanliness | Does the text read as if one careful person wrote it? |

### Narrator

The narrator is someone who has seen the thing up close. Five habits keep that voice steady:

- One person is addressed, as "you." Never write to `valued customers` or `dear users`.
- The narrator keeps the brand out of the spotlight. `We believe` and `we are proud to` go. Use "we" only for real work: we bake, we ship, we reply within a day.
- Knowledge comes before selling. "Warm it for a minute before you eat it" does more than `Buy now`.
- The distance to the reader stays fixed. Close enough to sound human, far enough to stay polite, and steady from start to finish.
- So does the point of view. If the copy starts with "we," it ends with "we."

The plain-language guidelines say the same about any document. You are speaking to the one person reading it, and "you" makes the text relevant to that reader. Source: [Federal Plain Language Guidelines, address the user](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/audience/address-the-user.md), checked 2026-09-27.

### Story

Even a 20-word caption has a small arc. First comes a thing, a person, or a place. Then a moment. The end is a small result: a tip, a quiet image, or the next step.

```
Our sourdough is made with love and the finest ingredients. Come try it today!
```

"The starter goes into the fridge at 9 at night and comes out at 6. By 8 the first loaves are on the shelf." That version has a before, a change, and an after. Every clock time in it comes from the baker, not from the writer.

The last sentence is usually the shortest. A story never ends on a moral.

### Texture

Texture ties a sentence to one subject. Use exact nouns, strong verbs, and at most one physical detail per short text.

- "Crust that cracks when you press it" says more than `delicious bread`.
- Take images from the subject's own world: the oven, the flour sack, the delivery van. Never borrow grand metaphors such as `a symphony of flavor`.
- Lists of countable things stay plain: commas, no adjectives, in the order people actually say them.

### Truthfulness

- Every fact in the copy traces to the brief, the profile, or a source the brand can show.
- What you do not know goes in a bracket: `[confirm: weight]`. An honest draft with brackets beats a complete draft with guesses.
- Do not exaggerate, and do not hedge what you know. A needless "may" or "might" also reads as machine text.
- Name the limit plainly, without apology. "Sold out by noon most days" is a fact, not a failure.
- Claims about health, money, the environment, reviews, and price need the evidence listed in [claims.md](claims.md).

### Cleanliness

A clean text has no filler sentence, one register, correct mechanics, and none of the machine patterns in [ai-tells.md](ai-tells.md). Mechanics follow the variant and house style in [style-guide.md](style-guide.md). Plain-English rules are in [prose.md](prose.md).

## One reader, one action

Before the first word, name the reader and the one thing they should do next. Then write only for that person.

- One reader. A caption for regulars and a caption for first-time buyers are two different texts.
- One action. Each piece asks for one next step: reply, book, try the sample, save the post. Two calls to action split the reader's attention.
- Put the action where the reader is ready for it. In a short text that is usually the end. On a long page, put it near the top and repeat the same action after each block of proof.

GOV.UK asks writers to address the user as "you" and to be specific and concise. Source: [GOV.UK, writing in the right tone](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/right-tone/), checked 2026-09-27.

```
Discover our range, follow us for updates, and sign up for our newsletter!
```

"Reply 'loaf' and we'll hold one for you until 10."

## Specificity ladder

A claim gets stronger each time it climbs one rung toward something a reader could check. Climb until the reader could verify the sentence, or until the brief runs out. Where it runs out, put a bracket.

| Rung | Bakery example | Software example |
|---|---|---|
| 1. Category | `quality bread` | `a better workflow` |
| 2. Type | sourdough | invoice approvals |
| 3. Named thing | the rye sourdough | the two-click approval button |
| 4. Measured detail | fermented for [confirm: hours] hours | approvals in [confirm: median time] |
| 5. Checkable fact with a source | fermented for [confirm: hours] hours, per the baker's log for [confirm: date] | a median approval time of [confirm: minutes] minutes in [confirm: month] billing data |

Rungs 4 and 5 are where brackets appear most. The writer never fills them from imagination.

## Show with facts, not adjectives

Every adjective in the draft stands in for a fact that earned it. Find the fact and let it replace the adjective. If there is no fact, cut the adjective.

| Telling | Showing |
|---|---|
| `carefully crafted` | Each loaf is shaped by hand. [confirm: who shapes them] |
| `amazing taste` | Sour at first, then sweet from the rye. |
| `fast support` | A person replies within [confirm: response time]. |
| `trusted by many` | [source needed: number of customers and date] |

Generic praise is where machine text drifts. Wikipedia's field guide to AI writing describes output that swaps specific facts for generic, positive statements. The subject ends up less specific and more exaggerated at once. Source: [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), revision 1376889964, checked 2026-09-27. GOV.UK warns that adjectives sound like spin. Source: [GOV.UK, right tone](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/right-tone/), checked 2026-09-27.

## Sentence rhythm

- Mix lengths. Two longer sentences, then a short one. A paragraph often ends on the short one.
- Keep sentences at or under the profile cap. The English default is 25 words at sentence-length dial 3. The dial runs from 15 words at 1 to 35 at 5 ([voice-profile.md](../voice-profile.md#sentence-length)). GOV.UK asks writers to check any sentence over 25 words. Source: [GOV.UK A to Z style guide](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), checked 2026-09-27.
- Vary the first word. Three sentences in a row that open with "We" or "This" read as a template. Google's style guide tells writers not to start every sentence the same way. Source: [Google developer documentation style guide: voice and tone](https://developers.google.com/style/tone), checked 2026-09-27.
- Put the subject and verb early. A long opening clause makes the reader hold everything until the verb arrives, so give conditions a sentence of their own.
- The linter flags three same-word openings in a row (`en-same-opening`) and six or more sentences of nearly equal length (`en-flat-rhythm`).

```
We bake every morning. We use local flour. We deliver across town. We love what we do.
```

"The first batch leaves the oven at 6, before most of the street is awake. Flour comes from [confirm: mill name], two towns over. Delivery starts at 8."

## Three editing passes

Edit in three passes, in this order. Each pass has one job, so nothing gets fixed twice.

### Cut

- Delete the warm-up sentence at the top and the summary at the end. Test by removing them; if nothing is lost, they stay out.
- Delete stacked adjectives, repeated ideas, and sentences that only announce the next sentence.
- Cut words, then sentences, and never a fact. Every number, name, date, price, and condition survives the cut.
- Swap long words for short ones: "help," not `assist`; "use," not `utilize` ([Federal Plain Language Guidelines, simple words](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/words/use-simple-words-phrases.md), checked 2026-09-27).

### Sharpen

- Replace each vague word with the specific one. "Soon" becomes a date, or a bracket.
- Name the actor. "We refund you within [confirm: days] days," not `refunds will be processed`. The plain-language guidelines say active voice makes clear who does what ([use active voice](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/conversational/use-active-voice.md), checked 2026-09-27).
- One idea per sentence. Move an "if" clause into a sentence of its own ([write short sentences](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/concise/write-short-sentences.md), checked 2026-09-27).

### Listen

- Read the text aloud. Wherever your breath runs out, split the sentence.
- Wherever it sounds like a brochure, rewrite that line from the facts.
- Check every sentence over the profile cap and every paragraph over 150 words ([prose.md](prose.md#paragraphs)).
- Listen for the same word twice in one sentence and for three sentences that start alike.

## Checklist

Linter rule ids: `en-long-sentence`, `en-long-paragraph`, `en-same-opening`, `en-flat-rhythm`, `en-passive`, `en-hidden-verb`, `en-complex-word`, `en-superlative`, `en-stat-claim`, `en-moral-close`, `en-summary-opener`, `en-rhetorical-open`, `en-cliche-open`.

- [ ] One narrator talks to one reader as "you," and "we" appears only for real work.
- [ ] The text has a small arc: a thing, a moment, a small result.
- [ ] Each adjective was replaced by the fact behind it, or cut.
- [ ] Every fact traces to the brief or a source; the rest is in `[confirm: …]` or `[source needed: …]` brackets.
- [ ] The copy asks for one action, at the point where the reader is ready.
- [ ] Sentence lengths rise and fall, and no three sentences open with the same word.
- [ ] All three passes ran: cut, sharpen, listen.
