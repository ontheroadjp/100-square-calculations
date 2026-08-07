# CLAUDE.md

AI 運用の single source of truth。`AGENTS.md` はこのファイルへの symlink。

## プロジェクト概要

計算ドリル PDF 生成ツール群。CLI(`nuts_calc.py`、Python + ReportLab)とWeb UI(`web/backend` Flask + `web/frontend` React/Vite)がある。独立プロトタイプ `nuts_calc_tex.py` は7つの互換コマンドとLaTeX専用 `frac` を実装し、`NUTS_CALC_RENDERER=latex` で選択する。分数カードと4〜6年生の中学受験準備27プリセットはこの場合だけ表示され、学年配置の一次資料は `docs/reference/` に保存する。

**解消済みの既知の欠陥**: `web/frontend/package.json` に `i18next`/`react-i18next`/`i18next-browser-languagedetector`/`i18next-http-backend` が不足し `npm run build` が失敗していた問題は解消済み(2026-08-05 実機再確認、`npm install && npm run build` 成功)。

**解消済みバグ**: 旧 `100masu.py:158` の `ini.intermediate` 未定義参照バグ(`ope` 以外の全コマンドが `NameError` で失敗)は、`nuts_calc.py` への移行時に `args.intermediate` へ修正済み。7コマンドすべての正常動作を実機確認済み。

**既知の未修正事項**: `tests/test_nuts_calc_init.py` に9件の失敗するテストがある。`nuts_calc.py` の一部バリデーションが `exit()` から `exit(1)` に修正された(issue #37)後、テスト側の期待値が更新されないまま残っている stale なテストで、実装のバグではない。詳細: `docs/L2_development/test.md`。

## Custom / Command の使い分け（AI向けルール）

- task.md: ドキュメント変更を伴う実装に特化。issue 自動生成〜実装〜ドラフト PR 作成まで。docs/* は変更しない。
- patch.md: ドキュメント変更を伴わない軽微な修正に特化。issue/PR 不要。branch + commit → ユーザーが main へマージ。スコープが広がった場合は /task へエスカレーション。
- docs-sync.md: git diff を事実として docs を最小更新し、ドラフト PR を公開する。HARD STOP 時は /init-docs を要求して終了する。
- init-docs.md: repo の実態把握と設計ドキュメント再構築。重い初期化。docs-sync が説明不能になった時点でここに戻る。

## Local Tooling Environment

Observed by /init-docs (2026-08-07):
- gh: 2.97.0
- gh auth: logged in to github.com as ontheroadjp (ssh protocol, scopes: admin:public_key, gist, read:org, repo)
- node: v24.16.0 (via mise: `~/.local/share/mise/installs/node/24/bin/node`)
- npm: 11.13.0 (same mise install)
- Node runtime manager hints: no repo-local `.nvmrc`/`.node-version`/`.tool-versions`/`mise.toml` found; node/npm resolved from the user's global mise install, not a repo-local pin. `web/frontend` has a real Node.js dependency (React/Vite build) — node/npm ARE required there, unlike the CLI/`factory.sh`/`nuts_calc_tex.py` which remain Python-only (the latter additionally requires `pdflatex`, not Node.js).

Notes:
- If `gh` operations fail with API schema or compatibility errors, check `gh --version` first. Prefer upgrading `gh` when possible; if upgrading is impossible, use an equivalent `gh api` REST call or GitHub Web UI for the affected operation.
- Before npm operations, run `node --version` and `npm --version` to confirm Node.js and npm are available in the current shell. This also initializes Node.js in lazy-loaded runtime manager environments such as nvm.
- Do not install or upgrade `gh`, Node.js, or npm automatically without explicit user confirmation.

## Python Environment

- No lock file, `requirements.txt`, or `pyproject.toml` exists. CLI dependency is `reportlab`; the web backend additionally needs `Flask`/`Flask-Cors`; the test suite needs `pytest`. Install via `pip install reportlab flask flask-cors pytest` (see `README.md`).
- Before running `nuts_calc.py`, confirm `python3 -c "import reportlab"` succeeds; if not, ask before installing.
- repo-local `venv/` has Python 3.12.3, ReportLab 5.0.0, Flask 3.1.3, Flask-Cors 6.0.5, and pytest 9.1.1. System `python3` did not resolve ReportLab/Flask during the 2026-08-07 observation; activate `venv/` or install only after user confirmation.
- `python3 -m pytest` collects 319 tests as of 2026-08-07. Excluding `tests/test_nuts_calc_init.py`, 297 tests pass; that stale file has 9 known failures and 13 passes. `pdflatex`-dependent tests ran successfully; see `docs/L2_development/test.md`.
- `nuts_calc_tex.py` (experimental LaTeX prototype) additionally requires `pdflatex` on `PATH`; its `pdflatex`-dependent CLI tests auto-skip when it's absent.

## Web Frontend Environment (`web/frontend`)

- `web/frontend/package.json` includes the `i18next` family of packages; `npm run build` succeeds (re-verified 2026-08-07). The previously-tracked missing-dependency defect is resolved.
- Frontend pure-function tests use Node's built-in runner directly: `node --test web/frontend/src/drillPresets.test.js web/frontend/src/verticalLayout.test.js` (7 passed on 2026-08-07). There is no `npm test` script.
- `npm run lint` currently fails once at `web/frontend/src/drillPresets.js:304` because `no-irregular-whitespace` rejects a full-width space in a Japanese comment.
