#!/usr/bin/env python3
"""Builds work/gowans363.html (Gowans Weekly Friday Auction) from work/gowans363_result.json and scans/g3_*.json."""
import json, glob, os, base64, html, re, datetime
from PIL import Image
W = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(W)
E = html.escape; PREM = 1.198
def load(p, default=None): return json.load(open(p)) if os.path.exists(p) else default
def money(s):
    m = re.search(r'[\d,]+(?:\.\d+)?', s or ''); return float(m.group(0).replace(',', '')) if m else None
def close_key(c):
    m = re.match(r'(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+) ([AP])M', c or '')
    if not m: return 0
    d, mo, y, h, mi, s, ap = m.groups(); h = int(h) % 12 + (12 if ap == 'P' else 0)
    return int(y) * 1e10 + int(mo) * 1e8 + int(d) * 1e6 + h * 1e4 + int(mi) * 100 + int(s)
def short_close(c): return (c or '').replace('6/10/2026 ', '').replace(' AEST', '')
def thumb(cd):
    p = f'{W}/thumbs/{cd}.jpg'; src = f'{W}/photos/{cd}_1.jpg'
    if not os.path.exists(p) and os.path.exists(src):
        im = Image.open(src).convert('RGB'); im.thumbnail((240, 240)); im.save(p, quality=60)
    return f'<img class="th" alt="" src="data:image/jpeg;base64,{base64.b64encode(open(p,"rb").read()).decode()}">' if os.path.exists(p) else '<div class="th none">no photo</div>'
CAT = {'g3': dict(name='Weekly Friday Auction', chid=363, closes='Fri 2 Oct 2026, live from 10:00 AM (absentee bids close 9:30 AM)', lots='1,352 lots')}
res = load(f'{W}/gowans363_result.json', {'lots': [], 'not_researched': [], 'interest': []})
mk = {p['cdid']: p for p in res['lots']}
D = {}
for k in CAT:
    recs = {}
    for f in sorted(glob.glob(f'{R}/scans/{k}_*.json')):
        for x in json.load(open(f)):
            if x['state'] == 'SCANNED' or x['cdid'] not in recs: recs[x['cdid']] = x
    D[k] = dict(recs=recs, refresh=load(f'{W}/refresh_{k}.json', {}), interest=[i for i in res.get('interest', []) if i.get('key') == k], nr={x['cdid']: x for x in res.get('not_researched', [])})

def age_flag(date):
    m = re.search(r'(20\d\d)', date or '')
    if not m: return ''
    y = int(m.group(1))
    return ' <span class="pill warn">over 24 months old</span>' if y <= 2023 else (' <span class="pill low">about 2 years old</span>' if y == 2024 else '')
def ev_list(items, kind, label, hint):
    if not items: return f'<div class="ev {kind}"><h5>{label}</h5><p class="mut small">None found.</p></div>'
    li = ''.join(f'<li><a href="{E(x.get("url") or "#")}" target="_blank" rel="noopener">{E(str(x.get("price","")))}</a> <span class="mut">{E(str(x.get("date","")))}, {E(str(x.get("venue","")))}</span>{age_flag(x.get("date")) if kind != "ask" else ""}<br><span class="small">{E((x.get("note") or "")[:260])}</span></li>' for x in items)
    return f'<div class="ev {kind}"><h5>{label}</h5><p class="small mut">{hint}</p><ul>{li}</ul></div>'
def card(p, k):
    d = D[k]; rec = d['recs'].get(p['cdid'], {}); rf = d['refresh'].get(str(p['cdid']), {})
    bid = rf.get('current_bid') or rec.get('current_bid'); chk = rf.get('checked') or rec.get('checked'); bc = rf.get('bid_count', rec.get('bid_count'))
    bm = money(bid); allin = f'${bm*PREM:,.2f}' if bm else 'no bids yet'
    bidtxt = (f'{E(bid)} ({bc} bids)' if bm else 'No bids yet') + f' <span class="mut">at {E(chk or "")}</span>'
    t = p['triage']; kk, f = p.get('keep_max_hammer') or 0, p.get('flip_max_hammer') or 0
    if t == 'KEEP': mx = f'KEEP max hammer ${kk:,.0f} (all-in ${kk*PREM:,.2f})'
    elif t == 'FLIP': mx = f'FLIP max hammer ${f:,.0f} (all-in ${f*PREM:,.2f})'
    elif t == 'BOTH': mx = f'KEEP max ${kk:,.0f}, FLIP max ${f:,.0f} (hammer)'
    else: mx = 'No maximum bid (no sold support)'
    over = ''
    cls = {'KEEP': 'keep', 'FLIP': 'flip', 'BOTH': 'keep'}.get(t, 'near')
    lo, hi = p.get('guide_low_aud'), p.get('guide_high_aud')
    guide = f'${lo:,.0f} to ${hi:,.0f}' if (lo or hi) else 'none'
    q = f'<p class="q"><b>Ask Gowans:</b> {E(p["question_for_gowans"])}</p>' if p.get('question_for_gowans') else ''
    return f'''<article class="lot {cls}" data-close="{close_key(rec.get('close'))}">
<div class="lh">{thumb(p['cdid'])}<div class="lt"><h4><a href="{E(rec.get('url','#'))}" target="_blank" rel="noopener">Lot {E(str(rec.get('lot_label') or p['lot']))}</a> <span class="mut">sold live in lot order from 10 AM</span></h4>
<p class="what">{E(p['what_it_is'][:300])}</p><p><span class="pill {p['confidence'].lower()}">{E(p['confidence'])} confidence</span> <span class="pill low">score {p.get('market_score')}/10</span> {over}</p></div></div>
<dl class="kv"><dt>Photo findings</dt><dd>{E((p.get('key_photo_findings') or '')[:400])}</dd><dt>Condition</dt><dd>{E((p.get('condition') or '')[:250])}</dd>
<dt>Absentee bids so far</dt><dd>{rec.get('bid_count', 0)} <span class="mut">(amounts are not shown on this site)</span></dd><dt>Suggested max</dt><dd><b>{E(mx)}</b> <span class="mut">(all-in = hammer x 1.198)</span></dd>
<dt>Market guide</dt><dd>{guide} <span class="mut">{E(p.get('guide_summary') or '')}</span></dd></dl>
<div class="evs">{ev_list(p.get('sold', []), 'sold', 'Sold (price paid)', 'Only these set a maximum bid.')}{ev_list(p.get('unsold', []), 'unsold', 'Unsold (ceiling signal)', 'Did not sell. Not a value.')}{ev_list(p.get('asking', []), 'ask', 'Asking (not a price paid)', 'Optimistic. Never used for a max.')}</div>
<details><summary>Working and confidence</summary><p class="small"><b>Why {E(p['confidence'])}:</b> {E(p.get('confidence_reason') or '')}</p><p class="small"><b>Dropped entries:</b> {E(p.get('dropped_entries') or 'none')}</p><p class="small"><b>Working:</b> {E(p['working'])}</p></details>{q}</article>'''

def coverage(k):
    d = D[k]; recs = d['recs']; C = CAT[k]; n = lambda s: sum(1 for x in recs.values() if x['state'] == s)
    unsc = [x for x in recs.values() if x['state'] == 'UNSCANNED']
    un = ''.join(f'<li>cdid {x["cdid"]}: {E(str(x.get("reason")))}</li>' for x in unsc) or '<li>None.</li>'
    ids = len(open(f'{W}/index_{k}.txt').read().split())
    return f'''<div class="cov"><h3>{C["name"]}</h3><p class="mut">Auction {C["chid"]}, {C["closes"]}</p>
<dl class="kv"><dt>Lots in the auction (from the site API)</dt><dd>{ids}</dd><dt>Lots scanned, every photo viewed</dt><dd>{n('SCANNED')}</dd><dt>Not in this sale</dt><dd>{n('NOT_IN_SALE')}</dd><dt>Unscanned</dt><dd>{len(unsc)}</dd></dl><ul class="plain">{un}</ul></div>'''

def table_all(k):
    d = D[k]; rows = []
    for cd, x in sorted(d['recs'].items(), key=lambda kv: (kv[1].get('lot') or 0, str(kv[1].get('lot_label') or ''))):
        if x['state'] != 'SCANNED': continue
        p = mk.get(cd); tri = p['triage'] if p else ('SKIP' if x.get('verdict') != 'CANDIDATE' else 'CANDIDATE, not researched')
        sc = p['market_score'] if p else (d['nr'].get(cd, {}).get('strength') if cd in d['nr'] else x.get('strength'))
        finding = (p.get('key_photo_findings') if p else x.get('findings')) or ''
        why = (p.get('score_reason') if p else (d['nr'].get(cd, {}).get('rescore_note') or x.get('reason'))) or ''
        rows.append(f'<tr><td><a href="{E(x["url"])}" target="_blank" rel="noopener">{E(str(x.get("lot_label") or x["lot"]))}</a></td><td>{E((x.get("title") or "")[:80])}</td><td>{x.get("photo_count")}</td><td>{E(str(tri))}</td><td>{sc if sc is not None else ""}</td><td>{E(finding[:170])}</td><td>{E(why[:150])}</td><td>{x.get("bid_count", 0)}</td></tr>')
    return f'<details><summary>Every lot in this catalogue ({len(rows)}), with photos viewed and a finding</summary><div class="tw"><table><thead><tr><th>Lot</th><th>Title</th><th>Photos</th><th>Result</th><th>Score</th><th>What the photos show</th><th>Why</th><th>Absentee bids</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></details>'

def section(k):
    d = D[k]; C = CAT[k]
    L = [p for p in res['lots'] if d['recs'].get(p['cdid'])]
    srt = lambda ks: sorted([p for p in L if p['triage'] in ks], key=lambda p: (p['lot'], p['cdid']))
    out = [f'<section id="{k}"><h2>{C["name"]} ({C["lots"]}, closes {C["closes"]})</h2>']
    for ks, title, empty, note in ((('FLIP',), 'FLIP picks (buy to resell)', 'None. No lot had sold support for a resale ceiling.', ''), (('KEEP',), 'KEEP picks (buy to own)', 'None.', ''), (('BOTH',), 'BOTH picks (keep or resell)', 'None.', '')):
        items = srt(ks); out.append(f'<h3>{title}</h3>' + (''.join(card(p, k) for p in items) if items else f'<p class="mut">{empty}</p>'))
    lv = srt(('LOOK AT VIEWING',))
    out.append('<h3>Look at the inspection</h3><p class="small">A credible identification with real-looking value, but no sold support, so no maximum bid. Inspection is Friday from 8:30 AM at 37 Main Road, Moonah. Phone (03) 6278 1600.</p>' + (''.join(card(p, k) for p in lv) or '<p class="mut">None.</p>'))
    out.append('<h3>Near misses</h3>' + (''.join(card(p, k) for p in srt(('NEAR MISS',))) or '<p class="mut">None.</p>'))
    it = d['interest']
    if it:
        rows = ''.join(f'<tr><td><a href="{E(d["recs"].get(x["cdid"],{}).get("url","#"))}" target="_blank" rel="noopener">{E(str(d["recs"].get(x["cdid"],{}).get("lot_label") or x["lot"]))}</a></td><td>{E(d["recs"].get(x["cdid"],{}).get("title") or "")[:60]}</td><td>{E(x["kind"])}</td><td>{E(x["note"])}</td></tr>' for x in sorted(it, key=lambda x: x['lot']))
        out.append(f'<h3>For interest: wine, whisky and watches</h3><div class="tw"><table><thead><tr><th>Lot</th><th>Title</th><th>Kind</th><th>Notes</th></tr></thead><tbody>{rows}</tbody></table></div>')
    out.append(table_all(k)); out.append('</section>'); return ''.join(out)

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=10))).strftime('%d/%m/%Y %H:%M AEST')
refreshed = sorted({v['checked'] for k in D for v in D[k]['refresh'].values()})
ref_txt = f'{refreshed[0]} to {refreshed[-1]}' if refreshed else 'not yet'
meta = load(f'{W}/gowans363_meta.json', {})
CSS = open(f'{W}/page.css').read()
page = f'''<title>Gowans Friday Auction</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Public+Sans:wght@400;500;700&display=swap">
<style>{CSS}</style>
<main class="wrap">
<header><p class="eyebrow">Gowans Auctions, Moonah. Weekly Friday auction, Fri 2 Oct 2026</p><h1>Gowans Friday auction</h1>
<p class="lead">{meta.get('bottom_line','')}</p></header>
<section class="status"><h2>Run details</h2>
<dl class="kv"><dt>Deadline</dt><dd><b>Online absentee bids close 9:30 AM Friday 2 Oct (Hobart).</b> The live room auction starts at 10 AM, in lot order. After 9:30 AM, ring the office to leave an absentee bid. Winning bidders are emailed by 5 PM Friday. If two absentee bids are the same amount, the first one placed wins.</dd>
<dt>Inspection</dt><dd>Friday from 8:30 AM (Thursday 9 AM to 5:30 PM has passed). Gowans, 37 Main Road, Moonah, phone (03) 6278 1600.</dd>
<dt>Buyer's premium</dt><dd>19.8% including GST on the hammer price, on all lots except vehicles (contact the office). This is the auction's own notice, so the older 17.6% on the support page looks out of date. All-in = hammer x 1.198.</dd>
<dt>Mode</dt><dd>Lot data and photos came from Gowans' public API and image store. Read-only: no bids, logins or forms. There are no prices on this site, only a count of absentee bids.</dd>
<dt>Collection</dt><dd>Pickup from 37 Main Road, Moonah. Inbound freight assumed $0 (local).</dd>
<dt>Page built</dt><dd>{now}.</dd>
<dt>Blocked or login sources</dt><dd>eBay, Wine-Searcher and Australian Whisky Auctions are closed to this session (403 from the sites). Artrecord and AASD rate-limit and hide prices. No logins were tried.</dd>
<dt>Resume point</dt><dd>Workflow run {meta.get('run','')}. Batch files are in scans/ (g3_), one per batch.</dd></dl>
<div class="covs">{coverage('g3')}</div>
<details open><summary>Assumptions</summary><ul class="plain">{''.join('<li>'+x+'</li>' for x in meta.get('assumptions',[]))}</ul></details></section>
{section('g3')}
<footer class="small">Only sold prices with a URL and a date set maximum bids. "No comps" means no maximum bid. Built by Claude Code.</footer>
</main>'''
open(f'{W}/gowans363.html', 'w').write(page); print('built', len(page) // 1024, 'KB')
