# `backend/renderers.py`

## 目的・役割

`backend/app.py` の `POST /generate-pdf` エンドポイントが呼び出す「レンダラー選択・CLI コマンド構築・subprocess 実行」ロジックを、Flask に一切依存しない純粋関数として切り出したモジュール(issue #36)。レンダラーを env 変数(`NUTS_CALC_RENDERER`)で切り替え可能にする設計を保持しており、現在は `nuts_calc_tex.py`(LaTeX、[[../../../../nuts_calc_tex.py]] 参照)が唯一到達可能なレンダラー(`nuts_calc.py`/ReportLab は issue #232 で削除。将来別レンダラーを追加する場合は `RENDERER_SCRIPTS` にエントリを1つ加えるだけでよい)。

## 動作の概要

- `RendererRequest` と `build_command()` は `frac` 用の `numerator_digits`/`denominator_digits` を値付きCLIオプションへ、`same_denominator`/`different_denominators`/`proper_operands`/`proper_result` を真偽フラグへ変換する。これらは `latex` レンダラーの `nuts_calc_tex.py` だけが解釈するため、呼び出し側がレンダラー情報に基づいて送信可否を制御する(`backend/renderers.py:8-38,83-126`)。
- `RendererRequest.result_max` は Web リクエストの整数値を `--result-max <value>` へ変換する。これは `nuts_calc_tex.py` の `ope` 全式形式に共通する最終結果上限であり、LaTeX専用パラメーターとして呼び出し側が `latexOnly` 項目からのみ送る(`backend/renderers.py:9-54,130-144`)。

- `RENDERER_SCRIPTS`(`renderers.py:64-66`): レンダラー名から呼び出すスクリプトの絶対パス(`BACKEND_DIR / 'nuts_calc_tex.py'`、`BACKEND_DIR` は `Path(__file__).resolve().parent`)へのレジストリ。issue #232 以前は `'reportlab'`(`nuts_calc.py`)のエントリも持っていたが、同issueでの削除に伴い `'latex'` の1エントリのみになった。`nuts_calc_tex.py` は `renderers.py` と同じ `backend/` 直下にあるため、単純に `Path(__file__)` の親ディレクトリを基準に解決する(issue #88 のリポジトリ再編で `web/backend/renderers.py` から `backend/renderers.py` へ移動した際、旧 `REPO_ROOT = BACKEND_DIR.parent.parent`(2階層上、当時は `web/backend/` の2階層上がリポジトリルートだった)から変更)。スクリプトパスを絶対パス化しているため、呼び出し元プロセスの cwd に依存せずスクリプトを解決できる。
- `get_renderer_name()`(`renderers.py:87-104`): env 変数 `NUTS_CALC_RENDERER` を読み、未設定なら `DEFAULT_RENDERER`(`'latex'`、issue #186 で `'reportlab'` から変更)を返す。`RENDERER_SCRIPTS` に無い値が指定された場合は許可値一覧を含む `ValueError` を送出する。issue #232 以前は `UNAVAILABLE_RENDERERS`(`{'reportlab'}`)という専用の特別扱いで「現在利用不可」という個別メッセージを出していたが、`nuts_calc.py` 削除に伴い `RENDERER_SCRIPTS` から `'reportlab'` エントリ自体を除いたため、この特別扱いは不要になった(下記「`UNAVAILABLE_RENDERERS` を廃止した理由」参照) — 明示的な `reportlab` 指定も他の未知の値と同じ汎用エラーで拒否される。
- `build_command(renderer_name, params, out_file)`(`renderers.py:107-...`): リクエストの `params`(dict)を CLI 引数に変換する。レンダラー名に依存しないロジックで、`RENDERER_SCRIPTS[renderer_name]` で選んだスクリプトパスのみが異なる(将来2つ目のレンダラーが追加されても、そのスクリプトが同じ CLI 引数体系を持つ限りこのロジックは変更不要)。`paper_size`/`command_type` が欠けている場合は `ValueError` を送出する(旧 `app.py` のインライン実装と同じ挙動)。
- `run(params, output_dir, renderer_name=None)`(`renderers.py:234-`): `renderer_name` 省略時は `get_renderer_name()` で解決し、UUID ファイル名を生成して `subprocess.run(..., check=True)` を実行、`(output_filepath, output_filename, completed_process)` を返す。呼び出し元(`app.py`)が `completed_process.stdout`/`.stderr` をログに使う。例外(`subprocess.CalledProcessError`/`FileNotFoundError`/`ValueError`)は呼び出し元に伝播させ、HTTP レスポンスへの変換は行わない(Flask 非依存の設計方針)。
- `RendererRequest`(`TypedDict`、`renderers.py:9-56`)は `num: int` フィールドを持つ(issue #138)。これは `backend/problem_generation.py`([[problem_generation.py]] 参照)専用のフィールドで、`build_command`/`run` は参照しない(`POST /generate-problems` が生成する問題数を指定するために使う)。
- `RendererRequest`: リクエスト params の型ヒント。全キー任意(`total=False`)。`carry_mode` は `Literal['required','none','mixed']` で、`CARRY_MODE_FLAGS` が順に `--carry-borrow`/`--no-carry-borrow`/`--mixed-carry-borrow` へ変換する。未知値は無視せず `ValueError` にする。`missing_value: bool` や `terms` 系も同様に保持する。`remainder_mode`(`Literal['required','none','mixed']`、issue #91)は `carry_mode` と全く同じパターンで、`REMAINDER_MODE_FLAGS` が `--remainder`/`--no-remainder`/`--mixed-remainder` へ変換し、未知値は同様に `ValueError` にする。`reducible_mode`(`Literal['required','none','mixed']`、issue #114)も同じパターンで、`REDUCIBLE_MODE_FLAGS` が `--require-reducible`/`--no-reducible`/`--mixed-reducible` へ変換する(`frac`/`mixed` の乗除算専用、[[../../../../nuts_calc_tex.py]] 参照)。`with_name_field: bool`(issue #93)は `with_bottom_answer` と同じ単純な真偽フラグパターンで、真の場合のみ `--with-name-field` を追加する。

## 重要な設計判断とその理由

### Flask に依存しない設計にした理由

issue #19 のトラッキング issue にある「将来 `nuts_calc.py`/`nuts_calc_tex.py` を同じ CLI 契約で切り替えられるラッパーを作る」という構想(`nuts_calc.py` は issue #232 で削除済みだが、複数レンダラーを同じ契約で切り替える設計思想自体は維持している)、および issue #36 の背景にある「将来的に専用 API として独立させたい(ただし `nuts_calc_tex.py` の PDF 品質チューニングが先)」という方針に基づき、`build_command`/`run` はいずれも Flask の `request`/`jsonify` に一切触れず、プレーンな `dict` を受け取る設計にしている。これにより、将来 API を独立サービス化する際は本ファイルをほぼそのまま移設でき、`app.py` 側は HTTP クライアントに差し替えるだけで済む。

### subprocess 呼び出しに `cwd` を指定していない理由

実装時に一度 `subprocess.run(..., cwd=REPO_ROOT)` を試したが、`--out-file` はサーバー側で `os.path.join(output_dir, ...)` により生成される相対パス(`PDF_OUTPUT_DIR = './generated_pdfs'`、呼び出し元プロセスの cwd 基準)であるため、`cwd=REPO_ROOT` を指定すると `nuts_calc_tex.py` 側の `--out-file` 解決先が呼び出し元の cwd からずれて `FileNotFoundError` になる実バグを起こした。スクリプトパス自体は `RENDERER_SCRIPTS` で既に絶対パス解決済みのため `cwd` を変更する必要はなく、`subprocess.run` は cwd 未指定(呼び出し元プロセスの cwd を継承)のままにしている。

### コマンド構築ロジックをレンダラー非依存にしている理由

`build_command()` は `renderer_name` に応じてスクリプトパス(`RENDERER_SCRIPTS[renderer_name]`)を選ぶだけで、CLI 引数への変換ロジック自体はレンダラーを問わず共通処理を通す。issue #232 以前はこれが「`nuts_calc.py`/`nuts_calc_tex.py` 2レンダラー間の共用」を指していたが、`nuts_calc.py` 削除後もこの非依存設計は維持している(将来レンダラーが追加された場合に備える設計判断、2026-08-20 決定)。`carry_mode` を含む LaTeX 専用パラメータも `build_command()` 自体はレンダラー名で抑止せず変換するため、呼び出し元は `GET /renderer-info` が `latex` のときだけ送る必要がある。Webプリセットは対象カードへ `latexOnly: true` を付けてこの契約を守る。

### `UNAVAILABLE_RENDERERS` を廃止した理由(issue #232)

issue #186 時点では `nuts_calc.py`(`reportlab`)のコード自体は残したまま、`get_renderer_name()` に `UNAVAILABLE_RENDERERS = {'reportlab'}` という専用の特別扱いを追加し、「現在利用不可」という個別メッセージで明示的な `reportlab` 指定を拒否していた(`RENDERER_SCRIPTS` にはまだ `'reportlab'` エントリが残っていたため、専用チェックがなければ通常どおり選択できてしまう状態だった)。issue #232 で `nuts_calc.py` のコード自体を削除するにあたり、`RENDERER_SCRIPTS` から `'reportlab'` エントリも併せて削除したため、`get_renderer_name()` の「`RENDERER_SCRIPTS` に無い値は許可値一覧付きの `ValueError`」という既存の汎用チェックだけで同じ「利用不可」の結果を得られるようになり、`UNAVAILABLE_RENDERERS` という専用の特別扱いは不要になった。これにより、将来また別のレンダラーを一時的に無効化したくなった場合も、そのレンダラーを `RENDERER_SCRIPTS` から一時的に外すだけで済む(専用の除外リストを別途メンテナンスする必要がない)。

## 統合ポイント

- 呼び出し元: `backend/app.py`(`POST /generate-pdf` ルートハンドラ。`GET /renderer-info` は `get_renderer_name()` のみを直接呼ぶ)。`backend/factory.sh` は本ファイルを経由せず `nuts_calc_tex.py` を直接 subprocess 実行する(issue #232 でバッチ生成の呼び出し先を `nuts_calc.py` から切替、[[../../factory.sh]] 参照)。
- 呼び出し先: `nuts_calc_tex.py`(`subprocess` 経由)。`pdflatex`/`lualatex` の存在チェックは `nuts_calc_tex.py` 側で行う([[../../../../nuts_calc_tex.py]] 参照)。

## 注意事項・既知の制限

- `nuts_calc_tex.py` は、バリデーション失敗メッセージを `print()`(stdout)で出力してから `exit(1)` する実装のため、`subprocess.CalledProcessError.stderr` は空文字になりうる。`app.py` 側は `e.stdout` を優先してエラーメッセージを組み立てる(issue #37 で修正、`docs/L3_implementation/backend/app.py.md` 参照)。
- `get_renderer_name()` は呼び出しごとに env 変数を再読み込みする(プロセス起動時にキャッシュしない)。Flask アプリのライフサイクル中に env 変数が変わることは通常想定されないため実用上の影響はないが、テスト容易性(`monkeypatch.setenv`)を優先した設計。
- `nuts_calc.py`(ReportLab)は issue #232 で削除された。`RENDERER_SCRIPTS` は現在 `'latex'` の1エントリのみを持つが、`get_renderer_name()`/`build_command()`/`run()` はいずれもレンダラー名をハードコードしておらず、将来2つ目のレンダラーが追加された場合は `RENDERER_SCRIPTS` にエントリを1つ加えるだけで動作する設計を維持している(2026-08-20 決定)。

## 変更履歴(git log より自動生成)

- 506d7b4 feat(#186): make latex+lualatex the default reachable configuration
- 13bef63 #138 backend: add POST /generate-problems for PDF-free ope problem generation (#175)
- 7b064ef #114 nuts_calc_tex.py: add reducibility control to frac/mixed multiplication and division (#165)
- 1a32b29 #153 Add reusable result ceilings and grade-2 addition up to 1,000 (#158)
- 26ec449 #93 nuts_calc_tex.py: add optional name field to generated worksheets (#105)
- eae5107 #91 nuts_calc_tex.py: add remainder control to division (none/required/mixed) (#102)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
