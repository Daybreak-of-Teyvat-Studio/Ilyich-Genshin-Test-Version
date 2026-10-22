# -*- coding: utf-8 -*-
import io, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
SK = r'C:\Users\LR\.zcode\skills\hoi4-modder-cn'
CL = r'C:\Users\LR\.claude\skills\hoi4-modder-cn'

ADD = '''
## 实战案例：interface/ 旧副本致 UI 缺陷（2026-10-17，三个 bug 一网打尽）

游戏更新后，mod 里"原版文件的旧副本"会缺新 sprite/新 GUI 元素 → 各类 UI 半坏。本次三例：

| 症状 | 文件 | 缺什么 | 修法 |
|---|---|---|---|
| 选国界面国家列顺序/筛选乱 | `interface/frontendgamesetupview.gui` | `filters`、`more_countries`、`new_content`、`country_name`（日志 "Could not find ... in window" 直接点名）+ 笔误 `GFX country filter_entry`（空格！应为下划线） | 从原版当前文件**按元素块提取**（括号配对）插到 mod 文件同名父窗口的收尾 `}` 前；笔误替换；另补 `GFX_country_filter_entry` sprite 到 `frontendgamesetupview.gfx` |
| 主菜单社媒行一个图标不显示 | `interface/core.gfx` | 新版 sprite `x`（X 图标）等 8 个 | 把原版多出的 spriteType 块原样插进 mod 的 `spriteTypes = {` 收尾前（顺序无关） |
| 主菜单左下角最新 DLC 图标异常 | `interface/frontendmainview.gfx` | `GFX_frontend_banner_dlc051/052`、`GFX_frontend_medal_dlc051` | 同上 |

**诊断法（快）**：
1. 对 mod 的 `interface/` 每个"与原版同名"的文件做**名字集差**（`name = "..."` 全集：sprite 名 / GUI 元素名）→"原版有 mod 无"= 缺项清单；
2. `error.log` 里 `Could not find sprite type [...]` / `Could not find "X" in window Y` = 缺失的 sprite 名 + **元素所在的父窗口名**（插入位置直接由它给出）；
3. 修法优先"**补差异块**"（mod 文件是设计分叉时，绝不能整文件替换原版——会丢 mod 的布局）；纯旧副本（mod 独有≈0）才可整文件替换或删除。
4. 验证：跑一次游戏，`error.log` 里上述两类报错归 0。

**教训**：mod 分叉过的界面文件（frontendmainview.gui / frontendgamesetupview.gui / topbar.gui / nationalfocusview.gui / countrypoliticsview.* / countrydiplomacyview.gui / countrytechtreeview.gui / credits.txt 等）都带"旧副本"属性 — 每次游戏大版本更新后照上表巡一遍。
'''

fp = os.path.join(SK, 'references', 'version-adapt.md')
t = io.open(fp, 'rb').read().decode('utf-8-sig')
if 'interface/ 旧副本致 UI 缺陷' not in t:
    t = t.rstrip('\r\n') + '\n' + ADD + '\n'
io.open(fp, 'wb').write(t.encode('utf-8'))
print('version-adapt.md 追加 ✓')

s = io.open(os.path.join(SK, 'SKILL.md'), 'rb').read().decode('utf-8-sig')
s = s.replace('version: 2.20', 'version: 2.21').replace('版本：v2.20', '版本：v2.21').replace('当前版本 **v2.20**', '当前版本 **v2.21**')
io.open(os.path.join(SK, 'SKILL.md'), 'wb').write(s.encode('utf-8'))
for f in ('SKILL.md', 'references/version-adapt.md'):
    shutil.copy2(os.path.join(SK, f.replace('/', os.sep)), os.path.join(CL, f.replace('/', os.sep)))
print('skill v2.21 + .claude 同步 ✓')

M = r'C:\Users\LR\.zcode\cli\memories\projects\ilyich-genshin-test-version-57bab93f04048e34\memory\gamma-mod-progress.md'
mt = io.open(M, 'rb').read().decode('utf-8-sig')
add = '''
## 10-17 三个 UI bug（全修，日志归零）
- **选国界面**（国家顺序乱）：`frontendgamesetupview.gui` 旧副本缺 `filters/more_countries/new_content/country_name` + 笔误 `GFX country filter_entry` → 已从原版补块、修笔误、补 `GFX_country_filter_entry` sprite（frontendgamesetupview.gfx）。
- **主菜单社媒图标**（按用户要求不新增按钮）：真因 = `core.gfx` 旧副本缺 `x`（X 图标）等 8 sprite → 已补；我一度新增的 7 个社媒元素已回退（用 Beta 版同名文件恢复）。
- **主菜单左下角 DLC 图标列**：`frontendmainview.gfx` 旧副本缺 `GFX_frontend_banner_dlc051/052`、`GFX_frontend_medal_dlc051` → 已补（dlc052 = Thunder at Our Gates，游戏侧本就 Active ✓）。
- 终验：`Could not find sprite type` / `Could not find "..." in window` / MAP_ERROR / invalid state 全 **0** ✓。其它仍属旧副本、本次未动的界面文件：frontendmainview.gui（社交行结构为旧版）、topbar.gui、nationalfocusview.gui、countrypoliticsview.gui/.gfx、countrydiplomacyview.gui、countrytechtreeview.gui、credits.txt —— 建议后续整轮 version-adapt。
- 备份：`.backups/ui_20261017_000603`、`ui_last`/`prebeta_*`（frontendmainview.gui 已用 Beta 版恢复）。skill v2.21 记入 version-adapt.md。
'''
if '10-17 三个 UI bug' not in mt:
    mt = mt.rstrip('\r\n') + '\n' + add + '\n'
io.open(M, 'wb').write(mt.encode('utf-8'))
print('记忆 ✓')
