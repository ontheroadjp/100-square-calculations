# `backend/tests/test_nuts_calc_tex_fraction_generation.py`

## 目的・役割

`nuts_calc_tex.py` の分数四則演算と分数比較の純粋な生成・表示・CSVロジックを、pdflatexに依存せず検証する。

## 動作概要

- 分数四則の厳密計算、同分母条件、異分母条件、表示時の約分を検証する。
- `compare` は3比較パターンと真分数・仮分数・帯分数・`mix` の組合せを生成し、等値を除外して表示上の分子/分母条件を守ることを検証する（`backend/tests/test_nuts_calc_tex_fraction_generation.py:79-108`）。
- blank版の比較記号が枠、解答版が不等号になること、CSVが左右の整数部・分子・分母と関係記号を保存することを検証する（`backend/tests/test_nuts_calc_tex_fraction_generation.py:111-133`）。
- `build_fraction_csv_rows` のCSV列テストは、issue #112 で末尾に追加された `a_whole`/`b_whole` を含む11列を検証する。`problem.a.whole`/`problem.b.whole` が既定0のとき、先頭9列の値は帯分数対応前と無変更であることを保証する。
- `reducible_mode`(issue #114、`frac -o mul`/`div` 専用)は `required`/`none`/`mixed` の3値それぞれについて、生成された全問題の未約分の raw 分子・分母(`_raw_gcd` ヘルパーが `mul`/`div` に応じて計算)が `gcd > 1`/`gcd == 1`/両方混在、を満たすことを検証する。

CLI レベル(`--a-fraction-form`/`--b-fraction-form` を `frac -o add`/`sub` に拡張する帯分数対応、issue #112。`--require-reducible`/`--no-reducible`/`--mixed-reducible`、issue #114)の PDF生成・CSV・バリデーションエラーは pdflatex サブプロセス経由のため `backend/tests/test_nuts_calc_tex.py` 側でカバーする(本ファイルは pdflatex 非依存の純粋ロジックのみ)。

## 統合ポイント

対象は `nuts_calc_tex.py` の `generate_fraction_problems()` と `generate_fraction_comparison_problems()`、関連するTeX/CSVビルダーである。

## 変更履歴(git log より自動生成)

- 80f5c5f feat(#112): add mixed-number (帯分数) support to nuts_calc_tex.py frac add/sub
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
