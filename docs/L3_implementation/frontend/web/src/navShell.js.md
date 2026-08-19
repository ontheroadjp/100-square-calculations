# `frontend/web/src/navShell.js`

## 目的・役割

`index.html`/`catalog.html`/`preset.html` の3ページ共通のナビゲーションシェル(issue #97)。モバイルの下部固定タブバーと、PCの左固定サイドバーを描画する。旧 `<nav class="grade-nav">`(「ドリルを探す」/「カスタム」の2リンクバー、`custom.html` 削除に伴い廃止)を置き換える。

## 動作の概要

- `mountNavShell()`: `<nav class="bottom-tab-bar">` と `<nav class="pc-sidebar">` の2つの `<nav>` 要素を生成し、`document.body` の先頭(sidebar)と末尾(bottom bar)にそれぞれ挿入する。表示切り替えは `_navShell.scss` の `@media (min-width: 768px)` に委ねる(モバイル: bottom-tab-bar 表示・pc-sidebar 非表示、PC: 逆)。
- `MOBILE_TABS`(4項目: ホーム/作る/履歴/マイページ)と `SIDEBAR_ITEMS`(5項目: 上記+お気に入り)は `docs/uiux/wireframe_v1.png` のモバイル/PC で項目数が異なる実態(issue本文が挙げる5項目とは不一致、#97実装時にwireframe画像を優先すると確認済み)にそのまま合わせている。
- 各項目は `item.href` の有無で描画を切り替える: `href` があれば `<a>`(有効)、なければ `<button disabled>`(非活性)。「履歴」「お気に入り」「マイページ」は対応するページが未実装のため全て非活性。
- アイコンは `ICONS` オブジェクトに手書きの inline SVG(stroke ベース)として定義。新規アイコンライブラリは追加していない(`frontend/web` の「React・i18nライブラリ非依存」という既存方針に合わせた)。

## 重要な設計判断とその理由

### 「ホーム」と「作る」が両方とも `index.html` に遷移し、「作る」だけを active にしている理由

wireframe の「リピーターのホーム画面」(2回目以降の訪問者向け画面)はまだ実装されていない。現状の3ページ(index/catalog/preset)は全て wireframe の「モバイル: メインフロー」(①トップ〜⑤PDFプレビュー)に属するため、この3ページでは常に「作る」を active として扱う。「ホーム」は将来のリピーター向けホーム画面が実装されるまでは「作る」と同じ遷移先を持つプレースホルダーとして機能する。

### `document.body` に直接 `prepend`/`append` する設計にした理由

各 HTML ファイルにマウント用の `<div>` を用意せず、`navShell.js` 側で `document.body` に直接ノードを追加する設計にした。これにより3ページとも `import { mountNavShell } from './navShell.js'; mountNavShell();` の2行を追加するだけで組み込め、HTML側の変更を最小化できる。`.bottom-tab-bar`/`.pc-sidebar` は `position: fixed` のため、body に直接追加してもレイアウトへの影響は `_navShell.scss` 側の `body` パディング調整のみで完結する。

## 統合ポイント

- 呼び出し元: `home.js`/`catalog.js`/`preset.js`(いずれもエントリ先頭付近で `mountNavShell()` を呼ぶ)。
- 呼び出し先: `strings.js`(`t`、ナビラベルの翻訳)。
- スタイル: `styles/_navShell.scss`(`.bottom-tab-bar`/`.pc-sidebar`/`.nav-item`/`.tab-item`/`.sidebar-item`/`.sidebar-brand` を定義)。

## 注意事項・既知の制限

- アクティブタブは常に「作る」固定で、引数によるアクティブタブ切り替えは実装していない(現状3ページとも同じ扱いのため、YAGNI により未対応)。将来リピーター向けホーム画面(issue #90 の後続issue)が追加された際に、`mountNavShell(activeTab)` のような形でパラメータ化が必要になる可能性がある。
- `custom.html` 削除に伴い `CUSTOM_GRADE`(`drillPresets.js`)は `frontend/web` 側で完全に未使用になったが、かつて併存していた `frontend/spa` との共有コピーだったため削除していなかった([[./drillPresets.js]] 参照。`frontend/spa` 自体は issue #233 で削除済み)。

## 変更履歴(git log より自動生成)

- b11ac96 feat(#97): rebuild frontend/web nav shell and design tokens, remove custom generator/search/ungraded UI
