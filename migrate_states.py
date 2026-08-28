# -*- coding: utf-8 -*-
"""Beta -> Gamma state content migration (方案B geometric mapping)."""
import csv, os, re, sys
from collections import defaultdict, Counter
import numpy as np
from PIL import Image
import openpyxl

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
BETA = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
GAMMA = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
XLSX = os.path.join(ROOT, '地块迁移_Gamma州映射_几何.xlsx')

# geometric transform (Beta full-res px -> Gamma full-res px)
AX, BX = 0.9739, -732.0
AY, BY = 0.9759, 81.4


# ---------- province centroid computation ----------
def load_definition_land(defpath):
    d = {}
    with open(defpath, encoding='utf-8') as f:
        for row in csv.reader(f, delimiter=';'):
            if len(row) < 5:
                continue
            try:
                pid = int(row[0])
            except ValueError:
                continue
            if row[4] == 'land':
                d[pid] = (int(row[1]), int(row[2]), int(row[3]))
    return d


def compute_centroids(defpath, bmppath):
    land = load_definition_land(defpath)
    rgb2pid = {}
    for pid, rgb in land.items():
        rgb2pid.setdefault(rgb, []).append(pid)
    color2pid = {rgb: pids[0] for rgb, pids in rgb2pid.items()}

    im = np.asarray(Image.open(bmppath).convert('RGB'))
    H, W, _ = im.shape
    R = im[:, :, 0].astype(np.int64)
    G = im[:, :, 1].astype(np.int64)
    B = im[:, :, 2].astype(np.int64)
    key = (R << 16) | (G << 8) | B
    flat = key.ravel()

    lk = np.array(sorted(color2pid.keys()), dtype=np.int64)
    # encode sorted rgb keys to int64
    lk_enc = (np.array([c[0] for c in sorted(color2pid.keys())], dtype=np.int64) << 16) \
             | (np.array([c[1] for c in sorted(color2pid.keys())], dtype=np.int64) << 8) \
             | np.array([c[2] for c in sorted(color2pid.keys())], dtype=np.int64)
    lp = np.array([color2pid[c] for c in sorted(color2pid.keys())], dtype=np.int64)

    idx = np.searchsorted(lk_enc, flat)
    idx_clip = np.clip(idx, 0, len(lk_enc) - 1)
    valid = lk_enc[idx_clip] == flat
    pid_flat = np.where(valid, lp[idx_clip], -1)

    xx = np.broadcast_to(np.arange(W, dtype=np.int64)[None, :], (H, W)).ravel()
    yy = np.broadcast_to(np.arange(H, dtype=np.int64)[:, None], (H, W)).ravel()

    mask = pid_flat >= 0
    vp = pid_flat[mask]
    maxpid = int(max(land.keys()))
    sx = np.bincount(vp, weights=xx[mask], minlength=maxpid + 1)
    sy = np.bincount(vp, weights=yy[mask], minlength=maxpid + 1)
    cnt = np.bincount(vp, minlength=maxpid + 1)

    centroids = {}
    for pid in land:
        if cnt[pid] > 0:
            centroids[pid] = (sx[pid] / cnt[pid], sy[pid] / cnt[pid])
    return centroids


# ---------- block extraction ----------
def find_block_end(text, open_idx):
    depth = 0
    i = open_idx
    while i < len(text):
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def extract_block(text, key):
    m = re.search(key + r'\s*=\s*\{', text)
    if not m:
        return None
    o = text.index('{', m.start())
    e = find_block_end(text, o)
    if e is None:
        return None
    return text[o + 1:e]


# ---------- Beta state parsing ----------
def parse_beta(text):
    info = {}
    m = re.search(r'name\s*=\s*"([^"]*)"', text)
    info['name'] = m.group(1) if m else ''
    m = re.search(r'\bid\s*=\s*(\d+)', text)
    info['id'] = m.group(1) if m else ''
    m = re.search(r'state_category\s*=\s*([A-Za-z_]+)', text)
    info['state_category'] = m.group(1) if m else ''
    m = re.search(r'local_supplies\s*=\s*([\d.]+)', text)
    info['local_supplies'] = m.group(1) if m else ''
    m = re.search(r'buildings_max_level_factor\s*=\s*([\d.]+)', text)
    info['bmlf'] = m.group(1) if m else ''
    m = re.search(r'manpower\s*=\s*(\d+)', text)
    info['manpower'] = m.group(1) if m else ''
    info['resources'] = extract_block(text, 'resources')
    info['buildings'] = extract_block(text, 'buildings')
    return info


# ---------- Gamma state parsing ----------
def parse_gamma(text):
    info = {}
    m = re.search(r'\bid\s*=\s*(\d+)', text)
    info['id'] = m.group(1) if m else ''
    m = re.search(r'owner\s*=\s*([A-Za-z_]+)', text)
    info['owner'] = m.group(1) if m else ''
    info['cores'] = re.findall(r'add_core_of\s*=\s*([A-Za-z_]+)', text)
    info['vps'] = re.findall(r'victory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}', text)
    prov_inner = extract_block(text, 'provinces')
    info['provinces'] = re.findall(r'\d+', prov_inner) if prov_inner is not None else []
    m = re.search(r'manpower\s*=\s*(\d+)', text)
    info['manpower'] = m.group(1) if m else ''
    return info


# ---------- remap province-specific building entries ----------
def remap_buildings(inner, b2g, unmapped):
    if not inner:
        return ''
    def repl(m):
        bpid = int(m.group(1))
        gpid = b2g.get(bpid)
        if gpid is None:
            unmapped.append(bpid)
            return m.group(0)
        return '%d = {' % gpid
    return re.sub(r'(\d+)\s*=\s*\{', repl, inner)


TOKEN_RE = re.compile(r'\{|\}|=|"(?:[^"\\]|\\.)*"|\d+(?:\.\d+)?|[A-Za-z_][A-Za-z_0-9]*')


def normalize_entries(inner):
    """Split a HOI4 block body into top-level entries, one per line,
    spacing '=' and keeping nested blocks inline."""
    tokens = TOKEN_RE.findall(inner)
    entries = []
    i = 0
    n = len(tokens)
    while i < n:
        t = tokens[i]
        if t in ('{', '}', '='):
            i += 1
            continue
        key = t
        i += 1
        parts = [key]
        if i < n and tokens[i] == '=':
            parts.append('=')
            i += 1
            if i < n and tokens[i] == '{':
                parts.append('{')
                i += 1
                depth = 1
                body = []
                while i < n and depth > 0:
                    tt = tokens[i]
                    if tt == '{':
                        depth += 1
                    elif tt == '}':
                        depth -= 1
                        if depth == 0:
                            i += 1
                            break
                    body.append(tt)
                    i += 1
                parts.append(' '.join(body))
                parts.append('}')
            elif i < n:
                parts.append(tokens[i])
                i += 1
        entries.append(' '.join(parts))
    return entries


# ---------- output builder ----------
def build_output(g, b, b2g, unmapped):
    L = []
    L.append('state = {')
    L.append('\tid = %s' % g['id'])
    L.append('\tname = "%s"' % b['name'])
    L.append('\tmanpower = %s' % b.get('manpower', g.get('manpower', '100000')))
    L.append('\tstate_category = %s' % b.get('state_category', 'pastoral'))
    L.append('')
    res_entries = normalize_entries(b.get('resources') or '')
    L.append('\tresources = {')
    for e in res_entries:
        L.append('\t\t' + e)
    L.append('\t}')
    L.append('')
    L.append('\thistory = {')
    L.append('\t\towner = %s' % g['owner'])
    for c in g['cores']:
        L.append('\t\tadd_core_of = %s' % c)
    bld = remap_buildings(b.get('buildings') or '', b2g, unmapped)
    bld_entries = normalize_entries(bld)
    L.append('\t\tbuildings = {')
    for e in bld_entries:
        L.append('\t\t\t' + e)
    L.append('\t\t}')
    for vp in g['vps']:
        L.append('\t\tvictory_points = { %s %s }' % (vp[0], vp[1]))
    L.append('\t}')
    L.append('')
    L.append('\tprovinces = {')
    L.append('\t\t' + ' '.join(g['provinces']))
    L.append('\t}')
    if b.get('bmlf'):
        L.append('\tbuildings_max_level_factor = %s' % b['bmlf'])
    if b.get('local_supplies'):
        L.append('\tlocal_supplies = %s' % b['local_supplies'])
    L.append('}')
    return '\n'.join(L) + '\n'


def main():
    print('loading mapping xlsx...')
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    ws = wb['Gamma州映射']
    rows = list(ws.iter_rows(values_only=True))
    hdr = rows[0]
    gamma_to_beta = {}
    for r in rows[1:]:
        gamma_to_beta[int(r[0])] = int(r[3])
    print('  gamma->beta mapping:', len(gamma_to_beta))

    print('computing Beta province centroids...')
    beta_cent = compute_centroids(
        os.path.join(BETA, 'map', 'definition.csv'),
        os.path.join(BETA, 'map', 'provinces.bmp'))
    print('  beta centroids:', len(beta_cent))

    print('computing Gamma province centroids...')
    gamma_cent = compute_centroids(
        os.path.join(GAMMA, 'map', 'definition.csv'),
        os.path.join(GAMMA, 'map', 'provinces.bmp'))
    print('  gamma centroids:', len(gamma_cent))

    # build beta -> gamma province nearest mapping (for building remap)
    print('building beta->gamma province mapping...')
    g_ids = list(gamma_cent.keys())
    g_arr = np.array([gamma_cent[i] for i in g_ids], dtype=np.float64)
    b2g = {}
    for bid, (bx, by) in beta_cent.items():
        gx = AX * bx + BX
        gy = AY * by + BY
        d2 = (g_arr[:, 0] - gx) ** 2 + (g_arr[:, 1] - gy) ** 2
        j = int(np.argmin(d2))
        b2g[bid] = g_ids[j]
    print('  province mapping built:', len(b2g))

    # parse beta state files
    print('parsing Beta state files...')
    beta_dir = os.path.join(BETA, 'history', 'states')
    beta_states = {}
    for fn in os.listdir(beta_dir):
        if not fn.endswith('.txt'):
            continue
        with open(os.path.join(beta_dir, fn), encoding='utf-8') as f:
            t = f.read()
        info = parse_beta(t)
        if info['id']:
            beta_states[int(info['id'])] = info
    print('  beta states parsed:', len(beta_states))

    # process gamma files
    print('processing Gamma state files...')
    gamma_dir = os.path.join(GAMMA, 'history', 'states')
    stats = Counter()
    missing_beta = []
    unmapped = []
    for fn in os.listdir(gamma_dir):
        if not fn.endswith('.txt'):
            continue
        p = os.path.join(gamma_dir, fn)
        with open(p, encoding='utf-8') as f:
            t = f.read()
        g = parse_gamma(t)
        gid = int(g['id']) if g['id'] else None
        if gid is None:
            stats['no_id'] += 1
            continue
        bid = gamma_to_beta.get(gid)
        if bid is None or bid not in beta_states:
            missing_beta.append(gid)
            stats['missing_beta'] += 1
            continue
        b = beta_states[bid]
        out = build_output(g, b, b2g, unmapped)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(out)
        stats['written'] += 1

    print('  written:', stats['written'])
    print('  missing_beta:', stats['missing_beta'], missing_beta[:20])
    print('  no_id:', stats['no_id'])
    print('  unmapped building provinces:', len(unmapped), Counter(unmapped).most_common(20))


if __name__ == '__main__':
    main()
