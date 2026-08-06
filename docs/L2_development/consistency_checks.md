# Consistency Checks

CI が存在しないため、整合性確認は手動実行に依存する。以下は `/init-docs` 再実行(2026-08-06、issue #65)の Phase 4 で実施した検証内容と結果。

## 実施した検証

### 1. CLI 全コマンドの実行可否(実機検証)

- 検証方法: `pip install reportlab` 済みの環境で7種類の `command`(`ope`/`com`/`100`/`99`/`aBc`/`squ`/`pi`)すべてを実行(過去の検証結果を踏襲、`nuts_calc.py` の関連箇所に変更差分はない)。
- 結果: **全コマンド成功**(過去検証を再確認)。

### 2. Web フロントエンドのビルド可否(実機検証・再検証)

- 検証方法: `cd web/frontend && npm run build` を実行(`node_modules/` は既にインストール済みの状態で実行)。
- 結果: **成功**。`vite v7.1.5 building for production... ✓ 67 modules transformed... ✓ built in 1.12s`。`web/frontend/package.json` に `i18next`/`i18next-browser-languagedetector`/`i18next-http-backend`/`react-i18next` が存在することを確認済み(`grep -c '"i18next"' web/frontend/package-lock.json` も2件ヒット)。
- 過去の記録(2026-07-22、本ファイルの旧版)は「失敗」だったが、その後のコミット(`724f752` 等、`docs/L3_implementation/specification_summary.md` に記録)で解消済み。docs 側の記述更新漏れがあった箇所(`project_overview.md`/`operation_model.md`/`policy.md`/`CLAUDE.md`)を本 `/init-docs` 実行で修正した。

### 3. pytest テストスイートの実行可否(実機検証・新規)

- 検証方法: リポジトリルートで `python3 -m pytest -q` を実行。
- 結果: **222件を収集**。`tests/test_nuts_calc_init.py` は既知の9失敗・13成功。分数/backend単体22件と分数`pdflatex` CLI 2件は成功。既知ファイルを除く全件実行は最終サマリを取得できず未確認として [[test]] に分離した。
- 過去の `docs/.ai/repo.profile.json`(2026-07-22 時点)は `"tests": "No test files or test directory exist"` としていたが、これは誤り(`tests/` は少なくとも issue #4 のテスト追加以降存在する)。本 `/init-docs` 実行で修正した。

### 4. README/README_ja ⇄ 実装(パッケージング)

- 検証方法: `README.md:18`(および `README_ja.md`)の「`requirements.txt`/`pyproject.toml`/`setup.py` が存在しない」旨の注記と、リポジトリ内のパッケージ定義ファイルの有無を突き合わせ。
- 結果: **一致**。`setup.py`/`pyproject.toml`/`requirements.txt` のいずれも存在しない(`find` で確認済み)。README.md は既にこの点を明示的に注記済みで、過去に指摘されていた「pip 経由でインストールでき依存関係も処理される」という誤記(2026-07-22 時点)は解消されている。

### 5. `nuts_calc.py` ヘッダーコメント ⇄ 実ファイル名

- 検証方法: `nuts_calc.py:4-13` のヘッダーコメント内の "Script: 100masu.py" と実際のファイル名を突き合わせ。
- 結果: **不一致(軽微、継続)**。リネーム時(コミット `d9fc0a3`)にヘッダーコメントが更新されておらず、旧ファイル名のまま。動作に影響はないが記述の取り残し。

### 6. `.gitignore` の `example_result.pdf` 除外例外

- 検証方法: `.gitignore` 内の `!example_result.pdf` という除外例外と、実際のファイル存在を突き合わせ。
- 結果: **不一致(軽微、継続)**。`example_result.pdf` は `dev` ブランチのマージで削除済みのため、この例外行は現在は無効(対象が存在しない)。実害はない。

### 7. `docs/.ai/repo.profile.json` ⇄ docs

- `commands` に定義された各コマンド(`run_tests`/`run_cli_tex_prototype` を今回追加)は本ドキュメント群(`operation_model.md`)で説明済み。
- `entrypoints` に `nuts_calc_tex.py` を追加(実ファイルの存在、および `docs/L3_implementation/nuts_calc_tex.py.md` での文書化を確認済み)。
- `primary_docs` は `L1_project/repository_structure.md` と `L3_implementation/specification_summary.md` を指し、両ファイルの実在を確認済み。

### 8. CI 定義との整合性

- `.github/workflows` 等の CI 定義が存在しないため(`find .github -type f` で確認、ヒットなし)、この観点の検証は該当なし(N/A)。

### 9. `docs/L3_implementation/*.md` ⇄ 実装(サンプリング検証)

- `nuts_calc.py.md`/`nuts_calc_tex.py.md`/`web/backend/app.py.md`/`web/backend/renderers.py.md` は、HEAD の最新コミット(`f613008`、issue #43)までの変更履歴セクションが git log と一致していることを確認済み。これらのファイルは既に高い精度で最新化されていたため、本 `/init-docs` 実行では変更していない。
- 一方 `L1_project/*.md`・`L2_development/operation_model.md`・`L0_concept/policy.md`・`CLAUDE.md` は、上記2・3の検証で判明した通り古い情報(i18next 未解消、テスト不在)を含んでいたため、本 `/init-docs` 実行で修正した。`/docs-sync` が個々の PR 差分に対して最小更新を行う運用のため、変更されたファイルに直接対応しない L1/L2 サマリ文書や CLAUDE.md が同期対象から漏れていたと考えられる(推定、`docs-sync.md` の運用ルールからの推測であり断定はできない)。

## 未確認事項(分離)

- `web/backend`(Flask)を実際に起動しての結合テスト(`pytest` のモジュールレベル単体テストとは別に、実プロセスを起動してフロントエンドと繋いだ動作確認)は未実施。
- `factory.sh` を実際にフル実行した場合の `dist/` 配下の生成結果(今回は `nuts_calc.py` の直接実行のみ検証)。
- `web/backend/generated_pdfs/` のクリーンアップ運用の有無。
- `nuts_calc_tex.py` の実機コンパイル(`pdflatex` インストール環境での CLI 直接実行)は今回未実施(ユニットテストの成功と `docs/L3_implementation/nuts_calc_tex.py.md` の記録を根拠とした間接確認のみ)。
- README.md と README_ja.md の内容差分(`Architecture`/`Design Principles` セクションの有無)。[[../L1_project/repository_structure]] に記録済み。
