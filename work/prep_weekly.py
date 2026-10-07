#!/usr/bin/env python3
"""Usage: prep_weekly.py <auction_id> <key> "<close text>"
Prepare a Gowans Weekly Friday Auction from the public API data already fetched into work/gw<id>/lots_raw.json.
Downloads every large photo from S3 (8 threads), builds contact sheets, writes raw_g3_<tag>.json batches of 15 and index_g3.txt."""
import json, os, re, sys, time, subprocess, datetime
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
W=os.path.dirname(os.path.abspath(__file__)); AID,KEY,CLOSE=sys.argv[1],sys.argv[2],sys.argv[3]
L=json.load(open(f'{W}/gw{AID}/lots_raw.json'))
lots=[x for x in L if x['attributes']['title']!='AUCTION INFORMATION' and x['attributes']['number']]
lots.sort(key=lambda x:x['attributes']['ordering'])
def dl(job):
    url,out=job
    if os.path.exists(out) and os.path.getsize(out)>1000: return True
    for a in range(3):
        r=subprocess.run(['curl','-sS','-L','--max-time','40','-o',out,'-w','%{http_code}',url],capture_output=True)
        if r.stdout.decode()[-3:]=='200' and os.path.getsize(out)>1000: return True
        time.sleep(2*(a+1))
    if os.path.exists(out): os.remove(out)
    return False
jobs=[]; meta={}
for x in lots:
    a=x['attributes']; cd=int(x['id']); paths=[]
    for i,im in enumerate(a['image_urls'],1):
        u=(im.get('large') or im.get('medium') or list(im.values())[0])['url']; out=f'{W}/photos/{cd}_{i}.jpg'; jobs.append((u,out)); paths.append(out)
    meta[cd]=paths
print(len(lots),'lots',len(jobs),'photos',flush=True)
t0=time.time()
with ThreadPoolExecutor(8) as ex: ok=list(ex.map(dl,jobs))
print('downloaded',sum(ok),'of',len(jobs),'in',int(time.time()-t0),'s',flush=True)
def sheet(paths,cd,lab):
    ims=[Image.open(p).convert('RGB') for p in paths]; n=len(ims); cols=1 if n==1 else 2
    rows=(n+cols-1)//cols; cw,chh=(800,600) if n==1 else (600,450)
    S=Image.new('RGB',(cols*cw,rows*chh),'white'); d=ImageDraw.Draw(S)
    for i,im in enumerate(ims):
        im.thumbnail((cw,chh)); xx,yy=(i%cols)*cw,(i//cols)*chh; S.paste(im,(xx,yy))
        d.rectangle([xx,yy,xx+170,yy+20],fill='black'); d.text((xx+4,yy+4),f'lot {lab} photo {i+1}/{n}',fill='yellow')
    out=f'{W}/sheets/{cd}.jpg'; S.save(out,quality=85); return out
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=10))).strftime('%d/%m/%Y %H:%M:%S AEST')
recs=[]
for x in lots:
    a=x['attributes']; cd=int(x['id']); label=a['number']; paths=[p for p in meta[cd] if os.path.exists(p)]
    digits=re.sub(r'\D','',label) or '0'
    rec={'cdid':cd,'auction':KEY,'url':f'https://www.gowansauctions.com.au/auction/{AID}','http':200,'lot':int(digits),'lot_label':label,
         'close':CLOSE,'premium':'19.8%',
         'title':a['title'],'description':(a['title']+(' | '+a['description'] if a['description'] else '')).strip(),'estimate':None,
         'current_bid':None,'bid_count':a['bid_count'],'checked':now,'photo_id':str(cd),'photo_count':len(paths),'photo_files':paths}
    if paths: rec['state']='FETCHED'; rec['sheet']=sheet(paths,cd,label)
    else: rec['state']='UNSCANNED'; rec['reason']='no photo'
    recs.append(rec)
batches=[]
for i in range(0,len(recs),15):
    c=recs[i:i+15]; tag=c[0]['cdid']
    json.dump(c,open(f'{W}/raw_{KEY}_{tag}.json','w'),indent=1); batches.append({'key':KEY,'tag':tag,'ids':[r['cdid'] for r in c]})
json.dump({'batches':batches},open(f'{W}/gowans{AID}_args.json','w'),separators=(',',':'))
open(f'{W}/index_{KEY}.txt','w').write('\n'.join(str(r['cdid']) for r in recs))
print(len(batches),'batches written; no-photo lots',sum(1 for r in recs if r['state']!='FETCHED'),flush=True)
