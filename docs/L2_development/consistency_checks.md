# Consistency Checks

CI 定義が存在しないため、整合性はローカルで再現可能なコマンドと実装参照で保証する。以下は standalone `/init-docs` 再実行(2026-09-02)の結果である。

## 実体に対する検証

| 観点 | 検証 | 結果・根拠 |
|---|---|---|
| LaTeX CLI | `cd backend && python3 nuts_calc_tex.py A4 ope ...` を実行 | PDF を生成して成功。コマンド定義は `backend/nuts_calc_tex.py`。旧 ReportLab CLI(`nuts_calc.py`)は issue #232 で削除された |
| Python tests | `cd backend && python3 -m pytest -q` | 1107 passed in 78.49s(`backend/pytest.ini:4` の `-n auto` による並列実行) |
| Frontend(web) build | `cd frontend/web && npm run build` | 成功。`dist/index.html`/`catalog.html`/`preset.html` の3エントリを出力(`custom.html` は issue #97 で削除) |
| Frontend(web) tests | `node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js frontend/web/vite.config.test.js` | 72 passed |
| API | ルートと renderer 変換をソース/pytest で照合 | `POST /generate-pdf`・`POST /generate-problems`・`GET /renderer-info` の3本。唯一の内部 PDF 経路の全20コマンドと `100` 専用 JSON envelope を含む backend テストは上記1107件に含まれ成功 |
| Web バックエンド実プロセス | `backend/app.py` を起動し `frontend/web` からブラウザで検証(issue #88 時点では `frontend/spa` も併せて検証していたが、`frontend/spa` 自体が issue #233 で削除された)。`frontend/web` は issue #99 で学年選択(トップ)→カテゴリ別ドリル一覧(カタログ)の2画面に再構築済み(検索・絞り込みUI・カスタム生成フォームはいずれも issue #97/#99 で撤去済み) | 学年選択→カテゴリ別ドリル一覧→PDF生成/プレビュー/ダウンロードがいずれも正常動作。pytest による自動結合テストではなく手動確認 |

**(削除済み、issue #233)** この2026-08-20時点の検証では `frontend/spa` も併存しており、`node --test`(3ファイル)17 passed・`npm run build` 成功・`npm run lint` は `drillPresets.js:433` の全角空白を `no-irregular-whitespace` が拒否し1失敗、という結果だった。`frontend/spa` 自体が issue #233 で削除されたため、これらの検証項目自体が対象外になった。

## docs → 実体

- docs に記載したエントリポイント6件(`backend/nuts_calc_tex.py`, `backend/factory.sh`, `backend/app.py`, `frontend/web/{index,catalog,preset}.html`)の実在を確認した。旧 `backend/nuts_calc.py` は issue #232 で削除されたため対象外。`custom.html` は issue #97 で削除済みのため対象外(`docs/.ai/repo.profile.json:entrypoints` と一致)。7件目だった `frontend/spa/src/main.jsx` は issue #233 の `frontend/spa` 削除に伴い対象から外れた。
- L1〜L3、README、CLAUDE.md に記載した主要パスは `rg` で抽出して実在を確認した。L0 は既存のため workflow 規定により更新・検証対象外とした。
- CLI、backend、frontend(web)の主要コマンドはすべて `docs/.ai/repo.profile.json:commands` に登録し、[[operation_model]] または [[test]] で説明した。
- `frontend/web` は本番依存に KaTeX、devDependencies に Vite/Sass を持つ。lock file の実解決値は KaTeX 0.16.47、Vite 8.2.1、Sass 1.102.0(`frontend/web/package-lock.json:698,1110,1158`)。

## repo profile ↔ docs

- `doc_roots` の4ディレクトリはすべて実在する。
- `primary_docs.investigation` と `primary_docs.structure` はそれぞれ [[../L3_implementation/specification_summary]] と [[../L1_project/repository_structure]] を指し、両方実在する。
- `commands` の install/run/build/test/lint は [[operation_model]] と [[test]] に対応する。CI 由来のコマンドはないため、実装(`package.json:scripts`, `pytest.ini`, CLI argparse)と実機結果を優先した。issue #88 の移動に伴い、`commands` 内のパスをすべて `backend/`・`frontend/web/` 基準に更新した(`frontend/spa/` 基準のコマンドは issue #233 の削除に伴い repo profile から除去済み)。

## CI 整合性

`.github/workflows` および `.github` 配下のファイルは存在しない。したがって CI/CD doc は生成せず、CI と docs の矛盾は N/A と判定する。CI が追加された場合は最優先の事実として本手順を再検証する。

## 継続している不一致・未確認事項

- `.gitignore:33` は存在しない `example_result.pdf` の除外例外を残す。
- 既存 L0(`docs/L0_concept/{concept,policy}.md`)には、削除済みの `nuts_calc.py`・`web/{backend,frontend}`・React SPA・ReportLab を現行構成として扱う記述が残る。ただし `/init-docs` の再実行では既存 L0 を検証・更新しないという保護ルールのため、今回も変更対象外とした。L0 の訂正は `/docs-sync` が候補を `docs/.ai/l0_candidates.md` に記録した後、ユーザー承認付き `/concept-maker` だけが行える。
- `factory.sh` の全量実行、Flask と frontend の実プロセス結合の自動テスト化、production deploy、`backend/generated_pdfs/` の清掃運用は未確認。確定には運用設定または E2E/deploy 定義が必要だが、現行リポジトリには存在しない。
- README.md と README_ja.md は `Architecture`/`Design Principles` の有無などで完全な対訳ではない。日本語版同期が意図的かはリポジトリから確定できない。
- frontendのブラウザDOM/E2Eテスト方針は未確認。現行 `node:test` は純粋関数と Vite 設定のみを対象とする。

## 判定

今回生成・更新対象とした L1〜L3 docs、repo profile、README、実装、利用可能な実行コマンドは相互に説明可能である。既存 L0 は保護ルールにより検証対象外として明示的に分離したため、Phase 4 の整合性条件を満たす。
