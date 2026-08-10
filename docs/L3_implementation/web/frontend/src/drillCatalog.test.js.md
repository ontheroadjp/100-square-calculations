# `web/frontend/src/drillCatalog.test.js`

## 目的・役割

探索カタログの通常式・筆算統合、レンダラー別の可用性、分類と複合形式フィルタを検証する Node.js 組み込みテスト。

## 動作の概要

- LaTeX時の2項計算形式統合と、ReportLab時の筆算非表示を確認する（`drillCatalog.test.js:6-39`）。
- 数の種類、演算分類、学年、レベル、検索語、形式のフィルタを確認する（`drillCatalog.test.js:41-59`）。
- 将来のかっこ付き虫食い算に備え、複数形式のAND絞り込みを固定データで検証する（`drillCatalog.test.js:61-77`）。

## 統合ポイント

- 対象: `drillCatalog.js`
- 実行: `node --test web/frontend/src/drillCatalog.test.js`
