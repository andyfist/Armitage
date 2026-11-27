#!/usr/bin/env python3
"""Usage: python3 pipeline/chrome_import.py <chid> <chrome_results.json | results folder | results .zip> [...]

A folder or zip (the results_<pack>/ folder an all-lots Chrome pack writes, one <chunk>.json per
5 lots) is read whole. Results for other catalogues (their "chid" field) are skipped, so the
same folder can be imported once per catalogue. When a lot was done twice (a Sonnet helper
handed it back to an Opus helper), both sets of prices are kept and the Opus identification wins.

Merges the findings of a Chrome research session (the file described in chrome_brief.md)
into the sale's market files: each entry is added to pipeline/sales/<chid>/market/<cdid>.json
tagged "via": "chrome" (a lot with no market file yet gets one), identification and
viewing_check are updated, and every SOLD entry is also appended to
pipeline/state/chrome_sold.json so the results database keeps it. Run pipeline/assess.py
afterwards for the final maximums. Importing the same file twice adds nothing twice.
"""
import glob
import json
import os
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLD = os.path.join(ROOT, 'pipeline', 'state', 'chrome_sold.json')


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    chid = sys.argv[1]
    D = os.path.join(ROOT, 'pipeline', 'sales', chid)
    results = []
    for src in sys.argv[2:]:
        if src.endswith('.zip'):
            tmp = tempfile.mkdtemp()
            zipfile.ZipFile(src).extractall(tmp)
            src = tmp
        files = sorted(glob.glob(os.path.join(src, '**', '*.json'), recursive=True)) if os.path.isdir(src) else [src]
        for f in files:
            try:
                got = json.load(open(f))
            except (ValueError, OSError) as e:
                print(f'{f}: not readable JSON ({e}), skipped', file=sys.stderr)
                continue
            if isinstance(got, dict):
                got = got.get('lots') or got.get('results') or [got]
            results += [r for r in got if isinstance(r, dict)]
    results = [r for r in results if str(r.get('chid') or chid) == str(chid)]
    results.sort(key=lambda r: 1 if 'opus' in str(r.get('model_used') or '').lower() else 0)  # Opus last, so it wins
    sold_db = json.load(open(SOLD)) if os.path.exists(SOLD) else []
    known = {(s.get('url'), s.get('aud_hammer')) for s in sold_db}
    # a results file with no cdids (the brief once left them out) is matched on lot number:
    # the Chrome list first, since Gowans can give several lots the same number
    by_lot = {}
    for f in ('lots.json', 'chrome_list.json'):
        p = os.path.join(D, f)
        rows = json.load(open(p)) if os.path.exists(p) else []
        if isinstance(rows, dict):
            rows = rows.get('lots', [])
        seen = {}
        for x in rows:
            seen.setdefault(str(x.get('lot')), set()).add(x['cdid'])
        by_lot.update({k: v.pop() for k, v in seen.items() if len(v) == 1})
    added, lots = 0, 0
    for r in results:
        cdid = r.get('cdid') or by_lot.get(str(r.get('lot')))
        if not r.get('cdid') and r.get('lot') is not None and not cdid:
            print(f"lot {r.get('lot')}: no cdid and the lot number is not unique, skipped", file=sys.stderr)
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
            si = str(e.get('same_item') or '').strip().lower()  # assess.py needs exactly yes or close
            e['same_item'] = 'yes' if si.startswith('yes') else 'close' if si.startswith('close') else (si or 'yes')
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
