# -*- coding: utf-8 -*-
"""薇斯纳（MMD PMX） -> HOI4 .mesh 转换器。

管线
  1. 解析 PMX（顶点/法线/UV/面/材质/骨骼/权重）
  2. Umeyama 把 MMD 骨架对齐到 HOI4 标准 33 骨骼骨架（s, R, t）
  3. 顶点/法线变换到 HOI4 骨架空间
  4. 按材质筛选（去掉 结晶/头饰），按 4 个语义组归并材质
  5. 每组把用到的贴图打进一张图集并重映射 UV
  6. MMD 权重 -> HOI4 33 骨骼（名字规则 + 层级继承 + 位置最近兜底），top4 归一化
  7. 输出 .mesh（skeleton 块直接复用 PRC_infantry.mesh 的，保证与原版动画完全一致）
  8. 输出 DDS 贴图（DXT1/DXT5 + 全 mip 链）

用法： python vysna_build.py [--cap-scale 1.0] [--outdir ...]
"""
import argparse
import os
import sys
from collections import defaultdict

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")

from pmx_parse import PMX                      # noqa: E402
from pdx_write import write_tree, tangents     # noqa: E402
from dds_encode import write_dds, rgba_from_image  # noqa: E402

import xml.etree.ElementTree as Xml            # noqa: E402

# ------------------------------------------------------------------ 路径
SRC = r"C:\Users\XIANGZIYUAN\vysna_work\薇斯纳"
PRC_ZIP_DIR = r"C:\Users\XIANGZIYUAN\vysna_work\PRC_infantry"
DEFAULT_OUT = os.path.join(HERE, "..", "vysna_out")

# ------------------------------------------------------------------ HOI4 标准骨架（33 根）
HOI4_RIG = [
    ("Root", -1), ("Hip", 0), ("LeftUpLeg", 1), ("LeftLeg", 2), ("LeftFoot", 3),
    ("LeftToeBase", 4), ("back_mid", 1), ("LeftShoulder", 6), ("LeftArm", 7),
    ("LeftForeArm", 8), ("LeftForeArmRoll", 9), ("LeftHand", 10),
    ("Left_Hand_node", 11), ("Left_Hand_node_2", 11), ("Left_Hand_node_3", 11),
    ("Left_Hand_node_4", 11), ("head", 6), ("RightShoulder", 6), ("RightArm", 17),
    ("RightForeArm", 18), ("RightForeArmRoll", 19), ("RightHand", 20),
    ("Right_Hand_node", 21), ("Right_Hand_node_2", 21), ("Right_Hand_node_3", 21),
    ("Right_Hand_node_4", 21), ("mid_back_node", 6), ("RightUpLeg", 1),
    ("RightLeg", 27), ("RightFoot", 28), ("RightToeBase", 29),
    ("Root_node_1", 0), ("Root_node_2", 0),
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

# 拟合用的锚点（MMD 名 -> HOI4 名）。只取解剖学上可靠的关节。
FIT_ANCHORS = {
    "全ての親": "Root",
    "左足": "LeftUpLeg", "右足": "RightUpLeg",
    "左ひざ": "LeftLeg", "右ひざ": "RightLeg",
    "左足首": "LeftFoot", "右足首": "RightFoot",
    "左つま先": "LeftToeBase", "右つま先": "RightToeBase",
    "左ひじ": "LeftForeArm", "右ひじ": "RightForeArm",
    "左手首": "LeftHand", "右手首": "RightHand",
    "頭": "head",
    "上半身": "back_mid",
    "センター": "Hip",
}

# 材质 -> 语义组
MAT_GROUP = {
    "颜": "face", "颜2": "face", "颜3": "face", "颜4": "face", "睫": "face",
    "眉": "face", "白目": "face", "目": "face", "瞳": "face", "目光": "face",
    "鼻线": "face", "口舌": "face", "齿": "face", "星目": "face", "照れ": "face",
    "前髪": "hair", "髮": "hair", "髮+": "hair",
    "翼": "hair", "翼2": "hair",          # 这两个用的就是 髮.png，跟头发同组
    "翼+": "wing",                        # 用 翼s.png
    "体": "body", "体2": "body", "披肩": "body", "披肩饰": "body",
    "肌": "body", "肌2": "body",
    "袜": "body", "袜s": "body", "袜s2": "body",
    "裙": "body", "裙内": "body", "裙+": "body", "披肩s": "body",
}
EXCLUDE_KEYS = [
    "结晶",     # 结晶/结晶+/结晶s 装饰件，用户要求去掉
    "头饰",     # 头饰，用户要求去掉
    # ---- 以下为「与基础层几何重合」的 MMD 叠加材质，一律剔除后画的那一层 ----
    # 它们靠材质绘制顺序分层，而 HOI4 只有深度测试：重合处谁可见取决于
    # LESS / LESS_EQUAL 的实现细节，不可靠。而且这些层的贴图大多是「大面积透明」
    # 的叠加图（透明区 RGB 常为黑），一旦胜出就会出现黑块。
    # 完整重合清单见 .workbuddy/scripts/coincident.py 的 report_coincident.txt。
    "照れ",     # vs 颜      1942 三角 -> 会盖黑整张脸
    "袜s",      # 袜s/袜s2 vs 袜  1678 三角 -> 会盖黑整条腿
    "翼+",      # vs 翼       430 三角
    "髮+",      # vs 髮 5775 / 前髪 4758 三角 -> 会盖黑整片刘海
    "肌2",      # vs 体      2504 三角（贴图 肌.png 可见率 0.0%）
    "披肩s",     # vs 披肩      243 三角（贴图 体s.png 可见率 0.1%）
    "裙+",      # vs 体       449 三角（贴图 体s.png）
    "颜3",      # vs 颜2      896 三角（表情层，且 UV 的 v 越界绕回）
    "颜4",      # vs 颜2/颜3  896 三角（同上）
    # 说明：裙 / 裙内 也逐点重合（1822 三角），但两者用的是同一张贴图 裙.png，
    #       谁的 UV 区域胜出都是裙料，视觉上无差别，故保留。
    # ---- 眼部叠层：只留 目，其余全剔 ----
    # 实测 scripts/eye_only.py：只渲染 目 一张，就是一只**完整正确**的眼睛
    # （眼白 + 虹膜 + 瞳孔 + 高光 + 下眼睑那朵小花全都在 目.png 里）。
    # 而 白目/瞳/目光/星目 只是把同一只眼拆成几片同轴叠层，在 HOI4 的纯深度
    # 测试下必然互相遮挡（实测出来是一对空白白眼窝）。
    # 所以这里整层剔除，眼 = 单个 目 材质，零 z-fighting。
    "白目",     # 444 面，源图借脸皮 颜.png，是个横跨双眼的薄透镜 -> 会盖住虹膜
    "瞳",       # 192 面，瞳孔已画在 目.png 内
    "目光",     # 200 面，高光已画在 目.png 内
    "星目",     # 28 面，星形眼（特殊表情用），默认脸不该有
]

# ★ 精确名剔除（子串匹配会误伤：如 "目" 会命中 "目2"）
EXCLUDE_EXACT = set()

# ============================ 眼睛（本模型最难的一块） ============================
#
# ★ 结论：眼睛 = 单个「目」材质，其余眼部叠层已在 EXCLUDE_KEYS 里整层剔除。
#   实测 scripts/eye_only.py：只渲染 目 一张，就是一只完整正确的眼睛
#   （眼白 + 虹膜 + 瞳孔 + 高光 + 下眼睑那朵花全画在 目.png 里）。
#   原模型的 白目/瞳/目光/星目 只是把同一只眼拆成几片「同轴叠层」，
#   靠 MMD 的材质绘制顺序分层；HOI4 只有深度测试，必然互相遮挡。
#
# ★ 「目」需要沿视线方向（-Z，角色朝 -Z）整层前推，否则会被脸皮 颜/颜2 盖住，
#   渲染出来是一对空白白眼窝（这正是长期排查的症状）。
#   实测扫描见 scripts/eye_push2.py：只保留 颜/颜2/睫/目 时，
#     push=0.010 -> 虹膜只露出下半
#     push=0.020 -> 大半露出
#     push=0.030 -> 完整
#     push=0.045 -> 完整且最饱满   ← 采用
#     push=0.060 -> 同样正常（说明阈值约 0.025，0.045 有充足余量）
#   量级参考：0.045 / 身高 7.4 ≈ 0.6%，肉眼不可见，也不会从脸颊凸出来。
#   ⚠ 注意 push 必须做在「按材质分开的顶点副本」上（见下面组装循环的注释），
#     直接改 Vt 会把同一批顶点在其它材质里的位置一起挪走。
EYE_FORWARD = {
    "目": 0.0450,   # 虹膜贴片（含眼白/瞳孔/高光）
}

# ---------------- 通用兜底：让本脚本能直接吃其它原神系 MMD 模型 ----------------
# 上面的 MAT_GROUP / EYE_FORWARD 是薇斯纳的精确表；命中不了的材质走下面启发式，
# 保证「任意模型都能跑通」。分组只决定 draw call 切分与图集张数，
# 分错了顶多多打一张图集，不影响几何/骨骼正确性。
_M_FACE_K = ("颜", "顏", "眼", "目", "瞳", "睫", "眉", "口", "舌", "歯", "齿",
             "鼻", "照", "脸", "臉", "泪", "涙", "嘴", "颊")
_M_FACE_EN = ("face", "eye", "iris", "pupil", "lash", "brow", "mouth",
              "teeth", "tear", "tongue", "nose")
_M_HAIR_K = ("髮", "髪", "毛", "翼", "尾")
_M_HAIR_EN = ("hair", "wing", "feather", "tail")


def mat_group_of(nm):
    """材质名 -> body / face / hair / wing（找不到规则时兜底 body）"""
    v = MAT_GROUP.get(nm)
    if v:
        return v
    # 「神之眼」是原神系的腰间/背部挂件，名字里带「眼」但绝不是脸 -> 先排掉
    if "神之眼" in nm or "神之心" in nm:
        return "body"
    low = nm.lower()
    if any(k in nm for k in _M_FACE_K) or any(k in low for k in _M_FACE_EN):
        return "face"
    if any(k in nm for k in _M_HAIR_K) or any(k in low for k in _M_HAIR_EN):
        return "hair"
    return "body"


def eye_forward(nm):
    """只对「完整的眼」材质前推；眼白/瞳/高光/眉/睫等叠层与眉毛一律不推。"""
    v = EYE_FORWARD.get(nm)
    if v is not None:
        return v
    low = nm.lower()
    no = ("白目", "瞳", "目光", "星目", "眉", "睫", "罩", "lash", "brow",
          "eyewhite", "eye_white", "irishighlight")
    if any(k in nm for k in no) or any(k in low for k in no):
        return None
    if "目" in nm or "眼" in nm or low in ("eye", "eyes", "iris"):
        return 0.0450
    return None

# ★ 关于眼球 UV（本模型的坑，记下来免得再踩）：
#   PMX 里 目/瞳 的 uv 是 u[0.090,0.910] v[0.011,0.990]（基本是整张贴图）。
#   但 MMD 导出器会把「接缝顶点」的 uv 故意 +1（例如 0.0416 表示 1.0416），
#   目的是让双线性采样不跨格渗色。所以直接看 min/max 会以为 uv 是 [-0.32, ...]
#   —— 那是接缝顶点的 1.0+小数，不是真的负坐标。
#   正确处理就是 np.mod(uv, 1.0)，不要做任何「UV 盒子线性映射」，
#   否则会把整层压成一个点（踩过：被压成 0.009 宽、采样到 gutter 全黑）。

GROUP_CAP = {"face": 512, "hair": 768, "body": 512, "wing": 512}
GUTTER = 8

# ==================== 绑定姿态对齐（bind conform）====================
#
# ★ 为什么必须做
#   MMD 骨架与 HOI4 骨架的**比例不同**：本模型大腿根 y=11.22 / 头 16.88，
#   腿长 : 躯干 = 1.78；HOI4 是 3.40 : 3.05 = 1.11。任何「整体相似变换」
#   都不可能同时对齐所有关节，实测残留偏差：
#       左足(大腿根) -> LeftUpLeg   y 差 0.84
#       左ひざ(膝)   -> LeftLeg     x 差 0.42, y 差 0.34
#       左足首(踝)   -> LeftFoot    x 差 0.76
#       左つま先(脚尖)-> LeftToeBase x 差 0.92
#   后果：蒙皮时每根骨绕**它自己的原点**旋转，而那个原点离真正的腿有 0.8~0.9
#   远 —— 走路时两条腿绕错误的圆心摆动、互相穿插。用真实动画离线渲染可复现：
#   scripts/_posetest/VY_BEFORE_f12_front.png（两腿交叉成 X）。
#   对照：MOD 里跑得好好的 Keqing / Amber / Furina，腿部几何的 x 是
#   0.55 / 0.75 / 0.9，正落在骨架的 0.44 / 0.67 / 0.88 上；
#   我们原来是 0.28 / 0.31 / 0.15，明显偏内。
#
# ★ 做法 = 标准的「改绑定姿态」
#   绑定时每根骨都是纯平移，所以 M_i·B_i⁻¹ 也是纯平移 (q_i − p_i)：
#       v' = Σ w_i · (v + q_i − p_i) = v + Σ w_i · (q_i − p_i)
#   即「每个顶点按权重把各骨的位移向量加权平均加上去」。
#   这样网格的 rest 姿态与骨架严格一致，动画的旋转轴心回到解剖学位置。
#
# ⚠ 只有「解剖学骨骼」参与（腿/臂/脊柱/头）。头发、翅膀、裙、物理骨、
#   IK 骨一律不参与，原因见 CONFORM_DENY。
CONFORM_ALLOW = ("足", "ひざ", "つま先", "足先", "腕", "ひじ", "肘", "手首",
                 "手捩", "肩", "指", "センター", "グルーブ", "腰", "上半身",
                 "下半身", "頭", "首")
CONFORM_DENY = (
    # IK / 控制骨：位移可达 3.5，但正常情况下没有顶点权重
    "ＩＫ", "IK", "操作中心", "全ての親", "すべての親", "ダミー",
    # 翅膀：骨铺满整对翅膀（左上翼_16 在 (2.14, 7.82, 2.36)，离 mid_back_node
    # 有 4.1 远），照位移走会把整对翅膀拽成一个点
    "翼",
    # 长发：同理（髮_26 离 head 有 2.4），而它们本就该刚性跟随头骨
    "髮", "髪", "前髪",
    # 裙：本来就该跟着骨盆
    "スカート", "裙",
    # 袖/披肩等装饰
    "袖", "Sleeve", "Cape", "Rosette", "ShirtDecor", "Breast",
    # 五官：它们跟着 head 骨，head 的位移本来就 ~0
    "顔", "颜", "目", "瞳", "睫", "眉", "口", "歯", "鼻", "耳", "照", "表情",
)


def conform_weight(nm):
    """这根 MMD 骨是否参与绑定姿态对齐。"""
    if any(k in nm for k in CONFORM_DENY):
        return 0.0
    if any(k in nm for k in CONFORM_ALLOW):
        return 1.0
    return 0.0



# ------------------------------------------------------------------ 工具
def umeyama(src, dst):
    """求 dst ≈ s*R@src + t。无反射约束。"""
    src = np.asarray(src, np.float64)
    dst = np.asarray(dst, np.float64)
    n = len(src)
    mu_s, mu_d = src.mean(0), dst.mean(0)
    sc, dc = src - mu_s, dst - mu_d
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


def robust_umeyama(srcs, dsts, names, rounds=3, keep=0.75):
    """带离群点剔除的 Umeyama。返回 (s, R, t, 使用的锚点名)。"""
    idx = list(range(len(srcs)))
    s = R = t = None
    for r in range(rounds):
        s, R, t = umeyama([srcs[i] for i in idx], [dsts[i] for i in idx])
        pred = (s * (R @ np.array([srcs[i] for i in idx]).T).T) + t
        res = np.linalg.norm(pred - np.array([dsts[i] for i in idx]), axis=1)
        if r == rounds - 1 or len(idx) <= 6:
            break
        thr = np.quantile(res, keep)
        newidx = [idx[k] for k in range(len(idx)) if res[k] <= thr]
        if len(newidx) < 6:
            break
        idx = newidx
    return s, R, t, [names[i] for i in idx]


# ------------------------------------------------------------------ 骨骼映射
def build_bone_map(pmx, s, R, t, report):
    bname = [b["name"] for b in pmx.bones]
    n = len(bname)
    hmap = np.full(n, -1, dtype=np.int64)

    # ---- 1) 名字规则
    # ⚠ 顺序铁律：腿 -> 臂 -> 躯干 -> 头。因为「足首」(脚踝) 含「首」(脖子)、
    #   「手首」(手腕) 也含「首」，头部规则必须排在最后，否则脚踝/手腕会被判成头。
    def by_name(nm):
        L, Rr = nm.startswith("左"), nm.startswith("右")
        side = "Left" if L else ("Right" if Rr else None)
        # 翅膀（挂在背后）
        # ★★ 绝对不要挂 mid_back_node！实测：42 个原版步兵动画里 39 个（93%）把它
        #    的 s 通道恒设为 0 —— HOI4 用它当"可选背部装备"的开关，步兵不背包就
        #    整根骨缩没，挂在上面的几何会在游戏里彻底消失（翅膀就是这么没的）。
        #    改挂它的父骨 back_mid：42/42 个动画都安全（s 恒为 1）。
        if "翼" in nm:
            return "back_mid"
        # 根控制骨
        if "全ての親" in nm or "操作中心" in nm:
            return "Root"
        # ---- 腿（必须先于「首」判断）
        if "つま先" in nm or "足先" in nm:
            return (side + "ToeBase") if side else None
        if "ひざ" in nm:
            return (side + "Leg") if side else None
        if "足首" in nm:
            return (side + "Foot") if side else None
        if "足" in nm:
            return (side + "UpLeg") if side else None
        # ---- 臂
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
        # ---- 躯干
        if any(k in nm for k in ("上半身", "胸")):
            return "back_mid"
        if any(k in nm for k in ("センター", "グルーブ", "腰", "下半身",
                                 "スカート", "裙", "PJ_", "Q_")):
            return "Hip"
        if any(k in nm for k in ("Cape", "Rosette", "ShirtDecor", "Breast")):
            return "back_mid"
        # ---- 头（放最后）
        if any(k in nm for k in ("首", "頭", "髮", "髪", "前髪", "顔", "颜", "瞳",
                                 "睫", "眉", "口", "歯", "鼻", "耳", "照", "目",
                                 "Ear", "Hair", "Face")):
            return "head"
        return None

    n_named = 0
    for i, nm in enumerate(bname):
        g = by_name(nm)
        if g and g in HOI4_INDEX:
            hmap[i] = HOI4_INDEX[g]
            n_named += 1

    # ---- 2) 层级继承（physics 骨跟着解剖学父骨走）
    n_inherit = 0
    for _ in range(12):
        changed = 0
        for i, b in enumerate(pmx.bones):
            if hmap[i] >= 0:
                continue
            pa = b["parent"]
            if pa is not None and 0 <= pa < n and hmap[pa] >= 0:
                hmap[i] = hmap[pa]
                changed += 1
        n_inherit += changed
        if changed == 0:
            break

    # ---- 3) 位置最近兜底
    hpos = np.array([HOI4_REST[nm] for nm in HOI4_ORDER])
    mpos = np.array([b["pos"] for b in pmx.bones])
    mh = (s * (R @ mpos.T).T) + t
    n_pos = 0
    rest = np.where(hmap < 0)[0]
    if len(rest):
        d = np.linalg.norm(mh[rest][:, None, :] - hpos[None, :, :], axis=2)
        hmap[rest] = np.argmin(d, axis=1)
        n_pos = len(rest)

    report("  骨骼映射：名字规则 %d，层级继承 %d，位置兜底 %d，共 %d 根"
           % (n_named, n_inherit, n_pos, n))
    return hmap


# ------------------------------------------------------------------ 图集
def next_pow2(v):
    p = 1
    while p < v:
        p *= 2
    return p


def fresh(path):
    """本项目工作区禁止覆盖已存在文件，且脚本内 os.remove 会被静默拦截。
    所以目标名被占用时自动改用 name_2.ext / name_3.ext ..."""
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(path)
    i = 2
    while os.path.exists("%s_%d%s" % (stem, i, ext)):
        i += 1
    return "%s_%d%s" % (stem, i, ext)


def resize_keep_aspect(im, cap):
    w, h = im.width, im.height
    sc = min(1.0, cap / float(max(w, h)))
    nw = max(4, int(round(w * sc)))
    nh = max(4, int(round(h * sc)))
    # 对齐到 4 的倍数
    nw -= nw % 4
    nh -= nh % 4
    nw, nh = max(4, nw), max(4, nh)
    if (nw, nh) != (w, h):
        im = im.resize((nw, nh), 1)
    return im


def build_atlas(tex_indices, pmx, cap, report, tag):
    """把若干贴图打进一张 PO2 图集。
    返回 (atlas_rgba (H,W,4), placements {tex_idx: (X,Y,W,H, tex_w, tex_h)})，
    其中 (X,Y,W,H) 是含 gutter 的 cell 在 atlas 中的位置，(tex_w,tex_h) 是贴图在 cell 内区尺寸。
    """
    tiles = {}
    for ti in tex_indices:
        path = pmx.textures[ti].replace("\\", os.sep).replace("/", os.sep)
        full = os.path.join(SRC, path)
        im = Image.open(full)
        im = resize_keep_aspect(im, cap)
        tw, th = im.width, im.height
        a = np.asarray(im.convert("RGBA"), np.uint8)
        G = GUTTER
        cw, ch = tw + 2 * G, th + 2 * G
        cell = np.zeros((ch, cw, 4), np.uint8)
        cell[G:G + th, G:G + tw] = a
        # 边缘延展（防 mip/双线性渗出）
        cell[:G, G:G + tw] = a[0:1, :, :]
        cell[G + th:, G:G + tw] = a[-1:, :, :]
        cell[:, :G] = cell[:, G:G + 1]
        cell[:, G + tw:] = cell[:, G + tw - 1:G + tw]
        tiles[ti] = (cell, tw, th)

    # 货架装箱：按高度降序。枚举若干 PO2 宽度，取面积最小的一组。
    order = sorted(tiles, key=lambda k: (-tiles[k][0].shape[0], tiles[k][0].shape[1]))
    total_area = sum(t[0].shape[0] * t[0].shape[1] for t in tiles.values())
    maxw = max(t[0].shape[1] for t in tiles.values())

    def pack(aw):
        x = y = rowh = 0
        place = {}
        for k in order:
            cell = tiles[k][0]
            cw, ch = cell.shape[1], cell.shape[0]
            if x + cw > aw:
                x = 0
                y += rowh
                rowh = 0
            place[k] = (x, y, cw, ch, tiles[k][1], tiles[k][2])
            x += cw
            rowh = max(rowh, ch)
        return place, y + rowh

    best = None
    cands = set()
    w = next_pow2(maxw)
    while w <= 4096:
        cands.add(w)
        w *= 2
    cands.add(next_pow2(int(np.sqrt(total_area) * 1.1)))
    for aw in sorted(cands):
        place, need_h = pack(aw)
        ah = next_pow2(need_h)
        if ah > 4096:
            continue
        score = (aw * ah, max(aw, ah))     # 面积优先，其次更接近正方形
        if best is None or score < best[0]:
            best = (score, aw, ah, place, need_h)
    if best is None:
        raise RuntimeError("图集装箱失败：%s" % sorted(cands))
    _, aw, ah, place, need_h = best

    atlas = np.zeros((ah, aw, 4), np.uint8)
    for k, (X, Y, cw, ch, tw, th) in place.items():
        atlas[Y:Y + ch, X:X + cw] = tiles[k][0]
    used_w = max(v[0] + v[2] for v in place.values())
    report("  [%s] 贴图 %d 张 -> 图集 %dx%d  (占用 %dx%d)"
           % (tag, len(tex_indices), aw, ah, used_w, need_h))
    return atlas, place


# ------------------------------------------------------------------ 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.abspath(DEFAULT_OUT))
    ap.add_argument("--cap-scale", type=float, default=1.0)
    ap.add_argument("--name", default="Vysna")
    ap.add_argument("--pmx", default=None,
                    help="源 PMX 绝对路径（默认用 SRC 下的 薇斯纳.pmx）")
    ap.add_argument("--no-conform", action="store_true",
                    help="跳过绑定姿态对齐（调试用，产物动画会错）")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    # 本项目工作区禁止覆盖已存在文件 —— 先把上次的产物清掉（删除是允许的）
    for fn in os.listdir(args.outdir):
        fp = os.path.join(args.outdir, fn)
        if os.path.isfile(fp):
            try:
                os.remove(fp)
            except OSError as e:
                print("  !! 清理旧文件失败 %s: %s" % (fn, e))
    log = []

    def P(s=""):
        log.append(str(s))
        print(s)

    P("=" * 74)
    P("%s PMX -> HOI4 .mesh" % args.name)
    P("=" * 74)

    pmx = PMX(args.pmx or os.path.join(SRC, "薇斯纳.pmx"))
    P("源: %s  顶点 %d  三角 %d  材质 %d  骨骼 %d  贴图 %d"
      % (pmx.name, pmx.vcount, pmx.face_index_count // 3,
         len(pmx.materials), len(pmx.bones), len(pmx.textures)))

    # ---------- 1) 骨架对齐
    bname = [b["name"] for b in pmx.bones]
    bidx = {}
    for i, nm in enumerate(bname):
        bidx.setdefault(nm, i)
    src, dst, names = [], [], []
    for mmd_nm, h4_nm in FIT_ANCHORS.items():
        if mmd_nm in bidx:
            src.append(pmx.bones[bidx[mmd_nm]]["pos"])
            dst.append(HOI4_REST[h4_nm])
            names.append(mmd_nm)
    P("")
    P("骨架对齐（分三步定 s / R / t）：")
    # ① 旋转：锚点最小二乘（只用方向）
    _, R, _ = umeyama(src, dst)
    mb = np.array([b["pos"] for b in pmx.bones], np.float64)
    mbr = (R @ mb.T).T

    def bp(nm):
        return mbr[bidx[nm]]

    # ② 尺度：用骨架身高（头骨 <-> 脚尖骨）对齐。
    #    比"整体包围盒"更可靠：MMD 与 HOI4 的头发/装备体积不同，包围盒会被带偏。
    s = ((HOI4_REST["head"][1] - HOI4_REST["LeftToeBase"][1])
         / (bp("頭")[1] - bp("左つま先")[1]))
    # ③ 平移：Y 由脚尖骨落地定；XZ 由躯干中线定
    ty = HOI4_REST["LeftToeBase"][1] - s * bp("左つま先")[1]
    MID_SRC = [n for n in ("全ての親", "センター", "腰", "上半身", "上半身1",
                           "上半身2", "首", "頭") if n in bidx]
    MID_DST = ["Hip", "back_mid", "head"]
    ms = np.mean([bp(n) for n in MID_SRC], 0)
    md = np.mean([HOI4_REST[n] for n in MID_DST], 0)
    t = np.array([md[0] - s * ms[0], ty, md[2] - s * ms[2]])

    P("  scale = %.6f   (源骨架身高 %.3f -> HOI4 %.3f)"
      % (s, bp("頭")[1] - bp("左つま先")[1],
         HOI4_REST["head"][1] - HOI4_REST["LeftToeBase"][1]))
    P("  R = %s" % np.array2string(R, precision=4, suppress_small=True).replace("\n", "\n      "))
    P("  t = %s" % np.array2string(t, precision=4, suppress_small=True))

    # 关键关节落点自检
    P("  关节落点自检（源 -> 期望）：")
    for mmd_nm, h4_nm in [("左つま先", "LeftToeBase"), ("左足首", "LeftFoot"),
                          ("左ひざ", "LeftLeg"), ("左足", "LeftUpLeg"),
                          ("センター", "Hip"), ("上半身", "back_mid"),
                          ("頭", "head"), ("左手首", "LeftHand")]:
        if mmd_nm in bidx:
            got = s * bp(mmd_nm) + t
            exp = np.array(HOI4_REST[h4_nm])
            P("      %-8s -> %-14s 落点 (%6.3f,%6.3f,%6.3f)  期望 (%6.3f,%6.3f,%6.3f)  偏差 %.3f"
              % (mmd_nm, h4_nm, got[0], got[1], got[2], exp[0], exp[1], exp[2],
                 np.linalg.norm(got - exp)))

    # 用最终的 (s,R,t) 报锚点残差
    srcA = np.array(src)
    pred = (s * (R @ srcA.T).T) + t
    res = np.linalg.norm(pred - np.array(dst), axis=1)
    P("")
    P("锚点残差（最终变换）：mean=%.4f  max=%.4f   (HOI4 身高 7.42)"
      % (res.mean(), res.max()))

    # ---------- 2) 顶点变换
    V = np.array(pmx.v_pos, np.float64)
    Vt = (s * (R @ V.T).T) + t
    Nr = np.array(pmx.v_nrm, np.float64)
    Nt = (R @ Nr.T).T
    Nt /= np.maximum(np.linalg.norm(Nt, axis=1, keepdims=True), 1e-9)
    UV = np.array(pmx.v_uv, np.float64)
    P("")
    P("变换后顶点包围盒：")
    for ax, nm in enumerate("XYZ"):
        P("    %s: [%8.4f, %8.4f]  跨度 %7.4f"
          % (nm, Vt[:, ax].min(), Vt[:, ax].max(), Vt[:, ax].max() - Vt[:, ax].min()))
    P("    参考：HOI4 模型 Y 跨度 ~7.42（脚 y≈0，头顶 y≈7.42）")

    # ---------- 3) 材质筛选与分组
    keep = []
    for i, mt in enumerate(pmx.materials):
        # EXCLUDE_EXACT 走精确名（否则 "目" 会误伤 "目2"），EXCLUDE_KEYS 走子串
        if mt["name"] in EXCLUDE_EXACT or any(k in mt["name"] for k in EXCLUDE_KEYS):
            continue
        keep.append(i)
    P("")
    P("材质 %d 个，排除装饰件后保留 %d 个（去掉 %s）"
      % (len(pmx.materials), len(keep),
         "/".join(sorted({mt["name"] for i, mt in enumerate(pmx.materials)
                          if i not in keep}))))

    # 面区间
    rng = []
    acc = 0
    for i, mt in enumerate(pmx.materials):
        rng.append((i, acc, mt["face_count"]))
        acc += mt["face_count"]

    grp_faces = defaultdict(list)      # group -> [(mat_idx, a, b, c)]
    grp_mats = defaultdict(set)
    for i, st, cnt in rng:
        if i not in keep:
            continue
        nm = pmx.materials[i]["name"]
        g = mat_group_of(nm)
        if g is None:
            P("    !! 材质 %r 未分组，跳过" % nm)
            continue
        grp_mats[g].add(nm)
        for k in range(st, st + cnt, 3):
            grp_faces[g].append((i, pmx.faces[k], pmx.faces[k + 1], pmx.faces[k + 2]))

    P("")
    P("分组结果：")
    for g in sorted(grp_faces):
        P("    %-6s 材质 %d 个 %-40s 三角 %d"
          % (g, len(grp_mats[g]), ",".join(sorted(grp_mats[g])),
             len(grp_faces[g])))

    # ---------- 4) 图集
    P("")
    P("构建贴图图集（gutter=%d px）：" % GUTTER)
    atlases = {}
    for g in sorted(grp_faces):
        tis = set()
        for mi, a, b, c in grp_faces[g]:
            ti = pmx.materials[mi]["tex"]
            if 0 <= ti < len(pmx.textures):
                tis.add(ti)
        cap = int(GROUP_CAP.get(g, 512) * args.cap_scale)
        atlas, place = build_atlas(sorted(tis, key=lambda t: str(t)), pmx, cap, P, g)
        atlases[g] = (atlas, place)

    # 贴图最终文件名（若被占用会自动改名，mesh 里的引用同步更新）
    tex_file = {}
    for g in atlases:
        tex_file[g] = os.path.basename(
            fresh(os.path.join(args.outdir, "%s_%s_diffuse.dds" % (args.name.lower(), g))))
    nomat = os.path.basename(fresh(os.path.join(
        args.outdir, "%s_nospec.dds" % args.name.lower())))
    nonrm = os.path.basename(fresh(os.path.join(
        args.outdir, "%s_flat_normal.dds" % args.name.lower())))
    P("")
    P("贴图输出名：%s  共享 %s / %s"
      % (", ".join("%s=%s" % (g, tex_file[g]) for g in sorted(tex_file)), nomat, nonrm))

    # ---------- 5) 权重迁移
    P("")
    hmap = build_bone_map(pmx, s, R, t, P)

    nb = len(HOI4_ORDER)
    used_cnt = defaultdict(int)

    # ---------- 5b) 绑定姿态对齐（原理见文件顶部 CONFORM_ALLOW 的说明）
    hpos = np.array([HOI4_REST[nm] for nm in HOI4_ORDER], np.float64)
    bp_t = (s * (R @ np.array([b["pos"] for b in pmx.bones], np.float64).T).T) + t
    cw = np.array([conform_weight(b["name"]) for b in pmx.bones], np.float64)
    disp = (hpos[hmap] - bp_t) * cw[:, None]

    # ★★ 未参与对齐的骨**不能原地不动**。
    #   身体整体被搬走（中轴 dy 达 −0.86），而这些骨留原地 → 挂在它们上面的几何
    #   会与身体错位。实测最典型的受害者就是**眼睛**：
    #     「目」材质绑在 左目先 / 右目先 上，而 CONFORM_DENY 里有 "目" → cw=0；
    #     脸皮「颜」绑 頭（参与对齐）被搬走，眼球却原地不动 →
    #     眼球陷进脸里，渲染/游戏里眼睛变成闭眼（只剩脸皮上画的睫毛线）。
    #     「睫」同理，所以闭眼线还在。
    #   正确做法：沿父链向上继承**最近一个已对齐祖先**的位移 —— 刚性跟随，
    #   与所属部位保持原始相对位置（眼睛跟 頭、翅膀/长发跟 上半身 或 back_mid）。
    #   ⚠ 绝不能改用它们「自己的 disp」：翼骨自己的 disp 达 4.118，
    #     会把整对翅膀拽成一个点（这正是上一轮踩过的坑）。
    n_b = len(pmx.bones)
    resolved = cw > 0.0
    n_inherit = 0
    if not args.no_conform:
        for _ in range(64):
            changed = 0
            for i in range(n_b):
                if resolved[i]:
                    continue
                j = pmx.bones[i]["parent"]
                if 0 <= j < n_b and resolved[j]:
                    disp[i] = disp[j]
                    resolved[i] = True
                    n_inherit += 1
                    changed += 1
            if not changed:
                break
        P("  刚性跟随：%d 根骨沿父链继承了祖先的位移（眼睛/睫毛/翅膀/长发等）"
          % n_inherit)

    # ★★ 沿轴连续位移曲线：中轴（腰→胸→头）+ 双腿，共 3 条链。
    name2i = {b["name"]: i for i, b in enumerate(pmx.bones)}
    #   不能逐骨常量位移，因为那是「分段常量场」，而相邻骨的目标位相差极大：
    #     中轴实测 dy = 下半身 −0.751 / 腰 −0.860 / 上半身2 −0.799 / 首 +0.365
    #     → 上半身2 与 首 之间**跳变 1.16**，脖子上下被撕开、头悬空
    #       （渲染/游戏里就是用户报的「没有脖子 / 脖子太长」）。
    #     腿实测 dx = 大腿根 +0.065 / 膝盖 +0.417 / 脚踝 +0.761 / 脚尖 +0.917
    #     → 膝盖处被撕成两截。
    #   改成按**顶点自身 y** 在锚点间线性插值 → 位移场处处连续，
    #   几何只是被平滑地拉伸/压缩（源骨架与 HOI4 骨架的段长比例不同，这是必然代价）。
    #   ⚠ 锚点的目标 y 必须互不相同，否则插值会退化成「全部压到同一高度」
    #     （所以 `首` 不单列锚点，让它落在 上半身..頭 之间由插值自然给出位置）。
    CHAIN_JOINTS = (
        # 中轴
        (("センター", "Hip"), ("上半身", "back_mid"), ("頭", "head")),
        (("左足", "LeftUpLeg"), ("左ひざ", "LeftLeg"),
         ("左足首", "LeftFoot"), ("左つま先", "LeftToeBase")),
        (("右足", "RightUpLeg"), ("右ひざ", "RightLeg"),
         ("右足首", "RightFoot"), ("右つま先", "RightToeBase")),
    )
    leg_curves = []       # [(该链所有源骨索引集合, y锚点升序, disp升序)]
    for chain in CHAIN_JOINTS:
        tgts = set(HOI4_INDEX[t] for _sn, t in chain if t in HOI4_INDEX)
        idxs = set(i for i in range(len(hmap)) if hmap[i] in tgts and cw[i] > 0.0)
        ys, ds = [], []
        for sn, tn in chain:
            bi = name2i.get(sn)
            if bi is None or tn not in HOI4_INDEX:
                continue
            ys.append(bp_t[bi][1])
            ds.append(hpos[HOI4_INDEX[tn]] - bp_t[bi])
        if len(ys) < 2 or not idxs:
            P("  [警告] 部位链锚点不足（%s），该链退回逐骨常量位移" % chain[0][0][0])
            idxs = set()
        if idxs:
            o = np.argsort(ys)
            leg_curves.append((idxs, np.array(ys)[o], np.array(ds)[o]))
            P("  部位链 %-8s 锚点 y=%s  dy(y)=%s  覆盖源骨 %d"
              % (chain[0][0], np.array2string(np.array(ys)[o], precision=3),
                 np.array2string(np.array(ds)[o][:, 1], precision=3), len(idxs)))

    P("")
    if args.no_conform:
        P("★ 跳过绑定姿态对齐（--no-conform）：网格保持整体拟合后的位置。")
    else:
        delta = np.zeros_like(Vt)
        dom = np.full(pmx.vcount, -1, np.int64)
        for k in range(pmx.vcount):
            acc = np.zeros(3)
            tot = 0.0
            acc_o = np.zeros(3)
            tot_o = 0.0
            leg_tot = [0.0] * len(leg_curves)
            best, bw = -1, 0.0
            for b, w in zip(pmx.v_wbone[k], pmx.v_wweight[k]):
                # ⚠ b 是 MMD 骨索引（0..549），不是 HOI4 索引，别拿 nb 去卡
                #   未映射到 HOI4 骨的源骨（hmap<0）同样有 disp（父链继承得来），
                #   不能再跳过 —— 否则绑在它们上面的顶点会原地不动而与身体脱节。
                if w <= 1e-6 or not (0 <= b < n_b):
                    continue
                hit = False
                for li, (idxs, _y, _d) in enumerate(leg_curves):
                    if b in idxs:
                        leg_tot[li] += w
                        hit = True
                        break
                if not hit:
                    acc_o += w * disp[b]
                    tot_o += w
                if w > bw:
                    best, bw = hmap[b], w
            # 腿部：按 y 插值出的连续位移
            if tot_o > 0.0:
                acc += acc_o
                tot += tot_o
            for li, (_idxs, ys, ds) in enumerate(leg_curves):
                if leg_tot[li] <= 0.0:
                    continue
                yy = Vt[k, 1]
                acc += leg_tot[li] * np.array(
                    [np.interp(yy, ys, ds[:, j]) for j in range(3)])
                tot += leg_tot[li]
            if tot > 0.0:
                delta[k] = acc / tot
            dom[k] = best
        Vt = Vt + delta

        dm = np.linalg.norm(delta, axis=1)
        P("★ 绑定姿态对齐（bind conform）—— 把网格拉到 HOI4 骨架的 rest 姿态")
        P("    参与对齐的源骨 %d / %d；顶点位移 |d| 中位 %.4f  P99 %.4f  最大 %.4f"
          % (int(cw.sum()), len(cw), float(np.median(dm)),
             float(np.quantile(dm, 0.99)), float(dm.max())))
        P("    腿部几何 x 剖面（对齐后；骨架是 0.44 / 0.67 / 0.88 / 1.14）：")
        for h4 in ("LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
                   "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase"):
            sel = dom == HOI4_INDEX[h4]
            if sel.sum():
                c = Vt[sel].mean(0)
                P("      %-14s n=%6d  质心 (%7.3f,%7.3f,%7.3f)   骨架 x=%6.3f  差 %6.3f"
                  % (h4, int(sel.sum()), c[0], c[1], c[2], HOI4_REST[h4][0],
                     c[0] - HOI4_REST[h4][0]))
        P("    变换后顶点包围盒：")
        for ax, nm in enumerate("XYZ"):
            P("        %s: [%8.4f, %8.4f]  跨度 %7.4f"
              % (nm, Vt[:, ax].min(), Vt[:, ax].max(),
                 Vt[:, ax].max() - Vt[:, ax].min()))

    # ---------- 6) 组装每组 mesh
    meshes = []
    P("")
    P("生成 draw call：")
    for g in sorted(grp_faces):
        fl = grp_faces[g]
        # ★ 顶点去重必须连「所属材质」一起进 key（tri=None 分组）：
        #   grp_faces 里 triangle 是 (mi, a, b, c)，同一个 PMX 顶点可能被
        #   多个材质引用；若只按顶点号去重，后面的材质会复用前面材质的
        #   UV/前推量，整层就废了（实测：白目 的 UV 被并进别的层，
        #   只剩几个像素大、采样到 gutter 的黑色）。
        key_of = {}
        old = []
        tri = np.empty(len(fl) * 3, np.int32)
        mat_of = []
        for j, (mi, a, b, c) in enumerate(fl):
            for slot, x in enumerate((a, b, c)):
                k = (mi, x)
                idx = key_of.get(k)
                if idx is None:
                    idx = len(old)
                    key_of[k] = idx
                    old.append(x)
                    mat_of.append(mi)
                tri[3 * j + slot] = idx
        old = np.array(old, np.int64)

        pos = Vt[old]
        nrm = Nt[old]

        # 眼睛：整层沿视线方向（-Z，角色朝 -Z）前推，压过脸皮 颜/颜2。
        # 必须在这里做（而不是改 Vt）：PMX 顶点是全模型共用的，
        # 直接改 Vt 会把同一批顶点在其它材质里的位置一起挪走。
        n_push = 0
        for k in range(len(old)):
            d = eye_forward(pmx.materials[mat_of[k]]["name"])
            if d is None:
                continue
            pos[k, 2] -= d
            n_push += 1
        if n_push:
            P("    [%s] 眼球层前推顶点 %d 个" % (g, n_push))

        # UV：按所属材质重映射到图集
        uvs = np.zeros((len(old), 2), np.float64)
        for k in range(len(old)):
            mi = mat_of[k]
            grp = mat_group_of(pmx.materials[mi]["name"])
            atlas, place = atlases[grp]
            ti = pmx.materials[mi]["tex"]
            X, Y, cw, ch, tw, th = place[ti]
            AH, AW = atlas.shape[0], atlas.shape[1]
            su, sv = UV[old[k], 0], UV[old[k], 1]

            # PMX 会给接缝顶点的 uv 故意 +1（0.0416 表示 1.0416），
            # 目的只是让双线性采样不跨格渗色。取模即可复原真实图坐标。
            # 千万不要做「UV 盒子线性映射」——会被 1.0+小数 撑爆成一点。
            su = np.mod(su, 1.0)
            sv = np.mod(sv, 1.0)
            uvs[k] = ((X + GUTTER + su * tw) / AW,
                      (Y + GUTTER + sv * th) / AH)

        # 权重
        W = np.zeros((len(old), nb), np.float64)
        for k, ox in enumerate(old):
            wb = pmx.v_wbone[ox]
            ww = pmx.v_wweight[ox]
            for b, w in zip(wb, ww):
                if w > 1e-6 and 0 <= b < len(hmap):
                    W[k, hmap[b]] += w
        W[W < 1e-4] = 0.0
        order = np.argsort(-W, axis=1)[:, :4]
        ix4 = np.full((len(old), 4), -1, np.int32)
        w4 = np.zeros((len(old), 4), np.float64)
        for k in range(len(old)):
            sel = order[k]
            vals = W[k, sel]
            tot = vals.sum()
            if tot <= 0:
                ix4[k, 0] = HOI4_INDEX["Hip"]
                w4[k, 0] = 1.0
                continue
            vals = vals / tot
            j = 0
            for q in range(4):
                if vals[q] > 0:
                    ix4[k, j] = sel[q]
                    w4[k, j] = vals[q]
                    used_cnt[HOI4_ORDER[sel[q]]] += 1
                    j += 1

        ta = tangents(pos, nrm, uvs, tri)
        m = {
            "p": pos.astype(np.float32).ravel().tolist(),
            "n": nrm.astype(np.float32).ravel().tolist(),
            "ta": ta.astype(np.float32).ravel().tolist(),
            "u0": uvs.astype(np.float32).ravel().tolist(),
            "tri": tri.tolist(),
            "min": pos.min(0).astype(np.float32).tolist(),
            "max": pos.max(0).astype(np.float32).tolist(),
            "shader": "PdxMeshStandard",
            "diff": tex_file[g],
            "nrm": nonrm,
            "spec": nomat,
            "bones": 4,
            "ix": ix4.ravel().astype(np.int32).tolist(),
            "w": w4.ravel().astype(np.float32).tolist(),
            "_group": g,
            "_verts": len(old),
        }
        meshes.append(m)
        P("    %-6s 顶点 %7d 三角 %7d  Y:[%7.3f,%7.3f]  X:[%7.3f,%7.3f]  贴图 %s"
          % (g, len(old), len(fl), pos[:, 1].min(), pos[:, 1].max(),
             pos[:, 0].min(), pos[:, 0].max(), m["diff"]))

    # 每根骨骼影响顶点数
    P("")
    P("各 HOI4 骨骼受影响顶点数（全部 draw call 合计）：")
    for nm in HOI4_ORDER:
        P("    %-20s %8d" % (nm, used_cnt.get(nm, 0)))

    # ★ 防护：HOI4 原生步兵动画会把这些骨的 s 通道设为 0（= 整根骨缩没），
    #   挂在上面的几何在游戏里会彻底消失。实测统计见 scripts/report_anim_hidden_bones.txt
    #   （42 个 GER_infantry*.anim 里：mid_back_node 39 次、6 个 Hand_node 11~40 次）。
    HIDDEN_RISK = ("mid_back_node", "Left_Hand_node", "Left_Hand_node_2",
                   "Left_Hand_node_3", "Right_Hand_node", "Right_Hand_node_2",
                   "Right_Hand_node_3", "Right_Hand_node_4")
    bad = [(nm, used_cnt.get(nm, 0)) for nm in HIDDEN_RISK if used_cnt.get(nm, 0) > 0]
    P("")
    if bad:
        P("★★ 警告：以下骨骼在有动画里会被隐藏（s=0），绑上去的顶点会消失：")
        for nm, c in bad:
            P("      %-20s %8d 个顶点   <-- 请改挂到它的父骨上" % (nm, c))
    else:
        P("✔ 无顶点绑到「动画里会被隐藏」的骨上（检查了 %d 根）" % len(HIDDEN_RISK))

    # ---------- 7) skeleton 块：复用 PRC_infantry.mesh
    import pdx_data
    ref = pdx_data.read_meshfile(os.path.join(PRC_ZIP_DIR, "PRC_infantry.mesh"))
    ref_skel = None
    for obj in ref:
        for shape in obj:
            s2 = shape.find("skeleton")
            if s2 is not None:
                ref_skel = s2
    assert ref_skel is not None, "参考 mesh 里没找到 skeleton"
    bones = []
    for b in ref_skel:
        bones.append((b.tag, b.get("ix"), b.get("pa"), b.get("tx")))
    P("")
    P("skeleton 复用 PRC_infantry.mesh：%d 根骨（%s ... %s）"
      % (len(bones), bones[0][0], bones[-1][0]))

    # 交叉验证：参考骨架反推的 rest 位置 vs 我们的 HOI4_REST
    # 注意：Left_Hand_node 等骨骼在参考文件里 tx 是退化的（值 ~1e12），求逆会爆，
    #       这些骨直接从检查里排除。
    maxd = 0.0
    nbad = 0
    for nm, ix, pa, tx in bones:
        ta = np.array(tx, np.float64)
        if np.abs(ta).max() > 1e6:
            nbad += 1
            continue
        cols = ta.reshape(4, 3)
        Rm = np.column_stack([cols[0], cols[1], cols[2]])
        tm = cols[3]
        pos = -Rm.T @ tm
        if nm in HOI4_REST:
            maxd = max(maxd, float(np.linalg.norm(pos - np.array(HOI4_REST[nm]))))
    P("    与内置 HOI4_REST 的最大偏差 = %.5f（应 < 0.01；跳过 %d 根退化 tx 的骨）"
      % (maxd, nbad))

    # ---------- 8) 写 .mesh
    root = Xml.Element("File")
    root.set("pdxasset", [1, 0])
    obj = Xml.SubElement(root, "object")
    shape = Xml.SubElement(obj, "%s_infantryShape" % args.name)
    for m in meshes:
        me = Xml.SubElement(shape, "mesh")
        for k in ("p", "n", "ta", "u0", "tri"):
            me.set(k, m[k])
        ab = Xml.SubElement(me, "aabb")
        ab.set("min", m["min"])
        ab.set("max", m["max"])
        mt = Xml.SubElement(me, "material")
        mt.set("shader", m["shader"])
        mt.set("diff", m["diff"])
        mt.set("n", m["nrm"])
        mt.set("spec", m["spec"])
        sk = Xml.SubElement(me, "skin")
        sk.set("bones", [4])
        sk.set("ix", m["ix"])
        sk.set("w", m["w"])
    skel = Xml.SubElement(shape, "skeleton")
    for nm, ix, pa, tx in bones:
        b = Xml.SubElement(skel, nm)
        b.set("ix", ix)
        if pa is not None:
            b.set("pa", pa)
        b.set("tx", tx)

    mesh_path = fresh(os.path.join(args.outdir, "%s_infantry.mesh" % args.name))
    write_tree(mesh_path, root)
    P("")
    P("写出 %s（%d bytes）" % (mesh_path, os.path.getsize(mesh_path)))

    # ---------- 9) 写 DDS
    P("")
    P("写出贴图：")
    for g in sorted(atlases):
        atlas, _ = atlases[g]
        name = tex_file[g]
        p = os.path.join(args.outdir, name)
        has_alpha = bool((atlas[..., 3] < 250).any())
        fmt = "DXT5" if has_alpha else "DXT1"
        write_dds(p, atlas, fmt)
        P("    %-34s %5dx%-5d %s  %8d bytes (alpha=%s)"
          % (name, atlas.shape[1], atlas.shape[0], fmt, os.path.getsize(p), has_alpha))
        # 图集 PNG 便于目视
        Image.fromarray(atlas, "RGBA").save(
            fresh(os.path.join(args.outdir, "%s_%s_atlas.png" % (args.name.lower(), g))))

    # 4x4 平坦 spec / normal（参考原版做法：nospe 是 4x4 的 DXT5）
    flat = np.zeros((4, 4, 4), np.uint8)
    write_dds(os.path.join(args.outdir, nomat), flat, "DXT5")
    nrm = np.zeros((4, 4, 4), np.uint8)
    nrm[..., 0] = 128
    nrm[..., 1] = 128
    nrm[..., 2] = 255
    nrm[..., 3] = 255
    write_dds(os.path.join(args.outdir, nonrm), nrm, "DXT5")
    P("    %-34s    4x4   DXT5      (透明 spec)" % nomat)
    P("    %-34s    4x4   DXT5      (平坦 normal)" % nonrm)

    # ---------- 10) 回读自检
    P("")
    P("回读自检（用 pdx_data 解析刚写出的文件）：")
    chk = pdx_data.read_meshfile(mesh_path)
    nsh = 0
    ntri = 0
    nv = 0
    for o in chk:
        for sh in o:
            for mm in sh.findall("mesh"):
                nsh += 1
                nv += len(mm.get("p")) // 3
                ntri += len(mm.get("tri")) // 3
            if sh.find("skeleton") is not None:
                P("    skeleton 骨骼 %d 根" % len(sh.find("skeleton")))
    P("    mesh 节点 %d，合计顶点 %d，三角 %d" % (nsh, nv, ntri))

    rep = fresh(os.path.join(args.outdir, "build_report.txt"))
    open(rep, "w", encoding="utf-8").write("\n".join(log))
    P("")
    P("报告：%s" % rep)
    return mesh_path


if __name__ == "__main__":
    main()
