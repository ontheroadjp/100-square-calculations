# `frontend/web/src/pageHeader.js`

## 目的・役割

`catalog.js`(学年別カテゴリ画面)と `presetDetail.js`(ドリル設定画面)で重複していた `<header class="catalog-header">` マークアップを共通化した、issue #157 の成果物。`navShell.js`([[./navShell.js]] 参照)と同じ「JSモジュール化した共通UI片」パターンを踏襲する。

## 動作の概要

- `pageHeaderHtml(title, description)`: `title`(見出し)と `description`(見出し下の説明文)の2引数を受け取り、`<header class="catalog-header">` マークアップ文字列を返す純粋関数。戻るリンクは常に `href="index.html"` 固定。アイコンは `ICONS.chevronLeft`。
- `title`/`description` は呼び出し側で `t()` により解決済みの文字列を渡す設計とし、本モジュール自体は `strings.js`/`drillPresets.js` のキー構造を知らない(`frontend/web/src/pageHeader.js:1-10`)。

## 重要な設計判断とその理由

### `description` を固定文言ではなく引数にした理由

当初の `catalog.js`/`presetDetail.js` は見出し下の説明文をどちらも `t('category_picker_heading')`(「練習したい計算ドリルを選んでください」)固定で表示していた。ユーザー要望により、学年ごと(`catalog.js`)・ドリルごと(`presetDetail.js`)に異なる指導ポイント文言(保護者向け、専門用語を避けた平易な一文)を表示できるようにする必要があったため、`description` を呼び出し側から渡す引数として設計した。`catalog.js` は `grade_point_${grade}`、`presetDetail.js` は `item.pointKey`([[./drillPresets.js]] 参照)をそれぞれ渡す。

## 統合ポイント

- 呼び出し元: `catalog.js`([[./catalog.js]] 参照)、`presetDetail.js`(設定画面のヘッダーのみ、[[./presetDetail.js]] 参照)。
- 呼び出し先: `icons.js`(`ICONS.chevronLeft`)。

## 注意事項・既知の制限

- href は `index.html` 固定で引数化していない(現状の2呼び出し元がいずれも同じ遷移先のため、YAGNI)。
- `presetDetail.js` のプレビュー画面ヘッダー(`<header class="preview-header">`、`ICONS.chevronLeft` + `<h3>` + `data-action="back-to-done"`)は構造が異なる別コンポーネントで、本モジュールの対象外。
- `catalog.js` の空状態(grade が不正な場合の `emptyStateHtml()`)はヘッダー自体を表示しないため、本モジュールを経由しない。

## 変更履歴（git log より自動生成）

- 1ae72a3 feat(#157): add per-grade/per-drill header descriptions via a shared page header component
