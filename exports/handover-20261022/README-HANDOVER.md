# 提瓦特黎明（HOI4 Mod）交接包

生成日期：2026-10-22
用途：交接给下一位接手者（可能使用 ZCode + GLM / Claude Code）。

## 1. 项目与路径

| 项 | 路径 |
|---|---|
| 仓库 | `C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version` |
| 主线 mod | `Daybreak of Teyvat Gamma Version` |
| 游戏根目录（**只读**） | `F:\Steam\steamapps\common\Hearts of Iron IV` |
| 部署副本（**游戏实际加载**） | `C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version` |

游戏加载的是**部署副本**，不是仓库目录；两边必须同时改。

## 2. 安装（ZCode / GLM / Claude Code）

1. **主技能**：把 `skills/hoi4-skill-aimodding/` 整个目录复制到
   `C:\Users\<你>\.zcode\skills\hoi4-skill-aimodding\`
   （若也用 Claude Code，再复制一份到 `~\.claude\skills\`）。
   注意 `SKILL.md` 的 frontmatter `name` 必须与目录名一致（当前是 `hoi4-skill-aimodding`）。
2. **记忆**：把 `memory/` 放到项目根（或你客户端的记忆目录），每次会话**先读 `memory/MEMORY.md`**；其余 .md 按需读。
3. **项目指令**：把 `AGENTS.md` 放到项目根。若客户端只认 `CLAUDE.md`，复制一份改名为 `CLAUDE.md`。
4. **项目自有技能**：`project-skills/` 是仓库 `.skills/` 的副本（建筑浮空、FBX/PMX 转 mesh、高度图、图标流水线、bug triage、scripted GUI 等），可放进 `~/.zcode/skills/` 或项目 `.skills/`。
   （已剔除两个 20MB+ 的素材文件：`日月全事 月之六.pdf`、`原神素材.zip`，需要时从原 `.skills/` 取。）
5. **工具/文档**：`tools/` 与 `docs/` 放回仓库对应目录。`tools/*.py` 被 `.gitignore` 忽略，clone 不会带，必须手动放。
6. **未包含**：`rhoiscribe-hoi4` 技能（23MB exe，可选），需要时从原 `.dsh/skills/` 拷贝或按官方说明下载。

## 3. 六条铁律（必须遵守）

1. **双副本同改**：仓库 + 部署副本同时写，改完用 `tools/compare_copies.py` 核对（0 差异）。
2. **州号 1-N 严格连号**：删州/合并后立即补号；**只准「简单迁移」（尾部补号）**，严禁全量迁移；战略区 id 也必须连号。
3. **改地块归属/重划必须用户点名**：不得以"地理更合理"自行推断。
4. **回复简洁**：不反复追问状态，汇报一次即止。
5. **文件卫生**：脚本放 `tools/`、文档放 `docs/`，不在仓库根目录生成文件；本地化 yml 必须 BOM + CRLF。
6. **判官工作流**：改州/省后启动一次游戏，按 `logs/error.log` 把 buildings 修到 0 报错（`not within specified state` / `invalid state` / `coastal but no port`）。

## 4. 当前状态（截至 2026-10-22）

- **689 州、1-689 连号**；省 4698；VP 285；战略区 **1-9**（1 暗之外海、2 马斯克礁、3 果酒湖、4 风啸山坡、5 苍风高地、6 坠星山谷、7 明冠山地、8 风息山、9 龙脊雪山）。
- 最近提交：`92e25e0b8 补给01`（远程 `main` 已同步）。
- **未提交改动**：`interface/frontendgamesetupview.gui`（选国预览的溢出图标格移到屏幕外 `x=2000`，目的是让预览只显示前 3 个大图标）。补丁见 `patches/uncommitted-interface.patch`，未验证完。
- 已知遗留（非本轮引入）：`check_states` 的 C 核心 91 条（纳塔双层核心等）、english 重复 VP key；`check_brackets` 应全过。
- 部署副本与仓库当前是否一致：跑 `python tools/compare_copies.py` 确认。

## 5. 自检命令

需要 Python 3 + numpy（本机原先用 DSH 自带运行时，接手机器请自行 `pip install numpy`）：

```bat
python skills\hoi4-skill-aimodding\scripts\check_states.py --mod "Daybreak of Teyvat Gamma Version"
python skills\hoi4-skill-aimodding\scripts\check_brackets.py --mod "Daybreak of Teyvat Gamma Version"
python tools\compare_copies.py
```

`check_brackets.py` 已固定 UTF-8 读取（v2.23 起），不需要 `-X utf8`。

## 6. tools/ 常用脚本

| 脚本 | 用途 |
|---|---|
| `gamma_state_edits.py` | 转省 / 改归属（自动同步 buildings） |
| `rebuild_buildings_final.py` | buildings 终版重整；**海军吸附口径与游戏不符，改州后勿盲跑** |
| `check_buildings.py` | buildings 守门检查 |
| `compare_copies.py` / `what_changed.py` | 双副本全树对照 |
| `audit_operations.py` | 从 `.backups/` 回放操作历史 |
| `fill_state_gaps.py`（在 skill `scripts/`） | 简单迁移补号 |

## 7. GUI 调试经验（本轮踩过的坑）

- 选国预览/外交的精神图标容量由**容器宽度 ÷ 槽宽**决定，不是 `grid.size`；改 `max_slots` 未必生效。
- `spirit_idea_entry_small` / `spirit_modifier_entry_small` 是**三处 GUI 共用**的模板（frontmatter 在 `frontendgamesetupview.gui` 里），无法只让外交大、预览小。
- 当前方案：small 模板 68×68、`scale=1`（外交全大图标）；预览溢出格移到屏幕外，只显示前 3 个。

## 8. 交接提醒

- 用户偏好：回复简洁、命令无歧义、不反复追问。
- 大改前备份到 `.backups/<批次>_<时间戳>`。
- 改完州/省数据后务必自检 + 进游戏验证。
