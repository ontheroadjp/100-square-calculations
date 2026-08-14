# `frontend/web/src/styles/_home.scss`

## 目的・役割

ホーム画面のヒーローと学年選択カードを定義する。

## 動作の概要

`.hero-section` 内にタイトルと説明をまとめる(`frontend/web/src/styles/_home.scss:9-23`)。`.grade-picker` 配下では見出し、レスポンシブなグリッド、学年ごとの色を持つカード、アバターを定義する(`frontend/web/src/styles/_home.scss:25-74`)。

## 統合ポイント

- 呼び出し元: `main.scss`。
- 利用元: `index.html`、`home.js`。
- 呼び出し先: `_base.scss` のデザイントークン。
