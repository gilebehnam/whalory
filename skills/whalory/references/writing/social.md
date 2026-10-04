# Social media / شبکه‌های اجتماعی

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Give a reader one useful idea in the selected social format.

Tone: Natural public conversation with a specific point. Avoid: Engagement bait, fake personal experience and invented scenes.

Evidence: Supplied asset context, attributable observations and working links.

Destination budget: One post or explicitly numbered frames; use the requested count.

Shared craft: [existing family method](../playbooks-social.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Instagram caption](#instagram-caption)
- [LinkedIn post](#linkedin-post)
- [X post and thread](#x-post-thread)
- [Threads post](#threads-post)
- [Bluesky post](#bluesky-post)
- [Facebook post](#facebook-post)
- [YouTube title and description](#youtube-description)
- [TikTok and short-video caption](#tiktok-caption)
- [Story sequence](#story-sequence)
- [Social carousel](#carousel)
- [Other social platform post](#other-platform)

## Instagram Caption

**کپشن اینستاگرام · `social.instagram_caption`**

Choose observation, explanation or story from the supplied asset context. A visible object does not prove origin, ownership or a personal memory.

Required inputs: post_context, facts, reader. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `caption` / کپشن | Write copy-ready caption with a concrete supplied detail and main point. |
| `cta` / اقدام بعدی | Add a next step only if the brief calls for one. |
| `optional_tags` / برچسب‌های اختیاری | Provide optional relevant tags separately from caption copy; limits remain dated-source dependent. |

Review: No invented scene: review the actual Instagram caption against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Verify the destination field and counting unit from dated source data; otherwise label its limit unverified. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Linkedin Post

**پست لینکدین · `social.linkedin_post`**

Distinguish the author's direct experience from cited observations and interpretation. End naturally without requiring an engagement question.

Required inputs: idea, evidence, author_role. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `post` / پست | Develop the real observation, reasoning, practical use and caveat in readable paragraphs. |
| `optional_discussion_prompt` / پرسش اختیاری | Offer a specific discussion question only if a useful answer is expected. |

Review: No fake experience: review the actual LinkedIn post against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. No engagement bait: review the actual LinkedIn post against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## X Post Thread

**پست و رشته‌پست ایکس · `social.x_post_thread`**

Decide whether one unit answers the brief before splitting; each unit must make sense in order.

Required inputs: idea, facts, thread_need. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `post_or_thread` / پست یا رشته‌پست | Provide either one post or a numbered thread, explicitly labeled. |
| `ordered_units` / بخش‌های مرتب | Preserve attribution and conditions across unit boundaries. |

Review: Do not invent a maximum; distinguish characters, graphemes, bytes, units and SMS segments. Unit coherence: review the actual X post and thread against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Threads Post

**پست تردز · `social.threads_post`**

Choose one conversational point supported by supplied facts; a reply invitation is optional.

Required inputs: idea, facts, audience. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `post` / پست | Write the point in a self-contained post. |
| `optional_reply_prompt` / دعوت اختیاری به پاسخ | Invite a relevant response without bait or manufactured controversy. |

Review: Platform fit: review the actual Threads post against supplied evidence. No engagement bait: review the actual Threads post against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Bluesky Post

**پست بلواسکای · `social.bluesky_post`**

Let the reader understand why the supplied link is relevant before opening it.

Required inputs: idea, facts, links. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `post` / پست | Write a concise post with attributable claims. |
| `link_context` / توضیح پیوند | Keep URLs exact and explain their destination. |

Review: Do not invent a maximum; distinguish characters, graphemes, bytes, units and SMS segments. Link integrity: review the actual Bluesky post against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Facebook Post

**پست فیسبوک · `social.facebook_post`**

Adapt the framing to the actual group or page and its documented norms.

Required inputs: idea, facts, group_or_page. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `post` / پست | Write the useful point in the community's context. |
| `cta` / اقدام بعدی | Offer an action that the group or page actually supports. |

Review: Community fit: review the actual Facebook post against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Verify the destination field and counting unit from dated source data; otherwise label its limit unverified. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Youtube Description

**توضیح و عنوان یوتیوب · `social.youtube_description`**

Describe the actual video; supplied timestamps are the only basis for chapters.

Required inputs: video_content, actual_timestamps, links. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `title` / عنوان | Give a title faithful to the content. |
| `description` / توضیح | Summarize value, sources and verified links. |
| `chapters_if_supplied` / فصل‌ها در صورت وجود زمان‌ها | List supplied timestamps in order; omit chapters when timings are unknown. |

Review: No fake chapters: review the actual YouTube title and description against supplied evidence. Link integrity: review the actual YouTube title and description against supplied evidence. No clickbait: review the actual YouTube title and description against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Tiktok Caption

**کپشن تیک‌تاک و ویدیوی کوتاه · `social.tiktok_caption`**

Use the caption to clarify the actual video rather than invent a second event.

Required inputs: video_context, facts, platform. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `caption` / کپشن | Write a compact caption consistent with visible or supplied action. |
| `optional_tags` / برچسب‌های اختیاری | Keep optional tags relevant and separate. |

Review: Asset consistency: review the actual TikTok and short-video caption against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Do not invent a maximum; distinguish characters, graphemes, bytes, units and SMS segments. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Story Sequence

**استوری چندفریمی · `social.story_sequence`**

Build a sequence with one job per frame: introduce, explain and invite action. Specify interactions only when the host actually supports them.

Required inputs: facts, frame_count, goal, visual_context. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `frame_copy` / متن فریم‌ها | Number frames and give each one concise overlay copy. |
| `interaction_notes` / یادداشت تعامل | Describe the actual asset role and optional supported poll or question box. |
| `final_cta` / اقدام نهایی | Use the final frame for one clear next action and its conditions. |

Review: One idea per frame: review the actual Story sequence against supplied evidence. Compare names, numbers, units, conditions and claims across every output unit. Interaction honesty: review the actual Story sequence against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Carousel

**کاروسل شبکه‌های اجتماعی · `social.carousel`**

Give the sequence a reader question, evidence-led development and useful close.

Required inputs: topic, facts, slide_budget. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `slide_copy` / متن اسلایدها | Number slide copy with one point per slide. |
| `cover` / جلد | Make the cover's promise match the actual slides. |
| `closing` / پایان | End with a useful conclusion or action. |
| `caption` / کپشن | Provide a companion caption without repeating every slide. |

Review: Sequence coherence: review the actual Social carousel against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Slide density: review the actual Social carousel against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Other Platform

**پست سایر شبکه‌ها و کانال‌ها · `social.other_platform`**

Name the platform and verify its affordances before adapting the goal-and-shape method.

Required inputs: platform, purpose, facts. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `channel_adapted_copy` / متن متناسب با کانال | Produce copy suited to the stated audience and destination. |
| `limits_note` / یادداشت محدودیت | List unverified platform rules rather than inventing maxima. |

Review: Capability detection: review the actual Other social platform post against supplied evidence. Do not invent a maximum; distinguish characters, graphemes, bytes, units and SMS segments. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
