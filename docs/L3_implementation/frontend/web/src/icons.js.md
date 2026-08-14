# `frontend/web/src/icons.js`

## 目的・役割

`docs/uiux/wireframe_v1.png` に合わせた Material Symbols(Outlined, Apache License 2.0)のインライン SVG アイコン集。アイコンフォント/webfont は使わず、ビルド依存を増やさない `frontend/web` の方針に合わせて生の SVG マークアップ文字列として保持している(issue #97 台の nav シェル刷新で導入、issue #126 で `face`/`chevronLeft` を追加)。

## 動作の概要

- `ICONS` オブジェクトが唯一のエクスポート。各キーは Material Symbols の名称に対応する `<svg viewBox="0 -960 960 960" ...>` 文字列(`fill="currentColor"` で呼び出し側のテキスト色を継承)。
- 現在のキー: `home`/`create`/`history`/`favorite`/`mypage`/`brand`(いずれも `navShell.js` のタブ/サイドバー用)、`back`(未タイトルの単独「戻る」CTA用、`arrow_back`)、`chevronRight`(disclosure 開閉トグル用)、`checkDone`(完了画面の大きなチェックマーク)、`face`(学年カードのアバターアイコン、issue #126)、`chevronLeft`(ページヘッダーの戻る矢印、issue #126)。
- 呼び出し側はテンプレートリテラル内で `${ICONS.xxx}` として直接埋め込む(innerHTML 経由)。

## 重要な設計判断とその理由

### `back`(arrow_back)と `chevronLeft`(chevron_left)を使い分けている理由

`back` は「戻る」ボタン単体が独立したCTAとして存在する箇所(`catalog.js`/`preset.js`/`presetDetail.js` の空状態フォールバックリンク)で使う、シャフト付きの矢印アイコン。一方 `chevronLeft` は、ページヘッダーの「アイコン+タイトル」を1つのクリック領域にまとめた `.page-header-row`(`catalog.js`/`presetDetail.js` 参照)専用で、wireframe の各画面ヘッダーが一貫して山形(`<`)を使っている見た目に合わせて issue #126 で追加した。既存の `back` を CSS で回転・反転させるのではなく、Material Symbols の実際の `chevron_left` パスを別キーとして持たせることで、他のアイコンと同じ「公式パスをそのまま保持する」一貫性を保っている。

## 統合ポイント

- 呼び出し元: `navShell.js`、`home.js`、`catalog.js`、`preset.js`、`presetDetail.js`、`pcMakeFlow.js`。
- 呼び出し先: なし(依存を持たない純データモジュール)。

## 注意事項・既知の制限

- 各アイコンの `width`/`height` 属性はハードコードされており、呼び出し側で個別にサイズ変更する仕組みはない(CSS の `svg { width: ... }` 上書きは可能)。
- ソース: Google の `material-design-icons` リポジトリ(Apache License 2.0)から Outlined スタイルのパスをそのまま転記している。

## 変更履歴(git log より自動生成)

- bf48e4c feat(#130): make catalog page accent color switch dynamically per grade
- 1bb0f69 #126 frontend/web: add missing wireframe icons and unify page headers (#127)
- 90864a5 refactor(frontend/web): replace hand-drawn nav/UI icons with Material Symbols
