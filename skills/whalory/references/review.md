# Review checklist

Go through this list before delivering any text, from top to bottom. Each row has an "If not" column with one of three answers. "Return" means the text goes back to the writer and is not delivered. "Fix in place" means you correct it on the spot. "Note" means it goes in the internal note. To score a text, use the [scoring rubric](editor.md#scoring-rubric).

## Contents

1. Was the route right? [Diagnosis](#diagnosis)
2. Does the text move its job forward? [Goal and call to action](#goal-and-call-to-action)
3. The brand's voice: [Profile](#profile)
4. Nothing invented: [Truthfulness](#truthfulness)
5. Face to face, behind the scenes, a year later: [Ethics](#ethics)
6. Buttons and messages that don't deceive: [Dark patterns](#dark-patterns)
7. Opening, narrator, detail, ending: [Narrator and story](#narrator-and-story)
8. Verbs, rhythm, image: [Texture](#texture)
9. AI tells, spelling, punctuation: [Cleanliness](#cleanliness)
10. Length, channel, publication date: [Format and timing](#format-and-timing)
11. Links, images, errors, plain language: [Accessibility](#accessibility)
12. Script or manual checklist: [Automated checks](#automated-checks)
13. Which number judges the text: [Success metric](#success-metric)
14. Next to the benchmark text: [Final test](#final-test)

## Diagnosis

The internal note has a diagnosis line in the conversation language, such as:

```
تشخیص: کپشنِ اینستاگرام · مشتریِ تازه · پروفایل: cafe (آغاز) · بی‌پرسش · آزمون: دستی
Diagnosis: Instagram caption · first-time customer · Profile: cafe (starter) · no questions · QA: manual
```

Before polishing the text, check that line against the request. Clean text on the wrong route means doing the work twice. How to build the line: [diagnosis note](router.md#diagnosis-note). If the route was wrong, see [when detection is wrong](router.md#when-detection-is-wrong).

| Check | If not |
|---|---|
| Format and channel are what the user asked for, or a correct guess from the request | Return; route again |
| The reader is the reader of the profile or the brief | Return |
| Output language, variant, and market are right, such as `fa-IR`, `fa-AF`, `en-US`, `en-GB`, or bilingual; [output language, variant, and market](router.md#output-language-variant-and-market) | Return |
| Risk was judged correctly, and nothing about health, money, licenses, or sensitive claims slipped past | Return |
| If a question was needed and not asked, the assumptions are in the note; [question gate](intake.md) | Note |
| The note has its "Diagnosis:" line | Note |

## Goal and call to action

The text was written to do a job. Ask whether it moves that job forward or only reads well.

| Check | If not |
|---|---|
| The goal of the text fits in one sentence: sell, introduce, inform, reassure, guide | Return to the [brief](brief.md) |
| Every part of the text serves that goal, and off-topic sentences are gone | Fix in place |
| The reader knows what to do after reading, and that action takes one verb | Return |
| The call to action works in this channel. Examples: the bio link on Instagram, a button in email, a short link or code in SMS | Fix in place |
| It has one main call to action; a second one, if present, is smaller and comes after | Fix in place |
| The text's promise matches the place the call to action leads to: same price, same condition, same words | Return |
| A service message, such as a verification code or a delay notice, carries no sales call to action | Fix in place |

## Profile

| Check | If not |
|---|---|
| The right profile was found and read, or the note says none was found | Return |
| `LEARNINGS.md` next to the profile, if present, was read and its lessons applied | Return |
| The profile's settings for this format were applied, such as the sentence cap or the caption emoji limit | Fix in place |
| The brand name and fixed terms are spelled as the profile spells them | Fix in place |
| None of the profile's "avoid" words appear | Fix in place |

Profile structure and precedence: [voice profile](voice-profile.md).

## Truthfulness

| Check | If not |
|---|---|
| No story, person, quote, number, result, or memory was invented | Return |
| No superlative or exaggeration appears without evidence | Return |
| In a sensitive industry, claims and regulation for the market were checked: sensitive claims ([fa](fa/claims.md), [en](en/claims.md)) and regulation (fa (in Whalory Pro), en (in Whalory Pro)) | Return |
| Unknown details are marked with brackets | Fix in place |
| In a rewrite, no fact, number, or condition from the original was changed or dropped | Return |
| Any fiction carries the label «قصه», or "story" in English | Return |

## Ethics

The three quick tests from professional ethics ([fa](fa/ethics.md#سه-آزمونِ-سریع), [en](en/ethics.md#three-quick-tests)). A "no" to any of them sends the text back.

| Test | Question |
|---|---|
| Face to face | Could you say this sentence to this person, face to face, in the shop or the clinic? |
| Behind the scenes | If the reader saw how this text was made, would they still be fine with it? |
| A year later | If this text were read again in a year under the writer's name, would the writer still stand by it? |

Four shorter checks follow:

- The text doesn't sell with fear or shame ([fa](fa/ethics.md#ترس-و-شرم), [en](en/ethics.md#fear-and-shame)).
- If the text is paid for, as an ad or a paid partnership, the opening line says so ([fa](fa/ethics.md#شفافیتِ-تبلیغ), [en](en/ethics.md#ad-labels)).
- Real people, photos, and data appear only with permission ([fa](fa/ethics.md#رضایت-و-حریم), [en](en/ethics.md#consent-and-privacy)).
- Texts about urgency, a vulnerable reader, current news, inspiration, or data also pass the one-line test for their subject. It sits in the second table in the Persian [three quick tests](fa/ethics.md#سه-آزمونِ-سریع).

## Dark patterns

Button and message text is part of the interface design, and the writer shares the responsibility for it. The full list, with alternatives: [dark patterns in the interface](fa/ethics.md#الگوی-تاریک-در-رابط) and [confirmshaming and other dark patterns](en/ethics.md#confirmshaming-and-other-dark-patterns).

| Check | If not |
|---|---|
| Urgency and scarcity have a real reason that fits in one sentence ([fa](fa/ethics.md#فوریت-و-کمیابیِ-ساختگی), [en](en/ethics.md#fake-urgency-and-scarcity)) | The urgency is removed |
| The decline button doesn't shame the reader and says plainly «بعداً» or «نه، ممنون» ("Later", "No, thanks") | Fix in place |
| A button that takes money says so: «پرداختِ [مبلغ]» ("Pay [amount]") | Return |
| The full cost, with shipping and tax, shows on the opening page | Return |
| No box is pre-ticked for the newsletter or marketing SMS | Return |
| Canceling is as easy as signing up, and its text is visible and clear | Return |
| The options don't confuse and contain no double negatives | Fix in place |
| A «امتیاز بده» or «اعلان را روشن کن» prompt ("rate us", "turn on notifications") appears once, with a «دیگر نپرس» ("don't ask again") option | Fix in place |

If the design itself holds a dark pattern and the writer was asked only to fill in the blanks, the text is not written. The note gives the reason.

## Narrator and story

| Check | If not |
|---|---|
| The opening sentence starts with something concrete: an object, a place, a time, someone's hands at work, a sensory detail, or the news itself | Return |
| The narrator talks to one person and doesn't make the copy about itself | Fix in place |
| The point of view and the narrator's distance stay fixed | Fix in place |
| The text has concrete details | Return |
| It survives the substitution test: with a competitor's name swapped in, the text is no longer true | Return |
| Its arc fits the narrative dial and the format | Fix in place |
| The ending is short, with no moral and no summary | Fix in place |

## Texture

| Check | If not |
|---|---|
| Verbs are strong and adjectives are few | Fix in place |
| The rhythm moves between long and short sentences | Fix in place |
| Any image comes from the subject's own world | Fix in place |

## Cleanliness

| Check | If not |
|---|---|
| No pattern from the AI tells lists ([fa](fa/ai-tells.md), [en](en/ai-tells.md)) | Return |
| One tone runs through the whole text | Return |
| No dash sits in the middle of a sentence | Fix in place |
| No sentence is redundant | Fix in place |
| Persian: the zero-width non-joiner (ZWNJ), Persian «ی» and «ک», «ه‌ی», «» quotes, and Persian digits are correct | Fix in place |
| English: one spelling variant, sentence-case headings, and the profile's settings for the Oxford comma and contractions; [style guide](en/style-guide.md) | Fix in place |
| No bureaucratic words | Fix in place |

## Format and timing

| Check | If not |
|---|---|
| Length fits the format guide and the channel's limit: forms ([fa](fa/forms.md), [en](en/forms.md)) and channels ([fa](fa/channels.md), [en](en/channels.md)) | Fix in place |
| The common trap of this [format](fa/forms.md) and this industry (fa (in Whalory Pro), en (in Whalory Pro)) is absent | Fix in place |
| The publication date was checked against the occasions calendar ([fa](fa/occasions.md), [en](en/occasions.md)), and on days of mourning the tone and promotion follow that file | Return |
| Dates, money, numbers, and addresses follow the [writing conventions](fa/conventions.md) or the [English style guide](en/style-guide.md) | Fix in place |
| If the text sits in a code file, keys and placeholders are untouched; [interface microcopy](fa/forms.md#ریزمتنِ-رابط), microcopy in a repository (fa (in Whalory Pro), en (in Whalory Pro)) | Return |

## Accessibility

The short version, needed for every text.

| Check | If not |
|---|---|
| Link text makes sense on its own and isn't «این‌جا» or «کلیک کنید» ("here", "click here") | Fix in place |
| An image has alt text that says what the image does; a decorative image gets empty alt text | Fix in place |
| Color or position on the screen never carries meaning alone: «فیلدهای ستاره‌دار»، «دکمه‌ی ادامه» ("starred fields", "the Continue button") | Fix in place |
| The error message sits next to its field, names the problem, and says how to fix it | Return |
| No emoji sits mid-sentence, and no meaning is carried by emoji alone | Fix in place |
| Latin words, numbers, and addresses sit correctly in Persian text, and the paragraph order isn't scrambled | Fix in place |
| The language is plain: one idea per sentence, and each term explained at first use | Fix in place |
| Videos have captions, and audio scripts are written for the ear | Fix in place |

## Automated checks

```bash
python <skill path>/scripts/lint.py draft.txt --profile <profile> --format <format>
```

`lint.py` runs the Persian or English linter line by line. Add `--lang fa` or `--lang en` to force one, and `--facts brief.txt` to flag English facts missing from the brief.

| Check | If not |
|---|---|
| The script finished with no errors | Return |
| Each remaining warning has a reason, and the note gives it | Note |
| If code can't run, the [manual quality assurance (QA) in `SKILL.md`](../SKILL.md#manual-qa) was done. The note says "QA: manual" («آزمون: دستی»), or "QA: manual (script not run)" («آزمون: دستی (اسکریپت اجرا نشد)») | Note |

## Success metric

A text meant to do a job has a number that judges it, chosen before publication. If the number is picked after the results are in, every result looks like a win.

| Check | If not |
|---|---|
| One main metric was written down before publication, such as clicks, replies, completed forms, or fewer tickets | Note |
| The metric fits the job; views and likes don't measure it | Fix in place |
| The source of the number is known: a tagged link, a separate discount code, a support report | Note |
| In an A/B test, only one thing differs between the two versions | Return |

## Final test

Put the text next to the profile's benchmark text and read both aloud. If one sounds like a person and the other like a brochure, rewrite it.
