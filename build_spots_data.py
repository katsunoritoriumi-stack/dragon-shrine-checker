"""
all_spots_with_coords.csv (432件) から spots_data.js を再生成するスクリプト。
色・typeNameをname文字列から抽出し、pageUrlはfix_urls.pyと同じロジックで生成。
"""
import csv, json, re
from urllib.parse import quote

INPUT  = "all_spots_with_coords.csv"
OUTPUT = "spots_data.js"

# 色 → (fill, border)
COLOR_STYLE = {
    '白':   ('#F5F5F5', '#BBBBBB'),
    '白銀': ('#BDD0E0', '#8AAABB'),
    '銀':   ('#9E9E9E', '#616161'),
    '金':   ('#FFD700', '#B8860B'),
    '紫':   ('#AB47BC', '#6A1B9A'),
    '群青': ('#1565C0', '#0D3C77'),
    '青':   ('#29B6F6', '#0277BD'),
    '緑':   ('#66BB6A', '#2E7D32'),
    '黄':   ('#FFEE58', '#F9A825'),
    '橙':   ('#FFA726', '#E65100'),
    '赤':   ('#EF5350', '#B71C1C'),
    '黒':   ('#424242', '#212121'),
}

# 色の長い順に並べてマッチング（白銀が白より先にマッチするよう）
COLOR_ORDER = sorted(COLOR_STYLE.keys(), key=len, reverse=True)

# 龍神タイプ一覧（名前から抽出するためのパターン）
# 例: 第3白龍(シジキルチニ) → color=白, typeName=白龍
TYPE_SUFFIXES = ['龍', '鳳', '麟', '武']

FULLWIDTH_SLUG = {
    '第1白龍(ヘランターニ)': '第１白龍（ヘランターニ）',
    '第2白龍(ツフヌ・ヨネ)': '第２白龍（ツフヌ・ヨネ）',
}

BASE = 'https://zefuwa.riat-or.jp'
LIST_PATH = '/龍神所在地\u3000一覧'


def detect_color(name):
    for color in COLOR_ORDER:
        # 「第N白龍」の「白」が color の候補
        # 龍神名のパターン: 第N[色][タイプ]
        pat = rf'第\d+{re.escape(color)}[龍鳳麟武]'
        if re.search(pat, name):
            return color
    return None


def detect_typename(name, color):
    if not color:
        return None
    for suffix in TYPE_SUFFIXES:
        candidate = color + suffix
        if candidate in name:
            return candidate
    return None


def make_page_url(name, color, typename):
    if name in FULLWIDTH_SLUG:
        slug = FULLWIDTH_SLUG[name]
    else:
        slug = name.replace('(', '').replace(')', '')
    path = f"{LIST_PATH}/{color}/{typename}/{slug}"
    return BASE + quote(path, safe='/')


with open(INPUT, encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

spots = []
skipped = 0
for row in rows:
    lat_s = row.get('lat', '').strip()
    lng_s = row.get('lng', '').strip()
    if not lat_s or not lng_s:
        skipped += 1
        continue
    try:
        lat = float(lat_s)
        lng = float(lng_s)
    except ValueError:
        skipped += 1
        continue

    name = row['name']
    color = detect_color(name)
    typename = detect_typename(name, color)

    if not color or not typename:
        # フォールバック: 不明な場合は白として扱う
        color = color or '白'
        typename = typename or (color + '龍')

    fill, border = COLOR_STYLE.get(color, ('#AAAAAA', '#666666'))
    page_url = make_page_url(name, color, typename)

    spots.append({
        'prefecture': row['prefecture'],
        'name': name,
        'address': row['address'],
        'landmark': row['landmark'],
        'lat': lat,
        'lng': lng,
        'color': color,
        'typeName': typename,
        'pageUrl': page_url,
        'fill': fill,
        'border': border,
    })

print(f"生成: {len(spots)}件 (スキップ: {skipped}件)")

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write('const SPOTS = ')
    f.write(json.dumps(spots, ensure_ascii=False, separators=(',', ':')))
    f.write(';\n')

print(f"保存: {OUTPUT}")

# 色別集計
from collections import Counter
color_count = Counter(s['color'] for s in spots)
for c, n in sorted(color_count.items()):
    print(f"  {c}: {n}件")
