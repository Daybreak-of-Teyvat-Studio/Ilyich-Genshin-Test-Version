# -*- coding: utf-8 -*-
"""最终验收：直接扫 MOD 本体（不用 out6）"""
import os, re, json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
STG = os.path.dirname(os.path.abspath(__file__))
MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
PACKS = ("MOT","INA","LYY","FON","NAT","NDK","SNE","SUM")
FR = json.load(open(os.path.join(STG, "file_region.json"), encoding="utf-8"))
DIRS = {"focus": "national_focus", "idea": "ideas"}
ICON = re.compile(r'^\s*(icon|picture)\s*=\s*(\S+?)\s*\r?$')

# DOT 池
POOL = set()
for p in PACKS:
    s = open(os.path.join(STG, "DOT_Icons_%s.gfx" % p), encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r'name\s*=\s*"(GFX_[^"]+)"', s):
        if "_shine" not in m.group(1): POOL.add(m.group(1))
# defined（MOD + 原版）
defined = set()
for root in (MOD, r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"):
    for dp, dn, fn in os.walk(root):
        if any(x in dp for x in (".backups", "备份文件BY Ruka")): continue
        for f in fn:
            if not f.endswith(".gfx"): continue
            try: s = open(os.path.join(dp, f), encoding="utf-8", errors="ignore").read()
            except Exception: continue
            for m in re.finditer(r'name\s*=\s*"([^"]+)"', s): defined.add(m.group(1))

per_file = collections.defaultdict(collections.Counter)
n = 0; unk = 0; und = 0; region_bad = 0; kind_bad = 0
bad_detail = []
srcmix = collections.Counter()
for kind, sub in DIRS.items():
    d = os.path.join(MOD, "common", sub)
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".txt"): continue
        h = FR.get(fn)
        raw = open(os.path.join(d, fn), encoding="utf-8", errors="ignore", newline='').read().split("\n")
        for i, ln in enumerate(raw, 1):
            m = ICON.match(ln)
            if not m: continue
            v = m.group(2); n += 1
            if not v or "unknown" in v.lower(): unk += 1; bad_detail.append(("unknown", kind, fn, i, v)); continue
            if v not in defined: und += 1; bad_detail.append(("未定义", kind, fn, i, v))
            if v in POOL: per_file[(kind, fn)][v] += 1
            if h and h in PACKS and ("_%s_" % h) not in v:
                region_bad += 1; srcmix[(fn, h)] += 1
            if kind == "idea" and v.startswith("GFX_goal_"):
                kind_bad += 1; bad_detail.append(("idea用goal类", kind, fn, i, v))

print("=== MOD 本体最终验收 ===")
print("icon/picture 总条目        : %d" % n)
print("unknown / 空值: %d" % unk)
print("真·未定义                 : %d" % und)
print("★ 地区错配                 : %d" % region_bad)
print("★ idea 误用 GFX_goal_ 类   : %d" % kind_bad)

over = {k: {s: c for s, c in v.items() if c > 2} for k, v in per_file.items()}
over = {k: v for k, v in over.items() if v}
print("★ 单文件内每 sprite >2 次  : %d 个文件" % len(over))
for k, v in sorted(over.items(), key=lambda x: -max(x[1].values()))[:8]:
    print("     %s/%s  最重 %d 次" % (k[0], k[1], max(v.values())))

if region_bad:
    print("\n=== 地区错配明细（按文件）===")
    for (fn, h), c in srcmix.most_common(20): print("   %-34s 应属 %-4s 错配 %d 条" % (fn, h, c))
if bad_detail:
    print("\n=== 其他问题（前20）===")
    for b in bad_detail[:20]: print("   %s  %s/%s:%d  %s" % b)

print("\n=== 用户点名的 idea 文件：地区核对 ===")
for fn in ("RAG_ideas.txt","SGS_ideas.txt","SFS_ideas.txt","SAN_Neo_ideas.txt",
           "VAN_ideas.txt","NAT_Neo_ideas.txt","NDK_ideas.txt","HZH.txt","PBF_ideas.txt"):
    p = os.path.join(MOD, "common", "ideas", fn)
    if not os.path.isfile(p): print("   %-22s (不存在)" % fn); continue
    c = collections.Counter()
    for ln in open(p, encoding="utf-8", errors="ignore", newline='').read().split("\n"):
        m = ICON.match(ln)
        if m and m.group(2) in POOL:
            pm = re.match(r'GFX_(?:goal|idea)_([A-Za-z]+)_', m.group(2))
            c[pm.group(1) if pm else "?"] += 1
    exp = FR.get(fn)
    ok = "OK" if (exp and list(c) == [exp]) else ("跨地区" if len(c) > 1 else "检查")
    print("   %-22s 应属 %-5s 实际 %-22s %s" % (fn, exp, dict(c), ok))
