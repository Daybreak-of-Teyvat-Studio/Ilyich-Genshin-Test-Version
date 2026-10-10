# -*- coding: utf-8 -*-
"""evidence3.py —— 钉死 MAP_ERROR 规则 + buildings 重建丢失清单 + 15 州详情"""
import os, re, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
B = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')

# --- A) 每州 buildings 行计数 → 找零行州 ---
print('=' * 70)
print('【A】gamma buildings.txt 每州行数：零行州 vs 42 错误州')
per_state = collections.Counter()
prov_of = collections.defaultdict(set)
for l in open(os.path.join(G, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    if not l.strip():
        continue
    c = l.split(';')
    if len(c) < 7:
        continue
    per_state[c[0].strip()] += 1
    prov_of[c[0].strip()].add(c[6].strip())
all_states = set(str(i) for i in range(1, 751))
zero = sorted(int(s) for s in all_states - set(per_state))
print(f'  有行的州: {len(per_state)} / 零行州 {len(zero)}: {zero}')
err42 = [317, 709, 710, 711, 712, 713, 714, 715, 716, 717, 719, 720, 721, 722, 723, 724, 725, 726, 727,
         728, 729, 730, 731, 732, 733, 734, 735, 736, 737, 738, 739, 740, 741, 742, 743, 744, 745, 746,
         747, 748, 749, 750]
print(f'  42 错误州 - 零行州 = {sorted(set(err42) - set(zero))}')
print(f'  零行州 - 42 错误州 = {sorted(set(zero) - set(err42))}')

# --- B) 15 个 too many buildings 州的楼型明细 ---
print()
print('=' * 70)
print('【B】15 州 buildings 行楼型明细（找异常类型）')
bad = [76, 82, 223, 246, 269, 284, 311, 500, 560, 564, 569, 584, 587, 590, 607]
detail = collections.defaultdict(collections.Counter)
for l in open(os.path.join(G, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    if not l.strip():
        continue
    c = l.split(';')
    if len(c) >= 7 and c[0].strip() in [str(x) for x in bad]:
        detail[int(c[0])][c[1].strip()] += 1
for s in bad[:4]:
    print(f'  s{s}: {dict(detail[s])}')
# 对比一个正常 town 州
print('  对照 s100（前5行类型）:', dict(list(detail.get(100, {}).items())[:6]) if 100 in detail else '无数据')

# --- C) 全图每州行数分布（看 15 州是否真的异常多）---
print()
tot = [(int(s), n) for s, n in per_state.items() if s.isdigit()]
tot.sort(key=lambda x: -x[1])
print('  行数最多的 20 个州:', tot[:20])

# --- D) 317 的 loc / 详情 ---
print()
print('=' * 70)
print('【D】state 317 的定位')
for yml in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*state*')):
    t = open(yml, encoding='utf-8-sig', errors='replace').read()
    for m in re.finditer(r'DOT_STATE_317[^\n]*', t):
        print(f'  {os.path.basename(yml)}: {m.group(0)[:110]}')

# --- E) 15 州的 loc 是否缺失 ---
print()
print('=' * 70)
print('【E】15 州 name key 在 loc 中的存在性')
allloc = ''
for yml in glob.glob(os.path.join(G, 'localisation', 'simp_chinese', '*.yml')):
    allloc += open(yml, encoding='utf-8-sig', errors='replace').read()
for s in ([76] + bad[1:5]):
    key = f'DOT_STATE_{s}'
    found = re.search(r'(?m)^\s*' + key + r':\d?', allloc)
    print(f'  {key}: {"有loc" if found else "★缺loc"}')

# --- F) beta/vanilla railways.txt ---
print()
print('=' * 70)
print('【F】railways.txt 三方对比')
for tag, base in (('原版', V), ('beta', B), ('gamma', G)):
    p = os.path.join(base, 'map', 'railways.txt')
    if os.path.exists(p):
        raw = open(p, 'rb').read()
        txt = raw.decode('utf-8-sig', errors='replace')
        print(f'  {tag}: {len(raw)}B, 非空行 {len([x for x in txt.split(chr(10)) if x.strip()])}')
    else:
        print(f'  {tag}: 不存在')

# --- G) buildings.txt.bak 的类型清单 vs 现版 ---
print()
print('=' * 70)
print('【G】buildings.txt.bak_221808 楼型清单')
bak = os.path.join(G, 'map', 'buildings.txt.bak_221808')
if os.path.exists(bak):
    tb = collections.Counter()
    for l in open(bak, encoding='utf-8-sig', errors='replace'):
        if l.strip():
            c = l.split(';')
            if len(c) >= 2:
                tb[c[1].strip()] += 1
    for t, n in tb.most_common():
        print(f'    {t:32s} ×{n}')
else:
    print('  不存在')

# --- H) 原版 buildings.txt 类型清单 ---
print()
print('=' * 70)
print('【H】原版 buildings.txt 楼型清单')
tv = collections.Counter()
for l in open(os.path.join(V, 'map', 'buildings.txt'), encoding='utf-8-sig', errors='replace'):
    if l.strip():
        c = l.split(';')
        if len(c) >= 2:
            tv[c[1].strip()] += 1
for t, n in tv.most_common():
    print(f'    {t:32s} ×{n}')

# --- I) beta airports.txt 尾部 20 行（海洋州怎么给的选址）---
print()
print('=' * 70)
print('【I】beta airports.txt 末尾 15 行（海洋州选址玄机）')
t = open(os.path.join(B, 'map', 'airports.txt'), encoding='utf-8-sig', errors='replace').read()
ls = [l.rstrip() for l in t.split('\n') if l.strip()]
for l in ls[-15:]:
    print('   ', l)
