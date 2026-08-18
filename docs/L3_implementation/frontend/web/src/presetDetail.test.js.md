# `frontend/web/src/presetDetail.test.js`

## 目的・役割

`presetDetail.js` が公開するDOM非依存の純粋関数をNode標準テストで検証し、プリセット詳細画面の設定値解決、サマリ、問題数レイアウト、例題変換の契約を保証する。

## 動作の概要

10/20/30問とrows/columnsの対応、完了サマリの構築、分数・帯分数・演算子を含む例題のKaTeX用セグメント変換、静的/動的例題の選択を検証する。依存するchoice設定については、`disabledWhen` が現在状態から非活性を判定し、`resolveValue` が非活性中の強制表示値を返すことを検証する(`frontend/web/src/presetDetail.test.js:78-89`)。

## 重要な設計判断とその理由

DOM環境やブラウザテスト依存を追加せず、状態依存ロジックを `selectedSettingValue` と `isSettingDisabled` に分離して直接テストする。HTMLの `disabled` 属性自体の描画はVite buildと実機確認で保証する。

## 統合ポイント

- テスト対象: `frontend/web/src/presetDetail.js` のexportされた純粋関数(`frontend/web/src/presetDetail.test.js:3-12`)。
- 実行方法: `node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js`。

## 注意事項・既知の制限

DOMイベント、CSSの見た目、PDF生成APIとの通信はこの単体テストの対象外。
