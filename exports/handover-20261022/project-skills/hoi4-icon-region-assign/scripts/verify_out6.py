# -*- coding: utf-8 -*-
"""out6 最终验收：按用户口径（单文件内每 sprite ≤2）严格校验"""
import os, re, json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
STG = os.path.dirname(os.path.abspath(__file__))
MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
OUT = os.path.join(STG, "out6")
BAK = os.path.join(STG, "backup_v10")
PACKS = ("MOT","INA","LYY","FON","NAT","NDK","SNE","SUM")
FR = json.load(open(os.path.join(STG, "file_region.json"), encoding="utf-8"))

# DOT 池
POOL = set()
for p in PACKS:
    s = open(os.path.join(STG, "DOT_Icons_%s.gfx" % p), encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r'name\s*=\s*"(GFX_[^"]+)"', s):
        if "_shine" not in m.group(1): POOL.add(m.group(1))

# MOD+原版 defined
defined = set()
for root in (MOD, r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"):
    for dp, dn, fn in os.walk(root):
        if any(x in dp for x in (".backups", "备份文件BY Ruka")): continue
        for f in fn:
            if not f.endswith(".gfx"): continue
            try: s = open(os.path.join(dp, f), encoding="utf-8", errors="ignore").read()
            except Exception: continue
            for m in re.finditer(r'name\s*=\s*"([^"]+)"', s): defined.add(m.group(1))

ICON = re.compile(r'^\s*(icon|picture)\s*=\s*(\S+?)\s*\r?$')

print("=== out6 最终验收 ===")
per_file = collections.defaultdict(collections.Counter)
kindmix = collections.Counter(); unk = 0; und = 0; outside = 0
region_bad = 0; kind_bad = 0; n = 0
for f in sorted(os.listdir(OUT)):
    kind, _, fn = f.partition("__")
    raw = open(os.path.join(OUT, f), encoding="utf-8", errors="ignore", newline='').read().split("\n")
    h = FR.get(fn)
    for i, ln in enumerate(raw, 1):
        m = ICON.match(ln)
        if not m: continue
        v = m.group(2); n += 1
        kindmix[(kind, v.split("_")[1] if v.startswith("GFX_") else "other")] += 1
        if not v or "unknown" in v.lower(): unk += 1; continue
        if v not in defined: und += 1
        if v not in POOL: outside += 1
        per_file[f][v] += 1
        if h and h in PACKS and ("_%s_" % h) not in v: region_bad += 1
        if kind == "idea" and not v.startswith("GFX_idea_"): kind_bad += 1
        if kind == "focus" and not v.startswith("GFX_goal_"): kind_bad += 1

print("条目总数: %d" % n)
print("unknown/空          : %d" % unk)
print("真·未定义           : %d" % und)
print("不在 DOT 池(原版图标): %d  (保持不动，非本次范围)" % outside)
print("地区错配            : %d" % region_bad)
print("种类错配            : %d  (原版 focus 可用 idea 类，MOD 现有 298 例即合法)" % kind_bad)

over = {f: {k: v for k, v in c.items() if v > 2} for f, c in per_file.items()}
over = {f: c for f, c in over.items() if c}
print("\n★ 单文件内每 sprite >2 次: %d 个文件" % len(over))
for f, c in sorted(over.items(), key=lambda x: -max(x[1].values()))[:10]:
    print("   %-36s 最重 %s=%d" % (f, max(c, key=c.get), max(c.values())))

print("\n=== 复用分布（单文件内）===")
b = collections.Counter()
for f, c in per_file.items():
    for v, k in c.items(): b[min(k, 6)] += 1
for k in sorted(b):
    print("   单文件内用 %d 次: %d 个 (文件,sprite) 组合" % (k if k < 6 else "6+", b[k]))

print("\n=== 用户点名项（原为大规模重复）===")
for t in ("SAN", "LYY", "NAT", "GUN", "MOT"):
    mx = 0; where = ""
    for f, c in per_file.items():
        for v, k in c.items():
            if "_%s_" % t in v and k > mx: mx = k; where = "%s/%s" % (f, v)
    print("   %-4s 包内单文件最高复用: %d  %s" % (t, mx, where))

print("\n=== diff 复核 ===")
viol = 0; unbal = 0
for f in sorted(os.listdir(OUT)):
    bp = os.path.join(BAK, f)
    if not os.path.isfile(bp): continue
    a = open(bp, encoding="utf-8", errors="ignore", newline='').read()
    b = open(os.path.join(OUT, f), encoding="utf-8", errors="ignore", newline='').read()
    if len(a.split("\n")) != len(b.split("\n")): viol += 1; continue
    for x, y in zip(a.split("\n"), b.split("\n")):
        if x == y: continue
        if ("icon" in x or "picture" in x) and ("icon" in y or "picture" in y):
            if x.split("=")[0].strip() != y.split("=")[0].strip(): viol += 1
        else: viol += 1
    if (a.count("{") - a.count("}")) != (b.count("{") - b.count("}")): unbal += 1
print("   非 icon/picture 行改动 : %d" % viol)
print("   括号深度变化: %d" % unbal)
