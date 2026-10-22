# 有限战争 · 通用模板（动态目标决策 + 任务结算）

> 本文件是一套**可直接套用**的机制骨架，不绑定任何具体国家或 mod。
> 示例缩进一律是 **tab**，落地时照抄，不要换成空格。

## 适用场景

- **殖民地 / 边境「有限战争」**：只在一个战区打，不触发同盟链，有硬性时间与投降度上限。
- **动态目标征伐**：想对「当前占据目标州的国家」自动生成宣战条目，而不是给每个潜在敌人手写一条决策。
- **可复用的四个零件**：
  1. `target_array` 动态决策（一国一条）
  2. 战争范围**快照**（宣战瞬间冻结争夺州）
  3. 任务（mission）三出口：完成 / 取消 / 超时
  4. 事件链谈和 + 战后割州 + 清理

## 机制总览（七步）

```
① 静态战区数组（state 列表，写死在历史文件）
        ↓
② 刷新「候选目标」数组（country 列表：战区各州的 controller，去重）
        ↓
③ 决策挂 target_array → 每个候选国生成一条
        ↓
④ 点击：快照「实际争夺州」+ 记目标变量 + 记目标盟友
        ↓
⑤ 限制：退阵营 / can_join_factions = no / N 天任务 / 投降度阈值
        ↓
⑥ 任务三出口 → 事件链谈和 → 按快照逐州割让
        ↓
⑦ 清理变量 + 刷新候选数组
```

## 数据模型

| 数组 / 变量 | 作用域类型 | 写入时机 | 读取方 | 生命周期 |
|---|---|---|---|---|
| `TAG_lw_states` | state | 历史文件里 `every_state` 过滤州号 | 刷新脚本、决策 `target_trigger` / `highlight_states` | 永久 |
| `TAG_lw_controllers` | country | `TAG_refresh_lw_controllers` | 决策的 `target_array` | 每次刷新重建 |
| `lw_states`（本次争夺） | state | 宣战时快照 | 任务胜负判定、战后割州、控制权变化 | 一场战争 |
| `lw_target_allies` | country | 宣战时（宗主国）+ 担保 on_action | `TAG_peace_out` | 一场战争 |
| `previous_lw_targets` | country | （可选）宣战成功后追加 | 仅作历史记录，默认不参与判定 | 可选 |
| `lw_target` | country（变量） | 宣战时 | 任务、事件、清理 | 一场战争 |
| `global.lw_surrender_threshold` | 数值 | 任一国历史文件里设一次 | 任务取消/完成判定 | 全局共用 |

## 代码骨架

### 1) 历史文件：定义战区 + 全局阈值

```hoi4
# history/countries/TAG - Name.txt
# 战区：这场「有限战争」允许夺取的州
every_state = {
	limit = {
		OR = {
			state = 100
			state = 101
			state = 102
		}
	}
	add_to_array = {
		array = ROOT.TAG_lw_states
		value = THIS
	}
}

# 全局投降度阈值（0.2 = 20%），所有有限战争共用
set_variable = { global.lw_surrender_threshold = 0.2 }
```

### 2) 刷新候选目标（scripted_effects）

从战区反推「现在谁占着这些州」，去重后重建 country 数组。**排除自己**，否则决策会对自己生成。

```hoi4
# common/scripted_effects/TAG_scripted_effects.txt
TAG_refresh_lw_controllers = {
	clear_array = TAG.TAG_lw_controllers

	for_each_scope_loop = {
		array = TAG.TAG_lw_states
		if = {
			limit = {
				controller = { NOT = { tag = ROOT } }     # 排除自己
				NOT = {
					controller = {
						is_in_array = { array = TAG.TAG_lw_controllers value = THIS }
					}
				}
			}

			controller = {
				add_to_array = { array = TAG.TAG_lw_controllers value = THIS }
			}
		}
	}
}
```

**何时刷新**：国策完成、战争结束、州控制权变化后。国策里直接 `TAG_refresh_lw_controllers = yes` 调用即可。

### 3) 决策类别 + 决策本体

```hoi4
# common/decisions/categories/TAG_decision_categories.txt
TAG_lw_cat = {
	priority = 45
	icon = GFX_decision_category_military_operation

	allowed = {
		original_tag = TAG
	}
	visible = {
	}
}
```

```hoi4
# common/decisions/TAG.txt
TAG_lw_cat = {

	TAG_start_lw = {
		target_root_trigger = {
			original_tag = TAG
		}

		# ★ 关键：对数组里每个通过 target_trigger 的国家各生成一条，FROM = 该国家
		target_array = ROOT.TAG_lw_controllers

		target_trigger = {
			# ① 确实在候选名单里
			is_in_array = {
				array = ROOT.TAG_lw_controllers
				value = FROM
			}
			# ② 至少占着战区里一个州
			any_of_scopes = {
				array = ROOT.TAG_lw_states
				is_controlled_by = FROM
			}
			# ③ 可选：想限制「同一国家只打一次」，取消下面这行注释
			# NOT = { is_in_array = { array = previous_lw_targets value = FROM } }
		}

		visible = {
			has_completed_focus = TAG_lw_unlock
		}

		available = {
			NOT = {
				is_ally_with = FROM
				has_war_with = FROM
				has_non_aggression_pact_with = FROM
				FROM = { is_guaranteed_by = ROOT }
			}

			custom_trigger_tooltip = {
				tooltip = is_not_engaged_in_a_limited_war
				NOT = { has_variable = lw_target }
			}
		}

		highlight_states = {
			highlight_states_trigger = {
				is_in_array = { array = ROOT.TAG_lw_states value = THIS }
				is_controlled_by = FROM
			}
		}

		cost = 20

		complete_effect = {
			# —— 记原阵营，然后单干 ——
			clear_variable = pre_lw_faction_leader
			if = {
				limit = {
					is_in_faction = yes
					is_faction_leader = no
				}
				faction_leader = {
					set_variable = { ROOT.pre_lw_faction_leader = THIS }
				}
				leave_faction = yes
			}
			set_rule = { can_join_factions = no }

			# —— 清上一场残留 ——
			clear_array = lw_states
			clear_variable = lw_target
			clear_array = lw_target_allies

			# —— 快照：只把「当前被目标控制」的战区州记进来 ——
			for_each_scope_loop = {
				array = TAG_lw_states
				if = {
					limit = { is_controlled_by = FROM }
					add_to_array = { array = ROOT.lw_states value = THIS }
				}
			}

			set_variable = { lw_target = FROM }

			# —— 目标是附庸时，把宗主国拉进盟友名单 ——
			if = {
				limit = { var:lw_target = { is_subject = yes } }
				var:lw_target = {
					overlord = {
						add_to_array = { array = ROOT.lw_target_allies value = THIS }
					}
				}
			}

			declare_war_on = {
				target = FROM
				type = annex_everything
			}

			activate_mission = TAG_lw_mission

			# 可选：记录历史（默认不参与判定；要「只打一次」见 target_trigger 第 ③ 条）
			# add_to_array = { previous_lw_targets = FROM }
		}
	}
}
```

### 4) 任务：三个出口

```hoi4
TAG_lw_mission = {
	visible = { always = yes }
	is_good = no

	# 完成条件：战区全占
	available = {
		all_of_scopes = {
			array = ROOT.lw_states
			is_controlled_by = ROOT
		}
	}

	fire_only_once = no            # 关键：设 yes 会让整套机制全局只能用一次
	activation = { always = no }

	# 取消：目标没了 / 已投降 / 投降度超过阈值
	cancel_trigger = {
		OR = {
			exists = no
			has_capitulated = yes
			surrender_progress > var:global.lw_surrender_threshold
		}
	}

	days_mission_timeout = 365

	complete_effect = {
		country_event = { id = TAG_lw_events.1 hours = 2 }
	}

	cancel_effect = {
		if = {
			limit = { surrender_progress > var:global.lw_surrender_threshold }
			var:lw_target = {
				country_event = { id = TAG_lw_events.6 hours = 2 }
			}
		}
	}

	timeout_effect = {
		var:lw_target = {
			country_event = { id = TAG_lw_events.6 hours = 2 }
		}
	}
}
```

### 5) 事件链（职责分工）

| 事件 | 收件人 | 作用 |
|---|---|---|
| `.1` | 发起国 | 打赢/到期通知：选「谈和」→ 通知目标 `.2`；选「继续打」→ 清变量、加战争支持 |
| `.2` | 目标国 | 选「结束」→ 发 `.3`；选「继续」→ 自减稳定/战争支持，发 `.4` |
| `.3` | 发起国 | **结算**：`TAG_peace_out` → 逐州 `transfer_state_to` → 战后钩子（解锁后续决策）→ 重入阵营 → 清理 |
| `.6` | 目标国 | 失败/超时：给发起国台阶（割一州停战 / 继续打） |

结算事件的核心循环：

```hoi4
	TAG_peace_out = yes

	for_each_scope_loop = {
		array = lw_states
		owner = {
			if = {
				limit = {
					FROM = { NOT = { is_in_array = { array = lost_states_due_to_lw value = PREV.PREV } } }
				}
				FROM = { add_to_array = { array = lost_states_due_to_lw value = PREV.PREV } }
			}
		}
		transfer_state_to = ROOT
	}

	TAG_re_add_to_old_faction = yes
	TAG_clear_lw_variables = yes
```

### 6) 清理与战后收尾

```hoi4
TAG_clear_lw_variables = {
	hidden_effect = {
		clear_array = TAG.lw_states
		clear_array = TAG.lw_target_allies
		clear_variable = TAG.pre_lw_faction_leader
		clear_variable = TAG.lw_target
		TAG_refresh_lw_controllers = yes          # 控制权变了，重算候选
		set_rule = { can_join_factions = yes }
	}
}

TAG_re_add_to_old_faction = {
	if = {
		limit = {
			has_variable = pre_lw_faction_leader
			NOT = { has_war_with = var:pre_lw_faction_leader }
			var:pre_lw_faction_leader = {
				exists = yes
				is_subject = no
				has_capitulated = no
				is_faction_leader = yes
			}
		}
		set_rule = { can_join_factions = yes }
		var:pre_lw_faction_leader = { add_to_faction = ROOT }
	}
}

# 批量和平：盟友名单逐个 + 目标本人
TAG_peace_out = {
	for_each_scope_loop = {
		array = TAG.lw_target_allies
		if = {
			limit = { has_war_with = TAG }
			white_peace = { tag = TAG }
			every_subject_country = {
				limit = { has_war_with = TAG }
				white_peace = { tag = TAG }
			}
		}
	}

	if = {
		limit = { has_variable = TAG.lw_target }
		white_peace = { tag = var:TAG.lw_target }
	}
}
```

## 要改的参数（8 处）

| # | 位置 | 替换成 |
|---|---|---|
| 1 | 所有 `TAG` | 你的国家 TAG |
| 2 | `TAG_lw_states` 里的州号 | 你的战区州号 |
| 3 | `global.lw_surrender_threshold` | 想要的投降度阈值（0~1），全局只设一次 |
| 4 | `days_mission_timeout = 365` | 战争最长天数 |
| 5 | `cost = 20` | 政治点数消耗 |
| 6 | `has_completed_focus = TAG_lw_unlock` | 解锁国策 |
| 7 | 事件 namespace `TAG_lw_events` | 你自己的 namespace |
| 8 | `lost_states_due_to_lw` / `pre_lw_faction_leader` 等变量名 | 换成不冲突的命名 |
| 9 | 开战次数模式 | 默认不限；要「一国一次」见下节 |

## 开战次数：默认不限，可切回「一国一次」

| 模式 | `target_trigger` | `complete_effect` | mission |
|---|---|---|---|
| **不限次数（默认）** | 不查 `previous_lw_targets` | 不记录 | `fire_only_once = no` |
| 一国一次 | 加 `NOT = { is_in_array = { array = previous_lw_targets value = FROM } }` | `add_to_array = { previous_lw_targets = FROM }` | `fire_only_once = yes` |

三个位置必须**同进同退**：

- 只加 `target_trigger` 判定、mission 仍是 `no` → 打完还能再点（判定没生效？不，是判定生效了但 `previous_lw_targets` 没记录时永远为空，于是等于没限制）。
- 只改 mission 为 `yes`、不加判定 → 决策照常出现，但点了之后 `activate_mission` 直接失败：**战争打起来了，任务却不走**，365 天判定、谈和、割州全部失效。
- 想「每个目标一次、但不同目标可以各打一次」→ 用「一国一次」那套即可，天然按国家区分。

> 补充：即便不限次数，`target_trigger` 里的「至少占着战区一个州」仍会挡住打完之后目标已无战区州的情况——所以重复打同一国家，前提是它又拿回了战区里的州。

## 本地化 key（必须补）

- 决策：`TAG_start_lw` / `TAG_start_lw_desc`
- 任务：`TAG_lw_mission` / `_desc` / `_timeout`
- 事件：`TAG_lw_events.1.t` `.desc` `.a` `.b`，依次到 `.7`
- 提示：`is_not_engaged_in_a_limited_war`

## 坑与验收清单

1. **`target_array` 必须配 `target_root_trigger`**，否则条目会对所有国家生成。
2. **数组元素类型必须一致**：`target_array` 里是 country，`target_trigger` 里就按 country 写；把 state 塞进 country 数组会静默失效（不报错、条目凭空消失）。
3. **默认不限次数**：不查黑名单 + mission 用 `fire_only_once = no`。要改回「一国一次」必须**同时**改两处（target_trigger 加 `previous_lw_targets` 判定 + mission 设 `fire_only_once = yes`），只改一处会出现「决策可点但任务激活不了」的假死。
4. **`global.lw_surrender_threshold` 是全局变量**，多个国家共用；要做「每国不同阈值」必须改成国家变量，并同步改任务里的两处判定。
5. **`lw_states` 存的是 state scope**，但 `on_state_control_changed` 里比较的是 `FROM.FROM`（州 ID）；靠引擎的 scope→id 转换对上，不要改成直接存 ID。
6. **快照必须只收录「目标当前控制」的州**，否则战后可能把第三方或自己的州割过来。
7. **事件里的 `for_each_scope_loop` 默认 scope 是 state**，`owner = { }` / `controller = { }` 才能进到国家作用域。
8. **验收**：改完跑 `scripts/check_brackets.py`（括号/引号/BOM），再进游戏确认：决策条目数 = 候选国数；点一次后该国条目消失（已不在候选名单）；365 天或投降度达标后能正常谈和割州；默认配置下**谈和之后还能对同一国家再次开战**（若启用「一国一次」则不应再出现条目）。
