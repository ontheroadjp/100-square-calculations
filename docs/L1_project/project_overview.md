# Project Overview

## 目的

計算ドリル(四則演算・補数・100マス計算・九九・aBc変換・平方数・円周率倍)の練習用 PDF を、CLI(`nuts_calc.py`)または Web UI(`web/`)から生成するツール群。設計意図は [[concept]] を参照。

## 技術スタック

CI 定義・パッケージ定義(lock file 等)は Python 側に存在しないため、実装コードと README から直接確認した事実を記載する。

| 項目 | 内容 | 根拠 |
|---|---|---|
| CLI 言語 | Python 3 | `nuts_calc.py:1` shebang、`README.md:106` |
| 主要ライブラリ(CLI) | ReportLab | `nuts_calc.py` の import 群 |
| Web バックエンド | Flask + Flask-Cors | `web/backend/app.py:1-2,7-8`、`README.md:107-108` |
| Web フロントエンド | React 19 + Vite 7 + Tailwind CSS 4 | `web/frontend/package.json:12-29` |
| 国際化 | react-i18next(英語/日本語) | `web/frontend/src/i18n.js:1-4` |
| バッチ生成 | Bash(`set -Ceu`) | `factory.sh:1,38` |
| CLI(実験的プロトタイプ) | `nuts_calc_tex.py`(LaTeX/`pdflatex` レンダリング、`nuts_calc.py` とコード共有なし) | `nuts_calc_tex.py:1`、[[../L3_implementation/nuts_calc_tex.py]] |
| テスト | pytest(`tests/`、14ファイル、`pytest.ini`) | `pytest.ini:1-3`、`find tests -name 'test_*.py'` |
| パッケージマネージャ(Python) | pip(lock file なし。旧 `setup.py` は削除済み、`git log` のコミット `d9fc0a3` で確認) | `README.md:13-14` は pip インストールを謳うが検証すると裏付けとなるパッケージ定義ファイルは存在しない |
| パッケージマネージャ(Web) | npm(`package-lock.json` あり) | `web/frontend/package-lock.json` |
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

`nuts_calc.py` と同じ7コマンドを LaTeX(`pdflatex`)でレンダリングする独立プロトタイプ(issue #19 配下の全8フェーズが完了済み)。`nuts_calc.py` からは import 等のコード共有を一切行わない。まだ `web/backend`(`NUTS_CALC_RENDERER=latex` 経由でのみ有効化)からのみ到達可能で、`factory.sh` からは呼ばれない。筆算(縦書き)形式は `nuts_calc.py` から issue #46 で削除され、この `nuts_calc_tex.py` に一本化されている。詳細は [[../L3_implementation/nuts_calc_tex.py]] を参照。

### Web UI(`web/`、新規)

- `web/backend/app.py`: Flask アプリ。エンドポイントは `POST /generate-pdf`(PDF生成)と `GET /renderer-info`(現在有効なレンダラー名の取得、issue #46)の2つ。コマンド構築・レンダラー選択・subprocess 実行のロジックは `web/backend/renderers.py`(issue #36)に切り出されており、env 変数 `NUTS_CALC_RENDERER`(`reportlab`|`latex`、デフォルト `reportlab`)で `nuts_calc.py`/`nuts_calc_tex.py` を切り替えられる。詳細は [[../L3_implementation/specification_summary]] を参照。
- `web/frontend/src/App.jsx`: ヘッダー(タイトル・英語/日本語の言語切り替え)を描画し、本体は `GradeDrills.jsx` に委譲するシェル(`web/frontend/src/App.jsx`)。
- `web/frontend/src/GradeDrills.jsx`: トップ画面。学年(1〜6年生)+「無学年」+「カスタム」をリンク風ボタンで並べ、選択中の学年に応じて `drillPresets.js` のプリセットをカード表示する(通常形式のグリッドの下に、筆算プリセットがある学年のみ「筆算」セクションをインライン表示)。カードの「PDFを生成」を押すと、グリッドの代わりに詳細ページ(プレビュー・用紙サイズ/ページ数/問題数の設定・「戻る」)に切り替わる。詳細ページを開くと自動でプレビュー生成され、設定を変更するまで「PDF再生成」は非活性。ダウンロードは常に実際の `<a href download>` リンクをユーザーがクリックする2段階方式。
- `web/frontend/src/CustomGenerator.jsx`: 「カスタム」選択時に表示される、7種類の `command` すべてに対応する詳細パラメータフォーム(用紙サイズ・数値範囲・演算子・行列数・オプション)。`activeTab` state でタブ切り替え(計算内容/用紙/オプション/PDFプレビュー)を実装。

## 補助機能

- 用紙サイズ4種(A3/A4/A4横/B5)とページ分割: `nuts_calc.py`(旧 `100masu.py` から踏襲)。
- 解答を別紙/同一紙に赤字/末尾にまとめての切り替え(`--merge`, `--with-bottom-answer`)。
- CSV 出力オプション(`--csv`, `--debug`)。
- `factory.sh` によるバッチ生成。`python nuts_calc.py` という呼び出しに変更され(旧: 裸の `100masu.py`)、`PATH` 解決の曖昧さが軽減されている(`factory.sh:127` 等)。

## エントリポイント

- `nuts_calc.py` — CLI 単体実行: `python3 nuts_calc.py <paper_size> <command> [options]`
- `factory.sh` — バッチ実行(`python nuts_calc.py` を内部で呼び出す。リポジトリルートでの実行を前提)
- `web/backend/app.py` — Flask サーバー起動: `python app.py`(`web/backend` ディレクトリ内で実行、`http://127.0.0.1:5000`)
- `web/frontend/src/main.jsx` — React アプリのエントリ。`npm run dev`(`http://localhost:5173`)または `npm run build` で起動/ビルド

## 未確認事項

- 自動テストの有無: リポジトリ内に test ファイルは存在しない。
- CI/CD: `.github/workflows` 等の定義は存在しない。
- Web UI の実運用(本番デプロイ)構成: README には開発サーバーの起動手順のみが記載されており、本番ビルド・デプロイ手順の記述はない。
