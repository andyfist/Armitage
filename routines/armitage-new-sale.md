# Routine: Armitage new-sale check and funnel

Schedule: every two hours, 7am to 9pm Australia/Hobart (`CRON_TZ=Australia/Hobart 23 7-21/2 * * *`).
Needs: repo andyfist/armitage (`main`), Gmail, the Workflow tool.

Armitage puts a sale's catalogues online a few days to a week before the lots close
(the 21 Oct 2026 sale appeared on 16 and 19 Oct). This check notices a new catalogue
within two hours of it appearing, emails Andy, and then runs the funnel on it: prep,
photo scan of every lot (Opus, medium effort), price hints from our own databases, bid
check, and the Chrome pack. Since 27 Nov 2026 (Andy) the cloud does NO web price search:
every lot is priced in Chrome on Andy's PC, with eBay sold prices and Terapeak open and
his other sites signed in, from one combined prompt per batch of catalogues. Heavy and
bulky lots, large furniture, whitegoods and vehicles are left out and listed. Each stage
that finishes sends Andy one email. Everything hangs off `pipeline/state/sales.json`.

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
      opted in to this multi-agent run through this routine. It photo-scans every lot
      that is not left out, on Opus at medium effort, and looks up price hints in our own
      databases only (no web search: never pass `cloudWeb`). It takes one to several hours. Save the returned result to `pipeline/sales/<chid>/funnel_result.json`.
      Then `python3 pipeline/stage.py <chid> scanned --note "<counts.SCANNED> lots photo-scanned, <candidates_total> candidates, <researched count> researched"`
      and email the output. If the workflow fails part way, run it again: finished
      batches are skipped, and the files written so far are kept.
   c. Bid check: `python3 pipeline/assess.py <chid>` prints the "first pass done" email;
      send it to andyfist@gmail.com with subject "Armitage <name>: photo scan done, <PASS> lots pass on database prices so far".
      Say in the first line of the body that these are database prices only and that every lot
      is priced in Chrome next.
      Then `python3 pipeline/stage.py <chid> researched` (no email needed for that one).
   d. Chrome pack: do this once per run, AFTER steps a to c are done for every new catalogue,
      with all of this run's new catalogues together (Andy wants one combined Chrome prompt,
      not one per catalogue; Friday's and Monday's catalogues each get their own pack):
      `python3 pipeline/chrome_brief.py <chid> [<chid> ...]`. It writes the pack folder
      `pipeline/sales/packs/armitage_<chids>/` (PROMPT.md, index.json, left_out.md, chunks/) and
      `armitage_<chids>.zip` next to it, writes `chrome_email.txt` in each sale folder, and prints
      the counts. Every lot that is not left out is in it: Part A books, Part B art, Part C lots
      the scan flagged as possibly high value (all three on Opus helpers), Part D the rest (Sonnet).
      If the `mcp__remote-devices__device_commit_files` tool is available to you, copy PROMPT.md,
      index.json, left_out.md and the zip (save them under `/mnt/project-files/<pack name>/` first)
      to `C:\Users\Andy\Documents\claude\<pack name>\` on Andy's PC; if not, the email tells him
      how to get it. Then, for each catalogue, run
      `python3 pipeline/stage.py <chid> chrome_list --note "every lot in the Chrome pack <pack name>" --body pipeline/sales/<chid>/chrome_email.txt`
      and email the output of the first one only (one email per pack). Add the zip to the commit
      in step f: `git add pipeline/sales/packs/*.zip` (the folder itself is not committed).
   e. Photo list: `python3 pipeline/photo_list.py <chid>` writes `pipeline/sales/<chid>/photo_list.md`
      and prints the email (first line is the subject): send it to andyfist@gmail.com.
      Then `python3 pipeline/stage.py <chid> photo_list` (no email needed for that one).
   f. Commit the sale's files (photos, sheets, crops and per-lot files are ignored by git)
      and the state: `git add pipeline/sales/<chid> pipeline/state/sales.json && git commit -m "Armitage <chid>: funnel" && git push origin main`.
6. Bidder scan. Do this on the 7:23 and 17:23 runs, and on every run on a day when lots
   of the catalogue close. It applies to each catalogue in `current` whose `researched`
   stage is done (see `pipeline/state/sales.json`) and whose last lot has not closed yet.
   a. `python3 pipeline/bidders.py <chid> --refresh` re-reads the lot pages (about 8 minutes
      per 1,800 lots), rebuilds the bidder history, and prints the "bidder scan" email
      (first line is the subject). It writes `pipeline/sales/<chid>/wfargs_bidders.json`
      only when flagged lots have not been valued yet.
   b. If `wfargs_bidders.json` exists, run the Workflow tool with the script file
      `pipeline/wf_funnel.js` and that file's JSON as `args` (Andy has opted in to this
      multi-agent run through this routine; it scans and researches just those lots). Then
      `python3 pipeline/assess.py <chid>` and `python3 pipeline/bidders.py <chid>` again
      (no `--refresh`) so the email carries the fresh values.
   c. Email the bidder scan output to andyfist@gmail.com when it lists at least one lot;
      then `python3 pipeline/stage.py <chid> bidders --note "<n> lots flagged"` (no email).
   d. Commit: `git add pipeline/sales/<chid> pipeline/state && git commit -m "Armitage <chid>: bidders" && git push origin main`.
7. Morning email. On the 7:23 run of a day when lots of the catalogue close, after the
   bidder scan: `python3 pipeline/morning.py <chid>` prints the email (first line is the
   subject) with every closing time that matters; send it to andyfist@gmail.com, then
   `python3 pipeline/stage.py <chid> morning_email` and commit the state as in 6d.
8. Post-sale review. For each catalogue in `pipeline/state/sales.json` whose last lot has
   closed (its `close_last` is in the past) and whose `reviewed` stage is not done, once
   `pipeline/armitage_results.py` exists: run `python3 pipeline/armitage_results.py --chid <chid>`
   (its closing bids and bid histories go into `databases/armitage.json`), then
   `python3 pipeline/review.py <chid>` and email its output to andyfist@gmail.com (first
   line is the subject). Then `python3 pipeline/stage.py <chid> reviewed` and commit:
   `git add pipeline/sales/<chid> pipeline/state databases/armitage.json && git commit -m "Armitage <chid>: review" && git push origin main`.
9. Reply in one short line: catalogues on the site, new ones found, emails sent, funnel
   stages run, anything that failed. Commit nothing else and send no other email.
