# `web/frontend/src/drillPresets.js`

## 目的・役割

「学年(1〜6、または無学年)」を `POST /generate-pdf`(`web/backend/app.py`/`renderers.py`)へのリクエストパラメータにマッピングする静的な設定データ。UI ロジックを一切持たず、`GRADES`・`UNGRADED`・`CUSTOM_GRADE`・`presetsByGrade` の4つを export するのみ。

## 動作の概要

- `presetsByGrade[grade]`(`grade` は `1`〜`6` の数値、または `UNGRADED`(`'ungraded'`))は `{ normal: [...], written: [...], examPrep: [...] }` の形。`normal` は横書き(`a + b = c`)形式、`written` は筆算(縦書き/`vertical: true`)形式、`examPrep` は中学受験対策(issue #73、後述)のプリセット配列。`examPrep` を持つのは学年4〜6のみで、それ以外(1〜3、`UNGRADED`)は空配列。各 preset は `{ id, titleKey, descKey, params, numberInput? }` の形。
  - `params`: `/generate-pdf` にそのまま渡す固定パラメータ(例: `{ command_type: 'ope', operator: ['add', 'sub'], a_min: 1, a_max: 9, b_min: 1, b_max: 9 }`)。既存の加減算プリセットには、同じ桁数条件で `operator: ['add']` と `operator: ['sub']` を指定する単独プリセットが先行し、順に加算・減算・加減算が表示される(`drillPresets.js:22-42`)。
  - `numberInput`: ユーザーがカードごとに変更できる追加パラメータがある場合のみ存在。`{ param, labelKey, min, max, default }` で、`param` が `params` にマージされる対象キー(例: 九九の「段」は `a_value`)。
- `titleKey`/`descKey` は `public/locales/{en,ja}/translation.json` のキー。
- `UNGRADED`(`presetsByGrade['ungraded']`)は他の学年キーと完全に同じ `{ normal, written }` 構造を持つため、`GradeDrills.jsx` 側は数値学年と区別せず同じロジックで扱える(`CUSTOM_GRADE` のみ別 UI として分岐)。

## 重要な設計判断

- **分数カードは学習指導要領に沿って配置する**: `nuts_calc_tex.py` の `frac` コマンド(issue #65)を使い、3年は簡単な同分母加減(真分数かつ答えも真分数)、4年は同分母加減、5年は異分母加減、6年は分数の乗除を配置する。根拠資料は `docs/reference/elementary-course-of-study-mathematics-2017.pdf` と同READMEに保存している(`drillPresets.js:139-149,207-216,267-276,318-327`)。
- **分数カードはLaTeX専用**: 各カードに `latexOnly: true` を付ける。`GradeDrills.jsx` が `GET /renderer-info` の結果で除外するため、`frac` 非対応の `nuts_calc.py` へ誤送信されない。
- **かっこ付き計算カードも学習指導要領に沿って配置する(issue #67)**: `nuts_calc_tex.py` の `ope --use-parentheses`(issue #67)を使い、4年生に基本形、5・6年生に発展形(指導要領上の正式単元ではない応用ドリル)を配置する。根拠資料は分数カードと同じ `docs/reference/elementary-course-of-study-mathematics-2017.pdf`(196ページ、第４学年 A(6) 数量の関係を表す式「四則の混合した式や（　）を用いた式」)。分数カードと同じ理由で `latexOnly: true` を付ける。
  - `g4-parentheses`(`a_value: 1, b_value: 1`)・`g5-parentheses-advanced`(`a_value: 2, b_value: 1`)・`g6-parentheses-advanced`(`a_value: 3, b_value: 1`)はいずれも `operator: ['mix']` で、`--use-parentheses` 自体が問題ごとに演算子(`op_left`/`op_right`)とかっこの位置(`position`)をランダムに選ぶため、カード側で演算子を固定していない(旧実装はカードごとに固定の演算子ペアと左かっこ固定だったが、「かっこの位置・演算子・式全体のパターンが単調」というレビュー指摘を受けて廃止)。学年間の差は `a` の桁数のみ(1桁→2桁→3桁)で表現する。
  - `b_value` を3カードとも `1`(1桁、1〜9)に固定しているのは UI 上の意図ではなく、`nuts_calc_tex.py` 側の制約に合わせたもの: 第3項 `c` は `b` と同じレンジを再利用するため(`nuts_calc_tex.py` 参照)、`b`/`c` を広げると一部の演算子・かっこ位置の組み合わせ(例: 2桁×2桁の掛け算を外側の引き算に使う)で解が見つからず `ValueError` になることをシミュレーションで確認済み。詳細は [[../../../../nuts_calc_tex.py]] を参照。
- **虫食い算カードも学習指導要領に沿って配置する(issue #69)**: `nuts_calc_tex.py` の `ope --missing-value`(issue #69)を使い、1年生は導入的な応用(指導要領上の正式単元ではない)、2年生は指導要領記載の「加法と減法との相互関係」(`elementary-course-of-study-mathematics-2017.pdf` p.114、例: `□＋５＝12`)、3年生は「乗法・除法の相互関係」(同 p.55、例: `12÷3` を `3×□＝12` として出題)、4〜6年生は既存の `g4/g5/g6-mix` プリセットと同じオペランド条件を流用した四則混合の発展的応用として配置する(`drillPresets.js:51-65,103-118,181-195,273-287,366-381,443-458`)。分数・かっこ付き計算カードと同じ理由で `latexOnly: true` を付ける。
  - `g1-missing-value`/`g2-missing-value` は加減算のみ(`operator: ['add', 'sub']`)、`g3-missing-value` は乗除算のみ(`operator: ['mul', 'div']`)、`g4`〜`g6` は `operator: ['mix']`。いずれも `ope --missing-value` 自体が blank 位置(`a`/`b`)を問題ごとにランダムに選ぶため、カード側で blank 位置を指定するパラメータは存在しない。
  - `--missing-value` は答え `c` を blank 候補に含めない(`nuts_calc_tex.py` 参照: 答えを隠すのは通常の `ope` と区別がつかず虫食い算の本質ではないため)。そのため学年カードのオペランド範囲は既存の対応する `mix`/`add`/`sub`/`mul`/`div` プリセットと同じ値をそのまま流用でき、`--use-parentheses` のような「`b`/`c` を狭いレンジに保つ」といった特別な回避策は不要(決定的フォールバックを持つ既存の `CALC_FUNCTIONS` を再利用しているため `ValueError` のリスク自体がない)。
- **中学受験対策カード(`examPrep`、issue #73)は `nuts_calc_tex.py` の `ope --terms`/`--mixed-operators`/`--use-parentheses`(issue #71のN項一般化)を組み合わせた27枚(学年4/5/6 × 3段階 × 3レベル)**: `buildExamPrepPresets(grade, aValue)`(`drillPresets.js` 冒頭)がid/titleKey/descKey/paramsを機械的に生成する。id パターンは `g{grade}-examprep-{stage}-{level}`(`stage` は `basic`/`intermediate`/`advanced`、`level` は `1`/`2`/`3`)。
  - 段階軸: `basic`(`mixed_operators` 未指定=偽、`use_parentheses` 未指定=偽、演算子は問題ごとに `mix` から1種類選ばれ全項に適用)/ `intermediate`(`mixed_operators: true`、かっこ無し)/ `advanced`(`mixed_operators: true` かつ `use_parentheses: true`)。
  - レベル軸: `terms`(項数)が `1→3`/`2→4`/`3→5`。`resolve_term_range()` のクランプ下限(かっこ使用時3項、通常2項)を下回らないため `advanced` の level 1(3項)もクランプされずそのまま使われる。
  - 桁数レンジは既存の `g4/g5/g6-parentheses*` と同じ設計を踏襲: 最初の項(`a_value`)だけ学年で1→2→3桁(`buildExamPrepPresets` の第2引数)に増やし、残りの全項(`b_value`)は27パターン全てで `1`(1桁)に固定する。これは `nuts_calc_tex.py` の `assign_tree_operands()`/`generate_multi_term_ope_problems()` がいずれも「最初の葉だけ `nums_a`、残り全部が `nums_b`」という規約を持つため([[../../../../nuts_calc_tex.py]] 参照)。
  - **`ValueError` リスクの事前検証**: `ope --terms`/`--use-parentheses` は決定的フォールバックを持たず、項数が増えるほど `ValueError` のリスクが悪化することが `nuts_calc_tex.py` 側の設計判断として記録されている。本カード設計の27通り全ての(桁数レンジ×項数×段階)組み合わせは、実装前に `nuts_calc_tex.py` の生成関数を直接呼ぶシミュレーションで安全性を確認済み(600〜4000問中失敗ゼロ)。この事前確認は `tests/test_nuts_calc_tex_exam_prep_presets.py` として回帰テスト化されており、パラメータの組み合わせを変更する場合は両方(本ファイルとテスト)を同期させる必要がある。
  - 分数・かっこ付き計算カードと同じ理由で全27カードに `latexOnly: true` を付ける。
- **日本の学習指導要領(算数)の学年配置に沿った内容確定**(2026年見直し):
  - 1年生に `written`(筆算)セクションは存在しない。筆算という記法は指導要領上、正式には2年生から導入されるため。
  - 2年生の加減算(`normal`/`written` とも)は「2位数+2位数」(`a_value: 2, b_value: 2`)。指導要領の2年生内容「2位数の加法及び減法の計算、それらの筆算の仕方」に対応する。
  - 3年生に `--intermediate`(途中式)を使った掛け算工夫プリセット(`g3-mul-intermediate`)を追加。指導要領3年の「乗数や被乗数を分解して計算する工夫」に対応する内容が、これまでどの学年にも存在しなかったため。
  - 4年生の `written` に掛け算(3桁×2桁、`g4-mul-written`)・わり算(3桁÷2桁、長除法、`g4-div-written`)を追加。指導要領4年の「乗法・除法の筆算」に対応する。`nuts_calc.py`/`nuts_calc_tex.py` 側は既に対応済み(掛け算の複数桁乗数は issue #10、わり算の長除法は issue #11)だったが、フロントエンドのプリセットには未反映だった。
  - `aBc`(4桁数の分解暗算)・`squ`(平方数)は、指導要領上どの学年にも対応する明示的な単元が無い発展的な暗算ドリルのため、`UNGRADED`(無学年)に分類する(以前はそれぞれ6年生・5年生に割り当てていたが、根拠のない学年紐付けだったため移動した)。対照的に `pi`(×3.14)は5年生で正式に指導される円周率の定数(3.14)に直結するため、5・6年生に残している。
- **`com` コマンドの `a_value` は「桁数」ではなく補数の対象(target)そのもの**(`nuts_calc.py` の `main()` 内 `target = ini.a_value` を参照)。そのため `g1-complement10` は `a_value: 10`、`g2-complement100` は `a_value: 100` としている(桁数ではない点に注意)。
- **加減算の単独・混合プリセットはすべて併存する**: 加算のみ・減算のみを選びたい利用者に対応するため、既存の `operator: ['add', 'sub']` プリセットを削除せず、同一の難易度条件と `vertical` 設定を持つ `['add']`・`['sub']` プリセットを直前に配置する。これによりカード配列の描画順が「加算 → 減算 → 加減算」となる(`drillPresets.js:22-42`, `drillPresets.js:89-117`, `drillPresets.js:153-181`)。
- **`99`/`squ`/`pi` コマンドの `a_value` は「開始する数」**(`get_fixed_format_data` で `start_num = ini.a_value` として使われる)。九九は段そのもの(1〜9)なので `numberInput.default: 2` かつ `max: 9`、`squ`/`pi` は連番の開始位置なので `numberInput.default: 1` かつ `max: 20`。
- **`nuts_calc.py`/`nuts_calc_tex.py` 間のレンダラー相違を踏まえた除外**: `web/backend/renderers.py` は `NUTS_CALC_RENDERER` 環境変数でどちらのスクリプトにも切り替えられ、両者が同一の CLI サーフェスを持つ前提で実装されている。しかし調査の結果、3箇所で挙動が食い違うことが判明し、それぞれ別issueとして追跡している:
  - `--vertical` + `operator: ['mix']`: `nuts_calc.py` は拒否するが `nuts_calc_tex.py` は拒否しない(issue #41)。→ 本ファイルはこの組み合わせを一切使わない。
  - `--intermediate` と `operator`: `nuts_calc.py` は非 `mul` を指定しても黙って `mul` に上書きするが、`nuts_calc_tex.py` は明示的に拒否する(issue #42)。→ `g3-mul-intermediate` は `operator: ['mul']` を明示することで両レンダラーで動作する。
  - `100` コマンドに `a_value`/`b_value` を明示指定(2桁・3桁)した場合、`nuts_calc.py` 側だけ桁数変換が無視される(issue #43)。→ `100` コマンドのプリセットは `a_value: 1, b_value: 1`(グレード1のみ)に限定している。

## 統合ポイント

- 呼び出し元: `GradeDrills.jsx`(`GRADES`/`UNGRADED`/`CUSTOM_GRADE` でナビゲーションを描画、`presetsByGrade[selectedGrade].normal`/`.written`/`.examPrep` でカードを描画)
- 呼び出し先: なし(純粋なデータモジュール)

## 注意事項・既知の制限

- `nuts_calc.py`/`nuts_calc_tex.py`/`web/backend/app.py` 側にパラメータの許可リストバリデーションが薄いため(`docs/L3_implementation/specification_summary.md` 既知の制約)、ここで不正な組み合わせを作らないよう注意する。特に上記のレンダラー相違(issue #41/#42/#43)が解消されるまでは、該当する組み合わせを追加しないこと。
- `written` の内容は学年によって件数・対応演算が異なる(1年生は0件、他学年は1〜3件)。
- `examPrep` は学年4〜6のみ9件ずつ、他は空配列。パラメータの組み合わせは `tests/test_nuts_calc_tex_exam_prep_presets.py` のシミュレーション結果に依存しているため、`buildExamPrepPresets` の桁数・項数・段階の設計を変更する場合はテストと合わせて見直すこと。

## 変更履歴(git log より自動生成)

- 7290008 feat(#73): add entrance-exam-prep drill section for grades 4-6
- 6c2ee20 feat(#69): add ope --missing-value option with grade menu cards
- 1b7e795 feat(#67): add ope --use-parentheses option with grade menu cards
- 7c89a52 feat(#65): add curriculum-aligned fraction worksheets
- b727443 feat(#61): add separate addition and subtraction drills
- 5211d63 feat(#44): rework grade-based drill menu per curriculum, inline written-calculation section, add Ungraded category
- f0201d6 feat(#13): add grade-based written-calculation (hissan) drill menu
- 0631cf9 feat(#5): add grade-based drill PDF picker to web/frontend
