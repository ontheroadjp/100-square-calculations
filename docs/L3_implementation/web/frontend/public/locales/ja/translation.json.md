# `web/frontend/public/locales/ja/translation.json`

## 目的・役割

フロントエンドの日本語翻訳辞書。個別プリセットに加え、数の種類からの探索、出題形式/目的、演算分類、問題形式フィルタの表示文言を定義する。

## 注意事項

`drillPresets.js` の `titleKey`/`descKey` と完全一致させる。探索画面の `number_type_*`、`operation_group_*`、`form_*` キーは `GradeDrills.jsx` と `drillCatalog.js` から参照される。

## 変更履歴(git log より自動生成)

- 9e296ee feat(#83): add fraction comparison worksheets
- 1186039 feat(#78): add carry-aware grade 1 drills
- 6889ef0 feat(#76): add decimal ope arithmetic and int/decimal/fraction mixed command
- 7290008 feat(#73): add entrance-exam-prep drill section for grades 4-6
- 6c2ee20 feat(#69): add ope --missing-value option with grade menu cards
- 1b7e795 feat(#67): add ope --use-parentheses option with grade menu cards
- 7c89a52 feat(#65): add curriculum-aligned fraction worksheets
