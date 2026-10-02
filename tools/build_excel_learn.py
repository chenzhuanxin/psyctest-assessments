# -*- coding: utf-8 -*-
"""学习力 20 主题 -> psyctest_学习力测评题目与维度.xlsx"""
import json
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

plan = {}
for l in open("batch_spec/batch_learn.txt", encoding="utf-8"):
    l = l.strip()
    if not l or l.startswith("#"):
        continue
    p = l.split("|")
    plan[int(p[0])] = {"id": int(p[0]), "domain": p[1], "name": p[2],
                       "size": int(p[3]), "style": p[4], "desc": p[5]}
data = {tid: json.load(open(f"questions_learn/{tid:03d}.json", encoding="utf-8"))
        for tid in plan}

wb = Workbook()
thin = Side(style="thin", color="D9D9D9")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
hfill = PatternFill("solid", fgColor="4472C4")
hfont = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
body = Font(name="微软雅黑", size=9)
wrap = Alignment(vertical="top", wrap_text=True)
center = Alignment(horizontal="center", vertical="top")


def header(ws, cols, widths):
    for j, (c, w) in enumerate(zip(cols, widths), 1):
        cell = ws.cell(row=1, column=j, value=c)
        cell.font = hfont
        cell.fill = hfill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
        ws.column_dimensions[get_column_letter(j)].width = w


def put(ws, r, values, centers=()):
    for j, v in enumerate(values, 1):
        c = ws.cell(row=r, column=j, value=v)
        c.font = body
        c.alignment = center if j in centers else wrap
        c.border = border


# ---------- 说明 ----------
ws0 = wb.active
ws0.title = "说明"
ws0.sheet_view.showGridLines = False
total_q = sum(len(d["questions"]) for d in data.values())
info = [
    ("学习力测评主题（20个侧面） · 题目与维度设计总表", 14, True),
    ("", 11, False),
    (f"覆盖范围：20 个互不重复的学习力主题，共 {total_q} 道原创题目（每主题 30 题）", 11, False),
    ("生成时间：2026-10-01；题目为原创设计，未抄录任何真实量表原文", 11, False),
    ("", 11, False),
    ("工作表结构：", 11, True),
    ("  ① 学习力主题清单：20 个主题的设计说明（主题定位、考察维度预告）", 11, False),
    ("  ② 主题总览：每主题一行，题数/维度数/分数段数由公式自动统计", 11, False),
    ("  ③ 题目明细：每道题一行，含题干、题型、所属维度、各选项文本与分值", 11, False),
    ("  ④ 维度设置：每个维度一行，含说明、包含题号、最低分/总分（公式汇总）", 11, False),
    ("  ⑤ 分数段分析：每个维度 3-4 个分数段，含评级、分析解读与建议", 11, False),
    ("", 11, False),
    ("计分口径（与前一份《psyctest_测评题目与维度.xlsx》完全一致）：", 11, True),
    ("  · 单选题：得分为所选选项分值。情景选择类 4-5 个选项分值为 1..n 的排列；", 11, False),
    ("  · 频率自评类：选项固定 从不/偶尔/经常/总是（1-4 分），反向陈述题分值 4/3/2/1；", 11, False),
    ("  · 多选题（题干注明）：得分为所选选项分值之和（0/1/2 分制）；", 11, False),
    ("  · 知识问答类（主题9 逻辑推理）：正确项 1 分、错误项 0 分，维度分即答对数；", 11, False),
    ("  · 维度得分 = 该维度题目得分之和；范围见《维度设置》最低分~总分；", 11, False),
    ("  · 题目满分/最低分、维度题数/最低分/总分均为公式，改动分值后自动重算。", 11, False),
    ("", 11, False),
    ("20 个主题的设计逻辑：动力系统（1-2）→ 规划执行（3-5）→ 认知方法（6-8）→ 思维能力（9-11）", 11, False),
    ("→ 信息处理（12-13）→ 应用迁移（14-15）→ 情绪与情境（16-18）→ 社会性学习（19-20）", 11, False),
    ("", 11, False),
    ("使用提示：学习韧性、考前焦虑等主题的分析与建议为非诊断表述，仅供自我探索与工具设计参考。", 11, False),
]
for i, (txt, size, bold) in enumerate(info, 1):
    c = ws0.cell(row=i, column=1, value=txt)
    c.font = Font(name="微软雅黑", size=size, bold=bold)
ws0.column_dimensions["A"].width = 100

# ---------- 学习力主题清单 ----------
wsL = wb.create_sheet("学习力主题清单")
header(wsL, ["序号", "主题", "出题风格", "题数", "主题定位与考察维度", "维度构成"],
       [6, 22, 11, 7, 56, 34])
r = 2
for tid in sorted(plan):
    d = data[tid]
    dimtxt = "、".join(f"{x['name']}({x['code']})" for x in d["dimensions"])
    put(wsL, r, [tid, plan[tid]["name"], plan[tid]["style"], plan[tid]["size"],
                 plan[tid]["desc"], dimtxt], centers=(1, 3, 4))
    r += 1
wsL.freeze_panes = "A2"
wsL.auto_filter.ref = f"A1:F{r-1}"

# ---------- 主题总览 ----------
wsA = wb.create_sheet("主题总览")
header(wsA, ["主题序号", "一级主题域", "测评主题", "出题风格", "题数", "维度数", "分数段数"],
       [9, 12, 26, 11, 8, 8, 10])
r = 2
for tid in sorted(plan):
    d = data[tid]
    nb = sum(len(x["bands"]) for x in d["dimensions"])
    put(wsA, r, [tid, plan[tid]["domain"], plan[tid]["name"], plan[tid]["style"],
                 f"=COUNTIF(题目明细!$A:$A,A{r})",
                 f"=COUNTIF(维度设置!$A:$A,A{r})",
                 f"=COUNTIF(分数段分析!$A:$A,A{r})"], centers=(1, 4, 5, 6, 7))
    r += 1
wsA.freeze_panes = "A2"
wsA.auto_filter.ref = f"A1:G{r-1}"

# ---------- 题目明细 ----------
wsB = wb.create_sheet("题目明细")
header(wsB, ["主题序号", "一级主题域", "测评主题", "题号", "题干", "题型", "维度代码", "维度名称",
             "选项A文本", "A分值", "选项B文本", "B分值", "选项C文本", "C分值", "选项D文本", "D分值",
             "选项E文本", "E分值", "题目满分", "题目最低分"],
       [9, 10, 20, 6, 40, 7, 8, 12, 22, 6, 22, 6, 22, 6, 22, 6, 22, 6, 8, 8])
r = 2
for tid in sorted(plan):
    d = data[tid]
    dimname = {x["code"]: x["name"] for x in d["dimensions"]}
    for q in d["questions"]:
        opts = q["options"]
        row = [tid, plan[tid]["domain"], plan[tid]["name"], q["no"], q["text"], q["type"],
               q["dim"], dimname[q["dim"]]]
        for k in range(5):
            row += ([opts[k]["text"], opts[k]["score"]] if k < len(opts) else [None, None])
        e5 = f",R{r}" if len(opts) == 5 else ""
        row += [f"=MAX(J{r},L{r},N{r},P{r}{e5})", f"=MIN(J{r},L{r},N{r},P{r}{e5})"]
        put(wsB, r, row, centers=(1, 4, 6, 7, 10, 12, 14, 16, 18, 19, 20))
        r += 1
wsB.freeze_panes = "E2"
wsB.auto_filter.ref = f"A1:T{r-1}"

# ---------- 维度设置 ----------
wsC = wb.create_sheet("维度设置")
header(wsC, ["主题序号", "测评主题", "维度代码", "维度名称", "维度说明", "题目数",
             "包含题号", "维度最低分", "维度总分"],
       [9, 22, 8, 14, 44, 8, 24, 10, 10])
r = 2
for tid in sorted(plan):
    d = data[tid]
    for x in d["dimensions"]:
        nos = [q["no"] for q in d["questions"] if q["dim"] == x["code"]]
        put(wsC, r, [tid, plan[tid]["name"], x["code"], x["name"], x["desc"],
                     f"=COUNTIFS(题目明细!$A:$A,A{r},题目明细!$G:$G,C{r})",
                     "、".join(str(n) for n in nos),
                     f"=SUMIFS(题目明细!$T:$T,题目明细!$A:$A,A{r},题目明细!$G:$G,C{r})",
                     f"=SUMIFS(题目明细!$S:$S,题目明细!$A:$A,A{r},题目明细!$G:$G,C{r})"],
                 centers=(1, 3, 6, 8, 9))
        r += 1
wsC.freeze_panes = "A2"
wsC.auto_filter.ref = f"A1:I{r-1}"

# ---------- 分数段分析 ----------
wsD = wb.create_sheet("分数段分析")
header(wsD, ["主题序号", "测评主题", "维度代码", "维度名称", "分数段", "下限", "上限", "评级", "分析", "建议"],
       [9, 22, 8, 14, 8, 7, 7, 10, 48, 48])
r = 2
for tid in sorted(plan):
    d = data[tid]
    for x in d["dimensions"]:
        for bi, bd in enumerate(x["bands"], 1):
            put(wsD, r, [tid, plan[tid]["name"], x["code"], x["name"], f"第{bi}段",
                         bd["min"], bd["max"], bd["level"], bd["analysis"], bd["advice"]],
                 centers=(1, 5, 6, 7, 8))
            r += 1
wsD.freeze_panes = "A2"
wsD.auto_filter.ref = f"A1:J{r-1}"

out = "psyctest_学习力测评题目与维度.xlsx"
wb.save(out)
nd = sum(len(d["dimensions"]) for d in data.values())
nb = sum(len(x["bands"]) for d in data.values() for x in d["dimensions"])
print(f"已生成 {out}: 题目 {total_q} 行 / 维度 {nd} 行 / 分数段 {nb} 行")
