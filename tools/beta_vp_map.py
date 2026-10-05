# -*- coding: utf-8 -*-
"""
Beta 版 Province 级 + 胜利点名称标注图（按国家分图）
  · 底图：provinces.bmp 渲染（陆地白/海蓝灰）
  · 线条：省界（细浅灰线）+ 州界（深灰线）
  · 标注：胜利点名称（省质心处）+ VP 值
  · 州界线保留但**不标注州名**
  · 全图 2 倍分辨率 + 按国家裁剪子图
"""
import os, re, sys, math, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
BETA = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
OUTDIR = os.path.join(ROOT, 'Beta_VP标注图')
os.makedirs(OUTDIR, exist_ok=True)
Z = 2
FONT_SIZE = 11

# ===== 数据加载 =====
ST = os.path.join(BETA, 'history', 'states')
LOC = os.path.join(BETA, 'localisation', 'simp_chinese')

# 州数据
s2p, s2o, s2vp, s2nm = {}, {}, {}, {}
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
    nm = re.search(r'name\s*=\s*"([^"]*)"', t)
    s2nm[sid] = nm.group(1) if nm else ''

p2s = {}
for s, ps in s2p.items():
    for p in ps:
        p2s[p] = s

# VP 本地化名
sn_path = os.path.join(LOC, 'DOT_state_names_gamma_l_simp_chinese.yml')
vpf_path = os.path.join(LOC, 'DOT_Victory_Points_l_simp_chinese.yml')
vp_names = {}
vpf_raw = open(vpf_path, 'rb').read()
vpf_t = vpf_raw.decode('utf-8-sig' if vpf_raw[:3] == b'\xef\xbb\xbf' else 'utf-8',
                       errors='replace')
for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s+"([^"]*)"', vpf_t, re.M):
    vp_names[int(m.group(1))] = m.group(2)

# Beta 本地化（州名 → 中文）
beta_loc = os.path.join(BETA, 'localisation', 'simp_chinese')
beta_loc_names = {}
for lf in [os.path.join(beta_loc, f) for f in os.listdir(beta_loc) if f.endswith('.yml')]:
    try:
        t = open(lf, encoding='utf-8-sig', errors='replace').read()
        for m in re.finditer(r'^\s*(STATE_\d+):\d*\s+"([^"]*)"', t, re.M):
            beta_loc_names[m.group(1)] = m.group(2)
    except Exception:
        pass

# definition.csv
defs = {}
for line in open(os.path.join(BETA, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = line.split(';')
    if len(a) > 6 and a[0].strip().isdigit():
        defs[int(a[0])] = (int(a[1]), int(a[2]), int(a[3]), a[4])
rgb2id = { (v[0], v[1], v[2]): pid for pid, v in defs.items() }

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
flat = prov.ravel()
npx = np.bincount(flat, minlength=int(prov.max()) + 2)
gx = np.tile(np.arange(W, dtype=np.float64), H)
gy = np.repeat(np.arange(H, dtype=np.float64), W)
cx = np.bincount(flat, weights=gx, minlength=len(npx)) / np.maximum(npx, 1)
cy = np.bincount(flat, weights=gy, minlength=len(npx)) / np.maximum(npx, 1)

# 国家分组
TAG_CN = {
    'MOT': '蒙德', 'DVA': '风龙领', 'RAG': '莱艮芬德领', 'LAW': '前劳伦斯领',
    'GUN': '古恩希尔德领', 'FAV': '西风教会', 'SPI': '清泉镇', 'ANR': '奔狼领',
    'DRA': '龙脊雪山', 'LYY': '璃月', 'BRF': '黑岩厂', 'KQP': '沉玉谷',
    'SHP': '上风蚀地', 'GYP': '孤云阁', 'CYG': '沉玉谷·上', 'YLH': '玉陵',
    'INA': '稻妻', 'SAN': '珊瑚宫', 'ASA': '清濑神社', 'TSU': '鹤观',
    'SUM': '须弥', 'VAN': '桓那兰那', 'SDH': '千壑沙地', 'SGS': '苍漠囿土',
    'SGD': '饰金砂原', 'FON': '枫丹', 'NAT': '纳塔', 'NCE': '回声之子',
    'NSC': '悬木人', 'NPS': '流泉之众', 'NCP': '沃陆之邦', 'NFF': '花羽会',
    'NMN': '烟谜主', 'NDK': '挪德卡莱', 'SNE': '至冬', 'PRI': '天理',
    'ABY': '深渊教团', 'HIL': '丘丘部落联盟', 'MHL': '丘丘部落',
    'SDS': '至冬南方领', 'HIL': '丘丘部落联盟',
}
# 补充
TAG_CN.update({'ASA': '清濑神社', 'TSU': '鹤观会', 'HIL': '丘丘部落联盟',
               'SDS': '至冬南方领', 'SFG': '沙之海', 'SGC': '沙之海·东', 'SKD': '沙之海·西'})

countries = collections.defaultdict(list)
for s, o in s2o.items():
    if o and s2p[s]:
        countries[o].append(s)

print(f'Beta 州 {len(s2p)} | 国家 {len(countries)} | VP 总数 {sum(len(v) for v in s2vp.values())}')

# ===== 渲染 =====
# 全图底色
base = np.full((H, W, 3), (225, 232, 240), np.uint8)
land_mask = np.isin(prov, [p for p, (r, g, b, k) in defs.items() if k == 'land'])
base[land_mask] = (250, 250, 250)

# 州界线（深灰）
state_arr = np.zeros_like(prov)
for s, ps in s2p.items():
    state_arr[prov == ps[0] if False else np.isin(prov, ps)] = s
sb = np.zeros((H, W), bool)
sb[:, 1:] |= (state_arr[:, 1:] != state_arr[:, :-1])
sb[1:, :] |= (state_arr[1:, :] != state_arr[:-1, :])
sb &= land_mask
base[sb] = (100, 100, 105)

# 省界线（浅灰细线）
pb = np.zeros((H, W), bool)
pb[:, 1:] |= (prov[:, 1:] != prov[:, :-1])
pb[1:, :] |= (prov[1:, :] != prov[:-1, :])
pb &= land_mask & ~sb
base[pb] = (215, 215, 218)

# VP 标记（小红点）
vp_pos = {}
for sid, vps in s2vp.items():
    for pid, val in vps:
        if pid in cx and npx[pid] > 0:
            vp_pos[pid] = (cx[pid], cy[pid])

img = Image.fromarray(base, 'RGB').resize((W * Z, H * Z), Image.NEAREST)
d = ImageDraw.Draw(img)
font = ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc', FONT_SIZE)
font_bold = ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc', FONT_SIZE)

# VP 标注
for pid, (vx, vy) in sorted(vp_pos.items()):
    tx, ty = vx * Z, vy * Z
    loc_nm = vp_names.get(pid, '')
    # 找值
    val = ''
    for s, vps in s2vp.items():
        for p, v in vps:
            if p == pid:
                val = str(v)
                break
    if loc_nm:
        label = f'{loc_nm}({val})' if val else loc_nm
    else:
        label = f'VP{pid}({val})' if val else f'VP{pid}'
    d.text((tx, ty), label, font=font, fill=(180, 30, 30), anchor='mm',
           stroke_width=2, stroke_fill=(255, 255, 255))

# 全图保存
full_out = os.path.join(OUTDIR, 'Beta全图_VP标注.png')
img.save(full_out)
print(f'全图: {full_out} ({W*Z}x{H*Z})')

# 按国家裁剪子图
print('\n=== 按国家裁剪 ===')
for tag in sorted(countries):
    cn = TAG_CN.get(tag, tag)
    sts = countries[tag]
    all_p = [p for s in sts for p in s2p[s]]
    if not all_p:
        continue
    xs = [cx[p] for p in all_p if npx[p] > 0]
    ys = [cy[p] for p in all_p if npx[p] > 0]
    if not xs:
        continue
    margin = 30
    x0, x1 = max(0, int(min(xs) - margin)), min(W, int(max(xs) + margin))
    y0, y1 = max(0, int(min(ys) - margin)), min(H, int(max(ys) + margin))
    crop = img.crop((x0 * Z, y0 * Z, x1 * Z, y1 * Z))
    fn = f'Beta_{cn}_VP标注.png'
    fp = os.path.join(OUTDIR, fn)
    crop.save(fp)
    print(f'  {fn}  ({crop.size[0]}x{crop.size[1]})  {len(sts)} 州 {len(all_p)} 省')

print(f'\n输出目录: {OUTDIR}')
