# 子学说教程（修正版）

> **制作者：猫妖**（原教程），经对照原版 1.19.3 `common/doctrines/subdoctrines/land/infantry_subdoctrines.txt` 校验修订（修正处标 ⚠️【修正】；初版曾误判 mastery 机制，经群友反馈与原版 grand_doctrines 复核后已改正）。

## 学说体系四层结构（⚠️【修正·新增】原教程只讲子学说一层）

```
common/doctrines/
  folders/          大类：land / air / sea / special_forces
  grand_doctrines/  大学说（互斥的根，耗经验解锁）
  tracks/           轨道：每轨道一个子学说槽 + 里程碑
  subdoctrines/     子学说 + rewards 掌握度奖励   ← 本教程
```
给已有轨道挂新子学说只需写 subdoctrines 一层；新建轨道/大学说才动上三层。

## 子学说模板

```
XXXX = {                       # 子学说 ID = 全游戏唯一标识
    track = infantry           # track = 挂载轨道 = 决定子学说出现在哪个栏目
                               # 陆军: infantry/combat_support/armor/operations
                               # 海军: submarines/screens/capital_ships/carriers
                               # 空军: fighter_aircraft/strike_aircraft/medium_aircraft/heavy_aircraft
    name = XXXX                # name = 名称本地化 key = 界面上显示的名字
    description = XXXX         # description = 描述本地化 key = 界面悬停显示
    icon = GFX_XXX             # icon = 图标名 = 界面图标；需在 interface/*.gfx 注册贴图

    xp_cost = XXX              # xp_cost = 解锁消耗 = 花多少点经验激活本学说
    xp_type = army             # xp_type = 经验类型 = army（navy/air 同理）

    # ============ available = 子学说解锁条件 ============
    available = {
        has_dlc = "No Compromise, No Surrender"   # 拥有不妥协 DLC
        tag = TAG
    }

    # ============ visible = 子学说显示条件 ============
    visible = {
        has_dlc = "No Compromise, No Surrender"
        tag = TAG
    }

    # ============ ai_will_do = AI 选择倾向 ============
    ai_will_do = {
        base = 1                    # 基础权重
        modifier = {
            factor = 95             # 权重 ×95
            tag = TAG               # 条件：什么国家的 AI
        }
    }

    # ============ 掌握度来源声明（⚠️【修正·新增】原教程缺失）============
    # 可选：声明本子学说吸收哪些单位类别的战斗掌握度
    mastery = {
        categories = {
            category_cavalry
            category_all_infantry
        }
    }

    # ============ 激活效果 = 解锁后【立刻】生效 ============
    # ⚠️【修正】原教程一律写顶层——实际分两类（原版两种都出现）：
    #   · 直接写顶层：师修饰符块 category_xxx = {...}、
    #     国家级修正（如 unit_cavalry_design_cost_factor = -1）、
    #     enable_tactic = <战术>（解锁战术卡）
    #   · 必须包在 effect = { ... } 里：add_tech_bonus 等【普通效果】
    #     （原版 mobile_infantry：effect = { add_tech_bonus = {...} }）

    category_all_infantry = {      # 师修饰符：作用于该类别所有单位
        soft_attack = 0.30
        hard_attack = 0.30
        defense = 0.30
        breakthrough = 0.10
    }

    experience_gain_army_unit_factor = 0.05   # 国家级修正：直接写顶层

    effect = {                                 # 普通效果：必须包 effect
        add_tech_bonus = {
            bonus = 0.5
            uses = 1
            category = motorized_equipment     # category key 查附录 unit-categories-参考
            name = XXXX
        }
    }

    # ============ rewards = 掌握度奖励 = 解锁后随掌握度逐层生效 ============
    # 精通度（mastery）随时间/行动积累（add_daily_mastery / add_mastery 等来源），
    # rewards 各条目按声明顺序解锁；mastery 的两种写法等价：
    #   · 每层写相同值（增量）：mastery = 100 × 5 层
    #   · 写递增累计值：mastery = 100 / 200 / 300 / 400 / 500
    # 数值自定义（原版常见每层 50）；字段可省略（原版 mobile_infantry，分布规则待确认）。
    # 结构：rewards = { 条目名 = { mastery = 阈值 ...加成 } }
    # 条目名 = 本地化 key（任意名），界面显示该层名字。

    rewards = {
        XXXX_reward_1 = {                # 第一层
            mastery = 100
            category_all_infantry = {    # 师修饰符写法同上
                soft_attack = 0.05
            }
            experience_gain_army_unit_factor = 0.05   # 也可写国家级修正
        }
        XXXX_reward_2 = {                # 第二层
            mastery = 100
        }
        XXXX_reward_3 = {                # 第三层
            mastery = 100
        }
        XXXX_reward_4 = {                # 第四层
            mastery = 100
        }
        XXXX_reward_5 = {                # 第五层
            mastery = 100
        }
    }
}
```

## 大学说模板（grand doctrine，⚠️【补充】原教程缺失，语法经原版 land_grand_doctrines.txt 校验）

```
new_mobile_warfare = {          # 大学说 ID
    folder = land               # 所属大类（land/air/sea/special_forces）
    name = GRAND_DOCTRINE_XXX
    description = GRAND_DOCTRINE_XXX_DESC
    icon = GFX_doctrine_xxx_medium
    available = { always = yes }
    xp_cost = 100
    xp_type = army
    ai_will_do = { base = 1  modifier = { factor = 0  is_major = no } }

    tracks = {                  # 本大学说包含哪些轨道（= 可选哪些子学说类型）
        infantry
        combat_support
        armor
        operations
    }

    # 激活效果：解锁立即生效，直接写顶层
    planning_speed = 0.20
    army_speed_factor = 0.10
    enable_tactic = tactic_unexpected_thrust

    milestones = {              # 轨道里程碑（匿名块列表，按轨道给额外奖励）
        {                       # Infantry 轨道
            org_loss_when_moving = -0.15
            land_reinforce_rate = 0.02
            enable_tactic = tactic_delay
            effect = { ... }
        }
        ...
    }
}
```

## category key 白名单

写 `category_xxx` 时查附录 **`unit-categories-参考.txt`**（已与原版 1.19.3 逐 key 校对 49/49 一致）。**该文件只作参考，不要放进 mod 的 `common/unit_tags/`**——放进去会覆盖原版类别定义。

## 验收

- `error.log` 无 doctrine 报错；`add_tech_bonus` 的 `category` 必须是合法 key（**写错报 `Unknown technology category`**）
- 进游戏学说界面：子学说可见（DLC 条件）、XP 消耗正确、解锁后修饰符生效、rewards 各层随掌握度解锁
