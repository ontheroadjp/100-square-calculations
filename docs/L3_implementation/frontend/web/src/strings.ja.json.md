# `frontend/web/src/strings.ja.json`

## 目的・役割

`frontend/web` の日本語UI文言をキーと文字列の対応として保持する。`strings.js` の `t(key)` がこのJSONを読み、該当キーの文言を返す。

## 動作の概要

画面見出し、操作ラベル、ドリル名、設定値などの日本語文言を一元管理する。難易度キーは `difficulty_basic`(基礎)、`difficulty_standard`(標準)、`difficulty_basic_standard`(基礎〜標準)、`difficulty_advanced`(発展)を定義する(`frontend/web/src/strings.ja.json:159-162`)。2年生の九九設定では `setting_question_order_label`(出題順序)と `setting_option_order_ascending`/`descending`/`random`(1から/9から/ランダム)を提供する(`frontend/web/src/strings.ja.json:163-195`)。2年生の発展項目には「答えが1,000までの足し算」というタイトルと、3桁までの数を使い答えを1,000以下にする説明を提供する(`frontend/web/src/strings.ja.json:214-217`)。

`grade_point_1`〜`grade_point_6`(issue #157)は `catalog.js` のページヘッダーdescriptionに使う、学年ごとの指導ポイント文言。`menu_*_point`(60件、`drillPresets.js` の各アイテムの `pointKey` に対応)は `presetDetail.js` のページヘッダーdescriptionに使う、ドリルごとの指導ポイント文言。いずれも保護者(非専門家)が読むことを想定し、専門用語を避けた平易な一文で「なぜこの単元が大事か」を伝える文体を採用する。既存の `menu_*_desc`(旧 `drillCatalog.js` 向けの機械的な説明文)とは文体・用途が異なる別系統のキーとして併存する([[./drillPresets.js]] 参照)。

## 統合ポイント

- 呼び出し元: `strings.js` がJSON moduleとしてimportする。
- 利用元: `catalog.js`、`pcMakeFlow.js`、`presetDetail.js` など、`t()` を呼ぶ各UIモジュール。

## 注意事項・既知の制限

- `frontend/web` は日本語専用であり、言語別JSONの切り替え機構はない。
- 未定義キーは `strings.js` によりキー文字列そのものが表示される。

## 変更履歴（git log より自動生成）

- 32dd948 feat(#153): add reusable result ceiling for ope drills
- 06870bb #148 Add multiplication-table question-order options (#150)
- 85e58b1 #146 Add an advanced difficulty badge to the web UI (#147)
- 1edfbb5 fix(frontend/web): clarify grade-2/3 arithmetic menu label wording
- d43d1bc #130 frontend/web: make catalog page accent color switch dynamically per grade (#131)
- 77f95b7 #101 frontend/web: add PC 4-column layout to the make flow (#119)
- 9d1371e #100 frontend/web: rebuild preset detail settings/completion/preview screens (#118)
- 1bd6fa6 #99 Rebuild frontend/web top and catalog screens to match wireframe screens 1-2 (#116)
- 94eb478 #98 Rebuild frontend/web drill menu data model to match calculation_drill_menu_parameters_v1.md (#115)
- 8007488 #97 frontend/web: rebuild nav shell, design tokens, and remove legacy features (#109)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
