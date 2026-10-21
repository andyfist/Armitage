#!/usr/bin/env python3
"""Usage: python3 pipeline/assess.py <chid> [--profit 200] [--fee 0.15] [--premium 0.22] [--months 24]

The bid check, in code, no AI. Reads one sale's funnel output (pipeline/sales/<chid>/):
scans/*.json (which lots are candidates and how strong), market/<cdid>.json (the price
evidence the researchers found) and bids.json (current bid), and applies the rule agreed
on 21 Oct 2026: a lot only gets a maximum bid if there is a SOLD price with a link and a
date behind it, and that bid must still leave at least $200 net profit after the buyer's
premium and the selling fees.

  net resale  = median same-item SOLD price (AUD, last --months) x (1 - fee)
  max hammer  = (net resale - profit) / (1 + premium), rounded down to $5

Writes assessment.json, chrome_list.json (lots for the browser research on the home
computer) and assessment_email.txt, and prints the email.
"""
import argparse
import datetime
import glob
import json
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTHS = {m: i + 1 for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}


def money(s):
    m = re.search(r'[\d,]+(?:\.\d+)?', str(s or ''))
    return float(m.group(0).replace(',', '')) if m else 0.0


def entry_date(text):
    """Best-effort date from the free text researchers write ('Nov 2025', '2025-11-03', '3 Nov 2025', 'live, seen 21 Oct 2026')."""
    t = str(text or '')
    m = re.search(r'(20\d\d)-(\d\d)(?:-(\d\d))?', t)
    if m:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1))
    m = re.search(r'(\d{1,2})?[ /]?([A-Za-z]{3})[a-z]*\.? ?(20\d\d)', t)
    if m and m.group(2).lower()[:3] in MONTHS:
        return datetime.date(int(m.group(3)), MONTHS[m.group(2).lower()[:3]], int(m.group(1) or 1))
    m = re.search(r'(\d{1,2})/(\d{1,2})/(20\d\d)', t)
    if m:
        return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = re.search(r'\b(20\d\d)\b', t)
    if m:
        return datetime.date(int(m.group(1)), 6, 30)
    return None


def round_down5(x):
    return int(max(x, 0) // 5 * 5)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('chid')
    ap.add_argument('--profit', type=float, default=200, help='minimum net profit in dollars (default 200)')
    ap.add_argument('--fee', type=float, default=0.15, help='selling fees as a fraction of the resale price (default 0.15)')
    ap.add_argument('--premium', type=float, default=0.22, help="Armitage buyer's premium incl. GST (default 0.22)")
    ap.add_argument('--months', type=int, default=24, help='only SOLD prices this recent count (default 24)')
    ap.add_argument('--top', type=int, default=25, help='lots listed in the email (default 25)')
    args = ap.parse_args()
    D = os.path.join(ROOT, 'pipeline', 'sales', args.chid)
    cat = json.load(open(os.path.join(D, 'cat.json'))) if os.path.exists(os.path.join(D, 'cat.json')) else {'name': f'catalogue {args.chid}'}
    bids = json.load(open(os.path.join(D, 'bids.json'))) if os.path.exists(os.path.join(D, 'bids.json')) else {}
    today = datetime.date.today()
    cutoff = today - datetime.timedelta(days=30 * args.months)

    # candidates from the scans (strength = the rescored value if a rescore file exists)
    scanned, cands = 0, {}
    for f in glob.glob(os.path.join(D, 'scans', '*.json')):
        for r in json.load(open(f)):
            if r.get('state') == 'SCANNED':
                scanned += 1
            if r.get('verdict') == 'CANDIDATE':
                cands[r['cdid']] = r
    for f in glob.glob(os.path.join(D, 'titles', 'rescore_*.json')):
        try:
            for s in json.load(open(f)).get('scores', []):
                if s['cdid'] in cands:
                    cands[s['cdid']].update(strength_scan=cands[s['cdid']].get('strength'), strength=s['score'], rescore_note=s.get('rationale'))
        except Exception:
            pass

    lots = []
    for cdid, c in sorted(cands.items(), key=lambda kv: kv[1].get('lot') or 0):
        mf = os.path.join(D, 'market', f'{cdid}.json')
        m = json.load(open(mf)) if os.path.exists(mf) else None
        b = bids.get(str(cdid), {})
        current = money(b.get('current_bid'))
        out = {'cdid': cdid, 'lot': c.get('lot'), 'title': c.get('title'), 'strength': c.get('strength'), 'findings': c.get('findings'),
               'condition': c.get('condition'), 'current_bid': current, 'bid_count': b.get('bid_count'), 'close': b.get('close'),
               'identification': (m or {}).get('identification'), 'researched': m is not None, 'needs_chrome': bool((m or {}).get('needs_chrome')),
               'chrome_hint': (m or {}).get('chrome_hint', ''), 'sold': [], 'sold_old': [], 'unsold': [], 'asking': [], 'resale': 0,
               'net_resale': 0, 'max_hammer': 0, 'status': '', 'why': ''}
        for e in (m or {}).get('entries', []):
            price = float(e.get('aud_price') or 0)
            same = str(e.get('same_item', '')).lower()
            rec = {'aud_price': price, 'date': e.get('date'), 'venue': e.get('venue'), 'url': e.get('url'), 'same_item': same, 'note': e.get('note', '')}
            if e.get('kind') == 'SOLD' and price > 0 and e.get('url') and same in ('yes', 'close') and 'snippet only' not in str(e.get('note', '')).lower():
                d = entry_date(e.get('date'))
                (out['sold'] if (d is None or d >= cutoff) else out['sold_old']).append(rec)
            elif e.get('kind') == 'UNSOLD':
                out['unsold'].append(rec)
            elif e.get('kind') == 'ASKING':
                out['asking'].append(rec)
        if out['sold']:
            prices = sorted(x['aud_price'] for x in out['sold'])
            out['resale'] = statistics.median(prices)
            out['net_resale'] = out['resale'] * (1 - args.fee)
            out['max_hammer'] = round_down5((out['net_resale'] - args.profit) / (1 + args.premium))
            if out['max_hammer'] >= max(current, 5):
                out['status'] = 'PASS'
                out['why'] = (f"{len(prices)} same-item SOLD price(s), median ${out['resale']:,.0f}; less {args.fee:.0%} fees = ${out['net_resale']:,.0f}; "
                              f"less ${args.profit:,.0f} profit, / {1 + args.premium:.2f} premium = max hammer ${out['max_hammer']:,}")
            else:
                out['status'] = 'FAIL'
                out['why'] = f"max hammer ${out['max_hammer']:,} from a median SOLD of ${out['resale']:,.0f} does not clear the current bid ${current:,.0f}"
        elif m is None:
            out['status'] = 'NOT RESEARCHED'
            out['why'] = 'no market file'
        elif out['sold_old'] or out['asking'] or out['unsold'] or out['needs_chrome'] or (out['strength'] or 0) >= 6:
            out['status'] = 'CHROME'
            out['why'] = 'no recent same-item SOLD price in the cloud sources; ' + ('researcher asked for eBay/signed-in sites' if out['needs_chrome'] else
                         'older sold, asking or unsold evidence only' if (out['sold_old'] or out['asking'] or out['unsold']) else 'strong photo score')
        else:
            out['status'] = 'DROP'
            out['why'] = 'no sold evidence and a weak photo score'
        lots.append(out)

    chrome = [x for x in lots if x['status'] in ('PASS', 'CHROME')]
    # browser research goes to every lot that passes or might pass, best prospects first
    chrome.sort(key=lambda x: (-(x['max_hammer'] or 0), -(x['strength'] or 0)))
    counts = {s: sum(1 for x in lots if x['status'] == s) for s in ('PASS', 'CHROME', 'FAIL', 'DROP', 'NOT RESEARCHED')}
    result = {'chid': args.chid, 'name': cat.get('name'), 'assessed': today.isoformat(), 'rule': vars(args), 'scanned': scanned,
              'candidates': len(lots), 'counts': counts, 'lots': lots}
    json.dump(result, open(os.path.join(D, 'assessment.json'), 'w'), indent=1)
    json.dump([{k: x[k] for k in ('cdid', 'lot', 'title', 'status', 'strength', 'max_hammer', 'current_bid', 'identification', 'chrome_hint', 'close')} for x in chrome],
              open(os.path.join(D, 'chrome_list.json'), 'w'), indent=1)

    passes = sorted([x for x in lots if x['status'] == 'PASS'], key=lambda x: -(x['max_hammer'] - x['current_bid']))
    lines = [f"First pass done for {cat.get('name')}: {scanned} lots photo-scanned, {len(lots)} candidates researched, "
             f"{counts['PASS']} pass the ${args.profit:,.0f} rule now, {counts['CHROME']} more need the Chrome research.", '']
    if passes:
        lines.append(f"Lots that pass now (max hammer, current bid, what it is):")
        for x in passes[:args.top]:
            lines.append(f"- Lot {x['lot']}: max ${x['max_hammer']:,} (bid ${x['current_bid']:,.0f}, {x['bid_count'] or 0} bids), {x['title']}. "
                         f"{(x['identification'] or '')[:120]} Sold evidence: {len(x['sold'])} price(s), median ${x['resale']:,.0f}.")
        if len(passes) > args.top:
            lines.append(f"... and {len(passes) - args.top} more in assessment.json")
        lines.append('')
    lines.append(f"Chrome list: {len(chrome)} lots in chrome_list.json (passes first, then lots with no sold price yet).")
    lines.append("Maximums are provisional until the Chrome research confirms them. Only a SOLD price with a link and a date sets a maximum.")
    text = '\n'.join(lines)
    open(os.path.join(D, 'assessment_email.txt'), 'w').write(text + '\n')
    print(text)


if __name__ == '__main__':
    sys.exit(main())
