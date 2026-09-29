#!/usr/bin/env python3
"""Usage: refresh_bids.py <auction> <cdid> [<cdid> ...]  (text only). Prints JSON {cdid: {current_bid, bid_count, checked}}"""
import sys,re,json,subprocess,time,datetime
CH={'1':28711,'2':28712}; a=sys.argv[1]; out={}
for cd in sys.argv[2:]:
    time.sleep(1)
    h=subprocess.run(['curl','-sS','--max-time','30',f'https://armitage.bidsonline.com.au/catalogue_detail.aspx?cdid={cd}&chid={CH[a]}&category=ALL&style=group'],capture_output=True).stdout.decode('utf8','ignore')
    t=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',re.sub(r'<script.*?</script>','',h,flags=re.S)))
    cur=re.search(r'Current Bid \(\$\): (\$[\d,\.]+|[^ ]+)',t)
    rows=re.findall(r'<tr>\s*<td>[^<]*</td>\s*<td>\d+</td>\s*<td>[\d\.,]+</td>\s*<td>[\d/: APM]+</td>',h)
    out[cd]={'current_bid':cur.group(1) if cur else None,'bid_count':len(rows),'checked':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=10))).strftime('%d/%m/%Y %H:%M AEST')}
print(json.dumps(out))
