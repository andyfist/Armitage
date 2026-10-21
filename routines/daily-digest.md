# Routine: daily digest

Schedule: daily at 6:40am Australia/Hobart (`CRON_TZ=Australia/Hobart 40 6 * * *`).
Needs: repo andyfist/armitage (branch with `scraper/marketplace.py`), `APIFY_TOKEN`, Gmail.

## Prompt

You are running the daily Armitage bargain-hunt digest. The repo is checked out in your
working directory. If `scraper/marketplace.py` is missing, run
`git fetch origin claude/charming-brown-bo3xbf && git checkout claude/charming-brown-bo3xbf`.
Read HUNTING.md and follow it; the profit threshold is $500.

1. Marketplace. Run the quick scan: `python3 scraper/marketplace.py --no-details --state armitage-7250-newest -o data/fb_quick.json --photos data/fb_photos --max-spend 0.10`
   and triage it per HUNTING.md. On Mondays only, also run the full scan,
   `python3 scraper/marketplace.py -o data/fb.json --photos data/fb_photos --max-spend 0.75`,
   and triage that with the galleries and descriptions. If a run says Apify aborted it or
   another run holds the state lock, note it and move on; do not retry.
2. Armitage Auctions. Run `python3 scraper/armitage.py -o data/lots.json` and find the
   close date of the current sale. If `reports/<close-date>.md` exists, that sale is done:
   skip to step 3. Otherwise follow HUNTING.md steps 2-5 for the whole catalogue (title
   pass on every lot; `cd scraper && python3 fetch_photos.py ../data/lots.json ../data/shortlist <lot numbers>`
   for the shortlist; price check; write `reports/<close-date>.md`), then commit and push
   the report to the branch you are on.
3. Alerts already sent: search Gmail for `in:sent subject:"Marketplace hit" newer_than:1d`.
4. Apify spend: GET https://api.apify.com/v2/users/me/limits with header
   `Authorization: Bearer $APIFY_TOKEN`; read current.monthlyUsageUsd and
   limits.maxMonthlyUsageUsd.
5. Email andyfist@gmail.com from Gmail, subject "Armitage daily: <date>", plain text, even
   if there is nothing to report. Sections: Hits (link, price or bid, value range, evidence,
   max to pay, question to ask); Near misses (one line each); Alerts sent in the last 24 h;
   Leads (garage, clearing and deceased-estate sales with date and address); Counts
   (Marketplace listings triaged, auction lots triaged or "sale already covered"); Apify
   spend (today and month-to-date against the limit). Short: it is read on a phone.

Send no other email. Do not change the scrapers. If anything fails, say exactly what in
the digest if you can send it, otherwise in your final message.
