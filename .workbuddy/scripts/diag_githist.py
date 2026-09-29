# -*- coding: utf-8 -*-
"""用 git 历史逐个版本，检验 buildings.txt 与同版本 provinces.bmp 的吻合度。
结论若是某个版本吻合、后续版本不吻合 → 说明地图被改而 buildings 没跟着改。"""
import subprocess, struct, os, sys, collections
import numpy as np

ROOT = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version'
G = 'Daybreak of Teyvat Gamma Version'
OUT = os.path.join(ROOT, '.workbuddy', 'report_githist.txt')
TMP = os.path.join(ROOT, '.workbuddy', 'tmp_git')
os.makedirs(TMP, exist_ok=True)

L = []
def P(*a):
    L.append(' '.join(str(x) for x in a))

def sh(*args):
    r = subprocess.run(args, cwd=ROOT, capture_output=True)
    return r.stdout

def cat(commit, path):
    r = subprocess.run(['git', 'cat-file', 'blob', f'{commit}:{G}/{path}'],
                       cwd=ROOT, capture_output=True)
    return r.stdout if r.returncode == 0 else None

def bmp_info(raw):
    o = struct.unpack_from('<I', raw, 10)[0]
    W, H = struct.unpack_from('<ii', raw, 18)
    bpp = struct.unpack_from('<H', raw, 28)[0]
    return o, W, H, bpp

def load_pids(raw):
    o, W, H, bpp = bmp_info(raw)
    if bpp != 24:
        return None, W, H, bpp
    rb = W * 3
    a = np.frombuffer(raw, dtype=np.uint8, offset=o)[:rb * H].reshape(H, W, 3)
    return (a[:, :, 2].astype(np.int32) << 16) | (a[:, :, 1].astype(np.int32) << 8) | a[:, :, 0].astype(np.int32), W, H, bpp

def defmap(raw):
    m = {}
    for ln in raw.decode('utf-8', 'replace').splitlines():
        f = ln.strip().split(';')
        if len(f) >= 5:
            try:
                m[(int(f[1]) << 16) | (int(f[2]) << 8) | int(f[3])] = int(f[0])
            except ValueError:
                pass
    return m

commits = ['f918069a', '1c81cfd2', '43bdcede', 'dc17d022', 'ceea236d', 'c306a543', '1d2edb03', '5074d891']
P('commit        date              prov.bmp        buildings条数   命中率(row=z)  命中率(row=H-1-z)')
P('-' * 110)
for c in commits:
    pr = cat(c, 'map/provinces.bmp')
    br = cat(c, 'map/buildings.txt')
    dr = cat(c, 'map/definition.csv')
    dt = sh('git', 'log', '-1', '--format=%ci', c).decode().strip()
    if pr is None or br is None or dr is None:
        P(f'{c}  {dt}  [缺文件] prov={pr is not None} build={br is not None} def={dr is not None}')
        continue
    pids, W, H, bpp = load_pids(pr)
    if pids is None:
        P(f'{c}  {dt}  provinces.bmp 非24bpp ({bpp})')
        continue
    dmap = defmap(dr)
    tot = h1 = h2 = 0
    for ln in br.decode('utf-8', 'replace').splitlines():
        f = ln.strip().split(';')
        if len(f) < 6:
            continue
        try:
            pid = int(f[0]); x = float(f[2]); z = float(f[4])
        except ValueError:
            continue
        tot += 1
        c1 = int(x); r1 = int(z)
        c2 = int(x); r2 = H - 1 - int(z)
        if 0 <= c1 < W and 0 <= r1 < H and dmap.get(int(pids[r1, c1])) == pid:
            h1 += 1
        if 0 <= c2 < W and 0 <= r2 < H and dmap.get(int(pids[r2, c2])) == pid:
            h2 += 1
    if tot == 0:
        P(f'{c}  {dt}  {W}x{H}({bpp}bpp)  buildings 无可解析行')
    else:
        P(f'{c}  {dt}  {W}x{H}({bpp}bpp)  {tot:>9,}   {100.0*h1/tot:>8.2f}%   {100.0*h2/tot:>10.2f}%')

open(OUT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L))
