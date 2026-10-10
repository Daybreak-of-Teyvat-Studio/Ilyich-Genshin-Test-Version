# -*- coding: utf-8 -*-
"""fix_naval_pack.py —— 海军/OOB/触发器修复大礼包（仓库+副本，先备份）
1) 恢复 VAN_1936_naval.txt（12 字节空壳，beta→gamma 迁移丢失）
2) PRI_1936_Naval.txt 舰名去重（201 艘重名"时 1"→ 按前缀连号）
3) INA 补 4 类舰船变体（Sumeru_Class×2/Natlan_Class/Fontaine_Class/Snezhnaya_Class）
   FAV 补 2 类（Mondstadt_Class heavy_2 / Fontaine_Class light_1）—— 模板取自原版
4) NewMOT_scripted_triggers.txt 8 处除零保护
"""
import os, re, sys, glob, shutil, datetime, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
COPIES = [('仓库', os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')),
          ('副本', r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version')]
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(ROOT, '.backups', f'navalpack_{stamp}')
os.makedirs(BD, exist_ok=True)


def load(p):
    raw = open(p, 'rb').read()
    return raw, raw.decode('utf-8-sig')


def save(p, t, bom):
    open(p, 'wb').write(((b'\xef\xbb\xbf' if bom else b'') + t.encode('utf-8')))


# ---- 原版变体模板（完整块提取） ----
def vanilla_block(hull):
    for p in glob.glob(os.path.join(V, 'history', 'countries', '*.txt')):
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        for m in re.finditer(r'create_equipment_variant\s*=\s*\{', t):
            depth, i = 0, m.end() - 1
            while i < len(t):
                if t[i] == '{':
                    depth += 1
                elif t[i] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            block = t[m.start():i + 1]
            if re.search(r'type\s*=\s*' + hull + r'\b', block):
                return block
    return None


TPL = {h: vanilla_block(h) for h in ('ship_hull_light_1', 'ship_hull_light_2',
                                     'ship_hull_cruiser_1', 'ship_hull_cruiser_2', 'ship_hull_heavy_2')}
for h, b in TPL.items():
    assert b, f'模板缺 {h}'
print('原版模板已取:', {h: len(b) for h, b in TPL.items()})


def make_variant(hull, name):
    """用原版模板生成新变体（改名、去 name_group）"""
    b = TPL[hull]
    b = re.sub(r'name = "[^"]*"', f'name = "{name}"', b, count=1)
    b = re.sub(r'(?m)^[ \t]*name_group[ \t]*=.*\r?\n', '', b)
    return b


for tag, base in COPIES:
    # 1) VAN 空壳
    p = os.path.join(base, 'history', 'units', 'VAN_1936_naval.txt')
    open(p, 'wb').write(b'units = {}\r\n')
    print(f'{tag}: VAN_1936_naval.txt 空壳恢复 ✓')

    # 2) PRI 舰名去重（顺序重编号：前缀 + 递增序号，全局唯一）
    p = os.path.join(base, 'history', 'units', 'PRI_1936_Naval.txt')
    if tag == '仓库':
        shutil.copy2(p, os.path.join(BD, 'PRI_1936_Naval.txt'))
    raw, t = load(p)
    seq = collections.Counter()

    def new_name(old):
        m2 = re.match(r'^(.+?)\s*\d+$', old)
        prefix = m2.group(1).strip() if m2 else old.strip()
        seq[prefix] += 1
        return f'{prefix} {seq[prefix]}'

    out, last, total = [], 0, 0
    for m in re.finditer(r'(ship = \{ name = ")([^"]+)(")', t):
        total += 1
        out.append(t[last:m.start(2)])
        out.append(new_name(m.group(2)))
        last = m.end(2)
    out.append(t[last:])
    t2 = ''.join(out)
    uniq = set(re.findall(r'ship = \{ name = "([^"]+)"', t2))
    assert len(uniq) == total, f'{tag}: 去重失败 {len(uniq)}/{total}'
    save(p, t2, raw[:3] == b'\xef\xbb\xbf')
    print(f'{tag}: PRI 舰名去重 {len(uniq)}/{total} ✓')

    # 3) INA/FAV 变体补充
    adds = {
        'INA - Inazuma.txt': [('ship_hull_cruiser_1', 'Sumeru_Class'),
                              ('ship_hull_cruiser_2', 'Sumeru_Class'),
                              ('ship_hull_light_1', 'Natlan_Class'),
                              ('ship_hull_light_1', 'Fontaine_Class'),
                              ('ship_hull_light_2', 'Snezhnaya_Class')],
        'FAV - Favonius.txt': [('ship_hull_heavy_2', 'Mondstadt_Class'),
                               ('ship_hull_light_1', 'Fontaine_Class')],
    }
    for fn, lst in adds.items():
        p = os.path.join(base, 'history', 'countries', fn)
        if tag == '仓库':
            shutil.copy2(p, os.path.join(BD, fn))
        raw, t = load(p)
        t = t.rstrip() + '\r\n\r\n'
        for hull, nm in lst:
            t += make_variant(hull, nm) + '\r\n\r\n'
        save(p, t, raw[:3] == b'\xef\xbb\xbf')
        print(f'{tag}: {fn} 补 {len(lst)} 个变体 ✓')

    # 4) 除零保护
    p = os.path.join(base, 'common', 'scripted_triggers', 'NewMOT_scripted_triggers.txt')
    if tag == '仓库':
        shutil.copy2(p, os.path.join(BD, 'NewMOT_scripted_triggers.txt'))
    raw, t = load(p)
    pat = re.compile(r'(?m)^([ \t]*)divide_temp_variable = \{ MOT_Temp_Var1 = MOT_SUM_Votes \}[ \t]*\r?$')

    def guard(m):
        ind = m.group(1)
        return (f'{ind}if = {{\r\n'
                f'{ind}\tlimit = {{ check_variable = {{ MOT_SUM_Votes > 0 }} }}\r\n'
                f'{ind}\tdivide_temp_variable = {{ MOT_Temp_Var1 = MOT_SUM_Votes }}\r\n'
                f'{ind}}}\r\n'
                f'{ind}else = {{ set_temp_variable = {{ MOT_Temp_Var1 = 0 }} }}')
    t2, n = pat.subn(guard, t)
    assert n == 8, f'{tag}: 除零保护 {n} 处（应 8）'
    save(p, t2, raw[:3] == b'\xef\xbb\xbf')
    print(f'{tag}: 除零保护 {n} 处 ✓')

print()
print('=== 验证 ===')
for tag, base in COPIES:
    p = os.path.join(base, 'history', 'units', 'VAN_1936_naval.txt')
    ok1 = open(p, 'rb').read() == b'units = {}\r\n'
    p = os.path.join(base, 'history', 'units', 'PRI_1936_Naval.txt')
    names = re.findall(r'ship = \{ name = "([^"]+)"', open(p, encoding='utf-8-sig').read())
    ok2 = len(names) == len(set(names))
    p = os.path.join(base, 'history', 'countries', 'INA - Inazuma.txt')
    ok3 = len(re.findall(r'create_equipment_variant', open(p, encoding='utf-8-sig').read())) >= 5
    p = os.path.join(base, 'common', 'scripted_triggers', 'NewMOT_scripted_triggers.txt')
    ok4 = len(re.findall(r'MOT_SUM_Votes > 0', open(p, encoding='utf-8-sig').read())) == 8
    print(f'  {tag}: VAN空壳={ok1} PRI去重={ok2}({len(names)}舰) INA变体={ok3} 除零保护={ok4}')
