import os, io, re

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
BK = os.path.join(REPO, '.backups', 'mega014_20261014_220448')
OUT = os.path.join(REPO, 'tools', 'r1diff_out.txt')
o = []

cur = io.open(os.path.join(G, 'map', 'strategicregions', 'DOT_Strategicregions_01.txt'), 'rb').read()
old = io.open(os.path.join(BK, '仓库_r1_DOT_Strategicregions_01.txt'), 'rb').read()
o.append(f'当前 r1: {len(cur)}B, CRCRLF={cur.count(bytes([13,13,10]))}, CRLF={cur.count(bytes([13,10]))}')
o.append(f'备份 r1: {len(old)}B, CRCRLF={old.count(bytes([13,13,10]))}, CRLF={old.count(bytes([13,10]))}')
tc = cur.decode('utf-8-sig')
to = old.decode('utf-8-sig')
o.append(f'行数: 当前 {len(tc.splitlines())} vs 备份 {len(to.splitlines())}')

def pblock(t):
    m = re.search(r'provinces=\{([^}]*)\}', t, re.S)
    return m.group(1) if m else None

pc, po = pblock(tc), pblock(to)
for name, pb in (('当前', pc), ('备份', po)):
    if pb is None:
        o.append(f'{name} provinces 块: 未找到!')
        continue
    lines = [l.strip() for l in pb.splitlines() if l.strip()]
    bad = [l for l in lines if not l.isdigit()]
    nums = [int(l) for l in lines if l.isdigit()]
    o.append(f'{name} provinces: {len(lines)} 个, 升序={nums == sorted(nums)}, 非常数字行={bad[:5] if bad else "无 ✓"}')
    o.append(f'   前 6={nums[:6]}, 后 6={nums[-6:]}')

missing = [860, 1531, 2282, 3544, 4681, 4682, 4683, 4684]
if pc:
    has = [p for p in missing if re.search(rf'(^|\s){p}(\s|$)', pc)]
    o.append(f'当前 r1 仍含这 8 省中的: {has if has else "无（已移除 ✓）"}')
o.append(f'当前 r1 花括号: {{={tc.count(chr(123))} }}={tc.count(chr(125))}')

# 备份里 provinces 块外的结构（确认我的移除脚本没动别的）
o.append('')
o.append('当前 r1 头部 6 行:')
for l in tc.splitlines()[:6]:
    o.append('  ' + repr(l[:90]))
o.append('当前 r1 provinces 块前后各 2 行:')
i = tc.find('provinces={')
seg = tc[i:i+160]
o.append('  ' + repr(seg))

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))

# 删除区域46（双副本）
for root in (G, DEPL):
    fp = os.path.join(root, 'map', 'strategicregions', 'DOT_Strategicregions_46.txt')
    if os.path.exists(fp):
        os.remove(fp)
        o.append(f'已删除区域46: {root}')
    o.append(f'  {root} 战略区: {sorted(os.listdir(os.path.join(root, "map", "strategicregions")))}')
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')
