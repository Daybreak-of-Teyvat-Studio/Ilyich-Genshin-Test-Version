import os, io, datetime, glob

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
VANILLA = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\trace1015_out.txt'
o = []

CUT = datetime.datetime(2026, 10, 14, 22, 10, 0)

for label, root in [('仓库', REPO), ('副本', DEPL)]:
    o.append(f'===== {label}: 10-14 22:10 之后修改的文件 =====')
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        if '.backups' in dirpath or '.git' in dirpath:
            continue
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            try:
                mt = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
            except OSError:
                continue
            if mt > CUT:
                n += 1
                if n <= 60:
                    o.append(f'  {mt:%m-%d %H:%M:%S}  {os.path.relpath(fp, root)}')
    o.append(f'  （共 {n} 个）')
    o.append('')

# 原版：有没有缺 weather 的战略区
vsd = os.path.join(VANILLA, 'map', 'strategicregions')
o.append('===== 原版战略区：缺 weather 的文件 =====')
miss = []
for fp in glob.glob(os.path.join(vsd, '*.txt')):
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    if 'weather' not in t:
        miss.append(os.path.basename(fp))
o.append(f'  共 {len(glob.glob(os.path.join(vsd, "*.txt")))} 个区域文件, 缺 weather: {miss if miss else "无"}')
o.append('')

# 副本区域文件：weather 有无 + 结构对比
sd = os.path.join(DEPL, 'map', 'strategicregions')
for f in sorted(os.listdir(sd)):
    fp = os.path.join(sd, f)
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    has_w = 'weather' in t
    o.append(f'副本 {f}: weather={"有" if has_w else "【无】"}, {len(t)} 字符')
# 区域1 的 weather 块提取（首尾）
fp1 = os.path.join(sd, 'DOT_Strategicregions_01.txt')
t1 = io.open(fp1, 'rb').read().decode('utf-8-sig', errors='replace')
i = t1.find('weather')
o.append('')
o.append(f'区域1 weather 块起始（字符 {i}）: {t1[i-20:i+300]!r}')
o.append(f'区域1 weather 块结束: {t1[-200:]!r}')
# 统计区域1 weather 的 period 数量与 between 值
import re
bets = re.findall(r'between=\{\s*([\d.\-]+)\s+([\d.\-]+)\s*\}', t1)
o.append(f'区域1 weather period between 对: {len(bets)} 个')
o.append(f'  前 6 个: {bets[:6]}')
o.append(f'  后 6 个: {bets[-6:]}')

# WER 报告（最新）
o.append('')
o.append('===== WER 最新报告 =====')
import subprocess
for base in [r'C:\ProgramData\Microsoft\Windows\WER\ReportArchive', r'C:\ProgramData\Microsoft\Windows\WER\ReportQueue']:
    if not os.path.isdir(base):
        continue
    dirs = sorted(glob.glob(os.path.join(base, 'hoi4*')), key=os.path.getmtime, reverse=True)
    for d in dirs[:3]:
        mt = datetime.datetime.fromtimestamp(os.path.getmtime(d))
        o.append(f'-- {d}  ({mt:%m-%d %H:%M})')
        for f in os.listdir(d):
            if f.lower().endswith('.wer') or f.lower() == 'report.wer':
                t = io.open(os.path.join(d, f), 'rb').read().decode('utf-16', errors='replace')
                keys = [l for l in t.splitlines() if any(k in l for k in ('FaultingModule', 'ExceptionCode', 'Sig[', 'AppPath', 'ModName'))]
                for l in keys[:20]:
                    o.append(f'   {l.strip()[:200]}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok', len(o))
