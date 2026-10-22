#!/bin/sh
# Top up every price database. Each scraper only fetches sales it has not saved yet,
# so a night with no new sales makes a handful of requests and changes nothing.
cd "$(dirname "$0")/.." || exit 1
python3 -I databases/noble.py
python3 -I databases/aba.py
