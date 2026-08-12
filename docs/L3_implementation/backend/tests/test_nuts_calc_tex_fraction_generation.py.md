# `backend/tests/test_nuts_calc_tex_fraction_generation.py`

## 目的・役割

`nuts_calc_tex.py` の分数四則演算と分数比較の純粋な生成・表示・CSVロジックを、pdflatexに依存せず検証する。

## 動作概要

- 分数四則の厳密計算、同分母条件、異分母条件、表示時の約分を検証する。
- `compare` は3比較パターンと真分数・仮分数・帯分数・`mix` の組合せを生成し、等値を除外して表示上の分子/分母条件を守ることを検証する（`backend/tests/test_nuts_calc_tex_fraction_generation.py:79-108`）。
- blank版の比較記号が枠、解答版が不等号になること、CSVが左右の整数部・分子・分母と関係記号を保存することを検証する（`backend/tests/test_nuts_calc_tex_fraction_generation.py:111-133`）。

## 統合ポイント

対象は `nuts_calc_tex.py` の `generate_fraction_problems()` と `generate_fraction_comparison_problems()`、関連するTeX/CSVビルダーである。

## 変更履歴(git log より自動生成)

- 9e296ee feat(#83): add fraction comparison worksheets
- 7c89a52 feat(#65): add curriculum-aligned fraction worksheets
