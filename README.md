# 龍神マップ 座標検証ツール

## ファイル構成

```
dragon-shrine-checker/
├── check_coordinates.py   ← ① 座標を検証してレポートを作る
├── apply_fixes.py         ← ③ 修正をCSVに反映する
└── README.md              ← このファイル
```

---

## 使い方（全体の流れ）

### Step 1：CSVをダウンロード

1. Googleスプレッドシートを開く
2. メニュー「ファイル」→「ダウンロード」→「カンマ区切り値（.csv）」
3. ダウンロードしたファイルを `spots.csv` という名前にして、このフォルダに入れる

---

### Step 2：APIキーを設定

`check_coordinates.py` をテキストエディタで開き、以下の行を修正：

```python
GEOCODING_API_KEY = "YOUR_API_KEY_HERE"  ← ここにAPIキーを貼り付ける
```

**APIキーの取得方法：**
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを作成（または既存を選択）
3. 「APIとサービス」→「ライブラリ」→「Geocoding API」を有効化
4. 「認証情報」→「APIキーを作成」

---

### Step 3：検証を実行

ターミナル（コマンドプロンプト）で：

```bash
python check_coordinates.py
```

実行後、`report.html` が生成されます。

---

### Step 4：レポートを確認

`report.html` をブラウザで開くと：
- ⚠️ 要確認の場所一覧が表示される
- Googleマップリンクで現地を確認できる
- 候補座標のリンクも表示される

---

### Step 5：修正内容を入力

`review_results.json` をテキストエディタで開き、
修正したい行の以下の値を変更：

```json
{
  "row_num": 5,
  "name": "〇〇神社",
  ...
  "fixed_lat": 35.1234,   ← 正しい緯度を入力
  "fixed_lng": 138.5678,  ← 正しい経度を入力
  "confirmed": true        ← false → true に変更
}
```

---

### Step 6：修正を反映

```bash
python apply_fixes.py
```

`spots_fixed.csv` が生成されます。

---

### Step 7：スプレッドシートにインポート

1. Googleスプレッドシートを開く
2. 「ファイル」→「インポート」→「アップロード」
3. `spots_fixed.csv` を選択
4. 「現在のシートを置き換える」を選択してインポート

---

## よくあるトラブル

| 症状 | 対処法 |
|------|--------|
| `CSVファイルが見つかりません` | spots.csv をこのフォルダに置いたか確認 |
| `取得失敗（REQUEST_DENIED）` | APIキーが間違っているか、Geocoding APIが有効になっていない |
| `取得失敗（OVER_QUERY_LIMIT）` | API利用制限に達した。少し待ってから再実行 |
| 座標の列が読めない | CSVの列名が `lng` か `ing` か確認（スクリプトが自動対応） |
