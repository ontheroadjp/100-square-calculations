# `backend/tests/test_nuts_calc_tex_abc_generation.py`

## 目的・役割

`nuts_calc_tex.py` の `aBc` 問題データ生成と TeX content formatter を LaTeX 実行なしで検証する単体テスト。

## 動作の概要と主要な判定ロジック

- 問題数、連番 index、各桁の 0〜9 制約、`AbcProblem.answer` と先頭ゼロを含む4桁表示を検証する(`test_nuts_calc_tex_abc_generation.py:18-42`)。
- 既存 `build_abc_block_tex` の blank/filled 表示と、内部 presentation API 用 `build_abc_slot_content_tex` が番号 prefix だけを除いた同一本体を返すことを検証する(`test_nuts_calc_tex_abc_generation.py:45-61`)。
- bottom answer と CSV 行のデータ契約を検証する(`test_nuts_calc_tex_abc_generation.py:64-79`)。

## 重要な設計判断

slot formatter のテストは Layer 2 の `\makebox` 出力との文字列一致ではなく、既存 block formatter から番号 prefix を除いた本文との一致を確認する。Layer 2 は番号ボックス幅が0でも `\makebox` 自体を出力するため、content-format の等価性とは別の責務だからである。

## 統合ポイント

対象は `backend/nuts_calc_tex.py` の `AbcProblem`、`generate_abc_problems`、`build_abc_block_tex`、`build_abc_slot_content_tex`、bottom-answer/CSV helpers。

## 注意事項・既知の制限

純粋関数テストであり PDF コンパイルは行わない。実 PDF と Flask routing は他の end-to-end/API テストが担う。
