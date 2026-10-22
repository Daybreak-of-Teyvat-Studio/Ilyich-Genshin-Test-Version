# -*- coding: utf-8 -*-
import io, sys
sys.stdout.reconfigure(encoding='utf-8')
M = r'C:\Users\LR\.zcode\cli\memories\projects\ilyich-genshin-test-version-57bab93f04048e34\memory\gamma-mod-progress.md'
t = io.open(M, 'rb').read().decode('utf-8-sig')
add = '''- **10-16 晚 第二批 VP 8 条**（备份 `.backups/vp2_20261016_233039`）：1506疗养院旧址(30)、**3223 改名改值**（疗养院旧址15 → 疗养院风神像25）、1451好肉族大锅(5)、748黑日族方碑(5)、3657好睡族大殿(5)、301野猪林(5)、3349导光机关(5)、894导光机关(5)；涉及州 392/427/433/448/511/522，VP 总数 268→275。'''
if '第二批 VP 8 条' not in t:
    t = t.rstrip('\r\n') + '\n' + add + '\n'
io.open(M, 'wb').write(t.encode('utf-8'))
print('ok')
