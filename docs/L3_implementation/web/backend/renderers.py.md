# `web/backend/renderers.py`

## 目的・役割

`web/backend/app.py` の `POST /generate-pdf` エンドポイントが呼び出す「レンダラー選択・CLI コマンド構築・subprocess 実行」ロジックを、Flask に一切依存しない純粋関数として切り出したモジュール(issue #36)。`nuts_calc.py`(ReportLab)と `nuts_calc_tex.py`(LaTeX、[[../../../../nuts_calc_tex.py]] 参照)の2レンダラーを env 変数で切り替え可能にする。

## 動作の概要

- `RendererRequest` と `build_command()` は `frac` 用の `numerator_digits`/`denominator_digits` を値付きCLIオプションへ、`same_denominator`/`different_denominators`/`proper_operands`/`proper_result` を真偽フラグへ変換する。これらは `latex` レンダラーの `nuts_calc_tex.py` だけが解釈するため、呼び出し側がレンダラー情報に基づいて送信可否を制御する(`web/backend/renderers.py:8-38,83-126`)。

- `RENDERER_SCRIPTS`(`renderers.py:38-41`): レンダラー名(`'reportlab'`/`'latex'`)から呼び出すスクリプトの絶対パス(`REPO_ROOT / 'nuts_calc.py'` / `REPO_ROOT / 'nuts_calc_tex.py'`、`REPO_ROOT` は `Path(__file__)` から2階層上に解決)へのレジストリ。スクリプトパスを絶対パス化しているため、呼び出し元プロセスの cwd に依存せずスクリプトを解決できる。
- `get_renderer_name()`(`renderers.py:44-56`): env 変数 `NUTS_CALC_RENDERER` を読み、未設定なら `DEFAULT_RENDERER`(`'reportlab'`、既存動作を保つデフォルト)を返す。`RENDERER_SCRIPTS` に無い値が指定された場合は許可値一覧を含む `ValueError` を送出する。
- `build_command(renderer_name, params, out_file)`(`renderers.py:59-119`): リクエストの `params`(dict)を CLI 引数に変換する。`nuts_calc.py` と `nuts_calc_tex.py` は `paper_size`/`command`/`-a`/`-b`/`--rows`/`--descend` 等の CLI 引数体系がほぼ完全に一致しているため、このロジックはレンダラー間で共用しており、`RENDERER_SCRIPTS[renderer_name]` で選んだスクリプトパスのみが異なる。`paper_size`/`command_type` が欠けている場合は `ValueError` を送出する(旧 `app.py` のインライン実装と同じ挙動)。
- `run(params, output_dir, renderer_name=None)`(`renderers.py:122-141`): `renderer_name` 省略時は `get_renderer_name()` で解決し、UUID ファイル名を生成して `subprocess.run(..., check=True)` を実行、`(output_filepath, output_filename, completed_process)` を返す。呼び出し元(`app.py`)が `completed_process.stdout`/`.stderr` をログに使う。例外(`subprocess.CalledProcessError`/`FileNotFoundError`/`ValueError`)は呼び出し元に伝播させ、HTTP レスポンスへの変換は行わない(Flask 非依存の設計方針)。
- `RendererRequest`(`TypedDict`、`renderers.py:8-29`): リクエスト params の型ヒント。全キー任意(`total=False`)。`missing_value: bool`(issue #69)は `use_parentheses` と並ぶ latex 専用の真偽フラグとして追加されている。`terms: int`/`terms_min: int`/`terms_max: int`/`mixed_operators: bool`(issue #73、`nuts_calc_tex.py` 側は issue #71 で実装済み)も同様に latex 専用で、`build_command()` はそれぞれ `--terms`/`--terms-min`/`--terms-max`/`--mixed-operators` に変換する(`mixed_operators` は他の真偽フラグと同じく `params.get()` で真の場合のみ付与)。

## 重要な設計判断とその理由

### Flask に依存しない設計にした理由

issue #19 のトラッキング issue にある「将来 `nuts_calc.py`/`nuts_calc_tex.py` を同じ CLI 契約で切り替えられるラッパーを作る」という構想、および issue #36 の背景にある「将来的に専用 API として独立させたい(ただし `nuts_calc_tex.py` の PDF 品質チューニングが先)」という方針に基づき、`build_command`/`run` はいずれも Flask の `request`/`jsonify` に一切触れず、プレーンな `dict` を受け取る設計にしている。これにより、将来 API を独立サービス化する際は本ファイルをほぼそのまま移設でき、`app.py` 側は HTTP クライアントに差し替えるだけで済む。

### subprocess 呼び出しに `cwd` を指定していない理由

実装時に一度 `subprocess.run(..., cwd=REPO_ROOT)` を試したが、`--out-file` はサーバー側で `os.path.join(output_dir, ...)` により生成される相対パス(`PDF_OUTPUT_DIR = './generated_pdfs'`、呼び出し元プロセスの cwd 基準)であるため、`cwd=REPO_ROOT` を指定すると `nuts_calc.py`/`nuts_calc_tex.py` 側の `--out-file` 解決先が呼び出し元の cwd からずれて `FileNotFoundError` になる実バグを起こした。スクリプトパス自体は `RENDERER_SCRIPTS` で既に絶対パス解決済みのため `cwd` を変更する必要はなく、`subprocess.run` は cwd 未指定(呼び出し元プロセスの cwd を継承)のままにしている。

### コマンド構築ロジックを共用している理由

`nuts_calc.py`(`nuts_calc.py:97-` の `_init()`)と `nuts_calc_tex.py`(`nuts_calc_tex.py:80-266` の `_init()`)の CLI 引数体系(`paper_size`/`command`/`-a`/`-b`/`--a-min`/`--a-max`/`--b-min`/`--b-max`/`-o`/`--descend`/`--reverse`/`--shuffle`/`--intermediate`/`-r`/`-c`/`-ww`/`-p`/`-m`/`--csv`/`--out-file`/`--debug`)はほぼ一致するため、`build_command` はレンダラー間で分岐させず、スクリプトパスの選択のみをレンダラー固有の差分として扱っている。ただし `--vertical`(筆算/written-calculation 形式)、`--use-parentheses`(かっこ付き3項式、issue #67)、`--missing-value`(虫食い算、issue #69)、`--terms`/`--terms-min`/`--terms-max`/`--mixed-operators`(N項演算・演算子混合、issue #71・issue #73でWeb層に配線)は例外で、いずれも `nuts_calc_tex.py`(`latex`)専用のフラグである(`--vertical` は `nuts_calc.py` から削除済み、issue #46。それ以外は `nuts_calc_tex.py` にのみ実装されている)。`build_command` は `params["vertical"]`/`params["use_parentheses"]`/`params["missing_value"]`/`params["terms"]`/`params["terms_min"]`/`params["terms_max"]`/`params["mixed_operators"]` を両レンダラーに対して無条件に変換するため、呼び出し元(`app.py`)は `latex` が有効なとき(`GET /renderer-info` で判定)のみこれらを送るよう注意する必要がある — さもないと `nuts_calc.py` 側で `unrecognized arguments` となり `subprocess.CalledProcessError` が送出される。

## 統合ポイント

- 呼び出し元: `web/backend/app.py`(`POST /generate-pdf` ルートハンドラ。`GET /renderer-info` は `get_renderer_name()` のみを直接呼ぶ)。
- 呼び出し先: `nuts_calc.py` または `nuts_calc_tex.py`(`subprocess` 経由)。`latex` レンダラーは `nuts_calc_tex.py` 側で `pdflatex` の存在チェックを行う([[../../../../nuts_calc_tex.py]] 参照)。

## 注意事項・既知の制限

- `nuts_calc.py`/`nuts_calc_tex.py` 双方とも、バリデーション失敗メッセージを `print()`(stdout)で出力してから `exit(1)` する実装のため、`subprocess.CalledProcessError.stderr` は空文字になりうる。`app.py` 側は `e.stdout` を優先してエラーメッセージを組み立てる(issue #37 で修正、`docs/L3_implementation/web/backend/app.py.md` 参照)。なお `nuts_calc.py` の `com`/`99`/`squ`/`pi`/`100` バリデーションは同 issue 以前は引数なし `exit()`(終了コード0)を使っており、`check=True` の `subprocess.run` がそもそも `CalledProcessError` を送出しない不具合があった(`nuts_calc.py` 側で修正済み)。
- `get_renderer_name()` は呼び出しごとに env 変数を再読み込みする(プロセス起動時にキャッシュしない)。Flask アプリのライフサイクル中に env 変数が変わることは通常想定されないため実用上の影響はないが、テスト容易性(`monkeypatch.setenv`)を優先した設計。
- `--vertical` は `nuts_calc.py` から削除済み(issue #46)。`--use-parentheses`(issue #67)/`--missing-value`(issue #69)/`--terms`系・`--mixed-operators`(issue #71・issue #73)はそもそも `nuts_calc.py` に実装されていない。`nuts_calc.py`/`nuts_calc_tex.py` の CLI 引数体系はこの4点を除き一致する([[../../../../nuts_calc.py]] 参照)。

## 変更履歴(git log より自動生成)

- 7290008 feat(#73): add entrance-exam-prep drill section for grades 4-6
- 6c2ee20 feat(#69): add ope --missing-value option with grade menu cards
- 1b7e795 feat(#67): add ope --use-parentheses option with grade menu cards
- 7c89a52 feat(#65): add curriculum-aligned fraction worksheets
- 9ead364 refactor(#46): remove --vertical from nuts_calc.py; gate written-calculation UI on active renderer
- 8062b9f fix(#36): invoke the running interpreter (sys.executable) instead of hardcoded python3
- 155caf8 feat(#36): switch web/backend renderer between nuts_calc.py and nuts_calc_tex.py via env var
