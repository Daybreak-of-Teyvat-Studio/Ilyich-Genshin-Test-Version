# -*- coding: utf-8 -*-
"""写入 12 个州名（按 STATE 号解释，已双读验证）"""
import os, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
SN = os.path.join(G, 'localisation', 'simp_chinese', 'DOT_state_names_gamma_l_simp_chinese.yml')

NEW = {404: '荆夫港', 392: '疗养院旧址', 547: '星荧洞窟', 533: '雪葬之都·近郊',
       520: '眠龙谷', 521: '覆雪之路', 535: '雪葬之都·旧宫', 534: '雪山山顶',
       46: '无名岛', 68: '地中之盐', 78: '明蕴镇', 77: '瑶光滩'}

cur = open(SN, encoding='utf-8-sig', errors='replace').read()
names = {}
for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', cur, re.M):
    names[int(m.group(1))] = m.group(2)

# 存在性校验
sids = {}
for f in os.listdir(ST):
    if f.endswith('.txt'):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
        mo = re.search(r'\bowner\s*=\s*(\w+)', t)
        sids[sid] = mo.group(1) if mo else None
missing = [s for s in NEW if s not in sids]
assert not missing, f'州不存在: {missing}'

bdir = os.path.join(ROOT, '.backups', 'names12_' +
                    datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(bdir, exist_ok=True)
shutil.copy2(SN, os.path.join(bdir, os.path.basename(SN)))

print('=== 写入内容 ===')
for s, nm in sorted(NEW.items()):
    print(f'  state {s:4d}（{sids[s]}）: 「{names.get(s)}」 → 「{nm}」')
    names[s] = nm

lines = ['l_simp_chinese:'] + [f' DOT_STATE_{s}:0 "{names[s]}"' for s in sorted(names)]
open(SN, 'wb').write(b'\xef\xbb\xbf' + ('\r\n'.join(lines) + '\r\n').encode('utf-8'))
raw = open(SN, 'rb').read()
print(f'\nBOM={raw[:3] == b"\xef\xbb\xbf"}  CRLF={raw.count(bytes([13,10]))}/{raw.count(bytes([10]))}  条数={len(names)}')

txt = open(SN, encoding='utf-8-sig', errors='replace').read()
v = dict((int(m.group(1)), m.group(2)) for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', txt, re.M))
named = {k: x for k, x in v.items() if x != '*'}
print(f'\n=== 全部具名州 {len(named)} 个 ===')
for k in sorted(named):
    print(f'  state {k:4d}（{sids.get(k)}）: 「{named[k]}」')
print(f'\n备份 {bdir}')
