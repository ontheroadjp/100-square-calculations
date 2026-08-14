# `frontend/web/src/styles/_catalog.scss`

## 目的・役割

学年別カタログのヘッダー、カテゴリ見出し、戻る導線を定義する。

## 動作の概要

`.catalog-header` と `.category-section` が、それぞれの子見出しを内包する(`frontend/web/src/styles/_catalog.scss:10-35`)。`.page-header-row` と `.back-button` はアイコン付きのページ移動導線を提供する(`frontend/web/src/styles/_catalog.scss:53-103`)。

issue #130 で、学年別カタログの配色を動的化した。`.catalog-header-title` の背景色、`.category-section h2` の左ボーダー、`.back-button:hover` の文字色は `var(--color-primary, #{$color-primary})`(hover は `--color-primary-hover`)という形で参照し、`.grade-N` クラスが祖先に無い場合は既存の固定 `$color-primary`(-hover) にフォールバックする。`--color-primary-hover` は学年別の専用トーンを持たず、`--color-primary` と同じ `$color-grade-N` の値をそのまま使う(hover 専用の別配色を追加しない設計判断、下記参照)。

`$color-grade-1`〜`6` を `--color-primary`/`--color-primary-hover` にマップする `.grade-1`〜`.grade-6` の `@each` ループ本体は、issue #132 で `_base.scss` へ移設した(下記参照)。`main.scss` が全ページ分の Sass を1本の CSS にバンドルするため、`.grade-N` ルールをどのページ固有パーシャルに置いても全ページへ適用されるが、複数パーシャル(当初は `_catalog.scss` のみだったが issue #132 で `presetDetail.js` の設定画面にも `.grade-N` が必要になった)が同じマップを個別に持つ重複を避けるため、一箇所(`_base.scss`)に集約した。`.grade-N` クラス自体は `catalog.js`([[../../catalog.js]] 参照)が `#catalog` コンテナに、`presetDetail.js`([[../../presetDetail.js]] 参照)が `preset.html` のマウント先コンテナに、それぞれ付与する。

## 重要な設計判断とその理由

### `--color-primary-hover` を計算せず `--color-primary` と同じ値にした理由

初期実装では `sass:color` の `color.scale($color, $lightness: -12%)` でグレードごとに暗くしたホバー色を計算していたが、計算結果が `rgb(92.4%, 59.2%, 4.2%)` のような percentage 表記になり、どの `$color-grade-N` の hex 値とも一致しなかった(ユーザー指摘)。ユーザーに確認した結果、「両変数とも同じ `$color-grade-N` をそのまま使う」方針が選ばれたため、`sass:color` への依存自体を削除し、`--color-primary-hover: #{$color}` と `--color-primary` に同じ値を代入する形に単純化した。

## 統合ポイント

- 呼び出し元: `main.scss`。
- 利用元: `catalog.js`(`.grade-N` クラス付与元)、`preset.js`、`presetDetail.js`(`.back-button`/`.page-header-row` に加え、issue #132 以降は `.grade-N` クラスも付与するため学年色に追従する)。
- 呼び出し先: `_base.scss` のデザイントークン(`$color-primary`/`$color-primary-hover`/`$color-grade-1`〜`6`、および `.grade-N` カスタムプロパティルール本体、issue #132)。

## 変更履歴(git log より自動生成)

- bf48e4c feat(#130): make catalog page accent color switch dynamically per grade
- 3625e47 #128 Reorganize frontend web Sass by UI hierarchy (#129)
