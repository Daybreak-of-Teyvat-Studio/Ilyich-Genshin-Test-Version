# 提瓦特黎明 Beta —— 代码 Bug 检查与修复报告（第二轮 / 重做版）

> ## ⚠️ 本报告所述的文件改动已于 2026-09-19 00:10 **全部回退**
>
> 原因：报告中 FIX-1「删除 4 个空占位同名文件」的判断**错误**——那些空文件是作者故意的「屏蔽开关」，
> 删掉其中的 `common/national_focus/generic.txt` 导致原版焦点树复活、与 MOD 的同名 `generic_focus` 撞车，
> **游戏在加载期直接崩溃**。
>
> 现在 MOD 已回到你提供的原始副本状态，并只打了两个针对崩溃的补丁。
> **请以 `docs/崩溃诊断与修复报告.md` 为最新依据**；本报告仅保留作为分析结论与待办清单的参考
> （第六节的设计层问题、遗留清单仍然有效），其中的「已修复」表述**不再代表文件当前状态**。


- **检查对象**：`Daybreak of Teyvat Beta Version`（HOI4 **1.19.3.0** Operation Postern）
- **本轮时间**：2026-09-18（重做）
- **权威依据**（三层交叉验证）：
  1. **游戏运行时日志** —— 以游戏自己的判定为准
     - 修复前：`crashes/hoi4_20260918_210717/logs/error.log`（11,471,018 B / 91,801 行）
     - 修复后：`crashes/hoi4_20260918_232550/logs/error.log`（390,774 B / 2,437 行）
  2. **原版 1.19.3 定义库**（`Hearts of Iron IV/`）逐项对照（模块名、资源名、修饰符名、分类名）
  3. **本 MOD 自带手册** `docs/DOT_HOI4_Modding_Skills.md`（HOI4 Modding 维基全集）
- **备份**：`C:\Users\XIANGZIYUAN\hoi4lint\backup_MOD_redo\`（本轮动手前 1,739 个脚本文件的完整快照）
- **脚本工具**：`C:\Users\XIANGZIYUAN\hoi4lint\`
  `redo_check.py`（状态核实）· `apply_fixes3.py`（第一轮修复器）· `apply_newfix.py`（第二轮修复器）· `fix_anr.py`（结构修复）· `worklist.py` · `verify_round2.py`

---

## 一、结论摘要

| 层级 | 结论 |
|---|---|
| **语法层** | 1,743 个脚本文件括号/引号（忽略注释与字符串后）**全部平衡**，无解析失败。 |
| **修复量** | 第一轮 **71 处** 重新应用；第二轮新增 **67 处实质修复** + 42 处无损规范化。 |
| **效果** | 上一轮修复已获日志证实：**报错体积 11.5 MB → 393 KB（降至 3.4%）**，其中 `has_tech`/`Invalid tech` 从 **175,740 行 → 0**。 |
| **最大新发现** | 两个原版**同名决议分类文件被不完整覆盖**，静默删掉了 **27 个原版分类定义**，牵连约 **190 条**报错；已从原版回填补齐。 |
| **剩余** | 约 **350 处** 可定位问题仍存在，绝大多数属「MOD 自造、脚本层无法实现」或「版本错配」，需作者决策（见第五节）。 |

> ⚠️ 本轮开工时发现：上一轮的修复成果**已被回滚**（`# FIXED:` 标记全部消失、`has_tech = mobile_warfare` 16 处重新出现、报告文件不见了）。当前工作区是一份**更新的副本**（比上一轮多 39 个文件、另 5 个文件被改动）。本轮即在**这份新副本**上重新完整执行。

---

## 二、第二轮新增修复（67 处）

### A. 【重大】决议分类被不完整覆盖 —— 回填原版 27 个分类

HOI4 按「路径+文件名」合并/覆盖：MOD 里放一个与原版同名的文件，**原版同名文件整份失效**。本 MOD 在这两个文件上做了**残缺副本**：

| 文件 | MOD 定义数 | 原版定义数 | 结果 |
|---|---|---|---|
| `common/decisions/categories/00_decision_categories.txt` | 24 | 28 | 丢失 `fascism_on_the_rise`、`democratic_on_the_rise`、`communism_on_the_rise`、`economy_decisions` |
| `common/decisions/categories/CHI_decision_categories.txt` | 11 | 34 | 丢失 `CHI_warlord_core_territories_cat` 等 **23 个** |

**后果**：原版 `political_decisions.txt`、`CHI_decisions.txt`、`CHI_warlord_decisions.txt` 里引用了这些分类的决议全部报 `Unknown category`，**牵连约 190 条报错、上百个决议被整条忽略**。

**处理**：按顶层块（depth-0）比对，把原版缺失的分类定义**原样回填**到 MOD 的两个文件末尾（已加 `FIXED:` 注释）。校验结果：**两者均 28/28、34/34，缺失 0**。

> 依据：`docs/DOT_HOI4_Modding_Skills.md` → *Mods* 页「Minimize overwrites of vanilla files」。

### B. 拼写与大小写（5 处）

| 文件:行 | 原 | 改 |
|---|---|---|
| `history/states/STATE-546.txt:21` | `manpowe r= 152215` | `manpower = 152215` |
| `common/decisions/DVA_decisions.txt:7495` | `arget_state = STATE_ID` | `target_state = STATE_ID` |
| `events/NewMOT_Knights_event.txt:3141` | `add_autonomy_score = { socre = 100 }` | `{ value = 100 }`（手册：参数名是 `value`） |
| `common/ideologies/00_ideologies.txt:244/245` | `moblization_speed` / `moblization_laws_cost_factor` | `mobilization_*` |

### C. 触发器 / 效果用法（19 处）

| 文件 | 问题 | 处理 | 依据 |
|---|---|---|---|
| `events/NewMOT_Knights_event.txt` ×2 | `has_country_leader = MOT_Noelle` | `has_country_leader = { character = MOT_Noelle }` | 手册：该触发器**必须带块**，`character = <token>` |
| `events/Eula_Event.txt` ×2 | `has_same_ideology = LAW` | `LAW = { has_same_ideology = yes }` | 手册：它是**布尔**（与 ROOT 比），不是目标参数 |
| `events/NAT_Neo_Event.txt` | `LIMIT = { IS_NAT = YES}`、`NAT_Get_Core = YES` | `limit = { Is_NAT = yes }`、`NAT_Get_Core = yes` | MOD 内定义的脚本化触发器名是 `Is_NAT`；`NAT_Get_Core` 是**效果**不是触发器 |
| `common/special_projects/projects/DOT_land_projects.txt:33` | `IS_LYY = YES` | `Is_LYY = yes` | 同上，MOD 定义名为 `Is_LYY` |
| `events/RAG_CM_Event.txt` ×10 | `is_puppet = YES`（且下一行重复一遍） | 合并为 `is_puppet = yes` | 布尔值须小写 |
| `common/national_focus/RAGv1_Focus.txt:865` | `all_other_country = { limit = {…} … }` | 去掉 `limit` 包裹 | `all_*` 是**触发器作用域**，不接受 `limit`（`every_*` 才需要） |
| `common/decisions/Faction_Help.txt:123` | `allowed` 里放 `any_other_country = {…}` | 移除（`available` 里已有同样检查） | 决策 `allowed` 不接受跨国外作用域 |
| `common/on_actions/ANR_influence_on_actions.txt`、`common/decisions/DOT_Up.txt` ×2 | `ELSE = { limit = {…} 效果 }` | `else_if = { … }` | `else` **不允许** `limit` |

### D. 修饰符 / 资源 / 单位属性名（10 处）

| 文件 | 原 | 改 | 依据 |
|---|---|---|---|
| `common/dynamic_modifiers/MOT_dynamic_modifiers.txt` ×4、`common/decisions/ANR_struggle_from_three_routes_decisions.txt` ×1 | `navy_doctrine_cost_factor` | `naval_doctrine_cost_factor` | 原版写法 35 处，`navy_` 形式 0 处 |
| `common/decisions/DOT_Activity_decisions.txt:266` | `stability = 0.01` | `stability_factor = 0.01` | 原版 `stability_factor` 1349 处，`stability =` 0 处 |
| `common/national_focus/SAN_Neo_Focus.txt:2287`、`events/SAN_Neo_Event.txt:1785` | `type = aluminum` | `type = aluminium` | 原版资源名只有 `aluminium` |
| `common/units/SUM_Units.txt:45/142` | 单位属性 `defence` | `defense` | 原版**单位属性**用 `defense`；`defence` 只出现在**地形修正块**里（该文件其余 7 处属此类，**未动**） |

### E. 结构错误：`on_monthly_RAG` 缺 `effect = { }` 包裹（1 处）

`common/on_actions/ANR_influence_on_actions.txt` 的 `on_monthly_RAG`（原 195–231 行）**直接**写了 `if = {`，而相邻的 `on_monthly_DVA` / `on_monthly_MOT` / `on_monthly_LAW` 都有 `effect = { }` 包裹。on_action 只认 `effect` / `events` / `random_events` 等键，所以它内部的 `if` 被判为非法键——这正是日志里两条 `Unexpected token: IF` 的真因。已补上包裹层，括号深度归零。

### F. 坦克模块名与重复键（3 处，其余见第五节 F）

| 文件:行 | 问题 | 处理 |
|---|---|---|
| `common/ai_equipment/generic_tank.txt:68` | `main_armament_slot = main_armament_slot = tank_close_support_gun`（键名写了两遍） | 收敛为 `main_armament_slot = tank_close_support_gun` |
| 同文件 ×2 | `tank_heavy_canon_2` | `tank_heavy_cannon_2`（原版存在 `_2`/`_3`，`canon` 少个 n） |

### G. 无损规范化（42 处，**非 bug**）

`common/on_actions/ANR_influence_on_actions.txt`(31) / `common/decisions/DOT_Up.txt`(10) / `common/decisions/DOT_Rule_Decisions.txt`(1) 中的大写 `IF = {` 统一为小写 `if = {`。

> 说明：HOI4 **同时接受**大写与小写关键字（本 MOD 全文有 8000+ 处大写 `AND/OR/NOT/IF/ELSE` 且绝大多数不报错），因此这 42 处纯属风格统一，**不修也不会报错**。此前误以为 `IF` 大写是致错原因，实际致错原因是上面的 **E 结构问题**。

---

## 三、第一轮修复（本轮重新应用，71 处）

因成果被回滚，以下修复在本轮**重新应用并逐条校验（0 处未命中）**：

| 类别 | 内容 |
|---|---|
| **空占位覆盖文件（3 个，删除）** | `common/continuous_focus/generic.txt`、`common/raids/land_infiltration_custom.txt`、`common/raids/paratrooper_raids_custom.txt` 均为 0 字节，等于静默删除原版同名内容 |
| **学说判定（16 处，**最大收益**）** | `common/ai_equipment/generic_tank.txt`：`has_tech = mobile_warfare / superior_firepower / trench_warfare / mass_assault` → `has_doctrine = new_mobile_warfare / superior_firepower / grand_battleplan / mass_assault`（1.19 学说已迁至 `common/doctrines/`） |
| **无效效果（15 块）** | 能力文件里 `add_temporary_buff_to_units`（1.19 不存在）→ 内容并入 `unit_modifiers` |
| **缺块效果/触发器** | `uncomplete_national_focus`、`custom_trigger_tooltip` 补 `{ }`；`puppet` 的 `end_wars` 子键收正 |
| **拼写** | `exist`→`exists`、`hsa_country_flag`、`stablity_factor`、`army_defense_factor`、`civilian_use`→`civilian_factory_use`、`industy`→`industry`、`infantry_equipment`→`infantry_weapons`、`add_timed_ideas`→`add_timed_idea` |
| **触发器/作用域误用** | `every_owned_state`→`all_owned_state`、`every_other_country`→`all_other_country`、`is_at_war_with`→`has_war_with`、`has_government_in_exile`→`is_government_in_exile`、`random_owned_states`→`random_owned_state`、`has_faction_members`→`is_in_faction`、`create_alliance`→`add_to_faction` |
| **数据损坏** | `state_flag` 乱码 `LYY_????_improved`→`LYY_state_infra_improved`、`LYY_??_built`→`LYY_state_industry_built`；失效条件 `days_sonce_decision_taken` 剥离 |
| **`limit` 位置** | `FROM = { limit = {…} }` → `FROM = { if = { limit = {…} … } }` |

**日志实证（修复前 vs 修复后）**

| 报错模式 | 修复前 | 修复后 |
|---|---:|---:|
| `has_tech` / `Invalid tech` | **175,740** | **0** |
| `add_temporary_buff_to_units` | 30 | 0 |
| `custom_trigger_tooltip` / 触发位 `custom_effect_tooltip` | 9 / 8 | 0 / 0 |
| `uncomplete_national_focus` | 1 | 0 |
| `Invalid effect 'limit'` | 2 | 0 |
| `civilian_use` | 5 | 0 |
| `Unknown trigger-type: exist` / `hsa_country_flag` | 1 / 2 | 0 / 0 |
| `days_sonce/since_decision_taken` | 4 | 0 |
| `add_timed_ideas` / `add_metal` | 4 / 2 | 0 / 0 |
| **日志总体积** | **11,471,018 B** | **390,774 B** |

---

## 四、如何验证本轮修复

1. 启动游戏，进主菜单即可（无需开局），退出。
2. 打开最新的 `Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log`。
3. **预期归零**：`Unknown category`（决议分类）、`manpowe`、`arget_state`、`socre`、`moblization`、`naval_doctrine_cost_factor` 拼错、`IS_NAT`/`IS_LYY` 大写、`is_puppet = YES`、`LIMIT`、`has_country_leader` 缺块、`has_same_ideology = LAW`、`type = aluminum`、`Unexpected token: IF`（ANR 那两条）、`Unexpected limit in an else block`（ANR/DOT_Up）、`tank_heavy_canon`。
4. 剩余报错应只剩第五节列出的设计类问题。

**回滚**：把 `C:\Users\XIANGZIYUAN\hoi4lint\backup_MOD_redo\` 下的文件按相同相对路径拷回 MOD 根目录即可（动手前完整快照）。单文件回滚就覆盖单个文件。

---

## 五、仍需你决策的问题（未改动）

按「投入产出比」排序。

### A. 自定义修饰符不存在（约 60 处，**机制问题**）
脚本层**无法**创造新修饰符，原版 `common/` 中 0 处、手册中 0 处：
- `common/ideas/DOT_Government.txt`：`mora_cost_daily`(28)、`mora_cost_ms`(6)、`mora_cost_io`(5) —— 「摩拉」是原创意，1.19 没有这个资源，需改用现成机制（如 `political_power_cost_factor` 或自定义动态修正）。
- `common/ideas/FOD_ideas.txt`：`convoys/destroyer/cruiser/fighter/tactical_bomber_production_speed_factor`(5) —— 1.19 无按舰种/机种的生产速度修饰符，建议改用 `production_speed_dockyard_factor` / `industrial_capacity_dockyard`。
- `air_close_air_support_attack_factor`（FOM/PBF/HZH ideas + HZH 动态修正，4 处）—— 手册里只有 `air_close_air_support_org_damage_factor`，名字对不上。
- 其他：`cavalry_speed_factor`、`motorized_speed_factor`、`special_forces_speed_factor`、`local_manpower_for_controller`、`equipment_bonus`(写在动态修正里)、`production_resource_need_factor`(写在 MIO 里)、`military_industrial_organization_research_bonus`、`naval_supremacy_factor`、MIO 里的 `soft_attack`。
- `common/ideologies/00_ideologies.txt`：`send_volunteers_size`、`industrial_capacity_factor`、`week_manpower` —— 这几个本身是合法修饰符，但**意识形态的 `modifiers` 块只接受有限子集**，需换成该块允许的写法。

### B. 6 字符「国家 TAG」（约 54 处，**最严重**）
`events/LYY_Ganyu_Events.txt` 把 `LYY_KEQ`/`LYY_SHH`/`LYY_NGL`/`LYY_JMG` 当国家 TAG 用，另外 `LYY_CloudRetainer`/`LYY_MoonCarver`/`LYY_MountainShaper`/`LYY_MadamePing` 也同理。HOI4 的 TAG **必须是 3 个字母**。
**方案**：(a) 新建 3 字母 TAG（`KEQ`/`SHH`/`NGL`/`JMG`…）并全局替换；(b) 若这些本不是国家，改用 `has_country_flag` / 变量表达。

### C. 引用但从未定义的 `scripted_effects`（5 个）
`NCup_Multi_Our_Points1`、`MOT_Re_Decisions_Support`、`INA_nuclear_fusion_crazy`、`INA_nuclear_fusion_calm`、`FON_increase_Neuvillette_repulse_Primordial_Sea_cost_effect`（最后这个在 `FON_scripted_effects.txt` 里被注释掉了）。**补定义**还是**删调用**？

### D. `events/NAT_Neo_Event.txt` 自造效果（13 个）
`add_infrastructure`、`build_fortifications`、`add_garrison_template`、`add_electricity`、`add_nuclear_research`、`add_land_experience_gain`、`army_experience_gain`、`add_armor_attack_factor`、`add_land_breakthrough`、`add_doctrine_progress`、`build_naval_base`、`add_special_forces_cap`、`add_production_speed_factory` —— 需逐个改写为 `add_building_construction` / `add_tech_bonus` / 国家修正等真实机制。

### E. 把「修饰符」当「效果」写在效果块里
- `common/decisions/NAT_Neo_decisions.txt:735/774/877`：`consumer_goods_factor`（在 `complete_effect` 内）
- `common/decisions/NewMOT_decisions.txt:1437/1447`：`free_building_slots`
- `common/decisions/LAW_decisions.txt:1967`：`targeted_modifier` 被嵌进 `modifier = {…}`（手册明确二者是**并列独立块**）
- `common/national_focus/SAN_Neo_Focus.txt` ×13：`num_of_factories = 2` —— 手册里 `num_of_factories` 是**触发器**（`num_of_factories > 10`），不是效果。加工厂应写 `add_offsite_building = { type = industrial_complex level = 2 }`（民用还是军用、离岸还是本州，需你定）。

### F. 【版本错配】坦克模块层级
`common/ai_equipment/generic_tank.txt` 引用的模块名有相当一部分在 1.19.3 **完全不存在**（MOD 自身也没定义，其 `units/equipment/modules/` 里只有一个飞机模块文件）：

| 引用名 | 原版 1.19.3 实际情况 |
|---|---|
| `tank_high_velocity_cannon_4` / `_5` | 最高只到 `_3` |
| `tank_heavy_cannon_4` / `_5` | 最高只到 `_3` |
| `tank_medium_cannon_3` | 只有 `tank_medium_cannon` 与 `_2` |
| `tank_anti_air_cannon_4` | 最高只到 `_3` |
| `tank_heavy_anti_air_cannon_3` / `_4` | 不存在该系列 |
| `tank_heavy_howitzer_2` / `_3` | 只有 `tank_heavy_howitzer`（无分档） |
| `tank_radio_4` / `_5`、`tank_radio_module` | 只有 `tank_radio_1/2/3` |
| `tank_composite_armor`、`tank_hydropneumatic_suspension` | 不存在 |
| `anti_tank_guided_missiles` | 不存在 |

**建议**：这个文件疑似来自其它版本/其它 MOD，建议整体按 1.19.3 的模块清单重做一次（我没有机械替换，因为层级语义靠猜会改坏 AI 设计）。

### G. 决议 `allowed` 块里的作用域（4 处）
`common/decisions/DRA_sucrose_decisions.txt:1161/1477/1603/1730`：`allowed = { FROM = { has_war_support < 0.8 } }` —— `allowed` 不支持 `FROM`。看上下文，这个检查更适合放进同决议已有的 `target_trigger`（那里 `FROM` 是合法的）。

### H. 师级模板（`events/LYY_Keqing_Events.txt`）
`has_division_template`（触发器）、`create_division_template`（效果）在 1.19 无此名；另有 `is_core`、`location`、`add_state_modifier: days` 用法待确认。

### I. 结构性「Unexpected token」（约 30 处，需逐个看语义）
| 文件 | 报错 |
|---|---|
| `common/national_focus/FON_focus.txt` ×7 | `Unexpected token: focus` |
| `common/scripted_guis/Peace_offer_peace_deal*.txt` ×2 | `context_type` |
| `events/RAG_NE_Event.txt` ×4 | `visible` |
| `events/DVA_events.txt` ×2 | `trigger` |
| `common/characters/*_Characters.txt` ×7 | `corps_commander` |
| `common/units/Ilyich_Hero.txt` ×4 | `fire_range` / `shore_bombardment` / `evasion` / `port_capacity_usage` |
| `common/ai_templates/DOT_templates.txt` ×3 | `regimental_support` |
| `common/scripted_effects/DOT_scripted_effects.txt` ×3 | `integer` |
| `common/military_industrial_organization/policies/_MOT_policies.txt` ×7 | `mio_policy_*` |
| `common/bop/KNA.txt` ×2 | `Unexpected token: =` |
| `common/technologies/PRI_Tech.txt` | `Entry doesn't exist: PRI_medium_tank` |

### J. 缺失贴图 / 精灵（约 300 行，148 个唯一）
`gfx/interface/goals/FOD/*`（约 40 个 FOD 国策图标）、`gfx/leaders/LY/Venti*`、`Nahida*`、`Eula3`、`gfx/interface/cabinet/*`、`gfx/generic_bg_*` 等 —— 属美术缺口，需补图或删除对应 `GFX_` 引用。

### K. `game_rules` 缺失（约 50 类）
`HOL_ai_behavior`(15)、`SWE_ai_behavior`(10)、`SPR_ai_behavior`(10)、`LIT_ai_behavior`(9)、`GRE_ai_behavior`(9)、`CHI/SOV/INS_ai_behavior`、`MOT_ChoosetheWay`(12)、`africa/americas_colonization_status` 等 —— 在 `common/game_rules/` 中补定义即可。

### L. `recruit_character` 写在事件里（约 20 处）
`events/NewMOT_Knights_event.txt`(12)、`events/INA_Events.txt`(8) —— 手册明确该效果**只能**出现在 `history/` 文件里（开局一次性执行），建议迁到 `history/countries/`。

### M. 其他
- **MIO 定义冲突**：`DOT_generic_organization.txt` / `ANR_organization.txt` / `NDK_organization.txt` 里大量 `parameter ... is both overridden and in delete_...`；`DVA_organization.txt` 里 `trait DVA_MIO_Navy_Trait_* has parent DVA_MIO_Air_Trait_* but this is not a valid parent`；`NDK_organization.txt` 有 `Duplicate database id DOT_Third_Round_Knockout`。
- `invalid on_win / on_lose / on_cancel event for start border war`（共 94 条）—— `start_border_war` 需要合法的 `on_win`/`on_lose`/`on_cancel` 事件 id。
- `invalid database object for effect/trigger: basic_medium_battery / advanced_centimetric_radar / improved_decimetric_radar`（73 条）—— 把**装备名**当变量用了，需显式写 `var:` 前缀或改用 `has_equipment`。
- `Invalid decision in has_active_timed_decision trigger: has_active_mission = PHI_investment_plan_#`（12 条）。
- `Duplicate idea. PRC_soviet_tribute_#`（6 条）、`Invalid focus: NDK_revise_law`、`Unexpected token: landmark_tunigi_hollow`（`history/states/STATE-492.txt:31`，地标未在 `common/buildings/` 定义）、`bad mission type: MISSION_SEARCH_AND_DESTROY`、`Invalid subunit: ranger_battalion`、`Invalid subunit category: category_MAR_aircraft`、`Not a valid value: LAW`（Eula 事件）、`Not a valid value: NAT_Faction`。
- `Couldn't find particle object "yw_Vernia_Blue_gundam_particle"`（16 条）。
- **.mod 描述文件不一致**：工作区 `Daybreak of Teyvat Beta Version.mod` 里 `path=` 指向 `D:/MOD/...`（实际在 C:，启动器读的是 `Documents/.../mod/` 下那份，不影响运行，但建议同步修正）。

---

## 六、给作者的两条工程建议

1. **不要再放「与原版同名」的空文件或残缺副本**。想屏蔽原版内容用 `.mod` 里的 `replace_path`；想覆盖就必须写完整内容。本轮两个分类文件、上一轮三个 0 字节文件，全是这一类事故。
2. **升级版本时优先核对四类**：① 学说 `has_tech` → `has_doctrine`；② 新效果在旧版不存在（`add_temporary_buff_to_units`）；③ 效果/触发器块语法（`uncomplete_national_focus`、`custom_trigger_tooltip`、`has_country_leader`、`puppet{end_wars}`）；④ 装备模块/修饰符的**版本改名**（本轮 F 组）。本轮与上一轮的绝大多数错误都源于此。
