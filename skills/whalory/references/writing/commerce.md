# Products, catalogs and commerce / محصول، کاتالوگ و فروشگاه

Selective family playbook generated from the shared [writing registry](../../data/catalogs/writing-capabilities.json). Read the selected task only. Contract implementation is local; model quality and human review remain unverified.

Reader purpose: Help a buyer evaluate an item with accurate specifications and conditions.

Tone: Precise, helpful product language using consistent units. Avoid: Imputed stock, warranty, origin, compatibility, specs or discounts.

Evidence: SKU, variant, approved specifications, price dates and asset provenance.

Destination budget: Preserve row identity and requested fields; platform limits need dated verification.

Shared craft: [existing family method](../playbooks-product.md). [Operation and API contract](../task-index.md#local-api-and-handoff).

## Contents

- [Product description](#product-description)
- [Product specifications](#product-specification)
- [Category page](#category-page)
- [Marketplace listing](#marketplace-listing)
- [App-store listing](#app-store-listing)
- [Brand catalog](#brand-catalog)
- [Service catalog](#service-catalog)
- [Batch SKU copy](#sku-batch)
- [Packaging and label copy](#packaging-label)
- [Sales brochure](#sales-brochure)

## Product Description

**توضیح محصول · `commerce.product_description`**

Translate verified specifications into useful explanations without inferring new benefits.

Required inputs: product_sheet, facts, reader. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `description` / توضیح | Describe the actual item and intended use. |
| `features` / ویژگی‌ها | List supported features with precise units. |
| `conditions` / شرایط | Include material compatibility, care, availability or warranty conditions only when supplied. |

Review: Spec integrity: review the actual Product description against supplied evidence. Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. No fake benefits: review the actual Product description against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Product Specification

**مشخصات و جدول محصول · `commerce.product_specification`**

Keep variants and units explicit; unknown dimensions never become zero.

Required inputs: verified_specs, units, variants. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `spec_table` / جدول مشخصات | Create a specification table with values and units. |
| `definitions` / تعریف‌ها | Explain technical terms only where needed. |
| `gaps` / کمبودها | List missing or conflicting specs for confirmation. |

Review: Unit integrity: review the actual Product specifications against supplied evidence. No imputed specs: review the actual Product specifications against supplied evidence. Variant accuracy: review the actual Product specifications against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Category Page

**صفحه‌ی دسته‌بندی فروشگاه · `commerce.category_page`**

Help selection within the actual catalog without claiming stock or superiority.

Required inputs: catalog, selection_criteria, reader. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `intro` / مقدمه | Explain what the category contains. |
| `buying_guidance` / راهنمای انتخاب | Give selection criteria grounded in supplied specs. |
| `links` / پیوندها | Link to actual relevant items. |

Review: Catalog consistency: review the actual Category page against supplied evidence. No fake stock: review the actual Category page against supplied evidence. Link integrity: review the actual Category page against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Marketplace Listing

**آگهی بازارگاه · `commerce.marketplace_listing`**

Match supplied item facts to the destination's actual field structure.

Required inputs: product_facts, platform, fields. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `title` / عنوان | Write a factual title using approved product identity. |
| `fields` / فیلدها | Populate requested fields without invented specs. |
| `description` / توضیح | Explain item use and conditions within verified destination limits. |

Review: Platform rules: review the actual Marketplace listing against supplied evidence. Spec integrity: review the actual Marketplace listing against supplied evidence. Do not invent a maximum; distinguish characters, graphemes, bytes, units and SMS segments. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## App Store Listing

**متن صفحه‌ی اپلیکیشن · `commerce.app_store_listing`**

Describe shipped functionality for the stated version and store.

Required inputs: actual_features, version, store. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `title` / عنوان | Write the factual app name or title variant. |
| `short_copy` / متن کوتاه | Summarize the current reader value. |
| `description` / توضیح | Explain actual features and limitations. |
| `release_notes` / یادداشت انتشار | Include only changes delivered in the supplied version. |

Review: Capability truth: review the actual App-store listing against supplied evidence. Version accuracy: review the actual App-store listing against supplied evidence. Store rules: review the actual App-store listing against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Brand Catalog

**کاتالوگ برند · `commerce.brand_catalog`**

Decide whether this is a brand introduction or a dated sales catalog. Preserve each SKU, variant, price, unit and row identity; an asset brief is separate from approved imagery.

Required inputs: approved_brand, product_data, prices, assets. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `catalog_structure` / ساختار کاتالوگ | Give cover, introduction, categories, item pages, terms and contact structure. |
| `item_copy` / متن اقلام | Write item-specific copy with verified specifications and conditions keyed by SKU. |
| `index` / فهرست | Provide an index that points to the correct item and variant. |
| `cta` / اقدام بعدی | Use the approved contact or purchase path; keep the missing-data manifest separate. |

Review: Sku integrity: review the actual Brand catalog against supplied evidence. Preserve approved amount, currency, unit, eligibility and date without modifying commercial terms. List each actual asset source and usage permission; placeholders or briefs are not delivered assets. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Service Catalog

**کاتالوگ خدمات · `commerce.service_catalog`**

Define each service by scope, exclusions and approved terms rather than implied guarantees.

Required inputs: services, scope, prices, terms. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `service_cards` / معرفی خدمات | Describe each service and its deliverables. |
| `comparison` / مقایسه | Compare services on the same approved criteria. |
| `conditions` / شرایط | State prices, dates, dependencies and exclusions. |

Review: Separate included deliverables, exclusions, dependencies and agreement status. Preserve approved amount, currency, unit, eligibility and date without modifying commercial terms. No fake guarantees: review the actual Service catalog against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Sku Batch

**متن دسته‌ای محصولات · `commerce.sku_batch`**

Confirm or declare the column map, then work row by row without overwriting original data.

Required inputs: csv_or_json, field_mapping, locale. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `per_sku_copy` / متن هر شناسهٔ کالا | Return generated fields keyed to unchanged row/SKU identities. |
| `issues_manifest` / فهرست مسائل | Report per-row gaps and failures so partial output cannot look complete. |

Review: Row identity: review the actual Batch SKU copy against supplied evidence. Spec integrity: review the actual Batch SKU copy against supplied evidence. Partial failure: review the actual Batch SKU copy against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Packaging Label

**متن بسته‌بندی و لیبل · `commerce.packaging_label`**

Fit approved information to actual panel space and market review requirements.

Required inputs: approved_specs, label_constraints, market. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `front_back_copy` / متن رو و پشت | Separate front and back panel copy. |
| `required_fields` / فیلدهای لازم | Include supplied mandatory fields and units. |
| `gaps` / کمبودها | Mark missing regulated details for qualified review. |

Review: Regulated review: review the actual Packaging and label copy against supplied evidence. Unit integrity: review the actual Packaging and label copy against supplied evidence. Space constraints: review the actual Packaging and label copy against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.

## Sales Brochure

**بروشور فروش · `commerce.sales_brochure`**

Guide the reader from need to evidenced offer and an actual contact path.

Required inputs: offer, proof, audience, format. Missing facts remain labeled; at most three consequential questions per round.

| Output section | Required result |
|---|---|
| `sections` / بخش‌ها | Order sections around the buyer's decision. |
| `short_copy` / متن کوتاه | Write short copy for the supplied print space. |
| `contact_path` / راه تماس | Preserve the correct contact and offer conditions. |

Review: Trace each objective claim to a supplied source; unsupported claims remain labeled gaps. Reader path: review the actual Sales brochure against supplied evidence. Contact accuracy: review the actual Sales brochure against supplied evidence. Validate output section presence, locked exact spans, supplied evidence ids and per-key placeholders; semantic review remains required.

Status: `implemented_not_verified`; local deterministic checks do not certify semantic quality, external publication, or expert approval.
