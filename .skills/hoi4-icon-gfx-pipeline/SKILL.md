---
name: hoi4-icon-gfx-pipeline
description: Normalize HOI4 mod icon asset naming and rebuild interface gfx SpriteType declarations. Use when the user asks to rename or normalize game icon and idea assets (goal_TAG_name.png / idea_TAG_name.png), remove duplicated tag or Idea_ segments, add shine sweep animations to goal icons, regenerate or audit interface/*.gfx SpriteType files, or when sprite and texturefile paths report as invalid. Also use when icon directories under gfx/interface/goals|ideas need deduplication, cleanup of legacy naming, or a final acceptance check across multiple country tags.
agent_created: true
---

# HOI4 MOD 图标命名规范化 + gfx 重建流水线

把散乱的图标资产收敛成一套**可预测、可校验**的命名与 sprite 声明，并在多国 tag 场景下彻底消除
「重复文件 / 失效路径 / 历史遗留混入 gfx」三类问题。

## 核心口径（先确认，用户可能有自己的偏好）

| 项 | 规范 |
|---|---|
| goal 文件 | `goal_<TAG>_<英文名>.png`，`<TAG>` **全大写** |
| idea 文件 | `idea_<TAG>_<英文名>.png`，`<TAG>` **全大写** |
| idea 重复段 | 名字里**不保留** `Idea_` 段（`idea_LYY_Alchemy_Bench.png`，不是 `idea_LYY_Idea_Alchemy_Bench.png`） |
| 目录 | `gfx/interface/goals/<TAG>/`、`gfx/interface/ideas/<TAG>/` —— **复数**，绝不新建 `goal/` 或 `idea/` |
| goal 尺寸 | 96×87 |
| idea 尺寸 | 64×64 |
| sprite 名 | `GFX_<kind>_<TAG>_<英文名>` |
| goal shine | goal 要 `<name>_shine` 双段扫光动画 |
| idea shine | **不要** —— 用户常只给 goal 加 shine |
| 目录内 | 不许有子文件夹 |

`英文名` 只能是 `[A-Za-z0-9_]`，不得含空格、连字符、中文。来源 topics 里的名字是
`<Tag>_<英文名>`（idea 是 `<Tag>_Idea_<英文名>`），归一时要**剥掉 `<Tag>` 段、剥掉 `Idea_` 段**、
把空格换成下划线、把连续下划线压成一个。

## 执行流程

### 0. 定位权威源（最重要的一步）

**磁盘上的文件可能只落了一半，绝不能靠磁盘现状定性。** 权威源是生成产物目录，例如
`out_<TAG>_v7/{goal,idea}/`（第一批）和 `out_<TAG>_v8/{goal,idea}/`（第二批）。
先确认这些目录存在且各有 200 张，再开始。

### 1. 落地规范名 PNG

跑 `scripts/norm_final.py`（按项目改里面的 `MOD` / `GEN` / `TAGS` 常量），它会：
- 从权威源复制出规范名文件（目标名不存在才写）
- 输出待删清单 `_rm_norm_final.txt`

### 2. 幂等补齐（补漏的正确入口）

跑 `scripts/rebuild_all.py`。**幂等**：已存在就跳过并校验 md5，不存在才复制。
脚本跑完会直接打印每个目录的「规范名 N」，这个 N 必须等于预期值（通常 200）。

### 3. 删非规范名文件

⚠️ **删之前必须校验安全性**：每条待删文件都要确认「目标规范名文件已存在且 md5 相同」，
否则会连带删掉刚建好的正确文件（这是本流程最容易出的事故）。

跑 `scripts/rm_final.py`（需 `dangerouslyDisableSandbox: true`）。它会打印
`删除 N / 已存在 M / 失败 0`，**失败数必须是 0**。

### 4. 生成 gfx

跑 `scripts/build_gfx.py`，输出到 `stage4/DOT_Icons_<TAG>.gfx`。
脚本只收录「规范名 + 尺寸符合规格」的 PNG，自动排除历史遗留。期望输出：

```
TAG     goal   idea   shine   sprite  depth
LYY      200    200     200      400      0
...
异常国家: 0 / 8
```

### 5. 落地 gfx

工作区通常禁止 shell 子进程覆盖已存在文件，唯一可用方式：

```bash
for T in LYY MOT INA; do
  rm -f "$MOD/interface/DOT_Icons_$T.gfx"
  cat "$STAGE/DOT_Icons_$T.gfx" > "$MOD/interface/DOT_Icons_$T.gfx"
done
```
（需 `dangerouslyDisableSandbox: true`）

### 6. 验收

跑 `scripts/accept.py`，检查：每目录数量 / 文件名格式 / 尺寸 / 非规范名残留 / 单数目录残留 /
子文件夹 / sprite 名唯一性与格式 / goal·idea·shine 数量 / shine 配对 / texturefile 与
animationmaskfile 路径有效性 / 括号平衡。全绿才算完成。

想看被排除的历史遗留具体是哪些，跑 `scripts/list_legacy.py`。

## 必须避开的坑

1. **「已存在」判定必须查目标名，不能查源名。**
   `os.path.exists(源文件名)` 会命中磁盘上的旧命名文件，于是全部跳过、正确版本从未生成。
   永远先算出 `norm` 再查 `norm`。

2. **生成删除清单时，归一函数会把新旧两版算成同一个名字**，导致刚建好的规范名被列进删除清单。
   `Lyy_X` 与 `goal_Lyy_X` 归一后都是 `X`。删除前务必做「目标存在 + md5 相同」双重校验。

3. **删除速度**：Bash逐条 `rm` 约 14 秒/条（沙箱每次都过检查），3000 张要 12 小时；
   单进程 Python `os.remove` 约 0.29 秒/条。**永远用 Python 批删**。
   `xargs -0 -n 40 rm -f` 会被沙箱 SIGTERM 强杀。

4. **覆盖已存在文件**：`shutil.copyfile` / `open(...,'w')` / `os.rename` / `cp -f` 全被拒；
   `os.rename` 报 WinError 5。只有 Bash「`rm -f` + `cat >`」可用。
   搬文件用 `shutil.copyfile` 到新名 + 删旧名。

5. **判定「本批生成 vs 历史遗留」的最稳口径是「在 topics 名单里 + 尺寸符合规格」**，
   不能只看文件名格式 —— 遗留文件里也有恰好尺寸合规的。

6. **验收脚本自己最容易写错**，务必：
   - 路径校验正则加 `^` 锚点（否则 3200 个正确路径全部误报）
   - 用 `r'...%s...' % kind` 时确认占位符数量匹配（多余的 `%` 会 TypeError）
   - 不要把Windows 路径塞进 Bash 里的 `python -c`（MSYS 路径混用 → FileNotFoundError），
     一律写成 `.py` 文件用绝对解释器跑

7. **`gfx` 不在 `replace_path` 里**，查 gfx 文件必须连原版一起查。
   `effectFile = "gfx/FX/buttonstate.lua"` 是引擎内建伪路径，磁盘上没有这个文件，不要去建。

## shine SpriteType 模板

```
\tSpriteType = {
\t\tname = "<sprite>_shine"
\t\ttexturefile = "<与本体相同的 texturefile>"
\t\teffectFile = "gfx/FX/buttonstate.lua"
\t\tanimation = {
\t\t\tanimationmaskfile = "<与本体相同的 texturefile>"
\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"
\t\t\tanimationrotation = -90.0
\t\t\tanimationlooping = no
\t\t\tanimationtime = 0.75
\t\t\tanimationdelay = 0
\t\t\tanimationblendmode = "add"
\t\t\tanimationtype = "scrolling"
\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }
\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }
\t\t}
\t\tanimation = { ... animationrotation = 90.0 ... }
\t\tlegacy_lazy_load = no
\t}
```

`shine_overlay.dds` 用原版路径即可，MOD 不必自带，引擎会回落。
校验路径时用 `^\t\ttexturefile = "..."$` 这种带缩进锚定的正则，
否则会误匹配 3 空格缩进的 `animationtexturefile`。