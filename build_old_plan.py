# -*- coding: utf-8 -*-
"""
旧配置案.csv 生成スクリプト
260617_クラス名簿表フル.csv の F列（インターン企業名）を配置決定として採用し、
新配置案.csv と同じ列構成に変換する。
"""
import csv, re
from math import radians, sin, cos, sqrt, atan2

BASE = r'C:\antigravity\public\00_作業\2026-06\インターンシップ管理'
INPUT = r'C:\antigravity\public\00_作業\input\260617_クラス名簿表フル.csv'

def haversine(a, b):
    R = 6371.0
    dlat = radians(b[0]-a[0]); dlon = radians(b[1]-a[1])
    h = sin(dlat/2)**2 + cos(radians(a[0]))*cos(radians(b[0]))*sin(dlon/2)**2
    return R*2*atan2(sqrt(h), sqrt(1-h))

# ---- 企業マスターDB (No → 企業情報) ----
comp_by_no   = {}   # No → dict
comp_by_name = {}   # 企業名 → dict
with open(BASE + r'\企業マスターDB.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        no = (r.get('No') or '').strip()
        if no:
            comp_by_no[no]   = r
            comp_by_name[(r.get('企業名') or '').strip()] = r

# ---- 企業立地DB (No → 最寄り駅・路線・距離) ----
loc_by_no = {}
with open(BASE + r'\企業立地DB.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        no = (r.get('No') or '').strip()
        if no:
            loc_by_no[no] = r

# ---- 駅マスターDB (駅名 → 座標) ----
station_coords = {}
with open(BASE + r'\駅マスターDB.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        name = (r.get('駅名') or '').strip()
        try:
            station_coords[name] = (float(r['緯度']), float(r['経度']))
        except ValueError:
            pass

# ---- 生徒名簿DB (学年+組+番号 → 事前説明1業種/2業種) ----
stu_extra = {}
with open(BASE + r'\生徒名簿DB.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        key = (r['学年'].strip(), r['組'].strip(), r['番号'].strip())
        stu_extra[key] = {
            '事前説明1': (r.get('事前説明１') or '').strip(),
            '事前説明2': (r.get('事前説明２') or '').strip(),
            '事前説明1業種': (r.get('事前説明1業種') or '').strip(),
            '事前説明2業種': (r.get('事前説明2業種') or '').strip(),
        }

# ---- 希望業種の正規化 (旧CSV 希望番号 → カテゴリ) ----
PREF_MAP = {
    '1': '製造工業', '2': '製造食品', '3': '物流', '4': '販売',
    '5': '保育',     '6': '販売',     # 6=福祉・介護→販売に近いが「その他」で処理
    '7': '美容',     '8': 'その他',
    '4b': '販売',
}
def norm_pref(code):
    code = (code or '').strip()
    return PREF_MAP.get(code, 'その他')

# ---- マッチ判定 (新配置案と同じ5段階) ----
MATCH_LABEL = ['◎事前説明1', '◎事前説明2', '○第1希望', '○第2希望', '○第3希望', '[NG]不一致']
def match_level(pref_layers, comp_cats):
    cats = [c.strip() for c in comp_cats.split(',')]
    for i, p in enumerate(pref_layers):
        if p and p != 'その他' and p in cats:
            return i
    return 5

# ---- 旧名簿を処理して旧配置案を生成 ----
OLD_HEADER = [
    '学年','組','番号','性別',
    '配属企業No','企業名','業種カテゴリ','受け入れ先住所','緯度','経度',
    '日付','最寄り駅','市町','距離km',
    '業種マッチ','事前説明1','事前説明2','第1希望','第2希望','第3希望','備考'
]

def find_comp(no_raw, name_raw):
    """No. 列または企業名で企業を引く。旧CSVのNoは '5E' 形式。"""
    c = comp_by_no.get(no_raw.strip())
    if c:
        return c
    # 企業名で部分一致検索
    name_raw = name_raw.strip()
    for k, v in comp_by_name.items():
        if k == name_raw or name_raw in k or k in name_raw:
            return v
    return None

out_rows = []
warn_count = 0

with open(INPUT, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        nen  = row['学年'].strip()
        kumi = row['組'].strip()
        ban  = row['番号'].strip()
        sex  = row['性別'].strip()
        no_raw   = (row.get('No.') or '').strip()
        cname    = (row.get('インターン企業名') or '').strip()
        date_str = (row.get('日付') or '').strip()
        machi    = (row.get('市町') or '').strip()
        eki      = (row.get('最寄り駅') or '').strip()
        biko     = (row.get('備考') or '').strip()

        # 希望業種（旧CSV: 第１希望列=番号コード）
        p1 = norm_pref(row.get('第１希望') or '')
        p2 = norm_pref(row.get('第２希望') or '')
        p3 = norm_pref(row.get('第３希望') or '')

        # 企業マスターから企業情報を取得
        comp = find_comp(no_raw, cname)
        if comp:
            comp_no   = comp.get('No','').strip()
            comp_name = comp.get('企業名','').strip()
            comp_cat  = comp.get('業種カテゴリ','').strip()
            comp_addr = comp.get('住所','').strip()
            try:
                comp_lat = float(comp.get('緯度',''))
                comp_lng = float(comp.get('経度',''))
            except ValueError:
                comp_lat = comp_lng = ''
        else:
            comp_no   = no_raw
            comp_name = cname
            comp_cat  = ''
            comp_addr = ''
            comp_lat  = comp_lng = ''
            warn_count += 1
            print(f'  [WARN] 企業未マッチ: No={no_raw} 名={cname}')

        # 生徒の最寄り駅座標 → 企業までの距離
        dist_km = ''
        if eki and comp_lat != '':
            sc = station_coords.get(eki)
            if sc:
                dist_km = round(haversine(sc, (comp_lat, comp_lng)), 1)

        # 事前説明（生徒名簿DBから）
        se = stu_extra.get((nen, kumi, ban), {})
        setsu1     = se.get('事前説明1', '')
        setsu2     = se.get('事前説明2', '')
        setsu1_cat = se.get('事前説明1業種', '')
        setsu2_cat = se.get('事前説明2業種', '')

        # マッチ判定
        pref_layers = [setsu1_cat, setsu2_cat, p1, p2, p3]
        mlv = match_level(pref_layers, comp_cat) if comp_cat else 5
        match_label = MATCH_LABEL[mlv]

        out_rows.append([
            nen, kumi, ban, sex,
            comp_no, comp_name, comp_cat, comp_addr,
            comp_lat if comp_lat != '' else '',
            comp_lng if comp_lng != '' else '',
            date_str, eki, machi, dist_km,
            match_label, setsu1, setsu2, p1, p2, p3, biko
        ])

out_path = BASE + r'\旧配置案.csv'
with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(OLD_HEADER)
    w.writerows(out_rows)

# サマリ
from collections import Counter
match_counts = Counter(r[14] for r in out_rows)
print(f'旧配置案.csv 出力: {len(out_rows)}件 / 未マッチ企業: {warn_count}件')
for label in MATCH_LABEL:
    cnt = match_counts.get(label, 0)
    if cnt:
        print(f'  {label}: {cnt}件')
