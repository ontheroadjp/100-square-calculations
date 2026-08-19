# `backend/nuts_calc_tex.py`

## 目的・役割

`nuts_calc.py`(ReportLab ベース)とは**完全に独立した**、LaTeX(TeX)でレンダリングする計算ドリル PDF 生成 CLI のプロトタイプ。issue #19(親トラッキング issue)で計画されている全7コマンド再実装のうち、Phase 1(issue #20)で CLI 引数・ページ/PDF レイアウト・TeX ビルドパイプライン・CSV 出力という共通基盤を実装し、Phase 2(issue #21)で `ope` コマンド(四則演算 add/sub/mul/div/mix、横書き・`--vertical`・`--intermediate`)、Phase 3(issue #22)で `com` コマンド(補数: `a + __ = target`)、Phase 4(issue #23)で `100` コマンド(100マス計算: 11×11 の加算表)、Phase 5(issue #24)で `99` コマンド(九九: 固定の1段 × `--rows`×`--columns` 問、`--descend`/`--reverse`/`--shuffle` の並び替え)、Phase 6(issue #25)で `aBc` コマンド(暗算: 4桁の数字列 `abcd` を2桁ずつのペア `ab`/`cd` に分けて変換する暗算ステートメント)、Phase 7(issue #26)で `squ` コマンド(二乗数: `-a` から始まる整数列を `a × a` の形で出題、`--descend`/`--reverse`/`--shuffle` の並び替えは `99` と共通)、Phase 8(issue #27)で `pi` コマンド(円周率倍: `-a` から始まる整数列を `a × 3.14` の形で出題、並び替えオプションは `squ` と共通)を実装した。これで issue #19 が計画する全7コマンドの実装が完了している。issue #94 では、小学5年生の数の性質ドリル3種(偶数・奇数判定、倍数列挙、約数列挙)に対応する `evenodd`/`multiples`/`divisors` の3コマンドを追加し、issue #95 では2つの整数からLCM/GCDを出題する `lcm`/`gcd` を追加し、issue #96 では分数・小数の表現変換ドリル5種(約分・通分・分数を小数に直す・小数を分数に直す・割り算の答えを分数で表す)に対応する `simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac` の5コマンドを追加した(いずれも詳細は後述)。

`nuts_calc.py` とは import 等のコード共有を一切行わない(`nuts_calc.py` 側も変更しない)。将来的に両者を同じ CLI 契約で切り替えられるラッパーを作る前提のため、引数体系は `nuts_calc.py` の `_init()` に似せているが、実装は完全に別物。問題生成ロジック(`calc_add`/`calc_sub`/`calc_mul`/`calc_div`/`generate_ope_problems`)も `nuts_calc.py` の `get_operation_data` 等とは独立に再実装している(意味論は似せているが、コードは共有しない)。issue #65 では LaTeX 固有の8番目のコマンド `frac` を追加し、分数の四則演算を実装した。issue #67 では `ope` コマンドに LaTeX 固有のオプション `--use-parentheses` を追加し、かっこ付き3項式(`(a op b) op c` または `a op (b op c)`)の出題を実装した。issue #69 では `ope` コマンドに LaTeX 固有のオプション `--missing-value` を追加し、`a op b = c` のうち `a`/`b`(演算子の両オペランド)いずれか1つを枠で隠す虫食い算(missing-number)の出題を実装した。issue #71 では `ope` コマンドに `--terms`/`--terms-min`/`--terms-max`/`--mixed-operators` を追加して2項固定だった `ope` を任意項数(2〜12)の多項演算に一般化するとともに、`--use-parentheses` を固定3項・2形状(`(a op b) op c`/`a op (b op c)`)からN項(N>=3)のランダムな2分木構造に一般化した。issue #76 では `ope` コマンドに `--a-decimal-places`/`--b-decimal-places` を追加して小数の四則演算(横書きのみ)に対応するとともに、LaTeX 固有の9番目のコマンド `mixed` を追加し、整数・小数・分数を混在させた任意項数の四則演算(答えは常に厳密な分数)を実装した。issue #78 では2項整数 `ope` の加減算へ繰り上がり・繰り下がり条件を追加し、1年生向けWebカードから利用できるようにした。

### `ope --carry-borrow`/`--no-carry-borrow`/`--mixed-carry-borrow`(issue #78, #81)

- 3フラグは argparse の排他グループで、内部では `carry_mode='required'|'none'|'mixed'` に正規化する。2項の `ope` と `add`/`sub` のみ対応し、`--mixed-carry-borrow` は `-o add sub` の両方を必須とする。かっこ・虫食い算・多項との併用は `_init()` が拒否する(`nuts_calc_tex.py:626-639`)。
- **小数オペランドとの併用(issue #113)**: `--a-decimal-places`/`--b-decimal-places` との併用は当初 `_init()` が一律拒否していたが、issue #113 で緩和した。`addition_has_carry`/`subtraction_has_borrow`/`calc_add`/`calc_sub` はいずれも「スケールされた整数」(`a`/`b` そのもの)に対して桁単位で動作し、小数桁数という概念を一切持たない(`generate_ope_problems` の docstring、`nuts_calc_tex.py:1367-1371` 参照)。加減算では `a_decimal_places == b_decimal_places` が別の汎用バリデーションで既に強制されている(`nuts_calc_tex.py:680`、`a_decimal_places != b_decimal_places` の場合は `-o mul`/`-o div` の単独指定を要求)ため、桁が揃っている限り整数の場合と全く同じロジックで正しく繰り上がり/繰り下がりを判定できる。`ope -o div` 専用の `--remainder` 系(下記)は同種の制約を issue #113 の対象外として維持している。
- issue #81 で旧 `--carry`/`--no-carry`/`--mixed-carry` は後方互換エイリアスを設けず削除した。`ArgumentParser(allow_abbrev=False)` により、旧名が新フラグの省略として受理されることも防ぐ(`nuts_calc_tex.py:115-123`)。
- `addition_has_carry()`/`subtraction_has_borrow()` が各桁を下位から調べる。`calc_add(..., carry)` は指定範囲を最大1000回優先し、成立しなければ範囲を無視して元レンジの桁幅を保つ代表値を合成する。フラグ未指定(`carry=None`)では受け取った初回抽選値を即座に返し、従来の乱数消費と結果を変えない(`nuts_calc_tex.py:834-897`)。
- `calc_sub(..., borrow=True)`(issue #92 で全面改訂)は `calc_add(..., carry=True)` と同じパターンに合わせた: まず呼び出し側が渡した `nums_a`/`nums_b`(=設定された `a_min`/`a_max`/`b_min`/`b_max`)の範囲内で最大1000回、正の結果かつ繰り下がる組を再抽選し、尽きたら `build_borrow_fallback(a_width, b_width)` へ決定的にフォールバックする。`build_borrow_fallback` は `a` を「`b` より1桁以上広い(最低2桁)」幅に広げたうえで `a=10^(a_width-1)`(1の位0)、`b`(1の位を非0に固定)を合成し、1の位の比較だけで繰り下がりと正の結果を保証する(`build_addition_fallback` の桁幅保存フォールバックと対になる設計)。**唯一の例外**: `nums_a`/`nums_b` が両方とも1桁(1〜9)の場合、正の結果を持つ繰り下がり組がそのレンジ内に一切存在しえないため、この形状(Web層の1年生 mixed-carry プリセットが `add`/`sub` で `a_min=1/a_max=9`・`b_min=1/b_max=9` を共有しているために踏む唯一の実使用パターン)に限り、旧来どおり `BORROWING_MINUENDS`(10〜19)/`BORROWING_SUBTRAHENDS`(1〜9)からの再抽選(尽きれば `(10, 1, 9)`)を維持する。これにより、`a_min=10/a_max=19` を明示設定する単独 borrow プリセットは(元々 `nums_a` が 10〜19 なので)一般経路の再抽選だけで従来と同じ分布を再現し、`a_min=1/a_max=9` の mixed-carry プリセットは特例経路によって挙動が完全不変になる。`borrow=False` は指定範囲を優先後、正で繰り下がらない代表値へフォールバックする。`borrow=None` は従来の「答えが正」だけを保証する経路である(`nuts_calc_tex.py:979-1049`)。
- `generate_ope_problems()` は `required` なら各加算で繰り上がり、各減算で繰り下がりを必須にし、`none` なら両方を禁止する。`mixed` は加算を無条件抽選して繰り上がりあり/なしを混ぜ、減算ごとに繰り下がりなし/ありを抽選する(繰り下がりあり時の実際のサンプリング挙動は `calc_sub` 参照、`nuts_calc_tex.py:1151-1196`)。
- **`--result-max` は `ope` の全式形式に共通する最終結果上限**: 1以上の整数を受け取り、通常2項の add/sub/mul/div/mix、かっこ付きN項式、平坦なN項式、虫食い算のいずれでも最終結果が上限以下になるまで式全体を再抽選する。通常2項の小数計算だけは内部整数 `c` ではなく、`ope_result_decimal_places()` で解釈した表示値を基準に判定する。条件を `MAX_OPERAND_RETRY_ATTEMPTS` 内に満たせなければ `ValueError` とし、上限を無視した問題は生成しない。`ope` 以外または1未満の値は `_init()` で拒否する(`nuts_calc_tex.py:193-196,620-624,1341-1404,1769-1810,1991-2033,2135-2166`)。

### `ope --remainder`/`--no-remainder`/`--mixed-remainder`(issue #91)

- 3フラグは `carry_group` と同じ形の argparse 排他グループで、内部では `remainder_mode: RemainderMode = Literal['required', 'none', 'mixed']` に正規化する。`ope -o div` の単独指定のみ対応し(`args.operator != ['div']` を拒否)、かっこ・虫食い算・多項・`--intermediate`・小数(`--a-decimal-places`/`--b-decimal-places`)との併用は `_init()` が拒否する。フラグ未指定時は `remainder_mode=None` で、issue #91 以前と完全に同じ「常に割り切れる」挙動を保つ。
- `calc_div(a, b, nums_a, nums_b, remainder=None)`: `remainder` が真値でない(`None`/`False`)場合は元の「`a % b == 0` になるまで再抽選し、尽きたら `find_exact_division_pair` へ決定的フォールバック」という経路をそのまま通る(コード自体は分岐が増えただけで挙動は無変更)。`remainder=True` の場合は対称な新経路(「`a % b != 0` になるまで再抽選し、尽きたら `find_remainder_division_pair` へ決定的フォールバック」)を通る。戻り値は既存と同じ `(a, b, c)` の3要素(`c` は常に `a // b`)で、呼び出し側の型は変わらない。
- `find_remainder_division_pair(nums_a, nums_b)`: `find_exact_division_pair` と対になる決定的フォールバック。倍数だけを飛び飛びに走査する `find_exact_division_pair` の最適化(非倍数は「大半」なのでこの最適化は不要)とは異なり、`nums_b` × `nums_a` を単純に総当たりして最初に見つかった非倍数ペアを返す。
- `generate_ope_problems(..., remainder_mode=None)`: `operator == 'div'` かつ `remainder_mode is not None` の場合だけ `CALC_FUNCTIONS['div']` を経由せず `calc_div` を直接呼ぶ(`carry_mode` が `add`/`sub` に対して行っているのと同じパターン)。`'mixed'` は問題ごとに `random.choice((False, True))` で余りあり/なしを抽選する(`carry_mode='mixed'` の減算と同じ考え方)。`OpeProblem.remainder`(既定0)は演算子が `'div'` のときだけ `a - b * c` から導出し、それ以外の演算子では常に0のまま(`calc_div` の戻り値だけを見れば済み、`remainder_mode` の値そのものを保持する必要がない)。
- **日本語テキスト「あまり」ではなく `\cdots`(または `build_ope_bottom_answer_tex` ではプレーンASCIIの `...`)を使う理由**: 本ファイルは素の `pdflatex`(CJK/日本語フォントパッケージ未読み込み、`nuts_calc_tex.py:677-684` のプリアンブル参照)でコンパイルしており、日本語グリフを含む文字列を渡すと `pdflatex` が `Fatal error occurred, no output PDF file produced` で失敗する(実機で確認済み)。`\cdots`(数式モード)または `...`(`build_ope_bottom_answer_tex` はテキストモードのため素の3ピリオド)は、日本の教科書でも使われる「3⋯2」という余り表記の慣用的な省略形であり、フォント追加なしで安全に描画できる代替として採用した。`build_horizontal_block_tex`(横書き)/`build_ope_bottom_answer_tex`(下部解答欄)の双方で、`problem.remainder` が0のとき(既定・非div演算子を含む)は追加の出力を一切行わないため、issue #91 以前の出力と完全に同一(回帰なし)。
- `build_ope_csv_rows` は `remainder` 列(`problem.remainder`、常にプレーン `int`)を末尾に追加した7列 `[page_number, index, a, operator, b, c, remainder]` になった(非div演算子・余りなしの割り算では常に0)。旧6列を前提にした呼び出し元がある場合は末尾列を無視すれば従来通り読める。

### `frac` コマンド(issue #65、帯分数対応は issue #112)

- `_init()` は `--numerator-digits`/`--denominator-digits`(各1〜3)、`--same-denominator`/`--different-denominators`(排他)、`--proper-operands`、`--proper-result` を受け付ける。分子の桁数が分母を上回る状態で真分数を要求するなど、生成不能な代表的組み合わせを事前に拒否する(`nuts_calc_tex.py:155-184,305-328`)。
- `FractionOperand` は出題時の未約分の分子・分母を保持し、`FractionProblem.c` は標準ライブラリ `fractions.Fraction` による厳密な約分済み解答を保持する。これにより、例えば問題の `2/4` はそのまま表示しつつ答えは `1/2` と表示できる(`nuts_calc_tex.py:1338-1361,1431-1438`)。
- `generate_fraction_problems()` は `add`/`sub`/`mul`/`div`/`mix` を問題ごとに解決し、答えが正になる問題だけを生成する。`--proper-result` はさらに答えを1未満へ制限し、同分母・異分母条件も生成時に保証する。条件を1000回以内に満たせない場合は明確な `ValueError` にする(`nuts_calc_tex.py:1394-1434`)。
- 問題・解答は `\frac` と `\displaystyle` で横書き表示する。通常の問題PDF、`_read.pdf`、`--merge`、`--with-bottom-answer`、`--csv` の全出力経路に対応する。答えの文字色は既存コマンドと同じ黒である(`nuts_calc_tex.py:1441-1500,1510-1565`)。
- 学年別配置の根拠となる文部科学省資料は `docs/reference/` に保存する。Webカードは LaTeX レンダラー時のみ表示される([[frontend/web/src/drillPresets.js]]、[[frontend/spa/src/drillPresets.js]]、[[frontend/spa/src/GradeDrills.jsx]])。

#### 帯分数(帯分数を含む/まぜる)対応(issue #112)

- `docs/uiux/calculation_drill_menu_parameters_v1.md:60-61,74-75` の「数の種類: 分数 / 帯分数を含む / まぜる」設定に対応するため、`compare` コマンド専用だった `--a-fraction-form`/`--b-fraction-form`(`proper`/`improper`/`mixed`/`mix`)を `frac -o add`/`sub` の単独指定にも拡張した。`_init()` は `frac` では `improper` を拒否し(帯分数ドリルは 真分数/帯分数 の2形式のみで、生の仮分数オペランドは curriculum doc に存在しない)、複数演算子・`mix` 演算子との併用も拒否する(帯分数の意味論を単一の add/sub に限定するため)(`nuts_calc_tex.py:543-558` 付近)。
- `FractionOperand.whole`(既定0)が整数部を保持する。`.value` は `whole*denominator+numerator` から `Fraction` を計算するため、`whole=0` の既存呼び出し元(`simplify`/`commondenom`/`mixed`/`divfrac` など)は無変更(`nuts_calc_tex.py` の `FractionOperand` 定義直後)。
- 新規 `random_fraction_arithmetic_operand(form, ...)`: `form='mix'` は `compare` の `COMPARISON_FORMS`(`proper`/`improper`/`mixed`)とは異なる `FRACTION_ARITHMETIC_MIXED_NUMBER_FORMS = ('proper', 'mixed')` から抽選する(`improper` を含めない)。`form='proper'` は既存の `random_fraction_operand(..., proper_operands, denominator)` へそのまま委譲するため、`a_fraction_form`/`b_fraction_form` を指定しない(既定 `'proper'`)場合の `generate_fraction_problems()` は issue #112 以前と完全に同一のオペランドを生成する(回帰なし)。`form='mixed'` は真分数部(`random_fraction_operand(..., True, ...)`)に `whole=random.randint(1, 9)` を付与する。
- `generate_fraction_problems()` は `a_form`/`b_form`(既定 `'proper'`)を追加し、`mixed_number_display = a_form != 'proper' or b_form != 'proper'` を `FractionProblem` に記録する。a/b は独立に(`compare` の `--a-fraction-form`/`--b-fraction-form` と同じ設計で)抽選されるため、1問内で片方だけ帯分数になる組み合わせも生成しうる。
- 新規 `fraction_to_mixed_number_tex()`: `FractionOperand.whole`(存在しない `Fraction` では `getattr` で0扱い)を起点に `divmod(numerator, denominator)` で整数部を確定し、`whole{fraction_tex}`(`compare` の `comparison_operand_to_tex` と同じ、空白なしの連結)を返す。既存の `fraction_to_tex()` 自体は一切変更していない(`divfrac` が `fraction_to_tex(FractionOperand(a, b))` で意図的に未約分の仮分数のまま表示する既存契約を壊さないため)。
- `build_fraction_block_tex`/`build_fraction_bottom_answer_tex` は `problem.mixed_number_display` が真の問題だけ `fraction_to_mixed_number_tex` を使う(オペランドだけでなく答えも対象)。偽の問題(既定)は従来通り `fraction_to_tex` を使うため、`--a-fraction-form`/`--b-fraction-form` 未指定時の出力は無変更。
- `build_fraction_csv_rows` は `a_whole`/`b_whole` を末尾に追加した11列(`[page_number, index, a_num, a_den, operator, b_num, b_den, c_num, c_den, a_whole, b_whole]`)になった。`whole=0` が既定のため、帯分数を使わない問題では末尾2列が常に0になるだけで既存の9列分は無変更(issue #91 の `remainder` 列追加と同じ、末尾追加による後方互換パターン)。
- `build_fraction_pages` は `ini.a_fraction_form`/`ini.b_fraction_form` を `generate_fraction_problems` へそのまま渡す。

### `compare` コマンド(issue #83)

- 分数2つの間にある枠へ不等号を書く比較ドリルを生成するLaTeX専用コマンド。`--comparison-pattern` は `same-denominator`（同分母・異分子）、`same-numerator`（同分子・異分母）、`different-denominators`（異分母）を選ぶ。分子・分母の桁数は既存の `--numerator-digits`/`--denominator-digits`（各1〜3）を共用する（`nuts_calc_tex.py:130-233,439-473`）。
- 左右の表示形式は `--a-fraction-form`/`--b-fraction-form` で独立に `proper`/`improper`/`mixed`/`mix` から選ぶ。`mixed` は整数部1〜9と真分数部を持つ帯分数、`mix` は問題ごとに3形式から抽選する。標準ライブラリ `Fraction` により帯分数を含む値を厳密に比較し、等値は出題しない（`nuts_calc_tex.py:2674-2758`）。
- blank PDF は既存の `BOXED_BLANK_TEX` を比較記号位置に置き、解答PDFは `<` または `>` を出力する。CSVは整数部・分子・分母・関係記号を左右それぞれ保存する。`main()` は専用ページ生成・CSV出力へ分岐する（`nuts_calc_tex.py:2761-2816,3001-3065`）。
- 分数四則専用フラグと比較専用フラグは `_init()` で相互に拒否し、既存の `frac`/`mixed` の挙動を変えない（`nuts_calc_tex.py:452-473`）。

### `ope --a-decimal-places`/`--b-decimal-places`(issue #76、`--vertical` との併用は issue #134)

- `_init()` は `command == 'ope'` のときのみこれらを許可する(`command != 'ope'` の場合は拒否)。`--intermediate`/`--use-parentheses`/`--missing-value`/`--terms`系との併用は引き続き全て拒否する(N項系の infra を一切共有しない、独立した拡張)。値域は `MIN_DECIMAL_PLACES`(0)〜`MAX_DECIMAL_PLACES`(2)。
- **`--vertical` との併用(issue #134)**: 当初 `_init()` が一律拒否していたが、`xlop`(add/sub/mul)・vendor済み `longdivision`(div、divisor が整数の場合)がいずれも小数点付きオペランドをそのまま正しく描画できることを実機の `pdflatex` コンパイルで確認できたため、緩和した。`build_vertical_block_tex()`(後述)が横書きビルダーと同じ `format_decimal_value()` を経由するよう変更されており、`places<=0` では従来と出力が変わらない(後方互換)。ただし `'div'` オペレーターかつ `b_decimal_places > 0`(除数が小数)の組み合わせだけは引き続き明示的に拒否する: vendor済み `longdivision` の `\intlongdivision` は除数に整数しか受け付けず(`Divisor 'X.X' is not an integer` エラー、実機確認済み)、除数の小数点をシフトして整数化する回避策(教科書的には標準の手法だが、`--vertical` の表示内容が横書きと異なる数値になってしまう)はユーザーの意向で不採用とした。この組み合わせ(小数×小数の割り算)の筆算対応は issue #180(agenda)で検討中、対応方針が決まるまで実装しない(`nuts_calc_tex.py:746-757` 付近)。
- **設計の核心**: `OpeProblem.a`/`b`/`c` は常に `calc_add`/`calc_sub`/`calc_mul`/`calc_div` が返す生の整数のまま保持し(この4関数自体は一切変更していない)、`a_decimal_places`/`b_decimal_places`(既定 0)という表示用メタデータだけを新設した。`format_decimal_value(raw, places)` が `raw` を文字列化してから小数点を挿入するだけ(整数演算・文字列操作のみ、浮動小数点は一切使わない)なので、`a`/`b` は「スケールされた整数」として生成・検証され、表示時にだけ `10^places` で割った位置に小数点を置く。これにより、加減算は `a_decimal_places == b_decimal_places` の場合そのまま整数加減算が正しい答えになり(`calc_sub` の正の結果保証がそのまま「引き算の答えが正」の保証になる)、乗算は `c` の小数桁数が `a_decimal_places + b_decimal_places`、除算は `a_decimal_places - b_decimal_places`(`_init()` が `a_decimal_places >= b_decimal_places` を強制)になる。`ope_result_decimal_places(operator, a_places, b_places)` がこの3パターンを計算する。
- **無限小数を一切生成しない不変条件**: 除算の答えは `calc_div` の「`a % b == 0` の場合のみ成立」という既存の厳密割り切れ判定をそのまま再利用しているため、生成される小数の答えは常に有限小数になる(浮動小数点誤差も、循環小数も発生しない)。ユーザー要件により、この不変条件は本コマンド・`mixed` コマンド共通の設計原則。
- `a_decimal_places != b_decimal_places` の場合(小数×整数・小数÷整数などの非対称ケース)は `-o/--operator` を `['mul']` または `['div']` の単独指定に限定する(`_init()` が拒否)。等しい場合(小数×小数・小数÷小数を含む)は `add`/`sub`/`mul`/`div`/`mix` を制限なく使える。
- `generate_ope_problems()`/`build_horizontal_block_tex()`/`build_ope_bottom_answer_tex()`/`build_ope_csv_rows()` はいずれも `a_decimal_places`/`b_decimal_places` が既定値(0)のときは `format_decimal_value` が `str(raw)` をそのまま返すため、既存の整数専用出力(CSV の型を含む)と完全に同一(回帰なし)。CSV は 0 桁のときのみ生の `int` を書き込み、小数桁がある場合だけ `format_decimal_value` の文字列に切り替える(`build_ope_csv_rows` 参照)。

### `mixed` コマンド(issue #76)

- 整数・小数・分数(`int`/`decimal`/`fraction`)を混在させたオペランドの四則演算(横書きのみ)。`MixedOperand`(`kind`/`display`/`value: Fraction`)が1オペランドを表し、`value` は常に `fractions.Fraction` による厳密値(浮動小数点は一切使わない)。`random_mixed_operand()` は `kind` に応じて `int`(`digit_range` によるプレーン整数)/`decimal`(スケール整数を `format_decimal_value` で表示しつつ `Fraction(scaled, 10**places)` を厳密値として保持)/`fraction`(`frac` コマンドの `random_fraction_operand`/`fraction_to_tex` をそのまま再利用)を生成する。
- `--a-kind`/`--b-kind`(`nargs='*'`、既定は3種類全て)で最初の項/2項目以降それぞれの許容 kind を指定する(多項 `ope` の `nums_a`/`nums_b` 規約=最初の葉だけ別集合、を踏襲)。
- 項数は `ope` と共通の `--terms`/`--terms-min`/`--terms-max`(既定2項、`resolve_term_range()` を `command in ('ope', 'mixed')` に拡張して共有)、演算子は `--mixed-operators` の有無に応じて木を使わないフラットな評価(`evaluate_left_to_right`/`evaluate_mixed_expression`)を使う。両関数は元々 `PAREN_STAGE_FUNCTIONS`(int用)にハードコードされていたが、`stage_functions` 引数(既定 `PAREN_STAGE_FUNCTIONS`)を追加して汎用化し、`mixed` コマンドは `MIXED_STAGE_FUNCTIONS`(Fraction用、`mixed_stage_add`/`_sub`/`_mul`/`_div`)を渡す。この汎用化により多項 `ope` 側の呼び出し・既存テストは無変更(デフォルト引数で完全後方互換)。
- **答えは常に厳密な分数、小数表記には決して変換しない**: `mixed_stage_div` は `Fraction` の除算をそのまま使う(常に厳密、`y` は全 kind が正の値しか生成しないため常に非ゼロ)。`build_mixed_block_tex`/`build_mixed_bottom_answer_tex` はいずれも `fraction_to_tex(problem.result)` で答えを表示するため、例えば `2 ÷ 3` のような循環小数になる除算でも `\frac{2}{3}` という厳密な分数として出題でき、無限小数が出力に現れることはない(ユーザー要件、`ope` の小数拡張と共通の設計原則)。
- CSV は `[page_number, index, terms, mixed, expression, result_numerator, result_denominator]` の7列(`expression` は多項 `ope` の `build_multi_term_ope_expression_text` と同じ自己記述文字列、各オペランドは `display`(例: `"0.5"`/`"3"`/`"\frac{1}{4}"`)をそのまま使う)。
- 根拠資料: 学習指導要領解説 p.293-294 の「内容の取扱い」注記「整数や小数の乗法や除法を分数の場合の計算にまとめることも取り扱うものとする」、および同ページの例示 `5÷2×0.3` を分数の積にまとめる計算。この記述は乗法・除法のみに言及しているが、ユーザーの明示的な指示により四則すべて(`MIX_OPERATORS` = add/sub/mul/div)を許可している。

### `frac`/`mixed --require-reducible`/`--no-reducible`/`--mixed-reducible`(issue #114)

- `docs/uiux/calculation_drill_menu_parameters_v1.md` の小学6年生・分数×整数/整数×分数/分数×分数/分数÷整数/整数÷分数/分数÷分数の6項目が要求する固有設定「約分: なし / あり / まぜる」に対応する。3フラグは `carry_group`/`remainder_group` と同じ形の argparse 排他グループで、内部では `reducible_mode: ReducibleMode = Literal['required', 'none', 'mixed']` に正規化する(`nuts_calc_tex.py:94-96,244-267`)。
- `raw_mul_div_is_reducible(a_numerator, a_denominator, b_numerator, b_denominator, operator)`: 2つの未約分(表示用の生の)分子・分母を `mul` なら単純に、`div` なら `a` の分子×`b` の分母/`a` の分母×`b` の分子で掛け合わせ、`math.gcd(raw_numerator, raw_denominator) > 1` で「表示されている生の分子・分母のまま計算すると約分が必要か」を判定する。`simplify` コマンドの `math.gcd(...) > 1` 再抽選パターン(前述)を `frac`/`mixed` の乗除算1問に一般化したもの(`nuts_calc_tex.py` の `generate_fraction_problems` 直前)。
- `frac`: `-o mul`/`-o div`(`{'mul', 'div'}` の部分集合、複数指定も可)にのみ許可する。`_init()` は `command not in ('frac', 'mixed')` または演算子が `mul`/`div` 以外を含む場合を拒否する。`generate_fraction_problems(..., reducible_mode=None)` は問題ごとに(`'mixed'` モードなら `random.choice((False, True))` で、それ以外は固定で)`wants_reducible` を決め、生成した `a`/`b`(いずれも未約分の `FractionOperand`)の raw reducibility が一致するまでリトライする(`--proper-result` 等の既存条件と同じ retry ループに追加条件として合流)。
- `mixed`: 2項(`terms_min == terms_max == 2`、`--terms`系/`--mixed-operators` との併用禁止)かつ `--a-kind`/`--b-kind` が `{('fraction',), ('int',)}`(順不同)である場合のみ許可する。「未約分」の概念は `decimal` kind(`Fraction` コンストラクタが常に自動約分するスケール整数)や fraction×fraction(`frac` コマンドの領分)には自然に定義できないため、curriculum の分数×整数/整数×分数の形にスコープを絞った(`nuts_calc_tex.py` の `reducible_mode` validation ブロック内コメント参照)。
- `MixedOperand` に `raw_numerator`/`raw_denominator`(既定 `None`)を追加した。`random_mixed_operand()` は `int` を `(value, 1)`、`decimal` を `(scaled, 10**decimal_places)`、`fraction` を元の `FractionOperand.numerator`/`.denominator`(未約分)としてこれらを常に埋める。`value: Fraction` フィールド自体は変更しておらず(常に自動約分済み)、新フィールドはオペランド自身の表示形に対応する未約分値を別途保持する目的のみに使う。既定 `None` のため、3引数(`kind`/`display`/`value`)だけで構築する既存呼び出し・テストは無変更。
- `generate_mixed_problems(..., reducible_mode=None)` は `frac` と同じ per-problem `wants_reducible` パターンを使うが、`gap_count` が常に1(2項限定)であることが validation で保証されているため、`operands[0]`/`operands[1]` と `problem_operators[0]` だけを見れば足りる。

### `ope --use-parentheses`(issue #67、issue #71 でN項に一般化)

- `_init()` は `command == 'ope'` のときのみ `--use-parentheses` を許可し、`--vertical`/`--intermediate` との併用を拒否する。`-o/--operator` の受け付け方は通常の `ope`(`mix` を含む1〜4個の演算子)と全く同じで、「かっこ内外の演算子をちょうど2つ指定する」といった専用の制約は課さない。
- **issue #71 以降の現在の実装**: 固定3項・2形状(`(a op b) op c`/`a op (b op c)`)ではなく、N項(N>=3、下記「`--terms`/`--terms-min`/`--terms-max`/`--mixed-operators`」参照)のランダムな2分木構造に一般化されている。`TreeOpeProblem`(`index`/`operands`/`operators`/`tree`/`result`)が1問を表し、`tree`(`ExprTreeNode` の2分木)が実際の構造を保持する。`operands`/`operators` は `flatten_tree()` による平坦化ビュー(参考用、構造そのものは表さない)。N=3 の場合、この一般化アルゴリズムは旧来の `position='left'`/`'right'` の2形状を厳密に再現する(`build_tree_shape(3)` が生成しうる分割は1/2枚と2/1枚の2通りのみ)。
- `build_tree_shape()`: 葉数 `leaf_count` に対してランダムな分割点(`1..leaf_count-1`)で再帰的に2分木の形を作る。`assign_tree_operands()` は中間順走査で最初の葉に `nums_a`、それ以外の全ての葉に `nums_b` を割り当てる(旧来の「第3項cが`-b`のレンジを再利用する」規約をN項に一般化、後述)。`assign_tree_operators()` は `--mixed-operators` の有無に応じて木全体で1つの演算子を使うか、内部ノードごとに独立して演算子を選ぶ。
- `evaluate_expr_tree()`: post-order で評価し、`PAREN_STAGE_FUNCTIONS`(`paren_stage_add`/`_sub`/`_mul`/`_div`、`calc_sub`/`calc_div` と同じ検証: 減算は正の結果のみ、除算は割り切れる場合のみ)で各ノードを検証する。どこかのノードが無効なら `None` を返し、`generate_tree_ope_problems()` が木構造・演算子・全オペランド値をまとめて再抽選する(`MAX_OPERAND_RETRY_ATTEMPTS` 回まで)。**`calc_sub`/`calc_div` と異なり決定的フォールバックを持たない**ため、有効な木が極端に少ない演算子/構造の組み合わせでは `ValueError` になりうる(既知の制限、後述)。旧 `generate_paren_ope_problems` は `op_left`/`op_right`/`position` を固定してオペランドのみ再抽選する細粒度リトライだったが、現在の実装は木構造ごと再抽選するより単純な戦略に変更されている。
- `render_expr_tree()`: ルート以外の全内部ノードを括弧で包んで再帰的にレンダリングする(`build_tree_ope_expression_tex` はTeX記号版、`build_tree_ope_structure_text` は演算子名版でCSV出力用)。
- `build_ope_pages()` は `ini.use_parentheses` が真の場合、通常の2項 `ope` 生成ロジックに入らず `build_tree_ope_pages()` に委譲する。`--vertical`/`--intermediate` は非対応のため `Page.layout` は常に `'inline'`。

### `ope --terms`/`--terms-min`/`--terms-max`/`--mixed-operators`(issue #71)

- `_init()` は `command == 'ope'` のときのみこれらのオプションを許可し、`--vertical`/`--intermediate`/`--missing-value` との併用を拒否する。`--terms` は `--terms-min`/`--terms-max` を無条件に上書きする(エラーにはしない)。これは `-a/--a-value` が `--a-min`/`--a-max` を無条件に上書きする既存の挙動と同じパターンで、独立した検証を追加せずに済ませている。
- **項数floor/上限のクランプ(意図的な設計判断)**: `resolve_term_range(terms_min, terms_max, use_parentheses)` が、通常の `ope` では2項未満、`--use-parentheses` 使用時は3項未満(2項の括弧は無意味なため)を要求された場合、**エラーにせず該当する下限にクランプする**。同様に `MAX_OPE_TERMS`(12)を超える値も上限にクランプする。これは本ファイルの支配的な `failure()`/`exit(1)` バリデーション慣習からの**意図的な例外**であり、ユーザーからの明示的な要望による(下限未満/以下を指定してもエラーで止めず、意図に近い最小構成で出題を継続してほしいという要求)。
- `_ope_uses_multi_term(ini)`: `terms_min`/`terms_max` が既定値(2)から変わっているか `--mixed-operators` が指定されていれば真。`build_ope_pages()` は `--use-parentheses` → `--missing-value` → 多項(`_ope_uses_multi_term`)→ 通常2項、の順で分岐する。新オプションを一切指定しない場合、`_ope_uses_multi_term` は常に偽になるため、デフォルトの `ope` 呼び出しは無変更の2項固定コードパス(`generate_ope_problems`/`OpeProblem`/`build_ope_csv_rows` 等)をそのまま通る(出力が同等なのではなく、文字通り同じコードが実行される)。
- **括弧なし多項(`MultiTermOpeProblem`: `index`/`operands`/`operators`/`mixed`/`result`)**: `--mixed-operators` が偽の場合、問題ごとに1つの演算子を選び全ての箇所に適用し、`evaluate_left_to_right()` で左から順に評価する(`a sub b sub c` なら両方の減算が独立して正でなければならない、`calc_sub`/`calc_div` の単一ステップ検証をチェーンへ一般化)。真の場合、箇所ごとに独立して演算子を選び、`evaluate_mixed_expression()` が**標準の数学演算優先順位**(×÷が+−より先)で評価する: `split_into_precedence_groups()` が連続する `mul`/`div` を1グループにまとめ、`evaluate_left_to_right()` を2段階(グループ内→グループ間)で適用する。木は作らないリスト操作ベースの実装(`evaluate_expr_tree` とは別経路)。
- CSV出力は可変長のオペランド/演算子リストに対応するため、固定列数ではなく自己記述的な単一文字列列を使う: 括弧なし多項(`build_multi_term_ope_csv_rows`)は `[page_number, index, terms, mixed, expression, result]` の6列(`expression` は `"5 sub 3 mul 2"` のような演算子名ベースの空白区切り文字列)、木構造(`build_tree_ope_csv_rows`)は `[page_number, index, terms, structure, result]` の5列(`structure` は `"(5 add 3) mul 2"` のようにネスト・値・演算子を全て含む自己記述文字列)。旧来の固定10列の括弧付きCSV形状(`[a, op_left, b, op_right, c, position, inner, result]`)はこれに置き換わった。通常2項 `ope` のCSV形状(`[page_number, index, a, operator, b, c]`)は無変更。

### `ope --missing-value`(issue #69)

- `_init()` は `command == 'ope'` のときのみ `--missing-value` を許可し、`--vertical`/`--intermediate`/`--use-parentheses` との併用を拒否する(`nuts_calc_tex.py:223-231,362-371`)。
- `MissingValueProblem`(`index`/`a`/`b`/`operator`/`c`/`blank`)が1問を表す。新しい算術ロジックは追加せず、既存の `OpeProblem` と同じ `CALC_FUNCTIONS`(`calc_add`/`calc_sub`/`calc_mul`/`calc_div`)をそのまま呼び出して `a op b = c` を成立させたうえで、`blank` にどの位置を隠すかを記録するだけの薄いラッパーになっている(`generate_missing_value_problems`、`nuts_calc_tex.py:973-990`)。`calc_sub`/`calc_div` の決定的フォールバックも自動的に引き継がれる。
- `blank` の候補は `MISSING_VALUE_POSITIONS = ('a', 'b')` に限定し、**答え `c` は候補に含めない**(後述の設計判断を参照)。
- `build_missing_value_block_tex()` は `n) $a op b = c$` を生成し、`blank` が `'a'`/`'b'` のときだけその位置を `BOXED_BLANK_TEX`(`com` の欠けた加数と共有する角枠、旧 `COM_BLANK_ANSWER_TEX` からリネーム)に置き換える。`c` は常に実値を表示する。
- `build_missing_value_page_pair`/`build_missing_value_bottom_answer_tex`/`build_missing_value_csv_rows`/`build_missing_value_pages` は `ope --use-parentheses` の対応する関数群と同じ構造。`build_missing_value_csv_rows` は `[page_number, index, a, operator, b, c, blank]` の7列。`Page.layout` は常に `'inline'`(`--vertical`/`--intermediate` 非対応)。
- `build_ope_pages()` は `ini.use_parentheses` の次に `ini.missing_value` をチェックし、真の場合は `build_missing_value_pages()` に委譲する(`nuts_calc_tex.py:1539-1560`)。両フラグは `_init()` のバリデーションで排他が保証されているため、この2分岐は同時に真にならない。

### `lcm`/`gcd` コマンド(issue #95)

- 2つの整数から最小公倍数(LCM)/最大公約数(GCD)を出題する、LaTeX 固有の11・12番目のコマンド。`docs/uiux/calculation_drill_menu_parameters_v1.md` の学年5「公倍数・最小公倍数」「公約数・最大公約数」に対応する(issue #90 の子issue、#94(倍数・約数・偶数奇数、単一整数の性質)とは独立に実装、依存関係なし)。
- `NumberPairProblem`(`index`/`a`/`b`/`c`)が1問を表す。`generate_number_pair_problems(compute, nums_a, nums_b, order, start_index)` は `a`/`b`(`ini.a_min`〜`ini.b_max` から独立に `random.choice`)に `compute`(標準ライブラリ `math.lcm`/`math.gcd`)を適用するだけの薄い生成関数で、`calc_sub`/`calc_div` と異なり正の整数同士では常に定義されるため再抽選・決定的フォールバックは不要(`nuts_calc_tex.py` の `NumberPairProblem` 定義直後)。
- `build_number_pair_pages(ini, compute, label)` が `'lcm'`/`'gcd'` 両コマンドで共有される唯一の生成・レンダリング経路: `math.lcm`/`math.gcd`(と表示ラベル `'LCM'`/`'GCD'`)以外の差分が一切ないため、`build_com_pages`/`build_kuku_pages` のようにコマンドごとに関数を複製せず、`compute`/`label` を引数化して1つの実装を両コマンドで再利用する(`main()` の `elif ini.command == 'lcm': ... build_number_pair_pages(ini, math.lcm, 'LCM')` / `'gcd'` の2分岐参照)。
- `build_number_pair_block_tex()` は `n) $\mathrm{LABEL}(a, b) = c$`(`LABEL` は `LCM`/`GCD`)を生成する。blank 版は `c` の代わりに、`squ`/`pi`/`99`/`aBc` と同じ固定幅の `\hspace{1.5em}`(`BLANK_ANSWER_TEX`)を出力する(`com`/`missing-value` の角枠 `BOXED_BLANK_TEX` ではない、答え1つだけを隠す「二数入力・一答出力」形式のため)。日本語ラベル「最小公倍数」「最大公約数」ではなく英語 `LCM`/`GCD` を採用した理由は、本ファイルが素の `pdflatex`(CJK未対応)でコンパイルされているためで、`--with-name-field` の `Name:` ラベル(issue #93)と同じ制約・同じ設計判断(後述の設計判断セクション参照)。
- `-a`/`-b`(桁数)は `ope`/`100` と同じ `set_min_max_value()` によるレンジ変換の対象に含めた(`_init()`: `if args.command in ('ope', '100', 'lcm', 'gcd', 'divfrac')`。`divfrac` は issue #96 で追加)。`-a`/`-b` 省略時は既定の `--a-min`/`--a-max`/`--b-min`/`--b-max`(1〜9)がそのまま使われる。`--vertical`/`--intermediate`/`--use-parentheses`/`--missing-value`/`--terms`系/`--carry-borrow`系/`--remainder`系/`--a-decimal-places`系は、いずれも既存の `_init()` バリデーションが `command != 'ope'` を理由に無条件で拒否するため、`lcm`/`gcd` を明示的に除外する追加コードは不要だった。
- `build_number_pair_csv_rows` は1問1行、`[page_number, index, a, b, c]` の列で CSV を書き出す(`99`/`aBc` 等と同じ「オペランド→答え」の素直な列構成)。

### `simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac` コマンド(issue #96)

- issue #90 の子issue。`docs/uiux/calculation_drill_menu_parameters_v1.md` の小学5年生表にある分数・小数の表現変換ドリル5種(約分・通分・分数を小数に直す・小数を分数に直す・割り算の答えを分数で表す)に対応する、LaTeX 固有の13〜17番目のコマンド。5種とも同表で「固有設定: —」(選択可能な追加パラメータなし)のため、新規CLIフラグは追加せず、`simplify`/`commondenom`/`frac2dec` は既存の `--numerator-digits`/`--denominator-digits`(`frac`/`compare`/`mixed` と共有、`_init()` のゲート対象コマンドリストに追加)を、`divfrac` は既存の `-a`/`-b`/`--a-min`/`--a-max`/`--b-min`/`--b-max`(`lcm`/`gcd` と共有)を再利用する。`frac2dec`/`dec2frac` の小数桁数は CLI フラグ化せず内部でランダムに選ぶ。
- `simplify`: `SimplifyProblem`(`index`/`operand: FractionOperand`/`reduced: Fraction`)。`generate_simplify_problems()` は `frac` の `random_fraction_operand()` を再利用しつつ、`math.gcd(numerator, denominator) > 1`(約分可能)になるまで最大 `MAX_OPERAND_RETRY_ATTEMPTS` 回再抽選する(既約分数のままでは約分ドリルとして成立しないため)。`reduced` は `FractionOperand.value` プロパティ(`Fraction` の自動約分)をそのまま使う。
- `commondenom`: `CommonDenomProblem`(`index`/`a`/`b`/`a_converted`/`b_converted`、いずれも `FractionOperand`)。`generate_commondenom_problems()` は `random_fraction_operand()` を2回呼び、分母が異なるまで再抽選した上で(同分母では通分が無意味)、`math.lcm(a.denominator, b.denominator)` を共通分母として両方の分子をスケールする(学校で教える通分の手順そのまま)。
- `frac2dec`: `Frac2DecProblem`(`index`/`operand: FractionOperand`/`decimal_places`/`scaled_numerator`)。`denominator_decimal_places(denominator)` が分母を2と5の素因数の個数に分解し、それ以外の素因数が残れば `None`(循環小数)を返す。`terminating_denominators(min, max)` でこの判定を満たす分母だけに候補を絞ることで、`generate_frac2dec_problems()` は常に有限小数を生成する -- `ope`/`mixed` の小数拡張が既に確立している「循環小数を一切生成しない」不変条件(nuts_calc_tex.py.md の該当セクション参照)をこの変換ドリルにも適用したもの。分母が `10**places` を必ず割り切ることが保証されるため、`scaled_numerator = numerator * (10 ** places) // denominator` の整数除算は常に厳密。表示は既存の `format_decimal_value()` をそのまま再利用する。
- `dec2frac`: `Dec2FracProblem`(`index`/`decimal_places`/`scaled_numerator`/`reduced: Fraction`)。`generate_dec2frac_problems()` は `ope` の小数拡張と同じ scaled-integer 方式(`format_decimal_value(scaled_numerator, decimal_places)`)で小数を生成し、`decimal_places` は `DEC2FRAC_MIN_DECIMAL_PLACES`(1)〜`MAX_DECIMAL_PLACES`(2、`ope` と共有)からランダムに選ぶ。`scaled_numerator` は `[1, 10**decimal_places - 1]` から選ぶため常に `10**decimal_places` の倍数になり得ず、`reduced = Fraction(scaled_numerator, 10**decimal_places)`(自動約分)の分母は常に1より大きい。
- `divfrac`: `DivFracProblem`(`index`/`a`/`b`)。`generate_divfrac_problems()` は `generate_number_pair_problems()`(`lcm`/`gcd`)と同じ「`a`/`b` を独立に `random.choice`」パターンだが、出力の型が分数(整数ではない)であるため `NumberPairProblem`/`build_number_pair_pages` は再利用せず独立実装にした(`build_com_pages`/`build_kuku_pages` を複製した際の判断基準 -- 差分が「計算関数とラベルだけ」の場合のみ共通化する -- と同じ理由)。答え `a/b` は `fraction_to_tex(FractionOperand(a, b))` で描画する: `fraction_to_tex(Fraction(a, b))` ではなく `FractionOperand` を渡すのは、`Fraction` がコンストラクタで自動約分してしまい、このドリルの本質である「約分しない a/b」という答えを壊してしまうため。`_init()` は `--b-min >= 1` を要求し(0除算防止、`multiples`/`divisors` の `--a-min >= 1` チェックと同じパターン)、`b=0` は発生しない。
- 5コマンドとも CJK制約(素の `pdflatex`)に該当する日本語テキスト・ラベルを一切使わないため(数字・分数・小数のみ)、`evenodd`/`--with-name-field` のような英語ラベルへの置き換えは不要だった。
- CSV列: `simplify` は `[page_number, index, numerator, denominator, reduced_numerator, reduced_denominator]`、`commondenom` は `[page_number, index, a_num, a_den, b_num, b_den, a_conv_num, a_conv_den, b_conv_num, b_conv_den]`、`frac2dec` は `[page_number, index, numerator, denominator, decimal_display]`、`dec2frac` は `[page_number, index, decimal_display, reduced_numerator, reduced_denominator]`、`divfrac` は `[page_number, index, a, b]`(答えは `a`/`b` から自明なため列を持たない、`squ` が `b` 列を持たない設計判断と同じ理由)。

## 動作の概要

### 共通基盤(Phase 1)

- `_init()`(`nuts_calc_tex.py:74-250`): `nuts_calc.py` と同じ引数(`paper_size`/`command`/`-a`/`-b`/`--a-min`/`--a-max`/`--b-min`/`--b-max`/`-o`/`--rows`/`--columns`/`--page`/`--merge`/`--csv`/`--out-file`/`--with-bottom-answer`/`--with-name-field`/`--vertical`/`--intermediate`/`--debug` 等)を独立に定義・パースする。`-r`/`-c`/`-p` は1以上を要求する。`command == '100'` の場合、`-a`/`-b`(桁数)が指定されていれば1〜3の範囲であることを、`-a`/`-b` の桁数レンジ変換(`set_min_max_value`)より**前**に検証する(範囲外だと `set_min_max_value` 内で `IndexError` になる、または負のインデックスで誤ったレンジになるため。詳細は後述)。`-a`/`-b` の桁数レンジ変換自体は `command in ('ope', '100')` の場合のみ行う。`command == 'com'` の場合は `-a/--a-value`(補数ターゲット)が必須かつ2以上であることを検証する。`command == '99'` の場合は `-a/--a-value`(九九の段)が必須であることを検証する(値域は `nuts_calc.py` と同じく未検証)。`command == 'squ'` の場合は `-a/--a-value`(開始する二乗数の起点)が必須であることを検証する(`99` と同じ形、値域は同じく未検証)。`command == 'pi'` の場合は `-a/--a-value`(円周率倍する整数列の起点)が必須であることを検証する(`squ` と全く同じ形)。`command == 'aBc'` の場合は `-a`/`-b` を一切使用しない(`com`/`99`/`squ`/`pi` と異なり検証も不要)。`command == 'ope'` の場合のみ `--intermediate` のバリデーションを行う(後述)。
- `Page` データクラス(`blocks: list[str]`, `columns: int`, `bottom_answer_tex: str | None`, `layout: str`): 1ページ分の LaTeX コンテンツを表す最小単位。`layout='inline'`(横書き用。本文幅を列数で割った等幅セルに問題を中央配置し、余剰の本文高を行間に配分)、`layout='tabular'`(`--vertical` 用、後述)、`layout='block'`(100マス表のような自己完結したLaTeXブロック用)の3種類。問題ブロックは生成順に各列を上から下へ満たす列優先で配置するため、複数列では問題番号2は問題番号1の直下に置かれる。
- `--rows` の既定値: 通常形式では `DEFAULT_ROWS`(10)を使う。`ope --vertical` では `VERTICAL_DEFAULT_ROWS_BY_PAPER_SIZE` により、A3/A4は4行、B5/A4横は2行を使う。筆算ブロックは複数行にわたるため、既定の `--page` 数を物理PDFのページ数として保つための用紙別設定である。明示した `--rows` は常にそのまま使う。
- `build_preamble_tex`/`build_page_header_tex`/`build_page_tex`/`build_document_tex`: LaTeX ソースを文字列として組み立てる。用紙サイズは `geometry` パッケージのオプション(`a3paper`/`a4paper`/`b5paper`/`a4paper,landscape`)にマッピングし、左右15mm・上20mm・下40mmの余白、ヘッダー(タイトル・日付欄)、下端寄りに配置するフッター(ページ番号・著作権、`fancyhdr`)、行×列グリッドを構築する。プリアンブルは `longdivision`/`xlop`/`array`/`fancyhdr`/`xcolor`(`table` オプション、`100` コマンドのヘッダー網掛けに使用)を読み込む。
- `LatexEngineAdapter`(issue #120): プラガブルなLaTeXエンジン抽象化。`typing.Protocol` で `binary_name: str`/`build_preamble_additions() -> str`/`compile(tex_source, out_pdf_path) -> None` の3メンバーを要求する。共通の subprocess 起動ロジック(一時ディレクトリで `<binary_name> -interaction=nonstopmode -halt-on-error` を実行し、生成PDFを指定パスへコピー、失敗時は該当エンジンの出力末尾を含めて `exit(1)`)は `_SubprocessLatexEngineAdapter` 基底クラス(issue #121 でリファクタリング抽出、旧 `compile_tex` 独立関数をメソッド化した設計をそのまま踏襲)にまとまっており、`PdflatexEngineAdapter`(`binary_name = 'pdflatex'`、`build_preamble_additions()` は空文字列)と `LuaLatexEngineAdapter`(`binary_name = 'lualatex'`、`build_preamble_additions()` は `fontspec` + `\setmainfont{Noto Sans CJK JP}`(`LUALATEX_CJK_FONT_NAME`)を返す。issue #121、詳細・設計判断は後述)はいずれもこれを継承するだけで `compile()` を実装済みにできる。`NUTS_CALC_TEX_ENGINE` 環境変数(`LATEX_ENGINE_ENV_VAR`)で選択するエンジン名を解決する `get_latex_engine_name()`/`get_latex_engine_adapter()` は、`backend/renderers.py` の `NUTS_CALC_RENDERER`/`get_renderer_name()` パターン(未設定時は `DEFAULT_LATEX_ENGINE` にフォールバックし、`LATEX_ENGINE_ADAPTERS` dict に無い値は `ValueError`)を意図的に踏襲している。`DEFAULT_LATEX_ENGINE` は issue #186 で `'pdflatex'` から `'lualatex'` に変更され、日本語対応の `lualatex` が既定エンジンになった(`nuts_calc_tex.py:893-910`)。`NUTS_CALC_TEX_ENGINE=pdflatex` を明示指定すれば従来どおり `pdflatex` を選択できる。`build_preamble_tex(paper_size, engine_adapter=None)` は `engine_adapter` 省略時 `PdflatexEngineAdapter()` にフォールバックする(既存呼び出し元・テストの出力を変えないため)一方、`build_document_tex` は `engine_adapter` を必須引数として要求する(`main()` 内の呼び出し元が常に解決済みインスタンスを持つため)。将来エンジンを追加する場合、新しい `LatexEngineAdapter` 実装クラス(多くの場合 `_SubprocessLatexEngineAdapter` を継承するだけで済む)と `LATEX_ENGINE_ADAPTERS` への登録のみで足り、`build_preamble_tex`/`build_document_tex`/`main()` 側の変更は不要な設計。
- `--with-name-field`(issue #93): `build_page_header_tex(with_name_field: bool = False)`(`nuts_calc_tex.py:701-711`)が真の場合のみ、Date/Time行の直後に独立したLaTeX改行(`\\\\`)を挟んで `Name: \underline{\hspace{8cm}}` 行を追加する。`with_name_field` は `build_page_tex`(`nuts_calc_tex.py:789`)→ `build_document_tex`(`nuts_calc_tex.py:804-809`)→ `main()`(`nuts_calc_tex.py:3199-3216`、`ini.with_name_field` を2箇所の `build_document_tex` 呼び出しへ渡す)という単一経路でスレッドされる。ヘッダーは全12コマンド共通の呼び出し(`build_page_tex` 単独箇所)を通るため、`--with-bottom-answer` のようにコマンドごとの `build_X_pages` 関数へ個別配線する必要がなく、`_init()` でのコマンド限定バリデーションも行わない(全コマンドで無条件に有効)。フラグ未指定時は `with_name_field=False` がデフォルト値のまま伝播するため、既存の `Date: ... \hfill Time: ...` 行のみの出力と完全に同一(回帰なし、実機PDF比較で確認済み)。日本語ラベル(「なまえ：」)ではなく英語 `Name:` を採用した理由は後述の設計判断を参照。
- 出力ファイル名の導出は `nuts_calc.py`(issue #15 修正後)と同様に `os.path.splitext(ini.out_file)` を使う(`_read.pdf`/`.csv` の付与)。
- `main(ini)`(`nuts_calc_tex.py:1157-`): 冒頭で `get_latex_engine_adapter()` を解決し(未知の `NUTS_CALC_TEX_ENGINE` 値は `ValueError` を捕捉して `failure()` 経由で `exit(1)`)、続けて `shutil.which(engine_adapter.binary_name)` が `None` なら(既定アダプターでは `pdflatex`、メッセージ文言は issue #120 以前と完全に同一)`exit(1)` する。`ini.command == 'ope'` なら `build_ope_pages`、`'com'` なら `build_com_pages`、`'100'` なら `build_hundred_square_pages`、`'99'` なら `build_kuku_pages`、`'aBc'` なら `build_abc_pages`、`'squ'` なら `build_squ_pages`、それ以外(`'pi'`、7コマンドの choices のうち上記6分岐に該当しない残り)なら `build_pi_pages` で実データを生成し、`--merge` の有無に応じて blank/filled/merge の3モードで `build_document_tex(..., engine_adapter=engine_adapter)` をビルドし、`engine_adapter.compile(tex_source, out_path)`(旧 `compile_tex(tex_source, out_path)` 呼び出しをメソッド化したもの)でPDF化する。`--csv` 指定時は、`ope`/`com`/`100`/`99`/`aBc`/`squ`/`pi` それぞれの実問題データを CSV に書き出す(7コマンド全てが実データを持つため、プレースホルダー用の CSV フォールバックは Phase 8 で削除済み)。

### `ope` コマンド(Phase 2)

- `OpeProblem` データクラス(`index`/`a`/`b`/`operator`/`c`/`a_decimal_places`/`b_decimal_places`/`remainder`)が1問を表す。`remainder`(既定0、issue #91)は `operator == 'div'` のときだけ `a - b * c` の意味を持ち、それ以外は常に0。
- フラグ未指定時の `calc_add`/`calc_mul` は単純計算。`calc_sub`/`calc_div` は `nuts_calc.py` の同名関数と同じ意味論(結果が正になるまで/割り切れるまで、最大 `MAX_OPERAND_RETRY_ATTEMPTS`(1000)回オペランドを再抽選)をベースに独立に再実装し、再抽選後は `calc_sub` が `(max(nums_a), min(nums_b))`、`calc_div` が `find_exact_division_pair` へ決定的にフォールバックする。`--carry-borrow`系指定時だけ、上記issue #78の条件付き経路へ分岐する(`nuts_calc_tex.py:874-999`)。
- `generate_ope_problems`(`nuts_calc_tex.py:433-451`): `operators` に `'mix'` が含まれる場合は `add`/`sub`/`mul`/`div` の4種から**問題ごとに**ランダムな演算子を選ぶ(`nuts_calc.py` の `mix` 展開と同じ意味論)。
- 横書き: `build_horizontal_block_tex` が `n) $a op b = c$` を生成する。blank 版は `c` の代わりに、下線を伴わない固定幅の `\hspace{1.5em}` を出力する。`--intermediate` 指定時は `build_horizontal_intermediate_block_tex` が代わりに使われ、`build_intermediate_memo`(`memo.md` STEP 1 の2桁×1桁暗算メモ技法: `a` の十の位×`b` と一の位×`b` をそれぞれ2桁ゼロ埋めして連結)を挟んだ `n) $a \times b \Rightarrow memo \Rightarrow c$` を出力する。同じ固定幅の空欄を使うため、通常・途中式とも解答欄のレイアウトを維持する。
- `--vertical`(筆算): `build_vertical_block_tex`(`nuts_calc_tex.py:1517-1554`)が問題の `operator` に応じて分岐する。
  - `add`/`sub`/`mul`: `xlop` の `\opadd`/`\opsub`/`\opmul` を使用(多桁の乗数は自動で部分積の複数段表示になる)。blank 版は `\opset{resultstyle=\phantom,carrystyle=\phantom,intermediarystyle=\phantom}` を `\begingroup`/`\endgroup` で局所適用し、結果・繰り上がり・部分積の**数字だけ**を不可視化する(レイアウトの高さ・幅は保持されるため、罫線位置は blank/filled で一致する)。オペランドは `format_decimal_value(problem.a, problem.a_decimal_places)`/同 `b` を経由して渡す(issue #134。`places<=0` では `str(raw)` と等しいため既存の整数専用出力に影響なし)。
    - **既知の制限(xlopの表示上の癖)**: `xlop` は小数第1位が0の値(例: `"8.0"`)の末尾ゼロを自動的に省略して `"8"` と描画する(パッケージ自身の数値パーサーの挙動で、こちら側の入力文字列は正しく `"8.0"` を渡している)。答え自体の計算・表示は正しい(実機確認: `\opmul{8.7}{8.0}` → `8.7 × 8`(本来 `8.0`)、答え `69.6` は正しい)。横書き(`build_horizontal_block_tex`)は `xlop` を経由せず `format_decimal_value()` の文字列をそのまま出すため、この癖の影響を受けない。
  - `div`: `longdivision` の `\intlongdivision` を使用。blank 版は `stage=0` オプションで除数・被除数の枠のみを表示する。被除数は `format_decimal_value(problem.a, problem.a_decimal_places)`、除数は `format_decimal_value(problem.b, problem.b_decimal_places)` を経由する(issue #134)。`b_decimal_places > 0`(除数が小数)の組み合わせは `_init()` が拒否するため、この関数に到達する時点で除数は常に整数(前述の `ope --a-decimal-places`/`--b-decimal-places` セクション参照)。
    - **既知の制限(罫線のスタイル)**: `longdivision` パッケージ(vendor版)が描く枠は、英語圏教科書に典型的な「丸みのある括弧+上部の横線」スタイル(`\smash{\big)}` ベース)で、日本の教科書に典型的な「直角に近い逆L字」の罫線とは見た目が異なる。パッケージの `style` オプション(`default`/`standard`/`tikz`/`german`/`brazilian`)のうち `tikz`(要 `\usepackage{tikz}`、現状のプリアンブルには含めていない)を試したところ、`arc` によるやや滑らかな曲線にはなるが、依然として英語圏スタイルの範疇に留まることを実機確認した。日本式の罫線が必要な場合はパッケージの `style` 切り替えでは不十分で、自前の罫線描画(TikZ等)が要る規模の変更になる。issue #134 では対応しないと決定した(新規 issue も起票しない)。
  - `mix` の場合、各問題は生成時点で具体的な演算子(add/sub/mul/div のいずれか)に確定しているため、`build_vertical_block_tex` は追加の分岐なしに機能する。
- `build_ope_page_pair`(`nuts_calc_tex.py:508-528`): `vertical`/`intermediate` フラグに応じて上記のブロックビルダーと `Page.layout`(`vertical` なら `'tabular'`、それ以外は `'inline'`)を選び、同一の問題リストから blank/filled の `Page` ペアを作る(blank/filled は同じ問題を使い、表示のみが異なる)。
- `build_ope_pages`(`nuts_calc_tex.py:557-578`): `ini.a_min`〜`ini.b_max` から候補集合を作り、ページごとに `rows*columns` 問を生成してページペアを積み上げる。`--with-bottom-answer` 指定時は `build_ope_bottom_answer_tex` で `(index) c` の一覧を blank ページ末尾に追加する。
- `build_ope_csv_rows`(`nuts_calc_tex.py:535-540`): 1問1行、`[page_number, index, a, operator, b, c, remainder]` の列で CSV を書き出す(ヘッダー行なし、Phase 1 と同じ方針。`remainder` 列は issue #91 で追加、詳細は前述の `ope --remainder` セクション参照)。

### `com` コマンド(Phase 3)

- `ComProblem` データクラス(`index`/`a`/`target`/`c`、`nuts_calc_tex.py:598-604`)が1問を表す。`a + c = target` が常に成り立つ。
- `generate_com_problems`(`nuts_calc_tex.py:607-618`): `1..target-1` の範囲から `a` を `random.choice` で選び、`c = target - a` を計算する。`nuts_calc.py` の `get_complement_data` と意味論は同じだが独立に再実装している(コード共有なし)。`a` は範囲の閉区間からの毎回の乱択で選ぶため、`nuts_calc.py` 側にあった「事前に `random.sample` でシャッフルしてから `random.choice` する」という冗長な前処理は行わない。
- `build_com_block_tex`(`nuts_calc_tex.py:721-724`): `n) $a + □ = target$`(blank)/`n) $a + c = target$`(filled)を生成する。blank の欠けた加数には `COM_BLANK_ANSWER_TEX` の四角枠を表示し、`\vcenter` で枠の中心を数式軸に揃える。blank でも `target` はそのまま表示し、隠すのは答え `c` のみ。通常計算の式末尾にある解答欄は引き続き共通の `BLANK_ANSWER_TEX` による空白表示で、四角枠にはしない(`nuts_calc_tex.py:64-65,721-724`)。
- `build_com_page_pair`/`build_com_pages`(`nuts_calc_tex.py:629-673`): `ope` の同名関数群と同じ構造。`--vertical`(筆算)には未対応(issue #22 のスコープ外、`Page.layout` は常に `'inline'`)。`--with-bottom-answer` 指定時は `build_com_bottom_answer_tex` で `(index) c` の一覧を blank ページ末尾に追加する。
- `build_com_csv_rows`(`nuts_calc_tex.py:645-650`): 1問1行、`[page_number, index, a, target, c]` の列で CSV を書き出す。

### `100` コマンド(Phase 4)

- `HundredSquareTable` データクラス(`left_values`/`top_values`、`answers` プロパティで `left_values[r] + top_values[c]` の10×10行列を計算)が1枚の加算表を表す。
- `sample_hundred_square_values`(`nuts_calc_tex.py` の `100` セクション): 候補範囲のリストを `HUNDRED_SQUARE_SAMPLE_REPEAT_FACTOR`(2)倍に複製してから `random.sample` で10個抽出する。既定の桁数1レンジ(1-9、9個の値)は10枠に対して1個不足するため、複製しないと `random.sample` が母集団不足で失敗する。`nuts_calc.py:1469-1474` の `seed.extend(...)` パターンと同じ意味論を再実装している(コード共有なし)。
- `generate_hundred_square`: 左列・上段それぞれに `sample_hundred_square_values` を適用して `HundredSquareTable` を作る。
- `build_hundred_square_block_tex`: 11×11の LaTeX `tabular` を1枚組み立てる。左上角は空欄、ヘッダー行(`top_values`)・ヘッダー列(`left_values`)は `colortbl`(`xcolor[table]` 経由)の `\rowcolor`/`\columncolor` で網掛けする。blank 版はデータセルを空文字列、filled 版は `left + top` の和を表示する。
- `build_hundred_square_pages`: `ini.page` 枚分、1ページ1表(`Page(blocks=[...], columns=1)`)の blank/filled ペアを生成する。`ini.rows`/`ini.columns`/`ini.with_bottom_answer` は `nuts_calc.py` の元実装同様に未使用(固定サイズの表1枚のみ、下部解答欄なし)。
- `build_hundred_square_csv_rows`: ページごとに、ヘッダー行(`[page_number, '', *top_values]`)と10本のデータ行(`[page_number, left, *answer_row]`)を書き出す。

### `99` コマンド(Phase 5)

- `KukuProblem` データクラス(`index`/`a`/`b`/`c`)が1問を表す。`a`(段、`-a/--a-value` から取得)はページ内の全問題で共通。
- `generate_kuku_problems`(乗数 `b` の生成): `order = ini.rows * ini.columns` 問を1ページ分生成する。乗数 `b` は `1..KUKU_MULTIPLIER_MAX`(=9)を周期とする連番(`i % KUKU_MULTIPLIER_MAX + 1`)で、`order` が9を超える場合は10問目以降が `×1` から折り返して繰り返す(issue #152)。`--descend` は昇順リストを反転するのではなく `KUKU_MULTIPLIER_MAX - (i % KUKU_MULTIPLIER_MAX)`(`9,8,...,1,9,8,...`)で降順の折り返し列を直接構築する(issue #155: 昇順の折り返し済みリストをそのまま反転すると境界がずれ、`9` からではなく `1` から始まってしまう不具合があった)。`--shuffle` は(`--descend` 適用後の並びを)`random.shuffle` する。`nuts_calc.py` と同じくコード共有はせず独立に再実装している。issue #24 実装時点では `order` を9問固定にせず `nuts_calc.py` 側の(当時の)未キャップ挙動をそのまま踏襲する設計が意図的に選択されていたが、issue #149 で `nuts_calc.py` 側が先に修正され、issue #152 で本ファイルもその決定を覆して追従した(下記「重要な設計判断」参照)。
- `build_kuku_block_tex`: 通常は `n) $a \times b = c$` を生成する。blank 版は `c` を、下線を伴わない固定幅の `\hspace{1.5em}` に置き換える。`--reverse` 指定時は式の左右を入れ替えて `n) $c = a \times b$` にする(blank でも隠すのは常に `c`)。この入れ替えの意味論は `nuts_calc.py` の `get_fixed_format_data` が `is_reverse` のとき返すタプルの並びが `vals_c` を `vals_a`/`vals_b` より前に置く(`nuts_calc.py:543-545`)ことから独立に解釈・再実装したもの(`nuts_calc.py` 側のレンダリングパイプラインは完全に別実装のため、表示結果を直接比較検証してはいない)。
- `build_kuku_page_pair`/`build_kuku_pages`: `ope`/`com` と同じ構造。`Page.layout` は常に `'inline'`(`--vertical` 未対応)。`--with-bottom-answer` 指定時は `build_kuku_bottom_answer_tex` で `(index) c` の一覧を blank ページ末尾に追加する。
- `build_kuku_csv_rows`: 1問1行、`[page_number, index, a, b, c]` の列で CSV を書き出す。

### `aBc` コマンド(Phase 6)

- `AbcProblem` データクラス(`index`/`a`/`b`/`c`/`d`)が1問を表す。`abcd_display` プロパティが `f"{a}{b}{c}{d}"` で4桁の表示文字列を、`answer` プロパティが `(a*10+b)*10 + (c*10+d)`(2桁ペア `ab` を10倍してもう一方の2桁ペア `cd` を加算)を計算する。
- `generate_abc_problems`: `a`/`b`/`c`/`d` をそれぞれ独立に `0..9`(`ABC_DIGIT_MAX`)から `random.choice` で選ぶ。`nuts_calc.py` の `get_aBc_data`(`nuts_calc.py:548-587`)と同じ範囲・意味論だが独立に再実装している(コード共有なし)。`ope --intermediate` の暗算メモ技法(`build_intermediate_memo`)と同じ「2桁ペアへの分解」の考え方を、単独の変換ドリルとして流用したもの(`memo.md` セクション3)。
- `build_abc_block_tex`: `n) $abcd \Rightarrow answer$` を生成する。blank 版は `answer` の代わりに、下線を伴わない固定幅の `\hspace{1.5em}` を出力する。
- `build_abc_page_pair`/`build_abc_pages`: `com`/`99` と同じ構造。`order = ini.rows * ini.columns`。`Page.layout` は常に `'inline'`(`--vertical` 未対応)、`-a`/`-b` は不使用。`--with-bottom-answer` 指定時は `build_abc_bottom_answer_tex` で `(index) answer` の一覧を blank ページ末尾に追加する。
- `build_abc_csv_rows`: 1問1行、`[page_number, index, a, b, c, d, answer]` の列で CSV を書き出す。

### `squ` コマンド(Phase 7)

- `SquProblem` データクラス(`index`/`a`/`c`)が1問を表す。`99`(kuku)の `KukuProblem` と異なり `a` はページ内で問題ごとに変化する側、`b` は常に `a` と同値のため専用フィールドを持たない。
- `generate_squ_problems`(数列 `a` の生成): `order = ini.rows * ini.columns` 問を1ページ分生成する。`a` は `-a/--a-value`(`start_num`)を起点とする `start_num..start_num+order-1` の連番で、`c = a * a`。`--descend` で `start_num+order-1..start_num` の降順に反転し、`--shuffle` で(`--descend` 反転後の並びを)`random.shuffle` する。`nuts_calc.py` の `get_fixed_format_data`(`mode == 'squ'`、`nuts_calc.py:508-526,541-542`)と同じ意味論(`num_list = [start_num+i for i in range(order)]`)だが、`order` を `99` と同じく `rows*columns` に連動させている(`nuts_calc.py` 側は `order = rows` で列ごとに `start_num` がリセットされる設計だが、`nuts_calc_tex.py` は `99`/`aBc` で確立済みの「1ページ分をフラットな `rows*columns` 件の列とみなす」方針をそのまま踏襲した)。`start_num` はページをまたいでも変化しない(`nuts_calc.py` 側で `ini.a_value` が書き換えられる箇所がないことを踏襲し、各ページで同じ起点から独立して数列を生成し直す)。`nuts_calc.py` と同じくコード共有はせず独立に再実装している。
- `build_squ_block_tex`: 通常は `n) $a \times a = c$` を生成する。blank 版は `c` の代わりに、下線を伴わない固定幅の `\hspace{1.5em}` を出力する。`--reverse` 指定時は式の左右を入れ替えて `n) $c = a \times a$` にする(blank でも隠すのは常に `c`)。`build_kuku_block_tex` の `reverse` 処理と同じ構造。
- `build_squ_page_pair`/`build_squ_pages`: `99` と同じ構造。`Page.layout` は常に `'inline'`(`--vertical` 未対応)。`--with-bottom-answer` 指定時は `build_squ_bottom_answer_tex` で `(index) c` の一覧を blank ページ末尾に追加する。
- `build_squ_csv_rows`: 1問1行、`[page_number, index, a, c]` の列で CSV を書き出す(`b` は常に `a` と同値のため冗長な列を持たない、`99` の `[..., a, b, c]` との差異)。

### `pi` コマンド(Phase 8)

- `PiProblem` データクラス(`index`/`a`/`c`)が1問を表す。`squ` の `SquProblem` と同じ形(`b` は常に `PI_MULTIPLIER`(3.14)で固定のため専用フィールドを持たない)。
- `generate_pi_problems`(数列 `a` の生成): `order = ini.rows * ini.columns` 問を1ページ分生成する。`a` は `-a/--a-value`(`start_num`)を起点とする `start_num..start_num+order-1` の連番で、`c = round(a * PI_MULTIPLIER, 2)`。`--descend`/`--shuffle` の意味論は `generate_squ_problems` と全く同じ(`descend` で降順反転、`shuffle` で反転後の並びをさらにランダム化)。`nuts_calc.py` の `get_fixed_format_data`(`mode == 'pi'`、`nuts_calc.py:508-522,527-530,541-542`)と同じ数列生成・意味論だが、`c` の丸め方が異なる(後述)。`nuts_calc.py` と同じくコード共有はせず独立に再実装している。
- `build_pi_block_tex`: 通常は `n) $a \times 3.14 = c$` を生成する。blank 版は `c` の代わりに、下線を伴わない固定幅の `\hspace{1.5em}` を出力する。`--reverse` 指定時は式の左右を入れ替えて `n) $c = a \times 3.14$` にする(blank でも隠すのは常に `c`)。`build_squ_block_tex` の `reverse` 処理と同じ構造。
- `build_pi_page_pair`/`build_pi_pages`: `squ` と同じ構造。`Page.layout` は常に `'inline'`(`--vertical` 未対応)。`--with-bottom-answer` 指定時は `build_pi_bottom_answer_tex` で `(index) c` の一覧を blank ページ末尾に追加する。
- `build_pi_csv_rows`: 1問1行、`[page_number, index, a, c]` の列で CSV を書き出す(`squ` と同じ列構成、`b` は常に `PI_MULTIPLIER` で固定のため冗長な列を持たない)。
- `pi` は issue #19 が計画する7コマンドの最後の1つで、Phase 1 時点のプレースホルダーコンテンツ(`build_placeholder_page`/`build_placeholder_pages`)を実データ生成に置き換える形で実装した。全7コマンドが実データを持つようになったため、これらのプレースホルダー関数と `main()` の CSV フォールバック(プレースホルダー相当の行を書き出す分岐)は Phase 8 で削除した。

### `evenodd`/`multiples`/`divisors` コマンド(issue #94)

- `docs/uiux/calculation_drill_menu_parameters_v1.md` の小学5年生表にある「偶数・奇数」「倍数」「約数」(いずれも固有設定なしの基礎ドリル)に対応する3つの独立した top-level command。`squ`/`pi`/`aBc` と同じ「1ドリル形状=1コマンド」規約に従い、`numprop` 系の単一コマンド+サブモードにはしていない。
- 3コマンドとも `com`/`99`/`squ`/`pi` のような単一の `-a/--a-value` を必須にせず、既存の `--a-min`/`--a-max`(既定1〜9)から**問題ごとに独立して**ランダムな基準値を抽選する(`ope` の二項生成と同じ per-problem 抽選パターン)。1ページに複数の独立した問題を並べるドリルであり、`squ`/`pi` のような単一の連続数列や `com`/`99` のような単一ターゲットにはそぐわないための設計判断。
- `evenodd`: `EvenOddProblem`(`index`/`a`/`is_even`、`label` プロパティが `'even'`/`'odd'` を返す)。`generate_evenodd_problems(nums_a, order, start_index)` が `nums_a` から `random.choice` で `a` を抽選し `a % 2 == 0` を判定する。
- `multiples`: `MultiplesProblem`(`index`/`a`/`multiples: list[int]`)。`generate_multiples_problems(nums_a, order, start_index, count)` が抽選した `a` の `a, 2a, ..., count*a` を返す。`count` は新設の `--multiples-count`(既定 `DEFAULT_MULTIPLES_COUNT`=4、最小 `MIN_MULTIPLES_COUNT`=1)で制御し、`_init()` は `command == 'multiples'` のときのみこのオプションを許可する。
- `divisors`: `DivisorsProblem`(`index`/`a`/`divisors: list[int]`)。`generate_divisors_problems(nums_a, order, start_index)` が抽選した `a` の約数を `range(1, a+1)` の総当たりで昇順に列挙する(1と`a`自身を必ず含む)。追加オプションはない(常に全約数)。
- `_init()` は `command in ('multiples', 'divisors')` のとき `--a-min >= 1` を要求する(`multiples`/`divisors` はともに0以下の基準値が数学的に無意味なため。`evenodd` は負数でも偶奇判定が可能なためこの制約はない)。
- レンダリングは3コマンドとも `aBc`/`squ` と同じ `n) $a \Rightarrow 結果$` 形式(`build_evenodd_block_tex`/`build_multiples_block_tex`/`build_divisors_block_tex`)。blank 版は既存の `BLANK_ANSWER_TEX`(`\hspace{1.5em}`)で結果全体を隠す(`multiples`/`divisors` の可変長リストに対しても、項目ごとの個別空欄ではなく単一の空欄で答え全体を隠す、`aBc` の複数桁答えと同じ簡素化方針)。
- **CJK制約への対応**(issue #93 の `--with-name-field` と同じ理由): 本ファイルは素の `pdflatex`(CJK/日本語フォント未読込)でコンパイルしており、日本語グリフを含む文字列を渡すと `Fatal error occurred, no output PDF file produced` で確実に失敗する。`evenodd` の答えは本来「偶数」「奇数」だが、これを踏襲できないため英語 `even`/`odd` を採用した。`\mathrm{even}`/`\mathrm{odd}`(コアLaTeX2eの `\mathrm`、追加パッケージ不要)で数式モード内に upright 表示する。`multiples`/`divisors` の答えは数字とカンマのみのためこの制約に該当しない。
- `build_evenodd_pages`/`build_multiples_pages`/`build_divisors_pages` は `squ`/`pi` と同じ構造(`order = ini.rows * ini.columns` 問をページごとに生成、`--with-bottom-answer` で `build_X_bottom_answer_tex` を末尾に追加)。`Page.layout` は常に `'inline'`(`--vertical` 等は他コマンドと同じく `_init()` の汎用チェックで拒否される)。
- CSV列: `evenodd` は `[page_number, index, a, label]` の固定4列。`multiples`/`divisors` はリスト長が可変のため、`build_multiples_csv_rows`/`build_divisors_csv_rows` はリストをスペース区切りの単一文字列に変換した `[page_number, index, a, "6 12 18 24"]` 形式にする(多項 `ope`/`mixed` の自己記述文字列カラムと同じ方針)。
- `main()` のディスパッチは `squ`/`pi` と同じパターンで `evenodd_pages_problems`/`multiples_pages_problems`/`divisors_pages_problems` の3変数を追加し、`ini.command` の分岐と CSV 書き出し分岐の両方に対応する `elif` を追加した。

## 重要な設計判断とその理由

### `aBc` の4桁表示を常にゼロ埋めする理由(`nuts_calc.py` との差異)

`nuts_calc.py` の `get_aBc_data` は `abcd` を整数として結合してから `len(str(abcd)) == 3` の場合だけゼロ埋めする(`nuts_calc.py:577-578`)という部分的な対応で、2桁以下になるケース(例: `a=0, b=0, c=0, d=5` → `"5"`)はゼロ埋めされないまま表示される潜在的な不整合がある。`nuts_calc_tex.py` はこれを踏襲せず、`AbcProblem.abcd_display` が常に `f"{a}{b}{c}{d}"` で4桁全てを個別に文字列化するため、先頭が0の場合も含めて常に4桁で表示される。

### `99` の問題数を `--rows`×`--columns` に連動させた理由

issue #24 の Scope には "single times-table row" とあるが、実装着手時に `nuts_calc.py` の元実装(`order = rows`、当時は乗数がページの行数に連動し9で頭打ちにならなかった)を確認した上でユーザーと相談し、「1ページ9問固定」ではなく `ope`/`com` と同じ `order = rows * columns` によるタイル化を採用することを明示的に決定した(9問固定案は却下)。この「問題数を `rows × columns` に連動させる」タイル化自体は issue #152 後も変更していない(変わったのは下記の乗数の値域のみ)。`-a/--a-value`(段)の値域は `nuts_calc.py` に合わせて1〜9への制限を行わない(`100` コマンドの桁数バリデーションとは異なる判断、こちらも変更なし)。

### `99` の乗数(b)を1〜9に制限しなかった判断を issue #152 で覆した理由

上記の issue #24 での決定時点では、乗数 `b` の値域を1〜9に制限しないことも合わせて確認されており(`order` が9を超えれば `b` もそれに応じて9を超える)、`nuts_calc.py` の元実装(修正前)の挙動をそのまま踏襲する設計だった。issue #149 で `nuts_calc.py` 側がこの挙動を「実在しない九九(例: `×10`)を出題してしまうバグ」として修正し(乗数を1〜9で折り返す)、その修正時点では `nuts_calc_tex.py` 側は独立した実験的プロトタイプであり、かつ issue #24 で明示的に確認済みの設計判断だったことを理由にスコープ外とした。しかし `NUTS_CALC_RENDERER=latex` 環境での実機確認により、この「意図的な非対称」が実際のユーザー体験としては同じ不具合(標準の九九に存在しない乗数が出題される)を引き起こすことが判明したため、issue #152 でこの判断を覆し、`nuts_calc.py` と同じ折り返し挙動(`KUKU_MULTIPLIER_MAX = 9` で周期化)に統一した。

### `100` の `-a`/`-b` 桁数変換を `nuts_calc.py` の挙動から意図的に修正した理由

`nuts_calc.py` の元実装は、`100` コマンドで `-a`/`-b` が**省略された場合のみ** `set_min_max_value` で桁数1のレンジに変換し、明示的に `-a 2` 等を指定した場合は `a_value` が保存されるだけでレンジには反映されない(桁数3超のガードのみ効く)、という一貫性のないバグが `nuts_calc.py:245-255` に存在する。`nuts_calc_tex.py` ではこれを再現せず、`_init()` の桁数レンジ変換を `command in ('ope', '100')` の場合に常に適用するよう統一した(`-a`/`-b` が `None` でなければ常に変換)。Phase 3(`com`)で `nuts_calc.py` 側の冗長な前処理を踏襲しなかったのと同じ方針。

なお、この桁数レンジ変換を先に実装した際、`100` の桁数バリデーション(1〜3の範囲チェック)を変換の**後**に置いてしまい、`-a 6` 以上で `set_min_max_value` 内の `digits_list[value - 1]` が `IndexError` を送出する(`digits_list` は5要素)、`-a 0` 以下で負のインデックスにより誤った(意図しない5桁の)レンジが黙って採用される、という2つの実バグが生じていた(PR #31 の codex レビューで指摘、修正済み)。現在は `_init()` 内でこのバリデーションを `set_min_max_value` 呼び出しより前に移動している。

### `-a`/`-b` の桁数レンジ変換を `ope` 限定にゲートしている理由

`_init()` は元々、`command` に関わらず `-a/--a-value` が指定されると `set_min_max_value()`(`value` を「桁数」とみなし `digits_list[value - 1]` で範囲を引く、`digits_list` は5要素)で `a_min`/`a_max` に変換していた。`com` は `nuts_calc.py` の意味論を踏襲して `-a` を「桁数」ではなく「補数のターゲット値そのもの」として使うため、`-a 100` のような(5を超える)値を渡すと `digits_list[99]` で無条件 `IndexError` になる潜在バグがあった(issue #22 の実装着手時に発見)。`com` を実装するにあたり、この変換を `command == 'ope'` の場合のみ行うようゲートし、`com` の `a_value` は生の整数のまま `generate_com_problems` に渡るようにした。

### `--vertical` のグリッドレイアウトを行ごとに独立した `tabular` に分割している理由

`--vertical` ブロック(xlop/longdivision の出力)は複数行にまたがる LaTeX コンテンツのため、横書きプレースホルダーで使っている `\hspace` によるテキスト結合(`build_inline_grid_tex`)では列が揃わない。当初は1ページ分の全ブロックを1つの `tabular` にまとめていたが、**LaTeX の `tabular` はページをまたいで自動改ページしない**ため、既定の `-r 10` のような行数の多いグリッドでは、その `tabular` 全体がページに収まらず丸ごと次ページへ送られ、結果として1ページ目が空白になり2ページ目の下端から内容が溢れて実質的に問題が失われる不具合が実機コンパイルで確認された。この問題を避けるため、`build_tabular_grid_tex`(`nuts_calc_tex.py:284-314`)は**行ごとに独立した1行だけの `tabular`** を生成し、既存の `\par\vspace` 区切り(`build_inline_grid_tex` と同じ)で連結する設計にしている。これにより通常の段落と同様に行単位で自然に改ページできる。回帰テスト: `backend/tests/test_nuts_calc_tex.py::test_cli_ope_vertical_default_rows_does_not_drop_content`。

列幅は `\dimexpr(\textwidth-2N\tabcolsep)/N\relax`(`N`=列数)で動的に計算しており、用紙サイズ(A3/A4/B5/A4横)や列数が変わっても `\textwidth` に追従する。

横書きの `build_inline_grid_tex` と筆算の `build_tabular_grid_tex` は、共通の `build_column_major_rows` を使って問題ブロックを列優先の視覚行に変換する。これにより、どちらの形式でも左端の列を上から下へ読んだときに問題番号が連番となり、2列なら `1, 2, ...` の右側に次の列の問題が置かれる。問題データやCSVの生成順は変えず、変更するのはPDF上の配置だけである。

### 横書き問題を等幅セルと可変行間で配置する理由

横書きの問題を固定の`\hspace`と行間で結合すると、ページの左上に寄り、列数が少ない場合は中央に過大な空白が生じる。`build_inline_grid_tex`は本文幅からセル余白を引いた幅を列数で等分する`p{...}`セルを使い、各問題をそのセル内で中央揃えにする。そのため2列では各半ページの中央、4列では各4分割領域の中央に問題が置かれる。各行の前に`\vfill`を置くことで、ヘッダー、任意の下部解答欄、下40mmのフッタ領域を除いた可用高さに行を均等配分する。

100マス表は内部で`tabular`を生成する自己完結ブロックのため、横書きグリッドのセルに入れるとLaTeXの表がネストしてコンパイルできない。`layout='block'`で別扱いにし、`\vfill`で本文内に配置することで、同じ余白方針を守りながらネストを回避する。

### 筆算で用紙別の既定行数を使う理由

筆算は `xlop`/`longdivision` が複数行の数式を出力するため、通常計算用の既定10行×2列(20問)をそのまま使うと、1つの論理ページがLaTeXの自動改ページで複数の物理PDFページに分割される。`VERTICAL_DEFAULT_ROWS_BY_PAPER_SIZE` は、最も高さを要する3桁×2桁の掛け算を基準に、既定2列で1ページに収まる行数を用紙別に定める。通常形式の既定10行は変えず、ユーザーが `--rows` を指定した場合はその意図を優先するため上限チェックや自動縮小は行わない。

### blank(練習用)版の実現方法が xlop と longdivision で異なる理由

`longdivision` は `stage=0` オプションで「除数・被除数の枠のみ」を表示するモードを最初から持っている(vendoring 時に確認済み)。一方 `xlop` には同等の「結果を隠す」フラグが存在しないため、`xlop` が公開している桁ごとのスタイルフック(`resultstyle`/`carrystyle`/`intermediarystyle`、いずれも各桁の描画をラップするマクロを差し替えられる)に `\phantom` を割り当てることで、**数字だけを不可視化しつつレイアウトの寸法は保持する**という実質的に同じ効果を得ている。実機コンパイルで、blank/filled 両方の罫線位置が一致することを目視確認済み。

### `mix` の演算子は生成時点で確定させる

`--operator mix` は `generate_ope_problems` が問題ごとにランダムな演算子(add/sub/mul/div)を選んで `OpeProblem.operator` に確定値として保存する。レンダラー(`build_vertical_block_tex`/`build_horizontal_block_tex`)は `'mix'` という値を一切扱わず、常に具体的な4演算子のいずれかだけを見ればよい。

### `--intermediate` は `-o mul` 単独・`--vertical` 併用不可

`nuts_calc.py` の `--intermediate`(`b_max` が1桁を超えると失敗)と同じ制約に加え、`nuts_calc_tex.py` では暗算メモ技法が数学的に mul 専用のため `args.operator != ['mul']` の場合も `_init()`(`nuts_calc_tex.py:211-219`)で明示的に拒否している。`nuts_calc.py` 側は `mix` 等と組み合わせても実行時まで気づかない潜在バグがあるが、ここでは意図的にそれより厳格にした。

### `--merge` のセマンティクス(`nuts_calc.py` との違い)

`nuts_calc.py` の `--merge` は「回答ページを1ページ遅延させて次ページに挿入する」("next_content" の仕組み)という独特の割り込み方をするが、`nuts_calc_tex.py` はこれをあえて単純化し、**各ページの直後にその回答ページを続ける**(page1(blank) → page1(answer) → page2(blank) → page2(answer) → ...)方式にしている。実装がシンプルになり、LaTeX 1回のコンパイルで完結する(PDF マージ用の追加ライブラリが不要)というメリットがあるための意図的な設計判断。

### `longdivision` パッケージの vendoring

`longdivision`(CTAN、LPPL ライセンス)は Ubuntu の `texlive-latex-extra` に同梱されていないため、`vendor/texmf/tex/latex/longdivision/longdivision.sty` としてリポジトリに同梱し、`compile_tex` が `TEXINPUTS` 環境変数にこのパスを追加することで、クローン後に手動で `TEXMFHOME` へ配置しなくても `pdflatex` から解決できるようにしている(`nuts_calc_tex.py:43,362`)。`xlop`(add/sub/mul の繰り上がり・部分積表示に使用、Ubuntu 標準の `texlive-latex-extra` に同梱)はプリアンブルで読み込むのみで vendoring 不要。

### `pi` の答え `c` を小数点2桁に丸める理由(`nuts_calc.py` との差異)

`nuts_calc.py` の `get_fixed_format_data`(`mode == 'pi'`)は `c = a * 3.14` を丸めずそのまま `str()` で表示する。`PI_MULTIPLIER`(3.14)は小数点2桁の定数であり、整数 `a` との積は数学的には常に小数点2桁で表現できるはずだが、IEEE 754 の浮動小数点乗算は一部の `a`(例: `a=5` で `5 * 3.14 == 15.700000000000001`、`a=10` で `31.400000000000002`)で丸め誤差由来の余分な桁を生成する。`nuts_calc.py` はこれをそのまま印刷ドリルに表示してしまう潜在的な見栄えの悪さがあるが、`nuts_calc_tex.py` はこれを踏襲せず `generate_pi_problems` で `round(a * PI_MULTIPLIER, 2)` を使い、印刷結果に誤差由来の桁が現れないようにしている(`aBc` のゼロ埋め、Phase 6と同様、`nuts_calc.py` の不備を意図的に踏襲しない方針)。

### `nuts_calc.py` の `VERTICAL_UNSUPPORTED_OPERATORS` を踏襲しない

旧 `nuts_calc.py` の `--vertical` は `div`/`mix` を拒否していたが、issue #46 で ReportLab 側の筆算機能自体が削除された。`nuts_calc_tex.py` はこの旧制約を踏襲せず、xlop/longdivision により div/mix も筆算表示する。現在、筆算は LaTeX renderer に一本化されている(`nuts_calc.py` に `--vertical` 引数はない)。

### `--use-parentheses` の第3項以降が `-b`/`--b-value` のレンジを再利用する理由(issue #67、issue #71 でN項に一般化)

3つの数 `a`/`b`/`c` に対して専用の CLI フラグ(`--c-min`/`--c-max` 等)を追加せず、`c` は `b` と同じレンジ(`nums_c = nums_b`)から抽選する設計にしていた(旧実装)。issue #71 のN項一般化では、`assign_tree_operands()` が中間順走査で最初の葉(旧`a`に相当)のみ `nums_a`、それ以外の全ての葉(旧`b`/`c`に相当する2つ目以降すべて)を `nums_b` から抽選する形で、この規約をそのまま任意項数へ引き継いでいる。既存の CLI サーフェスを変えずに済むという理由に加え、後述のように広いレンジにすると解の存在しない演算子/構造の組み合わせが生じることを実装時のシミュレーションで確認したため、2つ目以降の項を意図的に狭いレンジへ固定する設計上の要請とも一致する。

### `--use-parentheses` で演算子・かっこの構造を問題ごとにランダム化する理由

初期実装では `-o/--operator` にちょうど2つの演算子を要求し、1回のCLI実行(1枚のプリント)内で演算子ペアとかっこの位置(常に `(a op b) op c`)が固定だった。「かっこの位置・かっこ内の演算子・式全体のパターンが単調」というレビュー指摘を受け、`generate_ope_problems` の `mix` 展開と同じ仕組みを二段階(`op_left`/`op_right`)に拡張し、`position`(`'left'`/`'right'`)も含めて問題ごとに独立して抽選するよう変更した(issue #67)。これにより `-o/--operator` は通常の `ope` と全く同じ受け付け方(`mix` を含む1〜4個)になり、専用のバリデーション(旧: ちょうど2個・`mix` 不可)は撤廃した。issue #71 では、この「問題ごとに構造・演算子をランダム化する」考え方をN項へ一般化し、`op_left`/`op_right`/`position` という固定2値の概念を「ランダムな2分木構造」+「`--mixed-operators` の有無による演算子選択方式(木全体で1つ、またはノードごとに独立)」に置き換えた。

### 数値レンジと演算子/構造の組み合わせによる `ValueError` リスクを軽減する設計

`generate_tree_ope_problems`(旧 `generate_paren_ope_problems`)はランダムな木構造・演算子の組み合わせに対してオペランドを再抽選するだけで、`calc_sub`/`calc_div` のような決定的フォールバックは持たない。実装時のシミュレーション(`a`/`b`/`c` を全て2桁(10〜99)にした場合)で、例えば `position='right'`, `op_right='mul'`, `op_left='sub'`(`a - (b × c)`)のような組み合わせは `b × c` が `a` の取りうる最大値を大きく超えるため、1000回の再抽選内で正の結果が一度も得られず確実に失敗することを確認した(旧3項固定実装での検証結果)。この失敗を避けるため、Web プリセット(`drillPresets.js` の `g4/g5/g6-parentheses*`)は `a` の桁数だけを学年で増やし(1桁→2桁→3桁)、`b`/`c` は常に1桁のレンジに留める設計にしている。この組み合わせは全32通り(演算子4×4×位置2)がシミュレーション上安定して解を持つことを確認済み。issue #71 のN項一般化では、木のノード数がN-1個に増えるほど各ノードが独立に無効化しうる箇所も増えるため、**同じ桁数レンジでも項数が増えるほど `ValueError` のリスクは旧3項固定実装より悪化する**(既知の制限、後述)。issue #73 でWeb層(`drillPresets.js` の `examPrep` プリセット、27通り)を配線する際にこのリスクを再検証しており、`a`(最初の項)だけ学年で桁数を上げ(1桁→2桁→3桁)、残りの全項は1桁に留める設計(既存の `g4/g5/g6-parentheses*` と同じ規約)を項数5・かっこ+演算子混合まで拡張した上で、600〜4000問のシミュレーションで失敗ゼロを確認済み(`backend/tests/test_nuts_calc_tex_exam_prep_presets.py`)。

### `--missing-value` の blank 候補から答え `c` を除外する理由(issue #69)

実装時の初期版は `MISSING_VALUE_POSITIONS = ('a', 'b', 'c')` として3候補すべてから抽選していたが、ユーザーレビューで「`c`(答え)を隠すのは通常の `ope`(常に答えを隠す)と区別がつかず、虫食い算(式中の数を問う)の本質ではない」という指摘を受け、`('a', 'b')` の2候補(演算子の両オペランドのみ)に限定した。これに伴い `build_missing_value_block_tex()` は `c` を条件分岐なしに常に実値表示する形へ簡略化し、`MISSING_VALUE_TEX_VALUES` の `'c'` キーも削除した(到達不能になる分岐を残さない)。

### `COM_BLANK_ANSWER_TEX` を `BOXED_BLANK_TEX` にリネームした理由(issue #69)

`com` コマンドの欠けた加数を示す角枠 LaTeX(`\fbox` ベース)は、`--missing-value` の欠けたオペランドにもそのまま流用できる見た目だったため、`com` 専用を示唆する名前 `COM_BLANK_ANSWER_TEX` から、用途を限定しない `BOXED_BLANK_TEX` にリネームして両方の呼び出し元(`build_com_block_tex`/`build_missing_value_block_tex`)で共有した。

### `--with-name-field` のラベルに日本語「なまえ：」ではなく英語 `Name:` を採用した理由(issue #93)

issue の Scope 本文は日本語ラベル「なまえ：____________」を提案していたが、本ファイルは素の `pdflatex`(CJK/日本語フォントパッケージ未読み込み、プリアンブル参照)でコンパイルしており、日本語グリフを含む文字列を渡すと `Fatal error occurred, no output PDF file produced` で確実に失敗する(issue #91 の余り表記「あまり」→`\cdots` と同じ制約、詳細は上記の `ope --remainder` セクション参照)。既存ヘッダー(`Date:`/`Time:`)自体が英語表記であることとも整合させ、英語 `Name:` を採用した。この制約への根本対応(LuaLaTeX 等の日本語対応エンジンへの移行、および `docs/latex/tex_calculation_drill_layout_guidelines.md` に基づくレイアウト統一)は issue #104(トラッキング issue)として切り出し済みで、実装は #120(本ファイルの `LatexEngineAdapter` 抽象化、対応済み)→ #121(日本語対応エンジンアダプターの評価・実装、対応済み、下記参照)→ #122(レイアウト統一)に分解されている。**この `Name:` 英語ラベル自体は #121 でも置き換えていない**(#121 のスコープは新アダプターが日本語テキストをクラッシュせずコンパイルできることの確立のみで、既存の英語回避策を実際に日本語へ置き換えるのは別スコープと issue 本文に明記されているため)。

### `LuaLatexEngineAdapter` の採用理由と `Noto Sans CJK JP` フォント選定(issue #121)

- **エンジン選定**: 日本語対応の選択肢として LuaLaTeX+fontspec+CJKフォント、LuaLaTeX+luatexja、upLaTeX(pLaTeX系)の3案を比較した。このマシン(Ubuntu)では `lualatex`/`fontspec` は導入済みで、不足していたのは fontspec が LuaLaTeX 上でフォントを読み込むために必要な `luaotfload` のみだった。`luaotfload` は `texlive-luatex` パッケージ(`sudo apt install texlive-luatex` で2パッケージ、既存の `texlive-latex-extra` 等の依存で完結)で導入できる。一方 `luatexja`(正式な日本語組版に必要な禁則処理・JFM字間パッケージ)は、Ubuntu では `texlive-lang-japanese` 経由でのみ提供され、これは `texlive-lang-cjk`(中国語・韓国語・タイ語フォント一式を含む114パッケージ)を巻き込む。upLaTeX も同じ `texlive-lang-japanese` が必要になる。#121 のスコープ(短い日本語文字列がクラッシュせずコンパイルできることの確立のみ、段落単位の日本語組版への置き換えは明示的にスコープ外)では禁則処理・JFM字間は不要なため、導入コストが軽い LuaLaTeX+fontspec+CJKフォント案を採用し、luatexja/upLaTeX は段落テキストが必要になった時点の再検討事項として見送った。副次的な利点として、LuaLaTeX は `luatex85`(`texlive-luatex` に含まれる pdfTeX 互換レイヤー)により pdfTeX 時代のパッケージ(`xlop`/`longdivision`)との互換性リスクが upLaTeX(pTeX系列の別プリミティブ体系)より低い。
- **`xlop`/`longdivision` の出力が無影響であることの検証**: 両パッケージは筆算の数字を内部的に数式モードでタイプセットしており、`\setmainfont`(fontspec)はテキストモードの地の文フォントのみに作用し数式モード(Computer Modern Math)には影響しない。このため `pdflatex` 版と `LuaLatexEngineAdapter` 版で `\intlongdivision`/`\opdiv` ブロックの出力を画像比較し、画素単位で完全一致することを実機確認済み(`test_cli_ope_vertical_produces_pdfs_under_lualatex_engine` が回帰として自動化)。
- **等幅(モノスペース)CJKフォントを採用しなかった理由**: 実装当初、桁揃えの崩れ防止を目的に `Noto Sans Mono CJK JP`(等幅)を検討したが、上記の通り筆算の桁揃えは数式モード側(常に等幅な Computer Modern Math の数字)が担っており `\setmainfont` の変更はこの目的に一切寄与しないことが判明したため、動機が成立しないと判断し通常の `Noto Sans CJK JP`(プロポーショナル)を採用した(ユーザー確認済み)。数式フォント自体の変更(`unicode-math` 等)も、CM Math が最初から等幅数字を持ち実績があること、CJKフォントは数式フォントに必要な MATH テーブルを持たないこと、`xlop`/`longdivision` が CM Math のメトリクスを前提にしている可能性があることから、リスクに見合わないと判断し見送った。
- **既知の制限**: `\setmainfont` はドキュメント全体の地の文(数式モード外)のフォントを変更する。`Date:`/`Time:`/`Name:`/フッター(著作権・ページ番号)等の英語ラベルも、この lualatex エンジン選択時は `Noto Sans CJK JP` で描画される(pdflatex エンジンの Computer Modern から見た目が変わる)。数式モード内の数字・記号は影響を受けない。この副作用は許容範囲と判断し、Japanese 文字だけを対象にフォントを切り替える(スパン単位でのフォント切り替えマクロを全文字列生成箇所に配線する)といった、より侵襲的な設計は見送った。

## 統合ポイント

- 呼び出し元: CLI 直接実行(`python3 nuts_calc_tex.py <paper_size> <command> ...`)と、`NUTS_CALC_RENDERER=latex` を設定した `backend`。backend は `renderers.py:48-54,170-189` で script を選択し subprocess 起動する。`nuts_calc.py` と `factory.sh` からは呼ばれない。
- 呼び出し先: `NUTS_CALC_TEX_ENGINE` 未設定時は既定エンジンの `lualatex`(要 `texlive-luatex`、`fonts-noto-cjk`。issue #121/#186、詳細は `CLAUDE.md` の Local Tooling Environment を参照)を呼び出す。`NUTS_CALC_TEX_ENGINE=pdflatex` 明示指定時は代わりに `pdflatex`(要 LaTeX ディストリビューション、`texlive-latex-base` + `texlive-latex-extra`)を呼び出す。

## 注意事項・既知の制限

- **issue #19 が計画する7コマンド全てが実装済み**: `ope`/`com`/`100`/`99`/`aBc`/`squ`/`pi` は全て実データを生成する。Phase 1 時点のプレースホルダーコンテンツ・関数(`build_placeholder_page`/`build_placeholder_pages`)は Phase 8(issue #27)で削除済み。
- **`100` は `--a-min`/`--a-max` を極端に狭めると `ValueError` になりうる**: `sample_hundred_square_values` は候補範囲を2倍に複製してから10個抽出するため、範囲の要素数が5未満(例: `--a-min 5 --a-max 5`)だと母集団不足で `random.sample` が例外を送出する。`nuts_calc.py` 側の元実装にも同型の潜在バグがあり、本 Phase のスコープ外として未対応。
- **既定エンジンのバイナリが必須**: `shutil.which(engine_adapter.binary_name)` が `None` の場合は明確なエラーメッセージ(`"<binary_name> not found"`)で `exit(1)` する。`NUTS_CALC_TEX_ENGINE` 未設定時の既定は `lualatex`(issue #186)のため、通常は `lualatex` が必須。CI やローカル環境に LaTeX が無い場合、`backend/tests/test_nuts_calc_tex.py` は `pytest.mark.skipif` で自動的にスキップされる(`backend/tests/test_nuts_calc_tex_ope_generation.py`/`backend/tests/test_nuts_calc_tex_com_generation.py`/`backend/tests/test_nuts_calc_tex_kuku_generation.py`/`backend/tests/test_nuts_calc_tex_squ_generation.py`/`backend/tests/test_nuts_calc_tex_pi_generation.py` の純 Python ユニットテストは pdflatex なしでも実行される)。このファイル自身の skip 条件は歴史的経緯で `pdflatex` の有無のみを見ており(`shutil.which("pdflatex") is None`)、`NUTS_CALC_TEX_ENGINE` の既定変更後もほとんどのテストは env 変数未指定のまま(=`lualatex` 経由で)実行される。`NUTS_CALC_TEX_ENGINE=pdflatex`(issue #121)を明示指定する場合は同様に `pdflatex` が必須で、`backend/tests/test_nuts_calc_tex_lualatex_engine.py` は `lualatex` が無い環境では同じ `pytest.mark.skipif` パターンで自動スキップされる(`backend/tests/test_nuts_calc_tex_engine_adapter.py` のアダプター選択・プリアンブル生成テストはどちらの LaTeX バイナリも不要な純 Python テスト)。`test_cli_fails_clearly_when_pdflatex_missing`/`test_cli_fails_clearly_when_lualatex_missing_by_default`(issue #186)は、それぞれ明示的な `pdflatex` 選択・env 変数未指定(既定 `lualatex`)の2経路で binary-missing エラーメッセージを検証する。
- **`--descend`/`--reverse`/`--shuffle` は `ope`/`com`/`100` でも引数として受理されるが未使用**: `99`/`squ`/`pi` コマンドでのみ意味を持つ。`--debug` はどのコマンドでも未使用のまま。
- **`com`/`99`/`aBc`/`squ`/`pi` は `--vertical`/`--intermediate` 未対応、ただし挙動が異なる**: `--vertical` は指定しても静かに無視され(`build_com_pages`/`build_kuku_pages`/`build_abc_pages`/`build_squ_pages`/`build_pi_pages` は `Page.layout` を常に `'inline'` にする)、`com` は常に横書き(`n) $a + □ = target$`)、`99` は常に横書き(`n) $a \times b = c$`、`--reverse` 指定時は式の左右が入れ替わる)、`aBc` は常に横書き(`n) $abcd \Rightarrow answer$`)、`squ`/`pi` は常に横書き(それぞれ `n) $a \times a = c$`/`n) $a \times 3.14 = c$`、`--reverse` 指定時は式の左右が入れ替わる)で出力される。一方 `--intermediate` は無視されず、`_init()`(`nuts_calc_tex.py:247-249`)が `command != 'ope'` を検知した時点で `"--intermediate is only supported for the 'ope' command."` として `exit(1)` する(`com`/`99`/`aBc`/`squ`/`pi` いずれでも同様、`--vertical` の有無に関わらない)。それぞれ issue #22/#24/#25/#26/#27 のスコープ外。`evenodd`/`multiples`/`divisors`(issue #94)も同じ扱いで、`--vertical` は静かに無視され常に横書き(`n) $a \Rightarrow 結果$`)、`--intermediate` は同じ `_init()` の汎用チェックで `exit(1)` する。
- **`squ`/`pi` の数列(a)は9で頭打ちにならない**: `order = ini.rows * ini.columns` が9を超えると `squ`/`pi` の数列はそれに応じて9を超える(`nuts_calc.py` の元実装を踏襲した意図的な設計、詳細は上記の設計判断を参照)。`99` の乗数(b)は issue #152 でこの挙動から除外され、`KUKU_MULTIPLIER_MAX`(=9)で周期的に折り返すようになった(`squ`/`pi` は対象外、現状維持)。
- **`--vertical` 指定時の CSV/bottom-answer の桁**: 特別な整形はしておらず、`build_ope_csv_rows`/`build_ope_bottom_answer_tex` は横書き・縦書きで共通(問題データそのものは表示形式に関わらず同一)。
- **`pi` の答え `c` は丸め済み**: `generate_pi_problems` が `round(a * PI_MULTIPLIER, 2)` を返すため、`build_pi_csv_rows`/`build_pi_bottom_answer_tex`/`build_pi_block_tex` はいずれも丸め後の値のみを扱う(`nuts_calc.py` の生の浮動小数点値との差異、詳細は上記の設計判断を参照)。
- **`ope --use-parentheses`(N項一般化後)は決定的フォールバックを持たない**: `calc_sub`/`calc_div` と異なり、`generate_tree_ope_problems` は木構造・演算子・オペランドの組み合わせ全体を単純な再抽選(`MAX_OPERAND_RETRY_ATTEMPTS` 回)のみで解を探す。`a`/`b`/`c` の全レンジが広い(特に2桁以上)状態で `sub`/`div` を含む組み合わせ(例: `a - (b × c)`)は、有効な解がほぼ存在せず `ValueError` になりうることをシミュレーションで確認済み(詳細は上記の設計判断を参照)。呼び出し側は最初の葉以外(`-b`/`--b-value` 由来)を狭いレンジに保つことでこれを回避する。**項数(`--terms`等)が増えるほど木のノード数も増え、`ValueError` のリスクは旧3項固定実装よりさらに悪化する**(issue #71)。
- **`ope --terms`/`--terms-min`/`--terms-max`/`--mixed-operators` の項数floor/上限は `failure()`/`exit(1)` ではなくクランプする**(issue #71、意図的な例外): 通常の `ope` では2項未満、`--use-parentheses` 使用時は3項未満を要求してもエラーにならず、該当する下限(2または3)に自動的に引き上げられる。`MAX_OPE_TERMS`(12)を超える値も上限にクランプされる。本ファイルの他の数値バリデーションはすべて `failure()` による即時エラーであり、この挙動は唯一の例外(`resolve_term_range()` 参照)。
- **`ope --use-parentheses`/`--terms`系は `--vertical`/`--intermediate` 非対応**: `_init()` が明示的に拒否する(`command != 'ope'` の場合も同様)。`Page.layout` は常に `'inline'`。
- **`ope --missing-value` は `--vertical`/`--intermediate`/`--use-parentheses`/`--terms`系いずれとも併用不可**: `_init()` が明示的に拒否する(`command != 'ope'` の場合も同様)。`Page.layout` は常に `'inline'`。決定的フォールバックを持つ既存の `CALC_FUNCTIONS` をそのまま再利用しているため、`ope --use-parentheses`/`--terms`系と異なり `ValueError` のリスクはない(常に `a op b = c` が先に確定してから隠す位置を選ぶだけのため)。
- **Web層(`backend/renderers.py`、`frontend/spa/src/drillPresets.js`)は issue #73 で issue #71 の新オプションに対応済み**: `--terms`/`--terms-min`/`--terms-max`/`--mixed-operators` は `RendererRequest`/`build_command()` で変換され、学年4〜6の「中学受験」プリセット27件(`drillPresets.js` の `examPrep`)から利用される。詳細は [[backend/renderers.py]]/[[frontend/spa/src/drillPresets.js]] を参照。
- **`ope` の小数拡張(`--a-decimal-places`/`--b-decimal-places`)は横書き限定**: `--vertical`(筆算)と組み合わせるとエラーになる。`xlop`/`longdivision` は小数点そのものはマクロレベルでサポートしている(`decimalsepsymbol` オプション等)が、筆算描画の実機検証・調整は本 issue のスコープ外として意図的に見送っている(将来拡張の余地として残す)。
- **`mixed` コマンドも決定的フォールバックを持たない**: `generate_mixed_problems` は `ope --use-parentheses`/`--terms`系と同じ単純な再抽選(`MAX_OPERAND_RETRY_ATTEMPTS` 回)のみで解を探す。加算・乗算は必ず成功するが、減算(`mixed_stage_sub`)は最初の項が2項目以降より小さいと失敗しうる。Web プリセット(`drillPresets.js` の `g6-mixed-*`)は `operator: ['mix']`(除算・乗算に限らず全演算子が対象)で桁数を小さく保つ(`numerator_digits`/`denominator_digits` = 1、`decimal_places` = 1)ことでこのリスクを抑えている。
- **`mixed` コマンドの答えは常に厳密な分数、無限小数は一切出力しない**: `mixed` の除算は `fractions.Fraction` の厳密除算をそのまま使い、答えは常に `fraction_to_tex` で分数表示する(小数表記への変換は一切行わない)。`ope` の小数拡張も、`calc_div` の厳密割り切れ判定(`a % b == 0`)を再利用しているため、生成される小数の答えは常に有限小数になる。この2点はユーザー要件による明示的な設計上の不変条件。

## 変更履歴(git log より自動生成)

- b2c1d27 docs: sync documentation
- 550f35f docs(#186): note lualatex default and binary-missing test coverage in nuts_calc_tex.py.md
- 506d7b4 feat(#186): make latex+lualatex the default reachable configuration
- 231bde1 #134 frontend/web: add 出題形式 (式/筆算) setting to add/sub/mul/div preset detail pages (#181)
- 7b064ef #114 nuts_calc_tex.py: add reducibility control to frac/mixed multiplication and division (#165)
- bc0eef5 #113 nuts_calc_tex.py: allow --carry-borrow with decimal operands (#164)
- 1a32b29 #153 Add reusable result ceilings and grade-2 addition up to 1,000 (#158)
- d2e8744 #152 #155 Fix kuku multiplier range and descend order in both renderers (#156)
- e8db9d7 #112 nuts_calc_tex.py: add mixed-number (帯分数) display support to the frac command (#125)
- 380c2b1 #121 nuts_calc_tex.py: add Japanese-capable LuaLaTeX engine adapter (#124)
