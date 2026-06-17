# -*- coding: utf-8 -*-
"""
旧配置案と新配置案を全生徒で比較し、
旧配置案の条件が許容できない度合を ×（罰, max5）でランク付けする。
理由を備考に記述し、比較検討.csv として保存。
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

old = load(BASE + r'\旧配置案.csv')
new = load(BASE + r'\新配置案.csv')

# マッチラベル → レベル（小さいほど良い）
LEVEL = {
    '◎事前説明1': 0, '◎事前説明2': 1,
    '○第1希望': 2, '○第2希望': 3, '○第3希望': 4,
    '🔴不一致': 5, '[NG]不一致': 5, '不一致': 5,
}
LEVEL_NAME = {0:'事前説明1', 1:'事前説明2', 2:'第1希望', 3:'第2希望', 4:'第3希望', 5:'業種不一致'}

def to_float(x):
    try:
        return float(x)
    except (ValueError, TypeError):
        return None

def match_penalty(label):
    lv = LEVEL.get(label, 5)
    return {0:0, 1:0, 2:1, 3:2, 4:3, 5:5}[lv], lv

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
    '新_企業名','新_業種マッチ','新_距離km','新_日付',
    '許容不可ランク','備考'
]

rows = []
rank_counter = {}

for key in sorted(old.keys(), key=lambda k:(int(k[0]), int(k[1]), int(k[2]))):
    o = old[key]
    n = new.get(key, {})

    o_match = o['業種マッチ'].strip()
    o_dist  = to_float(o['距離km'])
    o_comp  = o['企業名'].strip()
    o_date  = o['日付'].strip()
    o_eki   = o['最寄り駅'].strip()

    n_match = n.get('業種マッチ','').strip()
    n_dist  = to_float(n.get('距離km'))
    n_comp  = n.get('企業名','').strip()
    n_date  = n.get('日付','').strip()

    mp, o_lv = match_penalty(o_match)
    dp, dist_reason = dist_penalty(o_dist)
    raw = mp + dp
    rank = max(1, min(5, raw))

    # ---- 理由文を構築 ----
    reasons = []
    # 業種マッチについて
    if o_lv >= 5:
        reasons.append('業種が希望・事前説明いずれにも一致せず最低評価')
    elif o_lv == 4:
        reasons.append('第3希望止まりで本人の上位希望から外れる')
    elif o_lv == 3:
        reasons.append('第2希望止まり')
    elif o_lv == 2:
        reasons.append('第1希望だが事前説明の優先枠から外れる')
    # 距離について
    if dist_reason:
        reasons.append(dist_reason)
    if o_eki == '' and o_dist is None:
        pass  # 既に距離未算出で言及

    # ---- 新配置案との比較 ----
    n_lv = LEVEL.get(n_match, None)
    comp_notes = []
    if n_lv is not None:
        if n_lv < o_lv:
            comp_notes.append(f'新案では{LEVEL_NAME[n_lv]}一致に改善')
        elif n_lv > o_lv:
            comp_notes.append(f'新案は{LEVEL_NAME[n_lv]}でむしろ旧案の方が業種は良い')
        else:
            comp_notes.append('業種マッチは新旧同等')
    if o_dist is not None and n_dist is not None:
        diff = round(o_dist - n_dist, 1)
        if diff >= 2:
            comp_notes.append(f'距離も新案で{diff}km短縮')
        elif diff <= -2:
            comp_notes.append(f'ただし距離は新案の方が{abs(diff)}km遠い')

    # ---- 備考まとめ ----
    if not reasons:
        body = '旧案でも事前説明一致かつ近距離で許容範囲'
    else:
        body = '／'.join(reasons)
    if comp_notes:
        body += '。' + '、'.join(comp_notes)

    rows.append([
        key[0], key[1], key[2], o['性別'].strip(),
        o_comp, o_match, o['距離km'].strip(), o_date,
        n_comp, n_match, n.get('距離km','').strip(), n_date,
        '×'*rank, body
    ])
    rank_counter[rank] = rank_counter.get(rank, 0) + 1

out_path = BASE + r'\比較検討.csv'
with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(OUT_HEADER)
    w.writerows(rows)

print(f'比較検討.csv 出力: {len(rows)}件')
for r in sorted(rank_counter):
    print(f'  {"x"*r} (ランク{r}): {rank_counter[r]}件')
