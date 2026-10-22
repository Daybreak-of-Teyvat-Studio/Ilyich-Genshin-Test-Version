import os, io

SKILL = r'C:\Users\LR\.zcode\skills\hoi4-modder-cn'
kws = ['全量迁移', '简单迁移', '版本', 'v1.99', 'v2.00', '2.00', '1.99']
out = []
for dirpath, dirnames, filenames in os.walk(SKILL):
    if '__pycache__' in dirpath:
        continue
    for fn in filenames:
        if not fn.lower().endswith(('.md', '.txt')):
            continue
        fp = os.path.join(dirpath, fn)
        t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        rel = os.path.relpath(fp, SKILL)
        for i, line in enumerate(t.splitlines(), 1):
            for kw in kws:
                if kw in line:
                    out.append(f'{rel}:{i}: {line.strip()[:160]}')
                    break

io.open(r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\skill_check_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print(f'{len(out)} lines')
