# `frontend/web/src/styles/_drillList.scss`

## 目的・役割

ドリルの縦積みリスト、カード、難易度バッジ、空状態を一つのUI単位として定義する。

## 動作の概要

`.drill-list` の中に `.drill-list-card*` の見た目をネストする(`frontend/web/src/styles/_drillList.scss:3-53`)。カードは連続したリストとして表示し、最初のカードだけ上側、最後のカードだけ下側に角丸を付ける。最後のカードには下罫線も追加してリストを閉じる(`frontend/web/src/styles/_drillList.scss:22-31`)。`.drill-badge` は基礎(緑)・標準(橙)・発展(赤)の難易度バリエーションを定義し、発展には `.badge-advanced` を使う(`frontend/web/src/styles/_drillList.scss:60-91`)。空状態も同ファイルで定義する。

issue #130: `.drill-list-card:hover`(通常時・`:last-child` の2箇所)は `border: 2px solid`(issue #132 で 1px から変更)、ボーダー色は `border-color: var(--color-primary, #{$color-primary})` で参照する(`frontend/web/src/styles/_drillList.scss:18-21,32-35`)。`catalog.js` が `#catalog` に付与する `.grade-N` クラス(`_catalog.scss` 定義、[[./_catalog.scss]] 参照)の祖先がある場合はカードのhover枠線が学年別の `$color-grade-N` になり、無い場合(`pcMakeFlow.js` 由来のカード等)は既存の固定 `$color-primary` にフォールバックする。

## 統合ポイント

- 呼び出し元: `main.scss`。
- 利用元: `catalog.js`(hover枠線が `.grade-N` スコープ下で学年別色になる)、`pcMakeFlow.js`(`.grade-N` を付与しないため常に固定色)。
- 呼び出し先: `_base.scss` の色・余白・角丸トークン。

## 注意事項・既知の制限

PC作成フローの選択状態は `_pcMakeFlow.scss` の `.pc-drill-list-card` が追加で定義する。

## 変更履歴(git log より自動生成)

- e8ce3ec feat(#146): add advanced difficulty badge
- 2d9ee47 #132 frontend/web: dynamic grade accent, KaTeX fraction examples, generalized setting hints, and move problem count into common settings on preset detail page (#136)
- d43d1bc #130 frontend/web: make catalog page accent color switch dynamically per grade (#131)
- 3625e47 #128 Reorganize frontend web Sass by UI hierarchy (#129)
