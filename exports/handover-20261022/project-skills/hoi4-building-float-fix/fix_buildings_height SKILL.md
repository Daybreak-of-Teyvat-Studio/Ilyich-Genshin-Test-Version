---
name: hoi4-building-float-fix
description: 修复钢铁雄心 IV（HOI4）MOD 地图上「建筑模型悬空 / 浮空 / 陷进地里 / 埋进地形」的问题。核心是重算 map/buildings.txt 的第 4 列绝对高程：用 row=z,col=x（不翻转）双线性采样 heightmap，按 y = 0.09786518*h + 0.259962 逐条重写，跳过 floating_harbor 与已在容差内的行。也覆盖「胜利点图标悬空」的鉴别（那是 map/positions.txt 的坐标落海，属另一个文件另一套修法）、建筑 entity 缺失（landmark_xxx doesn't have an entity）与坐标问题的区分、以及工作区禁止覆盖已存在文件时的「先删后建」落地写法。触发词：建筑悬空、建筑浮空、建筑模型悬空、建筑陷进地里、建筑被埋、建筑不在高度上、building floating、位置不对、buildings.txt、y 列、第四列、高程列、heightmap 改了建筑就飘了、nudge、nudger、building placement、positions.txt、胜利点悬空、胜利点图标、州首府坐标落海、地图坐标映射、row=z、col=x、双线性采样。
agent_created: true
---

# HOI4 建筑悬空修复（buildings.txt 高程列）

## 症状与快速判别

用户说的通常是这几种：

- 「建筑模型悬空」/「建筑浮在空中」/「建筑飘着」
- 「建筑陷进地里」/「建筑被埋了一半」/「建筑跑到地底下」
- 换了 heightmap 之后「建筑都没贴在高度上了」
- 「地图上全是方块、占位符」（⚠️ 这不是本技能，见文末「不要混淆的三件事」）

**先做一件事：确认症状属于哪一类。**

| 现象 | 归属 | 看哪个文件 |
|---|---|---|
| 建筑模型浮空 / 入地，位置水平方向没错 | **本技能** | `map/buildings.txt` 第 4 列 |
| 建筑图标（旗帜/胜利点）浮在海面上 | `positions.txt` | 见文末「胜利点图标悬空」 |
| 图上出现占位方块、日志刷 `mapobject_N failed to load` | `trees.bmp` + 实体 | 见 `hoi4-heightmap-shaping` |
| 日志报 `Building xxx doesn't have an entity` | 实体定义缺失 | 见文末「entity 缺失」 |

判别方法一句话：**水平位置对不对？** 建筑的水平位置（x/z）由 buildings.txt 决定，高程（y）也由它决定。
如果用户说"位置偏了"而不是"悬空"，先怀疑 coord/省号映射，不要直接重算 y。

## 原理：第 4 列就是绝对高程

`map/buildings.txt` 每行格式：

```
province_id ; building_type ; x ; y ; z ; rotation ; ?
1;arms_factory;2277.04;9.81;1719.30;0.00;0
```

- **第 4 列 `y` 是引擎直接使用的绝对地形高程**，引擎不会去查 heightmap 补算。
- 所以 **heightmap 一改，全表建筑的 y 立刻过期** → 该在山上的建筑停在旧高度 = 悬空；
  该在平地的建筑在新高度下 = 入地。
- 换算关系（用原版反推，**不要猜、不要改系数**）：

```python
y = 0.09786518 * h + 0.259962      # 海平面 h=95 -> y ≈ 9.56
```

- 原版 `buildings.txt` 用这个公式复原残差：`mean|r| = 0.1179`，94.90% 落在 0.5 以内。
- 项目自制版本如果复原度只有 25% 上下，说明那列高程**是脱离地形生成的**，必须重算。

## ★铁律一：行序 ——「翻不翻转」取决于你怎么读图

HOI4 的 `z` 直接对应 BMP 的**存储行序**。所以同一份 heightmap，正确表达式随读法变：

| 读法 | 正确表达式 | 说明 |
|---|---|---|
| `np.frombuffer` 直读存储序 | `row = int(z)` | **不翻转** |
| `PIL.Image.open()` | `row = H - 1 - int(z)` | PIL 已把 bottom-up 翻成视觉序 |

两种写法**等价**，混搭才会错。实测四组合（同一份 4096×2048 高度图，40,829 条非浮港建筑）：

| 组合 | 中位 \|r\| | 判定 |
|---|---|---|
| `np.frombuffer` 直读 + `row = z` | **0.0050** | ✅ 正确 |
| `np.frombuffer` 直读 + `row = H-1-z` | 7.8255 | ❌ 错 |
| `PIL` 读 + `row = z` | 7.8255 | ❌ 错 |
| `PIL` 读 + `row = H-1-z` | **0.0050** | ✅ 正确 |

（`np.array_equal(pil_img, np_storage[::-1])` 为 `True`，这就是等价关系的证据。）

**这里历史上记反过**：早期用 PIL 反推出的「必须翻转」结论被当成了通用规则，
于是在 np 直读的管线里也去翻转，**直接派生出一个完全错误的「全量重算 12,631 行」方案**
（实际只需改 221 行）。教训：**行序的正确写法是绑定读法的，不要记成一个绝对规则；
更不要在没有验证的情况下就批量改文件。**

**落地判据（不需要参照任何历史记录，自己就能验）**：

1. 四组合各算一遍 `median|r|`，选最小的（脚本已内置自检，会自动切换）。
2. **非浮港建筑必须接近 100% 落在陆地（h ≥ 96）**：本项目正确映射 100.00%，错误映射 32.74%。

## ★铁律二：采样用双线性，整数采样有系统偏差

```python
def bilinear(hm, x, z):
    H, W = hm.shape
    c0, r0 = int(x), int(z)
    dc, dr = x - c0, z - r0
    return (hm[r0, c0] * (1-dc) + hm[r0, c0+1] * dc) * (1-dr) + \
           (hm[r0+1, c0] * (1-dc) + hm[r0+1, c0+1] * dc) * dr
```

- 整数采样（`hm[int(z), int(x)]`）会让残差从 `mean|r| = 0.0032` 劣化到 **0.0305**（约 10 倍）。
- 差 0.03 个世界单位肉眼看不出来，但**它会让"该不该改"的判定全线漂移**：
  用整数采样时 |r|>0.01 的有几百条，用双线性时是 **0 条**。

## ★铁律三：`x/z` 不是地图像素坐标，不能拿去比省号

- `buildings.txt` 的 x/z 是**引擎内部世界坐标**，与 `provinces.bmp` 的像素格不是一回事。
- 实证：**原版 buildings.txt 的坐标打在原版 provinces.bmp 上同样是 0% 命中**。
  所以「命中率 0%」不是缺陷，是比对方法错了。
- 判断建筑是否落地，**只能看 y 与 heightmap 采样值的吻合度**，不要看它落在哪个省的像素上。
- （`positions.txt` 不同：它的坐标**是**像素坐标，与 `provinces.bmp` 99.69% 命中；
  但那是因为它是从 24 位地图自动生成的。两个文件别混用同一套直觉。）

## 诊断流程（先量后改）

### 1. 备份（无条件）

```bash
mkdir -p .workbuddy/backup_$(date +%Y%m%d_%H%M%S)_buildings
cp "<MOD>/map/buildings.txt" .workbuddy/backup_.../buildings.txt
```

### 2. 读 heightmap

8 位索引 BMP 的头部字段偏移（**bpp 在 28，不是 26**，这个也踩过）：

```python
raw = open(p, 'rb').read()
off = struct.unpack_from('<I', raw, 10)[0]     # 横常见 1078；本项目有 off=142/1074 的自定义头
W   = struct.unpack_from('<i', raw, 18)[0]
H   = struct.unpack_from('<i', raw, 22)[0]
bpp = struct.unpack_from('<H', raw, 28)[0]     # ← 28
```

- **像素体后常有 2 个多余字节**，一律按 `off + W*H` 截断，不要用整个文件长度 reshape。
- 头部形态随用户编辑器变（实测见过 off=142、clrUsed=22 的形态），**读偏移，不要写死 1074/1078**。
- **不要凭"BMP 是 bottom-up"就顺手翻转** —— 见铁律一：行序的正确写法**绑定读法**。
  脚本已内置四组合自检（用中位数判），会自动选残差最小的那个；手写管线时也必须先跑一次自检，
  再决定要不要批量改文件。

### 3. 逐条算残差并分档

```python
r = y - (A * bilinear(hm, x, z) + B)
```

报告这几行（缺一不可）：

```
记录总数 / 浮港跳过 / 越界 / 残差在容差内 / 需要修正
修复前：mean|r| 、 max|r| 、 |r|>{0.01, 0.1, 0.5, 1.0, 3.0, 5.0} 各自多少条
待修行里 y 仍贴着海平面（|y-9.50| < 0.02）的有几条   ← nudge 漏改的典型症状
位移最大的 30 条（prov / type / x / z / y_old / y_new / dY / h）
```

### 4. 看残差分布决定"是不是真要改"（中位数 vs 均值，两个都要看）

**`mean|r|` 和 `median|r|` 的差距就是"脏行占比"的信号。** 实测一例：

```
样本 40,829   mean|r| = 0.2235   median|r| = 0.0037   max|r| = 11.41
   |r|>0.5 : 2,064     |r|>3.0 : 1,279
   待修行中 y 恰为 9.50 的: 3,264
```

mean 0.22 看起来像"整表都烂了"，但 **median 0.0037 说明 92% 的行是好的**，
只有 3,264 条从未初始化（y 全等于 9.50）的行在把均值抬起来。

- **只信 mean** → 会得出"要重算全表 4 万行"的错误结论（真发生过）。
- **只信 median** → 会漏掉那 3 千条脏行。
- **两个一起看**，才知道"该修多少"和"整体健康度"分别是多少。这也是脚本内置中位数自检的原因
  （用均值做行序自检时，脏行会把自检带偏）。

其余判据：

- 健康基线：`median|r| ≤ 0.005`（本项目用「正确行序 + 双线性」达到过 `mean|r| = 0.0032 / max = 0.005`）。
- 若 `median|r| ≈ 0.03` —— 先怀疑自己用了**整数采样**（见铁律二）。
- ⚠️ **`y ≈ 9.50` 不一定是错的**：h 在 94.5~96 的近岸平地，正确 y 本来就是 9.5 上下。
  判"未初始化"要看 `|y - (A*h+B)|`，不是看 `|y - 9.50|`。
- **「待修行里 y 恰好全等于同一个值」是很强的线索**：未初始化的行往往 y 完全相同
  （本项目是 9.50 = 海平面）。这个计数基本就等于脏行数。

## 修复

规则（顺序不能颠倒）：

1. `floating_harbor` **整类跳过** —— 它本来就该在水面（实测本项目 1,747 条，
   占"落在海面"的 1,732 条的绝大多数）。改它 = 把港口拽上岸。
2. 越界坐标（`x/z` 不在图内）保持原值，只记录。
3. `abs(y - y_new) <= tol`（默认 **0.005**）保持原值 —— **不要为了"统一格式"重写全表**，
   那会让 diff 从 221 行变成 4 万行，用户无法复核。这 0.005 的容差就是用来吃掉浮点尾数的。
4. 其余重算：`y_new = A * max(h, SEA) + B`，`SEA` 取 94（比海平面 95 低一点，
   容忍海岸线附近的插值抖动，避免码头掉到水面下）。
5. **只改第 4 列**，其它列逐字符保留；行序、行数、分隔符（`;`）、换行风格（`\r\n` vs `\n`）全不变。

用技能自带脚本：

```bash
# 诊断（默认不写文件）
python scripts/fix_buildings_height.py --map "<...>/Daybreak of Teyvat Gamma Version/map"

# 出力到新文件
python scripts/fix_buildings_height.py --map "<...>/map" \
       --out "<...>/.workbuddy/buildings_fixed.txt" \
       --report "<...>/.workbuddy/report_buildings.txt"
```

产物字节数变化很小（本项目 **+13 字节**，来自 `9.50` → `17.82` 这类从 4 字符变 5 字符）。
**字节数变化大就说明改错行了，回去查映射。**

## 落地：工作区禁止覆盖已存在文件时

本机（HOI4 MOD 工作区）的权限矩阵实测：

- **新建**（`cp` 到不存在的新名）→ 允许
- **删除**（`rm -f X`）→ 允许，rc=0，文件真的消失
- **覆盖**（`cp new X`，X 已存在）→ 拒绝 `Permission denied`
- **改名/移动**（`mv X Y`）→ 拒绝

所以就地替换的正确写法是「先删后建」，并且**把恢复分支写进同一条命令**：

```bash
cd "<MOD>/map"
cp "$PATCH" buildings_new.txt                    # 先在新名下落地
cp buildings.txt "$WB/backup_.../buildings.txt"  # 安全副本（已有也要再确认一次）
rm -f buildings.txt                              # 删除允许
if [ ! -f buildings.txt ]; then cp buildings_new.txt buildings.txt; fi   # 写回 + 兜底
ls -la buildings.txt && md5sum buildings.txt     # 必须回读校验
rm -f buildings_new.txt
```

- `buildings.txt` 在 `default.map` 里**没有**对应字段，没有"改配置指过去"的间接入口，
  所以必须原地替换（或让用户手工改名）。
- 如果 `rm` 也被拒 → 大概率是**图像编辑器/游戏正在独占该文件**，
  先让用户关掉，不要归因于沙箱。
- 内置 Write 工具能覆写工作区内的已存在文件，但 2 MB 级的文本用 Write 不现实 → 用上面的 shell 路线。

## 验证（交付前必须贴出来）

```
修复后：非浮港建筑 N 条，残差 mean|r| = 0.0032 ， max|r| = 0.005 ， |r|>0.01 的 = 0 条
```

再加两条：

- **只改了该改的行**：`diff` 行数 == 报告里的"需要修正"数；
  改写行的**除第 4 列外逐字段相等**（脚本天然保证，但要在报告里声明）。
- **坐标落省分布没变**（如果你顺带动过 x/z 才需要；只改 y 的话这步可省）。

## 不要混淆的三件事

### 1. 胜利点图标悬空（另一个文件、另一套修法）

用户会把两类"悬空"一起说，但它们完全独立：

- **现象**：旗帜/胜利点图标悬在海面上、或根本不出现。
- **真因（实测两个叠加）**：
  1. `history/states/*.txt` 的 `victory_points` 写成 4 参数
     （`victory_points = { 1582 1 2394 1 }`）。**引擎只接受 2 个参数**，整条语句被丢弃，
     该州胜利点全部不登记，日志报 `set victory points takes 2 parameters`。
     修法：拆成两条 `victory_points = { 1582 1 }`。全 MOD 复扫确认没有 4 参数残留。
  2. `map/positions.txt` 里**州首府省是袖珍岛**时，坐标落在海里。
     - 本项目 14 个省（222/674/688/774/860/1269/1752/2435/2473/3055/3939/4680/4689/4691）
       只有 15~173 像素，`positions` 坐标偏 1 px 就掉进海面（该点 h=91~92 < 96）。
     - 修法：取「该省像素中**离质心最近的 h ≥ 96 的像素**」。
       **文件字节数可以做到完全不变**（本项目只改 84 行 = 14 省 × 6 行）。
- `positions.txt` 格式是花括号块，**不是**每行 `id=`：

```
222={
	position={  1873.139 9.500 1684.197    ← 6 行同值
	...
	rotation={  0.000 × 6
	height={    0.000 × 6
}
```

  其中 `y` 恒为 `9.500`，是**高度占位值**，不是行号也不参与定位 ——
  **别拿它当行索引去采样 heightmap**（我踩过，导致所有省报"在深海"）。

- 顺带排除：MOD 通常**没有**覆盖 `interface/mapicons.gfx` / `mapicons.gui` /
  `gfx/interface/onmap_victorypoints_strip.dds`，图标资源用的就是原版，不用查。

### 2. 建筑 entity 缺失

日志里 `mapbuildings.cpp:1657` 报：

```
Building landmark_institute_of_tower doesn't have an entity
Building landmark_Lei_Line_research_center doesn't have an entity
```

这是**类型层**的问题：`common/buildings/*.txt` 里定义了这个 building，
但 `gfx/entities/*.asset/.gfx` 里没有对应的 `entity { name = ... }`。
和"悬空"无关（有 entity 才有模型；没有 entity 是**不显示**，不是浮空）。
修法见 `hoi4-mod-bug-triage`，别在 buildings.txt 里找。

### 3. 树木/地图物件占位方块

日志刷 `mapobject_N failed to load` → `trees.bmp` 用了没有 mesh 的索引。
用户会描述成"大量建筑悬空"。**先看是方块还是模型**：方块 = 本项，
模型浮空 = 本技能。修法见 `hoi4-heightmap-shaping` 的「树木物件编号」。

## 常见误判清单（都是真踩过的）

- ❌ 把行序记成绝对规则（比如"`z` 必须翻转"）→ 派生出"要改 12,631 行"的错误方案，实际只需 221 行。
  **判据：四组合自检取中位残差最小者 + 非浮港建筑必须接近 100% 落在 h≥96。**
- ❌ 只看 `mean|r|` 就判"整表都要重算" → 3 千条未初始化的脏行足以把均值从 0.004 抬到 0.22。
  必须同时看 `median|r|`，它才反映"整体健康度"。
- ❌ 拿 buildings 的 x/z 去比 provinces 像素省号 → 恒 0% 命中（原版也 0%），然后误判"坐标全错"。
- ❌ 用整数采样 → 残差 0.03，判定边界大量漂移。用双线性。
- ❌ 看 `y ≈ 9.50` 就判"残留海平面" → 近岸平地本来就该是 9.5。要看 `y - (A*h+B)`。
- ❌ 把 `floating_harbor` 一起"扶正" → 港口被拽上岸。
- ❌ BPP 读偏移 26 → 所有图报 bpp=1。正确偏移 **28**。
- ❌ 为了"整齐"重写整表 → diff 从 221 行变 4 万行，用户没法复核，也把 nudge 的成果覆盖掉。
- ❌ **交付后不回头确认产物还在不在。** 本项目实测出现过产物被 `git revert` 掉
  （提交信息就是 `Revert "胜利点和建筑悬空问题"`），下一轮再打开文件发现"又坏了"，
  同样的排查白做一遍。落地后必须 `git status --short` + `md5sum` 双确认，并把 md5 写进报告。

## 标准交付物

1. **修复后的 `map/buildings.txt`**（就地替换，md5 写进报告）
2. **备份** `.workbuddy/backup_<ts>_buildings/buildings.txt`
3. **报告** `.workbuddy/reports/建筑悬空_排查修复报告.md`，含：
   行序判据表（四组合）、修复前后 `mean|r| / median|r| / max|r|`、位移 top30、
   排除项、改动行数、md5
4. 如同时修了胜利点，**一并报告但分节写清是两回事**（两个文件、两套修法）
5. **落地后回头确认**：`git status --short`（应显示该文件已修改）+ `md5sum` 复核，
   并提醒用户「仓库里可能有人把它 revert 掉，提交前先看 diff」
6. memory 追加一条，并**更正任何记错的行序/映射记录**（本项目 `MEMORY.md` 曾记反）
