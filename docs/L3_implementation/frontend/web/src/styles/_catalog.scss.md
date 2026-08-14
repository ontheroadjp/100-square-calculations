# `frontend/web/src/styles/_catalog.scss`

## 目的・役割

学年別カタログのヘッダー、カテゴリ見出し、戻る導線を定義する。

## 動作の概要

`.catalog-header` と `.category-section` が、それぞれの子見出しを内包する(`frontend/web/src/styles/_catalog.scss:3-27`)。`.page-header-row` と `.back-button` はアイコン付きのページ移動導線を提供する(`frontend/web/src/styles/_catalog.scss:29-76`)。

## 統合ポイント

- 呼び出し元: `main.scss`。
- 利用元: `catalog.js`、`preset.js`、`presetDetail.js`。
- 呼び出し先: `_base.scss` のデザイントークン。

## 変更履歴(git log より自動生成)

- ff1576a refactor(#128): reorganize web Sass by UI hierarchy
