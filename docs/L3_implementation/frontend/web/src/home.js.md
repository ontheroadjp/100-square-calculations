# `frontend/web/src/home.js`

## 目的・役割

`index.html`(ホーム画面)のページエントリ。`frontend/spa` の `GradeDrills` コンポーネントのホーム状態(`route === 'home'`)に相当するが、`frontend/web` は複数ページ構成(issue #88)のため、ホーム画面のほとんどは `index.html` 内に静的マークアップとして直接書かれている。本ファイルが JS で担うのは「出題形式・目的で選ぶ」セクションのみ。

## 動作の概要

- `renderAvailableForms()`: `GET /renderer-info` を fetch して `activeRenderer` を確定し、`buildDrillCatalog(activeRenderer)` からその時点で1件以上ドリルが存在する `DRILL_FORMS` だけを抽出して `#formStartGrid` にリンク(`<a href="catalog.html?forms=...">`)として描画する。該当なしの場合はセクション自体(`#formSection`)を非表示のままにする。
- 「数の種類から選ぶ」「学年から選ぶ」の2セクションはレンダラーに依存しない固定リンクのため、`index.html` に直接ハードコードされておりJSは関与しない。

## 重要な設計判断とその理由

### ホーム画面の大部分を静的HTMLにした理由

ユーザーからの明示的な指示により、`frontend/web` は SPA(JSが `innerHTML` を書き換えて画面遷移を模倣する構成)ではなく、画面ごとに実在の `.html` を用意する構成にした(issue #88)。ホーム画面のリンク先の大半(数の種類・学年)は実行時に変わらない固定選択肢のため、JSでの動的生成を避けそのまま `<a href>` として `index.html` に書いている。「出題形式」だけはバックエンドのレンダラー設定(`reportlab`/`latex`)によって選択肢が変わりうるため、この部分だけ実行時にJSで組み立てている。

## 統合ポイント

- 呼び出し元: `index.html` の `<script type="module" src="/src/home.js">`。
- 呼び出し先: `strings.js`(`t`)、`drillCatalog.js`(`buildDrillCatalog`/`DRILL_FORMS`)、`backend`(`GET /renderer-info`)。

## 注意事項・既知の制限

- 検索フォーム(`<form method="get" action="catalog.html">`)も `index.html` に静的に書かれており、送信は通常のブラウザGETナビゲーションに任せている(JSによる `preventDefault`/フェッチは行わない)。
