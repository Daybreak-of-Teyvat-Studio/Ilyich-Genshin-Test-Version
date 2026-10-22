#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""HOI4 error.log 归类报告 —— 把游戏报错变成带真实行号的工作清单。

用法:
    python errorlog_report.py --mod "<MOD根>" [--log <error.log>] [--vanilla "<HOI4根>"]
                              [--patterns]

不带 --log 时自动挑选 crashes/*/logs/error.log 中体积最大的那份。
输出:
  1) 修复项对照友好的「消息模板计数」
  2) 按「文件 + 行号」聚合的 MOD 内错误清单（可直接照着改）

只读，不改任何文件。
"""
import argparse, collections, datetime, io, os, re, sys

def find_best_log() -> str:
    base = None
    # 常见位置：<Documents>/Paradox Interactive/Hearts of Iron IV
    for cand in [
        os.path.expanduser(r"~\Documents\Paradox Interactive\Hearts of Iron IV"),
        os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "Paradox Interactive", "Hearts of Iron IV"),
    ]:
        if os.path.isdir(cand):
            base = cand
            break
    if base is None:
        return ""
    best = None
    crash = os.path.join(base, "crashes")
    if os.path.isdir(crash):
        for d in os.listdir(crash):
            p = os.path.join(crash, d, "logs", "error.log")
            if os.path.isfile(p):
                sz = os.path.getsize(p)
                if best is None or sz > best[1]:
                    best = (p, sz)
    live = os.path.join(base, "logs", "error.log")
    if os.path.isfile(live) and (best is None or os.path.getsize(live) > best[1]):
        best = (live, os.path.getsize(live))
    return best[0] if best else ""

RE_INFILE = re.compile(r'in file: "([^"]+)" near line: (\d+)')
RE_FILELINE = re.compile(r'\]\s*([A-Za-z0-9_./\\ -]+\.(?:txt|yml|gui|gfx)):(\d+):\s*(.*)$')

def normalize(msg: str) -> str:
    msg = re.sub(r"\d+", "#", msg)
    return re.sub(r"\s+", " ", msg).strip()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", required=True)
    ap.add_argument("--vanilla", default="")
    ap.add_argument("--log", default="")
    ap.add_argument("--patterns", action="store_true", help="额外打印消息模板计数")
    a = ap.parse_args()

    log = a.log or find_best_log()
    if not log or not os.path.isfile(log):
        print("ERROR: 找不到 error.log，请用 --log 指定", file=sys.stderr)
        return 2
    mod = os.path.abspath(a.mod)

    txt = io.open(log, "r", encoding="utf-8", errors="replace").read()
    lines = txt.splitlines()
    print(f"日志: {log}")
    print(f"体积: {len(txt):,} B   行数: {len(lines):,}")
    print()

    if a.patterns:
        print("=== 消息模板计数（前 30）===")
        c = collections.Counter(normalize(l) for l in lines if l.strip())
        for msg, n in c.most_common(30):
            print(f"{n:>9,}  {msg[:160]}")
        print()

    def in_mod(rel: str) -> bool:
        return os.path.isfile(os.path.join(mod, rel.replace("/", os.sep)))

    byfile = collections.defaultdict(collections.Counter)
    other = 0
    for ln in lines:
        if not ln.strip():
            continue
        m = RE_INFILE.search(ln)
        if m:
            f, n = m.group(1), int(m.group(2))
        else:
            m = RE_FILELINE.search(ln)
            if not m:
                other += 1
                continue
            f, n = m.group(1), int(m.group(2))
        if in_mod(f):
            byfile[f][(n, normalize(ln.split("]:", 1)[-1]))] += 1
        else:
            other += 1

    total = sum(len(v) for v in byfile.values())
    print(f"=== MOD 内可定位错误点: {total} 处，覆盖 {len(byfile)} 个文件 ===")
    print(f"（另有 {other:,} 行涉及原版文件或无法定位）")
    print()
    for f in sorted(byfile, key=lambda k: -len(byfile[k])):
        print(f"### {f}   ({len(byfile[f])} 处)")
        for (n, msg), cnt in sorted(byfile[f].items()):
            print(f"    line {n:<7} x{cnt:<3} {msg[:150]}")
        print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
