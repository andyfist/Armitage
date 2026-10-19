import sys,re,json,subprocess,time,datetime
W='/home/user/Armitage/work'
for pair in sys.argv[1:]:
    chid,key=pair.split(':')
    R=json.load(open(f'{W}/armitage{chid}_result.json')); F=f'{W}/refresh_{key}.json'; ref=json.load(open(F))
    n=0
    for p in R['lots']:
        cd=p['cdid']; time.sleep(0.8)
        h=subprocess.run(['curl','-sS','--max-time','30',f'https://armitage.bidsonline.com.au/catalogue_detail.aspx?cdid={cd}&chid={chid}&category=ALL&style=group'],capture_output=True).stdout.decode('utf8','ignore')
        t=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',re.sub(r'<script.*?</script>','',h,flags=re.S)))
        cur=re.search(r'Current Bid \(\$\): (\$[\d,\.]+|[^ ]+)',t)
        if not cur: print('nobid',chid,cd,flush=True); continue
        rows=re.findall(r'<tr>\s*<td>[^<]*</td>\s*<td>\d+</td>\s*<td>[\d\.,]+</td>\s*<td>[\d/: APM]+</td>',h)
        r=ref.setdefault(str(cd),{}); r.update(current_bid=cur.group(1),bid_count=len(rows),checked=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=11))).strftime('%d/%m/%Y %H:%M AEDT')); n+=1
    json.dump(ref,open(F,'w'),indent=0); print(chid,'updated',n,'of',len(R['lots']),flush=True)
