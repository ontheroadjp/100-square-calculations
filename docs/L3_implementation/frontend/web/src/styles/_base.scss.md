# `frontend/web/src/styles/_base.scss`

## 目的・役割

`$color-*` 変数群と、リセット/`body`/`.app-container`/`.app-header`/`.main-content` のスタイルを定義するパーシャル。詳細な分割方針は [[./main.scss]] を参照。

## 動作の概要

`App.css`([[../../../../frontend/spa/src/App.css]] 参照)の該当セクション(Basic Reset、App Container、Header、Main Content Area)をそのまま Sass 化し、繰り返し使う色(`#333`/`#6b7280`/`#2563eb` 等)を `$color-text`/`$color-text-muted`/`$color-primary` 等の変数に置き換えている。メディアクエリはネストして各セレクタの直下に記述している(元の CSS はセレクタごとに別ブロックだった)。

issue #97 で `docs/uiux/wireframe_v1.png` に基づくデザイントークンを追加した: `$color-grade-1`〜`$color-grade-6`(学年別カード色)、`$space-xs`〜`$space-xl`(spacing scale)、`$radius-sm`/`$radius-md`/`$radius-pill`、`$font-size-sm`〜`$font-size-xl`。

issue #101 で `body` に `box-sizing: border-box` を追加した(下記「重要な設計判断」参照)。

## 重要な設計判断とその理由

### `body` に `box-sizing: border-box` を追加した理由(issue #101)

`_navShell.scss`(issue #97)は PC 幅で `body` に `padding-left: $nav-sidebar-width`(固定サイドバー分)を付与する。`body` が `box-sizing: border-box` を持たない(デフォルトの `content-box`)場合、`width: 100%` はコンテンツ幅のみを指定するため、そこに `padding-left` が加算され、`body` の実際の描画幅がビューポート幅+サイドバー幅まで膨張する。この状態でページ全体を横スクロールすると、`position: fixed` の `.pc-sidebar` まで一緒にずれてしまう(fixed 要素は initial containing block を基準にするため、ドキュメント自体が横スクロール可能になるとその影響を受ける)。issue #101 で PC 4カラムレイアウト(`pcMakeFlow.js`/`_pcMakeFlow.scss`)を実装した際、狭いウィンドウでこの潜在バグが実際にサイドバーのずれとして顕在化したため発見・修正した。`catalog.html`/`preset.html` を含む3ページ共通の `body` ルールであり、修正はグローバルに適用される(従来はコンテンツ幅が `max-width: 960px` に収まっていたため顕在化していなかった)。

## 統合ポイント

- 呼び出し元: `main.scss`(`@use 'base'`)、`_components.scss`/`_layout.scss`(`@use 'base' as *` で `$color-*` 変数を参照)。
- 呼び出し先: なし。

## 注意事項・既知の制限

- [[./main.scss]] と同じく、`frontend/spa/src/App.css` からの追従コピーが必要な保守対象。
- issue #97 で追加した `$color-grade-*` は本ファイル内では未使用(グレード選択カード自体の再デザインは issue #99 のスコープ)。`[[./navShell.scss]]` が `$space-*`/`$radius-*`/`$font-size-*` を消費している。

## 変更履歴(git log より自動生成)

- fix(#101): add box-sizing: border-box to body to prevent document overflow with the PC sidebar(このタスクでの変更。コミットハッシュは /docs-sync 実行時に確定)
- b11ac96 feat(#97): rebuild frontend/web nav shell and design tokens, remove custom generator/search/ungraded UI
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
