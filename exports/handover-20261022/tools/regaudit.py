import os, io, re

G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\regaudit_out.txt'
o = []

# definition: kind per province
kind = {}
loc = {}
for line in io.open(os.path.join(G, 'map', 'definition.csv'), 'rb').read().decode('utf-8-sig', errors='replace').splitlines():
    a = line.split(';')
    if len(a) > 4 and a[0].strip().isdigit():
        kind[int(a[0])] = a[4].strip()

# 州归属
p2s = {}
sd = os.path.join(G, 'history', 'states')
for f in os.listdir(sd):
    if not f.endswith('.txt'):
        continue
    t = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
    if m:
        for p in m.group(1).split():
            p2s[int(p)] = sid

def audit(fname, label):
    fp = os.path.join(G, 'map', 'strategicregions', fname)
    t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
    m = re.search(r'provinces=\{([^}]*)\}', t, re.S)
    provs = [int(x) for x in m.group(1).split()]
    o.append(f'{label} {fname}:')
    o.append(f'  省数={len(provs)}, 去重后={len(set(provs))}, 升序={provs == sorted(provs)}, 最大={max(provs)}, 最小={min(provs)}')
    if provs != sorted(provs):
        # 找出第一个逆序位置
        for i in range(1, len(provs)):
            if provs[i] < provs[i-1]:
                o.append(f'  ⚠ 第 {i+1} 个开始逆序: ...{provs[max(0,i-3):i+3]}...')
                break
    dups = [x for x in set(provs) if provs.count(x) > 1]
    o.append(f'  重复: {dups if dups else "无"}')
    return provs

p1 = audit('DOT_Strategicregions_01.txt', 'Gamma')
p46 = audit('DOT_Strategicregions_46.txt', 'Gamma')

o.append('')
o.append('===== 区域46 八省详情 =====')
for p in p46:
    o.append(f'  p{p}: 类型={kind.get(p, "不存在")}, 所属州={p2s.get(p, "无州")}')
o.append('')
o.append('===== 覆盖检查 =====')
allp = set(kind) - {0}
cov = set(p1) | set(p46)
o.append(f'  definition 省数(不含0)={len(allp)}, 两区并集={len(cov)}, 缺={sorted(allp - cov)[:10]}, 多={sorted(cov - allp)[:10]}')
o.append(f'  交集={sorted(set(p1) & set(p46))}')

o.append('')
o.append('===== Beta 的区域文件形态（前 3 个文件的 provinces 块写法） =====')
bsd = os.path.join(B, 'map', 'strategicregions')
for f in sorted(os.listdir(bsd))[:3]:
    t = io.open(os.path.join(bsd, f), 'rb').read().decode('utf-8-sig', errors='replace')
    m = re.search(r'provinces=\{([^}]*)\}', t, re.S)
    provs = [int(x) for x in m.group(1).split()]
    o.append(f'  {f}: {len(provs)} 省, 升序={provs == sorted(provs)}, 前 12={provs[:12]}')
    # 原始片段
    i = t.find('provinces={')
    o.append(f'      原文片段: {t[i:i+80]!r}')

o.append('')
o.append('===== Gamma 区域1 文件原文头尾（含换行形态） =====')
t = io.open(os.path.join(G, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt'), 'rb').read()
o.append(f'  前 60B: {t[:60]!r}')
o.append(f'  含 \\r\\r\\n 次数: {t.count(bytes([13,13,10]))}, \\r\\n 次数: {t.count(bytes([13,10]))}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')
