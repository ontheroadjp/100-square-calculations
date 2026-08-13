# `frontend/web/src/drillPresets.js`

## 目的・役割

`docs/uiux/calculation_drill_menu_parameters_v1.md` に定義された学年別ドリルメニューを、grade → category → menu-item の階層データとして保持する。`POST /generate-pdf` へのリクエストパラメータへのマッピングを担う純粋な ES module で、React・i18next に依存しない(issue #98)。issue #88 時点では `frontend/spa/src/drillPresets.js` の単純コピーだったが、#98 で `frontend/web` 専用の新データモデルへ全面的に書き換えられ、両ファイルの内容は完全に分岐した(以後、追従コピー関係はない)。

## 動作の概要

`GRADES`(`[1,2,3,4,5,6]`)・`UNGRADED`(`'ungraded'`)・`presetsByGrade` を export する。`presetsByGrade[grade]` は `{ <categoryId>: menuItem[] }` の形で、`categoryId` は `addition`/`subtraction`/`multiplication`/`division`/`fraction`/`four-operations`/`number-sense` のいずれか(該当する学年にのみ出現)。

各 `menuItem` は以下を持つ:
- `id`/`titleKey`/`descKey`: 全データモデル中で `id` は一意。
- `difficultyKey`: `difficulty_basic`/`difficulty_standard`/`difficulty_basic_standard` のいずれか(ドキュメントの「難易度」列)。
- `examples`: ドキュメントの「計算式の例」列をそのまま文字列配列にしたもの。
- `settings`: ドキュメントの「固有設定」「選択可能値」「固定値・表示」を表す配列。各要素は `type: 'choice'`(セグメントコントロール、`options`/`default` を持つ)または `type: 'fixed'`(表示のみで変更不可、`valueLabelKey` を持つ)。
- `buildParams(state)`: `state`(`{ <settingId>: <選択値> }`、`choice` 設定のみキーを持つ)から `POST /generate-pdf` のリクエストボディを組み立てる関数。
- `supportLevel`: `'full'`(`nuts_calc_tex.py` がその項目の全設定を実現できる)/`'partial'`(生成はできるが一部設定を実現できない)/`'none'`。#98 時点では全項目 `full` または `partial` で、`none` は未使用(#91-#96 で対象コマンドが出揃ったため)。
- `latexOnly`: ほぼ全項目で `true`(carry_mode/remainder_mode/decimal places/terms/frac/mixed/compare/数論系コマンドが `nuts_calc_tex.py` 専用のため)。プレーンな `ope`(掛け算のみ等)や `99`/`aBc`/`squ` の一部項目のみ `false`。

## 重要な設計判断とその理由

### `drillCatalog.js` との役割分担

`drillCatalog.js` は本ファイルを消費する側で、`buildDrillCatalog`/`filterDrillCatalog` の公開 API を変更せず内部実装だけをこの新データモデルに対応させた(issue #98)。`home.js`/`catalog.js`/`preset.js` は無変更(#97/PR #109 で作られた既存 UI をそのまま維持するため)。詳細は [[./drillCatalog.js]] を参照。

### `partial` サポートの項目と根拠(実機検証で判明した未追跡ギャップ)

以下は #91-#96 のいずれにも含まれない、#98 実装時の検証で新たに判明したバックエンド制約:
- 4・5年生「分数の足し算/引き算」(`g4-fraction-add`/`sub`、`g5-fraction-add`/`sub`)は issue #112 で `frac` コマンドが `--a-fraction-form`/`--b-fraction-form`(`mixed`/`mix`)による帯分数対応を実装したため `full` に引き上げ済み。詳細は下記「帯分数(#112)対応」を参照。
- 3年生「小数第1位までの足し算/引き算」・4年生「小数の足し算/引き算」: `--carry-borrow`系フラグは整数専用で、`--a-decimal-places`/`--b-decimal-places` と併用不可(`nuts_calc_tex.py:610-611`)。→ issue #113。
- 6年生の分数×整数・整数×分数・分数×分数・分数÷整数・整数÷分数・分数÷分数(計6項目): `frac`/`mixed` とも Python の `Fraction` が自動的に既約分数へ簡約するため、「約分が必要になるかどうか」を制御するフラグが存在しない。→ issue #114。

`partial` の項目も `settings` にはドキュメント通りの選択肢を全て含める(将来 backend 側の issue が閉じた際、データモデルの再設計なしに `supportLevel` を `full` へ引き上げられるようにするため)。

### `--mixed-carry-borrow`/`--mixed-remainder` の単一演算子制約

`--mixed-carry-borrow` は `-o add sub` の両方を指定した場合のみ有効で、単一演算子(`add`のみ・`sub`のみ)には使えない(`nuts_calc_tex.py:603-604`)。そのため `carryModeField(operator, state)` ヘルパーは、単一演算子の項目で `carryMode: 'mixed'` が選ばれた場合、`carry_mode` パラメータ自体を省略する(carry_mode フラグ無指定と同じ意味 = 繰り上がり/繰り下がりを制約しない、が「まぜる」の意図と一致するため)。

### 九九(`g2-kuku`)の段選択

「1〜9の段」選択時は `command_type: '99'`(`a_value` に段を指定)、「まぜる」選択時は `command_type: 'ope', operator: ['mul']`(`a_min`/`a_max`/`b_min`/`b_max` を1〜9のランダム)に切り替える。ドキュメントの1つの「固有設定」が実装上は異なる CLI コマンドへの切り替えとして実現されている。

### ドキュメントにない既存機能の扱い(written/examPrep/missing-value)

`docs/uiux/calculation_drill_menu_parameters_v1.md` に定義がない、以下の旧機能は #98 でデータモデルから削除した(ユーザー承認済み):
- 筆算(縦書き/`--vertical`)形式のペアリング(`written` バケット)。
- 中学受験対策(examPrep、27プリセット)。
- 虫食い算(`--missing-value`)。

いずれも `frontend/spa` および CLI では引き続き利用可能。復活させるかどうかは issue #111 で後日判断する。

## 統合ポイント

- 呼び出し元: `drillCatalog.js`(`GRADES`/`UNGRADED`/`presetsByGrade`)。
- 呼び出し先: なし(データ定義のみ)。

## 注意事項・既知の制限

- `frontend/spa/src/drillPresets.js` とはもはや無関係(#98 で分岐)。今後 `frontend/spa` 側のプリセットを変更しても本ファイルには影響しない。
- `settings`/`buildParams` はデータ構造として定義済みだが、実際にユーザーが選択肢を切り替える UI(セグメントコントロール等)は未実装(#99/#100 のスコープ)。現状 `drillCatalog.js` はデフォルト状態(`choice` 設定の `default` 値)の `buildParams()` 出力のみを使用する。

## 変更履歴（git log より自動生成）

- 21a7b33 feat(#98): rebuild frontend/web drill menu data model to match calculation_drill_menu_parameters_v1.md
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
