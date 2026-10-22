import os, io, glob, datetime, hashlib

LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
CR = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\crashes')
DOC = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = os.path.join(DOC, 'mod', 'Daybreak of Teyvat Gamma Version')
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\audit1015_out.txt'
o = []

# 1) 崩溃目录按时间列
o.append('===== 崩溃目录（按 mtime 倒序） =====')
ds = sorted(glob.glob(os.path.join(CR, 'hoi4_*')), key=os.path.getmtime, reverse=True)
for d in ds[:4]:
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(d))
    o.append(f'  {os.path.basename(d)}  mtime={mt:%m-%d %H:%M:%S}')

# 2) 最新崩溃（我那次）的 meta + exception
newest = ds[0]
o.append('')
o.append(f'===== 最新崩溃 {os.path.basename(newest)} =====')
for fn in ('meta.yml', 'exception.txt'):
    fp = os.path.join(newest, fn)
    if os.path.exists(fp):
        t = io.open(fp, 'rb').read().decode('utf-8', errors='replace')
        o.append(f'--- {fn} ---')
        for l in t.splitlines():
            if fn == 'meta.yml':
                if any(k in l for k in ('Mods:', 'LaunchArguments', 'DateTime', 'HasMods', 'debug')):
                    o.append('   ' + l.strip()[:200])
            else:
                o.append('   ' + l.strip()[:200])

# 3) 当前日志（我那次运行）关键统计
for lg in ('game.log', 'error.log'):
    fp = os.path.join(LOGS, lg)
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    raw = io.open(fp, 'rb').read()
    t = raw.decode('utf-8-sig', errors='replace')
    lines = t.splitlines()
    o.append('')
    o.append(f'===== {lg}: {len(lines)} 行, bytes={len(raw)}, mtime={mt:%m-%d %H:%M:%S} =====')
    if lg == 'game.log':
        for l in lines[:10]:
            o.append('  ' + l[:200])
    else:
        o.append('  首行: ' + (lines[0][:120] if lines else '(空)'))
        o.append('  末行: ' + (lines[-1][:160] if lines else '(空)'))
        import re
        for name, pat in [('MAP_ERROR', 'MAP_ERROR'), ('Loaded provinces', r'Loaded \d+ provinces'),
                          ('no strategic region', 'no strategic region'),
                          ('land province has no state', 'land province has no state'),
                          ('Missing State', 'Missing State'), ('BUILDING IGNORED', 'BUILDING IGNORED'),
                          ('coastal', 'coastal'), ('mask sea/temp', '马斯克海|temperature doesn'),
                          ('X crossing', 'X crossing')]:
            n = len([1 for l in lines if re.search(pat, l)])
            o.append(f'  [{n}] {name}')

# 4) 仓库 vs 副本 关键文件字节对比
o.append('')
o.append('===== 仓库 vs 副本（关键文件哈希） =====')
files = ['map/buildings.txt', 'map/airports.txt', 'map/rocketsites.txt',
         'map/strategicregions/DOT_Strategicregions_01.txt',
         'map/strategicregions/DOT_Strategicregions_46.txt',
         'map/definition.csv', 'map/provinces.bmp', 'descriptor.mod',
         'localisation/simp_chinese/DOT_state_names_gamma_l_simp_chinese.yml']
for rel in files:
    a = os.path.join(REPO, rel.replace('/', os.sep))
    b = os.path.join(DEPL, rel.replace('/', os.sep))
    ha = hashlib.md5(io.open(a, 'rb').read()).hexdigest()[:10] if os.path.exists(a) else 'MISSING'
    hb = hashlib.md5(io.open(b, 'rb').read()).hexdigest()[:10] if os.path.exists(b) else 'MISSING'
    o.append(f'  {rel}: 仓库={ha} 副本={hb} 一致={ha == hb}')
# states 数量
for label, root in [('仓库', REPO), ('副本', DEPL)]:
    sd = os.path.join(root, 'history', 'states')
    n = len([f for f in os.listdir(sd) if f.endswith('.txt')]) if os.path.isdir(sd) else -1
    o.append(f'  {label} states 文件数: {n}')

# 5) dlc_load.json
fp = os.path.join(DOC, 'dlc_load.json')
o.append('')
o.append('===== dlc_load.json =====')
o.append(io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace') if os.path.exists(fp) else 'MISSING')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')
