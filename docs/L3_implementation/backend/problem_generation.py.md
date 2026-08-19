# `backend/problem_generation.py`

## 目的・役割

`backend/app.py` の `POST /generate-problems` エンドポイント(issue #138)が呼び出す、PDF/LaTeX を一切生成しない「問題データのみ生成」ロジック。`renderers.py`(サブプロセス経由で `nuts_calc.py`/`nuts_calc_tex.py` を実行し PDF を作る、プレゼンテーション層)とは責務を分離した、データ層のモジュール。issue #166「データ層とプレゼンテーション層の分離」の最初の実装であり、以降の他コマンド対応は同issue配下の native sub-issue(#167-#174)で扱う。

現時点では `command_type == 'ope'` の素の2項四則演算(`--use-parentheses`/`--missing-value`/`--terms*`/`--mixed-operators` を伴わない形)のみに対応する。それ以外の `command_type`、および上記の `ope` 亜種フラグは `ValueError` を送出する。

## 動作の概要

- `generate_problems(params, renderer_name=None)`(公開関数): `renderer_name` 省略時は `renderers.get_renderer_name()` で解決。`command_type` が `'ope'` 以外、または `UNSUPPORTED_OPE_VARIANT_FLAGS`(`use_parentheses`/`missing_value`/`terms`/`terms_min`/`terms_max`/`mixed_operators`)のいずれかが truthy な場合は `ValueError` を送出する(`problem_generation.py:53-70`)。`num`(生成する問題数)が正の整数でない場合も `ValueError`。
- レンダラーごとに `_generate_ope_problems_reportlab`/`_generate_ope_problems_latex` に分岐し、`nuts_calc.py`/`nuts_calc_tex.py` の**既存の純粋データ生成関数をプロセス内で直接呼び出す**(サブプロセスを起動しない、PDF/LaTeXファイルを一切生成しない)。
    - reportlab: `nuts_calc.get_operation_data(nums_a, nums_b, operator, order=num, print_index=1, intermediate=intermediate)` をそのまま呼び出し、戻り値のタプル(`data_index, vals_a, operator_mark, vals_b, equal_marks, vals_c`、`intermediate=True` 時はさらに `vals_aabb` を含む8要素)を1問題1dictへ変換する。演算子記号(`+`/`-`/`×`/`÷`)は `SYMBOL_TO_OPERATOR_NAME` で `add`/`sub`/`mul`/`div` へ正規化する(latex側の表現と統一するための表示用マッピングであり、生成ロジックの複製ではない)。
    - latex: `nuts_calc_tex.generate_ope_problems(...)` を呼び出し、返る `OpeProblem` dataclass のリストをそのままdictへ変換する。`intermediate=True` の場合は `nuts_calc_tex.build_intermediate_memo(a, b)`(既存の純粋関数、LaTeXマークアップを含まないプレーンテキストを返す)を再利用してメモ文字列を追加する。
- `a_value`/`b_value`(桁数指定のショートハンド)は `nuts_calc.set_min_max_value()`(後述、両レンダラーで共用)経由で `a_min`/`a_max`/`b_min`/`b_max` に変換する。指定がなければ `a_min=1`/`a_max=9`/`b_min=1`/`b_max=9`(両CLIのデフォルトと同値)を使う。
- `intermediate=True` の場合、`operator == ['mul']` かつ `b_max <= SINGLE_DIGIT_MAX`(reportlab)/`INTERMEDIATE_SINGLE_DIGIT_MAX`(latex、いずれも値は9)であることを検証し、`_init()` の CLI バリデーションと同じ制約を(`exit(1)` ではなく)`ValueError` として再現する。

## 重要な設計判断とその理由

### サブプロセス+`--csv`読み取りではなく、プロセス内直接呼び出しを選んだ理由

当初は `--csv` フラグを付けてサブプロセス実行し、生成された PDF を破棄して CSV だけ読み取る案を検討したが、「データ層とプレゼンテーション層を完全に分離したい」という将来方針(issue #166)に反する(PDFを一度実際に生成してから捨てる無駄が残り、CSVの列構成もコマンドごとにバラバラで意味づけできない)ため却下した。`get_operation_data()`/`generate_ope_problems()` がどちらも PDF/LaTeX 非依存の純粋関数だったため、プロセス内直接呼び出しが可能だった。

### `nuts_calc.set_min_max_value()` を両レンダラーで共用している理由

`nuts_calc.py`/`nuts_calc_tex.py` は元々それぞれ独立に同一の桁数→範囲テーブルを `_init()` 内にネストした関数として持っていた(コード共有なしの2スクリプトのため)。今回 `nuts_calc.py` 側だけをモジュールレベル関数に抽出し(`nuts_calc.py:90-95`)、`nuts_calc_tex.py` は変更していない。latex分岐でも同じ関数を再利用しているのは、2つの完全に同一のテーブルを本ファイルに二重に持つよりも、既存の(モジュールレベル化済みの)実装を再利用する方が「複製しない」原則に合うと判断したため。`nuts_calc_tex.py` 自身の `_init()` 内の同名ネスト関数はそのまま残っている(CLIパスは変更していない)。

### `ope` 以外・`ope` 亜種を明示的に `ValueError` で拒否している理由

`frac`/`mixed`/`compare` 等の残り19コマンド、および `ope` の `--use-parentheses`/`--missing-value`/多項formatは、それぞれ別の生成関数を使い、出力の型(fraction・真偽値・リスト等)も `ope` の a/b/operator/result 形とは異なる。1つのissue(#138)でこれら全てを実装すると、データ層のレスポンス形状(envelope)の設計判断を全コマンド分一度に確定させることになりスコープが過大になるため、issue #166 のsub-issue群(#167でアーキテクチャ決定、#168-#173で各コマンド群)へ意図的に分割した。未対応の呼び出しは黙って無視/変換せず、明示的なエラーメッセージ(該当issue番号付き)で失敗させる。

### 非-`ope` コマンド群向け JSON contract 規約(issue #167、未実装・設計のみ)

issue #166 の sub-issue #167 で、残り約19個の `nuts_calc_tex.py` コマンド生成関数(`generate_com_problems`/`generate_kuku_problems`/`generate_abc_problems`/`generate_squ_problems`/`generate_pi_problems`/`generate_evenodd_problems`/`generate_multiples_problems`/`generate_divisors_problems`/`generate_fraction_problems`/`generate_fraction_comparison_problems`/`generate_mixed_problems`/`generate_number_pair_problems`/`generate_simplify_problems`/`generate_commondenom_problems`/`generate_frac2dec_problems`/`generate_dec2frac_problems`/`generate_divfrac_problems`、および `--use-parentheses`/`--missing-value`/多項系の `generate_tree_ope_problems`/`generate_multi_term_ope_problems`/`generate_missing_value_problems`)を `backend/problem_generation.py` へ本実装する #168-#173 が従う契約を以下のとおり決定した(このセクション自体はコード変更を伴わない設計記録)。

- **envelope**: `{"problems": [...]}` を変更しない(#138 踏襲)。item の形状はコマンド群ごとに異なってよい(単一の汎用スキーマには寄せない)。
- **item マッピング**: dataclass のフィールド名をそのまま JSON key として使う(`dataclasses.fields()` 相当の1:1変換)。非JSONネイティブな値型は以下のとおり変換する:
    - 標準 `Fraction`(`fractions` モジュール) → `{"numerator": f.numerator, "denominator": f.denominator}`(2キー、`whole` は持たない)。
    - `FractionOperand`/`FractionComparisonOperand`(`nuts_calc_tex.py:3207-3216`/`3466-3476`。いずれも既に `numerator`/`denominator`/`whole`(既定0)を持つ) → そのフィールドをそのまま JSON へ写す(3キー)。`Fraction` 変換と別形状なのは、`FractionOperand` 側だけが混合数の整数部(`whole`)概念を持つため。
    - ネストした dataclass(例: `TreeOpeProblem.tree: ExprTreeNode`、`nuts_calc_tex.py:1668-1686`)は同じ規則を再帰適用する(`left`/`right` が `None` なら `null`、`ExprTreeNode` ならネストした dict)。専用の木シリアライズ形式は起こさない。この項目は #168(`ope` variants)が最初の消費者になる想定。
    - `list[int]`/`list[str]` フィールド(`MultiplesProblem.multiples`/`DivisorsProblem.divisors`/`MultiTermOpeProblem.operands` 等)はそのまま JSON 配列にする。
- **計算プロパティ(`@property`)の扱い**: 上記の汎用変換は dataclass の実フィールドのみを対象とし、`EvenOddProblem.label`/`AbcProblem.abcd_display`/`AbcProblem.answer`/`FractionComparisonProblem.relation`/`Frac2DecProblem.decimal_display`/`Dec2FracProblem.decimal_display` のような派生プロパティは**自動では含めない**。各 family の sub-issue が、クライアント側でのロジック再実装(例: 偶数/奇数の日本語ラベルを JS 側で持つ)を避けたい場合にのみ、明示的な追加 key として個別に採用するかどうかを判断する。既存の `OpeProblemData.intermediate_memo`(`problem_generation.py:47`、`_generate_ope_problems_latex` が `nuts_calc_tex.build_intermediate_memo` を再利用して追加)がこのパターンの先例。
- **未対応の組み合わせのエラー**: 既存の `UNSUPPORTED_OPE_VARIANT_FLAGS` と同じ「issue番号付き `ValueError`」パターンを継続する。新規 family もサポート外のフラグ組み合わせを黙って無視・変換せず、明示的に失敗させる。
- **`command_type` の許可判定**: 現在の `if command_type != 'ope': raise`(`problem_generation.py:58-62`)を、`command_type` → 生成関数のディスパッチテーブルに置き換える。各 sub-issue は「関数を1つ追加し、テーブルに1エントリ追加する」だけで済み、共有の if/elif チェーンを編集しない(#168-#173 が並行作業してもコンフリクトしにくい)。`nuts_calc_tex.py` 側で既にジェネレータを共有しているコマンド群(例: `lcm`/`gcd` は `generate_number_pair_problems(compute, nums_a, nums_b, order, start_index)` を `compute=math.lcm`/`math.gcd` で呼び分けるだけ、`nuts_calc_tex.py:3821-3892`)は、`problem_generation.py` 側でも1関数を共有してよい。
- **reportlab 分岐は持たない**: `nuts_calc.py` は `['ope', 'com', '100', '99', 'aBc', 'squ', 'pi']` の7コマンドのみを実装しており(`nuts_calc.py:131`)、#167-#173 が対象とする残りコマンドは元から reportlab 側に存在しない。加えて `renderers.get_renderer_name()`(`renderers.py:90-108`)は `NUTS_CALC_RENDERER=reportlab` が明示指定された場合、`problem_generation.generate_problems()` に到達する前(`app.py`の`generate_problems`ハンドラ内)に `ValueError` を送出する(issue #186 以降)。したがって本番の HTTP 経路で `problem_generation.generate_problems()` に渡る `renderer_name` は常に `'latex'` であり、新規 family の生成関数は `_generate_ope_problems_reportlab`/`_generate_ope_problems_latex` のような二重実装を持たず、`nuts_calc_tex.py` を直接呼び出すだけでよい。
- **ファイル構成**: 当面は `problem_generation.py` を単一ファイルのまま維持する(パッケージ分割は本ファイルが概ね800行を超えた時点で再検討する)。

## 統合ポイント

- 呼び出し元: `backend/app.py` の `POST /generate-problems` ルートハンドラ。
- 呼び出し先: `backend/nuts_calc.py`(`get_operation_data`/`set_min_max_value`/`SINGLE_DIGIT_MAX`)、`backend/nuts_calc_tex.py`(`generate_ope_problems`/`build_intermediate_memo`/`MIN_DECIMAL_PLACES`/`INTERMEDIATE_SINGLE_DIGIT_MAX`)、`backend/renderers.py`(`get_renderer_name`、`RendererRequest` 型)。

## 注意事項・既知の制限

- `carry_mode`/`remainder_mode`/`result_max`/`a_decimal_places`/`b_decimal_places` は latex レンダラー専用パラメータ(`nuts_calc.py` に対応実装がない)。reportlab選択時にこれらが送られても本モジュールは無視する(`renderers.py`の`build_command`と同じ「呼び出し元がレンダラー情報に基づいて送信可否を制御する」契約を踏襲、明示的なエラーにはしていない)。
- reportlab側の `remainder` は常に `0`(`nuts_calc.py`の`calc_div`は正確に割り切れる組み合わせしか生成しないため、余り制御の概念がない)。latex側は `remainder_mode` 指定に応じて非ゼロになりうる。
- `nuts_calc.py`/`nuts_calc_tex.py` は完全に独立したスクリプトのままで、本ファイルはその両方を `import` する(サブプロセスではなく通常のPythonインポート)。両スクリプトとも `if __name__ == '__main__':` ガード済みのため、importしただけではCLI実行や副作用は発生しない。

## 変更履歴(git log より自動生成)

- a29ed4a feat(#138): add POST /generate-problems for PDF-free ope problem generation
