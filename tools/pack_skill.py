# -*- coding: utf-8 -*-
"""pack_skill.py —— 打包 hoi4-modder-cn v1.8 内测包到桌面
排除：config.json（含本机路径）、__pycache__、.gitignore"""
import os, sys, shutil, zipfile, datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.expanduser('~'), '.zcode', 'skills', 'hoi4-modder-cn')
STAGE = os.path.join(ROOT, '.scratch', 'pack_skill')
OUT = os.path.join(os.path.expanduser('~'), 'Desktop', 'hoi4-modder-cn-v1.8-内测版.zip')

NOTE = """HOI4 模组开发助手 hoi4-modder-cn · 内测版 v1.8
制作：猫妖
=============================================

【这是什么】
一个给 AI 助手（ZCode / Claude Code 等）用的 HOI4 模组开发技能包。
安装后对 AI 说「我要制作一个钢铁雄心4的XX mod」即可进入引导流程：
配置目录 → 选择任务 → 路线图确认 → 逐项制作（带验证点）。
也支持：挪省改州 / 州合并补号（自动迁移 id 关联的修正和本地化）/ 建筑高程修复 /
备份回滚 / 双自检关卡 / 闪退排查。

【安装方法】
把 hoi4-modder-cn 整个文件夹放到 AI 助手的 skills 目录：

· ZCode：      C:\\Users\\<你>\\.zcode\\skills\\hoi4-modder-cn
· Claude Code：C:\\Users\\<你>\\.claude\\skills\\hoi4-modder-cn

（两个都装也可以。）放好后重启 / 新开会话，对 AI 说
「我要制作一个钢铁雄心4的 mod」即可触发。

【首次使用】
AI 会引导你配置两个路径（只配一次）：
1. 钢铁雄心4 游戏根目录（只读参考，绝不写入）
2. 你的 mod 工作目录

【推荐配套（可选）】
· superpowers-zh 技能框架：npx superpowers-zh
· rhoiscribe-hoi4 资源包：https://github.com/czxieddan/RHoiScribe

【内容清单】
SKILL.md                       主引导（独特功能/铁律/分派/工作流）
references/user-guide.md       用户指引（引导流程/场景脚本/速查表）
references/task-roadmaps.md    任务路线图（18 类任务）
references/paradox-syntax.md   Paradox 语法与模板
references/map-data.md         省↔州数据一致性 + 语法关
references/gamma-pipeline.md   地图改造流水线实战经验（挪省/合并/补号/VP/地形）
references/buildings-height.md 建筑高程与防穿模（绿豆糕模块）
references/stat-keys.md        stat key 中英对照
references/icons-dds.md        单位图标规格
references/landmarks-3d.md     3D 地标工具链
references/version-adapt.md    版本适配
references/ra-notes.md         项目经验示例（可换成你自己的）
references/*doctrine*          主/子学说教程（猫妖团队）
references/unit-categories-参考.txt  单位类别白名单参考
scripts/                       可执行工具（高程修复/防穿模/补号/备份/双自检）

【内测注意】
· 请勿把本包与你本机的 config.json（含本机路径）再分发
· 遇到问题/bug 请记录：做了什么操作 + AI 的报错输出
· 游戏根目录永远是只读参考
· 内测反馈请发给猫妖
"""

if os.path.exists(STAGE):
    shutil.rmtree(STAGE)
os.makedirs(STAGE)
pkg = os.path.join(STAGE, 'hoi4-modder-cn')
shutil.copytree(SRC, pkg,
                ignore=shutil.ignore_patterns('config.json', '__pycache__', '.gitignore'))
open(os.path.join(STAGE, '安装说明-先看.txt'), 'w', encoding='utf-8-sig', newline='\r\n').write(NOTE)

if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for dp, dn, fn in os.walk(STAGE):
        for f in fn:
            p = os.path.join(dp, f)
            z.write(p, os.path.relpath(p, STAGE))
shutil.rmtree(STAGE)

# 验证
with zipfile.ZipFile(OUT) as z:
    names = z.namelist()
    bad = [n for n in names if 'config.json' in n or '__pycache__' in n]
    print(f'打包完成: {OUT}')
    print(f'大小: {os.path.getsize(OUT) / 1024:.0f} KB，文件 {len(names)} 个')
    print(f'敏感文件检查: {"✓ 无 config.json/__pycache__" if not bad else "✗ " + str(bad)}')
    print(f'修改时间: {datetime.date.today()}')
    for n in sorted(names)[:8]:
        print('  ' + n)
    print('  ...')
