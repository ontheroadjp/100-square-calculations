# Specification Summary

DB は存在しないため `database.md` は生成していない(永続化層なし。`web/backend/app.py` に DB 接続の記述なし)。API については、Flask バックエンドが1エンドポイントのみを提供するため、本ファイル内にまとめて記載し独立した `api.md` は生成していない。

## CLI 仕様(`nuts_calc.py`)

引数・出力仕様は旧 `100masu.py` から機能的に踏襲されている。詳細は [[../L2_development/operation_model]] を参照。実機で7種類の `command` すべての正常終了を確認済み。`ope` コマンドには `--vertical` フラグがあり、`add`/`sub`/`mul`(掛ける数が1桁のときのみ)を筆算(縦書き)形式で出力できる。詳細は [[nuts_calc.py]] を参照。

## Web API 仕様(`web/backend/app.py`)

### `POST /generate-pdf`

- 入力: JSON ボディ。必須キー: `paper_size`, `command_type`。任意キー: `a_value`, `b_value`, `a_min`, `a_max`, `b_min`, `b_max`, `operator`(配列), `descend`, `reverse`, `shuffle`, `intermediate`, `vertical`, `rows`, `columns`, `with_bottom_answer`, `page`, `merge`, `csv`, `debug`(`web/backend/app.py:16-54`)。
- 処理: 受け取った値を `nuts_calc.py` の CLI 引数に変換し、`--out-file` にサーバー側で生成した UUID ファイル名(`web/backend/generated_pdfs/worksheet_<uuid>.pdf`)を指定して `subprocess.run(..., check=True)` を実行(`web/backend/app.py:56-63`)。
- 出力: 成功時は生成された PDF ファイルをそのまま `send_file` で返す(`web/backend/app.py:69`)。失敗時は `{'error': ...}` を HTTP 400/500 で返す(`web/backend/app.py:28-29,71-79`)。
- 入力検証: `paper_size`/`command_type` の必須チェックのみ(`web/backend/app.py:28-29`)。値そのものの許可リスト検証はバックエンドには無く、最終的に `nuts_calc.py` 側の `argparse` の `choices` に委ねられている([[../L0_concept/policy]] に記録)。

## 既知の欠陥1(解消済み): 旧 `ini.intermediate` 未定義参照

`100masu.py`(現 `nuts_calc.py`)には、`command` が `ope` 以外だと `NameError: name 'ini' is not defined` で必ず失敗するバグが存在していた。`dev` ブランチのマージ(`nuts_calc.py`)で `if args.command == 'ope' or ini.intermediate:` が `if args.command == 'ope' or args.intermediate:` に修正されており、実機で7種類の `command` すべてが正常終了することを確認済み。修正コミット: `d9fc0a3`/`5466cdb` 系列(`100masu.py` → `nuts_calc.py` へのリネームと整理)。

## 既知の欠陥2(解消済み): `web/frontend` のビルド失敗(依存関係欠落)

`web/frontend/src/i18n.js` が import する `i18next`/`react-i18next`/`i18next-browser-languagedetector`/`i18next-http-backend` が、かつて `web/frontend/package.json` の `dependencies` に含まれておらず `npm run build` が `Rollup failed to resolve import "i18next"` で失敗していた。現行の `web/frontend/package.json` にはこれら4パッケージがすべて記載されており(コミット `724f752` 等)、実機で `npm install && npm run build` が成功することを確認済み。

## 未確認事項

- `web/backend/app.py` を実際に起動し、修正前の壊れた状態のフロントエンドを経由せず直接 `POST /generate-pdf` を叩いた場合に正常に PDF が返るか(バックエンド単体の動作確認)は本ドキュメント作業では未実施。
- `--intermediate` オプション(`nuts_calc.py`、`ope` コマンドの中間式表示)がフロントエンド経由も含めて意図通り動作するかは未検証。
