# -*- coding: utf-8 -*-
"""
梶田正規化案 と 旧配置案 を全生徒で比較・評価する。
梶田案の条件が許容できない度合を ×（罰, ×0〜×5）でランク付けし、
旧配置案との優劣を備考に記述。製造工業・製造食品は同一視。
中央可鍛工業は問答無用で×5。 → 梶田比較検討.csv
"""
import csv

BASE = r'C:\antigravity\public\00_作業\2026-06\インターンシップ管理'

def load(path):
    d = {}
    with open(path, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            key = (r['学年'].strip(), r['組'].strip(), r['番号'].strip())
            d[key] = r
    return d

old    = load(BASE + r'\旧配置案.csv')
kajita = load(BASE + r'\梶田正規化.csv')

LEVEL_NAME  = {0:'事前説明1', 1:'事前説明2', 2:'第1希望', 3:'第2希望', 4:'第3希望', 5:'業種不一致'}
LEVEL_LABEL = {0:'◎事前説明1', 1:'◎事前説明2', 2:'○第1希望', 3:'○第2希望', 4:'○第3希望', 5:'🔴不一致'}

# 製造工業 と 製造食品 は同一とみなす（→ '製造'）
def norm_cat(c):
    c = (c or '').strip()
    m = {
        '製造（食品）':'製造', '製造（工業）':'製造',
        '製造食品':'製造', '製造工業':'製造',
        '販売・サービス':'販売', 'アパレル':'販売', '販売':'販売',
        '保育・幼児教育':'保育', '保育':'保育',
        '運輸・物流':'物流', '物流':'物流',
        '美容':'美容', 'その他':'その他',
    }
    return m.get(c, c)

def comp_cat_set(cat_field):
    return {norm_cat(x) for x in (cat_field or '').split(',') if x.strip()}

def recompute_level(row):
    cats = comp_cat_set(row.get('業種カテゴリ',''))
    layers = [
        norm_cat(row.get('事前説明1','')), norm_cat(row.get('事前説明2','')),
        norm_cat(row.get('第1希望','')), norm_cat(row.get('第2希望','')), norm_cat(row.get('第3希望','')),
    ]
    for i, p in enumerate(layers):
        if p and p != 'その他' and p in cats:
            return i
    return 5

def to_float(x):
    try:
        return float(x)
    except (ValueError, TypeError):
        return None

def match_penalty(lv):
    return {0:0, 1:0, 2:1, 3:2, 4:3, 5:5}[lv]

def dist_penalty(dist):
    if dist is None:
        return 1, '距離未算出（最寄り駅未記入）'
    if dist > 20:
        return 3, f'{dist}kmは20km超で通学困難'
    if dist > 15:
        return 2, f'{dist}kmは15km超過'
    if dist > 10:
        return 1, f'{dist}kmとやや遠い'
    return 0, ''

OUT_HEADER = [
    '学年','組','番号','性別',
    '旧_企業名','旧_業種マッチ','旧_距離km','旧_日付',
    '梶田_企業名','梶田_業種マッチ','梶田_距離km','梶田_日付',
    '許容不可ランク','梶田vs旧','備考'
]

rows = []
rank_counter = {}
verdict_counter = {}

for key in sorted(kajita.keys(), key=lambda k:(int(k[0]), int(k[1]), int(k[2]))):
    k = kajita[key]
    o = old.get(key, {})

    k_dist = to_float(k['距離km'])
    k_comp = k['企業名'].strip()
    k_date = k['日付'].strip()
    k_eki  = k['最寄り駅'].strip()

    o_dist = to_float(o.get('距離km'))
    o_comp = o.get('企業名','').strip()
    o_date = o.get('日付','').strip()

    k_lv = recompute_level(k)
    o_lv = recompute_level(o) if o else None
    k_match = LEVEL_LABEL[k_lv]
    o_match = LEVEL_LABEL[o_lv] if o_lv is not None else ''

    mp = match_penalty(k_lv)
    dp, dist_reason = dist_penalty(k_dist)
    raw = mp + dp
    rank = min(5, raw)

    forced = '中央可鍛' in k_comp
    if forced:
        rank = 5

    # ---- 梶田案の問題点 ----
    reasons = []
    if k_lv >= 5:
        reasons.append('業種が希望・事前説明いずれにも一致せず最低評価')
    elif k_lv == 4:
        reasons.append('第3希望止まりで本人の上位希望から外れる')
    elif k_lv == 3:
        reasons.append('第2希望止まり')
    elif k_lv == 2:
        reasons.append('第1希望だが事前説明の優先枠から外れる')
    if dist_reason:
        reasons.append(dist_reason)

    # ---- 旧配置案との優劣 ----
    verdict = '同等'
    comp_notes = []
    if o_lv is not None:
        if k_lv < o_lv:
            verdict = '梶田が良い'
            comp_notes.append(f'業種マッチが旧案の{LEVEL_NAME[o_lv]}→梶田は{LEVEL_NAME[k_lv]}に改善')
        elif k_lv > o_lv:
            verdict = '旧案が良い'
            comp_notes.append(f'業種マッチが旧案の{LEVEL_NAME[o_lv]}より悪化し梶田は{LEVEL_NAME[k_lv]}')
        else:
            comp_notes.append('業種マッチは旧案と同等')
    if o_dist is not None and k_dist is not None:
        diff = round(o_dist - k_dist, 1)
        if diff >= 2:
            comp_notes.append(f'距離は梶田案で{diff}km短縮')
            if verdict == '同等':
                verdict = '梶田が良い'
        elif diff <= -2:
            comp_notes.append(f'距離は梶田案の方が{abs(diff)}km遠い')
            if verdict == '同等':
                verdict = '旧案が良い'

    if o_comp != k_comp:
        comp_notes.insert(0, f'配属先が旧案「{o_comp}」から変更')

    # ---- 備考 ----
    if not reasons:
        body = '梶田案でも事前説明一致かつ近距離で問題なし（製造工業・製造食品は同一視）'
    else:
        body = '／'.join(reasons)
    if comp_notes:
        body += '。' + '、'.join(comp_notes)
    if forced:
        body = '【中央可鍛工業のため強制×5】' + body

    rank_disp = '×'*rank if rank > 0 else '×0(問題なし)'

    rows.append([
        key[0], key[1], key[2], k['性別'].strip(),
        o_comp, o_match, o.get('距離km','').strip(), o_date,
        k_comp, k_match, k['距離km'].strip(), k_date,
        rank_disp, verdict, body
    ])
    rank_counter[rank] = rank_counter.get(rank, 0) + 1
    verdict_counter[verdict] = verdict_counter.get(verdict, 0) + 1

out_path = BASE + r'\梶田比較検討.csv'
with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(OUT_HEADER)
    w.writerows(rows)

print(f'梶田比較検討.csv 出力: {len(rows)}件')
print('--- 許容不可ランク（梶田案） ---')
for r in sorted(rank_counter):
    print(f'  {"x"*r if r else "x0"} (ランク{r}): {rank_counter[r]}件')
print('--- 旧配置案との優劣 ---')
for v in ('梶田が良い','同等','旧案が良い'):
    print(f'  {v}: {verdict_counter.get(v,0)}件')
