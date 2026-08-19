# Project Overview

## 目的

計算ドリル(四則演算・補数・100マス計算・九九・aBc変換・平方数・円周率倍・分数・数論等)の練習用 PDF を、CLI(`backend/nuts_calc_tex.py`)または Web UI(`frontend/web` の軽量静的サイト。`backend/app.py` の Flask API を利用する、issue #88)から生成するツール群。設計意図は [[concept]] を参照。旧 CLI `backend/nuts_calc.py`(ReportLab)は issue #232 で削除され、`nuts_calc_tex.py`(LaTeX)が唯一の実装になった。もう1つの Web フロントエンドだった `frontend/spa`(React SPA)は issue #233 で削除され、`frontend/web` が唯一の Web UI フロントエンドになった。

## 技術スタック

CI 定義・パッケージ定義(lock file 等)は Python 側に存在しないため、実装コードと README から直接確認した事実を記載する。

| 項目 | 内容 | 根拠 |
|---|---|---|
| CLI 言語 | Python 3 | `backend/nuts_calc_tex.py:1` shebang、`README.md:106` |
| 主要レンダリング方式(CLI) | LaTeX(既定エンジン `lualatex`、`pdflatex` も選択可、issue #121/#186) | `backend/nuts_calc_tex.py` の `LatexEngineAdapter` 群 |
| Web バックエンド | Flask + Flask-Cors | `backend/app.py:1-2,7-8`、`README.md:107-108` |
| Web フロントエンド | vanilla JS + Vite(React/i18nライブラリ非依存)+ Sass(日本語のみ、issue #88) | `frontend/web/package.json`、[[../L3_implementation/specification_summary]] |
| バッチ生成 | Bash(`set -Ceu`) | `backend/factory.sh:1,38` |
| テスト | pytest(`backend/tests/`、26個の `test_*.py`) + Node.js 組み込み `node:test`(`frontend/web` 2ファイル) | `backend/pytest.ini:1-3`、`backend/tests/`、`frontend/web/src/*.test.js` |
| パッケージマネージャ(Python) | pip(lock file なし。旧 `setup.py` は削除済み、`git log` のコミット `d9fc0a3` で確認) | `README.md:13-14` は pip インストールを謳うが検証すると裏付けとなるパッケージ定義ファイルは存在しない |
| パッケージマネージャ(Web) | npm(`frontend/web` が独立した `package-lock.json` を持つ) | `frontend/web/package-lock.json` |
| ライセンス | MIT | `LICENSE:1-21` |

## 主要機能(実装から確認)

`nuts_calc_tex.py` の `command` 引数で切り替わる、以下を含む20種類の生成モード。うち7種類(`ope`/`com`/`100`/`99`/`aBc`/`squ`/`pi`)は旧 `nuts_calc.py`(ReportLab、issue #232 で削除)から意味論を踏襲しつつ独立に再実装されたもの、残り13種類(分数・混合・比較・数論・変換系)はLaTeX専用の後発コマンドである:

1. `ope` — 四則演算(加減乗除、`--operator`、`--intermediate` で4桁変換法の中間式表示。小数・繰り上がり/繰り下がり・余り・かっこ付き/N項/虫食い式・最終結果上限 `--result-max` にも対応)
2. `com` — 補数
3. `100` — 100マス計算
4. `99` — 九九
5. `aBc` — 4桁→3桁変換の暗算トレーニング
6. `squ` — 平方数
7. `pi` — 円周率(3.14)倍
8. `frac`/`mixed` — 分数・整数/小数/分数混在の四則演算
9. `compare` — 分数・整数・小数の大小比較
10. `evenodd`/`multiples`/`divisors`/`lcm`/`gcd` — 数の性質(偶数奇数判定・倍数・約数・最小公倍数・最大公約数)
11. `simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac` — 分数・小数の表現変換

**実機確認**: 全20コマンドが `python3 nuts_calc_tex.py A4 <command> ...` で正常に完了し、PDF/CSV を生成することを確認済み(`backend/nuts_calc_tex.py:124-449`)。Webでは `latex` がデフォルトかつ唯一到達可能なレンダラーのため(issue #186)、LaTeX専用カードは常に表示される。`factory.sh`(issue #232 で `nuts_calc.py` から切替済み)は上記のうち `ope`/`aBc`/`squ`/`99` のみを呼び出す。

### Web バックエンド(`backend/`、`frontend/web` が利用)

- `backend/app.py`: Flask アプリ。エンドポイントは `POST /generate-pdf`(PDF生成)、`POST /generate-problems`(PDFを生成せず問題データのみJSONで返す、issue #138)、`GET /renderer-info`(現在有効なレンダラー名の取得、issue #46)の3つ。コマンド構築・レンダラー選択・subprocess 実行のロジックは `backend/renderers.py`(issue #36)に切り出されており、env 変数 `NUTS_CALC_RENDERER`(デフォルト `latex`、issue #186 で `reportlab` から変更)で切り替える。切り替えの仕組み自体は将来の別レンダラー追加に備えて温存しているが、`reportlab`(`nuts_calc.py`)は issue #232 でコード自体が削除され、明示指定は他の未知の値と同じ汎用エラーで拒否される。`POST /generate-problems` は `command_type='ope'` に加え `com`/`99`/`aBc`/`squ`/`pi`/`frac`/`mixed`/`compare`/`evenodd`/`multiples`/`divisors`/`lcm`/`gcd`/`simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac` の計19種類に対応する(`100` のみ対象外、[[../L3_implementation/api]] 参照)。`backend/problem_generation.py` が CLI の生成関数をプロセス内で直接呼び出す例外で、subprocess は起動しない。詳細は [[../L3_implementation/api]]・[[../L3_implementation/specification_summary]] を参照。

かつては React SPA `frontend/spa` ももう1つの Web フロントエンドとして存在し、`App.jsx`(ヘッダー・英語/日本語切り替え)、`GradeDrills.jsx`(学年別ドリル選択トップ画面。LaTeX レンダラー時は1年生の繰り上がり・繰り下がり条件別6カード、4〜6年生の中学受験準備27カードを含む)、`CustomGenerator.jsx`(7種類の `command` に対応する詳細パラメータフォーム)を持っていたが、issue #233 で削除された。

### Web フロントエンド: `frontend/web`(静的サイト、新規、issue #88)

React・i18n ライブラリを使わず(日本語のみ対応)、HTML/CSS(Sass)/vanilla JS のみで実装されている。ユーザーの明示的な指示により SPA(単一ページを JS ルーターで画面切替)ではなく、画面ごとに実在の `.html` を持つ複数ページ構成(`index.html`/`catalog.html`/`preset.html`。旧 `custom.html` は issue #97 で削除)として実装されており、画面遷移は `<a href>` リンクのみで行う(issue #99 で唯一残っていた `catalog.html` の GET フォームを撤去したため、GET フォーム送信による遷移は現在存在しない)。`index.html` は学年カラーの2×3学年カードグリッド、`catalog.html` は `?grade=N` を読み `drillPresets.js` の `presetsByGrade[grade]` をカテゴリ(たし算/ひき算/かけ算/わり算/分数/四則混合/数の性質)ごとのドリルカード一覧として描画する(issue #99、`docs/uiux/wireframe_v1.png` 画面①②に対応)。`index.html` は PC(≥768px)幅では上記グレードグリッドの代わりに `pcMakeFlow.js`(issue #101)による「学年/計算を選ぶ/ドリル設定/プレビュー」の4カラムレイアウトを表示し、`catalog.html`/`preset.html` へのページ遷移なしに学年選択〜PDFプレビュー/ダウンロードまでを1画面内で完結させる(`wireframe_v1.png` の「PC版レイアウトイメージ」に対応。モバイル3画面フローとは独立した実装)。`preset.html` は `?grade=N&drillId=...` からドリルアイテムを特定し、設定 → 完了 → プレビューの3画面(issue #100、`wireframe_v1.png` 画面③④⑤に対応)を1ページ内の状態遷移として描画する。issue #97 でカスタム生成フォーム・検索・無学年ドリルへの導線を、issue #99 で数の種類/学年/レベル別の絞り込みUIを撤去したため、当時併存していた `frontend/spa` とは機能的に同等ではなかった(issue #90 の後続issueで段階的に再構築中だったが、`frontend/spa` 自体が issue #233 で削除されたため、以後は追従目標ではなくなった)。`drillPresets.js` は issue #98 で grade → category → menu-item の web 専用モデルへ書き換えられ、`frontend/spa` との追従コピー関係は終了した。`verticalLayout.js` は引き続き共通ロジックのコピーである(コピー元の `frontend/spa` 自体は issue #233 で削除済み)。旧 `drillCatalog.js`(#98 で `drillPresets.js` から旧カタログ形状を組み立てていたアダプター)は issue #99 で `catalog.js` が、issue #100 で `preset.js` が経由をやめたことでどのページからも参照されなくなり、issue #110 でファイル自体を削除した。`preset.html` のドリル詳細画面は issue #139 で、`command_type: 'ope'` かつ `POST /generate-problems` が対応する亜種(かっこ付き・虫食い・多項・混合演算子を除く)に限り、静的な例題配列の代わりに 300ms デバウンスの `POST /generate-problems` 呼び出しで取得した実データを例題チップに表示するようになった(当時併存していた `frontend/spa` にはこの機能はなく、`frontend/web` 独自だった)。issue #176 では、1・2年生向け基礎 `ope` ドリルの答えがカードのタイトルに掲げた上限(例: 1,000)を超えないよう `--result-max` を渡す対応を追加した。詳細は [[../L3_implementation/specification_summary]] を参照。

## 補助機能

- 用紙サイズ4種(A3/A4/A4横/B5)とページ分割: `nuts_calc_tex.py`(旧 `nuts_calc.py`/`100masu.py` から意味論を踏襲)。
- 解答を別紙/同一紙に赤字/末尾にまとめての切り替え(`--merge`, `--with-bottom-answer`)。
- CSV 出力オプション(`--csv`, `--debug`)。
- `factory.sh` によるバッチ生成。呼び出し先を `python nuts_calc.py` から `python nuts_calc_tex.py` に変更した(issue #232)。CLI引数体系が両スクリプトで一致していたため再設計は不要だった(`backend/factory.sh:127` 等)。

## エントリポイント

- `backend/nuts_calc_tex.py` — CLI 単体実行: `python3 nuts_calc_tex.py <paper_size> <command> [options]`(要 `pdflatex`/`lualatex`、`backend/` ディレクトリ内で実行)。旧 CLI `backend/nuts_calc.py`(ReportLab)は issue #232 で削除された。
- `backend/factory.sh` — バッチ実行(`python nuts_calc_tex.py` を内部で呼び出す。`backend/` ディレクトリ内での実行を前提)
- `backend/app.py` — Flask サーバー起動: `python app.py`(`backend/` ディレクトリ内で実行、`http://127.0.0.1:5000`。`frontend/web` が利用)
- `frontend/web/{index,catalog,preset}.html` — 静的サイトの3エントリ。`npm run dev`(Vite dev server)または `npm run build` で起動/ビルド(`frontend/web/vite.config.js:8-12`)

## 未確認事項

- CI/CD: `.github/workflows` 等の定義は存在しない(`find .github -type f` で確認済み)。
- Web UI の実運用(本番デプロイ)構成: README には開発サーバーの起動手順と frontend build だけがあり、本番デプロイ手順はない。
- Python/Node 単体テストは Flask と React を実プロセスで接続する結合テストを含まない。React コンポーネントの DOM 描画も未テストで、frontend の2テストは純粋なプリセット/レイアウト関数だけを対象とする([[../L2_development/test]])。
