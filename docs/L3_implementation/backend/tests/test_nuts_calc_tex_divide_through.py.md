# `backend/tests/test_nuts_calc_tex_divide_through.py`

## 目的・役割

`nuts_calc_tex.py` の `--divide-through`(わり進み、issue #349)div モードを検証する単体・結合テスト。純 Python のヘルパー / 生成ロジックと、`pdflatex`-gated な CLI end-to-end / CLI 拒否テストを1ファイルにまとめる(feature 単位の集約。`--decimal-remainder` の #333/#334 テストが複数ファイルに分散しているのとは別方針)。

## 動作の概要と主要な判定ロジック

- **`divide_through_quotient`**: `parametrize` で受理ケース(`9.0÷4=2.25`、`9.4÷8=1.175`、整数被除数 `7÷4=1.75`、小数除数 `9.0÷2.5=3.6` など)の `(total_places, c)` を固定し、`c * b == a * 10**(total_places - (a_dp - b_dp))` という**整数**の恒等式で真の商と一致することを確認する(浮動小数の `==` 比較は last-ULP で割れるため使わない)。棄却ケース(`base_places` で既に割り切れる `8.0÷4` / `3.6÷3`、循環小数 `÷3`・`÷7`、商 < 1、ゼロ除数、見かけの整数除数 `4.0`)が `None` を返すこと、`max_total_decimal_places` の上限(`9.3÷8=1.1625` は4桁で受理、3桁上限で棄却)を検証する。
- **`find_divide_through_division_pair`**: grade 4(`b 2..9`)/ grade 5(`b_digits:2`)プリセットレンジで必ずペアが見つかること、全除数が3のレンジ(割り切れるか循環かのどちらか)で `None` を返すこと。
- **`calc_div_divide_through`**: 4-tuple `(a, b, c, total_places)` を返すこと、決定的フォールバック(`MAX_OPERAND_RETRY_ATTEMPTS` を 0 に monkeypatch)、条件を満たすペアが無いとき `ValueError`。
- **`generate_ope_problems(divide_through=True)`**: grade 4 / grade 5 レンジで、`remainder == 0`・`result_decimal_places` が上限以内・`a % b != 0`(真のわり進み)・`c * b == a * 10**(...)` を全問検証。`divide_through=False` が seed 固定で無フラグと完全一致(無変更)であること。`build_ope_slot_content_tex` が `9.0 \div 4 = 2.25` を `\cdots` tail なしで描画すること。
- **CLI(`pdflatex`-gated、`shutil.which("pdflatex") is None` で auto-skip)**: `--divide-through` で PDF + CSV を生成し、CSV の余り列が 0・商が2桁以上の小数・`float(a)/int(b) == float(c)` であることを確認。`parametrize` で不正組合せ11種(`-o add`、`-o div mul`、`--b-decimal-places 2`、`--decimal-remainder`・`--no-remainder`・`--quotient-digits`・`--integer-dividend`・`--vertical`・`--use-parentheses`・`--missing-value`・`--intermediate` との併用)が exit 1 で PDF を作らないこと、全除数3のレンジが fail-fast することを検証。

## 重要な設計判断

真の商との一致は浮動小数ではなく整数の恒等式 `c * b == a * 10**(total_places - base_places)` で確認する(`base_places = a_decimal_places - b_decimal_places`)。`8.1 / 5` のようなオペランドは float で厳密表現できず `c / 10**places == (a/10**a_dp)/(b/10**b_dp)` が偽になり得るため。

## 統合ポイント

対象は `backend/nuts_calc_tex.py` の `MAX_DIVIDE_THROUGH_QUOTIENT_DECIMAL_PLACES` / `divide_through_quotient` / `find_divide_through_division_pair` / `calc_div_divide_through` / `generate_ope_problems(divide_through=...)` / `build_ope_slot_content_tex`。転送経路([[../problem_generation.py]] / [[../three_layer_renderer.py]] / [[../renderer_config.py]])の結合は [[test_web_backend_app.py]] の既存 ope テストが `divide_through` キー未指定でカバーする(新キーは `total=False` で任意)。

## 注意事項・既知の制限

CLI テストは `pdflatex` が無いと丸ごと skip されるため、純 Python テスト(ヘルパー・`generate_ope_problems`)がエンジン非依存の主カバレッジ。`lualatex` 専用の描画確認は追加していない(`--decimal-remainder` と同じ方針)。

## 変更履歴（git log より自動生成）

- ebbe3c0 feat(#349): redesign decimal-division drills around a 余り setting and add --divide-through
