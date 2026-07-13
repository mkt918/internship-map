# -*- coding: utf-8 -*-
"""
260714データを最新版として 最終正規化.csv を再構築する。
- 260714_生徒データ.csv には氏名列が無いため氏名/ふりがなは空欄のまま
- 担当教員・担当教室は実データとして別途 教員教室_実データ.csv に保存
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
            '第1希望業種': (r.get('第1希望業種') or '').strip(),
            '第2希望業種': (r.get('第2希望業種') or '').strip(),
            '第3希望業種': (r.get('第3希望業種') or '').strip(),
            '最寄り駅DB': (r.get('最寄り駅') or '').strip(),
        }

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
teacher_room_rows = []
warn = []

with open(BASE + r'\260714_生徒データ.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        nen = row['学年'].strip(); kumi = row['組'].strip(); ban = row['番号'].strip()
        sex = row['性別'].strip()
        no_raw = (row.get('No.') or '').strip()
        cname = (row.get('インターン企業名') or '').strip()
        date_str = (row.get('日付') or '').strip()
        teacher_real = (row.get('担当教員') or '').strip()
        room_real = (row.get('担当教室') or '').strip()

        se = stu_extra.get((nen, kumi, ban), {})
        eki = canon_eki(se.get('最寄り駅DB', ''))
        p1 = se.get('第1希望業種', ''); p2 = se.get('第2希望業種', ''); p3 = se.get('第3希望業種', '')

        comp = find_comp(no_raw, cname)
        if comp:
            comp_no = comp.get('No', '').strip()
            comp_name = comp.get('企業名', '').strip()
            comp_cat = comp.get('業種カテゴリ', '').strip()
            comp_addr = comp.get('住所', '').strip()
            try:
                comp_lat = float(comp.get('緯度', '')); comp_lng = float(comp.get('経度', ''))
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
            nen, kumi, ban, '', '', sex,
            comp_no, comp_name, comp_cat, comp_addr,
            comp_lat if comp_lat != '' else '', comp_lng if comp_lng != '' else '',
            date_str, eki, '', dist_km,
            match_label, setsu1, setsu2, p1, p2, p3, ''
        ])
        teacher_room_rows.append([nen, kumi, ban, comp_name, date_str, teacher_real, room_real])

with open(BASE + r'\最終正規化.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(OUT_HEADER)
    w.writerows(out_rows)

with open(BASE + r'\教員教室_実データ.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['学年', '組', '番号', '企業名', '日付', '担当教員', '担当教室'])
    w.writerows(teacher_room_rows)

log = [f'最終正規化.csv 更新: {len(out_rows)}名']
if warn:
    log.append(f'企業未マッチ: {len(warn)}件')
    for w2 in warn:
        log.append(f'  {w2}')

with open(BASE + r'\_normalize_log714.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(log))

print('done')
