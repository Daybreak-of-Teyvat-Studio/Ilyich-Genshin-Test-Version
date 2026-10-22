# -*- coding: utf-8 -*-
import os, io, re, sys
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
OUT = os.path.join(REPO, 'tools', 'loc_migr_out.txt')
o = []

# 0) 重名检查：遗迹巨像 是否已被别的州用
LOC = 'DOT_state_names_gamma_l_simp_chinese.yml'
t = io.open(os.path.join(G, 'localisation', 'simp_chinese', LOC), 'rb').read().decode('utf-8-sig')
dup = [l.strip()[:100] for l in t.splitlines() if '遗迹巨像' in l]
o.append(f'「遗迹巨像」现有出现行: {dup}')

# 1) 迁移：DOT_STATE_63 的 * → 遗迹巨像；DOT_STATE_703 → *
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'localisation', 'simp_chinese', LOC)
    raw = io.open(fp, 'rb').read()
    bom = raw[:3] == bytes([0xef, 0xbb, 0xbf])
    tt = raw.decode('utf-8-sig')
    # 63 ← 遗迹巨像（若 63 还是 *）
    tt2, n1 = re.subn(r'(DOT_STATE_63:\d*\s*)"\*"', r'\g<1>"遗迹巨像"', tt)
    # 703 → *（若 703 是 遗迹巨像）
    tt2, n2 = re.subn(r'(DOT_STATE_703:\d*\s*)"遗迹巨像"', r'\g<1>"*"', tt2)
    io.open(fp, 'wb').write((bytes([0xef, 0xbb, 0xbf]) if bom else b'') + tt2.encode('utf-8'))
    o.append(f'{label}: 63→遗迹巨像({n1}), 703→*({n2})')
    # 复读
    chk = io.open(fp, 'rb').read().decode('utf-8-sig')
    for l in chk.splitlines():
        if re.match(r'\s*DOT_STATE_(63|703):', l):
            o.append('   ' + l.strip()[:90])

# 2) 双副本一致
a = io.open(os.path.join(G, 'localisation', 'simp_chinese', LOC), 'rb').read()
b = io.open(os.path.join(DEPL, 'localisation', 'simp_chinese', LOC), 'rb').read()
o.append(f'双副本一致: {a == b}; BOM={a[:3] == bytes([0xef,0xbb,0xbf])}, CRCRLF={a.count(bytes([13,13,10]))}')

# 3) 我这批 20 个州的核心检查（确认不在 C-91 里）
o.append('')
o.append('===== 我批次 20 州 owner/core =====')
sd = os.path.join(G, 'history', 'states')
for sid in (381, 390, 392, 404, 411, 412, 422, 433, 451, 464, 466, 467, 474, 482, 483, 484, 500, 510, 511, 524):
    tt = io.open(os.path.join(sd, f'{sid}-State_{sid}.txt'), 'rb').read().decode('utf-8-sig')
    ow = re.search(r'owner\s*=\s*(\w+)', tt)
    cores = re.findall(r'add_core_of\s*=\s*(\w+)', tt)
    flag = '' if (ow and cores == [ow.group(1)]) else '  ⚠'
    o.append(f'  s{sid}: owner={ow.group(1) if ow else "?"} cores={cores}{flag}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))
