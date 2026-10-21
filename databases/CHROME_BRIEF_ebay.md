# Chrome brief: eBay sold prices via Terapeak (and Leski results) for the price database

**Use Sonnet for this chat** (pick Sonnet in the model menu, or say "use Sonnet").

**Who runs this:** Claude in Chrome on Andy's computer (Claude Desktop open, computer awake),
signed in to Andy's own eBay account. The cloud cannot do this part: eBay returns 403 to it,
and Leski's results pages sit behind a CloudFront block. Both open normally in Andy's browser.

**Paste this into a new Claude Desktop chat with the Chrome extension switched on.**

---

You are building a sold-price list for coins and books, to help judge lots at Tasmanian
auctions. Read pages only. Never bid, buy, list, message sellers or change any account
setting. Go at a human pace (a few seconds between pages). If eBay shows a captcha or
"unusual activity" page, stop and tell Andy.

## 1. eBay sold prices from Terapeak (Seller Hub, Product Research)

Terapeak is eBay's research tool inside Seller Hub. It shows real sold prices and looks back
much further than the normal "sold items" search.

**Getting in.** Open `https://www.ebay.com.au/sh/research` (or Seller Hub, then Research, then
Product Research). **If you see a prompt to register as a seller, a "not available" message, or
a login that fails, stop and tell Andy plainly:** he may need to switch on Seller Hub / Terapeak
on his eBay account first (free for most accounts; eBay may ask for a seller registration or
subscription). Do not fill in registration or payment forms yourself. If Terapeak will not
open at all, say so and offer the fallback: eBay sold search at
`https://www.ebay.com.au/sch/i.html?_nkw=<words>&LH_Sold=1&LH_Complete=1&_sop=13&_ipg=240&LH_PrefLoc=1`
(only the last few months, so tell Andy it is the weaker option).

**For each search below:**
1. In Product Research, choose the **Sold** tab (not Active).
2. Type the keywords and search.
3. Set the date range to the **longest one offered** (the dropdown usually goes up to 365
   days; use anything longer if Andy's account offers it, for example two years). Note which
   range you used.
4. Set the marketplace/site to **eBay Australia** (Australian dollars). Leave condition on all.
5. Read the sold-listings table: title, sold price, shipping, condition and sold date, plus the
   listing link where Terapeak shows one. Page through up to about 100 rows per search, newest
   first. Stop earlier if the rows stop matching the search.
6. Skip rows with a hidden price ("Best offer accepted" without a real price) and anything
   clearly a reproduction.

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

- eBay (Terapeak): `sale` is today's date (the day you searched), `date` is the sold date,
  `hammer_aud` is the item price without postage, `premium_included` true (no buyer's premium
  on eBay). Put the shipping cost, the search words and the date range used in `description`,
  e.g. "condition Used; postage $12; Terapeak 'Australian florin 1932', 365 days". If Terapeak
  gives no item number, use `lot` "terapeak-<row number>" and leave `url` as the Terapeak page.
- Leski: `source` "leski", `sale` the auction id number, `lot` the lot number, `date` the
  auction date, `hammer_aud` the price shown, `premium_included` false, `url` the prices
  realised page.

Save all records as one JSON list to
`databases/ebay/sale_<today>.json` (or `databases/leski/sale_<id>.json`) in Andy's copy of the
Armitage repo. If you cannot write files, put the JSON in your reply and Andy will paste it
into a cloud chat to be committed. `python3 -I databases/load.py <words>` picks the new files
up automatically.

Also record, at the end, how many sold items each search returned (and the date range used), so we know which searches
are worth repeating.
