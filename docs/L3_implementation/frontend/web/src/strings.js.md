# `frontend/web/src/strings.js`

## 目的・役割

`frontend/web` は日本語のみ対応(i18n ライブラリ不要、issue #88)のため、`frontend/spa` の `i18next` ランタイムの代わりに、`frontend/spa/public/locales/ja/translation.json`([[../../frontend/spa/public/locales/ja/translation.json]] 参照)をそのまま静的にコピーした `strings.ja.json` を読み込み、キー引きするだけの `t(key)` 関数を提供する。

## 動作の概要

- `t(key)`: `strings.ja.json` から該当キーの日本語文字列を返す。キーが存在しない場合はキー自体をフォールバック表示する(翻訳漏れがあっても画面が壊れないようにするため)。
- `strings.ja.json` は元々 `frontend/spa` の `ja/translation.json` を丸ごとコピーしたもの。プリセットの `titleKey`/`descKey` など、`drillPresets.js`/`drillCatalog.js` が参照するキー体系は `frontend/spa` と共有している(データ側は移植時に変更していないため)。issue #97 で `frontend/web` 固有のナビゲーションシェル用キー(`nav_home`/`nav_create`/`nav_history`/`nav_favorites`/`nav_mypage`/`nav_brand`/`nav_mobile_label`/`nav_pc_label`)を追加し、同issueで撤去した検索UI・旧2リンクナビ専用のキー(旧 `nav_home`(「ドリルを探す」の意)・`drill_navigation_label`・`drill_search_label`・`drill_search_placeholder`)を削除した。これにより `strings.ja.json` は `frontend/spa` の `ja/translation.json` と完全一致ではなくなっている(`frontend/spa` 側にはナビシェル自体が存在しないため)。

## 重要な設計判断とその理由

### 手で JS へ書き写さず JSON をそのまま import した理由

349行・300件超のキーを手動で JS リテラルへ転記すると転記ミスのリスクが高いため、`frontend/spa` の `ja/translation.json` をそのまま `strings.ja.json` としてコピーし、Vite の JSON import 機能でオブジェクトとして読み込むだけにした。将来 `frontend/spa` 側の文言が更新された場合、`frontend/web` 側は追従コピーが必要になる(自動同期の仕組みは持たない)。

## 統合ポイント

- 呼び出し元: `home.js`/`catalog.js`/`preset.js`/`presetDetail.js`/`navShell.js`(issue #97 で追加)。`customGenerator.js` は issue #97 で削除済み。
- 呼び出し先: なし(`strings.ja.json` を読み込むのみ)。

## 注意事項・既知の制限

- 英語ロケール・言語切替 UI は持たない(要件により日本語固定)。`strings.ja.json` に `en` 相当のキーは含まれない。
- issue #97 の変更により `frontend/spa` の `ja/translation.json` との「追従コピー」関係は部分的に崩れている(ナビシェル用キーの追加・撤去済みUI用キーの削除)。今後 `frontend/spa` 側の翻訳を追従コピーする際は、この差分(ナビシェル用キーは対象外、撤去済みキーは復活させない)を踏まえる必要がある。
