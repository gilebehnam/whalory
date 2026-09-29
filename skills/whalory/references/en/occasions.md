# Occasions calendar

Holidays, remembrance days, and moments of grief change the tone of copy, even when the copy is not about them. This file gives the mode each international occasion puts the text in, and what that mode does to humor, emoji, and sales copy. It also says how to get each date right. Many of these dates move from year to year. Whalory computes or confirms each one for the year of publication and never writes it from memory. Open this file whenever a request names an occasion, the publication date is known, or copy is being scheduled. The Iranian calendar and its occasions are in the [Persian occasions file](../fa/occasions.md).

## Contents

- [Where dates come from](#where-dates-come-from)
- [Occasion modes](#occasion-modes)
- [Holiday season](#holiday-season)
- [New Year](#new-year)
- [Valentine's Day](#valentines-day)
- [Mother's Day: US and UK dates](#mothers-day-us-and-uk-dates)
- [Ramadan and the Eid holidays](#ramadan-and-the-eid-holidays)
- [Lunar New Year dates and names](#lunar-new-year-dates-and-names)
- [Pride](#pride)
- [Black Friday and Cyber Monday sales](#black-friday-and-cyber-monday-sales)
- [Thanksgiving: US and Canadian dates](#thanksgiving-us-and-canadian-dates)
- [Diwali](#diwali)
- [Remembrance days](#remembrance-days)
- [Nowruz for the diaspora](#nowruz-for-the-diaspora)
- [Grief and crisis](#grief-and-crisis)
- [Check the date before publishing](#check-the-date-before-publishing)
- [Checklist](#checklist)

## Where dates come from

Occasion dates follow one of five kinds of rule. Only the first kind is safe to remember.

| Kind of rule | Examples | Source (checked 2026-09-27) |
|---|---|---|
| Fixed date | New Year's Day, January 1; Christmas Day, December 25; US Veterans Day, November 11 | [US Code, title 5, section 6103](https://www.law.cornell.edu/uscode/text/5/6103) |
| Weekday of a month | US Mother's Day, the second Sunday in May; US Thanksgiving, the fourth Thursday in November | [US Code, title 36, section 117](https://www.law.cornell.edu/uscode/text/36/117) and [title 5, section 6103](https://www.law.cornell.edu/uscode/text/5/6103) |
| Tied to Easter | UK Mothering Sunday, 3 weeks before Easter Sunday | [Wikipedia, Mothering Sunday](https://en.wikipedia.org/wiki/Mothering_Sunday), revision 1373440146 |
| Lunar or lunisolar | Ramadan, the Eids, Lunar New Year, Diwali | See each section below |
| Astronomical | Nowruz, at the March equinox | [United Nations, International Day of Nowruz](https://www.un.org/en/observances/international-nowruz-day) |

Public holidays can also move to a substitute day. In England and Wales, the 2026 Boxing Day bank holiday falls on Monday, December 28. Source: [GOV.UK, bank holidays](https://www.gov.uk/bank-holidays), checked 2026-09-27.

Whalory's rules:

1. Never write a moving date from memory. Compute it from its rule, or confirm it in an official calendar for the year of publication.
2. When the calendar for that year is not out yet, or the date depends on a moon sighting, write a bracket: `[confirm: date of Eid al-Fitr in the target country]`.
3. Use the calendar of each market. A brand that sells in the US and the UK has two Mother's Days.
4. Record in the note which date was used, from which source, and when it was checked.

## Occasion modes

The context card has an `occasion` slot with four values ([router.md](../router.md#context-card)). Every occasion in this file takes exactly one of them, and the value changes the tone dials.

| | Festive | Mourning | National | None |
|---|---|---|---|---|
| Value | `festive` | `mourning` | `national` | `none` |
| Tone | Warm; a short greeting and one real detail | Quiet, short, respectful | Informative and neutral | From the profile, plus the section's own rule |
| Humor | From the profile | 1, no exceptions | 1; no jokes about the day itself | From the profile |
| Emoji | From the profile | 0 | 0 | From the profile |
| Exclamation marks | From the profile | 0 | 0 | From the profile |
| Sales copy | Allowed when the link to the occasion is real | Stopped; scheduled posts move | Low-key and separate from the day's name | Per the section |
| Discount named after the day | Allowed, with a real end date | Never | No | Per the section |
| Silence | Rarely needed | Often the right choice | Often the right choice | The brand's choice |

`none` means the profile's dials apply and the occasion only adds its own rule. An ordinary day is `none`.

Precedence: the mourning and national columns override the profile. A brand whose profile sets humor to 4 still writes with humor 1 on a day of mourning. Service messages, such as opening hours and delivery updates, go out in every mode.

## Holiday season

Mode: `festive` for audiences who celebrate; `none` for everyone else.

- Readers on one list may celebrate Christmas, another festival, or none. Match the greeting to the audience you know. "Happy holidays" suits a mixed list; "Merry Christmas" suits customers who celebrate Christmas.
- Christmas Day is December 25 in the US and the UK. Sources: [US Code, title 5, section 6103](https://www.law.cornell.edu/uscode/text/5/6103) and [GOV.UK, bank holidays](https://www.gov.uk/bank-holidays), checked 2026-09-27.
- Delivery cut-off dates come from the carrier, for the current year: `[confirm: last order date for delivery by December 24, from the carrier]`.
- Bank holidays close support desks and delay deliveries. Say which days are affected, per market.

## New Year

Mode: `festive`.

- New Year's Day is January 1. Source: [US Code, title 5, section 6103](https://www.law.cornell.edu/uscode/text/5/6103), checked 2026-09-27.
- Resolution copy works without shame. "New year, new you" framing sells through dissatisfaction; see [ethics.md](ethics.md#fear-and-shame).
- Time zones matter at midnight. A "happy new year" post scheduled in one time zone goes out early or late in another. Write the time with its zone ([style-guide.md](style-guide.md#dates-and-times)).
- Lunar New Year is a different date; see [Lunar New Year dates and names](#lunar-new-year-dates-and-names).

## Valentine's Day

Mode: `festive`.

- Valentine's Day is February 14. Source: [Wikipedia, Valentine's Day](https://en.wikipedia.org/wiki/Valentine%27s_Day), revision 1368166512, checked 2026-09-27.
- Not every reader has a partner. Copy that assumes one excludes the rest of the list. Gifts for friends, family, or yourself widen it.
- Do not assume the gender of anyone's partner.
- Offer an opt-out from Valentine's emails for readers who would rather skip them.

## Mother's Day: US and UK dates

Mode: `festive`.

| Market | Day | Source (checked 2026-09-27) |
|---|---|---|
| US | Mother's Day, the second Sunday in May | [US Code, title 36, section 117](https://www.law.cornell.edu/uscode/text/36/117) |
| UK | Mothering Sunday, the fourth Sunday in Lent, 3 weeks before Easter Sunday; often called Mother's Day | [Wikipedia, Mothering Sunday](https://en.wikipedia.org/wiki/Mothering_Sunday), revision 1373440146 |

- The UK date moves every year with Easter. Compute it for the year of publication.
- A brand that sells in both markets runs two calendars.
- For some readers this day is painful: people who have lost a mother or a child, or who are estranged. Offer an opt-out before the campaign, and keep the tone warm and simple.

## Ramadan and the Eid holidays

Mode: `none` during Ramadan, with the rules below; `festive` for Eid al-Fitr and Eid al-Adha.

- The Islamic calendar is lunar, and each month begins when the new crescent moon is sighted. Ramadan lasts 29 or 30 days, and the Islamic year is 10 to 11 days shorter than the solar year. Source: [Wikipedia, Ramadan](https://en.wikipedia.org/wiki/Ramadan), revision 1368464637, checked 2026-09-27.
- The start and end differ by place. Some communities rely on a local sighting, others on calculation or on the Saudi Arabian announcement. Source: the same page.
- Eid al-Fitr falls on the first day of Shawwal, the month after Ramadan, and begins at sunset on the night the crescent is first sighted. Source: [Wikipedia, Eid al-Fitr](https://en.wikipedia.org/wiki/Eid_al-Fitr), revision 1376906411, checked 2026-09-27.
- Eid al-Adha falls on the 10th of Dhu al-Hijjah, the last month of the Islamic calendar. Source: [Wikipedia, Eid al-Adha](https://en.wikipedia.org/wiki/Eid_al-Adha), revision 1376666142, checked 2026-09-27.

For copy:

- Never hard-code these dates. When the date depends on a sighting, prepare two versions, one for each possible day, or use a bracket.
- Greet the audience you know, in the words that audience uses, such as "Ramadan Mubarak" or "Eid Mubarak."
- Ramadan is not a sales hook on its own. Offers need a real link, such as changed opening hours or evening delivery.

## Lunar New Year dates and names

Mode: `festive`.

- The first day of Chinese New Year falls on the new moon between January 21 and February 20. Source: [Wikipedia, Chinese New Year](https://en.wikipedia.org/wiki/Chinese_New_Year), revision 1375910998, checked 2026-09-27.
- Use the name your audience uses. The same season is Chinese New Year or Spring Festival, Tết Nguyên Đán in Vietnam, and Seollal in Korea. "Lunar New Year" covers them all. Source: [Wikipedia, Lunar New Year](https://en.wikipedia.org/wiki/Lunar_New_Year), revision 1371951542, checked 2026-09-27.
- Traditions differ between cultures. The Vietnamese zodiac has the Buffalo and the Cat where the Chinese zodiac has the Ox and the Rabbit. Source: the same page.
- Compute the date for the year of publication; it changes every year.

## Pride

Mode: `festive` for brands that take part; `none` for the rest.

- In the United States, Pride Month is observed in June, the anniversary month of the 1969 Stonewall riots. Many cities around the world hold their events at other times, and in Canada the Pride season runs from June to September. Source: [Wikipedia, Pride Month](https://en.wikipedia.org/wiki/Pride_Month), revision 1369536499, checked 2026-09-27.
- Confirm the date of each local event rather than assuming June.
- Support in the copy should match what the brand does all year. A rainbow logo with nothing behind it fails the "behind the scenes" test in [ethics.md](ethics.md#three-quick-tests).
- Use the terms the community uses, and check them each year (inclusive.md (in Whalory Pro)).

## Black Friday and Cyber Monday sales

Mode: `none`, with the sales rules below.

- Black Friday is the Friday after Thanksgiving in the United States. Cyber Monday is the Monday after it. Sources: [Wikipedia, Black Friday](https://en.wikipedia.org/wiki/Black_Friday_(shopping)), revision 1375327511, and [Wikipedia, Cyber Monday](https://en.wikipedia.org/wiki/Cyber_Monday), revision 1367728232, checked 2026-09-27.
- Every discount must be real:
  - For US readers, a "was" price must be the real price the product was openly offered at for a reasonably substantial period ([claims.md](claims.md#reference-prices)).
  - In the EU, the "was" price is the lowest price of the previous 30 days ([claims.md](claims.md#the-30-day-prior-price)).
  - In the UK, the headline price includes every mandatory fee ([ethics.md](ethics.md#drip-pricing)).
  - Countdowns and "last chance" lines must be true ([ethics.md](ethics.md#fake-urgency-and-scarcity)).
- For Iranian readers, "Black Friday" is also the name of the shooting of protesters in Tehran's Jaleh Square on September 8, 1978. Source: [Wikipedia, Black Friday (1978)](https://en.wikipedia.org/wiki/Black_Friday_(1978)), revision 1358420060, checked 2026-09-27. For a diaspora audience, a campaign name of the brand's own is safer.

## Thanksgiving: US and Canadian dates

Mode: `festive`.

| Market | Date | Source (checked 2026-09-27) |
|---|---|---|
| US | The fourth Thursday in November | [US Code, title 5, section 6103](https://www.law.cornell.edu/uscode/text/5/6103) |
| Canada | The second Monday in October | [Wikipedia, Thanksgiving (Canada)](https://en.wikipedia.org/wiki/Thanksgiving_(Canada)), revision 1369365176 |

- One brand, two markets, two dates more than a month apart. Schedule each market separately.
- Gratitude copy works best with a real detail: who you thank and for what.

## Diwali

Mode: `festive`.

- Diwali is the Hindu festival of lights, and Jains and Sikhs celebrate their own versions of it. It follows the Hindu lunisolar calendar and falls between about mid-October and mid-November. The celebration lasts five days. Source: [Wikipedia, Diwali](https://en.wikipedia.org/wiki/Diwali), revision 1376690098, checked 2026-09-27.
- Compute or confirm the date for each year; it moves with the new moon.
- Greet the audience you know. "Happy Diwali" is the common English greeting.

## Remembrance days

Mode: `national` or `mourning` for the days in the table. US Veterans Day is different; see the end of this section.

| Day | Market | Date | Source (checked 2026-09-27) |
|---|---|---|---|
| Remembrance Day | Canada | November 11 | [Holidays Act](https://laws-lois.justice.gc.ca/eng/acts/h-5/page-1.html) |
| Remembrance Sunday | UK | The second Sunday in November: November 8 in 2026, November 14 in 2027 | [Wikipedia, Remembrance Sunday](https://en.wikipedia.org/wiki/Remembrance_Sunday), revision 1371463635 |
| Memorial Day | US | The last Monday in May: May 25 in 2026, May 31 in 2027 | [US Code, title 5, section 6103](https://www.law.cornell.edu/uscode/text/5/6103) |
| Anzac Day | Australia, New Zealand | April 25 | [Wikipedia, Anzac Day](https://en.wikipedia.org/wiki/Anzac_Day), revision 1366451858 |

For copy:

- No sales copy about the day, and no discount named after it. If the brand runs a sale that weekend, name it after the season, not the day.
- A brand that marks the day does it briefly and quietly, with no product in the message.
- Scheduled promotional posts for that day move to another day.

US Veterans Day follows a different rule. Its mode is `national`, and it falls on November 11 every year ([US Code, title 5, section 6103](https://www.law.cornell.edu/uscode/text/5/6103), checked 2026-09-27). It is not a day of mourning. The US Department of Veterans Affairs (VA) says Memorial Day remembers those who died in service. Veterans Day thanks all who served. It is mainly meant to thank living veterans ([VA, Veterans Day facts and information](https://department.va.gov/veterans-day/facts-and-information/), checked 2026-09-28). The same page spells the name without an apostrophe: Veterans Day.

- A real offer for veterans only, such as a discount or a free meal with its terms stated, fits the day when it thanks them. It is the one exception to the `national` rule on discounts.
- A sale for everyone that borrows the day's name does not: no `Veterans Day blowout`.
- Poppies belong to Memorial Day in the US, not to Veterans Day (same VA page).

## Nowruz for the diaspora

Mode: `festive`.

- Nowruz, the Persian New Year, begins at the vernal equinox, usually on March 20 or 21. The United Nations (UN) General Assembly proclaimed March 21 the International Day of Nowruz in 2010. People celebrate it across Iran, Central Asia, the Caucasus, the Balkans, and beyond. Source: [United Nations, International Day of Nowruz](https://www.un.org/en/observances/international-nowruz-day), checked 2026-09-27.
- The date changes with the equinox, so confirm it for the year and for the reader's time zone.
- Greetings can come in both languages: "Happy Nowruz" in English and `نوروزتان پیروز` in Persian. The Persian text follows the Persian pack.
- Readers in the diaspora may have roots anywhere Nowruz is kept, from Iran and Central Asia to the Caucasus and the Balkans. Do not assume one country's traditions.
- The Iranian calendar and its occasions: [Persian occasions file](../fa/occasions.md). Converting Solar Hijri dates: transcreation.md (in Whalory Pro).

## Grief and crisis

Mode: `mourning`.

When a tragedy hits the brand's community, its city, or the news its readers follow:

- Pause scheduled posts, and check everything queued for the next few days on every channel.
- Do not use the event to sell, and do not attach the brand to it for attention. If the brand's name could be removed and the message would still help someone, it may go out; otherwise it waits.
- Service messages still go out: opening hours, delivery delays, safety information, and how to reach a person.
- A statement, if the brand makes one, is short, specific, and free of product.
- Silence is often the right choice ([judgment.md](../judgment.md#silence-is-also-a-choice)). Condolences and outage messages follow the hard message playbook (in Whalory Pro).

## Check the date before publishing

- [ ] The publication date and time are known; if not, the note says so.
- [ ] The occasion's date was computed or confirmed for this year, not taken from memory.
- [ ] Neither the publication day nor the evening before it falls in a mourning period.
- [ ] Occasions that depend on a moon sighting have two versions, or a bracket.
- [ ] Someone checked the day's news before publishing: a tragedy, a day of mourning, or anything that makes cheerful copy wrong.
- [ ] Scheduled posts on every channel were reviewed the day before.
- [ ] Each weekday matches its date ([style-guide.md](style-guide.md#dates-and-times)).
- [ ] Public holidays that close support or delay delivery are named in the copy.
- [ ] A brand in several markets checked each market's calendar separately.
- [ ] An occasion line is in the note.

The diagnosis line gains `Occasion: [name]` before its quality assurance (QA) part ([router.md](../router.md#diagnosis-note)). The internal note adds one line:

```
Occasion: [name] · Mode: [festive/mourning/national/none] · Date: [date] · Source: [calendar] · Checked: [date]
```

In an automated run with no known publication date, this goes under `needs_verification`: "Check the publication date against occasions.md".

## Checklist

Linter rule ids: `en-emoji`, `en-bangs`, `en-numeric-date`, `en-superlative`. Occasion rules need a human reading.

- [ ] The occasion has one mode, and the dials follow it.
- [ ] Mourning and national days carry no sales copy and no discount named after the day, except a real offer for veterans on US Veterans Day.
- [ ] Every moving date was computed or confirmed for this year and market.
- [ ] Greetings fit the audience the brand knows, in the names that audience uses.
- [ ] Holiday discounts follow the price rules in [claims.md](claims.md#price-claims).
- [ ] The note records the date, its source, and when it was checked.
