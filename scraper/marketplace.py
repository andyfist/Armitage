#!/usr/bin/env python3
"""Pull new Facebook Marketplace listings around Launceston via Apify.

Uses blackfalcondata/facebook-marketplace-scraper (no Facebook login), which has its
own incremental mode and a strict radius, about US$0.0009 per listing. Every run is
capped by Apify at --max-spend (default US$0.50) so a bad input can't run up a bill.

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

import requests

ACTOR = "blackfalcondata~facebook-marketplace-scraper"
DEFAULT_MAX_SPEND = 0.50  # US$ per run, enforced by Apify
LAUNCESTON = (-41.4332, 147.1441)  # 7250

# Broad on purpose: bargains are mislabelled, so search for the way sellers
# describe clear-outs, not the brand names a dealer would search for.
QUERIES = [
    "old books", "antique", "vintage", "watch", "pocket watch", "old watch",
    "deceased estate", "estate", "clearing out", "garage sale", "box of",
    "collectables", "collection", "jewellery", "gold", "silver", "coins",
    "stamps", "pottery", "painting", "first edition", "militaria",
]


def call_actor(token, payload, max_spend):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.post(
        f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items",
        # Apify stops the run once it has charged this much.
        params={"timeout": 290, "maxTotalChargeUsd": max_spend},
        headers=headers,
        json=payload,
        timeout=310,
    )
    if r.status_code in (401, 402) and not token:
        sys.exit("Apify refused an unauthenticated request; no APIFY_TOKEN or network secret reached it.")
    if r.status_code == 401:
        sys.exit("Apify rejected the request (401): token missing or wrong. "
                 "Set APIFY_TOKEN or a network secret for api.apify.com.")
    if r.status_code == 403:
        sys.exit(f"Apify refused the run (403): {r.text[:300]}")
    r.raise_for_status()
    return r.json()


def run(token, queries, max_results, incremental, max_spend):
    payload = {
        "query": json.dumps(queries),
        "latitude": LAUNCESTON[0],
        "longitude": LAUNCESTON[1],
        "radiusKm": 50,
        "strictRadius": True,
        "sortBy": "newest",
        "includeDetails": True,
        "maxResults": max_results,
        "incrementalMode": incremental,
        "stateKey": "armitage-launceston-7250",
        "excludeEmptyFields": True,
    }
    return call_actor(token, payload, max_spend)


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
                with open(os.path.join(d, f"{i}.jpg"), "wb") as f:
                    f.write(requests.get(url, timeout=60).content)
            except requests.RequestException as e:
                print(f"photo failed {l['id']} #{i}: {e}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="data/fb.json")
    ap.add_argument("--max", type=int, default=0, help="max listings (0 = all available)")
    ap.add_argument("--no-incremental", action="store_true")
    ap.add_argument("--photos", help="directory to download listing photos into")
    ap.add_argument("--max-spend", type=float, default=DEFAULT_MAX_SPEND,
                    help=f"US$ cap on the Apify run (default {DEFAULT_MAX_SPEND})")
    args = ap.parse_args()

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print("APIFY_TOKEN not set; relying on a network secret for api.apify.com", file=sys.stderr)

    listings = [normalise(i) for i in
                run(token, QUERIES, args.max, not args.no_incremental, args.max_spend)]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(listings, f, indent=1)
    print(f"{len(listings)} listings -> {args.out}", file=sys.stderr)
    if args.photos:
        download_photos(listings, args.photos)


if __name__ == "__main__":
    main()
