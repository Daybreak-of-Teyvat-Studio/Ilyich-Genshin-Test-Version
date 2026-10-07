"""把 plan_full 应用到 MOD，生成 out4/，并做全量校验"""
import os, re, json, collections, shutil

MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
STG = r"C:\Users\XIANGZIYUAN\hoi4lint\icon_gen\stage4"
OUT = os.path.join(STG, "out6")
BAK = os.path.join(STG, "backup_v10")
DIRS = {"focus": os.path.join(MOD, "common", "national_focus"),
        "idea":  os.path.join(MOD, "common", "ideas")}

plan = json.load(open(os.path.join(STG, "plan_v10.json"), encoding="utf-8"))
grp = collections.defaultdict(dict)
for x in plan:
    grp[(x["kind"], x["file"])][x["line"]] = x["new"]

if os.path.isdir(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)
if os.path.isdir(BAK): shutil.rmtree(BAK)
os.makedirs(BAK)

nfile = nline = miss = bad = 0
detail = []
for (kind, fn), linemap in sorted(grp.items()):
    src = os.path.join(DIRS[kind], fn)
    if not os.path.isfile(src):
        miss += 1; detail.append("MISSING %s/%s" % (kind, fn)); continue
    shutil.copyfile(src, os.path.join(BAK, "%s__%s" % (kind, fn)))
    content = open(src, encoding="utf-8", errors="ignore", newline='').read()
    raw = content.split("\n")
    cnt = 0
    # 双断言：行号必须仍是一条 icon/picture 行，且当前值与 plan 记录的 old 一致
    planold = {x["line"]: x["old"] for x in plan if x["kind"] == kind and x["file"] == fn}
    for i, line in enumerate(raw, 1):
        if i in linemap:
            newv = linemap[i]
            m = re.match(r'^(\s*(?:icon|picture)\s*=\s*)(\S+)(.*?)(\r?)$', line)
            if not m:
                bad += 1
                detail.append("BADLINE %s/%s:%d %r" % (kind, fn, i, line[:60])); continue
            if m.group(2) != planold.get(i):
                bad += 1
                detail.append("DRIFT %s/%s:%d plan_old=%s file=%s" % (
                    kind, fn, i, planold.get(i), m.group(2))); continue
            raw[i-1] = m.group(1) + newv + m.group(3) + m.group(4)
            cnt += 1
    out = "\n".join(raw)
    with open(os.path.join(OUT, "%s__%s" % (kind, fn)), "w", encoding="utf-8", newline='') as f:
        f.write(out)
    nfile += 1; nline += cnt
    detail.append("%s/%s  改写 %d 行" % (kind, fn, cnt))

print("文件: %d  改写行: %d  缺文件: %d  异常行: %d" % (nfile, nline, miss, bad))

# ---- 校验 out4 ----
items = json.load(open(os.path.join(STG, "full_items.json"), encoding="utf-8"))["items"]
DOT = set(json.load(open(os.path.join(STG, "full_items.json"), encoding="utf-8"))["DOT"])

defined = set()
for dp, dn, fn in os.walk(MOD):
    if any(x in dp for x in (".backups", "备份文件BY Ruka")): continue
    for f in fn:
        if not f.endswith(".gfx"): continue
        try: s = open(os.path.join(dp,f), encoding="utf-8", errors="ignore").read()
        except Exception: continue
        for m in re.finditer(r'name\s*=\s*"([^"]+)"', s): defined.add(m.group(1))
VAN = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
for dp, dn, fn in os.walk(VAN):
    for f in fn:
        if not f.endswith(".gfx"): continue
        try: s = open(os.path.join(dp,f), encoding="utf-8", errors="ignore").read()
        except Exception: continue
        for m in re.finditer(r'name\s*=\s*"([^"]+)"', s): defined.add(m.group(1))

cnt = collections.Counter()
unk = 0; und = 0
for it in items:
    f = os.path.join(OUT, "%s__%s" % (it["kind"], it["file"]))
    if not os.path.isfile(f):
        continue
    raw = open(f, encoding="utf-8", errors="ignore", newline='').read().split("\n")
    ln = it["line"]
    if ln-1 >= len(raw): continue
    m = re.match(r'^(\s*(?:icon|picture)\s*=\s*)(\S+?)(\s*)\r?$', raw[ln-1])
    if not m: continue
    v = m.group(2)
    if not v or "unknown" in v.lower(): unk += 1; continue
    if v not in defined: und += 1; continue
    cnt[v] += 1

over = {k:v for k,v in cnt.items() if v > 2}
print("\n=== out6 校验 ===")
print("统计条目: %d  不同sprite: %d" % (sum(cnt.values()), len(cnt)))
print("unknown/空: %d" % unk)
print("真·未定义: %d" % und)
print("最大复用: %d  超限sprite: %d" % (max(cnt.values()) if cnt else 0, len(over)))
if over:
    for k, v in sorted(over.items(), key=lambda x:-x[1])[:10]:
        print("   %-46s %d" % (k, v))

# ---- 与备份逐行diff：只允许 icon/picture 变 ----
viol = 0; vdetail = []
for f in os.listdir(OUT):
    kind, _, fn = f.partition("__")
    bp = os.path.join(BAK, f)
    if not os.path.isfile(bp): continue
    a = open(bp, encoding="utf-8", errors="ignore", newline='').read().split("\n")
    b = open(os.path.join(OUT, f), encoding="utf-8", errors="ignore", newline='').read().split("\n")
    if len(a) != len(b):
        vdetail.append("LEN %s %d vs %d" % (f, len(a), len(b))); viol += 1; continue
    for i, (x, y) in enumerate(zip(a, b), 1):
        if x == y: continue
        if ("icon" in x or "picture" in x) and ("icon" in y or "picture" in y):
            if x.split("=")[0].strip() != y.split("=")[0].strip():
                vdetail.append("KEYDIFF %s:%d" % (f, i)); viol += 1
        else:
            vdetail.append("NONICON %s:%d %r" % (f, i, x[:50])); viol += 1
print("\n非icon/picture 行改动: %d" % viol)
for v in vdetail[:10]: print("  " + v)

# ---- 括号平衡 ----
unbal = []
for f in os.listdir(OUT):
    s = open(os.path.join(OUT, f), encoding="utf-8", errors="ignore").read()
    d0 = s.count("{") - s.count("}")
    sb = open(os.path.join(BAK, f), encoding="utf-8", errors="ignore").read() if os.path.isfile(os.path.join(BAK,f)) else ""
    d1 = sb.count("{") - sb.count("}")
    if d0 != d1: unbal.append("%s  out=%d bak=%d" % (f, d0, d1))
print("括号深度变化的文件: %d" % len(unbal))
for u in unbal[:10]: print("  " + u)

txt = ["文件 %d 改写 %d 缺 %d 异常 %d" % (nfile, nline, miss, bad), ""] + detail
open(os.path.join(STG, "out6_report.txt"), "w", encoding="utf-8").write("\n".join(txt))