# `frontend/web/src/styles/_formControls.scss`

## 目的・役割

設定フォームの入力要素と、PDFプレビューiframeの共通スタイルを定義する。

## 動作の概要

`.form-group` 配下のラベルと入力要素を縦方向に配置する(`frontend/web/src/styles/_formControls.scss:3-31`)。`.pdf-iframe-container` はサイズ・枠線・overflowを管理し、配下の `.pdf-iframe` を領域全体に広げる(`frontend/web/src/styles/_formControls.scss:33-45`)。

## 統合ポイント

- 呼び出し元: `main.scss`。
- 利用元: `presetDetail.js`、`pcMakeFlow.js`。
- 呼び出し先: `_base.scss` のデザイントークン。

## 注意事項・既知の制限

iframeのPDF表示機能はブラウザ内蔵ビューアに委ね、操作UIは実装しない。
