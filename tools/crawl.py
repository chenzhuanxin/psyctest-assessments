# -*- coding: utf-8 -*-
"""爬取 psyctest.cn 全部测评的标题+简介+分类（列表页分页爬取）"""
import re, json, time, sys, random
import urllib.request
import urllib.parse
from html import unescape

BASE = "https://m.psyctest.cn/tests/"
UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}

LIMIT = 24
MAX_OFFSET = 4000          # 保险上限
OUT_JSON = "tests.json"

CARD_SPLIT = re.compile(r'<div class="card mb-3 mb-md-4 border-0 shadow-sm overflow-hidden position-relative">')
RE_HREF    = re.compile(r'<a href="(/t/[A-Za-z0-9]+/)" class="text-decoration-none">')
RE_TITLE   = re.compile(r'<h2 class="h5 card-title[^"]*">([^<]+)</h2>')
RE_DESC    = re.compile(r'<div class="card-text small text-muted mb-2 text-truncate-line-2">\s*(.*?)\s*</div>', re.S)
RE_CAT     = re.compile(r"href='(/c/[A-Za-z0-9]+/\?type=test)'[^>]*>\s*<strong>([^<]+)</strong>")
RE_TOTPAGE = re.compile(r'(\d+)\s*</a>\s*</li>\s*<li class="page-item">\s*<a id="next_page_link"')

TAG = re.compile(r'<[^>]+>')

def strip_tags(s):
    return re.sub(r'\s+', ' ', unescape(TAG.sub('', s))).strip()

def fetch(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            print(f"  retry {i+1}: {e}", flush=True)
            time.sleep(3 + 3 * i)
    raise RuntimeError(f"fetch failed: {url}")

def parse_page(html):
    cards = CARD_SPLIT.split(html)[1:]
    out = []
    for c in cards:
        m = RE_HREF.search(c)
        if not m:
            continue
        url = "https://m.psyctest.cn" + m.group(1)
        tid = m.group(1).strip('/').split('/')[-1]
        mt = RE_TITLE.search(c)
        md = RE_DESC.search(c)
        mc = RE_CAT.search(c)
        title = strip_tags(mt.group(1)) if mt else ''
        desc  = strip_tags(md.group(1)) if md else ''
        cat   = strip_tags(mc.group(2)) if mc else ''
        out.append({"id": tid, "url": url, "title": title, "desc": desc, "category": cat})
    return out

def total_pages(html):
    m = RE_TOTPAGE.search(html)
    if m:
        return int(m.group(1))
    return None

def main():
    seen = {}
    offset = 0
    pages_expected = None
    empty_streak = 0
    while offset <= MAX_OFFSET:
        url = BASE + ("?" if offset or True else "") + urllib.parse.urlencode({"offset": offset, "limit": LIMIT})
        html = fetch(url)
        if pages_expected is None:
            pages_expected = total_pages(html)
            print(f"total pages: {pages_expected} (~{pages_expected*LIMIT} tests)", flush=True)
        cards = parse_page(html)
        new_cnt = 0
        for c in cards:
            if c["id"] not in seen:
                seen[c["id"]] = c
                new_cnt += 1
        total = len(seen)
        print(f"offset={offset:>4}  cards={len(cards):>2}  new={new_cnt:>2}  total={total}", flush=True)
        if not cards:
            empty_streak += 1
            if empty_streak >= 2:
                break
        else:
            empty_streak = 0
        offset += LIMIT
        time.sleep(0.35 + random.random() * 0.35)
        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump(list(seen.values()), f, ensure_ascii=False, indent=1)
    print(f"DONE: {len(seen)} tests", flush=True)

if __name__ == "__main__":
    main()
