---
name: gamma-tool-suite
description: 仓库 tools/ 目录的 Gamma mod 工具脚本清单（*.py 被 .gitignore 忽略，仅存本机）——各脚本用途与关键约定
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_3c421fb8-e84d-47d4-a44c-53452b380660
---

# Gamma mod 工具脚本（项目 `tools/` 目录，`*.py` 在 .gitignore 中不入库）

**收纳规矩（用户 2026-09-29 要求）**：脚本一律放 `tools/`、产出文档放 `docs/`、运行输出用完即删——**不要在项目根目录生成任何文件**（根目录只留 3 个 mod 版本目录、README、.gitignore）。此规矩已写入 SKILL.md 与 gamma-pipeline.md。

| 脚本 | 用途 | 关键点 |
|---|---|---|
| `gamma_state_edits.py` | 转省/改归属。语法 `省+州`（逗号/全角逗号=并列省共享右侧，句点/分号=指令分隔，空格=并列省）、`州+TAG` 改归属（核心清空只留新 TAG） | 转省自动同步 map/buildings.txt（**坐标像素省规则**——naval 水面标记会被错改到海州，转省后跑 rebuild_buildings_final 校正）；`--dry` 干跑。**改归属左侧只能是单个州号**，并列写法会报错，需拆两条 |
| ⚠ `rebuild_buildings_final.py` | **buildings 终版重整（单一权威规则一次遍历）**：naval 五类省列陆省直用否则吸附；其余类按坐标像素省；SL 全删重放每陆州标准 7×1+anti_air×3、海州 0 条；声明州不存在则删条目 | 取代所有部分修复脚本（多脚本各持口径互相覆盖是 09-29 灾难根源）。**⚠ 2026-10-16 实证其"海军吸附"口径与游戏不符**（它取 3×3 方格内最多数省，游戏取"最近沿海省"）——把 14 行海军行改坏（`14→35`、`44→434`），补号后又把正确的 62/65 退回合并前旧号 63/704。**改州后勿盲跑；一律走「判官工作流」（见 gamma-mod-progress 记忆）** |
| `trim_sl.py` | SL 超配物理删除：每陆州保留 7×1+anti_air×3，多余删除 | 与 rebuild_buildings_final 配套 |
| `rebuild_buildings.py` | 按当前 state 文件整体重建 map/buildings.txt（3×3 邻域判定） | 旧工具，被 rebuild_buildings_final 部分取代 |
| `check_buildings.py` | 守门：8 类州级生成点每州数量 vs 原始（`.backups/map_buildings_20260923_222654`）、行数/CRLF/BOM/字段数 | 每次州/buildings 改动后必跑；**州号映射变化时终验对照也要做同映射**（如 {860:125, 861:123}） |
| `crash_fix.py` | **海军建筑坐标修正**：地图标记点在海面时，按"吸附最近陆地省"定州（游戏真实规则） | 兼做海州 `state_category` 修正；每次转省后跑 |
| `fix_col7.py` | **buildings 第 7 列省号对齐**（声明州 vs 第 7 列省归属；水面海军类吸附） | 与 rebuild_buildings_final 规则互补；第 7 列多为 0 的陆上类不参与判定 |
| `rebuild_buildings_full.py` / `rebuild_buildings_std.py`(如存) | 中间版本（部分修复），已被 final 取代 | 留档勿再跑 |
| `fix_enclaves3.py` / `fix_enclaves2.py` / `fix_enclaves_min.py` | 飞地检测与移出：2px 桥接连通块 + 真实像素缝隙对比；min 版按用户指定单省转移 | `--dry` 出清单；**目标州必须由用户指定，不可自行推断**（自行迁 5 处被全部回滚） |
| `rollback_enclaves.py` | 按备份目录整体还原指定州文件 | 回滚前先把当前状态另存 `pre_rollback_*` |
| `integrate_states.py` | 按国家重排州（连通+3~8 省），蒙德系/璃月系/天理受保护 | 含语法自检与丢省兜底网 |
| `rebalance_states.py` | 多州省均分：`python rebalance_states.py 州1,州2,...` | 16 次随机化重试选紧凑度最优（组内最大质心距/等面积圆直径），防长条 |
| `terrain_pipeline.py` | 地形三步覆盖改造（全 plains → 国家覆盖 → 地理特征） | **必须同时写 definition.csv 与 terrain.bmp**；曾因漏写回循环导致机制层不更新（写盘成功≠内容变了） |
| `fix_definition_terrain.py` | 以 terrain.bmp 每省多数索引反推地形名，写回 definition.csv 第 7 列 | 两份不一致时的对齐工具 |
| `fix_gen_points.py` / `fix_gen_std.py` / `fix_gen_recover.py` / `fix_sea_sl.py` | 生成点从零重排（需 REMAP 且终验同映射、按"无 owner"跳过海州）/ 标准配置补齐 / 崩溃恢复 / 删海州误放 SL | **已被 rebuild_buildings_final.py 的 SL 重放+trim 链取代**；数据乱时勿用增量修复 |
| `fill_state_gaps.py`（在 skill `scripts/`） | **补空白 state 编号（两步尾部换位法·陆海分离）**：陆洞（升序）← 陆尾（降序）；被搬陆尾原号（升序）← 海尾（降序）；执行按**目标号升序**防撞号；同步 id/**name 行**/文件名/capital/buildings 第1列；**本地化重映射为覆盖式**（搬州真名覆盖目标 `*` 占位——旧版先到先得丢过 5 个名字） | `--mod <mod根目录> [--dry]`；前置强制检查（capital/buildings 引用空州 → 拒绝）；多洞时换位对数=2×洞数。**⚠ 10-18 实测：不迁 `map/airports.txt`/`rocketsites.txt` 的键**（11 个被搬州的键全部滞留在旧号 690-700）——补号后必须手工把旧键重命名到新号并确认 1..N 无缺键、无重复键 |
| `fill_gap_860.py` | 缺号 860/861 专项（旧法：海州段 862-902 前移 2 位） | 已被 fill_state_gaps 两步换位取代，留档 |
| `localisation_fix.py` | 州名 key 加 `DOT_` 前缀 + 本地化文件补 BOM、统一 CRLF | 修"原版地名混入"的必备工具 |
| `fix_state_names2.py` / `fix_name466.py` | 州名更正：把误命名的州清回 `*`，按**州号**写入正确中文名 | 名字对应的是 state 号，不是 province 号 |
| `dockyard_clean.py` | 删掉"州内有 `dockyard` 但已无沿海省"的非法州级行 | 游戏本就忽略，清理日志噪音 |
| `audit_operations.py` | 倒序回放所有 `.backups/*` 重建操作日志（哪些州/省/归属变化） | 用户问"某次改了什么"时跑它，不靠记忆 |
| `check_definition.py` / `check_terrain.py` / `check_mapdef.py` / `check_adj_pos.py` | nudge「地图定义文件存在错误」排查四件套：definition.csv 完整性 / terrain.bmp 模式调色板与备份 diff / provinces.bmp 颜色 vs definition 双向差集 + map 文件存在性 / adjacencies.csv 与 positions 覆盖 | 排查结论：map 层全部健康，nudge 报错真因是**州号缺号**（nudge 对缺号敏感，游戏本体不敏感；原版自带 112 个缺号） |
| `check_brackets.py`（在 skill `scripts/`） | **括号完整性自检（与 GitHub CI ci-test/Check.py 同规则）**：大括号匹配（common/ 全 txt+gui，# 注释后跳过栈式配对）/ simp_chinese 引号成对（每行未转义双引号=0或2）/ simp_chinese+english 本地化必须 UTF-8-SIG（BOM） | `--mod <mod根目录>`；**引号只查 simp_chinese**（english 引号是历史遗留，CI 也不查）；chardet 缺失时按 BOM 字节判定。push 前必跑 |
| `batch_desert.py` / `batch_fontaine2.py` / `batch_sumeru2.py` / `batch_fontaine.py` / `batch_round1.py` / `merge_run.py` | 批次驱动脚本：转省+合并+命名+VP 一次跑 | 模式：subprocess 调 gamma_state_edits → 读州文件构建合并指令 → 本地化/VP 写盘。**VP 追加写盘曾剥 BOM**（encoding='utf-8-sig' 读 + utf-8 写）——写本地化必须补 BOM |
| `rollback_states.py` | 整体 states 目录备份+恢复 | 恢复前先做当前态 safety 快照 |
| `gamma_regions.py` | 大区归属单一真源：解析 DOT_scripted_triggers.txt 的 Is_* 组 | |
| `gamma_palette.py` | 配色单一真源：FROZEN（冻结勿改）+ ADDED | `TAG_OF_COLOR` 供读色脚本用 |
| `gamma_read_colors.py` / `gamma_apply_colors.py` | 读涂色图逐省判定 / 按涂色装国 | 主导色判定+最近色容忍羽化 |
| `gamma_map_tools.py` / `gamma_border_layers.py` | 州号图/大区图 / 透明分界线稿 | |
| `vp_reset.py` / `vp_add2.py` / `vp_371.py` | VP 清零 / 批量加 VP+本地化+set_capital / 单州 VP | |
| `state_names_job.py` | 州名本地化改造：唯一 key `DOT_STATE_<id>` + `*` 占位 + 指定州中文名 | |
| `sea_split.py` / `sea_state_fix.py` | 海洋州创建（对角矩形内均分）/ 海州格式修复 | 新海州 `state_category = wasteland` |
| `beta_map2x.py` | Beta 州名标注图（2 倍分辨率，字号不变=相对更小） | |
| `beta_vp_map3.py` | Beta VP 标注图：省界+州界+VP 红点+名字，11264×4096，另出 29 张按国裁剪子图（全图缩放下 14px 字看不清，看子图） | VP 名收集自 Beta 全部本地化 yml |
| `fix_vp_pairs.py` | VP 多对块拆分（一 block 一对，字节级保缩进/CRLF/BOM） | 正则收尾用 `(?=\r?$)` 零宽断言防吞 \r |
| `fix_vp_loc_bom.py` | 本地化 yml 全量幂等补 BOM | |
| `build_beta_gamma_bridge.py` / `rebuild_all_v2.py` | **beta→gamma 本地化桥**（v2）：beta 州英文名→beta 中文 loc→gamma 同名州/VP；**只认活键**（州文件实际引用的 VP）+ 同号判别 + 人工映射 `beta_gamma_manual_map.json` | 输出 `beta_gamma_bridge.json`；死键=loc 有但州文件零引用（陈旧移植，必须排除） |
| `scan_gamma_script_ids.py` / `migration_v2_final.py` | 全模式扫描脚本中的 beta 州/省号 + 生成桌面 `beta至gamma_id迁移对照表.xlsx`（六 sheet） | 全模式：state 族/`states={}`/`provinces={}`/`path={}`/`controls_province`/`set_province_name id`/`location`/数字键块；**禁止盲跑 apply（会二次映射）** |
| `landmark_audit.py` / `used_vp_audit.py` / `identity_audit.py` | 地标名审计（beta vs gamma 表，同号=可疑）/ VP 键**活死判定**（州文件引用=活，否则陈旧）/ 同号对陈旧率抽查 | 判据核心：**活键才可信**，死键应清 |
| `zd_paint_read.py` / `coord_probe.py` / `coord_fft.py` / `coord_validate.py` | 涂色图读图（连通色块→省分组，`zd_division.json`）/ 坐标桥可行性验证（结论：**两版陆地布局非纯缩放，坐标桥不可行**） | 读图用 4/8 连通域自写（无 scipy）；纯水面笔误块自动忽略 |
| `make_zd_psd.py` / `make_zd_psd2.py` | 桌面临时 PSD 生成（pytoshop）：省图 + 省界线(中) + 底图三层，同 bbox 像素级重合 | pytoshop 坑：numpy2 下自动 alpha 通道 -1 溢出 → **显式补 `-1: 全255` alpha**；无 packbits → `compression=Compression.raw`；图层列表顺序=**自顶向下** |
| `what_changed.py` / `final_sweep.py` / `verify_swap_diff.py` / `compare_copies.py` | 仓库 vs 部署副本差异核对（mtime 扫描 / 全树 hash）/ 换位改动核对 | mtime 会骗人 → 用全树 hash；部署副本可当"改前快照"用 |
| `swap_tail_states.py` / `finish_swap.py` / `fix_state_errors.py` / `final_state_scan.py` | 尾段州号换位（708↔750）/ 修两类州文件错误（无效 dockyard + 错州省级块搬迁/删除）/ 全量重扫残余 | 换位要名随内容走；引用联动**只改真正换值的行**（否则产生"X=1"→"X = 1"的格式鬼影） |
| `verify_stateerrors.py` / `dump_stale_blocks.py` / `scan_ownerless.py` / `scan_tag_refs.py` / `check_sea_refs.py` / `check_tail_layout.py` | 州错误核实（沿海判定/块内容/无主州/海州引用/尾段布局） | 「无 owner」= 海州（正常）；区分沿海列（definition 第 6 列） |
| `audit_natlan_batch.py` | **指令批次逐条审计模板**：当前值 vs 批次前备份（states_20261003_200143），区分"从未落实"与"后来丢失"，输出 ✓/✗ 清单 | 每批指令落盘后跑它对账 |
| `audit_vp4.py` / `verify_natlan_theory.py` / `find_natlan_names.py` / `precheck_natlan_fix.py` / `fix_natlan_batch.py` / `fix_vp4.py` / `reinsert_vp.py` | 纳塔批次与 VP 补漏的一次性审计/修复脚本（理论验证、错挂名字定位、VP 增删+回读验证） | 留档可作模式参考 |
| `apply_batch_1005.py` / `apply_batch_1005b.py` / `apply_batch_1005c.py` / `apply_batch_1005d.py` / `apply_batch_1006.py` / `verify_batch_1005.py` | 批次落地模板：备份→转省(同步buildings)→州名(覆盖语义)→VP 值/清除/**改值**→首都(按指令顺序后写覆盖)→回读逐条验证；1006 支持 VPS 重复 pid 后名生效 + 州名覆盖现值 | **通用批次执行骨架，新批次直接复制改 ITEMS**；注意循环变量勿跨段复用（pid 被覆盖导致验证查错省）；脚本非幂等（转省 assert 已在目标州会中断），重跑验证需独立脚本 |
| `fix_4135.py` / `find_host.py` | VP 笔误纠正（清旧省+写新省+首都连带恢复）/ 查省所在州与 owner | 首都连带：错设的 tag 首都要查最早备份恢复原值（SGD=393 依据 09-27 备份） |
| `fix_buildings_col7.py` | **buildings 第 7 列声明州全量重算**：col7=陆省→col1=该省归属州；col7=海省+海军五类→像素吸附最近陆省定声明州（与 check_states G 项同款算法），只改违规行、复验 0 违规 | **转省批次后必跑**——转省挪走吸附目标省时，col7==pid 的行同步覆盖不到海军吸附行（10-07 实证 24 条转省漏 11 处） |
| `test_fill_gaps_refs.py` | fill_state_gaps v4 引用联动的合成用例自测（22 断言，临时目录搭迷你 mod） | 改 fill_state_gaps 后必跑 |
| `fix_col7.py` | **buildings 第 7 列省号对齐**（声明州 vs 第 7 列省归属；水面海军类吸附） | 修 nudge 全红 435 条 BUILDING IGNORED；之前的 crash_fix 按"坐标吸附"只改了海军类且验证同假设所以漏报 |
| `check_states.py`（在 skill `scripts/`） | **State 综合自检**：州语法/省覆盖/核心/VP/首都/本地化 BOM+孤儿+按语言目录查重/buildings 第 7 列规则+海州 SL | `--mod <mod根目录> [--baseline]`；动过州/省/本地化后主动提示运行；基线对照仅限 SL 类型 |
| `check_brackets.py`（在 skill `scripts/`） | **括号完整性自检（与 GitHub CI 同规则）**：大括号匹配（common/ 全 txt+gui）/ simp_chinese 引号成对 / 本地化 UTF-8-SIG（BOM） | `--mod <mod根目录>`；引号只查 simp_chinese（CI 同款）；push 前必跑，退出码 0/1 |

## 10-10 崩溃排查新增脚本（装备/海军/除零 + 日志取弹窗原文）
| 脚本 | 用途 | 关键点 |
|---|---|---|
| `fix_equip_errors.py` / `repair_onactions.py` | 闲云机-26型 底盘改 CAS（bomb_locks 只能配 `small_plane_cas_airframe_0`，原版实证）/ MOT 两船删无效 `front_1_custom_slot` / DVA 部队 2463→442 | 替换变体块**必须括号配对提取**（直接正则切会截断后续块，10-10 踩过）；改完跑 check_brackets |
| `fix_naval_pack.py` | VAN_1936_naval 空壳恢复 / PRI 228 舰名去重 / INA+FAV 补舰船变体（原版变体块模板改名生成）/ NewMOT 8 处除零保护 | 缺变体模板从原版 `history/countries/*.txt` 按 `type = <hull>` 提取 |
| `coastal_audit.py` | 沿海标记审计：provinces.bmp 8 邻域邻海 vs definition.csv 第 6 列（假沿海/漏标） | 实证 0/0，地图沿海标注干净 |
| `variant_gap.py` / `collect_missing.py` / `check_variant*.py` | 缺变体清单（OOB 用到的 hull vs 国家文件已有变体）/ 日志缺项聚合 / PRI 变体块详查 | `equipmentpool.cpp:1410` + `ship.cpp:1674` 是这两类错误的日志标记 |
| `read_wer.py` / `read_phase_errors.py` / `read_latest_logs.py` / `final_window_read.py` / `read_id_errors.py` / `pri_log.py` / `check_new_errors.py` | **死亡窗口取错**：WER AppCrash 签名（偏移 0x25516e5 / BEX64 / c0000409）/ 按时间片聚合非 GUI 错误 / "Failed to create id…Already exists（引擎自标 may crash）"上下文 | 普通模式日志丢缓冲 → 必须靠 **debug 日志**或 WER；`Failed to create id` 社区共识多为**非致命红鲱鱼**；死亡窗口 = 点开始后 2~5 秒 |
| `scan_mojibake.py` | 全 mod 扫 U+FFFD/锟斤拷 坏字符 | 实证 0 → 弹窗乱码是 ZH 字体渲染问题，非文件污染 |

## 外部工具
- **`F:\mod制作\Hoi4ICU.exe`（钢铁ICU）**：第三方 PyInstaller 打包的 HOI4 工具箱（`steelicu.hoi4.*`：localisation/mods/oob/techgui/gfx/subunits/icons…含 webview），55MB。10-08 11:07 自我更新后 **11:12 挂起（WER AppHang）**，是用户"**第一次**非 debug 打不开游戏"的疑似根因（游戏本体 11:17 会话正常）。**与 10-09~10-10 的"选国家→载入阶段崩溃"是两回事**（后者是 mod 数据/脚本问题，弹引擎对话框）。改它/诊断它时不要与 mod 数据问题混淆

## 环境坑（每次都要防）
- Windows 控制台中文会乱码；`findstr`/`Select-String` 二次编码。**输出写 UTF-8 文件再 Read**
- cmd 的 `for` 循环、PowerShell 多行字符串/here-doc 都不可靠 → **一律写 Python 脚本文件再跑**
- Python 脚本务必 `sys.stdout.reconfigure(encoding='utf-8')`；`.decode('utf-8-sig')` 会吞 BOM，写回必须补 `b'\xef\xbb\xbf'`——**这条已违反 5+ 次，每个写本地化的脚本都要检查**
- PowerShell 管道里 `--mod "带空格路径"` 的引号会被剥掉 → 补号类命令单独跑，不与其它命令拼一行
- python -c 的内联多行字符串转义极易失败 → 修改脚本一律用 Write 写 .py 文件执行，不用 python -c；**多行 `-c` 会被 shell 截断（多次实测静默失败/半执行）**，连简单的 confirm 也用脚本文件
- **读改写禁止在同一表达式里先 'wb' 后读**：`open(p,'wb').write(open(p,'rb').read()...)` 会先截断再读 → 文件清零（10-04 曾一次毁 3 个州文件）。铁律：先 `raw = open(p,'rb').read()` 存变量，再打开写
- 脚本改文件后**必读回验证**（数量/key 可再解析/括号平衡），并把"变更明细"打印出来；批次脚本非幂等（转省 assert 已在目标州会中断），重跑验证要用独立脚本
- 循环变量勿跨段复用（`pid` 在 VP 段被覆盖 → 后续验证查错对象，误报"验证失败"）

关联 [[hoi4-skill-structure]]、[[gamma-mod-progress]]
