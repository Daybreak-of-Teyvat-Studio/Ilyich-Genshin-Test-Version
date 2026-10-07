# -*- coding: utf-8 -*-
"""解析本地化（中文 + 英文），输出 loc.json = {key: [zh, en]}"""
import os, re, json, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")

MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
LOC = os.path.join(MOD, "localisation")
STG = os.path.dirname(os.path.abspath(__file__))

LINE = re.compile(r'^\s*([A-Za-z0-9_.]+):(?:\d+)?\s*"([^"]*)"')

def scan(subdir, idx):
    d = os.path.join(LOC, subdir)
    if not os.path.isdir(d): return 0
    n = 0
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith((".yml", ".yaml")): continue
        p = os.path.join(d, fn)
        raw = open(p, "rb").read()
        for enc in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
            try:
                txt = raw.decode(enc); break
            except Exception: continue
        else:
            continue
        for ln in txt.split("\n"):
            m = LINE.match(ln)
            if m:
                k, v = m.group(1), m.group(2)
                # 同key 多次出现（_desc 等），取第一个非空
                if k not in idx or (not idx[k] and v):
                    idx[k] = v
                n += 1
    return n

zh = {}; en = {}
print("中文条目:", scan("simp_chinese", zh))
print("英文条目:", scan("english", en))
# 顶层散yml
for fn in sorted(os.listdir(LOC)):
    if fn.lower().endswith((".yml", ".yaml")):
        raw = open(os.path.join(LOC, fn), "rb").read()
        try: txt = raw.decode("utf-8-sig")
        except Exception: continue
        for ln in txt.split("\n"):
            m = LINE.match(ln)
            if m and m.group(1) not in zh: zh[m.group(1)] = m.group(2)

keys = set(zh) | set(en)
out = {k: [zh.get(k, ""), en.get(k, "")] for k in keys}
json.dump(out, open(os.path.join(STG, "loc.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("合并 key数:", len(out))
# 抽样验证
for t in ("GFS_Instruction_of_Doing", "SAN_mobilize_watatsumi_militia", "NDK_Sliver_Moon", "MOT_Focus_II"):
    print(" ", t, "->", out.get(t))
