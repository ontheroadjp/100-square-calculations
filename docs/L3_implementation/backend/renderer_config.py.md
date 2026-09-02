# `backend/renderer_config.py`

## 目的・役割

Flask バックエンドの3エンドポイント(`POST /generate-pdf` / `POST /generate-problems` / `GET /renderer-info`)が使うレンダラーを `NUTS_CALC_RENDERER` 環境変数から解決し、それらのエンドポイントが受け取る JSON リクエストボディの形を表す共有 `TypedDict` `RendererRequest` を定義するだけの、Flask 非依存モジュール。

issue #36 では `renderers.py` という名前で「レンダラー選択・CLI コマンド構築・subprocess 実行」を担っていたが、`POST /generate-pdf` が全 command_type を内部プレゼンテーション API(3層モデル、`backend/three_layer_renderer.py`)でプロセス内生成するようになった(issue #174)ため、issue #297(#174 段3)で以下を削除し、モジュール名を `renderer_config.py` に変更した:

- `build_command()`(`RendererRequest` dict → `nuts_calc_tex.py` の CLI 引数配列への変換)
- `run()`(`subprocess.run` による `nuts_calc_tex.py` 起動)
- CLI フラグ変換テーブル `CARRY_MODE_FLAGS` / `REMAINDER_MODE_FLAGS` / `REDUCIBLE_MODE_FLAGS` / `DIVIDEND_MODE_FLAGS`
- `backend/app.py` の `_USE_LEGACY_PDF_PIPELINE` 切替定数と `if _USE_LEGACY_PDF_PIPELINE:` 分岐

## 動作の概要

- `RENDERER_ENV_VAR`(`"NUTS_CALC_RENDERER"`)/ `DEFAULT_RENDERER`(`"latex"`、issue #186 で `"reportlab"` から変更)。
- `RENDERER_SCRIPTS`: レンダラー名 → スクリプト絶対パス(`BACKEND_DIR / "nuts_calc_tex.py"`、`BACKEND_DIR` は `Path(__file__).resolve().parent`)のレジストリ。issue #232 以前は `"reportlab"`(`nuts_calc.py`)のエントリも持っていたが、同 issue の削除に伴い `"latex"` の1エントリのみ。
- `get_renderer_name()`: `NUTS_CALC_RENDERER` を読み、未設定なら `DEFAULT_RENDERER` を返す。`RENDERER_SCRIPTS` に無い値(明示的な `reportlab` を含む)は許可値一覧付きの `ValueError` を送出する。呼び出しごとに env を再読み込みする(テスト容易性を優先。`monkeypatch.setenv`)。
- `RendererRequest`(`TypedDict`、`total=False`): リクエスト params の型ヒント。全キー任意。`carry_mode` / `remainder_mode` / `reducible_mode`(`Literal["required","none","mixed"]`)、`dividend_mode`(`Literal["integer","decimal","mixed"]`)を含む。`a_multiple: int` / `b_multiple: int`(issue #331、`result_max` の直後)は2項 `ope` add/sub のオペランドを N の倍数に制限するキーで、`nuts_calc_tex.generate_ope_problems` まで [[problem_generation.py]] / [[three_layer_renderer.py]] が転送する([[nuts_calc_tex.py]] の `### ope --a-multiple/--b-multiple` 参照)。`num: int` は `backend/problem_generation.py` 専用(`POST /generate-problems` の生成問題数)。`reverse` / `merge` / `csv` / `debug` は **予約フィールド**: 3層モデルレンダラーは honor しない(`reverse` のみ `99`/`squ`/`pi` で honor、issue #292)。将来 CLI を3層モデルへ移行する際の統一 presentation API の布石として、legacy 経路削除(issue #297)後も残す。`nuts_calc_tex.py` の CLI オプション `--reverse` / `--merge` / `--csv` / `--debug` 自体は無改変。

## 重要な設計判断とその理由

### レンダラー切り替えの仕組みを残した理由

`nuts_calc.py`(ReportLab)は issue #232 でコード自体が削除され `RENDERER_SCRIPTS` は現在 `"latex"` の1エントリのみだが、`get_renderer_name()` はレンダラー名をハードコードせず、将来2つ目のレンダラーが追加された場合は `RENDERER_SCRIPTS` にエントリを1つ加えるだけで動作する設計を維持している(2026-08-20 決定)。

### `UNAVAILABLE_RENDERERS` を廃止した理由(issue #232)

issue #186 時点では `RENDERER_SCRIPTS` に `"reportlab"` エントリが残っていたため、`get_renderer_name()` に `UNAVAILABLE_RENDERERS = {"reportlab"}` という専用チェックを置き「現在利用不可」の個別メッセージで拒否していた。issue #232 で `RENDERER_SCRIPTS` から `"reportlab"` エントリ自体を削除したため、「`RENDERER_SCRIPTS` に無い値は許可値一覧付き `ValueError`」という汎用チェックだけで同じ結果を得られるようになり、専用の除外リストが不要になった。

### `build_command` / `run` を削除した理由(issue #297)

`build_command`/`run` は web バックエンドが `nuts_calc_tex.py` を外部コマンドとして subprocess 起動するためのアダプタ層だった。`POST /generate-pdf` が `backend/three_layer_renderer.py` の `render_worksheet_pdf`(`nuts_calc_tex.py` の内部関数をプロセス内で直接呼ぶ)へ全面移行し(issue #174)、`_USE_LEGACY_PDF_PIPELINE = False` を既定にした(issue #291)ことで、この subprocess アダプタは全リクエストで到達不能になった。緊急ロールバック用に一時的に温存されていたが、3層モデル経路が legacy の忠実な上位互換であることが確認された(issue #292)ため、2026-09-01 の #297 `/mtg` の go 判断を経て一括削除した。

## 統合ポイント

- 呼び出し元: `backend/app.py`(`generate_pdf()` / `generate_problems()` / `renderer_info()` が `get_renderer_name()` を呼ぶ)、`backend/problem_generation.py`(`generate_problems()` が `get_renderer_name()` を呼び、モジュール全体が `RendererRequest` を型注釈に使う)、`backend/three_layer_renderer.py`(`RendererRequest` を型注釈に使う)。
- 呼び出し先: なし(標準ライブラリ `os` / `pathlib` のみ)。`backend/factory.sh` は本ファイルを経由せず `nuts_calc_tex.py` を直接 subprocess 実行する。

## 注意事項・既知の制限

- レンダラー選択は env 変数のみで、リクエストごとの指定はできない(issue #36 のスコープ)。`GET /renderer-info` はこの env 変数由来のレンダラー名を読み取り専用で公開するだけで、切り替え手段ではない。
- issue #297 以降、本モジュールは PDF もデータも生成しない。`POST /generate-pdf` の PDF 生成は `backend/three_layer_renderer.py`、`POST /generate-problems` のデータ生成は `backend/problem_generation.py` が担う。

## 変更履歴(git log より自動生成)

- 56b66ad refactor(#297): delete the legacy /generate-pdf subprocess rendering path (rename renderers.py -> renderer_config.py)
- ba08963 feat(#317): add integer/decimal dividend selection to grade 5 decimal division
- 40dfb0a feat(#313): add mixed decimal operand order to grade 4 integer/decimal multiplication (#314)
- 37a5a80 #230 Split a_value/b_value's overloaded digit-count/direct-value semantics into a_digits/b_digits (#236)
- 700f115 #232 backend: remove nuts_calc.py (ReportLab renderer) and the reportlab dependency (#234)
- 9393898 #186 renderers/engine: make latex+lualatex the default (and only reachable) configuration (#187)
- 13bef63 #138 backend: add POST /generate-problems for PDF-free ope problem generation (#175)
