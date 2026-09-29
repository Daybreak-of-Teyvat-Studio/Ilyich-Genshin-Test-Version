# -*- coding: utf-8 -*-
"""侦察 HOI4 .mesh 二进制结构。"""
import glob
import os
import struct

ROOT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version"
P = os.path.join(ROOT, ".workbuddy", "vysna_work", "PRC_infantry", "PRC_infantry.mesh")
OUT = os.path.join(ROOT, ".workbuddy", "report_mesh_probe.txt")

L = []
def P_(s=""):
    L.append(str(s))

raw = open(P, "rb").read()
P_(f"file: {P}")
P_(f"size: {len(raw):,} bytes")
P_("")
P_("=" * 78)
P_("前 512 字节 hex + ascii")
P_("=" * 78)
for off in range(0, min(512, len(raw)), 16):
    chunk = raw[off:off + 16]
    hx = " ".join(f"{b:02x}" for b in chunk)
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    P_(f"{off:08x}  {hx:<47}  {asc}")

P_("")
P_("=" * 78)
P_("头部按多种假设解析")
P_("=" * 78)
ints = struct.unpack_from("<8i", raw, 0)
P_(f"<8i @0   : {ints}")
flts = struct.unpack_from("<8f", raw, 0)
P_(f"<8f @0   : " + ", ".join(f"{v:.4f}" for v in flts))

P_("")
P_("=" * 78)
P_("在文件里找可见字符串（长度>=3 的 ASCII 串）")
P_("=" * 78)
found = []
cur = bytearray()
cur_off = 0
for i, b in enumerate(raw):
    if 32 <= b < 127:
        if not cur:
            cur_off = i
        cur.append(b)
    else:
        if len(cur) >= 3:
            found.append((cur_off, bytes(cur).decode("ascii", "replace")))
        cur = bytearray()
if len(cur) >= 3:
    found.append((cur_off, bytes(cur).decode("ascii", "replace")))

P_(f"可见串数量: {len(found)}")
for off, s in found[:120]:
    P_(f"  @{off:08x} ({off:>8,})  {s}")

P_("")
P_("=" * 78)
P_("MOD 内全部 .mesh / .anim 文件")
P_("=" * 78)
for pat in ("**/*.mesh", "**/*.anim"):
    P_(f"--- {pat} ---")
    hits = []
    for base in ("Daybreak of Teyvat Gamma Version", "Daybreak of Teyvat Beta Version"):
        hits += glob.glob(os.path.join(ROOT, base, pat), recursive=True)
    if not hits:
        P_("  (无)")
    for h in hits:
        P_(f"  {os.path.getsize(h):>10,}  {os.path.relpath(h, ROOT)}")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("OK ->", OUT, f"({len(L)} lines)")
