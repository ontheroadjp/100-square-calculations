# `backend/tests/test_three_layer_renderer_review.py`

## 目的・役割

`backend/three_layer_renderer.py` の multi-source 「総合問題」ワークシートビルダー(issue #140、`command_type == 'review'`)を検証する。複数の別ドリルの問題を1枚に混在させる合成ロジックと、その入力検証・ウェイト按分・シャッフル決定性・`kind` ディスパッチを対象とする。

## 動作の概要と主要な判定ロジック

大半は pure-Python: `stub_engine` fixture が `three_layer_renderer.shutil.which` と両 LaTeX adapter(`LuaLatexEngineAdapter` / `PdflatexEngineAdapter`)の `compile` を monkeypatch し、生成 TeX を捕捉してダミー PDF を書く(`test_web_backend_app.py` と同じパターン)。1件だけ、`lualatex`/`pdflatex` のいずれも PATH に無いとき skip する実コンパイルの e2e テストを持つ。

- **`build_review_slot_content_tex` のディスパッチ**(`nuts_calc_tex.py`): `kind == 'ope'` は `build_ope_slot_content_tex`、`kind == 'frac'` は `build_fraction_slot_content_tex` へ委譲すること(手組みの `OpeProblem` / `FractionProblem` を payload に、それぞれの formatter の出力と一致することで確認)、未知 `kind` は `ValueError`。
- **ソース生成器**: `_review_ope_problems` / `_review_frac_problems` が指定個数・正しい `kind`・正しい payload 型を返すこと(`ope` は `operator` 反映、`frac` は `same_denominator`/`proper_result` により同分母・真分数になること)。
- **`_distribute_review_counts(weights, order)`**: ウェイト比按分(最大剰余法)を parametrize で検証 —— ウェイト合計 == `order` なら各ソースがウェイトそのまま、`[4,4,4,4,4]` を 10/20/30 スロットへ均等按分、`[3,1]→[15,5]`、`[1,1,1]→[7,7,6]`。
- **`_generate_review_pdf` の合成**: g3 相当の 5 ソース(`GRADE3_SOURCES`)で1ページ20スロットに全ソースが混在すること(`\problemnumberstyle{1)}`〜`{20)}`、`\div` と `\fractioneq{` の両方が TeX に出現)。`page: 3` で3ページ・スロット番号が跨いで 1..60 まで続くこと。`with_name_field` の反映。
- **シャッフル決定性**: ソース生成器と `build_presentation_document_tex` を monkeypatch し、`review_seed` を固定した2回のレンダリングでスロット順が一致すること、シャッフルが実際に並べ替えること(seed=123 が identity と異なる)、`shuffle: false` なら生成順のままであること。
- **入力検証**(`_render` = `render_worksheet_pdf` 経由): `sources` 欠落・空・要素が非オブジェクト・未対応 `command_type`(`compare` 等)・`num` が非正/非整数 → `ValueError`。`rows`/`columns` 過小 → `ValueError`。g3 ソースを 5×2 グリッド(10問)へ渡すとウェイトが 2 ずつへスケールされること。

## 統合ポイント

- 対象: `backend/three_layer_renderer.py` の `_review_ope_problems` / `_review_frac_problems` / `_REVIEW_SOURCE_GENERATORS` / `_resolve_review_sources` / `_distribute_review_counts` / `_generate_review_pdf`、および `render_worksheet_pdf` の `review` 分岐。`backend/nuts_calc_tex.py` の `ReviewProblem` / `build_review_slot_content_tex`。
- 呼び出し先の monkeypatch 対象: `three_layer_renderer.shutil` / `three_layer_renderer.nuts_calc_tex`(モジュール先頭で `import three_layer_renderer` / `import nuts_calc_tex`)。

## 注意事項・既知の制限

- 実 HTTP server は起動しない(`render_worksheet_pdf` を直接呼ぶ)。`POST /generate-pdf` 経由の HTTP レベルは `test_web_backend_app.py` の担当(現時点で `review` 専用ケースは未追加、必要になれば追記する)。
- 問題生成自体の乱数は seed で固定しない(他ビルダー同様)。`review_seed` はシャッフル順のみを決定的にする。

## 変更履歴（git log より自動生成）

- a116853 feat(#140): add the grade-3 multi-source review (総合問題) worksheet
