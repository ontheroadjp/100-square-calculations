# `frontend/web/src/catalog.js`

## 目的・役割

`catalog.html`(学年別カテゴリ画面)のページエントリ。issue #99 で `docs/uiux/wireframe_v1.png` の画面②(学年ごとのカテゴリ・ドリル一覧)に合わせて全面書き換えした。旧絞り込みフォーム(`numberType`/`grade`/`level`/`forms`)は撤去し、`drillCatalog.js` の `buildDrillCatalog`/`filterDrillCatalog`(旧5分類の `operationGroup` タクソノミー)を経由せず、`drillPresets.js` の `presetsByGrade[grade]`(たし算/ひき算/かけ算/わり算/分数/四則混合/数の性質のカテゴリマップ)を直接消費する。

## 動作の概要

- モジュール読み込み時に `mountNavShell()` を呼ぶ。
- `render()`: `location.search` から `grade` を読み、`GRADES`(1〜6)に含まれない場合は空状態(`no_drills_found` + 戻るリンク)を表示して終了する。
- `GET /renderer-info` を fetch して `activeRenderer` を確定する(失敗時は `reportlab` にフォールバック)。
- `CATEGORY_ORDER`(`addition`/`subtraction`/`multiplication`/`division`/`fraction`/`four-operations`/`number-sense` の固定順)でループし、`presetsByGrade[grade]` に存在するカテゴリだけを、各アイテムを `canUseItem(item, activeRenderer)`(`!item.latexOnly || activeRenderer === 'latex'`。`drillCatalog.js` 内の同名関数と同じロジックをこのファイル内に複製)でフィルタしたうえで描画する。`presetsByGrade` のオブジェクトキー挿入順は学年ごとに異なる(例: grade4 は division が addition より先)ため、表示順は `CATEGORY_ORDER` で固定している。
- `drillCardHtml`: ドリルカード1件を、タイトル・`item.difficultyKey`(`difficulty_basic`/`difficulty_standard`/`difficulty_basic_standard`)そのままを使う難易度バッジ・`item.examples[0]` を `formatExample()`(`+`/`-`/`×`/`÷` の前後にスペースを挿入。`/` は分数の区切りとして扱いスペースを入れない)で整形した例題1件、を `<a href="preset.html?grade=<grade>&drillId=<id>&format=default">` として描画する。カード全体がリンク。
- URL契約(`preset.html?grade=N&drillId=ID&format=default`)は #97/#98 時点から変更していないため、`preset.js`/`presetDetail.js`/`drillCatalog.js` は無変更のまま連携する。

## 重要な設計判断とその理由

### `drillCatalog.js` の `buildDrillCatalog`/`filterDrillCatalog` を経由しなくなった理由

`drillCatalog.js` の L3 doc([[./drillCatalog.js]] 参照)が issue #98 時点で「将来的に `home.js`/`catalog.js`/`preset.js` が #99/#100 の新 UI に置き換わった時点で、本ファイル自体の削除が可能になる(issue #110)」と明記していた通り、issue #99 のスコープは `catalog.js` をその新 UI に置き換えることだった。`buildDrillCatalog` が生成する `operationGroup`(旧5分類)は wireframe が要求する7カテゴリ(`addition`/`subtraction`/... のカテゴリキーそのもの)と一致しないため、`presetsByGrade` を直接読む設計にした。`preset.js` はまだ `drillCatalog.js` に依存しているため(issue #100 のスコープ)、`drillCatalog.js` 自体は削除していない。

### `canUseItem` を `drillCatalog.js` からインポートせず複製した理由

`drillCatalog.js` の `canUseItem` は非 export のプライベート関数であり、`catalog.js` が `presetsByGrade` を直接読む設計に切り替えたことで `drillCatalog.js` への依存を全体的に減らす方針と合わせ、1行のロジックのために export を追加するより複製の方が `drillCatalog.js`(将来削除候補、issue #110)への結合を増やさずに済むと判断した。

### 例題を1件・スペース整形して表示する理由

`docs/uiux/wireframe_v1.png` の画面②は各ドリルカードに例題を1件(`例）625 + 75` のようにスペース区切り)だけ表示している。`drillPresets.js` の `examples` 配列(最大3件、`'625+75'` のようにスペースなし)は元データのため、`catalog.js` 側で見た目だけ調整している。

## 統合ポイント

- 呼び出し元: `catalog.html` の `<script type="module" src="/src/catalog.js">`。
- 呼び出し先: `strings.js`(`t`)、`drillPresets.js`(`GRADES`/`presetsByGrade`)、`navShell.js`(`mountNavShell`)、`backend`(`GET /renderer-info`)。ドリルカードのリンク遷移先は `preset.html`(ブラウザナビゲーションのみ)。
- `drillCatalog.js`/`filterDrillCatalog`/`buildDrillCatalog` への依存はなくなった。

## 注意事項・既知の制限

- 絞り込みフォーム(`numberType`/`level`/`forms`、issue #97 で追加した「問題の形式」チェックボックスを含む)は issue #99 で完全に撤去した。カテゴリ・学年を横断した検索・絞り込みの導線は現在存在しない。
- `grade` パラメータが `GRADES`(1〜6)に含まれない場合(欠落・範囲外・`ungraded` など)は一律で空状態を表示する。

## 変更履歴(git log より自動生成)

- (issue #99 実装コミット) feat(#99): rebuild frontend/web catalog screen to match wireframe screen 2
- b11ac96 feat(#97): rebuild frontend/web nav shell and design tokens, remove custom generator/search/ungraded UI
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
