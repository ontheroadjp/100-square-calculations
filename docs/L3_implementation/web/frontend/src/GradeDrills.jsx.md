# `web/frontend/src/GradeDrills.jsx`

## 目的・役割

サイトのメイン画面。学年(1〜6年生)+「カスタム」をリンク風ボタンのナビゲーションとして表示し、選択中の学年に応じたプリセットのドリルPDFをダウンロードできるようにする。「カスタム」選択時は `CustomGenerator` をそのまま表示する(`web/frontend/src/GradeDrills.jsx:93-171`)。

## 動作の概要

- `GradeDrills`(親): `selectedGrade`(初期値 `1`、または `CUSTOM_GRADE`)・共有設定 `paperSize`/`pageCount` を状態として持つ。学年選択時のみ、共有設定(用紙サイズ・ページ数)と `presetsByGrade[selectedGrade]` から `PresetCard` を並べたグリッドを描画する。
- `PresetCard`(子、preset単位): 各カードが独立した状態(`numberValue`・`status`・`pdfUrl`・`error`)を持つ。`numberInput` を持つ preset(九九の「段」、`pi`/`squ` の「開始する数」)はカード内にインライン数値入力を表示する。

## 主要フロー: 生成→ダウンロードの2段階方式

`handleGenerate` は `preset.params` に共有設定(`paper_size`/`rows`/`columns`/`page`)と `numberInput` の値をマージして `POST /generate-pdf` を呼び、成功したら `status: 'ready'` にして `pdfUrl`(`URL.createObjectURL(blob)`)をセットする。ダウンロードボタンはこの時点で **実際の `<a href={pdfUrl} download>` リンク**に切り替わり、ユーザーがそれをクリックして初めてブラウザのダウンロードが走る(`web/frontend/src/GradeDrills.jsx:17-56, 121-136`)。

**なぜ `fetch` 完了後に `link.click()` を自動発火しないのか**: 実装当初は `fetch` の `await` 完了後に `document.createElement('a')` で合成した要素を即座に `.click()` させ、1クリックでダウンロードまで完了する設計にしていた。ブラウザ実機検証で、1枚目のダウンロードは成功するが、同一ページ内で2枚目以降のプリセットを続けてダウンロードしようとすると、Chrome側でファイルがディスクに保存されない(サーバー側ではPDF生成に成功しているのに、クライアント側の自動ダウンロードだけ失敗する)ことを確認した。`await` を挟んだ後の合成クリックは、直接のユーザー操作由来のダウンロードとして扱われない場合があるため、複数回の自動ダウンロードがブラウザ側で握りつぶされたと考えられる。既存の `CustomGenerator.jsx` と同じ「生成 → 実リンクをユーザーが明示的にクリック」という2ステップ方式に変更することでこの問題を回避した(実機で1年生・2年生の複数プリセットを連続ダウンロードして再現しないことを確認済み)。

## 統合ポイント

- 呼び出し元: `App.jsx`
- 呼び出し先: `drillPresets.js`(`GRADES`/`CUSTOM_GRADE`/`presetsByGrade`)、`CustomGenerator.jsx`(カスタム選択時)、`POST http://127.0.0.1:5000/generate-pdf`(`web/backend/app.py`)

## 注意事項・既知の制限

- backend の URL はハードコード(`CustomGenerator.jsx` と同様、既存の制約を踏襲)。
- ダウンロード後に `URL.revokeObjectURL` は呼んでいない(`CustomGenerator.jsx` の既存挙動に合わせた)。SPA として長時間・多数のプリセットを生成し続けるとメモリ上に objectURL が残り続けるが、通常の利用(数枚のPDFを生成してページを離脱)では実用上問題にならない。
- モバイルファーストのCSSは `web/frontend/src/App.css` の `.grade-nav`/`.preset-card-grid` などのセクションに実装している(基準はモバイル幅、`min-width: 600px`/`900px` で段階的に拡張)。

## 変更履歴(git log より自動生成)

- 0631cf9 feat(#5): add grade-based drill PDF picker to web/frontend
