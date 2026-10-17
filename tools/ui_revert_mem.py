# -*- coding: utf-8 -*-
import io, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
SK = r'C:\Users\LR\.zcode\skills\hoi4-modder-cn'
CL = r'C:\Users\LR\.claude\skills\hoi4-modder-cn'

# 1) 修正 version-adapt.md 的案例表：加"分叉 .gui 勿直接补块"的实测警示
fp = os.path.join(SK, 'references', 'version-adapt.md')
t = io.open(fp, 'rb').read().decode('utf-8-sig')
CAUTION = '''
**⚠ 实测警示（同日回退）**：上表"选国界面补元素"的做法在实测中被证明有害——该 mod 的 setup 界面是深度改版布局，把原版元素块（含原版坐标）直接插入同名父窗口会让整个页面乱掉，已回退。**结论：分叉过的 .gui 不做"补块"，只可逐个元素做可视验证的微调；无法验证就不动。** sprite（.gfx）层面的补充相对安全（不影响布局），但 DLC 图标列的"未启用"状态不吃 banner sprite，补齐后显示无变化——不要把它当解决方案。
'''
if '实测警示（同日回退）' not in t:
    t = t.rstrip('\r\n') + '\n' + CAUTION + '\n'
io.open(fp, 'wb').write(t.encode('utf-8'))
print('version-adapt.md 已加警示 ✓')

# 2) 版本 2.21 → 2.22
s = io.open(os.path.join(SK, 'SKILL.md'), 'rb').read().decode('utf-8-sig')
s = s.replace('version: 2.21', 'version: 2.22').replace('版本：v2.21', '版本：v2.22').replace('当前版本 **v2.21**', '当前版本 **v2.22**')
io.open(os.path.join(SK, 'SKILL.md'), 'wb').write(s.encode('utf-8'))
for f in ('SKILL.md', 'references/version-adapt.md'):
    shutil.copy2(os.path.join(SK, f.replace('/', os.sep)), os.path.join(CL, f.replace('/', os.sep)))
print('skill v2.22 + .claude 同步 ✓')

# 3) gamma-mod-progress 的 10-17 段更正
M = r'C:\Users\LR\.zcode\cli\memories\projects\ilyich-genshin-test-version-57bab93f04048e34\memory\gamma-mod-progress.md'
mt = io.open(M, 'rb').read().decode('utf-8-sig')
old = '## 10-17 三个 UI bug（全修，日志归零）'
new = '## 10-17 三个 UI bug（**修复已全部回退，未解决**）'
mt = mt.replace(old, new)
# 追加回退说明（插到该节标题后第一行之前不易定位，直接在该节末尾补一句）
idx = mt.find('## 10-17 三个 UI bug')
if idx != -1 and '已按用户要求全部回退' not in mt:
    mt = mt.rstrip('\r\n') + '\n- **回退（10-17）**：用户实测 DLC 图标列无变化、选国页面全乱 → 5 个 interface 文件已恢复到改前（core.gfx 39863B / frontendmainview.gfx 5348B / frontendgamesetupview.gui 53676B / frontendgamesetupview.gfx 9046B / frontendmainview.gui 16094B，双副本一致）。教训：分叉 .gui 不能直接补原版元素块。\n'
io.open(M, 'wb').write(mt.encode('utf-8'))
print('gamma-mod-progress 已更正 ✓')

# 4) MEMORY.md 行
mi = os.path.join(os.path.dirname(M), 'MEMORY.md')
s2 = io.open(mi, 'rb').read().decode('utf-8-sig')
s2 = s2.replace('— 症状→旧副本文件→缺失项对照表（DLC 图标列/选国排序/社媒图标），日志点名法',
                '— 根因对照表+诊断法；**修复已回退未解**（分叉 .gui 勿直接补块）')
s2 = s2.replace('hoi4-modder-cn（猫妖，v2.21；', 'hoi4-modder-cn（猫妖，v2.22；')
io.open(mi, 'wb').write(s2.encode('utf-8'))
print('MEMORY.md ✓')
