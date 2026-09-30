# -*- coding: utf-8 -*-
import os
import zipfile

BASE = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\.backup"
OUTDIR = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\vysna_work"
LOG = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_unzip.txt"

os.makedirs(OUTDIR, exist_ok=True)
lines = []

for name in ["PRC_infantry.zip", "薇斯纳.zip"]:
    src = os.path.join(BASE, name)
    dst = os.path.join(OUTDIR, os.path.splitext(name)[0])
    os.makedirs(dst, exist_ok=True)
    z = zipfile.ZipFile(src)
    lines.append(f"### {name} -> {dst}")
    raw = z.namelist()
    for info in z.infolist():
        try:
            # zip 里的中文名可能是 cp437 误解码，尝试还原
            nm = info.filename
            if not (info.flag_bits & 0x800):
                try:
                    nm = info.filename.encode("cp437").decode("gbk")
                except Exception:
                    nm = info.filename
            target = os.path.join(dst, nm.replace("/", os.sep))
            if info.is_dir():
                os.makedirs(target, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with z.open(info) as fsrc, open(target, "wb") as fdst:
                fdst.write(fsrc.read())
            lines.append(f"  OK  {nm}")
        except Exception as e:
            lines.append(f"  ERR {info.filename}: {e!r}")
    lines.append("")

open(LOG, "w", encoding="utf-8").write("\n".join(lines))
print("OK ->", LOG)
