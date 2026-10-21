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
2. Triage per the Quick scan rules in HUNTING.md: read every title, look at the one photo of
   every book lot and anything vague, web-search sold prices for anything that could clear
   $500 over the asking price.
3. If there is a hit, or something promising that needs the full gallery to judge, email
   andyfist@gmail.com from Gmail straight away, one email per listing, plain text, subject
   "Marketplace hit: <title> – $<price>". Body: the listing link first, then what it is,
   your value range and the evidence, the most you'd pay, the one question to ask the
   seller, and whether this is a confirmed hit or a "worth a look".
4. If nothing qualifies, send no email and commit nothing. Finish with one line: listings
   triaged, Apify cost of the run, and anything that failed.
