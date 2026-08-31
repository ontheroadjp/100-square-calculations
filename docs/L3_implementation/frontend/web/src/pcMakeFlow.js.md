# `frontend/web/src/pcMakeFlow.js`

## 目的・役割

`index.html` の PC(≥768px)向け4カラムレイアウト(「学年」/「計算を選ぶ」/「ドリル設定」/「プレビュー」)を描画・制御するマウント可能なウィジェット(issue #101、`docs/uiux/wireframe_v1.png` の「PC版レイアウトイメージ」)。モバイルは既存の `index.html`→`catalog.html`→`preset.html` という3画面遷移のままで、この4カラムはPC幅でのみ表示される([[./styles/_pcMakeFlow.scss]] 参照)。

## 動作の概要

- `mountPcMakeFlow(container)`: `grade`/`item`/設定状態/`pdfUrl` 等を持つクロージャ状態を構築し、`container.innerHTML` を丸ごと差し替える `renderAll()` で4カラムをまとめて再描画する(`catalog.js`/`presetDetail.js` と同じ「クリックのたびに innerHTML を全再生成」のパターンを踏襲)。
- カラム1(学年): `GRADES` をボタンのリストで表示。クリックで `selectGrade(grade)` → `item`/設定状態をリセットして再描画。
- カラム2(計算を選ぶ): `presetsByGrade[grade]` を `CATEGORY_ORDER`(`catalog.js` と同じ固定順序)でグルーピングし、`canUseItem(item, activeRenderer)` でフィルタしたドリルカードを表示。難易度は `DIFFICULTY_BADGE_CLASS` で `difficulty_basic`/`difficulty_standard`/`difficulty_basic_standard`/`difficulty_advanced` を対応するCSSクラスへ変換し、未知のキーは標準バッジへフォールバックする(`frontend/web/src/pcMakeFlow.js:19-24,113-122`)。クリックで `selectItem(item)` → 問題数・設定状態・詳細設定・PDF状態をデフォルトへリセットして再描画。
- カラム3(ドリル設定): 選択中アイテムの `settings`(`choice`/`fixed`)・問題数セグメント・詳細設定(用紙サイズ/ページ数)disclosure・名前をつけるトグル・「PDFを作成する」ボタンを表示。マークアップは `presetDetail.js` の設定画面とほぼ同一だが、戻るボタンは持たない(カラムが常時表示のため)。`type: 'fixed'` の設定は `presetDetail.js` から import した `fixedSettingView(setting)` を使い、choice と同一形状の非活性 segmented control として描画する(issue #303。旧実装は `.setting-fixed-value` の素テキスト。この分岐が唯一 `presetDetail.js` の非公開描画ヘルパーに依存する箇所)。詳細設定 disclosure の開閉シェブローンは `presetDetail.js` と同じ `ICONS.chevronRight`(issue #126。旧実装はテキストグリフ `›` を直書きしており、`icons.js` 導入コミット `90864a5` で唯一置き換え漏れていた)。
- カラム4(プレビュー): `status === 'loading'` 中はローディング文言、`pdfUrl` があれば iframe プレビュー+ダウンロードリンク、いずれもなければプレースホルダー文言(`pc_preview_placeholder`)を表示。
- `generatePdf()`: `presetDetail.js` と同じ `layoutForProblemCount`/`isVerticalOperation`/`POST /generate-pdf` の呼び出しパターンを使う。成功時は `pdfUrl` をセットするのみで、`presetDetail.js` の「done」画面(完了演出・確認サマリ)には遷移しない(カラム3の設定とカラム4のプレビューが同時に見えているため、モバイル向けの完了演出は不要と判断)。

## 重要な設計判断とその理由

### 設定フォーム・PDF生成ロジックを `presetDetail.js` から一部複製した理由

`presetDetail.js` の `mountPresetDetail()` は「1つのコンテナに settings/done/preview の3状態を順番に描画する」設計([[./presetDetail.js]] 参照)で、PC の「設定カラムとプレビューカラムが常時同時に見える」要件とはコンテナ構成そのものが異なる。issue #101 が要求する「モバイルの responsive CSS 流用ではなく専用のレイアウト/インタラクションパス」に従い、`PROBLEM_COUNT_OPTIONS`/`layoutForProblemCount`/`fixedSettingView`(issue #303)はそのまま import して共有しつつ、設定フォームのマークアップ生成と `generatePdf()` はこのファイル内に複製した。`buildSummaryParts`(完了画面のサマリ文生成)は PC 側に完了画面が無いため import していない。

### `CATEGORY_ORDER`/`canUseItem`/`formatExample` を `catalog.js` から複製した理由

`catalog.js` の該当ロジックは非 export のプライベート関数であり、`catalog.js` 自身が将来 `drillCatalog.js` 同様に置き換え/削除される可能性を考慮する必要はない(`catalog.js` は #99 の新UIそのもの)ものの、1行〜数行のロジックのために `catalog.js` に export を追加して結合を増やすより、複製する方が両ファイルの独立性を保てると判断した(`catalog.js` の `canUseItem` を `drillCatalog.js` から複製した際の判断と同じ理由、[[./catalog.js]] 参照)。

### 完了(confetti)画面を実装しなかった理由

wireframe の PC レイアウトはドリル設定とプレビューが同一画面に常時表示されており、モバイル版の「PDFを作成する」→「できました!」という単独の完了演出画面に相当するステップが存在しない。PDF生成が完了すればそのままプレビューカラムに反映されるため、完了画面相当のUIは意図的に作っていない。

## 統合ポイント

- 呼び出し元: `home.js`(`mountPcMakeFlow(document.getElementById('pcMakeFlow'))`)。
- 呼び出し先: `strings.js`(`t`)、`drillPresets.js`(`GRADES`/`presetsByGrade`)、`presetDetail.js`(`PROBLEM_COUNT_OPTIONS`/`layoutForProblemCount`/`fixedSettingView`)、`verticalLayout.js`(`getVerticalRows`/`isVerticalOperation`/`VERTICAL_COLUMNS`)、`icons.js`(`ICONS.chevronRight`、issue #126)、`backend`(`GET /renderer-info`、`POST /generate-pdf`、`http://127.0.0.1:5000` 固定)。
- スタイル: [[./styles/_pcMakeFlow.scss]](`.pc-make-flow`/`.pc-flow-*`/`.pc-grade-list*`/`.pc-drill-list-card`/`.pc-column-*` を定義。設定フォーム部分は `_components.scss` の `.preset-detail-settings`/`.segmented-control`/`.disclosure`/`.toggle-switch`/`.create-pdf-button` 等を共用)。
- マウント先: `index.html` の `<div id="pcMakeFlow"></div>`(モバイル用 `.grade-drills` と兄弟要素)。

## 注意事項・既知の制限

- `renderAll()` が毎回 `container.innerHTML` を丸ごと差し替えるため、カラム2/3の内部スクロール位置(`.pc-flow-column` の `overflow-y`、`.pc-flow-columns` の `overflow-x`)は設定変更・PDF生成のたびに先頭にリセットされる。既存 `presetDetail.js`/`catalog.js` と同じ制約であり、この規模のUIでは許容範囲と判断した。
- backend の URL がハードコードされている点は `presetDetail.js`/`preset.js` と同じ既知の制約([[./presetDetail.js]] 参照)。
- 右上のユーザー名/プレミアム会員バッジ(wireframe 上に存在)は、ログイン・課金機能自体がアプリに存在しないため未実装。`.pc-flow-topbar-actions`(空の `<div>`)として領域だけ確保しており、将来ログイン機能が実装された際にここへ追加する想定(ユーザー確認済み)。
- カラム2〜4は `grade`/`item` が未選択の間、`pc_select_grade_prompt`/`pc_select_drill_prompt`/`pc_preview_placeholder` のプレースホルダー文言を表示する。

## 変更履歴(git log より自動生成)

- abd63f8 feat(#303): render fixed drill settings as an inactive segmented control
- 85e58b1 #146 Add an advanced difficulty badge to the web UI (#147)
- 1bb0f69 #126 frontend/web: add missing wireframe icons and unify page headers (#127)
- 77f95b7 #101 frontend/web: add PC 4-column layout to the make flow (#119)
