# MEMORY.md —— 提瓦特黎明（项目长期备忘）

> HOI4 1.19 通用语法/排查已收进技能 `hoi4-mod-bug-triage` + `docs/DOT_HOI4_Modding_Skills.md`。
> 本文件只记**本项目特有的口径、路径、环境与当前状态**（2026-10-11 压缩重写）。

---

## 0. ⭐⭐⭐ 用户明确口径（最高优先级，不得自行推翻）

| 日期 | 口径 | 要点 |
|---|---|---|
| 10-06 | **角色国别表 = 用户名单** | 权威源 `hoi4lint\icon_gen\role_nation.py` 的 `WIKI_ROLE_TABLE`。**禁止** WebFetch/WebSearch 抓 wiki、**禁止**关键词猜。自检 `python role_nation.py`：MOT 25 / LYY 23 / INA 15 / SUM 13 / FON 14 / NAT 11 / NDK 9 / SNE 3 / OTH 5 |
| 10-07 | **图标 = v7 原版链路 + v4 命名/idea 规则** | v7x/frost_bases/render_frost/base12_only/geo_frame/tone_schemes/v10~v14 **全部作废** |
| 10-07 | **素材库用工作区 `.skills\bwiki\icons3`** | icons 3244 / icons2 1536 / **icons3 6417**（优先）/ portrait 125；**没有抠图，要自己抠** |
| 10-10 | **旧 localisation 一律不删** | 判据 = 「是否真覆盖」：值相同 ⇒ 无害保留；值不同 ⇒ 才处理 |
| 10-11 | **NAT 国策树要「近方形 + 左右对称」** | 参照 `SAN_Neo_Focus.txt`。允许**激进重组**；只要三终局路线/五意识形态/深渊登场机制不变即可 |
| 10-10 | **`ABY_focus.txt` 是用户主动删除的废弃物** | **禁止恢复、禁止再写回、不必再提**；ABY 相关一律不做（用户没要求） |
| 10-10 | **focus 文件必须保留 `focus_tree` 头部** | `id =` / `country = { factor / modifier }` / `default =` / `continuous_focus_position = {x=20 y=900}` **缺一不可**，否则无法加载；**不许删** |

**用户偏好（通用）**
- **禁止「偷懒注释掉问题代码」**：读手册做真实修复；注释只在引擎确无此能力并获用户确认后才用。
- 「费 token 的活先搁置」：先做机械、低风险的那批。
- 用户下指令的最简形式：「用 v12 链路给 <TAG> 生成 350 张 goal 图标」。

---

## 1. 环境与写保护（工程约束，踩过多次）

- **Python = `C:\Users\XIANGZIYUAN\.workbuddy\binaries\python\envs\default\Scripts\python.exe`**
  （numpy / Pillow）。`versions\3.13.12` 那份**没有 PIL**。
- **Bash 工具优于 PowerShell**：有 stdout、无中文 mojibake、能起长跑进程。⚠ PowerShell 的 `*>`/`2>` 会写成 UTF-16。
- **文件编码铁律**：脚本 **无 BOM + CRLF**；**localisation `.yml` 必须带 BOM + CRLF**；`.gfx`/`.txt` 无 BOM。
  改 CRLF 用 `hoi4lint\_fix_crlf.py`。校验三断言：BOM / CRLF 数 / 括号 depth 不变。
- **⚠ Edit 工具同一文件并行多条会互相覆盖** ⇒ 多处修改必须**串行**。
- 控制台 GBK 显示 UTF-8 是「假乱码」⇒ 只认字节或写文件再 Read。

### ⚠⚠ 工作区写保护（2026-10-07 实测）
| 操作 | 结果 |
|---|---|
| 写全新文件 / 新建目录 | ✅ |
| **`shutil.copyfile` 纯覆盖（不先删）** | ✅✅ **首选** |
| Python `open(p,'w')` 覆盖；内置 **Write/Edit 工具** | ✅ |
| `os.rename` / `cp -f`（先 unlink） | ❌ WinError 5 |
| `os.remove` 单个 | ✅ 但慢 |

⇒ **覆盖直接写，绝不先 `os.remove`**（撞 safe-delete 闸门）。
⇒ **safe-delete 批量闸门**：一轮累计 50 个删除**静默中止整个进程** ⇒ 清理放进一个 Python 进程；
⇒ 涉及工作区写入的脚本**拆成独立进程**。

---

## 2. 路径

| 用途 | 路径 |
|---|---|
| **MOD 根（当前工作区）** | `C:\Program Files (x86)\Steam\steamapps\common\HOI4 MOD Github\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version`（`.workbuddy` 在本目录） |
| 兄弟版 | 同根下 `Daybreak of Teyvat Alpha/Beta Version`（Beta 常含被 Gamma 清掉的内容） |
| 原版 1.19.3 | `C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV` |
| 脚本 + 备份 | `C:\Users\XIANGZIYUAN\hoi4lint\`（`icon_gen/`、`backup_nat_round11/`、`vanilla_tokens.pkl`） |
| 日志 | `Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log` |
| 地图/资产产物 | `Gamma Version\.workbuddy\mapgen\`；整包 `pack/teyvat_maps_3072.zip` |

**生效 `replace_path`**：history/countries|states|units、common/bookmarks|resources|ai_strategy(_plans)、events、
common/decisions|countries、map/strategicregions|supplyareas。
⚠ `common/national_focus`、`continuous_focus`、`gfx` **不在内**（前面的同名空文件是必需的屏蔽开关）。

---

## 3. ⭐ 工作区是「活的」文件系统 —— 必读

- ⚠ **会被外部副本整份覆盖，已多次回滚掉我做过的事**（含 MEMORY.md 本身）
  ⇒ **任何「我做过的事」必须先 `grep`/`ls` 核实当前状态，绝不能凭上下文记忆答复用户。**
- ⚠ 文件会被**合并改名** ⇒ 校验脚本**禁止写死文件名/固定计数**，按内容特征定位。
- ⚠ **外部进程会并发插行/截断文件**（实测往 focus 文件插 221 行 `icon`；把 `ABY_focus.txt` 截断成 0 字节）
  ⇒ 动手前**先备份**（`hoi4lint\backup_nat_round*`）。
- 全目录扫描排除 `.backups\`、`备份文件BY Ruka\`、`desktop.ini`、`gfx/_convert_log.txt`。
- `game.log` 报 **Loaded 11507 provinces** 才是本 MOD（13414 = 原版地球）。

---

## 4. ⭐⭐ NAT 剧本基线（2026-10-11 实测）

`nat_final_check.py`（10 项综合）**当前 EXIT=0 / 0 问题**。

| 项 | 数 | 文件 |
|---|---|---|
| NAT 国策 | **253**（单根 `NAT_Call_Tribal_Council`，BFS 253/253 可达） | `common/national_focus/NAT_Neo_Focus.txt`（**159927 B**，CRLF 5991） |
| ABY 国策 | **0 —— `ABY_focus.txt` 是空文件**（用户废弃物，勿动） | `common/national_focus/ABY_focus.txt` |
| 决议 | 146 决策块 + 11 决策容器 + 1 categories 文件（12 分类） | `common/decisions/NAT_Neo_decisions.txt` |
| 事件 | 260 `country_event` + 5 `news_event` | `events/NAT_Neo_Event.txt` |
| 民族精神 | 74 个 idea 块（picture 76） | `common/ideas/` |
| 动态修正 | 19（单文件，深渊7+恩情7+战况5） | `common/dynamic_modifiers/NAT_dynamic_modifiers.txt` |
| 宏 | 107（唯一 107、调用 77、未定义 0） | `NAT_Neo_effects.txt` + `DOT_scripted_effects.txt` |
| 本地化 | 主文件 2481 key / 重复 0 / 引用 919 **缺失 0** | `localisation/simp_chinese/NAT_Neo_Script_l_simp_chinese.yml`（BOM=True, CRLF 3132） |

### 架构铁律
1. **两大变量名不可改**：`NAT-ABY-Index`（深渊侵蚀度，开局 40）、`MVK-Prestige-Index`（火神恩情，开局 50）。
2. 改这两个变量**必须走宏**（`NAT_Abyss_Add_*`/`Sub_*`/`NAT_Grace_Add_*`/`Sub_*`），宏内同步写 country_flag。
3. 动态修正直接 `enable = { check_variable = { X > 60 } NOT = {...} }` 读变量 ⇒ 实时生效；区间互斥 + 首档 `has_variable` 守卫。
4. `NAT_ABY_T1..T7` / `NAT_MVK_T1..T7` flag 仅供 scripted localisation 显示档位名。
5. 三路线互斥终局：`NAT_Focus_Convergence_Final`（甲吞并）/ `Covenant_Final`（乙盟约）/ `Embers_Final`（丙余烬）；
   共通 `NAT_Focus_Finisher_Abyss_Quenched`。
6. 六族 tag `NCP NCE NPS NSC NFF NMN` + 自治州 `autonomy_NAT_State`；深渊方 `HIP`（开局无领地）+ `ABY`。
   5 意识形态：democratic/communism/**fascism**/neutrality/genshin。
7. **深渊登场**：HIP 开局无领地 → NAT 决议 `NAT_decisions-01`（门槛 `NAT-ABY-Index > 59`）→ 宏
   `NAT_Abyss_War_Trigger` → `NAT_Declare_Abyss_War` **只对 HIP 宣战** + `292 = { transfer_state_to = HIP }`。
   侵蚀度 > 140 自动引爆同一入口。

### ⭐⭐⭐ 国策树布局 = 容量受限 Kahn 分层（v906 定稿，2026-10-11 取代 v800/v900/v904 全部）
**正解算法**（`hoi4lint\build_v906.py <CAP>`）：
1. **层 = Kahn 出队顺序**，每层取 `ready[:CAP]` ⇒ `y(child)>y(parent)` **天然成立**，不需回算。
2. 叠 **14 轮重心排序**（上下交替，父均值/子均值排序）→ **逐层居中**（对齐父层中点）→ **间距≥2 铺开**（反复）。
3. **CAP=19 → 38 列 × 32 行 / 比例 1.219**（SAN 参照 37×31 = 1.19）。
   CAP=17→1.156 / CAP=21→1.344 / CAP=15→0.969。253 节点 ⇒ CAP 在 17~21 之间调。

**⭐ 磁盘 prerequisite 必须先 dump 再动手**：v800 是**严格单链**（253节点/252边，每点恰好 1 前置）。
只改 x/y 而不匹配新树 ⇒ 实测 **47 处倒挂**。快照存 `_disk_tree.json`。
**v906 保留磁盘真实 prerequisite 原样**（逐行 diff：非 x/y 差异 = 0 行），只重排坐标。

**已作废的错方向（别再走）**
| 方案 | 死因 |
|---|---|
| v18 / v800 轮廓法·Sugiyama | 54×51 / 31×37 倒T、栅栏 |
| v900 手工泳道 | 上部栅栏 + 下部散乱 |
| v902 容量分层（用 v900 的 PRE） | 树本身 40 层，压不动 |
| v904 纵向长链并列 | **SAN 同列垂直边 73% 来自树形连线，不是长链**；做出 94% 垂直边 + 比例 2.3 = 横向条带 |
| v903 祖父继承剪接 | 能压深度但尾部堆到 23 层 |
| 容量均衡 + `refresh()` 回算 | ⚠️ **`refresh()` 会把手动下移全部清零** |

**语义 bug 修正**：DRAGON×5 / NIGHT×2 原本「串行链 + mutually_exclusive」= 必须按序全做完（错）。
正解 = **同父并列兄弟**。互斥组必须横向摊开（间距 ≥2，同 y）。

**校验链**：`verify_tree.py <file>`（严格解析 prerequisite + 坐标 + 可达性）→
`apply_v906.py`（**只改 x/y 两行**，正则 `^\tfocus = {$` / `^\t\tid = `，**单 tab 不是双 tab**）→
`_final_guard.py`（逐行 diff 守卫）→ `_write906.py`（tmp + `shutil.copyfile` 纯覆盖，**勿先 os.remove**）。
备份 `hoi4lint\backup_nat_round13\`。

**定稿指标**：253 focus / x[-19,19] / y[0,31] / 重叠 0 / 间距<2 = 0 / 倒挂 0 / 可达 253/253 /
唯一根 `NAT_Call_Tribal_Council` / 三终局 + 汇合点全在 / `nat_final_check.py` 10 项 0 问题。
渲染 `render_free.py <lay.json> <out.png> <title>`，lay 需 `X`/`depth`/`new_pre` 三键。

### ⚠⚠ 本地化：只删「真覆盖」，其余一律保留（2026-10-10 事故）
**事故**：去重流程把 `NAT_Neo_Script_l_simp_chinese.yml` 里 16 行**整行删掉**（含 `NAT_Event.83.t/.d/.a/.b`）。
用户明确批评：**这些只是本地化，不影响剧本推进，不许删。**
- **判据**：key 在文件中**完全不存在** ⇒ 属误删，**必须恢复**；key 仍在但值改写 ⇒ 刻意重写，不动。
- **恢复**：从去重前快照 `hoi4lint\backup_loc_before_dedup.yml` 取原行追加末尾（脚本 `_loc_restore.py`）。
- 已恢复 `NAT_Event.83/84/85` 全套 + `NAT_Event.782.t/.a/.b`。
  几个事件号**已不被现行 `NAT_Neo_Event.txt` 引用**，纯惰性文本，留着无害。
- ⚠ **正则统计 loc 行数必须先 `.replace('\r\n','\n')`**，否则 `".*"$` 被 `\r` 挡住 ⇒ 全 0 漏报。

---

## 5. ⭐ 图标产线（v7 + v4）

链路：`pool_<TAG>.json` → `full_v7.py --n 350 --out out_<TAG>` → `build_v4.py` → `qa_v4.py` → `deploy_v4.py`。
- **参数冻结**：`subj_ratio` goal 0.80、`ex_glow` 0.62、`halo` 0.62、`contrast` 1.08、`bright` 1.06。goal **108×90**，idea **68×68**。
  框体 = v7 自绘 9 层华丽框 + `shape_of(名)` 四选一。立绘**不裁剪、不改色、不加圆形遮罩**。
- **idea = goal 中心方裁缩放**（`D=min(W,H)` 居中裁 → resize 68×68），**禁止** 68×68 上独立重跑 render。
- **命名 = 纯英文名，禁止序号**：`goal_FON_<English>.png` / `idea_FON_<English>.png`。
  译名**只查词库** `hoi4lint\icon_gen\gdict_words.json`（6819 条）。⚠ 自造译名离谱：爱可菲=Escofier、千织=Chiori。
- **引用规则**：focus 写 `icon = GFX_goal_<TAG>_<Name>`；idea **写裸名** `picture = <TAG>_<Name>`。
- **素材分配**：同素材最多 2 次（goal 1 + idea 1）⇒ 每国 350 个不同素材；**素材 `kind` 字段不可信**，按原始文件名校验。
- **语义匹配** `semmap2.py`（48 类目 + 624 DIRECT + 407 WEAK）：focus 71.7% / idea 64.0%。

### ⚠⚠ 图像判据（血泪）
- 判「抠图」唯一硬指标 = **`alpha.min() >= 8`**（`audit_cutout2.py`）。❌ `opaque 占比` 会漏掉整幅半透明底。
- 判「有背景」用几何判据 `detect_bg2.has_square_bg`。❌「近底色占比>18%」误报率极高。
- 成品判方块底看**主体区众数色占比**（正常中位 0.08），**别看框体 alpha**。
- 抠图必须 `cutout_force.py`（丢弃原 alpha）。
- **pHash 去重**：渲染前后都要查；阈值**素材级 HAM=4 / 成品级 6**；闸门必须**一进程内跨桶共享**。
- **build/渲染脚本刻意不删输出目录** ⇒ 跑完必 **`sync_to_manifest.py`**（先 `dryrun2.py` 秒级验证）。
- GFX 声明 `build_gfx_ship.py` 以**磁盘 PNG 文件名为唯一真相源**；9 个 `interface/DOT_Icons_<TAG>.gfx`。
  ⚠ shine 名 = `<name>_shine`。解析 SpriteType **禁止非贪婪配花括号**。

---

## 6. HOI4 通用坑（细则见技能，此处只留最常踩的）

1. **决议必须嵌在 `XXX_category = { }` 内**才归属该分类；层级**按括号深度**判断。
2. **决议 icon 与分类 icon 两套 namespace**：决议 `GFX_decision_X` / 分类 `GFX_decision_category_X`。
3. 抓边**必须从根正向 BFS 只取 `prerequisite` 块内的 focus**（`mutually_exclusive` 缩进完全相同，否则假报）。
4. 决议 desc 的 loc key = **块名 + `_desc`**。
5. **同一分类不得**在 `decisions/` 与 `categories/` **两处重复定义**。
6. 已移除语法：`add_timber`/`add_supply`/`add_to_mobilization`/`limited_annex`/`national_independence`。
7. on_actions TAG 钩子只有 `on_daily/weekly/monthly_<TAG>`（`on_quarterly` 不存在）。
8. loc key 可含**点号**；`KEY: "x"` 与 `KEY:0 "x"` 都合法。
9. **loc 值内只允许 `\n` 和 `\"`**；`\!` 触发 `Illegal break character`。
10. `check_variable = { X > N }` 的自动 tooltip 会去找名为 `X` 的 loc key ⇒ 变量要有显示名。
11. **「图标出不来」以 error.log 为准**（静态扫描 ~500 假阳性）；引擎对 focus `icon=` 自动补 `GFX_`。
12. **定位排版**：`x`/`y` + `relative_position_id`（`dx`/`dy` 出现 0 次）；同层相邻 x 间距 **≥ 2**。
13. **模型（gfx）绑定两层文件**：`.gfx` 定义层 + `.asset` 引用层。⚠ HOI4 建筑 mesh = Y-up。
14. CAD 建筑模型**不能按厚度剔薄片**。
15. `heightmap.bmp` 4096×2048 **8bpp**：10 最低 / 94 海平面 / 96 沿海 / 255 最高；改后必重生成 `world_normal.bmp`。

---

## 7. 方法论要点

0. **以 error.log 为准**：按 (文件, 行) 去重；用 `os.walk(MOD)` 建索引过滤非本 MOD 条目。
1. 脚本改文件：dry-run **必须 0 MISS** 才 `--apply`；改完三校验（BOM / CRLF / depth）。
2. **区分「纯语法修复」vs「改变玩法的修复」**：后者先报告用户拍板。
3. token 合法性双裁判：手册 key 表 + `vanilla_tokens.pkl` + `difflib`。
4. 「日志干净」必须先证伪：查 `dlc_load.json` 的 `enabled_mods`。
5. 多国共用素材池必须**串行** + `global_ledger.json`（并行 = 去重失效）。
6. **布局类问题先诊断再动手**：先量化（每层节点数、跨度、空洞）再换算法，别盲目加旋钮。

---

## 8. 遗留 / 已知未修（动手前先看）

- ⚠ **`common/national_focus/ABY_focus.txt` = 0 字节是用户主动删除的废弃物**（2026-10-10 用户拍板）。
  **不要再恢复、不要重写、不要向用户提议处理 ABY。**
- 7 个 `add_ideas` 指向 focus id（旧报未改）；194 处 `\N` 转义（非 NAT 文件）。
- **ABY/NAT 剧本仍未进游戏验证**（只在静态层校验）。
- `events/LYY_Ganyu_Events.txt`、`LYY_Keqing_Events.txt`、`LYY_News.txt`、`common/country_leader/LYY_traits.txt`
  中文注释**编码彻底损坏**（字面量 U+FFFD，最早 backup 就已坏）⇒ 原文永久丢失。**Gamma 未处理**。
- 若将来改 `NAT_Glory_Of_Natlan`：去掉 `Three_Paths_Crossing` 对它的前置会让它变死路，需同时接新下游。
- error.log 里的 `add_tech_bonus: Unknown technology category`（MOT/RAG/SAN/SNE/NAT events）与
  `has_ideas`/`end_war` 无效语法（`NAT_Neo_effects.txt`）均为**既有问题，与布局无关**，待后续单独处理。
