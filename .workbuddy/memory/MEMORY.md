# MEMORY.md —— 提瓦特黎明（DOT Gamma）项目长期备忘

> 通用 HOI4 语法/排查见技能 `hoi4-mod-bug-triage`。本文件只记**本项目特有**口径、路径、环境、状态。
> 逐轮细节见同目录 `2026-10-*.md`；方法论/工具链/参数/事故复盘见 `DOT_制作手册.md`。

## 0. ⭐ 用户铁律（最高优先级，不得自行推翻）
- **禁止恢复/回滚**：一律在「现状」上加工（2026-10-12 11:22 磁盘被外部副本整体回滚，282→85 国策）。
- **六族三阶段**：①开局六族=`autonomy_puppet`（history，`=`后两个空格）；②开篇国策只能转 `autonomy_NAT_State`（竞逐之盟），绝不开局吞并；③恩情>79 完成吞并国策才 `annex_country`；④恩情<19 六盟脱离并宣战。**顺序铁律：先 `end_puppet` 再宣战**（附属国不能对宗主宣战）。
- **机制效果用 decision 不用 action**；`on_actions` 只许开局初始化 + 档位显示同步。
- **`NAT_decisions-01/02/03` 必须保留**：01 深渊侵蚀30天 / 02 恩情涣散30天 / **03 深渊之蚀180天（到期未封渊→HIP宣战纳塔，`activation` 是唯一玩家开关）**。
- **分宗不改变部族国家颜色** ⇒ 分宗链条禁止 `set_cosmetic_tag`/`set_cosmetic_idea`，loc 显式声明。
- 10-06 **角色国别表=用户名单**（`hoi4lint\icon_gen\role_nation.py` 的 `WIKI_ROLE_TABLE`，禁止抓 wiki 猜词）。
- 10-07 **图标=v7 原版链路+v4 命名/idea 规则**；素材库=`.skills\bwiki\icons3`（icons3 6417 优先）。
- 10-10 **旧 localisation 一律不删**；**`ABY_focus.txt` 是废弃物禁止恢复/重写**；focus 文件必须保留 `focus_tree` 头部。
- 10-11 **NAT 剧本直接改原文件，禁止建 `_v2`**（TNO 风格）。路线↔意识形态：甲统一→`genshin`(主)/`communism`(副)；乙联邦→`democratic`(主)/`neutrality`(副)；丙深渊→`fascism`。**cosmetic 按意识形态上色，不按路线**；开局仅 1 个独特决议组，其余由国策 flag 解锁。
- **用户偏好**：禁止「注释掉问题代码」偷懒——读手册做真实修复；中文注释只写中文不写 ID。
- **禁止 git 提交**（用户 10-13 起明令）。所有修改仅落工作区。

## 1. 环境与写保护
- **Python**=`C:\Users\XIANGZIYUAN\.workbuddy\binaries\python\envs\default\Scripts\python.exe`（有 numpy/PIL）。
- **Bash 工具优于 PowerShell**（无 stdout 吞噬、无中文 mojibake）。中文路径硬编码在 UTF-8 脚本源码里，PS 只执行 `& <python> <脚本>`。
- **编码**：脚本无 BOM+CRLF；loc `.yml` 必须 BOM+CRLF，写入 `io.open(...,'w',newline='\r\n')`，写入后字节级自检。
- **Edit 工具同文件并行会互相覆盖** ⇒ 多处修改串行。
- **缩进**：`NAT_Neo_decisions.txt` 用 4 空格；focus/ideas/events 用 tab（事件层 tab1、option 层 tab2）；loc 键前导一空格。
- **区块改写四禁**（见手册 F2）：禁就地写回 / 禁字符级偏移 / **禁 depth 判块尾** / **插入点区分块内(`close`)块后(`close+1`)**。
- **工作区写保护**：shell 子进程对**已存在**文件 `open('w'/'r+b')`/`os.replace`/`os.rename`/`os.remove` 一律 `PermissionError`；**内置 Write/Edit 工具可写**。绕行：大二进制写「新文件名」再用 Edit 改引用它的配置。工作区外读写正常。

## 2. 路径
| 用途 | 路径 |
|---|---|
| MOD 根 | `…\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version` |
| 兄弟版 | 同根 `Alpha/Beta Version`；另有 `DOT05/06/07` |
| 原版 1.19.3 | `C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV` |
| 脚本+备份 | `C:\Users\XIANGZIYUAN\hoi4lint\` |
| 日志 | `Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log` |

生效 `replace_path`：history/countries|states|units、common/bookmarks|resources|ai_strategy(_plans)、events、common/decisions|countries、map/strategicregions|supplyareas。⚠ `common/national_focus`、`continuous_focus`、`gfx` **不在内**（同名空文件是屏蔽开关）。

## 3. ⭐ 工作区是「活的」文件系统
- 会被外部副本整份覆盖（多次回滚掉我做过的事，含 MEMORY.md 本身）⇒ **任何「我做过的事」先 grep/ls 核实，不凭记忆答复**。
- 文件会被合并改名 ⇒ 校验脚本按内容特征定位，不写死文件名/计数。
- 外部进程会并发插行/截断 ⇒ 动手前先备份。
- `game.log` 报 **Loaded 11507 provinces** 才是本 MOD（13414=原版地球）。

## 4. NAT 地图与机制现状
- NAT州61/六族州43/ABY州6/HIP州0。六族 tag：`NCP 沃陆之邦 NCE 回声之子 NPS 流泉之众 NSC 悬木人 NFF 花羽会 NMN 烟谜主`。
- 自治州 `autonomy_NAT_State`=「竞逐之盟」（`common/autonomous_states/DOT_Puppet.txt`）。
- 两变量 `NAT-ABY-Index`(侵蚀,开局40)、`MVK-Prestige-Index`(恩情,开局50)——**名不可改**。档位 flag `NAT_ABY_T1..T7`/`NAT_MVK_T1..T7`。深渊战况 `NAT-War-Index` 0/20/40/60/80→5档。
- **改两变量必须走宏**：`NAT_Abyss_Add/Sub_*`(Add=1/3/5/8/10/12/15/20/25/30/40；Sub=2/3/5/7/8/10/12/15/20/25/30)、`NAT_Grace_Add/Sub_*`(仅3/5/6/8/10/12/15/20/25/40，**无8档Sub**)。动态修正直接 `enable={check_variable={X>N} NOT={...}}`，区间互斥+首档 `has_variable` 守卫。三终局互斥 `NAT_Focus_Convergence_Final`/`Covenant_Final`/`Embers_Final`。
- **运行时接线铁律**：静态校验全绿≠机制在跑。判活看 `add_dynamic_modifier` 是否被调用。⚠ `on_actions` 跨文件叠加（同名钩子合并），挂载点缺失是静默的。10-12 已在 `common/on_actions/DOT_on_actions.txt` 的 `on_startup` 补齐恩情初值50+19个 `add_dynamic_modifier`（7深渊+7恩情+5战况，挂载==定义集合）。机制已迁 decision。
- 六块部族异议树（放射状，9非根全挂族根；双参照系 `NAT_Promote_Natlan_National_Identity`(40,1)子树23 / `NAT_The_Great_Unity_Of_All_Fires`(40,11)子树7；六族根 `NCP(50,2) NCE(58,2) NPS(66,2) / NSC(50,14) NFF(58,14) NMN(66,14)`；恩情降幅1-2层-5、3-4层-10走宏；分宗=置`_Independent`旗+先`end_puppet`+`NAT={country_event={id=NAT_Event.70X days=2}}`；事件 `NAT_Event.700..705` option 内 `declare_war_on`+`add_war_support=0.05`）。
- 效果扩充三层（任务#86）：107精神/591 modifier/340 loc，零非法（批1部族树54非根国策专属精神双通道下发；批2 30决议注释意图实装为限时精神；批3 23剧情事件补option效果）。生成器 `hoi4lint\task86_*.py`，备份 `hoi4lint\backup_task86\`。
- 深渊纳塔树 26 国策（门槛 `NAT-ABY-Index>100`；终局 `NAT_Abyss_Become_The_Abyss_Natlan`→`set_politics`+`NAT_Abyss_Set_Leader_Gustot`+`add_ideas=NAT_Abyssal_Natlan_Core`+吞HIP+对六族宣战）。5宏在 `common/scripted_effects/NAT_Neo_effects.txt`。24 `NAT_Abyssal_*` 精神。领袖 `create_country_leader`+`add_country_leader_trait`，`picture=GFX_portrait_NAT_Gustot`（`interface/DOT_Leader.gfx` 已补 SpriteType，贴图 `gfx/leaders/LY/Azhdaha.dds`）。
- 当前规模：国策171/决议69/事件88/精神205/loc 1573键。校验 `hoi4lint\nat_verify_six_tribes.py`、`task86_verify*.py`。

## 5. HOI4 语法铁律（已对原版 1.19.3 取证，详见技能/手册 F 节）
- modifier 中文显示两套 loc：`_<modifier>_tt`=` $MODIFIER_<大写>$: $RIGHT|+=%1$` 与 `MODIFIER_<大写>`=中文名。tooltip 列修正写 `[xxx_tt]`。`$MODIFIER@xxx@$` 语法不存在。
- **1.19.3 没有** farm/power_plant/radar_building/reconnaissance 四类修正；真实拼写见 `production_speed_radar_station_factor`/`recon_factor`/`production_speed_industrial_infrastructure_factor`，农业用 `monthly_population`。
- `annex_country={target=X transfer_troops=yes}`；脚本 `set_autonomy` 用 `autonomy_state`，history/countries 用 `autonomous_state`。
- `has_idea`(单数)合法；`set_cosmetic_tag=<纯国家tag>` 合法（自写审计会误报）；决议 `icon=<裸名>`→`GFX_decision_<裸名>`，分类→`GFX_decision_category_<裸名>`（两套命名空间）。
- **原版 `common/effects`、`common/triggers` 目录不存在** ⇒ 词表靠 grep 真实目录。`hoi4lint\vanilla_modifiers.json`(637条) 是新效果硬约束。
- 模型绑 `.gfx`+`.asset`，建筑 mesh 是 Y-up；`heightmap.bmp` 4096×2048 8bpp。

## 6. 遗留 / 已知未修
- NAT 剧本未进游戏验证（只看静态层+交叉引用）：`end_puppet` 对 `autonomy_puppet` 表现、`NAT={check_variable}` 跨作用域、`create_country_leader` 运行时换领袖、19个修正是否真挂上。
- 旧33决议中25个 `GFX_decision_*` 图标全库无声明（显示空白）——按「禁止恢复」只新增不改旧。
- 分类文件里 `NAT_Tribe_Deep/Rift/Grand/War/Ceasefire/Council` 六分类对应容器在回滚后基线中不存在。
- `ABY_focus.txt`=0字节是用户删除的废弃物，**不动**。
- `events/LYY_*`、`common/country_leader/LYY_traits.txt` 中文注释编码彻底损坏(U+FFFD)⇒原文永久丢失。
- error.log `add_tech_bonus: Unknown technology category`(MOT/RAG/SAN/SNE/NAT events) 既有问题待处理。
- **GUN 吞并他国 state 已主动禁用**（用户10-13要求 # 注释）：`GUN_Decisions.txt` L738 与 `NewMOT_Knights_event.txt` Knights.169–175 共7行已注释；未动 `GUN_Build_*`、Knights.44、Knights.204。
- **奇观 Palace 不显示（截至 10-14 未闭环）**：历经坐标/y/level/spawn_point 多轮修复均无效，已回退至最初配置（spawn_point=`nuclear_reactor_spawn`、y=9.50、state 改 `level=1`、省号 2671/1488）待用户开 1936 新局实测。
- **模型 BUG（10-14）**：①V3 胡桃/可莉头部白色方块；②原胡桃无头发、可莉无身体；③`gfx/models/buildings/factory.mesh` 过小+黑色脚手架。**已处理（10-14 午）**：factory=去重+放大 4/3+换干净石质贴图（备份 `hoi4lint/_tc/backup/factory_20261014_120959`）；胡桃/可莉=改用 `vysna_build` 全几何重建、图集幂二次方 1024×2048（备份 `hoi4lint/backup_full/20261014_123810`）——**待用户开新局实测**。

## 7. 璃月内战支线剧本（LYY Civil War，**六方全部实装**，2026-10-14）
- 蓝本文件：`Daybreak of Teyvat Gamma Version\LYY_CivilWar_Design.md`（六方版，~10.3 万字符 / 1086 行）。
- **六方 ↔ tag ↔ 意识形态（用户钦定，勿改）**：刻晴 `KQP`=`communism`（启蒙共和主义）；凝光 `LYY`=`democratic`（资本主义民主，正统现政府）；甘雨 `GYP`=`neutrality`（恢复帝君旧制）；申鹤 `SHP`=`fascism`（极端仙人治国）；公子 `YLH`=`fascism`/`neutrality`（至冬干涉军）；蓝砚 `CYG`=`genshin`（极端环保/无政府，沉玉谷水土危机）。**全 MOD 仍只用 5 种意识形态**；每派 2 路线（钦定主线+暗线），共 12 条。
- 每派规格：≥50 国策 / 10 决议 / 50 事件 / 10 精神 / 2 路线 / 1 特殊机制。**实装机制（双轴变量名不可改）**：KQP 变革度‖体制惯性（`KQP-Reform/Inertia-Index`，30/70）；LYY 财货‖律令（`LYY-Wealth/Law-Index`，50/50）；GYP 礼制‖民生（`GYP-Rite/Benevolence-Index`，60/40）；SHP 仙威‖戒律（`SHP-Might/Discipline-Index`，55/45）；YLH 战备‖封锁（`YLH-War/Blockade-Index`，60/40）；CYG 水土‖山心（`CYG-Soil/Will-Index`，30/55）。
- 新树置于原 `LYY_Neo_Focus` 右侧：原树**实测 118 国策、根 `LYY_Rock_and_Covenant` x=40、绝对最右 x=61**（非此前以为的 346/46）。六块实装 `x` 区间**依次为 KQP 64–98 / LYY 112–150 / GYP 165–199 / SHP 214–254 / YLH 265–305 / CYG 316–350**（两两不交）。除根外全部 `relative_position_id`；**横坐标间距 ≥2** 由生成器布局算法保证（叶列唯一+父居中+**同层强制留距**）。图标全用现成 `GFX_goal_LYY_*`（语义对应，含 `LYY_Lan_Yan`）。
- **数量口径（2026-10-14 用户明确）：国策/决议/事件/精神的数量要求一律为「下限」，可超不可低。**
- `BRF` 黑岩厂=**唯一野牌**（不设独立树）。MOD 已有占位内战线 `LYY_FC_Ganyu/Keqing/Ningguang/Shenhe`（loc 标"尚不可用"）。
- **两条新约束（2026-10-14 用户口径）**：① **游戏不显示子意识形态** ⇒ 全部只用 5 种基础意识形态 `set_politics`，禁写「子 xxx」；② **内战因帝君驾崩引发 ⇒ 帝君全程不出场**（不复活/不现身/不发话），涉及帝君者一律写"遗诏/遗泽/他留下的制度"。设计文档已按此改写（S3 超事件改为「帝君的遗诏」）。
- **实装进度（2026-10-14 完成六方 / 同夜再完成「战后层」）**：**KQP/LYY/GYP/SHP/YLH/CYG 六方内战 + 战后两套剧本全部落地**。内战 304 国策 / 94 决议 / 336 事件（6×56，段 2001–7056）/ 73 精神 / 60 档；**战后 326 / 76 / 336（段 8001–13056）/ 81 / 60**；合计 **国策 630 / 决议 170 / 事件 672 / 精神 154 / 动态修正 120 / 新闻 20**。全树 `LYY_Neo_Focus.txt` = **748 focus（原树 118 + 新增 630）/ 花括号 4972:4972**，12 块（六方 × 内战/战后）均在 `focus_tree` 内。备份 `hoi4lint\backup_civilwar\`。
- **⭐ 战后层（第二轮，2026-10-14 夜）要诀**：① 战后树**纵向下移**（非右移）——`POST_ROOT_Y = 22`、子树 y∈[22,34]，内战 y∈[2,16]，两层不重叠而横向仍在本派系列内；块标记 `# == <TAG> POST-WAR focus tree BEGIN/END ==`，与内战块同文件、可幂等重跑；② 战后**根国策 `available`** = `has_completed_focus = <本方首个内战国策>` ＋ 6 个 `owns_state`（121/150/177/170/456/658）；六方首个内战国策 id = `KQP_CivilWar_Dawn` / `LYY_CivilWar_Tianquan` / `GYP_CivilWar_Moonlit` / `SHP_CivilWar_Lone_Crane` / `YLH_CivilWar_Childe` / `CYG_CivilWar_Valley`；③ 根国策 `completion_reward` 内一次性接 `<TAG>PW_Init`（初始化战后两轴＋挂载 10 个动态修正）与 `LYY_PW_News_Begin`；④ 战后档位/共振 id 一律带 **`PW`** 标记（`<TAG>_PWCombo_*`），与内战层隔离；⑤ **新闻**：`events/LYY_CW_news.txt`，命名空间 **`LYY_News`**（已在 `events/LYY_Event_Script.txt` 声明，**勿重复 add_namespace**），id 9001–9010（内战）/ 9011–9020（战后），由 `LYY_CW_News_Begin` / `LYY_PW_News_Begin` **全局旗守卫**的脚本效果按 days 排程发射；⑥ 生成器 `post_<tag>.py` 六份（`post_kqp.py` 为模板）。设计文档见 **`LYY_CivilWar_Design.md` 附录 C**。
- **⭐⚠ cost 口径（用户 2026-10-14 23:08 明确）**：**只把六方新增国策的 cost 由 7 改为 6.0，原树 118 个既有国策保持 7**。`build_focus_file()` 里**只对新增块字符串**做 `re.sub(r"cost = 7(?![0-9.])", "cost = 6.0", block)`，**绝不对整份 `cur` 做全局替换**（首版全局替换把原树也改了，已回退）。现分层：原树 118 个 = `cost = 7`，六方新增 630 个 = `cost = 6.0`。原树权威基准副本 `hoi4lint\_civilwar\base_original_LYY_Neo_Focus.txt`（取自最早备份 `backup_civilwar\20261014_132428\`，sha256 前 16 位 `51567e96d9686067`），一键还原脚本 `restore_original_cost.py`。
- **⭐⚠ 多表合流 id 冲突铁律（2026-10-14 血泪）**：六个独立数据表合流时，**任何跨表的全局 id（双轴变量名 / 动态修正 id / 精神 id / 决议 id / 类别 id / 宏前缀）必须带层别标记**，不能靠「名字看起来不一样」。本轮战后表与内战表重名 8 处（`GYP_Rite_Tier_1..5`、`GYP-Rite-Index`、`CYG-Soil-Index`、`LYY_Spirit_Tianquan_Eternal`、`GYP_Spirit_Moonlit_Secretariat`、`YLH_Spirit_Five_Envoys`）⇒ 合并文件里后定义者**静默覆盖**前者。修复法：只改战后一侧加 `PW` 标记，再整仓重生成。扫描器 `_civilwar\scan_collisions.py`。
- **⭐ 合流架构（2026-10-14 夜起，取代分派系落盘）**：生成器 = `hoi4lint\_civilwar\cw_engine.py`（+ `cw_enrich.py` 修正扩充表 + `cw_news.py` 新闻表 + `data_<tag>.py` 六份内战数据表 + `post_<tag>.py` 六份战后数据表；`data_kqp.py` 只是把 **`gen_kqp.py` 的数据表**适配成统一 schema，**数据不搬家**，gen_kqp 有 `__main__` 守卫可安全 import）。旧 `faction_engine.py`/`gen_kqp.py` 保留但**弃用**。输出 **10 个合并**文件（旧的 48 个分派系文件已备份后删除）：
  | 内容 | 合并文件 |
  |---|---|
  | 六方 × 内战/战后共 12 子树（一条 focus_tree，各 `TAG focus tree` / `TAG POST-WAR focus tree` 分块） | `common/national_focus/LYY_Neo_Focus.txt` |
  | 决议（12 个 category 块 = 六方 × 内战/战后）/ 类别（12 定义） | `common/decisions/LYY_CW_decisions.txt` / `categories/LYY_CW_categories.txt` |
  | 事件（**672** 段，同 NS `LYY_Event`，**勿重复 add_namespace**） | `events/LYY_CW_events.txt` |
  | 新闻（**20** 段，NS `LYY_News`，9001–9020） | `events/LYY_CW_news.txt` |
  | 精神（**单个** `ideas={country={...}}` 顶层块，**154** 条） | `common/ideas/LYY_CW_ideas.txt` |
  | 动态修正（**168** 块 = 120 档 + 24 内战共振 + 24 战后共振态） | `common/dynamic_modifiers/LYY_CW_dynamic_modifiers.txt` |
  | 脚本宏（**218** 个，含两组新闻发射器） | `common/scripted_effects/LYY_CW_effects.txt` |
  | 机制挂载（**单文件**：`on_startup` 初始化 + `on_monthly` 保活，含战后守卫） | `common/on_actions/LYY_CW_on_actions.txt` |
  | 本地化（**5017** 键，BOM+CRLF） | `localisation/simp_chinese/LYY_CW_l_simp_chinese.yml` |
  校验器（**四件，全绿**）= `verify_requirements.py`（逐条对照用户 5 项要求）/ `verify_merged.py`（花括号/唯一性/定义==挂载/loc 编码）/ `global_check.py`（跨派系 + 事件区间 + 命名空间，**已按合并布局重写**）/ `scan_collisions.py`（内战 × 战后 id 冲突扫描）。另有 `make_overview.py`（生成 `LYY_CivilWar_Overview.md`）/ `restore_original_cost.py`（原树 cost 还原）。
- **⭐ 机制挂载写法**：`on_actions` 内用「**一个 `every_country` + limit 为 `OR={tag=…}` + 按 tag 的 `if`**」，避免同一 hook 内重复 `every_country` key。**保活钩子已由 `on_daily` 改为 `on_monthly`**（原版 1.19.3 有 `on_monthly`，vanilla 用 31 处）。`add_dynamic_modifier` 挂载集合必须==定义集合。
- **⭐ 文案「十条规则」（用户 10-14 夜二次下发，最高优先级的写作口径；规范原文 `.skills\Darwin Skills.md`）**：① 禁立靶子/虚假对比/对称排比（`不是X而是Y`、`既X又Y`、`不仅…而且…`）；② 删硬转折与空洞程度词；③ 删套话开场（值得注意的是/先说结论/众所周知/话说在前头…）；④ 禁表演性拆词（「所谓」/「把某词拆开」）；⑤ 禁会议式编号（第一/其一/首先，）；⑥ 清大厂黑话（赋能/抓手/闭环/链路/底层逻辑）与情绪标签（扎心/狂飙/拉爆/残酷…）；⑦ 删无分级最字（最+核心/关键/根本…）与追问词（到底/究竟）；⑧ 去名词化（进行X→X、作出决定→决定、造成影响→影响）；⑨ 语气平等（必须→需要、务必→要），不居高临下；⑩ 少破折号（`——`→`，`）与滥用引号（2–4 字短概念去引号）。**只改风格：事实/数据/专名一律不动。**
- **⭐ 文风管线 `cw_engine.py::style()`（10-14 夜二次重写，取代旧保守版）**：常量在文件顶部（`_FAKE`/`_RATHER`/`_BARE_ERSHI`/`_JIYOU`/`_BUJIN`/`_OPENERS`/`_NUMBERING`/`_DEL_ALWAYS`/`_DEL_DIIDAO`/`_NOMINAL_RE`/`_JARGON`/`_EMOTION`/`_DEGREE_DEL`/`_DEGREE_MAP`/`_MAXFIX`/`_DASH`/`_QUOTE_TERM`），`lint()` 做同口径体检（`style_report()` 打印原稿/残留对比）。**结果 1875 条样本 802 处命中 → 残留 0**；另跑标点异常扫描全 0。报告文件 `Daybreak of Teyvat Gamma Version\LYY_CivilWar_StyleRules.md`。
- **⚠ 文风管线三个血泪坑（务必保留）**：① **`不是X，而是Y` 必须整段替换为「是Y」**——旧版只删「，而是」遇 `不再是X，而是Y` 会变病句（`…的私约一个人与…`）；② **破折号转换必须排在管线最前**——原文大量用 `——是…` 表达对比，排在对比规则后会漏 9 条；③ **程度词不能纯删**——「灯格外亮」→「灯亮」、「非常时期」→「时期」会破句，须「整词虚张者删、破句者换平实词（非常→很/格外→更/极其→极/颇为→较）」并对成语 `非常时期|手段|之时` 加负向前瞻。
- **边界（有意保留、勿再删）**：对话祈使「记住今天」、语义性「没有谁必须服从」、可分级「最大/最好/最后一/最深处/最锋利」、非排比的「既…也是…」、专有名词与数据。
- **⭐ 效果扩充（用户 10-14 夜要求）**：精神追加修正 73 条（2→4~5 项/条）；档位追加修正 60 条；**双轴共振动态修正 24 个**（每方 4 态 `TAG_Combo_Twin_High/Twin_Low/A_High/B_High`，`enable` 内 `check_variable` 双判 >60 / <40）；决议附加效果 94 条（含 40+ 条直推双轴的 `R<n>/I<n>`）；终局国策自动收官加成（`flag` 以 `_Final`/`_Reunify`/`_Done`/`_Open` 结尾触发）；脚本宏步长 8 档（3/5/8/10/12/15/20/25）。扩充表数据在 `cw_enrich.py`（`IDEA_EXTRA`/`TIER_EXTRA`/`COMBO`/`DEC_EXTRA`）。
- **KQP 落地要点**（复用到其余五方）：① 国策插入 `common/national_focus/LYY_Neo_Focus.txt` 的 `# 刻晴内战国策线` 锚点，用 `KQP focus tree BEGIN/END` 包裹以便幂等重跑；② **决议文件的顶层块名必须等于 `common/decisions/categories/` 里定义的类别 id**（本轮曾写错为 `KQP_civilwar_decisions`）；③ 机制 = 动态修正 5+5 档（`enable` 区间互斥，`has_variable` 守首档）+ on_actions 挂载，变量 `KQP-Reform-Index`/`KQP-Inertia-Index`（开局 30/70）；④ 事件复用命名空间 `LYY_Event`；⑤ 事件配图用 `GFX_Civil_War_of_Liyue` / `GFX_report_event_generic_*`（vanilla interface 未被 replace_path，可用）；⑥ ⚠ **相对坐标：子国策 `x/y` 必须是「绝对 − 前置绝对」**，若同时写绝对 x 与 `relative_position_id` 会**翻倍错位**；⑦ ⚠ **事件/长文本 loc 内换行必须转义写 `\n`**（`esc()` 处理）；⑧ 布局算法 `layout()`：叶列唯一+父居中 ⇒ 同层横坐标差恒 ≥2。**通用引擎额外铁律**：⑨ **同层强制留距**收尾必开——终局节点多前置取列中点会落半列、与邻节点差 1（CYG 踩坑）；⑩ **事件选项内禁写 `ev=<自身id>`**（会自触发并虚增事件计数），改 `flag=`；⑪ 修正名/事件配图先过白名单——⚠ **原版无 `GFX_report_event_generic_navy`/`_green_politics`**，MOD 内**无任何** `GFX_report_event_generic_*`，可用者仅原版 41 个（handshake/conference/factory/military_parade/naval_treaty/riot/parliament/construction_site/rally…）；⑫ 决议图标**全库仅 `GFX_LYY_decision_01..15`** 15 个声明，六方共用；分类图标用原版 `GFX_decision_category_generic_*`/`money`/`power_struggle`。

- **⚠ 工作区写保护当前已失效**：shell 子进程可直接新建/改写/删除 MOD 内文件（本轮 create/append/remove 实测全部 OK）；仍建议「先备份再改写」。
