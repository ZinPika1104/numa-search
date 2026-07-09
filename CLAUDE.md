# ぬまサーチ — プロジェクト引き継ぎ(Claude Code用)

新潟県南魚沼市の観光スポット検索アプリ。**単一HTMLファイル**(index.html)で完結し、GitHub Pagesで公開中。

- リポジトリ: https://github.com/ZinPika1104/numa-search
- 公開URL: https://zinpika1104.github.io/numa-search/ (pushから1〜2分で自動更新)
- ライセンス: MIT

## ファイル構成

| ファイル | 役割 |
|---|---|
| index.html | アプリ本体(HTML+CSS+JSすべて入り)。**基本これだけ編集すればよい** |
| manifest.json / sw.js / icon-192.png / icon-512.png | PWA用(ホーム画面アプリ化)。sw.jsはネット優先キャッシュ |
| ogp.png | SNSシェア時のサムネイル画像(1200x630) |
| README.md | リポジトリ説明 |
| 南魚沼たびナビ_スポット一覧.xlsx | スポット一覧のExcel版(SPOTSから生成した写し) |

※すべてリポジトリ直下に置く。OGP/PWAはGitHub PagesのURL前提の設定。

## index.html の構造

すべて `<script>` 内のデータ配列を編集して機能追加・修正する設計。

### データ(編集ポイント)
- `const SPOTS = [...]` — スポット367件。コメント「スポットデータ(ここを編集して追加・修正できます)」が目印
  - フィールド: `id`(英数スラッグ・重複禁止), `name`, `genre`, `area`(六日町/塩沢/大和), `desc`, `niche`(ニッチ情報), `address`, `lat`/`lng`(近似座標。周辺提案・所要時間計算に使用), `hours`, `price`, `parking`, `season`, `tags`(配列)
  - genre は 観光/自然/飲食/カフェ/温泉/宿泊/買物/心霊 の8種のみ
- `const COURSES = [...]` — おすすめモデルコース(spots に SPOTS の id を列挙)
- `const SEASONS = [...]` — 四季紹介(photo:"" にURLを入れると写真表示)
- `const QUIZ = [...]` — ご当地クイズ(q/c[4択]/a[正解index]/exp)
- `const GENRE_COLORS` — 地図ピンのジャンル別色

### 主な機能(実装済み)
検索+ジャンルチップ / 現在地から近い順ソート(Geolocation、カードに距離・車の目安時間表示) / スポット詳細モーダル(Googleマップリンク・周辺5件・異ジャンル組み合わせ提案) / マイルート(localStorage保存・近い順並べ替え・Googleマップルート起動) / モデルコース / 四季セクション / クイズ / 心霊スポット(詳細に注意書き表示) / ぬまマップ(Leaflet+markercluster、ジャンル色分けピン、ズーム13以上で名前ラベル+クラスター解除、凡例でジャンル表示切替) / OGP / PWA対応

### 外部依存(CDN)
Leaflet 1.9.4 と Leaflet.markercluster 1.5.3(cdnjs)。地図タイルは OpenStreetMap。APIキー不要。

## 編集時の注意

1. **idの重複禁止**・座標は南魚沼市周辺(lat 36〜38, lng 138〜140)であること
2. 表示文字列は `esc()` を通してXSS対策(既存コードに倣う)
3. 動作確認: ブラウザで index.html を開くだけ。コンソールエラーが無いこと、スポット件数表示が正しいこと
4. 住所は現在 367件中104件が番地付き、263件が「南魚沼市(六日町地域)」等のエリア表記。エリア表記を実住所に置き換える作業は歓迎(Googleマップリンクは名前検索なので未入力でも動く)
5. 「五十沢温泉 ゆもとかん」の住所は情報源により宮394/宮17-4と揺れがある(現状は宮394)
6. 営業時間・料金は変動するため「(要確認)」表記を維持する

## デプロイ

```
git add -A && git commit -m "変更内容" && git push
```
push すれば GitHub Pages が自動更新。Excel版を更新した場合も一緒にpushする。

## 今後のアイデア(未着手)
- 残り263件の住所補完
- 四季セクションへの写真追加(SEASONSのphoto欄)
- 共有メモ運用(GitHub Issue 1本方式 or MEMO.md方式、未決定)
- スポットの写真対応 / お気に入り機能
