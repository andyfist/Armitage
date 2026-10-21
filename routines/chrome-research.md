# Routine: Chrome price research for one sale

Start: Andy starts a new chat in the Auction scans project on the home computer, with
Claude in Chrome connected, saying "Chrome research for Armitage <chid>, use Sonnet".
The model is Andy's call at the start of the chat: he wants this run on Sonnet or
something cheap (the work is searching and reading, not reasoning), and a chat only
switches model when he says so in his own words, not because this file says so.
Needs: repo andyfist/armitage (`main`), Claude in Chrome on Andy's computer (his own
signed-in eBay, LiveAuctioneers, Invaluable and whatever else he has accounts for), Gmail.

The cloud research (pipeline/wf_funnel.js) finds what it can on the open web. This
stage uses Andy's signed-in browser to get what the cloud cannot: eBay sold prices (Terapeak in Seller Hub first, which looks back furthest, then plain sold listings) and
auction results behind a login. It is the last word on a lot's value, and a maximum bid
is final only after it.

## Prompt

You are doing the Chrome price research for Armitage sale <chid>. First run
`git fetch origin main && git checkout main && git pull --ff-only origin main`. The brief
is `pipeline/sales/<chid>/chrome_brief.md`: read it in full and follow its rules exactly
(read-only; record only prices you can see on the page; SOLD, UNSOLD and ASKING kept
apart; same item only; the listing URL, never a search page; at most 6 searches a lot).

1. Load the Claude in Chrome tools, look at Andy's open tabs and work in a new tab. If
   the extension is not connected, say so in one line and stop.
2. Work through the lots in the brief's order, best prospects first. It is fine for this
   to run for hours. If a site starts showing robot checks, slow down on that site and
   move to the next lot. After every 10 lots, write what you have so far to
   `/mnt/project-files/armitage/<chid>/chrome_results_<chid>.json` (the JSON list the
   brief describes) so nothing is lost if the chat stops.
3. When the list is done, or Andy says stop: copy the file into the repo as
   `pipeline/sales/<chid>/chrome_results_<chid>.json`, then run
   `python3 pipeline/chrome_import.py <chid> pipeline/sales/<chid>/chrome_results_<chid>.json`,
   `python3 pipeline/assess.py <chid>` and `python3 pipeline/photo_list.py <chid>`.
   Commit and push: `git add pipeline/sales/<chid> pipeline/state && git commit -m "Armitage <chid>: Chrome research" && git push origin main`
   (if the push is rejected, `git pull --rebase origin main` and push again).
4. Email andyfist@gmail.com the output of assess.py, subject
   "Armitage <name>: Chrome research done, <PASS> lots pass the $200 rule". If the
   photo list changed, send the photo_list.py output as a second email (its first line is
   the subject).
5. Reply in one short line: lots done, lots with a SOLD price found, lots with nothing
   found, lots skipped and why. Commit nothing else and send no other email.
