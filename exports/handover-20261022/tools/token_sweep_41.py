# -*- coding: utf-8 -*-
"""token_sweep_41.py —— 41 个海州 id 的全 token 扫描（含 prioritize 列表等形式）"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')

SEA = sorted(set(range(709, 718)) | set(range(719, 751)))
TOK = re.compile(r'(?<![\d])(' + '|'.join(map(str, SEA)) + r')(?![\d])')
EXCLUDE = ('resource_prospecting', '14_sea_on_actions', '12_wuw', 'DOT_Resources')
# DOT_Resources 单独看（它的 740 系已处理，但可能还有别的海州号）

print('=== 全 token 扫描（common/events/history 非 states，排除已处理/原版文件）===')
hits_by_file = {}
for sub in ('common', 'events', 'history'):
    for dirpath, dirnames, filenames in os.walk(os.path.join(G, sub)):
        if 'states' in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if not fn.endswith('.txt'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, G)
            if any(x in rel for x in EXCLUDE):
                continue
            t = open(fp, encoding='utf-8-sig', errors='replace').read()
            for i, l in enumerate(t.split('\n')):
                ms = list(TOK.finditer(l))
                if not ms:
                    continue
                # 过滤明显噪声：days/cost/amount/value/坐标/年份 等
                stripped = l.strip()
                if re.search(r'(?i)(days|cost|amount|value|manpower|year|month|hours)\s*=', stripped) and not re.search(r'(?i)(state|owns|controls|transfer|prioritize|highlight|targets)', stripped):
                    continue
                hits_by_file.setdefault(rel, []).append((i + 1, [m.group(1) for m in ms], stripped[:130]))

for rel, hits in sorted(hits_by_file.items()):
    print(f'\n--- {rel} ({len(hits)} 行) ---')
    for ln, nums, ctx in hits[:15]:
        print(f'  L{ln} {nums}: {ctx}')
