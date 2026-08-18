# `backend/renderers.py`

## 目的・役割

`backend/app.py` の `POST /generate-pdf` エンドポイントが呼び出す「レンダラー選択・CLI コマンド構築・subprocess 実行」ロジックを、Flask に一切依存しない純粋関数として切り出したモジュール(issue #36)。`nuts_calc.py`(ReportLab)と `nuts_calc_tex.py`(LaTeX、[[../../../../nuts_calc_tex.py]] 参照)の2レンダラーを env 変数で切り替え可能にする。

## 動作の概要

- `RendererRequest` と `build_command()` は `frac` 用の `numerator_digits`/`denominator_digits` を値付きCLIオプションへ、`same_denominator`/`different_denominators`/`proper_operands`/`proper_result` を真偽フラグへ変換する。これらは `latex` レンダラーの `nuts_calc_tex.py` だけが解釈するため、呼び出し側がレンダラー情報に基づいて送信可否を制御する(`backend/renderers.py:8-38,83-126`)。
- `RendererRequest.result_max` は Web リクエストの整数値を `--result-max <value>` へ変換する。これは `nuts_calc_tex.py` の `ope` 全式形式に共通する最終結果上限であり、LaTeX専用パラメーターとして呼び出し側が `latexOnly` 項目からのみ送る(`backend/renderers.py:9-54,130-144`)。

- `RENDERER_SCRIPTS`(`renderers.py:38-41`): レンダラー名(`'reportlab'`/`'latex'`)から呼び出すスクリプトの絶対パス(`BACKEND_DIR / 'nuts_calc.py'` / `BACKEND_DIR / 'nuts_calc_tex.py'`、`BACKEND_DIR` は `Path(__file__).resolve().parent`)へのレジストリ。`nuts_calc.py`/`nuts_calc_tex.py` は `renderers.py` と同じ `backend/` 直下にあるため、単純に `Path(__file__)` の親ディレクトリを基準に解決する(issue #88 のリポジトリ再編で `web/backend/renderers.py` から `backend/renderers.py` へ移動した際、旧 `REPO_ROOT = BACKEND_DIR.parent.parent`(2階層上、当時は `web/backend/` の2階層上がリポジトリルートだった)から変更)。スクリプトパスを絶対パス化しているため、呼び出し元プロセスの cwd に依存せずスクリプトを解決できる。
- `get_renderer_name()`(`renderers.py:44-56`): env 変数 `NUTS_CALC_RENDERER` を読み、未設定なら `DEFAULT_RENDERER`(`'reportlab'`、既存動作を保つデフォルト)を返す。`RENDERER_SCRIPTS` に無い値が指定された場合は許可値一覧を含む `ValueError` を送出する。
- `build_command(renderer_name, params, out_file)`(`renderers.py:59-119`): リクエストの `params`(dict)を CLI 引数に変換する。`nuts_calc.py` と `nuts_calc_tex.py` は `paper_size`/`command`/`-a`/`-b`/`--rows`/`--descend` 等の CLI 引数体系がほぼ完全に一致しているため、このロジックはレンダラー間で共用しており、`RENDERER_SCRIPTS[renderer_name]` で選んだスクリプトパスのみが異なる。`paper_size`/`command_type` が欠けている場合は `ValueError` を送出する(旧 `app.py` のインライン実装と同じ挙動)。
- `run(params, output_dir, renderer_name=None)`(`renderers.py:122-141`): `renderer_name` 省略時は `get_renderer_name()` で解決し、UUID ファイル名を生成して `subprocess.run(..., check=True)` を実行、`(output_filepath, output_filename, completed_process)` を返す。呼び出し元(`app.py`)が `completed_process.stdout`/`.stderr` をログに使う。例外(`subprocess.CalledProcessError`/`FileNotFoundError`/`ValueError`)は呼び出し元に伝播させ、HTTP レスポンスへの変換は行わない(Flask 非依存の設計方針)。
- `RendererRequest`(`TypedDict`、`renderers.py:9-48`): リクエスト params の型ヒント。全キー任意(`total=False`)。`carry_mode` は `Literal['required','none','mixed']` で、`CARRY_MODE_FLAGS` が順に `--carry-borrow`/`--no-carry-borrow`/`--mixed-carry-borrow` へ変換する。未知値は無視せず `ValueError` にする(`renderers.py:26,62-66,143-150`)。`missing_value: bool` や `terms` 系も同様にLaTeX専用パラメータとして保持する。`remainder_mode`(`Literal['required','none','mixed']`、issue #91)は `carry_mode` と全く同じパターンで、`REMAINDER_MODE_FLAGS` が `--remainder`/`--no-remainder`/`--mixed-remainder` へ変換し、未知値は同様に `ValueError` にする。`reducible_mode`(`Literal['required','none','mixed']`、issue #114)も同じパターンで、`REDUCIBLE_MODE_FLAGS` が `--require-reducible`/`--no-reducible`/`--mixed-reducible` へ変換する(`frac`/`mixed` の乗除算専用、[[../../../../nuts_calc_tex.py]] 参照)。`with_name_field: bool`(issue #93)は `with_bottom_answer` と同じ単純な真偽フラグパターンで、真の場合のみ `--with-name-field` を追加する(`renderers.py:180-181`)。LaTeX専用パラメータのため、`nuts_calc.py` 側にはこのフラグに対応する実装がない。

## 重要な設計判断とその理由

### Flask に依存しない設計にした理由

issue #19 のトラッキング issue にある「将来 `nuts_calc.py`/`nuts_calc_tex.py` を同じ CLI 契約で切り替えられるラッパーを作る」という構想、および issue #36 の背景にある「将来的に専用 API として独立させたい(ただし `nuts_calc_tex.py` の PDF 品質チューニングが先)」という方針に基づき、`build_command`/`run` はいずれも Flask の `request`/`jsonify` に一切触れず、プレーンな `dict` を受け取る設計にしている。これにより、将来 API を独立サービス化する際は本ファイルをほぼそのまま移設でき、`app.py` 側は HTTP クライアントに差し替えるだけで済む。

### subprocess 呼び出しに `cwd` を指定していない理由

実装時に一度 `subprocess.run(..., cwd=REPO_ROOT)` を試したが、`--out-file` はサーバー側で `os.path.join(output_dir, ...)` により生成される相対パス(`PDF_OUTPUT_DIR = './generated_pdfs'`、呼び出し元プロセスの cwd 基準)であるため、`cwd=REPO_ROOT` を指定すると `nuts_calc.py`/`nuts_calc_tex.py` 側の `--out-file` 解決先が呼び出し元の cwd からずれて `FileNotFoundError` になる実バグを起こした。スクリプトパス自体は `RENDERER_SCRIPTS` で既に絶対パス解決済みのため `cwd` を変更する必要はなく、`subprocess.run` は cwd 未指定(呼び出し元プロセスの cwd を継承)のままにしている。

### コマンド構築ロジックを共用している理由

`nuts_calc.py` と `nuts_calc_tex.py` の共通CLI引数はレンダラー間で同じ変換処理を使い、スクリプトパスだけを切り替える。`carry_mode` を含むLaTeX専用パラメータも `build_command()` 自体はレンダラー名で抑止せず変換するため、呼び出し元は `GET /renderer-info` が `latex` のときだけ送る必要がある。Webプリセットは対象カードへ `latexOnly: true` を付けてこの契約を守る(`renderers.py:84-104,143-150`)。

## 統合ポイント

- 呼び出し元: `backend/app.py`(`POST /generate-pdf` ルートハンドラ。`GET /renderer-info` は `get_renderer_name()` のみを直接呼ぶ)。
- 呼び出し先: `nuts_calc.py` または `nuts_calc_tex.py`(`subprocess` 経由)。`latex` レンダラーは `nuts_calc_tex.py` 側で `pdflatex` の存在チェックを行う([[../../../../nuts_calc_tex.py]] 参照)。

## 注意事項・既知の制限

- `nuts_calc.py`/`nuts_calc_tex.py` 双方とも、バリデーション失敗メッセージを `print()`(stdout)で出力してから `exit(1)` する実装のため、`subprocess.CalledProcessError.stderr` は空文字になりうる。`app.py` 側は `e.stdout` を優先してエラーメッセージを組み立てる(issue #37 で修正、`docs/L3_implementation/backend/app.py.md` 参照)。なお `nuts_calc.py` の `com`/`99`/`squ`/`pi`/`100` バリデーションは同 issue 以前は引数なし `exit()`(終了コード0)を使っており、`check=True` の `subprocess.run` がそもそも `CalledProcessError` を送出しない不具合があった(`nuts_calc.py` 側で修正済み)。
- `get_renderer_name()` は呼び出しごとに env 変数を再読み込みする(プロセス起動時にキャッシュしない)。Flask アプリのライフサイクル中に env 変数が変わることは通常想定されないため実用上の影響はないが、テスト容易性(`monkeypatch.setenv`)を優先した設計。
- `--vertical`、`--use-parentheses`、`--missing-value`、`--terms`系、`--mixed-operators`、`--carry-borrow`/`--no-carry-borrow`/`--mixed-carry-borrow`、`--remainder`/`--no-remainder`/`--mixed-remainder`、`--require-reducible`/`--no-reducible`/`--mixed-reducible` は `nuts_calc.py` に存在しない。これらを持つリクエストはLaTeXレンダラーに限定する([[../../../../nuts_calc.py]] 参照)。

## 変更履歴(git log より自動生成)

- 32dd948 feat(#153): add reusable result ceiling for ope drills
- 392edbf feat(#93): add optional name field to nuts_calc_tex.py worksheets
- eae5107 #91 nuts_calc_tex.py: add remainder control to division (none/required/mixed) (#102)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
