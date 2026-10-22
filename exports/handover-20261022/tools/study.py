# -*- coding: utf-8 -*-
"""研究：setup gui 的 idea 块 + bookmark 结构，三方对照（Gamma / Beta / 原版）"""
import os, io, re, sys, difflib
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
B = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version'
V = r'F:\Steam\steamapps\common\Hearts of Iron IV'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\study_out.txt'
o = []

def rd(p):
    return io.open(p, 'rb').read().decode('utf-8-sig', errors='replace')

def close_brace(t, s):
    d = 0; k = s
    while k < len(t):
        if t[k] == '{': d += 1
        elif t[k] == '}':
            d -= 1
            if d == 0: return k + 1
        k += 1
    return -1

def block(t, name):
    m = re.search(r'name\s*=\s*"' + re.escape(name) + r'"', t)
    if not m: return None
    st = None
    for m2 in re.finditer(r'(?m)^[ \t]*[A-Za-z_]+\s*=\s*\{', t[:m.start()]):
        st = m2
    if st is None: return None
    bs = t.index('{', st.start())
    return t[st.start():close_brace(t, bs)]

# 1) idea 相关块三方对照
o.append('########## idea 块三方对照 ##########')
for label, root in [('Gamma', G), ('Beta', B), ('原版', V)]:
    fp = os.path.join(root, 'interface', 'frontendgamesetupview.gui')
    if not os.path.exists(fp):
        o.append(f'{label}: 无文件')
        continue
    t = rd(fp)
    date = os.path.getsize(fp)
    o.append(f'--- {label} ({date}B) ---')
    for nm in ('spirit_idea_entry', 'spirit_idea_entry_small', 'ideas', 'ideas_grid'):
        b = block(t, nm)
        if b:
            o.append(f'  [{nm}] ' + ' '.join(b.split())[:240])
        else:
            o.append(f'  [{nm}] 未找到')
    o.append('')

# 2) bookmark 结构三方对照
o.append('########## bookmark 三方对照 ##########')
for label, root in [('Gamma', G), ('Beta', B), ('原版', V)]:
    d = os.path.join(root, 'common', 'bookmarks')
    if not os.path.isdir(d):
        o.append(f'{label}: 无 bookmarks 目录')
        continue
    fs = sorted(os.listdir(d))
    o.append(f'--- {label}: {len(fs)} 个文件: {fs[:6]} ---')
    for f in fs[:4]:
        t = rd(os.path.join(d, f))
        tags = re.findall(r'(?m)^[ \t]*"?([A-Z]{3})"?\s*=\s*\{', t)
        o.append(f'  {f} ({len(t)}B): {len(tags)} 国, 前 12={tags[:12]}')
        # 书签级字段
        for key in ('default_country', 'filters', 'picture', 'date'):
            mm = re.search(r'(?m)^\s*(' + key + r'\s*=\s*[^\r\n]*)', t)
            o.append(f'      {key}: {mm.group(1).strip()[:90] if mm else "（无）"}')
    o.append('')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('\n'.join(o))
