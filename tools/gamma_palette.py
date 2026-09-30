# -*- coding: utf-8 -*-
"""
配色表 —— 单一真源。其他脚本 import 这里的 COL / TAG_OF_COLOR。

重要：FROZEN 是主写已开始使用的第一版配色，**逐个冻结，绝不改动**。
ADDED 是后来补发现的 tag 的颜色，与已有色保持足够距离。

直接运行本文件会输出色板图/清单到 Gamma_地图/分界图层/。
"""
import os, re, sys, colorsys, collections

# ---------------- 第一版配色，原样冻结（已对照当时渲染的色板图逐个核对）----------------
FROZEN = {
    'MOT': '#E6194B', 'GUN': '#3CB44B', 'DVA': '#FFE119', 'RAG': '#4363D8',
    'LAW': '#F58231', 'FAV': '#911EB4', 'SPI': '#42D4F4', 'ANR': '#F032E6',
    'DRA': '#BFEF45', 'LYY': '#FABED4', 'BRF': '#469990', 'INA': '#DCBEFF',
    'SAN': '#9A6324', 'ASA': '#FFFAC8', 'TSU': '#800000', 'SUM': '#AAFFC3',
    'VAN': '#808000', 'SDH': '#FFD8B1', 'SGS': '#000075', 'SGD': '#A9A9A9',
    'SFG': '#F5A9B8', 'SGC': '#008080', 'SKD': '#C0C000', 'FON': '#7F00FF',
    'NAT': '#FF6600', 'NCE': '#00A651', 'NSC': '#00B4FF', 'NPS': '#FF0080',
    'NCP': '#8B4513', 'NFF': '#DAA520', 'NMN': '#6A5ACD', 'NDK': '#2E8B57',
    'SNE': '#B22222', 'PRI': '#4682B4', 'ABY': '#DDA0DD', 'HIL': '#556B2F',
}
# ---------------- 后补 tag 的颜色（已定）----------------
ADDED = {
    'KQP': '#FC0707', 'SHP': '#06DBB7', 'GYP': '#7CDB78', 'CYG': '#A4AD41',
    'YLH': '#323984', 'MHL': '#FCD45F', 'SDS': '#06DB29', 'HIP': '#198403',
    'FOD': '#841A4B', 'FOM': '#32FC7D', 'PBF': '#8AA3FC', 'SFS': '#71DB06',
    'HZH': '#3C05AD', 'VLM': '#0709FC',
}
COL = dict(FROZEN)
COL.update(ADDED)
TAG_OF_COLOR = {v.upper(): t for t, v in COL.items()}
assert len(TAG_OF_COLOR) == len(COL), '配色表有重复颜色'

# 显示分组
SHOW = [
    ('蒙德', ['MOT', 'GUN', 'DVA', 'RAG', 'LAW', 'FAV', 'SPI', 'ANR', 'DRA']),
    ('璃月', ['LYY', 'BRF', 'KQP', 'SHP', 'GYP', 'CYG', 'YLH']),
    ('稻妻', ['INA', 'SAN', 'ASA', 'TSU']),
    ('须弥', ['SUM', 'VAN', 'SDH', 'SGS', 'SGD', 'SFG', 'SGC', 'SKD']),
    ('枫丹', ['FON']),
    ('纳塔', ['NAT', 'NCE', 'NSC', 'NPS', 'NCP', 'NFF', 'NMN']),
    ('挪德卡莱', ['NDK']),
    ('至冬', ['SNE']),
    ('其他国家·非国家势力', ['PRI', 'ABY', 'HIL', 'MHL', 'SDS', 'HIP']),
    ('其他国家·枫丹系（不在 Is_FON 里）', ['FOD', 'FOM', 'PBF']),
    ('其他国家·至冬系（不在任何大区里）', ['SFS', 'HZH']),
    ('其他国家·须弥系（不在 Is_SUM 里）', ['VLM']),
]

# 须弥系 / 纳塔系（这批先不装）
SUM_FACTION = ['SUM', 'VAN', 'SDH', 'SGS', 'SGD', 'SFG', 'SGC', 'SKD', 'VLM']
NAT_FACTION = ['NAT', 'NCE', 'NSC', 'NPS', 'NCP', 'NFF', 'NMN']


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def check_distances():
    """返回 (全表最小差, 其 tag 对, 冻结色之间最小差, 其 tag 对, 新色vs冻结最小差)"""
    fz = list(FROZEN)
    nw = list(ADDED)
    allt = list(COL)
    m_all = min((dist(hx(COL[a]), hx(COL[b])), a, b)
                for i, a in enumerate(allt) for b in allt[i + 1:])
    m_fz = min((dist(hx(COL[a]), hx(COL[b])), a, b)
               for i, a in enumerate(fz) for b in fz[i + 1:])
    m_new = min((dist(hx(COL[a]), hx(COL[b])), a, b) for a in nw for b in fz)
    return m_all[0], m_all[1:], m_fz[0], m_fz[1:], m_new[0], m_new[1:]


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from gamma_regions import tag_cn, G, ROOT
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    Image.MAX_IMAGE_PIXELS = None

    OUT = os.path.join(ROOT, 'Gamma_地图', '分界图层')
    os.makedirs(OUT, exist_ok=True)
    FONT, FONTB = r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\msyhbd.ttc'
    ST = os.path.join(G, 'history', 'states')
    cnt = collections.Counter()
    for f in os.listdir(ST):
        t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
        cnt[re.search(r'\bowner\s*=\s*(\w+)', t).group(1)] += 1

    m_all, pa, m_fz, pb, m_new, pc = check_distances()
    print(f'总 tag {len(COL)}（冻结 {len(FROZEN)} + 新增 {len(ADDED)}）')
    print(f'全表最小色差 {m_all:.1f}（{pa[0]} vs {pa[1]}，都是冻结色）')
    print(f'冻结色之间最小 {m_fz:.1f}（{pb[0]} vs {pb[1]}）')
    print(f'新色 vs 冻结最小 {m_new:.1f}（{pc[0]} vs {pc[1]}）')
    print('新增色: ' + '  '.join(f'{t}={tag_cn(t)}{COL[t]}' for t in ADDED))
    print('须弥系:', ' '.join(SUM_FACTION))
    print('纳塔系:', ' '.join(NAT_FACTION))

    CW, ROWH = 620, 27
    rows, cur, laid = 0, 0, []
    for head, tags in SHOW:
        if cur:
            rows += 1; cur = 0
        laid.append(('h', head, 0, rows)); rows += 1
        for t in tags:
            laid.append(('i', t, cur, rows))
            cur += 1
            if cur >= 2:
                cur = 0; rows += 1
    if cur:
        rows += 1
    W, H = 24 * 2 + CW * 2, 76 + rows * ROWH + 20
    img = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    f0 = ImageFont.truetype(FONTB, 22)
    f1 = ImageFont.truetype(FONTB, 17)
    f2 = ImageFont.truetype(FONT, 15)
    f3 = ImageFont.truetype(FONT, 13)
    d.text((24, 16), '提瓦特黎明 Gamma 配色表', font=f0, fill=(15, 15, 15))
    d.text((24, 46), '★ = 后补的颜色；其余与第一版完全一致，请勿改动',
           font=f3, fill=(190, 40, 40))
    for kind, val, col, row in laid:
        x, y = 24 + col * CW, 76 + row * ROWH
        if kind == 'h':
            d.rectangle([x, y + 3, x + CW * 2 - 40, y + ROWH + 2], fill=(238, 240, 246))
            d.text((x + 8, y + 5), val, font=f1, fill=(30, 50, 110))
        else:
            t = val
            n = cnt.get(t, 0)
            new = t in ADDED
            d.rectangle([x, y + 3, x + 44, y + 22], fill=hx(COL[t]), outline=(90, 90, 90))
            label = ('★ ' if new else '   ') + f'{tag_cn(t)}  {t}   {COL[t]}'
            d.text((x + 54, y + 5), label, font=f2,
                   fill=(190, 40, 40) if new else (15, 15, 15))
            wt = f'州数 {n}' if n else '〔无地〕'
            d.text((x + 54 + d.textlength(label, font=f2) + 10, y + 6), wt, font=f3,
                   fill=(120, 120, 120) if n else (200, 30, 30))
    img.save(os.path.join(OUT, '色板_配色表.png'))

    lines = ['# 提瓦特黎明 Gamma 配色表', '# ★ = 后补色；其余与第一版一致', '']
    for kind, val, *_ in laid:
        if kind == 'h':
            lines += ['', f'[{val}]']
        else:
            t = val
            lines.append(f'{"★" if t in ADDED else " "} {t:4s} {tag_cn(t):14s} {COL[t]}'
                         f'   州数 {cnt.get(t,0)}')
    open(os.path.join(OUT, '色板_配色表.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
    print('已出: 色板_配色表.png / .txt  -> ', OUT)


if __name__ == '__main__':
    main()
