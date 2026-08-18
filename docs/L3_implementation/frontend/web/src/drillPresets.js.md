# `frontend/web/src/drillPresets.js`

## 目的・役割

`docs/uiux/calculation_drill_menu_parameters_v1.md` に定義された学年別ドリルメニューを、grade → category → menu-item の階層データとして保持する。`POST /generate-pdf` へのリクエストパラメータへのマッピングを担う純粋な ES module で、React・i18next に依存しない(issue #98)。issue #88 時点では `frontend/spa/src/drillPresets.js` の単純コピーだったが、#98 で `frontend/web` 専用の新データモデルへ全面的に書き換えられ、両ファイルの内容は完全に分岐した(以後、追従コピー関係はない)。

## 動作の概要

`GRADES`(`[1,2,3,4,5,6]`)・`UNGRADED`(`'ungraded'`)・`presetsByGrade` を export する。`presetsByGrade[grade]` は `{ <categoryId>: menuItem[] }` の形で、`categoryId` は `addition`/`subtraction`/`multiplication`/`division`/`fraction`/`four-operations`/`number-sense` のいずれか(該当する学年にのみ出現)。

各 `menuItem` は以下を持つ:
- `id`/`titleKey`/`descKey`/`pointKey`: 全データモデル中で `id` は一意。`pointKey`(issue #157)は `presetDetail.js` のページヘッダーに表示する、保護者向けの平易な指導ポイント文言(60件、[[./pageHeader.js]] 参照)。既存の `descKey` はもともと旧 `drillCatalog.js` 向けの機械的な説明文で、同ファイルが issue #110 で削除された現在は本データモデル上のフィールドとしてのみ残る(`drillPresets.test.js` が全項目に `descKey` が存在することを検証しているため、フィールド自体は残置)。`pointKey` とは用途・文体が異なる別系統のキーとして併存する。
- `difficultyKey`: `difficulty_basic`/`difficulty_standard`/`difficulty_basic_standard`/`difficulty_advanced` のいずれか(ドキュメントの「難易度」列)。1年生の `g1-three-terms` は `difficulty_advanced` を使用する(`frontend/web/src/drillPresets.js:139-145`)。
- `examples`: ドキュメントの「計算式の例」列をそのまま文字列配列にしたもの。
- `settings`: ドキュメントの「固有設定」「選択可能値」「固定値・表示」を表す配列。各要素は `type: 'choice'`(セグメントコントロール、`options`/`default` を持つ)または `type: 'fixed'`(表示のみで変更不可、`valueLabelKey` を持つ)。`choice` の各 `option` は任意で `hintKey` を持てる(issue #132)。依存設定には任意の `disabledWhen(state)` と `resolveValue(state)` を持たせ、選択肢を表示したまま非活性化し、その間の表示・サマリ値を強制できる。`presetDetail.js` がこれらを解釈する([[./presetDetail.js]] 参照、`frontend/web/src/drillPresets.js:236-264`)。
- `buildParams(state)`: `state`(`{ <settingId>: <選択値> }`、`choice` 設定のみキーを持つ)から `POST /generate-pdf` のリクエストボディを組み立てる関数。
- `supportLevel`: `'full'`(`nuts_calc_tex.py` がその項目の全設定を実現できる)/`'partial'`(生成はできるが一部設定を実現できない)/`'none'`。#98 時点では全項目 `full` または `partial` で、`none` は未使用(#91-#96 で対象コマンドが出揃ったため)。
- `latexOnly`: ほぼ全項目で `true`(carry_mode/remainder_mode/decimal places/terms/frac/mixed/compare/数論系コマンドが `nuts_calc_tex.py` 専用のため)。プレーンな `ope`(掛け算のみ等)や `99`/`aBc`/`squ` の一部項目のみ `false`。
- `examplesFor(settingsState)`(任意、issue #135): `examples` を選択中の設定値に応じて動的に切り替えたい項目だけが持つ。`presetDetail.js` の `selectExamples(item, settingsState)` から呼ばれる([[./presetDetail.js]] 参照)。

## 重要な設計判断とその理由

### （削除済み）`drillCatalog.js` との役割分担

issue #98 時点では `drillCatalog.js` が本ファイルを消費する側として存在し、`buildDrillCatalog`/`filterDrillCatalog` の公開 API を変更せず内部実装だけをこの新データモデルに対応させていた。issue #99/#100 で `home.js`/`catalog.js`/`preset.js` が `presetsByGrade` を直接消費する方式へ移行して依存がなくなり、issue #110 で `drillCatalog.js` 自体を削除した。

### `partial` サポートの項目と根拠(実機検証で判明した未追跡ギャップ)

以下は #91-#96 のいずれにも含まれない、#98 実装時の検証で新たに判明したバックエンド制約:
- 4・5年生「分数の足し算/引き算」(`g4-fraction-add`/`sub`、`g5-fraction-add`/`sub`)は issue #112 で `frac` コマンドが `--a-fraction-form`/`--b-fraction-form`(`mixed`/`mix`)による帯分数対応を実装したため `full` に引き上げ済み。詳細は下記「帯分数(#112)対応」を参照。
- 3年生「小数第1位までの足し算/引き算」・4年生「小数の足し算/引き算」: `--carry-borrow`系フラグは整数専用で、`--a-decimal-places`/`--b-decimal-places` と併用不可(`nuts_calc_tex.py:610-611`)。→ issue #113。
- 6年生の分数×整数・整数×分数・分数×分数・分数÷整数・整数÷分数・分数÷分数(計6項目): `frac`/`mixed` とも Python の `Fraction` が自動的に既約分数へ簡約するため、「約分が必要になるかどうか」を制御するフラグが存在しない。→ issue #114。

`partial` の項目も `settings` にはドキュメント通りの選択肢を全て含める(将来 backend 側の issue が閉じた際、データモデルの再設計なしに `supportLevel` を `full` へ引き上げられるようにするため)。

### 帯分数(#112)対応: `fractionFormParams`/`proper_result` の連動

`NUMBER_KIND_OPTIONS`(`fraction`/`mixedNumber`/`mixed`、docs の「数の種類: 分数/帯分数を含む/まぜる」)を `fraction: {} / mixedNumber: {a,b}_fraction_form='mixed' / mixed: {a,b}_fraction_form='mix'` へ変換する `fractionFormParams(state)` ヘルパーを新設した。`numberKind` 未選択時の既定は `'mixed'`(=「まぜる」)で、これは backend の `--a-fraction-form mix --b-fraction-form mix` が a/b を独立抽選する挙動と一致する(`compare` コマンドの `--a-fraction-form`/`--b-fraction-form` と同じ設計、[[../../../../backend/nuts_calc_tex.py]] の該当セクション参照)。

`g4-fraction-sub`/`g5-fraction-sub` の `proper_result`(答え<1を要求)は `numberKind === 'fraction'` のときだけ真にする。帯分数を含む繰り下がりの答えは1以上になりうる(docs の例 `3 2/5-1 4/5=1 3/5`)ため、`proper_result: true` を無条件のままにすると帯分数繰り下がりドリルが成立しない。

### `--mixed-carry-borrow`/`--mixed-remainder` の単一演算子制約

`--mixed-carry-borrow` は `-o add sub` の両方を指定した場合のみ有効で、単一演算子(`add`のみ・`sub`のみ)には使えない(`nuts_calc_tex.py:603-604`)。そのため `carryModeField(operator, state)` ヘルパーは、単一演算子の項目で `carryMode: 'mixed'` が選ばれた場合、`carry_mode` パラメータ自体を省略する(carry_mode フラグ無指定と同じ意味 = 繰り上がり/繰り下がりを制約しない、が「まぜる」の意図と一致するため)。

### 選択肢ヒント(`hintKey`)の汎用化

旧実装は「値が `'mixed'` の設定は `setting_mixed_hint` を表示する」というハードコードだった。issue #132 でこれを `option.hintKey` ベースの汎用機構へ置き換え、`OPT_MIXED`(`carrySetting`/`remainderSetting`/`REDUCTION_OPTIONS` が共有)および `dan`/`NUMBER_KIND_OPTIONS`/`DENOMINATOR_CHOICE_OPTIONS` それぞれの独立した `'mixed'` オプションリテラル(計4箇所)に `hintKey: 'setting_mixed_hint'` を付与した。表示文言・表示条件(該当オプションが選択されているとき)は旧実装と同一で、挙動の変更はない。

### 選択中の設定に応じた例題切り替え(`examplesFor`/`examplesByChoice`、issue #135)

`presetDetail.js` の設定画面は元々 `item.examples`(静的配列)を常に表示していたが、issue #135 で選択中の設定を反映するよう変更した。バックエンドから実際の問題文をリアルタイム取得する仕組みは存在しない(`POST /generate-pdf` は PDF しか返さない)ため、静的にオーサリングした例題文字列を選択状態に応じて出し分ける方式を採用した。動的化そのものは別issue(#137 親、#138 backend API 新設、#139 frontend/web 動的プレビュー)へ切り出し済み。

汎用ヘルパー `examplesByChoice(settingIds, byCombo)`(`drillPresets.js:66-72`)は、`settingIds`(例: `['carryMode']`、複数設定なら `['denominator', 'numberKind']`)の現在値を `_` 結合したキーで `byCombo` を引く `examplesFor(settingsState)` を返す。全設定が既定値 `'mixed'` のときのキー(単一なら `'mixed'`、複数なら `'mixed_mixed'` 等)は `byCombo` に必ず存在させる規約とし、未知の値・未設定のフォールバック先にも使う。これにより、既定状態(`state.settingsState` が全設定のデフォルト値)での `examplesFor()` の出力は必ず元の静的 `examples` と一致する(`drillPresets.test.js` の `examplesFor(defaultState) matches the static examples array` で保証)。

`carryMode`/`remainderMode`/`denominator`/`numberKind`/`reduction`/`dan` を **choice型**で持つ23項目にのみ `examplesFor` を付与した(`fixed`型でしか持たない項目や、対象外の choice 設定(`operators` 等)しか持たない項目は対象外で、静的 `examples` のまま)。`supportLevel: 'partial'` な項目(小数の carry/borrow 系、6年生の reduction 系)は `buildParams` が実際には該当設定を無視するため、`examplesFor` が返す内容は「その設定を選ぶとどんな問題を意味するか」を示す説明用であり、実際に生成される PDF の内容と一致する保証はない(該当箇所にコメントで明記)。

### 九九(`g2-kuku`)の段選択

「1〜9の段」選択時は `command_type: '99'`(`a_value` に段を指定)、「まぜる」選択時は `command_type: 'ope', operator: ['mul']`(`a_min`/`a_max`/`b_min`/`b_max` を1〜9のランダム)に切り替える。固定段には「出題順序」(`ascending`/`descending`/`random`)があり、それぞれフラグなし/`descend: true`/`shuffle: true` に変換する。「まぜる」では全ての順序選択肢を表示したまま非活性化し、`resolveValue` で `random` を選択表示する。実際の生成は従来通り `ope` の両オペランドランダムであり、保持中の `questionOrder` 値には依存しない(`frontend/web/src/drillPresets.js:220-277`)。例題も固定段では選択順序に応じて先頭2問相当へ切り替える(`frontend/web/src/drillPresets.js:225-235`)。

### 2年生「答えが1,000までの足し算」「答えが1,000までの引き算」

`g2-add-result-1000` は2年生の addition カテゴリに置く発展項目で、1〜999の両オペランド範囲を保ったまま `result_max: 1000` を送る。単に各オペランドを500以下へ狭める方式では `999+1` のような有効問題を失うため、レンダラー共通の結果上限を利用する。既存の「100までの足し算」と同じ繰り上がり設定・動的例題を持ち、LaTeX専用 `carry_mode`/`result_max` を使うため `latexOnly: true` とする(`frontend/web/src/drillPresets.js:176-216`)。

`g2-sub-result-1000`(issue #154)は subtraction カテゴリの対称項目で、同じ `a_min:1, a_max:999, b_min:1, b_max:999, result_max: 1000` を送る。`calc_sub` は常に `a - b > 0` になるまでリトライするため、この演算子では `result_max` は算術上非拘束(最大でも `999-1=998<1000`)だが、足し算エントリと自己文書的に対称な形を保つため明示的に付与している。設定は「100までの引き算」と同じ `carrySetting('setting_borrow_label')` を使う(`frontend/web/src/drillPresets.js:217-255`)。

### ドキュメントにない既存機能の扱い(written/examPrep/missing-value)

`docs/uiux/calculation_drill_menu_parameters_v1.md` に定義がない、以下の旧機能は #98 でデータモデルから削除した(ユーザー承認済み):
- 筆算(縦書き/`--vertical`)形式のペアリング(`written` バケット)。
- 中学受験対策(examPrep、27プリセット)。
- 虫食い算(`--missing-value`)。

いずれも `frontend/spa` および CLI では引き続き利用可能。復活させるかどうかは issue #111 で後日判断する。筆算(縦書き)形式については、issue #133(親)配下の #134 が「表示形式(式/筆算)」設定として `frontend/web` へ個別設定の形で再導入することを起案済み(#111 の筆算部分をこちらで解決する位置づけ)。

## 統合ポイント

- 呼び出し元: `catalog.js`/`preset.js`(`GRADES`/`UNGRADED`/`presetsByGrade` を直接消費)、`presetDetail.js`(`item.examplesFor`/`item.examples` を `selectExamples()` 経由で参照、`item.pointKey` をヘッダーdescriptionとして参照、[[./presetDetail.js]] 参照)。
- 呼び出し先: なし(データ定義のみ)。

## 注意事項・既知の制限

- `frontend/spa/src/drillPresets.js` とはもはや無関係(#98 で分岐)。今後 `frontend/spa` 側のプリセットを変更しても本ファイルには影響しない。
- `settings`/`buildParams`/`examplesFor` を実際にユーザーが切り替える UI は `presetDetail.js`(`preset.html`)が実装している([[./presetDetail.js]] 参照)。

## 変更履歴（git log より自動生成）

- 1ae72a3 feat(#157): add per-grade/per-drill header descriptions via a shared page header component
- c9011f1 #154 Add grade-2 advanced subtraction capped at 1,000 (#159)
- 1a32b29 #153 Add reusable result ceilings and grade-2 addition up to 1,000 (#158)
- 06870bb #148 Add multiplication-table question-order options (#150)
- 85e58b1 #146 Add an advanced difficulty badge to the web UI (#147)
- 1d8ee60 #135 frontend/web: switch preset detail page example problems based on selected settings (#141)
- 2d9ee47 #132 frontend/web: dynamic grade accent, KaTeX fraction examples, generalized setting hints, and move problem count into common settings on preset detail page (#136)
- e8db9d7 #112 nuts_calc_tex.py: add mixed-number (帯分数) display support to the frac command (#125)
- 94eb478 #98 Rebuild frontend/web drill menu data model to match calculation_drill_menu_parameters_v1.md (#115)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
