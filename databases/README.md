# Price databases

Real prices realised at Australian auction houses, used by the Armitage pipeline to
**promote** lots for a closer look (a title that matches things that sold for $250 or more).
Nothing here is ever used to exclude a lot.

## Coverage (21 Oct 2026)

| Source | What | Sales | Lots | With a sold price | Dates |
|---|---|---|---|---|---|
| `noble/` Noble Numismatics, Sydney | Australian and world coins, banknotes, medals, tokens | 101 (44 to 142, plus 888) | 447,979 | 371,774 | Mar 1994 to Jul 2026 |
| `aba/` Australian Book Auctions, Melbourne | Australiana, voyages, maps, rare books | 20 (100 to 119, every sale they have held) | 3,603 | 2,969 | Jun 2021 to Sep 2026 |

Gowans (75,000 lots) stays in `work/gowans_all.json`; see `work/RESULTS_DB.md`.

Not scraped, and why:
- **Leski** (Melbourne, coins and banknotes): the results pages return HTTP 403 (CloudFront block) to the cloud. Included in the Chrome brief instead.
- **Lawsons**: "Access Denied" page on every request, so left alone.
- **Davidson** (Sydney): the results search came back empty to a plain request (it seems to need a browser session), and the sales are almost all art.
- **eBay**: 403 from the cloud. See `CHROME_BRIEF_ebay.md`, which Andy's computer can run; it reads sold prices from Terapeak (eBay Seller Hub), which looks back further than plain eBay sold search.
- Noble sale 889 (eNZ1, New Zealand medals) has no lots recorded on its page.

## Record format

Each `<source>/sale_<n>.json` (Noble files are gzipped, `.json.gz`) is a JSON list, one record per line:

```json
{"source": "noble", "sale": 142, "lot": "2173", "date": "2026-07-28",
 "title": "New Zealand: commemorative ten dollars, 1990, boxed set of uncuts, set 0198/1000.",
 "description": "New Zealand, commemorative ten dollars, 1990, boxed set of uncuts, set 0198/1000. Uncirculated.",
 "hammer_aud": 700.0, "premium_included": false, "unsold": false,
 "url": "https://www.noble.com.au/auctions/lot/?id=460159", "category": "coins"}
```

- `date` is the first day of the sale.
- `hammer_aud` is the hammer price. `premium_included` false means the buyer's premium is on top (Noble and ABA both quote hammer only).
- Unsold or passed-in lots have `hammer_aud` 0 and `unsold` true. Noble's sales before about 2010 list sold lots only, so passed lots are simply missing there.
- Extra fields some sources add: `sale_title` (Noble), `estimate_aud`, `catalogue_url` and `section` (ABA; section only where the catalogue text shows it).

## Using it

```sh
python3 -I databases/load.py 1930 penny --sold          # every word must match
python3 -I databases/load.py meredith tasmanian --min 250
```

In code: `sys.path.insert(0, 'databases'); from load import records` then
`for r in records(category='books'): ...`. Reading all 450,000 records takes about 3 seconds.

## Keeping it up to date

`sh databases/nightly.sh` runs every scraper. Each one keeps a state file
(`noble_state.json`, `aba_state.json`) and only fetches sales it has not saved, so a quiet
night makes about three requests. Then commit `databases/`.

Scraper rules: read-only, public results pages only, robots.txt honoured (including any
crawl delay), at least 1.5 seconds between requests, and a scraper stops and records
`blocked` in its state file the moment it sees a 403, 429 or bot-check page.

The ABA scraper needs `pdftotext` (poppler-utils) or the `pypdf` package. It caches PDFs in
`databases/.cache/` (not committed). Its records replace `work/aba_lots.json`, which had the
same prices but no dates, 132 bracketed years misread as lots, missed sub-lots such as 46.1, and one wrong price (sale 117 lot 17 sold for $4,000).

## Adding a source

Copy `aba.py` or `noble.py`, keep the record format, write `databases/<source>/sale_<n>.json`,
add a line to `nightly.sh` and a row to the coverage table above.
