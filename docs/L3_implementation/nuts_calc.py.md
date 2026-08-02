# `nuts_calc.py`

## 目的・役割

計算ドリル PDF 生成 CLI 本体。`argparse` でコマンドライン引数を解析し(`_init`)、ReportLab の `Frame`/`Table` を組み立てて PDF(と任意で CSV)を出力する(`main`)。対応する `command` は `ope`(四則演算)・`com`(補数)・`100`(100マス)・`99`(九九)・`aBc`・`squ`(平方数)・`pi`(円周率計算)の7種類。

## 動作の概要

- `_init()` が引数を検証・正規化して `argparse.Namespace` を返す。`command` ごとに `-a`/`-b`(桁数指定)から `a_min`/`a_max`/`b_min`/`b_max`(実際の数値範囲)を導出する(`nuts_calc.py:232-245`)。`ope` 以外の `command` では `--intermediate` を渡してもこの導出は行われない(`command == 'ope'` のみが対象、issue #4 Phase 1)。
- `_init()` は他に以下をバリデーションする: `com`/`99`/`squ`/`pi` の `-a` 必須(未指定時は `exit()`、終了コード0の既知の挙動)、`100` の `-a`/`-b` は3桁まで、`--intermediate` は第2引数(`b`)が1桁の場合のみ許可(`args.b_max > SINGLE_DIGIT_MAX` なら `exit(1)`、issue #4 Phase 3)、`--vertical` 関連の制約群(下記)、`-r`/`-c` は `MIN_ROWS_OR_COLUMNS`(=1)以上必須(`exit(1)`)。
- `main(ini)` は用紙サイズ・コマンドに応じて `Frame` レイアウトを組み立て、`get_vertical_contents_raw_dataset` で問題データを生成し、`command` ごとの描画ロジックで PDF 2種(通常版・解答版 `_read.pdf`)を作る。`ini.merge` が真の場合は1ファイルに問題ページ→解答ページを交互に収める(`next_content` による1ページ遅延の仕組み)。
- `nums_a`/`nums_b`(問題の種となる数値集合)は `ini.a_min`/`ini.a_max` などから `range(min, max + 1)`(上限含む)で構築する。`min == max` の場合は `random.sample` を経由せず単一要素リストにする分岐があり、この等価判定は `!=`(恒等比較 `is not` ではない)を使う(issue #4 Phase 2, 6)。同様の `range(min, max + 1)` 構築は `100` コマンド側にも独立して存在する。

## `ope` コマンドの出力形式(横書き / 筆算)

`ope` コマンドには2つの出力形式がある:

- **横書き形式(デフォルト)**: `a + b = c` を1行で表示。`get_operation_data` → `get_vertical_contents` → `add_vertical_frame_set` の組み合わせで、問題の各要素(index/a/演算子/b/=/answer)をそれぞれ専用の縦長 `Frame` に敷き詰める(`nuts_calc.py:927-956,1281-1348`)。
- **筆算(縦書き)形式(`--vertical`)**: 小学校で習う「筆算」の見た目(桁を揃えて演算子付きの2数を並べ、線の下に答え)で出力する。`add`・`sub`・`mul`(掛ける数が何桁でも対応。2桁以上のときは部分積の複数段表示、issue #10)・`div`(長除法、issue #11)に対応。

### 筆算形式の実装方針

横書き形式とは描画の考え方が根本的に異なる(桁ごとに列を揃える必要があり、問題ごとに1つの自己完結したブロックになる)ため、既存の「フィールドごとに1つの `Frame`」という設計は使わず、別経路で実装している:

- `get_vertical_digit_width`: `-a`/`-b` の範囲と選択演算子から、桁揃えに必要な桁数(列数)を算出する。ページ全体で共通の桁数を使うことで、問題ごとに列がガタつかないようにしている。`mul` は `a_max * b_max` を候補に入れており、これは掛ける数が何桁でも(部分積の各行を含めて)そのまま通用する桁数になる(下記「複数桁 mul」参照)。
- `get_vertical_calc_block`: 1問分のブロック((1+桁数)列の `Table`)を作る。基本形は3行(1行目=index+aの桁、2行目=演算子+bの桁(この行の下に線を引く)、3行目=答えの桁、`c_str=''` で空欄にできる)。掛ける数(`b_str`)が2桁以上の `mul` の場合は、2行目と最終行の間に `get_mul_partial_products` が返す部分積の行(桁数 = `len(b_str)`)を挿入し、最後の部分積行の下にもう1本線を引く。ブロックの行数はこの分だけ動的に増減する。
- `get_mul_partial_products(a_str, b_str)`: `b_str` の各桁(一の位から)に対して `a_str` を掛けた部分積を、一の位対応の行から順に返す純粋関数。`get_vertical_calc_block` から呼ばれ、各部分積は行位置(一の位からのシフト数)だけ右側を空白セルにして配置する。
- `pad_digits_to_width`: 数値文字列を右詰めで桁数分のセルに変換する(足りない桁は空文字)。
- `main()` 内、`is_vertical_ope`(`ini.command == 'ope' and ini.vertical`)が真のときだけ通る専用分岐(`nuts_calc.py` の frame 生成部と content 生成部それぞれに1箇所ずつ)で、`ini.columns` 個の等幅 `Frame` を作り、各 `Frame` に `ini.rows` 個の筆算ブロックを縦に並べた `Table` を流し込む。空欄版(`blank_columns`)を通常 PDF に、正答入り版(`filled_columns`)を `_read.pdf` に使う。`merge`/`with_bottom_answer`/`csv`/`debug` は既存の横書きパスと同じ変数・関数(`row_heights`/`get_bottom_results`/CSV 出力ブロック)を共有しているため、挙動は横書き版と揃っている。
- content 生成部のブロック描画ループは、行ごとに `operator_mark[row_idx][0]`(演算子記号)が `DIV_OPERATOR_SYMBOL`(`'÷'`)かどうかで `get_vertical_calc_block`(add/sub/mul)と `get_vertical_div_block`(div、issue #11)を分岐呼び出しする。この分岐は行単位のため、`-o add div` のような演算子混在指定も自然に動作する(add 行は3行ブロック、div 行は長除法ブロックとして、同一ページ・同一グリッド上に共存する)。

### 長除法(`div`)筆算ブロックの実装(issue #11)

`div` は add/sub/mul の3行固定レイアウトに乗らない(商・除数の囲み枠、複数段の引き算過程が必要)ため、専用の純粋関数とブロック描画関数を用意している:

- `compute_long_division_layout(a, b)`: 標準的な筆算長除法アルゴリズムの純粋関数。`a` の各桁を左から処理し、商の桁が非ゼロになるまで(または最後の桁に達するまで)剰余に畳み込む(先頭ゼロ抑制)。商が確定した時点で1ステップ発行し、`('partial', end_col, text)`(繰り下げ行、直前の余りと次の桁を連結した値。最初に発行されるステップでは省略される——それらの桁は被除数の行に既に見えているため)・`('product', end_col, text)`(その桁で引く値 = 商の桁 × 除数。この行の下に罫線を引く)・`('remainder', end_col, text)`(最終の余り。`calc_div` が整除する組しか生成しないため、実際には常に `'0'`)の3種のタプルを返す。`end_col` は `len(str(a))` 内での0始まり列番号で、その行の一番右の文字が揃う位置。`84÷7`(単純桁)・`120÷30`(先頭ゼロスキップ、最初のステップが3桁まとめて消費)・`875÷25`(g4-div 相当の3桁÷2桁)の3パターンで手計算検証済み(`tests/test_nuts_calc_data.py`)。
- `get_vertical_div_block`: `(2 + ステップ数)` 行 × `(1 + 桁数)` 列のブロックを作る。0行目=index + 商の桁(blank 版は空欄)、1行目=除数 + 被除数の桁(この行に `LINEAFTER`(列0の右、除数と被除数の間の縦線)と `LINEABOVE`(桁列の上、商と被除数を分ける横線 = 括弧の天井)を適用し、長除法の囲み枠を近似する)、2行目以降は `compute_long_division_layout` の各ステップ(`product` 行の下にのみ罫線)。各行のセル配置は `positioned_row`(ローカル関数)が `end_col` を基準に右詰めで計算する。`c_str == ''`(blank 版)は商・ステップ行を一切生成せず、除数・被除数の枠のみを表示する(`nuts_calc_tex.py` の `stage=0` と同じ方針、issue #21 参照)。
- ブロックの行数はステップ数に応じて動的に増減する(3桁÷2桁で最大6行程度)。これは複数桁 `mul` の部分積行と同じ「ブロックごとに行数が変わる」パターンを踏襲しており、新規のアーキテクチャ上のリスクはない(実機 PDF で行の重なり・欠けがないことを目視確認済み)。

### 重要な設計判断

- **対応演算を意図的に絞っている**: `mix`(`div` を含みうる)は `--vertical` では未対応。`_init()` で `VERTICAL_UNSUPPORTED_OPERATORS`(`mix` のみ)判定によりバリデーションし、非対応な組み合わせは PDF 生成前に `exit(1)` で弾く(`nuts_calc.py:257-270`)。掛ける数が2桁以上の `mul` は issue #9 の時点では未対応だったが、issue #10 で部分積の複数段表示に対応し、`_init()` 側の桁数制限は撤廃済み。`div` も issue #9 時点では未対応だったが、issue #11 で長除法ブロック(上記)を実装し撤廃済み。
- **複数桁 mul の部分積は幅の再計算なしに収まる**: 部分積(`a * 桁`)をシフトして得られる値は、常に合計(`a * b`)以下になる(各項の和が合計になるため)。したがって `get_vertical_digit_width` が合計向けに算出した桁数は、シフトを含めた部分積のどの行にもそのまま収まることが保証されており、部分積専用の幅計算は不要(issue #10 で確認済み)。
- **バリデーション失敗時は `exit(1)` を使う**: ファイル内の他の既存バリデーション(例: `-a option must be set.`)は引数なし `exit()` を使っており、実際には終了コード0を返すため、`web/backend/app.py` の `subprocess.run(..., check=True)` はこれを「成功」とみなしてしまう(既知の制限、下記参照)。今回追加したバリデーションはこの罠を避けるため明示的に `exit(1)` にしている。
- **ReportLab の `TableStyle` はコマンドの順序に依存する**: `get_vertical_calc_block` の `LINEBELOW`(区切り線、複数桁 mul では2本)は `GRID`(通常は透明なデバッグ用グリッド)より**後**に追加しなければならない。逆順にすると `GRID` の `width=0` 指定が同じセル境界の `LINEBELOW` を上書きして線が消える(実装中に実機で発見)。`get_vertical_div_block` の `LINEBELOW`(各 `product` 行の下)・`LINEAFTER`・`LINEABOVE`(囲み枠)も同じ理由で `GRID` より後に追加している(issue #11)。
- **筆算ブロックの高さは `slot_height * VERTICAL_BLOCK_HEIGHT_RATIO`(0.85)で計算し、外側の `Table` は `VALIGN: TOP`**: ブロックの行がスロットの100%を占めると隣接する問題同士が隙間なく密着して読みにくいため、上詰めにして下に余白を残している。行の高さはブロックの実際の行数(`len(data)`、複数桁 mul では部分積の分だけ増える)で均等割りするため、行数が多い問題ほど1行あたりは薄くなる(固定の `VERTICAL_BLOCK_ROWS` 定数は issue #10 で廃止)。
- **`calc_sub`/`calc_div` は無限リトライしない**: `nums_a`/`nums_b` の組み合わせに解(`a - b > 0` あるいは `a % b == 0`)が存在しない場合、`while True` のままだと永久にハングする。`MAX_OPERAND_RETRY_ATTEMPTS`(1000)回で打ち切り、`ValueError` を送出して `main()` の `try/except`(`failure()`)経由で明確に失敗させる(issue #4 Phase 5)。

## `ope` コマンドの `--intermediate`(途中式表示)

2桁×1桁の掛け算暗算法(`memo.md` 参照)を実装している。`get_operation_data` の `mul` 分岐で、`a`(2桁)の十の位・一の位それぞれに `b`(1桁)を掛けた値(2桁ゼロ埋め)を連結して4桁の数値(`aabb`)を作り、「`a × b => aabb => c`」の形で表示する(`nuts_calc.py:390-405`)。この4桁の数値を「最初の2桁+3桁目、それに4桁目を付け加える」という手順(STEP2、暗算する側が頭の中で行う)で3桁に変換すると、常に元の `a × b` と一致する(`10*A+B` の恒等式より)。

この技法は `b` が1桁であることが前提(`single_c` = `b` の十の位は使われず、常に0という前提)。`_init()` は `--intermediate` 指定時に `b_max` が1桁を超えると `exit(1)` で拒否する(issue #4 Phase 3)。

## 統合ポイント

- 呼び出し元: CLI 直接実行(`python3 nuts_calc.py <paper_size> <command> ...`)、`factory.sh`(バッチ生成)、`web/backend/app.py`(Web UI 経由)。
- 呼び出し先: なし(ReportLab で完結)。

## 注意事項・既知の制限

- `--vertical` は `ope` コマンドの `add`/`sub`/`mul`(掛ける数は何桁でも可)/`div`(長除法)に対応。`mix`/`--intermediate` との併用は非対応(上記参照)。
- `--intermediate` は `b` が1桁の場合のみ対応(上記参照)。
- `--a-min`/`--a-max`(または `--b-min`/`--b-max`)を同値で直接指定した場合、`ope` の乱数生成は単一値リストにフォールバックするため問題なく動作する(issue #4 Phase 6 で修正済み。以前は CPython の small-int キャッシュ範囲外の値で `IndexError` になっていた)。
- `-r`/`-c` は1以上必須(`_init()` でバリデーション、issue #4 Phase 9 関連で追加)。
- 出力ファイル名の導出(`OUTFILE_NAME_READ`/`OUTFILE_NAME_CSV`)は `os.path.splitext(ini.out_file)` でベース名と拡張子を分離し、ベース名に `_read.pdf`/`.csv` を付け足す。以前は `str.rstrip('.pdf')`(接尾辞除去ではなく文字クラス除去)を使っており、`.pdf` の直前が `.`/`p`/`d`/`f` のいずれかで終わるファイル名(例: `output_add.pdf`)だと壊れていた(issue #15 で修正済み)。
- `tests/`(pytest)に単体テスト・CLI 経由の end-to-end テストが存在する。実機での CLI 実行と生成 PDF の目視確認も引き続き検証手段として有効。

## 変更履歴(git log より自動生成)

- 2a7cd15 feat(#10): support multi-digit multiplier in vertical mul output
- 4aaf251 fix(#15): fix output filename derivation to use os.path.splitext
- cfea9ed fix(#4): fix 9 logic bugs found in CLI, web backend, and frontend
- 0a11eaf feat(#9): add vertical (written-calculation) output format for ope command
- 5466cdb refactor: Clean up old script and apply flat design to frontend
- d9fc0a3 refactor: Rename 100masu.py to nuts_calc.py and remove setup.py
