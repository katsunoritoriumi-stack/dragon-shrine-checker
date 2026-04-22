"""
geocode_status='failed' の92件を複数戦略で再ジオコーディングするスクリプト。

戦略（順番に試行）:
  1. ランドマークから有名地名を抽出してクエリ
  2. 住所の市区町村レベルのみ
  3. 都道府県 + ランドマーク抽出名
"""
import csv, re, time, urllib.request, urllib.parse, json, sys

sys.stdout.reconfigure(encoding='utf-8')

INPUT  = "all_spots_with_coords.csv"
OUTPUT = "all_spots_with_coords.csv"
HEADERS = {"User-Agent": "dragon-shrine-checker/1.0 (research project)"}

# ランドマーク文字列から有名地名を抽出するパターン
PLACE_PATTERNS = [
    r'([^\(（]+山)\s*[\(（]',          # 〇〇山(標高...)
    r'([^\(（]+山)\s*$',               # 〇〇山
    r'([^\(（]+岬)',                    # 〇〇岬
    r'([^\(（]+湖)',                    # 〇〇湖
    r'([^\(（]+池)',                    # 〇〇池
    r'([^\(（]+渓谷)',                  # 〇〇渓谷
    r'([^\(（]+神社)',                  # 〇〇神社
    r'([^\(（]+峡)',                    # 〇〇峡
    r'([^\(（]+滝)',                    # 〇〇滝
    r'([^\(（]+ダム)',                  # 〇〇ダム
    r'([^\(（]+灯台)',                  # 〇〇灯台
    r'([^\(（]+温泉)',                  # 〇〇温泉
    r'([^\(（]+沼)',                    # 〇〇沼
    r'([^\(（]+洞)',                    # 〇〇洞
]

def extract_place(landmark):
    """ランドマーク文字列から検索に使える地名を抽出"""
    for pat in PLACE_PATTERNS:
        m = re.search(pat, landmark)
        if m:
            name = m.group(1).strip()
            # 短すぎるものは除外
            if len(name) >= 3:
                return name
    return None

def extract_city(address):
    """住所から都道府県+市区町村を抽出"""
    m = re.match(r'([\u90fd\u9053\u5e9c\u770c].+?[市区町村郡])', address)
    if m:
        return m.group(1)
    # 括弧内の第2住所も試す
    m2 = re.search(r'[\(（]([\u90fd\u9053\u5e9c\u770c].+?[市区町村郡])[\)）]', address)
    if m2:
        return m2.group(1)
    return None

def extract_pref(address):
    """都道府県のみ"""
    m = re.match(r'([\u90fd\u9053\u5e9c\u770c][^\s\(（]+?[都道府県])', address)
    if m:
        return m.group(1)
    return None

def is_ocean(address):
    """海上スポットかどうか"""
    return any(k in address for k in ['沖合', '沖の', '海溝', '海底', '太平洋', '日本海', 'オホーツク', '東シナ海', '瀬戸内海', '北太平洋'])

def geocode(query):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": query, "format": "json", "limit": 1, "countrycodes": "jp"
    })
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read())
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"]), results[0].get("display_name","")
    except Exception as e:
        print(f"  エラー: {e}")
    return None, None, ""

with open(INPUT, encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

failed = [r for r in rows if r['geocode_status'] == 'failed']
print(f"対象: {len(failed)}件")

updated = 0
ocean_skipped = 0

for i, row in enumerate(failed, 1):
    name     = row['name']
    address  = row['address']
    landmark = row['landmark']
    pref     = row['prefecture']

    # 海上スポットはスキップ（座標計算不可）
    if is_ocean(address):
        print(f"[{i:2d}] OCEAN  | {name[:20]}")
        ocean_skipped += 1
        continue

    queries = []

    # 戦略1: ランドマークから地名抽出 + 都道府県
    place = extract_place(landmark) if landmark else None
    if place:
        queries.append(f"{place} {pref}")
        queries.append(place)

    # 戦略2: 住所の市区町村
    city = extract_city(address)
    if city:
        queries.append(city)
        if landmark:
            queries.append(f"{city} {landmark[:20]}")

    # 戦略3: 住所全体（括弧除去）
    clean_addr = re.sub(r'[\(（][^)）]*[\)）]', '', address).strip()
    if clean_addr and clean_addr not in queries:
        queries.append(clean_addr)

    # 戦略4: 都道府県 + ランドマーク先頭
    if landmark:
        queries.append(f"{pref} {landmark[:30]}")

    lat, lng, display = None, None, ""
    for q in queries:
        lat, lng, display = geocode(q)
        time.sleep(1.1)
        if lat is not None:
            break

    if lat is not None:
        row['lat'] = lat
        row['lng'] = lng
        row['geocode_status'] = 'ok'
        row['geocoded_address'] = display
        updated += 1
        print(f"[{i:2d}] OK     | {name[:22]:22s} | {q[:40]}")
    else:
        print(f"[{i:2d}] FAILED | {name[:22]:22s} | 全戦略失敗")

# 保存
fieldnames = ["prefecture","name","address","landmark","lat","lng","geocode_status","geocoded_address"]
with open(OUTPUT, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

ok_total  = sum(1 for r in rows if r['geocode_status'] == 'ok')
fail_total = sum(1 for r in rows if r['geocode_status'] == 'failed')
print(f"\n更新: {updated}件成功 / {ocean_skipped}件海上スキップ")
print(f"合計: ok={ok_total} failed={fail_total}")
print(f"保存: {OUTPUT}")
