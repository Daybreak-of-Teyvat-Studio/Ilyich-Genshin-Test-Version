import os, io

SKILL = r'C:\Users\LR\.zcode\skills\hoi4-modder-cn'
kws = ['全量', '重排', '迁移', '补号', '连号', '简单']
out = []
for dirpath, dirnames, filenames in os.walk(SKILL):
    if '__pycache__' in dirpath:
        continue
    for fn in filenames:
        if not fn.lower().endswith(('.md', '.txt', '.py')):
            continue
        fp = os.path.join(dirpath, fn)
        try:
            t = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace')
        except Exception as e:
            out.append(f'!! {fp}: {e}')
            continue
        rel = os.path.relpath(fp, SKILL)
        for i, line in enumerate(t.splitlines(), 1):
            for kw in kws:
                if kw in line:
                    out.append(f'{rel}:{i}: {line.strip()[:150]}')
                    break

io.open(r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\skill_grep_out.txt', 'w', encoding='utf-8').write('\n'.join(out))
print(f'{len(out)} lines -> skill_grep_out.txt')
