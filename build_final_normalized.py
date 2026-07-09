# -*- coding: utf-8 -*-
"""
260710データ(生徒・企業)を最新版として 最終正規化.csv を再構築する。
- 欠席3名を除外
- 氏名・ふりがな列を追加
- 企業名は更新済み企業マスターDB.csvから座標・カテゴリ等を再取得
"""
import csv
from math import radians, sin, cos, sqrt, atan2

BASE = r'C:\antigravity\public\00_作業\2026-06\インターンシップ管理'

def haversine(a, b):
    R = 6371.0
    dlat = radians(b[0]-a[0]); dlon = radians(b[1]-a[1])
    h = sin(dlat/2)**2 + cos(radians(a[0]))*cos(radians(b[0]))*sin(dlon/2)**2
    return R*2*atan2(sqrt(h), sqrt(1-h))

comp_by_no = {}
comp_by_name = {}
with open(BASE + r'\企業マスターDB.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        no = (r.get('No') or '').strip()
        comp_by_no[no] = r
        comp_by_name[(r.get('企業名') or '').strip()] = r

station_coords = {}
with open(BASE + r'\駅マスターDB.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        name = (r.get('駅名') or '').strip()
        try:
            station_coords[name] = (float(r['緯度']), float(r['経度']))
        except ValueError:
            pass

ALIAS = {'栢森駅': '柏森駅', '富岡駅': '富岡前駅', '森駅': '羽黒駅'}
def canon_eki(n):
    return ALIAS.get(n, n)

stu_extra = {}
with open(BASE + r'\生徒名簿DB.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        key = (r['学年'].strip(), r['組'].strip(), r['番号'].strip())
        stu_extra[key] = {
            '事前説明1': (r.get('事前説明１') or '').strip(),
            '事前説明2': (r.get('事前説明２') or '').strip(),
            '事前説明1業種': (r.get('事前説明1業種') or '').strip(),
            '事前説明2業種': (r.get('事前説明2業種') or '').strip(),
            '最寄り駅DB': (r.get('最寄り駅') or '').strip(),
        }

PREF_MAP = {'1': '製造工業', '2': '製造食品', '3': '物流', '4': '販売',
            '5': '保育', '6': '販売', '7': '美容', '8': 'その他',
            '4a': '販売', '4b': '販売', '4c': '販売'}
def norm_pref(code):
    return PREF_MAP.get((code or '').strip(), 'その他')

MATCH_LABEL = ['◎事前説明1', '◎事前説明2', '○第1希望', '○第2希望', '○第3希望', '[NG]不一致']
def match_level(pref_layers, comp_cats):
    cats = [c.strip() for c in comp_cats.split(',')]
    for i, p in enumerate(pref_layers):
        if p and p != 'その他' and p in cats:
            return i
    return 5

def find_comp(no_raw, name_raw):
    c = comp_by_no.get(no_raw.strip())
    if c:
        return c
    name_raw = name_raw.strip()
    for k, v in comp_by_name.items():
        if k == name_raw or name_raw in k or k in name_raw:
            return v
    return None

OUT_HEADER = [
    '学年', '組', '番号', '氏名', 'ふりがな', '性別',
    '配属企業No', '企業名', '業種カテゴリ', '受け入れ先住所', '緯度', '経度',
    '日付', '最寄り駅', '市町', '距離km',
    '業種マッチ', '事前説明1', '事前説明2', '第1希望', '第2希望', '第3希望', '備考'
]

out_rows = []
warn = []
skipped = []

with open(BASE + r'\260710_生徒データ.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        biko = (row.get('備考') or '').strip()
        nen = row['学年'].strip(); kumi = row['組'].strip(); ban = row['番号'].strip()
        sname = row['氏名'].strip(); furigana = row['ふりがな'].strip()

        if '欠席' in biko:
            skipped.append(f'{nen}-{kumi}-{ban} {sname} ({biko})')
            continue

        sex = row['性別'].strip()
        no_raw = (row.get('No.') or '').strip()
        cname = (row.get('インターン企業名') or '').strip()
        date_str = (row.get('日付') or '').strip()

        se = stu_extra.get((nen, kumi, ban), {})
        machi = ''
        eki = canon_eki(se.get('最寄り駅DB', ''))

        p1 = norm_pref(row.get('第１希望') if '第１希望' in row else '')
        # 260710データには第1〜3希望列が無いため roster DB 側の希望は使わず、
        # 事前説明のみでマッチ判定する
        p1 = p2 = p3 = ''

        comp = find_comp(no_raw, cname)
        if comp:
            comp_no = comp.get('No', '').strip()
            comp_name = comp.get('企業名', '').strip()
            comp_cat = comp.get('業種カテゴリ', '').strip()
            comp_addr = comp.get('住所', '').strip()
            try:
                comp_lat = float(comp.get('緯度', ''))
                comp_lng = float(comp.get('経度', ''))
            except ValueError:
                comp_lat = comp_lng = ''
        else:
            comp_no = no_raw; comp_name = cname; comp_cat = ''; comp_addr = ''
            comp_lat = comp_lng = ''
            warn.append(f'{nen}-{kumi}-{ban} No={no_raw} 名={cname}')

        dist_km = ''
        if eki and comp_lat != '':
            sc = station_coords.get(eki)
            if sc:
                dist_km = round(haversine(sc, (comp_lat, comp_lng)), 1)

        setsu1 = se.get('事前説明1', ''); setsu2 = se.get('事前説明2', '')
        setsu1_cat = se.get('事前説明1業種', ''); setsu2_cat = se.get('事前説明2業種', '')
        pref_layers = [setsu1_cat, setsu2_cat, p1, p2, p3]
        mlv = match_level(pref_layers, comp_cat) if comp_cat else 5
        match_label = MATCH_LABEL[mlv]

        out_rows.append([
            nen, kumi, ban, sname, furigana, sex,
            comp_no, comp_name, comp_cat, comp_addr,
            comp_lat if comp_lat != '' else '', comp_lng if comp_lng != '' else '',
            date_str, eki, machi, dist_km,
            match_label, setsu1, setsu2, p1, p2, p3, biko
        ])

with open(BASE + r'\最終正規化.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(OUT_HEADER)
    w.writerows(out_rows)

log = []
log.append(f'最終正規化.csv 更新: {len(out_rows)}名（除外{len(skipped)}名）')
for s in skipped:
    log.append(f'  除外: {s}')
if warn:
    log.append(f'企業未マッチ: {len(warn)}件')
    for w2 in warn:
        log.append(f'  {w2}')

with open(BASE + r'\_normalize_log.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(log))

print('done')
