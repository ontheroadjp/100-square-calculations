# `frontend/web/src/styles/_layout.scss`

## 目的・役割

`grade-drills`(ホーム/検索/絞り込み/カタログ)と `preset-detail`(プリセット詳細)画面固有のレイアウトを定義するパーシャル。詳細な分割方針は [[./main.scss]] を参照。

## 動作の概要

`App.css`([[../../../../frontend/spa/src/App.css]] 参照)のうち、`.grade-nav`/`.grade-link`/`.drill-search`/`.drill-filter-bar`/`.drill-home-section`/`.number-type-*`/`.drill-start-grid`/`.custom-generator`/`.preset-detail*` 等のセレクタを移植している。`$color-*` 変数は `_base.scss` から `@use 'base' as *` で参照する。

## 統合ポイント

- 呼び出し元: `main.scss`(`@use 'layout'`)。
- 呼び出し先: `_base.scss`(色変数)。

## 注意事項・既知の制限

- [[./main.scss]] と同じく、`frontend/spa/src/App.css` からの追従コピーが必要な保守対象。
