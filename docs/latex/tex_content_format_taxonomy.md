# `nuts_calc_tex.py` コンテンツフォーマット・タキソノミー

## 目的・位置づけ

issue #122 の成果物。`docs/latex/tex_calculation_drill_layout_guidelines.md` が定義するデータ/表示の責務分離方針のもと、`backend/nuts_calc_tex.py` の全 `build_*_block_tex()` 関数(24個)を実際に読み、各コマンドの**問題本体のみ**の視覚パターンを再利用可能なパターン一覧として整理したもの。

- 対象は各 `build_*_block_tex()` が生成する TeX 文字列の構造そのもの(`Page.layout`の`'inline'|'tabular'|'block'`はページ内でのブロックの並べ方を表すレイヤー1の属性であり、本タキソノミーの対象外)
- 問題番号(`n)` 部分)の描画はレイヤー2(#184)に切り出される予定のため、本タキソノミーは番号を除いた本体構造のみを分類する
- 本issueではコード変更を行わない。実際に共有TeXマクロへ落とし込む作業(レイヤー3retrofit)は #185、内部API設計は #183 がこのタキソノミーを起点に進める

## 調査方法

`backend/nuts_calc_tex.py` の `^def build_.*_block_tex` にマッチする全24関数を特定し、各関数本体を読んで実際に返す文字列の構造(等号/矢印/比較記号の有無、ブランクの見た目、複数行かどうか)を比較した。issue本文にあった予備仮説(`Page.layout` 由来)はこの調査の起点としてのみ使い、実際の関数の挙動を正とした。

## パターン一覧

### 1a. 単純等式(整数・小数)

`n) $<式> = <結果>$` の1行の数式。ブランク時は末尾の結果だけが**無枠**の空白(`BLANK_ANSWER_TEX = '\\hspace{1.5em}'`)に置き換わる。高さは1行相当で、フォントサイズ・行間の面で最もシンプルな部品。

| 関数 | コマンド | 備考 |
|---|---|---|
| `build_horizontal_block_tex` | `ope`(横式、`add`/`sub`/`mul`/`div`/`mix`) | `div` で余りがある場合のみ `\cdots <余り>` を末尾に追加する修飾がつく(`nuts_calc_tex.py:1506-1529`) |
| `build_tree_ope_block_tex` | `ope --use-parentheses` | 左辺がN項の2分木構造から再帰生成される括弧付き式(`nuts_calc_tex.py:1952-1955`)。文字列の型は1aと同一 |
| `build_multi_term_ope_block_tex` | `ope`(多項、括弧なし) | 左辺がフラットなN項式(`nuts_calc_tex.py:2152-2158`) |
| `build_kuku_block_tex` | `99` | `reverse` フラグで `c = a × b` と左右が入れ替わる(`nuts_calc_tex.py:2559-2571`) |
| `build_squ_block_tex` | `squ` | `reverse` 対応は `99` と同じ(`nuts_calc_tex.py:2757-2769`) |
| `build_pi_block_tex` | `pi` | `reverse` 対応は `99`/`squ` と同じ(`nuts_calc_tex.py:2921-2933`) |
| `build_number_pair_block_tex` | `lcm`/`gcd` | `\mathrm{LABEL}(a, b) = c` という関数呼び出し風の左辺(`nuts_calc_tex.py:3928-3931`) |

### 1b. 分数を含む等式

1aと文字列の型(`式 = 結果`、末尾のみ無枠ブランク)は同じだが、式の一部または全体に `\frac` を含み `\displaystyle` を要する。`tex_calculation_drill_layout_guidelines.md` セクション17が指摘する通り、分子・分母のフォントサイズや行高さの専用調整が必要で、1aと同じ固定高さのボックスをそのまま流用できない。

| 関数 | コマンド | 備考 |
|---|---|---|
| `build_fraction_block_tex` | `frac` | 帯分数表示(`fraction_to_mixed_number_tex`)にも対応(`nuts_calc_tex.py:3432-3439`) |
| `build_mixed_block_tex` | `mixed` | オペランドは int/decimal/fraction 混在可能だが、結果は常に `fraction_to_tex` で厳密分数表示(`nuts_calc_tex.py:3834-3846`) |
| `build_divfrac_block_tex` | `divfrac` | 左辺は整数の割り算(`a \div b`)だが右辺が分数(`nuts_calc_tex.py:4445-4455`) |

### 2. 枠付き空所を埋め込む等式

1a/1bと異なり、ブランクが式の**途中のオペランド**にあり、`\fbox` による罫線付きボックス(issue #265 以降は共有マクロ `\boxedblank`、それ以前は定数 `BOXED_BLANK_TEX`)で表示される。答え(`c`)自体は常に表示される。

| 関数 | コマンド | 備考 |
|---|---|---|
| `build_com_block_tex` | `com` | `a + [枠] = target` の固定形(`nuts_calc_tex.py:2372-2375`) |
| `build_missing_value_block_tex` | `ope --missing-value` | `a`/`b` のどちらか一方だけが枠になり、演算子は `add`/`sub`/`mul`/`div` いずれも可(`nuts_calc_tex.py:2278-2283`) |

### 3. 比較(関係式)

`A [関係記号] B` の形。ブランクは関係記号そのものが枠(2と同じ `\boxedblank`、issue #266 以降)になる点が2と共通するが、等号ではなく `<`/`>` を扱う点、int/decimal/fraction の kind混在に対応する点が固有。

| 関数 | コマンド | 備考 |
|---|---|---|
| `build_fraction_comparison_block_tex` | `compare` | `comparison_operand_to_tex` が kind に応じて整数・小数・分数を出し分ける(`nuts_calc_tex.py:3643-3648`) |

### 4a. 単純矢印変換

`n) $A \Rightarrow B$` の形。ブランク時は1a同様、末尾(この場合はB側全体)が無枠ブランクになる。

| 関数 | コマンド | 備考 |
|---|---|---|
| `build_abc_block_tex` | `aBc` | `abcd \Rightarrow <答え>`(`nuts_calc_tex.py:2670-2673`) |
| `build_evenodd_block_tex` / `build_evenodd_slot_content_tex` | `evenodd` | `a \Rightarrow \mathrm{even/odd}`。slot版は番号なしで内部 presentation API が使用する(`nuts_calc_tex.py:3348-3373`) |
| `build_multiples_block_tex` / `build_multiples_slot_content_tex` | `multiples` | Bがコンマ区切りの可変長リスト。slot版は番号なし(`nuts_calc_tex.py:3447-3457`) |
| `build_divisors_block_tex` | `divisors` | Bがコンマ区切りの可変長リスト(`nuts_calc_tex.py:3180-3183`) |

### 4b. 分数を含む矢印変換

4aと文字列の型は同じだが、片側または両側に `\frac` を含む。1a→1bと同じ理由で専用の高さ調整が必要。

| 関数 | コマンド | 備考 |
|---|---|---|
| `build_simplify_block_tex` | `simplify` | 両辺とも分数(`nuts_calc_tex.py:4023-4026`) |
| `build_frac2dec_block_tex` | `frac2dec` | 左辺のみ分数、右辺は小数(`nuts_calc_tex.py:4268-4271`) |
| `build_dec2frac_block_tex` | `dec2frac` | 左辺は小数、右辺のみ分数(`nuts_calc_tex.py:4360-4363`) |

### 4c. 2要素ペア矢印変換

`A, B \Rightarrow A', B'` の形。4a/4bと矢印を使う点は共通だが、両辺がそれぞれ2つの分数のコンマ区切りリストである点が異なり、単項の4a/4bへ単純に一般化できない(要素数が構造として固定2)。

| 関数 | コマンド | 備考 |
|---|---|---|
| `build_commondenom_block_tex` | `commondenom` | 通分前後の分数ペアを表示(`nuts_calc_tex.py:4121-4134`) |

### 5. 段階的矢印チェーン

矢印を2段使う唯一のパターン。`a \times b \Rightarrow <暗算メモ> \Rightarrow c` という3項3段の構造は他のどの関数とも共有できない。

| 関数 | コマンド | 備考 |
|---|---|---|
| `build_horizontal_intermediate_block_tex` | `ope --intermediate` | 暗算メモの生成は `build_intermediate_memo`(`nuts_calc_tex.py:1532-1546`) |

### 6. 筆算(縦式)

唯一の複数行パターン。`xlop`(`add`/`sub`/`mul`)または `longdivision`(`div`)パッケージに実際のレイアウトを委譲しており、桁揃え・繰り上がり/繰り下がりの表示・下線などTeX側の専用機構に依存する。ブランク版は `xlop` のスタイルフック(`resultstyle`等)を `\phantom` に差し替える、または `longdivision` の `stage=0` を使うことで実現しており、他のどのパターンとも異なる「文字列を差し替える」のではなく「描画オプションを切り替える」ブランク化の仕組みを持つ。

| 関数 | コマンド | 備考 |
|---|---|---|
| `build_vertical_block_tex` | `ope --vertical` | `b_decimal_places > 0` の除算(除数が小数)は非対応(`nuts_calc_tex.py:1549-1593`) |

### 7. グリッド表

1問=1行の他パターンと異なり、ページの一部を占める `tabular` 全体を1ブロックとして返す。問題番号という概念自体がなく(11×11のマス目全体が1つの「問題」)、ヘッダ行・ヘッダ列に色付け(`\rowcolor`/`\columncolor`)が入る点も他と全く異なる。

| 関数 | コマンド | 備考 |
|---|---|---|
| `build_hundred_square_block_tex` | `100` | `HUNDRED_SQUARE_SIZE`×`HUNDRED_SQUARE_SIZE` の加算表(`nuts_calc_tex.py:2457-2480`) |

## コマンド → パターン対応表(まとめ)

| コマンド(オプション) | パターン |
|---|---|
| `ope`(横式) | 1a |
| `ope --intermediate` | 5 |
| `ope --vertical` | 6 |
| `ope --use-parentheses` | 1a |
| `ope`(多項、括弧なし) | 1a |
| `ope --missing-value` | 2 |
| `com` | 2 |
| `100` | 7 |
| `99` | 1a |
| `aBc` | 4a |
| `squ` | 1a |
| `pi` | 1a |
| `evenodd` | 4a |
| `multiples` | 4a |
| `divisors` | 4a |
| `lcm`/`gcd` | 1a |
| `frac` | 1b |
| `compare` | 3 |
| `mixed` | 1b |
| `simplify` | 4b |
| `commondenom` | 4c |
| `frac2dec` | 4b |
| `dec2frac` | 4b |
| `divfrac` | 1b |

24関数・24コマンド(バリエーション)全てが上記8パターンのいずれか1つに過不足なく対応する。

## issue本文の予備仮説との差分

issue #122 本文にあった予備仮説は「分数を含む式(frac/mixed/simplify/commondenom/frac2dec/dec2frac/divfrac)」を1つの独立パターンとして挙げていたが、実際に関数を読むと、分数の有無は等式(1a↔1b)・矢印変換(4a↔4b)のどちらの型にも横断的に現れる「背が高くなる・`\displaystyle`が要る」という属性であり、単独のパターンではなく既存パターンを縦に割る軸だとわかった。また、`com`/`missing-value` の枠付き空所と `compare` の枠付き関係記号は、末尾が無枠ブランクになる1a/1bとは見た目が明確に異なるため、独立のパターン(2, 3)として分離した。`commondenom` は矢印変換だが両辺が2要素リストという点で単項の4a/4bと構造が異なるため4cとして区別した。

## 今後の利用

- #183(表示レイヤーの内部API設計)は本タキソノミーのパターン単位でコンポーネント境界を検討する
- #185(レイヤー3retrofit)は本タキソノミーのパターンごとに子issueを分割する
- 番号領域(`n)`)の共通化は #184 が別途扱う(本タキソノミーは問題本体のみを対象とし、番号の描画方式には触れていない)

## retrofit 状況

- **パターン1a・1b(issue #264、#185 の子)**: 表内の全 `build_*_block_tex` / `build_*_slot_content_tex`(1a: `ope` 横式 plain/tree/multi-term、`99`、`squ`、`pi`、`lcm`/`gcd`。1b: `frac`、`mixed`、`divfrac`)が、生の f-string ではなく共有 TeX マクロ経由で出力するようになった。`backend/nuts_calc_tex.py` の `build_content_format_macros_tex()` が `\newlength{\opspacewidth}`(定数 `CONTENT_FORMAT_OPSPACE_WIDTH_TEX`)・`\opspace`(guidelines 項目5/6/20)・`\horizontaleq`(1a wrapper)・`\fractioneq`(1b wrapper: `\displaystyle` + `\vphantom` 高さ strut、guidelines 項目17)を emit し、`build_document_tex`(レガシー CLI)と `build_presentation_document_tex`(内部 API)の両方が preamble 直後にこのブロックを差し込む。各 `build_*_block_tex` は `n) ` prefix + 対応する番号なし slot formatter の合成へ統一された。`divfrac` の problem 本文は本 retrofit で `\displaystyle` を得た(従来は答えキーのみ)。パターン2以降・Layer 1/2 の契約は対象外。
- **パターン2(issue #265、#185 の子)**: `build_com_block_tex` / `build_com_slot_content_tex`(`com`)と `build_missing_value_block_tex` / `build_missing_value_slot_content_tex`(`ope --missing-value`)が、`BOXED_BLANK_TEX` を直接埋め込む生の f-string ではなく共有 TeX マクロ経由で出力するようになった。`build_content_format_macros_tex()` に `\newlength{\boxedblankwidth}`(定数 `CONTENT_FORMAT_BOXED_BLANK_WIDTH_TEX = '1em'`、guidelines 項目6。隠したオペランドの桁数に応じてサイズを変えない**意図的な固定幅**)・`\boxedblank`(`\vcenter` をやめた baseline-anchored な `\fbox` + strut、guidelines 項目20)・`\boxedblankeq`(`$...$` wrapper + `\vphantom{\boxedblank}` で blank/filled 行の高さを一致、guidelines 項目17 相当)を追記した(#264 の `\opspace`/`\horizontaleq`/`\fractioneq` 定義は無変更)。演算子・`=` の間隔は #264 の `build_equation_lhs_tex` + `\opspace` を再利用する(パターン1a と同じ、項目5/20)。各 `build_*_block_tex` は `n) ` prefix + 対応する番号なし slot formatter の合成へ統一。Python 側はオペランドマーカー用に新定数 `BOXED_BLANK_OPERAND_TEX`(= `\boxedblank`)を使う。
- **パターン3(issue #266、#185 の子)**: `build_fraction_comparison_block_tex` / `build_fraction_comparison_slot_content_tex`(`compare`)が、生の `$\displaystyle ...$` f-string ではなく共有 `build_comparison_equation_tex`(`\compareeq{<a> \opspace <rel> \opspace <b>}`)経由で出力するようになった。`build_content_format_macros_tex()` に `\compareeq`(`\fractioneq` と同一形の `$\displaystyle #1\vphantom{\frac{0}{0}}$`、別名定義で縦位置処理を独立させる)を追記(#264/#265 の定義行は無変更)。ブランクの関係記号は #265 の `\boxedblank` を再利用し(`COMPARE_REL_BLANK_TEX` = `BOXED_BLANK_OPERAND_TEX`)、`\boxedblankwidth` を共有する。関係記号の両側に #264 の `\opspace`(項目5/20)、int/decimal オペランドは `\vcenter{\hbox{$...$}}` で `\frac` と数式軸中央を揃える(項目17)。小数点揃え(項目16)は単一行インライン比較には縦の小数カラムが無いため N/A。パターン3が最後の利用者だった生の `\vcenter` 定数 `BOXED_BLANK_TEX` は本 issue で削除された。
- パターン4以降(`build_abc_block_tex`・`build_simplify_block_tex`・`build_commondenom_block_tex`・`build_horizontal_intermediate_block_tex`・`build_vertical_block_tex`・`build_hundred_square_block_tex` ほか)は未 retrofit。
