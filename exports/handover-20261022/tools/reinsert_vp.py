# -*- coding: utf-8 -*-
"""reinsert_vp.py —— 重新给 s747/s722/s782 插入 VP（字节级 CRLF，修复上次裸 \\n 事故）"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  'Daybreak of Teyvat Gamma Version', 'history', 'states')
JOBS = {747: (2149, 25), 722: (1482, 25), 782: (4338, 10)}

for sid, (pid, val) in JOBS.items():
    p = os.path.join(ST, f'{sid}-State_{sid}.txt')
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8-sig')
    nl = b'\r\n' if b'\r\n' in raw else b'\n'
    if 'victory_points' in t:
        print(f'  s{sid}: 已有 victory_points，跳过')
        continue
    m = re.search(r'\bhistory\s*=\s*\{', t)
    depth, i = 0, m.end() - 1
    while True:
        if t[i] == '{':
            depth += 1
        elif t[i] == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    close = i
    ls = t.rfind('\n', 0, close) + 1
    ins = f'\t\tvictory_points = {{ {pid} {val} }}\n'
    t2 = t[:ls] + ins + t[ls:]
    data = t2.encode('utf-8')
    data = data.replace(b'}\n' + nl if False else ins.encode('utf-8').replace(b'\n', b'\n'),
                        ins.encode('utf-8').replace(b'\n', nl))
    data = t2.encode('utf-8').replace(ins.encode('utf-8'),
                                      ins.encode('utf-8').replace(b'\n', nl))
    open(p, 'wb').write((b'\xef\xbb\xbf' + data) if raw[:3] == b'\xef\xbb\xbf' else data)
    # 回读验证
    raw2 = open(p, 'rb').read()
    seg = raw2.split(b'victory_points')[1][:40]
    print(f'  s{sid}: 插入 p{pid}={val}，行尾 CRLF={nl in seg}，BOM={raw2[:3] == b"\xef\xbb\xbf"}')
