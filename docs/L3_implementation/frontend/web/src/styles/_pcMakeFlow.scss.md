# `frontend/web/src/styles/_pcMakeFlow.scss`

## 目的・役割

`pcMakeFlow.js` が描画する PC(≥768px)向け4カラムレイアウトのスタイルパーシャル(issue #101、`docs/uiux/wireframe_v1.png` の「PC版レイアウトイメージ」)。`index.html` のみが対象で、`catalog.html`/`preset.html` には影響しない。

## 動作の概要

- `$breakpoint-desktop: 768px` は [[./_navShell.scss]] の同名変数と同じ値(独立した変数、値だけ揃えている)。`.app-container.pc-flow-page`(`index.html` にのみ付与されるページ識別クラス)配下で、このブレークポイント以上のとき `.app-header`/`.grade-drills`(モバイル用グレードピッカー)を非表示にし、`.pc-make-flow` を表示に切り替える。
- `.pc-flow-columns` は4カラムの CSS Grid(`minmax(160px,1fr) minmax(280px,1.4fr) minmax(280px,1.4fr) minmax(240px,1.2fr)`)。各カラムに実用上の最小幅を与えたうえで `overflow-x: auto` を持たせ、ウィンドウが狭い場合はこのグリッド内だけで横スクロールさせる。
- `.pc-flow-column` は `height: calc(100vh - $topbar-height)` + `overflow-y: auto` で、カラムごとに独立して縦スクロールする(4カラムが同じ高さを保ったまま、それぞれの中身の量に応じて個別にスクロール)。

## 重要な設計判断とその理由

### `.pc-flow-columns` に `overflow-x: auto` を持たせた理由(ドキュメント全体を横スクロールさせない)

実装時に、`body`(`_navShell.scss` がPC幅で `padding-left: $nav-sidebar-width` を付与)に `box-sizing: border-box` が無かったため、`padding-left` 分だけドキュメント全体の描画幅がビューポート幅を超え、その状態でユーザーがページ全体を横スクロールすると `position: fixed` の `.pc-sidebar`(`_navShell.scss`)まで一緒にずれるという既存の潜在バグ([[./_base.scss]] で `box-sizing: border-box` を追加して修正、3ページ共通)を誘発することが分かった。合わせて、4カラムの合計最小幅がビューポート幅を超えた場合にドキュメント自体が横に伸びるのではなく `.pc-flow-columns` の内部だけがスクロールするよう、明示的な `min-width` 付き `minmax()` と `overflow-x: auto` をこのグリッドに持たせている。

### カラムの最小幅を `minmax()` で保証した理由

`grid-template-columns` を単純な `fr` 比率だけにすると、極端に狭いビューポートでカラムがテキストやカードを表示できないほど潰れてしまう(内部の `.drill-list-card`/PDF iframe 等は実用上の最小幅を必要とする)。`minmax(min, fr)` で最小幅を保証し、それを下回る場合はグリッド自体が横スクロール可能領域としてはみ出す設計にした。

## 統合ポイント

- 呼び出し元: `main.scss`(`@use 'pcMakeFlow';`、既存4パーシャルの後に追加)。
- 呼び出し先: `base`(`$color-*`/`$space-*`/`$radius-*`/`$font-size-*` を `@use 'base' as *` で参照)。
- 対象マークアップ: `pcMakeFlow.js` が生成する `.pc-make-flow`/`.pc-flow-topbar`/`.pc-flow-columns`/`.pc-flow-column`/`.pc-grade-list*`/`.pc-drill-list-card`/`.pc-settings-panel`/`.pc-preview-iframe-container`。設定フォーム部分の見た目(`.segmented-control`/`.disclosure`/`.toggle-switch`/`.create-pdf-button` 等)は `_components.scss` を共用しており、このファイルでは再定義していない。
- `index.html` の `.app-container` に付与された `pc-flow-page` クラス経由でのみ効果を持つ(`catalog.html`/`preset.html` の `.app-container` にはこのクラスが無いため無関係)。

## 注意事項・既知の制限

- 右上のユーザー名/プレミアム会員バッジ用に `.pc-flow-topbar-actions` という空の枠だけ確保しており、中身のスタイルは未定義(機能自体が未実装のため、[[../pcMakeFlow.js]] 参照)。
- `.pc-preview-iframe-container { height: 65vh; }` は固定のビューポート比率で、他カラムの実際の残り高さと厳密には連動していない(`calc()` で全カラム共通の `$topbar-height` を引く方式は採用したが、iframe だけをさらに厳密なピクセル計算にすると overflow 計算が複雑になるため、実機確認で違和感のない `vh` 値に留めた)。

## 変更履歴(git log より自動生成)

- d9599eb feat(#101): add PC 4-column layout to frontend/web's make flow
