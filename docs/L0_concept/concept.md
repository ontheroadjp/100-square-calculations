# Concept

## 目的

このリポジトリは、そろばん式暗算(フラッシュ暗算に近い「4桁変換法」)のトレーニング教材として使う計算ドリルの PDF を、CLI(`nuts_calc.py`)またはブラウザ上の Web フォーム(`web/`)から生成するツール群である。

根拠:
- `README.md:3-4` — "generate various types of mathematical practice worksheets... in PDF format... for mental arithmetic and basic math skills."
- `memo.md:1-543` — 暗算指導法(2桁×1桁、10いくつ同士の掛け算、2桁×11の掛け算などを4桁の数値に変換してから3桁に畳み込む方法)の解説と、学習ステップ(基礎力トレーニング→変換トレーニング→実践→書かないドリル)が詳細に記述されている。このファイルは `dev` ブランチのマージで一度削除されたが、暗算指導法の一次資料としての価値からユーザーの指示で復元済み(2026-07-22)。
- `factory.sh:124-160`(`_basic` 関数) — `step-01.pdf` 〜 `step-08.pdf` という名前で、`memo.md` の学習ステップに対応する PDF を一括生成している。
- `web/frontend/src/App.jsx:115-382` — CLI と同じ7種類の `command`(`ope`/`com`/`100`/`99`/`aBc`/`squ`/`pi`)をフォームで選択し、Flask バックエンド経由で同じ `nuts_calc.py` を呼び出す UI を提供している(根拠: `web/backend/app.py:20-22` が `python ../../nuts_calc.py` を `subprocess.run` する)。

`memo.md` は実装コードではないが、CLI/Web いずれもが生成する問題形式(`aBc`, `squ`, `99`, `com` など)の教育的な意味づけを説明する一次資料であり、ツールの設計意図を理解する上で必須の根拠である。

## 解決する問題

- 暗算力(特に中学受験を見据えた計算速度)を伸ばすための反復練習用ドリルを、紙に印刷できる形で継続的に・大量に・パラメータを変えながら生成する必要がある(`memo.md:328-394` に計算力の重要性の説明あり)。
- 市販のドリルでは実現しづらい細かいパラメータ調整(桁数、範囲、順序、ページ数、用紙サイズ、答えの有無など)を、CLI 引数または Web フォームで制御できるようにしている(根拠: `nuts_calc.py:37-150` 相当の `argparse` 定義、`web/frontend/src/App.jsx` のフォーム項目)。
- Web UI(`web/`)の追加により、`argparse` のオプション名を覚えていない利用者(保護者など)でもブラウザ上のフォームから同じ生成機能を使えるようにしている。

## 対象ユーザー

- CLI は開発者/保護者が直接操作することを前提としている(根拠: `README.md:35-71` の Usage セクション)。
- Web UI は言語切り替え(英語/日本語、`web/frontend/src/i18n.js`, `public/locales/{en,ja}/translation.json`)を備えており、非エンジニアの保護者が使うことを意図していると推測される(未確認: 明示的な想定利用者の記述はない)。
- `memo.md` の内容(受験算数、暗算指導のノウハウ)から、想定利用者は小学生(低学年〜中学受験期)とその保護者、または学習塾であると推定される。`nuts_calc.py` 内の `HEADER_STR`/`AUTHOR` = `'Nuts Education'`、PDF 内の copyright 表記 `Copyright(c) 2024 Nuts Education` から、"Nuts Education" というブランド名が使われていることが確認できる。ただし具体的な事業体としての詳細はリポジトリ内から確認できない(未確認)。

## 設計上の制約

- CLI 経路は、CLI → ReportLab → PDF/CSV のワンショット変換のみ(データベースなし)。Web UI 経路は React(ブラウザ) → Flask(`web/backend/app.py`) → `subprocess` で `nuts_calc.py` を起動 → 生成された PDF をレスポンスとして返す、という構成で、いずれも状態を永続化しない(根拠: `web/backend/app.py:1-83` に DB 接続や永続ストレージの記述なし。生成 PDF は `web/backend/generated_pdfs/` に一時保存されるのみ)。
- 用紙サイズは A3 / A4 / A4横(landscape) / B5 の4種類に限定され、それぞれ余白・フォントサイズ・仮想ページ分割数(A3は4分割、A4横は2分割)が異なるレイアウトロジックがハードコードされている(根拠: `nuts_calc.py` の用紙サイズ分岐、CLI 側の `100masu.py` 由来のロジックがそのまま引き継がれている)。
- 問題タイプ(`command` 引数)は `ope`(四則演算), `com`(補数), `100`(100マス計算), `99`(九九), `aBc`(4桁→3桁変換トレーニング), `squ`(平方数), `pi`(円周率倍)の7種類に限定される。CLI・Web UI 双方でこの7種類が共通のインターフェースになっている(根拠: `web/backend/app.py` はこれらの値をそのまま `nuts_calc.py` の位置引数として渡すだけで、独自のバリデーションを追加していない)。

## 未確認事項

- "Nuts Education" が何を指す組織/屋号か: リポジトリ内に説明なし。
- ライセンス: `LICENSE`(MIT, `LICENSE:1-21`)が追加されたことで再配布条件は明確になったが、Web UI 部分(React/Flask)を含めた全体に同じライセンスが適用される前提かは明記されていない。
