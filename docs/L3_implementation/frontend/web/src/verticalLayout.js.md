# `frontend/web/src/verticalLayout.js`

## 目的・役割

`frontend/spa/src/verticalLayout.js`([[../../frontend/spa/src/verticalLayout.js]] 参照)をそのまま複製したファイル。筆算(縦書き)出力の用紙サイズ別行数を解決する純粋関数で、React に依存しないため無変更で再利用できる。

## 動作の概要

`VERTICAL_ROWS_BY_PAPER_SIZE`/`VERTICAL_COLUMNS`/`getVerticalRows(paperSize)`/`isVerticalOperation(params)` を export する。内容は [[../../frontend/spa/src/verticalLayout.js]] と完全に同一。

## 統合ポイント

- 呼び出し元: `presetDetail.js`、`customGenerator.js`。
- 呼び出し先: なし。

## 注意事項・既知の制限

- `frontend/spa/src/verticalLayout.js` が更新された場合、本ファイルは追従コピーが必要(issue #88 時点では同一内容)。
