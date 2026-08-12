# `frontend/web/src/main.js`

## 目的・役割

`frontend/web` のエントリポイント。Sass のグローバルスタイル(`styles/main.scss`)を読み込み、`app.js` の `renderApp()` を `#app` 要素に対して1回呼び出す。

## 動作の概要

- `import './styles/main.scss'`: Vite が Sass コンパイルして `<style>` として注入する。
- `renderApp(document.querySelector('#app'))`: `index.html` の `<div id="app">` を起点にアプリ全体を描画する。

## 統合ポイント

- 呼び出し元: `index.html` の `<script type="module" src="/src/main.js">`。
- 呼び出し先: `app.js` の `renderApp()`。

## 注意事項・既知の制限

- `frontend/spa/src/main.jsx` と異なり React の `createRoot`/`StrictMode` は使わない。DOM 操作は素朴な `innerHTML` 差し替えベース([[./gradeDrills.js]] 参照)。
