#!/usr/bin/env python3
"""Usage: python3 pipeline/prep_gowans.py [<auction id>] [--name "<name>"] [--no-photos]

Gowans Auctions (Hobart) version of pipeline/prep.py: the same output files under
pipeline/sales/gowans<auction id>/ (cat.json, lots.json, lots/<id>.json, bids.json, titles/,
photos/, sheets/, wfargs.json), so every later stage (wf_funnel.js, assess.py, chrome_brief.py,
photo_list.py, bidders.py, morning.py) runs unchanged. The sale id is "gowans<auction id>".
With no auction id it takes the auction whose status is "current".

Gowans has a public JSON API (read-only, no login): /auctions/ and /lots/?filter[auction]=<id>.
A lot carries title, description, lot number, bid_count and photo URLs (sale_price is 0 until
the sale has run). It does NOT carry the bid history, so bids.json has a bid count and no
history (the bidder scan has nothing to work with on Gowans), and there is no estimate.
About 1 request a second for the API and 3 at a time for photos.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prep  # noqa: E402  (curl, sheet, close_key, now_text, constants)
import promote  # noqa: E402
import rules  # noqa: E402

API = 'https://www.gowansauctions.com.au/backend/api/v1'
PREMIUM = '19.8%'  # buyer's premium used in work/build_gowans.py; assess.py needs --premium 0.198


def api(path):
    for attempt in range(3):
        r = subprocess.run(['curl', '-sSL', '--max-time', '40', '-A', prep.UA, API + path], capture_output=True)
        try:
            return json.loads(r.stdout)
        except Exception:
            time.sleep(5 * (attempt + 1))
    sys.exit(f'Gowans API failed: {path}')


def hobart(iso):
    t = datetime.datetime.fromisoformat(iso.replace('Z', '+00:00')).astimezone(prep.HOBART)
    return t.strftime('%d/%m/%Y %I:%M:%S %p %Z').lstrip('0').replace('/0', '/')


def pick_auction(aid):
    data = api('/auctions/?page%5Bsize%5D=5&sort=-id')['data']
    for a in data:
        if (aid and a['id'] == str(aid)) or (not aid and a['attributes']['status'] == 'current'):
            return a
    sys.exit(f'auction {aid or "(current)"} not found in the latest five')


def all_lots(aid):
    rows, n = [], 1
    while True:
        d = api(f'/lots/?filter%5Bauction%5D={aid}&page%5Bsize%5D=100&page%5Bnumber%5D={n}')
        rows += d['data']
        if n >= d['meta']['pagination']['pages']:
            return rows
        n += 1
        time.sleep(1)


def photos(rec, urls, D):
    if rec.get('skip_photos'):
        return rec
    paths = []
    for n, u in enumerate(urls, 1):
        out = f'{D}/photos/{rec["cdid"]}_{n}.jpg'
        if not (os.path.exists(out) and os.path.getsize(out) > 1000):
            time.sleep(prep.PAUSE)
            _, code = prep.curl(u, out)
            if code != 200:
                if os.path.exists(out):
                    os.remove(out)
                rec['photo_err'] = f'photo _{n} http {code}'
                continue
        paths.append(out)
    rec['photo_count'] = len(paths)
    if paths:
        try:
            rec['sheet'] = prep.sheet(paths, f'{D}/sheets/{rec["cdid"]}.jpg', rec['lot_label'])
            rec['state'] = 'FETCHED'
        except Exception as e:
            rec.update(state='UNSCANNED', reason=f'bad photo: {e}')
    else:
        rec.update(state='UNSCANNED', reason=rec.get('photo_err') or 'no photos')
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('auction', nargs='?')
    ap.add_argument('--name')
    ap.add_argument('--no-photos', action='store_true')
    args = ap.parse_args()
    auc = pick_auction(args.auction)
    aid, att = auc['id'], auc['attributes']
    chid = f'gowans{aid}'
    close = hobart(att['bids_close_at'] or att['date'])
    name = args.name or f'Gowans {att["title"]} {att["code"]}'
    D = os.path.join(prep.ROOT, 'pipeline', 'sales', chid)
    for sub in ('photos', 'sheets', 'crops', 'lots', 'titles', 'obs', 'scans', 'market'):
        os.makedirs(os.path.join(D, sub), exist_ok=True)
    now = prep.now_text()

    raw = all_lots(aid)
    print('Gowans lots', len(raw), 'closes', close, flush=True)
    recs, bids, urls = [], {}, {}
    for x in raw:
        a = x['attributes']
        cd = int(x['id'])
        lot = int(re.sub(r'\D', '', str(a.get('number') or '')) or 0)  # 1262A -> 1262
        label = str(a.get('number') or a.get('number_preview') or cd)
        img = [(i.get('large') or i.get('medium') or {}).get('url') or i.get('original') for i in a['image_urls']]
        urls[cd] = [u for u in img if u]
        rec = {'cdid': cd, 'chid': chid, 'url': f'{API}/lots/{cd}/', 'http': 200, 'lot_label': label, 'lot': lot, 'premium': PREMIUM,
               'checked': now, 'close': close, 'title': (a.get('title') or '').strip(), 'description': (a.get('description') or '').strip(),
               'state': 'FETCHED', 'photo_count': 0, 'photo_urls': urls[cd]}
        rec['cls'], rec['cls_reason'] = rules.classify(rec['title'], rec['description'])
        if rec['cls'] == 'title_pass':
            why = promote.check(rec['title'], rec['description'])
            if why:
                rec['cls'], rec['cls_reason'] = 'always_look', why
        if rec['cls'] == 'exclude':
            rec.update(state='EXCLUDED', reason=rec['cls_reason'], skip_photos=True)
        if not urls[cd]:
            rec.update(skip_photos=True)
            if rec['state'] == 'FETCHED':
                rec.update(state='UNSCANNED', reason='no photos')
        recs.append(rec)
        bids[str(cd)] = {'current_bid': None, 'bid_count': a.get('bid_count') or 0, 'estimate': None, 'checked': now, 'close': close, 'history': []}
    counts = {k: sum(1 for r in recs if r['cls'] == k) for k in ('always_look', 'title_pass', 'exclude')}
    print('classes', counts, flush=True)

    if not args.no_photos:
        with ThreadPoolExecutor(3) as ex:
            recs = list(ex.map(lambda r: photos(r, urls[r['cdid']], D), recs))
        print('photos', sum(r.get('photo_count', 0) for r in recs), 'lots with photos', sum(1 for r in recs if r['state'] == 'FETCHED'), flush=True)

    recs.sort(key=lambda r: (r['lot'], r['cdid']))
    slim = [{k: v for k, v in r.items() if k not in ('skip_photos', 'photo_err')} for r in recs]
    for s in slim:
        json.dump(s, open(f'{D}/lots/{s["cdid"]}.json', 'w'), indent=1)
    json.dump(slim, open(f'{D}/lots.json', 'w'), indent=1)
    json.dump(bids, open(f'{D}/bids.json', 'w'), indent=1)
    title_lots = [r for r in slim if r['cls'] == 'title_pass' and r['title']]
    chunks = 0
    for i in range(0, len(title_lots), prep.CHUNK):
        chunks += 1
        json.dump([{'cdid': r['cdid'], 'lot': r['lot'], 'title': r['title'], 'description': r['description'][:400]}
                   for r in title_lots[i:i + prep.CHUNK]], open(f'{D}/titles/in_{chunks}.json', 'w'), indent=1)
    lots = [r['lot'] for r in slim if r['lot']]
    cat = {'chid': chid, 'name': name, 'lots': len(slim), 'lot_min': min(lots) if lots else None, 'lot_max': max(lots) if lots else None,
           'close_first': close, 'close_last': close, 'prepared': now, 'classes': counts,
           'with_photos': sum(1 for r in slim if r['state'] == 'FETCHED'), 'title_chunks': chunks, 'premium': PREMIUM}
    json.dump(cat, open(f'{D}/cat.json', 'w'), indent=1)
    wfargs = {
        'chid': chid, 'name': name, 'root': D, 'pipeline': os.path.join(prep.ROOT, 'pipeline'),
        'venue': 'run by Gowans Auctions in Hobart, Tasmania',
        'titleChunks': chunks, 'batch': prep.BATCH, 'concurrency': 8, 'maxMarket': 200,
        'alwaysLook': [{'cdid': r['cdid'], 'lot': r['lot'], 'title': r['title'], 'why': r['cls_reason']}
                       for r in slim if r['cls'] == 'always_look' and r['state'] == 'FETCHED'],
        'description': (f'Gowans Auctions (Hobart, Tasmania) weekly auction {att["code"]}: lots {cat["lot_min"]} to {cat["lot_max"]}, '
                        f'absentee bidding closes {close}; the room auction is the next morning. Buyer\'s premium about {PREMIUM}. '
                        'Gowans lots have few words and usually one or two photos, so treat the photos as the main evidence'),
    }
    json.dump(wfargs, open(f'{D}/wfargs.json', 'w'), separators=(',', ':'))
    print(json.dumps(cat), flush=True)


if __name__ == '__main__':
    main()
