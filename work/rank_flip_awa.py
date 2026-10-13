#!/usr/bin/env python3
# Rank Webb's lots for an NZ -> AU flip using Australian Whisky Auctions results collected in the browser.
# Usage: python3 -I rank_flip_awa.py <aid> <awa_json>
import sys, json, re, statistics

AID, SRC = sys.argv[1], sys.argv[2]
W = '/home/user/Armitage/work'
NZD_AUD = 0.80315
PREMIUM = 1.22425          # Webb's 19.5% + GST on the premium
EXCISE_LAL = 106.0         # A$ per litre of pure alcohol (estimate of spirits duty)
GST = 0.10
AWA_SELL = 0.125           # AWA seller fees incl GST (estimate, check AWA terms)

lots_by_label = {c['lot_label']: c for c in json.load(open(f'{W}/webbs{AID}/all_lots.json'))}
bids = json.load(open(f'{W}/webbs{AID}_bids.json'))['lots']
awa = json.load(open(SRC))


def vol_abv(title):
    t = title or ''
    v = re.search(r'(\d{3,4})\s*ml', t, re.I)
    cl = re.search(r'(\d{2,3})\s*cl\b', t, re.I)
    a = re.search(r'(\d{2}(?:\.\d)?)\s*%', t)
    vol = int(v.group(1)) if v else (int(cl.group(1)) * 10 if cl else 700)
    return vol, float(a.group(1)) if a else 43.0


def nbottles(title):
    m = re.match(r'\s*\((\d+)\)', title or '')
    return int(m.group(1)) if m else 1


rows = []
for e in awa:
    lab = str(e.get('lot'))
    c = lots_by_label.get(lab)
    if not c:
        continue
    b = bids.get(str(c['lot_id']), {})
    price = b.get('asking_bid') or b.get('current_bid')
    res = e.get('results') or []
    yes = [r for r in res if r.get('same_item') == 'yes' and isinstance(r.get('hammer_aud'), (int, float))]
    sold_yes = [r['hammer_aud'] for r in yes if r.get('sold')]
    passed_yes = [r['hammer_aud'] for r in yes if not r.get('sold')]
    close_sold = [r['hammer_aud'] for r in res if r.get('same_item') == 'close' and r.get('sold') and isinstance(r.get('hammer_aud'), (int, float))]
    typical = statistics.median(sold_yes) if sold_yes else 0
    conservative = min(sold_yes + passed_yes) if sold_yes else 0
    vol, abv = vol_abv(c['title'])
    n = nbottles(c['title'])
    buy = (price or 0) * PREMIUM * NZD_AUD
    duty = EXCISE_LAL * vol / 1000 * abv / 100 * n
    landed = (buy + duty) * (1 + GST)

    def profit(resale):
        return round(resale * (1 - AWA_SELL) - landed) if resale else None

    def breakeven(resale):
        if not resale:
            return 0
        return max(0, int((resale * (1 - AWA_SELL) / (1 + GST) - duty) / PREMIUM / NZD_AUD))

    rows.append({
        'n': e.get('n'), 'lot_label': lab, 'lot_id': c['lot_id'], 'title': c['title'], 'bottles': n, 'vol_ml': vol, 'abv': abv,
        'webbs_next_bid_nzd': price, 'current_bid_nzd': b.get('current_bid'), 'webbs_bids': b.get('bid_count'),
        'est_nzd': [b.get('est_low'), b.get('est_high')],
        'landed_aud': round(landed), 'duty_gst_aud': round(duty * (1 + GST) + buy * GST),
        'awa_sold_same': sorted(sold_yes), 'awa_passed_same': sorted(passed_yes), 'awa_sold_close': sorted(close_sold),
        'resale_typical_aud': typical, 'resale_conservative_aud': conservative,
        'profit_typical_aud': profit(typical), 'profit_conservative_aud': profit(conservative),
        'breakeven_hammer_nzd_typical': breakeven(typical), 'breakeven_hammer_nzd_conservative': breakeven(conservative),
        'awa_results': res, 'note': e.get('note', ''),
    })

ranked = sorted([r for r in rows if r['profit_conservative_aud'] is not None], key=lambda r: -r['profit_conservative_aud'])
json.dump({'params': {'NZD_AUD': NZD_AUD, 'premium': PREMIUM, 'excise_per_lal_aud': EXCISE_LAL, 'gst': GST, 'awa_sell_fees': AWA_SELL, 'freight_aud': 0},
           'rows': rows, 'ranked': [r['lot_label'] for r in ranked]}, open(f'{W}/webbs{AID}_flip_awa.json', 'w'), indent=0)
print('bottles', len(rows), 'with same-item AWA sold', len(ranked), 'positive conservative', sum(1 for r in ranked if r['profit_conservative_aud'] > 0), 'positive typical', sum(1 for r in rows if (r['profit_typical_aud'] or 0) > 0))
for r in ranked[:25]:
    print(f"{r['lot_label']:>6} | next NZ${r['webbs_next_bid_nzd']:>6} ({r['webbs_bids']} bids) | landed A${r['landed_aud']:>6} | AWA sold {r['awa_sold_same']} passed {r['awa_passed_same']} | profit cons A${r['profit_conservative_aud']} typ A${r['profit_typical_aud']} | b/e NZ${r['breakeven_hammer_nzd_conservative']}-{r['breakeven_hammer_nzd_typical']} | {r['title'][:55]}")
