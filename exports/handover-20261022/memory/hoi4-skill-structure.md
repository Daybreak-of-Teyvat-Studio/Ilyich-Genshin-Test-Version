---
name: hoi4-skill-structure
description: HOI4 skill hoi4-modder-cn（作者猫妖，v2.30）的位置、目录结构、版本递增规矩、独特功能章节与自检/补号/备份工具（禁全量迁移+简单迁移+数字 id 连号铁律已入册）
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_3c421fb8-e84d-47d4-a44c-53452b380660
---

# HOI4 skill **hoi4-modder-cn**（作者署名 **猫妖**，**版本 v2.30**）

位置（2026-10-17 起，DSH 迁移后**主副本**）：`C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\.dsh\skills\hoi4-modder-cn`（DSH 项目级技能根 `<项目>/.dsh/skills`，全 22 技能同装于此）。旧副本：`~/.zcode/skills/hoi4-modder-cn` 与 `~/.claude/skills/hoi4-modder-cn`，仍停在 v2.22 且沙箱不允许改（要同步需一次提权）。旧记：2026-10-04 从 `skills/hoi4` 重命名；`~/.claude/skills/hoi4`（v1.2 时代旧副本）已于 10-14 删除，备份 `C:\Users\LR\.claude\hoi4_skill_backup_20261014.zip`。两份均无 config.json（首次向导各自跑一次）。

版本历程：v1.2 → 1.3（空州闪退/VP一block一对/字节级\r陷阱）→ 1.4（重命名）→ 1.5（fill v4 引用联动）→ 1.6（纳塔批次事故）→ 1.65（括号分流格式规矩）→ 1.75（转省须联动海军吸附行）→ 1.8（合并必迁清单：本地化/修正/奇观）→ 1.9（涂色重划流水线 + fill 按相执行 + 连锁合并覆盖 + buildings 内嵌块括号配对）→ 1.95（beta→gamma 本地化桥迁移流水线）→ 1.96（启动竞态诊断三步 + 触发器正确名 has_full_control_of_state）→ 1.99 → **2.00（2026-10-14：禁「全量迁移」铁律 + 「简单迁移」尾部补号方法入 SKILL.md/gamma-pipeline.md/user-guide.md）** → **2.10（2026-10-15：战略区事故——数字 id 必须连号 + 战略区必备字段（全年 weather/升序省号/weatherpositions）+ CRCRLF 行尾污染与 nudge 报错关系，写入 SKILL.md 铁律与 gamma-pipeline.md 新章）** → **2.11（2026-10-16：更正旧误诊「一州多个 VP 必须写同一行」→ 正确=多个单对块独立行，原版 381 州/Beta 73 州/Gamma 52 州实证）** → **2.20（2026-10-16 夜：转省/合并/改号后的 buildings 连锁清单 + 「判官工作流」入 gamma-pipeline.md——改完州/省跑一次游戏，按 error.log 报错循环修到全 0）** → **2.21（2026-10-17：version-adapt.md 新增「interface/ 旧副本致 UI 缺陷」案例表——名字集差 → 日志点名 → 补差异块，禁止整文件替换分叉文件）** → **2.22（2026-10-17：迁移前末版，改动未记录在案）** → **2.23（2026-10-17：check_brackets.py 两处 open 固定 `encoding='utf-8'`——修 Windows cp936 默认编码把 UTF-8 中文读成乱码、误报 4 文件 13 行「双引号有问题」）** → **2.30（2026-10-18：新增「指令语法：RegionN名称」章节——用户 A+B+…=RegionN名 直接新建战略区：成员州展开省列表、从原区移除、12 段 weather、weatherpositions 2 条、loc key DOT_STRATEGICREGIONS_NN；SKILL.md 铁律同步一句）。**

结构：`SKILL.md`（快速开始入口、**⭐ 独特功能章节**（六项加粗+功能说明：地图迁移/一键备份回滚/双自检/建筑高程防穿模/全图改造流水线/闪退定位）、首次使用向导（配套 superpowers-zh、rhoiscribe-hoi4）、版本递增规矩）、`config.json`（hoi4_root=F:\Steam...\Hearts of Iron IV）、`scripts/`（check_states.py、fill_state_gaps.py、backup_states.py、check_brackets.py、fix_buildings_height.py、fix_height_crlf.py、fix_pierce.py——后三件**绿豆糕**制作）、`references/`（user-guide.md、task-roadmaps.md、paradox-syntax.md、stat-keys.md、map-data.md、buildings-height.md、**gamma-pipeline.md**（主经验库）、version-adapt.md、ra-notes.md 等）。

## 版本递增规矩（已写入 SKILL.md）
大更新 +0.1（新脚本/新章节/规则变更）；小更新 +0.01~0.05；正式版=整数（2.0）。三处同步：frontmatter、向导横幅、开源说明。

## fill_state_gaps.py v4+
两步尾部换位：陆洞（升序）← 陆尾（降序）；被搬陆尾原号 ← 海尾；id/name 行/文件名/capital/buildings 第1列/DOT_STATE 本地化（覆盖式）联动。
**v4 引用联动**（用户钦定的"数字 id 关联的修正和本地化自动迁移"）：① 单值 token `state/owns_state/controls_state/has_full_control_of/transfer_state = N`；② `states = { N N N }` 列表；③ 数字键州作用域块含 11 种标记。注释行/无标记数字块不误伤。合成自测 `tools/test_fill_gaps_refs.py` 22 断言。
**两处已修**：搬移必须**按相执行**（禁止跨相按目标号全局排序，洞号大于搬出者自身号时会先迁入后迁出 → FileExistsError）；**纯目标 id 的旧占位行让位**（`pure_targets = moved.values() - moved.keys()`，否则补号后本地化重复 key）。

## 自检
- `check_states.py --mod <mod根目录>`：州语法/省覆盖/核心/VP/首都/本地化 BOM+查重+孤儿/buildings 第 7 列+海州 SL
- `check_brackets.py --mod <mod根目录>`：与 GitHub CI 同规则（大括号/simp_chinese 引号/UTF-8-SIG），push 前必跑
- `backup_states.py --mod <mod根目录> [--restore <目录>]`：改省/州前强制备份

## gamma-pipeline.md 关键条目（新经验都沉淀在这）
空州必闪退；VP 一 block 只收一对参数；字节级两坑（`t.replace('\n',nl)` 致 \r\r\n、正则 `[ \t]*$` 吞 \r → 用 `(?=\r?$)`）；州号列表被当省号解析（无 p 前缀=州号直给；错号覆盖真名要查批次前备份恢复）；同路径先 'wb' 后读=文件清零；re.sub 勿重复拼捕获组已有字符；涂色重划流水线；大规模补号三坑；buildings 块提取必须括号配对；**州号空洞与补号：只准「简单迁移」（尾部补号），禁「全量迁移」——5 点联动 ①loc ②airports/rocketsites ③state 文件 id/name ④capital/脚本引用 ⑤buildings 行**；**beta→gamma 本地化桥迁移**（只认桥不认数值巧合——两版州号可能撞号；**只认活键**，死键=陈旧移植；**禁止盲跑 apply**）；**启动竞态**（Loaded 13414=原版地图 → 部署未完成就启动）；**触发器名 has_full_control_of_state 是单 token**；**无效 dockyard/错州省级块**（海岸省被划走→州级 only_costal 建筑非法；省级块要随省迁州）。

## 分发产物
桌面 `hoi4-modder-cn-v1.8-内测版.zip`（pack_skill.py 生成，排除 config.json/__pycache__，附安装说明）——**skill 已到 v2.20，包过期，再分发需重打**。

关联 [[gamma-tool-suite]]、[[gamma-mod-progress]]
