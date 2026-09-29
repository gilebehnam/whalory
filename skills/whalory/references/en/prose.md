# Plain English

Plain English is the default register of every English text Whalory writes, from a push notification to a pricing page. This file gives the rules for sentences, paragraphs, verbs, and words, with the thresholds `lint_en.py` checks. Each rule names its source. When a voice profile sets a different cap, the profile wins ([voice-profile.md](../voice-profile.md#precedence)). Bad examples sit in code blocks or inline code so the linter skips them.

## Contents

- [Sentences](#sentences)
- [Paragraphs](#paragraphs)
- [Active voice](#active-voice)
- [Hidden verbs](#hidden-verbs)
- [Must instead of `shall`](#must-instead-of-shall)
- [Positive language](#positive-language)
- [Noun strings](#noun-strings)
- [Abbreviations](#abbreviations)
- [Slashes](#slashes)
- [Contractions](#contractions)
- [Simple words](#simple-words)
  - [The dirty dozen](#the-dirty-dozen)
  - [Words GOV.UK avoids](#words-govuk-avoids)
- [Readability scores](#readability-scores)
- [Checklist](#checklist)

## Sentences

One idea per sentence. A sentence loaded with conditions and exceptions loses its main point, so give each part a sentence of its own. Source: [Federal Plain Language Guidelines, write short sentences](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/concise/write-short-sentences.md), checked 2026-09-27.

GOV.UK asks writers to check any sentence over 25 words. Source: [GOV.UK A to Z style guide](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), checked 2026-09-27. Whalory uses 25 words as the English default at sentence-length dial 3.

| Dial | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Longest sentence, in words | 15 | 20 | 25 | 30 | 35 |

Some formats start stricter. A format default can only tighten the general cap; a setting for that format in the profile's `formats` block overrides it.

| Format id | Word cap |
|---|---|
| `otp` | 15 |
| `caption`, `sms` | 20 |
| `subject` | 9 |
| `push`, `ui`, `headline` | 12 |
| `error` | 16 |

In Markdown, each list item, heading, and table cell counts as its own sentence. The rule id is `en-long-sentence`.

```
If your order has not arrived within ten business days of the dispatch date shown in your confirmation email, and you have checked with your neighbors, please contact us.
```

"Has it been ten business days since dispatch? The dispatch date is in your confirmation email. If your order still isn't there and your neighbors don't have it, please contact us."

The rewrite keeps every fact and condition. That means ten business days, the dispatch date, the confirmation email, the check with the neighbors, and the request to get in touch. A shorter version that drops the neighbor check changes what the customer must do first ([style-repair.md](style-repair.md#facts)).

## Paragraphs

The plain-language guidelines recommend paragraphs of no more than 150 words in three to eight sentences, and never longer than 250 words. A one-sentence paragraph now and then is fine. Vary the lengths so the page does not read in blocks. Source: [Federal Plain Language Guidelines, write short paragraphs](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/concise/write-short-paragraphs.md), checked 2026-09-27.

One topic per paragraph. The rule id is `en-long-paragraph`, which warns above 150 words.

## Active voice

Name the actor. In an active sentence, the person or company acting is the subject. Passive sentences often hide who does what. Source: [Federal Plain Language Guidelines, use active voice](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/conversational/use-active-voice.md), checked 2026-09-27. Mailchimp and Google ask for the active voice too. Sources: [Mailchimp Content Style Guide: grammar and mechanics](https://styleguide.mailchimp.com/grammar-and-mechanics/) and [Google developer documentation style guide, highlights](https://developers.google.com/style/highlights), both checked 2026-09-27.

| Passive | Active |
|---|---|
| `Your refund will be processed.` | We'll process your refund. |
| `Mistakes were made in your invoice.` | We made mistakes on your invoice. |
| `The form must be signed.` | You need to sign the form. |

The active version names the actor and adds nothing else. When the reader needs more, such as when the refund arrives or what went wrong, ask for it: `[confirm: refund time]`, `[confirm: what was wrong on the invoice]`.

The passive is right when the actor does not matter or is unknown. It also fits when a rule acts on its own, as in "Your account is locked after five failed attempts." The linter warns when more than `20%` of sentences in a text of five or more sentences are passive (`en-passive`).

## Hidden verbs

A hidden verb is a verb turned into a noun, which then needs a helper verb. Watch for endings such as -ment, -tion, -sion, and -ance, and for helper verbs such as make, give, take, reach, and achieve. Source: [Federal Plain Language Guidelines, avoid hidden verbs](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/words/avoid-hidden-verbs.md), checked 2026-09-27.

| Hidden | Plain |
|---|---|
| `conduct an analysis of` | analyze |
| `make a decision` | decide |
| `provide assistance` | help |
| `make an application` | apply |
| `carry out a review of` | review |

The rule id is `en-hidden-verb`.

## Must instead of `shall`

Use "must" for a requirement and "must not" for a prohibition. The word `shall` is ambiguous and rare in everyday speech. Source: [Federal Plain Language Guidelines, words for requirements](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/conversational/shall-and-must.md), checked 2026-09-27. GOV.UK also uses "must" for legal requirements. Source: [GOV.UK, clear language](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-language/), checked 2026-09-27.

Quoted legal text keeps its own wording; put it in quotation marks and do not rewrite it. The rule id is `en-shall`.

## Positive language

Two negatives in one sentence make the reader switch from no to yes. Say the positive version. Source: [Federal Plain Language Guidelines, use positive language](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/concise/use-positive-language.md), checked 2026-09-27.

| Double negative | Positive |
|---|---|
| `no fewer than` | at least |
| `is not ... unless` | is ... only if |
| `may not ... until` | may ... only when |
| `not uncommon` | common, or give the number |

The rule id is `en-double-negative`.

## Noun strings

More than three nouns in a row make readers think they have found the noun while they are still reading modifiers. Open the string with prepositions and articles. Source: [Federal Plain Language Guidelines, avoid noun strings](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/words/avoid-noun-strings.md), checked 2026-09-27.

```
customer account security settings update page
```

"The page where you update your account's security settings."

## Abbreviations

- Explain an abbreviation the first time you use it on a page, then use the short form. GOV.UK uses no full stops inside abbreviations: `BBC`, not `B.B.C.` Source: [GOV.UK A to Z style guide](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), checked 2026-09-27.
- A short name often beats an abbreviation: "the committee" instead of a string of capitals. The plain-language guidelines suggest no more than three abbreviations in one document, and preferably two. Source: [Federal Plain Language Guidelines, minimize abbreviations](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/words/minimize-abbreviations.md), checked 2026-09-27.
- Well-known abbreviations need no expansion. The linter keeps an allowlist that includes API, URL, PDF, FAQ, UK, EU, AI, SMS, and SEO. It warns on the first unexplained use of any other abbreviation in texts of 80 words or more (`en-undefined-abbr`).
- Plural abbreviations take a plain "s": APIs, not `API's`. Source: [Google developer documentation style guide, abbreviations](https://developers.google.com/style/abbreviations), checked 2026-09-27.

## Slashes

Write `and/or` as "a or b or both," or pick the one that is true. Source: [Federal Plain Language Guidelines, use simple words and phrases](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/words/use-simple-words-phrases.md), checked 2026-09-27. GOV.UK does not use a slash in place of "or." Source: [GOV.UK A to Z style guide](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), checked 2026-09-27. A slash between two words usually means the writer has not chosen.

| Slash | Plain |
|---|---|
| `Sign in/Log in` | Sign in (one term everywhere) |
| `his/her` | their |
| `pickup and/or delivery` | pickup, delivery, or both |

Units such as km/h and paths in code are not slashes of this kind. The rule id is `en-slash`, and it is off for the `ui` format.

## Contractions

Contractions make copy sound like speech. Sources disagree on how far to go, so the profile decides.

| Source | Rule |
|---|---|
| [Federal Plain Language Guidelines](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/conversational/use-contractions.md) | Use them wherever they sound natural, not wherever possible |
| [Microsoft Writing Style Guide, top 10 tips](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice) | Use them to sound friendly |
| [Mailchimp](https://styleguide.mailchimp.com/grammar-and-mechanics/) | Contractions are encouraged |
| [GOV.UK A to Z](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/) | Avoid negative contractions such as `can't` and conditional ones such as `should've`, because many users misread them |

All four sources were checked 2026-09-27. The profile key `contractions` takes three values:

- `use`: contract where speech would. In captions, posts, email, UI, bots, and replies the linter flags stiff forms such as `we will` (`en-no-contraction`).
- `avoid`: no contractions at all (`en-contraction`). Legal and very formal brands choose this.
- `positive-only`: "you'll" and "we're" are fine; negatives are spelled out, so "cannot" and "do not" (`en-contraction`). This is the GOV.UK rule.

## Simple words

Use the short, common word. "Buy," not `purchase`; "help," not `assist`; "about," not `approximately`. Source: [GOV.UK, clear language](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-language/), checked 2026-09-27. The linter maps long words to short ones with `en-complex-word` and flags stock metaphors with `en-metaphor-buzz`.

### The dirty dozen

These substitutions come from the Federal Plain Language Guidelines. Source: [use simple words and phrases](https://github.com/GSA/plainlanguage.gov/blob/main/_pages/guidelines/words/use-simple-words-phrases.md), checked 2026-09-27.

| Instead of | Use |
|---|---|
| `addressees` | you |
| `assist`, `assistance` | help |
| `commence` | begin, start |
| `implement` | carry out, start |
| `in accordance with` | by, following, under |
| `in order that` | for, so |
| `in the amount of` | for |
| `in the event of` | if |
| `it is` (as an empty opener) | leave it out |
| `promulgate` | issue, publish |
| `this activity`, `this command` | us, we |
| `utilize`, `utilization` | use |

The same guidelines add more pairs: `facilitate` becomes "help" or "ease," `prior to` becomes "before," `numerous` becomes "many," `sufficient` becomes "enough," and `in order to` becomes "to."

### Words GOV.UK avoids

GOV.UK lists words that hide meaning, with the replacement it prefers. Source: [GOV.UK A to Z style guide, words to avoid](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), checked 2026-09-27.

| Avoid | Say instead |
|---|---|
| `collaborate`, `liaise` | work with |
| `deliver` (for abstract things such as improvements) | make, create, provide |
| `deploy` (unless military or software) | use, build |
| `empower` | allow, give permission |
| `facilitate` | say how you are helping, for example "run" a workshop |
| `foster` (unless about children) | encourage, help |
| `impact` (unless a collision) | have an effect on, influence |
| `key` (unless it opens a lock) | important, or leave it out |
| `leverage` (unless financial) | influence, use |
| `robust` (unless a sturdy object) | well thought out, comprehensive |
| `streamline` | simplify |
| `tackle` | stop, solve, deal with |
| `transform` | describe the change |
| `going forward`, `moving forward` | from now on, in the future |
| `one-stop shop`, `hub`, `portal` | website, service |

GOV.UK spells some of these the British way, for example `utilise`; the list above uses the US form of each word.

## Readability scores

The linter reports two scores. They come from the same inputs: words per sentence and syllables per word.

| Score | Formula | Reading |
|---|---|---|
| Flesch Reading Ease (FRE) | `206.835 - 1.015 × (words ÷ sentences) - 84.6 × (syllables ÷ words)` | Higher is easier; 60 to 70 reads as plain English |
| Flesch-Kincaid Grade Level (FKGL) | `0.39 × (words ÷ sentences) + 11.8 × (syllables ÷ words) - 15.59` | A US school grade |

Sources: [Wikipedia, Flesch-Kincaid readability tests](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests), and for the grade formula [Kincaid and colleagues, Navy research report 8-75 (1975)](https://stars.library.ucf.edu/istlibrary/56/), both checked 2026-09-27.

How Whalory uses them:

- The grade target is `reading_grade_max` from the profile. When that key is empty, the jargon dial sets the target:

  | Jargon dial | 1 | 2 | 3 | 4 | 5 |
  |---|---|---|---|---|---|
  | Grade target | 6 | 8 | 10 | 12 | 14 |

- For health copy and for readers of the general public, aim for grade 8 or lower. An Institute of Medicine workshop recommended grade 8 or lower for informed-consent documents. Source: [National Cancer Institute (NCI), reading level tools](https://dctd.cancer.gov/research/ctep-trials/trial-development/reading-level-tools.pdf), checked 2026-09-27.
- The checks run on texts of 100 words or more, in long formats such as landing, about, blog, email, product, press, and reply. The rule ids are `en-readability-grade` and `en-readability-fre` (warning below 30).

What the scores miss: the same NCI document says the formulas are accurate to about 1.5 grade levels. They ignore vocabulary familiarity, concept density, layout, and cultural fit, and they need complete sentences, so lists and fragments distort them. Never write to the score. Short words alone do not make a text clear; fix the sentence, then read the score again.

## Checklist

Linter rule ids: `en-long-sentence`, `en-long-paragraph`, `en-passive`, `en-hidden-verb`, `en-shall`, `en-double-negative`, `en-undefined-abbr`, `en-slash`, `en-contraction`, `en-no-contraction`, `en-complex-word`, `en-metaphor-buzz`, `en-readability-grade`, `en-readability-fre`.

- [ ] Every sentence holds one idea and stays under the cap for its format.
- [ ] Paragraphs stay under 150 words, with one topic each.
- [ ] Each sentence names its actor, unless the actor truly does not matter.
- [ ] Requirements use "must" and "must not."
- [ ] No double negatives, no noun strings of four or more, no `and/or`.
- [ ] Each abbreviation is explained at first use or is on the allowlist.
- [ ] Contractions follow the profile value.
- [ ] Long words were swapped for short ones.
- [ ] The reading grade is within the target, and the fix came from the sentences, not from gaming the score.
