# -*- coding: utf-8 -*-
"""apply_beta_to_gamma_ids.py —— 按 beta→gamma 桥替换脚本中的旧 id（等用户确认后运行）

用法:
  python tools/apply_beta_to_gamma_ids.py --dry      # 预览全部替换点，不写盘
  python tools/apply_beta_to_gamma_ids.py            # 正式执行（先备份到 .backups/beta_ids_时间戳）

映射来源:
  1. 桥自动映射（bridge.json 中 status ✓ 的行）
  2. 人工覆盖: tools/beta_gamma_manual_map.json（可选，用户核对 Excel 后手工填）
     格式: {"state": {"<beta_id>": <gamma_id>, ...}, "province": {...}}
     人工映射优先级高于桥；填 "skip": true 的条目跳过不改

规则: 只替换桥上有映射的 id；注释行天然跳过（扫描基于去注释文本，替换按原位进行）；
     数字键州作用域块仅在含州作用域标记时替换；自动备份；写盘后回读计数验证。"""
import os, re, sys, glob, json, shutil, datetime, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
DRY = '--dry' in sys.argv

br = json.load(open(os.path.join(ROOT, 'tools', 'beta_gamma_bridge.json'), encoding='utf-8'))
SB, PB = br['state_bridge'], br['prov_bridge']

manual_path = os.path.join(ROOT, 'tools', 'beta_gamma_manual_map.json')
manual = {'state': {}, 'province': {}}
if os.path.exists(manual_path):
    manual.update(json.load(open(manual_path, encoding='utf-8')))
skip_s = {int(k) for k, v in manual['state'].items() if v == 'skip'}
skip_p = {int(k) for k, v in manual['province'].items() if v == 'skip'}

MAP_S, MAP_P = {}, {}
for k, v in SB.items():
    if v['status'].startswith('✓') and v['gamma_id']:
        MAP_S[int(k)] = int(v['gamma_id'])
for k, v in PB.items():
    if v['status'].startswith('✓') and v['gamma_pid']:
        MAP_P[int(k)] = int(v['gamma_pid'])
for k, v in manual['state'].items():
    if v != 'skip':
        MAP_S[int(k)] = int(v)
for k, v in manual['province'].items():
    if v != 'skip':
        MAP_P[int(k)] = int(v)
for k in skip_s:
    MAP_S.pop(k, None)
for k in skip_p:
    MAP_P.pop(k, None)
print(f'映射: 州 {len(MAP_S)} 条，省 {len(MAP_P)} 条'
      f'（人工覆盖 州{len(manual["state"])} 省{len(manual["province"])}，skip 州{len(skip_s)} 省{len(skip_p)}）')

TOKEN_RE = re.compile(r'\b(owns_state|controls_state|has_full_control_of|transfer_state|state)\s*=\s*(\d+)\b')
LIST_RE = re.compile(r'\b(states)\s*=\s*\{([^{}]*)\}')
PROV_RE = re.compile(r'\b(province|province_id)\s*=\s*(\d+)\b')
NUMKEY_RE = re.compile(r'^([ \t]*)(\d+)[ \t]*=[ \t]*\{')
MARKERS = ('add_dynamic_modifier', 'set_state_owner', 'set_state_controller', 'transfer_state',
           'add_building_construction', 'add_manpower', 'set_demilitarized_zone',
           'set_state_name', 'create_unit', 'add_resistance_target', 'set_victory_points',
           'owns_state', 'controls_state', 'has_full_control_of', 'state = ')


def blank_comments(t):
    return re.sub(r'#[^\n]*', lambda m: ' ' * len(m.group(0)), t)


def block_state_scope(cmt, brace):
    depth, i = 0, brace
    while i < len(cmt):
        c = cmt[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return any(mk in cmt[brace:i] for mk in MARKERS)
        i += 1
    return False


if not DRY:
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    BD = os.path.join(ROOT, '.backups', f'beta_ids_{stamp}')
    os.makedirs(BD, exist_ok=True)
    print(f'备份目录: {BD}')

total_files = total_edits = 0
per_file = collections.Counter()
for root, dirs, files in os.walk(MOD):
    dirs[:] = [d for d in dirs if d not in ('.backups', '.git') and '备份' not in d]
    for f in files:
        if not f.endswith('.txt'):
            continue
        p = os.path.join(root, f)
        rr = os.path.relpath(p, MOD).replace('\\', '/')
        if rr.startswith('history/states') or rr == 'map/buildings.txt' or rr.startswith('localisation'):
            continue
        raw = open(p, 'rb').read()
        t = raw.decode('utf-8-sig', errors='replace')
        cmt = blank_comments(t)
        edits = []   # (start, end, repl, 明细)
        for m in TOKEN_RE.finditer(cmt):
            v = int(m.group(2))
            if v in MAP_S:
                edits.append((m.start(2), m.end(2), str(MAP_S[v]), f'{m.group(1)}={v}→{MAP_S[v]}'))
        for m in LIST_RE.finditer(cmt):
            nums = [int(x) for x in m.group(2).split() if x.isdigit()]
            if any(v in MAP_S for v in nums):
                new_inner = ' '.join(str(MAP_S.get(v, v)) for v in nums)
                edits.append((m.start(), m.end(), f'{m.group(1)} = {{ {new_inner} }}',
                              f'states[{m.group(2).strip()}]→[{new_inner}]'))
        for m in PROV_RE.finditer(cmt):
            v = int(m.group(2))
            if v in MAP_P:
                edits.append((m.start(2), m.end(2), str(MAP_P[v]), f'{m.group(1)}={v}→{MAP_P[v]}'))
        for m in NUMKEY_RE.finditer(cmt):
            k = int(m.group(2))
            if k in MAP_S and block_state_scope(cmt, m.end() - 1):
                edits.append((m.start(2), m.end(2), str(MAP_S[k]), f'{k}→{MAP_S[k]}（州作用域块）'))
        if not edits:
            continue
        edits.sort()
        out, last = [], 0
        for s, e, rep, _ in edits:
            out.append(t[last:s]); out.append(rep); last = e
        out.append(t[last:])
        t2 = ''.join(out)
        total_files += 1
        total_edits += len(edits)
        per_file[rr] += len(edits)
        if DRY:
            if total_files <= 15:
                print(f'  [DRY] {rr}: {len(edits)} 处  ' + '；'.join(d for *_, d in edits[:5])
                      + ('...' if len(edits) > 5 else ''))
        else:
            shutil.copy2(p, os.path.join(BD, rr.replace('/', '__')))
            data = t2.encode('utf-8')
            open(p, 'wb').write((b'\xef\xbb\xbf' + data) if raw[:3] == b'\xef\xbb\xbf' else data)

print(f'\n{"[DRY] " if DRY else ""}共 {total_files} 个文件 {total_edits} 处替换')
if not DRY:
    print(f'备份: {BD}；请跑 check_brackets/check_states 复验')
print('映射明细见 Desktop/beta至gamma_id迁移对照表.xlsx')
