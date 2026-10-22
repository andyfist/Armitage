# Routine: rehearsal of the whole pipeline on a closed sale

Run by hand (a thread on the "Full web access" environment), not on a schedule. It runs
every stage on a sale that has already closed, exactly as the scheduled run would on a
live one, and ends with the post-sale review against the real hammer prices and bidders.
Its point is to find bugs and misses before a sale that matters.
Needs: repo andyfist/armitage (`main`), Gmail, the Workflow tool.

## Prompt

You are rehearsing the Armitage pipeline on the closed catalogues <chids> (one sale can
be several catalogues; do them one at a time, in order). First run
`git fetch origin main && git checkout main && git pull --ff-only origin main`.
Every email below goes to andyfist@gmail.com with "[Rehearsal] " in front of the subject,
so Andy sees each email exactly as the live run would send it. Everything is read-only
against Armitage.

For each catalogue <chid>:
1. `python3 pipeline/prep.py <chid>` (the lot pages and photos are still online after a
   sale closes). Then `python3 pipeline/stage.py <chid> prepped --note "<summary>"` and
   email its output.
2. Run the Workflow tool with the script file `pipeline/wf_funnel.js` and, as `args`, the
   JSON in `pipeline/sales/<chid>/wfargs.json` (Andy has opted in to this multi-agent run
   through this rehearsal). Save the result to `pipeline/sales/<chid>/funnel_result.json`,
   then `python3 pipeline/stage.py <chid> scanned --note "<counts>"` and email it.
3. `python3 pipeline/assess.py <chid> --ignore-bids` (the sale is closed, so the bids on
   the site are the final prices; `--ignore-bids` judges the rule on the evidence alone,
   as it would have been judged when the sale opened). Email its output with subject
   "Armitage <name>: first pass, <PASS> lots pass the $200 rule", then
   `python3 pipeline/stage.py <chid> researched`.
4. `python3 pipeline/chrome_brief.py <chid>`, then
   `python3 pipeline/stage.py <chid> chrome_list --note "<n> lots to research in Chrome" --body pipeline/sales/<chid>/chrome_email.txt`
   and email it. `python3 pipeline/photo_list.py <chid>`: email its output, then
   `python3 pipeline/stage.py <chid> photo_list`.
5. `python3 pipeline/bidders.py <chid>` (no `--refresh`: prep already saved the full bid
   histories). If it writes `pipeline/sales/<chid>/wfargs_bidders.json`, run the Workflow
   tool again with `pipeline/wf_funnel.js` and that file as `args`, then
   `python3 pipeline/assess.py <chid> --ignore-bids` and `python3 pipeline/bidders.py <chid>`
   again. Email the bidder scan output, then `python3 pipeline/stage.py <chid> bidders`.
6. `python3 pipeline/morning.py <chid> --date <the day the lots closed, d/m/yyyy>`: email it,
   then `python3 pipeline/stage.py <chid> morning_email`.
7. `python3 pipeline/armitage_results.py --chid <chid>` (skips what the overnight scrape
   already saved), then `python3 pipeline/review.py <chid>`: email its output, then
   `python3 pipeline/stage.py <chid> reviewed`.
8. Commit: `git add pipeline/sales/<chid> pipeline/state databases/armitage.json && git commit -m "Rehearsal: Armitage <chid>" && git push origin main`
   (if rejected, `git pull --rebase origin main` and push again).

If a stage fails, fix what is clearly a bug in the pipeline scripts on a branch, open a
pull request for it, and carry on with the next stage or catalogue using the fixed
script; say in the final reply exactly what broke. Reply at the end with one line per
catalogue (lots, scanned, candidates, passes, Chrome list, flagged by bidders, misses in
the review) and the pull requests opened.
