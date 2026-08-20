# Web API

Flask backend は worksheet 生成(PDF)・問題データのみ生成(JSON、issue #138)・renderer 能力確認の3エンドポイントを提供する。DB は使わない。`POST /generate-pdf` は移行済み command/variant(`divfrac`/`simplify` を含む)を `nuts_calc_tex.py` の内部 presentation API で生成し、未移行 command/variant だけを `backend/renderers.py` の CLI/subprocess 経路へフォールバックする hybrid routing である(`backend/app.py:90-187,265-327,1037-1326,1330-1395`)。`POST /generate-problems`(`command_type` は `'ope'`/`'com'`/`'99'`/`'aBc'`/`'squ'`/`'pi'`/`'frac'`/`'mixed'`/`'compare'`/`'evenodd'`/`'multiples'`/`'divisors'`/`'lcm'`/`'gcd'`/`'simplify'`/`'commondenom'`/`'frac2dec'`/`'dec2frac'`/`'divfrac'` に対応、`'100'` は対象外)も CLI を subprocess 起動せず、`backend/problem_generation.py` が既存データ生成関数を直接呼び出す。

## `POST /generate-pdf`

### Request

`Content-Type: application/json`。`paper_size` と `command_type` が必須で、欠落時は HTTP 400 を返す(`backend/app.py:17-22`)。

任意フィールドは原則として `RendererRequest` に列挙される(`backend/renderers.py:9-58`)。`multiples_count` は既存の `multiples` data/CLI contract として、内部 API 経路の `_generate_multiples_pdf` が追加で直接読む。

- 数値/範囲: `a_value`, `b_value`, `a_digits`, `b_digits`, `a_min`, `a_max`, `b_min`, `b_max`, `result_max`, `numerator_digits`, `denominator_digits`, `a_decimal_places`, `b_decimal_places`, `decimal_places`, `terms`, `terms_min`, `terms_max`, `rows`, `columns`, `page`。`multiples` 内部 API 経路はさらに `multiples_count` を受け付ける。
- 演算: `operator`, `a_kind`, `b_kind`(いずれも文字列配列)、`carry_mode`/`remainder_mode`(`required`|`none`|`mixed`)
- flag: `descend`, `reverse`, `shuffle`, `intermediate`, `vertical`, `use_parentheses`, `missing_value`, `mixed_operators`, `same_denominator`, `different_denominators`, `proper_operands`, `proper_result`, `with_bottom_answer`, `merge`, `csv`, `debug`

backend は renderer 互換性を事前検証せず、値を CLI option へ変換する。`carry_mode`/`remainder_mode` は3値をallowlist検証し、対応する `--carry-borrow` 系/`--remainder` 系フラグへ変換する。`result_max` は `--result-max` へ変換する。これらと `vertical`、`use_parentheses`、`missing_value`、`terms` 系、小数・mixed 系は LaTeX 専用パラメータで、`nuts_calc_tex.py` のみが解釈する。旧 ReportLab CLI(`nuts_calc.py`、issue #232 で削除)が選択可能だった頃は、これらが request に含まれればそのまま渡され `nuts_calc.py` が unknown option として失敗していた(frontend が `GET /renderer-info` で機能を gate していた理由はこの差にあった)。現在は `latex` が唯一到達可能なレンダラーのため実害はないが、`build_command()` 自体は将来の別レンダラーに備えてレンダラー非依存のまま値を無条件変換する設計を維持している(`backend/renderers.py:107-`)。

### Processing and response

`com`/`lcm`/`divfrac`/`gcd`/`evenodd`/`99`/`aBc`/`pi`/移行済み `ope` variants/`squ`/`multiples`/`divisors`/`frac`/`simplify` と基本2項 `mixed` は対応する `_generate_*_pdf` helper から `build_presentation_document_tex` と選択済み `LatexEngineAdapter` をプロセス内で直接呼ぶ。それ以外は `NUTS_CALC_RENDERER` から `latex` を選び、実行中の Python interpreter と CLI script を subprocess 起動する。`mixed` の terms系・`mixed_operators`・`reducible_mode` variants は明示的に subprocess を維持する。内部 API 経路は既定の1ページ blank basic-caseで、出力名は両経路とも `worksheet_<uuid>.pdf`、`PDF_OUTPUT_DIR` に生成後 `send_file(..., as_attachment=True)` で返す(`backend/app.py:90-187,265-327,1037-1326,1330-1395`)。

| 条件 | Status | Body |
|---|---:|---|
| 成功 | 200 | PDF attachment |
| JSON なし / 必須値欠落 | 400 | `{ "error": "..." }` |
| renderer 設定/CLI 実行/ファイル/予期しない例外 | 500 | `{ "error": "..." }` |

CLI は validation error を stdout に出すため、`CalledProcessError` 時は stdout を stderr より優先してエラー本文へ使う(`backend/app.py:39-44`)。

## `POST /generate-problems`(issue #138)

### Request

`Content-Type: application/json`。`paper_size`、`command_type`(`'ope'`/`'com'`/`'99'`/`'aBc'`/`'squ'`/`'pi'`/`'frac'`/`'mixed'`/`'compare'`/`'evenodd'`/`'multiples'`/`'divisors'`/`'lcm'`/`'gcd'`/`'simplify'`/`'commondenom'`/`'frac2dec'`/`'dec2frac'`/`'divfrac'` に対応)、`num`(生成する問題数、正の整数)が必須で、いずれか欠落・`num` が不正な場合は HTTP 400 を返す(`backend/app.py`)。それ以外の任意フィールドは `POST /generate-pdf` と同じ `RendererRequest` を使う。`com`/`99`/`squ`/`pi` は `a_value` も必須(`com` はさらに最小値 `nuts_calc_tex.MIN_COMPLEMENT_TARGET` 以上)。`frac`/`mixed`/`compare`/`simplify`/`commondenom`/`frac2dec` は `numerator_digits`/`denominator_digits`(既定1、範囲1〜3)、`operator` 等の CLI 相当パラメータを任意で受け付け、`nuts_calc_tex.py` の `_init()` と同じバリデーション(排他フラグ・digit 制約・`reducible_mode` の operator/operand-kind 制約、`compare` は `comparison_pattern`+非既定 kind の組み合わせ制約)を再現する。`multiples`/`divisors` は `a_min`(既定1)が1未満だと拒否し、`multiples` はさらに `multiples_count`(既定 `nuts_calc_tex.DEFAULT_MULTIPLES_COUNT`)が `nuts_calc_tex.MIN_MULTIPLES_COUNT` 未満だと拒否する。`lcm`/`gcd`/`divfrac` は `a_digits`/`b_digits` ショートハンドに対応する(issue #230。`a_value`/`b_value` はこの3コマンドでは読まれない。`evenodd`/`multiples`/`divisors` は `a_digits` にも非対応で `a_min`/`a_max` を直接使う)。`divfrac` はさらに `b_min`(既定1)が1未満だと拒否する(0除算回避)。`dec2frac` は digit 系オプションを受け付けない(小数桁数は `nuts_calc_tex.py` 側の固定レンジからランダムに決まる)。

### Processing and response

`command_type='ope'` の `--use-parentheses`/`--missing-value`/`--terms`系(`terms`/`terms_min`/`terms_max`/`mixed_operators`)が指定された場合、`backend/problem_generation.py` の `_determine_ope_variant()` が対象亜種を判定し(`nuts_calc_tex.py`の`_init()`と同じ相互排他バリデーション・term数レンジ解決を再現)、`_generate_tree_ope_problems`/`_generate_missing_value_problems`/`_generate_multi_term_ope_problems` のいずれかへディスパッチする。いずれも対応する `nuts_calc_tex.py` の既存生成関数をプロセス内で直接呼び出すのみで、subprocess は起動せず PDF/LaTeX ファイルも生成しない。亜種フラグが指定されない場合は `_generate_ope_problems_latex` を呼ぶ(`backend/problem_generation.py:63-71`)。issue #232 以前は `renderers.get_renderer_name()` で解決した renderer(`reportlab`/`latex`)に応じて `_generate_ope_problems_reportlab`/`_generate_ope_problems_latex` のいずれかへ分岐していたが、`nuts_calc.py`/reportlab のコード削除に伴いこの分岐自体を削除し、`ope` も他の非-`ope` コマンドと同じく単一実装になった。`ope` 以外(`com`/`99`/`aBc`/`squ`/`pi`/`frac`/`mixed`/`compare`/`evenodd`/`multiples`/`divisors`/`lcm`/`gcd`/`simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac`)は `_COMMAND_GENERATORS` ディスパッチテーブル(`backend/problem_generation.py:587-606`)経由で対応する生成関数へ振り分けられ、renderer 分岐は持たない(常に `nuts_calc_tex.py` を呼ぶ)。`lcm`/`gcd` は共有ヘルパー `_generate_number_pair_problems(params, num, compute)` を `compute=math.lcm`/`math.gcd` で呼び分けるだけの薄いラッパー経由で振り分けられる。`simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac` はいずれも対応する `nuts_calc_tex.py` の既存生成関数をそのまま呼び出すだけの薄いラッパー(`_generate_simplify_problems`/`_generate_commondenom_problems`/`_generate_frac2dec_problems`/`_generate_dec2frac_problems`/`_generate_divfrac_problems`、`backend/problem_generation.py:568-615`)。

item の形状はコマンド・亜種ごとに異なる(issue #167 で決定した JSON contract: dataclass のフィールド名をそのまま JSON key にする): `ope` の `--use-parentheses` は `{index, operands, operators, tree, result}`(`tree` はネストした式木)、`--terms`系は `{index, operands, operators, mixed, result}`、`--missing-value` は `{index, a, b, operator, c, blank}`。`com` は `{index, a, target, c}`、`99` は `{index, a, b, c}`、`aBc` は `{index, a, b, c, d}`、`squ`/`pi` は `{index, a, c}`。`frac` は `{index, a, b, operator, c, mixed_number_display}`(`a`/`b` は `{numerator, denominator, whole}`、`c` は `{numerator, denominator}`)。`mixed` は `{index, operands, operators, mixed, result}`(`ope`の`--terms`系と同じフィールド名だが、`operands` の各要素は `{kind, display, value, raw_numerator, raw_denominator}` で `value` は `{numerator, denominator}`、`result` も `{numerator, denominator}`)。`compare` は `{index, a, b, relation}`(`a`/`b` は `{numerator, denominator, whole, kind, decimal_places}`、`relation` は `"<"`/`">"`)。`evenodd` は `{index, a, is_even}`、`multiples` は `{index, a, multiples}`(`multiples` は `int` の配列)、`divisors` は `{index, a, divisors}`(`divisors` は昇順 `int` 配列)、`lcm`/`gcd` は `{index, a, b, c}`。`simplify` は `{index, operand, reduced}`(`operand` は `{numerator, denominator, whole}`、`reduced` は `{numerator, denominator}`)、`commondenom` は `{index, a, b, a_converted, b_converted}`(いずれも `{numerator, denominator, whole}`)、`frac2dec` は `{index, operand, decimal_places, scaled_numerator, decimal_display}`(`operand` は `{numerator, denominator, whole}`、`decimal_display` は `@property` を明示キー追加した整形済み小数文字列)、`dec2frac` は `{index, decimal_places, scaled_numerator, reduced, decimal_display}`(`reduced` は `{numerator, denominator}`)、`divfrac` は `{index, a, b}`(未約分の a/b そのものが答えのため専用の結果フィールドは持たない)。標準 `Fraction` フィールドはいずれも `{numerator, denominator}` の2キーへ変換される(`whole` は持たない、issue #170 で `_dataclass_to_dict()` に実装)。

| 条件 | Status | Body |
|---|---:|---|
| 成功 | 200 | `{ "problems": [...] }` |
| JSON なし / 必須値欠落・`num` 不正 | 400 | `{ "error": "..." }` |
| 未対応の `command_type`(`'100'` を含む)、亜種フラグの相互排他違反、`terms_min > terms_max`、`com`/`99`/`squ`/`pi` での `a_value` 欠落・`com` の最小値未満、`frac`/`mixed`/`compare`/`simplify`/`commondenom`/`frac2dec` の digit/排他/operator/operand-kind 制約違反、`compare` の `comparison_pattern`+非既定 kind の組み合わせ、`multiples`/`divisors` の `a_min` 1未満、`multiples` の `multiples_count` 下限未満、`divfrac` の `b_min` 1未満、その他データ層のエラー | 500 | `{ "error": "..." }` |

`ope` の `--use-parentheses`/`--missing-value`/`--terms`系/`--mixed-operators` は issue #168 で対応した。`com`/`99`/`aBc`/`squ`/`pi` は issue #169、`frac`/`mixed` は issue #170、`compare` は issue #171、`evenodd`/`multiples`/`divisors`/`lcm`/`gcd` は issue #172、`simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac` は issue #173 で対応し、issue #166 の全 sub-issue が完了した。`'100'` は単一の `HundredSquareTable` を返すため `{"problems": [...]}` envelope に合わず、意図的に対象外のまま(issue #169、`docs/L3_implementation/backend/problem_generation.py.md` 参照)。

## `GET /renderer-info`

入力なし。有効な renderer を `{ "renderer": "latex" }` として返す(`backend/app.py:78-84`)。`NUTS_CALC_RENDERER` が未設定なら `latex`(issue #186 で `reportlab` から変更)、`latex` 以外の値(`reportlab` を含む。`nuts_calc.py`/reportlab は issue #232 でコード自体が削除された)なら HTTP 500 と error JSON になる(`backend/renderers.py:87-104`)。

## 永続化と未確認事項

- DB、認証、rate limit は実装されていない。CORS は引数なしの `CORS(app)` で有効化される(`backend/app.py:8-13`)。
- 生成 PDF の削除処理は確認できない。`generated_pdfs/` の保持/清掃方針を確定するには repo 外の運用設定が必要である。
- Flask を実プロセス起動して frontend と接続する E2E はない。現行テストは Flask test client と renderer 純粋関数を対象とする(`backend/tests/test_web_backend_app.py`、`backend/tests/test_web_backend_renderers.py`)。
