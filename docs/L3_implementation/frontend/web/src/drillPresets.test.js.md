# `frontend/web/src/drillPresets.test.js`

## 目的・役割

`drillPresets.js` の grade → category → menu-item データモデルが、UIとPDF生成処理の前提を満たすことをNode標準テストで検証する。

## 動作の概要

全学年と未分類の全メニュー項目を列挙し、カテゴリ、必須フィールド、設定、IDの一意性、既定設定からのリクエスト生成、動的例題を検証する。`difficultyKey` は `KNOWN_DIFFICULTY_KEYS` に含まれることを要求し、基礎・標準・基礎〜標準・発展以外の未知の値やタイプミスを失敗させる(`frontend/web/src/drillPresets.test.js:5-16,26-34,50-61`)。

## 重要な設計判断とその理由

難易度は単なる文字列型ではなくUIの文言・CSS・互換分類と結び付く列挙値であるため、文字列であることだけでなく既知キーとの一致を検証する。

## 統合ポイント

- テスト対象: `drillPresets.js` の `GRADES`、`UNGRADED`、`presetsByGrade`。
- 実行方法: `node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js`。

## 注意事項・既知の制限

- DOM描画やSassの見た目は検証せず、データモデルの契約だけを対象とする。

## 変更履歴（git log より自動生成）

- e8ce3ec feat(#146): add advanced difficulty badge
- 1d8ee60 #135 frontend/web: switch preset detail page example problems based on selected settings (#141)
- 94eb478 #98 Rebuild frontend/web drill menu data model to match calculation_drill_menu_parameters_v1.md (#115)
