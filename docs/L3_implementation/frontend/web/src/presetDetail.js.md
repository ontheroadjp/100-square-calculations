# `frontend/web/src/presetDetail.js`

## 目的・役割

`frontend/spa/src/GradeDrills.jsx` 内の `PresetDetail` コンポーネント([[../../frontend/spa/src/GradeDrills.jsx]] 参照)を vanilla JS に移植したモジュール。`preset.html`(ドリル詳細ページ、issue #88)の中身(設定変更・PDF再生成・プレビュー・ダウンロード)を、React なしで実装する。

## 動作の概要

- `mountPresetDetail(container, { grade, preset, onBack })`: `container` に対して状態(`numberValue`/`paperSize`/`pageCount`/`density`/`status`/`pdfUrl`/`error`/`lastGenerated`)を持つクロージャを構築し、マウント直後に自動で `generatePdf()` を1回実行する(`frontend/spa` 版の「開いたら自動でプレビュー生成」と同じ挙動)。
- `generatePdf()`: `POST /generate-pdf` を叩き、成功時は `URL.createObjectURL(blob)` で `pdfUrl` を作って `<iframe>`/ダウンロードリンクに反映する。`isVerticalOperation(preset.params)` が真の場合は `rows`/`columns` を `getVerticalRows(paperSize)`/`VERTICAL_COLUMNS` から算出し、それ以外は `DENSITY_OPTIONS`(少なめ/標準/多め)から算出する(`frontend/spa` 版と同じ分岐)。
- `isDirty()`: 直近生成時の設定(`lastGenerated`)と現在の設定を比較し、変更がなければ「PDF再生成」ボタンを無効化する。`frontend/spa` 版の `isDirty` と同じロジック。
- 「戻る」ボタンは `onBack` コールバックを呼ぶだけで、戻り先はモジュール自身は関知しない(呼び出し元の `preset.js` が `history.back()` を渡す)。

## 統合ポイント

- 呼び出し元: `preset.js`(`preset.html` のページエントリ)。
- 呼び出し先: `strings.js`(`t`)、`verticalLayout.js`、`backend`(`POST /generate-pdf`、`http://127.0.0.1:5000` 固定)。

## 注意事項・既知の制限

- backend の URL がハードコードされている点は `frontend/spa` と同じ既知の制約([[../../frontend/spa/src/CustomGenerator.jsx]] 参照)。
- `frontend/web` は SPA(単一 `index.html` を JS ルーターで画面切替する構成)ではなく、画面ごとに実在の `.html`(`index.html`/`catalog.html`/`preset.html`/`custom.html`)を持つ複数ページ構成を採用している(issue #88、ユーザー要望)。本モジュールはその中の `preset.html` 用の、独立した「マウント可能なウィジェット」として設計されている(`customGenerator.js` と同じパターン)。ページ間の画面遷移(ホーム→カタログ→詳細)は JS の内部状態ではなく、通常の `<a href>` によるブラウザナビゲーション([[./catalog.js]] 参照)で行う。
