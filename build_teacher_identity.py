# -*- coding: utf-8 -*-
"""
巡回教員の「実在の担当者」割当を再構築する。
- 1教員あたり最大2日までしか担当しない（MAX_DAYS_PER_TEACHER）
- 同じ教員は同じ日に2ルートを担当できない（日ごとに1ルート=1教員なので自動的にOK）
- 必要な教員数は動的に増やす（各日、残り枠のある教員から負荷が少ない順に割当）
- 7/17(金)4限に全員でまとめて事前指導を行うため、教員ごとに
  「summer全体で自分が回る全生徒」を1グループとして集約する
"""
import json
import re

BASE = r'C:\antigravity\public\00_作業\2026-06\インターンシップ管理'
MAX_DAYS_PER_TEACHER = 2

with open(BASE + r'\patrol_routes.json', encoding='utf-8') as f:
    data = json.load(f)


def dsort(d):
    m = re.search(r'(\d+)/(\d+)', d)
    return (int(m.group(1)), int(m.group(2))) if m else (99, 99)


days = sorted(data, key=lambda d: dsort(d['date']))

load = {}          # teacher_id -> total students
day_count = {}      # teacher_id -> number of days assigned
assign_history = {}  # teacher_id -> [(date, route), ...]
next_id = 1


def new_teacher():
    global next_id
    tid = next_id
    load[tid] = 0
    day_count[tid] = 0
    assign_history[tid] = []
    next_id += 1
    return tid


for day in days:
    routes = sorted(day['routes'], key=lambda r: r['n_students'], reverse=True)
    for route in routes:
        # その日まだ割当されておらず、2日未満の教員から負荷最小を選ぶ
        candidates = [t for t in load if day_count[t] < MAX_DAYS_PER_TEACHER
                      and day['date'] not in [d for d, _ in assign_history[t]]]
        if candidates:
            tid = min(candidates, key=lambda t: (day_count[t], load[t]))
        else:
            tid = new_teacher()
        assign_history[tid].append((day['date'], route))
        load[tid] += route['n_students']
        day_count[tid] += 1

n_teachers = len(assign_history)

lines = []
for t in sorted(assign_history):
    hist = assign_history[t]
    total_stu = sum(r['n_students'] for _, r in hist)
    dates = [d for d, _ in hist]
    lines.append(f'教員{t}: 合計{total_stu}名 / 担当{len(hist)}日 / 日程{dates}')
lines.append(f'\n必要教員数: {n_teachers}名')

with open(BASE + r'\_teacher_balance.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

out = {}
for t, hist in assign_history.items():
    out[str(t)] = [
        {
            'date': d,
            'teacher_slot': r['teacher'],
            'n_students': r['n_students'],
            'n_companies': r['n_companies'],
            'companies': [s['name'] for s in r['stops']],
            'students': [s for stop in r['stops'] for s in stop['students']],
            'total_km': r['total_km'],
        }
        for d, r in hist
    ]

with open(BASE + r'\teacher_identity.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print('done')
