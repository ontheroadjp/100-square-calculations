# `web/frontend/src/GradeDrills.jsx`

## 目的・役割

サイトのメイン画面。学年(1〜6年生)+「カスタム」をリンク風ボタンのナビゲーションとして表示する。学年選択時はさらに「通常形式 / 筆算形式」のフォーマット切り替えタブとプリセット一覧のグリッドを表示し、いずれかのプリセットの「PDFを生成」を押すと、同じ画面内で詳細ページ(プレビュー+設定+ダウンロード)に切り替わる。「カスタム」選択時は `CustomGenerator` をそのまま表示する。

## 動作の概要

- `GradeDrills`(親): `selectedGrade`(初期値 `1`、または `CUSTOM_GRADE`)・`openPreset`(選択中のプリセット、または `null`)・`formatCategory`(`'normal'` | `'written'`、初期値 `'normal'`)を状態として持つ。`openPreset` が非 null の間はグリッドの代わりに `PresetDetail` を描画する「一覧⇔詳細」の単純な2画面構成(ルーティングライブラリは使わず、コンポーネント内 state で切り替え)。学年リンクをクリックすると `openPreset` に加え `formatCategory` も `'normal'` にリセットされる(学年を変えるたびに毎回「筆算形式」を選び直す必要がないようにするか迷ったが、学年ごとに `written` の内容・件数が異なるため、切り替え時の混乱を避けて常に `normal` から始める設計にしている)。
- `FORMAT_CATEGORIES`: `formatCategory` の選択肢定義(`value`/`labelKey` のペア)。`presetsByGrade[grade]` が `{ normal, written }` を持つ(`drillPresets.js` 参照)ことに対応するタブ UI で、`grade-nav`/`grade-link` と同じ見た目のクラスを流用し、`format-nav` で余白のみ上書きしている(`App.css`)。
- `PresetCard`(グリッド側): タイトル・説明・「PDFを生成」ボタンのみを持つ。クリックで親の `openPreset` にそのプリセットをセットする。
- `PresetDetail`(詳細ページ側): プリセットごとの生成設定(用紙サイズ・ページ数・問題数、`numberInput` を持つプリセットは段/開始する数も)・生成状態(`status`/`pdfUrl`/`error`)を保持する。マウント時に `useEffect` で自動的に1回 `generatePdf()` を実行し、詳細ページを開いた瞬間にプレビューが表示されるようにしている。`written`(筆算)プリセットも `params.vertical: true` が `/generate-pdf` にそのまま渡るだけで、`PresetDetail` 自体に筆算固有の分岐は無い(`nuts_calc.py` 側が `rows`/`columns` を横書きと同じ意味で使うため、問題数セレクタもそのまま機能する)。

## 主要フロー1: モーダルではなくページ内遷移

当初はプリセットカードから開く**モーダル**でプレビュー・設定・ダウンロードを行う実装だったが、ユーザーの指示により**通常のページ内遷移(グリッドの代わりに詳細ビューを描画)+「戻る」ボタン**に変更した。理由: モバイルでは元々モーダルを `92vh` の実質フルスクリーン表示にしており、フルページ化してもほぼ見た目は変わらない一方、モーダル特有の「ページスクロール/モーダル内スクロール/PDFプレビュー(PDF.js)内スクロール」が重なる操作性の問題(実機検証でPDF.jsのオーバーフローメニュー操作が意図と異なる要素に当たるなど)を回避でき、単一のスクロール領域に統一できる。

## 主要フロー2: 「PDF再生成」ボタンの活性/非活性

`PresetDetail` は `lastGenerated`(直近の生成に使った設定のスナップショット: `paperSize`/`pageCount`/`density`/`numberValue`)を保持し、現在の設定値と1つでも異なれば `isDirty = true` として「PDF再生成」ボタンを活性化する。生成中(`status === 'loading'`)または `isDirty` が `false`(まだ何も変更していない、または直前に生成した設定のまま)の場合はボタンを disabled にする。`generatePdf()` が成功するたびに `lastGenerated` を現在の設定で更新するため、再生成後は再びボタンが非活性に戻る。

## 主要フロー3: 生成→ダウンロードの2段階方式(ダウンロードボタン)

ダウンロードボタンは常に **実際の `<a href={pdfUrl} download>` リンク**(`status === 'ready'` かつ `pdfUrl` がある場合のみ活性、それ以外は disabled な `<button>` を表示)で、ユーザーが明示的にクリックして初めてブラウザのダウンロードが走る。

**なぜ `fetch` 完了後に `link.click()` を自動発火しないのか**: 実装当初は `fetch` の `await` 完了後に `document.createElement('a')` で合成した要素を即座に `.click()` させ、1クリックでダウンロードまで完了する設計にしていた。ブラウザ実機検証で、1枚目のダウンロードは成功するが、同一ページ内で2枚目以降のプリセットを続けてダウンロードしようとすると、Chrome側でファイルがディスクに保存されない(サーバー側ではPDF生成に成功しているのに、クライアント側の自動ダウンロードだけ失敗する)ことを確認した。`await` を挟んだ後の合成クリックは、直接のユーザー操作由来のダウンロードとして扱われない場合があるため、複数回の自動ダウンロードがブラウザ側で握りつぶされたと考えられる。既存の `CustomGenerator.jsx` と同じ「生成 → 実リンクをユーザーが明示的にクリック」という2ステップ方式を踏襲することでこの問題を回避している(実機で複数プリセット・モーダル内DL・詳細ページ内DLのいずれでも連続ダウンロードが再現しないことを確認済み)。

## 統合ポイント

- 呼び出し元: `App.jsx`
- 呼び出し先: `drillPresets.js`(`GRADES`/`CUSTOM_GRADE`/`presetsByGrade`)、`CustomGenerator.jsx`(カスタム選択時)、`POST http://127.0.0.1:5000/generate-pdf`(`web/backend/app.py`)

## 注意事項・既知の制限

- backend の URL はハードコード(`CustomGenerator.jsx` と同様、既存の制約を踏襲)。
- ダウンロード後に `URL.revokeObjectURL` は呼んでいない(`CustomGenerator.jsx` の既存挙動に合わせた)。SPA として長時間・多数のプリセットを生成し続けるとメモリ上に objectURL が残り続けるが、通常の利用では実用上問題にならない。
- 「問題数」(少なめ/標準/多め)は `nuts_calc.py` の `rows`/`columns` にマッピングされる固定値(5×2 / 10×2 / 10×4)。100マス計算プリセット(`command_type === '100'`)は `rows`/`columns` を使わない固定10×10グリッドのため、`PresetDetail` はこのプリセットに限り問題数セレクタを表示しない。
- モバイルファーストのCSSは `web/frontend/src/App.css` の `.grade-nav`/`.format-nav`/`.preset-card-grid`/`.preset-detail-*` などのセクションに実装している。
- `written` の内容は学年によって件数・対応演算が異なる(`drillPresets.js.md` 参照)。3年生のみ `mul` を含み、4〜6年生は `add`/`sub` のみ(`nuts_calc.py --vertical` の対応範囲による制約)。

## 変更履歴(git log より自動生成)

- f0201d6 feat(#13): add grade-based written-calculation (hissan) drill menu
- 39b8f97 feat(#7): switch preset PDF preview to a full detail page with a dirty-checked regenerate button
- 0631cf9 feat(#5): add grade-based drill PDF picker to web/frontend
