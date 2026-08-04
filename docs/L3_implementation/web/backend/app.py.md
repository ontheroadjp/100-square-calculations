# `web/backend/app.py`

## 目的・役割

`nuts_calc.py`/`nuts_calc_tex.py` を Web 経由で呼び出すための薄い Flask API。エンドポイントは `POST /generate-pdf`(PDF 生成)と `GET /renderer-info`(現在有効なレンダラー名の取得、issue #46)の2つ。コマンド構築・レンダラー選択・subprocess 実行のロジックは `web/backend/renderers.py`([[renderers.py]] 参照、issue #36)に切り出されており、本ファイルは JSON パース・`renderers` 呼び出し・HTTP レスポンス変換のみを担う。

## 動作の概要

- `POST /generate-pdf`: 必須パラメータ(`paper_size`/`command_type`)のみ本ファイルで検証し(`app.py:21-22`)、それ以外のコマンド構築は行わない。`renderers.get_renderer_name()` で env 変数 `NUTS_CALC_RENDERER`(`reportlab`|`latex`、デフォルト `reportlab`)からレンダラーを解決し、`renderers.run(data, PDF_OUTPUT_DIR, renderer_name)` を呼ぶ(`app.py:24-27`)。`data`(リクエスト JSON)はそのまま `renderers.run` に渡され、CLI 引数への変換は `renderers.build_command` が担う。成功時は生成された PDF をそのまま `send_file` で返す。失敗時は例外の型に応じて `{'error': ...}` を HTTP 500 で返す: `ValueError`(レンダラー名不正・必須パラメータ欠如)、`subprocess.CalledProcessError`(レンダラー実行失敗)、`FileNotFoundError`(スクリプト未検出)、その他 `Exception`。
- `GET /renderer-info`(issue #46): `renderers.get_renderer_name()` の結果をそのまま `{'renderer': 'reportlab'|'latex'}` として返す。`nuts_calc.py` が `--vertical`(筆算)を持たなくなった(issue #46)ため、`web/frontend` がリクエスト前にどちらのレンダラーが有効かを判定し、`latex` の場合のみ筆算 UI を出す目的で追加された(`web/frontend/src/GradeDrills.jsx`/`CustomGenerator.jsx` 参照)。env 変数が不正な場合は `renderers.get_renderer_name()` が送出する `ValueError` を捕捉し、`{'error': ...}` を HTTP 500 で返す。

## 統合ポイント

- 呼び出し元: `web/frontend/src/CustomGenerator.jsx`(`POST /generate-pdf`)、`web/frontend/src/GradeDrills.jsx`(`GET /renderer-info`、マウント時に1回)。
- 呼び出し先: `web/backend/renderers.py`(レンダラー選択・実行)。

## 注意事項・既知の制限

- `nuts_calc.py`/`nuts_calc_tex.py` 側のバリデーション失敗メッセージは `print()`(stdout)に出力されるため、`subprocess.CalledProcessError` ハンドラは `e.stdout` を優先し(空なら `e.stderr` にフォールバック)、それを `error` フィールドに含める(issue #37 で修正)。`nuts_calc.py` 側でも `com`/`99`/`squ`/`pi`/`100` のバリデーション失敗が引数なし `exit()`(終了コード0、`subprocess.run(check=True)` が例外を送出しない)になっていた不具合を同 issue で `exit(1)` に修正済み([[../../../nuts_calc.py]] 参照)。修正前はこの経路で `CalledProcessError` すら発生せず、後続の `send_file` が `FileNotFoundError` になり実際の理由と無関係な「Renderer script not found」を返していた。
- backend の URL がフロントエンド側にハードコードされている(`web/frontend/src/CustomGenerator.jsx`/`GradeDrills.jsx` 側の既知の制約、[[../../frontend/src/CustomGenerator.jsx]] 参照)。
- レンダラー選択は env 変数のみで、リクエストごとの指定はできない(issue #36 のスコープ)。`GET /renderer-info` はこの env 変数由来のレンダラー名をフロントエンドに公開する読み取り専用エンドポイントであり、フロントエンドからレンダラーを切り替える手段ではない。

## 変更履歴(git log より自動生成)

- (issue #46) feat: add GET /renderer-info endpoint so the frontend can detect the active renderer
- 155caf8 feat(#36): switch web/backend renderer between nuts_calc.py and nuts_calc_tex.py via env var
- cfea9ed fix(#4): fix 9 logic bugs found in CLI, web backend, and frontend
- 0a11eaf feat(#9): add vertical (written-calculation) output format for ope command
- d9fc0a3 refactor: Rename 100masu.py to nuts_calc.py and remove setup.py
- 68daa78 feat: Implement web interface (React + Tailwind + Flask)
