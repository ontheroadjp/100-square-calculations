# `frontend/web/package.json`

## 目的・役割

`frontend/web`(HTML/CSS(Sass)/JS のみで実装した軽量フロントエンド、issue #88)のビルド設定。`frontend/spa`(React/Vite)と同じ Vite だが、React・i18next 系パッケージは一切含まない。

## 動作の概要

- `scripts`: `dev`(`vite`)/`build`(`vite build`)/`preview`(`vite preview`)。`frontend/spa` と同じコマンド体系。
- `devDependencies`: `vite` と `sass`(Dart Sass CLI 相当。Vite が `.scss` import を検出すると自動的に呼び出す)のみ。`react`/`react-dom`/`i18next` 系の依存は持たない。
- `dependencies`: `katex`(issue #132、`presetDetail.js` の問題サンプルを分数・帯分数表記でレンダリングするために追加。ブラウザバンドルに含まれるランタイム依存のため `devDependencies` ではなくこちらに置く)。

## 重要な設計判断とその理由

### Vite vanilla テンプレートを採用した理由

ユーザーからの明示的な要望により、gulp のような軽量ビルド構成(保存時の自動 Sass コンパイル・dev サーバー)を求めつつ webpack 級の重量設定は避けたいという方針で、`frontend/spa` と同じ Vite を React なしの vanilla テンプレートで採用した。ツールを一つに統一でき、設定はほぼゼロで Sass・HMR・本番ビルドが揃う。

### 複数ページ構成(SPAではない)にした理由

ユーザーからの明示的な指示により、`frontend/web` は SPA(単一 `index.html` を JS ルーターで画面切替する構成)ではなく、画面ごとに実在の `.html`(`index.html`/`catalog.html`/`preset.html`/`custom.html`)を持つ構成にした(issue #88)。このため `vite.config.js`(`build.rollupOptions.input` に4つの `.html` を列挙)で Vite のマルチページビルドを設定している。

## 統合ポイント

- 呼び出し元: `npm run dev`/`npm run build`(開発者が直接実行)。
- 呼び出し先: なし(ビルド設定のみ)。

## 注意事項・既知の制限

- バックエンド API は `frontend/spa` と同じ `backend/`([[../../backend/app.py]] 参照)を共有する。`frontend/web` 独自のバックエンドは持たない。

## 変更履歴（git log より自動生成）

- 7b5a9b9 feat(#132): add per-grade accent, KaTeX examples, generalized setting hints, and move problem count into common settings on preset detail page
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
