#!/usr/bin/env python3
"""
SPOTS配列のデータ整合性チェック + 機械的に直せる問題(id重複)のみ自動修正する。
使い方: python3 scripts/validate_spots.py [--fix]
  --fix を付けると id重複を自動修正して index.html を書き換える(他の問題は修正しない)。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "index.html"

ALLOWED_GENRES = {"観光", "自然", "飲食", "カフェ", "温泉", "宿泊", "買物", "心霊"}
LAT_RANGE = (36.0, 38.0)
LNG_RANGE = (138.0, 140.0)
REQUIRED_FIELDS = ["id", "name", "genre", "area", "address", "lat", "lng"]
DIGIT_RE = re.compile(r"[0-90-9]")


def find_matching(text, open_idx, open_ch, close_ch):
    depth = 0
    in_str = None
    i = open_idx
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in ('"', "'"):
            in_str = ch
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError(f"matching {close_ch} not found")


def split_objects(arr_text):
    """arr_text内のトップレベル { ... } オブジェクトの (start, end) を文字列境界を考慮して返す"""
    spans = []
    depth = 0
    start = -1
    in_str = None
    i = 0
    while i < len(arr_text):
        ch = arr_text[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in ('"', "'"):
            in_str = ch
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                spans.append((start, i + 1))
        i += 1
    return spans


def extract_field_str(raw, key):
    m = re.search(rf'{key}\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    if m:
        return m.group(1), m.start(1), m.end(1)
    m = re.search(rf"{key}\s*:\s*'((?:[^'\\]|\\.)*)'", raw)
    if m:
        return m.group(1), m.start(1), m.end(1)
    return None, None, None


def extract_field_num(raw, key):
    m = re.search(rf"{key}\s*:\s*(-?\d+(?:\.\d+)?)", raw)
    if m:
        return float(m.group(1)), m.start(1), m.end(1)
    return None, None, None


def load_spots_array():
    html = INDEX_HTML.read_text(encoding="utf-8")
    start_marker = "const SPOTS = ["
    start_idx = html.index(start_marker)
    arr_open = start_idx + len(start_marker) - 1
    arr_close = find_matching(html, arr_open, "[", "]")
    arr_text = html[arr_open:arr_close + 1]
    return html, arr_open, arr_close, arr_text


def main():
    fix = "--fix" in sys.argv
    html, arr_open, arr_close, arr_text = load_spots_array()
    spans = split_objects(arr_text)

    objects = []
    for (s, e) in spans:
        raw = arr_text[s:e]
        id_val, id_s, id_e = extract_field_str(raw, "id")
        name_val, _, _ = extract_field_str(raw, "name")
        genre_val, _, _ = extract_field_str(raw, "genre")
        area_val, _, _ = extract_field_str(raw, "area")
        address_val, _, _ = extract_field_str(raw, "address")
        lat_val, _, _ = extract_field_num(raw, "lat")
        lng_val, _, _ = extract_field_num(raw, "lng")
        objects.append({
            "span": (s, e),
            "raw": raw,
            "id": id_val, "id_offset": (s + id_s, s + id_e) if id_s is not None else None,
            "name": name_val, "genre": genre_val, "area": area_val,
            "address": address_val, "lat": lat_val, "lng": lng_val,
        })

    # 重複id検出
    id_positions = {}
    for idx, o in enumerate(objects):
        id_positions.setdefault(o["id"], []).append(idx)
    duplicates = {k: v for k, v in id_positions.items() if k and len(v) > 1}

    # 範囲外 lat/lng
    out_of_range = [o for o in objects
                     if o["lat"] is None or o["lng"] is None
                     or not (LAT_RANGE[0] <= o["lat"] <= LAT_RANGE[1])
                     or not (LNG_RANGE[0] <= o["lng"] <= LNG_RANGE[1])]

    # 不正genre
    invalid_genre = [o for o in objects if o["genre"] not in ALLOWED_GENRES]

    # 必須フィールド欠落
    missing_fields = []
    for o in objects:
        missing = [f for f in REQUIRED_FIELDS if o.get(f) in (None, "")]
        if missing:
            missing_fields.append((o, missing))

    # 住所未補完(エリア表記のまま=数字を含まない)
    placeholder_address = [o for o in objects if o["address"] and not DIGIT_RE.search(o["address"])]

    print(f"総スポット数: {len(objects)}")
    print()

    fixed_count = 0
    if duplicates:
        print(f"[重複id] {len(duplicates)}件のidが重複しています:")
        replacements = []  # (abs_start, abs_end, new_text)
        for base_id, idxs in duplicates.items():
            print(f"  - {base_id}: {len(idxs)}件")
            for n, idx in enumerate(idxs[1:], start=2):
                o = objects[idx]
                if o["id_offset"] is None:
                    continue
                new_id = f"{base_id}-{n}"
                abs_s, abs_e = o["id_offset"]
                replacements.append((abs_s, abs_e, new_id))
                print(f"      -> {n}番目の出現を \"{new_id}\" にリネーム" + (" (--fix実行)" if fix else " (--fixで実行されます)"))
        if fix and replacements:
            replacements.sort(key=lambda r: r[0], reverse=True)
            new_arr_text = arr_text
            for abs_s, abs_e, new_text in replacements:
                new_arr_text = new_arr_text[:abs_s] + new_text + new_arr_text[abs_e:]
            new_html = html[:arr_open] + new_arr_text + html[arr_close + 1:]
            INDEX_HTML.write_text(new_html, encoding="utf-8")
            fixed_count = len(replacements)
            print(f"  -> index.html を更新しました({fixed_count}件リネーム)")
        print()
    else:
        print("[重複id] 問題なし")
        print()

    if out_of_range:
        print(f"[座標範囲外] {len(out_of_range)}件(lat 36-38 / lng 138-140 の範囲外):")
        for o in out_of_range:
            print(f"  - {o['id']} ({o['name']}): lat={o['lat']}, lng={o['lng']}")
        print()
    else:
        print("[座標範囲外] 問題なし")
        print()

    if invalid_genre:
        print(f"[不正genre] {len(invalid_genre)}件:")
        for o in invalid_genre:
            print(f"  - {o['id']} ({o['name']}): genre=\"{o['genre']}\"")
        print()
    else:
        print("[不正genre] 問題なし")
        print()

    if missing_fields:
        print(f"[必須フィールド欠落] {len(missing_fields)}件:")
        for o, missing in missing_fields:
            print(f"  - {o['id'] or '(id不明)'} ({o['name'] or '(name不明)'}): 欠落={missing}")
        print()
    else:
        print("[必須フィールド欠落] 問題なし")
        print()

    print(f"[住所未補完(エリア表記のまま)] {len(placeholder_address)}件:")
    for o in placeholder_address:
        print(f"  - {o['id']} ({o['name']}): {o['address']}")
    print()

    print("=== サマリー ===")
    print(f"自動修正: id重複 {fixed_count}件")
    print(f"要確認(レポートのみ): 座標範囲外 {len(out_of_range)}件 / 不正genre {len(invalid_genre)}件 / "
          f"必須フィールド欠落 {len(missing_fields)}件 / 住所未補完 {len(placeholder_address)}件")

    return 0


if __name__ == "__main__":
    sys.exit(main())
