# Chrome brief: eBay sold prices (and Leski results) for the price database

**Who runs this:** Claude in Chrome on Andy's computer (Claude Desktop open, computer awake).
The cloud cannot do this part: eBay returns 403 to it, and Leski's results pages sit behind
a CloudFront block. Both open normally in Andy's own browser.

**Paste this into a new Claude Desktop chat with the Chrome extension switched on.**

---

You are building a sold-price list for coins and books, to help judge lots at Tasmanian
auctions. Read pages only. Never bid, buy, message sellers or change any account setting.
Go at a human pace (a few seconds between pages). If eBay shows a captcha or "unusual
activity" page, stop and tell Andy.

## 1. eBay Australia sold listings

For each search below, open
`https://www.ebay.com.au/sch/i.html?_nkw=<words>&LH_Sold=1&LH_Complete=1&_sop=13&_ipg=240&LH_PrefLoc=1`
(sold and completed, Australia only, newest first, 240 per page). Read the first page only.
Record **sold** listings only (green price, "Sold" date). Skip "Best offer accepted" when the
real price is hidden, and skip lots that are clearly reproductions.

Coins and notes (category `coins`):
- 1930 penny; 1923 halfpenny; 1925 penny; 1946 penny
- Australian florin 1932; Australian shilling 1915H; Australian crown 1937 1938
- Australian sovereign; Australian half sovereign; Sydney Mint sovereign
- pre-decimal coin collection; Australian coin album; silver coins lot Australian
- Australian banknote ten shilling; Australian one pound note; Australian five pound note
- Australian $1 note star; Australian error note; Australian first prefix note
- Australian proof set; 1966 round 50 cent; Perth Mint gold coin
- war medal Australian named; WW1 trio; Tasmania token; Tasmanian trade token

Books (category `books`):
- Louisa Anne Meredith; Tasmania first edition book; Van Diemen's Land book
- Australiana first edition; Gould birds Australia; Australian exploration journal
- Antarctic first edition; Mawson Home of the Blizzard; Captain Cook voyages
- signed first edition Australian; Norman Lindsay limited edition; Ferguson bibliography
- antique map Australia; Tasmania antique map; early Australian photograph album

## 2. Leski Auctions prices realised (optional, if time allows)

Open `https://www.leski.com.au/previous-auctions/`. For each auction whose name mentions
coins, banknotes, books, Australiana or historical, open its "Prices Realised" link
(`auctions.leski.com.au/auctions/print-realized-prices/id/<n>`). Record every lot with a
price. Leski asks for 10 seconds between pages: wait that long.

## 3. How to record each sale

One JSON object per sold item, in this exact shape:

```json
{"source": "ebay", "sale": "2026-10-22", "lot": "<eBay item number>",
 "date": "YYYY-MM-DD", "title": "<listing title>", "description": "<condition, grade, edition, anything useful>",
 "hammer_aud": 123.0, "premium_included": true, "unsold": false,
 "url": "https://www.ebay.com.au/itm/<item number>", "category": "coins"}
```

- eBay: `sale` is today's date (the day you searched), `date` is the sold date, `hammer_aud`
  is the item price without postage, `premium_included` true (no buyer's premium on eBay).
- Leski: `source` "leski", `sale` the auction id number, `lot` the lot number, `date` the
  auction date, `hammer_aud` the price shown, `premium_included` false, `url` the prices
  realised page.

Save all records as one JSON list to
`databases/ebay/sale_<today>.json` (or `databases/leski/sale_<id>.json`) in Andy's copy of the
Armitage repo. If you cannot write files, put the JSON in your reply and Andy will paste it
into a cloud chat to be committed. `python3 -I databases/load.py <words>` picks the new files
up automatically.

Also record, at the end, how many sold items each search returned, so we know which searches
are worth repeating.
