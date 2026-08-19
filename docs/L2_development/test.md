# Test

## テスト戦略

- Python は pytest を使う。`backend/pytest.ini:1-3` が `testpaths = tests` と `pythonpath = .` を定義する(issue #88 で `backend/` ディレクトリへ移動。`pythonpath = .` は `backend/` 起点のまま機能するため内容変更なし)。CI は存在しないためローカル実行が保証手段である。
- `nuts_calc_tex.py` は純 Python の生成関数に加え、`pdflatex`/`lualatex` がある環境では PDF 生成も対象にする(`backend/tests/test_nuts_calc_tex.py:16-23`)。旧 ReportLab CLI(`nuts_calc.py`)向けのテスト(`test_nuts_calc_init.py`/`test_nuts_calc_data.py`/`test_nuts_calc_cli.py`/`conftest.py`)は issue #232 での削除に伴い、対象ファイルごと削除した。
- Flask は test client とレンダラー変換関数をモジュールレベルで検証する(`backend/tests/test_web_backend_app.py`、`backend/tests/test_web_backend_renderers.py`)。
- `frontend/spa` は Node.js 組み込み `node:test` でプリセット構造・カタログ構築・筆算行数を、`frontend/web` はプリセットデータモデルと詳細画面の純粋ヘルパーを検証する。DOMやブラウザE2Eは対象外である。

## テスト構成

`backend/tests/` には26個の `test_*.py` がある(issue #88 でリポジトリルートの `tests/` から移動)。主な責務は次のとおり。

| 対象 | ファイル | 根拠・理由 |
|---|---|---|
| LaTeX CLI | `test_nuts_calc_tex.py` とコマンド別 `test_nuts_calc_tex_*_generation.py` | 10コマンド、小数、分数比較、混合数種、繰り上がり条件の生成ロジックと `pdflatex` 成果物を検証する |
| 小数・混合プリセット | `test_nuts_calc_tex_decimal_generation.py`, `test_nuts_calc_tex_decimal_mixed_presets.py`, `test_nuts_calc_tex_mixed_generation.py` | issue #76 の小数 `ope` と `mixed` を検証する |
| 中学受験プリセット | `test_nuts_calc_tex_exam_prep_presets.py` | 4〜6年生×3段階×3レベルの組み合わせが retry 上限を枯渇させないことを生成関数で検証する |
| Web backend | `test_web_backend_app.py`, `test_web_backend_renderers.py` | renderer 選択、HTTP 応答、JSON→CLI 引数変換を検証する。issue #88 の移動に伴い `sys.path` の組み立て(旧: `REPO_ROOT / "web" / "backend"`)を `BACKEND_DIR` 直接参照に修正済み |
| Web backend(問題データのみ生成) | `test_problem_generation.py` | `POST /generate-problems`(issue #138)が使う `backend/problem_generation.py` の in-process 生成ラッパーを検証する |
| Frontend 純粋関数(`frontend/spa`) | `drillPresets.test.js`, `drillCatalog.test.js`, `verticalLayout.test.js` | package 追加なしで `node:test` を直接使う |
| Frontend 純粋関数(`frontend/web`) | `drillPresets.test.js`, `presetDetail.test.js` | メニュー項目の契約、設定サマリ、例題整形を `node:test` で検証する |

## 実行方法

Python 依存を手動導入してから `backend/` ディレクトリ内で実行する。

```bash
cd backend
pip install flask flask-cors pytest
python3 -m pytest -q
```

`frontend/spa` のテストは `package.json:scripts` に `test` がないため、次を直接実行する。

```bash
node --test frontend/spa/src/drillPresets.test.js frontend/spa/src/drillCatalog.test.js frontend/spa/src/verticalLayout.test.js
```

静的検査と build は別コマンドである。

```bash
cd frontend/spa
npm run lint
npm run build
```

`frontend/web` の `package.json` にはテスト・lintスクリプトがないため、テストは直接実行する:

```bash
node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js
cd frontend/web
npm run build
```

## 実行結果(2026-08-20、issue #232 の `nuts_calc.py` 削除後に再検証)

| 検証 | 結果 |
|---|---|
| `cd backend && python3 -m pytest -q` | 687 passed |
| `frontend/spa` `node --test ...`(3ファイル) | 17 passed |
| `frontend/web` `node --test ...`(2ファイル) | 45 passed |
| `cd frontend/spa && npm run build` | 成功 |
| `cd frontend/spa && npm run lint` | 1失敗: `frontend/spa/src/drillPresets.js:433` の全角空白を `no-irregular-whitespace` が拒否(issue #88 以前から継続する既知の指摘。行番号はプリセット追加により `:363` から変化) |
| `cd frontend/web && npm run build` | 成功(3 HTML エントリ: `index.html`/`catalog.html`/`preset.html`。`custom.html` は issue #97 で削除) |

**(解消済み、issue #232)** 以前は `backend/tests/test_nuts_calc_init.py` に9件の既知 stale 失敗(`exit()` の `SystemExit(None)` を期待するが、実装は issue #37 で `exit(1)` に修正済みだったための stale な期待値)があった。issue #232 で `nuts_calc.py` 本体とともにこのテストファイル自体を削除したため、この9件は「修正」ではなく「対象ファイルの削除」により解消した。

## カバレッジ方針

`pytest-cov`、frontend coverage、数値目標は設定されていない(`backend/pytest.ini:1-3`、`frontend/spa/package.json:6-10`、`frontend/web/package.json`)。現状はテスト件数と対象機能で回帰範囲を管理する。

## 未確認事項

- React コンポーネントの DOM 描画、Flask を実プロセス起動した結合テスト、ブラウザ E2E の方針は未確認。確定には対応する test runner/config が必要だが、現行 `package.json` とリポジトリ内設定には存在しない。
- frontendのDOM描画とブラウザE2Eの方針は未確認。現行のNodeテストは両frontendとも純粋関数のみを対象とする。
- lint 1件をコード修正するか lint 設定で許容するかは未決定。対象は `frontend/spa/src/drillPresets.js:433` と `frontend/spa/eslint.config.js`。
