---
name: hoi4-scripted-gui-panel
description: 钢铁雄心 IV（Hearts of Iron IV）MOD 里"表格型机制面板"（scripted GUI 报表：背景网格 DDS + 一堆 instantTextboxType + scripted_gui properties）的加行/加列/改布局/换背景。当用户要求「在机制界面加一栏/加一行/把某栏挪到某栏右边/换背景图/国名显示不出来」，或涉及 interface/*.gui、interface/*.gfx、common/scripted_guis/*.txt、gfx/**/*.dds 的表格面板改动时使用。覆盖坐标公式、center 容器的 position 补偿、text 的本地化键语义、中文字体 override、背景 DDS 的"逐像素搬运+接边"扩图法、未压缩 A8R8G8B8 DDS 头模板、以及工作区被外部并发改写时的外科式改法。触发词：HOI4 界面、机制界面、OB_General_Stats、scripted GUI、instantTextboxType、加一栏、加一列、加一行、背景网格、background.dds。
agent_created: true
---

# HOI4 scripted GUI 表格面板改造

## 什么时候用

用户要在一个**报表型面板**上动结构：加一行国家、加一栏数据、把某栏挪位置、换/扩背景图。
这类面板由 4 个文件共同构成，**改一个必须同步改其余**：

| 文件 | 作用 |
|---|---|
| `interface/<名>.gui` | 窗口 + 背景 + 15 个国旗 iconType + N 组数据 instantTextboxType + 表头 instantTextboxType |
| `interface/<名>.gfx` | `spriteType` 把 `GFX_<名>_background` 指到 `gfx/.../xxx.dds` |
| `common/scripted_guis/<名>_GUI.txt` | `properties = { TAG = { image = [TAG.GetFlag] } }`，**属性名必须等于 .gui 里的 iconType 元素名** |
| `gfx/.../<名>.dds` | 面板底色 + 金色格线的**网格图**；行高/列宽和 .gui 的坐标是硬绑定的 |

## 结构约定（先看清再动手）

```
containerWindowType = {
    name = "xxx_window"
    position = { x = P y = Q }      # orientation=center + origo=center ⇒ 这是"元素中心相对屏幕中心的偏移"
    size = { width = W height = H }
    background = { quadTextureSprite = "GFX_xxx_background"  position = { x=BX y=BY }  size = { x=BW y=BH } }
    iconType = { name = "MOT"  spriteType = "GFX_flag_small"  position = { x=120 y=150 } ... }   # 每行一个国旗
    instantTextboxType = { name = "MOT1"  position = { x=165 y=150 }  text = "[?MOT.num_armies]" }  # 第1栏第1行
    ...
    instantTextboxType = { name = "H-STATE"  position = { x=165 y=130 }  text = "State" }            # 表头
}
```

- 元素名 = `<TAG><栏号>`，栏号 1..N；表头名 `H-<栏名>`；国旗元素名就是 TAG。
- 行 y = `ROW_Y0 + ROW_DY * i`（常见 150 + 25i）；表头 y 通常 `ROW_Y0-20`。
- 栏 x = `COL_X0 + Σ(前面各栏宽度)`。**不要**写成固定的 `COL_X0 + 120k`，一旦某栏宽度不是 120 就会错。
- 背景 DDS 的竖线位置 = 该栏文字 x **减去 15**（即 120 栏宽 ⇒ 竖线在 40+120k）；横线 y = 68+25i。
  背景元素在容器 (110,105)，所以 **DDS 内坐标 = 容器坐标 - 110 / -105**。

## 三条最容易踩的坑

### 1. 改窗口宽度必须同步改 `position.x`
`orientation = center` + `origo = center` ⇒ `左边缘 = position.x - size.width / 2`。
想让面板左上角不动：`新 position.x = 旧左边缘 + 新宽度/2`。
（例：1110→1350，左边缘 -895 不变 ⇒ `position.x = -895 + 675 = -220`。）

### 2. `text` 的语义：它是**本地化键**，不是表达式
- `text = "State"`、`text = "ACHIEVEMENTS"` —— 引擎先查本地化表，查到就显示本地化值，查不到就原样显示。vanilla 全是这个用法。
- **要显示国家名字，直接写 TAG 当键**：`text = "MOT"` ⇒ 显示 `MOT:0 "蒙德"`（按当前语言）。这是最稳的做法。
- `text = "[X]"` 是另一套（本地化命令/脚本化本地化）：`[脚本化本地化键]`、`[?变量]`。
  手册明确 **`?` 是"变量"标记**，`[?TAG.var]` = "TAG 的变量 var"。
- 想显示"随意识形态变更的动态国名"，用 `[MOT.GetName]`（`GetName` 是命名空间，**不带 `?`**）。
  若这个写法在你的版本里不生效，退回 `text = "MOT"`。
- 想在数字后加格式：`[?TAG.dx|0]`（0 位小数）、`[?TAG.casualties|*]`（K/M）、`[?TAG.surrender_progress|%1]`。

### 3. 中文必须用有中文 override 的字体
`Hearts of Iron IV/interface/core_chinese.gfx` 里对 `hoi_16mbs / hoi_18 / hoi_18b / hoi_18mbs /
hoi_20b / hoi_20bs / hoi_24header / hoi_30header / hoi_36header / hoi_22tech / hoi_22chat / hoi_33 /
hoi4_typewriter16|22` 做了中文位图替换 —— **这些字体能显示汉字**。
`hoi_24header` 有中文 override，可以直接拿它显示中文（实测中文表头正常）。
一个汉字约占字号大小的宽度（24px 字体 ≈ 24px/字），**7 个汉字 ≈ 168px**，据此定栏宽。

## 加一栏的完整流程

1. **改 `.gui`（外科式逐行改，不要整体重写）**：
   - 窗口 `position.x` / `size.width`；`background` 的 `size.x`；
   - 在**最后一组数据栏之后、Headers 注释之前**插入 15 个块（每个 10 行，块与块之间**不留空行**，整组之后留 1 个空行）；
   - 在 **H-最后一栏 之后、`\t}` 收尾之前**插入 1 个表头块；
   - 新栏 `maxWidth` 不要照抄 400——最后一栏要收窄（如 `栏宽-5`），否则长国名会溢出面板右缘。
2. **扩背景 DDS（不要重新画）**：把现有 DDS/PNG **逐像素搬**进新画布，只在右侧补：
   - 新竖线在 `新栏 x - 15`（即"补一个 120 格"就是 `原宽-?`…按竖线序号算），2px 粗，y 范围抄原竖线；
   - 把每条横线从**原来的右端**接着画到 `新宽 - 11`（原图左留 9px、右留 11px，保持对称）；
   - 其余区域填原底色。这样既保证老区域 100% 不变，又不用去猜原图几何。
3. **补 `common/scripted_guis/*.txt` 的 properties**：只有**新增了国家行**才需要；
   只加数据栏不用改（properties 只管国旗图片）。
4. **校验后才落地**（见下）。

## DDS 怎么写

**优先未压缩 A8R8G8B8**（无损、写起来最省事；手册：GUI 贴图"通常是 ARGB8/A8R8G8B8，不带 mipmap"）：

```python
import struct
def dds_argb8(rgba, w, h):          # rgba 为 R,G,B,A 顺序的 bytearray，长 w*h*4
    stride = w * 4
    data = bytearray(w * h * 4)     # DDS 里实际是 B,G,R,A
    for i in range(w * h):
        o = i * 4
        data[o], data[o+1], data[o+2], data[o+3] = rgba[o+2], rgba[o+1], rgba[o], rgba[o+3]
    hdr  = b'DDS ' + struct.pack('<7I', 124, 0x100F, h, w, stride, 0, 0)   # size,flags,H,W,pitch,depth,mips
    hdr += b'\x00' * 44                                                    # reserved1[11]
    hdr += struct.pack('<2I', 32, 0x41) + b'\x00' * 4 + struct.pack('<I', 32)  # pf.size,pf.flags(ALPHAPIXELS|RGB),fourCC=0,bpp=32
    hdr += struct.pack('<IIII', 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    hdr += struct.pack('<I', 0x1000) + b'\x00' * 16                        # caps=DDSCAPS_TEXTURE
    assert len(hdr) == 128
    return hdr + bytes(data)
```
- 文件必须叫 `.dds` 且内容是 dds。**有人会把 PNG 直接改名成 `.dds`** —— 打开发现 `magic` 是 `\x89PNG` 就说明中招了，顺手改回标准 dds。
- 压缩格式用 DXT5（16 字节/块，684 字节头那种说法是错的：标准头是 128 字节 = 4 字节 magic + 124 字节 DDS_HEADER）。
- 纯 Python 解码器/PNG 预览：读 `gfx/.../*.dds` → 解 DXT5 或未压缩 → 写 PNG，用来给用户看效果、也用来做"回读一致率"校验。

## 落地前的校验清单（缺一不可）

- `.gui`：括号 `depth` **与改前相同**；`instantTextboxType` 数 == `1 + 栏数 + 栏数×行数`；`iconType` 数 == 行数；
  无 BOM（或与原文件一致）、纯 CRLF、无裸 `\r`；新栏元素名与 `text` 自洽且顺序 == 行序。
- 贴图：`magic == b'DDS '`、`dwSize == 124`、`dwWidth/dwHeight` 正确、`len(bytes) - 128 == w*h*4`、
  解码回读与原缓冲**逐像素一致 100%**、老区域"除横线接边外"零改动。
- 备份：改前每个文件各存一份到独立 `backup_*` 目录。
- 脚本一律 **dry-run（0 MISS）→ `--apply`**，断言用"行号 + 内容"双条件。

## ⚠️ 工作区可能被外部并发改写

实测同一工作区会被另一份副本/另一位编辑者动过：**去掉表头颜色码、给取数加小数位、整体换掉背景图并改 `.gui` 的 size**。
因此：

1. **动手前先比对**：把"上次自己生成的产物"（或从备份还原的版本）与现盘逐行 diff，
   列出差异 → **有差异就一律改用外科式逐行编辑**，绝不整体重写，否则会无声回滚别人的改动。
2. 保留对方风格：对方把表头改成了英文，新加的表头就也用英文；对方去掉了 `§` 颜色码，新加的也别加。
3. 长跑脚本**重定向到文件再读**，别管道给 `tail`（管道破裂会中断写入循环）。

## 小陷阱

- Python 里拼 `.gui` 文本时，`|%1` 这类取数格式串会被当成 printf 占位符 → 要写 `|%%1`。
- 用 `open(p, encoding='utf-8', newline='')` 读、`.split('\n')` 改（元素自带 `\r`）、`'\n'.join()` 写回，
  CRLF 才不会被改成 LF；确定无 BOM 时可不用 `utf-8-sig`。
