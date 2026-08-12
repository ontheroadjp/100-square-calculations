# `frontend/spa/src/GradeDrills.jsx`

## 目的・役割

ドリル探索、検索、プリセット詳細表示を担うメイン画面。トップでは数の種類・出題形式/目的・学年の三つの入口を表示し、数の種類を選んだ後は学習内容に沿ってカードを区分する。

## 動作の概要

- `GradeDrills` は選択した数の種類、問題形式、学年、レベル、検索語を state として持ち、`drillCatalog.js` の分類済みエントリを絞り込む（`GradeDrills.jsx:272-326`）。
- 数の種類の入口は整数・小数・分数・混合。整数は足し算・引き算、掛け算・割り算、四則混合、小数は前二者と該当時の四則混合、分数はたし算・ひき算、かけ算・わり算、分数の大小の順で表示する（`GradeDrills.jsx:26-31,233-268`）。
- 整数ページだけは、該当カードがある場合に「（ ）を使う」「虫食い算」のチェックボックスを表示する。複数選択は AND 条件であり、将来かっこ付き虫食い算を追加しても同じ導線で扱える（`GradeDrills.jsx:31,236-255,299-303`）。
- トップの出題形式/目的入口は、現レンダラーで利用可能な筆算・かっこ・虫食い算・九九/暗算/数の練習・中学受験対策を表示する（`GradeDrills.jsx:325,379-384`）。
- `PresetDetail` は従来どおりPDF生成、用紙・ページ・問題数の設定とダウンロードを担当する（`GradeDrills.jsx:35-193`）。

## 重要な設計判断

数の種類と演算・問題形式を別の軸にした。トップで「小数・分数」と「足し算・引き算」を同列にせず、整数の形式フィルタは独立カードにせず演算分類と組み合わせるためである。

## 統合ポイント

- 呼び出し元: `App.jsx`
- 呼び出し先: `drillCatalog.js`、`drillPresets.js`、`CustomGenerator.jsx`、`verticalLayout.js`、`GET /renderer-info`、`POST /generate-pdf`

## 注意事項・既知の制限

- `latex` レンダラー専用カードは `buildDrillCatalog(activeRenderer)` が除外するため、利用可能な入口とフィルタはレンダラーによって変わる。
- 現在は小数の四則混合、およびかっこ付き虫食い算のプリセットがないため、対応する空の中見出しは表示しない。

## 変更履歴（git log より自動生成）

- d956e48 feat(#86): rebuild drill discovery by number type
- 7290008 feat(#73): add entrance-exam-prep drill section for grades 4-6
- 7c89a52 feat(#65): add curriculum-aligned fraction worksheets
- fd449c7 fix(#57): apply vertical layout in web UI
- 9ead364 refactor(#46): remove --vertical from nuts_calc.py; gate written-calculation UI on active renderer
