# `frontend/web/src/custom.js`

## 目的・役割

`custom.html`(カスタム生成フォーム画面)のページエントリ。`GET /renderer-info` を取得してから `customGenerator.js`([[./customGenerator.js]] 参照)の `mountCustomGenerator()` に橋渡しする薄いグルーコード。

## 動作の概要

- `mount()`: `GET /renderer-info` を fetch し、`activeRenderer === 'latex'` を `supportsVertical` として `mountCustomGenerator(document.getElementById('generator'), { supportsVertical })` に渡す。

## 統合ポイント

- 呼び出し元: `custom.html` の `<script type="module" src="/src/custom.js">`。
- 呼び出し先: `customGenerator.js`(`mountCustomGenerator`)、`backend`(`GET /renderer-info`)。

## 注意事項・既知の制限

- `frontend/spa` では `GradeDrills.jsx` が1回だけ `GET /renderer-info` を取得し `supportsVertical` を `CustomGenerator` に prop で渡していたが、`frontend/web` はページごとに独立している(issue #88)ため、`custom.html` に直接アクセスした場合でも `supportsVertical` を自前で取得できるよう、本ファイルが同じ fetch を再度行う。
