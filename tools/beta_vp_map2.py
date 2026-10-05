# -*- coding: utf-8 -*-
"""Beta Province 级 + 胜利点名称标注图（按国家分图）· 修复版
   VP 位置画可见标记（圆点+外圈），名字用大字号标注"""
import os, re, sys, shutil, math, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
BETA = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
OUTDIR = os.path.join(ROOT, 'Beta_VP标注图')
if os.path.exists(OUTDIR):
    shutil.rmtree(OUTDIR)
os.makedirs(OUTDIR, exist_ok=True)
Z = 2
FONT_VP = 14

ST = os.path.join(BETA, 'history', 'states')
LOC = os.path.join(BETA, 'localisation', 'simp_chinese')

# ===== 数据 =====
s2p, s2o, s2vp = {}, {}, {}
for f in sorted(os.listdir(ST)):
    if not f.endswith('.txt'):
        continue
    t = open(os.path.join(ST, f), encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    mo = re.search(r'\bowner\s*=\s*(\w+)', t)
    s2o[sid] = mo.group(1) if mo else None
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    s2p[sid] = [int(x) for x in pm.group(1).split()] if pm else []
    vm = re.search(r'victory_points\s*=\s*\{([^}]*)\}', t)
    vps = []
    if vm:
        v = vm.group(1).split()
        for i in range(0, len(v) - 1, 2):
            vps.append((int(v[i]), int(v[i + 1])))
    s2vp[sid] = vps
p2s = {}
for s, ps in s2p.items():
    for p in ps:
        p2s[p] = s

# VP 本地化
vp_names = {}
vp_file = os.path.join(LOC, 'DOT_Victory_Points_l_simp_chinese.yml')
if os.path.exists(vp_file):
    for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s+"([^"]*)"',
                         open(vp_file, encoding='utf-8-sig', errors='replace').read(), re.M):
        vp_names[int(m.group(1))] = m.group(2)

# definition
defs = {}
rgb2id = {}
for line in open(os.path.join(BETA, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        pid = int(a[0])
        defs[pid] = (int(a[1]), int(a[2]), int(a[3]), a[4])
        rgb2id[(int(a[1]), int(a[2]), int(a[3]))] = pid

# provinces.bmp
arr = np.asarray(Image.open(os.path.join(BETA, 'map', 'provinces.bmp')).convert('RGB')).astype(np.uint32)
H, W = arr.shape[:2]
key = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
uniq, inv = np.unique(key, return_inverse=True)
plut = np.zeros(len(uniq), np.int32)
for i, k in enumerate(uniq):
    k = int(k)
    plut[i] = rgb2id.get((k >> 16, (k >> 8) & 255, k & 255), 0)
prov = plut[inv].reshape(H, W)
land_mask = np.isin(prov, [p for p, d in defs.items() if d[3] == 'land'])
flat = prov.ravel()
npx = np.bincount(flat, minlength=int(prov.max()) + 2)
gx = np.tile(np.arange(W, dtype=np.float64), H)
gy = np.repeat(np.arange(H, dtype=np.float64), W)
cx = np.bincount(flat, weights=gx, minlength=len(npx)) / np.maximum(npx, 1)
cy = np.bincount(flat, weights=gy, minlength=len(npx)) / np.maximum(npx, 1)

# 州分组
countries = collections.defaultdict(list)
for s, o in s2o.items():
    if o and s2p[s]:
        countries[o].append(s)

# ===== 底图渲染 =====
base = np.full((H, W, 3), (228, 235, 242), np.uint8)
base[land_mask] = (252, 252, 250)

state_arr = np.zeros_like(prov)
for s, ps in s2p.items():
    state_arr[np.isin(prov, ps)] = s

# 州界（深灰）
sb = np.zeros((H, W), bool)
sb[:, 1:] |= (state_arr[:, 1:] != state_arr[:, :-1])
sb[1:, :] |= (state_arr[1:, :] != state_arr[:-1, :])
sb &= land_mask
base[sb] = (90, 90, 95)

# 省界（浅灰）
pb = np.zeros((H, W), bool)
pb[:, 1:] |= (prov[:, 1:] != prov[:, :-1])
pb[1:, :] |= (prov[1:, :] != prov[:-1, :])
pb &= land_mask & ~sb
base[pb] = (210, 210, 214)

# VP 省填色（淡红）
vp_provs = set()
for s, vps in s2vp.items():
    for pid, v in vps:
        vp_provs.add(pid)
for pid in vp_provs:
    if pid < len(npx) and npx[pid] > 0:
        mask = (prov == pid) & land_mask
        base[mask] = (255, 220, 220)

# ===== 2x 渲染 =====
img = Image.fromarray(base, 'RGB').resize((W * Z, H * Z), Image.NEAREST)
d = ImageDraw.Draw(img)
font_vp = ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc', FONT_VP)
font_st = ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc', 16)
font_st_b = ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc', 16)

# VP 标注（圆点 + 名字）
for sid, vps in s2vp.items():
    for pid, val in vps:
        if pid >= len(npx) or npx[pid] == 0:
            continue
        tx, ty = cx[pid] * Z, cy[pid] * Z
        loc_nm = vp_names.get(pid, f'VP{pid}')
        label = f'{loc_nm}({val})'
        # 圆点标记
        r_dot = 5
        d.ellipse([tx - r_dot, ty - r_dot, tx + r_dot, ty + r_dot],
                  fill=(200, 40, 40), outline=(255, 255, 255), width=2)
        # 名字标注（偏移避免与圆点重叠）
        d.text((tx + 8, ty - 12), label, font=font_vp,
               fill=(160, 20, 20), stroke_width=2, stroke_fill=(255, 255, 255))

# 州名不标注（用户要求：只显示 VP 名）

# ===== 全图保存 =====
full_path = os.path.join(OUTDIR, 'Beta全图_VP标注.png')
img.save(full_path)
print(f'全图: {full_path} ({W*Z}x{H*Z})')

# ===== 按国家裁剪 =====
print('\n=== 按国家裁剪 ===')
TAG_CN = {
    'MOT': '蒙德', 'DVA': '风龙领', 'RAG': '莱艮芬德领', 'LAW': '前劳伦斯领',
    'GUN': '古恩希尔德领', 'FAV': '西风教会', 'SPI': '清泉镇', 'ANR': '奔狼领',
    'DRA': '龙脊雪山', 'LYY': '璃月', 'BRF': '黑岩厂', 'KQP': '沉玉谷',
    'SHP': '上风蚀地', 'GYP': '孤云阁', 'CYG': '沉玉谷上', 'YLH': '玉陵',
    'INA': '稻妻', 'SAN': '珊瑚宫', 'ASA': '清濑神社', 'TSU': '鹤观',
    'SUM': '须弥', 'VAN': '桓那兰那', 'SDH': '千壑沙地', 'SGS': '苍漠囿土',
    'SGD': '饰金砂原', 'FON': '枫丹', 'NAT': '纳塔', 'NCE': '回声之子',
    'NSC': '悬木人', 'NPS': '流泉之众', 'NCP': '沃陆之邦', 'NFF': '花羽会',
    'NMN': '烟谜主', 'NDK': '挪德卡莱', 'SNE': '至冬', 'PRI': '天理',
    'ABY': '深渊教团', 'HIL': '丘丘部落联盟', 'MHL': '丘丘部落',
    'SDS': '至冬南方领', 'SFG': '沙之海', 'SGC': '沙之海东', 'SKD': '沙之海西',
}
for tag in sorted(countries):
    cn = TAG_CN.get(tag, tag)
    sts = countries[tag]
    all_p = [p for s in sts for p in s2p[s]]
    if not all_p:
        continue
    xs = [cx[p] for p in all_p if p < len(npx) and npx[p] > 0]
    ys = [cy[p] for p in all_p if p < len(npx) and npx[p] > 0]
    if not xs:
        continue
    margin = 30
    x0, x1 = max(0, int(min(xs) - margin)), min(W, int(max(xs) + margin))
    y0, y1 = max(0, int(min(ys) - margin)), min(H, int(max(ys) + margin))
    crop = img.crop((x0 * Z, y0 * Z, x1 * Z, y1 * Z))
    fn = f'Beta_{cn}_VP标注.png'
    crop.save(os.path.join(OUTDIR, fn))
    print(f'  {fn}  ({crop.size[0]}x{crop.size[1]})  {len(sts)} 州')

print(f'\n输出: {OUTDIR}')
