# Paradox 脚本语法与文件写法模板

## 1. 基础语法

- 块：`key = { ... }`（内部 tab 缩进）
- 赋值：`key = value` —— 数字、标识符**不带引号**；字符串带双引号 `"..."`（如 `abbreviation = "INF"`、`sprite = "artillery"`）
- 列表：`key = { item1 item2 }`，元素各占一行
- 布尔：`yes` / `no`（**不是** `true`/`false`）
- 注释：`#`
- 数值可为小数或负数（如 `soft_attack = -0.4`）

## 2. 单位定义 common/units/*.txt

顶层 `sub_units = { ... }`，每个子单位一个 `name = { ... }` 块：

```text
sub_units = {
    infantry = {
        abbreviation = "INF"
        sprite = infantry
        map_icon_category = infantry
        priority = 600
        ai_priority = 200
        active = no

        type = { infantry }
        group = infantry
        categories = {
            category_front_line
            category_army
        }

        combat_width = 2
        max_strength = 25        # HP
        max_organisation = 60    # 组织度
        default_morale = 0.3     # 恢复
        manpower = 1000          # 人力

        training_time = 90
        suppression = 1.5        # 镇压
        weight = 0.5
        supply_consumption = 0.06

        soft_attack = 3.0        # 对人员
        hard_attack = 0.5        # 对装甲
        defense = 4.0            # 防御
        breakthrough = 0.5       # 突破
        hardness = 0.0           # 装甲度

        need = { infantry_equipment = 100 }      # 装备需求
        essential = { mechanized_equipment }     # 无此装备则属性失效
        transport = motorized_equipment          # 摩托化/机械化的载具

        forest = { attack = 0.1 defence = 0.1 movement = 0.15 }   # 地形修正
    }
}
```

关键字段：
- **分类**：`type`（infantry/support/motorized/mechanized/armor 等）、`group`、`categories`、`map_icon_category`（infantry/armored/other/ship/transport/uboat）
- **特殊兵种标志**：`special_forces` / `marines` / `mountaineers` / `rangers` —— 是 `categories = { }` 块里的**分类 token**，不是 yes/no 布尔标志
- **属性**：`soft_attack`(对人员)、`hard_attack`(对装甲)、`defense`(防御)、`breakthrough`(突破)、`hardness`(装甲度)、`max_strength`(HP)、`max_organisation`(组织度)、`default_morale`(士气恢复)
- **供给**：`manpower`、`supply_consumption`、`weight`(补给重量)、`suppression`(镇压)、`combat_width`(战场宽度)、`training_time`
- **装备**：`need = { equipment = 数量 }`、`essential = { equipment }`、`transport = xxx_equipment`
- **地形修正块**（可含 attack/defence/movement，可为负）：`forest` `hills` `mountain` `jungle` `marsh` `plains` `urban` `desert` `river` `amphibious`

## 3. GFX 注册 interface/*.gfx

```text
spriteTypes = {
    spriteType = { name = "GFX_xxx" textureFile = "gfx/..." noOfFrames = 2 }
}
```
原版用单行内联 + 空格对齐；mod 里多行展开等价。`textureFile` 路径相对 mod 根目录，通常不带引号（带了也兼容）。

## 4. 师编制 history/units/TAG_1936.txt

```text
division_template = {
    name = "模板名"
    division_names_group = XXX_INF_01
    regiments = {
        infantry = { x = 0 y = 0 }
        infantry = { x = 0 y = 1 }
    }
    support = { }
}

units = {
    division = {
        division_name = { is_name_ordered = yes name_order = 1 }
        location = 13240                # 省份 ID
        division_template = "模板名"
        start_experience_factor = 0.2
        start_equipment_factor = 1
    }
}

instant_effect = {                       # 开局生产
    add_equipment_production = {
        equipment = { type = infantry_equipment_0 creator = "TAG" }
        requested_factories = 1
        progress = 0.50
        efficiency = 80
    }
}
```

- 师编制模板用 `(x, y)` 网格排团，最多 5 列 × 5 行。`is_locked = yes` 禁止玩家编辑模板。

## 5. 本地化 localisation/<lang>/*.yml

```yaml
l_simp_chinese:        # 英文用 l_english:
 KEY: "中文文本"
```
- **本地化 .yml 必须带 UTF-8 BOM**（首字节 `EF BB BF`），否则整文件被 HOI4 静默忽略——事件标题/描述/选项全空白。`.txt` 脚本文件无需 BOM。写 .yml 用 `[System.IO.File]::WriteAllText($p, $text, [System.Text.UTF8Encoding]::new($true))` 或事后补 BOM。
- 变量 `$VAR$`；格式化后缀 `$VAR|H`（高亮）/ `|Y`（黄）/ `|R`（红）
- 内联颜色 `§Y...§!`（黄）、`§R...§!`（红）

## 6. 装备定义 common/units/equipment/*.txt（archetype / parent）

顶层 `equipments = { ... }`，用**原型（archetype）+ 变体（variant）**两级结构：

```text
equipments = {
    infantry_equipment = {          # 原型：定义基础属性，不可建造
        year = 1936
        is_archetype = yes
        is_buildable = no
        type = infantry
        group_by = archetype
        interface_category = interface_category_land
        active = yes

        reliability = 0.9
        maximum_speed = 4
        defense = 20
        breakthrough = 2
        hardness = 0
        armor_value = 0
        soft_attack = 3
        hard_attack = 0.5
        ap_attack = 1
        air_attack = 0

        lend_lease_cost = 1
        build_cost_ic = 0.43
        resources = { steel = 2 }
    }

    infantry_equipment_1 = {        # 变体：继承原型，覆盖差异
        year = 1936
        archetype = infantry_equipment
        parent = infantry_equipment_0
        priority = 10
        visual_level = 1
        defense = 22
        soft_attack = 6
        build_cost_ic = 0.50
    }
}
```

要点：
- 原型 `is_archetype = yes` + `is_buildable = no`；变体 `archetype = <原型名>` + `parent = <上级变体>`（链式升级）
- `visual_level` 控制 3D 模型等级；`priority` 控制 AI 选择权重
- `build_cost_ic`（工厂产出成本）、`resources`（steel/chromium/tungsten/oil/aluminum/rubber）
- 陆战属性：`defense` `breakthrough` `hardness` `armor_value` `soft_attack` `hard_attack` `ap_attack`(穿甲) `air_attack`

## 7. 舰艇：舰体与模块

舰艇作为**兵种**定义在 `common/units/destroyer.txt` 等，结构同 §2（`sub_units`），但 `type`/`group` 用 ship 类。舰艇的**舰体**与**模块**才是核心：

**舰体**（`common/units/equipment/ship_hull_*.txt`）是带 `module_slots` 的装备：

```text
ship_hull_light = {                 # 舰体原型
    year = 1922
    is_archetype = yes
    is_buildable = no
    type = screen_ship
    interface_category = interface_category_screen_ships
    alias = destroyer

    module_slots = {
        fixed_ship_battery_slot = {
            required = yes
            allowed_module_categories = { ship_light_battery dp_light_battery }
        }
        fixed_ship_engine_slot = {
            required = yes
            allowed_module_categories = { light_ship_engine }
        }
        mid_1_custom_slot = {
            required = no
            allowed_module_categories = { ship_torpedo ship_anti_air ship_depth_charge }
        }
    }

    module_count_limit = {           # 模块数量限制
        category = ship_radar
        count < 2
    }

    default_modules = {              # 默认装载
        fixed_ship_battery_slot = empty
        fixed_ship_engine_slot = light_ship_engine_1
        mid_1_custom_slot = empty
    }

    # 海军专属属性
    lg_attack = 0                   # 轻炮
    hg_attack = 0                   # 重炮
    torpedo_attack = 0
    sub_attack = 1                  # 反潜
    anti_air_attack = 0
    armor_value = 0
    surface_detection = 20          # 水面探测
    sub_detection = 2.5             # 反潜探测
    surface_visibility = 10         # 水面可见度（越低越好）
    naval_speed = 32
    naval_range = 2000
    fuel_consumption = 0
    naval_dominance_factor = 20     # 制海权贡献
    max_strength = 25
    build_cost_ic = 400
    resources = { steel = 2 }
    manpower = 250
}
```

- 舰体类型 `type`：`screen_ship`(护卫) / `capital_ship`(主力) / `submarine` / `carrier` / `transport`
- 变体继承：`module_slots = inherit` 整体继承；或逐槽 `fixed_ship_battery_slot = inherit` + 重写某槽
- `default_modules` 槽位值：`empty`(空) / 模块名 / `inherit`

**模块**（`common/units/equipment/modules/00_ship_modules.txt`）：

```text
equipment_modules = {
    limit = { has_dlc = "Man the Guns" }

    ship_light_battery_1 = {
        abbreviation = "saa"
        category = ship_light_battery
        sfx = sfx_ui_sd_module_turret

        add_stats = {               # 加算
            lg_attack = 1
            build_cost_ic = 90
        }
        multiply_stats = {          # 乘算（百分比，负值减速）
            naval_speed = -0.01
        }
        add_average_stats = {       # 按数量平均（穿甲用）
            lg_armor_piercing = 1
        }

        can_convert_from = {        # 改装来源
            module_category = ship_light_battery
            convert_cost_ic = 60
        }
        critical_parts = { damaged_light_guns }
    }
}
```

模块三种数值修改：`add_stats`(直接加)、`multiply_stats`(百分比乘)、`add_average_stats`(按数量平均，用于穿甲)。`parent = <上级模块>` 链式升级。改装 `can_convert_from = { module_category = ... }` 或 `{ module = ... }`。

## 8. 国策 common/national_focus/*.txt

```text
focus_tree = {
    id = china_warlord_focus

    country = {                     # 适用国家（factor 加权 + modifier）
        factor = 0
        modifier = {
            add = 10
            OR = { tag = YUN tag = SIK }
        }
    }

    default = no
    continuous_focus_position = { x = 50 y = 1350 }

    focus = {
        id = CHI_secure_internal_politics
        icon = GFX_goal_generic_major_alliance
        x = 6
        y = 0
        cost = 10

        prerequisite = { focus = XXX }          # 前置国策
        mutually_exclusive = { focus = YYY }    # 互斥国策

        available = { }              # 可见/可点条件
        bypass = { }                 # 自动跳过条件
        cancel_if_invalid = yes
        continue_if_invalid = no
        available_if_capitulated = no

        ai_will_do = { factor = 1 }

        completion_reward = {        # 完成效果
            add_political_power = 100
        }
    }
}
```

要点：
- `id` 全局唯一，通常 `TAG_xxx` 前缀；**`id` 可用中文**（如 `id = 苏联基地车`），游戏把 id 直接当显示文本，无需本地化——中文 id 别误判为 bug
- `x`/`y` 网格坐标；`relative_position_id = <某国策>` 相对定位
- 互斥 `mutually_exclusive = { focus = A focus = B }`（两个国策互相指）
- 连续国策（continuous focus）加 `continuous = yes`，位置用 `continuous_focus_position`
- 三选一互斥：三个国策各自 `mutually_exclusive = { focus = 另两个 }`
- `available = { ... }`（手动可点）与 `bypass = { hidden_trigger = { ... } }`（条件满足自动完成）配合：某角色靠 bypass 自动获得、另一角色靠 available 手动点。注意 `available = no` 不阻止 bypass。
- `bypass = { trigger }` 满足时国策自动完成**且照常执行 completion_reward**（等同手动完成），可用于"落地即自动吞并、跳过手动点首国策"：`bypass = { capital_scope = { OR = { is_core_of = TAN is_core_of = LUX ... } } }`。
- 判断"落地州属于哪个国家"用 `capital_scope = { is_core_of = TAG }`（核心绑定在州上，不依赖该国开局是否存在）。判**单地块国家（1 州）**：`history/states/*.txt` 每个州文件对同一 tag 会**同时写 `owner = TAG` 和 `add_core_of = TAG`（双写）**，数核心州要按州文件去重、不能直接数行数——阿尔巴尼亚 ALB 实为 3 州（44-Albania + 805-Northern Epirus + 934-Shkoder）、巴拿马 PAN 2 州（含 685 运河区）、也门 YEM 4 州、阿法尔 AFA 4 州。

## 9. 决议 common/decisions/*.txt + categories

**决议**（一个类别块内包多个决议）：

```text
BALTIC_entente = {                  # 决议类别
    formalize_the_entente = {       # 决议 ID
        allowed = {                 # 谁能执行（通常 OR tag）
            OR = { tag = LIT tag = LAT tag = EST }
        }
        icon = GFX_decision_xxx
        is_good = yes
        fire_only_once = yes

        available = { }             # 显示条件（满足才能点）
        visible = { }               # 是否显示在列表
        cost = 50                   # 政治点数
        days_remove = 70            # 多少天后自动移除

        complete_effect = {         # 执行效果
            if = { limit = { ... } ... }
        }
        cancel_effect = { }
        remove_effect = { }
        timeout_effect = { }

        ai_will_do = { factor = 200 }
    }
}
```

要点：
- 决议 ID 全局唯一，前缀 `TAG_`
- 地图决议加 `state_target = yes` + `target_trigger = { FROM = { ... } }`；`FROM`=目标省，`ROOT`=执行国
- `fire_only_once` / `is_good`（好坏决议，影响 AI 排序）
- 动态生成部队：`complete_effect` 里 `division_template = { ... }` + `create_unit = { division = "name = \"...\" division_template = \"...\"" }`
- 变量：`set_variable` / `add_to_variable` / `subtract_from_variable` / `check_variable = { var = X value = N compare = ... }`

**决议分类**（`common/decisions/categories/*.txt`，控制决议在哪个标签页显示）：

```text
propaganda_efforts = {
    icon = generic_propaganda
    visible = { }
}
MTG_naval_treaties = {
    picture = GFX_decision_cat_picture_naval_treaties
    allowed = { has_dlc = "Man the Guns" }
    visible = { ... }
    priority = 10
}
```

## 10. 事件 events/*.txt

```text
add_namespace = XXX_events

country_event = {
    id = XXX_events.1
    title = XXX_events.1.t
    desc = XXX_events.1.desc
    picture = GFX_report_event_generic

    is_triggered_only = yes      # 只能被其它效果触发（否则用 MTTH 随机触发）
    fire_only_once = yes
    hidden = no

    trigger = { ... }            # 触发条件（随机触发时配合 mean_time_to_happen）
    # mean_time_to_happen = { months = 120 }

    immediate = { ... }          # 事件弹出时立即执行（无选项）

    option = {
        name = XXX_events.1.a
        ai_chance = { base = 10 }
        add_political_power = 100
    }
}
```

要点：
- namespace 用 `add_namespace = XXX_events`，事件 ID 为 `XXX_events.N`
- 本地化 key：`XXX_events.N.t`（标题）/ `.desc`（描述）/ `.a` `.b`（选项）
- **选项 key 跳过 `.d`**（`.d`/`.desc` 是描述 key）；第 4 个选项用 `.e`（即 `.a .b .c .e`），不是 `.d`
- 触发方式二选一：`is_triggered_only = yes`（被动）vs `mean_time_to_happen = { days/months = N }` + `trigger`（随机）
- `fire_only_once = yes` 只触发一次
- 触发其它事件：`country_event = { id = XXX_events.2 days = 5 random_days = 3 }`；**不要 `days`/`random_days` = 立即触发**（点击选项后马上弹下一个事件）
- 开局立即触发：在 `common/on_actions/` 的 `on_startup` 里写 `every_country = { limit = { is_ai = no } country_event = { id = XXX.1 } }`（不加 `days`）
- 新闻事件用 `news_event = { ... }`（带 `major = yes` 等）

## 11. 科技 common/technologies/*.txt

```text
technologies = {
    @1918 = 0      # 年份宏，用于 y 坐标
    @1936 = 2
    @1938 = 4

    infantry_weapons = {
        enable_equipments = { infantry_equipment_0 }        # 解锁装备
        enable_equipment_modules = { tank_heavy_machine_gun }  # 解锁模块
        enable_subunits = { infantry }                      # 解锁兵种

        path = {                       # 后续科技（科技树连线）
            leads_to_tech = infantry_weapons1
            research_cost_coeff = 1
        }

        research_cost = 1.5
        start_year = 1918
        folder = { name = infantry_folder position = { x = 0 y = -1 } }

        categories = { infantry_weapons }

        ai_will_do = { factor = 1 }
    }
}
```

要点：
- 顶层 `technologies = { ... }`；`@年份` 是坐标宏（`position = { x = 0 y = @1936 }`）
- `enable_equipments` / `enable_equipment_modules` / `enable_subunits` 解锁内容
- `path = { leads_to_tech = xxx research_cost_coeff = N }` 定义科技树连线（前置关系由上游的 leads_to_tech 表达）
- `start_year`（最早可研究年份，早于会加成本）、`research_cost`（基础成本）
- **⚠️ 科技门控字段是 `allow` 不是 `available`**：technologies 没有 `available` 字段，写 `available = { 触发器 }` 会被 CWT 当修正块解析，报 CW267 "Expected a unit_stat value"（对块内任何 `key = value` 都报，与触发器写法无关）。可用触发器：`check_variable`/`has_country_flag` 等在 `allow` 内均正常。
- `folder = { name position = { x y } }` 定位到科技树文件夹；`allow = { }` 控制可否研究

## 12. 国家历史 history/countries/[TAG] - 名称.txt

```text
capital = 44                     # 首都省份 ID

OOB = "ALB_1936"                 # 或 set_oob = "XXX"（条件分支时）

set_technology = {               # 开局已研究科技
    infantry_weapons = 1
    tech_trucks = 1
}

recruit_character = ALB_king_zog  # 招募将领/顾问角色

set_politics = {                 # 政治体制
    ruling_party = neutrality
    last_election = "1933.3.5"
    election_frequency = 48
    elections_allowed = no
}

set_popularities = {             # 各意识形态支持率
    neutrality = 100
}

add_ideas = AFG_pashtunwali      # 开局拥有的国家精神/idea

set_convoys = 5                  # 运输船数量
```

要点：
- 文件名 `[TAG] - 名称.txt`，TAG 与 `common/countries` 定义一致
- `OOB` 指向 `history/units/[OOB].txt`；`set_oob` 用于 `if = { limit = { has_dlc = ... } ... }` 分支
- `set_variable = { name = value }` 设置开局变量（常配合动态 modifier）
- `add_ideas` 加国家精神；`set_technology` 加科技；`recruit_character` 招募角色
- 可释放国家模式（仿 vanilla HAW）：history 文件 `capital` 指向 core 州，但该州被别国 `owner` 拥有；事件里 `set_capital` 再覆盖

## 13. 脚本触发器 / 脚本效果

**脚本触发器**（`common/scripted_triggers/*.txt`）：

```text
example_trigger = {              # 定义（可用 ROOT/FROM/PREV/THIS 作用域占位符）
    tag = GER
    is_ai = no
}
```
使用：`trigger = { example_trigger = yes }`

要点：
- 命名通常 `Is_XXX` / `is_XXX`；用于复用复杂条件、地区分组（如 `Is_MOT`、`Is_LYY`）
- 内部作用域占位符：`ROOT` `FROM` `PREV` `THIS`
- 分组检查用 scripted triggers（如 `Is_MOT`、`Is_LYY`）而非硬编码国家 tag 列表

**脚本效果**（`common/scripted_effects/*.txt`）同理，定义效果块，用 `effect_name = yes` 调用。

## 14. 想法/国家精神 common/ideas/*.txt

```text
ideas = {
    country = {                   # 类型：国家精神
        AFG_mohammad_zahir_shah_ns = {
            allowed = { original_tag = AFG }      # 谁能获得
            picture = AFG_zahir_shah_idea
            removal_cost = -1                     # -1 = 不可移除
            modifier = {
                stability_factor = 0.1
            }
        }
    }
}
```

要点：
- 顶层 `ideas = { 类型 = { idea名 = { ... } } }`
- 类型：`country`（国家精神）、`political_advisor`（顾问）、`law`（法律）、`minister`、`designer`（设计局）等
- `modifier = { ... }` 数值效果；`removal_cost = -1` 不可移除
- `allowed = { }` 谁能获得、`allowed_civil_war = { }` 内战限制

## 15. 国家定义 common/countries/*.txt + country_tags

**country_tags**（`common/country_tags/00_countries.txt`）注册 tag → 文件：

```text
GER = "countries/Germany.txt"
ENG = "countries/United Kingdom.txt"
```

**countries**（`common/countries/[名称].txt`）：

```text
graphical_culture = middle_eastern_gfx
graphical_culture_2d = middle_eastern_2d

color = { 64 160 167 }
```

要点：
- `color = { R G B }`（0–255 整数，地图着色）
- `graphical_culture` / `graphical_culture_2d` 决定兵模/界面风格

## 16. 意识形态 common/ideologies/*.txt

```text
ideologies = {
    democratic = {
        types = { conservatism liberalism socialism populism }   # 子意识形态
        dynamic_faction_names = { "FACTION_NAME_DEMOCRATIC_1" "..." }
        color = { 0 0 255 }
        rules = {                     # 行为规则
            can_create_collaboration_government = no
            can_declare_war_on_same_ideology = no
            can_force_government = yes
            can_send_volunteers = no
            can_puppet = no
        }
        war_impact_on_world_tension = 0.25
        faction_impact_on_world_tension = 0.1
        modifiers = { ... }
    }
}
```

要点：
- 四大意识形态：`democratic`(民主) / `communism`(共产) / `fascism`(法西斯) / `neutrality`(中立)
- 子类型 `types = { }`（如 `socialism` `stalinism` `fascism_ideology` `despotism` 等）
- `rules` 控制能否宣战/傀儡/志愿军/保障等行为
- cosmetic tag 本地化：`set_cosmetic_tag = XXX` 后，用 `XXX`（及 `XXX_<ideology>`）作本地化 key 覆盖国名/党派显示

## 17. 角色 common/characters/*.txt

```text
characters = {
    ALB_king_zog = {
        name = ALB_king_zog
        portraits = {
            civilian = { large = GFX_portrait_King_Zog }
        }
        country_leader = {            # 国家领袖
            ideology = despotism
            traits = { skanderbeg_ii }
            expire = "1965.1.1.1"
            id = -1
        }
    }

    ALB_xhemal_aranitasi = {
        name = ALB_xhemal_aranitasi
        portraits = { army = { large = GFX_portrait_X large small = GFX_portrait_X_small } }
        field_marshal = {             # 元帅
            skill = 2
            attack_skill = 1
            defense_skill = 3
            planning_skill = 2
            logistics_skill = 1
            legacy_id = -1
        }
    }

    ALB_halil_nergutti = {
        advisor = {                   # 顾问
            slot = high_command
            idea_token = ALB_halil_nergutti
            ledger = navy
            allowed = { original_tag = ALB }
            traits = { navy_capital_ship_2 }
            cost = 100
            ai_will_do = { factor = 1.0 }
        }
        name = "Halil Nergutti"
        portraits = { army = { small = "GFX_idea_generic_navy_arab_1" } }
    }
}
```

要点：
- 顶层 `characters = { char_id = { ... } }`
- 角色类型（角色块键名）：`country_leader`(国家领袖) `field_marshal`(元帅) **`corps_commander`(将军)** `navy_leader`(海军将领) `advisor`(顾问) `scientist`(科学家)。⚠️ **没有 `general` 这个键**——"将军"的角色块键名是 `corps_commander`（本体 characters 里 785 处用 `corps_commander`、0 处用 `general`）
- 顾问 `slot`：`political_advisor`(政治顾问) `high_command`(最高统帅部) `army_chief`(陆军部长) `navy_chief`(海军部长) `air_chief`(空军部长) `theorist`(理论家)
- 将领技能：`skill`(总体) + `attack_skill` `defense_skill` `planning_skill` `logistics_skill`
- 领袖 `ideology` 对应子意识形态，`traits` 领袖特质；`expire` 死亡/退役日期
- **招募/任命**：`recruit_character = char_id` **只在 `history/countries` 有效**；effect（scripted_effect/event/decision）里用 `promote_character = { character = char_id ideology = xxx }`，前提是 character 已 recruit 进池子。`recruit_character` 写进 effect 不生效。
- **老式 `create_country_leader` vs character 系统**：`create_country_leader = { name = "本地化key" desc = "..." picture = "spriteType名" ideology = ... }` 内联创建，`name` 带引号、不依赖 character 定义；现代推荐 character 系统（`name = char_name` 无引号引用本地化 key）。
- **`large` 有两种写法，`small` 需注册**：`large` 既可写 **png 路径直引**（`large = "gfx/leaders/XIA/Portrait_X.png"`，引擎自动处理，**无需注册**，本项目 65 张将领头像全用这种），也可写 spriteType 名；`small` 通常写 spriteType 名，需先在 `interface/*.gfx` 注册 `spriteType = { name = "GFX_X_minister" texturefile = "gfx/interface/ministers/<TAG>/X.png" }`。
- **character 系统 leader 无 desc**：desc 只存在于老式 `create_country_leader`；character 定义里没有 desc 字段，领导人描述文本不会显示。

- **`portraits` 分组要和角色类型配对**：将军/元帅 → `portraits = { army = { large = ... } }`；国家领袖/顾问 → `portraits = { civilian = { large/small = ... } }`。**纯将领误写 `civilian` 会导致将领头像不显示**。同一角色可同时给 `army` 和 `civilian` 两套（既当将军又当顾问时）。
- **一个角色可挂多个角色块**：`corps_commander` + `advisor` 可共存；也允许两个 `country_leader` 块（**`ideology` 不同**，代表一人对应多个意识形态——这是合法的，不是重复键 bug）。
- **顾问槽位与中文名（本项目约定，`head_of_intel` 容易看错）**：`head_of_government`=总理 `foreign_minister`=外长 `economy_minister`=财长 `security_minister`=内长 **`head_of_intel`=军长**。其余：`chief_of_staff`/`chief_of_army`/`chief_of_navy`/`chief_of_airforce`/`high_command`/`political_advisor`/`theorist`。**`head_of_intel` 配"军长"不是 bug**——先查该 mod 自己的本地化怎么译，再判断。
- **顾问可用的前提是角色已入池**：`advisor = { slot = ... }` 只是定义职务，**角色必须先在 `history/countries/<TAG>.txt` 里 `recruit_character`**，或以 `activate_advisor = <idea_token>` 激活，否则不会出现在顾问槽里。项目的常见模式：开局内阁在 history 里 `recruit_character` + `activate_advisor`；路线切换的内阁在国策/事件里 `activate_advisor`。
- **特质定义的两个目录**：指挥官特质（`type = land`、`trait_type = personality_trait`）→ `common/unit_leader/*.txt` 的 `leader_traits = {}`；顾问/领袖特质 → `common/country_leader/*.txt` 的 `leader_traits = {}`。**放错目录不报错但不生效**。
- **多行文本的注释行会漏过正则**：`(?<!#)\s*recruit_character` 的 lookbehind 只看匹配起点前一字符，而 `\s*` 可零宽匹配，所以 `# recruit_character = X` 仍会命中——按行 `strip()` 后判断 `startswith('#')` 才可靠。

## 18. 地区与战略区/补给区

**地区 state**（`history/states/[id]-名称.txt`）：

```text
state = {
    id = 1
    name = "STATE_1"
    manpower = 322900
    state_category = town            # 地区类型

    history = {
        owner = FRA
        victory_points = { 3838 1 }  # 省份ID 胜利点值
        buildings = {                # 建筑等级
            infrastructure = 2
            industrial_complex = 1
            air_base = 1
            3838 = { naval_base = 3 }
        }
        add_core_of = COR
        add_core_of = FRA
    }

    provinces = { 3838 9851 11804 }
    local_supplies = 0.0
}
```

要点：
- `state_category`：`wasteland`(荒芜) / `enclave` / `town` / `city` / `large_city` / `metropolis` / `megalopolis`（决定建筑槽数）
- `history.owner` 开局拥有国；`add_core_of` 核心
- `buildings`：`infrastructure`(基建) `industrial_complex`(工厂) `air_base`(机场) `naval_base`(海军基地) `anti_air_building`(防空)

**战略区**（`map/strategicregions/[id]-名称.txt`）：

```text
strategic_region = {
    id = 1
    name = "STRATEGICREGION_1"
    provinces = { 221 271 296 }
    weather = {
        period = {                     # 时段（between 0.0-1.0 为全年比例）
            between = { 0.0 30.0 }
            temperature = { -6.0 12.0 }
            no_phenomenon = 0.500
            rain_light = 1.000
            rain_heavy = 0.150
            snow = 0.200
            mud = 0.300
        }
    }
}
```

**补给区**（`map/supplyareas/[id]-SupplyArea.txt`）：

```text
supply_area = {
    id = 1
    name = "SUPPLYAREA_1"
    value = 12                # 补给量
    states = { 5 85 763 807 }
}
```

## 19. OOB 海军舰队与空军联队

**海军舰队**（history/units 里，与陆军师并列）：

```text
units = {
    fleet = {
        name = "Comando Navale"
        naval_base = 11837            # 基地省份
        task_force = {
            name = "I Squadra Navale"
            location = 11837
            ship = {
                name = "RN Caio Duilio"
                pride_of_the_fleet = yes
                definition = battleship
                start_experience_factor = 0.25
                equipment = {
                    ship_hull_heavy_1 = { amount = 1 owner = ITA version_name = "Andrea Doria Class" }
                }
            }
        }
    }
}
```

要点：
- `fleet`(舰队) → `task_force`(特遣队) → `ship`(单舰)
- `definition` = 兵种名（battleship/destroyer/submarine 等 sub_units）；`equipment` 指定舰体型号 + `version_name` 级名
- `pride_of_the_fleet = yes` 舰队旗舰

**空军联队**（history/units 里）：

```text
air_wings = {
    7 = {                            # 省份 ID
        small_plane_cas_airframe_0 = {
            owner = "HOL"
            amount = 12
            version_name = "Fokker C.X"
        }
    }
}
```

要点：
- 按省份 `省份ID = { 机型 = { owner amount version_name } }` 分配飞机
- 机型是装备 archetype：`small_plane_airframe_0`(战斗机) `small_plane_cas_airframe_0`(对地攻击机) `medium_plane_airframe_0`(中型机) 等

## 20. 关键文件路径结构

| 用途 | 路径 |
|------|------|
| 单位（兵种）定义 | `common/units/*.txt` |
| 装备定义 | `common/units/equipment/*.txt` |
| 装备模块 | `common/units/equipment/modules/*.txt` |
| 单位 tag 分类 | `common/unit_tags/*.txt` |
| 国家定义 | `common/countries/*.txt` |
| 国家 tag 注册 | `common/country_tags/*.txt` |
| 意识形态 | `common/ideologies/*.txt` |
| 角色（将领/顾问） | `common/characters/*.txt` |
| 界面/图标注册 | `interface/*.gfx` |
| 特殊单位注册 | `interface/DOT_special_units.gfx` |
| 师编制模板 / OOB | `history/units/[TAG]_1936.txt` |
| 国家历史 | `history/countries/*.txt` |
| 地区 | `history/states/*.txt` |
| 战略区 | `map/strategicregions/*.txt` |
| 补给区 | `map/supplyareas/*.txt` |
| 想法/国家精神 | `common/ideas/*.txt` |
| 决议 | `common/decisions/*.txt` |
| 决议分类 | `common/decisions/categories/*.txt` |
| 动态修饰符 | `common/dynamic_modifiers/*.txt` |
| 事件 | `events/*.txt` |
| 国策 | `common/national_focus/` |
| 科技 | `common/technologies/*.txt` |
| 脚本触发器 | `common/scripted_triggers/*.txt` |
| 脚本效果 | `common/scripted_effects/*.txt` |
| 本地化(简中) | `localisation/simp_chinese/*.yml` |
| 建筑定义 | `common/buildings/*.txt` |
| 实体定义 | `gfx/entities/*.asset` |
| mesh 注册 | `gfx/entities/*.gfx` |

## 21. 动态修饰符 common/dynamic_modifiers/*.txt

```text
barracks_1 = {
    icon = GFX_idea_unknown        # 可选
    enable = { always = yes }      # 可选，不写则加上即生效
    remove_trigger = { always = no }  # 可选，不写则永不自动移除
    training_time_factor = -0.10   # 数值可写死或引用变量 var_xxx
    experience_gain_army_factor = 0.20
    army_leader_start_level = 1
}
```

- 加：`add_dynamic_modifier = { modifier = barracks_1 }`（**不写 `days` = 永久**，直到 `remove_dynamic_modifier` 移除；scope 默认当前国家）
- 移除：`remove_dynamic_modifier = { modifier = barracks_1 }`
- 判断：`has_dynamic_modifier = { modifier = barracks_1 }`
- 名称本地化 key = modifier id（如 `barracks_1:0 "兵营：一级"`）；效果里的 stat key 由游戏自动翻译
- **「等级」无原生字段**：用 N 个独立 modifier 替换实现。升级决议 `complete_effect` 里 `remove_dynamic_modifier = { modifier = lv1 }` + `add_dynamic_modifier = { modifier = lv2 }`；决议用 `fire_only_once = yes` + `available = { has_dynamic_modifier = { modifier = lv1 } }` 门控，确保只显示下一级
