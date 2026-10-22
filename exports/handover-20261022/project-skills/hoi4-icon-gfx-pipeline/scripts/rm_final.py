# -*- coding: utf-8 -*-
"""按清单批量删除（单进程 os.remove，比 Bash 逐条 rm 快两个数量级）。

删的是「非规范名 PNG」—— 它们的权威副本都在 out_<TAG>_v7 / v8里，
外加磁盘上已存在的规范名大写版，删掉不丢内容。
"""
import os, sys, time

MOD = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
       r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version")
LST = r"C:\Users\XIANGZIYUAN\hoi4lint\icon_gen\stage4\_rm_norm_final.txt"
PROG = r"C:\Users\XIANGZIYUAN\hoi4lint\icon_gen\stage4\rm_final_progress.txt"

rels = [l.strip() for l in open(LST, encoding='utf-8') if l.strip()]
ok = skip = fail = 0
errs = []
t0 = time.time()
for i, rel in enumerate(rels, 1):
    p = os.path.join(MOD, rel.replace('/', os.sep))
    if not os.path.exists(p):
        skip += 1
        continue
    try:
        os.remove(p)
        ok += 1
    except Exception as e:
        fail += 1
        if len(errs) < 20:
            errs.append('%s : %s %s' % (rel, type(e).__name__, e))
    if i % 200 == 0:
        with open(PROG, 'w', encoding='utf-8') as f:
            f.write('%d/%d ok=%d skip=%d fail=%d %.0fs'
                    % (i, len(rels), ok, skip, fail, time.time() - t0))

with open(PROG, 'w', encoding='utf-8') as f:
    f.write('完成 %d/%d ok=%d skip=%d fail=%d %.0fs'
            % (len(rels), len(rels), ok, skip, fail, time.time() - t0))
print('清单 %d 条：删除 %d，已不存在 %d，失败 %d，耗时 %.1fs'
      % (len(rels), ok, skip, fail, time.time() - t0))
for e in errs:
    print('  %s' % e)