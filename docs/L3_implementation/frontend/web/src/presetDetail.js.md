# `frontend/web/src/presetDetail.js`

## 目的・役割

`preset.html`(ドリル詳細ページ)の中身を実装するマウント可能なウィジェット。issue #100 で、`docs/uiux/wireframe_v1.png` の画面③④⑤(設定 → 完了 → プレビュー)に合わせた3状態ビューへ全面書き換えした。旧実装(issue #88〜#99時点)は単一画面で、マウント直後に自動でPDFを生成し、設定フォームと常時表示iframeを同居させていた。

## 動作の概要

- `mountPresetDetail(container, { grade, item, onBack })`: `item` は `drillPresets.js` の生アイテム(`settings`/`buildParams`/`supportLevel`/`difficultyKey`/`examples` 等、[[./drillPresets.js]] 参照)をそのまま受け取る。`screen`(`'settings' | 'done' | 'preview'`)を含む状態を持つクロージャを構築するが、マウント時に自動生成は行わない(`screen: 'settings'` で開始)。
- 設定画面(`screen === 'settings'`):
  - ページヘッダーは `<header class="preset-detail-header"><button class="page-header-row" data-action="back">${ICONS.chevronLeft}<h3 class="preset-detail-title">...</h3></button></header>`(issue #126)。アイコン・タイトルどちらをクリックしても `container` のクリック委譲(`data-action === 'back'` → `onBack()`)が発火する単一のクリック領域で、「戻る」というテキストラベルは持たない。
  - 例題チップ(`item.examples`)、`supportLevel === 'partial'` の制限注記
  - 問題数 segmented control(10/20/30問。`layoutForProblemCount()` で `nuts_calc.py` の `rows`/`columns` に変換。20問が旧実装の標準密度=10行×2列と同値)
  - `item.settings` を動的レンダリング: `type: 'choice'` は segmented control(値が `'mixed'` のとき汎用ヒント文 `setting_mixed_hint` を表示)、`type: 'fixed'` は読み取り専用表示
  - 「詳細設定(共通設定)」disclosure(初期折りたたみ)に用紙サイズ・ページ数を格納
  - 「名前をつける」トグル: 状態は保持するが `buildParams()` の出力には混ぜない(issue A3 でパラメータが用意されるまでUIのみ)
  - `supportLevel === 'none'` は「PDFを作成する」を無効化し「準備中」表示に切り替える(現行 `drillPresets.js` に `none` のアイテムは存在しないが、issue要求に従い汎用実装)
- `generatePdf()`: `item.buildParams(state.settingsState)` で request body の演算パラメータを得て、`POST /generate-pdf` を叩く。`isVerticalOperation(params)` が真の場合のみ `getVerticalRows`/`VERTICAL_COLUMNS` を使う(現行データモデルでは到達しない分岐だが、旧実装からの後方互換として維持)。成功時は `screen = 'done'` に遷移し、古い `pdfUrl` があれば `URL.revokeObjectURL()` で解放する。失敗時は `screen = 'settings'` に留まりエラーメッセージを表示する。
- 完了画面(`screen === 'done'`): チェックマーク+静的CSS confetti、`buildSummaryParts()` によるサマリ文(例:「20問・基礎・繰り上がり：まぜる」)、4アクション(PDFを開く→`screen='preview'`、ダウンロードする→`<a download>`、同じ条件でもう1枚作る→`generatePdf()` 再実行、トップに戻る→`index.html`)。
- プレビュー画面(`screen === 'preview'`): `<iframe src="${pdfUrl}#navpanes=0">`。ズーム等はブラウザ内蔵PDFビューアのツールバーに委ね、自前実装しない。戻る操作は `history.back()` ではなく `screen = 'done'` への内部遷移(ブラウザ履歴を消費しない)。ヘッダーは設定画面と同じ `<header class="preview-header"><button class="page-header-row" data-action="back-to-done">${ICONS.chevronLeft}<h3 class="preset-detail-title">${t('preview_heading')}</h3></button></header>` パターン(issue #126。旧実装は `<div class="preview-header">` + `<span>` タイトルで、`<header>` タグではなかった)。
- `layoutForProblemCount(problemCount)`・`buildSummaryParts(..., translate)` はエクスポートされた純粋関数。`buildSummaryParts` は `translate` を引数で受け取る設計にしており、`presetDetail.test.js`(L3 doc化は見送り、`frontend/web` の既存 `drillPresets.test.js` にも個別docが無い慣例に合わせた)から `strings.ja.json` の実際の日本語文言に依存せずアサーションできる。

## 重要な設計判断とその理由

### `drillCatalog.js` を経由しない直接消費に変更した理由

旧実装は `drillCatalog.js`(`catalog.js` が issue #99 で経由をやめた後も `preset.js` だけが使い続けていた)経由でプリセットを取得していたが、`drillCatalog.js` の `createCatalogEntries()` はカタログ構築時点でデフォルト状態の `item.buildParams(defaultState)` を1回だけ呼んで結果を凍結する([[./drillCatalog.js]] 参照)。設定画面でユーザー操作のたびに `buildParams(state)` を呼び直す必要があるインタラクティブなUIとは根本的に非互換なため、`item` を生のまま受け取る形に変更した(`preset.js` 側の変更は [[./preset.js]] 参照)。

## 統合ポイント

- 呼び出し元: `preset.js`(`preset.html` のページエントリ)。
- 呼び出し先: `strings.js`(`t`)、`verticalLayout.js`、`icons.js`(`ICONS.chevronLeft`、issue #126)、`backend`(`POST /generate-pdf`、`http://127.0.0.1:5000` 固定)。

## 注意事項・既知の制限

- backend の URL がハードコードされている点は `frontend/spa` と同じ既知の制約([[../../frontend/spa/src/CustomGenerator.jsx]] 参照)。
- `preset.html` は元々静的な `<header class="app-header"><h1>100マス計算ジェネレーター</h1></header>` を持っていたが、このファイルが描画する設定画面の見出し(旧: 独立した `<h3 class="preset-detail-title">`)と重複していた(issue #126)ため、静的ヘッダーを削除し本ファイル側の `<header>` に一本化した([[./home.js]] 参照)。
- 完了画面のPDFサムネイルは実PDFレンダリングではなく静的なCSS装飾(`.completion-thumbnail`)。confettiも静的CSS(アニメーションなし)。例題チップは1行表示(wireframeは2行)。いずれもissue #100のスコープ簡略化として意図的に採用した。
- `frontend/web` は複数ページ構成(issue #88、ユーザー要望)。本モジュールは `preset.html` 用の独立した「マウント可能なウィジェット」として設計されている(`customGenerator.js` と同じパターン、issue #97 で `customGenerator.js` 自体は削除済み)。

## 変更履歴(git log より自動生成)

- 64f005b feat(#100): rebuild frontend/web preset detail settings/completion/preview screens
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
