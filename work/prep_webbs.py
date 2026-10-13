#!/usr/bin/env python3
# Prep for the Webb's whisky photo scan. Read-only: fetches public catalogue and lot pages and lot images.
# Usage: python3 -I prep_webbs.py <auction_id>
import sys, re, os, json, html, glob, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

AID = sys.argv[1]
W = '/home/user/Armitage/work'
D = f'{W}/webbs{AID}'
LOTS = f'{D}/lots'
PH = f'{D}/photos'
SH = f'{D}/sheets'
for p in (LOTS, PH, SH):
    os.makedirs(p, exist_ok=True)
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'
BASE = 'https://auctions.webbs.co.nz'


def get(url, path=None, tries=3):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
            if path:
                open(path, 'wb').write(data)
            return data
        except Exception as e:
            err = e
            time.sleep(2 * (t + 1))
    print('FAIL', url, err, file=sys.stderr)
    return None


# 1. catalogue: lot id, lot label, slug
cat = {}
for f in sorted(glob.glob(f'{D}/pg_*.html')):
    s = open(f, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'lot-details/index/catalog/%s/lot/(\d+)/([^?"]+)\?[^"]*" class="auc-lot-link" id="lot[^"]*">Lot ([^<]+)<' % AID, s):
        cat[m.group(1)] = {'lot_id': int(m.group(1)), 'slug': m.group(2), 'lot_label': m.group(3).strip()}
print('catalogue lots', len(cat))


# 2. lot pages
def fetch_lot(lid):
    p = f'{LOTS}/{lid}.html'
    if not os.path.exists(p) or os.path.getsize(p) < 5000:
        get(f'{BASE}/lot-details/index/catalog/{AID}/lot/{lid}/{cat[lid]["slug"]}', p)
        time.sleep(0.3)
    return lid


with ThreadPoolExecutor(6) as ex:
    list(ex.map(fetch_lot, cat))


def text(x):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()


recs = []
for lid, c in cat.items():
    p = f'{LOTS}/{lid}.html'
    if not os.path.exists(p):
        c['state'] = 'NO_PAGE'
        recs.append(c)
        continue
    s = open(p, encoding='utf-8', errors='ignore').read()
    i = s.find('description-info-content')
    block = text(s[i:i + 6000]) if i > 0 else ''
    desc = block.split('Terms and conditions')[0].replace('description-info-content">', '').strip()
    m = re.search(r'Categories:\s*(.*)$', desc)
    c['category'] = m.group(1).strip() if m else ''
    c['description'] = re.sub(r'\s*Categories:.*$', '', desc).replace('Description:', '').strip()
    t = re.search(r'<meta name="description" content="([^"]*)"', s)
    c['title'] = html.unescape(t.group(1)) if t else c['slug']
    imgs = []
    for im in re.findall(r'images/lot/(\d+)/(\d+)_xl\.jpg', s):
        if im not in imgs:
            imgs.append(im)
    c['images'] = [f'{BASE}/images/lot/{a}/{b}_xl.jpg' for a, b in imgs]
    recs.append(c)

WH = re.compile(r'whisk|bourbon|scotch|single malt|blended malt|rye|spirits', re.I)
def cat_tail(c):
    return c.get('category', '').replace('Fine Wines & Whiskies', '')


whisky = [c for c in recs if WH.search(cat_tail(c)) or WH.search(c.get('title', ''))]
# also non-wine spirits lots whose category is a general spirits or miniatures group
NOTWH = re.compile(r'brandy|cognac|armagnac|gin\b|rum\b|vodka|liqueur|tequila|sake|port\b|fortified|wine', re.I)
other_spirits = [c for c in recs if c not in whisky and (
    re.search(r'miniature|decanter|mixed|assorted|unlabel', c.get('title', ''), re.I)
    or ('Prestige Spirits' in c.get('category', '') and not NOTWH.search(cat_tail(c)))
    or cat_tail(c).strip(' >') in ('Spirits', 'Misc'))]
sel = whisky + other_spirits
print('whisky lots', len(whisky), 'other spirits/mixed', len(other_spirits))
json.dump(recs, open(f'{D}/all_lots.json', 'w'))


# 3. photos at the largest size the site serves (_xl, about 1000 px long side)
def fetch_img(job):
    url, path = job
    if not os.path.exists(path) or os.path.getsize(path) < 2000:
        get(url, path)
    return path


jobs = []
for c in sel:
    c['photos'] = []
    for n, u in enumerate(c['images'], 1):
        path = f'{PH}/{c["lot_id"]}_{n}.jpg'
        jobs.append((u, path))
        c['photos'].append(path)
with ThreadPoolExecutor(8) as ex:
    list(ex.map(fetch_img, jobs))
ok = sum(1 for _, p in jobs if os.path.exists(p) and os.path.getsize(p) >= 2000)
print('photos', ok, 'of', len(jobs))

# 4. contact sheets for orientation only (agents must read the full-size originals)
from PIL import Image
sizes = []
for c in sel:
    ims = [Image.open(p).convert('RGB') for p in c['photos'] if os.path.exists(p)]
    for im in ims:
        sizes.append(max(im.size))
    if not ims:
        continue
    th = [im.copy() for im in ims]
    for t in th:
        t.thumbnail((400, 400))
    cols = min(4, len(th))
    rows = (len(th) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * 410, rows * 410), 'white')
    for k, t in enumerate(th):
        sheet.paste(t, ((k % cols) * 410 + 5, (k // cols) * 410 + 5))
    sheet.save(f'{SH}/{c["lot_id"]}.jpg', quality=85)
    c['sheet'] = f'{SH}/{c["lot_id"]}.jpg'
    c['photo_count'] = len(ims)
print('max image side: min', min(sizes) if sizes else 0, 'max', max(sizes) if sizes else 0)

# 5. batches of 6 lots
batches = []
for i in range(0, len(sel), 6):
    b = sel[i:i + 6]
    tag = b[0]['lot_id']
    keep = ['lot_id', 'lot_label', 'title', 'description', 'category', 'photos', 'photo_count', 'sheet']
    json.dump([{k: c.get(k) for k in keep} for c in b], open(f'{D}/batch_{tag}.json', 'w'), indent=1)
    batches.append({'tag': tag, 'ids': [c['lot_id'] for c in b]})
json.dump({'auction': AID, 'batches': batches}, open(f'{W}/webbs{AID}_args.json', 'w'))
print('batches', len(batches))
