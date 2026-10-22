# -*- coding: utf-8 -*-
"""最终分配 v10 —— 地区正确 + 单文件内每图≤2 次 + 语义优先
硬约束：
  H1 地区正确：有地区归属的文件，只用本地区 DOT 包的 sprite（NDK 视为独立地区）
  H2 单文件内每个 sprite 最多用 2 次
  H3 只用 8 个 DOT 包内 sprite（有真实定义）
  H4 idea 只用 GFX_idea_ 类；focus 只用 GFX_goal_ 类
  H5 无地区归属的文件（DOT_generic / PRI / KNA / MHL / DOT_* 通用 idea）→ 不动
软目标：语义匹配 —— 用 ctxmap.json 的 focus id / idea 块名 + 本地化中文名打分
"""
import os, re, json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")

STG = os.path.dirname(os.path.abspath(__file__))
MAXUSE_IN_FILE = 2
MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
FDIR = os.path.join(MOD, "common", "national_focus")
IDIR = os.path.join(MOD, "common", "ideas")
PACKS = ("MOT", "INA", "LYY", "FON", "NAT", "NDK", "SNE", "SUM")

ZH = json.load(open(os.path.join(STG, "word_zh_all.json"), encoding="utf-8"))
EXACT = ZH.get("exact", {}); LOWER = ZH.get("lower", {})
LOC = json.load(open(os.path.join(STG, "loc.json"), encoding="utf-8"))
FR = json.load(open(os.path.join(STG, "file_region.json"), encoding="utf-8"))
CTXMAP = json.load(open(os.path.join(STG, "ctxmap.json"), encoding="utf-8"))

STOP = set("the a an of and or to in for on with de la le du is are be".split())

# ---------- 池 ----------
POOL = {}
for p in PACKS:
    POOL[("focus", p)] = []
    POOL[("idea", p)] = []
KINDMAP = {"goal": "focus", "idea": "idea"}
for p in PACKS:
    fp = os.path.join(STG, "DOT_Icons_%s.gfx" % p)
    if not os.path.exists(fp):
        print("!! 缺 %s" % fp); continue
    s = open(fp, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r'name\s*=\s*"(GFX_(goal|idea)_%s_[^"]+)"' % p, s):
        if "_shine" in m.group(0): continue
        POOL[(KINDMAP[m.group(2)], p)].append(m.group(1))
for k in POOL: POOL[k] = sorted(set(POOL[k]))
print("池规模: focus=%d idea=%d" % (len(POOL[("focus", "MOT")]), len(POOL[("idea", "MOT")])))

# ---------- 语义工具 ----------
def en2zh(w):
    return EXACT.get(w) or LOWER.get(w.lower())

def zh_grams(zh_text):
    """中文文本 → 2-gram 集合（去标点）"""
    t = re.sub(r'[^\w\u4e00-\u9fff]', '', zh_text or "")
    if not t: return set()
    if len(t) == 1: return {t}
    return {t[i:i+2] for i in range(len(t)-1)}

def sprite_zh(name):
    """sprite 名 → 中文语义串（英文逐词译名拼接）"""
    rest = name
    m = re.match(r'^(?:GFX_)?(?:goal|idea)_(?:[A-Za-z]+_)*?([A-Z][A-Z0-9]*[A-Z0-9])_(.+)$', name)
    if m: rest = m.group(2)
    else:
        m2 = re.match(r'^(?:GFX_)?(?:goal|idea)_(.+)$', name)
        if m2: rest = m2.group(1)
    out = []
    for w in [x for x in rest.split("_") if x]:
        if w.isdigit() or len(w) <= 1: continue
        z = en2zh(w)
        if not z: continue
        for t in re.split(r"[、,，/\s]+", z):
            t = t.strip()
            if t and t.lower() not in STOP: out.append(t)
    return "".join(out)

def sprite_grams(name):
    z = sprite_zh(name)
    if z: return zh_grams(z)
    # 译不出中文 → 用英文词的 3-gram 兜底
    t = re.sub(r'[^A-Za-z]', '', name.lower())
    return {t[i:i+3] for i in range(0, max(1, len(t)-2))} if t else set()

def focus_zhgrams(ctx):
    """focus/idea id → 中文语义 grams（本地化中文名优先，英文 id 逐词译兜底）"""
    if not ctx: return set()
    zh = en2zh(ctx)
    loc = LOC.get(ctx)
    parts = []
    if loc and loc[0]: parts.append(loc[0])
    elif zh: parts.append(zh)
    rest = re.sub(r'^[A-Za-z]+[0-9]*_', '', ctx)
    for w in [x for x in rest.split("_") if x and not x.isdigit()]:
        z = en2zh(w)
        if z: parts.append(z)
    g = set()
    for p in parts: g |= zh_grams(p)
    return g

def focus_descgrams(ctx):
    """id_desc 的中文描述 grams —— 只用于概念桥接，帮助消歧"""
    if not ctx: return set()
    e = LOC.get(ctx + "_desc")
    if not e or not e[0]: return set()
    return zh_grams(e[0][:80])

CONCEPT = {
 "经济": "贸易 商业 财富 市场 税收 金融 财政 产业 经济 通商 商会 银行 钱",
 "生产": "产能 产量 产出 制造 工艺 工业 作坊 工厂 生产 冶铁 锻造 铸造",
 "军事": "军队 士兵 武器 战争 作战 部队 兵团 军事 将领 练兵 征兵 军备",
 "外交": "外交 条约 同盟 谈判 关系 使节 协定 拜访 和平 友谊 结盟",
 "内政": "政务 治理 行政 吏治 治安 秩序 建设 基建 市政 改革 廉政 官僚",
 "科技": "研究 科研 技术 发明 学院 学术 教育 科技 实验 学者 智慧 知识",
 "工业": "工厂 工业 制造 生产 车间 产业 流水线 锻造 机械 采矿 矿",
 "农业": "农业 农场 种植 丰收 农作物 粮 水利 灌溉 屯田 渔业 田",
 "集权": "统率 指挥 中枢 执政 政务 议事 议会 治理 秩序 法令 集权 中央 权威 皇权",
 "民族": "民族 族群 文化 传统 习俗 血统 认同 身份 团结 同族 民俗",
 "海军": "海军 舰队 海战 航海 舰船 水军 港口 远航 海运 船",
 "空军": "空军 飞行 航空 制空 战机 翱翔 空袭 飞",
 "贸易": "贸易 通商 商会 港口 远航 货物 商路 互市 关税 买卖",
 "革命": "革命 起义 暴动 反抗 颠覆 斗争 共和 抗争 运动",
 "教育": "教育 学校 学院 学术 研究 人才 知识 培养 书籍 图书馆 书",
 "工程": "工程 建设 基建 水利 桥梁 道路 设施 营造 施工 修理 修缮",
 "医疗": "医疗 医生 药物 治病 医院 卫生 健康 疫病 瘟疫",
 "司法": "司法 法院 审判 法律 法令 犯罪 治安 监狱 律法 律令",
 "税收": "税收 财政 税务 国库 预算 金币 关税 钱 财",
 "军工": "军工 兵工厂 军备 武器 装备 部队 现代化 军械",
 "水利": "水利 灌溉 水渠 河道 治水 水坝 沟渠",
 "铁路": "铁路 火车 轨道 列车 运输 车站 机车",
 "商贸": "商贸 商路 商业 贸易 集市 商会 税",
 "粮食": "粮食 补给 军粮 民用 消费 物资 后勤",
 "人口": "人口 生育 户口 移民 劳动力 兵源 征召",
 "海军基地": "海军 军港 舰队 造船 舰船 基地",
}
CONCEPT_G = {k: zh_grams(v) for k, v in CONCEPT.items()}

def bridge(g):
    out = set(g)
    for k, cg in CONCEPT_G.items():
        if cg & g:
            out |= cg
    return out

def sc(a, b):
    if not a or not b: return 0.0
    i = a & b
    if not i: return 0.0
    return 0.70*len(i)/len(a) + 0.30*len(i)/len(a|b)

# 打分下限：只要有 1 个 2-gram 命中就算候选（而不是要求 0.02 的比例）
MIN_HIT = 0.0001
def has_hit(a, b):
    return bool(a) and bool(b) and bool(a & b)

def cands_ok(qg, pg):
    """标题 grams 在池里能否找到任何可用候选"""
    if not qg: return False
    for j in range(len(pg)):
        if has_hit(qg, pg[j]): return True
    return False

# ---------- 收集条目 ----------
def collect(d, kind):
    out = collections.defaultdict(list)
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".txt"): continue
        raw = open(os.path.join(d, fn), encoding="utf-8", errors="ignore", newline='').read().split("\n")
        cm = CTXMAP.get("%s/%s" % (kind, fn), {})
        for i, ln in enumerate(raw, 1):
            m = re.match(r'^(\s*(?:icon|picture)\s*=\s*)(\S+?)(\s*)\r?$', ln)
            if not m: continue
            out[fn].append({"line": i, "old": m.group(2), "ctx": cm.get(str(i), "")})
    return out

F = collect(FDIR, "focus"); I = collect(IDIR, "idea")
print("focus 文件 %d 条%d | idea 文件 %d 条 %d" % (
    len(F), sum(len(v) for v in F.values()), len(I), sum(len(v) for v in I.values())))

# 池的语义索引
PG = {k: [sprite_grams(n) for n in v] for k, v in POOL.items()}
print("池语义索引完成")

# ---------- 逐文件分配 ----------
plan = []
stats = collections.Counter()
skipped = []
for kind, tree in (("focus", F), ("idea", I)):
    for fn, lst in sorted(tree.items()):
        home = FR.get(fn)
        if not home or home not in PACKS:
            skipped.append((kind, fn, len(lst))); continue
        pool = POOL[(kind, home)]; pg = PG[(kind, home)]
        if not pool:
            skipped.append((kind, fn, len(lst))); continue
        cands = []
        for it in lst:
            qg = focus_zhgrams(it["ctx"])
            if not qg: qg = sprite_grams(it["old"])
            # 概念桥接：仅扩展标题本身，不混入 desc
            qb = bridge(qg) if qg else set()
            # 描述只在「标题完全找不到候选」时启用
            dg = focus_descgrams(it["ctx"]) if not cands_ok(qg, pg) else set()
            qd = (bridge(dg | qg) if dg else set())
            lst_sc = []
            for j in range(len(pool)):
                s = sc(qg, pg[j]) if qg else 0.0
                if has_hit(qg, pg[j]): lst_sc.append((s, 0, j))
                elif has_hit(qb, pg[j]):
                    lst_sc.append((sc(qb, pg[j]) * 0.85, 1, j))
                elif has_hit(qd, pg[j]):
                    lst_sc.append((sc(qd, pg[j]) * 0.75, 2, j))
            lst_sc.sort(reverse=True)
            cands.append(lst_sc[:120])
        used = collections.Counter(); got = {}
        flat = sorted([(-s, mode, i, j) for i, l in enumerate(cands) for s, mode, j in l])
        for negs, mode, i, j in flat:
            if i in got: continue
            n = pool[j]
            if used[n] >= MAXUSE_IN_FILE: continue
            used[n] += 1; got[i] = (n, -negs, "literal" if mode == 0 else "concept")
        for i in range(len(lst)):
            if i in got: continue
            it = lst[i]; pick = None; pk = 0.0; pmode = "same_region"
            # ① 原 sprite 仍在本区且未满额 → 保留
            if it["old"] in pool and used[it["old"]] < MAXUSE_IN_FILE:
                pick = it["old"]; pmode = "keep"
            # ② 回退到该条自己的候选列表，取未满额的最高分（关键：保住语义）
            if pick is None:
                for s, mode, j in cands[i]:
                    n = pool[j]
                    if used[n] < MAXUSE_IN_FILE:
                        pick = n; pk = s; pmode = "literal" if mode == 0 else "concept"; break
            # ③ 候选全满 → 该区池额度确实不够，取未满额里跟语义最接近的（重算全池）
            if pick is None:
                qg = focus_zhgrams(it["ctx"])
                qb = bridge(qg) if qg else set()
                if not qb: qb = sprite_grams(it["old"])
                best = None; bs = MIN_HIT
                for n, g in zip(pool, pg):
                    if used[n] >= MAXUSE_IN_FILE: continue
                    s = sc(qb, g)
                    if s > bs: bs = s; best = n
                if best is None:
                    for n in pool:
                        if used[n] < MAXUSE_IN_FILE: best = n; break
                pick = best; pk = bs; pmode = "concept_fb"
            if pick is None:
                stats["pool_exhausted"] += 1; continue
            used[pick] += 1
            got[i] = (pick, pk, pmode)
        for i, it in enumerate(lst):
            if i not in got: continue
            n, s, mode = got[i]
            if n != it["old"]:
                plan.append({"kind": kind, "file": fn, "line": it["line"],
                             "old": it["old"], "new": n, "score": round(s, 4),
                             "mode": mode, "home": home, "ctx": it["ctx"]})
            stats["mode_" + mode] += 1

print("\n=== 分配完成 ===")
print("变更条目: %d" % len(plan))
print("方式: %s" % {k[5:]: v for k, v in stats.items() if k.startswith("mode_")})
print("池耗尽: %d" % stats["pool_exhausted"])
print("跳过(无地区归属) %d 个文件:" % len(skipped))
for k, f, n in skipped: print("    %s/%-32s %d 条" % (k, f, n))

plan.sort(key=lambda x: (x["kind"], x["file"], x["line"]))
json.dump(plan, open(os.path.join(STG, "plan_v10.json"), "w", encoding="utf-8"), ensure_ascii=False)

# ---------- 校验（按最终结果全量复核，不是只看 plan）----------
print("\n=== 校验（全量最终态）===")
final = {}
for kind, tree in (("focus", F), ("idea", I)):
    for fn, lst in tree.items():
        for it in lst:
            key = (kind, fn, it["line"])
            new = next((x["new"] for x in plan if x["kind"] == kind and x["file"] == fn
                        and x["line"] == it["line"]), it["old"])
            final[key] = new
byfile = collections.defaultdict(collections.Counter)
for (kind, fn, ln), n in final.items():
    byfile[(kind, fn)][n] += 1
over = [(k, n, v) for k, c in byfile.items() for n, v in c.items() if v > MAXUSE_IN_FILE]
print("单文件内复用>2 的 sprite: %d" % len(over))
for o in over[:10]: print("   ", o)
allpool = set(sum(POOL.values(), []))
print("最终 sprite 不在 DOT 池: %d" % sum(1 for v in final.values() if v not in allpool))
badreg = 0
for (kind, fn, ln), v in final.items():
    h = FR.get(fn)
    if h and h in PACKS and ("_%s_" % h) not in v: badreg += 1
print("地区错配: %d" % badreg)
badkind = 0
for (kind, fn, ln), v in final.items():
    if kind == "idea" and not v.startswith("GFX_idea_"): badkind += 1
    if kind == "focus" and not v.startswith("GFX_goal_"): badkind += 1
print("种类错配(idea用goal类/focus用idea类): %d" % badkind)
sem = [x["score"] for x in plan if x["mode"] in ("literal", "concept")]
if sem:
    print("语义分配 %d 条, 平均分 %.4f, >0.3 的 %d 条" % (len(sem), sum(sem)/len(sem), sum(1 for s in sem if s > 0.3)))
