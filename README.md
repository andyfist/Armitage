# Armitage

Bargain hunting for Launceston-area auctions (7250 + 50 km): scrape the catalogue,
have Claude triage every lot and look at the photos of anything promising, and
report lots with a realistic **$1,000+ profit** after buyer's premium.

## Sources

| Source | Status |
|---|---|
| Armitage Auctions (armitage.bidsonline.com.au), Invermay | ✅ `scraper/armitage.py`, about 1,900 lots per sale |
| Tulloch's, Launceston | not yet (site is a single page, no catalogue online) |
| Facebook Marketplace | `scraper/marketplace.py` uses Apify's logged-out scraper, so your own account is never used. Needs `APIFY_TOKEN` |
| Gumtree | ❌ blocks automated requests |
| Garage Sale Trail (November) | to add when the 2026 map is published |

## Running a hunt

```sh
pip install requests
python3 scraper/armitage.py -o data/lots.json            # all open lots, titles, bids, close times
cd scraper && python3 fetch_photos.py ../data/lots.json ../data/shortlist 883 818 943
```

Facebook Marketplace (new listings since the last run, 50 km around 7250):

```sh
python3 scraper/marketplace.py -o data/fb.json --photos data/fb_photos
```

Then ask Claude to follow `HUNTING.md`, which covers the triage rules and report format.
Reports go in `reports/`.
