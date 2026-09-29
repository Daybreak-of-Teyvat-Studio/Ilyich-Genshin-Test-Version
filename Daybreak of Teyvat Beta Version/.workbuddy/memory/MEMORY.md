# MEMORY.md —— 提瓦特黎明 Beta（项目长期备忘）

> HOI4 1.19 的可复用知识已收进技能 `hoi4-mod-bug-triage`。本文件只记**本项目特有**的路径、环境与状态。

## 环境
- 文件 I/O 走 Python 绝对路径：`C:/Users/XIANGZIYUAN/.workbuddy/binaries/python/versions/3.13.12/python.exe`；**Bash 工具能返回 stdout，PowerShell 会吞 stdout**；bash 的 coreutils（`ls`/`cd`/`grep`/`dirname`）时好时坏，不要依赖。
- ⚠️ 控制台按 GBK 显示 UTF-8 会造成"假乱码" → 只认字节，或写文件再 Read。
- 长跑脚本**重定向到文件再读**，别管道给 `tail`/`head`（管道破裂会中断写入循环）。
- 整行删/插：`open(p,'r',encoding='utf-8-sig',newline='')` 读 → `.split('\n')`（元素自带 `\r`）→ `'\n'.join()` 写回（也 `newline=''`）。CRLF/LF 混排也不动。

## 路径
| 用途 | 路径 |
|---|---|
| MOD 根 | `...\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Beta Version` |
| 原版 1.19.3 | `C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV` |
| 脚本/备份 | `C:\Users\XIANGZIYUAN\hoi4lint\`（`backup_MOD_batch1..32`） |
| 修复前报错快照 | `hoi4lint\betamod_errors.txt`（499 处） |
| 原版 key 语料 | `hoi4lint\vanilla_tokens.pkl`（41396 token） |
| 手册 key 抽取 | `hoi4lint\manual_keys.json` / `_detail.json`（1696 个） |
| 日志 | `Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log` |
| 手册 | `docs/DOT_HOI4_Modding_Skills.md`（32844 行） |

## 工作区特性
- 工作区会被外部副本**整份覆盖**；**外部进程还会并发插行**（实测往 3 个 focus 文件插了 221 行 `icon`）→ 动手前先重扫当前状态 + 先备份。
- 全目录扫描排除 `.backups\`、`备份文件BY Ruka\`、`desktop.ini`、`gfx/_convert_log.txt`。
- 启动器读 `Documents/.../mod/` 那份 `.mod`；工作区副本的 `path=` 指向 `D:/MOD/...` 是错的。
- 生效 `replace_path` **10 条**：history/countries|states|units、common/bookmarks|resources|ai_strategy|ai_strategy_plans、events、map/strategicregions|supplyareas。`common/national_focus` 与 `continuous_focus` **不在内** → MOD 里那两个空文件是必需的屏蔽开关。
- 曾同时加载 9 个 MOD（Beta、Gamma、Ilyich Build Landmark / DoT / Peace Negotiation / Tech and Model / Wish System / Nuke Enhancement、ugc_3187424293）；语言 `l_simp_chinese`。

## 方法论（要点，细则见技能）
1. **以 error.log 为准**；日志按帧重复 → 先按 (文件, 行) 去重（17 MB → 532 条）。
2. 日志**覆盖全部已加载 MOD** → 用 `os.walk(MOD)` 建「相对路径 → 全路径」索引过滤（825 处里 499 处属 Beta）。
3. 脚本用「行号 + 内容」**双断言**，**dry-run 必须 0 MISS** 才 `--apply`；改完三校验：**BOM 保留 / CRLF 减少量 == 删行数 / 括号 depth 不变**。幂等靠「先从 backup 还原再干净跑一次」。
4. **「日志干净」必须先证伪**：查 `dlc_load.json` 的 `enabled_mods`；`game.log` 报 **Loaded 11507 provinces** 才是本 MOD（13414 = 原版地球 = 没加载）。
5. 报错行号用 `near line: N`，不用 `[file:N]`。
6. ⚠️ **区分「纯语法修复」vs「改变玩法的修复」**：后者（补回丢失子单位/分类、改国策树、AI 装备设计、改 state flag 名）**先报告作者拍板** —— 作者常故意放坏来禁用内容。
7. 「未定义」必须**跨全部已加载 MOD + 原版**搜一遍再定论。
8. token 合法性双裁判：手册 key 表 + `vanilla_tokens.pkl`（配 `difflib`）。**只有 `Unexpected token: X` 才证明键被移除**。

## 崩溃类问题（独立于"报错清理"的另一条线）
- **症状定位法**：崩溃先查 `crashes\<时间戳>\logs\error.log` 里带引擎自述警告的行
  （如 `gui.cpp:931: Undefined GUI_TYPE: X - This will most likely crash the game`）；
  再用 `minidump.dmp` 的字符串拿"崩溃时正在读的文件"。
- ⚠️ **`error.log` 尾部有固定噪音**，每次都出现在同一位置、**不是崩溃原因**，别被带偏：
  `event_target:WTT_communist_china`、`Invalid state for is_controlled_by 907 = GER`、
  `events/SEA_Japan.txt:14661: controller: invalid event target: controller`。
- 崩溃样本常**跨多天重复且完全同源**（栈地址一致）→ 先按"异常码 + 栈偏移"分组，别逐份当新问题查。
- 队列里疑似共犯（**各崩溃日期的 mods 不同**）：`hoi4_20260923_*` 上午那批全是
  **`Daybreak of Teyvat Gamma Version.mod`**（该版地图文件几乎全空：`supply_nodes.txt`=3B、
  `airports/railways/rocketsites`=0B，`history/units/` 目录整个不存在）；
  09-23 12:47 与 09-24 22:26 两份是 **`Ilyich Genshin Daybreak of Teyvat.mod`（＝Beta）**。
- **2026-09-24 的真凶（✅ 已修复）**：
  `common/scripted_guis/acedemy_of_science_scripted_gui.txt:5` 的
  `window_name = "acedemy_of_science_decision_ui_window"` **从未有任何 .gui 定义过**
  （Beta/Gamma/Release 三版皆无；git 全历史也只有引用方，没有本体）
  → 玩家跨日时引擎重建脚本窗口拿到空指针 → `C0000005` 闪退（"过了一天就崩"）。
  触发 flag `DVA_start_research_plan_flag` 来自 `DVA_focustree.txt:1907`
  （focus `DVA_establish_institute_of_Tower`）。
  **修复**：新建 `interface/DVA_acedemy_of_science_scripted_gui.gui` 定义该窗口
  （10 个 icon：`dvalin_power_1..3_icon` → `GFX_DVA_governer1/2/3`；
  `dvalin_control_1..7_icon` → `quadTextureSprite = GFX_war_escalation_level_1..7`，原版 `eventwindow.gfx` 有），
  并删除 `parent_window_token = technology_tab`。**保留 `context_type = player_context`**
  （它没被任何 decision category 绑定，改成 `decision_category` 会无处挂载）。
  校验：49 个 window_name **孤儿 0**；括号平衡；properties 10 元素与 .gui 一一对应。
  备份 `hoi4lint/backup_MOD_batch33/{,fixed/}`。
  修法 B（应急 1 行）：`visible = { always = no }`。
- ✅ **别误判 `parent_window_token`**：`technology_tab` 是原版
  `common/scripted_guis/_documentation.md` 白名单里的**合法 token**，不是坏 token；
  致命的只是 `window_name` 指向的容器没定义。
- **同类隐患自查脚本**：`hoi4lint\window_check.py` / `window_check2.py` —— 把
  `interface/**/*.gui` 全文拼起来，逐条校验每个 `scripted_guis/*.txt` 的 `window_name`
  是否有对应定义（`.gui` 里认的是 `name = "X"`）。**改完 scripted_gui 必跑一次**。
  校验辅助：`hoi4lint\verify_fix.py`（孤儿数 + 括号平衡 + properties↔gui 元素对照）。

## 已知不可修复
- `events/LYY_Ganyu_Events.txt`、`LYY_Keqing_Events.txt`、`LYY_News.txt`、`common/country_leader/LYY_traits.txt` 的中文注释**编码被彻底损坏**（字面量 `U+FFFD`，最早的 `backup_MOD` 就已损坏）→ 原文永久丢失，只能清理不能还原；batch31 已清除（全库 0 残留）。
- **Gamma 版有完全相同的损坏，尚未处理**（不在工作区内）。

## 用户偏好（重要）
- **禁止"偷懒注释掉问题代码"**：要读 `docs/DOT_HOI4_Modding_Skills.md` 做**真实修复**；注释只在引擎确无此能力且经用户确认后才用（batch13/14 纯注释法已回滚）。已注释的非法结构要**还原成等价的合法结构**（如裸 `limit` → `if = { limit = {…} …效果 }`），而不是长期注释。
- **费 token 的活先搁置**：先做机械、低风险的那批；「技术类别逐条定夺 / 作用域改写 / 装备模块实测」这类费脑子的先放着。
