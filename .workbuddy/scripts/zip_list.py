# -*- coding: utf-8 -*-
import os
import zipfile

BASE = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\.backup"
OUT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_zip_list.txt"

lines = []
for name in ["PRC_infantry.zip", "薇斯纳.zip"]:
    p = os.path.join(BASE, name)
    lines.append("=" * 78)
    lines.append(f"### {name}   ({os.path.getsize(p):,} bytes)")
    lines.append("=" * 78)
    try:
        z = zipfile.ZipFile(p)
        infos = z.infolist()
        lines.append(f"条目数: {len(infos)}")
        tot = 0
        for i in infos:
            tot += i.file_size
            flag = "" if not i.is_dir() else "  <DIR>"
            lines.append(f"  {i.file_size:>12,}  {i.filename}{flag}")
        lines.append(f"--- 解压后总大小: {tot:,} bytes ---")
    except Exception as e:
        lines.append(f"ERROR: {e!r}")
    lines.append("")

open(OUT, "w", encoding="utf-8").write("\n".join(lines))
print("OK ->", OUT)
