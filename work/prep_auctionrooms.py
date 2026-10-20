#!/usr/bin/env python3
"""Usage: prep_auctionrooms.py <key> <sale> "<close text>" <pages>      (The Auction Rooms, Welland SA)
       prep_auctionrooms.py <key> collector "<close text>" <post url>   (The Collector, Murrumbeena VIC, gallery on the auction post)
Fetches the public lot list (title and photo only; these sites show no estimate and no bid on the list), downloads every
full-size photo, builds contact sheets, writes raw_<key>_<tag>.json batches of 30 and index_<key>.txt. Read-only.
cdid is synthetic: int(sale + 4-digit list position) for The Auction Rooms, the gallery photo id for The Collector."""
import json, os, re, sys, time, subprocess, datetime, html
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
W = os.path.dirname(os.path.abspath(__file__)); KEY, SALE, CLOSE, ARG = sys.argv[1:5]
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
os.makedirs(f'{W}/photos', exist_ok=True); os.makedirs(f'{W}/sheets', exist_ok=True); os.makedirs(f'{W}/{KEY}', exist_ok=True)
def get(url, out):
    if os.path.exists(out) and os.path.getsize(out) > 1000: return open(out, errors='ignore').read()
    for a in range(4):
        r = subprocess.run(['curl', '-sS', '-L', '--max-time', '60', '-A', UA, '-o', out, '-w', '%{http_code}', url], capture_output=True)
        if r.stdout.decode()[-3:] == '200' and os.path.getsize(out) > 1000: return open(out, errors='ignore').read()
        time.sleep(2 * (a + 1))
    raise SystemExit(f'failed {url}')
lots = []   # (cdid, label, title, photo_urls, page_url)
if SALE == 'collector':
    raw = get(ARG, f'{W}/{KEY}/post.html'); seen = set()
    for m in re.finditer(r'<img[^>]*title="([^"]*)"[^>]*src="https://www\.thecollector\.com\.au/wp-content/uploads/wppa/thumbs/(\d+)\.jpg', raw):
        t, pid = html.unescape(m.group(1)).strip(), int(m.group(2))
        if pid in seen: continue
        seen.add(pid); lots.append((pid, str(len(lots) + 1), t, [f'https://www.thecollector.com.au/wp-content/uploads/wppa/{pid}.jpg'], ARG))
else:
    for p in range(1, int(ARG) + 1):
        raw = get(f'https://theauctionrooms.com.au/auctions/sale-{SALE}/?jsf=woocommerce-archive&pagenum={p}', f'{W}/{KEY}/p{p}.html')
        raw = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', '', raw)
        # each lot card: a lot page link, a thumbnail <img> and "Lot N" then the title
        cards = re.split(r'(?=<div class="[^"]*auction-grid-item)', raw)[1:]
        for c in cards:
            u = re.search(r'href="(https://theauctionrooms\.com\.au/catalogue/auction/sale-%s/lot-[^"]+)"' % SALE, c)
            im = re.search(r'src="(https://theauctionrooms\.com\.au/wp-content/uploads/[^"]+?)(?:-\d+x\d+)?\.(jpe?g|png|webp)"', c)
            lb = re.search(r'>Lot ([\w.]+)</a>', c); al = re.search(r'<img[^>]*alt="([^"]*)"', c)
            txt = html.unescape(re.sub(r'<[^>]+>', '\n', c)); tl = re.search(r'Lot\s+[\w.]+\s*\n\s*([^\n]+)', txt)
            if not (u and lb): continue
            label = lb.group(1); title = html.unescape(al.group(1)).strip() if al and al.group(1).strip() else (tl.group(1).strip() if tl else '')
            if any(l[1] == label for l in lots): continue
            photos = [f'{im.group(1)}.{im.group(2)}'] if im else []
            lots.append((int(f'{SALE}{len(lots) + 1:04d}'), label, title, photos, u.group(1)))
print(len(lots), 'lots', flush=True)
def dl(job):
    url, out = job
    if os.path.exists(out) and os.path.getsize(out) > 1000: return True
    for a in range(3):
        r = subprocess.run(['curl', '-sS', '-L', '--max-time', '40', '-A', UA, '-o', out, '-w', '%{http_code}', url], capture_output=True)
        if r.stdout.decode()[-3:] == '200' and os.path.getsize(out) > 1000: return True
        time.sleep(2 * (a + 1))
    if os.path.exists(out): os.remove(out)
    return False
jobs = []; meta = {}
for cd, label, title, photos, page in lots:
    meta[cd] = [f'{W}/photos/{cd}_{i}.jpg' for i in range(1, len(photos) + 1)]
    jobs += list(zip(photos, meta[cd]))
t0 = time.time()
with ThreadPoolExecutor(6) as ex: ok = list(ex.map(dl, jobs))
print('downloaded', sum(ok), 'of', len(jobs), 'in', int(time.time() - t0), 's', flush=True)
def sheet(paths, cd, lab):
    ims = [Image.open(p).convert('RGB') for p in paths]; n = len(ims); cols = 1 if n == 1 else 2
    rows = (n + cols - 1) // cols; cw, chh = (1000, 750) if n == 1 else (600, 450)
    S = Image.new('RGB', (cols * cw, rows * chh), 'white'); d = ImageDraw.Draw(S)
    for i, im in enumerate(ims):
        im.thumbnail((cw, chh)); xx, yy = (i % cols) * cw, (i // cols) * chh; S.paste(im, (xx, yy))
        d.rectangle([xx, yy, xx + 170, yy + 20], fill='black'); d.text((xx + 4, yy + 4), f'lot {lab} photo {i + 1}/{n}', fill='yellow')
    out = f'{W}/sheets/{cd}.jpg'; S.save(out, quality=85); return out
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=11))).strftime('%d/%m/%Y %H:%M:%S AEDT')
recs = []
for cd, label, title, photos, page in lots:
    paths = [p for p in meta[cd] if os.path.exists(p)]; digits = re.sub(r'\D', '', label.split('.')[0]) or '0'
    rec = {'cdid': cd, 'auction': KEY, 'url': page, 'http': 200, 'lot': int(digits), 'lot_label': label, 'close': CLOSE,
           'title': title, 'description': title, 'estimate': None, 'current_bid': None, 'bid_count': None, 'checked': now,
           'photo_id': str(cd), 'photo_count': len(paths), 'photo_files': paths}
    if paths: rec['state'] = 'FETCHED'; rec['sheet'] = sheet(paths, cd, label)
    else: rec['state'] = 'UNSCANNED'; rec['reason'] = 'no photo'
    recs.append(rec)
batches = []
for i in range(0, len(recs), 30):
    c = recs[i:i + 30]; tag = c[0]['cdid']
    json.dump(c, open(f'{W}/raw_{KEY}_{tag}.json', 'w'), indent=1); batches.append({'key': KEY, 'tag': tag, 'ids': [r['cdid'] for r in c]})
json.dump({'batches': batches}, open(f'{W}/{KEY}_args.json', 'w'), separators=(',', ':'))
open(f'{W}/index_{KEY}.txt', 'w').write('\n'.join(str(r['cdid']) for r in recs))
print(len(batches), 'batches written; no-photo lots', sum(1 for r in recs if r['state'] != 'FETCHED'), flush=True)
