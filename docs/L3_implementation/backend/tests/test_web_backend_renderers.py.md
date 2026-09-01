# `backend/tests/test_web_backend_renderers.py`

## 目的・役割

FlaskバックエンドがPDF生成リクエストを正しいCLI引数へ変換することを検証する。

## 動作概要

`build_command()` の位置引数、値付きオプション、真偽フラグ、LaTeX専用パラメーター変換を検証する。`test_build_command_translates_a_digits_and_b_digits`(issue #230)は新設の `a_digits`/`b_digits` が `--a-digits`/`--b-digits` へ変換されることを検証する(既存の `a_value` パススルーとは独立、`build_command()` はいずれの意味も解釈せず機械的に転送するだけ)。`result_max` は `--result-max 1000` へ変換されることを任意スカラー群のテストで固定する。分数・小数・繰り上がり・余り・N項式などの既存変換もそれぞれ独立して検証する。`get_renderer_name()` が `reportlab`(削除済み)を含む未知の値を一律 `Unknown NUTS_CALC_RENDERER value` で拒否することも検証する(issue #232、`test_get_renderer_name_rejects_removed_reportlab`)。issue #232 以前は多くのテストが `renderer_name` を `"reportlab"`/`"latex"` で分けて実行していたが、`build_command()` 自体はレンダラー名に依存しないロジックのため、`"latex"` 固定に統一した。

## 統合ポイント

対象は `backend/renderers.py:build_command()` である。

## 変更履歴(git log より自動生成)

- ba08963 feat(#317): add integer/decimal dividend selection to grade 5 decimal division
- 40dfb0a feat(#313): add mixed decimal operand order to grade 4 integer/decimal multiplication (#314)
- 37a5a80 #230 Split a_value/b_value's overloaded digit-count/direct-value semantics into a_digits/b_digits (#236)
- 700f115 #232 backend: remove nuts_calc.py (ReportLab renderer) and the reportlab dependency (#234)
- 9393898 #186 renderers/engine: make latex+lualatex the default (and only reachable) configuration (#187)
- 7b064ef #114 nuts_calc_tex.py: add reducibility control to frac/mixed multiplication and division (#165)
- 1a32b29 #153 Add reusable result ceilings and grade-2 addition up to 1,000 (#158)
- 26ec449 #93 nuts_calc_tex.py: add optional name field to generated worksheets (#105)
- eae5107 #91 nuts_calc_tex.py: add remainder control to division (none/required/mixed) (#102)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
