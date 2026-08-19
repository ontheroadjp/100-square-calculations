# `frontend/web/src/styles/main.scss`

## 目的・役割

`frontend/web` のグローバルスタイルのエントリポイント。かつて併存していた `frontend/spa/src/App.css`(734行の単一 CSS ファイル。`frontend/spa` 自体は issue #233 で削除)を、Sass の `@use` でパーシャル分割して移植したもの。クラス名・見た目は `App.css` と同一になるよう移植している(当時の `frontend/spa` とほぼ同じ HTML 構造・クラス命名で組んでいたため、CSS 側もセレクタをそのまま踏襲できた)。

## 動作の概要

`base`、`formControls`、`drillList`、`home`、`catalog`、`presetDetail`、`navShell`、`pcMakeFlow` をこの順で `@use` する(`frontend/web/src/styles/main.scss:1-8`)。各ページエントリ(`home.js`/`catalog.js`/`preset.js`)の先頭で `import './styles/main.scss'` され、Vite が Dart Sass でコンパイルする。

## 重要な設計判断とその理由

### 画面・UI階層で分割する理由

`frontend/web` は、スタイルの利用箇所と親子関係が追いやすいよう以下の責務で分割する:
- `_base.scss`: リセット、デザイントークン、ページ全体のシェル。
- `_formControls.scss`: フォーム入力とPDF iframe。
- `_drillList.scss`: ドリルリスト、ドリルカード、難易度バッジ、空状態。
- `_home.scss`: ホーム画面のヒーローと学年選択。
- `_catalog.scss`: カタログのヘッダー、カテゴリ、戻る導線。
- `_presetDetail.scss`: プリセット設定・完了・プレビュー画面。

過度な抽象化(mixin・関数の多用)は避け、Sass の機能は「変数」と「ネスト」の2つだけに絞った。`App.css` からの移植であり新規デザインではないため、変数化した色以外は元の値をそのまま踏襲している。

issue #97 で4つ目のパーシャル `_navShell.scss`([[./navShell.scss]] 参照)を追加した。`App.css` に対応部分がない完全新規コンポーネント(共通ナビゲーションシェル)のため、既存3分類とは独立させた。issue #101 で5つ目のパーシャル `_pcMakeFlow.scss`([[./_pcMakeFlow.scss]] 参照、PC向け4カラムレイアウト)を同様の理由で追加した。

## 統合ポイント

- 呼び出し元: `home.js`/`catalog.js`/`preset.js`(各ページエントリが個別に `import`。`frontend/web` は複数ページ構成のため単一の `main.js` は存在しない、issue #88)。
- 呼び出し先: 各スタイルパーシャル。

## 注意事項・既知の制限

- かつて併存していた `frontend/spa/src/App.css` の追従が必要な場合は、対応する責務のパーシャルへ反映する運用だった(`_navShell.scss`/`_pcMakeFlow.scss` は `frontend/web` 固有のため対象外)。`frontend/spa` 自体は issue #233 で削除され、以後追従コピー元は存在しない。

## 変更履歴(git log より自動生成)

- ff1576a refactor(#128): reorganize web Sass by UI hierarchy
- d9599eb feat(#101): add PC 4-column layout to frontend/web's make flow
- b11ac96 feat(#97): rebuild frontend/web nav shell and design tokens, remove custom generator/search/ungraded UI
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
