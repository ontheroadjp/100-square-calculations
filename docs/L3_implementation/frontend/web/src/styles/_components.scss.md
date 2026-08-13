# `frontend/web/src/styles/_components.scss`

## 目的・役割

フォーム部品・カード・バッジなど、複数画面(ドリルカタログ/プリセット詳細)で共通して使う見た目のパーツを定義するパーシャル。詳細な分割方針は [[./main.scss]] を参照。

## 動作の概要

`App.css`([[../../../../frontend/spa/src/App.css]] 参照)のうち、`.form-group`/`.preset-card*`/`.drill-badge*`/`.preset-download-button`/`.pdf-iframe*`/`.regenerate-button`/`.back-button` 等のセレクタを移植している。`$color-*` 変数は `_base.scss` から `@use 'base' as *` で参照する。

issue #97 で `custom.html`/`src/customGenerator.js` を削除した際、それらだけが使っていた `.form-layout`/`.form-grid`/`.checkbox-group`/`.checkbox-grid`/`.required-text`/`.optional-text`/`.submit-button-container`/`.submit-button`/`.tab-nav`/`.tab-pane`/`.no-pdf-message`/`.result-display`/`.download-button`/`.error-message` を削除した(他ファイルでの参照がないことを `grep` で確認済み)。

## 統合ポイント

- 呼び出し元: `main.scss`(`@use 'components'`)。
- 呼び出し先: `_base.scss`(色変数)。

## 注意事項・既知の制限

- [[./main.scss]] と同じく、`frontend/spa/src/App.css` からの追従コピーが必要な保守対象。`customGenerator.js` 専用だった上記クラスは issue #97 で削除済みのため、`App.css` 側に対応クラスが残っていても本ファイルには追従しない。

## 変更履歴(git log より自動生成)

- b11ac96 feat(#97): rebuild frontend/web nav shell and design tokens, remove custom generator/search/ungraded UI
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
