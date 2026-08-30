# `backend/tests/test_web_backend_app.py`

## 目的・役割

Flask test client を使い、`backend/app.py` の3ルートと PDF generation routing・エラー変換を実サーバーなしで検証する。

## 動作の概要と主要な判定ロジック

issue #286 の回帰として、`com` の migrated helper に `page=2`、`with_bottom_answer=true`、`with_name_field=true` を同時指定し、生成 TeX が2ページ、各ページの名前欄、ページを跨いだ問題番号と bottom answer を持つことを検証する。加えて migrated helper が `page <= 0` を拒否することを検証する(`test_web_backend_app.py:174-230`)。

`POST /generate-pdf` の内部 presentation API 移行済み command ごとに、`renderers.run` を失敗 stub へ置き換えて subprocess fallback が呼ばれないことを固定する。`divfrac` は内部 routing、`a_digits` と明示 range の解決、`b_min >= 1` と layout の検証、compile failure を確認する(`test_web_backend_app.py:524-634`)。`simplify` は分数・矢印・blank PDF、fraction digit と layout の検証、compile failure を確認する(`test_web_backend_app.py:1000-1075`)。`frac2dec` は分数から有限小数への矢印と blank PDF、subprocess 非使用、fraction digit/layout 検証、compile failure を確認する(`test_web_backend_app.py:1078-1153`)。`dec2frac`(issue #222)は小数から約分済み分数への矢印と blank PDF、subprocess 非使用、`rows`/`columns` の下限検証、compile failure を確認する(digit 系オプションを取らないため fraction digit の検証はない)。`compare`(issue #224、#266 で共通部品化)は `test_generate_pdf_compare_uses_presentation_api_not_subprocess` が subprocess 非使用と、捕捉 TeX に `\compareeq{` と `\boxedblank`(比較記号位置の角枠、`COMPARE_REL_BLANK_TEX`)が含まれること(`\Rightarrow`/`BLANK_ANSWER_TEX` ではない)、`test_generate_pdf_compare_rejects_invalid_basic_input` が `numerator_digits`/`denominator_digits` 範囲外と `rows`/`columns` 過小の HTTP 500、`test_generate_pdf_compare_maps_compile_failure_to_500` が compile failure の HTTP 500 変換を固定する(`dec2frac` トリオと同型、`numerator_digits`/`denominator_digits` は `simplify`/`frac2dec` と同じ検証)。`mixed` は基本2項に加え、`terms` 固定、`terms_min`/`terms_max` 範囲、`mixed_operators` variant が内部 API を使うことを確認する。generator 境界を捕捉して解決済み terms と mixed-operator bool の伝達も検証し、逆転した terms 範囲は HTTP 500、`reducible_mode` variant は subprocess 維持を固定する(`test_web_backend_app.py:1431-1565`)。`POST /generate-pdf` の `100`(issue #229)は、subprocess 非使用と番号ボックスなし(`\makebox[` を含まない)の PDF 生成、生成 TeX が legacy `build_document_tex`(`Page(columns=1, layout='block')` blank)経路と**バイト等価**であること(`test_generate_pdf_hundred_square_matches_legacy_document_output`、`generate_hundred_square` を固定テーブルへ monkeypatch)、compile failure の HTTP 500 変換、軸レンジ過小(`a_min==a_max`)の HTTP 500(`resolve_hundred_square_axes` の "distinct values" `ValueError`)を固定する。`POST /generate-pdf` の `ope --missing-value`(issue #223)は、`test_generate_pdf_ope_missing_value_uses_presentation_api_not_subprocess` が subprocess 非使用を、`test_generate_pdf_ope_missing_value_maps_compile_failure_to_500` が compile failure の HTTP 500 変換を固定する(#205 の plain `ope` ペアと同型)。`test_generate_pdf_ope_variants_still_use_subprocess_renderer` の parametrize からは `{"missing_value": True}` 単独ケースを除外し(移行済み)、無効な `{"use_parentheses": True, "missing_value": True}` 併用のみ subprocess fallback として残す。`POST /generate-pdf` の `commondenom`(issue #225)は、`test_generate_pdf_commondenom_uses_presentation_api_not_subprocess` が subprocess 非使用と `\Rightarrow`/`\displaystyle`/`BLANK_ANSWER_TEX` を含む blank PDF 生成を、`test_generate_pdf_commondenom_rejects_invalid_basic_input`(`rows`/`columns` を 0 に parametrize)が下限検証の HTTP 500 を、`test_generate_pdf_commondenom_maps_compile_failure_to_500` が compile failure の HTTP 500 変換を固定する(`dec2frac` の trio と同型、fraction digit 検証は `simplify` と共有のため専用ケースは持たない)。`POST /generate-problems` については、`command_type == '100'`(issue #228)が `{"table": {left_values, top_values, answers}}` の10×10 envelope(`problems` キーなし、`answers[r][c] == left_values[r] + top_values[c]`)を返すこと、および `100` でも `num` 欠落は HTTP 400 のままであることを固定する。

## 重要な設計判断

LaTeX binary の有無や実コンパイル時間に依存せず routing を検証するため、`shutil.which` と両 engine adapter の `compile` を monkeypatch する。subprocess 非使用の証明は戻り値の観察だけでなく、`renderers.run` が呼ばれた時点でテストを失敗させる。

## 統合ポイント

- 対象: `backend/app.py` の Flask routes と各 `_generate_*_pdf` helper。
- 呼び出し先: `backend/nuts_calc_tex.py`、`backend/problem_generation.py`、`backend/renderers.py`。いずれもテストごとに必要な境界だけを monkeypatch する。

## 注意事項・既知の制限

Flask test client の単体・結合テストであり、実 HTTP server や実 LaTeX コンパイルは起動しない。実 engine による生成は renderer/CLI 系の別テストまたは手動 smoke test が担う。

## 変更履歴（git log より自動生成）

- e462247 feat(#284): migrate multi-term mixed PDF generation
- 230261c feat(#227): migrate ope --vertical to the internal presentation API
- 3c55ae3 feat(#226): migrate ope --intermediate to the internal presentation API
- 9b643c3 feat(#270): render the hundred-square grid table via shared TeX components (#280)
- 299eab0 feat(#267): render arrow-conversion content formats via shared TeX components (#279)
- f794743 feat(#266): render the comparison content format via a shared TeX component (#277)
- 4088bf0 feat(#264): render equation content formats via shared TeX components (#275)
- 2d4c435 feat(#225): migrate commondenom to the internal presentation API (#274)
- 84c789b feat(#224): migrate compare to the internal presentation API (#273)
- 7943190 feat(#223): migrate ope --missing-value to the internal presentation API (#272)
