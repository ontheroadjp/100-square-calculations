# `frontend/spa/src/App.css`

## 目的・役割

Reactフロントエンド全体のモバイルファーストな表示を定義する。ドリル探索画面ではトップ入口、数の種類ページ、中見出し、問題形式フィルタを整形する。

## 動作の概要

- `.number-type-header` と `.number-type-section` は数の種類ページの導入文と分類ごとの余白・可読幅を整える（`App.css:509-532`）。
- `.format-filter` はチェックボックスを持つfieldsetを折り返し可能に表示し、モバイルでも操作可能な高さを確保する（`App.css:534-554`）。
- 既存の `.drill-start-grid` はトップの数種別・出題形式・学年の入口に共用される（`App.css:556-575`）。

## 変更履歴（git log より自動生成）

- d956e48 feat(#86): rebuild drill discovery by number type
- 7290008 feat(#73): add entrance-exam-prep drill section for grades 4-6
- 5211d63 feat(#44): rework grade-based drill menu per curriculum, inline written-calculation section, add Ungraded category
