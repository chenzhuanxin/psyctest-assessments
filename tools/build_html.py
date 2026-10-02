# -*- coding: utf-8 -*-
"""把测评 JSON 注入 HTML 模板 -> 生成可独立打开的测评单页应用
用法： python build_html.py questions_learn/005.json
      python build_html.py questions/001.json --out MBTI测评.html
"""
import json, re, sys, os

TPL = "app_template.html"

# 主题级引导语（可选覆盖；缺省则用引擎自动生成的描述）
INTROS = {}

def build(src_json, out_html=None):
    d = json.load(open(src_json, encoding="utf-8"))
    assert d.get("questions") and d.get("dimensions"), "JSON 需含 questions 与 dimensions"
    if "intro" not in d:
        d["intro"] = INTROS.get(d["id"]) or ""
    tpl = open(TPL, encoding="utf-8").read()
    payload = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    html = tpl.replace("/*__TEST_DATA__*/null", payload, 1)
    out = out_html or f"{d['theme']}_测评.html"
    out = re.sub(r'[\\/:*?"<>|]', "_", out)
    open(out, "w", encoding="utf-8").write(html)
    nq = len(d["questions"]); nd = len(d["dimensions"])
    print(f"OK  {out}  ({d['domain']}/{d['theme']})  {nq}题 {nd}维度  {os.path.getsize(out)//1024}KB")
    return out

if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    if not args:
        print(__doc__); sys.exit(1)
    src = args[0]
    out = args[args.index("--out") + 1] if "--out" in args else None
    build(src, out)
