# -*- coding: utf-8 -*-
"""抓取 1799 个测评详情页：提取 JSON-LD 完整简介 + 所属分类"""
import re, json, time, random, threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
RE_JSONLD = re.compile(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', re.S)
RE_CAT = re.compile(r"title='所属分类:([^']+)'")
RE_BADGE_HREF = re.compile(r'href="/c/[A-Za-z0-9]+/"[^>]*title=\'所属分类')

lock = threading.Lock()
results = {}
fails = []

def fetch(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            last = e
            time.sleep(1.5 + 2 * i)
    raise last

def strip_md(s):
    # 轻量 markdown -> 纯文本
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)          # [text](url) -> text
    s = s.replace('\\/', '/')
    s = re.sub(r'(\*\*|__|`|~~)', '', s)                     # 强调符号
    s = re.sub(r'^#{1,6}\s*', '', s, flags=re.M)             # 标题井号
    s = s.replace('\\u003e', '>').replace('> ', '', 0)
    s = re.sub(r'^\s*>\s?', '', s, flags=re.M)               # 引用块
    s = re.sub(r'^\s*[-*]\s+', '· ', s, flags=re.M)          # 列表符号
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()

def work(t):
    url = t["url"]
    try:
        html = fetch(url)
        m = RE_JSONLD.search(html)
        desc = ""
        if m:
            try:
                data = json.loads(m.group(1))
                desc = strip_md(data.get("description", "") or "")
            except Exception:
                desc = ""
        if not desc:
            # 退回 og:description（截断版）
            mo = re.search(r'property="og:description" content="([^"]*)"', html)
            if mo:
                desc = mo.group(1)
        mc = RE_CAT.search(html)
        cat = mc.group(1).strip() if mc else t.get("category", "")
        with lock:
            results[t["id"]] = {"id": t["id"], "url": url, "title": t["title"],
                                "desc": desc, "category": cat}
        return True
    except Exception as e:
        with lock:
            fails.append((t["id"], str(e)))
        return False

def main():
    tests = json.load(open("tests.json", encoding="utf-8"))
    done_ids = set()
    try:
        old = json.load(open("tests_full.json", encoding="utf-8"))
        for v in old:
            if v["desc"]:
                results[v["id"]] = v
                done_ids.add(v["id"])
    except FileNotFoundError:
        pass
    todo = [t for t in tests if t["id"] not in done_ids]
    print(f"todo={len(todo)} cached={len(done_ids)}", flush=True)
    t0 = time.time()
    ok = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(work, t) for t in todo]
        for i, f in enumerate(as_completed(futs), 1):
            ok += f.result()
            if i % 100 == 0:
                with lock:
                    with open("tests_full.json", "w", encoding="utf-8") as fp:
                        json.dump(list(results.values()), fp, ensure_ascii=False)
                el = time.time() - t0
                print(f"{i}/{len(todo)} ok={ok} elapsed={el:.0f}s eta={el/i*(len(todo)-i):.0f}s", flush=True)
    with open("tests_full.json", "w", encoding="utf-8") as fp:
        json.dump(list(results.values()), fp, ensure_ascii=False)
    print(f"DONE ok={ok} fails={len(fails)}", flush=True)
    for fid, err in fails[:20]:
        print("FAIL", fid, err, flush=True)

if __name__ == "__main__":
    main()
