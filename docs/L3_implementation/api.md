# Web API

Flask backend は worksheet 生成(PDF)・問題データのみ生成(JSON、issue #138)・renderer 能力確認の3エンドポイントを提供する。DB は使わない。`POST /generate-pdf` は生成 CLI を subprocess として起動して PDF を返し、backend はこの生成ロジックを重複実装しない(`backend/app.py:15-50`、`backend/renderers.py:170-189`)。`POST /generate-problems`(`command_type` は `'ope'`/`'com'`/`'99'`/`'aBc'`/`'squ'`/`'pi'`/`'frac'`/`'mixed'`/`'compare'`/`'evenodd'`/`'multiples'`/`'divisors'`/`'lcm'`/`'gcd'` に対応、`'100'` は対象外)は例外で、CLI を subprocess 起動せず、`backend/problem_generation.py` が CLI スクリプト内の既存データ生成関数を `command_type` → 生成関数のディスパッチテーブル経由でプロセス内で直接呼び出す(`backend/problem_generation.py:47-587`)。

## `POST /generate-pdf`

### Request

`Content-Type: application/json`。`paper_size` と `command_type` が必須で、欠落時は HTTP 400 を返す(`backend/app.py:17-22`)。

任意フィールドは `RendererRequest` に列挙される(`backend/renderers.py:9-54`)。

- 数値/範囲: `a_value`, `b_value`, `a_min`, `a_max`, `b_min`, `b_max`, `result_max`, `numerator_digits`, `denominator_digits`, `a_decimal_places`, `b_decimal_places`, `decimal_places`, `terms`, `terms_min`, `terms_max`, `rows`, `columns`, `page`
- 演算: `operator`, `a_kind`, `b_kind`(いずれも文字列配列)、`carry_mode`/`remainder_mode`(`required`|`none`|`mixed`)
- flag: `descend`, `reverse`, `shuffle`, `intermediate`, `vertical`, `use_parentheses`, `missing_value`, `mixed_operators`, `same_denominator`, `different_denominators`, `proper_operands`, `proper_result`, `with_bottom_answer`, `merge`, `csv`, `debug`

backend は renderer 互換性を事前検証せず、値を CLI option へ変換する。`carry_mode`/`remainder_mode` は3値をallowlist検証し、対応する `--carry-borrow` 系/`--remainder` 系フラグへ変換する。`result_max` は `--result-max` へ変換する。これらと `vertical`、`use_parentheses`、`missing_value`、`terms` 系、小数・mixed 系は LaTeX 専用だが、reportlab 選択時にも request に含まれればそのまま渡され、`nuts_calc.py` が unknown option として失敗する。frontend が `GET /renderer-info` で機能を gate する理由はこの差にある(`backend/renderers.py:130-170`)。

### Processing and response

`NUTS_CALC_RENDERER` から `latex`(default、issue #186 で `reportlab` から変更。明示的な `reportlab` 指定は到達不能で「利用不可」エラーになる)を選び、実行中の Python interpreter (`sys.executable`) と対応 script を使う(`backend/renderers.py:61-67,90-107,254-273`)。出力名は `worksheet_<uuid>.pdf` で、`PDF_OUTPUT_DIR` に生成後 `send_file(..., as_attachment=True)` で返す(`backend/app.py:11-13,24-34`、`backend/renderers.py:182-189`)。

| 条件 | Status | Body |
|---|---:|---|
| 成功 | 200 | PDF attachment |
| JSON なし / 必須値欠落 | 400 | `{ "error": "..." }` |
| renderer 設定/CLI 実行/ファイル/予期しない例外 | 500 | `{ "error": "..." }` |

CLI は validation error を stdout に出すため、`CalledProcessError` 時は stdout を stderr より優先してエラー本文へ使う(`backend/app.py:39-44`)。

## `POST /generate-problems`(issue #138)

### Request

`Content-Type: application/json`。`paper_size`、`command_type`(`'ope'`/`'com'`/`'99'`/`'aBc'`/`'squ'`/`'pi'`/`'frac'`/`'mixed'`/`'compare'`/`'evenodd'`/`'multiples'`/`'divisors'`/`'lcm'`/`'gcd'` に対応)、`num`(生成する問題数、正の整数)が必須で、いずれか欠落・`num` が不正な場合は HTTP 400 を返す(`backend/app.py`)。それ以外の任意フィールドは `POST /generate-pdf` と同じ `RendererRequest` を使う。`com`/`99`/`squ`/`pi` は `a_value` も必須(`com` はさらに最小値 `nuts_calc_tex.MIN_COMPLEMENT_TARGET` 以上)。`frac`/`mixed`/`compare` は `numerator_digits`/`denominator_digits`(既定1、範囲1〜3)、`operator` 等の CLI 相当パラメータを任意で受け付け、`nuts_calc_tex.py` の `_init()` と同じバリデーション(排他フラグ・digit 制約・`reducible_mode` の operator/operand-kind 制約、`compare` は `comparison_pattern`+非既定 kind の組み合わせ制約)を再現する。`multiples`/`divisors` は `a_min`(既定1)が1未満だと拒否し、`multiples` はさらに `multiples_count`(既定 `nuts_calc_tex.DEFAULT_MULTIPLES_COUNT`)が `nuts_calc_tex.MIN_MULTIPLES_COUNT` 未満だと拒否する。`lcm`/`gcd` は `a_value`/`b_value` ショートハンドに対応する(`evenodd`/`multiples`/`divisors` は非対応で `a_min`/`a_max` を直接使う)。

### Processing and response

`command_type='ope'` の `--use-parentheses`/`--missing-value`/`--terms`系(`terms`/`terms_min`/`terms_max`/`mixed_operators`)が指定された場合、`backend/problem_generation.py` の `_determine_ope_variant()` が対象亜種を判定し(`nuts_calc_tex.py`の`_init()`と同じ相互排他バリデーション・term数レンジ解決を再現)、`_generate_tree_ope_problems`/`_generate_missing_value_problems`/`_generate_multi_term_ope_problems` のいずれかへディスパッチする。いずれも対応する `nuts_calc_tex.py` の既存生成関数をプロセス内で直接呼び出すのみで、subprocess は起動せず PDF/LaTeX ファイルも生成しない。亜種フラグが指定されない場合は従来どおり `renderers.get_renderer_name()` で解決した renderer(`reportlab`/`latex`)に応じて `_generate_ope_problems_reportlab`/`_generate_ope_problems_latex` を呼ぶ(`backend/problem_generation.py:74-90`)。`ope` 以外(`com`/`99`/`aBc`/`squ`/`pi`/`frac`/`mixed`/`compare`/`evenodd`/`multiples`/`divisors`/`lcm`/`gcd`)は `_COMMAND_GENERATORS` ディスパッチテーブル(`backend/problem_generation.py:573-587`)経由で対応する生成関数へ振り分けられ、renderer 分岐は持たない(常に `nuts_calc_tex.py` を呼ぶ)。`lcm`/`gcd` は共有ヘルパー `_generate_number_pair_problems(params, num, compute)` を `compute=math.lcm`/`math.gcd` で呼び分けるだけの薄いラッパー経由で振り分けられる。

item の形状はコマンド・亜種ごとに異なる(issue #167 で決定した JSON contract: dataclass のフィールド名をそのまま JSON key にする): `ope` の `--use-parentheses` は `{index, operands, operators, tree, result}`(`tree` はネストした式木)、`--terms`系は `{index, operands, operators, mixed, result}`、`--missing-value` は `{index, a, b, operator, c, blank}`。`com` は `{index, a, target, c}`、`99` は `{index, a, b, c}`、`aBc` は `{index, a, b, c, d}`、`squ`/`pi` は `{index, a, c}`。`frac` は `{index, a, b, operator, c, mixed_number_display}`(`a`/`b` は `{numerator, denominator, whole}`、`c` は `{numerator, denominator}`)。`mixed` は `{index, operands, operators, mixed, result}`(`ope`の`--terms`系と同じフィールド名だが、`operands` の各要素は `{kind, display, value, raw_numerator, raw_denominator}` で `value` は `{numerator, denominator}`、`result` も `{numerator, denominator}`)。`compare` は `{index, a, b, relation}`(`a`/`b` は `{numerator, denominator, whole, kind, decimal_places}`、`relation` は `"<"`/`">"`)。`evenodd` は `{index, a, is_even}`、`multiples` は `{index, a, multiples}`(`multiples` は `int` の配列)、`divisors` は `{index, a, divisors}`(`divisors` は昇順 `int` 配列)、`lcm`/`gcd` は `{index, a, b, c}`。標準 `Fraction` フィールドはいずれも `{numerator, denominator}` の2キーへ変換される(`whole` は持たない、issue #170 で `_dataclass_to_dict()` に実装)。

| 条件 | Status | Body |
|---|---:|---|
| 成功 | 200 | `{ "problems": [...] }` |
| JSON なし / 必須値欠落・`num` 不正 | 400 | `{ "error": "..." }` |
| 未対応の `command_type`(`'100'` を含む)、亜種フラグの相互排他違反、`terms_min > terms_max`、`com`/`99`/`squ`/`pi` での `a_value` 欠落・`com` の最小値未満、`frac`/`mixed`/`compare` の digit/排他/operator/operand-kind 制約違反、`compare` の `comparison_pattern`+非既定 kind の組み合わせ、`multiples`/`divisors` の `a_min` 1未満、`multiples` の `multiples_count` 下限未満、reportlab レンダラーへの亜種フラグ指定、その他データ層のエラー | 500 | `{ "error": "..." }` |

`ope` の `--use-parentheses`/`--missing-value`/`--terms`系/`--mixed-operators` は issue #168 で対応した(reportlab レンダラーには `nuts_calc.py` に対応実装がないため明示的に拒否される)。`com`/`99`/`aBc`/`squ`/`pi` は issue #169、`frac`/`mixed` は issue #170、`compare` は issue #171、`evenodd`/`multiples`/`divisors`/`lcm`/`gcd` は issue #172 で対応した。`'100'` は単一の `HundredSquareTable` を返すため `{"problems": [...]}` envelope に合わず、意図的に対象外のまま(issue #169、`docs/L3_implementation/backend/problem_generation.py.md` 参照)。それ以外の `command_type`(`simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac` の残り5コマンド)は引き続き明示的に拒否される(issue #166 の sub-issue #173 で追って対応)。

## `GET /renderer-info`

入力なし。有効な renderer を `{ "renderer": "latex" }` として返す(`backend/app.py:78-84`)。`NUTS_CALC_RENDERER` が未設定なら `latex`(issue #186 で `reportlab` から変更)、許可外の値、または明示的な `reportlab`(issue #186 で到達不能化、コードは削除していない)なら HTTP 500 と error JSON になる(`backend/renderers.py:90-107`)。

## 永続化と未確認事項

- DB、認証、rate limit は実装されていない。CORS は引数なしの `CORS(app)` で有効化される(`backend/app.py:8-13`)。
- 生成 PDF の削除処理は確認できない。`generated_pdfs/` の保持/清掃方針を確定するには repo 外の運用設定が必要である。
- Flask を実プロセス起動して frontend と接続する E2E はない。現行テストは Flask test client と renderer 純粋関数を対象とする(`backend/tests/test_web_backend_app.py`、`backend/tests/test_web_backend_renderers.py`)。
