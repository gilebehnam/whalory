# Short forms

Each short form has a job, a length, a shape, and a trap that catches most drafts. This file sets out the structure of each English short form, with one before-and-after pair. Fill every slot in a template with real material; a slot with no material stays a bracket, such as `[confirm: weight]`. The examples use a fictional bakery and a fictional software company. The details in each "after" version stand for facts that would come from a brief. Longer forms are listed in [where other forms live](#where-other-forms-live).

## Contents

- [Caption](#caption)
- [Product blurb](#product-blurb)
- [About page](#about-page)
- [Customer reply](#customer-reply)
- [UI microcopy](#ui-microcopy)
- [Error, empty, and wait states](#error-empty-and-wait-states)
- [Headline](#headline)
- [Where other forms live](#where-other-forms-live)
- [Checklist](#checklist)

## Caption

| Part | Rule |
|---|---|
| Job | Put the reader in one moment. The full explanation lives somewhere else. |
| Length | One to three sentences; the `caption` format caps a sentence at 20 words |
| Shape | The moment, one concrete detail, then one small call to action |
| Trap | A heading or bold title line, stacked emoji, hashtags inside sentences, "link in bio" as the opening |

```
[moment or detail], [place or time].
[one short line: a tip, a result, or the next step]
```

Put the point, and any "Ad" label, in the first line: a long caption is cut off behind "more" ([channels.md](channels.md#instagram)). Hashtags go at the end.

```
✨ Introducing Our New Autumn Menu! ✨ We're so excited to share our delicious seasonal creations with you. Come visit us today! #bakery #autumn #delicious
```

"The first pumpkin loaf of the year came out at 6 this morning. By 9 there were two left on the counter."

## Product blurb

| Part | Rule |
|---|---|
| Job | Tell the reader what this is, who it is for, and what to do with it |
| Length | Three to six sentences, in two or three short paragraphs |
| Shape | What it is; who it is for; one proof; one next step |
| Trap | A list of features, stacked adjectives, an opening of `This product` |

```
[name]: [what it is, in plain words].
For [who], when [situation].
[one proof: a measured detail or a sourced fact]
[one next step: how to use, keep, or order it]
```

```
Our premium artisan rye bread is carefully crafted using only the finest ingredients for an unforgettable taste experience.
```

"Dark rye, sour and dense, baked in a 2 lb loaf. Made for people who want bread that keeps: wrapped in a cloth, it stays good for five days. Slice it thin and toast it."

## About page

| Part | Rule |
|---|---|
| Job | Tell the story of the place and the people, not a mission statement |
| Length | Three to five short paragraphs |
| Shape | Start from a real scene; say what you do, with verbs; name who does it; give one proof; say what is still in progress |
| Trap | `our vision`, `our values`, three pillars of "we," `we're not just a bakery` |

```
[a real scene from the business: who, where, when]
[what you do, in verbs]
[who runs it, and one checkable fact about them]
[one proof: a number, a date, or a named partner]
[what is still in progress or what you have not done yet]
```

```
At our bakery, we believe in passion, quality, and community. Our mission is to bring people together through the timeless art of baking.
```

"The ovens go on at 4. By 6, [confirm: owner's name] has shaped the first 40 loaves by hand, the way she learned at [confirm: where she trained]. We bake bread, rolls, and one cake a day, and we sell out most afternoons. We don't deliver yet. We're working on it."

## Customer reply

| Part | Rule |
|---|---|
| Job | Answer the question and fix the problem, in that order |
| Length | Two to five sentences for a routine reply |
| Shape | Thank the person once, for something specific; answer; fix or explain the fix; give the next step with a time |
| Trap | `We apologize for any inconvenience`, blame on the customer, a script that ignores what they wrote |

```
Thanks for [the specific thing they did or told you].
[the answer, or what went wrong, named plainly]
[what you have done or will do, and when]
[the next step for them, if any]
```

Name the mistake instead of apologizing for "any inconvenience." Harder cases, such as outages, recalls, and complaints in public, follow the hard message playbook (in Whalory Pro).

```
Dear valued customer, we apologize for any inconvenience caused. Your concern is important to us and we will look into the matter.
```

"Thanks for sending the photo of the box. The loaf was crushed because we packed it on its side, and that's on us. A new one ships today, and you'll get tracking by 5 p.m. Keep the first one; there's no need to send it back."

## UI microcopy

| Element | Rule | Not this | This |
|---|---|---|---|
| Button | A verb and an object, in sentence case | `Submit` | Send invoice |
| Second button | Plain and neutral | `No, I'll keep paying more` | Not now |
| Field label | A short noun | `Please enter your mobile number` | Mobile number |
| Helper text | Only when needed | `Enter a valid format` | 10 digits, no spaces |
| Confirmation | The result, not a ceremony | `Operation completed successfully` | Invoice sent to Acme Ltd |
| Destructive confirmation | Name what will be lost | `Are you sure?` | Delete 3 invoices? You can't undo this. |
| Leaving the site | Say where the reader is going | `Redirecting…` | Opening your bank's payment page |

The rules behind the table:

- Buttons and headings use sentence case. Sources: [Mailchimp, web elements](https://styleguide.mailchimp.com/web-elements/) and [Microsoft top 10 tips](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice), checked 2026-09-27.
- One term per feature, everywhere in the product. If the product says "Sign in," no screen says "Log in" ([common-errors.md](common-errors.md#log-in-and-login)).
- A decline button never shames the reader ([ethics.md](ethics.md#confirmshaming-and-other-dark-patterns)).

```
Button: Click Here To Proceed
Label: Please input your email address below
Toast: Your changes have been saved successfully!
```

"Button: Continue to payment. Label: Email. Toast: Changes saved."

Strings in a code repository, locale files, plurals, and placeholders: ux-strings.md (in Whalory Pro).

## Error, empty, and wait states

| State | What it says | Example |
|---|---|---|
| Error | What happened, what did not happen, and what the reader can do now | "Your payment didn't go through, and you haven't been charged. Try another card or pay by bank transfer." |
| Empty | One friendly sentence and the first action | "No saved loaves yet. Tap the heart on any bread to keep it here." |
| Wait | What is happening, and how long it takes if you know | "Checking your address. This takes a few seconds." |

- No blame, and no exclamation marks in failure messages. Mailchimp never uses exclamation marks in failure messages. Source: [Mailchimp grammar and mechanics](https://styleguide.mailchimp.com/grammar-and-mechanics/), checked 2026-09-27.
- Say "you haven't been charged" only when the system knows it. When it does not, say what the bank usually does and give a way to check: `[confirm: refund time from the payment provider]`.
- Keep error codes out of the main message. If support needs one, put it on a second line.
- Google's style guide avoids `please note` and exclamation marks. Source: [Google developer documentation style guide: voice and tone](https://developers.google.com/style/tone), checked 2026-09-27.
- The `error` format caps a sentence at 16 words and allows no emoji or exclamation marks ([prose.md](prose.md#sentences)).

```
Oops! Something went wrong!! Error 0x80070005. Please try again later.
```

"We couldn't save your changes because the connection dropped. Your draft is still here. Try again when you're back online."

## Headline

| Part | Rule |
|---|---|
| Headline | One promise the reader can check, in sentence case; the `headline` format caps it at 12 words |
| Subheading | One or two sentences that open the headline up |
| Button | One precise action |
| Trap | Contrast headlines, "best," "first," or "smart" without evidence, three short slogans in a row |

```
[headline: the concrete promise]
[subheading: who it is for and the proof]
[button: verb + object]
```

```
Not Just Bread. A Way Of Life.
Fresh. Local. Authentic.
```

"Rye bread that keeps for five days. Baked every morning at 6 and wrapped in cloth, not plastic. [Button: Order a loaf]"

Taglines, subject lines, and testing headlines: headlines.md (in Whalory Pro).

## Where other forms live

The Persian forms file also covers newsletters, SMS and push, FAQs, and scripts. In English those forms have their own files. Each playbook below works in every edition, and the English craft file adds the detail.

| Form | Playbook | English craft file |
|---|---|---|
| Email and newsletters | [the email playbook](../playbooks-messages.md#email) | email.md (in Whalory Pro) |
| SMS and push notifications | [the SMS playbook](../playbooks-messages.md#sms) | sms-push.md (in Whalory Pro) |

## Checklist

Linter rule ids: `en-caption-header`, `en-emoji`, `en-emoji-format`, `en-bangs`, `en-long-sentence`, `en-minimizer`, `en-please-note`, `en-link-text`, `en-channel-length`.

- [ ] The form does its one job: a moment, a product, a story, an answer, an action, or a promise.
- [ ] Every slot holds real material or a bracket.
- [ ] Captions have no heading; hashtags sit at the end.
- [ ] Buttons are a verb and an object, in sentence case, and use the product's one term for each feature.
- [ ] Errors say what happened and what to do, with no blame and no exclamation mark.
- [ ] The customer reply names the mistake and gives the next step with a time.
- [ ] The headline's promise is something the reader can check.
