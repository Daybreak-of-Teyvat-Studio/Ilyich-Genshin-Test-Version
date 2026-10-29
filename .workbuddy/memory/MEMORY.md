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
- **★只许在当前磁盘状态上做增量补丁（用户 10-29 19:02 明令）**：禁止拿 `_backup_*` 整份回写覆盖；用户会随时手改文件（删块、改名、调位置），旧备份里没有这些改动。删/补都按「块」定位（name 精确匹配），改前另存**新**快照（`_backup_*_<时间戳>`），改后用块名集合 diff 自证没丢块。
- **★别把用户的「手改」当损坏**：文件「被回退／块消失」先问一句，绝不按「磁盘有文件就补」自动补回。

## 1 编码（最易致命）
- loc `.yml` = UTF-8 BOM + CRLF（缺 BOM 整份静默丢弃）；`key: "值"` 不带 `:0` 是合法写法，别批量改。
- `common/ideas|characters|country_leader|idea_tags`、`history/{countries,states}`、`map/supply_nodes|railways`、战略区 txt、`weatherpositions.txt`、`.asset` = **无 BOM + CRLF**（BOM 让首行变 `Unexpected token: characters`）。
- 脚本无 BOM + CRLF；Edit 同文件多处改动必须串行。
- **★禁混用「字节读 + newline 写」**：`raw.decode()` 读入后原文仍是 `\r\n`，再用 `open(..., newline='\r\n')` 写 ⇒ 每个换行变 `\r\r\n`（10-28 一次性污染 63 个 state + 12 个 asset）。要么全程字节（`open(wb)` 写 `encode()`），要么文本读（默认 `\r\n`→`\n`）+ `newline='\r\n'` 写。改完必须查 `b'\r\r\n' not in data` 与 `BOM`。
- **★反向坑：文本读 + 二进制写会吃掉 CRLF**（10-29 19:00 中招）。`open(p,encoding='utf-8').read()` 的 universal-newlines 已把 `\r\n` 变成 `\n`，再 `open(p,'wb').write(s.encode())` ⇒ 整份文件变裸 LF，编辑器里显示「全文改动」。正解：`open(p,'rb').read().decode('utf-8')` 读入（保留 `\r\n`），改完 `encode()` 后 `wb` 写；或改完统一 `b.replace(b'\n', b'\r\n')` 并断言 `b.count(b'\r')==0` 再替换。

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
- **★Palace / 地标落点只认 `map/buildings.txt`**（`map/buildings_landmark.txt` 是自己维护的坐标表，引擎不读）。Palace 的 `spawn_point = nuclear_reactor_spawn`（DOT_Palace 例外，用 special_project_facility_spawn），所以「宫殿站哪」＝该州那条 `<州id>;nuclear_reactor_spawn` 行的 x/y/z；另有 `<州id>;<X>_Palace` 行可显式钉住（历史版本里两行逐位相同）。核落点：positions.txt 拿省中心 (x,z) → provinces.bmp 反查省色 → definition.csv；`y = heightmap[row][x]*0.1`，`row = H - z`。工具 `palace_move_coords.py`／`verify_palace_coords.py`。
- **省建筑 / 州建筑判据**：`level_cap` 里**有 `province_max` = 省建筑**（每省独立计数）；只写 `state_max` 才是州建筑（每州一个）；`shares_slots = yes` 才占州民用槽（landmark 不写）。`show_on_map` 语义随之变「每州数量」。state 文件里州建筑写 `buildings` 顶级（引擎自选省），写进 `<省id> = { … }` 则位置钉死在该省。
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
- **武器「大面积没颜色」先查贴图、别先怀疑材质**：多数是源资产 PBR 靠金属反射呈色、diffuse 近白。
  别整张调色 —— 用网格三角的 UV **栅格化 mask** 精确圈出问题区域再染（`fix_bh_blade.py`），
  DDS 只重编码 mask 覆盖的 4x4 块（`dds_patch.py`），其余块原始压缩字节保留，免得把好区域二次压缩。
  **判外观只用 `render_mesh_pixel.py`（逐像素 UV + Z-buffer）**；`render_mesh_tex.py` 是每三角取平均色，
  会把三角色差画成横向色带，容易误判成贴图接缝。hoi4lint 里 `_backup_*` 系列为各轮备份。
- **武器族口径**：`<前缀>_sword_sabre[_holder].mesh` + `_diffuse/_normal/_spec.dds`，主 mesh Y 跨度统一 **3.2167**（×scale 2.9 = 9.33），刃尖 −Y、柄尾 +Y。现役：BH/HPY/JS/SL/MOT/DG(薙草)/CD(裁断斧)/HM(护摩)。**holder 不能无脑切 −Y 端 18%**——刃在 −Y 时会切出刀尖，用 `weapon_holder_cut.py --keep "y>=…"` 按区间取柄部。改名必须连 **mesh 内部串**一起改（材质名带 u32 长度前缀），工具 `rename_dot2bh.py`、预览 `render_mesh_tex.py`、四层核验 `verify_sabre_family.py`。

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
