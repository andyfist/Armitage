#!/usr/bin/env python3
"""Usage: python3 pipeline/prep.py <chid> [--name "<catalogue name>"] [--no-photos]

Read-only prep of one Armitage Auctions catalogue for the funnel. Reads the public group
page for the lot list, every lot page (title, description, close time, photos, and the
estimate, current bid and bid count, which go to bids.json only so the scan never sees
them), sorts each lot with pipeline/rules.py (and pipeline/promote.py, which sends lots
whose title matches past sales of $250 or more straight to the photo scan), downloads the
photos of every lot that is not excluded, builds a contact sheet per lot, and writes everything under
pipeline/sales/<chid>/:

  cat.json        the catalogue: name, lot count, close times, counts per class
  lots.json       every lot (slim record, no bids)         lots/<cdid>.json   one file per lot
  bids.json       estimate, current bid, bid count, close per lot (never shown to the scan)
  titles/in_<n>.json   chunks of 100 title-pass lots       photos/ sheets/ crops/   images (not in git)
  wfargs.json     arguments for pipeline/wf_funnel.js

About 3 to 4 requests a second in total. Re-running skips photos already on disk.
"""
import argparse
import datetime
import html
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import promote  # noqa: E402
import rules  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://armitage.bidsonline.com.au'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'
PAUSE = 0.7
BATCH = 15      # lots per photo-scan agent
CHUNK = 100     # lots per title-pass agent

try:
    from zoneinfo import ZoneInfo
    HOBART = ZoneInfo('Australia/Hobart')
except Exception:
    HOBART = datetime.timezone(datetime.timedelta(hours=11), 'AEDT')


def now_text():
    return datetime.datetime.now(HOBART).strftime('%d/%m/%Y %H:%M %Z')


def curl(url, out=None, tries=3):
    """GET with curl (it follows the proxy settings). Returns (body or None, http code)."""
    code = '0'
    for attempt in range(tries):
        cmd = ['curl', '-sS', '-L', '-A', UA, '--max-time', '40', '-w', '%{http_code}'] + (['-o', out] if out else []) + [url]
        r = subprocess.run(cmd, capture_output=True)
        code = (r.stdout if out else r.stdout[-3:]).decode(errors='ignore')[-3:]
        if code == '200':
            return (None if out else r.stdout[:-3]), 200
        if code == '404':
            return None, 404
        time.sleep(10 * (attempt + 1))
    return None, int(code) if code.isdigit() else 0


def strip(h):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', h, flags=re.S)))).strip()


CLOSE_RE = re.compile(r'(\d+)/(\d+)/(\d+) (\d+):(\d+)(?::(\d+))? ([AP])M')


def close_key(c):
    m = CLOSE_RE.search(c or '')
    if not m:
        return 0
    d, mo, y, h, mi, s, ap = m.groups()
    h = int(h) % 12 + (12 if ap == 'P' else 0)
    return int(y) * 10**10 + int(mo) * 10**8 + int(d) * 10**6 + h * 10**4 + int(mi) * 100 + int(s or 0)


def group_items(chid):
    """The cdid list from the catalogue's group page."""
    body, code = curl(f'{BASE}/catalogue-group.aspx?chid={chid}&BID=')
    if code != 200:
        sys.exit(f'group page http {code}')
    g = body.decode('utf8', 'ignore')
    items, seen = [], set()
    for m in re.finditer(r'id="item_(\d+)"(.*?)id="timelabel_\1"[^>]*>([^<]*)<', g, flags=re.S):
        cd = int(m.group(1))
        if cd in seen:
            continue
        seen.add(cd)
        blk = m.group(2)
        lot = re.search(r'Lot:\s*([^\s<]+)\s*-', blk)
        pid = re.search(r'products/grid/(\d+)_', blk)
        items.append({'cdid': cd, 'lot_label': lot.group(1) if lot else '', 'pid': pid.group(1) if pid else None, 'close_group': m.group(3).strip()})
    return items


def parse_lot(chid, it, now):
    """One lot page -> (record for the scan, bids record)."""
    time.sleep(PAUSE)
    cd = it['cdid']
    url = f'{BASE}/catalogue_detail.aspx?cdid={cd}&chid={chid}&category=ALL&style=group'
    rec = {'cdid': cd, 'chid': chid, 'url': url, 'http': 0, 'lot_label': it['lot_label'], 'premium': '22%', 'checked': now}
    body, code = curl(url)
    rec['http'] = code
    if code != 200:
        rec.update(state='UNSCANNED', reason=f'http {code}', photo_id=it['pid'], photo_ns=[], title=None, description=None,
                   lot=int(re.sub(r'\D', '', it['lot_label']) or 0), close=it['close_group'])
        return rec, {}
    h = body.decode('utf8', 'ignore')
    t = strip(h)
    lot = re.search(r'Lot No\. ?(\w+)', t)
    close = re.search(r'Auction Closes: (\d+/\d+/\d+ [\d:]+ [AP]M \w+)', t)
    desc = re.search(r'Description:(.*?)Estimate:', t)
    est = re.search(r'Estimate: Estimate ([^ ]+(?: ?- ?[^ ]+)?)', t)
    cur = re.search(r'Current Bid \(\$\): (\$[\d,\.]+|[^ ]+)', t)
    title = re.search(r'<h2 class="post-title">(.*?)<span', h, flags=re.S)
    bid_rows = re.findall(r'<tr>\s*<td>([^<]*)</td>\s*<td>(\d+)</td>\s*<td>([\d\.,]+)</td>\s*<td>([\d/: APM]+)</td>', h)
    label = (lot.group(1) if lot else it['lot_label']) or str(cd)
    digits = re.sub(r'\D', '', label) or '0'
    pids = re.findall(r'products/(\d+)_\d+\.jpg', h)
    pid = it['pid'] or (pids[0] if pids else None)
    ns = sorted({int(n) for p, n in re.findall(r'products/(\d+)_(\d+)\.jpg', h) if p == pid})
    rec.update(lot=int(digits), lot_label=label, close=close.group(1) if close else it['close_group'],
               title=strip(title.group(1)) if title else None, description=(desc.group(1).strip() if desc else None),
               photo_id=pid, photo_ns=ns, state='FETCHED')
    bids = {'current_bid': cur.group(1) if cur else None, 'bid_count': len(bid_rows), 'estimate': est.group(1) if est else None,
            'checked': now, 'close': rec['close'],
            # the bid history as shown on the page: who (bidder number and hometown as Armitage prints them), amount, when
            'history': [{'who': strip(w), 'no': n, 'amount': a, 'when': t} for w, n, a, t in bid_rows]}
    return rec, bids


def sheet(paths, out, label):
    from PIL import Image, ImageDraw
    ims = [Image.open(p).convert('RGB') for p in paths]
    n = len(ims)
    cols = 1 if n == 1 else 2
    rows = (n + cols - 1) // cols
    cw, ch = (800, 600) if n == 1 else (600, 450)
    S = Image.new('RGB', (cols * cw, rows * ch), 'white')
    d = ImageDraw.Draw(S)
    for i, im in enumerate(ims):
        im.thumbnail((cw, ch))
        x, y = (i % cols) * cw, (i // cols) * ch
        S.paste(im, (x, y))
        d.rectangle([x, y, x + 170, y + 20], fill='black')
        d.text((x + 4, y + 4), f'lot {label} photo {i + 1}/{n}', fill='yellow')
    S.save(out, quality=85)
    return out


def photos(rec, D):
    """Download the photos the page lists, probing past the last one until a 404; build the contact sheet."""
    if rec.get('state') == 'UNSCANNED' or rec.get('skip_photos'):
        return rec
    pid = rec.get('photo_id')
    if not pid:
        rec.update(state='UNSCANNED', reason='no photo id', photo_count=0)
        return rec
    ns = rec.get('photo_ns') or []
    maxn = max(ns) if ns else 0
    paths, n = [], 1
    while n <= 40:
        out = f'{D}/photos/{rec["cdid"]}_{n}.jpg'
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            code = 200
        else:
            time.sleep(PAUSE)
            _, code = curl(f'{BASE}/images/products/{pid}_{n}.jpg', out)
            if code != 200 and os.path.exists(out):
                os.remove(out)
        if code == 200:
            paths.append(out)
        elif code == 404:
            if n > maxn:
                break
        else:
            rec['photo_err'] = f'photo _{n} http {code}'
        n += 1
    rec['photo_count'] = len(paths)
    if paths:
        try:
            rec['sheet'] = sheet(paths, f'{D}/sheets/{rec["cdid"]}.jpg', rec['lot_label'])
        except Exception as e:  # a truncated download crashed a mainland prep once; drop the file and move on
            rec.update(state='UNSCANNED', reason=f'bad photo: {e}')
            return rec
        rec['state'] = 'FETCHED'
    else:
        rec.update(state='UNSCANNED', reason=rec.get('photo_err') or 'no photos')
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('chid')
    ap.add_argument('--name', default=None, help='catalogue name (defaults to the name in pipeline/state/sales.json or "catalogue <chid>")')
    ap.add_argument('--no-photos', action='store_true', help='lot pages only; no photo download')
    args = ap.parse_args()
    chid = args.chid
    D = os.path.join(ROOT, 'pipeline', 'sales', chid)
    for sub in ('photos', 'sheets', 'crops', 'lots', 'titles', 'obs', 'scans', 'market'):
        os.makedirs(os.path.join(D, sub), exist_ok=True)
    now = now_text()

    name = args.name
    if not name:
        state_file = os.path.join(ROOT, 'pipeline', 'state', 'sales.json')
        if os.path.exists(state_file):
            name = json.load(open(state_file)).get('catalogues', {}).get(chid, {}).get('name')
    name = name or f'catalogue {chid}'

    # 1. group page, 2. lot pages
    items = group_items(chid)
    print('group page lots', len(items), flush=True)
    with ThreadPoolExecutor(3) as ex:
        parsed = list(ex.map(lambda it: parse_lot(chid, it, now), items))
    recs = [r for r, _ in parsed]
    bids = {str(r['cdid']): b for r, b in parsed if b}
    print('lot pages', sum(1 for r in recs if r['http'] == 200), 'of', len(recs), flush=True)

    # 3. sort every lot with the rules; excluded lots get no photos
    for r in recs:
        r['cls'], r['cls_reason'] = rules.classify(r.get('title'), r.get('description'))
        if r['cls'] == 'title_pass':  # the results database can promote a lot to the photo scan, never exclude it
            why = promote.check(r.get('title'), r.get('description'))
            if why:
                r['cls'], r['cls_reason'] = 'always_look', why
        if r['cls'] == 'exclude' and r.get('state') == 'FETCHED':
            r.update(state='EXCLUDED', reason=r['cls_reason'], skip_photos=True, photo_count=0)
    counts = {k: sum(1 for r in recs if r['cls'] == k) for k in ('always_look', 'title_pass', 'exclude')}
    print('classes', counts, flush=True)

    # 4. photos and contact sheets
    if not args.no_photos:
        with ThreadPoolExecutor(3) as ex:
            recs = list(ex.map(lambda r: photos(r, D), recs))
        print('photos', sum(r.get('photo_count', 0) for r in recs), 'lots with photos', sum(1 for r in recs if r.get('state') == 'FETCHED'), flush=True)

    # 5. write everything
    recs.sort(key=lambda r: (r.get('lot') or 0, r['cdid']))
    slim = []
    for r in recs:
        s = {k: v for k, v in r.items() if k not in ('photo_ns', 'skip_photos', 'photo_err')}
        slim.append(s)
        json.dump(s, open(f'{D}/lots/{r["cdid"]}.json', 'w'), indent=1)
    json.dump(slim, open(f'{D}/lots.json', 'w'), indent=1)
    json.dump(bids, open(f'{D}/bids.json', 'w'), indent=1)

    title_lots = [r for r in slim if r['cls'] == 'title_pass' and r.get('title')]
    chunks = 0
    for i in range(0, len(title_lots), CHUNK):
        chunks += 1
        json.dump([{'cdid': r['cdid'], 'lot': r['lot'], 'title': r['title'], 'description': (r.get('description') or '')[:400]}
                   for r in title_lots[i:i + CHUNK]], open(f'{D}/titles/in_{chunks}.json', 'w'), indent=1)

    closes = sorted((r.get('close') for r in recs if r.get('close')), key=close_key)
    lots = [r['lot'] for r in recs if r.get('lot')]
    cat = {'chid': chid, 'name': name, 'lots': len(recs), 'lot_min': min(lots) if lots else None, 'lot_max': max(lots) if lots else None,
           'close_first': closes[0] if closes else None, 'close_last': closes[-1] if closes else None, 'prepared': now,
           'classes': counts, 'with_photos': sum(1 for r in recs if r.get('state') == 'FETCHED'), 'title_chunks': chunks}
    json.dump(cat, open(f'{D}/cat.json', 'w'), indent=1)
    wfargs = {
        'chid': chid, 'name': name, 'root': D, 'pipeline': os.path.join(ROOT, 'pipeline'),
        'titleChunks': chunks, 'batch': BATCH, 'concurrency': 8, 'maxMarket': 200,
        'alwaysLook': [{'cdid': r['cdid'], 'lot': r['lot'], 'title': r['title'], 'why': r['cls_reason']}
                       for r in slim if r['cls'] == 'always_look' and r.get('state') == 'FETCHED'],
        'description': (f'Armitage Auctions (Invermay, Launceston) online auction, {name}: lots {cat["lot_min"]} to {cat["lot_max"]}, '
                        f'each lot closes at its own time from {cat["close_first"]} to {cat["close_last"]}'),
    }
    json.dump(wfargs, open(f'{D}/wfargs.json', 'w'), separators=(',', ':'))
    print(json.dumps(cat), flush=True)


if __name__ == '__main__':
    main()
