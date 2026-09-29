import os, io, re

MOD = r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
VAN = r'C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV'
out = []

def read(p):
    try:
        return io.open(p, 'r', encoding='utf-8-sig', errors='replace').read()
    except Exception:
        return ''

# ---- collect all technology ids (van + mod) ----
tech = set()
for root in (VAN, MOD):
    d = os.path.join(root, 'common', 'technologies')
    if not os.path.isdir(d):
        continue
    for dp, dn, fn in os.walk(d):
        for f in fn:
            t = read(os.path.join(dp, f))
            for m in re.finditer(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{', t, re.M):
                tech.add(m.group(1))
out.append('tech ids (van+mod) = %d' % len(tech))

# ---- collect idea ids ----
ideas = set()
for root in (VAN, MOD):
    d = os.path.join(root, 'common', 'ideas')
    if not os.path.isdir(d):
        continue
    for dp, dn, fn in os.walk(d):
        for f in fn:
            t = read(os.path.join(dp, f))
            for m in re.finditer(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{', t, re.M):
                ideas.add(m.group(1))
out.append('idea ids (van+mod) = %d' % len(ideas))

# ---- history/units ----
for root, tag in ((VAN, 'VAN'), (MOD, 'MOD')):
    d = os.path.join(root, 'history', 'units')
    files = []
    if os.path.isdir(d):
        for dp, dn, fn in os.walk(d):
            for f in fn:
                files.append(os.path.relpath(os.path.join(dp, f), d))
    out.append('%s history/units files: %d %s' % (tag, len(files), files[:10]))

# ---- six new country files + NAT: check set_technology ids / ideas / portrait ext ----
TARGETS = ['NAT - Natlan.txt', 'NCE - Children_of_Echoes.txt', 'NSC - Scions_of_the_Canopy.txt',
           'NPS - People_of_the_Springs.txt', 'NCP - Collective_of_Plenty.txt',
           'NFF - Flower-Feather_Clan.txt', 'NMN - Masters_of_the_Night-Wind.txt']
hd = os.path.join(MOD, 'history', 'countries')

out.append('')
out.append('=== per-file audit ===')
for fn in TARGETS:
    p = os.path.join(hd, fn)
    if not os.path.isfile(p):
        out.append('%s : MISSING' % fn)
        continue
    t = read(p)
    lines = t.split('\n')
    bad_tech, bad_idea, pngs, oobs = [], [], [], []
    # set_technology block
    for m in re.finditer(r'set_technology\s*=\s*\{', t):
        i = m.end() - 1
        depth = 0
        j = i
        while j < len(t):
            if t[j] == '{':
                depth += 1
            elif t[j] == '}':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = t[i+1:j]
        body_nc = re.sub(r'#[^\n]*', '', body)
        for mm in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\d', body_nc):
            if mm.group(1) not in tech:
                bad_tech.append(mm.group(1))
    for mm in re.finditer(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*$', re.sub(r'#[^\n]*', '', t), re.M):
        pass
    # add_ideas block contents
    for m in re.finditer(r'add_ideas\s*=\s*\{([^}]*)\}', t):
        for w in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', m.group(1)):
            if w not in ideas:
                bad_idea.append(w)
    for mm in re.finditer(r'""?([^"\n]*\.png)"?', t):
        pngs.append(mm.group(1))
    for mm in re.finditer(r'set_naval_oob\s*=\s*"([^"]*)"', t):
        oobs.append(mm.group(1))
    for mm in re.finditer(r'oob\s*=\s*"([^"]*)"', t):
        oobs.append(mm.group(1))
    out.append('--- %s' % fn)
    out.append('   bad tech ids : %s' % (sorted(set(bad_tech)) or 'none'))
    out.append('   unknown ideas: %s' % (sorted(set(bad_idea)) or 'none'))
    out.append('   png refs     : %s' % (pngs or 'none'))
    out.append('   oob refs     : %s' % oobs)

# ---- where is DOT_geneGovernment_Control4 / Ilyich_Ruin_tech ----
out.append('')
out.append('=== search for the suspicious ids across VAN+MOD ===')
for key in ['DOT_geneGovernment_Control4', 'DOT_geneGovernment_Control', 'Ilyich_Ruin_tech', 'Daybreak_of_Teyvat']:
    hits = []
    for root, tag in ((VAN, 'VAN'), (MOD, 'MOD')):
        for dp, dn, fn in os.walk(root):
            if 'gfx' in dp or '.git' in dp:
                continue
            for f in fn:
                if not f.lower().endswith(('.txt', '.yml')):
                    continue
                p = os.path.join(dp, f)
                try:
                    t = io.open(p, 'r', encoding='utf-8-sig', errors='replace').read()
                except Exception:
                    continue
                if key in t:
                    hits.append(os.path.relpath(p, root) + '(' + tag + ')')
    out.append('  %-32s hits=%d %s' % (key, len(hits), hits[:6]))

# ---- navy leader ids collision ----
out.append('')
out.append('=== navy leader ids declared in history/countries (mod) ===')
ids = {}
for dp, dn, fn in os.walk(os.path.join(MOD, 'history')):
    for f in fn:
        t = read(os.path.join(dp, f))
        for m in re.finditer(r'create_navy_leader\s*=\s*\{([^}]*)\}', t, re.S):
            b = m.group(1)
            i = re.search(r'id\s*=\s*(\d+)', b)
            n = re.search(r'name\s*=\s*"([^"]*)"', b)
            if i:
                ids.setdefault(i.group(1), []).append((os.path.relpath(os.path.join(dp, f), MOD), n.group(1) if n else '?'))
dup = {k: v for k, v in ids.items() if len(v) > 1}
out.append('  declared ids: %d ; duplicated: %s' % (len(ids), dup if dup else 'none'))
out.append('  sample: %s' % list(ids.items())[:8])

with io.open(r'C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\_h1.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('OK')
