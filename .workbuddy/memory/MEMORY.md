# MEMORY.md —— 提瓦特黎明（DOT Gamma）项目备忘
> 细节见 `.workbuddy/memory/2026-10-*.md`；技能 `hoi4-mod-bug-triage`；工具在 `~/.workbuddy/workspace/hoi4lint/`。本文件只留铁律与当前口径。

## 0 铁律
- 禁回滚／禁 git／禁注释掉问题代码；中文注释只写中文；直改原文件禁 `_v2`；旧 loc 一行不删；`ABY_focus.txt` 不动；focus 保留 `focus_tree` 头；数量一律下限。
- 修 bug 只修不删（loc 同键重复：拆 `key`/`key_desc`、空值补正文）。颜色闭合用状态机判（`§X` 开／`§!` 关），数 `§` 奇偶是错的。
- 事件/新闻 desc 200–400 字（去空白），生成取下限 206；禁破折号。
- 新增内容并入同名 `<国>_*` 文件；新闻由 `completion_reward` 触发 `news_event={id=NS.n days=1}`；`add_namespace` 写文件首部。
- 机制三件套 `*_Init` 置初值 → `*_Tier_Refresh` 卸全档挂唯一档 → `on_daily` 的 `*_Sync` 保鲜；轴指数变化放 `hidden_effect` 外＋逐条 `custom_effect_tooltip`。
- `dynamic_modifier` ≤10%；备份一律出 MOD（`hoi4lint/_backup_*`）。
- **★产物统一放 `C:\Users\XIANGZIYUAN\.workbuddy\workspace\`，家目录根下不新建**。

## 1 编码（最易致命）
- loc `.yml` = UTF-8 BOM + CRLF（缺 BOM 整份静默丢弃）；`key: "值"` 不带 `:0` 是合法写法，别批量改。
- `common/ideas|characters|country_leader|idea_tags`、`history/{countries,states}`、`map/supply_nodes|railways`、战略区 txt、`weatherpositions.txt`、`.asset` = **无 BOM + CRLF**（BOM 让首行变 `Unexpected token: characters`）。
- 脚本无 BOM + CRLF；Edit 同文件多处改动必须串行。
- **★禁混用「字节读 + newline 写」**：`raw.decode()` 读入后原文仍是 `\r\n`，再用 `open(..., newline='\r\n')` 写 ⇒ 每个换行变 `\r\r\n`（10-28 一次性污染 63 个 state + 12 个 asset）。要么全程字节（`open(wb)` 写 `encode()`），要么文本读（默认 `\r\n`→`\n`）+ `newline='\r\n'` 写。改完必须查 `b'\r\r\n' not in data` 与 `BOM`。

## 2 环境
- Python = `…\binaries\python\envs\default\Scripts\python.exe`；Bash 优于 PowerShell。
- `replace_path`：history/{countries,states,units}、bookmarks、resources、ai_strategy*、strategicregions、supplyareas（decisions／national_focus／gfx 不在内）。
- **MOD 根 = `Ilyich-Genshin-Test-Version/Daybreak of Teyvat Gamma Version/`**；同级 `Ilyich Genshin Daybreak of Teyvat/` 是旧快照，勿误改。
- 工作区可能被外部会话整份覆盖 ⇒ 改完复核。

## 3 角色 / 肖像 / 顾问
- 四槽位 `civilian{large,small}` + `army{large,small}`，全库零空；`large` 156×210 走 `gfx/leaders/<TAG>/`，缺了用 `Backups/`。
- `small` 优先级：cabinet 58–74px → cabinet 156×210 **裁 65×67 存 gen**（不能直接引用）→ `DOT_PP/idea_*.png` → 立绘裁（裁切框 0.78×图高、水平居中贴顶）→ `cabinet/Undecided.dds`（式大将占位）。
- **造 gen 图前必须穷举匹配**：①递归扫 `cabinet/` 全目录（`LYY/`、`VAN/`、`NDK/`、`DVA/`、`FON/`、`KNA/`、`PRI/` 都有小图）②剥尾号与 `DOT_` 前缀 ③别名表（`Miko→INA_miko`、`Momoka→Kirara`、`Kaveh→Cavy`）。只收 58–74 方图。
- **同角色多变体共用一张小图**；裁图前查重（dHash=0 即重复）。cabinet 小图**只按角色 ID 匹配，绝不看 `large` 名**（large 多为借图）。
- **`gfx/leaders/LY/Gunnhildr.dds` 的 `large` 一律不动**（72 块无名占位，用户拍板）；但 small 绝不能指它或任何 `gfx/leaders/` 大图。
- **★`create_*` 内联立绘用 png 会报 `character_manager.cpp:307 unexpected format`（无法推算 small）**。要 png 化必须改成 character 块 + `recruit_character`。
- `country_leader` 块**不支持 `visible`**（只认 ideology／traits／expire／desc／id），一个 character 只能有一个 `country_leader` 子块 ⇒ 同角色多意识形态必须拆成多个 ID。
- 内阁顾问：每角色一个 `advisor` 块；`traits` 只放**一个**专属称号特质；`high_command`／`theorist` 的 `slot_ledger` 是 `invalid`，**必须显式写 `ledger`**；同角色两个 advisor 块报 `tries to cumulate`。
- `advisor.idea_token` 只是标识符，效果由 `traits` 承担；自定义 idea 类别必须在 `common/idea_tags/` 注册，否则整份静默丢弃。
- 角色肖像是**全游戏唯一可直接写图片路径、不需 sprite** 的地方；idea 的 `picture` 必须裸名。

## 4 地图 / 建筑
- `map/buildings.txt` 行 `州id;建筑id;x;y;z;旋转`，**第一字段是州 id**；z 轴与位图行相反（`row = H - z`）；`y = heightmap[row][x] * 0.1`。
- `nuclear_reactor_spawn` 的 8 个 `*_Palace` 行列必须等于本州该行；收尾 `fix_showcase_positions.py --apply`。
- 建筑等级不得超 `00_buildings.txt` 的 `level_cap`：infrastructure 5、air/naval_base 10、arms/industrial/dockyard 20、anti_air 5、radar 6、rocket/synthetic 3。
- 战略区：**区内省集 4-邻接连通是硬要求**（不连通静默崩在 `Loaded 8022 provinces`，error.log 不报）；id 不许空洞；纯陆区不写 `naval_terrain`；`provinces` 不能有 0 号省。

## 5 当前口径
- 胜利点只 5/10/20/40（439 点/323 州），首都州 40；原值≥25 的主点必为 20 档。
- 经济：每国工厂 10–100、人口 4–40 千万整千；现工厂 944／港口 115／机场 98。补给只给最高胜点 ≥10 的州（205 条）；铁路 439 胜点进网 431。
- **可控角色**：璃月／SAN／须弥／纳塔**不得招募非可控角色**（名单 `tools/char_playable.py`）；**须弥只动 `SUM - Sumeru.txt`**；保留 `LYY_Morax`／`LYY_Marchosius`／**`SUM_Azar`**（见下条）。现 279 条违规 0。
- **★删 `recruit_character` 前必验「会不会失国」**：这些国家都没有 `set_country_leader`，领导人＝按招募顺序第一个 `country_leader.ideology` 所属 group 等于 `set_politics.ruling_party` 的角色。两个已踩过的坑：**SUM 开局 ruling=neutrality，唯一符合的是 `SUM_Azar`（oligarchism）**，`SUM_Nahida` 是 wisdom→genshin 当不了；**SAN 开局 ruling=democratic，唯一符合的是 `SAN_Kokomi`（conservatism）**，四个 Kokomi 变体分别是 eternity/Rosism/Black_Rosism/anarchism。工具 `recruit_integrity.py`（四层总核，判领导人要用 `finditer` 取**全部** country_leader，只取第一个会误报）、`fix_sum_leader.py`、`leader_cover_bak.py`。
- **★create→character 转换的验收标准**：不能只看「角色在不在」，要按 create 的 **kind** 逐一核槽位（`createtochar_slots.py`）。`create_corps_commander` 漏建**不报错**，只会静默少一个将领 —— `SAN_Gorou` 就是这么丢了（10-25 已补建）。块命名归一用「纯字母数字子串包含」，不要剥 `^[a-z]{2,5}_` 前缀（会把 `Ying_A` 剥成 `a`）。
- **countries 只招募同 TAG 前缀角色**（`X - *.txt` 只能 `X_`）。MOT 系 34 处 `create_*` 已于 10-24 全改为 character + `recruit_character`（GUN 新建 `GUN_Characters.txt`）。
- **★跨 tag 招募判据（用户 10-24 23:59 拍板）＝看角色块所在文件**：`X - *.txt` 只能招募写在 `X_Characters.txt` 里的块，不看 ID 前缀、不管角色设定国籍；原版 `<TAG>.txt` 同算对应文件。`ANR_characters.txt` 里 `Venti`/`Mona`/`Razor`/`Kayae` 无前缀也属 ANR。
- `recruit_character` 大小写不敏感，大小写变体并存 ⇒ `already assigned`（LYY 13／NAT 5 条未清）。
- NAT 六族 NCP/NCE/NPS/NSC/NFF/NMN；LYY 六派 12 线；SAN 三终局；SUM 888 国策/170 决议，只重建国策用 `regen_focus_only.py`。
- 兵模：`clone` 每 tag 12 个、不能覆盖 attach；三件套 `*_sabre_*`；`肌/肌2` 是皮肤层不能剔除。

## 6 排布与清理
- **不要无用空行**：块内空行全删；标量连排；`recruit_character` 同类连排且**每文件只集中一处**；只在语句类型切换留 1 空行；注释行不参与分组。
- tab 按括号层级缩进；注释掉的废弃块直接删。
- 蒙德系 TAG（称号特质跳过）：`MOT`/`NEWMOT`/`DVA`/`FAV`/`GUN`/`ANR`/`DRA`/`LAW`/`RAG`/`SPI`。

## 7 遗留
- **崩溃取证**：`0xc0000409` 不出 crashes 转储，看 Windows 事件日志；`error.log` 末段停在哪＝崩在哪个库；`sr_trial.py` 出现 `[1936.01.01.12]` 即成功（48–57s）。
- **`gfx/leaders` 已全 png**（Europe 与最外层 4 张占位图除外）；798 个原文件在 `_trash_leaders_20261024_231925`。剩 5 条 `unexpected format` 来自 `FRA - France.txt` 的 5 个 create。
- `gfx/leaders/LY/FurinaGod.png` 从未存在，`DOT_Rule_Decisions.txt` 4 处 `set_portraits` 指它（其余四神都有 `*God.png`）——待决。
- 待拍板：蒙德 169 角色称号特质；`Backups/` 172 张备用图；`PRI` 建港；`DRA` 首都名；2 个落海胜点。
- 遗留报错：NAT 三个 `on_monthly` 无挂载；5 个悬空 `custom_effect_tooltip`；若干 `Unknown modifier`。
- 工作区 `rm` 被安全删除劫持且静默失败 ⇒ 用 Python `os.replace`/`shutil.move` 或 PowerShell `Move-Item` 移出。
