# -*- coding: utf-8 -*-
"""audit_natlan_batch.py —— 核对纳塔批次指令（转省15 / 州名12 / VP5）在当前 mod 的落实情况

对照：
  1. 当前 mod 数据（states + localisation + history/countries）
  2. 批次前备份 .backups/states_20261003_200143（判断"从未落实"还是"后来丢失"）
  3. 10-03 names_natlan* 备份（上次会话当时写进了什么）
"""
import os, re, sys, glob

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
ST = os.path.join(MOD, 'history', 'states')
PRE = os.path.join(ROOT, '.backups', 'states_20261003_200143', 'history', 'states')

# ---------- 指令 ----------
TRANSFERS = [(399, 737), (389, 735), (2192, 707), (4298, 643), (4319, 643),
             (1243, 747), (4461, 810), (141, 828), (425, 828), (4414, 828),
             (4383, 767), (1472, 767), (4393, 767), (196, 782), (4367, 782)]
NAMES = [(1379, '柴薪之丘', True), (643, '圣火竞技场', False), (747, '烟谜主', False),
         (828, '溶水域', False), (810, '流泉之众', False), (781, '悬木人', False),
         (766, '彩石顶', False), (767, '祖遗庙宇', False), (814, '窃火者密岛', False),
         (782, '燃素开采研究所', False), (105, '浮土静界', False), (106, '玉裙之丘', False)]
VPS = [(2149, '烟谜主', 25, True), (389, None, None, False), (1482, '花羽会', 25, True),
       (4154, None, None, False), (4338, '燃素开采研究所', 10, False)]


def read(p):
    return open(p, encoding='utf-8-sig', errors='replace').read()


def scan_states(dirpath):
    """返回 {sid: {'provinces': set, 'vps': {pid: val}, 'owner': str, 'namekey': str}}"""
    out = {}
    for f in glob.glob(os.path.join(dirpath, '*.txt')):
        t = read(f)
        sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
        pv = re.search(r'provinces\s*=\s*\{([^}]*)\}', t)
        vps = {}
        for vm in re.finditer(r'victory_points\s*=\s*\{([^}]*)\}', t):
            xs = vm.group(1).split()
            for i in range(0, len(xs) - 1, 2):
                vps[int(xs[i])] = int(xs[i + 1])
        om = re.search(r'\bowner\s*=\s*(\w+)', t)
        nm = re.search(r'name\s*=\s*"DOT_STATE_(\d+)"', t)
        out[sid] = {'provinces': set(int(x) for x in pv.group(1).split()) if pv else set(),
                    'vps': vps, 'owner': om.group(1) if om else None,
                    'namekey': nm.group(1) if nm else None, 'file': f}
    return out


def scan_loc():
    """返回 (dot_state {id: name}, vp_names {pid: name})"""
    ds, vpn = {}, {}
    for p in glob.glob(os.path.join(MOD, 'localisation', '**', '*.yml'), recursive=True):
        for m in re.finditer(r'^\s*DOT_STATE_(\d+):\d*\s+"([^"]*)"', read(p), re.M):
            ds[int(m.group(1))] = m.group(2)
        for m in re.finditer(r'^\s*VICTORY_POINTS_(\d+):\d*\s+"([^"]*)"', read(p), re.M):
            vpn[int(m.group(1))] = m.group(2)
    return ds, vpn


def scan_capitals():
    caps = {}
    for p in glob.glob(os.path.join(MOD, 'history', 'countries', '*.txt')):
        tag = os.path.basename(p).split(' -')[0].strip()
        for m in re.finditer(r'(?m)^\s*capital\s*=\s*(\d+)', read(p)):
            caps[tag] = int(m.group(1))
    return caps


cur = scan_states(ST)
pre = scan_states(PRE) if os.path.isdir(PRE) else {}
ds, vpn = scan_loc()
caps = scan_capitals()


def prov2state(states, pid):
    return [s for s, d in states.items() if pid in d['provinces']]


n_ok = 0
rows = []

# ---------- 转省 ----------
for pid, tgt in TRANSFERS:
    now = prov2state(cur, pid)
    old = prov2state(pre, pid) if pre else []
    ok = now == [tgt]
    n_ok += ok
    rows.append(('转省', f'p{pid}→s{tgt}', ok,
                 f'现在在 {now or "无"}；批次前在 {old or "?"}'))

# ---------- 州名 ----------
for sid, nm, flag in NAMES:
    if flag:
        # 1379 超出州号上限，是省号语义：p1379 所在州应为该名（p1379 ∈ s720）
        host = prov2state(cur, 1379)
        ok = bool(host) and ds.get(host[0]) == nm
        n_ok += ok
        rows.append(('州名', f'p{sid}所在州「{nm}」', ok,
                     f'p{sid} 在 s{host or "?"}；该州现名「{ds.get(host[0]) if host else "?"}」'))
        continue
    exist = sid in cur
    loc = ds.get(sid)
    ok = exist and loc == nm
    n_ok += ok
    extra = f'本地化现值「{loc}」' if exist else '州不存在'
    key_ok = cur[sid]['namekey'] == str(sid) if exist else False
    if exist and not key_ok:
        extra += f'；state文件name键错指DOT_STATE_{cur[sid]["namekey"]}'
    rows.append(('州名', f's{sid}「{nm}」', ok, extra))

# ---------- VP ----------
for pid, nm, val, cap in VPS:
    hosts = prov2state(cur, pid)
    if nm is None:  # 清除
        gone = all(pid not in cur[h]['vps'] for h in hosts)
        loc_gone = pid not in vpn
        n_ok += gone
        rows.append(('VP清除', f'p{pid}', gone,
                     f'所在州 {hosts or "无"}；state VP 条目'
                     f'{"已清" if gone else "仍在: " + str({h: cur[h]["vps"].get(pid) for h in hosts})}'
                     f'；本地化 key {"已清" if loc_gone else "仍存在: " + vpn[pid]}'))
        continue
    h = hosts[0] if hosts else None
    in_state = h is not None and cur[h]['vps'].get(pid) == val
    loc_ok = vpn.get(pid) == nm
    cap_ok = True
    cap_msg = ''
    if cap and h is not None:
        owner = cur[h]['owner']
        # 双首都指令（s747 与 s722 同国且都标首都）按指令顺序取最后 → 722
        cap_ok = caps.get(owner) == 722
        cap_msg = f'；首都: {owner} capital={caps.get(owner)}（双首都取最后=722）'
    ok = in_state and loc_ok and cap_ok
    n_ok += ok
    msgs = []
    if h is None:
        msgs.append('省份不在任何州！')
    else:
        msgs.append(f'在 s{h}')
        msgs.append('state VP=' + (str(cur[h]['vps'].get(pid)) if pid in cur[h]['vps'] else '缺失')
                    + (f'（应={val}）' if pid in cur[h]['vps'] and cur[h]['vps'][pid] != val else ''))
        msgs.append(f'本地化「{vpn.get(pid)}」' + ('' if loc_ok else f'（应「{nm}」）'))
    rows.append(('VP', f'p{pid}「{nm}」{val}' + ('+首都' if cap else ''), ok,
                 '；'.join(msgs) + cap_msg))

# 首都专项：两个州都标了首都（s747 烟谜主、s722 花羽会），按指令顺序取最后 → NMN capital 应=722
cap_row = caps.get(cur[747]['owner'])
rows.append(('首都', '双首都取最后(722)', cap_row == 722, f'NMN capital={cap_row}'))

# ---------- 输出 ----------
W = 62
print(f'{"类别":<4}  {"指令":<24} {"落实":<4} 详情')
print('-' * 100)
for cat, item, ok, msg in rows:
    mark = '✓' if ok else '✗'
    print(f'{cat:<5} {item:<26} {mark:<3} {msg}')
miss = [r for r in rows if not r[2]]
print('-' * 100)
print(f'落实 {n_ok}/{len(rows)}；未落实 {len(miss)} 条')
