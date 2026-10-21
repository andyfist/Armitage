# Search counts and date ranges

## How to use this list (short version)

- Files: databases/ebay/sale_2026-10-21.json (eBay Australia sold items, last 3 years) and databases/leski/sale_<auction>.json (Leski prices realised, 2013-2026, one file per auction). Every record has the same fields; hammer_aud is the price in Australian dollars.
- To price a lot: filter by category (coins / books / stamps / other) and search the title for the key words (date, denomination, author, title). Always read the whole description, not just the title: categories and search filters are good but not perfect, and a Leski title can leave out extra items that are listed later in the lot text.
- Prices change over time. Gold and silver coins especially: single Leski half sovereigns made $220-440 hammer (median about $270) in 2015 but $620-760 (median about $650) in 2025-26. Use the most recent sales (2024-2026) for anything bought for its metal, and treat older prices as a floor.
- Worked example, "1923 halfpenny, about Fine": eBay single coins 2025-26 mostly AU$700-1,200 (graded examples about $840-1,970, one PCGS AU50 at $3,512); Leski single 1923 halfpennies made AU$340-800 hammer in 2014-2019 (about $410-970 with premium, and older, so lower). So a Fine example is roughly $600-1,000 to a buyer today.
- Leski prices are hammer prices WITHOUT the buyer's premium; multiply by about 1.21 to compare with eBay prices or with what a buyer pays. eBay prices are what the buyer paid for the item (before eBay's Buyer Protection fee on private-seller items).
- Leski coin lots in the mixed "Stamps, Coins..." sales often have very short text (e.g. "1923. F+, carded") because Leski prints the coin type as a section heading. Such lots were filed as coins where the neighbouring lots are coins, but if a date-only lot matters, check the lots around it.
- Thin or missing data (from test searches): Calder's Native Tribes of Tasmania, original Bligh voyages, Bradman-signed books and the Ferguson bibliography have no or only one sale; Boer War medals, exhibition medals, Bonwick, holey dollars and the Adelaide pound have Leski sales only (no eBay). In such cases treat the figures as a rough guide.
- Words used below: "rows returned" = sold listings Terapeak showed for the search; "hit 100 cap" = Terapeak shows at most 100, so only the newest sales are included; "dup" = the same listing also found by another search (stored once); "off-target" = the listing was not the thing searched for.
- eBay descriptions carry warnings where relevant: "this is a HALF sovereign", "this is a 1937 + 1938 pair (two coins)", "lot of more than one note", "title does not say first edition", "facsimile/reproduction print", "price well below the gold value". A few Leski lots whose catalogue text is only a heading are marked "[Leski catalogue text for this lot is only this heading; see the lot page]".

## Part 1: eBay Australia sold listings via Terapeak (searched 2026-10-21)

Settings: eBay Australia, Sold, all conditions, "Last 3 years" (the longest window offered), newest first, up to 100 rows per search (Terapeak shows 2 pages of 50). Searches that returned 100 rows hit that cap, so their sold-date span is only the most recent part of the 3 years. One extra search, "1930 penny (highest prices)", was added on 2026-10-22: words "1930 penny australia", sorted by highest average sold price, first page of 50 rows, because the newest-first "1930 penny" search held no genuine 1930 penny.

Kept = rows saved to databases/ebay/sale_2026-10-21.json. Every dropped row is listed with its reason in ebay_drops.json. Rules, by search type:
- All searches: hidden prices and removed listings dropped; replicas, fillers, copies, novelty and "not gold" items dropped.
- Key-date searches (1930/1925/1946 penny, 1923 halfpenny, 1932 florin, 1915 shilling, 1937-38 crown, 1966 round 50c): only single genuine coins of that date are kept. Sets, albums, multi-coin lots (including sets "missing" or "ex" the key date) and modern commemoratives or bullion pieces are dropped. Exception: in the crown search a 1937 + 1938 pair is kept, because that is how they usually sell; the description says "this is a 1937 + 1938 pair (two coins)".
- Sovereign searches: silver or gold-plated modern issues, $1 "subscription" coins, replicas (Macquarie Mint, "Million Dollar" sets), banknotes called "half sovereign", jewellery (pendants, brooches, pins) and albums are dropped. Modern GOLD sovereigns (Perth Mint proofs) are kept. Half sovereigns that turned up in the full-sovereign search are kept and marked "this is a HALF sovereign" in the description.
- Perth Mint gold coin: gold-plated, gold-tone and gilded silver items, gold bars, bundles and jewellery dropped; genuine modern gold coins (bullion and proof) are the target and are kept.
- Silver coins lot: modern silver bullion and proofs dropped; what remains is pre-decimal silver plus lots of 1966 round 50c pieces (80% silver, decimal).
- Book and map searches: stamps, first-day covers, coins, jewellery, tableware, frames, games, trade cards and comics dropped; first-edition searches also drop titles that say 2nd/later edition. Modern books are NOT dropped: the general book searches include many recent $10-40 books, so look at the title and date before using a price.
- "early Australian photograph album": all 7 rows are copies of one 1976 book, "Gundagai Album", so this search gives no prices for actual photograph albums.
- First-edition searches: "Australiana first edition" only keeps titles that say first edition / 1st (genuine firsts whose eBay title does not say so are dropped as off-target). "Tasmania first edition book", "Antarctic first edition" and "signed first edition Australian" keep any matching book; where the title does not say first edition the description says "title does not say first edition" (188 rows), so do not read those as first-edition prices.
- "Norman Lindsay limited edition": most sales are limited-edition facsimile etchings and modern prints. They are kept (they are what turns up at auction) and marked "facsimile/reproduction print (not an original etching)" when the title or item details show a facsimile, reprint, lithograph, print, numbered edition or COA; books by Lindsay are not marked. Non-print items (e.g. a radiator mascot) are dropped.
- Crown search: 1937 + 1938 pairs selling for under AU$100 are dropped as probable copies (two crowns hold about 52g of silver). Perth Mint gold: coins selling for under 60% of their stated gold weight are kept but marked "price well below the gold value".
- Medal searches: ribbons, ribbon bars, miniatures, stickers, photos, unnamed or "name erased" medals and foreign (e.g. German) medals are dropped, unless the lot is named medals.
- Banknote searches: lots of more than one note are kept but marked "lot of more than one note" (divide by the number of notes before comparing); coins and books are dropped. The $1 star search keeps only single $1 notes.
A listing found by two searches is stored once (counted in "dup").

| Search | Category | Rows returned | Kept | Of which dup | Kept sold-date span | Main drop reasons |
|---|---|---|---|---|---|---|
| 1930 penny | coins | 100 (hit 100 cap) | 0 | 0 | none kept | other date 56, reproduction/modern copy 22, set or replica, not the single key-date coin 17 |
| 1930 penny (highest prices) | coins | 50 | 15 | 0 | 2024-02-12 to 2026-06-26 | other date 19, set or replica, not the single key-date coin 12, off-target 3 |
| 1923 halfpenny | coins | 100 (hit 100 cap) | 31 | 0 | 2025-06-13 to 2026-10-13 | set or replica, not the single key-date coin 46, reproduction/modern copy 21, other date 1 |
| 1925 penny | coins | 100 (hit 100 cap) | 58 | 0 | 2026-09-05 to 2026-10-15 | set or replica, not the single key-date coin 20, reproduction/modern copy 12, off-target 10 |
| 1946 penny | coins | 100 (hit 100 cap) | 54 | 0 | 2026-09-07 to 2026-10-15 | set or replica, not the single key-date coin 23, off-target 12, reproduction/modern copy 11 |
| Australian florin 1932 | coins | 100 (hit 100 cap) | 48 | 0 | 2025-12-03 to 2026-10-14 | reproduction/modern copy 27, set or replica, not the single key-date coin 25 |
| Australian shilling 1915H | coins | 89 | 53 | 0 | 2023-11-01 to 2026-10-07 | reproduction/modern copy 20, set or replica, not the single key-date coin 14, off-target 2 |
| Australian crown 1937 1938 | coins | 59 | 50 | 0 | 2023-11-15 to 2026-10-06 | set or replica, not the single key-date coin 6, price far below silver value (two crowns hold about 52g of silver): probably copies 1, other date 1 |
| Australian sovereign | coins | 100 (hit 100 cap) | 41 | 0 | 2026-03-17 to 2026-10-11 | off-target 25, reproduction/modern copy 19, not shown to be Australian 15 |
| Australian half sovereign | coins | 100 (hit 100 cap) | 62 | 10 | 2024-03-25 to 2026-10-11 | off-target 27, not shown to be Australian 6, reproduction/modern copy 5 |
| Sydney Mint sovereign | coins | 100 (hit 100 cap) | 73 | 5 | 2026-03-01 to 2026-10-11 | reproduction/modern copy 25, off-target 2 |
| pre-decimal coin collection | coins | 100 (hit 100 cap) | 80 | 1 | 2026-09-01 to 2026-10-15 | off-target 11, reproduction/modern copy 7, empty album or accessory 2 |
| Australian coin album | coins | 100 (hit 100 cap) | 12 | 1 | 2026-09-26 to 2026-10-14 | empty album or accessory 80, reproduction/modern copy 8 |
| silver coins lot Australian | coins | 100 (hit 100 cap) | 88 | 1 | 2026-09-06 to 2026-10-15 | off-target 7, modern bullion, not pre-decimal silver 5 |
| Australian banknote ten shilling | coins | 100 (hit 100 cap) | 98 | 0 | 2026-03-10 to 2026-10-15 | coin or book, not a banknote 2 |
| Australian one pound note | coins | 100 (hit 100 cap) | 97 | 0 | 2025-05-23 to 2026-10-15 | off-target 3 |
| Australian five pound note | coins | 62 | 56 | 4 | 2023-12-04 to 2026-08-18 | off-target 3, coin or book, not a banknote 3 |
| Australian $1 note star | coins | 7 | 2 | 0 | 2025-03-13 to 2025-04-20 | off-target 4, reproduction/modern copy 1 |
| Australian error note | coins | 34 | 31 | 0 | 2023-12-11 to 2026-09-25 | off-target 2, coin or book, not a banknote 1 |
| Australian first prefix note | coins | 100 (hit 100 cap) | 97 | 0 | 2026-05-29 to 2026-10-15 | off-target 3 |
| Australian proof set | coins | 100 (hit 100 cap) | 91 | 0 | 2026-10-06 to 2026-10-18 | off-target 8, reproduction/modern copy 1 |
| 1966 round 50 cent | coins | 100 (hit 100 cap) | 77 | 0 | 2026-10-08 to 2026-10-15 | set or replica, not the single key-date coin 19, reproduction/modern copy 2, off-target 1 |
| Perth Mint gold coin | coins | 100 (hit 100 cap) | 73 | 1 | 2026-08-01 to 2026-10-15 | off-target 26, reproduction/modern copy 1 |
| war medal Australian named | coins | 100 (hit 100 cap) | 85 | 0 | 2025-06-12 to 2026-10-14 | off-target 7, ribbons, miniatures, unnamed or foreign medals, or accessories 6, reproduction/modern copy 2 |
| WW1 trio | coins | 100 (hit 100 cap) | 51 | 0 | 2025-10-05 to 2026-09-24 | ribbons, miniatures, unnamed or foreign medals, or accessories 30, reproduction/modern copy 19 |
| Tasmania token | coins | 100 (hit 100 cap) | 87 | 0 | 2025-11-15 to 2026-10-12 | off-target 12, reproduction/modern copy 1 |
| Tasmanian trade token | coins | 2 | 2 | 0 | 2025-03-22 to 2026-08-29 | - |
| Louisa Anne Meredith | books | 19 | 16 | 0 | 2024-01-06 to 2026-05-11 | reproduction/modern copy 2, off-target 1 |
| Tasmania first edition book | books | 100 (hit 100 cap) | 96 | 0 | 2024-09-01 to 2026-10-13 | later edition, not a first edition 3, off-target 1 |
| Van Diemen's Land book | books | 94 | 89 | 0 | 2023-10-27 to 2026-10-12 | reproduction/modern copy 4, off-target 1 |
| Australiana first edition | books | 100 (hit 100 cap) | 30 | 0 | 2023-12-31 to 2026-08-09 | off-target 58, not a book, map or print 12 |
| Gould birds Australia | books | 100 (hit 100 cap) | 12 | 0 | 2026-04-01 to 2026-09-24 | not John Gould / not a book 73, not a book, map or print 9, reproduction/modern copy 6 |
| Australian exploration journal | books | 49 | 30 | 0 | 2023-11-19 to 2026-06-08 | not a book, map or print 15, reproduction/modern copy 4 |
| Antarctic first edition | books | 47 | 46 | 2 | 2023-12-14 to 2026-10-09 | not a book, map or print 1 |
| Mawson Home of the Blizzard | books | 48 | 48 | 0 | 2023-11-30 to 2026-09-12 | - |
| Captain Cook voyages | books | 100 (hit 100 cap) | 50 | 0 | 2025-12-26 to 2026-10-13 | not a book, map or print 47, off-target 2, reproduction/modern copy 1 |
| signed first edition Australian | books | 100 (hit 100 cap) | 97 | 0 | 2026-08-05 to 2026-10-16 | not a book, map or print 3 |
| Norman Lindsay limited edition | books | 100 (hit 100 cap) | 99 | 0 | 2025-08-08 to 2026-10-02 | reproduction/modern copy 1 |
| Ferguson bibliography | books | 2 | 1 | 0 | 2025-08-18 to 2025-08-18 | reproduction/modern copy 1 |
| antique map Australia | books | 100 (hit 100 cap) | 47 | 1 | 2025-09-25 to 2026-08-30 | reproduction/modern copy 24, not a book, map or print 23, map not of Australia 6 |
| Tasmania antique map | books | 49 | 12 | 2 | 2023-11-15 to 2026-06-20 | not a book, map or print 34, reproduction/modern copy 3 |
| early Australian photograph album | books | 7 | 7 | 0 | 2024-04-05 to 2026-09-25 | - |

eBay total: 42 searches, 3,318 rows returned, 2,164 records saved (unique items). Sold dates span 2023-10-27 to 2026-10-18.

Notes: hammer_aud is Terapeak's average sold price per item, i.e. the winning bid or Buy It Now price the buyer paid (premium_included true; eBay has no separate buyer's premium; postage shown separately in the description). Where one listing sold several units the description says so and the date is the last sale. eBay Australia adds a Buyer Protection fee for the buyer on items from private sellers; Terapeak prices leave it out (on the item pages spot-checked it added about 5-8%). Fixed-price items may also have sold below the asking price by accepted offer; the Terapeak figure is the actual sale price. Condition is not shown in the Terapeak table, so it is only known when the title says it.

1930 penny: the newest-first search kept none (its 100 newest rows were other dates, sets lacking 1930, fillers and silver/gold-plated replicas). The price-sorted extra search kept 15 single 1930 pennies from 2024-2026: AU$23,262 (graded VF35, 103 bids) and AU$10,853 (estate find, 40 bids) at the top, then AU$2,794, AU$1,240 ("not authenticated, found with a lot of old coins", 87 bids), and eleven at AU$437-678. Most of the cheaper ones are uncertified and 1930 pennies are often faked or altered, so treat those as "sold as described, authenticity unknown".

## Part 2: Leski prices realised (auctions.leski.com.au)

Comparing the two sources: eBay prices are what the buyer paid. Leski hammer prices exclude Leski's buyer's premium, currently 19.5% plus GST (about 21.45% in total for Australian buyers, per leski.com.au/information-for-buyers, checked 2026-10-22; older sales may have had a different rate). To compare a Leski hammer price with eBay, multiply it by about 1.21.

Leski's online archive (auctions.leski.com.au/auctions, 207 auctions from Feb 2013 to Oct 2026, listing saved as leski_archive.tsv) was checked auction by auction. Included: every auction whose name contains coin(s), banknote(s), book(s), Australiana or historical (56 auctions), plus 11 whose names do not use those words but whose catalogues are the same kind of material: the four "Australian & Colonial" sales (494, 500, 509, 516), the "Australian History" / "Australian & Colonial History" sales (188, 221, 225, 278), "An Eclectic Library and a History of Photography" (306, books), the Dr Henry Nowik collection of maps & prints (360) and the John Lancaster collection of Australian trade exhibitions (60: exhibition medals, catalogues, tickets and covers). Not included: the upcoming sale 656 (no prices yet), 249 (Trevor Hiscock "Australian Colonies", which is colonial postage stamps; its first catalogue page was checked), and every other sale whose name does not match the rule. Those are listed one by one in the table at the end of this file. Note that some of them may still hold coins or books: the ten "Quarterly Collectors Auction Series" sales (2013-2016) and the named estate/collection sales are general collectables sales. One file per auction: databases/leski/sale_<id>.json. Only lots with a realised price are recorded; passed-in lots have no price and are not recorded. Hammer prices exclude buyer's premium (premium_included false). Catalogue pages were read 10+ seconds apart as Leski asks. "Lots in catalogue" is the count Leski shows in the archive and every catalogue was read to its last lot. Auction dates and names are taken from the archive list (for multi-day sales this is the date the archive shows). The url field is Leski's prices-realised link for the sale, which downloads a PDF; the readable catalogue for the same sale is https://auctions.leski.com.au/auctions/catalog/id/<sale>. Leski's catalogue list shows at most 500 characters of each lot description; where a description was cut there it ends with "…" (653 records), and in some older sales Leski itself ends the cut text with "..." (206 records); the full text is on the lot's own page. A few estimates that were not money amounts (e.g. "Estimate adjusted") are shown as "n/a".

| Auction | Date | Name | Lots in catalogue | Sold lots recorded | coins / books / stamps / other | Total hammer AUD |
|---|---|---|---|---|---|---|
| 650 | 2026-05-30 | Australian & Historical | 1546 | 1374 | 49 / 336 / 30 / 959 | 1,127,290 |
| 653 | 2026-04-28 | Coins & Banknotes, Postcards, Stamps and Postal History | 1159 | 974 | 505 / 9 / 455 / 5 | 583,590 |
| 640 | 2025-11-29 | Australian & Historical | 1589 | 1428 | 22 / 252 / 12 / 1142 | 1,343,070 |
| 644 | 2025-11-12 | Coins & Banknotes, Postcards, Stamps and Postal History | 1169 | 944 | 533 / 11 / 398 / 2 | 594,370 |
| 634 | 2025-06-17 | Coins and Stamps | 871 | 723 | 364 / 5 / 351 / 3 | 810,880 |
| 637 | 2025-05-24 | Australian & Historical | 1569 | 1376 | 27 / 389 / 9 / 951 | 1,284,140 |
| 623 | 2024-12-07 | Australian & Historical | 1552 | 1259 | 11 / 293 / 12 / 943 | 1,354,050 |
| 633 | 2024-10-20 | The Dr Jane Lennon Collection / Australian & Historical | 581 | 520 | 9 / 129 / 5 / 377 | 488,180 |
| 628 | 2024-09-17 | Stamps, Coins & Postcards | 954 | 586 | 105 / 3 / 472 / 6 | 244,580 |
| 620 | 2024-06-30 | The Holey Dollars and Dumps of New South Wales / Coins & Banknotes of Australia and the World | 479 | 421 | 419 / 0 / 1 / 1 | 1,104,020 |
| 613 | 2024-05-25 | Australian & Historical | 1486 | 1369 | 41 / 414 / 2 / 912 | 1,083,010 |
| 600 | 2023-12-18 | Coins, Banknotes & Stamps | 1188 | 827 | 383 / 6 / 431 / 7 | 510,325 |
| 604 | 2023-11-18 | Australian & Historical | 1498 | 1313 | 64 / 199 / 2 / 1048 | 929,870 |
| 607 | 2023-05-29 | Australian & Historical / Rare & Fine Wine | 219 | 212 | 0 / 0 / 0 / 212 | 84,350 |
| 597 | 2023-05-27 | Australian & Historical | 1383 | 1188 | 26 / 275 / 14 / 873 | 895,300 |
| 584 | 2023-02-20 | Coins, Banknotes & Stamps | 919 | 702 | 411 / 2 / 284 / 5 | 542,610 |
| 586 | 2022-12-04 | Australian & Historical | 1271 | 1082 | 29 / 234 / 4 / 815 | 752,920 |
| 573 | 2022-06-25 | Australian & Historical | 1502 | 1351 | 4 / 299 / 14 / 1034 | 969,000 |
| 575 | 2022-05-10 | Stamps, Coins & Postal History | 802 | 564 | 121 / 13 / 429 / 1 | 293,060 |
| 566 | 2021-12-09 | Stamps, Coins & Postal History | 761 | 497 | 171 / 1 / 323 / 2 | 228,440 |
| 562 | 2021-11-27 | Australian & Historical | 1337 | 1132 | 10 / 231 / 26 / 865 | 789,600 |
| 556 | 2021-06-27 | Stamps, Coins & Postal History | 751 | 483 | 105 / 0 / 377 / 1 | 272,340 |
| 551 | 2021-05-29 | Australian & Historical | 1315 | 1183 | 15 / 243 / 9 / 916 | 1,168,145 |
| 542 | 2021-02-07 | Stamps, Coins & Postal History | 604 | 384 | 56 / 0 / 327 / 1 | 413,480 |
| 539 | 2021-01-22 | Timed Online - Day 1 - Coins, Banknotes & Australian Stamps | 615 | 133 | 6 / 2 / 125 / 0 | 12,791 |
| 530 | 2020-11-28 | Australian & Historical | 1214 | 1035 | 12 / 213 / 14 / 796 | 819,145 |
| 525 | 2020-08-22 | Stamps, Coins & Postal History | 984 | 609 | 52 / 4 / 546 / 7 | 383,520 |
| 524 | 2020-06-13 | Australian & Historical | 940 | 783 | 7 / 217 / 13 / 546 | 616,480 |
| 520 | 2019-12-11 | Stamps, Coins & Postal History | 490 | 231 | 8 / 7 / 211 / 5 | 72,385 |
| 516 | 2019-11-24 | Australian & Colonial | 669 | 511 | 5 / 184 / 1 / 321 | 453,765 |
| 511 | 2019-08-28 | Stamps, Coins & Postal History | 784 | 541 | 89 / 12 / 440 / 0 | 224,610 |
| 509 | 2019-05-26 | Australian & Colonial | 750 | 568 | 3 / 121 / 4 / 440 | 450,805 |
| 496 | 2018-12-16 | Stamps, Coins & Banknotes | 500 | 247 | 74 / 0 / 171 / 2 | 210,495 |
| 500 | 2018-12-02 | Australian & Colonial | 516 | 356 | 5 / 69 / 1 / 281 | 278,110 |
| 494 | 2018-07-15 | Australian & Colonial | 721 | 552 | 22 / 168 / 2 / 360 | 451,980 |
| 360 | 2017-06-07 | Dr Henry Nowik AO OBE Collection of Maps & Prints Online | 33 | 22 | 0 / 22 / 0 / 0 | 10,760 |
| 221 | 2017-05-30 | Australian History | 706 | 487 | 2 / 114 / 7 / 364 | 552,180 |
| 277 | 2017-05-23 | Coins, Medals & Banknotes | 463 | 414 | 410 / 3 / 0 / 1 | 260,685 |
| 278 | 2017-04-27 | Australian History Online | 65 | 36 | 0 / 10 / 2 / 24 | 5,585 |
| 306 | 2017-03-21 | An Eclectic Library and a History of Photography | 131 | 56 | 0 / 56 / 0 / 0 | 4,165 |
| 184 | 2016-11-28 | Coins, Medals & Banknotes | 296 | 264 | 251 / 12 / 0 / 1 | 243,130 |
| 60 | 2016-10-18 | The John Lancaster Collection of Australian Trade Exhibitions | 574 | 356 | 48 / 126 / 179 / 3 | 143,710 |
| 225 | 2016-10-17 | Australian History featuring the David & Leslie Frost Collection of Australian and Colonial Antiques | 914 | 718 | 16 / 91 / 2 / 609 | 747,715 |
| 188 | 2016-06-28 | Australian & Colonial History | 663 | 523 | 4 / 123 / 8 / 388 | 568,520 |
| 204 | 2016-03-03 | Coins & Banknotes | 332 | 252 | 249 / 2 / 0 / 1 | 261,177 |
| 159 | 2015-11-09 | Australian & Colonial – Antique & Historical | 590 | 415 | 1 / 174 / 1 / 239 | 405,730 |
| 154 | 2015-09-29 | Coins, Banknotes, Stamps & Postal History | 943 | 731 | 226 / 4 / 492 / 9 | 645,458 |
| 145 | 2015-06-19 | Stamps, Coins & Postal History | 797 | 573 | 40 / 1 / 532 / 0 | 816,980 |
| 128 | 2015-05-19 | Australian & Colonial – Antique & Historical | 539 | 417 | 14 / 151 / 12 / 240 | 394,390 |
| 121 | 2015-03-05 | Stamps, Coins and Postal History | 1015 | 865 | 82 / 12 / 771 / 0 | 771,590 |
| 111 | 2014-12-09 | Stamps, Coins and Postal History | 341 | 254 | 96 / 1 / 157 / 0 | 141,955 |
| 109 | 2014-11-06 | Australian & Colonial – Antique & Historical | 476 | 312 | 9 / 74 / 6 / 223 | 698,275 |
| 88 | 2014-06-25 | Stamps, Coins and Postal History | 332 | 229 | 42 / 4 / 182 / 1 | 107,865 |
| 48 | 2014-06-03 | Australian & Colonial – Antique & Historical | 395 | 285 | 9 / 52 / 18 / 206 | 496,335 |
| 79 | 2014-04-30 | Stamps, Coins and Postal History | 341 | 228 | 48 / 6 / 173 / 1 | 100,755 |
| 47 | 2014-02-18 | Stamps, Coins and Postal History | 519 | 335 | 52 / 1 / 282 / 0 | 184,260 |
| 21 | 2013-12-10 | Stamps, Coins and Postal History | 438 | 260 | 79 / 1 / 179 / 1 | 164,137 |
| 70 | 2013-09-18 | Sporting & Historical Memorabilia | 1000 | 741 | 11 / 395 / 27 / 308 | 229,606 |
| 73 | 2013-09-11 | Stamps, Coins and Postal History | 657 | 404 | 38 / 5 / 352 / 9 | 152,935 |
| 72 | 2013-08-14 | Sporting and Historical Memorabilia | 848 | 626 | 9 / 379 / 23 / 215 | 243,913 |
| 75 | 2013-06-27 | Stamps, Coins and Postal History | 695 | 424 | 107 / 2 / 314 / 1 | 153,910 |
| 74 | 2013-06-25 | Sporting and Historical Memorabilia | 1167 | 688 | 10 / 436 / 19 / 223 | 200,024 |
| 107 | 2013-05-22 | Sporting, Military and Historical Memorabilia | 667 | 436 | 14 / 281 / 2 / 139 | 187,365 |
| 69 | 2013-03-28 | Supplementary Lots: Gold Coins and Ingots | 72 | 72 | 71 / 0 / 0 / 1 | 41,795 |
| 108 | 2013-03-28 | Stamps, Coins and Postal History | 358 | 243 | 28 / 2 / 210 / 3 | 151,019 |
| 114 | 2013-02-28 | Stamps, Coins and Postal History | 596 | 372 | 29 / 1 / 335 / 7 | 135,630 |
| 113 | 2013-02-14 | Sporting & Historical Memorabilia | 615 | 404 | 12 / 263 / 5 / 124 | 342,902 |

Leski total: 67 auctions, 39,900 sold lots recorded, auction dates 2013-02-14 to 2026-05-30.

category is a keyword classification of each lot: coins = coins, banknotes, tokens, medals and medallions, bullion; books = books, maps, prints and engravings, documents, letters, photographs, posters and paper ephemera; stamps = stamps, covers, postal history, postal stationery and postcards; other = everything else (pottery, furniture, paintings, silver, wine, etc.). It is a guide for filtering, not a cataloguer's judgement. How it was set: keyword rules first (using the sale type as a hint: coin sales lean to coins, mixed coin-and-stamp sales lean to stamps); then every lot where the rules were not clear-cut (20,872 of the 39,900, listed in leski_ai_categories.tsv) was read and labelled one by one by an AI reader; that label is stored unless one of the consistency rules below or a hand correction changed it. Philatelic-numismatic covers (PNCs) count as coins; jewellery with a coin or nugget, badges and original artworks count as other. In two independent checks of Leski records drawn at random from all 39,900, 319 of 320 and 330 of 330 had the right category (about 98% if borderline cases such as trade cards or a fob are counted as wrong); 154 lots found wrong by reviewers' targeted sweeps were then corrected by hand (leski_manual_categories.tsv), and in mixed coin-and-stamp sales a lot with no stamp words inside a run of coin lots is filed as coins. Remaining errors are concentrated in short coin lots of the mixed sales (see the note at the top).

Reading the Leski records: description = Leski's lot text, then " | Estimate <low - high> | Leski <sale name>" added on the end (kept inside description because the record shape has no estimate field). In coin sales Leski groups lots under section headings (e.g. SOVEREIGNS) that are not part of the lot text, so a short title like "1908P, KEVII" means a coin of that heading; check neighbouring lots or the catalogue if the denomination matters.

## Appendix: Leski auctions not included

Every other auction in Leski's archive list, with the reason it was left out.

| Auction | Date | Name | Lots | Reason |
|---|---|---|---|---|
| 656 | 2026-10-27 | The Spencer Sandilands Collection | 610 | upcoming, no prices yet |
| 661 | 2026-10-06 | Sporting Memorabilia | 647 | name does not mention coins, banknotes, books, Australiana or historical |
| 665 | 2026-08-29 | Decorative Arts & Collectables / including the Hellwege Photographica Collection | 1578 | name does not mention coins, banknotes, books, Australiana or historical |
| 659 | 2026-06-27 | Decorative Arts & Collectables | 1361 | name does not mention coins, banknotes, books, Australiana or historical |
| 654 | 2026-05-13 | Apothecary, Advertising, Radios & Other Collectables | 507 | name does not mention coins, banknotes, books, Australiana or historical |
| 649 | 2026-03-30 | Sporting Memorabilia | 709 | name does not mention coins, banknotes, books, Australiana or historical |
| 648 | 2026-03-14 | Decorative Arts & Collectables | 1617 | name does not mention coins, banknotes, books, Australiana or historical |
| 657 | 2026-02-25 | Mid-Century Masterpieces / the Art of Murano Glass and Decorative Arts | 245 | name does not mention coins, banknotes, books, Australiana or historical |
| 643 | 2025-10-11 | Decorative Arts & Collectables | 1596 | name does not mention coins, banknotes, books, Australiana or historical |
| 639 | 2025-09-18 | Sporting Memorabilia | 799 | name does not mention coins, banknotes, books, Australiana or historical |
| 642 | 2025-09-03 | Australian & International / Affordable Art, Objects and Cameras | 465 | name does not mention coins, banknotes, books, Australiana or historical |
| 585 | 2025-08-12 | The Gary & Genevieve Morgan Collection / Part Two | 236 | name does not mention coins, banknotes, books, Australiana or historical |
| 638 | 2025-06-28 | Decorative Arts & Collectables | 1414 | name does not mention coins, banknotes, books, Australiana or historical |
| 631 | 2025-03-29 | Decorative Arts, Collectables & Cameras | 1560 | name does not mention coins, banknotes, books, Australiana or historical |
| 611 | 2025-03-18 | Australian & International / Decorative Arts, Paintings & Collectables | 650 | name does not mention coins, banknotes, books, Australiana or historical |
| 626 | 2025-02-12 | Sporting Memorabilia | 1065 | name does not mention coins, banknotes, books, Australiana or historical |
| 627 | 2024-11-16 | Decorative Arts & Collectables | 1360 | name does not mention coins, banknotes, books, Australiana or historical |
| 625 | 2024-10-29 | Eve Glenn Poster Collection, the Beatles, Cameras & Photographic Equipment. | 1079 | name does not mention coins, banknotes, books, Australiana or historical |
| 630 | 2024-09-22 | The Pratten, Landis and Burghley Collections / Decorative Arts | 570 | name does not mention coins, banknotes, books, Australiana or historical |
| 609 | 2024-08-11 | An Eye for Beauty / Private Collection of International Decorative Arts - Part II | 810 | name does not mention coins, banknotes, books, Australiana or historical |
| 622 | 2024-06-22 | Decorative Arts & Collectables | 1620 | name does not mention coins, banknotes, books, Australiana or historical |
| 616 | 2024-05-01 | Sporting Memorabilia | 602 | name does not mention coins, banknotes, books, Australiana or historical |
| 615 | 2024-03-26 | The Michael Family Camera Museum / Part Three | 651 | name does not mention coins, banknotes, books, Australiana or historical |
| 617 | 2024-03-24 | The Michael and Valerie Gregg Collection | 795 | name does not mention coins, banknotes, books, Australiana or historical |
| 610 | 2024-02-10 | Decorative Arts & Collectables | 1629 | name does not mention coins, banknotes, books, Australiana or historical |
| 614 | 2023-12-12 | The Michael Family Camera Museum / Part Two | 652 | name does not mention coins, banknotes, books, Australiana or historical |
| 612 | 2023-11-20 | The Estate of Martin Sachs - Part III | 76 | name does not mention coins, banknotes, books, Australiana or historical |
| 608 | 2023-10-04 | Fine & Antique Clocks | 188 | name does not mention coins, banknotes, books, Australiana or historical |
| 594 | 2023-09-22 | Sporting Memorabilia | 1046 | name does not mention coins, banknotes, books, Australiana or historical |
| 602 | 2023-08-26 | Decorative Arts & Collectables | 1416 | name does not mention coins, banknotes, books, Australiana or historical |
| 590 | 2023-07-22 | An Eye for Beauty / Private Collection of International Decorative Arts | 892 | name does not mention coins, banknotes, books, Australiana or historical |
| 595 | 2023-06-22 | Antique and Vintage Tools | 120 | name does not mention coins, banknotes, books, Australiana or historical |
| 606 | 2023-04-30 | Beauty & Grace / an Art Deco Collection | 317 | name does not mention coins, banknotes, books, Australiana or historical |
| 603 | 2023-03-30 | The Estate of Martin Sachs - Part II | 313 | name does not mention coins, banknotes, books, Australiana or historical |
| 596 | 2023-03-18 | Decorative Arts & Collectables | 1531 | name does not mention coins, banknotes, books, Australiana or historical |
| 587 | 2022-11-05 | Decorative Arts & Collectables | 1322 | name does not mention coins, banknotes, books, Australiana or historical |
| 579 | 2022-09-11 | Decorative Arts & Collectables | 1581 | name does not mention coins, banknotes, books, Australiana or historical |
| 569 | 2022-08-26 | Sporting Memorabilia | 870 | name does not mention coins, banknotes, books, Australiana or historical |
| 580 | 2022-08-09 | The Michael Family Camera Museum / Part One | 316 | name does not mention coins, banknotes, books, Australiana or historical |
| 583 | 2022-05-29 | The Estate of Brian Myddleton Davis AM | 187 | name does not mention coins, banknotes, books, Australiana or historical |
| 571 | 2022-03-28 | The Maruska Aughterson Collection | 304 | name does not mention coins, banknotes, books, Australiana or historical |
| 570 | 2022-03-27 | Decorative Arts & Collectables | 1553 | name does not mention coins, banknotes, books, Australiana or historical |
| 574 | 2022-03-08 | The Estate of Martin Sachs | 349 | name does not mention coins, banknotes, books, Australiana or historical |
| 563 | 2021-12-07 | The Gary & Genevieve Morgan Collection - Part One | 220 | name does not mention coins, banknotes, books, Australiana or historical |
| 567 | 2021-11-06 | Decorative Arts & Collectables | 1561 | name does not mention coins, banknotes, books, Australiana or historical |
| 552 | 2021-09-20 | Sporting Memorabilia | 846 | name does not mention coins, banknotes, books, Australiana or historical |
| 568 | 2021-09-05 | Dendron House, Mount Eliza / the Foster Collection | 211 | name does not mention coins, banknotes, books, Australiana or historical |
| 554 | 2021-08-14 | Decorative Arts & Collectables | 1467 | name does not mention coins, banknotes, books, Australiana or historical |
| 550 | 2021-05-09 | The Joseph Greenberg Collection | 703 | name does not mention coins, banknotes, books, Australiana or historical |
| 543 | 2021-02-27 | Decorative Arts & Collectables | 1305 | name does not mention coins, banknotes, books, Australiana or historical |
| 555 | 2021-01-22 | Timed Online - Day 2 - World Philately | 287 | name does not mention coins, banknotes, books, Australiana or historical |
| 541 | 2020-11-12 | Sporting Memorabilia | 659 | name does not mention coins, banknotes, books, Australiana or historical |
| 535 | 2020-10-31 | Decorative Arts & Collectables | 1081 | name does not mention coins, banknotes, books, Australiana or historical |
| 529 | 2020-09-26 | The Geoffrey Burke Collection / Mid Century Masterpieces | 880 | name does not mention coins, banknotes, books, Australiana or historical |
| 528 | 2020-06-28 | Decorative Arts & Collectables | 911 | name does not mention coins, banknotes, books, Australiana or historical |
| 521 | 2020-05-10 | Sporting Memorabilia | 716 | name does not mention coins, banknotes, books, Australiana or historical |
| 533 | 2020-04-22 | Toys Online | 141 | name does not mention coins, banknotes, books, Australiana or historical |
| 534 | 2020-04-21 | Stamps & Postal History Online | 523 | name does not mention coins, banknotes, books, Australiana or historical |
| 526 | 2020-03-22 | A Treasure Chest of Toys, Trains and Models | 362 | name does not mention coins, banknotes, books, Australiana or historical |
| 523 | 2020-02-22 | Decorative Arts & Collectables | 1008 | name does not mention coins, banknotes, books, Australiana or historical |
| 527 | 2019-12-05 | The 2019 Melbourne Cup Carnival Online Auction | 69 | name does not mention coins, banknotes, books, Australiana or historical |
| 515 | 2019-12-11 | Aviation / the Centenary of the Ross & Keith Smith Flight and the 50th Anniversary of the Moon Landing | 261 | name does not mention coins, banknotes, books, Australiana or historical |
| 517 | 2019-10-20 | Decorative Arts & Collectables | 889 | name does not mention coins, banknotes, books, Australiana or historical |
| 519 | 2019-09-15 | Fine and Rare Clocks / the Tudor House Clock Museum, Yarrawonga | 371 | name does not mention coins, banknotes, books, Australiana or historical |
| 513 | 2019-08-11 | Sporting Memorabilia | 501 | name does not mention coins, banknotes, books, Australiana or historical |
| 514 | 2019-06-23 | Decorative Arts & Collectables | 592 | name does not mention coins, banknotes, books, Australiana or historical |
| 512 | 2019-05-05 | The Art of Constant Rearrangement / the Joshua McClelland Print Room & Rathdowne Galleries | 477 | name does not mention coins, banknotes, books, Australiana or historical |
| 508 | 2019-03-03 | Decorative Arts & Collectables | 710 | name does not mention coins, banknotes, books, Australiana or historical |
| 502 | 2019-02-24 | Sporting Memorabilia | 376 | name does not mention coins, banknotes, books, Australiana or historical |
| 510 | 2018-12-13 | Model Cars & Toys | 228 | name does not mention coins, banknotes, books, Australiana or historical |
| 495 | 2018-10-28 | Decorative Arts, Watches & Collectables | 628 | name does not mention coins, banknotes, books, Australiana or historical |
| 506 | 2018-09-23 | The Blythman Collection | 233 | name does not mention coins, banknotes, books, Australiana or historical |
| 499 | 2018-09-02 | A Celebration of Cricket | 292 | name does not mention coins, banknotes, books, Australiana or historical |
| 479 | 2018-06-29 | The Ralph Drexel Collection: Part 8 | 216 | name does not mention coins, banknotes, books, Australiana or historical |
| 478 | 2017-12-06 | The Ralph Drexel Collection Online: Part 7 | 198 | name does not mention coins, banknotes, books, Australiana or historical |
| 453 | 2017-10-25 | The Ralph Drexel Collection Online: Part 6 | 201 | name does not mention coins, banknotes, books, Australiana or historical |
| 389 | 2017-09-05 | Drexel Part 5 Online | 233 | name does not mention coins, banknotes, books, Australiana or historical |
| 434 | 2017-08-11 | Postmarks, Postal History & Picture Postcards | 600 | name does not mention coins, banknotes, books, Australiana or historical |
| 364 | 2017-08-15 | Sporting Memorabilia | 597 | name does not mention coins, banknotes, books, Australiana or historical |
| 381 | 2017-08-09 | Drexel Part 4 Online | 234 | name does not mention coins, banknotes, books, Australiana or historical |
| 367 | 2017-06-21 | Sir Edward Ford Collection of Autographs & Artworks: Part 2 Online | 23 | name does not mention coins, banknotes, books, Australiana or historical |
| 303 | 2017-06-26 | Stamps & Postal History | 1416 | name does not mention coins, banknotes, books, Australiana or historical |
| 348 | 2017-06-14 | The Ralph Drexel Collection: Part 3 Online | 206 | name does not mention coins, banknotes, books, Australiana or historical |
| 346 | 2017-05-30 | Stamps and Postal History Online | 245 | name does not mention coins, banknotes, books, Australiana or historical |
| 318 | 2017-05-17 | Rock 'n Roll Online | 105 | name does not mention coins, banknotes, books, Australiana or historical |
| 312 | 2017-05-16 | Sporting Memorabilia | 632 | name does not mention coins, banknotes, books, Australiana or historical |
| 326 | 2017-05-03 | The Rail Road Online | 189 | name does not mention coins, banknotes, books, Australiana or historical |
| 329 | 2017-04-13 | The Ted Lynch Collection of Sports Cards | 307 | name does not mention coins, banknotes, books, Australiana or historical |
| 321 | 2017-04-04 | The Ralph Drexel Collection Online: Part 2 | 233 | name does not mention coins, banknotes, books, Australiana or historical |
| 320 | 2017-04-06 | The Jascha Heifetz and Family Collection Online | 136 | name does not mention coins, banknotes, books, Australiana or historical |
| 301 | 2017-04-04 | Tom Frommer’s Airmails Part II – “Famous Pilots & Famous Flights” International Pioneers, Australia, New Guinea & Papua | 319 | name does not mention coins, banknotes, books, Australiana or historical |
| 302 | 2017-04-03 | Victoria: featuring Max Watson’s Franks & Les Molnar’s TPOs | 492 | name does not mention coins, banknotes, books, Australiana or historical |
| 305 | 2017-03-21 | Stamps & Postal History Online | 253 | name does not mention coins, banknotes, books, Australiana or historical |
| 288 | 2017-02-22 | The Ralph Drexel Collection Online: Part 1 | 246 | name does not mention coins, banknotes, books, Australiana or historical |
| 310 | 2017-02-27 | Stamps, Postal History & Picture Postcards | 1322 | name does not mention coins, banknotes, books, Australiana or historical |
| 304 | 2017-02-01 | Stamps & Postal History Online | 200 | name does not mention coins, banknotes, books, Australiana or historical |
| 282 | 2016-12-06 | Sports Online | 558 | name does not mention coins, banknotes, books, Australiana or historical |
| 241 | 2016-11-28 | Stamps & Postal History | 1348 | name does not mention coins, banknotes, books, Australiana or historical |
| 247 | 2016-10-23 | The America's Cup Auction featuring the Private Collections of Ben Lexcen & Alan Bond | 378 | name does not mention coins, banknotes, books, Australiana or historical |
| 200 | 2016-09-19 | Sporting Memorabilia | 863 | name does not mention coins, banknotes, books, Australiana or historical |
| 226 | 2016-09-11 | Tom Frommer’s Grand Prix Pioneer Australian Air Mails | 330 | name does not mention coins, banknotes, books, Australiana or historical |
| 249 | 2016-09-11 | Australian Colonies: the Trevor Hiscock Collection | 262 | colonial postage stamps (catalogue checked) |
| 230 | 2016-06-25 | Sir Edward Ford Autographs Collection | 40 | name does not mention coins, banknotes, books, Australiana or historical |
| 210 | 2016-06-29 | Stamps and Postal History | 1007 | name does not mention coins, banknotes, books, Australiana or historical |
| 209 | 2016-05-23 | Arthur Gray Part II | 361 | name does not mention coins, banknotes, books, Australiana or historical |
| 190 | 2016-05-10 | Sporting Memorabilia | 800 | name does not mention coins, banknotes, books, Australiana or historical |
| 191 | 2016-03-21 | Quarterly Collectors Auction Series | 821 | name does not mention coins, banknotes, books, Australiana or historical |
| 202 | 2016-02-25 | Stamps & Postal History | 928 | name does not mention coins, banknotes, books, Australiana or historical |
| 161 | 2016-02-08 | Sporting Memorabilia | 731 | name does not mention coins, banknotes, books, Australiana or historical |
| 162 | 2015-12-14 | The Picture Postcard As Art: Images from the Golden Era | 1138 | name does not mention coins, banknotes, books, Australiana or historical |
| 171 | 2015-12-08 | Quarterly Collectors Auction Series | 942 | name does not mention coins, banknotes, books, Australiana or historical |
| 160 | 2015-11-08 | The Marvin Hurnall Collection | 435 | name does not mention coins, banknotes, books, Australiana or historical |
| 169 | 2015-11-02 | The Pharlap Auction | 2 | name does not mention coins, banknotes, books, Australiana or historical |
| 172 | 2015-10-30 | The Arthur Gray Collection | 502 | name does not mention coins, banknotes, books, Australiana or historical |
| 157 | 2015-09-21 | Quarterly Collectors Auction Series | 1121 | name does not mention coins, banknotes, books, Australiana or historical |
| 143 | 2015-09-07 | Sporting Memorabilia | 781 | name does not mention coins, banknotes, books, Australiana or historical |
| 139 | 2015-06-29 | Quarterly Collectors Auction Series | 1072 | name does not mention coins, banknotes, books, Australiana or historical |
| 122 | 2015-04-23 | Sporting Memorabilia | 583 | name does not mention coins, banknotes, books, Australiana or historical |
| 117 | 2015-03-30 | Quarterly Collectors Auction Series | 1036 | name does not mention coins, banknotes, books, Australiana or historical |
| 142 | 2015-03-05 | Stamps and Postal History | 322 | name does not mention coins, banknotes, books, Australiana or historical |
| 101 | 2015-02-03 | Sporting Memorabilia | 607 | name does not mention coins, banknotes, books, Australiana or historical |
| 110 | 2014-12-02 | Quarterly Collectors Auction Series | 1278 | name does not mention coins, banknotes, books, Australiana or historical |
| 91 | 2014-11-07 | The Melbourne Cup Auction | 621 | name does not mention coins, banknotes, books, Australiana or historical |
| 104 | 2014-09-01 | The Fletch Collection | 111 | name does not mention coins, banknotes, books, Australiana or historical |
| 95 | 2014-08-25 | Quarterly Collectors Auction Series | 995 | name does not mention coins, banknotes, books, Australiana or historical |
| 94 | 2014-08-12 | The Julian Sterling Philately Collection - Part 3 | 207 | name does not mention coins, banknotes, books, Australiana or historical |
| 93 | 2014-08-12 | The Julian Sterling Philately Collection - Part 2 | 217 | name does not mention coins, banknotes, books, Australiana or historical |
| 85 | 2014-08-05 | Sporting Memorabilia | 726 | name does not mention coins, banknotes, books, Australiana or historical |
| 51 | 2014-05-21 | Sporting Memorabilia | 784 | name does not mention coins, banknotes, books, Australiana or historical |
| 77 | 2014-05-06 | Quarterly Collectors Auction Series | 927 | name does not mention coins, banknotes, books, Australiana or historical |
| 83 | 2014-04-30 | The Julian Sterling Philately Collection - Part 1 | 152 | name does not mention coins, banknotes, books, Australiana or historical |
| 46 | 2014-04-13 | Antique & Collectable Cameras | 235 | name does not mention coins, banknotes, books, Australiana or historical |
| 31 | 2014-02-25 | Sporting Memorabilia | 496 | name does not mention coins, banknotes, books, Australiana or historical |
| 49 | 2014-02-04 | Quarterly Collectors Auction Series | 795 | name does not mention coins, banknotes, books, Australiana or historical |
| 41 | 2013-12-05 | Sporting Memorabilia | 525 | name does not mention coins, banknotes, books, Australiana or historical |
| 26 | 2013-12-04 | Quarterly Collectors Auction Series | 582 | name does not mention coins, banknotes, books, Australiana or historical |
| 25 | 2013-09-26 | The Alex Jesaulenko Collection | 187 | name does not mention coins, banknotes, books, Australiana or historical |
| 118 | 2013-05-16 | Airmails 2013 | 353 | name does not mention coins, banknotes, books, Australiana or historical |
| 71 | 2013-05-08 | Medical, Dental & Pharmaceutical | 291 | name does not mention coins, banknotes, books, Australiana or historical |
| 116 | 2013-03-27 | Sporting Memorabilia | 450 | name does not mention coins, banknotes, books, Australiana or historical |
