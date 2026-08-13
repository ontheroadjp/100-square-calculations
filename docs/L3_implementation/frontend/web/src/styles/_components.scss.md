# `frontend/web/src/styles/_components.scss`

## 目的・役割

フォーム部品・カード・バッジなど、複数画面(ドリルカタログ/プリセット詳細)で共通して使う見た目のパーツを定義するパーシャル。詳細な分割方針は [[./main.scss]] を参照。

## 動作の概要

`App.css`([[../../../../frontend/spa/src/App.css]] 参照)のうち、`.form-group`/`.preset-card*`/`.drill-badge*`/`.preset-download-button`/`.pdf-iframe*`/`.regenerate-button`/`.back-button` 等のセレクタを移植している。`$color-*` 変数は `_base.scss` から `@use 'base' as *` で参照する。

issue #97 で `custom.html`/`src/customGenerator.js` を削除した際、それらだけが使っていた `.form-layout`/`.form-grid`/`.checkbox-group`/`.checkbox-grid`/`.required-text`/`.optional-text`/`.submit-button-container`/`.submit-button`/`.tab-nav`/`.tab-pane`/`.no-pdf-message`/`.result-display`/`.download-button`/`.error-message` を削除した(他ファイルでの参照がないことを `grep` で確認済み)。

issue #99 で `catalog.js` の学年別カテゴリ画面用に以下を追加した:
- `.badge-basic`/`.badge-standard`(`item.difficultyKey` に対応する基礎/標準バッジの配色。`difficulty_basic_standard` は `.badge-standard` を流用)
- `.drill-list-card`/`.drill-list-card-heading`/`.drill-list-card-title`/`.drill-list-card-example`(カテゴリ内のドリルカード。カード全体が `<a>` のクリッカブル領域)

issue #100 で `presetDetail.js`([[../presetDetail.js]] 参照)の設定/完了/プレビュー3画面用に以下を追加した:
- `.preset-detail-settings`/`.preset-detail-done`/`.preset-detail-preview`(各画面のルート。`display: flex; flex-direction: column`)
- `.example-chip-row`/`.example-chip`(例題チップ)、`.support-level-note`(`partial`/`none` サポートレベルの注記)
- `.setting-block`/`.setting-label`/`.setting-fixed-value`/`.setting-hint`、`.segmented-control`/`.segmented-option`(問題数・ドリル固有設定の segmented control。choice/fixed 共通の見た目)
- `.disclosure`/`.disclosure-toggle`/`.disclosure-chevron`/`.disclosure-body`(「詳細設定(共通設定)」開閉)
- `.toggle-row`/`.toggle-label`/`.toggle-switch`/`.toggle-switch-thumb`(「名前をつける」トグルスイッチ)
- `.create-pdf-button`(「PDFを作成する」プライマリボタン)
- `.completion-visual`/`.completion-check`/`.confetti-dot-1`〜`-6`/`.completion-heading`/`.completion-summary`/`.completion-thumbnail`/`.completion-actions`/`.completion-secondary-button`(完了画面。confettiは静的CSS装飾、サムネイルは実PDFレンダリングではない簡易プレースホルダー)
- `.preview-header`/`.preview-iframe-container`(プレビュー画面。ズームUI等は自前実装せずブラウザ内蔵PDFビューアに委ねる)

これに伴い `_layout.scss`([[./_layout.scss]] 参照)にあった旧単一画面版の `.preset-detail`/`.preset-detail-title`/`.preset-detail-status`/`.preset-detail-settings`/`.preset-detail-actions` を削除した。特に旧 `.preset-detail-settings`(`display: grid` の項目グリッド)は本ファイルの新 `.preset-detail-settings`(画面ルートの `flex-column`)とクラス名が衝突し、`main.scss` の `@use` 順(`components` の後に `layout`)により後勝ちで新スタイルを上書きしてレイアウトが崩れる実機バグを引き起こしたため、削除は必須の修正だった。

## 統合ポイント

- 呼び出し元: `main.scss`(`@use 'components'`)。
- 呼び出し先: `_base.scss`(色変数)。

## 注意事項・既知の制限

- [[./main.scss]] と同じく、`frontend/spa/src/App.css` からの追従コピーが必要な保守対象。`customGenerator.js` 専用だった上記クラスは issue #97 で削除済みのため、`App.css` 側に対応クラスが残っていても本ファイルには追従しない。issue #99 で追加した `.badge-basic`/`.badge-standard`/`.drill-list-card*` は `frontend/web` 固有(`frontend/spa` に対応UIなし)のため、同様に追従コピー対象外。
- 旧絞り込みグリッド用の `.drill-start-card`/`.filter-reset`/`.format-filter` セレクタ、旧カタロググリッド用の `.preset-card`/`.preset-card-grid`/`.preset-card-title`/`.preset-card-desc`/`.level-badge` セレクタは issue #99 で `index.html`/`catalog.html` からの参照元マークアップを削除し、現在参照元がない(`.preset-card-error` は `presetDetail.js` が引き続き使用、`.drill-badge` は `catalog.js` の新バッジ実装が基底クラスとして引き続き使用)。スタイル定義自体は削除していない(削除の要否は範囲外と判断)。

## 変更履歴(git log より自動生成)

- f111bd7 feat(#99): rebuild frontend/web top and catalog screens to match wireframe screens 1-2
- 8007488 #97 frontend/web: rebuild nav shell, design tokens, and remove legacy features (#109)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
