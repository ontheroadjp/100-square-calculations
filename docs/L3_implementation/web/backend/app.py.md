# `web/backend/app.py`

## 目的・役割

`nuts_calc.py`/`nuts_calc_tex.py` を Web 経由で呼び出すための薄い Flask API。エンドポイントは `POST /generate-pdf` の1つのみ。コマンド構築・レンダラー選択・subprocess 実行のロジックは `web/backend/renderers.py`([[renderers.py]] 参照、issue #36)に切り出されており、本ファイルは JSON パース・`renderers` 呼び出し・HTTP レスポンス変換のみを担う。

## 動作の概要

- 必須パラメータ(`paper_size`/`command_type`)のみ本ファイルで検証し(`app.py:20-21`)、それ以外のコマンド構築は行わない。
- `renderers.get_renderer_name()` で env 変数 `NUTS_CALC_RENDERER`(`reportlab`|`latex`、デフォルト `reportlab`)からレンダラーを解決し、`renderers.run(data, PDF_OUTPUT_DIR, renderer_name)` を呼ぶ(`app.py:23-26`)。`data`(リクエスト JSON)はそのまま `renderers.run` に渡され、CLI 引数への変換は `renderers.build_command` が担う。
- 成功時は生成された PDF をそのまま `send_file` で返す。失敗時は例外の型に応じて `{'error': ...}` を HTTP 500 で返す: `ValueError`(レンダラー名不正・必須パラメータ欠如)、`subprocess.CalledProcessError`(レンダラー実行失敗)、`FileNotFoundError`(スクリプト未検出)、その他 `Exception`。

## 統合ポイント

- 呼び出し元: `web/frontend/src/CustomGenerator.jsx`(`fetch('http://127.0.0.1:5000/generate-pdf')`)。
- 呼び出し先: `web/backend/renderers.py`(レンダラー選択・実行)。

## 注意事項・既知の制限

- `nuts_calc.py`/`nuts_calc_tex.py` 側のバリデーション失敗メッセージは `print()`(stdout)に出力されるが、このファイルは `subprocess.CalledProcessError` 発生時に `e.stderr` のみをエラーメッセージとして返すため、バリデーションエラーの具体的な理由がフロントエンドのエラー表示には渡らない(HTTP 500 は返るが `error` は空文字になる)。両レンダラー共通の既知の制限であり、issue #37 で追跡中(今回のスコープでは未修正)。
- backend の URL がフロントエンド側にハードコードされている(`web/frontend/src/CustomGenerator.jsx` 側の既知の制約、[[../../frontend/src/CustomGenerator.jsx]] 参照)。
- レンダラー選択は env 変数のみで、リクエストごとの指定はできない(フロントエンドはレンダラーの違いを一切意識しない設計、issue #36 のスコープ)。

## 変更履歴(git log より自動生成)

- cfea9ed fix(#4): fix 9 logic bugs found in CLI, web backend, and frontend
- 0a11eaf feat(#9): add vertical (written-calculation) output format for ope command
- d9fc0a3 refactor: Rename 100masu.py to nuts_calc.py and remove setup.py
- 68daa78 feat: Implement web interface (React + Tailwind + Flask)
