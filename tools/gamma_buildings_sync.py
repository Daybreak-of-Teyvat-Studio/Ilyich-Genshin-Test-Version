# -*- coding: utf-8 -*-
"""
map/buildings.txt 同步器（供 gamma_state_edits.py 转省后调用）。

HOI4 的 map/buildings.txt 每条形如：
    <州id>;<建筑>;<x>;<y>;<z>;<旋转>;<末列>
**省是由坐标反查出来的**：像素 = (x, 2048 - z)（Z 轴向上、位图 Y 向下），
已用 positions.txt 验证 8021/8021 命中。

省一转州必须同步这张表，否则游戏 `BUILDING IGNORED!` 忽略该建筑，沿海省会变成
`coastal but has no port` 并崩溃。但**不能简单地把所有条目都改到新州**——那会让
原州丢掉「州级生成点」，游戏报 `no air base site / no rocket site /
no gun emplacement defined for state N` 并崩溃。

规则：
  · 州级生成点（每州数量恒定的类型）→ 留在原州，把位置挪到原州内最近的省
  · 其余（随省走的）→ 声明州改为新州

州级类型清单由数据判定得出：这些类型在原始表里每州数量恒定
（air_base / fuel_silo / radar_station / nuclear_reactor_spawn / rocket_site_spawn /
synthetic_refinery / stronghold_network 各 1；anti_air_building 3；
arms_factory / industrial_complex 各 6 —— 后三者按「随省走」处理也不会崩，
但为了不动工厂布局，这里只对游戏会校验的生成点做原地保留）。

对外接口：
    sync(moves, dry=False) -> dict      moves = {province_id: (old_state, new_state)}
"""
import os, re, sys, shutil, datetime, collections
import numpy as np

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
BP = os.path.join(G, 'map', 'buildings.txt')

# 游戏会在加载时校验「每州至少一个」的生成点类型
STATE_LEVEL = {'air_base', 'fuel_silo', 'radar_station', 'nuclear_reactor_spawn',
               'rocket_site_spawn', 'synthetic_refinery', 'stronghold_network',
               'anti_air_building'}

_geom = None


def _load_geom():
    global _geom
    if _geom:
        return _geom
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    rgb2id, kind = {}, {}
    for line in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig',
                     errors='replace'):
        a = line.split(';')
        if len(a) > 6 and a[0].strip().isdigit():
            rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = int(a[0])
            kind[int(a[0])] = a[4]
    arr = np.asarray(Image.open(os.path.join(G, 'map', 'provinces.bmp'))
                     .convert('RGB')).astype(np.uint32)
    H, W = arr.shape[:2]
    key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
    uniq, inv = np.unique(key, return_inverse=True)
    plut = np.zeros(len(uniq), np.int32)
    for i, k in enumerate(uniq):
        k = int(k)
        plut[i] = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
    prov = plut[inv].reshape(H, W)
    ST = os.path.join(G, 'history', 'states')
    p2s, s2p = {}, collections.defaultdict(list)
    for f in os.listdir(ST):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
        for p in re.findall(r'\d+', re.search(r'provinces = \{([^}]*)\}', t).group(1)):
            p2s[int(p)] = sid
            s2p[sid].append(int(p))
    ptxt = open(os.path.join(G, 'map', 'positions.txt'), encoding='utf-8-sig',
                errors='replace').read()
    POS = {}
    for m in re.finditer(r'(?m)^(\d+)=\{\s*position=\{\s*([\d.\-]+) ([\d.\-]+) ([\d.\-]+)',
                         ptxt):
        POS[int(m.group(1))] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
    _geom = (prov, kind, p2s, s2p, POS, H, W)
    return _geom


def _prov_at(x, z, prov, kind, H, W, rad=1):
    xi, yi = int(round(x)), int(round(H - z))
    if 0 <= xi < W and 0 <= yi < H:
        p = int(prov[yi, xi])
        if p and kind.get(p) == 'land':
            return p
    for d in range(1, rad + 1):
        for dy in range(-d, d + 1):
            for dx in range(-d, d + 1):
                if max(abs(dx), abs(dy)) != d:
                    continue
                yy, xx = yi + dy, xi + dx
                if 0 <= xx < W and 0 <= yy < H:
                    q = int(prov[yy, xx])
                    if q and kind.get(q) == 'land':
                        return q
    return 0


def sync(moves, dry=False, verbose=True, state_map=None):
    """moves = {province_id: (old_state, new_state)}
    state_map 可选：调用方在内存里的 省->州 映射（转省未写盘时磁盘上是旧的）"""
    if not moves:
        return {}
    prov, kind, p2s_disk, s2p, POS, H, W = _load_geom()
    p2s = state_map if state_map is not None else p2s_disk
    for p, (old, new) in moves.items():
        if p2s.get(p) != new:
            raise ValueError(f'省 {p} 的州现值 {p2s.get(p)} != 预期 {new}，moves 参数不对')

    def nearest_in(state, p):
        px, _, pz = POS.get(p, (2048, 0, 1024))
        c = [q for q in s2p[state] if q in POS and q != p]
        c.sort(key=lambda q: (POS[q][0] - px) ** 2 + (POS[q][2] - pz) ** 2)
        return c

    raw = open(BP, 'rb').read()
    if raw[:3] == b'\xef\xbb\xbf':
        raise ValueError('buildings.txt 带 BOM，先处理')
    lines = raw.decode('utf-8').split('\r\n')
    used = collections.defaultdict(collections.Counter)
    n_reloc = n_reown = 0
    for i, l in enumerate(lines):
        if not l.strip():
            continue
        f = l.split(';')
        if len(f) != 7:
            continue
        st, bt, x, z = int(f[0]), f[1], float(f[2]), float(f[4])
        p = _prov_at(x, z, prov, kind, H, W, 1)
        if p not in moves or st != moves[p][0]:
            continue
        old, new = moves[p]
        if bt in STATE_LEVEL:
            cands = nearest_in(old, p)
            if not cands:
                continue
            q = cands[used[(old, bt)][p] % len(cands)]
            used[(old, bt)][p] += 1
            qx, qy, qz = POS[q]
            f[2], f[3], f[4] = f'{qx:.2f}', f'{qy:.2f}', f'{qz:.2f}'
            n_reloc += 1
        else:
            f[0] = str(new)
            n_reown += 1
        lines[i] = ';'.join(f)
    if not (n_reloc or n_reown):
        if verbose:
            print('buildings.txt 无需同步')
        return {}
    if verbose:
        print(f'buildings.txt 同步：州级生成点挪位置 {n_reloc} 条，随省改州 {n_reown} 条')
    if not dry:
        bdir = os.path.join(ROOT, '.backups',
                            'map_buildings_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(bdir, exist_ok=True)
        shutil.copy2(BP, os.path.join(bdir, 'buildings.txt'))
        with open(BP, 'w', encoding='utf-8', newline='') as fh:
            fh.write('\r\n'.join(lines))
        if verbose:
            print(f'  buildings.txt 已写入，备份 {bdir}')
    return {'relocated': n_reloc, 'reowned': n_reown}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print(__doc__)
