"""
残り35件の手動対処スクリプト:
- 海上スポット: 基準点+方位+距離で座標を計算
- 陸上スポット: ピンポイントクエリで再試行
"""
import csv, math, time, urllib.request, urllib.parse, json, sys

sys.stdout.reconfigure(encoding='utf-8')

INPUT  = "all_spots_with_coords.csv"
OUTPUT = "all_spots_with_coords.csv"
HEADERS = {"User-Agent": "dragon-shrine-checker/1.0 (research)"}

# --- 方位・距離から座標を計算 ---
def offset_coord(lat, lng, bearing_deg, dist_km):
    R = 6371.0
    d = dist_km / R
    b = math.radians(bearing_deg)
    lat1, lng1 = math.radians(lat), math.radians(lng)
    lat2 = math.asin(math.sin(lat1)*math.cos(d) + math.cos(lat1)*math.sin(d)*math.cos(b))
    lng2 = lng1 + math.atan2(math.sin(b)*math.sin(d)*math.cos(lat1), math.cos(d)-math.sin(lat1)*math.sin(lat2))
    return round(math.degrees(lat2), 5), round(math.degrees(lng2), 5)

# 海上スポット: {name: (lat, lng, note)}
# 基準点の座標は有名地点を使用
OCEAN_COORDS = {
    '第5赤龍(レエエオオン)':  (*offset_coord(45.52, 141.93, 315, 30),   '宗谷岬から北西30km沖'),
    '第1赤麟(ヘヨイリエリ)':  (*offset_coord(43.95, 147.00, 45,  150),  '色丹島から北東150km沖'),
    '第8赤鳳(ヨイクイール)':  (*offset_coord(43.33, 140.33, 270, 230),  '神威岬から真西230km沖'),
    '第8赤武(スエレン)':      (*offset_coord(41.93, 143.25, 180, 20),   '襟裳岬から真南20km沖'),
    '第7赤武(ソケイウエオ)':  (*offset_coord(37.65, 141.38, 60,  80),   '南相馬市から東北東80km沖'),
    '第7銀鳳(ヘイルキケル)':  (*offset_coord(36.30, 140.50, 90,  400),  '茨城県東沖400km'),
    '第7赤鳳(ヨエナル)':      (*offset_coord(27.04, 142.16, 210, 300),  '姉島から南南西300km沖'),
    '第3赤武(セレウヒルン)':  (*offset_coord(34.72, 139.39, 180, 10),   '伊豆大島から真南10km沖'),
    '第3赤鳳(ヨオエオオル)':  (*offset_coord(35.27, 139.16, 270, 3),    '小田原市沖3km'),
    '第3赤麟(ヘーオガエ)':    (*offset_coord(38.32, 138.53, 0,   60),   '佐渡弾埼岬から真北60km沖'),
    '第7銀龍(フナゲエビア)':  (*offset_coord(37.39, 136.89, 315, 220),  '輪島市沖北西220km大和堆'),
    '第4赤龍(ルーオイ)':      (*offset_coord(34.39, 136.27, 0,   220),  '経ヶ崎岬から真北220km沖'),
    '第5赤麟(ヘーケル)':      (34.15, 133.75, '瀬戸内海 大槌島付近'),
    '第9赤麟(ホウオオルエ)':  (*offset_coord(33.35, 131.99, 0,   45),   '佐田岬から真北45km沖'),
    '第5金武(ガエロヤエル)':  (*offset_coord(32.72, 133.02, 180, 300),  '足摺岬から南300km沖'),
    '第9赤龍(ロイコケワ)':    (*offset_coord(32.72, 133.02, 135, 30),   '足摺岬から南東30km沖'),
    '第4金麟(ナゲ・リーリ)':  (*offset_coord(33.79, 129.74, 270, 150),  '壱岐島から西150km海底'),
    '第2赤麟(フリオキオン)':  (*offset_coord(32.67, 128.84, 225, 250),  '福江島から南西250km沖'),
    '第1赤龍(リユカルエル)':  (29.22, 129.32, '草垣群島(下ノ島)'),
}

# 陸上スポット: {name: [query候補リスト]}
LAND_QUERIES = {
    '第9白麟(ネオア・ユキ)':  ['色丹島 北海道根室市', '色丹島'],
    '第3青龍(ヤエル)':        ['金華山 宮城県石巻市', '金華山島 宮城県'],
    '第6青麟(ババ・ニエヒーオ)': ['入道崎 秋田県男鹿市', '入道崎 男鹿'],
    '第1緑武(キエオオーイ)':  ['相俣ダム 群馬県', '赤谷湖 群馬県みなかみ'],
    '第6黄龍(ヒエコ・クエ)':  ['蛇喰渓谷 群馬県', '群馬県藤岡市下日野'],
    '第5銀龍(グイフエン)':    ['靖国神社 千代田区九段北', '靖国神社 東京都'],
    '第7白龍(ユボキ・エネ)':  ['霧ヶ峰 長野県茅野市', '八島ヶ原湿原 長野県'],
    '第3白麟(ウマバワウル)':  ['乗鞍岳 長野県', '乗鞍岳山頂'],
    '第1黄鳳(ヅエギグール)':  ['川浦渓谷 岐阜県', '岐阜県関市板取'],
    '第8白龍(ニウグネキゲ)':  ['六甲山最高峰 神戸市', '六甲山 兵庫県神戸市'],
    '第2白龍(ツフヌ・ヨネ)':  ['玉置山 奈良県十津川村', '玉置山 奈良県'],
    '第6青鳳(ユエケナリブ)':  ['友ヶ島 和歌山市', '友ヶ島 和歌山県'],
    '第9金武(ユエオブルン)':  ['古満目 高知県大月町', '高知県幡多郡大月町'],
    '第3緑龍(ホケイチ)':      ['にこ淵 高知県仁淀川', '高知県吾川郡いの町'],
    '第6白銀麟(テソケ・ジデ)': ['仰烏帽子山 熊本県', '烏帽子山 熊本県五木村'],
    '第4黒龍(ワエオリ)':      ['熊野座神社 熊本県高森町', '高森町 熊本県阿蘇郡'],
}

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

updated = 0
for row in rows:
    if row['geocode_status'] != 'failed':
        continue
    name = row['name']

    # 海上スポット
    if name in OCEAN_COORDS:
        lat, lng, note = OCEAN_COORDS[name]
        row['lat'] = lat
        row['lng'] = lng
        row['geocode_status'] = 'calculated'
        row['geocoded_address'] = note
        updated += 1
        print(f"CALC   | {name[:25]:25s} | {lat:.4f}, {lng:.4f} ({note})")
        continue

    # 陸上スポット
    if name in LAND_QUERIES:
        lat, lng, display = None, None, ""
        for q in LAND_QUERIES[name]:
            lat, lng, display = geocode(q)
            time.sleep(1.1)
            if lat:
                break
        if lat:
            row['lat'] = lat
            row['lng'] = lng
            row['geocode_status'] = 'ok'
            row['geocoded_address'] = display
            updated += 1
            print(f"OK     | {name[:25]:25s} | {lat:.4f}, {lng:.4f}")
        else:
            print(f"FAILED | {name[:25]:25s} | 全クエリ失敗")

fieldnames = ["prefecture","name","address","landmark","lat","lng","geocode_status","geocoded_address"]
with open(OUTPUT, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

ok    = sum(1 for r in rows if r['geocode_status'] in ('ok','calculated','manual'))
fail  = sum(1 for r in rows if r['geocode_status'] == 'failed')
print(f"\n更新: {updated}件 | ok/calculated={ok} | failed={fail}")
print(f"保存: {OUTPUT}")
