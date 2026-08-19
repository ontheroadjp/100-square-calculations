# 100マス計算ジェネレーター

## 概要
このプロジェクトは、主に100マス計算に焦点を当てた、様々な種類の算数練習用ワークシートをPDF形式で生成するツール群を提供します。暗算や基本的な算数スキルを向上させるための、カスタマイズされた練習教材を作成するのに役立ちます。

## 特徴
*   **多様な問題形式**: 基本的な四則演算（足し算、引き算、掛け算、割り算）、補数、100マス計算表、九九、平方数、特定の暗算問題など、様々なワークシートを生成します。
*   **カスタマイズ可能な生成**: 豊富なコマンドラインオプションにより、用紙サイズ、数値範囲、演算子、問題数、出力形式などを指定できます。
*   **PDF出力**: すべてのワークシートは、印刷に適した高品質なPDFファイルとして生成されます。
*   **解答オプション**: ページ下部に解答を含めたり、解答ファイルを結合したり、さらなる分析のために生の問題データをCSVに出力したりできます。
*   **自動一括生成**: `factory.sh`スクリプトは、事前に設定された様々なワークシートを自動で生成し、構造化された出力ディレクトリ (`dist/`) を作成します。
*   **Web UIフロントエンド** (`frontend/web`): 日本語のみに対応した、HTML/CSS(Sass)/JSのみ(React・i18nライブラリ不要)の軽量な静的サイト実装で、ドリルカタログの閲覧機能を提供します。同じ Flask バックエンドを利用します。(学年別・中学受験準備プリセットを提供する英語/日本語切替対応の React SPA `frontend/spa` がもう1つのフロントエンドとして存在していましたが、issue #233 で削除されました。)

## セットアップ
CLI(`nuts_calc_tex.py`)にはPython 3とLaTeX環境(`pdflatex`/`lualatex`)が必要です(pipパッケージへの依存はありません)。Web UIにはさらにFlask、Flask-Cors、Node.js、npmが必要です。Python側には `requirements.txt`/`pyproject.toml`/`setup.py` がないため、依存関係は手動で導入します。

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

3.  **Python依存関係をインストールする**(Web UIを使う場合。CLI自体はpipパッケージ不要):
    ```bash
    pip install flask flask-cors
    ```

4.  **Webフロントエンドの依存関係をインストールする**:
    ```bash
    cd frontend/web && npm install && cd ../..
    ```

5.  **LaTeX環境のインストール（オプション）**: `nuts_calc_tex.py` は `pdflatex` を使います。分数、筆算、小数、整数・小数・分数混合、中学受験準備、繰り上がり条件付きカードを使う場合に必要です。`longdivision` はリポジトリ内に同梱されています。

    作業が完了したら、仮想環境を非アクティベートするには:
    ```bash
    deactivate
    ```

## 使用方法

### `nuts_calc_tex.py`を使ったワークシートの生成
`nuts_calc_tex.py`スクリプト(`backend/` 内)は、主要なジェネレーターです。様々なオプションを付けて直接実行できます。旧 ReportLab版 `nuts_calc.py` は issue #232 で削除されました。

```bash
cd backend
python nuts_calc_tex.py <用紙サイズ> <コマンド> [オプション]
```

**例: A4サイズの足し算問題を5ページ生成する**
```bash
python nuts_calc_tex.py A4 ope -o add -p 5 --out-file addition_A4_5pages.pdf
```

**例: 100マス計算表を生成する（A3サイズ）**
```bash
python nuts_calc_tex.py A3 100 --out-file 100_square_A3.pdf
```

**例: 九九の「7の段」をランダムな順序で生成する（A4横向き）**
```bash
python nuts_calc_tex.py a4l 99 -a 7 --shuffle --out-file kuku_7_random_A4L.pdf
```

すべてのオプションのリストを表示するには、以下を実行してください。
```bash
python nuts_calc_tex.py -h
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

2.  **フロントエンドを起動する**(`frontend/web`、日本語のみ、React・i18nライブラリ不要):
    ```bash
    cd frontend/web
    npm install
    npm run dev
    ```
    通常 `http://localhost:5173` で実行されます。

起動できたら、ブラウザでフロントエンドのアドレス（例: `http://localhost:5173`）を開いてWebインターフェースにアクセスしてください。

### チェックの実行

```bash
cd backend && python3 -m pytest -q
node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js
cd frontend/web && npm run build
```

`frontend/web` には lint/test スクリプトはありません。

## 依存関係
*   Python 3
*   Flask (`pip install Flask`)
*   Flask-Cors (`pip install Flask-Cors`)
*   Node.js と npm (`frontend/web` 用)
*   `pdflatex`/`lualatex`(`nuts_calc_tex.py` / LaTeXレンダラー用。CLI自体の唯一の外部依存で、pipパッケージは不要)

## アーキテクチャ

リポジトリは `backend/` + `frontend/{web}` 構成(将来 `backend`/`frontend` を別リポジトリに分離する可能性も見据えている)。かつては `frontend/{spa,web}` として2つの独立したフロントエンドを持っていたが、`frontend/spa` は issue #233 で削除された。

*   **CLI**: `backend/nuts_calc_tex.py` → LaTeX(`lualatex`/`pdflatex`) → PDF/CSV。サーバー、DB、永続状態はありません。旧 ReportLab版 `nuts_calc.py` は issue #232 で削除されました。
*   **Web UI**: フロントエンド(`frontend/web` の軽量静的サイト) → Flask backend(`backend/app.py`) → `backend/renderers.py` → `nuts_calc_tex.py` をsubprocess実行し、PDFを返します。レンダラー切り替えの仕組み(`NUTS_CALC_RENDERER`)自体は将来の別レンダラー追加に備えて維持されています。
*   **バッチ**: `backend/factory.sh` が `nuts_calc_tex.py` を繰り返し呼び出し、`dist/` に成果物を生成します。

`nuts_calc_tex.py` は旧 ReportLab版とコード共有しない独立実装で、互換7コマンドにLaTeX専用の分数・混合・比較・数論・変換系コマンドを加えた計20コマンドを持ちます。

## 設計原則

*   問題生成ロジックは各renderer CLIが所有し、Web backendはJSONをCLI引数へ変換します。
*   Python側は依存関係を固定していないため、必要なパッケージを手動で導入します。
*   CIはなく、pytest、Node組み込みテスト、Vite buildによるローカル検証が品質ゲートです。
*   `frontend/web` は React・i18nライブラリを使わない軽量なフロントエンドとして追加され、SPA(JSルーターによる単一ページ切替)ではなく、実在の複数ページで構成される静的サイトとして実装されている(かつて存在した `frontend/spa` はこの対比のもとで issue #233 まで併存していたが、現在は削除済み)。共有パッケージには依存せず、少数の純粋データモジュールを自身の中に持つ(将来のリポジトリ分離を見据えた設計)。

## ライセンス
MIT License
