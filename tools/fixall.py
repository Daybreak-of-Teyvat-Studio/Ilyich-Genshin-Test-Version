import os, io, re, shutil

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
SORT46 = None
for d in os.listdir(os.path.join(REPO, '.backups')):
    if d.startswith('sort46_'):
        SORT46 = os.path.join(REPO, '.backups', d)
OUT = os.path.join(REPO, 'tools', 'fixall_out.txt')
o = []

# 0) 游戏是否在跑
import subprocess
r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    '(Get-Process hoi4 -ErrorAction SilentlyContinue | Measure-Object).Count'],
                   capture_output=True, text=True)
running = r.stdout.strip() != '0'
o.append(f'hoi4 进程数: {r.stdout.strip()}（running={running}）')

# 1) 修 airports/rocketsites 的 CRCRLF（双副本）
o.append('')
for name in ('airports.txt', 'rocketsites.txt'):
    for label, root in [('仓库', G), ('副本', DEPL)]:
        fp = os.path.join(root, 'map', name)
        raw = io.open(fp, 'rb').read()
        n = raw.count(bytes([13, 13, 10]))
        if n:
            fixed = raw.replace(bytes([13, 13, 10]), bytes([13, 10]))
            io.open(fp, 'wb').write(fixed)
            chk = io.open(fp, 'rb').read()
            o.append(f'{label} {name}: {n} 处 CRCRLF → 修复, 现 CRCRLF={chk.count(bytes([13,13,10]))}, CRLF={chk.count(bytes([13,10]))}, {len(chk)}B')
        else:
            o.append(f'{label} {name}: 无 CRCRLF ✓')

# 2) 修 LF-only 的文件（应为 CRLF）
o.append('')
for rel in ('localisation/simp_chinese/DOT_state_names_gamma_l_simp_chinese.yml',
            'history/countries/NCE - Children_of_Echoes.txt',
            'history/states/62-State_62.txt'):
    for label, root in [('仓库', G), ('副本', DEPL)]:
        fp = os.path.join(root, rel.replace('/', os.sep))
        if not os.path.exists(fp):
            o.append(f'{label} {rel}: 不存在')
            continue
        raw = io.open(fp, 'rb').read()
        crlf = raw.count(bytes([13, 10]))
        lf = raw.count(bytes([10]))
        bom = raw[:3] == bytes([0xef, 0xbb, 0xbf])
        if lf > crlf:
            body = raw[3:] if bom else raw
            fixed = body.replace(bytes([13, 10]), bytes([10])).replace(bytes([10]), bytes([13, 10]))
            fixed = (bytes([0xef, 0xbb, 0xbf]) if bom else b'') + fixed
            io.open(fp, 'wb').write(fixed)
            chk = io.open(fp, 'rb').read()
            o.append(f'{label} {os.path.basename(rel)}: LF-only → CRLF, BOM={chk[:3] == bytes([0xef,0xbb,0xbf])}, CRLF={chk.count(bytes([13,10]))}, 独立LF={chk.count(bytes([10])) - chk.count(bytes([13,10]))}')
        else:
            o.append(f'{label} {os.path.basename(rel)}: 已是 CRLF ✓ (BOM={bom})')

# 3) 恢复区域46（sort46 备份的仓库版 = 升序+weather+naval_terrain, 干净 CRLF）
o.append('')
src46 = os.path.join(SORT46, '仓库_46.txt') if SORT46 else None
o.append(f'sort46 备份: {SORT46}, 含仓库_46.txt={os.path.exists(src46) if src46 else False}')
if src46 and os.path.exists(src46):
    raw = io.open(src46, 'rb').read()
    # 确保干净 CRLF
    raw = raw.replace(bytes([13, 13, 10]), bytes([13, 10]))
    for label, root in [('仓库', G), ('副本', DEPL)]:
        dst = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_46.txt')
        io.open(dst, 'wb').write(raw)
        chk = io.open(dst, 'rb').read()
        t = chk.decode('utf-8-sig')
        provs = [int(x) for x in re.search(r'provinces=\{([^}]*)\}', t, re.S).group(1).split()]
        o.append(f'{label} 区域46 写入: {len(chk)}B, CRCRLF={chk.count(bytes([13,13,10]))}, 省={provs}, weather={"有" if "weather" in t else "无"}')

# 4) weatherpositions 加回 46 的两条
o.append('')
for label, root in [('仓库', G), ('副本', DEPL)]:
    fp = os.path.join(root, 'map', 'weatherpositions.txt')
    raw = io.open(fp, 'rb').read()
    t = raw.decode('utf-8-sig').rstrip('\r\n')
    if '46;' not in t:
        t = t + '\r\n46;2654.29;9.50;890.53;big\r\n46;2652.06;9.50;879.03;big'
    io.open(fp, 'wb').write(t.encode('utf-8'))
    chk = io.open(fp, 'rb').read().decode('utf-8-sig')
    o.append(f'{label} weatherpositions: {chk.splitlines()}')

# 5) 终检
o.append('')
for label, root in [('仓库', G), ('副本', DEPL)]:
    md = os.path.join(root, 'map')
    bad = []
    for root2, dirs2, files2 in os.walk(md):
        for f in files2:
            if f.lower().endswith(('.txt', '.csv', '.map')):
                raw = io.open(os.path.join(root2, f), 'rb').read()
                if raw.count(bytes([13, 13, 10])):
                    bad.append(os.path.relpath(os.path.join(root2, f), md))
    o.append(f'{label} map/ 仍含 CRCRLF 的文件: {bad if bad else "无 ✓"}')
    o.append(f'   战略区: {sorted(os.listdir(os.path.join(root, "map", "strategicregions")))}')
    r1 = io.open(os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt'), 'rb').read()
    o.append(f'   区域1: {len(r1)}B CRCRLF={r1.count(bytes([13,13,10]))}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')
