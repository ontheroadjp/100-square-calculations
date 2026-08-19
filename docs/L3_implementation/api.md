# Web API

Flask backend は worksheet 生成(PDF)・問題データのみ生成(JSON、issue #138)・renderer 能力確認の3エンドポイントを提供する。DB は使わない。`POST /generate-pdf` は生成 CLI を subprocess として起動して PDF を返し、backend はこの生成ロジックを重複実装しない(`backend/app.py:15-50`、`backend/renderers.py:170-189`)。`POST /generate-problems`(`command_type='ope'` のみ対応)は例外で、CLI を subprocess 起動せず、`backend/problem_generation.py` が CLI スクリプト内の既存データ生成関数をプロセス内で直接呼び出す(`backend/problem_generation.py:53-91`)。

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

`Content-Type: application/json`。`paper_size`、`command_type`(現時点では `'ope'` のみ)、`num`(生成する問題数、正の整数)が必須で、いずれか欠落・`num` が不正な場合は HTTP 400 を返す(`backend/app.py`)。それ以外の任意フィールドは `POST /generate-pdf` と同じ `RendererRequest` を使う。

### Processing and response

`renderers.get_renderer_name()` で解決した renderer(`reportlab`/`latex`)に応じて `backend/problem_generation.py` の `_generate_ope_problems_reportlab`/`_generate_ope_problems_latex` を呼ぶ。両者とも `nuts_calc.py`/`nuts_calc_tex.py` の既存データ生成関数をプロセス内で直接呼び出すのみで、subprocess は起動せず PDF/LaTeX ファイルも生成しない(`backend/problem_generation.py:53-91`)。

| 条件 | Status | Body |
|---|---:|---|
| 成功 | 200 | `{ "problems": [...] }` |
| JSON なし / 必須値欠落・`num` 不正 | 400 | `{ "error": "..." }` |
| `command_type` が `'ope'` 以外、未対応の `ope` 亜種フラグ、その他データ層のエラー | 500 | `{ "error": "..." }` |

`ope` の `--use-parentheses`/`--missing-value`/`--terms`系/`--mixed-operators`、および `'ope'` 以外の `command_type` は明示的に拒否される(issue #166 のsub-issueで追って対応)。

## `GET /renderer-info`

入力なし。有効な renderer を `{ "renderer": "latex" }` として返す(`backend/app.py:78-84`)。`NUTS_CALC_RENDERER` が未設定なら `latex`(issue #186 で `reportlab` から変更)、許可外の値、または明示的な `reportlab`(issue #186 で到達不能化、コードは削除していない)なら HTTP 500 と error JSON になる(`backend/renderers.py:90-107`)。

## 永続化と未確認事項

- DB、認証、rate limit は実装されていない。CORS は引数なしの `CORS(app)` で有効化される(`backend/app.py:8-13`)。
- 生成 PDF の削除処理は確認できない。`generated_pdfs/` の保持/清掃方針を確定するには repo 外の運用設定が必要である。
- Flask を実プロセス起動して frontend と接続する E2E はない。現行テストは Flask test client と renderer 純粋関数を対象とする(`backend/tests/test_web_backend_app.py`、`backend/tests/test_web_backend_renderers.py`)。
