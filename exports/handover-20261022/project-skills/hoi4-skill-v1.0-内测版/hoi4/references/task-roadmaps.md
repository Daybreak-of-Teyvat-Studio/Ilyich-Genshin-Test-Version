# 任务路线图：常见任务的文件组成与顺序

**读这份的场景**：用户说要"做一个新国家 / 新国策树 / 新单位 / 新决议 / 新事件 / 新角色 / 新法案 / 新军工组织 / 新界面 / 本地化 / 新地标"之类，需要告诉用户**这项任务由哪些部分组成、按什么顺序做、互相怎么联动**，然后再动手。

通用原则：
- 每个路线图 = 文件清单 + 顺序 + 联动点 + 验收。具体语法模板查 `paradox-syntax.md` 对应章节，不在此重复。
- **本地化与 interface 素材不是独立任务**——它们内嵌在下面每个任务的清单里；通用规范汇总在文末「横切要素」。
- 告诉用户清单时**按依赖顺序**排列，标注哪些是"骨架（不做就跑不起来）"、哪些是"锦上添花（可后补）"。
- 同一个 mod 内**先看已有同类文件**，照抄结构（如已有国策树文件就抄它的块结构），不要凭通用写法凭空造。

## 一、新国策树（national focus tree）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | 树本体 | `common/national_focus/<名字>.txt`：`focus_tree = { id = ... country = { factor = ... } focus = { ... } }`，每个 focus 含 `id` / `icon` / `x`+`y`（网格定位）/ `cost` / `prerequisites`（前置连线）/ `mutually_exclusive`（互斥）/ `available` / `completion_reward` / `ai_will_do` | 骨架 |
| 2 | 图标注册 | `interface/*.gfx` 加 `spriteType { name = "GFX_goal_<icon>" textureFile = "gfx/interface/goals/<icon>.dds" }` + 图标文件 `gfx/interface/goals/<icon>.dds`（96×85，DXT 格式） | 骨架（缺了显示紫块，不崩） |
| 3 | 本地化 | `localisation/<语言>/<...>_l_<语言>.yml`：每个 focus 的 `<focus_id>:0 "名字"` 和 `<focus_id>_desc:0 "描述"`；其他语言可选 | 骨架（缺了显示原始 key） |
| 4 | 树分配给国家 | 任一：`history/countries/<TAG> - *.txt` 里 `load_focus_tree = <树id>`；或书签/事件里加载。另检查 `country = { factor }` 让该国默认选中 | 骨架 |
| 5 | 奖励依赖项 | completion_reward 里用到的自定义 idea（`common/ideas/`）、决议、事件、scripted_effect 等，各自按对应路线图补 | 视内容 |
| 6 | 联动检查 | focus 里引用的 `has_focus`、`complete_national_focus`、其他文件对该 focus id 的引用；新增 focus id 不要与全局重复（id 冲突 → `Failed to create id` 崩溃） | 验收 |

**验收**：`logs/error.log` 无 `Unable to find focus tree`、无 `Unknown focus <id>`；图标加载无 `Couldn't find texture`；本地化无缺 key（游戏内不显示原始 key）；进游戏：树显示、前置连线正确、互斥生效、点完奖励生效。

**提醒用户**：focus 树的 x/y 是树形图网格坐标，先画草图（哪条线、几个分支、互斥关系）再写文件，返工率最低。

## 二、新国家（新 tag）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | tag 注册 | `common/country_tags/*.txt`：`<TAG> = "countries/<TAG>.txt"`（3 个大写字母，全局唯一，不用已占用的） | 骨架 |
| 2 | 国家颜色/外观 | `common/countries/<TAG>.txt`：`color = rgb {...}`、`color_ui` | 骨架 |
| 3 | 国家历史 | `history/countries/<TAG> - 名字.txt`：`capital = <州id>`（**必须属于该国**）、`set_convoys`、oob、`add_ideas`、领导人等 | 骨架 |
| 4 | 领土 | `history/states/*.txt`：把若干州的 `owner` / `add_core_of` 给它（动省界/州归属则走 `map-data.md` 的完整流程，同步 `map/buildings.txt`） | 骨架 |
| 5 | 国旗 | `gfx/flags/<TAG>.tga` + `flags/medium/`、`flags/small/` 同名（不同意识形态变体按 `flags/<ideology>/` 放） | 骨架（缺了不崩，显示黑旗） |
| 6 | 本地化 | `common/countries` 对应语言 yml：`<TAG>` / `<TAG>_DEF` / `<TAG>_ADJ`；政党名 `common/parties` | 骨架 |
| 7 | 军队 | `history/units/<TAG>_1936.txt`（师编制 OOB） | 可后补 |
| 8 | 领导人/将领 | `common/characters/*.txt` + country history 里 `set_country_leader`（见 §五 角色） | 可后补 |
| 9 | 开局可见性 | 书签/事件/设定里把该国列为可选 | 视需求 |
| 10 | 脚本触发器 | 若项目有地区分组触发器（如 `Is_XXX`），把新 tag 加进对应分组，否则 AI/事件判定会漏它 | 视项目 |

**验收**：`error.log` 无 `Unknown country tag <TAG>`、无 `no provinces in state`；首都州归属正确；进游戏：地图颜色、国名、国旗、首都正确。

## 三、新单位（兵种）及图标

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | 单位定义 | `common/units/<分类>_Units.txt`：`<单位名> = { ... }`（数值、分类、grade） | 骨架 |
| 2 | 单位分类 | `common/unit_tags/<对应>_units_categories.txt` | 骨架 |
| 3 | 图标 DDS | 三件套（大图标 152×42、小地图 60×12、texticon），NVTT 裸 RGBA，`noOfFrames = 2`（左帧本单位、右帧基线步兵背景）——规格与制作管线见 `icons-dds.md` | 骨架 |
| 4 | GFX 注册 | `interface/*.gfx` 三个 spriteType：`GFX_unit_<名>_icon_medium` / `_medium_white` / `_icon_small` | 骨架 |
| 5 | 编制模板 | `history/units/<TAG>_1936.txt`：师模板里 `regiment = { regimenttype = <单位名> ... }` | 可后补 |
| 6 | 本地化 | 单位名/描述 key | 可后补 |
| 7 | 特殊单位注册 | 若是特殊单位，项目里的特殊单位注册 .gfx | 视项目 |

**验收**：`error.log` 无 `Unknown regiment <名>`、无图标纹理缺失；进游戏编制界面能看到该单位、图标显示正常。

## 四、新决议（decisions）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | 决议分类 | `common/decisions/categories/*.txt`：`<分类> = { icon = ... picture = ... }`（可复用已有分类，复用则跳过） | 骨架（新建分类时） |
| 2 | 决议本体 | `common/decisions/<名>.txt`：`<分类> = { <决议id> = { icon / allowed / visible / available / fire_only_once / cost / days_remove / removal_cost / timeout_effect / complete_effect / ai_will_do } }`；目标型决议（对州/国）加 `targeted_modifier` 或 `targets`、`target_trigger` | 骨架 |
| 3 | 图标 | `gfx/interface/decisions/<icon>.dds` + 在决议块用 `icon = <icon>` 引用 | 可后补（缺了灰图标） |
| 4 | 本地化 | `<决议id>` / `<决议id>_desc`；目标型决议可用动态 key | 骨架 |
| 5 | 联动 | effect 里引用的 idea/变量/事件先存在；`fire_only_once` 与 `timeout_effect` 的清理逻辑成对 | 验收 |

**验收**：`error.log` 无 `Unknown decision category`、无决议语法错误；进游戏决议面板出现、触发条件生效。

## 五、新事件（events）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | 事件本体 | `events/<名>.txt`：命名空间 `namespace = { xxx }` + `country_event = { id = xxx.1 ... }` 或 `news_event` / `unit_event`；块内 `title` / `desc` / `picture` / `trigger` / `mean_time_to_happen` 或 `immediate` / `option`（至少一个，含 `name` + `effect`） | 骨架 |
| 2 | 事件图片 | `gfx/event_pictures/<picture>.dds`；news_event 用 `news_event_pictures` | 可后补（缺了灰图） |
| 3 | 本地化 | `<ns>.<n>.t` / `.d` / `.a` / `.b` … 每个 option 一条；`[GetXXX]`、`[ROOT.GetName]` 等变量可内嵌 | 骨架 |
| 4 | 触发来源 | on_actions（`common/on_actions/*.txt`）挂事件，或决议/国策/焦点里 `country_event = { id = ... }` | 视设计 |
| 5 | 联动 | 事件 id 全局唯一（重复 → `Failed to create id`）；option effect 引用的对象先存在；新闻事件的 `major = yes` 决定是否全球播报 | 验收 |

**验收**：`error.log` 无事件语法错误、无 `Unknown event target`；实测触发链路。

## 六、新角色（领导人/将领/顾问，characters）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | 角色定义 | `common/characters/<名>.txt`：`characters = { <角色id> = { name / portraits / country_leader { ideology / traits / expiring } / advisor { slot = ... } / unit_leader {...} } }`；portraits 引用 `gfx/leaders/<TAG>/<图>.dds` | 骨架 |
| 2 | 立像/头像 | `gfx/leaders/<TAG>/` 下大像（portraits）与小型图；.dds 格式（DXT3/5；**格式不对报 `forbidden compression, have you tried DXT3?`**） | 骨架 |
| 3 | 上任 | `history/countries/<TAG> - *.txt` 里 `set_country_leader = <角色id>` 或 recruit_character；顾问在 country history `add_advisor_role` 或 ideas | 骨架 |
| 4 | 本地化 | 角色名/描述（角色名多在 characters 里直接写中文，或本地化 key） | 骨架 |
| 5 | 联动 | `add_country_leader_role` 引用的 ideology 必须已定义（**未定义报 `Invalid ideology`**）；traits 在 `common/unit_leader` / `common/traits` 里存在 | 验收 |

**验收**：`error.log` 无 `Invalid ideology`、无 `Large portrait path ... has unexpected format`；进游戏领导人显示、 traits 生效。

## 七、新法案（laws）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | 法案分类 | `common/laws/*.txt`：`<分类> = { <法案> = { cost / available / removable / modifier / effect / ai_will_do } }`，或复用现有分类在现有法案文件里加 | 骨架 |
| 2 | 修改器 | 法案的 `modifier = {...}` 用已有 stat key（查 `stat-keys.md`）；自定义 modifier 需先在 `common/modifiers` 定义 | 骨架 |
| 3 | 本地化 | `<法案id>` / `_desc` | 骨架 |
| 4 | 图标 | 复用已有法案图标或新加 goals 素材 | 可后补 |
| 5 | 联动 | `allow` 里的触发器（scripted_triggers 可复用）；politics power 消耗 `cost`；AI 权重 `ai_will_do` | 验收 |

**验收**：`error.log` 无 `Unknown law` / `Invalid modifier`；进游戏政治界面法案可选、生效、可撤销。

## 八、新军工组织（MIO，military industrial organization）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | 组织定义 | `common/military_industrial_organization/organizations/<TAG>_organization.txt`：`<组织id> = { allowed = {...} visible / available / icon / initial_stats / equipment / traits = { ... } }`；顶栏 `resources / policy` 等按版本语法 | 骨架 |
| 2 | traits 树 | 组织内 `traits = { <trait> = { ... parent = ... } }`，父节点必须存在（**缺失报 `trait xxx does not exist`**，真实日志形态：`in MIO <组织>: trait ... does not exist`） | 骨架 |
| 3 | 图标 | 组织图标与 trait 图标按版本放 `gfx/interface/mio/`（或 flags/goals），在块内引用 | 可后补 |
| 4 | 本地化 | 组织名 / trait 名与描述 | 骨架 |
| 5 | 挂接 | 国家在 `ideas` 或 organizations 的 `allowed` 里限定国家；装备关联 `equipment = { ... }` | 骨架 |

**验收**：`error.log` 无 `industrial_org_template.cpp` 报错（trait 不存在/引用缺失）；进游戏军工组织面板出现、trait 树可点。

## 九、界面 UI / GUI（窗口布局）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | 窗口布局 | `interface/<名>.gui`：`guiTypes = { containerWindowType = { name = "<窗口名>" size / position / orientation / iconTypes / buttonTypes / textBoxTypes / instantTextBoxType ... } }`；**原版界面要覆盖时，文件名与窗口名必须与原版一致**（整体替换） | 骨架 |
| 2 | 素材注册 | `interface/<名>.gfx`：`spriteType = { name = "GFX_xxx" textureFile = "gfx/interface/xxx.dds" }`；九宫格用 `corneredTileSpriteType`（noOfFrames / borderSize） | 骨架 |
| 3 | 素材文件 | `gfx/interface/` 下 .dds（DXT）；**TGA 不要带颜色表**（`Color Maps are not currently supported in TGA images`） | 骨架 |
| 4 | 逻辑挂接 | 按钮点击走 `common/scripted_guis/*.txt`（scripted_gui 绑定窗口名与效果）；纯展示窗口不需要 | 视设计 |
| 5 | 字体/文本 | 窗口内 textBox 引用本地化 key；中文字体注意已有字体定义 | 视设计 |

**验收**：`error.log` 无 `Failed to create gui object. Could not find sprite type [GFX_xxx]`、无 `Could not find "<节点>" in window <窗口>`（这两条是 GUI 缺素材/缺节点的真实报错形态）；进游戏界面显示、按钮可点、不遮挡原版元素。

**提醒用户**：改 GUI 前**必须备份原 .gui**；窗口名/节点名被别处引用（脚本、define），改名前后全局搜索。

## 横切要素：本地化与 interface 素材（内嵌在每个任务里，不独立立项）

**每个任务的路线图已包含它自己的本地化与图标/素材步骤**（如国策树的第 2/3 步、国家的第 5/6 步）。这里只汇总通用规范与速查，供任何任务引用：

**本地化通用规范**：
- 文件 `localisation/<语言>/<名>_l_<语言>.yml`（语言目录：`simp_chinese` / `english` / `japanese` / `russian` / `french`…）；首行 `l_<语言>:`
- 条目 `KEY:0 "文本"`（版本号可省略为 `KEY: "文本"`，**同一 mod 内风格统一**）；**必须 UTF-8 with BOM**
- 嵌入语法：颜色 `§R红§!`、变量 `[ROOT.GetName]`、`[GetXXX]`（配合 scripted_localisation）、换行 `\n`
- 特殊字符：`!` 在特定位置报 `Illegal break character (utf32=33)`；别用未配对的 `$`
- 覆盖原版：同名同 key 即覆盖；**文件名不要与原版相同**（避免整文件替换）

**interface 素材注册速查**：

| 需求 | 放哪 | 注册 |
|---|---|---|
| 国策图标 | `gfx/interface/goals/` | `GFX_goal_<名>` |
| idea 图标 | `gfx/interface/ideas/` | `GFX_idea_<名>`（或 idea 块内 `icon = GFX_xxx`） |
| 决议图标 | `gfx/interface/decisions/` | 决议块 `icon = <名>` |
| 事件图片 | `gfx/event_pictures/` | 事件块 `picture = <名>` |
| 领袖立绘 | `gfx/leaders/<TAG>/` | characters 里 portraits |
| 国旗 | `gfx/flags/` | 按文件名自动（`<TAG>.tga`） |
| 单位图标三件套 | `gfx/interface/counters/...` + `gfx/texticons/` | 见 `icons-dds.md` |
| 通用窗口素材 | `gfx/interface/` | 自定义 `GFX_xxx` |

**通用验收**：`error.log` 无 `Couldn't find texture file` / `Failed to create gui object`；本地化不显示原始 key；DDS 压缩格式正确（人物立绘 DXT3/5，`forbidden compression` 报错 = 格式不对）。

## 十、新学说（grand/sub doctrine，"不妥协"DLC 系统）

**前置知识**：学说体系分四层，全部在 `common/doctrines/`：`folders/`（大类 land/air/sea/special_forces）→ `grand_doctrines/`（大学说，互斥根）→ `tracks/`（轨道，每轨道一个子学说槽 + 里程碑）→ `subdoctrines/`（子学说 + rewards 掌握度奖励）。**给已有轨道挂新子学说只需第 4 步**；新建轨道/大学说才动前三层。

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | 大学说 | `grand_doctrines/<域>_grand_doctrines.txt`（复用已有则跳过）：`folder` / `name` / `icon` / `xp_cost` / `ai_will_do` / **`tracks = {...}`（本学说含哪些轨道）** / 激活效果直接写顶层（`planning_speed`、`enable_tactic`、category 块）/ `milestones`（轨道里程碑）。effect/triggers 名字见 `common/doctrines/_documentation.md` | 视需求 |
| 2 | 轨道 | `tracks/<域>_doctrine_tracks.txt`（复用已有轨道则跳过；轨道定义里程碑与完成奖励） | 视需求 |
| 3 | 子学说本体 | `subdoctrines/<域>/<track>_subdoctrines.txt`：`<id> = { track / name / description / icon / xp_cost / xp_type / visible{has_dlc="No Compromise, No Surrender"} / available / ai_will_do{base+modifier} / effect{...} / rewards{...} }` | 骨架 |
| 4 | mastery 声明 | 子学说块内可选 `mastery = { categories = {...} }`——声明吸收哪些单位类别的掌握度 | 可选 |
| 5 | 图标 | `.gfx` 注册 `GFX_doctrine_<名>_medium` + 贴图 | 骨架 |
| 6 | 本地化 | `name`/`description` 的 key + **rewards 每个条目名也是本地化 key** | 骨架 |
| 7 | 联动 | `effect` 里 `add_tech_bonus` 的 `category` 必须是 `common/unit_tags/00_categories.txt` 里的合法 key（**写错报 `Unknown technology category`**）；AI 换学说倾向查 `common/ai_strategy/doctrines.txt` | 验收 |

**语法勘误（对照原版 `infantry_subdoctrines.txt` 实测）**：

> 附录两份：**grand-doctrine-tutorial-主学说教程.txt**（主学说/轨道/里程碑完整教程，猫妖团队）与 **sub-doctrine-tutorial-子学说教程.md**（子学说教程修正版）。主学说 milestones 的变量标记（NOT has_variable → set 1 / else add +1）照抄原版固定写法，变量名换成自己的前缀且不与现有变量冲突。

- **`add_tech_bonus` 这类普通 effect 必须包在 `effect = { ... }` 里**——教程通篇没提这个包裹层。但注意区分：`category_xxx = {...}` 师修饰符块、国家级修正（如 `unit_cavalry_design_cost_factor`）、`enable_tactic = <战术>` 在原版就是**直接写顶层**的，教程这部分没错。
- **mastery 机制**：精通度随时间/行动积累（`add_daily_mastery` 等），rewards 各条目按声明顺序解锁；**每层写相同值（增量）与写递增累计值（100/200/…/500）等价**；数值自定义（原版常见每层 50）；字段可省略（原版 mobile_infantry，分布规则待确认）。（初版曾误判教程此处有错，经群友反馈与原版 grand_doctrines 复核后更正。）
- 师修饰符写在 `category_xxx = { soft_attack = ... }` 块（key 白名单见 `common/unit_tags/00_categories.txt`，**该文件只作参考，不要复制进 mod**）；国家级修正（如 `unit_cavalry_design_cost_factor`）写子学说块顶层。
- rewards 条目名 = 本地化 key = 界面上该层的名字。
- **教程缺失**：① 子学说可选 `mastery = { categories = {...} }` 声明吸收哪些类别的掌握度；② 学说体系是四层——`folders/`（大类）→ `grand_doctrines/`（大学说）→ `tracks/`（轨道+里程碑）→ `subdoctrines/`，教程只讲了子学说一层。

**验收**：`error.log` 无 doctrine 相关报错、无 `Unknown technology category`；进游戏学说界面：子学说可见、XP 消耗正确、解锁后修饰符与各层奖励生效、掌握度正常增长。

## 十一、权力平衡（bop, balance of power）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | BOP 定义 | `common/bop/<名>.txt`：`bop = { id = <名> icon = <名> left = { side = {...} range = {...} modifiers } right = {...} neutral = {...} }`；两侧 `side` 定义名字与效果，`range` 定义区间修饰 | 骨架 |
| 2 | 图标 | `gfx/interface/bop/`（左右侧图标、背景） | 骨架 |
| 3 | 本地化 | 两侧名/描述、区间名 | 骨架 |
| 4 | 挂到国家 | 国策/事件/决议里 `add_power_balance = { id = <名> left = yes/right = yes }`；移动用 `add_power_balance_value = { id = <名> value = 0.05 }` | 骨架 |
| 5 | 联动 | 触发器 `has_power_balance` / `power_balance_range`；修饰随区间自动启停 | 验收 |

**验收**：`error.log` 无 bop 相关报错；进游戏权力平衡条显示、图标与两侧效果正确。

## 十二、新特质（trait）（unit_leader/traits）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | trait 定义 | `common/unit_leader/*.txt`：`trait = { type = { land / air / naval / country } trait_type = <basic/personality/...> modifier = {...} attack_skill / defense_skill / level_gain_factor ... }`；**领导人特质也在 unit_leader 文件（type 含 country）** | 骨架 |
| 2 | 挂接 | 将领/领导人在 `common/characters` 的 `unit_leader` / `country_leader` 块里 `traits = { <trait> }`；也可事件/决议 `add_unit_leader_trait` | 骨架 |
| 3 | 本地化 | `<trait>` / `<trait>_desc` | 骨架 |
| 4 | 图标 | 将领技能图标按原版 `gfx/interface/` 体系（复用原版槽位可免） | 可后补 |
| 5 | 联动 | modifier 的 stat key 查 `stat-keys.md`；MIO 的 trait 是另一套（写在组织文件里，见 §八） | 验收 |

**验收**：`error.log` 无 `Unknown trait`、无 modifier 报错；进游戏角色面板显示特质与数值。

## 十三、新编制（division template）（history/units templates）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | 模板定义 | `history/units/<TAG>_1936.txt`：`division_template = { name = <本地化key> regiments = { x=0 y=0 <营type> ... }（(x,y) 网格，最多 5 列×5 行） support = { ... } is_locked = yes（锁定防玩家改） }` | 骨架 |
| 2 | 开局部队 | 同文件：`unit = { location = <省id> division = "<模板名>" = { leadership_xp / ... } }`（location 省必须陆地且属于该国） | 骨架 |
| 3 | 联动 | `regimenttype`/支援营必须是 `common/units` 已注册单位；模板名是本地化 key（或直接中文）；海军/空军编制另走 OOB 舰船/机队块 | 验收 |
| 4 | 经验/优先级 | `division = { experience = 0.2 }`、模板 `force_allow_reinforcing` 等可选 | 可后补 |

**验收**：`error.log` 无 `Unknown regiment` / `no unit by that name`；进游戏开局部队位置、编制、经验正确。

## 十四、新建筑（building）（buildings）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1 | 建筑定义 | `common/buildings/<名>.txt`：`<名> = { texturefile / max_level / spawn_point / provinces 或 state（省级或州级建筑）/ show_on_map / modifier = {...} / enabled / available / on_completion ... }` | 骨架 |
| 2 | 地图实体（可选） | 3D 模型五层流水线（building 定义 → entity → gfx 注册 → .mesh + 贴图 → 图标）见 `landmarks-3d.md`；**定义了实体才显示模型，否则报 `Building xxx doesn't have an entity`** | 视需求 |
| 3 | 放置 | 州级：`history/states/*.txt` 的 `buildings = { <名> = N }`；省级：`map/buildings.txt`（**动它必须走 `map-data.md` 同步流程**）；共享建筑 `common/buildings/shared_buildings.txt` 视情况 | 视需求 |
| 4 | 本地化 + 图标 | `<名>` / `<名>_desc`；建造界面图标 | 骨架 |
| 5 | 联动 | `modifier` 的 stat key 查 `stat-keys.md`；`available` 触发器；建筑上限受 `buildings_max_level_factor` 影响 | 验收 |

**验收**：`error.log` 无 `Building xxx doesn't have an entity`（要模型却没 entity 的真实报错）、无 modifier 报错；进游戏建造界面可建、建成生效、地图模型/图标正常。

## 十五、新民族精神 / 动态修正（idea / dynamic_modifier）

| # | 部分 | 文件 | 性质 |
|---|---|---|---|
| 1a | idea 定义 | `common/ideas/*.txt`：在对应分类块（如 `air_tech = {...}` 或自定义分类）里 `<idea名> = { picture = GFX_idea_xxx / modifier = {...} / allowed / available / removal_cost / cancel_if_invalid }`；隐藏类放 `hidden_ideas` | 骨架 |
| 1b | dynamic_modifier 定义 | `common/dynamic_modifiers/*.txt`：`<名> = { icon = GFX_xxx modifier = {...} }`——modifier 里可引用**变量**（随 update 动态变化，这是它与 idea 的本质区别） | 骨架 |
| 2 | 挂接 | idea：country history `add_ideas = { <idea> }` 或国策/事件 `add_ideas`；dynamic_modifier：`add_dynamic_modifier = { modifier = <名> }`，数值变化用 `update_dynamic_modifier = yes` | 骨架 |
| 3 | 图片/图标 | idea：`gfx/interface/ideas/<picture>.dds`（`picture` 引用**不带 GFX 前缀的名字**或完整 GFX，按原版习惯）；dynamic_modifier：`GFX_idea_xxx` | 可后补 |
| 4 | 本地化 | idea：`<idea名>` / `<idea名>_desc`；dynamic_modifier：`<名>` / `<名>_desc`（动态变量用 `$变量$` 占位） | 骨架 |
| 5 | 联动 | 选择原则：**静态数值用 idea；数值会随事件/时间/变量变化的用 dynamic_modifier**；两者 modifier 的 stat key 查 `stat-keys.md` | 验收 |

**验收**：`error.log` 无 `Unknown idea`、无 `Invalid modifier`；进游戏精神/修正面板显示正确、数值生效、动态修正的变量随触发更新。

## 十六、新战术卡（tactic）（combat_tactics）

**文件只有一个**：`common/combat_tactics.txt`。

| # | 部分 | 内容 | 性质 |
|---|---|---|---|
| 1 | 拷贝原文件 | **原版全部战术都在这一个文件里，mod 加战术必须整文件拷入再追加**——同名覆盖是整文件替换，直接新建会丢掉原版全部战术 | 骨架（最关键一步） |
| 2 | 战术块 | `tactic_<名> = { is_attacker = yes/no / trigger = {...} / active = yes / base = { factor = 4 modifier = {...} } / picture = <名> / countered_by = tactic_<名> / attacker = N / defender = N / attacker_org_damage_modifier 等修正 }` | 骨架 |
| 3 | 命名铁律 | **战术名必须以 `tactic_` 开头**（原版文件头注释明示），否则学说/科技的 `enable_tactic` 引用不到 | 骨架 |
| 4 | 触发条件 | `trigger` 作用域含国家与战斗方：常用 `is_attacker`、`phase = no`、`skill_advantage > 0`、`combat_width` 比较、`has_trait`、地形条件等（原版 1.19 里 **没有 `hard =` / `soft =` 软硬系数**——那是旧版写法，现在用 `attacker = N` / `defender = N` 战果系数） | 骨架 |
| 5 | 克制关系 | `countered_by = tactic_<名>`（被谁克制）；对方选了克制战术则本卡效率大跌——攻防双向都要写 | 骨架 |
| 6 | 特殊阶段 | 全局 `phases = { close_combat tactical_withdrawal seize_bridge hold_bridge street_fighting }`（文件顶部已有，勿删）；块内 `display_phase = <阶段>` 让卡只在特定阶段出现 | 视需求 |
| 7 | 挂接 | 学说 `enable_tactic = tactic_<名>`、国策/特质同理；战术选取概率由 `base` 权重 × 领导人技能/特质/地形决定 | 视需求 |
| 8 | 本地化 + 图片 | 本地化 key 就是战术名（`tactic_<名>` 与 `<名>_desc`，原版在 `localisation/english/tactics_l_english.yml`）；`picture = <名>` 引用已注册的战术卡图——**优先复用原版 picture 名**（`attack`/`defend`/`tactic_sf_ambush` 等，零素材） | 骨架 |

**验收**：`error.log` 无 tactic 相关报错；进游戏开一战：新卡出现、选取概率符合 `base`、克制关系生效、加成数值对。

**提醒用户**：改这张表前备份；`countered_by` 指向的战术必须存在（写错名该卡选取逻辑会出错）；自定义贴图时在 `interface/*.gfx` 注册 sprite，全局搜 `GFX_tactic_` 参考原版。

## 十七、分析崩溃原因（crashes 最新转储）

**崩溃目录**：`%USERPROFILE%\Documents\Paradox Interactive\Hearts of Iron IV\crashes\`，每个转储是 `hoi4_YYYYMMDD_HHMMSS` 文件夹——**取时间戳最新的**。

**流程**：

| # | 步骤 | 要点 |
|---|---|---|
| 1 | 取最新转储 | 文件夹内应有 `exception.txt`（堆栈）、`logs\error.log`（**当次运行**的日志）、`minidump.dmp` |
| 2 | 读 exception.txt | 堆栈**全是 `PHYSFS_*` 无符号时基本没用**——不要试图从堆栈猜；但可留作指纹：两次崩溃堆栈帧偏移完全相同 = 同一根因 |
| 3 | 找当次日志 | 优先 `crash文件夹\logs\error.log`；若没有再读标准 `...\logs\error.log`。**核对时间戳**是否与 exception.txt 的崩溃时刻吻合（实测：日志可能滞后写、也可能根本没写进标准目录） |
| 4 | 时间线分析 | 日志只覆盖几十秒且无 `Launching SINGLEPLAYER-game` = **没进过游戏**（选国家/加载阶段挂）；有无 `Executing History` 决定崩在哪个阶段 |
| 5 | 关键词扫描 | 见下方「崩溃关键词 → 病因」表，逐个 grep 并**计数** |
| 6 | 噪音过滤 | `containerwindow.cpp` / `gfx_texture_loader.cpp` / `graphics.cpp` / `dlc.cpp` / `texturehandler.cpp` / `spritetype.cpp` / `pdxmeshtype.cpp` / `pdxassetutil.cpp` / 音频类是噪音；其余按「(来源cpp, 数字归一化的消息)」聚合**错误签名** |
| 7 | 对照法 | 手上有「上次能跑」的日志时，做**签名差集**：今天新增的错误 = 头号嫌疑；再结合最近改过的文件（git status/diff）定位 |
| 8 | 结论输出 | 根因 + 证据行（原文引用）+ 修复方案 + 修完后的复验方法 |

**崩溃关键词 → 病因 → 修法**（关键词全为 0 时才考虑别的方向）：

| error.log 关键词 | 病因 | 修法 |
|---|---|---|
| `location is not within specified state ... BUILDING IGNORED!` | `map/buildings.txt` 声明州与坐标所在省不符 | 重建同步（`map-data.md`） |
| `Province N is setup as coastal but has no port building` | 港口 `naval_base_spawn` 被忽略 → 该省无港口 | **会崩**。同步 buildings.txt |
| `MAP_ERROR: no air base site / no rocket site / no gun emplacement defined for state N` | 州级生成点被搬走 | **会崩**。生成点留原州（`map-data.md`） |
| `parser.cpp: unexpected token` / `Unknown History Command` / `persistent.cpp: Unexpected token` | **州文件语法损坏** | 过 `map-data.md` 的「语法关」逐文件修 |
| `MAP_ERROR: The land province N has no state.`（成百上千条） | 州文件大面积解析失败，或省无归属 | 查 state 文件结构 + 省归属唯一性 |
| `state.cpp: no provinces in state ... with id: N` | 同上（解析失败的州等于没有省） | 同上 |
| `Failed to create id N ... Already exists in game` | id 全局重复（角色/装备等） | 可能崩；grep 该 id 找重复定义 |
| `has too many buildings : -N` | 州建筑计数为负 | 建筑块结构问题 |

**经验教训（实测）**：

- 堆栈无符号时**别信堆栈**，日志尾部的 `MAP_ERROR` / `buildings.txt error` 才是病因；两次堆栈相同 = 同根因。
- 闪退后 `crashes\` 里**可能根本没有当次转储**、标准日志目录也可能没更新——那时让用户手动提供日志，或清空 error.log 后复现一次再取。
- 「错误签名归一化」（消息里的数字→N 再聚合）是对比两次日志的核心手段。
- 修复后**必须复跑同样的关键词清单确认全 0**，且语法关（`map-data.md`）与不变量都要过。

## 十八、其他高频小任务（速查）

| 任务 | 组成 |
|---|---|
| 新装备 | `common/units/equipment/*.txt` + 变体 + 本地化；舰船另需 `common/units/ships/` |
| 新科技 | `common/technologies/*.txt` + `interface/technologies` 图标 + `common/technology_tags` 分类 + 本地化 |
| 新游戏规则（game rules） | `common/game_rules/*.txt` + 本地化；脚本里 `has_game_rule` 引用（**规则不存在会刷 `game rule xxx does not exist`**） |
| 新战略区 | `map/strategicregions/*.txt`（id 唯一、**provinces 列省不列州**） |
| 新补给节点/铁路 | `map/supply_nodes.txt` / `map/railways.txt`（坐标为像素坐标） |
| 载入提示 | `localisation/.../loading_tips_l_*.yml` |
| 挪省/改州归属 | **走 `map-data.md` 完整流程**（state 文件 + `map/buildings.txt` 同步 + 语法关） |
| 建筑悬空/穿模 | **走 `buildings-height.md`**（高程重算 + 防穿模抬升） |
| 单位 category key 查询 | 附录 `unit-categories-参考.txt`（**只查不放进 mod**） |
