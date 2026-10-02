# -*- coding: utf-8 -*-
"""题目选项乱序：消除“正确/高分项总在A或D”的位置线索
规则：
  · 频率自评的四级锚点（从不/偶尔/经常/总是）保持语义顺序不动 —— 这是量表刻度，打乱会破坏作答体验
  · 其余题目（情景选择/轻松趣味/知识问答/多选题）用带种子随机数打乱，并按新位置重新标 A/B/C/D/E
  · 分值随选项文本一起移动，因此维度满分/最低分与分数段区间完全不变
  · 原文件先备份到 backup_original/
"""
import json, os, random, shutil, sys
from collections import Counter, defaultdict

LIKERT = {"从不", "偶尔", "经常", "总是"}
DIRS = ["questions", "questions_learn"]
BACKUP = "backup_original"

os.makedirs(BACKUP, exist_ok=True)
stat = {"themes": 0, "questions": 0, "shuffled": 0, "kept_likert": 0}
pos_max = Counter()          # 全库：最高分选项落在哪个字母
pos_correct = Counter()      # 知识问答：正确项字母
per_theme_worst = []

for root in DIRS:
    if not os.path.isdir(root):
        continue
    bdir = os.path.join(BACKUP, root)
    os.makedirs(bdir, exist_ok=True)
    for fn in sorted(os.listdir(root)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(root, fn)
        bak = os.path.join(bdir, fn)
        if not os.path.exists(bak):
            shutil.copy2(path, bak)
        d = json.load(open(path, encoding="utf-8"))
        tid = d["id"]
        rng = random.Random(tid * 7919 + 17)   # 可复现
        for q in d["questions"]:
            stat["questions"] += 1
            texts = [o["text"] for o in q["options"]]
            if set(texts) == LIKERT:
                stat["kept_likert"] += 1
                continue
            pairs = [(o["text"], o["score"]) for o in q["options"]]
            rng.shuffle(pairs)
            labels = "ABCDE"
            q["options"] = [{"label": labels[i], "text": t, "score": s}
                            for i, (t, s) in enumerate(pairs)]
            stat["shuffled"] += 1
        # 统计该主题内“最高分选项字母”分布，用于验证不再集中
        cnt = Counter()
        for q in d["questions"]:
            ss = [o["score"] for o in q["options"]]
            mx = max(ss)
            if ss.count(mx) != 1:      # 多选/并列跳过
                continue
            cnt[q["options"][ss.index(mx)]["label"]] += 1
        if cnt:
            tot = sum(cnt.values())
            top_letter, top_n = cnt.most_common(1)[0]
            per_theme_worst.append((d["theme"], top_letter, round(top_n / tot * 100)))
            for L, n in cnt.items():
                pos_max[L] += n
        if d.get("style") == "知识问答":
            for q in d["questions"]:
                ss = [o["score"] for o in q["options"]]
                if max(ss) == 0:
                    continue
                pos_correct[q["options"][ss.index(max(ss))]["label"]] += 1
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        stat["themes"] += 1

print("主题数:", stat["themes"], " 题目数:", stat["questions"])
print("已乱序:", stat["shuffled"], " 保留李克特锚点顺序:", stat["kept_likert"])
print("\n全库最高分选项字母分布:")
tot = sum(pos_max.values())
for L in "ABCDE":
    if pos_max[L]:
        print(f"  {L}: {pos_max[L]:>5}  ({pos_max[L]/tot*100:.1f}%)")
print("\n知识问答正确项字母分布:")
tc = sum(pos_correct.values())
for L in "ABCDE":
    if pos_correct[L]:
        print(f"  {L}: {pos_correct[L]:>4}  ({pos_correct[L]/tc*100:.1f}%)")
worst = sorted(per_theme_worst, key=lambda x: -x[2])[:8]
print("\n单个主题内最高分选项最集中的8例（占比越均匀越好）:")
for name, L, pct in worst:
    print(f"  {pct}% 集中在 {L} —— {name}")
