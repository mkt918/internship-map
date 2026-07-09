# -*- coding: utf-8 -*-
"""
事前指導 教室割当プラン生成
- 33の巡回グループ(日付×教員)を、1教室あたり最大2教員、10教室以内に収まるよう
  2ラウンド(1コマ目/2コマ目)に振り分ける
- 各ルームの生徒数合計が偏らないよう、大きいグループ+小さいグループのペアリングで平準化
"""
import json
import re

BASE = r'C:\antigravity\public\00_作業\2026-06\インターンシップ管理'
MAX_ROOMS = 10
MAX_TEACHERS_PER_ROOM = 2

with open(BASE + r'\patrol_routes.json', encoding='utf-8') as f:
    data = json.load(f)


def dsort(d):
    m = re.search(r'(\d+)/(\d+)', d)
    return (int(m.group(1)), int(m.group(2))) if m else (99, 99)


# 全グループをフラット化
groups = []
for day in sorted(data, key=lambda d: dsort(d['date'])):
    for route in day['routes']:
        groups.append({
            'date': day['date'],
            'teacher': route['teacher'],
            'n_students': route['n_students'],
            'n_companies': route['n_companies'],
            'companies': [s['name'] for s in route['stops']],
            'students': [s for stop in route['stops'] for s in stop['students']],
        })

n_groups = len(groups)
print(f'総グループ数: {n_groups}')

# 大小ペアリングで各ルームの人数を平準化
sorted_groups = sorted(groups, key=lambda g: g['n_students'], reverse=True)
pairs = []
lo, hi = 0, len(sorted_groups) - 1
while lo <= hi:
    if lo == hi:
        pairs.append([sorted_groups[lo]])
    else:
        pairs.append([sorted_groups[lo], sorted_groups[hi]])
    lo += 1
    hi -= 1

print(f'必要ルーム数（2名/室ペア数）: {len(pairs)}')

# ラウンド分割: 1ラウンド最大10室
rounds = []
for i in range(0, len(pairs), MAX_ROOMS):
    rounds.append(pairs[i:i + MAX_ROOMS])

# 結果出力
result = []
for ri, round_pairs in enumerate(rounds, 1):
    for room_no, pair in enumerate(round_pairs, 1):
        total_stu = sum(g['n_students'] for g in pair)
        result.append({
            'round': ri,
            'room': room_no,
            'groups': pair,
            'total_students': total_stu,
        })

# JSON保存
with open(BASE + r'\classroom_plan.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# コンソール表示
for r in result:
    names = ' / '.join(f'{g["date"]}教員{g["teacher"]}({g["n_students"]}名)' for g in r['groups'])
    print(f'  第{r["round"]}コマ 教室{r["room"]:>2}: {names}  計{r["total_students"]}名')

print(f'\n第1コマ: 教室{len(rounds[0])}室使用')
if len(rounds) > 1:
    print(f'第2コマ: 教室{len(rounds[1])}室使用')
