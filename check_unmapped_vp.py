# -*- coding: utf-8 -*-
import os, re, csv
import numpy as np
from PIL import Image

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
BETA = os.path.join(ROOT, 'Daybreak of Teyvat Beta Version')
GAMMA = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
AX, BX = 0.9739, -732.0
AY, BY = 0.9759, 81.4


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
    R = im[:, :, 0].astype(np.int64); G = im[:, :, 1].astype(np.int64); B = im[:, :, 2].astype(np.int64)
    key = (R << 16) | (G << 8) | B
    flat = key.ravel()
    sk = sorted(color2pid.keys())
    lk_enc = (np.array([c[0] for c in sk], dtype=np.int64) << 16) | (np.array([c[1] for c in sk], dtype=np.int64) << 8) | np.array([c[2] for c in sk], dtype=np.int64)
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
    centroids = {pid: (sx[pid] / cnt[pid], sy[pid] / cnt[pid]) for pid in land if cnt[pid] > 0}
    return centroids, land


# collect beta VP provinces from localization + state files
beta_vp = set()
for fn in os.listdir(os.path.join(BETA, 'history', 'states')):
    if not fn.endswith('.txt'):
        continue
    tt = open(os.path.join(BETA, 'history', 'states', fn), encoding='utf-8').read()
    beta_vp |= set(int(x) for x in re.findall(r'victory_points = \{ (\d+)', tt))
for lang in ['english', 'simp_chinese']:
    lp = os.path.join(BETA, 'localisation', lang)
    for f in os.listdir(lp):
        if 'victory' in f.lower() or 'Victory' in f:
            tt = open(os.path.join(lp, f), encoding='utf-8').read()
            beta_vp |= set(int(x) for x in re.findall(r'VICTORY_POINTS_(\d+)', tt))

beta_land = load_definition_land(os.path.join(BETA, 'map', 'definition.csv'))
print('beta VP provinces:', len(beta_vp))
unmapped = [p for p in sorted(beta_vp) if p not in beta_land]
print('unmapped (not in beta land definition):', unmapped)
# find their names
for lang in ['english', 'simp_chinese']:
    lp = os.path.join(BETA, 'localisation', lang)
    for f in os.listdir(lp):
        if 'victory' in f.lower() or 'Victory' in f:
            tt = open(os.path.join(lp, f), encoding='utf-8').read()
            for p in unmapped:
                for m in re.finditer(r'VICTORY_POINTS_%d:0\s*"([^"]*)"' % p, tt):
                    print('  ', p, lang, '->', m.group(1))
