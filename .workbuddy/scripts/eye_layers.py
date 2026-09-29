# -*- coding: utf-8 -*-
"""眼球叠层几何诊断：各材质在输出 mesh 中的 z 分布 + 层间重合关系。

角色朝 -Z ⇒ z 越小越靠前（越靠近观察者）。
需要弄清：白目(眼白) / 目(虹膜) / 瞳(瞳孔) / 目光(高光) / 颜,颜2(脸皮) / 睫
谁在前谁在后，以及是否几何重合（重合才需要前推）。
只读。"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")

from pmx_parse import PMX                      # noqa: E402
import render_preview as RP                    # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
MESH = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
        r"\Ilyich-Genshin-Test-Version\.workbuddy\vysna_out3\Vysna_infantry.mesh")
HERE_DIR = os.path.dirname(HERE)

# 与 vysna_build.py 保持一致的排除表（只关心 face 组）
EXCLUDE_KEYS = ["结晶", "头饰", "照れ", "袜s", "翼+", "髮+", "肌2", "披肩s",
                "裙+", "颜3", "颜4"]
MAT_GROUP = {
    "颜": "face", "颜2": "face", "颜3": "face", "颜4": "face", "睫": "face",
    "眉": "face", "白目": "face", "目": "face", "瞳": "face", "目光": "face",
    "鼻线": "face", "口舌": "face", "齿": "face", "星目": "face", "照れ": "face",
}

pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))

# ---- 复现 face 组在输出 tri 数组里的分段
# 注意：输出 mesh 的 face draw call 只包含「保留下来且属于 face 组」的材质，
# 所以偏移量必须只按这些材质累加，不能按 PMX 全部材质累加。
segs = []
out_tri = 0
for i, mt in enumerate(pmx.materials):
    nm = mt["name"]
    cnt = mt["face_count"]
    if any(k in nm for k in EXCLUDE_KEYS):
        continue
    if MAT_GROUP.get(nm) != "face":
        continue
    segs.append((nm, out_tri, cnt // 3, i))
    out_tri += cnt // 3

nodes = RP.gather(MESH)
# gather 返回全部 mesh 节点；找到三角数等于 face 组总数的那个
total = sum(s[2] for s in segs)
face = None
for nd in nodes:
    if len(nd["T"]) == total:
        face = nd
        break
assert face is not None, "没找到 face 节点（三角数 %d）" % total
P, T = face["P"], face["T"]
print("face 节点三角 %d  分段合计 %d" % (len(T), total))

out = []
out.append("face 组各材质在输出 mesh 中的 z 分布（z 越小越靠前，角色朝 -Z）")
out.append("=" * 92)
out.append("%-6s %7s %9s %9s %9s %9s" % ("材质", "三角", "z_min", "z_P25", "z_P50", "z_max"))
zinfo = {}
segs = [s for s in segs if s[2] > 0]      # 有些材质 face_count = 0
for nm, a, n, mi in segs:
    tri = T[a:a + n]
    z = P[tri][..., 2].ravel()
    zinfo[nm] = z
    out.append("%-6s %7d %9.5f %9.5f %9.5f %9.5f"
               % (nm, n, z.min(), np.percentile(z, 25), np.percentile(z, 50), z.max()))

out.append("")
out.append("按 z 中位数从前往后排序：")
zmed = sorted(((float(np.median(v)), k) for k, v in zinfo.items()))
for z, k in zmed:
    out.append("    %-6s z_med = %8.5f   (n=%d)" % (k, z, len(zinfo[k]) // 3))

# ---- 层间重合（质心取整 1e-3）与前后关系
out.append("")
out.append("层间几何重合检测（质心取整到 1e-3；只列重合率 > 5% 的对）")
out.append("-" * 92)


def cents(nm):
    tri = T[a_of[nm]:a_of[nm] + n_of[nm]]
    c = P[tri].mean(1)
    return np.round(c, 3)


a_of = {nm: a for nm, a, n, mi in segs}
n_of = {nm: n for nm, a, n, mi in segs}
cs = {nm: cents(nm) for nm, a, n, mi in segs}
zmed_of = {k: float(np.median(v)) for k, v in zinfo.items()}

names = [nm for nm, a, n, mi in segs]
pairs = []
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        A, B = names[i], names[j]
        ka = set(map(tuple, cs[A]))
        kb = set(map(tuple, cs[B]))
        inter = ka & kb
        if not inter:
            continue
        rate = len(inter) / float(min(len(ka), len(kb)))
        if rate > 0.05:
            pairs.append((rate, len(inter), A, B, zmed_of[A], zmed_of[B]))
pairs.sort(reverse=True)
for rate, c, A, B, za, zb in pairs:
    front = A if za < zb else B
    out.append("  重合 %5.1f%%  共同 %6d  %-6s(z=%8.5f)  vs  %-6s(z=%8.5f)   -> 在前：%s"
               % (rate * 100, c, A, za, B, zb, front))

# ---- 眼球叠层两两之间的「谁盖谁」：用其中一者的顶点去查另一者所在平面
out.append("")
out.append("说明：z 越小越靠前。若 A.z < B.z，则 B 需要被前推，或者 A 需要后移。")
out.append("      目标层级（前->后）：目光/瞳 > 目 > 白目 > 颜/颜2（脸皮）")

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_eye_layers.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_eye_layers_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt + "\n")
print("\n-> %s" % p)
