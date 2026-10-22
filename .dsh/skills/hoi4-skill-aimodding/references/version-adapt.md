# 版本适配（adapt to latest version）

**核心机制**：mod 文件与基础游戏文件**同相对路径即整体覆盖**（不是合并）。旧 mod 覆盖基础文件后，基础游戏 1.19 新增内容会被整个丢弃（stale override）。

## 流程

1. **shadow 检测**：Glob 列出 mod 全部文件，逐一对照基座游戏（`F:\Steam\steamapps\common\Hearts of Iron IV`，只读）是否有同名文件。
2. 对每个 stale override：复制基础游戏当前版本文件覆盖 mod 旧副本，再把 mod 独有内容**原样插回**。
3. 无独有内容的 stale override（如纯旧版 `00_buildings.txt`）直接删，让基础文件生效。
4. 有独有内容：先 grep 定位（如 `##RED ALERT##` 标记），再用**字面量 `.Replace()`**（非正则）在**已验证唯一锚点**处插回。

## 编码安全 IO（PowerShell 5.1）

```powershell
$enc = New-Object System.Text.UTF8Encoding($false)   # UTF-8 无 BOM
$c = [System.IO.File]::ReadAllText($p)                 # 读（自动 BOM 检测）
$c = $c.Replace("旧串", "新串")                          # 字面量，非正则
[System.IO.File]::WriteAllText($p, $c, $enc)           # 写，无 BOM

# 插多行块：检测行尾 + tab 转义
$nl = if ($c -match "`r`n") { "`r`n" } else { "`n" }
$t = "`t"

# 校验缩进：把 tab 替换成 <T> 观察
$c.Replace("`t", "<T>")
```

- 基础文件均为 UTF-8 无 BOM、LF 行尾；中文经 PowerShell 往返无损。

## 校验

锚点唯一 + 字节级验证；缩进检查（见上面 tab→`<T>` 技巧）；插块后花括号平衡（`{` 数 = `}` 数）+ Grep/Read 复核。

## 常见内容 bug（适配时发现）

- 装备变体 `parent = <自身>`（自引用）——第一级变体 `parent` 应指向 archetype。
- `original_tag = AND` —— `AND` 是触发器逻辑关键字不是 tag，多半是 `TAH` 写错。
- 兵牌 sprite：大图 `GFX_unit_X_icon_medium`、小图 `GFX_unit_X_icon_medium_white`（别漏 `_white`）。
- 国策 `id` 可用中文（`id = 苏联基地车`），游戏把 id 直接当显示文本，无需本地化——见中文 id 别误判为 bug。
- **学说系统重构（1.19）**：旧 `set_technology = { mobile_warfare = 1 }` 失效，改 `set_grand_doctrine = <id>`。id 校验位置 `common/doctrines/grand_doctrines/*.txt`：陆 `new_mobile_warfare`/`superior_firepower`/`grand_battleplan`/`mass_assault`（仅 mobile_warfare 有 `new_` 前缀）；海 `new_fleet_in_being`/`new_convoy_raiding`/`new_base_strike`；空 `new_strategic_destruction`/`new_battlefield_support`/`new_operational_integrity`。
- **空军装备枚举改名 airframe 原型（1.19）**：旧 `fighter_equipment`/`CAS_equipment`/`nav_bomber_equipment`/`tac_bomber_equipment`/`heavy_fighter_equipment`/`strat_bomber_equipment`/`scout_plane_equipment`（及 `cv_*`）→ `small_plane_airframe`/`small_plane_cas_airframe`/`small_plane_naval_bomber_airframe`/`medium_plane_airframe`/`medium_plane_fighter_airframe`/`medium_plane_scout_plane_airframe`/`large_plane_airframe`（各带 `cv_` 舰载版）。jet 类（`jet_fighter_equipment`/`jet_tac_bomber_equipment`/`jet_strat_bomber_equipment`）仍有效。
- 空军 sub_unit 必填 `land_air_wing_size = 100`（否则报 "must have a positive non-zero 'land_air_wing_size'"）。
- 装备 `carrier_capable` 在 archetype 与 subtype 之间必须一致，否则报 "must not change its 'carrier_capable' value inherited from its archetype"。
- **旗帜尺寸**：主 82x52 / 中 41x26 / 小 **10x7**（11x7 报 "Unexpected texture dimensions"）。命名：tag 用 `<TAG>_<ideology>.tga`；化妆 tag 用 `<cosmetic_tag>_<ideology>.tga`（ideology 用父级 key：communism/democratic/fascism/neutrality）。
- 自定义科技树文件夹 GUI 项需含 `iconType { name = "can_assign_design_team_icon" ... }`，否则报 "Could not find can_assign_design_team_icon"。

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

**⚠ 实测警示（同日回退）**：上表"选国界面补元素"的做法在实测中被证明有害——该 mod 的 setup 界面是深度改版布局，把原版元素块（含原版坐标）直接插入同名父窗口会让整个页面乱掉，已回退。**结论：分叉过的 .gui 不做"补块"，只可逐个元素做可视验证的微调；无法验证就不动。** sprite（.gfx）层面的补充相对安全（不影响布局），但 DLC 图标列的"未启用"状态不吃 banner sprite，补齐后显示无变化——不要把它当解决方案。

