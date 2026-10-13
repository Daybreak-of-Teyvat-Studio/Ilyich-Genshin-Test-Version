# -*- coding: utf-8 -*-
"""find_landmark2.py —— 精读两个地标的定义块 + entity 追查"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')

def block_of(t, name):
    m = re.search(r'(?m)^\s*' + re.escape(name) + r'\s*=\s*\{', t)
    if not m:
        return None
    depth, i = 0, m.end() - 1
    while i < len(t):
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    return t[m.start():i + 1]

for tag, base in (('gamma', G), ('beta', B)):
    p = os.path.join(base, 'common', 'buildings', 'DOT_landmark_buildings.txt')
    if not os.path.exists(p):
        print(f'{tag}: DOT_landmark_buildings.txt 不存在')
        continue
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    print('=' * 70)
    print(f'【{tag}】DOT_landmark_buildings.txt ({len(t)} 字符)')
    # 文件里全部建筑块名
    names = re.findall(r'(?m)^\s*(\w+)\s*=\s*\{', t)
    print(f'  全部块名: {names[:40]}')
    for tgt in ('landmark_institute_of_tower', 'landmark_Lei_Line_research_center'):
        blk = block_of(t, tgt)
        print(f'  --- {tgt} ---')
        if blk:
            for l in blk.split('\n')[:20]:
                print('    ', l.rstrip()[:120])
        else:
            print('    块未找到!')
    print()

# entity 追查：先拿 entity 名，再全树找
print('=' * 70)
print('【entity 全树追查】')
for tag, base in (('gamma', G), ('beta', B)):
    p = os.path.join(base, 'common', 'buildings', 'DOT_landmark_buildings.txt')
    t = open(p, encoding='utf-8-sig', errors='replace').read()
    ents = []
    for tgt in ('landmark_institute_of_tower', 'landmark_Lei_Line_research_center'):
        blk = block_of(t, tgt)
        if blk:
            m = re.search(r'(?m)^\s*entity\s*=\s*(\S+)', blk)
            ents.append((tgt, m.group(1) if m else None))
    print(f'  [{tag}] entity 引用: {ents}')
    for tgt, ent in ents:
        if not ent:
            continue
        hits = []
        for dirpath, dirnames, filenames in os.walk(base):
            if any(x in dirpath for x in ('.git', '.backups')):
                continue
            for fn in filenames:
                if fn.endswith(('.txt', '.gfx', '.asset')):
                    fp = os.path.join(dirpath, fn)
                    try:
                        tt = open(fp, encoding='utf-8-sig', errors='replace').read()
                    except Exception:
                        continue
                    if ent in tt:
                        hits.append(os.path.relpath(fp, base))
        print(f'      entity "{ent}" 出现于: {hits[:10]}')
    # 该文件里所有 entity 引用清单
    alle = re.findall(r'(?m)^\s*entity\s*=\s*(\S+)', t)
    print(f'  [{tag}] 文件里全部 entity 引用: {alle}')
