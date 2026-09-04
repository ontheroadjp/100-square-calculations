# `frontend/web/src/drillPresets.js`

## 目的・役割

`docs/uiux/calculation_drill_menu_parameters_v1.md` に定義された学年別ドリルメニューを、grade → category → menu-item の階層データとして保持する。`POST /generate-pdf` へのリクエストパラメータへのマッピングを担う純粋な ES module で、React・i18next に依存しない(issue #98)。issue #88 時点では `frontend/spa/src/drillPresets.js` の単純コピーだったが、#98 で `frontend/web` 専用の新データモデルへ全面的に書き換えられ、両ファイルの内容は完全に分岐した(以後、追従コピー関係はない)。

## 動作の概要

`GRADES`(`[1,2,3,4,5,6]`)・`UNGRADED`(`'ungraded'`)・`presetsByGrade` を export する。`presetsByGrade[grade]` は `{ <categoryId>: menuItem[] }` の形で、`categoryId` は `review`/`addition`/`subtraction`/`multiplication`/`division`/`decimal`/`fraction`/`four-operations`/`number-sense` のいずれか(該当する学年にのみ出現)。`review`(総合問題)は3年生専用の試作で、その学年の複数単元を1枚に混ぜるワークシート(issue #140、下記セクション参照)。`decimal` は5年生専用で、`multiplication`/`division` カテゴリを廃止した代わりに小数×小数・整数と小数の割り算をまとめる(issue #320、下記セクション参照)。`fraction` は3年生(issue #161で撤廃)・4年生(issue #315で撤廃)を除く5〜6年生に残る。カテゴリキーは `catalog.js` の固定 `CATEGORY_ORDER`(`review, addition, subtraction, multiplication, division, decimal, fraction, four-operations, number-sense`)による学年ページのセクション見出し順序付けにのみ使われ、`drillCatalog.js` の絞り込み分類(`numberType`/`operationGroup`)には影響しない(`Object.values(categories)` でカテゴリキーを捨ててフラット化するため)。

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
- 5年生の分数×整数・分数÷整数(2項目、issue #327 で6年生から移設)と6年生の整数×分数・分数×分数・整数÷分数・分数÷分数(4項目)の計6項目は、issue #114 で `nuts_calc_tex.py` に `--require-reducible`/`--no-reducible`/`--mixed-reducible` が追加されたことに伴い `full` へ引き上げ済み。詳細は下記「約分制御(#114)対応」を参照。

`partial` の項目も `settings` にはドキュメント通りの選択肢を全て含める(将来 backend 側の issue が閉じた際、データモデルの再設計なしに `supportLevel` を `full` へ引き上げられるようにするため)。

### 帯分数(#112)対応: `fractionFormParams`/`proper_result` の連動

`NUMBER_KIND_OPTIONS`(`fraction`/`mixedNumber`/`mixed`、docs の「数の種類: 分数/帯分数を含む/まぜる」)を `fraction: {} / mixedNumber: {a,b}_fraction_form='mixed' / mixed: {a,b}_fraction_form='mix'` へ変換する `fractionFormParams(state)` ヘルパーを新設した。`numberKind` 未選択時の既定は `'mixed'`(=「まぜる」)で、これは backend の `--a-fraction-form mix --b-fraction-form mix` が a/b を独立抽選する挙動と一致する(`compare` コマンドの `--a-fraction-form`/`--b-fraction-form` と同じ設計、[[../../../../backend/nuts_calc_tex.py]] の該当セクション参照)。

`g4-fraction-sub`/`g5-fraction-sub` の `proper_result`(答え<1を要求)は `numberKind === 'fraction'` のときだけ真にする。帯分数を含む繰り下がりの答えは1以上になりうる(docs の例 `3 2/5-1 4/5=1 3/5`)ため、`proper_result: true` を無条件のままにすると帯分数繰り下がりドリルが成立しない。

### 約分制御(#114)対応: `reducibleModeParam`

5年生の分数×整数(`g5-fraction-mul-int`)・分数÷整数(`g5-fraction-div-int`)と6年生の整数×分数(`g6-int-mul-fraction`)・分数×分数(`g6-fraction-mul`)・整数÷分数(`g6-int-div-fraction`)・分数÷分数(`g6-fraction-div`)の計6項目は、いずれも `id: 'reduction'` の choice 設定(`REDUCTION_OPTIONS` = なし/あり/まぜる、既定 `'mixed'`)を持つ。`reducibleModeParam(state)`(`state?.reduction ?? 'mixed'`)を各 `buildParams` の `reducible_mode` フィールドへそのまま渡す。分数×整数・分数÷整数の2項目は当初6年生にあったが、issue #327 で学習指導要領に合わせて5年生へ移設した(下記「分数×整数 / 分数÷整数 を6年生から5年生へ移設(issue #327)」参照)。

`--mixed-reducible` は `nuts_calc_tex.py` 側に `--mixed-carry-borrow` のような単一演算子制約がない(演算子1つだけの `frac -o mul`/`mixed -o div` 等でもそのまま有効)ため、`carryModeField` のように単一演算子時に `mixed` を省略する特例は不要で、`remainderModeParam` と同じ「常に値をそのまま送る」パターンを踏襲する(`drillPresets.js:56-63` 付近)。

分数×整数/分数÷整数/整数×分数/整数÷分数の4項目は `command_type: 'mixed'`(`a_kind`/`b_kind` を `fraction`/`int` の片方ずつに固定、`nuts_calc_tex.py` の `_init()` が要求する2項限定・fraction+int 限定の条件を満たす)、分数×分数/分数÷分数の2項目は `command_type: 'frac'`(`proper_operands: true` と併用)を使う。

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

### 1年生の「何十±何十」「2桁±1桁（繰り上がり・繰り下がりなし）」ドリル追加(issue #331)

学習指導要領解説 算数編 第1学年 A「加法及び減法」が「簡単な場合について，2位数などについても加法及び減法ができるようにする」として **何十±何十** と **2位数±1位数（繰り上がり・繰り下がりなし）** を挙げていることに対応し、`g1-add-20`/`g1-sub-20` と `g2-add-2digit`（筆算・繰り上がりあり）の間のギャップを埋めるドリルを4件追加した。`addition` は `[g1-add-10, g1-add-20, g1-add-tens, g1-add-100]`、`subtraction` は `[g1-sub-10, g1-sub-20, g1-sub-tens, g1-sub-100]` の順。難易度列はメニュー順ではなく「その学年で初めて学習するときの相対的な位置づけ」なので、基礎（`*-tens`）が標準（`g1-add-20`）の後に並んでいてよい。

- **`g1-add-tens` / `g1-sub-tens`（「何十のたし算/ひき算」、`difficulty_basic`）**: `buildParams()` は引数を取らず `{command_type:'ope', operator:['add'|'sub'], carry_mode:'none', a_min:10, a_max:90, b_min:10, b_max:90, a_multiple:10, b_multiple:10, result_max:100}` を返す。`a_multiple`/`b_multiple`（issue #331 で backend に新設した `--a-multiple`/`--b-multiple` の JSON キー）で両オペランドを10の倍数に、`carry_mode:'none'` で十の位も繰り上がらない範囲（和 ≤ 90 / 差 ≥ 0）に限定する。何十±何十 は plain `ope` の min/max レンジだけでは「10の倍数のみ」を表現できず（union にならない）、backend 変更なしでは分離不能だったため、reviewer 判断で本 issue のスコープに backend capability 追加を含めた（[[../../../../backend/nuts_calc_tex.py]] の `### ope --a-multiple/--b-multiple`）。
- **`g1-add-100` / `g1-sub-100`（「100までの足し算/引き算（くり上がりなし）」、`difficulty_standard`）**: `buildParams()` は `{command_type:'ope', operator:['add'|'sub'], carry_mode:'none', a_min:10, a_max:99, b_min:1, b_max:9, result_max:100}`。2桁±1桁で `carry_mode:'none'` + `b_max:9` により一の位が繰り上がらず、`a_min:10` で第1項は必ず2桁、結果は正の2桁。
- 4件とも `g1-add-10`/`g1-sub-10` と同じく非活性の `fixedSetting('carryMode', 'setting_carry_label'|'setting_borrow_label', 'setting_option_none', NONE_REQUIRED_MIXED_OPTIONS)` を1つだけ持ち、`examplesFor` は持たない（静的 `examples` のみ）。`supportLevel:'full'`、`latexOnly:true`。`result_max:100` は数学的には冗長だが issue #176 で確立した「Nまでの」系の自己文書化方針に従い明示する。
- live preview（`presetDetail.js` → `POST /generate-problems`）は `isLivePreviewSupported`（`command_type==='ope'` かつ `use_parentheses`/`missing_value` なし）で自動的に対象になり、`a_multiple`/`b_multiple` は [[../../../../backend/problem_generation.py]] がそのまま転送する。`presetDetail.js` 側の変更は不要。文言は [[./strings.ja.json]] に12キー追加。

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

### 4年生「小数×整数」は乗数が整数の場合のみ(issue #329、#313 の revert)

`g4-decimal-mul-int`(multiplication カテゴリ)は「小数(第1位)× 整数」の1形態のみを出す。学習指導要領解説 算数編 第4学年 A数と計算「小数」が扱うのは*乗数・除数が整数の場合*の小数の乗除法であり、乗数が小数になる場合(整数×小数・小数×小数)は第5学年「小数の乗法」の内容のため。5年生側は `g5-decimal-mul`(小数×小数)がカバーする。

- 設定: `settings: [fixedSetting('multiplier', 'setting_multiplier_label', 'setting_option_integer'), displayFormatSetting()]`。第1設定は非活性の「乗数：整数」固定ピル(兄弟 `g4-decimal-div-int` の「除数：整数」・`g5-decimal-mul` の「乗数：小数」と同じ形)。`displayFormatSetting()` を第2設定に持つため `DISPLAY_FORMAT_ITEM_IDS`(前述「出題形式(式/筆算)設定」)の19項目列挙に含まれ続ける。
- `buildParams(state)` は `state` を参照せず常に `{ command_type: 'ope', operator: ['mul'], a_digits: 2, b_digits: 1, a_decimal_places: 1, ...displayFormatParam(state) }` を返す(被乗数 `a` = 小数第1位、乗数 `b` = 整数)。`displayFormat: 'written'` のときのみ `vertical: true` が加わる。
- `examples` は `['3.6×7', '2.35×4', '5.8×3']`(すべて小数×整数)。設定に選択肢がないため `examplesFor` は持たない。
- `strings.ja.json`: `menu_g4_decimal_mul_int_title` =「小数×整数」、desc =「小数に整数を掛ける計算を練習します。」、point =「小数×整数の計算です。答えの小数点をどこに打つかがポイントになります。」([[./strings.ja.json]] 参照)。
- 経緯: issue #313/#314 で `id: 'factorOrder'` の choice(`int_decimal`/`decimal_int`/`mixed`、既定 `mixed`)と `DECIMAL_FACTOR_ORDER_OPTIONS` 定数、`mixed_decimal_operand_order` フラグ配線、`examplesByChoice(['factorOrder'], …)` を追加し、既定で乗数が小数になる問題(整数×小数・両順混在)を出していた。これが第4学年の範囲(乗数=整数)を超過していたため issue #329 で choice・定数・フラグ・`examplesFor` をすべて撤去し #313 以前の単一固定形態へ戻した。撤去に伴い `strings.ja.json` の `setting_option_int_times_decimal`/`setting_option_decimal_times_int` も他に参照がなくなり削除した。

### 5年生の小数カテゴリ新設、かけ算/わり算カテゴリ廃止(issue #320)

5年生の `multiplication` カテゴリ(`g5-decimal-mul` = 小数×小数 の1項目のみ)と `division` カテゴリ(`g5-decimal-div` = 整数と小数の割り算 の1項目のみ)を廃止し、両項目を内容無変更のまま新設の `decimal` カテゴリ(この順)へ移した。`decimal` は `presetsByGrade[5]` のオブジェクトキー順で `four-operations` より前に置くが、実際のセクション表示順は `CATEGORY_ORDER` が `'decimal'` を `'fraction'` の直前に固定するため「小数 → 分数 → 四則混合 → 数の性質・九九」になる。

- 5年生の算数は小数の乗除が中心のため、汎用の「かけ算」「わり算」見出しに単発の小数ドリルを分散させず、専用の「小数」見出し(`strings.ja.json` の `category_decimal` = 「小数」)にまとめる方針。`g5-decimal-mul`/`g5-decimal-div` の `id`/`titleKey`/`descKey`/`pointKey`/`settings`/`buildParams`/`examplesFor` は一切変更していない(カテゴリキーの移動のみ)。
- 小数の四則混合計算(`g5-decimal-four-ops`)は従来どおり `four-operations` カテゴリ(表示名「四則混合」)に残す。
- `multiplication`/`division`/`fraction` カテゴリキーは2〜4年生・6年生が引き続き使うため `CATEGORY_ORDER`・`KNOWN_CATEGORIES`・`strings.ja.json` の該当ラベルからは削除しない。`decimal` は現状5年生でしか使われないが、`CATEGORY_ORDER` に恒久追加した。
- `drillPresets.test.js` に「grade 5 groups ... under a dedicated decimal category」テストを追加し、issue #317 の被除数テストの参照を `presetsByGrade[5].division` → `presetsByGrade[5].decimal` へ更新した([[./drillPresets.test.js]] 参照)。`catalog.js`/`pcMakeFlow.js` は `CATEGORY_ORDER` 配列に `'decimal'` を1語足すだけの変更([[./catalog.js]]/[[./pcMakeFlow.js]] 参照)。

### 5年生「整数と小数の割り算」の被除数オプション3値化(issue #317)

`g5-decimal-div`(issue #320 以降は `decimal` カテゴリ、#320 以前は `division` カテゴリ)を改称・拡張した。変更前は `titleKey: 'menu_g5_decimal_div_title'`(文言「小数÷小数」)+ `settings: [fixedSetting('divisor', 'setting_divisor_label', 'setting_option_decimal')]`(非活性の「除数:小数」固定表示)+ 引数を無視する `buildParams: () => ({ command_type: 'ope', operator: ['div'], a_digits: 2, b_digits: 2, a_decimal_places: 1, b_decimal_places: 1 })` で、常に「小数(第1位)÷ 小数(第1位)= 整数」の1形態のみを出していた。

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

`carryMode`/`remainderMode`/`denominator`/`numberKind`/`reduction`/`dan` を **choice型**で持つ25項目(issue #305 で `g1-add-20`、issue #307 で `g1-sub-20` が固定→choice 化され順次追加)、および issue #309 で `operators` の3値化に伴い `g1-three-terms` に、issue #311 で同じく `operators` を choice 化した `g2-addsub-mixed` に `examplesFor` を付与した(それ以外の `fixed`型でしか持たない項目は対象外で、静的 `examples` のまま)。`supportLevel: 'partial'` な項目(小数の carry/borrow 系)は `buildParams` が実際には該当設定を無視するため、`examplesFor` が返す内容は「その設定を選ぶとどんな問題を意味するか」を示す説明用であり、実際に生成される PDF の内容と一致する保証はない(該当箇所にコメントで明記)。分数の reduction 系(計6項目、5年生の `g5-fraction-mul-int`/`g5-fraction-div-int` + 6年生の4項目)は issue #114 で `full` に引き上げ済みのため、この注記は現在対象外(`reducible_mode` が実際に backend へ渡り、選択どおりの問題が生成される)。

### 出題形式(式/筆算)設定(issue #134)

`displayFormatSetting()`/`displayFormatParam(state)`(`drillPresets.js:68-82` 付近)は、`carrySetting`/`carryModeField` と同じヘルパーパターンで「出題形式」(選択肢: 式/筆算、既定 `'horizontal'`)設定を追加する。`displayFormatParam(state)` は `'written'` 選択時のみ `{ vertical: true }` を返し(`nuts_calc_tex.py` の `--vertical`)、それ以外は `{}`(何も配線しない)。

`displayFormatSetting(disabledWhen)`(issue #349)は任意で述語 `disabledWhen(state)` を受け取り、渡されたときは `disabledWhen` と `resolveValue`(無効時 `'horizontal'` に解決)を設定へ足す。`presetDetail.js` の汎用 `isSettingDisabled`/`resolveSettingValue` がこれを解釈する(`g2-kuku` の `dan`→`questionOrder` と同じ仕組み)。

対象は次の19項目に限定し、機械的な「`--vertical` と併用可能かどうか」の判定だけで対象範囲を決めていない(ユーザー指示による明示的な列挙): `g2-add-2digit`/`g2-add-result-1000`/`g2-sub-2digit`/`g2-sub-result-1000`/`g3-add-result-10000`/`g3-decimal-addsub`/`g3-sub-result-10000`/`g3-decimal-sub`/`g3-mul-2x1`/`g3-mul-3x1`/`g3-mul-2x2`/`g3-mul-3x2`/`g4-decimal-add`/`g4-decimal-sub`/`g4-decimal-mul-int`/`g4-div-1digit`/`g4-div-2digit`/`g4-decimal-div-int`/`g5-decimal-mul`(`drillPresets.test.js` の `DISPLAY_FORMAT_ITEM_IDS` で厳密に一致検証)。ほとんどの項目は無条件で `command_type: 'ope'` を返すため `disabledWhen`/`resolveValue` は不要だが、**`g4-decimal-div-int` のみ例外**(issue #349): 統合された小数÷整数ドリルは 余り設定が「なし」以外(あり/わり進み)のとき筆算をレイアウトできないため、`displayFormatSetting((state) => (state?.remainderMode ?? 'none') !== 'none')` として筆算トグルを無効化する。`DISPLAY_FORMAT_ITEM_IDS` には引き続き含まれる(設定自体は持つ)。

`g5-decimal-div`(issue #349 で「整数と小数の割り算」から「小数のわり算」へ戻した)は 19 項目から除外したまま。vendor済み `longdivision` パッケージの `\intlongdivision` が整数の除数しか受け付けないため、除数が小数の 5年ドリルはどの余り設定でも筆算を出せない(issue #180(agenda)で対応方針を検討中、実装は保留)。よって `displayFormat` 設定自体を持たない。

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

3年生に新設した `four-operations` カテゴリは現在1項目を持つ(issue #328 で `g3-parentheses-mul-result-1000` を4年生へ移設。下記「括弧・かけ算を含む混合計算を3年生から4年生へ移設(issue #328)」参照):
- `g3-addsub-mixed-result-1000`: 加減算のみの3項混合(`terms:3, mixed_operators:true`)で `a_min:1, a_max:999, b_min:1, b_max:999, result_max: 1000`。2年生の対応項目(`g2-addsub-mixed`、issue #311 で「3つの数の足し引き」へ改称・演算モード選択化)と異なり `result_max` を持ち、演算モードは足し引き混合固定(掛け算は含まない)。学習指導要領解説 算数編 第3学年は □ を用いた式と同一演算3項の加減しか扱わないため、この項目のみが3年生 `four-operations` として妥当。

`catalog.js` の `CATEGORY_ORDER` は既に `four-operations` を `fraction` の直後(実質最後尾側)に固定しているため、3年生に `four-operations` カテゴリキーを追加するだけで学年ページ最下部にセクションが自動的に現れる(`catalog.js` 自体は無変更)。3年生・4年生とも `four-operations` カテゴリキーを保持するため、issue #328 の項目移設後もこの点は変わらない。

### 3年生の総合問題(複数ソース混在ワークシート)(issue #140)

3年生に `review` カテゴリを新設し、1項目 `g3-review`(`titleKey: 'menu_g3_review_title'`「3年の総合問題」)を置いた。学習指導要領 第3学年 A「数と計算」の複数単元 ―― 3〜4桁のたし算・ひき算、2〜3位数×1位数のかけ算、あまりのあるわり算(九九の範囲)、小数(1/10の位)のたし算・ひき算、同分母・真分数のたし算・ひき算 ―― を1枚に混在させる「総まとめ」。学年の総まとめとして `CATEGORY_ORDER`(`catalog.js`/`pcMakeFlow.js`)の**先頭**に `'review'` を置き、3年生ページでは他カテゴリより上に表示する。

- `settings: []`(設定なし)、`supportLevel: 'full'`、`latexOnly: true`。`examples` は静的(`presetDetail.js` のライブプレビューは `command_type === 'ope'` のみ対象のため `review` は静的例題のまま)。
- `buildParams()` は引数を取らず `{ command_type: 'review', shuffle: true, sources: [...5件...] }` を返す。`sources` 各要素は `{ command_type: 'ope'|'frac', num: 1, ...そのドリルのオプション }`。`num` は**相対ウェイト**で、backend の [[../../../../backend/three_layer_renderer.py]] `_generate_review_pdf` がプリント全体の問題数(`presetDetail.js` の 10/20/30 選択 = `rows*columns`)へウェイト按分する。5件を等ウェイト(`num:1`×5)にしているため、どの問題数でも5単元が均等になる。
- `sources` の内訳: `ope` add/sub(`carry_mode:'mixed'`, `a/b_min 100`/`max 9999`)、`ope` mul(`a 10..999`, `b 2..9`)、`ope` div(`remainder_mode:'mixed'`, `a 10..81`, `b 2..9`)、`ope` add/sub 小数(`a/b_decimal_places:1`, `a/b 1..99`)、`frac` add/sub(`numerator_digits:1`, `denominator_digits:1`, `same_denominator:true`, `proper_operands:true`, `proper_result:true`)。
- `command_type: 'review'` は `POST /generate-problems`(データのみ)非対応。CLI(`nuts_calc_tex.py`)にも `review` サブコマンドは無い(合成は backend の presentation 層専用)。
- `drillPresets.test.js` の `KNOWN_CATEGORIES` に `'review'` を追加した([[./drillPresets.test.js]] 参照)。`catalog.js`/`pcMakeFlow.js` は `CATEGORY_ORDER` 先頭に `'review'` を1語足すだけ([[./catalog.js]]/[[./pcMakeFlow.js]] 参照)。文言3キーは [[./strings.ja.json]] に追加。

### 1年生の総合問題(複数ソース混在ワークシート)(issue #365)

1年生に `review` カテゴリを新設し、1項目 `g1-review`(`titleKey: 'menu_g1_review_title'`「1年の総合問題」)を置いた(親 issue #358 の全学年 `review` 展開の第1子。#357 P3 = #364 で `review` が共有生成層に載ったことが前提)。学習指導要領 第1学年 A「数と計算」加法・減法の複数単元 ―― くり上がりのある1桁+1桁のたし算、くり下がりのある20までのひき算、2桁±1桁(くり上がり/くり下がりなし)、何十±何十 ―― を1枚に混在させる。`CATEGORY_ORDER` は既に `'review'` を先頭に持つため、`catalog.js`/`pcMakeFlow.js` は無変更。

- `settings: []`、`supportLevel: 'full'`、`latexOnly: true`。`examples` は静的(`['8+7', '13-6', '45+3', '68-5', '40+30']`)。
- `buildParams()` は引数を取らず `{ command_type: 'review', shuffle: true, sources: [...5件...] }` を返す。`sources` 各要素は既存の1年生メニュードリルの `buildParams()` 出力(その `ope` オプション)をそのまま流用し `num: 1` を付けたもの ―― (1) `ope` add `carry_mode:'required'` `a/b 1..9` `result_max:20`(= `g1-add-20` あり)、(2) `ope` sub `carry_mode:'required'` `a 10..19` `b 1..9` `result_max:20`(= `g1-sub-20` あり)、(3) `ope` add `carry_mode:'none'` `a 10..99` `b 1..9` `result_max:100`(= `g1-add-100`)、(4) `ope` sub 同(= `g1-sub-100`)、(5) `ope` add/sub `carry_mode:'none'` `a/b 10..90` `a_multiple:10`/`b_multiple:10` `result_max:100`(= `g1-add-tens`/`g1-sub-tens`)。`num` は相対ウェイトで [[../../../../backend/three_layer_renderer.py]] `_generate_review_pdf` が全問題数(10/20/30)へ按分する。等ウェイト×5。
- **番号配置**: 5 source すべてが plain 2項 `ope`(`terms`/`mixed_operators`/`vertical` なし)なので、`_resolve_number_placement`([[../../../../backend/three_layer_renderer.py]])が `review` を短1行ドリルと判定し、中央寄せの `inline` 番号配置(issue #355)を返す。左 gutter だと右に空白帯が出て左に寄って見えるため。`g3-review` は `frac` source を含むため引き続き `gutter`(出力バイト不変)。この判定のため `g1-review` の source からは3項計算(`g1-three-terms` 相当、`terms:3`)を意図的に外している(issue #365 のスコープも「1〜2位数のたし算・ひき算」で3項は対象外)。
- `command_type: 'review'` は `POST /generate-problems` 非対応(g3-review と同じ)。
- `drillPresets.test.js` に `g1-review` 専用テストを追加(5 source・全 `ope`・`num:1`・`terms`/`mixed_operators`/`vertical` なし・くり上がり/くり下がり/何十 各単元の存在、[[./drillPresets.test.js]] 参照)。文言3キーは [[./strings.ja.json]] に追加。

### 括弧・かけ算を含む混合計算を3年生から4年生へ移設(issue #328)

`(45+38)×12-56` 形式の「括弧・四則混合・演算の順序」は学習指導要領解説 算数編 第4学年 A「数量の関係を表す式」(（）を用いた式・四則の混合した式・計算の順序のきまり)の内容で、第3学年ではない。issue #161 で3年生 `four-operations` に新設した `g3-parentheses-mul-result-1000` を、`id`・`titleKey`/`descKey`/`pointKey` を `g3-`→`g4-` に付け替えて `g4-parentheses-mul-result-1000` として `grade4['four-operations']` の `g4-parentheses` 直後へ移した(この `g4-parentheses-mul-result-1000` 項目自体は後続の issue #340 で削除された。下記「4年生の括弧ドリルを2段階へ統合(issue #340)」参照)。移設時点では `examples`・`settings`・`supportLevel`・`latexOnly`・`buildParams` 本体を一切変更していない。3年生から括弧・かけ算を含む項目を除いた点(下記)は #340 後も有効。

`strings.ja.json` の対応3キー(`menu_g3_parentheses_mul_result_1000_{title,desc,point}` → `menu_g4_…`)は #328 では文言そのままでリネームした(#340 で当該3キーごと削除)。`menu_g3_addsub_mixed_result_1000_*` は3年生に残るため無変更。`docs/uiux/calculation_drill_menu_parameters_v1.md` は小学3年生の表から「括弧を含む足し算・引き算・かけ算」行を削除した(#328)。`drillPresets.test.js` の該当テストを4年生・新 id へ retarget し、3年生 `four-operations` が括弧・かけ算を含む項目を持たないことを検証する #328 テストを追加した([[./drillPresets.test.js]] 参照)。`CATEGORY_ORDER`(`catalog.js`/`pcMakeFlow.js`)は両学年とも `four-operations` カテゴリを維持するため無変更。

### 括弧の足し引きドリルを2年生から4年生へ移設し難易度を基礎へ(issue #330)

`35-(12+8)` 形式の「（　）を用いた式・（　）の中を先に計算するきまり」は学習指導要領解説 算数編 第4学年 A「数量の関係を表す式」の内容であり、第2学年ではない(一部の教科書が第2学年で「たしてからひく」文脈として非形式的に先取りするが、この項目はその規約を「ルールをはじめて学ぶ」ドリルとして明示している)。issue #161 以前から2年生 `four-operations` にあった `g2-parentheses` を、`id`・`titleKey`/`descKey`/`pointKey` を `g2-`→`g4-` に付け替えて `g4-parentheses-addsub` として `grade4['four-operations']` の `g4-four-operations` 直後・`g4-parentheses` の直前へ移した。`examples`(`['35-(12+8)', '52-(23+9)', '68-(15+22)']`)・`settings`(`parentheses` 固定=present)・`supportLevel`(`full`)・`latexOnly`(`true`)・`buildParams` 本体(`operator:['add','sub'], terms:3, use_parentheses:true, a_min:1, a_max:90, b_min:1, b_max:90`)は一切変更していない。

`difficultyKey` は移設前の `difficulty_standard` から `difficulty_basic` へ引き下げた。括弧内・括弧外とも加減のみ、数値 90 以下で、（　）ルールの最も素朴な導入にあたるため。issue #340 の統合後、4年生の括弧ドリルは2項目で難易度が段階化される: `g4-parentheses-addsub`(基礎、加減のみ) < `g4-parentheses`(標準、四則・除算含むが1桁)。いずれも `difficulty_advanced` は与えない(下記「4年生の括弧ドリルを2段階へ統合(issue #340)」参照)。

`g4-parentheses` へ統合せず独立項目として残した理由: `g4-parentheses` は除算を含む1桁オペランドの四則混合(`operator:['add','sub','mul','div'], a_digits:1`)で、括弧内に加減のみを置く本項目より難しく、本項目は括弧ルールの入口として最も易しい段階を担う。オペランド範囲指定は `a_min`/`a_max` 形式のままで、同じ4年生の `g4-parentheses` が使う `a_digits`/`b_digits` 形式とは異なる(移設元の2年生 `g2-parentheses` と同形式)。

`strings.ja.json` の対応3キー(`menu_g2_parentheses_{title,desc,point}` → `menu_g4_parentheses_addsub_{title,desc,point}`)は文言そのままでリネームし、g4 ブロック(`menu_g4_four_operations_point` の直後)へ移動した。`docs/uiux/calculation_drill_menu_parameters_v1.md` は小学2年生の表から「括弧を含む足し引き」行を削除し、小学4年生の表(「整数の四則混合計算」の直後)へ難易度列を `基礎`・備考「括弧内を先に計算。＋と－のみ」とした同等の行を追加した。`drillPresets.test.js` に、2年生 `four-operations` が `g2-addsub-mixed` のみで括弧項目を持たないことを検証する #330 テストと、`g4-parentheses-addsub` が `difficulty_basic` かつ加減のみ・括弧ありの `buildParams` を返すことを検証する #330 テストを追加した([[./drillPresets.test.js]] 参照)。`CATEGORY_ORDER`(`catalog.js`/`pcMakeFlow.js`)は両学年とも `four-operations` カテゴリを維持するため無変更。

### 4年生の括弧ドリルを2段階へ統合(issue #340)

issue #328・#330 の移設の結果、4年生 `four-operations` には括弧ドリルが3項目あった: `g4-parentheses-addsub`(基礎、＋−)・`g4-parentheses-mul-result-1000`(標準、＋−×・答え1,000まで・2桁)・`g4-parentheses`(標準、＋−×÷・1桁)。後ろの2つは同一の学習内容(（　）を先に → ×÷ → ＋−)を教えており、違いは ÷ の有無とオペランドの大きさという難易度の調整つまみに過ぎず、学習指導要領 第4学年 A「数量の関係を表す式」の別ステップではない(÷ の練習は `g4-div-1digit`/`g4-div-2digit` が別途担当)。標準の名前(「括弧を含む足し算・引き算・かけ算」と「括弧を含む四則混合計算」)も紛らわしかった。

そこで冗長な中間層 `g4-parentheses-mul-result-1000` オブジェクトを `grade4['four-operations']` から丸ごと削除し、2段階に統合した: 基礎 `g4-parentheses-addsub`(＋−) と 標準 `g4-parentheses`(＋−×÷)。`g4-parentheses` の `buildParams`(`operator:['add','sub','mul','div'], mixed_operators:true, use_parentheses:true, a_digits:1, b_digits:1`)・`examples`・`settings`・文言は一切変更していない(純粋な削除)。オペランド範囲を広げなかった理由: （　）+ 計算の順序のきまりという単元スキルは1桁オペランドで完全に練習でき(例 `(8+4)×5-6`)、`g4-parentheses` は ÷ を含むため1桁に留めると割り切れる素直な除算(÷2〜÷9)を保てる。2桁化 + ÷ はバックエンドが割り切れる2桁÷2桁を探索する必要が生じ、不自然な数とリトライ増を招くだけで単元上の意義がない。大きい数の練習は `g4-four-operations` と4年生の除算ドリルが既に担当する。

削除に伴い、`strings.ja.json` の `menu_g4_parentheses_mul_result_1000_{title,desc,point}` の3キーと、他に参照がなくなった `setting_option_addsubmul_mixed` キーを削除した(orphan setting option 削除の先例: issue #329)。`drillPresets.test.js` は #328 で retarget した「grade 4 parenthesized mix caps the answer at 1,000…」テストを削除し、4年生 `four-operations` の括弧項目がちょうど `['g4-parentheses-addsub','g4-parentheses']`(難易度 `difficulty_basic`/`difficulty_standard`)であること・`g4-parentheses-mul-result-1000` が存在しないことを検証する #340 テストへ置き換えた([[./drillPresets.test.js]] 参照)。`docs/uiux/calculation_drill_menu_parameters_v1.md` は小学4年生の表から「括弧を含む足し算・引き算・かけ算」行を削除する(「括弧を含む四則混合計算」行はパラメータ無変更のため据え置き)。バックエンド変更なし。`CATEGORY_ORDER` 無変更。

### g4-parentheses の除算を保証し non-trivial 化(issue #342)

統合後の標準 `g4-parentheses`(＋−×÷・1桁・`mixed_operators`)は「四則混合」と銘打っているのに、実測で除算が現れる問題は約19%、しかもその約65%が `x÷1` や `x÷x` という自明な除算だった(バックエンドの木リトライが、除算を避ける／÷1・x÷x で通る木を圧倒的に引きやすいため)。3つの static examples(`(8+4)×5-6` など)も除算を1つも含まず、かつ生成器が実際に出す形(3項・演算子2つ)ではなく4項・演算子3つで不整合だった。

対応: `buildParams` に `nontrivial_division: true` を追加。バックエンド([[../../../../backend/nuts_calc_tex.py]] の `--nontrivial-division`、issue #342)が「除算ノードを必ず1つ以上含み、全除算ノードで割る数・商とも2以上」になるまで木を再抽選する。frontend で立てるのはこのプリセットだけ。`examples` は生成器の実際の出力形(3項・演算子2つ・葉以外の内部ノードをかっこで包む)に合わせ、いずれも non-trivial な除算を含む `['(8+4)÷3', '8÷(6-4)', '(9÷3)×5']` に差し替えた。`operator`/`mixed_operators`/`use_parentheses`/`a_digits`/`b_digits`/`difficultyKey`/`settings`/文言は無変更。

オペランド範囲は広げていない(#340 と同じ理由: 1桁に留めることで割り切れる素直な除算 ÷2〜÷9 を保つ)。厳格化したリトライ受理条件でも 1桁・3項では平均約33回・最大約250回で収束し `MAX_OPERAND_RETRY_ATTEMPTS`(1000)に遠く届かないことを実測済み。`g4-parentheses` は live preview 非対応(`isLivePreviewSupported()` が `use_parentheses` を除外)のため、ユーザーが detail 画面で見るのはこの static `examples` のみ。

`drillPresets.test.js` は #340 の統合テストに `nontrivial_division: true` を追加し、`g4-parentheses` の `buildParams` 全体の deep-equal・`g4-parentheses-addsub` にはこのキーが付かないこと・examples が新しい3値であることを検証する #342 テストを追加した([[./drillPresets.test.js]] 参照)。`strings.ja.json` 無変更。`docs/uiux/calculation_drill_menu_parameters_v1.md` の4年生「括弧を含む四則混合計算」行は example を `(8+4)÷3` に更新し備考に「除算を必ず含み、割る数・商とも2以上」を追記する。

### 4年生の分数カテゴリ撤廃(issue #315)

issue #161 の3年生と同じ再編を4年生にも適用した。4年生の `fraction` カテゴリ(`g4-fraction-add`/`g4-fraction-sub` の2項目のみで構成)を撤廃し、両項目を内容無変更のまま `addition`/`subtraction` 配列の末尾へ移動した(`g4-fraction-add` は `g4-decimal-add` の後、`g4-fraction-sub` は `g4-decimal-sub` の後)。`id`/`titleKey`/`descKey`/`pointKey`/`settings`/`buildParams`/`examplesFor`、`g4-fraction-sub` の `proper_result` 判定コメントを含め一切変更していない。

カテゴリキーは学年ページのセクション見出し順序付け(`catalog.js` の `CATEGORY_ORDER`)にのみ使われ、削除済み `drillCatalog.js` の分類ロジック(`operationGroup`/`numberType`)には影響しない。よってこの移動によるカタログ絞り込みへの影響はない(#161 と同じ理屈)。`catalog.js` の `CATEGORY_ORDER` と `strings.ja.json` の `category_fraction` は5・6年生が引き続き `fraction` カテゴリを使うため無変更。`drillPresets.test.js` に3年生と対称な「grade 4 fraction items live under addition/subtraction」テストを追加した。

### 分数×整数 / 分数÷整数 を6年生から5年生へ移設(issue #327)

学習指導要領解説 算数編 第5学年 A(1)「分数」が分数×整数・分数÷整数を第5学年の内容として挙げている(第6学年は乗数・除数が分数の場合を扱う)ことに合わせ、`g6-fraction-mul-int`(分数×整数)・`g6-fraction-div-int`(分数÷整数)の2項目を `grade6.fraction` から `grade5.fraction` へ移し、`id`/`titleKey`/`descKey`/`pointKey` を `g6-`→`g5-` に付け替えた(`g5-fraction-mul-int`/`g5-fraction-div-int`)。`examples`/`examplesFor`/`settings`/`buildParams`(`command_type: 'mixed'`、`reducible_mode` 配線を含む)は一切変更していない。配置は `g5-fraction-sub` の直後・`g5-frac2dec` の直前(学習指導要領の系列: 約分・通分 → 分数の加減 → 分数×整数・分数÷整数 → 分数と小数の関係)。

`strings.ja.json` の対応6キー(`menu_g6_fraction_mul_int_{title,desc,point}`/`menu_g6_fraction_div_int_{title,desc,point}` → `menu_g5_…`)は文言そのままでリネームし、g5 ブロック(`menu_g5_gcd_point` の直後)へ移動した。`docs/uiux/calculation_drill_menu_parameters_v1.md` は分数×整数・分数÷整数の行を小学6年生の表から小学5年生の表(分数の引き算と分数を小数に直すの間)へ移した。整数×分数(`g6-int-mul-fraction`)・整数÷分数(`g6-int-div-fraction`)は乗数・除数が分数のため6年生に残す(issue #327 のスコープ外)。`drillPresets.test.js` の #114 テストの id リストを6年生に残る4項目へ縮小し、移設を検証する #327 テストを追加した([[./drillPresets.test.js]] 参照)。`CATEGORY_ORDER`(`catalog.js`/`pcMakeFlow.js`)は両学年とも `fraction` カテゴリを維持するため無変更。

### 3年生「商が2桁になる割り算」ドリル追加(issue #332)

学習指導要領解説 算数編 第3学年 A「除法」が「簡単な場合について、除数が1位数で商が2位数の除法」(例: `48÷4`、`69÷3`)を挙げているのに合わせ、`grade3.division` に3項目めの `g3-div-2digit-quotient` を追加した(配置は `g3-div-kuku` と `g3-div-remainder` の間)。`difficultyKey: 'difficulty_standard'`(基礎の九九ドリルの一段上、`g3-div-remainder` と同格)、`settings` は `g3-div-kuku` と同じ非活性の `fixedSetting('remainderMode', …, 'setting_option_none', …)`、`latexOnly: true`、`supportLevel: 'full'`。`displayFormatSetting` は付けない(3年生の割り算兄弟に前例がなく、`DISPLAY_FORMAT_ITEM_IDS` を増やさない)。

`buildParams()` は `{ command_type: 'ope', operator: ['div'], remainder_mode: 'none', a_min: 20, a_max: 99, b_min: 2, b_max: 9, quotient_digits: 2 }`。**商の2桁制約は `a_min`/`a_max`/`b_max` で近似せず、除数レンジを 2〜9 丸ごと使ったうえでバックエンドの新フラグ `quotient_digits`(CLI の `--quotient-digits 2`)に委ねる**(renderer-owned drill logic の原則。generator 側が「商ちょうど N 桁」を保証する。[[../../../backend/nuts_calc_tex.py]] の `### ope --quotient-digits N`、および転送経路の [[../../../backend/renderer_config.py]]/[[../../../backend/problem_generation.py]]/[[../../../backend/three_layer_renderer.py]] 参照)。`quotient_digits` は snake_case のリクエストキーで、`a_multiple` と同じ plain-ope 3経路(CLI `build_ope_pages` / live preview / in-process PDF)だけが転送する。`a_min: 20`(a_max 99)は除数 9 でも 2桁商の割り切れるペア(90÷9, 99÷9 等)が存在することを担保するだけの下限。

`strings.ja.json` に `menu_g3_div_2digit_quotient_{title,desc,point}` の3キーを `menu_g3_div_kuku_point` の直後へ追加([[./strings.ja.json]] 参照)。`docs/uiux/calculation_drill_menu_parameters_v1.md` の小学3年生表に「商が2桁になる割り算」行を「九九の範囲の割り算」と「余りのある割り算」の間へ追加。`drillPresets.test.js` に `buildParams()` の deep-equal(`quotient_digits: 2` を含む)と設定・難易度を検証する #332 テストを追加([[./drillPresets.test.js]] 参照)。`CATEGORY_ORDER` は無変更(`division` カテゴリは既存)。

### 4年生「小数のあまりのある割り算」ドリル追加(issue #333)

学習指導要領解説 算数編 第4学年 A「小数」除法が、小数÷整数で割り切れない場合(商を一の位まで求めてあまりを出す)を挙げているのに合わせ、`grade4.division` に3項目めの `g4-decimal-div-int-remainder` を追加した(配置は `g4-decimal-div-int` の直後)。`difficultyKey: 'difficulty_standard'`(`g4-decimal-div-int` と同格)、`latexOnly: true`、`supportLevel: 'full'`。`settings` は 2 つの非活性固定ピル: `fixedSetting('divisor', 'setting_divisor_label', 'setting_option_integer')`(除数:整数)と `fixedSetting('remainder', 'setting_remainder_label', 'setting_option_required')`(余り:あり)。このドリルは常に「あまりを出す」形なので、選択式の `remainderSetting`(なし/あり/まぜる)ではなく固定ピルで表現する。

**`displayFormatSetting` は付けない**(バックエンド `_init()` が `--vertical --decimal-remainder` を拒否する — longdivision が小数あまりのレイアウトをできない — ため。よって `drillPresets.test.js` の `DISPLAY_FORMAT_ITEM_IDS` 18項目列挙には**加えない**)。

`buildParams()`(引数を無視)は `{ command_type: 'ope', operator: ['div'], a_digits: 2, b_min: 2, b_max: 9, a_decimal_places: 1, decimal_remainder: true }`。**「商を一の位まで求めてゼロでない小数あまり」はレンジで近似せず、バックエンドの新フラグ `decimal_remainder`(CLI の `--decimal-remainder`)に委ねる**(renderer-owned drill logic。generator が「わられる数が真の小数・商 1 以上・あまり非ゼロ」を保証する。[[../../../backend/nuts_calc_tex.py]] の `### ope --decimal-remainder`、および転送経路の [[../../../backend/renderer_config.py]]/[[../../../backend/problem_generation.py]]/[[../../../backend/three_layer_renderer.py]] 参照)。`decimal_remainder` は snake_case のリクエストキーで、`quotient_digits` と同じ plain-ope 3経路だけが転送する。`b_min: 2`/`b_max: 9` は明示指定(`b_digits: 1` だと `÷1` の自明な割り算が混じるため)。**わり進み・商のがい数はこのオプションでは扱わない**(わり進みは将来の `ope -o div` フラグ候補、商のがい数は別途計画中の概数計算ドリルへ。あまりとは別 PR)。

`strings.ja.json` に `menu_g4_decimal_div_int_remainder_{title,desc,point}` の3キーを `menu_g4_decimal_div_int_point` の直後へ追加([[./strings.ja.json]] 参照)。`docs/uiux/calculation_drill_menu_parameters_v1.md` の小学4年生表に「小数のあまりのある割り算」行を「小数÷整数」の直後へ追加。`drillPresets.test.js` に `buildParams()` の deep-equal(`decimal_remainder: true` を含む)・2固定ピル・`DISPLAY_FORMAT_ITEM_IDS` に含まれないことを検証する #333 テストを追加([[./drillPresets.test.js]] 参照)。`CATEGORY_ORDER` は無変更。

### 5年生「小数のわり算（あまり）」ドリル追加(issue #334)

学習指導要領解説 算数編 第5学年「小数のわり算」(除数が小数)が、割り切れない場合(商を一の位まで求めてあまりを出す)を扱うのに合わせ、`grade5.decimal` に3項目めの `g5-decimal-div-remainder` を追加した(配置は `g5-decimal-div` の直後)。`difficultyKey: 'difficulty_standard'`、`latexOnly: true`、`supportLevel: 'full'`。`settings` は 2 つの非活性固定ピル: `fixedSetting('divisor', 'setting_divisor_label', 'setting_option_decimal')`(除数:小数)と `fixedSetting('remainder', 'setting_remainder_label', 'setting_option_required')`(余り:あり)。#333 の `g4-decimal-div-int-remainder`(除数:整数)と対になる。#317 の割り切れる `g5-decimal-div` は無変更で別メニューとして残す。

**`displayFormatSetting` は付けない**(#333 と同じ理由。`DISPLAY_FORMAT_ITEM_IDS` には加えない)。

`buildParams()`(引数を無視)は `{ command_type: 'ope', operator: ['div'], a_digits: 2, b_digits: 2, a_decimal_places: 1, b_decimal_places: 1, decimal_remainder: true }`。`g5-decimal-div` の `decimal_div_decimal` 分岐と同じレンジ(わられる数・わる数とも小数第1位)に `decimal_remainder: true` を足しただけ。バックエンドは #334 で `--decimal-remainder` を小数除数対応に一般化し、除数を整数にスケールしてから割る(あまりの小数点はずらす前のわられる数の位置にそろえる)。`b_decimal_places` は既に全経路が転送しているため追加配線は不要([[../../../backend/nuts_calc_tex.py]] の `### ope --decimal-remainder` 参照)。

`strings.ja.json` に `menu_g5_decimal_div_remainder_{title,desc,point}` の3キーを `menu_g5_decimal_div_point` の直後へ追加([[./strings.ja.json]] 参照)。`docs/uiux/calculation_drill_menu_parameters_v1.md` の小学5年生表に「小数のわり算（あまり）」行を「整数と小数の割り算」の直後へ追加。`drillPresets.test.js` に grade5 `decimal` の順序リスト更新と、`buildParams()` の deep-equal(`b_decimal_places: 1`/`decimal_remainder: true` を含む)・2固定ピル・`DISPLAY_FORMAT_ITEM_IDS` に含まれないこと・`g5-decimal-div` が無変更であることを検証する #334 テストを追加([[./drillPresets.test.js]] 参照)。`CATEGORY_ORDER` は無変更。

> **issue #349 で上記 #317 / #333 / #334 の4項目を2項目に統合した(下記「小数のわり算ドリルの余り設定への再編」参照)。** 現状: grade 4 division は `g4-decimal-div-int` の1項目、grade 5 `decimal` は `[g5-decimal-mul, g5-decimal-div]` の2項目。`g4-decimal-div-int-remainder` / `g5-decimal-div-remainder` / `DIVIDEND_TYPE_OPTIONS` は削除済み。

### 小数のわり算ドリルの余り設定への再編とわり進みモード(issue #349)

#318 監査(→ #326)の consolidation candidate B / C に対応。grade 4 の小数÷整数(割り切れる `g4-decimal-div-int` + あまり `g4-decimal-div-int-remainder`)と grade 5 の小数÷小数(#317 の被除数選択 `g5-decimal-div` + あまり `g5-decimal-div-remainder`)を、**それぞれ「余り」設定を持つ1項目**に統合した。他の全わり算ドリル(`g4-div-1digit` 等)が余りを「なし/あり/まぜる」の単一設定で持つのに合わせる。

- **共有ヘルパー**: `DECIMAL_DIV_REMAINDER_OPTIONS`(`OPT_NONE` / `OPT_REQUIRED` / `{ value: 'divide_through', labelKey: 'setting_option_divide_through' }` = なし/あり/わり進み)+ `decimalDivRemainderSetting(labelKey)`(`id: 'remainderMode'`, `type: 'choice'`, 既定 `'none'`)。`carrySetting`/`remainderSetting` の なし/あり/まぜる とは別の3択(backend に「両方まぜる」モードは無い)。
- **`examplesByChoice(settingIds, byCombo, defaultValue = 'mixed')`**: 第3引数を追加。既定値キーが `'mixed'` 以外(ここでは `'none'`)の設定に対応する。`byCombo.none` が静的 `examples` と一致する(#135 テストの規約)。
- **`g4-decimal-div-int`**(grade 4 `division`): `settings: [fixedSetting('divisor', …, 'setting_option_integer'), decimalDivRemainderSetting('setting_remainder_label'), displayFormatSetting((state) => (state?.remainderMode ?? 'none') !== 'none')]`。`buildParams(state)` は `base = { command_type: 'ope', operator: ['div'], a_digits: 2, b_min: 2, b_max: 9, a_decimal_places: 1 }` を共通に、`required` → `{ ...base, decimal_remainder: true }`、`divide_through` → `{ ...base, divide_through: true }`、`none` → `{ ...base, ...displayFormatParam(state) }`(筆算可)。旧 `g4-decimal-div-int` の `b_digits: 1` を `b_min: 2, b_max: 9` に統一した(÷1 の自明なわり算を排除、旧あまり項目と同レンジ)。
- **`g5-decimal-div`**(grade 5 `decimal`): `settings: [fixedSetting('divisor', …, 'setting_option_decimal'), decimalDivRemainderSetting('setting_remainder_label')]`。`displayFormat` は無し(小数除数は筆算不可、#180)。`base = { command_type: 'ope', operator: ['div'], a_digits: 2, b_digits: 2, a_decimal_places: 1, b_decimal_places: 1 }`、`required`/`divide_through` は g4 と同じフラグを足すだけ、`none` は `base` そのまま(#317 以前の割り切れる小数÷小数と同一)。
- **#317 の被除数(`dividendType`)設定は削除**(学習指導要領準拠の設計判断): 第5学年 A(3)「小数の除法」の中心は小数÷小数で、余り=なし が割り切れる小数÷小数をカバーする。被除数×余りはバックエンド上不整合になる(`--integer-dividend` は `--decimal-remainder`/`--divide-through` と相互排他、かつ整数商を強制する)。タイトルは `menu_g5_decimal_div_title` を「整数と小数の割り算」→「小数のわり算」に戻した。`DIVIDEND_TYPE_OPTIONS` と孤立文言(`setting_dividend_label` 等)を削除([[./strings.ja.json]] 参照)。
- **わり進み**は backend の新フラグ `divide_through`(`--divide-through`)に委ねる(renderer-owned drill logic)。商が有限小数で終わるまで割り進み、必要な桁数で商を出す(あまり無し)。詳細は [[../../../backend/nuts_calc_tex.py]] の `### ope --divide-through`、転送経路は [[../../../backend/renderer_config.py]] / [[../../../backend/problem_generation.py]] / [[../../../backend/three_layer_renderer.py]]。
- `DISPLAY_FORMAT_ITEM_IDS` は無変更(`g4-decimal-div-int` は元から含まれ設定を持ち続ける。`g5-decimal-div` は元から非対象)。`docs/uiux/calculation_drill_menu_parameters_v1.md` の grade 4/5 の該当行を統合。テストは #317/#333/#334 のテストを統合項目のテストに書き換え、grade5 `decimal` 順序リストを `['g5-decimal-mul', 'g5-decimal-div']` に更新([[./drillPresets.test.js]] 参照)。

### 概数（がい数）ドリルの新設(issue #346)

学習指導要領解説 算数編 第4学年 A(2)「概数」(四捨五入・切り上げ・切り捨て、和差積商の見積もり=概算)と第5学年「四捨五入して商を概数で表す」に対応する2項目を追加した。バックエンドは専用コマンド `approx`([[../../../backend/nuts_calc_tex.py]] の `### approx (概数)` 参照)。

- **4年生に `number-sense` カテゴリを新設**して `g4-approx` を置く(それまで grade4 は `division`/`addition`/`subtraction`/`multiplication`/`four-operations` のみ。`number-sense` は `CATEGORY_ORDER`・`KNOWN_CATEGORIES` に既存で `category_number-sense` ラベルもあるため追加コストなし。grade5 の非算術ドリルが同カテゴリに集約されているのと同じ扱い)。`difficulty_standard`・`latexOnly: true`・`supportLevel: 'full'`。`settings` は2つの `choice`: `approxKind`(`round` 四捨五入して概数 / `estimate` 式の見積もり、既定 `round`)と `approxOperator`(和/差/積/商、既定 `mul`)。`approxOperator` は `kind=estimate` のときだけ `buildParams` に反映される(`round` では backend が無視するためコメントで明記)。`buildParams(state)` は `{ command_type: 'approx', kind, ...(kind==='estimate' && { operator: [<add|sub|mul|div>] }) }` -- オペランドレンジは送らず、backend `resolve_approx_params` の kind 別既定(round は 1000..99999、estimate は 100..999)に委ねる。`examplesFor` は `approxKind`/`approxOperator` で例題を切り替える inline 関数(`examplesByChoice` は全 'mixed' キーを要求するため不適。`g1-three-terms` と同じ inline 方式)。
- **5年生の既存 `number-sense` カテゴリ**に `g5-approx-quotient` を追加(`g5-gcd` の直後)。`approxKind` は `type: 'fixed'`(`valueLabelKey: 'setting_option_approx_quotient_kind'` = 「商のがい数」)。`buildParams()`(引数無視)は `{ command_type: 'approx', kind: 'quotient', dividend_decimal_places: 1, quotient_decimal_places: 2 }`(`5.8 ÷ 7 ≒ 0.83`)。
- 両項目とも `displayFormatSetting` は付けない(≒ の矢印式に筆算形式はない。`DISPLAY_FORMAT_ITEM_IDS` には加えない)。`isLivePreviewSupported()` は `command_type === 'ope'` のみ true のため、`preset.html` のライブ例題チップは他の非-`ope` ドリルと同じく静的 `examples` を使う(`/generate-problems` の `approx` 対応はエンドポイント完全性・テスト用)。
- `strings.ja.json` にメニュー6キー + 設定/選択肢9キーを追加([[./strings.ja.json]] 参照)。`docs/uiux/calculation_drill_menu_parameters_v1.md` の第4・第5学年表に行を追加(/docs-sync)。`drillPresets.test.js` に g4-approx / g5-approx-quotient の検証テスト2件を追加([[./drillPresets.test.js]] 参照)。`CATEGORY_ORDER` は `number-sense` を既に含むため無変更。

### 3年生「3桁×2桁」ドリル追加と6年生「分数・小数の混合計算」の四則化(issue #351)

#318 監査(→ #326)が見落としていた2つのギャップに対応した。バックエンド([[../../../backend/nuts_calc_tex.py]] / [[../../../backend/problem_generation.py]])は変更せず、既存の `ope`・`mixed` コマンドで実現できることを実機確認した。

- **3年生 `multiplication` に `g3-mul-3x2` を追加**(`g3-mul-2x2` の直後)。解説算数編 第3学年 A(3)「乗法」が(2位数)・(3位数)×(1位数)・(2位数)を扱うのに合わせ、既存の `g3-mul-2x1`/`g3-mul-3x1`/`g3-mul-2x2` と完全に同形で `a_digits: 3, b_digits: 2` にしただけ。`difficultyKey: 'difficulty_standard'`、`settings: [displayFormatSetting()]`、`supportLevel: 'full'`、`latexOnly: false`、`buildParams(state)` は `{ command_type: 'ope', operator: ['mul'], a_digits: 3, b_digits: 2, ...displayFormatParam(state) }`。`DISPLAY_FORMAT_ITEM_IDS`(前述「出題形式(式/筆算)設定」)に加え、列挙は18→19項目になった。
- **`g6-fraction-decimal-mixed` を加算のみ→四則混合へ拡張**。変更前は `buildParams: () => ({ command_type: 'mixed', operator: ['add'], a_kind: ['fraction', 'decimal'], b_kind: ['fraction', 'decimal'], numerator_digits: 1, denominator_digits: 1, decimal_places: 1 })` で2項の加算のみ。変更後は `operator: ['add', 'sub', 'mul', 'div']` + `mixed_operators: true` + `terms: 3` にし、`a_kind`/`b_kind` に `'int'` を足して分数・小数・整数が混ざる3項式を出す。`mixed_operators: true` は `terms >= 3` のときだけ意味を持つ(2項だと演算子スロットが1つ)ため `terms: 3` を併記した。兄弟の `g6-fraction-four-ops`/`g6-fraction-muldiv-mixed` も `terms: 3` を使う。
- 固有設定は非活性ピル1個のまま。値ラベルキーを `setting_option_fraction_decimal_mixed`(「分数・小数混合」、他に参照なし)→ `setting_option_fraction_decimal_int_mixed`(「分数・小数・整数混合」)へ置換した。`examples` は `['2/3+0.5×4', '0.75-1/4÷2', '3+1/5×0.9']`。`latexOnly: true`・`command_type: 'mixed'` のため `isLivePreviewSupported()` は false のまま(`preset.html` は静的 `examples` を使う)。
- `strings.ja.json` にメニュー3キー(`menu_g3_mul_3x2_*`)を追加、`menu_g6_fraction_decimal_mixed_desc`/`_point` を四則・整数を含む文言へ更新、`setting_option_fraction_decimal_mixed` を上記キーへリネーム([[./strings.ja.json]] 参照)。`drillPresets.test.js` の `DISPLAY_FORMAT_ITEM_IDS` に `g3-mul-3x2` を追加しテスト名を19項目へ更新([[./drillPresets.test.js]] 参照)。`docs/uiux/calculation_drill_menu_parameters_v1.md` の第3・第6学年表を更新(/docs-sync)。

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

- f76b2d4 feat(#365): add the grade-1 multi-source review (総合問題) worksheet
- e9083d6 feat(#140): add the grade-3 multi-source review (総合問題) worksheet (#354)
- a249fb2 feat(#351): add grade-3 3x2 multiplication drill and broaden g6 fraction/decimal mixed to four operations (#353)
- 7203e9e feat(#349): redesign decimal-division drills around a remainder setting and add a divide-through mode (#352)
- ffd182f feat(#346): add the 概数 (approx) rounding / estimation drill (#348)
- e493735 feat(#334): extend --decimal-remainder to a decimal divisor and add the grade 5 小数のわり算 (あまり) drill (#347)
- 9da1116 feat(#333): add grade 4 decimal-remainder division drill and --decimal-remainder flag (#345)
- b2df846 feat(#332): add grade 3 two-digit-quotient division drill and --quotient-digits flag (#344)
- 36de01d fix(#342): guarantee a non-trivial division in every g4-parentheses problem (#343)
- 960657f refactor(#340): consolidate grade 4 parentheses drills to two tiers (#341)
