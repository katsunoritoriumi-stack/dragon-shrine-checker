# -*- coding: utf-8 -*-
import csv, json, time, urllib.request, urllib.parse
from pathlib import Path

CSV_INPUT = "spots.csv"
GEOCODING_API_KEY = "AIzaSyDXOSXgyhQ18mcBW-Ipyn7sYsrsqACHmVQ"
OUTPUT_JSON = "review_results.json"
OUTPUT_REPORT = "report.html"

def rev_geo(lat, lng, key):
    url = "https://maps.googleapis.com/maps/api/geocode/json?latlng={},{}&language=ja&key={}".format(lat, lng, key)
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            d = json.loads(r.read())
        if d["status"] == "OK" and d["results"]:
            return d["results"][0]["formatted_address"]
        return d["status"]
    except Exception as e:
        return str(e)

def make_report(results):
    rows_html = ""
    for r in results:
        map_url = "https://www.google.com/maps?q={},{}&z=15".format(r["lat_original"], r["lng_original"])
        rows_html += """
<div style="background:white;border-radius:8px;padding:16px;margin:12px 0;box-shadow:0 2px 4px rgba(0,0,0,0.1)">
  <div><span style="background:#34495e;color:white;padding:2px 8px;border-radius:4px;font-size:.85em">Row {row_num}</span> <strong>{name}</strong></div>
  <div style="background:#f8f9fa;padding:10px;border-radius:4px;margin:8px 0;font-size:.9em">
    <div><b>座標:</b> {lat}, {lng}</div>
    <div><b>住所:</b> {addr}</div>
    <div><b>landmark:</b> {lm}</div>
  </div>
  <a href="{map_url}" target="_blank" style="display:inline-block;padding:8px 16px;background:#4285f4;color:white;border-radius:6px;text-decoration:none;font-size:.9em">マップで確認</a>
  <div style="margin-top:10px;font-size:.9em">
    ズレている場合は正しい座標を入力:
    <input id="lat{row_num}" type="text" placeholder="緯度" style="width:130px;padding:4px;margin:4px;border:1px solid #ddd;border-radius:4px">
    <input id="lng{row_num}" type="text" placeholder="経度" style="width:130px;padding:4px;margin:4px;border:1px solid #ddd;border-radius:4px">
    <button onclick="fix({row_num})" style="padding:5px 12px;background:#27ae60;color:white;border:none;border-radius:4px;cursor:pointer">記録</button>
    <span id="ok{row_num}" style="color:#27ae60;display:none">記録しました</span>
  </div>
</div>""".format(
            row_num=r["row_num"], name=r["name"],
            lat=r["lat_original"], lng=r["lng_original"],
            addr=r["reverse_address"], lm=r["landmark"],
            map_url=map_url)

    html = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><title>座標確認レポート</title>
<style>body{{font-family:sans-serif;background:#f5f5f5;padding:20px;max-width:900px;margin:0 auto;color:#333}}
h1{{color:#2c3e50;border-bottom:3px solid #e74c3c;padding-bottom:10px}}
textarea{{width:100%;height:150px;font-size:.85em;border:1px solid #ddd;border-radius:4px;padding:8px}}</style>
</head><body>
<h1>龍神マップ 座標確認レポート</h1>
<p>各行の「マップで確認」で座標が正しいか確認し、ズレている場合は正しい座標を入力して「記録」を押してください。</p>
<p><strong>合計 {total} 件</strong></p>
{rows}
<div style="background:white;padding:20px;border-radius:8px;margin-top:20px;box-shadow:0 2px 4px rgba(0,0,0,0.1)">
<h2>修正リスト</h2>
<textarea id="out" readonly placeholder="記録した修正内容がここに表示されます"></textarea><br>
<button onclick="copy()" style="margin-top:8px;padding:8px 16px;background:#34495e;color:white;border:none;border-radius:4px;cursor:pointer">コピー</button>
</div>
<script>
var fixes={{}};
function fix(n){{
  var la=document.getElementById("lat"+n).value.trim();
  var ln=document.getElementById("lng"+n).value.trim();
  if(!la||!ln){{alert("緯度と経度を入力してください");return;}}
  fixes[n]={{lat:la,lng:ln}};
  document.getElementById("ok"+n).style.display="inline";
  update();
}}
function update(){{
  var lines=["行番号,修正後緯度,修正後経度"];
  for(var k in fixes) lines.push(k+","+fixes[k].lat+","+fixes[k].lng);
  document.getElementById("out").value=lines.join("\\n");
}}
function copy(){{
  document.getElementById("out").select();
  document.execCommand("copy");
  alert("コピーしました！Claudeに貼り付けてください。");
}}
</script>
</body></html>""".format(total=len(results), rows=rows_html)

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write(html)

def main():
    rows = []
    with open(CSV_INPUT, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 2):
            rows.append({"row_num": i})
            rows[-1].update(row)
    print("CSV: {} rows".format(len(rows)))
    results = []
    for i, row in enumerate(rows):
        name = row.get("name", "").strip()
        landmark = row.get("landmark", "").strip()
        lat_s = row.get("lat", "").strip()
        lng_s = row.get("lng", "").strip()
        rn = row["row_num"]
        try:
            lat = float(lat_s)
            lng = float(lng_s)
        except:
            print("Row{}: skip".format(rn))
            continue
        print("[{}/{}] Row{}: {}".format(i+1, len(rows), rn, name[:15]), end=" ... ")
        rev = rev_geo(lat, lng, GEOCODING_API_KEY)
        print(rev[:50] if rev else "NG")
        results.append({
            "row_num": rn, "name": name, "landmark": landmark,
            "lat_original": lat, "lng_original": lng,
            "reverse_address": rev
        })
        time.sleep(0.1)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    make_report(results)
    print("Done: {} items. Report: {}".format(len(results), OUTPUT_REPORT))

if __name__ == "__main__":
    main()