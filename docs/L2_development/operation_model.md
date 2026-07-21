# Operation Model

CI 定義が存在しないため（`.github/workflows` 等なし、確認済み）、以下は `README.md` および `factory.sh`/`100masu.py` の実装から逆引きした手順である。

## セットアップ

```bash
pip install reportlab
```
根拠: `README.md:32-35`。バージョン固定なし（[[policy]] 参照）。

## 単体実行

```bash
python3 100masu.py <paper_size> <command> [options]
```

- `paper_size`: `A3` | `A4` | `B5` | `a3` | `a4` | `b5` | `a4l`（大文字小文字どちらも可、`a4l` は A4 横向き） — 根拠: `100masu.py:46-50`
- `command`: `ope` | `com` | `100` | `99` | `aBc` | `squ` | `pi` — 根拠: `100masu.py:51-56`

実行例（実機で成功を確認済み）:
```bash
python3 100masu.py A4 ope -a 1 -b 1 --out-file result.pdf
```
→ `result.pdf` と `result_read.pdf`（解答用、`--merge` 未指定時）を生成（根拠: `100masu.py:730-762`、実行時の `export PDF` 出力を確認）。

**注意（実機確認済みの既知バグ）**: `command` に `ope` 以外（`com`, `100`, `99`, `aBc`, `squ`, `pi`）を指定すると、`100masu.py:158` の `NameError: name 'ini' is not defined` で必ず失敗する。README の Usage 例（`python 100masu.py B5 100` 等、`README.md:64,70`）はこの状態では実行できない。詳細は [[specification_summary]]。

### 主なオプション（`100masu.py:57-149`）

| オプション | 意味 |
|---|---|
| `-a/--a-value`, `-b/--b-value` | 項の桁数（1〜5）を指定し `--a-min/--a-max` 等を自動設定 |
| `--a-min/--a-max`, `--b-min/--b-max` | 項の値の範囲を直接指定 |
| `-o/--operator` | `add`/`sub`/`mul`/`div`/`mix`（複数指定可） |
| `--descend`, `--reverse`, `--shuffle` | 九九・固定フォーマット系の出題順制御 |
| `--intermediate` | 掛け算に4桁変換の中間式を表示 |
| `-r/--rows`, `-c/--columns` | 1ページあたりの行数・列数 |
| `-ww/--with-bottom-answer` | ページ下部にまとめて解答を表示 |
| `-p/--page` | 出力ページ数 |
| `-m/--merge` | 解答を別ファイルにせず本文に含める |
| `--csv` | 生成データを CSV でも出力 |
| `--out-file` | 出力ファイル名（デフォルト `result.pdf`） |
| `--debug` | フレーム境界線を表示、CSVも出力 |

## バッチ実行

```bash
./factory.sh
```
根拠: `factory.sh:265-269` が `_init` → `_args_check` → `_verbose` → `_main` の順で実行し、`_main` (`factory.sh:56-77`) が `dist/` 配下のディレクトリを作った上で `_basic` を呼ぶ（`_kuku` 系はコメントアウトされており現状は実行されない、`factory.sh:72-76`)。

前提: `100masu.py` が実行可能 (`chmod +x`) かつ `PATH` 上で解決できること（`factory.sh` 内で `100masu.py` を素のコマンド名として呼んでいるため、`factory.sh:90` 等）。カレントディレクトリを `100masu.py` が置かれているディレクトリにするか、`PATH` に追加する必要があると推測されるが、`factory.sh` 内にその設定はない（未確認: 実際にどう運用しているかは記述なし）。

**注意**: `_basic` 内の `ope`, `aBc` 以外の呼び出し（`squ` を含む一部行）は上記の `ini.intermediate` バグの影響を受ける可能性がある。`factory.sh:107` の `squ` 呼び出しは現状失敗すると推測される（未確認: 実際に `factory.sh` を実行して確認する必要あり。今回のドキュメント生成では `factory.sh` 自体は実行していない）。

## ビルド

PDF/CSV 生成そのものがビルド成果物であり、コンパイルやトランスパイルの工程は存在しない。

## 未確認事項

- `factory.sh` の実運用時のカレントディレクトリ/`PATH` 設定: 記述なし。実行して確認する必要がある。
- `dist/` ディレクトリの生成物の配布方法（Web公開、印刷業者への納品等）: 記述なし。
