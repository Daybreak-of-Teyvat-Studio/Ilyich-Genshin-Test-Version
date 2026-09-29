---
name: hoi4-mod-bug-triage
description: 钢铁雄心 IV（Hearts of Iron IV）MOD 的 bug 排查与修复技能。当用户要求「检查/排查/纠错/修复 HOI4 MOD 的代码」「error.log 报错分析」「mod 报 Invalid effect / Unknown trigger / Invalid tech」时使用。核心方法是把游戏运行时 error.log 作为权威证据，逐条与原版定义库对照，再用维基手册确认正确写法后精确落地修复。覆盖 common/（decisions、national_focus、abilities、ai_equipment、technologies、doctrines）、events/、history/、localisation/ 等目录，以及空占位文件覆盖原版、版本升级导致的语法变更（如 1.19 学说从科技树迁出）等典型坑。触发词：HOI4 MOD、钢四 MOD、提瓦特黎明、Daybreak of Teyvat、error.log、Invalid effect、Unknown trigger、Invalid tech、mod 报错、mod 纠错。
agent_created: true
---

# HOI4 MOD Bug 排查与修复

## 概览

HOI4 的脚本是 Clausewitz 文本（`key = value` / `key = { … }` / `#` 注释）。绝大多数「bug」不是语法错误，而是**语义错误**：标识符拼错、效果写在触发器位置、版本升级后语法变了、空文件静默覆盖了原版内容。因此排查必须**以游戏自己的报错为权威**，而不是靠静态扫描猜。

**关键前提**：语法层（括号/引号平衡）通常没问题。不要在上面浪费时间，直接看 `error.log`。

## 何时使用

- 用户要求检查 / 排查 / 纠错 / 修复某个 HOI4 MOD 的代码。
- 用户给出 `error.log`、贴出 `Invalid effect 'x'` / `Unknown trigger-type: x` / `Invalid tech` 等报错。
- MOD 表现异常：国策/决议不生效、事件不触发、能力无效果、AI 行为怪异。

## 第零步：如果症状是「进不去游戏 / 崩溃」（CTD），先走这条线

脚本语法错误几乎**不会**让游戏崩溃。遇到 CTD 不要继续在 error.log 里数报错，它有独立的证据源。

### 证据在哪

```
<用户目录>/Paradox Interactive/Hearts of Iron IV/
    crashes/<YYYYMMDD_HHMMSS>/
        exception.txt      ← 版本、异常码、崩溃地址（最关键）
        meta.yml           ← 启用了哪些 mod、是否读档
        minidump.dmp
        logs/error.log     ← 崩溃前最后写入的内容
        logs/system.log    ← 启动过程（显卡/分辨率等）
    logs/game.log          ← 很短，但能看出「加载到哪一步」
    logs/setup.log         ← 启动全过程（on_actions 注册、`Startup time`、`Session change`）
    logs/random.log        ← 开局初始化的分段时间（`Resetting game` / `Loading HistoryDatabase` / `CGraphicalMap ResetGame`）
    save games/*.hoi4      ← **游戏最后一次成功运行的时间预言机**（见下）
```

**「这崩溃是不是我造成的」有一条更快的判据，先用它，别急着改文件**：

```
ls -lat "<用户目录>/Paradox Interactive/Hearts of Iron IV/save games/"
```

最后一个存档（含 `autosave.hoi4`）的 mtime = 游戏**最后一次真正跑起来并玩进去**的时间。
它明显早于你动手的时间 → **这次 CTD 早于你的改动，与你的改动无关**，直接停止自我怀疑，把方向转到崩溃链本身。
（实测价值：一次排查里存档停在两天前，而 `crashes/` 这两天有 20 个目录，一眼就排除了「我把游戏改崩了」。）

对照时间线还要看 `meta.yml` 的 `DataChecksum`：同一次会话里它的值变了，说明**你在两次启动之间改过 mod 文件**；
三次崩溃若 `DataChecksum` 完全相同，则是同一份数据上的确定性崩溃，可反复复现来 A/B。

### 「点开始游戏后 1 秒崩」这一类的排查顺序（2026-09 实证）

日志长这样：

```
game.log:  Loaded <N> provinces. → Resetting game → Executing History … → [[ Launching SINGLEPLAYER-game ]]
crash:     1 秒后 C0000005
```

**它属于「世界初始化」阶段，不是文件解析阶段**，所以先做**排除**，比逐个文件猜快得多：

1. 在这条崩溃链上做关键词计数，**全部为 0 就说明地图与州数据是干净的**、可以排除：
   `MAP_ERROR`、`map/buildings`、`heightmap`、`terrain`、`provinces`、`definition.csv`。
2. 同时看 `crash/logs/system.log` 的 `Active Mod Count`：**只启用一个 MOD** 时，其余 MOD 提供的
   实体/单位/模型全部缺失，`Building X doesn't have an entity` 这类报错要按「缺依赖」而不是「MOD 自身坏」来解释。
3. 到这一步别再猜，做**变量隔离实验**（各跑一次即可）：
   - **换书签开局**：`common/bookmarks/*.txt` 里有几个 `date =`，换一个日期开。只有某一条线崩 → 病根在该书的
     `history/countries/*.txt` 里；全崩 → 病根在全局（图形资源 / 地图 mesh）。
   - **临时改名 `map/positions.txt`**（原版这个文件是 **0 字节**，位置由引擎自算）。MOD 自带的自制 positions
     是最容易被怀疑的一份「非原版产物」。
   - 把 3D 地表贴图目录里**你在最近一次提交里改过格式**的 DDS 换回去（实测见过
     `colormap_rgb_cityemissivemask_a.dds` 从 DXT5 被重编码成 DXT1；两个头都合法，所以不一定是它，
     但它是最可疑的图形资源）。
4. `git show --stat HEAD` 是**看「16:37 那一秒整目录被谁重写」的最快办法**：MOD 工作区常被 git 签出整体覆盖，
   提交作者和 commit message 会直接告诉你这是人做的还是流水线做的。`git status` 干净 = 磁盘状态 == 该提交。

### 三步定位法

1. **读 `exception.txt`，取崩溃偏移**（形如 `PHYSFS_swapULE64 (+ 12079230)`）。
   **偏移相同 = 同一处崩溃；偏移不同 = 换了地方崩。** 符号已被剥离，别指望函数名。
2. **用 `error.log` 最后一行 + 时间戳判断加载到了哪一步**：
   - `[no_game_date]` → **还没加载完**（启动期崩溃）；
   - `[1936.01.01.12]` 这类带日期的 → 已进入对局/界面。
   `logs/game.log` 里的 `Loaded N provinces` 是很好的进度锚点。
3. **把「改动前 / 改动后」两次运行做对比**——这是判断「是不是我改崩的」唯一可靠方法：
   - 打开 `--patterns` 模式，对比关键**关键词命中数**（见下表两个已复现症状）；
   - 再按归一化消息模板求差集，**只在改动后出现的新模板 = 你的回归**。
   - ⚠️ 陷阱：崩溃点提前会让日志整体变短，差集里会混进「只是因为跑得更浅才没出现」的项。**关键词定位比差集可靠。**
4. **先查历史**：按时间戳列出所有 `crashes/*/exception.txt`。**同样的偏移在你动手之前就反复出现 → 不是你造成的**；但仍要确认自己有没有把崩溃点「提前」。

### 三个已复现的 CTD 根因（照抄检查）

| 症状 | 根因 | 修法 |
|---|---|---|
| 加载期崩；日志有 `Only one national focus tree should be default, switching from X to X` | MOD 用**空文件**屏蔽原版同名定义（焦点树 / 持续国策等），那个空文件丢了 → 原版复活 → 与 MOD 的同名 id 撞车 | 恢复该空文件（3 字节 BOM 或 0 字节均可） |
| 进到某界面崩；日志有 `Could not find "X" in window Y`（`interface/*.gui`） | MOD 覆盖的 `.gui` 是**旧版本原版文件的副本**，缺新版新增的 GUI 元素 | 从原版同名文件把缺的元素块**原样插回**对应窗口；或删掉该覆盖 |
| **固定在某一天/某个日期节点崩**（最常见是"过了一天就闪退"）；日志有 `gui.cpp:931: Undefined GUI_TYPE: X - This will most likely crash the game` | `common/scripted_guis/*.txt` 里某个 `window_name = "X"` 在**任何 `.gui` 里都没有对应的 `name = "X"` 窗口**（未完成桩 / 改名后漏改）。跨日时引擎重建脚本窗口 → 空窗口指针 → `C0000005` | 新建/补一个 `containerWindowType { name = "X" ... }`；**临时代价 1 行**：把该 scripted_gui 的 `visible` 改成 `{ always = no }` |

> **为什么"第二天"才崩**：`context_type = player_context` 的脚本窗口只在玩家国求值，引擎把窗口重建集中在跨日节点，所以病灶（`gui.cpp:931`）出现在第 1 天末尾，崩溃落在第 2 天 01:00。

> ⚠️ **`parent_window_token` 不是坏 token**：`technology_tab` / `politics_tab` / `deployment_tab` / `top_bar` 等都在原版 `common/scripted_guis/_documentation.md` 的白名单里。别因为它"看着眼生"就下判断 —— 致命的是 `window_name` 指向的容器没定义。另外把 `context_type = player_context` 擅自改成 `decision_category` 前，先确认该 scripted_gui 真的被某个 `decision_category` 用 `scripted_gui = X` 绑定了（`grep` 全库），否则窗口会无处挂载。

### scripted_gui ↔ interface 交叉校验（改完必跑）

```python
# 1) 收集所有 interface/**/*.gui 里的 name = "X"
# 2) 收集所有 common/scripted_guis/*.txt 里的 window_name = "X"
# 3) 差集 = 孤儿窗口 = 必然闪退
```
现成脚本：`hoi4lint\window_check.py`（诊断用）、`window_check2.py`（带 parent token 清单）、
`verify_fix.py`（修复后校验：孤儿数 + 括号平衡 + `properties` 元素名 ↔ `.gui` 元素名一一对应）。

**修完后三查**：(a) 孤儿窗口数必须归 0；(b) 新 `.gui` 的花括号结尾 depth = 0 且**最小 depth ≥ 0**；
(c) `properties` 里声明的每个元素名都必须能在 `.gui` 里找到同名 `name`，且不多不少。
（`properties` 的 `image`/`frame` 是给**同名元素**动态赋值的 —— 名字对不上等于没接上。）

> 排查 `.gui` 用「元素 → 所属窗口」映射：对原版文件做花括号栈分析，取出每个元素块及其最近的 `containerWindowType` 父窗口名，再对照 MOD 同名文件里同名窗口是否缺这个元素。

### `interface/` 覆盖文件的系统体检

MOD 覆盖 `interface/` 下原版同名文件时，凡**体积明显小于原版**的（经验阈值 <70%）都是「旧副本」嫌疑，都缺新版元素、都可能在对应界面崩。一次性列出：

```
对每个 MOD interface/ 下的文件，若原版存在同名文件 → 算 体积比，按升序排列
```

## 第一步：锁定权威证据

```
<用户目录>/Paradox Interactive/Hearts of Iron IV/
    logs/error.log                      ← 最近一次运行，可能被截断
    crashes/<YYYYMMDD_HHMMSS>/logs/error.log   ← 崩溃现场完整日志，优先用这份
```

**务必选文件最大的那份 `crashes/*/logs/error.log`**——它包含整场加载+运行的全部报错，比 `logs/error.log` 完整得多（实测 11.5 MB vs 237 KB）。

日志格式自带 `file:line`，可直接定位：

```
[21:06:00][no_game_date][triggerimplementation.cpp:3153]: common/ai_equipment/generic_tank.txt:667: has_tech: Invalid tech
[21:05:50][no_game_date][trigger.cpp:700]: Invalid trigger 'hsa_country_flag' in common/decisions/DRA_sucrose_decisions.txt line : 1082
[21:05:51][no_game_date][effect.cpp:445]: Invalid effect 'end_wars' in common/national_focus/LAW_FocusTree_01.txt line : 4442
```

按「归一化后的消息模板」计数，先解决**数量最大**的那一类——通常是某个根因在每 tick 重复求值，能一次消掉几万行报错。

### ⚠️ 必须先按「文件属于谁」过滤（我漏做过一次，白干半天）

**`error.log` 不分来源，它把当前加载的每个 MOD 与原版的报错全都写在一起。** 直接拿它当「本 MOD 的工作清单」会把别的 MOD 的问题也算到自己头上。

实测：一份 825 处定位点的日志里，**只有 499 处属于目标 MOD**，其余 326 处属于另外 8 个外加 MOD / 原版（例如 `Unknown category: economy_decisions` 全来自不属于本 MOD 的 `common/decisions/DOD_hungary.txt`、`_generic_decisions.txt`）。

过滤方法（`scripts/errorlog_report.py` 已内建，见其 `in_mod()`）：

```python
# 建「相对路径小写 → 全路径」索引，报错路径 .lower() 查表命中才算本 MOD 的
idx = {}
for dp, _, fs in os.walk(MOD):
    for f in fs:
        idx[os.path.relpath(os.path.join(dp, f), MOD).replace("\\", "/").lower()] = True
# 命中 → 本 MOD 的问题；不命中 → 大概率是别的 MOD 或原版，别改
```

**反例（务必避免）**：看到 `Unknown category: X` 就去改本 MOD 的分类文件——先确认报错文件到底在哪。

## 第二步：判定标识符是否真的合法

报错说某标识符无效时，**必须**用原版统计来交叉验证，因为：
- 原版出现 0 次 → 大概率拼错或根本不存在；
- 原版出现很多次 → 标识符存在，报错的原因是**上下文/作用域用错**（例如效果写进了触发器块、必须带块却写了裸值）。

```bash
python scripts/errorlog_report.py --mod "<MOD根>" [--log <error.log>] [--patterns]
```

脚本会自动挑选**体积最大**的 `crashes/*/logs/error.log`，先给消息模板计数，再输出「MOD 内文件 + 真实行号」的工作清单，可直接照着改。只读，不会改文件。

## 第三步：查手册确认正确写法

**改之前一定先查规范**。优先使用项目自带的维基摘录（如果 `docs/` 下存在 `DOT_HOI4_Modding_Skills.md` 或类似名字的 HOI4 Modding 维基全集），它包含 Effect、Conditions、List of modifiers、Doctrine/Decision/Event/Character/Technology modding 等 53 页正文。检索方式：

```bash
# 在维基摘录里查某个效果/触发器的定义与参数
grep -n "| add_temporary_buff_to_units " docs/DOT_HOI4_Modding_Skills.md
grep -n "^| has_doctrine " docs/DOT_HOI4_Modding_Skills.md
```

没有本地摘录时用 WebFetch 查 `https://hoi4.paradoxwikis.com/Effect` / `/Conditions` / `/List_of_modifiers`。

**注意版本差**：维基反映的是**最新版**。若游戏版本较旧，维基里存在而游戏报 `Unknown effect-type` 的，就是「新版才有」——此时应改用旧版支持的等价机制（见 `references/version-gotchas.md`）。

## 第四步：落地修复（安全流程）

1. **先确认状态、先备份**：MOD 工作目录可能被 Git/外部副本整份覆盖（实测会连报告与修复一起抹掉）。每次开工先抽验一个上次修好的点（如 `grep "# FIXED:"`）确认还在，再备份：
   ```bash
   python scripts/mod_backup_verify.py backup --mod "<MOD根>" --out "<备份目录>"
   ```
   备份范围约 1~2 千个脚本文件，秒级完成。**不要**备份 `gfx/`（几万文件、体积大且很少需要改）。
2. **替换必须做存在性断言**：按「行号 + 该行必须包含的原文」双重校验再改，行号会因增删而漂移，只靠行号会改错行。见 `scripts/fixer_template.py`。
3. **先 dry-run 到 0 MISS 再 `--apply`**：dry-run 常会暴露自己脚本的缺陷（正则少了 `re.M`、上一处改动导致行号漂移、`expect` 数量算错）。
4. **逐条留痕**：在改动行尾加 `# FIXED: <说明>`，方便作者 `grep FIXED:` 复核，也方便回滚。
5. **改完校验**：
   ```bash
   python scripts/mod_backup_verify.py verify --mod "<MOD根>" --absent "<已修复模式的正则>"
   ```
   括号平衡校验**必须忽略 `#` 注释与 `"..."` 字符串**，否则会误报。
6. **让用户跑一次游戏，用新日志做「修复后校验」**：对比日志体积与各模式的计数衰减，这是最有力的成效证据（实测 11.5 MB → 393 KB，`has_tech` 报错 175,740 → 0）。**残留清单同时就是下一轮的工作清单。**

## 修复分级：哪些能直接改，哪些必须先问作者

从 `error.log` 拿到的清单里，**报错数量 ≠ 该不该改**。改之前先归类：

**A. 可直接改（纯语法 / 纯恢复，不改变游戏行为）**
- 拼写与命名错：`defence→defense`（单位内）、`aluminum→aluminium`、`hsa_country_flag→has_country_flag`、`navy_doctrine_cost_factor→naval_doctrine_cost_factor`、`exist→exists`、`socre→value`、`days_sonce→days_since`……
- 缺包裹块 / 块写错位置：`custom_trigger_tooltip = X` → `{ tooltip = X }`；`has_country_leader = X` → `{ character = X }`；`custom_effect_tooltip`（效果）出现在触发器位 → `custom_trigger_tooltip`；`on_monthly_*` 缺 `effect = { }` 包裹层。
- 值域错：布尔写成 `YES`/`NO`、枚举成员名错（查 `common/script_enums.txt`）。
- 键在本版本已移除（`Unexpected token: <键>`）→ **注释掉**而非删除（被拒的键本就不生效，行为零变化）。
- 结构性的**路径/文件名笔误**（如 `HSR = "countries/HRS.txt"` 而磁盘上是 `HSR.txt`）。

**B. 必须报告作者拍板（会激活原本失效的内容 = 改变玩法）**
- 回填「残缺副本」丢失的子单位 / 分类 / 焦点树。
- 修国策树结构，让原本游离或被吞的 focus 生效。
- 改 AI 装备设计的模块名（会改变 AI 选装）。
- 补上从未定义的决议分类且该决议**无 `visible` 门槛**（会立刻冒出）。

**判据**：改动是「让原本就该生效的重新生效」，还是「让原本没生效的开始生效」？后者就是玩法变更。

> 作者**经常故意把内容「放坏」来临时禁用**：`allow_branch` 挂一个永不设置的旗标、`available = { always = no }`、把 focus 留在焦点树外、文件里写 `#以下不可用` / `#暂时禁用`、给决议加 `has_country_flag = X_unlocked` 门槛。看到这些痕迹 → 默认「有意为之」，只报不改。

## 高频错误 → 修复对照

| 报错 | 真实原因 | 正确写法 |
|---|---|---|
| `has_tech: Invalid tech`（内容是学说名） | 1.19 起陆战学说从科技树迁到 `common/doctrines/grand_doctrines/`，**而且 id 改过名** | `has_doctrine = <1.19 学说 id>`：`new_mobile_warfare`（旧 `mobile_warfare`）/ `superior_firepower` / `grand_battleplan`（旧 `trench_warfare`）/ `mass_assault` |
| `Invalid effect 'add_temporary_buff_to_units'` | 该效果旧版不存在 | 写进能力的 `unit_modifiers` |
| `Non assign effect is not enclosed in {}: uncomplete_national_focus` | 该效果必须带块 | `uncomplete_national_focus = { focus = X }` |
| `Non assign trigger is not enclosed in {}: custom_trigger_tooltip` | 触发器必须带块 | `custom_trigger_tooltip = { tooltip = X }` |
| `Invalid trigger 'custom_effect_tooltip'` | 把「效果 tooltip」用在触发器块 | 换 `custom_trigger_tooltip` |
| `Invalid effect 'end_wars'` | `end_wars` 是 `puppet` 的子键 | `puppet = { target = X end_wars = yes }` |
| `Invalid effect 'limit'` | `limit` 只能出现在 `if`/`else`/`random_*` 内 | 外面补一层 `if = { }` |
| `Invalid effect 'free_building_slots'`（在 `random_owned_state` 等**效果块**内） | 它是**触发器**，被裸写进效果位 | 用 `limit = { free_building_slots = { building = infrastructure size > 1 } }` 包裹。⚠️ 只包**日志点名**的那些——同一文件里合法放在 `limit`/触发器位的**不要动**（盲包会嵌套 `limit` 反而报错；本 MOD 一个文件里 27 处只有 2 处非法） |
| `Missing icon shine for focus: <id>`（`nationalfocus.cpp:642`） | 引擎按 `<icon名>_shine` 找国策高光 spriteType；MOD 的 `interface/*.gfx` 是**部分覆盖**，只定义了图标本体、丢了 `_shine` 变体 | 见下节「focus icon shine 批量注册」 |
| `Invalid effect 'value'`（在 `add_popularity` 内） | 参数名错 | `popularity = …` |
| `Unknown modifier: civilian_use` | 修饰符名错 | `civilian_factory_use` |
| `Unknown modifier: stablity_factor` | 拼写 | `stability_factor` |
| `Unknown modifier: army_defense_factor` | 英式拼写 | `army_defence_factor` |
| `Invalid trigger 'exist'` | 拼写 | `exists` |
| `Invalid trigger 'hsa_country_flag'` | 拼写 | `has_country_flag` |
| `Invalid trigger 'is_at_war_with'` | 不存在 | `has_war_with` |
| `Invalid trigger 'has_government_in_exile'` | 词序 | `is_government_in_exile` |
| `Invalid trigger 'random_owned_states'` | 复数不存在 | `random_owned_state` |
| `Invalid trigger 'has_faction_members'` | 不存在 | `is_in_faction` |
| `Unknown trigger-type: has_division_template` | 旧名 | `has_template = "师模板名"`（原版 99 处） |
| `Unknown effect-type: create_division_template` | 旧名 | `division_template = { … }`（作效果直接写，原版 1462 处） |
| `Invalid trigger 'is_core'` | 不带对象 | `is_core_of = <tag>` |
| `Unknown modifier: targeted_modifier`（在 `modifier = { … }` 内） | `targeted_modifier` **不是** modifier 成员，而是 **decision 的顶层键**（与 `modifier`、`days_remove`、`ai_will_do` 同级） | 移出 `modifier` 块、挂到 decision 顶层。原版实证 `common/decisions/GRE.txt:2479`（原版 decisions 共 48 处：GRE/MEX/NOR/POL/PRC/SIA/SWI/USA/`_exiled_governments_*`），写法 `targeted_modifier = { tag = GER attack_bonus_against = 0.05 defense_bonus_against = 0.15 }`；同一批键在 `common/ideas/`（481 处）和 `common/country_leader/00_traits.txt`（16 处）里也合法 |
| `Invalid effect 'NP'` / `Unknown effect-type: <大写三字母>`（当作效果用） | 把**国家 tag** 当效果调用了（`NGP = { … }`），而该 tag 在 `common/country_tags/` 里根本没有定义 | 先跨全部已加载 MOD + 原版确认 tag 是否定义：未定义 → 该块整体静默失效，注销并报作者补 tag；已定义 → 用正确的 scope 调用 |
| `Unknown modifier: air_close_air_support_attack_factor` | CAS 机**没有**攻击加成修饰符 | `air_close_air_support_org_damage_factor = 0.1`（原版 `common/doctrines/subdoctrines/air/` 5 处；`..._attack_factor` 原版 0 处） |
| `Not a valid value: <tag>`（`leave_faction = <tag>`） | `leave_faction` 只取**布尔** | `leave_faction = yes`（原版 Effect 表无参形式） |
| `Unknown modifier: <name>_production_speed_factor`（装备级，如 `fighter_production_speed_factor`） | 1.19 **没有装备级生产率修饰符** | 只有建筑级 `production_speed_<建筑>_factor`（如 `production_speed_arms_factory_factor`，原版 514 处）与 `license_<类别>_production_speed_factor`；装备级只能注销 |
| `Invalid db object: motorized_0.` | 装备类型旧名 | `motorized_equipment_0`（原版 9 处，`motorized_0` 0 处） |
| `Invalid effect 'create_alliance'` | 不存在 | `add_to_faction = <tag>` |
| 触发器位出现 `every_owned_state` / `every_other_country` | 效果当触发器用 | `all_owned_state` / `all_other_country` |
| `Invalid effect 'modifier'`（在事件 option 内） | option 没有 `modifier` 子块 | 剥掉包裹，效果直挂 option |
| `add_tech_bonus: Unknown technology category` | 类别名错 | 取 `common/technology_tags/` 里的类别 |
| `days_since_decision_taken` 之类的「不存在触发器」 | 该触发器在 1.19 与原版中均无 | 改用变量自行计时，或去掉失效条件 |
| `Unknown category: X` / `Unknown category for : Y` | **决议分类文件被残缺同名副本覆盖**，原版分类定义丢失 | 从原版回填缺失的顶层块（见下节 3） |
| `Unknown category: X`（X 是本 MOD 自造名，如 `LYY_*` / `INA_*`） | MOD 的决议文件用了**从未定义过的分类**（作者只写了决议、忘了在 `common/decisions/categories/` 里定义分类）→ 整组决议被引擎静默忽略 | 在 `common/decisions/categories/` 下补一个最小定义块 `X = { icon = … }`（也可新建文件）。**先看 `visible`/`available` 有没有 `always = no` 或旗标门槛**：有门槛 → 补定义是纯恢复、不会无条件冒出；无门槛 → 会让决议立刻出现，属玩法变更，先问作者 |
| `Not a valid value: YES` / `: NO` | 触发器布尔值写成了大写 `YES`/`NO`（引擎只认 `yes`/`no`；大写只在脚本关键字 `AND/OR/NOT/IF` 上合法） | 改 `= yes`。注意 `LIMIT` 也是错的，应为 `limit` |
| `Value does not belong to designated Script EnumType: X not in script_enum_equipment_bonus_type` | `equipment_bonus` 里用了非枚举成员名（如 `CAS_equipment`、`anti_air_brigade`） | 查原版 `common/script_enums.txt` 的 `script_enum_equipment_bonus_type` 成员表：应为 `cas` / `anti_air` / `anti_tank` / `fighter` / `submarine` … |
| `Unexpected token: focus`（在 `common/national_focus/*.txt`） | 两种：①**多/少一个 `}`** 让焦点树提前闭合，之后的 `focus = {}` 全部游离在树外；②某个 focus **缺自己的收尾 `}`**，把后面所有 focus 变成它的子块（整条线被吞） | 用「花括号深度轨迹」找异常：树应在 depth 1 内包住所有 focus。修法 = 删掉多余的 `}` / 在缺括号的 focus 末尾补 `}`。⚠️ **会一次性激活所有游离/被吞的 focus，改变国策树布局与玩法 → 先报告作者**（作者常用「故意游离」来临时禁用一段国策，文件里往往留有 `#以下不可用` 之类注释） |
| ⚠️ **括号错误会互相抵消**（全文 `depth` 仍为 0，别被「括号平衡」骗过） | 一个「多余的 `}` 提前闭树」+ 一个「缺失的 `}`」同时存在 → 总深度抵消，整体校验显示 balanced，但结构已错。实测：`FON_focus.txt` 在 926 行多一个 `}`（提前关闭 focus_tree，其后 7 个 focus 全部游离，日志报 7 条 `Unexpected token: focus, near line: 944/970/…`），而 `FON_Total_loss_of_control` 又缺收尾 `}`（把它后面所有 focus 吞成子块） | **不能只看总平衡**，必须打「逐行 depth 轨迹」（`depth==0` 的行应只有文件首尾）+ 花括号**栈追踪**定位未闭合的 `{` 属于哪个块。修法：两处一起改——注销多余的 `}`、补齐缺失的 `}`，改完总 depth 依旧 0 |
| `Unexpected token: portraits`（在 `create_field_marshal` 内） | `create_field_marshal` **不接受 `portraits` 块**（那是角色/领袖文件的 schema） | 改成 `gfx = "gfx/leaders/XX/Name.dds"`（另有 `name` / `desc` / `traits`）；手册 `create_field_marshal` 条目为准 |
| `bad mission type: MISSION_X` | `ai_strategy { type = naval_mission_threshold id = MISSION_X }` 用了不存在的任务名（原版 `common/` 里 `MISSION_*` 只有 `MISSION_PATROL` / `MISSION_CONVOY_ESCORT`） | 换成有效任务名，或直接注释掉该 `ai_strategy` 块（本来就无效，行为零变化） |
| `Unexpected token: integer`（在 `randomize_variable` 内） | `randomize_variable` 的分布参数写法不对 | 照原版用法（分布用 `distribution`，取整走 `set_variable_to_random` 等）改写 |
| `Unexpected token: IF`（在 `on_actions` 里） | `on_monthly_*` 等**缺少 `effect = { }` 包裹层** | 补上包裹层（大写 `IF` 本身是合法的！） |
| `Non assign trigger is not enclosed in {}: has_country_leader` | 该触发器必须带块 | `has_country_leader = { character = X }` |
| `Not a valid value: LAW`（`has_same_ideology = LAW`） | 它是**布尔**（与 ROOT 比），不接受目标参数 | `LAW = { has_same_ideology = yes }` |
| `Unexpected token: socre` | `add_autonomy_score` 的参数名 | `value = <float>`（另有 `localization`） |
| `Unexpected token: defence`（单位定义内） | 单位属性是 `defense`；`defence` 只在**地形块**里合法 | 改 `defense =`；别误改地形块 |
| `Invalid resource: aluminum` | 资源名用英式拼写 | `aluminium` |
| `Unknown modifier: stability` | 没有裸 `stability` | `stability_factor` |
| `Unknown modifier: navy_doctrine_cost_factor` | 拼写 | `naval_doctrine_cost_factor` |
| `Unexpected limit in an else block` | `else` 不允许 `limit` | 改成 `else_if = { limit = { … } … }` |
| `Token from / is_ai / any_other_country is not supported within the allowed trigger` | 决策 `allowed` 块不接受跨国外作用域与 `is_ai` | 移到 `available`（或 `target_trigger`） |
| `Invalid module name ...: tank_xxx_4` | 模块名与游戏版本错配。1.19 **一级模块无 `_1` 后缀**（`tank_medium_cannon`），各系列最高档还不一样 | 逐一到原版 `common/units/equipment/modules/` 核对，别猜 |
| 同一行键名写了两遍（`a = a = value`） | 手抖 | 收敛为一处，否则会被当成「无效模块名」 |
| `Unknown modifier: mora_cost_daily` 这类**自造名** | 脚本层**无法**创造新修饰符/新资源 | 只能改用现成机制（换修饰符或自定义动态修正） |
| `Unexpected token: character` | `add_country_leader_trait` 不接受 `character` 键 | `add_country_leader_trait = <trait>`（作用于现任领袖） |
| `recruit_character should only happen in game/history files` | 写在事件里 | 迁到 `history/countries/` |
| `Unexpected token: <键名>`（在 `sub_units` 等单位块里） | 该键**引擎完全不认识**（多为旧版才有，或被某个 DLC 移除）→ 写了等于没写 | 注释掉或删掉。**判定关键：只有 `Unexpected token` 才证明键非法**；原版没用过的键不代表非法（见下节反直觉点 3） |
| `No localisation for modifier_experience_gain_<unit>_<x>_factor` | 自建海军/陆军单位漏了引擎为每个单位自动生成的 3 个修正符文案 | 在 `localisation/<lang>/` 补 `modifier_experience_gain_<unit>_{training,mission,combat}_factor`（原版 `modifiers_l_*.yml` 每个单位都有） |
| `Unexpected token: corps_commander` / `field_marshal` / `country_leader` / `navy_leader`（在角色文件里） | 这些角色块被写进了 `portraits = { }` **内部**。`portraits` 只接受 `civilian` / `army` / `navy` 三个分类键 | 把角色块移到 `portraits` 的**兄弟层**（即 `portraits { … }` 的收尾 `}` 之后）。原版实测：角色块在 portraits 内 0 次、之后 238 次。修法 = 把 `portraits` 的收尾 `}` 上移到第一个角色块之前，**括号总数不变** |
| `Malformed token: X.N`（事件 id） | 事件 `id = X.N` 的**前缀** `X` 没有任何 `add_namespace = X` 声明 → 整个事件被引擎丢弃（本地化键也一并失效） | 改**声明**而不是改 id：`add_namespace = X`。若 MOD 里 10 个事件 id 都是 `INA_News.N`，就把多写的 `add_namespace = INA_News_News` 改回 `INA_News` |
| `add_resource` 报参数错 / 资源没加 | 参数名写成了 `value = N` | 参数是 `amount = N`：`add_resource = { type = steel amount = 150 }` |
| `is_triggered_only = n`（或 `Y`/`1`）不生效 | 该键只认布尔字面量 | `= yes` / `= no`（`= n` 不是合法值，事件触发行为会异常） |
| `add_opinion_modifier` 用了 MOD 自造名但不报错也不生效 | 该 `modifier` 必须在 `common/opinion_modifiers/` 里定义过 | 先 `grep` `common/opinion_modifiers/` 确认该 id 存在；不存在就只能改用已定义的，或补一个定义块 |
| 事件里出现 `visible` / `portraits` / `trigger` | 这些键**不属于事件 schema** → 被静默忽略（本来就不生效） | 若只想「零行为变化」地消除报错，**注释掉**即可（删/注释前后行为一致） |
| `has_game_rule: game rule X does not exist` | `has_game_rule = { rule = X … }` 里的 `X` 用了**块内 `name =` 的本地化键**，而不是**规则的块名(id)** | 改成块名。本 MOD 例：`MOT_Way = { name = "MOT_ChoosetheWay" }` → 脚本须写 `rule = MOT_Way`（同理 `FAV_Way` / `AN_Way` / `RAG_Way` / `DRA_Way`）。判据：同 MOD 别处已写对 + `option=` 能对上该规则的 option 名 |
| `has_game_rule: game rule <原版规则名> does not exist`（如 `ENG_ai_behavior`） | **`common/game_rules/00_game_rules.txt` 是残缺同名副本**——MOD 复制了原版同名文件却只留一部分规则，把原版 66 条（`*_ai_behavior` / `*_colonization_status` / `*_fragmentation_status`）整份覆盖掉 | 把原版缺失的顶层块**并回** MOD 文件（属 A 类：会恢复原版 AI 开关，先报作者） |
| `add_tech_bonus: Unknown technology category X` | `category =` 的值必须是 `common/technology_tags/*.txt` 里 `technology_categories = { … }` 的成员，作者常误写设备名 | 查原版 `00_technology.txt` 的成员表：`industry` / `artillery` / `electronics` / `armor` / `train_tech` / `synth_resources` / `light_air` / `medium_air` / `heavy_air` / `infantry_tech` / `excavation_tech` / `air_equipment`。⚠️ 命名不匹配 ≠ 拼写错，**不能靠猜**，要作者逐条确认（属 A 类） |
| `Unexpected token: =`（在 `common/bop/*.txt` 的 `side`/`range` 里） | `icon = `（或其它键）**值被写空** → 解析器吃掉下一行的键，于是下一行的 `=` 变成意外 token。报错行是"被吃掉那行"的**下一行** | 补上正确的值（如 `icon = GFX_bop_XXX`）。删掉空键会变成"无图标"，不算干净修法 |
| `Duplicate database id X: X`（在 `common/military_industrial_organization/organizations/`） | 同一个 MIO 组织**在两个文件里各定义一次** | 先确认两份是否逐行相同 + 全库是否无引用；是 → 删一份，行为零变化 |
| `Invalid dynamic modifier X`（`add_dynamic_modifier` / `remove_dynamic_modifier`） | `common/dynamic_modifiers/` 里没有 id 为 `X` 的定义 | 补定义，或删掉调用（属 B 类） |
| `Event is set to trigger every day` | **不是错误，是提示**：事件 `is_triggered_only = no` 且没写 `mean_time_to_happen` | 无需修；不想天天触发就加 MTTH 或改 `is_triggered_only = yes` |
| `<ns>.<n>: No valid option for event. This might be a script bug` | 事件所有 `option` 的 `trigger` 在常见国家下都不成立 → 玩家看不到选项 | 补一个兜底 option（属设计决定，先报作者） |
| `divide_temp_variable: Trying to divide by zero. This is NOT what you want!` | `divide_temp_variable = { A = B }` 的 `B` 可能是 0 | 外面套 `if = { limit = { check_variable = { B > 0 } } … }` |
| `Unknown modifier: civilian_use` | 拼写 | `civilian_factory_use`（值是"用几个民用工厂"，故写成整数如 `= 5`） |
| `Unknown modifier: navy_doctrine_cost_factor` | 拼写 | `naval_doctrine_cost_factor`（同块里 `land_doctrine_cost_factor` / `air_doctrine_cost_factor` 就是对的） |
| `Unknown modifier: stability`（在 modifier 块内） | 没有裸 `stability` | `stability_factor` |
| `add_metal` / 其它非资源名 | MOD 的 `common/resources/` 只有 `oil` / `aluminium` / `rubber` / `tungsten` / `steel` / `chromium` / `coal` 之类；脚本层**不能新造资源** | 改用 `add_resource = { type = <已有资源> amount = N }`（属 B 类，要作者定） |
| 日志体积几十 MB 但报错种类很少 | `error.log` **每帧重复**同一条报错 | **分析前必须先按 (文件, 行号) 去重**，再看行数；`x<次数>` 高 ≠ 问题多 |
| 大量贴图缺失 | 资源缺口 | 补图或删 `GFX_` 引用 |

## focus icon shine 批量注册（可复用工作流）

**症状**：日志大量 `Missing icon shine for focus: <id>`。**机制**：渲染国策时引擎查找 spriteType `<icon名>_shine` 作高光；找不到就报。

**要点**：
- focus 的 `icon =` 是 **sprite 名**（如 `goal_ASA` / `GFX_goal_xxx`），不是 dds 路径。
- shine 复用 icon 自身图片（用户常明确要求「不新增图片」）：shine 的 `texturefile` = 该 icon sprite 的 `texturefile`；照抄 MOD 既有 shine 样例的完整结构（`effectFile = "gfx/FX/buttonstate.lua"` + 两个 `animation`，`animationtexturefile` 用 `gfx/interface/goals/shine_overlay.dds`）。
- **落地方式（用户偏好）**：在该 icon 的 SpriteType **定义正下方**插入 shine SpriteType（不是新建汇总文件）。

**步骤**：
1. 解析 `common/national_focus/*.txt`（若存在也含 `common/continuous_focus/`）取 `focus_id -> icon`。
2. 解析 `interface/**/*.gfx` 建 `spriteName -> texturefile` 与已存在的 `_shine` 集合；**同时解析原版同目录**（MOD 只是部分覆盖，很多 icon 定义在原版），MOD 覆盖原版。
3. 目标 = `作 focus 图标用 ∩ MOD gfx 里有定义 ∩ 缺 <name>_shine`。对每个目标，在其 SpriteType 块收尾 `}` 之后插入 shine 块。
4. 三校验：括号 depth=0、BOM 原样、CRLF 一致（`lf_only=0`、无 `\r\r\n`）。

**两个必踩的解析坑**：
- **focus 块取 id/icon 要取「第一个嵌套块之前」**：`focus = {` 自身的 `{` 之后、下一个 `{` 之前那段才是直接作用域。若错取成「`focus =` 后面第一个 `{` 之前」（=空），只能解析到极少数 focus（实测 177 vs 正确 3526）。
- **gfx 的 `SpriteType` 大小写混用**：有的文件写 `SpriteType = {`（大写 S）。解析必须 `re.IGNORECASE`，否则整份文件被漏掉（实测 DOT_Focus.gfx 全用大写）。

**验证覆盖**：修完把日志里 `Missing icon shine for focus` 的 focus id → icon 映射，核对每个 icon 现在都有 `_shine`。

### ⚡ 更省事的方案：先试 `icon = GFX_goal_unknown`（2026-09 实证，优先用这个）

若用户**不要求保留原图**，把无效 icon 直接改成 `icon = GFX_goal_unknown` 即可：

- 原版 `interface/goals.gfx` 有 `GFX_goal_unknown`，且 `goals_shine.gfx` 有对应的 `GFX_goal_unknown_shine` → **一改同时消掉 `Missing icon for focus` 与 `Missing icon shine for focus` 两类报错**（实测 397 处 icons + 398 处 shine 全覆盖，零遗漏）。
- 反向坑：若某个 focus 的 icon 值**本身以 `_shine` 结尾**（如 `GFX_Goal_X_shine`），引擎会去找 `GFX_Goal_X_shine_shine` → 基名存在也照样报 shine 错。这类也要一并改成 `GFX_goal_unknown`（或把 `_shine` 去掉）。
- 只有用户明确要求「保留原图标 / 复制 shine 块」时，才走上面的 shine 注册流程。

### ⚠️ 但先用占位图之前，务必做一次 sprite 名双向匹配（2026-09-20 实证，比重更大）

用户说「Missing icon 就统一给 `GFX_goal_unknown`」时，**先别直接照做**——日志里的 `Missing icon for focus` 只说明「按这个名字查不到 sprite」，其中相当一部分是**名字写错**，真身 sprite 就在库里。本 MOD 397 条里 **132 条可复原**（前后缀/大小写/拼写），只有 265 条是真·无图。

两侧都可能出错，所以要**双向**试：

| 现象 | 例 | 修法 |
|---|---|---|
| focus 里漏了前缀 | `DVA_Venti_alone` → `GFX_DVA_Venti_alone`（18 条） | 逐个补前缀 |
| **MOD 的 sprite 本来就定义成裸名** | `GFX_goal_DOT_02` → `goal_DOT_02`（DOT_Focus.gfx 里就是裸名） | **剥掉** `GFX_`/`GFX_goal_` 前缀再查 |
| 复数/typo | `GFX_goals_EAW_56`→`GFX_goal_EAW_56`；`GFX_goal_generic_occypy_…`→`…occupy…`；`GFX_goal_generic_support_democracy`→`GFX_goal_support_democracy` | `difflib` 近似（cutoff 0.87~0.88） |
| 原版自己的拼写错误 | `GFX_Goal_Victory_of_Fascism` → `GFX_Goal_Victory_of_**Fac**ism` | 照抄原版错名 |
| `icon = unknown` | `unknown` → `GFX_goal_unknown` | 与占位图等价，可直接归一 |

**算法**：`os.walk(原版 + 所有已启用 MOD)` 收 `interface/**/*.gfx|.gui` 里的 `name = "…"` 建全量 sprite 名集合（~45k）→ 对每个坏值依次试 `exact` → `{补/剥 前缀}` 组合 → **大小写不敏感** → `difflib.get_close_matches(cutoff≈0.88)`。命中后**再查 `<命中名>_shine` 是否也存在**：不存在的那几条才是真正需要走 shine 注册流程的（本 MOD 132 条里只有 6 条）。

**必须人工否决低置信度近似**：本 MOD 有 1 条 `GFX_MOT_EWAY3` 被近似到了 `GFX_MOT_EWAY1`（库里只有 1 号），语义完全不同 → 这类维持占位图，别硬套。

**判据**：`PBF`（79 条，PBF = 刺玫会国家 TAG）全库既无同名 sprite 也无同名图片 → 只能占位；`GFX_FOD_xxx`（约 40 条）图片目录 `gfx/interface/goals/FOD/` 里也没有对应文件 → 只能占位。**用「有没有同名图片」二次确认，能避免把该占位的硬修成错图。**

## 作用域 / 引用类高频修法（1.19 实证，2026-09 汇总）

排查原则：**日志报的「块首键名 / 行号」往往不是病根**，病根常在块内某个键、或**引用的对方**。以下每条都做过全库核验。

| 日志 | 病根 | 正确修法 |
|---|---|---|
| `Trigger failed to validate: …: free_building_slots` | 块内写了 `include_locked`，而 `building` 是 `infrastructure` / `air_base` | 删/注销该 `include_locked` 行（原版 infra 177 处、air_base 79 处从不用该键） |
| `Invalid scope type for effect set_state_controller` | 写在 state 作用域（如 `every_state`）内 | 改 `set_state_controller_to = <COUNTRY>`。**手册：`set_state_controller = <state>` 是国家作用域效果（参数为 state）；`_to = <country>` 才是 state 作用域效果**（原版 `common/decisions/GER.txt` 在 `every_state` 内即用 `_to`） |
| `Invalid scope type for effect add_extra_state_shared_building_slots` | 写在国家作用域（focus `completion_reward` / decision 效果） | 该效果是 state 作用域 → 须包 `capital_scope = {}` / `every_owned_state = {}` 等（属改玩法，先问作者） |
| `Invalid scope type for trigger is_attacker` | 写在 `any_other_country` 等非 combat 作用域 | 注销（is_attacker 只有 combat 作用域可用） |
| `Invalid effect 'limit'`（`Unknown effect-type: limit`） | `limit = {}` 被**裸写进效果块**（`FROM = {}` / `PREV = {}` / `on_action` 的 `effect = {}` 等）。`limit` 本身合法，但它只能作为 `if` / `else_if` / `random_*` / `every_*` / `any_*`（效果版）的**子键** | ✅ **真实修复**：把它套进 `if`，并用 `if` 包住**它后面那一整段效果**：<br>`FROM = { if = { limit = { <触发器> } <效果…> } }`<br>⚠️ 三个坑：① **不是把 `limit` 改名成 `if`** —— 块内装的是触发器，改名后引擎会拿 `has_global_flag` 当效果解析；② **收尾 `}` 要搬家** —— `if` 必须覆盖整段效果，所以原来的 `}` 删掉、在效果段末尾补一个 `}`；③ 顺手核作用域（见下条）。<br>❌ 直接 `#` 注销只是"消报错"，效果会**永久失效**——除非引擎确无等价写法且用户同意（本 MOD 已因此回滚过一批） |
| （顺手核）`is_ai` / `tag` 等写进州作用域 | 在 `on_actions` 里 `FROM` 是**被炸的州**（手册 on_actions 表 + 原版 `00_on_actions.txt:384` 的 `on_nuke_drop` 实证：`FROM = { is_core_of = … }` / `state = …`，且同块用了 state-only 的 `controller` / `remove_building`）。`is_ai` 是**国家作用域触发器**（手册「General **country-scoped** triggers」）。而 `From = { is_ai = yes }` 写在 `FROM = { … }` 内，`From` 仍指同一个州 → 作用域不符（引擎多半静默判假，比报错更危险） | 用 `owner = { is_ai = yes }`（手册：`owner` 可用于 state 作用域 → 取其所有者国家）。同理 `controller = { … }` 取控制者。**普遍规律**：手册查触发器的作用域前缀（country-scoped / state-scoped），州作用域里要测国家属性就加 `owner = { }` |
| `Error in focus: A`（且 A 的块看着没问题） | **十有八九是 B 的 `mutually_exclusive` 写错或自指**（`focus = A` 要求 A↔B 对称） | 修 B 的互斥指向。实测三例：名笔误（`MOT_PE_EB_Make_Emmigration`→`Attract_Emmigration`）、**自指**（`ChurchOppo_Good` 指自己）、词序/前缀错（`importance_Wind_Glider`）。另有 `relative_position_id` / `prerequisite` 要求目标 focus **在文件中更早出现**，否则注销该项 |
| `Invalid focus scripted in trigger. has_completed_focus = X` | X 不存在。**先用 `difflib.get_close_matches(X, 全库 focus id)` 找近似**再决定 | 高相似 → 改名（实测：`GER_rhineland`→`GER_remilitarize_the_rhineland` 旧版 id；`DVA_Mona2`→`DVA_Mona02`；`LYY_FC_Keqing_Ganyu_Alliance`→`LYY_FC_Ganyu_Keqing_Alliance`）；无候选 → 注销 + `#` 备注 |
| `Invalid dynamic modifier` / `add_timed_idea: Invalid idea` / `has_idea: X is not A valid Idea` / `has_active_mission` | 引用的标识符未定义 | 先用「前缀替换 + 全库 id 集合」找同族真名（实测 `MOT_Wonder_DM_*` 定义其实叫 `LYY_Wonder_DM_*`）；**同族只有一个成员时也要小心**（`…People2` 而库里只有 `…People1`，可能是作者未完成的第二阶）——拿不准就注销 + 备注 |
| `Not a valid compare token in trigger '='` | 触发器里 `date = 1937.9.13` 用了等号 | 日期比较只能用 `< > <= >=` → 改 `date > …` |
| `Unexpected token: who` | `has_opinion = { who = X }` | 键名应为 `target` |
| `Unexpected token: location` | `create_unit` 内写 `location =` | 手册无该键 → 注销（单位默认生成于当前 state） |
| `recruit_character should only happen in game/history files` | 在 events 里调用 | 注销（或把角色招募移到 `history/`） |
| `unknown rule 'X' in file common/ideas/…` | idea 的 `rule = {}` 块内写了非 1.19 键 | 注销该键。判定：原版 ideas 全库 0 次使用（实测 `can_justify_war` / `can_be_justified_against` / `can_be_called_to_war` 全部非法；合法的是 `can_create_factions` 等） |
| `has_game_rule: game rule option Y is not valid for the rule Z` | 选项名与规则定义里的 option 不一致 | 查规则定义块里的 option 真名（实测 `MOT_FAVRightUnion_Route`→`MOT_FAVRightUnion`） |
| `has_game_rule: game rule X does not exist` | **MOD 覆盖了 `common/game_rules/00_game_rules.txt` 但只写了子集**，原版独有规则全丢（实测丢 66 条） | 短期：注销该 `has_game_rule`；根治：把缺失规则回填（属玩法变更，先问作者） |
| `Unknown technology category X` | `add_tech_bonus` 的 `category =` 不在 `common/technology_tags/00_technology.txt` 的合法类别表（1.19 共 299 个）内 | 逐条换成合法类别（**改类别=改玩法，先问作者**），别用设备名当类别 |
| `Equipment category differs` + `Unbuildable plane variant` | `create_equipment_variant` 的模块与 airframe 类型不匹配（如 `small_plane_cas_airframe_*` 上装 `bomb_locks`） | 对照原版 `common/units/equipment/modules/00_plane_modules.txt` + 原版同型变体（`common/ai_equipment/ENG_planes.txt`）改模块；**属改玩法，先问作者** |

**判定「引用的东西是否存在」的两条铁律**：
1. **跨 9 个 MOD + 原版一起搜**（`conditional_surrender`、`peace_*` 由别的 MOD 提供，只看本 MOD 会误判）。
2. **同名不等于同类**：`DVA_Mona2` 是**角色 token**，而 Mona 焦点链的真实 id 是 `DVA_Mona1/Mona02/Mona3`。查 focus 存在性必须取 `focus = { id = X }` 里的 `id`，不能靠前缀匹配。



## 四类「静默」大坑（不报错或报错指向别处，但会毁内容）

1. **同名文件覆盖原版**：HOI4 按「相对路径 + 文件名」覆盖原版，MOD 里放一个同名文件，原版那份就整份失效。
   - ⛔ **不要看到空文件就删！**（我踩过这个雷，代价是一次 CTD）MOD 作者常**故意**放一个 0 字节 / 3 字节（仅 UTF-8 BOM）的同名文件来**屏蔽**原版定义，因为 MOD 自己的另一个文件定义了**同一个 id**。典型案例：`common/national_focus/generic.txt`（3 字节 BOM）屏蔽原版焦点树，因为 MOD 的 `DOT_generic.txt` 也定义了 `id = generic_focus`。删掉它 → 原版复活 → 两个同名 id 同时存在 → **加载期直接 CTD**，日志特征：
     ```
     nationalfocus.cpp: Only one national focus tree should be default, switching from generic_focus to generic_focus
     ```
   - **正确判定顺序**：
     1. 该目录在 `.mod` 的 `replace_path` 里吗？在 → 原版整目录不加载，空文件只表示「MOD 无此内容」，删除无影响。
     2. 不在 `replace_path` 里 → **在 MOD 全库搜索是否有别的文件定义了同一个 id**。有同名 id → 这个空文件是**有意屏蔽**，**必须保留**；没有同名 id → 才**可能**是事故痕迹。
     3. 拿不准一律**不删**。空文件是惰性的（不报错、不生效）；删错会崩。
   - 若确实想删掉某条原版内容，用 `replace_path`，不要用空文件。
2. **`replace_path` 误判**：动手前先读生效的 `.mod` 描述文件（在用户目录 `mod/` 下，**不是** MOD 工作区里的同名副本），确认 `replace_path` 列表，否则会把「有意替换」当成 bug、或把「事故覆盖」当成正常。
3. **【更隐蔽】残缺同名副本**：同名覆盖不要求文件为空——**只写了一部分的副本**同样会让原版那份失效，于是原版独有的定义凭空消失。
   - 真实案例：MOD 的 `common/decisions/categories/` 副本丢掉了 `economy_decisions` / `fascism_on_the_rise` 等 4 + 23 = 27 个分类定义；`common/units/infantry.txt` 副本丢了 `ranger_battalion` 子单位（牵连 ~31 处 `unknown token: ranger_battalion`）；`common/decisions/PRC.txt` 丢了 13 个 PRC 分类。静默丢定义会牵连成百条 `Unknown category` / `unknown token` 报错，并让整组决议/师名/子学说失效。
   - **系统扫描法**（一次跑完，别逐个撞）：
     ```python
     # 对每个「MOD 与同路径原版文件都存在」的文件，解析顶层 id（depth 0 的 `name = {`）做差集
     dirs = ["common/decisions/categories","common/units","common/doctrines","common/abilities",
             "common/ideas","common/on_actions","common/scripted_effects","common/scripted_triggers",
             "common/national_focus","common/technologies","common/ai_equipment","common/ai_templates",
             "common/decisions","common/bop","common/characters"]
     # 差集非空 → 残缺副本嫌疑
     ```
     实测本 MOD 命中 8 处：6 处真丢失 + `common/national_focus/generic.txt` 丢失 `focus_tree`（**这是故意占位，不能动**）。
   - 识别补充：把 MOD 与**原版同名文件**的「顶层块键集合」做差集（`scripts/fixer_template.py` 的 `top_blocks` / `backfill_missing_blocks`）。凡差集非空就要警惕。
   - 修复：把原版缺失的顶层块**原样回填**到 MOD 文件末尾（HOI4 按文件覆盖但块内是累加的，回填即可得到并集）。⚠️ 但仍要先走上面的「修复分级 A/B」判断——**回填 = 让原本失效的内容生效，属玩法变更，需作者确认**。
4. **【最容易漏】同一文件内顶层块 ID 重复 → 只有最后一个生效**（2026-09-24 实证）。
   语法完全合法、`error.log` 也**不报任何错**，只是策略/内容**静默失效**。高发于 `ai_strategy`、
   `ai_strategy_plans`、`decisions`、`characters` 这类「一个文件里几十个同名结构块」的目录，
   典型成因是**复制粘贴上一块后忘改块名**。
   - 真实案例（`common/ai_strategy/`）：
     - `MOT_ai_strategies.txt` 里 3 个块都叫 `DRA_VS_LAW`（内容分别打 LAW / RAG / MOT）→ 只剩打 MOT 的生效；
       且 `DRA_Prepare_War_with_RAG` 的条件写 RAG、**内容却写 LAW**（同一次复制事故）。
     - 同文件 3 个块都叫 `MOT_Civil_War_Construction_Ratio`（非雪山建军工 / 雪山 1938 前建民工 / 1938 后建军工）
       → 只剩最后一个，非雪山国家内战期完全不建厂。
     - `PRI_ai_strategies.txt` 2 个块都叫 `PRI_unit_production_02` → 1942 年后的兵种比例失效。
   - **扫描法**（必须用「行首无缩进」判定顶层块）：
     ```python
     TOP = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{')   # ^ 行首，无任何前导空白 = 顶层
     # 对目录下每个 .txt 收集 TOP 命中 → collections.defaultdict(list) → len(v)>1 即重复
     ```
     ⚠️ **不要用「花括号深度归零」来判定顶层块** —— 注释行里的 `{` `}` 会干扰计数，实测会得到「0 个块」的假结果（踩过）。
   - 修复：给重复块**改名**（按各自的真实意图，如 `DRA_VS_RAG` / `DRA_VS_MOT`），并顺手核对各块的
     `enable` / `allowed` 条件是否也跟着上一块复制错了（**通常一起错**）。
     ⚠️ 这是「让原本失效的策略复活」，**属玩法变更 → 先问作者**。
   - 配套体检：`hoi4lint\ai_strategy_scan.py`（块 ID 查重 + type 合法性对照原版）、
     `hoi4lint\plan_refs.py`（`ai_strategy_plans` 引用的 focus / idea / game_rule 是否存在）。

### ⚠️ 排查这类文件的三个「别误判」
- **`has_army_manpower = { type = armor ... }` 里的 `type` 不是 `ai_strategy` 的 type**，是 trigger 参数。
  统计 type 合法性时**只取 `ai_strategy = { ... }` 块内的**，否则会误报。
- **`id = TAG` 与 `tag = TAG` 在 `front_unit_request` / `front_control` 里都对**：原版 `CHI.txt`
  两种写法都有（`id=KHM` 简版、`tag=JAP + ratio + priority + ordertype + execution_type` 完整版）。
- **`ai_strategy_plans` 的 `ideas = { X }` 也可以填「顾问的 `idea_token`」**，不限于 `common/ideas/`；
  `common/characters/*.txt` 里的 `idea_token = X` 同样算数，别误报「idea 缺失」。

## 三个反直觉点（别白改）

- **大写脚本关键字是合法的**：`IF` / `ELSE` / `ELSE_IF` / `AND` / `OR` / `NOT` 大小写都能被解析。日志里出现 `Unexpected token: IF` **不是**因为大写，而是**外层缺包裹**（见上表）。不要为了「修」它去批量改大小写——那是纯噪声。
- **子串假阳性**：校验残留时，`manpowe` 会命中修好的 `manpower`，`arget_state` 会命中 `target_state`。检查「是否已清零」要用能区分边界的正则，或人工确认命中行。
- **判定一个键是否合法，只有引擎说了算**，别把「原版文件里出现过几次」当唯一标准：
  - 原版出现 0 次、但引擎**不报错** → 该键是引擎已知的，只是原版没在这类块里用。**保留**。（实例：`common/units/Ilyich_Hero.txt` 的海军单位里 `naval_speed` / `torpedo_attack` / `naval_range` / `surface_detection` 等，原版 unit 文件里一次都没出现，但引擎接受。）
  - 引擎报 `Unexpected token: <键>` → 该键**根本不存在**（旧版遗留或被移除）。**注释掉或删**。（实例：同文件的 `fire_range` / `shore_bombardment` / `evasion` / `port_capacity_usage`，自带手册把前三个标为 OBSOLETE。）
  - 正确流程：**先用 `error.log` 缩小到具体行 → 再查手册/原版确认「正确的替代写法」**；不要拿「原版没出现」当作删除依据。

## `localisation/`（.yml）的坑

- **必须有 UTF-8 BOM**。HOI4 读本地化要求文件带 BOM，丢了会出现「界面显示裸键名」。改 yml **务必原样保留 BOM**（读用 `utf-8-sig`，写回时手动补 `'\ufeff'`）。
- **行尾别改坏**。这类文件常是 CRLF。`t.split('\n')` 之后每行**仍带结尾 `\r`**，此时若用 `'\r\n'.join(lines)` 会产出 **`\r\r\n`**，把整个文件弄坏（我犯过）。正确做法是先剥掉行尾 `\r`，再统一 join：
  ```python
  nl = '\r\n' if '\r\n' in t else '\n'
  lines = [l[:-1] if l.endswith('\r') else l for l in t.split('\n')]
  # …修改 lines…
  io.open(fp, 'w', encoding='utf-8', newline='').write(('\ufeff' if bom else '') + nl.join(lines))
  ```
- **更稳的做法（推荐，逐字节精确）**：读写**都用 `newline=''`**，让每个元素自己带着行尾 `\r`，`'\n'.join()` 原样还原——连 **CRLF/LF 混排**的文件都不会被动到，也不用手工剥 `\r`：
  ```python
  with open(p, 'r', encoding='utf-8-sig', newline='') as fh:   # BOM 自动剥离
      lines = fh.read().split('\n')          # 每行可能以 '\r' 结尾，别 strip
  # …只做「整行删除 / 整行插入」或按行正则替换…
  with open(p, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='') as fh:
      fh.write('\n'.join(lines))
  ```
  代价：只能做**整行**级的改动（正则匹配时先 `line.rstrip('\r')` 再 match）。只改行内容而不动行尾时用它，比上面那版更不容易出错。
- **「同一 focus 里同一个键出现两次」**：HOI4 对重复键**后写覆盖前写**（不报错，但语义变了）。常见成因是自动修复脚本「漏了替换、改成追加」。核对法：按块解析后统计块内**直接所属**的该键条数（遍历行时维护块栈，遇键行取 `stack[-1]` 作归属，避免把嵌套子块的键算进来）。去重时**保留第一条**（通常位于 `id =` 之后的标准位），其余整行删除；删完复查 `depth` 不变、无 `\r\r\n`、CRLF 计数减少量 == 删除行数。
- **写完必须做字节级校验**（这一步救过我）：
  ```
  b.startswith(b'\xef\xbb\xbf')          # BOM 还在
  b.count(b'\r\r\n') == 0                # 没有双 CR
  b.count(b'\n') - b.count(b'\r\n') == 0 # 没有孤立 LF
  b.decode('utf-8')                      # 编码合法
  语言头（l_xxx:）只出现 1 次，键不重复
  ```
- **哪个语言生效**：读 `<用户目录>/Paradox Interactive/Hearts of Iron IV/settings.txt` 的 `language="l_simp_chinese"`。缺本地化只针对**当前语言**报错，但一次补齐各语言更稳。
- 引擎为**每个单位**自动生成一组修正符键，自建单位容易漏：`modifier_experience_gain_<unit>_{training,mission,combat}_factor`（报错 `subunitdefinition.cpp: No localisation for …`）。照原版 `localisation/english/modifiers_l_english.yml` 的体例补。

## 文件编码 / 乱码（先判可逆性，再决定清理还是还原）

用户看到 `���������ȶ���ÿ��` 这类东西时的处理流程（2026-09-21 实证）。

**第 1 步：先把「假乱码」排除掉。** 编辑器/控制台代码页不匹配会把正常 UTF-8 中文显示成乱码——**所见不能为准，只认字节**：

```python
b = open(p,'rb').read()
n_fffd = b.count(b'\xef\xbf\xbd')      # 文件里真的存了 U+FFFD
b.count(b'\xef\xbb\xbf')               # U+FEFF（BOM）
```

想看真实内容时**一定用 `unicode_escape` 输出**，别直接 print：`s.encode('unicode_escape').decode('ascii')`。

**第 2 步：判可逆性。** 成因几乎都是「GBK 中文 → 按 UTF-8 解码 + `errors='replace'` → 又存成 UTF-8」：

- 这类**不可逆**（U+FFFD 无条件丢字节）。验证：把当前文本 `text.encode('gbk')` 会因 `U+FFFD` 而失败 → 说明信息没了。
- 乱码的**指纹**（用来确证成因，也可用来识别边界）：
  | 产物平面 | 来源 | 例子 |
  |---|---|---|
  | U+0080–U+07FF | GBK 字节对恰是合法 2 字节 UTF-8 | `ʼ ı ҵ 壩 ÿ ½` |
  | U+0800–U+FFFF | 恰是合法 3 字节 | 随机汉字 `趋 娃 壩`、谚文 `뭌` |
  | 平面 14/15/16 | 恰是合法 4 字节 | `\U000e3ebb` |

**第 3 步：找完好副本（最重要，别急着删）。** 依次查：`backup_*` 备份链里**最早**那几份、同级其它版本目录（Gamma…）、作者自己的 `.backups\`、`Documents/.../mod/` 实际部署副本。**实例教训**：`LYY_Ganyu_Events.txt` 等 4 个文件在最早的 `backup_MOD` 里就已经是坏的 → 不是本地误操作，原文彻底丢失 → 才只能清理。

**第 4 步：清理算法（逐行，只动含乱码的行）**

```python
# 乱码字符集必须覆盖（⚠️ U+FFFD 落在「3 字节区」里，最容易被漏掉！）
is_moji = (o == 0xFFFD) or (0x80 <= o <= 0x7FF and ch != '\u00a7') \
          or (0xAC00 <= o <= 0xD7A4) or (0xE000 <= o <= 0xF900) \
          or (0xE0000 <= o <= 0x110000)
```

1. **`§`（U+00A7）必须白名单**——它是合法颜色码，删了就毁本地化。
2. 取 `#` 的位置：`#` 在**第一个乱码字符之前** → 注释行可清理；否则是**代码行，绝不能当注释删**。实测本 MOD 有 4 处 **state flag 名里混进了乱码**（`LYY_<乱码>_improved`），正确做法是**成对改名**（`NOT = { has_state_flag = X }` 与 `set_state_flag = X` 同步），不是删。
3. **乱码区间 = 第一个乱码字符 ~ 最后一个乱码字符，整段删除**。区间内夹着的 ASCII 也是中文 GBK 字节的残渣（`+5%`、`id`、`)`），**一起删**；但区间**外**的前后缀是作者手写的 ASCII（`# --- 1. ` 与 ` ---`、`# buff`、`# TAG`），要留。
4. 注释体若已无 `[\u4e00-\u9fff]{2,}` 连排汉字（或 `\u3000-\u303f`、`\uff00-\uffef`），则其中残留的**非 ASCII 全判为边界残渣**再清一遍。
5. 收尾判定：只剩空 `#` → **删整行**；行尾注释空了（`add_ideas = x   #`）→ 去掉 `#`；注释体只剩数字/标点（`# 4`、`# ()`）→ 同上；否则保留。
6. **别用「只在行首/行尾删」的简化版**——乱码在中间（`# --- 3. <乱码> ---`）时模板文字会保不住。

**第 5 步：校验 —— 汉字守恒审计（强烈建议）**

靠 CRLF/行数对不上是不够的，必须做一次逐行对齐的汉字差集：

```python
sm = difflib.SequenceMatcher(None, 改前行表, 改后行表, autojunk=False)
# 对 replace 的两两配对取 set(旧汉字) - set(新汉字)，逐条人眼确认
# 判据：所有「丢失的汉字」都必须来自被删的乱码行（那些汉字是随机产物：趋/獦/絜/壬…）
```

⚠️ difflib 的 `delete` 计数**会把相邻的 replace 并进去而偏小**，所以「删行数」要取 `len(前)-len(后)`，别用 opcode 统计（否则会报假的 CRLF 校验失败）。

**顺带会遇到的同类脏字符**

- `.gui` 里 `text = "\x11Y国家状态"` → `\x11` 是被写坏的 `§`（原版 `interface/core.gfx:796` 官方注释：`# Global text colors used in the entire game, for use in loc files ex: "§G Text Text§!"`）。后面跟的字母正是颜色（Y 黄 / G 绿 / R 红）→ 还原成 `§Y` / `§G`。
- 本地化里混入 `U+0081`（C1 控制符）、`U+200B`（零宽空格，多半是从网页粘的）→ 直接删字符即可。
- `gfx/_convert_log.txt` 这类的**工具输出日志**可能是 GBK 编码：游戏不读它，别去改（改了下次工具运行又写回 GBK）。

## 环境坑（Windows）

部分环境下 bash 的 coreutils 不可用（`ls`/`cd`/`head`/`dirname` 报 `command not found`），带 `| head` 的管道会直接让命令失败。此时改用 Python 全绝对路径完成读写与检索，输出先写文件再 `Read`：

```bash
"<managed python>" -c "import io; print(io.open(r'C:\path\file.txt','r',encoding='utf-8',errors='replace').read()[:3000])"
```

**⚠️ 绝对不要把长跑修复脚本的输出管道给这些缺失的外部命令**（`python fix.py --apply | tail -30`）。管道对端不存在 → 破裂 → Python 抛 `BrokenPipeError`，**写入循环会在中途中断**，产生「前 N 个文件已改、其余没改，且备份只覆盖前 N 个」的半成品状态，而 exit code 还是 127（看起来像命令写错，不像改坏文件）。**一律重定向到文件再读**：

```bash
python fix.py --apply > apply.txt 2>&1   # ✅ 之后用 Read 读 apply.txt
```

抢救与幂等：修复脚本的 `expect` 是「行号 + 该行原文」双断言，所以**对已改过的文件重跑会大量报 MISS（这是好事，说明断言在保护你）**。正确做法是先从 `backup_MOD_batchN` 还原全部目标文件，再干净地跑一次 `--apply`——不要试图让脚本「继续跑完剩下的」。

## 修复后校验（拿新 `error.log` 回验，别只靠静态分析）

用户跑完一轮游戏后，按这个顺序做，能避免 90% 的误判：

1. **先确认目标 MOD 真的加载了**（最容易翻车的一步）
   - 读 `<用户目录>/Paradox Interactive/Hearts of Iron IV/dlc_load.json` → `enabled_mods` 是不是包含目标 MOD；
   - 读 `logs/game.log` → `Loaded <N> provinces` 是不是**该 MOD 地图**的省份数（本 MOD 提瓦特 = **11507**；原版地球 = 13414）；
   - `logs/game.log` 有 `[[ Launching SINGLEPLAYER-game ]]` 才算真进了游戏；
   - `crashes/` 有没有**新目录**（对比时间戳，别把历史崩溃当成这次的）。
2. **日志要按 (文件, 行号) 去重再统计**。`error.log` 每帧重复，行数会虚高几十倍（实例：17 MB / 12.3 万行 → 实际只有 532 条唯一报错）。打印时带上 `x<次数>`，次数大 ≠ 问题多。
3. **抽取真实文件与行号**——PDX 报错有 4 种形态，写解析器必须全覆盖：
   ```
   A  path:LINE: msg
   B  Error: "<err>, near line: N" in file: "PATH" near line: M      ← 最常见
   C  <err> in PATH line : N
   D  Error: "<err>, near line: N" in file: "PATH"                    ← 无第二个行号
   ```
   只用形态 A 会**漏掉绝大多数** offender（本 MOD 曾因此误判成"全部修好了"）。
4. **只保留属于目标 MOD 的报错**：`os.walk(MOD)` 建「相对路径小写 → 全路径」索引，报错路径 `.lower()` 查表命中才算。（一次实测：825 处里只有 499 处属目标 MOD。）
5. **新旧对比要按「同一 MOD 过滤 + 同一解析器」**，并把基准里每条 `(file,line,msg)` 到新日志里找同文件同类消息（行号会因编辑位移）。分四类落表：**已消失 / 仍存在 / 同类但行号变 / 新增**。
6. **定向验证本轮改过的 token**：逐条正则在新日志里搜，期望 0 命中。注意子串假阳性（`manpowe` 会命中 `manpower`）与同名异因（`corps_commander` 可能命中原版 `create_corps_commander: Portrait not found`）。
7. **判「未定义」前，跨全部已加载 MOD 搜一遍**。各 MOD 工作区互为兄弟目录，`.mod` 里的 `path=` 才是权威位置。本 MOD 例：`conditional_surrender` 由 `Ilyich Genshin Peace Negotiation` 提供——只加载 Beta 时会假报未定义。
8. **回滚锚点**：每批改动写进独立 `backup_MOD_batchN\`，校验用 (BOM, CRLF 数, LF 数) 三元组与备份比对（脚本类 `.txt` 本来多半无 BOM，别把"无 BOM"当损坏）。

## 参考文件

- `references/version-gotchas.md` —— 版本升级导致的语法变更、各版本破坏性改动速查。
- `scripts/errorlog_report.py` —— 自动选取最完整的 `error.log`，消息模板计数 + 输出「MOD 内文件 + 真实行号」工作清单（只读）。
- `scripts/fixer_template.py` —— 修复器模板：`edit_line`（行号+原文双断言）/ `scrub_file`（整文件正则，自动 `re.M`）/ `insert_lines` / `delete_lines` / `top_blocks` + `backfill_missing_blocks`（回填原版缺失块）；支持 dry-run 与 `--apply`。
- `scripts/mod_backup_verify.py` —— `backup` 子命令做脚本文件快照；`verify` 子命令做**忽略注释/字符串**的括号平衡校验与残留模式检查。
