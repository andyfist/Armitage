"""Shared helpers for the price-database scrapers.

Every scraper in this folder:
- reads public results pages only, one request every RATE seconds or slower,
- checks robots.txt before fetching,
- stops the moment a site blocks it or shows a bot check (BlockedError),
- keeps its own small state file so a rerun only fetches what is new.

Common record (one per lot):
{"source","sale","lot","date":"YYYY-MM-DD","title","description",
 "hammer_aud":float,"premium_included":bool,"unsold":bool,"url","category":"coins"|"books"}
"""
import gzip
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
UA = 'Mozilla/5.0 (compatible; ArmitagePriceDB/1.0; read-only, 1 request per second)'
RATE = 1.5

MONTHS = {m: i for i, m in enumerate(
    'january february march april may june july august september october november december'.split(), 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
MONTHS['sept'] = 9

BOT_MARKERS = ('cf-challenge', 'captcha', 'are you a robot', 'verify you are human',
               'attention required', 'access denied', 'cf-browser-verification')


class BlockedError(Exception):
    pass


class Fetcher:
    def __init__(self, rate=RATE):
        self.rate = rate
        self.last = 0.0
        self.robots = {}

    def allowed(self, url):
        host = '{0.scheme}://{0.netloc}'.format(urlparse(url))
        if host not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                rp.parse(self._get(host + '/robots.txt').decode('utf-8', 'replace').splitlines())
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    raise BlockedError(f'robots.txt refused with HTTP {e.code} at {host}')
                rp.parse([])  # no robots.txt: everything allowed
            delay = rp.crawl_delay(UA) or rp.crawl_delay('*')
            if delay and delay > self.rate:
                self.rate = float(delay)
            self.robots[host] = rp
        return self.robots[host].can_fetch(UA, url)

    def _get(self, url, binary=False):
        wait = self.rate - (time.time() - self.last)
        if wait > 0:
            time.sleep(wait)
        self.last = time.time()
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()

    def get(self, url, binary=False, tries=3):
        """Fetch a page. Returns bytes (binary) or text; None on 404. Raises BlockedError."""
        if not self.allowed(url):
            raise BlockedError(f'robots.txt disallows {url}')
        for attempt in range(tries):
            try:
                data = self._get(url)
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if e.code in (401, 403, 429):
                    raise BlockedError(f'HTTP {e.code} at {url}')
                if attempt == tries - 1:
                    raise
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt == tries - 1:
                    raise
            time.sleep(5 * (attempt + 1))
        if binary:
            return data
        text = data.decode('utf-8', 'replace')
        low = text[:20000].lower()
        if any(m in low for m in BOT_MARKERS) and len(text) < 50000:
            raise BlockedError(f'bot check page at {url}')
        return text


def clean(fragment):
    """HTML fragment to plain text."""
    t = re.sub(r'<br\s*/?>', ' ', fragment or '')
    t = re.sub(r'<[^>]+>', '', t)
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


def parse_date(text):
    """First date in strings like '21-23 April 1999' or '30 November - 2 December 2010'."""
    if not text:
        return None
    low = text.lower()
    years = re.findall(r'\b(1[89]\d\d|20\d\d)\b', low)
    month = next((MONTHS[w] for w in re.findall(r'[a-z]+', low) if w in MONTHS), None)
    day = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\b', low)
    if not years or not month or not day:
        return None
    return f'{int(years[-1]):04d}-{month:02d}-{int(day.group(1)):02d}'


def money(text):
    m = re.search(r'\$\s*([\d,]+(?:\.\d+)?)', text or '')
    return float(m.group(1).replace(',', '')) if m else None


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, obj, indent=None):
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


def save_records(path, recs):
    """A JSON list with one record per line, so git diffs stay readable. A .gz path is gzipped."""
    tmp = path + '.tmp'
    opener = gzip.open if path.endswith('.gz') else open
    with opener(tmp, 'wt', encoding='utf-8') as f:
        f.write('[\n' + ',\n'.join(json.dumps(r, ensure_ascii=False) for r in recs) + '\n]\n')
    os.replace(tmp, path)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)
    sys.stdout.flush()
