# 提瓦特黎明（Daybreak of Teyvat）HOI4 Mod 仓库 — 工作约定

本文件是本仓库的常驻工作约定，等价于此前 ZCode/Claude Code 的记忆库。细节记忆在 `.dsh/memory/`，技能在 `.dsh/skills/`。

## 项目概况

- 钢铁雄心4 模组，三套版本目录：`Ilyich Genshin Test Version`（旧）/ `Daybreak of Teyvat Alpha Version` / `Daybreak of Teyvat Beta Version` / `Daybreak of Teyvat Gamma Version`。**主线开发 = Gamma**。
- **游戏实际加载的是本地部署副本**：`C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version`，不是仓库目录。
- 用户同时会找别的 AI 诊断，结论可能方向对但基于旧日志——一切结论以**最新日志和全量扫描**为准。

## 六条铁律

### 1. 双副本同改，改完核对
仓库 `...\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version` 与本地部署副本**必须同时写**。只改仓库游戏不生效；只改本地下次同步丢失。
交付前跑全树对照（文件数/大小/同大小哈希），不用 mtime（会骗人）。参考脚本 `tools/compare_copies.py`、`tools/what_changed.py`。2026-10-17 实检 17,203 文件 0 差异。
**部署副本在仓库外，写入会被沙箱拒绝**（workspace-write 只允许仓库内）——需要一次 `danger-full-access` 提权并说明原因；改完两处哈希必须一致。

### 2. 州号 1-N 严格连号，删/合并后立即补号
任何删州、合并州、新增战略区之后，**1..N 必须连续无空洞**，并同步五处：
① 本地化键 ② `airports.txt`/`rocketsites.txt` 键 ③ 州文件 `id`/`name` 键 ④ `capital`/脚本引用 ⑤ `buildings.txt` 行。

- **只准「简单迁移」（尾部补号）**：把号尾最后 k 个州搬进空出的号位，仅迁移这 k 个州。**严禁「全量迁移」**级联重排几百个州号（10-13 全量迁移方案导致 debug 都进不去，用户找人修回）。
- 战略区 id 同样必须连号（1..N）。10-15 崩溃事故根因就是新战略区用了 `id=46`（2-45 空洞 → 引擎越界静默崩溃，日志停在 `defines loaded`）。改成 `id=2` 立即能进。
- 州文件第 3 行 `name="DOT_STATE_N" # name="STATE_老号"` 是历次重划的权威「原号→现号」对照表；全表在 `tools/find_was_numbers_out.txt`，旧号引用迁移先查它。

### 3. 改地块归属/重划必须用户点名
转省、飞地并入、均分重划、空号重排：**目标必须由用户明确指定**，不得以「地理上更合理」自行推断写盘。我曾自行迁 5 处飞地被全部要求回滚。
- 模糊指令 → 先只读侦察出方案与影响面（哪些州/省、是否跨国），把选项摆给用户，等点名。
- 点名的指令（如 `188,3548+135`）可直接执行；`和周围的s均分` 这类有 A/B 两种做法，必须让用户选。
- 动手前 `--dry` 干跑念明细；每个写盘动作有可回滚备份（`.backups/<批次>_<时间戳>`）。
- 例外：用户给了明确设计图的大面积重划（如至冬涂色图）可自动落地，但**落地后主动报告歧义项**（双名取后、未涂省挂靠、落选名字）等用户裁决。

### 4. 回复简洁、命令无歧义、不反复追问
- 汇报一次即止，不追发「请确认 X 是否正常」；有问题用户会主动说。
- 结语只陈述已完成事项与遗留项。命令/指令示例用词精确、格式统一。
- 思考过程精简，不堆语气词、不自我重复。

### 5. 文件放置与卫生
- 脚本一律 `tools/`，产出文档 `docs/`，运行输出用完即删。**不在项目根目录生成任何文件**（根目录只留 mod 版本目录、README、.gitignore）。
- `tools/*.py` 被 `.gitignore` 忽略，仅存本机 → 交付脚本要说明，别指望 clone 可见。
- 改本地化 yml 必须补 BOM（UTF-8-SIG）与 CRLF；写盘后回读验证。
- 字节级陷阱：`t.replace('\n', nl)` 会写出 `\r\r\n`（双 CR）；正则 `[ \t]*$` 会吞掉 `\r`，收尾用 `(?=\r?$)`。
- push 前必跑 `check_brackets.py --mod <mod根目录>`（与 `ci-test/Check.py` 同规则：大括号配对、simp_chinese 引号成对、本地化 BOM）。

### 6. 改州/省后走「判官工作流」
改完州/省 → 启动游戏跑一次 → 按 `error.log` 报错循环修 `buildings.txt` 到全 0。
- **`tools/rebuild_buildings_final.py` 的海军吸附口径与游戏不符**（它取 3×3 方格最多数省，游戏取最近沿海省），改州后勿盲跑。
- `check_states.py --mod <mod根目录>` 自检：州语法/省覆盖/核心/VP/首都/本地化/buildings 第 7 列/海州 SL。
- 空州必闪退；VP 一 block 只收一对参数（多个 VP = 多个独立 block）。

## 地图指令解析格式（用户钦定）

| 写法 | 含义 |
|---|---|
| `2149烟谜主（25，首都）` | **VP**：括号内为胜利点数，「首都」标记；同国多首都按指令顺序最后生效 |
| `643圣火竞技场`（无括号） | **州命名**：id 直给州号，**绝不做「省号→所在州」解析** |
| `389胜利点清除` / `1482*` | 清除该省 VP（州条目 + `VICTORY_POINTS_<pid>` 键都删） |
| `735+759=735` | 转省：把省 759 转入州 735（默认转省，不是人工映射） |
| `A+B=A`（合并） | 合并州；合并与补号是连续两步 |
| `520+521+…=Region9龙脊雪山` | **新建 9 号战略区**「龙脊雪山」：成员州展开成省列表、从原区（Region1）移除、12 段 weather、weatherpositions 每区 2 条、loc key `DOT_STRATEGICREGIONS_09`（步骤见 gamma-pipeline「指令语法：RegionN名称」） |

- 用户指令即权威：同名条目覆盖现值；VP 括号数值=最终值；同批同 pid/州号两条 → 后者生效并在报告标出。
- 用户会即时修正自己（「是 708 和 750，不是 718」）——照最新一条执行。
- 批次落盘后逐条对账（模板 `tools/audit_natlan_batch.py`：当前值 vs 批次前备份，输出 ✓/✗）。

## 已验证的坑（Gamma UI/地图）

- DLC 图标少一个 = `frontendmainview.gui` 的 `mainmenu_dlc_ownership` 窗口高度裁掉第 10 个图标。
- 社媒 X 图标不显示 = `core.gfx` 缺 sprite `x`（补 `gfx/interface/icon_x.dds`）。
- 选国 tag 顺序乱 = `common/bookmarks/*.txt` 条目顺序 + 每条必须 `version = base_game`。
- 背景预览图不对 = 每张加载图需 `GFX_<名>_small` 指向 `gfx/loadingscreens/<名>_small.dds`（192×144），并补 `interface/small_background.gfx`；原版 `_small.dds` 是**未压缩 A8R8G8B8**（128B 头 + W×H×4），PIL 不能写 DDS。
- **分叉过的 `.gui` 不能直接「补原版元素块」**（布局会乱）；补 sprite / 新增独立文件相对安全。
- 海州无陆地省 → 引擎机场选址永远报 MAP_ERROR；Gamma 已删除全部海州。
- `has_full_control_of_state` 是单 token（`has_full_control_of state` 错）。
- definition.csv 第 5 列 kind、**第 6 列 coastal** 是 `only_costeal` 建筑判定依据。

## 技能（.dsh/skills/）

22 个技能已装入本仓库 `.dsh/skills/`（DSH 项目级技能根）。主线是 **`hoi4-modder-cn` v2.30（作者猫妖）**：hook 4 mod 全流程、`references/gamma-pipeline.md` 是主经验库、`scripts/` 有 check_states / fill_state_gaps / check_brackets / backup_states 等。另有 superpowers 系列（brainstorming / writing-plans / executing-plans / systematic-debugging / TDD / verification-before-completion 等）、中文工作流技能、`rhoiscribe-hoi4`（本地 HOI4 提示包，约 23 MB，exe 已 gitignore，可选）。

自检脚本用 `.dsh/skills/hoi4-modder-cn/scripts/` 下的版本；`check_states.py` 需要带 numpy 的运行时，`check_brackets.py` 已固定 UTF-8 读取（不再需要 `-X utf8`）。`~/.zcode`、`~/.claude` 里还有 2.22 旧副本，沙箱不允许改，不要误用。

任务匹配技能描述时先 `skill` 加载再动手；技能内容与本文冲突时，以用户最新指令为准。

## 记忆（.dsh/memory/）

`MEMORY.md` 是索引，一行一条；细节按需读单文件：

- `gamma-mod-progress.md` — Gamma 进度、崩溃排查史、州号映射、待办（10-18 快照：689 州、战略区 1-9；**以最新条目为准**）
- `gamma-tool-suite.md` — `tools/` 各脚本用途与坑（改州后勿盲跑 rebuild_buildings_final；fill_state_gaps 不迁 airports/rocketsites 键）
- `hoi4-skill-structure.md` — skill 结构/版本递增规矩/分发
- `ui-bugs-interface-stale-copies.md` — 10-17 UI bug 根因表
- `state-renumber-simple-migration.md` / `mod-dual-copy-rule.md` / `gamma-map-change-approval.md` / `user-gives-state-ids-for-names.md` / `user-reply-concise.md` — 五条用户规矩的完整来龙去脉

索引与细节文件冲突时以索引行为准，并顺手修正记录。
