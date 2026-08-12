# `frontend/web/src/drillCatalog.js`

## 目的・役割

`frontend/spa/src/drillCatalog.js`([[../../frontend/spa/src/drillCatalog.js]] 参照)をそのまま複製したファイル。`presetsByGrade` から検索・絞り込み可能なフラットなドリル一覧(カタログ)を構築する純粋関数群で、React・i18next に依存しないため無変更で再利用できる。

## 動作の概要

`buildDrillCatalog(renderer)`/`filterDrillCatalog(catalog, filters)`/`addSearchText(catalog, translate)`/`NUMBER_TYPES`/`OPERATION_GROUPS`/`DRILL_FORMS` を export する。`addSearchText` の第2引数 `translate` には `frontend/web` では `strings.js` の `t` を渡す(`frontend/spa` では `react-i18next` の `t`)。内容・設計判断は [[../../frontend/spa/src/drillCatalog.js]] を参照(完全に同一)。

## 統合ポイント

- 呼び出し元: `home.js`(利用可能な出題形式の算出)、`catalog.js`(カタログ構築・絞り込み)、`preset.js`(URLパラメータからのプリセット特定)。
- 呼び出し先: `drillPresets.js`(`GRADES`/`UNGRADED`/`presetsByGrade`)。

## 注意事項・既知の制限

- `frontend/spa/src/drillCatalog.js` が更新された場合、本ファイルは追従コピーが必要(issue #88 時点では同一内容)。[[./drillPresets.js]] と同じ制約。
