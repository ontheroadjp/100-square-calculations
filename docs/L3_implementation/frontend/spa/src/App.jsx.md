# `frontend/spa/src/App.jsx`

## 目的・役割

アプリのトップレベルシェル。ヘッダー(タイトル・言語切替)を描画し、本体は常に `GradeDrills` を描画する(`frontend/spa/src/App.jsx:1-38`)。

## 動作の概要

- `useTranslation()` から `t`/`i18n` を取得し、タイトルと言語切替ボタンのラベルに使う。
- `changeLanguage(lng)` は `i18n.changeLanguage(lng)` を呼ぶだけ(`frontend/spa/src/App.jsx:8-10`)。
- モード切り替え(学年別 / 詳細設定)は `App.jsx` レベルには存在しない。学年(1〜6)・無学年・カスタムの切り替えは `GradeDrills` 内部の状態として持たせている(下記 [[GradeDrills.jsx]] 参照)。

## 重要な設計判断

- 当初案では「学年別」「詳細設定」をヘッダーの別モードトグルとして分けていたが、ユーザー指示により学年リンクの一つとして「カスタム」を並べる構成に変更した。これにより `App.jsx` はヘッダーのみを担当するシンプルな構成になった。

## 統合ポイント

- 呼び出し元: `frontend/spa/src/main.jsx`
- 呼び出し先: `GradeDrills`(`frontend/spa/src/GradeDrills.jsx`)

## 注意事項・既知の制限

- 言語切替は `i18next-http-backend` 経由で `public/locales/{lng}/translation.json` を fetch する。ネットワーク(同一オリジンの静的ファイル配信)が必要。

## 変更履歴(git log より自動生成)

- 0631cf9 feat(#5): add grade-based drill PDF picker to web/frontend
- f219dcd feat(web): Reorganize UI with tabs and PDF preview
- 8e535fc feat(web): Implement note.com-like design with plain CSS
- 2024bfb feat(web): Implement i18n for language switching (EN/JA)
- 7b62e9b feat(web): Implement comprehensive UI for 100masu.py arguments
- 68daa78 feat: Implement web interface (React + Tailwind + Flask)
