# `web/frontend/src/GradeDrills.jsx`

## 目的・役割

サイトのメイン画面。学年(1〜6年生)+「無学年」+「カスタム」をリンク風ボタンのナビゲーションとして表示する。学年(または無学年)選択時は、通常形式のプリセット一覧グリッドと、その下部にインライン表示される「筆算」セクション(その学年に `written` プリセットがある場合のみ)を表示する。いずれかのプリセットの「PDFを生成」を押すと、同じ画面内で詳細ページ(プレビュー+設定+ダウンロード)に切り替わる。「カスタム」選択時は `CustomGenerator` をそのまま表示する。

## 動作の概要

- `GradeDrills`(親): `selectedGrade`(初期値 `1`、数値学年、`UNGRADED`、または `CUSTOM_GRADE`)・`openPreset`(選択中のプリセット、または `null`)・`activeRenderer`(初期値 `reportlab`)を状態として持つ。`supportsWritten` は `activeRenderer === 'latex'` から導出する。`openPreset` が非 null の間はグリッドの代わりに `PresetDetail` を描画する「一覧⇔詳細」の単純な2画面構成(ルーティングライブラリは使わず、コンポーネント内 state で切り替え)。
- **`supportsWritten`(issue #46)**: マウント時に `useEffect` で1回だけ `GET http://127.0.0.1:5000/renderer-info`(`web/backend/app.py`)を叩き、レスポンスの `renderer` が `'latex'`(= `nuts_calc_tex.py`)なら `true` にする。fetch 失敗時も `catch` で `false` にフォールバックする。初期値・フォールバック値をともに `false` にしているのは、バックエンドのデフォルトレンダラーが `reportlab`(`nuts_calc.py`、`--vertical` 非対応、issue #46 で削除)であることに合わせたもので、最も一般的なケース(env 変数未設定)では fetch 完了前後で表示が変化(フラッシュ)しない。
- **LaTeX専用プリセット(issue #65)**: `normalPresets` は `preset.latexOnly` が真のカードを `activeRenderer === 'latex'` の場合だけ残す。これにより `nuts_calc_tex.py` 固有の `frac` カードがReportLab環境で表示・送信されることを防ぐ。レンダラー取得失敗時も `reportlab` に戻る安全側の挙動である(`web/frontend/src/GradeDrills.jsx:201-239,264-268`)。
- `NAV_GRADES`: `[...GRADES, UNGRADED]`。学年ナビの「カスタム」ボタン手前に並べる項目(数値学年1〜6 → 無学年)。`presetsByGrade` のキー(`drillPresets.js`)がすべて `{ normal, written }` の同一構造を持つため、`UNGRADED` も数値学年と全く同じ描画ロジックで扱える。
- 筆算(`written`)は独立したタブではなく、通常グリッドの直後に `<section className="written-section">` として常時インライン表示する。`writtenPresets` は `!isCustom && supportsWritten` の場合のみ `presetsByGrade[selectedGrade].written` を参照し、それ以外(`isCustom`、または `supportsWritten` が `false`)は空配列にする(issue #46)。`presetsByGrade[selectedGrade].written` が空配列の学年(現状は1年生のみ)ではいずれにせよセクション自体を描画しない。以前は「通常形式/筆算形式」タブ切り替えだったが、筆算を隠さず常に見える位置に置きたいという要望により変更した。
- `PresetCard`(グリッド側): タイトル・説明・「PDFを生成」ボタンのみを持つ。クリックで親の `openPreset` にそのプリセットをセットする。通常セクション・筆算セクションのどちらでも同じコンポーネントを再利用する。
- `PresetDetail`(詳細ページ側): プリセットごとの生成設定(用紙サイズ・ページ数・問題数、`numberInput` を持つプリセットは段/開始する数も)・生成状態(`status`/`pdfUrl`/`error`)を保持する。マウント時に `useEffect` で1回 `generatePdf()` を実行し、詳細ページを開いた瞬間にプレビューを表示する。`written`(筆算)プリセットは `verticalLayout.js` の用紙別行数と2列を送るため、通常の問題密度セレクタは表示しない。通常プリセットだけが固定の問題密度(5×2 / 10×2 / 10×4)を使う。`writtenPresets` が `supportsWritten` でガードされているため、`PresetDetail` に到達する `written` プリセットは常に `latex` レンダラーが有効な状態になる。
- `<CustomGenerator supportsVertical={supportsWritten} />`: カスタム画面にも同じ `supportsWritten` 値をそのまま渡し、筆算チェックボックスの表示可否を揃える([[CustomGenerator.jsx]] 参照)。

## 主要フロー1: モーダルではなくページ内遷移

当初はプリセットカードから開く**モーダル**でプレビュー・設定・ダウンロードを行う実装だったが、ユーザーの指示により**通常のページ内遷移(グリッドの代わりに詳細ビューを描画)+「戻る」ボタン**に変更した。理由: モバイルでは元々モーダルを `92vh` の実質フルスクリーン表示にしており、フルページ化してもほぼ見た目は変わらない一方、モーダル特有の「ページスクロール/モーダル内スクロール/PDFプレビュー(PDF.js)内スクロール」が重なる操作性の問題(実機検証でPDF.jsのオーバーフローメニュー操作が意図と異なる要素に当たるなど)を回避でき、単一のスクロール領域に統一できる。

## 主要フロー2: 「PDF再生成」ボタンの活性/非活性

`PresetDetail` は `lastGenerated`(直近の生成に使った設定のスナップショット: `paperSize`/`pageCount`/`density`/`numberValue`)を保持し、現在の設定値と1つでも異なれば `isDirty = true` として「PDF再生成」ボタンを活性化する。生成中(`status === 'loading'`)または `isDirty` が `false`(まだ何も変更していない、または直前に生成した設定のまま)の場合はボタンを disabled にする。`generatePdf()` が成功するたびに `lastGenerated` を現在の設定で更新するため、再生成後は再びボタンが非活性に戻る。

## 主要フロー3: 生成→ダウンロードの2段階方式(ダウンロードボタン)

ダウンロードボタンは常に **実際の `<a href={pdfUrl} download>` リンク**(`status === 'ready'` かつ `pdfUrl` がある場合のみ活性、それ以外は disabled な `<button>` を表示)で、ユーザーが明示的にクリックして初めてブラウザのダウンロードが走る。

**なぜ `fetch` 完了後に `link.click()` を自動発火しないのか**: 実装当初は `fetch` の `await` 完了後に `document.createElement('a')` で合成した要素を即座に `.click()` させ、1クリックでダウンロードまで完了する設計にしていた。ブラウザ実機検証で、1枚目のダウンロードは成功するが、同一ページ内で2枚目以降のプリセットを続けてダウンロードしようとすると、Chrome側でファイルがディスクに保存されない(サーバー側ではPDF生成に成功しているのに、クライアント側の自動ダウンロードだけ失敗する)ことを確認した。`await` を挟んだ後の合成クリックは、直接のユーザー操作由来のダウンロードとして扱われない場合があるため、複数回の自動ダウンロードがブラウザ側で握りつぶされたと考えられる。既存の `CustomGenerator.jsx` と同じ「生成 → 実リンクをユーザーが明示的にクリック」という2ステップ方式を踏襲することでこの問題を回避している(実機で複数プリセット・モーダル内DL・詳細ページ内DLのいずれでも連続ダウンロードが再現しないことを確認済み)。

## 統合ポイント

- 呼び出し元: `App.jsx`
- 呼び出し先: `drillPresets.js`(`GRADES`/`UNGRADED`/`CUSTOM_GRADE`/`presetsByGrade`)、`CustomGenerator.jsx`(カスタム選択時、`supportsVertical` prop を渡す)、`GET http://127.0.0.1:5000/renderer-info`(マウント時、issue #46)、`POST http://127.0.0.1:5000/generate-pdf`(`web/backend/app.py`、実際のレンダラーは `web/backend/renderers.py` が `NUTS_CALC_RENDERER` で `nuts_calc.py`/`nuts_calc_tex.py` を切り替える)

## 注意事項・既知の制限

- backend の URL はハードコード(`CustomGenerator.jsx` と同様、既存の制約を踏襲。`/renderer-info` も同じホストにハードコード)。
- ダウンロード後に `URL.revokeObjectURL` は呼んでいない(`CustomGenerator.jsx` の既存挙動に合わせた)。SPA として長時間・多数のプリセットを生成し続けるとメモリ上に objectURL が残り続けるが、通常の利用では実用上問題にならない。
- 「問題数」(少なめ/標準/多め)は `nuts_calc.py`/`nuts_calc_tex.py` の `rows`/`columns` にマッピングされる固定値(5×2 / 10×2 / 10×4)。100マス計算プリセット(`command_type === '100'`)は `rows`/`columns` を使わない固定10×10グリッドのため、`PresetDetail` はこのプリセットに限り問題数セレクタを表示しない。
- モバイルファーストのCSSは `web/frontend/src/App.css` の `.grade-nav`/`.preset-card-grid`/`.written-section`/`.preset-detail-*` などのセクションに実装している。
- `written` の内容・件数は学年によって異なる(`drillPresets.js.md` 参照)。1年生は0件(セクション非表示)。加えて issue #46 以降は `supportsWritten`(バックエンドが `latex` レンダラーの場合のみ `true`)が `false` の間、`written` を持つ学年でもセクションごと非表示になる。

## 変更履歴(git log より自動生成)

- fd449c7 fix(#57): apply vertical layout in web UI
- 9ead364 refactor(#46): remove --vertical from nuts_calc.py; gate written-calculation UI on active renderer
- 5211d63 feat(#44): rework grade-based drill menu per curriculum, inline written-calculation section, add Ungraded category
- f0201d6 feat(#13): add grade-based written-calculation (hissan) drill menu
- 39b8f97 feat(#7): switch preset PDF preview to a full detail page with a dirty-checked regenerate button
- 0631cf9 feat(#5): add grade-based drill PDF picker to web/frontend
