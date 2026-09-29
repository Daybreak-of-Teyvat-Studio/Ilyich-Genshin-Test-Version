import os, re, io, glob, struct, collections
import numpy as np

D   = r"C:\Users\XIANGZIYUAN\Documents\Paradox Interactive\Hearts of Iron IV"
MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
VAN = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
OUT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_ctd2.txt"
L = []
def P(*a):
    L.append(" ".join(str(x) for x in a))

cdir = os.path.join(D, "crashes")

P("="*80); P("A. 今天各次崩溃的「最后日志行」与「崩溃前走到哪一步」"); P("="*80)
for c in sorted(os.listdir(cdir)):
    if not re.match(r"hoi4_2026092[34]", c):
        continue
    cd = os.path.join(cdir, c)
    ex = os.path.join(cd, "exception.txt")
    if not os.path.isfile(ex):
        continue
    t = io.open(ex, "r", encoding="utf-8", errors="replace").read()
    head = "\n".join(t.splitlines()[:6])
    P("#" * 70)
    P("### " + c)
    P(head)
    el = os.path.join(cd, "logs", "error.log")
    if os.path.isfile(el):
        lines = io.open(el, "r", encoding="utf-8", errors="replace").read().splitlines()
        P(f"   error.log 行数={len(lines):,}")
        for ln in lines[-12:]:
            P("   | " + ln[:200])
    else:
        P("   (无 error.log)")

P(""); P("="*80); P("B. MOD 是否覆盖了日志点名的界面文件"); P("="*80)
for rel in ["interface/frontendgamesetupview.gui", "interface/countryselectview.gui",
            "interface/frontendcountryselectview.gui"]:
    mp = os.path.join(MOD, rel)
    vp = os.path.join(VAN, rel)
    ma = os.path.getsize(mp) if os.path.isfile(mp) else None
    va = os.path.getsize(vp) if os.path.isfile(vp) else None
    P(f"   {rel:46s} MOD={ma!s:>10}  原版={va!s:>10}")
    if ma and va:
        P(f"      体积比 = {ma/va:.2%}" + ("   <-- 残缺副本嫌疑" if ma/va < 0.7 else ""))

P(""); P("="*80); P("C. buildings.txt 字段与第 1 列取值范围"); P("="*80)
bp = os.path.join(MOD, "map", "buildings.txt")
raw = open(bp, "rb").read()
lines = raw.split(b"\n")
fc = collections.Counter()
c1 = []
types = collections.Counter()
badline = []
for i, ln in enumerate(lines):
    s = ln.rstrip(b"\r")
    if not s:
        continue
    f = s.split(b";")
    fc[len(f)] += 1
    if len(f) >= 2:
        try:
            c1.append(int(f[0]))
            types[f[1].decode("ascii", "replace")] += 1
        except Exception:
            badline.append((i + 1, s[:80]))
P(f"   体积 = {len(raw):,} B   行数 = {len(lines):,}   字段数分布 = {dict(fc)}")
P(f"   第1列: 唯一值 {len(set(c1))}  范围 [{min(c1)}, {max(c1)}]")
P(f"   建筑类型数 = {len(types)}   top12 = {types.most_common(12)}")
P(f"   解析失败行 = {len(badline)}: {badline[:5]}")

P(""); P("="*80); P("D. definition.csv 与 provinces.bmp"); P("="*80)
dp = os.path.join(MOD, "map", "definition.csv")
if os.path.isfile(dp):
    b = open(dp, "rb").read()
    P(f"   definition.csv {len(b):,} B  BOM={b[:3]==b'\\xef\\xbb\\xbf'}  CRLF={b.count(bytes([13,10])):,}  行={len(b.split(bytes([10]))):,}")
    rows = [x for x in b.decode("utf-8-sig", "replace").splitlines() if x.strip()]
    P(f"   非空行 = {len(rows)}")
    ids = []
    cols = collections.Counter()
    bad = []
    for r in rows:
        f = r.split(";")
        cols[len(f)] += 1
        try:
            ids.append(int(f[0]))
        except Exception:
            bad.append(r[:60])
    P(f"   字段数分布 = {dict(cols)}   province id 范围 = [{min(ids)}, {max(ids)}]  唯一 = {len(set(ids))}")
    P(f"   解析失败 = {len(bad)}: {bad[:5]}")
    P("   前 3 行:")
    for r in rows[:3]:
        P("     " + r)

pp = os.path.join(MOD, "map", "provinces.bmp")
b = open(pp, "rb").read(64)
off = struct.unpack_from("<I", b, 10)[0]
w, h = struct.unpack_from("<ii", b, 18)
bpp = struct.unpack_from("<HH", b, 26)[1]
raw = open(pp, "rb").read()
px = np.frombuffer(raw[off:off + w * h * 3], dtype=np.uint8).reshape(h, w, 3)
colint = (px[:, :, 0].astype(np.int32) << 16) | (px[:, :, 1].astype(np.int32) << 8) | px[:, :, 2].astype(np.int32)
uniq = np.unique(colint)
P(f"   provinces.bmp {w}x{h} bpp={bpp}  唯一 RGB 数 = {len(uniq):,}")

P(""); P("="*80); P("E. history/states 与 provinces/definition 的数量对账"); P("="*80)
sdir = os.path.join(MOD, "history", "states")
sids = []
for f in sorted(glob.glob(os.path.join(sdir, "*.txt"))):
    t = io.open(f, "r", encoding="utf-8", errors="replace").read()
    m = re.search(r"^\s*id\s*=\s*(\d+)", t, re.M)
    if m:
        sids.append(int(m.group(1)))
P(f"   state 文件 {len(sids)} 个，id 范围 [{min(sids)}, {max(sids)}]")
P(f"   buildings.txt 第1列范围 [{min(c1)}, {max(c1)}]  ← 若与 state id 同域则第1列是 state_id")
P(f"   buildings 第1列不在 state id 集合里的个数 = {len([x for x in set(c1) if x not in set(sids)])}")
if set(c1) - set(sids):
    P(f"      例: {sorted(set(c1) - set(sids))[:20]}")

io.open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("WROTE", OUT, len(L), "lines")
