# MEMORY.md —— 提瓦特黎明（DOT Gamma）项目备忘
> 语法/排查见技能 `hoi4-mod-bug-triage`；工具链/路径见 `DOT_制作手册.md`；各国设计见 `.workbuddy\*_Design.md`；逐轮细节见同目录 `2026-10-*.md`。本文件只记铁律与当前口径。

## 0. 铁律
- 禁恢复/回滚、禁 git 提交、禁「注释掉问题代码」；一律在现状上加工；中文注释只写中文不写 ID。旧 loc 全不删；`ABY_focus.txt` 不动；focus 文件保留 `focus_tree` 头。
- 数量一律为下限；直接改原文件禁建 `_v2`。事件/新闻 desc 200–400 字（去空白），生成下限取 **206**（`style()` 会削 2-5 字）。**禁破折号**（`—–―─－`）。
- 新增事件/精神/loc/决议/类别/动修/宏/`on_actions` 一律并入同名 `<国>_*` 文件，禁另起平行文件。新闻必须由国策/事件 `completion_reward` 触发（`news_event = { id = NS.n days = 1 }`），禁按日期批量发射。
- `add_namespace = X` 写在事件文件自身首部，禁单独建 namespace 文件（否则整份 Malformed）；新闻块接在事件之后。
- 一 tag 组只写一棵 `focus_tree`；多国＝整块绝对 x 平移到右侧；**每个节点都要 `available = { tag = <归属> }`**（小写 `tag`，主国块也要）。
- 新增决议必须带 `has_completed_focus`（取分叉点前的通用国策）+ `visible = { has_country_flag = <旗标> }`。**visible 缺省是「一直可见灰着」，不想让人看见必须显式写 visible**。
- 机制修正分阶段：`*_Init` 只置初值 + 调一次 `*_Tier_Refresh`；`*_Tier_Refresh` 先卸全档再挂唯一致命一档；**轴宏 `<M>_A/B_Up_N` 只改变量、不再调 `Tier_Refresh`**（见下方死规矩）；档位保鲜由 `on_actions` 的 `*_Sync` 负责（`on_daily`）；每档配只读面板（`visible`=档位条件，`available = { always = no }`，`cost = 0`）。
- **★死规矩：只有 ≤10% 的国策/决议可以改国家动态修正 `dynamic_modifier`。** 现状 0.4%（剩 11 个＝机制启用里程碑国策）。冗余的定义是「同一组修正被大量 `effect xxx = yes` 反复引用」，**不是**「一个决议里并列 4~9 条不同修正」——后者正当，禁删（`converge_modifiers.py` 已停用）。
- **轴指数变化必须可见**：`add_to_variable` 本身无 tooltip，被 `hidden_effect` 包住玩家就看不到 ⇒ 轴指数 `add_to_variable` 必须提到 `hidden_effect` 外，逐条配 `custom_effect_tooltip = <变量>_Add_<N>` / `_Decrease_<N>`（文案 `§G加N§!`/`§R减N§!`）；纯机械尾巴（`*_Tier_Refresh` 等）留在包内，可用一句 `custom_effect_tooltip` 说明旧修正移除。
- **Tooltip 卫生（修正版）**：仍需 `hidden_effect` 包的是 `*_Tier_Refresh`/`*_Sync` 正文 + 连续 ≥2 行的纯变量/旗标段；**轴宏 `<M>_A/B_Up_N` 不再整体包裹**（其轴指数行要可见，见上条）；`custom_effect_tooltip` 必须留在包外。注意作者会把 `add_to_variable = {…} custom_effect_tooltip = X` 写在**同一行**，那种行不能进包。审计 `custom_effect_tooltip` 键时**必须先剥掉 `#...` 注释**（NAT 有 224 行注释残留会造成误报）。
- **备份一律放 MOD 外**：脚本生成的 `*.backup_*` 落在 MOD 里会被游戏当数据重复读取（loc 键/脚本重复）⇒ 一律写 `C:\Users\XIANGZIYUAN\hoi4lint\_backup_*`。
- **★loc 必须带 UTF-8 BOM**：含中文的 `localisation/**/*.yml` 缺 BOM 会被 HOI4 **整份静默丢弃**（症状＝某国决议/事件本地化**全空**，而非个别键失效）⇒ 每轮跑 `check_loc_bom.py`（现状 114 文件／缺 0／裸 LF 0）；写 loc 的脚本一律强制前置 `\xef\xbb\xbf` 并跟随原文件 CRLF。第五轮即因 `NAT_Neo_Script_l_simp_chinese.yml` 是 114 个 loc 里**唯一缺 BOM** 的，导致纳塔决议 loc 全空。
- **机制状态并入「重要信息公示」(Info_Board)**：空决议类别（`visible_when_empty = yes` + tag/旗标可见条件，仿蒙德 `MOT_Important_Shows`，本身不占决议位）。`_desc` 结构＝每条轴 `§Y<轴名>（变量 <VAR>）：§![?<VAR>]\n§W[<轴>_tier_name]§!\n§G[<轴>_tier_mods]§!`，末尾 `§Y共振：§!§W[<前缀>_Combo_combo_name]§!\n§G[<前缀>_Combo_combo_mods]§!`；无轴退 `DOT_Info_Board_NotStarted`，无共振退 `DOT_Info_Board_NoCombo`。**旧「机制状态面板」（`*_mech_category`／`SAN_PW_Mechanism`，每套 14 条只读决议）第五轮已全删（17 个：LYY 12／SUM 4／SAN 1），改为写进 Info_Board 描述。** 全部 17 个 `*_Info_Board`（6 新建 LYY 内战 + 11 原有）`priority = { base = 100 }`；凝光 `LYY_Info_Board` 加 `visible = { tag = LYY has_completed_focus = LYY_Tianquan_Eternal }`。**★类别优先级写法是 `priority = { base = N }`**（不是 `priority = N`）。scripted-loc 三类：`<轴>_tier_name`／`<前缀>_Combo_combo_name`／`<前缀>_Combo_combo_mods`（加原有 `<轴>_tier_mods`）。
- 只用 5 种基础意识形态，禁子意识形态；`set_cosmetic_tag` 按意识形态上色。机制效果用 decision。跨表全局 id 带层别标记。
- `on_actions` 内容必须包在 `effect = { }`（裸写 `every_country` 会让整份文件作废且静默）。
- 文案守 `.skills\Darwin Skills.md` 十条（只改风格不动事实）。

## 1. 环境
- Python=`…\binaries\python\envs\default\Scripts\python.exe`；Bash 优于 PowerShell。脚本无 BOM+CRLF；loc `.yml` 必须 BOM+CRLF 并自检；focus/ideas/events 用 tab，loc 键前导一空格。Edit 同文件并行互相覆盖⇒串行。动手前先备份。
- MOD 根 `…\Daybreak of Teyvat Gamma Version`；脚本+备份 `C:\Users\XIANGZIYUAN\hoi4lint\`。生效 `replace_path`：history/*、bookmarks|resources|ai_strategy*、events、decisions|countries、strategicregions|supplyareas（`national_focus`/`gfx` 不在内）。工作区「活的」，会被外部整份覆盖⇒先核实再改；`game.log` 报 Loaded 11507 provinces 才是本 MOD。

## 2. HOI4 语法（1.19.3）
- modifier loc：`_<modifier>_tt` 与 `MODIFIER_<大写>`。无 farm/power_plant/reconnaissance/`army_defense_factor`/`factory_output`/`manpower_factor`/`corruption`；英式 `army_defence_factor`，农业用 `monthly_population`。
- **哪些效果有 tooltip**：`add_dynamic_modifier`/`remove_dynamic_modifier`、`add_ideas`、`add_stability` 等**有**；`add_to_variable`/`set_variable`/`set_country_flag`/`clr_country_flag` **没有**（要显示须另配 `custom_effect_tooltip`）。⇒ tooltip 膨胀的主因是动修与可见效果，不是变量。
- 决议 `icon=<裸名>`→`GFX_decision_<裸名>`，分类→`GFX_decision_category_<裸名>`；分类描述键 `_desc`；空分类要显示须 `visible_when_empty = yes`。
- `annex_country={target=X transfer_troops=yes}`；`set_autonomy` 用 `autonomy_state`，history 用 `autonomous_state`。
- `hoi4lint\vanilla_modifiers.json`(647) 是新效果硬约束；`remove_dynamic_modifier = { modifier = X }` 可用；`on_actions` 跨文件叠加，挂载缺失静默。
- 一颗 `hidden_effect = { }` 只隐藏 tooltip、不改行为；可嵌套但没必要。档位刷新带旗标卫兵（`NOT has_country_flag <档>_At`）后幂等，连写两次等于一次。

## 3. 各国口径（细节见设计文档/日志）
- **NAT**：六族 `NCP/NCE/NPS/NSC/NFF/NMN`；变量 `NAT-ABY-Index`(40)/`MVK-Prestige-Index`(50)/`NAT-War-Index`/`NAT-Anance-Index` 不可改名，走 `NAT_Abyss_Add/Sub_*`、`NAT_Grace_Add/Sub_*`。四阶段 `autonomy_puppet`→`autonomy_NAT_State`→恩情>79 `annex_country`→恩情<19 脱离宣战（先 `end_puppet` 再宣战）。国策171/决议69/事件88/精神205。
- **LYY**：六派 KQP=communism／LYY=democratic／GYP=neutrality／SHP=fascism／YLH=fascism·neutrality／CYG=genshin，每派 2 路线共 12。战后层 y∈[22,34]、id 带 `PW`、块标记 `# == <TAG> POST-WAR focus tree BEGIN/END ==`。170 决议全带门槛；六派**内战**各 1 个 `*_Info_Board`（第五轮新增，凝光加 `LYY_Tianquan_Eternal` 门槛）+ 战后各 1 个 `*_PW_Info_Board`（原有点，机制状态已并入其描述）。生成器 `_civilwar\cw_engine.py`。
  **★tag 限定现状（10-17 已按用户口径收紧，勿再记错）**：`LYY_Neo_Focus.txt` 的 tag 限定分两层——① 树头 `country = { or = { tag = LYY/GYP/SHP/KQP/BRF/CYG/YLH } }`（7 tag 共用）；② focus 级共 **30** 个：6 个内战根 `{KQP,LYY,GYP,SHP,YLH,CYG}_CivilWar_*`、原树 6 个（`LYY_Rock_and_Covenant`=LYY+genshin、`LYY_Nation_{Fatui_and_Osial=YLH,Black_Rock_Factory=BRF,Chenyu_Valley=CYG}`、`LYY_Crisis_{Water_and_Soil,Land_Amidst_Monoliths}`=ABY）、**10-17 新增 18 个路线关键国策**（每派 3 个＝路线分叉点 + 两条路线终局，见下）。**10-17 12:29 起全库 `available = { always = yes }` 已删净（0 个）**：748 个 focus 中**无 available 块 707**、有真实条件 41、`always = yes` 0。删空键≠行为变化（focus 缺省即可用），但**文件里只剩真门控**，一眼可读。脚本 `strip_avail_always.py`（dry-run/`--apply`，幂等，只删 exact，mixed/empty 不碰，备份出 MOD）。
  **★六内战根的重复 `available` 已于 10-17 清理**：原先是模板默认 `available = { always = yes }` + 用户手工追加的 `available = { tag = <本方>, has_completed_focus = LYY_Rite_of_Parting }`（YLH 那个还把 `has_completed_focus` 注释掉了），HOI4 后者覆盖前者、行为正确但前一个是死键。**10-17 12:29 应用户指令「将国策文件中所有的 `available = { always = yes } 这一条删去」把死键删掉**，现在六根各只剩用户手写的那一个真门控；全库「同一 focus 多个 available」＝**0**。教训：**同块重复键会被后者覆盖，生成器模板留下的 `always = yes` 是死键，但清理前必须先确认第二个键存在**（本次六根均如此）。
  **补门控口径（用户 10-17 原话）**：「你只需要将少数关键国策加上限制就好，就像我之前的代码所写，你直接抄它的 available」——参照物就是上述六根手写的第二个 `available`。落地脚本 `gate_lyy_route_focuses.py`（dry-run/`--apply`，幂等，备份出 MOD）。**18 个路线关键国策**：KQP{`The_Great_Debate`,`Manifesto_of_Yuheng`,`Perpetual_Tutelage`}／LYY{`The_Right_Question`,`Constitution_of_Jade`,`Tianquan_Eternal`}／GYP{`The_Question_of_Heaven`,`The_Moonlit_Reign`,`The_Regent_Eternal`}／SHP{`The_Grand_Vigil`,`The_Lone_Ascension`,`The_Immortal_Throne`}／YLH{`The_Queens_Word`,`The_Last_Envelope`,`The_Throne_of_Ice`}／CYG{`The_Valley_Charter`,`The_Green_Pact`,`The_Last_Green_Hill`}。**注意设计文档 `LYY_CivilWar_Design.md` 里的路线门 id 与实际文件不符（只有 KQP 对得上），以 `_diag_lyy_forks.py` 结构化回溯的结果为准。**
  **参照系**：须弥 `SUM_Neo_Focus.txt` 同样只 gate 18 个关键国策（3 雨林路线根 + 沙漠各国 5 个），其余 870 个的 `available` 只是 `search_filters` 占位——「少数关键国策」才是本仓既定口径，不是 748 个全 gate。
- **SAN**：三终局 御神归鸣／万岛共和／御建承继，分叉 `SAN_PW_The_Crossroads`；双轴 `SAN-Mandate-Index`(40)／`SAN-Deep-Index`(30)。`SAN_PW_Info_Board`（机制状态已并入其描述）。改走 `_san\patch_pw_stage.py`（勿重跑引擎）。
- **SUM**：雨林 id `SUM_Neo_Focus_Tree`（起始 `SUM_PRO_Dawn_of_Sabzeruz`），324 国策 5 簇；沙漠 SGD/SDH/SGS 同树右侧（x 雨林[0,62]／SGD[70,138]／SDH[146,214]／SGS[222,290]），各 188 国策 6 簇。合计 国策888／事件888／决议**170**（第四轮 174，第五轮删 4 个机制面板）／loc6602。决议＝107 个 `SUM_Neo_Dec_*` + 63 个沙漠 `SUM_{SGD,SDH,SGS}_*`。4 个 Info_Board（`SUM_Neo_Info_Board` + 3 沙漠）。**只重建国策用 `_sum/regen_focus_only.py`、`_desert/regen_inc_focus.py`，禁重跑 main()**（会冲掉 Darwin 改写）。**10-19 前置条件已全部改为 OR**：27 个 focus 原为 3/5/6 个并列 `prerequisite` 块（AND），已合并为单块内多条 `focus =`（OR），`prerequisite` 块 949→865、focus 888 不变、条目 111 守恒；脚本 `merge_sum_prereq.py`（dry-run/`--apply`，只并「块内仅含 focus =」的，备份出 MOD）。**重跑生成器会把前置拆回多块，需重跑该脚本补回。**

## 4. 新闻 / 文案 / 性能
- 新闻四表：雨林12、沙漠各10、璃月战后20、珊瑚宫10，均挂国策 `completion_reward`；改完跑 `_desc\check_news_anchors.py`。
- Darwin：`_desc\darwin_pass.py`（`fit(200,400)`，`--check` 只读）已覆盖 6 个 loc 文件；越界0／破折号0。备份 `_desc\backup_darwin\`。
- 性能/工具：`wrap_hidden_effects.py`（R1 调用点 + R2 效果体 `hidden_effect` 包裹，`--apply` 门控、幂等、自动备份）、`verify_wrap.py`（内存预演结构校验）、`count_visible_mech.py`、`scan_effect_surface.py`、`analyze_effect_bodies.py`、`optimize_tier_chains.py`、`scan_modifier_packs.py`。
- 第四轮新增：`fix_axis_tooltips.py`（轴指数提包外 + 生成 `custom_effect_tooltip`）、`audit_dm_refs.py`（动修引用率审计）、`cut_dm_from_focus_path.py`（≤10% 死规矩落地）、`restore_modifiers.py`（误删修正还原）、`check_tooltip_keys.py`（tooltip 键存在性审计）、`list_remaining_dm.py`（已知崩溃未修）。**`converge_modifiers.py` 已停用**（顶部 `sys.exit(0)`，结论被用户否决）。
- 第五轮新增：`check_loc_bom.py`（loc BOM/裸 LF 审计，`--fix` 可修）、`diag_nat_loc.py`、`inv_info_boards.py`（只读盘点，出 `_inv_boards.json`）、`build_info_boards.py`（Info_Board 生成器主脚本，dry-run/`--apply`）、`check_info_boards.py`（desc↔scripted-loc↔loc 三向校验，忽略 `GFX_*` 精灵名）。

## 5. 遗留
- 未实测：`end_puppet` 对 `autonomy_*`、`create_country_leader`、动修是否真挂、四组国策横排／档位逐档变化／面板与生效修正一致／决议门槛是否挡住；`hidden_effect` 是否如预期静音 tooltip。
- **NAT 缺 `on_actions` 挂载文件（待用户定夺）**：NAT 动修**不是**休眠的——`NAT_Abyss_Add/Sub_*`、`NAT_Grace_Add/Sub_*` 每个宏内部都调 `NAT_Abyss_Sync`/`NAT_Grace_Sync`，且国策/决议大量调用（形式 `NAT = { NAT_Grace_Sub_5 = yes }`）。真正**零调用者**的是三个**时间漂移**效果：`NAT_ABY_Monthly_Tick`（深渊侵蚀度自然漂移）、`NAT_GRACE_Monthly_Tick`、`NAT_V3_Monthly_Tick`（燃素天网自持／大灵回应度／未封印裂隙按月侵蚀）⇒ 这些「每月」机制**永远不会跑**（既有问题，见 `NAT_剧本TNO版实装报告.md:155`）。修法＝新建 `common/on_actions/NAT_Neo_on_actions.txt` 挂 `on_monthly`，但会改变平衡，须用户点头。
- 真悬空 `custom_effect_tooltip` 键 5 个（均属**缺 loc 的遗留块**，非本仓新引入）：`DOT_Backup_decisions.txt` 的 `LYY_qiming/ningguang/shenhe_support_increase_tooltip`；`LYY_decisions.txt` 劳动法块（`LYY_Ganyu_Labor_Law`）的 `LYY_people_satisfaction_increase/decrease_tooltip`；`LAW_decisions.txt`（`LAW_HigherResist_of_LAW`）的 `LAW_High_Resist_Here`。已修为 `_Add_5` 的 1 处 NAT 笔误见下。
- **MOD 内疑似「重复读取」源（待用户定夺，未动）**：① `Daybreak of Teyvat Gamma Version\.backup\`（手放，含 `map/buildings.txt`+`unitstacks.txt`+地图 jpg，HOI4 只读顶层 `map/`，实际不会被读，但按「备份出 MOD」口径应外移）；② `common/decisions/DOT_Backup_decisions.txt`（手命名备份，3 条决议唯一，但其**类别 `LYY_Ganyu_Mortal_Adepti_Struggle` 与 `categories/LYY_decision_categories.txt:221` 重复声明**）。
- 审计脚本 `check_tooltip_keys.py` 的坑：本仓 NAT 文件有**行内**注释残留 `custom_effect_tooltip = GUN_Effects_are_Hidden # custom_effect_tooltip = NAT_*_Tooltip`，必须**从每行第一个 `#` 起整段剥掉**再匹配，否则误报 234 个「未定义」。
- **校验脚本断言要跟架构走**：删掉旧机制面板后，`_civilwar/verify_requirements.py`（原断言「机制面板类别 ≥12 / 档位条目 ≥168」）与 `_san/verify_san_pw.py`（原「机制面板条目 14 条」）会**假报红**；第五轮已改为断言「旧类别已移除 + 六派内战 Info_Board 齐全 + desc 含档位名/修正/共振名/共振修正」。凡删面板/改架构，务必同步改这类断言。
- 旧33决议 25 个 `GFX_decision_*` 图标无声明；`events/LYY_*` 注释编码损坏；`add_tech_bonus: Unknown technology category` 待处理。GUN 吞并 state 已禁用；奇观 Palace 不显示；模型 BUG 待实测；VAN 未做。范围外残留：`DOT_Backup_decisions.txt` 的 `LYY_Ganyu.61`、`Ilyich_Character.118`、`LAW.1–17`、`Teyvat_News.17`、`dragonspine.97`（悬空合计 14 条，均为原版/范围外）。
- **LYY tag 限定（10-17 已按用户口径收紧）**：不是「没有 available 限制」——树头 7 tag 白名单 + focus 级 tag 条件一直都在，44 个备份纵向比对从未出现「748 个全带 tag」的状态，也未发现任何备份回滚删过 tag 行（当前文件与 `backup_lyyeff_20261016_185838` 的 140 行 diff 全是效果名修正与 `hidden_effect` 包裹，`tag`/`available` 差异 0 行）。10-17 按用户口径「只给少数关键国策加限制、抄内战根手写的 available」补了 **18 个路线关键国策**（每派 3 个：路线分叉点 + 两终局），`always = yes` 624→606；剩余 606 个按须弥既定口径保持放开（须弥 888 个里也只 gate 18 个）。诊断脚本 `_diag_lyy_avail.py`／`_diag_lyy_tagfocus.py`／`_diag_lyy_avail_hist.py`／`_diag_lyy_forks.py`／`_diag_lyy_ids.py`（均只读）。
