# -*- coding: utf-8 -*-
"""adjacencies.csv 内容 + positions.txt 覆盖检查"""
import os, re, sys, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
VAN = r'F:\Steam\steamapps\common\Hearts of Iron IV'

print('=== mod adjacencies.csv 全文 ===')
print(open(os.path.join(G, 'map', 'adjacencies.csv'), encoding='utf-8-sig', errors='replace').read())
print('=== 原版 adjacencies.csv 前 5 行 ===')
vo = open(os.path.join(VAN, 'map', 'adjacencies.csv'), encoding='utf-8-sig', errors='replace').read().split('\n')
for l in vo[:5]:
    print('  ', l[:100])
print(f'  原版总行数 {len(vo)}')

# positions.txt 覆盖
rgb2id, kind = {}, {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
        kind[int(a[0])] = a[4]
arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
plut = np.zeros(len(uniq), np.int32)
for i, k in enumerate(uniq):
    k = int(k)
    plut[i] = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = plut[inv].reshape(H, W)
have = set()
pt = open(os.path.join(G, 'map', 'positions.txt'), encoding='utf-8-sig', errors='replace').read()
for m in re.finditer(r'(?m)^(\d+)=\{', pt):
    have.add(int(m.group(1)))
allp = set(np.unique(prov).tolist()) - {0}
missing = sorted(allp - have)
extra = sorted(have - allp)
print(f'\n=== positions.txt ===')
print(f'  条目 {len(have)}；位图省 {len(allp)}；缺失 {len(missing)} {missing[:10]}；多余 {len(extra)}')
