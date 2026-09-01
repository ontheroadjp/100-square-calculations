# `backend/tests/test_renderer_config.py`

## 目的・役割

`backend/renderer_config.py` の `get_renderer_name()`(レンダラー名解決)を検証する。Flask アプリも subprocess も起動せず、純粋関数を直接呼ぶ。

## 動作概要

- `test_get_renderer_name_defaults_to_latex_when_unset`: `NUTS_CALC_RENDERER` 未設定時に `"latex"` を返す。
- `test_get_renderer_name_reads_env_var`: `NUTS_CALC_RENDERER=latex` を反映する。
- `test_get_renderer_name_rejects_unknown_value`: 未知の値を `Unknown NUTS_CALC_RENDERER value` の `ValueError` で拒否する。
- `test_get_renderer_name_rejects_removed_reportlab`: 削除済みの `reportlab`(issue #232)も他の未知の値と同じ汎用エラーで拒否する。

## 統合ポイント

対象は `backend/renderer_config.py:get_renderer_name()`。

## 注意事項・既知の制限

issue #36 では `test_web_backend_renderers.py` として `build_command()`(JSON → CLI 引数変換)の変換規則を網羅的に検証する 30 件のテストも持っていたが、issue #297 で `build_command`/`run`(legacy subprocess 経路)が削除されたのに伴い、それらのテストも削除し、ファイルを `test_renderer_config.py` にリネームして `get_renderer_name()` のテスト 4 件のみを残した。

## 変更履歴(git log より自動生成)

- 56b66ad refactor(#297): delete the legacy /generate-pdf subprocess rendering path (rename test_web_backend_renderers.py -> test_renderer_config.py)
- ba08963 feat(#317): add integer/decimal dividend selection to grade 5 decimal division
- 40dfb0a feat(#313): add mixed decimal operand order to grade 4 integer/decimal multiplication (#314)
- 37a5a80 #230 Split a_value/b_value's overloaded digit-count/direct-value semantics into a_digits/b_digits (#236)
- 700f115 #232 backend: remove nuts_calc.py (ReportLab renderer) and the reportlab dependency (#234)
- 9393898 #186 renderers/engine: make latex+lualatex the default (and only reachable) configuration (#187)
