# `backend/factory.sh`

## 目的・役割

`dist/` 配下に、暗算練習用のワークシートPDFをあらかじめ決められた構成でバッチ生成するシェルスクリプト。`_main()` が呼ぶ `_basic()`(現在有効)は用紙サイズ(A3/A4)・問題数(20/45)ごとに8ステップの `ope`/`aBc`/`squ` ワークシートを生成する。九九(`99`)関連の `_kuku*()` 関数群は実装済みだが `_main()` 内でコメントアウトされており、現在は呼ばれない。

## 動作の概要

- 対象コマンド生成スクリプトを issue #232 で `nuts_calc.py`(ReportLab)から `nuts_calc_tex.py`(LaTeX)に切り替えた。CLI引数体系(`-a`/`-b`/`-o`/`-c`/`-r`/`-p`/`--out-file`/`--a-min`/`--a-max`/`--b-min`/`--b-max`/`--shuffle`/`--reverse` 等)は両スクリプトで共通のため、呼び出し箇所の置換のみで移行できた(`backend/factory.sh:127-190` 付近)。`renderers.py`(Flask backend が使うレンダラー選択レイヤー)は経由せず、`python nuts_calc_tex.py ...` を直接 subprocess 実行する。
- `_basic()`(`backend/factory.sh:117-150`)は用紙サイズ(a3/a4)ごとに8ステップ(基礎計算・暗算・実践)のワークシートを生成し、`${DIST_DIR}/mental_arithmetic/${long}/${size}/step-0N.pdf` へ出力する。
- `_kuku()`/`_kuku_descend()`/`_kuku_random()`/`_kuku_all_mix()`(`backend/factory.sh:155-193`)は九九(`99`)コマンドの通常順・降順・ランダム順・全段混合ワークシートを生成する実装だが、`_main()` からは呼ばれていない(コメントアウト済み、`backend/factory.sh:110-113`)。
- `_init()`/`_args_check()`/`_set_static_var()` 等はテンプレート由来の汎用オプションパーサ(`-h`/`-v`/`-a`/`-b`/`-c`/`--verbose` 等)で、本スクリプト固有の生成ロジックとは独立している。

## 重要な設計判断とその理由

### `nuts_calc_tex.py` への切り替えに再設計を伴わなかった理由(issue #232)

`nuts_calc_tex.py` は `nuts_calc.py` と同じ CLI 引数体系(`paper_size`/`command`/`-a`/`-b`/`--rows`/`--descend` 等)を実装当初から踏襲する設計方針で作られている([[../../nuts_calc_tex.py]] 参照)。`factory.sh` が使う `-a`/`-b`/`-o`/`-c`/`-r`/`-p`/`--out-file`/`--a-min`/`--a-max`/`--b-min`/`--b-max`/`--shuffle`/`--reverse` はいずれも両スクリプトで同一のため、`python nuts_calc.py` を `python nuts_calc_tex.py` に置換するだけで移行できた。

## 統合ポイント

- 呼び出し元: 手動実行(`./factory.sh`、引数不要)。CI からは呼ばれない(`docs/.ai/repo.profile.json` の `notes.ci` 参照)。
- 呼び出し先: `backend/nuts_calc_tex.py`(`subprocess` 経由、CLI 直接実行)。

## 注意事項・既知の制限

- `nuts_calc_tex.py` は LaTeX(既定 `lualatex`)でレンダリングするため、`nuts_calc.py`(ReportLab、Pythonライブラリのみで完結)と異なり `pdflatex`/`lualatex` が `PATH` 上に必要(issue #232 で追加された前提条件、`backend/factory.sh:26-29` のヘッダコメント参照)。
- `python`(`python3` ではない)を直接呼んでいる。実行環境の `python` が正しいインタプリタを指している前提で、本 issue のスコープでは変更していない。
- `_kuku*()` 関数群は実装済みだが `_main()` から呼ばれていない状態が本 issue 以前から続いている(コメントアウトの理由は git 履歴・issue から特定できず、未確認事項)。

## 変更履歴(git log より自動生成)

（このファイルは issue #232 で L3 ドキュメントを新規作成したため、変更履歴は未収集）
