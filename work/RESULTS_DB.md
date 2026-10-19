# Results database

Read-only record of what things sold for, used to set maximum bids.

- `gowans_all.json`: every lot on Gowans' public API (75,655 lots, July 2024 to Oct 2026), hammer = sale_price / 100, 0 = unsold. Rebuild or top up with `python3 -I crawl_gowans.py` (about 15 minutes, 1 request a second, resumable; delete the file to start again).
- `sold_db.json`: every sold comp the agents found in the *_result.json files, with URL and date. Rebuild with `python3 -I build_sold_db.py`.
- `comps.py <words>`: look up an item. `--years N` and `--min-price N` filter. Prints lowest, median and highest hammer.

Hammer prices exclude the 22% buyer's premium. Gowans dates are listing dates (the sale is about a week later). UNSOLD and ASKING prices never set a maximum.
Not yet included: Armitage's own past results (no public results page found), ABA price-list PDFs in bulk, other houses.
