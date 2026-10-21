# MEMORY.md —— 提瓦特黎明（DOT Gamma）项目备忘
> 语法/排查见技能 `hoi4-mod-bug-triage`；工具链见 `DOT_制作手册.md`；各国设计见 `.workbuddy\*_Design.md`；逐轮细节见 `2026-10-*.md`。本文件只记铁律与当前口径。

## 0. 铁律
- 禁恢复/回滚、禁 git 提交、禁「注释掉问题代码」。中文注释只写中文不写 ID。旧 loc 全不删；`ABY_focus.txt` 不动；focus 文件保留 `focus_tree` 头。数量一律下限；直接改原文件，禁建 `_v2`。
- **修 bug 只修不删**：loc 同键重复不许删行（把「名称+\n§g描述」拆成 `key`/`key_desc`、空值行补正文、改行尾注释），删行＝丢作者内容，用户会退回。颜色闭合用状态机（`§X` 开／`§!` 关）判，数 `§` 奇偶是错的。
- 事件/新闻 desc 200–400 字（去空白），生成下限取 206（`style()` 会削 2–5 字）。禁破折号（`—–―─－`）。
- 新增事件/精神/loc/决议/类别/动修/宏/`on_actions` 一律并入同名 `<国>_*` 文件。新闻必须由国策/事件 `completion_reward` 触发（`news_event = { id = NS.n days = 1 }`），禁按日期批量发射。`add_namespace` 写在事件文件自身首部。
- **focus 的 tag 限定＝树头白名单 + 少数关键国策**（LYY 30／SUM 18）；树头 `country = { or = { tag = … } }`，focus 级只给分叉点/终局写 `available`；缺省已删净（`strip_avail_always.py`）。
- 新增决议必须带 `has_completed_focus` + `visible = { … }`（`visible` 缺省＝一直可见灰着）；门槛国策要按绝对深度分层遍布全树（`map_sum_decisions.py`）。
- 机制修正分阶段：`*_Init` 置初值并调一次 `*_Tier_Refresh`；`*_Tier_Refresh` 先卸全档再挂唯一档；轴宏 `<M>_A/B_Up_N` 只改变量；档位保鲜由 `on_actions` 的 `*_Sync`（`on_daily`）负责；每档配只读面板（`available = { always = no }`、`cost = 0`）。
- **≤10% 的国策/决议可以改 `dynamic_modifier`**（现状 0.4%＝11 个机制里程碑）。冗余＝同一组修正被大量 `effect xxx = yes` 反复引用，不是「一个决议里并列多条不同修正」。
- **轴指数变化必须可见**：轴 `add_to_variable` 提到 `hidden_effect` 外，逐条配 `custom_effect_tooltip`（`§G加N§!`／`§R减N§!`）。
- **Tooltip 卫生**：`hidden_effect` 只包 `*_Tier_Refresh`/`*_Sync` 正文 + 连续 ≥2 行纯变量/旗标段；轴宏不整体包；`custom_effect_tooltip` 留包外。审计前先剥 `#…`。
- **备份一律放 MOD 外**：`C:\Users\XIANGZIYUAN\hoi4lint\_backup_*`。
- **loc 必须带 UTF-8 BOM**（缺 BOM 会被整份静默丢弃，症状＝某国本地化全空）⇒ 每轮跑 `check_loc_bom.py`。loc 里禁止泄漏变量 ID（`fix_var_labels_loc.py`）。
- Info_Board＝空决议类别（`visible_when_empty = yes`）+ `priority = { base = 100 }`（不是 `priority = N`），`_desc` 按轴拼 `§Y轴名：§![?VAR]` + 档位名 + 修正。
- 只用 5 种基础意识形态；`set_cosmetic_tag` 按意识形态上色。`on_actions` 内容必须包在 `effect = { }`。文案守 `.skills\Darwin Skills.md` 十条。

## 1. 环境
- Python=`…\binaries\python\envs\default\Scripts\python.exe`；Bash 优于 PowerShell。脚本无 BOM+CRLF；loc `.yml` 必须 BOM+CRLF；focus/ideas/events 用 tab；`.asset` 无 BOM+CRLF；**原版 txt 多为无 BOM+LF**（复制时保持）。Edit 同文件并行会互相覆盖⇒串行。动手前先备份。
- 生效 `replace_path`：history/{countries,states,units}、bookmarks、resources、ai_strategy*、strategicregions、supplyareas。**`decisions`／`national_focus`／`gfx` 不在内**。⇒ 改原版决议只能在**同路径整份复制**进 MOD 再改（mod 同路径文件替换原版文件）；同目录不同名的新文件是「重复 id」，不可靠。
- 工作区「活的」，会被外部/并行会话整份覆盖 ⇒ 改完隔几分钟复核；与记录不符先取证别覆盖。`game.log` 报 Loaded 11507 provinces 才是本 MOD。

## 2. HOI4 语法（1.19.3）
- modifier loc：`_<modifier>_tt` 与 `MODIFIER_<大写>`。无 farm/power_plant/reconnaissance/`army_defense_factor`/`factory_output`/`manpower_factor`/`corruption`；英式 `army_defence_factor`，农业用 `monthly_population`。
- 有 tooltip 的效果：`add_dynamic_modifier`/`remove_dynamic_modifier`、`add_ideas`/`remove_ideas`、`add_stability`；无 tooltip：`add_to_variable`/`set_variable`/`set_country_flag`。
- 前置：多个 `prerequisite = { }` 块是 AND，一块内多条 `focus =` 是 OR。
- 决议 `icon=<裸名>`→`GFX_decision_<裸名>`，分类→`GFX_decision_category_<裸名>`；空分类要显示须 `visible_when_empty = yes`。trigger 块内 `always = no` 可让 available/visible 恒假（隐藏原版条目用）。
- **idea 图标 `picture` 必须裸名**（游戏自动拼 `GFX_idea_`；写成 `GFX_idea_X` 会去取 `GFX_idea_GFX_idea_X` → 空白）。MIS 的 `icon =` 才写完整 sprite 名。原版 6153 条 `picture` 有 6131 条是裸名。
- **loc 硬规则**：只认小写 `\n`（`\N` 原样显示）；`§b` 是合法深蓝码（原版在用），畸形 `§！`/`§。`/`§，`/尾部裸 `§` 都要补 `!`；同键重复＝**后加载者胜**（删被覆盖的早行不改显示）；文件必须在 `localisation/<语言>/` 且带 BOM + `l_<语言>:` 头，放 localisation 根目录不加载。
- **解析 `.gfx` 必须 `re.I`**：属性名 `textureFile`（大写 F）与 `spriteType`（小写 s）大量并存，且要按花括号配对切块；用 `name…texturefile` 的正则近似会漏块、误报精灵缺失。
- `annex_country={target=X transfer_troops=yes}`；`set_autonomy` 用 `autonomy_state`，history 用 `autonomous_state`。
- `hoi4lint\vanilla_modifiers.json`(647) 是新效果硬约束；`on_actions` 跨文件叠加，挂载缺失静默。一颗 `hidden_effect` 只隐藏 tooltip、不改行为。
- **兵模**：`entity = { clone = "源" name = "<TAG>_<infantry|artillery|cavalry>_<0..3>_entity" }`，每 tag 12 个自动生效。**clone 不能覆盖 attach**（Amber 炮兵写死安柏炮手、骑兵写死安柏骑手）⇒ 每角色自建 `<角色>_artillery_entity`（炮手＝自己步兵），tag 只 clone 本阵营。悬空校验按 clone 值反查 name 集合。
- **三件套**：`*_sabre_infantry_rider_entity`＋`*_sabre_cavalry_rifle_combined_entity`（`infantry_cavalry_horse_mesh`，`Saddle_Node`=骑手，0.65）＋`*_sabre_cavalry_entity`（`infantry_cavalry_horse_frame_mesh`，1.2）；炮兵＝`frame_artillery_mesh`+`artillery_gun_entity`+`infantry=<自己>_infantry_entity`（1.0，`artillery_gun_entity` 是原版须白名单）。**步炮兵段 sabre 节点 `Right_Hand_node_4`/`mid_back_node_2` 已删，骑兵段 `Right_Hand_node`/`mid_back_node` 保留。**
- **MIO 图标按 tag 所属地区**：`GFX_idea_<地区>_*`（MOT/LYY/INA/SUM/FON/NAT/SNE/NDK/PRI），判不出（ABY、通用组织）走 `DOT` 池；组织→tag 读 `allowed` 的 `tag`/`original_tag`/`Is_X`，先剥 `NOT = { … }`；原图标已含本地区 token 的保留。
- **角色模型转换**：`肌`/`肌2` 是**皮肤层（四肢）**，不是叠加装饰，绝不能当重合层剔除（纳西妲缺手臂/腿的根因）；真正的叠加层是 `照れ/袜s/翼+/髮+/披肩s/裙+/白目/瞳/星目` 等。

## 3. 各国口径
- **NAT**：六族 NCP/NCE/NPS/NSC/NFF/NMN；变量 `NAT-ABY-Index`(40)/`MVK-Prestige-Index`(50) 不可改名。四阶段 `autonomy_puppet`→`autonomy_NAT_State`→恩情>79 吞并→恩情<19 脱离宣战。国策171/决议69/事件88/精神205。18 个分宗决议带 `ai_will_do`（傀儡 +100，`nat_dissent_ai.py`）；分宗决议的 `visible`/`available` 已加 tag 门控（三阶段＝`or = { tag = NAT, tag = <族> }`，Recapture 只给 NAT，否则部族会看到「对自己宣战」）。
- **LYY**：六派 12 路线；战后层 y∈[22,34]、id 带 `PW`、块标记 `# == <TAG> POST-WAR focus tree BEGIN/END ==`；170 决议全带门槛；六派内战 + 战后各 1 个 Info_Board。生成器 `_civilwar\cw_engine.py`。tag 限定 30 个（清单见 `2026-10-19.md`，以 `_diag_lyy_forks.py` 为准）。
- **SAN**：三终局，分叉 `SAN_PW_The_Crossroads`；双轴 `SAN-Mandate-Index`(40)／`SAN-Deep-Index`(30)。改走 `_san\patch_pw_stage.py`。
- **SUM**：雨林 `SUM_Neo_Focus_Tree`（起始 `SUM_PRO_Dawn_of_Sabzeruz`），沙漠 SGD/SDH/SGS 同树右侧。合计国策888／事件888／决议170／loc6602；门槛 162 个不同国策、深度 y3–y33（`map_sum_decisions.py`）。4 个 Info_Board。
  **结构**：`SUM_PRO_*` 是**共享序章**（d0 花神诞祭 → d1–d3 八条分支 → d4 `SUM_PRO_The_Choice` 前路的抉择）；之后 ST 圣树／RP 共和／GT 造神 三条路线互斥（`available = { has_completed_focus = SUM_PRO_The_Choice }`），`SUM_PL_*` 沙与林独立簇 d0–d10。
  **生成器纪律**：只重建国策用 `_sum/regen_focus_only.py`、`_desert/regen_inc_focus.py`，禁重跑 main()；重跑会把前置拆回多块 AND 并冲掉 `ai_will_do`，需补跑 `merge_sum_prereq.py` + `set_ai_weights.py`。
  **10-20**：序章 7 个负面精神按深度逐个 `remove_ideas`（`sum_remove_negative_spirits.py`）；`SUM_God_creation_plan01` 不删（草神满意度决议在 01/02/03 之间 swap）。

## 4. 工具链
- 结构/文案：`wrap_hidden_effects.py`、`verify_wrap.py`、`fix_axis_tooltips.py`、`audit_dm_refs.py`、`restore_modifiers.py`、`check_tooltip_keys.py`、`_desc\darwin_pass.py`（`--check` 只读）、`_desc\check_news_anchors.py`、`bug_scan.py`。
- loc/面板/国策：`check_loc_bom.py`、`fix_var_labels_loc.py`、`inv_info_boards.py`、`build_info_boards.py`、`check_info_boards.py`、`strip_avail_always.py`、`merge_sum_prereq.py`、`set_ai_weights.py`、`gate_lyy_route_focuses.py`、`map_sum_decisions.py`、`sum_remove_negative_spirits.py`。
- 兵模：`bind_unit_models.py`、`fix_artillery_entities.py`、`rebuild_entities_law.py`、`dedup_entities.py`、`strip_infantry_sabre.py`、`verify_entities2.py`、`reicon_mio_by_region.py` + `verify_mio_icons.py`、`nat_dissent_ai.py`。
- 模型：技能 `hoi4-pmx-to-mesh`（`vysna_build.py` 是唯一构建器）；本 MOD 的补丁版 `hoi4lint\nah_build.py`（+`rebuild_nahida.py`，可保留 `肌2`、带可选手臂重定向 `ARM_RETARGET`，默认关）。
- 胜利点：`vp_apply_liyue_sumeru.py`（Gamma→Beta，一 Beta 州一点）、`vp_apply_inazuma.py`（**Beta→Gamma**，一 Gamma 州可多点）、`verify_vp_*.py`、`vp_render_gamma.py` / `vp_render_inazuma.py`。**两版省号不可互译**，桥只能靠州名 + TPS（锚点 141，LOO 中位 19px）。**写盘必须按 gid 聚合**：逐 Beta 点遍历会让同一州被处理多次，第二次 `copy2` 把已写文件当备份源，备份被污染、单州只落 1 点。
- 一律 dry-run 先行、`--apply` 才写、幂等、自动备份出 MOD。

## 5. 遗留
- 未实测：`end_puppet` 对 `autonomy_*`、`create_country_leader`、动修是否真挂、档位逐档变化、决议门槛、兵模是否上屏、`hidden_effect` 静音。
- **NAT 缺 `on_actions` 挂载（待定夺）**：`NAT_ABY/GRACE/V3_Monthly_Tick` 零调用者 ⇒ 每月机制不跑；挂 `on_monthly` 会改平衡，须用户点头。
- 真悬空 `custom_effect_tooltip` 5 个（`DOT_Backup_decisions.txt` 的 `LYY_qiming/ningguang/shenhe_support_increase_tooltip`；`LYY_decisions.txt` 劳动法两块；`LAW_decisions.txt` 的 `LAW_High_Resist_Here`）。
- MOD 内疑似重复读取源：`…\.backup\`；`DOT_Backup_decisions.txt`（类别与 `categories/LYY_decision_categories.txt:221` 重复）。
- 实体口径（用户 10-19 定）：PBF→娜维娅、SGD→纳西妲、SNE 两份重复不管；BRF/MHL/VLM/SFS/SDS/SKD/SGC/SFG/YLH 不补兵模。重复只剩 SNE 12 个 + `Nilou_infantry_entity` 2 个。
- `DOT_Aranara.asset` 的 `VAN_infantry_entity` 名实不符（用炮兵 mesh）；`Aranara_*` 三件套无 tag 克隆。
- 旧33决议 25 个 `GFX_decision_*` 无声明；`events/LYY_*` 注释编码损坏；`add_tech_bonus` 类别未知名；Palace 不显示；范围外悬空 14 条。
- **`pose_render.py` 不能用 Maoyao_Guard 的 `.anim` 当判据**：同一 anim 下妮露（既知良好）手臂同样被撕开 ⇒ 那是 anim/工具不兼容，不是绑定问题。判断手臂好坏用 `render_preview.py` 静态渲染 + 骨骼几何质心比对。
