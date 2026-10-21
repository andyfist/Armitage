#!/usr/bin/env python3
"""Usage: python3 pipeline/new_sales.py [--no-save]

Read-only check of armitage.bidsonline.com.au for catalogues (sales) not seen before.
Every catalogue ever seen is remembered in pipeline/state/sales.json, seeded from
work/armitage_catalogues.json the first time. Prints one JSON object:

  checked   when the check ran (Hobart time)
  current   chids of the catalogues on the site right now
  new       catalogues seen for the first time, each with name, lot count, first and
            last close time, the catalogue URL and a ready-to-send email body
  errors    what went wrong, if anything
  alert_unreachable  true when the site has failed on two checks in a row

Two requests when nothing is new, plus one group-page request per new catalogue.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, 'pipeline', 'state', 'sales.json')
LEGACY = os.path.join(ROOT, 'work', 'armitage_catalogues.json')
BASE = 'https://armitage.bidsonline.com.au'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'

try:
    from zoneinfo import ZoneInfo
    HOBART = ZoneInfo('Australia/Hobart')
except Exception:  # no tz database on this machine: Tasmania is on daylight time Oct to Apr
    HOBART = datetime.timezone(datetime.timedelta(hours=11), 'AEDT')


def now_text():
    return datetime.datetime.now(HOBART).strftime('%d/%m/%Y %H:%M %Z')


def fetch(path, tries=3):
    """GET one page as text. Raises the last error after `tries` attempts."""
    err = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(f'{BASE}/{path}', headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode('utf-8', 'ignore')
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            err = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f'{path}: {err}')


def strip(h):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()


def list_catalogues():
    """The catalogues linked from the home page and the auctions page: {chid: {chid, name, catalogue_no?, starts?}}."""
    home, auctions = fetch(''), fetch('auctions.aspx')
    cats = {}
    for chid, name in re.findall(r'catalogue-group\.aspx\?chid=(\d+)[^"]*"[^>]*>([^<]+)<', home + auctions):
        cats.setdefault(chid, {'chid': chid, 'name': strip(name)})
    text = strip(auctions)
    for m in re.finditer(r'(ONLINE AUCTION.{0,120}?)\s*Catalogue No\. (\d+) - Starts: (\d+/\d+/\d+ [\d:]+ [AP]M)', text):
        name, no, starts = m.group(1).strip(), m.group(2), m.group(3)
        for c in cats.values():
            if c['name'].upper() == name.upper():
                c.update(catalogue_no=no, starts=starts)
    return cats


CLOSE_RE = re.compile(r'(\d+)/(\d+)/(\d+) (\d+):(\d+)(?::(\d+))? ([AP])M')


def close_key(text):
    """Sortable number for a close time like '21/10/2026 12:30:00 PM ADST' (0 when unreadable)."""
    m = CLOSE_RE.search(text or '')
    if not m:
        return 0
    d, mo, y, h, mi, s, ap = m.groups()
    h = int(h) % 12 + (12 if ap == 'P' else 0)
    return int(y) * 10**10 + int(mo) * 10**8 + int(d) * 10**6 + h * 10**4 + int(mi) * 100 + int(s or 0)


def close_pretty(text):
    """'21/10/2026 12:30:00 PM ADST' -> 'Wed 21 Oct 2026, 12:30 pm'."""
    m = CLOSE_RE.search(text or '')
    if not m:
        return text or 'unknown'
    d, mo, y, h, mi, s, ap = m.groups()
    h = int(h) % 12 + (12 if ap == 'P' else 0)
    dt = datetime.datetime(int(y), int(mo), int(d), h, int(mi))
    return dt.strftime('%a %d %b %Y, %I:%M %p').replace(' 0', ' ').lower().replace(dt.strftime('%a').lower(), dt.strftime('%a')).replace(dt.strftime('%b').lower(), dt.strftime('%b'))


def group_summary(chid):
    """Lot count and close times from the catalogue's group page (one request)."""
    page = fetch(f'catalogue-group.aspx?chid={chid}&BID=')
    items, seen = [], set()
    for m in re.finditer(r'id="item_(\d+)"(.*?)id="timelabel_\1"[^>]*>([^<]*)<', page, flags=re.S):
        cdid = int(m.group(1))
        if cdid in seen:
            continue
        seen.add(cdid)
        lot = re.search(r'Lot:\s*([^\s<]+)\s*-', m.group(2))
        items.append({'cdid': cdid, 'lot': lot.group(1) if lot else '', 'close': m.group(3).strip()})
    closes = sorted((close_key(i['close']), i['close']) for i in items if close_key(i['close']))
    return {
        'lots': len(items),
        'lot_first': items[0]['lot'] if items else '',
        'lot_last': items[-1]['lot'] if items else '',
        'close_first': closes[0][1] if closes else '',
        'close_last': closes[-1][1] if closes else '',
    }


def email_body(c):
    lines = [
        f"New Armitage sale found: {c['name']}" + (f" (catalogue {c['catalogue_no']})" if c.get('catalogue_no') else ''),
        f"Lots: {c.get('lots', '?')}" + (f" (lot {c['lot_first']} to {c['lot_last']})" if c.get('lot_first') else ''),
        f"First lot closes: {close_pretty(c.get('close_first'))}",
        f"Last lot closes: {close_pretty(c.get('close_last'))}",
        f"Catalogue: {BASE}/catalogue-group.aspx?chid={c['chid']}",
        f"Found: {c['first_seen']}",
        '',
        'Stage done: found. You will get another email as each later stage finishes.',
    ]
    return '\n'.join(lines)


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    state = {'catalogues': {}, 'failures': 0}
    if os.path.exists(LEGACY):  # first run: the catalogues the earlier watcher already knew about
        for chid, c in json.load(open(LEGACY)).items():
            c = dict(c)
            c.setdefault('stages', {})['found'] = c.get('first_seen', 'before the pipeline')
            state['catalogues'][chid] = c
    return state


def save_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(state, open(STATE, 'w'), indent=1, sort_keys=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--no-save', action='store_true', help='do not write pipeline/state/sales.json')
    args = ap.parse_args()

    state = load_state()
    out = {'checked': now_text(), 'current': [], 'new': [], 'errors': [], 'alert_unreachable': False}
    try:
        cats = list_catalogues()
    except Exception as e:
        state['failures'] = state.get('failures', 0) + 1
        out['errors'].append(f'could not read the Armitage site: {e}')
        out['alert_unreachable'] = state['failures'] == 2
        if not args.no_save:
            save_state(state)
        print(json.dumps(out, indent=1))
        return 1
    state['failures'] = 0
    out['current'] = sorted(cats)

    for chid, c in sorted(cats.items()):
        known = state['catalogues'].get(chid)
        if known:
            known.update({k: v for k, v in c.items() if v})  # pick up a catalogue number or start time seen later
            continue
        c['first_seen'] = out['checked']
        c['stages'] = {'found': out['checked']}
        try:
            c.update(group_summary(chid))
        except Exception as e:
            out['errors'].append(f'catalogue {chid}: group page failed: {e}')
        c['email'] = email_body(c)
        state['catalogues'][chid] = {k: v for k, v in c.items() if k != 'email'}
        out['new'].append(c)

    if not args.no_save:
        save_state(state)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
