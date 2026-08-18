# `frontend/web/src/presetDetail.js`

## 目的・役割

`preset.html`(ドリル詳細ページ)の中身を実装するマウント可能なウィジェット。issue #100 で、`docs/uiux/wireframe_v1.png` の画面③④⑤(設定 → 完了 → プレビュー)に合わせた3状態ビューへ全面書き換えした。旧実装(issue #88〜#99時点)は単一画面で、マウント直後に自動でPDFを生成し、設定フォームと常時表示iframeを同居させていた。

## 動作の概要

- `mountPresetDetail(container, { grade, item, onBack })`: `item` は `drillPresets.js` の生アイテム(`settings`/`buildParams`/`supportLevel`/`difficultyKey`/`examples` 等、[[./drillPresets.js]] 参照)をそのまま受け取る。`screen`(`'settings' | 'done' | 'preview'`)を含む状態を持つクロージャを構築するが、マウント時に自動生成は行わない(`screen: 'settings'` で開始)。マウント直後に `container.classList.add(\`grade-${grade}\`)` を実行し(issue #132)、以後全画面の再描画(`container.innerHTML` の丸ごと差し替え)を通じてこのクラスを保持する。`catalog.js` と同じ `.grade-N` カスタムプロパティ(`_base.scss` 参照)経由で、ヘッダー・選択中ボタン・PDF作成ボタン等が学年色に切り替わる。
- 設定画面(`screen === 'settings'`):
  - ページヘッダーは `catalog.js` と同じ `<header class="catalog-header"><div class="catalog-header-title"><a class="page-header-row" href="index.html">${ICONS.chevronLeft}<h1 class="catalog-heading">...</h1></a></div>...</header>` パターン(issue #132。旧: 独立した `.preset-detail-header`)。学年アクセントカラーの背景は `_catalog.scss` の `.catalog-header-title` スタイルをそのまま共用する。
  - 例題チップは `selectExamples(item, state.settingsState)`(export、issue #135)で取得した配列を `renderExampleHtml()`/`buildExampleSegments()`(共にexport、issue #132)で KaTeX 描画する。`selectExamples` は `item.examplesFor` があればそれを `state.settingsState` で呼んだ結果を、無ければ `item.examples` をそのまま返す純粋関数([[./drillPresets.js]] の「選択中の設定に応じた例題切り替え」参照)。設定を切り替えるたびに `render()` が呼ばれて `renderSettingsScreen()` 内で再計算されるため、`examplesFor` を持つ項目は表示中の例題がリアルタイムに切り替わる。分数・帯分数・演算子(`×`→`\times`、`÷`→`\div`)を数式トークンとして抽出し、日本語(`奇数`/`最大公約数` 等)や矢印はプレーンテキストのまま残す(KaTeX 自身のフォントに CJK グリフが無いため)。`exampleWithEquals()` が矢印を含まない例題の末尾へ `=` を補い(未解決の問題として表示)、矢印を含む例題(frac2dec/simplify/evenodd 等、既に結果を示している)はそのまま。
  - `supportLevel === 'partial'` の制限注記
  - `item.settings` を `.specific-setting-block` 内へ動的レンダリング: `type: 'choice'` は segmented control(選択中の値に対応する `option.hintKey` があればその下にヒント文を表示、issue #132 で `value === 'mixed'` ハードコードから汎用化)、`type: 'fixed'` は読み取り専用表示。choice が任意の `disabledWhen(settingsState)` を持つ場合は全ボタンへ `disabled` を付けて表示したまま操作不能にし、`resolveValue(settingsState)` があれば保持値ではなくその解決値を選択表示と完了サマリに使う(`frontend/web/src/presetDetail.js:31-37,114-124,155-176`)。
  - 「詳細設定(共通設定)」disclosure(初期折りたたみ)に問題数 segmented control(10/20/30問。`layoutForProblemCount()` で `nuts_calc.py` の `rows`/`columns` に変換。20問が旧実装の標準密度=10行×2列と同値)・用紙サイズ・ページ数を格納(issue #132 で問題数をここへ移動。旧実装は `.specific-setting-block` の外、disclosure の手前に独立表示していた)
  - 「名前をつける」トグル: 状態は保持するが `buildParams()` の出力には混ぜない(issue A3 でパラメータが用意されるまでUIのみ)
  - `supportLevel === 'none'` は「PDFを作成する」を無効化し「準備中」表示に切り替える(現行 `drillPresets.js` に `none` のアイテムは存在しないが、issue要求に従い汎用実装)
- `generatePdf()`: `item.buildParams(state.settingsState)` で request body の演算パラメータを得て、`POST /generate-pdf` を叩く。`isVerticalOperation(params)` が真の場合のみ `getVerticalRows`/`VERTICAL_COLUMNS` を使う(現行データモデルでは到達しない分岐だが、旧実装からの後方互換として維持。issue #134 が「表示形式(式/筆算)」設定を追加すると `vertical: true` を返すプリセットが登場し、この分岐が実際に使われるようになる予定)。成功時は `screen = 'done'` に遷移し、古い `pdfUrl` があれば `URL.revokeObjectURL()` で解放する。失敗時は `screen = 'settings'` に留まりエラーメッセージを表示する。
- 完了画面(`screen === 'done'`): チェックマーク+静的CSS confetti、`buildSummaryParts()` によるサマリ文(例:「20問・基礎・繰り上がり：まぜる」)、4アクション(PDFを開く→`screen='preview'`、ダウンロードする→`<a download>`、同じ条件でもう1枚作る→`generatePdf()` 再実行、トップに戻る→`index.html`)。
- プレビュー画面(`screen === 'preview'`): `<iframe src="${pdfUrl}#navpanes=0">`。ズーム等はブラウザ内蔵PDFビューアのツールバーに委ね、自前実装しない。戻る操作は `history.back()` ではなく `screen = 'done'` への内部遷移(ブラウザ履歴を消費しない)。ヘッダーは設定画面と同じ `<header class="preview-header"><button class="page-header-row" data-action="back-to-done">${ICONS.chevronLeft}<h3 class="preset-detail-title">${t('preview_heading')}</h3></button></header>` パターン(issue #126。旧実装は `<div class="preview-header">` + `<span>` タイトルで、`<header>` タグではなかった)。
- `layoutForProblemCount(problemCount)`・`buildSummaryParts(..., translate)`・`buildExampleSegments(example)`・`exampleWithEquals(example)`・`selectExamples(item, settingsState)`・`selectedSettingValue(setting, settingsState)`・`isSettingDisabled(setting, settingsState)` はエクスポートされた純粋関数。`buildSummaryParts` は `translate` を引数で受け取る設計にしており、`presetDetail.test.js` から `strings.ja.json` の実際の日本語文言に依存せずアサーションできる。`buildExampleSegments`/`exampleWithEquals` は文字列変換のみ行い、実際の `katex.renderToString()` 呼び出しは非公開の `renderExampleHtml()` が担う(DOM/KaTeX 依存部分をテスト対象から切り離すため、issue #132)。依存設定の値解決と非活性判定もDOMから分離した2関数を直接テストする(`frontend/web/src/presetDetail.js:31-37`)。

## 重要な設計判断とその理由

### `drillCatalog.js` を経由しない直接消費に変更した理由

旧実装は `drillCatalog.js`(`catalog.js` が issue #99 で経由をやめた後も `preset.js` だけが使い続けていた)経由でプリセットを取得していたが、`drillCatalog.js` の `createCatalogEntries()` はカタログ構築時点でデフォルト状態の `item.buildParams(defaultState)` を1回だけ呼んで結果を凍結する([[./drillCatalog.js]] 参照)。設定画面でユーザー操作のたびに `buildParams(state)` を呼び直す必要があるインタラクティブなUIとは根本的に非互換なため、`item` を生のまま受け取る形に変更した(`preset.js` 側の変更は [[./preset.js]] 参照)。

### KaTeX の CSS import を `preset.js` 側に置いた理由

`frontend/web` の node:test 群(`test_frontend_web` = `node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js`)は Vite を経由せず素の Node ESM ローダーで `presetDetail.js` を直接 import する。plain CSS の `import 'katex/dist/katex.min.css'` を `presetDetail.js` に書くと `ERR_UNKNOWN_FILE_EXTENSION` でテストが即失敗するため、CSS import は Vite バンドル経由でのみ読み込まれる `preset.js`(`preset.html` のページエントリ)側に置いた。JS 本体の `import katex from 'katex'` は katex パッケージが `exports.import` に ESM ビルド(`dist/katex.mjs`)を持つため `presetDetail.js` 内のままで node:test からも問題なく解決できる。

## 統合ポイント

- 呼び出し元: `preset.js`(`preset.html` のページエントリ。KaTeX の CSS も `preset.js` 側で import する、上記参照)。
- 呼び出し先: `katex`(`katex.renderToString()`、issue #132)、`strings.js`(`t`)、`verticalLayout.js`、`icons.js`(`ICONS.chevronLeft`、issue #126)、`backend`(`POST /generate-pdf`、`http://127.0.0.1:5000` 固定)、`item.examplesFor`(`drillPresets.js` 側の項目定義、issue #135、[[./drillPresets.js]] 参照)。

## 注意事項・既知の制限

- backend の URL がハードコードされている点は `frontend/spa` と同じ既知の制約([[../../frontend/spa/src/CustomGenerator.jsx]] 参照)。
- `preset.html` は元々静的な `<header class="app-header"><h1>100マス計算ジェネレーター</h1></header>` を持っていたが、このファイルが描画する設定画面の見出し(旧: 独立した `<h3 class="preset-detail-title">`)と重複していた(issue #126)ため、静的ヘッダーを削除し本ファイル側の `<header>` に一本化した([[./home.js]] 参照)。設定画面の見出しはその後 issue #132 で `.catalog-header` パターンへ再度差し替わっている(上記「動作の概要」参照)。
- 完了画面のPDFサムネイルは実PDFレンダリングではなく静的なCSS装飾(`.completion-thumbnail`)。confettiも静的CSS(アニメーションなし)。例題チップは1行表示(wireframeは2行)。いずれもissue #100のスコープ簡略化として意図的に採用した。
- `frontend/web` は複数ページ構成(issue #88、ユーザー要望)。本モジュールは `preset.html` 用の独立した「マウント可能なウィジェット」として設計されている(`customGenerator.js` と同じパターン、issue #97 で `customGenerator.js` 自体は削除済み)。
- 非活性な設定ボタンはHTMLの `disabled` 属性とクリックハンドラ双方で変更を拒否する(`frontend/web/src/presetDetail.js:169-172,374-383`)。

## 変更履歴(git log より自動生成)

- 7b5a9b9 feat(#132): add per-grade accent, KaTeX examples, generalized setting hints, and move problem count into common settings on preset detail page
- ab9fe98 feat(#126): add missing wireframe icons and unify page headers in frontend/web
- 90864a5 refactor(frontend/web): replace hand-drawn nav/UI icons with Material Symbols
- 9d1371e #100 frontend/web: rebuild preset detail settings/completion/preview screens (#118)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
