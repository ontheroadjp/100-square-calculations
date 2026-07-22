# Policy

## 技術選定ポリシー

- PDF 生成には ReportLab を採用している(根拠: `nuts_calc.py` の import 群、`README.md:105-110`)。
- Web UI は React 19 + Vite 7 + Tailwind CSS(フロントエンド、`web/frontend/package.json:12-29`)と Flask + Flask-Cors(バックエンド、`web/backend/app.py:1-2`)という構成。バックエンドは独自のドリル生成ロジックを持たず、既存の CLI(`nuts_calc.py`)を `subprocess.run` で呼び出すラッパーに徹している(根拠: `web/backend/app.py:20-63`)。これは CLI とロジックを二重実装しない設計判断と考えられる(未確認: 明示的な設計意図の記述はコード内にないが、実装から読み取れる一貫した方針)。
- Python 側は依存関係の固定(lock file, `requirements.txt`, `pyproject.toml` など)を行っていない。以前存在した `setup.py` はコミット `d9fc0a3`("Rename 100masu.py to nuts_calc.py and remove setup.py")で削除されており、`pip install` によるパッケージインストールの導線は現状ない。README.md の Setup セクション(`README.md:13-14`)は「pip 経由でインストールでき、reportlab の依存関係も処理される」と書いてあるが、これを裏付けるパッケージ定義ファイルは存在しない(README と実装の乖離。[[consistency_checks]] 参照)。
- npm 側は `web/frontend/package-lock.json` でバージョン固定されているが、`package.json` の `dependencies` に実際に import されている `i18next` 系パッケージが欠落しており、`npm install` 後の `npm run build`/`npm run dev` が失敗する(実機確認済み、詳細は [[specification_summary]])。

## セキュリティ方針

- CLI 単体の利用では外部入力は CLI 引数のみで、ネットワーク待受はない。
- Web UI 経路では Flask バックエンドが `CORS(app)` を制限なしで有効化しており(`web/backend/app.py:8`)、オリジン制限が存在しない。ローカル開発(`http://127.0.0.1:5000` ⇄ `http://localhost:5173`)を想定した設定と考えられるが、そのまま公開環境にデプロイした場合は任意のオリジンからの PDF 生成リクエストを許可してしまう(根拠: `CORS(app)` はオプション引数なしのグローバル許可)。
- Flask バックエンドは受け取ったフォーム値をそのまま `subprocess.run` の引数リストに連結して `nuts_calc.py` を起動している(`web/backend/app.py:20-59`)。`shell=True` は使っておらず引数はリストで渡されているため、シェルインジェクションの経路は確認できないが、`data.get(...)` の値をそのまま整数変換や文字列結合しているだけで、`paper_size`/`command_type` の値を許可リストで検証していない(`web/backend/app.py:25-32`)。`nuts_calc.py` 側の `argparse` の `choices` で最終的に弾かれるため実害は限定的と考えられるが、バックエンド単体では入力検証をしていない点は留意事項として記録する(未確認: 実際に不正な値を送って `argparse` のエラーがどう返るかは未検証)。
- 生成された PDF は `web/backend/generated_pdfs/` に UUID 付きファイル名で保存され続ける(`web/backend/app.py:11-12,56-58`)。このディレクトリの自動クリーンアップ処理は見当たらず、リクエストのたびにディスクへ蓄積される(未確認: 運用上のクリーンアップ手順があるかは記述なし)。また `.gitignore` にこのディレクトリ用のエントリがなく、誤ってコミットされるリスクがある。

## パフォーマンス要件

- 明示的なパフォーマンス要件の記述はリポジトリ内に存在しない(未確認)。

## 禁止事項・既知の制約

- **(解消済み)** 旧 `100masu.py:158` の `ini.intermediate` 未定義変数バグ(`ope` 以外の全コマンドが `NameError` で失敗する不具合)は、`dev` ブランチのマージ(`nuts_calc.py`)で `args.intermediate` に修正されており、CLI の7コマンドすべてが実機で正常終了することを確認済み。
- **(新規・実機確認済み)** `web/frontend` は `npm install && npm run build` を実行すると `i18next` の解決失敗でビルドに失敗する。`package.json` の依存関係が `src/i18n.js`/`src/App.jsx` の実際の import と一致していないため。詳細と再現手順は [[specification_summary]]。
- README.md(`README.md:13-14`)が pip 経由のインストールに言及しているが、パッケージ定義ファイル(`setup.py`/`pyproject.toml`)は存在しない。実際には `pip install reportlab flask flask-cors` のような個別インストールが必要。

## AI が変更判断前に確認すべきこと

- `web/frontend` に手を入れる際は、まず `package.json` に `i18next`/`react-i18next`/`i18next-browser-languagedetector`/`i18next-http-backend` を追加してビルドが通る状態にする必要がある(既知の未修正課題)。
- `web/backend/app.py` を触る際は、`CORS(app)` がオリジン無制限である点、および入力値の許可リスト検証がない点を認識した上で変更すること。
