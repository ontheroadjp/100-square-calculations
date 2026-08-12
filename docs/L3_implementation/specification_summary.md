# Specification Summary

DB は存在しないため `database.md` は生成していない(永続化層なし。`backend/app.py` に DB 接続の記述なし)。Flask バックエンドの2エンドポイントの詳細は [[api]] に分離した。

## CLI 仕様(`nuts_calc.py`)

引数・出力仕様は旧 `100masu.py` から機能的に踏襲されている。詳細は [[../L2_development/operation_model]] を参照。実機で7種類の `command` すべての正常終了を確認済み。筆算(縦書き)形式(旧 `--vertical` フラグ)は issue #46 で `nuts_calc.py` から削除され、`nuts_calc_tex.py` に一本化された(下記参照)。詳細は [[nuts_calc.py]] を参照。

## `nuts_calc_tex.py`(実験的プロトタイプ)

`nuts_calc.py` とはコード共有しない独立LaTeXレンダラー。issue #19の7コマンドに `frac`、`mixed`、`compare` を加えた計10コマンドを実装する。`frac` は分数の厳密な四則演算、`mixed` は整数・小数・分数を混在させた多項演算、`compare` は同分母・同分子・異分母の分数比較を生成し、`ope` は整数に加えて小数も扱う。issue #67 の `--use-parentheses`、issue #69 の `--missing-value`、issue #71 の `--terms`/`--terms-min`/`--terms-max`/`--mixed-operators` により、かっこ付き・虫食い・2〜12項の式を構成できる。issue #76 は小数 `ope` と `mixed` を追加した。issue #78 は2項整数 `ope` の加減算へ繰り上がり・繰り下がり条件を追加し、1年生向けWebカードを加算2・減算2・混合2の6枚に分割した。issue #81 でフラグ名を `--carry-borrow`/`--no-carry-borrow`/`--mixed-carry-borrow` に変更し、旧名は互換エイリアスなしで削除した。`allow_abbrev=False` により、旧名を含む長いオプションの省略形も受理しない。繰り下がりありの減算は10〜19−1桁に限定し、条件フラグ指定時は `--a-min` 等より条件を優先して候補範囲へフォールバックする。詳細は [[nuts_calc_tex.py]] を参照。

## Web API 仕様(`backend/app.py`)

本節は責務サマリである。request field、status code、renderer 差異の完全な一覧は [[api]] を参照。

### `POST /generate-pdf`

- 入力: JSON ボディ。必須キーは `paper_size`, `command_type`。任意キーには通常 CLI option、分数・小数・mixed・compare option、LaTeX 専用の `vertical`/`use_parentheses`/`missing_value`/`terms` 系と `carry_mode` を含む(`backend/renderers.py:9-48`)。
- 処理: 選択 renderer の CLI 引数へ変換し、UUID 出力名を指定して `subprocess.run(..., check=True)` を実行する(`backend/renderers.py:170-189`)。
- 出力: 成功時は PDF attachment。JSON/必須値欠落は HTTP 400、renderer/CLI 等の実行時失敗は HTTP 500(`backend/app.py:17-50`)。
- 入力検証: 必須キーの存在だけを backend で検証し、値の allowlist は CLI の argparse に委ねる。

### `GET /renderer-info`(issue #46)

- 入力: なし。
- 処理: `renderers.get_renderer_name()` を呼び、env 変数 `NUTS_CALC_RENDERER`(未設定時は `reportlab`)から解決した renderer 名を返す(`backend/renderers.py:48-69`)。
- 出力: 成功時は `{'renderer': 'reportlab'|'latex'}` を HTTP 200 で返す。`NUTS_CALC_RENDERER` に許可外の値が設定されている場合は `{'error': ...}` を HTTP 500 で返す。
- 用途: `frontend/spa`・`frontend/web`(issue #88 で追加された軽量静的サイト、両者とも `backend/app.py` を共通利用)がリクエスト前にどちらのレンダラーが有効かを判定し、`latex` のときのみ筆算(`vertical`)関連の UI を表示するために使う([[../../frontend/spa/src/GradeDrills.jsx]]/[[../../frontend/spa/src/CustomGenerator.jsx]] 参照)。

## 既知の欠陥1(解消済み): 旧 `ini.intermediate` 未定義参照、および issue #4 の9件のロジックバグ

`100masu.py`(現 `nuts_calc.py`)には、`command` が `ope` 以外だと `NameError: name 'ini' is not defined` で必ず失敗するバグが存在していた。`dev` ブランチのマージ(`nuts_calc.py`)で `if args.command == 'ope' or ini.intermediate:` が `if args.command == 'ope' or args.intermediate:` に修正されており、実機で7種類の `command` すべてが正常終了することを確認済み。修正コミット: `d9fc0a3`/`5466cdb` 系列(`100masu.py` → `nuts_calc.py` へのリネームと整理)。

その後の logic review(issue #4)で見つかった9件の独立したロジックバグも修正済み(`nuts_calc.py`/`backend/app.py`/`frontend/spa/src/CustomGenerator.jsx`)。この中で上記の条件式はさらに `if args.command == 'ope':` へ変更されている(`--intermediate` が `ope` 以外のコマンドの `-a` 必須チェックを迂回してしまう問題を修正)。詳細は各ファイルの L3 doc([[../../nuts_calc.py]]、[[../../backend/app.py]]、[[../../frontend/spa/src/CustomGenerator.jsx]])を参照。

同じくテスト作成中に見つかった issue #15(`OUTFILE_NAME_READ`/`OUTFILE_NAME_CSV` の導出が `str.rstrip('.pdf')` による文字クラス除去だったため、特定のファイル名で末尾が欠ける)も修正済み。上記の UUID ファイル名(`worksheet_<uuid>.pdf`)は16進数文字列のため末尾が `d`/`f` になり得ることから、CLI の直接指定に限らず Web API 経由でも実際に踏みうる不具合だった。詳細は [[../../nuts_calc.py]] を参照。

## 既知の欠陥2(解消済み): `frontend/spa` のビルド失敗(依存関係欠落)

`frontend/spa/src/i18n.js` が import する `i18next`/`react-i18next`/`i18next-browser-languagedetector`/`i18next-http-backend` が、かつて `frontend/spa/package.json` の `dependencies` に含まれておらず `npm run build` が `Rollup failed to resolve import "i18next"` で失敗していた。現行の `frontend/spa/package.json` にはこれら4パッケージがすべて記載されており(コミット `724f752` 等)、実機で `npm install && npm run build` が成功することを確認済み。

## 未確認事項

- `backend/app.py` を実際に起動し、修正前の壊れた状態のフロントエンドを経由せず直接 `POST /generate-pdf` を叩いた場合に正常に PDF が返るか(バックエンド単体の動作確認)は本ドキュメント作業では未実施。
- `--intermediate` オプション(`nuts_calc.py`、`ope` コマンドの中間式表示)は、CLI レベルでは `memo.md` の暗算法(2桁×1桁)と数式上一致することを自動テストで確認済み。フロントエンド経由(`frontend/spa/src/CustomGenerator.jsx` の `vertical` チェックボックスと同様の UI)で意図通り動作するかは引き続き未検証。
