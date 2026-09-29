# -*- coding: utf-8 -*-
"""批量解压 .backup 里的模型并探查结构（只读，结果写报告）。"""
import os
import sys
import zipfile
import collections

BK = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
      r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\.backup")
DST = (r"C:\Users\XIANGZIYUAN\vysna_work")

out = []
zips = [f for f in os.listdir(BK) if f.lower().endswith(".zip")]
out.append("找到 %d 个压缩包: %s" % (len(zips), zips))

for z in zips:
    tag = os.path.splitext(z)[0]
    tgt = os.path.join(DST, tag)
    zp = os.path.join(BK, z)
    if os.path.isdir(tgt):
        out.append("\n=== %s 已解压，跳过 ===" % tag)
    else:
        os.makedirs(tgt, exist_ok=True)
        with zipfile.ZipFile(zp) as f:
            names = f.namelist()
            # 中文文件名：cp437 -> gbk 还原
            for info in f.infolist():
                raw = info.filename
                try:
                    nm = raw.encode("cp437").decode("gbk")
                except Exception:
                    nm = raw
                info.filename = nm
            f.extractall(tgt)
        out.append("\n=== %s 解压完成 (%d 项) ===" % (tag, len(names)))

    # 结构探查
    exts = collections.Counter()
    pmxs, texs = [], []
    for root, _, files in os.walk(tgt):
        for fn in files:
            e = os.path.splitext(fn)[1].lower()
            exts[e] += 1
            if e in (".pmx", ".pmd"):
                pmxs.append(os.path.join(root, fn))
            elif e in (".png", ".jpg", ".bmp", ".tga", ".dds", ".spa", ".sph"):
                texs.append(fn)
    out.append("  扩展名: %s" % dict(exts))
    for p in pmxs:
        out.append("  PMX: %s  (%.1f MB)" % (p, os.path.getsize(p) / 1e6))
    out.append("  贴图 %d 张: %s" % (len(texs), sorted(texs)[:30]))
    # 顶层目录
    top = sorted(os.listdir(tgt))
    out.append("  顶层: %s" % top)

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_batch_prep.txt")
open(p, "w", encoding="utf-8").write("\n".join(out))
print("done ->", p)
