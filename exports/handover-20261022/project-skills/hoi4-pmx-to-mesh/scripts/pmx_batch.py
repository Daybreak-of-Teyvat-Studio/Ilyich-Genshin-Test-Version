# -*- coding: utf-8 -*-
"""批量：原神系 MMD PMX -> HOI4 .mesh

对 .backup 里的 心海/妮露/少女/茜特菈莉 各跑一遍 vysna_build 的管线，
其中：
  * SRC 指到各模型自己的目录
  * EXCLUDE_KEYS 追加「自动检测出的叠加层」
  * 自动检测 = ①贴图采样近全透明 ②与更早材质几何重合且透明（MMD 叠层）

用法: python pmx_batch.py [模型名...]   （不给参数=全部）
"""
import os
import sys
import collections

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import vysna_build as VB                      # noqa: E402
from pmx_parse import PMX                     # noqa: E402

WORK = r"C:\Users\XIANGZIYUAN\vysna_work"
OUT_ROOT = os.path.join(HERE, "..", "models_out")

# (工作目录名, PMX 文件名, 输出名/实体前缀, 精确剔除的材质名)
# ★ 实测（eye_probe2.py + 逐模型渲染验证）：
#   三家的「目」都是 MMD 的独立眼睛层，质量远好于脸皮上画的那对：
#     Kokomi 的 目 用 髮.png 的一块  -> 保留后得到正确的蓝紫色眼睛
#     Nilou  的 目 用 髮.png 的一块  -> 保留后得到正确的青蓝色眼睛（原神设定色）
#     Columbina 的 目 用 目.png 整图 -> 保留
#     Citlali 的眼睛在 目2（目1.png）里，而她另有一个 目 指向 体.png 的布料
#             -> 必须精确剔 目，否则那块布料会盖在脸上
#   Kokomi 的 手 也必须精确剔：子串匹配会连带 手套/手珍珠，导致整只手消失
#   子串匹配会把 目2 一起误伤，所以走 EXCLUDE_EXACT 精确名。
MODELS = [
    ("心海",     "珊瑚宫心海.pmx", "Kokomi",    ["手"]),
    ("妮露",     "妮露.pmx",       "Nilou",     []),
    ("少女",     "少女.pmx",       "Columbina", []),
    ("茜特菈莉", "茜特拉莉.pmx",   "Citlali",   ["目"]),
]

# 绝不自动剔除的名字（眼睛是唯一的完整眼层）
NEVER = ("目",)

# 基线剔除表：薇斯纳的 EXCLUDE_KEYS 里 结晶/头饰 是「那个模型」的专属需求，
# 这四个角色要保留头饰（Columbina 的黑纱、Citlali 的帽饰都是角色标志）。
NEVER_DROP = ("结晶", "头饰")
BASE_EXCLUDE = [k for k in VB.EXCLUDE_KEYS if k not in NEVER_DROP]

rep = []
DRY = False          # --dry：只做自动分析，不构建


def tex_of(pmx, src, ti, cache):
    if ti not in cache:
        p = pmx.textures[ti].replace("\\", os.sep).replace("/", os.sep)
        im = Image.open(os.path.join(src, p)).convert("RGBA")
        cache[ti] = np.asarray(im, np.uint8)
    return cache[ti]


def analyze(pmx, src, tag):
    """返回 (应剔除的材质名列表, 报告行)。"""
    cache = {}
    VP = np.asarray(pmx.v_pos, np.float64)
    VUV = np.asarray(pmx.v_uv, np.float64)
    info = []            # (idx, name, n_tri, centroid_set, alpha_zero_pct, alpha_op_pct)
    acc = 0
    L = []
    L.append("")
    L.append("=" * 108)
    L.append("【%s】材质 %d 个" % (tag, len(pmx.materials)))
    L.append("%-16s %6s %-30s %8s %8s %8s"
             % ("材质", "三角", "贴图", "全透明%", "半透明%", "不透明%"))
    L.append("-" * 108)
    for mi, mt in enumerate(pmx.materials):
        nm = mt["name"]
        n_tri = mt["face_count"] // 3
        st = acc
        acc += mt["face_count"]
        ti = mt["tex"]
        z = m = o = -1.0
        cen = set()
        if 0 <= ti < len(pmx.textures):
            a = tex_of(pmx, src, ti, cache)
            H, W = a.shape[:2]
            vidx = []
            for k in range(st, st + mt["face_count"], 3):
                f0, f1, f2 = pmx.faces[k], pmx.faces[k + 1], pmx.faces[k + 2]
                vidx.extend((f0, f1, f2))
                c = (VP[f0] + VP[f1] + VP[f2]) / 3.0
                cen.add((round(float(c[0]), 3), round(float(c[1]), 3),
                         round(float(c[2]), 3)))
            vidx = np.array(sorted(set(vidx)), np.int64)
            uv = VUV[vidx]
            x = np.clip((np.mod(uv[:, 0], 1.0) * W).astype(np.int64), 0, W - 1)
            y = np.clip((np.mod(uv[:, 1], 1.0) * H).astype(np.int64), 0, H - 1)
            al = a[y, x, 3].astype(np.float64)
            z = float((al < 8).mean() * 100)
            m = float(((al >= 8) & (al < 248)).mean() * 100)
            o = float((al >= 248).mean() * 100)
            texn = pmx.textures[ti].replace("\\", "/")[-28:]
        else:
            texn = "(无)"
        L.append("%-16s %6d %-30s %8.1f %8.1f %8.1f"
                 % (nm, n_tri, texn, z, m, o))
        info.append((mi, nm, n_tri, cen, z, o))

    drop = []
    L.append("")
    L.append("自动判定：")
    for i, (mi, nm, n_tri, cen, z, o) in enumerate(info):
        if z < 0 or not cen:
            continue
        if any(k in nm for k in NEVER):
            continue
        # ① 整层几乎不可见
        if z >= 95.0:
            drop.append(nm)
            L.append("    %-16s 全透明 %.1f%% -> 剔除（整层不可见）" % (nm, z))
            continue
        # ② 与「更早绘制」的材质几何重合 + 大面积透明 = MMD 叠加层
        best, bn = 0.0, None
        for nm2, cen2, z2, o2 in [(x[1], x[3], x[4], x[5]) for x in info[:i]]:
            if not cen2:
                continue
            inter = len(cen & cen2)
            if not inter:
                continue
            r = inter / min(len(cen), len(cen2))
            if r > best:
                best, bn = r, nm2
        if best >= 0.5 and z >= 70.0:
            drop.append(nm)
            L.append("    %-16s 与 %-14s 重合 %.0f%% 且全透明 %.1f%% -> 剔除（叠加层）"
                     % (nm, bn, best * 100, z))
    if not drop:
        L.append("    （无）")
    return drop, L


def run_one(dirname, pmxfile, name, exact=None):
    src = os.path.join(WORK, dirname)
    pmx = os.path.join(src, pmxfile)
    if not os.path.isfile(pmx):
        rep.append("!! 找不到 %s" % pmx)
        return
    outdir = os.path.join(OUT_ROOT, name)
    p = PMX(pmx)
    drop, L = analyze(p, src, name)
    rep.extend(L)
    if DRY:
        rep.append("    (dry-run，跳过构建)")
        return

    # patch 模块级配置
    VB.SRC = src
    VB.EXCLUDE_EXACT = set(exact or [])
    # ★ 走精确名的材质绝不能再进子串表，否则 "手" 会把 手套/手珍珠 一起吃掉
    exset = set(exact or [])
    VB.EXCLUDE_KEYS = BASE_EXCLUDE + [d for d in drop
                                      if d not in BASE_EXCLUDE and d not in exset]
    rep.append("    最终剔除清单: %s" % VB.EXCLUDE_KEYS)

    sys.argv = ["vysna_build.py", "--pmx", pmx, "--outdir", outdir,
                "--name", name]
    VB.main()
    rep.append("    -> 产物 %s" % outdir)


if __name__ == "__main__":
    DRY = "--dry" in sys.argv
    want = [a for a in sys.argv[1:] if not a.startswith("--")]
    for d, f, n, ex in MODELS:
        if want and n not in want and d not in want:
            continue
        rep.append("")
        rep.append("#" * 108)
        rep.append("### %s  ->  %s" % (d, n))
        rep.append("#" * 108)
        try:
            run_one(d, f, n, ex)
        except Exception as e:
            import traceback
            rep.append("!! 失败: %s" % e)
            rep.append(traceback.format_exc())
    rp = os.path.join(HERE, "report_batch_build.txt")
    open(rp, "w", encoding="utf-8").write("\n".join(rep))
    print("\n".join(rep[-60:]))
    print("\n-> " + rp)
