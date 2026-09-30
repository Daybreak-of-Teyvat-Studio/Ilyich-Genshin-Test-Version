# -*- coding: utf-8 -*-
"""操作日志重建：倒序处理备份，得到每次操作的精确增减（省进出）。"""
import os, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')


def read_state(path):
    t = open(path, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    ps = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
    mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    return sid, set(ps), (mo.group(1) if mo else None)


SNAP = {}          # sid -> set(provinces)  「较晚时刻」的快照
for f in os.listdir(ST):
    if f.endswith('.txt'):
        sid, ps, _ = read_state(os.path.join(ST, f))
        SNAP[sid] = ps

# 只处理 09-27（本会话）与 09-26 后期的州操作备份
dirs = [d for d in glob.glob(os.path.join(ROOT, '.backups', '*')) if os.path.isdir(d)]
dirs = [d for d in dirs if re.search(r'(gamma_states|state_rebalance|state_names|vp_|sea_state_fix)_\d{8}_\d{6}$',
                                     os.path.basename(d))]
dirs.sort(key=lambda d: os.path.basename(d).split('_')[-2:], reverse=True)

print('=== 操作日志（倒序重建，每行 = 一次写盘）===')
for b in dirs:
    name = os.path.basename(b)
    files = sorted(f for f in os.listdir(b) if f.endswith('.txt'))
    if not files:
        continue
    out_moves, in_moves, own_chg = [], [], []
    for f in files:
        sid, ps_before, own_before = read_state(os.path.join(b, f))
        ps_after = SNAP.get(sid, set())
        for p in ps_before - ps_after:
            out_moves.append(p)
        for p in ps_after - ps_before:
            in_moves.append(p)
        if own_before and sid in SNAP:
            cur_own = None
            t = open(os.path.join(ST, f'{sid}-State_{sid}.txt'), encoding='utf-8-sig',
                     errors='replace').read()
            mo = re.search(r'\bowner\s*=\s*(\w+)', t)
            cur_own = mo.group(1) if mo else None
            if cur_own and cur_own != own_before:
                own_chg.append(f'{sid}:{own_before}->{cur_own}')
        SNAP[sid] = ps_before          # 回退快照
    tag = ''
    if out_moves or in_moves:
        tag += f' 省移出 {len(out_moves)} 移入 {len(in_moves)}'
    if own_chg:
        tag += f' 归属改动 {own_chg}'
    if not tag:
        tag = ' （仅名称/VP 等非省变更）'
    print(f'  {name:44s} {len(files):4d} 文件{tag}')

print()
print('=== 本会话累计（09-27 的 gamma_states_* 批次）===')
tot_out = 0
for b in sorted(glob.glob(os.path.join(ROOT, '.backups', 'gamma_states_20260927_*'))):
    pass
