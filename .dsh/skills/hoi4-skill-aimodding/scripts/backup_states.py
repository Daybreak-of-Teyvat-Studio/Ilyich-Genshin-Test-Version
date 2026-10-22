# -*- coding: utf-8 -*-
"""
backup_states.py —— state 数据一键备份/回退

修改任何 province / state 之前先跑一次备份；出问题用 --restore 一键回退。

备份内容：history/states/*.txt（全部州文件）+ map/buildings.txt
备份位置：<mod同级的>.backups/states_<时间戳>/

用法:
    python backup_states.py --mod <mod根目录>                    # 备份
    python backup_states.py --mod <mod根目录> --restore <备份目录>  # 一键回退
    python backup_states.py --mod <mod根目录> --list               # 列出全部备份
"""
import os, re, sys, glob, shutil, argparse, datetime

ap = argparse.ArgumentParser(description='state 数据备份/回退')
ap.add_argument('--mod', required=True, help='mod 根目录')
ap.add_argument('--restore', help='回退到指定备份目录')
ap.add_argument('--list', action='store_true', help='列出全部备份')
args = ap.parse_args()
MOD = os.path.normpath(args.mod)
ST = os.path.join(MOD, 'history', 'states')
BP = os.path.join(MOD, 'map', 'buildings.txt')
sys.stdout.reconfigure(encoding='utf-8')

BAK_ROOT = os.path.normpath(os.path.join(MOD, '..', '.backups'))
if os.path.basename(os.path.dirname(MOD)) == '.backups':
    BAK_ROOT = os.path.join(MOD + '_backups')


def states_dir(bdir):
    return os.path.join(bdir, 'history', 'states') if os.path.isdir(
        os.path.join(bdir, 'history', 'states')) else bdir


def do_backup():
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bdir = os.path.join(BAK_ROOT, 'states_' + stamp)
    os.makedirs(os.path.join(bdir, 'history', 'states'), exist_ok=True)
    os.makedirs(os.path.join(bdir, 'map'), exist_ok=True)
    n = 0
    for f in os.listdir(ST):
        if f.endswith('.txt'):
            shutil.copy2(os.path.join(ST, f), os.path.join(bdir, 'history', 'states', f))
            n += 1
    if os.path.exists(BP):
        shutil.copy2(BP, os.path.join(bdir, 'map', 'buildings.txt'))
    print(f'备份完成: {bdir}')
    print(f'  州文件 {n} 个 + buildings.txt')


def do_restore(src):
    src_states = states_dir(src)
    assert os.path.isdir(src_states), f'备份目录无效: {src}'
    # 安全网：回退前先备份当前状态
    cur = os.path.join(BAK_ROOT, 'pre_restore_' +
                       datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(os.path.join(cur, 'history', 'states'), exist_ok=True)
    os.makedirs(os.path.join(cur, 'map'), exist_ok=True)
    for f in os.listdir(ST):
        if f.endswith('.txt'):
            shutil.copy2(os.path.join(ST, f), os.path.join(cur, 'history', 'states', f))
    if os.path.exists(BP):
        shutil.copy2(BP, os.path.join(cur, 'map', 'buildings.txt'))
    print(f'当前状态已另存: {cur}')
    # 回退
    n = 0
    for f in os.listdir(src_states):
        if f.endswith('.txt'):
            shutil.copy2(os.path.join(src_states, f), os.path.join(ST, f))
            n += 1
    # 删除备份里没有的州文件（防止残留）
    keep = set(os.listdir(src_states))
    for f in os.listdir(ST):
        if f.endswith('.txt') and f not in keep:
            os.remove(os.path.join(ST, f))
            print(f'  删除多余州文件: {f}')
    src_bp = os.path.join(src, 'map', 'buildings.txt')
    if os.path.exists(src_bp) and os.path.exists(BP):
        shutil.copy2(src_bp, BP)
    print(f'回退完成: 恢复 {n} 个州文件' +
          (' + buildings.txt' if os.path.exists(src_bp) else ''))


def do_list():
    for b in sorted(glob.glob(os.path.join(BAK_ROOT, 'states_*'))):
        n = len(glob.glob(os.path.join(states_dir(b), '*.txt')))
        mt = datetime.datetime.fromtimestamp(os.path.getmtime(b))
        print(f'  {os.path.basename(b)}  ({n} 州文件)  {mt}')


if args.restore:
    do_restore(args.restore)
elif args.list:
    do_list()
else:
    do_backup()
