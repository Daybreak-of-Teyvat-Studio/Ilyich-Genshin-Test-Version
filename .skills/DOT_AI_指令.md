我要你阅读文件DOT_HOI4_Modding_Skills，对BUG进行修复，而不是偷懒把有问题的代码注释掉。

对照error日志，将所有Event、focus、ideas decison effect modifier trigger、on action的错误效果改成正确效果，不知道怎么修正的就用#注销，并#备注原因

优化所有采用create_country_leader = { create_field_marshal = { create_corps_commander = { create_navy_leader = {的国家，将之改为Daybreak of Teyvat Beta Version\common\characters中的形式，并为history countries添加招募代码。
大头像large可以用原来的图片，找不到小头像small的一律使用这个图片small="gfx/interface/cabinet/Ying.dds"

Missing icon for focus 的focus就为之添加icon = GFX_goal_unknown #。
Missing icon shine for focus的focus就按下面的方案将图片路径复制一遍。就像这样，普通icon和shine icon用的是同一张图片。你只需要在没有shine icon的普通icon的定位下面加一条shine icon的代码即可。
SpriteType = {
    name = "GFX_FOD_Press_the_Fatui"
    texturefile = "gfx/interface/goals/FOD/GFX_FOD_Press_the_Fatui.png"
}

SpriteType = {
    name = "GFX_FOD_Press_the_Fatui_shine"
    texturefile = "gfx/interface/goals/FOD/GFX_FOD_Press_the_Fatui.png"
    effectFile = "gfx/FX/buttonstate.lua"
    animation = {
        animationmaskfile = "gfx/interface/goals/FOD/GFX_FOD_Press_the_Fatui.png"
        animationtexturefile = "gfx/interface/goals/shine_overlay.dds"
        animationrotation = -90.0
        animationlooping = no
        animationtime = 0.75
        animationdelay = 0
        animationblendmode = "add"
        animationtype = "scrolling"
        animationrotationoffset = { x = 0.0 y = 0.0 }
        animationtexturescale = { x = 1.0 y = 1.0 }
    }
    animation = {
        animationmaskfile = "GFX_FOD_Press_the_Fatui.png"
        animationtexturefile = "gfx/interface/goals/shine_overlay.dds"
        animationrotation = 90.0
        animationlooping = no
        animationtime = 0.75
        animationdelay = 0
        animationblendmode = "add"
        animationtype = "scrolling"
        animationrotationoffset = { x = 0.0 y = 0.0 }
        animationtexturescale = { x = 1.0 y = 1.0 }
    }
    legacy_lazy_load = no
}

---

# 内容实装铁律（2026-10-16 起，新增剧本一律照办）

## 一、产物必须并入同名文件，不许另起一套

一个新剧本产生的事件、新闻、命名空间、民族精神、决议、决议类别、动态修正、脚本效果、on_actions、本地化，
全部并入该国已有的同名文件，不要新建 `XXX_YYY_events.txt` 这类第二套文件：

| 内容 | 落点 |
|---|---|
| 事件 | `events/<国>_events.txt`（内部事件与新闻同文件） |
| 命名空间 | `events/<国>_namespace.txt` |
| 民族精神 | `common/ideas/<国>_ideas.txt`，插进 `ideas = { country = { … } }` 内层 |
| 决议 | `common/decisions/<国>_decisions.txt` |
| 决议类别 | `common/decisions/categories/<国>_categories.txt`（顶层块名必须等于类别 id） |
| 动态修正 | `common/dynamic_modifiers/<国>_dynamic_modifiers.txt` |
| 脚本效果 | `common/scripted_effects/<国>_effects.txt` |
| 挂载 | `common/on_actions/<国>_on_actions.txt`，只保留一个 `on_actions = { }`，各条写进同一 `on_startup` / `on_monthly` |
| 本地化 | `localisation/simp_chinese/<国>_l_simp_chinese.yml`，BOM + CRLF |

生成器负责产出「片段」，由主生成器读片段拼接；片段文件本身不下发到 MOD。

## 一之二、国策树：一个 tag 组只写一棵 `focus_tree`

**同一个国家绝不要写两棵 `focus_tree`。** 多棵树同时命中一个国家时，HOI4 按评分**择一显示**，
不是并列——写在后面的那几棵等于没实装（本仓踩过：四个 `focus_tree` 只看到雨林那棵）。

正确做法（照 `LYY_Neo_Focus.txt` 的写法）：

```
focus_tree = {
    id = <主 id>
    country = {
        factor = 0
        modifier = { add = 100   or = { tag = SUM  tag = SGD  tag = SDH  tag = SGS } }
    }
    default = no
    continuous_focus_position = { x = ... y = ... }
    # 各派/各国靠绝对 x 分块，块之间用横幅注释隔开：
    #   # ======== <TAG> 国策（<中文名>，排在…右侧）======== … # ======== <TAG> 国策 END ========
}
```

- 想让「B 的国策排在 A 右边」，就是**在同一棵树里**把 B 的整块绝对 x 平移到 A 的最右侧之外，
  不是再开一棵树、也不是把它排到下面。
- 平移整块：把偏移量加进该块**根节点**的绝对 x，相对坐标的 delta 自然抵消。
- **每一个块内、每一个节点的 `available` 都要用 `tag = <归属 tag>` 限定归属**，包括「主国」那一块。
  只给新加的块加、主块留 `available = { always = yes }` 是最常见的漏法 —— 结果是别的 tag 能点主国的国策，
  连带把主国的机制初始化、变量、档位修正全搅进别国（本仓 2026-10-16 踩过：雨林 324 个 focus 全是
  `always = yes`，SGD 可以点须弥的序章）。
- 触发器一律**小写 `tag`**（`tag = SUM`）。大写 `TAG =` 虽被解析器容忍，但不要用，统一小写。
- 自检：`focus_tree` 出现次数 == 1；全文 `available = { always = yes }` 出现 **0** 次；
  每个块的 `tag = <TAG>` 计数 == 该块 `focus = {` 计数；各块绝对 x 区间两两不交且按预期从左到右；同层横坐标间距 ≥ 2。

## 二、新闻一律由国策或事件触发

新闻不得按日期批量发射。不要写「`X_News_Begin` 宏 → 一次性挂 10 条 `days = 10/40/70…`」这种发射器。
正确做法：给每条新闻指定一个（或一组互斥的）里程碑国策，在该国策的 `completion_reward` 里写
`news_event = { id = <新闻命名空间>.<序号> days = 1 }`。
一组里放多个国策时，这些国策必须互斥，否则同一条新闻会被重复触发。
挂完后自查：每条新闻都能在国策树里找到触发点；脚本效果库内不再存在 `*_News_Begin`。

## 三、文案口径

- 破折号一律不用（`——` `–` `―` `─` `－` 全禁），遇到就换成逗号或句号。
- 事件 desc 与新闻 desc 都是 **200-400 字**（按去空白字符数计）。
- 文风照 `.skills/Darwin Skills.md` 的十条规则：去虚假对比、去对称排比、去套话开场、去会议式编号、去黑话与情绪标签、
  去无分级「最」字、动词优先、平等语气、少用引号、事实数据专名不动。
- 只改风格，不改事实、数据、专有名词。
- 改完用校验脚本回扫：desc 越界 0、破折号 0、键数不变、BOM+CRLF 不变。

## 四、跨表全局 id 必须带层别前缀

变量、动态修正、精神、决议、决议类别、宏名在整包里是同一张全局表，重名会静默覆盖。
同一国家多个剧本层（如内战 / 战后、雨林 / 沙漠）必须用层别标记区分。

## 五、生成器是权威，MOD 是现状

手改了 MOD 文件，就必须把生成器回填到同样的写法，否则下一轮重生成会把删掉的东西原样吐回来。
本仓踩过的实例：MOD 里的新闻发射宏是手改掉的，而 `cw_engine.py` / `san_pw_engine.py` 还在往外写。

- 回填时**以 MOD 实物为准**，把锚点表用只读脚本从 MOD 里抽出来存成数据模块，再让生成器读它。
- 生成器顶部若已失效（输出路径早被合并掉），写一行醒目告示，别让人直接重跑造出已删除的平行文件。
- 生成器的 `main()` 一律放进 `if __name__ == "__main__"`，保证导入不写盘，方便写体检脚本。

## 六、校验器本身也会过期

- 把独立文件并入同名文件后，「数顶层块」这类正则会把既有内容一起数进去。
  计数断言必须限定层别前缀（`^\t(SAN_PW_\w+) = \{`），或从整个目录收集。
- 「id 冲突」扫描原先按旧文件名排除自身；文件改名后它会拿自己和自己比，要按绝对路径排除。
- 判某事「非法」之前先回原版 grep 一遍。`vanilla_modifiers.json` 这类白名单会漏收，
  漏收会被误报成 MOD 的错误。
- 布局类断言要对着真正的判据写：关心的是「不重叠」，那就是「无重复绝对坐标 + 同层横坐标间距 ≥ 2」，
  不是「必须待在某个名义方块里」。

## 七、`on_actions`：内容必须包在 `effect = { }` 里

```hoi4
on_actions = {
    on_startup = {
        effect = {                        # ← 没有这一层，整份文件解析失败
            every_country = { limit = { tag = SUM }  SUM_Neo_Init = yes }
        }
    }
    on_monthly = { effect = { … } }
}
```

裸写 `every_country` 会报 `Unexpected token: every_country`，并且**整份文件作废**——
后面所有钩子一起失效，而且是静默的（游戏照常启动，只是机制没初始化）。
自检：文件里 `effect = {` 的出现次数 ≥ 2；`error.log` 里没有 `Unexpected token`。

## 八、决议：新增决议必须「完成对应国策」才能点

每条新决议的 `available` 里都要有 `has_completed_focus = <门槛国策>`。
门槛要选**分叉点之前的通用国策**（序章支线根、独立宣言、树根），否则互斥路线会被锁死。

```hoi4
<决议 id> = {
    icon = ...
    visible   = { has_country_flag = <进入该剧本的旗标> }   # 没进剧本时连灰掉都不显示
    available = {
        has_completed_focus = <门槛国策>
        <其他条件>
    }
    ...
}
```

自检：遍历每条新决议，`has_completed_focus` 必须在它的块内；门槛 id 必须是真实存在的国策。

## 九、机制修正：按国策分阶段赐予 + 只读面板

不要「开局把 14 个档位全挂上，靠各档 `enable` 内部互斥」。要写成三段式：

```
<M>_Init         = { hidden_effect = { 只置轴变量初值 + clamp;  <M>_Tier_Refresh = yes } }
<M>_Tier_Refresh = { hidden_effect = { <M>_RF_轴A = yes  <M>_RF_轴B = yes  <M>_RF_共振 = yes } }
<M>_RF_轴A      = { if = { limit = { has_variable = <轴变量> }
                      if/else_if 各档: if = { limit = { NOT = { has_country_flag <档>_At } } <档>_Set = yes } } }
<档>_Set        = { removeDM ×全部档; addDM ×本档; clr <档>_At ×全部; set_country_flag <档>_At }   # 先卸后挂
<M>_None        = { removeDM 共振档 ×N; clr 共振_At ×N }                                          # 仅共振组
<M>_A_Up_N / <M>_B_Up_N = { add_to_variable …;  custom_effect_tooltip = <轴变量>_Add_N }        # 轴宏：只改变量 + 可见说明，**不调 Tier_Refresh**
<M>_Sync         = { hidden_effect = { 变量丢了补初值;  <M>_Tier_Refresh = yes } }              # on_daily 保活
```

★ 轴宏**不得**调 `<M>_Tier_Refresh`（旧写法已废弃）。国策完成时只改变轴变量，档位由 `*_Sync` 在
`on_daily` 统一刷新（≤1 天延迟）。理由见第十二节「动修死规矩」。

**为什么必须这么写**：早期版本 `Tier_Refresh` 正文 **128 行**（14 卸 + 14 挂 + 条件），253 个国策
每次完成都把它整段展开进 tooltip（`add_dynamic_modifier`/`remove_dynamic_modifier` **是有 tooltip 的**），
并且每次都白跑 14 卸 14 挂。加「档位旗标卫兵」后，档位没变就是空转；正文压到 **7 行**且整体 `hidden_effect`。
旗标卫兵让刷新**幂等**，所以连写两次 `<M>_Tier_Refresh = yes` 等于一次，紧邻重复行应清掉。

**注意**：`*_Set` / `*_RF_*` 本身可以不再包 `hidden_effect`——它们只被 `Tier_Refresh` 的
`hidden_effect` 调用，属于**传递性静音**。但若某天有人直接从国策调 `*_Set`，就会漏 tooltip。

档位切换（`*_Tier_Refresh`）不再由国策直接触发，而是由 `*_Init`（开局一次）与 `*_Sync`（`on_daily`）驱动。
国策只管把轴变量推上去，`*_Sync` 次日把档位刷新到对应档 ⇒ 国策/决议几乎不碰 `dynamic_modifier`。

再配一个**只读**「机制状态」面板，把当前档位与生效修正显出来：

```hoi4
<M>_Mechanism = {                       # 顶层块名 == 类别 id
    <ID>_Tier_1_View = {
        allowed   = { tag = <TAG> }
        visible   = { <该档自身的 enable 条件> }   # 到档才出现
        available = { always = no }        # 永远点不动
        cost = 0
        fire_only_once = no
        complete_effect = { add_political_power = 0 }
    }
    …
}
```

描述文本由生成器把动修里的修正翻译成中文百分比；**整数位为 0 时要保留小数**（`-0.005` 要显示 `-0.50%`，
不能 `%+d%%` 截成 `+0%`）。漏译的键名要补进中文名表。

自检：`Init` 块内不再出现 `add_dynamic_modifier`；`Tier_Refresh` 存在且被 `Init` / `Sync` 调用；
面板条目数 == 档位数 + 共振态数；面板决议全部 `available = { always = no }`。

## 十、校验器要跟着版式一起改

改完架构（合并文件、合树、改门槛、改挂载方式）后，**旧断言会集体误报**。逐个核对：

- 断言「有几棵树 / 几棵块」的，改成新口径（如「`focus_tree` 出现次数 == 1」）。
- 比对相对坐标的，要先**解算成绝对坐标**再比；同时避开树头部的 `continuous_focus_position = { x = … }`
  （从 `BEGIN` 横幅之后再切）以及 `relative_position_id = <id>` 里的伪 `id = ` 匹配。
- 「id 冲突」要区分**定义**（`^\s*NAME = \{`）与**引用**（`has_completed_focus = NAME`），
  加了门槛之后引用会大量出现，按引用判会误报。
- 新闻计数要注意新闻可能已独立成 `events/<国>_news.txt`，且触发式样带 `days = 1`
  （正则用 `news_event = \{ id = <NS>\.\d+\b`，别写死 `}`）。

## 十一、Tooltip 卫生：机械效果一律 `hidden_effect`

玩家把鼠标停在国策/决议上时，HOI4 会把该效果块里**每个效果都展开成一行 tooltip**，
脚本效果会被整段插入。所以「一个 effect 带出一长串效果」会直接毁掉悬停体验。

**哪些效果有 tooltip（决定要不要藏）**

| 有 tooltip ⇒ 想藏才藏，或必须留 | 没有 tooltip ⇒ 藏了也没视觉变化 |
| --- | --- |
| `add_dynamic_modifier` / `remove_dynamic_modifier` | `add_to_variable` / `set_variable` / `clamp_variable` |
| `add_ideas` / `remove_ideas` / `add_timed_idea` | `set_country_flag` / `clr_country_flag` |
| `add_stability` / `add_war_support` / `add_political_power` | 各类 `*_Sync` / `*_Init` 内部状态同步 |
| `country_event` 之外的 `custom_effect_tooltip`（显式的） | — |

⇒ 真正会撑爆 tooltip 的是**动修**与**可见效果**，不是变量与旗标。
（反证：本 MOD 若要显示「火神恩情 +5」，必须另配 `custom_effect_tooltip = MVK-Prestige-Index_Add_5`，
变量本身不产生 tooltip。）

**统一规则**

1. 脚本效果里，凡是「机械链」——`*_Tier_Refresh` / `*_Sync` / `*_Init` 正文、
   连续 ≥2 行的变量/旗标段——正文一律裹一层 `hidden_effect = { … }`。
   ⚠ **轴宏 `<M>_A_Up_N` / `<M>_B_Up_N` 例外，不得整体包裹**：里面的轴指数变化是玩家要看的重要信息，
   必须留在包外并各配一行 `custom_effect_tooltip = <轴变量>_Add_<N>` / `_Decrease_<N>`（见第十二节）。
2. **`custom_effect_tooltip` 必须留在包外**，它是唯一给玩家看的说明。
   ⚠ 本 MOD 惯用**单行双效果**写法：`add_to_variable = { var = X value = 5 } custom_effect_tooltip = X_Add_5`
   ——这种行**不得进包**，写包裹器时要用「包体内是否出现 `custom_effect_tooltip`」做闸门。
3. 只在 `on_actions` 里被调用的效果**不必**包（on_action 不产生 tooltip），包了是零收益的改动。
4. 单行的 `set_country_flag` / 单行的 `add_to_variable` 也不必包——它们本来就没有 tooltip。

**做法（可复用脚本）**：`C:\Users\XIANGZIYUAN\hoi4lint\wrap_hidden_effects.py`
- R1「调用点」：在国策/决议/事件里找连续 ≥2 行的同类机械效果，就地包 `hidden_effect`（内容缩进 +1 tab），
  顺带删掉紧邻重复的同一行 `*_Tier_Refresh = yes`（幂等，重复无意义）。
- R2「效果体」：在 `common/scripted_effects/` 里，把**正文 100% 纯机械**（所有非空非注释行都是
  变量/旗标/`if|else_if|else|limit|AND|OR|NOT|check_variable|has_variable|random_list` 容器，
  且**不含**可见效果、原本没有 `hidden_effect`）的效果体整体包起来。
- 脚本幂等、`--apply` 门控、先备份到 `hoi4lint\_backup_hidden_<时间戳>\`；
  配套 `verify_wrap.py` 可在**内存里预演**并检查 `depth=0 / low=0 / 裸LF 未增 / 无 hidden 嵌套`。

自检：落盘后重跑一次脚本应报 **0 改动**；再跑一遍「包体内是否出现 `custom_effect_tooltip`」的检查，
新增包裹必须 **0 命中**（必要时拿备份核对，确认命中的都是**原有的** `hidden_effect`）。

## 十二、★动修死规矩 / 轴指数可见 / 备份位置（2026-10-16 深夜，用户口述）

### 12.1 ★ 死规矩：只有 ≤10% 的国策、决议可以改国家动态修正 `dynamic_modifier`

> 用户原话：「我说了，不要什么国策决议都去引用 effect，改国家修正。`sum_neo_focus` 的这个问题非常严重。
> 我定一个死规矩，只有 10% 的国策、决议可以改国家的动态修正 `dynamic_modifiers`。」

- **禁止**让几乎每个国策/决议的 `completion_reward` 一路展开到 `add_dynamic_modifier` / `remove_dynamic_modifier`。
- 正确链路：国策只推动**轴变量**（`add_to_variable` + `custom_effect_tooltip`）；档位修正由
  `*_Init`（开局）与 `*_Sync`（`on_daily`）驱动的 `*_Tier_Refresh` 统一挂/卸。
- 落地脚本：`audit_dm_refs.py`（审计引用率）、`cut_dm_from_focus_path.py`（删掉非白名单效果体里的
  `<M>_Tier_Refresh = yes` 并清理空 `hidden_effect`）。白名单＝效果体名以 `_Init`/`_Sync`/`_Tier_Refresh`/`_Set`/`_None` 结尾。
- 现状（本轮结果）：**56.1% → 0.4%**，剩 11 个都是「机制启用里程碑」国策。`on_actions` 同步频率
  已由 `on_monthly` 提到 `on_daily`，保证档位 ≤1 天刷新。
- **`common/ideas` 里的国家精神不在本规则内**（909 个 ≥4 修正块属正当写法）。

### 12.2 轴指数变化必须可见

> 用户原话：「`add_to_variable = { SUM-Oracle-Index = 25 }` 这类信息应该算重要信息，隐藏不太合适；
> 移除旧修正可以用 hidden_effect 加一句文字说明。」

- `add_to_variable` / `set_variable` **本身不产生 tooltip**，被 `hidden_effect` 包住就等于玩家看不到。
- 轴指数（`*-Index` 这类驱动变量）的 `add_to_variable` **必须提到 `hidden_effect` 外**，逐条补
  `custom_effect_tooltip = <轴变量>_Add_<N>` / `<轴变量>_Decrease_<N>`（作者惯例：加= `§G`，减= `§R`）。
- 「移除旧修正」这类机械尾巴可以留在 `hidden_effect` 内，但**要用一句 `custom_effect_tooltip` 说明**；
  `hidden_effect` 下信息量大时，至少留一行简短文字。
- 脚本：`fix_axis_tooltips.py`（提包外 + 生成键 + 追加 loc，幂等）。新增 loc 键仍须 **BOM + CRLF**。

### 12.3 一个决议里并列 4~9 条不同修正**不是**冗余

> 用户原话：「后面四条为什么要删掉呢，后面四条信息不算冗余吧，冗余只是各种过度引用的 `effect xxx = yes`。」

- 冗余＝**同一组修正被大量 `effect xxx = yes` 反复引用**；并列写 `war_support_factor`、
  `acclimatization_hot_climate_gain_factor`、`army_breakthrough_against_major_factor` 等多条**不同**修正是正当的，禁删。
- 因此在「收敛修正」上**不要自作主张合并**；`converge_modifiers.py` 已被否决并停用（顶部 `sys.exit(0)`）。

### 12.4 备份一律放在 MOD 目录之外

> 用户原话：「`.backup_nameloc_20261016_224634` 这类备份文件不要放 MOD 文件夹里面，会被重复读取。」

- 游戏会把 MOD 目录里**所有**文件当数据读，落在里面的 `*.backup_*` 会造成 loc 键重复、脚本重复。
- ⇒ 脚本生成的备份一律写 `C:\Users\XIANGZIYUAN\hoi4lint\_backup_*`，禁止落在 MOD 内。自检：MOD 内 `*.backup_*` 计数 == 0。

## 十三、机制状态并入「重要信息公示」+ loc 必须带 BOM（2026-10-17，用户口述）

> 用户原话：「把机制状态的信息也放到重要信息公示决议描述里面。提高重要信息公示决议组的优先级。
> LYY 天权凝光机制状态，应该在凝光完成第一个凝光派国策才显示。璃月也需要一个重要信息公示决议组。
> 纳塔决议的本地化 LOC 无法显示，可能是你改了纳塔 loc 的格式，修复。」
> 追加：「把机制状态的信息也放到重要信息公示决议描述里面之后，删除单独的机制状态信息显示决议组。」

### 13.1 ★ loc 文件必须带 UTF-8 BOM

- `localisation/**/*.yml` 只要含非 ASCII（中文），**必须**带 UTF-8 BOM（`EF BB BF`）。缺 BOM ⇒ 整份文件被
  HOI4 **静默丢弃**，症状是「某国决议/事件本地化**全空**」，**不是**个别键失效。
- 本轮根因：`NAT_Neo_Script_l_simp_chinese.yml` 是 `localisation/simp_chinese/` 共 114 个 loc 里
  **唯一缺 BOM** 的一个 ⇒ 纳塔决议 loc 全空。
- 自检脚本 `check_loc_bom.py`（`--fix` 可补、自动备份）；写 loc 的脚本一律强制前置 `\xef\xbb\xbf`。
- **别用裸 `\n` 往 CRLF 文件追加**（会造成混行），生成器用 `NL = "\r\n" if "\r\n" in t else "\n"`。

### 13.2 机制状态不再单开面板，改写入「重要信息公示」(Info_Board) 描述

- **旧态**：每套机制一个空类别 `*_mech_category`／`SAN_PW_Mechanism`，内含 14 条只读决议（2 轴×5 档 + 4 共振）。
  第五轮**全删 17 个**（LYY 12／SUM 4／SAN 1），不再有任何独立「机制状态显示决议组」。
- **新态**：Info_Board＝空类别（`visible_when_empty = yes` + `visible = { tag/旗标 }`，仿蒙德 `MOT_Important_Shows`，
  **不占任何决议位**）。机制状态写进其 `_desc`：

  ```
  §Y<轴名>（变量 <VAR>）：§![?<VAR>]
  §W[<轴>_tier_name]§!        ← 档位风格名（本轮新增）
  §G[<轴>_tier_mods]§!        ← 该档生效修正（原有）
  （第二轴同构）

  §Y共振：§!§W[<前缀>_Combo_combo_name]§!
  §G[<前缀>_Combo_combo_mods]§!
  ```

  无轴变量退 `DOT_Info_Board_NotStarted`，无共振退 `DOT_Info_Board_NoCombo`。
- **门槛**：`LYY_Info_Board`（凝光）加 `visible = { tag = LYY has_completed_focus = LYY_Tianquan_Eternal }`
  （完成第一个凝光派国策才显示）；其余五派按 tag 可见。璃月六派**内战各 1 个**新 Board。
- **优先级**：全部 17 个 `*_Info_Board` 升到 `priority = { base = 100 }`。
  ★注意类别优先级写法是 **`priority = { base = N }`**（**不是** `priority = N`，正则审计别写错）。
- **scripted-loc**：`common/scripted_localisation/<国>_Info_loc.txt`，新增三类 `defined_text` 块
  `<轴>_tier_name`／`<前缀>_Combo_combo_name`／`<前缀>_Combo_combo_mods`（原有 `<轴>_tier_mods`）。
  档位视图 loc 命名**各国不同**（LYY `LYY_Wealth_Tier_1_View`／SUM `SUM_Neo_Oracle_T1_View`／
  SAN `SAN_PW_Mandate_Tier_1_View`），写生成器前先核实每国的切片规则。
- 工具：`inv_info_boards.py`（只读盘点）、`build_info_boards.py`（生成器，`--apply`）、
  `check_info_boards.py`（desc↔scripted-loc↔loc 三向校验，忽略 `GFX_*` 精灵名噪声）。

### 13.3 改架构时同步改校验脚本

- 删旧面板后，`_civilwar/verify_requirements.py`、`_san/verify_san_pw.py` 里「断言面板存在」的检查会**假报红**。
  凡删/改被校验的架构，先搜脚本里对旧结构的断言，一并改成对新结构的断言（例：改为断言「旧类别已移除 +
  六派内战 Info_Board 齐全 + desc 含档位名/修正/共振名/共振修正」）。