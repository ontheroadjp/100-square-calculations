# `backend/tests/test_web_backend_app.py`

## 目的・役割

Flask test client を使い、`backend/app.py` の3ルートと PDF generation routing・エラー変換を実サーバーなしで検証する。

## 動作の概要と主要な判定ロジック

`POST /generate-pdf` の内部 presentation API 移行済み command ごとに、`renderers.run` を失敗 stub へ置き換えて subprocess fallback が呼ばれないことを固定する。`aBc` については engine adapter の `compile` を PDF header を書く stub に置き換え、レスポンスが HTTP 200/PDF になることを検証する(`test_web_backend_app.py:219-244`)。`nuts_calc_tex.failure()` が送出する `SystemExit` は API から JSON 500 として返ることも検証する(`test_web_backend_app.py:247-265`)。

## 重要な設計判断

LaTeX binary の有無や実コンパイル時間に依存せず routing を検証するため、`shutil.which` と両 engine adapter の `compile` を monkeypatch する。subprocess 非使用の証明は戻り値の観察だけでなく、`renderers.run` が呼ばれた時点でテストを失敗させる。

## 統合ポイント

- 対象: `backend/app.py` の Flask routes と各 `_generate_*_pdf` helper。
- 呼び出し先: `backend/nuts_calc_tex.py`、`backend/problem_generation.py`、`backend/renderers.py`。いずれもテストごとに必要な境界だけを monkeypatch する。

## 注意事項・既知の制限

Flask test client の単体・結合テストであり、実 HTTP server や実 LaTeX コンパイルは起動しない。実 engine による生成は renderer/CLI 系の別テストまたは手動 smoke test が担う。
