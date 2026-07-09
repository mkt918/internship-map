# -*- coding: utf-8 -*-
"""
15名教員体制での 7/17(金)4限 教室割当プラン
- 15名を 1教室2名ペアで割り振り（15名 → 7ペア+1名単独 = 8教室）
- 大小ペアリングで教室ごとの生徒数合計を平準化
"""
import json

BASE = r'C:\antigravity\public\00_作業\2026-06\インターンシップ管理'

with open(BASE + r'\teacher_identity.json', encoding='utf-8') as f:
    teachers = json.load(f)

items = []
for tid_str, routes in teachers.items():
    total_stu = sum(r['n_students'] for r in routes)
    items.append({'teacher': int(tid_str), 'routes': routes, 'total_students': total_stu})

sorted_items = sorted(items, key=lambda x: x['total_students'], reverse=True)
pairs = []
lo, hi = 0, len(sorted_items) - 1
while lo <= hi:
    if lo == hi:
        pairs.append([sorted_items[lo]])
    else:
        pairs.append([sorted_items[lo], sorted_items[hi]])
    lo += 1
    hi -= 1

result = []
for room_no, pair in enumerate(pairs, 1):
    total = sum(p['total_students'] for p in pair)
    result.append({'room': room_no, 'teachers': pair, 'total_students': total})

with open(BASE + r'\classroom_plan15.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

lines = []
for r in result:
    names = ' / '.join(f'教員{p["teacher"]}({p["total_students"]}名,{len(p["routes"])}日)' for p in r['teachers'])
    lines.append(f'教室{r["room"]}: {names}  合計{r["total_students"]}名')

with open(BASE + r'\_classroom15_view.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('done')
