# -*- coding: utf-8 -*-
"""check_launcher_db.py —— 检查 Paradox 启动器数据库与相关文件"""
import sys, os, datetime, sqlite3

sys.stdout.reconfigure(encoding='utf-8')
d = r'C:\Users\LR\Documents\Paradox Interactive\Hearts of Iron IV'
for f in ('launcher-v2.sqlite', 'launcher-v2_backup.sqlite', 'dlc_load.json', 'gameplaysettings.txt',
          'playsets_backup', 'playlists', '.launcher-cache'):
    p = os.path.join(d, f)
    if os.path.exists(p):
        t = os.path.getmtime(p)
        sz = os.path.getsize(p) if os.path.isfile(p) else '<dir>'
        print(f'{f}: {sz}  {datetime.datetime.fromtimestamp(t)}')
p = os.path.join(d, 'launcher-v2.sqlite')
try:
    con = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
    print('sqlite 完整性:', con.execute('PRAGMA integrity_check').fetchone())
    tabs = [x[0] for x in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print('表:', tabs)
    for tab in tabs:
        try:
            n = con.execute(f'SELECT COUNT(*) FROM "{tab}"').fetchone()[0]
            print(f'  {tab}: {n} 行')
        except Exception:
            pass
    con.close()
except Exception as e:
    print('sqlite 读取失败:', e)

# steelicu 数据目录
import glob
for pat in (r'C:\Users\LR\AppData\Roaming\steelicu*', r'C:\Users\LR\AppData\Local\steelicu*',
            r'C:\Users\LR\.steelicu*', r'F:\mod制作\*.json', r'F:\mod制作\*.log',
            r'F:\mod制作\config*', r'F:\mod制作\data*'):
    for hit in glob.glob(pat):
        print('steelicu 相关:', hit)
