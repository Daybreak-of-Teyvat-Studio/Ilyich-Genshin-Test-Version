# -*- coding: utf-8 -*-
import io, sys
sys.stdout.reconfigure(encoding='utf-8')
M = r'C:\Users\LR\.zcode\cli\memories\projects\ilyich-genshin-test-version-57bab93f04048e34\memory'
p1 = M + r'\MEMORY.md'
t = io.open(p1, 'rb').read().decode('utf-8-sig')
t = t.replace('hoi4-modder-cn（猫妖，v2.00；', 'hoi4-modder-cn（猫妖，v2.10；')
io.open(p1, 'wb').write(t.encode('utf-8'))
print('MEMORY.md:', [l for l in t.splitlines() if 'skill 结构' in l][0][:120])
p2 = M + r'\hoi4-skill-structure.md'
t2 = io.open(p2, 'rb').read().decode('utf-8-sig')
t2 = t2.replace('**skill 已到 v2.00，包过期', '**skill 已到 v2.10，包过期')
io.open(p2, 'wb').write(t2.encode('utf-8'))
print('分发产物行 ok:', 'v2.10' in t2)
