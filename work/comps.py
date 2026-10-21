#!/usr/bin/env python3
"""Usage: python3 -I comps.py <words> [--years N] [--min-price N]
Looks up sold prices for an item in the results database: gowans_all.json (every Gowans lot since mid-2024, hammer = sale_price/100)
and aba_lots.json (every Australian Book Auctions lot, sales 100 to 119, with hammer) and sold_db.json (every sold comp the agents found, with URL and date). Prints each hit and the lowest, median and highest hammer.
Hammer prices exclude the buyer's premium. Gowans titles are loose, so read the titles before trusting a number."""
import json, os, re, sys, statistics, datetime
W = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]; years = 10; floor = 0
if '--years' in args: i = args.index('--years'); years = float(args[i + 1]); del args[i:i + 2]
if '--min-price' in args: i = args.index('--min-price'); floor = float(args[i + 1]); del args[i:i + 2]
words = [w.lower() for w in args]
cut = (datetime.date.today() - datetime.timedelta(days=int(years * 365))).isoformat()
hits = []
G = f'{W}/gowans_all.json'
if os.path.exists(G):
    for k, r in json.load(open(G))['rows'].items():
        t = (r['title'] or '').lower()
        if r['hammer'] > floor and r['created'] >= cut and all(w in t for w in words):
            hits.append((r['created'], r['hammer'], f"Gowans lot {r['lot']} ({r['bids']} bids): {r['title']}", f"gowans id {k}"))
for r in json.load(open(f'{W}/sold_db.json')):
    blob = f"{r['item']} {r['note']}".lower()
    d = re.search(r'(20\d\d)-(\d\d)-(\d\d)', str(r['date'])); ds = d.group(0) if d else str(r['date'])
    if r['aud_hammer'] > floor and all(w in blob for w in words) and (not d or ds >= cut):
        hits.append((ds, r['aud_hammer'], f"{r['venue']} [{r['match']}]: {r['item'][:70]}", r['url']))
A = f'{W}/aba_lots.json'
if os.path.exists(A):
    mon = dict(January='01', February='02', March='03', April='04', May='05', June='06', July='07', August='08', September='09', October='10', November='11', December='12')
    for r in json.load(open(A)):
        if r['hammer'] and r['hammer'] > floor and all(w in r['text'].lower() for w in words):
            m = re.match(r'(\w+) (\d{4})', r['date'] or ''); ds = f"{m.group(2)}-{mon.get(m.group(1), '01')}" if m else f"sale {r['sale']}"
            if not m or ds >= cut[:7]: hits.append((ds, r['hammer'], f"Australian Book Auctions Sale {r['sale']} lot {r['lot']}: {r['text'][:90]}", r['price_url']))
hits.sort(reverse=True)
for h in hits[:40]: print(h[0], f"${h[1]:,.0f}", h[2], h[3])
if hits:
    p = sorted(h[1] for h in hits)
    print(f"\n{len(hits)} sales, lowest ${p[0]:,.0f}, median ${statistics.median(p):,.0f}, highest ${p[-1]:,.0f} (hammer, premium extra)")
else: print('no sales found')
