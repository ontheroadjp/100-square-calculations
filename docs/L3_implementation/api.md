# Web API

Flask backend は worksheet 生成と renderer 能力確認の2エンドポイントを提供する。DB は使わず、生成 CLI を subprocess として起動して PDF を返す。この分離により backend は計算問題ロジックを重複実装せず、CLI を唯一の生成実装として再利用する(`backend/app.py:15-58`、`backend/renderers.py:170-189`)。

## `POST /generate-pdf`

### Request

`Content-Type: application/json`。`paper_size` と `command_type` が必須で、欠落時は HTTP 400 を返す(`backend/app.py:17-22`)。

任意フィールドは `RendererRequest` に列挙される(`backend/renderers.py:9-42`)。

- 数値/範囲: `a_value`, `b_value`, `a_min`, `a_max`, `b_min`, `b_max`, `numerator_digits`, `denominator_digits`, `a_decimal_places`, `b_decimal_places`, `decimal_places`, `terms`, `terms_min`, `terms_max`, `rows`, `columns`, `page`
- 演算: `operator`, `a_kind`, `b_kind`(いずれも文字列配列)、`carry_mode`(`required`|`none`|`mixed`)
- flag: `descend`, `reverse`, `shuffle`, `intermediate`, `vertical`, `use_parentheses`, `missing_value`, `mixed_operators`, `same_denominator`, `different_denominators`, `proper_operands`, `proper_result`, `with_bottom_answer`, `merge`, `csv`, `debug`

backend は renderer 互換性を事前検証せず、値を CLI option へ変換する。`carry_mode` だけは3値を allowlist 検証し、それぞれ `--carry`/`--no-carry`/`--mixed-carry` へ変換する。`vertical`、`use_parentheses`、`missing_value`、`terms` 系、小数・mixed 系、`carry_mode` は LaTeX 専用だが、reportlab 選択時にも request に含まれればそのまま渡され、`nuts_calc.py` が unknown option として失敗する。frontend が `GET /renderer-info` で機能を gate する理由はこの差にある。

### Processing and response

`NUTS_CALC_RENDERER` から `reportlab`(default) または `latex` を選び、実行中の Python interpreter (`sys.executable`) と対応 script を使う(`backend/renderers.py:45-69,92-100`)。出力名は `worksheet_<uuid>.pdf` で、`PDF_OUTPUT_DIR` に生成後 `send_file(..., as_attachment=True)` で返す(`backend/app.py:11-13,24-34`、`backend/renderers.py:182-189`)。

| 条件 | Status | Body |
|---|---:|---|
| 成功 | 200 | PDF attachment |
| JSON なし / 必須値欠落 | 400 | `{ "error": "..." }` |
| renderer 設定/CLI 実行/ファイル/予期しない例外 | 500 | `{ "error": "..." }` |

CLI は validation error を stdout に出すため、`CalledProcessError` 時は stdout を stderr より優先してエラー本文へ使う(`backend/app.py:39-44`)。

## `GET /renderer-info`

入力なし。有効な renderer を `{ "renderer": "reportlab" }` または `{ "renderer": "latex" }` として返す(`backend/app.py:52-58`)。`NUTS_CALC_RENDERER` が未設定なら `reportlab`、許可外なら HTTP 500 と error JSON になる(`backend/renderers.py:48-69`)。

## 永続化と未確認事項

- DB、認証、rate limit は実装されていない。CORS は引数なしの `CORS(app)` で有効化される(`backend/app.py:8-13`)。
- 生成 PDF の削除処理は確認できない。`generated_pdfs/` の保持/清掃方針を確定するには repo 外の運用設定が必要である。
- Flask を実プロセス起動して frontend と接続する E2E はない。現行テストは Flask test client と renderer 純粋関数を対象とする(`backend/tests/test_web_backend_app.py`、`backend/tests/test_web_backend_renderers.py`)。
