#!/usr/bin/env python3
"""Usage: python3 pipeline/bidders.py <chid> [--refresh] [--no-photos]

Step 5 of the pipeline: who is bidding, and what that says about the lots.

Armitage prints each bid as a bidder number and hometown. An interstate bidder has
picked a lot out from far away and will pay freight on it, so they probably know
something. A bidder whose history shows a specialty (most of their bids in one category)
or real spending is treated the same way. The history is pipeline/state/bidders.json,
rebuilt on every run from databases/armitage.json (past sales, pipeline/armitage_results.py)
and every prepped sale's bids.json. Bidder numbers are account numbers that persist across
sales, so a bidder is keyed on the number. The hometown and state are typed by the bidder
and the state is often blank, so a Tasmanian town list and the bidder's other sales fill
it in; a town that is neither counts as unknown, never as interstate.

--refresh    re-read the lot pages first (bids change by the hour): every lot that is not
             excluded, or every lot on a day when lots of this sale close. About 8 minutes
             per 1,800 lots. Without it, bids.json as last saved is used.
--no-photos  do not download photos for flagged lots that have none (excluded lots)

Writes pipeline/sales/<chid>/bidders.json (every lot with a signal, strongest first) and,
for flagged lots the funnel has not researched, force.json and wfargs_bidders.json:
arguments for pipeline/wf_funnel.js that scan and research just those lots (run it with
the Workflow tool, then pipeline/assess.py). A flagged lot the research dropped is put on
the Chrome list instead. Prints the "bidder scan" email.
"""
import argparse
import datetime
import glob
import json
import os
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prep  # noqa: E402

ROOT = prep.ROOT
BASE = prep.BASE
PROFILES = os.path.join(ROOT, 'pipeline', 'state', 'bidders.json')
RESULTS_DB = os.path.join(ROOT, 'databases', 'armitage.json')

STATE_WORDS = {'TAS': 'TAS', 'TASMANIA': 'TAS', 'VIC': 'VIC', 'VICTORIA': 'VIC', 'NSW': 'NSW', 'QLD': 'QLD', 'QUEENSLAND': 'QLD',
               'SA': 'SA', 'WA': 'WA', 'NT': 'NT', 'ACT': 'ACT'}
STATE_RE = re.compile(r'\b(' + '|'.join(STATE_WORDS) + r')\b\.?', re.I)
# hometowns printed without a state are matched against this list; anything else is "unknown", never "interstate"
TAS_TOWNS = {t.lower() for t in (
    'Launceston Hobart Devonport Burnie Ulverstone Kingston Glenorchy Bellerive Howrah Lindisfarne Rosny Moonah Claremont Berriedale '
    'Sandy Bay Taroona Battery Point New Town North Hobart West Hobart South Hobart Lenah Valley Mount Stuart Montrose Austins Ferry '
    'Granton Bridgewater Brighton Old Beach Gagebrook Risdon Vale Lauderdale Cambridge Rokeby Seven Mile Beach Midway Point Sorell '
    'Dodges Ferry Richmond Dunalley Nubeena Port Arthur New Norfolk Huonville Cygnet Geeveston Dover Franklin Kettering Margate Snug '
    'Blackmans Bay Woodbridge Invermay Mowbray Newnham Riverside Trevallyn Prospect Kings Meadows Youngtown Summerhill Norwood '
    'Ravenswood Rocherlea Waverley St Leonards Newstead East Launceston West Launceston Legana Exeter Beaconsfield Beauty Point '
    'George Town Low Head Bridport Scottsdale Lilydale Evandale Longford Perth Cressy Campbell Town Ross Oatlands Deloraine '
    'Westbury Hadspen Carrick Mole Creek Sheffield Railton Latrobe Port Sorell Shearwater Hawley Beach Penguin Wynyard Somerset '
    'Smithton Stanley Queenstown Zeehan Strahan Rosebery Tullah St Helens Scamander Bicheno Swansea Triabunna Orford St Marys '
    'Fingal Derby Branxholm Rosevears Grindelwald Dilston Windermere Hillwood Pipers River Lebrina Nunamara Relbia Breadalbane '
    'Blackstone Heights Prospect Vale Kimberley Elizabeth Town Spreyton Quoiba Miandetta East Devonport Turners Beach Forth Don '
    'Heybridge Sulphur Creek Ridgley Boat Harbour Sisters Beach Rocky Cape Hamilton Bothwell Ouse Kempton Bagdad Tasmania'
).split()} | {'campbell town', 'george town', 'new norfolk', 'port sorell', 'port arthur', 'sandy bay', 'battery point', 'new town',
             'north hobart', 'west hobart', 'south hobart', 'lenah valley', 'mount stuart', 'austins ferry', 'old beach', 'risdon vale',
             'seven mile beach', 'midway point', 'dodges ferry', 'blackmans bay', 'kings meadows', 'st leonards', 'east launceston',
             'west launceston', 'beauty point', 'low head', 'mole creek', 'hawley beach', 'st helens', 'st marys', 'pipers river',
             'blackstone heights', 'prospect vale', 'elizabeth town', 'east devonport', 'turners beach', 'sulphur creek', 'boat harbour',
             'sisters beach', 'rocky cape'}

SPECIALTY_MIN_LOTS = 8      # a specialist has bid on at least this many lots ...
SPECIALTY_SHARE = 0.6       # ... with this share of them in one category
STRONG_WINS, STRONG_MEDIAN = 5, 200   # a strong buyer: this many wins at this median hammer or more


def money(s):
    try:
        return float(re.sub(r'[^\d.]', '', str(s or '')) or 0)
    except ValueError:
        return 0.0


def parse_who(h):
    """A bid row -> bidder number, town, state, autobid. Armitage prints the first cell of a bid
    as "138060 - Evandale, - AutoBid" or "59492 - DEVONPORT, TAS": the hometown and state are
    typed by the bidder, so the state is often blank (even for Hobart) and the town's case
    varies. Rows from databases/armitage.json carry the split already (bidder, town, state,
    autobid). The "no" cell that prep.py saves is the quantity, not the bidder number."""
    if isinstance(h, dict) and h.get('bidder'):
        num, town, state, autobid = str(h['bidder']), str(h.get('town') or ''), str(h.get('state') or '').upper(), bool(h.get('autobid'))
    else:
        s = re.sub(r'\s+', ' ', str((h.get('who') if isinstance(h, dict) else h) or '')).strip()
        autobid = bool(re.search(r'auto ?bid', s, re.I))
        s = re.sub(r'-?\s*auto ?bid\s*$', '', s, flags=re.I).strip()
        m = re.match(r'^(\d+)\s*-\s*(.*)$', s)
        if m:
            num, place = m.group(1), m.group(2)
        else:
            d = re.search(r'\d+', s)
            num, place = (d.group(0) if d else ''), re.sub(r'\bbidder\b|#|\d+', ' ', s, flags=re.I)
        parts = [p.strip(' .') for p in place.split(',')]
        town, state = parts[0], ''
        if len(parts) > 1 and parts[-1].upper() in STATE_WORDS:
            state = STATE_WORDS[parts[-1].upper()]
        else:
            m2 = STATE_RE.search(town)
            if m2:
                state, town = STATE_WORDS[m2.group(1).upper()], town[:m2.start()]
    town = re.sub(r'[()\[\]]', ' ', town)
    town = re.sub(r'\s+', ' ', town).strip().title()
    if not state and town.lower() in TAS_TOWNS:
        state = 'TAS'
    return {'no': num, 'town': town, 'state': state, 'autobid': autobid}


def bidder_key(p):
    """Bidder numbers are account numbers that persist across sales; the town is self-typed."""
    return p['no'] or (p['town'].lower() or '?')


def now_key():
    return prep.close_key(datetime.datetime.now(prep.HOBART).strftime('%d/%m/%Y %I:%M:%S %p'))


def closes_on(close, day):
    m = prep.CLOSE_RE.search(close or '')
    return bool(m) and (int(m.group(1)), int(m.group(2)), int(m.group(3))) == (day.day, day.month, day.year)


# ---------- profiles from every bid we have seen

def history_rows():
    rows, seen = [], set()

    def add(sale, cdid, lot, title, category, hammer, closed, h):
        p = parse_who(h)
        key = (str(sale), cdid, p['no'], p['town'], str(h.get('amount')), h.get('when'))
        if key in seen:
            return
        seen.add(key)
        rows.append({'sale': str(sale), 'cdid': cdid, 'lot': lot, 'title': title or '', 'category': category or '', 'hammer': hammer,
                     'closed': closed, 'who': h.get('who', ''), 'p': p, 'amount': money(h.get('amount')), 'when': h.get('when')})

    if os.path.exists(RESULTS_DB):
        for sale, entry in json.load(open(RESULTS_DB)).items():
            for r in entry.get('records', []):
                hammer = money(r.get('hammer_aud'))
                for h in r.get('history') or []:
                    add(sale, r.get('cdid'), r.get('lot'), r.get('title'), r.get('category'), hammer, bool(r.get('closed')), h)
    for f in glob.glob(os.path.join(ROOT, 'pipeline', 'sales', '*', 'bids.json')):
        d = os.path.dirname(f)
        lots = {}
        if os.path.exists(os.path.join(d, 'lots.json')):
            lots = {r['cdid']: r for r in json.load(open(os.path.join(d, 'lots.json')))}
        for cdid, b in json.load(open(f)).items():
            r = lots.get(int(cdid), {})
            cat = r.get('cls_reason') if r.get('cls') == 'always_look' else ''
            for h in b.get('history') or []:  # a live sale: no hammer and no winner yet
                add(os.path.basename(d), int(cdid), r.get('lot'), r.get('title'), cat, 0, False, h)
    return rows


def build_profiles(rows):
    prof, by_lot = {}, {}
    for r in rows:
        by_lot.setdefault((r['sale'], r['cdid']), []).append(r)
    for (sale, cdid), rs in by_lot.items():
        winner = max(rs, key=lambda r: r['amount']) if (rs[0]['closed'] and rs[0]['hammer'] > 0) else None
        per_bidder = {}
        for r in rs:
            k = bidder_key(r['p'])
            p = prof.setdefault(k, {'key': k, 'no': r['p']['no'], 'who': r['who'], 'town': r['p']['town'], 'state': r['p']['state'],
                                    'bids': 0, 'lots': 0, 'sales': set(), 'wins': 0, 'win_prices': [], 'categories': {}, 'autobids': 0})
            p['bids'] += 1
            p['autobids'] += int(r['p']['autobid'])
            p['sales'].add(sale)
            if r['p']['state'] and not p['state']:
                p['state'] = r['p']['state']
            per_bidder[k] = r['category']
        for k, cat in per_bidder.items():
            prof[k]['lots'] += 1
            prof[k]['categories'][cat or 'general'] = prof[k]['categories'].get(cat or 'general', 0) + 1
        if winner:
            w = prof[bidder_key(winner['p'])]
            w['wins'] += 1
            w['win_prices'].append(winner['hammer'])
    for p in prof.values():
        p['sales'] = len(p['sales'])
        p['interstate'] = p['state'] not in ('', 'TAS')
        p['median_win'] = statistics.median(p['win_prices']) if p['win_prices'] else 0
        p['spend'] = sum(p['win_prices'])
        del p['win_prices']
        cat, n = max(((c, n) for c, n in p['categories'].items() if c != 'general'), key=lambda x: x[1], default=('', 0))
        p['specialty'] = cat if (p['lots'] >= SPECIALTY_MIN_LOTS and n >= SPECIALTY_SHARE * p['lots']) else ''
        p['strong'] = p['wins'] >= STRONG_WINS and p['median_win'] >= STRONG_MEDIAN
    return prof


# ---------- the live sale

def refresh(chid, D, lots, bids, everything):
    now = prep.now_text()
    todo = [r for r in lots if everything or r.get('state') != 'EXCLUDED']
    items = [{'cdid': r['cdid'], 'lot_label': r.get('lot_label', ''), 'pid': r.get('photo_id'), 'close_group': r.get('close', '')} for r in todo]
    with ThreadPoolExecutor(3) as ex:
        parsed = list(ex.map(lambda it: prep.parse_lot(chid, it, now), items))
    n = 0
    for rec, b in parsed:
        if b:
            bids[str(rec['cdid'])] = b
            n += 1
    json.dump(bids, open(os.path.join(D, 'bids.json'), 'w'), indent=1)
    return n, len(items)


def status_text(f):
    s, mx = f['status'], f['max_hammer']
    text = {'PASS': f"we pass, max ${mx:,}", 'CHROME': 'on the Chrome list, no max yet', 'FAIL': f"fails the rule (max ${mx:,})",
            'DROP': 'research found nothing, now on the Chrome list', 'EXCLUDED': 'excluded by the rules, scanning it now',
            'SKIPPED': 'the scan skipped it, scanning it again now', 'NOT SCANNED': 'not scanned, scanning it now',
            'NOT RESEARCHED': 'scanned but not researched, researching it now', 'NO PHOTOS': 'no photos on the site, nothing to scan'}.get(s, s)
    return text if not f.get('note') else f"{text.split(',')[0]}, {f['note']}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('chid')
    ap.add_argument('--refresh', action='store_true', help='re-read the lot pages first')
    ap.add_argument('--no-photos', action='store_true', help='no photo download for flagged lots without photos')
    ap.add_argument('--top', type=int, default=40, help='lots listed in the email (default 40)')
    args = ap.parse_args()
    chid = args.chid
    D = os.path.join(ROOT, 'pipeline', 'sales', chid)
    cat = json.load(open(os.path.join(D, 'cat.json')))
    lots = json.load(open(os.path.join(D, 'lots.json')))
    bids = json.load(open(os.path.join(D, 'bids.json'))) if os.path.exists(os.path.join(D, 'bids.json')) else {}
    today = datetime.datetime.now(prep.HOBART).date()
    closing_today = [r for r in lots if closes_on(r.get('close'), today)]
    nk = now_key()
    all_closed = all(prep.close_key(r.get('close')) < nk for r in lots if r.get('close'))

    if args.refresh:
        n, t = refresh(chid, D, lots, bids, everything=bool(closing_today))
        print(f'refreshed bids on {n} of {t} lots', file=sys.stderr)

    prof = build_profiles(history_rows())
    os.makedirs(os.path.dirname(PROFILES), exist_ok=True)
    json.dump({'built': prep.now_text(), 'bidders': len(prof), 'profiles': prof}, open(PROFILES, 'w'), indent=1)

    a_lots = {}
    if os.path.exists(os.path.join(D, 'assessment.json')):
        a_lots = {x['cdid']: x for x in json.load(open(os.path.join(D, 'assessment.json')))['lots']}
    verdict = {}
    for f in glob.glob(os.path.join(D, 'scans', '*.json')):
        for r in json.load(open(f)):
            verdict[r['cdid']] = r.get('verdict')

    flagged, unknown = [], set()
    for r in lots:
        b = bids.get(str(r['cdid'])) or {}
        hist = b.get('history') or []
        if not hist:
            continue
        seen = {}
        for h in hist:
            p = parse_who(h)
            k = bidder_key(p)
            e = seen.setdefault(k, {'who': h.get('who', ''), 'no': p['no'], 'town': p['town'], 'state': p['state'], 'n': 0, 'top': 0.0, 'tags': []})
            e['n'] += 1
            e['top'] = max(e['top'], money(h.get('amount')))
        lot_cat = r.get('cls_reason') if r.get('cls') == 'always_look' else ''
        score = 0
        for k, e in seen.items():
            pr = prof.get(k, {})
            st = e['state'] or pr.get('state') or ''   # a blank state is filled from the bidder's other sales
            if st not in ('', 'TAS'):
                e['tags'].append('interstate' if e['state'] else f'interstate, {st} in an earlier sale')
                score += 3
            elif not st and e['town']:
                unknown.add(e['town'])
            if pr.get('specialty') and pr['specialty'] == lot_cat:
                e['tags'].append(f"{pr['specialty']} specialist")
                score += 2
            elif pr.get('specialty'):
                e['tags'].append(f"usually bids on {pr['specialty']}")
            if pr.get('strong'):
                e['tags'].append(f"strong buyer: {pr['wins']} wins, median ${pr['median_win']:,.0f}")
                score += 1
            if pr.get('sales', 0) > 1:
                e['tags'].append(f"seen in {pr['sales']} sales")
        crowd = len(seen) >= 4 or len(hist) >= 8
        if crowd:
            score += 1
        if score == 0:
            continue
        leader = max(seen.values(), key=lambda e: e['top'])
        x = a_lots.get(r['cdid'])
        researched = os.path.exists(os.path.join(D, 'market', f"{r['cdid']}.json"))
        if x:
            status, mx = x['status'], x.get('max_hammer') or 0
        elif r.get('state') == 'EXCLUDED':
            status, mx = 'EXCLUDED', 0
        elif verdict.get(r['cdid']) == 'SKIP':
            status, mx = 'SKIPPED', 0
        elif r.get('state') == 'UNSCANNED':
            status, mx = 'NO PHOTOS', 0
        else:
            status, mx = 'NOT SCANNED', 0
        flagged.append({'cdid': r['cdid'], 'lot': r.get('lot'), 'title': r.get('title') or '', 'category': lot_cat, 'status': status,
                        'max_hammer': mx, 'current_bid': money(b.get('current_bid')), 'bid_count': len(hist), 'close': b.get('close') or r.get('close'),
                        'score': score, 'crowd': crowd, 'leader': leader['who'], 'researched': researched,
                        'bidders': sorted(seen.values(), key=lambda e: -e['top']),
                        'why': '; '.join(f"{e['who']} ({', '.join(e['tags'])})" for e in seen.values() if e['tags']) + ('; 4 or more bidders' if crowd else '')})
    flagged.sort(key=lambda f: (-f['score'], -f['current_bid']))

    # what to do about the flagged lots the funnel has not valued
    to_research, no_photos, to_chrome = [], [], 0
    for f in flagged:
        if f['researched']:
            if f['status'] in ('DROP', 'FAIL'):
                mf = os.path.join(D, 'market', f"{f['cdid']}.json")
                m = json.load(open(mf))
                if not m.get('needs_chrome') and not m.get('chrome_done'):
                    m['needs_chrome'] = True
                    m['chrome_hint'] = (m.get('chrome_hint') or '') + f" Bidder signal: {f['why']}. Look harder for sold prices of this exact item."
                    json.dump(m, open(mf, 'w'), indent=1)
                    to_chrome += 1
            continue
        if f['status'] not in ('EXCLUDED', 'SKIPPED', 'NOT SCANNED', 'NOT RESEARCHED'):
            continue
        lf = os.path.join(D, 'lots', f"{f['cdid']}.json")
        rec = json.load(open(lf)) if os.path.exists(lf) else {}
        if rec.get('state') == 'EXCLUDED' and not args.no_photos:  # an excluded lot has no photos yet
            rec['state'] = 'FETCHED'
            rec.pop('skip_photos', None)
            rec = prep.photos(rec, D)
            rec.pop('photo_err', None)
            json.dump(rec, open(lf, 'w'), indent=1)
            for s in lots:
                if s['cdid'] == rec['cdid']:
                    s.update({k: v for k, v in rec.items() if k != 'photo_ns'})
            json.dump(lots, open(os.path.join(D, 'lots.json'), 'w'), indent=1)
        if rec.get('state') != 'FETCHED' or not rec.get('photo_count'):
            if rec.get('state') == 'EXCLUDED':  # --no-photos: it stays excluded, say so
                f['note'] = 'photos not downloaded'
            else:
                f['status'] = 'NO PHOTOS'
            no_photos.append(f)
            continue
        to_research.append(f)

    wf_path = os.path.join(D, 'wfargs_bidders.json')
    if to_research:
        wf = json.load(open(os.path.join(D, 'wfargs.json'))) if os.path.exists(os.path.join(D, 'wfargs.json')) else {'chid': chid, 'name': cat.get('name')}
        wf.update({'root': D, 'pipeline': os.path.join(ROOT, 'pipeline'), 'titleChunks': 0, 'minStrength': 1,
                   'tagPrefix': 'bid' + datetime.datetime.now(prep.HOBART).strftime('%d%H%M') + '-',
                   'alwaysLook': [{'cdid': f['cdid'], 'lot': f['lot'], 'title': f['title'], 'why': 'bidder signal: ' + f['why']} for f in to_research]})
        json.dump(wf, open(wf_path, 'w'), indent=1)
        json.dump({str(f['cdid']): 'bidder signal: ' + f['why'] for f in to_research}, open(os.path.join(D, 'force.json'), 'w'), indent=1)
    elif os.path.exists(wf_path):
        os.remove(wf_path)

    json.dump({'checked': prep.now_text(), 'closing_today': len(closing_today), 'all_closed': all_closed, 'flagged': flagged,
               'to_research': [f['cdid'] for f in to_research], 'no_photos': [f['cdid'] for f in no_photos], 'to_chrome': to_chrome,
               'bidders_known': len(prof), 'unknown_towns': sorted(unknown)}, open(os.path.join(D, 'bidders.json'), 'w'), indent=1)

    inter = [f for f in flagged if any('interstate' in e['tags'] for e in f['bidders'])]
    towns = sorted({f"{e['town']} {e['state']}".strip() for f in inter for e in f['bidders'] if 'interstate' in e['tags']})
    spec = sum(1 for f in flagged if any('specialist' in t for e in f['bidders'] for t in e['tags']))
    lines = [f"Armitage {cat.get('name')}: bidder scan, {len(flagged)} lots with interstate or known bidders", '',
             f"{len(flagged)} lots carry a signal from their bidders: {len(inter)} with an interstate bidder"
             + (f" ({', '.join(towns[:12])})" if towns else '') + f", {spec} with a specialist, {sum(1 for f in flagged if f['crowd'])} with 4 or more bidders. "
             + (f"{len(to_research)} had not been valued and are being scanned and researched now. " if to_research else '')
             + (f"{to_chrome} that the research dropped go to the Chrome list instead. " if to_chrome else '')
             + (f"{len(no_photos)} have no photos on the site. " if no_photos else ''),
             f"Bidder history: {len(prof)} bidders known from past sales." + (f" {len(closing_today)} lots close today." if closing_today else ''), '']
    if flagged:
        lines.append('Lots, strongest signal first:')
        for f in flagged[:args.top]:
            lines.append(f"- Lot {f['lot']}: {f['title'][:60]}. {status_text(f)}. Bid ${f['current_bid']:,.0f} ({f['bid_count']} bids), closes {f['close']}. "
                         f"Bidders: " + '; '.join(f"{e['who']}" + (f" [{', '.join(e['tags'])}]" if e['tags'] else '') + (' leads' if e is f['bidders'][0] else '')
                                                  for e in f['bidders'][:5]) + ('; ...' if len(f['bidders']) > 5 else ''))
        if len(flagged) > args.top:
            lines.append(f"... and {len(flagged) - args.top} more in bidders.json")
    if unknown:
        lines += ['', f"Hometowns not known to be Tasmanian (treated as unknown, not interstate): {', '.join(sorted(unknown)[:20])}"]
    lines += ['', f"Catalogue: {BASE}/catalogue-group.aspx?chid={chid}"]
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
