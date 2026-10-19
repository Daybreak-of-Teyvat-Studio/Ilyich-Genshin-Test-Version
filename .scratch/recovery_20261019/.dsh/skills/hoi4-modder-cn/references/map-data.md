# 地图数据一致性：省(province) ↔ 州(state)

**读这份的场景**：把省从一个州挪到另一个州；改州归属/核心；游戏进不去/进游戏闪退；`error.log` 出现 `not within specified state` / `coastal but has no port` / `no ... defined for state`。

## 铁律：省→州 的映射分散在多处，改一处必须同步另一处

| 文件 | 含"省→州"？ | 挪省时要改？ |
|---|---|---|
| `history/states/<id>-State_<id>.txt` | 是（`provinces = {...}`、省级建筑块、`victory_points`） | **要** |
| `map/buildings.txt` | **是**（每行第一列是州 id，省由坐标反查） | **要 —— 最容易漏，漏了就闪退** |
| `map/positions.txt` | 否（省 → 参考坐标） | 不用 |
| `map/strategicregions/*.txt` | 否（只列省） | 不用 |
| `map/definition.csv` | 否（省 → RGB / land-sea / 地形） | 不用 |
| `map/unitstacks.txt` | 否（首字段是省号，第二字段不是州） | 不用 |
| `map/cities.txt` / `railways.txt` / `supply_nodes.txt` | 否 | 不用 |

`history/states` 里跟着省走的三样：`provinces` 列表、省级建筑块 `<省id> = { ... }`（如 `naval_base`）、`victory_points = { <省id> <值> }`。三者必须一致，且胜利点所在省必须在本州 `provinces` 里。

## map/buildings.txt 格式与坐标约定

```
<州id>;<建筑类型>;<x>;<y>;<z>;<旋转>;<末列>
```

- **省号不是写死的，是由坐标反查出来的**：像素 `(x, 地图高度 - z)` —— Z 轴向上、位图 Y 向下，**Y 必须镜像**。
- **先验证轴向再用**：拿 `map/positions.txt` 里每个省自带的坐标去查 `provinces.bmp`，正确写法应 **100% 命中自身所在省**（本机实测 8021/8021）。用错轴向会全表对不上。
- 游戏加载时会校验：建筑坐标所在省必须属于第一列声明的州，否则 `BUILDING IGNORED!` 忽略该建筑。

## 两种建筑，处理方向相反 ⚠️

**判定方法**：统计每种建筑类型在**原始表**里"每州个数"是否恒定。恒定 = 州级；随省分布 = 随省走。

| 层级 | 类型 | 挪省时怎么处理 |
|---|---|---|
| **州级生成点**（每州数量恒定） | `air_base`、`fuel_silo`、`radar_station`、`nuclear_reactor_spawn`、`rocket_site_spawn`、`synthetic_refinery`、`stronghold_network`（各 1/州）、`anti_air_building`（3/州） | **留在原州**，把坐标挪到原州内另一个省（可取其 `positions.txt` 坐标）。跟着省走会让**原州丢掉生成点 → 闪退** |
| **随省走** | `naval_base_spawn`、`coastal_bunker`、`floating_harbor`、`naval_supply_hub`、`naval_headquarters`、`dockyard`、`bunker`、`supply_node`、`special_project_facility_spawn`、`arms_factory`、`industrial_complex` | 第一列改成**新州** |

## 崩溃症状 → 病因对照

| error.log 关键词 | 病因 | 修法 |
|---|---|---|
| `location is not within specified state ... BUILDING IGNORED!` | 第一列的州与坐标所在省不符 | 同步第一列 |
| `Province N is setup as coastal but has no port building. This will likely crash the game.` | 港口的 `naval_base_spawn` 被忽略 → 该省没港口 | 同步第一列（**这条会崩**） |
| `MAP_ERROR: no air base site / no rocket site / no gun emplacement defined for state N` | 该州的州级生成点被搬走了 | 生成点挪回原州（**这条会崩**） |
| 闪退但堆栈无符号（全是 `PHYSFS_*`） | 堆栈没用 | **看 `logs/error.log` 尾部**：崩溃前几秒的 `MAP_ERROR` / `buildings.txt error` 就是病因 |

**反查技巧**：`error.log` 里 `not within specified state` 的报错省号集合，应与你实际挪过的省集合**完全一致**；差集非空说明你的坐标解析和游戏不一致（先怀疑轴向/取整）。

## 正确流程

1. 改 `history/states/*.txt`：`provinces` 列表（保持升序）、跟着搬省级建筑块与 `victory_points`。
2. 同步 `map/buildings.txt`：州级生成点留在原州就地挪位置；其余改第一列。
3. **事后对"原始文件"验不变量**（这是唯一可靠的验收方式）：
   - 每种州级类型的**每州数量**与原始完全一致
   - **没有州缺任何州级生成点**
   - 行数不变、纯 CRLF、无 BOM、每行 7 字段
4. 边界情况：坐标落在省界 1px 外时，游戏可能仍判它在省内 → 按「建筑类型 + 原州 + 离该省最近」精确挑，并检查最近/次近距离差是否够大（>1.5 倍）以确认无歧义。
5. 改前备份原文件；改后复核字段变化形态（只该出现"改州列"和"州级生成点只挪坐标"两种）。

## 常见错误

- ❌ **只改 state 文件、漏 `map/buildings.txt`** → 港口被忽略 → `coastal but has no port` → 闪退。
- ❌ **把所有条目都跟着省改到新州** → 原州丢生成点 → `no air base site for state N` → 闪退。
- ❌ **用错坐标轴向**（把 `(x, z)` 当像素，忘记 Y 镜像）→ 全表对不上，还以为是数据错。**先用 positions.txt 验证**。
- ❌ **不验不变量**，只看着改完就交 → 问题留到启动时才炸，且崩点可能在选国家界面甚至更早。
- ❌ 把 `map/buildings.txt` 里的海军类条目按"州级"处理 → 该省丢港口。海军类是**随省走**的。

## 改完必须过「语法关」——比语义检查更致命

实测教训：一次州重排把 667 个州文件写坏（重建 `buildings` 块时只删掉了省级块的**首行**，
把块内的 `naval_base = 2` 和收尾 `}` 留了下来），结果：

- `parser.cpp: unexpected token in "history/states/N-State_N.txt" ( } )` 403 条
- `statehistory.cpp: Unknown History Command ==>\'naval_base\'<==` 378 条
- `persistent.cpp: Unexpected token: victory_points` 301 条
- `MAP_ERROR: The land province N has no state.` **2116 条**（解析失败的州等于没有省）
- 游戏崩，且崩点与建筑/港口无关 —— **只看日志关键词会误判方向**

**离线验收必须包含（缺一不可）：**

1. 每个文件 `{` 与 `}` 计数相等
2. `buildings` 块内**只允许**两种行：州级 `\t\t\t<小写key> = <值>`，或完整的省级子块
   `\t\t\t<省id> = {` … `\t\t\t}` —— 用**花括号配对**剥离，不要用正则只删首行
3. `victory_points` 里的省必须都在本州 `provinces` 里，且该行不重复出现
4. `owner` 恰好一行、`add_core_of` 与之一致
5. `provinces` 非空、**无重复归属**（一个省只能属于一个州）
6. 行首无空格、纯 CRLF、无 BOM

**重排/搬迁类工具的必备设计**：写盘后立刻跑上面的自检并**失败即报**。另外要防三类丢省 ——
受保护/未参与重排的州也必须写盘（否则移进它的省会消失）、`definition.csv` 里有但位图无像素的省
（`npx == 0`）不能被过滤掉、写盘前后各扫一遍「无归属省」做兜底。
