#!/usr/bin/env python3
"""Builds work/tracker.html from work/result_<a>.json, refresh_<a>.json, interest_<a>.json and scans/<a>_*.json."""
import json, glob, os, base64, html, re, datetime
W = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(W)
E = html.escape
def load(p, default=None):
    return json.load(open(p)) if os.path.exists(p) else default
def money(s):
    m = re.search(r'[\d,]+(?:\.\d+)?', s or ''); return float(m.group(0).replace(',', '')) if m else None
def close_key(c):
    m = re.match(r'(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+) ([AP])M', c or '')
    if not m: return 0
    d, mo, y, h, mi, s, ap = m.groups(); h = int(h) % 12 + (12 if ap == 'P' else 0)
    return int(y) * 1e10 + int(mo) * 1e8 + int(d) * 1e6 + h * 1e4 + int(mi) * 100 + int(s)
def short_close(c): return (c or '').replace('30/09/2026 ', '').replace(' AEST', '')
def thumb(cd):
    p = f'{W}/thumbs/{cd}.jpg'
    return f'<img class="th" alt="" src="data:image/jpeg;base64,{base64.b64encode(open(p,"rb").read()).decode()}">' if os.path.exists(p) else '<div class="th none">no photo</div>'

AUC = {'1': dict(name='Auction 1', label='Online Auction 30th September Lots 1-496', lots='1 to 496', first=3069703, last=3070215, start='12:45 PM', chid=28711),
       '2': dict(name='Auction 2', label='Lots 601-961', lots='601 to 961', first=3067062, last=3067440, start='3:32 PM', chid=28712),
       '3': dict(name='Auction 3', label='Online Auction 30th September lots 970-1353', lots='970 to 1353', first=3068394, last=3068770, start='5:33 PM', chid=28713)}
data = {}
for a in AUC:
    res = load(f'{W}/result_{a}.json')
    recs = {}
    for f in sorted(glob.glob(f'{R}/scans/{a}_*.json')):
        for x in json.load(open(f)):
            if x['state'] == 'SCANNED' or x['cdid'] not in recs: recs[x['cdid']] = x
    data[a] = dict(bx=[e for e in (load(f'{W}/browser_comps_2.json',{}).get('entries',[])) if e['auction']==a], bnotes={k.split(':')[1]:v for k,v in (load(f'{W}/browser_comps_2.json',{}).get('notes',{})).items() if k.split(':')[0]==a}, market=load(f'{W}/market_{a}.json'), res=res, recs=recs, refresh=load(f'{W}/refresh_{a}.json', {}), interest=load(f'{W}/interest_{a}.json', []), notes=load(f'{W}/notes_{a}.json', {}))

def coverage(a):
    d = data[a]; recs = d['recs']; A = AUC[a]
    if not recs: return f'<div class="cov"><h3>{A["name"]}</h3><p class="mut">Not started yet. Starts after auction 1 is published.</p></div>'
    n = lambda s: sum(1 for x in recs.values() if x['state'] == s)
    unsc = [x for x in recs.values() if x['state'] == 'UNSCANNED' and 'http 302' not in str(x.get('reason'))]; nis = n('NOT_IN_SALE') + sum(1 for x in recs.values() if x['state'] == 'UNSCANNED' and 'http 302' in str(x.get('reason')))
    found = n('SCANNED') + len(unsc)
    un = ''.join(f'<li>cdid {x["cdid"]}: {E(str(x.get("reason")))}</li>' for x in unsc) or '<li>None.</li>'
    extra = d['notes'].get('coverage_note', '')
    return f'''<div class="cov"><h3>{A["name"]}</h3>
<p class="mut">{E(A["label"])}, closing from {A["start"]} Hobart time</p>
<dl class="kv"><dt>cdids checked</dt><dd>{len(recs)} ({A["first"]} to {A["last"]})</dd>
<dt>Lots found in this sale</dt><dd>{n('SCANNED')}</dd>
<dt>Lots with every photo viewed</dt><dd>{n('SCANNED')}</dd>
<dt>cdids past the end of the sale</dt><dd>{nis}</dd>
<dt>Lots unscanned</dt><dd>{len(unsc)}</dd></dl>
<ul class="plain">{un}</ul><p class="small">{extra}</p></div>'''

def card(p, a, kind):
    d = data[a]; rec = d['recs'].get(p['cdid'], {}); rf = d['refresh'].get(str(p['cdid']), {})
    bid = rf.get('current_bid') or rec.get('current_bid'); chk = rf.get('checked') or rec.get('checked'); bc = rf.get('bid_count', rec.get('bid_count'))
    bm = money(bid); allin = f'${bm*1.22:,.2f}' if bm else '$0 bids so far'
    bidtxt = (f'{E(bid)} ({bc} bids)' if bm else 'No bids yet') + f' <span class="mut">at {E(chk or "")}</span>'
    fmax, kmax = p.get('flip_max_hammer') or 0, p.get('keep_max_hammer') or 0
    if kind == 'KEEP': maxtxt = f'KEEP max hammer ${kmax:,.0f} (all-in ${kmax*1.22:,.2f})'
    elif kind == 'FLIP': maxtxt = f'FLIP max hammer ${fmax:,.0f} (all-in ${fmax*1.22:,.2f})'
    else: maxtxt = 'BOTH: FLIP ${:,.0f}, KEEP ${:,.0f}'.format(fmax, kmax)
    if kind == 'NEAR MISS': maxtxt = 'No maximum bid (no sold comps)'
    over = ''
    if kind in ('KEEP', 'FLIP') and bm and (kmax if kind == 'KEEP' else fmax) < bm: over = '<span class="pill warn">Bid already above the max</span>'
    comps = ''.join(f'<li><a href="{E(c["url"])}" target="_blank" rel="noopener">{E(c["price"])} on {E(c["date"])}, {E(c["venue"])}</a>{" " + E(c["note"]) if c.get("note") else ""}</li>' for c in p.get('comps_kept', [])) or '<li class="mut">No sold comps.</li>'
    ask = f'<p class="small"><b>Asking prices (never used for a max):</b> {E(p["asking_note"])}</p>' if p.get('asking_note') else ''
    q = f'<p class="q"><b>Ask Armitage:</b> {E(p["question_for_armitage"])}</p>' if p.get('question_for_armitage') else ''
    cls = {'KEEP': 'keep', 'FLIP': 'flip', 'BOTH': 'keep', 'NEAR MISS': 'near'}[kind]
    return f'''<article class="lot {cls}" data-close="{close_key(rec.get('close'))}">
<div class="lh">{thumb(p['cdid'])}<div class="lt"><h4><a href="{E(rec.get('url','#'))}" target="_blank" rel="noopener">Lot {p['lot']}</a> <span class="mut">closes {E(short_close(rec.get('close')))}</span></h4>
<p class="what">{E(p['what_it_is'])}</p><p><span class="pill {p['confidence'].lower()}">{E(p['confidence'])} confidence</span> {over}</p></div></div>
<dl class="kv"><dt>Photo findings</dt><dd>{E(p.get('key_photo_findings') or '')}</dd><dt>Condition</dt><dd>{E(p.get('condition') or '')}</dd>
<dt>Estimate</dt><dd>{E(rec.get('estimate') or '')} <span class="mut">(shown for reference, not used in scoring)</span></dd>
<dt>Current bid</dt><dd>{bidtxt}</dd><dt>All-in at that bid</dt><dd>{allin}</dd><dt>Suggested max</dt><dd><b>{E(maxtxt)}</b></dd></dl>
<details><summary>Comps, working and confidence</summary><ul class="comps">{comps}</ul>{ask}
<p class="small"><b>Why {E(p['confidence'])}:</b> {E(p.get('confidence_reason') or '')}</p><p class="small"><b>Comps dropped:</b> {E(p.get('comps_dropped') or 'none')}</p><p class="small"><b>Working:</b> {E(p['working'])}</p></details>{q}</article>'''

def section(a):
    d = data[a]; res = d['res']; A = AUC[a]
    if not res: return ''
    picks = res['picks']; by = lambda k: sorted([p for p in picks if p['listing'] == k], key=lambda p: close_key(d['recs'].get(p['cdid'], {}).get('close')))
    out = [f'<section id="a{a}"><h2>{A["name"]}: {E(A["label"])}</h2>']
    hl = d['notes'].get('headline', '')
    if hl: out.append(f'<p class="lead">{hl}</p>')
    for k, title, empty in (('FLIP', 'FLIP picks (buy to resell)', 'None. No lot had enough verified sold comps to support a resale ceiling.'), ('KEEP', 'KEEP picks (buy to own)', 'None.'), ('BOTH', 'BOTH picks', None)):
        items = by(k)
        if k == 'BOTH' and not items: continue
        out.append(f'<h3>{title}</h3>' + (''.join(card(p, a, k) for p in items) if items else f'<p class="mut">{empty}</p>'))
    nm = by('NEAR MISS')
    out.append('<h3>Near misses</h3><p class="small">Identified from the photos but no verified sold comps, so there is no maximum bid. Check these at viewing (Wed from 8:30 AM) or ring (03) 6326 2555.</p>' + ''.join(card(p, a, 'NEAR MISS') for p in nm))
    nr = res.get('not_researched', [])
    if nr:
        rows = ''.join(f'<tr><td><a href="{E(d["recs"].get(x["cdid"],{}).get("url","#"))}" target="_blank" rel="noopener">{x["lot"]}</a></td><td>{E(x["title"])}</td><td>{x.get("strength")}</td><td>{E(x.get("rescore_note") or x["reason"])}</td></tr>' for x in nr)
        out.append(f'<h3>Not researched</h3><p class="small">Candidates outside the top 30 by estimate-blind score. Score is 1 to 10 on what the item is and its likely market value.</p><div class="tw"><table><thead><tr><th>Lot</th><th>Title</th><th>Score</th><th>Reason</th></tr></thead><tbody>{rows}</tbody></table></div>')
    dr = by('DROP')
    if dr:
        rows = ''.join(f'<tr><td><a href="{E(d["recs"].get(x["cdid"],{}).get("url","#"))}" target="_blank" rel="noopener">{x["lot"]}</a></td><td>{E(x["what_it_is"][:110])}</td><td>{E(x.get("drop_reason") or "")}</td></tr>' for x in dr)
        out.append(f'<details><summary>Researched and dropped ({len(dr)})</summary><div class="tw"><table><thead><tr><th>Lot</th><th>What</th><th>Why dropped</th></tr></thead><tbody>{rows}</tbody></table></div></details>')
    it = d['interest']
    if it:
        rows = ''.join(f'<tr><td><a href="{E(x["url"])}" target="_blank" rel="noopener">{x["lot"]}</a></td><td>{E(x["title"])}</td><td>{E(x["interest"]["kind"])}</td><td>{E(x["interest"]["note"])}</td><td>{E(x.get("current_bid") or "")}</td></tr>' for x in sorted(it, key=lambda x: close_key(x['close'])))
        out.append(f'<h3>For interest: whisky, spirits and watches</h3><p class="small">Not assessed for value. Bids are as at the scan time, not refreshed.</p><div class="tw"><table><thead><tr><th>Lot</th><th>Title</th><th>Kind</th><th>Notes</th><th>Bid</th></tr></thead><tbody>{rows}</tbody></table></div>')
    out.append('</section>'); return ''.join(out)


def age_flag(date):
    m = re.search(r'(20\d\d)', date or '')
    if not m: return ''
    y = int(m.group(1))
    return ' <span class="pill warn">over 24 months old</span>' if y <= 2023 else (' <span class="pill low">about 2 years old</span>' if y == 2024 else '')
def ev_list(items, kind, label, hint):
    if not items: return f'<div class="ev {kind}"><h5>{label}</h5><p class="mut small">None found.</p></div>'
    li = ''.join(f'<li><a href="{E(x.get("url") or "#")}" target="_blank" rel="noopener">{E(str(x.get("price","")))}</a> <span class="mut">{E(str(x.get("date","")))}, {E(str(x.get("venue","")))}</span>{age_flag(x.get("date")) if kind != "ask" else ""}<br><span class="small">{E((x.get("note") or "")[:260])}</span></li>' for x in items)
    return f'<div class="ev {kind}"><h5>{label}</h5><p class="small mut">{hint}</p><ul>{li}</ul></div>'

def browser_block(a, lot):
    d = data[a]; ents = [e for e in d['bx'] if e['lot'] == lot]; note = d['bnotes'].get(str(lot))
    if not ents and not note: return ''
    def L(kind, label, hint):
        xs = [e for e in ents if e['kind'] == kind]
        if not xs: return ''
        li = ''.join(f'<li><a href="{E(e["url"] or "#")}" target="_blank" rel="noopener">{E(e["price"])}</a> <span class="mut">{E(e["date"])}, {E(e["venue"])}</span><br><span class="small">{E(e["note"])} <i>({E(e["provenance"])})</i></span></li>' for e in xs)
        return f'<div class="ev {"sold" if kind=="SOLD" else ("unsold" if kind=="UNSOLD" else "ask")}"><h5>{label}</h5><p class="small mut">{hint}</p><ul>{li}</ul></div>'
    body = L('SOLD','Sold (from your browser)','Page not opened by Claude. Check provenance.') + L('UNSOLD','Unsold (from your browser)','Ceiling signal only.') + L('ASKING','Asking (from your browser)','Not a price paid.')
    nb = f'<p class="small">{E(note)}</p>' if note else ''
    return f'<details class="bx"><summary>Added from your browser comps</summary>{nb}<div class="evs">{body}</div></details>'

def card2(p, a):
    d = data[a]; rec = d['recs'].get(p['cdid'], {}); rf = d['refresh'].get(str(p['cdid']), {})
    bid = rf.get('current_bid') or rec.get('current_bid'); chk = rf.get('checked') or rec.get('checked'); bc = rf.get('bid_count', rec.get('bid_count'))
    bm = money(bid); allin = f'${bm*1.22:,.2f}' if bm else 'no bids yet'
    bidtxt = (f'{E(bid)} ({bc} bids)' if bm else 'No bids yet') + f' <span class="mut">at {E(chk or "")}</span>'
    t = p['triage']; k, f = p.get('keep_max_hammer') or 0, p.get('flip_max_hammer') or 0
    if t == 'KEEP': mx = f'KEEP max hammer ${k:,.0f} (all-in ${k*1.22:,.2f})'
    elif t == 'FLIP': mx = f'FLIP max hammer ${f:,.0f} (all-in ${f*1.22:,.2f})'
    elif t == 'BOTH': mx = f'KEEP max ${k:,.0f}, FLIP max ${f:,.0f} (hammer)'
    else: mx = 'No maximum bid (no sold support)'
    over = ''
    top = max(k, f) if t in ('KEEP', 'FLIP', 'BOTH') else 0
    if top and bm and (k if t == 'KEEP' else (f if t == 'FLIP' else max(k, f))) < bm: over = '<span class="pill warn">bid already above the max</span>'
    cls = {'KEEP': 'keep', 'FLIP': 'flip', 'BOTH': 'keep'}.get(t, 'near')
    lo, hi = p.get('guide_low_aud'), p.get('guide_high_aud')
    guide = f'${lo:,.0f} to ${hi:,.0f}' if (lo or hi) else 'none'
    q = f'<p class="q"><b>Ask Armitage:</b> {E(p["question_for_armitage"])}</p>' if p.get('question_for_armitage') else ''
    return f'''<article class="lot {cls}" data-close="{close_key(rec.get('close'))}">
<div class="lh">{thumb(p['cdid'])}<div class="lt"><h4><a href="{E(rec.get('url','#'))}" target="_blank" rel="noopener">Lot {p['lot']}</a> <span class="mut">closes {E(short_close(rec.get('close')))}</span></h4>
<p class="what">{E(p['what_it_is'][:300])}</p><p><span class="pill {p['confidence'].lower()}">{E(p['confidence'])} confidence</span> <span class="pill low">score {p.get('market_score')}/10</span> {over}</p></div></div>
<dl class="kv"><dt>Photo findings</dt><dd>{E((p.get('key_photo_findings') or '')[:400])}</dd><dt>Condition</dt><dd>{E((p.get('condition') or '')[:250])}</dd>
<dt>Current bid</dt><dd>{bidtxt}</dd><dt>All-in at that bid</dt><dd>{allin}</dd><dt>Suggested max</dt><dd><b>{E(mx)}</b></dd>
<dt>Market guide</dt><dd>{guide} <span class="mut">{E(p.get('guide_summary') or '')}</span></dd><dt>Estimate</dt><dd>{E(rec.get('estimate') or '')} <span class="mut">(reference only, not used)</span></dd></dl>
<div class="evs">{ev_list(p.get('sold', []), 'sold', 'Sold (price paid)', 'Only these set a maximum bid.')}{ev_list(p.get('unsold', []), 'unsold', 'Unsold (ceiling signal)', 'Did not sell. Not a value.')}{ev_list(p.get('asking', []), 'ask', 'Asking (not a price paid)', 'Optimistic. Never used for a max.')}</div>
{browser_block(a, p['lot'])}<details><summary>Working and confidence</summary><p class="small"><b>Why {E(p['confidence'])}:</b> {E(p.get('confidence_reason') or '')}</p><p class="small"><b>Dropped entries:</b> {E(p.get('dropped_entries') or 'none')}</p><p class="small"><b>Working:</b> {E(p['working'])}</p></details>{q}</article>'''

def section2(a):
    d = data[a]; mk = d['market']; A = AUC[a]
    L = mk['lots']; srt = lambda ks: sorted([p for p in L if p['triage'] in ks], key=lambda p: close_key(d['recs'].get(p['cdid'], {}).get('close')))
    out = [f'<section id="a{a}"><h2>{A["name"]}: {E(A["label"])}</h2>']
    if d['notes'].get('headline'): out.append(f'<p class="lead">{d["notes"]["headline"]}</p>')
    for ks, title, empty in ((('FLIP',), 'FLIP picks (buy to resell)', 'None. No lot had sold support for a resale ceiling.'), (('KEEP',), 'KEEP picks (buy to own)', 'None.'), (('BOTH',), 'BOTH picks (keep or resell)', 'None.')):
        items = srt(ks); out.append(f'<h3>{title}</h3>' + (''.join(card2(p, a) for p in items) if items else f'<p class="mut">{empty}</p>'))
    lv = srt(('LOOK AT VIEWING',))
    out.append('<h3>Look at viewing</h3><p class="small">A credible identification with real-looking value, but no sold support, so no maximum bid. Check at the preview (Wed from 8:30 AM) or ring (03) 6326 2555.</p>' + (''.join(card2(p, a) for p in lv) or '<p class="mut">None.</p>'))
    nm = srt(('NEAR MISS',))
    out.append('<h3>Near misses</h3>' + ''.join(card2(p, a) for p in nm))
    done = {p['cdid'] for p in L}
    nr = [x for x in (d['res'] or {}).get('not_researched', []) if x['cdid'] not in done]
    if nr:
        rows = ''.join(f'<tr><td><a href="{E(d["recs"].get(x["cdid"],{}).get("url","#"))}" target="_blank" rel="noopener">{x["lot"]}</a></td><td>{E(x["title"])}</td><td>{x.get("strength")}</td><td>{E(x.get("rescore_note") or x["reason"])}</td></tr>' for x in nr)
        out.append(f'<h3>Not researched</h3><div class="tw"><table><thead><tr><th>Lot</th><th>Title</th><th>Score</th><th>Reason</th></tr></thead><tbody>{rows}</tbody></table></div>')
    dr = srt(('DROP',))
    if dr:
        rows = ''.join(f'<tr><td><a href="{E(d["recs"].get(x["cdid"],{}).get("url","#"))}" target="_blank" rel="noopener">{x["lot"]}</a></td><td>{E(x["what_it_is"][:110])}</td><td>{E(x.get("score_reason") or "")[:140]}</td></tr>' for x in dr)
        out.append(f'<details><summary>Researched and dropped ({len(dr)})</summary><div class="tw"><table><thead><tr><th>Lot</th><th>What</th><th>Why</th></tr></thead><tbody>{rows}</tbody></table></div></details>')
    it = d['interest']
    if it:
        rows = ''.join(f'<tr><td><a href="{E(x["url"])}" target="_blank" rel="noopener">{x["lot"]}</a></td><td>{E(x["title"])}</td><td>{E(x["interest"]["kind"])}</td><td>{E(x["interest"]["note"])}</td><td>{E(x.get("current_bid") or "")}</td></tr>' for x in sorted(it, key=lambda x: close_key(x['close'])))
        out.append(f'<h3>For interest: whisky, spirits and watches</h3><p class="small">Not assessed for value. Bids as at scan time.</p><div class="tw"><table><thead><tr><th>Lot</th><th>Title</th><th>Kind</th><th>Notes</th><th>Bid</th></tr></thead><tbody>{rows}</tbody></table></div>')
    out.append('</section>'); return ''.join(out)

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=10))).strftime('%d/%m/%Y %H:%M AEST')
refreshed = sorted({v['checked'] for a in data for v in data[a]['refresh'].values()})
ref_txt = f'{refreshed[0]} to {refreshed[-1]}' if refreshed else 'not yet'
meta = load(f'{W}/page_meta.json', {})
CSS = open(f'{W}/page.css').read()
page = f'''<title>Armitage Sleeper Tracker</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Public+Sans:wght@400;500;700&display=swap">
<style>{CSS}</style>
<main class="wrap">
<header><p class="eyebrow">Armitage Auctions, Invermay. Closing Wed 30 Sep 2026</p><h1>Sleeper tracker</h1>
<p class="lead">{meta.get('bottom_line','')}</p></header>
<section class="status"><h2>Run details</h2>
<dl class="kv"><dt>Mode</dt><dd>DOWNLOAD MODE. Lot pages and photos were fetched directly with curl (HTTP 200, no proxy block). No browser was used. Read-only: no bids, logins, watches or forms.</dd>
<dt>Buyer's premium</dt><dd>22%, GST inclusive. Armitage support page (armitage.bidsonline.com.au/support.aspx): "All lots offered for auction incur a buyers premium of 22% (GST inclusive)". All-in cost = hammer x 1.22.</dd>
<dt>Collection</dt><dd>Pickup only from 9 Goodman Crt, Invermay. Inbound freight $0 (local). Phone (03) 6326 2555. Viewing Wed from 8:30 AM.</dd>
<dt>Bids refreshed</dt><dd>{ref_txt} (listed lots only). Page built {now}. Bids move fast near the close, so treat these as stale.</dd>
<dt>Blocked or login sources</dt><dd>{meta.get('blocked','none recorded')}</dd>
<dt>Resume point</dt><dd>Workflow run {meta.get('run','')}. Batch files are saved in scans/ in the repo, one per 15 cdids. Unscanned cdid ranges: {meta.get('unscanned','none')}.</dd></dl>
<div class="covs">{coverage('1')}{coverage('2')}{coverage('3')}</div>
<details open><summary>Assumptions</summary><ul class="plain">{''.join('<li>'+x+'</li>' for x in meta.get('assumptions',[]))}</ul></details></section>
{(section2('1') if data['1']['market'] else section('1'))}{(section2('2') if data['2']['market'] else section('2'))}{(section2('3') if data['3']['market'] else section('3'))}
<footer class="small">Only sold prices with a URL and a date are used for maximum bids. "No comps" means no maximum bid. Currency for any foreign comps is stated in each lot's working. Built by Claude Code.</footer>
</main>'''
open(f'{W}/tracker.html', 'w').write(page); print('built', len(page) // 1024, 'KB')
