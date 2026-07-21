# Specification Summary

API/DB は存在しないため、`docs/L3_implementation/api.md` と `database.md` は生成していない（本リポジトリは CLI → PDF/CSV 変換の単一プロセスであり、ネットワークインターフェースも永続化層もない。根拠: `100masu.py` に `socket`/`http.server`/`sqlite3` 等の import なし）。

## CLI 仕様（`100masu.py`）

### 引数

`100masu.py:37-150` の `argparse.ArgumentParser` 定義に基づく。位置引数2つ + オプション引数多数。詳細は [[operation_model]] の表を参照。

### 出力

| 条件 | 出力ファイル | 根拠 |
|---|---|---|
| 常時 | `<out-file>`（デフォルト `result.pdf`） | `100masu.py:730,735-748` |
| `--merge` 未指定時 | `<out-file の拡張子除去>_read.pdf`（解答用） | `100masu.py:731,749-762` |
| `--csv` または `--debug` 指定時 | `<out-file の拡張子除去>.csv` | `100masu.py:732,1204-1209` |

`rstrip('.pdf')` (`100masu.py:731-732`) は末尾の `pdf`/`.` 文字集合を1文字ずつ削るため、`out-file` の値によっては意図しない文字列になり得る（例: ファイル名が `ppdf.pdf` のように末尾が特定の文字集合で構成される場合）。通常の `result.pdf` では問題にならないが、`str.rstrip` は接尾辞除去ではなく文字集合除去である点に注意（`100masu.py:731-732` の実装をそのまま読んだ事実であり、実際に問題が起きるファイル名では未検証）。

## 既知の欠陥: `ini.intermediate` 未定義参照（実機確認済み・再現手順あり）

- 発生箇所: `100masu.py:158`
  ```python
  if args.command == 'ope' or ini.intermediate:
  ```
- 症状: `command` が `ope` 以外の場合、`ini` という名前は `_init()` 関数のどのスコープにも存在しないため `NameError: name 'ini' is not defined` が送出され、`_init()` の呼び出し元である `if __name__ == "__main__":` ブロック（`100masu.py:1217-1219`）まで伝播し、スタックトレースを出力してプロセスが異常終了する。
- 影響範囲: `command` の7種類のうち `ope` を除く6種類（`com`, `100`, `99`, `aBc`, `squ`, `pi`）すべてで発生する。`_init()` 内の分岐は `args.command` の値ごとに条件分岐しているが（`100masu.py:158,163-180`）、`ini.intermediate` の評価はこの1箇所の `if` 文にのみ現れ、`args.command != 'ope'` である限り必ず通過するため。
- 再現コマンド（実機で確認済み）:
  ```bash
  python3 100masu.py A4 com -a 100 --out-file /tmp/test_com.pdf
  python3 100masu.py A4 100 --out-file /tmp/test_100.pdf
  ```
  いずれも次のトレースで終了する:
  ```
  Traceback (most recent call last):
    File ".../100masu.py", line 1218, in <module>
      args = _init()
    File ".../100masu.py", line 158, in _init
      if args.command == 'ope' or ini.intermediate:
  NameError: name 'ini' is not defined. Did you mean: 'int'?
  ```
  一方 `python3 100masu.py A4 ope -a 1 -b 1 --out-file /tmp/test_ope.pdf` は成功し、`result.pdf`/`result_read.pdf` 相当のファイルが生成されることを確認済み。
- 混入経緯: `git show 39cdf62` の diff により、直前の実装では

  ```python
  if args.command == 'ope':
  ```

  だったものが、コミット `39cdf62 [NEW] --intermediate option`（このリポジトリの `master` HEAD `ac4167f` に含まれる直近の変更）で

  ```python
  if args.command == 'ope' or ini.intermediate:
  ```

  に変更され、コメントアウトされた案 `# args.command == 'ope' or args.command == 'mul-intermediate'` の代わりに採用されたことが原因と確認できる。恐らく `main(ini)` 内 (`100masu.py:678`) で使われている引数名 `ini` と、`_init()` 内のローカル変数 `args` を取り違えたことによる実装ミスと推測される（`_init()` 内では一貫して `args.xxx` が使われており、`ini.xxx` の参照はこの1箇所のみ）。
- 推測される修正（未実施・本ドキュメントのスコープ外）: `100masu.py:158` の `ini.intermediate` を `args.intermediate` に置き換えることで解消すると考えられるが、コード変更は `/init-docs` の作業範囲外のため実施していない。

## 未確認事項

- `--intermediate` オプション自体（`ope` コマンドで `-o mul` と組み合わせた場合の中間式表示、`100masu.py:303-310,981-984`）が意図通り動作するかは、上記バグとは独立した別の検証が必要（`ope` コマンド自体は実行できるため、`--intermediate` 単体の動作確認は本ドキュメント作業では未実施）。
