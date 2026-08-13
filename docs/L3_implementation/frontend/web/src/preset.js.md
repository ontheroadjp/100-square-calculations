# `frontend/web/src/preset.js`

## 目的・役割

`preset.html`(ドリル詳細画面)のページエントリ。URL のクエリ文字列(`grade`/`drillId`/`format`)からプリセットを特定し、`presetDetail.js`([[./presetDetail.js]] 参照)の `mountPresetDetail()` に橋渡しする薄いグルーコード。

## 動作の概要

- `findPreset()`: `location.search` から `grade`/`drillId`/`format` を読み、`GET /renderer-info` で `activeRenderer` を確定してから `buildDrillCatalog(activeRenderer)` でカタログを再構築し、`catalog.find(d => d.id === drillId)` → `drill.presets[format]` の順でプリセットを特定する。`catalog.js`([[./catalog.js]] 参照)のドリルカードが生成する `preset.html?grade=...&drillId=...&format=...` リンクと対になっている。
- プリセットが見つかった場合は `mountPresetDetail(container, { grade, preset, onBack: () => history.back() })` で描画する。`onBack` にはブラウザの戻る操作をそのまま割り当てており、遷移元(ホーム/カタログ、どのような絞り込み状態だったか)を `preset.js` 自身が覚えておく必要はない(ブラウザの履歴スタックに任せる)。
- 見つからない場合(不正なクエリ文字列で直接アクセスされた場合等)は「条件に合うドリルが見つかりません。」メッセージと、ホームへの戻りリンクを表示する。

## 統合ポイント

- 呼び出し元: `preset.html` の `<script type="module" src="/src/preset.js">`。
- 呼び出し先: `strings.js`(`t`)、`drillCatalog.js`(`buildDrillCatalog`)、`presetDetail.js`(`mountPresetDetail`)、`navShell.js`(`mountNavShell`、issue #97 で追加)、`backend`(`GET /renderer-info`)。

## 注意事項・既知の制限

- `catalog.js` 側でカタログに存在しない `drillId`/`format` の組み合わせへのリンクは生成されないため、通常操作でこの「見つからない」経路に入ることはない。直接URLを編集してアクセスした場合のフォールバックとしてのみ機能する。
