# `backend/nuts_calc.py`

## 目的・役割

計算ドリル PDF 生成 CLI 本体。`argparse` でコマンドライン引数を解析し(`_init`)、ReportLab の `Frame`/`Table` を組み立てて PDF(と任意で CSV)を出力する(`main`)。対応する `command` は `ope`(四則演算)・`com`(補数)・`100`(100マス)・`99`(九九)・`aBc`・`squ`(平方数)・`pi`(円周率計算)の7種類。

## 動作の概要

- `_init()` が引数を検証・正規化して `argparse.Namespace` を返す。`command` ごとに `-a`/`-b`(桁数指定)から `a_min`/`a_max`/`b_min`/`b_max`(実際の数値範囲)を導出する(`nuts_calc.py:232-247` 付近)。`ope` 以外の `command` では `--intermediate` を渡してもこの導出は行われない(`command == 'ope'` のみが対象、issue #4 Phase 1)。`100` コマンドも独自にこの導出を行う(下記)。
- `_init()` は他に以下をバリデーションする: `com`/`99`/`squ`/`pi` の `-a` 必須(未指定時は `exit(1)`、issue #37 で `exit()` から修正)、`100` の `-a`/`-b` は3桁まで(未指定/不正時は `exit(1)`、同じく issue #37 で修正)、`--intermediate` は第2引数(`b`)が1桁の場合のみ許可(`args.b_max > SINGLE_DIGIT_MAX` なら `exit(1)`、issue #4 Phase 3)、`-r`/`-c` は `MIN_ROWS_OR_COLUMNS`(=1)以上必須(`exit(1)`)。
- `100` コマンドの `a_min`/`a_max`/`b_min`/`b_max` 導出(`nuts_calc.py:237-247`)は、`-a`/`-b` 未指定時のデフォルト適用(`a_value = 1`)→ 3桁超えチェック → `set_min_max_value()` の無条件呼び出し、という順序で行う(issue #43)。以前は `set_min_max_value()` の呼び出しが `is None` 分岐の内側にあり、`-a 2`/`-a 3` のように明示指定すると導出自体がスキップされ、`a_min`/`a_max` が argparse のデフォルト(1, 9)のまま残る(1桁の表になる)不具合があった。`nuts_calc_tex.py:213-230` は元々「`a_value`/`b_value` が `None` でなければ無条件に導出」という構造でこの不具合を持たない。
- `main(ini)` は用紙サイズ・コマンドに応じて `Frame` レイアウトを組み立て、`get_vertical_contents_raw_dataset` で問題データを生成し、`command` ごとの描画ロジックで PDF 2種(通常版・解答版 `_read.pdf`)を作る。`ini.merge` が真の場合は1ファイルに問題ページ→解答ページを交互に収める(`next_content` による1ページ遅延の仕組み)。
- `nums_a`/`nums_b`(問題の種となる数値集合)は `ini.a_min`/`ini.a_max` などから `range(min, max + 1)`(上限含む)で構築する。`min == max` の場合は `random.sample` を経由せず単一要素リストにする分岐があり、この等価判定は `!=`(恒等比較 `is not` ではない)を使う(issue #4 Phase 2, 6)。同様の `range(min, max + 1)` 構築は `100` コマンド側にも独立して存在する。

## `ope` コマンドの出力形式(横書きのみ)

`ope` コマンドは横書き形式(`a + b = c` を1行で表示)のみに対応する。`get_operation_data` → `get_vertical_contents` → `add_vertical_frame_set` の組み合わせで、問題の各要素(index/a/演算子/b/=/answer)をそれぞれ専用の縦長 `Frame` に敷き詰める(`nuts_calc.py` の `main()` 内、frame 生成部と content 生成部それぞれ1箇所)。これら3関数は「vertical」を冠しているが、`ope`/`com`/`99`/`squ`/`pi`/`aBc` の全コマンドが共有する横書き描画基盤であり、特定コマンド専用ではない(下記「筆算(`--vertical`)形式の削除」参照)。

筆算(縦書き、`--vertical`)形式は issue #46 で `nuts_calc.py` から削除された。書き取り式の計算ドリルが必要な場合は `nuts_calc_tex.py`(LaTeX `xlop`/`longdivision` レンダリング)を使う。`backend` はどちらのスクリプトも `NUTS_CALC_RENDERER` env 変数で切り替え可能で、`frontend/spa` は `GET /renderer-info`(`backend/app.py`)で有効なレンダラーを判定し、筆算関連の UI を `nuts_calc_tex.py`(`latex`)選択時のみ表示する([[../../frontend/spa/src/GradeDrills.jsx]]/[[../../frontend/spa/src/CustomGenerator.jsx]] 参照)。

### 筆算(`--vertical`)形式の削除(issue #46)

`get_vertical_digit_width()` が桁幅を `mix` 展開前の生の `--operator` 引数から算出しており(問題ごとに実際に解決される `add`/`sub`/`mul`/`div` を見ていなかった)、`--vertical` と `mix` の組み合わせを安全にサポートできないという設計上のギャップが issue #41 の調査で見つかった。このギャップを個別に修正するのではなく、`nuts_calc_tex.py` がすでにより堅牢な筆算レンダラー(LaTeX `xlop`/`longdivision`)として実装済みであったため、`nuts_calc.py` からは `--vertical` 機能自体を削除し、以後の筆算出力は `nuts_calc_tex.py` に一本化する判断がなされた。

削除されたもの: `--vertical` CLI 引数とその `_init()` バリデーション、`VERTICAL_UNSUPPORTED_OPERATORS`/`VERTICAL_INDEX_COLUMN_RATIO`/`VERTICAL_BLOCK_HEIGHT_RATIO`/`DIV_OPERATOR_SYMBOL` の4定数、`pad_digits_to_width`/`get_vertical_digit_width`/`get_mul_partial_products`/`compute_long_division_layout`/`get_vertical_calc_block`/`get_vertical_div_block` の6関数、`main()` 内の `is_vertical_ope` 分岐(frame 生成部・content 生成部の2箇所)。

**削除対象の特定について**: `add_vertical_frame_set`/`get_vertical_contents_raw_dataset`/`get_vertical_contents` は名前に反して `--vertical` 専用ではなく、全コマンド共通の横書き描画基盤であることを実装前に呼び出し箇所を全て追跡して確認済み(`add_vertical_frame_set` は `is_vertical_ope` 分岐と全コマンド共通の `elif` 分岐の両方から呼ばれていた、`get_vertical_contents_raw_dataset`/`get_vertical_contents` は `is_vertical_ope` 判定より前後で無条件に呼ばれていた)。この3関数は削除せず維持している。

## `ope` コマンドの `--intermediate`(途中式表示)

2桁×1桁の掛け算暗算法(`memo.md` 参照)を実装している。`get_operation_data` の `mul` 分岐で、`a`(2桁)の十の位・一の位それぞれに `b`(1桁)を掛けた値(2桁ゼロ埋め)を連結して4桁の数値(`aabb`)を作り、「`a × b => aabb => c`」の形で表示する(`nuts_calc.py:390-405` 付近)。この4桁の数値を「最初の2桁+3桁目、それに4桁目を付け加える」という手順(STEP2、暗算する側が頭の中で行う)で3桁に変換すると、常に元の `a × b` と一致する(`10*A+B` の恒等式より)。

この技法は `b` が1桁かつ演算子が `mul` であることが前提(`single_c` = `b` の十の位は使われず、常に0という前提。`mul` 以外では暗算法自体が成立しない)。`_init()` は `--intermediate` 指定時に以下を `exit(1)` で拒否する:
- `--operator` が `['mul']` 以外(`nuts_calc.py:249-251`、issue #42)。以前は `main()` 内で `command == 'ope'` 時に無条件で `operator = ['mul']` に上書きしており(削除済み)、`--operator add --intermediate` のような組み合わせでも `--operator` の指定を無視して黙って `mul` の問題を生成していた。`nuts_calc_tex.py:261-262` は同じ組み合わせを実装当初から明示的に拒否しており、この非対称を解消した。
- `b_max` が1桁を超える場合(`nuts_calc.py:253-255`、issue #4 Phase 3)。

## 重要な設計判断

- **バリデーション失敗時は `exit(1)` を使う**: `com`/`99`/`squ`/`pi`(`-a` 必須)・`100`(`-a`/`-b` は3桁まで)のバリデーションは、かつて引数なし `exit()`(終了コード0)を使っており、`backend/app.py` の `subprocess.run(..., check=True)` がこれを「成功」とみなしてしまう不具合があった(issue #37 で `exit(1)` に修正済み)。ファイル内の他のバリデーションは元から `exit(1)` を使っており、この2箇所だけが例外的に `exit()` になっていた。
- **`calc_sub`/`calc_div` は無限リトライしない**: `nums_a`/`nums_b` の組み合わせに解(`a - b > 0` あるいは `a % b == 0`)が存在しない場合、`while True` のままだと永久にハングする。`MAX_OPERAND_RETRY_ATTEMPTS`(1000)回で打ち切り、`ValueError` を送出して `main()` の `try/except`(`failure()`)経由で明確に失敗させる(issue #4 Phase 5)。
- **`99`(九九)の乗数 `b` は常に1〜9に収める**: `get_fixed_format_data()` の `mode == '99'` 分岐(`nuts_calc.py:492-493`)は `num_list = [i % SINGLE_DIGIT_MAX for i in range(order)]`(既存定数 `SINGLE_DIGIT_MAX = 9` を再利用)で乗数列を生成する。`order`(1列あたりの行数、`get_vertical_contents_raw_dataset`: `order = rows`)が9を超える場合、10問目以降は `×1` から折り返して繰り返す。以前は `num_list = [i for i in range(order)]` で `b` が `order` に応じて9を超え(例: `frontend/web` の20問プリセットは `rows=10, columns=2` のため `b` が1〜10まで生成され、実在しない「×10」が出題されていた)、issue #149 で修正した。`squ`/`pi` 分岐(同じ関数、別の `num_list` 構築)はこの折り返しの対象外。`nuts_calc_tex.py::generate_kuku_problems` は独立実装で、`order` が9を超えても折り返さない設計(issue #24 で意図的に確認済み、[[nuts_calc_tex.py]] 参照)のままであり、本修正では変更していない。

## 統合ポイント

- 呼び出し元: CLI 直接実行(`python3 nuts_calc.py <paper_size> <command> ...`)、`factory.sh`(バッチ生成)、`backend/app.py`(`backend/renderers.py` 経由、Web UI 経由)。
- 呼び出し先: なし(ReportLab で完結)。

## 注意事項・既知の制限

- `--vertical`(筆算形式)は issue #46 で削除済み。書き取り式の計算ドリルが必要な場合は `nuts_calc_tex.py` を使う([[nuts_calc_tex.py]] 参照)。
- `--intermediate` は `-o mul`(単一の `mul` 演算子)かつ `b` が1桁の場合のみ対応(上記参照)。`-o` を省略するとデフォルトの `operator=['add']` になるため、`--intermediate` を使う呼び出し元は `-o mul` を明示する必要がある(issue #42)。
- `--a-min`/`--a-max`(または `--b-min`/`--b-max`)を同値で直接指定した場合、`ope` の乱数生成は単一値リストにフォールバックするため問題なく動作する(issue #4 Phase 6 で修正済み。以前は CPython の small-int キャッシュ範囲外の値で `IndexError` になっていた)。
- `-r`/`-c` は1以上必須(`_init()` でバリデーション、issue #4 Phase 9 関連で追加)。
- 出力ファイル名の導出(`OUTFILE_NAME_READ`/`OUTFILE_NAME_CSV`)は `os.path.splitext(ini.out_file)` でベース名と拡張子を分離し、ベース名に `_read.pdf`/`.csv` を付け足す。以前は `str.rstrip('.pdf')`(接尾辞除去ではなく文字クラス除去)を使っており、`.pdf` の直前が `.`/`p`/`d`/`f` のいずれかで終わるファイル名(例: `output_add.pdf`)だと壊れていた(issue #15 で修正済み)。
- `tests/`(pytest)に単体テスト・CLI 経由の end-to-end テストが存在する。実機での CLI 実行と生成 PDF の目視確認も引き続き検証手段として有効。
- `backend/tests/test_nuts_calc_init.py` に9件の既存失敗テストがある(`exit()` → `exit(1)` 修正(issue #37)後もテスト側の期待値が `code is None` のままになっている stale なテスト)。issue #46 の変更とは無関係で、`main` ブランチでも再現することを確認済み。

## 変更履歴(git log より自動生成)

- b6cb2af fix(#149): cap kuku multiplier at 1-9 in nuts_calc.py's 99 command
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
