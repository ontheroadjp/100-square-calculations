# `frontend/web/src/styles/main.scss`

## 目的・役割

`frontend/web` のグローバルスタイルのエントリポイント。`frontend/spa/src/App.css`([[../../../frontend/spa/src/App.css]] 参照、734行の単一 CSS ファイル)を、Sass の `@use` でパーシャル分割して移植したもの。クラス名・見た目は `App.css` と同一になるよう移植している(`frontend/spa` とほぼ同じ HTML 構造・クラス命名で組んでいるため、CSS 側もセレクタをそのまま踏襲できる)。

## 動作の概要

`@use 'base'; @use 'components'; @use 'layout'; @use 'navShell'; @use 'pcMakeFlow';`(issue #97 で `navShell`、issue #101 で `pcMakeFlow` を追加)の5行のみ。各ページエントリ(`home.js`/`catalog.js`/`preset.js`。`custom.js` は issue #97 で削除)の先頭で `import './styles/main.scss'` され、Vite が Dart Sass でコンパイルして `<style>` として注入する。

## 重要な設計判断とその理由

### 3ファイルに分割した理由(_base/_components/_layout)

`App.css` は無分割の1ファイル(734行)だったが、`frontend/web` では以下の3分類に分けた:
- `_base.scss`: リセット・変数(`$color-*`等のデザイントークン)・`.app-container`/`.app-header`/`.main-content` などページ全体のシェル。
- `_components.scss`: フォーム部品・ボタン・カード・バッジなど、複数画面で再利用される見た目のパーツ。
- `_layout.scss`: `grade-drills`/`preset-detail` など、特定画面の構造に紐づくレイアウト。

過度な抽象化(mixin・関数の多用)は避け、Sass の機能は「変数」と「ネスト」の2つだけに絞った。`App.css` からの移植であり新規デザインではないため、変数化した色以外は元の値をそのまま踏襲している。

issue #97 で4つ目のパーシャル `_navShell.scss`([[./navShell.scss]] 参照)を追加した。`App.css` に対応部分がない完全新規コンポーネント(共通ナビゲーションシェル)のため、既存3分類とは独立させた。issue #101 で5つ目のパーシャル `_pcMakeFlow.scss`([[./_pcMakeFlow.scss]] 参照、PC向け4カラムレイアウト)を同様の理由で追加した。

## 統合ポイント

- 呼び出し元: `home.js`/`catalog.js`/`preset.js`(各ページエントリが個別に `import`。`frontend/web` は複数ページ構成のため単一の `main.js` は存在しない、issue #88)。
- 呼び出し先: `_base.scss`/`_components.scss`/`_layout.scss`/`_navShell.scss`/`_pcMakeFlow.scss`。

## 注意事項・既知の制限

- `frontend/spa/src/App.css` が更新された場合、本ファイル(および `_base`/`_components`/`_layout` の3パーシャル)は追従コピーが必要(issue #88 時点ではほぼ同一内容)。`_navShell.scss`/`_pcMakeFlow.scss` は `App.css` に対応がないため対象外。

## 変更履歴(git log より自動生成)

- d9599eb feat(#101): add PC 4-column layout to frontend/web's make flow
- b11ac96 feat(#97): rebuild frontend/web nav shell and design tokens, remove custom generator/search/ungraded UI
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
