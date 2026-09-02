# `backend/tests/test_web_backend_app.py`

## 目的・役割

Flask test client を使い、`backend/app.py` の3ルートと PDF generation routing・エラー変換を実サーバーなしで検証する。

## 動作の概要と主要な判定ロジック

issue #286 の回帰として、`com` の migrated helper に `page=2`、`with_bottom_answer=true`、`with_name_field=true` を同時指定し、生成 TeX が2ページ、各ページの名前欄、ページを跨いだ問題番号と bottom answer を持つことを検証する。加えて migrated helper が `page <= 0` を拒否することを検証する。

`POST /generate-pdf` の内部 presentation API 移行済み command ごとに、LaTeX engine の `compile` を fake stub へ置き換えて `%PDF` 応答が返ることを固定する。issue #297 以前は `renderers.run` を失敗 stub へ置き換えて subprocess fallback 非到達も固定していたが、同 issue で legacy subprocess 経路が削除されたため、その guard は全テストから除去した(テスト名の `_uses_presentation_api_not_subprocess` はそのまま維持)。`divfrac` は内部 routing、`a_digits` と明示 range の解決、`b_min >= 1` と layout の検証、compile failure を確認する(`test_web_backend_app.py:524-634`)。`simplify` は分数・矢印・blank PDF、fraction digit と layout の検証、compile failure を確認する(`test_web_backend_app.py:1000-1075`)。`frac2dec` は分数から有限小数への矢印と blank PDF、subprocess 非使用、fraction digit/layout 検証、compile failure を確認する(`test_web_backend_app.py:1078-1153`)。`dec2frac`(issue #222)は小数から約分済み分数への矢印と blank PDF、subprocess 非使用、`rows`/`columns` の下限検証、compile failure を確認する(digit 系オプションを取らないため fraction digit の検証はない)。`compare`(issue #224、#266 で共通部品化)は `test_generate_pdf_compare_uses_presentation_api_not_subprocess` が subprocess 非使用と、捕捉 TeX に `\compareeq{` と `\boxedblank`(比較記号位置の角枠、`COMPARE_REL_BLANK_TEX`)が含まれること(`\Rightarrow`/`BLANK_ANSWER_TEX` ではない)、`test_generate_pdf_compare_rejects_invalid_basic_input` が `numerator_digits`/`denominator_digits` 範囲外と `rows`/`columns` 過小の HTTP 500、`test_generate_pdf_compare_maps_compile_failure_to_500` が compile failure の HTTP 500 変換を固定する(`dec2frac` トリオと同型、`numerator_digits`/`denominator_digits` は `simplify`/`frac2dec` と同じ検証)。`mixed` は基本2項に加え、`terms` 固定、`terms_min`/`terms_max` 範囲、`mixed_operators`、3つの `reducible_mode` variant が内部 API を使うことを確認する。generator 境界を捕捉して terms / mixed-operator / reducible mode の伝達、blank TeX、subprocess 非使用を固定し、逆転した terms 範囲と不正な reducible mode/operator/operand pairing は HTTP 500 を期待する(`test_web_backend_app.py:1432-1628`)。`POST /generate-pdf` の `100`(issue #229)は、subprocess 非使用と番号ボックスなし(`\makebox[` を含まない)の PDF 生成、生成 TeX が legacy `build_document_tex`(`Page(columns=1, layout='block')` blank)経路と**バイト等価**であること(`test_generate_pdf_hundred_square_matches_legacy_document_output`、`generate_hundred_square` を固定テーブルへ monkeypatch)、compile failure の HTTP 500 変換、軸レンジ過小(`a_min==a_max`)の HTTP 500(`resolve_hundred_square_axes` の "distinct values" `ValueError`)を固定する。`POST /generate-pdf` の `ope --missing-value`(issue #223)は、`test_generate_pdf_ope_missing_value_uses_presentation_api_not_subprocess` が subprocess 非使用を、`test_generate_pdf_ope_missing_value_maps_compile_failure_to_500` が compile failure の HTTP 500 変換を固定する(#205 の plain `ope` ペアと同型)。issue #291 で per-command の subprocess fallthrough が廃止されたため、旧 `test_generate_pdf_ope_variants_still_use_subprocess_renderer` は `test_generate_pdf_invalid_ope_variant_combo_returns_500_without_subprocess` へ改名し、無効な `{"use_parentheses": True, "vertical"|"intermediate"|"missing_value": True}` 併用が `render_worksheet_pdf` の明示 `ValueError` → HTTP 500 になることを固定する。`test_generate_pdf_unmatched_request_returns_500_without_subprocess_fallback`(`mixed` + `reducible_mode` + 多項 → 500)、`test_generate_pdf_unknown_command_type_returns_500_without_subprocess_fallback` が no-match エラーを固定する。issue #297 で legacy 経路が削除されたため、switch 依存の `test_generate_pdf_defaults_to_the_three_layer_pipeline`(`_USE_LEGACY_PDF_PIPELINE is False` を assert)と `test_generate_pdf_legacy_pipeline_switch_routes_every_request_through_subprocess` は削除した。`POST /generate-pdf` の `commondenom`(issue #225)は、`test_generate_pdf_commondenom_uses_presentation_api_not_subprocess` が subprocess 非使用と `\Rightarrow`/`\displaystyle`/`BLANK_ANSWER_TEX` を含む blank PDF 生成を、`test_generate_pdf_commondenom_rejects_invalid_basic_input`(`rows`/`columns` を 0 に parametrize)が下限検証の HTTP 500 を、`test_generate_pdf_commondenom_maps_compile_failure_to_500` が compile failure の HTTP 500 変換を固定する(`dec2frac` の trio と同型、fraction digit 検証は `simplify` と共有のため専用ケースは持たない)。issue #292 の `test_generate_pdf_forwards_reverse_to_slot_builder` は `99`/`squ`/`pi` × `reverse ∈ {False, True}` を parametrize し、slot builder(`three_layer_renderer.nuts_calc_tex.build_*_slot_content_tex`)を spy して request の `reverse` が `functools.partial` 経由で渡ること、および捕捉 TeX が reverse 時のみ `\horizontaleq{\hspace{1.5em} \opspace = \opspace `(左辺が blank = side-swap)を含むことを固定する。データ層の出題順序フラグについては、`test_generate_pdf_kuku_forwards_descend_and_shuffle`(`99`)と `test_generate_pdf_squ_forwards_descend_and_shuffle`(`squ`、issue #298)が、それぞれ `generate_kuku_problems` / `generate_squ_problems` を spy して request の `descend`/`shuffle` が昇順・非シャッフルへ握り潰されず generator へ渡ることを固定する(`_generate_squ_pdf` は issue #298 で `_generate_kuku_pdf` / `_generate_pi_pdf` に合わせて対称化された)。`POST /generate-problems` については、`command_type == '100'`(issue #228)が `{"table": {left_values, top_values, answers}}` の10×10 envelope(`problems` キーなし、`answers[r][c] == left_values[r] + top_values[c]`)を返すこと、および `100` でも `num` 欠落は HTTP 400 のままであることを固定する。

## 重要な設計判断

LaTeX binary の有無や実コンパイル時間に依存せず routing を検証するため、`shutil.which` と両 engine adapter の `compile` を monkeypatch する。issue #297 で legacy subprocess 経路が削除される前は、subprocess 非使用の証明として `renderers.run` を失敗 stub へ差し替えていた。

内部プレゼンテーション API 経路のグルーは issue #290 で `backend/app.py` から `backend/three_layer_renderer.py` へ移設されたため、内部 API 経路にかかる monkeypatch の対象は `three_layer_renderer.shutil` / `three_layer_renderer.nuts_calc_tex`(モジュール先頭で `import three_layer_renderer`)である。`shutil` / `nuts_calc_tex` は `sys.modules` の共有シングルトンなのでこの付け替えに挙動変更はなく、`app.py` がこれらを import しなくなったための追随にすぎない。`POST /generate-problems` 経路のテストは `backend_app.problem_generation` を monkeypatch する。issue #297 で legacy subprocess 経路とその `backend_app.renderers.run` guard は削除された。

## 統合ポイント

- 対象: `backend/app.py` の Flask routes と、`backend/three_layer_renderer.py` の `render_worksheet_pdf` 経由で到達する各 `_generate_*_pdf` helper(routing / 検証 / TeX 内容 / compile failure 変換)。
- 呼び出し先: `backend/three_layer_renderer.py`、`backend/nuts_calc_tex.py`、`backend/problem_generation.py`、`backend/renderer_config.py`(`RENDERER_ENV_VAR`、`GET /renderer-info` テスト用)。いずれもテストごとに必要な境界だけを monkeypatch する。

## 注意事項・既知の制限

Flask test client の単体・結合テストであり、実 HTTP server や実 LaTeX コンパイルは起動しない。実 engine による生成は renderer/CLI 系の別テストまたは手動 smoke test が担う。

## 変更履歴（git log より自動生成）

- 912657b fix(#342): guarantee non-trivial division in g4-parentheses (括弧を含む四則混合計算)
- b81378d feat(#331): add grade 1 two-digit ± within 100 drills and --a-multiple/--b-multiple operand constraint (#339)
- 7bbec1b refactor(#297): delete the legacy /generate-pdf subprocess rendering path (#325)
- f85a421 feat(#317): add integer/decimal dividend selection to grade 5 decimal division (#319)
- c03270f feat(#301): rebalance drill-sheet typography and rework hissan layout (#302)
- e6e0e98 fix(#298): honor descend / shuffle in _generate_squ_pdf (3-layer renderer) (#299)
- eb3afe8 feat(#292): honor the reverse equation side-swap in the 3-layer renderer for 99/squ/pi (#295)
- 6417a2f refactor(#291): add a hardcoded 3-layer-vs-legacy renderer switch and drop the per-command subprocess fallthrough (#294)
- 0b35732 refactor(#290): extract the 3-layer-model PDF glue from app.py into three_layer_renderer.py (#293)
- 32162b8 feat(#286): wire presentation page options (#288)
