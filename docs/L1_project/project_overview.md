# Project Overview

## 目的

計算ドリル(四則演算・補数・100マス計算・九九・aBc変換・平方数・円周率倍)の練習用 PDF を、CLI(`backend/nuts_calc.py`)または Web UI(`frontend/spa` の React SPA、または `frontend/web` の軽量静的サイト。いずれも `backend/app.py` の Flask API を共通利用する、issue #88)から生成するツール群。設計意図は [[concept]] を参照。

## 技術スタック

CI 定義・パッケージ定義(lock file 等)は Python 側に存在しないため、実装コードと README から直接確認した事実を記載する。

| 項目 | 内容 | 根拠 |
|---|---|---|
| CLI 言語 | Python 3 | `backend/nuts_calc.py:1` shebang、`README.md:106` |
| 主要ライブラリ(CLI) | ReportLab | `backend/nuts_calc.py` の import 群 |
| Web バックエンド | Flask + Flask-Cors | `backend/app.py:1-2,7-8`、`README.md:107-108` |
| Web フロントエンド(spa) | React/ReactDOM 19.1.1 + Vite 7.1.5 + Tailwind CSS 4.1.13 | `frontend/spa/package-lock.json:packages["node_modules/react"|"react-dom"|"vite"|"tailwindcss"].version` |
| 国際化(spa のみ) | i18next 26.3.6 + react-i18next 17.0.10(英語/日本語) | `frontend/spa/package-lock.json:packages["node_modules/i18next"|"react-i18next"].version`、`frontend/spa/src/i18n.js:1-29` |
| Web フロントエンド(web) | vanilla JS + Vite(React/i18nライブラリ非依存)+ Sass(日本語のみ、issue #88) | `frontend/web/package.json`、[[../L3_implementation/specification_summary]] |
| バッチ生成 | Bash(`set -Ceu`) | `backend/factory.sh:1,38` |
| CLI(実験的プロトタイプ) | `nuts_calc_tex.py`(LaTeX/`pdflatex` レンダリング、`nuts_calc.py` とコード共有なし) | `backend/nuts_calc_tex.py:1`、[[../L3_implementation/nuts_calc_tex.py]] |
| テスト | pytest(`backend/tests/`、26個の `test_*.py`) + Node.js 組み込み `node:test`(`frontend/spa` 3ファイル、`frontend/web` 2ファイル) | `backend/pytest.ini:1-3`、`backend/tests/`、`frontend/{spa,web}/src/*.test.js` |
| パッケージマネージャ(Python) | pip(lock file なし。旧 `setup.py` は削除済み、`git log` のコミット `d9fc0a3` で確認) | `README.md:13-14` は pip インストールを謳うが検証すると裏付けとなるパッケージ定義ファイルは存在しない |
| パッケージマネージャ(Web) | npm(`frontend/spa`・`frontend/web` それぞれ独立した `package-lock.json` を持つ) | `frontend/spa/package-lock.json`、`frontend/web/package-lock.json` |
| ライセンス | MIT | `LICENSE:1-21` |

## 主要機能(実装から確認)

`nuts_calc.py` の `command` 引数で切り替わる7種類の生成モード(旧 `100masu.py` から機能・行番号ともに概ね踏襲、リネームはコミット `d9fc0a3`):

1. `ope` — 四則演算(加減乗除、`--operator`、`--intermediate` で4桁変換法の中間式表示)
2. `com` — 補数
3. `100` — 100マス計算
4. `99` — 九九
5. `aBc` — 4桁→3桁変換の暗算トレーニング
6. `squ` — 平方数
7. `pi` — 円周率(3.14)倍

**実機確認**: 上記7コマンドすべてが `python3 nuts_calc.py A4 <command> ...` で正常に完了し、PDF/CSV を生成することを確認済み。旧 `100masu.py:158` にあった `ini.intermediate` 未定義参照バグ([[../L0_concept/policy]] 参照)は解消されている。

### `nuts_calc_tex.py`(実験的プロトタイプ)

`nuts_calc.py` と同じ7コマンドにLaTeX専用の分数・混合・比較・数論・変換系を加えた計20コマンドをレンダリングする独立プロトタイプ。`ope` は小数、繰り上がり・繰り下がり、余り、かっこ付き/N項/虫食い式、最終結果上限(`--result-max`)に対応する。Webでは `latex` がデフォルトかつ唯一到達可能なレンダラーのため(issue #186)、LaTeX専用カードは常に表示される。`factory.sh` からは呼ばれない(`backend/nuts_calc_tex.py:124-449`)。

### Web バックエンド(`backend/`、`frontend/spa`・`frontend/web` 共通)

- `backend/app.py`: Flask アプリ。エンドポイントは `POST /generate-pdf`(PDF生成)、`POST /generate-problems`(PDFを生成せず問題データのみJSONで返す、issue #138)、`GET /renderer-info`(現在有効なレンダラー名の取得、issue #46)の3つ。コマンド構築・レンダラー選択・subprocess 実行のロジックは `backend/renderers.py`(issue #36)に切り出されており、env 変数 `NUTS_CALC_RENDERER`(デフォルト `latex`、issue #186 で `reportlab` から変更)で切り替える。`reportlab`(`nuts_calc.py`)は明示指定しても「利用不可」の明確なエラーになり到達不能(コード自体は削除していない)。`POST /generate-problems`(現時点では `command_type='ope'` のみ)は `backend/problem_generation.py` が CLI の生成関数をプロセス内で直接呼び出す例外で、subprocess は起動しない。詳細は [[../L3_implementation/api]]・[[../L3_implementation/specification_summary]] を参照。

### Web フロントエンド(spa): `frontend/spa`(React SPA)

- `frontend/spa/src/App.jsx`: ヘッダー(タイトル・英語/日本語の言語切り替え)を描画し、本体は `GradeDrills.jsx` に委譲するシェル。
- `frontend/spa/src/GradeDrills.jsx`: トップ画面。学年(1〜6年生)+「無学年」+「カスタム」をリンク風ボタンで並べ、選択中の学年に応じて `drillPresets.js` のプリセットをカード表示する。LaTeX レンダラー時は、1年生に繰り上がり・繰り下がり条件で分けた加算2・減算2・混合2の6カードを表示し、通常形式の下に「筆算」を、4〜6年生ではさらに「中学受験」(各学年9カード、基礎/標準/発展×3レベル)を表示する。カードの「PDFを生成」を押すと詳細ページに切り替わり、プレビュー生成後に実際の `<a href download>` からダウンロードする。
- `frontend/spa/src/CustomGenerator.jsx`: 「カスタム」選択時に表示される、7種類の `command` すべてに対応する詳細パラメータフォーム(用紙サイズ・数値範囲・演算子・行列数・オプション)。`activeTab` state でタブ切り替え(計算内容/用紙/オプション/PDFプレビュー)を実装。

### Web フロントエンド(web): `frontend/web`(静的サイト、新規、issue #88)

React・i18n ライブラリを使わず(日本語のみ対応)、HTML/CSS(Sass)/vanilla JS のみで実装されている。ユーザーの明示的な指示により SPA(単一ページを JS ルーターで画面切替)ではなく、画面ごとに実在の `.html` を持つ複数ページ構成(`index.html`/`catalog.html`/`preset.html`。旧 `custom.html` は issue #97 で削除)として実装されており、画面遷移は `<a href>` リンクのみで行う(issue #99 で唯一残っていた `catalog.html` の GET フォームを撤去したため、GET フォーム送信による遷移は現在存在しない)。`index.html` は学年カラーの2×3学年カードグリッド、`catalog.html` は `?grade=N` を読み `drillPresets.js` の `presetsByGrade[grade]` をカテゴリ(たし算/ひき算/かけ算/わり算/分数/四則混合/数の性質)ごとのドリルカード一覧として描画する(issue #99、`docs/uiux/wireframe_v1.png` 画面①②に対応)。`index.html` は PC(≥768px)幅では上記グレードグリッドの代わりに `pcMakeFlow.js`(issue #101)による「学年/計算を選ぶ/ドリル設定/プレビュー」の4カラムレイアウトを表示し、`catalog.html`/`preset.html` へのページ遷移なしに学年選択〜PDFプレビュー/ダウンロードまでを1画面内で完結させる(`wireframe_v1.png` の「PC版レイアウトイメージ」に対応。モバイル3画面フローとは独立した実装)。`preset.html` は `?grade=N&drillId=...` からドリルアイテムを特定し、設定 → 完了 → プレビューの3画面(issue #100、`wireframe_v1.png` 画面③④⑤に対応)を1ページ内の状態遷移として描画する。issue #97 でカスタム生成フォーム・検索・無学年ドリルへの導線を、issue #99 で数の種類/学年/レベル別の絞り込みUIを撤去したため、現時点では `frontend/spa` と機能的に同等ではない(issue #90 の後続issueで段階的に再構築中)。`drillPresets.js` は issue #98 で grade → category → menu-item の web 専用モデルへ書き換えられ、`frontend/spa` との追従コピー関係は終了した。`verticalLayout.js` は引き続き共通ロジックのコピーである。旧 `drillCatalog.js`(#98 で `drillPresets.js` から旧カタログ形状を組み立てていたアダプター)は issue #99 で `catalog.js` が、issue #100 で `preset.js` が経由をやめたことでどのページからも参照されなくなり、issue #110 でファイル自体を削除した。`preset.html` のドリル詳細画面は issue #139 で、`command_type: 'ope'` かつ `POST /generate-problems` が対応する亜種(かっこ付き・虫食い・多項・混合演算子を除く)に限り、静的な例題配列の代わりに 300ms デバウンスの `POST /generate-problems` 呼び出しで取得した実データを例題チップに表示するようになった(`frontend/spa` にはこの機能はなく、`frontend/web` 独自)。issue #176 では、1・2年生向け基礎 `ope` ドリルの答えがカードのタイトルに掲げた上限(例: 1,000)を超えないよう `--result-max` を渡す対応を追加した。詳細は [[../L3_implementation/specification_summary]] を参照。

## 補助機能

- 用紙サイズ4種(A3/A4/A4横/B5)とページ分割: `nuts_calc.py`(旧 `100masu.py` から踏襲)。
- 解答を別紙/同一紙に赤字/末尾にまとめての切り替え(`--merge`, `--with-bottom-answer`)。
- CSV 出力オプション(`--csv`, `--debug`)。
- `factory.sh` によるバッチ生成。`python nuts_calc.py` という呼び出しに変更され(旧: 裸の `100masu.py`)、`PATH` 解決の曖昧さが軽減されている(`backend/factory.sh:127` 等)。

## エントリポイント

- `backend/nuts_calc.py` — CLI 単体実行: `python3 nuts_calc.py <paper_size> <command> [options]`(`backend/` ディレクトリ内で実行)
- `backend/nuts_calc_tex.py` — 実験的 LaTeX プロトタイプの単体実行: `python3 nuts_calc_tex.py <paper_size> <command> [options]`(要 `pdflatex`、`backend/` ディレクトリ内で実行)
- `backend/factory.sh` — バッチ実行(`python nuts_calc.py` を内部で呼び出す。`backend/` ディレクトリ内での実行を前提)
- `backend/app.py` — Flask サーバー起動: `python app.py`(`backend/` ディレクトリ内で実行、`http://127.0.0.1:5000`。`frontend/spa`・`frontend/web` 共通)
- `frontend/spa/src/main.jsx` — React アプリのエントリ。`npm run dev`(`http://localhost:5173`)または `npm run build` で起動/ビルド
- `frontend/web/{index,catalog,preset}.html` — 静的サイトの3エントリ。`npm run dev`(Vite dev server)または `npm run build` で起動/ビルド(`frontend/web/vite.config.js:8-12`)

## 未確認事項

- CI/CD: `.github/workflows` 等の定義は存在しない(`find .github -type f` で確認済み)。
- Web UI の実運用(本番デプロイ)構成: README には開発サーバーの起動手順と frontend build だけがあり、本番デプロイ手順はない。
- Python/Node 単体テストは Flask と React を実プロセスで接続する結合テストを含まない。React コンポーネントの DOM 描画も未テストで、frontend の2テストは純粋なプリセット/レイアウト関数だけを対象とする([[../L2_development/test]])。
