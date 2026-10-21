# Armitage

Bargain hunting for Launceston-area auctions (7250 + 100 km): scrape the catalogue,
have Claude triage every lot and look at the photos of anything promising, research
resale prices, and set a maximum bid that still leaves a worthwhile profit.

Profit rule (agreed 21 Oct 2026): at least **$200 net profit** after Armitage's 22%
buyer's premium and the selling fees. `HUNTING.md` and `work/flip_rule.py` still carry
the older "$500 or double your money" rule and will be updated with the scan funnel.

## What is where

| Path | What it is |
|---|---|
| `scraper/armitage.py` | Pulls every open Armitage lot (title, bid, close time, photos) into one JSON file |
| `scraper/marketplace.py` | Facebook Marketplace puller via Apify (quick scan, lookup, full scan) |
| `scraper/fetch_photos.py` | Downloads the photos of shortlisted lots |
| `routines/` | The prompts behind the two scheduled runs: hourly Marketplace quick scan, 6:40 am daily digest |
| `HUNTING.md` | Triage rules and report format for the title-first hunt |
| `reports/` | One report per sale close date from the daily digest |
| `work/` | The deep-scan toolkit and every sale researched so far (see below) |
| `scans/` | Raw photo-scan output per batch of 15 lots |
| `BOOK_RESEARCH_HANDOVER.md` | A brief for a Claude session on the home computer (Chrome, signed in) to price book lots |

### The deep-scan toolkit in `work/`

| Script | Job |
|---|---|
| `watch_armitage.py` | Lists the catalogues on armitage.bidsonline.com.au and prints any not seen before (`armitage_catalogues.json` remembers them) |
| `prep_armitage.py <chid> <key>` | Reads one catalogue, downloads every photo, builds contact sheets and batches of 15 lots for the scan |
| `wf_armitage.js` | The scan workflow: photo scan (Sonnet, estimate-blind), rescore, market comps, verify |
| `comps.py <words>` | Looks an item up in the results database (`gowans_all.json`, 75,655 Gowans hammer prices, plus `sold_db.json`); see `RESULTS_DB.md` |
| `flip_rule.py` | Turns a resale comp into a maximum hammer price after premium and selling fees |
| `refresh_armitage.py`, `refresh_bids.py` | Re-read current bid and bid count for shortlisted lots |
| `build_armitage.py` | Builds the tracker page (`armitage_<slug>.html`) from the results |
| `prep_webbs.py`, `wf_webbs.js`, `crawl_gowans.py`, `wf_gowans.js`, `wf_mainland.js` | The same tools adapted for Webb's (NZ whisky), Gowans (Hobart) and the stopped mainland scan |

Per-sale files are named by catalogue: `armitage<chid>_*.json` (Armitage 21 Oct 2026 was
catalogues 28838 to 28842), `gowans<no>_*`, `webbs991_*`. `raw_*`, `obs_*` and
`verified_*` are the scan's working files. `resale_plan_oct21.md` is the plan for
the lots won on 21 Oct.

Most `work/` scripts still hard-code `/home/user/Armitage/work` as their folder; that
is on the list to fix.

## History

This branch combines five earlier work branches (`claude/busy-cannon-xdpbf0`,
`claude/charming-brown-bo3xbf`, `claude/dreamy-euler-viirhe`,
`claude/new-session-to7a94`, `claude/zen-darwin-xj10rt`) that had grown separately
from an empty `main`. Nothing was dropped; where two branches held different versions
of the same file, the newer Armitage state won.

## Sources

| Source | Status |
|---|---|
| Armitage Auctions (armitage.bidsonline.com.au), Invermay | ✅ `scraper/armitage.py` and `work/prep_armitage.py`, about 1,900 lots per sale |
| Gowans Auctions, Moonah | ✅ `work/crawl_gowans.py` (results database) and `work/wf_gowans.js` (weekly scan) |
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

Facebook Marketplace (new listings since the last run, 100 km around 7250):

```sh
# quick scan: titles, prices, one photo; ~US$0.02 a run, fine to run hourly
python3 scraper/marketplace.py --no-details --state armitage-7250-newest -o data/fb_quick.json --photos data/fb_photos --max-spend 0.10
# lookup: gallery and description for one shortlisted listing; ~US$0.02 a title
python3 scraper/marketplace.py --lookup "The Shannon Rise by R.H. Wigram" -o data/fb_lookup.json --photos data/fb_photos
# full scan: details for everything new; ~US$0.45 a run, so on demand only
python3 scraper/marketplace.py -o data/fb.json --photos data/fb_photos --max-spend 0.75
```

The scheduled runs (hourly quick scan, daily digest) are defined in `routines/`; they
need to be created in the claude.ai routines UI with the repo and the Gmail connector
attached, because sessions started by the API get neither.

Then ask Claude to follow `HUNTING.md`, which covers the triage rules and report format.
Reports go in `reports/`.
