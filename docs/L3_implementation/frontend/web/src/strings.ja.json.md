# `frontend/web/src/strings.ja.json`

## 目的・役割

`frontend/web` の日本語UI文言をキーと文字列の対応として保持する。`strings.js` の `t(key)` がこのJSONを読み、該当キーの文言を返す。

## 動作の概要

画面見出し、操作ラベル、ドリル名、設定値などの日本語文言を一元管理する。難易度キーは `difficulty_basic`(基礎)、`difficulty_standard`(標準)、`difficulty_basic_standard`(基礎〜標準)、`difficulty_advanced`(発展)を定義する(`frontend/web/src/strings.ja.json:118-121`)。2年生の九九設定では `setting_question_order_label`(出題順序)と `setting_option_order_ascending`/`descending`/`random`(1から/9から/ランダム)を提供する(`frontend/web/src/strings.ja.json:128-154`)。2年生の発展項目には「1,000までの足し算」「1,000までの引き算」というタイトル(issue #161 でそれぞれ「答えが1,000までの足し算」「答えが1,000までの引き算」から短縮)と、3桁までの数を使い答えを1,000以下にする説明を提供する(`frontend/web/src/strings.ja.json:181-189`)。`menu_g1_add_20_desc` は issue #305 で `g1-add-20` の繰り上がり設定が選択可能(なし/あり/まぜる)になったのに合わせ、「繰り上がりのある、1桁どうしの足し算…」から「20までの数の足し算…繰り上がりは『なし』『あり』『まぜる』から選べます」へ改訂した。`menu_g1_sub_20_desc` も issue #307 で対称に、「繰り下がりのある、10〜19の数からの引き算…」から「20までの数の引き算…繰り下がりは『なし』『あり』『まぜる』から選べます」へ改訂した。`setting_option_sub_only`(「引き算のみ」)は issue #309 で `g1-three-terms` の演算モードに「引き算のみ」を追加した際に新設し、既存の `setting_option_add_only`(足し算のみ)と `setting_option_addsub_mixed`(足し引き混合)の間に置いた。同 issue で `menu_g1_three_terms_desc` も「足し算のみ、または足し算・引き算を混ぜて出題します」から「『足し算のみ』『引き算のみ』『足し引き混合』から選べます」へ改訂した([[./drillPresets.js]] 参照)。issue #311 は同じ演算モード追加を2年生の `g2-addsub-mixed` にも適用し、キー名は据え置いたまま `menu_g2_addsub_mixed_title` を「足し算・引き算の混合計算」から1年生と同じ「3つの数の足し引き」へ改称、`menu_g2_addsub_mixed_desc` を「＋と－を含む計算を練習します。」から「3つの数を順に足したり引いたりする練習です。「足し算のみ」「引き算のみ」「足し引き混合」から選べます。」へ、`menu_g2_addsub_mixed_point` を「＋と－が混ざった式を…」から「3つの数を、左から順番に一歩ずつ計算する練習です。式を焦らず進める習慣がつきます。」へ改訂した(「＋と－が混ざった」という限定表現が「足し算のみ」「引き算のみ」と不整合になるため)。issue #317 は5年生の `g5-decimal-div` を「小数÷小数」から `menu_g5_decimal_div_title`「整数と小数の割り算」へ改称し、`_desc`/`_point` を被除数選択(整数÷小数 / 小数÷小数 / まぜる)に合わせて改訂、`setting_dividend_label`(被除数)・`setting_option_integer_div_decimal`(整数÷小数)・`setting_option_decimal_div_decimal`(小数÷小数)を新設した(`setting_option_mixed` は流用、[[./drillPresets.js]] 参照)。issue #320 はカテゴリ見出しラベル `category_decimal`(「小数」)を `category_division`(「わり算」)と `category_fraction`(「分数」)の間に新設した。5年生の `multiplication`/`division` カテゴリ廃止に伴う新カテゴリで、`category_multiplication`/`category_division`(他学年が使用)は削除していない([[./drillPresets.js]]・[[./catalog.js]] 参照)。issue #327 は分数×整数・分数÷整数のドリルを学習指導要領に合わせて6年生から5年生へ移設したのに伴い、`menu_g6_fraction_mul_int_{title,desc,point}`・`menu_g6_fraction_div_int_{title,desc,point}` の6キーを文言そのままで `menu_g5_fraction_mul_int_*`・`menu_g5_fraction_div_int_*` へリネームし、`menu_g5_gcd_point` の直後(5年生ブロック)へ移動した(整数×分数・整数÷分数の `menu_g6_int_*_fraction_*` は6年生に残す、[[./drillPresets.js]] 参照)。issue #329 は4年生 `g4-decimal-mul-int` を乗数が整数の場合のみに戻したのに伴い、`menu_g4_decimal_mul_int_title` を「整数と小数の掛け算」から「小数×整数」へ、`_desc` を「小数に整数を掛ける計算を練習します。」へ、`_point` を「小数×整数の計算です。答えの小数点をどこに打つかがポイントになります。」へ改訂し(いずれも #313 以前の文言)、#313 で追加した `setting_option_int_times_decimal`(整数×小数)・`setting_option_decimal_times_int`(小数×整数)を他に参照がなくなったため削除した([[./drillPresets.js]] 参照)。issue #330 は括弧の足し引きドリル(`35-(12+8)`)を学習指導要領解説 算数編 第4学年 A「数量の関係を表す式」に合わせて2年生から4年生へ移設したのに伴い、`menu_g2_parentheses_{title,desc,point}` の3キーを文言そのままで `menu_g4_parentheses_addsub_{title,desc,point}` へリネームし、`menu_g4_four_operations_point` の直後(4年生ブロック)へ移動した(タイトル「括弧を含む足し引き」・説明文は不変、[[./drillPresets.js]] 参照)。

`grade_point_1`〜`grade_point_6`(issue #157)は `catalog.js` のページヘッダーdescriptionに使う、学年ごとの指導ポイント文言。`menu_*_point`(61件、`drillPresets.js` の各アイテムの `pointKey` に対応)は `presetDetail.js` のページヘッダーdescriptionに使う、ドリルごとの指導ポイント文言。いずれも保護者(非専門家)が読むことを想定し、専門用語を避けた平易な一文で「なぜこの単元が大事か」を伝える文体を採用する。既存の `menu_*_desc`(旧 `drillCatalog.js` 向けの機械的な説明文)とは文体・用途が異なる別系統のキーとして併存する([[./drillPresets.js]] 参照)。

issue #110 で `drillCatalog.js`(旧絞り込み/検索UIのアダプター)を削除した際、それ専用だった死んだキー47件(セクション見出し `subject_start_title`/`number_type_start_title`/`form_start_title`/`grade_start_title`、フィルタラベル `*_filter_label` 系、`all_*`/`clear_filters`、`subject_*`、`number_type_integers`/`_decimals`/`_fractions`/`_mixed` とその `_intro` 版、`operation_group_*`、`form_written`/`form_parentheses`/`form_missing-value`/`form_number-sense`/`form_exam-prep`、`level_basic`/`_standard`/`_advanced`/`_exam-prep`)も合わせて削除した。`no_drills_found` は `catalog.js`/`preset.js`/`pcMakeFlow.js` が引き続き使用するため保持した。

## 統合ポイント

- 呼び出し元: `strings.js` がJSON moduleとしてimportする。
- 利用元: `catalog.js`、`pcMakeFlow.js`、`presetDetail.js` など、`t()` を呼ぶ各UIモジュール。

## 注意事項・既知の制限

- `frontend/web` は日本語専用であり、言語別JSONの切り替え機構はない。
- 未定義キーは `strings.js` によりキー文字列そのものが表示される。

## 変更履歴（git log より自動生成）

- c20041c fix(#330): move parentheses add/sub drill from grade 2 to grade 4 and set difficulty to basic
- cbeb0a6 fix(#329): restrict grade 4 decimal×integer multiplication to an integer multiplier (#337)
- 5d42151 fix(#328): move parenthesized mixed-operation drill from grade 3 to grade 4 (#336)
- d31e15c fix(#327): reassign fraction-by-integer mul/div drills from grade 6 to grade 5 (#335)
- f440b57 refactor(#320): replace grade 5 multiplication/division sections with a dedicated 小数 section (#321)
- f85a421 feat(#317): add integer/decimal dividend selection to grade 5 decimal division (#319)
- 40dfb0a feat(#313): add mixed decimal operand order to grade 4 integer/decimal multiplication (#314)
- 7334a3a feat(#311): rename grade 2 three-term drill and add operator-mode selection (#312)
- 3278705 feat(#309): add subtraction-only mode to grade 1 three-term drill (#310)
- 571563e feat(#307): add borrow-mode settings to grade 1 subtraction drills (#308)
