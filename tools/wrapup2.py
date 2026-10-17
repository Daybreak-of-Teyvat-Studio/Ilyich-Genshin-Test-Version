# -*- coding: utf-8 -*-
import io, os, shutil, sys, datetime
sys.stdout.reconfigure(encoding='utf-8')
SK = r'C:\Users\LR\.zcode\skills\hoi4-modder-cn'
CL = r'C:\Users\LR\.claude\skills\hoi4-modder-cn'

SECTION = '''
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
'''

g = os.path.join(SK, 'references', 'gamma-pipeline.md')
t = io.open(g, 'rb').read().decode('utf-8-sig')
if '转省/合并/改号后的 buildings 连锁' not in t:
    t = t.rstrip('\r\n') + '\n' + SECTION + '\n'
io.open(g, 'wb').write(t.encode('utf-8'))
print('gamma-pipeline.md 追加新章 ✓', len(t), '字符')

# 版本 2.11 → 2.20
fp = os.path.join(SK, 'SKILL.md')
s = io.open(fp, 'rb').read().decode('utf-8-sig')
s = s.replace('version: 2.11', 'version: 2.20').replace('版本：v2.11', '版本：v2.20').replace('当前版本 **v2.11**', '当前版本 **v2.20**')
io.open(fp, 'wb').write(s.encode('utf-8'))
for f in ('SKILL.md', 'references/gamma-pipeline.md'):
    shutil.copy2(os.path.join(SK, f.replace('/', os.sep)), os.path.join(CL, f.replace('/', os.sep)))
print('skill v2.20 + .claude 同步 ✓')

# 记忆
M = r'C:\Users\LR\.zcode\cli\memories\projects\ilyich-genshin-test-version-57bab93f04048e34\memory\gamma-mod-progress.md'
mt = io.open(M, 'rb').read().decode('utf-8-sig')
add = '''
## 10-16 夜 大手术（转省+合并+补号+战略区）——已全部修复并通过判官复验
- **战略区**：①新区域「果酒湖」id=3（6 个海省 5719/6886/6937/7104/7293/7776 + **湖心岛 4679**——不加它区域1 会被判 fractioned=崩溃类）；②区域1 改名 **暗之外海**；③区域2 名 马斯克礁。ids {1,2,3} 连号 ✓。
- **转省**：1570→484、{1306,1960,3515}→435、845→500（VP 与省级块随省迁移 ✓）。
- **合并**：510+511+522→510（17 省）；**补号**：702→511、701→522（⇒ **700 州、1-700 连号**）。引用同步：LAW 首都 511→510、airports/rocketsites 键、loc（这批全是 `*` 占位无损失）。
- **buildings 连锁修复（判官法）**：149 行 `not within` → 按报错的 `was` 值写回第 1 列；74 行 `invalid state`（701/702 旧号）→ 按补号映射替换；9 省 `coastal no port` → 补 naval_base_spawn 行；474 州生成点被搬走 → 补回 10 行 SL。**终验：MAP_ERROR / not within / invalid state / coastal / fractioned 全 0 ✓**。
- **我先前 rebuild_buildings_final 的海军吸附口径与游戏不符**（"方格最多数"≠游戏"最近沿海省"），改坏了 14 行；已按游戏给的 `was` 值复原。**该工具的海军吸附逻辑不可信，改州后一律走判官法**。
- 既有噪音（非 mod、无法修）：原版 DLC `14_sea_on_actions.txt` 开局 6 条 `set_state_flag invalid state`（引用原版州号）；`X crossing (4095,480)`；frontend UI 缺项。
- 备份：`.backups/surg_* / refsync / o2_ / port_ / final_*` 多份。
'''
if '10-16 夜 大手术' not in mt:
    mt = mt.rstrip('\r\n') + '\n' + add + '\n'
io.open(M, 'wb').write(mt.encode('utf-8'))
mi = os.path.join(os.path.dirname(M), 'MEMORY.md')
s2 = io.open(mi, 'rb').read().decode('utf-8-sig')
s2 = s2.replace('hoi4-modder-cn（猫妖，v2.11；', 'hoi4-modder-cn（猫妖，v2.20；')
io.open(mi, 'wb').write(s2.encode('utf-8'))
print('记忆 + MEMORY.md ✓')
