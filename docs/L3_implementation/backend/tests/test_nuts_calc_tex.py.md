# `backend/tests/test_nuts_calc_tex.py`

## 目的・役割

`nuts_calc_tex.py` の end-to-end 回帰テスト。CLI をサブプロセスとして実際に起動し、`_init()` のバリデーション、PDF/CSV 出力、各コマンド(`ope`/`com`/`99`/`aBc`/`squ`/`pi`/フラグ系/数論系/分数変換系)の実際の生成結果を検証する。`nuts_calc_tex.py` は `nuts_calc.py` とコード共有がゼロのため、`tests/test_nuts_calc_cli.py`(`nuts_calc.py` 向け)とは独立している。

## 動作の概要

- `pytestmark = pytest.mark.skipif(shutil.which("pdflatex") is None, ...)` により、モジュール全体が `pdflatex` 未検出環境で自動スキップされる(`backend/tests/test_nuts_calc_tex.py:51-54`)。
- `run_tex_cli` フィクスチャ(`backend/tests/test_nuts_calc_tex.py:124-140`)が `subprocess.run([sys.executable, NUTS_CALC_TEX, *args], cwd=tmp_path, ...)` で CLI を実サブプロセス起動し、相対 `--out-file` を `tmp_path` に隔離する。
- `_assert_is_pdf`/`_pdf_page_count` ヘルパーが生成物を検証する。
- CLI の純粋関数(ロジックのみ、pdflatex 不要な部分)のテストは `test_nuts_calc_tex_ope_generation.py` 等の姉妹ファイルに分離されている(モジュール docstring 参照)。

## 重要な設計判断とその理由

### `--carry-borrow` 系フラグと小数オペランドの併用(issue #113)

- `test_cli_ope_add_carry_flags_work_with_decimal_places`/`test_cli_ope_sub_carry_borrow_works_with_decimal_places`/`test_cli_ope_mixed_carry_borrow_works_with_decimal_places` は、`ope --carry-borrow`/`--no-carry-borrow`/`--mixed-carry-borrow` と `--a-decimal-places`/`--b-decimal-places` の併用が成功し、CSV 上の値が正しく繰り上がり/繰り下がりしていることを検証する。既存の整数専用 carry テスト(`test_cli_ope_add_carry_flags_override_impossible_ranges` 等)と対になる。
- CSV の `a`/`b`/`result` フィールドは `format_decimal_value` で小数点が挿入された文字列(例 `"4.7"`)なので、`round(float(value) * 10 ** places)` でスケール済み整数へ戻してから `addition_has_carry`/`subtraction_has_borrow` で検証する(`int()` による切り捨てだと浮動小数点誤差で桁がずれる可能性があるため `round()` を使う)。
- `--remainder`/`--no-remainder`/`--mixed-remainder`(除算の余り制御)は小数オペランドとの併用を引き続き拒否する。issue #113 のスコープは加減算の `--carry-borrow` 系に限定され、除算の余り制御は対象外(`docs/L3_implementation/backend/nuts_calc_tex.py.md` 参照)。

### `--vertical` と小数オペランドの併用(issue #134)

- `test_cli_ope_decimal_rejects_vertical_combo`(小数+`--vertical`を一律拒否することを検証する失敗系テスト)を、実際にPDFが生成されることを検証する正常系テストへ置き換えた:
  - `test_cli_ope_decimal_add_sub_mul_vertical_produces_pdfs`(足し算/引き算/掛け算、対称小数桁数)
  - `test_cli_ope_decimal_multiply_by_integer_vertical_produces_pdfs`(小数×整数)
  - `test_cli_ope_decimal_divide_by_integer_vertical_produces_pdfs`(小数÷整数)
  - `test_cli_ope_decimal_multiply_by_decimal_vertical_produces_pdfs`(小数×小数)
  - いずれも既存の `test_cli_ope_vertical_add_sub_mul_produces_pdfs`/`test_cli_ope_vertical_div_produces_pdfs` と同じ `_assert_is_pdf` パターン(実際に `pdflatex` を通し PDF/CSV が生成されることを検証)。
- `test_cli_ope_decimal_rejects_vertical_with_decimal_divisor` を新設し、`div` オペレーターかつ `--b-decimal-places > 0`(小数÷小数)の組み合わせだけは引き続き明示的に拒否されることを検証する(除数に整数しか受け付けない vendor済み `longdivision` の制約。issue #180 で対応方針を検討中、`docs/L3_implementation/backend/nuts_calc_tex.py.md` 参照)。

### `--a-digits`/`--b-digits` の新設と `-a/--a-value` の桁数解釈廃止(issue #230)

- `ope`/`100`/`lcm`/`gcd`/`divfrac` の桁数ショートハンドを検証していた既存テストは、CLI引数 `--a-value <N>`/`--b-value <N>`(long form)または `-a <N>`(`100`/`lcm`/`gcd`/`divfrac` の short form)から `--a-digits <N>`/`--b-digits <N>` へ全面的に置き換えた。`com`/`99`/`squ`/`pi` の `-a` は値そのものの意味のままなので無変更。
- `test_cli_ope_no_longer_reads_a_value_as_digit_count`: 回帰テスト。`ope --a-value 99` は(旧実装では `set_min_max_value(99)` が `IndexError` で未処理クラッシュしていたが)`a_value` を一切読まなくなったため、単に無視されて正常終了することを検証する。
- `test_cli_ope_a_digits_sets_the_range`: `--a-digits`/`--b-digits` が実際に CSV 出力のオペランド範囲へ反映されることを検証する。
- `test_cli_com_ignores_unrelated_a_digits_flag`: `com` に `--a-digits` を渡しても(`com` はこのフィールドを一切読まないため)無視され、既存の `-a`(補数ターゲット)の挙動に影響しないことを検証する。「渡されたら拒否」ではなく「渡されても単に無視される」という issue #230 の設計方針の検証。

## 統合ポイント

- テスト対象: `backend/nuts_calc_tex.py`(CLI エントリポイント全体)。
- 実行方法: `cd backend && python3 -m pytest -q tests/test_nuts_calc_tex.py`(`pdflatex` が PATH 上に必要)。

## 注意事項・既知の制限

- `pdflatex` が無い環境ではモジュール全体がスキップされ、CIでの検証は行われない(no CI 定義、`docs/.ai/repo.profile.json` の `notes.ci` 参照)。
- 実サブプロセス起動 + LaTeX コンパイルを伴うため、他のテストファイルに比べて実行時間が長い(フルスイートで約2分)。

## 変更履歴（git log より自動生成）

- f5656c4 feat(#313): add mixed decimal operand order to grade 4 integer/decimal multiplication
- 3b6bc6c refactor(#230): split a_value/b_value's overloaded digit-count/direct-value semantics into a_digits/b_digits
- 490f44b #171 compare: support int/decimal/fraction kind mixing, expose via POST /generate-problems (#192)
- 19fc419 test: default nuts_calc_tex.py E2E fixture to pdflatex, not lualatex
- 9393898 #186 renderers/engine: make latex+lualatex the default (and only reachable) configuration (#187)
- 231bde1 #134 frontend/web: add 出題形式 (式/筆算) setting to add/sub/mul/div preset detail pages (#181)
- 7b064ef #114 nuts_calc_tex.py: add reducibility control to frac/mixed multiplication and division (#165)
- bc0eef5 #113 nuts_calc_tex.py: allow --carry-borrow with decimal operands (#164)
- e8db9d7 #112 nuts_calc_tex.py: add mixed-number (帯分数) display support to the frac command (#125)
- 241b2e1 #96 nuts_calc_tex.py: add fraction/decimal conversion drill commands (#108)
