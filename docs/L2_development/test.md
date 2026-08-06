# Test

## テスト戦略

- フレームワーク: pytest(`pytest.ini:1-3`、`testpaths = tests`, `pythonpath = .`)。CI 定義は存在しないため、実行は手動(またはローカルフック)に依存する([[operation_model]] 参照)。
- 対象: `nuts_calc.py`(引数バリデーション・問題データ生成関数の単体テスト、CLI をサブプロセス起動して PDF/CSV 出力を確認する end-to-end テスト)、`nuts_calc_tex.py`(問題データ生成関数の単体テストは常時実行、`pdflatex` を要する CLI end-to-end テストは `pdflatex` 未検出時に自動スキップ)、`web/backend`(`app.py`/`renderers.py` のモジュールレベル単体テスト)。
- 対象外(未カバー、実装から確認): `web/frontend`(React コンポーネント)。フロントエンドの自動テスト定義は `web/frontend/package.json` の `scripts` に存在しない(`lint`/`build`/`dev`/`preview` のみ)。

## テストファイル一覧(`find tests -name 'test_*.py'` で確認、15ファイル)

| ファイル | 対象 |
|---|---|
| `tests/test_nuts_calc_init.py` | `nuts_calc.py` の `_init()`(引数パース・バリデーション) |
| `tests/test_nuts_calc_data.py` | `nuts_calc.py` の問題データ生成関数 |
| `tests/test_nuts_calc_cli.py` | `nuts_calc.py` を CLI としてサブプロセス起動する end-to-end テスト |
| `tests/test_nuts_calc_tex.py` | `nuts_calc_tex.py` の共通基盤(Phase 1)、CLI end-to-end を含む |
| `tests/test_nuts_calc_tex_ope_generation.py` | `nuts_calc_tex.py` `ope` コマンドの問題データ生成(単体) |
| `tests/test_nuts_calc_tex_com_generation.py` | `nuts_calc_tex.py` `com` コマンドの問題データ生成(単体) |
| `tests/test_nuts_calc_tex_hundred_square_generation.py` | `nuts_calc_tex.py` `100` コマンドの問題データ生成(単体) |
| `tests/test_nuts_calc_tex_kuku_generation.py` | `nuts_calc_tex.py` `99` コマンドの問題データ生成(単体) |
| `tests/test_nuts_calc_tex_abc_generation.py` | `nuts_calc_tex.py` `aBc` コマンドの問題データ生成(単体) |
| `tests/test_nuts_calc_tex_squ_generation.py` | `nuts_calc_tex.py` `squ` コマンドの問題データ生成(単体) |
| `tests/test_nuts_calc_tex_pi_generation.py` | `nuts_calc_tex.py` `pi` コマンドの問題データ生成(単体) |
| `tests/test_nuts_calc_tex_fraction_generation.py` | `nuts_calc_tex.py` `frac` の厳密計算・生成制約・LaTeX/CSV(単体) |
| `tests/test_web_backend_app.py` | `web/backend/app.py`(Flask ルーティング) |
| `tests/test_web_backend_renderers.py` | `web/backend/renderers.py`(レンダラー選択・コマンド構築) |
| `tests/conftest.py` | pytest フィクスチャ共通定義 |

## 実行方法

```bash
pip install pytest
pytest -q
```

`pdflatex` 依存のテストのみを除外/対象にしたい場合は、対象ファイルを個別に指定する(例: `pytest tests/test_nuts_calc_tex_ope_generation.py`)。マーカーによる明示的な分離(`pytest.ini` に `markers` 定義なし)は確認できないため、`pdflatex` 有無による自動スキップの実装詳細は各テストファイル内の `pytest.mark.skipif` 相当の記述に依存する(`docs/L3_implementation/nuts_calc_tex.py.md:147` 参照)。

## 実行結果(2026-08-06 時点、`docs/init-docs-20260806` 上で確認)

```
222 tests collected
tests/test_nuts_calc_init.py: 9 failed, 13 passed
fraction generation + backend renderer tests: 22 passed
fraction pdflatex CLI tests: 2 passed
```

失敗した9件はすべて `tests/test_nuts_calc_init.py` に属し、いずれも「`nuts_calc.py` の一部バリデーション分岐(`com`/`99`/`squ`/`pi` の `-a` 必須チェック、`100` の桁数チェック)が `exit()`(`SystemExit(None)`)を返すこと」を期待するテストである。実装は issue #37 でこれらの分岐を `exit(1)` に修正済みのため、テスト側の期待値が古いままになっている(`tests/test_nuts_calc_init.py:1-9` のモジュール docstring が「pre-refactor safety net としてあえて現状の挙動を pin している」と明記しており、意図的に残されたstaleなテストであることがコード側からも確認できる)。`docs/L3_implementation/nuts_calc.py.md:55` にも同じ内容が記録されている。

既知ファイルを除く全テストの一括実行は実行環境から最終サマリが返らなかったため未確認。確定には `python3 -m pytest -q --ignore=tests/test_nuts_calc_init.py` が完走する環境で再実行する。

## カバレッジ方針

- カバレッジ計測ツール(`pytest-cov` 等)の導入・設定は確認できない(`pytest.ini`/`package.json` 等にカバレッジ関連の記述なし)。数値目標は存在しない。

## 未確認事項

- `web/frontend` の自動テスト方針(導入予定の有無)は本リポジトリから確認できない。
- 上記9件の失敗テストを「テスト側を修正する」「実装側の `exit(1)` を `exit()` に戻す」のどちらの方向で解消する計画があるかは、issue トラッカー(本リポジトリの `git log`/`docs` からは確認不能な GitHub Issues の議論)を見る必要がある。
