# Writing task index

Whalory adds a professional writing workflow to the AI host the user already uses: understand the task, collect facts, select the user's voice, draft for the destination, review and export. A task contract describes the work; it does not prove that a model has generated a good example.

The [shared registry](../data/catalogs/writing-capabilities.json) contains 163 task contracts in 16 families, including 20 expanded flagship contracts. Its task IDs, bilingual names, input needs, output sections, evidence, limits, tone and review requirements are consumed by local tools, Studio and backend. Every row is `implemented_not_verified`: deterministic contract checks are separate from semantic quality, host compatibility, expert review and publication approval.

## Selective loading and everyday requests

Read this index, select a task, then read only that task in its family playbook. The Python API loads the selected contract into a portable generation pack. Do not paste the entire registry into a model context.

Task, operation, language and channel are separate. “کردنشیال شرکت‌مون” selects `credentials_sales.company_credential`; “جواب این دایرکت” selects `messaging.dm_reply`; “متن همه صفحه‌های ثبت‌نام” selects `ux.flow_microcopy`; “گزارش هیئت‌مدیره” selects `management.board_memo`. “Adapt this article for LinkedIn” selects `social.linkedin_post` with operation `adapt`, while preserving the source's facts and caveats.

Credentials means a presentation of company, agency or freelance qualifications, services, people and demonstrated work. It never means passwords, tokens, licenses fabricated as evidence, invented clients, or an altered official credential. Use only permitted work samples and attributable outcomes.

Lexical routing is transparent and bounded. It returns candidate IDs and an ambiguity flag, not a calibrated probability. If no named contract fits, use `operations.other_business_format`, explain the proposed structure, and resolve the reader goal and destination. Do not claim native tested support from a nearby label.

## Operations

| Operation | Result and required care |
|---|---|
| `write` | Draft from the selected contract and evidence. Missing facts remain marked. |
| `rewrite` | Improve supplied text while preserving facts, conditions and purpose. Report material meaning changes. |
| `translate` | Preserve information, units and claim scope in the target variant. |
| `adapt` | Change audience, channel or shape. Declare material omissions; do not invent new facts. |
| `plan` | Return task-specific outline, evidence plan and assumptions. A plan is not completed research. |
| `review` | Return findings, repairs and unresolved checks. Separate observable error, editorial choice and missing evidence. |
| `score` | Use the existing five-axis 0–4 editorial rubric with passage evidence. No AI-detection score or unvalidated probability. |
| `prepare_for_publication` | Prepare a draft and readiness notes. This does not publish. |
| `export` | Package supplied content in a supported format. JSON, Markdown, plain text and CSV are available locally. |

Word, slide, PDF, image and external publication artifacts require an actual host capability and their own output checks. An image brief is a description, not a generated asset. CSV export is an escaped section/content table; it is not a spreadsheet application or a complete arbitrary-SKU exporter.

## Facts and review

Use a fact ledger with stable ID, text, source, status and lock intent. `supplied` means the user supplied it; `confirmed` means the user confirmed it; neither means independently verified. `verified` requires a source. `unknown` is never asserted: it becomes an exact missing-data placeholder. `unverified` and `proposed` retain their status and need review.

Lock names, numbers, units, prices, percentages, dates, currencies, URLs, actual capabilities, conditions, limitations, promises, quotations and attribution. For an omitted material fact, report the exact omitted span and reason for review. Relative dates need the task date and timezone; do not equate event, publication and offer-expiry dates.

The local checker validates section presence, exact locked spans, evidence IDs and per-key placeholders. It cannot establish factual truth, semantic equivalence, legal sufficiency, naturalness or brand fit. Missing exact spans fail unless declared as omissions, which remain review warnings. A returned `passed: true` never sets `publication_ready: true`.

Humor is restricted for complaints, incidents, payment failure, health, bereavement and personnel issues. Use the customer's approved voice; Whalory's own brand personality is not automatically the customer's voice. A formal document still needs clear, concrete prose.

## Local API and handoff

The standard-library module `scripts/task_registry.py` works offline and makes no model, paid, publication or external-message call. Its API is:

```python
from task_registry import load_registry, list_tasks, get_task, detect_task
from task_registry import build_generation_pack, validate_output, export_output

route = detect_task("برای شرکت‌مون کردنشیال بنویس")
pack = build_generation_pack({
    "request": "Write a company credential", "language": "en",
    "task_id": "credentials_sales.company_credential", "operation": "write",
    "reader": "A prospective service client",
    "facts": [{"id": "role", "text": "We designed the prototype.",
               "source": "supplied case note", "status": "supplied", "locked": True}],
    "inputs": {"company_facts": "[confirm company identity]",
               "services": "Prototype design", "team": "[confirm team]",
               "approved_cases": "[confirm display permission]"}
})
```

The brief accepts `request` (or string `brief`), optional `task_id`, `operation`, `language`, `variant`, `market`, `reader`, `channel`, `date`, `timezone`, `profile`, `inputs`, `facts`, `source_text`, `locale_strings`, explicit `fact_locks`, `forbidden_additions`, `parent_artifact`, `interactive` and `no_questions`. Rewrite, adapt, translate, review and export need source text or locale strings; missing material is reported, not silently invented.

A generation pack includes the selected `task`, `contract`, `output_contract`, `context`, `source`, `facts_ledger`, `fact_locks`, `locale_locks`, `missing_inputs`, up to three `questions`, `prompt`, review status and explicit capability flags. `kind: writing_generation_pack` and `model_generation: false` distinguish it from generated copy. Parent/source metadata supports article-to-post, PRD-to-release-notes and credential-to-proposal chains without merging separate artifacts.

The local output envelope is `content` (object keyed by the selected output section IDs), `warnings` (array), and `evidence_refs` (array of supplied known fact IDs). Optional `locale_strings` preserves nesting, keys and placeholder multiplicity. `omissions` lists exact omitted material spans. Review and plan operations use their explicit alternate section contracts. A backend may adapt this structure for its provider; provider output still needs its own validation.

```text
python scripts/task_registry.py list --language fa
python scripts/task_registry.py detect "Write a board memo"
python scripts/task_registry.py show product.prd
python scripts/task_registry.py pack brief.json
python scripts/task_registry.py check pack.json output.json
python scripts/task_registry.py export pack.json output.json --format markdown
python evals/evaluate_writing.py --report reports/writing-evaluation.json
```

The CLI prints output; shell redirection or a host's file writer decides where to save it. Exporting does not grant permission to send, publish, change a price, create a financial transaction or use a paid provider. Customer-facing text/Markdown/CSV contain copy only. JSON keeps internal warnings and review metadata in a separate object.

## Families and contracts

### Copywriting and advertising

کپی‌رایتینگ و تبلیغات

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Ad copy and variants](writing/copy_ads.md#ad-variant) | متن و واریانت تبلیغ | offer, facts, reader, placement | headline, body, cta, variants |
| [Campaign concept](writing/copy_ads.md#campaign-concept) | کانسپت و پیام کمپین | campaign_goal, offer, audience, channels | concept, key_message, channel_map |
| [Search ad](writing/copy_ads.md#search-ad) | متن تبلیغ جست‌وجو | query_intent, offer, destination | headlines, descriptions, destination_note |
| [Display ad](writing/copy_ads.md#display-ad) | تبلیغ بنری و نمایشی | offer, audience, placement | headline, support_line, cta |
| [Paid social ad](writing/copy_ads.md#paid-social-ad) | تبلیغ شبکه‌ی اجتماعی | offer, audience, platform, asset_context | primary_text, headline, cta |
| [Retargeting copy](writing/copy_ads.md#retargeting-ad) | متن بازگشت مخاطب | offer, stage, previous_contact | message, cta, variants |
| [Headline bank](writing/copy_ads.md#headline-bank) | بانک تیتر | subject, facts, placement | distinct_headlines, selection_rationale |
| [Tagline and slogan](writing/copy_ads.md#tagline-slogan) | شعار و عبارت برند | brand_position, voice, proof | options, rationale, usage_note |
| [Print and outdoor copy](writing/copy_ads.md#print-outdoor-ad) | متن آگهی چاپی و محیطی | offer, reading_context, space | headline, body, contact_or_cta |
| [Offer announcement](writing/copy_ads.md#offer-announcement) | معرفی پیشنهاد یا تخفیف | price, terms, dates, eligibility | offer_copy, conditions, cta |

### Social media

شبکه‌های اجتماعی

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Instagram caption](writing/social.md#instagram-caption) | کپشن اینستاگرام | post_context, facts, reader | caption, cta, optional_tags |
| [LinkedIn post](writing/social.md#linkedin-post) | پست لینکدین | idea, evidence, author_role | post, optional_discussion_prompt |
| [X post and thread](writing/social.md#x-post-thread) | پست و رشته‌پست ایکس | idea, facts, thread_need | post_or_thread, ordered_units |
| [Threads post](writing/social.md#threads-post) | پست تردز | idea, facts, audience | post, optional_reply_prompt |
| [Bluesky post](writing/social.md#bluesky-post) | پست بلواسکای | idea, facts, links | post, link_context |
| [Facebook post](writing/social.md#facebook-post) | پست فیسبوک | idea, facts, group_or_page | post, cta |
| [YouTube title and description](writing/social.md#youtube-description) | توضیح و عنوان یوتیوب | video_content, actual_timestamps, links | title, description, chapters_if_supplied |
| [TikTok and short-video caption](writing/social.md#tiktok-caption) | کپشن تیک‌تاک و ویدیوی کوتاه | video_context, facts, platform | caption, optional_tags |
| [Story sequence](writing/social.md#story-sequence) | استوری چندفریمی | facts, frame_count, goal, visual_context | frame_copy, interaction_notes, final_cta |
| [Social carousel](writing/social.md#carousel) | کاروسل شبکه‌های اجتماعی | topic, facts, slide_budget | slide_copy, cover, closing, caption |
| [Other social platform post](writing/social.md#other-platform) | پست سایر شبکه‌ها و کانال‌ها | platform, purpose, facts | channel_adapted_copy, limits_note |

### Website and product pages

وب‌سایت و صفحه‌های محصول

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Landing page](writing/web.md#landing-page) | لندینگ پیج | offer, reader, proof, primary_action | hero, sections, proof, faq, cta |
| [Website homepage](writing/web.md#homepage) | صفحه‌ی اصلی وب‌سایت | product_map, audiences, actions | hero, pathways, summary, nav_copy |
| [About page](writing/web.md#about-page) | صفحه‌ی درباره‌ی ما | history, team, facts | about_copy, team_intro, contact_path |
| [Feature page](writing/web.md#feature-page) | صفحه‌ی قابلیت | actual_feature, use_cases, limitations | problem, behavior, examples, cta |
| [Use-case page](writing/web.md#use-case-page) | صفحه‌ی کاربرد یا صنعت | reader_job, workflow, actual_capabilities | scenario, workflow, proof, cta |
| [Pricing explanation](writing/web.md#pricing-explainer) | توضیح پلن و قیمت | approved_prices, terms, entitlements | plan_copy, comparison, questions |
| [FAQ page](writing/web.md#faq-page) | صفحه‌ی پرسش‌های متداول | actual_questions, verified_answers | question_answer_pairs, links |
| [Contact and collaboration page](writing/web.md#contact-page) | صفحه‌ی تماس و همکاری | contact_routes, response_policy | contact_copy, form_hints, expectations |
| [Download and installation page](writing/web.md#download-install-page) | صفحه‌ی دانلود و نصب | verified_hosts, versions, steps | host_paths, commands, troubleshooting |
| [Product comparison page](writing/web.md#comparison-page) | صفحه‌ی مقایسه‌ی محصول | competitor_sources, own_capabilities, date | criteria_table, context, limitations |

### UX writing for websites and apps

یوایکس رایتینگ وب‌سایت و اپلیکیشن

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Complete website or app flow copy](writing/ux.md#flow-microcopy) | متن کامل یک جریان وب یا اپ | flow_states, user_goal, system_behavior | state_string_map, notes, fallbacks |
| [Button and label copy](writing/ux.md#button-label) | دکمه و لیبل | action, result, space | labels, alternatives |
| [Form labels and hints](writing/ux.md#form-hint) | فرم و راهنمای فیلد | field_purpose, validation, data_use | labels, hints, validation_messages |
| [Onboarding copy](writing/ux.md#onboarding) | آنبوردینگ و نخستین استفاده | product_job, steps, permissions | intro, step_copy, skip_copy |
| [Error and recovery copy](writing/ux.md#error-recovery) | پیام خطا و بازیابی | error_cause, data_state, allowed_actions | title, body, recovery_cta |
| [Empty and loading states](writing/ux.md#empty-loading) | حالت خالی و انتظار | state, cause, next_action | empty_copy, loading_copy, cancel_copy |
| [Confirmation and success copy](writing/ux.md#confirmation-success) | تأیید و موفقیت | actual_result, next_step, reference_data | confirmation, summary, next_action |
| [Push notification](writing/ux.md#push-notification) | پوش نوتیفیکیشن | event, recipient_context, deep_link | title, body, destination_note |
| [Consent and permission copy](writing/ux.md#consent-permissions) | رضایت و دسترسی | data_purpose, scope, retention, choices | notice, choices, settings_copy |
| [Locale-file copy review](writing/ux.md#locale-file-review) | متن فایل‌های زبان محصول | locale_file, key_context, variables | safe_string_updates, change_notes |

### SEO and editorial publishing

سئو، مقاله و نشر تخصصی

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [SEO article](writing/seo_editorial.md#article) | مقاله‌ی سئو شده | search_intent, verified_sources, reader, expertise | article, metadata, internal_links, image_brief |
| [SEO content brief](writing/seo_editorial.md#content-brief) | بریف محتوای سئو | topic, intent, source_scope, reader | outline, questions, evidence_plan |
| [Pillar page](writing/seo_editorial.md#pillar-page) | صفحه‌ی پیلار | topic_scope, subtopics, sources | pillar_copy, subpage_links, glossary |
| [Topic-cluster plan](writing/seo_editorial.md#topic-cluster) | طرح خوشه‌ی محتوایی | audience, topic, existing_pages | cluster_map, briefs, link_plan |
| [Metadata and search snippets](writing/seo_editorial.md#meta-snippets) | متاتایتل و متادیسکریپشن | page_content, intent, brand | title, description, variants |
| [Editorial newsletter](writing/seo_editorial.md#newsletter) | خبرنامه‌ی تحلیلی یا آموزشی | theme, sources, reader, send_context | subject, preheader, body, links |
| [Thought-leadership article](writing/seo_editorial.md#thought-leadership) | مقاله‌ی دیدگاه حرفه‌ای | thesis, evidence, author_experience | argument, examples, counterpoints |
| [White paper and guide](writing/seo_editorial.md#whitepaper) | وایت‌پیپر و راهنمای عمیق | scope, sources, method, reader | structured_document, evidence, limitations |
| [Business research summary](writing/seo_editorial.md#research-summary) | خلاصه‌ی پژوهش برای کسب‌وکار | supplied_paper, decision_context | summary, implications, limitations |
| [Content refresh](writing/seo_editorial.md#content-refresh) | به‌روزرسانی مقاله‌ی قدیمی | current_article, new_sources, change_goal | revised_article, change_log, metadata |

### Brand voice and verbal identity

صدای برند و هویت کلامی

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Brand voice profile](writing/brand.md#voice-profile) | پروفایل صدای برند | brand_facts, samples, reader, formats | VOICE_md, voice_json, examples |
| [Verbal identity guide](writing/brand.md#verbal-identity) | سند هویت کلامی | position, audiences, voice_samples | principles, tone_matrix, examples |
| [Positioning statement](writing/brand.md#positioning-statement) | بیانیه‌ی جایگاه‌یابی | segment, problem, offer, proof | statement, rationale, evidence_gaps |
| [Messaging architecture](writing/brand.md#message-house) | معماری پیام برند | position, proof, segments | core_message, pillars, evidence_map |
| [Brand story](writing/brand.md#brand-story) | داستان برند | verified_history, people, turning_points | story, short_version, source_notes |
| [Brand manifesto](writing/brand.md#manifesto) | مانیفست برند | values, actual_commitments, reader | manifesto, commitment_map |
| [Naming concepts and rationale](writing/brand.md#naming-rationale) | نام‌گذاری و منطق نام | brief, constraints, language_context | name_options, rationale, screening_plan |
| [Brand terminology glossary](writing/brand.md#terminology) | واژه‌نامه و اصطلاحات برند | terms, product_concepts, locales | glossary, preferred_avoided_forms |
| [Situational tone matrix](writing/brand.md#tone-matrix) | ماتریس لحن موقعیت‌ها | base_voice, situations, channels | matrix, examples, guardrails |
| [Brand voice audit](writing/brand.md#brand-review) | ممیزی صدای محتوای برند | content_samples, approved_voice | findings, repairs, priorities |

### Products, catalogs and commerce

محصول، کاتالوگ و فروشگاه

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Product description](writing/commerce.md#product-description) | توضیح محصول | product_sheet, facts, reader | description, features, conditions |
| [Product specifications](writing/commerce.md#product-specification) | مشخصات و جدول محصول | verified_specs, units, variants | spec_table, definitions, gaps |
| [Category page](writing/commerce.md#category-page) | صفحه‌ی دسته‌بندی فروشگاه | catalog, selection_criteria, reader | intro, buying_guidance, links |
| [Marketplace listing](writing/commerce.md#marketplace-listing) | آگهی بازارگاه | product_facts, platform, fields | title, fields, description |
| [App-store listing](writing/commerce.md#app-store-listing) | متن صفحه‌ی اپلیکیشن | actual_features, version, store | title, short_copy, description, release_notes |
| [Brand catalog](writing/commerce.md#brand-catalog) | کاتالوگ برند | approved_brand, product_data, prices, assets | catalog_structure, item_copy, index, cta |
| [Service catalog](writing/commerce.md#service-catalog) | کاتالوگ خدمات | services, scope, prices, terms | service_cards, comparison, conditions |
| [Batch SKU copy](writing/commerce.md#sku-batch) | متن دسته‌ای محصولات | csv_or_json, field_mapping, locale | per_sku_copy, issues_manifest |
| [Packaging and label copy](writing/commerce.md#packaging-label) | متن بسته‌بندی و لیبل | approved_specs, label_constraints, market | front_back_copy, required_fields, gaps |
| [Sales brochure](writing/commerce.md#sales-brochure) | بروشور فروش | offer, proof, audience, format | sections, short_copy, contact_path |

### Credentials, presentations and business development

کردنشیال، ارائه و توسعه‌ی کسب‌وکار

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Company credential profile](writing/credentials_sales.md#company-credential) | کردنشیال و پروفایل شرکت | company_facts, services, team, approved_cases | profile_sections, evidence, cases, contact |
| [Agency credentials deck](writing/credentials_sales.md#agency-credential) | کردنشیال آژانس | agency_services, team, case_evidence | deck_copy, service_map, cases |
| [Freelancer credential profile](writing/credentials_sales.md#freelancer-profile) | پروفایل و کردنشیال فریلنسر | skills, verified_work, scope, availability | profile, selected_work, offer, contact |
| [Professional and executive bio](writing/credentials_sales.md#professional-bio) | بیو حرفه‌ای و معرفی مدیر | cv, verified_roles, reader, length | short_medium_long_bio |
| [Portfolio copy](writing/credentials_sales.md#portfolio) | پورتفولیو و معرفی نمونه‌کار | work_samples, role, permission | project_intros, role, process, outcome |
| [Evidence-backed case study](writing/credentials_sales.md#case-study) | کیس‌استادی مستند | case_facts, role, baseline, outcome, evidence | problem, approach, results, limits |
| [Business and freelance proposal](writing/credentials_sales.md#proposal) | پروپوزال و پیشنهاد همکاری | client_need, scope, deliverables, terms | proposal, scope, timeline, terms |
| [RFP and tender response](writing/credentials_sales.md#rfp-response) | پاسخ به RFP و مناقصه | rfp, capabilities, evidence, terms | compliance_matrix, response, gaps |
| [Business and investor pitch deck](writing/credentials_sales.md#pitch-deck) | پیچ‌دک کسب‌وکار و سرمایه‌گذار | problem, solution, metrics, market_sources, ask | slide_copy, speaker_notes, evidence |
| [Statement of work draft](writing/credentials_sales.md#sow) | شرح کار و دامنه‌ی قرارداد | scope, deliverables, roles, acceptance | sow_draft, assumptions, review_items |

### DM, email and SMS

دایرکت، ایمیل و پیامک

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Direct-message reply](writing/messaging.md#dm-reply) | پاسخ دایرکت | incoming_message, case_facts, policy | reply, optional_clarifying_question |
| [Direct-message outreach](writing/messaging.md#dm-outreach) | دایرکت معرفی و همکاری | recipient_context, offer, relationship | short_dm, optional_followup |
| [DM follow-up](writing/messaging.md#dm-followup) | پیگیری دایرکت | previous_thread, time_context, next_step | followup, close_option |
| [Customer email](writing/messaging.md#customer-email) | ایمیل به مشتری | purpose, facts, recipient_stage | subject, preheader, body, cta |
| [Cold outreach email](writing/messaging.md#cold-email) | ایمیل معرفی سرد | recipient_public_context, offer, proof | subject, email, soft_cta |
| [Email sequence](writing/messaging.md#email-sequence) | توالی ایمیل | goal, stages, offer, approved_cadence | sequence, entry_exit_notes |
| [Transactional SMS and verification code](writing/messaging.md#sms-transactional) | پیامک تراکنشی و کد تأیید | event, variables, sender, expiry | sms_template, variables |
| [Promotional SMS](writing/messaging.md#sms-promotion) | پیامک تبلیغاتی | offer, terms, recipient_scope | sms, conditions, cta |
| [Messenger-channel post](writing/messaging.md#messenger-channel) | متن کانال تلگرام و پیام‌رسان‌ها | channel, facts, links, goal | post, button_labels, links |
| [Event invitation and reminder](writing/messaging.md#event-invitation) | دعوت‌نامه و یادآوری رویداد | event, date, timezone, location, registration | invitation, reminder, cta |

### Support and difficult communications

پشتیبانی و ارتباطات دشوار

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Customer-support reply](writing/support.md#customer-reply) | پاسخ تیکت مشتری | ticket, case_facts, policy, allowed_actions | reply, next_steps |
| [Complaint response](writing/support.md#complaint-response) | پاسخ شکایت و نارضایتی | complaint, verified_events, remedy | acknowledgment, explanation, action |
| [Public-review reply](writing/support.md#review-reply) | پاسخ نظر عمومی | review, case_facts, public_scope | public_reply, private_followup_route |
| [Outage notice](writing/support.md#outage-notice) | اطلاع‌رسانی اختلال | affected_scope, known_status, next_update | notice, status, update_path |
| [Delay notice](writing/support.md#delay-notice) | پیام تأخیر و بدقولی | original_commitment, actual_status, new_plan | notice, options, next_update |
| [Refund and return response](writing/support.md#refund-return) | بازپرداخت و مرجوعی | policy, case_status, eligible_actions | reply, steps, conditions |
| [Price-change communication](writing/support.md#price-change-notice) | اطلاع تغییر قیمت | approved_change, effective_date, existing_terms | notice, faq, options |
| [Difficult stakeholder message](writing/support.md#hard-message) | پیام سخت به ذی‌نفعان | decision, reason, affected_people, options | message, questions, next_steps |
| [Chatbot conversation flow](writing/support.md#chatbot-flow) | دیالوگ چت‌بات | intents, knowledge, actions, fallback | dialogue_nodes, transitions, handoff |
| [Help-center article](writing/support.md#help-article) | مقاله‌ی راهنما و مرکز کمک | actual_steps, version, known_failures | steps, screens_notes, troubleshooting |

### PR and media communications

روابط عمومی و رسانه

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Press release](writing/pr_media.md#press-release) | بیانیه و خبر رسمی | news, facts, approved_quotes, contact | release, boilerplate, contact |
| [Press kit](writing/pr_media.md#press-kit) | پرس‌کیت و معرفی رسانه‌ای | facts, approved_assets, spokespeople | fact_sheet, bios, assets_manifest |
| [Media pitch](writing/pr_media.md#media-pitch) | پیشنهاد سوژه به رسانه | angle, evidence, recipient_context | pitch, subject, source_offer |
| [Founder announcement](writing/pr_media.md#founder-announcement) | اعلان بنیان‌گذار | actual_event, founder_role, facts | announcement, short_version |
| [Crisis statement draft](writing/pr_media.md#crisis-statement) | بیانیه‌ی بحران | verified_events, unknowns, approved_actions | holding_statement, update, review_items |
| [Interview preparation](writing/pr_media.md#interview-qa) | آمادگی مصاحبه و پرسش‌وپاسخ | subject, facts, spokesperson, known_questions | question_answers, bridges, gaps |
| [Executive speech](writing/pr_media.md#executive-speech) | سخنرانی مدیر | occasion, audience, facts, speaker_voice | speech, delivery_notes |
| [Event and speaker introduction](writing/pr_media.md#event-intro) | معرفی سخنران و مراسم | verified_bio, event_context, pronunciation | intro, transition |
| [Partnership announcement](writing/pr_media.md#partnership-announcement) | اعلان همکاری مشترک | approved_scope, partners, permissions | announcement, partner_copy, faq |
| [Public stakeholder Q&A](writing/pr_media.md#public-qa) | پرسش‌وپاسخ عمومی ذی‌نفعان | actual_questions, facts, approved_policy | qa, unresolved_items |

### Product management and development

مدیریت محصول و توسعه

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Product requirements document](writing/product.md#prd) | سند نیازمندی محصول PRD | problem, evidence, scope, constraints | prd, requirements, risks, open_questions |
| [Product problem statement](writing/product.md#problem-statement) | بیانیه‌ی مسئله‌ی محصول | user_evidence, context, impact | statement, evidence, gaps |
| [Product opportunity brief](writing/product.md#opportunity-brief) | بریف فرصت محصول | signals, users, business_context | brief, options, unknowns |
| [User stories and behavior scenarios](writing/product.md#user-stories) | استوری کاربر و رفتارها | roles, goals, flows, constraints | stories, edge_cases |
| [Product acceptance criteria](writing/product.md#acceptance-criteria) | معیار پذیرش محصول | requirements, states, edge_cases | criteria, examples |
| [Roadmap narrative](writing/product.md#roadmap) | روایت و توضیح رودمپ | goals, initiatives, capacity, dependencies | roadmap_narrative, tradeoffs, uncertainties |
| [Release notes](writing/product.md#release-notes) | یادداشت انتشار و تغییرات | merged_changes, version, known_issues | notes, user_impact, limitations |
| [Discovery synthesis](writing/product.md#discovery-synthesis) | جمع‌بندی کشف و مصاحبه | research_notes, method, participant_scope | themes, evidence, questions |
| [Product experiment plan](writing/product.md#experiment-plan) | طرح آزمایش محصول | hypothesis, baseline, metrics, constraints | plan, decision_rules, risks |
| [Product strategy narrative](writing/product.md#strategy) | استراتژی محصول | market_evidence, goals, capabilities | choices, rationale, assumptions, actions |

### Management, strategy and reporting

مدیریت، استراتژی و گزارش

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Business strategy memo](writing/management.md#strategy-memo) | یادداشت استراتژی کسب‌وکار | context, evidence, goals, options | memo, choices, tradeoffs, actions |
| [Management decision memo](writing/management.md#decision-memo) | یادداشت تصمیم مدیریتی | decision, options, evidence, constraints | recommendation, alternatives, risks |
| [Board memo](writing/management.md#board-memo) | یادداشت و گزارش هیئت‌مدیره | actual_performance, risks, decisions_needed | summary, performance, risks, asks |
| [OKR draft and review](writing/management.md#okr) | هدف و نتیجه‌ی کلیدی OKR | strategy, baseline, capacity, time_window | objectives, key_results, owners_to_confirm |
| [KPI and WBR/MBR/QBR report](writing/management.md#kpi-report) | گزارش شاخص و WBR/MBR/QBR | metrics, definitions, period, comparators | readout, drivers, uncertainties, actions |
| [Executive summary](writing/management.md#executive-summary) | خلاصه‌ی اجرایی | source_document, decision_context | summary, key_findings, asks |
| [Business plan narrative](writing/management.md#business-plan) | طرح کسب‌وکار | model, market_sources, assumptions, capacity | plan, assumptions, scenarios |
| [Budget and financial narrative](writing/management.md#budget-narrative) | توضیح بودجه و سناریوی مالی | actual_budget, assumptions, approved_scenarios | narrative, variance, risks |
| [Management risk report](writing/management.md#risk-report) | گزارش ریسک مدیریتی | observed_risks, evidence, owners | risk_summary, options, open_items |
| [Investor update](writing/management.md#investor-update) | گزارش به سرمایه‌گذار | actual_metrics, milestones, risks, asks | update, metrics, asks |

### Operations, process and work documents

فرایند، عملیات و اسناد کار

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Standard operating procedure](writing/operations.md#sop) | روش اجرایی استاندارد SOP | actual_process, roles, systems, exceptions | sop, steps, checks, exceptions |
| [Work instruction](writing/operations.md#work-instruction) | دستور کار عملیاتی | task, tools, conditions, checks | steps, warnings, completion_check |
| [Meeting agenda](writing/operations.md#meeting-agenda) | دستور جلسه | purpose, topics, participants, time_budget | agenda, prep, decisions |
| [Meeting minutes and follow-up](writing/operations.md#meeting-minutes) | صورت‌جلسه و پیگیری | notes, decisions, assigned_actions | minutes, action_register, open_items |
| [Project status update](writing/operations.md#project-status) | گزارش وضعیت پروژه | actual_status, milestones, risks | status, blockers, decisions_needed |
| [Handover document](writing/operations.md#handover) | سند تحویل و انتقال کار | current_state, assets, owners, open_work | handover, checklist, references |
| [Internal policy draft](writing/operations.md#policy-draft) | پیش‌نویس سیاست و مقررات داخلی | approved_intent, scope, jurisdiction, roles | policy_draft, exceptions, review_items |
| [Internal knowledge-base article](writing/operations.md#knowledge-base) | مقاله‌ی دانش داخلی | source_material, workflow, reader | article, examples, references |
| [Incident postmortem](writing/operations.md#postmortem) | گزارش رخداد و درس‌آموخته | timeline, evidence, impact, actions | timeline, causes_to_confirm, actions |
| [Process-change communication](writing/operations.md#process-change) | اعلان تغییر فرایند | approved_change, affected_roles, date | change_notice, steps, faq |
| [Regulated-information draft](writing/operations.md#regulated-information) | پیش‌نویس اطلاعات سلامت، مالی یا حقوقی | topic, market, verified_sources, reviewer | draft, sources, review_gates |
| [Custom business writing format](writing/operations.md#other-business-format) | قالب نوشتاری سفارشی کسب‌وکار | goal, reader, input_material, destination | agreed_structure, copy, qa_notes |

### People and team communications

منابع انسانی و ارتباطات تیم

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Job description](writing/people.md#job-description) | شرح شغل | actual_role, scope, requirements, terms | job_description, success_expectations |
| [Recruitment ad](writing/people.md#recruitment-ad) | آگهی استخدام | approved_role, terms, application_route | ad, requirements, apply_copy |
| [Employee onboarding guide](writing/people.md#employee-onboarding) | آن‌بوردینگ کارکنان | actual_process, roles, resources | guide, first_steps, contacts |
| [Employee handbook draft](writing/people.md#handbook) | راهنمای کارکنان | approved_policies, jurisdiction, resources | handbook, policy_links, review_items |
| [Performance feedback](writing/people.md#performance-feedback) | بازخورد عملکرد | observations, impact, role_expectations | feedback, examples, agreement_questions |
| [Performance-review narrative](writing/people.md#performance-review) | گزارش ارزیابی عملکرد | verified_outcomes, criteria, employee_context | review, evidence, growth_plan |
| [Interview scorecard copy](writing/people.md#interview-scorecard) | فرم و متن ارزیابی مصاحبه | role_criteria, interview_evidence | questions, rubric, evidence_notes |
| [Culture and values memo](writing/people.md#culture-memo) | پیام فرهنگ و ارزش‌ها | actual_values, examples, context | memo, behavior_examples |
| [Organizational-change message](writing/people.md#change-announcement) | اعلان تغییر سازمانی | approved_change, known_impacts, next_steps | message, faq, support_routes |
| [Exit and transition communication](writing/people.md#exit-transition) | ارتباطات خروج و انتقال مسئولیت | approved_facts, transition_plan, audience | message, handover_notice, review_items |

### Scripts, storytelling and learning

اسکریپت، روایت و آموزش

| Task | فارسی | Required input | Output sections |
|---|---|---|---|
| [Short and long video script](writing/scripts_training.md#video-script) | اسکریپت ویدیوی کوتاه و بلند | goal, facts, duration, format | script, visual_notes, spoken_copy |
| [Reels script](writing/scripts_training.md#reel-script) | اسکریپت ریلز | idea, facts, visual_context | opening, beats, spoken_copy, caption |
| [Podcast script](writing/scripts_training.md#podcast-script) | اسکریپت پادکست | topic, sources, host_voice, format | intro, segments, transitions, outro |
| [Webinar script](writing/scripts_training.md#webinar-script) | اسکریپت وبینار | learning_goal, material, duration | run_of_show, spoken_notes, qa_prompts |
| [Product explainer script](writing/scripts_training.md#explainer-script) | اسکریپت توضیح محصول | actual_workflow, reader, facts | script, demo_notes, cta |
| [Training-module text](writing/scripts_training.md#training-module) | متن ماژول آموزشی | learning_goal, sources, reader_level | lesson, examples, exercise |
| [Workshop facilitation script](writing/scripts_training.md#workshop-facilitation) | متن تسهیلگری کارگاه | goal, participants, activities, time | facilitator_notes, prompts, debrief |
| [Course description and syllabus](writing/scripts_training.md#course-description) | معرفی دوره و سرفصل | actual_curriculum, instructor_facts, terms | description, syllabus, prerequisites |
| [Business storytelling draft](writing/scripts_training.md#story-narrative) | روایت و داستان کسب‌وکار | actual_material, fiction_permission, reader | story, short_version, source_notes |
| [Presentation copy and speaker notes](writing/scripts_training.md#presentation-notes) | متن اسلاید و یادداشت ارائه | purpose, evidence, audience, slide_budget | slide_copy, speaker_notes, source_notes |
