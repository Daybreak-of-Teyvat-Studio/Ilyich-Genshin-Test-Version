# -*- coding: utf-8 -*-
"""dump 薇斯纳.pmx 的骨骼清单（名字/父/位置），并按关键词分类统计受影响顶点。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pmx_parse import PMX  # noqa

SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_bones.txt")

pmx = PMX(os.path.join(SRC, "薇斯纳.pmx"))
L = []
P = L.append

# 顶点权重统计
cnt = np.zeros(len(pmx.bones), dtype=np.int64)
for i in range(pmx.vcount):
    for b, w in zip(pmx.v_wbone[i], pmx.v_wweight[i]):
        if b >= 0 and w > 1e-6:
            cnt[b] += 1

P("骨骼总数 %d" % len(pmx.bones))
P("%-5s %-28s %-6s %-22s %-8s %s" % ("idx", "name", "parent", "pos", "顶点数", "flag"))
for b in pmx.bones:
    P("%-5d %-28s %-6d (%7.3f,%7.3f,%7.3f) %-8d 0x%04x" % (
        b["index"], b["name"], b["parent"],
        b["pos"][0], b["pos"][1], b["pos"][2], cnt[b["index"]], b["flag"]))

# 只列有顶点影响的
P("")
P("=" * 60)
P("有顶点影响的骨骼（按顶点数降序）:")
order = np.argsort(-cnt)
for i in order:
    if cnt[i] == 0:
        break
    P("  %-6d %-28s %8d" % (i, pmx.bones[i]["name"], cnt[i]))

txt = "\n".join(L)
open(OUT, "w", encoding="utf-8").write(txt)
print("总骨骼 %d，有影响的 %d" % (len(pmx.bones), int((cnt > 0).sum())))
print("\n".join(L[:5]))
print("...")
print("\n".join(L[-60:]))
