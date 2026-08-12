# `frontend/web/src/drillPresets.js`

## 目的・役割

`frontend/spa/src/drillPresets.js`([[../../frontend/spa/src/drillPresets.js]] 参照)をそのまま複製したファイル。「学年(1〜6、または無学年)」を `POST /generate-pdf` へのリクエストパラメータにマッピングする静的データで、React・i18next に一切依存しない純粋な ES module のため、`frontend/web` でもコード変更なしで再利用できる。

## 動作の概要

`GRADES`・`UNGRADED`・`CUSTOM_GRADE`・`presetsByGrade` の4つを export する。内容・設計判断は [[../../frontend/spa/src/drillPresets.js]] を参照(完全に同一)。

## 重要な設計判断とその理由

### コピーにした理由(モノレポ内シンボリックリンク等を使わなかった理由)

`frontend/spa` と `frontend/web` は将来的に別リポジトリへ分離される可能性がある(issue #88)ため、シンボリックリンクや共有パッケージ化はせず、単純なファイルコピーにした。今後 `drillPresets.js` の内容(学年別プリセット)を変更する場合は、両ファイルを個別に更新する必要がある(自動同期の仕組みはない)。

## 統合ポイント

- 呼び出し元: `catalog.js`/`drillCatalog.js`(`GRADES`/`UNGRADED`)。`CUSTOM_GRADE` は `frontend/web` が複数ページ構成(issue #88)のため未使用(`custom.html` へは通常の `<a href>` で遷移する)。
- 呼び出し先: なし(データ定義のみ)。

## 注意事項・既知の制限

- `frontend/spa/src/drillPresets.js` が更新された場合、本ファイルは追従コピーが必要(issue #88 時点では同一内容)。
