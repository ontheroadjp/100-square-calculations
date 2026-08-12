# `frontend/web/src/customGenerator.js`

## 目的・役割

`frontend/spa/src/CustomGenerator.jsx`([[../../frontend/spa/src/CustomGenerator.jsx]] 参照)を vanilla JS に移植したモジュール。`nuts_calc.py`/`nuts_calc_tex.py` の生パラメータを直接指定してPDFを生成する詳細設定フォーム(計算設定/用紙設定/オプション/PDF の4タブ)を、React なしで実装する。

## 動作の概要

- `mountCustomGenerator(container, { supportsVertical })`: フォーム全項目(`paperSize`/`commandType`/`aValue`/`bValue`/`aMin`〜`bMax`/`operators`/`descend`/`reverse`/`shuffle`/`intermediate`/`vertical`/`rows`/`columns`/`withBottomAnswer`/`page`/`merge`/`csv`/`debug`/`activeTab`)を1つの `state` オブジェクトに持ち、`render()` で全体を再構築する。
- `handleSubmit`: `frontend/spa` 版と同じ条件分岐で `formData` を組み立て、`POST /generate-pdf` を呼ぶ。成功時は `activeTab` を `'pdf'` に切り替えてプレビューを表示する。
- `isRequired('a_value')`: `commandType` が `com`/`99`/`squ`/`pi` のときのみ true(`frontend/spa` 版と同一)。
- `enableVerticalLayout(paperSize)`: `getVerticalRows`/`VERTICAL_COLUMNS` から `rows`/`columns` を算出する。`vertical` チェックボックスON時、および `vertical` がON状態で `paperSize` を変更したときに呼ばれる(`frontend/spa` 版と同一)。

## 重要な設計判断とその理由

### 入力欄ごとに「render() する/しない」を使い分けている理由

`gradeDrills.js` の検索欄と同じ理由(1文字入力ごとに `<input>` を作り直すとフォーカスが外れる)により、`aMin`/`aMax`/`bMin`/`bMax`/`aValue`/`bValue`/`rows`/`columns`/`page` のようなテキスト/数値入力は、`input` イベントで `state` の値だけを更新し `render()` を呼ばない(ブラウザのネイティブ挙動でその場の値表示・フォーカスが維持される)。一方、以下は構造的な見た目の変化を伴うため `render()` が必要:
- `commandType` の変更: 表示するフィールド自体が変わる(`ope`/`com`/`100`/`99`/`squ`/`pi` で表示項目が異なる)。
- タブ切り替え(`data-action="tab"`): 表示するタブペインが変わる。
- `paperSize` の変更(かつ `vertical` がON): 同じ「用紙設定」タブ内の `rows`/`columns` 欄が `enableVerticalLayout()` により自動更新されるため、その変更を画面に反映する必要がある。
- フォーム送信: ローディング状態・生成結果(PDFタブ)を反映する必要がある。

一方、チェックボックス/ラジオボタン(`operators`/`descend`/`reverse`/`shuffle`/`intermediate`/`vertical`/`withBottomAnswer`/`merge`/`csv`/`debug`)はブラウザがチェック状態を自己管理するため、他の可視要素に影響しない限り `render()` を呼ばない。`vertical` チェックボックスは例外で、状態(`rows`/`columns`)は更新するが、それらは別タブ(用紙設定)にあり今その場では見えないため `render()` は呼ばない(タブを切り替えたときの `render()` で自然に反映される)。

## 統合ポイント

- 呼び出し元: `gradeDrills.js`(`nav-custom` 遷移時)。
- 呼び出し先: `strings.js`(`t`)、`verticalLayout.js`、`backend`(`POST /generate-pdf`)。

## 注意事項・既知の制限

- backend の URL がハードコードされている点は `frontend/spa` と同じ既知の制約([[../../frontend/spa/src/CustomGenerator.jsx]] 参照)。
- `aBc` コマンドは `command_type` の選択肢にはあるが、`frontend/spa` 版と同様に固有の追加パラメータUIは持たない(`nuts_calc_tex.py` 側のデフォルト挙動に委ねる)。
