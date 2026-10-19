#!/usr/bin/env python3
"""Usage: python3 -I build_sold_db.py
Collects every SOLD comp found so far (all *_result.json) into sold_db.json, one row per sale, de-duplicated.
Rows keep: what the lot was, price (aud_price = hammer), date, venue, url, note, the lot it was found for.
UNSOLD and ASKING entries are counted but not stored as sales."""
import json, glob, os, re, collections
W = os.path.dirname(os.path.abspath(__file__))
rows, seen, kinds = [], set(), collections.Counter()
for f in sorted(glob.glob(f'{W}/*_result.json')):
    src = os.path.basename(f).replace('_result.json', '')
    for p in json.load(open(f)).get('lots', []):
        for e in p.get('sold') or []:
            note = (e.get('note') or '').strip()
            kind = 'SOLD' if note.upper().startswith('SOLD') else 'UNSOLD' if note.upper().startswith(('UNSOLD', 'PASSED')) else 'ASKING' if note.upper().startswith('ASKING') else 'OTHER'
            kinds[kind] += 1
            if kind != 'SOLD' or not (e.get('aud_price') or 0) > 0: continue
            k = (e.get('url'), e.get('aud_price'), str(e.get('date')))
            if k in seen: continue
            seen.add(k)
            rows.append(dict(item=(p.get('what_it_is') or '')[:140], aud_hammer=e['aud_price'], price_text=e.get('price'), date=e.get('date'),
                             venue=e.get('venue'), url=e.get('url'), note=note[:300], found_for=f"{src} lot {p.get('lot')}"))
json.dump(rows, open(f'{W}/sold_db.json', 'w'), indent=1)
print(len(rows), 'distinct SOLD rows;', dict(kinds))
