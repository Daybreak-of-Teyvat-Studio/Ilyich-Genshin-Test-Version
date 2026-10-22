---
name: hoi4
version: 1.0
description: 钢铁雄心4(HOI4)模组开发指南与新手引导 — 从「我要制作一个钢铁雄心4的XX mod」一句话开始，引导完成 mod 骨架搭建、新国家/新国策树/新单位/新事件等全部内容制作、地图与州数据（挪省/州重排/海洋州/地形/胜利点）、本地化、崩溃排查。当用户想制作或修改任何 HOI4 mod、编辑 .txt/.gfx/.yml/.mesh 文件、挪省改州、加胜利点或州名、改地形、排查闪退时使用。
author: 猫妖
user-invocable: true
---

# HOI4 模组开发助手

HOI4（Hearts of Iron IV）使用 Paradox Interactive 专有脚本语言（形似 Lua），对格式极其敏感。所有工作围绕编辑 `.txt` / `.gfx` / `.yml` / `.asset` / `.mesh` 文件展开。本 skill 采用**渐进披露**：先读本文件掌握铁律与分派，再按任务读对应 reference，不要一次性全读。

**制作者：猫妖**

## 快速开始（用户引导总入口）

用户说「我要制作一个钢铁雄心4的XX mod」「给 mod 加新国家」「闪退了」等任何诉求时：
**按 `references/user-guide.md` 引导**——环境自检 → 首次配置向导 → 任务分流
（从零建 mod / 加内容 / 地图 / 排错 / 本地化）→ 路线图确认 → 逐项制作并给验证点。
目标：3 轮对话内进入实际制作；每个数字（省号/州号）双读核对；大改动先 `--dry` 过目。

## 首次使用（每个环境只做一次）

开始任何任务之前，先检查本 skill 目录下是否存在 `config.json`：

- **存在** → 读取其中的 `hoi4_root` 与 `mod_root`，直接开始任务。
- **不存在** → 按下面的欢迎块原样展示给用户，依次收集两个路径，验证通过后写入 `config.json`。

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  HOI4 模组开发助手 · 首次使用向导
  制作者：猫妖    版本：v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  💡 想达到最佳效果，推荐先安装两个配套项目：
     · superpowers-zh（技能框架）
       安装命令：npx superpowers-zh
     · rhoiscribe-hoi4（HOI4 本地 mod 开发资源包）
       网址：https://github.com/czxieddan/RHoiScribe

  开始前需要配置两个路径（只配置一次，之后自动加载）：

  1. 钢铁雄心4 游戏根目录
     例如：F:\Steam\steamapps\common\Hearts of Iron IV
     用途：只读参考原版文件（语法模板 / 单位数值 / GUI 结构），
           本助手绝不写入这个目录。

  2. 你要制作的 mod 目录
     例如：C:\Users\你\Documents\Paradox Interactive\Hearts of Iron IV\mod\MyMod
           （也可以是仓库里的 mod 工程目录）
     用途：所有修改都发生在这里。

  请把两个路径发给我（可以一条消息发两个）。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**路径验证规则**（不通过就告诉用户哪里不对并重新询问，不要猜）：

| 路径 | 必须存在 | 说明 |
|---|---|---|
| 游戏根目录 | `launcher-settings.json` 或 `map/` + `interface/` | 只读参考，禁止写入 |
| mod 目录 | `descriptor.mod` 或任意 `*.mod` 文件 | 所有修改发生在这里 |

`config.json` 格式：

```json
{ "hoi4_root": "F:\\Steam\\steamapps\\common\\Hearts of Iron IV",
  "mod_root":  "C:\\...\\mod\\MyMod" }
```

**配置完成后，紧接着展示第二段询问**（原样给用户）：

```text
  路径已配置完成，可以开工了。

  接下来想做点什么？常见的有：

  · 新国家            · 新国策树          · 新单位 / 兵种图标
  · 新决议            · 新事件            · 新角色（领导人/将领/顾问）
  · 新法案            · 新军工组织 (MIO)  · 新学说（陆海空子学说）
  · 新民族精神/动态修正 · 新特质            · 新编制            · 新建筑
  · 权力平衡 (BOP)    · 新战术卡 (tactic)  · 界面 UI / GUI
  · 本地化补全 / 修正
  · 新装备 / 新科技    · 新 3D 地标

  · 地图调整（挪省、改州归属、州重排）
  · 建筑悬空 / 穿模修复
  · 分析崩溃原因（读最新 crash 转储定位）
  · 其他任何 mod 修改 —— 直接描述你的目标即可

  选一个编号或用一句话描述你的目标。
  我会先列出这项任务要做的全部工作与顺序，你确认后再动手。
```

**用户回答后**：按任务类型查 `references/task-roadmaps.md`，把对应路线图（文件清单 + 顺序 + 联动 + 验收）整理给用户看，**经用户确认后**再动手。路线图里没有的任务类型，先去游戏根目录找已有同类文件研究结构，再给用户组清单。

## 编辑铁律（必读）

- **缩进一律用 tab（制表符），绝不用空格。** HOI4 解析器对格式严格。
- **不要用 Edit 工具改 tab 缩进的 Paradox 脚本文件** —— 它会在 tab/空格不匹配时静默失败。改 `.gfx` / `.txt` 用 **PowerShell 正则 `-replace`**（或字节级处理的 Python 脚本），它能正确处理 tab。
- **PowerShell `-replace` 大小写不敏感**，批量改名（如 `RAP`→`RAF`）会连带把 `rap_role_` 误改大写。要区分大小写用 **`-creplace`**。tag/flag 大小写敏感，务必核实。
- 替换共享模板路径时用**上下文感知**模式：匹配目标 `name = "..."` 行之前的 `textureFile` 行，避免误改其它单位。
- **始终照抄附近已有代码作为模板**，风格偏差即错误。
- 用户用中文报统计名（如"额外损伤"）时，**先核实确切英文 key 再动手**，不要猜。`additional_collateral_damage` = 对建筑/基建附带损伤（超重型火炮），**不是** `soft_attack`（对人员）。
- **单点改动牵动多文件时，验收方式是"与原始文件对比不变量"，不是"看起来对"**；改完必须过"语法关"（括号配对、字段完整、无重复键），再验语义。

## 分派表（按任务读 reference）

| 任务 | 读 |
|------|-----|
| **用户引导 / 首次使用 / 不知道从哪开始** | `references/user-guide.md` —— 环境自检、首次配置对话脚本、任务分流（从零建 mod/加内容/地图/排错/本地化）、一句话任务速查 |
| **改了 state/省后自检 / 报告州数据健康度** | `scripts/check_states.py --mod <mod根目录>` —— 州语法/省覆盖/核心/VP/首都/本地化/buildings 全项一遍；动过地图数据后主动提示运行 |
| **规划新任务**（新国家/新国策树/新单位/新决议/新事件…）：任务由哪些文件组成、按什么顺序 | `references/task-roadmaps.md` —— 首次使用后的"要做什么"环节也用它 |
| 任何 .txt/.gfx/.yml 文件结构、语法模板 | `references/paradox-syntax.md` |
| 角色/领导人/将领/顾问（common/characters） | `references/paradox-syntax.md` §17 |
| 单位/装备/国家修正/触发器/效果 的 stat key | `references/stat-keys.md` |
| 单位图标 DDS 转换 / GFX 注册 | `references/icons-dds.md` |
| 3D 地标 / Blender 工具链 | `references/landmarks-3d.md` |
| **挪省(province)属州、改州归属、进游戏闪退** | `references/map-data.md` —— 省→州映射散在 state 文件与 `map/buildings.txt` 两处，改一处必同步另一处；含改完必过的"语法关"清单 |
| **建筑悬空/陷地/被山体穿模**（heightmap 改动后尤甚） | `references/buildings-height.md` —— 第 4 列 y 重算 + 防穿模抬升，配 `scripts/` 三个工具。**本模块由绿豆糕制作** |
| **批量挪省/均分州/海州/州名/VP/地形**（Gamma 全图改造流水线） | `references/gamma-pipeline.md` —— 多州均分紧凑度优化、海洋州创建、州名 `*` 化、VP 管理、地形三步覆盖、合并修复与从零重排 |
| 适配基础游戏新版本（stale override） | `references/version-adapt.md` |
| **本项目专属经验示例**（决议/科技树/占领…） | `references/ra-notes.md` —— 特定 mod 的经验库，**先按索引 Grep 关键词，不要整读**；可替换为你自己项目的积累 |

> 读法：**先 `SKILL.md`（首次使用+铁律+分派）→ 按任务读一个 reference → 本项目细节再去项目专属经验库按关键词 Grep**。

## 脚本（scripts/，可与 reference 配合使用）

| 脚本 | 用途 |
|------|-----|
| `scripts/fix_buildings_height.py` | 建筑高程**诊断**报告（有 LF 陷阱，不要用于落地） |
| `scripts/fix_height_crlf.py` | 建筑高程重算**落地**（字节级保持 CRLF） |
| `scripts/fix_pierce.py` | 建筑防穿模抬升（陡坡被山埋；v4 规则） |
| `scripts/fill_state_gaps.py` | 补空白 state 编号（尾部填洞·陆海分离；连号 capital/buildings/本地化） |

三个脚本均为**绿豆糕**制作的模块（方法与公式来源），`--map <mod>/map` 参数化调用，改前自动备份。用法见 `references/buildings-height.md`。

## 项目根目录工具（Gamma 流水线，不入 scripts/ 因含项目路径）

| 脚本 | 用途 |
|------|-----|
| `gamma_state_edits.py` | 转省 + 改归属 + 自动同步 buildings.txt |
| `rebalance_states.py` | 多州省均分（紧凑度优化） |
| `terrain_pipeline.py` | 地形三步改造 |
| `buildings_final_fix.py` | buildings.txt 合并修复（单遍历陆+海） |
| `fix_gen_points.py` | 州级生成点从零重排 |
| `state_names_job.py` | 州名本地化改造 |
| `vp_reset.py` / `vp_add2.py` / `vp_371.py` | VP 管理 |
| `sea_split.py` / `sea_state_fix.py` | 海洋州创建 / 修复 |
| `check_buildings.py` | buildings.txt 守门检查 |
| `gamma_read_colors.py` / `gamma_apply_colors.py` | 涂色读色 / 装国 |
| `gamma_map_tools.py` / `gamma_border_layers.py` / `gamma_palette.py` | 地图工具 |

用法见 `references/gamma-pipeline.md` 和 `references/map-data.md`。

## 标准工作流

1. **首次使用**：检查/创建 `config.json`（见上）。
2. 判断任务层级：单位数值 / 图标 / 编制 / 本地化 / 3D 模型 / 地图与州数据 / 建筑高程 / 版本适配。
3. 按分派表读对应 reference（只读需要的那一个）。
4. **模板优先**：reference 已有该文件类型的模板，直接照抄删改；只有 reference 没有的字段/知识才去游戏根目录找同类文件（只读）。
5. 执行：改 tab 文件用 PowerShell 正则或脚本；图标先核对 DDS 二进制规格（魔数/尺寸/NVTT），别信文件名；3D 用命令行 Blender 验证脚本跑通。
6. **改地图/州数据后必须验不变量**（`references/map-data.md`）；**改建筑高程后必须过语法与残差双重验收**（`references/buildings-height.md`）。闪退类问题先读 `logs/error.log` 尾部。
7. **动过 state / province / buildings / 本地化之后，主动询问用户是否运行 State 自检**：
   `python <skill>/scripts/check_states.py --mod <mod根目录> [--baseline <原始buildings.txt>]`
   （州语法/省覆盖/核心/VP/首都/本地化 BOM 与孤儿/buildings 引用与海州生成点，全项一遍）
8. 适配新版本：shadow 检测 → 重建 stale override → 保留独有内容（见 version-adapt）。
9. 每次写完退出前，把新学到的非显而易见经验追加进对应 reference。

## 目录结构

```
hoi4/
  SKILL.md                    # 本文件：首次使用 + 铁律 + 分派
  config.json                 # 首次使用后生成（不入库，见 .gitignore）
  references/
    user-guide.md             # 用户指引：引导流程、场景对话脚本、一句话任务速查
    task-roadmaps.md          # 任务路线图：常见任务的文件组成与顺序
    sub-doctrine-tutorial-子学说教程.md   # 子学说教程修正版（猫妖原教程 + 原版校验勘误）
    grand-doctrine-tutorial-主学说教程.txt   # 主学说/轨道/里程碑完整教程（猫妖团队）
    paradox-syntax.md         # Paradox 脚本语法与文件模板（19 类文件）
    stat-keys.md              # stat / modifier key 中英对照
    icons-dds.md              # 单位图标 DDS 规格与注册
    landmarks-3d.md           # 3D 地标 / Blender 工具链
    map-data.md               # 省↔州数据一致性 + 语法关
    buildings-height.md       # 建筑高程与防穿模
    gamma-pipeline.md         # Gamma 全图改造流水线（均分/海州/州名/VP/地形）
    unit-categories-参考.txt  # 单位类别白名单全注释参考（只查不放进 mod）
    version-adapt.md          # 基础游戏版本适配
    ra-notes.md               # 项目专属经验库（示例，可换成你自己的）
  scripts/
    fix_buildings_height.py   # 建筑高程诊断
    fix_height_crlf.py        # 建筑高程落地（CRLF 保持）
    fix_pierce.py             # 建筑防穿模抬升
```

项目根目录另有 Gamma 流水线工具（不入 skill scripts/，因含硬编码路径）：
`gamma_state_edits.py` `rebalance_states.py` `terrain_pipeline.py` `buildings_final_fix.py`
`fix_gen_points.py` `state_names_job.py` `vp_reset.py` `vp_add2.py` `sea_split.py`
`sea_state_fix.py` `check_buildings.py` `gamma_read_colors.py` `gamma_apply_colors.py`
`gamma_map_tools.py` `gamma_border_layers.py` `gamma_palette.py` `fix_buildings_height.py`
`fix_height_crlf.py` `fix_pierce.py`

## 开源说明

- 本 skill 由**猫妖**制作，当前版本 **v1.0**，欢迎自由使用、修改与分发。
- `references/ra-notes.md` 是特定 mod 的项目经验，仅作"如何沉淀项目经验"的示例；使用你自己的项目时可直接替换或删除。
- 游戏根目录仅作只读参考，任何情况下不要把游戏本体文件复制进你的开源仓库。
