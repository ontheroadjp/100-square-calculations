# `frontend/web/src/verticalLayout.js`

## 目的・役割

かつて併存していた `frontend/spa/src/verticalLayout.js` をそのまま複製したファイル(`frontend/spa` 自体は issue #233 で削除済み)。筆算(縦書き)出力の用紙サイズ別行数を解決する純粋関数で、React に依存しないため無変更で再利用できる。

## 動作の概要

`VERTICAL_ROWS_BY_PAPER_SIZE`/`VERTICAL_COLUMNS`/`getVerticalRows(paperSize)`/`isVerticalOperation(params)` を export する。内容は複製元の `frontend/spa/src/verticalLayout.js`(issue #233 で削除)と完全に同一だった。

## 統合ポイント

- 呼び出し元: `presetDetail.js`、`customGenerator.js`。
- 呼び出し先: なし。

## 注意事項・既知の制限

- 複製元だった `frontend/spa/src/verticalLayout.js` は issue #233 で削除され、以後追従コピー元は存在しない。本ファイルは以後独立して保守する。
