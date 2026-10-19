---
name: ui-bugs-interface-stale-copies
description: 10-17 UI bug 根因与现状：DLC 图标=窗口高度、X 图标=core.gfx 补 sprite、选国顺序=bookmark version=base_game、背景预览=_small.dds；分叉 .gui 勿塞原版块
metadata:
  node_type: memory
  type: project
  originSessionId: sess_3c421fb8-e84d-47d4-a44c-53452b380660
---

# 提瓦特黎明 10-17 界面 bug 根因表（现状）

| 症状 | 根因 | 状态 |
|---|---|---|
| DLC 图标少一个（dlc052） | `frontendmainview.gui` 的 `mainmenu_dlc_ownership` 窗口高度 583 裁掉第 10 个图标 → 改 684 | 已修 |
| 社媒 X 图标不显示 | `core.gfx` 缺 sprite `x`（旧副本） → 补 `gfx/interface/icon_x.dds` | 已修 |
| 选国国家 tag 顺序乱 | `common/bookmarks/*.txt` 条目顺序 + 每条必须 `version = base_game` 才按文件顺序显示 | 已修 |
| 开始游戏界面：更换背景按钮花、背景预览图不对 | ①按钮用 `GFX_button_238x38`，core.gfx 旧副本缺失 → 补；②预览图 = 每张加载图的 `GFX_<名>_small`，mod 只有大图没有 `_small.dds` 且无 `interface/small_background.gfx` → 全部预览落到原版图 | 10-17 修毕待验 |

**背景预览做法**：`common/frontend/backgrounds/base_backgrounds.txt`（原版文件，mod 未覆盖）列条目 `load_N = {}`；每个条目需要 `interface/small_background.gfx` 里同名 `GFX_<名>_small` 指向 `gfx/loadingscreens/<名>_small.dds`（192x144、DLC 里用 corneredTileSpriteType size 192x144）。无定义时只兜底一张图。原版 `_small.dds` 是**未压缩 A8R8G8B8**（128B 头 + W*H*4），PIL 不能写 DDS，可复制原版 192x144 的 128B 头后拼 BGRA 像素。

**⚠ 铁律**：分叉过的 .gui 不能直接"补原版元素块"（布局会乱）；补 sprite/新增独立文件相对安全。

关联 [[gamma-mod-progress]]、[[hoi4-skill-structure]]
