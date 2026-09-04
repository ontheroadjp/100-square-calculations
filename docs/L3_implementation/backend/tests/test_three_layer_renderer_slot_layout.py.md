# `backend/tests/test_three_layer_renderer_slot_layout.py`

## 目的・役割

`three_layer_renderer._resolve_number_placement`(issue #355)が `/generate-pdf`
request dict から Layer 2 の `inline` グリッド番号位置を正しく選ぶことを、LaTeX
実行なしで検証する単体テスト。短1行ドリルには中央寄せの別配置
(`_SHORT_DRILL_NUMBER_PLACEMENT` = `'inline'`)、それ以外は既定 `'gutter'` を
返すこと、および allowlist が conservative でありバイト等価を壊さないことを固定する。

## 動作の概要と主要な判定ロジック

- `test_the_alternate_placement_is_a_valid_non_default_number_placement`: 別配置
  定数が既定と異なり、`nuts_calc_tex.NumberPlacement` の許容値であることを確認する。
- `test_short_single_line_drills_get_the_alternate_placement`(parametrized): 別配置
  `'inline'` を返すべき request 群 —
  - `_SHORT_SINGLE_LINE_COMMAND_TYPES`(`99`/`squ`/`pi`/`com`/`evenodd`/`lcm`/`gcd`)
  - plain 2項 `ope`(桁数・大きさ・小数・余りあり除算・加減混在は許容)
  - **全 `sources` が短1行の `review`**(issue #365): 全 source が `ope` plain 2項
    (`g1-review`)や、`ope` + `_SHORT_SINGLE_LINE_COMMAND_TYPES` の混在でも各 source
    が短1行なら別配置。
- `test_everything_else_keeps_the_gutter_placement`(parametrized): 既定 `'gutter'`
  を保つべき request 群 —
  - allowlist 外の `command_type`(`frac`/`mixed`/`compare`/`100`/`divfrac`/`approx`/
    `multiples`/`divisors`/`aBc`)
  - **wide な source を1つでも含む `review`**(issue #365): `frac` 混在(= `g3-review`)、
    `terms:3` の多項チェーン混在、`vertical:True` の筆算混在、および `sources` が空 /
    キー自体が無い `review`。
  - 3列以上のグリッド(短 `command_type` でも詰まっているため別配置不要)
  - 複数行・幅可変の `ope` variant(`vertical`/`intermediate`/`use_parentheses`/
    `missing_value`/`mixed_operators`/`terms*`)
- `test_columns_ceiling_overrides_a_short_command_type`: `columns=4` の `squ` が
  `command_type` 判定より先に `gutter` へ落ちることを確認する。

## 重要な設計判断

`review` は複数ドリルを1グリッドに混ぜるため、`_review_is_short_single_line` は
**全 source が個別に短1行判定を通る**ときだけ別配置を許す(1つでも wide な source が
あると中央寄せの列がガタつくため)。この設計により `g3-review`(`frac` を含む)は
issue #355 導入時の `gutter` 出力をバイト等価で維持し、`g1-review`(plain 2項 `ope`
×5)だけが `inline` になる。テストはこの境界を parametrized ケースで固定する。

## 統合ポイント

対象は `backend/three_layer_renderer.py` の `_resolve_number_placement` /
`_ope_is_short_single_line` / `_review_is_short_single_line` /
`_SHORT_SINGLE_LINE_COMMAND_TYPES` / `_SHORT_DRILL_MAX_COLUMNS` /
`_SHORT_DRILL_NUMBER_PLACEMENT`。実 PDF 生成経路は
`test_three_layer_renderer_review.py` と `test_web_backend_app.py` が担う。
frontend 側の `g1-review` recipe は `frontend/web/src/drillPresets.test.js` が検証する。

## 注意事項・既知の制限

`_resolve_number_placement` の戻り値だけを検証し、実際の LaTeX compile や
生成 TeX の差分は扱わない。

## 変更履歴（git log より自動生成）

- feat(#365): add the grade-1 multi-source review (総合問題) worksheet
