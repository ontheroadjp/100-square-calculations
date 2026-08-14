# `frontend/web/src/styles/_presetDetail.scss`

## 目的・役割

プリセット詳細の設定、作成完了、PDFプレビュー画面のスタイルを一元管理する。

## 動作の概要

`.preset-detail` を画面ルートにして、例題、設定ブロック、セグメント選択、開閉領域、トグル、作成ボタン、完了表示、プレビューを各親要素の下にネストして定義する(`frontend/web/src/styles/_presetDetail.scss:3-303`)。

## 重要な設計判断とその理由

### `$color-primary` の直書きを `var(--color-primary, ...)` へ置き換えた理由(issue #132)

`.specific-setting-block` の枠線、`.segmented-option.is-selected`、`.create-pdf-button`(通常/hover)、`.toggle-switch.is-on`、`.completion-secondary-button:hover` は、いずれも `$color-primary` を直書きしていたため学年に関わらず常に同じ青色だった。`_base.scss` が `.grade-N { --color-primary; --color-primary-hover; }` を定義するようになった(issue #130 で `_catalog.scss` にあったものを集約)ことを受け、これらすべてを `var(--color-primary, #{$color-primary})` フォールバック形式に置き換え、`presetDetail.js` が `container` に付与する `grade-N` クラス経由で学年色に追従するようにした。

旧 `&-header { background-color: var($color-primary, $color-primary); }`(`.preset-detail-header` 用)は、対象クラス自体が `presetDetail.js` 側で `.catalog-header` パターンに置き換わり未使用になった([[../presetDetail.js]] 参照)ことに加え、`var()` の第一引数に `#{}` 補間なしで Sass 変数を渡すと不正な CSS になる実装ミスもあったため削除した。

## 統合ポイント

- 呼び出し元: `main.scss`。
- 利用元: `presetDetail.js`、`pcMakeFlow.js`。
- 呼び出し先: `_base.scss` のデザイントークン(`.grade-N` カスタムプロパティ含む、issue #132)。

## 注意事項・既知の制限

`.preset-detail` の設定画面はモバイル詳細画面とPC作成フローで共有し、PC固有のレイアウトは `_pcMakeFlow.scss` が追加する。`pcMakeFlow.js` の `container` には `grade-N` クラスが付かないため、そちら側は常に `var()` のフォールバック値(固定の `$color-primary`)のままになる(issue #132 のスコープ外)。

## 変更履歴(git log より自動生成)

- 7b5a9b9 feat(#132): add per-grade accent, KaTeX examples, generalized setting hints, and move problem count into common settings on preset detail page
- ff1576a refactor(#128): reorganize web Sass by UI hierarchy
