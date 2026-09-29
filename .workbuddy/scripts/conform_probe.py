# -*- coding: utf-8 -*-
"""绑定姿态对齐的前期测量：
  1. 参考模型 PRC_infantry 自己的几何——脚到底在 x 多少？
  2. 我们的模型：每根 MMD 骨变换后的位置 p、映射到的 HOI4 骨、位移 q-p。
     重点看翅膀骨（翼*）和腿骨，判断「加权位移对齐」会不会把翅膀推飞。
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdx_data import read_meshfile  # noqa: E402
from pmx_parse import PMX           # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "report_conform_probe.txt")
L = []
P = L.append

HOI4_REST = {
    "Root": (0.0, 0.0, 0.0), "Hip": (0.0, 3.9842, 0.0874),
    "LeftUpLeg": (0.4364, 3.4557, 0.0881), "LeftLeg": (0.6674, 2.0382, 0.1234),
    "LeftFoot": (0.8813, 0.4592, 0.4211), "LeftToeBase": (1.1356, 0.0571, 0.0075),
    "back_mid": (0.0, 4.5314, 0.0675), "LeftShoulder": (0.3192, 5.8114, 0.0327),
    "LeftArm": (0.7141, 5.8690, 0.1240), "LeftForeArm": (1.6297, 5.1430, 0.1928),
    "LeftForeArmRoll": (2.0082, 4.8882, 0.0460), "LeftHand": (2.3635, 4.6490, -0.0918),
    "RightShoulder": (-0.3192, 5.8114, 0.0327), "RightArm": (-0.7141, 5.8690, 0.1240),
    "RightForeArm": (-1.6297, 5.1430, 0.1928),
    "RightForeArmRoll": (-2.0081, 4.8882, 0.0460),
    "RightHand": (-2.3635, 4.6490, -0.0918),
    "head": (0.0, 6.5045, 0.0337), "mid_back_node": (0.0, 4.5799, 0.9770),
    "RightUpLeg": (-0.4364, 3.4557, 0.0881), "RightLeg": (-0.6674, 2.0382, 0.1234),
    "RightFoot": (-0.8813, 0.4592, 0.4211), "RightToeBase": (-1.1356, 0.0571, 0.0075),
    "Left_Hand_node": (2.5845, 4.2989, -0.3321),
    "Left_Hand_node_2": (2.5845, 4.2989, -0.3931),
    "Left_Hand_node_3": (2.5845, 4.2989, -0.3322),
    "Left_Hand_node_4": (2.5845, 4.2989, -0.5512),
    "Right_Hand_node": (-2.5845, 4.2989, -0.3321),
    "Right_Hand_node_2": (-2.5845, 4.2989, -0.4073),
    "Right_Hand_node_3": (-2.5845, 4.2989, -0.4858),
    "Right_Hand_node_4": (-2.5845, 4.2989, -0.5828),
    "Root_node_1": (0.0, 0.0, 0.0), "Root_node_2": (0.0, 0.0, 0.0),
}
HOI4_ORDER = ["Root", "Hip", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
              "back_mid", "LeftShoulder", "LeftArm", "LeftForeArm",
              "LeftForeArmRoll", "LeftHand", "Left_Hand_node",
              "Left_Hand_node_2", "Left_Hand_node_3", "Left_Hand_node_4",
              "head", "RightShoulder", "RightArm", "RightForeArm",
              "RightForeArmRoll", "RightHand", "Right_Hand_node",
              "Right_Hand_node_2", "Right_Hand_node_3", "Right_Hand_node_4",
              "mid_back_node", "RightUpLeg", "RightLeg", "RightFoot",
              "RightToeBase", "Root_node_1", "Root_node_2"]
HOI4_INDEX = {n: i for i, n in enumerate(HOI4_ORDER)}

# ---------------- 1) 参考模型自己的几何
P("=" * 76)
P("【1】参考模型 PRC_infantry 自己的几何（它定义了这个骨架该长什么样）")
P("=" * 76)
root = read_meshfile(r"C:\Users\XIANGZIYUAN\vysna_work\PRC_infantry\PRC_infantry.mesh")
pts = []
for obj in root:
    for shape in obj:
        for m in shape.findall("mesh"):
            if "p" in m.attrib:
                pts.append(np.array(m.get("p"), np.float64).reshape(-1, 3))
P_ = np.concatenate(pts, 0)
P("  全部顶点 %d，bbox X[%.3f,%.3f] Y[%.3f,%.3f] Z[%.3f,%.3f]"
  % (len(P_), P_[:, 0].min(), P_[:, 0].max(), P_[:, 1].min(),
     P_[:, 1].max(), P_[:, 2].min(), P_[:, 2].max()))
for lo, hi, tag in [(0.0, 0.30, "脚底（y<0.30）"), (0.30, 1.00, "踝/小腿下段"),
                    (1.00, 2.10, "小腿"), (2.10, 3.50, "大腿"),
                    (3.50, 4.60, "盆骨/腰")]:
    sel = (P_[:, 1] >= lo) & (P_[:, 1] < hi)
    if sel.sum() == 0:
        continue
    xs = P_[sel, 0]
    left = xs[xs > 0]
    right = xs[xs < 0]
    P("    %-12s n=%4d  |  x>0: [%6.3f,%6.3f] 均值 %6.3f (n=%d)"
      % (tag, int(sel.sum()), left.min() if len(left) else 0,
         left.max() if len(left) else 0, left.mean() if len(left) else 0, len(left)))
    P("    %-12s            x<0: [%6.3f,%6.3f] 均值 %6.3f (n=%d)"
      % ("", right.min() if len(right) else 0, right.max() if len(right) else 0,
         right.mean() if len(right) else 0, len(right)))
P("")
P("  骨架 LeftFoot=(%.3f,%.3f,%.3f)  LeftToeBase=(%.3f,%.3f,%.3f)"
  % (HOI4_REST["LeftFoot"] + HOI4_REST["LeftToeBase"]))
P("  -> 参考模型自己的脚也在 x≈±0.9~1.1，**骨架不是「随便定的」**。")

# ---------------- 2) 我们的模型的骨位移
P("")
P("=" * 76)
P("【2】薇斯纳：各 MMD 骨的位移向量 disp = q(HOI4 目标) - p(源骨变换后)")
P("=" * 76)

s = 0.389774
R = np.array([[1.0, -0.0, -0.0],
              [0.0, 0.9985, 0.0544],
              [0.0, -0.0544, 0.9985]])
t = np.array([-0.0, -0.0614, 0.4709])

pmx = PMX(r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳\薇斯纳.pmx")


def by_name(nm):
    L_, Rr = nm.startswith("左"), nm.startswith("右")
    side = "Left" if L_ else ("Right" if Rr else None)
    if "翼" in nm:
        return "mid_back_node"
    if "全ての親" in nm or "操作中心" in nm:
        return "Root"
    if "つま先" in nm or "足先" in nm:
        return (side + "ToeBase") if side else None
    if "ひざ" in nm:
        return (side + "Leg") if side else None
    if "足首" in nm:
        return (side + "Foot") if side else None
    if "足" in nm:
        return (side + "UpLeg") if side else None
    if "肩" in nm:
        return (side + "Shoulder") if side else None
    if "ひじ" in nm or "肘" in nm:
        return (side + "ForeArm") if side else None
    if "手捩" in nm:
        return (side + "ForeArmRoll") if side else None
    if "腕" in nm:
        return (side + "Arm") if side else None
    if any(k in nm for k in ("手首", "指", "ダミー", "袖", "Sleeve")):
        return (side + "Hand") if side else None
    if any(k in nm for k in ("上半身", "胸")):
        return "back_mid"
    if any(k in nm for k in ("センター", "グルーブ", "腰", "下半身",
                             "スカート", "裙", "PJ_", "Q_")):
        return "Hip"
    if any(k in nm for k in ("Cape", "Rosette", "ShirtDecor", "Breast")):
        return "back_mid"
    if any(k in nm for k in ("首", "頭", "髮", "髪", "前髪", "顔", "颜", "瞳",
                             "睫", "眉", "口", "歯", "鼻", "耳", "照", "目",
                             "Ear", "Hair", "Face")):
        return "head"
    return None


# 复现 build_bone_map（名字 -> 层级继承 -> 位置兜底）
bname = [b["name"] for b in pmx.bones]
n = len(bname)
hmap = np.full(n, -1, np.int64)
for i, nm in enumerate(bname):
    g = by_name(nm)
    if g and g in HOI4_INDEX:
        hmap[i] = HOI4_INDEX[g]
for _ in range(12):
    ch = 0
    for i, b in enumerate(pmx.bones):
        if hmap[i] >= 0:
            continue
        pa = b["parent"]
        if pa is not None and 0 <= pa < n and hmap[pa] >= 0:
            hmap[i] = hmap[pa]
            ch += 1
    if ch == 0:
        break
hpos = np.array([HOI4_REST[nm] for nm in HOI4_ORDER])
mpos = np.array([b["pos"] for b in pmx.bones], np.float64)
mh = (s * (R @ mpos.T).T) + t
rest = np.where(hmap < 0)[0]
if len(rest):
    d = np.linalg.norm(mh[rest][:, None, :] - hpos[None, :, :], axis=2)
    hmap[rest] = np.argmin(d, axis=1)

disp = hpos[hmap] - mh
mag = np.linalg.norm(disp, axis=1)
P("  位移量最大的 30 根骨：")
P("    %-22s %-16s %-24s %-24s %7s" % ("MMD 骨", "-> HOI4 骨", "p(源骨)", "q(HOI4)", "|disp|"))
for i in np.argsort(-mag)[:30]:
    P("    %-22s %-16s (%7.3f,%7.3f,%7.3f)   (%7.3f,%7.3f,%7.3f)  %7.3f"
      % (bname[i], HOI4_ORDER[hmap[i]], mh[i][0], mh[i][1], mh[i][2],
         hpos[hmap[i]][0], hpos[hmap[i]][1], hpos[hmap[i]][2], mag[i]))

P("")
P("  翅膀骨（名字含「翼」）全部：")
P("    %-22s %-16s %-24s %-24s %7s" % ("MMD 骨", "-> HOI4 骨", "p(源骨)", "q(HOI4)", "|disp|"))
for i, nm in enumerate(bname):
    if "翼" in nm:
        P("    %-22s %-16s (%7.3f,%7.3f,%7.3f)   (%7.3f,%7.3f,%7.3f)  %7.3f"
          % (nm, HOI4_ORDER[hmap[i]], mh[i][0], mh[i][1], mh[i][2],
             hpos[hmap[i]][0], hpos[hmap[i]][1], hpos[hmap[i]][2], mag[i]))

P("")
P("  腿骨链：")
for nm in ("左足", "左ひざ", "左足首", "左つま先", "左足D", "左ひざD", "左足首D", "左つま先D"):
    if nm in bname:
        i = bname.index(nm)
        P("    %-22s %-16s (%7.3f,%7.3f,%7.3f)   (%7.3f,%7.3f,%7.3f)  %7.3f"
          % (nm, HOI4_ORDER[hmap[i]], mh[i][0], mh[i][1], mh[i][2],
             hpos[hmap[i]][0], hpos[hmap[i]][1], hpos[hmap[i]][2], mag[i]))

# 翅膀顶点的权重构成
P("")
P("  翅膀材质（翼/翼2）顶点用到的 MMD 骨：")
cnt = {}
mat_of_v = {}
acc = 0
for mt in pmx.materials:
    for k in range(acc, acc + mt["face_count"], 3):
        for v in (pmx.faces[k], pmx.faces[k + 1], pmx.faces[k + 2]):
            mat_of_v[v] = mt["name"]
    acc += mt["face_count"]
for v, nmv in mat_of_v.items():
    if nmv not in ("翼", "翼2"):
        continue
    for b, w in zip(pmx.v_wbone[v], pmx.v_wweight[v]):
        if w > 1e-6:
            cnt.setdefault(bname[b], [0, 0.0])
            cnt[bname[b]][0] += 1
            cnt[bname[b]][1] += w
for k, v in sorted(cnt.items(), key=lambda x: -x[1][1])[:20]:
    P("      %-22s 顶点引用 %5d  权重和 %8.1f" % (k, v[0], v[1]))

txt = "\n".join(L)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(txt)
print(txt)
print("\n-> " + OUT)
