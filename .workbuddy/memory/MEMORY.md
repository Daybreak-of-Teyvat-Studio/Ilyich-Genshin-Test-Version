# MEMORY.md —— 提瓦特黎明（DOT Gamma）项目备忘
> 语法/排查见技能 `hoi4-mod-bug-triage`；工具链全量见 `tools/` 与 `DOT_制作手册.md`；各国设计见 `.workbuddy\*_Design.md`；逐轮细节见 `2026-10-*.md`。本文件只记铁律与当前口径。

## 0. 铁律
- 禁恢复/回滚、禁 git 提交、禁「注释掉问题代码」。中文注释只写中文不写 ID。旧 loc 全不删；`ABY_focus.txt` 不动；focus 文件保留 `focus_tree` 头。数量一律下限；直接改原文件，禁建 `_v2`。
- **修 bug 只修不删**：loc 同键重复不许删行（拆成 `key`/`key_desc`、空值行补正文、改行尾注释），删行＝丢作者内容。颜色闭合用状态机（`§X` 开／`§!` 关）判，数 `§` 奇偶是错的。
- 事件/新闻 desc 200–400 字（去空白），生成下限取 206（`style()` 削 2–5 字）。禁破折号（`—–―─－`）。
- 新增事件/精神/loc/决议/类别/动修/宏/`on_actions` 一律并入同名 `<国>_*` 文件。新闻必须由国策/事件 `completion_reward` 触发（`news_event = { id = NS.n days = 1 }`）。`add_namespace` 写在事件文件首部。
- **focus 的 tag 限定＝树头白名单 + 少数关键国策**（LYY 30／SUM 18）；树头 `country = { or = { tag = … } }`，focus 级只给分叉点/终局写 `available`；缺省已删净（`strip_avail_always.py`）。
- 新增决议必须带 `has_completed_focus` + `visible = { … }`（缺省＝一直可见灰着）；门槛国策按绝对深度分层遍布全树（`map_sum_decisions.py`）。
- 机制修正分阶段：`*_Init` 置初值并调一次 `*_Tier_Refresh`；`*_Tier_Refresh` 先卸全档再挂唯一档；轴宏 `<M>_A/B_Up_N` 只改变量；档位保鲜由 `on_actions` 的 `*_Sync`（`on_daily`）负责；每档配只读面板（`available = { always = no }`、`cost = 0`）。
- **≤10% 的国策/决议可改 `dynamic_modifier`**（现状 0.4%＝11 个）。冗余＝同一组修正被大量 `effect xxx = yes` 反复引用。
- **轴指数变化必须可见**：`add_to_variable` 提到 `hidden_effect` 外，逐条配 `custom_effect_tooltip`（`§G加N§!`／`§R减N§!`）。
- **Tooltip 卫生**：`hidden_effect` 只包 `*_Tier_Refresh`/`*_Sync` 正文 + 连续 ≥2 行纯变量/旗标段；轴宏不整体包；`custom_effect_tooltip` 留包外。审计前先剥 `#…`。
- **备份一律放 MOD 外**：`C:\Users\XIANGZIYUAN\hoi4lint\_backup_*`。
- **loc 必须带 UTF-8 BOM**（缺 BOM 整份静默丢弃，症状＝某国本地化全空）⇒ 每轮跑 `check_loc_bom.py`；禁泄漏变量 ID（`fix_var_labels_loc.py`）。
- **`history/states/*.txt` 必须无 BOM + CRLF**（与 loc 相反！）。带 BOM 时 `Unexpected token: ﻿state` 并整份丢弃；689 个全带 → 州库空 → 过 `Loaded N provinces` 就闪退（2026-10-22 事故）。体检 `tools/check_state_all.py`，修 `fix_state_bom.py --apply`。
- `map/supply_nodes.txt`、`railways.txt` 同样**无 BOM + CRLF**；核对 `tools/verify_supply2.py`。
- Info_Board＝空决议类别（`visible_when_empty = yes`）+ `priority = { base = 100 }`（不是 `priority = N`），`_desc` 按轴拼 `§Y轴名：§![?VAR]` + 档位名 + 修正。
- 只用 5 种基础意识形态；`set_cosmetic_tag` 按意识形态上色。`on_actions` 内容必须包在 `effect = { }`。文案守 `.skills\Darwin Skills.md` 十条。

## 1. 环境
- Python=`…\binaries\python\envs\default\Scripts\python.exe`；Bash 优于 PowerShell。脚本无 BOM+CRLF；loc `.yml` 必须 BOM+CRLF；focus/ideas/events 用 tab；`.asset` 无 BOM+CRLF；**原版 txt 多为无 BOM+LF**。Edit 同文件并行会互相覆盖⇒串行。动手前先备份。
- 生效 `replace_path`：history/{countries,states,units}、bookmarks、resources、ai_strategy*、strategicregions、supplyareas。**`decisions`／`national_focus`／`gfx` 不在内** ⇒ 改原版决议只能同路径整份复制进 MOD。
- 工作区「活的」，会被外部会话整份覆盖 ⇒ 改完隔几分钟复核。`game.log` 报 Loaded 11507 provinces 才是本 MOD。真 MOD 根＝`Daybreak of Teyvat Gamma Version/`（仓库根另有 Alpha/Beta 与 `tools/`）。

## 2. HOI4 语法（1.19.3）
- modifier loc：`_<modifier>_tt` 与 `MODIFIER_<大写>`。无 farm/power_plant/reconnaissance/`army_defense_factor`/`factory_output`/`manpower_factor`/`corruption`；英式 `army_defence_factor`，农业用 `monthly_population`。
- 有 tooltip 的效果：`add/remove_dynamic_modifier`、`add/remove_ideas`、`add_stability`；无 tooltip：`add_to_variable`/`set_variable`/`set_country_flag`。
- 前置：多个 `prerequisite = { }` 块是 AND，一块内多条 `focus =` 是 OR。
- 决议 `icon=<裸名>`→`GFX_decision_<裸名>`；空分类要显示须 `visible_when_empty = yes`；trigger 内 `always = no` 可隐藏原版条目。
- **idea 图标 `picture` 必须裸名**（写成 `GFX_idea_X` → 取 `GFX_idea_GFX_idea_X` → 空白）。MIS 的 `icon =` 才写完整 sprite 名。
- **loc 硬规则**：只认小写 `\n`；`§b` 合法；畸形 `§！`/`§。`/尾部裸 `§` 补 `!`；同键重复＝**后加载者胜**；文件须在 `localisation/<语言>/` 且带 BOM + `l_<语言>:` 头。
- **解析 `.gfx` 必须 `re.I`**：`textureFile`（大 F）与 `spriteType` 并存，按花括号配对切块。
- `annex_country={target=X transfer_troops=yes}`；`set_autonomy` 用 `autonomy_state`，history 用 `autonomous_state`。
- `hoi4lint\vanilla_modifiers.json`(647) 是新效果硬约束；`on_actions` 跨文件叠加，挂载缺失静默。
- **兵模**：`entity = { clone = "源" name = "<TAG>_<infantry|artillery|cavalry>_<0..3>_entity" }`，每 tag 12 个生效。**clone 不能覆盖 attach** ⇒ 每角色自建 `<角色>_artillery_entity`（炮手＝自己步兵），tag 只 clone 本阵营。
- **三件套**：`*_sabre_infantry_rider_entity`＋`*_sabre_cavalry_rifle_combined_entity`（`infantry_cavalry_horse_mesh`，`Saddle_Node`=骑手，0.65）＋`*_sabre_cavalry_entity`（`infantry_cavalry_horse_frame_mesh`，1.2）；炮兵＝`frame_artillery_mesh`+`artillery_gun_entity`+`infantry=<自己>_infantry_entity`（`artillery_gun_entity` 是原版须白名单）。步炮兵段 sabre 节点 `Right_Hand_node_4`/`mid_back_node_2` 已删，骑兵段保留。
- **MIO 图标按 tag 所属地区**：`GFX_idea_<地区>_*`（MOT/LYY/INA/SUM/FON/NAT/SNE/NDK/PRI），判不出走 `DOT` 池；组织→tag 读 `allowed` 的 `tag`/`original_tag`/`Is_X`，先剥 `NOT = { … }`。
- **角色模型转换**：`肌`/`肌2` 是**皮肤层（四肢）**，绝不能当重合装饰剔除（纳西妲缺手臂/腿的根因）；叠加层才是 `照れ/袜s/翼+/髮+/披肩s/裙+/白目/瞳/星目`。

## 3. 各国口径
- **胜利点（2026-10-22 终版）**：档位只 5/10/20/40；**首都州 40**（`history/countries` 的 `capital` 是**州 id**）；基数＝**有胜点的州（323）**，即每 5 个 1 个 20 点、每 3 个 1 个 10 点，其余与副点恒 5。现状 **40×32、20×65、10×108、5×234（439 点／323 州）**。禁止给无胜点州补点（`eco_vp_fill.py` 勿再跑）。排序以作者原始值（`hoi4lint\_orig_head`）为准，只把分区/副本内部点降权；**原值≥25 的州主点必为 20 档**。工具 `eco_vp4.py --apply` → `eco_report.py`/`eco_render_vp.py`；`_vp_list.py` 出清单。
   - **水文核查（2026-10-22）**：439 点全部落在 `land` 省（definition.csv type）+ heightmap 全部 ≥ 海平面（96）+ 均在所属州 `provinces` 内 ⇒ 0 违规。仅 2 例「省是极小岛、质心落海」（图标会画到水上）：`3049`（state 328，20 点「雾灵渚神像」，州仅此一省）与 `1772`（state 384，5 点「最后的藏宝地·入口」，含两块礁）。脚本 `hoi4lint\chk_vp_water2.py`、`chk_vp_height.py`、`chk_vp_centroid.py`；`per-state 质心法`＝胜点图标落点判据。
- **经济（2026-10-22 01:45 终版，`eco_apply3.py`）**：按档位重设 `state_category`（40→metropolis/20→city/10→large_town/5→town/0→rural）、`manpower`、`buildings`、`resources`。约束：每国工厂 10–100（军/民/船比例见 `eco_config.CFG`）、人口 4–40 千万且每州整千（`split_pop()` 差值摊给最大州）、港口/机场只在有胜点州且每国 1–10、基建 7/6/5/4/2、资源按地形+档位加权。现状：工厂 944（军352/民498/船94）、港口 115、机场 98、基建 2358、人口 33.76 亿。
  - **写入必须行级**（`line_depths()` 按深度+正则定位整行）。**`eco_apply2.py` 勿再跑**（字符偏移拼接曾写坏 5 个州 `add_core_of = Abuildings = {`；修复 `fix_state_corrupt.py`，回滚 `eco_revert_build.py`）。
  - **港口例外 4 国**：NMN/NCE/RAG 无沿海省、PRI 唯一胜点州在内陆 ⇒ 恒 0。
- **补给（2026-10-22 02:0x 重做，`eco_supply2.py`／核对 `verify_supply2.py`）**：口径改为**只给「州内最高胜点 ≥10」的州放补给点**，取该州最高分胜点省 ⇒ `supply_nodes.txt` **205 条**（40×32＋20×65＋10×108）。
- **铁路＝原文件增量接线（用户 02:0x 明示「保留原铁路文件，在其基础上把可连的胜点都连上」，`eco_rail_extend.py`／核对 `verify_rail_extend.py`）**：原 102 行**逐行零改动**，尾部追加 71 行 / 93 段 ⇒ 共 **173 行 / 805 段 / 827 省**。做法：既有网络节点当虚拟源做多源 Dijkstra，把未联网胜点沿陆地最短路接入（并查集防环）；无铁路但 ≥2 个胜点的孤岛块内 Prim 自连；线段等级＝两端胜点档位较大者。结果**胜点省联网 421/439（95.9%）**，剩 **18 个孤礁（单点陆块）接不成铁路**，含 2 个 40 点（`860` state 64、`1808` state 345）；补给点联网 193/205。`eco_supply2.py` 默认只写补给点，要动铁路必须显式 `--rails`（现网已由本脚本管，勿再跑 `--rails`）。
  - 地图是**多块独立区域板**（4096×2048）；含胜利点的陆块共 **40 个**，其中 19 个有铁路、21 个无（18 个只 1 个胜点）。
- **NAT**：六族 NCP/NCE/NPS/NSC/NFF/NMN；变量 `NAT-ABY-Index`(40)/`MVK-Prestige-Index`(50) 不可改名。四阶段 `autonomy_puppet`→`autonomy_NAT_State`→恩情>79 吞并→恩情<19 脱离宣战。国策171/决议69/事件88/精神205。分宗决议带 `ai_will_do`（傀儡 +100）与 tag 门控（三阶段 `or = { tag = NAT, tag = <族> }`，Recapture 只给 NAT）。
- **LYY**：六派 12 路线；战后层 y∈[22,34]、id 带 `PW`、块标记 `# == <TAG> POST-WAR focus tree BEGIN/END ==`；170 决议全带门槛；六派内战+战后各 1 个 Info_Board。生成器 `_civilwar\cw_engine.py`。
- **SAN**：三终局，分叉 `SAN_PW_The_Crossroads`；双轴 `SAN-Mandate-Index`(40)／`SAN-Deep-Index`(30)。改走 `_san\patch_pw_stage.py`。
- **SUM**：雨林 `SUM_Neo_Focus_Tree`（起始 `SUM_PRO_Dawn_of_Sabzeruz`），沙漠 SGD/SDH/SGS 同树右侧。国策888／事件888／决议170／loc6602；门槛 162 个国策、深度 y3–y33。4 个 Info_Board。
  - `SUM_PRO_*` 是**共享序章**（d0 花神诞祭 → d1–d3 八分支 → d4 `SUM_PRO_The_Choice`），之后 ST 圣树／RP 共和／GT 造神三线互斥；`SUM_PL_*` 沙与林独立簇 d0–d10。
  - 生成器纪律：只重建国策用 `_sum/regen_focus_only.py`、`_desert/regen_inc_focus.py`，禁重跑 main()（会拆前置、冲掉 `ai_will_do`）。序章 7 个负面精神按深度逐个 `remove_ideas`；`SUM_God_creation_plan01` 不删（草神满意度决议在 01/02/03 间 swap）。

## 4. 工具链（当前主力）
- 经济/胜利点：`eco_vp4.py`（定档）、`eco_apply3.py`（行级写盘）、`eco_revert_build.py`、`fix_state_corrupt.py`、`fix_state_bom.py`、`check_state_all.py`、`eco_supply2.py` + `verify_supply2.py`、`eco_report.py`、`eco_render_vp.py`、`eco_render_econ.py`、`render_vp_supply.py`、`_vp_list.py`。
- 文案/结构：`wrap_hidden_effects.py`、`verify_wrap.py`、`fix_axis_tooltips.py`、`audit_dm_refs.py`、`restore_modifiers.py`、`check_tooltip_keys.py`、`_desc\darwin_pass.py`（`--check`）、`_desc\check_news_anchors.py`、`bug_scan.py`。
- loc/面板/国策：`check_loc_bom.py`、`fix_var_labels_loc.py`、`inv_info_boards.py`、`build_info_boards.py`、`check_info_boards.py`、`strip_avail_always.py`、`merge_sum_prereq.py`、`set_ai_weights.py`、`gate_lyy_route_focuses.py`、`map_sum_decisions.py`。
- 兵模/模型：`bind_unit_models.py`、`fix_artillery_entities.py`、`rebuild_entities_law.py`、`dedup_entities.py`、`strip_infantry_sabre.py`、`verify_entities2.py`、`reicon_mio_by_region.py`+`verify_mio_icons.py`、`nat_dissent_ai.py`；模型走技能 `hoi4-pmx-to-mesh`（`vysna_build.py`；本 MOD 补丁版 `hoi4lint\nah_build.py`）。
- 胜利点旧工具：`vp_apply_liyue_sumeru.py`（Gamma→Beta）、`vp_apply_inazuma.py`（Beta→Gamma）、`vp_apply_mond.py`、`vp_render_*.py`。**两版省号不可互译**，桥只能州名+TPS（锚点141，LOO 中位19px）。写盘必须按 gid 聚合，一州多点「追加到最后一条 victory_points 后」。
- 参考图：`.backup/Beta_VP标注图/提瓦特大地图6.7.jpg`（25500×22500）是多块区域板拼接、左上另有缩略图，跨板不可坐标变换，只能逐板裁切读字（≥0.4 缩放可读）。
- 一律 dry-run 先行、`--apply` 才写、幂等、自动备份出 MOD。

## 5. 遗留
- 未实测：`end_puppet` 对 `autonomy_*`、`create_country_leader`、动修是否真挂、档位逐档变化、决议门槛、兵模是否上屏、`hidden_effect` 静音。
- **NAT 缺 `on_actions` 挂载（待定夺）**：`NAT_ABY/GRACE/V3_Monthly_Tick` 零调用者 ⇒ 每月机制不跑；挂 `on_monthly` 会改平衡，须用户点头。
- 真悬空 `custom_effect_tooltip` 5 个（`DOT_Backup_decisions.txt` 的 `LYY_qiming/ningguang/shenhe_support_increase_tooltip`；`LYY_decisions.txt` 劳动法两块；`LAW_decisions.txt` 的 `LAW_High_Resist_Here`）。
- MOD 内疑似重复读取源：`…\.backup\`；`DOT_Backup_decisions.txt`（类别与 `categories/LYY_decision_categories.txt:221` 重复）。
- 实体口径（用户 10-19 定）：PBF→娜维娅、SGD→纳西妲、SNE 两份重复不管；BRF/MHL/VLM/SFS/SDS/SKD/SGC/SFG/YLH 不补兵模。
- `DOT_Aranara.asset` 的 `VAN_infantry_entity` 名实不符；`Aranara_*` 三件套无 tag 克隆。旧33决议 25 个 `GFX_decision_*` 无声明；`add_tech_bonus` 类别未知名；Palace 不显示；范围外悬空 14 条。
- **`pose_render.py` 不能用 Maoyao_Guard 的 `.anim` 当判据**：同一 anim 下妮露手臂同样被撕开 ⇒ anim/工具不兼容，不是绑定问题。判手臂用 `render_preview.py` 静态渲染 + 骨骼质心比对。
- 待用户确认：能否正常进游戏（若仍失败要 `game.log` 末行 + `error.log` 前 10 条）；`PRI` 是否破例建港；`DRA` 首都 40 点名「阿贝多的实验营地」是否改「寒天之钉」；2 个质心落海的胜点是否要移动/剔除。
