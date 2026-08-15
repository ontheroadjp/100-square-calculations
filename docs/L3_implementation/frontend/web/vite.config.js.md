# `frontend/web/vite.config.js`

## 目的・役割

`frontend/web` の Vite 設定。開発サーバーで Sass の元ファイルと行番号をブラウザーの開発者ツールへ提供し、複数の HTML ページを独立したビルドエントリとして扱う。

## 動作の概要

- `css.devSourcemap` を有効にし、開発時に Sass から生成した CSS の source map を配信する（`frontend/web/vite.config.js:4-7`）。
- `index.html`、`catalog.html`、`preset.html` を `build.rollupOptions.input` に登録し、Vite のマルチページビルドを構成する（`frontend/web/vite.config.js:8-16`）。

## 重要な設計判断とその理由

source map は開発サーバーの CSS にだけ有効化する。Chrome DevTools で Elements から `_base.scss` などの Sass partial と行番号を参照できるようにする一方、production build では JavaScript source map の公開と配布容量の増加を避ける。

## 統合ポイント

- 呼び出し元: `npm run dev`、`npm run build`、`npm run preview`。
- 呼び出し先: Vite の CSS preprocessor とマルチページ build 設定。
- 回帰テスト: `frontend/web/vite.config.test.js:1-9` が、開発用 CSS source map が有効で production build source map が未設定であることを確認する。

## 注意事項・既知の制限

- 元の Sass ファイル名・行番号を確認する際は `npm run dev` を使用する。production build は source map を出力しない。
- Chrome DevTools 側でも CSS source map が有効である必要がある。
