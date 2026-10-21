#!/usr/bin/env python3
"""Usage: python3 pipeline/review.py <chid> [--big 300]

Step 8, after a sale has closed and pipeline/armitage_results.py --chid <chid> has put its
results and bid histories in databases/armitage.json: compares what the funnel did with
what happened, so the next sale is scanned better.

  passes    lots we passed: sold within our maximum, went over it, or unsold
  misses    lots that made --big or more at the hammer, or that an interstate bidder bid
            on, and that the funnel excluded, never scanned, skipped, dropped or failed:
            the stage where each fell out and the reason it gave there
  bidders   the bidder signals, and whether the flagged lots made money

Writes pipeline/sales/<chid>/review.json and review.md, appends one line per big miss to
pipeline/state/lessons.md (the title words that should have promoted it), and prints the
email (first line is the subject).
"""
import argparse
import datetime
import glob
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prep  # noqa: E402
import promote  # noqa: E402
from bidders import money, parse_who  # noqa: E402

ROOT = prep.ROOT
RESULTS_DB = os.path.join(ROOT, 'databases', 'armitage.json')
LESSONS = os.path.join(ROOT, 'pipeline', 'state', 'lessons.md')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('chid')
    ap.add_argument('--big', type=float, default=300, help='a hammer price this high counts as a miss if we did not shortlist the lot (default 300)')
    ap.add_argument('--top', type=int, default=25, help='lots per list in the email (default 25)')
    args = ap.parse_args()
    chid = args.chid
    D = os.path.join(ROOT, 'pipeline', 'sales', chid)
    cat = json.load(open(os.path.join(D, 'cat.json'))) if os.path.exists(os.path.join(D, 'cat.json')) else {'name': f'catalogue {chid}'}
    db = json.load(open(RESULTS_DB)) if os.path.exists(RESULTS_DB) else {}
    entry = db.get(chid)
    if not entry:
        sys.exit(f'no results for {chid} in {RESULTS_DB}: run python3 pipeline/armitage_results.py --chid {chid} first')
    results = {r['cdid']: r for r in entry.get('records', []) if r.get('closed')}
    if not results:
        sys.exit(f'{chid}: no closed lots in the results yet')

    lots = {r['cdid']: r for r in json.load(open(os.path.join(D, 'lots.json')))} if os.path.exists(os.path.join(D, 'lots.json')) else {}
    scans = {}
    for f in glob.glob(os.path.join(D, 'scans', '*.json')):
        for r in json.load(open(f)):
            scans[r['cdid']] = r
    a_lots = {}
    if os.path.exists(os.path.join(D, 'assessment.json')):
        a_lots = {x['cdid']: x for x in json.load(open(os.path.join(D, 'assessment.json')))['lots']}
    flagged = {}
    if os.path.exists(os.path.join(D, 'bidders.json')):
        flagged = {f['cdid']: f for f in json.load(open(os.path.join(D, 'bidders.json')))['flagged']}

    def stage_of(cdid):
        """Where the funnel left this lot, and the reason it gave there."""
        x, s, r = a_lots.get(cdid), scans.get(cdid), lots.get(cdid, {})
        if x:
            return f"bid check: {x['status']}", x.get('why') or ''
        if s and s.get('verdict') == 'SKIP':
            return 'scan: skipped', s.get('reason') or ''
        if s and s.get('verdict') == 'CANDIDATE':
            return 'scan: candidate, not researched', s.get('reason') or ''
        if r.get('state') == 'EXCLUDED' or r.get('cls') == 'exclude':
            return 'rules: excluded', r.get('cls_reason') or ''
        if r.get('state') == 'UNSCANNED':
            return 'prep: no photos', r.get('reason') or ''
        if r.get('cls') == 'title_pass':
            return 'title pass: not kept', ''
        if r:
            return 'scan: not scanned', r.get('reason') or ''
        return 'not in the prep', ''

    passes, misses, rows = [], [], []
    for cdid, res in sorted(results.items(), key=lambda kv: money(kv[1].get('lot'))):
        hammer = money(res.get('hammer_aud'))
        hist = res.get('history') or []
        who = [parse_who(h) for h in hist]
        inter = sorted({f"{p['town']} {p['state']}".strip() for p in who if p['state'] not in ('', 'TAS')})
        winner = parse_who(max(hist, key=lambda h: money(h.get('amount')))) if hist and hammer else None
        stage, why = stage_of(cdid)
        row = {'cdid': cdid, 'lot': res.get('lot'), 'title': res.get('title') or lots.get(cdid, {}).get('title') or '', 'hammer': hammer,
               'bids': len(hist), 'interstate': inter, 'won_interstate': bool(winner and winner['state'] not in ('', 'TAS')),
               'stage': stage, 'why': why, 'flagged': cdid in flagged, 'max': (a_lots.get(cdid) or {}).get('max_hammer') or 0}
        rows.append(row)
        if stage == 'bid check: PASS':
            row['outcome'] = 'unsold' if not hammer else ('within max' if hammer <= row['max'] else f"over max by ${hammer - row['max']:,.0f}")
            passes.append(row)
        elif (hammer >= args.big or inter) and stage not in ('bid check: CHROME',):
            misses.append(row)
    misses.sort(key=lambda r: (-r['hammer'], -len(r['interstate'])))
    big = [r for r in rows if r['hammer'] >= args.big]
    big_short = [r for r in big if r['stage'] in ('bid check: PASS', 'bid check: CHROME')]
    sold = [r['hammer'] for r in rows if r['hammer'] > 0]
    inter_lots = [r for r in rows if r['interstate']]
    flagged_rows = [r for r in rows if r['flagged']]
    stats = {'closed': len(rows), 'sold': len(sold), 'median_hammer': statistics.median(sold) if sold else 0, 'total_hammer': sum(sold),
             'candidates': len(a_lots), 'passes': len(passes), 'within_max': sum(1 for r in passes if r.get('outcome') == 'within max'),
             'over_max': sum(1 for r in passes if str(r.get('outcome', '')).startswith('over')), 'unsold_passes': sum(1 for r in passes if r.get('outcome') == 'unsold'),
             'big': len(big), 'big_shortlisted': len(big_short), 'misses': len(misses), 'interstate_lots': len(inter_lots),
             'interstate_won': sum(1 for r in rows if r['won_interstate']), 'flagged': len(flagged_rows),
             'flagged_big': sum(1 for r in flagged_rows if r['hammer'] >= args.big)}

    # lessons: the title words of every big lot the funnel let go, for the rules and the promote index
    big_misses = [r for r in misses if r['hammer'] >= args.big]
    if big_misses:
        os.makedirs(os.path.dirname(LESSONS), exist_ok=True)
        new = not os.path.exists(LESSONS)
        with open(LESSONS, 'a') as f:
            if new:
                f.write('# Lessons from closed sales\n\nOne line per lot that made real money after the funnel let it go: where it fell out, and the title words that should have promoted it.\n\n')
            for r in big_misses:
                f.write(f"- {datetime.date.today().isoformat()} Armitage {chid} lot {r['lot']}: ${r['hammer']:,.0f} for \"{r['title'][:70]}\" fell out at {r['stage']}"
                        + (f" ({r['why'][:90]})" if r['why'] else '') + f"; words: {' '.join(promote.tokens(r['title'])[:6])}\n")

    json.dump({'chid': chid, 'reviewed': prep.now_text(), 'big': args.big, 'stats': stats, 'passes': passes, 'misses': misses, 'lots': rows},
              open(os.path.join(D, 'review.json'), 'w'), indent=1)

    lines = [f"Armitage {cat.get('name')}: review, {stats['big_shortlisted']} of {stats['big']} lots over ${args.big:,.0f} were on our list, {stats['misses']} misses", '',
             f"{stats['closed']} lots closed, {stats['sold']} sold, median hammer ${stats['median_hammer']:,.0f}, ${stats['total_hammer']:,.0f} in all. "
             f"We researched {stats['candidates']} candidates and passed {stats['passes']}: {stats['within_max']} sold within our maximum, "
             f"{stats['over_max']} went over it, {stats['unsold_passes']} unsold. Of the {stats['big']} lots that made ${args.big:,.0f} or more, "
             f"{stats['big_shortlisted']} were on our list (pass or Chrome). Interstate bidders were on {stats['interstate_lots']} lots and won "
             f"{stats['interstate_won']}; the bidder scan had flagged {stats['flagged']} lots, {stats['flagged_big']} of which made ${args.big:,.0f} or more.", '']
    if passes:
        lines.append('Our passes (max, hammer, outcome):')
        for r in sorted(passes, key=lambda r: -r['hammer'])[:args.top]:
            lines.append(f"- Lot {r['lot']}: max ${r['max']:,}, hammer ${r['hammer']:,.0f}, {r['outcome']}. {r['title'][:60]}")
        lines.append('')
    if misses:
        lines.append(f"Misses (made ${args.big:,.0f}+ or drew an interstate bidder, and we let them go):")
        for r in misses[:args.top]:
            lines.append(f"- Lot {r['lot']}: ${r['hammer']:,.0f}" + (f", interstate: {', '.join(r['interstate'][:3])}" if r['interstate'] else '')
                         + f". {r['title'][:60]}. Fell out at {r['stage']}" + (f": {r['why'][:100]}" if r['why'] else '') + '.')
        if len(misses) > args.top:
            lines.append(f"... and {len(misses) - args.top} more in review.json")
        lines.append('')
    if big_misses:
        lines.append(f"{len(big_misses)} lesson line(s) added to pipeline/state/lessons.md; the rules and the promote index are the places to act on them.")
    text = '\n'.join(lines)
    open(os.path.join(D, 'review.md'), 'w').write(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
