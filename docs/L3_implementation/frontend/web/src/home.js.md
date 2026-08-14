# `frontend/web/src/home.js`

## 目的・役割

`index.html`(トップ画面)のページエントリ。issue #99 で `docs/uiux/wireframe_v1.png` の画面①(学年選択トップ)に合わせて全面書き換えし、`mountNavShell()` を呼ぶだけの薄いエントリになった。

## 動作の概要

- モジュール読み込み時に `mountNavShell()`(issue #97 で追加)を呼び、モバイル下部タブバー/PCサイドバーを描画する。
- 続けて `mountPcMakeFlow(document.getElementById('pcMakeFlow'))`(issue #101 で追加)を呼び、PC(≥768px)向け4カラムレイアウトをマウントする。`#pcMakeFlow` は `index.html` に追加した空の `<div>` で、モバイル幅では CSS(`_pcMakeFlow.scss`)により非表示。
- `document.getElementById('appHeader').innerHTML` に `ICONS.brand` + `t('nav_brand')`(「計算ドリル」)を書き込み、`index.html` の空の `<header id="appHeader">` にブランド見出し(`<h1 class="app-header-brand">`)を描画する(issue #126)。`_pcMakeFlow.scss` がデスクトップ幅で `.app-header` を非表示にするため、実質モバイル幅でのみ見える。
- `document.querySelectorAll('.grade-picker-card')` の各カードへ、`ICONS.face` を包んだ `<span class="grade-picker-avatar" aria-hidden="true">` を `insertAdjacentHTML('afterbegin', ...)` で先頭挿入する(issue #126、wireframe の学年カードアバターに対応)。
- ヒーローコピー(「毎日の計算練習をすぐにプリント」等)と学年カラーの2×3学年カードグリッド(`catalog.html?grade=N` への静的リンク、モバイル専用)は `index.html` に直接ハードコードしており、カードのDOM構造自体はJSが関与しない(アイコン注入のみJS側)。

## 重要な設計判断とその理由

### 「出題形式・目的で選ぶ」セクション(旧 `renderAvailableForms`)を削除した理由

issue #98 で `DRILL_FORMS`(`drillCatalog.js`)が常に空配列を返すようになったため、#98 以降このセクションは常に非表示の死んだコードになっていた(`docs/L3_implementation/frontend/web/src/drillCatalog.js.md` 参照)。issue #99 のトップ画面書き換えでこの死んだコードとそれが依存していた `buildDrillCatalog`/`DRILL_FORMS`/`UNGRADED`/`renderer-info` fetch を丸ごと削除した。

### ホーム画面の大部分を静的HTMLにした理由(issue #88 以来変更なし)

`frontend/web` は SPA ではなく画面ごとに実在の `.html` を用意する構成のため、学年カードのリンク先(`catalog.html?grade=1`〜`6`)のように実行時に変わらない固定選択肢は `index.html` に直接 `<a href>` として書いている。

## 統合ポイント

- 呼び出し元: `index.html` の `<script type="module" src="/src/home.js">`。
- 呼び出し先: `navShell.js`(`mountNavShell`)、`pcMakeFlow.js`(`mountPcMakeFlow`、issue #101 で追加)、`strings.js`(`t`)、`icons.js`(`ICONS`、issue #126 でブランドヘッダー/学年カードアイコン注入のため復活)。`drillCatalog.js`/`drillPresets.js`/`backend` への直接依存は issue #99 で撤去したまま(`pcMakeFlow.js` 経由での間接依存のみ issue #101 で復活している)。

## 注意事項・既知の制限

- 検索フォーム(issue #97 で削除済み)、数の種類/学年テキストリンクの3セクション構成・出題形式セクション(issue #99 で削除)はいずれも過去のUIであり、現在は存在しない。
- `index.html` は元々静的な `<header class="app-header"><h1>100マス計算ジェネレーター</h1></header>` を持っていたが、`catalog.html`/`preset.html` 側の同名ヘッダーが各ページの動的見出しと重複していた(issue #126)ため、`index.html` 側も空の `<header id="appHeader">` に置き換えて JS 側でブランド表示に差し替えた。`catalog.html`/`preset.html` は静的ヘッダー自体を削除し、`catalog.js`/`presetDetail.js` が描画する `<header>` に一本化している([[./catalog.js]]/[[./presetDetail.js]] 参照)。

## 変更履歴(git log より自動生成)

- ab9fe98 feat(#126): add missing wireframe icons and unify page headers in frontend/web
- 77f95b7 #101 frontend/web: add PC 4-column layout to the make flow (#119)
- 1bd6fa6 #99 Rebuild frontend/web top and catalog screens to match wireframe screens 1-2 (#116)
- 8007488 #97 frontend/web: rebuild nav shell, design tokens, and remove legacy features (#109)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
