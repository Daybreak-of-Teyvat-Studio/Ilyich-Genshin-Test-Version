import os, io, datetime, glob

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
CR = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\crashes')
OUT = os.path.join(REPO, 'tools', 'nudgecheck_out.txt')
o = []

# 1) 最新日志/转储时间线
o.append('===== 日志文件时间线 =====')
for f in sorted(os.listdir(LOGS), key=lambda x: os.path.getmtime(os.path.join(LOGS, x)), reverse=True)[:8]:
    fp = os.path.join(LOGS, f)
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    o.append(f'  {mt:%m-%d %H:%M:%S}  {f}  {os.path.getsize(fp)}B')
o.append('')
o.append('===== 崩溃目录（新→旧） =====')
ds = sorted(glob.glob(os.path.join(CR, 'hoi4_*')), key=os.path.getmtime, reverse=True)
for d in ds[:4]:
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(d))
    o.append(f'  {os.path.basename(d)}  {mt:%m-%d %H:%M:%S}')

# 2) error.log / system.log 里找 nudge 相关内容
o.append('')
for fn in ('error.log', 'system.log'):
    fp = os.path.join(LOGS, fn)
    if not os.path.exists(fp):
        continue
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    lines = t.splitlines()
    o.append(f'===== {fn} (mtime {mt:%H:%M:%S}, {len(lines)} 行) =====')
    hits = [l for l in lines if any(k in l.lower() for k in ('nudge', 'map definition', 'map_definition', 'buildings.txt', 'not within', 'BUILDING IGNORED', 'MAP_ERROR', 'state'))]
    o.append(f'  命中 nudge/map/state 关键词 {len(hits)} 行，前 25:')
    for l in hits[:25]:
        o.append('    ' + l[:200])
    o.append(f'  首行: {lines[0][:150] if lines else "(空)"}')
    o.append(f'  末 5 行:')
    for l in lines[-5:]:
        o.append('    ' + l[:200])

# 3) 检查所有 mega014 改过的文件 + 所有 map/*.txt 的行尾（CRCRLF 污染）
o.append('')
o.append('===== map/ 全部文本文件行尾体检（CRCRLF 污染检查） =====')
md = os.path.join(G, 'map')
for root2, dirs2, files2 in os.walk(md):
    for f in sorted(files2):
        if not f.lower().endswith(('.txt', '.csv', '.map')):
            continue
        rel = os.path.relpath(os.path.join(root2, f), md)
        raw = io.open(os.path.join(root2, f), 'rb').read()
        crcrlf = raw.count(bytes([13, 13, 10]))
        crlf = raw.count(bytes([13, 10]))
        lf = raw.count(bytes([10]))
        lonecr = raw.count(bytes([13])) - crlf
        flag = ' ⚠CRCRLF!' if crcrlf else ''
        o.append(f'  {rel:34s} {len(raw):>8}B CRLF={crlf:>5} CRCRLF={crcrlf:>5} 孤立CR={lonecr}{flag}')

# 4) mega014 改过的非 map 文件行尾
o.append('')
o.append('===== mega014 改过的其它文件行尾 =====')
targets = [
    'localisation/simp_chinese/DOT_state_names_gamma_l_simp_chinese.yml',
    'localisation/simp_chinese/DOT_Victory_Points_l_simp_chinese.yml',
    'common/decisions/DOT_Wonder_decisions.txt',
    'common/decisions/DOT_Wonder_decision_categories.txt',
    'common/on_actions/DOT_wonder_state_array_on_actions.txt',
    'common/scripted_effects/LYY_scripted_effects.txt',
    'common/scripted_localisation/DOT_wonder_state_scripted_localisation.txt',
    'common/scripted_triggers/NewMOT_scripted_triggers.txt',
    'history/countries/NCE - Children_of_Echoes.txt',
    'common/decisions/DVA_decisions.txt',
    'common/resources/DOT_Resources.txt',
]
for rel in targets:
    fp = os.path.join(G, rel.replace('/', os.sep))
    if not os.path.exists(fp):
        o.append(f'  {rel}: 不存在')
        continue
    raw = io.open(fp, 'rb').read()
    crcrlf = raw.count(bytes([13, 13, 10]))
    crlf = raw.count(bytes([13, 10]))
    lf = raw.count(bytes([10]))
    o.append(f'  {os.path.basename(rel):56s} {len(raw):>7}B CRLF={crlf:>5} CRCRLF={crcrlf:>5} 独立LF={lf - crlf}{" ⚠" if crcrlf else ""}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')
