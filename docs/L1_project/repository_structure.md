# Repository Structure

モノレポ構成ではない。単一ディレクトリにスクリプトとドキュメントが並ぶフラットな構成（`apps/`, `packages/` 等のサブパッケージ分割なし。ディレクトリ一覧で確認済み）。

```
100-square-calculations/
├── 100masu.py          # PDF生成CLI本体（実行可能）
├── factory.sh          # バッチ生成シェルスクリプト（実行可能）
├── memo.md             # 暗算指導法の解説（教育コンテンツ、非コード）
├── example_result.pdf  # 生成物のサンプル
├── README.md           # 利用者向け説明（一部が実装と乖離、詳細は policy.md）
├── .gitignore          # *.pdf(example_result.pdf除く)/*.txt/*.csv/.DS_Store を除外
└── docs/                # 本コマンドで追加した設計ドキュメント
```

## 各ファイルの責務（実装から確認）

- `100masu.py`: CLI エントリポイント兼ロジック全体。以下の内部構成を持つ（行番号は `ac4167f` 時点）。
  - `_init()` (`100masu.py:29-181`): `argparse` によるコマンドライン引数定義とバリデーション。**既知バグ**: `100masu.py:158` で未定義の `ini` を参照 (`ini.intermediate`)。
  - データ生成関数群: `get_operation_data()` (`222`), `get_complement_data()` (`342`), `get_fixed_format_data()` (`377`), `get_aBc_data()` (`445`) — 各 `command` モードに対応する問題データを作る。
  - レイアウト関数群: `add_vertical_frame_set()` (`184`), `get_vertical_contents_raw_dataset()` (`519`), `get_vertical_contents()` (`579`), `get_bottom_results()` (`610`), `add_header_index()` (`487`), `addPageNumber()` (`642`) — ReportLab の `Frame`/`Table` を組み立てる。
  - `main(ini)` (`678-1219`): 用紙サイズ・余白・フォントサイズの決定、`BaseDocTemplate` の構築、ページ内容の流し込み、PDF/CSV 書き出し。
- `factory.sh`: `_basic`（`100masu.py:79-115` 相当、実際は `factory.sh:79-115`）や `_kuku` 系関数で、用紙サイズ・分量違いの複数パターンを `dist/` 以下に一括生成する。汎用シェルボイラープレート（`_usage`, `_log`, `_err` 等、`factory.sh:12-45`）を土台にしている。
- `memo.md`: コードではなく、暗算指導法・学習ステップ・受験算数における計算力の重要性を説明する日本語の教育コンテンツ。`100masu.py` が生成する問題形式（`aBc` 等）の教育的な意味づけの一次資料。
- `example_result.pdf`: `.gitignore` で `*.pdf` は除外されているが `!example_result.pdf` で明示的に追跡対象にしている生成物サンプル (`.gitignore:2-3`)。
- `README.md`: セットアップ・使い方の説明。ただし `command` の例（`operations`/`complements`）が実装の `choices`（`ope`/`com`）と一致していない（[[policy]] 参照）。

## 未確認事項

- `docs/` 以外に、リポジトリ外で管理されているドキュメント（Notion、Google Docs等）があるかどうかは本リポジトリから確認できない。
