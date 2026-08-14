# `frontend/web/src/styles/_presetDetail.scss`

## 目的・役割

プリセット詳細の設定、作成完了、PDFプレビュー画面のスタイルを一元管理する。

## 動作の概要

`.preset-detail` を画面ルートにして、例題、設定ブロック、セグメント選択、開閉領域、トグル、作成ボタン、完了表示、プレビューを各親要素の下にネストして定義する(`frontend/web/src/styles/_presetDetail.scss:3-303`)。

## 統合ポイント

- 呼び出し元: `main.scss`。
- 利用元: `presetDetail.js`、`pcMakeFlow.js`。
- 呼び出し先: `_base.scss` のデザイントークン。

## 注意事項・既知の制限

`.preset-detail` の設定画面はモバイル詳細画面とPC作成フローで共有し、PC固有のレイアウトは `_pcMakeFlow.scss` が追加する。
