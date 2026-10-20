# MEMORY.md —— 提瓦特黎明（DOT Gamma）项目备忘
> 语法/排查见技能 `hoi4-mod-bug-triage`；工具链/路径见 `DOT_制作手册.md`；各国设计见 `.workbuddy\*_Design.md`；逐轮细节见同目录 `2026-10-*.md`。本文件只记铁律与当前口径。

## 0. 铁律
- 禁恢复/回滚、禁 git 提交、禁「注释掉问题代码」；一律在现状上加工。中文注释只写中文不写 ID。旧 loc 全不删；`ABY_focus.txt` 不动；focus 文件保留 `focus_tree` 头。
- 数量一律为下限；直接改原文件禁建 `_v2`。事件/新闻 desc 200–400 字（去空白），生成下限取 **206**（`style()` 会削 2–5 字）。**禁破折号**（`—–―─－`）。
- 新增事件/精神/loc/决议/类别/动修/宏/`on_actions` 一律并入同名 `<国>_*` 文件，禁另起平行文件。新闻必须由国策/事件 `completion_reward` 触发（`news_event = { id = NS.n days = 1 }`），禁按日期批量发射。`add_namespace = X` 写在事件文件自身首部，禁单独建 namespace 文件（否则整份 Malformed）。
- **focus 的 tag 限定＝「树头白名单 + 少数关键国策」**：一棵 `focus_tree` 一组 tag，多国＝整块绝对 x 平移；树头 `country = { or = { tag = … } }`，focus 级只给路线分叉点/终局写 `available`（LYY 30、SUM 18）。缺省 `available`＝`always = yes`，已删净（`strip_avail_always.py`）；同 focus 多个 `available` 后者覆盖前者（现 0 处）。
- 新增决议必须带 `has_completed_focus` + `visible = { … }`。**`visible` 缺省是「一直可见灰着」，不想让人看见必须显式写**。门槛国策要**遍布国策树**（按绝对深度 y 分层，别全压开局 6 个），见 `map_sum_decisions.py`。
- 机制修正分阶段：`*_Init` 只置初值 + 调一次 `*_Tier_Refresh`；`*_Tier_Refresh` 先卸全档再挂唯一致命一档；**轴宏 `<M>_A/B_Up_N` 只改变量、不再调 `Tier_Refresh`**；档位保鲜由 `on_actions` 的 `*_Sync`（`on_daily`）负责；每档配只读面板（`visible`=档位条件，`available = { always = no }`，`cost = 0`）。
- **★死规矩：只有 ≤10% 的国策/决议可以改 `dynamic_modifier`。** 现状 0.4%（11 个＝机制启用里程碑）。冗余的定义是「同一组修正被大量 `effect xxx = yes` 反复引用」，**不是**「一个决议里并列 4~9 条不同修正」——后者正当禁删（`converge_modifiers.py` 已停用）。
- **轴指数变化必须可见**：`add_to_variable` 无 tooltip，被 `hidden_effect` 包住玩家就看不到 ⇒ 轴指数 `add_to_variable` 必须提到包外，逐条配 `custom_effect_tooltip = <变量>_Add_<N>`／`_Decrease_<N>`（`§G加N§!`／`§R减N§!`）；纯机械尾巴留包内。
- **Tooltip 卫生**：`hidden_effect` 只包 `*_Tier_Refresh`/`*_Sync` 正文 + 连续 ≥2 行纯变量/旗标段；**轴宏 `<M>_A/B_Up_N` 不整体包**。`custom_effect_tooltip` 必须留包外；作者常把 `add_to_variable = {…} custom_effect_tooltip = X` 写在同一行，那种行不能进包。审计前**先剥 `#…` 注释**（NAT 有 224 行注释残留会误报）。
- **备份一律放 MOD 外**：`C:\Users\XIANGZIYUAN\hoi4lint\_backup_*`。MOD 内的 `*.backup_*` 会被当数据重复读取。
- **★loc 必须带 UTF-8 BOM**：含中文的 `localisation/**/*.yml` 缺 BOM 会被 HOI4 **整份静默丢弃**（症状＝某国决议/事件本地化**全空**）⇒ 每轮跑 `check_loc_bom.py`（现 114 文件／缺 0／裸 LF 0）。第五轮即因 `NAT_Neo_Script_l_simp_chinese.yml` 唯一缺 BOM，导致纳塔决议 loc 全空。
- **loc 里禁止泄漏变量 ID**：写「体制惯性：`[?KQP-Inertia-Index]`」，不写「（变量 KQP-Renew-Index）」（`fix_var_labels_loc.py`，已清 34 处）。变量显示名定义（`NAT-ABY-Index:"§G深渊侵蚀度§!"`）合法，保留。
- **机制状态并入「重要信息公示」(Info_Board)**：空决议类别（`visible_when_empty = yes` + tag/旗标可见）+ `priority = { base = 100 }`（**★不是 `priority = N`**）。`_desc`＝每轴 `§Y<轴名>：§![?<VAR>]\n§W[<轴>_tier_name]§!\n§G[<轴>_tier_mods]§!`，末尾共振同构；无轴退 `DOT_Info_Board_NotStarted`、无共振退 `DOT_Info_Board_NoCombo`。
- 只用 5 种基础意识形态，禁子意识形态；`set_cosmetic_tag` 按意识形态上色。机制效果用 decision。跨表全局 id 带层别标记。
- `on_actions` 内容必须包在 `effect = { }`（裸写 `every_country` 会让整份文件作废且静默）。
- 文案守 `.skills\Darwin Skills.md` 十条（只改风格不动事实）。

## 1. 环境
- Python=`…\binaries\python\envs\default\Scripts\python.exe`；Bash 优于 PowerShell。脚本无 BOM+CRLF；loc `.yml` 必须 BOM+CRLF 并自检；focus/ideas/events 用 tab，loc 键前导一空格；`.asset` 无 BOM+CRLF。Edit 同文件并行会互相覆盖⇒串行。动手前先备份。
- MOD 根 `…\Daybreak of Teyvat Gamma Version`；脚本+备份 `C:\Users\XIANGZIYUAN\hoi4lint\`。生效 `replace_path`：history/*、bookmarks|resources|ai_strategy*、events、decisions|countries、strategicregions|supplyareas（`national_focus`/`gfx` **不在内**）。工作区「活的」，会被外部整份覆盖⇒先核实再改；`game.log` 报 Loaded 11507 provinces 才是本 MOD。

## 2. HOI4 语法（1.19.3）
- modifier loc：`_<modifier>_tt` 与 `MODIFIER_<大写>`。无 farm/power_plant/reconnaissance/`army_defense_factor`/`factory_output`/`manpower_factor`/`corruption`；英式 `army_defence_factor`，农业用 `monthly_population`。
- **哪些效果有 tooltip**：`add_dynamic_modifier`/`remove_dynamic_modifier`、`add_ideas`、`add_stability` 等**有**；`add_to_variable`/`set_variable`/`set_country_flag`/`clr_country_flag` **没有**（要显示须另配 `custom_effect_tooltip`）。⇒ tooltip 膨胀主因是动修与可见效果，不是变量。
- 前置：多个 `prerequisite = { }` 块是 **AND**，一块内多条 `focus =` 是 **OR**。
- 决议 `icon=<裸名>`→`GFX_decision_<裸名>`，分类→`GFX_decision_category_<裸名>`；分类描述键 `_desc`；空分类要显示须 `visible_when_empty = yes`。
- `annex_country={target=X transfer_troops=yes}`；`set_autonomy` 用 `autonomy_state`，history 用 `autonomous_state`。
- `hoi4lint\vanilla_modifiers.json`(647) 是新效果硬约束；`remove_dynamic_modifier = { modifier = X }` 可用；`on_actions` 跨文件叠加，挂载缺失静默。
- 一颗 `hidden_effect = { }` 只隐藏 tooltip、不改行为；档位刷新带旗标卫兵（`NOT has_country_flag <档>_At`）后幂等。
- **兵模挂接靠命名约定**：`entity = { clone = "<源>" name = "<TAG>_<infantry|artillery|cavalry>_<0..3>_entity" }`，每 tag 12 个即自动生效。**★clone 不能覆盖 attach**：`Amber_artillery_entity` 写死炮手、`Amber_sabre_cavalry_entity` 写死骑手 ⇒ 别国 clone 出来是「安柏的炮组/安柏骑的马」。正确做法＝每角色各建 `<角色>_artillery_entity`（炮手=自己步兵），tag 只 clone 本阵营角色。悬空校验**按 clone 值反查 name 集合**（曾漏报 `Ayaka_artillery_entity` 被 8 处引用却未定义）。
- **角色兵模三件套**：`*_sabre_infantry_rider_entity`（角色 mesh + cavalry 动画 + sabre）＋`*_sabre_cavalry_rifle_combined_entity`（`infantry_cavalry_horse_mesh`，`Saddle_Node`=骑手，0.65）＋`*_sabre_cavalry_entity`（`infantry_cavalry_horse_frame_mesh`，挂 infantry/cavalry/`DOT_infantry_cavalry_horse_entity`，1.2）；炮兵＝`frame_artillery_mesh` + `artillery_gun_entity` + `infantry=<自己>_infantry_entity`（1.0），`artillery_gun_entity` 是原版实体须白名单。**★步炮兵段（`*_infantry_entity`）sabre 节点是 `Right_Hand_node_4`/`mid_back_node_2`，骑兵段是 `Right_Hand_node`/`mid_back_node`**（10-19 已按用户要求删前者 24 行／12 文件，骑兵保留）。
- **MIO 图标按 tag 所属地区取**：`gfx/interface/ideas/<地区>/` 对应 `GFX_idea_<地区>_*`（MOT 蒙德／LYY 璃月／INA 稻妻／SUM 须弥／FON 枫丹／NAT 纳塔／SNE 至冬／NDK 挪德卡莱／PRI 天理），判不出地区（ABY、`DOT_generic` 里 `allowed` 全是 `NOT` 的通用组织）一律用 `DOT` 池。组织→tag 读 `allowed` 的 `tag`/`original_tag`/`Is_X = yes`，**先剥 `NOT = { … }`**。**原图标已含本地区/本 tag token 的保留不动**（作者手挑）。

## 3. 各国口径（细节见设计文档/日志）
- **NAT**：六族 `NCP/NCE/NPS/NSC/NFF/NMN`；变量 `NAT-ABY-Index`(40)/`MVK-Prestige-Index`(50)/`NAT-War-Index`/`NAT-Anance-Index` 不可改名，走 `NAT_Abyss_Add/Sub_*`、`NAT_Grace_Add/Sub_*`。四阶段 `autonomy_puppet`→`autonomy_NAT_State`→恩情>79 `annex_country`→恩情<19 脱离宣战（先 `end_puppet` 再宣战）。国策171/决议69/事件88/精神205。18 个分宗决议带 `ai_will_do = { base = 1 modifier = { add = 100 is_subject_of = NAT } }`（`nat_dissent_ai.py`）；`NAT_Dissent_<族>` 旗标在 NAT 与部族两边都设，故 NAT 自己也能看到分宗决议（未堵）。
- **LYY**：六派 KQP=communism／LYY=democratic／GYP=neutrality／SHP=fascism／YLH=fascism·neutrality／CYG=genshin，每派 2 路线共 12。战后层 y∈[22,34]、id 带 `PW`、块标记 `# == <TAG> POST-WAR focus tree BEGIN/END ==`。170 决议全带门槛；六派内战各 1 个 `*_Info_Board`（凝光加 `LYY_Tianquan_Eternal`）+ 战后各 1 个 `*_PW_Info_Board`。生成器 `_civilwar\cw_engine.py`。
  **tag 限定现状**：树头 `country = { or = { tag = LYY/GYP/SHP/KQP/BRF/CYG/YLH } }`；focus 级共 **30** 个＝6 内战根 + 原树 6 个 + **18 个路线关键国策**（每派 3 个＝分叉点 + 两条路线终局；**具体 id 见 `2026-10-19.md`，`LYY_CivilWar_Design.md` 的路线门 id 与实际文件不符，只有 KQP 对得上，以 `_diag_lyy_forks.py` 为准**）。脚本 `gate_lyy_route_focuses.py`。
- **SAN**：三终局 御神归鸣／万岛共和／御建承继，分叉 `SAN_PW_The_Crossroads`；双轴 `SAN-Mandate-Index`(40)／`SAN-Deep-Index`(30)。改走 `_san\patch_pw_stage.py`（勿重跑引擎）。
- **SUM**：雨林 id `SUM_Neo_Focus_Tree`（起始 `SUM_PRO_Dawn_of_Sabzeruz`），324 国策 5 簇；沙漠 SGD/SDH/SGS 同树右侧（x 雨林[0,62]／SGD[70,138]／SDH[146,214]／SGS[222,290]），各 188 国策 6 簇。合计 国策888／事件888／决议**170**／loc6602＝107 个 `SUM_Neo_Dec_*` + 63 个沙漠 `SUM_{SGD,SDH,SGS}_*`；门槛重映射为 **162 个不同国策**、深度 y3–y33、30 分支（`map_sum_decisions.py`）。4 个 Info_Board。
  **生成器纪律**：只重建国策用 `_sum/regen_focus_only.py`、`_desert/regen_inc_focus.py`，**禁重跑 main()**（会冲掉 Darwin 改写）。**重跑生成器会把前置拆回多块 AND、并冲掉 `ai_will_do`，需重跑 `merge_sum_prereq.py` + `set_ai_weights.py` 补回。**
  **10-19**：27 个 focus 前置合并为单块多条（AND→OR，块 949→865、条目 111 守恒）；AI 权重 圣树加冕 50／共和 25／造神 25，沙漠 IND 线 10／WAR 线 6（共 180 focus）；沙漠独立线国策本身已带 `end_puppet` + `puppet_wargoal_focus`，无需加效果。

## 4. 新闻 / 文案 / 工具链
- 新闻四表：雨林12、沙漠各10、璃月战后20、珊瑚宫10，均挂国策 `completion_reward`；改完跑 `_desc\check_news_anchors.py`。Darwin：`_desc\darwin_pass.py`（`fit(200,400)`，`--check` 只读），越界0／破折号0。
- 结构/性能/文案：`wrap_hidden_effects.py`、`verify_wrap.py`、`fix_axis_tooltips.py`、`audit_dm_refs.py`、`cut_dm_from_focus_path.py`、`restore_modifiers.py`、`check_tooltip_keys.py`、`optimize_tier_chains.py`。
- loc/面板/国策：`check_loc_bom.py`（`--fix`）、`fix_var_labels_loc.py`、`inv_info_boards.py`、`build_info_boards.py`、`check_info_boards.py`（三向校验，忽略 `GFX_*`）、`strip_avail_always.py`、`merge_sum_prereq.py`、`set_ai_weights.py`、`gate_lyy_route_focuses.py`、`map_sum_decisions.py`。
- 兵模：`bind_unit_models.py`、`fix_artillery_entities.py`、`rebuild_entities_law.py`（兰那罗炮兵/骑兵 + 优菈炮兵 + LAW 迁到优菈）、`dedup_entities.py`、`strip_infantry_sabre.py`、`verify_entities2.py`（剥注释查重名/悬空/每 tag 12 个）、`reicon_mio_by_region.py` + `verify_mio_icons.py`（**取代旧 `reicon_mio.py`**）、`nat_dissent_ai.py`。`hoi4-icon-gfx-pipeline` 技能。
- 一律 dry-run 先行、`--apply` 才写、幂等、自动备份出 MOD。

## 5. 遗留
- 未实测：`end_puppet` 对 `autonomy_*`、`create_country_leader`、动修是否真挂、国策横排／档位逐档变化／面板与生效修正一致／决议门槛是否挡住／兵模是否上屏；`hidden_effect` 是否如预期静音 tooltip。
- **NAT 缺 `on_actions` 挂载（待用户定夺）**：真正**零调用者**的是三个时间漂移效果 `NAT_ABY_Monthly_Tick`／`NAT_GRACE_Monthly_Tick`／`NAT_V3_Monthly_Tick` ⇒ 「每月」机制永远不跑；Add/Sub 宏内部都调 Sync 且被国策大量调用，是活的。修法＝新建 `common/on_actions/NAT_Neo_on_actions.txt` 挂 `on_monthly`（会改平衡，须用户点头）。- 真悬空 `custom_effect_tooltip` 5 个（缺 loc 的遗留块）：`DOT_Backup_decisions.txt` 的 `LYY_qiming/ningguang/shenhe_support_increase_tooltip`；`LYY_decisions.txt` 劳动法块的 `LYY_people_satisfaction_increase/decrease_tooltip`；`LAW_decisions.txt` 的 `LAW_High_Resist_Here`。
- **MOD 内疑似重复读取源（未动）**：`…\.backup\`；`common/decisions/DOT_Backup_decisions.txt`（其类别与 `categories/LYY_decision_categories.txt:221` 重复声明）。
- **★工作区会被并行改写**：10-19 18:23–18:30 期间 `gfx/entities/*.asset` 被人（或另一会话）逐份改写，把 tag↔角色 重排并删掉部分 tag。⇒ **改完必须隔几分钟再复核一次**；发现内容与记录不符时先取证、别覆盖。**当前实体口径（用户 10-19 定）**：PBF→娜维娅、SGD→纳西妲、SNE 两份重复不管；BRF／MHL／VLM／SFS／SDS／SKD／SGC／SFG／YLH **明确不补兵模**。剩余重复只 SNE 12 个 + `Nilou_infantry_entity` 2 个（后者第 9 行简版／第 31 行详版，后者生效，既有问题）。
- **`DOT_Aranara.asset` 的 `VAN_infantry_entity` 名实不符（未动）**：pdxmesh 是 `frame_artillery_mesh` + 炮兵 attach，即 VAN 的「步兵」实际渲染成炮；且 VAN 只有 4 个步兵克隆，缺 artillery/cavalry。`Aranara_*` 三件套已建好但**无 tag 克隆**（MHL 按口径不补），要用只需加克隆块。
- 旧33决议 25 个 `GFX_decision_*` 图标无声明；`events/LYY_*` 注释编码损坏；`add_tech_bonus` 类别未知名；GUN 吞并 state 已禁用；Palace 不显示；VAN 未做。范围外悬空引用 14 条（详见日志）。
- **校验脚本断言要跟架构走**：改架构（如删机制面板）后 `_civilwar/verify_requirements.py`、`_san/verify_san_pw.py` 会假报红，须同步改断言。
