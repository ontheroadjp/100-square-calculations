# `frontend/web/src/styles/_drillList.scss`

## 目的・役割

ドリルの縦積みリスト、カード、難易度バッジ、空状態を一つのUI単位として定義する。

## 動作の概要

`.drill-list` の中に `.drill-list-card*` の見た目をネストする(`frontend/web/src/styles/_drillList.scss:3-53`)。カードは連続したリストとして表示し、最初のカードだけ上側、最後のカードだけ下側に角丸を付ける。最後のカードには下罫線も追加してリストを閉じる(`frontend/web/src/styles/_drillList.scss:22-31`)。バッジの難易度バリエーションと空状態も定義する(`frontend/web/src/styles/_drillList.scss:55-88`)。

## 統合ポイント

- 呼び出し元: `main.scss`。
- 利用元: `catalog.js`、`pcMakeFlow.js`。
- 呼び出し先: `_base.scss` の色・余白・角丸トークン。

## 注意事項・既知の制限

PC作成フローの選択状態は `_pcMakeFlow.scss` の `.pc-drill-list-card` が追加で定義する。

## 変更履歴(git log より自動生成)

- ff1576a refactor(#128): reorganize web Sass by UI hierarchy
