# HOI4 版本破坏性改动速查

排查「以前能用、现在报错」的 MOD 时先看这张表。官方 wiki 反映最新版；若报错说明游戏版本更旧，则维基里的写法**不可用**，需向下兼容。

## 1.19（Operation Postern）

### 陆战学说迁出科技树 —— 影响最大
- 学说定义从 `common/technologies/` 迁到 `common/doctrines/`：
  - `common/doctrines/grand_doctrines/land_grand_doctrines.txt`（大国策）
  - `common/doctrines/subdoctrines/<folder>/*.txt`（子学说）
- 1.19 的四个陆战 grand doctrine id：`new_mobile_warfare`、`superior_firepower`、`grand_battleplan`、`mass_assault`
  （注意 mobile warfare 加了 `new_` 前缀，其余三个沿用旧名）
- 判定方式：
  - `has_tech = mass_assault` ❌ → `has_doctrine = mass_assault` ✅
  - 其他相关触发器：`has_any_grand_doctrine = land`、`has_subdoctrine_in_track = infantry`、`has_completed_subdoctrine`、`has_completed_track`、`has_mastery`、`has_mastery_level`
  - 相关效果：`set_grand_doctrine`、`set_sub_doctrine`、`add_mastery`、`add_daily_mastery`
- 旧写法 `trench_warfare` 等名字已不是有效 id（原版仅在 `history/countries/` 的**注释**里残留）。语义映射建议 `trench_warfare → grand_battleplan`。
- 典型报错：`<file>:<line>: has_tech: Invalid tech`（**消息里不带科技名**，只能用报错行号回原文件定位）。
- **怎么确定映射（别猜）**：`common/ai_equipment/generic_tank.txt` 这类文件是「四学说 × N 档」矩阵，块名前缀与学说一一对应（`BLITZ_*` / `SUPERIOR_*` / `TRENCH_*` / `SOVIET_*`），而且「默认档」的 `enable` 常写成 `NOT = { OR = { 四个学说 } }`——作者列的**就是四大陆战学说**，只是其中两个名字过期。用它反推映射，再拿原版 `land_grand_doctrines.txt` 的**顶层 id**（按第 1/120/254/369 行顺序：`new_mobile_warfare` / `superior_firepower` / `grand_battleplan` / `mass_assault`）逐个核对，即可确定 1:1 对应关系。

### 单位定义（`common/units/*.txt`）里的 `sub_units`：只有引擎说了算
1.19 的**舰船战斗属性来自装备/模块，不来自 `sub_units`**——原版 9 个海军单位的 `sub_units` 合计只用了 21 个键（`sprite` / `map_icon_category` / `priority` / `active` / `type` / `need_equipment` / `need_equipment_modules` / `max_organisation` / `supply_consumption` / `critical_parts` / `critical_part_damage_chance_mult` / `hit_profile_mult`）。

但**原版没用过 ≠ 非法**：`naval_speed`、`torpedo_attack`、`anti_air_attack`、`surface_detection`、`sub_detection`、`surface_visibility`、`sub_visibility`、`naval_range`、`search_and_destroy_coordination`、`convoy_raiding_coordination` 引擎全部接受（不报错）。

真正被移除的键会被**解析层**直接拒绝（`Unexpected token: <键>`）。1.19.3 实测已移除的：

| 键 | 替代说明 |
|---|---|
| `fire_range` | 主炮射程改由装备/模块决定 |
| `shore_bombardment` | 对岸炮击改由 `lg_attack` / `hg_attack` 决定 |
| `evasion` | 闪避改由 `naval_speed` 参与计算 |
| `port_capacity_usage` | 引擎完全不识别 |

→ 处理方式：**注释掉**（保留作者原意）。被拒绝的键本就不生效，所以注释后行为零变化。

### 引擎自动生成的修正符本地化
自建海军单位会缺一组引擎自动生成的键，报 `subunitdefinition.cpp: No localisation for modifier_experience_gain_<unit>_{training,mission,combat}_factor`。原版 `localisation/english/modifiers_l_english.yml` 里每个海军单位都有这 3 个，照体例补即可。

### 其他
- `add_resource` 用 `type = <resource> amount = <int>` 形式（不要写成 `add_resource = { steel = 100 }`）。
- 资源列表以 `common/resources/*.txt` 为准（`replace_path` 该目录时更要核对，常见的有 `metal` 这种其实并不存在的名字）。**1.19.3 实际只有**：`aluminium`（英式！`aluminum` 会报 `Invalid resource`）、`chromium`、`coal`、`oil`、`rubber`、`steel`、`tungsten`。

### 装备模块改名（AI 装备设计文件的重灾区）
`common/ai_equipment/*.txt` 里写的模块名必须与游戏版本的 `common/units/equipment/modules/` 对得上，否则报
`Invalid module name for module slot specification.` / `Invalid module name or module category name for AI equipment design specification.`。

1.19.3 实测规律：
- **一级模块没有 `_1` 后缀**：`tank_medium_cannon`（不是 `tank_medium_cannon_1`）、`tank_heavy_cannon`、`tank_high_velocity_cannon`、`tank_anti_air_cannon`。
- **各系列最高档不一致**：medium cannon 只到 `_2`；heavy / high_velocity / anti_air cannon 到 `_3`；`tank_heavy_howitzer` **无分档**；`tank_radio_1/2/3` 只有三档。
- 常见笔误：`tank_heavy_canon_*`（少一个 n）。
- 还有个隐藏坑：**同一行键名写两遍**（`main_armament_slot = main_armament_slot = tank_close_support_gun`）会被报成「无效模块名」，实际是键名重复。
- 结论：**不要凭记忆或从别的 MOD 抄**，一律以原版 `common/units/equipment/modules/` 的实际清单为准；层级语义靠猜会改坏 AI 设计，宁可整理成清单交作者确认。

### 修饰符名的两个易错点
- `navy_doctrine_cost_factor` ❌ → `naval_doctrine_cost_factor` ✅（原版 35 处用后者的写法）。
- 没有裸 `stability`，只有 `stability_factor`（原版 1349 处）。

### 单位属性：`defense` vs `defence`
- **单位属性块里是 `defense`**（美式）。
- `defence` 只在**地形修正块**里合法（`hills = { attack = … defence = … movement = … }`），原版 `common/units/*.txt` 里 158 处全是地形用法。
- 所以批量替换前必须先判断该行属于哪个块，否则会改坏地形数据。

## 1.17 前后

- `has_completed_track` 自 1.17 起可用。
- `has_doctrine` / `has_any_grand_doctrine` 属于本次学说体系。

## 1.14 前后

- 决策、事件、国策中的 `targeted_modifier` 一直是**与 `modifier` 平行的独立块**，任何时候都不能嵌进 `modifier = { … }` 里。若报 `Unknown modifier: targeted_modifier`，就是嵌套错了。

## 长期存在、易被误认为「版本问题」的坑

| 构造 | 规则 |
|---|---|
| `uncomplete_national_focus` | 必须 `{ focus = X }`；`complete_national_focus = X` 才是裸值 |
| `custom_trigger_tooltip` | 必须 `{ tooltip = X }` |
| `custom_effect_tooltip` | 是**效果**，裸值 `custom_effect_tooltip = X`；不能用在触发器块 |
| `puppet` | `puppet = X` 或 `puppet = { target = X end_wars = yes }`；`end_wars` 不是独立效果 |
| `add_country_leader_trait` | 只接受 trait（或 `ideology = …`），**没有** `character` 键；作用于现任国家领袖 |
| `recruit_character` | 只能出现在 `history/` 文件 |
| `limit` | 只能出现在 `if` / `else_if` / `random_list` / `random_owned_state` 等流程块内。**`else` 不接受 `limit`**（要与 `else_if` 区分） |
| `supply_units` | 是合法效果，常出现在能力的 `one_time_effect` 里，别误删 |
| 事件 `option` | 没有 `modifier` 子块 |
| 触发器位 | 不能用 `every_*` 效果：`every_owned_state`→`all_owned_state`，`every_other_country`→`all_other_country` |
| 变量运算在权重块 | `ai_will_do.modifier` 只能放触发器与 `set_temp_variable`/`multiply_temp_variable` 等**临时**变量运算；`multiply_variable`（非临时）会报 `Invalid trigger` |
| 国家 TAG | 必须**恰好 3 个字母**。`LYY_KEQ` 这类 6 字符会被当作未知效果/触发器 |
| `add_tech_bonus` 的 `category` | 必须是 `common/technology_tags/*.txt` 中 `technology_categories` 里声明过的类别（如 `industry`、`infantry_weapons`、`artillery`、`support_tech`、`electronics`）。常见笔误：`industy`、`infantry_equipment` |
| 大小写 | `IF`/`ELSE`/`ELSE_IF`/`AND`/`OR`/`NOT` 等关键字**大小写均合法**，不要当 bug 改 |
| `on_actions` 的子块 | `on_monthly_*` / `on_startup` 等**必须**写 `effect = { }`（或 `events` / `random_events`）；直接把 `if = { }` 放在下面会被报成 `Unexpected token: IF`，且整块不生效 |
| `has_country_leader` | 必须带块：`has_country_leader = { ruling_only = yes character = X }` |
| `has_same_ideology` | 是**布尔**（与 ROOT 比较），不是目标参数；要跟别的国家比就写 `TAG = { has_same_ideology = yes }` |
| `add_autonomy_score` | 参数是 `value = <float>`（还有 `localization`），不是 `score`/`socre` |
| 触发器作用域 | 触发器位用 `all_*`（`all_owned_state` / `all_other_country`）且**不接受 `limit`**；`every_*` 才是效果、才需要 `limit` |
| 决策 `allowed` 块 | 不接受 `from` / `any_other_country` / `is_ai` 等；这类判断应放 `available` 或 `target_trigger` |
| `else` 块 | **不允许** `limit`。想要「否则如果」用 `else_if = { limit = { … } … }` |
| `num_of_factories` | 是**触发器**（`num_of_factories > 10`），**不是**效果；效果块里加工厂要写 `add_offsite_building = { type = … level = … }` |
| 同名文件覆盖 | 三种破坏方式：**空文件**（很可能作者故意的屏蔽开关，见 SKILL.md 静默坑第 1 条）、**残缺副本**、**旧版本整份副本** |

## 排查顺序建议

1. 按消息模板计数，先啃数量最大的那一类（往往是单一根因在每 tick 重复求值，一次能消掉几万行）。
2. 再处理 `Invalid effect` / `Invalid trigger`（影响功能是否生效）。
3. 最后处理 `Unknown modifier`（影响数值是否正确生效）。
4. 贴图缺失、`GAME_RULE_MISSING`、`DIVISION_TOKEN` 属资源/定义缺口，与脚本逻辑无关，单独列给作者。
