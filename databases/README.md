# Price databases

Real prices realised at Australian auction houses, used by the Armitage pipeline to
**promote** lots for a closer look (a title that matches things that sold for $250 or more).
Nothing here is ever used to exclude a lot.

## Coverage (21 Oct 2026)

| Source | What | Sales | Lots | With a sold price | Dates |
|---|---|---|---|---|---|
| `noble/` Noble Numismatics, Sydney | Australian and world coins, banknotes, medals, tokens | 101 (44 to 142, plus 888) | 447,979 | 371,774 | Mar 1994 to Jul 2026 |
| `aba/` Australian Book Auctions, Melbourne | Australiana, voyages, maps, rare books | 20 (100 to 119, every sale they have held) | 3,603 | 2,969 | Jun 2021 to Sep 2026 |
| `ebay/` eBay Australia sold listings (Terapeak, run from Andy's computer) | coins and banknotes 1,489; books and maps 675 (42 searches) | 1 (searched 21 Oct 2026) | 2,164 | 2,164 | Oct 2023 to Oct 2026 |
| `leski/` Leski Auctions, Melbourne (prices realised, run from Andy's computer) | coins 5,770; books and paper 7,145; stamps 9,805; other Australiana 17,180 | 67 (coin, book, stamp and Australian & Historical sales) | 39,900 | 39,900 (sold lots only) | Feb 2013 to May 2026 |

Gowans (75,000 lots) stays in `work/gowans_all.json`; see `work/RESULTS_DB.md`.

Not scraped, and why:
- **Leski** (Melbourne, coins and banknotes): the results pages return HTTP 403 (CloudFront block) to the cloud, so `leski/` was collected with the Chrome brief on Andy's computer instead.
- **Lawsons**: "Access Denied" page on every request, so left alone.
- **Davidson** (Sydney): the results search came back empty to a plain request (it seems to need a browser session), and the sales are almost all art.
- **eBay**: 403 from the cloud. `ebay/` came from `CHROME_BRIEF_ebay.md` run on Andy's computer (Terapeak, 21 Oct 2026). Re-run it to add a new `ebay/sale_<date>.json`.

`SEARCH_COUNTS_ebay_leski.md` lists every eBay search (rows found, kept, sold-date span, why rows were dropped) and every Leski auction included or left out. Read its first section before pricing from these two: eBay prices are what the buyer paid (`premium_included` true), Leski prices are hammer only (add about 21.45% to compare), Terapeak shows at most 100 rows per search so many eBay searches only cover recent months, and the general book searches include cheap modern books. `ebay/drops_2026-10-21.json` holds every eBay row left out, with the reason. `leski/leski_archive.tsv` is Leski's full auction list; the two `*_categories.tsv` files record how each Leski lot was given its category (manual fixes and AI-assigned).
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
