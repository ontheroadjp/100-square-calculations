# `frontend/web/src/strings.js`

## 目的・役割

`frontend/web` は日本語のみ対応(i18n ライブラリ不要、issue #88)のため、`frontend/spa` の `i18next` ランタイムの代わりに、`frontend/spa/public/locales/ja/translation.json`([[../../frontend/spa/public/locales/ja/translation.json]] 参照)をそのまま静的にコピーした `strings.ja.json` を読み込み、キー引きするだけの `t(key)` 関数を提供する。

## 動作の概要

- `t(key)`: `strings.ja.json` から該当キーの日本語文字列を返す。キーが存在しない場合はキー自体をフォールバック表示する(翻訳漏れがあっても画面が壊れないようにするため)。
- `strings.ja.json` の import は `with { type: 'json' }` インポート属性を付けている(issue #100)。Vite(≧5)は属性なしのプレーンな `import ja from './strings.ja.json'` でも動作するが、`frontend/web` のテストは Vite を介さないプレーンな `node --test` で動くため、属性なしだと Node 側で `strings.js` を import しようとした瞬間に失敗する。`presetDetail.js`([[./presetDetail.js]] 参照)の `presetDetail.test.js` が `presetDetail.js` を直接importして純粋関数(`layoutForProblemCount`/`buildSummaryParts`)をテストする際にこの経路を踏むため追加した。
- `strings.ja.json` は元々 `frontend/spa` の `ja/translation.json` を丸ごとコピーしたもの。プリセットの `titleKey`/`descKey` など、`drillPresets.js`/`drillCatalog.js` が参照するキー体系は `frontend/spa` と共有している(データ側は移植時に変更していないため)。issue #97 で `frontend/web` 固有のナビゲーションシェル用キー(`nav_home`/`nav_create`/`nav_history`/`nav_favorites`/`nav_mypage`/`nav_brand`/`nav_mobile_label`/`nav_pc_label`)を追加し、同issueで撤去した検索UI・旧2リンクナビ専用のキー(旧 `nav_home`(「ドリルを探す」の意)・`drill_navigation_label`・`drill_search_label`・`drill_search_placeholder`)を削除した。issue #99 で新トップ/カテゴリ画面用のキー(`grade_full_1`〜`6`、`category_picker_heading`、`category_addition`/`category_subtraction`/`category_multiplication`/`category_division`/`category_fraction`/`category_four-operations`/`category_number-sense`、`example_prefix`)を追加した。issue #101 で PC 4カラムレイアウト用のキー(`pc_grade_column_heading`/`pc_category_column_heading`/`pc_settings_column_heading`/`pc_select_grade_prompt`/`pc_select_drill_prompt`/`pc_preview_placeholder`)を追加した([[./pcMakeFlow.js]] 参照。カラム見出し「プレビュー」自体は既存の `preview_heading` を再利用しており新規キーではない)。これにより `strings.ja.json` は `frontend/spa` の `ja/translation.json` と完全一致ではなくなっている(`frontend/spa` 側にはナビシェル・新カテゴリ体系・PCレイアウト用キーが存在しないため)。旧絞り込みUI専用キー(`subject_*`/`number_type_*_intro`/`form_*`/`*_filter_label`/`all_*`/`clear_filters` 等)は issue #99 で参照元(`catalog.js`/`index.html`)を削除したが、キー自体は削除していない(削除の要否は範囲外と判断。将来の docs-sync/清掃作業で扱う)。

## 重要な設計判断とその理由

### 手で JS へ書き写さず JSON をそのまま import した理由

349行・300件超のキーを手動で JS リテラルへ転記すると転記ミスのリスクが高いため、`frontend/spa` の `ja/translation.json` をそのまま `strings.ja.json` としてコピーし、Vite の JSON import 機能でオブジェクトとして読み込むだけにした。将来 `frontend/spa` 側の文言が更新された場合、`frontend/web` 側は追従コピーが必要になる(自動同期の仕組みは持たない)。

## 統合ポイント

- 呼び出し元: `catalog.js`/`preset.js`/`presetDetail.js`/`navShell.js`(issue #97 で追加)/`pcMakeFlow.js`(issue #101 で追加)。`home.js` は issue #99 で `t()` への直接依存を撤去した(トップ画面の文言は `index.html` に直接ハードコード。`pcMakeFlow.js` 経由での間接依存は issue #101 で生じている)。`customGenerator.js` は issue #97 で削除済み。
- 呼び出し先: なし(`strings.ja.json` を読み込むのみ)。

## 注意事項・既知の制限

- 英語ロケール・言語切替 UI は持たない(要件により日本語固定)。`strings.ja.json` に `en` 相当のキーは含まれない。
- issue #97/#99 の変更により `frontend/spa` の `ja/translation.json` との「追従コピー」関係は部分的に崩れている(ナビシェル用キー・カテゴリ画面用キーの追加、撤去済みUI用キーの削除)。今後 `frontend/spa` 側の翻訳を追従コピーする際は、この差分(ナビシェル/カテゴリ用キーは対象外、撤去済みキーは復活させない)を踏まえる必要がある。

## 変更履歴(git log より自動生成)

- feat(#101): add PC 4-column layout string keys(このタスクでの変更。コミットハッシュは /docs-sync 実行時に確定)
- 64f005b feat(#100): rebuild frontend/web preset detail settings/completion/preview screens
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
