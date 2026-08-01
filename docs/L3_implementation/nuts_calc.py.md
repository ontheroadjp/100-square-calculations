# `nuts_calc.py`

## 目的・役割

計算ドリル PDF 生成 CLI 本体。`argparse` でコマンドライン引数を解析し(`_init`)、ReportLab の `Frame`/`Table` を組み立てて PDF(と任意で CSV)を出力する(`main`)。対応する `command` は `ope`(四則演算)・`com`(補数)・`100`(100マス)・`99`(九九)・`aBc`・`squ`(平方数)・`pi`(円周率計算)の7種類。

## 動作の概要

- `_init()` が引数を検証・正規化して `argparse.Namespace` を返す。`command` ごとに `-a`/`-b`(桁数指定)から `a_min`/`a_max`/`b_min`/`b_max`(実際の数値範囲)を導出する(`nuts_calc.py:215-244,272`)。
- `main(ini)` は用紙サイズ・コマンドに応じて `Frame` レイアウトを組み立て、`get_vertical_contents_raw_dataset` で問題データを生成し、`command` ごとの描画ロジックで PDF 2種(通常版・解答版 `_read.pdf`)を作る。`ini.merge` が真の場合は1ファイルに問題ページ→解答ページを交互に収める(`next_content` による1ページ遅延の仕組み)。

## `ope` コマンドの出力形式(横書き / 筆算)

`ope` コマンドには2つの出力形式がある:

- **横書き形式(デフォルト)**: `a + b = c` を1行で表示。`get_operation_data` → `get_vertical_contents` → `add_vertical_frame_set` の組み合わせで、問題の各要素(index/a/演算子/b/=/answer)をそれぞれ専用の縦長 `Frame` に敷き詰める(`nuts_calc.py:927-956,1281-1348`)。
- **筆算(縦書き)形式(`--vertical`)**: 小学校で習う「筆算」の見た目(桁を揃えて演算子付きの2数を並べ、線の下に答え)で出力する。`add`・`sub`・`mul`(掛ける数が1桁のときのみ)に対応。

### 筆算形式の実装方針

横書き形式とは描画の考え方が根本的に異なる(桁ごとに列を揃える必要があり、問題ごとに1つの自己完結したブロックになる)ため、既存の「フィールドごとに1つの `Frame`」という設計は使わず、別経路で実装している:

- `get_vertical_digit_width`: `-a`/`-b` の範囲と選択演算子から、桁揃えに必要な桁数(列数)を算出する。ページ全体で共通の桁数を使うことで、問題ごとに列がガタつかないようにしている。
- `get_vertical_calc_block`: 1問分のブロック(3行 × (1+桁数)列の `Table`)を作る。1行目=index+aの桁、2行目=演算子+bの桁(この行の下に線を引く)、3行目=答えの桁(`c_str=''` で空欄にできる)。
- `pad_digits_to_width`: 数値文字列を右詰めで桁数分のセルに変換する(足りない桁は空文字)。
- `main()` 内、`is_vertical_ope`(`ini.command == 'ope' and ini.vertical`)が真のときだけ通る専用分岐(`nuts_calc.py` の frame 生成部と content 生成部それぞれに1箇所ずつ)で、`ini.columns` 個の等幅 `Frame` を作り、各 `Frame` に `ini.rows` 個の筆算ブロックを縦に並べた `Table` を流し込む。空欄版(`blank_columns`)を通常 PDF に、正答入り版(`filled_columns`)を `_read.pdf` に使う。`merge`/`with_bottom_answer`/`csv`/`debug` は既存の横書きパスと同じ変数・関数(`row_heights`/`get_bottom_results`/CSV 出力ブロック)を共有しているため、挙動は横書き版と揃っている。

### 重要な設計判断

- **対応演算を意図的に絞っている**: `div`(長除法は商・除数の囲み枠を使う全く別レイアウトが必要)と `mix`(`div` を含みうる)、および掛ける数が2桁以上の `mul`(部分積の複数段表示が必要)は `--vertical` では未対応。`_init()` で `VERTICAL_UNSUPPORTED_OPERATORS`(`div`/`mix`)と `SINGLE_DIGIT_MAX` 判定によりバリデーションし、非対応な組み合わせは PDF 生成前に `exit(1)` で弾く(`nuts_calc.py:257-270`)。理由・スコープは issue #9(本機能)/#10(複数桁 mul の部分積対応)/#11(長除法対応)を参照。
- **バリデーション失敗時は `exit(1)` を使う**: ファイル内の他の既存バリデーション(例: `-a option must be set.`)は引数なし `exit()` を使っており、実際には終了コード0を返すため、`web/backend/app.py` の `subprocess.run(..., check=True)` はこれを「成功」とみなしてしまう(既知の制限、下記参照)。今回追加したバリデーションはこの罠を避けるため明示的に `exit(1)` にしている。
- **ReportLab の `TableStyle` はコマンドの順序に依存する**: `get_vertical_calc_block` の `LINEBELOW`(答えとの区切り線)は `GRID`(通常は透明なデバッグ用グリッド)より**後**に追加しなければならない。逆順にすると `GRID` の `width=0` 指定が同じセル境界の `LINEBELOW` を上書きして線が消える(実装中に実機で発見)。
- **筆算ブロックの高さは `slot_height * VERTICAL_BLOCK_HEIGHT_RATIO`(0.85)で計算し、外側の `Table` は `VALIGN: TOP`**: ブロックの3行がスロットの100%を占めると隣接する問題同士が隙間なく密着して読みにくいため、上詰めにして下に余白を残している。

## 統合ポイント

- 呼び出し元: CLI 直接実行(`python3 nuts_calc.py <paper_size> <command> ...`)、`factory.sh`(バッチ生成)、`web/backend/app.py`(Web UI 経由)。
- 呼び出し先: なし(ReportLab で完結)。

## 注意事項・既知の制限

- `--vertical` は `ope` コマンドの `add`/`sub`/`mul`(掛ける数が1桁)のみ対応。`div`/`mix`/複数桁 `mul`/`--intermediate` との併用は非対応(上記参照)。
- 自動テストはリポジトリ内に存在しない(`docs/.ai/repo.profile.json` の `notes.tests` 参照)。実機での CLI 実行と生成 PDF の目視確認が検証手段。
