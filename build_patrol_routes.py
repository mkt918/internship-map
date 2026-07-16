# -*- coding: utf-8 -*-
"""
教員見回りルート生成スクリプト
- 日付ごとに企業をクラスタリング（最大4社/教員）
- 各クラスター内をTSP最近傍法で並べる
- 学校(学校)を出発/帰着点とする
"""
import csv, re, json, random
from math import radians, sin, cos, sqrt, atan2
from collections import defaultdict

BASE = r'C:\antigravity\public\00_作業\2026-06\インターンシップ管理'

# 学校 座標
SCHOOL = (35.3338, 136.8908)
SCHOOL_NAME = '学校（出発・帰着）'
MAX_PER_TEACHER = 3
MAX_TEACHERS = 5

def haversine(a, b):
    R = 6371.0
    dlat = radians(b[0]-a[0]); dlon = radians(b[1]-a[1])
    h = sin(dlat/2)**2 + cos(radians(a[0]))*cos(radians(b[0]))*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(h), sqrt(1-h))

# 企業マスターDB（No→座標のフォールバック用）
compDB = {}
with open(BASE + r'\企業マスターDB.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        no = (r.get('No') or '').strip()
        try:
            lat = float(r['緯度']); lng = float(r['経度'])
        except:
            lat = lng = None
        compDB[no] = {'name': r.get('企業名','').strip(), 'lat': lat, 'lng': lng,
                      'cat': r.get('業種カテゴリ','').strip()}

# 日付×企業グループ化（最終正規化.csv = 260710データ反映済み・欠席除外済み・氏名付き）
date_comp = defaultdict(dict)
with open(BASE + r'\最終正規化.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        no = (row.get('配属企業No') or '').strip()
        cname = (row.get('企業名') or '').strip()
        date = (row.get('日付') or '').strip()
        nen = row['学年'].strip(); kumi = row['組'].strip(); ban = row['番号'].strip()
        sname = (row.get('氏名') or '').strip()
        try:
            lat = float(row.get('緯度', '')); lng = float(row.get('経度', ''))
        except (ValueError, TypeError):
            comp = compDB.get(no)
            lat = comp['lat'] if comp else None
            lng = comp['lng'] if comp else None
        cat = (row.get('業種カテゴリ') or '').strip()
        key = no
        if date not in date_comp:
            date_comp[date] = {}
        if key not in date_comp[date]:
            date_comp[date][key] = {'name': cname, 'lat': lat, 'lng': lng, 'cat': cat, 'students': [], 'student_names': {}}
        sid = f'{nen}-{kumi}-{ban}'
        date_comp[date][key]['students'].append(sid)
        date_comp[date][key]['student_names'][sid] = sname

def tsp_nearest(points, start):
    unvisited = list(range(len(points)))
    route = []
    cur = start
    while unvisited:
        nearest = min(unvisited, key=lambda i: haversine(cur, (points[i]['lat'], points[i]['lng'])))
        route.append(nearest)
        cur = (points[nearest]['lat'], points[nearest]['lng'])
        unvisited.remove(nearest)
    return route

def kmeans_cluster(points, k, seed=0):
    random.seed(seed)
    if len(points) <= k:
        return [[i] for i in range(len(points))]
    indices = list(range(len(points)))
    # k-means++ init
    centers_idx = [random.choice(indices)]
    while len(centers_idx) < k:
        dists = [min(haversine((points[i]['lat'],points[i]['lng']),
                               (points[c]['lat'],points[c]['lng'])) for c in centers_idx)
                 for i in indices]
        total = sum(dists)
        r = random.random() * total
        cum = 0
        for i, d in enumerate(dists):
            cum += d
            if cum >= r:
                centers_idx.append(indices[i]); break
        else:
            centers_idx.append(indices[-1])
    centers = [{'lat': points[i]['lat'], 'lng': points[i]['lng']} for i in centers_idx]
    for _ in range(100):
        clusters = [[] for _ in range(k)]
        for i, p in enumerate(points):
            nc = min(range(k), key=lambda c: haversine((p['lat'],p['lng']),(centers[c]['lat'],centers[c]['lng'])))
            clusters[nc].append(i)
        new_centers = []
        for c in range(k):
            if clusters[c]:
                avg_lat = sum(points[i]['lat'] for i in clusters[c]) / len(clusters[c])
                avg_lng = sum(points[i]['lng'] for i in clusters[c]) / len(clusters[c])
                new_centers.append({'lat': avg_lat, 'lng': avg_lng})
            else:
                new_centers.append(centers[c])
        if new_centers == centers:
            break
        centers = new_centers
    return [c for c in clusters if c]

def split_oversize(clusters, comps, max_size):
    result = []
    for c in clusters:
        if len(c) <= max_size:
            result.append(c)
        else:
            sub_k = -(-len(c) // max_size)
            sub_pts = [comps[i] for i in c]
            sub_cls = kmeans_cluster(sub_pts, sub_k, seed=1)
            for sc in sub_cls:
                result.append([c[i] for i in sc])
    return result

def route_cost(clusters, comps):
    cost = 0
    for c in clusters:
        pts = [comps[i] for i in c]
        prev = SCHOOL
        for p in pts:
            cost += haversine(prev, (p['lat'], p['lng']))
            prev = (p['lat'], p['lng'])
        cost += haversine(prev, SCHOOL)
    return cost

def date_sort_key(d):
    m = re.search(r'(\d+)/(\d+)', d)
    return (int(m.group(1)), int(m.group(2))) if m else (99, 99)

all_results = []
for date in sorted(date_comp.keys(), key=date_sort_key):
    comps = list(date_comp[date].values())
    n = len(comps)
    n_teachers = min(MAX_TEACHERS, -(-n // MAX_PER_TEACHER))

    # --- 改良案B: 1-5企業を先に地理クラスタリング、残りを別途 ---
    idx_15   = [i for i, c in enumerate(comps) if any(s.startswith('1-5-') for s in c['students'])]
    idx_rest = [i for i in range(n) if i not in idx_15]

    def best_cluster(indices, pts_all):
        """indices に含まれる企業を MAX_PER_TEACHER 以下に分割（最良シード選択）"""
        pts = [pts_all[i] for i in indices]
        m = len(pts)
        if m == 0:
            return []
        k_local = max(1, -(-m // MAX_PER_TEACHER))
        if m <= k_local:
            return [[indices[j]] for j in range(m)]
        best_c = None; best_v = float('inf')
        for seed in range(30):
            cls = kmeans_cluster(pts, k_local, seed=seed)
            cls = split_oversize(cls, pts, MAX_PER_TEACHER)
            if any(len(c) > MAX_PER_TEACHER for c in cls):
                continue
            v = route_cost(cls, pts)
            if v < best_v:
                best_v = v; best_c = cls
        if best_c is None:
            best_c = [[j] for j in range(0, m, MAX_PER_TEACHER)]
        # ローカルインデックス → グローバルインデックスに変換
        return [[indices[j] for j in grp] for grp in best_c]

    clusters_15   = best_cluster(idx_15, comps)
    clusters_rest = best_cluster(idx_rest, comps)
    clusters = clusters_15 + clusters_rest

    n_teachers = min(MAX_TEACHERS, len(clusters))

    day_routes = []
    for t_idx, cluster in enumerate(clusters):
        pts = [comps[i] for i in cluster]
        order = tsp_nearest(pts, SCHOOL)
        ordered_pts = [pts[i] for i in order]
        prev = SCHOOL; total_km = 0; stops = []
        for p in ordered_pts:
            d = haversine(prev, (p['lat'], p['lng']))
            total_km += d
            stops.append({'name': p['name'], 'cat': p['cat'],
                          'lat': p['lat'], 'lng': p['lng'],
                          'students': p['students'],
                          'student_names': [p['student_names'].get(s, '') for s in p['students']],
                          'dist_from_prev': round(d, 1)})
            prev = (p['lat'], p['lng'])
        total_km += haversine(prev, SCHOOL)
        day_routes.append({
            'teacher': t_idx + 1,
            'stops': stops,
            'total_km': round(total_km, 1),
            'n_companies': len(stops),
            'n_students': sum(len(s['students']) for s in stops)
        })

    all_results.append({
        'date': date,
        'n_companies': n,
        'n_students': sum(len(c['students']) for c in comps),
        'n_teachers': len(clusters),
        'routes': day_routes
    })

with open(BASE + r'\patrol_routes.json', 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
print('patrol_routes.json 生成完了')
for day in all_results:
    print(f"\n{day['date']}: {day['n_companies']}社/{day['n_students']}名 → 教員{day['n_teachers']}名")
    for r in day['routes']:
        names = ' → '.join(s['name'][:12] for s in r['stops'])
        print(f"  教員{r['teacher']}: {r['n_companies']}社/{r['n_students']}名 計{r['total_km']}km | {names}")
