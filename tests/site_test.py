# -*- coding: utf-8 -*-
"""验证总集成 index.html 与抽样测评页"""
import json, re, pathlib, random, sys
from playwright.sync_api import sync_playwright

SITE = pathlib.Path("site").resolve()
PAT = re.compile(r'let TEST_DATA = (\{.*?\});\s*\n\s*const CONFIG', re.S)
errs = []

def run_one(pg, html_path, data, label):
    pg.goto(html_path.as_uri())
    pg.wait_for_timeout(400)
    assert pg.locator("#i-title").inner_text() == data["theme"], f"{label} 标题不符"
    assert pg.locator("#i-dims .dim-row").count() == len(data["dimensions"]), f"{label} 维度数不符"
    pg.click("#btn-start")
    pg.wait_for_timeout(300)
    pages = 0
    while True:
        for i in range(pg.locator("#q-list .qcard").count()):
            box = pg.locator(f"#q-list .qcard >> nth={i}")
            typ = box.locator(".opts").get_attribute("data-type")
            for j in ([1] if typ == "单选" else [0, 2]):
                box.locator(f".opts .opt >> nth={j}").click()
        pages += 1
        if pg.locator("#btn-submit").is_visible():
            break
        pg.click("#btn-next")
        pg.wait_for_timeout(160)
        if pages > 40:
            errs.append(f"{label} 翻页异常"); return
    pg.on("dialog", lambda d: d.accept())
    pg.click("#btn-submit")
    pg.wait_for_timeout(900)
    assert pg.locator("#scr-result").is_visible(), f"{label} 无结果页"
    rate = pg.locator("#r-rate").inner_text()
    total = pg.locator("#r-total").inner_text()
    dims = pg.locator("#r-dims .dim-row").count()
    review = pg.locator("#r-review .rv-item").count()
    assert dims == len(data["dimensions"]) and review == len(data["questions"])
    assert "%" in rate and "/" in total
    print(f"  ✓ {label}: {len(data['questions'])}题/{pages}页 结果 {total} 得分率{rate} 维度{dims} 回顾{review}")

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1366, "height": 950})
    logs = []
    pg.on("pageerror", lambda e: errs.append("index:" + str(e)))
    pg.on("console", lambda m: logs.append(m.type + ":" + m.text) if m.type == "error" else None)
    pg.goto((SITE / "index.html").as_uri())
    pg.wait_for_timeout(600)
    n_cards = pg.locator(".card").count()
    n_groups = pg.locator("section.grp").count()
    stats = pg.locator("#stats").inner_text().replace("\n", " ")
    print(f"index: 卡片{n_cards} 分类区块{n_groups} | {stats[:60]}")
    assert n_cards == 411, f"卡片数 {n_cards} != 411"
    assert n_groups == 15, f"分类数 {n_groups} != 15"
    pg.screenshot(path="shot_index.png", full_page=False)

    # 搜索
    pg.fill("#q", "MBTI")
    pg.wait_for_timeout(350)
    found = pg.locator(".card").count()
    assert 0 < found < 411, f"搜索失效 {found}"
    print("搜索 MBTI ->", found, "个结果")
    pg.screenshot(path="shot_index_search.png")

    # 清空 + 风格筛选
    pg.fill("#q", "")
    pg.wait_for_timeout(300)
    pg.click(".chip[data-s='知识问答']")
    pg.wait_for_timeout(350)
    kn = pg.locator(".card").count()
    assert 0 < kn < 411
    print("风格筛选 知识问答 ->", kn, "个")
    pg.click(".chip[data-s='']")
    pg.wait_for_timeout(300)

    # 侧栏分类跳转
    pg.click("nav.side a[data-g='学习力']")
    pg.wait_for_timeout(400)
    assert pg.locator(".card").count() == 20, "分类筛选失效"
    print("分类 学习力 -> 20 个")
    pg.click("nav.side a[data-g='']")
    pg.wait_for_timeout(300)

    # 点击卡片真实跳转
    pg.locator(".card >> nth=0").click()
    pg.wait_for_timeout(600)
    assert "/web/" in pg.url and pg.locator("#i-title").inner_text() != "—", "卡片跳转失败"
    print("卡片跳转 ->", pg.url.split("/")[-1], pg.locator("#i-title").inner_text())
    pg.go_back()

    # 抽样跑 5 个测评（覆盖不同域与风格）
    idx = open(SITE / "index.html", encoding="utf-8").read()
    man = json.loads(re.search(r'const MANIFEST = (\[.*?\]);\nconst GROUPS', idx, re.S).group(1))
    random.seed(20)
    picks = []
    for dom in ["人格与个性", "心理健康", "知识与趣味娱乐", "学习力", "性与性别心理"]:
        cand = [m for m in man if m["domain"] == dom]
        picks.append(random.choice(cand))
    picks.append([m for m in man if m["style"] == "知识问答"][0])
    for m in picks:
        d = json.loads(PAT.search((SITE / "web" / m["file"]).read_text(encoding="utf-8")).group(1))
        run_one(pg, SITE / "web" / m["file"], d, f"{m['code']} {m['theme'][:14]}({m['style']})")

    assert not logs, f"console errors: {logs[:4]}"
    assert not errs, f"errors: {errs[:4]}"
    b.close()
print("\n=== 站点验证全部通过 ===")
