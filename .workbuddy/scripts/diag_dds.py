import os, struct, subprocess, io

MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
VAN = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
REPO = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version"
OUT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_dds.txt"
L = []
def P(*a):
    L.append(" ".join(str(x) for x in a))

def dds_info(raw):
    if raw[:4] != b"DDS ":
        return "不是 DDS"
    h = struct.unpack_from("<I", raw, 4)[0]           # dwSize(124)
    flags, height, width = struct.unpack_from("<III", raw, 8)
    pitch, depth, mips = struct.unpack_from("<III", raw, 20)
    pf_size, pf_flags, fourcc = struct.unpack_from("<III", raw, 76)
    fourcc_s = struct.pack("<I", fourcc).decode("ascii", "replace")
    return (f"{width}x{height} mips={mips} pitch={pitch} depth={depth} "
            f"fourcc={fourcc_s!r} pfFlags=0x{pf_flags:X} hdrSize={h}")

P("="*80)
P("map/terrain/*.dds 头部（MOD 工作区 vs 原版）")
P("="*80)
mdir = os.path.join(MOD, "map", "terrain")
vdir = os.path.join(VAN, "map", "terrain")
for f in sorted(os.listdir(mdir)):
    if not f.lower().endswith(".dds"):
        continue
    mp = os.path.join(mdir, f)
    vp = os.path.join(vdir, f)
    P(f"--- {f} ---")
    P(f"   MOD  {os.path.getsize(mp):>10,} B   {dds_info(open(mp,'rb').read(128))}")
    if os.path.isfile(vp):
        P(f"   原版 {os.path.getsize(vp):>10,} B   {dds_info(open(vp,'rb').read(128))}")

P("")
P("="*80)
P("colormap_rgb_cityemissivemask_a.dds 的历史（git HEAD / HEAD~1）")
P("="*80)
rel = "Daybreak of Teyvat Gamma Version/map/terrain/colormap_rgb_cityemissivemask_a.dds"
for rev in ["HEAD", "HEAD~1", "HEAD~2"]:
    try:
        r = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=REPO, capture_output=True)
        if r.returncode != 0:
            P(f"   {rev}: 取不到")
            continue
        b = r.stdout
        P(f"   {rev:8s} {len(b):>10,} B   {dds_info(b[:128])}")
        # 完整 blob 的字节数是否符合该尺寸的 DXT 家族
        P(f"            头后面还有 {len(b)-128:,} B 数据")
    except Exception as e:
        P(f"   {rev}: {e}")

P("")
P("="*80)
P("其余地图 bmp 尺寸与原版比例对照（判断是否齐整）")
P("="*80)
def bmp_wh(p):
    b = open(p, "rb").read(64)
    if b[:2] != b"BM":
        return None
    return struct.unpack_from("<ii", b, 18)
pairs = ["provinces.bmp", "heightmap.bmp", "terrain.bmp", "rivers.bmp", "cities.bmp",
         "trees.bmp", "world_normal.bmp"]
P(f"{'文件':20s} {'MOD':>14s} {'原版':>14s}   比例")
for n in pairs:
    a = bmp_wh(os.path.join(MOD, "map", n))
    v = bmp_wh(os.path.join(VAN, "map", n))
    ratio = f"{a[0]/v[0]:.3f} x {a[1]/v[1]:.3f}" if a and v else "-"
    P(f"{n:20s} {str(a):>14s} {str(v):>14s}   {ratio}")

io.open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("WROTE", OUT, len(L))
