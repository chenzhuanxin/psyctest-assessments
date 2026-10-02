# -*- coding: utf-8 -*-
"""读取主题Excel -> 计算每个主题的出题数与风格 -> 生成批次清单 batches.json"""
import json, math
from openpyxl import load_workbook

wb = load_workbook("psyctest_测评主题.xlsx", data_only=False)
ws = wb["测评主题"]
themes = []
for r in ws.iter_rows(min_row=2, values_only=True):
    themes.append({"id": r[0], "domain": r[1], "name": r[2], "desc": r[3], "matches": r[4]})
assert len(themes) == 391, len(themes)

# 出题数基准（按一级域）
BASE = {
    "人格与个性": 28, "恋爱与亲密关系": 30, "婚姻与家庭": 28, "人际与社交": 28,
    "职场与事业": 28, "心理健康": 25, "情绪与压力管理": 24, "认知与能力": 22,
    "自我成长与人生观": 26, "金钱与财富": 22, "性与性别心理": 22,
    "亲子儿童与青少年": 18, "知识与趣味娱乐": 22, "投射与潜意识": 18,
}
# 风格默认（按一级域）
STYLE = {
    "人格与个性": "情景选择", "恋爱与亲密关系": "情景选择", "婚姻与家庭": "情景选择",
    "人际与社交": "情景选择", "职场与事业": "情景选择", "心理健康": "频率自评",
    "情绪与压力管理": "频率自评", "认知与能力": "频率自评", "自我成长与人生观": "情景选择",
    "金钱与财富": "情景选择", "性与性别心理": "情景选择", "亲子儿童与青少年": "频率自评",
    "知识与趣味娱乐": "知识问答", "投射与潜意识": "轻松趣味",
}
# 知识问答主题（有正确答案）
KNOWLEDGE = {"智商（IQ）","逻辑推理","空间判断力","综合知识储备","语言文学素养","数字敏感度",
             "记忆力","城市知识系列","百科精英挑战","影视知识（哈利波特/怪奇物语）","科幻名著知识（三体）",
             "明星粉丝等级","历史名人知识","游戏角色趣味（王者荣耀）"}
# 轻松趣味主题（非知识类的娱乐向）
FUN = {"运势预测","前世今生与轮回","灵异奇幻趣味","沙雕搞怪指数","吃货等级与美食趣味",
       "穿搭外貌趣味","宠物萌宠趣味","季节天气趣味","社交平台趣味","音乐乐器人格",
       "图片投射测试","情境假设投射","TAT主题统觉测验"}
# 旗舰主题出题数覆盖
OVERRIDE = {
    "MBTI 16型人格": 88, "大五人格（Big Five）": 60, "九型人格": 60, "艾森克人格EPQ": 60,
    "卡特尔16PF人格因素": 60, "DISC行为风格": 48, "FPA性格色彩": 40, "菲尔人格测试": 20,
    "霍兰德职业兴趣（RIASEC）": 60, "职业价值观": 40, "职业锚定位": 40, "一般职业能力（GATB）": 48,
    "PHQ-9抑郁筛查": 20, "SDS抑郁自评量表": 24, "贝克抑郁量表（BDI）": 26, "汉密尔顿抑郁量表（HAMD）": 20,
    "QIDS快速抑郁筛查": 18, "伯恩斯抑郁清单（BDC）": 18, "产后抑郁（EPDS）": 18, "老年抑郁（GDS）": 18,
    "焦虑自评（SAS）": 24, "广泛性焦虑（GAD-7）": 18, "考试焦虑（TAS）": 24, "恐惧症筛查": 20,
    "强迫症筛查（Y-BOCS）": 24, "双相情感障碍筛查（MDQ/YMRS）": 20, "创伤后应激（PTSD）": 20,
    "综合心理筛查（SCL-90）": 60, "DASS-21情绪联合量表": 24, "心情温度计（BSRS-5）": 15,
    "大学生心理健康（UPI）": 30, "中学生心理健康（MSSMHS）": 30, "成人自闭谱系筛查（AQ/RAADS）": 40,
    "成人ADHD筛查（ASRS）": 20, "自恋倾向（NPI/ANS/MNS）": 40, "讨好型人格": 32,
    "情商（EQ）": 40, "智商（IQ）": 30, "创造力": 30, "城市知识系列": 30, "百科精英挑战": 30,
    "性取向（Kinsey等）": 30, "ABO性别气质": 24, "SM倾向（S/M属性）": 30, "BDSM性偏好": 24,
    "儿童行为评估（CBCL）": 24, "儿童自闭筛查（CAST）": 20, "校园欺凌受害": 20,
    "中国大五人格问卷": 40, "情绪稳定性": 30, "心理韧性（CD-RISC）": 25, "自尊水平（SES）": 20,
    "安全感（马斯洛）": 30, "自我效能感（GSES）": 20, "延迟满足": 18, "人生意义感": 18,
    "压力知觉（PSS）": 18, "应对方式（SCSQ）": 20, "生活事件压力": 24, "睡眠与失眠": 22,
    "拖延症": 22, "冲动性（BIS-11）": 22, "手机成瘾": 18, "网络成瘾（IAD）": 20, "游戏成瘾与依赖": 20,
    "饮食态度与暴食（EAT-26）": 22, "孤独感": 22, "害羞与羞怯": 20, "萨提亚沟通姿态": 24,
    "FIRO-B人际关系倾向": 30, "社交恐惧症": 30, "社交焦虑触发因素": 24, "愤怒与易激惹": 24,
    "嫉妒情绪": 18, "羞耻感与羞耻敏感": 22, "内疚感": 16, "自卑心理": 26, "空虚感": 16,
    "心理老化": 16, "更年期自测": 15, "亚健康状态": 16, "脑疲劳与精神疲倦": 16,
    "儿童青少年心理健康（MHS-CA）": 24, "青少年品行障碍筛查": 20, "家长反思功能（PRFQ）": 18,
    "儿童共情力": 16, "儿童抑郁（DSRS-C）": 18, "金钱与财富": 22, "财商水平": 26,
    "投资风险承受力": 26, "炒股心理": 22, "领导力": 35, "管理能力": 35, "团队角色与协作": 30,
    "跳槽与离职决策": 26, "求职与面试": 26, "职场压力与心理疲劳": 24, "工作满意度与倦怠": 24,
    "MBTI维度细分（I/E、S/N、T/F、J/P）": 30, "黑暗三联征/人格黑暗面": 30,
}
NAME_FIX = {"黑暗三联征/人格黑暗面": "人格黑暗面（黑暗三联征）"}

def assign(t):
    n = t["name"]
    n = NAME_FIX.get(n, n)
    if n in OVERRIDE:
        size = OVERRIDE[n]
    else:
        size = BASE[t["domain"]]
        m = t["matches"] or 0
        if m >= 30: size += 6
        elif m >= 15: size += 3
        elif m <= 5: size -= 4
        size = max(15, min(size, 48))
    if n in KNOWLEDGE: style = "知识问答"
    elif n in FUN: style = "轻松趣味"
    else: style = STYLE[t["domain"]]
    # 知识问答主题也压到 15-40
    if style == "知识问答":
        size = max(15, min(size, 40))
    t["size"] = size
    t["style"] = style
    return t

for t in themes: assign(t)

# 批次划分：按域顺序切，每批约11个主题（允许9-13浮动保持同域优先同批）
DOMAIN_ORDER = ["人格与个性","恋爱与亲密关系","婚姻与家庭","人际与社交","职场与事业","心理健康",
                "情绪与压力管理","认知与能力","自我成长与人生观","金钱与财富","性与性别心理",
                "亲子儿童与青少年","知识与趣味娱乐","投射与潜意识"]
batches = []
cur = []
for dom in DOMAIN_ORDER:
    dt = [t for t in themes if t["domain"] == dom]
    for t in dt:
        cur.append(t)
        if len(cur) >= 11:
            batches.append(cur); cur = []
    # 域结束：不足11个的余量留到下一域开头（保证同域尽量同批），若cur>=16则切批
    if len(cur) >= 16:
        batches.append(cur); cur = []
if cur: batches.append(cur)
# 均衡：>400题拆两半；末批<160并入前批
def qsum(b): return sum(t["size"] for t in b)
res = []
for b in batches:
    if qsum(b) > 400:
        half = 0; split_at = 0
        for i, t in enumerate(b):
            half += t["size"]
            if half >= qsum(b) / 2:
                split_at = i + 1; break
        res.append(b[:split_at]); res.append(b[split_at:])
    else:
        res.append(b)
if len(res) >= 2 and qsum(res[-1]) < 160:
    prev = res[-2] + res[-1]
    if qsum(prev) <= 400:
        res = res[:-2] + [prev]
batches = res
# 总题量
total_q = sum(t["size"] for t in themes)
print("主题数:", len(themes), " 批次数:", len(batches), " 预计总题量:", total_q)
print("各批题量:", [sum(t['size'] for t in b) for b in batches])
print("风格分布:", {s: sum(1 for t in themes if t['style']==s) for s in set(t['style'] for t in themes)})
json.dump(batches, open("batches.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("batches.json 已生成")
