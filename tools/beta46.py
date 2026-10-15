import os, io, re

G1 = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\Daybreak of Teyvat Gamma Version\map\strategicregions\DOT_Strategicregions_01.txt'
B46 = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV\mod\Daybreak of Teyvat Beta Version\map\strategicregions\DOT_Strategicregions_46.txt'
OUT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version\tools\beta46_out.txt'
o = []

raw1 = io.open(G1, 'rb').read()
t1 = raw1.decode('utf-8-sig', errors='replace')
o.append(f'Gamma R1: {len(raw1)}B, BOM={raw1[:3] == bytes([0xef,0xbb,0xbf])}')
o.append(f'  naval_terrain 出现: {t1.count("naval_terrain")}')
for m in re.finditer(r'naval_terrain\s*=\s*(\w+)', t1):
    o.append(f'  naval_terrain = {m.group(1)}')
# 顶层字段
tops = re.findall(r'\n\t([a-z_]+)=', t1.replace('\r', ''))
o.append(f'  R1 顶层字段（去重）: {sorted(set(tops))}')

rawb = io.open(B46, 'rb').read()
tb = rawb.decode('utf-8-sig', errors='replace')
o.append('')
o.append(f'Beta R46: {len(rawb)}B, BOM={rawb[:3] == bytes([0xef,0xbb,0xbf])}')
o.append(f'  CRLF={rawb.count(b"\r\n")}, LF={rawb.count(b"\n")}, CR={rawb.count(b"\r")}, \\r\\r\\n={rawb.count(b"\r\r\n")}')
topsb = re.findall(r'\n\t([a-z_]+)=', tb.replace('\r', ''))
o.append(f'  B46 顶层字段（去重）: {sorted(set(topsb))}')

# Gamma R1 的 weather 块尾部 3 行 + Beta R46 weather 块 = 是否同值？
def weather_values(text):
    i = text.find('weather={')
    seg = text[i:]
    vals = {}
    for m in re.finditer(r'(between|temperature|no_phenomenon|rain_light|rain_heavy|snow|blizzard|arctic_water|mud|sandstorm|min_snow_level)=\{?\s*([\d.\s\-]+)\}?', seg):
        vals.setdefault(m.group(1), []).append(m.group(2).strip())
    return vals

w1 = weather_values(t1)
wb = weather_values(tb)
o.append('')
o.append('Gamma R1 weather 值 vs Beta R46 weather 值（对比）:')
for k in ['between', 'temperature', 'no_phenomenon', 'rain_light', 'rain_heavy', 'snow', 'blizzard', 'arctic_water', 'mud', 'sandstorm', 'min_snow_level']:
    a = w1.get(k, [])
    b = wb.get(k, [])
    o.append(f'  {k}: R1={a}')
    o.append(f'  {" " * len(k)}  B46={b}')
    o.append(f'  {" " * len(k)}  相同={a == b}')

io.open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('ok')
