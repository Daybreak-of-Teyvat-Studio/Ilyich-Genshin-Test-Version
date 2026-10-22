# 单位图标 DDS 流水线

## 1. 源图标

- 基址：`F:\Steam\steamapps\common\Hearts of Iron IV\gfx\interface\counters\`
- 大图标源：`division_templates_large\custom_template_XXX.dds`（**raw RGBA 单帧** 76×42，12896B）
- 小图标源：`division_templates_small\custom_template_XXX.dds`（30×12，1568B）

## 2. 目标格式（必须匹配现有单位，如 SUM_Eremites）

- 大图标 `divisions_large/unit_[name]_icon.dds`：**152×42，NVTT raw RGBA，25664B**
- 小图标 `divisions_small/onmap_unit_[name]_icon.dds`：**60×12，NVTT raw RGBA，3008B**
- 均 `noOfFrames = 2`（两帧并排）
- 头：`pf_flags=0x41`，offset 64 处 NVTT 标记，位掩码 R=0xFF G=0xFF00 B=0xFF0000 A=0xFF000000

## 3. 转换脚本

单帧源（76×42 / 30×12 raw RGBA）→ 每行复制一遍加宽一倍 → 写 NVTT 头。

```python
import struct

def write_nvtt_dds(path, pixels, width, height):
    hdr = bytearray(128)
    hdr[0:4] = b'DDS '
    struct.pack_into('<I', hdr, 4, 124)
    struct.pack_into('<I', hdr, 8, 0x100F)
    struct.pack_into('<I', hdr, 12, height)
    struct.pack_into('<I', hdr, 16, width)
    struct.pack_into('<I', hdr, 20, width * 4)
    struct.pack_into('<I', hdr, 24, 1)
    struct.pack_into('<I', hdr, 28, 1)
    hdr[64:68] = b'NVTT'
    struct.pack_into('<I', hdr, 76, 32)
    struct.pack_into('<I', hdr, 80, 0x41)
    struct.pack_into('<I', hdr, 88, 32)
    struct.pack_into('<I', hdr, 92, 0x000000FF)
    struct.pack_into('<I', hdr, 96, 0x0000FF00)
    struct.pack_into('<I', hdr, 100, 0x00FF0000)
    struct.pack_into('<I', hdr, 104, 0xFF000000)
    struct.pack_into('<I', hdr, 108, 0x1000)
    rgba = bytearray()
    for r, g, b, a in pixels:
        rgba.extend([r, g, b, a])
    with open(path, 'wb') as f:
        f.write(bytes(hdr))
        f.write(bytes(rgba))

def double_width(pixels, w, h):
    new = []
    for y in range(h):
        row = pixels[y * w:(y + 1) * w]
        new.extend(row + row)
    return new
```

**坑**：
- 把 PNG 改名成 `.dds` **不能用**，必须是真 DDS 二进制。
- DXT5 压缩图标要先解压再处理。
- header offset 64 的 NVTT 标记是游戏读文件的必需项。

## 4. 两帧结构与右帧约定

- **左帧（frame 0）**：单位专属图标（独特剪影），在帧内居中（dx≈0, dy≈0）。
- **右帧（frame 1）**：通用步兵背景，取自基座游戏步兵图标，**不是左帧复制**：
  - 大：`divisions_large\unit_infantry_icon.dds`
  - 小：`divisions_small\onmap_unit_infantry_icon.dds`
- 基座步兵右帧规格（对齐基准）：大 49×27 内容 dx=+0.5 dy=+2.5（76×42 帧内）；小 25×12 dx=-0.5 dy=0.0（30×12 帧内）。

## 5. 调试校验

- 每个图标核对：`152×42 25664B NVTT`（大）/ `60×12 3008B NVTT`（小）。
- 魔数必须是 `DDS `（bytes 0-3），不是 PNG 魔数 `\x89PNG`。
- 若 DDS 头读出垃圾尺寸，多半是改名 PNG。

帧对齐校验：

```python
import struct
def check_icon(path):
    with open(path, 'rb') as f:
        data = f.read()
    h = struct.unpack_from('<I', data, 12)[0]
    w = struct.unpack_from('<I', data, 16)[0]
    px = data[128:]
    fw = w // 2
    for fi, fl in enumerate(['Left', 'Right']):
        xs, ys = [], []
        for y in range(h):
            for x in range(fw):
                a = px[(y * w + fi * fw + x) * 4 + 3]
                if a > 30: xs.append(x); ys.append(y)
        cx = sum(xs)/len(xs); cy = sum(ys)/len(ys)
        fc = (fw-1)/2.0; fm = (h-1)/2.0
        print(f'{fl}: dx={cx-fc:+.1f} dy={cy-fm:+.1f}')
```

## 6. GFX 注册（每个单位三个 spriteType）

```text
spriteType = {
    name = "GFX_unit_[name]_icon_medium"
    textureFile = "gfx/interface/counters/divisions_large/unit_[name]_icon.dds"
    noOfFrames = 2
}
spriteType = {
    name = "GFX_unit_[name]_icon_medium_white"
    textureFile = "gfx/interface/counters/divisions_small/onmap_unit_[name]_icon.dds"
    noOfFrames = 2
}
spriteType = {
    name = "GFX_unit_[name]_icon_small"
    textureFile = "gfx/texticons/unit_DOT_Infantryer_small.dds"
    legacy_lazy_load = no
    noOfFrames = 2
}
```

命名约定：`GFX_unit_[name]_icon_medium` / `_medium_white` / `_small`。兵牌大图是 `_medium`、小图是 `_medium_white`（别漏 `_white`）。
