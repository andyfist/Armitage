"""Read every price database in this folder, and look items up from the command line.

In code:
    sys.path.insert(0, 'databases'); from load import records
    for r in records(category='coins'): ...

Command line (all words must appear in title or description):
    python3 -I databases/load.py 1930 penny
    python3 -I databases/load.py sturt expeditions --min 250 --sold
"""
import argparse
import glob
import gzip
import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))


def records(source=None, category=None):
    """Yield every record from databases/<source>/sale_*.json[.gz]."""
    for path in sorted(glob.glob(os.path.join(HERE, '*', 'sale_*.json*'))):
        if source and os.path.basename(os.path.dirname(path)) != source:
            continue
        opener = gzip.open if path.endswith('.gz') else open
        with opener(path, 'rt', encoding='utf-8') as f:
            for r in json.load(f):
                if category is None or r.get('category') == category:
                    yield r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('words', nargs='+')
    ap.add_argument('--source')
    ap.add_argument('--category', choices=['coins', 'books', 'stamps', 'other'])
    ap.add_argument('--min', type=float, default=0, help='minimum hammer')
    ap.add_argument('--sold', action='store_true', help='sold lots only')
    ap.add_argument('--limit', type=int, default=40)
    a = ap.parse_args()
    words = [w.lower() for w in a.words]
    hits = []
    for r in records(a.source, a.category):
        text = (r['title'] + ' ' + r['description']).lower()
        if all(w in text for w in words) and r['hammer_aud'] >= a.min and (not a.sold or not r['unsold']):
            hits.append(r)
    hits.sort(key=lambda r: r['date'] or '', reverse=True)
    for r in hits[:a.limit]:
        price = 'UNSOLD' if r['unsold'] else f"${r['hammer_aud']:,.0f}"
        print(f"{r['date']}  {r['source']} {r['sale']}/{r['lot']}  {price:>9}  {r['description'][:150]}")
    sold = [r['hammer_aud'] for r in hits if not r['unsold']]
    if sold:
        print(f'\n{len(hits)} hits, {len(sold)} sold: low ${min(sold):,.0f}, median ${statistics.median(sold):,.0f}, '
              f'high ${max(sold):,.0f} (hammer; eBay prices already include everything the buyer paid, other houses add a buyer\'s premium)')
    else:
        print(f'\n{len(hits)} hits, none sold')


if __name__ == '__main__':
    main()
