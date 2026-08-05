# Operation Model

CI 定義が存在しないため(`.github/workflows` 等なし、確認済み)、以下は `README.md`/`README_ja.md` および `factory.sh`/`nuts_calc.py`/`web/` の実装から逆引きした手順である。

## CLI: セットアップと実行

```bash
python3 -m venv venv
source venv/bin/activate
pip install reportlab
```
根拠: `README.md:22-26,35`。パッケージ定義ファイル(`requirements.txt`/`pyproject.toml`/`setup.py`)は存在しないため、`pip install reportlab` を手動実行する必要がある([[../L0_concept/policy]] 参照)。

```bash
python3 nuts_calc.py <paper_size> <command> [options]
```
- `paper_size`: `A3` | `A4` | `B5` | `a4l`(A4横向き、大文字小文字どちらも可)
- `command`: `ope` | `com` | `100` | `99` | `aBc` | `squ` | `pi`

実行例(実機で成功を確認済み、7コマンドすべて):
```bash
python3 nuts_calc.py A4 ope -a 1 -b 1 --out-file result.pdf
python3 nuts_calc.py A4 com -a 100 --out-file result.pdf
python3 nuts_calc.py A4 100 --out-file result.pdf
python3 nuts_calc.py A4 99 -a 1 --out-file result.pdf
python3 nuts_calc.py A4 aBc -a 1 --out-file result.pdf
python3 nuts_calc.py A4 squ -a 1 --out-file result.pdf
python3 nuts_calc.py A4 pi -a 1 --out-file result.pdf
```
いずれも `result.pdf`(と `--merge` 未指定時は `result_read.pdf`)を生成し `All done` で終了することを確認済み。旧 `100masu.py:158` にあった `ini.intermediate` 未定義バグは解消されている。

## バッチ実行

```bash
./factory.sh
```
`factory.sh` は内部で `python nuts_calc.py ...`(`python` コマンド、`python3` ではない点に注意)を呼び出す(`factory.sh:127` 等)。リポジトリルートで実行し、`python` が有効な venv 等で `reportlab` を解決できる状態であることが前提。`_main`(`factory.sh` 内)が `dist/` 配下のディレクトリを作った上で `_basic` を呼ぶ(`_kuku` 系はコメントアウトされており現状は実行されない)。

## Web バックエンド(Flask)

```bash
cd web/backend
source ../../venv/bin/activate   # 上記でvenvを作成している場合
pip install Flask Flask-Cors
python app.py
```
根拠: `README.md:77-90`。`http://127.0.0.1:5000` で起動し、`POST /generate-pdf` にフォーム相当の JSON を送ると `nuts_calc.py` を `subprocess` 実行して PDF を返す(`web/backend/app.py:14-79`)。

## Web フロントエンド(React + Vite)

```bash
cd web/frontend
npm install
npm run dev      # http://localhost:5173
```

`npm run build` は 2026-08-05 時点の `main`(このブランチの分岐元)で実機確認済み: `package.json` に `i18next`/`react-i18next`/`i18next-browser-languagedetector`/`i18next-http-backend` が揃っており(コミット `724f752` 等)、`npm install && npm run build` が成功する(以前の "Rollup failed to resolve import "i18next"" 失敗は解消済み。詳細は [[../L3_implementation/specification_summary]])。

## `nuts_calc_tex.py`(実験的LaTeXプロトタイプ)のセットアップと実行

```bash
# pdflatex を含む LaTeX ディストリビューションが必要(例: texlive-latex-base + texlive-latex-extra)
python3 nuts_calc_tex.py A4 ope -a 1 -b 1 --out-file result.pdf
```
`vendor/texmf/tex/latex/longdivision/` を `TEXINPUTS` 経由で解決するため、クローン後の追加セットアップは不要(`nuts_calc.py` とは独立の CLI で、`factory.sh`/`web/backend/app.py` からは直接呼ばれない)。`pdflatex` が `PATH` にない場合は `_init()` ではなく `compile_tex` が明確なエラーで `exit(1)` する。詳細は [[../L3_implementation/nuts_calc_tex.py]]。

## テスト(pytest)

```bash
pip install pytest
pytest -q
```
`pytest.ini`(`testpaths = tests`, `pythonpath = .`)によりリポジトリルートで実行する。2026-08-05 時点でこのブランチの分岐元(`main`)で実行し、196件中187件成功・9件失敗を確認済み。失敗の9件は `tests/test_nuts_calc_init.py` の既知のstaleなテスト(`nuts_calc.py` の一部バリデーションが `exit()` から `exit(1)` に修正された(issue #37)後もテスト側の期待値が更新されていない)で、今回のドキュメント作業とは無関係。詳細は [[test]] を参照。`pdflatex` 依存の `nuts_calc_tex.py` CLI テストは `pdflatex` 未インストール時は自動的にスキップされる。

## ビルド

- CLI/Web バックエンド: ビルド工程なし(PDF/CSV 生成そのものが成果物)。
- Web フロントエンド: `npm run build`(Vite)。実機確認済み(成功)。

## 未確認事項

- `factory.sh` を実際に実行して `dist/` 配下の全生成物が意図通りかは未検証(今回は `nuts_calc.py` を直接呼び出しての動作確認のみ実施)。
- Web バックエンドを実際に起動し、フロントエンドと結合して `POST /generate-pdf`/`GET /renderer-info` が動作するかの結合確認(`pytest` の `tests/test_web_backend_app.py` はモジュールレベルの単体テストで、実プロセス起動を伴う結合確認ではない)は本ドキュメント作業では未実施。
- `nuts_calc_tex.py` の実機コンパイル(`pdflatex` インストール環境での CLI 直接実行)は本ドキュメント作業では未実施。ユニットテストと `docs/L3_implementation/nuts_calc_tex.py.md` に記載の過去の実機コンパイル確認内容を根拠としている。
