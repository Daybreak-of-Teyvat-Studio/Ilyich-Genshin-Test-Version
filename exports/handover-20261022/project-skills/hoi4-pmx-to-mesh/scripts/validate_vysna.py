# -*- coding: utf-8 -*-
"""校验 Vysna 模型在 MOD 里的定义自洽性与跨文件引用完整性。

注：本项目已把 Vysna 的定义并入 `DOT_All_Entity.gfx` / `DOT_All_Entity.asset`
（不是独立的 DOT_Vysna.gfx/.asset），下面的路径按实际生效文件写。

检查项：
  1) 括号配平
  2) gfx 里 pdxmesh 的 file 是否存在
  3) asset 里引用的 pdxmesh 是否在 gfx（或 MOD 其它 gfx）里定义
  4) asset 各 state 引用的 animation id 是否在该 pdxmesh 的 animation 列表里
  5) asset 各 attach 的挂点骨名是否真实存在于 mesh 的 skeleton
  6) asset 各 attach 引用的实体名是否在 MOD 内已定义
  7) ★ mesh 里不能有顶点绑到「动画里会被 s=0 隐藏」的骨上
     （否则那些几何会在游戏里消失；见 scripts/anim_hidden_bones.py 的统计）
  8) ★ attach 挂点如果落在「会被隐藏的骨」上，是**原版设计」（= 该装备会被收起），
     给出提示而不报错
"""
import os
import re
import sys

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
from pdx_data import read_meshfile  # noqa: E402

MOD = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
       r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version")
GFX = os.path.join(MOD, r"gfx\entities\DOT_All_Entity.gfx")
ASSET = os.path.join(MOD, r"gfx\entities\DOT_All_Entity.asset")
MESH = os.path.join(MOD, r"gfx\models\units\DOT_Vysna\Vysna_infantry.mesh")

GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"

# 42 个 GER_infantry*.anim 里被 s=0 隐藏的骨（次数见注释）
HIDDEN_RISK = {
    "mid_back_node": 39, "Left_Hand_node": 31, "Left_Hand_node_2": 40,
    "Left_Hand_node_3": 11, "Right_Hand_node": 15, "Right_Hand_node_2": 40,
    "Right_Hand_node_3": 40, "Right_Hand_node_4": 40,
}

out = []
ok = True


def bad(msg):
    global ok
    ok = False
    out.append("  [FAIL] " + msg)


def good(msg):
    out.append("  [ ok ] " + msg)


def strip_comments(s):
    return re.sub(r"#[^\n]*", "", s)


def blocks(src, keyword):
    """按「花括号配平」提取所有 `keyword = { ... }` 块（缩进无关）。
    ⚠ 不要用 `\\n\\t\\}` 这类写死缩进的正则 —— 不同文件的缩进不一样，
       DOT_All_Entity.gfx 用 4 空格，写死 tab 会一个都匹配不到。"""
    out_b = []
    for m in re.finditer(re.escape(keyword) + r"\s*=\s*\{", src):
        i = m.end() - 1
        depth = 0
        for j in range(i, len(src)):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    out_b.append(src[i + 1:j])
                    break
    return out_b


def brace_balance(path, label):
    s = strip_comments(open(path, encoding="utf-8").read())
    depth = 0
    for ch in s:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                bad("%s 括号提前闭合" % label)
                return
    if depth == 0:
        good("%s 括号配平（深度归零）" % label)
    else:
        bad("%s 括号不配平，剩余深度 %d" % (label, depth))


out.append("=" * 76)
out.append("1) 语法：括号配平")
out.append("=" * 76)
brace_balance(GFX, os.path.basename(GFX))
brace_balance(ASSET, os.path.basename(ASSET))

# ---------- 解析 gfx ----------
out.append("")
out.append("=" * 76)
out.append("2) gfx：pdxmesh 定义与文件存在性")
out.append("=" * 76)
gsrc = open(GFX, encoding="utf-8").read()
pm_blocks = blocks(gsrc, "pdxmesh")
gfx_mesh = {}          # pdxmesh 名 -> animation id 集合
for b in pm_blocks:
    m = re.search(r'name\s*=\s*"([^"]+)"', b)
    if not m:
        continue
    nm = m.group(1)
    f = re.search(r'file\s*=\s*"([^"]+)"', b)
    anims = set(re.findall(r'animation\s*=\s*\{\s*id\s*=\s*"([^"]+)"', b))
    gfx_mesh[nm] = anims
    if f:
        fp = os.path.join(MOD, f.group(1).replace("/", os.sep))
        ours = "Vysna" in nm
        if os.path.isfile(fp):
            good('pdxmesh "%s" -> file 存在 (%d B)，动画 %d 组'
                 % (nm, os.path.getsize(fp), len(anims)))
        elif ours:
            bad('pdxmesh "%s" -> file 不存在: %s' % (nm, f.group(1)))
        else:
            out.append('  [info] pdxmesh "%s" -> file 不存在: %s'
                       '（非 Vysna，MOD 既有问题，不在本次范围）' % (nm, f.group(1)))
    elif "Vysna" in nm:
        bad('pdxmesh "%s" 缺 file' % nm)

# ---------- 全 MOD + 游戏本体已定义实体名 ----------
# ⚠ attach 可以指向**原版本体**的实体（例：cigarette_entity / lighter_entity 在
#   ../../Hearts of Iron IV/gfx/entities/units_infantry.asset），只扫 MOD 会误报。
defined = set()
for base, dirs in ((MOD, ["gfx"]), (GAME, [os.path.join("gfx", "entities")])):
    for sub in dirs:
        for root, _, files in os.walk(os.path.join(base, sub)):
            for fn in files:
                if not fn.lower().endswith((".asset", ".gfx")):
                    continue
                try:
                    t = open(os.path.join(root, fn), encoding="utf-8",
                             errors="ignore").read()
                except OSError:
                    continue
                for m in re.finditer(r'name\s*=\s*"([^"]+)"', t):
                    defined.add(m.group(1))
out.append("")
out.append("  （MOD + 游戏本体共声明 %d 个名字，用于跨文件实体引用检查）" % len(defined))

# ---------- 读 mesh：骨架骨名 + 顺序（slot 索引） ----------
mroot = read_meshfile(MESH)
MESH_ORDER = []
MESH_BONES = set()
for sk in mroot.iter("skeleton"):
    for n in sk:
        MESH_ORDER.append(n.tag)
        MESH_BONES.add(n.tag)
out.append("  （mesh 骨架 %d 根骨）" % len(MESH_ORDER))

# ---------- 解析 asset ----------
out.append("")
out.append("=" * 76)
out.append("3) asset：实体定义 / 动画 id / 挂点骨名 / 引用实体")
out.append("=" * 76)
asrc = open(ASSET, encoding="utf-8").read()
ent_blocks = re.split(r"\nentity\s*=\s*\{", asrc)[1:]
for b in ent_blocks:
    mname = re.search(r'name\s*=\s*"([^"]+)"', b)
    if not mname:
        continue
    nm = mname.group(1)
    # 只校验与 Vysna 相关的实体（Vysna 本体 + 它的 clone）
    if "Vysna" not in nm and 'clone = "Vysna_infantry_entity"' not in b:
        continue
    pmesh = re.search(r'pdxmesh\s*=\s*"([^"]+)"', b)
    out.append("")
    out.append("  ── entity \"%s\"" % nm)
    if not pmesh:
        if 'clone = "Vysna_infantry_entity"' in b:
            good('clone 自 "Vysna_infantry_entity"（继承全部定义）')
            continue
        bad("缺 pdxmesh")
        continue
    pname = pmesh.group(1)
    if pname not in gfx_mesh:
        bad('pdxmesh "%s" 未在 %s 中定义' % (pname, os.path.basename(GFX)))
        continue
    good('pdxmesh = "%s"（已定义）' % pname)
    anim_ids = gfx_mesh[pname]

    # state 引用的 animation
    used = set(re.findall(r'animation\s*=\s*"([^"]+)"', b))
    missing = sorted(used - anim_ids)
    if missing:
        bad("state 引用了未定义的 animation：%s" % missing)
    else:
        good("state 引用的 %d 个 animation 全部有定义" % len(used))

    # getter for propagate_state
    # ⚠ propagate_state = { <名> = <状态> } 的 <名> 既可能是 attach 名，也可能是
    #   状态机名（如原版原样抄来的 `infantry`），**不能当失败**，只作提示。
    prop = set(re.findall(r'propagate_state\s*=\s*\{\s*(\w+)\s*=', b))
    attaches = dict(re.findall(r'attach\s*=\s*\{\s*name\s*=\s*"([^"]+)"\s+(\w+)\s*=', b))
    if prop - set(attaches):
        out.append("        （提示）propagate_state 引用的名字不在 attach 列表：%s"
                   "（原版即如此，非错误）" % sorted(prop - set(attaches)))
    else:
        good("propagate_state 指向的 attach 均存在：%s" % (sorted(prop) or "无"))

    scale = re.search(r"scale\s*=\s*([0-9.]+)", b)
    good("scale = %s" % (scale.group(1) if scale else "未设（默认 1.0）"))

    # attach 目标实体
    bad_refs = []
    for aname, akey in sorted(attaches.items()):
        tgt = re.search(r'attach\s*=\s*\{\s*name\s*=\s*"%s"\s+%s\s*=\s*"([^"]+)"'
                        % (re.escape(aname), re.escape(akey)), b)
        if tgt and tgt.group(1) not in defined:
            bad_refs.append("%s(%s) -> %s" % (aname, akey, tgt.group(1)))
    if bad_refs:
        bad("attach 的目标实体未找到：%s" % bad_refs)
    else:
        good("attach 的 %d 个目标实体均在 MOD 中已定义" % len(attaches))

    # 挂点骨名对照 mesh skeleton
    anames = set(attaches.values())
    unknown = sorted(anames - MESH_BONES)
    if unknown:
        bad("attach 挂点骨名不在 mesh 骨架中：%s" % unknown)
    else:
        good("attach 挂点骨名全部存在于 mesh 骨架（%s）" % ", ".join(sorted(anames)))

    # 挂点落在「会被隐藏的骨」上是原版设计（= 该装备在特定动画里被收起）
    hid = sorted(a for a in anames if a in HIDDEN_RISK)
    if hid:
        out.append("        （提示）以下挂点位于会被 s=0 隐藏的骨上，属原版"
                   "\"收起该装备\"的设计：%s" % ", ".join(hid))

# ---------- 4) mesh 侧：不能有顶点绑到会被隐藏的骨 ----------
out.append("")
out.append("=" * 76)
out.append("4) mesh：是否有顶点绑到「动画里会被 s=0 隐藏」的骨")
out.append("=" * 76)
risk_hits = {}
for m in mroot.iter("mesh"):
    if not m.get("p"):
        continue
    sk = m.find("skin")
    if sk is None or not sk.get("ix"):
        continue
    ix = set(int(v) for v in sk.get("ix"))
    for gi in ix:
        if 0 <= gi < len(MESH_ORDER):
            bn = MESH_ORDER[gi]
            if bn in HIDDEN_RISK:
                risk_hits[bn] = risk_hits.get(bn, 0) + 1
out.append("  对 %d 根骨做了检查（42 个 GER_infantry*.anim 的隐藏统计）" % len(HIDDEN_RISK))
for bn, n in sorted(HIDDEN_RISK.items(), key=lambda kv: -kv[1]):
    out.append("    %-22s 被隐藏 %2d/42 个动画   mesh 引用 %s"
               % (bn, n, ("★ %d 个 mesh 节点" % risk_hits[bn]) if bn in risk_hits else "无"))
if risk_hits:
    bad("有顶点绑到会被隐藏的骨上（那些几何会在游戏里消失）：%s" % sorted(risk_hits))
else:
    good("没有任何顶点绑到会被隐藏的骨上 —— 所有几何都会在所有动画里显示")

out.append("")
out.append("=" * 76)
out.append(("总判定：全部通过 ✔" if ok else "总判定：存在失败项 ✘"))
out.append("=" * 76)

txt = "\n".join(out)
print(txt)
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_vysna_validate")
path = base + ".txt"
i = 2
while os.path.exists(path):
    path = "%s_%d.txt" % (base, i)
    i += 1
with open(path, "w", encoding="utf-8") as f:
    f.write(txt + "\n")
print("-> %s" % path)
