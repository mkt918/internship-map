# -*- coding: utf-8 -*-
"""
インターンシップ配置最適化スクリプト v2
正規化DB（企業マスターDB.csv / 生徒名簿DB.csv）を直接読み込む。

優先順位（確定方針）:
- バランス型: 業種マッチ優先 + 同マッチ度なら近い企業
- 原則15km・例外可（希望業種が遠方にしかない場合のみ超過許容）
- 特殊ルール全適用: 1年生→4優先企業 / 3D→北名古屋物流希望 / 保育希望なし→製造系先行
- 競合時: 選択肢が少ない生徒を優先

業種マッチ階層:
  0 = 事前説明1業種 一致 (最優先)
  1 = 事前説明2業種 一致
  2 = 第1希望業種 一致
  3 = 第2希望業種 一致
  4 = 不一致
出力: 新配置案.csv
"""
import csv, re
from math import radians, sin, cos, sqrt, atan2
from collections import defaultdict, Counter

BASE = r'C:\antigravity\public\00_作業\2026-06\インターンシップ管理'

# ============================================================
# ユーティリティ
# ============================================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    d = lambda a: radians(a)
    dlat = d(lat2 - lat1); dlon = d(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(d(lat1)) * cos(d(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def parse_capacity(text):
    """受け入れ人数の説明 → 1日あたり定員"""
    text = (text or '').strip()
    # 全角数字を半角化
    text = text.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    if not text:
        return 2
    m = re.search(r'(\d+)\s*[名人]', text)
    if m: return int(m.group(1))
    m = re.search(r'最大\s*(\d+)', text)
    if m: return int(m.group(1))
    m = re.search(r'(\d+)', text)
    if m: return int(m.group(1))
    return 2

def parse_dates(text):
    """受入可能日程テキスト（; 区切り） → ["7/27(月)", ...]"""
    if not text: return []
    return [d.strip() for d in text.split(';') if d.strip()]

DAY_ORDER = {}
for i, (mo, da) in enumerate([(7,27),(7,28),(7,29),(7,30),(7,31),
                              (8,24),(8,25),(8,26),(8,27),(8,28)]):
    DAY_ORDER[f"{mo}/{da}"] = i

def date_month(d):
    m = re.match(r'(\d+)/', d)
    return int(m.group(1)) if m else 0

def date_order(d):
    m = re.match(r'(\d+)/(\d+)', d)
    return DAY_ORDER.get(f"{m.group(1)}/{m.group(2)}", 99) if m else 99

# ============================================================
# データ読み込み
# ============================================================
def read_dict(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

comp_rows = read_dict(BASE + r'\企業マスターDB.csv')
stu_rows  = read_dict(BASE + r'\生徒名簿DB.csv')

# --- 企業 ---
# 業種カテゴリは "製造食品, 販売" のように複数の場合あり → set化
def split_cats(text):
    return set(c.strip() for c in (text or '').replace('、', ',').split(',') if c.strip())

companies = {}
for r in comp_rows:
    no = (r.get('No') or '').strip()
    if not no: continue
    companies[no] = {
        'no': no,
        'name': r.get('企業名','').strip(),
        'cats': split_cats(r.get('業種カテゴリ','')),
        'gyoushu': r.get('業種カテゴリ','').strip(),
        'address': r.get('住所','').strip(),
        'lat': r.get('緯度','').strip(),
        'lng': r.get('経度','').strip(),
        'accepts_1': r.get('受入_1年','').strip().upper() == 'Y',
        'accepts_2': r.get('受入_2年','').strip().upper() == 'Y',
        'cap': parse_capacity(r.get('受け入れ人数の説明','')),
        'cap_text': r.get('受け入れ人数の説明','').strip(),
        'access': r.get('アクセス','').strip(),
        'dates': parse_dates(r.get('受入可能日程','')),
        'coords': None,
    }
    try:
        companies[no]['coords'] = (float(companies[no]['lat']), float(companies[no]['lng']))
    except (ValueError, TypeError):
        companies[no]['coords'] = None

# --- 生徒 ---
def fcoord(v):
    try: return float(v)
    except (ValueError, TypeError): return None

students = []
for r in stu_rows:
    g = (r.get('学年') or '').strip()
    if not g.isdigit(): continue
    lat = fcoord(r.get('駅緯度')); lng = fcoord(r.get('駅経度'))
    # マッチ用カテゴリ階層（事前説明1 > 事前説明2 > 第1希望 > 第2希望 > 第3希望）
    pref_layers = [
        (r.get('事前説明1業種','') or '').strip(),
        (r.get('事前説明2業種','') or '').strip(),
        (r.get('第1希望業種','') or '').strip(),
        (r.get('第2希望業種','') or '').strip(),
        (r.get('第3希望業種','') or '').strip(),
    ]
    students.append({
        'grade': int(g),
        'cls': (r.get('組') or '').strip(),
        'num': (r.get('番号') or '').strip(),
        'gender': (r.get('性別') or '').strip(),
        'setsumei1': r.get('事前説明１','').strip(),
        'setsumei2': r.get('事前説明２','').strip(),
        'pref_layers': pref_layers,
        'p_pref': (r.get('第1希望業種','') or '').strip(),
        'r_pref': (r.get('第2希望業種','') or '').strip(),
        't_pref': (r.get('第3希望業種','') or '').strip(),
        'city': (r.get('市町') or '').strip(),
        'station': (r.get('最寄り駅') or '').strip(),
        'coords': (lat, lng) if (lat is not None and lng is not None) else None,
        'biko_in': (r.get('備考') or '').strip(),
        'assigned': None, 'assigned_date': None, 'match_level': None,
        'dist_km': None, 'biko': '',
    })

# ============================================================
# マッチ判定（事前説明1 > 事前説明2 > 第1希望 > 第2希望）
# ============================================================
def cat_match(pref, comp_cats):
    """希望業種カテゴリが企業カテゴリ集合と一致するか"""
    if not pref or pref == 'その他':
        return False
    return pref in comp_cats

def match_level(s, comp):
    cc = comp['cats']
    for lv, pref in enumerate(s['pref_layers']):
        if cat_match(pref, cc):
            return lv
    return 5

def dist_km(s, comp):
    sc = s['coords']; cc = comp['coords']
    if sc and cc:
        return haversine(sc[0], sc[1], cc[0], cc[1])
    return 999.0

# ============================================================
# 定員管理
# ============================================================
cap_map = defaultdict(lambda: defaultdict(int))
for no, c in companies.items():
    for d in c['dates']:
        cap_map[no][d] = c['cap']

# 「各日」明記なし or 「いずれか1日」系 → 全日程合計の上限
TOTAL_CAP_OVERRIDE = {
    '1A':2,'1B':2,'1C':2,'1H':5,'2A':2,'2C':4,'2D':2,
    '3A':3,'3B':3,'3C':2,'3D':10,'41C':3,'41E':3,
    '42A':1,'42B':2,'43A':1,'44B':2,'44C':2,'44D':2,
    '44A1':1,'44A2':1,'44A3':1,'5H':2,'5O':2,'1G':4,'1K':5,
}
MONTHLY_CAP_OVERRIDE = {'43B': {7:6, 8:6}}
EXCLUDED = {'1D'}  # 遠距離のため除外

total_map = {}
monthly_map = defaultdict(lambda: defaultdict(int))
for no in TOTAL_CAP_OVERRIDE:
    total_map[no] = TOTAL_CAP_OVERRIDE[no]
for no, mc in MONTHLY_CAP_OVERRIDE.items():
    for mo, cap in mc.items():
        monthly_map[no][mo] = cap

def cap_available(no, date):
    if cap_map[no][date] <= 0: return False
    if no in TOTAL_CAP_OVERRIDE and total_map.get(no,0) <= 0: return False
    if no in MONTHLY_CAP_OVERRIDE and monthly_map[no][date_month(date)] <= 0: return False
    return True

def consume_cap(no, date):
    cap_map[no][date] -= 1
    if no in TOTAL_CAP_OVERRIDE:
        total_map[no] = total_map.get(no,0) - 1
    if no in MONTHLY_CAP_OVERRIDE:
        monthly_map[no][date_month(date)] -= 1

def available_dates(no, comp, july_only):
    return sorted(
        [d for d in comp['dates'] if cap_available(no, d) and (not july_only or date_month(d) == 7)],
        key=date_order
    )

def assign_student(s, no, date, ml, comp):
    s['assigned'] = no
    s['assigned_date'] = date
    s['match_level'] = ml
    s['dist_km'] = round(dist_km(s, comp), 1)
    consume_cap(no, date)

# ============================================================
# フェーズ1: 1年生 → 4優先企業（マッチ + 15km以内）
# ============================================================
PRIORITY_1NEN = ['42B', '43B', '2C', '2D']
for s in [s for s in students if s['grade'] == 1]:
    if s['assigned']: continue
    for pno in PRIORITY_1NEN:
        c = companies.get(pno)
        if not c: continue
        ml = match_level(s, c)
        if ml >= 5: continue          # マッチしない企業はスキップ
        if dist_km(s, c) > 15.0: continue
        ds = available_dates(pno, c, july_only=True)
        if ds:
            assign_student(s, pno, ds[0], ml, c)
            break

# ============================================================
# フェーズ1.5: 3D → 北名古屋エリア物流希望2年生
# ============================================================
STATIONS_3D = {'西春駅','上小田井駅','徳重名古屋芸大前駅','大山寺駅','岩倉駅'}
def eligible_3d(s):
    if s['grade'] != 2: return False
    geo_ok = s['station'] in STATIONS_3D or '名古屋市' in s['city']
    # 物流希望が階層のどこかにあるか
    pref_ok = '物流' in s['pref_layers'][:3]
    return geo_ok and pref_ok

c3d = companies.get('3D')
if c3d:
    cand = sorted([s for s in students if not s['assigned'] and eligible_3d(s)],
                  key=lambda s: (match_level(s, c3d), dist_km(s, c3d)))
    for s in cand:
        ds = available_dates('3D', c3d, july_only=False)
        if not ds: break
        assign_student(s, '3D', ds[0], match_level(s, c3d), c3d)

# ============================================================
# フェーズ2: 残り全員
# 保育希望なし生徒を先に処理（製造/物流枠を先取り）→ 選択肢が少ない順
# ============================================================
def count_options(s, july_only):
    return sum(
        1 for no, c in companies.items()
        if no not in EXCLUDED
        and ((s['grade'] == 1 and c['accepts_1']) or (s['grade'] == 2 and c['accepts_2']))
        and available_dates(no, c, july_only)
    )

def has_hoiku_pref(s):
    return '保育' in s['pref_layers']

unassigned = [s for s in students if not s['assigned']]
unassigned.sort(key=lambda s: (1 if has_hoiku_pref(s) else 0,
                               count_options(s, s['grade'] == 1)))

def build_candidates(s, july_only):
    cands = []
    for no, c in companies.items():
        if no in EXCLUDED: continue
        if s['grade'] == 1 and not c['accepts_1']: continue
        if s['grade'] == 2 and not c['accepts_2']: continue
        ds = available_dates(no, c, july_only)
        if not ds: continue
        cands.append((match_level(s, c), dist_km(s, c), no, ds[0]))
    return cands

for s in unassigned:
    july_only = (s['grade'] == 1)
    cands = build_candidates(s, july_only)
    if not cands and s['grade'] == 2:
        cands = build_candidates(s, july_only=False)
    if not cands:
        continue
    cands.sort(key=lambda x: (x[0], x[1]))   # マッチ度→距離
    if s['coords'] is not None:
        within15 = [c for c in cands if c[1] <= 15.0]
        chosen = (within15 if within15 else cands)[0]
        if not within15:
            s['biko'] = f'15km圏内に空きなし（最近接{chosen[1]:.1f}km）'
    else:
        chosen = cands[0]
        s['biko'] = '住所（市町）から距離算出'
    ml, dk, no, d = chosen
    assign_student(s, no, d, ml, companies[no])

# ============================================================
# 出力
# ============================================================
MATCH_LABELS = {0:'◎事前説明1', 1:'◎事前説明2', 2:'○第1希望', 3:'○第2希望', 4:'○第3希望', 5:'🔴不一致'}
HEADERS = ['学年','組','番号','性別','配属企業No','企業名','業種カテゴリ','受け入れ先住所',
           '緯度','経度','日付','最寄り駅','市町','距離km','業種マッチ',
           '事前説明1','事前説明2','第1希望','第2希望','第3希望','備考']

out_path = BASE + r'\新配置案.csv'
with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(HEADERS)
    for s in students:
        no = s['assigned']
        if no:
            c = companies[no]
            lat, lng = (c['lat'], c['lng'])
            label = MATCH_LABELS.get(s['match_level'], '?')
            addr = c['address']; cat = c['gyoushu']; name = c['name']
        else:
            lat = lng = ''; label = '❌未配置'; addr = cat = name = ''
            s['biko'] = s['biko'] or '配置先なし'
        w.writerow([
            s['grade'], s['cls'], s['num'], s['gender'], no or '', name, cat, addr,
            lat, lng, s['assigned_date'] or '', s['station'], s['city'],
            s['dist_km'] if s['dist_km'] is not None else '', label,
            s['setsumei1'], s['setsumei2'], s['p_pref'], s['r_pref'], s['t_pref'], s['biko'],
        ])

# ============================================================
# サマリ
# ============================================================
total = len(students)
assigned = sum(1 for s in students if s['assigned'])
print("=== 配置結果 ===")
print(f"生徒数: {total} / 配置済: {assigned} / 未配置: {total-assigned}")
for lv, label in MATCH_LABELS.items():
    cnt = sum(1 for s in students if s['match_level'] == lv)
    print(f"  {label.replace(chr(0x1f534),'[NG]')}: {cnt}件")
over15 = sum(1 for s in students if s['dist_km'] and s['dist_km'] > 15.0 and s['dist_km'] < 900)
print(f"  15km超過: {over15}件")
print("\n企業別割当数:")
cc = Counter(s['assigned'] for s in students if s['assigned'])
for no in sorted(cc):
    c = companies[no]
    print(f"  {no:5} {c['name'][:18]:<18} {cc[no]}名 (定員/日:{c['cap']})")
print(f"\n出力: {out_path}")
