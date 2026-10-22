# -*- coding: utf-8 -*-
import os, io, re, sys, glob, datetime
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
LOGS = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\logs')
CR = os.path.expanduser(r'~\Documents\Paradox Interactive\Hearts of Iron IV\crashes')
OUT = os.path.join(REPO, 'tools', 'crashcheck_out.txt')
o = []

# 1) 崩溃目录
ds = sorted(glob.glob(os.path.join(CR, 'hoi4_*')), key=os.path.getmtime, reverse=True)
o.append('===== 最新崩溃 =====')
for d in ds[:3]:
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(d))
    o.append(f'  {os.path.basename(d)}  {mt:%m-%d %H:%M:%S}')
    ex = os.path.join(d, 'exception.txt')
    if os.path.exists(ex):
        t = io.open(ex, 'rb').read().decode('utf-8', errors='replace')
        for l in t.splitlines()[:8]:
            o.append('     ' + l.strip()[:150])

# 2) 日志
t = io.open(os.path.join(LOGS, 'error.log'), 'rb').read().decode('utf-8-sig', errors='replace')
mt = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(LOGS, 'error.log')))
lines = t.splitlines()
o.append('')
o.append(f'===== error.log ({len(lines)} 行, mtime {mt:%H:%M:%S}) =====')
for k in ('MAP_ERROR', 'not within specified state', 'invalid state', 'invalid arguments',
          'no provinces in state', 'no air base site', 'State Error', 'Executing History',
          'no strategic region', 'coastal', 'Missing State', 'fractioned'):
    n = len([1 for l in lines if k in l])
    o.append(f'  [{n}] {k}')
o.append('  末 20 行:')
for l in lines[-20:]:
    o.append('    ' + l[:180])
# 首行时间戳（判断是用户那次还是我的）
o.append(f'  首行: {lines[0][:120] if lines else "(空)"}')

# 3) buildings.txt 完整性（我脚本被中断）
o.append('')
a = io.open(os.path.join(G, 'map', 'buildings.txt'), 'rb').read()
b = io.open(os.path.join(DEPL, 'map', 'buildings.txt'), 'rb').read()
la = a.split(b'\r\n')
o.append(f'buildings 仓库: {len(a)}B, {len(la)} 行, 尾={a[-10:]!r}')
o.append(f'buildings 双副本一致: {a == b}')
bad = [i + 1 for i, l in enumerate(la) if len(l.decode('utf-8', 'replace').split(';')) != 7]
o.append(f'非7字段行: {bad[:8] if bad else "无 ✓"}')

# 4) 空州/异常州检查（全 700 州）
o.append('')
sd = os.path.join(G, 'history', 'states')
empty, nobldg, misfit = [], [], []
for f in sorted(os.listdir(sd)):
    if not f.endswith('.txt'):
        continue
    raw = io.open(os.path.join(sd, f), 'rb').read()
    tt = raw.decode('utf-8-sig')
    sid = int(re.search(r'\bid\s*=\s*(\d+)', tt).group(1))
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', tt, re.S)
    ps = m.group(1).split() if m else []
    if not ps:
        empty.append(sid)
    if 'buildings' not in tt:
        nobldg.append(sid)
    if tt.count('{') != tt.count('}'):
        misfit.append(sid)
o.append(f'空 provinces 州: {empty if empty else "无 ✓"}')
o.append(f'无 buildings 块州: {nobldg if nobldg else "无 ✓"}')
o.append(f'括号不配平州: {misfit if misfit else "无 ✓"}')
o.append(f'州文件数: {len([f for f in os.listdir(sd) if f.endswith(".txt")])}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))
