# -*- coding: utf-8 -*-
"""
駅マスターDB と 企業立地DB を生成する。
- 駅DB: 駅名, 緯度, 経度, 路線(複数全記載), 利用生徒数
- 企業立地DB: No, 企業名, 住所, 緯度, 経度, 最寄り駅, 路線, 徒歩/アクセス補足
路線は知識ベースで補完。複数路線が乗り入れる駅は全記載。
"""
import csv, re
from math import radians, sin, cos, sqrt, atan2
from collections import defaultdict

BASE = r'C:\antigravity\public\00_作業\2026-06\インターンシップ管理'

def haversine(a, b):
    R = 6371.0
    d = radians
    dlat = d(b[0]-a[0]); dlon = d(b[1]-a[1])
    h = sin(dlat/2)**2 + cos(d(a[0]))*cos(d(b[0]))*sin(dlon/2)**2
    return R*2*atan2(sqrt(h), sqrt(1-h))

# ============================================================
# 駅マスター（座標 + 路線、知識ベース）
# 複数路線は「; 」区切りで全記載
# ============================================================
# (駅名: (緯度, 経度, 路線))
STATIONS = {
    # --- 生徒名簿に出現する駅 ---
    '一宮駅':            (35.303837, 136.802979, '名鉄名古屋本線'),
    '尾張一宮駅':        (35.3096,   136.8006,   'JR東海道本線'),
    '羽黒駅':            (35.3592,   136.9509,   '名鉄犬山線'),
    '下小田井駅':        (35.2017,   136.8758,   '名鉄犬山線'),
    '柏森駅':            (35.3580,   136.9178,   '名鉄犬山線'),
    '岩倉駅':            (35.279434, 136.871414, '名鉄犬山線'),
    '犬山駅':            (35.378441, 136.944427, '名鉄犬山線; 名鉄小牧線; 名鉄広見線'),
    '犬山口駅':          (35.376,    136.942,    '名鉄犬山線'),
    '江南駅':            (35.332081, 136.870773, '名鉄犬山線'),
    '上小田井駅':        (35.2222,   136.8742,   '名鉄犬山線; 名古屋市営地下鉄鶴舞線'),
    '新那加駅':          (35.3960,   136.9210,   '名鉄各務原線'),
    '新木曽川駅':        (35.3390,   136.8957,   '名鉄名古屋本線'),
    '西春駅':            (35.2654,   136.8956,   '名鉄犬山線'),
    '石仏駅':            (35.2657,   136.8970,   '名鉄犬山線'),
    '大山寺駅':          (35.3325,   136.9078,   '名鉄犬山線'),
    '田県神社前駅':      (35.3195,   136.9234,   '名鉄小牧線'),
    '徳重名古屋芸大前駅':(35.2497,   136.8971,   '名鉄小牧線'),
    '富岡前駅':          (35.3795,   136.9607,   '名鉄小牧線'),
    '布袋駅':            (35.3208,   136.8938,   '名鉄犬山線'),
    '扶桑駅':            (35.359165, 136.913055, '名鉄犬山線'),
    '平針駅':            (35.1189,   136.9685,   '名古屋市営地下鉄鶴舞線'),
    '名鉄名古屋駅':      (35.181438, 136.90657,  '名鉄名古屋本線; 名鉄犬山線; 名鉄常滑線'),
    '木曽川駅':          (35.3373,   136.9048,   'JR東海道本線'),
    '木曽川堤駅':        (35.3380,   136.9048,   '名鉄名古屋本線'),
    '木津用水駅':        (35.3285,   136.9024,   '名鉄犬山線'),
    '木田駅':            (35.2486,   136.8218,   '名鉄津島線'),
    # --- 企業アクセスに出現する追加駅 ---
    '小牧原駅':          (35.2755,   136.9255,   '名鉄小牧線'),
    '味岡駅':            (35.2876,   136.9320,   '名鉄小牧線'),
    '赤池駅':            (35.1130,   137.0150,   '名古屋市営地下鉄鶴舞線; 名鉄豊田線'),
    '七宝駅':            (35.1722,   136.8000,   '名鉄津島線'),
    '楽田駅':            (35.3460,   136.9430,   '名鉄小牧線'),
    '岩塚駅':            (35.1730,   136.8530,   '名古屋市営地下鉄東山線'),
    '八田駅':            (35.1530,   136.8530,   'JR関西本線; 近鉄名古屋線; 名古屋市営地下鉄東山線'),
    '間内駅':            (35.2620,   136.9230,   '名鉄小牧線'),
    '春日井駅':          (35.2480,   136.9720,   'JR中央本線'),
}

# 駅名の表記ゆれ（生徒DB「栢森」= 「柏森」、富岡=富岡前 等）
ALIAS = {
    '栢森駅': '柏森駅',
    '富岡駅': '富岡前駅',
}

def canon(name):
    return ALIAS.get(name, name)

# ============================================================
# 生徒名簿から駅別利用者数を集計
# ============================================================
with open(BASE + r'\生徒名簿DB.csv', encoding='utf-8-sig') as f:
    stu = list(csv.DictReader(f))

usage = defaultdict(int)
for r in stu:
    st = (r.get('最寄り駅') or '').strip()
    if st:
        usage[canon(st)] += 1

# ============================================================
# 駅マスターDB.csv 出力
# ============================================================
station_path = BASE + r'\駅マスターDB.csv'
with open(station_path, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['駅名', '緯度', '経度', '路線', '利用生徒数'])
    for name in sorted(STATIONS):
        lat, lng, line = STATIONS[name]
        w.writerow([name, lat, lng, line, usage.get(name, 0)])

# ============================================================
# 企業ごとの最寄り駅を判定（アクセス記載優先→なければ最近接計算）
# ============================================================
with open(BASE + r'\企業マスターDB.csv', encoding='utf-8-sig') as f:
    comp = list(csv.DictReader(f))

# アクセス文に出現しうる駅名（長い名前から優先マッチ）
station_names_sorted = sorted(STATIONS.keys(), key=len, reverse=True)

def station_in_text(text):
    """アクセス文から駅名を抽出。
    Pass1: 「○○駅」と完全一致するものを出現位置の早い順（同位置は長い駅名優先）。
           路線名「名鉄犬山線」等の誤マッチを防ぐため駅サフィックス必須。
    Pass2: 「駅」を外した駅名で補完（例:「小牧原」「味岡」駅）。ただし直後が「線」なら路線名なので除外。
    """
    if not text:
        return None
    # Pass1: 完全一致（駅サフィックス付き）
    best = None; best_pos = 10**9; best_len = 0
    for name in STATIONS:
        idx = text.find(name)
        if idx >= 0 and (idx < best_pos or (idx == best_pos and len(name) > best_len)):
            best, best_pos, best_len = name, idx, len(name)
    if best:
        return best
    # Pass2: 駅名ベース（路線名は除外）
    best = None; best_pos = 10**9
    for name in station_names_sorted:
        base = name[:-1]
        for m in re.finditer(re.escape(base), text):
            if text[m.end():m.end()+1] == '線':   # 「犬山線」等は路線名
                continue
            if m.start() < best_pos:
                best, best_pos = name, m.start()
            break
    return best

def nearest_station(coords):
    best = None; bd = 1e9
    for name, (lat, lng, line) in STATIONS.items():
        d = haversine(coords, (lat, lng))
        if d < bd:
            bd = d; best = name
    return best, round(bd, 1)

loc_path = BASE + r'\企業立地DB.csv'
with open(loc_path, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['No','企業名','住所','緯度','経度','最寄り駅','路線','駅からの距離km','判定方法','アクセス原文'])
    for r in comp:
        no = (r.get('No') or '').strip()
        if not no: continue
        name = r.get('企業名','').strip()
        addr = r.get('住所','').strip()
        try:
            lat = float(r.get('緯度','')); lng = float(r.get('経度',''))
            coords = (lat, lng)
        except ValueError:
            lat = lng = ''; coords = None
        access = r.get('アクセス','').strip()

        st = station_in_text(access)
        method = ''
        dist = ''
        if st:
            method = 'アクセス記載'
            if coords:
                dist = round(haversine(coords, STATIONS[st][:2]), 1)
        elif coords:
            st, dist = nearest_station(coords)
            method = '最近接計算'
        line = STATIONS[st][2] if st else ''
        w.writerow([no, name, addr, lat, lng, st or '', line, dist, method, access.replace('\n',' ')])

print('駅マスターDB:', station_path, '/ 駅数:', len(STATIONS))
print('企業立地DB :', loc_path, '/ 企業数:', sum(1 for r in comp if (r.get('No') or '').strip()))
