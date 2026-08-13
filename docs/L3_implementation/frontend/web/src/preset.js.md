# `frontend/web/src/preset.js`

## 目的・役割

`preset.html`(ドリル詳細画面)のページエントリ。URL のクエリ文字列(`grade`/`drillId`)からドリルアイテムを特定し、`presetDetail.js`([[./presetDetail.js]] 参照)の `mountPresetDetail()` に橋渡しする薄いグルーコード。issue #100 で `drillCatalog.js` 経由の解決をやめ、`drillPresets.js` の `presetsByGrade` を直接検索する方式に変更した。

## 動作の概要

- `findItemById(drillId, renderer)`: `[...GRADES, UNGRADED]` の全学年・全カテゴリを走査し、`id === drillId` のアイテムを探す(`drillPresets.test.js` の「id はデータモデル全体で一意」という保証に依拠しており、URLの `grade` パラメータでの絞り込みは行わない。旧 `drillCatalog.js` 経由の実装も同様に id のみで一致させていた挙動を踏襲)。`canUseItem(item, renderer)`(`catalog.js` と同じロジック、[[./catalog.js]] 参照)で `latexOnly` アイテムを現在の renderer に応じてフィルタする。
- `findPreset()`: `location.search` から `grade`/`drillId` を読み、`GET /renderer-info` で `activeRenderer` を確定してから `findItemById()` を呼ぶ。見つかれば `{ grade, item }` を返す(旧実装の `format` クエリパラメータは、データモデルに複数フォーマットの概念がなくなった(issue #98)ため参照しなくなった。`catalog.js` のリンク生成には `&format=default` が名残として残っているが無害)。
- 見つかった場合は `mountPresetDetail(container, { grade, item, onBack: () => history.back() })` で描画する。`onBack` にはブラウザの戻る操作をそのまま割り当てており、遷移元(ホーム/カタログ)を `preset.js` 自身が覚えておく必要はない。
- 見つからない場合(不正なクエリ文字列で直接アクセスされた場合等)は「条件に合うドリルが見つかりません。」メッセージと、ホームへの戻りリンクを表示する。

## 統合ポイント

- 呼び出し元: `preset.html` の `<script type="module" src="/src/preset.js">`。
- 呼び出し先: `strings.js`(`t`)、`drillPresets.js`(`GRADES`/`UNGRADED`/`presetsByGrade`)、`presetDetail.js`(`mountPresetDetail`)、`navShell.js`(`mountNavShell`、issue #97 で追加)、`backend`(`GET /renderer-info`)。`drillCatalog.js` への依存はissue #100で撤去した(ファイル自体の削除は #110 の範囲)。

## 注意事項・既知の制限

- `catalog.js` 側でカタログに存在しない `drillId` へのリンクは生成されないため、通常操作でこの「見つからない」経路に入ることはない。直接URLを編集してアクセスした場合のフォールバックとしてのみ機能する。

## 変更履歴(git log より自動生成)

- 64f005b feat(#100): rebuild frontend/web preset detail settings/completion/preview screens
- 8007488 #97 frontend/web: rebuild nav shell, design tokens, and remove legacy features (#109)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
