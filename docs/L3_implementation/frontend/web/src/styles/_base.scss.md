# `frontend/web/src/styles/_base.scss`

## 目的・役割

`$color-*` 変数群と、リセット/`body`/`.app-container`/`.app-header`/`.main-content` のスタイルを定義するパーシャル。詳細な分割方針は [[./main.scss]] を参照。

## 動作の概要

かつて併存していた `frontend/spa/src/App.css`(`frontend/spa` 自体は issue #233 で削除)の該当セクション(Basic Reset、App Container、Header、Main Content Area)をそのまま Sass 化し、繰り返し使う色(`#333`/`#6b7280`/`#2563eb` 等)を `$color-text`/`$color-text-muted`/`$color-primary` 等の変数に置き換えている。メディアクエリはネストして各セレクタの直下に記述している(元の CSS はセレクタごとに別ブロックだった)。

issue #97 で `docs/uiux/wireframe_v1.png` に基づくデザイントークンを追加した: `$color-grade-1`〜`$color-grade-6`(学年別カード色)、`$space-xs`〜`$space-xl`(spacing scale)、`$radius-sm`/`$radius-md`/`$radius-pill`、`$font-size-sm`〜`$font-size-xl`。`$radius-xs`(`.drill-badge` 等が利用)は以降に追加された。

issue #101 で `body` に `box-sizing: border-box` を追加した(下記「重要な設計判断」参照)。

issue #132 で、`$color-grade-1`〜`6` を CSS カスタムプロパティ `--color-primary`/`--color-primary-hover` にマップする `.grade-1`〜`.grade-6` の `@each` ループを追加した(`frontend/web/src/styles/_base.scss:30-49` あたり)。元は issue #130 で `_catalog.scss` にのみ定義されていたが、`main.scss` が全ページの Sass を1本の CSS にバンドルする性質上、複数ページ(`catalog.js`/`presetDetail.js` の両方が自身のコンテナへ `.grade-N` を付与する)が同じマップを必要とするようになったため、ここへ集約した。`--color-primary-hover` は学年別の専用トーンを持たず `--color-primary` と同じ値を使う(`_catalog.scss.md` の「重要な設計判断」参照)。

## 重要な設計判断とその理由

### `body` に `box-sizing: border-box` を追加した理由(issue #101)

`_navShell.scss`(issue #97)は PC 幅で `body` に `padding-left: $nav-sidebar-width`(固定サイドバー分)を付与する。`body` が `box-sizing: border-box` を持たない(デフォルトの `content-box`)場合、`width: 100%` はコンテンツ幅のみを指定するため、そこに `padding-left` が加算され、`body` の実際の描画幅がビューポート幅+サイドバー幅まで膨張する。この状態でページ全体を横スクロールすると、`position: fixed` の `.pc-sidebar` まで一緒にずれてしまう(fixed 要素は initial containing block を基準にするため、ドキュメント自体が横スクロール可能になるとその影響を受ける)。issue #101 で PC 4カラムレイアウト(`pcMakeFlow.js`/`_pcMakeFlow.scss`)を実装した際、狭いウィンドウでこの潜在バグが実際にサイドバーのずれとして顕在化したため発見・修正した。`catalog.html`/`preset.html` を含む3ページ共通の `body` ルールであり、修正はグローバルに適用される(従来はコンテンツ幅が `max-width: 960px` に収まっていたため顕在化していなかった)。

## 統合ポイント

- 呼び出し元: `main.scss`(`@use 'base'`)、`_components.scss`/`_layout.scss`(`@use 'base' as *` で `$color-*` 変数を参照)。
- 呼び出し先: なし。

## 注意事項・既知の制限

- [[./main.scss]] と同じく、かつて併存していた `frontend/spa/src/App.css` からの追従コピーが必要な保守対象だった(`frontend/spa` 自体は issue #233 で削除され、以後追従コピー元は存在しない)。
- issue #97 で追加した `$color-grade-*` は issue #132 以降、本ファイル内の `.grade-N` ルールが直接消費する(上記参照)。`[[./navShell.scss]]` が `$space-*`/`$radius-*`/`$font-size-*` を消費している。

## 変更履歴(git log より自動生成)

- 7b5a9b9 feat(#132): add per-grade accent, KaTeX examples, generalized setting hints, and move problem count into common settings on preset detail page
- d43d1bc #130 frontend/web: make catalog page accent color switch dynamically per grade (#131)
- 1bb0f69 #126 frontend/web: add missing wireframe icons and unify page headers (#127)
- 77f95b7 #101 frontend/web: add PC 4-column layout to the make flow (#119)
- 8007488 #97 frontend/web: rebuild nav shell, design tokens, and remove legacy features (#109)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
