# Routine: hourly Marketplace quick scan

Schedule: hourly, 7am to 10pm Australia/Hobart (`CRON_TZ=Australia/Hobart 7 7-22 * * *`).
Needs: repo andyfist/armitage (branch with `scraper/marketplace.py`), `APIFY_TOKEN`, Gmail.

## Prompt

You are running the hourly Facebook Marketplace quick scan for the Armitage bargain hunt.
The repo is checked out in your working directory. If `scraper/marketplace.py` is missing,
run `git fetch origin claude/charming-brown-bo3xbf && git checkout claude/charming-brown-bo3xbf`.
Read HUNTING.md; the profit threshold is $500.

1. Run `python3 scraper/marketplace.py --no-details --state armitage-7250-quick -o data/fb_quick.json --photos data/fb_photos --max-spend 0.10`.
   It returns only listings new since the last quick scan, usually a handful. If it says
   Apify aborted the run or another run holds the state lock, stop; do not retry.
2. Shortlist per the Quick scan rules in HUNTING.md: read every title, look at the one
   photo of every book lot and anything vague, and keep anything that could plausibly
   clear $500 over the asking price.
3. For each shortlisted listing run
   `python3 scraper/marketplace.py --lookup "<exact title>" -o data/fb_lookup.json --photos data/fb_photos`
   (several --lookup flags in one run is fine) and judge it on the full gallery and
   description, then web-search sold prices.
4. If there is a hit, email andyfist@gmail.com from Gmail straight away, one email per
   listing, plain text, subject "Marketplace hit: <title> – $<price>". Body: the listing
   link first, then what it is, your value range and the evidence from the photos and
   description, the most you'd pay, and the one question to ask the seller.
5. If nothing qualifies, send no email and commit nothing. Finish with one line: listings
   triaged, lookups done, Apify cost, and anything that failed.
