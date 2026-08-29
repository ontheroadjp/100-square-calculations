# `backend/tests/test_nuts_calc_tex_content_area_layout.py`

## 目的・役割

`ContentAreaLayout` と番号なし Layer-3 content formatter の合成を、LaTeX 実行なしで文字列レベルに検証する単体テスト。

## 動作の概要と主要な判定ロジック

- 10/20/30問の preset、任意 rows/columns、番号ボックス幅、slot順序を検証する。
- 各 `build_*_slot_content_tex` が問題番号を含まず、`number_box_width_mm=0` の Layer-2 slot と合成した本文が既存 `build_*_block_tex` と一致することを確認する。
- `evenodd` は `\mathrm{even/odd}` を保持する番号なし本文を検証する(`test_nuts_calc_tex_content_area_layout.py:490-512`)。
- `multiples` は可変長のコンマ区切り回答と blank 表示を保持する番号なし本文を検証する(`test_nuts_calc_tex_content_area_layout.py:542-565`)。
- `frac` は `\displaystyle`、厳密分数・帯分数、blank を保った番号なし本文と legacy block の合成同値性を検証する(`test_nuts_calc_tex_content_area_layout.py:112-143`)。
- `mixed` は整数・小数・分数の混在式、厳密分数結果、blank を保持する番号なし本文を検証する(`test_nuts_calc_tex_content_area_layout.py:362-403`)。
- `simplify` は pattern-4b の分数、矢印、blank/filled 表示を検証し、番号なし本文と legacy block の合成同値性を固定する(`test_nuts_calc_tex_content_area_layout.py:146-176`)。
- `frac2dec` は pattern-4b の分数、矢印、有限小数または blank の表示を検証し、番号なし本文と legacy block の合成同値性を固定する(`test_nuts_calc_tex_content_area_layout.py:180-213`)。
- `dec2frac`(issue #222)は pattern-4b の小数、矢印、約分済み分数または blank の表示を検証し、番号なし本文(`build_dec2frac_slot_content_tex`)と legacy block(`build_dec2frac_block_tex`)の合成同値性を固定する。`frac2dec` と対になる逆向きの変換。
- `commondenom`(issue #225)は `build_commondenom_slot_content_tex` が問題番号を含まないこと(`filled_content` に `"5)"` が現れない)、通分後の2分数(未約分)と blank(`BLANK_ANSWER_TEX`)の表示、および番号なし本文と legacy `build_commondenom_block_tex` の `number_box_width_mm=0` での合成同値性を検証する(`test_build_commondenom_slot_content_tex_omits_number_and_renders_answers`/`test_build_commondenom_slot_content_tex_reconstructs_legacy_block_body`)。
- `divfrac` は pattern-1b の番号なし本文が答えを未約分のまま保持すること、blank 表示、legacy block との合成同値性を検証する(`test_nuts_calc_tex_content_area_layout.py:405-431`)。
- `divisors` は可変長のコンマ区切り約数リストと blank を保持し、legacy block と合成後の本文が一致することを検証する(`test_nuts_calc_tex_content_area_layout.py:568-591`)。
- `ContentAreaLayout.numbered` の既定が `True` であること、および `100` の `build_hundred_square_slot_content_tex` が `build_hundred_square_block_tex` へバイト等価に委譲し `\makebox` を含まないこと(番号 prefix を元々持たない grid)を検証する(issue #229、`test_content_area_layout_defaults_to_numbered`/`test_build_hundred_square_slot_content_tex_ports_block_tex_as_is`)。
- `ope --missing-value`(issue #223)は `build_missing_value_slot_content_tex` が問題番号を含まないこと、および blank/filled × blanked-a/blanked-b の全組合せで番号なし本文と legacy `build_missing_value_block_tex` の合成同値性(`number_box_width_mm=0`)を検証する(`test_build_missing_value_slot_content_tex_omits_problem_number`/`test_build_missing_value_slot_content_tex_matches_block_tex_body_when_composed`)。
- `compare`(issue #224)は pattern-3 の番号なし本文(`build_fraction_comparison_slot_content_tex`)が `\displaystyle`・両オペランドの `\frac`・中置の関係記号(filled は `<`、blank は `BOXED_BLANK_TEX`)を保ち問題番号を含まないこと、および `number_box_width_mm=0` の Layer-2 slot と合成した本文が legacy `build_fraction_comparison_block_tex` と一致することを検証する(`test_build_fraction_comparison_slot_content_tex_omits_number_and_renders_answers`/`test_build_fraction_comparison_slot_content_tex_reconstructs_legacy_block_body`)。

## 重要な設計判断

既存 CLI block formatter は互換経路として残し、内部 presentation API 用 slot formatter だけが番号描画を Layer 2 に委譲する。テストはこの責務分離と本文の表示互換性を同時に固定する。

## 統合ポイント

対象は `backend/nuts_calc_tex.py` の `ContentAreaLayout`、`build_content_area_slot_tex`、各 `build_*_slot_content_tex` と既存 `build_*_block_tex`。Flask routing と PDF attachment は `test_web_backend_app.py` が担う。

## 注意事項・既知の制限

TeX文字列の構成だけを検証し、実際の LaTeX compile や画像差分は扱わない。

## 変更履歴（git log より自動生成）

- feat(#225): migrate commondenom to the internal presentation API
- 84c789b feat(#224): migrate compare to the internal presentation API (#273)
- c22ee17 feat(#223): migrate ope --missing-value to the internal presentation API
- 7585ce7 feat(#229): migrate the 100 hundred-square command to the internal presentation API (#271)
- ce8f8b6 feat(#222): migrate dec2frac to the internal presentation API (#261)
- 4cb1c11 feat(#221): migrate frac2dec to presentation API
- 156c2d2 Merge remote-tracking branch 'origin/main' into feat/220-migrate-simplify-presentation-api
- ab8daf7 feat(#220): migrate simplify PDF generation
- 1fe5a14 feat(#219): migrate divfrac to presentation API
- 5cd034c feat(#218): migrate mixed PDF generation (#253)
- 5736b74 feat(#217): migrate frac PDF generation (#252)
- 1c331f9 feat(#216): migrate divisors to presentation API (#251)
