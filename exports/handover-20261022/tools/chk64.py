import os, io, re, glob

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\chk64_out.txt'
o = []

for label, root in [('仓库', REPO), ('副本', DEPL)]:
    fp = os.path.join(root, 'history', 'states', '64-State_64.txt')
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
    provs = m.group(1).split() if m else []
    o.append(f'{label} s64 省份: {provs}')
    m2 = re.search(r'owner\s*=\s*(\w+)', t)
    o.append(f'{label} s64 owner: {m2.group(1) if m2 else "?"}')

# loc 键
o.append('')
for key in ['DOT_STRATEGICREGIONS_46', 'DOT_STRATEGICREGIONS_01']:
    for label, root in [('仓库', REPO)]:
        pat = os.path.join(root, 'localisation', 'simp_chinese', '*.yml')
        hits = []
        for f in glob.glob(pat):
            tt = io.open(f, 'rb').read().decode('utf-8-sig', errors='replace')
            for line in tt.splitlines():
                if key in line:
                    hits.append(f'{os.path.basename(f)}: {line.strip()[:120]}')
        o.append(f'{label} loc[{key}]: {hits if hits else "（无）"}')

# 62 州文件原始字节（缩进）
fp = os.path.join(REPO, 'history', 'states', '62-State_62.txt')
raw = io.open(fp, 'rb').read()
o.append('')
o.append(f's62 原始字节前 60B: {raw[:60]!r}')
o.append(f's62 含 tab? {b"\\t" in raw}, 含 8 空格缩进? {b"        id" in raw}')
fp = os.path.join(REPO, 'history', 'states', '63-State_63.txt')
raw = io.open(fp, 'rb').read()
o.append(f's63 原始字节前 60B: {raw[:60]!r}')
o.append(f's63 行尾风格: CRLF={raw.count(b"\\r\\n")}, LF total={raw.count(b"\\n")}, 单独CR={raw.count(b"\\r")}')
o.append(f's63 结尾 20B: {raw[-20:]!r}')

# 区域46 与 区域1 在副本的字节一致性
for f in ['DOT_Strategicregions_46.txt', 'DOT_Strategicregions_01.txt']:
    a = io.open(os.path.join(REPO, 'map', 'strategicregions', f), 'rb').read()
    b = io.open(os.path.join(DEPL, 'map', 'strategicregions', f), 'rb').read()
    o.append(f'{f}: 仓库/副本 字节一致 = {a == b}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')
