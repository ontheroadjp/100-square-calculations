# `frontend/web/src/presetDetail.js`

## 目的・役割

`frontend/spa/src/GradeDrills.jsx` 内の `PresetDetail` コンポーネント([[../../frontend/spa/src/GradeDrills.jsx]] 参照)を vanilla JS に移植したモジュール。ドリルカードから開く「プリセット詳細」画面(設定変更・PDF再生成・プレビュー・ダウンロード)を、React なしで実装する。`GradeDrills.jsx` 内に同居していた `PresetDetail` を独立ファイルに切り出している(`frontend/web` では単一ファイルが大きくなりすぎないよう、`gradeDrills.js`/`customGenerator.js` と並列のトップレベルモジュールにした)。

## 動作の概要

- `mountPresetDetail(container, { grade, preset, onBack })`: `container` に対して状態(`numberValue`/`paperSize`/`pageCount`/`density`/`status`/`pdfUrl`/`error`/`lastGenerated`)を持つクロージャを構築し、マウント直後に自動で `generatePdf()` を1回実行する(`frontend/spa` 版の「開いたら自動でプレビュー生成」と同じ挙動)。
- `generatePdf()`: `POST /generate-pdf` を叩き、成功時は `URL.createObjectURL(blob)` で `pdfUrl` を作って `<iframe>`/ダウンロードリンクに反映する。`isVerticalOperation(preset.params)` が真の場合は `rows`/`columns` を `getVerticalRows(paperSize)`/`VERTICAL_COLUMNS` から算出し、それ以外は `DENSITY_OPTIONS`(少なめ/標準/多め)から算出する(`frontend/spa` 版と同じ分岐)。
- `isDirty()`: 直近生成時の設定(`lastGenerated`)と現在の設定を比較し、変更がなければ「PDF再生成」ボタンを無効化する。`frontend/spa` 版の `isDirty` と同じロジック。

## 統合ポイント

- 呼び出し元: `gradeDrills.js`(ドリルカードの「PDFを生成」等のボタンが押されたとき)。
- 呼び出し先: `strings.js`(`t`)、`verticalLayout.js`、`backend`(`POST /generate-pdf`、`http://127.0.0.1:5000` 固定)。

## 注意事項・既知の制限

- backend の URL がハードコードされている点は `frontend/spa` と同じ既知の制約([[../../frontend/spa/src/CustomGenerator.jsx]] 参照)。
- `back`/`regenerate` ボタンと `number-value`/`paper-size`/`page-count`/`density` 各入力のイベントは `container` への委譲(`addEventListener`)1回のみで、`render()` のたびに再登録はしない(`container` 自体は `gradeDrills.js` 側で毎回新規生成されるため、リスナーの重複は発生しない。[[./gradeDrills.js]] の「render() のたびに root 配下を丸ごと作り直す理由」参照)。
