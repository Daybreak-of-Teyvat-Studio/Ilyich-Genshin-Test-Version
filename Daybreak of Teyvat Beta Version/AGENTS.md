# 提瓦特黎明（Daybreak of Teyvat）— HOI4 Mod 项目规则

原神主题 HOI4 total conversion mod，代码为 Paradox Interactive 脚本语言（形似 Lua，对格式极其敏感）。所有工作围绕编辑 `.txt` / `.gfx` / `.yml` 文件展开。详细开发指南用 `hoi4` skill。

## 编辑铁律

- **缩进一律用 tab**，绝不用空格。HOI4 解析器对格式严格。
- **不要用 Edit 工具直接改 Paradox 脚本文件** — tab/空格不匹配时会静默失败。改 `.gfx` / `.txt` 用 **PowerShell 正则 `-replace`**；批量改名需区分大小写时用 **`-creplace`**（`-replace` 大小写不敏感，会把 `rap_role_` 这类误改成大写）。
- **始终照抄附近已有代码作模板**，风格偏差即是错误。
- 用户用中文报统计名（如"额外损伤"）时，**先核实确切的英文 key 再动手，不要猜**。`additional_collateral_damage` = 建筑/基建附带损伤（超重型火炮类特殊数值），**不是** `soft_attack`（对人员杀伤）。

## 关键路径

- **单位定义**：`common/units/*.txt`（如 `Fatui_Skirmisher.txt`、`HIP_RockfondRifthound.txt`）
- **图标**：`interface/DVA_Tech.gfx`（单位 counter 图标）、`interface/DOT_special_units.gfx`（特殊单位注册）
- **编制模板 / OOB**：`history/units/COUNTRY_1936.txt`（如 `HIP_1936.txt`、`SFS_1936.txt`）
- **简中本地化**：`localisation/simp_chinese/ZZZ_l_simp_chinese.yml`（单位名）、`localisation/simp_chinese/DVA_l_simp_chinese.yml`（事件/决议）
- **决议**：`common/decisions/ABY_decisions.txt`（深渊教团决议，创建 HIP 编制）
- **事件**：`events/ABY_Event.txt`（HIP 编制创建的触发事件）
- **国策**：`common/national_focus/`
- **国家历史**：`history/countries/HIP - Hilichurl_Puppet.txt`

## 国家 tag

HIP = 丘丘人傀儡国，ABY = 深渊教团，SNE = 至冬/愚人众。

## 编制模板

编制用 (x, y) 网格放置团，最多 5 列 × 5 行；`is_locked = yes` 防止玩家编辑模板。
