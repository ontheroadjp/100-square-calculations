# `web/backend/app.py`

## 目的・役割

`nuts_calc.py` を Web 経由で呼び出すための薄い Flask API。エンドポイントは `POST /generate-pdf` の1つのみ。

## 動作の概要

- リクエスト JSON のキーを `nuts_calc.py` の CLI 引数に変換し(`app.py:34-54`)、サーバー側で生成した UUID ファイル名を `--out-file` に指定して `subprocess.run(..., check=True)` で実行する(`app.py:56-63`)。
- 成功時は生成された PDF をそのまま `send_file` で返す。失敗時(`CalledProcessError`/`FileNotFoundError`/その他)は `{'error': ...}` を HTTP 500 で返す(`ope`/`command_type` 必須チェックのみ 400)。

## 統合ポイント

- 呼び出し元: `web/frontend/src/CustomGenerator.jsx`(`fetch('http://127.0.0.1:5000/generate-pdf')`)。
- 呼び出し先: `nuts_calc.py`(`subprocess` 経由)。

## 注意事項・既知の制限

- `data.get(...)` で真偽値フラグを CLI フラグに変換する行(`descend`/`reverse`/`shuffle`/`intermediate`/`vertical`/`with_bottom_answer`/`merge`/`csv`/`debug`)は同じパターンの繰り返しで、`vertical`(`--vertical`、筆算形式出力、[[../../../nuts_calc.py]] 参照)もこの並びに追加してある(`app.py:47-48`)。
- `nuts_calc.py` 側のバリデーション失敗メッセージは `print()`(stdout)に出力されるが、このファイルは `subprocess.CalledProcessError` 発生時に `e.stderr` のみをエラーメッセージとして返すため、バリデーションエラーの具体的な理由がフロントエンドのエラー表示には渡らない(HTTP 500 は返るが `error` は空文字になる)。既存の全バリデーション(`-a option must be set.` 等)に共通する既知の制限であり、今回のスコープでは変更していない。
- backend の URL がフロントエンド側にハードコードされている(`web/frontend/src/CustomGenerator.jsx` 側の既知の制約、[[../../frontend/src/CustomGenerator.jsx]] 参照)。

## 変更履歴(git log より自動生成)

- 0a11eaf feat(#9): add vertical (written-calculation) output format for ope command
- d9fc0a3 refactor: Rename 100masu.py to nuts_calc.py and remove setup.py
- 68daa78 feat: Implement web interface (React + Tailwind + Flask)
