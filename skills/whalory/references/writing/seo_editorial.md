# SEO and editorial publishing / سئو، مقاله و نشر تخصصی

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Answer a search or editorial question with attributable evidence.

Tone: Useful explanation; separate observation, inference and advice. Avoid: Keyword stuffing, fake research, invented expertise and unsupported recency.

Evidence: Source title or identifier, date, relevance, limitations and approved links.

Destination budget: Length follows intent and supplied brief; no invented search-engine length rule.

Shared craft: [existing family method](../playbooks-web.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [SEO article](#article)
- [SEO content brief](#content-brief)
- [Pillar page](#pillar-page)
- [Topic-cluster plan](#topic-cluster)
- [Metadata and search snippets](#meta-snippets)
- [Editorial newsletter](#newsletter)
- [Thought-leadership article](#thought-leadership)
- [White paper and guide](#whitepaper)
- [Business research summary](#research-summary)
- [Content refresh](#content-refresh)

## Article

**مقاله‌ی سئو شده · `seo_editorial.article`**

Answer the search intent with supplied primary evidence and actual expertise. Separate research gaps from prose; image briefs are instructions, not generated assets.

Required inputs: search_intent, verified_sources, reader, expertise. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `article` / مقاله | Write a direct answer, evidenced explanation, useful examples and limitations. |
| `metadata` / فراداده | Provide title and description faithful to article content without invented search limits. |
| `internal_links` / پیوندهای داخلی | Suggest only known relevant internal destinations; mark unavailable URLs. |
| `image_brief` / بریف تصویر | Describe image purpose, placement and alt; identify whether an asset exists. |

Review: Source quality: review the actual SEO article against supplied evidence. Search intent: review the actual SEO article against supplied evidence. No keyword stuffing: review the actual SEO article against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Content Brief

**بریف محتوای سئو · `seo_editorial.content_brief`**

Translate intent into a researchable article plan without inventing keyword volume.

Required inputs: topic, intent, source_scope, reader. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `outline` / طرح کلی | Organize headings by reader question. |
| `questions` / پرسش‌ها | List questions the article must answer. |
| `evidence_plan` / برنامهٔ شواهد | Map planned claims to sources still needed. |

Review: Intent clarity: review the actual SEO content brief against supplied evidence. Source plan: review the actual SEO content brief against supplied evidence. No fake volume: review the actual SEO content brief against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Pillar Page

**صفحه‌ی پیلار · `seo_editorial.pillar_page`**

Define the topic boundary, then orient readers to distinct subtopics.

Required inputs: topic_scope, subtopics, sources. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `pillar_copy` / متن اصلی موضوع | Explain the central topic with source-backed sections. |
| `subpage_links` / پیوند زیرصفحه‌ها | Link to existing or explicitly proposed subpages. |
| `glossary` / واژه‌نامه | Define necessary terms in reader language. |

Review: Coverage coherence: review the actual Pillar page against supplied evidence. Source quality: review the actual Pillar page against supplied evidence. Link integrity: review the actual Pillar page against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Topic Cluster

**طرح خوشه‌ی محتوایی · `seo_editorial.topic_cluster`**

Map different reader intentions before grouping pages; traffic effects require data.

Required inputs: audience, topic, existing_pages. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `cluster_map` / نقشهٔ خوشه | Show topic, intent and intended page relationships. |
| `briefs` / بریف‌ها | Give each page a non-duplicative brief. |
| `link_plan` / برنامهٔ پیوند | Explain useful links without unsupported ranking promises. |

Review: No cannibalization claim without data: review the actual Topic-cluster plan against supplied evidence. Intent distinctness: review the actual Topic-cluster plan against supplied evidence. Source plan: review the actual Topic-cluster plan against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Meta Snippets

**متاتایتل و متادیسکریپشن · `seo_editorial.meta_snippets`**

Summarize the actual page accurately and preserve important qualifications.

Required inputs: page_content, intent, brand. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `title` / عنوان | Give page-faithful title options. |
| `description` / توضیح | Describe the answer or offer actually on the page. |
| `variants` / گزینه‌ها | Differentiate angles without claiming a universal search cutoff. |

Review: Page consistency: review the actual Metadata and search snippets against supplied evidence. No fake search limits: review the actual Metadata and search snippets against supplied evidence. No clickbait: review the actual Metadata and search snippets against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Newsletter

**خبرنامه‌ی تحلیلی یا آموزشی · `seo_editorial.newsletter`**

Choose a reader benefit from the supplied theme and sources, then make links useful.

Required inputs: theme, sources, reader, send_context. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `subject` / موضوع پیام | Write an honest subject line. |
| `preheader` / پیش‌نمایش | Use preheader to add context rather than duplicate. |
| `body` / متن | Curate and explain the sourced material. |
| `links` / پیوندها | Preserve URLs and identify what each opens. |

Review: Source quality: review the actual Editorial newsletter against supplied evidence. Link integrity: review the actual Editorial newsletter against supplied evidence. Reader value: review the actual Editorial newsletter against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Thought Leadership

**مقاله‌ی دیدگاه حرفه‌ای · `seo_editorial.thought_leadership`**

State a thesis with evidence and counterpoints; cited experience must not become the author's lived experience.

Required inputs: thesis, evidence, author_experience. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `argument` / استدلال | Develop the argument with fact/inference separation. |
| `examples` / مثال‌ها | Use actual examples and attributed experience. |
| `counterpoints` / دیدگاه‌های دیگر | Include credible limitations or alternative interpretations. |

Review: No fake experience: review the actual Thought-leadership article against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Inference labels: review the actual Thought-leadership article against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Whitepaper

**وایت‌پیپر و راهنمای عمیق · `seo_editorial.whitepaper`**

Describe method and evidence before claiming findings; a literature synthesis is not original research.

Required inputs: scope, sources, method, reader. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `structured_document` / سند | Organize scope, method, findings and implications. |
| `evidence` / شواهد | Trace material claims to supplied sources. |
| `limitations` / محدودیت‌ها | Explain data and method limitations. |

Review: Method clarity: review the actual White paper and guide against supplied evidence. Source quality: review the actual White paper and guide against supplied evidence. Do not invent participants, interviews, study methods, findings or researcher authority. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Research Summary

**خلاصه‌ی پژوهش برای کسب‌وکار · `seo_editorial.research_summary`**

Preserve the study question, method and scope before discussing implications.

Required inputs: supplied_paper, decision_context. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `summary` / خلاصه | Summarize actual findings and uncertainty. |
| `implications` / کاربرد و برداشت | Explain decision relevance as inference where appropriate. |
| `limitations` / محدودیت‌ها | Retain caveats, population limits and causal boundaries. |

Review: Compare the output to source meaning including material qualifications, negations and uncertainty. Separate observed change from causal attribution and retain plausible concurrent factors. Uncertainty: review the actual Business research summary against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Content Refresh

**به‌روزرسانی مقاله‌ی قدیمی · `seo_editorial.content_refresh`**

Compare old claims with supplied new evidence; do not silently erase history.

Required inputs: current_article, new_sources, change_goal. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `revised_article` / مقالهٔ بازنگری‌شده | Revise only justified passages and preserve relevant qualifications. |
| `change_log` / گزارش تغییر | List changed claims and the source that justified each. |
| `metadata` / فراداده | Update metadata to match the revised article. |

Review: Dated claims: review the actual Content refresh against supplied evidence. Fact locks: review the actual Content refresh against supplied evidence. Link integrity: review the actual Content refresh against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
