# `frontend/web/src/presetDetail.test.js`

## 目的・役割

`presetDetail.js` が公開するDOM非依存の純粋関数をNode標準テストで検証し、プリセット詳細画面の設定値解決、サマリ、問題数レイアウト、例題変換の契約を保証する。

## 動作の概要

10/20/30問とrows/columnsの対応、完了サマリの構築、分数・帯分数・演算子を含む例題のKaTeX用セグメント変換、静的/動的例題の選択を検証する。依存するchoice設定については、`disabledWhen` が現在状態から非活性を判定し、`resolveValue` が非活性中の強制表示値を返すことを検証する。固定設定(`type: 'fixed'`、issue #303)については `fixedSettingView(setting)` が、兄弟 option リストありなら全 option と `labelKey === valueLabelKey` に一致する `selectedValue` を、なしなら単一合成ピルを返すこと、一致 option が無い場合は `selectedValue: null` になることを検証する。

## 重要な設計判断とその理由

DOM環境やブラウザテスト依存を追加せず、状態依存ロジックを `selectedSettingValue`・`isSettingDisabled`・`fixedSettingView` に分離して直接テストする。HTMLの `disabled` 属性・`.segmented-control.is-disabled` の見た目はVite buildと実機確認で保証する。

## 統合ポイント

- テスト対象: `frontend/web/src/presetDetail.js` のexportされた純粋関数(`frontend/web/src/presetDetail.test.js:3-12`)。
- 実行方法: `node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js`。

## 注意事項・既知の制限

DOMイベント、CSSの見た目、PDF生成APIとの通信はこの単体テストの対象外。

## 変更履歴（git log より自動生成）

- aca0f4f feat(#134): add 出題形式 (式/筆算) setting to add/sub/mul/div preset detail pages
- 81e0b2d #139 frontend/web: switch preset detail example previews to live backend generation (#177)
- 06870bb #148 Add multiplication-table question-order options (#150)
- 1d8ee60 #135 frontend/web: switch preset detail page example problems based on selected settings (#141)
- 2d9ee47 #132 frontend/web: dynamic grade accent, KaTeX fraction examples, generalized setting hints, and move problem count into common settings on preset detail page (#136)
- 9d1371e #100 frontend/web: rebuild preset detail settings/completion/preview screens (#118)
