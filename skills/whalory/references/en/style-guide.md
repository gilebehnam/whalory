# Style guide

This file covers the mechanics of English copy: spelling by variant, commas, numbers, money, dates, dashes, capitals, quotes, and loud marks. Style guides disagree on many of these points, so each rule names the guides behind it. The brand's profile picks the variant and, when it wants one, a house style ([voice-profile.md](../voice-profile.md#the-json-file-key-by-key)). Without a profile, Whalory writes `en-US` with US spelling and the Oxford comma. British spellings appear only in inline code in this file, so that the file itself stays in one variant.

## Contents

- [Variants](#variants)
- [US and UK spelling](#us-and-uk-spelling)
- [Oxford comma](#oxford-comma)
- [Numbers](#numbers)
- [Money and percentages](#money-and-percentages)
- [Measurements](#measurements)
- [Phone numbers](#phone-numbers)
- [Dates and times](#dates-and-times)
- [Ranges](#ranges)
- [Dashes](#dashes)
- [Sentence-case headings](#sentence-case-headings)
- [Curly and straight quotes](#curly-and-straight-quotes)
- [Ampersands](#ampersands)
- [Latin abbreviations](#latin-abbreviations)
- [Link text](#link-text)
- [Exclamation marks](#exclamation-marks)
- [Emoji](#emoji)
- [House-style presets](#house-style-presets)
- [Checklist](#checklist)

## Variants

Whalory writes eight English variants, named with their language tags.

| Tag | Market | Spelling the linter derives |
|---|---|---|
| `en-US` | United States | `us` |
| `en-GB` | United Kingdom | `uk` |
| `en-AU` | Australia | `uk` |
| `en-CA` | Canada | `uk-ize` |
| `en-NZ` | New Zealand | `uk` |
| `en-IE` | Ireland | `uk` |
| `en-IN` | India | `uk` |
| `en-ZA` | South Africa | `uk` |

The router picks the variant from the target channel or market first, then the profile's `variant`, then the default `en-US` ([router.md](../router.md#output-language-variant-and-market)). A profile can set `spelling` directly to `us`, `uk`, or `uk-ize`. The last one is the Canadian pattern: British `-our` and `-re` with -ize, as in `colour`, `centre`, and organize. Canadian English also generally prefers analyze, program, and tire, so the linter treats those forms as neutral under `uk-ize`. Source: [Wikipedia: American and British English spelling differences](https://en.wikipedia.org/wiki/American_and_British_English_spelling_differences), revision 1376796299, checked 2026-09-28. When neither the variant nor `spelling` is known, the linter follows the majority form in the document and only checks that the text does not mix.

Market is a separate slot from variant. An English tagline for a bakery in Berlin is written in the default `en-US`. Its market slot reads `unknown`, because Whalory has no file for German rules, and the note names Germany ([router-examples.md](../router-examples.md#8-english-tagline-for-a-berlin-bakery)).

## US and UK spelling

The main spelling families, from the Wikipedia survey of American and British spelling. Source: [Wikipedia: American and British English spelling differences](https://en.wikipedia.org/wiki/American_and_British_English_spelling_differences), revision 1376796299, checked 2026-09-27.

| Family | US | UK |
|---|---|---|
| -or, -our | color, behavior, favor, flavor, neighbor | `colour`, `behaviour`, `favour`, `flavour`, `neighbour` |
| -er, -re | center, theater, fiber, liter | `centre`, `theatre`, `fibre`, `litre` |
| -ize, -ise | organize, recognize, prioritize, customize | `organise`, `recognise`, `prioritise`, `customise` |
| -yze, -yse | analyze, paralyze | `analyse`, `paralyse` |
| doubled l | traveled, canceled, labeled, modeling | `travelled`, `cancelled`, `labelled`, `modelling` |
| single l | fulfillment, enrollment, installment | `fulfilment`, `enrolment`, `instalment` |
| -og, -ogue | catalog, analog | `catalogue`, `analogue` |
| -se, -ce | defense, offense, license (noun) | `defence`, `offence`, `licence` (noun) |
| ae, oe | pediatric, anemia, estrogen | `paediatric`, `anaemia`, `oestrogen` |
| dropped e | aging, likable, sizable | `ageing`, `likeable`, `sizeable` |
| single words | gray, aluminum, percent | `grey`, `aluminium`, `per cent` |

Points the same source makes:

- The -ize ending is also correct British English. The Oxford English Dictionary and Oxford University Press recommend it, a practice called Oxford spelling. GOV.UK still requires the -ise forms.
- Some words take -ise everywhere: advise, compromise, exercise, promise, revise, supervise, surprise. Some take -ize everywhere: capsize, seize, size.
- The -yze words have no Oxford exception: British English writes `analyse` even with Oxford spelling.
- British English uses `practise` and `license` as verbs and `practice` and `licence` as nouns. US English writes practice and license for both.
- US style puts periods and commas inside closing quotation marks; British style follows the sense.

Two rules for copy:

1. One variant per document. Both forms of any family in one text is an error (`en-spelling-mix`). A quotation in another variant keeps its spelling and sits in quotation marks.
2. Normalize to the profile's spelling. The linter can fix forms off the variant (`en-spelling-variant`, fixable). It skips pairs whose right form depends on meaning: program and `programme`, check and `cheque`, tire and `tyre`, license and `licence`, practice and `practise`, and meter and `metre`.

## Oxford comma

The Oxford (serial) comma is the comma before "and" or "or" at the end of a list of three or more: "flour, water, and salt."

| Guide | Rule | Source (checked 2026-09-27) |
|---|---|---|
| Chicago Manual of Style | Required (6.19) | [Chicago's Shop Talk blog](https://cmosshoptalk.com/2020/02/11/oxford-chicago-and-the-serial-comma/) |
| Microsoft | Use it ("Remember the last comma") | [Microsoft top 10 tips](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice) |
| Google developer docs | Use it | [Google style highlights](https://developers.google.com/style/highlights) |
| Mailchimp | Use it | [Mailchimp grammar and mechanics](https://styleguide.mailchimp.com/grammar-and-mechanics/) |
| Associated Press (AP) Stylebook | Only when needed to avoid ambiguity | [Purdue Online Writing Lab (OWL), AP style](https://owl.purdue.edu/owl/subject_specific_writing/journalism_and_journalistic_writing/ap_style.html) |

The profile key `oxford_comma` sets the rule. With `true` the linter flags a missing comma, with `false` it flags a present one, and with `null` it only flags a document that mixes both (`en-oxford-comma`). Whalory's own English voice uses the comma.

## Numbers

| Guide | Spell out | Numerals |
|---|---|---|
| AP | one to nine | 10 and up |
| Microsoft | zero through nine in body text | 10 and up; always for measurements, percentages, and UI input |
| Chicago | zero through one hundred, and certain round multiples, in nontechnical text | Other numbers |
| GOV.UK | "one" in phrases such as "one or two of them" | Everything else, including 2 to 9 |
| Mailchimp | A number that starts a sentence | Everything else |

Sources, all checked 2026-09-27:

- [Purdue OWL, AP style](https://owl.purdue.edu/owl/subject_specific_writing/journalism_and_journalistic_writing/ap_style.html)
- [Microsoft, numbers](https://learn.microsoft.com/en-us/style-guide/numbers)
- [Chicago Manual of Style Q&A on section 9.2](https://www.chicagomanualofstyle.org/qanda/data/faq/topics/Numbers/faq0012.html)
- [GOV.UK A to Z, numbers](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/)
- [Mailchimp grammar and mechanics](https://styleguide.mailchimp.com/grammar-and-mechanics/)

Rules the guides share, with the same sources:

- Do not start a sentence with a numeral. Spell it out or add a word before it: "More than 10 stores" or "Eleven stores." GOV.UK allows a numeral at the start of a title or subheading, and so does Whalory. A headline such as "7 checks before you sign a lease" is fine; a body sentence never opens with a numeral.
- Use commas in numbers of four or more digits: 1,000 and 9,000. Microsoft leaves years, pixels, and baud rates without a comma until five digits.
- Keep one style inside a group. If one item needs a numeral, use numerals for the whole group (Microsoft).
- Write `7 million` or the full number, not `7M`. Microsoft allows K, M, and B only in UI where space is short.

Whalory's default for marketing copy is numerals for anything a reader might compare or act on: prices, sizes, times, and counts. Set `house_style` when the brand follows AP, Microsoft, or Chicago, and the linter checks spelled-out small numbers (`en-numeral-style`). The start-of-sentence check runs for every style (`en-numeral-start`). It skips headings, table cells, list items, and quotations, and it is off for the `headline`, `otp`, `ui`, and `sms` formats, where a numeral may open the line.

## Money and percentages

- Whole amounts take no decimals: £75, not `£75.00`; £75.50 when pence are included. Source: [GOV.UK A to Z, money](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), checked 2026-09-27.
- When the currency could be unclear, Microsoft puts the currency code before the amount with no space, as in `USD1.42 billion`. When it is clear, the symbol is enough. Currency names are lowercase: US dollar, euro. Source: [Microsoft, currency](https://learn.microsoft.com/en-us/style-guide/global-communications/currency), checked 2026-09-27.
- Never convert a price silently. A price quoted for one market is restated only with the currency and a note, as transcreation.md (in Whalory Pro) sets out for Persian prices.
- Use the % sign with numerals, with no space: `20%`. AP has allowed the sign with numerals since 2019, and GOV.UK, Mailchimp, and Microsoft use it too. Sources, all checked 2026-09-27: [Poynter on the AP change](https://www.poynter.org/reporting-editing/2019/ap-says-the-percentage-sign-now-ok-when-used-with-a-numeral-thats-shift5/), [GOV.UK A to Z](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), [Mailchimp](https://styleguide.mailchimp.com/grammar-and-mechanics/), [Microsoft, percent](https://learn.microsoft.com/en-us/style-guide/a-z-word-list-term-collections/p/percent-percentage).
- Microsoft does not start a sentence with the % sign and writes "percentage" when no number is given.

Price claims, reference prices, and "free" have their own rules in [claims.md](claims.md#price-claims).

## Measurements

| Point | GOV.UK | Microsoft |
|---|---|---|
| Numerals | Always | Always, even below 10 |
| Space before an abbreviated unit | No space: `3,500kg` | A space: 3 cm |
| First mention | Spell out a unit of more than one word, then abbreviate | Examples show both forms, such as "3 centimeters" and "3 cm" |
| Temperature | Celsius | No rule on the numbers page |

Sources, checked 2026-09-27: [GOV.UK A to Z, measurements](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/) and [Microsoft, numbers](https://learn.microsoft.com/en-us/style-guide/numbers).

Give the units the reader's market uses. When you convert a size or weight, keep the original figure next to it. Round so that the converted figure never promises more than the original. For a weight or volume the buyer receives, round down: 500 g is 17.6 oz, not 18 oz. A product sheet from the brand beats any conversion you do yourself; if the sheet is missing, use a bracket: `[confirm: weight in ounces]`.

## Phone numbers

- GOV.UK puts a label such as "Telephone:" before the number and separates the area, mobile, or international code from the rest. Its examples include `020 7946 0457` and `+44 (0)29 2018 0542`. Source: [GOV.UK A to Z, telephone numbers](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), checked 2026-09-27.
- For the United States and Canada, Microsoft separates the parts with hyphens only, as in 612-555-0175. For other regions it defers to each region's localization guide. Source: [Microsoft, numbers](https://learn.microsoft.com/en-us/style-guide/numbers), checked 2026-09-27.
- For readers in several countries, write the number in international form with the plus sign and country code.
- Copy the number from the brand's own records, digit by digit. A number Whalory does not have stays in a bracket: `[confirm: phone number]`.

## Dates and times

| Point | US (Microsoft) | UK (GOV.UK) |
|---|---|---|
| Date | June 12, 2026 | 12 June 2026, no comma |
| Month | Spelled out | Spelled out; short forms only in tables |
| Time | 10:45 AM, with AM or PM | `5:30pm` |
| Noon and midnight | "noon" and "midnight," not 12:00 | "midday"; `11:59pm` when "midnight" could mean two days |
| Time zone | Include it for events | Add "UK time" for readers outside the UK |

Sources, checked 2026-09-27: [Microsoft: time and place](https://learn.microsoft.com/en-us/style-guide/global-communications/time-place), [Microsoft, numbers](https://learn.microsoft.com/en-us/style-guide/numbers), and [GOV.UK A to Z: dates and times](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/). AP abbreviates some months before a specific date, such as Jan. and Aug. Source: [Purdue OWL, AP style](https://owl.purdue.edu/owl/subject_specific_writing/journalism_and_journalistic_writing/ap_style.html), checked 2026-09-27.

In `en-US` copy, Whalory writes times the AP way: 9 a.m. and 5:30 p.m. are right. That means a numeral, a space, and lowercase letters with periods. It drops `:00`, and it writes "noon" and "midnight" in words. Source: [Purdue OWL, AP style](https://owl.purdue.edu/owl/subject_specific_writing/journalism_and_journalistic_writing/ap_style.html), checked 2026-09-28. With `house_style: microsoft`, write 10:45 AM and 5:00 PM, as in the table. `en-GB` copy follows GOV.UK: `9am` and `5:30pm`. Other variants follow the brand's own habit, or GOV.UK when there is none. In an SMS, where every character counts, the compact `3:30pm` is fine in any variant.

- Never write an all-numeric date in copy. Microsoft notes that `6/12/2017` can mean June 12 or December 6 depending on the country (`en-numeric-date`).
- Check that the weekday matches the date before you publish. A right date next to the wrong weekday sends people on the wrong day.
- Avoid seasons for deadlines. Summer in the northern hemisphere is winter in the southern one, so Microsoft names months or quarters instead.
- For a deadline, GOV.UK writes "on or before" a date. Times for an international audience carry a time zone.

Occasion dates follow their own rules in [occasions.md](occasions.md#where-dates-come-from).

## Ranges

- Use "to" in ranges: "500 to 900," "10 a.m. to 11 a.m.," and "Monday to Friday." GOV.UK writes the times as `10am to 11am`. Source: [GOV.UK A to Z](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), checked 2026-09-27.
- Microsoft writes "from 9 through 17" for number ranges and "to" for time ranges. It keeps the en dash for page ranges, and for tables and UI where space is short. It never writes "from" before an en dash range. Source: [Microsoft, numbers](https://learn.microsoft.com/en-us/style-guide/numbers), checked 2026-09-27.
- Microsoft's "through" also makes an inclusive end date clear in US copy: "Sale runs June 1 through June 7."

The linter checks hyphen ranges when the house style is `govuk` or `microsoft` (`en-range-hyphen`).

## Dashes

Whalory's copy does not put a dash in the middle of a sentence. This is one of the machine patterns the method bans in every language ([three rules](../../SKILL.md#three-rules-that-never-change)). Use a comma, a colon, parentheses, or a full stop.

When a dash stays, for example inside a quoted title, the house style decides its spacing:

| Style | Em dash |
|---|---|
| Chicago, Microsoft, Mailchimp | Closed: `word—word` |
| AP | Spaced: `word — word` |

Microsoft also warns that too many em dashes hurt readability. Sources, checked 2026-09-27:

- [Microsoft: dashes and hyphens](https://learn.microsoft.com/en-us/style-guide/punctuation/dashes-hyphens/)
- [Mailchimp grammar and mechanics](https://styleguide.mailchimp.com/grammar-and-mechanics/)
- [AP vs. Chicago on em dashes](https://apvschicago.com/2011/05/em-dashes-and-ellipses-closed-or-spaced.html)

- Never use a hyphen or a double hyphen as a dash (`en-dash-spacing`, fixable).
- More than one em dash per 150 words, or per paragraph, is a warning (`en-dash-density`). The reasons are in [ai-tells.md](ai-tells.md#em-dash-density).

## Sentence-case headings

Capitalize only the first word and proper nouns in headings, buttons, menu items, and ads: "Track your order," not `Track Your Order`.

| Guide | Rule | Source (checked 2026-09-27) |
|---|---|---|
| Microsoft | Sentence case; "When in doubt, don't capitalize" | [Microsoft top 10 tips](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice) |
| Google developer docs | Sentence case for titles and headings | [Google style highlights](https://developers.google.com/style/highlights) |
| GOV.UK | Sentence case, even in page titles and service names | [GOV.UK A to Z](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/) |
| Material Design 3 | Sentence case in UI text | [Material Design 3, writing guidelines](https://m3.material.io/foundations/content-design/style-guide/ux-writing-best-practices) |
| Mailchimp | Sentence case for headings and buttons; title case for page titles and global navigation | [Mailchimp, web elements](https://styleguide.mailchimp.com/web-elements/) |
| Apple | One capitalization style per type of UI element, applied consistently; Apple's own menus and buttons use title case | [Apple Human Interface Guidelines, writing](https://developer.apple.com/design/human-interface-guidelines/writing) |
| Chicago | Title case for titles of works; the 18th edition renamed "headline style" to "title case" | [Chicago, what's new](https://www.chicagomanualofstyle.org/help-tools/what-s-new.html) |

Headings end without a full stop or colon (`en-heading-punct`, fixable), as Microsoft's top 10 tips also say. The title-case check (`en-title-case-heading`) is off only when the house style is `chicago`. AP headlines use sentence case, so the check stays on for `ap`.

## Curly and straight quotes

- Use one style of quotation marks and apostrophes per document. Mixing straight and curly marks in one text is a warning, and the linter can normalize to the majority style (`en-quote-mix`, fixable).
- Microsoft uses straight quotation marks. In US style, the closing mark comes after a comma or period; British style places it by sense. Sources: [Microsoft, quotation marks](https://learn.microsoft.com/en-us/style-guide/punctuation/quotation-marks) and [Wikipedia, spelling differences](https://en.wikipedia.org/wiki/American_and_British_English_spelling_differences), both checked 2026-09-28.
- House rule for `en-US`: commas and periods go inside the closing quotation mark, in Whalory's own files and in the copy it writes. The exception is a literal string that the reader must type or match exactly, where a stray period would change it. Examples are a search term, a keyword, a code, a command, or a field value such as `QA: manual`. There the punctuation stays outside. Interface labels quoted as examples of wording follow the main rule: "Delete project," not "Yes." Google's developer style guide has the same exception for literal strings. Source: [Google developer documentation style guide, quotation marks](https://developers.google.com/style/quotation-marks), checked 2026-09-28. British variants place the punctuation by sense.
- GOV.UK uses single quotes for UI labels and unusual terms, and double quotes only for words someone actually said or wrote. Source: [GOV.UK A to Z](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), checked 2026-09-27.
- A mix of curly and straight marks is also one of the signs of pasted machine text ([ai-tells.md](ai-tells.md#style-tells)).

## Ampersands

Write "and" in running text and headings. Keep `&` only when it is part of a brand or company name as registered, or a logo. Sources, checked 2026-09-27: [GOV.UK A to Z](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), [Microsoft, ampersand](https://learn.microsoft.com/en-us/style-guide/a-z-word-list-term-collections/a/ampersand), and [Mailchimp](https://styleguide.mailchimp.com/grammar-and-mechanics/). The rule id is `en-ampersand`, off for `ui` and `headline`, where space is tight.

## Latin abbreviations

Instead of `e.g.`, `i.e.`, and `etc.`, write "for example," "such as," or "that is." GOV.UK notes that screen readers can read `eg` aloud as "egg," and that `ie` is not always understood. Microsoft does not use `e.g.` either. Sources, checked 2026-09-27: [GOV.UK A to Z](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/) and [Microsoft, eg](https://learn.microsoft.com/en-us/style-guide/a-z-word-list-term-collections/e/eg). The linter checks this only for the `govuk` house style (`en-latin-abbr`); Whalory avoids the abbreviations in all copy.

## Link text

The link text names the destination and makes sense read on its own: "See delivery times," not `Click here`. Mailchimp never uses "click here" and does not link a leading article, and Google asks for descriptive link text. Sources, checked 2026-09-27: [Mailchimp, web elements](https://styleguide.mailchimp.com/web-elements/) and [Google style highlights](https://developers.google.com/style/highlights). The rule id is `en-link-text`. Interface rules for links, buttons, and alt text are in ux-strings.md (in Whalory Pro).

## Exclamation marks

- Mailchimp uses them sparingly, never more than one at a time, and never in failure messages. Google's style guide avoids them. Microsoft saves them "for when they count." Sources, checked 2026-09-27: [Mailchimp](https://styleguide.mailchimp.com/grammar-and-mechanics/), [Google: voice and tone](https://developers.google.com/style/tone), [Microsoft, exclamation points](https://learn.microsoft.com/en-us/style-guide/punctuation/exclamation-points).
- Whalory's default is zero (`exclaim_max: 0`). The profile can raise it.
- Two in a row is always an error. More than the profile allows is a warning, and so is any exclamation mark in an error message or a hard message (`en-bangs`).

## Emoji

- Mailchimp uses emoji "infrequently and deliberately." Source: [Mailchimp](https://styleguide.mailchimp.com/grammar-and-mechanics/), checked 2026-09-27.
- Microsoft keeps emoji out of serious topics. It never uses one in place of a word, in the middle of a sentence, or as a bullet. Its general limit is three per post. Screen readers read each emoji's name aloud, and not every screen reader supports them, so the meaning must survive without them. Source: [Microsoft, emoji](https://learn.microsoft.com/en-us/style-guide/a-z-word-list-term-collections/e/emoticons-emoji), checked 2026-09-27.
- Whalory's default is zero (`emoji_max: 0`). A profile or format can allow more; captions often do.
- One emoji in an SMS changes its encoding and cuts a single message from 160 characters to 70 ([channels.md](channels.md#sms)).

The rule ids are `en-emoji` for the count and `en-emoji-format` for emoji at the start of a bullet or heading.

## House-style presets

The profile key `house_style` switches on the rules of one published guide. Leave it `null` unless the brand has adopted a guide.

| Value | What changes in the linter |
|---|---|
| `null` | Defaults: sentence-case headings, closed em dash, no numeral-style check |
| `chicago` | Numbers below 100 in words (`en-numeral-style`); title-case check off |
| `ap` | Spell out one to nine (`en-numeral-style`); spaced em dash expected (`en-dash-spacing`); headings stay in sentence case. Set `oxford_comma: false` if the brand follows AP's simple-series rule |
| `microsoft` | One to nine in words (`en-numeral-style`); ranges with "to" or "through" (`en-range-hyphen`) |
| `google` | Defaults |
| `govuk` | Ranges with "to" (`en-range-hyphen`); no Latin abbreviations (`en-latin-abbr`); negative contractions spelled out (`en-contraction`); set `spelling` to `uk` |
| `mailchimp` | Defaults |

## Checklist

Linter rule ids: `en-spelling-mix`, `en-spelling-variant`, `en-oxford-comma`, `en-numeral-style`, `en-numeral-start`, `en-numeric-date`, `en-range-hyphen`, `en-dash-spacing`, `en-dash-density`, `en-title-case-heading`, `en-heading-punct`, `en-quote-mix`, `en-ampersand`, `en-latin-abbr`, `en-link-text`, `en-bangs`, `en-emoji`, `en-emoji-format`, `en-double-space`.

- [ ] One variant and one spelling throughout, matching the profile or `en-US`.
- [ ] Serial commas follow `oxford_comma`, and the document never mixes both styles.
- [ ] Numbers follow the house style; no body sentence opens with a numeral.
- [ ] Prices keep their currency, and no amount was converted without a note.
- [ ] Dates are spelled out for the variant, times follow the variant's form (9 a.m. in `en-US`), and each weekday matches its date.
- [ ] Ranges use "to" or "through."
- [ ] No dash in the middle of a sentence.
- [ ] Headings and buttons are in sentence case, without a final full stop or colon.
- [ ] One quote style, with commas and periods inside the closing mark in `en-US` except after a literal string; "and" instead of `&`; no `e.g.` or `i.e.`
- [ ] Link text names its destination.
- [ ] Exclamation marks and emoji stay within the profile's caps.
