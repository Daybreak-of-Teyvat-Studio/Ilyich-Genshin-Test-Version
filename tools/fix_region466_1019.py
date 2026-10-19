# -*- coding: utf-8 -*-
"""Fix 2026-10-19: move state 466 (蒙德城) provinces from Region1 to Region6 (坠星山谷)."""
import io, os, re, sys, shutil, datetime

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version"
MOD = os.path.join(ROOT, "Daybreak of Teyvat Gamma Version")
RD = os.path.join(MOD, "map", "strategicregions")
APPLY = "--apply" in sys.argv

PROVS = [292, 1395, 3433, 3435, 3441, 3456, 3481, 3485]


def rd(p):
    raw = open(p, "rb").read()
    return raw.decode("utf-8-sig"), raw[:3] == b"\xef\xbb\xbf"


def wr(p, t, bom):
    if APPLY:
        open(p, "wb").write((b"\xef\xbb\xbf" if bom else b"") + t.encode())


def get_provs(t):
    m = re.search(r"provinces\s*=\s*\{([^}]*)\}", t)
    return [int(x) for x in m.group(1).split()]


def set_provs(t, ps):
    return re.sub(r"(provinces\s*=\s*\{)[^}]*(\})",
                  lambda m: m.group(1) + "\r\n" + "\n".join(map(str, ps)) + "\r\n\t" + m.group(2), t, count=1)


r1p = os.path.join(RD, "DOT_Strategicregions_01.txt")
r6p = os.path.join(RD, "DOT_Strategicregions_06.txt")
t1, b1 = rd(r1p)
t6, b6 = rd(r6p)
p1, p6 = get_provs(t1), get_provs(t6)
print("R1 before:", len(p1), "R6 before:", len(p6))
missing = [x for x in PROVS if x not in p1]
print("466 provinces not in R1:", missing)
new1 = [x for x in p1 if x not in PROVS]
new6 = sorted(set(p6) | set(PROVS))
print("R1 after:", len(new1), "R6 after:", len(new6))

if APPLY:
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = os.path.join(ROOT, ".backups", "region466_" + stamp)
    os.makedirs(bdir, exist_ok=True)
    for f in (r1p, r6p):
        shutil.copy2(f, os.path.join(bdir, os.path.basename(f)))
    for path, text, bom, provs in ((r1p, t1, b1, new1), (r6p, t6, b6, new6)):
        nl = "\r\n" if "\r\n" in text else "\n"
        body = nl.join(map(str, provs))
        text = re.sub(r"(provinces\s*=\s*\{)[^}]*(\})",
                      lambda m: m.group(1) + nl + body + nl + "\t" + m.group(2), text, count=1)
        wr(path, text, bom)
    print("written; backup:", bdir)
else:
    print("[DRY] nothing written")
