# `frontend/web/src/strings.js`

## 目的・役割

`frontend/web` は日本語のみ対応(i18n ライブラリ不要、issue #88)のため、`frontend/spa` の `i18next` ランタイムの代わりに、`frontend/spa/public/locales/ja/translation.json`([[../../frontend/spa/public/locales/ja/translation.json]] 参照)をそのまま静的にコピーした `strings.ja.json` を読み込み、キー引きするだけの `t(key)` 関数を提供する。

## 動作の概要

- `t(key)`: `strings.ja.json` から該当キーの日本語文字列を返す。キーが存在しない場合はキー自体をフォールバック表示する(翻訳漏れがあっても画面が壊れないようにするため)。
- `strings.ja.json` は `frontend/spa` の `ja/translation.json` を丸ごとコピーしたもの。プリセットの `titleKey`/`descKey` など、`drillPresets.js`/`drillCatalog.js` が参照するキー体系は `frontend/spa` と完全に共有している(データ側は移植時に変更していないため)。

## 重要な設計判断とその理由

### 手で JS へ書き写さず JSON をそのまま import した理由

349行・300件超のキーを手動で JS リテラルへ転記すると転記ミスのリスクが高いため、`frontend/spa` の `ja/translation.json` をそのまま `strings.ja.json` としてコピーし、Vite の JSON import 機能でオブジェクトとして読み込むだけにした。将来 `frontend/spa` 側の文言が更新された場合、`frontend/web` 側は追従コピーが必要になる(自動同期の仕組みは持たない)。

## 統合ポイント

- 呼び出し元: `home.js`/`catalog.js`/`presetDetail.js`/`customGenerator.js` すべて。
- 呼び出し先: なし(`strings.ja.json` を読み込むのみ)。

## 注意事項・既知の制限

- 英語ロケール・言語切替 UI は持たない(要件により日本語固定)。`strings.ja.json` に `en` 相当のキーは含まれない。
