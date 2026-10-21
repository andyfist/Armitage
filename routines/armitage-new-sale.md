# Routine: Armitage new-sale check

Schedule: every two hours, 7am to 9pm Australia/Hobart (`CRON_TZ=Australia/Hobart 23 7-21/2 * * *`).
Needs: repo andyfist/armitage (`main`), Gmail.

Armitage puts a sale's catalogues online a few days to a week before the lots close
(the 21 Oct 2026 sale appeared on 16 and 19 Oct). This check notices a new catalogue
within two hours of it appearing and emails Andy. Later stages of the pipeline hang
off the same state file, `pipeline/state/sales.json`.

## Prompt

You are running the Armitage new-sale check. The repo is checked out in your working
directory. First run `git fetch origin main && git checkout main && git pull --ff-only origin main`.
If `pipeline/new_sales.py` is still missing, reply "new-sale check is not on main yet" and stop.

1. Run `python3 pipeline/new_sales.py`. It prints JSON with `current` (catalogues on
   the site now), `new` (catalogues never seen before, each with `name`, `lots`,
   `close_first`, `close_last` and an `email` body), `errors` and `alert_unreachable`.
2. For each entry in `new`, email andyfist@gmail.com from Gmail, plain text, subject
   "New Armitage sale: <name>", body exactly the `email` field. One email per catalogue.
3. If `alert_unreachable` is true (the site failed two checks running), email
   andyfist@gmail.com once, subject "Armitage check: site unreachable", with the error
   text and this line: "If this is the cloud workspace's network setting, allow
   armitage.bidsonline.com.au under Project settings, Environment." Do not email on a
   single failure.
4. If `pipeline/state/sales.json` changed, commit it to main and push:
   `git add pipeline/state/sales.json && git commit -m "Armitage sales seen <date>" && git push origin main`.
   If the push is rejected, `git pull --rebase origin main` and push again.
5. Reply in one short line: catalogues on the site, new ones found, emails sent,
   anything that failed. Commit nothing else and send no other email.
