# -*- coding: utf-8 -*-
"""按用户权威表重建【文件级】地区映射。
输出 file_region.json = { 文件名: 地区包 or None }
None = 跨地区共享 / 不属于任一DOT 地区（DOT_generic / PRI / KNA / MHL 等）
"""
import json, os, re, sys
from collections import Counter, defaultdict

STG = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8")

T2P = json.load(open(os.path.join(STG, "tag2pack.json"), encoding="utf-8"))
items = json.load(open(os.path.join(STG, "full_items.json"), encoding="utf-8"))["items"]

# NDK(诺德克莱因) 有独立 400sprite 图标包且 focus id 全为 NDK_* → 视为独立地区
T2P.setdefault("NDK", "NDK")

# 文件名 → tag。特殊写法先剥掉 New 前缀 / v1 后缀
def tag_of(fn):
    stem = fn[:-4] if fn.lower().endswith(".txt") else fn
    head = stem.split("_")[0]
    for pre in ("New",):
        if head.startswith(pre) and head[len(pre):] in T2P:
            head = head[len(pre):]
    # RAGv1 → RAG
    m = re.match(r"^([A-Z]{3})v\d+$", head)
    if m and m.group(1) in T2P:
        head = m.group(1)
    return head

# 共享/无地区文件：文件名本身就是 DOT_generic 之类
SHARED = {  # 不属于任何 DOT 地区，保持原样
    "DOT_generic.txt",       # 通用国策（原版 effort体系）
    "Faction_Help.txt",      # 阵营帮助（跨地区）
    "_manpower.txt",         # 人力（通用）
    "PRI_ideas.txt", "PRI_Focus.txt", "PRI_Focus_II.txt",   # 天理，表中"无 DOT 归属"
}

# GFS_FocusTree_00 的 country 块 = FAV/LAW/SPI/DVA → 全蒙德
# KNA(坎纳斯) / MHL(丘丘部落) / KQP(丘丘人解放战线)：用户 2026-10-05 确认丘丘人归蒙德；
# KQP 的 allowed 条件是 tag = KQP 或 tag = LYY → 璃月
OVERRIDE = {"GFS_FocusTree_00.txt": "MOT", "WholeMOT_ideas.txt": "MOT",
            "KNA_focus.txt": "MOT", "KNA_ideas.txt": "MOT", "MHL_Focus.txt": "MOT",
            "KQP_ideas.txt": "LYY"}

fr = {}
cnt = Counter()
for it in items:
    fn = it["file"]
    if fn in fr:
        cnt[(it["kind"], fr[fn])] += 1
        continue
    if fn in SHARED:
        home = None
    elif fn in OVERRIDE:
        home = OVERRIDE[fn]
    else:
        t = tag_of(fn)
        home = T2P.get(t)
        if home is None:
            print("  [未覆盖] %-32s tag=%s kind=%s" % (fn, t, it["kind"]))
    fr[fn] = home
    cnt[(it["kind"], home)] += 1

json.dump(fr, open(os.path.join(STG, "file_region.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("\n=== 文件 -> 地区 ===")
by = defaultdict(list)
for fn, h in sorted(fr.items()):
    by[h].append(fn)
for h in sorted(by, key=lambda x: (x is None, x)):
    print(" ", h, ":", " ".join(by[h]))

print("\n=== 容量核算（每文件条目数 vs 本区池额度）===")
# 每包 focus/idea sprite 数
pool = Counter()
for n in json.load(open(os.path.join(STG, "full_items.json"), encoding="utf-8"))["DOT"]:
    kind = "focus" if n.startswith("GFX_goal_") else "idea"
    pool[(n.split("_")[2], kind)] += 1

fcount = Counter(); icount = Counter()
for it in items:
    (fcount if it["kind"] == "focus" else icount)[(fr[it["file"]], it["file"])] += 1

bad = []
for kind, ctr in (("focus", fcount), ("idea", icount)):
    for (h, fn), n in ctr.items():
        if h is None:
            continue
        cap = pool.get((h, kind), 0) * 2
        flag = "  << 超容量" if n > cap else ""
        if n > cap:
            bad.append((kind, fn, h, n, cap))
print("  超容量文件数:", len(bad))
for b in bad:
    print("   ", b)

print("\n=== 各地区总需求 vs 地区总额度（仅参考）===")
agg = Counter()
for kind, ctr in (("focus", fcount), ("idea", icount)):
    for (h, fn), n in ctr.items():
        agg[(kind, h)] += n
for (kind, h), n in sorted(agg.items(), key=lambda x: (x[0][0], x[0][1] is None, x[0][1] or "")):
    if h is None:
        print("  %-6s %-6s %5d  (跨地区，全池可用)" % (kind, h, n))
    else:
        cap = pool.get((h, kind), 0) * 2
        print("  %-6s %-6s %5d/ %4d" % (kind, h, n, cap))
