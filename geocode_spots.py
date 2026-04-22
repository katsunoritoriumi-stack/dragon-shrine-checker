import csv
import time
import urllib.request
import urllib.parse
import json

INPUT = "all_spots.csv"
OUTPUT = "all_spots_with_coords.csv"
HEADERS = {"User-Agent": "dragon-shrine-checker/1.0 (research project)"}

def geocode(query):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "jp",
    })
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read())
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"]), results[0].get("display_name", "")
    except Exception as e:
        print(f"  エラー: {e}")
    return None, None, ""

with open(INPUT, encoding="utf-8-sig") as f:
    spots = list(csv.DictReader(f))

total = len(spots)
print(f"対象: {total}件")

results = []
for i, spot in enumerate(spots, 1):
    pref    = spot["prefecture"]
    name    = spot["name"]
    address = spot["address"]
    landmark = spot["landmark"]

    # 試行順: 住所+ランドマーク → 住所のみ → 都道府県+ランドマーク
    queries = []
    if address and landmark:
        queries.append(f"{address} {landmark}")
    if address:
        queries.append(address)
    if pref and landmark:
        queries.append(f"{pref} {landmark}")

    lat, lng, display = None, None, ""
    for q in queries:
        lat, lng, display = geocode(q)
        time.sleep(1.1)  # Nominatim利用規約: 1秒以上の間隔
        if lat is not None:
            break

    status = "ok" if lat is not None else "failed"
    results.append({
        "prefecture": pref,
        "name": name,
        "address": address,
        "landmark": landmark,
        "lat": lat if lat is not None else "",
        "lng": lng if lng is not None else "",
        "geocode_status": status,
        "geocoded_address": display,
    })

    elapsed_est = (total - i) * 1.1
    print(f"[{i:3d}/{total}] {status:6s} | {name[:20]:20s} | lat={lat}, lng={lng}")

with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["prefecture","name","address","landmark","lat","lng","geocode_status","geocoded_address"])
    writer.writeheader()
    writer.writerows(results)

ok_count = sum(1 for r in results if r["geocode_status"] == "ok")
print(f"\n完了: {ok_count}/{total}件 取得成功")
print(f"保存: {OUTPUT}")
