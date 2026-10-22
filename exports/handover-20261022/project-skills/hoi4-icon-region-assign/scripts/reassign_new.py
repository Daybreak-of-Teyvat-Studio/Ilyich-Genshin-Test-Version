# -*- coding: utf-8 -*-
"""只重跑「新增了地区归属」的文件（KNA_focus / KNA_ideas / KQP_ideas）。
复用 reassign_v10.py 的全部逻辑，但只输出这几个文件的 plan，避免动已写回的 56 个。
输出 plan_extra2.json + out7/
"""
import os, re, sys, json, collections
sys.stdout.reconfigure(encoding="utf-8")
STG = r"C:\Users\XIANGZIYUAN\hoi4lint\icon_gen\stage4"
ONLY = {"MHL_Focus.txt"}

src = open(os.path.join(STG, "reassign_v10.py"), encoding="utf-8").read()
# 禁用原脚本的落盘，改为 exec 捕获其全局变量后复用
src = src.replace('json.dump(plan, open(os.path.join(STG, "plan_v10.json"), "w", encoding="utf-8"), ensure_ascii=False)',
                  'pass  # 落盘由本脚本负责')
g = {"__file__": os.path.join(STG, "reassign_v10.py"), "__name__": "reassign_v10"}
exec(compile(src, "reassign_v10_all", "exec"), g)

collect = g["collect"]; FR = g["FR"]; POOL = g["POOL"]; PG = g["PG"]; PACKS = g["PACKS"]
focus_zhgrams = g["focus_zhgrams"]; sprite_grams = g["sprite_grams"]
sc = g["sc"]; bridge = g["bridge"]; has_hit = g["has_hit"]; MIN_HIT = g["MIN_HIT"]
MAXUSE = g["MAXUSE_IN_FILE"]; FDIR = g["FDIR"]; IDIR = g["IDIR"]

F = collect(FDIR, "focus"); I = collect(IDIR, "idea")

plan = []
for kind, tree in (("focus", F), ("idea", I)):
    for fn, lst in sorted(tree.items()):
        if fn not in ONLY: continue
        home = FR.get(fn)
        assert home in PACKS, (fn, home)
        pool = POOL[(kind, home)]; pg = PG[(kind, home)]
        cands = []
        for it in lst:
            qg = focus_zhgrams(it["ctx"])
            if not qg: qg = sprite_grams(it["old"])
            qb = bridge(qg) if qg else set()
            dg = g["focus_descgrams"](it["ctx"]) if not g["cands_ok"](qg, pg) else set()
            qd = (bridge(dg | qg) if dg else set())
            ls = []
            for j in range(len(pool)):
                if has_hit(qg, pg[j]): ls.append((sc(qg, pg[j]), 0, j))
                elif has_hit(qb, pg[j]): ls.append((sc(qb, pg[j]) * 0.85, 1, j))
                elif has_hit(qd, pg[j]): ls.append((sc(qd, pg[j]) * 0.75, 2, j))
            ls.sort(reverse=True)
            cands.append(ls[:120])
        used = collections.Counter(); got = {}
        flat = sorted([(-s, m, i, j) for i, l in enumerate(cands) for s, m, j in l])
        for negs, m, i, j in flat:
            if i in got: continue
            n = pool[j]
            if used[n] >= MAXUSE: continue
            used[n] += 1; got[i] = (n, -negs, "literal" if m == 0 else "concept")
        for i in range(len(lst)):
            if i in got: continue
            it = lst[i]; pick = None; pk = 0.0; pm = "same_region"
            if it["old"] in pool and used[it["old"]] < MAXUSE:
                pick = it["old"]; pm = "keep"
            if pick is None:
                for s, m, j in cands[i]:
                    if used[pool[j]] < MAXUSE:
                        pick = pool[j]; pk = s; pm = "literal" if m == 0 else "concept"; break
            if pick is None:
                qb2 = bridge(focus_zhgrams(it["ctx"])) or sprite_grams(it["old"])
                best = None; bs = MIN_HIT
                for n, gg in zip(pool, pg):
                    if used[n] >= MAXUSE: continue
                    s = sc(qb2, gg)
                    if s > bs: bs = s; best = n
                if best is None:
                    for n in pool:
                        if used[n] < MAXUSE: best = n; break
                pick = best; pk = bs; pm = "concept_fb"
            used[pick] += 1; got[i] = (pick, pk, pm)
        for i, it in enumerate(lst):
            if i not in got: continue
            n, s, m = got[i]
            if n != it["old"]:
                plan.append({"kind": kind, "file": fn, "line": it["line"],
                             "old": it["old"], "new": n, "score": round(s, 4),
                             "mode": m, "home": home, "ctx": it["ctx"]})
        print("%-8s %-18s 地区 %-4s 条目 %3d 变更 %d" % (kind, fn, home, len(lst),
              sum(1 for x in plan if x["file"] == fn and x["kind"] == kind)))

json.dump(plan, open(os.path.join(STG, "plan_extra2.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("\nplan_extra2.json 共 %d 条" % len(plan))
print("方式: %s" % dict(collections.Counter(x["mode"] for x in plan)))
bad = [x for x in plan if ("_%s_" % x["home"]) not in x["new"]]
print("地区错配: %d" % len(bad))
for x in bad[:5]: print("  ", x)
