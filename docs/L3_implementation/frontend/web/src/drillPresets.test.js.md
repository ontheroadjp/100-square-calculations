# `frontend/web/src/drillPresets.test.js`

## 目的・役割

`drillPresets.js` の grade → category → menu-item データモデルが、UIとPDF生成処理の前提を満たすことをNode標準テストで検証する。

## 動作の概要

全学年と未分類の全メニュー項目を列挙し、カテゴリ、必須フィールド、設定、IDの一意性、既定設定からのリクエスト生成、動的例題を検証する。`difficultyKey` は `KNOWN_DIFFICULTY_KEYS` に含まれることを要求し、基礎・標準・基礎〜標準・発展以外の未知の値やタイプミスを失敗させる(`frontend/web/src/drillPresets.test.js:5-16,26-34,50-61`)。choice 設定の任意の `disabledWhen`/`resolveValue` が関数であることを検証し、2年生九九の固定段3順序がフラグなし/`descend`/`shuffle` へ変換されること、および「まぜる」が保持中の順序にかかわらず従来のランダム `ope` パラメータを返すことを回帰テストする(`frontend/web/src/drillPresets.test.js:65-107`)。

2年生の発展足し算・発展引き算(issue #154)について、それぞれ addition/subtraction カテゴリに存在し、`difficulty_advanced`/`latexOnly: true` を持ち、既定の「まぜる」状態から1〜999のオペランド範囲と `result_max: 1000` を生成することを検証する(`frontend/web/src/drillPresets.test.js:100-132`)。

## 重要な設計判断とその理由

難易度は単なる文字列型ではなくUIの文言・CSS・互換分類と結び付く列挙値であるため、文字列であることだけでなく既知キーとの一致を検証する。

## 統合ポイント

- テスト対象: `drillPresets.js` の `GRADES`、`UNGRADED`、`presetsByGrade`。
- 実行方法: `node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js`。

## 注意事項・既知の制限

- DOM描画やSassの見た目は検証せず、データモデルの契約だけを対象とする。

## 変更履歴（git log より自動生成）

- 32dd948 feat(#153): add reusable result ceiling for ope drills
- 06870bb #148 Add multiplication-table question-order options (#150)
- 85e58b1 #146 Add an advanced difficulty badge to the web UI (#147)
- 1d8ee60 #135 frontend/web: switch preset detail page example problems based on selected settings (#141)
- 94eb478 #98 Rebuild frontend/web drill menu data model to match calculation_drill_menu_parameters_v1.md (#115)
