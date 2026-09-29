import os, re, struct, glob, collections, io
import numpy as np

D   = r"C:\Users\XIANGZIYUAN\Documents\Paradox Interactive\Hearts of Iron IV"
MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
VAN = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
OUT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_ctd.txt"
L = []
def P(*a):
    L.append(" ".join(str(x) for x in a))

# ---------- 0. 权威 MOD 描述文件 ----------
P("="*80); P("0. 已启用的 MOD 描述文件"); P("="*80)
mdir = os.path.join(D, "mod")
if os.path.isdir(mdir):
    for f in sorted(os.listdir(mdir)):
        if f.lower().endswith(".mod"):
            p = os.path.join(mdir, f)
            try:
                t = io.open(p, "r", encoding="utf-8-sig", errors="replace").read()
            except Exception as e:
                t = "READ FAIL " + str(e)
            P(f"--- {f} ---")
            for ln in t.splitlines()[:20]:
                P("   " + ln)
else:
    P("  mod 目录不存在:", mdir)

# ---------- 1. 崩溃签名汇总 ----------
P(""); P("="*80); P("1. 崩溃签名汇总（按时间）"); P("="*80)
cdir = os.path.join(D, "crashes")
sigs = collections.OrderedDict()
rows = []
for c in sorted(os.listdir(cdir)) if os.path.isdir(cdir) else []:
    cd = os.path.join(cdir, c)
    ex = os.path.join(cd, "exception.txt")
    if not os.path.isfile(ex):
        continue
    t = io.open(ex, "r", encoding="utf-8", errors="replace").read()
    addr = (re.search(r"at address (0x[0-9A-Fa-f]+)", t) or [None, "?"])[1]
    offs = re.findall(r"\(\+ (\d+)\)", t)[:8]
    dt = (re.search(r"^Date/Time:\s*(.+)$", t, re.M) or [None, "?"])[1].strip()
    my = os.path.join(cd, "meta.yml")
    cs = ""
    mods = ""
    if os.path.isfile(my):
        m = io.open(my, "r", encoding="utf-8", errors="replace").read()
        cs = ((re.search(r"^DataChecksum:\s*(\S*)", m, re.M) or [None, ""])[1])
        mods = ((re.search(r"^Mods:\s*(.*)$", m, re.M) or [None, ""])[1]).strip()
    key = (addr, ",".join(offs[:4]))
    sigs.setdefault(key, []).append(c)
    rows.append((c, dt, addr, offs, cs, mods))

# 只列 Sep 23 之后的（含今天）
for (c, dt, addr, offs, cs, mods) in rows:
    P(f"{c:26s} {dt:22s} {addr}  off[0:4]={offs[:4]}")
P("")
P("--- 签名分组（同地址+同偏移 = 同一处崩溃）---")
for i, (k, v) in enumerate(sigs.items(), 1):
    P(f"签名{i}: addr={k[0]}  n={len(v)}")
    P(f"    出现在: {', '.join(v)}")

# ---------- 2. 最近三次崩溃的日志尾部 ----------
P(""); P("="*80); P("2. 最近一次崩溃的现场日志"); P("="*80)
last = rows[-1][0] if rows else None
if last:
    for name in ["game.log", "error.log", "system.log"]:
        p = os.path.join(cdir, last, "logs", name)
        P(f"--- {last}/logs/{name} ---")
        if not os.path.isfile(p):
            P("   (不存在)"); continue
        sz = os.path.getsize(p)
        P(f"   体积 {sz:,} 字节")
        b = open(p, "rb").read()
        t = b.decode("utf-8", "replace")
        lines = t.splitlines()
        tail = lines[-40:] if len(lines) > 40 else lines
        for ln in tail:
            P("   | " + ln)
P("")
P("--- 用户目录 logs/game.log（最近一次运行）---")
p = os.path.join(D, "logs", "game.log")
if os.path.isfile(p):
    P(io.open(p, "r", encoding="utf-8", errors="replace").read())

# ---------- 3. map 目录文件体检（与原版对照）----------
P(""); P("="*80); P("3. map 目录 BMP 体检（MOD vs 原版）"); P("="*80)
def hdr(p):
    b = open(p, "rb").read(64)
    if b[:2] != b"BM":
        return None
    off = struct.unpack_from("<I", b, 10)[0]
    w, h = struct.unpack_from("<ii", b, 18)
    dib = struct.unpack_from("<I", b, 14)[0]
    bpp = struct.unpack_from("<HH", b, 26)[1]
    cu  = struct.unpack_from("<I", b, 46)[0]
    return dict(off=off, w=w, h=h, dib=dib, bpp=bpp, cu=cu, size=os.path.getsize(p))

mmap = os.path.join(MOD, "map")
vmap = os.path.join(VAN, "map")
names = sorted(set(os.path.basename(x) for x in glob.glob(os.path.join(mmap, "*.bmp"))))
P(f"{'文件':28s} {'MOD bpp/off/色槽/尺寸':38s} {'原版 bpp/off/色槽/尺寸':38s} 判定")
for n in names:
    a = hdr(os.path.join(mmap, n))
    vp = os.path.join(vmap, n)
    b = hdr(vp) if os.path.isfile(vp) else None
    fa = f"{a['bpp']}/{a['off']}/{a['cu']}/{a['w']}x{a['h']}" if a else "非BMP"
    fb = f"{b['bpp']}/{b['off']}/{b['cu']}/{b['w']}x{b['h']}" if b else "(无)"
    flag = ""
    if a and b and (a["bpp"] != b["bpp"]):
        flag = "!! 位深与原版不同"
    P(f"{n:28s} {fa:38s} {fb:38s} {flag}")

# terrain.bmp 索引合法性
P("")
P("--- terrain.bmp 索引 vs 00_terrain.txt 定义 ---")
tp = os.path.join(mmap, "terrain.bmp")
if os.path.isfile(tp):
    raw = open(tp, "rb").read()
    h = hdr(tp)
    n = h["cu"] or (h["off"] - 14 - h["dib"]) // 4
    po = 14 + h["dib"]
    pal = [tuple(raw[po + i*4: po + i*4 + 3][::-1]) for i in range(n)]
    a = np.frombuffer(raw[h["off"]: h["off"] + h["w"]*h["h"]], dtype=np.uint8)
    used = sorted(collections.Counter(a.tolist()).items())
    P(f"   {h['size']:,} B  off={h['off']} bpp={h['bpp']} clrUsed={h['cu']} palN={n} {h['w']}x{h['h']}")
    P(f"   palette: " + ", ".join(f"{i}={c}" for i, c in enumerate(pal)))
    P(f"   直方图: {used}")
    vt = io.open(os.path.join(VAN, "common", "terrain", "00_terrain.txt"), "r", encoding="utf-8", errors="replace").read()
    block = vt.split("terrain = {")[-1]
    valid = set(int(x) for x in re.findall(r"color\s*=\s*\{\s*(\d+)\s*\}", block))
    P(f"   00_terrain.txt 合法索引: {sorted(valid)}")
    usedset = set(k for k, _ in used)
    P(f"   未定义索引: {sorted(usedset - valid)}")
else:
    P("   terrain.bmp 不存在！")

# 其他 BMP 的索引合法性（cities/trees/rivers/heightmap/provinces/world_normal）
P("")
P("--- 其余关键 BMP 的位深与索引范围 ---")
for n in ["provinces.bmp", "heightmap.bmp", "cities.bmp", "trees.bmp", "rivers.bmp",
          "world_normal.bmp", "colormap_rgb.bmp", "colormap_water.bmp", "terrain.bmp"]:
    p = os.path.join(mmap, n)
    if not os.path.isfile(p):
        P(f"   {n:22s} 不存在"); continue
    h = hdr(p)
    if not h:
        P(f"   {n:22s} 非 BMP"); continue
    raw = open(p, "rb").read()
    a = np.frombuffer(raw[h["off"]: h["off"] + h["w"]*h["h"]], dtype=np.uint8) if h["bpp"] == 8 else None
    extra = ""
    if h["bpp"] == 8:
        u = np.unique(a)
        extra = f" 索引数={len(u)} 范围=[{u.min()},{u.max()}]"
    P(f"   {n:22s} size={h['size']:,} off={h['off']} bpp={h['bpp']} clrUsed={h['cu']} {h['w']}x{h['h']}{extra}")

# ---------- 4. history/states 体检 ----------
P(""); P("="*80); P("4. history/states 体检"); P("="*80)
sdir = os.path.join(MOD, "history", "states")
if os.path.isdir(sdir):
    fs = sorted(glob.glob(os.path.join(sdir, "*.txt")))
    P(f"   文件数 = {len(fs)}")
    zero = [os.path.basename(f) for f in fs if os.path.getsize(f) == 0]
    P(f"   0 字节文件 = {len(zero)}: {zero[:20]}")
    tot = 0
    ids = collections.Counter()
    bad = []
    for f in fs:
        t = io.open(f, "r", encoding="utf-8", errors="replace").read()
        tot += len(t.splitlines())
        m = re.search(r"^\s*id\s*=\s*(\d+)", t, re.M)
        if m:
            ids[int(m.group(1))] += 1
        else:
            bad.append(os.path.basename(f) + " (无 id)")
    P(f"   总行数 = {tot:,}")
    P(f"   无 id 的文件 = {len(bad)}: {bad[:20]}")
    dup = {k: v for k, v in ids.items() if v > 1}
    P(f"   重复 state id = {len(dup)}  例: {list(dup.items())[:20]}")
    P(f"   state id 范围 = [{min(ids) if ids else '-'}, {max(ids) if ids else '-'}]")
else:
    P("   history/states 目录不存在")

# 原版对照
vsdir = os.path.join(VAN, "history", "states")
if os.path.isdir(vsdir):
    P(f"   （原版 history/states 文件数 = {len(glob.glob(os.path.join(vsdir, '*.txt')))}）")

io.open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("WROTE", OUT, len(L), "lines")
