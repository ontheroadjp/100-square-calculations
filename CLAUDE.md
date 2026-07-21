# CLAUDE.md

AI 運用の single source of truth。`AGENTS.md` はこのファイルへの symlink。

## プロジェクト概要

計算ドリル PDF 生成ツール群。CLI(`nuts_calc.py`、Python + ReportLab、旧名 `100masu.py`)と、それをラップする Web UI(`web/backend` Flask + `web/frontend` React/Vite)の2経路がある。詳細は `docs/L0_concept/`, `docs/L1_project/`, `docs/L2_development/`, `docs/L3_implementation/` を参照。`docs/.ai/repo.profile.json` に主要コマンドと primary_docs へのポインタがある。

**既知の欠陥(実機確認済み・未修正)**: `web/frontend/package.json` に `i18next`/`react-i18next`/`i18next-browser-languagedetector`/`i18next-http-backend` が不足しており、`npm run build` が `Rollup failed to resolve import "i18next"` で失敗する。詳細: `docs/L3_implementation/specification_summary.md`。

**解消済みバグ**: 旧 `100masu.py:158` の `ini.intermediate` 未定義参照バグ(`ope` 以外の全コマンドが `NameError` で失敗)は、`nuts_calc.py` への移行時に `args.intermediate` へ修正済み。7コマンドすべての正常動作を実機確認済み。

## Custom / Command の使い分け（AI向けルール）

- task.md: ドキュメント変更を伴う実装に特化。issue 自動生成〜実装〜ドラフト PR 作成まで。docs/* は変更しない。
- patch.md: ドキュメント変更を伴わない軽微な修正に特化。issue/PR 不要。branch + commit → ユーザーが main へマージ。スコープが広がった場合は /task へエスカレーション。
- docs-sync.md: git diff を事実として docs を最小更新し、ドラフト PR を公開する。HARD STOP 時は /init-docs を要求して終了する。
- init-docs.md: repo の実態把握と設計ドキュメント再構築。重い初期化。docs-sync が説明不能になった時点でここに戻る。

## Local Tooling Environment

Observed by /init-docs (2026-07-22, re-run after the `dev` merge):
- gh: 2.96.0
- gh auth: logged in to github.com as ontheroadjp (ssh protocol, scopes: admin:public_key, gist, read:org, repo)
- node: v24.16.0 (via mise: `~/.local/share/mise/installs/node/24/bin/node`)
- npm: 11.13.0 (same mise install)
- Node runtime manager hints: no repo-local `.nvmrc`/`.node-version`/`.tool-versions`/`mise.toml` found; node/npm resolved from the user's global mise install, not a repo-local pin. Since the `dev` merge, `web/frontend` now has a real Node.js dependency (React/Vite build) — node/npm ARE required there, unlike the CLI/`factory.sh` which remain Python-only.

Notes:
- If `gh` operations fail with API schema or compatibility errors, check `gh --version` first. Prefer upgrading `gh` when possible; if upgrading is impossible, use an equivalent `gh api` REST call or GitHub Web UI for the affected operation.
- Before npm operations, run `node --version` and `npm --version` to confirm Node.js and npm are available in the current shell. This also initializes Node.js in lazy-loaded runtime manager environments such as nvm.
- Do not install or upgrade `gh`, Node.js, or npm automatically without explicit user confirmation.

## Python Environment

- No lock file, `requirements.txt`, or `pyproject.toml` exists. Only dependency is `reportlab`, installed via `pip install reportlab` (see `README.md`).
- Before running `100masu.py`, confirm `python3 -c "import reportlab"` succeeds; if not, ask before installing.
