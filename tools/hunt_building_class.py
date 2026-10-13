# -*- coding: utf-8 -*-
"""hunt_building_class.py —— 找"building类"的真身：①DOT_Resources 740 决策块 ②GFX_idea_DOT_0xxx 使用者 ③六名州/六旧州 buildings 行核对"""
import os, re, sys, glob, struct

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

print('=== ① DOT_Resources.txt 中 740 决策块全文（L1080-1140）===')
p = os.path.join(G, 'common', 'decisions', 'DOT_Resources.txt')
ls = open(p, encoding='utf-8-sig', errors='replace').read().split('\n')
for i in range(1075, min(len(ls), 1145)):
    print(f'  L{i+1}: {ls[i].rstrip()[:120]}')

print()
print('=== ② GFX_idea_DOT_0 / DOT_Goal 的使用者（common 全目录）===')
for pat in (r'GFX_idea_DOT_0', r'DOT_Goal', r'GFX_goal_DOT', r'GFX_DOT_Goal'):
    hits = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, 'common')):
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(dirpath, fn)
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            for m in re.finditer(pat, t):
                ln = t[:m.start()].count('\n') + 1
                hits.append((os.path.relpath(fp, G), ln, t[max(0, m.start() - 40):m.end() + 40].replace('\n', ' ')[:110]))
    print(f'  --- {pat}: {len(hits)} 处 ---')
    for rel, ln, ctx in hits[:10]:
        print(f'    {rel} L{ln}: ...{ctx}...')

print()
print('=== ③ GFX_idea_DOT_0740 这类名字在 gfx 的定义处（确认 sprite 名）===')
p = os.path.join(G, 'interface', 'DOT_Icons_DOT_Idea.gfx')
ls2 = open(p, encoding='utf-8-sig', errors='replace').read().split('\n')
n = 0
for l in ls2:
    if 'GFX_idea_DOT_0740' in l or 'GFX_idea_DOT_0741' in l or 'GFX_idea_DOT_0748' in l:
        print('  ', l.strip()[:140])
        n += 1
print(f'  {n} 处')

print()
print('=== ④ 六个“名字州”的 buildings 行坐标核对 ===')
gk, colors = {}, {}
for l in open(os.path.join(G, 'map', 'definition.csv'), encoding='utf-8-sig', errors='replace').read().split('\n'):
    c = l.strip().split(';')
    if len(c) >= 5:
        try:
            pid = int(c[0])
            gk[pid] = c[4]
            colors[(int(c[1]), int(c[2]), int(c[3]))] = pid
        except ValueError:
            pass
raw = open(os.path.join(G, 'map', 'provinces.bmp'), 'rb').read()
off = struct.unpack('<I', raw[10:14])[0]
W, H = struct.unpack('<ii', raw[18:26])
RB = W * 3
PIX = raw[off:]
def px(x, z):
    i = z * RB + x * 3
    return colors.get((PIX[i + 2], PIX[i + 1], PIX[i]))

s2p = {}
for f in glob.glob(os.path.join(G, 'history', 'states', '*.txt')):
    t = open(f, encoding='utf-8-sig', errors='replace').read()
    m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    if m and m2:
        s2p[int(m.group(1))] = [int(x) for x in re.findall(r'\d+', m2.group(1))]
p2s = {}
for s, ps in s2p.items():
    for pp in ps:
        p2s.setdefault(pp, s)

for sid in (570, 136, 254, 574, 636, 695, 278, 279, 282, 284, 289, 290):
    bad = 0
    cnt = 0
    for l in open(os.path.join(G, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
        c = l.split(';')
        if len(c) >= 7 and c[0].strip() == str(sid):
            cnt += 1
            prov = px(int(float(c[2])), int(float(c[4])))
            if prov is None or p2s.get(prov) != sid:
                bad += 1
    print(f'  s{sid}: 行 {cnt}, 坐标越界 {bad}')
