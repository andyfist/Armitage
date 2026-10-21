# Routine: price databases, nightly top-up

Schedule: daily at 2:10 am Australia/Hobart (`CRON_TZ=Australia/Hobart 10 2 * * *`).
Needs: repo andyfist/armitage (`main`).

The price databases in `databases/` (Noble Numismatics coins, Australian Book Auctions,
Armitage's own past results, more as they are added) feed the promote rule in
`pipeline/promote.py` and the comps lookup in `pipeline/comps.py`. Each scraper only
fetches sales it has not saved yet, so a quiet night is a handful of requests.

## Prompt

You are running the nightly price-database top-up. The repo is checked out in your
working directory. First run `git fetch origin main && git checkout main && git pull --ff-only origin main`.

1. `sh databases/nightly.sh` (every scraper in turn; each is read-only, honours
   robots.txt and stops on a 403 or bot check, recording `blocked` in its state file).
2. If `pipeline/armitage_results.py` exists, run `python3 pipeline/armitage_results.py --refresh-open`
   so sales that closed since the last run get their closing bids and bid histories into
   `databases/armitage.json`.
3. `python3 pipeline/promote.py --rebuild` (the promote index is not in git; this keeps it
   current with the databases).
4. If `git status --short databases/` shows changes: `git add databases && git commit -m "Databases top-up <date>" && git push origin main`
   (if the push is rejected, `git pull --rebase origin main` and push again).
5. Reply in one short line: sales added per source, anything blocked, whether a commit was
   pushed. Send no email. If a source has recorded `blocked` in its state file for three
   nights running, say so in the reply so it can be looked at.
