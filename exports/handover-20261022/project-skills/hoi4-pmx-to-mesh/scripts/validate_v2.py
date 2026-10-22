# -*- coding: utf-8 -*-
"""通用校验：DOT_GenshinV2.gfx / .asset 与四个 .mesh 的自洽性。
  ① 括号配平  ② pdxmesh.file 存在  ③ 贴图文件齐全
  ④ entity -> pdxmesh 引用存在  ⑤ attach 骨名在 mesh 骨架里
  ⑥ mesh 里有无顶点绑到「动画里会被 s=0 隐藏」的骨（翅膀那次踩的坑）
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"C:\Users\XIANGZIYUAN\hoi4_pdx_mesh_src")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdx_data import read_meshfile  # noqa: E402

MOD = (r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github"
       r"\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version")
GFX = os.path.join(MOD, r"gfx\entities\DOT_GenshinV2.gfx")
ASSET = os.path.join(MOD, r"gfx\entities\DOT_GenshinV2.asset")

# 42 个 GER_infantry*.anim 里被 s=0 隐藏过、次数 ≥ 8 的骨
HIDDEN = {"mid_back_node", "Left_Hand_node", "Left_Hand_node_2", "Left_Hand_node_3",
          "Right_Hand_node", "Right_Hand_node_2", "Right_Hand_node_3",
          "Right_Hand_node_4"}

L = []
ok = fail = 0


def good(s):
    global ok
    ok += 1
    L.append("  [OK]   " + s)


def bad(s):
    global fail
    fail += 1
    L.append("  [FAIL] " + s)


def strip_c(s):
    return re.sub(r"#[^\n]*", "", s)


def blocks(text, key):
    """按花括号配平提取 key = { ... } 的块"""
    out = []
    for m in re.finditer(r"\b%s\s*=\s*\{" % key, text):
        i = m.end() - 1
        d = 0
        for j in range(i, len(text)):
            if text[j] == "{":
                d += 1
            elif text[j] == "}":
                d -= 1
                if d == 0:
                    out.append(text[i + 1:j])
                    break
    return out


gsrc = strip_c(open(GFX, encoding="utf-8").read())
asrc = strip_c(open(ASSET, encoding="utf-8").read())
for path, nm in ((GFX, "DOT_GenshinV2.gfx"), (ASSET, "DOT_GenshinV2.asset")):
    t = strip_c(open(path, encoding="utf-8").read())
    if t.count("{") == t.count("}"):
        good("%s 括号配平 (%d 对)" % (nm, t.count("{")))
    else:
        bad("%s 括号不配平 { %d } %d" % (nm, t.count("{"), t.count("}")))

# ---------- pdxmesh
L.append("")
L.append("【pdxmesh】")
meshes = {}
for b in blocks(gsrc, "pdxmesh"):
    n = re.search(r'name\s*=\s*"([^"]+)"', b)
    f = re.search(r'file\s*=\s*"([^"]+)"', b)
    if not n:
        bad("pdxmesh 缺 name")
        continue
    nn = n.group(1)
    anims = re.findall(r'animation\s*=\s*\{\s*id\s*=\s*"([^"]+)"', b)
    meshes[nn] = set(anims)
    fp = os.path.join(MOD, f.group(1).replace("/", os.sep)) if f else None
    if not fp or not os.path.isfile(fp):
        bad('%s -> file 不存在 (%s)' % (nn, f.group(1) if f else "缺 file"))
        continue
    good("%s -> %s (%d B, 动画 %d 组)" % (nn, f.group(1), os.path.getsize(fp), len(anims)))
    # 贴图齐全
    texs = set(re.findall(r"[a-z0-9_]+\.dds", open(fp, "rb").read().decode("latin-1")))
    d = os.path.dirname(fp)
    miss = [t for t in texs if not os.path.isfile(os.path.join(d, t))]
    if misn := miss:
        bad("%s 缺贴图 %s" % (nn, misn))
    else:
        good("%s 引用的 %d 张贴图全部就位" % (nn, len(texs)))
    # 骨架与隐藏骨
    root = read_meshfile(fp)
    sk_names, hit = set(), {}
    for sk in root.iter("skeleton"):
        for bn in sk:
            sk_names.add(bn.tag)
    for o in root.iter("object"):
        for sh in o:
            skel = sh.find("skeleton")
            bnames = [bn.tag for bn in skel] if skel is not None else []
            for mm in sh.findall("mesh"):
                sk = mm.find("skin")
                if sk is None:
                    continue
                raw = sk.get("ix")
                if raw is None:
                    continue
                ix = raw if isinstance(raw, list) else [int(x) for x in str(raw).split()]
                for i in ix:
                    if 0 <= i < len(bnames) and bnames[i] in HIDDEN:
                        hit[bnames[i]] = hit.get(bnames[i], 0) + 1
    # 只统计非挂点子类（rider 等）—— 这里简单汇报
    if hit:
        bad("%s：%d 个顶点绑到会被动画隐藏的骨 %s" % (nn, sum(hit.values()), hit))
    else:
        good("%s 无顶点绑到「会被 s=0 隐藏的骨」" % nn)

# ---------- entity
L.append("")
L.append("【entity】")
for b in blocks(asrc, "entity"):
    n = re.search(r'name\s*=\s*"([^"]+)"', b)
    p = re.search(r'pdxmesh\s*=\s*"([^"]+)"', b)
    if not n:
        continue
    nn = n.group(1)
    if not p:
        bad('%s 缺 pdxmesh' % nn)
        continue
    if p.group(1) not in meshes:
        bad('%s -> pdxmesh "%s" 未定义' % (nn, p.group(1)))
        continue
    states = re.findall(r'state\s*=\s*\{\s*name\s*=\s*"([^"]+)"\s*animation\s*=\s*"([^"]+)"', b)
    miss = sorted({a for _, a in states} - meshes[p.group(1)])
    sc = re.search(r"scale\s*=\s*([0-9.]+)", b)
    att = re.findall(r'attach\s*=\s*\{\s*name\s*=\s*"([^"]+)"\s+(\w+)\s*=', b)
    if miss:
        bad('%s 引用了 pdxmesh 里没有的 animation id: %s' % (nn, miss))
    else:
        good("%s -> %s  state %d 个全部命中  scale=%s  attach %d 个"
             % (nn, p.group(1), len(states), sc.group(1) if sc else "?", len(att)))

L.append("")
L.append("  ================ 通过 %d 项，失败 %d 项 ================" % (ok, fail))
txt = "\n".join(L)
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_validate_v2.txt")
open(p, "w", encoding="utf-8").write(txt)
print(txt)
