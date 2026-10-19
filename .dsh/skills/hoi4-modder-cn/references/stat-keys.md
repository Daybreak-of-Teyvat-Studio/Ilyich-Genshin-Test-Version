# 速查表

## 1. 单位属性 stat key（sub_units / equipment 直接写）

| 英文 key | 中文 | 说明 |
|----------|------|------|
| soft_attack | 对人员杀伤 | 对低装甲率目标 |
| hard_attack | 对装甲杀伤 | 对高装甲率目标 |
| defense | 防御 | 防守时闪避次数 |
| breakthrough | 突破 | 进攻时闪避次数 |
| hardness | 装甲率 | 0–1，越高越耐 soft_attack |
| armor_value | 装甲厚度 | 高于敌方穿甲则减伤 |
| ap_attack | 穿甲深度 | 高于敌方装甲则增伤 |
| max_strength | HP | 承受伤害能力 |
| max_organisation | 组织度 | 归零无法战斗/移动 |
| default_morale | 恢复速度 | 无战斗时每小时恢复组织度 |
| suppression | 镇压能力 | 镇压反抗 |
| weight | 重量 | 影响海运/登陆运力 |
| supply_consumption | 补给使用 | 每日补给消耗 |
| fuel_consumption | 燃油使用 | 每日燃油消耗 |
| training_time | 训练时间 | 天 |
| combat_width | 战场宽度 | |
| maximum_speed | 最大速度 | km/h |
| reliability | 可靠性 | 0–1，越低越易故障 |
| recon | 侦察 | |
| entrenchment | 堑壕 | |
| additional_collateral_damage | 额外附带损害 | 对要塞/基建额外伤害（超重型火炮），**不是** soft_attack |

**海军**：`lg_attack`(轻型火炮攻击) `hg_attack`(重型火炮攻击) `lg_armor_piercing` `hg_armor_piercing` `torpedo_attack`(鱼雷) `sub_attack`(深水炸弹/反潜) `anti_air_attack`(防空) `surface_detection`(对海探测) `sub_detection`(对潜探测) `surface_visibility`(水面可见度，越低越好) `naval_speed`(节) `naval_range`(km) `shore_bombardment`(对岸炮击) `naval_dominance_factor`(制海权贡献)

**空军**：`air_attack`(对空攻击) `air_defence`(空中防御) `air_agility`(机动) `air_superiority`(空优) `air_range`(航程 km) `air_ground_attack`(对地攻击) `naval_strike_attack`(对海攻击) `strategic_bombing`(战略轰炸)

## 2. 国家修正 modifier key（ideas / static_modifiers）

| 英文 key | 中文 |
|----------|------|
| stability_factor | 稳定度 |
| war_support_factor | 战争支持度 |
| political_power_factor | 政治点数 |
| political_power_gain | 每日政治点数 |
| consumer_goods_factor | 消费品 |
| research_speed_factor | 研究速度 |
| production_factory_efficiency_factor | 生产效率上限 |
| production_efficiency_gain_factor | 生产效率增长 |
| factory_output | 工厂产出 |
| industrial_capacity_factor | 工业产能 |
| construction_speed_factor | 建造速度 |
| local_resources_factor | 战略资源获取 |
| local_manpower | 当地人力 |
| army_org_factor | 陆军组织度 |
| army_org_regain | 陆军组织度恢复 |
| army_attack_factor | 陆军攻击 |
| army_defense_factor | 陆军防御 |
| army_speed_factor | 陆军速度 |
| supply_consumption_factor | 补给消耗 |
| attrition | 损耗 |
| experience_gain_factor | 经验增长 |
| training_time_factor | 训练时间 |
| experience_gain_army_factor | 陆军经验增长 | 仅陆军；`experience_gain_factor` 为全兵种 |
| army_leader_start_level | 新陆军指挥官初始等级 | 加算到将领基础等级（1→+1） |
| max_command_power | 最大指挥点数 |

命名规律：`X_factor` = 百分比乘算，`X_gain` = 每日加算（如 `political_power_gain`）。单位专属用 `army_`/`navy_`/`air_` 前缀。

注意：`command_cap` 已失效 → 用 `max_command_power`（绝对数值）。`category_army` 不是合法 equipment_bonus 类别（只在 modifier/学说作用域有效），装备加成只能写具体装备 key。

## 3. 触发器 trigger 速查

- **逻辑**：`AND = { }` `OR = { }` `NOT = { }`
- **国家**：`tag = GER` `original_tag` `exists = yes` `is_ai = no` `has_government = communism` `is_in_faction_with = X` `is_subject_of = X` `is_major = yes` `has_war = yes` `has_completed_focus = XXX` `has_idea = XXX` `has_country_flag = XXX` `has_global_flag = XXX` `controls_state = 123` `owns_state`
- **数值**：`check_variable = { var = X value = N compare = less_than/greater_than/equals }` `num_of_factories > 10` `has_manpower > 1000` `political_power > 50`
- **遍历**：`any_country = { ... }` `all_country` `any_owned_state` `any_state` `every_owned_state`（`count = N` 限制数量）
- **其它**：`date > 1939.1.1` `has_dlc = "Man the Guns"` `is_in_faction = no` `is_on_continent = europe`（7 大洲：`europe` `asia` `africa` `middle_east` `north_america` `south_america` `australia`）

## 4. 效果 effect 速查

- **政治**：`add_political_power = 100` `add_stability = 0.1` `add_war_support = 0.1` `set_politics = { ruling_party = X elections_allowed = no }` `set_popularities = { X = 100 }` `add_popularity = { ideology = X popularity = 0.5 }`
- **国家**：`set_country_flag = X` `clr_country_flag = X` `set_global_flag = X` `set_cosmetic_tag = XXX` `annex_country = { target = X transfer_troops = no }` `release = X` `puppet = X` `create_faction = X` `add_to_faction = X` `leave_faction` `declare_war_on = { target = X }` `set_rule = { can_create_factions = yes }` `change_tag_from = ROOT`（把玩家 ROOT 变成当前 tag；**必须放作用域块最后一行**，否则后续 effect 作用域失效报 Invalid Scope；ROOT 被删除，新 tag 需已存在且有领地，否则直接游戏结束）
- **地区（STATE scope）**：`set_state_owner_to = TAG`（注意不是 `set_state_owner`）
- **科技**：`add_tech_bonus = { ... }` `set_technology = { infantry_weapons = 1 }` `add_research_slot = 1` `set_grand_doctrine = <id>`（1.19 学说重构后旧 `set_technology = { mobile_warfare = 1 }` 失效，改用 grand doctrine id）
- **部队**：`division_template = { name = "..." regiments = { ... } }` `create_unit = { division = "name = \"...\" division_template = \"...\"" }` `add_manpower = 1000`
- **想法**：`add_ideas = XXX` `add_timed_idea = { idea = XXX days = 70 }` `remove_ideas = XXX`
- **变量**：`set_variable = { var = X value = N }` `add_to_variable` `subtract_from_variable` `multiply_variable` `divide_variable`
- **事件**：`country_event = { id = XXX_events.1 days = 5 random_days = 3 }` `news_event` `hidden_effect = { ... }`
- **国策**：`unlock_national_focus = XXX` `complete_national_focus = XXX`
- **控制流**：`if = { limit = { ... } ... }` `else_if` `else` `random_list = { 50 = { } 50 = { } }` `every_country = { limit = { ... } ... }`
