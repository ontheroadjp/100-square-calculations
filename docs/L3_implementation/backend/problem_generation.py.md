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

## 統合ポイント

- 呼び出し元: `backend/app.py` の `POST /generate-problems` ルートハンドラ。
- 呼び出し先: `backend/nuts_calc.py`(`get_operation_data`/`set_min_max_value`/`SINGLE_DIGIT_MAX`)、`backend/nuts_calc_tex.py`(`generate_ope_problems`/`build_intermediate_memo`/`MIN_DECIMAL_PLACES`/`INTERMEDIATE_SINGLE_DIGIT_MAX`)、`backend/renderers.py`(`get_renderer_name`、`RendererRequest` 型)。

## 注意事項・既知の制限

- `carry_mode`/`remainder_mode`/`result_max`/`a_decimal_places`/`b_decimal_places` は latex レンダラー専用パラメータ(`nuts_calc.py` に対応実装がない)。reportlab選択時にこれらが送られても本モジュールは無視する(`renderers.py`の`build_command`と同じ「呼び出し元がレンダラー情報に基づいて送信可否を制御する」契約を踏襲、明示的なエラーにはしていない)。
- reportlab側の `remainder` は常に `0`(`nuts_calc.py`の`calc_div`は正確に割り切れる組み合わせしか生成しないため、余り制御の概念がない)。latex側は `remainder_mode` 指定に応じて非ゼロになりうる。
- `nuts_calc.py`/`nuts_calc_tex.py` は完全に独立したスクリプトのままで、本ファイルはその両方を `import` する(サブプロセスではなく通常のPythonインポート)。両スクリプトとも `if __name__ == '__main__':` ガード済みのため、importしただけではCLI実行や副作用は発生しない。

## 変更履歴(git log より自動生成)

(新規ファイル。issue #138 で追加)
