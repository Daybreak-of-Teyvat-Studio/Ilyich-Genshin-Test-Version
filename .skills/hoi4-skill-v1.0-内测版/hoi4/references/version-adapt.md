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
