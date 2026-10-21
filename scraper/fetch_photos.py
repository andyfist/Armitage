#!/usr/bin/env python3
"""Download full descriptions + photos for a shortlist of lots.

    python3 scraper/fetch_photos.py data/lots.json data/shortlist 883 874 ...
Writes data/shortlist/<lot>/{info.json,1.jpg,2.jpg,...}
"""
import json
import os
import sys

from armitage import add_details, session

lots_file, out_dir, *wanted = sys.argv[1:]
by_lot = {l["lot"]: l for l in json.load(open(lots_file))}
for n in wanted:
    lot = add_details(by_lot[n])
    d = os.path.join(out_dir, n)
    os.makedirs(d, exist_ok=True)
    for i, url in enumerate(lot["photos"][:6], 1):
        with open(os.path.join(d, f"{i}.jpg"), "wb") as f:
            f.write(session.get(url, timeout=60).content)
    json.dump(lot, open(os.path.join(d, "info.json"), "w"), indent=1)
    print(n, len(lot["photos"]), "photos |", lot.get("description", "")[:300])
