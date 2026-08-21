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
- `divfrac` は pattern-1b の番号なし本文が答えを未約分のまま保持すること、blank 表示、legacy block との合成同値性を検証する(`test_nuts_calc_tex_content_area_layout.py:405-431`)。
- `divisors` は可変長のコンマ区切り約数リストと blank を保持し、legacy block と合成後の本文が一致することを検証する(`test_nuts_calc_tex_content_area_layout.py:568-591`)。

## 重要な設計判断

既存 CLI block formatter は互換経路として残し、内部 presentation API 用 slot formatter だけが番号描画を Layer 2 に委譲する。テストはこの責務分離と本文の表示互換性を同時に固定する。

## 統合ポイント

対象は `backend/nuts_calc_tex.py` の `ContentAreaLayout`、`build_content_area_slot_tex`、各 `build_*_slot_content_tex` と既存 `build_*_block_tex`。Flask routing と PDF attachment は `test_web_backend_app.py` が担う。

## 注意事項・既知の制限

TeX文字列の構成だけを検証し、実際の LaTeX compile や画像差分は扱わない。

## 変更履歴（git log より自動生成）

- 4cb1c11 feat(#221): migrate frac2dec to presentation API
- 156c2d2 Merge remote-tracking branch 'origin/main' into feat/220-migrate-simplify-presentation-api
- ab8daf7 feat(#220): migrate simplify PDF generation
- 1fe5a14 feat(#219): migrate divfrac to presentation API
- 5cd034c feat(#218): migrate mixed PDF generation (#253)
- 5736b74 feat(#217): migrate frac PDF generation (#252)
- 1c331f9 feat(#216): migrate divisors to presentation API (#251)
- c85124d Migrate multiples PDF generation to the presentation API (#249)
- 8117acc Migrate evenodd PDF generation to the presentation API (#248)
- 3370b1c #212 Migrate generate-pdf gcd to the internal presentation API (#246)
- 1c3fdee #211 generate-pdf: migrate lcm to the internal presentation API (#245)
- 429c088 #210 generate-pdf: migrate pi to the internal presentation API (#244)
- 40ad870 #209 generate-pdf: migrate squ to the internal presentation API (#243)
- a6187e9 #208 generate-pdf: migrate 99 (kuku) to the internal presentation API (#242)
- 7a159b9 #207 generate-pdf: migrate ope (multi-term) to the internal presentation API (#241)
