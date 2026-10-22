# -*- coding: utf-8 -*-
"""跑游戏当判官：解析 mapbuildings 报错 → 修正 buildings.txt 第 1 列 → 复验"""
import os, io, re, sys, subprocess, time, datetime, shutil
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(REPO, '.backups', f'oracle_{stamp}')
os.makedirs(BD, exist_ok=True)
o = []
for label, root in [('repo', G), ('depl', DEPL)]:
    shutil.copy2(os.path.join(root, 'map', 'buildings.txt'), os.path.join(BD, f'{label}_buildings.txt'))
o.append(f'备份: {BD}')

def run_game(secs=95):
    subprocess.run(['powershell', '-NoProfile', '-Command',
                    "$p = Start-Process -FilePath 'F:\\Steam\\steamapps\\common\\Hearts of Iron IV\\hoi4.exe' "
                    "-ArgumentList '-debug' -WorkingDirectory 'F:\\Steam\\steamapps\\common\\Hearts of Iron IV' -PassThru; "
                    f"Start-Sleep -Seconds {secs}; if (-not $p.HasExited) {{ Stop-Process -Id $p.Id -Force }}"])
    time.sleep(3)

def parse_errors():
    t = io.open(os.path.join(LOGS, 'error.log'), 'rb').read().decode('utf-8-sig', errors='replace')
    out = []
    for l in t.splitlines():
        m = re.search(r'map/buildings\.txt error at line (\d+): map building\(([^)]*)\) location is not within specified state\. Supposed to be \'(\d+) - [^\']*\' but was \'(\d+) - ', l)
        if m:
            out.append(('within', int(m.group(1)), int(m.group(4))))   # 行号, 应改成的值(=was)
        m = re.search(r'map/buildings\.txt error at line (\d+): map building location has invalid state \((\d+)', l)
        if m:
            out.append(('invalid', int(m.group(1)), None))
    mp = [l for l in t.splitlines() if 'MAP_ERROR' in l]
    st = [l for l in t.splitlines() if 'State Error' in l or 'invalid state building' in l]
    return out, len(mp), st

for round_no in (1, 2):
    o.append(f'===== 第 {round_no} 轮：跑游戏 =====')
    run_game()
    errs, n_map, st = parse_errors()
    o.append(f'  within 类 {len([e for e in errs if e[0]=="within"])} 条, invalid 类 {len([e for e in errs if e[0]=="invalid"])} 条, MAP_ERROR {n_map} 条')
    for l in st[:6]:
        o.append('  ' + l.strip()[:170])
    if not errs:
        o.append('  无建筑报错 ✓')
        break
    fixed = 0
    for label, root in [('仓库', G), ('副本', DEPL)]:
        fp = os.path.join(root, 'map', 'buildings.txt')
        raw = io.open(fp, 'rb').read()
        lines = raw.split(b'\r\n')
        for kind, ln, val in errs:
            if kind != 'within' or val is None:
                continue
            i = ln - 1
            if 0 <= i < len(lines):
                f = lines[i].decode('utf-8', 'replace').split(';')
                if len(f) == 7:
                    f[0] = str(val)
                    lines[i] = ';'.join(f).encode('utf-8')
                    fixed += 1
        new = b'\r\n'.join(lines)
        if new.endswith(b'\r\n'):
            new = new[:-2]
        io.open(fp, 'wb').write(new)
    o.append(f'  已修正 {fixed} 行（双副本）')

# 终检
o.append('')
a = io.open(os.path.join(G, 'map', 'buildings.txt'), 'rb').read()
b = io.open(os.path.join(DEPL, 'map', 'buildings.txt'), 'rb').read()
o.append(f'buildings.txt: {len(a)}B, 双副本一致={a == b}, 尾={a[-16:]!r}')
ap = io.open(os.path.join(G, 'map', 'airports.txt'), 'rb').read()
o.append(f'airports.txt 首 8B={ap[:8]!r} (BOM={ap[:3] == bytes([0xef,0xbb,0xbf])})')
io.open(os.path.join(REPO, 'tools', 'oracle_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))
