# `frontend/spa/src/verticalLayout.js`

## 目的・役割

筆算(`ope` + `vertical`)をWeb UIから生成する際に、用紙に収まる行数と列数を一元的に決定する。CLIの筆算既定値と同じ設定をUIが明示送信するため、通常計算用の問題密度が筆算PDFのページ数を増やすことを防ぐ。

## 動作の概要

- `VERTICAL_ROWS_BY_PAPER_SIZE`: A3/A4を4行、B5/A4横を2行に対応付ける。
- `VERTICAL_COLUMNS`: 筆算の既定列数2を表す。
- `getVerticalRows(paperSize)`: 大文字小文字を区別せず用紙別の行数を返す。未対応値はA4の行数を返す。
- `isVerticalOperation(params)`: `command_type === 'ope'` かつ `vertical === true` のリクエストだけを筆算と判定する。

## 統合ポイント

- 呼び出し元: `GradeDrills.jsx` の筆算プリセット、`CustomGenerator.jsx` の筆算オプション。
- 呼び出し先: なし。返した `rows`/`columns` は各コンポーネントから `POST /generate-pdf` のJSONとして送られる。

## 注意事項・既知の制限

- これはUI上の既定値であり、カスタム画面でユーザーが手動指定した行数は検証・制限しない。

## 変更履歴(git log より自動生成)

- fd449c7 fix(#57): apply vertical layout in web UI
