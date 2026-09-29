import os, re, io, glob, collections

MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
VAN = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
OUT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_ctd3.txt"
L = []
def P(*a):
    L.append(" ".join(str(x) for x in a))

# ---------- 1. 建筑定义表（MOD + 原版）----------
P("="*80); P("1. 建筑类型定义表"); P("="*80)
defined = {}
for root, tag in ((MOD, "MOD"), (VAN, "原版")):
    for f in glob.glob(os.path.join(root, "common", "buildings", "*.txt")):
        t = io.open(f, "r", encoding="utf-8", errors="replace").read()
        # 顶层块: name = {
        for m in re.finditer(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", t, re.M):
            nm = m.group(1)
            if nm in ("buildings",):
                continue
            defined.setdefault(nm, []).append((tag, os.path.basename(f)))
P(f"   定义到的建筑类型总数 = {len(defined)}")
modonly = sorted(k for k, v in defined.items() if any(t == "MOD" for t, _ in v))
P(f"   MOD 侧提供的类型 ({len(modonly)}): {modonly}")

# ---------- 2. history/states 里实际指派的建筑 ----------
P(""); P("="*80); P("2. history/states 里指派的建筑类型"); P("="*80)
sdir = os.path.join(MOD, "history", "states")
assigned = collections.Counter()
where = collections.defaultdict(list)
files = sorted(glob.glob(os.path.join(sdir, "*.txt")))
for f in files:
    t = io.open(f, "r", encoding="utf-8", errors="replace").read()
    # 在 buildings = { ... } 块里取 key = N
    for mb in re.finditer(r"buildings\s*=\s*\{(.*?)\}", t, re.S):
        for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\d+", mb.group(1)):
            nm = m.group(1)
            assigned[nm] += 1
            if len(where[nm]) < 4:
                where[nm].append(os.path.basename(f))
P(f"   指派的建筑种类 = {len(assigned)}")
undef = []
for nm, c in assigned.most_common():
    ok = nm in defined
    if not ok:
        undef.append(nm)
    P(f"   {nm:44s} x{c:<6} 定义={'MOD '+str(defined[nm]) if ok and any(t=='MOD' for t,_ in defined[nm]) else ('原版' if ok else '**未定义**')}")
P("")
P(f"   **未定义的建筑类型 = {len(undef)}: {undef}**")

# ---------- 3. landmark 类建筑 ----------
P(""); P("="*80); P("3. landmark 建筑与实体（对照日志里的 doesn't have an entity）"); P("="*80)
for nm in ["landmark_institute_of_tower", "landmark_Lei_Line_research_center"]:
    P(f"   {nm}: 定义 = {defined.get(nm, '未定义')}")
# 找 gfx entities 定义
ents = {}
for root, tag in ((MOD, "MOD"), (VAN, "原版")):
    for f in glob.glob(os.path.join(root, "gfx", "entities", "*.gfx")) + glob.glob(os.path.join(root, "gfx", "**", "*.gfx"), recursive=True):
        try:
            t = io.open(f, "r", encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for m in re.finditer(r'^\s*name\s*=\s*"([^"]+)"', t, re.M):
            ents.setdefault(m.group(1), (tag, os.path.relpath(f, root)))
for nm in ["landmark_institute_of_tower", "landmark_Lei_Line_research_center",
           "landmark_institute_of_tower_entity", "landmark_Lei_Line_research_center_entity"]:
    P(f"   entity '{nm}': {ents.get(nm, '未找到')}")

# ---------- 4. buildings.txt 数值范围核验 ----------
P(""); P("="*80); P("4. buildings.txt 第 4 列（高程）数值核验"); P("="*80)
bp = os.path.join(MOD, "map", "buildings.txt")
ys = []
xs = []
zs = []
rots = collections.Counter()
for ln in open(bp, "rb").read().split(b"\n"):
    s = ln.rstrip(b"\r")
    if not s:
        continue
    f = s.split(b";")
    if len(f) != 7:
        continue
    try:
        xs.append(float(f[2])); ys.append(float(f[3])); zs.append(float(f[4]))
        rots[f[5].decode("ascii", "replace")] += 1
    except Exception:
        pass
import statistics as st
P(f"   行数 = {len(ys):,}")
P(f"   x 范围 [{min(xs):.1f}, {max(xs):.1f}]   z 范围 [{min(zs):.1f}, {max(zs):.1f}]")
P(f"   y 范围 [{min(ys):.3f}, {max(ys):.3f}]  中位 {st.median(ys):.3f}")
P(f"   y 的 10 大取值: {collections.Counter(round(v,3) for v in ys).most_common(10)}")
P(f"   旋转列取值: {dict(rots)}")
# 原版 buildings.txt 对照
vp = os.path.join(VAN, "map", "buildings.txt")
if os.path.isfile(vp) and os.path.getsize(vp) > 0:
    P("   原版 map/buildings.txt 前 3 行:")
    for ln in io.open(vp, "r", encoding="utf-8", errors="replace").read().splitlines()[:3]:
        P("     " + ln)
    P(f"   原版体积 = {os.path.getsize(vp):,}")
else:
    P(f"   原版 map/buildings.txt: 不存在或 0 字节 (size={os.path.getsize(vp) if os.path.isfile(vp) else 'N/A'})")

# ---------- 5. victory_points 语法检查 ----------
P(""); P("="*80); P("5. history/states 里 victory_points 的写法"); P("="*80)
bad = []
good = 0
for f in files:
    t = io.open(f, "r", encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"^\s*(set_)?victory_points\s*=(.*)$", t, re.M):
        v = m.group(2).strip()
        if not v.startswith("{"):
            bad.append((os.path.basename(f), v[:60]))
        else:
            good += 1
P(f"   带花括号的正确写法 = {good}")
P(f"   缺花括号的写法 = {len(bad)}")
for a, b in bad[:15]:
    P(f"     {a}: victory_points = {b}")
# 展示一条原文
if bad:
    f0 = os.path.join(sdir, bad[0][0])
    t = io.open(f0, "r", encoding="utf-8", errors="replace").read().splitlines()
    P("")
    P(f"   --- {bad[0][0]} 第 18-32 行 ---")
    for i, ln in enumerate(t[17:32], 18):
        P(f"   {i:4d}| {ln}")

io.open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("WROTE", OUT, len(L))
