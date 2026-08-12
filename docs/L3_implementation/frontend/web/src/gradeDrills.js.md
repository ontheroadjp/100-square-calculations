# `frontend/web/src/gradeDrills.js`

## 目的・役割

`frontend/spa/src/GradeDrills.jsx`([[../../frontend/spa/src/GradeDrills.jsx]] 参照)を vanilla JS に移植したモジュール。学年別ドリルカタログのホーム画面・検索・絞り込み・(数の種類別)カタログ表示・プリセット詳細への遷移・カスタム生成画面への遷移を、React なしで実装する。

## 動作の概要

- `mountGradeDrills(root)`: `root` 配下に状態(`state`: `route`/`selectedNumberType`/`selectedForms`/`selectedGrade`/`selectedLevel`/`query`/`openPreset`/`activeRenderer`)を持つクロージャを構築し、`render()` を呼ぶ。マウント時に `GET /renderer-info` を1回 fetch し、`activeRenderer` を確定させる(`frontend/spa` の `GradeDrills` コンポーネントの `useEffect` と同じタイミング)。
- `render()`: `root.innerHTML = ''` で毎回クリアし、新しい `<div class="grade-drills">` を生成して追加する。`state.openPreset` があれば `presetDetail.js` の `mountPresetDetail()` に、`state.route === CUSTOM_GRADE` なら `customGenerator.js` の `mountCustomGenerator()` に委譲する。それ以外はホーム画面またはカタログ画面(検索/絞り込みバー・数の種類別ビュー・ドリルカードグリッド)を `innerHTML` 文字列として構築する。
- 状態遷移はすべて `data-action`/`data-role` 属性を介したイベント委譲(`view.addEventListener('click'|'change'|'input', ...)`)で行う。`openCatalog()`/`toggleForm()` は `frontend/spa` の同名関数とロジックを一致させている。
- `select-grade`/`select-level` ボタンの遷移先(数の種類・絞り込み条件を保持するかどうか)は、クリック時に `inNumberTypeView()`(`state.selectedNumberType && !state.query.trim()`)を再評価して判定する。これは render 時にどちらの分岐(`numberTypeCatalogHtml`/`drillGridHtml`)が使われたかを、クリック時点の state から逆算する形になっている。

## 重要な設計判断とその理由

### render() のたびに `root` 配下を丸ごと作り直す理由

`mountPresetDetail`/`mountCustomGenerator` はそれぞれ渡されたコンテナ要素に対して独自に `addEventListener` する設計のため、同じコンテナを使い回すと画面遷移のたびにリスナーが重複登録されてしまう(例: ホーム→カスタム→ホーム→カスタムと往復するたびに送信が二重に走る)。これを避けるため、`render()` は毎回新しい `<div>` を作って `root` に追加し、直前の `<div>`(とそこに紐づくリスナー)を DOM から切り離す(ガベージコレクション対象にする)ことで、暗黙的にリスナーの重複を防いでいる。

### 検索ボックスのフォーカス・カーソル位置を明示的に復元している理由

検索入力の `input` イベントは `state.query` を更新して即座に `render()`(=DOM 再構築)するため、何もしなければ1文字入力するたびに `<input>` 要素が作り直されてフォーカスが外れ、連続入力ができなくなる。これを避けるため、`render()` の冒頭で「フォーカスが検索欄にあったか」と「カーソル位置」を保存し、再構築後に同じ `<input>` へフォーカスとカーソル位置を復元している。`CustomGenerator` 相当の数値入力欄([[./customGenerator.js]] 参照)は、この問題を「値変更時は re-render しない(state だけ更新)」という別の方式で回避しており、検索欄だけがこの明示的な復元方式を使う(検索欄は route 変更を伴う re-render が必須のため、re-render を避ける方式が使えないことによる非対称な設計)。

## 統合ポイント

- 呼び出し元: `app.js`。
- 呼び出し先: `drillPresets.js`(`GRADES`/`UNGRADED`/`CUSTOM_GRADE`)、`drillCatalog.js`(カタログ構築・絞り込み)、`presetDetail.js`、`customGenerator.js`、`strings.js`(`t`)。

## 注意事項・既知の制限

- `frontend/spa` の `NumberTypeCatalog`/`DrillCard`/`DrillGrid` は React サブコンポーネントだったが、`frontend/web` では HTML 文字列を返すヘルパー関数(`drillCardHtml`/`drillGridHtml`/`numberTypeCatalogHtml`)として同じファイル内に定義している(モジュール分割はしていない)。
