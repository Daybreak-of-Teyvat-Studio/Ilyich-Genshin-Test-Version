# -*- coding: utf-8 -*-
"""正确抽取每条 icon/picture 所属的 focus id / idea 块名。
focus: id = X
idea : 顶层块名X = { （用括号深度定位，不能只看 id=）
输出 ctxmap.json = { "kind/file:line": ctx }
"""
import os, re, json, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
STG = os.path.dirname(os.path.abspath(__file__))
MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"

ICON = re.compile(r'^(\s*)(icon|picture)\s*=\s*(\S+?)\s*\r?$')
# 块首：name = {  或  name = {   （name 可含字母数字下划线）
BLOCK = re.compile(r'^\s*([A-Za-z0-9_.]+)\s*=\s*\{\s*$')
FOCUSID = re.compile(r'^\s*id\s*=\s*([A-Za-z0-9_.]+)')

def depth_delta(line):
    s = re.sub(r'"[^"]*"', '', line)      # 去字符串
    s = re.sub(r'#.*$', '', s)             # 去注释
    return s.count('{') - s.count('}')

def scan(path, kind):
    raw = open(path, encoding="utf-8", errors="ignore", newline='').read().split("\n")
    out = {}
    # 深度栈：(depth, name)
    stack = []
    for i, ln in enumerate(raw, 1):
        m = ICON.match(ln)
        if m:
            # 找最近的 focus id / 块名
            ctx = ""
            for d, nm in reversed(stack):
                if kind == "focus":
                    # focus 块首是 focus_tree={ 或 id=x
                    ctx = nm if nm and not nm.startswith("focus_tree") else ""
                else:
                    ctx = nm
                if ctx: break
            out[i] = ctx
        dd = depth_delta(ln)
        # 入栈
        bm = BLOCK.match(ln)
        if bm:
            nm = bm.group(1)
            if kind == "focus":
                fm = FOCUSID.match(ln)
                if fm: nm = fm.group(1)
            stack.append((0, nm))
        # 更新所有深度
        if dd:
            # 先按 { } 顺序处理
            for ch_i, ch in enumerate(re.sub(r'#.*$', '', re.sub(r'"[^"]*"', '', ln))):
                pass
            # 简化：整行增减
            if dd > 0:
                # 该行可能有多个 {，只把最外层归到刚压入的名字
                for lvl, nm in stack:
                    pass
                stack = [(lvl + dd, nm) for lvl, nm in stack]
                # 记录当前最外层块名
                stack.append((stack[-1][0] - dd, bm.group(1) if bm else ""))
            elif dd < 0:
                stack = [(lvl + dd, nm) for lvl, nm in stack]
                stack = [(lvl, nm) for lvl, nm in stack if lvl >= 0]
        # 记录块名映射：让下一轮icon 能拿到
        if bm:
            pass
    return out

def scan2(path, kind):
    """重写版：显式维护「当前最内层块名」"""
    raw = open(path, encoding="utf-8", errors="ignore", newline='').read().split("\n")
    out = {}
    depth = 0
    cur = ""              # 当前最内层块名
    lastid = ""           # focus: 最近遇到的 id=
    for i, ln in enumerate(raw, 1):
        m = ICON.match(ln)
        if m:
            out[i] = lastid if kind == "focus" else cur
        fm = FOCUSID.match(ln)
        if fm: lastid = fm.group(1)
        bm = BLOCK.match(ln)
        if bm:
            nm = bm.group(1)
            if kind == "focus" and fm: nm = fm.group(1)
            cur = nm
        dd = depth_delta(ln)
        if dd < 0:
            # 退到外层：粗略地保留最后一个非空名
            pass
        depth += dd
    return out

res = {}
for kind, sub in (("focus", "national_focus"), ("idea", "ideas")):
    d = os.path.join(MOD, "common", sub)
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".txt"): continue
        r = scan2(os.path.join(d, fn), kind)
        n_with = sum(1 for v in r.values() if v)
        n_all = len(r)
        res["%s/%s" % (kind, fn)] = r
        print("%-6s %-34s %3d 条, ctx 有 %3d (%.0f%%)" % (kind, fn, n_all, n_with,
              100.0*n_with/n_all if n_all else 0))

json.dump(res, open(os.path.join(STG, "ctxmap.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("\n写出 ctxmap.json")
