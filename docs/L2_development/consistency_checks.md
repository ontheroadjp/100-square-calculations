# Consistency Checks

CI が存在しないため、整合性確認は手動実行に依存する。以下は `/init-docs` 再実行(2026-07-22、`dev` ブランチのマージ後)の Phase 4 で実施した検証内容と結果。

## 実施した検証

### 1. CLI 全コマンドの実行可否(実機検証)

- 検証方法: `pip install reportlab` 済みの venv で7種類の `command`(`ope`/`com`/`100`/`99`/`aBc`/`squ`/`pi`)すべてを実行。
- 結果: **全コマンド成功**。旧 `100masu.py:158` の `ini.intermediate` 未定義バグは `nuts_calc.py` では `args.intermediate` に修正されており(`git log` のコミット `d9fc0a3`/`5466cdb` 系列で `100masu.py` → `nuts_calc.py` へのリネームと整理が行われた)、再発は確認されなかった。

### 2. Web フロントエンドのビルド可否(実機検証)

- 検証方法: `web/frontend` で `npm install && npm run build` を実行。
- 結果: **失敗**。`src/i18n.js:1-4` が import する `i18next`, `react-i18next`(`src/App.jsx:2` からも import), `i18next-browser-languagedetector`, `i18next-http-backend` が `web/frontend/package.json` の `dependencies` に存在せず、`package-lock.json` にも該当パッケージのエントリがないことを `grep` で確認済み。`npm run build` はビルド開始直後に `Rollup failed to resolve import "i18next"` で失敗する。
- 対応: 実装修正(`package.json` への追加)は `/init-docs` のスコープ外のため実施していない。[[../L0_concept/policy]] と [[../L3_implementation/specification_summary]] に既知の欠陥として記録。

### 3. README/README_ja ⇄ 実装(パッケージング)

- 検証方法: `README.md:13-14`(および `README_ja.md:14`)の「pip 経由でインストールでき、reportlab の依存関係も処理される」という記述と、リポジトリ内のパッケージ定義ファイルの有無を突き合わせ。
- 結果: **不一致**。`setup.py`/`pyproject.toml`/`requirements.txt` のいずれも存在しない(`find` で確認済み。過去の `setup.py` はコミット `d9fc0a3` で削除されたことを `git log` で確認)。実際には `pip install reportlab flask flask-cors` のような個別インストールが必要。

### 4. `nuts_calc.py` ヘッダーコメント ⇄ 実ファイル名

- 検証方法: `nuts_calc.py:4-13` のヘッダーコメント内の "Script: 100masu.py" / "Usage: python 100masu.py ..." と実際のファイル名を突き合わせ。
- 結果: **不一致(軽微)**。リネーム時(コミット `d9fc0a3`)にヘッダーコメントが更新されておらず、旧ファイル名のまま。動作に影響はないが記述の取り残し。

### 5. `.gitignore` の `example_result.pdf` 除外例外

- 検証方法: `.gitignore:32-33` の `!example_result.pdf` という除外例外と、実際のファイル存在を突き合わせ。
- 結果: **不一致(軽微)**。`example_result.pdf` は `dev` ブランチのマージで削除済みのため、この例外行は現在は無効(対象が存在しない)。実害はない。

### 6. `docs/.ai/repo.profile.json` ⇄ docs

- `commands` に定義された各コマンドは本ドキュメント群(`operation_model.md`)で説明済み。
- `primary_docs` は `L1_project/repository_structure.md` と `L3_implementation/specification_summary.md` を指し、両ファイルの実在を確認済み。

### 7. CI 定義との整合性

- `.github/workflows` 等の CI 定義が存在しないため、この観点の検証は該当なし(N/A)。

## 未確認事項(分離)

- `web/backend`(Flask)を実際に起動しての結合テスト(フロントエンドのビルドが壊れているため未実施)。
- `factory.sh` を実際にフル実行した場合の `dist/` 配下の生成結果(今回は `nuts_calc.py` の直接実行のみ検証)。
- `web/backend/generated_pdfs/` のクリーンアップ運用の有無。
