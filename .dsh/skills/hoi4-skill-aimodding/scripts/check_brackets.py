# -*- coding: utf-8 -*-
"""
check_brackets.py —— 括号完整性自检（与 GitHub CI ci-test/Check.py 同规则）

检测项（与 CI 完全一致）：
  1. 大括号匹配：common/ 全部 .txt / .gui（# 注释后跳过、栈式配对）
  2. 本地化中文引号：simp_chinese 全部 .yml 每行未转义双引号数必须为 0 或 2
  3. 本地化编码：simp_chinese 与 english 的 .yml 必须带 BOM（chardet 识别为 UTF-8-SIG）

用法:
    python check_brackets.py --mod <mod根目录>
退出码: 0 = 全部通过; 1 = 有问题（打印文件名+行号）
"""
import os, re, sys, argparse
try:
    import chardet
except ImportError:
    chardet = None

ap = argparse.ArgumentParser(description='括号完整性自检（大括号/引号/编码）')
ap.add_argument('--mod', required=True, help='mod 根目录')
args = ap.parse_args()
MOD = os.path.normpath(args.mod)
sys.stdout.reconfigure(encoding='utf-8')

blackList = [os.path.normpath(os.path.join(MOD, 'common', '备份文件')),
             os.path.normpath(os.path.join(MOD, '.backups'))]
n_err = 0


def in_blacklist(p):
    rp = os.path.normpath(p)
    return any(rp == b or rp.startswith(b + os.sep) for b in blackList)


# 1. 大括号匹配
def check_bracket_file(fp):
    global n_err
    ok = True
    record = []
    with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
        for index, line in enumerate(fh, 1):
            for c in line:
                if c == '#':
                    break
                elif c == '{':
                    record.append('{')
                elif c == '}':
                    if record and record[-1] == '{':
                        record.pop()
                    else:
                        print(f'文件出错: {fp} 大括号不匹配 {record}, 行号: {index}')
                        ok = False
    if record:
        print(f'文件出错: {fp} 大括号不匹配 {record}')
        ok = False
    if not ok:
        n_err += 1
    return ok


def walk_mod(exts, fn):
    for root, dirs, files in os.walk(MOD):
        if in_blacklist(root):
            dirs[:] = []
            continue
        for f in files:
            if f.endswith(exts):
                fn(os.path.join(root, f))


for root, dirs, files in os.walk(MOD):
    if in_blacklist(root):
        dirs[:] = []
        continue
    for f in files:
        if f.endswith(('.txt', '.gui')):
            check_bracket_file(os.path.join(root, f))

# 2/3. 本地化
def check_quotation(fp):
    global n_err
    ok = True
    with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
        for index, line in enumerate(fh, 1):
            cnt, last = 0, ''
            for c in line:
                if c == '#' and cnt != 1:
                    break
                elif c == '"' and last != '\\':
                    cnt += 1
                last = c
            if cnt not in (0, 2):
                print(f'文件出错: {fp} 英文双引号有问题, 行号: {index}')
                ok = False
    if not ok:
        n_err += 1
    return ok


def check_encoding(fp):
    global n_err
    raw = open(fp, 'rb').read()
    if raw[:3] == b'\xef\xbb\xbf':
        return True
    det = chardet.detect(raw)['encoding'] if chardet else 'utf-8'
    print(f'文件出错: {fp} 文件编码格式为: {det}（缺 BOM，需 utf-8-sig）')
    n_err += 1
    return False


# 引号检查仅 simp_chinese（与 CI 一致）；编码检查 simp_chinese + english
for lang in ('simp_chinese', 'english'):
    d = os.path.join(MOD, 'localisation', lang)
    if not os.path.isdir(d):
        continue
    for root, dirs, files in os.walk(d):
        for f in files:
            if f.endswith('.yml'):
                fp = os.path.join(root, f)
                if lang == 'simp_chinese':
                    check_quotation(fp)
                check_encoding(fp)

print(f'\n结果: {"全部通过 ✓" if n_err == 0 else f"{n_err} 个文件有问题"}')
sys.exit(0 if n_err == 0 else 1)
