# Repository Structure

単一リポジトリだが、`web/` 以下は `backend`/`frontend` に分かれたミニ・モノレポ構成(それぞれ独立した実行環境: Python venv / npm)。ディレクトリ一覧で確認済み。

```
100-square-calculations/
├── nuts_calc.py         # PDF生成CLI本体(実行可能。旧 100masu.py)
├── nuts_calc_tex.py     # LaTeX(pdflatex)レンダリングの実験的プロトタイプCLI(実行可能。nuts_calc.pyとコード共有なし)
├── factory.sh           # バッチ生成シェルスクリプト(実行可能)
├── memo.md              # 暗算指導法の解説(教育コンテンツ、非コード)
├── LICENSE              # MIT License
├── README.md            # 利用者向け説明(英語)
├── README_ja.md         # 利用者向け説明(日本語、README.md の対訳。Architecture/Design Principles セクションは README.md にのみ存在し未追随、下記「未確認事項」参照)
├── pytest.ini           # pytest 設定(testpaths=tests, pythonpath=.)
├── .gitignore
├── tests/               # pytestテストスイート(14ファイル)。nuts_calc.py/nuts_calc_tex.py/web/backendを対象
├── vendor/
│   └── texmf/tex/latex/longdivision/  # CTAN 'longdivision' パッケージのvendoring(nuts_calc_tex.pyの--vertical divで使用)
├── web/
│   ├── backend/
│   │   ├── app.py         # Flask API(POST /generate-pdf, GET /renderer-info)
│   │   └── renderers.py   # レンダラー選択・CLIコマンド構築・subprocess実行(Flask非依存、issue #36)
│   └── frontend/        # React + Vite + Tailwind の SPA
│       ├── src/
│       │   ├── main.jsx           # エントリポイント
│       │   ├── App.jsx            # ヘッダー(タイトル・言語切替)+ GradeDrills を描画するシェル
│       │   ├── GradeDrills.jsx    # 学年別(1-6+無学年+カスタム)ドリルPDF選択画面(メインUI)
│       │   ├── CustomGenerator.jsx # 詳細パラメータ指定フォーム(「カスタム」選択時)
│       │   ├── drillPresets.js    # 学年→/generate-pdf パラメータのプリセット定義
│       │   ├── App.css
│       │   └── i18n.js            # react-i18next 設定
│       ├── public/locales/{en,ja}/translation.json  # 翻訳文言
│       ├── package.json         # i18next系4パッケージを含む(下記「既知の欠陥」参照、解消済み)
│       └── package-lock.json
└── docs/                 # /init-docs で生成した設計ドキュメント
```

`example_result.pdf` は `dev` ブランチのマージで削除されている(`.gitignore` には依然 `!example_result.pdf` という除外例外が残っているが、対象ファイルが存在しないため実質無効。[[../L2_development/consistency_checks]] 参照)。

## 各ファイル/ディレクトリの責務(実装から確認)

- `nuts_calc.py`: CLI エントリポイント兼ロジック全体。ファイル冒頭のヘッダーコメント(`nuts_calc.py:4-13`)は "Script: 100masu.py" のままリネーム前の名称を残しており、実際のファイル名(`nuts_calc.py`)と食い違っている(ドキュメンテーションの取り残し、実害はない)。内部構成(引数パース、7種のデータ生成関数、ReportLab レイアウト構築、`main()`)は旧 `100masu.py` から機能的に踏襲。
- `factory.sh`: `_basic`/`_kuku`系関数で用紙サイズ・分量違いの複数パターンを `dist/` 以下に一括生成。呼び出し方法が `100masu.py ...`(裸のコマンド名)から `python nuts_calc.py ...` に変更され(`factory.sh:127` 等)、`nuts_calc.py` がリポジトリルートにあり `python`(`python3` ではない)が `PATH` 上にあることを前提にしている。
- `memo.md`: コードではなく、暗算指導法・学習ステップ・受験算数における計算力の重要性を説明する日本語の教育コンテンツ。`dev` ブランチのマージで一度削除されたが、ユーザーの指示によりマージ後に `main` の内容から復元済み(2026-07-22)。
- `LICENSE`: MIT License(`LICENSE:1-21`、Copyright (c) 2025 ontheroadjp)。`dev` ブランチのマージで新規追加。
- `README.md` / `README_ja.md`: 英語/日本語で内容が対応した利用者向け説明。CLI・`factory.sh`・Web UI(バックエンド/フロントエンド起動手順)をカバーしている。
- `web/backend/app.py`: Flask アプリ。`/generate-pdf` の単一エンドポイントで `nuts_calc.py` を `subprocess` 実行するラッパー(詳細は [[../L1_project/project_overview]])。
- `web/frontend/`: Vite ベースの React SPA。`node_modules/` と `dist/` は `.gitignore` で除外済み(`.gitignore:53-54`)。トップ画面は学年別ドリル選択(`GradeDrills.jsx`)で、そこから「カスタム」を選ぶと詳細パラメータ指定フォーム(`CustomGenerator.jsx`)に切り替わる。

## 未確認事項

- `docs/` 以外に、リポジトリ外で管理されているドキュメント(Notion、Google Docs等)があるかどうかは本リポジトリから確認できない。
- `web/backend/generated_pdfs/`(実行時に自動作成されるディレクトリ、`web/backend/app.py:11-12`)が `.gitignore` の対象になっていない点は [[../L0_concept/policy]] に記録済み。
