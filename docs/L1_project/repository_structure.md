# Repository Structure

単一リポジトリだが、CLI/バックエンド関連は `backend/` に、フロントエンドは `frontend/` 配下の `spa`/`web` 2実装に、それぞれ分かれたミニ・モノレポ構成(それぞれ独立した実行環境: Python venv / npm)。issue #88 で `web/backend`・`web/frontend`・リポジトリルート直下の CLI/テストを再編し、`backend`/`frontend/{spa,web}` レイアウトに変更した(将来 `backend`/`frontend` を別リポジトリへ分離する可能性を見据えた構成、[[../L0_concept/policy]] 未記載・issue #88 の背景)。ディレクトリ一覧で確認済み。

```
100-square-calculations/
├── memo.md              # 暗算指導法の解説(教育コンテンツ、非コード)
├── LICENSE              # MIT License
├── README.md            # 利用者向け説明(英語)
├── README_ja.md         # 利用者向け説明(日本語、README.md の対訳。下記「未確認事項」参照)
├── .gitignore
├── backend/              # CLI・Flask API・テストを集約した自己完結ツリー(issue #88)
│   ├── nuts_calc.py        # PDF生成CLI本体(実行可能。旧 100masu.py)
│   ├── nuts_calc_tex.py    # LaTeX(pdflatex)レンダリングの実験的プロトタイプCLI(実行可能。nuts_calc.pyとコード共有なし)
│   ├── factory.sh          # バッチ生成シェルスクリプト(実行可能)
│   ├── app.py              # Flask API(POST /generate-pdf, GET /renderer-info)
│   ├── renderers.py        # レンダラー選択・CLIコマンド構築・subprocess実行(Flask非依存、issue #36)
│   ├── pytest.ini          # pytest 設定(testpaths=tests, pythonpath=.)
│   ├── tests/               # pytestテストスイート(18個のtest_*.py)。nuts_calc.py/nuts_calc_tex.py/app.py/renderers.pyを対象
│   └── vendor/
│       └── texmf/tex/latex/longdivision/  # CTAN 'longdivision' パッケージのvendoring(nuts_calc_tex.pyの--vertical divで使用)
├── frontend/
│   ├── spa/              # React + Vite + Tailwind の SPA(旧 web/frontend、issue #88 で無変更のまま移動)
│   │   ├── src/
│   │   │   ├── main.jsx           # エントリポイント
│   │   │   ├── App.jsx            # ヘッダー(タイトル・言語切替)+ GradeDrills を描画するシェル
│   │   │   ├── GradeDrills.jsx    # 学年別(1-6+無学年+カスタム)ドリルPDF選択画面(メインUI)
│   │   │   ├── CustomGenerator.jsx # 詳細パラメータ指定フォーム(「カスタム」選択時)
│   │   │   ├── drillPresets.js    # 学年→/generate-pdf パラメータのプリセット定義(1年生条件付き加減算・中学受験準備等)
│   │   │   ├── drillCatalog.js    # プリセットから検索・絞り込み可能なカタログを構築する純粋関数群
│   │   │   ├── drillPresets.test.js / drillCatalog.test.js # node:test によるプリセット/カタログ構造テスト
│   │   │   ├── verticalLayout.js / verticalLayout.test.js # 筆算行数の純粋関数と node:test
│   │   │   ├── App.css
│   │   │   └── i18n.js            # react-i18next 設定
│   │   ├── public/locales/{en,ja}/translation.json  # 翻訳文言
│   │   ├── package.json         # i18next系4パッケージを含む
│   │   └── package-lock.json
│   └── web/               # HTML/CSS(Sass)/JS のみの軽量実装(新規、issue #88)。日本語のみ、i18nライブラリ不要
│       ├── index.html / catalog.html / preset.html / custom.html  # 画面ごとに実在するページ(SPAではない複数ページ構成、ユーザー要望)
│       ├── vite.config.js       # Vite マルチページビルド設定(4 HTML エントリ)
│       ├── src/
│       │   ├── home.js / catalog.js / preset.js / custom.js  # 各ページのエントリスクリプト
│       │   ├── drillPresets.js / drillCatalog.js / verticalLayout.js  # frontend/spa から複製した純粋データ/ロジック(React/i18n非依存のため無変更で再利用)
│       │   ├── presetDetail.js / customGenerator.js  # マウント可能な独立ウィジェット(それぞれ preset.js / custom.js から呼ばれる)
│       │   ├── strings.js / strings.ja.json  # i18next の代わりの静的日本語文字列テーブル(ja/translation.json を複製)
│       │   └── styles/main.scss (+ _base/_components/_layout.scss)  # frontend/spa の App.css を移植した Sass
│       └── package.json         # devDependencies は vite と sass のみ(React・i18next系は含まない)
└── docs/                 # 設計ドキュメントと教材仕様の一次資料(reference/)
```

`example_result.pdf` は `dev` ブランチのマージで削除されている(`.gitignore` には依然 `!example_result.pdf` という除外例外が残っているが、対象ファイルが存在しないため実質無効。[[../L2_development/consistency_checks]] 参照)。

## 各ファイル/ディレクトリの責務(実装から確認)

- `backend/nuts_calc.py`: CLI エントリポイント兼ロジック全体。ファイル冒頭のヘッダーコメント(`nuts_calc.py:4-13`)は "Script: 100masu.py" のままリネーム前の名称を残しており、実際のファイル名(`nuts_calc.py`)と食い違っている(ドキュメンテーションの取り残し、実害はない)。内部構成(引数パース、7種のデータ生成関数、ReportLab レイアウト構築、`main()`)は旧 `100masu.py` から機能的に踏襲。
- `backend/nuts_calc_tex.py`: 7つの互換コマンドとLaTeX専用 `frac`/`mixed`/`compare` の計10コマンドをレンダリングする独立プロトタイプ。`compare` は同分母・同分子・異分母の分数比較を扱い、`ope` は小数と繰り上がり・繰り下がり条件付き加減算にも対応する。`vendor/texmf` の参照は `__file__` からの自己相対解決のため、issue #88 の移動後も無修正で動作する。
- `backend/factory.sh`: `_basic`/`_kuku`系関数で用紙サイズ・分量違いの複数パターンを `dist/` 以下に一括生成。`python nuts_calc.py ...`(`backend/` 内の相対呼び出し)を内部で使うため、`backend/` ディレクトリ内での実行を前提にしている(`python`(`python3` ではない)が `PATH` 上にあることも前提)。`nuts_calc_tex.py` は呼び出さない。
- `memo.md`: コードではなく、暗算指導法・学習ステップ・受験算数における計算力の重要性を説明する日本語の教育コンテンツ。
- `LICENSE`: MIT License(`LICENSE:1-21`、Copyright (c) 2025 ontheroadjp)。
- `README.md` / `README_ja.md`: 英語/日本語で内容が対応した利用者向け説明。CLI・`factory.sh`・Web UI(バックエンド/フロントエンド起動手順)をカバーしている。README.md には `Architecture`/`Design Principles` セクションがあるが README_ja.md には対応するセクションがなく、両者は完全な対訳ではなくなっている(下記「未確認事項」参照)。
- `backend/tests/`: pytestテストスイート(18個の `test_*.py`)。分数・小数・整数/小数/分数混合、繰り上がり条件付き加減算、4〜6年生の中学受験プリセットを検証する。`frontend/spa` には別途 `node:test` 形式の3ファイルがある(`frontend/spa/src/*.test.js`)。`frontend/web` には自動テストがない(未確認事項参照)。詳細は [[../L2_development/test]]。
- `docs/reference/`: 教材仕様の根拠となる一次資料を出典・取得日・SHA-256と共に保存する(`docs/reference/README.md:1-24`)。
- `backend/vendor/texmf/tex/latex/longdivision/`: CTAN の `longdivision` パッケージ(LPPLライセンス)を vendoring したもの。Ubuntu の `texlive-latex-extra` に同梱されていないため、`nuts_calc_tex.py` が `TEXINPUTS` 経由でこのパスを解決する([[../L3_implementation/nuts_calc_tex.py]] 参照)。
- `backend/app.py`: Flask アプリ。`POST /generate-pdf`(PDF生成)と `GET /renderer-info`(有効レンダラー名の取得)の2エンドポイント。コマンド構築・レンダラー選択・subprocess実行は `backend/renderers.py` に切り出されている(詳細は [[../L1_project/project_overview]])。`frontend/spa` と `frontend/web` の両方から共通利用される。
- `backend/renderers.py`: `NUTS_CALC_RENDERER` env 変数(`reportlab`|`latex`)で `nuts_calc.py`/`nuts_calc_tex.py` を切り替えて呼び出す、Flask 非依存の純粋関数群(issue #36)。`RENDERER_SCRIPTS` はスクリプトパスを `Path(__file__).resolve().parent`(=`backend/`)基準で解決する(issue #88 で `web/backend/` からの移動に伴い repo-root 基準から変更)。
- `frontend/spa/`: Vite ベースの React SPA。`node_modules/` と `dist/` は `.gitignore` で除外済み。トップ画面は学年別ドリル選択(`GradeDrills.jsx`)で、LaTeX 時の4〜6年生には中学受験準備セクションも表示する。そこから「カスタム」を選ぶと詳細パラメータ指定フォーム(`CustomGenerator.jsx`)に切り替わる。
- `frontend/web/`: HTML/CSS(Sass)/JS のみの軽量フロントエンド(新規、issue #88)。`frontend/spa` と機能的に同等だが、React・i18n ライブラリを使わず日本語のみに対応する。ユーザーの明示的な指示により、SPA(単一 `index.html` を JS ルーターで画面切替する構成)ではなく、画面ごとに実在の `.html` を持つ複数ページ構成として実装されている(通常の `<a href>` リンクと GET フォームで画面遷移する)。

## 未確認事項

- `docs/` 以外に、リポジトリ外で管理されているドキュメント(Notion、Google Docs等)があるかどうかは本リポジトリから確認できない。
- `backend/generated_pdfs/`(実行時に自動作成されるディレクトリ、`backend/app.py:11-12`)が `.gitignore` の対象になっていない点は [[../L0_concept/policy]] に記録済み。
- README.md には存在する `Architecture`/`Design Principles` セクションが README_ja.md にはない(`grep -n '^##' README_ja.md` で確認済み)。意図的な省略か更新漏れかは本リポジトリから確認できない。
- `frontend/web` には `frontend/spa`(`node:test` 3ファイル)や `backend`(pytest)に相当する自動テストが存在しない。issue #88 の実装過程で手動ブラウザ検証のみ行われたことが確認できる(issue #88 のコメント)が、自動テストを追加するかどうかの方針はリポジトリ内から確認できない。
