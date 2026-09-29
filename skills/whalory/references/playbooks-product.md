# Playbooks: products and stores

This file is part of the [playbooks](playbooks.md). Each task's row is in the [task index](playbooks.md#task-index), and every playbook here assumes the [shared steps](playbooks.md#shared-steps). The "Questions" line of a playbook only names its row in the question bank; the [question gate](intake.md#decision-order) decides whether to ask. The "References" line lists the Persian craft files after "fa:" and the English ones after "en:". Read the list for the output language. The quality assurance (QA) line gives the checks and the `--format` id.

## Contents

- [Products and stores](#products-and-stores)
  - [Product description](#product-description)

## Products and stores

### Product description

1. Take the exact name, place, ingredients or parts, use, and care from the brief, the product sheet, or the photo.
2. The pattern for short copy about one thing: name and origin, a person's scene and reason, parts, and a friendly tip.
3. The opening line starts with something concrete; the ending is a tip.
4. No superlatives and no medical claims; a sensitive claim goes through the claims file ([fa/claims.md](fa/claims.md), [en/claims.md](en/claims.md)).
5. If a product photo came with the request, use only what can be seen; the boundary is in fa/photo-to-story.md#دو-حالت-یک-مرز (in Whalory Pro).
6. For an app page on Cafe Bazaar or Myket, use the fields and limits of that store: Cafe Bazaar and Myket (in Whalory Pro). For the App Store or Google Play: en/marketplaces.md#app-store-listing (in Whalory Pro) and en/marketplaces.md#google-play-listing (in Whalory Pro). An app-store page in either language takes the format id `listing`; its channel ids are `cafebazaar`, `myket`, `app-store`, and `google-play`.

**Questions:** The "Product descriptions and marketplace listings" row of the [question bank](intake.md#question-bank-by-task). No-default slot: the definite specifications.
**References:** fa: [fa/forms.md#متنِ-کوتاهِ-یک-چیز](fa/forms.md#متنِ-کوتاهِ-یک-چیز), fa/product-copy.md#معرفیِ-محصول (in Whalory Pro), fa/hooks.md (in Whalory Pro), fa/anatomy.md (in Whalory Pro), fa/industries.md (in Whalory Pro) · en: [en/forms.md#product-blurb](en/forms.md#product-blurb), en/web-pages.md#product-pages (in Whalory Pro), en/anchors.md#product-description (in Whalory Pro), en/industries.md (in Whalory Pro)
**Output:** Three to six sentences in two or three paragraphs; for a store page, the specifications come separately.
**QA:** The opening sentence starts with something concrete. Substitution test: with a rival product's name in place, the text stops being true. Every claim has evidence. `--format product`; for an app-store page, `--format listing` with `--channel` and that store's id.

