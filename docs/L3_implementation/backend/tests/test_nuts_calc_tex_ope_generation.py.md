# `backend/tests/test_nuts_calc_tex_ope_generation.py`

## 目的・役割

`nuts_calc_tex.py` の整数・小数 `ope` 問題生成を、TeX実行に依存せず純粋関数単位で検証する。

## 動作の概要

四則演算、繰り上がり・繰り下がり、余り、かっこ付き式、平坦なN項式、虫食い算などの生成契約を検証する。`result_max` については四則すべての通常2項式と表示値基準の小数判定、かっこ付き式、N項式、虫食い算を対象に、境界値を受理することと不可能な上限で `ValueError` になることを確認する(`backend/tests/test_nuts_calc_tex_ope_generation.py:103-136,602-617,720-735,784-796`)。

## 重要な設計判断とその理由

結果上限は小学2年生プリセットだけの例で検証せず、各生成経路の公開関数へ直接渡す。これにより `--result-max` が特定演算・特定UIに閉じず、`ope` の全式形式で共通利用できる契約を固定する。

## 統合ポイント

- テスト対象: `backend/nuts_calc_tex.py` の `ope` 生成・評価関数。
- 実行方法: `cd backend && python3 -m pytest -q tests/test_nuts_calc_tex_ope_generation.py`。

## 注意事項・既知の制限

- 純粋関数テストのため `pdflatex` は不要。PDF/CSV出力は別のCLIテストが担う。

## 変更履歴（git log より自動生成）

- 32dd948 feat(#153): add reusable result ceiling for ope drills
- bd8f170 #92 nuts_calc_tex.py: fix borrow-required subtraction to respect configured digit range (#103)
- eae5107 #91 nuts_calc_tex.py: add remainder control to division (none/required/mixed) (#102)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
