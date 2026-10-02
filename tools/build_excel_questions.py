# -*- coding: utf-8 -*-
"""汇总391个问卷JSON -> psyctest_测评题目与维度.xlsx（4张数据表+说明页）"""
import json
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

batches = json.load(open("batches.json", encoding="utf-8"))
plan = {}
for b in batches:
    for t in b:
        plan[t["id"]] = t

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

# ============ 说明页 ============
ws0 = wb.active
ws0.title = "说明"
ws0.sheet_view.showGridLines = False
info = [
    ("赛可心理测试测评主题 · 测评题目与维度设计总表", 14, True),
    ("", 11, False),
    ("覆盖范围：391 个测评主题（与《psyctest_测评主题.xlsx》序号一致），共 10,275 道原创题目", 11, False),
    ("生成时间：2026-10-01；题目为本项目原创设计，未抄录任何真实量表原文", 11, False),
    ("", 11, False),
    ("工作表结构：", 11, True),
    ("  ① 主题总览：每个主题一行（题数、维度数由公式统计）", 11, False),
    ("  ② 题目明细：每道题一行，含题干、题型、所属维度、各选项文本与分值", 11, False),
    ("  ③ 维度设置：每个维度一行，含说明、包含题号、最低分/总分（公式汇总）", 11, False),
    ("  ④ 分数段分析：每个维度 3-5 个分数段，含评级、分析解读与建议", 11, False),
    ("", 11, False),
    ("计分口径：", 11, True),
    ("  · 单选题：得分为所选选项的分值。情景/趣味类单选 4-5 个选项分值为 1..n 的排列；", 11, False),
    ("  · 频率自评类单选：选项固定 从不/偶尔/经常/总是（1-4 分），反向陈述题分值 4/3/2/1；", 11, False),
    ("  · 多选题（题干注明）：得分为所选选项分值之和（0/1/2 分制，选得越多分越高）；", 11, False),
    ("  · 知识问答类：单选/多选正确项 1 分、错误项 0 分，维度分即答对题数；", 11, False),
    ("  · 维度得分 = 该维度所有题目得分之和；维度得分范围为《维度设置》中的最低分~总分；", 11, False),
    ("  · 题目满分/最低分、维度题数/最低分/总分均由工作表内公式自动汇总，改动分值后自动重算。", 11, False),
    ("", 11, False),
    ("分数段口径：每维度 3-5 段，区间连续无缝覆盖[最低分,总分]；知识类固定 不及格/及格/良好/优秀。", 11, False),
    ("", 11, False),
    ("使用提示：心理健康类主题的分析与建议均为非诊断表述，仅供自我探索与工具设计参考；", 11, False),
    ("如需用于筛查场景，建议由专业人士复核分数段解读后再上线。", 11, False),
]
for i, (txt, size, bold) in enumerate(info, 1):
    c = ws0.cell(row=i, column=1, value=txt)
    c.font = Font(name="微软雅黑", size=size, bold=bold)
ws0.column_dimensions["A"].width = 100

# ============ 主题总览 ============
wsA = wb.create_sheet("主题总览")
header(wsA,
       ["主题序号", "一级主题域", "测评主题", "出题风格", "题数", "维度数", "分数段数"],
       [9, 15, 26, 11, 8, 8, 10])
r = 2
for tid in sorted(plan):
    d = json.load(open(f"questions/{tid:03d}.json", encoding="utf-8"))
    nb = sum(len(x["bands"]) for x in d["dimensions"])
    put(wsA, r, [tid, plan[tid]["domain"], plan[tid]["name"], plan[tid]["style"],
                 f"=COUNTIF(题目明细!$A:$A,A{r})",
                 f"=COUNTIF(维度设置!$A:$A,A{r})",
                 f"=COUNTIF(分数段分析!$A:$A,A{r})"], centers=(1, 4, 5, 6, 7))
    r += 1
wsA.freeze_panes = "A2"
wsA.auto_filter.ref = f"A1:G{r-1}"

# ============ 题目明细 ============
wsB = wb.create_sheet("题目明细")
header(wsB,
       ["主题序号", "一级主题域", "测评主题", "题号", "题干", "题型", "维度代码", "维度名称",
        "选项A文本", "A分值", "选项B文本", "B分值", "选项C文本", "C分值", "选项D文本", "D分值",
        "选项E文本", "E分值", "题目满分", "题目最低分"],
       [9, 13, 22, 6, 40, 7, 8, 12, 22, 6, 22, 6, 22, 6, 22, 6, 22, 6, 8, 8])
r = 2
for tid in sorted(plan):
    d = json.load(open(f"questions/{tid:03d}.json", encoding="utf-8"))
    dimname = {x["code"]: x["name"] for x in d["dimensions"]}
    for q in d["questions"]:
        opts = q["options"]
        row = [tid, plan[tid]["domain"], plan[tid]["name"], q["no"], q["text"], q["type"],
               q["dim"], dimname[q["dim"]]]
        for k in range(5):
            if k < len(opts):
                row += [opts[k]["text"], opts[k]["score"]]
            else:
                row += [None, None]
        # 满分/最低分公式（E列可空，MAX/MIN 忽略空单元格）
        f_max = f"=MAX(J{r},L{r},N{r},P{r}" + (f",R{r}" if len(opts) == 5 else "") + ")"
        f_min = f"=MIN(J{r},L{r},N{r},P{r}" + (f",R{r}" if len(opts) == 5 else "") + ")"
        row += [f_max, f_min]
        put(wsB, r, row, centers=(1, 4, 6, 7, 10, 12, 14, 16, 18, 19, 20))
        r += 1
wsB.freeze_panes = "E2"
wsB.auto_filter.ref = f"A1:T{r-1}"

# ============ 维度设置 ============
wsC = wb.create_sheet("维度设置")
header(wsC,
       ["主题序号", "测评主题", "维度代码", "维度名称", "维度说明", "题目数",
        "包含题号", "维度最低分", "维度总分"],
       [9, 22, 8, 14, 44, 8, 22, 10, 10])
r = 2
for tid in sorted(plan):
    d = json.load(open(f"questions/{tid:03d}.json", encoding="utf-8"))
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

# ============ 分数段分析 ============
wsD = wb.create_sheet("分数段分析")
header(wsD,
       ["主题序号", "测评主题", "维度代码", "维度名称", "分数段", "下限", "上限", "评级", "分析", "建议"],
       [9, 22, 8, 14, 8, 7, 7, 9, 48, 48])
r = 2
for tid in sorted(plan):
    d = json.load(open(f"questions/{tid:03d}.json", encoding="utf-8"))
    dimname = {x["code"]: x["name"] for x in d["dimensions"]}
    for x in d["dimensions"]:
        for bi, bd in enumerate(x["bands"], 1):
            put(wsD, r, [tid, plan[tid]["name"], x["code"], x["name"], f"第{bi}段",
                         bd["min"], bd["max"], bd["level"], bd["analysis"], bd["advice"]],
                 centers=(1, 5, 6, 7, 8))
            r += 1
wsD.freeze_panes = "A2"
wsD.auto_filter.ref = f"A1:J{r-1}"

out = "psyctest_测评题目与维度.xlsx"
wb.save(out)
print("已生成", out, "题目行", r - 1)
