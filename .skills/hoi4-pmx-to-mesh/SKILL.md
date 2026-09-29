---
name: hoi4-pmx-to-mesh
description: 把 MMD 的 PMX/PMD 角色模型（.pmx + 一串贴图）转成钢铁雄心 IV（HOI4）可直接上游戏的单位模型：自写 PMX 解析器读网格/材质/骨骼/权重，把骨架用「相似变换 + 分步定标」映射到 HOI4 原版 33 根标准骨骼（从而复用原版步兵动画），合并贴图成图集并重映射 UV，用纯 numpy 编码 DXT1/DXT5 DDS，最后按 pdxasset 二进制格式写出 .mesh，并配套写好 gfx/entities 下的 .gfx（pdxmesh + animation 组）与 .asset（entity + attach 挂点）。当用户说「把这个 pmx/mmd 模型转成 HOI4 模型」「MMD 模型转钢铁雄心」「给某某角色做 HOI4 单位模型」「需要绑骨、复用原版动画」「PMX 转 mesh」「把模型转成 pdxmesh」时使用。也覆盖：mesh 二进制格式解析/写出、PMX 2.0 逐字段解析、HOI4 33 骨骼骨架与 rest 位置、MMD 叠层材质（同轴重合面）在只有深度测试的引擎里的整层剔除策略、眼球叠层可见性排查、顶点级 vs 三角形级遮挡测量、PMX 接缝顶点 UV +1 的坑、图集 gutter 与 UV 重映射、平铺法线/透明 spec 占位贴图的写法。触发词：PMX、PMD、MMD、pmx2mesh、pdxasset、pdxmesh、.mesh、mesh 格式、骨骼映射、绑骨、rig、armature、33 根骨骼、动画复用、DDS、DXT5、DXT1、BC1、BC3、图集、atlas、UV 重映射、权重迁移、skin、inverse bind、z-fighting、叠层材质、depth test、眼睛不显示、黑脸、黑腿。
agent_created: true
---

# PMX/MMD → HOI4 单位模型

把 MMD 角色（`.pmx`）转成 HOI4 能用的 `.mesh` + DDS + `.gfx` + `.asset`。
核心是把骨架**严格映射到 HOI4 原版 33 根标准骨骼**，这样可直接复用原版步兵/骑兵动画，
完全不用自己做动画。

> 完整可跑通的参考实现见 `scripts/vysna_build.py`（薇斯纳步兵模型，53,300 三角 / 3 draw call）。
> 里面的路径是那一轮的，换模型要改：`SRC`（pmx 路径）、`HOI4_RIG`、`FIT_ANCHORS`、`MAT_GROUP`、`EXCLUDE_KEYS`。

---

## 0. 先确认三件事，别急着写代码

1. **产物形态**：只要「能进游戏当单位」还是要「精细到能当立绘」？这决定要不要减面。
   用同 MOD 里**已跑起来的同类模型**做规模基线（例：某个已在用的 93,362 三角 → 你做到 5 万就没问题，
   **不需要减面**，能省掉一整轮 Blender 减面 + 权重重烘焙）。
2. **保留范围**：源模型常有装饰件（结晶/头饰/武器/特效）和**同轴叠层材质**。
   先问用户要留哪些，再决定 `EXCLUDE_KEYS`。
3. **是否复用原版动画**：几乎总是要。那就必须严格对齐 33 根骨骼。

**动手前务必读源模型目录里的 readme**。miHoYo / 商业模型通常写明
**禁止二次配布、禁止拆件、禁止商业用途**——照抄进 `.gfx` 头部注释里。

---

## 1. 工作目录：定在工作区**外**

本项目的 HOI4 工作区（`Ilyich-Genshin-Test-Version` 那棵树）**禁止覆盖已存在文件**、
**禁止 rename/move**（shell 里 `cp` 覆盖、`os.replace`、`os.rename` 全被拒；`rm -f` 反而**允许**）。

所以：
- 解包、中间产物、脚本、诊断报告，全部放**工作区外**，例如 `C:\Users\<user>\vysna_work\`。
- 最终产物再"先 `rm -f` 后 `cp`"落到 MOD 目录；**落之前先备份**到 `.workbuddy/backup_<时间戳>/`。
- 脚本里的输出目录一律用「自动避让名」函数（`fresh(path)`：存在就加 `_2`、`_3`），
  不要指望 `os.remove` —— 它被劫持成 safe-delete，回收站不可用时会**静默失败**。
- 大二进制**不要**用内置 Write 工具（会按文本编码破坏）；文本文件可以用 Write/Edit。

---

## 2. PMX 解析（`scripts/pmx_parse.py`）

PMX 2.0 布局：`"PMX "` magic → `version` f32 → globals（`gcount` u8，后跟 gcount 个 u8 决定
后续的索引宽度 / 文本编码 / 附加 UV 数）→ 模型名 → 顶点 → 面 → 贴图 → 材质 → 骨骼 → 变形 → 显示枠 → 刚体 → 关节。

用法（**没有 `parse()` 函数**，直接构造）：

```python
p = pmx_parse.PMX(path)
p.v_pos / p.v_nrm / p.v_uv / p.v_wtype / p.v_wbone / p.v_wweight
p.faces          # 扁平顶点索引，每 3 个一个三角
p.materials      # list[dict]
p.textures       # list[str]，相对源目录
p.bones          # list[dict]
```

**必须踩平的坑：**

| 坑 | 表现 | 正确做法 |
|---|---|---|
| 索引宽度 | 全家用 int32 读会错位 | `vidx/tidx/midx/moidx` **无符号**，`bidx/ridx` **有符号**；宽度由 globals 定 |
| 材质字段 | `KeyError: 'face_offset'` | 材质**只有 `face_count`**，偏移自己按 `_cursor` 累加 |
| **IK link 的角度限制** | 把骨骼读飞 | 判据是**每个 link 自带 1 字节 flag**，**不是**共用骨骼的 `ik_limit != 0` |
| 文本编码 | 名字乱码 | 按 globals 里的 encoding 选 `utf-16-le`(0) / `utf-8`(1) |

`draw_flag` 位标记：`0x01`=双面(no cull)、`0x10`=描边、`0x20`=顶点色。
MMD 的脸/眼材质常是 `0x03`（双面、无描边）——**渲染预览时若用单面剔除，眼球整层会消失**，
那是预览器的局限，不是模型问题。

---

## 3. HOI4 `.mesh` 格式（`scripts/pdx_write.py`）

magic `@@b@`（二进制）/ `@@t@`（文本）+ `pdxasset`（int 数组 `[1, 0]`）；
层次深度用 `[` 的重复次数表示；节点名以 NUL 结尾；
属性以 `!` 开头：`!<namelen:u8><name><type:c><count:i><data>`，`i`=int32 / `f`=float32 / `s`=string。

XML 树结构：

```
File
└─ object                       （名字 < 64 字符且 Latin-1 可编码）
   └─ shape [lod=N]
      ├─ mesh  ×N               ★ p/n/ta/u0/u1/u2/u3/tri/boundingsphere 是 mesh 的「属性」，不是子节点！
      │  ├─ aabb
      │  ├─ material           顺序 shader, diff, n, spec
      │  └─ skin               顺序 bones, ix, w
      └─ skeleton
         ├─ bone               顺序 ix, pa, tx
         └─ locator / node     顺序 p, q, pa, tx
```

- **`tri` 是每个 `mesh` 一张全局列表**（不是每 shape 一张）。
- `tx` 是**列主序 3×4** 的 inverse bind：`cols = reshape(4,3)`，`R = column_stack(cols[0..2])`，
  `t = cols[3]`，`pos = -R.T @ t`。
- **贴图路径写裸文件名**（如 `vysna_body_diffuse.dds`）就是对的 —— 原版 Keqing/Amber/Furina 的 mesh
  同样只写文件名，引擎按 mesh 所在目录解析。
- 参考形态：Keqing 是 **1 个 shape 下挂 6 个 mesh**（face/hair×2/clothes×2/skin），
  这是本 MOD 的标准做法；碰撞盒 shape 可选（Keqing 没有，Amber 有）。

**坑：`pdx_data.writeData` 用 `struct.pack("f"*size, *values)`，百万级属性会退化到不可用。**
必须自己用 numpy 写（见 `pdx_write.py`）。

自检：**读原版 mesh → 用写出器重写 → 逐字节比对必须完全一致**。这一步不做，后面全是白找。

---

## 4. 33 根标准骨骼（顺序即索引）

```
Root, Hip, LeftUpLeg, LeftLeg, LeftFoot, LeftToeBase, back_mid,
LeftShoulder, LeftArm, LeftForeArm, LeftForeArmRoll, LeftHand,
Left_Hand_node, Left_Hand_node_2, Left_Hand_node_3, Left_Hand_node_4,
head, RightShoulder, RightArm, RightForeArm, RightForeArmRoll, RightHand,
Right_Hand_node, Right_Hand_node_2, Right_Hand_node_3, Right_Hand_node_4,
mid_back_node, RightUpLeg, RightLeg, RightFoot, RightToeBase,
Root_node_1, Root_node_2
```

rest 位置（本项目实测反推，与参考 `tx` 反解最大偏差 **0.00006**；身高 ≈ **7.42**）：

```
Root (0,0,0)              Hip (0,3.9842,0.0874)      back_mid (0,4.5314,0.0675)
head (0,6.5045,0.0337)    mid_back_node (0,4.5799,0.9770)
LeftUpLeg (0.4364,3.4557,0.0881)  LeftLeg (0.6674,2.0382,0.1234)
LeftFoot  (0.8813,0.4592,0.4211)  LeftToeBase (1.1356,0.0571,0.0075)
LeftShoulder (0.3192,5.8114,0.0327)  LeftArm (0.7141,5.8690,0.1240)
LeftForeArm (1.6297,5.1430,0.1928)   LeftForeArmRoll (2.0082,4.8882,0.0460)
LeftHand (2.3635,4.6490,-0.0918)     Left_Hand_node (2.5845,4.2989,-0.3321)
```
右侧 x 取反。**`Left_Hand_node` 的 `tx` 在参考文件里是退化的（值 ~1e12），必须跳过。**

**骨架对齐用「分步定标」，不要一把 Umeyama 硬套**（轴/尺度耦合会让脚底离地）：

1. `R`：只用锚点最小二乘取**方向**；
2. `s`：**用骨架身高对齐** `(head.y − LeftToeBase.y) / (頭.y − 左つま先.y)`；
3. `t`：`ty` 由**脚尖骨落地**定；`tx/tz` 由**躯干中线**
   （`全ての親/センター/腰/上半身/上半身1/上半身2/首/頭` 均值 ↔ `Hip/back_mid/head` 均值）定。

骨骼映射优先级：① 名字规则 → ② 沿层级向上继承（限 12 轮）→ ③ 位置最近兜底。
映射函数里 **`by_name` 的匹配顺序是铁律：腿 → 臂 → 躯干 → 头**，否则 `足` 会被臂规则先吃掉。

### 4b. ★★★ 有 8 根骨在动画里会被「隐藏」，绝不能挂几何（翅膀消失的根因）

HOI4 用 **动画的 `s`（缩放）通道 = 0** 表示「这根骨本动画不参与」，整根骨被缩没，
挂在上面的几何在**游戏里彻底消失**（本地渲染器如果照做就看不到，照做是对的）。

实测扫遍 42 个 `GER_infantry*.anim`（脚本 `scripts/anim_hidden_bones.py`）：

| 骨 | 被隐藏的动画数 / 42 |
|---|---|
| `Left_Hand_node_2` / `Right_Hand_node_2` / `_3` / `_4` | 40 |
| **`mid_back_node`** | **39** |
| `Left_Hand_node` | 31 |
| `Right_Hand_node` | 15 |
| `Left_Hand_node_3` | 11 |
| `back_mid` / `Hip` / `head` / `Root` / `Chest` | **0（安全）** |

**后果**：`mid_back_node` 是原版挂「背包 / 可选装备」的骨，步兵不背包就把它缩没。
**任何「背后装备」性质的自定义几何（翅膀、披风、背包、光环）都绝不能挂它**
—— 挂上去 93% 的动画里会整个消失。改挂它的**父骨 `back_mid`**（42/42 动画都安全，
且 bind 位置只差 0.05~0.9，视觉上几乎一致）。

构建流程里**务必加一道自检**：把 `HIDDEN_RISK` 这 8 根骨的「受影响顶点数」打出来，
非 0 就报警。本项目踩坑现场：翅膀 3574 个顶点挂了 `mid_back_node`，游戏里整对翅膀不见，
而本地静态预览是好的（静帧不播动画，看不到 s=0）。

---

## 5. 贴图：图集 + UV 重映射 + DDS

- **图集**：按 draw call 分组（通常 body / face / hair），同组贴图打进一张 PO2 图集，
  货架装箱 + **gutter 边缘延展**（防 mip/双线性渗出），枚举 PO2 宽度取 `(面积, 最长边)` 最小的一组。
- **UV 重映射三件坑**：
  1. **PMX 会给「接缝顶点」的 uv 故意 +1**（`0.0416` 其实表示 `1.0416`），目的是让双线性采样不跨格渗色。
     直接看 `min/max` 会以为 uv 是负数。**正确处理就是 `np.mod(uv, 1)`**。
  2. **绝对不要做「UV 盒子线性映射」去"修负 uv"** —— 试过，会把整层压成一个点，
     采样到 gutter 变成**全黑**。
  3. 顶点去重的 key 必须带上**材质**（`(材质, 顶点)`），否则同一顶点被多个材质引用时
     UV / 位移会互相污染，整层废掉。
  4. 因为 UV 要重映射，**用完就跑一遍「图集采样 vs 源贴图采样」的逐点复核**，通道差应为 0。
- **DDS**：纯 numpy 编码 BC1/BC3（`scripts/dds_encode.py`），全 mip 链（降到 1×1）。
  `np.pad(mode="edge")` 补到 4 的倍数。是否用 DXT5 取决于该图集**是否真的用 alpha**。
  参考原版：`nospe` 是 **4×4 的 DXT5 占位**、平坦法线同理；本项目沿用这个做法。
- **贴图尺寸**：单位模型在屏幕上很小，**别按立绘分辨率做**。
  本 MOD 已有模型就有人用 512×512 全脸贴图。给个参照：face 1024×2048 / body 1024×2048 /
  hair 1024×1024 DXT5 合计约 7 MB，已经足够。**先按默认档做，觉得糊再翻倍**——
  翻倍一次 body 就会涨到 2048×4096（11 MB），不划算。

---

## 6. ★MMD 叠层材质：转换里最容易翻车的地方

MMD 大量使用**几何完全重合的叠层材质**，靠**材质绘制顺序**分层；
**HOI4 只有深度测试**，重合处谁可见取决于 `LESS`（先画赢）还是 `LESS_EQUAL`（后画赢），**不能靠猜**。

**诊断方法**（`scripts/coincident.py`）：用**三角形质心集合**（坐标取整到 1e-3）找所有真正重合的面。
不限材质索引数是否相等——只看索引相等会漏。
实测某模型一次找出 **11 组**真实重合：

```
髮 → 髮+   5775 三角      前髪 → 髮+  4758      体 → 肌2   2504
颜 → 照れ  1942           裙 → 裙内  1822      袜 → 袜s2  1678
颜2 → 颜4   524           体 → 裙+    449      翼 → 翼+    430
披肩 → 披肩s 243          目 → 瞳      192
```

**处理方针：把「后画的那一层」整层剔掉，保留基础层。**
这些叠加层的贴图大多是「大面积透明」的叠加图，**透明区的 RGB 常是黑**，
一旦在深度测试里胜出就是**整片黑块**（黑脸 / 黑腿 / 黑翅膀都是这么来的）。

例外：像 `裙 / 裙内` 这种**用的是同一张贴图**、谁的 UV 区域胜出都是同一种料，视觉无差别 → 可以保留。

**验证方法**：在自己的软件渲染器里加 `depth_le` 开关（`<` vs `<=`），
**两种规则各渲一遍，看差异**。剔干净后差异应压到「最大像素差个位数、几乎无像素超阈值」。

---

## 7. ★眼球叠层：可见性排查的完整套路

MMD 常把一只眼拆成 5 个同轴叠层：`白目`(眼白) / `目`(虹膜) / `瞳`(瞳孔) / `目光`(高光) / `星目`。
症状是「眼睛一片空白 / 一对白眼窝」。

**结论（省掉几小时）：先看 `目.png` 自己是不是一只完整的眼睛。**
实测：**只渲染 `目` 一张，就是一只完整正确的眼睛**（眼白 + 虹膜 + 瞳孔 + 高光 + 下眼睑装饰全在贴图里）。
→ **把 `白目/瞳/目光/星目` 全部整层剔除**，眼 = 单个材质，零 z-fighting。

剩下只需一步：`目` 被脸皮（`颜/颜2`）盖住 → **沿视线方向整层前推**。

**排查工具链（按顺序用）：**

1. `scripts/face_mats.py` —— 列出 face 组每个材质的**贴图 / draw_flag / 面数 / 是否被剔除**。
   一眼看出谁用哪张图（例：`星目` 用的是脸皮 `颜.png`，说明它不是眼，是脸上一片）。
2. `scripts/eye_only.py` —— **逐材质单独渲染**，各存一张图。
   这是**最有价值的一步**：直接看出每一个叠层单独长什么样。
3. `scripts/eye_push2.py` —— **前推量扫描**：只保留 `颜/颜2/睫/目`，渲染 push = 0 / 0.01 / 0.02 / 0.03 / 0.045 / 0.06，
   两种深度规则各一行。
   实测阈值约 **0.025**，取 **0.045**（≈身高的 0.6%，肉眼不可见）有充足余量。

**两个必须记住的测量教训：**

- **顶点级测量会骗人**：脸皮用**大三角**跨过眼部，眼附近根本没有脸皮顶点，
  按「顶点邻域」测永远得出"眼球已经在前面"的错误结论。
  **必须做三角形级（质心 / 2D 点-三角形 插值）遮挡测量。**
- **"整层前推"要小心方向**：角色朝 −Z，所以 **−Z 才是"前"**。
  前推必须做在**按材质分开的顶点副本**上——直接改共享的 `Vt` 会把同一批顶点在**其它材质**里的位置一起挪走。

**预览器要有两个开关**：`depth_le`（`<` / `<=`）和 `cull`（单面 / 双面，对齐 MMD 的 `0x01` 双面材质）。
没有这两个开关，你会对着自己工具的假象排查半天。

---

## 7b. ★★★ 绑定姿态对齐（bind conform）：修「走路两腿交叉成 X」

**症状**：模型进游戏能显示、能贴着地，但一走路两条腿绕错误的圆心摆动、互相穿插，
看起来像交叉成 X。**静帧预览完全正常**，只有播动画才暴露。

**根因**：MMD 骨架与 HOI4 标准骨架的**腿身比不同**，任何「整体相似变换」都无法同时对齐所有关节。
实测（薇斯纳）：源骨架腿:躯干 = **1.78**，HOI4 = **1.11**；源脚在 x=±0.31~0.56，
HOI4 骨架却要 x=±0.88~1.14。整体拟合后残留偏差：大腿根 0.84 / 膝盖 0.55 / 脚踝 0.77 / 脚尖 0.92。
蒙皮时每根骨**绕它自己的原点**旋转，而该原点离真正的腿有 0.8~0.9 远 → 腿绕错圆心摆动。

**怎么确认「骨架是硬契约、不是我们拟合错了」**：
- 同类模型（PRC/Keqing/Amber/Furina/Kokomi/Citlali）的骨架 rest 位置**逐字节一致**（偏差 0.000）；
- 它们自己的几何**就落在骨架值上**（Keqing 腿几何 x = 0.58/0.72/0.93，骨架 0.44/0.67/0.88）；
- PRC_infantry 自己的脚底就在 x≈±1.08。
脚本：`scripts/rig_check.py`（骨架一致性 + 「骨位置 ↔ 该骨主导顶点质心」距离，输出到报告）。

**解法**：绑定时每根骨都是纯平移 → `M_i·B_i⁻¹ = T(q_i − p_i)`，于是

```
v' = Σ w_i·(v + q_i − p_i) = v + Σ w_i·(q_i − p_i)
```

即**每个顶点按蒙皮权重加权平均各骨的位移向量 `disp_i = q_i − p_i`**，直接加到顶点上。
（这就是 Maya/Blender 里的 "bind pose conform"。）

**★★ 不参与对齐的骨要「沿父链继承位移」，绝不能原地不动**（本项目踩过，代价很大）：

身体整体被搬走（中轴 dy 达 −0.86），而这些骨留在原地 → 挂在它们上面的几何与身体脱节。
本项目最典型的受害者是**眼睛**：

| 对象 | 现象 |
|---|---|
| `左目先` / `右目先` | `目` 材质绑在这两根骨上，而 DENY 名单含 `"目"` → 权重 0 → 原地不动；脸皮 `颜` 绑 `頭`（参与对齐）被搬走 → **眼球陷进脸里**。游戏里表现就是「眼睛闭着」（只剩脸皮上画的睫毛线） |
| `睫`（睫毛） | 同样不动 → 闭眼线还在，加重「闭眼」观感 |
| 翅膀骨 / 长发骨 / 裙骨 | 同样会与躯干错位 |

**判据很反直觉**：`--no-conform` 的版本眼睛是**正常睁开的**，
只有做了对齐才变闭眼 —— 所以看到「某部位凭空坏掉」时要先怀疑 conform 的漏算骨。

**正确做法**：沿父链向上找**最近一个已对齐祖先**，继承它的 `disp`（刚性跟随）：

```python
resolved = cw > 0.0
for _ in range(64):                 # 父索引不一定排在子之前，多轮兜底
    changed = 0
    for i in range(n_b):
        if resolved[i]:
            continue
        j = pmx.bones[i]["parent"]
        if 0 <= j < n_b and resolved[j]:
            disp[i] = disp[j]
            resolved[i] = True
            changed += 1
    if not changed:
        break
```

同一条链上的骨继承**同一个**祖先的 disp → 整块几何刚性平移、形状不变 ✔
（眼睛跟 `頭`、翅膀/长发跟 `上半身` 或 `back_mid`、裙摆跟 `Hip`。）

⚠ **绝不能改用它们「自己的 disp」**：翼骨自己的 disp 达 4.118，会把整对翅膀拽成一个点。
也就是说 DENY 名单决定的是「不取自己的目标位」，**不是**「不动」。

**实现要点**：
- 权重表按**源骨名**判定，不是 HOI4 骨名；
- ⚠ **索引别混**：`disp` 数组按源骨（本例 550 根）索引，
  写 `if 0 <= b < n_b`（`n_b = len(pmx.bones)`）**不要**写成 `if 0 <= b < 33`
  （拿 HOI4 骨数去卡源骨索引，会让绝大多数顶点算不出位移，中位数位移 0.0000）。
- ⚠ **顶点循环里不能再写 `if hmap[b] < 0: continue`**：未映射到 HOI4 骨的源骨
  如今也有 disp（继承来的），跳过它们等于又漏一批顶点。
- 效果自检看**腿部几何 x 剖面**：对齐后 `LeftFoot` 质心 0.894 / 骨架 0.881（差 +0.013）、
  `LeftToeBase` 1.140 / 1.136（差 +0.005）。
- 另一个自检：**顶点位移中位数**。若只有 0.02 量级，说明大批顶点没吃到位移（漏骨）；
  本项目修好后是 **0.195**（550 根源骨中 97 根直接对齐、445 根靠继承）。

**代价（可接受，别过度优化）**：腿部被等比压缩 ~23%（腿身比 1.78 → 1.11），
腰/大腿根处有一段平滑过渡，大腿略变直、裙摆略走样。这是把长腿适配到 HOI4 比例的必然结果。

### ★★★ 位移场必须是「位置的光滑函数」，不能是「逐骨常量」（会撕开网格）

**这是 conform 最容易翻车的地方，本项目踩过：**

第一版实现是「每根骨一个常量位移 `disp_i = q_i − p_i`，顶点取 `Σ w_i·disp_i`」。
结果**大腿和小腿在膝盖处被撕开**（渲染可见断口 + 小腿整体外移）。
**静帧看不明显，放大腿部特写就很清楚。**

**根因**：相邻腿骨的目标位置相差极大 —— 实测

| 关节 | `disp_x` | `disp_y` |
|---|---|---|
| 大腿根 (`左足`→LeftUpLeg) | **+0.065** | −0.839 |
| 膝盖 (`左ひざ`→LeftLeg) | **+0.417** | −0.343 |
| 脚踝 (`左足首`→LeftFoot) | **+0.761** | +0.071 |
| 脚尖 (`左つま先`→LeftToeBase) | **+0.917** | 0.000 |

逐骨常量位移 = **分段常量位移场**。蒙皮权重在膝盖处从「腿骨」切到「膝骨」，
位移就**跳变 0.35~0.5** → 网格被撕开。

**修法**：对每条肢体链，把位移改成**沿骨轴位置的连续插值**：

1. 取该链的关节锚点 `(源骨拟合后位置 p_j, 目标 HOI4 位置 q_j)`；
2. 锚点按 y 升序排好，位移 `d_j = q_j − p_j`；
3. 每个顶点按自己的 y 做 `np.interp(y, ys, ds)` → 连续位移；
4. 与其它骨的位移按**蒙皮权重**混合（`w_leg` 与 `1−w_leg`），保证髋部过渡平滑。

**为什么这样就连续**：锚点间斜率实测几乎一致（0.184 / 0.173）→ 位移场近似一条直线
→ 腿变成**平滑地「外展 + 缩短」**，而不是「分段平移」。效果：膝盖断口消失，
走路仍不交叉（腿骨与腿几何仍然吻合）。

⚠ **锚点集合要包含映射到该链的全部源骨**（不止 4 个主关节骨，还有 `左足D`/`左ひざD`
这类变形骨），否则它们会退回逐骨常量位移，重新产生台阶。

**自检**：写个「按 y 分带统计腿部几何 mean x」的脚本（`scripts/leg_profile.py`），
看 `mean x` 随 y 是否单调平滑。有台阶就是一目了然的。

### ★★★ 只对腿做不够：中轴链也必须连续 —— 这是「没脖子 / 脖子太长」的根因

**症状**：腿修好之后，模型看起来「头和肩之间断开、脖子被拉长或干脆没了」。

**根因**：HOI4 骨架里**没有独立的脖子骨** —— `head` 的父直接是 `back_mid`（胸背），
`back_mid`(4.53) 到 `head`(6.50) 这 **1.97** 的区间全靠几何填充。
而 MMD 的 `首`（脖子）和 `頭`（头）**按名字规则都被映射到 `head`** 这一根骨上，
两者源位置相差 1.88，于是各自算出**不同的常量位移**。

中轴链实测（薇斯纳，源骨拟合后的落点 y → 需要位移 dy）：

| 源骨 | 落点 y | 映射到 | dy |
|---|---|---|---|
| センター | 3.90 | Hip (3.98) | +0.08 |
| 下半身 | 4.74 | Hip | **−0.75** |
| 腰 | 4.84 | Hip | **−0.86** |
| 上半身2 | 5.33 | back_mid (4.53) | **−0.80** |
| 首 | 6.14 | head (6.50) | **+0.37** |
| 頭 | 6.51 | head | −0.01 |

`上半身2`(−0.80) 与 `首`(+0.37) 之间**跳变 1.16** → 颈部几何被上下撕开：
下方胸段被压进胸腔、上方颈段被拉到颅底，中间留空 → 视觉上就是「头悬空、没脖子」。
（同一处还会让 `5.0~6.4` 这段的顶点数掉 40%~45%，可用剖面脚本量化。）

**修法**：把「肢体链插值」推广成通用的**部位链（chain）** —— 中轴也作为一条链参与：

```python
CHAIN_JOINTS = (
    (("センター", "Hip"), ("上半身", "back_mid"), ("頭", "head")),   # 中轴
    (("左足", "LeftUpLeg"), ("左ひざ", "LeftLeg"),
     ("左足首", "LeftFoot"), ("左つま先", "LeftToeBase")),           # 左腿
    (("右足", "RightUpLeg"), ...),                                   # 右腿
)
```
每条链：`骨集合 = {源骨 | hmap[骨] ∈ 该链目标骨 且 conform 允许}`，
锚点 = `(源锚点骨拟合后 y, 目标骨位置 − 源锚点骨拟合后 y)`，顶点按自身 y 做 `np.interp`。

修后中轴 dy = **+0.103 / −0.188 / 0**（一条平缓曲线），颈部几何完全恢复。

**⚠⚠ 关键约束：同一条链里，锚点的目标位置必须互不相同。**
若两个锚点目标是同一根骨（例如给 `首` 和 `頭` 各列一个都指向 `head` 的锚点），
线性插值会**退化成「把整段压到目标那一个高度上」**：

```
d(y) = d₁ + (d₂−d₁)·(y−y₁)/(y₂−y₁)，其中 d_k = H − y_k
⇒ target(y) = y + d(y) ≡ H        // 整条脖子被压成一层！
```
所以**不要**把 `首` 单列成锚点 —— 让它落在 `上半身..頭` 之间、由插值自然给出位置就对了。

**代价**：胸段被纵向压缩约 0.15（源 `上半身`→`頭` 跨 1.761，目标 `back_mid`→`head` 跨 1.974，
斜率 1.121 其实是**拉伸**；压缩主要发生在 `センター..上半身` 段，斜率 0.645）。可接受。

**诊断脚本**（都能独立跑，输出带自动避让的报告）：
- `scripts/neck_check.py <mesh...>` —— y 分带剖面 + **中轴半径剖面**（|x|<0.9，排除翅膀/手臂，
  「脖子 = 中轴最细处」）+ **按主导骨分组**。多传几个 mesh 即可横向对比。
- `scripts/spine_probe.py` —— 直接列出中轴各源骨的落点 y 与所需 dy，一眼看出台阶位置。
- `scripts/make_neck_sheet.py` —— 拼「未对齐 / 旧对齐 / 新对齐」三版颈部和走路对照图。
- ⚠ 用 PIL 拼图写中文标签会显示成方块（自带位图字体无 CJK），**标签一律用 ASCII**。

**另外两条排查经验**：
- **必须拿「未做对齐」的同名产物做对照**（`--no-conform` 或旧产物）。本项目就是靠这个
  一眼确认「断口是 conform 引入的，不是模型自带的」。
- 放大腿部特写渲染（`--zoom 2.8 --focus-y 1.7`）才能在交付前发现这类问题，
  全身图里看着只是「膝盖有点怪」。

---

## 7c. ★★ 用真实动画离线摆姿势渲染（验证绑定的唯一可靠手段）

**必须做**，否则只能在游戏里肉眼发现「走路交叉」这类问题。脚本：`scripts/pose_render.py`。

**`.anim` 格式**（与 `.mesh` 同一个 pdxasset 容器，`pdx_data.read_meshfile()` 直接能读）：
```
File → info → bone ×j + samples
  info: fps / sa(帧数) / j(骨数)
  每根骨: sa（通道类型串，由 s/t/q 组成，空串 = 未动画）、t(3)、q(4)、s(1)
  samples: t(3×N) / q(4×N) / s(1×N)
```
**四个致命约定**（每一条都实测验证过，任一条搞错模型就炸开）：

1. **采样排列是「帧主序」**：`offset = frame * num_bones_with_channel + slot_of_this_bone`
   （骨主序会让整个模型四散炸开）。
2. **四元数分量顺序是 (x, y, z, w)**，不是 wxyz。
3. **动画存的是每根骨「相对父骨的完整局部变换」，不是 delta**：
   `M_i = M_parent @ T(t) @ R(q) @ S(s)`，`world = 累积 M`，`skin_i = world_i @ B_i⁻¹`，
   `v' = Σ w_i·skin_{g_i}·v`。
4. **`s` 通道 = 0 表示整根骨缩没**（见 4b 节，这是翅膀消失的机制）。

**退化的 `tx` 必须替换**，否则求逆直接 `LinAlgError`：
`Left_Hand_node`（值 ~4.3e12）、`Root_node_1`/`Root_node_2`（全 0，det=0）。
判据 `abs(det) < 1e-6 or max|a| > 1e5`，处理办法是改用同前缀的下一根骨。

**判定读法对不对，用「已验证正常的同类模型」当标尺**：拿 Keqing（游戏内确认正常）
跑同一份 `GER_infantry_moving_rifle.anim`，走路姿势合理即说明读法正确
（`anim_convention.py` 枚举「四元数顺序 × 采样序」四种组合，只有 `xyzw + frame` 得到
解剖学合理结果：head y=6.26、脚尖 y≈0.2、左右脚镜像）。

**动画接线链路**（要知道游戏到底在读哪个文件）：
MOD `.gfx` 里 `id="move" type="GER_infantry_rifle_moving_animation"`
→ 游戏本体 `gfx/models/units/animation.asset` 定义该 animation 名指向 `.anim` 文件
（`GER_infantry_moving_rifle.anim`，41 帧 @ 30.75 fps，33 骨）。

---

## 8. 接入 MOD：`.gfx` 与 `.asset`

**`.gfx`（pdxmesh 定义）**
```
objectTypes = {
    pdxmesh = {
        name = "<Name>_infantry_mesh"
        file = "gfx/models/units/<DIR>/<Name>_infantry.mesh"
        animation = { id = "idle"   type = "GER_infantry_rifle_idle_animation" }
        animation = { id = "attack" type = "GER_infantry_rifle_attack_animation" }
        ... 共 27 组（idle/attack/support_attack/charge_rifle/charge_rifle_shoot/move/march_move/
                     retreat/death/long_idle01~05/cavalry_idle/cavalry_move/training/jumping_jacks/
                     pushup/guard_rifle/aim_exercise/bicycle_idle/bicycle_idle_2/bicycle_move/
                     bicycle_move_2/bicycle_retreat/bicycle_retreat_2）
    }
}
```
**抄同 MOD 里已跑通的同类模型**（本例抄 Keqing）最稳，动画 id 一个都别漏。
材质内嵌在 mesh 里，所以 pdxmesh **不需要 `meshsettings`**。

**`.asset`（entity 定义）**
```
entity = {
    name = "<Name>_infantry_entity"
    pdxmesh = "<Name>_infantry_mesh"
    default_state = "idle"
    state = { ... }                       # 抄参考实体
    attach = { name = "rifle1"  Right_Hand_node = "DOT_infantry_weapon_right_entity" }
    attach = { name = "rifle2"  Left_Hand_node  = "DOT_infantry_weapon_left_entity" }
    attach = { name = "rifle3"  Root_node_2     = "..." }
    attach = { name = "rifle4"  mid_back_node   = "..." }
    scale = 0.85
}
```
- `scale` 用同族模型的**中位值**。判据：把新模型顶点 **Y 范围**和同类比
  （本例 Keqing 7.62 / Amber 8.10 / Furina 8.24 / Kokomi 8.13 / Odetta 8.58，薇斯纳 8.07 → 取 0.85）。
- **★`attach` 的挂点骨与「收起装备」机制**：HOI4 就是靠把挂点骨的动画 `s` 通道设 0
  来**隐藏挂在该点上的武器/装备**（背枪、收枪、叼烟、点火）。
  所以 `attach` 落在 `mid_back_node` / `*_Hand_node*` / `Root_node_1` 上**是正常且正确的**
  （见 4b 节的隐藏统计表），但那根骨上**不能放自绘几何** —— 两者性质完全不同，别混。
  `propagate_state = { <名> = <状态> }` 的 `<名>` 既可能是 attach 名也可能是状态机名
  （原版就有 `infantry`），写校验时**只作提示、不要判定为错**。
- `attach` 允许指向**游戏本体**的实体（例 `cigarette_entity` / `lighter_entity` 在
  `Hearts of Iron IV/gfx/entities/units_infantry.asset`）→ 校验脚本必须**同时扫 MOD 与游戏本体**，
  只扫 MOD 会误报一堆"实体未找到"。
- **实体指派机制**：国家文件（`common/countries/*.txt`）只设 `graphical_culture`；
  `common/units/*.txt` 的单位类型定义**不含模型字段**。模型纯靠**实体命名约定**绑定：
  - `<TAG>_<单位类型>_entity`
  - 编号变体 `<TAG>_<单位类型>_N_entity`（原版实例：`generic_infantry_2_entity`、`ROM_infantry_2_entity`）
  → 所以只定义 `<Name>_infantry_entity` **不会自动生效**，要按上面的约定加 clone 才会被某国用上。

**校验脚本必须写**（本例 `validate_vysna.py`），逐项检查：
括号配平 → pdxmesh 的 `file` 存在 → 动画 id 有定义 → entity 引用的 pdxmesh 已定义 →
animation 全部有定义 → attach 目标实体在 MOD 中已定义 → **attach 挂点骨名存在于 mesh 骨架**。
全绿才算接线完成。

---

## 9. 交付前的最后三件事

1. **从"部署后"的文件再渲染一次**（不是从产物目录），确认部署这一跳没出错。
2. 两种深度规则都渲一遍，比较差异。
3. 检查三角数落在同 MOD 已用模型的区间内；`scale` 与 Y 范围对上。

## 附：脚本清单

| 脚本 | 作用 |
|---|---|
| `pmx_parse.py` | PMX 2.0 纯 Python 解析器（含 IK link 正确实现） |
| `pdx_write.py` | `.mesh` 二进制写出器（numpy；roundtrip 逐字节一致） |
| `dds_encode.py` | 纯 numpy DDS BC1/BC3 编码器（含 mip 链） |
| `pdx_data.py` | GPL，读 `.mesh` / `.anim`（来自 MahdiBaghbani 的 `io_pdx_mesh` fork） |
| `render_preview.py` | 软件光栅化预览器（带 `depth_le` / `cull` 开关） |
| `vysna_build.py` | ★完整参考实现：PMX → mesh + 图集 + DDS + **bind conform** + 隐藏骨自检 |
| `pose_render.py` | ★★用真实 `.anim` 摆姿势渲染（帧主序 + `xyzw` 四元数；退化 `tx` 自动替换） |
| `anim_convention.py` | 枚举「四元数顺序 × 采样序」四种组合，判定 `.anim` 读法 |
| `anim_hidden_bones.py` | 扫一遍动画，统计哪些骨 `s` 恒 0（= 会被隐藏，不能挂几何） |
| `anim_scales.py` | 列出单个动画里每根骨的 `s` 取值 |
| `rig_check.py` | 骨架一致性 + 「骨位置 ↔ 该骨主导顶点质心」距离（查腿身比错配） |
| `eye_bone_check.py` | ★列出某材质绑的骨 —— 查「眼睛不显示/某部位与身体错位」的第一入口 |
| `eye_uv_region.py` | 把材质 UV 三角形画回源贴图（判断采样区对不对） |
| `eye_uv_atlas.py` | 把材质 UV 包围盒画回**图集**，用脸皮当标尺验证图集 UV 重映射 |
| `eye_bbox.py` | 从最终 mesh 按材质分段量几何包围盒（含 z，判断谁挡谁） |
| `eye_iso.py` | 逐层渲染 face 组材质，定位遮挡责任层 |
| `eye_tex_big.py` | 放大并排眼睛相关源贴图（肉眼看睁眼/闭眼内容在哪张） |
| `make_eye_sheet.py` | 拼「未对齐/旧版/新版」脸部 + 走路对照图 |
| `neck_check.py` | ★y 分带剖面 + 中轴半径剖面 + 按主导骨分组（查「没脖子」类问题） |
| `spine_probe.py` | ★列出中轴各源骨的落点 y 与所需 dy —— 一眼看出位移台阶 |
| `make_neck_sheet.py` | 拼「未对齐/旧对齐/新对齐」颈部+走路对照图（标签须用 ASCII） |
| `leg_profile.py` | ★按高度分带统计腿部几何 mean x —— 查 conform 位移场的台阶/断口 |
| `conform_probe.py` | 打印各源骨的 `disp = q − p`（决定哪些骨必须排除出 conform） |
| `wing_diag.py` | 逐项拆解某根骨的 `tx` / 动画通道 / 摆姿势后顶点云（查「几何塌缩成一点」） |
| `make_leg_sheet.py` | 拼「未对齐 / 旧对齐 / 新对齐」三版腿部对照图 |
| `wing_check.py` | 量化指定骨驱动的顶点云在 bind 与各帧的包围盒 |
| `alpha_check.py` | 逐材质采样源贴图 alpha（区分「真透明」与「黑块假象」） |
| `coincident.py` | 按三角形质心找「几何重合的叠层材质」 |
| `face_mats.py` | 列出某组材质的贴图 / draw_flag / 面数 / 是否剔除 |
| `eye_only.py` | 逐材质单独渲染（定位遮挡责任层） |
| `eye_push2.py` | 眼球前推量扫描 |

---

## 9. 批量转换多个模型（多角色流水线）

`vysna_build.py` 本体是「单模型」设计，但加了三处通用化后就能直接吃任意原神系 MMD：

| 通用化点 | 作用 |
|---|---|
| `--pmx <绝对路径>` | 指定源文件（默认仍是 `SRC/薇斯纳.pmx`） |
| `mat_group_of(nm)` | 材质名 -> body/face/hair 的**启发式**兜底（精确表命中不了就走它） |
| `eye_forward(nm)` | 模糊识别「完整的眼」层（眼白/瞳/高光/眉/睫一律不推） |
| `EXCLUDE_EXACT` | **精确名**剔除集合。必须的：子串表会把 `目` 命中到 `目2`、`手` 命中到 `手套` |

驱动脚本 `pmx_batch.py` 的流程：
1. **自动检测叠加层**：① 贴图采样区**近全透明**（≥95%）② 与「更早绘制」的材质**几何重合**（≥50%）
   且**大面积透明**（≥70%）。这两条能自动抓住 `髮+ / 前髪+ / 后髮+ / 照れ / 手` 这类 MMD 叠层。
2. 叠加**每模型精确剔除表**（人工判定的那几条）。
3. 设 `sys.argv` 后直接调 `vysna_build.main()`。
`--dry` 只输出检测结论、不构建 —— 先跑它，剔错东西一眼可见。

### ★ 判断「某材质是不是眼睛」只能靠渲染，不能看贴图
把材质的 UV 包围盒裁成贴图块来看**会误判**：虹膜放大后长得像布纹/金属饰件，
据此我差点把心海、妮露的眼睛当装饰件删掉。正确流程是
`eye_probe2.py`（列出眼部材质 + UV 区域 + 中心色）→ **真的渲染一张脸**
（`render_preview.py --views front --zoom 5.5 --focus-y <头高>`）→ 再定论。

各角色「眼睛在哪一层」完全不同（有的用 `目.png` 整图，有的借用 `髮.png` 的一小块，
有的眼睛在 `目2` 里而另有一个 `目` 指向布料）—— **每个模型都要单独确认一遍**。

### 批量时另外两个陷阱
- **单模型专属的剔除项不要带进批量**：薇斯纳的 `结晶`/`头饰` 是那**一个**模型的定制需求，
  套到少女身上会删掉她的黑纱头饰。批量时把这类项从基线名单里摘出来。
- **命名冲突**：部署前先 `ls gfx/models/units/`。已有同名目录时加后缀（本次用 `V2`），
  **绝不覆盖**别人已经接入、可能已被国家引用的模型。

### 注册文件写成新文件，别去改大文件
把 pdxmesh / entity 写进新建的 `gfx/entities/<批次名>.gfx|.asset` 即可（HOI4 会加载该目录下所有文件）。
好处：① 绕开本工作区「不可覆盖已存在文件」的限制；② 不碰用户在维护的 `DOT_All_Entity.*`。
写完用 `validate_v2.py` 校验：括号配平 / `pdxmesh.file` 存在 / 贴图齐全 /
`entity->pdxmesh` 引用 / state 的 animation id 命中 / **有无顶点绑到会被 s=0 隐藏的骨**。

### 本批次新增脚本
| 脚本 | 作用 |
|---|---|
| `pmx_batch.py` | ★多模型批量转换驱动（自动叠加层检测 + 每模型精确剔除表，`--dry` 预演） |
| `eye_probe2.py` | ★列出各模型眼部材质 + UV 区域 + 中心像素色（判眼睛的第一步） |
| `validate_v2.py` | ★通用注册校验（6 类检查，一次覆盖整批） |
| `batch_sheets.py` | 批量出「四视图 + 走路帧」交付拼图 |

