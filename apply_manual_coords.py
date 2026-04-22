"""
geocode_failed_spots.xlsx に入力した緯度・経度を
all_spots_with_coords.csv に反映して
all_spots_with_coords_updated.csv として保存するスクリプト。

使い方:
  1. geocode_failed_spots.xlsx の「修正後緯度」「修正後経度」列に座標を入力して保存
  2. python apply_manual_coords.py を実行
"""

import csv
import openpyxl

EXCEL_FILE = "geocode_failed_spots.xlsx"
CSV_IN     = "all_spots_with_coords.csv"
CSV_OUT    = "all_spots_with_coords_updated.csv"

# --- Excelから修正済み座標を読み込む ---
wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
ws = wb.active

manual_coords = {}  # key: name → (lat, lng)
for row in ws.iter_rows(min_row=2, values_only=True):
    no, prefecture, name, address, landmark, lat, lng, note = (list(row) + [None]*8)[:8]
    if name and lat and lng:
        try:
            manual_coords[name] = (float(lat), float(lng))
        except (ValueError, TypeError):
            pass

print(f"Excelから読み込んだ修正座標: {len(manual_coords)}件")

# --- CSVを読み込んで反映 ---
with open(CSV_IN, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

updated = 0
for row in rows:
    if row["geocode_status"] == "failed" and row["name"] in manual_coords:
        lat, lng = manual_coords[row["name"]]
        row["lat"] = lat
        row["lng"] = lng
        row["geocode_status"] = "manual"
        updated += 1

still_failed = sum(1 for r in rows if r["geocode_status"] == "failed")

# --- 保存 ---
fieldnames = ["prefecture", "name", "address", "landmark", "lat", "lng", "geocode_status", "geocoded_address"]
with open(CSV_OUT, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"反映件数: {updated}件")
print(f"未解決: {still_failed}件")
print(f"保存完了: {CSV_OUT}")
