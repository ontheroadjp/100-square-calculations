# `frontend/web/src/styles/_layout.scss`

## 目的・役割

`grade-drills`(ホーム/絞り込み/カタログ)と `preset-detail`(プリセット詳細)画面固有のレイアウトを定義するパーシャル。詳細な分割方針は [[./main.scss]] を参照。

## 動作の概要

`App.css`([[../../../../frontend/spa/src/App.css]] 参照)のうち、`.drill-filter-bar`/`.drill-home-section`/`.number-type-*`/`.drill-start-grid`/`.preset-detail*` 等のセレクタを移植している。`$color-*` 変数は `_base.scss` から `@use 'base' as *` で参照する。

issue #97 で共通ナビゲーションシェル導入・カスタム生成フォーム/検索UI撤去に伴い、`.grade-nav`/`.grade-link`(旧2リンクナビ)、`.drill-search`(検索ボックス)、`.custom-generator`(`customGenerator.js` 専用コンテナ)を削除した(いずれも参照元マークアップが同issueで削除済み)。

## 統合ポイント

- 呼び出し元: `main.scss`(`@use 'layout'`)。
- 呼び出し先: `_base.scss`(色変数)。

## 注意事項・既知の制限

- [[./main.scss]] と同じく、`frontend/spa/src/App.css` からの追従コピーが必要な保守対象。`.grade-nav`/`.grade-link`/`.drill-search`/`.custom-generator` は issue #97 で削除済みのため、`App.css` 側に対応クラスが残っていても本ファイルには追従しない。

## 変更履歴(git log より自動生成)

- b11ac96 feat(#97): rebuild frontend/web nav shell and design tokens, remove custom generator/search/ungraded UI
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
