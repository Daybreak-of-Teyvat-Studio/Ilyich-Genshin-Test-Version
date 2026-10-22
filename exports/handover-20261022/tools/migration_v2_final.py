# -*- coding: utf-8 -*-
"""migration_v2_final.py —— 扫描 v2（扩展模式）+ Excel v2
扩展模式：province=/province_id=/controls_province/owns_province/provinces={}列表/
         path={}列表/set_province_name id=/location=
Excel 输出：桌面 beta至gamma_id迁移对照表.xlsx（覆盖）
"""
import os, re, sys, glob, json, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
br = json.load(open(os.path.join(ROOT, 'tools', 'beta_gamma_bridge.json'), encoding='utf-8'))
SB = {int(k): v for k, v in br['state_bridge'].items()}
PB = {int(k): v for k, v in br['prov_bridge'].items()}
LIVE = set(br['live'])
DEAD = set(br['dead'])
g_p2s = {int(k): v for k, v in br['g_p2s'].items()}
g_owner = {int(k): v for k, v in br['g_owner'].items()}

TOKEN_RE = re.compile(r'\b(owns_state|controls_state|has_full_control_of_state|transfer_state|state)\s*=\s*(\d+)\b')
CTRL_PROV_RE = re.compile(r'\b(controls_province|owns_province)\s*=\s*(\d+)\b')
PROV_RE = re.compile(r'\b(province|province_id)\s*=\s*(\d+)\b')
LIST_RE = re.compile(r'\b(states)\s*=\s*\{([^{}]*)\}')
PLIST_RE = re.compile(r'\b(provinces|path)\s*=\s*\{([^{}]*)\}')
SETPN_RE = re.compile(r'set_province_name\s*=\s*\{[^}]*?\bid\s*=\s*(\d+)')
LOC_RE = re.compile(r'(?m)^\s*location\s*=\s*(\d+)')
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


def line_of(t, pos):
    return t.count('\n', 0, pos) + 1


def snippet(t, pos):
    s = t.rfind('\n', 0, pos) + 1
    e = t.find('\n', pos)
    e = len(t) if e == -1 else e
    return t[s:e].strip()[:90]


rows = []
nfiles = 0
for root, dirs, files in os.walk(G):
    dirs[:] = [d for d in dirs if d not in ('.backups', '.backup', '.git', '备份')]
    for f in files:
        if not f.endswith('.txt'):
            continue
        p = os.path.join(root, f)
        rr = os.path.relpath(p, G).replace('\\', '/')
        if rr.startswith('history/states') or rr == 'map/buildings.txt' or rr.startswith('localisation') or rr.startswith('map/'):
            continue
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        cmt = blank_comments(t)
        nfiles += 1
        hits = []
        for m in TOKEN_RE.finditer(cmt):
            hits.append((line_of(t, m.start()), 'state 族', int(m.group(2)), snippet(t, m.start()), '州'))
        for m in CTRL_PROV_RE.finditer(cmt):
            hits.append((line_of(t, m.start()), m.group(1), int(m.group(2)), snippet(t, m.start()), '省'))
        for m in PROV_RE.finditer(cmt):
            hits.append((line_of(t, m.start()), m.group(1), int(m.group(2)), snippet(t, m.start()), '省'))
        for m in LIST_RE.finditer(cmt):
            for x in m.group(2).split():
                if x.isdigit():
                    hits.append((line_of(t, m.start()), 'states 列表', int(x), snippet(t, m.start()), '州'))
        for m in PLIST_RE.finditer(cmt):
            for x in m.group(2).split():
                if x.isdigit():
                    hits.append((line_of(t, m.start()), f'{m.group(1)} 列表', int(x), snippet(t, m.start()), '省'))
        for m in SETPN_RE.finditer(cmt):
            hits.append((line_of(t, m.start()), 'set_province_name id', int(m.group(1)), snippet(t, m.start()), '省'))
        for m in LOC_RE.finditer(cmt):
            hits.append((line_of(t, m.start()), 'location', int(m.group(1)), snippet(t, m.start()), '省'))
        for m in NUMKEY_RE.finditer(cmt):
            k = int(m.group(2))
            if block_state_scope(cmt, m.end() - 1):
                hits.append((line_of(t, m.start()), '数字键州作用域块', k, snippet(t, m.start()), '州'))
        for line, pat, i, snip, kind in hits:
            if kind == '州':
                rec = SB.get(i)
                if rec and rec['status'].startswith('✓'):
                    st, gid = rec['status'], rec['gamma_id']
                elif rec:
                    st, gid = '⚠ 州名未匹配（' + rec['status'] + '）', None
                else:
                    st, gid = '? id 不在 beta 州表（可能已是 gamma 号）', None
                cn = rec['cn'] if rec else None
            else:
                rec = PB.get(i)
                if rec and rec['status'].startswith('✓'):
                    st, gid = rec['status'], rec['gamma_pid']
                elif rec:
                    st, gid = '⚠ ' + rec['status'], None
                else:
                    st, gid = '? id 不在 beta 地标表（可能已是 gamma 号/无名省）', None
                cn = rec['cn'] if rec else None
            rows.append({'file': rr, 'line': line, 'pattern': pat, 'id': i, 'kind': kind,
                         'beta_name': cn, 'gamma_id': gid, 'status': st, 'snippet': snip})

stat = collections.Counter(r['status'].split('（')[0] for r in rows)
print(f'扫描 {nfiles} 文件，引用 {len(rows)} 条')
for k, v in stat.most_common(12):
    print(f'  {k}: {v}')
json.dump(rows, open(os.path.join(ROOT, 'tools', 'beta_refs_inventory.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ---------- Excel v2 ----------
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

GREEN = PatternFill('solid', fgColor='C6EFCE')
RED = PatternFill('solid', fgColor='FFC7CE')
YELL = PatternFill('solid', fgColor='FFEB9C')
HDR = Font(bold=True)
OUT = os.path.join(os.path.expanduser('~'), 'Desktop', 'beta至gamma_id迁移对照表.xlsx')
wb = Workbook()


def sheet(ws, headers, data, widths, status_col=None):
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        ws.cell(1, c).font = HDR
        ws.column_dimensions[get_column_letter(c)].width = widths[c - 1]
    for row in data:
        ws.append(row)
        if status_col:
            v = str(row[status_col - 1] or '')
            cell = ws.cell(ws.max_row, status_col)
            cell.fill = GREEN if v.startswith('✓') else (RED if v.startswith('✗') else YELL)
    ws.freeze_panes = 'A2'


ws = wb.active
ws.title = '总览'
info = [
    ('生成说明', 'v2：以【州文件实际使用的 VP（活键237）】为可信源；同号且未被使用的 loc 键=陈旧移植（死键264）'),
    ('引用总数', len(rows)),
    ('可自动映射 ✓', sum(v for k, v in stat.items() if k.startswith('✓'))),
    ('陈旧/未匹配 ⚠', sum(v for k, v in stat.items() if k.startswith('⚠'))),
    ('未知 ?（可能已是 gamma 号）', sum(v for k, v in stat.items() if k.startswith('?'))),
    ('地标映射（省）', '✓修正 32 + ✓同号活键 4；⚠仅死键 254；✗gamma无名 54（见「地标映射表」）'),
    ('州映射', '✓ 143 个干净映射（见「州映射表」）'),
    ('待人工', '（1）⚠陈旧类地标请给正确 gamma 号；（2）?未知类可能是迁移后残留 beta 号，按文件上下文核对'),
    ('人工映射文件', 'tools/beta_gamma_manual_map.json：{"province": {"1314": 442}} 形式，填入后重跑本脚本生效'),
]
for k, v in info:
    ws.append([k, v])
ws.column_dimensions['A'].width = 30
ws.column_dimensions['B'].width = 110

ws = wb.create_sheet('地标映射表')
data = []
for k in sorted(PB):
    v = PB[k]
    gid = v['gamma_pid']
    st = v['status']
    stt = f"s{g_p2s.get(gid)}（{g_owner.get(g_p2s.get(gid))}）" if gid else ''
    data.append([k, v['cn'] or '', gid or '', stt, st, v.get('note', '')])
sheet(ws, ['beta省号', 'beta中文名', 'gamma省号', 'gamma州(owner)', '状态', '备注'], data,
      [9, 22, 10, 22, 24, 34], status_col=5)

ws = wb.create_sheet('州映射表')
data = [[k, v['en'] or '', v['cn'] or '', v['gamma_id'] or '', v['status'], v.get('note', '')]
        for k, v in sorted(SB.items())]
sheet(ws, ['beta州号', 'beta英文名', 'beta中文名', 'gamma州号', '状态', '备注'], data,
      [9, 26, 20, 10, 20, 26], status_col=5)

ws = wb.create_sheet('引用明细')
data = [[r['file'], r['line'], r['pattern'], r['snippet'], r['id'], r['beta_name'] or '',
         r['gamma_id'] or '', r['status']] for r in rows]
sheet(ws, ['文件路径', '行号', '模式', '片段', 'beta号', 'beta名', 'gamma号', '状态'], data,
      [44, 7, 18, 58, 8, 20, 9, 30], status_col=8)

ws = wb.create_sheet('待人工清单')
groups = collections.defaultdict(list)
for r in rows:
    if not r['status'].startswith('✓'):
        groups[(r['kind'], r['id'], r['status'], r['beta_name'])].append(r)
data = []
for (kind, i, st, nm), rs in sorted(groups.items(), key=lambda kv: (kv[0][0], -len(kv[1]))):
    files = collections.Counter(x['file'] for x in rs)
    data.append([kind, i, nm or '', st, len(rs),
                 '；'.join(f'{k}×{v}' for k, v in files.most_common(4))])
sheet(ws, ['类型', 'beta号', 'beta名', '状态', '次数', '涉及文件(前4)'], data,
      [8, 8, 20, 30, 7, 90], status_col=4)

wb.save(OUT)
print(f'Excel v2 已写入: {OUT}')
print(f'  地标映射表 {len(PB)} 行，州映射表 {len(SB)} 行，引用明细 {len(rows)} 行，待人工 {len(data)} 组')
