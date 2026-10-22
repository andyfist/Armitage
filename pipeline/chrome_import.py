#!/usr/bin/env python3
"""Usage: python3 pipeline/chrome_import.py <chid> <chrome_results.json>

Merges the findings of a Chrome research session (the file described in chrome_brief.md)
into the sale's market files: each entry is added to pipeline/sales/<chid>/market/<cdid>.json
tagged "via": "chrome" (a lot with no market file yet gets one), identification and
viewing_check are updated, and every SOLD entry is also appended to
pipeline/state/chrome_sold.json so the results database keeps it. Run pipeline/assess.py
afterwards for the final maximums. Importing the same file twice adds nothing twice.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLD = os.path.join(ROOT, 'pipeline', 'state', 'chrome_sold.json')


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    chid, src = sys.argv[1], sys.argv[2]
    D = os.path.join(ROOT, 'pipeline', 'sales', chid)
    results = json.load(open(src))
    if isinstance(results, dict):
        results = results.get('lots') or results.get('results') or [results]
    sold_db = json.load(open(SOLD)) if os.path.exists(SOLD) else []
    known = {(s.get('url'), s.get('aud_hammer')) for s in sold_db}
    added, lots = 0, 0
    for r in results:
        cdid = r.get('cdid')
        if not cdid:
            continue
        mf = os.path.join(D, 'market', f'{cdid}.json')
        m = json.load(open(mf)) if os.path.exists(mf) else {'cdid': cdid, 'lot': r.get('lot'), 'identification': '', 'entries': [], 'searches_tried': ''}
        have = {(e.get('url'), e.get('aud_price'), e.get('kind')) for e in m['entries']}
        for e in r.get('entries', []):
            key = (e.get('url'), e.get('aud_price'), e.get('kind'))
            if key in have or not e.get('url'):
                continue
            e = dict(e)
            e['via'] = 'chrome'
            e.setdefault('same_item', 'yes')
            m['entries'].append(e)
            have.add(key)
            added += 1
            if e.get('kind') == 'SOLD' and (e.get('url'), e.get('aud_price')) not in known:
                sold_db.append({'chid': chid, 'cdid': cdid, 'lot': r.get('lot'), 'item': r.get('identification') or m.get('identification'),
                                'aud_hammer': e.get('aud_price'), 'date': e.get('date'), 'venue': e.get('venue'), 'url': e.get('url'),
                                'match': e.get('same_item', 'yes'), 'note': e.get('note', '')})
                known.add((e.get('url'), e.get('aud_price')))
        if r.get('identification'):
            m['identification'] = r['identification']
        if r.get('viewing_check'):
            m['viewing_check'] = r['viewing_check']
        if r.get('searches_tried'):
            m['searches_tried'] = (m.get('searches_tried') or '') + ' | chrome: ' + r['searches_tried']
        m['needs_chrome'] = False
        m['chrome_done'] = True
        os.makedirs(os.path.dirname(mf), exist_ok=True)
        json.dump(m, open(mf, 'w'), indent=1)
        lots += 1
    os.makedirs(os.path.dirname(SOLD), exist_ok=True)
    json.dump(sold_db, open(SOLD, 'w'), indent=1)
    print(f'{lots} lots updated, {added} entries added; chrome_sold.json now holds {len(sold_db)} sold prices. Now run: python3 pipeline/assess.py {chid}')


if __name__ == '__main__':
    main()
