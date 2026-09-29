# 第七批：focus icon shine 注册 + 高频 Invalid effect 处理报告

日期：2026-09-20 范围：Daybreak of Teyvat **Beta Version**

---

## 一、focus icon shine 批量注册（已完成）

### 背景与机制
HOI4 渲染国策图标时，会查找 `<icon名>_shine` 的 spriteType 作为高光层；找不到就报
`Missing icon shine for focus: <focus_id>`。

### 诊断
- 解析 `common/national_focus/*.txt`：**3526** 个 focus，**1071** 个不同 icon。
- 解析 `interface/*.gfx`（84 个文件、3665 个 spriteType）：大量 focus 图标**只有本体 sprite、没有 `_shine` 变体**。
- 历史日志中 `Missing icon shine for focus` 共 1727 条，映射到 **576** 个不同 icon。

### 处置（按用户要求：shine 复用 icon 本身图片，不新增图片）
对 MOD 内 `interface/*.gfx` 中**作为 focus 图标使用、且缺少 `_shine`** 的 SpriteType，
在其定义**正下方插入一条 shine SpriteType**，格式与 MOD 既有样例
（`FOD_goals.gfx` 的 `GFX_FOD_Press_the_Fatui_shine`）一致：

```
SpriteType = {
    name = "<icon>_shine"
    texturefile = "<icon 自己的 texturefile>"          # 与本体重合图片
    effectFile = "gfx/FX/buttonstate.lua"
    animation = { animationmaskfile = "<icon tex>"
                  animationtexturefile = "gfx/interface/goals/shine_overlay.dds"
                  animationrotation = -90.0 ... }
    animation = { ... animationrotation = 90.0 ... }   # 反向再扫一遍
    legacy_lazy_load = no
}
```

### 结果
- 共新增 **407** 条 shine，涉及 **15** 个 gfx 文件（DOT_Focus 51 / DOT_VAN_focus 37 /
  DOT_MOT_Ideas 29 / Friend_KX_goals 83 / NewMOT_event 57 / RAG_focus 89 / KNA 17 …）。
- 三校验：所有文件 **括号 depth=0**、**BOM 保持原样**、**CRLF 一致（lf_only=0、无 `\r\r\n`）**。
- 备份：`C:\Users\XIANGZIYUAN\hoi4lint\backup_shine\`
- 脚本：`hoi4lint\add_shine.py`；校验：`verify_shine2.py`

> 备注：修复后在 21:09 的实机日志中 `Missing icon shine` 已为 0（该次运行未见此类错误），
> 本批 shine 属于**预防性注册**，保证任何一次加载都不会再缺 shine。

---

## 二、高频 Invalid effect 批量处理

### 现状（21:09 日志，9 MOD 全启用；Beta 自身 620 条）
`Invalid effect` 共 75 条，涉及 **33** 个不同 token。经与
原版 token 语料库（41396）+ MOD 自有 541 个 scripted_effect / 135 个 scripted_trigger 比对分类：

### A. 已真实修复（3 处结构/拼写错误，共消 7 条报错）
| # | 文件:行 | 问题 | 修复 |
|---|---|---|---|
| 1 | `common/national_focus/FOM_Focus.txt:2991` | `add_popularity` 内用了 `value = 0.15` | 改为 `popularity = 0.15`（原版实证键名为 popularity） |
| 2 | `common/decisions/NewMOT_decisions.txt:1430,1440` | 效果块 `random_owned_state` 内直接写触发器 `free_building_slots` | 用 `limit = { free_building_slots = {...} }` 包裹（还原作者"需有空余建筑位"的意图） |
| 3 | `events/KNA_event.txt`（4 处，行 231/250/261/279） | `option` 内出现无效包裹 `modifier = { ... }`，导致内部 `custom_effect_tooltip`/`hidden_effect` 全部不生效、事件链断裂 | 删除伪包裹、内容上提为 option 直接效果 |

- 三校验全部通过（depth=0、BOM 保持、CRLF 一致、无 `\r\r\n`）。
- 备份：`C:\Users\XIANGZIYUAN\hoi4lint\backup_effectfix\`；脚本：`hoi4lint\fix_effects_batch.py`
- ⚠️ 注意：以上 3 项恢复的都是**作者原本想要的效果**（如 KNA 事件链 kna.14→15→17 现在能触发），
  属"恢复意图"，请确认是否符合预期。

### B. 需作者拍板（自创机制，原版无此能力，不能仅靠改名修复）
| token | 次数 | 位置示例 | 说明/建议 |
|---|---|---|---|
| `num_of_factories` | 13 | `SAN_Neo_Focus.txt` 的 `completion_reward` | 它是**触发器**不是效果；若本意是"需 2 工厂才能完成"，应移到 `available`/`bypass` 写 `num_of_factories > 1` |
| `KQP` / `SHP` / `NGP` / `CYG` / `LYY_CloudRetainer` / `LYY_MoonCarver` / `LYY_MountainShaper` / `LYY_MadamePing` | 12+6+1+1+2+2+2+1 | `events/LYY_Ganyu_Events.txt` | 用**角色名/6字母名当国家 scope**（`XXX = { ... }`）；HOI4 国家 TAG 必须 3 字母、也不支持按角色名 scope。需改用事件目标或对应 3 字母国家（如 KQP=刻晴党） |
| `MOT_Re_Decisions_Support` | 3 | `events/NewMOT_Knights_event.txt:101` | 形如 scripted_effect 调用，但全 MOD **未定义**；需补定义或改正确名 |
| `consumer_goods_factor` | 3 | `common/decisions/NAT_Neo_decisions.txt:733` | 是**修正符**不是效果；需经 `add_dynamic_modifier`/idea 施加 |
| `add_infrastructure` | 2 | `events/NAT_Neo_Event.txt` | 原版等价：`add_building_construction = { type = infrastructure level = N }`（state scope） |
| `build_fortifications` / `build_naval_base` | 2+1 | `NAT_Neo_Event.txt` | 原版等价：`add_building_construction = { type = bunker / naval_base ... }` |
| `add_land_experience_gain` / `army_experience_gain` | 2+1 | `NAT_Neo_Event.txt` | 欲加经验：用 `army_experience = N`；欲加"获取率"：改用 dynamic_modifier |
| `add_armor_attack_factor` / `add_land_breakthrough` / `add_special_forces_cap` / `add_production_speed_factory` | 1×4 | `NAT_Neo_Event.txt` | 皆为"施加某修正符"意图，需改用 `add_dynamic_modifier`（修正符名：`army_armor_attack_factor`/`breakthrough_factor`/`special_forces_cap`/`industrial_capacity_factory`） |
| `add_electricity` / `add_nuclear_research` / `add_doctrine_progress` / `add_garrison_template` | 1×4 | `NAT_Neo_Event.txt` | 原版无对应效果，需换机制（研究/资源/兵力） |
| `landmark_tunigi_hollow` | 1 | `history/states/STATE-492.txt` | 地标 id 需在 `common/buildings` 等定义过 |
| `FON_increase_Neuvillette_repulse_Primordial_Sea_cost_effect` | 1 | `common/decisions/FON_decisions.txt:221` | scripted_effect 疑似未定义/名不符 |
| `create_division_template` / `count` | 1+1 | `events/LYY_Keqing_Events.txt:68,98` | 原版无 `create_division_template`；`random_owned_state` 不支持 `count`。需换 `load_oob`/多段实现 |
| `modifier`(已修) / `value`(已修) / `limit`(1, `DOT_nuke_on_actions.txt:106`) / `end_wars`(1, `LAW_FocusTree_01.txt:4442`) | — | — | 属"合法键放错位置"，多数可结构调整；`limit` 在 `FROM` 内应包一层 `if = {}` |

> 说明：B 类在原版引擎里**不存在同名效果**，改名/包裹都无法凭空生效，属设计层问题，
> 需作者决定「改用哪个真实机制」或「补定义脚本」。这正是此前分批归类的 B 类（自创机制）。

### C. 数据参考文件
- `hoi4lint\effect_class.txt` — 33 个 token 的分类（UNKNOWN / VALID_VANILLA_KEY / NEAR）。
- `hoi4lint\effect_ctx.txt` — 每个 token 的源码上下文（文件:行 ±3 行）。

---

## 三、附：本批用到的产物
- 脚本：`add_shine.py`、`fix_effects_batch.py`、`classify_effects.py`、`extract_effect_ctx.py`
- 备份：`backup_shine\`（15 gfx）、`backup_effectfix\`（3 文件）
- 报告：`docs/DOT_第七批_shine与InvalidEffect报告.md`
