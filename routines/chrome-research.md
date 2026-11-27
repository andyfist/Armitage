# Routine: import the Chrome results for an Armitage sale

Since 27 Nov 2026 (Andy) every Armitage lot is priced in Chrome on Andy's PC, from the
one combined prompt in a Chrome pack (`pipeline/chrome_brief.py`, made by the new-sale
check). That chat runs on Andy's PC in Claude Desktop with Claude in Chrome: the main
chat on Opus 5.5, Opus helpers for books, art and flagged lots, Sonnet helpers for the
rest. It writes `results_<pack name>/` (one `<chunk>.json` per 5 lots) and zips it.

Start: Andy says "import the Chrome results" in the Auction scans project (or uploads
the zip). Needs: repo andyfist/armitage (`main`), Andy's PC folder
`C:\Users\Andy\Documents\claude` (approved), Gmail.

## Prompt

1. `git fetch origin main && git checkout main && git pull --ff-only origin main`.
2. Get the results: the zip Andy uploaded, or stage
   `C:\Users\Andy\Documents\claude\<pack name>\results_<pack name>.zip` (or the files in the
   `results_<pack name>` folder, if the run is not finished) from his PC. A part-done run can
   be imported; importing again later adds nothing twice.
3. Copy it into the repo as `pipeline/sales/packs/results_<pack name>.zip`, then for each
   catalogue in the pack (the chids in its name):
   `python3 pipeline/chrome_import.py <chid> pipeline/sales/packs/results_<pack name>.zip`,
   then `python3 pipeline/assess.py <chid>` and `python3 pipeline/photo_list.py <chid>`.
4. Check the maximums by hand before sending (program maximums are rough): every max
   needs a dated same-item SOLD link that is not Armitage or Gowans; never drop a lot
   because its bid is above the max (mark it "bid past max").
5. Commit and push: `git add pipeline/sales pipeline/state && git commit -m "Armitage <pack name>: Chrome results" && git push origin main`
   (if the push is rejected, `git pull --rebase origin main` and push again).
6. Email andyfist@gmail.com the assess.py output per catalogue, subject
   "Armitage <name>: Chrome check done, <PASS> lots pass the $200 rule", and the
   photo_list.py output if the photo list changed (its first line is the subject).
