# -*- coding: utf-8 -*-
"""中轴链落点探测：列出脊柱各源骨的落点 y 与目标 y，找位移台阶。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pmx_parse import PMX  # noqa: E402

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
S = 0.389774
# 从 build_report 抄的 R（近似：y' = .9985y + .0544z, z' = -.0544y + .9985z）
R = np.array([[1.0, 0.0, 0.0], [0.0, 0.9985, -0.0544], [0.0, -0.0544, 0.9985]])
T = np.array([0.0, -0.0614, 0.4709])

HOI4_REST = {
    "Hip": 3.9842, "back_mid": 4.5314, "head": 6.5045,
    "LeftShoulder": 5.8114, "LeftArm": 5.8690,
}
# 映射目标（从 vysna_build.by_name 的规则抄）
TARGET = {
    "センター": "Hip", "腰": "Hip", "下半身": "Hip", "グルーブ": "Hip",
    "上半身": "back_mid", "上半身1": "back_mid", "上半身2": "back_mid",
    "首": "head", "首1": "head", "頭": "head",
}


def main():
    pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
    rows = []
    out = []
    lines = []
    for b in pmx.bones:
        nm = b["name"]
        if nm not in TARGET:
            continue
        p = np.array(b["pos"], np.float64)
        y = (S * (R @ p))[1] + T[1]
        tgt = TARGET[nm]
        ty = HOI4_REST[tgt]
        lines.append((y, nm, tgt, y - ty))
    lines.sort()
    out.append("★ 中轴链：源骨落点 y  ->  目标骨 (目标 y)   需要位移 dy")
    for y, nm, tgt, dy in lines:
        out.append("    %-10s 落点 y=%6.3f  ->  %-9s (y=%6.3f)   dy=%+7.3f"
                   % (nm, y, tgt, HOI4_REST[tgt], -dy))
    out.append("")
    out.append("  说明：dy 是「这根骨要把顶点上移多少」。相邻骨 dy 相差越大，")
    out.append("        蒙皮权重切换处越容易出现位移台阶（几何被撕开/堆叠）。")
    # 头部几何的实际范围
    out.append("")
    out.append("  上下文中 HOI4 骨架：Hip y=3.984  back_mid y=4.531  head y=6.505")
    out.append("  → back_mid..head 跨 %.3f，就是「脖子+颅底」要填满的区间。" % (6.5045 - 4.5314))
    txt = "\n".join(out)
    print(txt)
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_spine_probe")
    n = 1
    while True:
        fn = "%s%s.txt" % (p, "" if n == 1 else "_%d" % n)
        try:
            fh = open(fn, "w", encoding="utf-8")
            break
        except PermissionError:
            n += 1
    fh.write(txt)
    fh.close()
    print("\n-> %s" % fn)


if __name__ == "__main__":
    main()
