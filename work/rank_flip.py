#!/usr/bin/env python3
# Rank Webb's lots for an NZ -> AU flip via Australian Whisky Auctions.
# Usage: python3 -I rank_flip.py <aid>
import sys, json, re

AID = sys.argv[1]
W = '/home/user/Armitage/work'
NZD_AUD = 0.80315
PREMIUM = 1.22425          # Webb's 19.5% + GST on premium
FREIGHT = 60.0             # A$ per bottle, NZ to AU courier for spirits (estimate)
EXCISE_LAL = 106.0         # A$ per litre of pure alcohol, customs duty equal to spirits excise (estimate)
GST = 0.10
AWA_SELL = 0.125           # AWA seller commission and fees, incl GST (estimate, check AWA terms)

awa = {l['lot_id']: l for l in json.load(open(f'{W}/webbs{AID}_awa_result.json'))['lots']}
bids = json.load(open(f'{W}/webbs{AID}_bids.json'))['lots']
lots = {c['lot_id']: c for c in json.load(open(f'{W}/webbs{AID}/all_lots.json'))}


def nbottles(title):
    m = re.match(r'\s*\((\d+)\)', title or '')
    return int(m.group(1)) if m else 1


rows = []
for lid, a in awa.items():
    b = bids.get(str(lid), {})
    price_nzd = b.get('asking_bid') or b.get('current_bid')
    if not price_nzd:
        continue
    n = nbottles(lots.get(lid, {}).get('title'))
    vol = (a.get('volume_ml') or 700) / 1000.0
    abv = (a.get('abv') or 40) / 100.0
    buy = price_nzd * PREMIUM * NZD_AUD
    freight = FREIGHT * n
    duty = EXCISE_LAL * vol * abv * n
    gst = GST * (buy + freight + duty)
    landed = buy + freight + duty + gst
    resale = a.get('au_resale_estimate_aud') or 0
    net = resale * (1 - AWA_SELL)
    profit = net - landed
    ents = a.get('entries', [])
    au_sold = [e for e in ents if e['kind'] == 'SOLD' and e.get('country', '').upper().startswith('AU') and e.get('same_item') in ('yes', 'close')]
    rows.append({
        'lot_id': lid, 'lot_label': a.get('lot_label'), 'title': lots.get(lid, {}).get('title'), 'bottling': a.get('bottling'),
        'bottles': n, 'price_nzd': price_nzd, 'current_bid_nzd': b.get('current_bid'), 'bid_count': b.get('bid_count'),
        'buy_aud': round(buy), 'freight_aud': round(freight), 'duty_aud': round(duty), 'gst_aud': round(gst), 'landed_aud': round(landed),
        'resale_aud': resale, 'net_aud': round(net), 'profit_aud': round(profit), 'roi': round(profit / landed, 2) if landed else 0,
        'au_sold_n': len(au_sold), 'au_sold_verified_n': sum(1 for e in au_sold if e.get('verified') == 'page opened'),
        'estimate_basis': a.get('estimate_basis'), 'entries': ents, 'search_status': a.get('search_status'),
        # the highest Webb's hammer that still breaks even after all costs
        'breakeven_hammer_nzd': max(0, int(((net / (1 + GST)) - freight - duty) / PREMIUM / NZD_AUD)) if resale else 0,
    })

rows.sort(key=lambda r: -r['profit_aud'])
json.dump({'params': {'NZD_AUD': NZD_AUD, 'premium': PREMIUM, 'freight_aud': FREIGHT, 'excise_per_lal': EXCISE_LAL, 'gst': GST, 'awa_sell_fees': AWA_SELL},
           'rows': rows}, open(f'{W}/webbs{AID}_flip.json', 'w'), indent=0)
pos = [r for r in rows if r['profit_aud'] > 0 and r['au_sold_n'] > 0]
print('lots priced', len(rows), 'positive with AU sold evidence', len(pos))
for r in rows[:25]:
    print(r['lot_label'], '| NZ$', r['price_nzd'], '| landed A$', r['landed_aud'], '| resale A$', r['resale_aud'], '| profit A$', r['profit_aud'], '| AU sold', r['au_sold_n'], '|', (r['bottling'] or '')[:60])
