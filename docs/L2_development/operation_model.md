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

**注意(実機確認済みの既知バグ)**: `npm install` 自体は成功するが、`npm run build`(および `npm run dev` で当該コンポーネントを描画しようとした場合)は `src/i18n.js` が要求する `i18next` 系パッケージが `package.json` の依存関係に存在しないため、Vite/Rollup のモジュール解決エラーで失敗する。

再現(実機確認済み):
```bash
cd web/frontend && npm install && npm run build
# => [vite]: Rollup failed to resolve import "i18next" from ".../src/i18n.js"
```
詳細は [[../L3_implementation/specification_summary]]。

## ビルド

- CLI/Web バックエンド: ビルド工程なし(PDF/CSV 生成そのものが成果物)。
- Web フロントエンド: `npm run build`(Vite)。上記の依存関係欠落により現状失敗する。

## 未確認事項

- `factory.sh` を実際に実行して `dist/` 配下の全生成物が意図通りかは未検証(今回は `nuts_calc.py` を直接呼び出しての動作確認のみ実施)。
- Web バックエンドを実際に起動し、フロントエンドと結合して `POST /generate-pdf` が動作するかは未検証(フロントエンドのビルドが壊れているため、結合テストの前提が崩れている)。
