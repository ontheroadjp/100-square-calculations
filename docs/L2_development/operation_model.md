# Operation Model

CI 定義が存在しないため(`.github/workflows` 等なし、確認済み)、以下は `README.md`/`README_ja.md` および `backend/factory.sh`/`backend/nuts_calc_tex.py`/`frontend/` の実装から逆引きした手順である。issue #88 でリポジトリを `backend/` + `frontend/{spa,web}` に再編したため、CLI/Flask 関連のコマンドはすべて `backend/` ディレクトリ内での実行が前提になっている。

## CLI: セットアップと実行

旧 ReportLab CLI(`nuts_calc.py`)は issue #232 で削除され、CLI は `nuts_calc_tex.py`(LaTeX レンダリング)のみになった。`nuts_calc_tex.py` は標準ライブラリのみで書かれており(`import argparse`/`csv`/`math`/`os`/`random`/`shutil`/`subprocess`/`tempfile` 等、`backend/nuts_calc_tex.py:40-50`)、pip パッケージのインストールは不要。ただし LaTeX ディストリビューション(既定エンジン `lualatex`。`pdflatex` も選択可、issue #121/#186、[[../L3_implementation/nuts_calc_tex.py]] 参照)が別途必要:

```bash
cd backend
python3 nuts_calc_tex.py <paper_size> <command> [options]
```
- `paper_size`: `A3` | `A4` | `B5` | `a4l`(A4横向き、大文字小文字どちらも可)
- `command`: `ope` | `com` | `100` | `99` | `aBc` | `squ` | `pi` | `frac` | `mixed` | `compare` | `evenodd` | `multiples` | `divisors` | `lcm` | `gcd` | `simplify` | `commondenom` | `frac2dec` | `dec2frac` | `divfrac`

実行例:
```bash
cd backend
python3 nuts_calc_tex.py A4 ope --a-min 1 --a-max 9 --b-min 1 --b-max 9 --operator add --rows 5 --columns 2 --page 1 --out-file result.pdf
```

## バッチ実行

```bash
cd backend
./factory.sh
```
`factory.sh` は内部で `python nuts_calc_tex.py ...`(`python` コマンド、`python3` ではない点に注意。issue #232 で `nuts_calc.py` から切替)を呼び出す(`backend/factory.sh:127` 等)。`backend/` ディレクトリ内で実行し、`python` が有効な LaTeX ディストリビューションを解決できる状態であることが前提。`_main`(`factory.sh` 内)が `dist/` 配下のディレクトリを作った上で `_basic` を呼ぶ(`_kuku` 系はコメントアウトされており現状は実行されない)。

## Web バックエンド(Flask、`frontend/spa`・`frontend/web` 共通)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install Flask Flask-Cors
python app.py
```
根拠: `README.md:77-90`。パッケージ定義ファイル(`requirements.txt`/`pyproject.toml`/`setup.py`)は存在しないため、`pip install Flask Flask-Cors` を手動実行する必要がある([[../L0_concept/policy]] 参照)。`http://127.0.0.1:5000` で起動し、`POST /generate-pdf` にフォーム相当の JSON を送ると `nuts_calc_tex.py` を `subprocess` 実行して PDF を返す(`backend/app.py:14-79`)。`renderers.py` のスクリプトパス解決は `Path(__file__).resolve().parent`(=`backend/`)基準のため、`backend/` 直下に `nuts_calc_tex.py` が存在することを前提にしている(issue #88)。

## Web フロントエンド(spa): React + Vite

```bash
cd frontend/spa
node --version
npm --version
npm install
npm run dev      # http://localhost:5173
```

`npm run build` は 2026-08-12 に実機確認済み(成功)。`package.json` に `i18next`/`react-i18next`/`i18next-browser-languagedetector`/`i18next-http-backend` が揃っている。`npm run lint` は同日の検証で `frontend/spa/src/drillPresets.js:433` の日本語コメント内全角空白を `no-irregular-whitespace` が拒否し、1件失敗する(行番号は issue #88 以前の観測時点(`:363`)から、プリセット追加に伴い `:433` へ変化しているが、指摘内容は同一)。

## Web フロントエンド(web): 静的サイト(vanilla JS + Sass、新規、issue #88)

```bash
cd frontend/web
node --version
npm --version
npm install
npm run dev      # http://localhost:5174 等(5173が使用中の場合は自動で別ポート)
```

`npm run build` は Vite のマルチページビルド(`vite.config.js` の `build.rollupOptions.input` に3つの `.html` を列挙。`custom.html` entry は issue #97 で削除)で `dist/index.html`/`catalog.html`/`preset.html` を出力する。2026-08-18 に実機確認済み(成功)。`package.json` の devDependencies は `vite`/`sass` のみで、React・i18next 系は含まない。`lint` スクリプトは定義されていない。

## `nuts_calc_tex.py` の追加コマンド例

```bash
cd backend
# pdflatex を含む LaTeX ディストリビューションが必要(例: texlive-latex-base + texlive-latex-extra)
python3 nuts_calc_tex.py A4 ope -a 1 -b 1 --out-file result.pdf
python3 nuts_calc_tex.py A4 frac --numerator-digits 1 --denominator-digits 1 --same-denominator --proper-operands -o add sub --out-file fractions.pdf
python3 nuts_calc_tex.py A4 compare --comparison-pattern same-denominator --a-fraction-form proper --b-fraction-form proper --out-file compare.pdf
python3 nuts_calc_tex.py A4 mixed --a-kind int decimal --b-kind fraction --terms 3 --out-file mixed.pdf
python3 nuts_calc_tex.py A4 ope -o add sub --mixed-carry-borrow --out-file grade1-mixed.pdf
```
`frac` は分子・分母の桁数(1〜3)と四則演算を受け付け、同分母・異分母・真分数条件を追加できる。`compare` は同分母・同分子・異分母の比較パターンと、左右独立の真分数・仮分数・帯分数指定を受け付ける。`mixed` は整数・小数・分数を混在させ、`ope` は `--a-decimal-places`/`--b-decimal-places` と `--carry-borrow`/`--no-carry-borrow`/`--mixed-carry-borrow` を追加で受け付ける。繰り上がり系フラグ指定時は `--a-min` 等の範囲より条件を優先し、必要なら対応する1桁加減算の候補範囲へフォールバックする。繰り下がりありの減算は10〜19−1桁に限定する。`backend/vendor/texmf/tex/latex/longdivision/` は `TEXINPUTS` 経由で解決する(`__file__` からの自己相対パスのため `backend/` 内での実行を前提にしなくても動作するが、CLI 自体は `backend/` 内実行を想定した相対パス例で記載している)。`pdflatex` が無い場合は明確なエラーで終了する。

`ope --result-max N` は通常2項・かっこ付き・N項・虫食いの全式形式で最終表示結果を `N` 以下に制約する。例: `python3 nuts_calc_tex.py A4 ope -o add --a-min 1 --a-max 999 --b-min 1 --b-max 999 --result-max 1000 --out-file result.pdf`。成立する式が retry 上限内に無ければ明示エラーになる(`backend/nuts_calc_tex.py:193-196,620-624,1341-1404`)。

## テスト(pytest)

```bash
cd backend
pip install pytest
python3 -m pytest -q
```
`backend/pytest.ini` により `backend/` ディレクトリ内で実行する。issue #232(`nuts_calc.py` 削除)後は687件全てが成功する。詳細は [[test]]。

frontend の純粋関数テストは `package.json` に script がないため直接実行する:

```bash
node --test frontend/spa/src/drillPresets.test.js frontend/spa/src/drillCatalog.test.js frontend/spa/src/verticalLayout.test.js
```

2026-08-19 に17件すべて成功した。`frontend/web` は `node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js` で45件すべて成功した。

## ビルド

- CLI/Web バックエンド: ビルド工程なし(PDF/CSV 生成そのものが成果物)。
- `frontend/spa`: `npm run build`(Vite)。2026-08-12 実機確認済み(成功)。
- `frontend/web`: `npm run build`(Vite、マルチページ)。2026-08-12 実機確認済み(成功)。

## 未確認事項

- `factory.sh` を実際に実行して `dist/` 配下の全生成物が意図通りかは未検証(今回は `nuts_calc_tex.py` を直接呼び出しての動作確認のみ実施)。
- Web バックエンドを実際に起動し、フロントエンドと結合して `POST /generate-pdf`/`GET /renderer-info` が動作するかの pytest による結合確認(`backend/tests/test_web_backend_app.py` はモジュールレベルの単体テストで、実プロセス起動を伴う結合確認ではない)は本ドキュメント作業では未実施。ただし issue #88 の実装過程では、`backend/app.py` を実プロセスで起動し `frontend/spa`・`frontend/web` の両方から手動ブラウザ検証を行い、正常動作を確認している(pytest によるものではない)。
- frontend の production build をどこへ配備するか、および Flask と結合したブラウザ E2E の実行方法は未確認。確定にはデプロイ設定または E2E 設定ファイルが必要だが、現行リポジトリには存在しない。
