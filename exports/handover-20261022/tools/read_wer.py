# -*- coding: utf-8 -*-
"""read_wer.py —— 读 12:51 崩溃的 WER 报告：异常/栈/模块"""
import sys, glob, os

sys.stdout.reconfigure(encoding='utf-8')
d = glob.glob(r'C:\ProgramData\Microsoft\Windows\WER\ReportArchive\AppCrash_hoi4*12*')
cands = sorted(glob.glob(r'C:\ProgramData\Microsoft\Windows\WER\ReportArchive\AppCrash_hoi4*'),
               key=os.path.getmtime, reverse=True)
p = os.path.join(cands[0], 'Report.wer')
print('读:', p)
raw = open(p, 'rb').read()
try:
    t = raw.decode('utf-16-le')
except Exception:
    t = raw.decode('utf-8', errors='replace')
ls = t.splitlines()
print(f'共 {len(ls)} 行')
print()
for i, l in enumerate(ls):
    if any(k in l for k in ('EventType', 'Sig[', 'DynamicSig[', 'Stack', 'FriendlyEventName',
                            'ConsentKey', 'AppName', 'AppPath', 'ReportDescription',
                            'TargetAppId', 'Response.Bucket')):
        if 'LoadedModule' in l:
            continue
        print(f'{i+1}: {l[:200]}')
