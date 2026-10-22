# -*- coding: utf-8 -*-
"""枫丹批：转省 2 + 命名 16 + 合并记下"""
import os, re, sys, shutil, datetime, subprocess
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
TOOL = os.path.join(ROOT, 'tools', 'gamma_state_edits.py')
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
SN = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')
ST = os.path.join(G, 'history', 'states')

# ① 转省
print('=== ① 转省 ===')
r = subprocess.run([sys.executable, TOOL, "330+43.1636+449"], capture_output=True,
                   text=True, encoding='utf-8', cwd=ROOT)
out = (r.stdout or '') + (r.stderr or '')
for l in out.split('\n'):
    if any(k in l for k in ('载入', '转省 [', '省 ', '已写入', '备份', '同步', '校验', '!!', '跳过')):
        print('  ', l.strip()[:130])

# ② 命名
NAMES = {69: '佩特莉可镇', 60: '海露港', 43: '白淞隧道', 449: '秋分山', 428: '白淞镇',
         439: '卡布狄斯堡遗迹', 16: '枫丹廷', 50: '茉洁站', 346: '欧庇克莱歌剧院',
         397: '露景泉', 54: '湖中垂柳', 389: '优兰尼娅湖', 38: '柔灯港',
         364: '新枫丹科学院', 357: '中央实验室遗址', 21: '幽林雾道'}
s2p = {}
for f in os.listdir(ST):
    if f.endswith('.txt'):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
        s2p[sid] = [int(x) for x in re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1).split()]
p2s = {p: s for s, ps in s2p.items() for p in ps}
for pid, nm in ((69, '佩特莉可镇'), (60, '海露港'), (43, '白淞隧道'), (449, '秋分山'),
                (428, '白淞镇'), (439, '卡布狄斯堡遗迹'), (16, '枫丹廷'), (50, '茉洁站'),
                (346, '欧庇克莱歌剧院'), (397, '露景泉'), (54, '湖中垂柳'),
                (389, '优兰尼娅湖'), (38, '柔灯港'), (364, '新枫丹科学院'),
                (357, '中央实验室遗址'), (21, '幽林雾道')):
    st = p2s.get(pid)
    own = None
    if st:
        t = open(os.path.join(ST, f'{st}-State_{st}.txt'), encoding='utf-8-sig',
                 errors='replace').read()
        mo = re.search(r'\bowner\s*=\s*(\w+)', t)
        own = mo.group(1) if mo else None
    print(f'  p{pid}「{nm}」∈ state {st}（{own}）')

cur = open(SN, encoding='utf-8-sig', newline='').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)
bdir = os.path.join(ROOT, '.backups', 'names_fontaine_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
shutil.copy2(SN, os.path.join(bdir, os.path.basename(SN)))
for s, nm in NAMES.items():
    names[s] = nm
lines = ['l_simp_chinese:'] + [f' DOT_STATE_{s}:0 "{names[s]}"' for s in sorted(names)]
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
raw = open(SN, 'rb').read()
print(f'\n命名 {len(NAMES)} 个写入  BOM={raw[:3] == b"\xef\xbb\xbf"}  条数={len(names)}')
print(f'备份 {bdir}')
print('\n=== 合并 16+31=16：记下暂不执行 ===')
