#!/usr/bin/env python3
"""Pull new Facebook Marketplace listings around Launceston via Apify.

Uses blackfalcondata/facebook-marketplace-scraper (no Facebook login), which has its
own incremental mode and a strict radius. Measured cost (Oct 2026): about US$0.03 per
run plus US$0.003 per listing, so --max 100 is roughly US$0.35.

Every run is capped by Apify at --max-spend (default US$0.50) so a bad input can't run
up a bill. The cap is a backstop, not a budget: Apify aborts the run when it is reached,
an aborted run returns NO listings, and it still bills a few cents over the cap. So keep
--max-spend well above the expected cost of the run, and use --max to control cost.

Two scan modes, each with its own incremental state (--state) so they don't hide new
listings from each other:
  quick: --no-details --state armitage-7250-newest. Title, price, location, one photo,
      link, newest first and only the first dozen per query. About US$0.01-0.03 per
      run once the baseline exists, so it can run hourly.
  full:  the default. Descriptions and galleries, but the actor fetches every detail
      page before it filters, so a run costs about US$0.45 even when nothing is new.

    python3 scraper/marketplace.py --no-details --state armitage-7250-newest -o data/fb_quick.json --max-spend 0.10
    python3 scraper/marketplace.py --lookup "The Shannon Rise by R.H. Wigram" -o data/fb_lookup.json --photos data/fb_photos

The usual pattern is quick scan, shortlist on title and photo, then --lookup (about
US$0.02 a title) for the gallery and description of each candidate.

Apify's official apify/facebook-marketplace-scraper is deliberately not supported: a
20-listing test run returned 403 US listings for US$5.00, because its limit applies
per search URL, it ignores the city in the URL, and it charges ~US$0.0124 per listing.
Auth: APIFY_TOKEN from the environment, sent as a Bearer header. If it isn't set,
requests go out without one, for when the environment adds the token itself as a
network secret for api.apify.com.

    python3 scraper/marketplace.py -o data/fb.json
    python3 scraper/marketplace.py -o data/fb.json --photos data/fb_photos   # also download photos
    python3 scraper/marketplace.py -o data/fb.json --max 20 --no-incremental  # small test run
"""
import argparse
import json
import os
import sys
import time

import requests

API = "https://api.apify.com/v2"
ACTOR = "blackfalcondata~facebook-marketplace-scraper"
DEFAULT_MAX_SPEND = 0.50  # US$ per run, enforced by Apify
RUN_TIMEOUT_SECS = 1800  # Apify kills the run after this
LAUNCESTON = (-41.4332, 147.1441)  # 7250
RADIUS_KM = 100
# Without listing details the actor can't measure distance, so Facebook's loose
# radius lets these through. Dropped by city name in --no-details runs.
FAR_CITIES = {
    "Hobart", "Kingston", "Sorell", "Margate", "Glenorchy", "Clarence", "Huonville",
    "New Norfolk", "Brighton", "Swansea", "Somerset", "Waratah", "Flowerdale", "Burnie",
    "Wynyard", "Smithton", "Queenstown", "Strahan", "Rosebery", "Zeehan",
}

# Broad on purpose: bargains are mislabelled, so search for the way sellers
# describe clear-outs, not the brand names a dealer would search for. Books come
# first because they're the likeliest source of unrecognised value, and because a
# --max test run only gets through the first few queries.
QUERIES = [
    "old books", "books", "box of books", "book collection", "antique books", "rare books",
    "antique", "vintage", "watch", "pocket watch", "old watch",
    "deceased estate", "estate", "clearing out", "garage sale", "box of",
    "collectables", "jewellery", "gold", "silver", "coins",
    "stamps", "pottery", "painting", "first edition",
    # Dropped: "militaria" (Facebook returns clothing) and "collection" ("collection
    # from Hadspen" in clothing ads). Both cost per listing and never matched a real item.
]


def call_actor(token, payload, max_spend):
    """Start the actor, wait for it to finish, return its dataset items.

    Runs asynchronously rather than via run-sync-get-dataset-items, which cuts the
    run off (and still bills it) after 300 s; a full run of 22 queries takes longer.
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.post(
        f"{API}/acts/{ACTOR}/runs",
        # Apify aborts the run once it has charged maxTotalChargeUsd.
        params={"maxTotalChargeUsd": max_spend, "timeout": RUN_TIMEOUT_SECS},
        headers=headers,
        json=payload,
        timeout=60,
    )
    if r.status_code in (401, 402) and not token:
        sys.exit("Apify refused an unauthenticated request; no APIFY_TOKEN or network secret reached it.")
    if r.status_code == 401:
        sys.exit("Apify rejected the request (401): token missing or wrong. "
                 "Set APIFY_TOKEN or a network secret for api.apify.com.")
    if not r.ok:
        sys.exit(f"Apify refused the run ({r.status_code}): {r.text[:500]}")
    run_id = r.json()["data"]["id"]
    print(f"Apify run {run_id} started (cap US${max_spend:.2f}); "
          f"if this script dies, collect it with --run {run_id}", file=sys.stderr)
    return collect_run(token, run_id)


def collect_run(token, run_id):
    """Wait for an Apify run to finish and return its dataset items."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    run = {"status": "RUNNING"}
    failures = 0
    while run["status"] in ("READY", "RUNNING"):
        # Short waits: a connection held open for long gets cut by proxies.
        try:
            r = requests.get(f"{API}/actor-runs/{run_id}", params={"waitForFinish": 20},
                             headers=headers, timeout=45)
            r.raise_for_status()
        except requests.RequestException as e:
            failures += 1
            if failures > 10:
                sys.exit(f"Lost contact with Apify while polling run {run_id}: {e}. "
                         f"The run may still finish; collect it with --run {run_id}")
            time.sleep(10)
            continue
        failures = 0
        run = r.json()["data"]
    r = requests.get(f"{API}/datasets/{run['defaultDatasetId']}/items",
                     params={"clean": "true"}, headers=headers, timeout=120)
    r.raise_for_status()
    items = r.json()
    # Apify keeps posting charges for a minute or so after the run ends.
    print(f"Apify run {run['id']}: {run['status']}, {len(items)} items, "
          f"US${run.get('usageTotalUsd') or 0:.3f} so far", file=sys.stderr)
    if run["status"] != "SUCCEEDED":
        msg = run.get("statusMessage") or run["status"]
        if not items:
            sys.exit(f"Apify run returned nothing: {msg}")
        print(f"warning: {msg}; keeping the {len(items)} listings it returned", file=sys.stderr)
    return items


def run(token, queries, max_results, incremental, max_spend, days=None, details=True,
        state="armitage-launceston-7250", radius=RADIUS_KM, strict=True, sort="newest"):
    payload = {
        "latitude": LAUNCESTON[0],
        "longitude": LAUNCESTON[1],
        "radiusKm": radius,
        "strictRadius": strict,
        "includeDetails": details,
        "maxResults": max_results,
        "incrementalMode": incremental,
        "excludeEmptyFields": True,
    }
    if details:
        payload["query"] = json.dumps(queries)
        payload["sortBy"] = sort  # newest: the actor sorts by the post date it fetched
    else:
        # Quick mode: the actor can't sort by newest without detail pages, but
        # Facebook can. Give it Facebook's own search URLs, newest first, and take
        # only the first dozen per query: that's every listing posted in the last
        # hour or so, for a cent or two. Without a cap it would catalogue every
        # listing for every query, which costs more than the run is worth.
        payload["startUrls"] = [
            "https://www.facebook.com/marketplace/launceston/search/?"
            + requests.compat.urlencode({"query": q, "sortBy": "creation_time_descend",
                                         "daysSinceListed": days or 1})
            for q in queries]
        payload["maxResults"] = max_results or 12 * len(queries)
    if incremental:
        payload["stateKey"] = state
    if days and details:
        payload["daysSinceListed"] = days
    return call_actor(token, payload, max_spend)


def lookup(token, titles, max_spend):
    """Full details (gallery, description, post date) for listings found by a quick
    scan: search for each exact title with details on. About US$0.02 per title."""
    # No radius limit (the quick scan already found it, wherever it is) and best
    # match first, so the listing with that exact title comes top. Pass the whole
    # title: a fragment of a common phrase can miss.
    items = run(token, titles, 10 * len(titles), False, max_spend, details=True,
                radius=500, strict=False, sort="relevance")
    wanted = [t.strip().lower() for t in titles]
    return [i for i in items
            if any(w in (first(i, "title") or "").lower() for w in wanted)]


def first(item, *keys):
    """First non-empty value among dotted key paths."""
    for key in keys:
        v = item
        for part in key.split("."):
            v = v.get(part) if isinstance(v, dict) else None
        if v not in (None, "", []):
            return v
    return None


def normalise(item):
    photos = first(item, "galleryUrls", "listing_photos", "photos") or []
    photos = [p if isinstance(p, str) else first(p, "image.uri", "uri", "url") for p in photos]
    if not photos:
        one = first(item, "imageUrl", "primary_listing_photo.image.uri", "primary_listing_photo.photo_image_url")
        photos = [one] if one else []
    return {
        "source": "facebook",
        "id": first(item, "id", "listingId"),
        "title": first(item, "title", "marketplace_listing_title", "custom_title") or "",
        "price": first(item, "priceValue", "listing_price.amount"),
        "price_text": first(item, "priceText", "listing_price.formatted_amount"),
        "location": first(item, "locationText", "location.reverse_geocode.city", "location"),
        "published": first(item, "publishedAt", "creation_time"),
        "change": item.get("changeType"),
        "description": first(item, "description", "redacted_description.text") or "",
        "url": first(item, "url", "listingUrl"),
        "photos": [p for p in photos if p],
        "raw": item,
    }


def download_photos(listings, out_dir):
    for l in listings:
        d = os.path.join(out_dir, str(l["id"]))
        os.makedirs(d, exist_ok=True)
        for i, url in enumerate(l["photos"][:6], 1):
            try:
                r = requests.get(url, timeout=60)
                r.raise_for_status()
            except requests.RequestException as e:
                print(f"photo failed {l['id']} #{i}: {e}", file=sys.stderr)
                continue  # don't leave an empty file behind
            with open(os.path.join(d, f"{i}.jpg"), "wb") as f:
                f.write(r.content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="data/fb.json")
    ap.add_argument("--max", type=int, default=0, help="max listings (0 = all available)")
    ap.add_argument("--no-incremental", action="store_true")
    ap.add_argument("--photos", help="directory to download listing photos into")
    ap.add_argument("--max-spend", type=float, default=DEFAULT_MAX_SPEND,
                    help=f"US$ cap on the Apify run (default {DEFAULT_MAX_SPEND})")
    ap.add_argument("--run", metavar="RUN_ID",
                    help="don't start a run; collect this existing Apify run's results")
    ap.add_argument("--days", type=int, help="only listings posted in the last N days")
    ap.add_argument("--no-details", action="store_true",
                    help="skip listing detail pages (no description or gallery; cheaper)")
    ap.add_argument("--state", default="armitage-launceston-7250",
                    help="incremental-mode state key; use a different one per scan type")
    ap.add_argument("--lookup", metavar="TITLE", action="append",
                    help="no scan; fetch full details for listings with this title (repeatable)")
    args = ap.parse_args()

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print("APIFY_TOKEN not set; relying on a network secret for api.apify.com", file=sys.stderr)

    if args.run:
        items = collect_run(token, args.run)
    elif args.lookup:
        items = lookup(token, args.lookup, args.max_spend)
    else:
        items = run(token, QUERIES, args.max, not args.no_incremental, args.max_spend,
                    days=args.days, details=not args.no_details, state=args.state)
    listings = [normalise(i) for i in items]
    if args.no_details:
        before = len(listings)
        listings = [l for l in listings
                    if l["raw"].get("state", "TAS") == "TAS"
                    and l["raw"].get("city") not in FAR_CITIES]
        if before != len(listings):
            print(f"dropped {before - len(listings)} listings outside the area", file=sys.stderr)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(listings, f, indent=1)
    print(f"{len(listings)} listings -> {args.out}", file=sys.stderr)
    if args.photos:
        download_photos(listings, args.photos)


if __name__ == "__main__":
    main()
