# `backend/pytest.ini`

## 目的・役割

`backend/` 配下の Python テストスイート(pytest)の設定ファイル。CI が存在しないため、このスイートのローカル実行が唯一の品質ゲートである(`docs/L2_development/test.md`)。

## 動作の概要

`backend/pytest.ini:1-4` の `[pytest]` セクションに 3 つの設定を持つ:

- `pythonpath = .` — `backend/` を import パスに加え、テストから `import nuts_calc_tex` / `import app` 等を可能にする。issue #88 でリポジトリルートの `pytest.ini` を `backend/` へ移動したが、`.` は実行時の rootdir(=`backend/`)起点で解決されるため内容変更は不要だった。
- `testpaths = tests` — 収集対象を `backend/tests/` に限定する。
- `addopts = -n auto` — `pytest-xdist` にテストをワーカープロセスへ分散させる。`auto` は `os.cpu_count()` 相当のワーカー数を使う。`python3 -m pytest -q` を追加フラグなしで並列実行にするための設定。

## 重要な設計判断とその理由

### `addopts = -n auto` を既定にした理由(issue #322)

スイートは相互依存のないテストで構成される — 純関数の生成ロジック検証と、`tmp_path` で出力先を分離した `pdflatex`/`lualatex` コンパイル検証のみ。後者が支配的コスト(8 論理コア環境で全 1147 件 283 秒のうち、`lualatex` コンパイル 61 件だけで約 152 秒)であり、プロセス並列で安全に短縮できる。`addopts` に置くことで、開発者や `/work` フローが特別なフラグを付けずに並列実行の恩恵を受ける。実測では 283 秒 → 85 秒(約 3.3 倍)に短縮し、`1147 passed` は不変。

### 直列実行へのフォールバック

単一テストのデバッグ時など直列実行が必要な場合は `python3 -m pytest -n0` で `addopts` の `-n auto` を打ち消せる。`pytest.ini` 側に条件分岐は持たせていない。

### トレードオフ: `pytest-xdist` が必須依存になる

`-n auto` を `addopts` に固定したため、`pytest-xdist` 未導入環境では pytest が `unrecognized arguments: -n` で即失敗する。リポジトリには `requirements.txt` 等がなく依存は手動導入のため、`README.md`(Running checks / Dependencies)に `pip install pytest pytest-xdist` を明記して対応する。

## 統合ポイント

- 呼び出し元: `cd backend && python3 -m pytest -q`(開発者が直接実行、`docs/.ai/repo.profile.json` の `run_tests`)。
- 依存: `pytest`、`pytest-xdist`(および推移依存の `execnet`)。repo-local `venv/` に導入する。
- 収集対象: `backend/tests/` 配下の `test_*.py`(現在 35 ファイル)。

## 注意事項・既知の制限

- `-n auto` 下でも `backend/tests/test_nuts_calc_tex.py` の subprocess 版 CLI テスト(`CLI_TIMEOUT_SECONDS = 60`)は 8 ワーカー同時コンパイル環境で問題なくパスしている。将来コンパイルが重くなりタイムアウトに接近する場合は `-n auto` を `-n <数>` に下げる余地がある。
- ワーカー間でテスト実行順は非決定的になる。順序依存のテストは現状存在しない。
- `docs/.ai/repo.profile.json` の `install_test_deps`(現在 `pip install pytest`)は `/init-docs` 管轄のため本 issue では更新しておらず、別途反映が必要。

## 変更履歴(git log より自動生成)

- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
- 6cebc5d test: add pytest regression suite for nuts_calc.py
