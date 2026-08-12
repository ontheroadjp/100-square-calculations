# `frontend/web/src/catalog.js`

## 目的・役割

`catalog.html`(ドリルカタログ・検索/絞り込み画面)のページエントリ。`frontend/spa/src/GradeDrills.jsx` のカタログ表示ロジック([[../../frontend/spa/src/GradeDrills.jsx]] 参照)を、React の内部 state ではなく URL のクエリ文字列を状態源として vanilla JS に移植したもの。

## 動作の概要

- `render()`: `location.search` を `URLSearchParams` でパースし(`q`/`numberType`/`grade`/`level`/`forms`)、`catalog.html` に静的配置された検索・絞り込みフォーム(`<select name="numberType">` 等)の初期値をその値に合わせる。`GET /renderer-info` を fetch して `activeRenderer` を確定し、`buildDrillCatalog`/`filterDrillCatalog`([[./drillCatalog.js]] 参照)でカタログと絞り込み結果を計算し、`#results` に描画する。
- `numberType` が指定されていて検索語が空の場合(`inNumberTypeView`)は数の種類別ビュー(`numberTypeCatalogHtml`。演算グループごとのセクション分け+`問題の形式`絞り込みチェックボックス)を、それ以外は単純なカードグリッド(`drillGridHtml`)を描画する。`frontend/spa` 版の同名分岐と同じ判定条件。
- `drillCardHtml`: ドリルカードの学年・レベルバッジ、生成ボタンを `<a href="...">` として描画する。学年/レベルバッジのリンク先(`catalogHref`)は、数の種類別ビュー内かどうかで `numberType`/`forms` を保持するかを切り替える(`frontend/spa` 版の `onSelectGrade`/`onSelectLevel` と同じ分岐)。生成ボタンは `preset.html?grade=<grade>&drillId=<id>&format=<format>` へのリンクになる。

## 重要な設計判断とその理由

### 状態を URL クエリ文字列だけで表現している理由

`frontend/web` は SPA ではなく複数ページ構成(issue #88、ユーザー要望)のため、`catalog.html` はページ単体で「今どの絞り込み条件が選ばれているか」を再現できる必要がある。JS のメモリ内 state に頼ると、ブラウザの戻る/進む・リロード・URL共有のたびに状態が失われるため、`frontend/spa` 版の `state`(React の `useState`)に相当する情報をすべて URL クエリ文字列に載せている。絞り込みフォームは `<form method="get">` のネイティブ送信に任せており、`submit` イベントを JS で横取りしない。

### 検索ボックスがキー入力ごとに絞り込まない理由

`frontend/spa`/旧 `frontend/web`(SPA版)では検索欄への1文字入力ごとに即座に再描画・絞り込みしていたが、本ページでは検索欄はフォームの一部であり、送信(Enterキーまたは「絞り込む」ボタン)しない限り `catalog.html` への実ナビゲーションは発生しない。これは静的ページ構成を選んだことの直接的なトレードオフで、JSによる `input` イベント監視・即時 fetch は行わない設計にしている。

## 統合ポイント

- 呼び出し元: `catalog.html` の `<script type="module" src="/src/catalog.js">`。
- 呼び出し先: `strings.js`(`t`)、`drillPresets.js`(`GRADES`/`UNGRADED`)、`drillCatalog.js`(カタログ構築・絞り込み)、`backend`(`GET /renderer-info`)。ドリルカードのリンク遷移先は `preset.html`(ブラウザナビゲーションのみ、JSからは呼ばない)。

## 注意事項・既知の制限

- 「問題の形式」絞り込みチェックボックス(`INTEGER_FORMAT_FILTERS`)は `numberType=integers` かつ検索語なしのときのみ表示する(`frontend/spa` 版と同じ条件)。フォーム内に動的に注入する構造のため、`catalog.html` 側は空の `<fieldset id="formatFilter" hidden>` を用意しておき、JS が中身と `hidden` 属性を制御する。
