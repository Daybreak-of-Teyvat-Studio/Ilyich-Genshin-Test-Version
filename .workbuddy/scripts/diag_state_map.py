import os, re, io, glob, collections

MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
OUT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_state_map.txt"
L = []
def P(*a):
    L.append(" ".join(str(x) for x in a))

# ---------- 1. definition.csv ----------
P("="*80); P("1. definition.csv 的省份分类"); P("="*80)
land, sea = set(), set()
rows = []
for ln in io.open(os.path.join(MOD, "map", "definition.csv"), "r", encoding="utf-8-sig", errors="replace").read().splitlines():
    f = ln.split(";")
    if len(f) < 8:
        continue
    try:
        pid = int(f[0])
    except Exception:
        continue
    rows.append((pid, f[4].strip().lower(), f[6].strip().lower()))
    (land if f[4].strip().lower() == "land" else sea).add(pid)
allids = set(p for p, _, _ in rows)
P(f"   总省数 = {len(allids)}   land = {len(land)}   sea = {len(sea)}")
P(f"   id 范围 = [{min(allids)}, {max(allids)}]  连续 = {len(allids) == max(allids)-min(allids)+1}")

# ---------- 2. history/states 声明的 provinces ----------
P(""); P("="*80); P("2. history/states 的 provinces 列表 vs definition.csv"); P("="*80)
sdir = os.path.join(MOD, "history", "states")
union = set()
owner = collections.defaultdict(list)
emptystate = []
noprov = []
stinfo = {}
for f in sorted(glob.glob(os.path.join(sdir, "*.txt"))):
    t = io.open(f, "r", encoding="utf-8", errors="replace").read()
    sid = re.search(r"^\s*id\s*=\s*(\d+)", t, re.M)
    sid = int(sid.group(1)) if sid else None
    m = re.search(r"provinces\s*=\s*\{([^}]*)\}", t, re.S)
    provs = [int(x) for x in re.findall(r"\d+", m.group(1))] if m else []
    if not m:
        noprov.append(os.path.basename(f))
    if len(provs) == 0:
        emptystate.append(os.path.basename(f))
    stinfo[sid] = provs
    for p in provs:
        union.add(p)
        owner[p].append(sid)
P(f"   州数 = {len(stinfo)}")
P(f"   声明到的省总数（去重）= {len(union)}")
P(f"   没有 provinces 块的州 = {len(noprov)}  {noprov[:8]}")
P(f"   有 provinces 块但为空的州 = {len(emptystate)}  {emptystate[:8]}")
land_not_in_state = sorted(p for p in land if p not in union)
P(f"   **陆地省但不在任何州里 = {len(land_not_in_state)}**  例: {land_not_in_state[:30]}")
sea_in_state = sorted(p for p in union if p in sea)
P(f"   **海省却被州声明 = {len(sea_in_state)}**  例: {sea_in_state[:30]}")
ghost = sorted(p for p in union if p not in allids)
P(f"   **州声明的省在 definition.csv 里不存在 = {len(ghost)}**  例: {ghost[:30]}")
dup = sorted(p for p, v in owner.items() if len(v) > 1)
P(f"   **被两个及以上的州重复声明 = {len(dup)}**  例: {[(p, owner[p]) for p in dup[:10]]}")

# ---------- 3. strategicregions ----------
P(""); P("="*80); P("3. map/strategicregions 与省份的对应"); P("="*80)
srfiles = glob.glob(os.path.join(MOD, "map", "strategicregions", "*.txt"))
P(f"   文件数 = {len(srfiles)}")
sr_union = set()
sr_dup = collections.defaultdict(list)
sr_blocks = 0
sr_ghost = []
for f in srfiles:
    t = io.open(f, "r", encoding="utf-8", errors="replace").read()
    for mb in re.finditer(r"^\s*(\d+)\s*=\s*\{", t, re.M):
        sr_blocks += 1
    for mb in re.finditer(r"provinces\s*=\s*\{([^}]*)\}", t, re.S):
        for x in re.findall(r"\d+", mb.group(1)):
            p = int(x)
            sr_union.add(p)
            sr_dup[p].append(1)
P(f"   战略区块数 = {sr_blocks}   声明到的省（去重）= {len(sr_union)}")
no_sr = sorted(p for p in land if p not in sr_union)
P(f"   **陆地省没有战略区 = {len(no_sr)}**  例: {no_sr[:30]}")
sr_ghost = sorted(p for p in sr_union if p not in allids)
P(f"   **战略区声明了不存在的省 = {len(sr_ghost)}**  例: {sr_ghost[:30]}")

# ---------- 4. 1936 书签全文 ----------
P(""); P("="*80); P("4. common/bookmarks/3_The_Traveler.txt（1936 开局用的书架）"); P("="*80)
bp = os.path.join(MOD, "common", "bookmarks", "3_The_Traveler.txt")
t = io.open(bp, "r", encoding="utf-8", errors="replace").read()
for i, ln in enumerate(t.splitlines(), 1):
    if i <= 60 or i >= 75:
        P(f"{i:4d}| {ln}")

P("")
P("="*80); P("5. 州文件的一个完整样例（380-State_380.txt）"); P("="*80)
sp = os.path.join(sdir, "380-State_380.txt")
if os.path.isfile(sp):
    for i, ln in enumerate(io.open(sp, "r", encoding="utf-8", errors="replace").read().splitlines(), 1):
        P(f"{i:4d}| {ln}")

io.open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("WROTE", OUT, len(L))
