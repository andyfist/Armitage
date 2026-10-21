#!/usr/bin/env python3
"""Pull every open lot from Armitage Auctions (armitage.bidsonline.com.au).

Writes a JSON list of lots (lot number, title, current bid, bid count, close
time, photo URLs) so the triage step can work from one file.

    python3 scraper/armitage.py -o data/lots.json
    python3 scraper/armitage.py -o data/lots.json --details   # also fetch descriptions + all photos
"""
import argparse
import html
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

BASE = "https://armitage.bidsonline.com.au/"
HEADERS = {"User-Agent": "Mozilla/5.0 (personal auction watchlist; low volume)"}

session = requests.Session()
session.headers.update(HEADERS)


def get(path):
    for attempt in range(3):
        try:
            r = session.get(BASE + path, timeout=60)
            r.raise_for_status()
            return r.text
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def clean(fragment):
    text = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def catalogue_ids():
    page = get("default.aspx")
    return sorted(set(re.findall(r"catalogue-group\.aspx\?chid=(\d+)", page)))


def catalogue_name(page):
    m = re.search(r"<title>(.*?)</title>", page, re.S)
    return clean(m.group(1)) if m else ""


LOT_RE = re.compile(
    r"images/products/thumbnails/(?P<pid>\d+)_th\.jpg.*?"
    r'<td valign="top" align="center">(?P<lot>[^<]*)</td>.*?'
    r'class="link" href="catalogue_detail\.aspx\?cdid=(?P<cdid>\d+)[^"]*">[^<]*</a>\s*<br />(?P<title>.*?)</td>.*?'
    r'id="NumBids_\d+">(?P<bids>\d*)</div>.*?'
    r'id="CurrentBid_\d+" class="currentbid">(?P<bid>.*?)</td>.*?'
    r'id="timelabel_\d+" class="Countdown" >(?P<closes>[^<]*)</div>',
    re.S,
)


def parse_bid(fragment):
    m = re.search(r"\$([\d,]+(?:\.\d+)?)", fragment)
    return float(m.group(1).replace(",", "")) if m else 0.0


def lots_in(chid):
    page = get(f"catalogue.aspx?chid={chid}")
    name = catalogue_name(page)
    lots = []
    for m in LOT_RE.finditer(page):
        pid, cdid = m["pid"], m["cdid"]
        lots.append({
            "catalogue": name,
            "chid": chid,
            "cdid": cdid,
            "lot": m["lot"].strip(),
            "title": clean(m["title"]),
            "bids": int(m["bids"] or 0),
            "current_bid": parse_bid(m["bid"]),
            "closes": m["closes"].strip(),
            "url": f"{BASE}catalogue_detail.aspx?cdid={cdid}&chid={chid}",
            "thumb": f"{BASE}images/products/thumbnails/{pid}_th.jpg",
            "photos": [f"{BASE}images/products/{pid}_1.jpg"],
        })
    return lots


def add_details(lot):
    page = get(f"catalogue_detail.aspx?cdid={lot['cdid']}&chid={lot['chid']}")
    pids = sorted(set(re.findall(r"images/products/(\d+_\d+)\.jpg", page)),
                  key=lambda p: int(p.split("_")[1]))
    if pids:
        lot["photos"] = [f"{BASE}images/products/{p}.jpg" for p in pids]
    m = re.search(r"Description:</td>(.*?)</table>", page, re.S)
    if m:
        lot["description"] = clean(m.group(1))
    return lot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="data/lots.json")
    ap.add_argument("--details", action="store_true",
                    help="fetch each lot page for the full description and every photo (slower)")
    args = ap.parse_args()

    lots = []
    for chid in catalogue_ids():
        found = lots_in(chid)
        print(f"catalogue {chid}: {len(found)} lots", file=sys.stderr)
        lots.extend(found)

    if args.details:
        with ThreadPoolExecutor(max_workers=4) as pool:
            lots = list(pool.map(add_details, lots))

    with open(args.out, "w") as f:
        json.dump(lots, f, indent=1)
    print(f"{len(lots)} lots -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
