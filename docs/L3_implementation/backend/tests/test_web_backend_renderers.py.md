# `backend/tests/test_web_backend_renderers.py`

## 目的・役割

FlaskバックエンドがPDF生成リクエストを正しいCLI引数へ変換することを検証する。

## 動作概要

`compare` リクエストの `comparison_pattern`、`a_fraction_form`、`b_fraction_form` が、LaTeXレンダラーの対応する3オプションへ変換されることを検証する（`backend/tests/test_web_backend_renderers.py:174-186`）。

## 統合ポイント

対象は `backend/renderers.py:build_command()` である。

## 変更履歴(git log より自動生成)

- 0dcb553 feat(#91): add remainder control to ope division
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
