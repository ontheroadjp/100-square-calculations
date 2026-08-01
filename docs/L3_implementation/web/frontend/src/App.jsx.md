# `web/frontend/src/App.jsx`

## 目的・役割

アプリのトップレベルシェル。ヘッダー(タイトル・言語切替)を描画し、本体は常に `GradeDrills` を描画する(`web/frontend/src/App.jsx:1-38`)。

## 動作の概要

- `useTranslation()` から `t`/`i18n` を取得し、タイトルと言語切替ボタンのラベルに使う。
- `changeLanguage(lng)` は `i18n.changeLanguage(lng)` を呼ぶだけ(`web/frontend/src/App.jsx:8-10`)。
- モード切り替え(学年別 / 詳細設定)は `App.jsx` レベルには存在しない。学年(1〜6)とカスタムの切り替えは `GradeDrills` 内部の状態として持たせている(下記 [[GradeDrills.jsx]] 参照)。

## 重要な設計判断

- 当初案では「学年別」「詳細設定」をヘッダーの別モードトグルとして分けていたが、ユーザー指示により学年リンクの一つとして「カスタム」を並べる構成に変更した。これにより `App.jsx` はヘッダーのみを担当するシンプルな構成になった。

## 統合ポイント

- 呼び出し元: `web/frontend/src/main.jsx`
- 呼び出し先: `GradeDrills`(`web/frontend/src/GradeDrills.jsx`)

## 注意事項・既知の制限

- 言語切替は `i18next-http-backend` 経由で `public/locales/{lng}/translation.json` を fetch する。ネットワーク(同一オリジンの静的ファイル配信)が必要。
