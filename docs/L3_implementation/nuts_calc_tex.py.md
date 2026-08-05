# `nuts_calc_tex.py`

## 目的・役割

`nuts_calc.py`(ReportLab ベース)とは**完全に独立した**、LaTeX(TeX)でレンダリングする計算ドリル PDF 生成 CLI のプロトタイプ。issue #19(親トラッキング issue)で計画されている全7コマンド再実装のうち、Phase 1(issue #20)で CLI 引数・ページ/PDF レイアウト・TeX ビルドパイプライン・CSV 出力という共通基盤を実装し、Phase 2(issue #21)で `ope` コマンド(四則演算 add/sub/mul/div/mix、横書き・`--vertical`・`--intermediate`)、Phase 3(issue #22)で `com` コマンド(補数: `a + __ = target`)、Phase 4(issue #23)で `100` コマンド(100マス計算: 11×11 の加算表)、Phase 5(issue #24)で `99` コマンド(九九: 固定の1段 × `--rows`×`--columns` 問、`--descend`/`--reverse`/`--shuffle` の並び替え)、Phase 6(issue #25)で `aBc` コマンド(暗算: 4桁の数字列 `abcd` を2桁ずつのペア `ab`/`cd` に分けて変換する暗算ステートメント)、Phase 7(issue #26)で `squ` コマンド(二乗数: `-a` から始まる整数列を `a × a` の形で出題、`--descend`/`--reverse`/`--shuffle` の並び替えは `99` と共通)、Phase 8(issue #27)で `pi` コマンド(円周率倍: `-a` から始まる整数列を `a × 3.14` の形で出題、並び替えオプションは `squ` と共通)を実装した。これで issue #19 が計画する全7コマンドの実装が完了している。

`nuts_calc.py` とは import 等のコード共有を一切行わない(`nuts_calc.py` 側も変更しない)。将来的に両者を同じ CLI 契約で切り替えられるラッパーを作る前提のため、引数体系は `nuts_calc.py` の `_init()` に似せているが、実装は完全に別物。問題生成ロジック(`calc_add`/`calc_sub`/`calc_mul`/`calc_div`/`generate_ope_problems`)も `nuts_calc.py` の `get_operation_data` 等とは独立に再実装している(意味論は似せているが、コードは共有しない)。

## 動作の概要

### 共通基盤(Phase 1)

- `_init()`(`nuts_calc_tex.py:74-250`): `nuts_calc.py` と同じ引数(`paper_size`/`command`/`-a`/`-b`/`--a-min`/`--a-max`/`--b-min`/`--b-max`/`-o`/`--rows`/`--columns`/`--page`/`--merge`/`--csv`/`--out-file`/`--with-bottom-answer`/`--vertical`/`--intermediate`/`--debug` 等)を独立に定義・パースする。`-r`/`-c`/`-p` は1以上を要求する。`command == '100'` の場合、`-a`/`-b`(桁数)が指定されていれば1〜3の範囲であることを、`-a`/`-b` の桁数レンジ変換(`set_min_max_value`)より**前**に検証する(範囲外だと `set_min_max_value` 内で `IndexError` になる、または負のインデックスで誤ったレンジになるため。詳細は後述)。`-a`/`-b` の桁数レンジ変換自体は `command in ('ope', '100')` の場合のみ行う。`command == 'com'` の場合は `-a/--a-value`(補数ターゲット)が必須かつ2以上であることを検証する。`command == '99'` の場合は `-a/--a-value`(九九の段)が必須であることを検証する(値域は `nuts_calc.py` と同じく未検証)。`command == 'squ'` の場合は `-a/--a-value`(開始する二乗数の起点)が必須であることを検証する(`99` と同じ形、値域は同じく未検証)。`command == 'pi'` の場合は `-a/--a-value`(円周率倍する整数列の起点)が必須であることを検証する(`squ` と全く同じ形)。`command == 'aBc'` の場合は `-a`/`-b` を一切使用しない(`com`/`99`/`squ`/`pi` と異なり検証も不要)。`command == 'ope'` の場合のみ `--intermediate` のバリデーションを行う(後述)。
- `Page` データクラス(`blocks: list[str]`, `columns: int`, `bottom_answer_tex: str | None`, `layout: str`): 1ページ分の LaTeX コンテンツを表す最小単位。`layout='inline'`(横書き・プレースホルダー用、`\hspace` でブロックをテキスト行として結合)と `layout='tabular'`(`--vertical` 用、後述)の2種類。
- `build_preamble_tex`/`build_page_header_tex`/`build_page_tex`/`build_document_tex`: LaTeX ソースを文字列として組み立てる。用紙サイズは `geometry` パッケージのオプション(`a3paper`/`a4paper`/`b5paper`/`a4paper,landscape`)にマッピングし、ヘッダー(タイトル・日付欄)・フッター(ページ番号・著作権、`fancyhdr`)・行×列グリッドを構築する。プリアンブルは `longdivision`/`xlop`/`array`/`fancyhdr`/`xcolor`(`table` オプション、`100` コマンドのヘッダー網掛けに使用)を読み込む。
- `compile_tex`: `pdflatex -interaction=nonstopmode -halt-on-error` を一時ディレクトリで subprocess 実行し、生成された PDF を指定パスへコピーする。失敗時は `pdflatex` の出力末尾を含めて `exit(1)` する。
- 出力ファイル名の導出は `nuts_calc.py`(issue #15 修正後)と同様に `os.path.splitext(ini.out_file)` を使う(`_read.pdf`/`.csv` の付与)。
- `main(ini)`(`nuts_calc_tex.py:1157-`): `ini.command == 'ope'` なら `build_ope_pages`、`'com'` なら `build_com_pages`、`'100'` なら `build_hundred_square_pages`、`'99'` なら `build_kuku_pages`、`'aBc'` なら `build_abc_pages`、`'squ'` なら `build_squ_pages`、それ以外(`'pi'`、7コマンドの choices のうち上記6分岐に該当しない残り)なら `build_pi_pages` で実データを生成し、`--merge` の有無に応じて blank/filled/merge の3モードでドキュメントをビルドする。`--csv` 指定時は、`ope`/`com`/`100`/`99`/`aBc`/`squ`/`pi` それぞれの実問題データを CSV に書き出す(7コマンド全てが実データを持つため、プレースホルダー用の CSV フォールバックは Phase 8 で削除済み)。

### `ope` コマンド(Phase 2)

- `OpeProblem` データクラス(`index`/`a`/`b`/`operator`/`c`)が1問を表す。
- `calc_add`/`calc_mul` は単純計算。`calc_sub`/`calc_div` は `nuts_calc.py` の同名関数と同じ意味論(結果が正になるまで/割り切れるまで、最大 `MAX_OPERAND_RETRY_ATTEMPTS`(1000)回オペランドを再抽選)をベースに独立に再実装しているが、`nuts_calc.py` 側にはない決定的フォールバックを追加している: `nums_a`×`nums_b` のうち条件を満たすペアが極めて少ない場合(例: `nums_a=1..1000`, `nums_b=[999,1000]` では正の結果になる組が `(1000, 999)` の1組のみ)、純粋な乱択再抽選だけでは1000回の試行内に解を引けない確率が無視できないため、再抽選が尽きた後に `calc_sub` は `(max(nums_a), min(nums_b))`、`calc_div` は `find_exact_division_pair`(各 `nums_b` の倍数を `nums_a` の範囲内だけ探索する決定的探索)にフォールバックし、解が存在する限り必ず成功するようにしている(codex レビュー指摘、PR #29 で対応)。
- `generate_ope_problems`(`nuts_calc_tex.py:433-451`): `operators` に `'mix'` が含まれる場合は `add`/`sub`/`mul`/`div` の4種から**問題ごとに**ランダムな演算子を選ぶ(`nuts_calc.py` の `mix` 展開と同じ意味論)。
- 横書き: `build_horizontal_block_tex` が `n) $a op b = c$` を生成する。blank 版は `c` の代わりに、下線を伴わない固定幅の `\hspace{1.5em}` を出力する。`--intermediate` 指定時は `build_horizontal_intermediate_block_tex` が代わりに使われ、`build_intermediate_memo`(`memo.md` STEP 1 の2桁×1桁暗算メモ技法: `a` の十の位×`b` と一の位×`b` をそれぞれ2桁ゼロ埋めして連結)を挟んだ `n) $a \times b \Rightarrow memo \Rightarrow c$` を出力する。同じ固定幅の空欄を使うため、通常・途中式とも解答欄のレイアウトを維持する。
- `--vertical`(筆算): `build_vertical_block_tex`(`nuts_calc_tex.py:478-505`)が問題の `operator` に応じて分岐する。
  - `add`/`sub`/`mul`: `xlop` の `\opadd`/`\opsub`/`\opmul` を使用(多桁の乗数は自動で部分積の複数段表示になる)。blank 版は `\opset{resultstyle=\phantom,carrystyle=\phantom,intermediarystyle=\phantom}` を `\begingroup`/`\endgroup` で局所適用し、結果・繰り上がり・部分積の**数字だけ**を不可視化する(レイアウトの高さ・幅は保持されるため、罫線位置は blank/filled で一致する)。
  - `div`: `longdivision` の `\intlongdivision` を使用。blank 版は `stage=0` オプションで除数・被除数の枠のみを表示する。
  - `mix` の場合、各問題は生成時点で具体的な演算子(add/sub/mul/div のいずれか)に確定しているため、`build_vertical_block_tex` は追加の分岐なしに機能する。
- `build_ope_page_pair`(`nuts_calc_tex.py:508-528`): `vertical`/`intermediate` フラグに応じて上記のブロックビルダーと `Page.layout`(`vertical` なら `'tabular'`、それ以外は `'inline'`)を選び、同一の問題リストから blank/filled の `Page` ペアを作る(blank/filled は同じ問題を使い、表示のみが異なる)。
- `build_ope_pages`(`nuts_calc_tex.py:557-578`): `ini.a_min`〜`ini.b_max` から候補集合を作り、ページごとに `rows*columns` 問を生成してページペアを積み上げる。`--with-bottom-answer` 指定時は `build_ope_bottom_answer_tex` で `(index) c` の一覧を blank ページ末尾に追加する。
- `build_ope_csv_rows`(`nuts_calc_tex.py:535-540`): 1問1行、`[page_number, index, a, operator, b, c]` の列で CSV を書き出す(ヘッダー行なし、Phase 1 と同じ方針)。

### `com` コマンド(Phase 3)

- `ComProblem` データクラス(`index`/`a`/`target`/`c`、`nuts_calc_tex.py:598-604`)が1問を表す。`a + c = target` が常に成り立つ。
- `generate_com_problems`(`nuts_calc_tex.py:607-618`): `1..target-1` の範囲から `a` を `random.choice` で選び、`c = target - a` を計算する。`nuts_calc.py` の `get_complement_data` と意味論は同じだが独立に再実装している(コード共有なし)。`a` は範囲の閉区間からの毎回の乱択で選ぶため、`nuts_calc.py` 側にあった「事前に `random.sample` でシャッフルしてから `random.choice` する」という冗長な前処理は行わない。
- `build_com_block_tex`(`nuts_calc_tex.py:659-662`): `n) $a + \hspace{1.5em} = target$`(blank、`ope` と共通の下線なし固定幅プレースホルダー)/`n) $a + c = target$`(filled)を生成する。blank でも `target` はそのまま表示し、隠すのは答え `c` のみ(issue #22 の "a + __ = target" 形式の通り)。
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
- `generate_kuku_problems`(乗数 `b` の生成): `order = ini.rows * ini.columns` 問を1ページ分生成する。乗数 `b` は基本 `1..order` の連番で、`--descend` で `order..1` の降順に反転し、`--shuffle` で(`--descend` 反転後の並びを)`random.shuffle` する。`order` が9を超えると `b` も9を超える値になる(`nuts_calc.py` の `get_fixed_format_data`(`mode == '99'`、`nuts_calc.py:508-522`)が `order = rows` を乗数の生成範囲に直結させている挙動を踏襲し、9問固定にはしていない)。`nuts_calc.py` と同じくコード共有はせず独立に再実装している。
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

## 重要な設計判断とその理由

### `aBc` の4桁表示を常にゼロ埋めする理由(`nuts_calc.py` との差異)

`nuts_calc.py` の `get_aBc_data` は `abcd` を整数として結合してから `len(str(abcd)) == 3` の場合だけゼロ埋めする(`nuts_calc.py:577-578`)という部分的な対応で、2桁以下になるケース(例: `a=0, b=0, c=0, d=5` → `"5"`)はゼロ埋めされないまま表示される潜在的な不整合がある。`nuts_calc_tex.py` はこれを踏襲せず、`AbcProblem.abcd_display` が常に `f"{a}{b}{c}{d}"` で4桁全てを個別に文字列化するため、先頭が0の場合も含めて常に4桁で表示される。

### `99` の問題数を `--rows`×`--columns` に連動させ、9問固定にしなかった理由

issue #24 の Scope には "single times-table row" とあるが、実装着手時に `nuts_calc.py` の元実装(`order = rows`、乗数がページの行数に連動し9で頭打ちにならない)を確認した上でユーザーと相談し、「1ページ9問固定」ではなく `ope`/`com` と同じ `order = rows * columns` によるタイル化を採用することを明示的に決定した(9問固定案は却下)。`-a/--a-value`(段)の値域も、`nuts_calc.py` に合わせて1〜9への制限を行わないことをあわせて確認済み(`100` コマンドの桁数バリデーションとは異なる判断)。

### `100` の `-a`/`-b` 桁数変換を `nuts_calc.py` の挙動から意図的に修正した理由

`nuts_calc.py` の元実装は、`100` コマンドで `-a`/`-b` が**省略された場合のみ** `set_min_max_value` で桁数1のレンジに変換し、明示的に `-a 2` 等を指定した場合は `a_value` が保存されるだけでレンジには反映されない(桁数3超のガードのみ効く)、という一貫性のないバグが `nuts_calc.py:245-255` に存在する。`nuts_calc_tex.py` ではこれを再現せず、`_init()` の桁数レンジ変換を `command in ('ope', '100')` の場合に常に適用するよう統一した(`-a`/`-b` が `None` でなければ常に変換)。Phase 3(`com`)で `nuts_calc.py` 側の冗長な前処理を踏襲しなかったのと同じ方針。

なお、この桁数レンジ変換を先に実装した際、`100` の桁数バリデーション(1〜3の範囲チェック)を変換の**後**に置いてしまい、`-a 6` 以上で `set_min_max_value` 内の `digits_list[value - 1]` が `IndexError` を送出する(`digits_list` は5要素)、`-a 0` 以下で負のインデックスにより誤った(意図しない5桁の)レンジが黙って採用される、という2つの実バグが生じていた(PR #31 の codex レビューで指摘、修正済み)。現在は `_init()` 内でこのバリデーションを `set_min_max_value` 呼び出しより前に移動している。

### `-a`/`-b` の桁数レンジ変換を `ope` 限定にゲートしている理由

`_init()` は元々、`command` に関わらず `-a/--a-value` が指定されると `set_min_max_value()`(`value` を「桁数」とみなし `digits_list[value - 1]` で範囲を引く、`digits_list` は5要素)で `a_min`/`a_max` に変換していた。`com` は `nuts_calc.py` の意味論を踏襲して `-a` を「桁数」ではなく「補数のターゲット値そのもの」として使うため、`-a 100` のような(5を超える)値を渡すと `digits_list[99]` で無条件 `IndexError` になる潜在バグがあった(issue #22 の実装着手時に発見)。`com` を実装するにあたり、この変換を `command == 'ope'` の場合のみ行うようゲートし、`com` の `a_value` は生の整数のまま `generate_com_problems` に渡るようにした。

### `--vertical` のグリッドレイアウトを行ごとに独立した `tabular` に分割している理由

`--vertical` ブロック(xlop/longdivision の出力)は複数行にまたがる LaTeX コンテンツのため、横書きプレースホルダーで使っている `\hspace` によるテキスト結合(`build_inline_grid_tex`)では列が揃わない。当初は1ページ分の全ブロックを1つの `tabular` にまとめていたが、**LaTeX の `tabular` はページをまたいで自動改ページしない**ため、既定の `-r 10` のような行数の多いグリッドでは、その `tabular` 全体がページに収まらず丸ごと次ページへ送られ、結果として1ページ目が空白になり2ページ目の下端から内容が溢れて実質的に問題が失われる不具合が実機コンパイルで確認された。この問題を避けるため、`build_tabular_grid_tex`(`nuts_calc_tex.py:284-314`)は**行ごとに独立した1行だけの `tabular`** を生成し、既存の `\par\vspace` 区切り(`build_inline_grid_tex` と同じ)で連結する設計にしている。これにより通常の段落と同様に行単位で自然に改ページできる。回帰テスト: `tests/test_nuts_calc_tex.py::test_cli_ope_vertical_default_rows_does_not_drop_content`。

列幅は `\dimexpr(\textwidth-2N\tabcolsep)/N\relax`(`N`=列数)で動的に計算しており、用紙サイズ(A3/A4/B5/A4横)や列数が変わっても `\textwidth` に追従する。

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

`nuts_calc.py` は `--vertical` で `div`/`mix` を拒否するが、`nuts_calc_tex.py` はこの制約を意図的に踏襲しない(親 issue #19 の指示、および上記の通り xlop/longdivision の組み合わせで div/mix も自然に筆算表示できることを確認済み)。

## 統合ポイント

- 呼び出し元: CLI 直接実行(`python3 nuts_calc_tex.py <paper_size> <command> ...`)のみ。`nuts_calc.py`/`web/backend/app.py`/`factory.sh` からは呼ばれない(まだ配線されていない)。
- 呼び出し先: `pdflatex`(要 LaTeX ディストリビューション、`texlive-latex-base` + `texlive-latex-extra`)。

## 注意事項・既知の制限

- **issue #19 が計画する7コマンド全てが実装済み**: `ope`/`com`/`100`/`99`/`aBc`/`squ`/`pi` は全て実データを生成する。Phase 1 時点のプレースホルダーコンテンツ・関数(`build_placeholder_page`/`build_placeholder_pages`)は Phase 8(issue #27)で削除済み。
- **`100` は `--a-min`/`--a-max` を極端に狭めると `ValueError` になりうる**: `sample_hundred_square_values` は候補範囲を2倍に複製してから10個抽出するため、範囲の要素数が5未満(例: `--a-min 5 --a-max 5`)だと母集団不足で `random.sample` が例外を送出する。`nuts_calc.py` 側の元実装にも同型の潜在バグがあり、本 Phase のスコープ外として未対応。
- **`pdflatex` が必須**: `shutil.which('pdflatex')` が `None` の場合は明確なエラーメッセージで `exit(1)` する。CI やローカル環境に LaTeX が無い場合、`tests/test_nuts_calc_tex.py` は `pytest.mark.skipif` で自動的にスキップされる(`tests/test_nuts_calc_tex_ope_generation.py`/`tests/test_nuts_calc_tex_com_generation.py`/`tests/test_nuts_calc_tex_kuku_generation.py`/`tests/test_nuts_calc_tex_squ_generation.py`/`tests/test_nuts_calc_tex_pi_generation.py` の純 Python ユニットテストは pdflatex なしでも実行される)。
- **`--descend`/`--reverse`/`--shuffle` は `ope`/`com`/`100` でも引数として受理されるが未使用**: `99`/`squ`/`pi` コマンドでのみ意味を持つ。`--debug` はどのコマンドでも未使用のまま。
- **`com`/`99`/`aBc`/`squ`/`pi` は `--vertical`/`--intermediate` 未対応、ただし挙動が異なる**: `--vertical` は指定しても静かに無視され(`build_com_pages`/`build_kuku_pages`/`build_abc_pages`/`build_squ_pages`/`build_pi_pages` は `Page.layout` を常に `'inline'` にする)、`com` は常に横書き(`n) $a + __ = target$`)、`99` は常に横書き(`n) $a \times b = c$`、`--reverse` 指定時は式の左右が入れ替わる)、`aBc` は常に横書き(`n) $abcd \Rightarrow answer$`)、`squ`/`pi` は常に横書き(それぞれ `n) $a \times a = c$`/`n) $a \times 3.14 = c$`、`--reverse` 指定時は式の左右が入れ替わる)で出力される。一方 `--intermediate` は無視されず、`_init()`(`nuts_calc_tex.py:247-249`)が `command != 'ope'` を検知した時点で `"--intermediate is only supported for the 'ope' command."` として `exit(1)` する(`com`/`99`/`aBc`/`squ`/`pi` いずれでも同様、`--vertical` の有無に関わらない)。それぞれ issue #22/#24/#25/#26/#27 のスコープ外。
- **`99` の乗数(b)・`squ`/`pi` の数列(a)は9で頭打ちにならない**: `order = ini.rows * ini.columns` が9を超えると `99` の乗数、`squ`/`pi` の数列いずれもそれに応じて9を超える(`nuts_calc.py` の元実装を踏襲した意図的な設計、詳細は上記の設計判断を参照)。
- **`--vertical` 指定時の CSV/bottom-answer の桁**: 特別な整形はしておらず、`build_ope_csv_rows`/`build_ope_bottom_answer_tex` は横書き・縦書きで共通(問題データそのものは表示形式に関わらず同一)。
- **`pi` の答え `c` は丸め済み**: `generate_pi_problems` が `round(a * PI_MULTIPLIER, 2)` を返すため、`build_pi_csv_rows`/`build_pi_bottom_answer_tex`/`build_pi_block_tex` はいずれも丸め後の値のみを扱う(`nuts_calc.py` の生の浮動小数点値との差異、詳細は上記の設計判断を参照)。

## 変更履歴(git log より自動生成)

- 93877f0 feat(#27): add nuts_calc_tex.py Phase 8 pi command (multiplication by pi)
- fa73c50 feat(#26): add nuts_calc_tex.py Phase 7 squ command (square numbers)
- be25ae8 feat(#25): add nuts_calc_tex.py Phase 6 aBc command (mental arithmetic statements)
- 1e14347 feat(#24): add nuts_calc_tex.py Phase 5 99 command (times-table / kuku)
- 51dcb6a fix(#23): validate 100 command digit count before range conversion
- 7393885 feat(#23): add nuts_calc_tex.py Phase 4 100 command (addition table)
- d45bc98 feat(#22): add nuts_calc_tex.py Phase 3 com command (complements)
- 82c0b6f fix(#21): guarantee calc_sub/calc_div succeed whenever a valid pair exists
- 44a3c18 feat(#21): add nuts_calc_tex.py Phase 2 ope command (horizontal/vertical/mix/intermediate)
- acb1e84 feat(#20): add nuts_calc_tex.py Phase 1 (LaTeX CLI/PDF foundation)
