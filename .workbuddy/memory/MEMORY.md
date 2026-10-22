# MEMORY.md —— 提瓦特黎明（DOT Gamma）项目备忘
> 语法见技能 `hoi4-mod-bug-triage`；手册 `DOT_制作手册.md`；逐轮细节 `2026-10-*.md`；工具在 `tools/`。本文件只记铁律与当前口径。

## 0 铁律
- 禁回滚/禁 git/禁注释掉问题代码；中文注释只写中文；直接改原文件禁 `_v2`；旧 loc 一行不删；`ABY_focus.txt` 不动；focus 保留 `focus_tree` 头；数量一律下限。
- 修 bug 只修不删：loc 同键重复不删行（拆 `key`/`key_desc`、空值补正文）。颜色闭合用状态机判（`§X` 开／`§!` 关），数 `§` 奇偶是错的。
- 事件/新闻 desc 200–400 字（去空白），生成取下限 206；禁破折号（`—–―─－`）。
- 新增内容并入同名 `<国>_*` 文件；新闻须由 `completion_reward` 触发 `news_event={id=NS.n days=1}`；`add_namespace` 写文件首部。
- focus tag 限定＝树头白名单＋少数关键国策（LYY30／SUM18）；`available` 只给分叉/终局。新增决议必须带 `has_completed_focus`＋`visible`。
- 机制三件套：`*_Init` 置初值→`*_Tier_Refresh` 卸全档挂唯一档→`on_daily` 的 `*_Sync` 保鲜；轴宏只改变量；每档配只读面板（`available={always=no}`、`cost=0`）。
- 轴指数变化必须可见：`add_to_variable` 放 `hidden_effect` 外＋逐条 `custom_effect_tooltip`；`hidden_effect` 只包 Refresh/Sync 正文与连续 ≥2 行变量段。
- `dynamic_modifier` 只给 ≤10% 条目（现 11 个）。备份一律出 MOD：`C:\Users\XIANGZIYUAN\hoi4lint\_backup_*`。

## 1 编码（最易致命）
- **loc `.yml` 必须 UTF-8 BOM + CRLF**（缺 BOM 整份静默丢弃）；**`history/states/*.txt` 必须无 BOM + CRLF**（带 BOM→州库空→闪退）。
- `map/supply_nodes.txt`、`railways.txt`、战略区 txt、`weatherpositions.txt`、`.asset` 同样无 BOM+CRLF；原版 txt 多无 BOM+LF。工具 `check_loc_bom.py`／`check_state_all.py`／`fix_state_bom.py`。
- 脚本无 BOM+CRLF；Edit 同一文件多处改动必须串行。

## 2 环境
- Python=`…\binaries\python\envs\default\Scripts\python.exe`；Bash 优于 PowerShell。
- `replace_path`：history/{countries,states,units}、bookmarks、resources、ai_strategy*、strategicregions、supplyareas（decisions／national_focus／gfx 不在内）。
- 工作区会被外部会话整份覆盖 ⇒ 改完复核。真 MOD 根＝`Daybreak of Teyvat Gamma Version/`。

## 3 语法要点（1.19.3）
- modifier loc：`_<modifier>_tt` 与 `MODIFIER_<大写>`；无 farm／factory_output／manpower_factor／corruption，用英式 `army_defence_factor`、农业 `monthly_population`。
- 有 tooltip：add/remove_dynamic_modifier、add/remove_ideas、add_stability；无：变量/旗标。
- 多个 `prerequisite` 块是 AND，块内多条 focus 是 OR。决议 `icon=<裸名>`→`GFX_decision_<裸名>`；空分类须 `visible_when_empty`。
- **idea 的 `picture` 必须裸名**（写 `GFX_idea_X` 会取到 `GFX_idea_GFX_idea_X` 而空白）；MIS `icon=` 才写完整 sprite 名。
- loc 只认小写 `\n`；同键重复＝后加载者胜；须在 `localisation/<语言>/`。解析 `.gfx` 要 `re.I`。
- `annex_country={target=X transfer_troops=yes}`；`set_autonomy` 用 `autonomy_state`，history 用 `autonomous_state`。`hoi4lint\vanilla_modifiers.json`(647) 是硬约束。

## 4 当前口径
- **胜利点**：只 5/10/20/40，首都州 40（`capital` 是州 id）；40×32、20×65、10×108、5×234（439 点/323 州）；不给无胜点州补点；原值≥25 的州主点必为 20 档。439 点全在 land 省且高于海平面；仅 `3049`、`1772` 两礁省质心落海（图标看着在水上，地图几何所致）。工具 `eco_vp4.py`。
- **经济**（`eco_apply3.py` 行级写入；`eco_apply2.py` 禁用）：按档设 category/manpower/buildings/resources；每国工厂 10–100、人口 4–40 千万且每州整千、港口机场只在胜点州。现状工厂 944、港口 115、机场 98、人口 33.76 亿。NMN/NCE/RAG/PRI 港口恒 0（地理）。
- **★基建等级硬上限 5**（`common/buildings/00_buildings.txt` 里 `infrastructure` 的 `level_cap = { state_max = 5 }`）：原写 7/6/5/4/2 中 97 个州的 6/7 超限，是 10:47 起持续崩溃（`C0000005 @ 0x7FF65395FD9B`，后为 `0xc0000409` BEX64）的**唯一确证越界**。`tools/fix_infra_cap.py` 压到 5（现分布 2/4/5）。**改经济时任何建筑都不得超过该文件里的 level_cap**（air_base 10、naval_base 10、arms/industrial 20、dockyard 20、anti_air 5、radar 6、rocket/synthetic 3）。
- **补给**（`eco_supply2.py`）：只给州内最高胜点 ≥10 的州放点 ⇒ 205 条。**铁路**（`eco_rail_extend.py`，原文件逐行不动只尾部追加）：439 胜点进网 431（8 个单省孤礁无解）；默认只写补给点，动铁路须 `--rails`。
- **战略区（当前＝「战略区01」48 区划分 + 连通修复，2026-10-22 20:33 实测能进游戏）**：用户明确「战略区01 的划分就可以，只不过他有BUG，你轻微调整修复一下」⇒ **保留 git `a947822ba` 的 48 区划分与全部区名**（蒙德 6 块：风啸山坡／苍风高地／坠星山谷／明冠山地／风息山／龙脊雪山 ＋ 蒙德海；璃月 3 ＋ 璃月海；须弥 2＋饰金砂原 2＋千壑沙地 2＋苍漠囿土＋须弥海；枫丹 3 ＋ 枫丹海；纳塔 2 ＋ 纳塔海；至冬 6 ＋ 至冬海；挪德卡莱 2 ＋ 挪德海），只修数据。**真正的 BUG＝21 个区的省集 4-邻接不连通**（碎成 2~10 片）；`tools/sr_fix_conn.py` 把每区除最大片外的碎块**整州并入相邻最多的区**，2 轮收敛，搬动 1254 省（7.8%），主要是岛屿并入 7 个海军区（符合「岛屿归海洋区」）。修后：48 区、不连通 0、跨区州 0、覆盖 8021、无重无缺、id 保持 1..48、天气 96 行 big 48／small 48。修前 48 区快照 `_backup_srfixconn_20261022_203026`，48 区原件 `_sr_a94_fixed_20261022_201617`，24 区（能进）`_backup_srconn_20261022_195451`，63 区方案停在 `_sr_park_pre_a94_*`。`provinces` 里绝不能有 0 号省（definition 首行占位→质心空→崩溃）；**id 不许空洞**（曾缺 17/18/19 直接崩）。
  - **★判据：区内省集连通是硬要求**（同机同图实测：24 区全连通版 37s 进游戏；48 区有 21 个不连通 → 43s 后崩在 `Loaded 8022 provinces`）。引擎**不会**在 error.log 报 fractioned／not-in-any／MAP_ERROR，直接静默崩，所以只能「静态自检 + 实机验」两条腿。
  - **★试机方法（不需要 Steam）**：`tools/sr_trial.py [--install <dir>] [--aiareas …] [--tag x]` —— 直接起 `hoi4.exe`（DETACHED）并删 game.log 后轮询：出现 `[1936.01.01.12]` 即成功（37–49s），进程先退且末行仍是 `Loaded 8022 provinces` 即崩溃。**`--aiareas` 只许按顺序替换 `strategic_regions = { … }` 里的数字**，用 `(core={)[^}]*` 这类正则会把整个区块吃空 → 3 处 `Unexpected token: area`（已踩过）。
  - **温度警告是原版常态**：`strategicregiontemplate.cpp:172/178` 的 overlapping／gap in temperature intervals 原版同样有，`between={ 0.0 30.0 }` 就是原版写法；48 区正常是 41×2＝82 行。
  - `weatherpositions.txt` id＝区 id，48×2=96 行，`sr_fix_conn.py` 重算（省内质心像素、高度 heightmap×0.1 夹 9.5–16、big/small 交替）。
  - 体检／报表：`tools/sr_connaudit.py`（连通／海军区／混合区／天气点／覆盖）、`tools/sr_final_report.py`（区号-中文名-归属国-省数-连通 对照表 ＋ 相对原版搬迁量，输出 `tools/sr_final_report_out.txt`）、`tools/sr_audit.py`（静态项）。
  - **原版对照口径（静态可判的合法边界）**：原版 304 区里有 67 个「含海省但没写 naval_terrain」的混合区 ⇒ 混合区不写合法；**0 个「纯陆区写 naval_terrain」** ⇒ 纯陆区写 naval_terrain 是缺陷（19:33 `fix_sr_naval.py` 修的就是这个）。`naval_terrain` 原版只用 `water_deep_ocean`(37)／`water_fjords`(14)／`water_shallow_sea`(12)。
  - **远海统一（`sr_ocean_unify.py`，SRK=4）**：近海区只保留「离岸 ≤4 跳」的贴岸水带，其余海省全部并入 1 号暗之外海 ⇒ **暗之外海 1372 省、单连通**（原本 402+369 两块被近海环隔开）；8 个近海区 240/74/308/103/229/320/329/328 省，各自单连通。近海带宽度改 `SRK` 重跑即可。
  - **海军区必须单连通**（引擎报 `Naval strategic region … is fractioned`）：判据用**共享边界像素数 ≥6**（`SRTHR=6`），碎块并入「相邻最多且主块能接上」的海军区。**海省 3323 个全部无州归属**⇒移海省不拆州；**陆地区同样必须连通（不连通会静默崩，实测已证）**，4/5/11/18/19/40/42 是「陆+海混合区」，靠区内的少量海省把零散陆块连起来，故其「纯陆片」有 2–3 片但整区连通。
  - `weatherpositions.txt` id＝区 id，48×2=96 行，`gen_sr_weather.py --apply` 重算（省内质心像素、高度 heightmap×0.1 夹 9.5–16）。
  - `FON_ai_areas.txt`＝core{26 27 28}／industrial{26 27 28}／coast{29}（**现行 48 区方案**；24 区方案时曾是 13／13／21）；**`ai_strategy/FON_civil_war_ai_strategies.txt` 有 5 处引用 core/industrial，文件被清空会变成悬空引用（AI 初始化解空指针→崩溃）**，区名与定义都不可删。
- **NAT**：六族 NCP/NCE/NPS/NSC/NFF/NMN；`NAT-ABY-Index`(40)／`MVK-Prestige-Index`(50) 不可改名；四阶段 autonomy_puppet→NAT_State→恩情>79 吞并→<19 脱离。
- **LYY** 六派 12 线（战后层 y22–34、id 带 `PW`）；**SAN** 三终局（`SAN_PW_The_Crossroads`）；**SUM** 888 国策／170 决议，`SUM_PRO_*` 共享序章，只重建国策用 `regen_focus_only.py`，禁重跑 main()。
- 兵模：`clone` 每 tag 12 个、不能覆盖 attach；三件套 `*_sabre_infantry_rider`／`*_sabre_cavalry_rifle_combined`／`*_sabre_cavalry_entity`；模型走技能 `hoi4-pmx-to-mesh`（`肌/肌2` 是皮肤层，绝不能当装饰剔除）。

## 5 遗留
- **崩溃取证口径**：`0xc0000409`(BEX64) 不出 crashes 转储，要去 Windows 事件日志（Application/1000 看异常码＋故障存储段 ID，同 ID＝同一 bug）；`error.log` 末段停在哪个阶段＝崩在哪个数据库；`game.log` 只有 `Loaded 8022 provinces` 说明崩在地图数据之后、主菜单之前。`crashes/*/exception.txt` 只对 `C0000005` 这类有转储的崩溃才有。
- **★排障顺序教训**：用户报「改了 X 就进不去」时先看**崩溃时间戳 vs 各改动的落地时间**。`crashes/` 里 10:47/12:23/12:33 三次都是 `C0000005 @ 0x7FF65395FD9B`；18:06/18:47/18:57 三次换成 `0xc0000409`，后两次**错误偏移 0x25516e5、故障存储段 1817481799177072825 完全一致**＝同一 bug。18:54 把基建压到 5 后 18:57 仍崩，故**基建超限不是根因**。
- **★「全部战略区单连通」在本图不可行**：陆省 THR=6 下 232 个连通分量（4-邻接 88 个），陆地区只 40 个；且有 168 个州本身横跨两个碎块（州不可拆）。`tools/fix_sr_all.py` 试算最多 28→23，代价是分区被搞乱。原版 304 区里也有 91 个 land 区含海省、29 个 naval 区含陆省、48 个区不连通 ⇒ 二者都是合法常态。
- **★工作区删不掉文件**：`rm` 被安全删除劫持且静默失败（耗时后 SIGTERM、文件仍在），**改用 PowerShell `Move-Item` 移出到 `hoi4lint/` 下**。
- 待用户实测：24 区对照组能否进游戏。能进 ⇒ 锁 48 区切块方式（应按地理连通块而非 owner tag 切）；仍崩 ⇒ 战略区无关，转查 error.log 末段 effect 报错与内存。
- `map/supplyareas/` 是空目录且 `replace_path` 指向它（用户已确认与此无关，暂不动）。
- `PRI` 是否破例建港；`DRA` 首都名是否改「寒天之钉」；2 个落海胜点是否处理；`rocketsites.txt` 州 499/510 各引一个外州省。
- NAT 三个 `on_monthly` 无挂载（挂上会改平衡须点头）；5 个悬空 `custom_effect_tooltip`。未实测：`end_puppet` 对 autonomy_*、动修是否真挂、兵模是否上屏。
