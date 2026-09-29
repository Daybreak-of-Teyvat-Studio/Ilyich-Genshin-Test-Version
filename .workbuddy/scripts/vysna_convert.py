# -*- coding: utf-8 -*-
"""薇斯纳 PMX -> HOI4 .mesh 转换器（纯 Python）。

管线：
  1. 解析 PMX（顶点/法线/UV/面/材质/骨骼/权重）
  2. 按材质筛选：排除结晶、头饰等装饰件（保留本体 + 翅膀）
  3. Umeyama 求 MMD 骨架 -> HOI4 标准骨架 的相似变换（s, R, t）
  4. 顶点坐标变换到 HOI4 骨架空间
  5. 把 MMD 权重迁移到 HOI4 的 33 根标准骨骼（多对一累加，取 top4 归一化）
  6. 按贴图分组材质
  7. 用 pdx_data.write_meshfile 输出 .mesh

不依赖 Blender。
"""
import os
import struct
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdx_data import write_meshfile  # noqa
from pmx_parse import PMX  # noqa

import xml.etree.ElementTree as Xml  # noqa

ROOT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version"
WORK = os.path.join(ROOT, ".workbuddy", "vysna_work", "薇斯纳")
OUTDIR = os.path.join(ROOT, ".workbuddy", "vysna_out")

# ---------------------------------------------------------------- HOI4 标准骨架
# (名字, 父索引)，位置见 HOI4_REST
HOI4_RIG = [
    ("Root", -1),
    ("Hip", 0),
    ("LeftUpLeg", 1),
    ("LeftLeg", 2),
    ("LeftFoot", 3),
    ("LeftToeBase", 4),
    ("back_mid", 1),
    ("LeftShoulder", 6),
    ("LeftArm", 7),
    ("LeftForeArm", 8),
    ("LeftForeArmRoll", 9),
    ("LeftHand", 10),
    ("Left_Hand_node", 11),
    ("Left_Hand_node_2", 11),
    ("Left_Hand_node_3", 11),
    ("Left_Hand_node_4", 11),
    ("head", 6),
    ("RightShoulder", 6),
    ("RightArm", 17),
    ("RightForeArm", 18),
    ("RightForeArmRoll", 19),
    ("RightHand", 20),
    ("Right_Hand_node", 21),
    ("Right_Hand_node_2", 21),
    ("Right_Hand_node_3", 21),
    ("Right_Hand_node_4", 21),
    ("mid_back_node", 6),
    ("RightUpLeg", 1),
    ("RightLeg", 27),
    ("RightFoot", 28),
    ("RightToeBase", 29),
    ("Root_node_1", 0),
    ("Root_node_2", 0),
]

HOI4_REST = {
    "Root": (0.0, 0.0, 0.0),
    "Hip": (0.0, 3.9842, 0.0874),
    "LeftUpLeg": (0.4364, 3.4557, 0.0881),
    "LeftLeg": (0.6674, 2.0382, 0.1234),
    "LeftFoot": (0.8813, 0.4592, 0.4211),
    "LeftToeBase": (1.1356, 0.0571, 0.0075),
    "back_mid": (0.0, 4.5314, 0.0675),
    "LeftShoulder": (0.3192, 5.8114, 0.0327),
    "LeftArm": (0.7141, 5.8690, 0.1240),
    "LeftForeArm": (1.6297, 5.1430, 0.1928),
    "LeftForeArmRoll": (2.0082, 4.8882, 0.0460),
    "LeftHand": (2.3635, 4.6490, -0.0918),
    "Left_Hand_node": (2.5845, 4.2989, -0.3321),
    "Left_Hand_node_2": (2.5845, 4.2989, -0.3931),
    "Left_Hand_node_3": (2.5845, 4.2989, -0.3322),
    "Left_Hand_node_4": (2.5845, 4.2989, -0.5512),
    "head": (0.0, 6.5045, 0.0337),
    "RightShoulder": (-0.3192, 5.8114, 0.0327),
    "RightArm": (-0.7141, 5.8690, 0.1240),
    "RightForeArm": (-1.6297, 5.1430, 0.1928),
    "RightForeArmRoll": (-2.0081, 4.8882, 0.0460),
    "RightHand": (-2.3635, 4.6490, -0.0918),
    "Right_Hand_node": (-2.5845, 4.2989, -0.3321),
    "Right_Hand_node_2": (-2.5845, 4.2989, -0.4073),
    "Right_Hand_node_3": (-2.5845, 4.2989, -0.4858),
    "Right_Hand_node_4": (-2.5845, 4.2989, -0.5828),
    "mid_back_node": (0.0, 4.5799, 0.9770),
    "RightUpLeg": (-0.4364, 3.4557, 0.0881),
    "RightLeg": (-0.6674, 2.0382, 0.1234),
    "RightFoot": (-0.8813, 0.4592, 0.4211),
    "RightToeBase": (-1.1356, 0.0571, 0.0075),
    "Root_node_1": (0.0, 0.0, 0.0),
    "Root_node_2": (0.0, 0.0, 0.0),
}
HOI4_ORDER = [n for n, _ in HOI4_RIG]
HOI4_INDEX = {n: i for i, n in enumerate(HOI4_ORDER)}

# MMD 骨骼名 -> HOI4 骨骼名（用于 Umeyama 拟合与权重迁移的锚点）
ANCHORS = {
    "全ての親": "Root",
    "センター": "Hip",
    "左足": "LeftUpLeg",
    "左ひざ": "LeftLeg",
    "左足首": "LeftFoot",
    "左つま先": "LeftToeBase",
    "右足": "RightUpLeg",
    "右ひざ": "RightLeg",
    "右足首": "RightFoot",
    "右つま先": "RightToeBase",
    "左肩": "LeftShoulder",
    "左腕": "LeftArm",
    "左ひじ": "LeftForeArm",
    "左手首": "LeftHand",
    "右肩": "RightShoulder",
    "右腕": "RightArm",
    "右ひじ": "RightForeArm",
    "右手首": "RightHand",
    "頭": "head",
    "上半身": "back_mid",
}

# 排除的材质（装饰件）
EXCLUDE_KEYS = ["结晶", "头饰"]

# 材质 -> 贴图分组名（决定 draw call / 最终材质数）
def tex_group(tex_path):
    """把贴图路径归到一个组名。"""
    base = os.path.basename(tex_path).lower()
    stem = os.path.splitext(base)[0]
    mapping = {
        "颜": "face", "表情1": "face", "表情": "face", "目": "face", "目2": "face",
        "瞳": "face", "目光": "face", "照れ": "face",
        "髮": "hair", "hair": "hair", "sp": "hair",
        "体": "body", "体s": "body", "肌": "body", "skin": "body",
        "裙": "skirt", "裙s": "skirt",
        "袜s": "sock", "袜": "sock",
        "翼s": "wing", "翼": "wing",
    }
    return mapping.get(stem, "misc")


def umeyama(src, dst):
    """求 dst ≈ s*R@src + t 的最小二乘相似变换。返回 (s, R, t)。"""
    src = np.asarray(src, dtype=np.float64)
    dst = np.asarray(dst, dtype=np.float64)
    n = len(src)
    mu_s = src.mean(0)
    mu_d = dst.mean(0)
    sc = src - mu_s
    dc = dst - mu_d
    cov = dc.T @ sc / n
    U, D, Vt = np.linalg.svd(cov)
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    var_s = (sc ** 2).sum() / n
    s = (D * np.diag(S)).sum() / var_s
    t = mu_d - s * R @ mu_s
    return s, R, t


def bone_map_table(pmx, s, R, t):
    """构造 MMD 骨骼索引 -> HOI4 骨骼索引 的映射。"""
    # 先按名字锚点
    out = {}
    bname = [b["name"] for b in pmx.bones]
    bidx = {nm: i for i, nm in enumerate(bname)}
    for mmd_nm, h4_nm in ANCHORS.items():
        if mmd_nm in bidx:
            out[bidx[mmd_nm]] = HOI4_INDEX[h4_nm]

    # 位置法兜底：把 MMD 骨骼位置变换到 HOI4 空间，找最近的 HOI4 骨骼
    h4_pos = np.array([HOI4_REST[n] for n in HOI4_ORDER])
    mmd_pos = np.array([b["pos"] for b in pmx.bones])
    mmd_in_h4 = (s * (R @ mmd_pos.T).T) + t
    d = np.linalg.norm(mmd_in_h4[:, None, :] - h4_pos[None, :, :], axis=2)

    # 名字规则优先（比位置更语义化）
    def by_name(nm):
        L = nm.startswith("左")
        Rr = nm.startswith("右")
        if "翼" in nm:
            return "mid_back_node"
        if any(k in nm for k in ("目", "眉", "髪", "口", "齿", "鼻", "耳", "顔", "颜", "瞳", "睫", "頭", "首", "照")):
            return "head"
        if any(k in nm for k in ("上半身", "胸", "肩P", "肩C")):
            return "back_mid"
        if any(k in nm for k in ("腰", "下半身", "グルーブ", "センター", "全ての親", "操作中心", "スカート", "裙")):
            return "Hip"
        if any(k in nm for k in ("つま先", "足先")):
            return ("LeftToeBase" if L else "RightToeBase") if (L or Rr) else None
        if "ひざ" in nm:
            return ("LeftLeg" if L else "RightLeg") if (L or Rr) else None
        if any(k in nm for k in ("足首", "足ＩＫ", "足IK")):
            return ("LeftFoot" if L else "RightFoot") if (L or Rr) else None
        if "足" in nm:
            return ("LeftUpLeg" if L else "RightUpLeg") if (L or Rr) else None
        if any(k in nm for k in ("肩",)):
            return ("LeftShoulder" if L else "RightShoulder") if (L or Rr) else None
        if any(k in nm for k in ("ひじ", "肘")):
            return ("LeftForeArm" if L else "RightForeArm") if (L or Rr) else None
        if any(k in nm for k in ("手首", "手", "指", "ダミー", "袖", "Sleeve")):
            return ("LeftHand" if L else "RightHand") if (L or Rr) else None
        if any(k in nm for k in ("腕", "捩")):
            return ("LeftArm" if L else "RightArm") if (L or Rr) else None
        return None

    for i, nm in enumerate(bname):
        if i in out:
            continue
        g = by_name(nm)
        if g and g in HOI4_INDEX:
            out[i] = HOI4_INDEX[g]
        else:
            out[i] = int(np.argmin(d[i]))
    return out


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    log = []
    def P(s=""):
        log.append(str(s))
        print(s)

    pmx = PMX(os.path.join(WORK, "薇斯纳.pmx"))
    P(f"PMX: {pmx.name}  顶点 {pmx.vcount:,}  三角形 {pmx.face_index_count // 3:,}  "
      f"材质 {len(pmx.materials)}  骨骼 {len(pmx.bones)}")

    # ---- Umeyama 对齐 ----
    bname = [b["name"] for b in pmx.bones]
    bidx = {nm: i for i, nm in enumerate(bname)}
    src, dst = [], []
    for mmd_nm, h4_nm in ANCHORS.items():
        if mmd_nm in bidx:
            src.append(pmx.bones[bidx[mmd_nm]]["pos"])
            dst.append(HOI4_REST[h4_nm])
    s, R, t = umeyama(src, dst)
    P("")
    P(f"Umeyama 对齐：scale={s:.6f}")
    P(f"R =\n{np.round(R, 5)}")
    P(f"t = {np.round(t, 5)}")
    # 残差
    srcA = np.array(src)
    pred = (s * (R @ srcA.T).T) + t
    res = np.linalg.norm(pred - np.array(dst), axis=1)
    P(f"锚点残差：mean={res.mean():.4f}  max={res.max():.4f}  (HOI4 身高约 7.4)")
    for (mmd_nm, h4_nm), rr in zip(ANCHORS.items(), res):
        P(f"    {mmd_nm:<10} -> {h4_nm:<16} 残差 {rr:.4f}")

    # ---- 顶点变换 ----
    V = np.array(pmx.v_pos, dtype=np.float64)          # (N,3)
    Vt = (s * (R @ V.T).T) + t
    Nr = np.array(pmx.v_nrm, dtype=np.float64)
    Nt = (R @ Nr.T).T
    Nt /= np.maximum(np.linalg.norm(Nt, axis=1, keepdims=True), 1e-9)
    UV = np.array(pmx.v_uv, dtype=np.float64)          # (N,2)

    P("")
    P(f"顶点变换后包围盒：")
    for ax, nm in enumerate("XYZ"):
        P(f"    {nm}: [{Vt[:, ax].min():.4f}, {Vt[:, ax].max():.4f}]   跨度 {Vt[:, ax].max()-Vt[:, ax].min():.4f}")
    P(f"    (HOI4 参考：Y 跨度约 7.49，X 约 5.51，Z 约 1.93)")

    # ---- 材质筛选 ----
    keep_mat = []
    for i, mt in enumerate(pmx.materials):
        if any(k in mt["name"] for k in EXCLUDE_KEYS):
            continue
        keep_mat.append(i)
    P("")
    P(f"材质：共 {len(pmx.materials)}，排除 {len(pmx.materials)-len(keep_mat)} 个装饰件，保留 {len(keep_mat)}")

    # 面区间
    ranges = []
    acc = 0
    for i, mt in enumerate(pmx.materials):
        ranges.append((i, acc, mt["face_count"]))
        acc += mt["face_count"]

    keep_faces = []          # (mat_idx, [v0,v1,v2])
    used_verts = set()
    for mi, st, cnt in ranges:
        if mi not in keep_mat:
            continue
        for k in range(st, st + cnt, 3):
            a, b, c = pmx.faces[k], pmx.faces[k + 1], pmx.faces[k + 2]
            keep_faces.append((mi, a, b, c))
            used_verts.update((a, b, c))

    P(f"保留三角形 {len(keep_faces):,}（原 {pmx.face_index_count//3:,}）")
    P(f"使用顶点 {len(used_verts):,}（原 {pmx.vcount:,}）")

    # 顶点重映射
    used = sorted(used_verts)
    old2new = {o: n for n, o in enumerate(used)}

    # ---- 权重迁移 ----
    bmap = bone_map_table(pmx, s, R, t)
    nb = len(HOI4_ORDER)
    W = np.zeros((len(used), nb), dtype=np.float64)
    for oi, old in enumerate(used):
        wb = pmx.v_wbone[old]
        ww = pmx.v_wweight[old]
        for b, w in zip(wb, ww):
            if w <= 1e-6 or b < 0 or b >= len(bmap):
                continue
            W[oi, bmap[b]] += w
    # 归一化 + 保留 top4
    W[W < 1e-4] = 0.0
    order = np.argsort(-W, axis=1)[:, :4]
    W4 = np.zeros((len(used), 4))
    I4 = np.zeros((len(used), 4), dtype=int) - 1
    for r in range(len(used)):
        idx = order[r]
        vals = W[r, idx]
        tot = vals.sum()
        if tot <= 0:
            I4[r, 0] = HOI4_INDEX["Hip"]
            W4[r, 0] = 1.0
            continue
        vals = vals / tot
        for j in range(4):
            if vals[j] > 0:
                I4[r, j] = int(idx[j])
                W4[r, j] = float(vals[j])

    # 统计每根骨骼受影响的顶点数
    cnt = defaultdict(int)
    for r in range(len(used)):
        for j in range(4):
            if I4[r, j] >= 0:
                cnt[HOI4_ORDER[I4[r, j]]] += 1
    P("")
    P("各 HOI4 骨骼受影响顶点数：")
    for nm in HOI4_ORDER:
        P(f"    {nm:<20} {cnt.get(nm, 0):>7,}")

    # ---- 组装 mesh ----
    # 顶点重排
    VP = Vt[used]
    VN = Nt[used]
    VU = UV[used]

    # 按材质分组 -> 按贴图组分组
    grp_faces = defaultdict(list)
    for mi, a, b, c in keep_faces:
        tp = pmx.materials[mi]["tex"]
        tex = pmx.textures[tp] if 0 <= tp < len(pmx.textures) else ""
        grp_faces[tex_group(tex)].append((old2new[a], old2new[b], old2new[c]))

    P("")
    P("按贴图分组后的材质（每组一个 draw call）：")
    for g, fl in sorted(grp_faces.items(), key=lambda kv: -len(kv[1])):
        P(f"    {g:<8} 三角形 {len(fl):>7,}")

    # ---- 写 XML 树 ----
    root = Xml.Element("File")
    root.set("pdxasset", [1, 0])
    obj = Xml.SubElement(root, "object")
    shape = Xml.SubElement(obj, "PRC_stubShape".replace("PRC_stub", "Vesna_"))
    shape.set("lod", [0])
    mesh = Xml.SubElement(shape, "mesh")
    mesh.set("p", VP.ravel().tolist())
    mesh.set("n", VN.ravel().tolist())
    mesh.set("u0", VU.ravel().tolist())

    tri_all = []
    for g, fl in sorted(grp_faces.items()):
        for (a, b, c) in fl:
            tri_all += [a, b, c]
    mesh.set("tri", tri_all)

    aabb = Xml.SubElement(mesh, "aabb")
    aabb.set("min", VP.min(0).tolist())
    aabb.set("max", VP.max(0).tolist())

    for g, fl in sorted(grp_faces.items()):
        mate = Xml.SubElement(mesh, "material")
        mate.set("shader", ["PdxMeshAdvanced"])
        mate.set("diff", [f"vysna_{g}_diffuse.dds"])
        mate.set("n", [f"vysna_{g}_normal.dds"])
        mate.set("spec", [f"vysna_{g}_specular.dds"])

    skin = Xml.SubElement(mesh, "skin")
    skin.set("bones", [4])
    skin.set("ix", I4.ravel().tolist())
    skin.set("w", [round(float(x), 6) for x in W4.ravel()])

    skel = Xml.SubElement(shape, "skeleton")
    for i, (nm, pa) in enumerate(HOI4_RIG):
        b = Xml.SubElement(skel, nm)
        b.set("ix", [i])
        if pa >= 0:
            b.set("pa", [pa])
        # 单位矩阵（列主序）：R=I, t=0
        b.set("tx", [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0])

    outpath = os.path.join(OUTDIR, "vesna.mesh")
    write_meshfile(outpath, root)
    P("")
    P(f"已写出 {outpath}  ({os.path.getsize(outpath):,} bytes)")

    open(os.path.join(OUTDIR, "convert_report.txt"), "w", encoding="utf-8").write("\n".join(log))
    return outpath


if __name__ == "__main__":
    main()
