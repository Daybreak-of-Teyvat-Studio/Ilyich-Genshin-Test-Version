# -*- coding: utf-8 -*-
"""test_fill_gaps_refs.py —— fill_state_gaps v4 引用联动迁移的合成用例自测

搭一个迷你 mod（6 陆州 + 1 海州，2 号州为空），跑 skill 的 fill_state_gaps.py，
校验：州文件搬移、buildings/capital/本地化联动、三类州号引用迁移、注释与无标记块不误伤。
"""
import os, sys, shutil, subprocess, tempfile, re

sys.stdout.reconfigure(encoding='utf-8')
SCRIPT = r'C:\Users\LR\.zcode\skills\hoi4-modder-cn\scripts\fill_state_gaps.py'
CRLF = '\r\n'


def w(path, text, bom=False, crlf=True):
    if crlf:
        text = text.replace('\n', CRLF)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'wb').write((b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8'))


def r(path):
    return open(path, 'rb').read().decode('utf-8-sig')


tmp = tempfile.mkdtemp(prefix='fgtest_')
mod = os.path.join(tmp, 'mod')

# ---- 州文件：1-6 陆（AAA），7 海；2 号空 ----
for sid, provs, owner in [(1, '11 12', 'AAA'), (2, '', 'AAA'), (3, '31', 'AAA'),
                          (4, '41', 'AAA'), (5, '51', 'AAA'), (6, '61', 'AAA'), (7, '71 72', '')]:
    own = f'\towner = {owner}{CRLF}\tadd_core_of = {owner}{CRLF}' if owner else ''
    w(os.path.join(mod, 'history', 'states', f'{sid}-State_{sid}.txt'), f'''state = {{
	id = {sid}
	name="DOT_STATE_{sid}"
	manpower = 1000
	state_category = town
	history = {{
{own}\t\tvictory_points = {{ 9{sid} 5 }}
	}}
	provinces = {{
		{provs}
	}}
}}''')

# ---- 引用文件 ----
w(os.path.join(mod, 'common', 'decisions', 'test_dec.txt'), f'''decision = {{
	6 = {{ add_dynamic_modifier = {{ modifier = X }} }}
	controls_state = 6
	owns_state = 5
	states = {{ 6 100 }}
	random_list = {{
		6 = {{ add_political_power = 100 }}
	}}
	has_full_control_of = 7
	transfer_state = 7
	# state = 6  注释里不该动
}}''')
w(os.path.join(mod, 'common', 'ai_strategy', 'test_ai.txt'),
  'ai_strategy = {\n\ttype = put_unit_buffers\n\tstates = { \n\t\t6\n\t\t100\n\t}\n}\n')
w(os.path.join(mod, 'history', 'countries', 'AAA.txt'), 'capital = 6\n')
w(os.path.join(mod, 'map', 'buildings.txt'),
  '4;arms_factory;1;1;2;0;41\r\n6;arms_factory;1;1;2;0;61\r\n7;naval_base;2;2;1;0;71\r\n')
w(os.path.join(mod, 'localisation', 'simp_chinese', 'test_l_simp_chinese.yml'),
  'l_simp_chinese:\n DOT_STATE_2:0 "*"\n DOT_STATE_6:0 "六号"\n DOT_STATE_7:0 "海七"\n', bom=True)

# ---- dry 预览 ----
p = subprocess.run([sys.executable, '-X', 'utf8', SCRIPT, '--mod', mod, '--dry'],
                   capture_output=True, text=True, encoding='utf-8')
assert p.returncode == 0, p.stdout + p.stderr
print(p.stdout)

# ---- 执行 ----
p = subprocess.run([sys.executable, '-X', 'utf8', SCRIPT, '--mod', mod],
                   capture_output=True, text=True, encoding='utf-8')
assert p.returncode == 0, p.stdout + p.stderr
print(p.stdout)
assert '搬移方案' in p.stdout

ok = []


def check(name, cond):
    ok.append((name, cond))


# 预期搬移：2(空删) ← 6(陆尾)；6 ← 7(海尾)。moved = {6:2, 7:6}
st = os.path.join(mod, 'history', 'states')
check('空州 2 已删（原空内容被陆尾覆盖，不再是空州）',
      '61' in r(os.path.join(st, '2-State_2.txt'))
      and re.search(r'provinces\s*=\s*\{\s*\}', r(os.path.join(st, '2-State_2.txt'))) is None)
check('陆尾 6 搬到 2', os.path.exists(os.path.join(st, '2-State_2.txt'))
      and 'id = 2' in r(os.path.join(st, '2-State_2.txt'))
      and 'DOT_STATE_2' in r(os.path.join(st, '2-State_2.txt'))
      and '61' in r(os.path.join(st, '2-State_2.txt')))
check('海尾 7 搬到 6', os.path.exists(os.path.join(st, '6-State_6.txt'))
      and 'id = 6' in r(os.path.join(st, '6-State_6.txt'))
      and '71 72' in r(os.path.join(st, '6-State_6.txt')))
check('7 号旧文件已删', not os.path.exists(os.path.join(st, '7-State_7.txt')))

dec = r(os.path.join(mod, 'common', 'decisions', 'test_dec.txt'))
check('数字键州作用域块 6→2', '2 = { add_dynamic_modifier = { modifier = X } }' in dec)
check('单值 token controls_state 6→2', 'controls_state = 2' in dec)
check('has_full_control_of 7→6', 'has_full_control_of = 6' in dec)
check('transfer_state 7→6', 'transfer_state = 6' in dec)
check('states 列表 6→2', 'states = { 2 100 }' in dec)
check('无标记 random_list 数字键不误伤', '6 = { add_political_power = 100 }' in dec)
check('注释里的 state = 6 不误伤', '# state = 6' in dec)
check('未搬州 owns_state = 5 不动', 'owns_state = 5' in dec)
check('CRLF 保持', '\r\n' in dec and '\r\r' not in dec)

ai = r(os.path.join(mod, 'common', 'ai_strategy', 'test_ai.txt'))
check('ai_strategy states 列表 6→2', '2\n\t\t100' in ai.replace('\r\n', '\n').replace('\t', '\n\t') or '2' in ai.split('states = {')[1].split('}')[0])

cap = r(os.path.join(mod, 'history', 'countries', 'AAA.txt'))
check('capital 6→2', 'capital = 2' in cap)

b = r(os.path.join(mod, 'map', 'buildings.txt'))
check('buildings 6→2', '2;arms_factory;1;1;2;0;61' in b)
check('buildings 7→6', '6;naval_base;2;2;1;0;71' in b)
check('buildings 4 不动', '4;arms_factory;1;1;2;0;41' in b)

loc_raw = open(os.path.join(mod, 'localisation', 'simp_chinese', 'test_l_simp_chinese.yml'), 'rb').read()
check('本地化 BOM 保持', loc_raw[:3] == b'\xef\xbb\xbf')
loc = loc_raw.decode('utf-8-sig')
check('DOT_STATE_6 名随州搬去 2（覆盖 *）', 'DOT_STATE_2:0 "六号"' in loc)
check('DOT_STATE_7 名随州搬去 6', 'DOT_STATE_6:0 "海七"' in loc)

# 终验：1-6 连号
ids = sorted(int(f.split('-')[0]) for f in os.listdir(st) if f.endswith('.txt'))
check('州号 1-6 连号', ids == [1, 2, 3, 4, 5, 6])

bad = [n for n, c in ok if not c]
for n, c in ok:
    print(('  ✓ ' if c else '  ✗ ') + n)
print(f'\n{len(ok) - len(bad)}/{len(ok)} 通过')
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if bad else 0)
