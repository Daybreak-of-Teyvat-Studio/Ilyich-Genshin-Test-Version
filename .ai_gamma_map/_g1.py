import os, io, re, json

MOD = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
VAN = r'C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV'
REL = 'interface/frontendgamesetupview.gui'

out = []

def parse(path):
    t = io.open(path, 'r', encoding='utf-8-sig', errors='replace').read()
    t = re.sub(r'#[^\n]*', '', t)
    toks = []
    for m in re.finditer(r'(\w+)\s*=\s*\{|\{|\}|"([^"]*)"', t):
        toks.append((m.group(0), m.start()))
    # brace-stack: record every block (type, name, depth)
    stack = []
    blocks = []   # (typename, name, depth, start_pos)
    cur_key = None
    lines = t.split('\n')
    def lineno(pos):
        return t.count('\n', 0, pos) + 1
    for tok, pos in toks:
        if tok.endswith('{') and len(tok) > 1:
            key = tok.split('=')[0].strip()
            # look ahead for first name = "..."
            nm = None
            seg = t[pos:pos+3000]
            m = re.search(r'name\s*=\s*"([^"]*)"', seg)
            if m:
                nm = m.group(1)
            blocks.append(['block', key, nm, len(stack), lineno(pos), pos])
            stack.append(blocks[-1])
        elif tok == '{':
            blocks.append(['anon', None, None, len(stack), lineno(pos), pos])
            stack.append(blocks[-1])
        elif tok == '}':
            if stack:
                b = stack.pop()
                b.append(lineno(pos))
    return blocks, t

mb, mt = parse(os.path.join(MOD, REL))
vb, vt = parse(os.path.join(VAN, REL))
out.append('MOD blocks=%d  VAN blocks=%d  MOD lines=%d VAN lines=%d' % (len(mb), len(vb), mt.count('\n')+1, vt.count('\n')+1))

def windows(blocks):
    # map windowame -> set of element names directly or nested inside, and list of window records
    ws = []
    for b in blocks:
        if b[1] and b[1].lower() in ('windowtype','containerwindowtype'):
            ws.append(b)
    return ws

def owner_window(blocks, idx):
    b = blocks[idx]
    d = b[3]
    for j in range(idx-1, -1, -1):
        if blocks[j][3] < d and blocks[j][1] and blocks[j][1].lower() in ('windowtype','containerwindowtype'):
            return blocks[j][2]
        if blocks[j][3] < d and blocks[j][1] in ('guiTypes',):
            return None
    return None

def named_in_window(blocks, wname, wtype_of=None):
    res = []
    for i, b in enumerate(blocks):
        if b[2] == wname and b[1] and b[1].lower() in ('windowtype','containerwindowtype'):
            # collect all named descendants until depth returns
            d = b[3]
            for j in range(i+1, len(blocks)):
                if blocks[j][3] <= d:
                    break
                if blocks[j][2]:
                    res.append((blocks[j][1], blocks[j][2], blocks[j][4]))
            break
    return res

diff = []
allw = set(b[2] for b in vb if b[2] and b[1] and b[1].lower() in ('windowtype','containerwindowtype'))
for w in sorted(x for x in allw if x):
    vn = named_in_window(vb, w)
    mn = named_in_window(mb, w)
    vnames = set(x[1] for x in vn)
    mnames = set(x[1] for x in mn)
    miss = sorted(vnames - mnames)
    extra = sorted(mnames - vnames)
    if miss or extra:
        diff.append((w, miss, extra, len(vnames), len(mnames)))
out.append('')
out.append('=== WINDOW DIFF (vanilla -> mod) ===')
for w, miss, extra, a, b2 in sorted(diff, key=lambda x: -len(x[1])):
    out.append('WIN %-46s van=%3d mod=%3d  MISSING(%d): %s' % (w, a, b2, len(miss), ', '.join(miss[:25])))
    if extra:
        out.append('      EXTRA-in-mod(%d): %s' % (len(extra), ', '.join(extra[:25])))

# windows present in mod but not vanilla
mw = set(x[2] for x in mb if x[2] and x[1] and x[1].lower() in ('windowtype','containerwindowtype'))
out.append('')
out.append('windows only in MOD: %s' % sorted(x for x in mw - allw if x))
out.append('windows only in VAN: %s' % sorted(x for x in allw - mw if x))

# sprite references in mod gui
def sprites_used(text):
    s = set()
    for m in re.finditer(r'(?:spriteType|sprite)\s*=\s*"([^"]*)"', text):
        s.add(m.group(1))
    return s
out.append('')
out.append('=== MOD gui sprite refs (%d) ===' % len(sprites_used(mt)))
out.append(', '.join(sorted(sprites_used(mt))))

# build sprite definition set from vanilla + mod
defs = {}
for root in (VAN, MOD):
    for dp, dn, fn in os.walk(os.path.join(root, 'interface')):
        for f in fn:
            if not f.lower().endswith(('.gfx', '.gui')):
                continue
            p = os.path.join(dp, f)
            try:
                txt = io.open(p, 'r', encoding='utf-8-sig', errors='replace').read()
            except Exception:
                continue
            for m in re.finditer(r'name\s*=\s*"([^"]*)"', txt):
                defs.setdefault(m.group(1), p)
out.append('')
out.append('total sprite defs (van+mod) = %d' % len(defs))
for s in sorted(sprites_used(mt)):
    out.append('  %-40s defined=%s' % (s, defs.get(s, 'NO')))

with io.open(r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\_g1.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('OK', len(out))
