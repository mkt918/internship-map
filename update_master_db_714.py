# -*- coding: utf-8 -*-
"""
260714_企業データ.csv / 260714_生徒データ.csv を最新版として更新する。
- 企業マスターDB.csv: 座標・業種カテゴリは既存継承、他は新データで上書き
  (希望者0名/受入×/欠席の企業は除外)
- 生徒データ: 260714の141名をそのまま採用(既に長欠3名は除外済み)
"""
import csv

BASE = r'C:\antigravity\public\00_作業\2026-06\インターンシップ管理'

# ── 企業データ読み込み（1行目はタイトル行なのでスキップ） ──
with open(BASE + r'\260714_企業データ.csv', encoding='utf-8-sig') as f:
    lines = f.readlines()
import io
new_comp = {}
for r in csv.DictReader(io.StringIO(''.join(lines[1:]))):
    no = r['No.'].strip()
    if not no:
        continue
    name = r['企業名'].strip()
    if '希望者0名' in name or '受け入れ×' in name or '欠席' in name:
        continue
    new_comp[no] = r

old_comp = {}
with open(BASE + r'\企業マスターDB.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        old_comp[r['No'].strip()] = r

OUT_HEADER = [
    'No', '企業名', '業種カテゴリ', '業種詳細', '住所', '緯度', '経度',
    '総人数', '当日ご担当者', '当日緊急連絡先', '実施時間', '集合時間', '集合場所',
    'アクセス', '自転車可', '駐輪場', '当日受付方法', '体験業務内容', '体験上の注意点',
    '服装・持ち物', '昼食について',
    '受入対象学科', '1日の最大受入人数',
    '受入_1年', '受入_2年', '受入可能日程', '特記事項'
]

merged_rows = []
added = []
for no in sorted(new_comp):
    n = new_comp[no]
    o = old_comp.get(no, {})
    if no not in old_comp:
        added.append((no, n['企業名'].strip()))
    merged_rows.append([
        no,
        n['企業名'].strip(),
        o.get('業種カテゴリ', '').strip(),
        o.get('業種詳細', '').strip(),
        n.get('受け入れ先住所', '').strip() or o.get('住所', '').strip(),
        o.get('緯度', '').strip(),
        o.get('経度', '').strip(),
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
        n.get('受入対象学科', '').strip(),
        n.get('1日の最大受入人数', '').strip(),
        o.get('受入_1年', '').strip(),
        o.get('受入_2年', '').strip(),
        o.get('受入可能日程', '').strip(),
        o.get('特記事項', '').strip(),
    ])

removed = [(no, old_comp[no]['企業名']) for no in old_comp if no not in new_comp]

with open(BASE + r'\企業マスターDB.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(OUT_HEADER)
    w.writerows(merged_rows)

log = [f'企業マスターDB: {len(merged_rows)}社に更新']
if added:
    log.append(f'新規追加: {added}')
if removed:
    log.append(f'除外: {removed}')

with open(BASE + r'\_update_log714.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(log))

print('done')
