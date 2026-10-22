# -*- coding: utf-8 -*-
"""Phase A 转省：1570→484, {1306,1960,3515}→435, 845→500"""
import os, io, re, sys, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(REPO, 'Daybreak of Teyvat Gamma Version')
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BD = os.path.join(REPO, '.backups', f'statesurg_{stamp}')
os.makedirs(BD, exist_ok=True)
o = []

MOVE = {1570: 484, 1306: 435, 1960: 435, 3515: 435, 845: 500}
edits = {}   # (label, sid) -> text

for label, root in [('repo', G), ('depl', DEPL)]:
    shutil.copytree(os.path.join(root, 'history', 'states'), os.path.join(BD, f'{label}_states'))
o.append(f'备份: {BD}')

def load(root, sid):
    fp = os.path.join(root, 'history', 'states', f'{sid}-State_{sid}.txt')
    raw = io.open(fp, 'rb').read()
    return fp, raw, raw.decode('utf-8-sig')

def provs_of(t):
    m = re.search(r'(provinces\s*=\s*\{)(\s*)([^}]*)(\s*)(\})', t, re.S)
    return [int(x) for x in m.group(3).split()], m

for label, root in [('repo', G), ('depl', DEPL)]:
    for prov, target in MOVE.items():
        # 找源州
        found = None
        for sid in range(1, 703):
            fp = os.path.join(root, 'history', 'states', f'{sid}-State_{sid}.txt')
            if not os.path.exists(fp):
                continue
            t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
            m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
            if str(prov) in [x for x in m.group(1).split()]:
                found = (sid, fp, t)
                break
        assert found, f'p{prov} 未找到源州'
        src_sid, src_fp, src_t = found
        o.append(f'[{label}] p{prov}: 源州 {src_sid} → 目标 {target}')
        # 1) 源州：移除省 + 取走 VP 行 + 取走省级块
        plist, m = provs_of(src_t)
        plist = [p for p in plist if p != prov]
        src_t2 = src_t[:m.start(3)] + ' '.join(str(p) for p in plist) + src_t[m.end(3):]
        # VP 行
        vp_pat = re.compile(r'(?m)^\t*victory_points\s*=\s*\{\s*' + str(prov) + r'\s+(\d+)\s*\}\r?\n')
        vm = vp_pat.search(src_t2)
        vp_line = None
        if vm:
            vp_line = f'\t\tvictory_points = {{ {prov} {vm.group(1)} }}\r\n'
            src_t2 = vp_pat.sub('', src_t2, count=1)
            o.append(f'    VP 行移走: {vp_line.strip()}')
        # 省级块（多行）
        bp = re.compile(r'\t+' + str(prov) + r'\s*=\s*\{')
        bm = bp.search(src_t2)
        blk = None
        if bm:
            depth = 0; k = bm.end() - 1
            while k < len(src_t2):
                if src_t2[k] == '{':
                    depth += 1
                elif src_t2[k] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            # 找块起始行的行首
            ls = src_t2.rfind('\n', 0, bm.start()) + 1
            le = k + 1
            while le < len(src_t2) and src_t2[le] in '\r\n':
                le += 1
            blk = src_t2[ls:le]
            src_t2 = src_t2[:ls] + src_t2[le:]
            o.append(f'    省级块移走: {blk[:60]!r}...')
        io.open(src_fp, 'wb').write(src_t2.encode('utf-8'))

        # 2) 目标州：加省 + 加 VP 行 + 加省级块（进 buildings 内）
        tgt_fp, _, tgt_t = load(root, target)
        tp, tm = provs_of(tgt_t)
        tp = sorted(set(tp) | {prov})
        tgt_t2 = tgt_t[:tm.start(3)] + ' '.join(str(p) for p in tp) + tgt_t[m.end(3):]
        if vp_line:
            vps = list(re.finditer(r'victory_points\s*=\s*\{[^}]*\}', tgt_t2))
            if vps:
                pos = vps[-1].end()
                while pos < len(tgt_t2) and tgt_t2[pos] in '\r\n':
                    pos += 1
                tgt_t2 = tgt_t2[:pos] + vp_line + tgt_t2[pos:]
            else:
                bi = tgt_t2.find('buildings = {')
                depth = 0; k = tgt_t2.find('{', bi)
                while k < len(tgt_t2):
                    if tgt_t2[k] == '{':
                        depth += 1
                    elif tgt_t2[k] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    k += 1
                pos = tgt_t2.find('\n', k) + 1
                tgt_t2 = tgt_t2[:pos] + vp_line + tgt_t2[pos:]
        if blk:
            bi = tgt_t2.find('buildings = {')
            depth = 0; k = tgt_t2.find('{', bi)
            while k < len(tgt_t2):
                if tgt_t2[k] == '{':
                    depth += 1
                elif tgt_t2[k] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            ls = tgt_t2.rfind('\n', 0, k) + 1
            tgt_t2 = tgt_t2[:ls] + blk + tgt_t2[ls:]
        io.open(tgt_fp, 'wb').write(tgt_t2.encode('utf-8'))

# 验证
o.append('')
o.append('===== 验证：转省后 =====')
sd = os.path.join(G, 'history', 'states')
p2s = {}
for f in sorted(os.listdir(sd)):
    if not f.endswith('.txt'):
        continue
    t = io.open(os.path.join(sd, f), 'rb').read().decode('utf-8-sig')
    sid = int(re.search(r'\bid\s*=\s*(\d+)', t).group(1))
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
    for p in m.group(1).split():
        p2s.setdefault(int(p), []).append(sid)
for prov, target in MOVE.items():
    o.append(f'  p{prov}: 现属州={p2s.get(prov)} (应=[{target}])')
for target in (484, 435, 500):
    t = io.open(os.path.join(sd, f'{target}-State_{target}.txt'), 'rb').read().decode('utf-8-sig')
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
    o.append(f'  州{target}: 省={m.group(1).split()}, VP块={re.findall(r"victory_points = {[^}]*}", t)}')
    o.append(f'       花括号 {t.count(chr(123))}={t.count(chr(125))}')
# 重复归属/丢失
dups = [p for p, s in p2s.items() if len(s) > 1]
o.append(f'  重复归属省: {dups if dups else "无 ✓"}')
# 源州一致性
for sid in (510, 511, 474, 499):
    t = io.open(os.path.join(sd, f'{sid}-State_{sid}.txt'), 'rb').read().decode('utf-8-sig')
    m = re.search(r'provinces\s*=\s*\{([^}]*)\}', t, re.S)
    o.append(f'  源州{sid}: 省={m.group(1).split()}, VP块={re.findall(r"victory_points = {[^}]*}", t)}, 括号 {t.count(chr(123))}={t.count(chr(125))}')
io.open(os.path.join(REPO, 'tools', 'phaseA_out.txt'), 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))
