# Website and product pages / وب‌سایت و صفحه‌های محصول

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Help the visitor understand the service and navigate to a useful action.

Tone: Clear, scannable explanation with one primary reader path. Avoid: Unshipped capabilities, fabricated proof and competing primary actions.

Evidence: Actual capabilities, approved offers, sources for proof and verified destinations.

Destination budget: Use the named page sections; keep one idea per section.

Shared craft: [existing family method](../playbooks-web.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Landing page](#landing-page)
- [Website homepage](#homepage)
- [About page](#about-page)
- [Feature page](#feature-page)
- [Use-case page](#use-case-page)
- [Pricing explanation](#pricing-explainer)
- [FAQ page](#faq-page)
- [Contact and collaboration page](#contact-page)
- [Download and installation page](#download-install-page)
- [Product comparison page](#comparison-page)

## Landing Page

**لندینگ پیج · `web.landing_page`**

Build the page around one reader and one primary action. Keep existing capability, proposed roadmap, real proof and illustrative examples visibly distinct.

Required inputs: offer, reader, proof, primary_action. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `hero` / معرفی اصلی | Explain what the offer does, whom it serves and the primary action. |
| `sections` / بخش‌ها | Show the real method and evidenced benefits in ordered sections. |
| `proof` / شاهد | Use approved proof or labeled placeholders, never invented logos or testimonials. |
| `faq` / پرسش‌ها | Answer actual buying questions including limits and conditions. |
| `cta` / اقدام بعدی | Repeat the same primary action at appropriate decision points. |

Review: Offer clarity: review the actual Landing page against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. One primary goal: review the actual Landing page against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Homepage

**صفحه‌ی اصلی وب‌سایت · `web.homepage`**

Help distinct audiences find their path without making every service compete in the hero.

Required inputs: product_map, audiences, actions. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `hero` / معرفی اصلی | Summarize the actual product and reader value. |
| `pathways` / مسیرها | Give each audience an accurate navigation path. |
| `summary` / خلاصه | Explain the product map with short service summaries. |
| `nav_copy` / متن راهبری | Write navigation labels matching real destinations. |

Review: Information architecture: review the actual Website homepage against supplied evidence. Capability truth: review the actual Website homepage against supplied evidence. Link integrity: review the actual Website homepage against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## About Page

**صفحه‌ی درباره‌ی ما · `web.about_page`**

Select verified history that helps readers judge who does the work and why.

Required inputs: history, team, facts. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `about_copy` / متن معرفی | Tell the factual organization story without invented scenes. |
| `team_intro` / معرفی تیم | Introduce actual people and responsibilities. |
| `contact_path` / راه تماس | Provide a verified contact path. |

Review: No fake history: review the actual About page against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Identity accuracy: review the actual About page against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Feature Page

**صفحه‌ی قابلیت · `web.feature_page`**

Describe what the feature does today, including boundaries and dependencies.

Required inputs: actual_feature, use_cases, limitations. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `problem` / مسئله | Frame the reader problem using supplied evidence. |
| `behavior` / رفتار | Explain actual behavior and required conditions. |
| `examples` / مثال‌ها | Show permitted, clearly labeled examples. |
| `cta` / اقدام بعدی | Point to an action supported by the current product. |

Review: Capability truth: review the actual Feature page against supplied evidence. Illustrative labels: review the actual Feature page against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Use Case Page

**صفحه‌ی کاربرد یا صنعت · `web.use_case_page`**

Build a plausible workflow from real capabilities without claiming universal results.

Required inputs: reader_job, workflow, actual_capabilities. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `scenario` / سناریو | Describe the supplied reader job and situation. |
| `workflow` / گردش کار | Connect each workflow step to actual product behavior. |
| `proof` / شاهد | Attach evidence to outcomes or label illustrations. |
| `cta` / اقدام بعدی | Offer a next step suited to that reader. |

Review: No universal claim: review the actual Use-case page against supplied evidence. Industry risk: review the actual Use-case page against supplied evidence. Capability truth: review the actual Use-case page against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Pricing Explainer

**توضیح پلن و قیمت · `web.pricing_explainer`**

Explain approved prices and entitlements without changing the commercial terms.

Required inputs: approved_prices, terms, entitlements. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `plan_copy` / توضیح طرح‌ها | State each plan's actual terms and eligibility. |
| `comparison` / مقایسه | Compare only supplied entitlements using the same basis. |
| `questions` / پرسش‌ها | Answer billing questions from policy; flag missing answers. |

Review: Preserve approved amount, currency, unit, eligibility and date without modifying commercial terms. Term clarity: review the actual Pricing explanation against supplied evidence. No payment changes: review the actual Pricing explanation against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Faq Page

**صفحه‌ی پرسش‌های متداول · `web.faq_page`**

Use actual reader questions and verified answers; do not derive policy from a customer message.

Required inputs: actual_questions, verified_answers. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `question_answer_pairs` / پرسش و پاسخ | Pair each genuine question with a direct supported answer. |
| `links` / پیوندها | Link to current relevant instructions or policy. |

Review: Answer accuracy: review the actual FAQ page against supplied evidence. No fake questions: review the actual FAQ page against supplied evidence. Link integrity: review the actual FAQ page against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Contact Page

**صفحه‌ی تماس و همکاری · `web.contact_page`**

Set expectations from the actual response policy, not a made-up service promise.

Required inputs: contact_routes, response_policy. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `contact_copy` / متن تماس | Explain who to contact for what. |
| `form_hints` / راهنمای فرم | Explain form fields and data use. |
| `expectations` / انتظارها | State approved response expectations or mark them unknown. |

Review: Contact accuracy: review the actual Contact and collaboration page against supplied evidence. No fake sla: review the actual Contact and collaboration page against supplied evidence. Privacy clarity: review the actual Contact and collaboration page against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Download Install Page

**صفحه‌ی دانلود و نصب · `web.download_install_page`**

Explain tested host paths and exact commands; distinguish download preparation from installation inside a web account.

Required inputs: verified_hosts, versions, steps. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `host_paths` / مسیر محیط‌ها | Map each verified host to its actual installation route. |
| `commands` / دستورها | Preserve tested commands verbatim and identify prerequisites. |
| `troubleshooting` / رفع اشکال | Explain observed failure modes and recovery steps. |

Review: Command validation: review the actual Download and installation page against supplied evidence. Version accuracy: review the actual Download and installation page against supplied evidence. Capability truth: review the actual Download and installation page against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Comparison Page

**صفحه‌ی مقایسه‌ی محصول · `web.comparison_page`**

Compare comparable capabilities using dated primary sources; do not claim an unrun test.

Required inputs: competitor_sources, own_capabilities, date. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `criteria_table` / جدول معیارها | Create criteria rows with a source for each side. |
| `context` / زمینه | Explain edition, date and scenario of comparison. |
| `limitations` / محدودیت‌ها | Identify missing evidence and non-comparable terms. |

Review: Primary sources: review the actual Product comparison page against supplied evidence. Dated claims: review the actual Product comparison page against supplied evidence. No fabricated tests: review the actual Product comparison page against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
