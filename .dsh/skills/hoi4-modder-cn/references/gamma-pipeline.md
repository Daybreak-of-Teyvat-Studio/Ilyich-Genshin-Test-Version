# Gamma 州重排 / 海州 / 州名 / 胜利点 / 地形改造 实战经验

**读这份的场景**：批量挪省或均分州；创建海洋州；给州写中文名；管理胜利点（VP）；按地理特征重设全图地形；以及这些操作出错后的排查。

## 工具链（项目 `tools/` 目录）

| 工具 | 用途 |
|---|---|
| `gamma_state_edits.py` | 转省 + 改归属（支持逗号/全角逗号/句点/空格混写；转省自动同步 buildings.txt） |
| `rebalance_states.py` | 多州省均分（紧凑度优化，16 次随机重试取最优） |
| `terrain_pipeline.py` | 地形三步改造（全平原→国家覆盖→地理特征） |
| `buildings_final_fix.py` | buildings.txt 合并修复（一次遍历修陆+海） |
| `fix_gen_points.py` | 州级生成点从零重排 |
| `state_names_job.py` | 州名本地化改造（唯一 key + 占位） |
| `vp_reset.py` / `vp_add2.py` / `vp_371.py` | VP 清零 / 批量加 VP + 本地化 + 首都 |
| `fix_vp_pairs.py` | VP 多对块拆分修复（一 block 一对，字节级保缩进/CRLF） |
| `fix_vp_loc_bom.py` | 本地化 yml 全量补 BOM（幂等） |
| `audit_natlan_batch.py` | 指令批次逐条审计模板（当前值 vs 批次前备份，输出 ✓/✗ 清单） |
| `sea_split.py` / `sea_state_fix.py` | 海洋州创建 / 海州修复 |
| `check_buildings.py` | 守门检查（对照原始文件验不变量） |

## 转省指令解析的坑

- **逗号有双重语义**：`395,524,1252,3504+464` = 四省同给 464（并列省，等同空格）；但 `1395+466.395` 的句点是指令分隔。解析规则：**句点/分号 = 指令分隔；逗号/全角逗号 = 并列省（等同空格）**。
- **全角逗号 `，`**（U+FF0C）必须显式 `.replace('\uff0c', ' ')`——用户会混用全半角。
- **改归属左侧只能是单个 state_id**，不支持 `742,731+SDH` 并列写法——需拆为两条。
- **「数字+名字」按有无括号分流（用户钦定规矩，杜绝省/州语义猜测）**：
  · `2149烟谜主（25，首都）` = **VP**——括号里必有胜利点数值，可带「首都」标记（同国多首都按指令顺序取最后）
  · `643圣火竞技场`（无括号）= **state 命名**——只有 id 和名字
  · 实证：无括号条目被当省号解析后，12 条州名全挂到「省号所在州」、VP 错位一格（见「纳塔批次」条目）

## 多州省均分

算法：合并参与州的省并集 → 找连通块 → 每块按省数比例分配州数 → 最远点种子 + BFS 均衡生长 → **16 次随机化重试取紧凑度最优**。

- **紧凑度** = 组内省质心最大距离 / 等面积圆直径（圆=1.0，越长条越大）。总评 = 按省数加权平均 + 最差组惩罚 + 省数失衡惩罚。
- 实测：30~43 省的岛屿群，最优总评 1.3~1.6（约 30 省的岛状地形上这是偏紧凑水平；1.0 只在大块方形区域可能）。
- 用户要求"别长条"时，用 16 次重试选优比手调边界省有效得多。
- **连通块约束**：如果省并集分成多个连通块，每块至少 1 个州；不够时从最大块拆补。

## 创建海洋州（无 owner 纯海域州）

- 文件格式：无 `owner` / 无 `add_core_of` / 无 VP / 无建筑 / `state_category = ocean` / `manpower = 0`
- **HOI4 合法**——纯海域州不需要 owner，游戏不崩。
- 从模板州复制时要**清干净**：`owner` 行、`add_core_of` 行、`victory_points` 行、省级建筑块 `N = {...}` 全部删除；`state_category` 改 `ocean`。
- **新州 id 从现有最大值+1 开始**（如现有 1-861 → 海州 862 起）。
- 落地后跑 `rebuild_buildings.py` 全表同步（海上 naval_base_spawn 等条目的声明州会自动修正）。

## 州名本地化改造

- state 文件的 `name` 行是本地化 key。当全 mod 州共用同名 key（如 `DOTTown`）时无法逐州命名——**必须先唯一化**：把每州 `name` 改为 `STATE_<id>`。
- 本地化文件 `localisation/simp_chinese/DOT_state_names_gamma_l_simp_chinese.yml`（新建，BOM+CRLF）：`STATE_<id>:0 "中文名"`。
- 用户说"改为 `*`"= 全部州名设占位符 `*`，然后逐州给中文名覆盖。
- 省号→所属州：用 `p2s` 映射（用户给省号+名字，你查它属于哪个州）。

## 胜利点（VP）管理

- state 文件格式：`victory_points = { <省id> <值> }`——**恰好 2 个参数**。原版 1000+ 个 VP 块**无一例外**都是一对；多 VP 用**多个块**表达，绝不写 `{ a b c d }`（实证：19 个州这样写全部报 `set victory points takes 2 parameters` 且整块 VP 被丢弃，error.log 可查）。修复脚本 `tools/fix_vp_pairs.py`（字节级拆块，保持缩进/CRLF）。
- 本地化 key：`VICTORY_POINTS_<省id>:0 "中文名"`。
- **VP 值必须是数字**——把中文名当值写入会产生 `{ 1808 至高神座 }` 这样的垃圾（实际踩过的坑：构造时传了 `(pid, cn)` 而非 `(pid, val)`）。
- **set_capital**：`history/countries/<TAG> - *.txt` 的 `capital = <州id>`（州级不是省级）。同国多 VP 时只取最后一次——先查冲突。
- **全清零再逐个加**是安全的：694 个州的 VP 全删 → 逐州写入新 VP → 复验总数。

## 本地化文件的 BOM 陷阱（再次踩坑）

**`.decode('utf-8-sig')` 会剥 BOM，`.encode('utf-8')` 不补 BOM** → 追加内容后写回 = 静默丢 BOM → 整个文件被游戏忽略 → 用户看到"没写本地化"。

正确写法：
```python
raw = open(p, 'rb').read()
t = raw.decode('utf-8-sig')          # 去掉 BOM 读入
# ... 修改 t ...
open(p, 'wb').write(b'\xef\xbb\xbf' + t.encode('utf-8'))   # 写回时补回 BOM
```

或者用 `open(p, 'w', encoding='utf-8-sig', newline='')` 写（Python 会自动加 BOM）。

**每次写完本地化必须验**：`BOM=True`、CRLF 计数、关键 key 在文件里。

## 地形三步覆盖改造

按用户指令顺序执行、后面覆盖前面：

1. 全部陆地省 → plains（水域省保持 ocean/lakes）
2. 国家覆盖：DRA/CYG→mountain，MHL→hills，SGD/SDH/SGS→desert（无条件覆盖该国每省）
3. **所有陆地省（六国不豁免）**按地理特征：城市(spawn_city)→urban > 原版山脉→mountain > 沿海→plains > 原版森林→forest > 邻山且海拔≥105→hills > 其余（三沙辖区→desert、其它→plains）

**关键数据源**：
- **terrain.bmp 调色板 index → 地形**：映射表在原版 `common/terrain/00_terrain.txt` 末尾的 `terrain = { ... }` 块。**index 13 = urban（spawn_city = yes）** = "地图上显示出的城市"判定依据。
- **heightmap 省均海拔**：用 `heightmap.bmp`（存储序行 = z，不翻转）按省取均值。
- 当 definition.csv 已被抹平（全 plains）时，**原版地形从 terrain.bmp 反推**，不从 definition.csv。

**写 definition.csv 和 terrain.bmp 都要改**——只改 definition（机制）不改 terrain.bmp（视觉）会导致地图颜色不匹配。

## 增量修复螺旋（反复踩过的教训）

在状态已经很乱的 buildings.txt 上做增量修复，脚本 A 修好的被脚本 B 改坏、脚本 B 修好的又被脚本 C 覆盖——**循环往复，每轮只修 536 条又冒出新的 536 条**。

**根因**：多个修复脚本各自有不同的"跳过条件"和"容差口径"（3×3 vs 5×5、只陆 vs 陆+海），互相不兼容，跑一遍 A 的成果被 B 的不同口径覆盖。

**正确做法**：当数据严重混乱时，**放弃增量修复，写一个"从零重排"脚本**——清除该类型的全部条目，从权威源（原始文件 / state 文件）按最终规则一次性重新放置。这样只有一条规则路径，不会互相打架。

**识别信号**：同一问题连续修 2 轮以上还有残留 → 停止增量，改从零重排。

## 州文件合并写入的三步覆盖顺序

转省 → 改归属 → 州名/VP/地形，每步覆盖前一步。用户可能中途调整策略，**不要假设之前的规则还成立**——每批指令都按最新指令理解。

## 州合并的必迁清单（用户钦定，2026-10-07）

合并不只是搬省删州，被并州的数字 id 关联资产必须转给存留州：
1. **本地化**：`DOT_STATE_<被并州>` 名字转给存留州或删除；VP key 随省走
2. **修正**：`state = <被并州号>` 族（owns_state / controls_state / has_full_control_of / transfer_state / states 列表）→ 改指存留州
3. **奇观**：奇观决议的州作用域块（`<被并州号> = { add_dynamic_modifier = … }` 等）→ 改指存留州，否则奇观失效
fill_state_gaps v4 的引用联动只覆盖"补号搬州"；合并的"被并州号→存留州号"映射用户指定，
执行前先把映射表喂给引用迁移逻辑再删州。暂缓合并组记录在项目 `docs/待办合并清单.md`。

**合并后必须接「简单迁移补号」**（空位 ← 号尾州；见下节「州号空洞与补号」）——合并删文件与补号是连续两步，别忘第二步。
本批实证（2026-10-14）：62 合并 63/65/66/67 → 被并号引用迁移 37 处（DVA 决议 ×8、DOT_Resources ×16、国策树 ×13）
→ 删 4 个州文件 → 尾部 703/704/705/706 补进 63/65/66/67（含 5 点联动）。

## 验收清单（每类操作各有其关）

做完任何一批改动，**逐项运行以下检查并念出数字**——"看起来对"不算过：

**A. 挪省 / 改归属后**
- 省总数守恒（如 4698）、重复归属 0
- 每个定义在 `definition.csv` 的陆地省都被某个州覆盖（0 未覆盖）
- `map/buildings.txt` 同步执行（脚本自动）

**B. buildings.txt 守门（`check_buildings.py`，对照原始文件）**
- 8 种州级类型每州数量与原始**完全一致**（0 不符）
- 无州缺任何生成点
- 每类建筑总量不变（arms_factory / industrial_complex / bunker / naval 四件套 / coastal_bunker / floating_harbor / dockyard …）
- 纯 CRLF、无 BOM、行数、字段数 0 异常
- 声明州与坐标不符 0 条

**C. 州文件语法关**
- 括号配对、无行首空格（必须 tab 缩进）
- `owner` 有且仅一行，`add_core_of` 必须等于 owner（海州两者皆无）
- `provinces` 非空
- `victory_points` 的省 ⊆ `provinces`，且参数个数为偶数（正常恰 2 个）
- 全 mod 无重复省归属

**D. 海州专项**
- `id` 行数字正确（**模板替换最容易只改 name 忘了改 id** → id 冲突必崩）
- 无 owner / add_core_of / VP / 建筑块，`state_category = ocean`
- 海省与海域省集合对得上（definition 里非 land 的省全部有着落）

**E. 本地化（每次写完都要念）**
- `BOM=True`、CRLF 计数
- 关键 key 确实在文件里（`grep` 计数）
- 中文名与用户给的逐字一致

**F. 地形**
- `definition.csv` 与 `terrain.bmp` **两份都改了**且一致
- 水域省未被动过
- 各类型分布与规则推导一致（不符合特征的省落在 plains 还是 desert 取决于 owner）


## 州名 key 禁用原版保留前缀（甲信越事故）

state 的 `name` key 写成 `STATE_<id>` 会**撞原版** `state_names_l_simp_chinese.yml` 的同名 key
（原版就有 STATE_3、STATE_534……全是真实州名）。一旦我们的本地化文件缺 BOM 或加载失败，
游戏回落原版名——地图出现「甲信越」「陕北」「伊丽莎白维尔」。

规矩：
- 州名 key 一律用 `DOT_STATE_<id>` 独有前缀
- 每次**新建/追加**本地化后必验 BOM（追加脚本极易剥掉 BOM——已发生 3 次）

## 新州文件必须 CRLF

新州文件用 `\n` 写盘 → `gamma_state_edits.py` 等按 `\r\n` 解析的工具**读不到 provinces 块**。
已做两层修复：全量转 CRLF + 工具正则改 `\r?\n` 容错。
规矩：写任何 Paradox 文件一律 `open(..., newline='')` + `\r\n`。

**字节级替换的两个 \r 陷阱**（fix_vp_pairs v1 踩坑）：
1. decode 后做局部替换、再 `t.replace('\n', nl)` 统一换行——已存在的 `\r\n` 会变 `\r\r\n`，全文件每行后多一空行。
2. 正则用 `[ \t]*$` 收尾——行尾 `\r` 不属于 `[ \t]`，匹配静默失败；改用 `\r?$` 则 `\r` 被消费进匹配，替换后丢 `\r` 留孤 `\n`。
正确做法：收尾用零宽断言 `(?=\r?$)`，替换串自带原缩进（`^([ \t]*)` 捕获），写盘按原 BOM/CRLF 字节级重组。

## 空州（provinces 块为空）= 必闪退

转省把某州省份全部搬走后**必须删除该州文件**并跑补号，只搬不删 →
`state.cpp: no provinces in state` → 「Executing History」阶段**闪退**（实证：719 州 4 省被拆到 730/709/748，文件忘删，游戏稳定复现崩溃）。
规矩：每次转省批次落盘后立刻扫一遍 `provinces = { }` 空块（`fill_state_gaps.py --dry` 的空白州扫描可复用），有则当场删号补号。

## 静默未写盘（写盘成功 ≠ 内容变了）

`terrain_pipeline.py` 曾漏掉「new_terr → lines」回写循环：脚本正常跑完、打印「已写入」，
但写进去的内容与原来一模一样——`definition.csv` 停在旧规则，与 terrain.bmp 差 743 省，
**连续三轮没发现**（每轮只看「写入成功」没 diff 内容）。
规矩：写盘后必须**读回验证**（改动行数 / 分布是否等于预期），不能只看有没有异常。

## buildings.txt 海军标记吸附规则（崩溃级）

海军类标记（naval_base_spawn / naval_headquarters / naval_supply_hub / coastal_bunker /
floating_harbor）画在**水面上**（离岸 1~8 像素）。游戏解析 = **吸附最近陆地省**，
不是「标记像素所在的省」。按像素省归州 → 1799 条 BUILDING IGNORED → 沿海省失去港口
→ 选国界面必崩（coastal but has no port）。

配套教训：
- 海州 `state_category` 只有原版 13 个合法值（**没有 ocean**）→ 用 `wasteland`
- 验证脚本与业务脚本用**同一个错误假设**时，验出 0 问题也是假的——必须用独立依据（error.log）

## 省号 / 州号必须双读核对（1466 笔误事故）

用户给的数字可能是州号也可能是省号，**两种解释都查**（存在性 + owner 语义）再用。
只用一种解释就动手：15 个蒙德地名曾全挂到至冬/枫丹的州上（用户给的其实是州号）。
语义印证法：`清泉镇→SPI`、`晨曦酒庄→RAG`、雪山地名→DRA。对不上就问，别猜（1466 是 466 笔误）。

## 州号列表被当省号解析（纳塔批次 32 条只对 15 条）

「数字+名字」**无 p 前缀 = 州号直给**（老规矩），绝不能做「省号→所在州」解析。
实证：一批 12 条州名全部写成省号所在州（`643圣火竞技场`→写到 s613，因 p643∈s613），
其中 3 个错号还**覆盖了已有真名**（s110 稻妻城、s595 无郁稠林北、s645【三运河之地】——
修复时必须查批次前备份恢复原值，不能一律改回 `*`）；5 条 VP 名错位一格
（`2149烟谜主(25,首都)` 的名与值写到了下一项的 389 上），州名还被二次写成 VP 值。
超上限的号（如 1379 > 州数上限）可能是省号语义（p1379 所在州），单独确认。
规矩：批次落盘后**逐条对照指令跑审计**（audit 脚本读当前值 + 批次前备份，
区分「从未落实」与「后来丢失」），报告 ✓/✗ 清单后再动。

## 字节级工具自身的两个坑（修复工具反被咬）

1. **re.sub 替换串重组捕获组**：group(1) 已含的字符（如 `DOT_STATE_643:` 的冒号）
   不能再拼一遍——`f'{m.group(1)}:0'` 会写成 `DOT_STATE_643::0`，key 静默失效。
   写完必须**回读验证**（key 能被再解析、数量对得上）。
2. **同一路径先 'wb' 后读 = 文件清零**：`open(p,'wb').write(open(p,'rb').read()...)`
   中 open('wb') 先截断、参数里的读拿到空内容，文件直接变 0 字节（一天内 3 个州文件中招）。
   铁律：读改写**分两步**——先 `raw = open(p,'rb').read()` 完整读入变量，再打开写。

## 飞地目标必须由用户指定（越权教训）

「飞地并入紧邻州」看似合理，但目标是用户的设计决定——自动处理 5 处后被要求回滚。
回滚流程已验证：`.backups` 上一批州文件直接复制回 + buildings 反向同步。
规矩：涉及**归属**的语义决定，列清单等用户拍板。

## 启动竞态：部署未完成就启动游戏（"原版地图混入"崩溃）

**症状**（一眼可诊）：game.log 显示 `Loaded 13414 provinces`（原版省数，mod 应为 8022）+ error.log
出现成批 `province has no strategic region`（13000+/13414）、`land province has no state`（7600+）、
`Missing State ID`（几十个）、崩溃转储 `IsMapInGoodState: no`。

**根因**：游戏启动时 mod 目录的文件复制（部署）还没完——引擎在启动瞬间建立文件索引，
此时 `map/definition.csv`、`provinces.bmp` 尚未写入 → 引擎回退用**原版**地图数据 → 全面错位 → 崩溃。
实证（2026-10-08）：部署复制 09:34:19-09:36:06，游戏 09:35:46 启动；副本里 definition.csv 的
**创建时间 09:36:05** 晚于启动时间，实锤。

**诊断三步**：① 对照表：`Loaded N provinces` 是否等于 mod 省数（用 definition.csv 最大 id 核对）；
② 查副本文件创建时间（`os.path.getctime`）是否晚于游戏启动；③ 与正常会话日志对照（正常会话零此类错误）。

**修复**：等复制完成再启动；或按项目 `.GithubDocs/DebugTheRepo.md` 的做法把 `.mod` 的 `path`
直接指向仓库（零复制、零竞态）。

## HOI4 触发器正确名：has_full_control_of_state（不是 has_full_control_of）

`has_full_control_of_state = <州>` 是**单个 token**（原版 1781 处实证）。两种错写都报错：
- `has_full_control_of state = X` → 报 `Invalid trigger 'state'` + `unexpected token ( = )`
- `has_full_control_of = X` → 报 `Unknown trigger-type: has_full_control_of`（不存在的触发器名）
修法：整体替换为 `has_full_control_of_state = X`。教训：**修触发器名先去原版 grep 确认完整 token**，
别照着残缺写法猜补 `=`。

## beta→gamma id 迁移（本地化为桥，分批可迭代）

旧版脚本（国策/决议/奇观/effect/trigger…）里的州省号全是 beta 号，以本地化为桥迁移：
- 州桥：beta 州英文名（state 文件 name=）→ beta 中文 loc → gamma 同名州；fallback 同名 VP→省→其州
- 省桥：beta `VICTORY_POINTS_<号>` 中文名 → gamma 同名 VP → 省号

**⚠ 陈旧移植键陷阱（2026-10-08 高塔孤王事故，v2 方法论）**：
gamma 的本地化表可能混有两层数据——**原始移植层**（保留 beta 编号的旧键）与**用户新建层**（正确 gamma 号）。
直接按名字取号会命中陈旧键（如 beta 1314「高塔孤王的遗址」→ gamma 死键 1314，
而正主是用户建的 442「孤王的高塔」）。判据：
- **活键 = 州文件 `victory_points = { N v }` 实际引用的键**（237/501 实证）——只有活键可信
- 死键 = loc 有、州文件零引用的键（~263 个）——陈旧垃圾，散落在旧文件里
  （`DOT_state_names_l` 132 死、`victory_points_l` 143 死、主文件 `DOT_Victory_Points` 近乎全活）
- **同名 + 同号 = 高度可疑**（213/221 实证）；同名 + 不同号 = 用户已修正（51 个）→ 直接采信
- 地标重命名（遗址→新名）需人工/近似匹配 + 用户确认
- **清理建议**：死键应删除（否则持续污染桥），但删前跑活键判定；删除需用户批准

**扫描模式必须全**（v1 漏过这些导致"有些地方没迁到"）：
token（state/owns_state/controls_state/has_full_control_of_state/transfer_state = N）、
`states = { }` 与 **`provinces = { }` / `path = { }` 列表**、`province = N`/`province_id = N`、
**`controls_province/owns_province = N`**、**`set_province_name = { id = N }`**、
**`location = N`**（history/units）、数字键州作用域块（须过标记检查）；注释天然跳过。

**重跑 apply 的危险**：迁移过的文件里已是 gamma 号，盲跑会把 gamma 号按 beta 语义二次映射。
后续执行必须按 Excel 逐行批准、按文件精确替换（或标记已迁移文件跳过）。

流程：build_beta_gamma_bridge（v2：活键+同号判别+人工映射）→ scan（全模式）→
Excel 对照（用户过目）→ apply --dry → 正式执行（逐文件备份）→ 括号自检。
人工映射文件 `tools/beta_gamma_manual_map.json`：`{"province": {"1314": 442}}`。

## 涂色重划（整片州界重设计流水线）

用户在省图上涂色（每连通色块=一个新州，四色即可，按连通块分组不按色值分组）：
1. 读图：调色板量化（alpha>128 且近色）→ 逐色 BFS 连通块 → 每省取多数色块 → 省分组；
   未涂省（湖泊/遗漏）挂到邻接多数块并单独报告；纯水面笔误块自动忽略
2. id 继承：新州 ← 省重叠最大的旧州号（名字/VP 就地保留最大化）；旧→新全量映射驱动
   本地化（名字跟内容走，每个新 key 取重叠最大旧名，落选报告丢弃）、首都、引用联动
   （整片重绘是一次性大工程、用户点名启动——与「禁全量迁移」不冲突；日常删州/合并一律走简单迁移）
3. manpower/资源按省数比例分摊；category/buildings 等级/核心取重叠最大旧州
4. 落地后：补号（洞=旧州数−新州数）→ buildings 终版重整 → 全项自检
实证：至冬 198 州 → 65 州，1125 省全部读出，补号 140 洞。

## 大规模补号的三个坑（至冬 140 洞事故）

1. **fill 搬移禁止跨相全局排序**：洞号可能大于搬出者自身号（洞落在尾部段内），
   按"目标号升序"执行会让"他州迁入"先于"本州迁出"→ FileExistsError。
   必须按相执行：①全部陆洞 ← 陆尾 → ②被腾陆尾 ← 海尾 → ③海洞（脚本已修）。
2. **补号后本地化重复 key**：纯目标 id（被迁入但自身不搬的洞号）的旧 `*` 占位行
   不会自删，与迁入州的新 key 重复（52 例）→ 5.5 已加"纯目标 id 让位"逻辑。
3. **连锁合并覆盖**：多个州并入同一存留州时，第二次合并若用缓存内容会把第一次
   并入的省覆盖丢失（实证：567、568→550，567 的 5 省全丢成孤儿）→ 逐合并刷新缓存
   或每合并后重扫。

## buildings 块提取必须括号配对（[^}]* 截断事故）

state 文件的 buildings 块可内嵌省级块（`10733 = { bunker = 2 }`）。
`re.search(r'(buildings\s*=\s*\{[^}]*)\}')` 到第一个 `}` 截断 → 重建的新州文件
括号失衡（29/65 个中招）。提取一律用平衡配对扫描。

## 战略区（strategic regions）——新加/改动必读（2026-10-15 静默崩溃事故）

**事故经过**：为 62+64 州新建战略区时，我照 Beta 同名区域的号用了 `id=46`（当时只有 `id=1`）。结果：游戏 debug 加载地图末尾 **静默 ACCESS_VIOLATION**（error.log 零 MAP_ERROR、零州/建筑报错；game.log 永远停在 `defines loaded`，**从不出现 `Loaded N provinces`**）。自启动二分实测：`{区域1, 无46}` → 能进；`{区域1, 有46}` → 崩；**把 `id=46` 改成 `id=2` → 立刻能进**。

### 铁律

1. **战略区号必须连号（1..N 连续无空洞）**——原版 304 区、Beta 70 区全是密的；有空洞（如 {1,46}）→ 引擎按 1..max 遍历区域数组 → 越界 → **静默崩溃**。新加区域**只能取下一个连续号**（现有 1 → 新加 2）。
2. **每个区域必须带全年 weather 块**（12 个 `period`，覆盖 `0.0`→`30.11`；原版 304/304、Beta 全都有）。缺 weather → 引擎报 `strategicregiontemplate.cpp: Region temperature doesn't cover the whole year, ending on 0.0 instead of 30.11`。
3. **`provinces` 列表必须升序**（原版/Beta 全部升序；乱序=可疑）。
4. **新加区域要同步 `map/weatherpositions.txt`**：格式 `<区域id>;<x>;<y>;<z>;big`，**每个区域 2 条**（坐标取该区域内省份 positions.txt 的坐标）。
5. **行尾纪律：只用单 CRLF**，禁 `\r\r\n`（双 CR 会被 **nudge** 判为地图定义错误；见下）。
6. 新区域可带 `naval_terrain=water_shallow_sea` 等（原版 63 区在用；海区建议带）。
7. **拆分后必须检查「被新区域完全包围、却还留在原区」的陆地州**（2026-10-19 实例：蒙德城 state 466 被 Region4/6 包围仍留在 Region1 → error.log 报 `Naval strategic region 暗之外海 is fractioned!`，并列出该州 8 个省）。陆地连通靠海：沿海州能经海连回 Region1，**内陆州一旦四周被划走就成了孤岛**。修法：把该州整州并入相邻的新区域（按州名/地理位置判断，如蒙德城→坠星山谷），不要只挪个别省。

### 指令语法：`RegionN名称`（用户钦定，2026-10-18）

用户直接给：`520+521+533+534+535+547=Region9龙脊雪山` —— 意思是**新建第 9 号战略区**，名称「龙脊雪山」，由列出的州组成。按以下规则落地：

1. **战略区 id = N**，必须接在现有最大 id 之后（现有 1..k → 新加 k+1..N，连号无洞）。
2. **成员按州展开成省列表**：把每个成员州的 `provinces` 全部并进来，**升序**、去重。若某成员州在本批被合并（如 `413+422=422`），用合并后的存留州展开（同批先合并、后建区）。
3. **必须从原区域（通常是 Region1）里删掉这些省**——同一省同时属于两个战略区=未定义行为。
4. 新区域文件放 `map/strategicregions/DOT_Strategicregions_NN.txt`，`id=N`、`name="DOT_STRATEGICREGIONS_NN"`；**12 段全年 weather 照抄同气候的既有区域**（缺段=引擎报 temperature cover 错误）；陆地州组成则**不要** `naval_terrain`。
5. 本地化：`DOT_STRATEGICREGIONS_NN:0 "名称"`（BOM+CRLF），旧占位 key 若同名要一并处理，避免重名。
6. `map/weatherpositions.txt` 每区补 **2 条** `<id>;<x>;<y>;<z>;big`，坐标取该区两个成员省 `map/positions.txt` 的首个 position。
7. 落盘后验：id 1..N 连号、每区 provinces 升序、跨区无重复省、所有陆地省都有区、每区 12 段 weather、weatherpositions 每区 2 条。
8. **还要更新 skill 自身记忆**（本条就是用户要求「记入 skill」的产物）。

### 排查方法（用户钦定：勿反复启动原版，直接对比地图文件）

- **对比地图文件**：与**原版**（`F:\Steam\...\Hearts of Iron IV\map\strategicregions\`，304 区）、**Beta**（同名区域文件，70 区）逐项对比：**id 是否连号**、province 表是否升序、weather 是否齐全、行尾是否干净。
- **对比备份**：`.backups/` 里的旧版本逐字节对比（本次即靠此发现 `\r\r\n` 污染：58,291B vs 50,120B、CRCRLF=8,177 vs 0）。
- **自启动二分**（允许时最有效）：改一处 → 启动 → 看是否出现 `game.log` 的 `Loaded N provinces` / 新崩溃转储。

### 行尾污染（CRCRLF）会怎样

`t.replace('\n', nl)` 式的"统一换行"会把已有 `\r\n` 变成 `\r\r\n`（本 skill 已记录两次）。本次三个地图文件被污染：`DOT_Strategicregions_01.txt`（→ 崩溃）、`airports.txt`、`rocketsites.txt`（各 695 处 → **nudge 报「地图定义错误」**；游戏本体忽略这两文件内容）。**修复=字节级 `b'\r\r\n' → b'\r\n'`**，修完全树扫描确认 0 处残留。

## 州号空洞与补号：只准「简单迁移」（★ 铁律，2026-10-14 用户明令）

### 禁令：不做「全量迁移」

删州/合并州空出号位后，**绝不允许级联重排大批州号**（「把删州留的洞整体前移」这类动几百个州的全表迁移）。
用户原话：「**不要全量迁移，你把最后的 706-709 改成 63,65,66,67 不就行了？**」

- 实证代价（2026-10-13）：删 41 个海州后我交了一版全量迁移 → **debug 都进不去**，由用户找人修回。
- 为什么禁：全量迁移牵动几百个州的 loc/airports/引用/首都/buildings，出错面大、无法逐条核对、回滚困难；
  简单迁移只动 k 个州，可逐条验证。

### 唯一合法补号法：「简单迁移」（尾部补号）

**空出 k 个号位 → 只从号尾搬最后 k 个州填进空位**，引用迁移只针对这 k 个被搬州做。

| 场景 | 空位 | 简单迁移动作 | 结果 |
|---|---|---|---|
| 合并 ABY 62+63+65+66+67→62（2026-10-14） | 63/65/66/67 | 尾部 703/704/705/706 → 63/65/66/67 | 702 州、1-702 连号 |
| 删 41 海州留下空洞（2026-10-13） | 数处 | 尾部州搬入空位（718→709 等，帮手执行） | 1-709 严格连号 |
| 尾部州腾位到 89/90/94（2026-10-13 夜，帮手） | 89/90/94 | 尾部 707→94、708→90、709→89 | 终态可查 state 文件 `# name="STATE_70x"` 注释 |

**陆海分段时两步换位**：设陆洞（升序）h1..hk：**① 陆洞 ← 陆州尾部（降序）**（如 859→855）；
**② 被搬走的陆尾原号 ← 海州尾部（降序）**（如 900→859）。结果：陆段连续、海段连续（尾部自然缩短）、
**总体严格连号**，只动 2k 个州。执行必须**按目标号升序**（先腾小号），否则 rename 撞号中断。
（旧方案「海州段整体前移 41 州」已废弃。）

### 被搬州（k 个）的 5 点引用联动——缺一不可

1. **loc 键**：`DOT_STATE_<old>` → `DOT_STATE_<new>`（州名跟州走；目标位旧 `*` 占位删除让位）
2. **airports / rocketsites 键**：`<old>={…}` → `<new>={…}`——**先删旧键再写新键**（本批残留过 707/708/709 重复键）
3. **state 文件**：文件名 `NNN-State_NNN.txt` + 文件内 `id` 行 + `name="DOT_STATE_N"`（三处同步）
4. **capital / 脚本引用**：`capital = N`、`owns_state / controls_state / has_full_control_of_state / transfer_state / state = N`、奇观决议 `<N> = { add_dynamic_modifier = … }`
5. **buildings.txt**：声明州列行迁移（本批 703-706→63-67 共 177 行）

（合并另有"被并号→存留号"的引用映射（用户指定），与补号搬州是两张映射表：先做合并映射，再补号。）

### 工具与校验

- 工具：`scripts/fill_state_gaps.py --mod <mod根目录> [--dry]`（已内置两步换位 + id/name/capital/buildings/脚本引用联动）——**--dry 结果先给用户过目再落地**。
- **nudge 编辑器对缺号敏感**：游戏本体允许缺号（原版 1.19.3 的 1-1079 有 112 个缺号），但 nudge 启动会弹「地图定义文件存在错误」。缺号在**两段交界**（如陆州尾 860/861 紧邻海州段）时，最优解是**邻段头部前移填补**（海州 862-902 整体前移 2 位到 860-900），全 id 连号且陆州零改动——见 tools/fill_gap_860.py（只动段界两侧少量州，不属于被禁的全量迁移）。
- 前置强制检查（任一命中即拒绝）：capital 指向空白州 / buildings 声明空白州 / 空白州有具名
- 同步：id 行 + 文件名、capital、buildings 第 1 列、DOT_STATE key（删空州 / 映射搬移州 / 查重）
- **州号引用联动迁移（v4 起，"数字 id 关联的修正"自动跟着搬）**：
  · 单值 token：`state = N` / `owns_state` / `controls_state` / `has_full_control_of_state` / `transfer_state`
  · 列表 token：`states = { N N N }`（ai_strategy put_unit_buffers 等）
  · 数字键州作用域块：`<N> = { … }` 且块内含州作用域标记
    （add_dynamic_modifier / set_state_owner / add_building_construction / create_unit 等 11 种）
    —— 如奇观决议的 `60 = { add_dynamic_modifier = … }`
  · 注释行、无标记数字块（如 random_list 权重 `6 = { add_political_power }`）不误伤；
    空州（被删州）的引用无法推断并入目标 → 保持警告，人工先改
- **流程次序**：先转省（省 + buildings 同步 + capital 搬迁 + 名字转移）→ 再补号
- 补号后必念：1-N 无缺号；被搬州旧号全树零残留（旧号可能以 event id 如 `NAT_Event.703`、random_list 权重等**非州引用**出现，要排除误报）；airports/rocketsites 无重复键
- 已在沙箱副本完整验证（500 并入 499 → 861 补位、暗之外海不动，全项通过）；
  v4 引用联动另有合成用例自测（tools/test_fill_gaps_refs.py，22 项断言）

## 转省 → 补号全流程实战（稻妻 22 条批次）

顺序：**转省（工具自动同步 buildings/VP/核心）→ 命名与 VP（按用户给的州号）→ 补号 → 检查**。
转省把单省州清空（如 123/125）→ 触发补号 → 陆州尾部（861/860）搬到空洞号。
**连锁反应清单**（每一项都被实际咬过）：
- 补号前置检查拦下 buildings 孤儿条目 20 条（历史错位）→ 先跑 crash_fix（吸附规则）再补号
- 被搬州（861惑饲滩/860菅名山）的用户命名与首都**自动跟随**（本地化 key 映射 + capital 映射）——
  这要求命名/首都先于补号做，或确认脚本映射覆盖
- 补号后生成点重放必须带 **REMAP**（原始 861→123、860→125），
  且**对照基线也要同样映射**——否则终验永远报 860/861 不符
- 生成点重放/补齐脚本遍历 `s2p` 时**海州也会被放生成点**（海州省份在 positions.txt 有坐标，
  `if not land` 拦不住——要用「无 owner」判定跳过）→ 海州 SL 条目必须清除（41 州 × 10 = 410 条）
- 一州多个 VP 用**多个单对块**（每块独占一行：`victory_points = { 省 值 }`）——
  **实证一致**：原版 381 州、Beta 73 州、Gamma 52 州（2026-10-16 再证：州 466 加 7 块全部生效）；
  **不要**写成单块多对 `{ a b c d }`（报 `set victory points takes 2 parameters` 整块丢弃）
  （旧说法「必须写同一行否则互相覆盖」经 10-16 复查为误诊，已更正）
- 终验对照的「数量不变」要考虑州集合变化：被删空州的份额消失是**正确**的
  （8590 = 8610 − 空州 2×10），不是丢失

## 回退后必须逐条重查之前批次（6 条遗漏事故）

`--restore` / pre_redo 恢复是**全量覆盖**——回退点之后的所有操作（转省、合并、命名、VP、impassable）
都会被冲掉。重做时**必须逐条对照回退前最后 N 批的指令**，不能凭记忆"大概都重做了"。

**检查方法**：每批指令取**前 3 条可验证项**（转省落点 / 州名 key / VP 值+所在州），
在当前文件中逐条核对。任何一条对不上 = 该批有遗漏。

**实战案例**（09-30 pre_redo 恢复后漏了 6 条）：
- 合并 `136+856→131` 的省 66 未跟着并入 → 66 留在了 422
- 合并 `118+435` 的省 118 → 留在了 816
- 转省 `4321→746`、`4454→811`、`474→771` → 三省分别留在 761/827/778
- 根因：回退后我只重做了 VP 和命名，**漏了转省和合并的省份落点**

**规矩**：回退后必须跑 `audit_operations.py`（备份倒序回放）列出回退点之后的所有操作，
逐条核对当前文件是否仍保留那些修改，漏了就补。

## 备份强制（修改 province/state 之前）

**任何**要改动 `history/states/`、`map/buildings.txt` 的操作（转省/合并/补号/换位/VP/重命名），
**第一步必须先跑备份**——用户要求这么做，以便随时回退：

```
python scripts/backup_states.py --mod <mod根目录>          # 备份（states 全部 + buildings.txt）
python scripts/backup_states.py --mod <mod根目录> --list    # 列出全部备份
python scripts/backup_states.py --mod <mod根目录> --restore .backups/states_<时间戳>  # 一键回退
```

- 回退自带安全网：回退前把当前状态另存 `pre_restore_<时间戳>`，可再"回退到回退"
- 本批多个 `--restore`/`--list` 的组合可以逐级回退（像 git 的 commit 链）
- **大批量操作中每完成一个子步骤就备份一次**（转省一次、合并一次、补号一次各自成点）

## State 自检（改州/省后的强制关卡）

**收纳规矩**：项目脚本一律放 `tools/`、产出文档放 `docs/`、运行输出用完即删——不要在项目根目录生成文件。

**触发时机**：任何 state 文件、definition.csv、buildings.txt、州名/VP 本地化被改动之后，
主动问用户「要不要跑一遍 State 自检？」并直接给命令。

**工具**：`scripts/check_states.py --mod <mod根目录> [--baseline <原始buildings.txt>]`

**括号完整性自检**（push GitHub 前必跑，与 CI 同规则）：
`scripts/check_brackets.py --mod <mod根目录>`
（大括号匹配 / simp_chinese 引号成对 / 本地化 BOM——三者任一失败 CI 都会拦）

检查项（一遍全过）：
- A 州文件：文件名=id、括号、tab、空州、缺号（附补号建议）
- B 省覆盖：definition.csv 陆/海省全归属、无重复
- C 核心：owner 与 add_core_of 一致、海州无 owner
- D 胜利点：格式、省⊆州
- E 首都：无悬空
- F 本地化：BOM、DOT_STATE/VICTORY_POINTS 覆盖、孤儿、**同语言目录内**重复
- G buildings：声明州存在、海州无生成点、每陆州 SL 数量（基线模式仅对照 SL——
  省级建筑声明州随转省大范围重排，逐州对照无意义）

经验：english 等其他语言目录的重复 key 是真实脏数据（英文显示取末值），照报不误。

## buildings 第 7 列规则（nudge 报错事故）

buildings.txt 每行**第 7 列就是省号**——游戏判定「声明州是否合法」用的是第 7 列省的归属
（水面标记对海军类吸附最近陆省），**不是**「标记坐标反查的省」。

事故：转省工具按坐标反查同步第 1 列，但**第 7 列没跟**——4403 从 791 转到 109 后，
坐标像素在 791 另一省的条目第 1 列保持 791、第 7 列仍是 4403 → nudge 报 435 条
`Supposed to be '791' but was '109' for province 4403` BUILDING IGNORED，nudge 工具全红。

修复规则（以第 7 列为准）：
- 第 7 列 = 陆省 → 第 1 列 = 该省所属州（SL 与省级类同规则）
- 第 7 列 = 海域省 → 海军类吸附最近陆省定声明州；陆地类标记在水上 = 非法（删或挪）

配套教训：
- 补号搬州时 **name key 行也要联动**（DOT_STATE_<old> → DOT_STATE_<new>），只改 id 行
  会导致州名 key 脱节（nudge 里显示 DOT_STATE_861）
- 验证假设必须与游戏一致：工具间互相验证（都按坐标反查）等于没验证
- check_states.py 的 G 项已内置第 7 列规则检查
- **转省同步必须含海军吸附行**：陆省搬走时，"吸附目标=该省"的海军标记行（col7 是海省、
  像素吸附到该省）声明州也要跟着改——只同步 col7==省号 的行会漏掉它们
  （实证：一次 24 条转省后 11 处 naval_base_spawn 声明州违规）。
  `tools/fix_buildings_col7.py` 按同款吸附算法全量重算声明州 + 复验，转省批次后跑一遍即可。

## 补号搬州的三处联动缺一不可（天云峠/望泷村连环丢失事故）

fill_state_gaps 搬州（如 851→764）时必须三处同步：
1. **id 行**、2. **name 行**（DOT_STATE_<old> → DOT_STATE_<new>）、
3. **本地化 DOT_STATE_<old> → <new> 重映射**。
漏 2 → nudge 显示裸 key；漏 3 → 名字"消失"（用户看到 574=* 而天云峠丢失）。

**重映射必须覆盖式**：目标 key 已有 `*` 占位而搬州带真名 → **覆盖**；
反之搬州带 `*`、目标有真名 → 保留真名。旧版"先到先得"去重把天云峠顶掉了
（`*` 旧行按号序在前）。同样适用于 buildings 联动。

**p 前缀规矩**（用户标注约定）：用户给「p1343 迪弗旧窟」= **省 1343 的胜利点本地化**
（`VICTORY_POINTS_1343:0 "迪弗旧窟"`）；无 p = 州名（`DOT_STATE_<州号>`）。
两者格式相近，**必须按前缀分流**，别把 VP 名字写到州名上。

## states 目录卫生（.b 残留假报事故）

目录里的 `*.b` / `__tmp_*` 等非标准文件会被 `gamma_state_edits` 按文件名前缀
**重复载入同一州** → 假报「重复归属」→ 转省 assert 中断。
规矩：临时备份文件写 `.backups/`，绝不留 states 目录；每次转省前扫一遍非标准文件。

## 格式三件套（转省/合并后自检）

1. **纯 CRLF**（LF 残留 → 工具解析失败）
2. **provinces 升序**（乱序是搬移/合并的副作用，游戏可能容忍但工具链会乱）
3. **BOM**（本地化）

## buildings 终版重整（单一权威规则一次到位）

`tools/rebuild_buildings_final.py`（游戏真实规则，已实测 0 不符）：
- **naval 五类**：声明州 = 省列陆省直用 / 水面标记吸附最近陆省
- **其余类**：声明州 = 标记坐标像素省的所属州（第 7 列多为 0，不参与）
- **SL 生成点**：每陆州 7×1 + anti_air×3（标准配置重放），海州 0 条
- 声明州不存在 → 条目删除

配套 `tools/trim_sl.py`（删超配）、`tools/check_definition.py` /
`check_terrain.py` / `check_mapdef.py` / `check_adj_pos.py`（地图定义健康度）。

**不要用多个部分修复脚本互相覆盖**——一个脚本一次遍历按同一规则对齐全部。

## 打包分发

`tools/pack_skill.py`（如已删，重新内联）：排除 config.json / __pycache__，
附安装说明，zip 到桌面。内测包不含本机路径。

## 常见误判清单

- ❌ 解析器漏全角逗号 → 看不懂的指令报错
- ❌ 多州均分后不查紧凑度 → 长条州
- ❌ 海州忘了删 owner/add_core_of/buildings → 语法错或崩溃
- ❌ 海州模板替换只改 name 没改 id 行 → id 冲突，进游戏必崩
- ❌ VP 值写了中文名 → 引擎读不了
- ❌ 本地化追加后不验 BOM → 整文件失效
- ❌ 地形改造只改 definition.csv 不改 terrain.bmp → 视觉与机制不一致
- ❌ 丘陵判定不放"六国不豁免"分支 → 六国境内永远 0 个丘陵
- ❌ 增量修复脚本互相覆盖 → 越修越乱
- ❌ 忘了 `tbimg.close()` → terrain.bmp 被句柄锁定，shutil.copy2 报 WinError 1224
- ❌ 均分脚本硬编码州号 → 换一组就失效（要参数化，州号从命令行读）
- ❌ 认定"非海即陆"的二分假设 → 遇到定义外省号（如 0 号）误判
- ❌ 州名 key 用 STATE_<id> 撞原版 → 原版地名混入（甲信越）
- ❌ 新州文件用 LF 换行 → 转省工具解析失败
- ❌ 海军建筑按「像素所在省」归州 → 大量条目被游戏丢弃 → 崩溃（要吸附最近陆地省）
- ❌ state_category 写 ocean（不存在）→ 州无类别
- ❌ 写盘后只看「成功」不 diff 内容 → definition.csv 停旧规则三轮未察觉
- ❌ 用户数字只按一种解释（省/州）处理 → 地名全挂错国
- ❌ 飞地目标自动决定 → 越权回滚
- ❌ 补号时海州被搬去填陆地洞 → 陆海段混串（要陆海分离配对）
- ❌ 补号/重放脚本遍历所有州时把海州也放生成点（要按「无 owner」跳过）
- ❌ 一州多个 VP 写成单块多对 `{ a b c d }` → 报错整块丢弃（要**多个单对块**，每块一行）
- ❌ 生成点重放对照基线不做州号映射 → 终验永远报旧号不符
- ❌ buildings 同步只按坐标反查改第 1 列、不管第 7 列省号 → nudge 全红 BUILDING IGNORED
- ❌ 补号搬州只改 id 行不改 name 行 → 州名 key 脱节
- ❌ 补号搬州只联动 id 行 → name key 与本地化脱节
- ❌ 本地化重映射"先到先得"去重 → 搬州真名被 `*` 占位顶掉（天云峠）
- ❌ 用户 p 前缀当成州名写 → 覆盖无辜州的州名
- ❌ states 目录留 .b/__tmp 文件 → 工具重复载入假报重复归属
- ❌ 多个部分修复脚本各持口径互相覆盖 → 越修越乱（终版=单一脚本一次遍历）
- ❌ 回退后凭记忆"大概都重做了" → 实际漏了 6 条（合并/转省落点）
- ❌ 回退后不跑 audit_operations.py 核对 → 遗漏不可见
- ❌ 删州/合并后用「全量迁移」级联重排几百州 → 用户铁律禁止（曾致 debug 都进不去）；只准简单迁移（尾部 k 个州补空位）
- ❌ 简单迁移漏迁 airports / rocketsites 键 → 旧键滞留成重复键（5 点联动第 2 点）
- ❌ 补号后扫旧号残留把 event id（如 NAT_Event.703）、random_list 权重误报为州引用 → 要排除非州引用

## 转省/合并/改号后的 buildings 连锁（2026-10-16 进游戏崩溃事故）

**事故**：转省 + 合并 + 尾部补号（只动 state 文件与引用）后，游戏**选完国家加载到最后崩溃**。日志三类：
1. `coastal but has no port ... This will likely crash the game`（**崩溃类**）——被转省/合并省份的港口行
   （naval_base_spawn 等）第 1 列仍是旧州号 → 整行被游戏丢弃 → 沿海省无港口 → 进游戏崩。
2. `mapbuildings.cpp:716 not within specified state. Supposed to be 'A' but was 'B'` ×N——凡被改动的州，
   其 buildings 行第 1 列都要跟着改（本次 149 行）。
3. `invalid state (701` —— 补号改号后，**旧号残留的 buildings 行**（701/702）变成"州不存在"；
   按 补号映射（701→522、702→511）整体替换即可（本次 74 行）。

**★ 权威判官工作流（推荐）**：改完州/省后**启动一次游戏**（debug 即可，到菜单就停），然后：
- `grep 'not within specified state' logs/error.log` → 把每条的 **`was 'B'` 的 B 写回该行第 1 列**（B = 游戏按标记像素/省列算出的正确州）；
- `grep 'invalid state (' error.log` → 按改号映射替换旧号；
- `grep 'coastal but has no port' error.log` → 这些省缺港口行，需给它们补 `naval_base_spawn` 行
  （`<州>;naval_base_spawn;<x>;9.50;<z>;0.00;<该省号>`，坐标取 positions.txt；或把该省已有的海军行第 1 列改对）；
- 复跑游戏直到 **MAP_ERROR / not within / invalid state / coastal-no-port 全为 0**。

**其它必查连锁**：
- **州级生成点（SL）会跟着坐标被搬走**：若某州的 SL 行坐标恰好落在被转走的省里，游戏会把它们判给新州 →
  原州变成 `MAP_ERROR: no air base site defined for state N`（**致命**）。修：给该州在其剩余省份的
  positions 坐标上补 7×1 + anti_air×3 十行 SL（本次 474 州）。
- **合并州改名/换号的引用**：`capital`（本次 LAW 首都 511→510）、`airports.txt`/`rocketsites.txt` 键、
  `DOT_STATE_<id>` 本地化键、脚本里 `state = N` 族，**连带旧号一起清**。
- **合并时州级建筑取"存留州原值"或≤上限，绝不"相加"**：本次把 5 个州的 infrastructure 相加成 10（上限 5）→
  `State Error: Trying to set invalid state building "infrastructure" to state #62`（该行被引擎丢弃）。
- **新建战略区会"切断"区域连通性**：把湖/海省从大区域划出后，某些孤岛省的唯一邻接省被划走 →
  `MAP_ERROR: Naval strategic region X is fractioned! ... separated: <省>`（**崩溃类**，release 弹窗）。
  修：把该孤岛省一并划入新区域（本次 4679 与果酒湖）。
- `14_sea_on_actions.txt` 等**原版 DLC 的 on_actions** 引用原版州号（>700）→ 开局 `set_state_flag invalid state`
  若干条，**既有噪音、无法修**（不属 mod）。

