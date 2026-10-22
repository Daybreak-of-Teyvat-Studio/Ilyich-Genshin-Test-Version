import os, io

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
OUT = os.path.join(REPO, 'tools', 'state_eol_out.txt')
o = []

sd = os.path.join(G, 'history', 'states')
bad_crcrlf = []
bad_lf = []
for f in sorted(os.listdir(sd)):
    if not f.endswith('.txt'):
        continue
    raw = io.open(os.path.join(sd, f), 'rb').read()
    crcrlf = raw.count(bytes([13, 13, 10]))
    crlf = raw.count(bytes([13, 10]))
    lf = raw.count(bytes([10]))
    if crcrlf:
        bad_crcrlf.append((f, crcrlf))
    if lf > crlf:
        bad_lf.append((f, lf, crlf))
o.append(f'states 文件数: {len([f for f in os.listdir(sd) if f.endswith(".txt")])}')
o.append(f'含 CRCRLF 的州文件: {bad_crcrlf if bad_crcrlf else "无 ✓"}')
o.append(f'LF-only 的州文件: {bad_lf if bad_lf else "无 ✓"}')

# 全 mod 扫描 CRCRLF（除 .backups）
o.append('')
o.append('===== 全 mod 扫描 CRCRLF（排除 .backups/.git） =====')
hits = []
for root2, dirs2, files2 in os.walk(G):
    if '.backups' in root2:
        continue
    for f in files2:
        if f.lower().endswith(('.txt', '.yml', '.csv', '.map', '.gui', '.gfx', '.asset', '.lua')):
            fp = os.path.join(root2, f)
            try:
                raw = io.open(fp, 'rb').read()
            except OSError:
                continue
            n = raw.count(bytes([13, 13, 10]))
            if n:
                hits.append((os.path.relpath(fp, G), n))
for h, n in hits[:40]:
    o.append(f'  {h}: {n} 处')
o.append(f'  共 {len(hits)} 个文件含 CRCRLF')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')
