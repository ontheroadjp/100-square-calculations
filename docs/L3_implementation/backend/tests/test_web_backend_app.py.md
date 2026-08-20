# `backend/tests/test_web_backend_app.py`

## 目的・役割

Flask test client を使い、`backend/app.py` の3ルートと PDF generation routing・エラー変換を実サーバーなしで検証する。

## 動作の概要と主要な判定ロジック

`POST /generate-pdf` の内部 presentation API 移行済み command ごとに、`renderers.run` を失敗 stub へ置き換えて subprocess fallback が呼ばれないことを固定する。`divfrac` は内部 routing、`a_digits` と明示 range の解決、`b_min >= 1` と layout の検証、compile failure を確認する(`test_web_backend_app.py:524-634`)。`simplify` は分数・矢印・blank PDF、fraction digit と layout の検証、compile failure を確認する(`test_web_backend_app.py:1000-1075`)。基本2項 `mixed` は内部 API 利用と入力検証を確認し、terms/mixed-operator/reducible variants は subprocess を維持することも固定する(`test_web_backend_app.py:1078-1176`)。

## 重要な設計判断

LaTeX binary の有無や実コンパイル時間に依存せず routing を検証するため、`shutil.which` と両 engine adapter の `compile` を monkeypatch する。subprocess 非使用の証明は戻り値の観察だけでなく、`renderers.run` が呼ばれた時点でテストを失敗させる。

## 統合ポイント

- 対象: `backend/app.py` の Flask routes と各 `_generate_*_pdf` helper。
- 呼び出し先: `backend/nuts_calc_tex.py`、`backend/problem_generation.py`、`backend/renderers.py`。いずれもテストごとに必要な境界だけを monkeypatch する。

## 注意事項・既知の制限

Flask test client の単体・結合テストであり、実 HTTP server や実 LaTeX コンパイルは起動しない。実 engine による生成は renderer/CLI 系の別テストまたは手動 smoke test が担う。

## 変更履歴（git log より自動生成）

- 156c2d2 Merge remote-tracking branch 'origin/main' into feat/220-migrate-simplify-presentation-api
- ab8daf7 feat(#220): migrate simplify PDF generation
- 1fe5a14 feat(#219): migrate divfrac to presentation API
- 5cd034c feat(#218): migrate mixed PDF generation (#253)
- 5736b74 feat(#217): migrate frac PDF generation (#252)
- 1c331f9 feat(#216): migrate divisors to presentation API (#251)
- c85124d Migrate multiples PDF generation to the presentation API (#249)
- 8117acc Migrate evenodd PDF generation to the presentation API (#248)
- 757d736 feat(#213): migrate abc pdf generation to presentation api
- 3370b1c #212 Migrate generate-pdf gcd to the internal presentation API (#246)
- 1c3fdee #211 generate-pdf: migrate lcm to the internal presentation API (#245)
- 429c088 #210 generate-pdf: migrate pi to the internal presentation API (#244)
- 40ad870 #209 generate-pdf: migrate squ to the internal presentation API (#243)
- a6187e9 #208 generate-pdf: migrate 99 (kuku) to the internal presentation API (#242)
- 7a159b9 #207 generate-pdf: migrate ope (multi-term) to the internal presentation API (#241)
- 5ec3e56 #206 generate-pdf: migrate ope --use-parentheses (tree variant) to the internal presentation API (#240)
- 99a8279 #205 generate-pdf: migrate ope (plain 2-term) to the internal presentation API (#239)
- 700f115 #232 backend: remove nuts_calc.py (ReportLab renderer) and the reportlab dependency (#234)
