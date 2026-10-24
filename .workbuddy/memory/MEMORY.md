# MEMORY.md —— 提瓦特黎明（DOT Gamma）项目备忘
> 语法见技能 `hoi4-mod-bug-triage`；手册 `DOT_制作手册.md`；逐轮细节 `2026-10-*.md`；工具在 `~/.workbuddy/workspace/hoi4lint/`。本文件只记铁律与当前口径。

## 0 铁律
- 禁回滚/禁 git/禁注释掉问题代码；中文注释只写中文；直接改原文件禁 `_v2`；旧 loc 一行不删；`ABY_focus.txt` 不动；focus 保留 `focus_tree` 头；数量一律下限。
- 修 bug 只修不删：loc 同键重复不删行（拆 `key`/`key_desc`、空值补正文）。颜色闭合用状态机判（`§X` 开／`§!` 关），数 `§` 奇偶是错的。
- 事件/新闻 desc 200–400 字（去空白），生成取下限 206；禁破折号（`—–―─－`）。
- 新增内容并入同名 `<国>_*` 文件；新闻须由 `completion_reward` 触发 `news_event={id=NS.n days=1}`；`add_namespace` 写文件首部。
- focus tag 限定＝树头白名单＋少数关键国策（LYY30／SUM18）；`available` 只给分叉/终局。新增决议必须带 `has_completed_focus`＋`visible`。
- 机制三件套：`*_Init` 置初值→`*_Tier_Refresh` 卸全档挂唯一档→`on_daily` 的 `*_Sync` 保鲜；轴宏只改变量；每档配只读面板（`available={always=no}`、`cost=0`）。轴指数变化必须可见：`add_to_variable` 放 `hidden_effect` 外＋逐条 `custom_effect_tooltip`。
- `dynamic_modifier` 只给 ≤10% 条目（现 11 个）。备份一律出 MOD：`workspace/hoi4lint/_backup_*`。
- **★所有 WorkBuddy 产物统一放 `C:\Users\XIANGZIYUAN\.workbuddy\workspace\`，家目录根下不再新建任何目录/文件**。

## 1 编码（最易致命）
- **loc `.yml` 必须 UTF-8 BOM + CRLF**（缺 BOM 整份静默丢弃）；**`key: "值"` 不带 `:0` 版本号是合法写法**（原版 11.9 万行如此），别当错误批量改；**`history/states/*.txt` 必须无 BOM + CRLF**（带 BOM→州库空→闪退）。
- `common/ideas|characters|country_leader/*.txt`、`history/countries/*.txt`、`map/supply_nodes.txt`、`railways.txt`、战略区 txt、`weatherpositions.txt`、`.asset` 一律无 BOM + CRLF（BOM 让首行变 `Unexpected token: ideas`/`characters`）。
- 脚本无 BOM+CRLF；Edit 同一文件多处改动必须串行。

## 2 环境
- Python=`…\binaries\python\envs\default\Scripts\python.exe`；Bash 优于 PowerShell。
- `replace_path`：history/{countries,states,units}、bookmarks、resources、ai_strategy*、strategicregions、supplyareas（decisions／national_focus／gfx 不在内）。
- 工作区会被外部会话整份覆盖 ⇒ 改完复核（10-24 丢过 `common/ideas/DOT_CharAdvisors.txt`）。
- **★MOD 根＝`Ilyich-Genshin-Test-Version/Daybreak of Teyvat Gamma Version/`**（`dlc_load.json` → `mod/Daybreak of Teyvat Gamma Version.mod`）。同级 `Ilyich Genshin Daybreak of Teyvat/` 是旧快照（角色文件只 32 个），不要误改。

## 3 语法要点（1.19.3）
- modifier loc：`_<modifier>_tt` 与 `MODIFIER_<大写>`；无 farm／factory_output／manpower_factor／corruption，用英式 `army_defence_factor`、农业 `monthly_population`。`hoi4lint/vanilla_modifiers.json`(647) 是硬约束。
- 有 tooltip：add/remove_dynamic_modifier、add/remove_ideas、add_stability；无：变量/旗标。
- **★可控角色口径**：名单只取萌娘百科各地区页「可控角色」（`char_playable.py`），蒙德整体不参与。三个坑：①角色可能定义在**别国文件**里（`SAN_Gorou` 在 `INA_Characters.txt`）⇒ 判重必须**全局扫 51 个角色文件**，否则 `Multiple character have the tag`；②同名异写归一（`Kaveh=Cavy`、`Kirara=Momoka`），变体 ID 单字母前缀要剥（`SAN_B_Kokomi`）；③同一角色多变体只要有**一个**带 advisor 就算有内阁身份。
- **★内阁顾问体系**：每个非蒙德角色都要有 `advisor` 块，`traits` 只放**一个专属称号特质**（称号英文 PascalCase，如「浅蔚轻行」→`Verdant_Strider`）。槽位六类混搭：`political_advisor`／`army_chief`／`navy_chief`／`air_chief`／`high_command`／`theorist`；后两者 `slot_ledger` 是 `invalid`，**必须显式写 `ledger`**。`cost = removal_cost = 100`、`ai_will_do = { factor = 1 }`、`allowed = { always = yes }`。三件套：`DOT_Char_Title_Traits.txt`(221 条)／`.gfx`／`_l_simp_chinese.yml`；称号表 `char_titles.py`（改称号只改这里再跑 `gen_title_traits.py`）。**同角色两个 `advisor` 块 → `tries to cumulate 2 times the same advisor type`**。
- **★`advisor.idea_token` 只是标识符**：原版大量 token 无对应 idea（`AFG_hares_muzafar`），效果由 `traits` 承担。自定义 idea 类别必须在 `common/idea_tags/00_idea.txt` 注册（未注册→`unknown category`、整份静默丢弃），新增类别**不写 `character_slot`**。
- **★肖像四字段**：每角色 `civilian={large small}` + `army={large small}`，1149 角色零空。`large` 156×210 走 `gfx/leaders/<TAG>/` 现成图，缺了才用 `Backups/`；`small` 优先级＝**cabinet 65×67 → cabinet 156×210 裁 65×67（存 `cabinet/gen/DOT_<名>.png`）→ `DOT_PP/idea_*.png` → **立绘裁 64×64 存 `cabinet/gen/DOT_<名>.png`（裁切框＝0.78×图高、水平居中贴顶，实测通吃半身/特写/全身）→ 立绘是原版 `portrait_europe_generic_*` 的用式大将那张 `cabinet/Undecided.dds`**（式大将＝`history/general/DOT_advisors.txt` 的 `Shiki_Taishou`，全库无同名图）。cabinet 里 `yelan/Yaoyao/xianglin.png` 是斜拍残图（白底大片留白／卡片被切边），已改用 DOT_PP 同名正图。**禁止新建肖像目录/Backups 副本**（`DOT_Chars` 已删）。**角色肖像是全游戏唯一可直接写图片路径、不需 sprite 的地方**；`advisor` 块没有 picture，内阁头像就是 `army.small`；idea 的 `picture` 必须**裸名**。缺立绘去 `.skills/bwiki/`（`icons*/<中文名>头像.png` 256²）→ 3:4 竖切＋元素色渐变；**绝不拿 DOT_PP 放大充 large**。
- **★★`Gunnhildr.dds` 口径（2026-10-24 用户两次拍板）**：`large = "gfx/leaders/LY/Gunnhildr.dds"` 是**有意为之的无名 NPC 占位大图，一律不许动**（现 72 块／144 槽）；但 `small` **绝不能**指 `Gunnhildr.dds` 或任何 `gfx/leaders/` 大图，必须用该角色在 cabinet／DOT_PP 里已有的对应小图；作者原本给这批人配的就是通用无名像（`MOT_Man_Knight1/2/3`、`MOT_Woman_Nun1`、`MOT_*_Citizen*`、`MOT_*_Yurenzhong1`、`SUM_Man_Scholar1`、`LAW 用 Undecided.dds`），**这就是"对应图片"**，别裁立绘造 `DOT_Gunnhildr.png`（已尝试过两轮、均被否）。这 72 人 cabinet／DOT_PP 无一人有专属图。
- **★★造 gen 图前必须先穷举匹配（2026-10-24 用户两次点名）**：`cabinet/gen/DOT_*.png` 只允许在「cabinet 与 DOT_PP 都没有」时才造。匹配三步缺一不可：①**递归**扫 `cabinet/` 全目录（`LYY/`、`VAN/`、`NDK/`、`DVA/`、`FON/`、`KNA/`、`PRI/` 都有小图）；②剥角色 ID **尾号**（`SGD_Candace02`→`candace`、`Cyno02`）与 **`DOT_` 前缀**（gen 名与 cabinet 裸名不比同一层）；③别名表（`Miko→INA_miko`、`Scaramouche→sanbing`、`Nico→idea_MOT_Nicole`、`Rosaria`≠`Rosalyn`）。误造后果：23 张重复图（Candace02／Cyno02／Ying／Nahida_Puppet／Bennett_N／Raiden／Lanyan…）已全部改回现成图、移出 MOD，gen 103→80。工具 `gen_reaudit.py`／`gen_fuzzy.py`／`gen_users.py`／`gen_repoint.py`。
- **★同角色多变体共用同一张小图**：`SGD_Candace02`／`candace02`／`SDH_Candace` 都是 candace，共用一张。归一＝去 TAG 前缀→去变体后缀（`_N/_M/_A/_H/_02/_03/_plus/_commander/_marshal/_puppet`）→去尾号→小写；拼写完全不同的别名再按 `large` basename 分组（`Momoka=Kirara=qiliangliang`、`Buer=纳西妲`）。**裁图前必先查重**：同一立绘只该有 1 个 `cabinet/gen/` 文件（dHash=0 即重复，`gen_dup.py`；共用 84 组、合并 5 个冗余）。KNA 丘丘人各兵种立绘虽同但形象完全不同，**不可互换**；cabinet 与 DOT_PP 混用的 70 组是图源风格选择（DOT_PP 圆头像在 65×67 更清晰），不属重复造图。引用大小写须与磁盘一致（`DOT_buer`→`DOT_Buer`，Linux 会挂）。
- **★cabinet 小图只按角色 ID 匹配，绝不看 `large` 名**（large 多为借图：蒙德 15 个 NPC 的 large 是 `Ying.dds`，按 large 匹配会全配成「荧」）。优先级：ID 原名→归一裸名→别名片（`Momoka→Kirara→qiliangliang`、`Kaveh→Cavy`、`Wanderer→sanbing`、`Heizou→luyeyuanpingzang`）→加任意 TAG 前缀（`ASA_Miko→INA_miko`）。只收 58–74 px 方图。工具 `cabinet_apply.py`／`revert_bad_small.py`。
- **★`country_leader` 块不支持 `visible`**（只认 ideology／traits／expire／desc／id），多变体靠事件 `set_country_leader` 切换。
- 多个 `prerequisite` 块是 AND，块内多条 focus 是 OR。决议 `icon=<裸名>`→`GFX_decision_<裸名>`；空分类须 `visible_when_empty`。loc 只认小写 `\n`；同键重复＝后加载者胜。解析 `.gfx` 要 `re.I`。
- `annex_country={target=X transfer_troops=yes}`；`set_autonomy` 用 `autonomy_state`，history 用 `autonomous_state`。

## 4 建筑 / 奇观坐标（`map/buildings.txt` 是唯一生效文件）
- 行格式 `州id;建筑id;x;y;z;旋转[;相邻海省]`，第一字段是**州 id 不是省 id**；**z 轴与位图行相反**：`row = H - z`（600 行校验误差中位 0.06，`row=z` 是 8.26）；`y = heightmap[row][x] * 0.1`（惯用 9.50）。海省灰度恒 10 ⇒ 灰度 10 判海。
- 写 `spawn_point = nuclear_reactor_spawn` 的 8 个 `*_Palace`，**该行 x/z/y 必须等于本州 `nuclear_reactor_spawn` 行**（精确式 `y = 0.09786518*h + 0.259962`，PIL 序 `row = H-1-z`）。收尾 `fix_showcase_positions.py --apply`（幂等）。
- **英日文地名 loc**：`loc_i18n_build.py` 生成 `DOT_Names_en/jp_l_*.yml`；译名优先 `dataset.genshin-dictionary.com/words.json`，再人工表 `loc_en_fill.tsv`+`loc_extra.tsv`；日文兜底＝opencc `s2t`+自建 `T2JP`。

## 5 当前口径
- **胜利点**：只 5/10/20/40，首都州 40；40×32、20×65、10×108、5×234（439 点/323 州）；不给无胜点州补点；原值≥25 的主点必为 20 档。`eco_vp4.py`。
- **经济**（`eco_apply3.py` 行级写入；`eco_apply2.py` 禁用）：每国工厂 10–100、人口 4–40 千万且每州整千、港口机场只在胜点州。现状工厂 944、港口 115、机场 98、人口 33.76 亿。
- **★建筑等级不得超过 `00_buildings.txt` 的 `level_cap`**：infrastructure 5（曾写 7/6）、air/naval_base 10、arms/industrial/dockyard 20、anti_air 5、radar 6、rocket/synthetic 3。`fix_infra_cap.py`。
- **补给**（`eco_supply2.py`）：只给州内最高胜点 ≥10 的州放点 ⇒ 205 条。**铁路**（`eco_rail_extend.py` 只尾部追加）：439 胜点进网 431。
- **战略区＝「战略区01」48 区 + 连通修复**（10-22 实测能进），保留全部区名与 48 区划分只修数据。**判据：区内省集 4-邻接连通是硬要求**（不连通会静默崩在 `Loaded 8022 provinces`，error.log 不报）。`sr_fix_conn.py` 把碎块整州并入相邻最多的区，2 轮收敛；修后不连通 0、跨区州 0、覆盖 8021、天气 96 行。`provinces` 绝不能有 0 号省；**id 不许空洞**。温度警告（`strategicregiontemplate.cpp:172/178`）是原版常态。
  - **原版对照**：67 个「含海省但无 naval_terrain」混合区合法；**0 个纯陆区写 naval_terrain**。**远海统一**（`sr_ocean_unify.py`，SRK=4）：近海区只留离岸 ≤4 跳水带，其余并入 1 号暗之外海 ⇒ 1372 省单连通。海军区判据＝共享边界像素 ≥6。
  - `FON_ai_areas.txt`＝core{26 27 28}/industrial{26 27 28}/coast{29}；**`FON_civil_war_ai_strategies.txt` 有 5 处引用，区名与定义不可删**（清空→悬空引用→AI 初始化崩）。
- **NAT**：六族 NCP/NCE/NPS/NSC/NFF/NMN；`NAT-ABY-Index`(40)／`MVK-Prestige-Index`(50) 不可改名；四阶段 autonomy_puppet→NAT_State→恩情>79 吞并→<19 脱离。
- **LYY** 六派 12 线（战后层 y22–34、id 带 `PW`）；**SAN** 三终局（`SAN_PW_The_Crossroads`）；**SUM** 888 国策/170 决议，`SUM_PRO_*` 共享序章，只重建国策用 `regen_focus_only.py`。
- **兵模**：`clone` 每 tag 12 个、不能覆盖 attach；三件套 `*_sabre_infantry_rider`／`*_sabre_cavalry_rifle_combined`／`*_sabre_cavalry_entity`；模型走技能 `hoi4-pmx-to-mesh`（`肌/肌2` 是皮肤层，绝不能当装饰剔除）。
- **★可控角色招募口径**（2026-10-24 用户三次纠偏）：璃月／SAN／须弥／纳塔国家**不得在 `history/countries` 招募非可控角色**；名单只取 `tools/char_playable.py`（璃月 22／须弥 14／纳塔 11）。**须弥只调 `SUM - Sumeru.txt`**，SDH/SFG/SGC/SGD/SGS/SKD/VAN/VLM 一律不动；**璃月保留 `LYY_Morax`（摩拉克斯）与 `LYY_Marchosius`（马科修斯）**，审计脚本 `EXCEPT` 已列白。现 276 条招募违规 0。
- **★`recruit_character` 大小写不敏感**：`LYY_KeQing` 与 `LYY_Keqing` 同时招募同一人 ⇒ `already assigned` 警告（LYY 13／NAT 5 条，**用户未点头前不动**）。角色块只写在 `common/characters`，`history/countries` 里写错大小写不报 Unknown。

## 6 排布与清理口径
- **★不要那么多无用空行**（2026-10-24 用户明确）：块内空行全删；标量赋值并成一类连排（`capital`/`oob`/`set_stability`…）；`recruit_character` 同类连排且**每个国家文件只准集中在一处**（`group_recruit.py --apply`，2026-10-24 已把 37 个文件散成 2–10 处的全部合并，920 条不变）；**只在语句类型切换处留 1 空行**；注释行不参与分组。`compact_blank.py --apply`（幂等；characters 顶层深度 1、countries 0）。已把 4301 行空行压到 1737。
- 缩进一律 tab 按括号层级；行尾注释随行；无 BOM + CRLF。注释掉的废弃块（`#create_country_leader = { … }`）直接删，`history/countries` 已清 5 处。
- 蒙德系 TAG（称号特质跳过）：`MOT`/`NEWMOT`/`DVA`/`FAV`/`GUN`/`ANR`/`DRA`/`LAW`/`RAG`/`SPI`。

## 7 遗留
- **崩溃取证**：`0xc0000409`(BEX64) 不出 crashes 转储，看 Windows 事件日志（Application/1000 异常码+故障存储段 ID）；`error.log` 末段停在哪＝崩在哪个数据库；`C0000005` 才有 `crashes/*/exception.txt`。**排障先对崩溃时间戳 vs 改动落地时间**。
- **`sr_trial.py` 试机**：直起 `hoi4.exe`（DETACHED）轮询 game.log，出现 `[1936.01.01.12]` 即成功（48–57s）；进程先退且末行仍是 `Loaded 8022 provinces` 即崩。
- **「全部战略区单连通」在本图不可行**：陆省 THR=6 下 232 个连通分量，168 个州横跨两碎块（州不可拆）。原版也有 91 个 land 区含海省、48 个区不连通 ⇒ 合法常态。
- **工作区删不掉文件**：`rm` 被安全删除劫持且静默失败 ⇒ 用 PowerShell `Move-Item` 移出。
- 待用户拍板：蒙德 169 角色是否也做称号特质；`Backups/` 剩余 172 张备用图是否指回各 TAG 目录；`PRI` 是否破例建港；`DRA` 首都名；2 个落海胜点。
- 遗留报错：NAT 三个 `on_monthly` 无挂载；5 个悬空 `custom_effect_tooltip`；`DOT_NAT_country_leader.txt` 的 `political_power_gain_factor`、`FOD/FOM_country_leader.txt` 的 `army_experience` 等 `Unknown modifier`；`SOV - Soviet union.txt` 十余处 `create_corps_commander` 引用不存在的 `gfx/leaders/SOV/Portrait_Soviet_*.dds`。
