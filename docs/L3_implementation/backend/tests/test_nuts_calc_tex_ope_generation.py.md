# `backend/tests/test_nuts_calc_tex_ope_generation.py`

## 目的・役割

`nuts_calc_tex.py` の整数・小数 `ope` 問題生成を、TeX実行に依存せず純粋関数単位で検証する。

## 動作の概要

四則演算、繰り上がり・繰り下がり、余り、かっこ付き式、平坦なN項式、虫食い算などの生成契約を検証する。`result_max` については四則すべての通常2項式と表示値基準の小数判定、かっこ付き式、N項式、虫食い算を対象に、境界値を受理することと不可能な上限で `ValueError` になることを確認する(`backend/tests/test_nuts_calc_tex_ope_generation.py:103-136,602-617,720-735,784-796`)。繰り上がり・繰り下がり(`carry_mode`)は整数専用テストに加え、`a_decimal_places`/`b_decimal_places` を設定した小数版でも同じ契約(`required`/`none` で判定が一致し、`OpeProblem` の桁数メタデータが保持される)を検証する(issue #113、`test_generate_add_sub_problems_applies_carry_and_borrow_filter_with_decimal_places`/`test_generate_ope_problems_decimal_carry_matches_illustrative_example`)。

## 重要な設計判断とその理由

結果上限は小学2年生プリセットだけの例で検証せず、各生成経路の公開関数へ直接渡す。これにより `--result-max` が特定演算・特定UIに閉じず、`ope` の全式形式で共通利用できる契約を固定する。

## 統合ポイント

- テスト対象: `backend/nuts_calc_tex.py` の `ope` 生成・評価関数。
- 実行方法: `cd backend && python3 -m pytest -q tests/test_nuts_calc_tex_ope_generation.py`。

## 注意事項・既知の制限

- 純粋関数テストのため `pdflatex` は不要。PDF/CSV出力は別のCLIテストが担う。

## 変更履歴（git log より自動生成）

- 912657b fix(#342): guarantee non-trivial division in g4-parentheses (括弧を含む四則混合計算)
- b81378d feat(#331): add grade 1 two-digit ± within 100 drills and --a-multiple/--b-multiple operand constraint (#339)
- c03270f feat(#301): rebalance drill-sheet typography and rework hissan layout (#302)
- a704907 feat(#269): render the written-calculation (hissan) content format via shared TeX components (#281)
- 8cce41a feat(#268): render the staged arrow-chain content format via a shared TeX component (#278)
- 64a8412 feat(#265): render the boxed-blank equation format via a shared TeX component (#276)
- 4088bf0 feat(#264): render equation content formats via shared TeX components (#275)
- bc0eef5 #113 nuts_calc_tex.py: allow --carry-borrow with decimal operands (#164)
- 1a32b29 #153 Add reusable result ceilings and grade-2 addition up to 1,000 (#158)
- bd8f170 #92 nuts_calc_tex.py: fix borrow-required subtraction to respect configured digit range (#103)
