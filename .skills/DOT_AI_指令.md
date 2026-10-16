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
<M>_Init         = { 只置轴变量初值 + clamp;  调 <M>_Tier_Refresh }
<M>_Tier_Refresh = { remove_dynamic_modifier × 全部档位;
                     按当前轴值 if/limit 只挂「唯一匹配的一档」+ 共振态 }
<M>_A_Up_N / <M>_B_Up_N = { add_to_variable …;  <M>_Tier_Refresh = yes }   # 轴宏
<M>_Sync         = { 变量丢了补初值;  <M>_Tier_Refresh = yes }              # 月度保活
```

轴宏只被国策的 `completion_reward` 调用 ⇒ 档位就是「按国策分阶段赐予」的。
少量直接改轴变量的地方，改完各跟一行 `<M>_Tier_Refresh = yes`。

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