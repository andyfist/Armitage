"""Noble Numismatics (Sydney) prices realised: Australian and world coins, banknotes, medals, tokens.

Source: https://www.noble.com.au/auctions lists every sale with a "prices realised" page
(sales 44 to now, plus specials such as 888 and 889). Each page holds every lot of that
sale with its description and hammer price, or "Passed in".

Writes databases/noble/sale_<n>.json.gz (gzipped; one list of common records per sale) and
databases/noble_state.json (which sales are done). Rerun any time: only sales not yet
saved, or saved with no lots, are fetched again.

    python3 -I databases/noble.py            # everything new
    python3 -I databases/noble.py --max 5    # at most 5 sales this run
    python3 -I databases/noble.py --sale 142 # refetch one sale
"""
import argparse
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, BlockedError, Fetcher, clean, load_json, log, money, parse_date, save_json, save_records  # noqa: E402

BASE = 'https://www.noble.com.au'
OUT = os.path.join(HERE, 'noble')
STATE = os.path.join(HERE, 'noble_state.json')

ROW = re.compile(
    r'<td class="prices-realised__cell-lot">\s*<a href="([^"]+)"[^>]*>\s*Lot\s+([^<]+?)\s*</a>\s*</td>\s*'
    r'<td class="prices-realised__cell-desc">(.*?)</td>\s*'
    r'<td class="prices-realised__cell-price">(.*?)</td>', re.S)


def list_sales(f):
    page = f.get(BASE + '/auctions')
    return sorted({int(n) for n in re.findall(r'href="/auctions/sale/(\d+)/prices-realised"', page)})


def parse_sale(sale, page):
    dates = re.search(r'prices-realised__dates">([^<]*)<', page)
    date = parse_date(clean(dates.group(1))) if dates else None
    title = re.search(r'prices-realised__sale-title">([^<]*)<', page)
    sale_title = clean(title.group(1)) if title else ''
    recs = []
    for href, lot, desc, price in ROW.findall(page):
        strong = re.search(r'<strong>(.*?)</strong>', desc, re.S)
        description = clean(desc)
        head = clean(strong.group(1)).rstrip(',') if strong else ''
        # title: the bold heading plus the start of the description, enough to match on
        rest = description[len(clean(strong.group(1))):].strip(' ,') if strong else description
        lot_title = (head + ': ' + rest if head else rest)[:120]
        hammer = money(clean(price))
        recs.append({
            'source': 'noble',
            'sale': sale,
            'lot': lot.strip(),
            'date': date,
            'title': lot_title,
            'description': description,
            'hammer_aud': hammer or 0.0,
            'premium_included': False,
            'unsold': not hammer,  # old sales show passed lots as $0
            'url': BASE + href,
            'category': 'coins',
            'sale_title': sale_title,
        })
    return recs, date


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max', type=int, default=0, help='stop after this many sales')
    ap.add_argument('--sale', type=int, action='append', help='refetch these sales')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    state = load_json(STATE, {'sales': {}})
    f = Fetcher()
    try:
        sales = a.sale or list_sales(f)
    except BlockedError as e:
        log('STOPPED, blocked:', e)
        state['blocked'] = str(e)
        save_json(STATE, state, indent=1)
        return 2
    todo = [s for s in sales if a.sale or not state['sales'].get(str(s), {}).get('lots')]
    todo.sort(reverse=True)  # newest first: most relevant prices
    log(f'{len(sales)} sales listed, {len(todo)} to fetch')
    done = 0
    for s in todo:
        if a.max and done >= a.max:
            break
        try:
            page = f.get(f'{BASE}/auctions/sale/{s}/prices-realised')
        except BlockedError as e:
            log('STOPPED, blocked:', e)
            state['blocked'] = str(e)
            break
        if page is None:
            log(f'sale {s}: no page (404)')
            state['sales'][str(s)] = {'lots': 0, 'missing': True, 'checked': time.strftime('%Y-%m-%d')}
            continue
        recs, date = parse_sale(s, page)
        save_records(os.path.join(OUT, f'sale_{s:03d}.json.gz'), recs)
        sold = sum(1 for r in recs if not r['unsold'])
        state['sales'][str(s)] = {'lots': len(recs), 'sold': sold, 'date': date,
                                  'fetched': time.strftime('%Y-%m-%d')}
        state.pop('blocked', None)
        save_json(STATE, state, indent=1)
        done += 1
        log(f'sale {s} ({date}): {len(recs)} lots, {sold} sold')
    save_json(STATE, state, indent=1)
    total = sum(v.get('lots', 0) for v in state['sales'].values())
    log(f'done this run: {done} sales; database now {total} lots in {len(state["sales"])} sales')
    return 0


if __name__ == '__main__':
    sys.exit(main())
