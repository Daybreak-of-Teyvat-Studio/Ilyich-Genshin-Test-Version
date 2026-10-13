# MEMORY.md —— 提瓦特黎明（项目长期备忘）

> HOI4 通用语法/排查见技能 `hoi4-mod-bug-triage`。只记**本项目特有**的口径、路径、环境与状态。
> ⛔ **2026-10-12 11:22 磁盘被外部副本整体回滚**（282→85 国策）。用户明令**「禁止恢复，就在现在 mod 文件的基础上加工」**。
> 逐轮细节见同目录 `2026-10-*.md`；**方法论/工具链/参数/事故复盘见 `DOT_制作手册.md`**。

---

## 0. ⭐ 用户口径（最高优先级，不得自行推翻）

- **禁止恢复**：一律在**现状**上加工，不许回滚备份。
- **六族三阶段铁律**：① 开局六族 = `autonomy_puppet`（history，`=` 后**两个空格**）
  ② 开篇国策**只能转 `autonomy_NAT_State`（竞逐之盟），绝不可开局吞并**
  ③ 恩情 **>79** 完成吞并国策才 `annex_country` ④ 恩情 **<19** 六盟脱离并宣战。
  **顺序铁律：必须先 `end_puppet` 解除附属再宣战**（附属国不能对宗主宣战）。
- **机制效果用 decision 不用 action**：`on_actions` 只许开局初始化 + 档位显示同步。
- **`NAT_decisions-01/02/03` 必须保留**：01 深渊侵蚀 30天 / 02 恩情涣散 30 天 /
  **03 深渊之蚀 180 天，到期未封渊 → HIP 宣战纳塔**（`activation` 是唯一玩家开关）。
- **六块部族异议树**：原树**最右边**加 6 块独立树，每块 10 个、**放射状**（9 个非根全挂族根）；
  都降恩情、都加强对应部族；点任一块树的**第一个国策** ⇒ 解锁 18 决议组（6 族 × 3 阶段；
  分宗 ⇒ 国际新闻事件 ⇒ 点开即宣战）。树与决议组由**纳塔 + 六族共享，仅恩情 < 50 可点**。
- **机制仪表盘**：显示恩情/侵蚀的决议描述界面要显示各档位的**国家修正效果**。
- **分宗不改变部族国家颜色**（用户明确纠正过 AI 的错误说法）⇒ 分宗链条里**禁止出现**
  `set_cosmetic_tag` / `set_cosmetic_idea`，并在 loc 里显式声明。
- 10-06 **角色国别表 = 用户名单**，权威源 `hoi4lint\icon_gen\role_nation.py` 的 `WIKI_ROLE_TABLE`；禁止抓 wiki、猜关键词。
- 10-07 **图标 = v7 原版链路 + v4 命名/idea 规则**（v7x/frost_bases/base12_only/geo_frame/tone_schemes/v10~v14 全作废）；
  **素材库 = `.skills\bwiki\icons3`**（icons3 6417 优先），无抠图要自己抠。
- 10-10 **旧 localisation 一律不删**（值同无害保留，值不同才处理）；**`ABY_focus.txt` 是废弃物，禁止恢复/重写/再提**；
  **focus 文件必须保留 `focus_tree` 头部**（`id=` / `country={factor,modifier}` / `default=` / `continuous_focus_position`）。
- 10-11 **NAT 剧本直接改原文件，禁止建 `_v2`**；参考 TNO 风格。
  路线↔意识形态：甲统一→`genshin`(主)/`communism`(副)；乙联邦→`democratic`(主)/`neutrality`(副)；丙深渊→`fascism`。
  ⚠ **cosmetic 按意识形态上色，不按路线**。**开局仅 1 个独特决议组**，其余分类由国策 flag 解锁。

**用户偏好**：禁止「偷懒注释掉问题代码」——读手册做真实修复，注释只在引擎确无能力并获确认后用。中文注释**只写中文，不写 ID**。

---

## 1. 环境与写保护

- **Python = `C:\Users\XIANGZIYUAN\.workbuddy\binaries\python\envs\default\Scripts\python.exe`**（有 numpy/PIL）；`versions\3.13.12` 无 PIL。
- **Bash 工具优于 PowerShell**（有 stdout、无中文 mojibake）。PS 的 `*>`/`2>` 写成 UTF-16；中文路径经 PS 传参会 mojibake
  ⇒ 写 UTF-8 Python 驱动脚本，中文路径硬编码在源码里。
- && **heredoc 里写反斜杠会被 bash 吃掉**（`\s` → `/s`）⇒ 改脚本源码用 `chr(92)` 拼接或事后单独修。
- **编码铁律**：脚本无 BOM+CRLF；**localisation `.yml` 必须 BOM+CRLF**。
  写入必须 `io.open(...,'w',newline='\r\n')`，读取先 `.replace('\r\n','\n')`。写入后**必须字节级自检**。
- && **Edit 工具同文件并行会互相覆盖** ⇒ 多处修改必须**串行**。控制台 GBK 显示 UTF-8 是假乱码 ⇒ 只认字节。
- **缩进口径**：`NAT_Neo_decisions.txt` 用 **4 空格**；focus/ideas/events 用 tab（事件层 tab1、`option` 层 tab2）；loc 键前导一个空格。完整表见手册 F3。
- && **区块改写四条禁令**（全部导致过静默错误，详解见 `DOT_制作手册.md` F2）：
  禁止就地写回 / 禁止字符级偏移 / **禁用 depth 判块尾**（`add_tech_bonus = { ... }` 单行块会让 depth 提前归零）
  / **插入点必须区分块内块后**（`close` 是块内、`close+1` 是块后；做错会让 `add_ideas` 落到块外而**静默失效**）。
- **focus 的 `icon =` 存裸名**（引擎自动补 `GFX_goal_`）⇒ 脚本里不要再拼前缀。
  **focus tooltip = loc 键 `<focus_id>_desc`** ⇒ **无需在 focus 块写 `desc =`**。
- `relative_position_id` 必须指向该国策自己的【祖先】（本项目另有 25 个挂子树参照系，见 4c）。
- **工作区写保护**：`shutil.copyfile`纯覆盖首选；`open(...,'w')`/Write/Edit 可用；
  `os.rename`/`cp -f`（先 unlink）WinError 5 ⇒ **绝不先 `os.remove`**。
- **长跑进程**：WMI Create、`run_in_background`、`nohup … &` 均实测被回收 ⇒ 需长驻先问用户
  （用户不接受自动启动类持久化）。判活用 `Get-CimInstance Win32_Process`。

## 2. 路径

| 用途 | 路径 |
|---|---|
| **MOD 根（工作区）** | `C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version` |
| 兄弟版 | 同根 `Daybreak of Teyvat Alpha/Beta Version`；另有 `DOT05/06/07` |
| 原版 1.19.3 | `C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV` |
| 脚本 + 备份 | `C:\Users\XIANGZIYUAN\hoi4lint\` |
| 日志 | `Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log` |

生效 `replace_path`：history/countries|states|units、common/bookmarks|resources|ai_strategy(_plans)、events、
common/decisions|countries、map/strategicregions|supplyareas。
⚠ `common/national_focus`、`continuous_focus`、`gfx` **不在内**（同名空文件是必需的屏蔽开关）。

## 3. ⭐ 工作区是「活的」文件系统

- ⚠ **会被外部副本整份覆盖，已多次回滚掉我做过的事**（含 MEMORY.md 本身）
  ⇒ **任何「我做过的事」必须先 grep/ls 核实，绝不凭上下文记忆答复用户**。
- ⚠ 文件会被**合并改名** ⇒ 校验脚本**禁止写死文件名/固定计数**，按内容特征定位。
- ⚠ **外部进程会并发插行/截断文件** ⇒ 动手前**先备份**。
- 扫描排除 `.backups\`、`备份文件BY Ruka\`、`desktop.ini`、`gfx/_convert_log.txt`。
- `game.log` 报 **Loaded 11507provinces** 才是本 MOD（13414 = 原版地球）。

## 4. NAT 地图与机制现状

| 项 | 值 |
|---|---|
| NAT州 / 六族州 / ABY 州 / HIP 州 | 61 / 43 / 6 / **0** |
| 六族 tag | `NCP 沃陆之邦` `NCE 回声之子` `NPS 流泉之众` `NSC 悬木人` `NFF 花羽会` `NMN 烟谜主` |
| 自治州 | `autonomy_NAT_State` =「竞逐之盟」，`common/autonomous_states/DOT_Puppet.txt` |
| 两变量 | `NAT-ABY-Index`（侵蚀，开局 40）、`MVK-Prestige-Index`（恩情，开局 50）—— **名不可改** |
| 档位 flag | `NAT_ABY_T1..T7` / `NAT_MVK_T1..T7`（仅供 scripted loc 显示） |
| 深渊战况 | `NAT-War-Index` 0/20/40/60/80 → `NAT_War_Tier_Calm…Collapse` 5 档 |

**铁律**：①改两变量**必须走宏**（`NAT_Abyss_Add/Sub_*` 粒度 Add=1/3/5/8/10/12/15/20/25/30/40、
Sub=2/3/5/7/8/10/12/15/20/25/30；`NAT_Grace_Add/Sub_*` 只有 3/5/6/8/10/12/15/20/25/40，**无 8 档 Sub**）；
②动态修正直接 `enable = { check_variable = { X > N } NOT = {...} }` 读变量，区间互斥 + 首档 `has_variable` 守卫；
③三终局互斥 `NAT_Focus_Convergence_Final` / `Covenant_Final` / `Embers_Final`。

### 4a. 仪表盘
显示位置 = `NAT_Decisions_desc`（容器 `NAT_Decisions` = 归火圣夜巡礼）末尾，追加两变量当前值 +
`[NAT_abyss_tier_mods]` / `[NAT_grace_tier_mods]`。两个 `defined_text`（各 7 档 + 兜底，**直接读变量**，
`text` 块**首个 trigger 为真者胜出**）。⚠ **`NAT_Decisions` 必须有同名 category 声明**否则玩家看不到分类描述。

### 4b. ⭐ 运行时接线（判活铁律）
**静态校验全绿 ≠ 机制在跑。判活看 `add_dynamic_modifier` 有没有被调用**（`enable` 只在挂载后生效）。
**⚠ `on_actions` 跨文件叠加**（同名钩子合并）⇒ 挂载点缺失是**静默**的。
判据：`grep -rn "NAT_Abyss_Tier_\|NAT_Grace_Tier_\|NAT_War_Tier_" <MOD> --include=*.txt | grep -v dynamic_modifiers/NAT_dynamic_modifiers.txt`
⇒ **空 = 从未挂载**。10-12 已在 `common/on_actions/DOT_on_actions.txt` 的 `on_startup` 补齐恩情初值 50 +
**19 个 `add_dynamic_modifier`**（7 深渊 + 7 恩情 + 5 战况；挂载集合 == 定义集合）。机制已迁 decision。

### 4c. 六块部族异议树
- **放射模板（六组同构，以 `NAT_Plenty_Dissent_Sprouts` 为准）**：每族 1 根 + 9 个；
  **9 个非根全部 `relative_position_id = <族根>`、`prerequisite` 也只有族根**。
  槽位（族内第 n 个，n=2..10）：`2:(-1,1) 3:(+1,1) 4:(-2,2) 5:(0,2) 6:(+2,2) 7:(-2,4) 8:(-1,3) 9:(+1,3) 10:(+2,4)`。
  同层横距恒 ≥2、层间 y 距 1。**不是** 1-2-3-4 金字塔（更早的旧方案，已作废）。
- **双参照系（14:15 轮口径，覆盖全链式）**：用户要求整棵子树挂同一参照系。
  `NAT_Promote_Natlan_National_Identity`（绝对 40,1）子树 **23** 个、
  `NAT_The_Great_Unity_Of_All_Fires`（绝对 40,11）子树 **7** 个，零重叠，子树外 115 个不动。
  30 个节点 `relative_position_id` 统一指向参照系，`x/y = 绝对 − 参照系绝对`。
  ⇒ **铁律：参照系必须是自己的【祖先】且是无 `prerequisite` 的根**（才有唯一绝对坐标）。
  现状：**89 个直连自身前置 + 25 个改挂子树参照系**；六族根坐标 `NCP(50,2) NCE(58,2) NPS(66,2) / NSC(50,14) NFF(58,14) NMN(66,14)`。
- 前缀 `NAT_Plenty_` / `NAT_Echoes_` / `NAT_Springs_` / `NAT_Canopy_` / `NAT_Flower_` / `NAT_Nightwind_`。
- **共享门槛双通道**（树被 7 国共用）：`OR = { NAT = { check_variable = { MVK-Prestige-Index < 50 } } check_variable = { MVK-Prestige-Index < 50 } }`
  + `NOT = { has_country_flag = NAT_Dissent_<TAG>_Independent }`。
- **两向旗标**：根国策给 NAT 与该族都写 `NAT_Dissent_Council` + `NAT_Dissent_<TAG>`。
- 恩情降幅第 1–2 层 `-5`、第 3–4 层 `-10`，**走 `NAT_Grace_Sub_*` 宏**；部族强化按层递增 PP/CP/稳定/战争支持。
- 决议组 `NAT_Dissent_Decisions`（同名分类放 categories + decisions 两处是**原版惯例**，引擎会合并）：
  `_Overture`(25) → `_Self_Rule`(40) → `_Severance`(60)，全 `fire_only_once`、全 `NAT_Grace_Sub_5`。
  **编号铁律：第 k 阶段写 Step(k+1)、读 Step(k)**。图标用 `generic_political_rally2` / `generic_army_support2` / `generic_independence2`。
- 分宗 = 置 `_Independent` 旗（两边都写）+ **同步先 `end_puppet`** + `NAT = { country_event = { id = NAT_Event.70X days = 2 } }`。
  **顺序是宣战能否触发的根因**（`end_puppet` 晚于 event 就静默失效）。另配 6 个 `_Recapture` 兜底宣战决议。
- 事件 `NAT_Event.700..705`：`major = yes` + `is_triggered_only = yes`，option 里
  `declare_war_on = { target = <TAG> type = annex_everything }` + `add_war_support = 0.05`，带 `exists` / `has_war` 守卫。

### 4d. ⭐ 效果扩充三层（10-12 下午，任务 #86）
三批共新增 **107 个民族精神 / 591 条 modifier / 340 条 loc**，全部零非法：
- **批1 部族树 54 个非根国策**（`NAT_{Plenty,Echoes,Springs,Canopy,Flower,Nightwind}_*`）：
  原先是**同一个模板**（只有 PP/CP/稳定/战争支持/人力），现每个国策按名字语义配
  **专属精神 + 专属即时效果**。效果**双通道下发**（纳塔本体 + `<TAG> = { }`），
  因六团树由纳塔与部族共享，单发只给一方是错的。
  例：夜行封锁→`night_spotting_chance`+`army_attack_factor`；涂鸦自守→补给四项；
  高塔自持→`air_detection`+`production_speed_radar_station_factor`；谷仓私账→`consumer_goods_factor`。
- **批2 30 个「归火圣夜巡礼」决议**：原文件里**每个决议都写着被注释掉的效果意图**
  （`# add_manpower = 0.15`、`# add_trade_efficiency`、`# add_agricultural_efficiency`…）。
  已把这些意图**实装为限时精神**（`days = 180~365`，与决议冷却期一致）。
- **批3 23 个关键剧情事件**（`NAT_Event.1/5/7/9/10/12/17/18/20/26/31/34/37/38/41/46/50/62/63/69/70/72/37/40`）：
  按叙事补 option 效果 + 限时精神（如「纳塔誓言的回响」「焚渊誓言」「终极决斗的余威」）。
- 生成器：`hoi4lint\task86_spec.py` / `task86_dec_spec.py` / `task86_ev_spec.py` /
  `task86_modcn.py`（modifier→中文名）+ `task86_apply*.py`（落地）+ `task86_verify{,2,3}.py`（校验）。
- 备份 `hoi4lint\backup_task86\`（decisions/events 为原始，ideas/loc 为分批中间态）。

### 4e. 深渊纳塔树（10-12 新增，26 国策）
- 位置纳塔树**右下方**，**8 层 1/4/3/5/2/5/4/2**，门槛 `check_variable = { NAT-ABY-Index > 100 }`（全部 26 个）。
- 前缀 `NAT_Abyss_`；终局 `NAT_Abyss_Become_The_Abyss_Natlan` → `set_politics = { ruling_party = fascism }`
  + `NAT_Abyss_Set_Leader_Gustot` + `add_ideas = NAT_Abyssal_Natlan_Core` + 吞并 HIP + 对六族宣战。
- 5 个宏（`common/scripted_effects/NAT_Neo_effects.txt`）：`NAT_Abyss_Set_Leader_Gustot` /
  `NAT_Abyss_Natlan_Absorb_HIP`（打 `NAT_Abyss_HIP_Absorbed` 旗让 `NAT_decisions-03` 失效）/
  `NAT_Abyss_Natlan_Purge_Tribes` / `NAT_Abyss_Natlan_Declare_Neighbor_Wars` / `NAT_Abyss_HIP_Offensive_Blocked`。
- 24 个 `NAT_Abyssal_*` 民族精神，四级资源效率递进（`production_oil_factor` 0.15→0.20→0.30→0.45，
  终局 0.50；`fuel_gain_factor` 0.20→0.30→0.45→0.60，终局 0.70；`production_lack_of_resource_penalty_factor` −0.15→−0.80）。
- 领袖：`create_country_leader { name desc picture expire ideology traits }` + `add_country_leader_trait`
  （原版**不存在** `add_country_leader` / `promote_country_leader` / `remove_country_leader`）；
  `picture` 用 `GFX_portrait_NAT_Gustot`（原版用 GFX 名）；特质声明在 `common/country_leader/DOT_NAT_country_leader.txt`。
- ✅ **已补** `GFX_portrait_NAT_Gustot` SpriteType（`interface/DOT_Leader.gfx` 末尾，贴图
  `gfx/leaders/LY/Azhdaha.dds` = 深渊之龙，与古斯托特身份最贴）。

### 4f. 当前规模
国策 **171**（145+26）/ 决议 **69** / 事件 **88** / 民族精神 **205**（+107）/ loc **1573 键**。
校验脚本 `hoi4lint\nat_verify_six_tribes.py`（A–G 七段）+ `task86_verify{,2,3}.py`（效果扩充三批）；
备份 `hoi4lint\backup_nat_six_tribes\`、`backup_abyss\`、`backup_task86\`、`.workbuddy\memory\backup_*\`。

## 5. 制作方法论 → 见 `DOT_制作手册.md`
布局（容量受限 Kahn 分层 CAP=17 / 38×32 / 比例 1.188）、loc 去重判据、图标产线（v7+v4）参数、
TNO 版工具链顺序、通用调试方法论全部在该文件。两条最易忘：
- **旧 loc 一律不删**；正则统计前必须 `.replace('\r\n','\n')`。
- 布局先诊断再动手（量化每层节点数/跨度/空洞），别盲加旋钮。

## 6. ⭐ HOI4 语法铁律（已对原版 1.19.3 逐一取证）

**通用坑清单已下沉到技能 `hoi4-mod-bug-triage` 与手册 F 节，这里只留本项目高频踩的**：
- && **modifier 中文显示靠两套 loc 键**：`<modifier>_tt` = ` $MODIFIER_<大写>$: $RIGHT|+=%1$`
  与 `MODIFIER_<大写>` = 中文名。tooltip 里逐项列修正写 `[xxx_tt]` 引用。
  && **`$MODIFIER@xxx@$` 语法不存在**（原版零处，别用）。
- && **1.19.3 没有** farm / power_plant / radar_building / reconnaissance 四类修正。
  真实拼写：`production_speed_radar_station_factor` / `recon_factor` /
  `production_speed_industrial_infrastructure_factor`；农业语义用 `monthly_population`。
- **吞并 = `annex_country = { target = X transfer_troops = yes }`**；`annex = X` 全原版无此写法。
- **脚本里 `set_autonomy` 键名 `autonomy_state`**；**history/countries 里是 `autonomous_state`**。
- `end_puppet = <subject>` 在 overlord 作用域内调用；`is_subject_of = <tag>` 合法 trigger。
  & **必须先 `end_puppet` 再宣战**（附属国不能对宗主宣战）。
- `has_idea`（单数）合法，`has_ideas` 不存在；`white_peace = { tag = X }` 合法，`end_war` 不存在。
- `set_cosmetic_tag = <纯国家 tag>` 合法（原版 11 处）= 还原成该国自身 ⇒ 自写审计脚本会误报。
- 决议 `icon = <裸名>` ⇒ `GFX_decision_<裸名>`；分类 ⇒ `GFX_decision_category_<裸名>`（**两套命名空间**）。
  & `generic_political_negotiation` / `_military_training` / `_political_summit` 全库无 SpriteType（既存坏图标）。
- loc 值内只允许 `\n` 与 `\"`；**值不能真跨行**。
- 已移除语法：`add_timber` / `add_supply` / `add_to_mobilization` / `limited_annex` / `national_independence`。
- on_actions TAG 钩子只有 `on_daily/weekly/monthly_<TAG>`（**无 `on_quarterly`**）。`add = 1` 是触发器不是效果。
- && **原版 `common/effects`、`common/triggers` 目录不存在** ⇒ 词表只能靠 grep 真实目录取证。
  原版全库 466MB 扫描会 SIGTERM 超时 ⇒ 只扫 `common/ideas` + `common/decisions` + `common/units`。
  已产出 `hoi4lint\vanilla_modifiers.json`（637 条白名单）作为新效果的**硬约束**。

**其余高频坑**：决议必须嵌在 `XXX_category` 内（层级按括号深度）；`check_variable` 的自动 tooltip
要找同名 loc 键；「图标出不来」以 error.log 为准（静态扫描 ~500 假阳性）；
抓 focus 边必须从根正向 BFS 只取 `prerequisite` 块内的 focus；
模型绑 `.gfx` + `.asset` 且建筑 mesh 是 Y-up；`heightmap.bmp` 是 4096×2048 8bpp。

## 7. 遗留 / 已知未修

- **NAT 剧本尚未进游戏验证**（只静态层 + 交叉引用）。重点复核：`end_puppet` 对 `autonomy_puppet` 的实际表现、
  `NAT = { check_variable }` 跨作用域取值、mission 倒计时、19 个修正是否真挂上、
  `create_country_leader` 运行时换领袖表现、`every_neighbor_country` 内 `THIS` 作用域行为。
- **`GFX_portrait_NAT_Gustot` SpriteType 未创建**（古斯托特头像缺失）。
- 旧 33 决议中 **25 个 `GFX_decision_*` 图标全库无声明**（显示空白）——按「禁止恢复」只新增不改旧。
- 分类文件里 `NAT_Tribe_Deep/Rift/Grand/War/Ceasefire/Council` 六个分类对应容器在回滚后基线中不存在。
- `ABY_focus.txt` = 0 字节是用户删除的废弃物，**不动**。
- 7 个 `add_ideas` 指向 focus id；194 处 `\N` 转义（非 NAT 文件）。
- `events/LYY_*`、`common/country_leader/LYY_traits.txt` 中文注释编码彻底损坏（U+FFFD，最早 backup 即坏）⇒ 原文永久丢失。
- error.log 里 `add_tech_bonus: Unknown technology category`（MOT/RAG/SAN/SNE/NAT events）为既有问题，待单独处理。
- **GUN 吞并他国 state 已主动禁用**（用户 10-13 要求 # 注释）：`GUN_Decisions.txt` L738 `transfer_state_to = GUN`
  与 `NewMOT_Knights_event.txt` Knights.169–175 共 7 行 `GUN = { set_state_owner = 94/120/26/21/118/113 }` 及 `annex_country = { target = MHL }` 已注释。
  未动 `GUN_Build_*`、Knights.44（他国吞 GUN）、Knights.204（GUN 战败吞 MHL，疑似 scope bug，见 2026-10-13 日志）。
