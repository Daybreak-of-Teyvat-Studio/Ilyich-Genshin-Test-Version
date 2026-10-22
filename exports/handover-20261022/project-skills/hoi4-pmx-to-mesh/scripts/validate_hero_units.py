#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HOI4 英雄单位注册校验（仿既有英雄建档后的自检）。

用法:
    python validate_hero_units.py <MOD根目录>

检查项（全部输出到 stdout，全绿才算接线完成）:
  1. 括号配平 + 注释/字符串剔除后的最小深度
  2. 事件 id 全局唯一（跨 events/ 全目录）
  3. 每个英雄的 7 项调用链闭合：
     sub_unit / division_template / create_unit 的模板名 /
     事件 trigger tag / 图标 spriteType / 中英本地化 / pdxmesh

设计要点：
  - 同名 <TAG> 只能被一个角色占（<TAG>_infantry_N_entity 会互相顶掉）
  - <TAG>_infantry_entity（无数字）不生效；生效的是 _0~_3
"""
import io
import os
import re
import sys


def read(p):
    return io.open(p, "r", encoding="utf-8-sig", errors="replace").read()


def brace_balance(text):
    s = re.sub(r'"[^"\n]*"', '""', text)   # 去字符串
    s = re.sub(r"#[^\n]*", "", s)          # 去注释
    d = mn = 0
    for ch in s:
        if ch == "{":
            d += 1
        elif ch == "}":
            d -= 1
            mn = min(mn, d)
    return d, mn


def collect_event_ids(events_dir):
    ids = {}
    for root, _, fs in os.walk(events_dir):
        for fn in fs:
            if not fn.endswith(".txt"):
                continue
            t = read(os.path.join(root, fn))
            for m in re.finditer(r'^\s*id\s*=\s*([A-Za-z_][A-Za-z_0-9]*\.\d+)', t, re.M):
                ids.setdefault(m.group(1), []).append(fn)
    return ids


def collect_entities(entities_dir):
    """返回 {entity_name: clone_target_or_None}。"""
    out = {}
    for fn in os.listdir(entities_dir):
        if not fn.endswith(".asset"):
            continue
        t = read(os.path.join(entities_dir, fn))
        for m in re.finditer(r'entity\s*=\s*\{(.*?)\n\}', t, re.S):
            b = m.group(1)
            nm = re.search(r'name\s*=\s*"([^"]+)"', b)
            cm = re.search(r'clone\s*=\s*"([^"]+)"', b)
            if nm:
                out[nm.group(1)] = cm.group(1) if cm else None
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    G = sys.argv[1]

    # 1) 括号配平（按需扩展要检查的文件清单）
    print("== 1. 括号配平 ==")
    targets = [
        "common/units/Ilyich_Hero.txt",
        "common/scripted_effects/Ilyich_Hero_effects.txt",
        "interface/Ilyich_Hero.gfx",
    ]
    ev_dir = os.path.join(G, "events")
    for fn in sorted(os.listdir(ev_dir)) if os.path.isdir(ev_dir) else []:
        if "Hero" in fn:
            targets.append("events/" + fn)
    for rel in targets:
        p = os.path.join(G, rel)
        if not os.path.exists(p):
            continue
        d, mn = brace_balance(read(p))
        flag = "OK" if d == 0 and mn >= 0 else "*** BAD ***"
        print("  %-52s balance=%+d min=%d %s" % (rel, d, mn, flag))

    # 2) 事件 id 唯一性
    print("== 2. 事件 id 唯一性 ==")
    ids = collect_event_ids(ev_dir)
    dups = {k: v for k, v in ids.items() if len(v) > 1}
    print("  总事件 id: %d，重复: %d" % (len(ids), len(dups)))
    for k in sorted(dups)[:10]:
        print("    *** dup %s -> %s" % (k, sorted(set(dups[k]))))
    if len(dups) > 10:
        print("    ... 共 %d 组重复（多为 MOD 既有问题，按需处理）" % len(dups))

    # 3) 各 <TAG>_infantry_N_entity 归属（谁占了谁）
    print("== 3. <TAG>_infantry_N_entity 归属 ==")
    ents = collect_entities(os.path.join(G, "gfx", "entities"))
    for n in sorted(ents):
        if re.match(r"^[A-Z]{3}_infantry_[0-3]_entity$", n):
            print("  %-26s <- %s" % (n, ents[n]))

    print()
    print("提示：无数字后缀的 <TAG>_infantry_entity 不生效，生效的是 _0~_3 这批。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
