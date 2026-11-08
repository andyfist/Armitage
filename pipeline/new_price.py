#!/usr/bin/env python3
"""Usage: python3 -I pipeline/new_price.py promote <saledir> <results.json> [--floor 500]
       python3 -I pipeline/new_price.py list <saledir>

The new-price check (Andy, 8 Nov 2026). Lot 1704 of the 11 Nov 2026 Armitage sale, a Waratah
Thumpa pneumatic star post driver that costs about $2,700 new, was skipped by the photo scan as
a "modern farm tool". Now every skipped lot that names a brand or a model (merge_scan.py lists
them as "products") gets its current new retail price looked up by an agent in the funnel
(pipeline/wf_funnel.js, phase "New price").

promote: reads the agent's results file, a JSON list of
    {"cdid", "lot", "product", "new_price_aud", "retailer", "url", "note"}
and writes scans/newprice_<name>.json with every lot whose new price is at least --floor
(rules.NEW_PRICE_FLOOR, $500) turned into a CANDIDATE, so assess.py researches it and the
Chrome list picks it up. It also records the new price as an ASKING entry ("new retail
price") in market/<cdid>.json. A new price never sets a maximum: only a SOLD price does.
Prints the promoted lots as JSON.

list: prints every lot already promoted in this sale.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules  # noqa: E402


def scan_record(D, cdid):
    """The lot's latest scan record (scans/*.json), falling back to its lot record."""
    rec = None
    for f in sorted(glob.glob(os.path.join(D, 'scans', '*.json'))):
        if os.path.basename(f).startswith('newprice_'):
            continue
        for r in json.load(open(f)):
            if r.get('cdid') == cdid and r.get('state') == 'SCANNED':
                rec = r
    if rec is None and os.path.exists(os.path.join(D, 'lots', f'{cdid}.json')):
        rec = json.load(open(os.path.join(D, 'lots', f'{cdid}.json')))
    return rec


def promote(D, src, floor):
    results = json.load(open(src))
    if isinstance(results, dict):
        results = results.get('checked') or results.get('results') or []
    out = []
    for x in results:
        try:
            cdid, price = int(x.get('cdid')), float(x.get('new_price_aud') or 0)
        except (TypeError, ValueError):
            continue
        if price < floor or not x.get('url'):
            continue
        r = dict(scan_record(D, cdid) or {'cdid': cdid, 'lot': x.get('lot'), 'title': x.get('product')})
        r.update({'state': 'PROMOTED', 'verdict': 'CANDIDATE', 'strength': max(int(r.get('strength') or 0), 7),
                  'new_price_aud': price, 'new_price_url': x.get('url'), 'product': x.get('product') or r.get('product'),
                  'reason': f"new-price check: {x.get('product')} costs about ${price:,.0f} new ({x.get('retailer') or x.get('url')}); "
                            f"the scan had said: {r.get('reason') or 'SKIP'}"})
        out.append(r)
        mf = os.path.join(D, 'market', f'{cdid}.json')
        m = json.load(open(mf)) if os.path.exists(mf) else {'cdid': cdid, 'lot': r.get('lot'), 'identification': x.get('product'), 'entries': []}
        if not any(e.get('url') == x.get('url') and e.get('kind') == 'ASKING' for e in m.get('entries', [])):
            m.setdefault('entries', []).append({'kind': 'ASKING', 'price': f"A${price:,.0f} new", 'currency': 'AUD', 'aud_price': price,
                                                'date': x.get('date') or 'current', 'venue': x.get('retailer') or 'retailer', 'url': x.get('url'),
                                                'same_item': 'yes', 'note': f"new retail price, not a resale price. {x.get('note') or ''}".strip(),
                                                'via': 'new_price'})
            os.makedirs(os.path.dirname(mf), exist_ok=True)
            json.dump(m, open(mf, 'w'), indent=1)
    name = os.path.splitext(os.path.basename(src))[0]
    os.makedirs(os.path.join(D, 'scans'), exist_ok=True)
    json.dump(out, open(os.path.join(D, 'scans', f'newprice_{name}.json'), 'w'), indent=1)
    print(json.dumps([{k: r.get(k) for k in ('cdid', 'lot', 'title', 'product', 'new_price_aud', 'reason', 'findings', 'condition', 'strength')} for r in out]))


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ('promote', 'list'):
        sys.exit(__doc__)
    floor = rules.NEW_PRICE_FLOOR
    if '--floor' in a:
        i = a.index('--floor')
        floor = float(a[i + 1])
        del a[i:i + 2]
    if a[0] == 'promote':
        promote(a[1], a[2], floor)
    else:
        print(json.dumps([r for f in glob.glob(os.path.join(a[1], 'scans', 'newprice_*.json')) for r in json.load(open(f))], indent=1))


if __name__ == '__main__':
    main()
