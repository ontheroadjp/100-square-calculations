# `nuts_calc_tex.py`

## 目的・役割

`nuts_calc.py`(ReportLab ベース)とは**完全に独立した**、LaTeX(TeX)でレンダリングする計算ドリル PDF 生成 CLI のプロトタイプ。issue #19(親トラッキング issue)で計画されている全7コマンド再実装のうち、Phase 1(issue #20)で CLI 引数・ページ/PDF レイアウト・TeX ビルドパイプライン・CSV 出力という共通基盤を実装し、Phase 2(issue #21)で `ope` コマンド(四則演算 add/sub/mul/div/mix、横書き・`--vertical`・`--intermediate`)、Phase 3(issue #22)で `com` コマンド(補数: `a + __ = target`)を実装した。`ope`/`com` 以外の5コマンド(`100`/`99`/`aBc`/`squ`/`pi`)は引数として受理されるものの、依然として Phase 1 時点のプレースホルダーコンテンツを出力する(issues #23-#27 で順次実装予定)。

`nuts_calc.py` とは import 等のコード共有を一切行わない(`nuts_calc.py` 側も変更しない)。将来的に両者を同じ CLI 契約で切り替えられるラッパーを作る前提のため、引数体系は `nuts_calc.py` の `_init()` に似せているが、実装は完全に別物。問題生成ロジック(`calc_add`/`calc_sub`/`calc_mul`/`calc_div`/`generate_ope_problems`)も `nuts_calc.py` の `get_operation_data` 等とは独立に再実装している(意味論は似せているが、コードは共有しない)。

## 動作の概要

### 共通基盤(Phase 1)

- `_init()`(`nuts_calc_tex.py:67-226`): `nuts_calc.py` と同じ引数(`paper_size`/`command`/`-a`/`-b`/`--a-min`/`--a-max`/`--b-min`/`--b-max`/`-o`/`--rows`/`--columns`/`--page`/`--merge`/`--csv`/`--out-file`/`--with-bottom-answer`/`--vertical`/`--intermediate`/`--debug` 等)を独立に定義・パースする。`-r`/`-c`/`-p` は1以上を要求する。`-a`/`-b` の桁数レンジ変換(`set_min_max_value`)は `command == 'ope'` の場合のみ行う(後述)。`command == 'com'` の場合は `-a/--a-value`(補数ターゲット)が必須かつ2以上であることを検証する。`command == 'ope'` の場合のみ `--intermediate` のバリデーションを行う(後述)。
- `Page` データクラス(`blocks: list[str]`, `columns: int`, `bottom_answer_tex: str | None`, `layout: str`): 1ページ分の LaTeX コンテンツを表す最小単位。`layout='inline'`(横書き・プレースホルダー用、`\hspace` でブロックをテキスト行として結合)と `layout='tabular'`(`--vertical` 用、後述)の2種類。
- `build_preamble_tex`/`build_page_header_tex`/`build_page_tex`/`build_document_tex`: LaTeX ソースを文字列として組み立てる。用紙サイズは `geometry` パッケージのオプション(`a3paper`/`a4paper`/`b5paper`/`a4paper,landscape`)にマッピングし、ヘッダー(タイトル・日付欄)・フッター(ページ番号・著作権、`fancyhdr`)・行×列グリッドを構築する。プリアンブルは `longdivision`/`xlop`/`array`/`fancyhdr` を読み込む。
- `compile_tex`: `pdflatex -interaction=nonstopmode -halt-on-error` を一時ディレクトリで subprocess 実行し、生成された PDF を指定パスへコピーする。失敗時は `pdflatex` の出力末尾を含めて `exit(1)` する。
- 出力ファイル名の導出は `nuts_calc.py`(issue #15 修正後)と同様に `os.path.splitext(ini.out_file)` を使う(`_read.pdf`/`.csv` の付与)。
- `main(ini)`(`nuts_calc_tex.py:733-769`): `ini.command == 'ope'` なら `build_ope_pages`、`'com'` なら `build_com_pages` で実データを、それ以外なら `build_placeholder_pages` で仮コンテンツを生成し、`--merge` の有無に応じて blank/filled/merge の3モードでドキュメントをビルドする。`--csv` 指定時は、`ope`/`com` ならそれぞれの実問題データ、それ以外はプレースホルダー相当の行を CSV に書き出す。

### `ope` コマンド(Phase 2)

- `OpeProblem` データクラス(`index`/`a`/`b`/`operator`/`c`)が1問を表す。
- `calc_add`/`calc_mul` は単純計算。`calc_sub`/`calc_div` は `nuts_calc.py` の同名関数と同じ意味論(結果が正になるまで/割り切れるまで、最大 `MAX_OPERAND_RETRY_ATTEMPTS`(1000)回オペランドを再抽選)をベースに独立に再実装しているが、`nuts_calc.py` 側にはない決定的フォールバックを追加している: `nums_a`×`nums_b` のうち条件を満たすペアが極めて少ない場合(例: `nums_a=1..1000`, `nums_b=[999,1000]` では正の結果になる組が `(1000, 999)` の1組のみ)、純粋な乱択再抽選だけでは1000回の試行内に解を引けない確率が無視できないため、再抽選が尽きた後に `calc_sub` は `(max(nums_a), min(nums_b))`、`calc_div` は `find_exact_division_pair`(各 `nums_b` の倍数を `nums_a` の範囲内だけ探索する決定的探索)にフォールバックし、解が存在する限り必ず成功するようにしている(codex レビュー指摘、PR #29 で対応)。
- `generate_ope_problems`(`nuts_calc_tex.py:433-451`): `operators` に `'mix'` が含まれる場合は `add`/`sub`/`mul`/`div` の4種から**問題ごとに**ランダムな演算子を選ぶ(`nuts_calc.py` の `mix` 展開と同じ意味論)。
- 横書き: `build_horizontal_block_tex` が `n) $a op b = c$`(blank 版は `c` の代わりに `\underline{\hspace{1.5em}}`)を生成。`--intermediate` 指定時は `build_horizontal_intermediate_block_tex` が代わりに使われ、`build_intermediate_memo`(`memo.md` STEP 1 の2桁×1桁暗算メモ技法: `a` の十の位×`b` と一の位×`b` をそれぞれ2桁ゼロ埋めして連結)を挟んだ `n) $a \times b \Rightarrow memo \Rightarrow c$` を出力する。
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
- `build_com_block_tex`(`nuts_calc_tex.py:622-625`): `n) $a + \underline{\hspace{1.5em}} = target$`(blank、`ope` の横書きブロックと同じ下線プレースホルダーを流用)/`n) $a + c = target$`(filled)を生成する。blank でも `target` はそのまま表示し、隠すのは答え `c` のみ(issue #22 の "a + __ = target" 形式の通り)。
- `build_com_page_pair`/`build_com_pages`(`nuts_calc_tex.py:629-673`): `ope` の同名関数群と同じ構造。`--vertical`(筆算)には未対応(issue #22 のスコープ外、`Page.layout` は常に `'inline'`)。`--with-bottom-answer` 指定時は `build_com_bottom_answer_tex` で `(index) c` の一覧を blank ページ末尾に追加する。
- `build_com_csv_rows`(`nuts_calc_tex.py:645-650`): 1問1行、`[page_number, index, a, target, c]` の列で CSV を書き出す。

## 重要な設計判断とその理由

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

### `nuts_calc.py` の `VERTICAL_UNSUPPORTED_OPERATORS` を踏襲しない

`nuts_calc.py` は `--vertical` で `div`/`mix` を拒否するが、`nuts_calc_tex.py` はこの制約を意図的に踏襲しない(親 issue #19 の指示、および上記の通り xlop/longdivision の組み合わせで div/mix も自然に筆算表示できることを確認済み)。

## 統合ポイント

- 呼び出し元: CLI 直接実行(`python3 nuts_calc_tex.py <paper_size> <command> ...`)のみ。`nuts_calc.py`/`web/backend/app.py`/`factory.sh` からは呼ばれない(まだ配線されていない)。
- 呼び出し先: `pdflatex`(要 LaTeX ディストリビューション、`texlive-latex-base` + `texlive-latex-extra`)。

## 注意事項・既知の制限

- **`ope`/`com` 以外の5コマンドは未実装**: `100`/`99`/`aBc`/`squ`/`pi` は Phase 1 時点のプレースホルダーコンテンツ(`n) ___` / `n) ___ = n`)のままで、issues #23-#27 で順次実装される。
- **`pdflatex` が必須**: `shutil.which('pdflatex')` が `None` の場合は明確なエラーメッセージで `exit(1)` する。CI やローカル環境に LaTeX が無い場合、`tests/test_nuts_calc_tex.py` は `pytest.mark.skipif` で自動的にスキップされる(`tests/test_nuts_calc_tex_ope_generation.py`/`tests/test_nuts_calc_tex_com_generation.py` の純 Python ユニットテストは pdflatex なしでも実行される)。
- **`--descend`/`--reverse`/`--shuffle`/`--debug` は `ope`/`com` でも引数として受理されるが未使用**: これらは `99` 等の将来実装で使われる予定。
- **`com` は `--vertical`/`--intermediate` 未対応**: 指定しても無視され、常に横書き(`n) $a + __ = target$`)で出力される(issue #22 のスコープ外)。
- **`--vertical` 指定時の CSV/bottom-answer の桁**: 特別な整形はしておらず、`build_ope_csv_rows`/`build_ope_bottom_answer_tex` は横書き・縦書きで共通(問題データそのものは表示形式に関わらず同一)。

## 変更履歴(git log より自動生成)

- d45bc98 feat(#22): add nuts_calc_tex.py Phase 3 com command (complements)
- 82c0b6f fix(#21): guarantee calc_sub/calc_div succeed whenever a valid pair exists
- 44a3c18 feat(#21): add nuts_calc_tex.py Phase 2 ope command (horizontal/vertical/mix/intermediate)
- acb1e84 feat(#20): add nuts_calc_tex.py Phase 1 (LaTeX CLI/PDF foundation)
