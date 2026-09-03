# `backend/tests/test_nuts_calc_tex_approx_generation.py`

## 目的・役割

`nuts_calc_tex.py` の `approx`(概数 rounding / estimation、issue #346)ドリルのロジックを LaTeX 実行なしで検証する単体テスト。丸めプリミティブ、`resolve_approx_params` の検証・デフォルト解決、`generate_approx_problems` の3 kind、block / bottom-answer / CSV レンダラを対象とする。pdflatex を必要としない純 Python 部分をカバーし、pdflatex-gated な end-to-end テスト([[test_nuts_calc_tex.py]] の `test_cli_approx_*`)を補完する。

## 動作の概要と主要な判定ロジック

- **丸めプリミティブ**: `_approx_round_to_place`(四捨五入は半数切り上げ、`up`/`down` は切り上げ/切り捨て、10 の倍数は昇格しない)、`_approx_round_value`(`--sig-digits` は「上から N けた」、N 桁以下の値は不変。`--round-place` があればそれを優先)、`round_half_up_fraction`(`Fraction` で厳密、`method='round'` は 四捨五入 = half away from zero であり Python `round()` の銀行丸めとは**異なる** -- テストは 0.125 → 0.13 でこの差を固定する)。
- **`resolve_approx_params`**: kind ごとのデフォルト充填(round は `sig_digits=2` と 1000..99999 レンジ、estimate は `sig_digits=1`、quotient は `quotient_decimal_places=2`/`dividend_decimal_places=1`)、estimate が単一 operator を要求すること、範囲外の decimal places 拒否、および `parametrize` による不正組合せ7種の `ValueError`(`--round-place` と `--sig-digits` の併用、`round_place < 1`、quotient での `--sig-digits`/`--round-method`、非-quotient での `--quotient-decimal-places`、丸めが全値で自明なレンジ、反転レンジ)。
- **`generate_approx_problems`**: seed 固定で 3 kind を生成し、round の答えが `_approx_round_value` と一致、estimate(mul)が「丸めた a × 丸めた b = 積」、estimate(div)が「丸めた被除数 ÷ 丸めた除数」で割り切れること、quotient の答えが `round_half_up_fraction` と一致し `answer_tex == answer_plain`(商には演算子が乗らない)であることを検証する。
- **レンダラ**: `build_approx_block_tex` の blank 版が答えを隠し `\horizontaleq{<expr> \opspace \fallingdotseq \opspace \hspace{1.5em}}`、filled 版が答えを埋めること、`build_approx_bottom_answer_tex` が `(n) $<answer_tex>$` を ` \quad ` 連結すること、CSV 行が `[page, index, kind, expr_plain, answer_plain]` の5列であることを検証する。

## 重要な設計判断

quotient 系のアサーションは Python 組込み `round()` ではなく `nuts_calc_tex.round_half_up_fraction` / `_approx_quotient_scaled` を期待値計算に使う。四捨五入(half away from zero)は `round()` の round-half-to-even と半数ケースで食い違うため、実装関数を真実の source とする。

## 統合ポイント

対象は `backend/nuts_calc_tex.py` の `_approx_round_to_place` / `_approx_round_value` / `_approx_round_range_is_nontrivial` / `round_half_up_fraction` / `resolve_approx_params`(`ApproxParams`)/ `_approx_estimate_operands` / `find_approx_estimate_pair` / `find_approx_quotient_pair` / `ApproxProblem` / `generate_approx_problems` / `build_approx_*`。

## 注意事項・既知の制限

純粋関数テストであり PDF コンパイルは行わない。実 PDF(両エンジンでの `≒` 描画)は [[test_nuts_calc_tex.py]] の pdflatex-gated `test_cli_approx_*`、Flask routing は [[test_web_backend_app.py]] の `test_generate_pdf_approx_*` / `test_generate_problems_approx_*` が担う。
