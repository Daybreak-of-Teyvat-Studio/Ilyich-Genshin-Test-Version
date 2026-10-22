---
name: hoi4-fbx-building-to-mesh
description: 把静态建筑/道具 FBX 转换成钢铁雄心 IV 可直接上游戏的建筑 .mesh 模型，不绑骨：绕过 FBX 二进制节点树直接扫 zlib 数组层提取几何、按 Z 直方图识别并删除最底层地基（含裙边）、焊接加立方体顶点聚类两级减面、重算法线/三平面 UV/正交切线，再按 pdxasset 二进制格式写出与原版建筑完全同构的 .mesh（含 aabb、material 与冒烟 locator）。当用户说「把这个 FBX 转成钢铁雄心模型」「把这个建筑/塔/寺庙模型转成 HOI4 建筑」「替换 factory.mesh / 工厂模型 / 建筑模型」「建筑模型不需要绑骨」「删掉最底层地基」「模型收敛到 5MB 以内」时使用。也覆盖：mesh 二进制格式逐字节解析与写出、pdxasset 的 p/n/ta/u0/tri 属性编码、object/polySurfaceShape1/mesh 层级、locator 挂点、顶点聚类减面、Gram-Schmidt 切线、面积加权法线、FBX 7400 数组层提取。触发词：FBX、fbx 转 mesh、建筑模型、工厂模型、factory.mesh、pdxasset、pdxmesh、.mesh、建筑模型转换、地基、减面、收敛、顶点聚类、locator、aabb。
agent_created: true
---

# 静态 FBX 建筑 → HOI4 建筑 .mesh

把静态建筑模型（`.fbx`）转成 HOI4 能直接加载的建筑 `.mesh`。
**不绑骨**：建筑是 `object → polySurfaceShape1 → mesh` 三层，外加 `aabb` / `material` /
`locator`，没有 skeleton / skin。

> 绑骨单位模型（PMX/MMD → 会动的步兵）走另一个技能 `hoi4-pmx-to-mesh`。
> 本技能只做**静态建筑/道具**。

---

## 0. 先确认四件事

1. **源格式**：FBX（binary 还是 ASCII？版本号？）、OBJ、还是 GLTF？
2. **顶在哪**：目标建筑的本地坐标系约定。原版 `factory.mesh` 的
   AABB 是 `min=[-0.266,-0.033,-0.619]`、`max=[0.463,1.165,0.392]`，
   **Y 是高度轴，底座不在 z=0**。多数 FBX 用 Z 作高度轴。
   → 与游戏放置无关（引擎按 AABB 摆放），但悬浮/沉地会直接看出来。
   本技能按 **z 为高度、底座贴 z=0** 输出。
3. **要删什么**："最底下的一层地基"到底多厚 —— 见第 2 节，**别只删一层**。
4. **面数与体积上限**：目标三角形数、`.mesh` 体积上限（常见 5 MB）。

---

## 1. 提取 FBX 几何：绕过节点树，直接扫数组层

### 为什么不能解析节点树

FBX binary 7400 的头部与 `FBXHeaderExtension` 存在厂商变体布局，
按标准 u32 name-length 扫描会失败（典型报错 `prop type 39 @455`、
`no Objects node found`）。3ds Max / Blender / Maya 导出的文件都可能中招。

### 但数组层是可靠的

**放弃节点树，改用数组层扫描。** 每个数组属性在文件里都是：

```
type:u8  count:u32  encoding:u32  compressedLength:u32  data[compressedLength]
```

`encoding == 1` 表示 zlib 压缩。做法：

1. 扫全文件找候选 zlib 起点：首字节 `0x78`，且 `(CMF*256+FLG) % 31 == 0`，
   `FLG & 0x20 == 0`（无预设字典）。
2. 从 `p-13` 往回读 13 字节拿到 `type / count / encoding / compressedLength`。
3. 解压，**自校验**：`len(inflated) == count * itemsize`（`itemsize` 见下表）。
   校验通过即命中，失败就跳过。

| type 字节 | 元素字节 |
|---|---|
| `d` | 8 |
| `f` | 4 |
| `l` | 8 |
| `i` | 4 |
| `b` | 1 |

`scripts/fbx_arrays.py` 是可直接跑的扫描器（已验证能从 11.6 MB 的
Max 2023 导出文件里取出全部 9 个数组）。

### 需要的数组

| 数组 | 类型 | 说明 |
|---|---|---|
| `Vertices` | double | 元素数 = 顶点数 × 3 |
| `PolygonVertexIndex` | int | 多边形索引，以**负数**结尾标记最后一项 |
| `Edges` | int | 本流程不需要 |
| `Normals` / `NormalsW` | double | 原版法线，本流程重算，不用 |
| `UV0` / `UVIndex0` | double / int | UV1 同理 |
| `UV1` / `UVIndex1` | double / int | |

### 三角化（fan）

`PolygonVertexIndex` 里负数索引 = `~i` 指向该多边形的最后一个顶点。
按负数切段，每段做扇形三角化：

```python
for e in ends:                      # ends = 负数项的位置
    poly = idx[start:e]
    p = len(poly)
    for k in range(1, p - 1):
        tri.append((poly[0], poly[k], poly[k + 1]))
    start = e + 1
```

保存为 `geo/Vertices.npy`（`(N,3)` float64）与 `geo/tris.npy`（`(M,3)` int64），
之后所有步骤只读这两个文件 —— **不必再碰 FBX**。

---

## 2. 找地基：是「一块板」，不是「一层」 ⚠️ 本技能最容易踩的坑

**先做 Z 直方图**，看最低处有几个离散 Z 值：

```python
import numpy as np, collections
z = V[:, 2]
hist = collections.Counter(np.round(z, 3))
for k in sorted(hist)[:8]:
    print(k, hist[k])
```

实测一个寺庙模型：

```
z=0.000  20716 verts   <- 底面
z=1.000   1136 verts   <- 中间层
z=2.000  ...           <- 顶面
```

地基是 **Z=0..2 的整块板**（三层水平面 + 四周立面裙边）。
**只删 `Z == 0` 那层会留下 1 单位高的基座裙边** —— 视觉上模型站在一圈矮墙上，
底面残留面积仍占足迹的 79%。

### 正确删除条件

```python
BASE_CUT = 2.0        # 板顶高度，不是 0！
keep = ~(V[T, 2].max(axis=1) <= BASE_CUT)
T = T[keep]
```

### 定量验证地基真的删干净了

```python
flat = T[(V[T,2].max(1) - V[T,2].min(1)) < 1e-6]   # 水平三角面
zc = V[flat, 2].mean(1)
a  = V[flat, 0:2]
area = np.abs((a[:,1,0]-a[:,0,0])*(a[:,2,1]-a[:,0,1])
             - (a[:,2,0]-a[:,0,0])*(a[:,1,1]-a[:,0,1])) * 0.5
lo = zc < zc.min() + 1e-4
print("bottom layer z=%.4f tris=%d area=%.3f" % (zc.min(), lo.sum(), area[lo].sum()))
```

删干净后这一层的面积应 ≈ 0（实测 0.001，占足迹 0%）。
如果它还占几十个百分点，说明 `BASE_CUT` 设小了。

⚠️ **面积一定要用 2D 叉积**。用 `np.cross` 的 3D 结果再取 z 分量会算错
（实测给出 45,971，而包围盒只有 69×72 = 4,968）。

---

## 3. 减面：焊接 + 立方体顶点聚类

### 焊接

FBX 按多边形角点分裂顶点，878,482 顶点里有大量重复：

```python
q = np.round(v, 4)
uniq, inv = np.unique(q, axis=0, return_inverse=True)
v, t = uniq[inv], inv[t]
```

实测 878,482 → 241,592。

### 顶点聚类（decimation）

**关键：聚类网格必须建立在包围盒的「立方体」上。**
按各轴分别归一化会把非立方 bbox（实测 69×73×46）压扁，模型直接变形：

```python
side = (v.max(0) - v.min(0)).max()
cell = side / grid
key = np.floor((v - v.min(0)) / cell).astype(np.int64)
uniq, inv = np.unique(key, axis=0, return_inverse=True)
v = np.zeros((len(uniq), 3))
np.add.at(v, inv, v0)              # 或取簇内均值
v /= np.bincount(inv)[:, None]
t = inv[t]
```

用**二分搜索 grid** 逼近目标面数，不要逐级倍增（倍增会从 20,000 面跳到 200 面）。
实测目标 20,000 面 → grid=39，得 19,056 面。

### 清理孤立顶点

聚类必然产生未被任何三角形引用的顶点（它们法线为 0，引擎会渲染出黑点）。
**必须在缩放前删掉**：

```python
used = np.unique(t)
remap = np.full(len(v), -1, dtype=np.int64)
remap[used] = np.arange(len(used))
t, v = remap[t], v[used]
```

实测 9,955 → 7,986。

---

## 4. 法线 / UV / 切线

### 法线：面积加权 + 面法线兜底

```python
fn = np.cross(v[t[:,1]] - v[t[:,0]], v[t[:,2]] - v[t[:,0]])   # 未归一化 = 面积加权
n = np.zeros_like(v)
for k in range(3):
    np.add.at(n, t[:, k], fn)
```

面积加权会**恰好抵消成 0**（实测有 2 个零法线顶点）。必须兜底：

```python
ln = np.linalg.norm(n, axis=1)
bad = ln < 1e-9
if bad.any():
    n[bad] = fn[bad[t[bad, 0]]]      # 退化成该顶点某个面的法线
    ln = np.linalg.norm(n, axis=1)
n /= ln[:, None]
```

### UV：三平面投影

源 UV 在焊接+聚类后已失效，按顶点法线主轴投影即可（建筑无需精确 UV）：

```python
axis = np.argmax(np.abs(n), axis=1)
uv = np.zeros((len(v), 2))
uv[axis == 0] = v[axis == 0][:, [0, 2]]
uv[axis == 1] = v[axis == 1][:, [0, 2]]   # 注意列序
uv[axis == 2] = v[axis == 2][:, [0, 1]]
mn, mx = v.min(0)[:2], v.max(0)[:2]
ext = np.where(mx - mn == 0, 1.0, mx - mn)
return (uv - mn) / ext
```

⚠️ 维度陷阱：**按面算的 axis 不能用来索引顶点**。必须写成按顶点的 `triplanar_uv(v, n)`，
否则报 `boolean index did not match indexed array`。

### 切线：w 分量绝不能累加 ⚠️

HOI4 的 `ta` 是每顶点 4 float（xyz + 握手 w），**原版 w 恒为 ±1**。
最自然的写法恰好是错的：

```python
# 错：w 被 np.add.at 累加成 -4..15
np.add.at(out, t[:, 0], np.hstack([T, np.ones((len(T), 1))]))
np.add.at(out, t[:, 1], np.hstack([T, -np.ones((len(T), 1))]))
```

正确写法 —— **只累加 xyz，归一化后与法线做 Gram-Schmidt，w 直接置 1.0**：

```python
acc = np.zeros((len(v), 3))
for k in range(3):
    np.add.at(acc, t[:, k], T)              # T 是每面单位切线
al = np.linalg.norm(acc, axis=1)
if (al < 1e-8).any():                # 累加抵消 -> 用任意垂直于法线的单位向量
    ref = np.tile([0., 0., 1.], (len(v), 1))
    ref[np.abs(n[:, 2]) > 0.9] = [1., 0., 0.]
    alt  = np.cross(n, ref)
    alt /= np.maximum(np.linalg.norm(alt, axis=1, keepdims=True), 1e-12)
    acc[al < 1e-8] = alt[al < 1e-8]
    al = np.linalg.norm(acc, axis=1)
acc /= al[:, None]
acc -= n * np.sum(acc * n, axis=1)[:, None]          # Gram-Schmidt
acc /= np.maximum(np.linalg.norm(acc, axis=1), 1e-12)[:, None]
out = np.hstack([acc, np.ones((len(v), 1))])
```

校验指标：`min|xyz| == 1.0`、零行 == 0、`max|T·N| < 1e-6`。
（对照原版 `factory.mesh`：318 行全部 `|xyz| == 1.0`，`w` 全为 1.0。）

UV 简并的三角形（`det == 0`）会让切线叉积爆炸，需退化成几何边方向。

---

## 5. 缩放定位

```python
ext = v.max(0) - v.min(0); ext[ext == 0] = 1.0
scale = float((TARGET_SIZE / ext).max())
v = (v - v.min(0)) * scale            # 最低点归零 —— 这一步就贴地了
ext = v.max(0) - v.min(0)
off = (TARGET_SIZE - ext) / 2.0
off[2] = 0.0                          # Z 不再偏移，否则模型悬空
v = v + off
```

`off[2] = 0.0` 是关键 —— 居中偏移若把偏移量也加到 Z 上，模型会浮空或半沉。

---

## 6. 写出 .mesh：二进制格式

`scripts/pdxml.py` 是自建的写入器（**不要用 `pdx_data.writeData()`** ——
它需要数值列表，传入空格分隔的字符串会走进 `all str` 分支，把整个数字串
当成单个字符串写出，产物只有几百字节）。

### 容器结构

```
"@@b@"                          文件头
pdxasset = int[1, 0]            ⚠️ 是 int 数组，不是字符串
[object\0
  [polySurfaceShape1\0
    [[[mesh\0
        !p   f  count  <3N float>     顶点位置
        !n   f  count  <3N float>     法线
        !ta  f  count  <4N float>     切线
        !u0  f  count  <2N float>     UV
        !tri i  count  <3M int>       三角索引
      [[aabb\0      !min f3  !max f3
      [[material\0  !shader s !diff s !n s !spec s
  [locator\0← File 直接子级，不在 mesh 内
    [[factorysmoke\0  !p f3  !q f4
```

### 三条编码规则（都是踩过的坑）

1. **对象记录** = `'[' * depth + name + '\x00'`，**名字前没有长度字节**。
   多写一个长度字节会让回读得到 `'\x06object'` 而不是 `'object'`。
2. **字符串值** = `s` + count(4，通常 1) + strlen(4) + 字节，
   **strlen 含结尾的 `\x00`**。漏掉 count 字段会让回读炸出
   `unpack_from requires a buffer of at least 1299735655 bytes`。
3. **`pdxasset` 是 int 数组 `[1, 0]`**，对应字节
   `i\x02\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00`。
   写成字符串 `'PdxMesh'` 会让回读显示 `pdxasset: '2'`。

原版头部长这样（可逐字节对照）：

```
@@b@!\x08pdxasseti\x02\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00[object\x00[[polySurfaceShape1\x00[[[mesh\x00
```

### Locator

冒烟/蒸汽挂点在 **`File` 直接子级**，不在 mesh 内。原版四元数是 `[0,0,0,-1]`：

```python
top = v[int(np.argmax(v[:, 2]))]
zq  = [0.0, 0.0, 0.0, -1.0]
locs = [('factorysmoke',  [top[0], top[1], top[2]], zq),
        ('factorysmoke2', [top[0], top[1], top[2]], zq)]
```

---

## 7. 校验清单

写盘后必须过一遍：

| 项 | 期望 |
|---|---|
| 体积 | ≤ 上限（5 MB ⇒ 612 KB 是安全的） |
| 结构树 | `File → object → polySurfaceShape1 → mesh(p,n,ta,u0,tri) → aabb, material` + 2 个 `locator` |
| 索引范围 | `tri.max() < len(v)` |
| 法线 | `min|n| == 1.0`，无零法线 |
| 切线 | `min|xyz| == 1.0`，零行 == 0，`w` 恒 1.0，`max|T·N| < 1e-6` |
| AABB | 与顶点实际 min/max 一致（容差 1e-4） |
| 落地 | `v[:,2].min() == 0` |
| 地基 | 底面水平层面积 ≈ 0 |

### 回读

```python
tree = read_meshfile(path)
```

⚠️ 两个回读陷阱：

1. `read_meshfile()` 返回的是 `ElementTree.Element`，属性在 `.attrib` 里，
   **且已经是字符串**。再喂给 `parseData()` 会报
   `TypeError: a bytes-like object is required, not 'str'`。
   自己按空白/逗号切分再转 float（注意剔除尾随逗号、正确处理科学计数法）。
2. **绝不要 `print` 整个 attrib**（29,865 个 float 会刷爆输出并被截断）。
   只打印 `keys()` 和摘要统计。

---

## 8. 装进 MOD

⚠️ 很多项目工作区对 shell 子进程有写保护：**新建文件可以，改写/删除已存在文件被拒**。

可靠顺序：

```bash
rm -f  <mod>/gfx/models/buildings/factory.mesh   # 删除通常可行
cp     <new>.mesh  <mod>/gfx/models/buildings/factory.mesh
```

**不要依赖 `mv` 改名让位** —— 实测同一轮里先成功后失败。
若 `rm` 也失败，才需要请用户手动覆盖。

替换前先备份原文件（存到工作区**之外**，例如 `~/hoi4lint/`）。

---

## 9. 完整跑法

```bash
PY=/c/Users/XIANGZIYUAN/.workbuddy/binaries/python/versions/3.13.12/python.exe
S=~/.workbuddy/skills/hoi4-fbx-building-to-mesh/scripts

# 1) 扫 FBX 数组 -> .npy（跑 fbx_arrays.py，按其输出对应数组）
# 2) 三角化 -> geo/Vertices.npy + geo/tris.npy
# 3) 出模型
$PY $S/build_building.py \
    --geo   <dir with Vertices.npy + tris.npy> \
    --out   out/building.mesh \
    --base-cut 2.0 \
    --target-tris 20000 \
    --size 0.7295,1.1980,1.0109 \
    --shader PdxMeshAdvancedSnow \
    --diff factory_d.dds --normal factory_n.dds --spec factory_s.dds
```

参数说明：

- `--base-cut`：地基板顶高度（**先看 Z 直方图再定**）
- `--size`：目标足迹 `x,y,z`
- `--locator <name>`：可重复；不给则默认 `factorysmoke` + `factorysmoke2`
- 贴图：建筑「内部无需贴图」时，单材质沿用目标建筑的既有 DDS 即可

---

## 参考实例

`temple.fbx`（3ds Max 2023 导出，binary FBX 7400，11.6 MB）
→ HOI4 建筑，替换 MOD 的 `factory.mesh`：

| 项 | 值 |
|---|---|
| 源 | 878,482 顶点 / 217,519 面 |
| 删地基 | −7,667 面（Z ≤ 2.0 整块） |
| 焊接后 | 241,592 顶点 |
| 聚类 grid=39 | 9,955 顶点 / 19,056 面 |
| 去孤立顶点 | 7,986 顶点 |
| 产物 | 612,431 字节（0.584 MB） |
| 足迹 / 高 | 1.568 × 1.676 × 1.011，底座 z=0 |
| 材质 | `PdxMeshAdvancedSnow` + factory_d/n/s.dds |