# -*- coding: utf-8 -*-
"""白目 的 UV 为何被压成一个点？直接看它的原始 UV 分布与三角形形状。"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pmx_parse import PMX                      # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
UV = np.array(pmx.v_uv, np.float64)
V = np.array(pmx.v_pos, np.float64)
faces = np.array(pmx.faces, np.int64)

EXCLUDE = ["结晶", "头饰", "照れ", "袜s", "翼+", "髮+", "肌2", "披肩s",
           "裙+", "颜3", "颜4"]
FG = {"颜", "颜2", "睫", "眉", "白目", "目", "瞳", "目光", "鼻线", "口舌",
      "齿", "星目", "照れ"}

segs = {}
acc = 0
for mt in pmx.materials:
    nm = mt["name"]
    cnt = mt["face_count"]
    if not any(k in nm for k in EXCLUDE) and nm in FG:
        segs[nm] = (acc, cnt, mt["tex"])
    acc += cnt

out = []
for nm in ["白目", "目", "瞳"]:
    a, cnt, ti = segs[nm]
    T = faces[a:a + cnt].reshape(-1, 3)
    f = np.unique(T)
    u, v = UV[f, 0], UV[f, 1]
    out.append("%s  顶点 %d  三角 %d" % (nm, len(f), len(T)))
    out.append("   uv  u[%.4f, %.4f] 跨度 %.4f    v[%.4f, %.4f] 跨度 %.4f"
               % (u.min(), u.max(), np.ptp(u), v.min(), v.max(), np.ptp(v)))
    out.append("   位置 x[%.4f, %.4f] 跨度 %.4f   y[%.4f, %.4f]   z[%.4f, %.4f]"
               % (V[f, 0].min(), V[f, 0].max(), np.ptp(V[f, 0]),
                  V[f, 1].min(), V[f, 1].max(),
                  V[f, 2].min(), V[f, 2].max()))
    # 前 8 个顶点的 uv
    out.append("   前 8 个顶点 uv: %s"
               % ["(%.4f,%.4f)" % (UV[i, 0], UV[i, 1]) for i in f[:8]])
    # uv 唯一值个数
    out.append("   去重后 uv 组合数 = %d（顶点 %d）"
               % (len(set((round(UV[i, 0], 5), round(UV[i, 1], 5)) for i in f)), len(f)))
    out.append("")

txt = "\n".join(out)
print(txt)
p = os.path.join(HERE, "report_sclera_uv.txt")
i = 2
while os.path.exists(p):
    p = os.path.join(HERE, "report_sclera_uv_%d.txt" % i)
    i += 1
open(p, "w", encoding="utf-8").write(txt + "\n")
print("-> %s" % p)
