#!/usr/bin/env python3
# Build the Webb's whisky label hunt page from webbs<aid>_result.json and webbs<aid>_meta.json.
# Usage: python3 -I build_webbs.py <aid>
import sys, json, html

AID = sys.argv[1]
W = '/home/user/Armitage/work'
R = json.load(open(f'{W}/webbs{AID}_result.json'))
M = json.load(open(f'{W}/webbs{AID}_meta.json'))
LOTS = {c['lot_id']: c for c in json.load(open(f'{W}/webbs{AID}/all_lots.json'))}
E = lambda x: html.escape(str(x if x is not None else ''))


def url(lid):
    c = LOTS.get(lid, {})
    return f'https://auctions.webbs.co.nz/lot-details/index/catalog/{AID}/lot/{lid}/{c.get("slug", "")}'


ORDER = {'CONFIRMED HIDDEN VALUE': 0, 'PARTLY CONFIRMED': 1, 'TITLE OVERSTATES': 2, 'NOT CONFIRMED': 3}
ver = sorted(R.get('verified', []), key=lambda v: (ORDER.get(v.get('verdict'), 9), -(v.get('keep_max_hammer_nzd') or 0)))
scan = {s['lot_id']: s for s in R.get('scan', [])}


def ev_list(name, items):
    if not items:
        return ''
    out = [f'<div class="ev"><b>{name}</b><ul>']
    for e in items:
        p = e.get('nzd_price')
        pr = f' (NZ${p:,.0f})' if isinstance(p, (int, float)) and p else ''
        out.append(f'<li>{E(e.get("price"))}{pr}, {E(e.get("venue"))}, {E(e.get("date"))}. <a href="{E(e.get("url"))}" target="_blank" rel="noopener">source</a>{(" " + E(e.get("note"))) if e.get("note") else ""}</li>')
    out.append('</ul></div>')
    return ''.join(out)


def card(v):
    lid = v['lot_id']
    s = scan.get(lid, {})
    km, fm = v.get('keep_max_hammer_nzd') or 0, v.get('flip_max_hammer_nzd') or 0
    bids = f'<div class="bids"><span>Keep max <b>{"NZ$" + format(km, ",") if km else "no max"}</b></span><span>Flip max <b>{"NZ$" + format(fm, ",") if fm else "no max"}</b></span><span class="conf">{E(v.get("confidence"))} confidence</span></div>'
    vcls = {0: 'good', 1: 'part', 2: 'over', 3: 'no'}.get(ORDER.get(v.get('verdict'), 3))
    return f'''<article class="card">
<div class="top"><a class="lot" href="{url(lid)}" target="_blank" rel="noopener">Lot {E(v.get("lot_label"))}</a><span class="verdict {vcls}">{E(v.get("verdict"))}</span></div>
<h3>{E(LOTS.get(lid, {}).get("title") or v.get("title"))}</h3>
{bids}
<p><b>What it really is:</b> {E(v.get("what_it_really_is"))}</p>
<p><b>What the title misses:</b> {E(v.get("what_the_title_misses"))}</p>
<p><b>Photo evidence:</b> {E(v.get("photo_evidence"))}</p>
<p><b>Market:</b> {E(v.get("guide_summary"))}</p>
{ev_list("Sold", v.get("sold"))}{ev_list("Unsold or passed in", v.get("unsold"))}{ev_list("Asking (not sold)", v.get("asking"))}
<details><summary>Working, condition and questions</summary>
<p><b>Working:</b> {E(v.get("working"))}</p>
<p><b>Condition:</b> {E(v.get("condition"))}</p>
<p><b>Confidence:</b> {E(v.get("confidence_reason"))}</p>
<p><b>Ask Webb's:</b> {E(v.get("question_for_webbs") or "nothing extra")}</p>
<p><b>Comps dropped by the checker:</b> {E(v.get("dropped_entries") or "none")}</p>
<p><b>Scan notes:</b> {E(s.get("text_read"))}</p>
</details>
</article>'''


rows = []
for s in sorted(R.get('scan', []), key=lambda s: (-(s.get('hidden_value_score') or 0), str(s.get('lot_label')))):
    lid = s['lot_id']
    rows.append(f'<tr data-s="{s.get("hidden_value_score", 0)}"><td><a href="{url(lid)}" target="_blank" rel="noopener">{E(s.get("lot_label"))}</a></td><td class="sc">{E(s.get("hidden_value_score"))}</td><td>{E(LOTS.get(lid, {}).get("title") or s.get("title"))}<div class="sub">{E(s.get("not_in_title"))}{(" | Title error: " + E(s.get("title_errors"))) if s.get("title_errors") and s.get("title_errors").lower() not in ("none", "none.") else ""}</div></td></tr>')

assump = ''.join(f'<li>{E(a)}</li>' for a in M.get('assumptions', []))
page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Webb's Whisky Hunt</title>
<style>
:root{{--bg:#f7f5f0;--card:#fff;--ink:#1d1b18;--mute:#6b665d;--line:#e3ded3;--acc:#8a4b12;--good:#1f7a3a;--part:#a46a00;--no:#8a8478;--over:#a33a2a}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#16140f;--card:#211e18;--ink:#eee8dc;--mute:#a59e90;--line:#373229;--acc:#e0a060;--good:#5cc47a;--part:#e0b040;--no:#9a9488;--over:#e07a6a}}}}
:root[data-theme="dark"]{{--bg:#16140f;--card:#211e18;--ink:#eee8dc;--mute:#a59e90;--line:#373229;--acc:#e0a060;--good:#5cc47a;--part:#e0b040;--no:#9a9488;--over:#e07a6a}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:880px;margin:0 auto;padding:16px}}h1{{font-size:1.5rem;margin:.2em 0}}h2{{font-size:1.15rem;margin:1.6em 0 .6em}}h3{{font-size:1rem;margin:.4em 0}}
a{{color:var(--acc)}}.meta{{color:var(--mute);font-size:.9rem}}.bl{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:12px 0}}.card p{{margin:.4em 0}}
.top{{display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap}}.lot{{font-weight:700;text-decoration:none}}
.verdict{{font-size:.75rem;font-weight:700;padding:2px 8px;border-radius:99px;border:1px solid currentColor}}.good{{color:var(--good)}}.part{{color:var(--part)}}.no{{color:var(--no)}}.over{{color:var(--over)}}
.bids{{display:flex;flex-wrap:wrap;gap:6px 14px;margin:.4em 0;font-size:.95rem}}.conf{{color:var(--mute)}}
.ev ul{{margin:.2em 0 .4em 1.1em;padding:0}}.ev li{{margin:.15em 0;font-size:.9rem}}details{{margin-top:.4em}}summary{{cursor:pointer;color:var(--acc)}}
.tw{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:.88rem}}td,th{{border-bottom:1px solid var(--line);padding:6px 4px;vertical-align:top;text-align:left}}.sc{{text-align:center;font-weight:700}}.sub{{color:var(--mute);font-size:.82rem}}
.flt{{margin:.4em 0}}.flt button{{background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:4px 10px;margin-right:4px}}
</style></head><body><main>
<h1>Webb's Whisky Hunt</h1>
<div class="meta">{E(M.get("sale"))}</div>
<div class="bl"><p>{E(M.get("bottom_line"))}</p></div>
<h2>Finds checked by Opus ({len(ver)})</h2>
{''.join(card(v) for v in ver) or '<p>No lots reached the check stage.</p>'}
<h2>Every whisky lot scanned ({len(rows)})</h2>
<p class="meta">Score 0 to 10 = how likely the photos show value the title misses. 0 means the title already says everything the label does.</p>
<div class="flt"><button onclick="f(3)">Score 3+</button><button onclick="f(1)">Score 1+</button><button onclick="f(0)">All</button></div>
<div class="tw"><table><thead><tr><th>Lot</th><th>Score</th><th>Title and what the photos add</th></tr></thead><tbody id="tb">{''.join(rows)}</tbody></table></div>
<h2>How this was done</h2><ul>{assump}</ul>
</main><script>function f(n){{document.querySelectorAll('#tb tr').forEach(function(r){{r.style.display=(+r.dataset.s>=n)?'':'none'}})}}f(1)</script></body></html>'''
open(f'{W}/webbs{AID}.html', 'w').write(page)
print('built', len(page) // 1024, 'KB', len(ver), 'verified', len(rows), 'rows')
