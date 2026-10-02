# -*- coding: utf-8 -*-
"""批量生成整站：411 个独立测评页 + 分门别类的总集成 index.html
输出目录 site/
  site/index.html            总集成导航（搜索/分类/风格筛选/随机）
  site/web/{CODE}.html       单个测评（自包含，可离线双击打开）
  site/data/{CODE}.json      对应题库配置（可用于引擎内“导入测评”或二次开发）
"""
import json, os, re, shutil, sys

SRC = [("questions", "P", "psyctest"), ("questions_learn", "L", "学习力")]
OUT = "site"
GROUP_ORDER = ["人格与个性", "恋爱与亲密关系", "婚姻与家庭", "人际与社交", "职场与事业",
               "心理健康", "情绪与压力管理", "认知与能力", "自我成长与人生观", "金钱与财富",
               "性与性别心理", "亲子儿童与青少年", "知识与趣味娱乐", "投射与潜意识", "学习力"]

tpl = open("app_template.html", encoding="utf-8").read()
idx_tpl = open("index_template.html", encoding="utf-8").read()

for sub in ("web", "data"):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)

manifest = []
for root, prefix, tag in SRC:
    for fn in sorted(os.listdir(root)):
        if not fn.endswith(".json"):
            continue
        d = json.load(open(os.path.join(root, fn), encoding="utf-8"))
        code = f"{prefix}{d['id']:03d}"
        d["code"] = code
        payload = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
        html = tpl.replace("/*__TEST_DATA__*/null", payload, 1)
        assert "/*__TEST_DATA__*/" not in html, "注入失败"
        open(os.path.join(OUT, "web", f"{code}.html"), "w", encoding="utf-8").write(html)
        json.dump(d, open(os.path.join(OUT, "data", f"{code}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        manifest.append({"code": code, "id": d["id"], "domain": d.get("domain") or "未分类",
                         "theme": d["theme"], "style": d.get("style", "情景选择"),
                         "nq": len(d["questions"]), "ndim": len(d["dimensions"]),
                         "dims": [x["name"] for x in d["dimensions"]],
                         "file": f"{code}.html"})

groups = [g for g in GROUP_ORDER if any(m["domain"] == g for m in manifest)]
groups += sorted({m["domain"] for m in manifest} - set(groups))
order = {g: i for i, g in enumerate(groups)}
manifest.sort(key=lambda m: (order.get(m["domain"], 99), m["code"]))

idx = idx_tpl.replace("/*__MANIFEST__*/[]", json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), 1)
idx = idx.replace("/*__GROUPS__*/[]", json.dumps(groups, ensure_ascii=False), 1)
assert "/*__MANIFEST__*/" not in idx and "/*__GROUPS__*/" not in idx
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(idx)

nq = sum(m["nq"] for m in manifest)
size = sum(f.stat().st_size for f in os.scandir(os.path.join(OUT, "web"))) / 1048576
print(f"生成完成：{len(manifest)} 个测评页 / {nq} 题 / {len(groups)} 个分类")
for g in groups:
    items = [m for m in manifest if m["domain"] == g]
    print(f"  {g:<10} {len(items):>3} 个  {sum(x['nq'] for x in items):>5} 题")
print(f"web 目录体积 {size:.1f} MB；index.html 与 data/ 已就绪")
