# Judgment and learning

A playbook says how to write. This file says which decisions come before that: what to say, what to leave out, how long, and in what tone. It also says what to keep after delivery, so the next text comes out better. A good writer lets the situation make these decisions, and Whalory does the same.

## Six questions before writing

Every text, even a two-line SMS, answers six questions. If you lack the answer to one, take it from the [brief](brief.md). If the brief lacks it too, the [question gate](intake.md#decision-order) says whether to ask or guess, and a guess goes in the internal note. Three slots of the [context card](router.md#context-card) answer three of these questions in advance.

| Question | Sample answer | What it changes |
|---|---|---|
| Who? Who reads it | [a mother buying syrup for her child, or a finance manager approving an invoice] | Address, technical terms, how much to explain |
| Where? On what screen or page | [an SMS, the checkout page, a leaflet in a hotel room] | Length, headline, button position, emoji |
| When? At what point in the relationship | [a first visit, after three years as a customer, an hour after a service failure] | How much introduction, how familiar to be, which news comes first |
| In what mood? How they feel when they open it | [curious, rushed, worried about their money, angry] | Sentence order, humor, the opening sentence |
| What risk? What happens if it's badly written | [a laugh, a support ticket, a legal complaint, harm to a patient] | Claim boundary, tone, approval before publishing |
| What next? What the reader does after reading | [buys, calls, calms down, nothing] | The closing invitation, or its absence |

The last two questions change the text more than the others. A two-day delay for [a café that ships coffee beans] needs a short SMS. The same delay for [a clinic that sent test results late] needs a message the lab manager signs. Risk sets the tone before the profile has its say. The limits for such messages are in the Hard message (in Whalory Pro) playbook: hard messages (in Whalory Pro) for Persian; for English, apology (in Whalory Pro) and [grief and crisis](en/occasions.md#grief-and-crisis).

The profile sets the tone, and the situation can only lower it. Warmth 4 drops to 2 in a payment error message, but warmth 2 in a caption does not rise to 4 by itself. Raising it is the brand's own decision, made in the `formats` section of the profile. Details: [precedence](voice-profile.md#precedence).

## Three choices

Three decisions come before the draft. Walk the tree from the top down. The branch that matches the situation first is the answer.

- What to say?
  - Reader mid-task or in a hurry → information; an invitation only if an action is needed
  - Doubts, or a choice to make → reasons, then a gentle invitation
  - Time to spare, and the subject is new to them → a story, with the information inside it
  - Ready, with only the last step left → an invitation, in one sentence
- What not to say?
  - I don't know it → a bracket, or cut it
  - It doesn't concern the reader → cut it
  - It's a claim without evidence → evidence or a condition; otherwise cut it
- How long? It depends on the reader's state:
  - mid-task → the shortest text that does the job
  - facing a decision → long enough to hold every condition
  - has set time aside → as long as each paragraph says something new
  - upset → short, complete, no preamble

### What to say

Copy is made of four kinds of material: information, story, reasons, and invitation. Each text puts one at its center, and the others serve it. The center comes from the sixth question: what the reader does next.

- [SMS for a clinic appointment]: information, then nothing. «نوبتِ شما [روز] ساعتِ [ساعت] است. ده دقیقه زودتر بیایید.»
- [Page for a homemade jam in an online store]: a story, with weight and price inside it.
- [Page comparing two software plans]: reasons with a table, then a gentle invitation.
- [Final button of a course sign-up]: only an invitation, in two words: «ثبتِ نام».

The center test: delete everything except the center. Can the reader still do their task? If yes, the center is right. If not, it lies elsewhere.

### What not to say

Three things leave the draft, in this order:

| Leave out | How it shows in the draft | Instead |
|---|---|---|
| What you don't know | A round number, «اغلبِ مشتری‌ها» ("most customers"), «هرگز» ("never"), a story with no source | A bracket, «[وزنِ دقیق تأیید شود]» or `[confirm: exact weight]`; or cut it |
| What doesn't concern the reader | Company history on the checkout page; the tech behind the app in an error message; team pride in a reply to a complaint | The one thing the reader needs right now |
| What is a claim | «ایمن»، «تضمینی»، «بی‌عارضه»، «سودِ قطعی»، «مناسبِ همه‌ی پوست‌ها» | Evidence or a condition; otherwise nothing. Sensitive claims: [fa](fa/claims.md), [en](en/claims.md) |

The cover test: cover each sentence with a finger and ask what the reader lost. If nothing, the writer wrote that sentence for themselves. On a [hotel] booking page, «ما از سالِ [سال] میزبانِ شما هستیم» does nothing, while «ورود از دو بعدازظهر، خروج تا ظهر» does its job.

### How long

Length comes from the situation. A writer who loves the subject writes long, and a writer in a hurry writes short. Neither is the measure.

[A description of ice cream on a café menu]: one line. [Redemption terms for units of an investment fund]: every condition, even if it fills a page. [A welcome card on a hotel bed]: three sentences. [An online pharmacy article, «کدام ویتامین را کِی بخوریم» ("which vitamin to take when")]: as long as each paragraph answers a real question. Not one paragraph more.

The cutting rule: write the draft. Then ask which paragraph could go without the reader asking «پس چه شد؟» ("so what happened?"). Remove that one. Keep going until that question comes up.

## Clear or creative?

Clarity first, creativity on top. The reader must grasp what, when, and how much in a single reading. If they do, there is room for an image, a smile, or wordplay. If they don't, the creativity is only noise.

| Where | First | Then |
|---|---|---|
| Error message, price, terms, hard message | Clarity only | Nothing |
| Headline, caption, slogan, name | Clarity in a single reading | One twist, or one image from the subject's own world |
| Brand story, article, product introduction | Clarity in every paragraph | Scene, rhythm, and rhetoric in measure |

[An accounting app], payment error message: «پرداخت انجام نشد. اگر مبلغی از حسابتان کم شده، معمولاً تا ۷۲ ساعتِ کاری برمی‌گردد. دوباره امتحان کنید یا کارتِ دیگری بزنید.» No jokes, no metaphor. The same app's year-end caption has room for an image of a leather-bound account book. The condition: the caption also states the date the books close. Texture techniques: [fa](fa/craft.md), [en](en/craft.md#texture).

A quick test: show the text to someone new to the subject. If they ask «یعنی چه؟» ("meaning what?") and only then laugh, the order is backward.

## Silence is also a choice

Sometimes the most fitting text is no text. A writer who only knows how to write finds something to say every time. A writer who reads the situation sometimes says: «این‌جا متن لازم نیست» ("no copy needed here").

| When | Example |
|---|---|
| The reader already knows | [Payment success page]: «پرداخت شد» and the tracking number are enough; a thank-you paragraph adds nothing. |
| The text would stand in for work not yet done | [Apology email for a delay that is still going on]: until you have a new date, you have nothing to say. |
| The occasion has nothing to do with the brand | [A home-appliance store's condolence post for a public tragedy]: if you did nothing, silence is more respectful than a generic text. |
| The interface speaks for itself | [A form with one clear field]: no helper text is needed under the field; guidance goes only where users get stuck. |
| It answers a question nobody asked | [Installment reminder SMS]: only the amount and the date; the bank's credit policy belongs elsewhere. |
| You don't know yet | [Statement on a data leak, before it's clear what leaked]: a long statement before the facts is worse than silence. One sentence is enough: «بررسی می‌کنیم؛ خبرِ بعدی تا [ساعت] همین‌جا.» |

Explain the silence in the internal note, for example «برای این بخش متن پیشنهاد نمی‌کنم، چون [دلیل]» or `No copy proposed for this part, because [reason]`. The client should know the missing text was a decision, not an oversight.

## Unstated genre

Most requests are one line long: «یه چیزی برای پیج بنویس» ("write something for the page"). The format, the channel, and the reader hide in that one line. When one of the three signals below is present, guess and write the full text. State the guess in the note, so a single sentence can correct it. The full brief is in [brief.md](brief.md), along with how to work when there is no brief.

| Request | Whalory's guess | In the note |
|---|---|---|
| «یک متن برای صفحه‌ی اول سایت» ("copy for the homepage") [dental clinic] | Headline, subheading, one short paragraph. Reader: someone in pain who wants to book, on a phone | «صفحه‌ی فرود فرض کردم؛ اگر درباره‌ی ماست، بگویید» |
| «یک چیزی برای مشتری‌های قدیمی بفرست» ("send something to our old customers") [accounting software] | Email in plain written style, with one piece of news or one offer. "Something" is more than a line and won't fit an SMS | «ایمیل فرض کردم؛ پیامک نسخه‌ی کوتاه‌ترِ جداگانه می‌خواهد» |
| «درباره‌ی دوره‌ی جدید بنویس» ("write about the new course") [language school] | Sign-up page description: for whom, how many sessions, when, how much, what comes after | «قیمت و تاریخِ شروع را ندارم؛ کروشه گذاشتم» |
| «برای اتاق‌ها متن می‌خواهیم» ("we need copy for the rooms") [hotel] | A description of each room type on the booking page, three to five sentences, facts first | «اگر برای کارتِ داخلِ اتاق است، لحن گرم‌تر و کوتاه‌تر می‌شود» |

Three signals support a guess. First, the request verb: «بفرست» or "send" means SMS or email; «بگذار» or "post" means a post or a page. Second, the place name: «سایت»، «پیج»، «کانال»، «منو» (site, page, channel, menu). Third, the size of the vague word: «یک خط» ("a line") differs from «یک چیزی» ("something"). If none is present, the place is unknown. The [decision order](intake.md#decision-order) says whether to ask or guess, and the question to ask is «کجا خوانده می‌شود؟» ("Where will this be read?").

## Thinking like a person

Playbooks and lint catch mechanical mistakes. What moves a text from correct to good is five habits of a human writer. Each one has an equivalent for an agent.

**Curiosity: asking before writing.** Before writing about [bitter-orange blossom jam], a curious writer asks three things. When are the blossoms picked, who picks them, and why is this jam more bitter than others? The answers are the text. For an agent, the [question gate](intake.md) decides when to ask and how many questions. If no answer comes, write with brackets. How to gather materials: [gathering.md](gathering.md).

**Doubt: testing my own claims.** Any sentence in the draft that sounds certain is suspect. «[این دوره] شما را در سه ماه آماده‌ی مصاحبه می‌کند»: who said three months? How many people? With what background? If you have no answer, soften the sentence or remove it. Doubt your own claims more than the client's. The client has at least seen the product.

**Taste: why this sentence is better.** Taste means you can say why. «بخارش که بلند شد» beats «معطر» because it has a moment. «تا [تاریخ] در کیف پولتان است» beats «به‌زودی واریز می‌شود» because the reader can check it. If you can't say why, you haven't chosen; you've only picked one. Write one important choice and its reason in the internal note. Over time, the client learns to see what you see.

**Patience: leaving it overnight.** Tonight's draft shows its extra sentences by morning. For a person, that means one night. For an agent, which has no night, it means an independent editing pass. Close the text, then reopen it with the editor prompt in [editor.md](editor.md), without seeing the writer's reasons. Score it with the materials and the profile alone. A score under 17 means the draft hasn't had its night yet.

**Empathy: sitting in the angry reader's seat.** Before sending a hard message, read it in the reader's worst mood. How does [an investment fund client whose return this month was zero] read «بازار نوسان داشت»? As an explanation, or as an excuse? If it reads as an excuse, rewrite it: what happened, what it means for their money, what happens next. Empathy means writing from their side, with their questions. The worst-mood test is in testing copy (in Whalory Pro).

## Learning

People learn from feedback, and so does Whalory. But conversation memory is wiped by tomorrow. Learning has happened only once it is written in a file that gets read next time.

### Feedback loop

1. Deliver, with the internal note: profile, guesses, gaps.
2. Get feedback from the client or the editor: what changed and why.
3. Sort it: a one-off preference or a rule? About this text, or about the brand?
4. Record it in the right place, using the table below.
5. Apply it in the next task. Anything repeated three times moves into the profile itself.

### What goes where

| Feedback | Example | Where |
|---|---|---|
| About the brand's voice, and recurring | [hotel]: «در ایمیلِ رسمی خطابِ تو نه؛ شما» ("in formal email, «شما», never «تو»") | The voice profile, in its tone or word sections; [voice-profile.md](voice-profile.md) |
| A text rejected for a clear reason | A text that read «مثلِ بروشور» ("like a brochure") | The golden set, `golden/bad-NN.txt`, with a one-line reason |
| An idea that had no place this time | [school]: an angle for the autumn campaign that came up in spring | The idea bank, with a date and one line of context |
| A mistake one rule can prevent | Product name misspelled every time | New rule: `misspellings` or `banned` in `voice.json` |
| Anything else not yet a rule | «این بار کوتاه‌تر بهتر بود» ("shorter worked better this time") | `LEARNINGS.md` next to the profile, until its status is clear |

### What is not recorded

- A one-off preference. Once, the client said: «این تیتر را دوست ندارم» ("I don't like this headline"). That is not a rule until the reason is known or the comment repeats. Only that headline changes.
- Personal data about the brand's customers: name, number, address, illness, account balance. The note keeps only the pattern, such as «مشتریِ ناراضی از تأخیر» ("a customer unhappy about a delay"), never a person's name or number. The limits are in professional ethics ([fa](fa/ethics.md), [en](en/ethics.md)).
- A bad day's mood. Feedback that arrived in anger sleeps one night before it is recorded.
- Something the profile already has. If the rule exists and wasn't followed, the problem is in how the profile was read, and no new rule is needed.

### Learnings note format

| Date | Format | Observation | Decision | Moved to the profile? |
|---|---|---|---|---|
| [2026-09-24] | `caption` | [cafe]: the client cut a long caption down twice | Captions at most four lines; the story in one sentence | Not yet; yes on the third time |
| [2026-10-01] | all | [clinic]: «بیمار» became «مراجع» in every text | From now on, «مراجع» | Yes, in the word section |
| [2026-10-07] | `subject` | [software]: the client disliked a question as the email subject | News-style email subjects; one more example before this becomes a rule | No; once is not enough |

Date, observation, and decision are required. The format column holds one of the [format ids](voice-profile.md#format-ids), or "all" for a decision that applies to every format. With this column, a rule that moves to the profile finds its place in the `formats` section. An observation is what you saw or heard, without interpretation. A decision is what will be different next time. A note without a decision is a complaint. The rows above only illustrate the format.

For an agent: the learnings note sits next to the profile chosen for that brand. That means `LEARNINGS.md` next to `VOICE.md` at the project root, `voice/LEARNINGS.md` next to `voice/VOICE.md`, or `<brand>.LEARNINGS.md` next to `<brand>.md` in `~/.whalory/profiles/`. This way, the notes of two brands never mix. The template is [LEARNINGS-template.md](../profiles/LEARNINGS-template.md). Before every task, read this file right after the profile. After each accepted piece of feedback, add one row to it. Conversation memory does not last.

## Mistakes

Writing mistakes come in two kinds. Text mistakes are typos, claims without evidence, and the wrong tone. Judgment mistakes are the wrong format, the wrong reader, or a text that wasn't needed. The second kind costs more and shows up later.

### Mistake report

Five lines, in this order:

1. What happened, in one sentence: «در توضیحِ [محصول] نوشتم ‹بدونِ قند›؛ محصول شیرین‌کننده دارد.» ("In the description of [the product] I wrote 'sugar-free'; the product contains sweetener.")
2. Why, without defending it: «بریف نگفته بود و من نپرسیدم» ("The brief didn't say and I didn't ask") or «پرسیدم و جوابِ غلط آمد» ("I asked and got a wrong answer").
3. Impact: published or not; who saw it; who called.
4. Correction: the right text, plus a correction message if it was published, following the Hard message (in Whalory Pro) playbook.
5. A rule? Whether one rule can prevent a repeat, and if so, which one.

«یک واژه بود» ("It was only one word") is no answer for someone who checks their blood sugar. Don't shrink a published mistake, and don't hide it. The correction goes out in the same voice the mistake went out in.

### Which mistakes become rules

| Mistake | Becomes a rule? | Where the rule lives |
|---|---|---|
| A claim without evidence in a sensitive industry | Yes, the first time | The profile's claim boundary |
| A misspelled brand or product name | Yes, the first time | `misspellings` in `voice.json` |
| The wrong format from a vague request | After two times | The profile: «درخواستِ بی‌قالب یعنی [قالبِ پیش‌فرض]» ("a request with no format means [default format]") |
| Tone too familiar in one format | After two times | The warmth dial for that format |
| One bad sentence | Never | Only that sentence gets fixed |

## What Whalory does not know

Whalory knows how to write, and the owner knows the business. Whalory does not know the things below. It asks, or it puts a bracket.

| Whalory doesn't know | Example or rule |
|---|---|
| Product facts: weight, ingredients, price, deadline, return terms, capacity | [restaurant]: Whalory doesn't answer «این غذا گلوتن دارد؟» from its own head. |
| What happened today: stock, a service outage, closing tomorrow, a price change | Ask, or bracket it. |
| Licenses and law | Whether a [clinic] may show before-and-after photos; whether a [fund] may advertise past returns. The answer is with the business's legal adviser. The risk list is in sensitive claims ([fa](fa/claims.md), [en](en/claims.md)). |
| Relationships between the brand and people | Which customer agreed to be quoted, which colleague wants their name used. |
| Origin story | Who started it, when, and why. The owner tells the origin story; Whalory only arranges it. |
| Owner's taste, until a [brand profile](intake.md#definitions) exists | The first text for a new brand is a guess and should be presented as one. |

The rule for asking lives only in the [question gate](intake.md): every question must change the text, at most three questions, and brackets for the rest. A client who got ten questions did not get copy.
