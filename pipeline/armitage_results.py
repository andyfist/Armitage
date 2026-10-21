#!/usr/bin/env python3
"""Usage: python3 pipeline/armitage_results.py [--from CHID --to CHID | --chid CHID ...] [--refresh-open] [--pause 1.0]

Read-only scrape of Armitage Auctions' past catalogues: every lot's title, description,
close time, closing bid (the hammer price when the lot had bids) and the bid history as
the lot page shows it (bidder number, hometown, amount, time). Two uses: the results
database (what things actually make at Armitage) and the bidder analysis (who bids on
what, and from where).

Writes databases/armitage.json: {chid: {name, lots, close_first, close_last, scraped,
lots: [record...]}}. Each record follows the shared database format (source, sale, lot,
date, title, description, hammer_aud, premium_included, url, category) plus bid_count,
estimate, closed and history. Resumable: a catalogue already in the file whose lots have
all closed is skipped; --refresh-open re-reads catalogues that are still running.

One request a second by default (about 10 minutes per 600 lots). Chids are roughly
sequential: the 30 Sep 2026 sale was 28711 to 28713 and 21 Oct was 28838 to 28842, so
--from 28600 --to 28850 covers 2026 so far; a chid that is not a catalogue costs one request.
"""
import argparse
import datetime
import html
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'databases', 'armitage.json')
BASE = 'https://armitage.bidsonline.com.au'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import rules
except Exception:  # category rules are optional here
    rules = None

try:
    from zoneinfo import ZoneInfo
    HOBART = ZoneInfo('Australia/Hobart')
except Exception:
    HOBART = datetime.timezone(datetime.timedelta(hours=11), 'AEDT')

PAUSE = 1.0


def curl(url, tries=3):
    code = '0'
    for attempt in range(tries):
        r = subprocess.run(['curl', '-sS', '-L', '-A', UA, '--max-time', '40', '-w', '%{http_code}', url], capture_output=True)
        code = r.stdout[-3:].decode(errors='ignore')
        if code == '200':
            return r.stdout[:-3].decode('utf8', 'ignore'), 200
        if code == '404':
            return None, 404
        time.sleep(10 * (attempt + 1))
    return None, int(code) if code.isdigit() else 0


def strip(h):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', h, flags=re.S)))).strip()


CLOSE_RE = re.compile(r'(\d+)/(\d+)/(\d+) (\d+):(\d+)(?::(\d+))? ([AP])M')


def close_dt(text):
    """'21/10/2026 12:30:00 PM ADST' -> aware datetime in Hobart time, or None."""
    m = CLOSE_RE.search(text or '')
    if not m:
        return None
    d, mo, y, h, mi, s, ap = m.groups()
    h = int(h) % 12 + (12 if ap == 'P' else 0)
    try:
        return datetime.datetime(int(y), int(mo), int(d), h, int(mi), int(s or 0), tzinfo=HOBART)
    except ValueError:
        return None


def money(s):
    m = re.search(r'[\d,]+(?:\.\d+)?', str(s or ''))
    return float(m.group(0).replace(',', '')) if m else 0.0


BIDDER_RE = re.compile(r'^\s*(\d+)\s*-\s*(.*?)\s*$')
STATES = ('TAS', 'VIC', 'NSW', 'ACT', 'QLD', 'SA', 'WA', 'NT')


def bidder(cell):
    """'77980 - Stanley, TAS  - AutoBid' -> {who, bidder: '77980', town: 'Stanley', state: 'TAS', autobid: True}.
    The state is often missing ('142599 - Gravelly Beach , '), so an empty state is not a sign of interstate."""
    who = strip(cell)
    auto = bool(re.search(r'-\s*AutoBid\s*$', who, re.I))
    rest = re.sub(r'\s*-\s*AutoBid\s*$', '', who, flags=re.I)
    m = BIDDER_RE.match(rest)
    no, place = (m.group(1), m.group(2)) if m else ('', rest)
    parts = [x.strip() for x in place.split(',')]
    state = parts[-1].upper() if len(parts) > 1 and parts[-1].upper() in STATES else ''
    town = parts[0] if parts else ''
    return {'who': who, 'bidder': no, 'town': town, 'state': state, 'autobid': auto}


def group_items(chid):
    body, code = curl(f'{BASE}/catalogue-group.aspx?chid={chid}&BID=')
    if code != 200 or not body:
        return None, code
    items, seen = [], set()
    for m in re.finditer(r'id="item_(\d+)"(.*?)id="timelabel_\1"[^>]*>([^<]*)<', body, flags=re.S):
        cd = int(m.group(1))
        if cd in seen:
            continue
        seen.add(cd)
        lot = re.search(r'Lot:\s*([^\s<]+)\s*-', m.group(2))
        items.append({'cdid': cd, 'lot_label': lot.group(1) if lot else '', 'close_group': m.group(3).strip()})
    title = re.search(r'<title>(.*?)</title>', body, re.S)
    name = strip(title.group(1)) if title else f'catalogue {chid}'
    return {'name': name, 'items': items}, 200


def parse_lot(chid, it, now):
    cd = it['cdid']
    url = f'{BASE}/catalogue_detail.aspx?cdid={cd}&chid={chid}&category=ALL&style=group'
    body, code = curl(url)
    rec = {'source': 'armitage', 'sale': str(chid), 'cdid': cd, 'lot': it['lot_label'], 'url': url, 'http': code}
    if code != 200 or not body:
        return rec
    t = strip(body)
    lot = re.search(r'Lot No\. ?(\w+)', t)
    close = re.search(r'Auction Closes: (\d+/\d+/\d+ [\d:]+ [AP]M \w+)', t)
    desc = re.search(r'Description:(.*?)Estimate:', t)
    est = re.search(r'Estimate: Estimate ([^ ]+(?: ?- ?[^ ]+)?)', t)
    cur = re.search(r'Current Bid \(\$\): (\$[\d,\.]+|[^ ]+)', t)
    title = re.search(r'<h2 class="post-title">(.*?)<span', body, flags=re.S)
    # bid history table, newest first: Bidder ("142599 - Gravelly Beach , " or "77980 - Stanley, TAS  - AutoBid"), Quantity, Bid, Date/Time
    rows = re.findall(r'<tr>\s*<td>([^<]*)</td>\s*<td>(\d+)</td>\s*<td>([\d\.,]+)</td>\s*<td>([\d/: APM]+)</td>', body)
    history = [dict(bidder(w), qty=int(q), amount=money(a), when=when.strip()) for w, q, a, when in rows]
    top = max((h['amount'] for h in history), default=0.0)
    close_text = close.group(1) if close else it['close_group']
    cdt = close_dt(close_text)
    closed = bool(cdt and cdt < now)
    bids = len(rows)
    rec.update({
        'lot': (lot.group(1) if lot else it['lot_label']) or str(cd),
        'title': strip(title.group(1)) if title else None,
        'description': desc.group(1).strip() if desc else None,
        'close': close_text, 'date': cdt.date().isoformat() if cdt else None, 'closed': closed,
        'estimate': est.group(1) if est else None,
        # closed lot pages no longer show "Current Bid", so the closing bid is the top of the bid history
        'current_bid': top or (money(cur.group(1)) if cur else None), 'bid_count': bids,
        # the hammer is the closing bid of a closed lot that had bids; a reserve may still have stopped the sale
        'hammer_aud': top if (closed and bids) else 0.0, 'premium_included': False,
        'reserve_note': 'reserve not met' if re.search(r'reserve not met', t, re.I) else '',
        'history': history,
        'category': (rules.classify(strip(title.group(1)) if title else '', desc.group(1) if desc else '')[1] if rules else ''),
    })
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--from', dest='frm', type=int)
    ap.add_argument('--to', type=int)
    ap.add_argument('--chid', type=int, nargs='*', default=[])
    ap.add_argument('--refresh-open', action='store_true', help='re-read catalogues that have not finished closing')
    ap.add_argument('--pause', type=float, default=1.0)
    ap.add_argument('--out', default=OUT)
    args = ap.parse_args()
    global PAUSE
    PAUSE = args.pause
    chids = list(args.chid) + (list(range(args.frm, args.to + 1)) if args.frm and args.to else [])
    if not chids:
        sys.exit('give --chid ... or --from and --to')
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    db = json.load(open(args.out)) if os.path.exists(args.out) else {}
    now = datetime.datetime.now(HOBART)

    for chid in chids:
        key = str(chid)
        have = db.get(key)
        if have and (have.get('all_closed') or not args.refresh_open):
            print(key, 'already scraped', 'and closed' if have.get('all_closed') else '(use --refresh-open to re-read)', flush=True)
            continue
        time.sleep(PAUSE)
        g, code = group_items(chid)
        if not g or not g['items']:
            print(key, 'no catalogue' if code == 200 else f'http {code}', flush=True)
            continue
        print(key, g['name'], len(g['items']), 'lots', flush=True)
        recs = []
        for i, it in enumerate(g['items']):
            time.sleep(PAUSE)
            recs.append(parse_lot(chid, it, now))
            if (i + 1) % 100 == 0:
                print(f'  {i + 1} of {len(g["items"])}', flush=True)
        closes = [r.get('close') for r in recs if r.get('close')]
        entry = {'chid': key, 'name': g['name'], 'lots': len(recs), 'scraped': now.strftime('%Y-%m-%d %H:%M %Z'),
                 'close_first': min(closes, key=lambda c: close_dt(c) or now) if closes else None,
                 'close_last': max(closes, key=lambda c: close_dt(c) or now) if closes else None,
                 'all_closed': all(r.get('closed') for r in recs if r.get('http') == 200),
                 'sold': sum(1 for r in recs if r.get('hammer_aud')), 'records': recs}
        db[key] = entry
        with open(args.out + '.tmp', 'w') as f:  # write then rename, so a commit mid-run never sees half a file
            json.dump(db, f, indent=0)
        os.replace(args.out + '.tmp', args.out)
        print(f"  saved: {entry['sold']} sold of {entry['lots']}, all closed: {entry['all_closed']}", flush=True)
    total = sum(e['lots'] for e in db.values())
    sold = sum(e.get('sold', 0) for e in db.values())
    print(json.dumps({'catalogues': len(db), 'lots': total, 'sold': sold, 'file': args.out}))


if __name__ == '__main__':
    main()
