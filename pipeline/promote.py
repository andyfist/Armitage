#!/usr/bin/env python3
"""Usage: python3 pipeline/promote.py [--rebuild] [--min-hammer 250] ["<title to test>" ...]

Promotes lots to the photo scan from hard data instead of hand-written rules. Builds an
index of word pairs from the results database (work/gowans_all.json, work/sold_db.json,
work/aba_lots.json): a pair of title words is "valuable" when at least three sales with that
pair made --min-hammer or more AND at least 60% of all sales with that pair did. A lot
whose title and description hold a valuable pair is promoted, never excluded (Andy,
21 Oct 2026: the database is for not overlooking things).

The index is cached in pipeline/state/promote_index.json; --rebuild remakes it (about 20
seconds) after the database grows. check(title, description) is what prep.py calls.
"""
import argparse
import itertools
import json
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, 'work')
INDEX = os.path.join(ROOT, 'pipeline', 'state', 'promote_index.json')
STOP = set('''a an and the of for with in on at to by from or as is are was were be been this that these those its it
lot lots pair pairs set sets box boxes group various assorted mixed misc quantity qty collection items item piece pieces
large small medium big little old new vintage antique style type inc incl including includes etc approx approximately
one two three four five six seven eight nine ten x cm mm inch inches h w d height width depth diam long high wide
plus other others some more lot# no nos number numbered size sized colour coloured color black white red blue green
brown grey gray gold silver plated epns china glass wood wooden metal brass copper iron tin plastic paper framed frame
unframed print prints picture pictures painting paintings oil original signed unsigned hand top bottom double single
half natural electric hard soft gas water cut edge narrow tall short century decorated drawer drawers door doors panel
panels glazed cream weight weights offset service coffee tea dinner part full good very fine early late dated marked
stamped made make style design designed decor shaped form base stand stands case cased boxed working condition'''.split())
GENERIC_PAIR_WORDS = set('gold silver sterling framed signed oil painting print vase bowl jug plate dish books book coins coin'.split())


def tokens(text):
    out = []
    for w in re.findall(r'[a-z0-9]+', (text or '').lower()):
        if len(w) >= 3 and w not in STOP and not w.isdigit():
            out.append(w)
    seen, uniq = set(), []
    for w in out:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return uniq[:14]


def pairs(words):
    return {'|'.join(sorted(p)) for p in itertools.combinations(words, 2)}


def records():
    """(title, hammer) for every sale in the database."""
    g = os.path.join(WORK, 'gowans_all.json')
    if os.path.exists(g):
        for r in json.load(open(g)).get('rows', {}).values():
            if r.get('title') and r.get('hammer', 0) > 0:
                yield r['title'], float(r['hammer'])
    s = os.path.join(WORK, 'sold_db.json')
    if os.path.exists(s):
        for r in json.load(open(s)):
            if r.get('item') and r.get('aud_hammer', 0) > 0 and r.get('match') in ('yes', 'close'):
                yield r['item'], float(r['aud_hammer'])
    a = os.path.join(WORK, 'aba_lots.json')
    if os.path.exists(a):
        for r in json.load(open(a)):
            if r.get('text') and r.get('hammer'):
                yield r['text'], float(r['hammer'])


def build(min_hammer=250):
    valuable = {}      # pair -> list of hammers >= min_hammer
    everything = {}    # pair -> count of all sales with that pair (only pairs seen in a valuable sale)
    rows = [(tokens(t), h) for t, h in records()]
    for words, h in rows:
        if h >= min_hammer:
            for p in pairs(words):
                valuable.setdefault(p, []).append(h)
    for words, h in rows:
        for p in pairs(words):
            if p in valuable:
                everything[p] = everything.get(p, 0) + 1
    index = {}
    for p, hs in valuable.items():
        a, b = p.split('|')
        if a in GENERIC_PAIR_WORDS and b in GENERIC_PAIR_WORDS:
            continue
        n, total = len(hs), everything.get(p, len(hs))
        if n >= 3 and n / total >= 0.6:
            index[p] = {'n': n, 'total': total, 'median': round(statistics.median(hs))}
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    json.dump({'min_hammer': min_hammer, 'sales': len(rows), 'pairs': index}, open(INDEX, 'w'), separators=(',', ':'))
    return index


_index = None


def load():
    global _index
    if _index is None:
        _index = json.load(open(INDEX))['pairs'] if os.path.exists(INDEX) else {}
    return _index


def check(title, description=''):
    """Return (reason or None). The reason names the best matching pair and what it made."""
    idx = load()
    if not idx:
        return None
    best = None
    for p in pairs(tokens(f'{title or ""} {description or ""}')):
        e = idx.get(p)
        if e and (best is None or (e['n'], e['median']) > (best[1]['n'], best[1]['median'])):
            best = (p, e)
    if not best:
        return None
    p, e = best
    return f"database: '{p.replace('|', ' + ')}' made ${e['median']:,} median in {e['n']} of {e['total']} sales"


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--rebuild', action='store_true')
    ap.add_argument('--min-hammer', type=int, default=250)
    ap.add_argument('titles', nargs='*')
    a = ap.parse_args()
    if a.rebuild or not os.path.exists(INDEX):
        idx = build(a.min_hammer)
        print(f'index built: {len(idx)} valuable word pairs', file=sys.stderr)
    for t in a.titles:
        print(check(t), '<-', t)
