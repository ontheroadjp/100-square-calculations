# `tests/test_web_backend_renderers.py`

## 目的・役割

FlaskバックエンドがPDF生成リクエストを正しいCLI引数へ変換することを検証する。

## 動作概要

`compare` リクエストの `comparison_pattern`、`a_fraction_form`、`b_fraction_form` が、LaTeXレンダラーの対応する3オプションへ変換されることを検証する（`tests/test_web_backend_renderers.py:174-186`）。

## 統合ポイント

対象は `web/backend/renderers.py:build_command()` である。
