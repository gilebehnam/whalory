# AI tells

Some patterns make English copy read as machine-made. One word proves nothing; a pattern of them does. This catalog gives each pattern with an example, a severity, the rule id in `lint_en.py`, and the fix. Open it before delivering any English text and during every review. When scripts cannot run, the tables here are the manual checklist. Every example of a tell sits in inline code or a code block, so the linter does not count this file against itself.

## Contents

- [Why tells matter](#why-tells-matter)
- [Severity and thresholds](#severity-and-thresholds)
- [Content tells](#content-tells)
- [Language tells](#language-tells)
  - [Vocabulary by era](#vocabulary-by-era)
  - [Negative parallelisms](#negative-parallelisms)
  - [Rule of three](#rule-of-three)
- [Style tells](#style-tells)
  - [Em-dash density](#em-dash-density)
  - [Title case in headings](#title-case-in-headings)
  - [Bold overuse](#bold-overuse)
  - [Inline-header bullets](#inline-header-bullets)
  - [Emoji bullets](#emoji-bullets)
- [Communication tells](#communication-tells)
  - [Collaborative residue](#collaborative-residue)
  - [Knowledge-cutoff speculation](#knowledge-cutoff-speculation)
- [Markup tells](#markup-tells)
  - [Chatbot citation artifacts](#chatbot-citation-artifacts)
- [Citation tells](#citation-tells)
- [Research evidence](#research-evidence)
- [Signs of human writing](#signs-of-human-writing)
- [Ineffective indicators](#ineffective-indicators)
- [Tell-to-rule map](#tell-to-rule-map)
- [Review without scripts](#review-without-scripts)
- [Substitution test](#substitution-test)
- [Checklist](#checklist)

## Why tells matter

Tells are quality problems. Each one marks a place where the text is generic, unsupported, padded, or talking to the wrong person. A reader who meets them stops trusting the rest, whoever wrote it.

The main source for this file is the WikiProject AI Cleanup guide on Wikipedia. It calls itself a descriptive field guide, not a set of rules. Its core idea is that language models drift toward the average: specific facts give way to generic, positive, important-sounding claims. The guide also warns that the signs are symptoms, and that editing only the surface could "just make detection harder." Source: [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), revision 1376889964 of September 26, 2026, checked 2026-09-28. The rest of this file cites that page as "the guide."

So Whalory never treats this catalog as a way to hide machine help. It fixes the cause: missing facts, a missing reader, or a missing point. Whether to disclose AI use is a separate question, answered in [ethics.md](ethics.md#ai-disclosure).

## Severity and thresholds

| Severity | Meaning | What to do |
|---|---|---|
| Error | A pattern that is machine-made, invented, or wrong in almost any text | Rewrite the sentence or paragraph from the facts. Never deliver a text with an error. |
| Warning | A sign that is sometimes fine and gives the text away in numbers | Keep it only if you can say in one sentence why it belongs; otherwise change it. |

Rewrite thresholds:

- One error: rewrite that sentence or paragraph from the facts up. Swapping one word does not fix an error, because the problem is the pattern.
- Three warnings from one group: rewrite the whole text. The groups are the six tell sections below: content, language, style, communication, markup, and citation. In a long text, count each section under a heading on its own.
- Vocabulary density: in any text of 150 words or more, three distinct words from the AI vocabulary list per 300 words is an error. So are five distinct words from that list and the buzzword list together (`en-ai-vocab-density`).
- Intentional warnings: a customer's real words in a quotation, or a product's official name. Say in the note which warning stayed and why. An intentional error is accepted only in a teaching example marked "not this."
- Profile: a word in the profile's `banned` list is an error (`en-profile-banned`), and a word in `avoid` is a warning (`en-profile-avoid`). The `allow` list exempts one named word from the buzzword check. It never exempts a structural pattern.

## Content tells

These tells inflate what the text says without adding a fact. The guide groups them under content. Group: content.

| Tell | Example | Rule | Fix |
|---|---|---|---|
| Inflated significance | `stands as a testament to`, `plays a pivotal role`, `marks a significant shift`, `left an indelible mark` | `en-significance` (warning) | Delete, or state the specific consequence with its source |
| Canned notability | `featured in numerous leading outlets`, `independent coverage`, `an active social media presence` | `en-media-canned` (warning) | List the real outlets with dates from the brief, or cut |
| Trailing -ing analysis | `, highlighting its commitment to quality.` and `, ensuring a seamless experience.` | `en-ing-analysis` (warning) | Cut the clause, or make it a sentence with a source |
| Promotional wording | `vibrant`, `nestled in the heart of`, `boasts a`, `diverse array`, `groundbreaking`, `renowned` | `en-buzzword` (warning) | Say what it does, for whom, with a number |
| Vague attribution | `Experts say`, `Studies show`, `It is widely believed`, `industry reports suggest` | `en-vague-attribution` (error) | Name and link the source, or delete; never invent a source |
| Challenges and outlook formula | `Despite its success, the brand faces challenges`; a heading `Future Outlook` | `en-challenges-outlook` (warning) | Name the specific, sourced problem, or drop it |
| Summary opener | `In conclusion,`, `Overall,`, `Ultimately,`, `In essence,` | `en-summary-opener` (warning) | End on the last concrete point or the call to action |
| Moral close | `Because at the end of the day, it's the people that matter.` | `en-moral-close` (warning) | End on the action |

The guide notes that newer models are "more subtly positive" than older ones, so a text can have few loud words and still say nothing. The [substitution test](#substitution-test) catches that.

## Language tells

Word choice and sentence patterns that repeat across machine text. Group: language.

| Tell | Example | Rule | Fix |
|---|---|---|---|
| AI vocabulary | `delve`, `tapestry`, `testament`, `underscore` (verb), `showcase`, `pivotal`, `intricate`, `meticulous`, `realm`, `garner`, `boast`, `bolster`, `interplay`, `noteworthy` | `en-ai-vocab` (warning) | The plain or specific word, or the fact itself |
| Buzzwords | `seamless`, `robust`, `leverage`, `unlock`, `elevate`, `empower`, `foster`, `game-changer`, `cutting-edge`, `harness`, `embark` | `en-buzzword` (warning) | Say what changes, for whom, by how much |
| Avoiding "is" and "has" | `serves as a hub`, `stands as the leader`; `features a`, `offers over 20` | `en-copula-avoid`, `en-marketing-has` (warnings) | "is" and "has" |
| Vague connection | `associated with`, `in connection with` | `en-vague-association` (warning) | State the relation, such as "was CEO of" or "supplies" |
| Transition openers | `Additionally,`, `Furthermore,`, `Moreover,`, `Notably,` at the start of a sentence | `en-additionally` (warning) | Delete, or use "also" inside the sentence |
| Didactic frame | `It's important to note that`, `worth noting`, `results may vary` | `en-didactic` (warning) | State the fact |

### Vocabulary by era

The guide groups the words that recur together by model period, and asks readers to take the lists literally. Check for the listed words themselves. A synonym hides the word, not the habit.

| Period in the guide | Words the guide lists |
|---|---|
| 2023 to mid-2024 (`GPT-4`) | `Additionally`, `boasts`, `bolstered`, `crucial`, `delve`, `emphasizing`, `enduring`, `garner`, `intricate/intricacies`, `interplay`, `key`, `landscape`, `meticulous/meticulously`, `pivotal`, `underscore`, `tapestry`, `testament`, `valuable`, `vibrant` |
| Mid-2024 to mid-2025 (`GPT-4o`) | `align with`, `bolstered`, `crucial`, `emphasizing`, `enhance`, `enduring`, `fostering`, `highlighting`, `pivotal`, `showcasing`, `underscore`, `vibrant` |
| Mid-2025 and on (`GPT-5`) | `emphasizing`, `enhance`, `highlighting`, `showcasing`, plus the words of canned notability ([content tells](#content-tells)) |

The guide notes that `delve` was overused in 2023 and early 2024, became less frequent later in 2024, and then dropped off sharply in 2025. The lists change with each model generation, so a text free of these words proves nothing. Studies of word frequency are in [research evidence](#research-evidence).

### Negative parallelisms

A negative parallelism sets up a claim nobody made, then knocks it down. It sounds decisive and says less than a plain sentence.

| Pattern | Example | Rule |
|---|---|---|
| `not just X, but Y` | `It's not just a coffee, but a ritual.` | `en-not-just` |
| `it's not X, it's Y` | `It isn't about speed. It's about trust.` | `en-not-x-but-y` |
| `no X, no Y, just Z` | `No fuss, no waiting, just great bread.` | `en-no-x-no-y` |

All three rules are warnings. Fix: state Y and support it. "Pour-over, brewed one cup at a time" needs no straw man.

### Rule of three

Triads of adjectives or phrases make a thin claim look thorough: `fast, reliable, and secure`, or three short slogans in a row. Keep a list of three only when there are exactly three real items. Otherwise keep the one that matters and replace it with a detail. The linter warns at two or more triads per 100 words, or triads in two consecutive sentences, in texts of 60 words or more (`en-triads`).

## Style tells

Formatting habits carried over from chat interfaces. Group: style.

### Em-dash density

The guide lists heavy em-dash use, often where a person would write a comma, parentheses, or a colon, and often in a punched-up sales register. It adds that AI-generated em dashes are usually surrounded by spaces. The guide treats the sign as useful next to other signs, not by itself. It also notes that some companies have tuned newer chatbots to suppress em dashes. It cites a July 2026 study in which, among current models, only Claude used them more than professional writers. Its September 2026 revision flags the sign as less common in current output.

Whalory's own drafts use no mid-sentence dash at all ([style-guide.md](style-guide.md#dashes)). The density warning exists for text Whalory is reviewing or repairing. The linter warns at more than one em dash per 150 words or per paragraph (`en-dash-density`). A spaced em dash gets its own warning, `en-dash-spacing`, unless the house style is `ap`, which spaces them on purpose.

### Title case in headings

The guide says chatbots "strongly tend to capitalize all main words" in headings. Microsoft, Google, and GOV.UK all use sentence case ([style-guide.md](style-guide.md#sentence-case-headings)). The rule is `en-title-case-heading`, a warning. It is off only for the `chicago` house style, which uses title case for titles. Associated Press (AP) headlines use sentence case, so the check stays on for `ap`.

### Bold overuse

Bold scattered through running text, often in a "key takeaways" style, is a style tell. GOV.UK uses bold only for interface elements in instructions and never for emphasis. Source: [GOV.UK A to Z style guide](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), checked 2026-09-27. The linter warns at more than one bold span per 100 words of prose (`en-bold-overuse`).

### Inline-header bullets

A list in which every item opens with a bold label and a colon is a common chat format:

```
- **Quality:** We use the finest ingredients.
- **Speed:** Orders ship fast.
- **Support:** Our team is always here for you.
```

Write prose, or plain bullets under a lead-in line. The linter warns at three such lines in a row (`en-inline-header-bullets`).

### Emoji bullets

Emoji at the start of bullets or headings are a formatting tell in professional copy. Microsoft's style guide says not to use emoji at the start of consecutive lines to fake a list. Source: [Microsoft Writing Style Guide, emoji](https://learn.microsoft.com/en-us/style-guide/a-z-word-list-term-collections/e/emoticons-emoji), checked 2026-09-27. The rule is `en-emoji-format`, off for the `caption`, `story`, and `reels` formats.

The guide lists one more style sign: straight and curly quotation marks mixed in one text (`en-quote-mix`). Curly quotes alone prove nothing; the mix is the sign. Whalory adds a rule of its own for social captions: no heading or bold title line inside a caption (`en-caption-header`).

## Communication tells

Text addressed to the person who asked for it instead of the reader. Group: communication.

### Collaborative residue

Leftovers from a chat: `Certainly!`, `Of course!`, `Great question`, `I hope this helps`, `Let me know if you'd like`, `Would you like me to`, `Here is a revised version`, `You're absolutely right`. A deliverable never speaks to its requester. The rules are `en-chatbot-residue` and `en-sycophancy`, both errors.

Flattering openers have a known cause. Sharma and colleagues found that assistants trained on human feedback tend to agree with users. The preference models behind them sometimes prefer a convincing sycophantic answer to a correct one. Source: [Sharma et al., Towards Understanding Sycophancy in Language Models](https://arxiv.org/abs/2310.13548), checked 2026-09-27.

Unfilled templates belong here too: `[Your Company]`, `[Insert date]`, `Lorem ipsum`, `TBD`, `XX%`, and a `{{variable}}` in prose. The rule is `en-template-residue`, an error. Whalory's own brackets, `[confirm: …]` and `[source needed: …]`, are not residue: the linter counts them in `stats.placeholders`, and the note lists each one.

### Knowledge-cutoff speculation

Phrases such as `as of my last knowledge update`, `based on available information`, `while specific details are limited`, or `not widely documented` are errors (`en-cutoff-speculation`). The guide notes that guesses introduced with "likely" often follow them. Delete the phrase and the guess, and put a bracket where the fact should be: `[source needed: founding year]`.

## Markup tells

Markdown and tool output pasted into a place that does not render it: stray asterisks, pound signs, or a fenced code block around plain copy. Group: markup.

### Chatbot citation artifacts

The guide lists traces that chat tools leave in copied text. Any of them is an error, and the claim they were attached to needs checking again (`en-chatbot-markup`).

| Tool named in the guide | Artifacts |
|---|---|
| ChatGPT | `contentReference`, `oaicite`, `turn0search0`, `attributableIndex`, `utm_source=chatgpt.com` |
| Gemini | `[cite: 1]`, `[span_1](start_span)` |
| Grok | `grok_card` |
| DeepSeek | `【1†` |
| Perplexity | `ppl-ai-file-upload` |

## Citation tells

The guide lists citation problems that often come from generated text. They include broken links, an invalid digital object identifier (DOI), and an International Standard Book Number (ISBN) that fails its checksum. Others are DOIs that lead to an unrelated paper and book citations without page numbers. Group: citation.

- Open every link and resolve every DOI before a text that cites it goes out. The linter warns on any DOI so that someone checks it, and flags an ISBN with a bad checksum as an error (`en-citation-check`).
- A number, study, or expert in the copy needs a source the brand can show. Without one, the linter flags it (`en-stat-claim`, `en-establishment-claim`), and the fix is a bracket: `[source needed: survey size and date]`.
- A quotation with a name after it is treated as a testimonial and needs the person's consent (`en-testimonial`; [claims.md](claims.md#testimonials-and-reviews)).

Source hierarchy and citation checks in depth: research.md (in Whalory Pro).

## Research evidence

What published studies measured. Each finding is about a population of texts; none of them lets anyone judge a single text.

Kobak and colleagues studied over 15 million PubMed abstracts from 2010 to 2024. They estimate that at least 13.5% of the 2024 abstracts were processed with language models. Of the excess style words of 2024, 66% were verbs and 14% were adjectives. Before 2024, most excess words had been content words, mostly nouns. The form `delves` appeared 28 times more often than expected. Source: [Kobak et al., Science Advances 2025](https://www.science.org/doi/10.1126/sciadv.adt3813), with the figures checked in the [arXiv version](https://arxiv.org/abs/2406.07016) on 2026-09-28.

Juzek and Ward found 21 focal words whose rise in scientific abstracts is likely the result of model use, among them `delve`, `intricate`, and `underscore`. They found no evidence that model architecture, algorithm choices, or training data cause the overuse. Their model tests are consistent with training on human feedback playing a role, but the question is not settled. Source: [Juzek and Ward, COLING 2025](https://aclanthology.org/2025.coling-main.426/), checked 2026-09-28.

Liang and colleagues studied peer reviews submitted to four AI conferences. They estimated that 6.5% to 16.9% of that text could have been substantially modified by a model. In the 2024 reviews for one of them, the International Conference on Learning Representations, `meticulous` became 34.7 times more likely to occur in a sentence. Source: [Liang et al., ICML 2024](https://arxiv.org/abs/2403.07183), checked 2026-09-28.

A second study by Liang and colleagues covered 950,965 papers published from January 2020 to February 2024. Model-modified content grew fastest in computer science, up to an estimated 17.5%. Mathematics papers and the Nature portfolio showed the least, up to 6.3%. In arXiv computer-science abstracts, the four words that models used most disproportionately, compared with human writers, were `realm`, `intricate`, `showcasing`, and `pivotal`. Source: [Liang et al., Mapping the Increasing Use of LLMs in Scientific Papers](https://arxiv.org/abs/2404.01268), abstract and Figure 2, checked 2026-09-28.

Reinhart and colleagues compared grammar rather than vocabulary. Instruction-tuned models used present participial clauses at 2 to 5 times the human rate, and nominalizations at 1.5 to 2 times. For `GPT-4o` the participial-clause rate was 5.3 times the human rate. The word `tapestry` appeared in 23% of its outputs. Source: [Reinhart et al., PNAS 2025, arXiv version](https://arxiv.org/abs/2410.16107), checked 2026-09-27.

Russell, Karpinska, and Iyyer asked annotators to label 300 non-fiction articles as human-written or machine-generated. Annotators who often use language models for writing did well: the majority vote of five of them misclassified only 1 of the 300 articles. Source: [Russell, Karpinska, and Iyyer, ACL 2025](https://aclanthology.org/2025.acl-long.267/), checked 2026-09-28. The guide summarizes this as individual heavy users being right about 90% of the time. It adds that participants who rarely used language models did only slightly better than chance.

Two lessons for copy. The trailing -ing clause and the hidden verb are measurable habits, so `en-ing-analysis` and `en-hidden-verb` are worth fixing even when no single word looks odd. And word lists change with each model generation, so the lasting fix is a fact, not a synonym.

## Signs of human writing

The guide lists patterns that were more common in articles written by people. Whalory uses them as targets for good copy, not as a disguise.

- Plain "is" and "has."
- Plain verbs: "wrote," not `authored`; "used," not `utilized`.
- Definite superlatives such as "was the first," which in copy need a source ([claims.md](claims.md#puffery-and-measurable-superlatives)).
- Honest hedges such as "perhaps" or "tends to," where the writer really is unsure.
- An occasional wordy phrase. A person sometimes writes `in order to`; the linter still suggests "to."

## Ineffective indicators

The guide names signs that prove nothing on their own. Do not rewrite a text for these reasons alone:

- Perfect grammar.
- A mix of registers.
- Bland prose, or merely fancy prose.
- Transition words, taken one at a time.
- Unsourced content. It is still a truthfulness problem ([claims.md](claims.md#evidence-before-claim)), but not a sign of machine writing.

The guide also warns that detection tools have real error rates and are easy to fool by paraphrase. Whalory does not run or quote detectors.

## Tell-to-rule map

One row per tell, with the rule that checks it. The manual checklist in `SKILL.md` groups the same ids into twenty checks.

| Tell | Rule id | Severity | Fix |
|---|---|---|---|
| AI vocabulary | `en-ai-vocab` | warning | Plain word or the fact |
| AI vocabulary density | `en-ai-vocab-density` | error | Rewrite from the facts |
| Buzzwords | `en-buzzword` | warning | What, for whom, how much |
| Inflated significance | `en-significance` | warning | Delete, or state the sourced consequence |
| Avoiding "is" | `en-copula-avoid` | warning | "is" and "are" |
| Marketing "has" | `en-marketing-has` | warning | "has" |
| Trailing -ing analysis | `en-ing-analysis` | warning | Cut, or a separate sourced sentence |
| Vague attribution | `en-vague-attribution` | error | Name and link the source |
| Canned notability | `en-media-canned` | warning | Real outlets and dates |
| `not just X, but Y` | `en-not-just` | warning | State Y |
| `it's not X, it's Y` | `en-not-x-but-y` | warning | State Y; drop the straw man |
| `no X, no Y, just Z` | `en-no-x-no-y` | warning | One plain sentence and evidence |
| Rule of three | `en-triads` | warning | Real lists of three only |
| Em dashes | `en-dash-density` | warning | Comma, colon, full stop |
| Summary opener | `en-summary-opener` | warning | End on the last concrete point |
| Challenges and outlook | `en-challenges-outlook` | warning | Specific sourced problems |
| Didactic frame | `en-didactic` | warning | State the fact |
| Chatbot residue | `en-chatbot-residue` | error | Remove |
| Sycophancy | `en-sycophancy` | error | Remove |
| Knowledge-cutoff speculation | `en-cutoff-speculation` | error | Delete; add `[source needed: …]` |
| Template residue | `en-template-residue` | error | Fill it or use a Whalory bracket |
| Chatbot markup | `en-chatbot-markup` | error | Delete and recheck the claim |
| Title case headings | `en-title-case-heading` | warning | Sentence case |
| Bold in running text | `en-bold-overuse` | warning | Remove the bold |
| Inline-header bullets | `en-inline-header-bullets` | warning | Prose or plain bullets |
| Emoji bullets and headings | `en-emoji-format` | warning | Remove |
| Mixed quotation marks | `en-quote-mix` | warning | One style (fixable) |
| Vague association | `en-vague-association` | warning | State the relation |
| Transition openers | `en-additionally` | warning | Delete or "also" |
| Stock openings | `en-cliche-open`, `en-rhetorical-open` | warning | Start with something concrete |
| `journey` talk | `en-journey` | warning | A concrete verb |
| Moral close | `en-moral-close` | warning | End on the action |
| Clickbait | `en-clickbait` | warning | Say the finding |
| Same opening word | `en-same-opening` | warning | Vary the first word |
| Flat rhythm | `en-flat-rhythm` | warning | Mix long and short |
| Heading in a caption | `en-caption-header` | warning | Start with the moment |
| Statistic without source | `en-stat-claim` | warning | Source or `[source needed: metric]` |
| Superlative | `en-superlative` | warning | Source and scope, or rewrite |
| Establishment claim | `en-establishment-claim` | error | Cite the study or remove |
| Testimonial | `en-testimonial` | warning | Verbatim, consented quotes only |
| DOI or ISBN | `en-citation-check` | warning; error for a bad ISBN | Resolve and fix |

## Review without scripts

When the assistant cannot run code, or the script fails:

1. Read the text once for errors only, using the error rows of the [tell-to-rule map](#tell-to-rule-map).
2. Read it again and count warnings by group. Three from one group means rewriting the whole text.
3. Run the [substitution test](#substitution-test).
4. Write the quality assurance (QA) line "QA: manual" in the note, or "QA: manual (script not run)" when a script failed. Name each warning you kept on purpose.

For a text that mixes English and Persian, check each line against the list for its own language. The Persian list is the [Persian catalog of tells](../fa/ai-tells.md).

## Substitution test

Swap the subject for a competitor, or the product for a different product. If the text still reads as true, it has no real detail, and the fix is structural.

```
Crafted with care for people who truly value quality.
```

That line fits a coffee roaster, a shoemaker, and a software company equally well. "Roasted on Tuesdays and shipped the same afternoon" fits one business, and only if the brief says so.

## Checklist

Linter rule ids: every id in the [tell-to-rule map](#tell-to-rule-map), especially the errors: `en-ai-vocab-density`, `en-vague-attribution`, `en-chatbot-residue`, `en-sycophancy`, `en-cutoff-speculation`, `en-template-residue`, `en-chatbot-markup`, `en-establishment-claim`.

- [ ] No error-level tell remains anywhere in the text.
- [ ] No group has three or more warnings; each kept warning is named in the note.
- [ ] Every number, study, expert, and quote has a source or a bracket.
- [ ] The text passes the substitution test.
- [ ] Headings are in sentence case; no bold in running text, no emoji bullets.
- [ ] The note says "QA: script", "QA: manual", or "QA: manual (script not run)".
