# `tests/test_web_backend_renderers.py`

## 目的・役割

FlaskバックエンドがPDF生成リクエストを正しいCLI引数へ変換することを検証する。

## 動作概要

`compare` リクエストの `comparison_pattern`、`a_fraction_form`、`b_fraction_form` が、LaTeXレンダラーの対応する3オプションへ変換されることを検証する（`tests/test_web_backend_renderers.py:174-186`）。

## 統合ポイント

対象は `web/backend/renderers.py:build_command()` である。

## 変更履歴(git log より自動生成)

- 9e296ee feat(#83): add fraction comparison worksheets
- bf720ce feat(#81): clarify carry-borrow CLI options
- 1186039 feat(#78): add carry-aware grade 1 drills
- 6889ef0 feat(#76): add decimal ope arithmetic and int/decimal/fraction mixed command
- 7290008 feat(#73): add entrance-exam-prep drill section for grades 4-6
- 6c2ee20 feat(#69): add ope --missing-value option with grade menu cards
- 7c89a52 feat(#65): add curriculum-aligned fraction worksheets
- 8062b9f fix(#36): invoke the running interpreter (sys.executable) instead of hardcoded python3
- 155caf8 feat(#36): switch web/backend renderer between nuts_calc.py and nuts_calc_tex.py via env var
