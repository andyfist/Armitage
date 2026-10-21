#!/usr/bin/env python3
"""Pull new Facebook Marketplace listings around Launceston via Apify.

Two Apify actors are supported (neither uses a Facebook login):
  blackfalcon (default): blackfalcondata/facebook-marketplace-scraper. Has its own
      incremental mode and a strict radius, about US$0.0009 per listing.
  apify: Apify's official apify/facebook-marketplace-scraper. More widely used but
      about US$0.0062 per listing and no incremental mode, so we de-duplicate locally
      (data/fb_seen.json) and keep the per-search limit low.
Auth: APIFY_TOKEN from the environment, sent as a Bearer header. If it isn't set,
requests go out without one, for when the environment adds the token itself as a
network secret for api.apify.com.

    python3 scraper/marketplace.py -o data/fb.json
    python3 scraper/marketplace.py -o data/fb.json --photos data/fb_photos   # also download photos
    python3 scraper/marketplace.py -o data/fb.json --max 20 --no-incremental  # small test run
    python3 scraper/marketplace.py -o data/fb.json --actor apify --max 10      # Apify's official actor
"""
import argparse
import json
import os
import sys

import requests

ACTORS = {
    "blackfalcon": "blackfalcondata~facebook-marketplace-scraper",
    "apify": "apify~facebook-marketplace-scraper",
}
SEEN_FILE = "data/fb_seen.json"
LAUNCESTON = (-41.4332, 147.1441)  # 7250

# Broad on purpose: bargains are mislabelled, so search for the way sellers
# describe clear-outs, not the brand names a dealer would search for.
QUERIES = [
    "old books", "antique", "vintage", "watch", "pocket watch", "old watch",
    "deceased estate", "estate", "clearing out", "garage sale", "box of",
    "collectables", "collection", "jewellery", "gold", "silver", "coins",
    "stamps", "pottery", "painting", "first edition", "militaria",
]


def call_actor(token, actor, payload):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.post(
        f"https://api.apify.com/v2/acts/{ACTORS[actor]}/run-sync-get-dataset-items",
        params={"timeout": 290},
        headers=headers,
        json=payload,
        timeout=310,
    )
    if r.status_code in (401, 402) and not token:
        sys.exit("Apify refused an unauthenticated request; no APIFY_TOKEN or network secret reached it.")
    if r.status_code == 401:
        sys.exit("Apify rejected the request (401): token missing or wrong. "
                 "Set APIFY_TOKEN or a network secret for api.apify.com.")
    r.raise_for_status()
    return r.json()


def run_apify(token, queries, max_results):
    # Facebook's own search URLs, newest first, listed in the last day. The city
    # slug sets the area; Facebook's default radius for it is used.
    urls = [{"url": "https://www.facebook.com/marketplace/launceston/search/?"
                    + requests.compat.urlencode({"query": q, "sortBy": "creation_time_descend",
                                                 "daysSinceListed": 1})}
            for q in queries]
    return call_actor(token, "apify", {
        "startUrls": urls,
        "resultsLimit": max_results or 20,
        "includeListingDetails": True,
    })


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
    return call_actor(token, "blackfalcon", payload)


def first(item, *keys):
    """First non-empty value among dotted key paths (the two actors name fields differently)."""
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
    ap.add_argument("--actor", choices=ACTORS, default="blackfalcon")
    args = ap.parse_args()

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print("APIFY_TOKEN not set; relying on a network secret for api.apify.com", file=sys.stderr)

    if args.actor == "apify":
        listings = [normalise(i) for i in run_apify(token, QUERIES, args.max)]
        seen = set(json.load(open(SEEN_FILE))) if os.path.exists(SEEN_FILE) else set()
        listings = [l for l in listings if l["id"] and str(l["id"]) not in seen]
        os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
        with open(SEEN_FILE, "w") as f:
            json.dump(sorted(seen | {str(l["id"]) for l in listings}), f)
    else:
        listings = [normalise(i) for i in run(token, QUERIES, args.max, not args.no_incremental)]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(listings, f, indent=1)
    print(f"{len(listings)} listings -> {args.out}", file=sys.stderr)
    if args.photos:
        download_photos(listings, args.photos)


if __name__ == "__main__":
    main()
