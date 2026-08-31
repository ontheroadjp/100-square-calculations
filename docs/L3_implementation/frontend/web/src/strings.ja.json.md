# `frontend/web/src/strings.ja.json`

## 目的・役割

`frontend/web` の日本語UI文言をキーと文字列の対応として保持する。`strings.js` の `t(key)` がこのJSONを読み、該当キーの文言を返す。

## 動作の概要

画面見出し、操作ラベル、ドリル名、設定値などの日本語文言を一元管理する。難易度キーは `difficulty_basic`(基礎)、`difficulty_standard`(標準)、`difficulty_basic_standard`(基礎〜標準)、`difficulty_advanced`(発展)を定義する(`frontend/web/src/strings.ja.json:118-121`)。2年生の九九設定では `setting_question_order_label`(出題順序)と `setting_option_order_ascending`/`descending`/`random`(1から/9から/ランダム)を提供する(`frontend/web/src/strings.ja.json:128-154`)。2年生の発展項目には「1,000までの足し算」「1,000までの引き算」というタイトル(issue #161 でそれぞれ「答えが1,000までの足し算」「答えが1,000までの引き算」から短縮)と、3桁までの数を使い答えを1,000以下にする説明を提供する(`frontend/web/src/strings.ja.json:181-189`)。`menu_g1_add_20_desc` は issue #305 で `g1-add-20` の繰り上がり設定が選択可能(なし/あり/まぜる)になったのに合わせ、「繰り上がりのある、1桁どうしの足し算…」から「20までの数の足し算…繰り上がりは『なし』『あり』『まぜる』から選べます」へ改訂した。`menu_g1_sub_20_desc` も issue #307 で対称に、「繰り下がりのある、10〜19の数からの引き算…」から「20までの数の引き算…繰り下がりは『なし』『あり』『まぜる』から選べます」へ改訂した。`setting_option_sub_only`(「引き算のみ」)は issue #309 で `g1-three-terms` の演算モードに「引き算のみ」を追加した際に新設し、既存の `setting_option_add_only`(足し算のみ)と `setting_option_addsub_mixed`(足し引き混合)の間に置いた。同 issue で `menu_g1_three_terms_desc` も「足し算のみ、または足し算・引き算を混ぜて出題します」から「『足し算のみ』『引き算のみ』『足し引き混合』から選べます」へ改訂した([[./drillPresets.js]] 参照)。

`grade_point_1`〜`grade_point_6`(issue #157)は `catalog.js` のページヘッダーdescriptionに使う、学年ごとの指導ポイント文言。`menu_*_point`(61件、`drillPresets.js` の各アイテムの `pointKey` に対応)は `presetDetail.js` のページヘッダーdescriptionに使う、ドリルごとの指導ポイント文言。いずれも保護者(非専門家)が読むことを想定し、専門用語を避けた平易な一文で「なぜこの単元が大事か」を伝える文体を採用する。既存の `menu_*_desc`(旧 `drillCatalog.js` 向けの機械的な説明文)とは文体・用途が異なる別系統のキーとして併存する([[./drillPresets.js]] 参照)。

issue #110 で `drillCatalog.js`(旧絞り込み/検索UIのアダプター)を削除した際、それ専用だった死んだキー47件(セクション見出し `subject_start_title`/`number_type_start_title`/`form_start_title`/`grade_start_title`、フィルタラベル `*_filter_label` 系、`all_*`/`clear_filters`、`subject_*`、`number_type_integers`/`_decimals`/`_fractions`/`_mixed` とその `_intro` 版、`operation_group_*`、`form_written`/`form_parentheses`/`form_missing-value`/`form_number-sense`/`form_exam-prep`、`level_basic`/`_standard`/`_advanced`/`_exam-prep`)も合わせて削除した。`no_drills_found` は `catalog.js`/`preset.js`/`pcMakeFlow.js` が引き続き使用するため保持した。

## 統合ポイント

- 呼び出し元: `strings.js` がJSON moduleとしてimportする。
- 利用元: `catalog.js`、`pcMakeFlow.js`、`presetDetail.js` など、`t()` を呼ぶ各UIモジュール。

## 注意事項・既知の制限

- `frontend/web` は日本語専用であり、言語別JSONの切り替え機構はない。
- 未定義キーは `strings.js` によりキー文字列そのものが表示される。

## 変更履歴（git log より自動生成）

- a08546b feat(#309): add subtraction-only mode to grade 1 three-term drill
- 571563e feat(#307): add borrow-mode settings to grade 1 subtraction drills (#308)
- 2f6add1 feat(#305): add carry-mode settings to grade 1 addition drills (#306)
- 231bde1 #134 frontend/web: add 出題形式 (式/筆算) setting to add/sub/mul/div preset detail pages (#181)
- 56aa1d3 #110 Remove frontend/web's unused drillCatalog.js and dead filter-UI i18n keys (#163)
- 17070be #161 frontend/web: rebuild grade-3 addition/subtraction menu, retire fraction category, add four-operations drills (#162)
- 9b366c1 #157 Add per-grade/per-drill header descriptions via a shared page header component (#160)
- c9011f1 #154 Add grade-2 advanced subtraction capped at 1,000 (#159)
- 1a32b29 #153 Add reusable result ceilings and grade-2 addition up to 1,000 (#158)
- 06870bb #148 Add multiplication-table question-order options (#150)
