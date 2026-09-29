# Channels

This file covers what the reader sees on each international channel and where the text gets cut off. It gives the limits in the unit each platform counts, and the habits that work there. The numbers are written inline so the skill works without the `data/` folder. Platforms change their limits, so every number carries its source, and all sources were checked on 2026-09-27. A number marked "unverified" came only from secondary sources; treat it as a guide, not a hard cap.

## Contents

- [Limits at a glance](#limits-at-a-glance)
- [How platforms count characters](#how-platforms-count-characters)
- [Instagram](#instagram)
- [LinkedIn](#linkedin)
- [X](#x)
- [Threads](#threads)
- [Bluesky](#bluesky)
- [TikTok](#tiktok)
- [YouTube](#youtube)
- [Pinterest](#pinterest)
- [Reddit](#reddit)
- [Facebook](#facebook)
- [Email](#email)
- [SMS](#sms)
- [Push notifications](#push-notifications)
- [Search snippet](#search-snippet)
- [Checklist](#checklist)

## Limits at a glance

Hard limits block publishing or get cut by the platform. Recommended lengths are what the platform or a trusted guide advises.

| Channel | Field | Limit | Unit | Source (checked 2026-09-27) |
|---|---|---|---|---|
| Instagram | Caption | 2,200 | characters | [Instagram Graph API, media](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media) |
| Instagram | Hashtags per post or reel | 5 | hashtags | [Instagram @creators announcement](https://www.threads.com/@creators/post/DSalXGPCWM4) |
| Instagram | Bio | 150 | characters | [Instagram Help](https://help.instagram.com/728994388226960/) |
| LinkedIn | Post | 3,000 | characters | [LinkedIn Help, posts](https://www.linkedin.com/help/linkedin/answer/a528176) |
| LinkedIn | Article | 125,000 | characters | [LinkedIn Help, articles](https://www.linkedin.com/help/linkedin/answer/a522483) |
| X | Post | 280 | weighted characters | [Counting characters on X](https://docs.x.com/fundamentals/counting-characters) |
| X | Long post (Premium) | 25,000 | characters | [Types of posts, in the X Help Center](https://help.x.com/en/using-x/types-of-posts) |
| X | Bio, display name | 160, 50 | characters | [Profile settings, in the X Help Center](https://help.x.com/en/managing-your-account/how-to-customize-your-profile) |
| Threads | Post or reply | 500 | characters | [Threads API overview](https://developers.facebook.com/docs/threads/overview) |
| Threads | Text attachment | 10,000 | characters | [Meta newsroom, text attachments](https://about.fb.com/news/2025/09/attach-text-threads-posts-share-longer-perspectives/) |
| Bluesky | Post | 300 graphemes and 3,000 bytes | graphemes, UTF-8 bytes | [Bluesky post lexicon](https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/app/bsky/feed/post.json) |
| Bluesky | Display name, description | 64, 256 | graphemes | [Bluesky profile lexicon](https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/app/bsky/actor/profile.json) |
| TikTok | Caption through the API | 2,200 | UTF-16 code units | [TikTok Content Posting API](https://developers.tiktok.com/doc/content-posting-api-reference-direct-post) |
| YouTube | Title | 100 | characters | [YouTube Help, titles](https://support.google.com/youtube/answer/57404) |
| YouTube | Description | 5,000 | characters (bytes in the API) | [YouTube Data API, videos](https://developers.google.com/youtube/v3/docs/videos) |
| YouTube | Tags, hashtags | 500 characters in total; more than 60 hashtags are all ignored | characters, hashtags | [YouTube Help, hashtags](https://support.google.com/youtube/answer/6390658) |
| Pinterest | Pin title | 100 | characters | [Pinterest Help, Pin specs](https://help.pinterest.com/en/article/review-pin-specs) |
| Pinterest | Pin description | 800 | characters | [Pinterest product specs](https://help.pinterest.com/en/business/article/pinterest-product-specs) |
| Reddit | Post title | 300 | characters | [Reddit API, submit](https://www.reddit.com/dev/api/#POST_api_submit) |
| Email | Subject, recommended | 60 characters and 9 words | characters, words | [Mailchimp, subject lines](https://mailchimp.com/help/best-practices-for-email-subject-lines/) |
| Email | Preview text, recommended | under 90 | characters | [Litmus, preview text](https://www.litmus.com/blog/the-ultimate-guide-to-preview-text-support) |
| SMS | One message | 160 (`GSM-7`) or 70 (`UCS-2`) | characters | [Twilio, SMS character limit](https://www.twilio.com/docs/glossary/what-sms-character-limit) |
| Push, Android | Title, text | 30, 40 (design guidance) | characters | [Android notifications](https://developer.android.com/design/ui/mobile/guides/home-screen/notifications) |
| Push, iOS | Whole payload | 4,096 | bytes | [Apple, generating a remote notification](https://developer.apple.com/documentation/usernotifications/generating-a-remote-notification) |
| Shopify | SEO title, meta description | 70, 320 | characters | [Shopify Help, adding keywords](https://help.shopify.com/en/manual/promoting-marketing/seo/adding-keywords) |

With the linter's `--channel` option, `en-channel-length` flags text over a hard limit, `en-channel-visible` flags text past the visible part, and `en-channel-items` flags too many hashtags or tags.

## How platforms count characters

A "character" means different things on different platforms. Count in the platform's own unit, or the copy fails at the last step.

| Unit | Who uses it | What it means for copy |
|---|---|---|
| Code points | Most platforms by default | Each letter, digit, space, or emoji piece counts once |
| UTF-8 bytes | Bluesky's second limit, the YouTube description in the API | Plain English letters are 1 byte; accented letters, other scripts, and emoji take 2 to 4 |
| UTF-16 code units | TikTok's API | Most emoji count 2 |
| Graphemes | Bluesky | What a reader sees as one character counts once, even a family emoji built from several code points |
| Weighted characters | X | Code points up to U+10FF count 1: Latin, Greek, Cyrillic, Hebrew, and Arabic-script letters, so Persian too, plus the zero-width non-joiner (ZWNJ). Chinese, Japanese, and Korean characters and emoji count 2; every link counts 23 |
| Segments | SMS | 160 or 153 per segment in `GSM-7`, 70 or 67 in `UCS-2` |
| Double width | Google Ads and Microsoft Advertising | Wide characters count 2; Microsoft also counts emoji as wide |

Sources, all checked 2026-09-27:

- X gives a weight of 1 to code points in the ranges 0 to 4351, 8192 to 8205, 8208 to 8223, and 8242 to 8247. All others weigh 2, every emoji counts 2, and every URL counts as 23. The first range is U+0000 to U+10FF, which holds the Persian letters (U+0600 to U+06FF). The second is U+2000 to U+200D, which holds the ZWNJ (U+200C). So a Persian post counts 1 per letter. Sources: [Counting characters on X](https://docs.x.com/fundamentals/counting-characters) and the [twitter-text configuration, version 3](https://github.com/twitter/twitter-text/blob/master/config/v3.json), checked 2026-09-28.
- Bluesky caps a post at 300 graphemes and 3,000 bytes. Source: [Bluesky post lexicon](https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/app/bsky/feed/post.json).
- Microsoft treats emoji as double width in search ads. Source: [Microsoft Advertising, responsive search ads](https://learn.microsoft.com/en-us/advertising/campaign-management-service/responsivesearchad?view=bingads-13).
- The SMS segment sizes come from [Twilio, SMS character limit](https://www.twilio.com/docs/glossary/what-sms-character-limit).

Whalory's `scripts/textcount.py` implements these units. The ad networks' limits are in ads.md (in Whalory Pro).

## Instagram

- Caption: up to 2,200 characters. Hashtags: at most 5 per post or reel, a limit Instagram's @creators account announced in December 2025. The Graph API page still lists the older figure of 30, so follow the newer 5. Bio: 150 characters. Sources in [limits at a glance](#limits-at-a-glance).
- A long caption is cut off in the feed behind "more." Put the point in the first line, and put any "Ad" label there too. The US Federal Trade Commission (FTC) says a disclosure must not hide behind "more." Source: [FTC, Disclosures 101 for influencers](https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers), checked 2026-09-27.
- Hashtags go at the end, never inside the sentence.
- A caption has no heading or bold title line (`en-caption-header`). Structure: [forms.md](forms.md#caption).

## LinkedIn

- Post: up to 3,000 characters. Article: up to 125,000 characters. LinkedIn documents no separate limit for an article headline. Sources in [limits at a glance](#limits-at-a-glance).
- The cut-off before "see more" is not documented by LinkedIn. Treat the first two short lines as the whole post for most readers.
- Limits for profile fields, such as the headline and the About section, are enforced in the app but not documented in LinkedIn Help (unverified).
- Write as a person with a point, not as a press release. One idea, one example, one question or next step.

## X

- Post: 280 weighted characters, with every link counted as 23. Premium accounts can write long posts of up to 25,000 characters. Bio: 160 characters; display name: 50. Sources in [limits at a glance](#limits-at-a-glance).
- An emoji counts 2, so a post full of emoji runs out faster than it looks. Chinese, Japanese, and Korean text counts 2 per character too, while Persian and other Arabic-script text counts 1 per letter.
- One post, one point. A thread needs a first post that works alone.

## Threads

- Post or reply: 500 characters. A text attachment of up to 10,000 characters launched on September 4, 2025; it cannot be edited or scheduled after posting. Sources in [limits at a glance](#limits-at-a-glance).
- Keep the post itself readable without the attachment. The attachment holds the detail, not the point.

## Bluesky

- Post: 300 graphemes and 3,000 bytes. A post can carry up to 8 tags of up to 64 graphemes each. Display name: 64 graphemes; description: 256. Sources: the [post lexicon](https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/app/bsky/feed/post.json) and the [profile lexicon](https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/app/bsky/actor/profile.json), checked 2026-09-27.
- Count graphemes, not code points. A flag or a family emoji is one grapheme but several code points.

## TikTok

- Caption: 2,200 UTF-16 code units when posted through the Content Posting API. The limit in the app's own composer is not documented by TikTok (unverified). Source in [limits at a glance](#limits-at-a-glance).
- The video carries the message; the caption adds the detail, the call to action, and any "Ad" label.
- Ad text on TikTok has its own limits: ads.md (in Whalory Pro).

## YouTube

- Title: 100 characters, and titles and descriptions cannot contain `<` or `>`. Description: 5,000 characters; the Data API counts this limit in bytes, so text in other scripts or with emoji runs out sooner. Tags: 500 characters in total. Sources in [limits at a glance](#limits-at-a-glance).
- Hashtags: if a video has more than 60, YouTube ignores all of them. The first 3 show next to the title. Source: [YouTube Help, hashtags](https://support.google.com/youtube/answer/6390658), checked 2026-09-27.
- Shorts can be up to 3 minutes long, with the same 100-character title. Source: [YouTube Help, Shorts](https://support.google.com/youtube/answer/10059070), checked 2026-09-27.
- Scripts, chapters, and descriptions: video-social.md (in Whalory Pro).

## Pinterest

- Pin title: 100 characters, but only about the first 40 may show in feeds (30 in Chinese, Japanese, or Korean (CJK) or Arabic scripts). Source: [Pinterest Help, Pin specs](https://help.pinterest.com/en/article/review-pin-specs), checked 2026-09-27.
- Pin description: 800 characters. Pinterest does not show descriptions in the home or search feeds, so the title and image carry the Pin. Source: [Pinterest product specs](https://help.pinterest.com/en/business/article/pinterest-product-specs), checked 2026-09-27.

## Reddit

- Post title: up to 300 characters. Source: [Reddit API, submit](https://www.reddit.com/dev/api/#POST_api_submit), checked 2026-09-27.
- Each community sets its own rules, and they come first. Read the community's rules before writing, and never post brand copy where the rules ban self-promotion.
- Write as a member of the community, disclose any connection to the brand, and answer the question that was asked.
- Promoted posts have separate limits: ads.md (in Whalory Pro).

## Facebook

- The research for this pack found no Meta documentation of a length limit for an organic post (checked 2026-09-27). Do not quote a number for it.
- Long posts are cut off behind "See more," so the first lines carry the post.
- Ad text on Facebook follows Meta's ad guide: ads.md (in Whalory Pro).

## Email

- Subject: the email standard itself has no practical cap on a subject. The standard, Request for Comments (RFC) 5322, limits each header line to 998 characters and recommends 78. Long headers can be folded. Source: [RFC 5322, section 2.1.1](https://www.rfc-editor.org/rfc/rfc5322.txt), checked 2026-09-27.
- Mailchimp recommends subjects of 60 characters or fewer and 9 words or fewer, with at most 3 punctuation marks and at most 1 emoji. Source: [Mailchimp, subject lines](https://mailchimp.com/help/best-practices-for-email-subject-lines/), checked 2026-09-27.
- Preview text (the preheader): Litmus recommends under 90 characters and notes that email apps show anywhere from none to about 278. Source: [Litmus, preview text](https://www.litmus.com/blog/the-ultimate-guide-to-preview-text-support), checked 2026-09-27.
- A US commercial email must not have a deceptive subject line. Source: [FTC compliance guide for commercial email](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business), checked 2026-09-27.
- Structure, sequences, and consent: email.md (in Whalory Pro). Subject lines in depth: headlines.md (in Whalory Pro).

## SMS

- One message holds 160 characters in the `GSM-7` alphabet, or 153 per segment when a message spans several. One character outside that alphabet switches the whole message to `UCS-2`: 70 characters, or 67 per segment. An emoji or a curly quote is enough. Twilio caps a message at 1,600 characters and recommends 320 or fewer. Source: [Twilio, SMS character limit](https://www.twilio.com/docs/glossary/what-sms-character-limit), checked 2026-09-27.
- Use straight quotes and no emoji in SMS unless the budget allows `UCS-2`.
- In the US, marketing texts name the brand, and the opt-in call to action states the message frequency and `Msg & data rates may apply`. The program supports the `STOP` and `HELP` keywords. Source: [Twilio, A2P 10DLC compliance](https://www.twilio.com/docs/messaging/compliance/a2p-10dlc), checked 2026-09-27.
- Count the longest possible value of every variable, such as a customer's name, before you promise a segment count.
- Templates, consent rules, and one-time passcodes: sms-push.md (in Whalory Pro).

## Push notifications

- Android: Google's design guidance keeps the title to 30 characters and the text to 40. The title always shows on one line, even when the notification expands. Source: [Android notifications](https://developer.android.com/design/ui/mobile/guides/home-screen/notifications), checked 2026-09-27.
- iOS: Apple sets no character limit for the title or body. The limit is the payload, 4,096 bytes. Source: [Apple, generating a remote notification](https://developer.apple.com/documentation/usernotifications/generating-a-remote-notification), checked 2026-09-27.
- Apple's design guidance asks for brief titles and complete sentences, and says not to truncate a message yourself; the system does it when needed. Source: [Apple Human Interface Guidelines, notifications](https://developer.apple.com/design/human-interface-guidelines/notifications), checked 2026-09-27.
- Marketing pushes on iOS need the user's explicit opt-in, asked for in the app (App Review Guideline 4.5.4). The app must also offer a way to opt out. Source: [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/), checked 2026-09-27.
- Write the push so the title alone makes sense. Android's guidance also leaves the app name out of the title.

## Search snippet

What a searcher sees before clicking is the title link and the snippet.

- Google sets no length limit on the `<title>` element or the meta description. Both are truncated in results as needed, usually to fit the device width. Sources: [Google Search Central, title links](https://developers.google.com/search/docs/appearance/title-link) and [Google Search Central, snippets](https://developers.google.com/search/docs/appearance/snippet), checked 2026-09-27.
- Google builds snippets mainly from the page content. It sometimes uses the meta description when that describes the page better. Source: [Google Search Central, snippets](https://developers.google.com/search/docs/appearance/snippet), checked 2026-09-27.
- Shopify allows SEO titles of up to 70 characters and recommends 60 or fewer. It recommends meta descriptions of about 160 characters, and text over 320 may be cut. Source: [Shopify Help, adding keywords](https://help.shopify.com/en/manual/promoting-marketing/seo/adding-keywords), checked 2026-09-27.
- GOV.UK keeps page titles to 65 characters or fewer. Source: [GOV.UK, clear titles](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-titles/), checked 2026-09-27.
- Put the words a searcher uses at the front of the title. Write a unique title and description for every page.

Titles, meta descriptions, and page copy in depth: web-pages.md (in Whalory Pro).

## Checklist

Linter rule ids: `en-channel-length`, `en-channel-visible`, `en-channel-items`, `en-caption-header`, `en-emoji`, `en-link-text`.

- [ ] The copy fits the channel's hard limit in the channel's own unit.
- [ ] The point, and any "Ad" label, sit in the visible part before "more."
- [ ] Hashtags and tags are within the count and sit at the end.
- [ ] SMS text uses `GSM-7` characters unless the budget allows `UCS-2`, and variables were counted at their longest.
- [ ] A push title makes sense on its own.
- [ ] Every number quoted from this file still matches its source when the copy goes out.
