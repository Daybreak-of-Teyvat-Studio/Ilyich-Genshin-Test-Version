import os, io, re

MOD = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
VAN = r'C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV'
out = []

def read(p):
    return io.open(p, 'r', encoding='utf-8-sig', errors='replace').read()

# ---------- 1. exact vanilla blocks for the missing names ----------
def strip_comments(t):
    return re.sub(r'#[^\n]*', '', t)

def find_blocks_with_name(text, names):
    """return dict name -> exact source slice of the block whose name = "<name>" """
    res = {}
    clean = strip_comments(text)
    for m in re.finditer(r'(\w+)\s*=\s*\{', clean):
        start = m.start()
        # first name in this block
        seg = clean[m.end():m.end()+400]
        nm = re.search(r'name\s*=\s*"([^"]*)"', seg)
        if not nm:
            continue
        if nm.group(1) not in names:
            continue
        # brace match from the '{' at m.end()-1
        i = m.end() - 1
        depth = 0
        while i < len(clean):
            c = clean[i]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        res[nm.group(1)] = (start, i + 1, text[start:i+1])
    return res

vgui = read(os.path.join(VAN, 'interface', 'frontendgamesetupview.gui'))
mgui = read(os.path.join(MOD, 'interface', 'frontendgamesetupview.gui'))
need = ['more_countries', 'filters', 'new_content', 'country_name', 'country_leader',
        'Background', 'expand_button', 'expanded_window', 'countries_mini_expanded']
vb = find_blocks_with_name(vgui, set(need))
out.append('=== VANILLA BLOCKS for missing names ===')
for n in need:
    if n in vb:
        out.append('----- %s (van offset %d..%d) -----' % (n, vb[n][0], vb[n][1]))
        out.append(vb[n][2])
    else:
        out.append('----- %s : NOT FOUND by parser -----' % n)

# ---------- 2. sprite refs in MOD gui, including weird ones ----------
out.append('')
out.append('=== MOD gui: all spriteType/quadTexture/button refs ===')
for m in re.finditer(r'(spriteType|quadTextureSprite)\s*=\s*"([^"]*)"', mgui):
    out.append('  %-20s %s' % (m.group(1), m.group(2)))
out.append('')
out.append('=== occurrences of filter_entry / 238x38 in MOD gui ===')
for pat in ['filter_entry', '238x38', 'GFX country', 'country filter']:
    idx = [i+1 for i, l in enumerate(mgui.split('\n')) if pat in l]
    out.append('  %-16s lines: %s' % (pat, idx[:20]))
out.append('=== occurrences in VAN gui ===')
for pat in ['filter_entry', '238x38']:
    idx = [i+1 for i, l in enumerate(vgui.split('\n')) if pat in l]
    out.append('  %-16s lines: %s' % (pat, idx[:20]))

# ---------- 3. who defines those sprites (van + mod, file-level override check) ----------
out.append('')
out.append('=== sprite definition search (van + mod) ===')
for target in ['GFX_country_filter_entry', 'GFX_button_238x38', 'GFX_country_filter_entry_shine']:
    hits = []
    for root in (VAN, MOD):
        for dp, dn, fn in os.walk(os.path.join(root, 'interface')):
            for f in fn:
                if not f.lower().endswith(('.gfx', '.gui')):
                    continue
                p = os.path.join(dp, f)
                try:
                    t = read(p)
                except Exception:
                    continue
                if re.search(r'name\s*=\s*"%s"' % re.escape(target), t):
                    hits.append(p)
    out.append('  %-34s defined in: %s' % (target, hits if hits else 'NONE'))

# ---------- 4. MOD interface files vs vanilla same path (stale-copy scan) ----------
out.append('')
out.append('=== MOD interface overrides vs vanilla (size ratio) ===')
rows = []
for dp, dn, fn in os.walk(os.path.join(MOD, 'interface')):
    for f in fn:
        mp = os.path.join(dp, f)
        rel = os.path.relpath(mp, MOD)
        vp = os.path.join(VAN, rel)
        if os.path.isfile(vp):
            ms, vs = os.path.getsize(mp), os.path.getsize(vp)
            rows.append((ms / vs if vs else 1.0, rel, ms, vs))
rows.sort()
for r, rel, ms, vs in rows[:40]:
    out.append('  %5.1f%%  %-60s mod=%8d van=%8d' % (r * 100, rel, ms, vs))
out.append('  total overrides: %d' % len(rows))

with io.open(r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\_g2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('OK')
