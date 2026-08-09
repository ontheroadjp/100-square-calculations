# Test

## テスト戦略

- Python は pytest を使う。`pytest.ini:1-3` が `testpaths = tests` と `pythonpath = .` を定義する。CI は存在しないためローカル実行が保証手段である。
- `nuts_calc.py` は引数検証、生成関数、subprocess 経由の PDF/CSV 出力を対象にする。`nuts_calc_tex.py` は純 Python の生成関数に加え、`pdflatex` がある環境では PDF 生成も対象にする(`tests/test_nuts_calc_tex.py:16-23`)。
- Flask は test client とレンラー変換関数をモジュールレベルで検証する(`tests/test_web_backend_app.py:20-53`、`tests/test_web_backend_renderers.py:19-191`)。
- frontend は Node.js 組み込み `node:test` でプリセット構造と筆算行数の純粋関数を検証する。React DOM やブラウザ E2E は対象外である。

## テスト構成

`tests/` には18個の `test_*.py` がある。主な責務は次のとおり。

| 対象 | ファイル | 根拠・理由 |
|---|---|---|
| ReportLab CLI | `test_nuts_calc_init.py`, `test_nuts_calc_data.py`, `test_nuts_calc_cli.py` | 引数、データ、成果物を層別に検証する |
| LaTeX CLI | `test_nuts_calc_tex.py` とコマンド別 `test_nuts_calc_tex_*_generation.py` | 9コマンド、小数、混合数種、繰り上がり条件の生成ロジックと `pdflatex` 成果物を検証する |
| 小数・混合プリセット | `test_nuts_calc_tex_decimal_generation.py`, `test_nuts_calc_tex_decimal_mixed_presets.py`, `test_nuts_calc_tex_mixed_generation.py` | issue #76 の小数 `ope` と `mixed` を検証する |
| 中学受験プリセット | `test_nuts_calc_tex_exam_prep_presets.py` | 4〜6年生×3段階×3レベルの組み合わせが retry 上限を枯渇させないことを生成関数で検証する(`tests/test_nuts_calc_tex_exam_prep_presets.py:18-81`) |
| Web backend | `test_web_backend_app.py`, `test_web_backend_renderers.py` | renderer 選択、HTTP 応答、JSON→CLI 引数変換を検証する |
| Frontend 純粋関数 | `drillPresets.test.js`, `verticalLayout.test.js` | package 追加なしで `node:test` を直接使う |

## 実行方法

Python 依存を手動導入してからリポジトリルートで実行する。

```bash
pip install reportlab flask flask-cors pytest
python3 -m pytest -q
```

既知の stale ファイルを分離して現行実装の回帰だけを見る場合:

```bash
python3 -m pytest -q --ignore=tests/test_nuts_calc_init.py
```

frontend のテストは `web/frontend/package.json:scripts` に `test` がないため、次を直接実行する。

```bash
node --test web/frontend/src/drillPresets.test.js web/frontend/src/verticalLayout.test.js
```

静的検査と build は別コマンドである。

```bash
cd web/frontend
npm run lint
npm run build
```

## 実行結果(2026-08-09、`docs/init-docs-20260809`)

| 検証 | 結果 |
|---|---|
| `python3 -m pytest --collect-only -q` | 408 tests collected |
| `python3 -m pytest -q --ignore=tests/test_nuts_calc_init.py` | 386 passed |
| `python3 -m pytest -q tests/test_nuts_calc_init.py` | 9 failed, 13 passed(既知 stale) |
| frontend `node --test ...` | 12 passed |
| `npm run build` | 成功(Vite 7.1.5、68 modules transformed) |
| `npm run lint` | 1失敗: `web/frontend/src/drillPresets.js:363` の全角空白を `no-irregular-whitespace` が拒否 |

9件の pytest 失敗は `exit()` の `SystemExit(None)` を期待するが、実装は issue #37 で `exit(1)` に修正済みである(`tests/test_nuts_calc_init.py:48-64,80-84`、`nuts_calc.py:230-259`)。したがって stale な期待値であり、現行実装の不具合とは判定しない。

## カバレッジ方針

`pytest-cov`、frontend coverage、数値目標は設定されていない(`pytest.ini:1-3`、`web/frontend/package.json:6-10`)。現状はテスト件数と対象機能で回帰範囲を管理する。

## 未確認事項

- React コンポーネントの DOM 描画、Flask を実プロセス起動した結合テスト、ブラウザ E2E の方針は未確認。確定には対応する test runner/config が必要だが、現行 `package.json` とリポジトリ内設定には存在しない。
- stale 9件をいつ更新するかはリポジトリ内から確定できない。GitHub issue/PR の方針確認が必要。
- lint 1件をコード修正するか lint 設定で許容するかは未決定。対象は `web/frontend/src/drillPresets.js:363` と `web/frontend/eslint.config.js`。
