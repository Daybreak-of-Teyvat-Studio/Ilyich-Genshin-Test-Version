# RA 项目实战笔记（Red Alert Descend）

> 由 `SKILL.md` 拆出：`SKILL.md` 只留铁律 + 分派（渐进披露），**项目实战经验全部在这里**。
>
> **不要整读本文件**（约 4.5 万字）。按下面的关键词索引 **Grep 后再读命中段落**；
> 每条 bullet 末尾的日期是经验获得的批次，便于判断新旧。

## 关键词索引

| 主题 | Grep 关键词 |
|------|-------------|
| 科技树 / 科技解锁 | `科技` `folder` `gridbox` `leads_to_tech` `enable_equipments` `隐藏科技` `set_technology` `建筑科技` |
| 兵种 / 装备 / 图标 | `sub_unit` `兵种` `装备` `icon` `texticon` `DDS` `双帧` `编制` `division_template` `carrier` |
| 决议 / 事件 | `决议` `decision` `visible` `available` `target_array` `on_map` `事件` `on_action` |
| 国策 | `国策` `focus` `cost` `prerequisite` `bypass` `scripted_localisation` `unlock_decision` |
| 角色 / 名字 / 本地化 | `角色` `character` `特质` `trait` `portrait` `头像` `本地化` `BOM` `名字` `ace` |
| 占领 / 顺从 / 抵抗 | `occupation_laws` `compliance` `resistance` `顺从` `抵抗` `占领法案` |
| 建筑 / 地标 / 州 | `building` `landmark` `add_building_construction` `add_offsite_building` `州 ` `state` |
| 阵营 / 超武 / 战争 | `create_faction` `faction` `核弹` `铁幕` `超时空` `天气` `wargoal` `start_border_war` `threat` `紧张度` |
| 排错 / 校验 | `error.log` `CWT` `RHoiScribe` `崩溃` `加载失败` `误报` `校验` |
| 脚本习惯 / 批量改 | `python` `PowerShell` `正则` `备份` `git` `反向` `docx` |
| 本项目事实（RA 专属） | `RAF` `开罗` `446` `埃及` `落地` `天选` `MCV` `资金` `抽奖` |

## 笔记正文（按获得批次排列）

## RA 项目验证过的经验（2026-09-02）

- **阵营专属科技树**：`technology_folders` 支持 `available = { has_global_flag = xxx }`（与 `has_dlc` 同法），按开局阵营 global flag 显示/隐藏文件夹；mod 内 RAF 科技 id 前缀用 `allies_ / soviet_ / yuri_` 区分阵营。
- **科技裸修正**：科技条目顶层可直接放修正键（如 `production_speed_buildings_factor = 0.05`，原版 industry.txt 即此写法），不需要 `modifier = {}` 块。
- **RHoiScribe**：`validate_hoi4_file` 传 mod 相对路径可独立校验（无需先 open workspace）；`open_hoi4_language_workspace` 参数名是 `workspace_root`。cmd 下多行 `python -c` 不可靠——写临时 .py 再执行。
- **PowerShell 内联改 Paradox 脚本拼 tab 字符串极易出错**：改用 python 脚本读写（`utf-8-sig` 读写自动处理 BOM；.txt 无 BOM，.yml 有 BOM）。
- **RHoiScribe 单文件校验误报（已知）**：单文件校验不解析 mod 的 scripted effects/triggers，`RAF_xxx = yes` 这类自定义调用会报 `Unexpected field` / `CW263` 误报；确认 `common/scripted_effects/` 里有定义即可忽略（本项目 `RAF_gain_cash`、`RAF_setup_role`、`RAF_starting_units` 等）。要精确校验请先 `open_hoi4_language_workspace`（参数 `workspace_root`）再 `validate_hoi4_project`（全 mod 输出约 810KB，用 python 解析计数，别塞进上下文）。

- **RA2 建筑→决议模式（2026-09-03）**：落地后建造决议组 `RAF_construction_category`（`allowed = { tag = RAF }`，`visible_when_empty = no`）。建筑决议模板：`days_remove = 30` + `modifier = { civilian_factory_use = 5 }`（占用民工，放 `modifier` 块）+ `remove_effect` 里首次 `set_variable`/`add_dynamic_modifier`、此后 `add_to_variable`；无 `cost` 字段即无 PP 消耗。**动态修饰符可引用国家变量**：`production_speed_buildings_factor = 变量名`（原版 8 处同款）。决议图标用 `GFX_decision_generic_construction`（`GFX_decision_generic_construct_*` 不存在）。MCV 选择标记 = `raf_mcv_allies/soviet/epsilon` global flag（RAF.1 三阵营也补设了，作为统一"选完基地车"信号）。
- **落地判定**：`RAF_finish_landing` 用 `change_tag_from = ROOT` 切 tag，落地后玩家 `tag = RAF`；决议分类的 `allowed` 用它把关。
- **决议次数上限**：执行计数用国家变量（缺失按 0 计），`available = { check_variable = { RAF_barracks_count < 19 } }`，`remove_effect` 里 `add_to_variable`。多档数值各挂一个变量、动态修饰符每行 stat 引用各自变量（如 training_time_factor / army_org_regain / army_attack_factor）。

- **sub_unit 要点（2026-09-03）**：定义放 `common/units/*.txt` 的 `sub_units = {}`；地形块直接写在兵种内（`forest/hills/mountain/desert/jungle/marsh/plains/river = { movement/attack/defence }`，river 块存在）；可靠性是 `reliability_factor`（维修连 0.05）；支援连互斥用 `same_support_type = <对方id>`；兵种本地化 key 只有 `id` 一个（无 _short）。RA2 步兵模板复制原版 `irregular_infantry`（soft_attack -0.05、defense -0.15 为负修正，"×N" 倍率按强度绝对值换算成正 offset）。

- **资源体系（2026-09-03）**：HOI4 现为 7 资源，定义在 `common/resources/00_resources.txt`（oil/aluminium/rubber/tungsten/steel/chromium/**coal**——铝是英式拼写 `aluminium`，煤炭存在！）。效果 `add_resource = { type = X amount = N }`，触发器 `has_resources_in_country = { resource = X amount > N }`。**"资源缺乏惩罚"的正确 key 是 `production_lack_of_resource_penalty_factor`**（`resource_lack_penalty` 不存在）——游戏自带文档 `F:\...\Hearts of Iron IV\documentation\modifiers_documentation.md` 是修正 key 的权威来源。
- **决议组信息展示**：决议组（category）没有 `desc` 字段（CWT 会报 CW263）；组级信息用 `custom_icon = { tag = RAF value = <变量> desc = <loc> visible = {} }`（tag 必填，原版 BUL/SOV 均此结构），loc 里可用 `$G[ROOT.变量]$!` 着色显示变量。**决议文件的分类包裹层里只能放决议**，分类定义（icon/visible 等）只能写在 categories/ 下。
- **RA 资金规则**：兑换所得计入 `RAF_cash_income`，花费计 `RAF_cash_cost`；所有建造类决议 `available = { check_variable = { RAF_cash_income > RAF_cash_cost } }`。**注意开局 0>0 为假——必须先卖资源才有资金建任何东西**（矿石精炼厂决议本身也受此限，需先有其它收入来源，否则死锁；兑换决议不受限）。

- **RA 资金与雷达兵种批次（2026-09-03）**：开局资金在 RAF.1/RAF.4 送 MCV 时 `set_variable = { RAF_cash_income = 20 }` / `{ RAF_cash_cost = 0 }`；建筑决议花费 = `complete_effect` 里 `add_to_variable = { RAF_cash_cost = 5 }`（点击即扣）。雷达类决议（苏雷达/盟空指部/尤里心灵感应器共用 idea `RAF_radar`：decryption=3 + 四系 intel_to_others 0.5）完成后 `set_country_flag = RAF_radar_built`，兵种科技 `allow = { has_country_flag = ... }`。**"×N 对空"的换算**：防空装备 AA1 `air_attack = 19`，兵种 offset = 19×(N−1)（防空步兵×3→38，重装大兵×8→133）。**防空步兵/重装大兵复制线列营 `anti_air_brigade`**（org 0、宽度1、需 anti_air_equipment 36），不是支援连 `anti_air`（org 0.2 纯 nerf）。旧遗留 sub_unit `rocketeer` 与新 `RAF_rocketeer` 并存，等用户清理。

- **NSB 旧式坦克装备复活模式（2026-09-03）**：原版 `common/units/equipment/tank_heavy/medium/light.txt` 里的 legacy 装备（heavy_tank_equipment_1 等）整块被 `#` 注释但仍可用——复制时原型块必须带 `is_archetype = yes` + `is_buildable = no`，变体用 `archetype = <原型>`；营 `need = { <原型id> = N }` 引用原型。**legacy 基准值**：heavy（soft15/hard12/brk36/def6/速5/甲70/费25）、medium（19/14/36/5/8/60/12）、medium SPG（soft42/hard1/brk3/def5/速8/费12）、light SPG（soft34/hard0.5/brk2/def4/速10/费8）。装备无 HP字段——"生命值+%"落在营的 `max_strength` 上。生产效率三 key：上限 `production_factory_max_efficiency_factor`、保持 `line_change_production_efficiency_factor`、增长 `production_factory_efficiency_gain_factor`。

- **NSB 科技解锁编制三件套（2026-09-03）**：让原版变形营可用 = 科技里同时 `enable_equipments`（底盘变体，如 `light_tank_aa_chassis_1`，由 x_tank_chassis.txt 的 duplicate_archetypes 宏生成）+ `enable_subunits`（如 `light_sp_anti_air_brigade`），照抄 NSB_armor.txt 模式。喷火系（light_tank_flame_chassis / light_flame_tank）走特殊项目无先例，暂不启用。两栖运兵船 = 复制 `common/units/equipment/convoys.txt` 的 convoy 原型（type = convoy，armor_value 0→10）；`support_equipment_1` 是支援连通用装备，科技里要显式 enable。

- **运输船池机制（2026-09-03）**：`type = convoy` 全游戏只有原型 `convoy` + 变体 `convoy_1`，自定义 convoy 型新原型**不会**计入运输船计数。要让"两栖运兵船"真正进船队：写成 `convoy` 原型的**变体**（`RAF_xxx_1 = { archetype = convoy  armor_value = 10 }`），科技 `enable_equipments` 它——与普通运输船同池同生产线，可切型号，零脚本。

- **图标迁移与旧条目删除（2026-09-03）**：兵种科技图标 = `GFX_<tech_id>_medium` → `gfx/interface/technologies/<folder名>/<tech_id>.dds`（换文件夹要连路径一起改）；兵种计数器图标 = `GFX_unit_<subunit_id>_icon_medium(+_white)` → `gfx/interface/counters/division_templates_{large|small}/`。迁移用"复制到新名+删旧文件+改 .gfx 注册"三步。删除兵种时记得全 mod 搜残留引用（history/OOB/事件）。**旧式飞行装备**：`x_plane_airframes.txt` 里 `jet_fighter_equipment` 原型未注释仍可用，新飞机做它的变体（同 convoy 技巧）。**air_ground_attack**：战斗机模板无该字段（=0），"+25%对地"按约定给 0.25（无实战意义，要 CAS 量级需手动给大值）。

- **RA 建筑前提链（2026-09-03）**：每个建筑决议完成时 `set_country_flag = RAF_<建筑>_built`（通用旗，一国只走一条阵营链所以无需按阵营分旗），下游决议 `available = { has_country_flag = 上游 }`。链：MCV(全局旗) → 发电厂 → 兵营/精炼厂 → 雷达/战车工厂/船坞 → 作战实验室 → 维修厂/超武/实验建筑。**组织度恢复没有分类修正**——只有 `army_org_regain`（全军）和 `local_org_regain`（州），"车辆/装甲专属恢复"做不了，只能全军或改营数据。占位科技模式：只有 `allow` 门控 + folder 位置 + 空 enable 块，等用户填。批量生成后必须跑逐段计数核对清单（python 统计 `- [x]`/`- [ ]`），字符串 replace 插行容易把旧行尾巴粘到新行上。

- **分类限定兵种修正（sub_unit modifiers，2026-09-03）**：`common/units/unit_modifiers/unit_modifiers.txt` 注册 `(兵种|category_分类, 后缀)` 对后，可在 idea/动态修正/决议里用 `modifier_army_sub_unit_<兵种或category_分类>_<后缀>` 做按兵种限定修正（AAT 学说的 `category = X` + 裸键是学说专属结构，idea 里用不了）。可用后缀仅 5 种：attack/defence/speed/max_org/**org_recovery_cap**_factor——**组织度恢复速度没有分类版**（army_org_regain 是全军），分类只能做"恢复上限"。mod 覆盖该文件 = 原版全量+追加注册。分类覆盖：装甲=category_all_armor，摩托化+机械化=category_vehicle_infantry，装甲车无分类用兵种 id 修饰。

- **RA 超武机制三件套（2026-09-03）**：① **状态域动态修正**：`add_dynamic_modifier = { modifier = X scope = ROOT days = 3 }` 在 state scope 可用（ETH_northern_thrust 模式），修正里用国家系修正（army_defense_factor/army_org_regain 等），scope = 生效国。② **地图点选决议**：`target_array = <全局数组> + state_target = yes + target_trigger + on_map_mode = map_and_decisions_view`，全局州数组用 on_startup `every_state = { add_to_array = { array = global.X value = THIS.id } }` 填充。③ **发射核弹**：`launch_nuke = { state = var:x use_nuke = no }`（country scope；state-targeted 决议里用 `set_variable = { ROOT.var = THIS.id }` 带出州 id；use_nuke = no 不消耗原版核弹，自带计数门控）。冷却用 `days_re_enable`。一次性信标 = state flag，传送 `teleport_armies = { to_state = PREV limit = { tag = ROOT } }`（limit 检查的是部队所有者）。**复制中心"训练复制单位"不可实现**（无单兵训练完成钩子）。

- **勘误（2026-09-03）**：地图点选全州决议**不需要自建数组**——引擎有内置集合 `game:all_states`（文档 documentation/script_collection_input.html），`target_array = game:all_states` 直接可用。原版决议没这么用只是因为原版从不需要"全州"目标（只打 core_states/固定 id 等子集）。同名机制：`game:all_countries`、`game:all_possible_countries`、`game:scope`。

- **create_unit 指定出生位置（2026-09-03）**：HOI4 没有 every_province 迭代器（那是 EU4/CK 的）；`create_unit` 用 **`country_score = { base = 1 modifier = { controls_state = event_target:X add = 1000 } }`** 给候选省份打分偏置到目标州（打分 scope 是省的控制国），配 `allow_spawning_on_enemy_provs = yes`。`create_unit` 还支持 `count = N`（多发生成）和 `id = N`（供 delete_unit 按 id 删）。批量按变量生成用 `for_loop_effect = { start = 0 end = <变量> compare = less_than ... }`。逐师移交归属没有效果——"缴获"= 计数+删除+等量重建（`change_division_template` 只换编制不换归属）。师编制模板可用 `division_template = { name is_locked regiments = { 营 = {x y} } }` 效果运行时创建（is_locked = yes 对玩家隐藏于设计器）。

- **角色与间谍（2026-09-03）**：characters 文件顶层是 `characters = {`（不是 TAG= {）；指挥官角色块 = **`corps_commander = { traits skill attack_skill... }`**（不是 army/unit_leader）；激活效果 `add_corps_commander_role = { character = <id> }`（activate_advisor 是顾问槽）。特工：`create_operative_leader = { bypass_recruitment = yes traits = {...} }`——**level 参数未证实**（9 级需求待解）。特性 id（00_traits.txt）：commando=特战军官、operative_well_groomed/escape_artist/safe_cracker/demolition_expert/master_interrogator/tough/natural_orator/seducer/infiltrator、infantry_leader=步兵指挥官、naval_invader=侵袭指挥官、invader_ii=两栖专家、naval_liason=海军人脉、guerilla_fighter=游击斗士、trickster=奇谋百出、war_hero=战争英雄、trait_reckless=鲁莽、motivated=充满动力；地形六件套=winter_specialist/winter_expert/desert_fox/swamp_fox/jungle_rat/urban_assault_specialist。
- **旧式飞机与舰船变体**：变体只覆写与原型不同的字段，其余继承。飞机无 重量/推力/布雷/扫雷/夜间惩罚/补给 字段（那是 BBA 模块/海军概念）；**舰船"搭载量"= air_capacity，原版船体不带（来自甲板模块）**——无槽位船体写 air_capacity 是超纲写法，CWT 会标红，游戏内需验证。舰船补给/天气惩罚字段未证实。快译名：对海瞄准=naval_strike_targetting、后勤打击=air_supply 任务、港口袭击=port_strike。

- **州控制权与师定位（2026-09-03）**：把某师所在州的控制权移交我方：`every_state → every_state_division（limit: division_has_majority_template = <子单位id> + owner = ROOT）→ PREV = { set_state_controller_to = ROOT }`——division_has_majority_template 参数是**子单位 id**（AAT bus 用例即此）。**海军船体额外有效字段**：`naval_weather_penalty_factor`（天气惩罚，基准 1，引擎会 -1 使用）、`naval_dominance_factor`；**无 air_capacity**（航母搭载量来自甲板模块，无槽位船体写 air_capacity CWT 标红、游戏内待验证）；**无 supply_consumption**（船只仅燃油）。中文"被弹系数"在 loc 无对应字段。

- **⚠️ 游戏崩溃/加载失败排查（2026-09-09 实战）**：CWT 校验 green **不代表游戏能加载**——CWT 不检查括号结构、字段有效性、scope 类型。真实 error.log 位置：`C:\Users\<user>\Documents\Paradox Interactive\Hearts of Iron IV\crashes\hoi4_<时间>\logs\error.log`。**本次找到的真实错误**：
  1. **多余 `}` 提前闭合块**（RAF_infantry.txt）：一个多余括号导致后面**所有**子单位解析失败，并连锁引发所有引用它们的科技报 "Entry doesn't exist in database"、所有装备报 "Malformed token"。**排查法**：用 python 逐行统计 `{`/`}` 深度，深度回到 0 后又出现内容 = 提前闭合。
  2. **旧式飞机装备（jet_fighter_equipment / jet_tac_bomber_equipment / jet_strat_bomber_equipment 等 `only_duplicate_archetype = yes` 原型）不支持 `allow_mission_type`**（那是 BBA 新式原型字段）——旧式用 `type = { cas strategic_bomber tactical_bomber air_transport }` 声明任务。
  3. **船体 `type` 值必须是 `screen_ship` / `capital_ship` / `carrier` / `submarine`**（不是 battleship/cruiser/light）。
  4. **`air_capacity` 不是有效字段**（航母搭载量来自甲板模块）。
  5. **`has_technology` 不存在，正确是 `has_tech`**。
  6. **`add_to_war` 正确语法**：`{ targeted_alliance = TAG enemy = TAG hostility_reason = asked_to_join single_target_only = yes }`。
  7. **state_target 决议**：`complete_effect` 里操作目标州必须用 `FROM = { }`（scope 是国家），`set_state_flag`/`teleport_armies` 都如此。
  8. **division scope 判断所有者**用 `OWNER = { tag = ROOT }`（不是 `owner = ROOT`）。
  9. **`artillery`/`field_hospital` 是子单位名不是科技 id**；artillery 默认 `active = yes` 无需解锁，野战医院科技 id 是 `tech_field_hospital`，工程连是 `tech_engineers`。
  10. **scripted effect 参数 `$amount$` 在决议调用处可能报 "Invalid effect 'amount'"**——改用国家变量传值更稳（`set_variable = { RAF_gain_amount = N }` + `RAF_gain_cash = yes`）。

- **⚠️⚠️ 装备文件名加载顺序（2026-09-09 崩溃根因）**：Paradox **按 ASCII 排序加载文件**，`RAF_*.txt`（R=82）排在原版 `convoys.txt`(c=99)、`tank_heavy.txt`(t=116)、`x_plane_airframes.txt`(x=120) **之前**，导致 `archetype = convoy` / `jet_fighter_equipment` 引用**尚未定义的原型** → 报 `Malformed token: <原型名>` 并连锁引发 `Only airplane equipment types support carrier_capable`、`Unrecognized mission type` 等假错误。**修复：mod 内引用 vanilla 原型的装备文件必须用 `zz_` 前缀**（如 `zz_ra_air.txt`），确保最后加载。同理适用于其他引用 vanilla 定义的脚本文件。
- **编制里的火炮营是 `artillery_brigade` 不是 `artillery`**：`artillery` 是支援连（type 含 support），放进 `regiments` 会报 `Subunit is of support type: artillery`。
- **`army_defense_factor` 不存在**（美式拼写）——正确是英式 **`army_defence_factor`**；军队防御类修正全用 defence 拼写。
- **.gfx 文件绝不能有 BOM**：`Unexpected token: spriteTypes` 就是 BOM 导致的（写入时用 `encoding='utf-8'` 而非 `utf-8-sig`）。
- **target_trigger 里操作/判断目标州需 `FROM = { }`**（scope 是国家）。
- **division scope 判断归属用 `OWNER = { tag = TAG }`**（`owner = ROOT` 报 Unknown trigger-type）。

- **RA 事件链结构（2026-09-09 定稿）**：RAF.1 选阵营（萌指/奇才/异教/天选者）→ RAF.2 选落点（当前仅开罗 state 446，其余注释预留）→ 若天选者则 RAF.4 选初始 MCV，否则 RAF_setup_faction_mcv 按阵营直接发 MCV。**落点选项内**：先 `random_state` 存 `RA_landing_state`，再判断阵营走 RAF.4 或直接 `RAF_finish_landing`（后者含 change_tag_from = ROOT，是真正的"落地"）。脚本效果 `RAF_setup_faction_mcv` 按 role flag 发对应 MCV + 初始资金 20/0。**开罗 = state 446**（原版名 Suez，owner ENG / core EGY，state_category = wasteland）。
- **国策 bypass 用 scripted_trigger**：`common/scripted_triggers/RAF_scripted_triggers.txt` 定义 `RAF_settle_down_bypass = { capital_scope = { OR = { is_core_of = ... } } }`，国策里写成 `#bypass = { RAF_settle_down_bypass = yes }` 注释预留（用户要求暂不启用）。RAF_settle_down 定位 x=-2 y=0，其后续政治线整体平移 -8（shell_company/cairo/nile/rwanda x=-6，aid_ethiopia x=-7，intervene_spain x=-5）。

- **⚠️⚠️ change_tag_from 的 COUNTRY 级内容全部丢失（2026-09-09 发电厂决议点不了的根因）**：`RAF = { change_tag_from = ROOT }` 之后，玩家国家是**全新的 RAF**，之前设在 ROOT（原国家）上的 `set_technology`、`set_variable`、country flag **全部失效**——只有 **global flag** 能存活（这正是本项目用 `raf_role_*` global flag 的原因）。**规则：切 tag 前只能设 global flag；科技/变量/国家旗必须在 `change_tag_from` 之后、在 RAF scope 内设置**。本次修复：新增脚本效果 `RAF_setup_mcv_and_cash`（在 RAF block 内、change_tag_from 之后调用），负责按 global flag 授予 MCV 科技 + 初始资金 20/0；`RAF_setup_faction_mcv` 退化为只设 global flag。
- **`release_puppet` / `is_puppet_of`**：`ENG = { release_puppet = EGY }` 用英国自有州释放埃及为傀儡；判定用 `EGY = { is_puppet_of = ENG }`（trigger 文档确认）。`add_civil_war_target = TAG` 把 TAG 加为内战目标（双方）；`declare_war_on = { target = X type = annex_everything }`。**卡萨拉 = state 883**（原版名 Kassala，owner ENG / core SUD / rural）。

- **决议 visible vs available（2026-09-09 用户指正）**：**前置条件放 `visible`（不满足则决议整个不显示），资源/计数类条件放 `available`（显示但灰掉）**。本项目所有建造决议的 `has_country_flag = <建筑>_built` 已从 available 移到 visible（共 29 处 + 补漏 7 处），只有链条入口的 3 个发电厂决议按设计无前置。标准形态：
  ```
  visible = { has_global_flag = raf_mcv_allies  has_country_flag = RAF_power_plant_built }
  available = { check_variable = { RAF_cash_income > RAF_cash_cost } }
  ```
- **⚠️ Python 批量改多块文本必须反向拼接**：先用 `re.finditer` 收集所有块的 (start, end, new_text)，再 `for ... in reversed(spans): out = out[:s] + new + out[e+1:]`。若正向边改边用原始偏移，后续块索引全部错位——**本次实测：29 块改了 22 块，后 7 块被静默跳过**（不是损坏，是跳过，很难发现）。改完务必写检查脚本枚举每个块的期望状态。
- **`add_offsite_building = { type = industrial_complex level = 5 }`**：地图外民用工厂（不占州建筑槽），用于给无地/荒地开局的产能。州类别升级直接用原版脚本效果 **`ETH_upgrade_state_category`**（`common/scripted_effects/ETH_scripted_effects.txt`，链：wasteland→pastoral→rural→town→large_town→city→large_city，每次升一级；槽位 wasteland=0 / pastoral=1 / rural=2）。

- **⚠️ 原版埃及并不存在（2026-09-09）**：`EGY`（埃及）是合法 tag，但**开局 0 个州**——它的 8 个核心州（446 开罗/苏伊士、447、452、453、456、457、552、907）全部由 **ENG 直接拥有**，且 `history/countries/ENG - Great Britain.txt` 里 **`#puppet = EGY` 是被注释掉的**。所以任何 `country_exists = EGY` 守卫都会让"释放埃及"永远不执行（我踩过这个坑）。正确判定：`ENG = { any_owned_state = { is_core_of = EGY } }`。
- **释放为殖民领用 `release_autonomy`**（不是 release_puppet）：
  ```
  ENG = { release_autonomy = { target = EGY  autonomy_state = autonomy_colony } }
  ```
  自治等级常量在 `common/autonomous_states/*.txt`：`autonomy_colony`(殖民领)/`autonomy_puppet`/`autonomy_dominion`/`autonomy_integrated_puppet` 等。释放会按"你拥有且目标有核心"的州划界；判定目标是否已是自家傀儡用 `EGY = { is_puppet_of = ENG }`。

- **⚠️ 科技树 GUI 硬编码规则（2026-09-09 科技页面打不开的根因）**：HOI4 科技页面是**硬编码 GUI**，`technology_tags` 里每新增一个 `technology_folders` 条目，就**必须在 `interface/countrytechtreeview.gui` 里配套**：① 该 folder 的内容容器 `containerWindowType = { name = "<folder>" ... }`；② `folder_tabs` 内的 `buttonType = { name = "<folder>_tab" quadTextureSprite = "GFX_<folder>_tab" }`；③ `techtree_<folder>_item` / `_small_item` 项；④ **每个科技一个格子盒** `gridboxtype = { name = "<科技id>_tree" position = { x y } slotsize = { width height } format = "UP" }`。缺 folder 容器 → `Could not find "X" in window countrytechtreeview` + `Could not find "X_tab"`；缺格子盒 → `Found no grid box for tech <id>`，**任一缺失都会让整个科技页面渲染失败**。格子盒是**绝对像素锚点**（原版 `infantry_weapons` 与 `tech_trucks` folder 坐标同为 (0,-1) 却各有 140,325 / 140,620 的锚点，靠锚点区分位置）；`size` 可省略（不限范围），多科技可共用同一锚点、由其 `folder.position` 的 x/y 拉开间距（slot 像素 = 锚点 + (x*slotsize.w, ±y*slotsize.h)）。
  **（2026-09-22 补全：坐标语法 + 实测布局 + 本项目定稿做法）**
  ① **坐标不是顶层 `x`/`y`**——原版科技文件里 0 处顶层 x/y，正确写法是块内 `folder = { name = <folder> position = { x = <列> y = <行> } }`；`width = 2` 可并排写（CWT 不报错，是否真影响宽/窄项未在游戏内验证）。
  ② **像素 = 锚点 + (x*slotsize.w, y*slotsize.h)，x 向右、y 向下**。这套方向是从原版反推的：armour_folder 的 `gwtank_tree` 锚点 (0,0)，`basic_light_tank` x=-4 在左、`basic_heavy_tank` x=+4 在右，与 `armour_subtitle_light/medium/heavy`(-73/207/480) 的顺序一致（副标题 = 列像素 + 207）。
  ③ **本项目定稿（对"引擎按名字找盒子"和"按区域包含找盒子"两种实现都成立）**：每个在树科技一个 `gridboxtype = { name = "<科技id>_tree" position = { x = 0 y = 0 } size = { width = 4900 height = 1300 } slotsize = { width = 70 height = 70 } format = "UP" }`。**锚点全设 (0,0)** → 无论引擎挑哪个盒子，算出的像素都是 `(x*70, y*70)`，等于把 folder 坐标直接当格子坐标用，绕开了"科技怎么和盒子配对的"这个没定论的机制。
  ④ **画布滚动范围由该 folder 的 `techtree_stripes` 容器 `size` 决定**（不是格子盒）：三阵营并排要把它放大（本项目 2000x1300 → 4900x1300），否则滚不到第三个阵营。
  ⑤ 三阵营并排 = 同一 folder 内横向错开（盟军 x 1..22、苏联 +25 → 26..47、尤里 +50 → 51..68）；宽项容器 183x84 会溢出 70px 格，**同行两个宽科技至少间隔 3 格**，行步长 2 = 140px。
  ⑥ **在树 = 有 folder 块**（本项目 93 个）；隐藏科技保留 `folder` 之外的字段并**删掉 folder**（隐藏科技仍可被 `set_technology` 授予，本项目遗留 `kirov_airship` 就是国策授予的隐藏科技）。
  ⑦ **建筑科技"只授予不研究"**：`allow = { always = no }`（原版 `heavy_battleship`/`suicide_craft` 同法，可正常显示在树里、被授予后点亮），并让对应建造决议 `remove_effect` 里 `set_technology = { <建筑科技> = 1 }`。
- **多个 convoy 类型不被支持**：`Multiple convoy types are not supported` —— convoy 型装备只能有一个（`convoy` 原型 + 其变体）。变体上**不要**再显式写 `type = convoy`，否则会另建一个 convoy 类型。
- **`scripted_triggers` 文件没有外层 wrapper**（与 scripted_effects 一致）：文件直接写 `名字 = { ... }`；写成 `scripted_triggers = { 名字 = {...} }` 会报 `Unknown trigger-type: <名字>`。
- **角色 `name` 必须是本地化键**，不能写原始字符串（如 `name = "谭雅"`）。写原始字符串会让引擎查不到键 → 回退"自动生成名字" → 无名字表时报 `character_manager.cpp: Failed to generate a name for a character`。正确：`name = RAF_tanya` + 本地化 `RAF_tanya:0 "谭雅"`。
- **志愿军类有效修正**（`send_volunteers_economy_factor` **不存在**）：`send_volunteer_size`（派遣上限）、`send_volunteers_tension`（紧张度限制）、`send_volunteer_factor`、`send_volunteer_divisions_required`（所需师数）、`army_experience_from_volunteers`、`air_volunteer_cap`。
- **carrier-capable 空军子单位**必须有正的 `carrier_air_wing_size`，否则报 `Carrier-capable airwing sub-units must have positive non-zero 'carrier_air_wing_size'`（`type` 含 fighter 的子单位会被视为 carrier-capable）。

- **隐藏科技树的正确做法（2026-09-09）**：科技**不写 `folder` 块**就不进科技树——原版 549 个科技里 128 个（`cv_early_fighter`、`basic_light_td`、`supersonic_fighter1` 等）就是这样，合法且无需任何 GUI。要"隐藏"一批科技：删掉它们的 `folder` **和** `path`（path 是树连线，无 folder 时无意义）。副作用：这类科技**不能被手动研究**，只能用 `set_technology` 授予（事件/决议/抽奖）。反之若保留 folder，就必须在 `interface/countrytechtreeview.gui` 里为该 folder 配齐容器+页签+item，且**每个科技一个 `<科技id>_tree` 格子盒**，否则整个科技页面渲染失败。
- **⚠️ Python 正则里 `|` 的优先级陷阱（本次把 GUI 改坏）**：写多行块匹配时，
  `r'A\nB_(?:X|Y)_\w+C|D"'` 会被解析成 `(A\nB_(?:X|Y)_\w+C)` **或** `(D")`——第一支只匹配到前缀就停，导致"删除块"只删掉前两行、残留 `"` + 字段 + `}`。**教训：多行模板匹配一定要把所有分支用非捕获组包住**（`(?:...|...)` 整体），或干脆不要用 `|`。**改坏后修复用行级手术**：定位损坏起止行号，用 `lines[:start] + new_lines + lines[end+1:]` 重建，比继续用正则可靠。**改完必须复核**：括号总深度 = 0、无奇数引号行、关键命名元素数量与改动前一致、总行数对得上。

- **隐藏科技的授予闭环（2026-09-16）**：把科技从科技树隐藏（删 folder/path）后，**必须给每个科技补一条 `set_technology` 授予途径**，否则它永远拿不到。本项目的三条授予链：① **建筑决议** `remove_effect` 授对应阵营科技（建兵营→基础步兵系、雷达→雷达系、战车工厂→载具系、海军船坞→舰船+两栖运输、作战实验室→高级单位、控制中心→遥控坦克，共 16 个决议）；② **抽奖事件** 授隐藏科技（黑鹰/狙击手/坦克杀手/空降/恐怖分子/自爆卡车/磁能坦克 + 谭雅/鲍里斯）；③ **落地事件** 授 MCV。**验收方法**：写脚本枚举全部科技 id，汇总所有文件里 `set_technology = { X = 1 }` 的 X，差集即"不可获得"的科技（本次查出 2 个漏网）。

- **⚠️ `error.log` 是最快的验证器（2026-09-22 一次查出 4 个真 bug，静态校验全绿也照样有错）**：`Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log` 每次运行游戏都重写，**报错带文件名+行号**；先 `grep RAF` 过滤一遍，比任何静态检查都准。已踩过的四种：
  - `unexpected token ... ( 99.6 )` 并连带 `Invalid trigger 'complete_effect' / 'ai_will_do'`：**`check_variable` 不支持 `>=`**（只有 `>` `<` `=`），解析在 `>=` 处断掉、把后面所有块当成触发器读。改 `> 99.5` 即消。
  - `Subunit is of support type: artillery`：**行炮兵子单位是 `artillery_brigade`**；`artillery` 是支援连（`regimental = no` / `group = support` / `combat_width = 0`），写进 `division_template` 的 `regiments` 网格就报这个（支援连要写进 `support = {}`）。
  - `Duplicate focus name will cause database problems: COG_xxx`：**自建国策 id 撞了原版国策**（COG_* 是原版刚果国策树 `common/national_focus/congo.txt`）。改 id 后**必须同时补 `RAF_<新id>` 名称键 + `RAF_<新id>_desc` 描述键**（原 id 的名字能从原版借到，改了就只能自补；中文名可在 `<本体>/localisation/simp_chinese/WUW_focus_l_simp_chinese.yml` 抄）。注意国策里的 `set_country_flag = COG_*`、`add_autonomy_score = { localization = COG_* }` 是**另外的键，不要跟着一起改名**。
  - `Couldnt find texticon: unit_RAF_gi_icon_small`：**自定义子单位缺小图标 texticon**。texticon 定义在 `interface/texticons.gfx`，命名 `GFX_unit_<子单位id>_icon_small`（支援连/空军另有 `unit_air_*`、`support_*` 系列）。**补法（本项目 `interface/zz_ra_texticons.gfx`，41 个子单位 70 条）**：给每个自制子单位写一条 spriteType，`texturefile` 直接指向原版同类 dds（`legacy_lazy_load = no`），**不必自备贴图**、也不必覆盖原版 `texticons.gfx`（新文件名 `zz_ra_*.gfx` 即可，spriteType 名不冲突就行）。
    **⚠️ 坑：`gfx/texticons/` 里的实际文件名和 spriteType 名对不上**（空军的 spriteType 叫 `GFX_unit_jet_fighter_icon_small`，文件却叫 `unit_air_jet_fighter_icon_small.dds`；还有 `super_heavy_armor_icon_small.dds` 不带 `unit_` 前缀；`GFX_unit_penal_battalion_icon_small` 指向 `unit_penal_infantry_icon_small.dds`）。所以**不要自己拼路径**，要**从原版 `interface/texticons.gfx` 里解析 `name`→`texturefile` 映射**再取用（原版该文件里有 371 条，其中可用 162 条 plain + 29 条 nato；`GFX_nato_unit_*` 只覆盖步兵/工兵/防空/反坦/炮/骑兵/装甲/摩步/伞兵等 29 个，其余没有 nato 版——**只在原版确实有 nato 版时才写 `GFX_nato_unit_<id>_icon_small`**，否则玩家开 NATO 符号时会取到风马牛不相及的图标）。映射取值示例：动员兵/大兵/新兵→infantry、警犬/恐怖分子→irregular_infantry、疯狂伊文→penal_battalion、海豹→marine_commando、火箭飞行兵→paratrooper、犀牛→heavy_armor、灰熊/狂风/磁电/幻影/光棱→medium_armor、遥控坦克/恐怖机器人→light_armor、天启/战斗要塞→super_heavy_armor、多功能步兵车→mechanized、精神控制车/神经突击车/自爆卡车→armored_car、防空履带车→light_sp_anti_air_brigade、坦克杀手→medium_tank_destroyer_brigade、V3→rocket_artillery、雌鹿→helicopter_brigade、夜鹰→helicopter_transport、黑鹰→jet_fighter、基洛夫→strat_bomber。

- **角色（将领/顾问）"装不上"的五个必需件（2026-09-17 两湖将领 + 程潜内阁实战）**：拿到一张角色设计表时，逐项查这五处，少一个就是"装不上"：① `common/characters/<TAG>.txt` 有角色块；② `history/countries/<TAG>.txt` 有 `recruit_character = id`——**顾问也必须入池，否则不出现在顾问槽里**；③ 特质定义放在**对的目录**；④ `portraits` 的**分组要和角色类型配对**；⑤ `name =` 键有本地化。**验收脚本**：分别枚举角色块 id 集、history 的 `recruit_character` 集、`name` 键集、`traits` 引用集，各自求差集。
- **特质分两个目录，放错不报错但不生效**：**指挥官**特质（`type = land` / `trait_type = personality_trait`）放 `common/unit_leader/*.txt`；**顾问/国家领袖**特质放 `common/country_leader/*.txt`。两者都是文件内 `leader_traits = { ... }` 块的顶层键。
- **⚠️ 原版特质中文名反查法（本次靠它救回 4 个被误当"新特质"的原版特质）**：文档给的中文特质名**不对应任何现有本地化键**时，别急着新建特质，先反查原版：① 权威表在 `<本体>/localisation/simp_chinese/traits_l_simp_chinese.yml`（2500+ 条，`key:0 "中文名"`）；② **有些特质名只出现在 `<本体>/localisation/simp_chinese/modifiers_l_simp_chinese.yml` 的 `modifier_trait_<id>_xp_gain_factor` 里，且与 traits_l 的译名不同**——本次 `trickster` 在 traits_l 叫"奇谋百出"、在 modifiers_l 叫"**诡谋指挥官**"，文档用的正是后者。**两处都要查**；③ 仍查不到就按英文名语义匹配（`expert_delegator`="Expert Delegator"→专业委任者；`militias_officer`="Militias Officer"→民团首领；`bearer_of_artillery`="Bearer of Artillery"→炮兵将领）；④ **注意 RF 会覆盖原版译名**（`expert_delegator`：原版"知人善任"→RF"知人善任大师"；`inspirational_leader`：原版"魅力非凡"→RF"鼓舞人心"），判断文档中文名指向哪个 id 要**以游戏内实际显示的译名（RF/RFCN 的译名）为准**，不是原版译名。**实在定不了就直接问用户，别自己造特质充数**。
- **RF 的 `replace_path` 不含 `common/unit_leader`**（它 replace 的是 `country_leader`/`characters`/`ideas`/`names` 等）——所以**原版全部陆军/海军/特工特质在 RF 环境下仍可用**，可直接引用 `bearer_of_artillery`、`trickster`、`militias_officer` 等原版 id，无需复制定义。反向含义：`common/unit_leader` 下 mod 自己的文件是**追加**而非覆盖。
- **同名重复键的两种后果（都在本项目实测到）**：① 完全相同的重复（`XIA_Tan_Zhen_trait` 写两遍）→ 冗余，删一个；② **内容不同的重复（`XIA_Li_Shizhang_trait` 两个块，一个给 `non_core_manpower`/`resistance_damage_to_garrison`、另一个给 `land_mastery_gain_factor`）→ 后者静默覆盖前者，前一个块的修正一直没生效**。批量体检要专门扫"同名键出现 ≥2 次"。**但注意**：同一角色有**两个 `country_leader` 块且 `ideology` 不同是合法的**（一人对应多个意识形态），不是重复 bug，别乱删。
- **角色 `portraits` 分组必须和角色类型配对**：将军/元帅用 `army = { large = ... }`；国家领袖/顾问用 `civilian = { large/small = ... }`。**纯将领误写成 `civilian` → 将领头像显示不出来**（本次修了 7 个）。`large` 写**png 路径**或 spriteType 名都行（路径形式引擎自动处理，无需注册）；`small` 一般写 spriteType 名，**必须先在 `interface/*.gfx` 注册**。顾问小头像是 53×67 级别的**小图**（放 `gfx/interface/ministers/<TAG>/`），和将领的 156×210 不是一回事。
- **一个角色可以同时挂多个角色块**：`corps_commander`（将领）+ `advisor`（顾问）可共存（本次唐蟒既是将领又是"军长"）。**顾问槽的中文名可能反直觉**：本项目本地化把 `head_of_intel` 译作"**军长**"（不是"军事情报首脑"），所以 `slot = head_of_intel` 配"军长"是**对的**，别当 bug 改——**改槽位前先用脚本查这个 mod 自己的本地化怎么译**。
- **⚠️ 名字池里加具名王牌飞行员（ace）的做法与真相（2026-09-17）**：格式是 `common/names/<file>.txt` 的**国家块内**（与 `male`/`female`/`surnames`/`callsigns` 同级）写 `ace = { name = Leslie  callsign = Les  surname = Clisby  type = fighter }`。但要知道：**ace 没有立绘槽、无法定点招募、不能 `recruit_character`**，只能作为随机生成的同名王牌出现——文档说"做成王牌飞行员而非陆军将领"时，实际含义就是这个。全游戏只有澳大利亚(AST)定义了 6 个具名 ace。**RF `replace_path="common/names"`**，所以 mod 内加 ace 必须新建 `zz_` 前缀文件并**用平衡括号法从 RF 原文完整复制国家名字块**再加 `ace`（只写 ace 块会覆盖掉原 male/surnames 池）。RF 名字池是**罗马化**的，中文人名会显示成 "Bangfan Shi" 这种顺序。
- **同文件混用 tab 与空格缩进时，解析器必须两者都接受**：本项目 `XIA.txt` 老角色用 tab、新角色用空格。顶层块匹配若写成 `^(\t)([A-Za-z_]...)=\{` 只认 tab → **92 个角色只抓到 43 个**，静默漏一半。正确写法 `^[ \t]+([A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*\{\n`。
- **⚠️ 校验脚本自身的三个正则陷阱（本次骗过我一轮）**：① **非贪婪 + 提前截断**：`^[ \t]+ID[ \t]*=[ \t]*\{\n(.*?)\n[ \t]*\}\n` 会在**第一个** `\n\t\t}\n` 处停（即 `portraits` 的收尾），导致所有角色都报"无 corps_commander 块"——**校验必须用平衡括号法**（找到 `{` 后数深度）。② **`portraits` 里含 "traits"**：`traits\s*=\s*\{` 会匹配到 `por**traits** = {`，误报一堆 `GFX_*_minister`/`civilian`/`large`/`small` 是"未定义特质"——必须加否定前瞻 `(?<![A-Za-z_])traits\s*=\s*\{`。③ **注释行**：`(?<!#)\s*recruit_character` 的 lookbehind 检查匹配起点前一字符，而 `\s*` 可匹配零宽，所以 `# recruit_character = X` **照样命中**——要按行 `strip()` 后判断 `startswith('#')`。
- **批量块替换必须"先收集、再反向应用"**：存下所有 `(start, end, new)` 后 `sort(key=lambda x: -x[0])` 从后往前改。正向边改边用原始偏移 → 后续块索引全部错位。**改完必须写独立校验脚本逐项核对期望值**（本次核对 45 个角色的 role/skill/四维/特质数量，异常 0）。
- **无 git 的项目动手前先物理备份**：`copy <file> _backup_xxx\<file>.bak`。本次项目 `git` 不在 PATH 也不是仓库，全靠备份目录兜底。**改完同时核对 BOM 与换行风格**：`common/` 下脚本是无 BOM + LF，`history/` 与 `localisation/*.yml` 是 **BOM + CRLF**；Python 文本模式读取会把 CRLF 归一成 LF，写回就变 LF-only——要么接受统一 LF（无害），要么用 `newline=''` 显式控制。
- **cmd 下"看起来单行"的 `python -c` 也不可靠**：不止多行 `-c` 会静默不执行，**含 `|` 或多语句的 `-c` 也会**（本次多次无输出/被 shell 吃掉）。**一律写临时 `.py` 再执行**；控制台 GBK 代码页会把 UTF-8 中文显示成乱码，但重定向到文件后的内容是对的——**乱码不等于文件坏**。
- **从 .docx 设计表批量导入角色的解析要点**：① `word/document.xml` 的条目是 `<w:tbl>` 表格，按 `<w:tr>`/`<w:tc>` 分解，**图片在 `<a:blip r:embed>`**；② 单元格里**图片和文字混排**，名字单元格可能只含图片，解析名字时要**排除含图片标记的单元格**，否则会把 `<IMG:rId6>` 当人名；③ 尺寸比对可判定"这张头像是否已在 mod 里"——**逐像素 `np.abs(a-b).mean() < 1` 视为同一张**（本次 54 张里 37 张已在位）；④ 表里常有**单位手误**（防御字段写成 `.1`、留空、`larger` 键、单人两行不同数值），要逐列核对并在报告里点出来，不要默默按 0/空处理。

- **⚠️⚠️ `change_tag_from` 的作用域陷阱（2026-09-16 二次踩坑）**：`RAF = { ... }` 块里，**切 tag 之前**的语句作用在 valid 的 RAF 作用域上、且会延续到新玩家国家（`RAF_setup_role` 的政体/国旗就是靠这个生效）；**切 tag 之后**再写语句，作用域已失效 → 报 `create_unit -- invalid scope state` 之类的错误并静默失败（`add_offsite_building` / `set_technology` 也会一起失效）。**正确姿势：所有"给新国家"的授予（科技/变量/地图外建筑/生成部队）都写在 `change_tag_from` 之前、`RAF = { }` 之内**，不要写在事件选项里用 `RAF = { ... }` 事后补（那属于失效作用域）。也别把授予写在原国家（ROOT/事件选项自身作用域）上——那属于旧国家，切 tag 后全丢。
- **生成单位到指定州**：`create_unit` 用 `prioritize_location = <省份 id>`（不是州 id；HOI4 无"州→省份"的脚本迭代器，只能填字面省份 id）。state 446（开罗/苏伊士）的省份为 `1155 4073 9947 12049`。
- **`cv_small_plane_naval_bomber_airframe` 是旧式原型**（`type = naval_bomber`），**不支持 `allow_mission_type`**；同族还有 `jet_fighter_equipment`/`jet_tac_bomber_equipment`/`jet_strat_bomber_equipment`。旧式一律用 `type = { ... }` 声明任务（可列多个，如 `type = { naval_bomber cas strategic_bomber air_transport }`）。

- **⚠️ `create_unit` 必须在【州作用域】调用（2026-09-16 修"没兵"的根因）**：在国家作用域直接写 `create_unit` 会报 `effectimplementation.cpp: create_unit -- invalid scope state` 并静默不生成部队。原版一律包在州作用域里：`capital_scope = { create_unit = { division = "..." owner = TAG count = N } }` 或 `random_owned_controlled_state = { create_unit = { ... owner = PREV } }`。想生成在特定州 → 用该国的 `capital_scope`（先把首都设成目标州）或 `random_owned_controlled_state` + `prioritize_location = <省份id>`（省份 id，非州 id）。
- **人物姓名生成失败 → 已解（2026-09-17）**：`character_manager.cpp: Failed to generate a name for a character of origins X and for country X` = 该 tag / cosmetic tag 在 `common/names/` 里没有姓名池。原版 `00_names.txt` 按顶层块分块，未列出的 tag 回退 `default`，但 **cosmetic tag 不回退**。**关键证据：原版 `RAJ_UK` / `MAL_UK` 就是「cosmetic tag 作 key」的姓名块**（声明在 `common/countries/cosmetic.txt`），所以按阵营给装潢标签各写一块即可；而且这种块可以是**局部块**——只写 `male` / `female` / `surnames` / `callsigns`，省略 `prefix` / `operation` 也合法，缺的部分走 `default`。本项目做法：`common/names/zz_ra_names.txt`（UTF-8 **无** BOM）里 `RAF_soviet`←原版 SOV、`RAF_allies`←USA、`RAF_epsilon`←GER 三块整块照抄，`RAF`（兜底）/ `RAF_resistance`（天选者）/ `NILE`（「成立尼罗河军管区」国策给的标签）写三池合并块。**推论：mod 里凡是被 `set_cosmetic_tag` 用到的非原版标签，都要「三件套」齐全**——①姓名块（缺 → 名字生成失败刷日志）、②`common/countries/cosmetic.txt` 条目（只有 `color` / `color_ui` 两行即可，决定旗帜底色）、③本地化 key `TAG:0 "国名"`（缺 → 国名直接显示裸 tag）。RAF 系四个标签已齐；**NILE 缺 ②③（已报用户，未改）**。**从原版抠整块用括号配平脚本**（`^TAG\s*=\s*\{` 定位 + 深度计数找闭合括号）再改 key，不要手抄；块内 `operation = { <州id> = { o_xxx } }` 的州 id 是原版的，照抄无副作用。
- **RHoiScribe `validate_hoi4_file` 的参数名是 `path`**（不是 `file_path`；传错报 "path is required when content is omitted"）。

## 2026-09-17 批次经验（决议门槛 / 头像池 / 兵种图标 / 配平自查）

- **`civilian_factory_use` 不拦点击（重要）**：decisions 里 `modifier = { civilian_factory_use = N }` 只是「占用 N 个民工」，**不会**阻止玩家在民工不足时点决议（原版 348 处带该字段的决议里，239 处另外在 `available` 写了门槛）。要真正拦住必须在 `available` 加国家触发器：`num_of_civilian_factories_available_for_projects > N-1`（文档 `triggers_documentation.md`：COUNTRY scope，"check amount of civilian factories available for a new project to use"；原版 ARG.txt / AST.txt 等即此写法）。本项目 39 条建造决议 + 2 条兵营升级决议已全部补上。
- **随机角色头像池 `portraits/<file>.txt`**：顶层**按 tag / cosmetic tag** 分块，子节点 `army = { male/female }`、`navy`、`political = { <ideology> = { male } }`、`operative`、`scientist`。①**装潢标签可作 key**（原版 `RAJ_UK` / `MAL_UK` / `SAF_COM` / `INS_HOL` 就是），与 `common/names` 同理；②`operative` 原版**只在 `default` 里**给了 `GFX_portrait_operative_unknown`（无面剪影）→ 自定义 tag 想要有脸的特工必须自己写 operative 池（可复用该阵营 army 头像）；③`scientist` 池在 `portraits/998_scientist_portraits.txt`，按 `continent = { name = north_america/europe/africa/middle_east/asia/south_america/australia scientist = {...} }`，另有少量 tag 专属（PAK/RAJ/RAJ_UK/AFG/MEX/SAF…）；④查找顺序：tag → 大洲 → `default`。本项目：`portraits/zz_ra_portraits.txt`，`RAF_soviet/allies/epsilon` 分取原版 SOV/USA/GER 的 army+navy，operative 复用陆军脸，scientist 用对应大洲通用脸；`RAF`/`RAF_resistance`/`NILE` 为三阵营合并。
- **兵种计数图标可直接复用原版 DDS**：sprite 名 `GFX_unit_<subunit_id>_icon_medium`（兵牌大图）/ `_medium_white`（地图小图），`textureFile` 指向原版文件即可，无需自制美术。步兵：`gfx/interface/counters/divisions_large/unit_infantry_icon.dds` + `divisions_small/onmap_unit_infantry_icon.dds`；维修连：`divisions_large/support_unit_maintenance_company_icon.dds` + `divisions_small/support_unit_maintenance_company_icon.dds`。注意 `interface/subuniticons.gfx` 是**原版整份拷贝**（同名文件覆盖原版），新图标必须 append 到这份拷贝里。
- **`equipment_capture_factor`**：缴获装备比例修正（country 类，可写在 sub_unit 内，原版维修连 0.05、Ethiopia idea 0.4）；同族还有 `equipment_capture`（基础比例）与 state 类的 `equipment_capture_for_controller`。
- **`all_state = { limit = { ... } <trigger> }`**：STATE 迭代器的正向写法（"所有州都满足"），比 `NOT = { any_state = { ... NOT = { ... } } }` 可读得多；`all_state` 的 scope 是 any，`all_owned_state` / `all_controlled_state` 是 COUNTRY。
- **决议 `complete_effect` 里的 `if / else_if`**：工具提示**只显示当前条件为真的分支** —— 借这一特性可以做到「一条决议按当前选中状态显示不同效果」（本项目矿石精炼：7 条选资源 + 3 条选数量的动态提示）。
- **⚠️ 批量改完必须做括号配平自查（本轮真踩到）**：`common/scripted_effects/*.txt` **没有 wrapper**，文件末尾多一个 `}` 会让加载器报错、甚至影响解析（本项目 RAF_scripted_effects.txt 末尾多 1 个 `}`，2543/2544）。扫法：逐行累加 `{`/`}`（跳过 `#` 注释行与行内注释），最终深度必须为 0、顶层块数可数；同时检查 `is_locked`/旧字段等是否删干净。
- **RHoiScribe `validate_hoi4_file` 不校验字段/触发器名是否存在**：给它带 `zzz_bogus_trigger` 的内容照样 green（只做语法/结构校验）。要确认字段或触发器是否合法，查原版 `documentation/triggers_documentation.md`、`effects_documentation.md`、`modifiers_documentation.md`（每条都写明 Supported Scopes / Targets），或看 `documentation/modifiers_documentation.md` 的修正分类。该类文件是权威来源，比猜快。
- **给州加建筑（原版标准写法，2026-09-17 验证）**：STATE scope 里先 `add_extra_state_shared_building_slots = N`，再 `add_building_construction = { type = industrial_complex|arms_factory level = N instant_build = yes }`（原版 AFG/ARG 国策即此组合）。**顺序重要**：槽位不够时建筑不会落成。效果也可用在 `capital_scope = { }` 里（开局落地给首都州建筑就是这么写的）。
- **项目事实：开罗 = 苏伊士 = 州 446**：州文件是 `history/states/446-Cairo.txt`，但文件内注释写 `# Suez`，`state_category = wasteland`，开局 owner = ENG / core = EGY，infrastructure 3，省 12049 有 naval_base 2。讨论"开罗/苏伊士"别当成两个州。
- **`add_offsite_building`（地图外工厂）语义未验证**：原版效果文档只有一句 "Add an offsite building to a country"，**无法确认它是否计入 `num_of_civilian_factories_available_for_projects`（即能否用于建造工程）**。若出现"工厂数够但建造决议点不动"，优先怀疑这条，改用州内真实工厂（见上一条）。

- **⚠️ 触发器迭代器不能写 `limit`（2026-09-17 踩坑）**：在 `available` / `visible` / `trigger` 这类**触发器**块里，`any_state` / `all_state` / `any_owned_state` / `all_owned_state` / `any_controlled_state` 等**不支持 `limit = { }`**，条件必须直接内联（原版全库检索：触发器迭代器 + limit 的用例为 0）。`limit` 只属于**效果**迭代器（`every_state` / `every_owned_state` / `random_state` …）。因此「所有满足 A 的州都满足 B」在触发器里的合法写法是**双重否定**：
  ```
  available = {
      NOT = {
          any_state = {
              is_core_of = EGY          # A
              NOT = { is_controlled_by = ROOT }   # B 的否定
          }
      }
  }
  ```
  踩坑记录：本项目曾把它"优化"成 `all_state = { limit = { is_core_of = EGY } is_controlled_by = ROOT }`，结果 `limit` 不生效、条件变成对**全世界每个州**判定 → 国策永久不可用。
- **`has_opinion` 的方向**：scope 是**持有看法的国家**，`target` 是看法对象。要"英国对我方评价 > 50"写 `ENG = { exists = yes has_opinion = { target = ROOT value > 50 } }`（原版 `BRA_soviet_economic_aid` 就是 `SOU = { has_opinion = { target = ROOT value > 49 } }`）。写在 focus/decision 自己的作用域里检查的是**自己对别人的看法**，方向反了。
- **⚠️ 原版兵种图标「大图名 ≠ 小图名」**：`gfx/interface/counters/divisions_large/unit_X_icon.dds` 的地图小图常叫 `divisions_small/onmap_unit_Y_icon.dds`，Y 与 X 不一定相同，必须**逐个核实文件是否存在**，别按规律猜：
  - large `unit_medium_tank_antiair_icon` ↔ small `onmap_unit_medium_spaa_icon`
  - large `unit_light_tank_antiair_icon` ↔ small `onmap_unit_light_spaa_icon`
  - large `unit_light_tank_artillery_icon` ↔ small `onmap_unit_light_spart_icon`
  - large `unit_medium_tank_at_icon` ↔ small `onmap_unit_medium_tank_destroyer_icon`
  - large `unit_marine_commando_icon` ↔ small `onmap_unit_marine_icon`
  - large `unit_helicopter_brigade_icon` ↔ small `onmap_helicopter_brigade_icon`（**无** `unit_` 前缀）
  - large `support_unit_hq_icon` ↔ small `onmap_unit_hq_icon`；large `support_unit_anti_air_icon` ↔ small `onmap_unit_anti_air_icon`（support 前缀换成 onmap_unit_）
  - 注意原版还有带**尾随空格**的脏文件名（如 `support_unit_hq_specops_icon .dds`），引用前先 `dir` 确认。
- **给别的国家生成编制师**：`TAG = { division_template = { name = ... regiments = { infantry = {x y} } support = { engineer = {x y} } }  capital_scope = { create_unit = { division = "name = \"X\" division_template = \"X\"" owner = TAG count = N } } }`。释放出来的殖民领会继承宗主的部分科技，所以用原版 `infantry` / `engineer` 编制一般是有科技的；若对方没科技，编制会以空装备/未激活状态生成。

- **两套原版编制图标的分工（2026-09-17 确认）**：
  - `gfx/interface/counters/divisions_large|small/` = **兵器剪影**（`unit_heavy_armor_icon.dds`、`support_unit_maintenance_company_icon.dds` 等），适合坦克/飞机/支援连，按装备类型一眼可辨；
  - `gfx/interface/counters/division_templates_large|small/` = **徽记符号**编号集（`custom_template_000..121.dds`，注意 **044–064 缺号**，实存 101 个），画的是头盔、骷髅、闪电、动物、十字、帽子这类符号（119=德式钢盔、3=交叉步枪、4=闪电、6=城堡塔、7=棋子兵、19=兽爪、28=子弹、29=爆炸、30=准星、35=恶魔脸、40=棕榈树、112=齿轮雪花、121="HQ"字样、113=降落伞、108=大象、94=野猪、101=骷髅交叉骨），**没有坦克/车辆图形**。
  - 想知道某编号画的是什么：用 Pillow 读 DDS（`Image.open('x.dds')` 直接支持）拼成带编号的联络表 PNG，再当图片看即可（本项目就这么挑的）。
- **本项目兵种图标约定**：把选中编号的 `division_templates_*` 文件**复制进 mod 并改名**为 `gfx/interface/counters/division_templates_large/unit_<兵种id>_icon.dds` 与 `division_templates_small/onmap_unit_<兵种id>_icon.dds`（`Copy-Item` 基座→mod 方向），再在 `interface/subuniticons.gfx` 注册 `GFX_unit_<兵种id>_icon_medium` / `_medium_white`，`noOfFrames = 2`。原版 `custom_template_*` 大图 76×42、小图 30×12，直接复制无需转格式。

- **⚠️ 兵种计数器图标必须是「双帧」（宽度×2），别直接拿 `custom_template_*` 用（2026-09-17 踩坑）**：
  - `gfx/interface/counters/divisions_large/unit_*.dds` = **152×42**（= 2 帧 ×76），small `divisions_small/onmap_unit_*.dds` = **60×12**（= 2 帧 ×30），spriteType 用 `noOfFrames = 2`；
  - `gfx/interface/counters/division_templates_large|custom_template_NNN.dds` = **76×42 单帧**、small 30×12 单帧（原版给"编制图标选择器"用，注册时不写 noOfFrames）；
  - 把单帧文件按 `noOfFrames = 2` 注册 → 游戏按 38×21 切半，图标显示会坏。**必须并排拼成双帧**（或直接挑一个本来就是双帧的图）。
  - 本项目图标 DDS 是**未压缩 32 位**（`pf` fourCC = 0，文件 = 128 字节头 + w×h×4，`flags = 0x81007`），所以拼双帧可纯字节操作、不需要图像编码器：每行数据复制一遍，改头里 offset 16 的 `width` 与 offset 20 的 `linear size`（各 ×2）即可。
- **`support_unit_maintenance_company_icon.dds` 没有小图**：`divisions_small/` 里不存在维修连小图，最接近的是 `onmap_unit_armored_maintenance_icon.dds`。**引用前逐个 `os.path.exists` 核实**（大图存在 ≠ 小图存在）。
- **⚠️ `set_technology` 不触发科技的 `on_research_complete`（英雄/将领授予必须写两处）**：科技里写 `on_research_complete = { add_corps_commander_role = { character = X } }` 只有**手动研发**才触发；作战实验室那类决议是 `set_technology = { X = 1 }` 授予的 → 不跑，指挥官拿不到。**凡是"靠 set_technology 给出去"的科技，其 on_research_complete 效果必须在授予它的决议/事件里再写一遍**。本项目定稿：盟军作战实验室→谭雅、苏联作战实验室→鲍里斯、尤里作战实验室→尤里X（各自阵营决议内；谭雅/鲍里斯另有抽奖那条独立授予，尤里X 两条路都写了）。

- **⚠️ 覆盖用户自制美术前，备份必须「只写一次」（2026-09-17 真丢过一次文件）**：脚本重跑时若备份步骤是"把当前文件复制到固定备份名"，第二次运行就会**用已改过的文件覆盖掉原始备份**，原图随之永久丢失（本项目 `unit_RAF_rocketeer_icon.dds` 就这么丢的）。正确做法：备份名带时间戳/序号，或 `if not os.path.exists(bak)` 才写；改完立刻用像素校验确认，别等下一轮。
- **判断两个 DDS 是不是同一张图：比像素，不要比 md5**：同一像素经不同工具（PIL 保存 vs 逐字节拼帧）落盘的容器字节不同，md5 必然不同，容易误判"没改动"。用 `Image.open(a).crop(左半帧)` 与 `Image.open(b).convert('RGBA')` 做 `ImageChops.difference(...).getextrema() == ((0,0),(0,0),(0,0),(0,0))` 才算同图。
- **项目现成可复用的双帧图标**：`gfx/interface/counters/division_templates_large|small/` 下除了自己拼的，还有 `unit_tripod_automat_icon.dds`（152×42 + 60×12，三脚机器人，原为某废弃兵种留的）——恐怖机器人（RAF_terror_drone）现在就用它；spriteType 直接指这个文件即可，不必再复制一份。

- **本项目是 git 仓库（2026-09-17 确认）**：mod 根目录 `C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Red Alert Descend` 下有 `.git`（用户用 GitHub Desktop 管理）。所以误改/误删可用 git 找回；**报告改动时可以直接提示用户「git 里能回退」**。另外：环境自带的"Is a git repository"探测在该目录返回 no，别信，自己 `os.path.isdir('.git')` 查。
- **重复内容排查套路**：怀疑某科技/兵种是重复品时，比较「兵种块 + 装备块」的数值是否逐项相同（本项目 `RAF_magnetron_tank` 与 `RAF_tesla_tank` 数值完全一致 → 确认是复制品，已整体删除：科技+装备+兵种+抽奖池条目+图标注册+本地化）。

- **误删后的恢复手法（2026-09-17）**：先查 git 有没有可取的版本——`git -C <mod> show HEAD:<相对路径>`（GitHub Desktop 自带的 git 在 `C:\Users\LR\AppData\Local\GitHubDesktop\app-*\resources\app\git\cmd\git.exe`，PATH 里通常没有，用 python subprocess 调）。本项目多数新增文件是**未跟踪**或**在最后一次提交之后才加**的，`git show` 取不到 → 改用手边信息重建：**如果被删的东西有孪生兄弟（同构的科技/装备/兵种块），直接克隆孪生块再替换 id 即可**，数值天然一致、格式也干净。
- **本项目 git 现状**：仓库在 mod 根目录，用户按版本提交（`9.6`/`9.5`/`0.1`…），工作区常年有大量未提交改动 → **不要用 `git checkout/restore` 去"撤销某个文件"，会把该文件里其它未提交的改动一起丢掉**；要精确回退只能手改或克隆孪生块。

- **动态国策名 / 描述（2026-09-17 验证可用）**：HOI4 允许**焦点名与 desc 按条件变化**，用 `common/scripted_localisation/*.txt` 里的 `defined_text`：
  ```
  defined_text = {
      name = RAF_african_liberation          # 与 focus id 同名
      text = { trigger = { has_global_flag = raf_mcv_soviet } localization_key = RAF_african_liberation_soviet }
      text = { trigger = { has_global_flag = raf_mcv_allies } localization_key = RAF_african_liberation_allies }
      text = { localization_key = RAF_african_liberation_default }   # 无 trigger = 兜底
  }
  defined_text = { name = RAF_african_liberation_desc   ... }        # desc 要另建一个，名字加 _desc
  ```
  **接线**：本地化里写 `RAF_african_liberation:0 "[RAF_african_liberation]"` 和 `RAF_african_liberation_desc:0 "[RAF_african_liberation_desc]"`（方括号触发动态查找）。原版范例：`national_focus/paraguay_uruguay_shared_branch.txt` 的 `GUAY_rekindle_old_gripes` + `common/scripted_localisation/TOA_Guay_scripted_loc.txt`。触发器在**调用该 key 的作用域**里求值（焦点 = 国家作用域，所以 `has_global_flag` / `tag` 都可用）。
- **阵营分支判据用「已选基地车」的 global flag**（`raf_mcv_soviet/allies/epsilon`）而不是角色 flag（`raf_role_*`）——这样天选者（选了某一家的 MCV）也能正确落到对应分支。
- **吞并 / 入阵营写法**：`annex_country = { target = TAG transfer_troops = yes }` 写在**吞并方**作用域（原版 `BBA_Italy` 吞并 ETH 即此写法）；`add_to_faction = TAG` 写在**自己**作用域 = 加入 TAG 所在阵营（共产国际 SOV / 同盟国 ENG / 轴心国 GER）。

- **⚠️ 国策 `cost` 的单位是「周」（不是天）**：`cost = 10` = **70 天**（原版默认国策时长），所以想要 14 天要写 `cost = 2`、35 天写 `cost = 5`。本项目政治线原本的 `cost = 5` 就是 35 天。
- **`has_government = <X>` 的语义**：`X` 是**意识形态组**（communism / democratic / fascism / neutrality），判定"执政党是否属于该组"——子意识形态（stalinism / liberalism / fascism_ideology / despotism）会自动归入对应组，所以可以拿它做"按当前意识形态分支"的判据。**注意**：`has_ideology` 是**角色（CHARACTER）作用域**的触发器（查角色是否有某子意识形态的领袖角色），国家作用域不能用它。
- **本项目「阵营/意识形态」分支写法（定稿）**：先判 `has_government = communism/democratic/fascism`（天选者可自由选意识形态，所以要跟当前意识形态走），**仍为 neutrality 时回退到开局所选的基地车 flag `raf_mcv_*`**，避免中立国家落空。这套同时写在国策效果与 `scripted_localisation` 的 `defined_text` 分支里，两处必须同步改。

- **世界紧张度的读与写（2026-09-17，先踩坑后修正）**：
  - **读**：动态变量 `threat`，**量纲 0~1**（原版 `threat > 0.15` / `threat < 0.98`），可用于触发器，也可用于 `set_temp_variable = { x = threat }`。
  - **写**：效果 **`add_threat = <百分点>`**（COUNTRY scope；文档 "Adds country threat"；**负数可用**——原版 `bulgaria.txt` 有 `add_threat = -1`，德国莱茵兰 `add_threat = 5`）。另有 `add_named_threat = { threat = N name = X }`（具名威胁）。
  - **⚠️ 量纲不同**（读数 0~1、写入按百分点），"把紧张度设回旧值"的正确套路：
    set_temp_variable = { before = threat }  → 做推高紧张度的事（如 declare_war_on）→
    set_temp_variable = { delta = threat } → subtract_from_temp_variable = { delta = before } →
    multiply_temp_variable = { delta = -100 } → add_threat = delta
  - **教训**：查效果是否存在要**多试近义关键词**——我起初搜 `set_world_tension` / `add_world_tension` 在 exe 里都是 -1，真实名字却是 `add_threat`。用 python 读 `hoi4.exe` 的 bytes 搜 ASCII 名仍是最快最权威的方法（tension / threat / world_ / set_ / add_ 都试一遍）。
- **边界战争是「效果」，不只是决议字段**：`start_border_war = { change_state_after_war = no  attacker = { state = X num_provinces = N }  defender = { state = Y num_provinces = N } }`（用**州 id**，可带 on_win/on_lose/on_cancel/leader_score/dig_in_factor 等）。同族效果：`set_border_war`(STATE scope) / `set_border_war_data` / `cancel_border_war` / `finalize_border_war`。原版也在决议里写同名块（`common/decisions/CHI_warlord_decisions.txt`、`common/decisions/FRA.txt`）。
- **wargoal 的 type 取值**（从原版 `create_wargoal` 用例穷举，因为类型表不在 script_enums.txt）：`annex_everything` / `take_state` / `take_state_focus` / `take_claimed_state` / `take_core_state` / `liberate_wargoal` / `puppet_wargoal_focus` / `topple_government`；`create_wargoal` 可带 `expire = 0`（永不过期）。**"傀儡战争目标" = `puppet_wargoal_focus`**。
- **`is_on_continent = <大洲>` 是 STATE 触发器**（europe/asia/africa/north_america/south_america/australia），常用于"所有非洲州"这类范围判定；注意触发器迭代器不能写 `limit`（见上一条双重否定写法）。

- **`add_to_faction` 的方向（2026-09-17 关键纠正）**：效果写在**目标阵营方**作用域，参数是要被拉进去的国家——"我方加入苏联阵营"要写 `SOV = { add_to_faction = ROOT }`，写成自己作用域里的 `add_to_faction = SOV` 是**反的**（会被理解成我方把 SOV 拉进我方阵营）。原版用例：`DEN.txt: FROM = { add_to_faction = ROOT }`。
- **`on_civil_war_end` on_action**：可用来做"某国内战结束后给相关国家打标记"（ROOT = 内战赢家，FROM 即将被吞并）；内战的各分裂 tag 与原 tag 共用 `original_tag`，所以判 `original_tag = SPR` 能覆盖 SPA/SPB/SPC/SPD。
- **国策树"移植"原版国策的做法**：保留原 id（本地化白拿，含中文）+ 在 mod 本地化里**覆盖 `_desc`**写自己的文案；改 `cost`、删掉 `available` 里与本国无关的限制（`is_subject` / `has_government`）、把原版专用脚本效果替换成通用实现、把 `set_cosmetic_tag` 指到自家标签；**注意保留对方引用的 DLC 资产**（idea / 动态修饰符 / 事件）时会带 DLC 依赖。
- **小心"在块尾追加效果"**：用 `t.rfind('}')` 定位国策块尾再追加，很容易把新块加到**国策外层**（CWT 会报 `Unexpected block 'xxx'`）。正确做法是按大括号配平定位 `completion_reward = { ... }` 内部再插。

- **按 `id = X` 定位事件定义时的坑（2026-09-17）**：事件引用也长这样——`country_event = { id = RAFgacha.16 }` 里的 `id = RAFgacha.16` 会被普通正则先匹配到，于是拿到的是"引用"而不是"定义"。要定位定义请**用行首锚定**：`re.search(r'^\tid = RAFgacha\.16\s*$', t, re.M)`（定义体里 id 独占一行）。

- **单位插画 → 图标/DDS 的生成流水线（2026-09-17 验证）**：
  - 源图常是白底 JPG：先**中心裁切**到目标长宽比再 LANCZOS 缩放，然后**从四边泛洪**（4 邻域 BFS，阈值约 228）把与边缘相连的近白像素 alpha 置 0 —— 只删背景、不伤机体上的白色。
  - HOI4 的 DDS 直接用**未压缩 32 位**最稳：从一张已有的合法 DDS **克隆 128 字节头**（尺寸要一致），像素按 **BGRA** 写（PIL 的 RGBA 需交换 R/B）。本项目实测 144×61 未压缩 = 35264 字节。
  - **科技图标**约定：`GFX_<tech_id>_medium` → `gfx/interface/technologies/<阵营>/<tech_id>.dds`，**尺寸 144×61**（原版科技图标同尺寸），tech 里不用写 icon 字段。
  - **装备图片**约定：装备的 `picture = <名字>` 会去找 **`GFX_<名字>_medium`**（原版 `picture = archetype_heavy_tank_equipment` ↔ `GFX_archetype_heavy_tank_equipment_medium`）；原版 archetype 图只有 47–144 × 28–49，看着小，本项目统一用 144×61 也正常显示。

- **`create_ship` 效果**：`create_ship = { type = <船体装备id> equipment_variant = "<变体名>" name = "..." }`（COUNTRY scope，直接把船塞进预备舰队）。**`equipment_variant` 是必填**（CWT 会报 CW242 warning "expected at least 1"），值填变体名/装备 id；原版用例见 `common/decisions/GER.txt`（`type = ship_hull_cruiser_1 equipment_variant = "Hilfskreuzer"`）。
- **给飞机/装备**：`add_equipment_to_stockpile = { type = <装备id> amount = N }` ✓（不会凭空生成编制，只是入库）。
- **抽奖送师**：需要先有师编制模板。做法是写一个 scripted effect，按阵营 + `country flag` 守卫「只建一次」（`division_template = { name = ... regiments = { 单位 = {x y} } }`，营位 x 最多 5 列），再在奖品条目里 `capital_scope = { create_unit = { division = "name = "模板名" division_template = "模板名"" owner = ROOT count = N } }`（`create_unit` 必须在州作用域）。

- **On-map（地图点选）决议的写法（本项目定稿）**：决议里写 `target_array = game:all_states` + `on_map_mode = map_and_decisions_view` + `state_target = yes`，用 `target_trigger = { FROM = { ... } }` 限制可点击的州（`FROM` = 被点的州），效果里同样用 `FROM = { ... }` 操作该州（`set_state_flag` / `add_core_of = ROOT` / `teleport_armies = { to_state = FROM }` 等）。参见 `common/decisions/RAF_targeted_decisions.txt`（信标/传送）与本项目心灵控制塔。
- **"建筑存在 → 我方拥有核心"这类条件性领土**：用 **state_flag**（`set_state_flag` / `has_state_flag` / `clr_state_flag`，STATE scope）最省事——不需要新建 `common/buildings` 定义和图标、不占建筑位，而且州旗随州走（州被占领后由占领者拆除即可）。代价是没有州面板里的建筑图标。要"能看见的建筑"才需要走 building 方案（`common/buildings/*.txt` + `max_level = 1` 保证每州一座 + 图标 + `shares_slots`），并需要用 `free_building_slots` 之类间接判定存在性。
- **触发器**：`any_neighbor_state`（STATE scope，"存在相邻州满足条件"）用来做"与我国相邻"判定；`is_controlled_by` / `is_owned_by` / `is_core_of` 都是 STATE scope，参数可写 TAG 或 ROOT。

- **占领法案（occupation_laws）自定义**：`common/occupation_laws/*.txt`，**顶层直接写 `<law_id> = { ... }`**（不要外层 `occupation_laws = { }` 包裹，CWT 会报 `Unexpected block`）。字段：`icon`（图标条帧号）、`gui_order`、`visible`/`available`（占领国作用域）、`state_modifier`（`resistance_target` / `resistance_decay` / `compliance_gain` / `required_garrison_factor` / `no_compliance_gain` …）、`suppressed_state_modifier`（抵抗被压到 0 后改用这个）、`fallback_law`、`ai_will_do`。
- **按州设置/覆盖占领法案**：`set_occupation_law = <law_id>`（STATE scope 时给 **PREV**（占领国）设置该州的覆盖；`set_occupation_law_where_available` 会逐级回退尝试；`default_law` 是特殊值 = 清除覆盖）。直接改数值：`set_compliance = 99` / `set_resistance = 1`（STATE scope，单位是百分数）。
- **顺从度 / 抵抗度的作用**：顺从度≈被占领州可提供的**人力与工厂产出**比例（99% ≈ 本土水平），但**建筑位（工厂槽）不受其影响**——那是州类别/是否核心决定的。做"占领≈核心"的效果时用「自定义占领法案 + set_compliance」最快。
- **决议可见性**：`on_map_mode = map_only` 让决议只出现在地图上（决议面板里看不到，但**决议组仍在面板里可见**）；`map_and_decisions_view` 则两边都出现。

- **"顺从度高到一定程度就弹出建立新政权"的开关**：机制在 `common/resistance_compliance_modifiers/compliance_modifiers.txt`（**core_compliance_modifier** 分级：`threshold` + `margin` + `visible` + `enabled` + `state_modifier` + `on_enable`）。例：`compliance_80`（阈值 80）的 `enabled` 里要求 `is_available_to_collaboration_government`（vanilla 脚本触发器）+ `has_rule = can_create_collaboration_government`，`on_enable` 触发 `occupied_countries.1`。**要屏蔽就同名覆盖 `is_available_to_collaboration_government`**（mod 里新建 `common/scripted_triggers/zz_*.txt` 抄 vanilla 原文再加自己的 NOT 条件；脚本触发器按名字解析、同名覆盖是可行的做法，代价是要跟原版更新同步）。替代品：`set_rule = { can_create_collaboration_government = no }` 是**国家级别**开关，做不到按州区分。
- **modifier 的小数量纲**：文档每个字段都标了精度——`compliance_gain` 是 3 位小数（0.05 = +5%，1 = +100%）、`compliance_growth` / `resistance_decay` / `resistance_growth` / `resistance_target` 是 0 位小数（整数百分比）。写"翻倍"时按字段精度乘即可。`resistance_growth` 可以写负数来主动压制抵抗度增长（抵消对手的加抵抗 buff）。

- **地标建筑（landmark）自定义**：`common/buildings/*.txt` 里 `buildings = { <id> = { ... } }`，关键字段：`show_on_map`、`base_cost`、`damage_factor = 0`（不被战略轰炸损坏）、`icon_frame`、`value`、`is_buildable = no`、`spawn_point = landmark_spawn`、`level_cap = { province_max = 1 }`（**设置了 province_max 就是省级建筑**）、`always_shown`、`drawn_at_distance`、`dlc_allowed = { has_dlc = Gotterdammerung }`（原版地标带这条）。**3D 模型按「建筑 id 同名」自动绑定**：`gfx/models/buildings/landmarks/<建筑id>.mesh` —— 想在 mod 里复刻某座原版地标，只把它的 `.mesh` 复制成自己 id 的名字即可（贴图路径仍在原版，照常解析）。
- **脚本触发器当国策前提并显示成人话**：把判断写成 scripted_trigger（`RAF_tower_50 = { check_variable = { RAF_tower_count > 50 } }`），再给**同名本地化 key**（`RAF_tower_50:0 "心灵控制塔超过 50 座"`），国策 `available` 里引用它时就会显示这句中文而不是裸条件。
- **计数"拥有 X 座建筑/州的地区"**：不要指望能按 flag 遍历计数，最稳的是**自己维护计数变量**（建 +1、拆 −1、落地初始化 0），因为拆塔的决定性效果可能发生在别国作用域——用 `RAF = { add_to_variable = { X = -1 } }` 跨作用域扣减即可。

- **阵营（faction）脚本接口**：`create_faction = <loc_key>`（COUNTRY scope，建阵营；文档标注 deprecated、推荐 `create_faction_from_template`，但无 Deeper Factions DLC 时照常可用）、`set_faction_name = <loc_key>`（用本地化 key 设名字，不是字面字符串）、`set_faction_leader = yes`（把当前国家设为所在阵营领袖）、`add_to_faction`、`leave_faction`。**成员要由"领袖"来拉**：在领袖作用域里 `add_to_faction = <被拉的国家>`（例如 `every_country = { event_target:leader = { add_to_faction = PREV } }`）。
- **按数值选"最强国家"的写法**：`num_of_factories` 等既是触发器也是**动态变量**，可在 `every_country` 里 `set_temp_variable = { now = num_of_factories }` 逐个读取，再用 `check_variable = { now > best }` 比较并 `save_event_target_as = <名字>` 记住当前最优（事件目标在同一个事件的 effect 里有效），一趟遍历即可选出最大值，不必写阈值循环。
- **战争名不可脚本设置**：HOI4 的战争名来自宣战理由类型（`declare_war_on` 的 `type`）的本地化，`declare_war_on` / `create_wargoal` / `start_border_war` 都没有名字字段；想让某场战争有专属名字只能覆盖对应类型的 loc（影响所有同类战争）或改用新闻事件/横幅标题。

- **给自建国策配原版图标的最快路径（2026-09-26 政治线图标实战）**：不自己挑图，**按中文名反查原版国策再偷它的 icon**：① 原版 9832 个国策的 `id → icon` 用正则 `\n\t\tid = (\S+)\n(?:.*?\n)*?\t\ticon = (\S+)` 一趟扫全 `common/national_focus/*.txt`；② 中文名表从 `<本体>/localisation/simp_chinese/*.yml` 一趟 `key: "value"` 收进 dict（**别对每个 id 单独 regex 全文扫描**，20MB 文本 × 3000 次 = 卡死几分钟）；③ 按国策中文名关键词（"立足点/军管/协定/远征/南进/最后通牒…"）人工挑意思最近的。本项目定稿映射：安身立命→`GFX_focus_PER_foothold_in_indus`、借壳上市→`GFX_focus_prc_infiltration`、开罗谈判→`GFX_focus_generic_balkans_focus`、援助埃塞俄比亚→`GFX_focus_generic_befriend_ethiopia`、介入西班牙→`GFX_focus_focus_fra_intervention_spain`、军管区→`GFX_focus_FIN_strengthen_military_administration`、声索→`GFX_goal_generic_territory_or_war`、刚果协定→`GFX_goal_generic_forceful_treaty`、刚果远征→`GFX_goal_generic_more_territorial_claims`、解放非洲→`GFX_focus_generic_africa_liberation`、统一非洲→`GFX_focus_ARG_south_american_unity`、自力更生→`GFX_goal_reichsautobahn`、结交盟友→`GFX_focus_generic_diplomatic_treaty`、进军西奈→`GFX_focus_JAP_nanshin_ron`、跨过直布罗陀→`GFX_focus_attack_britain`、心灵终结→`GFX_focus_PER_last_thousand_years`、征服世界→`GFX_focus_GER_hegemony_over_europe`、新疆土→`GFX_focus_generic_annex_country_2`、赤色黎明→`GFX_focus_JAP_a_red_dawn_over_asia`、自由万岁→`GFX_goal_support_democracy`、洗脑行动→`GFX_focus_generic_fascist_propaganda`、尤里心灵终结→`GFX_goal_generic_secret_weapon`、最后通牒→`GFX_goal_demand_sudetenland`。原版图标无需在 mod 注册；用前批量验证 `name = "GFX_xxx"` 存在于原版 interface/*.gfx 即可。

- **⚠️ 批量脚本改坏文件后的处理次序**：①停止在坏文件上继续补丁（越补越碎）；②用 `git show HEAD:<相对路径>` 取最后一次提交的原始版（本项目用户按版本提交，HEAD 往往不含本轮改动，但结构完整）；③把本轮改动写成**可重放的脚本**（加民工门槛、加前置、加授予），在原始版上重跑一遍；④核对"决策/国策条数 + 括号配平 + CWT green"三项。**动手前先记下条数与括号数**，出问题才能判断丢了什么。
- **国策解锁决议要写提示**：国策通过 flag/前置解锁某决议或决议组时，在 `completion_reward` 里写 `unlock_decision_tooltip = <decision_id>` 或 `unlock_decision_category_tooltip = <category_id>`，玩家才看得到"解锁决议：XXX"；一个国策解锁多条时可写多行（缺点是玩家会看到不属于自己阵营的那几条）。

- **⚠️ HOI4 科技树的「前置」写法（2026-09-17 验证）**：科技**没有** `prerequisites` 字段（在子科技里写 `prerequisites = { X }` 会报 `CW264 Unexpected bare value 'X'`）。箭头来自**父科技体内的 path 块**：
  ```
  父科技 = {
      x = 7  y = 1
      path = {
          leads_to_tech = 子科技
          research_cost_coeff = 1
      }
  }
  ```
  子科技只需要自己的 `x`/`y`（以及 `width = 2` 表示宽图标、`folder` 归属）。写树 = ①每个科技给坐标 ②每个前置关系写成父科技的 path。
- **科技树布局惯例**：同一行的科技 x 间隔至少 4（宽科技占 2 格、再留 2 格间隙）；行距用 1；根科技放 y=1（或靠上），每往下一行必须有上一行的前置；解锁装备/兵种的科技用 `width = 2`（宽图标），纯功能/建筑科技用默认宽度（小图标）。
- **批量改科技块时同样要小心**：把坐标插进 `X = {` 时别把 `{` 挪到坐标后面（会变成 `X = 
 x = 7
 {` → 整文件报 bare value）。稳妥做法：正则匹配到 `^(	)(\w+) = ?
(coords)		\{` 后修正回 ` = {
`。
