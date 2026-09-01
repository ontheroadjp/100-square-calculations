# `frontend/web/src/drillPresets.js`

## 目的・役割

`docs/uiux/calculation_drill_menu_parameters_v1.md` に定義された学年別ドリルメニューを、grade → category → menu-item の階層データとして保持する。`POST /generate-pdf` へのリクエストパラメータへのマッピングを担う純粋な ES module で、React・i18next に依存しない(issue #98)。issue #88 時点では `frontend/spa/src/drillPresets.js` の単純コピーだったが、#98 で `frontend/web` 専用の新データモデルへ全面的に書き換えられ、両ファイルの内容は完全に分岐した(以後、追従コピー関係はない)。

## 動作の概要

`GRADES`(`[1,2,3,4,5,6]`)・`UNGRADED`(`'ungraded'`)・`presetsByGrade` を export する。`presetsByGrade[grade]` は `{ <categoryId>: menuItem[] }` の形で、`categoryId` は `addition`/`subtraction`/`multiplication`/`division`/`fraction`/`four-operations`/`number-sense` のいずれか(該当する学年にのみ出現)。`fraction` は3年生(issue #161で撤廃)・4年生(issue #315で撤廃)を除く5〜6年生に残る。カテゴリキーは `catalog.js` の固定 `CATEGORY_ORDER`(`addition, subtraction, multiplication, division, fraction, four-operations, number-sense`)による学年ページのセクション見出し順序付けにのみ使われ、`drillCatalog.js` の絞り込み分類(`numberType`/`operationGroup`)には影響しない(`Object.values(categories)` でカテゴリキーを捨ててフラット化するため)。

各 `menuItem` は以下を持つ:
- `id`/`titleKey`/`descKey`/`pointKey`: 全データモデル中で `id` は一意。`pointKey`(issue #157)は `presetDetail.js` のページヘッダーに表示する、保護者向けの平易な指導ポイント文言(60件、[[./pageHeader.js]] 参照)。既存の `descKey` はもともと旧 `drillCatalog.js` 向けの機械的な説明文で、同ファイルが issue #110 で削除された現在は本データモデル上のフィールドとしてのみ残る(`drillPresets.test.js` が全項目に `descKey` が存在することを検証しているため、フィールド自体は残置)。`pointKey` とは用途・文体が異なる別系統のキーとして併存する。
- `difficultyKey`: `difficulty_basic`/`difficulty_standard`/`difficulty_basic_standard`/`difficulty_advanced` のいずれか(ドキュメントの「難易度」列)。1年生の `g1-three-terms` は `difficulty_advanced` を使用する(`frontend/web/src/drillPresets.js:226-278`)。
- `examples`: ドキュメントの「計算式の例」列をそのまま文字列配列にしたもの。
- `settings`: ドキュメントの「固有設定」「選択可能値」「固定値・表示」を表す配列。各要素は `type: 'choice'`(セグメントコントロール、`options`/`default` を持つ)または `type: 'fixed'`(変更不可、`valueLabelKey` を持つ。`presetDetail.js`/`pcMakeFlow.js` は choice と同一形状の非活性 segmented control として描画する、issue #303)。`fixedSetting(id, labelKey, valueLabelKey, options?)` の第4引数 `options` は任意で、兄弟 choice の option リスト(carry/remainder は `NONE_REQUIRED_MIXED_OPTIONS`、denominator は `DENOMINATOR_CHOICE_OPTIONS`)を渡すと非活性 control に全 option を表示できる。省略時は単一 disabled ピル。`options` を渡す場合は `labelKey === valueLabelKey` の option が必ず1つ含まれる不変条件を `drillPresets.test.js` が検証する。`choice` の各 `option` は任意で `hintKey` を持てる(issue #132)。依存設定には任意の `disabledWhen(state)` と `resolveValue(state)` を持たせ、選択肢を表示したまま非活性化し、その間の表示・サマリ値を強制できる。`presetDetail.js` がこれらを解釈する([[./presetDetail.js]] 参照)。
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
- 3年生「小数第1位までの足し算/引き算」(`g3-decimal-addsub`/`g3-decimal-sub`)・4年生「小数の足し算/引き算」(`g4-decimal-add`/`g4-decimal-sub`)は issue #113 で `nuts_calc_tex.py` の `--carry-borrow`系フラグが `--a-decimal-places`/`--b-decimal-places` と併用可能になったため `full` に引き上げ済み。`buildParams` に `carryModeField(['add'|'sub'], state)` を配線している(`drillPresets.js:388-407,445-464,667-686,689-708`)。
- 6年生の分数×整数・整数×分数・分数×分数・分数÷整数・整数÷分数・分数÷分数(計6項目)は、issue #114 で `nuts_calc_tex.py` に `--require-reducible`/`--no-reducible`/`--mixed-reducible` が追加されたことに伴い `full` へ引き上げ済み。詳細は下記「約分制御(#114)対応」を参照。

`partial` の項目も `settings` にはドキュメント通りの選択肢を全て含める(将来 backend 側の issue が閉じた際、データモデルの再設計なしに `supportLevel` を `full` へ引き上げられるようにするため)。

### 帯分数(#112)対応: `fractionFormParams`/`proper_result` の連動

`NUMBER_KIND_OPTIONS`(`fraction`/`mixedNumber`/`mixed`、docs の「数の種類: 分数/帯分数を含む/まぜる」)を `fraction: {} / mixedNumber: {a,b}_fraction_form='mixed' / mixed: {a,b}_fraction_form='mix'` へ変換する `fractionFormParams(state)` ヘルパーを新設した。`numberKind` 未選択時の既定は `'mixed'`(=「まぜる」)で、これは backend の `--a-fraction-form mix --b-fraction-form mix` が a/b を独立抽選する挙動と一致する(`compare` コマンドの `--a-fraction-form`/`--b-fraction-form` と同じ設計、[[../../../../backend/nuts_calc_tex.py]] の該当セクション参照)。

`g4-fraction-sub`/`g5-fraction-sub` の `proper_result`(答え<1を要求)は `numberKind === 'fraction'` のときだけ真にする。帯分数を含む繰り下がりの答えは1以上になりうる(docs の例 `3 2/5-1 4/5=1 3/5`)ため、`proper_result: true` を無条件のままにすると帯分数繰り下がりドリルが成立しない。

### 約分制御(#114)対応: `reducibleModeParam`

6年生の分数×整数(`g6-fraction-mul-int`)・整数×分数(`g6-int-mul-fraction`)・分数×分数(`g6-fraction-mul`)・分数÷整数(`g6-fraction-div-int`)・整数÷分数(`g6-int-div-fraction`)・分数÷分数(`g6-fraction-div`)の6項目は、いずれも `id: 'reduction'` の choice 設定(`REDUCTION_OPTIONS` = なし/あり/まぜる、既定 `'mixed'`)を持つ。`reducibleModeParam(state)`(`state?.reduction ?? 'mixed'`)を各 `buildParams` の `reducible_mode` フィールドへそのまま渡す。

`--mixed-reducible` は `nuts_calc_tex.py` 側に `--mixed-carry-borrow` のような単一演算子制約がない(演算子1つだけの `frac -o mul`/`mixed -o div` 等でもそのまま有効)ため、`carryModeField` のように単一演算子時に `mixed` を省略する特例は不要で、`remainderModeParam` と同じ「常に値をそのまま送る」パターンを踏襲する(`drillPresets.js:56-63` 付近)。

分数×整数/整数×分数の4項目は `command_type: 'mixed'`(`a_kind`/`b_kind` を `fraction`/`int` の片方ずつに固定、`nuts_calc_tex.py` の `_init()` が要求する2項限定・fraction+int 限定の条件を満たす)、分数×分数/分数÷分数の2項目は `command_type: 'frac'`(`proper_operands: true` と併用)を使う。

### `--mixed-carry-borrow`/`--mixed-remainder` の単一演算子制約

`--mixed-carry-borrow` は `-o add sub` の両方を指定した場合のみ有効で、単一演算子(`add`のみ・`sub`のみ)には使えない(`nuts_calc_tex.py:603-604`)。そのため `carryModeField(operator, state)` ヘルパーは、単一演算子の項目で `carryMode: 'mixed'` が選ばれた場合、`carry_mode` パラメータ自体を省略する(carry_mode フラグ無指定と同じ意味 = 繰り上がり/繰り下がりを制約しない、が「まぜる」の意図と一致するため)。

### 1年生の足し算の繰り上がり設定(issue #305)

`g1-add-10`(「10までの足し算」)は `result_max: 10` により繰り上がりが構造上発生しないが、`fixedSetting('carryMode', 'setting_carry_label', 'setting_option_none', NONE_REQUIRED_MIXED_OPTIONS)` で非活性の繰り上がり設定(`繰り上がり：なし` を選択表示)を持たせ、下記 `g1-add-20` の選択可能コントロールと表示を揃える。`buildParams` は従来どおり `carry_mode: 'none'` 固定。

`g1-add-20`(「20までの足し算」)は固定設定を廃し、`carrySetting('setting_carry_label')`(choice、なし/あり/まぜる、既定 `'mixed'`)へ変更した。`buildParams(state)` は繰り上がりモードで加数 A の上限を切り替える:

- `required`(あり): `carry_mode: 'required'`、`a_min:1, a_max:9, b_min:1, b_max:9, result_max:20`。初出単元の趣旨(10のまとまりを作る)に合わせ従来どおり 1桁+1桁 のくり上がりに限定する。
- `none`(なし): `carry_mode: 'none'`、`a_min:1, a_max:19, b_min:1, b_max:9, result_max:20`。加数 A を 1..19 に広げることで、繰り上がりなし・答え20以下の制約下で 1桁+1桁 と 2桁+1桁 が自然に混在する(お題が「20までの足し算」であり、この2つの出題形がともに成立するため)。加数 B は1桁のままなので出題形は {1桁+1桁, 2桁+1桁} に限定される。
- `mixed`(まぜる): `carryModeField(['add'], state)` が単一演算子のため `carry_mode` を省略し、`none` と同じ 1..19 / 1..9 のレンジを使う。

`examplesFor` は `examplesByChoice(['carryMode'], …)` で3モード分の例題を出し分ける(`mixed` キーは静的 `examples` と一致)。`menu_g1_add_20_desc` も「繰り上がりのある、1桁どうしの足し算」から「20までの数の足し算…繰り上がりは『なし』『あり』『まぜる』から選べます」へ改訂した([[./strings.ja.json]] 参照)。

### 1年生の引き算の繰り下がり設定(issue #307)

上記の足し算(issue #305)と対称に、1年生の引き算ペアにも繰り下がり設定を配線した。

`g1-sub-10`(「10までの引き算」)は非活性の `fixedSetting('carryMode', 'setting_borrow_label', 'setting_option_none', NONE_REQUIRED_MIXED_OPTIONS)`(`繰り下がり：なし` を選択表示)を持たせ、下記 `g1-sub-20` の選択可能コントロールと表示を揃える。表示と実体を一致させるため `buildParams` に `carry_mode: 'none'` を明示し、繰り下がりのある問題(旧例 `10-6` 等)を生成しないようにした(例も `8-3`/`9-4`/`7-2` に差し替え)。`a_min:2, a_max:10, b_min:1, b_max:9, result_max:10`。

`g1-sub-20`(「20までの引き算」)は固定設定(旧 `carry_mode: 'required'` 固定)を廃し、`carrySetting('setting_borrow_label')`(choice、なし/あり/まぜる、既定 `'mixed'`)へ変更した。`buildParams(state)` は繰り下がりモードで被減数の下限を切り替える:

- `required`(あり): `carry_mode: 'required'`、`a_min:10, a_max:19, b_min:1, b_max:9, result_max:20`。初出単元の趣旨(10のまとまりから借りる)に合わせ従来どおり 10〜19 の数からの繰り下がりに限定する。
- `none`(なし): `carry_mode: 'none'`、`a_min:2, a_max:19, b_min:1, b_max:9, result_max:20`。被減数を 2..19 に広げることで、繰り下がりなし・答え20以下の制約下で 1桁・2桁の数からの引き算が自然に混在する。減数は1桁のまま。
- `mixed`(まぜる): `carryModeField(['sub'], state)` が単一演算子のため `carry_mode` を省略し、`none` と同じ 2..19 / 1..9 のレンジを使う。

`examplesFor` は `examplesByChoice(['carryMode'], …)` で3モード分の例題を出し分ける(`mixed` キーは静的 `examples` と一致)。`menu_g1_sub_20_desc` も「繰り下がりのある、10〜19の数からの引き算」から「20までの数の引き算…繰り下がりは『なし』『あり』『まぜる』から選べます」へ改訂した([[./strings.ja.json]] 参照)。

### 1年生「3つの数の足し引き」の演算モードに「引き算のみ」を追加(issue #309)

`g1-three-terms`(`drillPresets.js:226-278`)の `operators` choice は元々 `add`(足し算のみ)/ `addsub`(足し引き混合、既定)の2値だった。両者の間に `sub`(引き算のみ、`setting_option_sub_only` = 「引き算のみ」)を追加し、既定は `addsub` のまま。`buildParams(state)` は `operatorByChoice = { add: ['add'], sub: ['sub'], addsub: ['add', 'sub'] }` で選択値を演算子配列へ写し、`operator.length > 1`(= `addsub`)のときだけ `mixed_operators: true` を付ける(単一演算子の `add`/`sub` は `mixed_operators` を出さない — [[../../../../backend/nuts_calc_tex.py]] の `--mixed-operators` は2演算子必須のため)。3モードとも `command_type: 'ope', terms: 3, a_min:1, a_max:9, b_min:1, b_max:9`。

この項目は `terms: 3` を常に送るため、issue #139 の live プレビュー対象でもある(下記 [[./presetDetail.js]] の multi-term 対応、issue #309)。`examplesFor` は backend 未到達時のフォールバック用に付与し(live 対象項目でも `examplesFor` を併存させる `g1-add-20`/`g1-sub-20` と同じ方針)、`operators` を直に読むインライン関数とした — `examplesByChoice` は fallback キーを `'mixed'` 固定で組み立てるため、`'mixed'` 値を持たない `operators`(`add`/`sub`/`addsub`)には合わない(`g2-kuku` の `dan` と同じ理由でインライン化)。`addsub` の返す配列は静的 `examples` と同一。

### 2年生「3つの数の足し引き」の改称と演算モード追加(issue #311)

issue #309 の `g1-three-terms` 変更を、2年生の `four-operations` カテゴリの `g2-addsub-mixed` にもそのまま適用した。変更前は `settings: [fixedSetting('operators', 'setting_operators_label', 'setting_option_addsub_mixed')]`(非活性の「足し引き混合」固定表示)と、引数を取らない `buildParams: () => ({ operator: ['add', 'sub'], terms: 3, mixed_operators: true, … })` だった。

- `settings` を `id: 'operators'` の choice(`add`/`sub`/`addsub`、`setting_option_add_only`/`setting_option_sub_only`/`setting_option_addsub_mixed`、既定 `addsub`)へ置き換えた。option の並びは `g1-three-terms` と揃え「引き算のみ」を中央に置く。
- `buildParams(state)` は `operatorByChoice = { add: ['add'], sub: ['sub'], addsub: ['add', 'sub'] }` で選択値を演算子配列へ写し、`operator.length > 1`(= `addsub`)のときだけ `mixed_operators: true` を付ける([[../../../../backend/nuts_calc_tex.py]] の `--mixed-operators` は2演算子必須)。3モードとも `command_type: 'ope', terms: 3, a_min: 1, a_max: 99, b_min: 1, b_max: 99`(オペランドレンジは変更前と同一。`result_max` は元々持たず、そのまま)。
- `examplesFor` をインライン `byChoice` 関数で付与した(`g1-three-terms` と同じ理由で `examplesByChoice` は使わない)。`addsub` は静的 `examples`(`['35+24-18', '46-15+22', '18+37-9']`)と同一。`sub` の例題(`['85-24-18', '76-15-22', '68-37-9']`)は途中結果がすべて正になる値を選定している(`evaluate_left_to_right` が引き算チェーンの各段を正に保つため生成自体は安全だが、フォールバック例題も同じ性質を満たすようオーサリングした)。
- `id`(`g2-addsub-mixed`)・`difficultyKey`(`difficulty_standard`)・`supportLevel`(`full`)・`latexOnly`(`true`)・string キー名は据え置き、`strings.ja.json` 側で `menu_g2_addsub_mixed_title` を「3つの数の足し引き」へ改称した([[./strings.ja.json]] 参照)。
- この項目も `terms: 3` を常に送るため live プレビュー対象で、`presetDetail.js` の変更は不要(#310 で multi-term の `operands[]/operators[]` 形状に対応済み、[[./presetDetail.js]] 参照)。

### 4年生「整数と小数の掛け算」の乗数オプション3値化(issue #313)

`g4-decimal-mul-int`(multiplication カテゴリ)を改称・拡張した。変更前は `titleKey: 'menu_g4_decimal_mul_int_title'`(文言「小数×整数」)+ `settings: [fixedSetting('multiplier', 'setting_multiplier_label', 'setting_option_integer'), displayFormatSetting()]`(非活性の「乗数:整数」固定表示)+ 引数を無視する `buildParams: (state) => ({ command_type: 'ope', operator: ['mul'], a_digits: 2, b_digits: 1, a_decimal_places: 1, ...displayFormatParam(state) })` で、常に「小数(第1位)× 整数」の1形態のみを出していた。

- `strings.ja.json` 側で `menu_g4_decimal_mul_int_title` を「整数と小数の掛け算」へ、desc/point も「かける順番は『整数×小数』『小数×整数』『まぜる』から選べる」旨へ改訂した([[./strings.ja.json]] 参照)。`id`/`descKey`/`pointKey`/`difficultyKey`/`supportLevel`(`full`)/`latexOnly`(`true`)は据え置き。`id` を変えないため `DISPLAY_FORMAT_ITEM_IDS`(前述「出題形式(式/筆算)設定」)の18項目列挙も無変更。
- 固定設定を `id: 'factorOrder'` の choice へ置き換えた。option は `DECIMAL_FACTOR_ORDER_OPTIONS`(`drillPresets.js:742-751` 付近)= `int_decimal`(`setting_option_int_times_decimal`「整数×小数」)/ `decimal_int`(`setting_option_decimal_times_int`「小数×整数」)/ `mixed`(`setting_option_mixed`「まぜる」、`hintKey: 'setting_mixed_hint'`)の3値、既定 `'mixed'`。`displayFormatSetting()` は第2設定として残す。
- `buildParams(state)` は `state?.factorOrder ?? 'mixed'` で分岐する。`base = { command_type: 'ope', operator: ['mul'], ...displayFormatParam(state) }` を共通にし:
    - `int_decimal` → `{ ...base, a_digits: 1, b_digits: 2, b_decimal_places: 1 }`(第1因数=整数1桁、第2因数=小数第1位2桁)。
    - `decimal_int` → `{ ...base, a_digits: 2, b_digits: 1, a_decimal_places: 1 }`(#313 以前と同一。第1因数=小数第1位)。
    - `mixed`(既定) → `{ ...base, a_digits: 2, b_digits: 1, a_decimal_places: 1, mixed_decimal_operand_order: true }`。`decimal_int` と同じ非対称 decimal-places 指定に `mixed_decimal_operand_order: true` を足すことで、`nuts_calc_tex.py` が問題ごとにどちらの因数へ小数点を置くかをランダムに入れ替える(1枚のプリントに「小数×整数」と「整数×小数」が混在)。乗算は可換なので積は不変。[[../../../../backend/nuts_calc_tex.py]] の `### ope --a-decimal-places/--b-decimal-places` と [[../../../../backend/renderers.py]] 参照。
- `mixed` は live preview 対象(`command_type === 'ope'` かつ `use_parentheses`/`missing_value` 無し)であり、`presetDetail.js` はリクエストボディに `...params` を展開するため `mixed_decimal_operand_order: true` が `POST /generate-problems` へも届く(`presetDetail.js` 側の変更は不要、[[./presetDetail.js]] 参照)。
- `examplesFor` を `examplesByChoice(['factorOrder'], { int_decimal: ['7×3.6','4×2.35','3×5.8'], decimal_int: ['3.6×7','2.35×4','5.8×3'], mixed: ['3.6×7','4×2.35','5.8×3'] })` で付与し、静的 `examples` を `mixed` キーと同じ `['3.6×7','4×2.35','5.8×3']` にした(`examplesByChoice` 規約どおり既定値キー = 静的配列)。

### 5年生「整数と小数の割り算」の被除数オプション3値化(issue #317)

`g5-decimal-div`(division カテゴリ)を改称・拡張した。変更前は `titleKey: 'menu_g5_decimal_div_title'`(文言「小数÷小数」)+ `settings: [fixedSetting('divisor', 'setting_divisor_label', 'setting_option_decimal')]`(非活性の「除数:小数」固定表示)+ 引数を無視する `buildParams: () => ({ command_type: 'ope', operator: ['div'], a_digits: 2, b_digits: 2, a_decimal_places: 1, b_decimal_places: 1 })` で、常に「小数(第1位)÷ 小数(第1位)= 整数」の1形態のみを出していた。

- `strings.ja.json` 側で `menu_g5_decimal_div_title` を「整数と小数の割り算」へ、desc/point も「わる数が小数、わられる数は『整数÷小数』『小数÷小数』『まぜる』から選べる。答えは割り切れる整数」旨へ改訂した([[./strings.ja.json]] 参照)。`id`/`descKey`/`pointKey`/`difficultyKey`(`difficulty_standard`)/`supportLevel`(`full`)/`latexOnly`(`true`)は据え置き。この項目は `DISPLAY_FORMAT_ITEM_IDS`(前述「出題形式(式/筆算)設定」)に元々含まれない(#180 で保留中)ため無変更。
- 固定設定を `id: 'dividendType'` の choice へ置き換えた。option は `DIVIDEND_TYPE_OPTIONS`(`drillPresets.js` の grade5 直前)= `integer_div_decimal`(`setting_option_integer_div_decimal`「整数÷小数」)/ `decimal_div_decimal`(`setting_option_decimal_div_decimal`「小数÷小数」)/ `mixed`(`setting_option_mixed`「まぜる」、`hintKey: 'setting_mixed_hint'`)の3値、既定 `'mixed'`。
- `buildParams(state)` は `state?.dividendType ?? 'mixed'` で分岐する。`base = { command_type: 'ope', operator: ['div'], a_digits: 2, b_digits: 2, b_decimal_places: 1 }` を共通にし:
    - `integer_div_decimal` → `{ ...base, a_decimal_places: 0, dividend_mode: 'integer' }`(被除数=整数、除数=小数第1位、商=整数)。
    - `decimal_div_decimal` → `{ ...base, a_decimal_places: 1 }`(#317 以前と同一。`dividend_mode` を送らない)。
    - `mixed`(既定) → `{ ...base, a_decimal_places: 1, dividend_mode: 'mixed' }`。`nuts_calc_tex.py` が問題ごとに整数被除数 / 小数被除数を抽選する(1枚のプリントに「整数÷小数」と「小数÷小数」が混在)。除数は常に小数。学習指導要領が「除数を整数にして計算」を教え、導入は商が整数であることに合わせた。[[../../../../backend/nuts_calc_tex.py]] の `### ope --a-decimal-places/--b-decimal-places` と [[../../../../backend/renderers.py]] 参照。
- live preview 対象(`command_type === 'ope'` かつ `use_parentheses`/`missing_value` 無し)であり、`presetDetail.js` はリクエストボディに `...params` を展開するため `dividend_mode` が `POST /generate-problems` へも届く(`presetDetail.js` 側の変更は不要、[[./presetDetail.js]] 参照)。
- `examplesFor` を `examplesByChoice(['dividendType'], { integer_div_decimal: ['72÷1.8','96÷2.4','51÷1.7'], decimal_div_decimal: ['7.2÷1.8','9.6÷2.4','8.4÷1.2'], mixed: ['72÷1.8','7.2÷1.8','96÷2.4'] })` で付与し、静的 `examples` を `mixed` キーと同じ `['72÷1.8','7.2÷1.8','96÷2.4']` にした(`examplesByChoice` 規約どおり既定値キー = 静的配列)。

### 選択肢ヒント(`hintKey`)の汎用化

旧実装は「値が `'mixed'` の設定は `setting_mixed_hint` を表示する」というハードコードだった。issue #132 でこれを `option.hintKey` ベースの汎用機構へ置き換え、`OPT_MIXED`(`carrySetting`/`remainderSetting`/`REDUCTION_OPTIONS` が共有)および `dan`/`NUMBER_KIND_OPTIONS`/`DENOMINATOR_CHOICE_OPTIONS` それぞれの独立した `'mixed'` オプションリテラル(計4箇所)に `hintKey: 'setting_mixed_hint'` を付与した。表示文言・表示条件(該当オプションが選択されているとき)は旧実装と同一で、挙動の変更はない。

### 選択中の設定に応じた例題切り替え(`examplesFor`/`examplesByChoice`、issue #135)

`presetDetail.js` の設定画面は元々 `item.examples`(静的配列)を常に表示していたが、issue #135 で選択中の設定を反映するよう変更した。バックエンドから実際の問題文をリアルタイム取得する仕組みは存在しない(`POST /generate-pdf` は PDF しか返さない)ため、静的にオーサリングした例題文字列を選択状態に応じて出し分ける方式を採用した。動的化そのものは別issue(#137 親、#138 backend API 新設、#139 frontend/web 動的プレビュー)へ切り出し済み。

汎用ヘルパー `examplesByChoice(settingIds, byCombo)`(`drillPresets.js:66-72`)は、`settingIds`(例: `['carryMode']`、複数設定なら `['denominator', 'numberKind']`)の現在値を `_` 結合したキーで `byCombo` を引く `examplesFor(settingsState)` を返す。全設定が既定値 `'mixed'` のときのキー(単一なら `'mixed'`、複数なら `'mixed_mixed'` 等)は `byCombo` に必ず存在させる規約とし、未知の値・未設定のフォールバック先にも使う。これにより、既定状態(`state.settingsState` が全設定のデフォルト値)での `examplesFor()` の出力は必ず元の静的 `examples` と一致する(`drillPresets.test.js` の `examplesFor(defaultState) matches the static examples array` で保証)。

`carryMode`/`remainderMode`/`denominator`/`numberKind`/`reduction`/`dan` を **choice型**で持つ25項目(issue #305 で `g1-add-20`、issue #307 で `g1-sub-20` が固定→choice 化され順次追加)、および issue #309 で `operators` の3値化に伴い `g1-three-terms` に、issue #311 で同じく `operators` を choice 化した `g2-addsub-mixed` に `examplesFor` を付与した(それ以外の `fixed`型でしか持たない項目は対象外で、静的 `examples` のまま)。`supportLevel: 'partial'` な項目(小数の carry/borrow 系)は `buildParams` が実際には該当設定を無視するため、`examplesFor` が返す内容は「その設定を選ぶとどんな問題を意味するか」を示す説明用であり、実際に生成される PDF の内容と一致する保証はない(該当箇所にコメントで明記)。6年生の reduction 系(6項目)は issue #114 で `full` に引き上げ済みのため、この注記は現在対象外(`reducible_mode` が実際に backend へ渡り、選択どおりの問題が生成される)。

### 出題形式(式/筆算)設定(issue #134)

`displayFormatSetting()`/`displayFormatParam(state)`(`drillPresets.js:68-82` 付近)は、`carrySetting`/`carryModeField` と同じヘルパーパターンで「出題形式」(選択肢: 式/筆算、既定 `'horizontal'`)設定を追加する。`displayFormatParam(state)` は `'written'` 選択時のみ `{ vertical: true }` を返し(`nuts_calc_tex.py` の `--vertical`)、それ以外は `{}`(何も配線しない)。

対象は次の18項目に限定し、機械的な「`--vertical` と併用可能かどうか」の判定だけで対象範囲を決めていない(ユーザー指示による明示的な列挙): `g2-add-2digit`/`g2-add-result-1000`/`g2-sub-2digit`/`g2-sub-result-1000`/`g3-add-result-10000`/`g3-decimal-addsub`/`g3-sub-result-10000`/`g3-decimal-sub`/`g3-mul-2x1`/`g3-mul-3x1`/`g3-mul-2x2`/`g4-decimal-add`/`g4-decimal-sub`/`g4-decimal-mul-int`/`g4-div-1digit`/`g4-div-2digit`/`g4-decimal-div-int`/`g5-decimal-mul`(`drillPresets.test.js` の `DISPLAY_FORMAT_ITEM_IDS` で厳密に一致検証)。全項目が無条件で `command_type: 'ope'` を返すため(`--vertical` は `ope` コマンドのみ実装、[[../../../../backend/nuts_calc_tex.py]] 参照)、`disabledWhen`/`resolveValue` は不要。

同じく `g5-decimal-div`(issue #317 で「小数÷小数」から「整数と小数の割り算」へ改称)は対象から除外した。vendor済み `longdivision` パッケージの `\intlongdivision` が整数の除数しか受け付けないため、除数の小数点をシフトして整数化する回避策(教科書的な標準手法)を検討したが、「出題形式:筆算のときも式と同じ数値表現である必要がある」というユーザー方針により不採用、issue #180(agenda)で対応方針を検討中(実装は保留)。

### 九九(`g2-kuku`)の段選択

「1〜9の段」選択時は `command_type: '99'`(`a_value` に段を指定)、「まぜる」選択時は `command_type: 'ope', operator: ['mul']`(`a_min`/`a_max`/`b_min`/`b_max` を1〜9のランダム)に切り替える。固定段には「出題順序」(`ascending`/`descending`/`random`)があり、それぞれフラグなし/`descend: true`/`shuffle: true` に変換する。「まぜる」では全ての順序選択肢を表示したまま非活性化し、`resolveValue` で `random` を選択表示する。実際の生成は従来通り `ope` の両オペランドランダムであり、保持中の `questionOrder` 値には依存しない(`frontend/web/src/drillPresets.js:220-277`)。例題も固定段では選択順序に応じて先頭2問相当へ切り替える(`frontend/web/src/drillPresets.js:225-235`)。

### 2年生「100までの足し算」の答え上限(issue #176)

`g2-add-2digit`(基礎、「100までの足し算」)はタイトルが答え≤100を示唆するが、修正前の `buildParams` はオペランド範囲(`a_min:1, a_max:99, b_min:1, b_max:99`)のみを制約しており、答え(2桁+2桁の和)は最大198まで生成され得た。全 `examples`/`examplesFor` の値はいずれも実際には答え100以下(例: `34+5=39`, `48+37=85`)で、タイトル・現行desc/pointKey・既存キュレーション済み例題はすべて「答え≤100」の意図で一致していたため、`g2-add-result-1000` と同じ `result_max`(結果上限。前セクション参照)パターンをこの基礎項目にも適用し `result_max: 100` を追加した(`frontend/web/src/drillPresets.js:207-211`)。オペランド範囲・タイトル・descは変更していない。`docs/uiux/calculation_drill_menu_parameters_v1.md` は当初この項目を「2桁までの足し算」と記載していたが、2026-08-19 の `/init-docs` で「100までの足し算」(`固定値・表示`に「答え：100まで」を追加)へ修正し、現行文言と一致させた。

対称項目 `g2-sub-2digit`(「100までの引き算」)は `a_max` (最小値からの引き算)が99以下のため、答えは構造上常に100未満になり、当初の答え上限バグはなかった。ただし issue #176 の追加調査で「Nまでの」系12項目のうち `result_max` を持たない7項目を洗い出し、うち小数第1位系2項目(`g3-decimal-addsub`/`g3-decimal-sub`、「まで」が桁数を指し無関係)を除く5項目(`g1-add-10`/`g1-add-20`/`g1-sub-10`/`g1-sub-20`/`g2-sub-2digit`)は、答えの上限がオペランド範囲や `carry_mode` の組み合わせからのみ暗黙に導かれ、コードを読むだけでは上限値が読み取れない状態だった。数学的には非拘束(生成される値の実測範囲を変えない)だが、`g2-sub-result-1000`/`g3-sub-result-10000` が既に採用している「対称性のため明示する」方針を踏襲し、この5項目にも自己文書化目的で `result_max` をそれぞれのタイトル上限値(`10`/`20`/`10`/`20`/`100`)で追加した。これにより「Nまでの」12項目のうち10項目が `result_max` で答え上限を明示し、残り2項目(decimal系)は意味論的に対象外であることが明確になった。

なお `g1-add-20` はその後 issue #305 で、`g1-sub-20` は issue #307 で繰り上がり/繰り下がり設定が選択可能になり、`buildParams` がモードでオペランドレンジを切り替えるようになったが、`result_max: 20` は全モードで維持している。`g1-sub-10` も issue #307 で `carry_mode: 'none'` を明示するようになったが `result_max: 10` は不変(前述「1年生の足し算の繰り上がり設定(issue #305)」「1年生の引き算の繰り下がり設定(issue #307)」参照)。

### 2年生「1,000までの足し算」「1,000までの引き算」

`g2-add-result-1000` は2年生の addition カテゴリに置く発展項目で、1〜999の両オペランド範囲を保ったまま `result_max: 1000` を送る。単に各オペランドを500以下へ狭める方式では `999+1` のような有効問題を失うため、レンダラー共通の結果上限を利用する。既存の「100までの足し算」と同じ繰り上がり設定・動的例題を持ち、LaTeX専用 `carry_mode`/`result_max` を使うため `latexOnly: true` とする(`frontend/web/src/drillPresets.js:182-223`)。タイトル文言は issue #161 で「答えが1,000までの足し算」から「1,000までの足し算」へ短縮した(desc は「答えが1,000までになる、…」のまま変更なし)。

`g2-sub-result-1000`(issue #154)は subtraction カテゴリの対称項目で、同じ `a_min:1, a_max:999, b_min:1, b_max:999, result_max: 1000` を送る。`calc_sub` は常に `a - b > 0` になるまでリトライするため、この演算子では `result_max` は算術上非拘束(最大でも `999-1=998<1000`)だが、足し算エントリと自己文書的に対称な形を保つため明示的に付与している。設定は「100までの引き算」と同じ `carrySetting('setting_borrow_label')` を使う(`frontend/web/src/drillPresets.js:224-265`)。タイトルも同様に「1,000までの引き算」へ短縮した(issue #161)。

### 3年生の足し算/引き算・分数の再構成、四則混合の新設(issue #161)

3年生の「3桁までの足し算/引き算」「4桁までの足し算/引き算」(桁数でオペランドを制限する方式)を廃止し、2年生の `result_max` パターンを踏襲した発展項目 `g3-add-result-10000`/`g3-sub-result-10000` に置き換えた(`a_min:1, a_max:9999, b_min:1, b_max:9999, result_max: 10000`、`frontend/web/src/drillPresets.js:368-387,430-449`)。減算側は2年生と同じ理由で `result_max` が算術上非拘束(最大でも `9999-1=9998<10000`)だが、対称性のため明示している。

3年生の `fraction` カテゴリ(`g3-fraction-add`/`g3-fraction-sub` の2項目のみで構成)を撤廃し、両項目を内容無変更のまま `addition`/`subtraction` 配列の末尾へ移動した(`frontend/web/src/drillPresets.js:413-427,472-486`)。カテゴリキーは `drillCatalog.js` の分類ロジックに影響しないため、この移動によるカタログ絞り込み・`operationGroup`/`numberType` への影響はない(4〜6年生の `fraction` カテゴリは対象外で変更なし)。

このブランチが main から分岐した後に issue #157/#160(全項目への `pointKey` 必須化)が main へ先に merge されたため、`g3-add-result-10000`/`g3-sub-result-10000`/`g3-addsub-mixed-result-1000`/`g3-parentheses-mul-result-1000` の4新規項目には `pointKey` と対応する `strings.ja.json` の文言を追加で用意し、`g3-fraction-add`/`g3-fraction-sub` は main 側で追加された既存の `pointKey`(`menu_g3_fraction_add_point`/`menu_g3_fraction_sub_point`)を維持したまま移動した(マージコンフリクト解消、`frontend/web/src/drillPresets.js` 全体で issue #161 と #157/#160 の変更を統合)。

3年生に新設した `four-operations` カテゴリ(`frontend/web/src/drillPresets.js:558-592`)は2項目を持つ:
- `g3-addsub-mixed-result-1000`: 加減算のみの3項混合(`terms:3, mixed_operators:true`)で `a_min:1, a_max:999, b_min:1, b_max:999, result_max: 1000`。2年生の対応項目(`g2-addsub-mixed`、issue #311 で「3つの数の足し引き」へ改称・演算モード選択化)と異なり `result_max` を持ち、演算モードは足し引き混合固定(掛け算は含まない)。
- `g3-parentheses-mul-result-1000`: 加減乗の3項混合に `use_parentheses: true` を加え、掛け算オペランドを2桁までに揃えるため `a_min:1, a_max:99, b_min:1, b_max:99`(2年生の `g2-parentheses` と同様に `a_min`/`a_max` 形式を使う。4年生の `g4-parentheses` が使う `a_digits`/`b_digits` 形式とは異なる)、`result_max: 1000` で答えの上限も揃える。

`catalog.js` の `CATEGORY_ORDER` は既に `four-operations` を `fraction` の直後(実質最後尾側)に固定しているため、3年生に `four-operations` カテゴリキーを追加するだけで学年ページ最下部にセクションが自動的に現れる(`catalog.js` 自体は無変更)。

### 4年生の分数カテゴリ撤廃(issue #315)

issue #161 の3年生と同じ再編を4年生にも適用した。4年生の `fraction` カテゴリ(`g4-fraction-add`/`g4-fraction-sub` の2項目のみで構成)を撤廃し、両項目を内容無変更のまま `addition`/`subtraction` 配列の末尾へ移動した(`g4-fraction-add` は `g4-decimal-add` の後、`g4-fraction-sub` は `g4-decimal-sub` の後)。`id`/`titleKey`/`descKey`/`pointKey`/`settings`/`buildParams`/`examplesFor`、`g4-fraction-sub` の `proper_result` 判定コメントを含め一切変更していない。

カテゴリキーは学年ページのセクション見出し順序付け(`catalog.js` の `CATEGORY_ORDER`)にのみ使われ、削除済み `drillCatalog.js` の分類ロジック(`operationGroup`/`numberType`)には影響しない。よってこの移動によるカタログ絞り込みへの影響はない(#161 と同じ理屈)。`catalog.js` の `CATEGORY_ORDER` と `strings.ja.json` の `category_fraction` は5・6年生が引き続き `fraction` カテゴリを使うため無変更。`drillPresets.test.js` に3年生と対称な「grade 4 fraction items live under addition/subtraction」テストを追加した。

### `ope` プリセットの桁数指定が `a_value`/`b_value` から `a_digits`/`b_digits` へ移行した理由(issue #230)

`backend/nuts_calc_tex.py` の `-a/--a-value` は、`ope`(と `100`/`lcm`/`gcd`/`divfrac`)では「桁数」、`99`/`squ`/`pi` では「値そのもの」という2つの異なる意味をコマンドによって切り替えて解釈していた。この単一パラメータへの意味の二重化を根本的に解消するため、issue #230 で `ope`/`100`/`lcm`/`gcd`/`divfrac` 専用の新フィールド `a_digits`/`b_digits` を新設し、`a_value`/`b_value` はこれらのコマンドで一切読まれなくなった(`docs/L3_implementation/backend/nuts_calc_tex.py.md` の該当セクション参照)。これに伴い、`ope` の桁数ショートハンドを使っていた13箇所のプリセット(`g3-decimal-addsub`/`g3-decimal-sub`/`g3-mul-2x1`/`g3-mul-3x1`/`g3-mul-2x2`/`g4-decimal-div-int`/`g4-decimal-add`/`g4-decimal-sub`/`g4-decimal-mul-int`/`g4-four-operations`/`g4-parentheses`/`g5-decimal-mul`/`g5-decimal-div`)を `a_value`/`b_value` から `a_digits`/`b_digits` へ機械的に置き換えた(値そのものは無変更)。`99`(`g2-kuku`)/`squ` プリセットの `a_value` は値そのものの意味のままなので無変更。`lcm`/`gcd`/`divfrac` プリセットはこの移行以前から `a_min`/`a_max`(明示レンジ)を直接指定しており対象外だった。

### ドキュメントにない既存機能の扱い(written/examPrep/missing-value)

`docs/uiux/calculation_drill_menu_parameters_v1.md` に定義がない、以下の旧機能は #98 でデータモデルから削除した(ユーザー承認済み):
- 筆算(縦書き/`--vertical`)形式のペアリング(`written` バケット)。
- 中学受験対策(examPrep、27プリセット)。
- 虫食い算(`--missing-value`)。

いずれも当時併存していた `frontend/spa` および CLI では引き続き利用可能だった(`frontend/spa` 自体は issue #233 で削除され、以後 CLI のみで利用可能)。復活させるかどうかは issue #111 で後日判断する。筆算(縦書き)形式については、issue #133(親)配下の #134 が「出題形式(式/筆算)」設定として `frontend/web` へ個別設定の形で再導入した(#111 の筆算部分をこちらで解決する位置づけ、対象18項目は前述の「出題形式(式/筆算)設定(issue #134)」セクション参照。`g5-decimal-div` は #180 で保留)。

## 統合ポイント

- 呼び出し元: `catalog.js`/`preset.js`(`GRADES`/`UNGRADED`/`presetsByGrade` を直接消費)、`presetDetail.js`(`item.examplesFor`/`item.examples` を `selectExamples()` 経由で参照、`item.pointKey` をヘッダーdescriptionとして参照、[[./presetDetail.js]] 参照)。
- 呼び出し先: なし(データ定義のみ)。

## 注意事項・既知の制限

- `frontend/spa/src/drillPresets.js` とはもはや無関係だった(#98 で分岐)。`frontend/spa` 自体が issue #233 で削除されたため、この分岐関係自体が過去のものになった。
- `settings`/`buildParams`/`examplesFor` を実際にユーザーが切り替える UI は `presetDetail.js`(`preset.html`)が実装している([[./presetDetail.js]] 参照)。

## 変更履歴（git log より自動生成）

- ba08963 feat(#317): add integer/decimal dividend selection to grade 5 decimal division
- 697db43 refactor(#315): move grade 4 fraction add/sub into addition/subtraction categories (#316)
- 40dfb0a feat(#313): add mixed decimal operand order to grade 4 integer/decimal multiplication (#314)
- 7334a3a feat(#311): rename grade 2 three-term drill and add operator-mode selection (#312)
- 3278705 feat(#309): add subtraction-only mode to grade 1 three-term drill (#310)
- 571563e feat(#307): add borrow-mode settings to grade 1 subtraction drills (#308)
- 2f6add1 feat(#305): add carry-mode settings to grade 1 addition drills (#306)
- a4104ca feat(#303): render fixed drill settings as an inactive segmented control (#304)
- 37a5a80 #230 Split a_value/b_value's overloaded digit-count/direct-value semantics into a_digits/b_digits (#236)
- 231bde1 #134 frontend/web: add 出題形式 (式/筆算) setting to add/sub/mul/div preset detail pages (#181)
