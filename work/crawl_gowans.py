#!/usr/bin/env python3
"""Usage: python3 -I crawl_gowans.py
Read-only crawl of Gowans' public lots API (all pages, 1 request a second). Writes gowans_all.json:
rows {id, title, lot, created, bids, hammer} where hammer = sale_price/100 (0 = unsold or not yet sold). Resumable: pages already saved are kept."""
import json, os, subprocess, time
W = os.path.dirname(os.path.abspath(__file__)); F = f'{W}/gowans_all.json'
db = json.load(open(F)) if os.path.exists(F) else {'pages': {}, 'rows': {}}
u = 'https://www.gowansauctions.com.au/backend/api/v1/lots/?page%5Bnumber%5D='
pages = 757
for n in range(1, 900):
    if str(n) in db['pages']: continue
    r = subprocess.run(['curl', '-sS', '--max-time', '40', u + str(n)], capture_output=True)
    try: d = json.loads(r.stdout)
    except Exception: time.sleep(5); r = subprocess.run(['curl', '-sS', '--max-time', '40', u + str(n)], capture_output=True)
    try: d = json.loads(r.stdout)
    except Exception: print('fail', n, flush=True); continue
    pages = d['meta']['pagination']['pages']
    if n > pages: break
    for x in d['data']:
        a = x['attributes']
        db['rows'][x['id']] = dict(title=a.get('title'), lot=a.get('number_preview'), created=(a.get('created') or '')[:10], bids=a.get('bid_count'), hammer=(a.get('sale_price') or 0) / 100)
    db['pages'][str(n)] = 1
    if n % 25 == 0: json.dump(db, open(F, 'w')); print(n, len(db['rows']), flush=True)
    time.sleep(1)
json.dump(db, open(F, 'w')); print('done', len(db['rows']))
