# -*- coding: utf-8 -*-
"""
fix_vp_pairs.py v2 —— 修复 victory_points 一 block 多对参数的语法错误

背景：HOI4 引擎的 set victory points 每个块只接受 2 个参数（省号 数值），
一 block 塞多对（{ a b c d }）会报
"set victory points takes 2 parameters" 且整块 VP 被丢弃。
原版所有 state 的 victory_points 块均为一对，多 VP 用多个块表达。

修复：把 { a b c d ... } 拆成多个 victory_points = { a b } 块。
字节级落地：保持原 CRLF / tab 缩进 / BOM 原样，不做全文替换。

用法:
    python tools/fix_vp_pairs.py --dry
    python tools/fix_vp_pairs.py            # 执行（自动备份到 .backups）
"""
import os, re, sys, glob, shutil, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version', 'history', 'states')
DRY = '--dry' in sys.argv

VP_RE = re.compile(r'(?m)^([ \t]*)victory_points[ \t]*=[ \t]*\{([^}]*)\}[ \t]*(?=\r?$)')


def fix_text(t, nl, report, fname):
    changed = 0

    def repl(m):
        nonlocal changed
        indent, inner = m.group(1), m.group(2).split()
        if len(inner) <= 2:
            return m.group(0)
        if len(inner) % 2 != 0:
            report.append(f'  !! 参数个数为奇数，跳过: {fname}: {inner}')
            return m.group(0)
        changed += 1
        blocks = [f'victory_points = {{ ' + ' '.join(inner[i:i + 2]) + ' }'
                  for i in range(0, len(inner), 2)]
        return indent + (nl + indent).join(blocks)

    return VP_RE.sub(repl, t), changed


hits = []
for p in sorted(glob.glob(os.path.join(ST, '*.txt'))):
    raw = open(p, 'rb').read()
    nl = '\r\n' if b'\r\n' in raw else '\n'
    t = raw.decode('utf-8-sig')
    t2, changed = fix_text(t, nl, [], os.path.basename(p))
    if changed:
        sid = os.path.basename(p).split('-')[0]
        pairs = re.findall(r'victory_points\s*=\s*\{([^}]*)\}', t)
        hits.append((p, t2, raw[:3] == b'\xef\xbb\xbf', nl))
        print(f'  state {sid}: ' + ' | '.join(' '.join(x.split()) for x in pairs if len(x.split()) != 2))

print(f'发现多对 VP 块的州: {len(hits)} 个')
if not hits:
    print('无需修复。')
    sys.exit(0)
if DRY:
    print('[DRY] 未写盘')
    sys.exit(0)

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bdir = os.path.join(ROOT, '.backups', f'vp_pairs_{stamp}')
os.makedirs(bdir, exist_ok=True)
for p, t2, has_bom, nl in hits:
    shutil.copy2(p, os.path.join(bdir, os.path.basename(p)))
    data = t2.encode('utf-8')
    if has_bom:
        data = b'\xef\xbb\xbf' + data
    open(p, 'wb').write(data)
print(f'已修复 {len(hits)} 个州文件，备份: {bdir}')
