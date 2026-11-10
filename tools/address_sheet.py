#!/usr/bin/env python3
"""ぬまサーチ 住所編集ツール

  書き出し:  python3 tools/address_sheet.py export
             → tools/address_edit.xlsx を index.html の最新内容で作り直す
  反映:      python3 tools/address_sheet.py apply
             → address_edit.xlsx の黄色い列(エリア/住所/緯度/経度)の変更を index.html に反映
  確認だけ:  python3 tools/address_sheet.py apply --dry-run

住所だけ書き換えて緯度・経度をそのままにした行は、国土地理院の住所検索(無料)で
座標を取り直す。検索が失敗したら座標はそのままにして、その旨を表示する。
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
XLSX = ROOT / "tools" / "address_edit.xlsx"
AREAS = ["六日町", "塩沢", "大和"]
HEADERS = ["id(変更禁止)", "スポット名", "ジャンル", "エリア", "住所", "緯度", "経度", "Googleマップで確認", "メモ(自由)"]

# 1スポット分: { id:"..." ... area:"..." ... address:"...", lat:数値, lng:数値
SPOT_RE = re.compile(
    r'\{ id:"(?P<id>[^"]+)", name:"(?P<name>[^"]*)", genre:"(?P<genre>[^"]*)", '
    r'area:"(?P<area>[^"]*)"(?P<mid>[^{}]*?)address:"(?P<address>(?:[^"\\]|\\.)*)", '
    r'lat:(?P<lat>-?[\d.]+), lng:(?P<lng>-?[\d.]+)'
)


def read_spots(html):
    spots = [m.groupdict() | {"span": m.span()} for m in SPOT_RE.finditer(html)]
    for s in spots:
        s["lat"], s["lng"] = float(s["lat"]), float(s["lng"])
    return spots


def js_str(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def export():
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.worksheet.datavalidation import DataValidation

    spots = read_spots(INDEX.read_text(encoding="utf-8"))
    wb = Workbook()
    ws = wb.active
    ws.title = "住所"
    base = Font(name="Arial", size=10)
    head_fill = PatternFill("solid", fgColor="1F3A4D")
    lock_fill = PatternFill("solid", fgColor="EDEFF1")
    edit_fill = PatternFill("solid", fgColor="FFF4C2")
    thin = Side(style="thin", color="D0D5D9")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    ws.append(HEADERS)
    for c in ws[1]:
        c.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        c.fill = head_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border
    for s in spots:
        q = urllib.parse.quote(s["name"] + " " + s["address"].replace('\\"', '"'))
        ws.append([s["id"], s["name"], s["genre"], s["area"], s["address"].replace('\\"', '"'),
                   s["lat"], s["lng"], "開く", ""])
        r = ws.max_row
        ws.cell(r, 8).hyperlink = f"https://www.google.com/maps/search/?api=1&query={q}"
        for col in range(1, 10):
            c = ws.cell(r, col)
            c.font = Font(name="Arial", size=10, color="0563C1", underline="single") if col == 8 else base
            c.border = border
            c.fill = edit_fill if col in (4, 5, 6, 7) else (lock_fill if col <= 3 else PatternFill())
        ws.cell(r, 6).number_format = "0.000000"
        ws.cell(r, 7).number_format = "0.000000"

    dv = DataValidation(type="list", formula1='"' + ",".join(AREAS) + '"', allow_blank=False,
                        error="六日町 / 塩沢 / 大和 から選んでください", errorTitle="エリア")
    ws.add_data_validation(dv)
    dv.add(f"D2:D{ws.max_row}")
    for i, w in enumerate([18, 30, 8, 9, 34, 12, 12, 16, 30], 1):
        ws.column_dimensions[chr(64 + i)].width = w
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:I{ws.max_row}"

    g = wb.create_sheet("使い方", 0)
    lines = [
        ("ぬまサーチ 住所編集シート", True),
        ("", False),
        ("1. 「住所」シートの黄色い列(エリア・住所・緯度・経度)だけを書き換えて保存する。", False),
        ("   灰色の列(id・スポット名・ジャンル)は変えない。行の追加・削除もしない(スポットの追加は index.html で)。", False),
        ("2. ターミナルで、numa-search フォルダに移動して次を実行する:", False),
        ("      python3 tools/address_sheet.py apply", False),
        ("   変更された行だけが index.html に反映され、変更内容が一覧表示される。", False),
        ("   先に確認だけしたいときは: python3 tools/address_sheet.py apply --dry-run", False),
        ("3. ブラウザで index.html を開いて確認 → git で commit / push。", False),
        ("", False),
        ("■ ピン位置(緯度・経度)について", True),
        ("・住所だけ変えて緯度・経度をそのままにすると、国土地理院の住所検索(無料)で座標を自動で取り直す。", False),
        ("  検索に失敗したときは座標はそのままで、ターミナルに「座標は未更新」と出る。", False),
        ("・自分で座標を入れたいときは、Googleマップで場所を右クリック → 一番上の数字(例: 37.065430, 138.876210)", False),
        ("  の前半を緯度、後半を経度に入れる。緯度 36〜38・経度 138〜140 の範囲外はエラーになる。", False),
        ("", False),
        ("■ 入力例", True),
        ("  住所: 南魚沼市小栗山2027-3   緯度: 37.068288   経度: 138.850172", False),
        ("", False),
        ("■ index.html を別の方法で直したあとは", True),
        ("  python3 tools/address_sheet.py export でこのファイルを作り直してから編集する(古いシートで上書きしないため)。", False),
    ]
    for i, (t, bold) in enumerate(lines, 1):
        c = g.cell(i, 1, t)
        c.font = Font(name="Arial", size=12 if i == 1 else 10, bold=bold)
    g.column_dimensions["A"].width = 110
    XLSX.parent.mkdir(exist_ok=True)
    wb.save(XLSX)
    print(f"書き出しました: {XLSX}  ({len(spots)}件)")


def geocode(address):
    url = "https://msearch.gsi.go.jp/address-search/AddressSearch?q=" + urllib.parse.quote(address)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "numa-search-tools"}), timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception:
        return None
    for f in data:
        lng, lat = f["geometry"]["coordinates"]
        if "南魚沼市" in f["properties"].get("title", "") and 36 < lat < 38 and 138 < lng < 140:
            return round(lat, 6), round(lng, 6)
    return None


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def apply(dry_run):
    from openpyxl import load_workbook

    if not XLSX.exists():
        sys.exit(f"{XLSX} がありません。先に export を実行してください。")
    html = INDEX.read_text(encoding="utf-8")
    spots = {s["id"]: s for s in read_spots(html)}
    ws = load_workbook(XLSX, data_only=True)["住所"]
    if [c.value for c in ws[1]][:7] != HEADERS[:7]:
        sys.exit("「住所」シートの見出しが変わっています。export で作り直してください。")

    errors, changes = [], []
    for row_no, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        sid, name, _, area, address, lat, lng = (list(r) + [None] * 7)[:7]
        if not sid:
            continue
        s = spots.get(sid)
        if not s:
            errors.append(f"{sid}: index.html に無い id です")
            continue
        area = (area or "").strip()
        address = (address or "").strip()
        lat, lng = num(lat), num(lng)
        if area not in AREAS:
            errors.append(f"{name}: エリア「{area}」は 六日町/塩沢/大和 のどれかにしてください")
            continue
        if not address:
            errors.append(f"{name}: 住所が空です")
            continue
        if lat is None or lng is None or not (36 < lat < 38 and 138 < lng < 140):
            errors.append(f"{name}: 緯度・経度が範囲外か空です({lat}, {lng})")
            continue
        old_addr = s["address"].replace('\\"', '"')
        coord_changed = abs(lat - s["lat"]) > 1e-6 or abs(lng - s["lng"]) > 1e-6
        if area == s["area"] and address == old_addr and not coord_changed:
            continue
        note = ""
        if address != old_addr and not coord_changed:
            g = geocode(address)
            if g:
                lat, lng = g
                note = "座標は住所から自動取得"
            else:
                note = "座標は未更新(住所検索に失敗。必要なら緯度・経度を手入力)"
        changes.append(dict(s=s, area=area, address=address, lat=lat, lng=lng, note=note, old_addr=old_addr,
                            row=row_no, geocoded=note.startswith("座標は住所から")))

    if errors:
        print("エラーがあるため反映しませんでした:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    if not changes:
        print("変更はありません。")
        return

    # 後ろから置き換えて位置ずれを防ぐ
    for c in sorted(changes, key=lambda c: -c["s"]["span"][0]):
        s = c["s"]
        a, b = s["span"]
        seg = html[a:b]
        m = SPOT_RE.match(seg)
        new = (f'{{ id:"{s["id"]}", name:"{m["name"]}", genre:"{m["genre"]}", area:"{c["area"]}"'
               f'{m["mid"]}address:"{js_str(c["address"])}", lat:{c["lat"]:.6f}, lng:{c["lng"]:.6f}')
        html = html[:a] + new + html[b:]

    print(f"{'(確認のみ) ' if dry_run else ''}{len(changes)}件の変更:")
    for c in changes:
        s = c["s"]
        print(f"  - {s['name']}")
        if c["area"] != s["area"]:
            print(f"      エリア: {s['area']} → {c['area']}")
        if c["address"] != c["old_addr"]:
            print(f"      住所:   {c['old_addr']} → {c['address']}")
        if abs(c["lat"] - s["lat"]) > 1e-6 or abs(c["lng"] - s["lng"]) > 1e-6:
            print(f"      座標:   {s['lat']}, {s['lng']} → {c['lat']:.6f}, {c['lng']:.6f}")
        if c["note"]:
            print(f"      ※ {c['note']}")
    if dry_run:
        return
    INDEX.write_text(html, encoding="utf-8")
    # 自動取得した座標をシートにも書き戻す(次回 apply で古い座標に戻さないため)
    auto = [c for c in changes if c["geocoded"]]
    if auto:
        wb = load_workbook(XLSX)
        sh = wb["住所"]
        for c in auto:
            sh.cell(c["row"], 6).value = c["lat"]
            sh.cell(c["row"], 7).value = c["lng"]
        try:
            wb.save(XLSX)
        except PermissionError:
            print("※ Excel でファイルが開いたままのため、自動取得した座標をシートに書き戻せませんでした。"
                  "Excel を閉じて export し直してください。")
    print("index.html を更新しました。ブラウザで確認してから commit / push してください。")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "export":
        export()
    elif cmd == "apply":
        apply("--dry-run" in sys.argv)
    else:
        print(__doc__)
