# MEMORY.md —— 提瓦特黎明（DOT Gamma）项目备忘
> 通用语法/排查见技能 `hoi4-mod-bug-triage`；方法论/工具链/路径见 `DOT_制作手册.md`；逐轮细节见同目录 `2026-10-*.md`。本文件只记项目特有口径。

## 0. ⭐ 铁律
- 禁恢复/回滚，一律在现状上加工；**禁 git 提交**；禁「注释掉问题代码」；中文注释只写中文不写 ID。
- 旧 loc 全不删；`ABY_focus.txt` 不动；focus 文件必须保留 `focus_tree` 头部。
- **数量一律为下限**；剧本直接改原文件，禁建 `_v2`。事件 desc 200–400 字、新闻 desc 200–400 字（去空白计）。**破折号一律不用**。⚠ 生成阶段补长下限取 **206**（`style()` 后置会削 2-5 字）。
- **内容实装**：新增剧本的事件/精神/loc/决议/类别/动修/宏/`on_actions` 一律**并入同名 `<国>_*` 文件**，禁另起 `X_Y_Desert_*` 平行文件；国策树插进该国 focus 文件内。**新闻一律由国策或事件的 `completion_reward` 触发**（`news_event = { id = NS.n days = 1 }`），禁写按日期批量发射的 `*_News_Begin` 宏。详见 `.skills\DOT_AI_指令.md`「内容实装铁律」。
- **一个 tag 组只写一棵 `focus_tree`**：同国多棵树是「评分择一」不是并列显示（10-16 事故：4 棵只看到 1 棵）。让 B 排在 A 右边＝同一棵树里把 B 整块绝对 x 平移到 A 之外（范例 `LYY_Neo_Focus.txt`）。**每个块每个节点都要 `available = { tag = <归属> }` —— 「主国」那块也要**，只给新块加、主块留 `always = yes` 会让别国能点主国国策并搅乱主国机制（10-16 深夜事故：雨林 324 个全漏）。触发器统一小写 `tag`。
- **新增决议一律带 `has_completed_focus` 门槛**，取**分叉点之前的通用国策**（免锁死互斥路线）；另配 `visible = { has_country_flag = <剧本旗标> }`。
- **机制修正按国策分阶段赐予**：`*_Init` 只置初值；`*_Tier_Refresh` 先卸全部档位再挂唯一匹配的一档，轴宏末尾调它（轴宏只被国策 `completion_reward` 调用）⇒ 档位随国策逐档解锁。每档另加**只读面板**（`visible`=该档 enable 条件，`available = { always = no }`，`cost = 0`）显示生效修正。
- 只用 5 种基础意识形态，**禁子意识形态**；`set_cosmetic_tag` 按意识形态上色。
- 机制效果用 decision 不用 action；`on_actions` 只许开局初始化+档位/保活同步，**内容必须包在 `effect = { }` 里**（裸写 `every_country` 会让整份文件作废且静默）。角色表=`hoi4lint\icon_gen\role_nation.py::WIKI_ROLE_TABLE`。图标 v7 原版链路+v4 命名，素材 `.skills\bwiki\icons3`。
- 文案「十条规则」见 `.skills\Darwin Skills.md`（只改风格不动事实）。跨表全局 id（变量/动修/精神/决议/类别/宏）必须带层别标记。

## 1. 环境
- Python=`…\.workbuddy\binaries\python\envs\default\Scripts\python.exe`；Bash 优于 PowerShell（中文硬编码进 UTF-8 脚本）。
- 脚本无 BOM+CRLF；loc `.yml` 必须 BOM+CRLF 并字节自检。focus/ideas/events 用 tab，loc 键前导一空格。Edit 同文件并行会互相覆盖⇒串行发。动手前先备份。
- MOD 根 `…\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version`；脚本+备份 `C:\Users\XIANGZIYUAN\hoi4lint\`（原版/日志路径见手册）。
- 生效 `replace_path`：history/*、bookmarks|resources|ai_strategy*、events、decisions|countries、strategicregions|supplyareas；⚠ `national_focus`/`continuous_focus`/`gfx` 不在内（同名空文件是屏蔽开关）。
- 工作区是「活的」：会被外部副本整份覆盖⇒任何「我做过的事」先 grep/ls 核实。`game.log` 报 Loaded 11507 provinces 才是本 MOD。

## 2. HOI4 语法（1.19.3 取证）
- modifier 两套 loc：`_<modifier>_tt` 与 `MODIFIER_<大写>`。**无** farm/power_plant/radar_building/reconnaissance 类修正，也**无** `army_defense_factor`/`division_attack_factor`/`navy_attack_factor`/`factory_output`/`manpower_factor`/`corruption`；英式 `army_defence_factor`，农业用 `monthly_population`。
- `annex_country={target=X transfer_troops=yes}`；脚本 `set_autonomy` 用 `autonomy_state`，history 用 `autonomous_state`。决议 `icon=<裸名>`→`GFX_decision_<裸名>`，分类→`GFX_decision_category_<裸名>`。
- 原版无 `common/effects`/`common/triggers`；`hoi4lint\vanilla_modifiers.json`(637) 是新效果硬约束。判活看 `add_dynamic_modifier` 是否被调用；`on_actions` 跨文件叠加，挂载缺失是静默的。**`on_startup`/`on_monthly` 内容必须写在 `effect = { }` 内**（`on_startup = { effect = { every_country = { … } } }`），否则报 `Unexpected token: every_country` 并整份文件作废（10-16 事故，机制从没初始化过）。
- 决议 `visible` 缺省是「一直可见（灰着）」；不想让玩家看到就写 `visible = { <条件> }`。动态修正 `remove_dynamic_modifier = { modifier = X }` 可用（先卸后挂来切换档位）。

## 3. NAT 纳塔
- 州61/六族43/ABY6；六族 `NCP/NCE/NPS/NSC/NFF/NMN`，自治州 `autonomy_NAT_State`。变量 `NAT-ABY-Index`(40)/`MVK-Prestige-Index`(50)/`NAT-War-Index` 名不可改、必走 `NAT_Abyss_Add/Sub_*`、`NAT_Grace_Add/Sub_*`。
- 四阶段：`autonomy_puppet`→只转 `autonomy_NAT_State`→恩情>79 才 `annex_country`→恩情<19 脱离宣战；**先 `end_puppet` 再宣战**；分宗不改色⇒禁 `set_cosmetic_tag`。国策171/决议69/事件88/精神205；`nat_verify_six_tribes.py`。

## 4. LYY 璃月内战（10-14）
- 六方↔意识形态（勿改）：KQP刻晴=communism｜LYY凝光=democratic｜GYP甘雨=neutrality｜SHP申鹤=fascism｜YLH公子=fascism/neutrality｜CYG蓝砚=genshin；每派 2 路线共 12，BRF 唯一野牌；双轴变量名不可改，六块 x 区间两两不交（见 10-14 日志）。
- 新增 cost 6.0、原树 118 个 7；战后层 y∈[22,34]、块标记 `# == <TAG> POST-WAR focus tree BEGIN/END ==` 幂等、id 带 `PW`。合计 国策630/决议170/事件672/精神154，生成器 `_civilwar\cw_engine.py`。
- **10-16 晚口径**：170 条决议全加 `has_completed_focus`（内战决议→各派 `*_CivilWar_*` 根，战后决议→各派 `*_PW_*` 根，共 12 个根 id；`build_decisions()` 的 `gate=F["ROOT"]`——`layout()` 返回的是**字符串**不是列表，`[0]` 会截成 `K`）；每派 2 个只读机制面板类别（共 12 类 / 168 条）；`*_Init` 只置初值、`*_Tier_Refresh` 先卸后挂（`Tier_Refresh = yes` 216 处）；`on_actions` 内容包进 `effect = { }`。`verify_requirements.py` 新增 (f) 段（门槛/面板/分阶段）并把新闻改从 `events/LYY_CW_news.txt` 取（支持 `days = 1`）。
- 要点：决议顶层块名==类别 id；相对坐标 `x/y`=「绝对−前置绝对」；长文本 loc 写 `\n`；事件选项禁写 `ev=<自身id>`。

## 5. SAN 珊瑚宫战后（10-14 夜）
- tag SAN 对 INA；三终局 御神归鸣 fascism／万岛共和 democratic／御建承继 neutrality，分叉 `SAN_PW_The_Crossroads`；机制双轴 `SAN-Mandate-Index`(40)／`SAN-Deep-Index`(30)，阈值 20/40/60/80，14 动修。国策100/决议20/事件100(`SAN_PW.20000–20099`)/新闻10/精神10；`_san\san_pw_engine.py`，`verify_san_pw.py` 全绿。
- **10-16 晚改造（走 `_san\patch_pw_stage.py`，勿直接重跑引擎）**：20 条战后决议全加 `has_completed_focus` 门槛（按主题映射到分叉点之前的通用国策，避开 A/B/C 三路线）+ `visible = { has_country_flag = SAN_PW_Active }`；`SAN_PW_Init` 改为只置初值，新增 `SAN_PW_Tier_Refresh`（先卸 14 个档位再挂唯一匹配的一档），轴变量改动处插 `SAN_PW_Tier_Refresh = yes` **76 处**（`SAN_Neo_Focus.txt` 66 + `SAN_Neo_decisions.txt` 10）；新增只读 `SAN_PW_Mechanism` 面板 14 条；补上全库原先缺失的 3 条战后决议类别 loc。改完 `verify_san_pw.py` 全绿（新增门槛/面板断言）。

## 6. SUM 须弥（10-15）
- 雨林：旧 `SUM_Focus_II.txt`(80) 退役成注释存根；新 `SUM_Neo_Focus.txt`(id `SUM_Neo_Focus_Tree`)，书签 `3_The_Traveler.txt` SUM 起始改 `SUM_PRO_Dawn_of_Sabzeruz`×3。国策324(5簇)/决议107(7类)/事件324/新闻12/精神106/动修14/loc2448；id 全 `SUM_` 起头；三路线↔五意识形态（`PRO_The_Choice` 分叉）；机制双轴 `SUM-Oracle-Index`(20)／`SUM-Canon-Index`(70)+`SUM-Genesis-Index`(10)；`_sum\sum_engine.py`，`verify_sum.py`+`extra_check.py` 全绿。
- 沙漠三国（10-16 晚定版，与雨林**同一棵** `focus_tree`）：`SGD 镀金沙漠`/`SDH 哈德拉玛维特`/`SGS 沙丘腰带`。`SUM_Neo_Focus.txt` **只有一棵** `focus_tree`（`id = SUM_Neo_Focus_Tree`，`country` 内 `OR = { tag=SUM tag=SGD tag=SDH tag=SGS }`）；绝对 x：雨林 [0,62]、SGD [70,138]、SDH [146,214]、SGS [222,290]（＝实装在雨林**右边**）。`desert_engine.focus_tree_text(xoff=)` 不自带头尾、只出 `# ======== <TAG> 国策（…右侧）========`…`END` 块；`xoff = 雨林 max x + 8`，逐国再追加「本国宽度 + 8」。；每节点 `available = { tag = <归属 tag> }`（**小写 `tag`；雨林块也必须有，10-16 深夜补齐**）。片段 `desert_trees.inc` 已改名 **`inc_focus.txt`**。
- 每国 6 簇：PRO 序章→IND 独立（`end_puppet`+`leave_faction`+双向 `puppet_wargoal_focus`）→RA/RB/RC 三互斥路线（门槛 `has_completed_focus=<TAG>_IND_Declaration`）→WAR 开战须弥（`declare_war_on={target=SUM type=annex_everything}`）。每国 国策188/事件188/决议21(5类)/精神21/新闻10/动修14。双轴 SGD `SUM-SGD-Deshret-Index`(30)/`…-Eremite-Index`(60)、SDH `…-Floral-Index`(40)/`…-Storm-Index`(55)、SGS `…-Pari-Index`(45)/`…-Relic-Index`(50)。
- **10-16 实装重构（用户口径）**：沙漠产物**全部并入 `SUM_Neo_*` 同名文件**，原 `SUM_Neo_Desert_*` 10 个文件已删。`desert_engine.py` 只产片段 `_desert\inc_*.txt`（trees/events/news/ns/ideas/decisions/categories/dynmods/effects/onstartup/onmonthly/loc），由 `sum_engine.splice_desert()` 拼接；`build_ideas/build_onactions` 带 `extra_*` 参数把沙漠内容塞进同一个 `ideas = { country = { … } }` 与同一个 `on_actions = { … }` 块。
- **新闻禁止按日期批量发射**：`NEWS_ANCHOR`（`desert_cfg.py` 三国各 10 条、`sum_cfg.py` 雨林 12 条）把每条新闻挂到指定国策的 `completion_reward`：`news_event = { id = <NS>.<n> days = 1 }`，锚点两两互斥保证至多一次。`*_News_Begin` 宏已从 SUM/沙漠引擎、`LYY_CW_effects.txt`、`SAN_Neo_effects.txt` 全部删除。
- **10-16 晚口径**：雨林 107 条决议按 7 类别门控（`DEC_GATE`）、沙漠 63 条按国别 5 类门控（`DEC_GATE_BY_TAG`，门槛全取全路线可达的 PRO 支线根 / `IND_Declaration`）；`SUM_Neo_Init` 只置初值、`SUM_Neo_Tier_Refresh` 先卸后挂（雨林轴宏 `SUM_Neo_A/B_Up` 被调 257 次、沙漠 48 个 `SUM_Neo_S*_A/B_Up_N` 各国策调 175 次，末尾都调它）；新增 4 个只读机制面板共 56 条；`on_actions` 内容包进 `effect = { }`。
- 合并后合计 国策 888／事件 888／新闻 42／精神 169／动修 56／决议 174（含 56 面板）／loc **6408** 键。`verify_desert.py`（**164 项**）+`verify_sum.py`（含 desc 字数与破折号）+`extra_check.py`+`check_gfx.py` 全绿。
- **10-16 深夜：四块互为独占**。雨林 324 个 focus 原为 `available = { always = yes }` ⇒ SGD/SDH/SGS 能点到须弥雨林（会误跑 `SUM_Neo_Init`）。修法：`sum_engine.py` 雨林分支改 `available = { tag = %s } % CFG["TAG"]`，`desert_engine.py` 的 `TAG =` 改小写 `tag =`；产物 466,479 → **465,558 B**，`tag = SUM`×324 / SGD×188 / SDH×188 / SGS×188，`always = yes` 与 `TAG =` 均 0 处。**只重建国策相关的 2 个文件**：新脚本 `_sum/regen_focus_only.py`、`_desert/regen_inc_focus.py`（先 diff 后 `--apply`，自动备份）——**禁重跑 `sum_engine.main()`/`desert_engine.main()`**（会把 loc 重新生成，冲掉 Darwin 改写）。

## 7. 遗留 / 未修
- 多数剧本未进游戏验证：`end_puppet` 对 `autonomy_*`、跨作用域 `check_variable`、`create_country_leader`、动修是否真挂上。
- 旧33决议中 25 个 `GFX_decision_*` 图标全库无声明（只新增不改旧）。`events/LYY_*` 中文注释编码损坏(U+FFFD)。error.log `add_tech_bonus: Unknown technology category` 待处理。
- GUN 吞并他国 state 已 `#` 禁用。奇观 Palace 不显示（10-14 未闭环）。模型 BUG（factory/胡桃/可莉）待实测。VAN 剧本未做。
- `_civilwar\verify_requirements.py` 与 `_san\verify_san_pw.py` 的旧失败项**10-16 已清零**（cost 6.110 笔误、战后横坐标判据过严、合并后计数口径、白名单漏收 10 个原版修正名 `vanilla_modifiers.json` 637→647）。修法见 10-16 日志第八、十一节。
- **LYY 有与须弥同类的「未限定 tag」问题，10-16 深夜核实但未改**：`LYY_Neo_Focus.txt` 748 个 focus 的 `available` 全是 `always = yes`，七方共用一棵树却无派系归属限定 ⇒ KQP 能看到并点到 GYP/SHP 等派的国策（连带跑它们的 `*_Init`）。须弥已在第三轮修掉同类问题；LYY 是否照此收紧**待用户定夺**（若收紧：原树段给 `tag = LYY`、六方块各给本国 tag，`cw_engine.py` 与 `verify_requirements.py` 需同步改）。已记进 `.workbuddy/LYY_CivilWar_Design.md`「已知差异」。
- **10-16 晚待实测（静态校验证明不了）**：单棵树上四组国策是否横向排开且各国只能点本国段；档位是否真的随国策完成逐档变化；只读机制面板是否只在对应档位出现且百分比与生效修正一致；决议是否在完成门槛国策前点不动；`end_puppet` 对 `autonomy_*` / `declare_war_on` 的实际表现。

## 8. 文案改写（Darwin 十条，10-16 全量跑过）
- 工具：`_desc\darwin_pools.py`（LYY/NAT/SAN/SUM 四套续写句池）+ `_desc\darwin_pass.py`（`style()`/`lint()`/`fit(lo=200,hi=400)`；`--check` 只读体检，`main()` 有 `__main__` 守卫）。
- 覆盖 6 个 loc 文件：`LYY_CW_`（键5016/desc692/[200,230]）／`LYY_Routes_`（794/103/[200,400]）／`LYY_Script_`（2168/79/[200,399]）／`NAT_Neo_Script_`（1588/92/[200,364]）／`SAN_Neo_Script_`（1836/293/[200,326]）／`SUM_Neo_l_simp_chinese.yml`（6288/930/[200,240]）。**越界 0、破折号 0、残留套话 0**，键集合与改写前备份逐条一致。
- 关键口径：**破折号禁**（`_DASH` 含 `—–―─－`）；`_OPENERS_MID` 处理句中套话（`但总的来说` 等）；`fit()` 对每个候选句先跑 `style()`，防止补充句把套话带回来。备份在 `_desc\backup_darwin\<stamp>.<file>`。
- **10-16 晚补丁**：`style()` 会削 2-5 字，导致 23 条事件 desc（雨林 11 + 沙漠 12）落到 196–199。已按主题逐条补一句收尾（`_desert\patch_desc_len.py`，幂等），并把生成器 `_grow(..., lo=200…)` 抬到 **206**（`_sum\sum_data.py` 2 处、`_desert\dpool.py` 1 处、`_desert\desert_engine.py` 2 处）。只读盘点用 `_desert\probe_sum_desc.py`。

## 9. 新闻锚点表（10-16 全库统一）
- 四张表，全由国策 `completion_reward` 里的 `news_event = { id = <NS>.<n> days = 1 }` 承载：须弥雨林 12 条/16 锚（`sum_cfg.NEWS_ANCHOR`）、沙漠三国各 10 条（`desert_cfg.NATIONS[*].NEWS_ANCHOR`，SGD 10 锚 / SDH 11 / SGS 13）、璃月战后 20 条/120 锚（`_civilwar\data_pw_news.py::PW_NEWS`）、珊瑚宫 10 条/10 锚（`_san\san_pw_engine.py::SAN_PW_NEWS`）。
- 只读体检 `_desc\check_news_anchors.py`：把四张表与 MOD 里国策文件实际写着的锚点逐条比对，**全一致**。改锚点后必须跑它。
- `sum_engine.py` 与 `desert_engine.py` 是权威生成器（改完要重跑）；`cw_engine.py` 已回填锚点与 `PW_NEWS`；⚠ `san_pw_engine.py` 已标注为「勿直接重跑」（其 `SAN_PW_*` 正式路径早已并入 `SAN_Neo_*`），要改就走 **`_san\patch_pw_stage.py`**（对 MOD 现状定点补丁，幂等；含「先删旧键再整体重写」的 loc 处理和一个 `re.split` 吞 ` = {` 的坑，已改为大括号配对）。
