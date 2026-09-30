# -*- coding: utf-8 -*-
"""
大区归属的单一真源：从模组自身文件读取，避免手工维护列表漏项。

  · 分组取自 common/scripted_triggers/DOT_scripted_triggers.txt 的
    Is_MOT / Is_LYY / Is_INA / Is_SUM / Is_FON / Is_NAT
  · 挪德卡莱(NDK)、至冬(SNE) 不在触发器里，按主写给的顺序单独成组
  · 其余 tag 归入「其他国家」
  · 中文国名取自 localisation/simp_chinese
"""
import os, re
import functools

ROOT = r'C:\Users\LR\Documents\GitHub\Ilyich-Genshin-Test-Version'
G = os.path.join(ROOT, 'Daybreak of Teyvat Gamma Version')
TRIGGERS = os.path.join(G, 'common', 'scripted_triggers', 'DOT_scripted_triggers.txt')
SC = os.path.join(G, 'localisation', 'simp_chinese')
COUNTRIES = os.path.join(G, 'history', 'countries')

# 触发器名 -> 大区显示名（顺序即输出顺序）
TRIGGER_REGION = [('Is_MOT', '蒙德'), ('Is_LYY', '璃月'), ('Is_INA', '稻妻'),
                  ('Is_SUM', '须弥'), ('Is_FON', '枫丹'), ('Is_NAT', '纳塔')]
# 不在触发器里、但主写指定要单独成组的
EXTRA_REGION = [('挪德卡莱', 'NDK'), ('至冬', 'SNE')]
OTHER = '其他国家'


def _read(p):
    return open(p, encoding='utf-8-sig', errors='replace').read()


def parse_trigger_groups(path=TRIGGERS):
    """返回 {大区名: [tag, ...]}，顺序与文件里一致"""
    txt = _read(path)
    groups = {}
    for trig, region in TRIGGER_REGION:
        m = re.search(rf'\b{trig}\s*=\s*\{{(.*?)\n\}}', txt, re.S)
        if not m:
            raise ValueError(f'找不到触发器 {trig}')
        tags = re.findall(r'original_tag\s*=\s*([A-Za-z_][A-Za-z0-9_]*)', m.group(1))
        seen, uniq = set(), []
        for t in tags:
            if t not in seen:
                seen.add(t)
                uniq.append(t)
        groups[region] = uniq
    return groups


def load_regions():
    """返回 [(大区名, 主国, [属国...]), ...]，最后一项固定为其他国家"""
    g = parse_trigger_groups()
    regs = []
    for trig, region in TRIGGER_REGION:
        tags = g[region]
        regs.append((region, tags[0], tags[1:]))
    for region, tag in EXTRA_REGION:
        regs.append((region, tag, []))
    return regs


def region_order(regs=None):
    regs = regs or load_regions()
    return [r[0] for r in regs] + [OTHER]


def region_of():
    """{tag: 大区名}"""
    out = {}
    for name, main, subs in load_regions():
        out[main] = name
        for s in subs:
            out[s] = name
    return out


def rank_of():
    """{tag: 组内序号}，主国为 0"""
    out = {}
    for name, main, subs in load_regions():
        out[main] = 0
        for i, s in enumerate(subs, 1):
            out[s] = i
    return out


@functools.lru_cache(maxsize=1)
def _loc_names():
    """从 simp_chinese 抽所有 TAG 的中文名"""
    names = {}
    prefer = {}
    for f in sorted(os.listdir(SC)):
        if not f.endswith('.yml'):
            continue
        for line in _read(os.path.join(SC, f)).splitlines():
            m = re.match(r'\s*([A-Z][A-Z0-9_a-z]{1,8}?):(?:\d+)?\s*"(.*)"\s*$', line)
            if not m:
                continue
            key, val = m.group(1), m.group(2)
            # 主键 TAG，退而求其次 TAG_DEF / TAG_ADJ
            if re.fullmatch(r'[A-Z]{2,5}', key):
                tag, base = key, True
            elif re.fullmatch(r'[A-Z]{2,5}_(?:DEF|ADJ)', key):
                tag, base = key.split('_')[0], False
            else:
                continue
            pri = 2
            if f.startswith('DOT_countries') or f == 'countries_l_simp_chinese.yml':
                pri = 0
            elif f.startswith(tag):
                pri = 1
            # 同优先级下，主键 TAG 比 _DEF/_ADJ 更该被采用
            score = (pri, 0 if base else 1)
            if tag not in names or score < prefer.get(tag, (9, 9)):
                names[tag] = val
                prefer[tag] = score
    return names


def tag_cn(tag):
    return _loc_names().get(tag, tag)


def all_country_tags():
    """history/countries 下定义的全部 tag"""
    tags = []
    for f in sorted(os.listdir(COUNTRIES)):
        m = re.match(r'([A-Za-z]{3})\s*-', f) or re.match(r'([A-Za-z]{3})\.txt', f)
        if m:
            tags.append(m.group(1).upper())
    return tags


def tag_en(tag):
    """从文件名取英文名"""
    for f in os.listdir(COUNTRIES):
        if f.upper().startswith(tag.upper()):
            base = os.path.splitext(f)[0]
            return base.split('-', 1)[1].strip() if '-' in base else ''
    return ''


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    for name, main, subs in load_regions():
        print(f'{name}: {main}={tag_cn(main)}　属国 ' +
              '  '.join(f'{s}={tag_cn(s)}' for s in subs))
    reg = region_of()
    allt = all_country_tags()
    print()
    print('未归入任何大区的国家 tag（全部国家定义 %d 个）:' % len(allt))
    print('  ', '  '.join(f'{t}={tag_cn(t)}' for t in allt if t not in reg))
