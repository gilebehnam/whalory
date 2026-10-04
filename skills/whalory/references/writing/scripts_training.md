# Scripts, storytelling and learning / اسکریپت، روایت و آموزش

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Help a listener learn or follow a spoken sequence tied to real material.

Tone: Speakable, paced and matched to listener knowledge. Avoid: Invented expertise, impossible demonstrations and fabricated testimony.

Evidence: Source material, actual workflow, learning objective and supplied duration.

Destination budget: Separate spoken copy, visual directions and timings; timings are estimates until read aloud.

Shared craft: [existing family method](../playbooks-social.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Short and long video script](#video-script)
- [Reels script](#reel-script)
- [Podcast script](#podcast-script)
- [Webinar script](#webinar-script)
- [Product explainer script](#explainer-script)
- [Training-module text](#training-module)
- [Workshop facilitation script](#workshop-facilitation)
- [Course description and syllabus](#course-description)
- [Business storytelling draft](#story-narrative)
- [Presentation copy and speaker notes](#presentation-notes)

## Video Script

**اسکریپت ویدیوی کوتاه و بلند · `scripts_training.video_script`**

Build a speakable sequence from actual facts and the requested duration; distinguish real footage from proposed visuals.

Required inputs: goal, facts, duration, format. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `script` / سناریو | Write the ordered script with estimated timings. |
| `visual_notes` / یادداشت تصویر | Describe actual or proposed visuals with status labels. |
| `spoken_copy` / متن گوینده | Provide narrator copy separate from production directions. |

Review: No fake scene: review the actual Short and long video script against supplied evidence. Speakability: review the actual Short and long video script against supplied evidence. Timing fit: review the actual Short and long video script against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Reel Script

**اسکریپت ریلز · `scripts_training.reel_script`**

Make the opening promise match a short, deliverable sequence based on available assets.

Required inputs: idea, facts, visual_context. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `opening` / شروع | Write an honest opening line. |
| `beats` / بخش‌های روایت | Sequence visual and narrative beats. |
| `spoken_copy` / متن گوینده | Give speakable short copy. |
| `caption` / کپشن | Write a caption consistent with the video. |

Review: No clickbait: review the actual Reels script against supplied evidence. Asset consistency: review the actual Reels script against supplied evidence. Timing fit: review the actual Reels script against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Podcast Script

**اسکریپت پادکست · `scripts_training.podcast_script`**

Use sourced material and host voice to sustain a coherent spoken argument.

Required inputs: topic, sources, host_voice, format. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `intro` / مقدمه | Introduce the real topic and listener value. |
| `segments` / بخش‌ها | Develop sourced segments with attribution. |
| `transitions` / انتقال‌ها | Write natural transitions. |
| `outro` / پایان | Close with a useful takeaway without fabricated quote or guest speech. |

Review: Source quality: review the actual Podcast script against supplied evidence. Speakability: review the actual Podcast script against supplied evidence. No fake quotes: review the actual Podcast script against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Webinar Script

**اسکریپت وبینار · `scripts_training.webinar_script`**

Align every segment with a learning goal and feasible duration.

Required inputs: learning_goal, material, duration. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `run_of_show` / برنامهٔ اجرا | Allocate supplied duration to actual activities. |
| `spoken_notes` / یادداشت گفتار | Write speakable facilitator notes. |
| `qa_prompts` / پرسش‌های گفت‌وگو | Prepare questions grounded in material without inventing audience responses. |

Review: Timing fit: review the actual Webinar script against supplied evidence. No fake expertise: review the actual Webinar script against supplied evidence. Learning alignment: review the actual Webinar script against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Explainer Script

**اسکریپت توضیح محصول · `scripts_training.explainer_script`**

Explain the actual workflow and show only actions the product supports.

Required inputs: actual_workflow, reader, facts. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `script` / سناریو | Write the reader-oriented explanation. |
| `demo_notes` / یادداشت نمایش | Specify real demonstration steps and expected visible behavior. |
| `cta` / اقدام بعدی | Offer a supported next action. |

Review: Capability truth: review the actual Product explainer script against supplied evidence. Step accuracy: review the actual Product explainer script against supplied evidence. Speakability: review the actual Product explainer script against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Training Module

**متن ماژول آموزشی · `scripts_training.training_module`**

Connect learning goal to source material, example and assessable practice.

Required inputs: learning_goal, sources, reader_level. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `lesson` / درس | Teach the objective in the learner's terms. |
| `examples` / مثال‌ها | Use accurate examples with any synthetic context labeled. |
| `exercise` / تمرین | Create an exercise and answer criteria that test transfer, not memorized wording. |

Review: Learning alignment: review the actual Training-module text against supplied evidence. No fake facts: review the actual Training-module text against supplied evidence. Regulated review if needed: review the actual Training-module text against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Workshop Facilitation

**متن تسهیلگری کارگاه · `scripts_training.workshop_facilitation`**

Design activities that can produce the stated learning or decision goal in the supplied time.

Required inputs: goal, participants, activities, time. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `facilitator_notes` / یادداشت تسهیل‌گر | Give facilitator steps and timing estimates. |
| `prompts` / پرسش‌ها | Provide prompts tied to each activity. |
| `debrief` / جمع‌بندی فعالیت | Debrief actual outputs without pretending outcomes have occurred. |

Review: Activity goal fit: review the actual Workshop facilitation script against supplied evidence. Use only evidenced outcomes with period and definition; never substitute an attractive invented metric. Time fit: review the actual Workshop facilitation script against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Course Description

**معرفی دوره و سرفصل · `scripts_training.course_description`**

Set expectations from actual curriculum, instructor facts and approved terms.

Required inputs: actual_curriculum, instructor_facts, terms. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `description` / توضیح | Explain what the course covers and whom it suits. |
| `syllabus` / سرفصل | Describe the real syllabus. |
| `prerequisites` / پیش‌نیازها | State required knowledge, access and conditions without invented certification. |

Review: No fake certification: review the actual Course description and syllabus against supplied evidence. No fake outcomes: review the actual Course description and syllabus against supplied evidence. Term clarity: review the actual Course description and syllabus against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Story Narrative

**روایت و داستان کسب‌وکار · `scripts_training.story_narrative`**

Use real material for factual narrative; fictional scenes need explicit permission and a visible fiction label.

Required inputs: actual_material, fiction_permission, reader. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `story` / روایت | Write the narrative with factual and fictional status clear. |
| `short_version` / نسخهٔ کوتاه | Provide a concise version preserving that status. |
| `source_notes` / یادداشت منابع | Record source, attribution and invention boundaries. |

Review: Fiction label: review the actual Business storytelling draft against supplied evidence. No fake scene: review the actual Business storytelling draft against supplied evidence. No fake experience: review the actual Business storytelling draft against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Presentation Notes

**متن اسلاید و یادداشت ارائه · `scripts_training.presentation_notes`**

Give each slide a clear evidenced point and connect it to the audience's decision.

Required inputs: purpose, evidence, audience, slide_budget. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `slide_copy` / متن اسلایدها | Write concise slide text within the supplied slide budget. |
| `speaker_notes` / یادداشت گوینده | Provide spoken explanation distinct from on-slide copy. |
| `source_notes` / یادداشت منابع | Attach sources and claim gaps to the correct slide. |

Review: Slide density: review the actual Presentation copy and speaker notes against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Story coherence: review the actual Presentation copy and speaker notes against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
