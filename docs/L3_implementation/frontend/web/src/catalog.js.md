# `frontend/web/src/catalog.js`

## 目的・役割

`catalog.html`(ドリルカタログ・絞り込み画面。検索UIは issue #97 で撤去済み)のページエントリ。`frontend/spa/src/GradeDrills.jsx` のカタログ表示ロジック([[../../frontend/spa/src/GradeDrills.jsx]] 参照)を、React の内部 state ではなく URL のクエリ文字列を状態源として vanilla JS に移植したもの。

## 動作の概要

- モジュール読み込み時に `mountNavShell()`(issue #97 で追加)を呼ぶ。
- `render()`: `location.search` を `URLSearchParams` でパースし(`numberType`/`grade`/`level`/`forms`。検索語 `q` は issue #97 で検索UI自体を撤去したため扱わない)、`catalog.html` に静的配置された絞り込みフォーム(`<select name="numberType">` 等)の初期値をその値に合わせる。`GET /renderer-info` を fetch して `activeRenderer` を確定し、`buildDrillCatalog` の結果から `UNGRADED` 学年のエントリを除外したうえで `filterDrillCatalog`([[./drillCatalog.js]] 参照)で絞り込み結果を計算し、`#results` に描画する。
- `numberType` が指定されている場合(`inNumberTypeView`。検索UI撤去に伴い issue #97 で `numberType` の有無だけの判定に単純化)は数の種類別ビュー(`numberTypeCatalogHtml`。演算グループごとのセクション分け+`問題の形式`絞り込みチェックボックス)を、それ以外は単純なカードグリッド(`drillGridHtml`)を描画する。
- `drillCardHtml`: ドリルカードの学年・レベルバッジ、生成ボタンを `<a href="...">` として描画する。学年/レベルバッジのリンク先(`catalogHref`)は、数の種類別ビュー内かどうかで `numberType`/`forms` を保持するかを切り替える(`frontend/spa` 版の `onSelectGrade`/`onSelectLevel` と同じ分岐)。生成ボタンは `preset.html?grade=<grade>&drillId=<id>&format=<format>` へのリンクになる。

## 重要な設計判断とその理由

### 状態を URL クエリ文字列だけで表現している理由

`frontend/web` は SPA ではなく複数ページ構成(issue #88、ユーザー要望)のため、`catalog.html` はページ単体で「今どの絞り込み条件が選ばれているか」を再現できる必要がある。JS のメモリ内 state に頼ると、ブラウザの戻る/進む・リロード・URL共有のたびに状態が失われるため、`frontend/spa` 版の `state`(React の `useState`)に相当する情報をすべて URL クエリ文字列に載せている。絞り込みフォームは `<form method="get">` のネイティブ送信に任せており、`submit` イベントを JS で横取りしない。

### 無学年ドリルをカタログ構築直後に除外している理由

`buildDrillCatalog` は `drillCatalog.js`([[./drillCatalog.js]] 参照)側で常に `UNGRADED` 学年のプリセットを含めて返す(`frontend/spa` と共有する実装のため変更していない)。issue #97 で無学年ドリルへのUI導線(`catalog.html` の `grade=ungraded` option、`index.html` の「無学年」リンク)を撤去したのに合わせ、`catalog.js` 側で `buildDrillCatalog(...).filter((drill) => drill.grade !== UNGRADED)` として一律除外することで、`grade` フィルタ未指定時の一覧・数の種類別ビューのいずれにも無学年ドリルが現れないようにしている。

## 統合ポイント

- 呼び出し元: `catalog.html` の `<script type="module" src="/src/catalog.js">`。
- 呼び出し先: `strings.js`(`t`)、`drillPresets.js`(`UNGRADED`)、`drillCatalog.js`(カタログ構築・絞り込み)、`navShell.js`(`mountNavShell`、issue #97 で追加)、`backend`(`GET /renderer-info`)。ドリルカードのリンク遷移先は `preset.html`(ブラウザナビゲーションのみ、JSからは呼ばない)。

## 注意事項・既知の制限

- 「問題の形式」絞り込みチェックボックス(`INTEGER_FORMAT_FILTERS`)は `numberType=integers` のときのみ表示する(検索語による分岐は issue #97 で検索UIごと撤去)。フォーム内に動的に注入する構造のため、`catalog.html` 側は空の `<fieldset id="formatFilter" hidden>` を用意しておき、JS が中身と `hidden` 属性を制御する。
