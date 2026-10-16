# -*- coding: utf-8 -*-
import os, io, re, sys, hashlib, glob
sys.stdout.reconfigure(encoding='utf-8')

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BD = sorted([d for d in glob.glob(os.path.join(REPO, '.backups', 'vp_mond_*'))], key=os.path.getmtime)[-1]
OUT = os.path.join(REPO, 'tools', 'vp_verify_out.txt')
o = []

o.append(f'备份目录: {BD}')

# 1) 编辑过的州文件：双副本一致 + 内容
STATES = [381, 390, 392, 404, 411, 412, 422, 433, 451, 464, 466, 467, 474, 482, 483, 484, 500, 510, 511, 524]
o.append('')
o.append('===== 州文件双副本一致性 =====')
bad = []
for sid in STATES:
    fa = os.path.join(G, 'history', 'states', f'{sid}-State_{sid}.txt')
    fb = os.path.join(DEPL, 'history', 'states', f'{sid}-State_{sid}.txt')
    ha = hashlib.md5(io.open(fa, 'rb').read()).hexdigest()
    hb = hashlib.md5(io.open(fb, 'rb').read()).hexdigest()
    if ha != hb:
        bad.append(sid)
o.append(f'  不一致: {bad if bad else "无 ✓（20 个州全部一致）"}')

# 2) loc 文件核对
o.append('')
for rel in ('localisation/simp_chinese/DOT_Victory_Points_l_simp_chinese.yml',
            'localisation/simp_chinese/victory_points_l_simp_chinese.yml',
            'localisation/simp_chinese/DOT_Strategic_Region_Names_l_simp_chinese.yml'):
    for label, root in [('仓库', G), ('副本', DEPL)]:
        fp = os.path.join(root, rel.replace('/', os.sep))
        raw = io.open(fp, 'rb').read()
        bom = raw[:3] == bytes([0xef, 0xbb, 0xbf])
        crlf = raw.count(bytes([13, 10]))
        lone = raw.count(bytes([10])) - crlf
        crcrlf = raw.count(bytes([13, 13, 10]))
        tail = raw[-30:]
        o.append(f'  {label} {os.path.basename(rel)}: {len(raw)}B BOM={bom} CRLF={crlf} 独立LF={lone} CRCRLF={crcrlf}')
        o.append(f'      尾部: {tail!r}')
    a = io.open(os.path.join(G, rel.replace('/', os.sep)), 'rb').read()
    b = io.open(os.path.join(DEPL, rel.replace('/', os.sep)), 'rb').read()
    o.append(f'     双副本一致: {a == b}')

# 3) 关键条目抽查
o.append('')
t = io.open(os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Victory_Points_l_simp_chinese.yml'), 'rb').read().decode('utf-8-sig')
o.append('===== DOT_Victory_Points 抽查 =====')
for k in ('VICTORY_POINTS_292', 'VICTORY_POINTS_3481', 'VICTORY_POINTS_3456', 'VICTORY_POINTS_352', 'VICTORY_POINTS_1582', 'VICTORY_POINTS_2294'):
    for l in t.splitlines():
        if k + ':' in l:
            o.append('  ' + l.strip()[:100])
t2 = io.open(os.path.join(G, 'localisation', 'simp_chinese', 'victory_points_l_simp_chinese.yml'), 'rb').read().decode('utf-8-sig')
for l in t2.splitlines():
    if 'VICTORY_POINTS_352:' in l:
        o.append('  旧文件 ' + l.strip()[:100])
t3 = io.open(os.path.join(G, 'localisation', 'simp_chinese', 'DOT_Strategic_Region_Names_l_simp_chinese.yml'), 'rb').read().decode('utf-8-sig')
for l in t3.splitlines():
    if '马斯克' in l:
        o.append('  区域名 ' + l.strip()[:100])

# 4) 备份尾部对比（原文件结尾风格）
o.append('')
ob = io.open(os.path.join(BD, 'repo_DOT_Victory_Points.yml'), 'rb').read()
o.append(f'备份(改前) DOT_Victory_Points 尾部: {ob[-30:]!r}')
o.append(f'当前                尾部: {io.open(os.path.join(G, "localisation", "simp_chinese", "DOT_Victory_Points_l_simp_chinese.yml"), "rb").read()[-30:]!r}')
# 新追加的 29 行确认
o.append('')
o.append('===== 追加行确认（末 31 行） =====')
tail_lines = t.splitlines()[-31:]
for l in tail_lines:
    o.append('  ' + l[:110])

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')
print('\n'.join(o))
