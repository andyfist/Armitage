#!/usr/bin/env python3
"""Usage: build_armitage.py <slug> <chid>:<key> [<chid>:<key> ...]
Builds work/armitage_<slug>.html from, per catalogue, work/armitage<chid>_result.json, armitage<chid>_cat.json,
refresh_<key>.json and scans/<key>_*.json, plus work/armitage_<slug>_meta.json (title, bottom_line, run, assumptions)."""
import json, glob, os, base64, html, re, datetime, sys
from PIL import Image
SLUG = sys.argv[1]; PAIRS = [a.split(':') for a in sys.argv[2:]]
W = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(W)
E = html.escape; PREM = 1.22
def load(p, default=None): return json.load(open(p)) if os.path.exists(p) else default
def money(s):
    m = re.search(r'[\d,]+(?:\.\d+)?', s or ''); return float(m.group(0).replace(',', '')) if m else None
def close_key(c):
    m = re.match(r'(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+) ([AP])M', c or '')
    if not m: return 0
    d, mo, y, h, mi, s, ap = m.groups(); h = int(h) % 12 + (12 if ap == 'P' else 0)
    return int(y) * 1e10 + int(mo) * 1e8 + int(d) * 1e6 + h * 1e4 + int(mi) * 100 + int(s)
def fmt_close(c):
    m = re.match(r'(\d+)/(\d+)/(\d+) (\d+):(\d+):\d+ ([AP]M)', c or '')
    if not m: return c or ''
    d, mo, y, h, mi, ap = m.groups()
    try: day = datetime.date(int(y), int(mo), int(d)).strftime('%a %d %b')
    except ValueError: day = f'{d}/{mo}'
    return f'{day} {int(h)}:{mi} {ap}'
def thumb(cd):
    p = f'{W}/thumbs/{cd}.jpg'; src = f'{W}/photos/{cd}_1.jpg'
    os.makedirs(f'{W}/thumbs', exist_ok=True)
    if not os.path.exists(p) and os.path.exists(src):
        im = Image.open(src).convert('RGB'); im.thumbnail((240, 240)); im.save(p, quality=60)
    return f'<img class="th" alt="" src="data:image/jpeg;base64,{base64.b64encode(open(p,"rb").read()).decode()}">' if os.path.exists(p) else '<div class="th none">no photo</div>'

CAT, RES, D = {}, {}, {}
for chid, k in PAIRS:
    cat = load(f'{W}/armitage{chid}_cat.json', {})
    CAT[k] = dict(name=cat.get('name', f'catalogue {chid}'), chid=chid, closes=f'{fmt_close(cat.get("close_first"))} to {fmt_close(cat.get("close_last"))}', lots=f'{cat.get("lots", "?")} lots', lot_min=cat.get('lot_min'), lot_max=cat.get('lot_max'))
    RES[k] = load(f'{W}/armitage{chid}_result.json', {'lots': [], 'not_researched': [], 'interest': []})
    recs = {}
    for f in sorted(glob.glob(f'{R}/scans/{k}_*.json')):
        for x in json.load(open(f)):
            if x['state'] == 'SCANNED' or x['cdid'] not in recs: recs[x['cdid']] = x
    D[k] = dict(recs=recs, refresh=load(f'{W}/refresh_{k}.json', {}), interest=RES[k].get('interest', []), nr={x['cdid']: x for x in RES[k].get('not_researched', [])})
mk = {p['cdid']: p for k in RES for p in RES[k]['lots']}

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
    bid = rf.get('current_bid'); chk = rf.get('checked') or rec.get('checked'); bc = rf.get('bid_count', 0); est = rf.get('estimate')
    bm = money(bid)
    bidtxt = (f'{E(bid)} ({bc} bids, all-in ${bm*PREM:,.2f})' if bm else 'No bids yet') + f' <span class="mut">at {E(chk or "")}</span>'
    t = p['triage']; kk, f = p.get('keep_max_hammer') or 0, p.get('flip_max_hammer') or 0
    if t == 'KEEP': mx = f'KEEP max hammer ${kk:,.0f} (all-in ${kk*PREM:,.2f})'
    elif t == 'FLIP': mx = f'FLIP max hammer ${f:,.0f} (all-in ${f*PREM:,.2f})'
    elif t == 'BOTH': mx = f'KEEP max ${kk:,.0f}, FLIP max ${f:,.0f} (hammer)'
    else: mx = 'No maximum bid (no sold support)'
    over = ''
    lim = kk or f
    if bm and lim and bm > lim: over = '<span class="pill warn">bidding already above the max</span>'
    cls = {'KEEP': 'keep', 'FLIP': 'flip', 'BOTH': 'keep'}.get(t, 'near')
    lo, hi = p.get('guide_low_aud'), p.get('guide_high_aud')
    guide = f'${lo:,.0f} to ${hi:,.0f}' if (lo or hi) else 'none'
    q = f'<p class="q"><b>Ask Armitage:</b> {E(p["question_for_armitage"])}</p>' if p.get('question_for_armitage') else ''
    return f'''<article id="c{p['cdid']}" class="lot {cls}" data-close="{close_key(rec.get('close'))}">
<div class="lh">{thumb(p['cdid'])}<div class="lt"><h4><a href="{E(rec.get('url','#'))}" target="_blank" rel="noopener">Lot {E(str(rec.get('lot_label') or p['lot']))}</a> <span class="mut">closes {E(fmt_close(rec.get('close')))}</span></h4>
<p class="what">{E(p['what_it_is'][:300])}</p><p><span class="pill {p['confidence'].lower()}">{E(p['confidence'])} confidence</span> <span class="pill low">score {p.get('market_score')}/10</span> {over}</p></div></div>
<dl class="kv"><dt>Photo findings</dt><dd>{E((p.get('key_photo_findings') or '')[:400])}</dd><dt>Condition</dt><dd>{E((p.get('condition') or '')[:250])}</dd>
<dt>Current bid</dt><dd>{bidtxt}</dd><dt>Armitage estimate</dt><dd>{E(est or "none shown")} <span class="mut">(not used in scoring)</span></dd><dt>Suggested max</dt><dd><b>{E(mx)}</b> <span class="mut">(all-in = hammer x 1.22)</span></dd>
<dt>Market guide</dt><dd>{guide} <span class="mut">{E(p.get('guide_summary') or '')}</span></dd></dl>
<div class="evs">{ev_list(p.get('sold', []), 'sold', 'Sold (price paid)', 'Only these set a maximum bid.')}{ev_list(p.get('unsold', []), 'unsold', 'Unsold (ceiling signal)', 'Did not sell. Not a value.')}{ev_list(p.get('asking', []), 'ask', 'Asking (not a price paid)', 'Optimistic. Never used for a max.')}</div>
<details><summary>Working and confidence</summary><p class="small"><b>Why {E(p['confidence'])}:</b> {E(p.get('confidence_reason') or '')}</p><p class="small"><b>Dropped entries:</b> {E(p.get('dropped_entries') or 'none')}</p><p class="small"><b>Working:</b> {E(p['working'])}</p>{('<p class="small"><b>Flip rule:</b> ' + E(p['flip_rule']) + '</p>') if p.get('flip_rule') else ''}</details>{q}</article>'''

def coverage(k):
    d = D[k]; recs = d['recs']; C = CAT[k]; n = lambda s: sum(1 for x in recs.values() if x['state'] == s)
    unsc = [x for x in recs.values() if x['state'] == 'UNSCANNED']
    un = ''.join(f'<li>cdid {x["cdid"]} (lot {E(str(x.get("lot_label")))}): {E(str(x.get("reason")))}</li>' for x in unsc) or '<li>None.</li>'
    ids = len(open(f'{W}/index_{k}.txt').read().split()) if os.path.exists(f'{W}/index_{k}.txt') else 0
    return f'''<div class="cov"><h3>{E(C["name"])}</h3><p class="mut">Catalogue {C["chid"]}, lots {C["lot_min"]} to {C["lot_max"]}, closing {E(C["closes"])}</p>
<dl class="kv"><dt>Lots in the catalogue (from the group page)</dt><dd>{ids}</dd><dt>Lots scanned, every photo viewed</dt><dd>{n('SCANNED')}</dd><dt>Unscanned</dt><dd>{len(unsc)}</dd></dl><ul class="plain">{un}</ul></div>'''

def table_all(k):
    d = D[k]; rows = []
    for cd, x in sorted(d['recs'].items(), key=lambda kv: (kv[1].get('lot') or 0, str(kv[1].get('lot_label') or ''))):
        if x['state'] != 'SCANNED': continue
        p = mk.get(cd); rf = d['refresh'].get(str(cd), {})
        tri = p['triage'] if p else ('SKIP' if x.get('verdict') != 'CANDIDATE' else 'CANDIDATE, not researched')
        sc = p['market_score'] if p else (d['nr'].get(cd, {}).get('strength') if cd in d['nr'] else x.get('strength'))
        finding = (p.get('key_photo_findings') if p else x.get('findings')) or ''
        why = (p.get('score_reason') if p else (d['nr'].get(cd, {}).get('rescore_note') or x.get('reason'))) or ''
        rows.append(f'<tr><td><a href="{E(x["url"])}" target="_blank" rel="noopener">{E(str(x.get("lot_label") or x["lot"]))}</a></td><td>{E((x.get("title") or "")[:80])}</td><td>{x.get("photo_count")}</td><td>{E(str(tri))}</td><td>{sc if sc is not None else ""}</td><td>{E(finding[:170])}</td><td>{E(why[:150])}</td><td>{E(rf.get("current_bid") or "")} ({rf.get("bid_count", 0)})</td><td>{E(fmt_close(x.get("close")))}</td></tr>')
    return f'<details><summary>Every lot in this catalogue ({len(rows)}), with photos viewed and a finding</summary><div class="tw"><table><thead><tr><th>Lot</th><th>Title</th><th>Photos</th><th>Result</th><th>Score</th><th>What the photos show</th><th>Why</th><th>Bid (count)</th><th>Closes</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></details>'

def ranked():
    rows = []
    for k in CAT:
        d = D[k]
        for p in RES[k]['lots']:
            rec = d['recs'].get(p['cdid'])
            km = p.get('keep_max_hammer') or 0
            if not rec or p['triage'] not in ('KEEP', 'FLIP', 'BOTH') or km <= 0: continue
            rf = d['refresh'].get(str(p['cdid']), {})
            try: bid = int(str(rf.get('current_bid') or '0').replace('$', '').replace(',', '').split('.')[0] or 0)
            except ValueError: bid = 0
            rows.append(((bid > km), -(p.get('market_score') or 0), {'High': 0, 'Medium': 1, 'Low': 2}.get(p.get('confidence'), 3), -(km - bid), k, p, rec, bid, km))
    rows.sort(key=lambda r: r[:4])
    tr = ''.join(f'<tr><td>{i}</td><td><a href="#c{p["cdid"]}">{E(str(rec.get("lot_label") or p["lot"]))}</a></td><td>{E((rec.get("title") or "")[:60])}</td><td>{E(p["triage"])}</td><td>{p.get("market_score")}</td><td>{E(p.get("confidence") or "")}</td><td>${km:,}</td><td>{("$" + format(p.get("flip_max_hammer") or 0, ",")) if p.get("flip_max_hammer") else ""}</td><td>{("$" + format(bid, ",")) if bid else "none"}{" <b>OVER</b>" if over else ""}</td><td>{E(fmt_close(rec.get("close")))}</td></tr>' for i, (over, _, _, _, k, p, rec, bid, km) in enumerate(rows, 1))
    return f'<section id="ranked"><h2>All picks, most to least attractive</h2><p class="small">Every lot with a maximum bid, across all five catalogues. Ranked by score, then confidence, then room between the current bid and the keep maximum. Lots already bid past the keep maximum sit at the bottom. Maximums are hammer prices. The catalogue sections below stay in lot order to match closing times.</p><div class="tw"><table><thead><tr><th>#</th><th>Lot</th><th>Title</th><th>Type</th><th>Score</th><th>Confidence</th><th>Keep max</th><th>Flip max</th><th>Bid now</th><th>Closes</th></tr></thead><tbody>{tr}</tbody></table></div></section>'

def section(k):
    d = D[k]; C = CAT[k]; res = RES[k]
    L = [p for p in res['lots'] if d['recs'].get(p['cdid'])]
    srt = lambda ks: sorted([p for p in L if p['triage'] in ks], key=lambda p: (p['lot'], p['cdid']))
    out = [f'<section id="{k}"><h2>{E(C["name"])} ({C["lots"]}, closing {E(C["closes"])})</h2>']
    for ks, title, empty in ((('FLIP',), 'FLIP picks (buy to resell)', 'None. No lot had sold support for a resale ceiling.'), (('KEEP',), 'KEEP picks (buy to own)', 'None.'), (('BOTH',), 'BOTH picks (keep or resell)', 'None.')):
        items = srt(ks); out.append(f'<h3>{title}</h3>' + (''.join(card(p, k) for p in items) if items else f'<p class="mut">{empty}</p>'))
    lv = srt(('LOOK AT VIEWING',))
    out.append('<h3>Look at the viewing</h3><p class="small">A credible identification with real-looking value, but no sold support, so no maximum bid. Viewing at 9 Goodman Crt, Invermay (phone (03) 6326 2555).</p>' + (''.join(card(p, k) for p in lv) or '<p class="mut">None.</p>'))
    out.append('<h3>Near misses</h3>' + (''.join(card(p, k) for p in srt(('NEAR MISS',))) or '<p class="mut">None.</p>'))
    it = d['interest']
    if it:
        rows = ''.join(f'<tr><td><a href="{E(d["recs"].get(x["cdid"],{}).get("url","#"))}" target="_blank" rel="noopener">{E(str(d["recs"].get(x["cdid"],{}).get("lot_label") or x["lot"]))}</a></td><td>{E(d["recs"].get(x["cdid"],{}).get("title") or "")[:60]}</td><td>{E(x["kind"])}</td><td>{E(x["note"])}</td></tr>' for x in sorted(it, key=lambda x: x['lot']))
        out.append(f'<h3>For interest: wine, whisky and watches</h3><div class="tw"><table><thead><tr><th>Lot</th><th>Title</th><th>Kind</th><th>Notes</th></tr></thead><tbody>{rows}</tbody></table></div>')
    out.append(table_all(k)); out.append('</section>'); return ''.join(out)

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=11))).strftime('%d/%m/%Y %H:%M AEDT')
refreshed = sorted({v.get('checked') for k in D for v in D[k]['refresh'].values() if v.get('checked')})
ref_txt = f'{refreshed[0]} to {refreshed[-1]}' if refreshed else 'not yet'
meta = load(f'{W}/armitage_{SLUG}_meta.json', {})
title = meta.get('title', 'Armitage online auction')
CSS = open(f'{W}/page.css').read()
all_first = sorted((CAT[k]['closes'] for k in CAT))
page = f'''<title>{E(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Public+Sans:wght@400;500;700&display=swap">
<style>{CSS}</style>
<main class="wrap">
<header><p class="eyebrow">Armitage Auctions, Invermay (Launceston). {E(meta.get('when', 'Online auction'))}</p><h1>{E(title)}</h1>
<p class="lead">{E(meta.get('bottom_line',''))}</p></header>
<section class="status"><h2>Run details</h2>
<dl class="kv"><dt>Closing</dt><dd><b>{E(meta.get('deadline', 'Each lot closes at its own time; the time is on every card and lot page.'))}</b></dd>
<dt>Viewing</dt><dd>{E(meta.get('viewing', 'On the closing day from 8:30 AM at 9 Goodman Crt, Invermay. Phone (03) 6326 2555.'))}</dd>{('<dt>Viewing checklist</dt><dd><ul class="plain">' + ''.join('<li>'+E(x)+'</li>' for x in meta.get('viewing_notes', [])) + '</ul></dd>') if meta.get('viewing_notes') else ''}
<dt>Buyer's premium</dt><dd>22% including GST on the hammer price (shown on every lot page). All-in = hammer x 1.22.</dd>
<dt>Mode</dt><dd>Lot data and photos came from Armitage's public lot pages. Read-only: no bids, logins or forms. The estimate and the current bid were hidden from the scoring agents and are shown here for information only. Bids last refreshed {E(ref_txt)}.</dd>
<dt>Collection</dt><dd>Pickup only from 9 Goodman Crt, Invermay. Inbound freight assumed $0 (local).</dd>
<dt>Page built</dt><dd>{now}.</dd>
<dt>Blocked or login sources</dt><dd>eBay, Wine-Searcher and Australian Whisky Auctions are closed to this session (403 from the sites). No logins were tried.</dd>
<dt>Resume point</dt><dd>Workflow runs {E(meta.get('run',''))}. Batch files are in scans/ (one per batch).</dd></dl>
<div class="covs">{''.join(coverage(k) for k in CAT)}</div>
<details open><summary>Assumptions</summary><ul class="plain">{''.join('<li>'+E(x)+'</li>' for x in meta.get('assumptions',[]))}</ul></details></section>
{ranked()}
{''.join(section(k) for k in CAT)}
<footer class="small">Only sold prices with a URL and a date set maximum bids. "No comps" means no maximum bid. Built by Claude Code.</footer>
</main>'''
open(f'{W}/armitage_{SLUG}.html', 'w').write(page); print('built', len(page) // 1024, 'KB')
