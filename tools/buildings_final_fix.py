# -*- coding: utf-8 -*-
"""最终合并修复：一次遍历，陆地条目→陆州、海上条目→海州，直接写回。"""
import os, re, sys, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')
BP = os.path.join(G, 'map', 'buildings.txt')

p2s = {}
for f in os.listdir(ST):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    for p in re.findall(r'\d+', re.search(r'provinces\s*=\s*\{([^}]*)\}', t).group(1)):
        p2s[int(p)] = sid

rgb2id = {}
for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
plut = np.zeros(len(uniq), np.int32)
for i, k in enumerate(uniq):
    k = int(k)
    plut[i] = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = plut[inv].reshape(H, W)

raw = open(BP, 'rb').read()
lines = raw.decode('utf-8').split('\r\n')
fixed = 0
for i, l in enumerate(lines):
    if not l.strip():
        continue
    f = l.split(';')
    if len(f) != 7:
        continue
    xi, yi = int(round(float(f[2]))), int(round(H - float(f[4])))
    if not (0 <= xi < W and 0 <= yi < H):
        continue
    p = int(prov[yi, xi])
    if p and p in p2s and int(f[0]) != p2s[p]:
        f[0] = str(p2s[p])
        lines[i] = ';'.join(f)
        fixed += 1

open(BP, 'w', encoding='utf-8', newline='').write('\r\n'.join(lines))
print(f'合并修复：{fixed} 条已改')

# 终验
mism = 0
for l in open(BP, encoding='utf-8-sig', newline='').read().split('\r\n'):
    if not l.strip():
        continue
    f = l.split(';')
    if len(f) != 7:
        continue
    xi, yi = int(round(float(f[2]))), int(round(H - float(f[4])))
    if not (0 <= xi < W and 0 <= yi < H):
        continue
    p = int(prov[yi, xi])
    if p and p in p2s and p2s[p] != int(f[0]):
        mism += 1
print(f'终验: 不符 {mism} 条')
