# `frontend/web/src/styles/_navShell.scss`

## 目的・役割

`navShell.js` が描画する共通ナビゲーションシェル(モバイル下部タブバー/PCサイドバー)専用のスタイルパーシャル(issue #97)。

## 動作の概要

- `$breakpoint-desktop: 768px` を境に、`.bottom-tab-bar`(モバイル: `display: flex`、PC: `display: none`)と `.pc-sidebar`(モバイル: `display: none`、PC: `display: flex`、`position: fixed; left: 0`)を切り替える。
- 両ナビとも `position: fixed` のため、ページ本文が隠れないよう `body` 自体に `padding-bottom`(モバイル、bottom-tab-barの高さ分)/`padding-left`(PC、sidebarの幅分)を同じブレークポイントで付与する。`.app-container` 自体は変更していない(body のパディングで押し出す設計)。
- `.nav-item` が共通のリンク/ボタンの見た目(色・カーソル・disabled状態)を定義し、`.tab-item`(縦積みアイコン+ラベル、`flex: 1` で均等幅)と `.sidebar-item`(横並びアイコン+ラベル、ホバー背景・active時の背景色)がそれぞれのレイアウトバリエーションを追加する。

## 重要な設計判断とその理由

### `_base.scss` の新規デザイントークンを利用している理由

`$space-*`/`$radius-*`/`$font-size-*`(`_base.scss` に issue #97 で追加)をこのファイルで使用している。他の既存パーシャル(`_components.scss`/`_layout.scss`)は既存のハードコード値をそのまま残し、このファイル(完全新規のコンポーネント)でのみ新トークンを使い始めている。issue #97 のスコープは「デザイントークンの定義」+「ナビシェルの実装」であり、既存コンテンツの全面的な置き換えは対象外(catalog/preset の中身の再デザインは issue #99/#100)のため。

## 統合ポイント

- 呼び出し元: `main.scss`(`@use 'navShell';`、`base`/`components`/`layout` の後に読み込む)。
- 呼び出し先: `base`(`$color-*`/`$space-*`/`$radius-*`/`$font-size-*` を `@use 'base' as *` で参照)。
- 対象マークアップ: `navShell.js` が生成する `.bottom-tab-bar`/`.pc-sidebar`/`.nav-item`/`.tab-item`/`.sidebar-item`/`.sidebar-brand`。

## 注意事項・既知の制限

- グレード別カード色(`$color-grade-1`〜`6`、`_base.scss` で定義)はこのファイルでは未使用。グレード選択カード自体の再デザイン(issue #99)がこれらのトークンを消費する想定。
