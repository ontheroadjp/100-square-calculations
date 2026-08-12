# `frontend/spa/src/drillCatalog.js`

## 目的・役割

学年別プリセットを、探索UI用の統一カタログエントリへ変換する純粋モジュール。数の種類・演算分類・問題形式を別属性として提供する。

## 動作の概要

- `buildDrillCatalog(renderer)` は `normal`、`written`、`examPrep` のプリセットを統合し、同一の2項計算は通常式と筆算を一つのカードに組み合わせる（`drillCatalog.js:77-143`）。
- 各エントリは `numberType`（整数・小数・分数・混合）、`operationGroup`、`forms`、学年、レベル、表示キー、生成形式を持つ（`drillCatalog.js:34-70,95-105`）。
- `filterDrillCatalog` は数の種類、演算分類、形式、学年、レベル、検索語をすべて満たすカードだけを返す。`forms` は配列の全項一致なので、かっこと虫食い算を組み合わせられる（`drillCatalog.js:146-156`）。

## 重要な設計判断

数の種類を排他的な旧 `subject` に置き換え、演算分類と形式を独立させた。これにより同じドリルを「整数」からも「筆算」からも到達可能にする。

## 統合ポイント

- 入力: `drillPresets.js`
- 呼び出し元: `GradeDrills.jsx`、`drillCatalog.test.js`

## 注意事項・既知の制限

- `forms` はカードの提供形式または問題特性を示す探索用メタデータであり、PDF生成パラメータを変更しない。

## 変更履歴（git log より自動生成）

- d956e48 feat(#86): rebuild drill discovery by number type
