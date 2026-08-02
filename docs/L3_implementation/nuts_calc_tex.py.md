# `nuts_calc_tex.py`

## 目的・役割

`nuts_calc.py`(ReportLab ベース)とは**完全に独立した**、LaTeX(TeX)でレンダリングする計算ドリル PDF 生成 CLI のプロトタイプ。issue #19(親トラッキング issue)で計画されている全7コマンド再実装の Phase 1(issue #20)にあたり、このコミット時点では **CLI 引数・ページ/PDF レイアウト・TeX ビルドパイプライン・CSV 出力という共通基盤のみ**を実装している。`command`/`operator` 引数は受け取るが、実際の問題データ生成・コマンドごとの分岐は未実装(プレースホルダーコンテンツで全体のパイプラインを検証している段階)。

`nuts_calc.py` とは import 等のコード共有を一切行わない(`nuts_calc.py` 側も変更しない)。将来的に両者を同じ CLI 契約で切り替えられるラッパーを作る前提のため、引数体系は `nuts_calc.py` の `_init()` に似せているが、実装は完全に別物。

## 動作の概要

- `_init()`: `nuts_calc.py` と同じ引数(`paper_size`/`command`/`-a`/`-b`/`--a-min`/`--a-max`/`--b-min`/`--b-max`/`-o`/`--rows`/`--columns`/`--page`/`--merge`/`--csv`/`--out-file`/`--with-bottom-answer`/`--debug` 等)を独立に定義・パースする。`-r`/`-c` は1以上、`-p` は1以上を要求する(`nuts_calc_tex.py:180-184`)。
- `Page` データクラス(`blocks: list[str]`, `columns: int`, `bottom_answer_tex: str | None`): 1ページ分の LaTeX コンテンツを表す最小単位。Phase 2 以降の各コマンド実装は、実データから `Page` を組み立てる関数を追加するだけでこの基盤に乗る設計。
- `build_preamble_tex`/`build_page_header_tex`/`build_page_tex`/`build_document_tex`: LaTeX ソースを文字列として組み立てる。用紙サイズは `geometry` パッケージのオプション(`a3paper`/`a4paper`/`b5paper`/`a4paper,landscape`)にマッピングし、ヘッダー(タイトル・日付欄)・フッター(ページ番号・著作権、`fancyhdr`)・行×列グリッドを構築する。
- `compile_tex`: `pdflatex -interaction=nonstopmode -halt-on-error` を一時ディレクトリで subprocess 実行し、生成された PDF を指定パスへコピーする。失敗時は `pdflatex` の出力末尾を含めて `exit(1)` する。
- 出力ファイル名の導出は `nuts_calc.py`(issue #15 修正後)と同様に `os.path.splitext(ini.out_file)` を使う(`_read.pdf`/`.csv` の付与)。
- `main(ini)`: `build_placeholder_page` で仮コンテンツ(`n) ___` / `n) ___ = n`)を rows×columns×pages 分生成し、`--merge` の有無に応じて blank/filled/merge の3モードでドキュメントをビルドする。`--csv` 指定時は問題データ相当の行を CSV に書き出す。

## `--merge` のセマンティクス(`nuts_calc.py` との違い)

`nuts_calc.py` の `--merge` は「回答ページを1ページ遅延させて次ページに挿入する」("next_content" の仕組み)という独特の割り込み方をするが、`nuts_calc_tex.py` はこれをあえて単純化し、**各ページの直後にその回答ページを続ける**(page1(blank) → page1(answer) → page2(blank) → page2(answer) → ...)方式にしている。実装がシンプルになり、LaTeX 1回のコンパイルで完結する(PDF マージ用の追加ライブラリが不要)というメリットがあるための意図的な設計判断。

## `longdivision` パッケージの vendoring

`longdivision`(CTAN、LPPL ライセンス、Phase 2 の `ope --vertical -o div` で使用予定)は Ubuntu の `texlive-latex-extra` に同梱されていないため、`vendor/texmf/tex/latex/longdivision/longdivision.sty` としてリポジトリに同梱し、`compile_tex` が `TEXINPUTS` 環境変数にこのパスを追加することで、クローン後に手動で `TEXMFHOME` へ配置しなくても `pdflatex` から解決できるようにしている(`nuts_calc_tex.py:36,258`)。プリアンブルでは `xlop`(add/sub/mul の繰り上がり表示に使用予定、Ubuntu 標準の `texlive-latex-extra` に同梱)も読み込んでいる。

## 統合ポイント

- 呼び出し元: CLI 直接実行(`python3 nuts_calc_tex.py <paper_size> <command> ...`)のみ。`nuts_calc.py`/`web/backend/app.py`/`factory.sh` からは呼ばれない(まだ配線されていない)。
- 呼び出し先: `pdflatex`(要 LaTeX ディストリビューション、`texlive-latex-base` 等)。

## 注意事項・既知の制限

- **`command`/`operator` は未使用**: Phase 1 時点ではプレースホルダーコンテンツのみで、実際の問題(四則演算・補数・100マス等)は生成されない。Phase 2(issue #21)以降で `ope` から順に実装される。
- **`pdflatex` が必須**: `shutil.which('pdflatex')` が `None` の場合は明確なエラーメッセージで `exit(1)` する。CI やローカル環境に LaTeX が無い場合、`tests/test_nuts_calc_tex.py` は `pytest.mark.skipif` で自動的にスキップされる。
- **`--descend`/`--reverse`/`--shuffle`/`--intermediate`/`--vertical`/`--debug` は引数として受理されるが未使用**: これらは Phase 2 以降(`ope` の `--vertical`/`--intermediate` など)や、コマンド固有の実装で使われる予定。
- `nuts_calc.py` 側の `VERTICAL_UNSUPPORTED_OPERATORS`(`div`/`mix` を `--vertical` で拒否)のような制約は、この実装では意図的に踏襲しない方針(親 issue #19 参照)。

## 変更履歴(git log より自動生成)

- acb1e84 feat(#20): add nuts_calc_tex.py Phase 1 (LaTeX CLI/PDF foundation)
