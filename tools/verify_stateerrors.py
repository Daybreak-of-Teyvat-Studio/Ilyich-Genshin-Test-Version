# -*- coding: utf-8 -*-
"""verify_stateerrors.py —— 核实最新日志的两类州错误
A) 无效船坞州 15/54/125/238/249：省份/沿海标记/buildings 块
B) 错州省份建筑块 9 处：省现在归谁、原州块现状、沿海标记
C) 3499 归属核实 + 全部声明 dockyard 的州 coastal 判定
"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(G, 'history', 'states')

# definition：land/coastal（第5列kind，第6列coastal）
kind, coastal = {}, {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace'):
    a = l.split(';')
    if len(a) > 6 and a[0].strip().isdigit() and int(a[0]) > 0:
        pid = int(a[0])
        kind[pid] = a[4]
        coastal[pid] = (a[5].strip().lower() == 'true')

# 州数据
states = {}
for f in glob.glob(os.path.join(ST, '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    pm = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    provs = [int(x) for x in (pm.group(1).split() if pm else [])]
    bm = re.search(r'buildings\s*=\s*\{', t)
    # 提取 buildings 块（平衡配对）
    block = None
    if bm:
        depth, i = 0, bm.end() - 1
        while i < len(t):
            if t[i] == '{':
                depth += 1
            elif t[i] == '}':
                depth -= 1
                if depth == 0:
                    block = t[bm.start():i + 1]
                    break
            i += 1
    om = re.search(r'\bowner\s*=\s*(\w+)', t)
    states[sid] = {'provs': provs, 'block': block, 'owner': om.group(1) if om else None, 'file': f}

p2s = {p: s for s, d in states.items() for p in d['provs']}

print('=== A) 无效船坞州 ===')
for sid in (15, 54, 125, 238, 249):
    d = states[sid]
    coast = [p for p in d['provs'] if coastal.get(p)]
    print(f's{sid} owner={d["owner"]} 省{len(d["provs"])} 沿海省={coast}')
    if d['block']:
        dy = re.search(r'dockyard\s*=\s*(\d+)', d['block'])
        print(f'    dockyard={dy.group(1) if dy else "无"}；块内省级键: '
              f'{[int(m.group(1)) for m in re.finditer(r"(?m)^\s*(\d+)\s*=\s*\{", d["block"])]}')

print()
print('=== B) 错州省份建筑块 ===')
for pid, sid in ((1772, 15), (1368, 152), (78, 186), (1821, 186), (2001, 204),
                 (356, 208), (2733, 249), (182, 415), (1157, 470)):
    cur = p2s.get(pid)
    print(f'  p{pid}: 名义州{sid} → 现在 s{cur}（沿海={coastal.get(pid)}，kind={kind.get(pid)}）'
          f'；s{sid} 是否仍含该省的块: '
          f'{"是" if states[sid]["block"] and re.search(r"(?m)^\s*" + str(pid) + r"\s*=\s*\{", states[sid]["block"]) else "否"}'
          f'；s{cur} 是否已声明: '
          f'{"是" if states[cur]["block"] and re.search(r"(?m)^\s*" + str(pid) + r"\s*=\s*\{", states[cur]["block"]) else "否"}')

print()
print('=== C) 3499 与全部 dockyard 州 ===')
print(f'  p3499 现在 s{p2s.get(3499)}，沿海={coastal.get(3499)}，kind={kind.get(3499)}')
print('  所有声明 dockyard 的州：')
for sid, d in sorted(states.items()):
    if d['block'] and re.search(r'dockyard\s*=\s*\d+', d['block']):
        coast = [p for p in d['provs'] if coastal.get(p)]
        flag = '' if coast else '  ← 无沿海省（无效！）'
        print(f'    s{sid}: 沿海省 {coast if len(coast) <= 3 else str(len(coast)) + "个"}{flag}')
