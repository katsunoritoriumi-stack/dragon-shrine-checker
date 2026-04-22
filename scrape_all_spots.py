import re
import csv
import requests
from bs4 import BeautifulSoup

URL = "https://zefuwa.riat-or.jp/%e9%be%8d%e7%a5%9e%e6%89%80%e5%9c%a8%e5%9c%b0%e3%80%80%e4%b8%80%e8%a6%a7%e3%80%80%e6%89%80%e5%9c%a8%e5%9c%b0%e7%9c%8c%e5%88%a5"

resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
resp.encoding = "utf-8"
soup = BeautifulSoup(resp.text, "html.parser")
page_text = soup.get_text(separator="\t")

spots = []
pref_blocks = re.split(r'[〈《](.+?)[〉》]', page_text)

current_pref = ""
for block in pref_blocks:
    block = block.strip()
    if not block:
        continue
    if "※" not in block and len(block) < 15:
        current_pref = block
        continue
    if not current_pref:
        continue

    entries = block.split("※")
    for entry in entries:
        entry = entry.strip()
        if not entry or not entry.startswith("第"):
            continue

        name_match = re.match(r"^(第\d+[^\t\n(]+\([^)]+\))", entry)
        name = name_match.group(1) if name_match else ""
        rest = entry[len(name):].strip() if name_match else entry

        tab_idx = rest.find("\t")
        if tab_idx >= 0:
            address = rest[:tab_idx].strip()
            landmark = rest[tab_idx + 1:].strip()
        else:
            address = rest.strip()
            landmark = ""

        address = re.sub(r"\s+", " ", address).strip()
        landmark = re.sub(r"\s+", " ", landmark).strip()

        spots.append({
            "prefecture": current_pref,
            "name": name,
            "address": address,
            "landmark": landmark,
        })

print(f"抽出件数: {len(spots)}")

output_path = "all_spots.csv"
with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["prefecture", "name", "address", "landmark"])
    writer.writeheader()
    writer.writerows(spots)

print(f"保存完了: {output_path}")
