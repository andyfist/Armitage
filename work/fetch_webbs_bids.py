#!/usr/bin/env python3
# Refresh current bid, opening (asking) bid, estimate and bid count for the scanned Webb's lots. Read-only.
# Usage: python3 -I fetch_webbs_bids.py <aid>
import sys, re, json, os, time, urllib.request, html
from concurrent.futures import ThreadPoolExecutor

AID = sys.argv[1]
W = '/home/user/Armitage/work'
D = f'{W}/webbs{AID}'
OUT = f'{D}/bids_pages'
os.makedirs(OUT, exist_ok=True)
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'
lots = {c['lot_id']: c for c in json.load(open(f'{D}/all_lots.json'))}
ids = [i for b in json.load(open(f'{W}/webbs{AID}_args.json'))['batches'] for i in b['ids']]


def one(lid):
    c = lots[lid]
    u = f'https://auctions.webbs.co.nz/lot-details/index/catalog/{AID}/lot/{lid}/{c["slug"]}'
    s = ''
    for t in range(3):
        try:
            s = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA}), timeout=40).read().decode('utf-8', 'ignore')
            break
        except Exception:
            time.sleep(2 * (t + 1))
    time.sleep(0.3)
    cb = re.search(r'"currentBid":(null|[0-9.]+)', s)
    ab = re.search(r'"askingBid":(null|[0-9.]+)', s)
    t = re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', s)))
    est = re.search(r'Estimate \$ ?([0-9,]+) ?- ?\$ ?([0-9,]+)', t)
    nb = re.search(r'(\d+) bids?\b', t)
    f = lambda m: None if (not m or m.group(1) == 'null') else float(m.group(1))
    return lid, {'current_bid': f(cb), 'asking_bid': f(ab),
                 'est_low': int(est.group(1).replace(',', '')) if est else None,
                 'est_high': int(est.group(2).replace(',', '')) if est else None,
                 'bid_count': int(nb.group(1)) if nb else 0}


with ThreadPoolExecutor(6) as ex:
    res = dict(ex.map(one, ids))
json.dump({'fetched_utc': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()), 'lots': {str(k): v for k, v in res.items()}}, open(f'{W}/webbs{AID}_bids.json', 'w'), indent=0)
print('lots', len(res), 'with current bid', sum(1 for v in res.values() if v['current_bid']), 'with asking', sum(1 for v in res.values() if v['asking_bid']))
