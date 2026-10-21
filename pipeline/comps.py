#!/usr/bin/env python3
"""Usage: python3 -I pipeline/comps.py <word> [<word> ...] [--min 0] [--limit 30] [--category coins|books] [--source NAME] [--json]

Looks an item up in every local price database and prints what lots with the same words
sold for: hammer prices with a date and a link or sale/lot reference, newest first, then
the low, median and high. Every word must appear in the lot's title or description.

Sources, all hammer prices with the buyer's premium not included:
  databases/<source>/sale_*.json[.gz]   Noble Numismatics (coins), Australian Book Auctions (books), more as added (databases/load.py)
  databases/armitage.json               Armitage's own past results (pipeline/armitage_results.py)
  work/gowans_all.json                  Gowans Auctions, Hobart, every lot since mid-2024
  work/sold_db.json and pipeline/state/chrome_sold.json   sold comps found by earlier research, with URL

The market researchers in pipeline/wf_funnel.js run this before they search the web; a
same-item hit here is a SOLD price like any other.
"""
import argparse
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'databases'))
try:
    from load import records as db_records
except ImportError:
    db_records = None

VENUE = {'noble': 'Noble Numismatics, Sydney', 'aba': 'Australian Book Auctions, Melbourne', 'armitage': 'Armitage Auctions, Launceston',
         'gowans': 'Gowans Auctions, Hobart'}


def rows(source=None, category=None):
    """Every sold lot we know of: source, venue, sale, lot, date, text, hammer, url, match."""
    if db_records and source not in ('gowans', 'armitage', 'research'):
        for r in db_records(source=source, category=category):
            if r.get('unsold') or not r.get('hammer_aud'):
                continue
            yield {'source': r['source'], 'venue': VENUE.get(r['source'], r['source']), 'sale': r.get('sale'), 'lot': r.get('lot'),
                   'date': r.get('date') or '', 'text': f"{r.get('title') or ''} {r.get('description') or ''}".strip(),
                   'hammer': float(r['hammer_aud']), 'url': r.get('url') or '', 'match': 'same words'}
    a = os.path.join(ROOT, 'databases', 'armitage.json')
    if os.path.exists(a) and source in (None, 'armitage'):
        for chid, e in json.load(open(a)).items():
            for r in e.get('records', []):
                if not r.get('hammer_aud') or not r.get('closed'):
                    continue
                if category and not (r.get('category') or '').startswith(category):
                    continue
                yield {'source': 'armitage', 'venue': VENUE['armitage'], 'sale': chid, 'lot': r.get('lot'), 'date': r.get('date') or '',
                       'text': f"{r.get('title') or ''} {r.get('description') or ''}".strip(), 'hammer': float(r['hammer_aud']),
                       'url': r.get('url') or '', 'match': 'same words'}
    g = os.path.join(ROOT, 'work', 'gowans_all.json')
    if os.path.exists(g) and source in (None, 'gowans') and category is None:
        for k, r in json.load(open(g)).get('rows', {}).items():
            if r.get('title') and r.get('hammer', 0) > 0:
                yield {'source': 'gowans', 'venue': VENUE['gowans'], 'sale': '', 'lot': r.get('lot'), 'date': r.get('created') or '',
                       'text': r['title'], 'hammer': float(r['hammer']), 'url': f'gowans lot id {k}', 'match': 'same words'}
    if source in (None, 'research') and category is None:
        for f in (os.path.join(ROOT, 'work', 'sold_db.json'), os.path.join(ROOT, 'pipeline', 'state', 'chrome_sold.json')):
            if not os.path.exists(f):
                continue
            for r in json.load(open(f)):
                if r.get('item') and r.get('aud_hammer', 0) > 0 and r.get('match') in ('yes', 'close'):
                    yield {'source': 'research', 'venue': r.get('venue') or 'earlier research', 'sale': '', 'lot': r.get('lot') or '',
                           'date': r.get('date') or '', 'text': f"{r['item']} {(r.get('note') or '')[:100]}", 'hammer': float(r['aud_hammer']),
                           'url': r.get('url') or '', 'match': r['match']}


def search(words, source=None, category=None, min_hammer=0):
    words = [w.lower() for w in words]
    hits = [r for r in rows(source, category) if r['hammer'] >= min_hammer and all(w in r['text'].lower() for w in words)]
    hits.sort(key=lambda r: r['date'], reverse=True)
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('words', nargs='+')
    ap.add_argument('--min', type=float, default=0, help='minimum hammer')
    ap.add_argument('--limit', type=int, default=30)
    ap.add_argument('--category', default=None, help='coins or books (narrows the sources that carry a category)')
    ap.add_argument('--source', default=None, help='noble, aba, armitage, gowans or research')
    ap.add_argument('--json', action='store_true', help='JSON instead of text')
    a = ap.parse_args()
    hits = search(a.words, a.source, a.category, a.min)
    prices = [h['hammer'] for h in hits]
    summary = {'words': a.words, 'hits': len(hits), 'low': min(prices) if prices else 0, 'median': statistics.median(prices) if prices else 0,
               'high': max(prices) if prices else 0, 'note': 'hammer prices, buyer\'s premium not included'}
    if a.json:
        print(json.dumps({'summary': summary, 'hits': hits[:a.limit]}, indent=1))
        return
    for h in hits[:a.limit]:
        ref = h['venue'] + (f" sale {h['sale']}" if h['sale'] else '') + (f" lot {h['lot']}" if h['lot'] else '')
        print(f"{str(h['date'])[:10]:10}  ${h['hammer']:>8,.0f}  {ref}: {h['text'][:140]}  {h['url']}")
    if hits:
        print(f"\n{len(hits)} sold hits: low ${summary['low']:,.0f}, median ${summary['median']:,.0f}, high ${summary['high']:,.0f} ({summary['note']})")
    else:
        print('nothing sold with all those words in any local database')


if __name__ == '__main__':
    main()
