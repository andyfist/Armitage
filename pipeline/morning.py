#!/usr/bin/env python3
"""Usage: python3 pipeline/morning.py <chid> [--date d/m/yyyy]

Prints the auction-morning email: every lot closing today that is worth bidding on (PASS
or CHROME in assessment.json) or carries a bidder signal (bidders.json), in closing order,
with its closing time, our maximum, the current bid and who is bidding, plus the first and
last closing time of the day. Run after pipeline/bidders.py --refresh on the morning of a
closing day (routines/armitage-new-sale.md). The first line is the subject.
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prep  # noqa: E402
from bidders import closes_on, money  # noqa: E402

ROOT = prep.ROOT
BASE = prep.BASE


def clock(close):
    m = prep.CLOSE_RE.search(close or '')
    return f"{int(m.group(4))}:{m.group(5)} {m.group(7)}M" if m else '?'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('chid')
    ap.add_argument('--date', default=None, help='the day, d/m/yyyy (default today, Hobart)')
    ap.add_argument('--top', type=int, default=60, help='lots listed (default 60)')
    args = ap.parse_args()
    D = os.path.join(ROOT, 'pipeline', 'sales', args.chid)
    cat = json.load(open(os.path.join(D, 'cat.json')))
    lots = json.load(open(os.path.join(D, 'lots.json')))
    bids = json.load(open(os.path.join(D, 'bids.json'))) if os.path.exists(os.path.join(D, 'bids.json')) else {}
    day = datetime.datetime.strptime(args.date, '%d/%m/%Y').date() if args.date else datetime.datetime.now(prep.HOBART).date()
    a_lots = {}
    if os.path.exists(os.path.join(D, 'assessment.json')):
        a_lots = {x['cdid']: x for x in json.load(open(os.path.join(D, 'assessment.json')))['lots']}
    flagged = {}
    if os.path.exists(os.path.join(D, 'bidders.json')):
        flagged = {f['cdid']: f for f in json.load(open(os.path.join(D, 'bidders.json')))['flagged']}

    today = [r for r in lots if closes_on((bids.get(str(r['cdid'])) or {}).get('close') or r.get('close'), day)]
    today.sort(key=lambda r: prep.close_key((bids.get(str(r['cdid'])) or {}).get('close') or r.get('close')))
    watch = []
    for r in today:
        x, f, b = a_lots.get(r['cdid']), flagged.get(r['cdid']), bids.get(str(r['cdid'])) or {}
        if not ((x and x['status'] in ('PASS', 'CHROME')) or f):
            continue
        close = b.get('close') or r.get('close')
        status = ('max $' + format(x['max_hammer'], ',') if x and x['status'] == 'PASS' else 'no max yet (Chrome list)' if x and x['status'] == 'CHROME'
                  else x['status'].lower() if x else 'not valued')
        who = ''
        if f:
            who = ' Bidders: ' + '; '.join(e['who'] + (f" [{', '.join(e['tags'])}]" if e['tags'] else '') for e in f['bidders'][:3])
        watch.append((close, f"- {clock(close)}: lot {r.get('lot')} {(r.get('title') or '')[:50]}. {status}, bid ${money(b.get('current_bid')):,.0f} "
                             f"({len(b.get('history') or [])} bids).{who}"))

    first = clock((bids.get(str(today[0]['cdid'])) or {}).get('close') or today[0].get('close')) if today else '?'
    last = clock((bids.get(str(today[-1]['cdid'])) or {}).get('close') or today[-1].get('close')) if today else '?'
    passes = sum(1 for c, _ in watch if 'max $' in _)
    gw = args.chid.startswith('gowans')
    lines = [f"{'' if gw else 'Armitage '}{cat.get('name')}: {len(today)} lots close today, {len(watch)} to watch (first {first}, last {last})", '',
             f"{len(today)} lots close today, {day.strftime('%A %d %B')}, from {first} to {last} Hobart time. {len(watch)} of them are worth watching: "
             f"{passes} with a maximum, {len(watch) - passes} still without one. Bid at {'https://www.gowansauctions.com.au/' if gw else BASE + '/catalogue-group.aspx?chid=' + args.chid}", '',
             f"A maximum is the most to pay as a hammer price; the {'19.8%' if gw else '22%'} premium is already allowed for. Do not go over it.", '']
    for c, line in watch[:args.top]:
        lines.append(line)
    if len(watch) > args.top:
        lines.append(f"... and {len(watch) - args.top} more in assessment.json")
    if not today:
        lines.append('No lots of this sale close today.')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
