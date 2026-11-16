#!/usr/bin/env python3
"""ぬまサーチ 住所と座標の突き合わせチェック

  python3 tools/check_coords.py            # 5m以内を「正しい」とみなす
  python3 tools/check_coords.py --ok 50    # 判定のしきい値(m)を変える

index.html の各スポットの住所を国土地理院の住所検索で座標にし、
登録されている lat/lng との距離を測る。結果は tools/coord_check.csv に保存
(距離の大きい順。Excel・スプシでそのまま開ける)。

判定:
  OK      … しきい値以内
  要確認  … しきい値〜2km
  要修正  … 2km超
  検索不可 … 住所が見つからない(南魚沼市内でヒットしない)
注意: 地理院の住所検索は番地まで特定できず町名の代表点を返すことがある。
「一致した住所」列が入力住所より短い行は、距離が大きくても座標が誤りとは限らない。
"""
import csv
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from address_sheet import INDEX, read_spots  # noqa: E402

OUT = Path(__file__).resolve().parent / "coord_check.csv"
FAR = 2000


def geocode(address):
    url = "https://msearch.gsi.go.jp/address-search/AddressSearch?q=" + urllib.parse.quote(address)
    req = urllib.request.Request(url, headers={"User-Agent": "numa-search-tools"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except Exception:
            time.sleep(1)
    else:
        return None
    for f in data:
        lng, lat = f["geometry"]["coordinates"]
        title = f["properties"].get("title", "")
        if "南魚沼市" in title and 36 < lat < 38 and 138 < lng < 140:
            return lat, lng, title
    return None


def dist_m(a, b):
    r = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def main():
    ok = 5.0
    if "--ok" in sys.argv:
        ok = float(sys.argv[sys.argv.index("--ok") + 1])
    spots = read_spots(INDEX.read_text(encoding="utf-8"))
    rows = []
    for i, s in enumerate(spots, 1):
        addr = s["address"].replace('\\"', '"')
        g = geocode(addr)
        if g is None:
            d, verdict, hit, glat, glng = None, "検索不可", "", "", ""
        else:
            glat, glng, hit = g
            d = dist_m((s["lat"], s["lng"]), (glat, glng))
            verdict = "OK" if d <= ok else ("要確認" if d <= FAR else "要修正")
        rows.append([verdict, "" if d is None else round(d), s["id"], s["name"], addr, hit,
                     s["lat"], s["lng"], glat, glng])
        print(f"\r{i}/{len(spots)}", end="", file=sys.stderr, flush=True)
        time.sleep(0.2)
    print(file=sys.stderr)

    rows.sort(key=lambda r: (r[1] == "", -(r[1] or 0)))
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["判定", "距離(m)", "id", "スポット名", "住所", "一致した住所",
                    "登録緯度", "登録経度", "住所の緯度", "住所の経度"])
        w.writerows(rows)

    counts = {}
    for r in rows:
        counts[r[0]] = counts.get(r[0], 0) + 1
    print(f"しきい値 {ok:g}m / 全{len(rows)}件")
    for k in ["OK", "要確認", "要修正", "検索不可"]:
        print(f"  {k}: {counts.get(k, 0)}件")
    print(f"結果: {OUT.relative_to(INDEX.parent)}")


if __name__ == "__main__":
    main()
