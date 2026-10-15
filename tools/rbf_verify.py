import os, io, shutil, collections

REPO = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version'
DEPL = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Gamma Version'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\rbf_verify_out.txt'
o = []

fp = os.path.join(REPO, 'map', 'buildings.txt')
raw = io.open(fp, 'rb').read()
# 去尾换行（原版/beta 惯例：结尾无换行）
if raw.endswith(b'\r\n'):
    raw = raw[:-2]
    io.open(fp, 'wb').write(raw)
    o.append('已去尾换行')
elif raw.endswith(b'\n'):
    raw = raw[:-1]
    io.open(fp, 'wb').write(raw)
    o.append('已去尾换行(LF)')

raw = io.open(fp, 'rb').read()
o.append(f'bytes: {len(raw)}, BOM={raw[:3] == bytes([0xef,0xbb,0xbf])}')
o.append(f'CRLF={raw.count(bytes([13,10]))}, 孤立LF={raw.count(b"\n") - raw.count(bytes([13,10]))}, 孤立CR={raw.count(b"\r") - raw.count(bytes([13,10]))}')

lines = raw.decode('utf-8-sig').split('\r\n')
o.append(f'行数 {len(lines)}')
bad = [i for i, l in enumerate(lines, 1) if len(l.split(';')) != 7]
o.append(f'非7字段行: {bad if bad else "无 ✓"}')

cnt = collections.Counter()
for l in lines:
    f = l.split(';')
    if len(f) == 7 and f[0].isdigit():
        cnt[int(f[0])] += 1
o.append('')
o.append('重点州行数（预期 62→115, 63→46, 65→51, 66→34, 67→46）:')
for s in (62, 63, 65, 66, 67, 89, 90, 94):
    o.append(f'  s{s}: {cnt.get(s, 0)}')

# 抽查：62 是否拿到 ABY 全部行；63-67 是否已无 ABY 坐标行
o.append('')
o.append('抽查 62 的 air_base 行:')
n = 0
for l in lines:
    f = l.split(';')
    if f[0] == '62' and f[1] == 'air_base':
        o.append(f'  {l[:100]}')
        n += 1
o.append(f'  （{n} 行）')

o.append('抽查 63 的坐标（前 5 行任意类型）:')
n = 0
for l in lines:
    f = l.split(';')
    if f[0] == '63' and n < 5:
        o.append(f'  {l[:100]}')
        n += 1
# 旧 ABY 坐标（2636/2638/2627/2635 等）是否还出现在 63-67
o.append('')
o.append('63-67 中仍有 ABY 坐标(2630-2660, z 840-900)的行:')
n = 0
for l in lines:
    f = l.split(';')
    try:
        x, z = float(f[2]), float(f[4])
    except Exception:
        continue
    if f[0] in ('63', '65', '66', '67') and 2620 <= x <= 2680 and 840 <= z <= 900:
        n += 1
        if n <= 5:
            o.append(f'  {l[:100]}')
o.append(f'  共 {n} 行（预期 0）')

# 同步副本
dst = os.path.join(DEPL, 'map', 'buildings.txt')
io.open(dst, 'wb').write(raw)
back = io.open(dst, 'rb').read()
o.append('')
o.append(f'副本已写入, 字节一致: {back == raw}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')
