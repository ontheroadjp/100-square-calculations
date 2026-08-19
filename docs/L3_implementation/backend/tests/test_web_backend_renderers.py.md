# `backend/tests/test_web_backend_renderers.py`

## 目的・役割

FlaskバックエンドがPDF生成リクエストを正しいCLI引数へ変換することを検証する。

## 動作概要

`build_command()` の位置引数、値付きオプション、真偽フラグ、LaTeX専用パラメーター変換を検証する。`result_max` は `--result-max 1000` へ変換されることを任意スカラー群のテストで固定する(`backend/tests/test_web_backend_renderers.py:68-83`)。分数・小数・繰り上がり・余り・N項式などの既存変換もそれぞれ独立して検証する。

## 統合ポイント

対象は `backend/renderers.py:build_command()` である。

## 変更履歴(git log より自動生成)

- 506d7b4 feat(#186): make latex+lualatex the default reachable configuration
- 7b064ef #114 nuts_calc_tex.py: add reducibility control to frac/mixed multiplication and division (#165)
- 1a32b29 #153 Add reusable result ceilings and grade-2 addition up to 1,000 (#158)
- 26ec449 #93 nuts_calc_tex.py: add optional name field to generated worksheets (#105)
- eae5107 #91 nuts_calc_tex.py: add remainder control to division (none/required/mixed) (#102)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
