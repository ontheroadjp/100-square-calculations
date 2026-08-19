# CLAUDE.md

**チャットはすべて日本語で行うこと**

AI 運用の single source of truth。`AGENTS.md` はこのファイルへの symlink。

## プロジェクト概要

計算ドリル PDF 生成ツール群。CLI(`backend/nuts_calc_tex.py`、Python + LaTeX)と、共通の Flask バックエンド(`backend/app.py`)を利用する Web UI フロントエンド `frontend/web`(HTML/CSS(Sass)/JS のみの軽量な日本語専用静的サイト)がある。issue #88 でリポジトリ構成を `backend/` + `frontend/{spa,web}` に再編し、CLI・Flask・テストを `backend/` に集約した(当初は `frontend/spa` という React/Vite 製のもう1つのフロントエンドも存在したが、issue #233 で削除され `frontend/web` が唯一の Web UI フロントエンドになった)。旧 ReportLab CLI `nuts_calc.py` は issue #232 で削除され、`nuts_calc_tex.py`(7つの互換コマンドとLaTeX専用の分数・混合・比較・数論・変換系を合わせた計20コマンドを実装)が唯一の CLI になった(`NUTS_CALC_RENDERER=latex` が既定かつ唯一到達可能。切り替えの仕組み自体は将来の別レンダラー追加に備えて維持)。`ope --result-max` は全式形式の最終結果を上限制約でき、2年生Webメニューの発展足し算では答えを1,000以下にするため利用する。

**解消済みの既知の欠陥**: `frontend/spa/package.json` に `i18next`/`react-i18next`/`i18next-browser-languagedetector`/`i18next-http-backend` が不足し `npm run build` が失敗していた問題は解消済み(2026-08-12 実機再確認、`npm install && npm run build` 成功)。`frontend/spa` 自体は issue #233 で削除済み(履歴上の事実)。

**解消済みバグ**: 旧 `100masu.py:158` の `ini.intermediate` 未定義参照バグ(`ope` 以外の全コマンドが `NameError` で失敗)は、`nuts_calc.py`(旧 ReportLab CLI、issue #232 で削除)への移行時に `args.intermediate` へ修正済み(履歴上の事実)。

**解消済み(issue #232)**: `backend/tests/test_nuts_calc_init.py` の9件の既知 stale 失敗(`nuts_calc.py` の一部バリデーションが `exit()` から `exit(1)` に修正された(issue #37)後、テスト側の期待値が更新されないまま残っていたもの)は、`nuts_calc.py` 本体とともにこのテストファイル自体が削除されたことで解消した(修正ではなく削除による解消)。詳細: `docs/L2_development/test.md`。

## Custom / Command の使い分け（AI向けルール）

- task.md: ドキュメント変更を伴う実装に特化。issue 自動生成〜実装〜ドラフト PR 作成まで。docs/* は変更しない。
- patch.md: ドキュメント変更を伴わない軽微な修正に特化。issue/PR 不要。branch + commit → ユーザーが main へマージ。スコープが広がった場合は /task へエスカレーション。
- docs-sync.md: git diff を事実として docs を最小更新し、ドラフト PR を公開する。HARD STOP 時は /init-docs を要求して終了する。
- init-docs.md: repo の実態把握と設計ドキュメント再構築。重い初期化。docs-sync が説明不能になった時点でここに戻る。

## Local Tooling Environment

Observed by /init-docs (2026-08-20, documentation-only mode via /docs-sync HARD STOP recovery for issue #232; versions unchanged since the 2026-08-19 observation):
- gh: 2.97.0
- gh auth: logged in to github.com as ontheroadjp (ssh protocol, scopes: admin:public_key, gist, read:org, repo)
- node: v24.16.0 (via mise: `~/.local/share/mise/installs/node/24/bin/node`)
- npm: 11.13.0 (same mise install)
- Node runtime manager hints: no repo-local `.nvmrc`/`.node-version`/`.tool-versions`/`mise.toml` found; node/npm resolved from the user's global mise install, not a repo-local pin. `frontend/web` has a real Node.js dependency (Vite build) — node/npm ARE required there, unlike the CLI/`factory.sh`/`nuts_calc_tex.py` (in `backend/`) which remain Python-only (the latter additionally requires `pdflatex`, not Node.js).
- `nuts_calc_tex.py`'s optional Japanese-capable `lualatex` engine adapter (`NUTS_CALC_TEX_ENGINE=lualatex`, issue #121) additionally requires: the `lualatex` binary (LuaHBTeX, present via the base TeX Live install), the `texlive-luatex` apt package (provides `luaotfload`, the font loader `fontspec` needs on LuaLaTeX; installed 2026-08-14 via `sudo apt install texlive-luatex`, 2 packages, self-contained on top of the already-installed `texlive-latex-extra`), and the `fonts-noto-cjk` apt package (provides `Noto Sans CJK JP`, already present on this machine). None of this is required for the default `pdflatex` engine or for `backend/app.py`. upLaTeX/`luatexja` were evaluated and rejected for now: on Ubuntu both live inside `texlive-lang-japanese`, which pulls in `texlive-lang-cjk` (114 packages, including unrelated Chinese/Korean/Thai support) versus `texlive-luatex`'s 2; revisit only if paragraph-level Japanese typesetting (kinsoku shori/JFM spacing) is needed.

Notes:
- If `gh` operations fail with API schema or compatibility errors, check `gh --version` first. Prefer upgrading `gh` when possible; if upgrading is impossible, use an equivalent `gh api` REST call or GitHub Web UI for the affected operation.
- Before npm operations, run `node --version` and `npm --version` to confirm Node.js and npm are available in the current shell. This also initializes Node.js in lazy-loaded runtime manager environments such as nvm.
- Do not install or upgrade `gh`, Node.js, or npm automatically without explicit user confirmation.

## Python Environment

- All CLI/Flask code lives under `backend/` (moved there from the repo root and `web/backend/` in issue #88); run these commands with `backend/` as the working directory.
- No lock file, `requirements.txt`, or `pyproject.toml` exists. The CLI (`nuts_calc_tex.py`) has zero pip dependencies (standard library only); the web backend needs `Flask`/`Flask-Cors`; the test suite needs `pytest`. Install via `pip install flask flask-cors pytest` (see `README.md`). The former ReportLab CLI `nuts_calc.py` (which did depend on the `reportlab` package) was removed in issue #232.
- repo-local `venv/` has Python 3.12.3, Flask 3.1.3, Flask-Cors 6.0.5, and pytest 9.1.1.
- `cd backend && python3 -m pytest` collects and passes all 687 tests as of 2026-08-20 (issue #232 removed `nuts_calc.py` along with its dedicated test files, which had carried 9 long-standing known-stale failures -- resolved by deletion, not by fixing the assertions). `pdflatex`-dependent tests ran successfully; see `docs/L2_development/test.md`.
- `nuts_calc_tex.py` requires `pdflatex`/`lualatex` on `PATH`; its `pdflatex`-dependent CLI tests auto-skip when it's absent. Its `vendor/texmf` lookup is resolved relative to its own file location (`backend/vendor/texmf`), so it required no code change when `backend/` was introduced in issue #88. Its optional `lualatex` engine adapter (see Local Tooling Environment above) has its own `lualatex`-gated tests (`backend/tests/test_nuts_calc_tex_lualatex_engine.py`, plus pure-Python adapter-selection tests in `test_nuts_calc_tex_engine_adapter.py` that need neither binary) that auto-skip the same way when `lualatex` is absent.

## Web Frontend Environment (`frontend/web`)

`frontend/web` shares the same `backend/app.py` Flask API (issue #88). It was originally one of two independent frontends alongside `frontend/spa` (a React SPA); `frontend/spa` was removed in issue #233, leaving `frontend/web` as the sole Web UI frontend.

- `frontend/web` (lightweight static multi-page site — `index.html`/`catalog.html`/`preset.html` — Vite + Sass + KaTeX, Japanese only): `npm run build` succeeds (verified 2026-08-19, 3 HTML entries). Its two `node:test` files are run directly and 45 tests passed (up from 36 as of issue #139/#176's live-preview and answer-cap work); no npm test/lint scripts are configured. Its grade→category→menu-item model diverged from the former `frontend/spa`'s in issue #98. Its `preset.html` detail screen also calls `backend/app.py`'s `POST /generate-problems` endpoint (issue #138/#139) for live example previews — a feature the former `frontend/spa` did not have.
