# `frontend/web/src/styles/_components.scss`

## 目的・役割

フォーム部品・ボタン・タブ・カード・バッジなど、複数画面(カスタム生成フォーム/ドリルカタログ/プリセット詳細)で共通して使う見た目のパーツを定義するパーシャル。詳細な分割方針は [[./main.scss]] を参照。

## 動作の概要

`App.css`([[../../../../frontend/spa/src/App.css]] 参照)のうち、`.form-*`/`.checkbox-*`/`.submit-button`/`.tab-*`/`.preset-card*`/`.drill-badge*`/`.download-button`/`.pdf-iframe*`/`.regenerate-button`/`.back-button` 等のセレクタを移植している。`$color-*` 変数は `_base.scss` から `@use 'base' as *` で参照する。

## 統合ポイント

- 呼び出し元: `main.scss`(`@use 'components'`)。
- 呼び出し先: `_base.scss`(色変数)。

## 注意事項・既知の制限

- [[./main.scss]] と同じく、`frontend/spa/src/App.css` からの追従コピーが必要な保守対象。
