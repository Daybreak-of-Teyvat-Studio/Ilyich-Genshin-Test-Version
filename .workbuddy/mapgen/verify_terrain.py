# -*- coding: utf-8 -*-
"""验收：确认 default.map 指向、新文件可用，并生成改动位置标注图"""
import os, io, struct, time
import numpy as np
from PIL import Image

G = r"C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version"
M = os.path.join(G, "map")
H = os.path.join(G, ".workbuddy")
RUN = time.strftime("%m%d_%H%M%S")
rep = []
def P(*a): rep.append(" ".join(str(x) for x in a))

P("===== default.map =====")
P(io.open(os.path.join(M, "default.map"), "r", encoding="utf-8-sig").read().strip())

P("")
P("===== 相关文件 =====")
for n in ["terrain.bmp", "terrain_new.bmp", "terrain_mountain.bmp", "heightmap.bmp",
          "heightmap_new.bmp", "heightmap_new_new.bmp"]:
    p = os.path.join(M, n)
    if os.path.isfile(p):
        P("  %-24s %9d  %s" % (n, os.path.getsize(p),
          time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(p)))))

dm = io.open(os.path.join(M, "default.map"), "r", encoding="utf-8-sig").read()
import re as _re
tm = _re.search(r'terrain\s*=\s*"([^"]+)"', dm)
hmn = _re.search(r'heightmap\s*=\s*"([^"]+)"', dm)
TER = tm.group(1) if tm else "terrain.bmp"
HMN = hmn.group(1) if hmn else "heightmap.bmp"
new_path = os.path.join(M, TER)
chk = np.array(Image.open(new_path))
hm = np.array(Image.open(os.path.join(M, HMN)))
tb = np.array(Image.open(os.path.join(M, "terrain.bmp")))
land = hm >= 94
mask = land & (hm >= 175)

P("")
P("===== 验收 =====")
P("  生效 terrain 文件 = %s，尺寸 %s，heightmap = %s" % (TER, chk.shape, HMN))
P("  目标色 (58,131,82) 像素数 = %d" % int(((chk[:,:,0]==58)&(chk[:,:,1]==131)&(chk[:,:,2]==82)).sum()))
P("  与原 terrain 差异像素 = %d ; mask = %d ; 完全一致: %s"
  % (int((chk != tb).any(axis=2).sum()), int(mask.sum()), bool(((chk != tb).any(axis=2) == mask).all())))
P("  非命中区完全未变: %s" % bool((chk[~mask] == tb[~mask]).all()))

# 标注图：整图上把改动位置描成亮红
ann = tb.copy()
from scipy import ndimage as ndi
edge = mask & ~ndi.binary_erosion(mask, np.ones((3, 3)))
ann[mask] = (255, 0, 0)
ann[edge] = (255, 255, 0)
out = os.path.join(H, "terrain_paint_preview", "run_" + RUN)
os.makedirs(out, exist_ok=True)
Image.fromarray(ann).resize((1024, 512), Image.NEAREST).save(os.path.join(out, "annotated.png"))
P("")
P("标注图（红=改动区，黄=边界）: %s" % os.path.join(out, "annotated.png"))

io.open(os.path.join(H, "terrain_verify_%s.txt" % RUN), "w", encoding="utf-8").write("\n".join(rep))
print("\n".join(rep))
