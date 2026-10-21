#!/usr/bin/env python3
"""Usage: python3 pipeline/stage.py <chid> <stage> [--note "<one line>"] [--body <file>]

Records that a pipeline stage finished for one sale in pipeline/state/sales.json and prints
the "stage finished" email (subject line first, then a blank line, then the body) for the
scheduled run to send. Stages, in order: found, prepped, scanned, researched, chrome_list,
photo_list, bidders, morning_email, reviewed.
"""
import argparse
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, 'pipeline', 'state', 'sales.json')
STAGES = ['found', 'prepped', 'scanned', 'researched', 'chrome_list', 'photo_list', 'bidders', 'morning_email', 'reviewed']
LABEL = {'found': 'sale found', 'prepped': 'catalogue read and photos downloaded', 'scanned': 'titles and photos scanned',
         'researched': 'cloud price research done', 'chrome_list': 'Chrome research list ready', 'photo_list': 'photo request list ready',
         'bidders': 'bidder scan done', 'morning_email': 'auction-morning email sent', 'reviewed': 'post-sale review done'}

try:
    from zoneinfo import ZoneInfo
    HOBART = ZoneInfo('Australia/Hobart')
except Exception:
    HOBART = datetime.timezone(datetime.timedelta(hours=11), 'AEDT')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('chid')
    ap.add_argument('stage', choices=STAGES)
    ap.add_argument('--note', default='', help='one line for the email, e.g. counts')
    ap.add_argument('--body', default=None, help='file whose text goes under the note')
    args = ap.parse_args()

    state = json.load(open(STATE)) if os.path.exists(STATE) else {'catalogues': {}, 'failures': 0}
    c = state['catalogues'].setdefault(args.chid, {'chid': args.chid, 'name': f'catalogue {args.chid}'})
    when = datetime.datetime.now(HOBART).strftime('%d/%m/%Y %H:%M %Z')
    c.setdefault('stages', {})[args.stage] = when
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(state, open(STATE, 'w'), indent=1, sort_keys=True)

    done = [s for s in STAGES if s in c['stages']]
    nxt = next((s for s in STAGES if s not in c['stages']), None)
    lines = [f"Armitage {c.get('name')}: {LABEL[args.stage]}", '']
    if args.note:
        lines += [args.note, '']
    if args.body and os.path.exists(args.body):
        lines += [open(args.body).read().rstrip(), '']
    if c.get('close_first'):
        lines.append(f"Lots close from {c['close_first']} to {c.get('close_last', '?')}.")
    lines.append(f"Stages done: {', '.join(done)}." + (f" Next: {nxt}." if nxt else ''))
    lines.append(f"Catalogue: https://armitage.bidsonline.com.au/catalogue-group.aspx?chid={args.chid}")
    print('\n'.join(lines))


if __name__ == '__main__':
    sys.exit(main())
