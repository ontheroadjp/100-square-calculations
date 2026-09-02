# `frontend/web/src/drillPresets.test.js`

## 目的・役割

`drillPresets.js` の grade → category → menu-item データモデルが、UIとPDF生成処理の前提を満たすことをNode標準テストで検証する。

## 動作の概要

全学年と未分類の全メニュー項目を列挙し、カテゴリ、必須フィールド、設定、IDの一意性、既定設定からのリクエスト生成、動的例題を検証する。`difficultyKey` は `KNOWN_DIFFICULTY_KEYS` に含まれることを要求し、基礎・標準・基礎〜標準・発展以外の未知の値やタイプミスを失敗させる(`frontend/web/src/drillPresets.test.js:5-16,26-34,50-61`)。`descKey` と同様に `pointKey`(issue #157、`presetDetail.js` のヘッダーdescription用)が文字列であることも検証する(`frontend/web/src/drillPresets.test.js:55-56`)。choice 設定の任意の `disabledWhen`/`resolveValue` が関数であることを検証し、2年生九九の固定段3順序がフラグなし/`descend`/`shuffle` へ変換されること、および「まぜる」が保持中の順序にかかわらず従来のランダム `ope` パラメータを返すことを回帰テストする(`frontend/web/src/drillPresets.test.js:65-107`)。`type: 'fixed'` 設定が `options` を持つ場合(issue #303)は、その `options` が非空配列で各要素が `value`/`labelKey` 文字列を持ち、かつ `labelKey === valueLabelKey` に一致する option が必ず1つ含まれる不変条件を「every settings entry is a valid choice or fixed setting」テストで全項目にわたり検証する。

2年生の発展足し算・発展引き算(issue #154)について、それぞれ addition/subtraction カテゴリに存在し、`difficulty_advanced`/`latexOnly: true` を持ち、既定の「まぜる」状態から1〜999のオペランド範囲と `result_max: 1000` を生成することを検証する(`frontend/web/src/drillPresets.test.js:100-132`)。

1年生の足し算(issue #305)について、`g1-add-10` が `type: 'fixed'` の `carryMode` 設定(`valueLabelKey: 'setting_option_none'`)を持ち `buildParams()` が従来どおり `carry_mode: 'none'`/`result_max: 10` を返すこと、`g1-add-20` が `type: 'choice'` の `carryMode`(options `none`/`required`/`mixed`)を持ち、`required` は 1桁+1桁(`a_max: 9`)、`none`/`mixed` は加数 A を 1..19 に広げた混在レンジを `result_max: 20` で返すこと(`mixed` と無引数呼び出しは `carry_mode` を省略)を検証する。

1年生の引き算(issue #307)について対称に、`g1-sub-10` が `type: 'fixed'` の `carryMode` 設定(`valueLabelKey: 'setting_option_none'`)を持ち `buildParams()` が `carry_mode: 'none'`/`result_max: 10` を返すこと(旧 `10-6` 型を生成しない)、`g1-sub-20` が `type: 'choice'` の `carryMode`(options `none`/`required`/`mixed`)を持ち、`required` は 10〜19 の被減数(`a_min: 10`、`carry_mode: 'required'`)、`none`/`mixed` は被減数を 2..19 に広げた混在レンジを `result_max: 20` で返すこと(`mixed` と無引数呼び出しは `carry_mode` を省略)を検証する。

6年生の整数×分数・分数×分数・整数÷分数・分数÷分数(4項目、issue #114)について、`supportLevel` が `'full'` であること、および `reduction` 設定の `required`/`none`/`mixed` の各値と未設定時のフォールバック(`'mixed'`)が `buildParams(state).reducible_mode` へそのまま反映されることを検証する。分数×整数・分数÷整数は issue #327 で5年生へ移設したため、この #114 テストの id リストから外し(6年生に残る4項目のみ)、別途「分数×整数 / 分数÷整数 live in the grade 5 fraction category, not grade 6(issue #327)」テストで、`g6-fraction-mul-int`/`g6-fraction-div-int` が `presetsByGrade[6].fraction` に存在しないこと、および `g5-fraction-mul-int`/`g5-fraction-div-int` が `presetsByGrade[5].fraction` に存在し `supportLevel: 'full'`・`latexOnly: true`・`buildParams` の形(`command_type: 'mixed'`、`operator`、`a_kind: ['fraction']`、`b_kind: ['int']`)・`reducible_mode` 配線を満たすことを検証する。

1年生「3つの数の足し引き」(`g1-three-terms`、issue #309)について、`operators` choice が `add`/`sub`/`addsub` をこの順で持ち(`sub` = `setting_option_sub_only` を `add` と `addsub` の間に）既定が `addsub` であること、`buildParams({operators})` が `add`→`operator:['add']`、`sub`→`operator:['sub']`(いずれも `mixed_operators` なし)、`addsub` と無引数→`operator:['add','sub'], mixed_operators:true` を返すこと(3モードとも `terms:3, a_min:1,a_max:9,b_min:1,b_max:9`)、および `examplesFor` が `add`→加算のみ・`sub`→減算のみの例題を返し `addsub`・無引数は静的 `examples` と一致することを検証する。

2年生「3つの数の足し引き」(`g2-addsub-mixed`、issue #311)について、上記 `g1-three-terms` テストと対称の内容を検証する。`operators` choice の option 順序・labelKey・既定(`addsub`)、`buildParams` の3モード写像(`add`/`sub` は `mixed_operators` なし、`addsub` と無引数は `mixed_operators: true`。3モードとも `terms:3, a_min:1,a_max:99,b_min:1,b_max:99`、`result_max` なし)、`examplesFor` の演算子追従(`add`→`-` を含まない、`sub`→`+` を含まない、`addsub`・無引数は静的 `examples` と一致)を確認する。

5年生の小数カテゴリ(issue #320)について、`presetsByGrade[5].multiplication`/`presetsByGrade[5].division` がいずれも `undefined` であること、`presetsByGrade[5].decimal` が `['g5-decimal-mul', 'g5-decimal-div']` をこの順で持つこと、`g5-decimal-four-ops` が引き続き `four-operations` カテゴリに存在することを検証する。`KNOWN_CATEGORIES` セットにも `'decimal'` を追加した。

5年生「整数と小数の割り算」(`g5-decimal-div`、issue #317)について、`dividendType` choice が `integer_div_decimal`/`decimal_div_decimal`/`mixed` をこの順・対応 labelKey で持ち既定が `mixed` であること、`buildParams` の3モード写像(`integer_div_decimal`→`a_decimal_places:0, dividend_mode:'integer'`、`decimal_div_decimal`→`a_decimal_places:1` のみ(#317 前と同一・`dividend_mode` なし)、`mixed`・無引数・`{}`→`a_decimal_places:1, dividend_mode:'mixed'`。3モードとも `command_type:'ope', operator:['div'], a_digits:2, b_digits:2, b_decimal_places:1`)、`examplesFor` の追従(`integer_div_decimal`→`整数÷小数.` パターン、`decimal_div_decimal`→`小数÷小数.` パターン、`mixed`は静的 `examples` と一致)を確認する。

## 重要な設計判断とその理由

難易度は単なる文字列型ではなくUIの文言・CSS・互換分類と結び付く列挙値であるため、文字列であることだけでなく既知キーとの一致を検証する。

## 統合ポイント

- テスト対象: `drillPresets.js` の `GRADES`、`UNGRADED`、`presetsByGrade`。
- 実行方法: `node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js`。

## 注意事項・既知の制限

- DOM描画やSassの見た目は検証せず、データモデルの契約だけを対象とする。

## 変更履歴（git log より自動生成）

- 94df557 fix(#327): reassign 分数×整数 / 分数÷整数 drills from grade 6 to grade 5
- f440b57 refactor(#320): replace grade 5 multiplication/division sections with a dedicated 小数 section (#321)
- f85a421 feat(#317): add integer/decimal dividend selection to grade 5 decimal division (#319)
- 697db43 refactor(#315): move grade 4 fraction add/sub into addition/subtraction categories (#316)
- 40dfb0a feat(#313): add mixed decimal operand order to grade 4 integer/decimal multiplication (#314)
- 7334a3a feat(#311): rename grade 2 three-term drill and add operator-mode selection (#312)
- 3278705 feat(#309): add subtraction-only mode to grade 1 three-term drill (#310)
- 571563e feat(#307): add borrow-mode settings to grade 1 subtraction drills (#308)
- 2f6add1 feat(#305): add carry-mode settings to grade 1 addition drills (#306)
- a4104ca feat(#303): render fixed drill settings as an inactive segmented control (#304)
