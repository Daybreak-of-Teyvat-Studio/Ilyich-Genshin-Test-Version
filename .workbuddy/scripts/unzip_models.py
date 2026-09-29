# -*- coding: utf-8 -*-
"""重新解压 PRC_infantry.zip 与 薇斯纳.zip（含 zip 中文名 cp437->gbk 还原）。
结果与日志写入 .workbuddy/vysna_work/ 。
"""
import os
import zipfile

ROOT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version"
BAK = os.path.join(ROOT, "Daybreak of Teyvat Gamma Version", ".backup")
WORK = r"C:\Users\XIANGZIYUAN\vysna_work"          # 工作区外，避开写保护
LOG = os.path.join(ROOT, ".workbuddy", "scripts", "report_unzip.txt")

lines = []


def fix_name(info):
    """zip 里中文名若未标 UTF-8，Python 会按 cp437 解；还原成 gbk。"""
    if info.flag_bits & 0x800:
        return info.filename
    try:
        raw = info.filename.encode("cp437")
    except UnicodeEncodeError:
        return info.filename
    for enc in ("gbk", "utf-8", "big5"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return info.filename


def do_zip(zpath, outdir, tag):
    lines.append("=" * 70)
    lines.append(f"[{tag}] {zpath}")
    if not os.path.isfile(zpath):
        lines.append("  !! 文件不存在")
        return
    os.makedirs(outdir, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            name = fix_name(info)
            lines.append(f"  {info.file_size:>10}  {name}")
            if info.is_dir():
                continue
            target = os.path.join(outdir, name.replace("/", os.sep))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with z.open(info) as src, open(target, "wb") as dst:
                dst.write(src.read())
    lines.append(f"  -> 解压到 {outdir}")


do_zip(os.path.join(BAK, "PRC_infantry.zip"),
       os.path.join(WORK, "PRC_infantry"), "PRC")
do_zip(os.path.join(BAK, "薇斯纳.zip"),
       os.path.join(WORK, "薇斯纳"), "VYSNA")

with open(LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done ->", LOG)
