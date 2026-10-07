# -*- coding: utf-8 -*-
"""写回进度核对（focus/idea 分目录正确比较）"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
STG = r"C:\Users\XIANGZIYUAN\hoi4lint\icon_gen\stage4"
MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\common"
OUT = os.path.join(STG, "out6")
DIRS = {"focus": "national_focus", "idea": "ideas"}

done = []; todo = []
for f in sorted(os.listdir(OUT)):
    kind, _, fn = f.partition("__")
    src = os.path.join(OUT, f)
    dst = os.path.join(MOD, DIRS[kind], fn)
    if not os.path.isfile(dst): todo.append((kind, fn, "目标缺失")); continue
    a = open(src, encoding="utf-8", errors="ignore", newline='').read()
    b = open(dst, encoding="utf-8", errors="ignore", newline='').read()
    (done if a == b else todo).append((kind, fn, "已写回" if a == b else "内容不一致"))

print("已写回 %d / %d" % (len(done), len(done)+len(todo)))
if todo:
    print("\n待处理:")
    for k, f, s in todo: print("  %-6s %-34s %s" % (k, f, s))
