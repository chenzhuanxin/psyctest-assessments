# -*- coding: utf-8 -*-
"""中央校验器：校验391个问卷JSON并自动修复分数段区间"""
import json, os

batches = json.load(open("batches.json", encoding="utf-8"))
plan = {}
for b in batches:
    for t in b:
        plan[t["id"]] = t

report = {"themes": [], "repairs": 0, "errors": []}
warn = []

def q_low_high(q):
    scores = [o["score"] for o in q["options"]]
    if q["type"] == "多选":
        return sum(min(0, s) for s in scores), sum(s for s in scores if s > 0)
    return min(scores), max(scores)

def fix_bands(dims, qmap):
    """qmap: dim code -> list of questions; 修复 bands 覆盖 [low, high]"""
    n = 0
    for d in dims:
        qs = qmap[d["code"]]
        lo = sum(q_low_high(q)[0] for q in qs)
        hi = sum(q_low_high(q)[1] for q in qs)
        bands = sorted(d["bands"], key=lambda b: b["min"])
        # 重建连续区间
        if len(bands) < 2:
            warn.append(f"{d['code']} bands<2")
            continue
        changed = False
        if bands[0]["min"] != lo:
            bands[0]["min"] = lo; changed = True
        if bands[-1]["max"] != hi:
            bands[-1]["max"] = hi; changed = True
        for i in range(1, len(bands)):
            exp = bands[i-1]["max"] + 1
            if bands[i]["min"] != exp:
                bands[i]["min"] = exp; changed = True
            if bands[i]["max"] < bands[i]["min"]:
                bands[i]["max"] = bands[i]["min"]; changed = True
        # 保证递增到 hi
        if bands[-1]["min"] > hi:
            bands[-1]["min"] = max(lo, hi - 1); changed = True
            bands[-1]["max"] = hi
        d["bands"] = bands
        n += 1 if changed else 0
    return n

for tid in sorted(plan):
    p = f"questions/{tid:03d}.json"
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        report["errors"].append(f"{tid}: 解析失败 {e}")
        continue
    tinfo = plan[tid]
    issues = []
    qs = d["questions"]
    # 题数
    if not (15 <= len(qs) <= 120):
        issues.append(f"题数{len(qs)}越界")
    if len(qs) != tinfo["size"]:
        warn.append(f"{tid}: 题数{len(qs)}≠计划{tinfo['size']}")
    # 题号连续
    if [q["no"] for q in qs] != list(range(1, len(qs) + 1)):
        issues.append("题号不连续")
    dims = {x["code"]: x for x in d["dimensions"]}
    if not (2 <= len(dims) <= 5):
        issues.append(f"维度数{len(dims)}")
    qmap = {c: [] for c in dims}
    multi_cnt = 0
    for q in qs:
        if q["type"] not in ("单选", "多选"):
            issues.append(f"题型{q.get('type')}")
        if q["type"] == "多选":
            multi_cnt += 1
            scores = [o["score"] for o in q["options"]]
            if any(s < 0 or s > 2 for s in scores):
                if tinfo["style"] == "知识问答" and all(s in (0, 1) for s in scores):
                    pass  # 知识多选 0/1 计分
                else:
                    issues.append(f"Q{q['no']}多选分值越界")
        else:
            scores = sorted(o["score"] for o in q["options"])
            texts = [o["text"] for o in q["options"]]
            if tinfo["style"] == "知识问答":
                # 知识单选：恰1个正确(1分)其余0分
                if scores != [0, 0, 0, 1] and scores != [0, 0, 0, 0, 1]:
                    issues.append(f"Q{q['no']}知识单选分值{scores}")
            elif tinfo["style"] == "频率自评" and set(texts) == {"从不", "偶尔", "经常", "总是"}:
                if scores != [1, 2, 3, 4]:
                    issues.append(f"Q{q['no']}频率分值{scores}")
            else:
                # 情景/趣味单选：分值为1..n的排列，n=选项数(4或5)
                n = len(scores)
                if n not in (4, 5) or scores != list(range(1, n + 1)):
                    issues.append(f"Q{q['no']}单选分值{scores}")
        if len(q["options"]) not in (4, 5):
            issues.append(f"Q{q['no']}选项数{len(q['options'])}")
        if q["dim"] not in dims:
            issues.append(f"Q{q['no']}维度{q['dim']}未定义")
        else:
            qmap[q["dim"]].append(q)
    if multi_cnt == 0:
        warn.append(f"{tid}: 无多选题")
    if multi_cnt > 0.2 * len(qs) + 0.001:
        warn.append(f"{tid}: 多选{multi_cnt}超20%")
    for c, lst in qmap.items():
        if len(lst) < 3:
            issues.append(f"维度{c}仅{len(lst)}题")
    # 修复分数段
    nfix = fix_bands(d["dimensions"], qmap)
    if nfix:
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        report["repairs"] += nfix
    if issues:
        report["errors"].append(f"{tid}: " + "; ".join(issues[:6]))
    report["themes"].append({"id": tid, "nq": len(qs), "ndim": len(dims),
                             "style": tinfo["style"]})

total_q = sum(t["nq"] for t in report["themes"])
print(f"主题 {len(report['themes'])}/391  总题量 {total_q}  修复分数段维度数 {report['repairs']}")
print(f"错误主题数 {len(report['errors'])}  警告 {len(warn)}")
for e in report["errors"][:20]: print("ERR", e)
for w in warn[:15]: print("WARN", w)
json.dump(report, open("validate_report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("报告已写入 validate_report.json")
