# `frontend/web/package.json`

## 目的・役割

`frontend/web`(HTML/CSS(Sass)/JS のみで実装した軽量フロントエンド、issue #88)のビルド設定。`frontend/spa`(React/Vite)と同じ Vite だが、React・i18next 系パッケージは一切含まない。

## 動作の概要

- `scripts`: `dev`(`vite`)/`build`(`vite build`)/`preview`(`vite preview`)。`frontend/spa` と同じコマンド体系。
- `devDependencies`: `vite` と `sass`(Dart Sass CLI 相当。Vite が `.scss` import を検出すると自動的に呼び出す)のみ。`react`/`react-dom`/`i18next` 系の依存は持たない。

## 重要な設計判断とその理由

### Vite vanilla テンプレートを採用した理由

ユーザーからの明示的な要望により、gulp のような軽量ビルド構成(保存時の自動 Sass コンパイル・dev サーバー)を求めつつ webpack 級の重量設定は避けたいという方針で、`frontend/spa` と同じ Vite を React なしの vanilla テンプレートで採用した。ツールを一つに統一でき、設定はほぼゼロで Sass・HMR・本番ビルドが揃う。

## 統合ポイント

- 呼び出し元: `npm run dev`/`npm run build`(開発者が直接実行)。
- 呼び出し先: なし(ビルド設定のみ)。

## 注意事項・既知の制限

- バックエンド API は `frontend/spa` と同じ `backend/`([[../../backend/app.py]] 参照)を共有する。`frontend/web` 独自のバックエンドは持たない。
