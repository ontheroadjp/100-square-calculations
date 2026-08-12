# `frontend/web/src/app.js`

## 目的・役割

アプリのトップレベルシェル。`frontend/spa/src/App.jsx`([[../../frontend/spa/src/App.jsx]] 参照)に相当するが、言語切替 UI は持たない(日本語固定のため)。ヘッダー(タイトルのみ)を描画し、本体は `gradeDrills.js` の `mountGradeDrills()` に委譲する。

## 動作の概要

- `renderApp(root)`: `root.innerHTML` にヘッダーと `#main-content` コンテナを書き込み、`mountGradeDrills(document.getElementById('main-content'))` を呼ぶ。

## 統合ポイント

- 呼び出し元: `main.js`。
- 呼び出し先: `gradeDrills.js` の `mountGradeDrills()`。

## 注意事項・既知の制限

- `frontend/spa` の `App.jsx` にあった `lang-switcher`(English/日本語切替ボタン)は、`frontend/web` が日本語のみ対応のため実装していない。
