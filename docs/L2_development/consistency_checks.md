# Consistency Checks

CI 定義が存在しないため、整合性はローカルで再現可能なコマンドと実装参照で保証する。以下は `/init-docs` 再実行(2026-08-07)の結果である。

## 実体に対する検証

| 観点 | 検証 | 結果・根拠 |
|---|---|---|
| ReportLab CLI | `nuts_calc.py` の7コマンドを1問ずつ repo-local `venv/` で実行 | 全て PDF と回答 PDF を生成して成功。コマンド定義は `nuts_calc.py:114-217` |
| LaTeX CLI | `nuts_calc_tex.py A4 frac ...` を `pdflatex` 付きで実行 | PDF と回答 PDF を生成して成功。compile は `nuts_calc_tex.py:633-646` |
| Python tests | `python3 -m pytest -q --ignore=tests/test_nuts_calc_init.py` | 297 passed。全体は319件、除外ファイルは既知どおり9 failed / 13 passed |
| Frontend tests | `node --test web/frontend/src/drillPresets.test.js web/frontend/src/verticalLayout.test.js` | 7 passed |
| Frontend build | `cd web/frontend && npm run build` | 成功、Vite 7.1.5、68 modules transformed |
| Frontend lint | `cd web/frontend && npm run lint` | 1失敗。`drillPresets.js:304` の全角空白を `no-irregular-whitespace` が拒否 |
| API | ルートと renderer 変換をソース/pytest で照合 | `POST /generate-pdf` と `GET /renderer-info` の2本(`web/backend/app.py:15-58`)。backend テストは上記297件に含まれ成功 |

## docs → 実体

- docs に記載したエントリポイント5件(`nuts_calc.py`, `nuts_calc_tex.py`, `factory.sh`, `web/backend/app.py`, `web/frontend/src/main.jsx`)の実在を確認した。`docs/.ai/repo.profile.json:entrypoints` と一致する。
- L1〜L3、README、CLAUDE.md に記載した主要パスは `rg` で抽出して実在を確認した。L0 は既存のため workflow 規定により更新・検証対象外とした。
- CLI、backend、frontend の主要コマンドはすべて `docs/.ai/repo.profile.json:commands` に登録し、[[operation_model]] または [[test]] で説明した。
- frontend の依存バージョンは `web/frontend/package-lock.json` から確認した。直接依存の解決値は React 19.1.1、Vite 7.1.5、i18next 26.3.6 等で、範囲指定は `package.json:12-32` にある。

## repo profile ↔ docs

- `doc_roots` の4ディレクトリはすべて実在する。
- `primary_docs.investigation` と `primary_docs.structure` はそれぞれ [[../L3_implementation/specification_summary]] と [[../L1_project/repository_structure]] を指し、両方実在する。
- `commands` の install/run/build/test/lint は [[operation_model]] と [[test]] に対応する。CI 由来のコマンドはないため、実装 (`package.json:scripts`, `pytest.ini`, CLI argparse) と実機結果を優先した。

## CI 整合性

`.github/workflows` および `.github` 配下のファイルは存在しない。したがって CI/CD doc は生成せず、CI と docs の矛盾は N/A と判定する。CI が追加された場合は最優先の事実として本手順を再検証する。

## 継続している不一致・未確認事項

- `nuts_calc.py:5,13` は旧名 `100masu.py` をコメントに残す。実害はないが実ファイル名と不一致。
- `.gitignore:33` は存在しない `example_result.pdf` の除外例外を残す。
- `npm run lint` は `web/frontend/src/drillPresets.js:304` のコメント内全角空白で失敗する。修正方針は未決定であり、対象ソースと `web/frontend/eslint.config.js` を確認する必要がある。
- `factory.sh` の全量実行、Flask と frontend の実プロセス結合、production deploy、`web/backend/generated_pdfs/` の清掃運用は未確認。確定には運用設定または E2E/deploy 定義が必要だが、現行リポジトリには存在しない。
- README.md と README_ja.md は `Architecture`/`Design Principles` の有無などで完全な対訳ではない。日本語版同期が意図的かはリポジトリから確定できない。

## 判定

生成・更新した docs、repo profile、実装、利用可能な実行コマンドは相互に説明可能である。既知 stale pytest と lint 失敗は成功扱いにせず明示的に分離したため、Phase 4 の整合性条件を満たす。
