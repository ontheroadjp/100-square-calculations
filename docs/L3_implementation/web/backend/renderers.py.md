# `web/backend/renderers.py`

## 目的・役割

`web/backend/app.py` の `POST /generate-pdf` エンドポイントが呼び出す「レンダラー選択・CLI コマンド構築・subprocess 実行」ロジックを、Flask に一切依存しない純粋関数として切り出したモジュール(issue #36)。`nuts_calc.py`(ReportLab)と `nuts_calc_tex.py`(LaTeX、[[../../../../nuts_calc_tex.py]] 参照)の2レンダラーを env 変数で切り替え可能にする。

## 動作の概要

- `RENDERER_SCRIPTS`(`renderers.py:38-41`): レンダラー名(`'reportlab'`/`'latex'`)から呼び出すスクリプトの絶対パス(`REPO_ROOT / 'nuts_calc.py'` / `REPO_ROOT / 'nuts_calc_tex.py'`、`REPO_ROOT` は `Path(__file__)` から2階層上に解決)へのレジストリ。スクリプトパスを絶対パス化しているため、呼び出し元プロセスの cwd に依存せずスクリプトを解決できる。
- `get_renderer_name()`(`renderers.py:44-56`): env 変数 `NUTS_CALC_RENDERER` を読み、未設定なら `DEFAULT_RENDERER`(`'reportlab'`、既存動作を保つデフォルト)を返す。`RENDERER_SCRIPTS` に無い値が指定された場合は許可値一覧を含む `ValueError` を送出する。
- `build_command(renderer_name, params, out_file)`(`renderers.py:59-119`): リクエストの `params`(dict)を CLI 引数に変換する。`nuts_calc.py` と `nuts_calc_tex.py` は `paper_size`/`command`/`-a`/`-b`/`--rows`/`--descend` 等の CLI 引数体系がほぼ完全に一致しているため、このロジックはレンダラー間で共用しており、`RENDERER_SCRIPTS[renderer_name]` で選んだスクリプトパスのみが異なる。`paper_size`/`command_type` が欠けている場合は `ValueError` を送出する(旧 `app.py` のインライン実装と同じ挙動)。
- `run(params, output_dir, renderer_name=None)`(`renderers.py:122-141`): `renderer_name` 省略時は `get_renderer_name()` で解決し、UUID ファイル名を生成して `subprocess.run(..., check=True)` を実行、`(output_filepath, output_filename, completed_process)` を返す。呼び出し元(`app.py`)が `completed_process.stdout`/`.stderr` をログに使う。例外(`subprocess.CalledProcessError`/`FileNotFoundError`/`ValueError`)は呼び出し元に伝播させ、HTTP レスポンスへの変換は行わない(Flask 非依存の設計方針)。
- `RendererRequest`(`TypedDict`、`renderers.py:8-29`): リクエスト params の型ヒント。全キー任意(`total=False`)。

## 重要な設計判断とその理由

### Flask に依存しない設計にした理由

issue #19 のトラッキング issue にある「将来 `nuts_calc.py`/`nuts_calc_tex.py` を同じ CLI 契約で切り替えられるラッパーを作る」という構想、および issue #36 の背景にある「将来的に専用 API として独立させたい(ただし `nuts_calc_tex.py` の PDF 品質チューニングが先)」という方針に基づき、`build_command`/`run` はいずれも Flask の `request`/`jsonify` に一切触れず、プレーンな `dict` を受け取る設計にしている。これにより、将来 API を独立サービス化する際は本ファイルをほぼそのまま移設でき、`app.py` 側は HTTP クライアントに差し替えるだけで済む。

### subprocess 呼び出しに `cwd` を指定していない理由

実装時に一度 `subprocess.run(..., cwd=REPO_ROOT)` を試したが、`--out-file` はサーバー側で `os.path.join(output_dir, ...)` により生成される相対パス(`PDF_OUTPUT_DIR = './generated_pdfs'`、呼び出し元プロセスの cwd 基準)であるため、`cwd=REPO_ROOT` を指定すると `nuts_calc.py`/`nuts_calc_tex.py` 側の `--out-file` 解決先が呼び出し元の cwd からずれて `FileNotFoundError` になる実バグを起こした。スクリプトパス自体は `RENDERER_SCRIPTS` で既に絶対パス解決済みのため `cwd` を変更する必要はなく、`subprocess.run` は cwd 未指定(呼び出し元プロセスの cwd を継承)のままにしている。

### コマンド構築ロジックを共用している理由

`nuts_calc.py`(`nuts_calc.py:100-277` の `_init()`)と `nuts_calc_tex.py`(`nuts_calc_tex.py:80-266` の `_init()`)の CLI 引数体系(`paper_size`/`command`/`-a`/`-b`/`--a-min`/`--a-max`/`--b-min`/`--b-max`/`-o`/`--descend`/`--reverse`/`--shuffle`/`--intermediate`/`--vertical`/`-r`/`-c`/`-ww`/`-p`/`-m`/`--csv`/`--out-file`/`--debug`)は完全に一致することを実装前に比較確認済み。このため `build_command` はレンダラー間で分岐させず、スクリプトパスの選択のみをレンダラー固有の差分として扱っている。

## 統合ポイント

- 呼び出し元: `web/backend/app.py`(`POST /generate-pdf` ルートハンドラ)のみ。
- 呼び出し先: `nuts_calc.py` または `nuts_calc_tex.py`(`subprocess` 経由)。`latex` レンダラーは `nuts_calc_tex.py` 側で `pdflatex` の存在チェックを行う([[../../../../nuts_calc_tex.py]] 参照)。

## 注意事項・既知の制限

- `nuts_calc.py`/`nuts_calc_tex.py` 双方とも、バリデーション失敗メッセージを `print()`(stdout)で出力してから `exit()`/`exit(1)` する実装のため、`subprocess.CalledProcessError.stderr` は空文字になりうる。`app.py` 側の現在のエラーハンドリングは `e.stderr` のみを HTTP レスポンスに含めるため、バリデーション失敗の具体的理由がフロントエンドに届かない既知の制限がある(`docs/L3_implementation/web/backend/app.py.md` 参照、issue #37 で追跡)。
- `get_renderer_name()` は呼び出しごとに env 変数を再読み込みする(プロセス起動時にキャッシュしない)。Flask アプリのライフサイクル中に env 変数が変わることは通常想定されないため実用上の影響はないが、テスト容易性(`monkeypatch.setenv`)を優先した設計。

## 変更履歴(git log より自動生成)

- (未コミット: issue #36 で新規作成)
