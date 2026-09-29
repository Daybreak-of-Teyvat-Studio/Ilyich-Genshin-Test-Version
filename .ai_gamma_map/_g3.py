import os, io, re

MOD = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
VAN = r'C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV'
out = []

def read(p):
    try:
        return io.open(p, 'r', encoding='utf-8-sig', errors='replace').read()
    except Exception:
        return ''

# ---------- A. sprite-id level comparison for overridden .gfx files ----------
out.append('=== A. overridden interface/*.gfx : sprite ids dropped vs vanilla ===')
tot = 0
for dp, dn, fn in os.walk(os.path.join(MOD, 'interface')):
    for f in fn:
        if not f.lower().endswith('.gfx'):
            continue
        mp = os.path.join(dp, f)
        rel = os.path.relpath(mp, MOD)
        vp = os.path.join(VAN, rel)
        if not os.path.isfile(vp):
            continue
        vt, mt = read(vp), read(mp)
        vids = set(re.findall(r'name\s*=\s*"([^"]*)"', vt))
        mids = set(re.findall(r'name\s*=\s*"([^"]*)"', mt))
        missing = sorted(vids - mids)
        if missing:
            tot += len(missing)
            out.append('  %s : van=%d mod=%d MISSING %d' % (rel, len(vids), len(mids), len(missing)))
            out.append('      ' + ', '.join(missing[:40]))
out.append('  --- total dropped sprite ids: %d' % tot)

# ---------- B. every spriteType reference in MOD interface/** , is it defined anywhere (van+mod)? ----------
out.append('')
out.append('=== B. undefined sprite references inside MOD interface/ ===')
defs = {}
for root in (VAN, MOD):
    for dp, dn, fn in os.walk(os.path.join(root, 'interface')):
        for f in fn:
            if not f.lower().endswith(('.gfx', '.gui')):
                continue
            t = read(os.path.join(dp, f))
            for m in re.finditer(r'name\s*=\s*"([^"]*)"', t):
                defs[m.group(1)] = os.path.join(dp, f)
out.append('  sprite defs (van+mod): %d' % len(defs))
bad = {}
for dp, dn, fn in os.walk(os.path.join(MOD, 'interface')):
    for f in fn:
        if not f.lower().endswith(('.gui', '.gfx')):
            continue
        p = os.path.join(dp, f)
        t = read(p)
        for i, line in enumerate(t.split('\n'), 1):
            for m in re.finditer(r'(?:quadTextureSprite|spriteType)\s*=\s*"([^"]*)"', line):
                s = m.group(1)
                if s not in defs:
                    bad.setdefault(s, []).append((os.path.relpath(p, MOD), i))
for s in sorted(bad):
    out.append('  UNDEFINED %-38s used %d x : %s' % (s, len(bad[s]), bad[s][:4]))

# ---------- C. generic: which MOD interface/*.gui override vanilla and drop window elements ----------
out.append('')
out.append('=== C. gui overrides: element-level diff summary ===')

def parse_blocks(text):
    clean = re.sub(r'#[^\n]*', '', text)
    blocks = []
    stack = []
    for m in re.finditer(r'(\w+)\s*=\s*\{|\{|\}', clean):
        tok = m.group(0)
        if tok == '{':
            blocks.append({'key': None, 'name': None, 'depth': len(stack), 'start': m.start()})
            stack.append(len(blocks) - 1)
        elif tok == '}':
            if stack:
                i = stack.pop()
                blocks[i]['end'] = m.start()
        else:
            key = tok.split('=')[0].strip()
            blocks.append({'key': key, 'name': None, 'depth': len(stack), 'start': m.start()})
            stack.append(len(blocks) - 1)
    # assign names: first name= inside block, but only if it belongs directly (approx: within 300 chars)
    for b in blocks:
        if 'end' not in b:
            b['end'] = len(clean)
        seg = clean[b['start']:min(b['start'] + 400, b['end'])]
        m = re.search(r'name\s*=\s*"([^"]*)"', seg)
        if m:
            b['name'] = m.group(1)
    return blocks, clean

for dp, dn, fn in os.walk(os.path.join(MOD, 'interface')):
    for f in fn:
        if not f.lower().endswith('.gui'):
            continue
        mp = os.path.join(dp, f)
        rel = os.path.relpath(mp, MOD)
        vp = os.path.join(VAN, rel)
        if not os.path.isfile(vp):
            continue
        vb, _ = parse_blocks(read(vp))
        mb, _ = parse_blocks(read(mp))
        vn = set(b['name'] for b in vb if b['name'])
        mn = set(b['name'] for b in mb if b['name'])
        miss = sorted(vn - mn)
        if miss:
            out.append('  %s : van names=%d mod names=%d MISSING %d : %s' % (rel, len(vn), len(mn), len(miss), ', '.join(miss[:30])))

with io.open(r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\_g3.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('OK')
