"""
spots_data.js の pageUrl を修正するスクリプト。

修正ルール:
- 第1白龍(ヘランターニ)、第2白龍(ツフヌ・ヨネ) のみ全角数字・全角括弧
- その他 430 件は括弧を除去してそのまま（中黒・などは維持）
"""

import json
import re
from urllib.parse import quote

INPUT = "spots_data.js"
OUTPUT = "spots_data.js"

# 2件だけ全角スラッグ
FULLWIDTH_SLUG = {
    '第1白龍(ヘランターニ)': '第１白龍（ヘランターニ）',
    '第2白龍(ツフヌ・ヨネ)': '第２白龍（ツフヌ・ヨネ）',
}

BASE = 'https://zefuwa.riat-or.jp'
LIST_PATH = '/龍神所在地\u3000一覧'  # 全角スペース


def make_page_url(spot):
    name = spot['name']
    color = spot['color']
    type_name = spot['typeName']

    if name in FULLWIDTH_SLUG:
        slug = FULLWIDTH_SLUG[name]
    else:
        # 括弧のみ除去（中黒・など他の記号は維持）
        slug = name.replace('(', '').replace(')', '')

    path = f"{LIST_PATH}/{color}/{type_name}/{slug}"
    return BASE + quote(path, safe='/')


# spots_data.js を読み込み（JS→JSON）
with open(INPUT, encoding='utf-8') as f:
    raw = f.read()

# "const SPOTS = [...];" → JSON配列として解析
m = re.match(r'const SPOTS = (\[.*\]);?\s*$', raw, re.DOTALL)
if not m:
    raise ValueError("spots_data.js のフォーマットが期待と異なります")

spots = json.loads(m.group(1))
print(f"読み込み: {len(spots)} 件")

# URL 修正
fixed = 0
for spot in spots:
    new_url = make_page_url(spot)
    if spot['pageUrl'] != new_url:
        spot['pageUrl'] = new_url
        fixed += 1

print(f"URL修正: {fixed} 件")

# 書き出し
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write('const SPOTS = ')
    f.write(json.dumps(spots, ensure_ascii=False, separators=(',', ':')))
    f.write(';\n')

print(f"保存完了: {OUTPUT}")
