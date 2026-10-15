import os, io, re

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\cover1015_out.txt'
o = []

# definition.csv 省份集合
defp = os.path.join(REPO, 'map', 'definition.csv')
raw = io.open(defp, 'rb').read()
t = raw.decode('utf-8-sig', errors='replace')
prov_ids = set()
for line in t.splitlines():
    line = line.strip()
    if not line or line.lower().startswith('province'):
        continue
    p = line.split(';')
    try:
        prov_ids.add(int(p[0]))
    except ValueError:
        pass
o.append(f'definition.csv: {len(prov_ids)} 个省份 id, max={max(prov_ids)}, min={min(prov_ids)}')

def region_provs(fname):
    fp = os.path.join(REPO, 'map', 'strategicregions', fname)
    tt = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    m = re.search(r'provinces=\{([^}]*)\}', tt, re.S)
    return [int(x) for x in m.group(1).split()]

p1 = region_provs('DOT_Strategicregions_01.txt')
p46 = region_provs('DOT_Strategicregions_46.txt')
s1, s46 = set(p1), set(p46)

o.append(f'区域1: {len(p1)} 省（去重 {len(s1)}）, 区域46: {len(p46)} 省（去重 {len(s46)}）')
o.append(f'区域1∩区域46 重复: {sorted(s1 & s46) if s1 & s46 else "无"}')
covered = s1 | s46
missing = sorted(prov_ids - covered)
extra = sorted(covered - prov_ids)
o.append(f'两区并集 {len(covered)} 省')
o.append(f'定义有但无战略区的省: {missing[:20]}{" ...共" + str(len(missing)) + "个" if len(missing) > 20 else ""}' if missing else '定义有但无战略区的省: 无 ✓')
o.append(f'战略区里有但定义外的省: {extra if extra else "无 ✓"}')
o.append(f'覆盖完整性: {"✓ 全等" if covered == prov_ids else "✗ 不等"}')

# 区域46 的 8 省在 definition 与州归属
o.append('')
o.append('区域46 八省状态:')
for x in p46:
    o.append(f'  p{x}: 在定义={x in prov_ids}')
# 查这 8 省是否落在 62/64
for n in (62, 64):
    fp = os.path.join(REPO, 'history', 'states', f'{n}-State_{n}.txt')
    tt = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', tt, re.S)
    o.append(f'  s{n} 省份: {m.group(1).split()}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')
