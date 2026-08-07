# Specification Summary

DB は存在しないため `database.md` は生成していない(永続化層なし。`web/backend/app.py` に DB 接続の記述なし)。Flask バックエンドの2エンドポイントの詳細は [[api]] に分離した。

## CLI 仕様(`nuts_calc.py`)

引数・出力仕様は旧 `100masu.py` から機能的に踏襲されている。詳細は [[../L2_development/operation_model]] を参照。実機で7種類の `command` すべての正常終了を確認済み。筆算(縦書き)形式(旧 `--vertical` フラグ)は issue #46 で `nuts_calc.py` から削除され、`nuts_calc_tex.py` に一本化された(下記参照)。詳細は [[nuts_calc.py]] を参照。

## `nuts_calc_tex.py`(実験的プロトタイプ)

`nuts_calc.py` とはコード共有しない独立LaTeXレンダラー。issue #19の7コマンドに `frac` を加えた計8コマンドを実装する。`frac` は分子・分母の桁数(各1〜3)、同分母/異分母、真分数条件、add/sub/mul/div/mixを指定できる。未約分の出題表記を保持し、答えは `fractions.Fraction` で厳密に約分してPDF・下部解答・CSVへ出力する(`nuts_calc_tex.py:118-184,305-328,1339-1565`)。学年カードの根拠資料は `docs/reference/` に保存し、カードはLaTeXレンダラー時だけ表示する(`web/frontend/src/drillPresets.js:154-327`、`web/frontend/src/GradeDrills.jsx:201-269`)。issue #67 では `ope` コマンドに `--use-parentheses`(LaTeX専用)を追加し、かっこ付き多項式を出題する機能を実装した(当初は固定3項式 `(a op b) op c`/`a op (b op c)` のみ対応)。issue #69 では `ope` コマンドに `--missing-value`(LaTeX専用)を追加し、`a op b = c` のうち `a`/`b`(演算子の両オペランド)いずれか1つを隠す虫食い算を出題する。答え `c` は隠す候補に含まれない(通常の `ope` の答え非表示と区別がつかなくなるため)。issue #71 では `ope` コマンドに `--terms`/`--terms-min`/`--terms-max`/`--mixed-operators`(いずれもLaTeX専用)を追加し、2項固定だった `ope` を任意項数(2〜12)の多項演算に一般化するとともに、`--use-parentheses` を固定3項からN項(N>=3)のランダムな2分木構造へ一般化した。項数が下限(通常2、`--use-parentheses` 使用時は3)未満または上限(12)超で指定された場合はエラーにせずクランプする。詳細は [[nuts_calc_tex.py]] を参照。

## Web API 仕様(`web/backend/app.py`)

本節は責務サマリである。request field、status code、renderer 差異の完全な一覧は [[api]] を参照。

### `POST /generate-pdf`

- 入力: JSON ボディ。必須キーは `paper_size`, `command_type`。任意キーには通常 CLI option、分数 option、LaTeX 専用の `vertical`/`use_parentheses`/`missing_value`/`terms` 系を含む(`web/backend/renderers.py:9-42`)。
- 処理: 選択 renderer の CLI 引数へ変換し、UUID 出力名を指定して `subprocess.run(..., check=True)` を実行する(`web/backend/renderers.py:170-189`)。
- 出力: 成功時は PDF attachment。JSON/必須値欠落は HTTP 400、renderer/CLI 等の実行時失敗は HTTP 500(`web/backend/app.py:17-50`)。
- 入力検証: 必須キーの存在だけを backend で検証し、値の allowlist は CLI の argparse に委ねる。

### `GET /renderer-info`(issue #46)

- 入力: なし。
- 処理: `renderers.get_renderer_name()` を呼び、env 変数 `NUTS_CALC_RENDERER`(未設定時は `reportlab`)から解決した renderer 名を返す(`web/backend/renderers.py:48-69`)。
- 出力: 成功時は `{'renderer': 'reportlab'|'latex'}` を HTTP 200 で返す。`NUTS_CALC_RENDERER` に許可外の値が設定されている場合は `{'error': ...}` を HTTP 500 で返す。
- 用途: `web/frontend` がリクエスト前にどちらのレンダラーが有効かを判定し、`latex` のときのみ筆算(`vertical`)関連の UI を表示するために使う([[../../web/frontend/src/GradeDrills.jsx]]/[[../../web/frontend/src/CustomGenerator.jsx]] 参照)。

## 既知の欠陥1(解消済み): 旧 `ini.intermediate` 未定義参照、および issue #4 の9件のロジックバグ

`100masu.py`(現 `nuts_calc.py`)には、`command` が `ope` 以外だと `NameError: name 'ini' is not defined` で必ず失敗するバグが存在していた。`dev` ブランチのマージ(`nuts_calc.py`)で `if args.command == 'ope' or ini.intermediate:` が `if args.command == 'ope' or args.intermediate:` に修正されており、実機で7種類の `command` すべてが正常終了することを確認済み。修正コミット: `d9fc0a3`/`5466cdb` 系列(`100masu.py` → `nuts_calc.py` へのリネームと整理)。

その後の logic review(issue #4)で見つかった9件の独立したロジックバグも修正済み(`nuts_calc.py`/`web/backend/app.py`/`web/frontend/src/CustomGenerator.jsx`)。この中で上記の条件式はさらに `if args.command == 'ope':` へ変更されている(`--intermediate` が `ope` 以外のコマンドの `-a` 必須チェックを迂回してしまう問題を修正)。詳細は各ファイルの L3 doc([[../../nuts_calc.py]]、[[../../web/backend/app.py]]、[[../../web/frontend/src/CustomGenerator.jsx]])を参照。

同じくテスト作成中に見つかった issue #15(`OUTFILE_NAME_READ`/`OUTFILE_NAME_CSV` の導出が `str.rstrip('.pdf')` による文字クラス除去だったため、特定のファイル名で末尾が欠ける)も修正済み。上記の UUID ファイル名(`worksheet_<uuid>.pdf`)は16進数文字列のため末尾が `d`/`f` になり得ることから、CLI の直接指定に限らず Web API 経由でも実際に踏みうる不具合だった。詳細は [[../../nuts_calc.py]] を参照。

## 既知の欠陥2(解消済み): `web/frontend` のビルド失敗(依存関係欠落)

`web/frontend/src/i18n.js` が import する `i18next`/`react-i18next`/`i18next-browser-languagedetector`/`i18next-http-backend` が、かつて `web/frontend/package.json` の `dependencies` に含まれておらず `npm run build` が `Rollup failed to resolve import "i18next"` で失敗していた。現行の `web/frontend/package.json` にはこれら4パッケージがすべて記載されており(コミット `724f752` 等)、実機で `npm install && npm run build` が成功することを確認済み。

## 未確認事項

- `web/backend/app.py` を実際に起動し、修正前の壊れた状態のフロントエンドを経由せず直接 `POST /generate-pdf` を叩いた場合に正常に PDF が返るか(バックエンド単体の動作確認)は本ドキュメント作業では未実施。
- `--intermediate` オプション(`nuts_calc.py`、`ope` コマンドの中間式表示)は、CLI レベルでは `memo.md` の暗算法(2桁×1桁)と数式上一致することを自動テストで確認済み。フロントエンド経由(`web/frontend/src/CustomGenerator.jsx` の `vertical` チェックボックスと同様の UI)で意図通り動作するかは引き続き未検証。
