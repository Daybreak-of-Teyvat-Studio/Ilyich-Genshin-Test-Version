# -*- coding: utf-8 -*-
import io, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
SK = r'C:\Users\LR\.zcode\skills\hoi4-modder-cn'
fp = os.path.join(SK, 'SKILL.md')
t = io.open(fp, 'rb').read().decode('utf-8-sig')
t = t.replace('version: 2.00', 'version: 2.10')
t = t.replace('版本：v2.00', '版本：v2.10')
t = t.replace('当前版本 **v2.00**', '当前版本 **v2.10**')
io.open(fp, 'wb').write(t.encode('utf-8'))
chk = io.open(fp, 'rb').read().decode('utf-8-sig')
print('--- 版本行 ---')
for l in chk.splitlines():
    if '2.10' in l:
        print('  ' + l.strip()[:130])
CL = r'C:\Users\LR\.claude\skills\hoi4-modder-cn'
for f in ('SKILL.md', 'references/gamma-pipeline.md'):
    src = os.path.join(SK, f.replace('/', os.sep))
    dst = os.path.join(CL, f.replace('/', os.sep))
    shutil.copy2(src, dst)
    print(f'同步 .claude: {f}  {os.path.getsize(dst)}B')
