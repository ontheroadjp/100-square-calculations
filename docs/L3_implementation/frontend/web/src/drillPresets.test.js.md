# `frontend/web/src/drillPresets.test.js`

## 目的・役割

`drillPresets.js` の grade → category → menu-item データモデルが、UIとPDF生成処理の前提を満たすことをNode標準テストで検証する。

## 動作の概要

全学年と未分類の全メニュー項目を列挙し、カテゴリ、必須フィールド、設定、IDの一意性、既定設定からのリクエスト生成、動的例題を検証する。`difficultyKey` は `KNOWN_DIFFICULTY_KEYS` に含まれることを要求し、基礎・標準・基礎〜標準・発展以外の未知の値やタイプミスを失敗させる(`frontend/web/src/drillPresets.test.js:5-16,26-34,50-61`)。`descKey` と同様に `pointKey`(issue #157、`presetDetail.js` のヘッダーdescription用)が文字列であることも検証する(`frontend/web/src/drillPresets.test.js:55-56`)。choice 設定の任意の `disabledWhen`/`resolveValue` が関数であることを検証し、2年生九九の固定段3順序がフラグなし/`descend`/`shuffle` へ変換されること、および「まぜる」が保持中の順序にかかわらず従来のランダム `ope` パラメータを返すことを回帰テストする(`frontend/web/src/drillPresets.test.js:65-107`)。`type: 'fixed'` 設定が `options` を持つ場合(issue #303)は、その `options` が非空配列で各要素が `value`/`labelKey` 文字列を持ち、かつ `labelKey === valueLabelKey` に一致する option が必ず1つ含まれる不変条件を「every settings entry is a valid choice or fixed setting」テストで全項目にわたり検証する。

2年生の発展足し算・発展引き算(issue #154)について、それぞれ addition/subtraction カテゴリに存在し、`difficulty_advanced`/`latexOnly: true` を持ち、既定の「まぜる」状態から1〜999のオペランド範囲と `result_max: 1000` を生成することを検証する(`frontend/web/src/drillPresets.test.js:100-132`)。

1年生の足し算(issue #305)について、`g1-add-10` が `type: 'fixed'` の `carryMode` 設定(`valueLabelKey: 'setting_option_none'`)を持ち `buildParams()` が従来どおり `carry_mode: 'none'`/`result_max: 10` を返すこと、`g1-add-20` が `type: 'choice'` の `carryMode`(options `none`/`required`/`mixed`)を持ち、`required` は 1桁+1桁(`a_max: 9`)、`none`/`mixed` は加数 A を 1..19 に広げた混在レンジを `result_max: 20` で返すこと(`mixed` と無引数呼び出しは `carry_mode` を省略)を検証する。

1年生の引き算(issue #307)について対称に、`g1-sub-10` が `type: 'fixed'` の `carryMode` 設定(`valueLabelKey: 'setting_option_none'`)を持ち `buildParams()` が `carry_mode: 'none'`/`result_max: 10` を返すこと(旧 `10-6` 型を生成しない)、`g1-sub-20` が `type: 'choice'` の `carryMode`(options `none`/`required`/`mixed`)を持ち、`required` は 10〜19 の被減数(`a_min: 10`、`carry_mode: 'required'`)、`none`/`mixed` は被減数を 2..19 に広げた混在レンジを `result_max: 20` で返すこと(`mixed` と無引数呼び出しは `carry_mode` を省略)を検証する。

6年生の分数×整数・整数×分数・分数×分数・分数÷整数・整数÷分数・分数÷分数(計6項目、issue #114)について、`supportLevel` が `'full'` であること、および `reduction` 設定の `required`/`none`/`mixed` の各値と未設定時のフォールバック(`'mixed'`)が `buildParams(state).reducible_mode` へそのまま反映されることを検証する。

1年生「3つの数の足し引き」(`g1-three-terms`、issue #309)について、`operators` choice が `add`/`sub`/`addsub` をこの順で持ち(`sub` = `setting_option_sub_only` を `add` と `addsub` の間に）既定が `addsub` であること、`buildParams({operators})` が `add`→`operator:['add']`、`sub`→`operator:['sub']`(いずれも `mixed_operators` なし)、`addsub` と無引数→`operator:['add','sub'], mixed_operators:true` を返すこと(3モードとも `terms:3, a_min:1,a_max:9,b_min:1,b_max:9`)、および `examplesFor` が `add`→加算のみ・`sub`→減算のみの例題を返し `addsub`・無引数は静的 `examples` と一致することを検証する。

## 重要な設計判断とその理由

難易度は単なる文字列型ではなくUIの文言・CSS・互換分類と結び付く列挙値であるため、文字列であることだけでなく既知キーとの一致を検証する。

## 統合ポイント

- テスト対象: `drillPresets.js` の `GRADES`、`UNGRADED`、`presetsByGrade`。
- 実行方法: `node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js`。

## 注意事項・既知の制限

- DOM描画やSassの見た目は検証せず、データモデルの契約だけを対象とする。

## 変更履歴（git log より自動生成）

- b77d1db feat(#307): add borrow-mode settings to grade 1 subtraction drills
- 2f6add1 feat(#305): add carry-mode settings to grade 1 addition drills (#306)
- a4104ca feat(#303): render fixed drill settings as an inactive segmented control (#304)
- 231bde1 #134 frontend/web: add 出題形式 (式/筆算) setting to add/sub/mul/div preset detail pages (#181)
- d542657 #176 frontend/web: cap the answer for grade-1/2 basic ope drills at their titled bound (#178)
- 7b064ef #114 nuts_calc_tex.py: add reducibility control to frac/mixed multiplication and division (#165)
- 17070be #161 frontend/web: rebuild grade-3 addition/subtraction menu, retire fraction category, add four-operations drills (#162)
- 9b366c1 #157 Add per-grade/per-drill header descriptions via a shared page header component (#160)
- c9011f1 #154 Add grade-2 advanced subtraction capped at 1,000 (#159)
- 1a32b29 #153 Add reusable result ceilings and grade-2 addition up to 1,000 (#158)
