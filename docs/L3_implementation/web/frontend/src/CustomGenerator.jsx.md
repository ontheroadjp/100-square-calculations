# `web/frontend/src/CustomGenerator.jsx`

## 目的・役割

`nuts_calc.py` の生パラメータ(command_type・桁数・演算子・行/列数など)を直接指定してPDFを生成する詳細設定フォーム。旧 `App.jsx` に直書きされていたフォームロジックをそのまま移設したもので、動作は変更していない(`web/frontend/src/CustomGenerator.jsx:1-330`)。

## 動作の概要

- `commandType`(`ope`/`com`/`100`/`99`/`aBc`/`squ`/`pi`)ごとにタブ(計算設定・用紙設定・オプション・PDF)内の表示項目を出し分ける。
- `handleSubmit` が `formData` を組み立てて `POST http://127.0.0.1:5000/generate-pdf` を呼び、成功時は `blob` から `URL.createObjectURL` で `pdfUrl` を作り、PDFタブに切り替えてプレビュー(`<iframe>`)と `<a href={pdfUrl} download>` を表示する(`web/frontend/src/CustomGenerator.jsx:39-104`)。
- `a_value`/`b_value` は `commandType` ごとに送信要否が分岐する(`formData` 組み立て内、`CustomGenerator.jsx:45-52`)。入力欄自体は `ope`/`100` で `a_value`/`b_value` の両方、`com`/`99`/`squ`/`pi` で `a_value` のみ表示する(`CustomGenerator.jsx:181,193`)のに対し、`formData` 側の分岐もこれと1対1で対応している必要がある(以前は `100` の分岐が漏れており、入力しても送信されなかった。issue #4 Phase 4 で修正済み)。
- `commandType === 'ope'` のとき、「オプション」タブに `vertical`(筆算形式で出力)チェックボックスがある。チェック時のみ `formData.vertical = true` を送信し、`web/backend/app.py` 経由で `nuts_calc.py --vertical` を呼び出す([[../../../../nuts_calc.py]] 参照)。対応演算(add/sub/mul。mul は掛ける数の桁数を問わず対応、issue #10)以外(div/mix)を選んだ場合のバリデーションはフロントエンドでは行わず、`nuts_calc.py` 側のエラーに委ねている。

## 重要な設計判断

- 元の `App.jsx` にあった未使用の `handleOperatorChange` 関数(ラジオボタンの `onChange` からは呼ばれておらず、実質デッドコード)は移設時に削除した。挙動に影響なし。
- 言語切替(`i18n.language`/`changeLanguage`)はヘッダー側(`App.jsx`)の責務になったため、このコンポーネントは `useTranslation()` の `t` のみを使用する。
- `vertical` チェックボックスは既存の `intermediate`(途中式を表示)と同じパターン(`commandType === 'ope'` の時だけ表示、チェック時のみ `formData` に含める)を踏襲している。

## 統合ポイント

- 呼び出し元: `GradeDrills.jsx`(「カスタム」選択時に描画)
- 呼び出し先: `POST http://127.0.0.1:5000/generate-pdf`(`web/backend/app.py`)

## 注意事項・既知の制限

- backend の URL がハードコードされている(`http://127.0.0.1:5000`)。これは移設前から存在した既存の制約で、今回のスコープでは変更していない。
- CSS クラス名(`form-group`/`tab-nav`/`checkbox-grid` 等)は `web/frontend/src/App.css` のグローバルセレクタに依存する(スコープされていない)。

## 変更履歴(git log より自動生成)

- cfea9ed fix(#4): fix 9 logic bugs found in CLI, web backend, and frontend
- 0a11eaf feat(#9): add vertical (written-calculation) output format for ope command
- 0631cf9 feat(#5): add grade-based drill PDF picker to web/frontend
