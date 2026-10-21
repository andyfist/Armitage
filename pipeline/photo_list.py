#!/usr/bin/env python3
"""Usage: python3 pipeline/photo_list.py <chid>

Writes pipeline/sales/<chid>/photo_list.md, the list Andy takes to the viewing: one line
per lot worth bidding on or still undecided, in lot order, with exactly what to look at or
photograph (from the researchers' viewing_check and the scan's condition notes), the
provisional maximum and the closing time. Prints the email that points Andy to it and
tells him how to send the photos back (a new chat in the project).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://armitage.bidsonline.com.au'


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    chid = sys.argv[1]
    D = os.path.join(ROOT, 'pipeline', 'sales', chid)
    cat = json.load(open(os.path.join(D, 'cat.json')))
    a = json.load(open(os.path.join(D, 'assessment.json')))
    rows = []
    for x in a['lots']:
        if x['status'] not in ('PASS', 'CHROME'):
            continue
        mf = os.path.join(D, 'market', f"{x['cdid']}.json")
        m = json.load(open(mf)) if os.path.exists(mf) else {}
        check = (m.get('viewing_check') or '').strip()
        if check.lower() in ('', 'nothing', 'none', 'n/a'):
            check = ''
        cond = (x.get('condition') or '').strip()
        rows.append({'lot': x['lot'], 'cdid': x['cdid'], 'title': x['title'], 'status': x['status'], 'max': x.get('max_hammer') or 0,
                     'bid': x.get('current_bid') or 0, 'close': x.get('close') or '', 'check': check, 'condition': cond,
                     'what': (x.get('identification') or '')[:160]})
    rows.sort(key=lambda r: (r['lot'] or 0))
    need_photo = [r for r in rows if r['check']]

    out = [f"# Armitage {cat['name']}: viewing list", '',
           f"{len(rows)} lots to look at ({sum(1 for r in rows if r['status'] == 'PASS')} pass the $200 rule on current evidence, "
           f"{sum(1 for r in rows if r['status'] == 'CHROME')} still need a price). {len(need_photo)} need a specific photo or check. "
           f"Lots close from {cat.get('close_first')} to {cat.get('close_last')}. Viewing at 9 Goodman Crt, Invermay.", '',
           'Photograph everything in daylight: the whole item, then the detail asked for. Upload the photos in a new chat in the Auction scans project, '
           f'saying "viewing photos for Armitage {chid}", and name each photo by lot number (for example 924-title-page.jpg).', '',
           '| Lot | What it is | Look at / photograph | Max (provisional) | Bid now | Closes |', '|---|---|---|---|---|---|']
    for r in rows:
        what = r['what'] or r['title']
        check = r['check'] or ('general condition: ' + r['condition'] if r['condition'] else 'general condition and completeness')
        out.append(f"| {r['lot']} | {what} | {check} | {'$' + format(r['max'], ',') if r['max'] else 'none yet'} | ${r['bid']:,.0f} | {r['close']} |")
    out += ['', f"Lot pages: {BASE}/catalogue-group.aspx?chid={chid}"]
    path = os.path.join(D, 'photo_list.md')
    open(path, 'w').write('\n'.join(out) + '\n')

    email = [f"Armitage {cat['name']}: photo request list ready", '',
             f"{len(rows)} lots to look at, {len(need_photo)} of them with a specific photo or check. The list is in the repo at pipeline/sales/{chid}/photo_list.md "
             f"(https://github.com/andyfist/armitage/blob/main/pipeline/sales/{chid}/photo_list.md).", '',
             'The ones that need a specific photo:']
    for r in need_photo[:40]:
        email.append(f"- Lot {r['lot']}: {r['check']} ({r['title'][:50]})")
    if len(need_photo) > 40:
        email.append(f"... and {len(need_photo) - 40} more in the list")
    email += ['', f'To send the photos: start a new chat in the Auction scans project saying "viewing photos for Armitage {chid}" and upload them there. '
              'You get an answer on each lot as the photos arrive.',
              f"Lots close from {cat.get('close_first')} to {cat.get('close_last')}."]
    print('\n'.join(email))


if __name__ == '__main__':
    main()
