#!/usr/bin/env python3
"""Usage: watch_armitage.py
Read-only. Lists the catalogues on armitage.bidsonline.com.au right now, remembers them in work/armitage_catalogues.json
and prints the ones not seen before as JSON (chid, name, catalogue_no, starts)."""
import re, json, os, html, subprocess, datetime

W = os.path.dirname(os.path.abspath(__file__))
BASE = 'https://armitage.bidsonline.com.au'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'
P = f'{W}/armitage_catalogues.json'
known = json.load(open(P)) if os.path.exists(P) else {}


def get(path):
    r = subprocess.run(['curl', '-sS', '-L', '-A', UA, '--max-time', '40', f'{BASE}/{path}'], capture_output=True)
    return r.stdout.decode('utf8', 'ignore')


home = get(''); auc = get('auctions.aspx')
links = re.findall(r'catalogue-group\.aspx\?chid=(\d+)[^"]*"[^>]*>([^<]+)<', home + auc)
cats = {}
for chid, name in links:
    cats.setdefault(chid, {'chid': chid, 'name': html.unescape(name).strip()})
t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', auc)))
for m in re.finditer(r'(ONLINE AUCTION.{0,120}?)\s*Catalogue No\. (\d+) - Starts: (\d+/\d+/\d+ [\d:]+ [AP]M)', t):
    nm, no, st = m.group(1).strip(), m.group(2), m.group(3)
    for c in cats.values():
        if c['name'].upper() == nm.upper(): c.update(catalogue_no=no, starts=st)
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=11))).strftime('%d/%m/%Y %H:%M AEDT')
new = []
for chid, c in cats.items():
    if chid not in known:
        c['first_seen'] = now; known[chid] = c; new.append(c)
    else:
        known[chid].update({k: v for k, v in c.items() if v})
json.dump(known, open(P, 'w'), indent=1)
print(json.dumps({'checked': now, 'current': list(cats.keys()), 'new': new}))
