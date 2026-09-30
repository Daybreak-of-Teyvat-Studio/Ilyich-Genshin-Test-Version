# -*- coding: utf-8 -*-
"""① 22 省转省 ② 9 组州合并（源州全省并入目标州，源州清空）"""
import os, re, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
TOOL = os.path.join(ROOT, 'tools', 'gamma_state_edits.py')

# ① 转省
MOVES = ("2244+628.2213,3986+653.1403,4039+637.682,4048+677.2156,4240+693."
         "587+706.779+648.1262,4032+660")
print('=== ① 转省 ===')
r = subprocess.run([sys.executable, TOOL, MOVES], capture_output=True, text=True,
                   encoding='utf-8', cwd=ROOT)
out = (r.stdout or '') + (r.stderr or '')
for l in out.split('\n'):
    if any(k in l for k in ('载入', '已写入', '备份', '同步', '校验', '!!', '跳过')):
        print('  ', l.strip()[:120])

# ② 合并：读转省后的源州省列表 → 拼指令
MERGES = [(131, [136, 856]), (535, [565]), (628, [636]), (693, [703, 727]),
          (753, [764]), (676, [695]), (699, [706]), (630, [641]), (76, [570, 574])]
ST = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'history', 'states')
s2p = {}
for f in os.listdir(ST):
    if f.endswith('.txt'):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
        s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]

cmd_parts = []
total = 0
for dst, srcs in MERGES:
    probs = []
    for s in srcs:
        probs += s2p[s]
    cmd_parts.append(','.join(map(str, probs)) + f'+{dst}')
    total += len(probs)
    print(f'  合并 {"+".join(map(str, srcs))} → {dst}（{len(probs)} 省）')
cmd = '.'.join(cmd_parts)
print(f'\n=== ② 合并（共 {total} 省）===')
r = subprocess.run([sys.executable, TOOL, cmd], capture_output=True, text=True,
                   encoding='utf-8', cwd=ROOT)
out = (r.stdout or '') + (r.stderr or '')
for l in out.split('\n'):
    if any(k in l for k in ('载入', '已写入', '备份', '同步', '校验', '!!')):
        print('  ', l.strip()[:120])
