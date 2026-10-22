# -*- coding: utf-8 -*-
import io, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')

# 1) 版本 2.10 → 2.11（三处）+ 同步 .claude
SK = r'C:\Users\LR\.zcode\skills\hoi4-modder-cn'
fp = os.path.join(SK, 'SKILL.md')
t = io.open(fp, 'rb').read().decode('utf-8-sig')
t = t.replace('version: 2.10', 'version: 2.11').replace('版本：v2.10', '版本：v2.11').replace('当前版本 **v2.10**', '当前版本 **v2.11**')
io.open(fp, 'wb').write(t.encode('utf-8'))
CL = r'C:\Users\LR\.claude\skills\hoi4-modder-cn'
for f in ('SKILL.md', 'references/gamma-pipeline.md'):
    shutil.copy2(os.path.join(SK, f.replace('/', os.sep)), os.path.join(CL, f.replace('/', os.sep)))
print('skill v2.11 + 同步 .claude ✓')

# 2) 进度记忆追加 10-16 记录
M = r'C:\Users\LR\.zcode\cli\memories\projects\ilyich-genshin-test-version-57bab93f04048e34\memory\gamma-mod-progress.md'
mt = io.open(M, 'rb').read().decode('utf-8-sig')
add = '''

## 10-16 批次（蒙德 VP 30 条 + 战略区改名 + 补号 loc 尾巴）
- **战略区改名**：马斯克海 → **马斯克礁**（`DOT_Strategic_Region_Names…yml` 的 DOT_STRATEGICREGIONS_46 键；编号仍是 id=2）。
- **蒙德 VP 30 条已落地**（备份 `.backups/vp_mond_20261016_180614`）：20 个州；**292 改值**（原"骑士团总部"25 → "喷泉广场"10）；其余 29 条新增；3481 西风骑士团总部（50）→ **MOT 首都本就=466，零改动**；loc 全部进 `DOT_Victory_Points_l_simp_chinese.yml`（30 键，BOM+CRLF）；**352 在旧文件 `victory_points_l` 的同名键已同步对齐为"无相之雷"**（避免重复键取错值）。州 466 = 7 个 VP 块（多 VP=多个单对块，与原版/Beta/Gamma 52 州实证一致）。
- **补号 loc 尾巴补完**：`DOT_STATE_703` 的"**遗迹巨像**"按"州名跟州走"迁到 `DOT_STATE_63`，703 置 `*`（704-712 孤儿键全是 `*`，无害留观）。
- check_states 结果：**93 条 = 91 条既有纳塔核心问题（100-172 段，owner=NAT 族但多挂 NCP 核心）+ 2 条 F 项**（DOT_STATE 孤儿 703-712、english 目录 VP 重复键——均既有/无害）；VP 总数 268、capital 零悬空、702 州 1-702 ✓。
- **skill 更正（v2.11）**：旧说法"一州多个 VP 必须写同一行否则互相覆盖"**为误诊已更正**——正确=多个单对块（原版 381 州/Beta 73 州/Gamma 52 州实证）。'''
if '## 10-16 批次' not in mt:
    mt = mt.rstrip('\r\n') + add + '\n'
io.open(M, 'wb').write(mt.encode('utf-8'))
print('记忆已追加 ✓')

# 3) MEMORY.md 索引行微调
MI = os.path.join(os.path.dirname(M), 'MEMORY.md')
mi = io.open(MI, 'rb').read().decode('utf-8-sig')
mi = mi.replace('地图定义错误全清、引用迁移完毕；待测试', '地图定义错误全清、引用迁移完毕；10-15 战略区连号事故已破案修复（游戏可进）、10-16 蒙德 VP 30 条+马斯克礁')
io.open(MI, 'wb').write(mi.encode('utf-8'))
print('MEMORY.md ✓')
