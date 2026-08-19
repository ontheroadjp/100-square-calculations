# Consistency Checks

CI 定義が存在しないため、整合性はローカルで再現可能なコマンドと実装参照で保証する。以下は `/init-docs` documentation-only mode 再実行(2026-08-20、issue #232 の `nuts_calc.py` 削除を受けた `/docs-sync` HARD STOP からの復旧)の結果である。

## 実体に対する検証

| 観点 | 検証 | 結果・根拠 |
|---|---|---|
| LaTeX CLI | `cd backend && python3 nuts_calc_tex.py A4 ope ...` を実行 | PDF を生成して成功。コマンド定義は `backend/nuts_calc_tex.py`。旧 ReportLab CLI(`nuts_calc.py`)は issue #232 で削除された |
| Python tests | `cd backend && python3 -m pytest -q` | 687 passed(旧 ReportLab CLI 専用テストの削除により、以前の既知 stale 9件は「修正」ではなく「対象ファイル削除」で解消) |
| Frontend(spa) tests | `node --test frontend/spa/src/drillPresets.test.js frontend/spa/src/drillCatalog.test.js frontend/spa/src/verticalLayout.test.js` | 17 passed |
| Frontend(spa) build | `cd frontend/spa && npm run build` | 成功 |
| Frontend(spa) lint | `cd frontend/spa && npm run lint` | 1失敗。`drillPresets.js:433` の全角空白を `no-irregular-whitespace` が拒否(既知、継続中) |
| Frontend(web) build | `cd frontend/web && npm run build` | 成功。`dist/index.html`/`catalog.html`/`preset.html` の3エントリを出力(`custom.html` は issue #97 で削除) |
| Frontend(web) tests | `node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js` | 45 passed |
| API | ルートと renderer 変換をソース/pytest で照合 | `POST /generate-pdf`・`POST /generate-problems`(issue #138)・`GET /renderer-info` の3本。`result_max` を含む backend テストは上記687件に含まれ成功 |
| Web バックエンド実プロセス | `backend/app.py` を起動し `frontend/spa`・`frontend/web` の両方からブラウザで検証(issue #88)。`frontend/web` は issue #99 で学年選択(トップ)→カテゴリ別ドリル一覧(カタログ)の2画面に再構築済み(検索・絞り込みUI・カスタム生成フォームはいずれも issue #97/#99 で撤去済み) | 学年選択→カテゴリ別ドリル一覧→PDF生成/プレビュー/ダウンロードがいずれも正常動作。pytest による自動結合テストではなく手動確認 |

## docs → 実体

- docs に記載したエントリポイント7件(`backend/nuts_calc_tex.py`, `backend/factory.sh`, `backend/app.py`, `frontend/spa/src/main.jsx`, `frontend/web/{index,catalog,preset}.html`)の実在を確認した。旧 `backend/nuts_calc.py` は issue #232 で削除されたため対象外。`custom.html` は issue #97 で削除済みのため対象外(`docs/.ai/repo.profile.json:entrypoints` と一致)。
- L1〜L3、README、CLAUDE.md に記載した主要パスは `rg` で抽出して実在を確認した。L0 は既存のため workflow 規定により更新・検証対象外とした。
- CLI、backend、frontend(spa/web 両方)の主要コマンドはすべて `docs/.ai/repo.profile.json:commands` に登録し、[[operation_model]] または [[test]] で説明した。
- `frontend/spa` の依存バージョンは `frontend/spa/package-lock.json` から確認した(React 19.1.1、Vite 7.1.5、i18next 26.3.6 等、issue #88 前と変化なし)。`frontend/web` は `vite`/`sass` の2つのみを devDependencies に持つことを `frontend/web/package.json` で確認した。

## repo profile ↔ docs

- `doc_roots` の4ディレクトリはすべて実在する。
- `primary_docs.investigation` と `primary_docs.structure` はそれぞれ [[../L3_implementation/specification_summary]] と [[../L1_project/repository_structure]] を指し、両方実在する。
- `commands` の install/run/build/test/lint は [[operation_model]] と [[test]] に対応する。CI 由来のコマンドはないため、実装(`package.json:scripts`, `pytest.ini`, CLI argparse)と実機結果を優先した。issue #88 の移動に伴い、`commands` 内のパスをすべて `backend/`・`frontend/spa/`・`frontend/web/` 基準に更新した。

## CI 整合性

`.github/workflows` および `.github` 配下のファイルは存在しない。したがって CI/CD doc は生成せず、CI と docs の矛盾は N/A と判定する。CI が追加された場合は最優先の事実として本手順を再検証する。

## 継続している不一致・未確認事項

- `.gitignore:33` は存在しない `example_result.pdf` の除外例外を残す。
- `npm run lint`(`frontend/spa`)は `drillPresets.js:433` のコメント内全角空白で失敗する。修正方針は未決定であり、対象ソースと `frontend/spa/eslint.config.js` を確認する必要がある。
- `factory.sh` の全量実行、Flask と frontend の実プロセス結合の自動テスト化、production deploy、`backend/generated_pdfs/` の清掃運用は未確認。確定には運用設定または E2E/deploy 定義が必要だが、現行リポジトリには存在しない。
- README.md と README_ja.md は `Architecture`/`Design Principles` の有無などで完全な対訳ではない。日本語版同期が意図的かはリポジトリから確定できない。
- frontendのブラウザDOM/E2Eテスト方針は未確認。現行 `node:test` は純粋関数のみを対象とする。

## 判定

生成・更新した docs、repo profile、実装、利用可能な実行コマンドは相互に説明可能である。既知 stale pytest と lint 失敗は成功扱いにせず明示的に分離したため、Phase 4 の整合性条件を満たす。
