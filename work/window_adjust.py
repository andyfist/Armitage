#!/usr/bin/env python3
"""Recompute keep/flip maximum bids using SOLD entries from the last N years (default 10) instead of 24 months.
Usage: python3 -I window_adjust.py [years]. Idempotent: the original 24-month values are kept in keep_max_24m / flip_max_24m. A wider window only ADDS maximums for lots that had none.
Only SOLD entries already collected and verified are used (same item or close, not 'category guide'); older entries the
verifier dropped are not recovered. Rule unchanged: keep = lowest qualifying SOLD aud_price / 1.22, flip = / 2.44, rounded down."""
import json, re, sys, math
W = '/home/user/Armitage/work'; YEARS = int(sys.argv[1]) if len(sys.argv) > 1 else 10
MIN_YEAR = 2026 - YEARS
FILES = ['armitage28839', 'armitage28840', 'armitage28841', 'armitage28842', 'armitage28838']
def qualifies(e):
    n = (e.get('note') or '')
    if re.search(r'category guide|snippet only|lead only|not verified|different (title|item)', n, re.I) and not re.search(r'same_item:?\s*(yes|close)', n, re.I): return False
    return bool(re.search(r'same[_ ]item:?\s*(yes|close)|SOLD,? (same|close)|\bclose\b|same item', n, re.I)) and not re.search(r'category guide', n, re.I)
def ym(e):
    d = str(e.get('date') or '')
    m = re.search(r'(20\d\d)-(\d\d)', d) or None
    if m: return int(m.group(1)), int(m.group(2))
    m = re.search(r'\d{1,2}/(\d{1,2})/(20\d\d)', d)
    if m: return int(m.group(2)), int(m.group(1))
    m = re.search(r'(20\d\d)', d)
    return (int(m.group(1)), 6) if m else (0, 0)
def year(e):
    m = re.findall(r'(20\d\d|19\d\d)', str(e.get('date') or '')); return int(m[0]) if m else None
# excluded after review: comp is a different vintage (826) / covers one book of a ten-book lot (25)
SKIP = {('armitage28839', 826), ('armitage28838', 25)}
changes = []
for f in FILES:
    P = f'{W}/{f}_result.json'; R = json.load(open(P))
    for l in R['lots']:
        if 'keep_max_24m' not in l: l['keep_max_24m'] = l.get('keep_max_hammer') or 0; l['flip_max_24m'] = l.get('flip_max_hammer') or 0
        old_k, old_f = l['keep_max_24m'], l['flip_max_24m']
        if (f, l['lot']) in SKIP:
            l['keep_max_hammer'], l['flip_max_hammer'] = old_k, old_f; continue
        pool = [e for e in (l.get('sold') or []) if qualifies(e) and (e.get('aud_price') or 0) > 0 and (year(e) or 0) >= MIN_YEAR]
        old_window = [e for e in pool if ym(e) >= (2024, 11)]
        if old_k > 0 or old_window or not pool:
            l['keep_max_hammer'], l['flip_max_hammer'] = old_k, old_f; continue   # only lots whose answer is blocked by the 24-month limit change
        low = min(e['aud_price'] for e in pool)
        if low >= 820 and len(pool) < 2:
            l['keep_max_hammer'], l['flip_max_hammer'] = old_k, old_f; continue   # a single older sale is too thin for a maximum over $1,000
        new_k, new_f = math.floor(low / 1.22), math.floor(low / 2.44)
        if (new_k, new_f) != (old_k, old_f):
            l['working'] = re.sub(r' \| \d+-YEAR WINDOW.*$', '', l.get('working') or '') + f" | {YEARS}-YEAR WINDOW (your instruction, replacing the 24-month rule): lowest same or close SOLD since {MIN_YEAR} is A${low:.0f} ({'; '.join(sorted({(e.get('venue') or '')[:30]+' '+str(e.get('date'))[:12] for e in pool if e['aud_price'] == low}))}); keep = {low:.0f} / 1.22 = {new_k}, flip = {low:.0f} / 2.44 = {new_f}. Was keep {old_k}, flip {old_f}."
            if l.get('triage') in ('LOOK AT VIEWING', 'NEAR MISS') and new_k > 0:
                l['triage'] = 'KEEP'; l['confidence'] = 'Low'
            l['keep_max_hammer'], l['flip_max_hammer'] = new_k, new_f
            changes.append((f, l['lot'], old_k, old_f, new_k, new_f, round(low), (l.get('what_it_is') or '')[:50]))
    json.dump(R, open(P, 'w'), indent=1)
json.dump(changes, open(f'{W}/window_changes.json', 'w'))
print(len(changes), 'lots changed')
for c in sorted(changes, key=lambda c: -(c[4] - c[2])): print(f"{c[0][-5:]} lot {c[1]}: keep {c[2]} -> {c[4]}, flip {c[3]} -> {c[5]} (lowest {c[6]}) {c[7]}")
