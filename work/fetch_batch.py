#!/usr/bin/env python3
"""Usage: fetch_batch.py <auction 1|2> <first_cdid> <last_cdid>
Read-only. Fetches lot pages + photos (about 1 request/sec), writes work/raw_<auction>_<first>.json
and contact sheets work/sheets/<cdid>.jpg (plus work/sheets/<cdid>_full.txt listing photo paths)."""
import sys, re, json, time, subprocess, html, os, datetime
from PIL import Image, ImageDraw
BASE='https://armitage.bidsonline.com.au'
CH={'1':28711,'2':28712}; RANGE={'1':(1,496),'2':(601,961)}
W=os.path.dirname(os.path.abspath(__file__))
def curl(url, out=None):
    for attempt in range(3):
        cmd=['curl','-sS','--max-time','30','-w','%{http_code}']+(['-o',out] if out else [])+[url]
        r=subprocess.run(cmd,capture_output=True)
        code=(r.stdout if out else r.stdout[-3:]).decode()[-3:]
        if code=='200': return (None if out else r.stdout[:-3]), 200
        if code in ('404',): return None, 404
        time.sleep(20*(attempt+1))
    return None, int(code) if code.isdigit() else 0
def strip(h): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',re.sub(r'<script.*?</script>|<style.*?</style>','',h,flags=re.S)))).strip()
def parse(cd, ch, auction):
    time.sleep(1)
    body,code=curl(f'{BASE}/catalogue_detail.aspx?cdid={cd}&chid={ch}&category=ALL&style=group')
    rec={'cdid':cd,'auction':auction,'url':f'{BASE}/catalogue_detail.aspx?cdid={cd}&chid={ch}&category=ALL&style=group','http':code}
    if code!=200: rec['state']='UNSCANNED'; rec['reason']=f'http {code}'; return rec,None
    h=body.decode('utf8','ignore'); t=strip(h)
    lot=re.search(r'Lot No\. ?(\d+)',t); close=re.search(r'Auction Closes: (\d+/\d+/\d+ [\d:]+ [AP]M \w+)',t)
    desc=re.search(r'Description:(.*?)Estimate:',t); est=re.search(r'Estimate: Estimate ([^ ]+(?: ?- ?[^ ]+)?)',t)
    cur=re.search(r'Current Bid \(\$\): (\$[\d,\.]+|[^ ]+)',t)
    title=re.search(r'<h2 class="post-title">(.*?)<span',h,flags=re.S)
    rows=re.findall(r'<tr>\s*<td>[^<]*</td>\s*<td>\d+</td>\s*<td>[\d\.,]+</td>\s*<td>[\d/: APM]+</td>',h)
    rec.update(lot=int(lot.group(1)) if lot else None, close=close.group(1) if close else None,
      title=strip(title.group(1)) if title else None, description=desc.group(1).strip() if desc else None,
      estimate=est.group(1) if est else None, current_bid=cur.group(1) if cur else None, bid_count=len(rows),
      checked=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=10))).strftime('%d/%m/%Y %H:%M:%S AEST'))
    lo,hi=RANGE[auction]
    if not rec['lot'] or not rec['close'] or not rec['close'].startswith('30/09/2026') or not lo<=rec['lot']<=hi:
        rec['state']='NOT_IN_SALE'; return rec,None
    ids=re.findall(r'products/(\d+)_(\d+)\.jpg',h); pid=ids[0][0] if ids else None
    return rec,pid
def photos(pid,cd):
    paths=[]
    for n in range(1,40):
        out=f'{W}/photos/{cd}_{n}.jpg'; time.sleep(1)
        _,code=curl(f'{BASE}/images/products/{pid}_{n}.jpg',out)
        if code==200: paths.append(out)
        else:
            if os.path.exists(out): os.remove(out)
            if code==404: break
            return paths,f'photo _{n} http {code}'
    return paths,None
def sheet(paths,cd,lot):
    ims=[Image.open(p).convert('RGB') for p in paths]; n=len(ims); cols=1 if n==1 else 2
    rows=(n+cols-1)//cols; cw,chh=(800,600) if n==1 else (600,450)
    S=Image.new('RGB',(cols*cw,rows*chh),'white'); d=ImageDraw.Draw(S)
    for i,im in enumerate(ims):
        im.thumbnail((cw,chh)); x,y=(i%cols)*cw,(i//cols)*chh; S.paste(im,(x,y))
        d.rectangle([x,y,x+150,y+20],fill='black'); d.text((x+4,y+4),f'lot {lot} photo {i+1}/{n}',fill='yellow')
    out=f'{W}/sheets/{cd}.jpg'; S.save(out,quality=85); return out
if __name__=='__main__':
    a,f,l=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]); res=[]
    for cd in range(f,l+1):
        rec,pid=parse(cd,CH[a],a)
        if pid:
            ps,err=photos(pid,cd); rec['photo_id']=pid; rec['photo_count']=len(ps); rec['photo_files']=ps
            if err or not ps: rec['state']='UNSCANNED'; rec['reason']=err or 'no photos'
            else: rec['state']='FETCHED'; rec['sheet']=sheet(ps,cd,rec['lot'])
        elif rec.get('state') is None: rec['state']='UNSCANNED'; rec['reason']='no photo id'
        res.append(rec); print(cd,rec.get('lot'),rec['state'],rec.get('photo_count'),flush=True)
    json.dump(res,open(f'{W}/raw_{a}_{f}.json','w'),indent=1)
