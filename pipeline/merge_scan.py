#!/usr/bin/env python3
"""Usage: python3 pipeline/merge_scan.py <saledir> <tag> <cdid> [<cdid> ...]

Merges the lot records of one scan batch (pipeline/sales/<chid>/lots/<cdid>.json) with the
scan agent's observations (obs/<tag>.json, keyed by cdid) into scans/<tag>.json and prints
the batch summary as JSON. A lot counts as SCANNED only when photos_viewed equals its
photo_count; only SCANNED lots may be CANDIDATE or SKIP.
"""
import json
import os
import sys

D, tag, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
obs_file = os.path.join(D, 'obs', f'{tag}.json')
obs = json.load(open(obs_file)) if os.path.exists(obs_file) else {}
force_file = os.path.join(D, 'force.json')  # written by bidders.py: lots to research whatever the scan thinks of them
force = json.load(open(force_file)) if os.path.exists(force_file) else {}
out, counts = [], {}
for cdid in ids:
    r = json.load(open(os.path.join(D, 'lots', f'{cdid}.json')))
    o = obs.get(str(cdid))
    if r.get('state') == 'FETCHED':
        if o and int(o.get('photos_viewed', 0) or 0) == r.get('photo_count'):
            r.update(o)
            r['state'] = 'SCANNED'
            if r.get('verdict') not in ('CANDIDATE', 'SKIP'):
                r['verdict'] = 'SKIP'
                r['reason'] = r.get('reason') or 'no reason given'
            if str(cdid) in force and r['verdict'] == 'SKIP':
                r['verdict'] = 'CANDIDATE'
                r['strength'] = max(int(r.get('strength') or 0), 4)
                r['reason'] = f"{force[str(cdid)]}; the scan said: {r.get('reason')}"
        else:
            r['state'] = 'UNSCANNED'
            r['reason'] = 'photos not all viewed' if o else 'no observation recorded'
            r['verdict'] = None
    out.append(r)
    counts[r['state']] = counts.get(r['state'], 0) + 1
os.makedirs(os.path.join(D, 'scans'), exist_ok=True)
json.dump(out, open(os.path.join(D, 'scans', f'{tag}.json'), 'w'), indent=1)
cands = [{k: x.get(k) for k in ('cdid', 'lot', 'title', 'reason', 'strength', 'findings', 'condition')} for x in out if x.get('verdict') == 'CANDIDATE']
interest = [{'cdid': x['cdid'], 'lot': x.get('lot'), **x['interest']} for x in out if isinstance(x.get('interest'), dict)]
print(json.dumps({'counts': counts, 'unscanned': [{'cdid': x['cdid'], 'reason': x.get('reason')} for x in out if x['state'] == 'UNSCANNED'],
                  'candidates': cands, 'interest': interest}))
