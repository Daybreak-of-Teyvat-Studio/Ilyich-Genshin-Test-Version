#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""带断言与试运行的 HOI4 MOD 批量修复器 —— 编辑引擎模板。

核心思想：**绝不只靠行号**。行号会因增删漂移，所以每次改动都做
「行号 + 该行必须包含的原文」双重断言；命中才改，不命中记为 MISS 并打印实际内容。

用法:
    python fixer_template.py            # DRY：只打印将做的改动
    python fixer_template.py --apply    # 实际写入

把下面 FIXES 段落改成你自己的改动即可。所有写操作都会自动在行尾留 `# FIXED:` 标记（可选）。
"""
import io, os, re, sys

MOD = r"<在此填 MOD 根目录>"
DRY = "--apply" not in sys.argv
LOG = []

def rec(kind, where, old="", new=""):
    LOG.append((kind, where, str(old).strip()[:110], str(new).strip()[:110]))

def readlines(rel):
    return io.open(os.path.join(MOD, rel), "r", encoding="utf-8", errors="replace", newline="").read().split("\n")

def writelines(rel, L):
    if not DRY:
        io.open(os.path.join(MOD, rel), "w", encoding="utf-8", newline="").write("\n".join(L))

def text_of(rel):
    return io.open(os.path.join(MOD, rel), "r", encoding="utf-8", errors="replace", newline="").read()

def write_text(rel, t):
    if not DRY:
        io.open(os.path.join(MOD, rel), "w", encoding="utf-8", newline="").write(t)

def edit_line(rel, ln, oldsub, newsub, label=""):
    """第 ln 行（1 起）必须包含 oldsub，替换为 newsub。"""
    L = readlines(rel)
    if ln - 1 >= len(L) or oldsub not in L[ln - 1]:
        actual = L[ln - 1].strip()[:80] if ln - 1 < len(L) else "<EOF>"
        rec("MISS", "%s:%d" % (rel, ln), label or oldsub, "实际: " + actual)
        return
    L[ln - 1] = L[ln - 1].replace(oldsub, newsub)
    rec("FIX", "%s:%d" % (rel, ln), label or oldsub, newsub)
    writelines(rel, L)

def scrub_file(rel, pat, repl, label="", expect=None, keep_comment=""):
    """整文件正则替换（自动带 re.M）。expect 用于断言命中数量，不符会 WARN。"""
    t = text_of(rel)
    t2, n = re.subn(pat, repl, t, flags=re.M)
    if not n:
        rec("MISS", rel, label or pat)
    else:
        if keep_comment and "# FIXED" not in repl:
            t2 = t2
        rec("FIX", rel + " x%d" % n, label or pat, repl)
        if expect is not None and n != expect:
            rec("WARN", rel, "预期 %d 处，实际 %d 处" % (expect, n))
        write_text(rel, t2)
    return n

def insert_lines(rel, after_ln, new_lines, label=""):
    """在 after_ln 行之后插入若干行（1 起；after_ln=0 表示插到文件开头）。"""
    L = readlines(rel)
    for k, s in enumerate(new_lines):
        L.insert(after_ln + k, s)
    rec("FIX", "%s:%d" % (rel, after_ln), label or "insert", " | ".join(new_lines)[:110])
    writelines(rel, L)

def delete_lines(rel, start_ln, end_ln, label=""):
    L = readlines(rel)
    rec("FIX", "%s:%d-%d" % (rel, start_ln, end_ln), label or "delete", "<%d 行>" % (end_ln - start_ln + 1))
    del L[start_ln - 1:end_ln]
    writelines(rel, L)

def top_blocks(text):
    """解析 depth-0 的 (key, start_idx, end_idx)，忽略 # 注释里的花括号。
    用于把原版缺失的块回填进 MOD 的同名覆盖文件。"""
    lines = text.split("\n")
    blocks, cur, depth = [], None, 0
    for i, ln in enumerate(lines):
        c = ln.split("#")[0]
        if cur is None:
            m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", c)
            if m and depth == 0:
                cur = (m.group(1), i)
                depth = c.count("{") - c.count("}")
                if depth <= 0:
                    blocks.append((cur[0], cur[1], i)); cur, depth = None, 0
                continue
        else:
            depth += c.count("{") - c.count("}")
            if depth <= 0:
                blocks.append((cur[0], cur[1], i)); cur, depth = None, 0
    return blocks, lines

def backfill_missing_blocks(mod_rel, vanilla_abs, label=""):
    """把原版文件里 MOD 缺失的顶层块追加到 MOD 同名文件末尾。
    专治「残缺同名副本静默删掉原版定义」（典型报错：Unknown category）。"""
    mt = text_of(mod_rel)
    vt = io.open(vanilla_abs, "r", encoding="utf-8", errors="replace").read()
    vb, vlines = top_blocks(vt)
    mb, _ = top_blocks(mt)
    mk = {k for k, _, _ in mb}
    missing = [b for b in vb if b[0] not in mk]
    rec("INFO", mod_rel, "原版顶层 %d / MOD %d / 缺失 %d" % (len(vb), len(mb), len(missing)),
        ", ".join(b[0] for b in missing))
    if missing:
        add = ["", "", "# ===== FIXED: 以下定义自原版回填（同名残缺副本曾导致其丢失）====="]
        for k, a, b in missing:
            add += vlines[a:b + 1]
            add.append("")
        write_text(mod_rel, mt.rstrip("\n") + "\n" + "\n".join(add))

# =====================================================================
# FIXES: 在此写你的改动。示例（改前务必先 dry-run 到 0 MISS）：
#
# edit_line(r"events\Some_event.txt", 123, "has_country_leader = Alice",
#           "has_country_leader = { character = Alice }", "必须带块")
# scrub_file(r"common\decisions\X.txt", r"^\s*IF\s*=\s*\{", "if = {", "统一小写(非必须)")
# scrub_file(r"common\units\X.txt", r"defence = ", "defense = ", "单位属性")
# =====================================================================

print("=" * 100)
print("变更清单 (DRY=%s, 共 %d 条)" % (DRY, len(LOG)))
for kind, where, old, new in LOG:
    print(f"[{kind}] {where}")
    print(f"       old: {old}")
    if new:
        print(f"       new: {new}")
print()
print("MISS 数:", sum(1 for k, *_ in LOG if k == "MISS"))
if sum(1 for k, *_ in LOG if k == "MISS"):
    print(">>> 有未命中项，请先修正 FIXES 再 --apply")
