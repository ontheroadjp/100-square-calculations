# CLAUDE.md

AI 運用の single source of truth。`AGENTS.md` はこのファイルへの symlink。

## プロジェクト概要

計算ドリル PDF 生成ツール群。CLI(`backend/nuts_calc.py`、Python + ReportLab)と、共通の Flask バックエンド(`backend/app.py`)を利用する2つの独立した Web UI フロントエンド(`frontend/spa`: React/Vite、`frontend/web`: HTML/CSS(Sass)/JS のみの軽量な日本語専用静的サイト)がある。issue #88 でリポジトリ構成を `backend/` + `frontend/{spa,web}` に再編し、CLI・Flask・テストを `backend/` に集約した。独立プロトタイプ `nuts_calc_tex.py` は7つの互換コマンドとLaTeX専用の分数・混合・比較・数論・変換系を合わせた計20コマンドを実装し、`NUTS_CALC_RENDERER=latex` で選択する。`ope --result-max` は全式形式の最終結果を上限制約でき、2年生Webメニューの発展足し算では答えを1,000以下にするため利用する。

**解消済みの既知の欠陥**: `frontend/spa/package.json` に `i18next`/`react-i18next`/`i18next-browser-languagedetector`/`i18next-http-backend` が不足し `npm run build` が失敗していた問題は解消済み(2026-08-12 実機再確認、`npm install && npm run build` 成功)。

**解消済みバグ**: 旧 `100masu.py:158` の `ini.intermediate` 未定義参照バグ(`ope` 以外の全コマンドが `NameError` で失敗)は、`nuts_calc.py` への移行時に `args.intermediate` へ修正済み。7コマンドすべての正常動作を実機確認済み。

**既知の未修正事項**: `backend/tests/test_nuts_calc_init.py` に9件の失敗するテストがある。`nuts_calc.py` の一部バリデーションが `exit()` から `exit(1)` に修正された(issue #37)後、テスト側の期待値が更新されないまま残っている stale なテストで、実装のバグではない。詳細: `docs/L2_development/test.md`。

## Custom / Command の使い分け（AI向けルール）

- task.md: ドキュメント変更を伴う実装に特化。issue 自動生成〜実装〜ドラフト PR 作成まで。docs/* は変更しない。
- patch.md: ドキュメント変更を伴わない軽微な修正に特化。issue/PR 不要。branch + commit → ユーザーが main へマージ。スコープが広がった場合は /task へエスカレーション。
- docs-sync.md: git diff を事実として docs を最小更新し、ドラフト PR を公開する。HARD STOP 時は /init-docs を要求して終了する。
- init-docs.md: repo の実態把握と設計ドキュメント再構築。重い初期化。docs-sync が説明不能になった時点でここに戻る。

## Local Tooling Environment

Observed by /init-docs (2026-08-18, issue #153 documentation-only mode):
- gh: 2.97.0
- gh auth: logged in to github.com as ontheroadjp (ssh protocol, scopes: admin:public_key, gist, read:org, repo)
- node: v24.16.0 (via mise: `~/.local/share/mise/installs/node/24/bin/node`)
- npm: 11.13.0 (same mise install)
- Node runtime manager hints: no repo-local `.nvmrc`/`.node-version`/`.tool-versions`/`mise.toml` found; node/npm resolved from the user's global mise install, not a repo-local pin. `frontend/spa` and `frontend/web` each have a real Node.js dependency (Vite build) — node/npm ARE required there, unlike the CLI/`factory.sh`/`nuts_calc_tex.py` (in `backend/`) which remain Python-only (the latter additionally requires `pdflatex`, not Node.js).
- `nuts_calc_tex.py`'s optional Japanese-capable `lualatex` engine adapter (`NUTS_CALC_TEX_ENGINE=lualatex`, issue #121) additionally requires: the `lualatex` binary (LuaHBTeX, present via the base TeX Live install), the `texlive-luatex` apt package (provides `luaotfload`, the font loader `fontspec` needs on LuaLaTeX; installed 2026-08-14 via `sudo apt install texlive-luatex`, 2 packages, self-contained on top of the already-installed `texlive-latex-extra`), and the `fonts-noto-cjk` apt package (provides `Noto Sans CJK JP`, already present on this machine). None of this is required for the default `pdflatex` engine or for `nuts_calc.py`/`backend/app.py`. upLaTeX/`luatexja` were evaluated and rejected for now: on Ubuntu both live inside `texlive-lang-japanese`, which pulls in `texlive-lang-cjk` (114 packages, including unrelated Chinese/Korean/Thai support) versus `texlive-luatex`'s 2; revisit only if paragraph-level Japanese typesetting (kinsoku shori/JFM spacing) is needed.

Notes:
- If `gh` operations fail with API schema or compatibility errors, check `gh --version` first. Prefer upgrading `gh` when possible; if upgrading is impossible, use an equivalent `gh api` REST call or GitHub Web UI for the affected operation.
- Before npm operations, run `node --version` and `npm --version` to confirm Node.js and npm are available in the current shell. This also initializes Node.js in lazy-loaded runtime manager environments such as nvm.
- Do not install or upgrade `gh`, Node.js, or npm automatically without explicit user confirmation.

## Python Environment

- All CLI/Flask code lives under `backend/` (moved there from the repo root and `web/backend/` in issue #88); run these commands with `backend/` as the working directory.
- No lock file, `requirements.txt`, or `pyproject.toml` exists. CLI dependency is `reportlab`; the web backend additionally needs `Flask`/`Flask-Cors`; the test suite needs `pytest`. Install via `pip install reportlab flask flask-cors pytest` (see `README.md`).
- Before running `nuts_calc.py`, confirm `python3 -c "import reportlab"` succeeds; if not, ask before installing.
- repo-local `venv/` has Python 3.12.3, ReportLab 5.0.0, Flask 3.1.3, Flask-Cors 6.0.5, and pytest 9.1.1. System `python3` did not resolve ReportLab/Flask during the 2026-08-07 observation; activate `venv/` or install only after user confirmation.
- `cd backend && python3 -m pytest` collects 586 tests as of 2026-08-18. Excluding `tests/test_nuts_calc_init.py`, 564 tests pass; that stale file has 9 known failures and 13 passes (577 passed, 9 failed when combined). `pdflatex`-dependent tests ran successfully; see `docs/L2_development/test.md`.
- `nuts_calc_tex.py` (experimental LaTeX prototype) additionally requires `pdflatex` on `PATH`; its `pdflatex`-dependent CLI tests auto-skip when it's absent. Its `vendor/texmf` lookup is resolved relative to its own file location (`backend/vendor/texmf`), so it required no code change when `backend/` was introduced in issue #88. Its optional `lualatex` engine adapter (see Local Tooling Environment above) has its own `lualatex`-gated tests (`backend/tests/test_nuts_calc_tex_lualatex_engine.py`, plus pure-Python adapter-selection tests in `test_nuts_calc_tex_engine_adapter.py` that need neither binary) that auto-skip the same way when `lualatex` is absent.

## Web Frontend Environments (`frontend/spa`, `frontend/web`)

Two independent frontends share the same `backend/app.py` Flask API (issue #88); neither depends on the other or on a shared internal package.

- `frontend/spa` (React SPA, English/Japanese via i18next): pure-function tests use Node's built-in runner directly and 17 passed on 2026-08-18. There is no `npm test` script. `npm run lint` has one known `no-irregular-whitespace` failure in a Japanese comment.
- `frontend/web` (lightweight static multi-page site — `index.html`/`catalog.html`/`preset.html` — Vite + Sass + KaTeX, Japanese only): `npm run build` succeeds (verified 2026-08-18, 3 HTML entries). Its two `node:test` files are run directly and 36 tests passed; no npm test/lint scripts are configured. Its grade→category→menu-item model diverged from `frontend/spa` in issue #98.
