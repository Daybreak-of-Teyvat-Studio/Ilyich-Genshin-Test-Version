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
- **模型 BUG（10-14 新浮现，待修）**：①V3 胡桃/可莉头部白色方块；②原胡桃无头发、可莉无身体；③`gfx/models/buildings/factory.mesh` 过小（需 +1/3）且外圈黑色脚手架需删。
