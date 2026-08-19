# Specification Summary

DB は存在しないため `database.md` は生成していない(永続化層なし。`backend/app.py` に DB 接続の記述なし)。Flask バックエンドの2エンドポイントの詳細は [[api]] に分離した。

## CLI 仕様(`nuts_calc.py`)

引数・出力仕様は旧 `100masu.py` から機能的に踏襲されている。詳細は [[../L2_development/operation_model]] を参照。実機で7種類の `command` すべての正常終了を確認済み。筆算(縦書き)形式(旧 `--vertical` フラグ)は issue #46 で `nuts_calc.py` から削除され、`nuts_calc_tex.py` に一本化された(下記参照)。詳細は [[nuts_calc.py]] を参照。

## `nuts_calc_tex.py`(実験的プロトタイプ)

`nuts_calc.py` とはコード共有しない独立LaTeXレンダラー。issue #19の7コマンドに `frac`、`mixed`、`compare` を加えた10コマンドに、issue #94の `evenodd`(偶数・奇数判定)/`multiples`(倍数列挙)/`divisors`(約数列挙)、issue #95の `lcm`/`gcd`(最小公倍数・最大公約数)、issue #96の `simplify`(約分)/`commondenom`(通分)/`frac2dec`(分数を小数に直す)/`dec2frac`(小数を分数に直す)/`divfrac`(割り算の答えを分数で表す、a÷b=a/b)を加えた計20コマンドを実装する。`evenodd`/`multiples`/`divisors` は `com`/`99`/`squ`/`pi` の単一 `-a/--a-value` ではなく `ope` と同じ `--a-min`/`--a-max` から問題ごとにランダムな基準値を抽選し、`evenodd` の答えはpdflatexのCJKフォント未対応制約により英語 `even`/`odd` を採用する(`--with-name-field` と同じ制約)。`lcm`/`gcd` は2つの整数からLCM/GCDを出題する二数入力・一答出力ドリルで、`math.lcm`/`math.gcd` と表示ラベル(`LCM`/`GCD`)以外は完全に同じ実装を共有し、同様に英語ラベルを採用している。`simplify`/`commondenom`/`frac2dec` は既存の `--numerator-digits`/`--denominator-digits` を再利用し、`frac2dec`/`dec2frac` は分母を素因数2・5のみに制限することで循環小数を一切生成しない。`divfrac` は `lcm`/`gcd` と同じ二数入力パターンだが答えを約分せず `a/b` のまま表示する。`frac` は分数の厳密な四則演算、`mixed` は整数・小数・分数を混在させた多項演算、`compare` は同分母・同分子・異分母の分数比較を生成し、`ope` は整数に加えて小数も扱う。issue #67 の `--use-parentheses`、issue #69 の `--missing-value`、issue #71 の `--terms`/`--terms-min`/`--terms-max`/`--mixed-operators` により、かっこ付き・虫食い・2〜12項の式を構成できる。issue #76 は小数 `ope` と `mixed` を追加した。issue #78 は2項整数 `ope` の加減算へ繰り上がり・繰り下がり条件を追加し、1年生向けWebカードを加算2・減算2・混合2の6枚に分割した。issue #81 でフラグ名を `--carry-borrow`/`--no-carry-borrow`/`--mixed-carry-borrow` に変更し、旧名は互換エイリアスなしで削除した。`allow_abbrev=False` により、旧名を含む長いオプションの省略形も受理しない。繰り上がりあり加算・繰り下がりあり減算は、条件フラグ指定時に設定された `--a-min` 等の候補範囲内でまず再抽選し、見つからなければ桁幅を保った代表値へ決定的にフォールバックする。ただし繰り下がりあり減算は、設定範囲が両方とも1桁(1〜9)の場合(正の結果を持つ繰り下がり組がそのレンジ内に存在しえない)に限り、issue #92 以前と同じ10〜19−1桁のサンプリングを維持する。issue #91 は `ope -o div` 専用の `--remainder`/`--no-remainder`/`--mixed-remainder` を追加し、除算の余りあり/なし/まぜるを制御できるようにした(`--carry-borrow` 系と同じ排他グループ・決定的フォールバックのパターン)。issue #93 は全コマンド共通のページヘッダーへ `--with-name-field` を追加し、Name欄を任意で印字できるようにした(pdflatexのCJKフォント未対応制約により、日本語ラベルではなく既存の `Date:`/`Time:` と同じ英語ラベルを採用)。issue #104 は本ファイルのLaTeX実行系をプラガブルな `LatexEngineAdapter`(`NUTS_CALC_TEX_ENGINE` 環境変数、既定 `lualatex`、issue #186 で `pdflatex` から変更)へ抽象化する計画として、#120(アダプター導入、対応済み)→ #121(日本語対応エンジン評価・実装、対応済み: LuaLaTeX+fontspec+Noto Sans CJK JP を採用)→ #122(レイアウト統一)に分解された。issue #112 は `frac -o add`/`sub` に帯分数表示を追加し、`compare` 専用だった `--a-fraction-form`/`--b-fraction-form`(`proper`/`mixed`/`mix`、`frac` では `improper` 拒否)を共有した。答えが1以上になる場合も帯分数表記になる。issue #113 は `--carry-borrow`/`--no-carry-borrow`/`--mixed-carry-borrow` を `--a-decimal-places`/`--b-decimal-places` と併用可能にした(加減算の生成ロジックはスケール済み整数に対して桁単位で動作するため、小数桁数が揃っていれば整数と同じ判定でそのまま機能する)。issue #114 は `frac -o mul`/`div` と二項限定の `mixed -o mul`/`div`(fraction×int の組合せのみ)に `--require-reducible`/`--no-reducible`/`--mixed-reducible` を追加し、未約分の生の分子・分母のまま計算した積・商が約分を要するかどうかを制御できるようにした(`--carry-borrow`/`--remainder` 系と同じ排他グループ・`mixed` モードのパターン)。issue #134 は `ope --vertical` を `--a-decimal-places`/`--b-decimal-places` と併用できるよう拡張した(`xlop`/`longdivision` がいずれも小数点付きオペランドを正しく描画できることを実機確認した上での緩和)。ただし `div` オペレーターかつ除数が小数(`--b-decimal-places > 0`)の組み合わせのみ引き続き拒否する(`longdivision` の `\intlongdivision` が整数の除数しか受け付けないため)。詳細は [[nuts_calc_tex.py]] を参照。

`--result-max` は通常2項・かっこ付き・N項・虫食いの全 `ope` 式形式で最終結果を上限以下に制約し、小数は表示値を基準に判定する。成立する式が retry 上限内に見つからなければ、上限を無視せず明示的に失敗する(`backend/nuts_calc_tex.py:193-196,620-624,1341-1404,1769-1810,1991-2033,2135-2166`)。

## Web API 仕様(`backend/app.py`)

本節は責務サマリである。request field、status code、renderer 差異の完全な一覧は [[api]] を参照。

### `POST /generate-pdf`

- 入力: JSON ボディ。必須キーは `paper_size`, `command_type`。任意キーには通常 CLI option、分数・小数・mixed・compare option、LaTeX 専用の `vertical`/`use_parentheses`/`missing_value`/`terms` 系、`carry_mode`、`remainder_mode`、`reducible_mode`、`result_max` を含む(`backend/renderers.py:9-54`)。
- 処理: 選択 renderer の CLI 引数へ変換し、UUID 出力名を指定して `subprocess.run(..., check=True)` を実行する(`backend/renderers.py:170-189`)。
- 出力: 成功時は PDF attachment。JSON/必須値欠落は HTTP 400、renderer/CLI 等の実行時失敗は HTTP 500(`backend/app.py:17-50`)。
- 入力検証: 必須キーの存在だけを backend で検証し、値の allowlist は CLI の argparse に委ねる。

### `POST /generate-problems`(issue #138)

- 入力: `POST /generate-pdf` と同じ JSON ボディに加え、生成する問題数を指定する `num`(正の整数、必須)。`command_type='ope'`(素の2項四則演算 + issue #168 の `--use-parentheses`/`--missing-value`/`--terms`系(`terms`/`terms_min`/`terms_max`/`mixed_operators`)3亜種)に加え、issue #169 で `com`/`99`/`aBc`/`squ`/`pi` にも対応した。`100` は意図的に対象外(`ValueError`、下記「位置づけ」参照)。
- 処理: subprocess は起動せず、`backend/problem_generation.py` が `nuts_calc.py`/`nuts_calc_tex.py` の既存データ生成関数(`get_operation_data`/`generate_ope_problems`/`generate_tree_ope_problems`/`generate_multi_term_ope_problems`/`generate_missing_value_problems`/`generate_com_problems`/`generate_kuku_problems`/`generate_abc_problems`/`generate_squ_problems`/`generate_pi_problems`)を、`command_type` → 生成関数のディスパッチテーブル(`_COMMAND_GENERATORS`)経由でプロセス内で直接呼び出す。PDF/LaTeXファイルは一切生成しない(`backend/problem_generation.py:47-344`)。
- 出力: 成功時は `{'problems': [...]}` を HTTP 200 で返す(コマンド・亜種ごとに item の形状が異なる)。必須値欠落は HTTP 400、未対応の `command_type`(`100` を含む)、亜種フラグの相互排他違反(例: `missing_value`+`use_parentheses`)、`terms_min > terms_max`、`com`/`99`/`squ`/`pi` での `a_value` 欠落、または reportlab レンダラーへの亜種フラグ指定(`nuts_calc.py` に対応実装がない)は `ValueError` を HTTP 500 で返す(`backend/app.py`)。
- 位置づけ: issue #166「データ層とプレゼンテーション層の分離」の実装。issue #167 でアーキテクチャ・JSON contract を決定、issue #168 で `ope` 亜種、issue #169 で `com`/`99`/`aBc`/`squ`/`pi` を実装した。`100` は単一の `HundredSquareTable` を返す(`num`-many のリストではない)ため `{'problems': [...]}` envelope に合わず、意図的に対象外のまま(issue #169)。残り約14コマンド(`frac`/`mixed`/`compare` 等)は同issue配下の `agenda` ラベル付き sub-issue(#170-#173)で追って対応する。issue #139 で `frontend/web/src/presetDetail.js` が最初の呼び出し元となり、`command_type: 'ope'` かつ未対応フラグなしのプリセットに限り、設定変更のたびにこのエンドポイントから例題チップを取得する(それ以外のプリセットは issue #135 由来の静的 `examples`/`examplesFor` のまま)。

### `GET /renderer-info`(issue #46)

- 入力: なし。
- 処理: `renderers.get_renderer_name()` を呼び、env 変数 `NUTS_CALC_RENDERER`(未設定時は `latex`、issue #186 で `reportlab` から変更)から解決した renderer 名を返す(`backend/renderers.py:90-107`)。
- 出力: 成功時は `{'renderer': 'latex'}` を HTTP 200 で返す。`NUTS_CALC_RENDERER` に許可外の値が設定されている場合、または明示的に `reportlab` が指定された場合(issue #186 で非推奨・到達不能になったが `RENDERER_SCRIPTS`/コード自体は削除していない)は `{'error': ...}` を HTTP 500 で返す。
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
