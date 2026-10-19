#!/usr/bin/env python3
"""Merge the lots 1-600 (chid 28838) workflow pieces into armitage28838_result.json.
Verified lots come from every active run's verify results (journal) plus the *_verified_*.json backups.
Counts, interest and not_researched come from the original eight runs' scan and rescore results."""
import json, glob, os, collections
W = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(f'{W}/armitage28838_runs.json')); runs = R['runs']
base = '/root/.claude/projects/-home-user-Armitage/b111cc0b-3b39-598b-9bc6-fe519f4d82c3/subagents/workflows/'
orig = {1: 'wf_6c3fc591-b70', 2: 'wf_1a9e60ca-cdc', 3: 'wf_4b20c8f2-d61', 4: 'wf_28039263-46b', 5: 'wf_98f0f38a-7d5', 6: 'wf_c5343a79-a12', 7: 'wf_fb9b540c-27e', 8: 'wf_7b983c9e-14e'}

def events(path):
    try: return [json.loads(l) for l in open(path) if l.strip()]
    except FileNotFoundError: return []

V, finished, unfinished = {}, [], []
for k in R['active']:
    ev = events(runs[k]['journal'])
    starts = {e['key']: e for e in ev if e.get('type') == 'started'}
    done = any(e.get('type') not in ('launched', 'started', 'result') for e in ev)
    (finished if done else unfinished).append(k)
    for e in ev:
        if e.get('type') != 'result': continue
        lab = (starts.get(e.get('key')) or {}).get('label', '')
        r = e.get('result')
        if lab.startswith('verify') and isinstance(r, dict):
            for l in r.get('lots') or []: V[l['cdid']] = l
for f in glob.glob(f'{W}/armitage28838*_verified_*.json'):
    try:
        for l in json.load(open(f)).get('lots') or []: V.setdefault(l['cdid'], l)
    except Exception: pass

# manual overrides from my own research, applied on top of the verified lots (keyed by cdid as a string)
try:
    for cd, patch in json.load(open(f'{W}/armitage28838_overrides.json')).items():
        rec = V.get(int(cd)) or {'cdid': int(cd)}
        rec.update(patch); V[int(cd)] = rec
except FileNotFoundError:
    pass

counts = collections.Counter(); interest = []; cands = {}; scores = {}; unscanned = []
for n, run in orig.items():
    args = json.load(open(f'{W}/armitage28838_wfargs_p{n}.json')); tags = {b['tag'] for b in args['batches']}
    ev = events(base + run + '/journal.jsonl'); starts = {e['key']: e for e in ev if e.get('type') == 'started'}
    seen = set()
    for e in ev:
        if e.get('type') != 'result': continue
        lab = (starts.get(e.get('key')) or {}).get('label', ''); r = e.get('result')
        if lab.startswith('scan ') and isinstance(r, dict):
            tag = int(lab.split(':')[1])
            if tag in tags and tag not in seen:
                seen.add(tag)
                for kk, vv in (r.get('counts') or {}).items(): counts[kk] += vv or 0
                interest.extend(r.get('interest') or []); unscanned.extend(r.get('unscanned') or [])
                for c in r.get('candidates') or []: cands[c['cdid']] = dict(c, key='a8')
        if lab.startswith('rescore') and isinstance(r, dict):
            for x in r.get('scores') or []: scores[x['cdid']] = x
for cd, c in cands.items():
    c['strength_scan'] = c.get('strength')
    if cd in scores: c['strength'] = scores[cd]['score']; c['rescore_note'] = scores[cd]['rationale']
to_research = [c for c in cands.values() if (c.get('strength') or 0) >= 4]
not_researched = [{k: c.get(k) for k in ('cdid', 'lot', 'key', 'title', 'reason', 'strength', 'strength_scan', 'rescore_note')} for c in cands.values() if (c.get('strength') or 0) < 4]
partial = bool(unfinished)
out = {'batches': 40, 'counts': dict(counts), 'unscanned_after_retry': unscanned, 'candidates_total': len(cands), 'to_research': len(to_research),
       'not_researched': not_researched, 'interest': interest, 'lots': sorted(V.values(), key=lambda l: l['lot']),
       'missing': [c['cdid'] for c in to_research if c['cdid'] not in V], 'partial': partial,
       'runs_finished': finished, 'runs_unfinished': unfinished}
json.dump(out, open(f'{W}/armitage28838_result.json', 'w'), indent=1)
print(f"verified {len(V)} of {len(to_research)} researched lots; candidates {len(cands)}; counts {dict(counts)}; finished {len(finished)} unfinished {len(unfinished)}; partial={partial}")
