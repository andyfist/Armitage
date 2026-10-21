"""Australian Book Auctions (Melbourne) results: Australiana, voyages, maps, rare books.

Source: https://australianbookauctions.com/past-sales/ lists every sale (100 onwards; ABA
began numbering at 100) with a catalogue PDF and a "Sales Results" price-list PDF.
The price list gives lot number and hammer for sold lots only, so a catalogue lot that
is missing from it was unsold (hammer_aud 0, unsold true).

This replaces the one-off build behind work/aba_lots.json (same lots, common format,
with sale dates and section names added).

Writes databases/aba/sale_<n>.json and databases/aba_state.json. PDFs are cached in
databases/.cache/aba/ (git-ignored by databases/.gitignore) and can be deleted.
Needs pdftotext (poppler-utils) or the pypdf package.

    python3 -I databases/aba.py             # every sale not yet saved
    python3 -I databases/aba.py --sale 119  # refetch one sale
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, BlockedError, Fetcher, clean, load_json, log, parse_date, save_json, save_records  # noqa: E402

BASE = 'https://australianbookauctions.com'
OUT = os.path.join(HERE, 'aba')
CACHE = os.path.join(HERE, '.cache', 'aba')
STATE = os.path.join(HERE, 'aba_state.json')


def list_sales(f):
    """[{sale, date, name, cat_url, price_url, page_url}] from the past-sales page."""
    page = f.get(BASE + '/past-sales/')
    sales = []
    # each sale card ends with its "View more" button
    for card in re.split(r'View more', page):
        price = re.search(r'href="([^"]+?price-list[^"]*?\.pdf)"', card, re.I)
        if not price:
            continue
        num = re.search(r'(\d{3})-price-list', price.group(1), re.I)
        if not num:
            continue
        cat = re.search(r'href="([^"]+?\.pdf)"[^>]*>(?:\s*<i[^>]*></i>)?\s*Catalogue', card, re.I)
        link = re.findall(r'href="(https://australianbookauctions\.com/auction/[^"]+)"', card)
        text = clean(card[-3000:])
        date = re.findall(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w*\.?\s+\d{1,2}\w{0,2}\s+[A-Za-z]{3,9}\.?\s+\d{4}', text)
        name = re.findall(r'<h2[^>]*>(.*?)</h2>', card, re.S)
        sales.append({
            'sale': int(num.group(1)),
            'date': parse_date(date[-1]) if date else None,
            'name': clean(name[-1]) if name else '',
            'cat_url': cat.group(1) if cat else None,
            'price_url': price.group(1),
            'page_url': link[-1] if link else BASE + '/past-sales/',
        })
    uniq = {}
    for s in sales:
        uniq.setdefault(s['sale'], s)
    return [uniq[k] for k in sorted(uniq)]


def pdf_text(path):
    if shutil.which('pdftotext'):
        return subprocess.run(['pdftotext', path, '-'], capture_output=True, text=True, check=True).stdout
    import pypdf
    return '\n'.join(p.extract_text() or '' for p in pypdf.PdfReader(path).pages)


def fetch_pdf(f, url, name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        data = f.get(url, binary=True)
        if data is None:
            return None
        with open(path, 'wb') as fh:
            fh.write(data)
    return path


def parse_prices(text):
    # 'Price List. Auction Number 119' is not followed by '$', so only lot/price pairs match
    # sub-lots such as 46.1 are kept as their own lot
    return {lot: float(p.replace(',', '')) for lot, p in re.findall(r'(?<![\d$,.])(\d{1,4}(?:\.\d+)?)\s+\$([\d,]+)', text)}


SECTION = re.compile(r'^[ \t]*(?!Lots?\b)([^\n]{3,80}?)\.?[ \t]+Lots?[ \t]+\d+\s*[-–]\s*\d+\s*$', re.M)


def parse_catalogue(text):
    """{lot: (section, description)} from '[n]' markers in the catalogue text."""
    # a lot marker sits alone on its line ('[12]'), or is followed by a SURNAME, ('[12] CURR, Edward');
    # a sub-lot ('[46.1] PLOMLEY...') may be followed by anything.
    # Requiring that keeps bracketed years at the start of a line, such as '[1850]', out.
    parts = re.split(r"^\s*\[(\d{1,4}\.\d+|\d{1,4}(?=\]\s*$|\][ \t]+[A-Z][A-Z'\-]+[,.]))\][ \t]*", text, flags=re.M)
    lots, section = {}, ''
    head = parts[0]
    for i in range(1, len(parts) - 1, 2):
        sec = SECTION.findall(head)
        if sec:
            section = sec[-1].strip()
        body = parts[i + 1]
        head = body  # a section heading sits at the end of the previous lot's text
        body = SECTION.sub('', body)
        body = re.sub(r'Illustrated online( at)? www\.invaluable\.com', '', body)
        body = re.sub(r'\s+', ' ', body).strip()
        n = parts[i]
        if n not in lots:
            lots[n] = (section, body)
    return lots


def title_of(desc):
    m = re.match(r'(.{20,140}?[a-z\])]\.)\s', desc)
    return (m.group(1) if m else desc[:120]).strip()


def build(sale, prices, cat):
    recs = []
    for lot in sorted(set(cat) | set(prices), key=float):
        section, desc = cat.get(lot, ('', ''))
        est = re.search(r'Estimate\s+\$([\d,]+)\s*/\s*\$?([\d,]+)', desc)
        hammer = prices.get(lot)
        r = {
            'source': 'aba',
            'sale': sale['sale'],
            'lot': lot,
            'date': sale['date'],
            'title': title_of(desc) if desc else f'Lot {lot} (not in catalogue text)',
            'description': desc,
            'hammer_aud': hammer or 0.0,
            'premium_included': False,
            'unsold': hammer is None,
            'url': sale['price_url'],
            'category': 'books',
            'section': section,
            'catalogue_url': sale['cat_url'],
        }
        if est:
            r['estimate_aud'] = [float(est.group(1).replace(',', '')), float(est.group(2).replace(',', ''))]
        recs.append(r)
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sale', type=int, action='append', help='refetch these sales')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    state = load_json(STATE, {'sales': {}})
    f = Fetcher()
    try:
        sales = list_sales(f)
        for s in sales:
            if a.sale and s['sale'] not in a.sale:
                continue
            if not a.sale and state['sales'].get(str(s['sale']), {}).get('lots'):
                continue
            ppath = fetch_pdf(f, s['price_url'], f"price_{s['sale']}.pdf")
            cpath = fetch_pdf(f, s['cat_url'], f"cat_{s['sale']}.pdf") if s['cat_url'] else None
            if not ppath:
                log(f"sale {s['sale']}: price list missing")
                continue
            prices = parse_prices(pdf_text(ppath))
            cat = parse_catalogue(pdf_text(cpath)) if cpath else {}
            recs = build(s, prices, cat)
            save_records(os.path.join(OUT, f"sale_{s['sale']}.json"), recs)
            sold = sum(1 for r in recs if not r['unsold'])
            state['sales'][str(s['sale'])] = {'lots': len(recs), 'sold': sold, 'date': s['date'],
                                              'catalogue_lots': len(cat), 'fetched': time.strftime('%Y-%m-%d')}
            state.pop('blocked', None)
            save_json(STATE, state, indent=1)
            log(f"sale {s['sale']} ({s['date']}): {len(recs)} lots, {sold} sold, {len(cat)} in catalogue text")
    except BlockedError as e:
        log('STOPPED, blocked:', e)
        state['blocked'] = str(e)
    save_json(STATE, state, indent=1)
    total = sum(v.get('lots', 0) for v in state['sales'].values())
    log(f'database now {total} lots in {len(state["sales"])} sales')


if __name__ == '__main__':
    main()
