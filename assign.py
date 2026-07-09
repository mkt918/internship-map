# -*- coding: utf-8 -*-
"""
インターンシップ配置最適化スクリプト
出力: 新配置案.csv (地図用データベース)
"""
import csv, io, re
from math import radians, sin, cos, sqrt, atan2
from collections import defaultdict

# ============================================================
# 座標データ
# ============================================================
# 最寄り駅不明時の市町代表座標
CITY_COORDS = {
    "各務原市":       (35.394,  136.918),   # 新那加駅エリア
    "北名古屋市":     (35.227,  136.869),   # 西春/上小田井エリア
    "丹羽郡大口町":   (35.323,  136.905),   # 大口エリア
    "丹羽郡扶桑町":   (35.362,  136.912),
    "江南市":         (35.332,  136.871),
    "一宮市":         (35.303,  136.800),
    "犬山市":         (35.380,  136.940),
    "岩倉市":         (35.279,  136.871),
}

STATION_COORDS = {
    "名鉄名古屋駅": (35.181438, 136.90657),
    "下小田井駅":   (35.2017,   136.8758),
    "上小田井駅":   (35.2222,   136.8742),
    "徳重名古屋芸大前駅": (35.2497, 136.8971),
    "西春駅":       (35.2654,   136.8956),
    "石仏駅":       (35.2657,   136.8970),
    "木田駅":       (35.2486,   136.8218),
    "平針駅":       (35.1189,   136.9685),
    "大山寺駅":     (35.3325,   136.9078),
    "岩倉駅":       (35.279434, 136.871414),
    "布袋駅":       (35.3208,   136.8938),
    "木津用水駅":   (35.3285,   136.9024),
    "江南駅":       (35.332081, 136.870773),
    "栢森駅":       (35.3580,   136.9178),
    "扶桑駅":       (35.359165, 136.913055),
    "羽黒駅":       (35.3592,   136.9509),
    "犬山口駅":     (35.376,    136.942),
    "犬山駅":       (35.378441, 136.944427),
    "富岡前駅":     (35.3795,   136.9607),
    "富岡駅":       (35.3795,   136.9607),
    "田県神社前駅": (35.3195,   136.9234),
    "一宮駅":       (35.303837, 136.802979),
    "尾張一宮駅":   (35.3096,   136.8006),
    "新木曽川駅":   (35.3390,   136.8957),
    "木曽川駅":     (35.3373,   136.9048),
    "木曽川堤駅":   (35.3380,   136.9048),
    "新那加駅":     (35.3960,   136.9210),
}

COMPANY_COORDS = {
    "1A": (35.35247, 136.973373), "1B": (35.301033, 137.002777),
    "1C": (35.298954, 136.94664), "1D": (35.119911, 137.029266),
    "1E": (35.188705, 136.809784),"1G": (35.3251,   136.895706),
    "1H": (35.34903,  136.941666),"1I": (35.308201, 136.892395),
    "1J": (35.342197, 136.874588),"1K": (35.352619, 136.869812),
    "2A": (35.31641,  136.873947),"2B": (35.353722, 136.875168),
    "2C": (35.371872, 136.907837),"2D": (35.323299, 136.86908),
    "3A": (35.293083, 136.885376),"3B": (35.329754, 136.943909),
    "3C": (35.314816, 136.893631),"3D": (35.154476, 136.850098),
    "41A":(35.299957, 136.822708),"41B":(35.323132, 136.868393),
    "41C":(35.33247,  136.866745),"41E":(35.332783, 136.859161),
    "42A":(35.3391,   136.869308),"42B":(35.313831, 136.878494),
    "43A":(35.225266, 136.883301),"43B":(35.339359, 136.871674),
    "44A1":(35.303158,136.803268),"44A2":(35.294224,136.82579),
    "44A3":(35.303356,136.803253),"44B":(35.330742, 136.905304),
    "44C":(35.235859, 136.881241),"44D":(35.274368, 136.920776),
    "5A": (35.311146, 136.802643),"5B": (35.334476, 136.852432),
    "5C": (35.323299, 136.867432),"5D": (35.354492, 136.88533),
    "5E": (35.360222, 136.858276),"5F": (35.368015, 136.885666),
    "5G": (35.342247, 136.870865),"5H": (35.315956, 136.869095),
    "5I": (35.336178, 136.867859),"5J": (35.324711, 136.881989),
    "5K": (35.34539,  136.880692),"5L": (35.348694, 136.863403),
    "5M": (35.345955, 136.852081),"5N": (35.311016, 136.875839),
    "5O": (35.347504, 136.864716),"5P": (35.352188, 136.85791),
    "5Q": (35.363976, 136.874802),
}

# ============================================================
# 業種カテゴリ正規化
# ============================================================
# カテゴリ: 保育 / 製造工業 / 製造食品 / 物流 / 美容 / 販売
def norm_cat(text):
    """業種テキスト → カテゴリset"""
    t = text.lower()
    cats = set()
    if any(k in t for k in ['保育', '幼児', '幼稚', '児童', '福祉', '介護']):
        cats.add('保育')
    if any(k in t for k in ['食品製造', '漬物', '和菓子', '飲食サービス', '製造（食品', '製造業（食品']):
        cats.add('製造食品')
    if any(k in t for k in ['製造業（全般', '製造（工業', 'メーカー', '自動車部品', 'プラスチック',
                             'エンジニアリング', 'ベビー衣料製造']):
        cats.add('製造工業')
    # 「製造業」だけ → 工業
    if '製造業' in t and '製造食品' not in cats and '製造工業' not in cats:
        cats.add('製造工業')
    if '製造' in t and '製造食品' not in cats and '製造工業' not in cats:
        cats.add('製造工業')
    if any(k in t for k in ['物流', '倉庫', '運輸', '配送', '運搬', '警備']):
        cats.add('物流')
    if any(k in t for k in ['美容', '理容']):
        cats.add('美容')
    if any(k in t for k in ['小売', '販売', 'アパレル', '着物', 'きもの', 'サービス', '複合サービス', '飲食']):
        cats.add('販売')
    if not cats:
        cats.add('その他')
    return cats

# ============================================================
# ユーティリティ
# ============================================================
def _resolve_coords(station, city):
    """最寄り駅座標 → なければ市町代表座標"""
    if station and station in STATION_COORDS:
        return STATION_COORDS[station]
    for key, coords in CITY_COORDS.items():
        if key in city:
            return coords
    return None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    d = lambda a: radians(a)
    dlat = d(lat2 - lat1); dlon = d(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(d(lat1)) * cos(d(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def parse_capacity(text):
    text = text.strip()
    if not text or any(k in text for k in ['？', '未定']): return 2
    m = re.search(r'(\d+)\s*名', text)
    if m: return int(m.group(1))
    m = re.search(r'最大\s*(\d+)', text)
    if m: return int(m.group(1))
    m = re.search(r'^\s*(\d+)\s*$', text)
    if m: return int(m.group(1))
    return 2

def parse_company_dates(text):
    """受入可能日程テキスト → ["7/27(月)", ...]"""
    text = text.replace('（', '(').replace('）', ')').replace('\n', ' ')
    dates = []
    for m in re.finditer(r'(\d+)月(\d+)日[（(]([月火水木金土日])[）)]', text):
        d = f"{m.group(1)}/{m.group(2)}({m.group(3)})"
        if d not in dates: dates.append(d)
    for m in re.finditer(r'(\d+)/(\d+)[（(]([月火水木金土日])[）)]', text):
        d = f"{m.group(1)}/{m.group(2)}({m.group(3)})"
        if d not in dates: dates.append(d)
    return dates

def parse_blocked_dates(flag, text):
    """大会重複フラグと日程テキスト → blocked月/日 set"""
    if flag != '○' or not text or text.strip() in ['', '不明']:
        return set()
    text = text.strip().replace('　', '').replace('，', ',').replace('、', ',')
    blocked = set()
    # range "M/D～D" or "M月D日～D日"
    m = re.search(r'(\d+)[月/](\d+)日?[〜～](\d+)', text)
    if m:
        month = int(m.group(1))
        for day in range(int(m.group(2)), int(m.group(3))+1):
            blocked.add(f"{month}/{day}")
        return blocked
    # individual dates
    for m2 in re.finditer(r'(\d+)[月/](\d+)', text):
        blocked.add(f"{m2.group(1)}/{m2.group(2)}")
    # trailing day after comma: "7/29,30"
    m3 = re.search(r'(\d+)/\d+[,，]\s*(\d+)', text)
    if m3:
        blocked.add(f"{m3.group(1)}/{m3.group(2)}")
    return blocked

def date_month(d):
    m = re.match(r'(\d+)/', d)
    return int(m.group(1)) if m else 0

def date_day(d):
    m = re.match(r'\d+/(\d+)', d)
    return int(m.group(1)) if m else 0

def date_blocked(date_str, blocked):
    m = re.match(r'(\d+)/(\d+)', date_str)
    if m: return f"{m.group(1)}/{m.group(2)}" in blocked
    return False

DAY_ORDER = {}
for i, (mo, da) in enumerate([(7,27),(7,28),(7,29),(7,30),(7,31),(8,24),(8,25),(8,26),(8,27),(8,28)]):
    DAY_ORDER[f"{mo}/{da}"] = i

def date_order(d):
    m = re.match(r'(\d+)/(\d+)', d)
    return DAY_ORDER.get(f"{m.group(1)}/{m.group(2)}", 99) if m else 99

# ============================================================
# データ読み込み
# ============================================================
def read_csv(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.reader(io.StringIO(f.read())))

comp_rows = read_csv(r'C:\antigravity\public\00_作業\input\260617_インターンシップ事業所.csv')
stu_rows  = read_csv(r'C:\antigravity\public\00_作業\input\260617_クラス名簿表フル.csv')

# 事業所データ構築
companies = {}
for row in comp_rows[2:]:
    if len(row) < 10: continue
    no = row[0].strip()
    if not re.match(r'\d', no): continue
    name     = row[2].strip()
    gyoushu  = row[3].strip()
    address  = row[6].strip() if len(row) > 6 else ''
    gakka    = row[7].strip() if len(row) > 7 else ''
    nittei   = row[8].strip() if len(row) > 8 else ''
    cap_text = row[9].strip() if len(row) > 9 else ''
    access   = row[13].strip() if len(row) > 13 else ''

    accepts_1 = '生活文化科' in gakka or (not '商業科' in gakka and '生活' not in gakka)
    accepts_2 = '商業科' in gakka or (not '生活文化科' in gakka)
    if '生活文化科' in gakka and '商業科' in gakka:
        accepts_1 = accepts_2 = True

    cap = parse_capacity(cap_text)
    # 5O: 合計2名 → per-date=1
    if '合計で2名' in cap_text: cap = 1

    companies[no] = {
        'no': no, 'name': name, 'gyoushu': gyoushu, 'cats': norm_cat(gyoushu),
        'address': address, 'accepts_1': accepts_1, 'accepts_2': accepts_2,
        'dates': parse_company_dates(nittei), 'cap': cap, 'access': access,
        'coords': COMPANY_COORDS.get(no),
    }

# 生徒データ構築
students = []
for row in stu_rows[1:]:
    if len(row) < 20 or not row[0].strip().isdigit(): continue
    grade = int(row[0].strip())
    cls   = int(row[1].strip()) if row[1].strip().isdigit() else 0
    num   = int(row[2].strip()) if row[2].strip().isdigit() else 0
    gender = row[3].strip()

    i_gy  = row[8].strip()  if len(row) > 8  else ''
    l_gy  = row[11].strip() if len(row) > 11 else ''
    p_pref= row[15].strip() if len(row) > 15 else ''
    r_pref= row[17].strip() if len(row) > 17 else ''
    t_pref= row[19].strip() if len(row) > 19 else ''
    city    = row[21].strip() if len(row) > 21 else ''
    station = row[22].strip() if len(row) > 22 else ''

    taikai_flag = row[26].strip() if len(row) > 26 else ''
    taikai_text = row[27].strip() if len(row) > 27 else ''
    blocked = parse_blocked_dates(taikai_flag, taikai_text)

    il_cats   = norm_cat(i_gy) | norm_cat(l_gy)
    pref_cats = [norm_cat(p_pref), norm_cat(r_pref), norm_cat(t_pref)]

    students.append({
        'grade': grade, 'cls': cls, 'num': num, 'gender': gender,
        'i_gy': i_gy, 'l_gy': l_gy, 'p_pref': p_pref, 'r_pref': r_pref, 't_pref': t_pref,
        'il_cats': il_cats, 'pref_cats': pref_cats,
        'city': city, 'station': station, 'station_coords': _resolve_coords(station, city),
        'blocked': blocked, 'taikai_text': taikai_text,
        'assigned': None, 'assigned_date': None, 'match_level': None, 'dist_km': None, 'biko': '',
    })

# ============================================================
# 配置アルゴリズム
# ============================================================
# 定員管理: cap_map[no][date] = 残枠数
cap_map = defaultdict(lambda: defaultdict(int))
for no, c in companies.items():
    for d in c['dates']:
        cap_map[no][d] = c['cap']

PRIORITY_1NEN = {'42B', '43B', '2C', '2D'}

# ============================================================
# 特殊定員制約
# ============================================================
# 「いずれかの1日のみ」= 全日程合計でこの人数
TOTAL_CAP_OVERRIDE = {
    # K列「各日」なし・複数日程あり → 受入可能日程の中からどれか1日のみ
    '1A':  2,   # 1日最大2名
    '1B':  2,   # 1日最大2名
    '1C':  2,   # いずれかの日程で2名まで
    # '1D' は除外（遠距離）
    '1H':  5,   # 1日最大5名
    '2A':  2,   # 1日2名
    '2C':  4,   # 1日最大2名×最大2日
    '2D':  2,   # 2名
    '3A':  3,   # いずれかの1日で最大3名
    '3B':  3,   # いずれか1日のみ
    '3C':  2,   # 1日最大2名
    '3D':  10,  # 1日間のみ・10名程度
    '41C': 3,   # いずれかの一日で最大3名
    '41E': 3,   # 3名
    '42A': 1,   # 1日1名
    '42B': 2,   # 1日最大2名
    '43A': 1,   # 1日1名
    '44B': 2,   # 2人
    '44C': 2,   # 1日最大2名
    '44D': 2,   # 2名
    '44A1': 1,  # 各店1日1名
    '44A2': 1,
    '44A3': 1,
    '5H':  2,   # 不明（デフォルト2）
    '5O':  2,   # 合計で2名
    '1G':  4,   # 1・2年生それぞれ2名ずつ
    '1K':  5,   # 「今回は5名程度でお願い」(最大10名だが希望5名)
}
# 月ごと上限: {月: 上限数}
MONTHLY_CAP_OVERRIDE = {
    '43B': {7: 6, 8: 6},  # 前半3名×最大2日、後半3名×最大2日
}

# total_map[no] = 残り配置枠（全日程合計）
total_map = {}
monthly_map = defaultdict(lambda: defaultdict(int))

def init_caps():
    for no, c in companies.items():
        if no in TOTAL_CAP_OVERRIDE:
            total_map[no] = TOTAL_CAP_OVERRIDE[no]
        if no in MONTHLY_CAP_OVERRIDE:
            for mo, cap in MONTHLY_CAP_OVERRIDE[no].items():
                monthly_map[no][mo] = cap

def cap_available(no, date):
    """日付枠 + 全体枠 + 月枠 全て残っているか"""
    if cap_map[no][date] <= 0:
        return False
    if no in TOTAL_CAP_OVERRIDE and total_map.get(no, 0) <= 0:
        return False
    if no in MONTHLY_CAP_OVERRIDE:
        mo = date_month(date)
        if monthly_map[no][mo] <= 0:
            return False
    return True

def consume_cap(no, date):
    cap_map[no][date] -= 1
    if no in TOTAL_CAP_OVERRIDE:
        total_map[no] = total_map.get(no, 0) - 1
    if no in MONTHLY_CAP_OVERRIDE:
        monthly_map[no][date_month(date)] -= 1

def match_level(student, comp):
    """業種マッチレベル: 0=IL一致, 1=第1希望, 2=第2希望, 3=第3希望, 4=不一致"""
    cc = comp['cats']
    if cc & student['il_cats']:              return 0
    if cc & student['pref_cats'][0] - {'その他'}: return 1
    if cc & student['pref_cats'][1] - {'その他'}: return 2
    if cc & student['pref_cats'][2] - {'その他'}: return 3
    return 4

def dist_km(student, comp):
    sc = student['station_coords']
    cc = comp['coords']
    if sc and cc: return haversine(sc[0], sc[1], cc[0], cc[1])
    return 999.0

def available_dates(no, comp, blocked, july_only):
    return sorted(
        [d for d in comp['dates']
         if cap_available(no, d)
         and not date_blocked(d, blocked)
         and (not july_only or date_month(d) == 7)],
        key=date_order
    )

def assign_student(s, no, date, ml, comp):
    s['assigned']      = no
    s['assigned_date'] = date
    s['match_level']   = ml
    s['dist_km']       = round(dist_km(s, comp), 1)
    consume_cap(no, date)

init_caps()

# 1D は除外（遠距離）
EXCLUDED = {'1D'}

# ============================================================
# フェーズ1: 1年生 → 4優先企業（IL一致 + 15km以内）
# ============================================================
for s in [s for s in students if s['grade'] == 1]:
    for pno in PRIORITY_1NEN:
        c = companies.get(pno)
        if not c or not (c['cats'] & s['il_cats']): continue
        if dist_km(s, c) > 15.0: continue
        for d in available_dates(pno, c, s['blocked'], july_only=True):
            assign_student(s, pno, d, 0, c)
            break
        if s['assigned']: break

# ============================================================
# フェーズ1.5: 3D → 北名古屋エリア物流希望2年生を優先配置
# 条件: 駅が西春/上小田井/徳重名古屋芸大前/大山寺/岩倉 or 市区が名古屋市
#       かつ P or R が物流希望
# ============================================================
STATIONS_3D = {'西春駅', '上小田井駅', '徳重名古屋芸大前駅', '大山寺駅', '岩倉駅'}

def eligible_3d(s):
    if s['grade'] != 2: return False
    geo_ok = s['station'] in STATIONS_3D or '名古屋市' in s['city']
    pref_ok = '物流' in s['pref_cats'][0] or '物流' in s['pref_cats'][1]
    return geo_ok and pref_ok

c3d = companies.get('3D')
if c3d:
    candidates_3d = sorted(
        [s for s in students if not s['assigned'] and eligible_3d(s)],
        key=lambda s: (match_level(s, c3d), dist_km(s, c3d))
    )
    for s in candidates_3d:
        adates = available_dates('3D', c3d, s['blocked'], july_only=False)
        if not adates: break
        assign_student(s, '3D', adates[0], match_level(s, c3d), c3d)

# ============================================================
# フェーズ2: 残り全員
# ソート: 保育希望なし生徒を先に（製造/物流枠を先取り）→ 選択肢が少ない順
# ============================================================
def count_options(s, july_only):
    return sum(
        1 for no, c in companies.items()
        if no not in EXCLUDED
        and (s['grade'] == 1 and c['accepts_1'] or s['grade'] == 2 and c['accepts_2'])
        and available_dates(no, c, s['blocked'], july_only)
    )

def has_hoiku_pref(s):
    return any('保育' in cats for cats in s['pref_cats'])

unassigned = [s for s in students if not s['assigned']]
# 保育希望なし → 先に処理、同じ中は選択肢が少ない順
unassigned.sort(key=lambda s: (1 if has_hoiku_pref(s) else 0,
                               count_options(s, s['grade'] == 1)))

def build_candidates(s, july_only):
    cands = []
    for no, c in companies.items():
        if no in EXCLUDED: continue
        if s['grade'] == 1 and not c['accepts_1']: continue
        if s['grade'] == 2 and not c['accepts_2']: continue
        adates = available_dates(no, c, s['blocked'], july_only)
        if not adates: continue
        ml = match_level(s, c)
        dk = dist_km(s, c)
        cands.append((ml, dk, no, adates[0]))
    return cands

for s in unassigned:
    july_only = (s['grade'] == 1)
    candidates = build_candidates(s, july_only)

    # 2年生で7月に入れなかった場合は8月も試す
    if not candidates and s['grade'] == 2:
        candidates = build_candidates(s, july_only=False)

    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1]))
        has_coords = s['station_coords'] is not None
        if has_coords:
            within15 = [c for c in candidates if c[1] <= 15.0]
            chosen = (within15 if within15 else candidates)[0]
            ml, dk, no, d = chosen
            if not within15:
                s['biko'] = f'15km圏内に空きなし（最近接{dk:.1f}km）'
        else:
            chosen = candidates[0]
            ml, dk, no, d = chosen
            s['biko'] = '住所（市町）から距離算出'
        assign_student(s, no, d, ml, companies[no])

# ============================================================
# 出力
# ============================================================
MATCH_LABELS = {0: '✅IL一致', 1: '⭕第1希望', 2: '⭕第2希望', 3: '⭕第3希望', 4: '🔴不一致'}
HEADERS = ['学年','組','番号','性別','配属企業No','企業名','業種','受け入れ先住所',
           '緯度','経度','日付','最寄り駅','市町','距離km','業種マッチ',
           '①業種(I)','②業種(L)','第1希望(P)','第2希望(R)','第3希望(T)','大会重複','備考']

out_path = r'C:\antigravity\public\00_作業\2026-06\インターンシップ管理\新配置案.csv'
with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(HEADERS)
    for s in students:
        no = s['assigned']
        if no:
            c = companies[no]
            co = c['coords']
            lat, lng = (co[0], co[1]) if co else ('', '')
            match_label = MATCH_LABELS.get(s['match_level'], '?')
            biko = ''
        else:
            c = {}; lat = lng = ''; match_label = '❌未配置'; s['biko'] = '配置先なし'
        taikai_info = s['taikai_text'] if s['blocked'] else ''
        w.writerow([
            s['grade'], s['cls'], s['num'], s['gender'],
            no or '',
            c.get('name','') if no else '',
            c.get('gyoushu','') if no else '',
            c.get('address','') if no else '',
            lat, lng,
            s['assigned_date'] or '',
            s['station'], s['city'],
            s['dist_km'] if s['dist_km'] is not None else '',
            match_label,
            s['i_gy'], s['l_gy'], s['p_pref'], s['r_pref'], s['t_pref'],
            taikai_info, s['biko'],
        ])

# サマリ表示
total = len(students)
assigned = sum(1 for s in students if s['assigned'])
print(f"=== 配置結果 ===")
print(f"生徒数: {total} / 配置済: {assigned} / 未配置: {total-assigned}")
for lv, label in MATCH_LABELS.items():
    cnt = sum(1 for s in students if s['match_level'] == lv)
    print(f"  {label}: {cnt}件")
print(f"\n企業別割当数:")
from collections import Counter
comp_count = Counter(s['assigned'] for s in students if s['assigned'])
for no in sorted(comp_count):
    c = companies[no]
    print(f"  {no} {c['name'][:15]:<15} {comp_count[no]}名 (定員/日:{c['cap']})")
print(f"\n出力: {out_path}")
