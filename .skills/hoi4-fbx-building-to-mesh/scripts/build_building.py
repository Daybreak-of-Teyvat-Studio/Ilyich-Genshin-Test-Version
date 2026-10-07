# -*- coding: utf-8 -*-
"""Convert a static FBX building -> HOI4 building .mesh (no skeleton).

Pipeline
  1. drop the bottom foundation block (see BASE_CUT notes below)
  2. weld duplicate vertices (FBX splits vertices per polygon corner)
  3. drop degenerate triangles
  4. vertex-clustering decimation until the triangle budget fits
  5. drop vertices no triangle references (no zero-normal leftovers)
  6. scale to the target building footprint, base flat on z=0
  7. recompute smooth normals, triplanar UVs, Gram-Schmidt tangents, AABB
  8. write the .mesh with the same attribute set a vanilla building uses

Usage
  python build_building.py --geo <dir with Vertices.npy + tris.npy> \\
      --out <output.mesh> [--base-cut 2.0] [--target-tris 20000] \\
      [--size 0.7295,1.1980,1.0109] [--shader PdxMeshAdvancedSnow] \\
      [--diff factory_d.dds] [--normal factory_n.dds] [--spec factory_s.dds]

Step 0 (once per FBX) is scripts/fbx_arrays.py + triangulating PolygonVertexIndex
into tris.npy -- see SKILL.md.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdxml  # noqa: E402

GEO = '_tc/geo'

# The foundation is a *block* of stacked Z layers, not one plane.  Read the Z
# histogram first (see SKILL.md "finding the foundation") and set this to the
# top of the block -- everything with max-Z <= BASE_CUT goes.
BASE_CUT = 2.0
TARGET_TRIS = 20000      # decimation budget
CLUSTER_GRID = 96        # clustering resolution (per axis, over the bbox)

# vanilla factory.mesh footprint (x, y, z-extent) with base at z=0
TARGET_SIZE = np.array([0.7295, 1.1980, 1.0109])


# ----------------------------------------------------------------- load
def load_raw(geo):
    v = np.load(os.path.join(geo, 'Vertices.npy')).reshape(-1, 3).astype(np.float64)
    t = np.load(os.path.join(geo, 'tris.npy')).astype(np.int64)
    return v, t


def drop_foundation(v, t, base_cut=None):
    """Remove the bottom foundation block.

    The slab spans Z 0..N as N+1 stacked layers (Z=0 bottom face, Z=1..N-1
    intermediate, Z=N top face) with vertical skirt walls joining them.
    Cutting only Z==0 leaves the skirt behind, so drop the whole block:
    every triangle whose max Z is at or below the block top goes.
    """
    if base_cut is None:
        base_cut = BASE_CUT
    keep = ~(v[t, 2].max(axis=1) <= base_cut)
    return v, t[keep]


def weld(v, t, decimals=4):
    """Merge vertices that share a position; returns (new_v, new_t)."""
    q = np.round(v, decimals)
    _, first, inverse = np.unique(q, axis=0, return_index=True,
                                  return_inverse=True)
    nv = v[first]
    nt = inverse[t]
    return nv, nt


def drop_degenerate(v, t, eps=1e-9):
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) * 0.5
    ok = area > eps
    ifok = (t[:, 0] != t[:, 1]) & (t[:, 1] != t[:, 2]) & (t[:, 0] != t[:, 2])
    return t[ok & ifok]


def cluster_simplify(v, t, grid):
    """Vertex-clustering decimation: snap vertices to a uniform grid and
    average the points that land in the same cell.

    The grid is built on a CUBE that bounds the model, so a non-cubic
    footprint (e.g. 69 x 73 x 46) does not get squashed on one axis.
    """
    mn = v.min(axis=0)
    ext = v.max(axis=0) - mn
    side = ext.max()
    if side <= 0:
        return v, t
    cell = side / grid
    key = np.floor((v - mn) / cell).astype(np.int64)
    dims = key.max(axis=0) + 1
    flat = (key[:, 0] * dims[1] + key[:, 1]) * dims[2] + key[:, 2]

    uniq, inverse = np.unique(flat, return_inverse=True)
    nv = np.zeros((len(uniq), 3))
    cnt = np.zeros(len(uniq))
    np.add.at(nv, inverse, v)
    np.add.at(cnt, inverse, 1)
    nv /= cnt[:, None]

    nt = drop_degenerate(nv, inverse[t], eps=1e-12)
    return nv, nt


def simplify_to_budget(v, t, budget):
    """Binary-search the clustering grid for the largest mesh that still
    fits the triangle budget (i.e. the finest resolution that fits)."""
    lo, hi = 4, 512
    best = (cluster_simplify(v, t, lo)[0], cluster_simplify(v, t, lo)[1], lo)
    while lo <= hi:
        mid = (lo + hi) // 2
        nv, nt = cluster_simplify(v, t, mid)
        if len(nt) <= budget:
            best = (nv, nt, mid)
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def compute_normals(v, t):
    """Area-weighted smooth vertex normals, with a face-normal fallback for
    any vertex whose accumulated normal cancels out to zero."""
    n = np.zeros_like(v)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    fn = np.cross(b - a, c - a)          # length == 2 * area
    for k in range(3):
        np.add.at(n, t[:, k], fn)
    ln = np.linalg.norm(n, axis=1)

    bad = ln < 1e-12
    if bad.any():
        # average the face normals of the faces touching each bad vertex
        acc = np.zeros((len(v), 3))
        cnt = np.zeros(len(v))
        fnn = fn / np.maximum(np.linalg.norm(fn, axis=1)[:, None], 1e-20)
        for k in range(3):
            np.add.at(acc, t[:, k], fnn)
            np.add.at(cnt, t[:, k], 1.0)
        fallback = acc / np.maximum(cnt[:, None], 1.0)
        fb = np.linalg.norm(fallback, axis=1) < 1e-12
        fallback[fb] = np.array([0.0, 0.0, 1.0])
        n[bad] = fallback[bad]
        ln = np.linalg.norm(n, axis=1)

    ln[ln == 0] = 1.0
    return n / ln[:, None]


def triplanar_uv(v, n):
    """Cheap deterministic UVs: pick each VERTEX's dominant normal axis and
    project onto the matching coordinate plane."""
    axis = np.argmax(np.abs(n), axis=1)
    uv = np.zeros((len(v), 2))
    uv[axis == 0] = v[axis == 0][:, [1, 2]]
    uv[axis == 1] = v[axis == 1][:, [0, 2]]
    uv[axis == 2] = v[axis == 2][:, [0, 1]]
    mn = v.min(axis=0)[:2]
    mx = v.max(axis=0)[:2]
    ext = np.where(mx - mn == 0, 1.0, mx - mn)
    return (uv - mn) / ext


def tangents(v, t, uv, n):
    """Per-vertex 4-float tangents (HOI4 expects vec4 per vertex).

    Accumulate the xyz direction per vertex only; the w (handedness) slot must
    stay +-1 like the vanilla assets -- never accumulate it.
    Vertices whose accumulated direction cancels to zero get an arbitrary unit
    vector orthogonal to their normal, so no zero rows are emitted.
    """
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    e1 = b - a
    e2 = c - a
    du1 = uv[t[:, 1], 0] - uv[t[:, 0], 0]
    dv1 = uv[t[:, 1], 1] - uv[t[:, 0], 1]
    du2 = uv[t[:, 2], 0] - uv[t[:, 0], 0]
    dv2 = uv[t[:, 2], 1] - uv[t[:, 0], 1]
    det = du1 * dv2 - du2 * dv1

    # degenerate UV triangles: fall back to the geometric edge direction
    bad = np.abs(det) < 1e-12
    if bad.any():
        e1n = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-12)
        det = det.copy()
        det[bad] = 1.0
        T = np.where(bad[:, None], e1n,
                     (e1 * dv2[:, None] - e2 * dv1[:, None]))
        T = T / np.maximum(det, 1e-12)[:, None]
    else:
        T = (e1 * dv2[:, None] - e2 * dv1[:, None]) / det[:, None]

    ln = np.linalg.norm(T, axis=1)
    T = T / np.where(ln == 0, 1.0, ln)[:, None]

    acc = np.zeros((len(v), 3))
    for k in range(3):
        np.add.at(acc, t[:, k], T)
    al = np.linalg.norm(acc, axis=1)

    # fallback for cancelling vertices: any unit vector perpendicular to normal
    if (al < 1e-8).any():
        ref = np.tile(np.array([0.0, 0.0, 1.0]), (len(v), 1))
        swap = np.abs(n[:, 2:3]) > 0.9
        ref[swap[:, 0]] = np.array([1.0, 0.0, 0.0])
        alt = np.cross(n, ref)
        alt /= np.maximum(np.linalg.norm(alt, axis=1, keepdims=True), 1e-12)
        acc[al < 1e-8] = alt[al < 1e-8]
        al = np.linalg.norm(acc, axis=1)

    acc /= al[:, None]
    # Gram-Schmidt against the normal so tangent stays orthogonal
    acc -= n * np.sum(acc * n, axis=1)[:, None]
    acc /= np.maximum(np.linalg.norm(acc, axis=1), 1e-12)[:, None]

    out = np.zeros((len(v), 4))
    out[:, :3] = acc
    out[:, 3] = 1.0
    return out


# ----------------------------------------------------------------- write
def build_xml(v, t, n, uv, tan, shader, diff, nrm_tex, spec):
    mn = v.min(axis=0)
    mx = v.max(axis=0)

    root = Xml.Element('File')
    root.set('pdxasset', 'PdxMesh')
    obj = Xml.SubElement(root, 'object')
    obj.set('name', 'temple')
    shp = Xml.SubElement(obj, 'shape')
    shp.set('name', 'temple')
    shp.set('lod', 'all')

    def fmt(a):
        return ' '.join('%.6f' % x for x in np.asarray(a).ravel())

    # NOTE: write_meshfile reads these as XML *attributes* of <mesh>,
    # not as child elements.
    mesh = Xml.SubElement(shp, 'mesh')
    mesh.set('p', fmt(v))
    mesh.set('n', fmt(n))
    mesh.set('ta', fmt(tan))
    mesh.set('u0', fmt(uv))
    mesh.set('tri', ' '.join(str(int(x)) for x in t.ravel()))
    mesh.set('boundingsphere', fmt((mn + mx) / 2.0))

    aabb = Xml.SubElement(mesh, 'aabb')
    aabb.set('min', fmt(mn))
    aabb.set('max', fmt(mx))

    mat = Xml.SubElement(mesh, 'material')
    mat.set('shader', shader)
    mat.set('diff', diff)
    mat.set('n', nrm_tex)
    mat.set('spec', spec)
    return root


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--geo', required=True, help='dir with Vertices.npy + tris.npy')
    ap.add_argument('--out', required=True, help='output .mesh path')
    ap.add_argument('--base-cut', type=float, default=BASE_CUT,
                    help='drop triangles whose max Z <= this (top of the foundation block)')
    ap.add_argument('--target-tris', type=int, default=TARGET_TRIS)
    ap.add_argument('--size', default=','.join(str(x) for x in TARGET_SIZE),
                    help='target footprint x,y,z')
    ap.add_argument('--shader', default='PdxMeshAdvancedSnow')
    ap.add_argument('--diff', default='factory_d.dds')
    ap.add_argument('--normal', default='factory_n.dds')
    ap.add_argument('--spec', default='factory_s.dds')
    ap.add_argument('--locator', action='append', default=None,
                    help='locator name to emit at the model top (repeatable)')
    args = ap.parse_args()

    target_size = np.array([float(x) for x in args.size.split(',')])

    v, t = load_raw(args.geo)
    print('loaded: %d verts %d tris' % (len(v), len(t)))

    v, t = drop_foundation(v, t, args.base_cut)
    print('after dropping Z<=%.2f slab: %d verts %d tris'
          % (args.base_cut, len(v), len(t)))

    v, t = weld(v, t)
    print('after weld: %d verts %d tris' % (len(v), len(t)))

    if len(t) > args.target_tris:
        v, t, grid = simplify_to_budget(v, t, args.target_tris)
        print('after clustering grid=%d: %d verts %d tris'
              % (grid, len(v), len(t)))

    print('\nfinal: %d verts %d tris' % (len(v), len(t)))
    print('bbox min = %s' % np.array2string(v.min(axis=0), precision=4))
    print('bbox max = %s' % np.array2string(v.max(axis=0), precision=4))

    # Drop vertices no triangle references (leftovers from clustering) so we
    # never ship degenerate zero-normal vertices.
    n_before = len(v)
    used = np.unique(t)
    remap = np.full(n_before, -1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    t = remap[t]
    v = v[used]
    print('dropped %d unreferenced vertices -> %d remain'
          % (n_before - len(v), len(v)))

    ext = v.max(axis=0) - v.min(axis=0)
    ext[ext == 0] = 1.0
    k = target_size / ext
    scale = float(k.max())
    v = (v - v.min(axis=0)) * scale     # lowest point -> 0
    ext = v.max(axis=0) - v.min(axis=0)

    # keep the model centred on its own footprint like the original
    off = (target_size - ext) / 2.0
    off[2] = 0.0                      # sit flat on the ground plane (z=0)
    v = v + off
    print('scaled by %.5f -> footprint %s (base at z=0)'
          % (scale, np.array2string(ext, precision=4)))

    n = compute_normals(v, t)
    uv = triplanar_uv(v, n)
    tan = tangents(v, t, uv, n)

    # Smoke locators at the top of the tallest tower, mirroring the vanilla
    # factorysmoke / factorysmoke2 (which sit at the top of the smokestack).
    # Vanilla quaternion is (0,0,0,-1); keep that so the emitter orientation
    # matches what the building effect expects.
    names = args.locator if args.locator else ['factorysmoke', 'factorysmoke2']
    top = v[int(np.argmax(v[:, 2]))]
    zq = [0.0, 0.0, 0.0, -1.0]
    locs = [(nm, [top[0], top[1], top[2]], zq) for nm in names]

    out = args.out
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    size = pdxml.write_mesh(out, v.ravel().tolist(), n.ravel().tolist(),
                            tan.ravel().tolist(), uv.ravel().tolist(),
                            t.ravel().tolist(),
                            args.shader, args.diff, args.normal, args.spec,
                            locators=locs)
    print('wrote %s' % out)
    print('size = %d bytes (%.3f MB)  limit 5 MB -> %s'
          % (size, size / 1048576.0, 'OK' if size <= 5 * 1048576 else 'TOO BIG'))


if __name__ == '__main__':
    main()