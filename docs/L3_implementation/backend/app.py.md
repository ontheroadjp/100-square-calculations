# `backend/app.py`

## 目的・役割

`nuts_calc.py`/`nuts_calc_tex.py` を Web 経由で呼び出すための薄い Flask API。エンドポイントは `POST /generate-pdf`(PDF 生成)、`POST /generate-problems`(問題データのみ生成、PDF非生成、issue #138)、`GET /renderer-info`(現在有効なレンダラー名の取得、issue #46)の3つ。コマンド構築・レンダラー選択・subprocess 実行のロジックは `backend/renderers.py`([[renderers.py]] 参照、issue #36)に、問題データのみのプロセス内直接生成ロジックは `backend/problem_generation.py`([[problem_generation.py]] 参照、issue #138)に切り出されており、本ファイルは JSON パース・`renderers`/`problem_generation` 呼び出し・HTTP レスポンス変換のみを担う。

## 動作の概要

- `POST /generate-pdf`: 必須パラメータ(`paper_size`/`command_type`)のみ本ファイルで検証し(`app.py:21-22`)、それ以外のコマンド構築は行わない。`renderers.get_renderer_name()` で env 変数 `NUTS_CALC_RENDERER`(`reportlab`|`latex`、デフォルト `reportlab`)からレンダラーを解決し、`renderers.run(data, PDF_OUTPUT_DIR, renderer_name)` を呼ぶ(`app.py:24-27`)。`data`(リクエスト JSON)はそのまま `renderers.run` に渡され、CLI 引数への変換は `renderers.build_command` が担う。成功時は生成された PDF をそのまま `send_file` で返す。失敗時は例外の型に応じて `{'error': ...}` を HTTP 500 で返す: `ValueError`(レンダラー名不正・必須パラメータ欠如)、`subprocess.CalledProcessError`(レンダラー実行失敗)、`FileNotFoundError`(スクリプト未検出)、その他 `Exception`。
- `POST /generate-problems`(issue #138): 必須パラメータ(`paper_size`/`command_type`/`num`、`num` は正の整数)を本ファイルで検証する(`app.py`の`generate_problems`ハンドラ)。`renderers.get_renderer_name()` でレンダラーを解決し、`problem_generation.generate_problems(data, renderer_name)` を呼ぶ。成功時は `{'problems': [...]}` をそのまま JSON で返す(PDFファイルは生成しない)。`command_type='ope'` 以外や `ope` の一部亜種フラグなど未対応の入力は `problem_generation` 側が送出する `ValueError` を捕捉し `{'error': ...}` を HTTP 500 で返す(`/generate-pdf` と同じ「必須パラメータ欠如は400、ロジック層のエラーは500」という区分けを踏襲)。
- `GET /renderer-info`(issue #46): `renderers.get_renderer_name()` の結果をそのまま `{'renderer': 'reportlab'|'latex'}` として返す。`nuts_calc.py` が `--vertical`(筆算)を持たなくなった(issue #46)ため、`frontend/spa` がリクエスト前にどちらのレンダラーが有効かを判定し、`latex` の場合のみ筆算 UI を出す目的で追加された(`frontend/spa/src/GradeDrills.jsx`/`CustomGenerator.jsx` 参照)。env 変数が不正な場合は `renderers.get_renderer_name()` が送出する `ValueError` を捕捉し、`{'error': ...}` を HTTP 500 で返す。

## 統合ポイント

- 呼び出し元: `frontend/spa/src/CustomGenerator.jsx`(`POST /generate-pdf`)、`frontend/spa/src/GradeDrills.jsx`(`GET /renderer-info`、マウント時に1回)。`POST /generate-problems` は issue #138 時点でまだフロントエンドから呼ばれていない(issue #137 の動的プレビュー系サブissueが将来の呼び出し元候補)。
- 呼び出し先: `backend/renderers.py`(レンダラー選択・PDF生成実行)、`backend/problem_generation.py`(問題データのみのプロセス内直接生成)。

## 注意事項・既知の制限

- `nuts_calc.py`/`nuts_calc_tex.py` 側のバリデーション失敗メッセージは `print()`(stdout)に出力されるため、`subprocess.CalledProcessError` ハンドラは `e.stdout` を優先し(空なら `e.stderr` にフォールバック)、それを `error` フィールドに含める(issue #37 で修正)。`nuts_calc.py` 側でも `com`/`99`/`squ`/`pi`/`100` のバリデーション失敗が引数なし `exit()`(終了コード0、`subprocess.run(check=True)` が例外を送出しない)になっていた不具合を同 issue で `exit(1)` に修正済み([[../../../nuts_calc.py]] 参照)。修正前はこの経路で `CalledProcessError` すら発生せず、後続の `send_file` が `FileNotFoundError` になり実際の理由と無関係な「Renderer script not found」を返していた。
- backend の URL がフロントエンド側にハードコードされている(`frontend/spa/src/CustomGenerator.jsx`/`GradeDrills.jsx` 側の既知の制約、[[../../frontend/src/CustomGenerator.jsx]] 参照)。
- レンダラー選択は env 変数のみで、リクエストごとの指定はできない(issue #36 のスコープ)。`GET /renderer-info` はこの env 変数由来のレンダラー名をフロントエンドに公開する読み取り専用エンドポイントであり、フロントエンドからレンダラーを切り替える手段ではない。

## 変更履歴(git log より自動生成)

- a29ed4a feat(#138): add POST /generate-problems for PDF-free ope problem generation
- 9ead364 refactor(#46): remove --vertical from nuts_calc.py; gate written-calculation UI on active renderer
- 53eb72d fix(#37): surface renderer stdout in error responses; use exit(1) for -a/-b validation failures
- 155caf8 feat(#36): switch web/backend renderer between nuts_calc.py and nuts_calc_tex.py via env var
- cfea9ed fix(#4): fix 9 logic bugs found in CLI, web backend, and frontend
- 0a11eaf feat(#9): add vertical (written-calculation) output format for ope command
- d9fc0a3 refactor: Rename 100masu.py to nuts_calc.py and remove setup.py
- 68daa78 feat: Implement web interface (React + Tailwind + Flask)
