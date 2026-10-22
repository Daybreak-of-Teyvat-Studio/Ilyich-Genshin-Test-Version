import os, io, re

repo = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
depl = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'

out = []
for label, root in [('仓库', repo), ('副本', depl)]:
    sd = os.path.join(root, 'history', 'states')
    ids = []
    for fn in os.listdir(sd):
        m = re.match(r'^(\d+)-State_\1\.txt$', fn)
        if m:
            ids.append(int(m.group(1)))
    ids.sort()
    holes = [i for i in range(1, max(ids) + 1) if i not in set(ids)]
    out.append(f'{label}: {len(ids)} 州文件, max={max(ids)}, 缺号={holes if holes else "无"}')
    # 尾部 703-709 是否残留旧文件
    res = [i for i in (703, 704, 705, 706, 707, 708, 709, 718) if i in set(ids)]
    out.append(f'  旧号残留(703-709/718): {res if res else "无"}')
    # 63/65/66/67 的注释
    for n in (63, 65, 66, 67, 89, 90, 94):
        fp = os.path.join(sd, f'{n}-State_{n}.txt')
        if os.path.exists(fp):
            head = io.open(fp, 'rb').read().decode('utf-8-sig', errors='replace').splitlines()[:4]
            com = [l for l in head if 'name=' in l]
            out.append(f'  s{n}: {com[0].strip()[:80] if com else "??"}')

io.open(r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\verify702.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')
