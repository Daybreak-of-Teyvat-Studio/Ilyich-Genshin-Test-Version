# -*- coding: utf-8 -*-
"""verify_mega014.py —— 验证：连号/合并62/战略区/引用残留"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]

for tag, base in COPIES:
    print('=' * 60)
    print(f'【{tag}】')
    # 1) 连号
    ids = []
    for f in glob.glob(os.path.join(base, 'history', 'states', '*.txt')):
        t = open(f, encoding='utf-8-sig', errors='replace').read()
        m = re.search(r'(?m)^\s*id\s*=\s*(\d+)', t)
        if m:
            ids.append(int(m.group(1)))
    ids = sorted(ids)
    gaps = [i for i in range(1, max(ids) + 1) if i not in set(ids)]
    print(f'  州: {len(ids)} 个, 1-{max(ids)}, 缺号 {gaps[:10]}{"✓" if not gaps and max(ids) == len(ids) else "★"}')

    # 2) 合并后 62
    t = open(os.path.join(base, 'history', 'states', '62-State_62.txt'), encoding='utf-8-sig', errors='replace').read()
    m2 = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
    ps = re.findall(r'\d+', m2.group(1)) if m2 else []
    nblocks = len(re.findall(r'(?m)^\s*\d+\s*=\s*\{', t))
    print(f'  62 州: 省{len(ps)} {ps} 省块{nblocks} ✓' if len(ps) == 5 and nblocks == 5 else f'  62 州: ★省{ps} 块{nblocks}')

    # 3) 新 63/65/66/67
    for sid, was in (('63', '703'), ('65', '704'), ('66', '705'), ('67', '706')):
        fs = glob.glob(os.path.join(base, 'history', 'states', f'{sid}-*.txt'))
        if fs:
            tt = open(fs[0], encoding='utf-8-sig', errors='replace').read()
            ok = f'id = {sid}' in tt and f'name="DOT_STATE_{sid}"' in tt and f'name="STATE_{was}"' in tt
            print(f'  s{sid}(原{was}): {"✓" if ok else "★"} [{os.path.basename(fs[0])}]')

    # 4) 战略区
    p1 = os.path.join(base, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt')
    n1 = len([l for l in open(p1, encoding='utf-8-sig', errors='replace') if l.strip() and l.strip().isdigit()])
    p2 = os.path.join(base, 'map', 'strategicregions', 'DOT_Strategicregions_46.txt')
    ok2 = os.path.exists(p2)
    n2 = len([l for l in open(p2, encoding='utf-8-sig', errors='replace') if l.strip().isdigit()]) if ok2 else 0
    print(f'  区域1: {n1} 省（应8013）| 区域46: {n2} 省（应8）')

    # 5) airports/rocketsites 现状
    ap = open(os.path.join(base, 'map', 'airports.txt'), encoding='utf-8-sig', errors='replace').read()
    for k in ('63', '65', '66', '67', '89', '90', '94', '703', '704', '705', '706', '707', '708', '709'):
        m = re.search(rf'(?m)^\s*{k}\s*=\s*\{{([^}}]*)\}}', ap)
        if m:
            print(f'    airports s{k} = {m.group(1).strip()}')
    # 6) 引用残留 token 扫描（703-706 全树）
    TOK = re.compile(r'(?<![\d])(703|704|705|706)(?![\d])')
    resid = 0
    for sub in ('common', 'events', 'history'):
        for dirpath, dirnames, filenames in os.walk(os.path.join(base, sub)):
            if 'states' in dirpath.split(os.sep):
                continue
            for fn in filenames:
                if not fn.endswith('.txt'):
                    continue
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, base)
                if 'resource_prospecting' in rel or '14_sea' in rel or '12_wuw' in rel:
                    continue
                t2 = open(fp, encoding='utf-8-sig', errors='replace').read()
                for i, l in enumerate(t2.split('\n')):
                    if TOK.search(l) and not re.search(r'(?i)(days|cost|amount|value|year|expire)\s*=', l):
                        print(f'    ⚠ 残留 {rel} L{i+1}: {l.strip()[:110]}')
                        resid += 1
    print(f'  703-706 引用残留: {resid}')
