# Test

## テスト戦略

- Python は pytest を使う。`backend/pytest.ini:1-4` が `testpaths = tests`、`pythonpath = .`、`addopts = -n auto` を定義する(issue #88 で `backend/` ディレクトリへ移動。`pythonpath = .` は `backend/` 起点のまま機能するため内容変更なし。`addopts = -n auto` は issue #322 で追加し、`pytest-xdist` によりテストを CPU コア数だけのワーカーへ分散する)。CI は存在しないためローカル実行が保証手段である。
- `nuts_calc_tex.py` は純 Python の生成関数に加え、`pdflatex`/`lualatex` がある環境では PDF 生成も対象にする(`backend/tests/test_nuts_calc_tex.py:16-23`)。旧 ReportLab CLI(`nuts_calc.py`)向けのテスト(`test_nuts_calc_init.py`/`test_nuts_calc_data.py`/`test_nuts_calc_cli.py`/`conftest.py`)は issue #232 での削除に伴い、対象ファイルごと削除した。
- Flask は test client(`backend/tests/test_web_backend_app.py`)とレンダラー名解決(`backend/tests/test_renderer_config.py`。issue #297 で `test_web_backend_renderers.py` からリネーム、`build_command` テストは同 issue で削除)をモジュールレベルで検証する。
- `frontend/web` は Node.js 組み込み `node:test` でプリセットデータモデル、詳細画面の純粋ヘルパー、Vite 設定を検証する。DOMやブラウザE2Eは対象外である。

## テスト構成

`backend/tests/` には34個の `test_*.py` がある(issue #88 でリポジトリルートの `tests/` から移動)。主な責務は次のとおり。

| 対象 | ファイル | 根拠・理由 |
|---|---|---|
| LaTeX CLI | `test_nuts_calc_tex.py` とコマンド別 `test_nuts_calc_tex_*_generation.py` | 全20コマンド、小数、分数比較、混合数種、繰り上がり条件の生成ロジックと LaTeX 成果物を検証する |
| 小数・混合プリセット | `test_nuts_calc_tex_decimal_generation.py`, `test_nuts_calc_tex_decimal_mixed_presets.py`, `test_nuts_calc_tex_mixed_generation.py` | issue #76 の小数 `ope` と `mixed` を検証する |
| 中学受験プリセット | `test_nuts_calc_tex_exam_prep_presets.py` | 4〜6年生×3段階×3レベルの組み合わせが retry 上限を枯渇させないことを生成関数で検証する |
| Web backend | `test_web_backend_app.py`, `test_renderer_config.py` | `test_web_backend_app.py` は HTTP 応答と 3層モデル経路への routing を、`test_renderer_config.py`(issue #297 で `test_web_backend_renderers.py` からリネーム)は `get_renderer_name()` を検証する。issue #297 で legacy subprocess 経路と JSON→CLI 引数変換(`build_command`)のテストは削除。issue #88 の移動に伴い `sys.path` の組み立て(旧: `REPO_ROOT / "web" / "backend"`)を `BACKEND_DIR` 直接参照に修正済み |
| Web backend(問題データのみ生成) | `test_problem_generation.py` | `POST /generate-problems`(issue #138)が使う `backend/problem_generation.py` の in-process 生成ラッパーを検証する |
| Frontend 純粋関数(`frontend/web`) | `drillPresets.test.js`, `presetDetail.test.js` | メニュー項目の契約、設定サマリ、例題整形を `node:test` で検証する |
| Frontend build 設定 | `frontend/web/vite.config.test.js` | 開発用 CSS sourcemap が有効で production sourcemap は未設定であることを検証する |

## 実行方法

Python 依存を手動導入してから `backend/` ディレクトリ内で実行する。

```bash
cd backend
pip install flask flask-cors pytest pytest-xdist
python3 -m pytest -q
```

`addopts = -n auto`(`backend/pytest.ini`)により `python3 -m pytest` は追加フラグなしで並列実行になる。`pytest-xdist` 未導入だと `unrecognized arguments: -n` で即失敗するため、上記の `pip install` に含める。単一テストのデバッグ等で逐次実行したい場合は `python3 -m pytest -n0` で打ち消す。

`frontend/web` の `package.json` にはテスト・lintスクリプトがないため、テストは直接実行する:

```bash
node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js frontend/web/vite.config.test.js
cd frontend/web
npm run build
```

## 実行結果(2026-09-01、standalone `/init-docs` で再検証)

| 検証 | 結果 |
|---|---|
| `cd backend && python3 -m pytest -q` | 1147 passed in 86.05s。`backend/pytest.ini:4` の `addopts = -n auto` により pytest-xdist で並列実行 |
| `frontend/web` `node --test ...`(3ファイル) | 72 passed |
| `cd frontend/web && npm run build` | 成功(3 HTML エントリ: `index.html`/`catalog.html`/`preset.html`。`custom.html` は issue #97 で削除) |

**(解消済み、issue #232)** 以前は `backend/tests/test_nuts_calc_init.py` に9件の既知 stale 失敗(`exit()` の `SystemExit(None)` を期待するが、実装は issue #37 で `exit(1)` に修正済みだったための stale な期待値)があった。issue #232 で `nuts_calc.py` 本体とともにこのテストファイル自体を削除したため、この9件は「修正」ではなく「対象ファイルの削除」により解消した。

**frontend/spa の削除(issue #233)**: 上記2026-08-20時点では `frontend/spa` も併存しており、`node --test ...`(3ファイル)17 passed・`npm run build` 成功・`npm run lint` は `frontend/spa/src/drillPresets.js:433` の全角空白を `no-irregular-whitespace` が拒否して1失敗、という結果だった。`frontend/spa` 自体が issue #233 で削除されたため、これらの検証項目自体が対象外になった。

## カバレッジ方針

`pytest-cov`、frontend coverage、数値目標は設定されていない(`backend/pytest.ini:1-4`、`frontend/web/package.json`)。現状はテスト件数と対象機能で回帰範囲を管理する。

## 未確認事項

- フロントエンドの DOM 描画、Flask を実プロセス起動した結合テスト、ブラウザ E2E の方針は未確認。確定には対応する test runner/config が必要だが、現行 `package.json` とリポジトリ内設定には存在しない。
- frontendのDOM描画とブラウザE2Eの方針は未確認。現行のNodeテストは純粋関数と Vite 設定のみを対象とする。
