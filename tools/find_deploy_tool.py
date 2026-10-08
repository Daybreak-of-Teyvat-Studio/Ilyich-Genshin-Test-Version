# -*- coding: utf-8 -*-
"""find_deploy_tool.py —— 找仓库里引用 Paradox mod 目录的部署/同步脚本"""
import os, sys, re

sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
PAT = re.compile(r'Paradox Interactive[\\/]Hearts of Iron IV[\\/]mod', re.I)
hits = []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in ('.backups', '.git', 'node_modules', '__pycache__')]
    for f in fn:
        if not f.endswith(('.py', '.bat', '.cmd', '.ps1', '.md', '.txt', '.json')):
            continue
        p = os.path.join(dp, f)
        try:
            t = open(p, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        if PAT.search(t):
            hits.append(os.path.relpath(p, ROOT))
print(f'引用 Paradox mod 目录的文件 {len(hits)} 个:')
for h in hits[:40]:
    print(' ', h)
