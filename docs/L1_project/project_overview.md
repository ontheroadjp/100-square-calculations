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
| テスト | pytest(`backend/tests/`、18個の `test_*.py`) + Node.js 組み込み `node:test`(`frontend/spa` 3ファイル。`frontend/web` に自動テストなし) | `backend/pytest.ini:1-3`、`backend/tests/`、`frontend/spa/src/*.test.js` |
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

`nuts_calc.py` と同じ7コマンドにLaTeX専用 `frac`、`mixed`、`compare` を加えた計10コマンドを `pdflatex` でレンダリングする独立プロトタイプ。`frac` は厳密な分数四則演算、`mixed` は整数・小数・分数を混在させた多項式、`compare` は同分母・同分子・異分母の分数比較を生成し、`ope` は小数および2項整数加減算の繰り上がり・繰り下がり条件にも対応する。Webでは `NUTS_CALC_RENDERER=latex` の場合だけ、分数・小数・混合計算・筆算・中学受験準備と、1年生の条件付き加減算6カードを表示する。`factory.sh` からは呼ばれない。

### Web バックエンド(`backend/`、`frontend/spa`・`frontend/web` 共通)

- `backend/app.py`: Flask アプリ。エンドポイントは `POST /generate-pdf`(PDF生成)と `GET /renderer-info`(現在有効なレンダラー名の取得、issue #46)の2つ。コマンド構築・レンダラー選択・subprocess 実行のロジックは `backend/renderers.py`(issue #36)に切り出されており、env 変数 `NUTS_CALC_RENDERER`(`reportlab`|`latex`、デフォルト `reportlab`)で `nuts_calc.py`/`nuts_calc_tex.py` を切り替えられる。詳細は [[../L3_implementation/specification_summary]] を参照。

### Web フロントエンド(spa): `frontend/spa`(React SPA)

- `frontend/spa/src/App.jsx`: ヘッダー(タイトル・英語/日本語の言語切り替え)を描画し、本体は `GradeDrills.jsx` に委譲するシェル。
- `frontend/spa/src/GradeDrills.jsx`: トップ画面。学年(1〜6年生)+「無学年」+「カスタム」をリンク風ボタンで並べ、選択中の学年に応じて `drillPresets.js` のプリセットをカード表示する。LaTeX レンダラー時は、1年生に繰り上がり・繰り下がり条件で分けた加算2・減算2・混合2の6カードを表示し、通常形式の下に「筆算」を、4〜6年生ではさらに「中学受験」(各学年9カード、基礎/標準/発展×3レベル)を表示する。カードの「PDFを生成」を押すと詳細ページに切り替わり、プレビュー生成後に実際の `<a href download>` からダウンロードする。
- `frontend/spa/src/CustomGenerator.jsx`: 「カスタム」選択時に表示される、7種類の `command` すべてに対応する詳細パラメータフォーム(用紙サイズ・数値範囲・演算子・行列数・オプション)。`activeTab` state でタブ切り替え(計算内容/用紙/オプション/PDFプレビュー)を実装。

### Web フロントエンド(web): `frontend/web`(静的サイト、新規、issue #88)

React・i18n ライブラリを使わず(日本語のみ対応)、HTML/CSS(Sass)/vanilla JS のみで実装されている。ユーザーの明示的な指示により SPA(単一ページを JS ルーターで画面切替)ではなく、画面ごとに実在の `.html` を持つ複数ページ構成(`index.html`/`catalog.html`/`preset.html`。旧 `custom.html` は issue #97 で削除)として実装されており、画面遷移は `<a href>` リンクのみで行う(issue #99 で唯一残っていた `catalog.html` の GET フォームを撤去したため、GET フォーム送信による遷移は現在存在しない)。`index.html` は学年カラーの2×3学年カードグリッド、`catalog.html` は `?grade=N` を読み `drillPresets.js` の `presetsByGrade[grade]` をカテゴリ(たし算/ひき算/かけ算/わり算/分数/四則混合/数の性質)ごとのドリルカード一覧として描画する(issue #99、`docs/uiux/wireframe_v1.png` 画面①②に対応)。issue #97 でカスタム生成フォーム・検索・無学年ドリルへの導線を、issue #99 で数の種類/学年/レベル別の絞り込みUIを撤去したため、現時点では `frontend/spa` と機能的に同等ではない(issue #90 の後続issueで段階的に再構築中)。`drillPresets.js`/`drillCatalog.js`/`verticalLayout.js` は `frontend/spa` から複製した純粋データ/ロジック(React/i18n 非依存のため無変更で再利用可能)。詳細は [[../L3_implementation/specification_summary]] を参照。

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
- `frontend/web/{index,catalog,preset,custom}.html` — 静的サイトの4エントリ。`npm run dev`(Vite dev server)または `npm run build` で起動/ビルド(`vite.config.js` の `build.rollupOptions.input` に4エントリを列挙)

## 未確認事項

- CI/CD: `.github/workflows` 等の定義は存在しない(`find .github -type f` で確認済み)。
- Web UI の実運用(本番デプロイ)構成: README には開発サーバーの起動手順と frontend build だけがあり、本番デプロイ手順はない。
- Python/Node 単体テストは Flask と React を実プロセスで接続する結合テストを含まない。React コンポーネントの DOM 描画も未テストで、frontend の2テストは純粋なプリセット/レイアウト関数だけを対象とする([[../L2_development/test]])。
