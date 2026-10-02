# -*- coding: utf-8 -*-
"""端到端验证：加载测评HTML、自动作答、检查结果页、截图"""
import sys, json, pathlib
from playwright.sync_api import sync_playwright

HTML = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "学习力测评_学习拖延与自律.html").resolve()
DATA = sys.argv[2] if len(sys.argv) > 2 else "questions_learn/005.json"
d = json.load(open(DATA, encoding="utf-8"))
NQ, ND = len(d["questions"]), len(d["dimensions"])
errs = []

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 1000})
    logs = []
    pg.on("console", lambda m: logs.append(f"{m.type}: {m.text}"))
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(HTML.as_uri())
    pg.wait_for_timeout(500)

    # 介绍页
    assert pg.locator("#i-title").inner_text() == d["theme"], "标题不符"
    dims_shown = pg.locator("#i-dims .dim-row").count()
    assert dims_shown == ND, f"介绍页维度数 {dims_shown} != {ND}"
    pg.screenshot(path="shot_intro.png", full_page=True)

    # 开始
    pg.click("#btn-start")
    pg.wait_for_timeout(400)
    qcards = pg.locator("#q-list .qcard").count()
    print("首页题卡数:", qcards)
    assert qcards > 0

    # 故意测试未答拦截
    pg.click("#btn-next")
    pg.wait_for_timeout(200)
    toast_txt = pg.locator("#toast").inner_text()
    assert "未作答" in toast_txt, f"未答拦截失效: {toast_txt}"
    print("未答拦截 OK:", toast_txt)

    # 逐页作答：单选题选第2项，多选题选第1、3项
    pages = 0
    while True:
        for i in range(pg.locator("#q-list .qcard").count()):
            box = pg.locator(f"#q-list .qcard >> nth={i}")
            typ = box.locator(".opts").get_attribute("data-type")
            idx = [1] if typ == "单选" else [0, 2]
            for j in idx:
                box.locator(f".opts .opt >> nth={j}").click()
                pg.wait_for_timeout(25)
        pages += 1
        if pg.locator("#btn-submit").is_visible():
            break
        pg.click("#btn-next")
        pg.wait_for_timeout(280)
        if pages > 20:
            errs.append("翻页死循环"); break
    print("翻页数:", pages)
    pg.wait_for_timeout(500)
    pg.screenshot(path="shot_quiz.png", full_page=True)

    # 答题卡跳转测试
    pg.click("#q-sheet button >> nth=0")
    pg.wait_for_timeout(300)
    assert "第 1 页" in pg.locator("#q-plabel").inner_text(), "答题卡跳转失效"
    # 回到末页提交
    for _ in range(pages):
        if pg.locator("#btn-submit").is_visible():
            break
        pg.click("#btn-next")
        pg.wait_for_timeout(200)
    pg.on("dialog", lambda dl: dl.accept())
    pg.click("#btn-submit")
    pg.wait_for_timeout(1400)

    # 结果页
    assert pg.locator("#scr-result").is_visible(), "结果页未显示"
    rate = pg.locator("#r-rate").inner_text()
    total = pg.locator("#r-total").inner_text()
    badge = pg.locator("#r-badge").inner_text()
    dimcards = pg.locator("#r-dims .dim-row").count()
    radar_ok = pg.locator("#r-radar svg polygon").count() >= 5
    review = pg.locator("#r-review .rv-item").count()
    bars = pg.locator("#r-dims .dim-bar > i").all_inner_texts
    print("结果页:", rate, "|", total, "|", badge, "| 维度卡:", dimcards, "| 雷达:", radar_ok, "| 逐题:", review)
    assert dimcards == ND, "结果页维度数不符"
    assert review == NQ, f"逐题回顾 {review} != {NQ}"
    assert radar_ok, "雷达图缺失"
    assert "%" in rate
    # 分数段文本存在
    for i in range(ND):
        ab = pg.locator(f"#r-dims .dim-row >> nth={i}").inner_text()
        assert "维度解读" in ab and "改进建议" in ab, f"维度{i}缺解读/建议"
    # 进度环非零
    off = pg.locator("#ring-arc").get_attribute("style")
    assert "stroke-dashoffset" in (off or ""), "得分环未动"
    pg.screenshot(path="shot_result.png", full_page=True)

    # 深色模式
    pg.click("#btn-theme")
    pg.wait_for_timeout(400)
    assert pg.evaluate("document.documentElement.dataset.theme") == "dark", "主题切换失效"
    pg.screenshot(path="shot_dark.png", full_page=True)

    # 展开逐题回顾
    pg.click("#btn-theme")
    pg.click("details.review summary")
    pg.wait_for_timeout(300)

    # 手机视口
    m = b.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
    m.goto(HTML.as_uri()); m.wait_for_timeout(400)
    m.screenshot(path="shot_mobile_intro.png")
    m.click("#btn-start"); m.wait_for_timeout(400)
    m.screenshot(path="shot_mobile_quiz.png")

    js_err = [l for l in logs if l.startswith("error")]
    print("console errors:", js_err[:5])
    assert not errs, f"页面异常: {errs}"
    assert not js_err, f"JS报错: {js_err}"
    b.close()

print("\n=== 端到端全部通过 ===")
print(f"校验项：标题/维度{ND}个/未答拦截/翻页{pages}页/答题卡跳转/结果页评级{rate}/总分{total}/维度卡{dimcards}/雷达图/逐题回顾{review}/分数段解读/深色模式/移动视口")
