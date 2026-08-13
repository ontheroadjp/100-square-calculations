# 100マス計算ジェネレーター

## 概要
このプロジェクトは、主に100マス計算に焦点を当てた、様々な種類の算数練習用ワークシートをPDF形式で生成するツール群を提供します。暗算や基本的な算数スキルを向上させるための、カスタマイズされた練習教材を作成するのに役立ちます。

## 特徴
*   **多様な問題形式**: 基本的な四則演算（足し算、引き算、掛け算、割り算）、補数、100マス計算表、九九、平方数、特定の暗算問題など、様々なワークシートを生成します。
*   **カスタマイズ可能な生成**: 豊富なコマンドラインオプションにより、用紙サイズ、数値範囲、演算子、問題数、出力形式などを指定できます。
*   **PDF出力**: すべてのワークシートは、印刷に適した高品質なPDFファイルとして生成されます。
*   **解答オプション**: ページ下部に解答を含めたり、解答ファイルを結合したり、さらなる分析のために生の問題データをCSVに出力したりできます。
*   **自動一括生成**: `factory.sh`スクリプトは、事前に設定された様々なワークシートを自動で生成し、構造化された出力ディレクトリ (`dist/`) を作成します。
*   **学年別・中学受験準備プリセット**: Web UIは1〜6年生のカードを提供します。LaTeXレンダラーでは、1年生に繰り上がり・繰り下がり条件で分けた加算2・減算2・混合2の6カード、4〜6年生に中学受験準備27カードを追加します。
*   **独立した2つのWeb UIフロントエンド**: `frontend/spa` は英語/日本語切替対応の React SPA です。`frontend/web` は日本語のみに対応した、HTML/CSS(Sass)/JSのみ(React・i18nライブラリ不要)の軽量な静的サイト実装で、ドリルカタログの閲覧機能を提供します。いずれも同じ Flask バックエンドを利用します。

## セットアップ
ReportLab版にはPython 3、Web UIにはさらにFlask、Flask-Cors、Node.js、npmが必要です。`nuts_calc_tex.py` または `NUTS_CALC_RENDERER=latex` を使う場合は `pdflatex` を含むLaTeX環境も必要です。Python側には `requirements.txt`/`pyproject.toml`/`setup.py` がないため、依存関係は手動で導入します。

1.  **リポジトリをクローンする**:
    ```bash
    git clone https://github.com/ontheroadjp/100-square-calculations.git
    cd 100-square-calculations
    ```

2.  **仮想環境を作成し、アクティベートする**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Python依存関係をインストールする**:
    ```bash
    pip install reportlab flask flask-cors
    ```

4.  **Webフロントエンドの依存関係をインストールする**:
    ```bash
    cd frontend/spa && npm install && cd ../..   # React SPA
    cd frontend/web && npm install && cd ../..   # 軽量な静的UI(どちらか一方で構いません)
    ```

5.  **LaTeX環境のインストール（オプション）**: `nuts_calc_tex.py` は `pdflatex` を使います。分数、筆算、小数、整数・小数・分数混合、中学受験準備、繰り上がり条件付きカードを使う場合に必要です。`longdivision` はリポジトリ内に同梱されています。

    作業が完了したら、仮想環境を非アクティベートするには:
    ```bash
    deactivate
    ```

## 使用方法

### `nuts_calc.py`を使ったワークシートの生成
`nuts_calc.py`スクリプト(`backend/` 内)は、主要なジェネレーターです。様々なオプションを付けて直接実行できます。

```bash
cd backend
python nuts_calc.py <用紙サイズ> <コマンド> [オプション]
```

**例: A4サイズの足し算問題を5ページ生成する**
```bash
python nuts_calc.py A4 ope -o add -p 5 --out-file addition_A4_5pages.pdf
```

**例: 100マス計算表を生成する（A3サイズ）**
```bash
python nuts_calc.py A3 100 --out-file 100_square_A3.pdf
```

**例: 九九の「7の段」をランダムな順序で生成する（A4横向き）**
```bash
python nuts_calc.py a4l 99 -a 7 --shuffle --out-file kuku_7_random_A4L.pdf
```

すべてのオプションのリストを表示するには、以下を実行してください。
```bash
python nuts_calc.py -h
```

### `nuts_calc_tex.py` のLaTeX専用ドリル

以下の例は `backend/` ディレクトリ内(`cd backend`)での実行を前提とします。`frac` は厳密な分数計算、`mixed` は整数・小数・分数の混合計算を生成します。2項整数の加減算では `--carry-borrow`、`--no-carry-borrow`、`--mixed-carry-borrow` を指定できます。これらの条件は数値範囲指定より優先され、繰り下がりありの減算は10〜19−1桁に限定されます。`ope -o div` では `--remainder`、`--no-remainder`、`--mixed-remainder` で割り算の余りを必須・禁止・混在から選べます(既定値と `--no-remainder` はこのフラグ追加以前と同じ挙動です)。素の `pdflatex` は日本語フォントに対応していないため、余りは「あまり」ではなく `\cdots`(例: `11 ÷ 4 = 2 ⋯ 3`)で表示されます。

```bash
python3 nuts_calc_tex.py A4 frac --numerator-digits 1 --denominator-digits 1 -o add sub --out-file fractions.pdf
python3 nuts_calc_tex.py A4 ope -o add sub --mixed-carry-borrow --out-file grade1-mixed.pdf
python3 nuts_calc_tex.py A4 ope -o div --remainder --out-file division-remainder.pdf
```

### `factory.sh`を使った一括生成
`factory.sh`スクリプト(`backend/` 内)は、事前に定義されたワークシートのセットの生成を自動化し、構造化された出力ディレクトリ (`dist/`) を作成します。

```bash
cd backend
./factory.sh
```

これにより、様々な暗算やその他の練習用シートが`dist/`ディレクトリに生成されます。生成されるワークシートの具体的な種類と設定を理解するには、`factory.sh`スクリプトを確認してください。

### Webインターフェースの実行 (Flask + いずれか一方のフロントエンド)

Webインターフェースを使用するには、Flaskバックエンドと、2つの独立したフロントエンドのうちいずれか一方を起動する必要があります。両フロントエンドとも同じバックエンドを使うため、両方同時に起動する必要はありません。

1.  **Flaskバックエンドを起動する**:
    *   ターミナルを開き、`backend`ディレクトリに移動します:
        ```bash
        cd backend
        ```
    *   仮想環境がアクティベートされていることを確認します（セットアップに従った場合）:
        ```bash
        source ../venv/bin/activate # venvの場所が異なる場合はパスを調整してください
        ```
    *   Flaskアプリを実行します:
        ```bash
        python app.py
        ```
    *   バックエンドは通常 `http://127.0.0.1:5000` で実行されます。

2.  **フロントエンドを起動する**(いずれか一方を選択):
    *   **React SPA**(`frontend/spa`、英語/日本語):
        ```bash
        cd frontend/spa
        npm install
        npm run dev
        ```
        通常 `http://localhost:5173` で実行されます。
    *   **軽量な静的UI**(`frontend/web`、日本語のみ、React・i18nライブラリ不要):
        ```bash
        cd frontend/web
        npm install
        npm run dev
        ```
        通常 `http://localhost:5173` で実行されます(両方の開発サーバーを同時に起動した場合、Vite が自動的に次の空きポート、例えば `5174` を選びます)。

起動できたら、ブラウザでフロントエンドのアドレス（例: `http://localhost:5173`）を開いてWebインターフェースにアクセスしてください。

### チェックの実行

```bash
cd backend && python3 -m pytest -q --ignore=tests/test_nuts_calc_init.py
node --test frontend/spa/src/drillPresets.test.js frontend/spa/src/drillCatalog.test.js frontend/spa/src/verticalLayout.test.js
cd frontend/spa && npm run build
cd frontend/web && npm run build
```

`backend/tests/test_nuts_calc_init.py` の9件は、修正済みの終了コードに期待値が追従していない既知の stale テストです。`npm run lint`(`frontend/spa`)は現在 `frontend/spa/src/drillPresets.js:433` の全角空白で1件失敗します。`frontend/web` には lint/test スクリプトはありません。

## 依存関係
*   Python 3
*   Flask (`pip install Flask`)
*   Flask-Cors (`pip install Flask-Cors`)
*   Node.js と npm (`frontend/spa` または `frontend/web` 用)
*   (オプション) `pdflatex`（`nuts_calc_tex.py` / LaTeXレンダラー用）

## アーキテクチャ

リポジトリは `backend/` + `frontend/{spa,web}` 構成で、Flask バックエンドを2つの独立したフロントエンドで共有する(将来 `backend`/`frontend` を別リポジトリに分離する可能性も見据えている)。

*   **CLI**: `backend/nuts_calc.py` → ReportLab → PDF/CSV。サーバー、DB、永続状態はありません。
*   **Web UI**: フロントエンド(`frontend/spa` の React SPA、または `frontend/web` の軽量静的サイト) → Flask backend(`backend/app.py`) → `backend/renderers.py` → `nuts_calc.py`（既定）または `nuts_calc_tex.py`（`NUTS_CALC_RENDERER=latex`）をsubprocess実行し、PDFを返します。
*   **バッチ**: `backend/factory.sh` が `nuts_calc.py` を繰り返し呼び出し、`dist/` に成果物を生成します。

`nuts_calc_tex.py` はReportLab版とコード共有しない独立実装で、互換7コマンドにLaTeX専用 `frac`/`mixed`/`compare` を加えた計10コマンドを持ちます。

## 設計原則

*   問題生成ロジックは各renderer CLIが所有し、Web backendはJSONをCLI引数へ変換します。
*   Python側は依存関係を固定していないため、必要なパッケージを手動で導入します。
*   CIはなく、pytest、Node組み込みテスト、Vite buildによるローカル検証が品質ゲートです。
*   `frontend/web` は React・i18nライブラリを使わない軽量な代替フロントエンドとして追加され、SPA(JSルーターによる単一ページ切替)ではなく、実在の複数ページで構成される静的サイトとして実装されている。両フロントエンドは共有パッケージに依存せず、少数の純粋データモジュールをそれぞれ複製している(将来のリポジトリ分離を見据えた設計)。

## ライセンス
MIT License
