# `frontend/web/src/styles/_catalog.scss`

## 目的・役割

学年別カタログのヘッダー、カテゴリ見出し、戻る導線を定義する。

## 動作の概要

`.catalog-header` と `.category-section` が、それぞれの子見出しを内包する(`frontend/web/src/styles/_catalog.scss:26-51`)。`.page-header-row` と `.back-button` はアイコン付きのページ移動導線を提供する(`frontend/web/src/styles/_catalog.scss:69-119`)。

issue #130 で、学年別カタログの配色を動的化した。`$color-grade-1`〜`6`(`_base.scss` 定義)を CSS カスタムプロパティ `--color-primary`/`--color-primary-hover` にマップする `.grade-1`〜`.grade-6` クラスを `@each` ループで生成する(`frontend/web/src/styles/_catalog.scss:1-17`)。`.catalog-header-title` の背景色、`.category-section h2` の左ボーダー、`.back-button:hover` の文字色は `var(--color-primary, #{$color-primary})`(hover は `--color-primary-hover`)という形で参照し、`.grade-N` クラスが祖先に無い場合は既存の固定 `$color-primary`(-hover) にフォールバックする。`--color-primary-hover` は学年別の専用トーンを持たず、`--color-primary` と同じ `$color-grade-N` の値をそのまま使う(hover 専用の別配色を追加しない設計判断、下記参照)。`.grade-N` クラス自体は `catalog.js`([[../../catalog.js]] 参照)が `#catalog` コンテナに付与する。

## 重要な設計判断とその理由

### `--color-primary-hover` を計算せず `--color-primary` と同じ値にした理由

初期実装では `sass:color` の `color.scale($color, $lightness: -12%)` でグレードごとに暗くしたホバー色を計算していたが、計算結果が `rgb(92.4%, 59.2%, 4.2%)` のような percentage 表記になり、どの `$color-grade-N` の hex 値とも一致しなかった(ユーザー指摘)。ユーザーに確認した結果、「両変数とも同じ `$color-grade-N` をそのまま使う」方針が選ばれたため、`sass:color` への依存自体を削除し、`--color-primary-hover: #{$color}` と `--color-primary` に同じ値を代入する形に単純化した。

## 統合ポイント

- 呼び出し元: `main.scss`。
- 利用元: `catalog.js`(`.grade-N` クラス付与元)、`preset.js`、`presetDetail.js`(`.back-button`/`.page-header-row` を描画するが `.grade-N` クラスは付与されないため、常に固定フォールバック色のまま)。
- 呼び出し先: `_base.scss` のデザイントークン(`$color-primary`/`$color-primary-hover`/`$color-grade-1`〜`6`)。

## 変更履歴(git log より自動生成)

- ff1576a refactor(#128): reorganize web Sass by UI hierarchy
