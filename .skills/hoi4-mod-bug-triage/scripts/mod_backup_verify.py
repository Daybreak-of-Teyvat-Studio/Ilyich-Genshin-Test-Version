#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""HOI4 MOD 备份 / 校验 二合一。

用法:
    python mod_backup_verify.py backup --mod "<MOD根>" --out "<备份目录>"
    python mod_backup_verify.py verify --mod "<MOD根>" [--absent "<正则>"] [--absent "<正则2>"]

verify 做两件事：
  1) 括号/引号平衡校验 —— **忽略 # 注释与 "..." 字符串内的花括号**，
     否则会大量误报（实测朴素的 count("{") 会误判 3 个文件）。
  2) 残留检查 —— 确认修复目标已清零；注意剔除自己写的 # FIXED 注释，
     以及「子串陷阱」（如检查 `arget_state` 会命中已修好的 `target_state`）。
"""
import argparse, os, re, shutil, sys

BACKUP_DIRS = ["common", "events", "history", "interface", "localisation",
               "portraits", "map", "tools", "docs", "tutorial"]
BACKUP_EXT = (".txt", ".yml", ".ini", ".lua", ".gfx", ".gui", ".info", ".md", ".csv", ".asset")
SKIP_DIR_MARK = (os.sep + ".workbuddy", os.sep + ".backups", os.sep + ".git")

def _iter_files(mod):
    for dp, dn, fn in os.walk(mod):
        if any(m in dp for m in SKIP_DIR_MARK):
            continue
        for f in fn:
            if f.lower().endswith(BACKUP_EXT):
                yield os.path.join(dp, f), os.path.relpath(os.path.join(dp, f), mod)

def do_backup(mod, out):
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out, exist_ok=True)
    n = 0
    for d in BACKUP_DIRS:
        src = os.path.join(mod, d)
        if not os.path.isdir(src):
            continue
        for dp, dn, fn in os.walk(src):
            for f in fn:
                if f.lower().endswith(BACKUP_EXT):
                    sp = os.path.join(dp, f)
                    rel = os.path.relpath(sp, mod)
                    dp2 = os.path.join(out, rel)
                    os.makedirs(os.path.dirname(dp2), exist_ok=True)
                    shutil.copy2(sp, dp2)
                    n += 1
    for f in os.listdir(mod):
        if f.lower().endswith(".mod"):
            shutil.copy2(os.path.join(mod, f), os.path.join(out, f))
            n += 1
    print("已备份 %d 个文件 -> %s" % (n, out))
    print("回滚：按相同相对路径拷回 MOD 根目录即可。")

def do_verify(mod, absent):
    files = list(_iter_files(mod))
    bad = []
    for fp, rel in files:
        o = c = 0
        for ln in open(fp, "r", encoding="utf-8", errors="replace").read().split("\n"):
            seg = ln.split("#")[0]                  # 去注释
            seg = re.sub(r'"[^"]*"', "", seg)       # 去字符串
            o += seg.count("{"); c += seg.count("}")
        if o != c:
            bad.append((rel, o, c))
    print("### 括号平衡：检查 %d 个文件，不平衡 %d 个" % (len(files), len(bad)))
    for rel, o, c in bad[:30]:
        print("   {=%d }=%d   %s" % (o, c, rel))

    if absent:
        print()
        print("### 残留检查（应全为 0；已剔除注释行）")
        for pat in absent:
            tot = []
            rx = re.compile(pat, re.M)
            for fp, rel in files:
                for i, ln in enumerate(open(fp, "r", encoding="utf-8", errors="replace").read().split("\n")):
                    code = ln.split("#")[0]
                    if rx.search(code):
                        tot.append((rel, i + 1, ln.strip()[:100]))
            print("   %d 处  <= %s" % (len(tot), pat))
            for rel, n, s in tot[:10]:
                print("        %s:%d  %s" % (rel, n, s))
    return 0

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup"); b.add_argument("--mod", required=True); b.add_argument("--out", required=True)
    v = sub.add_parser("verify"); v.add_argument("--mod", required=True); v.add_argument("--absent", action="append", default=[])
    a = ap.parse_args()
    if a.cmd == "backup":
        do_backup(a.mod, a.out); return 0
    return do_verify(a.mod, a.absent)

if __name__ == "__main__":
    sys.exit(main())
