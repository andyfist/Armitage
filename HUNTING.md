# Hunt procedure (for Claude)

Goal: flag lots where **likely resale − (hammer × 1.22) ≥ $500**. Armitage's
buyer's premium is 20% + GST, so 22% in total. Pickup only, from 9 Goodman Crt, Invermay.

1. `python3 scraper/armitage.py -o data/lots.json`
2. **Title pass.** Read every title, not just keyword hits. Shortlist anything where a
   $500 gap is plausible:
   - **Books first.** Unrecognised value is most likely here: sellers and auction houses
     rarely know what they have. Early Australiana, explorers' journals, Tasmanian unit
     histories, Gould, limited editions, signed copies, and any boxed or bulk lot whose
     photos show cloth or leather spines. Shortlist every book lot that is vague.
   - Watches: Rolex, Tudor, Omega, Longines, gold cases, pocket watches.
   - Precious metal: gold or silver by weight. Melt = grams × purity × spot (9ct is 0.375, 18ct is 0.75).
   - Designer goods, Tasmanian studio pottery (John Campbell, McLaren), colonial furniture,
     listed Tasmanian artists, coins, militaria.
   - Anything where the lot's **estimate is far below** what the description implies.
3. **Photo pass.** Run `fetch_photos.py` on the shortlist and look at every photo. Check
   dial and case details, title pages and imprint dates, hallmarks, maker's marks, and
   the boxes and cards that come with designer goods. Reject reprints, facsimiles and
   decorative copies.
4. **Price check.** Use web search for sold or dealer prices. Be conservative: use the
   price you could sell at, not retail.
5. **Report.** Write `reports/<close-date>.md`. For each hit, give the lot, link, close
   time, current bid, estimate, evidence from the photos, value range, a **max bid**
   (the hammer price that still leaves $500), risks, and what to ask the auction house
   or check at viewing.

## Facebook Marketplace

Two scans, both covering 100 km around Launceston (`RADIUS_KM` in the script), so
Devonport, Scottsdale and St Helens are in and Hobart is out. Each returns only
listings new or changed since its own last run.

- **Quick scan (hourly):** `python3 scraper/marketplace.py --no-details --state
  armitage-7250-quick -o data/fb_quick.json --photos data/fb_photos --max-spend 0.10`.
  Title, price, suburb, one photo and the link; no description. About US$0.02 a run.
  Shortlist on the title and that one photo: every book lot, anything vague, anything
  that could plausibly clear $500.
- **Lookup (for each shortlisted listing):** `python3 scraper/marketplace.py --lookup
  "<exact title>" -o data/fb_lookup.json --photos data/fb_photos`. Fetches the whole
  gallery, the description and the post date for that listing, about US$0.02 a title
  (several `--lookup` flags can go in one run). Judge the candidate on this: spines,
  title pages, hallmarks, dial, what the seller actually says. Then price-check and
  alert on a hit.
- **Full scan (on demand only):** `python3 scraper/marketplace.py -o data/fb.json
  --photos data/fb_photos --max-spend 0.75`. Details for everything new. About US$0.45
  a run whatever it finds, because the actor fetches every detail page, so there is
  rarely a reason to prefer it over quick scan plus lookups.

Apify aborts a run at `--max-spend`; an aborted run returns nothing but still bills, so
if that happens use `--max` to take fewer listings rather than retrying. Don't start two
runs with the same `--state` at once: the second exits with "Another run holds the
state lock" and returns nothing. The threshold is the
same: resale minus the asking price must be at least $500, with no buyer's premium.
Mislabelled listings are where the bargains are ("old watch, no idea", "box of books"),
so look at the photos of anything vague rather than trusting the title. Open every
book listing's photos and read the spines; a $3-each paperback pile can hide one
title worth the threshold on its own. Speed matters,
so put hits in the alert email straight away, each with the listing link and the one
question to ask the seller.
