#!/usr/bin/env python3
"""Usage: prep_armitage.py <chid> <key> ["<catalogue name>"]
Read-only prep of one Armitage Auctions (bidsonline) catalogue. Reads the public group page for the cdid list, each lot
page (title, description, close time, bid count, estimate, current bid), downloads every photo at full size, builds
contact sheets and writes raw_<key>_<tag>.json batches of 15 for the scan workflow.
The estimate, current bid and bid count go to refresh_<key>.json only, so the scan agents never see them.
About 3 to 4 requests a second in total (3 workers, each pausing between requests)."""
import sys, re, json, time, html, os, datetime, subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw

CHID, KEY = sys.argv[1], sys.argv[2]
NAME = sys.argv[3] if len(sys.argv) > 3 else f'catalogue {CHID}'
W = os.path.dirname(os.path.abspath(__file__))
BASE = 'https://armitage.bidsonline.com.au'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'
os.makedirs(f'{W}/photos', exist_ok=True); os.makedirs(f'{W}/sheets', exist_ok=True)
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=11))).strftime('%d/%m/%Y %H:%M AEDT')
PAUSE = 0.7


def curl(url, out=None, tries=3):
    for a in range(tries):
        cmd = ['curl', '-sS', '-L', '-A', UA, '--max-time', '40', '-w', '%{http_code}'] + (['-o', out] if out else []) + [url]
        r = subprocess.run(cmd, capture_output=True)
        code = (r.stdout if out else r.stdout[-3:]).decode(errors='ignore')[-3:]
        if code == '200': return (None if out else r.stdout[:-3]), 200
        if code == '404': return None, 404
        time.sleep(10 * (a + 1))
    return None, int(code) if code.isdigit() else 0


def strip(h):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', h, flags=re.S)))).strip()


def close_key(c):
    m = re.match(r'(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+) ([AP])M', c or '')
    if not m: return 0
    d, mo, y, h, mi, s, ap = m.groups(); h = int(h) % 12 + (12 if ap == 'P' else 0)
    return int(y) * 1e10 + int(mo) * 1e8 + int(d) * 1e6 + h * 1e4 + int(mi) * 100 + int(s)


# 1. group page: the cdid list for this catalogue
body, code = curl(f'{BASE}/catalogue-group.aspx?chid={CHID}&BID=')
if code != 200: sys.exit(f'group page http {code}')
g = body.decode('utf8', 'ignore')
items, seen = [], set()
for m in re.finditer(r'id="item_(\d+)"(.*?)id="timelabel_\1"[^>]*>([^<]*)<', g, flags=re.S):
    cd = int(m.group(1)); blk = m.group(2)
    if cd in seen: continue
    seen.add(cd)
    lot = re.search(r'Lot:\s*([^\s<]+)\s*-', blk); pid = re.search(r'products/grid/(\d+)_', blk)
    items.append({'cdid': cd, 'lot_label': lot.group(1) if lot else '', 'pid': pid.group(1) if pid else None, 'close_group': m.group(3).strip()})
print('group page lots', len(items), flush=True)


# 2. lot pages
def parse(it):
    time.sleep(PAUSE)
    cd = it['cdid']; url = f'{BASE}/catalogue_detail.aspx?cdid={cd}&chid={CHID}&category=ALL&style=group'
    rec = {'cdid': cd, 'auction': KEY, 'url': url, 'http': 0, 'lot_label': it['lot_label'], 'premium': '22%', 'checked': NOW}
    body, code = curl(url); rec['http'] = code
    if code != 200:
        rec.update(state='UNSCANNED', reason=f'http {code}', photo_id=it['pid'], photo_ns=[])
        return rec, {}
    h = body.decode('utf8', 'ignore'); t = strip(h)
    lot = re.search(r'Lot No\. ?(\w+)', t); close = re.search(r'Auction Closes: (\d+/\d+/\d+ [\d:]+ [AP]M \w+)', t)
    desc = re.search(r'Description:(.*?)Estimate:', t); est = re.search(r'Estimate: Estimate ([^ ]+(?: ?- ?[^ ]+)?)', t)
    cur = re.search(r'Current Bid \(\$\): (\$[\d,\.]+|[^ ]+)', t)
    title = re.search(r'<h2 class="post-title">(.*?)<span', h, flags=re.S)
    rows = re.findall(r'<tr>\s*<td>[^<]*</td>\s*<td>\d+</td>\s*<td>[\d\.,]+</td>\s*<td>[\d/: APM]+</td>', h)
    label = (lot.group(1) if lot else it['lot_label']) or str(cd)
    digits = re.sub(r'\D', '', label) or '0'
    pids = re.findall(r'products/(\d+)_\d+\.jpg', h)
    pid = it['pid'] or (pids[0] if pids else None)
    ns = sorted({int(n) for p, n in re.findall(r'products/(\d+)_(\d+)\.jpg', h) if p == pid})
    rec.update(lot=int(digits), lot_label=label, close=close.group(1) if close else it['close_group'],
               title=strip(title.group(1)) if title else None, description=(desc.group(1).strip() if desc else None),
               photo_id=pid, photo_ns=ns)
    bids = {'current_bid': cur.group(1) if cur else None, 'bid_count': len(rows), 'estimate': est.group(1) if est else None,
            'checked': NOW, 'close': rec['close']}
    return rec, bids


with ThreadPoolExecutor(3) as ex:
    parsed = list(ex.map(parse, items))
recs = [r for r, _ in parsed]
refresh = {str(r['cdid']): b for r, b in parsed if b}
print('lot pages', sum(1 for r in recs if r['http'] == 200), 'of', len(recs), flush=True)


# 3. photos: the ones the page lists, then keep probing until a 404 past the last one
def sheet(paths, cd, lab):
    ims = [Image.open(p).convert('RGB') for p in paths]; n = len(ims); cols = 1 if n == 1 else 2
    rows = (n + cols - 1) // cols; cw, chh = (800, 600) if n == 1 else (600, 450)
    S = Image.new('RGB', (cols * cw, rows * chh), 'white'); d = ImageDraw.Draw(S)
    for i, im in enumerate(ims):
        im.thumbnail((cw, chh)); xx, yy = (i % cols) * cw, (i // cols) * chh; S.paste(im, (xx, yy))
        d.rectangle([xx, yy, xx + 170, yy + 20], fill='black'); d.text((xx + 4, yy + 4), f'lot {lab} photo {i + 1}/{n}', fill='yellow')
    out = f'{W}/sheets/{cd}.jpg'; S.save(out, quality=85); return out


def photos(rec):
    pid = rec.get('photo_id'); paths = []
    if rec.get('state') == 'UNSCANNED': return rec
    if not pid: rec.update(state='UNSCANNED', reason='no photo id', photo_count=0, photo_files=[]); return rec
    ns = rec.get('photo_ns') or []; maxn = max(ns) if ns else 0; n = 1
    while n <= 40:
        out = f'{W}/photos/{rec["cdid"]}_{n}.jpg'
        if os.path.exists(out) and os.path.getsize(out) > 1000: code = 200
        else:
            time.sleep(PAUSE); _, code = curl(f'{BASE}/images/products/{pid}_{n}.jpg', out)
            if code != 200 and os.path.exists(out): os.remove(out)
        if code == 200: paths.append(out)
        elif code == 404:
            if n > maxn: break
        else: rec['photo_err'] = f'photo _{n} http {code}'
        n += 1
    rec['photo_count'] = len(paths); rec['photo_files'] = paths
    if paths: rec['state'] = 'FETCHED'; rec['sheet'] = sheet(paths, rec['cdid'], rec['lot_label'])
    else: rec.update(state='UNSCANNED', reason=rec.get('photo_err') or 'no photos')
    return rec


with ThreadPoolExecutor(3) as ex:
    recs = list(ex.map(photos, recs))
print('photos', sum(r.get('photo_count', 0) for r in recs), 'lots with photos', sum(1 for r in recs if r.get('state') == 'FETCHED'), flush=True)

# 4. batches of 15 in lot order; estimate, current bid and bid count stay out of the scan data
recs.sort(key=lambda r: (r.get('lot') or 0, r['cdid']))
batches = []
for i in range(0, len(recs), 15):
    c = recs[i:i + 15]; tag = c[0]['cdid']
    slim = [{k: v for k, v in r.items() if k != 'photo_ns'} for r in c]
    json.dump(slim, open(f'{W}/raw_{KEY}_{tag}.json', 'w'), indent=1)
    batches.append({'key': KEY, 'tag': tag, 'ids': [r['cdid'] for r in c]})
json.dump(refresh, open(f'{W}/refresh_{KEY}.json', 'w'), indent=0)
open(f'{W}/index_{KEY}.txt', 'w').write('\n'.join(str(r['cdid']) for r in recs))
closes = sorted((r.get('close') for r in recs if r.get('close')), key=close_key)
lots = [r['lot'] for r in recs if r.get('lot')]
cat = {'chid': CHID, 'key': KEY, 'name': NAME, 'lots': len(recs), 'lot_min': min(lots) if lots else None, 'lot_max': max(lots) if lots else None,
       'close_first': closes[0] if closes else None, 'close_last': closes[-1] if closes else None, 'prepared': NOW}
json.dump(cat, open(f'{W}/armitage{CHID}_cat.json', 'w'), indent=1)
name = (f'Armitage Auctions (Invermay, Launceston) online auction, {NAME}: lots {cat["lot_min"]} to {cat["lot_max"]}, '
        f'each lot closes at its own time from {cat["close_first"]} to {cat["close_last"]}')
json.dump({'batches': batches, 'key': KEY, 'prefix': f'armitage{CHID}', 'concurrency': 16, 'name': name},
          open(f'{W}/armitage{CHID}_wfargs.json', 'w'), separators=(',', ':'))
print(len(batches), 'batches;', cat, flush=True)
