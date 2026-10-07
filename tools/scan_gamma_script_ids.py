# -*- coding: utf-8 -*-
"""scan_gamma_script_ids.py —— 扫描 gamma 脚本中的 beta 州/省 id 引用
（国策/决议/奇观/effect/trigger/on_actions/事件/国家历史…）
输出: tools/beta_refs_inventory.json（每条: 文件/行号/模式/片段/id/桥结果/状态）"""
import os, re, sys, glob, json, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
BR = json.load(open(os.path.join(ROOT, 'tools', 'beta_gamma_bridge.json'), encoding='utf-8'))
SB, PB = BR['state_bridge'], BR['prov_bridge']
BETA_STATE_IDS = {int(k) for k in SB}

TOKEN_RE = re.compile(r'\b(owns_state|controls_state|has_full_control_of|transfer_state|state)\s*=\s*(\d+)\b')
LIST_RE = re.compile(r'\b(states)\s*=\s*\{([^{}]*)\}')
PROV_RE = re.compile(r'\b(province|province_id)\s*=\s*(\d+)\b')
NUMKEY_RE = re.compile(r'^([ \t]*)(\d+)[ \t]*=[ \t]*\{')
MARKERS = ('add_dynamic_modifier', 'set_state_owner', 'set_state_controller', 'transfer_state',
           'add_building_construction', 'add_manpower', 'set_demilitarized_zone',
           'set_state_name', 'create_unit', 'add_resistance_target', 'set_victory_points',
           'owns_state', 'controls_state', 'has_full_control_of', 'state = ')
PATTERNS = {'owns_state': 'owns_state', 'controls_state': 'controls_state',
            'has_full_control_of': 'has_full_control_of', 'transfer_state': 'transfer_state',
            'state': 'state = N', 'states': 'states 列表', 'province': 'province = N',
            'province_id': 'province_id = N', 'numkey': '数字键州作用域块'}


def blank_comments(t):
    return re.sub(r'#[^\n]*', lambda m: ' ' * len(m.group(0)), t)


def line_of(t, pos):
    return t.count('\n', 0, pos) + 1


def snippet(t, pos):
    s = t.rfind('\n', 0, pos) + 1
    e = t.find('\n', pos)
    e = len(t) if e == -1 else e
    return t[s:e].strip()[:90]


def block_has_state_scope(cmt, brace):
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


rows = []
files_scanned = 0
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
        files_scanned += 1
        hits = []   # (line, pattern, id, snippet, guarded)
        for m in TOKEN_RE.finditer(cmt):
            hits.append((line_of(t, m.start()), PATTERNS[m.group(1)], int(m.group(2)),
                         snippet(t, m.start()), True))
        for m in LIST_RE.finditer(cmt):
            for x in m.group(2).split():
                if x.isdigit():
                    hits.append((line_of(t, m.start()), PATTERNS['states'], int(x),
                                 snippet(t, m.start()), True))
        for m in PROV_RE.finditer(cmt):
            hits.append((line_of(t, m.start()), PATTERNS[m.group(1)], int(m.group(2)),
                         snippet(t, m.start()), True))
        for m in NUMKEY_RE.finditer(cmt):
            k = int(m.group(2))
            guarded = block_has_state_scope(cmt, m.end() - 1)
            if guarded or 1 <= k <= 740:
                hits.append((line_of(t, m.start()), PATTERNS['numkey'], k,
                             snippet(t, m.start()), guarded))
        for line, pat, i, snip, guarded in hits:
            if pat == 'province = N' or pat == 'province_id = N' or pat == '数字键州作用域块' and i > 740:
                br = PB.get(str(i))
                kind = '省'
                gid = br['gamma_pid'] if br else None
                cn = br['cn'] if br else None
                if br:
                    st = br['status']
                else:
                    st = '? 无beta VP名（不可桥）'
            else:
                br = SB.get(str(i))
                kind = '州'
                if br:
                    gid, cn, st = br['gamma_id'], br['cn'], br['status']
                else:
                    gid = cn = None
                    st = '? id不在beta州列表（可能已是gamma号）'
            if pat == '数字键州作用域块' and not guarded:
                st = '⚠ 无州作用域标记（疑似权重/变量，默认不动）'
            rows.append({'file': rr, 'line': line, 'pattern': pat, 'id': i,
                         'kind': kind, 'beta_name': cn, 'gamma_id': gid,
                         'status': st, 'snippet': snip, 'guarded': guarded})

print(f'扫描 {files_scanned} 个脚本文件，引用 {len(rows)} 条')
stat = collections.Counter(r['status'].split('（')[0] for r in rows)
for k, v in stat.most_common():
    print(f'  {k}: {v}')
with open(os.path.join(ROOT, 'tools', 'beta_refs_inventory.json'), 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
print('已存 tools/beta_refs_inventory.json')
