# Hunt procedure (for Claude)

Goal: flag lots where **likely resale − (hammer × 1.22) ≥ $1,000**. Armitage's
buyer's premium is 20% + GST, so 22% in total. Pickup only, from 9 Goodman Crt, Invermay.

1. `python3 scraper/armitage.py -o data/lots.json`
2. **Title pass.** Read every title, not just keyword hits. Shortlist anything where a
   $1k gap is plausible:
   - Watches: Rolex, Tudor, Omega, Longines, gold cases, pocket watches.
   - Books: early Australiana, explorers' journals, Tasmanian unit histories, Gould, limited editions.
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
   (the hammer price that still leaves $1k), risks, and what to ask the auction house
   or check at viewing.
