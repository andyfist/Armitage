#!/usr/bin/env python3
"""Usage: merge_scan.py <auction> <first_cdid>
Merges work/raw_<a>_<f>.json (fetch tool output) with work/obs_<a>_<f>.json (agent observations, keyed by cdid)
into scans/<a>_<f>.json. Enforces: SCANNED only if photos_viewed == photo_count; only SCANNED lots may be CANDIDATE/SKIP."""
import sys, json, os
a,f=sys.argv[1],sys.argv[2]; W=os.path.dirname(os.path.abspath(__file__))
raw=json.load(open(f'{W}/raw_{a}_{f}.json')); obs=json.load(open(f'{W}/obs_{a}_{f}.json')) if os.path.exists(f'{W}/obs_{a}_{f}.json') else {}
out=[]; cnt={}
for r in raw:
    r=dict(r); r.pop('photo_files',None); o=obs.get(str(r['cdid']))
    if r['state']=='FETCHED':
        if o and int(o.get('photos_viewed',0))==r['photo_count']:
            r.update(o); r['state']='SCANNED'
            if r.get('verdict') not in ('CANDIDATE','SKIP'): r['verdict']='SKIP'; r['reason']=r.get('reason') or 'no reason given'
        else:
            r['state']='UNSCANNED'; r['reason']='photos not all viewed' if o else 'no observation recorded'; r['verdict']=None
    out.append(r); cnt[r['state']]=cnt.get(r['state'],0)+1
os.makedirs(f'{W}/../scans',exist_ok=True)
json.dump(out,open(f'{W}/../scans/{a}_{f}.json','w'),indent=1)
cands=[{k:x.get(k) for k in('cdid','lot','title','estimate','current_bid','reason','strength','findings','condition')} for x in out if x.get('verdict')=='CANDIDATE']
print(json.dumps({'counts':cnt,'unscanned':[[x['cdid'],x.get('reason')] for x in out if x['state']=='UNSCANNED'],'candidates':cands}))
