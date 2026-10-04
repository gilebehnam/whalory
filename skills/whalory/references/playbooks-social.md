# Playbooks: social media, ads, and campaigns

This file is part of the [playbooks](playbooks.md). Each task's row is in the [task index](playbooks.md#task-index), and every playbook here assumes the [shared steps](playbooks.md#shared-steps). The "Questions" line of a playbook only names its row in the question bank; the [question gate](intake.md#decision-order) decides whether to ask. The "References" line lists the Persian craft files after "fa:" and the English ones after "en:". Read the list for the output language. The quality assurance (QA) line gives the checks and the `--format` id.

## Contents

- [Social media and messaging apps](#social-media-and-messaging-apps)
  - [Caption](#caption)
  - [Social post](#social-post)
- [Headlines, ads, and campaigns](#headlines-ads-and-campaigns)
  - [Tagline and slogan](#tagline-and-slogan)

## Social media and messaging apps

### Caption

1. One moment in one to three sentences. The opening line makes sense on its own, before the "more" cut.
2. One sensory image and one small ending; the full explanation belongs somewhere else.
3. Hashtags stay out of the sentence and go at the end. No heading and no bold title line in a caption.
4. If the publishing date falls near an occasion, check it against the occasions file: [fa/occasions.md](fa/occasions.md) or [en/occasions.md](en/occasions.md).
5. A rhymed caption is still brand copy. Keep to one device that comes from the subject's own world: fa: sound devices (in Whalory Pro). English has no verse file yet, so follow the same rules with new English examples.

**Questions:** The "Captions and social media" row of the [question bank](intake.md#question-bank-by-task).
**References:** fa: [fa/forms.md#کپشن](fa/forms.md#کپشن), [fa/channels.md#اینستاگرام](fa/channels.md#اینستاگرام), fa/hooks.md (in Whalory Pro), fa/social-scripts.md#کپشنِ-همراه (in Whalory Pro) · en: [en/forms.md#caption](en/forms.md#caption), [en/channels.md#instagram](en/channels.md#instagram), [en/channels.md#tiktok](en/channels.md#tiktok), en/anchors.md#caption (in Whalory Pro)
**Output:** The caption; hashtags, if needed, on a separate line.
**QA:** The caption shows one moment and is not a full product introduction; emoji follow the profile. `--format caption`.

### Social post

Text-first feed posts on LinkedIn, X, Threads, Bluesky, and Facebook, where the words carry the post. A post under a photo or video on Instagram or TikTok is a [caption](#caption).

1. Name the platform and the author: a person's profile or a company page. The author's role sets the narrator; the profile sets the tone.
2. The opening line or two must work alone, before the platform folds the post. Put the news, the result, or the scene there, not a greeting. The fold and the limits of each platform are in [en/channels.md](en/channels.md) and [fa/channels.md](fa/channels.md).
3. One idea per post: one piece of news, one lesson, or one story, with one concrete detail from the materials. Numbers and names come only from the brief; a gap gets a bracket.
4. Short paragraphs, and a list only when the content is a real list. Links, mentions, and hashtags follow the platform and the profile; no hashtag inside a sentence.
5. End on one clear next step or one real question, with no summary and no moral.
6. For X and Bluesky, count characters the way the platform counts them: [en/channels.md#how-platforms-count-characters](en/channels.md#how-platforms-count-characters). In a thread, each post carries one idea, and the opening post stands on its own.

**Questions:** The "Captions and social media" row of the [question bank](intake.md#question-bank-by-task).
**References:** fa: [fa/channels.md#لینکدین](fa/channels.md#لینکدین), [fa/channels.md#ایکس](fa/channels.md#ایکس), [fa/forms.md#قصه‌ی-کوتاه-یا-پستِ-روایی](fa/forms.md#قصه‌ی-کوتاه-یا-پستِ-روایی) · en: [en/channels.md#linkedin](en/channels.md#linkedin), [en/channels.md#x](en/channels.md#x), [en/channels.md#threads](en/channels.md#threads), [en/channels.md#bluesky](en/channels.md#bluesky), [en/channels.md#facebook](en/channels.md#facebook), en/anchors.md#linkedin-post (in Whalory Pro)
**Output:** The post, with its character count in the platform's unit; for a thread, one numbered block per post.
**QA:** The opening works without the rest; one idea; no hashtag inside a sentence; nothing the brief does not support. `--format post`, and `--channel` with the platform's id when `data/channels/` is present.

## Headlines, ads, and campaigns

### Tagline and slogan

1. Ten headlines in ten different ways, then choose.
2. The substitution test, the page test, and reading aloud.
3. A slogan says what the brand does, in the brand's own words, with no superlative.
4. Delivery: the top three options, each with a one-line reason.

**Questions:** The "Base questions" row of the [question bank](intake.md#question-bank-by-task).
**References:** fa: [fa/forms.md#سرتیتر-و-بالای-صفحه](fa/forms.md#سرتیتر-و-بالای-صفحه), fa/headlines.md (in Whalory Pro), fa/rhetoric-fa.md (in Whalory Pro), fa/copywriting.md#تگ‌لاین (in Whalory Pro) · en: [en/forms.md#headline](en/forms.md#headline), en/headlines.md (in Whalory Pro), en/headlines.md#taglines (in Whalory Pro), en/copywriting.md (in Whalory Pro)
**Output:** Three headlines or slogans with their reasons; the rest of the ten only if the user asks.
**QA:** No empty curiosity-gap headline and no superlative without evidence. `--format headline`.

