import os, re, io, glob, collections

MOD = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
VAN = r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
OUT = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\.workbuddy\report_bookmark.txt"
L = []
def P(*a):
    L.append(" ".join(str(x) for x in a))

# ---------- 索引：ideas / focus / ideology ----------
def collect(pattern_list, key_re):
    s = set()
    for pat in pattern_list:
        for f in glob.glob(pat, recursive=True):
            try:
                t = io.open(f, "r", encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            s |= set(key_re.findall(t))
    return s

idea_ids = collect([os.path.join(MOD, "common", "ideas", "*.txt"), os.path.join(MOD, "common", "ideas", "**", "*.txt"),
                    os.path.join(VAN, "common", "ideas", "*.txt"), os.path.join(VAN, "common", "ideas", "**", "*.txt")],
                   re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", re.M))
focus_ids = collect([os.path.join(MOD, "common", "national_focus", "*.txt"), os.path.join(VAN, "common", "national_focus", "*.txt")],
                    re.compile(r"\bid\s*=\s*([A-Za-z_][A-Za-z0-9_]*)"))
ideo_ids = collect([os.path.join(MOD, "common", "ideologies", "*.txt"), os.path.join(VAN, "common", "ideologies", "*.txt")],
                   re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", re.M))
# 国家 tag 是否声明
tags = set()
for p in [os.path.join(MOD, "common", "country_tags", "*.txt"), os.path.join(VAN, "common", "country_tags", "*.txt")]:
    for f in glob.glob(p):
        tags |= set(re.findall(r"^\s*([A-Z0-9]{3})\s*=", io.open(f, "r", encoding="utf-8", errors="replace").read(), re.M))

P("="*80); P("0. 索引规模"); P("="*80)
P(f"   idea id = {len(idea_ids):,}   focus id = {len(focus_ids):,}   ideology = {len(ideo_ids)}   tag = {len(tags)}")

# ---------- 逐书签交叉核对 ----------
bdir = os.path.join(MOD, "common", "bookmarks")
cdir = os.path.join(MOD, "history", "countries")
cfiles = set()
for root, _, fs in os.walk(cdir):
    for f in fs:
        cfiles.add(os.path.relpath(os.path.join(root, f), cdir).replace("\\", "/").lower())
        cfiles.add(f.lower())
P(""); P(f"   history/countries 下的文件数 = {len(cfiles)//2 if cfiles else 0}（相对路径+文件名两套索引）")
P(f"   实际文件 = {len(glob.glob(os.path.join(cdir, '**', '*'), recursive=True))}")

for bf in sorted(glob.glob(os.path.join(bdir, "*.txt"))):
    t = io.open(bf, "r", encoding="utf-8", errors="replace").read()
    P(""); P("="*80); P(f"书签: {os.path.basename(bf)}   ({len(t.splitlines())} 行)"); P("="*80)
    names = re.findall(r'name\s*=\s*"([^"]+)"', t)
    dates = re.findall(r"date\s*=\s*([\d.]+)", t)
    P(f"   name = {names}    date = {dates}")
    # history 引用
    hs = re.findall(r'history\s*=\s*"([^"]+)"', t)
    miss = []
    for h in hs:
        cand = h if h.lower().endswith(".txt") else h + ".txt"
        if cand.lower() not in cfiles and h.lower() not in cfiles:
            miss.append(h)
    P(f"   history 引用 {len(hs)} 个，**找不到文件的 = {len(miss)}**  {miss[:20]}")
    # ideology
    ids = re.findall(r"ideology\s*=\s*([A-Za-z_][A-Za-z0-9_]*)", t)
    bad_id = sorted(set(ids) - ideo_ids)
    P(f"   ideology 用到的: {sorted(set(ids))}   **未定义 = {bad_id}**")
    # 国家 tag 块
    bk = t[t.find("bookmark"):]
    used_tags = re.findall(r'^\s*"([A-Z0-9]{3})"\s*=\s*\{', t, re.M)
    bad_tags = sorted(set(used_tags) - tags)
    P(f"   书签里的国家 tag = {len(used_tags)} 个   **未在 country_tags 定义 = {bad_tags}**")
    # ideas
    idea_used = set()
    for mb in re.finditer(r"ideas\s*=\s*\{([^}]*)\}", t, re.S):
        idea_used |= set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", mb.group(1)))
    idea_used = {x for x in idea_used if x not in ("yes", "no")}
    bad_ideas = sorted(idea_used - idea_ids)
    P(f"   ideas 引用 {len(idea_used)} 个   **未定义 = {len(bad_ideas)}**  {bad_ideas[:30]}")
    # focuses
    fo = set()
    for mb in re.finditer(r"focuses\s*=\s*\{([^}]*)\}", t, re.S):
        fo |= set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", mb.group(1)))
    bad_fo = sorted(fo - focus_ids)
    P(f"   focuses 引用 {len(fo)} 个   **未定义 = {len(bad_fo)}**  {bad_fo[:30]}")

# ---------- 16:46 日志开头 ----------
P(""); P("="*80); P("16:46 崩溃日志的最初 25 行（看加载起点有没有异常）"); P("="*80)
lp = r"C:\Users\XIANGZIYUAN\Documents\Paradox Interactive\Hearts of Iron IV\crashes\hoi4_20260924_164658\logs\error.log"
for i, ln in enumerate(io.open(lp, "r", encoding="utf-8", errors="replace").read().splitlines()[:25], 1):
    P(f"{i:4d}| {ln[:190]}")

io.open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("WROTE", OUT, len(L))
