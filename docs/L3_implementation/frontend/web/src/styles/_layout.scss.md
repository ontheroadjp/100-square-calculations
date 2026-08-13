# `frontend/web/src/styles/_layout.scss`

## 目的・役割

`grade-drills`(ホーム/絞り込み/カタログ)と `preset-detail`(プリセット詳細)画面固有のレイアウトを定義するパーシャル。詳細な分割方針は [[./main.scss]] を参照。

## 動作の概要

`App.css`([[../../../../frontend/spa/src/App.css]] 参照)のうち、`.drill-filter-bar`/`.drill-home-section`/`.number-type-*`/`.drill-start-grid`/`.preset-detail*` 等のセレクタを移植している。`$color-*` 変数は `_base.scss` から `@use 'base' as *` で参照する。

issue #97 で共通ナビゲーションシェル導入・カスタム生成フォーム/検索UI撤去に伴い、`.grade-nav`/`.grade-link`(旧2リンクナビ)、`.drill-search`(検索ボックス)、`.custom-generator`(`customGenerator.js` 専用コンテナ)を削除した(いずれも参照元マークアップが同issueで削除済み)。

issue #99 で `docs/uiux/wireframe_v1.png` 画面①②に合わせ、以下を追加した:
- `.hero-section`/`.hero-title`/`.hero-subtitle`(トップ画面のヒーローコピー)
- `.grade-picker-heading`/`.grade-picker-grid`/`.grade-picker-card`(`.grade-picker-card-1`〜`-6` で `_base.scss` の `$color-grade-1`〜`-6` を適用する学年カラーカード。2列/600px以上で3列)
- `.catalog-header`/`.catalog-heading`/`.category-picker-heading`(カテゴリ画面のヘッダー)
- `.category-section`/`.category-heading`/`.drill-list`(カテゴリ見出し+ドリルカードの縦積みリスト)

## 統合ポイント

- 呼び出し元: `main.scss`(`@use 'layout'`)。
- 呼び出し先: `_base.scss`(色変数。`$color-grade-1`〜`-6` を issue #99 で初めて消費した)。

## 注意事項・既知の制限

- [[./main.scss]] と同じく、`frontend/spa/src/App.css` からの追従コピーが必要な保守対象。`.grade-nav`/`.grade-link`/`.drill-search`/`.custom-generator` は issue #97 で削除済みのため、`App.css` 側に対応クラスが残っていても本ファイルには追従しない。issue #99 で追加した `.hero-*`/`.grade-picker-*`/`.catalog-*`/`.category-*` は `frontend/web` 固有(`frontend/spa` に対応UIなし)のため、同様に追従コピー対象外。
- 旧絞り込みフォーム用の `.drill-filter-bar`/`.format-filter` セレクタは issue #99 で参照元マークアップ(`catalog.html`)を削除したが、本ファイル側のスタイル定義自体は削除していない(削除の要否は範囲外と判断)。

## 変更履歴(git log より自動生成)

- f111bd7 feat(#99): rebuild frontend/web top and catalog screens to match wireframe screens 1-2
- 8007488 #97 frontend/web: rebuild nav shell, design tokens, and remove legacy features (#109)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
