# -*- coding: utf-8 -*-
"""轮 2：转省 5 组 + 命名（双读 1416/1442）"""
import os, re, sys, shutil, datetime, subprocess
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
TOOL = os.path.join(ROOT, 'tools', 'gamma_state_edits.py')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
SN = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')

# ① 转省
MOVES = "4321+746.4454+811.474,4361+771.434+796.45,310,1564,4411,4420+800"
print('=== ① 转省 ===')
r = subprocess.run([sys.executable, TOOL, MOVES], capture_output=True, text=True,
                   encoding='utf-8', cwd=ROOT)
out = (r.stdout or '') + (r.stderr or '')
for l in out.split('\n'):
    if any(k in l for k in ('载入', '转省 [', '省 ', '已写入', '备份', '同步', '校验', '!!', '跳过')):
        print('  ', l.strip()[:130])

# ② 命名
s2p, s2o = {}, {}
for f in os.listdir(ST):
    if f.endswith('.txt'):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
        mo = re.search(r'\bowner\s*=\s*(\w+)', t)
        s2o[sid] = mo.group(1) if mo else None
        s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
p2s = {p: s for s, ps in s2p.items() for p in ps}

NAMES = {761: '喀万驿', 774: '阿如村', 797: '活力之家', 771: '舍身陷坑', 796: '秘仪圣殿',
         800: '赤王陵', 833: '砾石之丘', 832: '避让之丘', 835: '荼柯落谷北',
         844: '荼柯落谷南', 816: '吞羊岩', 811: '舍身步道', 762: '饱饮之丘北',
         783: '饱饮之丘南'}
for pid, nm in ((1343, '迪弗旧窟'), (4216, '桓摩洞'), (1416, '雨的尽头'), (1442, '晴雨的经纬')):
    st = p2s.get(pid)
    print(f'  p{pid}「{nm}」 ∈ state {st}（{s2o.get(st)}）')
    if st:
        NAMES[st] = nm

s2all = set(s2p)
miss = [s for s in NAMES if s not in s2all]
assert not miss, f'州不存在: {miss}'
cur = open(SN, encoding='utf-8-sig', errors='replace').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)
bdir = os.path.join(ROOT, '.backups', 'names_desert2_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
shutil.copy2(SN, os.path.join(bdir, os.path.basename(SN)))
for s, nm in NAMES.items():
    names[s] = nm
lines = ['l_simp_chinese:'] + [f' DOT_STATE_{s}:0 "{names[s]}"' for s in sorted(names)]
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
raw = open(SN, 'rb').read()
print(f'\n=== ② 命名 {len(NAMES)} 个  BOM={raw[:3] == b"\xef\xbb\xbf"}  条数={len(names)}')
print(f'备份 {bdir}')
