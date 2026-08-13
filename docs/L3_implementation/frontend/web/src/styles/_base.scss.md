# `frontend/web/src/styles/_base.scss`

## 目的・役割

`$color-*` 変数群と、リセット/`body`/`.app-container`/`.app-header`/`.main-content` のスタイルを定義するパーシャル。詳細な分割方針は [[./main.scss]] を参照。

## 動作の概要

`App.css`([[../../../../frontend/spa/src/App.css]] 参照)の該当セクション(Basic Reset、App Container、Header、Main Content Area)をそのまま Sass 化し、繰り返し使う色(`#333`/`#6b7280`/`#2563eb` 等)を `$color-text`/`$color-text-muted`/`$color-primary` 等の変数に置き換えている。メディアクエリはネストして各セレクタの直下に記述している(元の CSS はセレクタごとに別ブロックだった)。

issue #97 で `docs/uiux/wireframe_v1.png` に基づくデザイントークンを追加した: `$color-grade-1`〜`$color-grade-6`(学年別カード色)、`$space-xs`〜`$space-xl`(spacing scale)、`$radius-sm`/`$radius-md`/`$radius-pill`、`$font-size-sm`〜`$font-size-xl`。

## 統合ポイント

- 呼び出し元: `main.scss`(`@use 'base'`)、`_components.scss`/`_layout.scss`(`@use 'base' as *` で `$color-*` 変数を参照)。
- 呼び出し先: なし。

## 注意事項・既知の制限

- [[./main.scss]] と同じく、`frontend/spa/src/App.css` からの追従コピーが必要な保守対象。
- issue #97 で追加した `$color-grade-*` は本ファイル内では未使用(グレード選択カード自体の再デザインは issue #99 のスコープ)。`[[./navShell.scss]]` が `$space-*`/`$radius-*`/`$font-size-*` を消費している。
