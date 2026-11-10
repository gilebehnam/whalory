# Plain English: copy you can read aloud

Language models write correct English that nobody speaks. They average the web, and much of the web is corporate, academic or optimized for search. This guide covers what to ask for before writing, what to leave out while writing, and how to revise. Each pattern names its rule id in `lint_en.py`, so manual and scripted checks match. Bad examples sit in code spans.

Persian version: [`plain-persian.md`](../fa/plain-persian.md). Full catalog: [`ai-tells.md`](ai-tells.md).

## Contents

- [Why "be casual" fails](#why-be-casual-fails)
- [Before writing](#before-writing)
- [Replacement table](#replacement-table)
- [Habits and rules](#habits-and-rules)
- [Revision](#revision)
- [Compact brief for any assistant](#compact-brief-for-any-assistant)
- [Five common mistakes](#five-common-mistakes)
- [Sources](#sources)

## Why "be casual" fails

A tone description is vague, and the model drifts back to its safe default within two paragraphs. The safe default is formal. Three things hold, and Whalory's method already uses all three:

1. **Specific bans.** A list of words and structures to avoid beats any description of style. The table below is that list.
2. **Numeric caps.** "No sentence over 18 words" can be counted; "keep it short" cannot. Whalory's default cap is 25 words, and a profile or channel can tighten it.
3. **A sample.** Two paragraphs the user wrote teach more than ten lines about tone. Keep them in the voice profile: [`voice-profile.md`](../voice-profile.md).

## Before writing

| Step | What to ask for | Where it lives in Whalory |
|---|---|---|
| Reader | One named person, not "users": "a designer who just went freelance". | Context card, [`brief.md`](../brief.md) |
| Good sample | Two paragraphs by the user: "copy the rhythm, sentence length and word choice; the content differs." | Voice profile |
| Counter-example | One "not like this" line next to one "like this" line. The boundary is clearer from both sides. | `examples` in the profile |
| Caps | Sentence length, sentences per paragraph, total words. | `--max-words`, channel limits |
| Questions | Ask before writing when the answer changes the text. Whalory asks at most three, one at a time. | Question gate, [`intake.md`](../intake.md) |
| Outline | Skeleton first, one sentence per section; full text after approval. | Method, outline step |

## Replacement table

| Instead of | Write | Rule |
|---|---|---|
| `is of great importance` | matters, or say why | `en-complex-word` |
| `was reviewed by the team` | the team reviewed | `en-passive` |
| `in order to`, `for the purpose of` | to | `en-complex-word` |
| `therefore`, `thus` at every turn | so | manual |
| `it is worth noting that` | cut; state the fact | `en-didactic` |
| `the aforementioned` | this, or name it | `en-complex-word` |
| `significantly`, `dramatically` | the number or the example, or cut | `en-inflated-adverb` |
| `in conclusion` | cut | `en-summary-opener` |
| `in today's world` | cut, or a real date | `en-cliche-open` |
| `let's dive into` | start with the point | `en-metaphor-buzz` |
| `at the end of the day`, `game-changer` | in short; say why it matters | `en-moral-close`, `en-buzzword` |
| `not only … but also` | two sentences, or the positive half | `en-not-just` |
| `resulted in the identification of` | found | `en-hidden-verb` |
| `it was decided that` | Ana decided | `en-impersonal-passive` |
| `we hope you found this helpful` | cut | `en-chatbot-residue` |

## Habits and rules

| Habit | Fix | Rule |
|---|---|---|
| Bureaucratic word | The short word that does the job | `en-complex-word` |
| Long sentence | One idea per sentence; split at the second idea | `en-long-sentence` |
| Opening flattery | Drop `Great question!`; the first sentence answers | `en-sycophancy`, `en-chatbot-residue` |
| Stock wrap-up | Delete the last paragraph and see what is lost; end on new information | `en-summary-opener`, `en-moral-close` |
| Inflated adverb | The adverb stands in for a missing number; give it | `en-inflated-adverb` |
| Passive without an actor | Name who did it | `en-passive`, `en-impersonal-passive` |
| Decorative triad | Two things get two words; no third word for rhythm | `en-triads` |
| Negative parallelism | Drop the straw man; state the positive point | `en-not-just`, `en-not-x-but-y` |
| Hidden verb | `conduct a review` becomes "review" | `en-hidden-verb` |
| Talking to a crowd | One reader, "you" | `en-corporate-we` |
| Borrowed idiom | Plain words | `en-metaphor-buzz` |
| Emoji and bold | No emoji headings; bold only where needed | `en-emoji-format`, `en-bold-overuse` |
| Labelled bullets | `- **Speed:** …` becomes a sentence; lists only for steps or counts | `en-inline-header-bullets` |
| Flat rhythm | After two long sentences, a short one; paragraphs of different lengths | `en-flat-rhythm`, `en-same-opening` |
| Machine certainty | Say where you are unsure; name the exception | manual, [`claims.md`](claims.md) |
| Adjective pile | One adjective per noun, then what it does | `en-adjective-stack`, `en-buzzword` |
| Unsupported general claim | One concrete example per claim, or cut the claim | manual |
| Corporate we | First person singular when one person stands behind the text; who did what | `en-corporate-we` |

## Revision

1. **Read it aloud.** Wherever you stumble or wince, the sentence is still machine-made. Rewrite that sentence, not the whole text.
2. **Halve it.** Rewrite once at half the words with no loss of information. What goes first is usually the robotic part.
3. **Third round.** Do not accept the first output; the best version usually comes on the third pass.
4. **Script.** Run `lint.py`; each error means rewriting that sentence. Thresholds: [`ai-tells.md`](ai-tells.md#severity-and-thresholds).

## Compact brief for any assistant

When the user has no Whalory install, or the assistant cannot run scripts, hand over this block. If the text has only two or three problems, send only those lines; a shorter brief is followed more closely.

```text
Write plain English, the way a person talks.
Reader: [one specific person]
Tone: [for example, warm and precise]
Do not use: is of great importance, in order to, it is worth noting, the aforementioned,
significantly, dramatically, in conclusion, in today's world, let's dive into,
at the end of the day, game-changer, not only … but also, we strive to, valued customers,
we hope you found this helpful.
Rules:
1. Prefer the short word.
2. Keep verbs as verbs: "decide", not "make a decision".
3. Name who did it.
4. At most [18] words a sentence and three sentences a paragraph; vary the lengths.
5. One adjective per noun. Every general claim gets one concrete example, or goes.
6. Talk to one reader as "you"; no corporate "we".
7. No opening flattery and no closing summary.
8. No emoji; no bold-label bullet lists.
9. Say where you are unsure.
Last step: read the text and rewrite only the sentences that sound artificial aloud.
```

## Five common mistakes

1. **Describing tone only.** "Be friendly" without a ban list lasts two paragraphs.
2. **Every rule at once.** A very long brief drops rules. Give the three or four that matter, then add.
3. **Accepting the first draft.** Run one "halve it" pass.
4. **No sample.** Two paragraphs by the user are the cheapest, strongest input.
5. **Rewriting everything.** Good parts get worse. Send only the problem sentences.

## Sources

- George Orwell, "Politics and the English Language", 1946; the six rules at the end. [orwellfoundation.com](https://www.orwellfoundation.com/the-orwell-foundation/orwell/essays-and-other-works/politics-and-the-english-language/)
- Federal Plain Language Guidelines, US government; "hidden verbs", "active voice", "short sentences". [plainlanguage.gov](https://www.plainlanguage.gov/guidelines/)
- Wikipedia, "Signs of AI writing". [en.wikipedia.org](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Nielsen Norman Group, "How users read on the web". [nngroup.com](https://www.nngroup.com/articles/how-users-read-on-the-web/)
- UK Government, "Writing for GOV.UK". [gov.uk](https://www.gov.uk/guidance/content-design/writing-for-gov-uk)
- Strunk and White, *The Elements of Style*.
- Mojtaba Yazdanpanah, a Persian workbook on getting natural Persian from AI (Melina Design School, issue 04, [mojtabaui.ir](https://mojtabaui.ir)). Whalory took the order of work and several habits from it and merged them with its own rules; the wording and examples here are Whalory's.
