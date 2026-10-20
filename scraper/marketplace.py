#!/usr/bin/env python3
"""Pull new Facebook Marketplace listings around Launceston via Apify.

Uses the blackfalcondata/facebook-marketplace-scraper actor (no Facebook login).
Incremental mode means each run only returns listings that are new or changed
since the previous run. Needs APIFY_TOKEN in the environment.

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
LAUNCESTON = (-41.4332, 147.1441)  # 7250

# Broad on purpose: bargains are mislabelled, so search for the way sellers
# describe clear-outs, not the brand names a dealer would search for.
QUERIES = [
    "old books", "antique", "vintage", "watch", "pocket watch", "old watch",
    "deceased estate", "estate", "clearing out", "garage sale", "box of",
    "collectables", "collection", "jewellery", "gold", "silver", "coins",
    "stamps", "pottery", "painting", "first edition", "militaria",
]


def run(token, queries, max_results, incremental):
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
    r = requests.post(
        f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items",
        params={"token": token, "timeout": 290},
        json=payload,
        timeout=310,
    )
    r.raise_for_status()
    return r.json()


def normalise(item):
    photos = item.get("galleryUrls") or ([item["imageUrl"]] if item.get("imageUrl") else [])
    return {
        "source": "facebook",
        "id": item.get("id") or item.get("listingId"),
        "title": item.get("title", ""),
        "price": item.get("priceValue"),
        "price_text": item.get("priceText"),
        "location": item.get("location") or item.get("locationText"),
        "published": item.get("publishedAt"),
        "change": item.get("changeType"),
        "description": item.get("description", ""),
        "url": item.get("url") or item.get("listingUrl"),
        "photos": photos,
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
    args = ap.parse_args()

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("APIFY_TOKEN is not set; add it to the environment's secrets")

    listings = [normalise(i) for i in run(token, QUERIES, args.max, not args.no_incremental)]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(listings, f, indent=1)
    print(f"{len(listings)} listings -> {args.out}", file=sys.stderr)
    if args.photos:
        download_photos(listings, args.photos)


if __name__ == "__main__":
    main()
