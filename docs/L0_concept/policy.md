# Policy

## 技術選定ポリシー

- PDF 生成には ReportLab を採用している(根拠: `nuts_calc.py` の import 群、`README.md:105-110`)。
- Web UI は React 19 + Vite 7 + Tailwind CSS(フロントエンド、`web/frontend/package.json:12-29`)と Flask + Flask-Cors(バックエンド、`web/backend/app.py:1-2`)という構成。バックエンドは独自のドリル生成ロジックを持たず、既存の CLI(`nuts_calc.py`)を `subprocess.run` で呼び出すラッパーに徹している(根拠: `web/backend/app.py:20-63`)。これは CLI とロジックを二重実装しない設計判断と考えられる(未確認: 明示的な設計意図の記述はコード内にないが、実装から読み取れる一貫した方針)。
- Python 側は依存関係の固定(lock file, `requirements.txt`, `pyproject.toml` など)を行っていない。以前存在した `setup.py` はコミット `d9fc0a3`("Rename 100masu.py to nuts_calc.py and remove setup.py")で削除されており、`pip install` によるパッケージインストールの導線は現状ない。README.md の Setup セクション(`README.md:13-14`)は「pip 経由でインストールでき、reportlab の依存関係も処理される」と書いてあるが、これを裏付けるパッケージ定義ファイルは存在しない(README と実装の乖離。[[consistency_checks]] 参照)。
- npm 側は `web/frontend/package-lock.json` でバージョン固定されている。`package.json` の `dependencies` には `i18next`/`react-i18next`/`i18next-browser-languagedetector`/`i18next-http-backend` が含まれており、`npm install && npm run build` が成功することを実機で再確認済み(2026-08-05)。過去(2026-07-22 時点)はこれらのパッケージが欠落しビルドが失敗していたが、その後のコミットで解消されている(詳細は [[specification_summary]])。
- `nuts_calc_tex.py`(実験的プロトタイプ)は LaTeX(`pdflatex`)エンジンに依存する。CTAN の `longdivision` パッケージは Ubuntu の `texlive-latex-extra` に同梱されていないため `vendor/texmf/tex/latex/longdivision/` としてリポジトリに vendoring している(LPPLライセンス)。`xlop` は同パッケージに同梱されているため vendoring していない(詳細は [[../L3_implementation/nuts_calc_tex.py]])。

## セキュリティ方針

- CLI 単体の利用では外部入力は CLI 引数のみで、ネットワーク待受はない。
- Web UI 経路では Flask バックエンドが `CORS(app)` を制限なしで有効化しており(`web/backend/app.py:8`)、オリジン制限が存在しない。ローカル開発(`http://127.0.0.1:5000` ⇄ `http://localhost:5173`)を想定した設定と考えられるが、そのまま公開環境にデプロイした場合は任意のオリジンからの PDF 生成リクエストを許可してしまう(根拠: `CORS(app)` はオプション引数なしのグローバル許可)。
- Flask バックエンドは受け取ったフォーム値をそのまま `subprocess.run` の引数リストに連結して `nuts_calc.py` を起動している(`web/backend/app.py:20-59`)。`shell=True` は使っておらず引数はリストで渡されているため、シェルインジェクションの経路は確認できないが、`data.get(...)` の値をそのまま整数変換や文字列結合しているだけで、`paper_size`/`command_type` の値を許可リストで検証していない(`web/backend/app.py:25-32`)。`nuts_calc.py` 側の `argparse` の `choices` で最終的に弾かれるため実害は限定的と考えられるが、バックエンド単体では入力検証をしていない点は留意事項として記録する(未確認: 実際に不正な値を送って `argparse` のエラーがどう返るかは未検証)。
- 生成された PDF は `web/backend/generated_pdfs/` に UUID 付きファイル名で保存され続ける(`web/backend/app.py:11-12,56-58`)。このディレクトリの自動クリーンアップ処理は見当たらず、リクエストのたびにディスクへ蓄積される(未確認: 運用上のクリーンアップ手順があるかは記述なし)。また `.gitignore` にこのディレクトリ用のエントリがなく、誤ってコミットされるリスクがある。

## パフォーマンス要件

- 明示的なパフォーマンス要件の記述はリポジトリ内に存在しない(未確認)。

## 禁止事項・既知の制約

- **(解消済み)** 旧 `100masu.py:158` の `ini.intermediate` 未定義変数バグ(`ope` 以外の全コマンドが `NameError` で失敗する不具合)は、`dev` ブランチのマージ(`nuts_calc.py`)で `args.intermediate` に修正されており、CLI の7コマンドすべてが実機で正常終了することを確認済み。
- **(解消済み)** `web/frontend` の `npm install && npm run build` が `i18next` 系パッケージの欠落で失敗していた既知の欠陥は解消済み(2026-08-05 実機再確認)。詳細は [[specification_summary]]。
- **(既知・未修正)** `tests/test_nuts_calc_init.py` に9件の失敗するテストがある。`nuts_calc.py` のバリデーション分岐が `exit()` から `exit(1)` に修正された(issue #37)後、テスト側の期待値が更新されないまま残っている stale なテスト。実装のバグではない(テストファイル自身の docstring、`docs/L3_implementation/nuts_calc.py.md:55`、[[../L2_development/test]] 参照)。
- README.md(`README.md:18`)が「パッケージ定義ファイルが存在しない」旨を既に明記しており、この点についての README と実装の乖離は解消済み。実際には `pip install reportlab flask flask-cors` のような個別インストールが必要な点は変わらない。

## AI が変更判断前に確認すべきこと

- `web/frontend` は現在ビルド可能な状態(`npm install && npm run build` 成功、2026-08-05 確認)。変更を加えた際は `npm run build` で再確認すること。
- `nuts_calc.py` の `_init()` バリデーション周りを変更する際は、`tests/test_nuts_calc_init.py` の9件の失敗テストが「意図的に stale なままにしている既知の状態」であることを踏まえ、無関係な差分でこれらのテスト数が変動していないか確認すること([[../L2_development/test]] 参照)。
- `web/backend/app.py` を触る際は、`CORS(app)` がオリジン無制限である点、および入力値の許可リスト検証がない点を認識した上で変更すること。
