# Repository Structure

単一リポジトリだが、CLI/バックエンド関連は `backend/` に、フロントエンドは `frontend/web` に、それぞれ分かれたミニ・モノレポ構成(それぞれ独立した実行環境: Python venv / npm)。issue #88 で `web/backend`・`web/frontend`・リポジトリルート直下の CLI/テストを再編し、`backend`/`frontend/{spa,web}` レイアウトに変更した(将来 `backend`/`frontend` を別リポジトリへ分離する可能性を見据えた構成、[[../L0_concept/policy]] 未記載・issue #88 の背景)。当初は `frontend/spa`(React SPA)も併存していたが、issue #233 で削除され `frontend/web` が唯一のフロントエンドになった。ディレクトリ一覧で確認済み。

```
100-square-calculations/
├── memo.md              # 暗算指導法の解説(教育コンテンツ、非コード)
├── LICENSE              # MIT License
├── README.md            # 利用者向け説明(英語)
├── README_ja.md         # 利用者向け説明(日本語、README.md の対訳。下記「未確認事項」参照)
├── .gitignore
├── backend/              # CLI・Flask API・テストを集約した自己完結ツリー(issue #88)
│   ├── nuts_calc_tex.py    # LaTeX(pdflatex/lualatex)レンダリングのPDF生成CLI本体(実行可能)。旧 ReportLab CLI nuts_calc.py は issue #232 で削除
│   ├── factory.sh          # バッチ生成シェルスクリプト(実行可能)
│   ├── app.py              # Flask API(POST /generate-pdf, POST /generate-problems, GET /renderer-info)
│   ├── renderers.py        # レンダラー選択・CLIコマンド構築・subprocess実行(Flask非依存、issue #36)
│   ├── problem_generation.py  # POST /generate-problems 用、CLIの生成関数をin-processで呼ぶラッパー(issue #138)
│   ├── pytest.ini          # pytest 設定(testpaths=tests, pythonpath=.)
│   ├── tests/               # pytestテストスイート(26個のtest_*.py)。nuts_calc_tex.py/app.py/renderers.py/problem_generation.pyを対象
│   └── vendor/
│       └── texmf/tex/latex/longdivision/  # CTAN 'longdivision' パッケージのvendoring(nuts_calc_tex.pyの--vertical divで使用)
├── frontend/
│   └── web/               # HTML/CSS(Sass)/JS のみの軽量実装(新規、issue #88)。日本語のみ、i18nライブラリ不要。かつて併存していた spa/(React SPA)は issue #233 で削除
│       ├── index.html / catalog.html / preset.html  # 画面ごとに実在するページ(SPAではない複数ページ構成、ユーザー要望)。custom.html は issue #97 で削除
│       ├── vite.config.js / vite.config.test.js  # Vite マルチページビルド設定(3 HTML エントリ)と dev sourcemap 設定テスト
│       ├── src/
│       │   ├── home.js / catalog.js / preset.js  # 各ページのエントリスクリプト。custom.js は issue #97 で削除
│       │   ├── navShell.js  # モバイル下部タブバー/PCサイドバーの共通ナビゲーションシェル(issue #97)
│       │   ├── pcMakeFlow.js  # index.html のPC(≥768px)向け4カラムレイアウト(学年/計算を選ぶ/ドリル設定/プレビュー、issue #101)。マウント可能な独立ウィジェット(home.js から呼ばれる)
│       │   ├── drillPresets.js / verticalLayout.js  # 前者はissue #98でweb専用モデルへ分岐。後者のみspa由来の共通ロジック。旧drillCatalog.jsはissue #110で削除
│       │   ├── presetDetail.js  # マウント可能な独立ウィジェット(preset.js から呼ばれる)。customGenerator.js は issue #97 で削除
│       │   ├── strings.js / strings.ja.json  # 静的日本語文字列テーブル。issue #97 でナビシェル用キー、issue #101 でPC4カラムレイアウト用キーを追加(この差分により `frontend/spa` の `ja/translation.json` との完全一致ではなくなった)
│       │   └── styles/main.scss (+ _base/_components/_layout/_navShell/_pcMakeFlow.scss)  # frontend/spa の App.css を移植した Sass + issue #97 で追加したナビシェル用パーシャル + issue #101 で追加したPC4カラムレイアウト用パーシャル
│       └── package.json         # devDependencies は vite と sass のみ(React・i18next系は含まない)
└── docs/                 # 設計ドキュメントと教材仕様の一次資料(reference/)
```

`example_result.pdf` は `dev` ブランチのマージで削除されている(`.gitignore` には依然 `!example_result.pdf` という除外例外が残っているが、対象ファイルが存在しないため実質無効。[[../L2_development/consistency_checks]] 参照)。

## 各ファイル/ディレクトリの責務(実装から確認)

- `backend/nuts_calc_tex.py`: CLI エントリポイント兼ロジック全体。旧 ReportLab CLI(`nuts_calc.py`、旧 `100masu.py` から機能的に踏襲していた実装)は issue #232 で削除され、本ファイルが唯一の CLI/PDF生成ロジックになった。7つの互換コマンド(`ope`/`com`/`100`/`99`/`aBc`/`squ`/`pi`)とLaTeX専用の分数・混合・比較・数論・変換系を合わせた計20コマンドをレンダリングする。`ope` は小数、繰り上がり/繰り下がり、余り、複数式形式、結果上限に対応する。`vendor/texmf` は `__file__` から自己相対解決する。
- `backend/factory.sh`: `_basic`/`_kuku`系関数で用紙サイズ・分量違いの複数パターンを `dist/` 以下に一括生成。`python nuts_calc_tex.py ...`(`backend/` 内の相対呼び出し、issue #232 で `nuts_calc.py` から切替)を内部で使うため、`backend/` ディレクトリ内での実行を前提にしている(`python`(`python3` ではない)が `PATH` 上にあることも前提。LaTeX(`pdflatex`/`lualatex`)が別途必要)。
- `memo.md`: コードではなく、暗算指導法・学習ステップ・受験算数における計算力の重要性を説明する日本語の教育コンテンツ。
- `LICENSE`: MIT License(`LICENSE:1-21`、Copyright (c) 2025 ontheroadjp)。
- `README.md` / `README_ja.md`: 英語/日本語で内容が対応した利用者向け説明。CLI・`factory.sh`・Web UI(バックエンド/フロントエンド起動手順)をカバーしている。README.md には `Architecture`/`Design Principles` セクションがあるが README_ja.md には対応するセクションがなく、両者は完全な対訳ではなくなっている(下記「未確認事項」参照)。
- `backend/tests/`: pytestテストスイート(26個の `test_*.py`、`test_problem_generation.py` は issue #138 の `backend/problem_generation.py` を検証する)。Flask/CLI変換、各ドリル生成を検証する(issue #232 でレンダラーは `latex` の1種類のみになった)。`frontend/web` には `node:test` 3ファイル(`src/` の2ファイルと `vite.config.test.js`)がある。詳細は [[../L2_development/test]]。
- `docs/reference/`: 教材仕様の根拠となる一次資料を出典・取得日・SHA-256と共に保存する(`docs/reference/README.md:1-24`)。
- `backend/vendor/texmf/tex/latex/longdivision/`: CTAN の `longdivision` パッケージ(LPPLライセンス)を vendoring したもの。Ubuntu の `texlive-latex-extra` に同梱されていないため、`nuts_calc_tex.py` が `TEXINPUTS` 経由でこのパスを解決する([[../L3_implementation/nuts_calc_tex.py]] 参照)。
- `backend/app.py`: Flask アプリ。`POST /generate-pdf`(PDF生成)、`POST /generate-problems`(PDFを生成せず問題データのみJSONで返す、issue #138)、`GET /renderer-info`(有効レンダラー名の取得)の3エンドポイント。コマンド構築・レンダラー選択・subprocess実行は `backend/renderers.py` に切り出されている(詳細は [[../L1_project/project_overview]])。`frontend/web` から利用される(かつては `frontend/spa` も共通利用していたが issue #233 で削除)。`POST /generate-problems` は現状 `frontend/web` の `preset.html` のみが呼ぶ。
- `backend/renderers.py`: `NUTS_CALC_RENDERER` env 変数(デフォルト `latex`、issue #186 で `reportlab` から変更)経由で `nuts_calc_tex.py` を呼び出す、Flask 非依存の純粋関数群(issue #36)。レンダラー切り替えの仕組み自体は将来の別レンダラー追加に備えて温存しているが、`nuts_calc.py`(ReportLab)は issue #232 でコード自体が削除され、`RENDERER_SCRIPTS` は現在 `latex` の1エントリのみを持つ。`RENDERER_SCRIPTS` はスクリプトパスを `Path(__file__).resolve().parent`(=`backend/`)基準で解決する(issue #88 で `web/backend/` からの移動に伴い repo-root 基準から変更)。
- `backend/problem_generation.py`: `POST /generate-problems` が使う、`nuts_calc_tex.py` の既存データ生成関数をsubprocessを起動せずプロセス内で直接呼び出すラッパー(issue #138)。`ope` を含む19コマンド(`100` を除く全対応コマンド)に対応する。詳細は [[../L3_implementation/api]]。
- `frontend/web/`: HTML/CSS(Sass)/JS のみの軽量フロントエンド(新規、issue #88)。React・i18n ライブラリを使わず日本語のみに対応する。ユーザーの明示的な指示により、SPA(単一 `index.html` を JS ルーターで画面切替する構成)ではなく、画面ごとに実在の `.html` を持つ複数ページ構成として実装されている(通常の `<a href>` リンクと GET フォームで画面遷移する)。かつて併存していた `frontend/spa/`(Vite ベースの React SPA。トップ画面は学年別ドリル選択の `GradeDrills.jsx`、「カスタム」選択時の詳細パラメータ指定フォーム `CustomGenerator.jsx` を持ち、`frontend/web` と機能的に同等だった)は issue #233 で削除された。

## 未確認事項

- `docs/` 以外に、リポジトリ外で管理されているドキュメント(Notion、Google Docs等)があるかどうかは本リポジトリから確認できない。
- `backend/generated_pdfs/`(実行時に自動作成されるディレクトリ、`backend/app.py:11-12`)が `.gitignore` の対象になっていない点は [[../L0_concept/policy]] に記録済み。
- README.md には存在する `Architecture`/`Design Principles` セクションが README_ja.md にはない(`grep -n '^##' README_ja.md` で確認済み)。意図的な省略か更新漏れかは本リポジトリから確認できない。
- ブラウザDOM/E2Eテストの方針は未確認。`frontend/web` の3つの `node:test` はデータモデル・純粋ヘルパー・Vite 設定のみを対象とする。
