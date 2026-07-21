# Project Overview

## 目的

計算ドリル（四則演算・補数・100マス計算・九九・aBc変換・平方数・円周率倍）の練習用 PDF を、パラメータ指定で生成する Python 製 CLI ツール。設計意図は [[concept]] を参照。

## 技術スタック

根拠の優先順位（CI定義 > パッケージ定義 > 設定ファイル）に従って確認したが、本リポジトリには CI 定義もパッケージ定義（`requirements.txt` 等）も存在しない。以下は実装コードと README から直接確認した事実。

| 項目 | 内容 | 根拠 |
|---|---|---|
| 言語 | Python 3 | `100masu.py:1` shebang `#!/usr/bin/env python`、`README.md:15` "Python 3" |
| 実行時に確認した Python | 3.12.3 (`python3 --version`) | ローカル環境観測。リポジトリが特定バージョンを要求する記述はなし（未確認） |
| 主要ライブラリ | ReportLab | `100masu.py:12-18` の import、`README.md:16,35` |
| 標準ライブラリ利用 | `argparse`, `random`, `csv`, `os`, `sys` | `100masu.py:4-8` |
| シェル | Bash (`set -Ceu`) | `factory.sh:1,3` |
| パッケージマネージャ | pip（バージョン固定なし） | `README.md:35` `pip install reportlab` のみ。lock file 不在を確認済み |

## 主要機能（実装から確認）

`100masu.py` の `command` 引数（`100masu.py:51-56`）で切り替わる7種類の生成モード:

1. `ope` — 四則演算（加減乗除、`--operator` で `add`/`sub`/`mul`/`div`/`mix` を指定、`--intermediate` で4桁変換法の中間式付き掛け算を出力）。実装: `get_operation_data()` (`100masu.py:222-339`)。**唯一、実行時エラーなく動作することを実機確認済み。**
2. `com` — 補数（目標値からの差を問う）。実装: `get_complement_data()` (`100masu.py:342-374`)。
3. `100` — 100マス計算（10×10の足し算マス）。実装: `main()` 内の `ini.command == '100'` 分岐 (`100masu.py:1114-1193`)。
4. `99` — 九九。実装: `get_fixed_format_data()` (`100masu.py:377-442`, mode=='99')。
5. `aBc` — 4桁の数値を3桁に変換する暗算トレーニング（`memo.md` の STEP1/STEP2 に対応）。実装: `get_aBc_data()` (`100masu.py:445-484`)。
6. `squ` — 平方数。実装: `get_fixed_format_data()` (mode=='squ')。
7. `pi` — 円周率(3.14)倍。実装: `get_fixed_format_data()` (mode=='pi')。

**既知の欠陥（実機確認済み）**: `com`/`100`/`99`/`aBc`/`squ`/`pi` の6モードは、現在の HEAD (`ac4167f`) で `python3 100masu.py A4 <command> ...` を実行すると `100masu.py:158` の `NameError: name 'ini' is not defined` で必ず失敗する。詳細は [[specification_summary]]。

## 補助機能

- 用紙サイズ4種（A3/A4/A4横/B5）とそれぞれの仮想ページ分割（A3=4分割、A4横=2分割）: `100masu.py:702-796`。
- 解答を別紙にする/同じ紙に赤字で載せる/末尾にまとめて載せるの切り替え（`--merge`, `--with-bottom-answer`）: `100masu.py:749-762, 853-854, 1103-1106`。
- 生成データを CSV としても出力するオプション (`--csv`, `--debug`): `100masu.py:1047-1056, 1204-1209`。
- `factory.sh` によるバッチ生成（用紙サイズ・分量違いの複数 PDF を `dist/` 配下にまとめて生成）: `factory.sh:56-156`。

## エントリポイント

- `100masu.py`（実行可能、`chmod +x` 済み） — 単体実行: `python3 100masu.py <paper_size> <command> [options]`
- `factory.sh`（実行可能） — バッチ実行。内部で `100masu.py` をコマンドとして直接呼び出しており（`factory.sh:90` など）、`100masu.py` が実行可能かつ `PATH` 上にあることを前提にしている（未確認: 実行時に `PATH` 解決に失敗する可能性があるが、`factory.sh` 内に `PATH` 設定や `./100masu.py` 呼び出しの記述はない）。

## 未確認事項

- 自動テストの有無: リポジトリ内に test ファイルは存在しない（`find` で確認済み）。品質保証プロセスは不明。
- CI/CD: `.github/workflows` 等の定義は存在しない。
