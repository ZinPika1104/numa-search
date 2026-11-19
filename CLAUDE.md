# ぬまサーチ — プロジェクト引き継ぎ(Claude Code用)

新潟県南魚沼市の観光スポット検索サイト。対象は関わりのある学生で、無料で使える。**単一HTMLファイル**(index.html)で完結し、GitHub Pagesで公開中。

- リポジトリ: https://github.com/ZinPika1104/numa-search
- 公開URL: https://zinpika1104.github.io/numa-search/ (main へのpushから1〜2分で自動更新)
- ライセンス: MIT
- コンセプト: 普通の地図アプリは選択肢が多すぎて行き先を選びにくい → ニッチ情報と「みんながどこへ行っているか」の可視化で選びやすくする。一番の狙いは、初めて来た人と地元を知る人が一緒に行き先を話す**コミュニケーションツール**としての利用(2026-11-16 設計相談より)

## ファイル構成

| ファイル | 役割 |
|---|---|
| index.html | アプリ本体(HTML+CSS+JSすべて入り)。**基本これだけ編集すればよい** |
| manifest.json / sw.js / icon-192.png / icon-512.png | PWA用(ホーム画面アプリ化)。sw.jsはネット優先キャッシュ |
| ogp.png | SNSシェア時のサムネイル画像(1200x630) |
| README.md | リポジトリ説明 |
| spot_list.md | ジャンル別スポット一覧(Markdown) |
| 南魚沼たびナビ_スポット一覧.xlsx | スポット一覧のExcel版(SPOTSから生成した写し) |
| tools/address_edit.xlsx + tools/address_sheet.py | 住所・エリア・座標の編集シートと、index.html との相互変換 |
| tools/check_coords.py → tools/coord_check.csv | 住所を地理院の住所検索で座標化し、登録座標との距離をチェック |
| scripts/validate_spots.py | SPOTSの整合性チェック(id重複・ジャンル・座標範囲・必須項目・住所未補完)。`--fix` でid重複のみ自動修正 |

※サイト用ファイルはすべてリポジトリ直下。OGP/PWAはGitHub PagesのURL前提の設定。

## index.html の構造

すべて `<script>` 内のデータ配列・定数を編集して機能追加・修正する設計。

### ページ構成(セクション順)
ヒーロー → いま推したいスポット(Pick up) → みんなのランキング → スポットをさがす → ぬまマップ → おすすめモデルコース → 南魚沼の四季 → ぬまクイズ → おすすめお土産 → アクセス

### データ(編集ポイント)
- `const ALL_SPOTS = [...]` — スポット全**367件**(飲食162/カフェ41/買物40/観光37/宿泊33/自然32/温泉18/心霊4)。コメント「スポットデータ(ここを編集して追加・修正できます)」が目印
- `const HIDDEN_GENRES = ["宿泊","心霊"]` — サイトに出さないジャンル(2026-11-16〜)。`SPOTS` は ALL_SPOTS からこれを除いた表示用(現在330件)。データは残っているので、配列から消せば再表示できる(色・アイコン・心霊の注意書きも用意済み)
  - フィールド: `id`(英数スラッグ・重複禁止), `name`, `genre`, `area`(六日町/塩沢/大和), `desc`, `niche`(ニッチ情報), `address`, `lat`/`lng`(周辺提案・所要時間計算・地図ピンに使用), `hours`, `price`, `parking`, `season`, `tags`(配列)
  - genre は 観光/自然/飲食/カフェ/温泉/宿泊/買物/心霊 の8種。`GENRES` は HIDDEN_GENRES を除いた表示用
- `const COURSES = [...]` — モデルコース6本(王道1日/塩沢さんぽ/絶景ドライブ/グルメ/浦佐・大和/冬)。spots に SPOTS の id を列挙
- `const SEASONS = [...]` — 四季紹介(photo:"" にURLを入れると写真表示)
- `const QUIZ = [...]` / `const QUIZ_HARD = [...]` — ご当地クイズ 通常10問+難問10問(q/c[4択]/a[正解index]/exp)
- `const PHOTOS = {}` — スポット写真。`id: "撮影者名"` を足すと `photos/<id>.jpg` を表示(現在は空・photosフォルダ未作成)
- `HERO_IDS` / `HERO_PHOTO` / `HERO_GRAD` — ヒーロー画像、`PICKUP_IDS` — 推しスポット
- `GENRE_COLORS` / `GENRE_ICONS` — 地図ピンのジャンル別色・アイコン、`KANA` — あいうえお行絞り込み用の読み
- `FB_PROJECT_ID` / `FB_API_KEY` — Firebase(Firestore)接続設定。空にするとコメント・リアクション・ランキングが非表示になる

### 主な機能(実装済み)
- **検索**: キーワード+ジャンルチップ、ブックマーク・行った済・あいうえお行での絞り込み、現在地から近い順ソート(カードに距離・車の目安時間)
- **スポット詳細モーダル**: Googleマップリンク・周辺5件・異ジャンル組み合わせ提案、⭐ブックマーク、✅行った!、👍いいね/💖行きたい、💬みんなのコメント
- **制覇率**: 「行った!」件数から算出(localStorage)。ブックマーク・行った済・マイルートは書き出し/復元可能(機種変更の引き継ぎ用)
- **みんなのランキング**(Firestore): 🏆制覇率(ニックネーム+アイコンで任意参加・脱退可)/💖行きたい/👍いいね、エリア別タブ
- **マイルート**: localStorage保存・近い順並べ替え・Googleマップのルート起動
- **ぬまマップ**: MapLibre GL JS(ベクター地図)、背景は OpenFreeMap(標準/淡色)と地理院の写真の切替、地名は日本語表記、ジャンル色分けピン(canvasで絵文字入り画像を生成)、ズーム13以上でクラスター解除・名前は重ならない所だけ表示、凡例でジャンル表示切替
- モデルコース / 四季 / クイズ(通常・難問) / お土産 / アクセス / OGP / PWA

### 外部依存
- MapLibre GL JS 4.7.1(cdnjs)。2026-11-19 に Leaflet から移行(動きの重さ・見た目の改善のため)
- 地図タイル: OpenFreeMap(標準=liberty / 淡色=positron、無料・APIキー不要)、写真のみ国土地理院 地理院タイル
- Google Maps API は無料枠(月1万回)はあるがカード登録とキー管理が必要なため不採用
- Firebase Firestore(REST APIで直接 fetch。SDKは未使用)

## 編集時の注意

1. **idの重複禁止**・座標は南魚沼市周辺(lat 36〜38, lng 138〜140)であること。変更後は `python3 scripts/validate_spots.py` で確認
2. 表示文字列は `esc()` を通してXSS対策(既存コードに倣う)。コメント・ニックネームなど他人が書いた文字列は特に注意
3. 動作確認: ブラウザで index.html を開くだけ。コンソールエラーが無いこと、スポット件数表示が正しいこと
4. 住所は 363件中332件が番地付き、31件が地区名のみ/山頂・エリア表記など(2026-11-16時点。validate_spots.py の「住所未補完」で一覧が出る)。Googleマップリンクは名前検索なので未補完でも動く
   - 住所・エリア・座標は `tools/address_edit.xlsx` で編集し `python3 tools/address_sheet.py apply` で index.html に反映できる(使い方はxlsxの「使い方」シート)。index.html を直接直したら `python3 tools/address_sheet.py export` でxlsxを作り直す
   - **ピン位置の微調整は「位置調整モード」**: サイトを `?edit#numamap` 付きで開く → ピンをタップ「📍位置を直す」→ 赤いピンをドラッグ(または地図をタップ)→「📋 一覧をコピー」。コピーした文字を `tools/coord_edits.txt` に貼って `python3 tools/apply_coord_edits.py` で index.html に反映(xlsxも自動で作り直す)。直した内容はその端末の localStorage(numaCoordEdits)に保存され、通常URLでは何も表示されない。写真地図に切り替えると建物の入口に合わせやすい
   - 座標の妥当性は `python3 tools/check_coords.py` で確認(結果は tools/coord_check.csv。山頂など住所が粗いスポットは距離が大きく出ても誤りとは限らない)
   - 地図の出典表示(国土地理院・OpenStreetMap)を消さないこと。座標の一部は OpenStreetMap 由来
5. 「五十沢温泉 ゆもとかん」の住所は情報源により宮394/宮17-4と揺れがある(現状は宮394)
6. 営業時間・料金は変動するため「(要確認)」表記を維持する

## デプロイ

作業はブランチで行い、main にマージして push すると GitHub Pages が自動更新される。

```
git add -A && git commit -m "変更内容" && git push
```
Excel版・spot_list.md を更新した場合も一緒にコミットする。

## 今後のアイデア(未着手)
- 残り31件の住所補完
- 四季セクション・スポットへの写真追加(SEASONSのphoto欄 / PHOTOS)
- 共有メモ運用(GitHub Issue 1本方式 or MEMO.md方式、未決定)
- 2026-11-16 設計相談で出た案(いずれも採用は未決定):
  - 参加者の悩みから逆算したタイプ別ルート(王道/ちょっとコアな食/地元の人が行く所)
  - 質問に答えると「あなただけのルート」ができる診断機能
  - 訪問後アンケート(人に勧めたいか・思っていたのと違ったか)で満足度を上げる
  - チャット機能
