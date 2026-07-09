# -*- coding: utf-8 -*-
"""
260710_企業データ.csv / 260710_生徒データ.csv を最新版として全データを更新する。
- 企業マスターDB.csv: 座標・業種カテゴリ・受入可能日程・受入学年は既存を継承しつつ、
  新データの詳細項目（担当者・連絡先・集合時間・服装等）を追加/上書き
- 生徒データ: 氏名・ふりがなを追加、長欠3名を除外、企業変更1件(2-4-22)を反映
"""
import csv

BASE = r'C:\antigravity\public\00_作業\2026-06\インターンシップ管理'

# ── 企業マスターDB更新 ──
old_comp = {}
with open(BASE + r'\企業マスターDB.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        old_comp[r['No'].strip()] = r

new_comp = {}
with open(BASE + r'\260710_企業データ.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        no = r['No.'].strip()
        new_comp[no] = r

OUT_HEADER = [
    'No', '企業名', '業種カテゴリ', '業種詳細', '住所', '緯度', '経度',
    '総人数', '当日ご担当者', '当日緊急連絡先', '実施時間', '集合時間', '集合場所',
    'アクセス', '自転車可', '駐輪場', '当日受付方法', '体験業務内容', '体験上の注意点',
    '服装・持ち物', '昼食について',
    '受入_1年', '受入_2年', '受入可能日程', '特記事項'
]

merged_rows = []
removed = []
for no in sorted(old_comp):
    if no not in new_comp:
        removed.append((no, old_comp[no]['企業名']))
        continue
    o = old_comp[no]
    n = new_comp[no]
    merged_rows.append([
        no,
        n['企業名'].strip(),
        o['業種カテゴリ'].strip(),
        o['業種詳細'].strip(),
        n['受け入れ先住所'].strip() or o['住所'].strip(),
        o['緯度'].strip(),
        o['経度'].strip(),
        n.get('総人数', '').strip(),
        n.get('当日ご担当者', '').strip(),
        n.get('当日緊急連絡先', '').strip(),
        n.get('実施時間', '').strip(),
        n.get('集合時間', '').strip(),
        n.get('集合場所', '').strip(),
        n.get('アクセス', '').strip(),
        n.get('自転車での\n訪問の可否', '').strip(),
        n.get('自転車訪問の場合\n駐輪場', '').strip(),
        n.get('当日受付方法', '').strip(),
        n.get('体験業務内容', '').strip(),
        n.get('体験上の注意点', '').strip(),
        n.get('服装・持ち物について', '').strip(),
        n.get('昼食について', '').strip(),
        o['受入_1年'].strip(),
        o['受入_2年'].strip(),
        o['受入可能日程'].strip(),
        o['特記事項'].strip(),
    ])

with open(BASE + r'\企業マスターDB.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(OUT_HEADER)
    w.writerows(merged_rows)

log = []
log.append(f'企業マスターDB: {len(merged_rows)}社に更新（除外: {removed}）')

# ── 生徒データ更新 ──
students = []
with open(BASE + r'\260710_生徒データ.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        students.append(r)

absent = [r for r in students if '欠席' in r.get('備考', '')]
active = [r for r in students if '欠席' not in r.get('備考', '')]

log.append(f'\n生徒データ: 総数{len(students)}名 / 欠席除外{len(absent)}名 / 実施対象{len(active)}名')
for r in absent:
    log.append(f'  除外: {r["学年"]}-{r["組"]}-{r["番号"]} {r["氏名"]} ({r["備考"]})')

changed = [r for r in active if '変更済み' in r.get('備考', '') or r.get('備考', '').strip() not in ('',)]
for r in changed:
    if '変更' in r.get('備考', ''):
        log.append(f'  企業変更: {r["学年"]}-{r["組"]}-{r["番号"]} {r["氏名"]} -> {r["インターン企業名"]} ({r["備考"]})')

with open(BASE + r'\260710_生徒データ_有効分.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(list(students[0].keys()))
    for r in active:
        w.writerow(list(r.values()))

with open(BASE + r'\_update_log.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(log))

print('done')
