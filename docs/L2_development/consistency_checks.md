# Consistency Checks

CI が存在しないため、整合性確認は手動実行に依存する。以下は `/init-docs` の Phase 4 で実施した検証内容と結果。

## 実施した検証

### 1. README ⇄ 実装 (`100masu.py` の `argparse`)

- 検証方法: `README.md:41-70` に記載されたコマンド例と `100masu.py:51-56` の `choices` を突き合わせ。
- 結果: **不一致**。README は `operations`/`complements`/`100` を案内しているが、実装の `choices` は `ope`/`com`/`100`/`99`/`aBc`/`squ`/`pi`。README 記載のコマンドをそのまま実行すると `argparse` のエラーで失敗する（実機確認可能、本ドキュメント作業内では argparse のエラーメッセージ生成までは実行未実施。`choices` の文字列比較で不一致を確認済み）。
- 対応: [[policy]] に既知の乖離として記録。README 自体の修正は本コマンドのスコープ外（`/init-docs` は docs/README/CLAUDE.md の scaffold のみを担当し、実装や既存 README 本文の書き換えは行わない）。

### 2. `command` 引数の実行可否（実機検証）

- 検証方法: `pip install reportlab` 済みの venv で `python3 100masu.py A4 ope -a 1 -b 1 --out-file test.pdf` と `python3 100masu.py A4 100 --out-file test.pdf` 等を実行。
- 結果: `ope` は成功（PDF生成を確認）。`com`/`100` は `100masu.py:158` で `NameError: name 'ini' is not defined` により失敗。`99`/`aBc`/`squ`/`pi` も同じコード経路（`_init()` 内の同一 `if` 文）を通るため同様に失敗すると推定される（`ope` 以外はすべて `args.command == 'ope'` が False になり、`ini.intermediate` の評価に進むため）。
- 根拠となるコミット差分: `git show 39cdf62 -- 100masu.py` で、旧コード `if args.command == 'ope':` が `if args.command == 'ope' or ini.intermediate:` に変更されたことを確認済み。

### 3. `docs/.ai/repo.profile.json` ⇄ docs

- `commands.run`, `commands.batch_generate` は本ドキュメント群（`operation_model.md`）で説明済み。
- `doc_roots` は実際に生成した `docs/L0_concept`, `L1_project`, `L2_development`, `L3_implementation` と一致。
- `primary_docs` は `L1_project/repository_structure.md` と `L3_implementation/specification_summary.md` を指し、両ファイルの実在を確認済み。

### 4. CI 定義との整合性

- `.github/workflows` 等の CI 定義が存在しないため、この観点の検証は該当なし（N/A）。将来 CI が追加された場合はこのファイルと `docs/.ai/repo.profile.json` の `commands` を再検証すること。

## 未確認事項（分離）

- `README.md` のコマンド例が argparse 実行時に具体的にどのエラーメッセージ・終了コードになるかは未実行（`choices` の不一致から失敗することは確定しているが、エラーメッセージ文言は未確認）。確認するには `python3 100masu.py A4 operations` を実行する。
- `factory.sh` 経由での `squ`/`com`/`100` 等の呼び出しが実際に失敗するかは `factory.sh` 自体を実行していないため未確認。確認するには `./factory.sh` を実行し `dist/` 配下の生成結果を見る必要がある。
