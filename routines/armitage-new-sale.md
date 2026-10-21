# Routine: Armitage new-sale check and funnel

Schedule: every two hours, 7am to 9pm Australia/Hobart (`CRON_TZ=Australia/Hobart 23 7-21/2 * * *`).
Needs: repo andyfist/armitage (`main`), Gmail, the Workflow tool.

Armitage puts a sale's catalogues online a few days to a week before the lots close
(the 21 Oct 2026 sale appeared on 16 and 19 Oct). This check notices a new catalogue
within two hours of it appearing, emails Andy, and then runs the funnel on it: prep,
title pass, photo scan, cloud price research, bid check. Each stage that finishes sends
Andy one email. Everything hangs off `pipeline/state/sales.json`.

## Prompt

You are running the Armitage new-sale check. The repo is checked out in your working
directory. First run `git fetch origin main && git checkout main && git pull --ff-only origin main`.
If `pipeline/new_sales.py` is still missing, reply "new-sale check is not on main yet" and stop.

1. Run `python3 pipeline/new_sales.py`. It prints JSON with `current` (catalogues on
   the site now), `new` (catalogues never seen before, each with `chid`, `name`, `lots`,
   `close_first`, `close_last` and an `email` body), `errors` and `alert_unreachable`.
2. For each entry in `new`, email andyfist@gmail.com from Gmail, plain text, subject
   "New Armitage sale: <name>", body exactly the `email` field. One email per catalogue.
3. If `alert_unreachable` is true (the site failed two checks running), email
   andyfist@gmail.com once, subject "Armitage check: site unreachable", with the error
   text and this line: "If this is the cloud workspace's network setting, allow
   armitage.bidsonline.com.au under Project settings, Environment." Do not email on a
   single failure.
4. Commit and push the state: `git add pipeline/state/sales.json && git commit -m "Armitage sales seen <date>" && git push origin main`.
   If the push is rejected, `git pull --rebase origin main` and push again.
5. For each new catalogue, run the funnel, one catalogue at a time. Every command below
   is read-only against Armitage and uses only files under `pipeline/sales/<chid>/`.
   a. Prep: `python3 pipeline/prep.py <chid>` (20 to 40 minutes for a 600-lot catalogue:
      it reads every lot page and downloads the photos of every lot that is not excluded).
      It ends by printing the catalogue summary JSON. Then run
      `python3 pipeline/stage.py <chid> prepped --note "<lots> lots read, <with_photos> with photos; <classes.exclude> excluded, <classes.always_look> straight to the photo scan, <classes.title_pass> to the title pass"`
      and email its output to andyfist@gmail.com (first line is the subject, the rest is the body).
   b. Scan and research: run the Workflow tool with the script file `pipeline/wf_funnel.js`
      and, as `args`, the JSON object in `pipeline/sales/<chid>/wfargs.json`. Andy has
      opted in to this multi-agent run through this routine. It takes one to several
      hours. Save the returned result to `pipeline/sales/<chid>/funnel_result.json`.
      Then `python3 pipeline/stage.py <chid> scanned --note "<counts.SCANNED> lots photo-scanned, <candidates_total> candidates, <researched count> researched"`
      and email the output. If the workflow fails part way, run it again: finished
      batches are skipped, and the files written so far are kept.
   c. Bid check: `python3 pipeline/assess.py <chid>` prints the "first pass done" email;
      send it to andyfist@gmail.com with subject "Armitage <name>: first pass, <PASS> lots pass the $200 rule".
      Then `python3 pipeline/stage.py <chid> researched` (no email needed for that one).
   d. Commit the sale's files (photos, sheets, crops and per-lot files are ignored by git)
      and the state: `git add pipeline/sales/<chid> pipeline/state/sales.json && git commit -m "Armitage <chid>: funnel" && git push origin main`.
6. Reply in one short line: catalogues on the site, new ones found, emails sent, funnel
   stages run, anything that failed. Commit nothing else and send no other email.
