"""
龍神マップ 座標修正反映スクリプト
====================================
check_coordinates.py でレポートを確認後、
review_results.json を編集して修正座標を入力してから、
このスクリプトを実行するとCSVが更新されます。

使い方:
  1. report.html でズレを確認する
  2. review_results.json を開き、修正したい行の
     "fixed_lat" と "fixed_lng" に正しい座標を入力する
  3. "confirmed": true に変更する
  4. python apply_fixes.py を実行する
  5. spots_fixed.csv が出力されるので、スプレッドシートにインポートする
"""

import csv
import json
from pathlib import Path

CSV_INPUT   = "spots.csv"
JSON_INPUT  = "review_results.json"
CSV_OUTPUT  = "spots_fixed.csv"

def apply_fixes():
    # JSONを読み込む
    json_path = Path(JSON_INPUT)
    if not json_path.exists():
        print(f"❌ {JSON_INPUT} が見つかりません。先に check_coordinates.py を実行してください。")
        return

    with open(json_path, encoding="utf-8") as f:
        results = json.load(f)

    # 修正対象だけ抽出
    fixes = {r["row_num"]: r for r in results if r.get("confirmed") and r.get("fixed_lat") and r.get("fixed_lng")}

    if not fixes:
        print("⚠️  confirmed=true かつ fixed_lat/fixed_lng が設定されている行がありません。")
        print("   review_results.json を編集してから再実行してください。")
        return

    print(f"✏️  {len(fixes)} 件の修正を適用します...\n")

    # 元CSVを読み込んで修正
    csv_path = Path(CSV_INPUT)
    rows = []
    fieldnames = []
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for i, row in enumerate(reader, start=2):
            if i in fixes:
                fix = fixes[i]
                old_lat = row.get("lat", "")
                old_lng = row.get("lng", row.get("ing", ""))  # 列名ゆらぎ対応
                row["lat"] = str(fix["fixed_lat"])
                # lng か ing か判定
                if "lng" in row:
                    row["lng"] = str(fix["fixed_lng"])
                elif "ing" in row:
                    row["ing"] = str(fix["fixed_lng"])
                print(f"  行{i}: {fix['name']}")
                print(f"    lat: {old_lat} → {fix['fixed_lat']}")
                print(f"    lng: {old_lng} → {fix['fixed_lng']}")
            rows.append(row)

    # 修正済みCSVを書き出す
    with open(CSV_OUTPUT, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ 修正済みCSVを保存しました: {CSV_OUTPUT}")
    print(f"   このファイルをGoogleスプレッドシートにインポートしてください。")
    print(f"   （ファイル → インポート → アップロード → 現在のシートを置き換える）")

if __name__ == "__main__":
    apply_fixes()
