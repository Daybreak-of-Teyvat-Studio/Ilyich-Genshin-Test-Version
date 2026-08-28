# -*- coding: utf-8 -*-
"""Beta -> Gamma 州迁移 v3：修复通胀/州名重复/错字，迁移 victory_points 及本地化。"""
import csv, os, re
from collections import defaultdict, Counter
import numpy as np
from PIL import Image
import openpyxl

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
BETA = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
GAMMA = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
XLSX = os.path.join(ROOT, '地块迁移_Gamma州映射_几何.xlsx')

AX, BX = 0.9739, -732.0
AY, BY = 0.9759, 81.4


def load_definition_land(defpath, land_only=False):
    d = {}
    with open(defpath, encoding='utf-8') as f:
        for row in csv.reader(f, delimiter=';'):
            if len(row) < 5:
                continue
            try:
                pid = int(row[0])
            except ValueError:
                continue
            if land_only and row[4] != 'land':
                continue
            d[pid] = (int(row[1]), int(row[2]), int(row[3]))
    return d


def compute_centroids(defpath, bmppath, land_only=False):
    land = load_definition_land(defpath, land_only=land_only)
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

    sk = sorted(color2pid.keys())
    lk_enc = (np.array([c[0] for c in sk], dtype=np.int64) << 16) \
             | (np.array([c[1] for c in sk], dtype=np.int64) << 8) \
             | np.array([c[2] for c in sk], dtype=np.int64)
    lp = np.array([color2pid[c] for c in sk], dtype=np.int64)

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
    info['manpower'] = int(m.group(1)) if m else 0
    res_inner = extract_block(text, 'resources')
    info['resources'] = {k: float(v) for k, v in re.findall(r'(\w+)\s*=\s*([\d.]+)', res_inner or '')} if res_inner else {}
    info['buildings'] = extract_block(text, 'buildings')
    info['vps'] = re.findall(r'victory_points\s*=\s*\{\s*(\d+)\s+(\d+)\s*\}', text)
    prov_inner = extract_block(text, 'provinces')
    info['provinces'] = [int(x) for x in re.findall(r'\d+', prov_inner)] if prov_inner is not None else []
    return info


def parse_gamma(text):
    info = {}
    m = re.search(r'\bid\s*=\s*(\d+)', text)
    info['id'] = m.group(1) if m else ''
    m = re.search(r'owner\s*=\s*([A-Za-z_]+)', text)
    info['owner'] = m.group(1) if m else ''
    info['cores'] = re.findall(r'add_core_of\s*=\s*([A-Za-z_]+)', text)
    prov_inner = extract_block(text, 'provinces')
    info['provinces'] = [int(x) for x in re.findall(r'\d+', prov_inner)] if prov_inner is not None else []
    return info


TOKEN_RE = re.compile(r'\{|\}|=|"(?:[^"\\]|\\.)*"|\d+(?:\.\d+)?|[A-Za-z_][A-Za-z_0-9]*')


def normalize_entries(inner):
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


def classify_buildings(inner):
    state_entries = []
    prov_entries = []
    for e in normalize_entries(inner or ''):
        m = re.match(r'^(\d+)\s*=\s*\{\s*(.*?)\s*\}$', e)
        if m:
            prov_entries.append((int(m.group(1)), m.group(2)))
        else:
            state_entries.append(e)
    return state_entries, prov_entries


def state_centroid(provinces, cent):
    xs, ys = [], []
    for p in provinces:
        if p in cent:
            xs.append(cent[p][0])
            ys.append(cent[p][1])
    if not xs:
        return None
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def load_loc_dir(dirpath):
    d = {}
    if os.path.isdir(dirpath):
        for f in os.listdir(dirpath):
            if not f.endswith('.yml'):
                continue
            for line in open(os.path.join(dirpath, f), encoding='utf-8'):
                m = re.match(r'^\s*([A-Za-z_][\w]*)\s*:\d+\s*"([^"]*)"', line)
                if m:
                    d[m.group(1)] = m.group(2)
    return d


def prettify(key):
    return key.replace('_', ' ')


def main():
    print('== load mapping ==')
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    ws = wb['Gamma州映射']
    rows = list(ws.iter_rows(values_only=True))
    gamma_to_beta = {int(r[0]): int(r[3]) for r in rows[1:]}

    print('== province centroids ==')
    beta_cent = compute_centroids(os.path.join(BETA, 'map', 'definition.csv'),
                                  os.path.join(BETA, 'map', 'provinces.bmp'),
                                  land_only=False)
    gamma_cent = compute_centroids(os.path.join(GAMMA, 'map', 'definition.csv'),
                                   os.path.join(GAMMA, 'map', 'provinces.bmp'),
                                   land_only=True)
    g_ids = list(gamma_cent.keys())
    g_arr = np.array([gamma_cent[i] for i in g_ids], dtype=np.float64)
    b2g = {}
    for bid, (bx, by) in beta_cent.items():
        gx = AX * bx + BX
        gy = AY * by + BY
        d2 = (g_arr[:, 0] - gx) ** 2 + (g_arr[:, 1] - gy) ** 2
        b2g[bid] = g_ids[int(np.argmin(d2))]

    print('== parse states ==')
    beta_dir = os.path.join(BETA, 'history', 'states')
    beta_states = {}
    for fn in os.listdir(beta_dir):
        if not fn.endswith('.txt'):
            continue
        info = parse_beta(open(os.path.join(beta_dir, fn), encoding='utf-8').read())
        if info['id']:
            beta_states[int(info['id'])] = info

    gamma_dir = os.path.join(GAMMA, 'history', 'states')
    gamma_info = {}
    gamma_prov_to_state = {}
    gamma_file = {}
    for fn in os.listdir(gamma_dir):
        if not fn.endswith('.txt'):
            continue
        g = parse_gamma(open(os.path.join(gamma_dir, fn), encoding='utf-8').read())
        if not g['id']:
            continue
        gid = int(g['id'])
        gamma_info[gid] = g
        gamma_file[gid] = fn
        for p in g['provinces']:
            gamma_prov_to_state[p] = gid

    # state centroids
    beta_sc = {bid: state_centroid(b['provinces'], beta_cent) for bid, b in beta_states.items()}
    gamma_sc = {gid: state_centroid(g['provinces'], gamma_cent) for gid, g in gamma_info.items()}
    gamma_sc_arr_ids = [gid for gid in gamma_sc if gamma_sc[gid] is not None]
    gamma_sc_arr = np.array([gamma_sc[gid] for gid in gamma_sc_arr_ids], dtype=np.float64)

    def nearest_gamma(bid):
        bc = beta_sc.get(bid)
        if bc is None:
            return None
        gx = AX * bc[0] + BX
        gy = AY * bc[1] + BY
        d2 = (gamma_sc_arr[:, 0] - gx) ** 2 + (gamma_sc_arr[:, 1] - gy) ** 2
        return gamma_sc_arr_ids[int(np.argmin(d2))]

    print('== children & orphans ==')
    children = defaultdict(list)
    for gid, bid in gamma_to_beta.items():
        children[bid].append(gid)
    orphans = [bid for bid in beta_states if bid not in children]
    print('matched beta:', len(children), 'orphans:', len(orphans))

    # assign orphans to nearest gamma
    for bid in orphans:
        ng = nearest_gamma(bid)
        if ng is not None:
            children[bid].append(ng)

    # normalization: weight = province count of child gamma
    print('== normalize manpower/resources ==')
    contributions = defaultdict(list)  # gamma_id -> [(beta_id, weight)]
    total_weight = {}
    for bid, gs in children.items():
        tw = 0
        for gid in gs:
            w = len(gamma_info[gid]['provinces'])
            contributions[gid].append((bid, w))
            tw += w
        total_weight[bid] = tw if tw > 0 else 1

    man_sum = Counter()
    res_sum = defaultdict(Counter)
    for gid, lst in contributions.items():
        for bid, w in lst:
            tw = total_weight[bid]
            b = beta_states[bid]
            man_sum[gid] += b['manpower'] * w / tw
            for r, v in b['resources'].items():
                res_sum[gid][r] += v * w / tw

    print('== generate unique names ==')
    cn_names = load_loc_dir(os.path.join(GAMMA, 'localisation', 'simp_chinese'))
    en_names = load_loc_dir(os.path.join(GAMMA, 'localisation', 'english'))
    name_counter = Counter()
    gamma_name_key = {}
    gamma_name_cn = {}
    gamma_name_en = {}
    missing_cn = set()
    for bid in sorted(beta_states):
        b = beta_states[bid]
        base = b['name']
        if base not in cn_names:
            missing_cn.add(base)
        cn = cn_names.get(base, prettify(base))
        en = en_names.get(base, prettify(base))
        # sort children by reading order (y then x)
        gs = sorted(children.get(bid, []), key=lambda gid: (gamma_sc.get(gid, (0, 0))[1], gamma_sc.get(gid, (0, 0))[0]))
        for gid in gs:
            name_counter[base] += 1
            n = name_counter[base]
            if n == 1:
                key = base
                disp_cn = cn
                disp_en = en
            else:
                key = '%s_%d' % (base, n)
                disp_cn = '%s·%d' % (cn, n)
                disp_en = '%s %d' % (en, n)
            gamma_name_key[gid] = key
            gamma_name_cn[gid] = disp_cn
            gamma_name_en[gid] = disp_en
    print('unique names assigned:', len(gamma_name_key), 'missing cn for:', len(missing_cn))

    print('== route province buildings ==')
    extra_buildings = defaultdict(list)
    for bid, b in beta_states.items():
        se, pe = classify_buildings(b['buildings'])
        b['state_entries'] = se
        b['prov_entries'] = pe
        for bpid, body in pe:
            gpid = b2g.get(bpid)
            if gpid is None:
                continue
            owner = gamma_prov_to_state.get(gpid)
            if owner is None:
                continue
            extra_buildings[owner].append('%d = { %s }' % (gpid, body))

    print('== route victory points ==')
    vp_extra = defaultdict(list)
    for bid, b in beta_states.items():
        for bpid, score in b['vps']:
            gpid = b2g.get(int(bpid))
            if gpid is None:
                continue
            owner = gamma_prov_to_state.get(gpid)
            if owner is None:
                continue
            vp_extra[owner].append((gpid, score))

    print('== write gamma state files ==')
    stats = Counter()
    for gid, g in gamma_info.items():
        bid = gamma_to_beta.get(gid)
        b = beta_states.get(bid)
        if b is None:
            stats['missing_beta'] += 1
            continue
        man = int(round(man_sum.get(gid, 0)))
        resources = {r: v for r, v in res_sum[gid].items() if v >= 0.0005}
        cat = b['state_category']
        if cat == 'pastrol':
            cat = 'pastoral'
        name = gamma_name_key.get(gid, b['name'])

        L = []
        L.append('state = {')
        L.append('\tid = %s' % gid)
        L.append('\tname = "%s"' % name)
        L.append('\tmanpower = %d' % man)
        L.append('\tstate_category = %s' % cat)
        L.append('')
        L.append('\tresources = {')
        for r in sorted(resources):
            L.append('\t\t%s = %.3f' % (r, resources[r]))
        L.append('\t}')
        L.append('')
        L.append('\thistory = {')
        L.append('\t\towner = %s' % g['owner'])
        for c in g['cores']:
            L.append('\t\tadd_core_of = %s' % c)
        L.append('\t\tbuildings = {')
        for e in b['state_entries']:
            L.append('\t\t\t' + e)
        for e in extra_buildings.get(gid, []):
            L.append('\t\t\t' + e)
        L.append('\t\t}')
        for gpid, score in sorted(vp_extra.get(gid, [])):
            L.append('\t\tvictory_points = { %d %s }' % (gpid, score))
        L.append('\t}')
        L.append('')
        L.append('\tprovinces = {')
        L.append('\t\t' + ' '.join(str(x) for x in g['provinces']))
        L.append('\t}')
        if b.get('bmlf'):
            L.append('\tbuildings_max_level_factor = %s' % b['bmlf'])
        if b.get('local_supplies'):
            L.append('\tlocal_supplies = %s' % b['local_supplies'])
        L.append('}')
        out = '\n'.join(L) + '\n'
        with open(os.path.join(gamma_dir, gamma_file[gid]), 'w', encoding='utf-8') as f:
            f.write(out)
        stats['written'] += 1
    print('written:', stats['written'], 'missing_beta:', stats['missing_beta'])

    print('== write state-name localization ==')
    # write suffixed keys only (base keys already in DOT_state_names files)
    cn_suffix = []
    en_suffix = []
    for gid, key in gamma_name_key.items():
        base = beta_states[gamma_to_beta[gid]]['name']
        if key == base:
            continue
        cn = gamma_name_cn[gid]
        en = gamma_name_en[gid]
        cn_suffix.append(' %s:0 "%s"' % (key, cn))
        en_suffix.append(' %s:0 "%s"' % (key, en))
    if cn_suffix:
        with open(os.path.join(GAMMA, 'localisation', 'simp_chinese', 'DOT_Gamma_state_names_l_simp_chinese.yml'), 'w', encoding='utf-8') as f:
            f.write('l_simp_chinese:\n' + '\n'.join(cn_suffix) + '\n')
    if en_suffix:
        with open(os.path.join(GAMMA, 'localisation', 'english', 'DOT_Gamma_state_names_l_english.yml'), 'w', encoding='utf-8') as f:
            f.write('l_english:\n' + '\n'.join(en_suffix) + '\n')
    print('suffixed name keys: cn=%d en=%d' % (len(cn_suffix), len(en_suffix)))

    print('== remap victory-point localization ==')
    vp_files = ['english/victory_points_l_english.yml',
                'simp_chinese/DOT_Victory_Points_l_simp_chinese.yml',
                'simp_chinese/SGS_victory_points_l_simp_chinese.yml',
                'simp_chinese/victory_points_l_simp_chinese.yml']
    vp_remapped = 0
    vp_unmapped = 0
    for rel in vp_files:
        src = os.path.join(BETA, 'localisation', rel)
        if not os.path.exists(src):
            continue
        txt = open(src, encoding='utf-8').read()
        bpids = [int(x) for x in re.findall(r'VICTORY_POINTS_(\d+)', txt)]

        def repl(m):
            bpid = int(m.group(1))
            gpid = b2g.get(bpid)
            return 'VICTORY_POINTS_%d' % gpid if gpid is not None else m.group(0)

        txt = re.sub(r'VICTORY_POINTS_(\d+)', repl, txt)
        unmapped = sum(1 for b in bpids if b not in b2g)
        dst = os.path.join(GAMMA, 'localisation', rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(txt)
        vp_remapped += len(bpids) - unmapped
        vp_unmapped += unmapped
    print('vp keys remapped:', vp_remapped, 'unmapped:', vp_unmapped)


if __name__ == '__main__':
    main()
