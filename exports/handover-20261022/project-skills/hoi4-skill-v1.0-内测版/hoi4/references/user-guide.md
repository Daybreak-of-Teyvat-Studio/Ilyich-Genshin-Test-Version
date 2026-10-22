# HOI4 Skill 用户指引（AI 引导手册）

**本文件的读者是 AI**：用户说「我要制作一个钢铁雄心4的某某 mod」或任何 mod 制作诉求时，
按本手册引导。目标：**3 轮对话内让用户进入实际制作**，不让用户在配置和术语里迷路。

---

## 第 0 步：环境自检（每次会话必做，静默完成，不刷屏）

1. 读 skill 目录下 `config.json`（含 `hoi4_root` 游戏根目录、`mod_root` mod 工作目录）
2. **不存在** → 走下面的【首次使用向导】
3. **存在** → 静默验证：
   - 游戏根目录下有 `launcher-settings.json` 或 `hoi4.exe`
   - `mod_root` 目录存在
4. 验证失败 → 只说一句「检测到之前的游戏目录已失效，重新确认一下」然后重问那一项
5. 全部通过 → 直接进入【任务分流】，**不要复述配置**

---

## 首次使用向导（对话脚本）

**开始前先告诉用户**（一次性说明，不阻塞配置流程）：

```text
💡 想达到最佳效果，推荐先安装两个配套项目：
   · superpowers-zh（技能框架）—— 安装命令：npx superpowers-zh
   · rhoiscribe-hoi4（HOI4 本地 mod 开发资源包） —— https://github.com/czxieddan/RHoiScribe
   不装也完全能用，装了体验更完整。
```

一次只问一件事，每问都给**常见默认值**让用户可以直接回车/复制：，每问都给**常见默认值**让用户可以直接回车/复制：

### 第 1 问 · 游戏根目录

```text
开始前先确认两个目录（一次配置，之后一直生效）。

1️⃣ 钢铁雄心4装在哪？（游戏根目录，不是创意工坊目录）
   常见位置：
   · Steam 默认：C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV
   · 找法：Steam 库 → 右键游戏 → 管理 → 浏览本地文件

   直接把文件夹路径粘贴给我即可。
```

**验证**：目录下有 `hoi4.exe` / `launcher-settings.json` / `common\` 三者之一即可。
**失败回应**：「这个目录里没找到 hoi4.exe——可能是选到了 Steam 库的根目录或 workshop 目录，再确认一下？」

### 第 2 问 · mod 工作目录

```text
2️⃣ mod 放在哪个目录？
   常见位置：C:\Users\<你>\Documents\Paradox Interactive\Hearts of Iron IV\mod

   · 从零做新 mod → 给我这个目录就行，mod 名后面一起定
   · 改已有的 mod → 直接把那个 mod 的文件夹路径给我
```

**验证**：目录存在。若用户给的是已有 mod 的路径，顺手读它的 `descriptor.mod`
记下 name/path/version，在下一问里展示「已识别到 mod：XX」。

### 第 3 问 · 确认 + 任务意向

```text
✅ 配置完成：
   游戏根目录：<...>
   mod 目录：<...>

   接下来想做什么？直接一句话就行，比如：
   · 「我要制作一个钢铁雄心4的原神 mod」
   · 「给这个 mod 加一个新国家」
   · 「做一个新国策树」
   · 「地图上加几个岛」
   · 「进了游戏就闪退，帮我看看」

   你说完我会先列出这件事要做的全部工作（组成清单 + 顺序 + 怎么验收），
   你确认后我再动手。
```

**写入 config.json** 后提示已保存，以后不再问。

---

## 任务分流（用户的话 → 场景 → 路线）

| 用户说（举例） | 场景 | 第一步动作 |
|---|---|---|
| 「我要制作一个钢铁雄心4的XX mod」 | **A 从零建 mod** | 场景 A 流程 |
| 「给XX mod加新国家 / 新国策树 / 新单位…」 | **B 现有 mod 加内容** | 报路线图 |
| 「改地图 / 挪省 / 州重排 / 加海岛」 | **C 地图与州** | 读 `map-data.md`、`gamma-pipeline.md` |
| 「闪退 / 报错 / 进不去」 | **D 排查** | 读最新 crash 转储 + `logs/error.log` 尾部 |
| 「汉化 / 改名 / 加本地化」 | **E 本地化** | BOM 规矩（`gamma-pipeline.md`） |
| 「改地形 / 加胜利点 / 州改名」 | **C 的子项** | `gamma-pipeline.md` 对应节 |

### 场景 A：从零做新 mod（引导脚本）

```text
好，做一个「XX」mod。我建议按这个顺序搭骨架：

第 1 步  建 mod 骨架（我来）：
         mod 文件夹 + descriptor.mod + 空目录结构 + 本地化文件壳
         —— 做完就能在启动器里看到并勾选这个 mod
第 2 步  定核心设定（需要你）：
         · 改编自什么（历史/架空/跨作品）？
         · 玩什么（国家扮演？战争？种田？）
         · 有多少个国家 / 从哪年开始？
第 3 步  按组成逐个立项（每项我会给「组成清单+顺序+验收」）：
         常见组成：新国家 → 国策树 → 角色 → 事件 → 本地化 → 地图/州（可选）
第 4 步  每完成一项 → 进游戏验证一次（我给验证点）

先告诉我第 2 步的三个问题，或者直接说「先搭骨架」我就开工。
```

**骨架内容**（场景 A 第 1 步的实际操作）：
- `<mod_name>/descriptor.mod`：`name`、`path`、`supported_version`、`tags`
- mod 目录旁的 `<mod_name>.mod` 指针文件（launches 需要）
- 目录：`common/`、`history/`、`localisation/simp_chinese/`、`gfx/`、`interface/`（按需增）
- 本地化壳：`l_simp_chinese:` 首行 + **BOM**（没有 BOM 整个文件失效）

### 场景 B：现有 mod 加内容（引导脚本）

```text
收到。先让我看一下这个 mod 的现状（已有哪些文件、用的什么结构），然后
给你列「新国家 / 新国策树 / …」的组成清单和制作顺序，你确认后开工。
```

动作：读 mod 的 `common/` `history/` `localisation/` 结构 → 查 `task-roadmaps.md`
对应节 → **输出路线图等确认**。路线图格式：

```text
【新国家】要做的事（按顺序）：
 1. common/country_tags/  — 国家 tag（3 字母）   ← 一切的前提
 2. history/countries/    — 国家历史（政体、首都、军队）
 3. common/national_focus/— 国策树（可选）
 4. common/ideas/         — 民族精神（可选）
 5. localisation/         — 中文名（tag、国策、精神全部要）
 验收：开局选到这个国家、名字显示正确、不闪退
确认后我按 1→5 做。
```

### 场景 D：崩溃排查（引导脚本）

```text
发我崩溃时间点就行（或者什么都不用发），我去读最新的崩溃转储和 error.log。
另外告诉一下：是点启动就崩、进加载界面崩、还是选国家后崩？这决定先查哪层。
```

动作：`crashes\hoi4_最新\exception.txt` + `logs\error.log` 尾部 → 分类定位
（地图数据 / 州语法 / 本地化 / interface）→ 给出修复。

---

## 制作过程中的引导规矩

1. **每次只推进一层**：路线图确认 → 做第 1 项 → 汇报+验收点 → 用户点头 → 第 2 项。
   不要一口气做完全部组成。
2. **每个完成的产出都有「进游戏验证点」**：告诉用户怎么看效果（开局界面/某个国家/某个按钮）。
3. **需要用户决定的事列成清单**（国名、tag、首都、领土范围），给默认建议让用户改——
   别让用户从零想，也别自作主张。
4. **tab 缩进、BOM、CRLF、原版文件只读** 这些铁律对用户透明地执行，不用反复解释。
5. 用户给的数字（省号/州号/值）**双读核对**后动手，对不上就问。
6. 大改动（转省、地形、补号）一律先干跑 `--dry`，把结果给用户过目再落地。

---

## 常见一句话任务速查（AI 动作表）

| 用户说 | AI 做 | 读什么 |
|---|---|---|
| 做个新 mod | 场景 A 骨架 + 核心设定三问 | 本文件 |
| 新国家 | 路线图：tag→history→focus→ideas→本地化 | `task-roadmaps.md` |
| 新国策树 | 路线图：folders→focus 树→本地化+图标 | `task-roadmaps.md` |
| 新单位/装备 | categories→equipment→stat keys | `stat-keys.md`、`icons-dds.md` |
| 新学说 | 主/子学说教程 | 两个 doctrine 教程 |
| 新事件/决议/角色/法案/MIO/BOP/特质/编制/建筑/战术卡 | 路线图 | `task-roadmaps.md` |
| 挪省/改州归属/州重排 | 工具链 + 语法关 | `map-data.md` |
| 均分州/海州/州名/VP/地形/补号 | Gamma 流水线 | `gamma-pipeline.md` |
| 建筑悬空/穿模 | 高程重算+防穿模 | `buildings-height.md` |
| 闪退 | 崩溃分流 | 本文件场景 D |
| 本地化/汉化 | BOM+CRLF 规矩 | `gamma-pipeline.md` |
| 适配游戏新版本 | stale override | `version-adapt.md` |
| 改了州/省之后 | State 自检（`scripts/check_states.py --mod <mod>`），AI 主动提示 | 本文件·引导规矩 |

---

## 新手常见误区（用户问到就解释）

- 「mod 放 workshop 目录行不行」→ 不行，自己的 mod 放 Documents 的 mod 目录
- 「为什么改了没生效」→ 启动器里勾选 mod / 本地化缺 BOM / 缓存（`Documents\...\hearts_of_iron_iv\` 下 gtfe 之类缓存可删）
- 「游戏更新后 mod 坏了」→ 版本适配（stale override 重建）
- 「我改了原版文件」→ 游戏根目录永远只读，改 mod 副本
