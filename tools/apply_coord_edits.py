#!/usr/bin/env python3
"""ぬまサーチ 位置調整モードの結果を index.html に反映する

  使い方:
    1. サイトを ...?edit#numamap で開き、ピンを動かして「📋 一覧をコピー」
    2. コピーした文字を tools/coord_edits.txt に貼って保存
    3. python3 tools/apply_coord_edits.py            (確認だけ: --dry-run)
       ファイル名を指定する場合: python3 tools/apply_coord_edits.py 別のファイル.txt

  1行の形式: id<TAB>緯度<TAB>経度<TAB># スポット名(#以降は無視)
  反映後は address_edit.xlsx も作り直す(tools/address_sheet.py export)。
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
DEFAULT = ROOT / "tools" / "coord_edits.txt"


def parse(text):
    edits = []
    for n, line in enumerate(text.splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 3:
            sys.exit(f"{n}行目の形式が違います: {line}")
        sid, lat, lng = parts[0], float(parts[1]), float(parts[2])
        if not (36 <= lat <= 38 and 138 <= lng <= 140):
            sys.exit(f"{n}行目 {sid}: 座標が南魚沼市周辺の範囲外です ({lat}, {lng})")
        edits.append((sid, lat, lng))
    return edits


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    src = Path(args[0]) if args else DEFAULT
    if not src.exists():
        sys.exit(f"{src} がありません。コピーした一覧をこのファイルに貼ってください。")
    edits = parse(src.read_text(encoding="utf-8"))
    if not edits:
        sys.exit("反映する行がありません。")

    html = INDEX.read_text(encoding="utf-8")
    for sid, lat, lng in edits:
        # そのスポットの { id:"..." から次の { id:" までの範囲にある最初の lat/lng だけを書き換える
        pat = re.compile(r'(\{ id:"' + re.escape(sid) + r'",(?:(?!\{ id:").)*?lat:)(-?[\d.]+)(, lng:)(-?[\d.]+)', re.S)
        m = pat.search(html)
        if not m:
            print(f"× {sid}: index.html に見つかりません(スキップ)")
            continue
        print(f"○ {sid}: {m.group(2)}, {m.group(4)} → {lat:.6f}, {lng:.6f}")
        html = html[:m.start()] + f"{m.group(1)}{lat:.6f}{m.group(3)}{lng:.6f}" + html[m.end():]

    if dry:
        print("(--dry-run なので保存していません)")
        return
    INDEX.write_text(html, encoding="utf-8")
    print(f"index.html に {len(edits)} 件反映しました。xlsx を作り直します…")
    subprocess.run([sys.executable, str(ROOT / "tools" / "address_sheet.py"), "export"], check=False)


if __name__ == "__main__":
    main()
