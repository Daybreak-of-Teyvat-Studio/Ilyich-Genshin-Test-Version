# -*- coding: utf-8 -*-
"""2026-10-19 修正：撤销 429 误并（429 本应是 419）

- 419 并入 421（用户本意 419+421+427=421）
- 429（现内容=原 852/蛇骨矿洞）改名到 419，保持 1..689 连号
- 429 恢复为挪德卡莱州（1156/1532/2464，NDK，VP 2464 10），并从 Region7 退回 Region1
"""
import io, os, re, sys, shutil, datetime

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version"
MOD = os.path.join(ROOT, "Daybreak of Teyvat Gamma Version")
ST = os.path.join(MOD, "history", "states")
RD = os.path.join(MOD, "map", "strategicregions")
LOC = os.path.join(MOD, "localisation", "simp_chinese")
APPLY = "--apply" in sys.argv
BACKUP_429 = os.path.join(ROOT, ".backups", "mond_merge_20261018_235920", "429-State_429.txt")


def rd(p):
    raw = open(p, "rb").read()
    return raw.decode("utf-8-sig"), raw[:3] == b"\xef\xbb\xbf"


def wr(p, t, bom):
    open(p, "wb").write((b"\xef\xbb\xbf" if bom else b"") + t.encode())


def spath(sid):
    return os.path.join(ST, f"{sid}-State_{sid}.txt")


def info(sid):
    t, b = rd(spath(sid))
    provs = [int(x) for x in re.search(r"provinces\s*=\s*\{([^}]*)\}", t).group(1).split()]
    vps = [(int(a), int(b)) for a, b in re.findall(r"victory_points\s*=\s*\{\s*(\d+)\s+(\d+)", t)]
    return t, b, provs, vps


t419, b419, p419, v419 = info(419)
t421, b421, p421, v421 = info(421)
t429, b429, p429, v429 = info(429)
t429old, b429old = rd(BACKUP_429)
p429old = [int(x) for x in re.search(r"provinces\s*=\s*\{([^}]*)\}", t429old).group(1).split()]

print("419:", p419, v419)
print("421:", p421, v421)
print("429(cur):", p429, v429)
print("429(restore):", p429old)

ENC = set(p429old)
# --- 421 final: 419 merged in, enclave out
new421 = sorted((set(p421) | set(p419)) - ENC)
new421_vps = [v for v in v421 if v[0] not in ENC] + v419
print("421 final:", len(new421), new421, new421_vps)

# --- blocks to move: from 419 into 421
PROV_BLK = re.compile(r"\t\t\t(\d+) = \{\r\n((?:\t\t\t\t[^\r\n]*(?:\r\n))+)+\t\t\t\}")
blocks419 = [(int(m.group(1)), m.group(0)) for m in PROV_BLK.finditer(t419)]
blocks421 = [(int(m.group(1)), m.group(0)) for m in PROV_BLK.finditer(t421)]
print("blocks 419:", [b[0] for b in blocks419], "| 421:", [b[0] for b in blocks421])

# 419's block provinces are inside 419 (no per-province blocks there? check)
print("419 block provs in 419:", [p for p, _ in blocks419 if p in p419])

if not APPLY:
    print("[DRY]")
    sys.exit()

stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
bdir = os.path.join(ROOT, ".backups", "fix429_" + stamp)
os.makedirs(bdir, exist_ok=True)
for sid in (419, 421, 429):
    shutil.copy2(spath(sid), os.path.join(bdir, f"{sid}-State_{sid}.txt"))
for f in ("airports.txt", "rocketsites.txt", "buildings.txt"):
    shutil.copy2(os.path.join(MOD, "map", f), os.path.join(bdir, f))
for f in ("DOT_Strategicregions_01.txt", "DOT_Strategicregions_07.txt"):
    shutil.copy2(os.path.join(RD, f), os.path.join(bdir, f))
for f in os.listdir(LOC):
    if f.endswith(".yml") and ("state_names_gamma" in f or "Strategic_Region" in f):
        shutil.copy2(os.path.join(LOC, f), os.path.join(bdir, f))

# ---------- 1) build new 421 ----------
t = t421
# drop enclave blocks from 421
for p, blk in blocks421:
    if p in ENC:
        t = t.replace(blk, "", 1)
# drop enclave VPs
for p, v in list(v421):
    if p in ENC:
        t = re.sub(r"\t\tvictory_points = \{ " + str(p) + r" \d+ \}\r\n", "", t, count=1)
# add 419's blocks before history close: simplest append to buildings block
for p, blk in blocks419:
    bm = re.search(r"\t\tbuildings = \{", t)
    depth = 0
    for i in range(bm.end() - 1, len(t)):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                close = i
                break
    line_start = t.rfind("\r\n", 0, close) + 2
    t = t[:line_start] + blk + "\r\n" + t[line_start:]
# add 419 VPs before history close
if v419:
    h = re.search(r"(?m)^\thistory = \{", t)
    depth = 0
    for i in range(h.end() - 1, len(t)):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                close = i
                break
    line_start = t.rfind("\r\n", 0, close) + 2
    add = "".join(f"\t\tvictory_points = {{ {p} {v} }}\r\n" for p, v in v419)
    t = t[:line_start] + add + t[line_start:]
t = re.sub(r"(provinces\s*=\s*\{\r?\n\t\t)[^\r\n]*(\r?\n\t\})",
           lambda m: m.group(1) + " ".join(map(str, new421)) + m.group(2), t, count=1)
wr(spath(421), t, b421)
os.remove(spath(419))

# ---------- 2) rename 429 -> 419 ----------
t429 = re.sub(r"(\bid\s*=\s*)429\b", r"\g<1>419", t429, count=1)
t429 = t429.replace('name="DOT_STATE_429"', 'name="DOT_STATE_419"')
wr(spath(419), t429, b429)
os.remove(spath(429))

# ---------- 3) restore 429 ----------
wr(spath(429), t429old, b429old)

# ---------- 4) buildings remap by province ----------
p2s = {}
for fn in os.listdir(ST):
    if not fn.endswith(".txt"):
        continue
    sid = int(fn.split("-")[0])
    t = io.open(os.path.join(ST, fn), encoding="utf-8-sig").read()
    for x in re.search(r"provinces\s*=\s*\{([^}]*)\}", t).group(1).split():
        p2s[int(x)] = sid
bp = os.path.join(MOD, "map", "buildings.txt")
bt, bb = rd(bp)
lines = bt.split("\r\n")
changed = 0
for i, ln in enumerate(lines):
    f = ln.split(";")
    if len(f) == 7 and f[0].isdigit():
        pid = int(f[6]) if f[6].isdigit() else None
        if pid in p2s and int(f[0]) != p2s[pid]:
            f[0] = str(p2s[pid])
            lines[i] = ";".join(f)
            changed += 1
wr(bp, "\r\n".join(lines), bb)
print("buildings rows fixed:", changed)

# ---------- 5) airports / rocketsites ----------
for fn in ("airports.txt", "rocketsites.txt"):
    p = os.path.join(MOD, "map", fn)
    t, b = rd(p)
    keys = {}
    for line in t.split("\r\n"):
        m = re.match(r"^(\d+)=\{(.*)\}$", line.strip())
        if m:
            keys[int(m.group(1))] = [int(x) for x in m.group(2).split()]
    k421 = set(keys.get(421, [])) | set(keys.get(419, []))
    k421 -= ENC
    k419 = set(keys.get(429, []))
    k429 = set(ENC)
    for k in (419, 421, 429):
        keys.pop(k, None)
    for k, v in ((419, k419), (421, k421), (429, k429)):
        keys[k] = sorted(v)
    body = "\r\n".join(
        f"{k}={{{' '.join(map(str, v))} }}" for k, v in sorted(keys.items()))
    wr(p, body + "\r\n", b)

# ---------- 6) loc ----------
locf = os.path.join(LOC, "DOT_state_names_gamma_l_simp_chinese.yml")
t, b = rd(locf)
# move 429's name to 419, clear 419 old, add 429 as *
m = re.search(r'(?m)^(\s*)DOT_STATE_429:(\d*)\s*"([^"]*)"', t)
name429 = m.group(3) if m else "*"
t = re.sub(r"(?m)^\s*DOT_STATE_419:\d*\s*\"[^\"]*\"\r?\n", "", t)
t = re.sub(r"(?m)^\s*DOT_STATE_429:\d*\s*\"[^\"]*\"\r?\n", "", t)
t = t.rstrip("\r\n") + f'\r\n DOT_STATE_419:0 "{name429}"\r\n DOT_STATE_429:0 "*"\r\n'
wr(locf, t, b)

# ---------- 7) regions: R7 remove enclave, R1 add ----------
for fn, add in (("DOT_Strategicregions_07.txt", set()), ("DOT_Strategicregions_01.txt", ENC)):
    p = os.path.join(RD, fn)
    t, b = rd(p)
    ps = [int(x) for x in re.search(r"provinces\s*=\s*\{([^}]*)\}", t).group(1).split()]
    ps = sorted((set(ps) - ENC) | add)
    nl = "\r\n" if "\r\n" in t else "\n"
    body = nl.join(map(str, ps))
    t = re.sub(r"(provinces\s*=\s*\{)[^}]*(\})",
               lambda m: m.group(1) + nl + body + nl + "\t" + m.group(2), t, count=1)
    wr(p, t, b)

print("done; backup:", bdir)
