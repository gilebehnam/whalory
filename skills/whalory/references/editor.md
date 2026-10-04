# Editor prompt and scoring rubric

This file holds two tools: a text for handing writing or editing to another agent, and a rubric for scoring any text. Use the rubric alongside the [review checklist](review.md). The checklist says what to check; the rubric says what score the text gets.

## Handoff prompt

Use this text to hand writing or editing to another agent. This file does not register or run any agent, and it is not permission to publish or send anything.

> Use the `whalory` skill to write or edit this text. First find the voice profile: [path to the profile, or "follow the order in `SKILL.md`"]. If a learnings note (`LEARNINGS.md` or `<brand>.LEARNINGS.md`) sits next to the profile, read it too. Then read `SKILL.md` and the playbook for this task in `references/playbooks.md`. Open only the references that playbook names. For a sensitive industry, also open the claims file of the output language: `references/fa/claims.md` or `references/en/claims.md`. If you can't ask the user, write with brackets and list your assumptions in the note. Keep every fact, number, name, condition, and unit from the input. Invent no story, person, quote, result, or detail, and mark each gap with a bracket. Take the tone and dials from the profile and hold them to the end.

> Do three editing passes, then run the text through the three quick ethics tests in `references/fa/ethics.md` or `references/en/ethics.md`. Next, run `scripts/lint.py` from the skill folder with `--profile` for the brand and `--format` for the format. Fix every error it reports. If you can't run code, go through the manual quality assurance (QA) section of `SKILL.md`. Then follow the quality loop in `references/review.md`. A blind review follows, with at most two revision rounds, until the text has 0 lint errors and at least 17 out of 20. Give the finished text first. Keep the internal note separate and short: the "Diagnosis:" line, the profile, what is missing, and claims that need approval. The QA line comes last.

For a Persian conversation, the same prompt in Persian:

> با اسکیلِ `whalory` (والوری) این متن را بنویس یا ویرایش کن. اول پروفایلِ صدا را پیدا کن: [مسیرِ پروفایل، یا «طبقِ ترتیبِ SKILL.md»]. اگر یادداشتِ یادگیری، یعنی `LEARNINGS.md` یا `<برند>.LEARNINGS.md`، کنارِ پروفایل هست، آن هم خوانده شود. بعد `SKILL.md` و دستورِ همین کار در `references/playbooks.md` را بخوان. از مرجع‌ها فقط سراغِ آن‌هایی برو که همان دستور نام برده؛ اگر صنعت حساس است، فایلِ ادعاهای زبانِ خروجی هم: `references/fa/claims.md` یا `references/en/claims.md`. اگر نمی‌توانی از کاربر بپرسی، با کروشه بنویس و فرض‌ها را در یادداشت بیاور. واقعیت، عدد، نام، شرط و واحدِ ورودی را حفظ کن. هیچ قصه، آدم، نقل‌قول، نتیجه یا جزئیاتی نساز و جای خالی را با کروشه مشخص کن. لحن و دکمه‌ها را از پروفایل بگیر و تا آخر نگه دار.

> سه دورِ ویرایش انجام بده و متن را از سه آزمونِ سریعِ اخلاق در `references/fa/ethics.md` یا `references/en/ethics.md` بگذران. بعد `scripts/lint.py` را از پوشه‌ی اسکیل با `--profile` همان برند و `--format` همان قالب اجرا کن. هر خطایی که داد، درست کن؛ اگر اجرای کد نداری، بخشِ آزمونِ دستی (Manual QA) در `SKILL.md` را برو. بعد چرخه‌ی کیفیت در `references/review.md` را طی کن: بازبینیِ کور، و حداکثر دو دورِ بازنویسی تا متن بی‌خطا شود و دست‌کم ۱۷ از ۲۰ بگیرد. متنِ آماده را اول بده. یادداشتِ داخلی جدا و کوتاه باشد: خطِ «تشخیص»، پروفایل، آنچه کم است و ادعاهای نیازمندِ تأیید. خطِ آزمون آخرِ یادداشت می‌آید.

Information to send with the prompt. Not all of it is required:
- Task: write / rewrite / shorten / lengthen / review / translate
- Brand and profile path
- Output language, variant, and market, such as `fa-IR` or `en-GB`
- Format and where it will be read
- Reader
- Goal, and what the reader does after reading
- Materials and allowed facts
- Draft text
- Length or space limit
- Publication date, to check against the occasions calendar ([fa](fa/occasions.md), [en](en/occasions.md))
- The metric that will judge the text
- Who approves sensitive claims
- Whether the agent may ask the user; the rule is in the [question gate](intake.md)

## Two-agent work

For important work, keep the writer and the editor apart. The editor sees only the text, the materials, and the profile. The expected score and the writer's opinion never reach it. A second agent's agreement is not a substitute for a real review.

## Blind-review protocol

The `whalory-editor` agent, the `review` command, and the `review` prompt of the Model Context Protocol (MCP) server follow these steps. They are step 3 of the [quality loop](review.md#quality-loop). In a host without subagents, run them as a separate pass: [review without a second agent](#review-without-a-second-agent).

1. The editor receives four inputs and nothing else: the draft, the profile (name or path), the format id and channel, and the facts list. The facts list holds every number, name, date, price, quote, and claim the writer used, each with its source in the brief. For a transcreation, the source text is the facts list.
2. The editor never sees the conversation, the writer's note or reasons, earlier drafts, or an expected score. If the facts list is missing, the review says so in its opening line and treats every fact in the draft as unverified.
3. Load the profile and its `formats` entry for this format with `profile_lookup`, or read the files.
4. Lint the draft with `lint_text`, or run `scripts/lint.py draft.txt --profile <profile> --format <id> --facts facts.txt --json`. Check the channel limit with `channel_limits` or `--channel`.
5. Compare facts. Any number, name, date, price, quote, or claim that the facts list lacks counts as invented. It goes on the must-fix list. For a rewrite or a transcreation, also run `compare_texts` with the source as `before` and the draft as `after`, then read `added` and `dropped_conditions`.
6. Score with the [scoring rubric](#scoring-rubric) and run the ethics tests. A lint error left in the draft makes the verdict "return", whatever the total.
7. Return three parts, in this order. First, the score table. Second, the must-fix list: at most seven items, the most serious first, each with its line and reason. Third, at most three line edits, each quoting the line and offering a replacement. Never rewrite the whole text.
8. The writer applies the must-fix items. When the verdict was "return", the edited draft goes back to the editor with the same four inputs. The loop allows two such revision rounds at most.

## Review without a second agent

When the host has no subagents, the same assistant reviews its own draft. Keep the drafting reasoning out of the review as far as you can.

1. Close the drafting work first. The draft, its facts list, and the note are final for this round.
2. Start a new pass from the four inputs of the protocol, and nothing else. Set aside the request's wording, your reasons, earlier versions, and the score you expect.
3. Read the draft top to bottom as a stranger's text, the way its reader meets it: in its channel, at its real length. On this first reading, only mark where a reader would stumble.
4. Lint, check the facts against the list, and score the ten axes one at a time. Never move a score to reach a total.
5. Write the score table, the must-fix list, and the line edits before you touch the draft. Then revise.

The QA line calls this "self-review" («بازخوانیِ جدا»). It is weaker than a separate editor. For high-risk copy, the note also asks a person to read the claims before publishing.

## Bulk work

For hundreds of texts, such as product descriptions:

1. The materials for each text arrive separately and in a structured form. In a comma-separated values (CSV) file or a spreadsheet, the source columns stay untouched and the new text goes in a new column.
2. Write three sample rows first and show them. The shape of this first reply is in [bulk tasks](intake.md#bulk-tasks). If nobody is there to look, score those three rows with the rubric, then continue.
3. Write the rest in batches of fifty. Each batch is appended to the output file and gets a progress line, such as «ردیفِ ۱ تا ۵۰ از ۱٬۲۰۰» or "rows 1 to 50 of 1,200".
4. Lint each batch on the new columns only, and send back every text with an error. The source columns are not linted:
   `lint.py out.csv --csv-columns title_new,bullets_new,desc_new --csv-key sku --json --profile <profile>`
   The full sequence is in bulk catalog from a spreadsheet (in Whalory Pro).
5. A person reads at least five random texts against the rubric.
6. If one error repeats across several texts, its root is in the prompt or the profile. Fix it there as well as in the texts.

## Scoring rubric

Ten axes, each scored 0 to 2: 0 is a serious problem, 1 needs work, 2 is acceptable. The total is out of 20.

| Axis | In Persian | Question |
|---|---|---|
| Fit with the brief | «هم‌خوانی با بریف» | Does it follow the brief's task, reader, channel, and goal? Was the "Diagnosis:" line right? |
| Opening | «شروع» | Does the opening sentence start with something concrete: an object, a place, a time, someone's hands at work, a sensory detail, or the news itself? |
| Narrator and tone | «راوی و لحن» | Does it talk to one person without making the copy about itself? Do tone and dials match the profile and format, and hold throughout? |
| Story | «قصه» | Does its arc suit the profile's narrative dial? |
| Detail | «جزئیات» | Does it have concrete details specific to this subject? Does it survive the substitution test? |
| Language | «زبان» | Does sentence length match the profile dial, with varied rhythm? Are the verbs strong, the adjectives few, and the profile's "avoid" words absent? |
| Truthfulness | «واقعی بودن» | Is nothing invented, inflated, or claimed without evidence? Are the claim boundaries of the profile and the industry respected? |
| Cleanliness | «تمیزی» | Is it free of AI tells, mid-sentence dashes, and typos? Are the script rules kept, such as the zero-width non-joiner (ZWNJ) in Persian or one spelling variant in English? |
| Clear next step | «روشنیِ قدمِ بعد» | Does the reader know what to do next, with one verb? Can they take that step in this channel, and does its promise match the destination? |
| Ending | «پایان» | Does the ending suit the format, with no moral and no summary? |

**Pass:** a total of at least 17 out of 20, and never a zero in fit with the brief, truthfulness, or cleanliness.

**The ethics test is separate from the score.** A text that fails the three quick tests ([fa](fa/ethics.md#سه-آزمونِ-سریع), [en](en/ethics.md#three-quick-tests)) goes back whatever its total. If the text deals with urgency, a vulnerable reader, current news, inspiration, or data, the one-line test for that subject runs as well.

Some axes don't apply to a format, such as story for a button or a verification code. Such an axis gets 2 and is marked «نامربوط», or "not applicable" in English, in the table. Some messages are themselves the next step, such as a receipt. There, clear next step only needs to say that no action is needed, or when the next update will arrive.

Deliver the score like this, in the conversation language. In English:

```
| Axis | Score | Why | Fix |
|---|---|---|---|
| Fit with the brief | 2 | [...] | none |
| Clear next step | 1 | [two buttons with the same weight] | [turn the second button into a text link] |
...
Total: [..] out of 20 · Verdict: pass / return
```

In Persian, with the Persian axis names from the table above:

```
| محور | نمره | چرا | اصلاح |
|---|---|---|---|
| هم‌خوانی با بریف | ۲ | [...] | هیچ |
| روشنیِ قدمِ بعد | ۱ | [دو دکمه با یک وزن] | [دکمه‌ی دوم به پیوندِ متنی] |
...
جمع: [..] از ۲۰ · حکم: قبول / برگشت
```

## Condensed loop for paste-in prompts

Paste-in prompts, such as a custom GPT, a Gem, or a chat project, often have no code execution and no subagents. They carry this short form of the [quality loop](review.md#quality-loop) instead. In English:

> Before you deliver any copy:
>
> 1. Check it against the checklist of its language and fix every failure.
> 2. Reread it as someone else's text, with only the brief's facts and the profile in view. Score ten axes from 0 to 2: fit with the brief, opening, narrator and tone, story, detail, language, truthfulness, cleanliness, clear next step, and ending.
> 3. Below 17 out of 20, or with a zero in fit, truthfulness, or cleanliness, fix it and score again, twice at most.
> 4. Give the copy first, and end the note with one line, such as "QA: manual · self-review 18/20 · 1 revision round".

In Persian:

> پیش از تحویلِ هر متن: ۱) آن را با فهرستِ آزمونِ زبانِ خودش بسنج و هر ایرادی را درست کن. ۲) متن را مثلِ نوشته‌ی کسِ دیگری دوباره بخوان و فقط واقعیت‌های بریف و پروفایل را جلوی چشم داشته باش. به ده محور از ۰ تا ۲ نمره بده: هم‌خوانی با بریف، شروع، راوی و لحن، قصه، جزئیات، زبان، واقعی بودن، تمیزی، روشنیِ قدمِ بعد و پایان. ۳) اگر جمع کمتر از ۱۷ از ۲۰ شد، یا هم‌خوانی، واقعی بودن یا تمیزی صفر گرفت، درستش کن و دوباره نمره بده؛ حداکثر دو بار. ۴) متن را اول بده و یادداشت را با یک خط تمام کن، مثلِ «آزمون: دستی · بازخوانیِ جدا: ۱۸ از ۲۰ · یک دورِ بازنویسی».
