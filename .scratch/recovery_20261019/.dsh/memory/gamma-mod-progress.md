---
name: gamma-mod-progress
description: 提瓦特黎明 Gamma mod 的至冬重划/合并/VP 进度、beta→gamma id 迁移 v2、崩溃排查（10-10
  已定位：四张地图文件被毁 + 317 两行坏行 → MAP_ERROR 弹窗 → release 崩）
metadata:
  node_type: memory
  type: project
  originSessionId: sess_3c421fb8-e84d-47d4-a44c-53452b380660
---

# Gamma mod 进度（截至 2026-10-18）

## 当前基准
- **689 州，1-689 严格连号零缺号**（10-18 批：11 个州被合并删除 + 简单迁移补号；此前 700 州）。省 4698、VP 285、战略区 1-9 连号（3 个旧区 + 蒙德 6 个新区）。
- **10-18 蒙德批次**（备份 `.backups/mond_merge_20261018_235920`、`fill_gaps_20261018_235935`、`mond_regions_20261019_000001`）：
  - 合并 8 组删 11 州：`413+422=422`、`453+467+469=469`、`505+524=505`、`28+381=381`、`382+390=382`、`400+411=400`、`429+421+427=421`、`450+452+460=450`；引用迁移 9 个脚本文件（decisions/focus/trigger/event）+ capital；buildings 569 行改列；airports/rocketsites 键并集。
  - 简单迁移（fill_state_gaps）：690→524、691→467、692→460、693→453、694→452、695→429、696→427、697→413、698→411、699→390、700→28；**工具漏迁 airports/rocketsites 键**（11 个旧键滞留 690-700），已手工重命名补齐（见 gamma-tool-suite 记忆）。
  - 新建战略区 4-9：4 风啸山坡 46 省、5 苍风高地 25、6 坠星山谷 48、7 明冠山地 54、8 风息山 39、9 龙脊雪山 44；从 Region1 移除 256 省；weatherpositions 每区 2 条；`DOT_STRATEGICREGIONS_04-09` 改名，02/03 旧名清成 `*`。
  - VP 11 条：105(20) 丘尔德里克、462(10) 登山营地、246(25) 忍冬之树、1513(15) 芬德尼尔之顶、3732(10) 星荧洞窟、811(10) 自律守护机关、2271(20) 无相之冰、964(25) 阿贝多的实验营地、3639(20) 腐殖之心、473 25→15 山脊守望、3565(25) 晨曦酒庄；RAG 首都本就 =500（p3565 所在州），无需改。
  - 州名：501 登山营地、510 达达乌帕谷。
  - **丢名提示**：被并州 467「北风领」并入 469「奔狼领」，北风领名字未保留（用户未指定，待定夺）。
  - 双副本：部署副本此前整体滞后（5,835 文件旧于仓库，如 ideas 停在 10-15），已整体镜像同步，现 0 文件差异（仅副本多 40 个头像素材）。
- **10-17 收尾清理**：simp_chinese `DOT_state_names_gamma_*.yml` 删除 50 个孤儿 `DOT_STATE_701-750`（全是 `*` 占位，来自已删海州段）——双副本同改、哈希一致、`.backups/dotstate_orphans_20261017_172527`；删后 `check_states` 的 F 组只剩已知 english 重复 VP key。同时把 `check_brackets.py` 读取固定 UTF-8（v2.23），Windows 默认 cp936 不再误报。
- **702 州时代记录**（历史）：10-14：帮手夜里 707/708/709→89/90/94；合并 ABY 62+63+65+66+67→62，尾部 703/704/705/706 简单迁移补 63/65/66/67；新建战略区 46 马斯克海 8 省（备份 `.backups/mega014_20261014_220448`）；省 8021；SNE 65 州；buildings 终版重整 0 违规；check_brackets 全过；check_states 仅剩已知 english 重复 key
- **★ 10-15 崩溃事故（已破案并修复）——根因 = 战略区 id 不连号**：debug 于 10:22/10:42/11:13/11:15 反复 ACCESS_VIOLATION、error.log 零 MAP_ERROR、零州/建筑报错，就崩在地图加载末尾（game.log 永远停在 `defines loaded`，从不出现 `Loaded N provinces`）。用户断案关键：「合并前能进游戏，问题出在合并和战略区更改上」「是地图的问题，对比地图文件就行」。**实测二分（自启动游戏验证，每次 ~2 分钟）**：区域 1 恢复 + 删区域 46 → 能进；区域 1 干净 + 区域 46 存在 → 崩。**真因：我给新战略区用了 `id=46`（抄 Beta 同名区号），而原版 304 区、Beta 70 区全是 1..N 连续无空洞——id 数组被按 1..max 遍历 → 2-45 空洞 → 越界静默崩溃。改成 `id=2` 后立刻能进（实测 150s 无崩溃，game.log 出现 `Loaded 8022 provinces` + `Launching SINGLEPLAYER-game`）。铁律：战略区号也必须连号。**
- **同批发现并修复的其它损伤（我 mega014 脚本的行尾 bug）**：`t.replace('\n', nl)` 陷阱把三个地图文件的行尾写成 `\r\r\n`（双 CR）——`DOT_Strategicregions_01.txt`（58,291B→修回 50,120B）、`airports.txt`、`rocketsites.txt`（各 695 处）→ **这三个是 nudge 报「地图定义错误」的根源**；已全部修成单 CRLF。另修 `DOT_state_names_gamma_l…yml`/`NCE - Children_of_Echoes.txt`/`62-State_62.txt` 的 LF-only → CRLF（双副本）。全 mod 现已 0 处 CRCRLF。**遗留**：~155 个旧州文件是 LF-only（历史遗留、游戏能读，属卫生问题，未动）。
- **buildings.txt 权威重整（10-15 补做）**：合并时漏了"被并州行改指存留州"——139 行需改（其中 63/65/66/67→62 各 31 行=124 行）、40 条超配 SL 删除；跑 `tools/rebuild_buildings_final.py` 一次到位，**终验 0 不符**（s62=115 行、63/65/66/67 各省内归位、ABY 坐标行零残留）。
- **新战略区现状**：文件 `DOT_Strategicregions_02.txt`（`id=2`，name 键仍是 `DOT_STRATEGICREGIONS_46` → 显示名「马斯克海」；loc 里 `DOT_STRATEGICREGIONS_02`=风啸山坡 未占用）、8 省升序（860 1531 2282 3544 4681-4684）、含 naval_terrain=water_shallow_sea + 12 段全年 weather；`weatherpositions.txt` 加了 `2;…` 两条。**待用户定夺**：名称是否跟编号走（02=风啸山坡）还是保「马斯克海」。
- 非致命遗留：`map.cpp:1932 Map invalid X crossing. Please fix pixels at coords: 4095,480`（历史遗留、非崩溃主因）；frontendgamesetupview 一批 UI 缺项（旧债）
- 至冬 65 州里只有零星命名/VP：320凝露镇、312巡猎者木屋、7海屑镇、**281生栖树沼（10-13 更名，原焰羽谷）**、**256奥古洛夫镇（10-13 新）**、212曙光车站、186至冬宫、228【冬契军】总部、260科洛列夫茨基剧院、178格鲁波夫、209至冬堡、321凝露镇——**其余基本为空，是后续批次的富矿**
- 旧→新州号映射文档：`docs/州号变动_20261007至冬重划.md`；分组在 `tools/zd_division.json`

## ★★ 崩溃根因深挖（10-10 深夜，debug 全程日志破译）——地图定义错误 4 类
**英文弹窗原文**：`Failed to load the map / Some errors are present in the map definition and have been logged to error.log`。release 在弹窗后 abort（丢日志尾巴）；**debug 点掉弹窗能进游戏，日志完整**——所以"只能debug打开"。**修复=清掉地图定义类错误**。

**四类（来自 23:09 debug 全程日志，共 371 条）**：
| 类 | 条数 | 定位 | 机制 |
|---|---|---|---|
| `strategicair MAP_ERROR` | 126 | 42 州（41 海州+317） | 引擎要求每州有 air/rocket/gun 选址；选址=该州 spawn 行（air_base 等）的坐标落点 |
| `mapbuildings:679` not over land | 9 | 317×8（同坐标在水上）+463×1 | 行坐标落海 → "ignoring instance" → 无选址 |
| `mapbuildings:716` not within state | 111 | 约40州（清单在 tools/dig2_out.txt） | 行坐标落进别州 |
| `mapbuildings:634` invalid arguments | 125 | buildings.txt 40753-41001 | 尾段每行间多一个空行（\r\n\r\n） |
**关键事实（推翻旧猜想）**：①airports.txt/rocketsites.txt 内容与 MAP_ERROR **无关**（13:09 空文件 vs 23:09 满文件报错一样；它们是引擎从行**派生**的，实证 beta `1={1073}` = beta s1 air_base 行所在省）；②**beta 的 700-740 全是陆地州**（省全 land），gamma 的海洋州是 gamma 独有构造，**无 beta 先例**；③海州 manpower 全 0 = 设计正确（"has no people" = 引擎例行提示）。

**10-10 深夜已修（双副本，备份 mapfix2_20261010_233x / revert_sea_20261010_235155）**：120 行坐标挪进声明州陆地（317×8 挪到 (1805,1379) 省2978；其余挪到州内最近 interior 点）；删 125 空行 + 去尾换行（原版/beta 文件结尾均无换行）；**海州补行试验=已证伪并撤销**（23:47 run 实证：317 三条 MAP_ERROR 消失 126→123 ✓ 但海州 123 条仍在——引擎要求选址行落在**该州自己的陆地省**，海州无陆地=结构性无解；补的 328 行反而添 328 条 :716，已撤——buildinggs 回到 40876 行）；海军：INA cru_2 变体重命名 `Sumeru_Cruiser_2_Class`+2 舰同步、FAV heavy_2 删 `front_1_custom_slot`（**23:47 run 显示这两处修改均未解决其目标报错——机制仍未破译**）。

**★ 海州裁撤完成（10-12 深夜，用户拍板方案 B；10-13 更正收尾）**：从 hoi4.exe 挖出弹窗真身——`MAP_LOADING_ERROR_*` 紧挨 `IsMapInGoodState` → **弹窗 = IsMapInGoodState 检查失败**，输入 = 全部 `MAP_ERROR:` 前缀日志。机场选址须落本州境内陆地省 → 无陆地海州永远报警 → 删除全部 41 个海州（=原版式）。**⚠️ 教训（用户点名批评）：删州必须立即重编号闭合空缺——"1-N 严格连号"是铁律（记忆里本有却未执行）**：我当时留了 709-717/719-750 空号还把 718 卡中间，连 debug 都进不去；用户找的帮手把 **718→709 重编号**修好（当时 709 州、1-709 连续零缺号；后续 10-13 夜帮手又做 707/708/709→89/90/94，10-14 我合并+补号 → 现 702 州）。**10-13 我清理了重编号残留**（双副本，备份 fix718_20261013_123231）：NCE 首都 `718→709`、airports/rocketsites 键 `718→709`、709 州文件 name 键 `DOT_STATE_718→DOT_STATE_709`、loc `DOT_STATE_709=回声之子`、`DOT_STATE_718=*`。**现行铁律补充：任何州删除/新增后必须让 1-N 连号，且同步 ①loc 键 ②airports/rocketsites 键 ③州文件 name 键 ④capital/脚本引用 ⑤buildings 行；补号只准「简单迁移」（尾部补号），严禁全量迁移级联重排（见 [[state-renumber-simple-migration]]）。**
删海州同时迁移的 7 处引用（按州文件注释原号全表）：**730→301 天空岛**（Space Program + ABY_Event）、**731→300**（VAN×2）、**710→583**（ANR + LYY）、**852→695、736→294**（INA_Focus prioritize）。airports/rocketsites 已清至 709 行。

**★★★★ 州文件注释 = 644 州完整"原号→现号"对照表（10-12 发现，万能工具）**：每个州文件第 3 行 `name="DOT_STATE_N" # name="STATE_老号"`——**这是历次重划的权威映射（10-07 那次）**。六名字全验证：859→570 知比山、858→136 茂知祭场、851→254 望泷村、855→574 天云峠、854→636 无想刃狭间、852→695 蛇骨矿洞。海州段：709→718、710→583…740→290…750→274、843→72、844→11、849→2、850→318。**全表存 `tools/find_was_numbers_out.txt`——此后任何"旧号引用迁移"先查它。** 遗留：`history/units/MHL_2.txt` L398 `location = 2463 # 715`（715→322；value=2463 属"DVA 部队 location 待给新目标"同族，待用户精对应）。

原版铁律：原版无任何全水域州；湖省并入陆州（118/126）；海省 3133/3133 全部无州。

**★ 州号搬移的 id 关联迁移缺口（用户点名，10-12 部分执行）**：补号搬移时只搬了州内容，**loc 键和脚本引用的数字 id 没有跟着搬全**。
- **六名字已转移（10-12 已应用，双副本，备份 names_refs_20261012_232457）**：知比山→**570**（TSU 鹤观陆地州，其文件备注保留旧键 `# name="STATE_859"`；钢13/铬11/有工厂，完全对得上）、茂知祭场→136、天云峠→574、无想刃狭间→636、蛇骨矿洞→695、望泷村→254；六个海州键（740/741/744/745/747/748）清回 `*`。**每个名字现在各只有一份、全在陆地州键上**（5 个陆地副本原本就在，570 为本次新写）。
- **740 脚本引用 23 处 → 570（同步应用）**：DOT_Resources×5、KNA×1、VAN_decisions×1、DRA×1、FAV×3、LAW×2、NewMOT×8、ANR×1、VAN_scripted_triggers×1——"先放在陆地州上"，等用户回头对应具体正确州。
- **"building类"效果块对齐（10-12 二轮，备份 effect_scopes_20261012_233234）**：`DOT_Resources.txt` 16 个资源开发决策中，9 个决策的效果块裸作用域（`N = { set_state_flag / add_resource }`）还挂着旧号——已全部对齐到各自 owns_state 号，共 **27 处**：4→229、2→266、3/1→133、13→435、12/39→570、39→570、51→130、56→156、41→570。关键证据：Spring/Crystals 两决策的 owns **早已是 570**（用户此前改过），效果块滞后 = "没跟着走"。现全部 16 决策 = owns = highlight = 效果号（唯 Use_Big_Tree：highlight 133 ≠ owns 229，保留待用户精对应）。
- **未动待用户对应**：`710`×2（ANR_influence L444、LYY_scripted_effects L128 transfer_state）、`731`×2（VAN_decisions L267、VAN_scripted_triggers L10 列表）；Use_Big_Tree 的 133/229。
- **误报排查记录（勿再追）**：gfx 的 `GFX_goal_DOT_0740`/`DOT_Idea (740).png` = 图片目录号（1-1618）非州号；`map/positions.txt`/`unitstacks.txt` 的 740-748 命中 = 坐标/编号噪声；`province = 741`（LAW_FocusTree_00）= 省级引用（省 741 ∈ 州 444）无辜；state 278-290 的 `# name="STATE_74X"` 注释 = 旧纪元元数据（278=748…290=740，与搬移表吻合）。

**★ 州号搬移的 id 关联迁移缺口（用户点名，10-12 部分执行）**：补号搬移时只搬了州内容，**loc 键和脚本引用的数字 id 没有跟着搬全**。

**仍未解**：FAV light_1 / INA light_2 变体（同为"version 0"报错，变体块与已通过者几乎一致，机制未破译）；X-crossing (4095,480)（4 bmp×4 坐标解释+P2/P3/四色全扫均无线索，挂账）；15 州 too many buildings；首都 3 例（Springvale 等"set capital they dont own"）；trigger/history 类历史遗留（WTT_communist_china、game rule 不存在等）——首都/trigger/history 用户已明确"先记录不动"。

**修复历经（时间顺序）**：08-27/09-23/09-24 四张地图文件被工具毁坏（airports 0B、rocketsites 探针 26B、supply_nodes 3B、railways 0B）→ 已恢复（airports/rocketsites 按 750 州重建=派生物、supply_nodes 127 行）；landmark x2 缺 entity → 已在 gfx/entities/DOT_buildings.asset 补 entity 块（1657 报错已消失 ✓）；317 两行坐标（首轮）。

## 至冬涂色重划（10-07 晚）
- 涂色图在**桌面 `hoi4ra2mod\提瓦特黎明\Gamma至冬省图_双层.png`**（821×527 = PSD 画布，偏移 1562,278，RGBA，5 色，白=透明）；198 州 → 65 州，1125 省全分配、0 未涂、4 个纯水面笔误块忽略
- 名字处置：多数原地保留；格鲁波夫→178、至冬堡→209、凝露镇→321；列车总站落选丢弃（待用户指定新州号）
- 《至冬 PSD》= 桌面 `Gamma至冬省图_双层.psd`（底图=`.ai_gamma_map\分界图层\底图_原版地图_无标注.png`、省界线(中) 透明层、省图=provinces.bmp；同 bbox 裁 821×527 → 像素级重合）；pytoshop 生成

## 合并执行情况
- **已执行（10-07）**：583+603、718+552、567/568→550（连锁覆盖事故已修）、72→70、507→526、735+759=735
- **仍未执行（用户"暂时不做"）**：16+31、822+646、543+586、71+600、525+528

## 尾段布局整理 708↔750（10-09 晚，用户点名）
- 708↔750 内容互换 → **s708 = NAT「分道誓约之地」**、**s750 = 海州**。联动：文件名/id/`name` 键/首都/buildings 第 1 列(35 行)/本地化(键随内容走)/脚本引用。备份 `.backups\swap708_*`
- **未动（用户"先别动其他的"）**：718（NCE 陆州）仍嵌海段中 → 海段 = 709-717 + 719-750
- 小瑕：`DOT_STATE_708:00` 双零版本号（无害）

## beta→gamma id 迁移（10-08 新工程；v1 有缺陷，v2 方法论）
- **活键 = 州文件 `victory_points = { N v }` 实引（237）**；死键 ~263 = beta 旧编号陈旧移植（`DOT_state_names_l` 132 死/`victory_points_l` 143 死 等）；同名+同号=213/221 死、同名+不同号=用户已修正直接采信
- **1314 塔案例**：beta 1314「高塔孤王的遗址」→ gamma 死键；正主 = 用户新建 442「孤王的高塔」（s433）。已修 focustree/ANR/删陈旧键；映射 `tools/beta_gamma_manual_map.json`；副作用：ANR 风王高塔块改对后开局即触发 `DOT_ControlProvince.10`
- v2 必扫模式：`provinces={}`/`path={}`、`controls_province`/`owns_province`、`set_province_name={id}`、`location=`、`province_id`
- v2 工具链：`rebuild_all_v2.py`（桥 v2 → `beta_gamma_bridge.json`）、`migration_v2_final.py`（桌面对照表 xlsx，2843 条）。桥省侧 ✓36 / ⚠仅死键 253 / ✗无名 54；州侧 ✓143
- **⚠ 禁止再盲跑 `apply_beta_to_gamma_ids.py`**；按 Excel 逐行批准、按文件精确替换

## 崩溃排查历史（10-08 上午 → 10-09 晚：state 层已清）
- **10-08 上午部署竞态**：`Loaded 13414 provinces`+成批无战略区/无州 → mod 复制未完成回退原版地图（副本文件 ctime 晚于启动）；数据无损
- **10-09 修**：5 个无效 dockyard（州内零沿海省）；9 处省级 `naval_base` 块错挂（5 搬迁→s384/s150/s237/s405/s489、4 删重复）；全 750 州重扫残余=0
- **判定铁律**：definition.csv 第 5 列 kind、**第 6 列 coastal**（`only_costeal` 建筑依据）；buildings.txt 非零第 7 列合法
- 顺带真 bug：`has_full_control_of_state = X`（单 token，原版实证；`has_full_control_of state`/`has_full_control_of` 都错），69 处已改

## 部署与调试环境（重要）
- **游戏加载 `Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version`（真实目录）**；`dlc_load.json` 只启用该 mod
- **改动务必仓库+部署副本双写**；用全树 hash 比对（mtime 会骗人）；竞态预防：等复制完成（约 2 分钟）或按 `.GithubDocs\DebugTheRepo.md` 把 `.mod` path 指向仓库
- 用户常同时找别的 AI 诊断 → 结论方向可能对但数据是旧日志的，须用最新日志/全量扫描复核

## 启动工具「钢铁ICU」
- **`F:\mod制作\Hoi4ICU.exe`** = 第三方 PyInstaller HOI4 工具箱；很可能是真正启动入口（官方 launcher sqlite 时间戳自 09-23 未变）
- "非 debug 打不开"与 mod 数据问题的区分见上（10-10 已结案为地图文件）

## 待用户拍板 / 待办
- **清理 263 个死键**（已建议待批）
- **253 个"仅死键"地标的正确 gamma 号**——需用户指定
- **DVA 残留**：18 铁路 `path` 块 + `DVA_1936` 十支部队 `location` 现全 = 2463（璃月，可疑）
- **顶住回退的塔修复**：仓库 3 文件（DVA_focustree/ANR/DOT_state_names_l）为塔修复版、副本为旧版——用户未表态
- 718 仍嵌海州中段；海洋 province/state 转移"以后再写"；english 重复 key；ra-notes 开源去留；15+ tag 无地；配色 FROZEN 36 色
- **state 合并必迁清单（10-07 钦定）**：①本地化 ②修正（`state = N` 族）③**奇观**；`docs/待办合并清单.md`
- **铁路/宫殿**：railways 空文件容忍中（恢复需邻接校验）；宫殿 8 座类型齐全但 beta 坐标废（新地图全落海）→ 需重定点

## 关键环境
- Gamma `Daybreak of Teyvat Gamma Version`；Beta `Daybreak of Teyvat Beta Version`（740 州，provinces.bmp 5632×2048 / 11506 省）
- 原版只读 `F:\Steam\steamapps\common\Hearts of Iron IV`（原版 definition.csv 13414 省——识别"回退原版"）
- 日志 `%USERPROFILE%\Documents\Paradox Interactive\Hearts of Iron IV\logs\`；转储 `crashes\hoi4_<时间戳>\`；WER `C:\ProgramData\Microsoft\Windows\WER\ReportArchive|ReportQueue\`
- GitHub CI：`ci-test/test.sh` → `ci-test/Check.py`（大括号/common txt+gui、simp_chinese 引号成对、simp_chinese+english UTF-8-SIG）
- beta loc 事实：beta `DOT_state_names_l` 几乎无 `STATE_` key（仅 4），州名靠 state 文件 `name=` + 中文 loc 反查；beta VP loc 344 省；gamma 279 州有名、501 VP 名（含死键）
- **地形/图层资源**：`.ai_gamma_map\分界图层\` 有 `底图_原版地图_无标注.png`(4096×2048)、`省界线_淡/中/实_透明.png`、`州界线_透明.png`、`州号_透明.png`、`色板_配色表`——三图层同画布 4096×2048

关联 [[gamma-tool-suite]]、[[hoi4-skill-structure]]、[[user-gives-state-ids-for-names]]、[[gamma-map-change-approval]]

## 10-16 批次（蒙德 VP 30 条 + 战略区改名 + 补号 loc 尾巴）
- **战略区改名**：马斯克海 → **马斯克礁**（`DOT_Strategic_Region_Names…yml` 的 DOT_STRATEGICREGIONS_46 键；编号仍是 id=2）。
- **蒙德 VP 30 条已落地**（备份 `.backups/vp_mond_20261016_180614`）：20 个州；**292 改值**（原"骑士团总部"25 → "喷泉广场"10）；其余 29 条新增；3481 西风骑士团总部（50）→ **MOT 首都本就=466，零改动**；loc 全部进 `DOT_Victory_Points_l_simp_chinese.yml`（30 键，BOM+CRLF）；**352 在旧文件 `victory_points_l` 的同名键已同步对齐为"无相之雷"**（避免重复键取错值）。州 466 = 7 个 VP 块（多 VP=多个单对块，与原版/Beta/Gamma 52 州实证一致）。
- **补号 loc 尾巴补完**：`DOT_STATE_703` 的"**遗迹巨像**"按"州名跟州走"迁到 `DOT_STATE_63`，703 置 `*`（704-712 孤儿键全是 `*`，无害留观）。
- check_states 结果：**93 条 = 91 条既有纳塔核心问题（100-172 段，owner=NAT 族但多挂 NCP 核心）+ 2 条 F 项**（DOT_STATE 孤儿 703-712、english 目录 VP 重复键——均既有/无害）；VP 总数 268、capital 零悬空、702 州 1-702 ✓。
- **skill 更正（v2.11）**：旧说法"一州多个 VP 必须写同一行否则互相覆盖"**为误诊已更正**——正确=多个单对块（原版 381 州/Beta 73 州/Gamma 52 州实证）。
- **10-16 晚 第二批 VP 8 条**（备份 `.backups/vp2_20261016_233039`）：1506疗养院旧址(30)、**3223 改名改值**（疗养院旧址15 → 疗养院风神像25）、1451好肉族大锅(5)、748黑日族方碑(5)、3657好睡族大殿(5)、301野猪林(5)、3349导光机关(5)、894导光机关(5)；涉及州 392/427/433/448/511/522，VP 总数 268→275。

## 10-16 夜 大手术（转省+合并+补号+战略区）——已全部修复并通过判官复验
- **战略区**：①新区域「果酒湖」id=3（6 个海省 5719/6886/6937/7104/7293/7776 + **湖心岛 4679**——不加它区域1 会被判 fractioned=崩溃类）；②区域1 改名 **暗之外海**；③区域2 名 马斯克礁。ids {1,2,3} 连号 ✓。
- **转省**：1570→484、{1306,1960,3515}→435、845→500（VP 与省级块随省迁移 ✓）。
- **合并**：510+511+522→510（17 省）；**补号**：702→511、701→522（⇒ **700 州、1-700 连号**）。引用同步：LAW 首都 511→510、airports/rocketsites 键、loc（这批全是 `*` 占位无损失）。
- **buildings 连锁修复（判官法）**：149 行 `not within` → 按报错的 `was` 值写回第 1 列；74 行 `invalid state`（701/702 旧号）→ 按补号映射替换；9 省 `coastal no port` → 补 naval_base_spawn 行；474 州生成点被搬走 → 补回 10 行 SL。**终验：MAP_ERROR / not within / invalid state / coastal / fractioned 全 0 ✓**。
- **我先前 rebuild_buildings_final 的海军吸附口径与游戏不符**（"方格最多数"≠游戏"最近沿海省"），改坏了 14 行；已按游戏给的 `was` 值复原。**该工具的海军吸附逻辑不可信，改州后一律走判官法**。
- 既有噪音（非 mod、无法修）：原版 DLC `14_sea_on_actions.txt` 开局 6 条 `set_state_flag invalid state`（引用原版州号）；`X crossing (4095,480)`；frontend UI 缺项。
- 备份：`.backups/surg_* / refsync / o2_ / port_ / final_*` 多份。

## ★ 判官工作流（10-16 夜确立，改州/省后必用）
**改完州/省后启动一次游戏（debug 到菜单即可），用 error.log 当判官，循环修到全 0**：
- `not within specified state` → 把每行报错里的 **`was 'B'` 的 B 写回该行第 1 列**（B = 游戏按"标记像素省 / 第 7 列省"算出的正确州，比自写吸附算法可靠）；
- `invalid state (N)` → 按补号映射把旧号替换（本次 701→522、702→511 共 74 行）；
- **`coastal but has no port`（崩溃类）** → 该沿海省缺有效港口行；修=把它的海军行（`col7 == 该省`）第 1 列改成现属州，或补一行 `naval_base_spawn`（坐标取 positions.txt）；
- **`MAP_ERROR: no air base site defined for state N`（致命）** → 该州生成点行被"坐标随省走"带走了；修=按该州剩余省份的 positions 坐标补 7×1+anti_air×3 十行 SL；
- **`MAP_ERROR: Naval strategic region X is fractioned! separated: <省>`（崩溃类 / release 弹窗）** → 新建战略区把海/湖省划走后，某孤岛陆省的**唯一邻接省**被划入新区域，它与原区域的陆地连通被切断；修=把该孤省一并划入新区域（本次 4679 = 湖心岛，唯一邻居就是果酒湖的海省 6886）；
- **合并州"建筑相加"会超上限**：5 个州 infrastructure 相加=10 > 上限 5 → `State Error: Trying to set invalid state building "infrastructure" to state #62`（该行被引擎丢弃）。**合并时州级建筑取存留州原值（或 ≤ 上限），绝不相加**；已按存留州原值 2/1/2/1/1 恢复。

**⚠ 工具可靠性警告**：`rebuild_buildings_final.py` 的**海军吸附口径与游戏不符**（它用"3×3 方格内最多数省"，游戏用"最近沿海省"）——本次它把 14 行海军行改坏（如 `14 → 35`、`44 → 434`），并在补号后把正确的 62/65 又退回合并前旧号。**改州后不要再盲跑它；一律走判官法：以游戏报的 `was` 值为准并跑游戏复核。** 另：**buildings.txt 里 `#` 不是合法注释**——助手给 8 行宫殿加 `#` 前缀（`#466;MOT_Palace;…`）被引擎当成 state 0 → `invalid state (0`；去掉 `#` 即修复。尾部空行 → `:634 invalid arguments count`，也要删。

**既有噪音（非 mod、无法修，勿追）**：原版东南亚 DLC `common/on_actions/14_sea_on_actions.txt`（**不在 mod 里**）开局报 6 条 `set_state_flag invalid state`（引用原版州号）；`map.cpp:1932 X crossing (4095,480)`；frontendgamesetupview 一批 UI 缺项。

## nudge（地图编辑器）启动与判读（10-16）
- **启动参数 = `-editor`**（hoi4.exe 里只有 `start`/`-editor`/`--editor`；"nudge" 只是控制台命令名）。
- nudge 对 buildings.txt 的问题**比游戏本体严格**：游戏容忍（只 BUILDING IGNORED）的条目 nudge 会红。所以"游戏能进但 nudge 报错"是正常的紧张关系；**判官仍以游戏 error.log 为准**，nudge 红项按同上三类修（col1 错 / `#` 前缀 / 空行）。
- 注意：nudge 若在已有实例运行中启动会**不写日志**（10-16 实测第二次 -editor 无新日志）；复验前先确认无 hoi4 进程。

## 10-16 其余既有噪音/待办
- **155 个旧州文件仍是 LF-only**（历史遗留，游戏能读，属卫生问题，未动）
- **`MHL_2.txt` L398 `location = 2463 # 715`** 仍未对应（715 已并入他州，与 DVA 部队 location 同族）
- `get_provs()` 类脚本注意：本批 surg 脚本曾误改 18 行（把 62/65 退回 63/704），已撤销——**脚本改完必须逐行核对受影响集合，不能只信脚本自报的"修正 N 行"**。

## 10-17 三个 UI bug（**修复已全部回退，未解决**）
- **选国界面**（国家顺序乱）：`frontendgamesetupview.gui` 旧副本缺 `filters/more_countries/new_content/country_name` + 笔误 `GFX country filter_entry` → 已从原版补块、修笔误、补 `GFX_country_filter_entry` sprite（frontendgamesetupview.gfx）。
- **主菜单社媒图标**（按用户要求不新增按钮）：真因 = `core.gfx` 旧副本缺 `x`（X 图标）等 8 sprite → 已补；我一度新增的 7 个社媒元素已回退（用 Beta 版同名文件恢复）。
- **主菜单左下角 DLC 图标列**：`frontendmainview.gfx` 旧副本缺 `GFX_frontend_banner_dlc051/052`、`GFX_frontend_medal_dlc051` → 已补（dlc052 = Thunder at Our Gates，游戏侧本就 Active ✓）。
- 终验：`Could not find sprite type` / `Could not find "..." in window` / MAP_ERROR / invalid state 全 **0** ✓。其它仍属旧副本、本次未动的界面文件：frontendmainview.gui（社交行结构为旧版）、topbar.gui、nationalfocusview.gui、countrypoliticsview.gui/.gfx、countrydiplomacyview.gui、countrytechtreeview.gui、credits.txt —— 建议后续整轮 version-adapt。
- 备份：`.backups/ui_20261017_000603`、`ui_last`/`prebeta_*`（frontendmainview.gui 已用 Beta 版恢复）。skill v2.21 记入 version-adapt.md。
- **回退（10-17）**：用户实测 DLC 图标列无变化、选国页面全乱 → 5 个 interface 文件已恢复到改前（core.gfx 39863B / frontendmainview.gfx 5348B / frontendgamesetupview.gui 53676B / frontendgamesetupview.gfx 9046B / frontendmainview.gui 16094B，双副本一致）。教训：分叉 .gui 不能直接补原版元素块。
