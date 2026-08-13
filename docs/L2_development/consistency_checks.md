# Consistency Checks

CI 定義が存在しないため、整合性はローカルで再現可能なコマンドと実装参照で保証する。以下は `/init-docs` documentation-only mode 再実行(2026-08-12、issue #88 のリポジトリ再編 [`backend/` + `frontend/{spa,web}`] 直後)の結果である。

## 実体に対する検証

| 観点 | 検証 | 結果・根拠 |
|---|---|---|
| ReportLab CLI | `cd backend && python3 nuts_calc.py A4 ope ...` を実行 | PDF を生成して成功。コマンド定義は `backend/nuts_calc.py` |
| Python tests | `cd backend && python3 -m pytest -q --ignore=tests/test_nuts_calc_init.py` | 398 passed。全体は420件、除外ファイルは既知どおり9 failed / 13 passed(除外せずフルスイートを実行すると411 passed, 9 failed) |
| Frontend(spa) tests | `node --test frontend/spa/src/drillPresets.test.js frontend/spa/src/drillCatalog.test.js frontend/spa/src/verticalLayout.test.js` | 17 passed |
| Frontend(spa) build | `cd frontend/spa && npm run build` | 成功 |
| Frontend(spa) lint | `cd frontend/spa && npm run lint` | 1失敗。`drillPresets.js:433` の全角空白を `no-irregular-whitespace` が拒否(既知、継続中) |
| Frontend(web) build | `cd frontend/web && npm run build` | 成功。`dist/index.html`/`catalog.html`/`preset.html` の3エントリを出力(`custom.html` は issue #97 で削除) |
| API | ルートと renderer 変換をソース/pytest で照合 | `POST /generate-pdf` と `GET /renderer-info` の2本。`carry_mode` を含む backend テストは上記398件に含まれ成功 |
| Web バックエンド実プロセス | `backend/app.py` を起動し `frontend/spa`・`frontend/web` の両方からブラウザで検証(issue #88) | ドリル検索・絞り込み・PDF生成/プレビュー/ダウンロード・カスタム生成フォームがいずれも正常動作。pytest による自動結合テストではなく手動確認 |

## docs → 実体

- docs に記載したエントリポイント7件(`backend/nuts_calc.py`, `backend/nuts_calc_tex.py`, `backend/factory.sh`, `backend/app.py`, `frontend/spa/src/main.jsx`, `frontend/web/{index,catalog,preset,custom}.html`)の実在を確認した。`docs/.ai/repo.profile.json:entrypoints` と一致する。
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

- `nuts_calc.py:5,13` は旧名 `100masu.py` をコメントに残す。実害はないが実ファイル名と不一致。
- `.gitignore:33` は存在しない `example_result.pdf` の除外例外を残す。
- `npm run lint`(`frontend/spa`)は `drillPresets.js:433` のコメント内全角空白で失敗する。修正方針は未決定であり、対象ソースと `frontend/spa/eslint.config.js` を確認する必要がある。
- `factory.sh` の全量実行、Flask と frontend の実プロセス結合の自動テスト化、production deploy、`backend/generated_pdfs/` の清掃運用は未確認。確定には運用設定または E2E/deploy 定義が必要だが、現行リポジトリには存在しない。
- README.md と README_ja.md は `Architecture`/`Design Principles` の有無などで完全な対訳ではない。日本語版同期が意図的かはリポジトリから確定できない。
- `frontend/web` に `frontend/spa` 相当の自動テストを追加するかどうかの方針は未確認。

## 判定

生成・更新した docs、repo profile、実装、利用可能な実行コマンドは相互に説明可能である。既知 stale pytest と lint 失敗は成功扱いにせず明示的に分離したため、Phase 4 の整合性条件を満たす。
